"""Canceled native navigation must not reinject/reset the existing JS bridge."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from backend.desktop import _install_file_drop_transport


class Event:
    def __init__(self, *handlers):
        self.handlers = list(handlers)

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self


class NavigationCompletionTests(unittest.TestCase):
    def fixture(self):
        original = Mock()
        notify = Mock()
        control = SimpleNamespace(NavigationStarting=Event(), NavigationCompleted=Event(original),
                                  WebMessageReceived=Event(notify),
                                  CoreWebView2=SimpleNamespace(FrameNavigationStarting=Event()))
        window = SimpleNamespace(original_url='http://127.0.0.1:4321/',
            native=SimpleNamespace(browser=SimpleNamespace(webview=control, on_script_notify=notify,
                                                           on_navigation_completed=original)))
        _install_file_drop_transport(window)
        return window, control, original

    def test_canceled_navigation_keeps_the_existing_trusted_document_bridge(self):
        window, control, original = self.fixture()
        _install_file_drop_transport(window)
        self.assertEqual(len(control.NavigationCompleted.handlers), 1)
        sender = SimpleNamespace(Source=window.original_url)
        control.NavigationCompleted.handlers[0](sender, SimpleNamespace(IsSuccess=False, WebErrorStatus='OperationCanceled'))
        original.assert_not_called()

    def test_real_loads_and_other_failures_keep_normal_bridge_initialization(self):
        window, control, original = self.fixture()
        sender = SimpleNamespace(Source=window.original_url)
        for success, status in ((True, 'Unknown'), (False, 'ConnectionAborted'), (False, 'HostNameNotResolved')):
            args = SimpleNamespace(IsSuccess=success, WebErrorStatus=status)
            control.NavigationCompleted.handlers[0](sender, args)
            original.assert_called_with(sender, args)
        self.assertEqual(original.call_count, 3)


if __name__ == '__main__':
    unittest.main()
