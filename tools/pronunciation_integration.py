"""Source-only isolated real-model integration checks for the current engine.

Run with the matching Python environment. Models are read without modification;
all generated libraries, samples and evidence go into an explicit new directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait_job(jobs, key, early=None, timeout=300):
    deadline, observed = time.monotonic() + timeout, False
    while time.monotonic() < deadline:
        job = jobs.store.get('jobs', key)
        if job['completed'] and not observed:
            observed = True
            if early:
                early(job)
        if job['state'] in {'completed', 'cancelled', 'failed', 'interrupted'}:
            while jobs.state() and time.monotonic() < deadline:
                time.sleep(.02)
            if job['state'] == 'failed':
                raise AssertionError(job['message'])
            return jobs.store.get('jobs', key)
        time.sleep(.02)
    raise AssertionError('Generation timed out.')


def verify_audio(jobs, job):
    import numpy as np
    import soundfile as sf
    folder = jobs.store.root / 'jobs' / job['id']
    complete, rate = sf.read(folder / 'recording.wav', dtype='int16')
    assert rate == 24000 and np.any(complete) and np.all(np.isfinite(complete))
    offset = 0
    for section in jobs.stream(job['id'])['sections']:
        raw, _ = sf.read(folder / f"section-{section['index']:06d}.wav", dtype='int16')
        assert abs(offset / rate - section['start']) < 1 / rate
        assert np.array_equal(raw, complete[offset:offset + len(raw)])
        offset += len(raw)
        pause = round(section['pause'] * rate)
        assert not np.any(complete[offset:offset + pause])
        offset += pause
    assert offset == len(complete)
    return digest(folder / 'recording.wav')


def integration(arguments):
    from backend.documents import prepare
    from backend.jobs import Jobs
    from backend.models import Models
    from backend.server import AppServer
    from backend.storage import Store
    store = Store(arguments.output / 'data')
    jobs = Jobs(store, Models(arguments.models))
    server = AppServer(ROOT / 'frontend/dist', store)
    server.start()
    evidence = {}
    try:
        store.save_settings({'processing_device': arguments.device, 'performance_mode': 'balanced', 'cache_enabled': True})
        markdown = '# A room for listening\n\n' + '\n\n'.join(
            f'Passage {i + 1}. A long reading begins with a little room for curiosity. Listen to the first words while '
            'the next thought is prepared. Let each sentence arrive at its own pace.' for i in range(8))
        document = store.document(markdown, 'A room for listening')
        prepared = prepare(markdown)
        first = jobs.start(prepared, document, 'af_heart', 1)
        observed = []

        def early(job):
            stream = jobs.stream(job['id'])
            assert stream['available'] > 0 and stream['sections']
            observed.append(job['state'] not in {'completed', 'assembling'})
            section = stream['sections'][0]
            request = urllib.request.Request(server.url + f"/media/{job['id']}/section-{section['index']:06d}.wav", headers={'Range': 'bytes=0-63'})
            with urllib.request.urlopen(request, timeout=10) as response:
                assert response.status == 206 and response.read(4) == b'RIFF'

        first = wait_job(jobs, first['id'], early)
        assert first['state'] == 'completed' and any(observed), 'Early audio was not observed.'
        verify_audio(jobs, first)
        evidence['generation'] = {key: first.get(key) for key in ('engine', 'total', 'first_audio_seconds', 'duration', 'processing_seconds', 'throughput')}
        print('Early HTTP audio, exact section/final samples and generation passed', flush=True)
        repeated = wait_job(jobs, jobs.start(prepared, document, 'af_heart', 1)['id'])
        assert repeated['cache_hits'] == repeated['total'] and repeated['generated_sections'] == 0
        assert verify_audio(jobs, first) == verify_audio(jobs, repeated)
        evidence['cache'] = {'hits': repeated['cache_hits'], 'seconds': repeated['processing_seconds']}

        # A new voice prevents cache hits; stop after the first published section.
        store.save_settings({'cache_enabled': False})
        interrupted = jobs.start(prepared, document, 'am_michael', 1)
        interrupted = wait_job(jobs, interrupted['id'], lambda job: jobs.stop())
        assert interrupted['state'] == 'cancelled' and 0 < interrupted['completed'] < interrupted['total']
        folder = store.root / 'jobs' / interrupted['id']
        before = {path.name: digest(path) for path in folder.glob('section-*.wav')}
        snapshot = {key: interrupted[key] for key in ('chunks', 'options', 'voice', 'speed', 'pronunciation_identity', 'audio_identity')}
        jobs.save_position(interrupted['id'], .5)
        jobs.close()
        jobs = Jobs(store, Models(arguments.models))
        resumed = wait_job(jobs, jobs.start(prepare(interrupted['markdown'], interrupted['options']),
                                         document, interrupted['voice'], interrupted['speed'], resume=interrupted['id'])['id'])
        assert resumed['state'] == 'completed' and resumed['position'] == .5
        assert all(digest(folder / name) == value for name, value in before.items())
        assert all(resumed[key] == value for key, value in snapshot.items())
        verify_audio(jobs, resumed)
        evidence['recovery'] = {'saved_sections': len(before), 'resumed_sections': resumed['total'], 'position': resumed['position']}
        print('Cache reuse, cancellation and restart/continuation passed', flush=True)

        store.save_settings({'processing_device': 'cpu', 'performance_mode': 'quiet', 'cache_enabled': False})
        quiet = wait_job(jobs, jobs.start(prepare('A short CPU reading leaves room for other applications.'), document, 'af_heart', 1)['id'])
        assert quiet['engine']['threads'] == 1 and quiet['engine']['background']
        verify_audio(jobs, quiet)
        evidence['quiet_cpu'] = {'engine': quiet['engine'], 'throughput': quiet['throughput']}
        jobs.benchmark()
        jobs.stop_benchmark()
        deadline = time.monotonic() + 300
        while jobs.operation and time.monotonic() < deadline:
            time.sleep(.1)
        with jobs.lock:
            assert jobs.performance.benchmark['state'] == 'cancelled'
        jobs.benchmark()
        while jobs.operation and time.monotonic() < deadline:
            time.sleep(.1)
        # The listener clears operation while still holding its lock and saving
        # the completed recommendation. Wait for that transaction to finish.
        with jobs.lock:
            assert jobs.performance.benchmark['state'] == 'completed'
            result = jobs.performance.recommendation()
        assert result and result['cpu']['throughput'] > 0
        evidence['benchmark'] = result
        return evidence
    finally:
        jobs.close()
        server.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--models', type=Path, default=ROOT / '.app-data/models')
    parser.add_argument('--device', choices=['cpu', 'gpu'], default='cpu')
    arguments = parser.parse_args()
    arguments.output = arguments.output.resolve()
    if arguments.output.exists():
        raise ValueError('Use a new evidence directory; existing libraries and recordings are never overwritten.')
    arguments.output.mkdir(parents=True)
    evidence = integration(arguments)
    (arguments.output / 'results.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps({'success': True, 'evidence': str(arguments.output / 'results.json')}), flush=True)


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
