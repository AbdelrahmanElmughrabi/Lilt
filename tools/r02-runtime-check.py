"""Real CPU/CUDA generation with synthetic text, pinned existing models and injected IO faults."""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import sqlite3
import sys
import time
import traceback
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, required=True, help='Existing approved public model fixture directory')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.tmp') or output == ROOT / '.tmp':
        parser.error('Use a new output directory under this workspace .tmp.')
    output.mkdir(parents=True, exist_ok=False)
    from backend.bridge import Bridge
    from backend.jobs import Jobs
    from backend.models import Models, FILES, GPU_FILE
    from backend.model_trust import verify_file
    from backend.storage import Store

    fixture = args.models.resolve()
    model_before = {}
    for name in (*FILES, GPU_FILE):
        verify_file(fixture / name)
        model_before[name] = hashlib.sha256((fixture / name).read_bytes()).hexdigest()
    store = Store(output / 'library')
    store.save_settings({'model_release': 'keep', 'warm_start': False, 'cache_enabled': True})
    models = Models(store.root / 'models', fixture)
    jobs = Jobs(store, models)
    bridge = Bridge(store, models, jobs)
    result = {'success': False, 'runs': [], 'model_fixture': str(fixture),
              'limits': ['Source backend workers, not frozen/installed MSIX.',
                         'Synthetic text; SQL write fault and invalid optional cache path injected.',
                         'No human listening or performance benchmark.']}
    put = store.put
    injected = False

    def constrained_put(table, item):
        nonlocal injected
        if table == 'jobs' and item.get('completed', 0) > 0 and not injected:
            injected = True
            raise sqlite3.OperationalError('Synthetic one-time progress persistence fault')
        return put(table, item)

    store.put = constrained_put
    try:
        for device in ('cpu', 'gpu'):
            if device == 'gpu':
                jobs.release_engine()
            bridge.save_settings({'processing_device': device, 'gpu_device': 0 if device == 'gpu' else -1})
            invalid_cache = output / 'unavailable-optional-cache'
            if device == 'gpu':
                invalid_cache.write_bytes(b'Synthetic non-directory cache fixture.')
                queue_put = jobs.commands.put

                def no_cache(command):
                    if isinstance(command, dict) and command.get('kind') == 'generate':
                        command = command | {'cache': str(invalid_cache)}
                    return queue_put(command)

                jobs.commands.put = no_cache
            text = 'This is a synthetic release test. The previous saved recording stays intact. Short pauses make each word clear.'
            document = store.document(text, 'R-02 ' + device.upper())
            job = bridge.generate(document['id'], text, store.settings())
            noticed = False
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                state = bridge.get_state()
                noticed |= 'not been saved' in state['recovery']['message']
                saved = store.get('jobs', job['id'])
                if saved['state'] in {'failed', 'cancelled'}:
                    raise AssertionError(saved['message'])
                if saved['state'] == 'completed' and jobs.state() is None:
                    break
                time.sleep(.1)
            else:
                raise TimeoutError(device + ' generation did not finish.')
            path = store.root / 'jobs' / job['id'] / 'recording.wav'
            with wave.open(str(path), 'rb') as audio:
                frames, rate = audio.getnframes(), audio.getframerate()
                assert audio.getnchannels() == 1 and audio.getsampwidth() == 2 and rate == 24000
                assert any(audio.readframes(min(frames, 24000)))
            expected_provider = 'CPUExecutionProvider' if device == 'cpu' else 'CUDAExecutionProvider'
            assert saved['engine']['provider'] == expected_provider
            if device == 'cpu':
                assert injected and noticed, 'The actual pending-write warning was not observed.'
            assert not jobs.pending_storage()['message']
            run = {'device': device, 'provider': saved['engine']['provider'], 'frames': frames,
                   'audio_seconds': frames / rate, 'progress_warning_observed': noticed,
                   'optional_cache_init_fault': device == 'gpu', 'job': job['id']}
            result['runs'].append(run)
            print(json.dumps({'phase': 'completed', **run}), flush=True)
        result['success'] = True
    except Exception as error:
        result.update(error=str(error), traceback=traceback.format_exc())
    finally:
        store.put = put
        jobs.close()
        result['model_fixture_unchanged'] = all(hashlib.sha256((fixture / name).read_bytes()).hexdigest() == digest
                                                for name, digest in model_before.items())
        if not result['model_fixture_unchanged']:
            result['success'] = False
        (output / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return 0 if result['success'] else 1


if __name__ == '__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())
