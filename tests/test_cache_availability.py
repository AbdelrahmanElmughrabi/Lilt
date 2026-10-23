"""Optional parent-cache failures must not become library/save failures."""
import sqlite3
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.bridge import Bridge
from backend.documents import prepare
from backend.jobs import Jobs
from backend.storage import Store


class CacheAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='violilt-cache-availability-')
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'library')
        self.document = self.store.document('Synthetic cache boundary.', 'Cache boundary')
        clock = patch('backend.jobs.time.monotonic', return_value=10)
        self.clock = clock.start()
        self.addCleanup(clock.stop)

    def fixture(self, collision=False, enabled=True):
        self.store.save_settings({'cache_enabled': enabled})
        if collision:
            (self.store.root / 'section-cache').write_bytes(b'Keep this conflicting file.')
        jobs = Jobs.__new__(Jobs)
        try:
            with patch('backend.jobs.threading.Thread'):
                jobs.__init__(self.store, None)
        except Exception:
            for channel in (jobs.commands, jobs.events):
                channel.cancel_join_thread()
                channel.close()
            raise
        channels = jobs.commands, jobs.events

        def cleanup():
            jobs.active = None
            jobs.close()
            for channel in channels:
                channel.cancel_join_thread()
                channel.close()

        self.addCleanup(cleanup)
        models = SimpleNamespace(status=lambda: {'state': 'missing', 'voices': []})
        jobs.performance_state = lambda: None
        return jobs, Bridge(self.store, models, jobs)

    def wave(self):
        path = self.store.root / 'source.wav'
        with wave.open(str(path), 'wb') as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(24000)
            writer.writeframes(b'\x01\x00' * 240)
        return path

    def test_enabled_collision_keeps_library_and_conflicting_file(self):
        jobs, bridge = self.fixture(collision=True)
        state = bridge.get_state()
        self.assertEqual(len(state['documents']), 1)
        self.assertFalse(state['cache']['available'])
        self.assertIsNone(state['cache']['count'])
        self.assertIsNone(state['cache']['bytes'])
        self.assertTrue(state['cache']['message'])
        self.assertIsNone(jobs.cache)
        self.assertEqual((self.store.root / 'section-cache').read_bytes(), b'Keep this conflicting file.')

    def test_disabled_collision_does_not_block_library(self):
        _, bridge = self.fixture(collision=True, enabled=False)
        self.assertFalse(bridge.get_state()['settings']['cache_enabled'])
        self.assertEqual(self.store.get('documents', self.document['id'])['markdown'], self.document['markdown'])

    def test_initialization_permission_error_keeps_library(self):
        with patch('backend.jobs.SectionCache', side_effect=PermissionError('Synthetic cache access failure')):
            _, bridge = self.fixture()
            self.assertFalse(bridge.get_state()['cache']['available'])
            self.assertEqual(len(bridge.get_state()['documents']), 1)

    def test_scan_failure_is_throttled_and_recovers_without_restart(self):
        jobs, bridge = self.fixture()
        self.clock.return_value = 14
        with patch('backend.jobs.SectionCache.status', side_effect=PermissionError('Synthetic scan failure')) as scan:
            with self.assertLogs(level='ERROR') as logs:
                first = bridge.get_state()['cache']
                self.assertFalse(first['available'])
                self.assertEqual(bridge.get_state()['cache'], first)
                self.assertEqual(scan.call_count, 1)
                self.clock.return_value = 18
                self.assertFalse(bridge.get_state()['cache']['available'])
                self.assertEqual(scan.call_count, 2)
            self.assertEqual(len(logs.output), 1, 'Repeated polling must not flood the log.')
        self.clock.return_value = 22
        self.assertTrue(bridge.get_state()['cache']['available'])
        self.assertEqual(bridge.get_state()['cache']['message'], '')

    def test_initialization_recovers_after_conflict_is_removed(self):
        jobs, bridge = self.fixture(collision=True)
        conflict = self.store.root / 'section-cache'
        conflict.rename(self.store.root / 'preserved-conflict')
        self.clock.return_value = 14
        self.assertTrue(bridge.get_state()['cache']['available'])
        self.assertTrue(jobs.cache.root.is_dir())
        self.assertEqual((self.store.root / 'preserved-conflict').read_bytes(), b'Keep this conflicting file.')

    def test_healthy_cache_reuses_audio_and_reports_actual_counts(self):
        jobs, bridge = self.fixture()
        jobs.cache.put('a' * 64, self.wave())
        target = self.store.root / 'reused.wav'
        self.assertTrue(jobs.cache.fetch('a' * 64, target))
        self.clock.return_value = 14
        state = bridge.get_state()['cache']
        self.assertTrue(state['available'])
        self.assertEqual(state['count'], 1)
        self.assertEqual(state['bytes'], target.stat().st_size)

    def test_failed_partial_clear_is_an_error_and_invalidates_old_counts(self):
        jobs, bridge = self.fixture()
        jobs.cache.put('a' * 64, self.wave())
        self.clock.return_value = 14
        self.assertEqual(bridge.get_state()['cache']['count'], 1)

        def partial_clear():
            (jobs.cache.root / ('a' * 64 + '.wav')).unlink()
            raise PermissionError('Synthetic partial clear failure')

        with patch.object(jobs.cache, 'clear', side_effect=partial_clear):
            with self.assertRaisesRegex(PermissionError, 'partial clear'):
                bridge.clear_cache()
        self.assertEqual(bridge.get_state()['cache']['count'], 0)
        self.assertEqual(len(bridge.get_state()['documents']), 1)

    def test_unavailable_cache_clear_does_not_claim_success(self):
        _, bridge = self.fixture(collision=True)
        with self.assertRaises(OSError):
            bridge.clear_cache()
        self.assertFalse(bridge.get_state()['cache']['available'])

    def test_required_settings_and_programming_errors_are_not_hidden(self):
        jobs, _ = self.fixture()
        with patch.object(self.store, 'settings', side_effect=sqlite3.OperationalError('Required storage failed')):
            with self.assertRaises(sqlite3.OperationalError):
                jobs.cache_state()
        self.clock.return_value = 14
        with patch.object(jobs.cache, 'status', side_effect=TypeError('Programming defect')):
            with self.assertRaises(TypeError):
                jobs.cache_state()

    def test_worker_command_keeps_cache_path_when_parent_cache_is_unavailable(self):
        jobs, _ = self.fixture(collision=True)
        jobs.models = SimpleNamespace(root=self.store.root, status=lambda: {'state': 'ready', 'voices': ['af_heart']})
        jobs.performance = SimpleNamespace(resolve=lambda _: {'provider': 'CPUExecutionProvider'})
        jobs._audio_identity = Mock(return_value=['synthetic identity'])
        jobs._worker = Mock()
        jobs.commands = Mock()
        with patch('backend.jobs.pronunciation_identity', return_value={'fixture': True}):
            jobs.start(prepare(self.document['markdown']), self.document, 'af_heart', 1)
        command = jobs.commands.put.call_args.args[0]
        self.assertEqual(command['cache'], str(self.store.root / 'section-cache'))
        self.assertTrue(command['cache_enabled'])
        self.assertIsNone(jobs.cache)
