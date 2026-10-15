import unittest
import json
import threading
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch

from backend.desktop import install_csp_bridge, _install_file_drop_transport


class DesktopBridgeTests(unittest.TestCase):
    def test_drop_transport_uses_native_file_objects_and_preserves_other_messages(self):
        class Event:
            def __init__(self):
                self.handlers = []
            def __iadd__(self, handler):
                self.handlers.append(handler)
                return self
            def __isub__(self, handler):
                self.handlers.remove(handler)
                return self
        class CoreWebView2File:
            Path = 'C:/notes/original.md'
        original = Mock()
        event = Event()
        event.handlers.append(original)
        control = SimpleNamespace(WebMessageReceived=event)
        bridge = Mock()
        bridge.import_dropped_documents.return_value = {'documents': [], 'errors': []}
        delivered = threading.Event()
        window = SimpleNamespace(native=SimpleNamespace(browser=SimpleNamespace(
            webview=control, on_script_notify=original)),
            _js_api=bridge, run_js=Mock(side_effect=lambda _script: delivered.set()))
        _install_file_drop_transport(window)
        _install_file_drop_transport(window)
        self.assertEqual(len(event.handlers), 1)
        args = Mock()
        args.get_WebMessageAsJson.return_value = json.dumps(['get_state', '[]', 'normal'])
        event.handlers[0](None, args)
        original.assert_called_once_with(None, args)
        args.get_WebMessageAsJson.return_value = json.dumps({'type': 'lilt:file-drop', 'id': 'request123', 'paths': ['C:/untrusted.md']})
        args.get_AdditionalObjects.return_value = [CoreWebView2File(), object()]
        event.handlers[0](None, args)
        self.assertTrue(delivered.wait(3))
        bridge.import_dropped_documents.assert_called_once_with(['C:/notes/original.md'])
        self.assertTrue(window.run_js.call_args.args[0].startswith('window.pywebview._returnValuesCallbacks["import_dropped_documents"]["request123"]'))

    def test_safe_builder_precedes_ready_and_return_delivery_avoids_eval(self):
        from webview import util
        original = Mock(return_value=('base;', 'ready;'))
        window = Mock(spec=['evaluate_js', 'run_js'])
        original_evaluate = window.evaluate_js
        with patch.object(util, 'load_js_files', original):
            install_csp_bridge(Path(__file__).parents[1] / 'assets/desktop-api.js')
            loader = util.load_js_files
            install_csp_bridge(Path(__file__).parents[1] / 'assets/desktop-api.js')
            self.assertIs(util.load_js_files, loader)
            code, finish = loader(window, 'edgechromium')
            self.assertTrue(code.startswith('base;'))
            self.assertIn('window.pywebview._createApi = function', code)
            self.assertEqual(finish, 'ready;')
            callback = 'window.pywebview._returnValuesCallbacks["get_state"]["id"]({value:"{}"})'
            window.evaluate_js(callback)
            window.run_js.assert_called_once_with(callback)
            window.evaluate_js('1 + 1')
            original_evaluate.assert_called_once_with('1 + 1', None)
            patched_evaluate = window.evaluate_js
            loader(window, 'edgechromium')
            self.assertIs(window.evaluate_js, patched_evaluate)
