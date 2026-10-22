import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.bridge import Bridge
from backend.documents import prepare
from backend.limits import MAX_FILE_BATCH, MAX_MARKDOWN_BYTES
from backend.performance import Performance
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

    def test_huge_numeric_preferences_reject_the_whole_public_update(self):
        for key in ('speed', 'heading_pause', 'paragraph_pause', 'cpu_threads'):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    self.bridge.save_settings({'theme': 'dark', key: 10 ** 400})
                self.assertEqual(self.store.settings()['theme'], 'light')

    def test_huge_saved_preferences_use_defaults_and_preserve_raw_rows(self):
        self.store.save_settings({'theme': 'dark'})
        keys = ('speed', 'heading_pause', 'paragraph_pause', 'cpu_threads')
        raw = str(10 ** 400)
        with self.store.connect() as connection:
            connection.executemany('INSERT INTO settings VALUES (?, ?)', [(key, raw) for key in keys])
        saved = self.store.settings()
        self.assertEqual(saved['theme'], 'dark')
        for key, expected in zip(keys, (1.0, 0.6, 0.3, 0)):
            self.assertEqual(saved[key], expected)
        self.assertEqual(self.store.recovery_summary()['count'], len(keys))
        self.store.settings()
        self.assertEqual(self.store.recovery_summary()['count'], len(keys))
        with self.store.connect() as connection:
            for key in keys:
                self.assertEqual(connection.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()[0], raw)

    def _assert_record_is_recovered(self, table, invalid):
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            store = Store(Path(directory))
            reading = store.document('# Keep these words', 'Healthy')
            recording = {'id': 'healthy-job', 'state': 'completed', 'title': 'Healthy recording',
                         'voice': 'af_heart', 'speed': 1.0, 'created': 100, 'duration': 1,
                         'position': 0, 'completed': 1, 'total': 1, 'preview': False}
            store.put('jobs', recording)
            original = reading if table == 'documents' else recording
            broken = original | {'id': 'broken'} | invalid
            raw = json.dumps(broken)
            with store.connect() as connection:
                connection.execute(f'INSERT INTO {table} VALUES (?, ?, ?)', ('broken', raw, 200))
            folder = store.root / 'jobs' / 'broken'
            folder.mkdir()
            audio = folder / 'recording.wav'
            audio.write_bytes(b'preserve disposable saved audio')
            jobs = SimpleNamespace(state=lambda: None, performance_state=lambda: None, cache_state=lambda: {})
            models = SimpleNamespace(status=lambda: {'state': 'missing', 'voices': []})
            bridge = Bridge(store, models, jobs)
            state = bridge.get_state()
            self.assertEqual([item['id'] for item in state['documents']], [reading['id']])
            self.assertEqual([item['id'] for item in state['jobs']], [recording['id']])
            self.assertEqual(state['recovery']['count'], 1)
            self.assertTrue(state['recovery']['message'])
            self.assertEqual(bridge.get_state()['recovery']['count'], 1)
            with self.assertRaisesRegex(ValueError, 'needs recovery'):
                store.get(table, 'broken')
            with store.connect() as connection:
                self.assertEqual(connection.execute(f'SELECT body FROM {table} WHERE id=?', ('broken',)).fetchone()[0], raw)
                self.assertEqual(connection.execute('SELECT body FROM recovery_rows').fetchone()[0], raw)
            self.assertEqual(audio.read_bytes(), b'preserve disposable saved audio')
            self.assertEqual(store.get('documents', reading['id']), reading)
            self.assertEqual(store.get('jobs', recording['id']), recording)

    def test_bad_saved_document_metadata_does_not_break_library_state(self):
        for invalid in ({'opened': [1]}, {'opened': 'yesterday'}, {'opened': False},
                        {'opened': float('nan')}, {'created': 10 ** 400}, {'source': ['not a path']}):
            with self.subTest(invalid=invalid):
                self._assert_record_is_recovered('documents', invalid)

    def test_bad_saved_job_fields_do_not_break_library_state(self):
        for invalid in ({'unread_symbols': None}, {'unread_symbols': [None]},
                        {'pronunciation_warnings': 'not a list'}, {'created': 'yesterday'},
                        {'position': []}, {'speed': 'fast'}, {'title': None},
                        {'duration': float('inf')}, {'completed': '1'}, {'preview': 1},
                        {'chunks': [{'text': [], 'pause': 0}]},
                        {'sections': [{'index': 0, 'start': 0, 'duration': 'bad', 'pause': 0}]},
                        {'engine': []}, {'options': {'heading_pause': 10 ** 400}}):
            with self.subTest(invalid=invalid):
                self._assert_record_is_recovered('jobs', invalid)

    def _invalid_benchmarks(self):
        valid = {'identity': 'fixture', 'cpu': {'threads': 1},
                 'best': {'provider': 'CPUExecutionProvider', 'threads': 1}}
        return [valid | {'best': {'threads': 1}},
                valid | {'best': {'provider': 'CUDAExecutionProvider', 'threads': 1}},
                valid | {'best': {'provider': 'CUDAExecutionProvider', 'threads': 1, 'device_id': []}},
                valid | {'best': valid['best'] | {'throughput': 'fast'}},
                valid | {'best': valid['best'] | {'label': []}},
                valid | {'results': {}},
                valid | {'results': [valid['best'] | {'throughput': 'fast'}]},
                valid | {'created': 10 ** 400}]

    def test_invalid_benchmark_updates_are_rejected_before_writing(self):
        for benchmark in self._invalid_benchmarks():
            with self.subTest(benchmark=benchmark):
                with self.assertRaises(ValueError):
                    self.store.save_settings({'theme': 'dark', 'benchmark_result': benchmark})
                self.assertEqual(self.store.settings()['theme'], 'light')
                self.assertNotIn('benchmark_result', self.store.settings())

    def test_bad_saved_benchmarks_fall_back_to_cpu_and_preserve_raw_rows(self):
        self.store.save_settings({'theme': 'dark'})
        performance = Performance.__new__(Performance)
        performance.store, performance.models = self.store, SimpleNamespace(root=self.root / 'models')
        performance.physical = 4
        performance.identity = lambda: 'fixture'
        for benchmark in self._invalid_benchmarks():
            with self.subTest(benchmark=benchmark):
                raw = json.dumps(benchmark)
                with self.store.connect() as connection:
                    connection.execute('INSERT OR REPLACE INTO settings VALUES (?, ?)', ('benchmark_result', raw))
                saved = self.store.settings()
                self.assertEqual(saved['theme'], 'dark')
                self.assertNotIn('benchmark_result', saved)
                self.assertIsNone(performance.recommendation())
                self.assertEqual(performance.resolve(saved)['provider'], 'CPUExecutionProvider')
                with self.store.connect() as connection:
                    self.assertEqual(connection.execute("SELECT value FROM settings WHERE key='benchmark_result'").fetchone()[0], raw)
        self.assertEqual(self.store.recovery_summary()['count'], len(self._invalid_benchmarks()))
        # Keep valid CPU recommendations and GPU measurements usable; failed
        # benchmark candidates legitimately contain an error instead of timing.
        cpu = {'provider': 'CPUExecutionProvider', 'device_id': -1, 'threads': 1,
               'label': 'CPU', 'throughput': 2.0}
        gpu = {'provider': 'CUDAExecutionProvider', 'device_id': 0, 'threads': 2,
               'label': 'Fixture NVIDIA', 'throughput': 4.0}
        valid = {'identity': 'fixture', 'created': 100, 'cpu': cpu, 'best': gpu,
                 'results': [cpu, gpu, gpu | {'error': 'Fixture candidate failed'}]}
        self.store.save_settings({'benchmark_result': valid})
        performance.providers = ['CUDAExecutionProvider']
        performance.adapters = [{'id': 0, 'name': 'Fixture NVIDIA', 'memory_mb': 1024}]
        performance.models.gpu_verified = True
        self.assertEqual(performance.recommendation(), valid)
        self.assertEqual(performance.resolve(self.store.settings())['provider'], 'CUDAExecutionProvider')

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
