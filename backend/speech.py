"""One persistent process owns inference, benchmarking, and section publication."""
from __future__ import annotations

import os
import json
import logging
import time
import wave
import uuid
from pathlib import Path


def speech_worker(commands, events, cancel, runtime_directory=None):
    if runtime_directory:
        from .runtime import activate_gpu_runtime
        activate_gpu_runtime(runtime_directory)
    import numpy as np
    import soundfile as sf
    from .cache import SectionCache, audio_info, section_key
    from .pcm_audio import MAX_AUDIO_BYTES, RATE, open_pcm
    from .performance import create_engine
    from .pronunciation import pronunciation_compatible, pronunciation_identity

    engine, identity = None, None
    process_pronunciation = pronunciation_identity()

    def load(command, config=None, job_id=None):
        nonlocal engine, identity
        config = config or command['config']
        if pronunciation_identity() != process_pronunciation:
            raise ValueError('Pronunciation files changed while Violilt was open. Restart Violilt before creating or continuing a reading.')
        model, voices = config['model'], command['voices']
        version = (model, os.path.getmtime(model), voices, os.path.getmtime(voices),
                   config['provider'], config['device_id'], config['threads'], config.get('spinning', False),
                   json.dumps(pronunciation_identity(), sort_keys=True))
        if version != identity:
            engine = None
            if job_id is not None:
                events.put({'id': job_id, 'state': 'preparing', 'message': 'Loading model…'})
            engine = create_engine(model, voices, config)
            identity = version
        return engine

    def priority(config):
        if os.name == 'nt':
            import psutil
            try:
                psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if config.get('background') else psutil.NORMAL_PRIORITY_CLASS)
            except psutil.AccessDenied:
                pass

    while True:
        command = commands.get()
        if command is None:
            return
        kind = command.get('kind', 'generate')
        if kind == 'benchmark':
            results = []
            sample = 'A long reading can begin with a small passage. Listen to the first words while the next part is prepared, and let each thought arrive at its own pace.'
            for index, config in enumerate(command['candidates']):
                if cancel.is_set():
                    break
                events.put({'kind': kind, 'state': 'running', 'completed': index, 'total': len(command['candidates']),
                            'message': 'Testing ' + config['label'], 'results': results.copy()})
                try:
                    priority(config)
                    started = time.perf_counter()
                    voice_engine = load(command, config)
                    loading = time.perf_counter() - started
                    voice_engine.create('A little room for listening.', voice='af_heart', speed=1, lang='en-us')
                    if cancel.is_set():
                        break
                    started = time.perf_counter()
                    samples, rate = voice_engine.create(sample, voice='af_heart', speed=1, lang='en-us')
                    elapsed = time.perf_counter() - started
                    if not len(samples) or rate != 24000 or not np.all(np.isfinite(samples)):
                        raise ValueError('The backend returned invalid audio.')
                    results.append({key: value for key, value in config.items() if key != 'model'} | {
                        'load_seconds': loading, 'processing_seconds': elapsed, 'audio_seconds': len(samples) / rate,
                        'throughput': len(samples) / rate / elapsed})
                except Exception as error:
                    results.append({key: value for key, value in config.items() if key != 'model'} | {'error': str(error)[:500]})
                events.put({'kind': kind, 'state': 'running', 'completed': index + 1, 'total': len(command['candidates']),
                            'message': 'Compared ' + config['label'], 'results': results.copy()})
            events.put({'kind': kind, 'state': 'cancelled' if cancel.is_set() else 'completed',
                        'completed': len(results), 'total': len(command['candidates']), 'results': results,
                        'message': 'Speed test stopped.' if cancel.is_set() else 'Your speed test is ready.'})
            continue
        if kind == 'warmup':
            try:
                if not cancel.is_set():
                    priority(command['config'])
                    load(command)
                events.put({'kind': kind, 'state': 'ready', 'message': 'Voice engine loaded.'})
            except Exception as error:
                events.put({'kind': kind, 'state': 'failed', 'message': str(error)[:500]})
            continue

        job = command['job']
        key = job['id']
        directory = Path(command['directory'])
        cache = None
        started = time.perf_counter()
        sections, available, hits, generated = [], 0.0, 0, 0
        warnings = list(job.get('pronunciation_warnings', []))
        total = len(job['chunks'])
        try:
            directory.mkdir(parents=True, exist_ok=True)
            if command['cache_enabled']:
                try:
                    cache = SectionCache(Path(command['cache']), command['cache_limit_mb'])
                except OSError:
                    logging.warning('Reusable audio cache is unavailable; generating without cache')
            if not pronunciation_compatible(job.get('pronunciation_identity'), process_pronunciation):
                raise ValueError('This reading uses different pronunciation files. Start a new reading after restarting Violilt.')
            priority(command['config'])
            events.put({'id': key, 'state': 'preparing', 'message': 'Checking saved audio…'})
            for index, chunk in enumerate(job['chunks']):
                if cancel.is_set():
                    events.put({'id': key, 'state': 'cancelled', 'message': 'Stopped. Your available audio and completed sections are saved.'})
                    break
                path = directory / f'section-{index:06d}.wav'
                info = audio_info(path)
                reusable = info is not None
                if not reusable and path.is_file():
                    # Keep unsupported/interrupted originals out of decoding and
                    # retain their bytes before publishing a regenerated section.
                    path.replace(path.with_name(path.name + '.unreadable-' + uuid.uuid4().hex))
                    notice = 'Unsupported or incomplete saved audio was kept separately and regenerated.'
                    if notice not in warnings:
                        warnings.append(notice)
                cache_key = section_key(chunk['text'], job['voice'], job['speed'], job['audio_identity'])
                if not reusable and cache:
                    try:
                        if cache.fetch(cache_key, path):
                            info, reusable = audio_info(path), True
                            hits += 1
                    except OSError:
                        cache = None
                        logging.warning('Reusable audio could not be read; generating without cache')
                if not reusable:
                    voice_engine = load(command, job_id=key)
                    if cancel.is_set():
                        events.put({'id': key, 'state': 'cancelled', 'message': 'Stopped. Your available audio and completed sections are saved.'})
                        break
                    events.put({'id': key, 'state': 'generating', 'completed': index, 'total': total,
                                'message': f'Model loaded. Generating section {index + 1} of {total}…'})
                    samples, rate = voice_engine.create(chunk['text'], voice=job['voice'], speed=job['speed'],
                                                        lang='en-gb' if job['voice'].startswith('b') else 'en-us')
                    section_warnings = list(getattr(voice_engine, 'last_pronunciation_warnings', []))
                    if not len(samples) or rate != 24000 or not np.all(np.isfinite(samples)):
                        raise ValueError('The speech engine returned an invalid audio section.')
                    temporary = path.with_suffix('.part')
                    sf.write(temporary, samples, rate, format='WAV', subtype='PCM_16')
                    SectionCache.write_warnings(path, section_warnings)
                    temporary.replace(path)
                    info = audio_info(path)
                    if info is None:
                        raise ValueError('The generated audio could not be saved as complete PCM WAV.')
                    generated += 1
                    if cache:
                        try:
                            cache.put(cache_key, path)
                        except OSError:
                            cache = None
                            logging.warning('Reusable audio could not be stored; continuing without cache')
                for warning in SectionCache.read_warnings(path):
                    if warning not in warnings:
                        warnings.append(warning)
                pause = int(chunk['pause'] * 24000) / 24000 if index < total - 1 else 0
                sections.append({'index': index, 'start': available, 'duration': info.frames / 24000, 'pause': pause})
                available += info.frames / 24000 + pause
                elapsed = time.perf_counter() - started
                event = {'id': key, 'state': 'generating' if generated else 'preparing', 'completed': index + 1, 'total': total,
                         'sections': sections.copy(), 'available_duration': available, 'throughput': available / max(elapsed, 0.001),
                         'processing_seconds': elapsed, 'cache_hits': hits, 'generated_sections': generated,
                         'pronunciation_warnings': warnings.copy(),
                         'message': (f'Reusing saved audio. {index + 1} of {total} sections ready to listen'
                                     if reusable else f'{index + 1} of {total} sections ready to listen')}
                if index == 0:
                    event['first_audio_seconds'] = max(0, time.time() - job.get('attempt_started', job['created']))
                events.put(event)
                if command['config'].get('pace') and not reusable:
                    cancel.wait(command['config']['pace'])
            else:
                if cancel.is_set():
                    events.put({'id': key, 'state': 'cancelled', 'message': 'Stopped. Your completed sections are saved.'})
                    continue
                events.put({'id': key, 'state': 'assembling', 'message': 'Saving the complete recording…'})
                temporary = directory / 'recording.part'
                frames = 0
                with wave.open(str(temporary), 'wb') as output:
                    output.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
                    for index, section in enumerate(sections):
                        if cancel.is_set():
                            break
                        with open_pcm(directory / f'section-{index:06d}.wav') as source:
                            if source.info.frames != round(section['duration'] * RATE):
                                raise ValueError('A saved section changed before assembly. Try continuing again.')
                            for block in source.blocks():
                                if cancel.is_set():
                                    break
                                if frames * 2 + len(block) > MAX_AUDIO_BYTES:
                                    raise ValueError('This recording exceeds WAV capacity. Split it into smaller documents.')
                                output.writeframesraw(block)
                                frames += len(block) // 2
                        silence = round(section['pause'] * RATE)
                        while silence and not cancel.is_set():
                            count = min(silence, 65536)
                            if (frames + count) * 2 > MAX_AUDIO_BYTES:
                                raise ValueError('This recording exceeds WAV capacity. Split it into smaller documents.')
                            output.writeframesraw(bytes(count * 2))
                            frames += count
                            silence -= count
                if cancel.is_set():
                    events.put({'id': key, 'state': 'cancelled', 'message': 'Stopped. Your completed sections are saved.'})
                    continue
                info = audio_info(temporary)
                if info is None:
                    raise ValueError('The assembled recording could not be saved as complete PCM WAV.')
                duration = info.duration
                if abs(duration - available) > 1 / 24000:
                    raise ValueError('The final recording does not match its section timeline.')
                recording = directory / 'recording.wav'
                if recording.is_file() and audio_info(recording) is None:
                    recording.replace(recording.with_name(recording.name + '.unreadable-' + uuid.uuid4().hex))
                    notice = 'Unsupported or incomplete saved audio was kept separately and regenerated.'
                    if notice not in warnings:
                        warnings.append(notice)
                temporary.replace(recording)
                events.put({'id': key, 'state': 'completed', 'completed': total, 'total': total, 'duration': duration,
                            'pronunciation_warnings': warnings.copy(),
                            'processing_seconds': time.perf_counter() - started, 'message': 'Your recording is ready.'})
        except Exception as error:
            events.put({'id': key, 'state': 'failed', 'message': f'Generation stopped: {str(error)[:700]}'})
