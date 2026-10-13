from __future__ import annotations

import copy
import json
import math
import multiprocessing as mp
import threading
import time
import uuid

from .cache import SectionCache
from .models import FILES, GPU_FILE
from .performance import Performance, model_identity
from .pronunciation import pronunciation_identity
from .runtime import gpu_runtime_directory
from .sections import listening_chunks, manifest, published_sections
from .speech import speech_worker

TERMINAL = {'completed', 'cancelled', 'failed', 'interrupted'}
RESUMABLE = {'cancelled', 'failed', 'interrupted'}
PRONUNCIATION_CHANGED = ('This reading used a different pronunciation engine. '
                         'Your saved audio is kept. Start a new reading to continue.')


def public_job(job):
    result = {key: value for key, value in job.items() if key not in {
        'chunks', 'markdown', 'sections', 'audio_identity', 'pronunciation_identity', 'fingerprint'}}
    result.pop('unread_symbols', None)
    result['unread_count'] = len(job.get('unread_symbols', []))
    compatible = job['state'] in RESUMABLE and job.get('pronunciation_identity') == pronunciation_identity()
    result.update(can_resume=compatible, resume_message=PRONUNCIATION_CHANGED
                  if job['state'] in RESUMABLE and not compatible else '')
    return result


class Jobs:
    def __init__(self, store, models):
        self.store, self.models = store, models
        self.lock = threading.RLock()
        self.context = mp.get_context('spawn')
        self.commands, self.events = self.context.Queue(), self.context.Queue()
        self.cancel = self.context.Event()
        self.process, self.active, self.operation = None, None, None
        self.closing = False
        self.performance = Performance(store, models) if models else None
        self.cache = SectionCache(store.root / 'section-cache', store.settings()['cache_limit_mb'])
        self._identities = {}
        self._cache_sample = (0, {})
        for job in store.all('jobs'):
            if job['state'] not in TERMINAL:
                job.update(state='interrupted', message='This reading was interrupted. Your completed sections are saved.')
                store.put('jobs', job)
        threading.Thread(target=self._listen, daemon=True).start()

    def _worker(self):
        if not self.process or not self.process.is_alive():
            self.process = self.context.Process(target=speech_worker,
                args=(self.commands, self.events, self.cancel, gpu_runtime_directory()), daemon=True)
            self.process.start()

    def _audio_identity(self, filename, pronunciation=None):
        pronunciation = pronunciation if pronunciation is not None else pronunciation_identity()
        paths = [self.models.root / filename, self.models.root / FILES[1]]
        runtime = (self.performance.gpu_runtime or {}).get('runtime', self.performance.runtime)
        key = (tuple((str(path), path.stat().st_size, path.stat().st_mtime_ns) for path in paths),
               json.dumps(pronunciation, sort_keys=True), runtime)
        if key not in self._identities:
            self._identities[key] = [model_identity(path) for path in paths] + [runtime, copy.deepcopy(pronunciation)]
        return self._identities[key]

    def _write_unread(self, job):
        symbols = job.get('unread_symbols', [])
        if not symbols:
            return
        directory = (self.store.root / 'jobs' / job['id']).resolve()
        if directory.parent != (self.store.root / 'jobs').resolve():
            raise ValueError('Invalid recording location.')
        directory.mkdir(parents=True, exist_ok=True)
        lines = ['Symbols omitted from the prepared speech text.',
                 'Later sections may not have been generated if this reading was stopped.',
                 f"Reading: {job['title']}", f"Recording: {job['id']}", '']
        for symbol in symbols:
            codes = ' '.join(f'U+{ord(c):04X}' for c in symbol)
            lines.append(f'{json.dumps(symbol, ensure_ascii=False)} ({codes})')
        temporary = directory / 'unread.part'
        temporary.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        temporary.replace(directory / 'unread.txt')

    def start(self, prepared, document, voice, speed, preview=False, resume=None):
        with self.lock:
            if self.active or self.operation == 'benchmark':
                raise ValueError('Finish or cancel the current reading or speed test first.')
            pronunciation = copy.deepcopy(pronunciation_identity())
            if resume:
                job = self.store.get('jobs', resume)
                if job['state'] not in RESUMABLE:
                    raise ValueError('This reading cannot be continued.')
                # Old sections remain listenable, but must never be extended by another engine.
                if job.get('pronunciation_identity') != pronunciation:
                    raise ValueError(PRONUNCIATION_CHANGED)
            status = self.models.status()
            if status['state'] != 'ready':
                raise ValueError('Set up the local voice engine first.')
            if voice not in status['voices']:
                raise ValueError('Choose an available English voice.')
            speed = float(speed)
            if not 0.5 <= speed <= 2:
                raise ValueError('Narration speed must be between 0.5× and 2×.')
            if not prepared['chunks']:
                raise ValueError('This document has no readable text.')
            settings = self.store.settings()
            if resume:
                filename = job.get('model_file', FILES[0])
                if filename not in {FILES[0], GPU_FILE}:
                    raise ValueError('Unknown saved voice model.')
                config = self.performance.resolve(settings | {'processing_device': 'gpu' if filename != FILES[0] else 'cpu'})
                identity = self._audio_identity(filename, pronunciation)
                if job.get('audio_identity') != identity or job['markdown'] != document['markdown'] or job['voice'] != voice or job['speed'] != speed or job['options'] != prepared['options']:
                    raise ValueError('Continue with the original text, voice, and model files.')
                job.update(state='preparing', message='Continuing your reading…')
                job['sections'], job['available_duration'] = published_sections(job, self.store.root / 'jobs' / job['id'])
                job['completed'] = len(job['sections'])
            else:
                config = self.performance.resolve(settings)
                filename = GPU_FILE if config['provider'] != 'CPUExecutionProvider' else FILES[0]
                chunks = listening_chunks(prepared['chunks'])
                job = {'id': uuid.uuid4().hex, 'document_id': document['id'], 'title': document['title'],
                       'voice': voice, 'speed': speed, 'words': prepared['words'], 'preview': preview,
                       'chunks': chunks, 'markdown': document['markdown'], 'options': copy.deepcopy(prepared['options']),
                       'unread_symbols': list(prepared.get('unread_symbols', [])),
                       'audio_identity': self._audio_identity(filename, pronunciation), 'pronunciation_identity': pronunciation,
                       'model_file': filename,
                       'created': time.time(), 'state': 'preparing', 'completed': 0, 'total': len(chunks),
                       'duration': 0, 'position': 0, 'sections': [], 'available_duration': 0,
                       'message': 'Preparing your first words…'}
            job.update(attempt_started=time.time(), engine={key: value for key, value in config.items() if key != 'model'},
                       cache_hits=0, generated_sections=0)
            self.store.put('jobs', job)
            try:
                self._write_unread(job)
            except OSError as error:
                job.update(state='failed', message='Could not save unread.txt. Your text and available audio are kept.')
                self.store.put('jobs', job)
                raise ValueError(job['message']) from error
            self.active = job
            self.cancel.clear()
            self._worker()
            self.commands.put({'kind': 'generate', 'job': job, 'directory': str(self.store.root / 'jobs' / job['id']),
                               'config': config, 'voices': str(self.models.root / FILES[1]),
                               'cache': str(self.cache.root), 'cache_enabled': settings['cache_enabled'],
                               'cache_limit_mb': settings['cache_limit_mb']})
            return public_job(job)

    def stop(self):
        with self.lock:
            if self.active:
                self.cancel.set()
                self.active.update(state='cancelling', message='Stopping after the current section…')
                self.store.put('jobs', self.active)
        return True

    def benchmark(self):
        with self.lock:
            if self.active or self.operation:
                raise ValueError('Finish the current reading or engine preparation first.')
            if self.models.status()['state'] != 'ready':
                raise ValueError('Set up the voice engine before running a speed test.')
            self.performance._identity = None
            candidates = self.performance.candidates()
            self.performance.benchmark = {'state': 'running', 'completed': 0, 'total': len(candidates), 'results': [], 'message': 'Starting a local speed test…'}
            self.operation = 'benchmark'
            self.cancel.clear()
            self._worker()
            self.commands.put({'kind': 'benchmark', 'candidates': candidates, 'voices': str(self.models.root / FILES[1])})
        return True

    def stop_benchmark(self):
        with self.lock:
            if self.operation == 'benchmark':
                self.cancel.set()
                self.performance.benchmark.update(state='cancelling', message='Stopping after this sample…')
        return True

    def warmup(self):
        with self.lock:
            if self.active or self.operation or self.models.status()['state'] != 'ready':
                return False
            config = self.performance.resolve(self.store.settings())
            self.operation = 'warmup'
            self.performance.warmup = {'state': 'loading', 'message': 'Loading your voice engine…'}
            self.cancel.clear()
            self._worker()
            self.commands.put({'kind': 'warmup', 'config': config, 'voices': str(self.models.root / FILES[1])})
        return True

    def stream(self, key):
        with self.lock:
            job = self.active if self.active and self.active['id'] == key else self.store.get('jobs', key)
            if 'sections' not in job:
                job['sections'], job['available_duration'] = published_sections(job, self.store.root / 'jobs' / key)
                self.store.put('jobs', job)
            return manifest(job)

    def save_position(self, key, position):
        with self.lock:
            job = self.active if self.active and self.active['id'] == key else self.store.get('jobs', key)
            value = float(position)
            if not math.isfinite(value):
                raise ValueError('Choose a valid listening position.')
            previous = job.get('position', 0)
            job['position'] = max(0, min(value, job.get('available_duration', job.get('duration', 0))))
            if abs(job['position'] - previous) >= 1:
                job['last_listened'] = time.time()
            self.store.put('jobs', job)
        return True

    def performance_state(self):
        with self.lock:
            return self.performance.status(self.process)

    def cache_state(self):
        if time.monotonic() - self._cache_sample[0] > 3:
            self._cache_sample = (time.monotonic(), self.cache.status())
        return self._cache_sample[1] | {'limit_mb': self.store.settings()['cache_limit_mb']}

    def clear_cache(self):
        with self.lock:
            if self.active or self.operation:
                raise ValueError('Finish the current reading or speed test before clearing reusable audio.')
            self.cache.clear()
            self._cache_sample = (0, {})
        return True

    def _listen(self):
        import queue
        while not self.closing:
            try:
                event = self.events.get(timeout=0.5)
            except queue.Empty:
                with self.lock:
                    if self.closing:
                        return
                    if self.process and not self.process.is_alive():
                        if self.active:
                            self.active.update(state='failed', message='The speech process stopped. Your completed sections are saved.')
                            self.store.put('jobs', self.active)
                            self.active = None
                        if self.operation:
                            getattr(self.performance, self.operation).update(state='failed', message='The speech process stopped. You can try again.')
                            self.operation = None
                continue
            with self.lock:
                if self.closing:
                    return
                kind = event.get('kind')
                if kind == 'benchmark':
                    if self.operation != kind:
                        continue
                    if self.performance.benchmark['state'] == 'cancelling' and event['state'] == 'running':
                        event.update(state='cancelling', message='Stopping after this sample…')
                    self.performance.benchmark.update(event)
                    if event['state'] in TERMINAL:
                        self.operation = None
                        valid = [result for result in event['results'] if 'throughput' in result]
                        cpu = [result for result in valid if result['provider'] == 'CPUExecutionProvider']
                        if event['state'] == 'completed' and cpu:
                            maximum = max(item['throughput'] for item in cpu)
                            efficient = min((item for item in cpu if item['throughput'] >= maximum * 0.95), key=lambda item: item['threads'])
                            best = max(valid, key=lambda item: item['throughput'])
                            self.store.save_settings({'benchmark_result': {'identity': self.performance.identity(),
                                'created': time.time(), 'cpu': efficient, 'best': best, 'results': event['results']}})
                elif kind == 'warmup':
                    self.performance.warmup.update(event)
                    self.operation = None
                elif self.active and event.get('id') == self.active['id']:
                    # Continuation scans checkpoints again; publication stays monotonic.
                    if event.get('completed', self.active['completed']) < self.active['completed']:
                        for field in ('completed', 'sections', 'available_duration', 'first_audio_seconds'):
                            event.pop(field, None)
                    if self.active['state'] == 'cancelling' and event['state'] not in TERMINAL:
                        event.update(state='cancelling', message='Stopping after the current section…')
                    self.active.update(event)
                    self.store.put('jobs', self.active)
                    if event['state'] in TERMINAL:
                        self.active = None

    def state(self):
        with self.lock:
            return public_job(self.active) if self.active else None

    def close(self):
        self.closing = True
        with self.lock:
            if self.active:
                self.active.update(state='interrupted', message='Continue this reading when you return.')
                self.store.put('jobs', self.active)
                self.active = None
            self.operation = None
        self.cancel.set()
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=3)
