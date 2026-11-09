"""Exercise actual reported text, real audio, cache and restart in a new library."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.pronunciation_integration import digest, verify_audio, wait_job


def integration(arguments):
    from backend.documents import prepare
    from backend.jobs import Jobs
    from backend.models import Models
    from backend.server import AppServer
    from backend.storage import Store

    original = json.loads(arguments.snapshot.read_text(encoding='utf-8'))
    before = json.loads(arguments.before.read_text(encoding='utf-8'))
    indices = sorted({8, 9, *(item['section'] - 1 for item in before['languages']['en-us']['failures']),
                      *(i for i, c in enumerate(original['chunks']) if 'pet = generate' in c['text'])})
    selected = '\n\n'.join(original['chunks'][i]['text'] for i in indices)
    markdown = original['markdown'] if arguments.full_document else selected
    store = Store(arguments.output / 'data')
    jobs = Jobs(store, Models(arguments.models))
    server = AppServer(ROOT / 'frontend/dist', store)
    server.start()
    evidence = {'device': arguments.device, 'full_document': arguments.full_document,
                'original_job_id': original['id'], 'selected_original_sections': [i + 1 for i in indices]}
    try:
        store.save_settings({'processing_device': arguments.device, 'performance_mode': 'balanced', 'cache_enabled': True})
        prepared = prepare(markdown, original['options'], original['title'])
        document = store.document(markdown, prepared['title'])

        def early(job):
            stream = jobs.stream(job['id'])
            assert stream['available'] > 0 and stream['sections'] and not stream['complete']
            request = urllib.request.Request(server.url + f"/media/{job['id']}/section-000000.wav",
                                             headers={'Range': 'bytes=0-63'})
            with urllib.request.urlopen(request, timeout=10) as response:
                assert response.status == 206 and len(response.read()) == 64
            evidence['early_audio'] = {'state': job['state'], 'available': stream['available'], 'http_status': 206}

        first = wait_job(jobs, jobs.start(prepared, document, original['voice'], original['speed'])['id'], early, timeout=900)
        first_digest = verify_audio(jobs, first)
        assert first['markdown'] == markdown
        assert store.get('documents', document['id'])['markdown'] == markdown
        if arguments.full_document:
            if arguments.allow_spacing:
                assert ''.join(''.join(c['text'] for c in first['chunks']).split()) == ''.join(''.join(c['text'] for c in original['chunks']).split())
            else:
                assert first['chunks'] == original['chunks']
        expected_provider = 'CUDAExecutionProvider' if arguments.device == 'gpu' else 'CPUExecutionProvider'
        assert first['engine']['provider'] == expected_provider
        evidence['generation'] = {key: first.get(key) for key in (
            'id', 'engine', 'voice', 'total', 'duration', 'first_audio_seconds', 'throughput', 'pronunciation_identity')}
        evidence['generation']['audio_sha256'] = first_digest
        print(f"Real {arguments.device} speech: {first['total']} sections, early audio and exact WAV assembly passed.", flush=True)

        cached = wait_job(jobs, jobs.start(prepared, document, original['voice'], original['speed'])['id'], timeout=900)
        assert cached['cache_hits'] == cached['total'] and cached['generated_sections'] == 0
        assert verify_audio(jobs, cached) == first_digest
        evidence['cache'] = {'hits': cached['cache_hits'], 'total': cached['total'], 'identical_audio': True}

        # All failure classes also go through British cancellation/restart.
        store.save_settings({'cache_enabled': False})
        recovery = prepare(selected, original['options'], 'Punctuation restart check')
        recovery_doc = store.document(selected, recovery['title'])
        cancelled = wait_job(jobs, jobs.start(recovery, recovery_doc, 'bf_emma', 1)['id'], lambda job: jobs.stop(), timeout=900)
        assert cancelled['state'] == 'cancelled' and 0 < cancelled['completed'] < cancelled['total']
        folder = store.root / 'jobs' / cancelled['id']
        hashes = {file.name: digest(file) for file in folder.glob('section-*.wav')}
        fields = ('chunks', 'markdown', 'options', 'voice', 'speed', 'pronunciation_identity', 'audio_identity')
        snapshot = {key: copy.deepcopy(cancelled[key]) for key in fields}
        jobs.save_position(cancelled['id'], .5)
        jobs.close()
        jobs = Jobs(store, Models(arguments.models))
        resumed = wait_job(jobs, jobs.start(recovery, recovery_doc, 'bf_emma', 1, resume=cancelled['id'])['id'], timeout=900)
        assert resumed['state'] == 'completed' and resumed['position'] == .5
        assert all(resumed[key] == value for key, value in snapshot.items())
        assert all(digest(folder / name) == value for name, value in hashes.items())
        verify_audio(jobs, resumed)
        evidence['recovery'] = {'id': resumed['id'], 'provider': resumed['engine']['provider'],
                                'voice': resumed['voice'], 'total': resumed['total'],
                                'saved_sections': len(hashes), 'position': resumed['position']}
        print('British speech, cache hits, cancellation/restart and saved section hashes passed.', flush=True)
        evidence['success'] = True
        return evidence
    finally:
        jobs.close()
        server.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', choices=['cpu', 'gpu'], default='cpu')
    parser.add_argument('--full-document', action='store_true')
    parser.add_argument('--allow-spacing', action='store_true', help='Verify whitespace-only content changes instead of identical old chunks.')
    parser.add_argument('--models', type=Path, default=ROOT / '.app-data/models')
    arguments = parser.parse_args()
    arguments.output = arguments.output.resolve()
    arguments.output.mkdir(parents=True, exist_ok=False)
    if arguments.device == 'gpu':
        os.environ['VIOLILT_GPU_RUNTIME'] = str(ROOT / '.cuda-probe')
    result = integration(arguments)
    (arguments.output / 'results.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
