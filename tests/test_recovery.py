import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from backend.bridge import Bridge
from backend.documents import prepare
from backend.limits import MAX_FILE_BATCH, MAX_MARKDOWN_BYTES
from backend.storage import SCHEMA_VERSION, Store, UnsupportedLibraryVersion


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = Store(self.root / 'data')
        self.bridge = Bridge(self.store, None, None)

    def tearDown(self):
        self.temporary.cleanup()

    def test_invalid_preferences_reject_the_whole_update(self):
        for invalid in ({'voice': None}, {'voice': '../voice'}, {'heading_pause': '0.6'},
                        {'include_code': 'false'}, {'paragraph_pause': float('nan')},
                        {'speed': True}, {'cpu_threads': float('inf')}, {'theme': []},
                        {'cache_limit_mb': 256.0}, {'unknown': True}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    self.bridge.save_settings({'theme': 'dark'} | invalid)
                self.assertEqual(self.store.settings()['theme'], 'light')

    def test_corrupt_preferences_preserve_raw_data_and_valid_preferences(self):
        self.store.save_settings({'theme': 'dark'})
        with self.store.connect() as connection:
            connection.executemany('INSERT INTO settings VALUES (?, ?)',
                                   [('voice', 'null'), ('heading_pause', '{broken')])
        settings = self.store.settings()
        self.assertEqual(settings['theme'], 'dark')
        self.assertEqual(settings['voice'], 'af_heart')
        self.assertEqual(settings['heading_pause'], 0.6)
        self.assertEqual(self.store.recovery_summary()['count'], 2)
        self.store.settings()
        self.assertEqual(self.store.recovery_summary()['count'], 2)
        with self.store.connect() as connection:
            self.assertEqual(connection.execute("SELECT value FROM settings WHERE key='heading_pause'").fetchone()[0], '{broken')
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM recovery_rows').fetchone()[0], 2)

    def test_corrupt_record_does_not_hide_healthy_readings_or_delete_original(self):
        healthy = self.store.document('# Keep these words', 'Keep')
        with self.store.connect() as connection:
            connection.execute('INSERT INTO documents VALUES (?, ?, ?)', ('broken', '{invalid', 1))
        self.assertEqual(self.store.all('documents'), [healthy])
        with self.assertRaisesRegex(ValueError, 'needs recovery'):
            self.store.get('documents', 'broken')
        self.assertEqual(self.store.recovery_summary()['count'], 1)
        with self.store.connect() as connection:
            self.assertEqual(connection.execute("SELECT body FROM documents WHERE id='broken'").fetchone()[0], '{invalid')

    def test_unversioned_database_is_backed_up_before_migration(self):
        root = self.root / 'legacy'
        root.mkdir()
        with closing(sqlite3.connect(root / 'library.sqlite3')) as connection, connection:
            connection.execute('CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            connection.execute('INSERT INTO settings VALUES (?, ?)', ('theme', json.dumps('dark')))
        migrated = Store(root)
        self.assertEqual(migrated.settings()['theme'], 'dark')
        backups = list((root / 'backups').glob('*.sqlite3'))
        self.assertEqual(len(backups), 1)
        with closing(sqlite3.connect(backups[0])) as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT value FROM settings WHERE key='theme'").fetchone()[0], '"dark"')
        with migrated.connect() as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], SCHEMA_VERSION)
        Store(root)
        self.assertEqual(len(list((root / 'backups').glob('*.sqlite3'))), 1)

    def test_newer_schema_is_rejected_without_changing_database(self):
        with self.store.connect() as connection:
            connection.execute(f'PRAGMA user_version = {SCHEMA_VERSION + 1}')
        before = self.store.db.read_bytes()
        with self.assertRaises(UnsupportedLibraryVersion):
            Store(self.store.root)
        self.assertEqual(self.store.db.read_bytes(), before)

    def test_failed_backup_prevents_migration(self):
        with self.store.connect() as connection:
            connection.execute('PRAGMA user_version = 0')
        before = self.store.db.read_bytes()
        with patch.object(Store, '_backup', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                Store(self.store.root)
        self.assertEqual(self.store.db.read_bytes(), before)

    def test_limits_apply_before_parser_or_import_mutation(self):
        source = self.root / 'large.md'
        source.write_bytes(b'x' * (MAX_MARKDOWN_BYTES + 1))
        with self.assertRaisesRegex(ValueError, '2 MB'):
            self.bridge._import_document_path(source)
        with self.assertRaises(ValueError):
            self.bridge.import_dropped_documents([str(source)] * (MAX_FILE_BATCH + 1))
        with self.assertRaises(ValueError):
            prepare('x' * (MAX_MARKDOWN_BYTES + 1))
        with self.assertRaises(ValueError):
            prepare('hello', {'include_code': 'false'})
        self.assertEqual(self.store.all('documents'), [])
