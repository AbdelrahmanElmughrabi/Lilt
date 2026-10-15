"""Source-only real-model release/reload check using a new isolated library."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def wait_for(predicate, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.05)
    raise AssertionError('Timed out waiting for the voice process.')


def check(args):
    import psutil
    import soundfile as sf
    from backend.documents import prepare
    from backend.jobs import Jobs
    from backend.models import Models
    from backend.storage import Store

    args.output.mkdir(parents=True, exist_ok=False)
    store = Store(args.output / 'data')
    store.save_settings({'processing_device': args.device, 'cache_enabled': False, 'model_release': 'idle'})
    jobs = Jobs(store, Models(args.models))
    evidence = {'device': args.device, 'runs': []}
    try:
        for index in range(2):
            markdown = '# A little room\n\nA quiet reading begins with a little curiosity.'
            prepared = prepare(markdown)
            document = store.document(markdown, prepared['title'])
            started = time.monotonic()
            created = jobs.start(prepared, document, 'af_heart', 1)
            wait_for(lambda: jobs.state() is None)
            job = store.get('jobs', created['id'])
            assert job['state'] == 'completed', job['message']
            assert job['generated_sections'] > 0 and job['cache_hits'] == 0
            elapsed = time.monotonic() - started
            process = jobs.process
            pid = process.pid
            resident_mb = round(psutil.Process(pid).memory_info().rss / 1048576, 1)
            audio = store.root / 'jobs' / job['id'] / 'recording.wav'
            digest = hashlib.sha256(audio.read_bytes()).hexdigest()
            release_started = time.monotonic()
            if index == 0:
                jobs.release_engine()
            else:
                # Advance only the idle timestamp; the real listener performs release.
                # Exact before/after-120-second boundaries are covered by unit tests.
                with jobs.lock:
                    jobs.idle_since = time.monotonic() - 120
                wait_for(lambda: jobs.performance_state()['memory']['state'] == 'unloaded', timeout=15)
            release_seconds = time.monotonic() - release_started
            assert not psutil.pid_exists(pid), 'Released worker still exists.'
            assert hashlib.sha256(audio.read_bytes()).hexdigest() == digest
            samples, rate = sf.read(audio)
            assert rate == 24000 and len(samples) and any(samples)
            jobs.save_position(job['id'], 1)
            assert jobs.stream(job['id'])['complete']
            evidence['runs'].append({'release': 'manual' if index == 0 else 'idle listener with advanced timestamp',
                                     'generation_seconds': round(elapsed, 2), 'worker_rss_mb': resident_mb,
                                     'release_seconds': round(release_seconds, 2), 'worker_exited': True,
                                     'saved_audio_readable': True, 'job': job['id']})
        store.save_settings({'model_release': 'immediate'})
        jobs.warmup()
        wait_for(lambda: jobs.operation is None and jobs.performance_state()['memory']['state'] == 'unloaded')
        evidence['immediate_after_warmup'] = True
        print(json.dumps(evidence, indent=2))
        (args.output / 'evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    finally:
        jobs.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, default=ROOT / 'dist/pronunciation/Lilt/models')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', choices=('cpu', 'gpu'), default='cpu')
    check(parser.parse_args())
