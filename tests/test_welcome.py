"""Durable welcome presentation state with disposable stores and no speech."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.bridge import Bridge
from backend.desktop import _allowed_native_call
from backend.storage import Store


class WelcomeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'library')
        self.models = SimpleNamespace(status=lambda: {'state': 'missing', 'voices': []})
        self.jobs = SimpleNamespace(state=lambda: None, performance_state=lambda: None,
                                    cache_state=lambda: {'count': 0, 'bytes': 0})
        self.bridge = Bridge(self.store, self.models, self.jobs)

    def test_completion_survives_restart_without_changing_public_preferences(self):
        self.store.save_settings({'theme': 'dark', 'speed': 1.25})
        before = self.bridge.get_state()
        self.assertEqual(before['welcome_version'], 0)
        self.assertNotIn('welcome_version', before['settings'])
        self.assertTrue(self.bridge.complete_welcome())
        reopened = Bridge(Store(self.store.root), self.models, self.jobs).get_state()
        self.assertEqual(reopened['welcome_version'], 1)
        self.assertEqual(reopened['settings'], before['settings'])
        self.assertEqual(reopened['recovery']['count'], 0)

    def test_stale_public_settings_write_cannot_reset_welcome_completion(self):
        self.bridge.complete_welcome()
        self.bridge.save_settings({'theme': 'dark', 'welcome_version': 0})
        state = self.bridge.get_state()
        self.assertEqual(state['welcome_version'], 1)
        self.assertEqual(state['settings']['theme'], 'dark')
        self.assertNotIn('welcome_version', state['settings'])

    def test_failed_completion_does_not_persist_a_false_acknowledgement(self):
        with patch.object(self.store, 'save_settings', side_effect=OSError('Fixture storage unavailable')):
            with self.assertRaises(OSError):
                self.bridge.complete_welcome()
        self.assertEqual(Bridge(Store(self.store.root), self.models, self.jobs).get_state()['welcome_version'], 0)

    def test_invalid_saved_marker_keeps_welcome_and_other_preferences(self):
        self.store.save_settings({'theme': 'dark'})
        with self.store.connect() as connection:
            connection.execute('INSERT INTO settings VALUES (?, ?)', ('welcome_version', json.dumps(True)))
        state = self.bridge.get_state()
        self.assertEqual(state['welcome_version'], 0)
        self.assertEqual(state['settings']['theme'], 'dark')
        self.assertGreater(self.store.recovery_summary()['count'], 0)
        self.bridge.complete_welcome()
        self.assertEqual(self.bridge.get_state()['welcome_version'], 1)

    def test_only_zero_argument_completion_is_exposed_on_native_transport(self):
        window = SimpleNamespace(_js_api=self.bridge)
        self.assertTrue(_allowed_native_call(window, ['complete_welcome', '[]', 'welcome1']))
        self.assertFalse(_allowed_native_call(window, ['complete_welcome', '[true]', 'welcome1']))
        self.assertFalse(_allowed_native_call(window, ['_store', '[]', 'welcome1']))


if __name__ == '__main__':
    unittest.main()
