import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

from backend.bridge import Bridge
from backend.jobs import Jobs
from backend.storage import Store
from tests.test_pcm_audio import pcm


class Dialogs:
    def __init__(self, path, confirmation=True):
        self.path, self.confirmation = path, confirmation

    def create_file_dialog(self, *_args, **_kwargs):
        return (str(self.path),)

    def create_confirmation_dialog(self, *_args):
        return self.confirmation


class IdleJobs:
    lock = threading.RLock()

    def state(self):
        return None


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'data')
        self.bridge = Bridge(self.store, None, IdleJobs())

    def tearDown(self):
        self.temp.cleanup()

    def recording(self):
        key = uuid.uuid4().hex
        directory = self.store.root / 'jobs' / key
        directory.mkdir()
        audio = directory / 'recording.wav'
        audio.write_bytes(pcm())
        self.store.put('jobs', {'id': key, 'state': 'completed', 'title': 'A reading', 'duration': 12})
        return key, audio

    def test_import_handles_utf8_bom_without_changing_original(self):
        source = self.root / 'reading.md'
        source.write_text('# My reading\n\nHello.', encoding='utf-8-sig')
        original = source.read_bytes()
        self.bridge._window = Dialogs(source)
        document = self.bridge.import_document()
        self.bridge.save_document(document['id'], '# A new title')
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(document['title'], 'My reading')

    def test_export_copies_complete_recording_and_adds_wav_extension(self):
        key, source = self.recording()
        target = self.root / 'export'
        self.bridge._window = Dialogs(target)
        result = Path(self.bridge.export_recording(key))
        self.assertEqual(result.suffix, '.wav')
        self.assertEqual(result.read_bytes(), source.read_bytes())

    def test_export_rejects_unsupported_audio_without_replacing_existing_file(self):
        key, source = self.recording()
        source.write_bytes(b'FORM' + bytes(60))
        target = self.root / 'export.wav'; target.write_bytes(b'previous complete export')
        self.bridge._window = Dialogs(target)
        with self.assertRaisesRegex(ValueError, 'supported PCM WAV'):
            self.bridge.export_recording(key)
        self.assertEqual(target.read_bytes(), b'previous complete export')
        self.assertEqual(source.read_bytes(), b'FORM' + bytes(60))
        self.assertEqual(list(self.root.glob('.violilt-export-*')), [])

    def test_drop_imports_multiple_files_preserves_sources_and_skips_duplicates(self):
        first, second = self.root / 'one.MD', self.root / 'two.markdown'
        first.write_text('# First\n\nHello.', encoding='utf-8-sig')
        second.write_text('# Second\n\nMore words.', encoding='utf-8')
        originals = [first.read_bytes(), second.read_bytes()]
        result = self.bridge.import_dropped_documents([str(first), str(second), str(first)])
        self.assertEqual(result['errors'], [])
        self.assertEqual([doc['title'] for doc in result['documents']], ['First', 'Second'])
        self.assertEqual([doc['source'] for doc in result['documents']], [str(first), str(second)])
        self.assertEqual([first.read_bytes(), second.read_bytes()], originals)

    def test_drop_reports_invalid_files_without_losing_valid_readings(self):
        valid, invalid, wrong = self.root / 'good.md', self.root / 'bad.md', self.root / 'audio.wav'
        valid.write_text('# Good', encoding='utf-8')
        invalid.write_bytes(b'\xff\xfe\x00')
        wrong.write_bytes(b'not markdown')
        folder = self.root / 'folder.md'
        folder.mkdir()
        result = self.bridge.import_dropped_documents([str(valid), str(invalid), str(wrong), str(folder), str(self.root / 'missing.md')])
        self.assertEqual(len(result['documents']), 1)
        self.assertEqual(result['documents'][0]['title'], 'Good')
        self.assertEqual(len(result['errors']), 4)
        self.assertIn('UTF-8', result['errors'][0]['message'])
        self.assertEqual(len(self.store.all('documents')), 1)

    def test_drop_requires_a_nonempty_list(self):
        for value in ([], None, 'one.md'):
            with self.assertRaises(ValueError):
                self.bridge.import_dropped_documents(value)

    def test_existing_export_is_not_replaced_when_confirmation_is_declined(self):
        key, _ = self.recording()
        target = self.root / 'existing.wav'
        target.write_bytes(b'keep this')
        self.bridge._window = Dialogs(target, confirmation=False)
        self.assertIsNone(self.bridge.export_recording(key))
        self.assertEqual(target.read_bytes(), b'keep this')

    def test_removing_record_retains_audio_unless_deletion_is_selected(self):
        first, retained = self.recording()
        second, deleted = self.recording()
        self.bridge.remove_recording(first)
        self.bridge.remove_recording(second, delete_audio=True)
        self.assertTrue(retained.exists())
        self.assertFalse(deleted.exists())
        self.assertEqual(self.store.all('jobs'), [])

    def test_removing_working_copy_keeps_original_and_recordings(self):
        source = self.root / 'original.md'
        source.write_text('# Original', encoding='utf-8')
        document = self.store.document('# Original', 'Original', str(source))
        _, audio = self.recording()
        self.bridge.remove_document(document['id'])
        self.assertTrue(source.exists())
        self.assertTrue(audio.exists())
        self.assertEqual(self.store.all('documents'), [])

    def test_restart_marks_unfinished_jobs_as_interrupted(self):
        key = uuid.uuid4().hex
        self.store.put('jobs', {'id': key, 'state': 'generating'})
        jobs = Jobs(self.store, None)
        try:
            self.assertEqual(self.store.get('jobs', key)['state'], 'interrupted')
            self.assertIsNone(jobs.state())
        finally:
            jobs.close()

    @patch('backend.bridge.select_file')
    def test_reveal_imported_markdown_selects_original_path(self, select):
        source = self.root / 'notes, with spaces & symbols.md'
        source.write_text('# Original', encoding='utf-8')
        document = self.store.document('# Changed working copy', 'Changed', str(source))
        self.assertTrue(self.bridge.reveal_document(document['id']))
        select.assert_called_once_with(source)
        self.assertEqual(source.read_text(encoding='utf-8'), '# Original')

    @patch('backend.bridge.subprocess.Popen')
    def test_reveal_rejects_missing_source_or_file(self, launch):
        for source in (None, str(self.root / 'gone.md'), str(self.root)):
            document = self.store.document('# Reading', 'Reading', source)
            with self.assertRaises(ValueError):
                self.bridge.reveal_document(document['id'])
        with self.assertRaises(ValueError):
            self.bridge.reveal_document('unknown')
        launch.assert_not_called()

    @patch('backend.bridge.subprocess.Popen')
    @patch('backend.bridge.select_file')
    def test_reveal_recording_selects_wav_and_unfinished_opens_folder(self, select, launch):
        key, audio = self.recording()
        self.bridge.reveal_recording(key)
        select.assert_called_once_with(audio)
        launch.assert_not_called()
        job = self.store.get('jobs', key)
        job['state'] = 'cancelled'
        self.store.put('jobs', job)
        self.bridge.reveal_recording(key)
        self.assertNotIn('/select,', launch.call_args.args[0])
        self.assertIn(str(audio.parent), launch.call_args.args[0])
        self.assertFalse(launch.call_args.kwargs['shell'])
        select.assert_called_once()

    @patch('backend.bridge.subprocess.Popen')
    def test_reveal_recording_rejects_missing_output_and_path_escape(self, launch):
        key, audio = self.recording()
        audio.unlink()
        with self.assertRaises(ValueError):
            self.bridge.reveal_recording(key)
        self.store.put('jobs', {'id': '../outside', 'state': 'cancelled'})
        with self.assertRaises(ValueError):
            self.bridge.reveal_recording('../outside')
        self.store.put('jobs', {'id': 'no-output', 'state': 'cancelled'})
        with self.assertRaises(ValueError):
            self.bridge.reveal_recording('no-output')
        launch.assert_not_called()

    @patch('backend.bridge.select_file', side_effect=OSError('unavailable'))
    def test_reveal_reports_explorer_launch_failure(self, _launch):
        key, _ = self.recording()
        with self.assertRaisesRegex(ValueError, 'File Explorer could not be opened'):
            self.bridge.reveal_recording(key)

    def test_home_recent_readings_use_open_time_instead_of_last_edit(self):
        models, jobs = Mock(), Mock()
        models.status.return_value = {'state': 'missing'}
        jobs.state.return_value = None
        jobs.performance_state.return_value = None
        jobs.cache_state.return_value = {}
        bridge = Bridge(self.store, models, jobs)
        with patch('backend.storage.time.time', return_value=100):
            first = self.store.document('# First', 'First', 'C:/notes/first.md')
        with patch('backend.storage.time.time', return_value=200):
            second = self.store.document('# Second', 'Second')
        with patch('backend.storage.time.time', return_value=300):
            bridge.get_document(first['id'])
        with patch('backend.storage.time.time', return_value=400):
            bridge.save_document(second['id'], '# An edit')
        state = bridge.get_state()
        self.assertEqual([doc['id'] for doc in state['documents']], [first['id'], second['id']])
        self.assertEqual(state['documents'][0]['source'], 'C:/notes/first.md')
        self.assertNotIn('markdown', state['documents'][0])


if __name__ == '__main__':
    unittest.main()
