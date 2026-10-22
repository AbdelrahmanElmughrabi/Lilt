"""Idle policy boundaries and real spawned-worker release/restart without inference."""
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.bridge import Bridge
from backend.jobs import Jobs
from backend.performance import validate
from backend.storage import Store


def idle_worker(commands, events, cancel, runtime_directory=None):
    while True:
        command = commands.get()
        if command is None:
            return
        events.put({'kind': 'warmup', 'state': 'ready', 'message': 'Fixture ready.'})


class ModelMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name))
        # Policy tests control time and do not need a listener thread.
        with patch('backend.jobs.threading.Thread'):
            self.jobs = Jobs(self.store, None)
        self.jobs.performance = SimpleNamespace(warmup={}, status=lambda process, **kwargs: {})

    def tearDown(self):
        self.jobs.close()
        for channel in (self.jobs.commands, self.jobs.events):
            channel.cancel_join_thread()
            channel.close()
        self.temp.cleanup()

    def test_default_and_persisted_policy_validation(self):
        self.assertEqual(self.store.settings()['model_release'], 'idle')
        for policy in ('idle', 'immediate', 'keep'):
            validate({'model_release': policy})
            self.store.save_settings({'model_release': policy})
            self.assertEqual(Store(self.store.root).settings()['model_release'], policy)
        with self.assertRaises(ValueError):
            validate({'model_release': 'sometimes'})

    def test_idle_threshold_and_keep_policy(self):
        self.jobs.process = Mock()
        with patch('backend.jobs.time.monotonic', return_value=10):
            self.jobs._release_if_idle()
        with patch.object(self.jobs, '_release_worker') as release:
            with patch('backend.jobs.time.monotonic', return_value=129.99):
                self.jobs._release_if_idle()
            release.assert_not_called()
            with patch('backend.jobs.time.monotonic', return_value=130):
                self.jobs._release_if_idle()
            release.assert_called_once()
            release.reset_mock()
            self.store.save_settings({'model_release': 'keep'})
            with patch('backend.jobs.time.monotonic', return_value=10000):
                self.jobs._release_if_idle()
            release.assert_not_called()
        self.jobs.process = None

    def test_generation_benchmark_and_warmup_block_manual_and_auto_release(self):
        self.jobs.process = Mock()
        self.jobs.idle_since = 0
        self.store.save_settings({'model_release': 'immediate'})
        with patch.object(self.jobs, '_release_worker') as release:
            for active, operation in (({'id': 'running'}, None), (None, 'benchmark'), (None, 'warmup')):
                self.jobs.active, self.jobs.operation = active, operation
                with self.assertRaisesRegex(ValueError, 'Finish the current'):
                    self.jobs.release_engine()
                self.jobs._release_if_idle()
                release.assert_not_called()
            self.jobs.active = self.jobs.operation = None
            self.jobs._release_if_idle()
            release.assert_called_once()
        self.jobs.process = None

    def test_graceful_release_replaces_channels_and_preserves_saved_files(self):
        recording = self.store.root / 'jobs' / 'recording.wav'
        recording.write_bytes(b'saved audio')
        self.jobs.process = Mock()
        self.jobs.process.is_alive.side_effect = [True, False, False]
        process = self.jobs.process
        old = (self.jobs.commands, self.jobs.events, self.jobs.cancel)
        self.assertTrue(Bridge(self.store, None, self.jobs).release_engine())
        process.join.assert_any_call(timeout=3)
        process.terminate.assert_not_called()
        process.close.assert_called_once()
        self.assertIsNone(self.jobs.process)
        for previous, current in zip(old, (self.jobs.commands, self.jobs.events, self.jobs.cancel)):
            self.assertIsNot(previous, current)
        self.assertEqual(recording.read_bytes(), b'saved audio')
        self.assertEqual(self.jobs.performance_state()['memory']['state'], 'unloaded')
        self.assertTrue(self.jobs.release_engine())

    def test_stalled_idle_worker_uses_fallback_and_never_claims_release_if_alive(self):
        process = self.jobs.process = Mock()
        process.is_alive.side_effect = [True, True, False]
        self.jobs.release_engine()
        process.terminate.assert_called_once()
        process = self.jobs.process = Mock()
        process.is_alive.return_value = True
        with self.assertRaisesRegex(ValueError, 'has not stopped'):
            self.jobs.release_engine()
        self.assertTrue(self.jobs.releasing)
        self.assertEqual(self.jobs.performance_state()['memory']['state'], 'releasing')
        with self.assertRaisesRegex(ValueError, 'still releasing'):
            self.jobs._worker()
        process.is_alive.return_value = False
        self.jobs._release_if_idle()
        self.assertIsNone(self.jobs.process)

    def test_real_worker_restart_and_listener_survives_queue_rotation(self):
        self.jobs.models = SimpleNamespace(root=self.store.root / 'models', status=lambda: {'state': 'ready'})
        self.jobs.performance.resolve = lambda settings: {}
        listener = threading.Thread(target=self.jobs._listen)
        listener.start()
        try:
            with patch('backend.jobs.speech_worker', idle_worker), patch('backend.jobs.gpu_runtime_directory', return_value=None):
                for _ in range(2):
                    self.assertTrue(self.jobs.warmup())
                    deadline = time.monotonic() + 10
                    while self.jobs.operation and time.monotonic() < deadline:
                        time.sleep(.02)
                    self.assertIsNone(self.jobs.operation)
                    process = self.jobs.process
                    self.assertTrue(process.is_alive())
                    self.assertTrue(self.jobs.release_engine())
                    self.assertIsNone(self.jobs.process)
                    self.assertTrue(listener.is_alive())
        finally:
            self.jobs.close()
            listener.join(timeout=5)
        self.assertFalse(listener.is_alive())


if __name__ == '__main__':
    unittest.main()
