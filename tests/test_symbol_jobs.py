import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
from backend.pcm_audio import audio_info, write_pcm16

from backend.cache import section_key
from backend.documents import prepare
from backend.jobs import Jobs, public_job
from backend.models import FILES
from backend.storage import Store


class UnreadReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'data')
        self.jobs = Jobs(self.store, None)
        model_folder = self.root / 'models'
        model_folder.mkdir()
        for name in FILES:
            (model_folder / name).write_bytes(b'fixture model')
        self.jobs.models = SimpleNamespace(root=model_folder, status=lambda: {'state': 'ready', 'voices': ['af_heart']})
        self.jobs.performance = SimpleNamespace(resolve=Mock(return_value={
            'model': str(model_folder / FILES[0]), 'provider': 'CPUExecutionProvider'}),
            gpu_runtime=None, runtime='fixture')
        self.jobs._worker = Mock()

    def tearDown(self):
        self.jobs.close()
        self.temp.cleanup()

    def start(self, markdown):
        prepared = prepare(markdown)
        doc = self.store.document(markdown, prepared['title'])
        created = self.jobs.start(prepared, doc, 'af_heart', 1)
        command = self.jobs.commands.get(timeout=2)
        return prepared, doc, command['job'], created

    def interrupt(self, job):
        job.update(state='interrupted')
        self.store.put('jobs', job)
        self.jobs.active = None

    def report(self, job):
        return self.store.root / 'jobs' / job['id'] / 'unread.txt'

    def test_report_is_present_before_worker_and_snapshot_does_not_follow_edits(self):
        prepared, doc, job, created = self.start('# Original ➔ title\n\nA➔B 🦊 C. Next sentence.')
        report = self.report(job).read_text(encoding='utf-8')
        self.assertIn('"🦊" (U+1F98A)', report)
        self.assertNotIn('U+2794', report)
        self.assertEqual(created['unread_count'], 1)
        self.assertNotIn('unread_symbols', created)
        self.assertEqual(job['markdown'], doc['markdown'])
        self.assertEqual(job['title'], 'Original ➔ title')
        self.assertEqual(job['chunks'][-1]['text'], 'A right arrow B C. Next sentence.')
        prepared['unread_symbols'].append('🐙')
        self.assertEqual(self.jobs.active['unread_symbols'], ['🦊'])
        self.assertEqual(self.store.get('jobs', job['id'])['unread_symbols'], ['🦊'])
        self.assertEqual(self.report(job).read_text(encoding='utf-8'), report)

    def test_shared_audio_key_has_separate_original_unread_reports(self):
        _, _, first, _ = self.start('Hello 🦊 world.')
        self.interrupt(first)
        _, _, second, _ = self.start('Hello 🐙 world.')
        keys = [section_key(j['chunks'][0]['text'], j['voice'], j['speed'], j['audio_identity'])
                for j in (first, second)]
        self.assertEqual(keys[0], keys[1])
        first_audio = self.report(first).parent / 'section-000000.wav'
        write_pcm16(first_audio, np.full(1000, .1), 24000)
        self.jobs.cache.put(keys[0], first_audio)
        self.assertTrue(self.jobs.cache.fetch(keys[1], self.report(second).parent / 'section-000000.wav'))
        self.assertIn('🦊', self.report(first).read_text(encoding='utf-8'))
        self.assertNotIn('🐙', self.report(first).read_text(encoding='utf-8'))
        self.assertIn('🐙', self.report(second).read_text(encoding='utf-8'))
        self.assertNotIn('🦊', self.report(second).read_text(encoding='utf-8'))

    def test_resume_recreates_report_from_saved_list_and_never_duplicates(self):
        prepared, doc, job, _ = self.start('First 🦊 sentence. Next 🦊 sentence.')
        snapshot = copy.deepcopy(job['chunks'])
        original_report = self.report(job).read_bytes()
        self.interrupt(job)
        self.report(job).unlink()
        prepared['unread_symbols'] = ['🐙']
        prepared['chunks'].reverse()
        for _ in range(2):
            self.jobs.start(prepared, doc, 'af_heart', 1, resume=job['id'])
            resumed = self.jobs.commands.get(timeout=2)['job']
            self.assertEqual(resumed['unread_symbols'], ['🦊', '🦊'])
            self.assertEqual(resumed['chunks'], snapshot)
            self.assertEqual(self.report(job).read_bytes(), original_report)
            self.interrupt(resumed)

    def test_report_failure_does_not_dispatch_inference(self):
        prepared = prepare('Hello 🦊 world.')
        doc = self.store.document('Hello 🦊 world.', 'Original')
        with patch.object(self.jobs, '_write_unread', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(ValueError, 'Could not save unread.txt'):
                self.jobs.start(prepared, doc, 'af_heart', 1)
        self.jobs._worker.assert_not_called()
        self.assertIsNone(self.jobs.active)
        self.assertEqual(self.store.all('jobs')[0]['state'], 'failed')
        self.assertEqual(self.store.all('jobs')[0]['unread_symbols'], ['🦊'])

    def test_report_records_compound_symbols_and_controls_safely(self):
        _, _, job, _ = self.start('one👨‍👩‍👧two')
        job['unread_symbols'].append('\x00')
        self.jobs._write_unread(job)
        report = self.report(job).read_text(encoding='utf-8')
        self.assertIn('U+1F468 U+200D U+1F469 U+200D U+1F467', report)
        self.assertIn('"\\u0000" (U+0000)', report)
        self.assertNotIn('\x00', report)

    def test_all_unread_document_starts_no_job(self):
        prepared = prepare('🦊')
        doc = self.store.document('🦊', 'Original')
        with self.assertRaisesRegex(ValueError, 'no readable text'):
            self.jobs.start(prepared, doc, 'af_heart', 1)
        self.jobs._worker.assert_not_called()
        self.assertEqual(self.store.all('jobs'), [])

    def test_old_recording_defaults_to_no_report_without_mutation(self):
        old = {'id': 'a' * 32, 'state': 'completed'}
        self.assertEqual(public_job(old)['unread_count'], 0)
        self.assertEqual(old, {'id': 'a' * 32, 'state': 'completed'})


if __name__ == '__main__':
    unittest.main()
