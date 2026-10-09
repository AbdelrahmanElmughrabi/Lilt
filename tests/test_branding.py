import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from backend.bridge import Bridge
from backend.jobs import Jobs
from backend.storage import Store, data_directory


class BrandingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.environment = patch.dict(os.environ, {'LOCALAPPDATA': str(self.root)}, clear=True)
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def test_migration_keeps_documents_recordings_models_cache_and_preferences(self):
        legacy = Store(self.root / 'Folio')
        document = legacy.document('# My words', 'My words')
        key = uuid.uuid4().hex
        legacy.put('jobs', {'id': key, 'state': 'completed', 'position': 12.5})
        for name in (f'jobs/{key}/recording.wav', f'jobs/{key}/section-000000.wav', 'models/voices.bin', 'section-cache/speech.wav'):
            file = legacy.root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'unchanged content')
        legacy.save_settings({'theme': 'dark', 'voice': 'bf_emma', 'speed': 1.2, 'cpu_threads': 2})
        migrated = Store(data_directory())
        self.assertEqual(migrated.root, self.root / 'Lilt')
        self.assertEqual(migrated.get('documents', document['id']), document)
        self.assertEqual(migrated.get('jobs', key)['position'], 12.5)
        self.assertEqual(migrated.settings()['theme'], 'dark')
        self.assertEqual(migrated.settings()['palette'], 'lilt')
        self.assertEqual(migrated.settings()['cpu_threads'], 2)
        for file in legacy.root.rglob('*'):
            if file.is_file() and file.name != 'library.sqlite3':
                self.assertEqual(file.read_bytes(), (migrated.root / file.relative_to(legacy.root)).read_bytes())
        self.assertTrue((legacy.root / 'library.sqlite3').exists())
        migrated.save_settings({'palette': 'classic'})
        self.assertEqual(Store(data_directory()).settings()['palette'], 'classic')

    def test_existing_lilt_library_wins_and_overrides_do_not_migrate(self):
        Store(self.root / 'Folio').document('# Old', 'Old')
        current = Store(self.root / 'Lilt')
        current.document('# Current', 'Current')
        self.assertEqual(Store(data_directory()).all('documents')[0]['title'], 'Current')
        with patch.dict(os.environ, {'FOLIO_DATA_DIR': str(self.root / 'legacy-override')}):
            self.assertEqual(data_directory(), self.root / 'legacy-override')
            with patch.dict(os.environ, {'LILT_DATA_DIR': str(self.root / 'new-override')}):
                self.assertEqual(data_directory(), self.root / 'new-override')

    def test_failed_migration_does_not_publish_partial_data_or_change_original(self):
        legacy = Store(self.root / 'Folio')
        legacy.document('# Keep me', 'Keep me')
        (legacy.root / 'models/voice.bin').write_bytes(b'voice')
        before = legacy.db.read_bytes()
        with patch('backend.storage.shutil.copytree', side_effect=OSError('simulated failure')):
            with self.assertRaises(OSError):
                data_directory()
        self.assertFalse((self.root / 'Lilt').exists())
        self.assertEqual(legacy.db.read_bytes(), before)
        self.assertFalse(list(self.root.glob('.lilt-migration-*')))

    def test_migrated_partial_job_survives_restart(self):
        legacy = Store(self.root / 'Folio')
        key = uuid.uuid4().hex
        legacy.put('jobs', {'id': key, 'state': 'generating', 'position': 3, 'completed': 1})
        folder = legacy.root / 'jobs' / key
        folder.mkdir()
        (folder / 'section-000000.wav').write_bytes(b'checkpoint')
        migrated = Store(data_directory())
        jobs = Jobs(migrated, None)
        try:
            self.assertEqual(migrated.get('jobs', key)['state'], 'interrupted')
            self.assertEqual(migrated.get('jobs', key)['position'], 3)
            self.assertEqual((migrated.root / 'jobs' / key / 'section-000000.wav').read_bytes(), b'checkpoint')
        finally:
            jobs.close()

    def test_preexisting_incomplete_destination_is_not_overwritten(self):
        Store(self.root / 'Folio').document('# Keep me', 'Keep me')
        destination = self.root / 'Lilt'
        destination.mkdir()
        marker = destination / 'keep.txt'
        marker.write_text('keep')
        with self.assertRaises(FileExistsError):
            data_directory()
        self.assertEqual(marker.read_text(), 'keep')

    def test_palette_validation_and_appearance_persist_independently(self):
        store = Store(self.root / 'data')
        bridge = Bridge(store, None, None)
        bridge.save_settings({'theme': 'system', 'palette': 'classic'})
        bridge.save_settings({'palette': 'lilt'})
        saved = Store(store.root).settings()
        self.assertEqual(saved['theme'], 'system')
        self.assertEqual(saved['palette'], 'lilt')
        with self.assertRaises(ValueError):
            bridge.save_settings({'palette': 'unknown'})


if __name__ == '__main__':
    unittest.main()
