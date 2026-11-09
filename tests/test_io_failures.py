"""Disposable storage fault injection; never fills disks or changes real ACLs."""
import copy
import queue
import sqlite3
import tempfile
import threading
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.bridge import Bridge
from backend.jobs import Jobs
from backend.storage import Store
from tests.test_pcm_audio import pcm


class IOFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'library')
        with patch('backend.jobs.threading.Thread'):
            self.jobs = Jobs(self.store, None)
        self.addCleanup(self.cleanup_jobs)
        self.clock = 10
        self.jobs._release_if_idle = Mock()

    def cleanup_jobs(self):
        self.jobs.active = None
        self.jobs.process = None
        self.jobs.close()
        for channel in (self.jobs.commands, self.original_events):
            channel.cancel_join_thread()
            channel.close()

    @property
    def original_events(self):
        return getattr(self, '_original_events', self.jobs.events)

    def job(self):
        item = {'id': uuid.uuid4().hex, 'title': 'Synthetic reading', 'created': 1,
                'state': 'generating', 'completed': 0, 'total': 2, 'duration': 0,
                'voice': 'af_heart', 'speed': 1, 'position': 0, 'message': 'Generating.'}
        self.store.put('jobs', item)
        self.jobs.active = copy.deepcopy(item)
        return item

    def listen(self, *items):
        self._original_events = self.jobs.events
        actions = iter(items)

        def get(timeout):
            try:
                item = next(actions)
            except StopIteration:
                self.jobs.closing = True
                raise queue.Empty()
            return item() if callable(item) else item

        self.jobs.events = SimpleNamespace(get=get)
        errors = []
        try:
            with patch('backend.jobs.time.monotonic', side_effect=lambda: self.clock):
                self.jobs._listen()
        except (sqlite3.Error, OSError) as error:
            errors.append(type(error).__name__)
        self.assertEqual(errors, [], 'Storage failure escaped and killed the listener.')

    def test_listener_survives_failed_progress_write_and_persists_latest_after_recovery(self):
        item = self.job()
        saved = self.store.put
        failing = True

        def put(*args):
            if failing:
                raise sqlite3.OperationalError('injected database full')
            return saved(*args)

        def recover():
            nonlocal failing
            self.assertEqual(self.store.get('jobs', item['id'])['completed'], 0)
            failing = False
            self.clock += 5
            return {'id': item['id'], 'state': 'completed', 'completed': 2, 'duration': 1}

        with patch.object(self.store, 'put', side_effect=put):
            self.listen({'id': item['id'], 'state': 'generating', 'completed': 1}, recover)
        self.assertIsNone(self.jobs.active)
        self.assertEqual(self.store.get('jobs', item['id'])['state'], 'completed')

    def test_failed_terminal_write_is_retained_and_retried_without_another_worker_event(self):
        item = self.job()
        saved = self.store.put
        calls = 0

        def put(*args):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise sqlite3.OperationalError('injected locked database')
            return saved(*args)

        def idle():
            self.clock += 5
            raise queue.Empty()

        with patch.object(self.store, 'put', side_effect=put):
            self.listen({'id': item['id'], 'state': 'completed', 'completed': 2}, idle)
        self.assertIsNone(self.jobs.active)
        self.assertEqual(self.store.get('jobs', item['id'])['state'], 'completed')

    def test_benchmark_write_failure_does_not_kill_listener_or_lose_pending_result(self):
        self.jobs.operation = 'benchmark'
        self.jobs.performance = SimpleNamespace(benchmark={'state': 'running'}, warmup={}, identity=lambda: {'fixture': True})
        result = {'provider': 'CPUExecutionProvider', 'throughput': 1, 'threads': 1}
        attempts = []

        def save(value):
            attempts.append(value)
            if len(attempts) == 1:
                raise sqlite3.OperationalError('injected settings full')

        def idle():
            self.clock += 5
            raise queue.Empty()

        with patch.object(self.store, 'save_settings', side_effect=save):
            self.listen({'kind': 'benchmark', 'state': 'completed', 'results': [result]}, idle)
        self.assertIsNone(self.jobs.operation)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0], attempts[1])

    def test_close_cancels_and_terminates_worker_even_if_interrupted_write_fails(self):
        item = self.job()
        process = self.jobs.process = Mock()
        process.is_alive.return_value = True
        errors = []
        with patch.object(self.store, 'put', side_effect=sqlite3.OperationalError('injected full on close')):
            try:
                self.jobs.close()
            except sqlite3.Error as error:
                errors.append(type(error).__name__)
        self.assertEqual(errors, [], 'The shutdown write prevented cleanup.')
        self.assertTrue(self.jobs.cancel.is_set())
        process.terminate.assert_called_once()
        process.join.assert_called_once_with(timeout=3)
        self.assertIsNone(self.jobs.active)
        self.assertEqual(self.store.get('jobs', item['id'])['state'], 'generating')

    def export_fixture(self, existing=True):
        item = self.job()
        item['state'] = 'completed'
        self.store.put('jobs', item)
        source = self.store.root / 'jobs' / item['id'] / 'recording.wav'
        source.parent.mkdir()
        source.write_bytes(pcm())
        target = self.root / 'export.wav'
        if existing:
            target.write_bytes(b'previous complete export')
        bridge = Bridge(self.store, None, None)
        bridge._window = SimpleNamespace(create_file_dialog=lambda *a, **k: (str(target),),
                                         create_confirmation_dialog=lambda *a: True)
        return bridge, item['id'], source, target

    def test_partial_export_failure_preserves_existing_destination_and_source(self):
        bridge, key, source, target = self.export_fixture()
        before = source.read_bytes(), target.read_bytes()

        def partial(_source, destination):
            Path(destination).write_bytes(b'partial')
            raise OSError(28, 'injected export disk full')

        with patch('backend.bridge.copy_pcm', side_effect=partial):
            with self.assertRaises(OSError):
                bridge.export_recording(key)
        self.assertEqual((source.read_bytes(), target.read_bytes()), before)
        self.assertEqual(list(self.root.glob('.violilt-export-*')), [])

    def test_partial_export_failure_does_not_publish_a_new_destination(self):
        bridge, key, source, target = self.export_fixture(existing=False)

        def partial(_source, destination):
            Path(destination).write_bytes(b'partial')
            raise OSError(28, 'injected export disk full')

        with patch('backend.bridge.copy_pcm', side_effect=partial):
            with self.assertRaises(OSError):
                bridge.export_recording(key)
        self.assertFalse(target.exists())
        self.assertEqual(source.read_bytes(), pcm())

    def test_failed_final_export_replace_preserves_existing_destination(self):
        bridge, key, source, target = self.export_fixture()
        with patch('pathlib.Path.replace', side_effect=PermissionError('injected export file lock')):
            with self.assertRaises(PermissionError):
                bridge.export_recording(key)
        self.assertEqual(target.read_bytes(), b'previous complete export')
        self.assertEqual(source.read_bytes(), pcm())
        self.assertEqual(list(self.root.glob('.violilt-export-*')), [])

    def test_healthy_rows_remain_readable_when_quarantine_write_fails(self):
        healthy = self.store.document('Keep this synthetic reading.', 'Healthy')
        with self.store.connect() as connection:
            connection.execute('INSERT INTO documents VALUES (?, ?, ?)', ('broken', '{bad', 1))
        connect = self.store.connect

        @contextmanager
        def constrained():
            with connect() as connection:
                def execute(sql, *args):
                    if sql.startswith('INSERT OR IGNORE INTO recovery_rows'):
                        raise sqlite3.OperationalError('injected readonly recovery table')
                    return connection.execute(sql, *args)
                yield SimpleNamespace(execute=execute)

        errors, documents = [], []
        with patch.object(self.store, 'connect', constrained):
            try:
                documents = self.store.all('documents')
            except sqlite3.Error as error:
                errors.append(type(error).__name__)
        self.assertEqual(errors, [], 'Failed recovery bookkeeping hid healthy readings.')
        self.assertEqual([doc['id'] for doc in documents], [healthy['id']])
        self.assertGreater(self.store.recovery_summary()['count'], 0)
        with connect() as connection:
            self.assertEqual(connection.execute("SELECT body FROM documents WHERE id='broken'").fetchone()[0], '{bad')

    def test_whole_file_database_damage_fails_without_replacing_original_bytes(self):
        directory = self.root / 'damaged'
        directory.mkdir()
        database = directory / 'library.sqlite3'
        database.write_bytes(b'Unusable synthetic SQLite fixture.')
        before = database.read_bytes()
        with self.assertRaises(sqlite3.DatabaseError):
            Store(directory)
        self.assertEqual(database.read_bytes(), before)

    def test_pending_terminal_state_is_visible_as_unsaved_and_blocks_new_work(self):
        item = self.job()
        terminal = item | {'state': 'completed', 'completed': 2, 'duration': 5, 'available_duration': 5}
        self.jobs.active = None
        self.jobs.models = SimpleNamespace(status=lambda: {'state': 'ready'})
        self.jobs.performance_state = lambda: None
        self.jobs.cache_state = lambda: {}
        bridge = Bridge(self.store, self.jobs.models, self.jobs)
        with patch.object(self.store, 'put', side_effect=sqlite3.OperationalError('injected full')):
            with self.jobs.lock:
                self.jobs._save_progress(terminal)
            state = bridge.get_state()
            self.assertEqual(state['jobs'][0]['state'], 'assembling')
            self.assertIn('not been saved', state['recovery']['message'])
            with self.assertRaisesRegex(ValueError, 'not been saved'):
                self.jobs.start({}, {}, 'af_heart', 1)
            with self.assertRaisesRegex(ValueError, 'not been saved'):
                self.jobs.save_position(item['id'], 3)
            self.assertEqual(self.jobs.pending_storage()['job']['state'], 'completed')
        with self.jobs.lock:
            self.jobs._flush_persistence(force=True)
        self.assertEqual(self.store.get('jobs', item['id'])['position'], 3)
        self.assertEqual(bridge.get_state()['jobs'][0]['state'], 'completed')
        self.assertEqual(self.jobs.pending_storage()['message'], '')

    def test_persistence_retries_are_throttled_and_coalesce_only_latest_progress(self):
        item = self.job()
        item['total'] = 100
        with patch('backend.jobs.time.monotonic', return_value=10), \
             patch.object(self.store, 'put', side_effect=sqlite3.OperationalError('injected full')) as put:
            for index in range(100):
                with self.jobs.lock:
                    self.jobs._save_progress(item | {'completed': index})
            self.assertEqual(put.call_count, 1)
            self.assertEqual(self.jobs.pending_storage()['job']['completed'], 99)
            self.assertIsNone(self.jobs._pending_benchmark)


if __name__ == '__main__':
    unittest.main()
