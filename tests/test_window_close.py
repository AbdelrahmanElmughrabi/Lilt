import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.desktop import _install_file_drop_transport
from backend.window_close import install_close_guard


class Event:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, callback):
        self.handlers.append(callback)
        return self

    def __isub__(self, callback):
        self.handlers.remove(callback)
        return self


@patch.dict('sys.modules', {'System': SimpleNamespace(Action=lambda callback: callback)})
class WindowCloseTests(unittest.TestCase):
    def fixture(self, armed=True):
        pending = []
        core = SimpleNamespace(Source='http://127.0.0.1:4321/', ExecuteScriptAsync=Mock(),
                               FrameNavigationStarting=Event())
        original = Mock()
        messages = Event()
        messages.handlers.append(original)
        control = SimpleNamespace(CoreWebView2=core, BeginInvoke=pending.append,
                                  NavigationStarting=Event(), WebMessageReceived=messages)
        window = SimpleNamespace(original_url=core.Source, events=SimpleNamespace(closing=Event()),
                                 native=SimpleNamespace(browser=SimpleNamespace(webview=control, on_script_notify=original)),
                                 _js_api=SimpleNamespace())
        guard = install_close_guard(window)
        window.destroy = Mock(side_effect=guard.on_closing)
        guard.armed = armed
        return guard, window, core, pending

    def test_uninitialized_window_can_close_and_registration_is_idempotent(self):
        guard, window, _, pending = self.fixture(armed=False)
        self.assertIs(install_close_guard(window), guard)
        self.assertEqual(len(window.events.closing.handlers), 1)
        self.assertTrue(guard.on_closing())
        self.assertEqual(pending, [])

    def test_close_cancels_synchronously_and_dispatches_once_without_waiting_for_js(self):
        guard, window, core, pending = self.fixture()
        self.assertFalse(guard.on_closing())
        request = guard.request
        self.assertFalse(guard.on_closing())
        self.assertEqual(guard.request, request)
        self.assertEqual(len(pending), 1)
        core.ExecuteScriptAsync.assert_not_called()
        pending.pop(0)()
        script = core.ExecuteScriptAsync.call_args.args[0]
        self.assertIn('violilt:close-request', script)
        self.assertIn(json.dumps(request), script)
        self.assertNotIn('eval(', script)
        window.destroy.assert_not_called()

    def test_only_matching_boolean_approval_can_destroy_and_approval_is_consumed(self):
        guard, window, _, pending = self.fixture()
        guard.on_closing()
        pending.pop(0)()
        for request, saved in [('unknown', True), (None, True), (guard.request, 'true'), (guard.request, 1)]:
            guard.respond(request, saved)
        self.assertEqual(pending, [])
        guard.respond(guard.request, True)
        guard.respond(guard.request, True)
        self.assertEqual(len(pending), 1)
        window.destroy.assert_not_called()
        pending.pop(0)()
        window.destroy.assert_called_once()
        self.assertIsNone(guard.request)
        self.assertFalse(guard.approved)
        self.assertFalse(guard.on_closing(), 'A later close must require its own save approval.')

    def test_cancel_rejects_late_approval_and_a_new_close_gets_a_new_request(self):
        guard, window, _, pending = self.fixture()
        guard.on_closing()
        old = guard.request
        guard.respond(old, False)
        guard.respond(old, True)
        pending.pop(0)()  # Canceled script dispatch must do nothing.
        window.destroy.assert_not_called()
        guard.on_closing()
        self.assertNotEqual(guard.request, old)
        guard.respond(old, True)
        self.assertFalse(guard.finishing)

    def test_cancel_can_revoke_queued_completion_without_losing_a_new_close(self):
        guard, window, _, pending = self.fixture()
        guard.on_closing()
        pending.pop(0)()
        old = guard.request
        guard.respond(old, True)
        guard.respond(old, False)
        guard.on_closing()
        current = guard.request
        pending.pop(0)()  # Old completion must not clear the newer request.
        self.assertEqual(guard.request, current)
        window.destroy.assert_not_called()
        pending.pop(0)()
        guard.respond(current, True)
        pending.pop(0)()
        window.destroy.assert_called_once()

    def test_dispatch_and_completion_recheck_the_current_page(self):
        guard, window, core, pending = self.fixture()
        guard.on_closing()
        core.Source = 'https://external.invalid/'
        pending.pop(0)()
        core.ExecuteScriptAsync.assert_not_called()
        self.assertIsNone(guard.request)
        core.Source = window.original_url
        guard.on_closing()
        pending.pop(0)()
        guard.respond(guard.request, True)
        core.Source = 'https://external.invalid/'
        pending.pop(0)()
        window.destroy.assert_not_called()
        self.assertIsNone(guard.request)

    def test_native_dispatch_failure_keeps_the_window_open_and_allows_retry(self):
        guard, window, core, pending = self.fixture()
        core.ExecuteScriptAsync.side_effect = RuntimeError('Disposable dispatch failure')
        guard.on_closing()
        with self.assertLogs(level='ERROR'):
            pending.pop(0)()
        self.assertIsNone(guard.request)
        window.destroy.assert_not_called()
        core.ExecuteScriptAsync.side_effect = None
        self.assertFalse(guard.on_closing())
        self.assertEqual(len(pending), 1)

    def test_native_destroy_failure_does_not_leave_future_close_approved(self):
        guard, window, _, pending = self.fixture()
        guard.on_closing()
        pending.pop(0)()
        window.destroy.side_effect = RuntimeError('Disposable close failure')
        guard.respond(guard.request, True)
        with self.assertLogs(level='ERROR'):
            pending.pop(0)()
        self.assertFalse(guard.approved)
        self.assertFalse(guard.on_closing())

    def test_close_transport_requires_trusted_origin_and_a_bounded_request_id(self):
        guard, window, _, pending = self.fixture(armed=False)
        _install_file_drop_transport(window)
        receive = window.native.browser.webview.WebMessageReceived.handlers[0]

        def send(message, source=window.original_url):
            receive(None, SimpleNamespace(Source=source, get_WebMessageAsJson=lambda: json.dumps(message)))

        send({'type': 'violilt:close-ready'}, 'https://external.invalid/')
        self.assertFalse(guard.armed)
        send({'type': 'violilt:close-ready'})
        self.assertTrue(guard.armed)
        guard.on_closing()
        pending.pop(0)()
        request = guard.request
        send({'type': 'violilt:close-response', 'id': request, 'saved': True}, 'https://external.invalid/')
        send({'type': 'violilt:close-response', 'id': 'x' * 65, 'saved': True})
        send({'type': 'violilt:close-response', 'id': request, 'saved': 'true'})
        self.assertEqual(pending, [])
        send({'type': 'violilt:close-response', 'id': request, 'saved': True})
        self.assertEqual(len(pending), 1)
        pending.pop(0)()
        window.destroy.assert_called_once()


if __name__ == '__main__':
    unittest.main()
