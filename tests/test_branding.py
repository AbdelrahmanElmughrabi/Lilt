import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from backend.bridge import Bridge
from backend.jobs import Jobs
from backend.storage import Store, data_directory, import_library


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
        legacy = Store(self.root / 'PreviousBrand')
        document = legacy.document('# My words', 'My words')
        key = uuid.uuid4().hex
        legacy.put('jobs', {'id': key, 'state': 'completed', 'position': 12.5})
        for name in (f'jobs/{key}/recording.wav', f'jobs/{key}/section-000000.wav', 'models/voices.bin', 'section-cache/speech.wav'):
            file = legacy.root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'unchanged content')
        legacy.save_settings({'theme': 'dark', 'voice': 'bf_emma', 'speed': 1.2, 'cpu_threads': 2})
        with patch.dict(os.environ, {'VIOLILT_IMPORT_DATA_DIR': str(legacy.root)}):
            migrated = Store(data_directory())
        self.assertEqual(migrated.root, self.root / 'Violilt')
        self.assertEqual(migrated.get('documents', document['id']), document)
        self.assertEqual(migrated.get('jobs', key)['position'], 12.5)
        self.assertEqual(migrated.settings()['theme'], 'dark')
        self.assertEqual(migrated.settings()['palette'], 'violilt')
        self.assertEqual(migrated.settings()['cpu_threads'], 2)
        for file in legacy.root.rglob('*'):
            if file.is_file() and file.name != 'library.sqlite3' and not file.name.endswith('-instance.lock'):
                self.assertEqual(file.read_bytes(), (migrated.root / file.relative_to(legacy.root)).read_bytes())
        self.assertTrue((legacy.root / 'library.sqlite3').exists())
        migrated.save_settings({'palette': 'classic'})
        self.assertEqual(Store(data_directory()).settings()['palette'], 'classic')

    def test_existing_violilt_library_wins_and_overrides_do_not_migrate(self):
        Store(self.root / 'PreviousBrand').document('# Old', 'Old')
        current = Store(self.root / 'Violilt')
        current.document('# Current', 'Current')
        self.assertEqual(Store(data_directory()).all('documents')[0]['title'], 'Current')
        with patch.dict(os.environ, {'VIOLILT_IMPORT_DATA_DIR': str(self.root / 'PreviousBrand')}):
            self.assertEqual(data_directory(), self.root / 'Violilt')
            with patch.dict(os.environ, {'VIOLILT_DATA_DIR': str(self.root / 'new-override')}):
                self.assertEqual(data_directory(), self.root / 'new-override')

    def test_failed_migration_does_not_publish_partial_data_or_change_original(self):
        legacy = Store(self.root / 'PreviousBrand')
        legacy.document('# Keep me', 'Keep me')
        (legacy.root / 'models/voice.bin').write_bytes(b'voice')
        before = legacy.db.read_bytes()
        with patch.dict(os.environ, {'VIOLILT_IMPORT_DATA_DIR': str(legacy.root)}), patch('backend.storage.shutil.copytree', side_effect=OSError('simulated failure')):
            with self.assertRaises(OSError):
                data_directory()
        self.assertFalse((self.root / 'Violilt').exists())
        self.assertEqual(legacy.db.read_bytes(), before)
        self.assertFalse(list(self.root.glob('.violilt-migration-*')))

    def test_migrated_partial_job_survives_restart(self):
        legacy = Store(self.root / 'PreviousBrand')
        key = uuid.uuid4().hex
        legacy.put('jobs', {'id': key, 'state': 'generating', 'position': 3, 'completed': 1})
        folder = legacy.root / 'jobs' / key
        folder.mkdir()
        (folder / 'section-000000.wav').write_bytes(b'checkpoint')
        with patch.dict(os.environ, {'VIOLILT_IMPORT_DATA_DIR': str(legacy.root)}):
            migrated = Store(data_directory())
        jobs = Jobs(migrated, None)
        try:
            self.assertEqual(migrated.get('jobs', key)['state'], 'interrupted')
            self.assertEqual(migrated.get('jobs', key)['position'], 3)
            self.assertEqual((migrated.root / 'jobs' / key / 'section-000000.wav').read_bytes(), b'checkpoint')
        finally:
            jobs.close()

    def test_preexisting_incomplete_destination_is_not_overwritten(self):
        previous = Store(self.root / 'PreviousBrand')
        previous.document('# Keep me', 'Keep me')
        destination = self.root / 'Violilt'
        destination.mkdir()
        marker = destination / 'keep.txt'
        marker.write_text('keep')
        with patch.dict(os.environ, {'VIOLILT_IMPORT_DATA_DIR': str(previous.root)}), self.assertRaises(FileExistsError):
            data_directory()
        self.assertEqual(marker.read_text(), 'keep')

    def test_palette_validation_and_appearance_persist_independently(self):
        store = Store(self.root / 'data')
        bridge = Bridge(store, None, None)
        bridge.save_settings({'theme': 'system', 'palette': 'classic'})
        bridge.save_settings({'palette': 'violilt'})
        saved = Store(store.root).settings()
        self.assertEqual(saved['theme'], 'system')
        self.assertEqual(saved['palette'], 'violilt')
        with self.assertRaises(ValueError):
            bridge.save_settings({'palette': 'unknown'})

    def test_import_normalizes_previous_palette_and_excludes_process_files(self):
        previous = Store(self.root / 'PreviousBrand')
        previous.save_settings({'theme': 'dark'})
        # Simulate a historical value; the current write API rejects it.
        with previous.connect() as connection:
            connection.execute("INSERT INTO settings VALUES ('palette', '\"previous-brand\"')")
        (previous.root / 'previous-brand.log').write_text('old log')
        (previous.root / '.previous-instance.lock').write_bytes(b'lock')
        browser = previous.root / 'webview'
        browser.mkdir()
        (browser / 'cache').write_bytes(b'old browser data')
        imported = Store(import_library(previous.root, self.root / 'Violilt'))
        self.assertEqual(imported.settings()['palette'], 'violilt')
        self.assertEqual(imported.settings()['theme'], 'dark')
        self.assertFalse((imported.root / 'webview').exists())
        self.assertFalse(list(imported.root.glob('*.log')))
        self.assertFalse(list(imported.root.glob('.*-instance.lock')))
        self.assertEqual(previous.settings()['theme'], 'dark')
        with previous.connect() as connection:
            self.assertEqual(connection.execute("SELECT value FROM settings WHERE key = 'palette'").fetchone()[0], '"previous-brand"')

    def test_import_rejects_missing_overlapping_and_existing_destinations(self):
        previous = Store(self.root / 'PreviousBrand')
        for source, destination in ((self.root / 'missing', self.root / 'Violilt'),
                                    (previous.root, previous.root),
                                    (previous.root, previous.root / 'nested'),
                                    (previous.root, self.root)):
            with self.subTest(source=source, destination=destination), self.assertRaises(ValueError):
                import_library(source, destination)
        current = Store(self.root / 'Violilt')
        current.document('# Keep', 'Keep')
        with self.assertRaises(FileExistsError):
            import_library(previous.root, current.root)
        self.assertEqual(current.all('documents')[0]['title'], 'Keep')


if __name__ == '__main__':
    unittest.main()
