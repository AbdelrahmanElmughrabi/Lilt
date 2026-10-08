import tempfile
import threading
import unittest
import uuid
from pathlib import Path

from backend.bridge import Bridge
from backend.jobs import Jobs
from backend.storage import Store


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
        audio.write_bytes(b'test audio content')
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


if __name__ == '__main__':
    unittest.main()
