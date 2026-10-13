"""Verify symbol preparation, real audio, cache and recovery in a new library."""
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
    from backend.jobs import Jobs, public_job
    from backend.models import Models
    from backend.server import AppServer
    from backend.storage import Store

    store = Store(arguments.output / 'data')
    jobs = Jobs(store, Models(arguments.models))
    server = AppServer(ROOT / 'frontend/dist', store)
    server.start()
    evidence = {}
    try:
        store.save_settings({'processing_device': arguments.device, 'performance_mode': 'quiet',
                             'cache_enabled': True})
        markdown = '# Symbol ➔ reading\n\n' + '\n\n'.join(
            f'Passage {i + 1}. Before➔middle 🦊 after. Next sentence stays. '
            'The room is 20°C. Two × three is six. one👨‍👩‍👧two. Every word stays in its place.'
            for i in range(6))
        prepared = prepare(markdown)
        assert 'Before right arrow middle after. Next sentence stays.' in prepared['text']
        assert 'one two' in prepared['text']
        assert prepared['unread_symbols'] == ['🦊', '👨‍👩‍👧'] * 6
        document = store.document(markdown, prepared['title'])
        evidence['preparation'] = {'original': markdown, 'spoken': prepared['text'],
                                   'unread': prepared['unread_symbols']}

        def early(job):
            stream = jobs.stream(job['id'])
            assert stream['available'] > 0 and stream['sections'] and not stream['complete']
            request = urllib.request.Request(server.url + f"/media/{job['id']}/section-000000.wav",
                                             headers={'Range': 'bytes=0-63'})
            with urllib.request.urlopen(request) as response:
                assert response.status == 206 and len(response.read()) == 64
            evidence['early_audio'] = {'available': stream['available'], 'state': job['state']}

        first = wait_job(jobs, jobs.start(prepared, document, 'af_heart', 1)['id'], early)
        first_digest = verify_audio(jobs, first)
        assert store.get('documents', document['id'])['markdown'] == markdown
        assert first['title'] == 'Symbol ➔ reading'
        assert first['markdown'] == markdown
        assert public_job(first)['unread_count'] == 12
        first_report = (store.root / 'jobs' / first['id'] / 'unread.txt').read_text(encoding='utf-8')
        assert first_report.count('"🦊"') == 6
        evidence['first'] = {'id': first['id'], 'engine': first['engine'], 'sections': first['total'],
                             'first_audio_seconds': first['first_audio_seconds'], 'throughput': first['throughput'],
                             'audio_sha256': first_digest}

        # Both originals have identical speech. Their unread lists stay local.
        alternate = markdown.replace('🦊', '🐙')
        second_doc = store.document(alternate, prepared['title'])
        second = wait_job(jobs, jobs.start(prepare(alternate), second_doc, 'af_heart', 1)['id'])
        assert second['cache_hits'] == second['total'] and second['generated_sections'] == 0
        assert verify_audio(jobs, second) == first_digest
        second_report = (store.root / 'jobs' / second['id'] / 'unread.txt').read_text(encoding='utf-8')
        assert '🐙' in second_report and '🦊' not in second_report
        assert '🐙' not in first_report
        evidence['cache'] = {'id': second['id'], 'hits': second['cache_hits'],
                             'total': second['total'], 'distinct_reports': True}
        print('Real symbol speech, early ranged audio and cached speech/report separation passed.', flush=True)

        store.save_settings({'cache_enabled': False})
        interrupted = wait_job(jobs, jobs.start(prepared, document, 'bf_emma', 1)['id'], lambda job: jobs.stop())
        assert interrupted['state'] == 'cancelled' and 0 < interrupted['completed'] < interrupted['total']
        folder = store.root / 'jobs' / interrupted['id']
        before = {path.name: digest(path) for path in folder.glob('section-*.wav')}
        fields = ('chunks', 'options', 'voice', 'speed', 'markdown', 'pronunciation_identity',
                  'audio_identity', 'unread_symbols')
        snapshot = {key: copy.deepcopy(interrupted[key]) for key in fields}
        report_before = (folder / 'unread.txt').read_bytes()
        jobs.save_position(interrupted['id'], .5)
        jobs.close()
        (folder / 'unread.txt').unlink()
        jobs = Jobs(store, Models(arguments.models))
        resumed = wait_job(jobs, jobs.start(prepare(interrupted['markdown'], interrupted['options']),
                                          document, 'bf_emma', 1, resume=interrupted['id'])['id'])
        assert resumed['state'] == 'completed' and resumed['position'] == .5
        assert all(resumed[key] == value for key, value in snapshot.items())
        assert all(digest(folder / name) == value for name, value in before.items())
        assert (folder / 'unread.txt').read_bytes() == report_before
        verify_audio(jobs, resumed)
        evidence['recovery'] = {'id': resumed['id'], 'saved_sections': len(before), 'total': resumed['total'],
                                'position': resumed['position'], 'report_recreated': True}
        print('British speech, cancellation, restart, checkpoints and unread report reconstruction passed.', flush=True)
        return evidence
    finally:
        jobs.close()
        server.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--models', type=Path, default=ROOT / '.app-data/models')
    parser.add_argument('--runtime', type=Path, default=ROOT / '.cuda-probe')
    parser.add_argument('--device', choices=['cpu', 'gpu'], default='cpu')
    arguments = parser.parse_args()
    arguments.output = arguments.output.resolve()
    if arguments.output.exists():
        raise ValueError('Use a new evidence directory; existing libraries and recordings are never overwritten.')
    arguments.output.mkdir(parents=True)
    if arguments.device == 'gpu':
        os.environ['LILT_GPU_RUNTIME_DIR'] = str(arguments.runtime.resolve())
    evidence = integration(arguments)
    (arguments.output / 'results.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'success': True, 'evidence': str(arguments.output / 'results.json')}), flush=True)


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
