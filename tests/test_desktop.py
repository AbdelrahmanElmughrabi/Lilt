import unittest
import json
import queue
import threading
import time
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch

from backend.desktop import install_csp_bridge, _install_file_drop_transport, _trusted_page, _allowed_native_call


class DesktopBridgeTests(unittest.TestCase):
    def confined_drop(self, result=None, error=None):
        class Event:
            def __init__(self): self.handlers = []
            def __iadd__(self, handler): self.handlers.append(handler); return self
            def __isub__(self, handler): self.handlers.remove(handler); return self

        class Control:
            def __init__(self):
                self.owner = threading.get_ident()
                self.unsafe_reads = 0
                self.pending = queue.Queue()
                self.queued = threading.Event()
                self.delivered = threading.Event()
                self.core = SimpleNamespace(Source='http://127.0.0.1:4321/', FrameNavigationStarting=Event(),
                                            ExecuteScriptAsync=Mock(side_effect=lambda _: self.delivered.set()))
                self.WebMessageReceived, self.NavigationStarting = Event(), Event()
            @property
            def CoreWebView2(self):
                if threading.get_ident() != self.owner:
                    self.unsafe_reads += 1
                return self.core
            def BeginInvoke(self, callback):
                self.pending.put(callback)
                self.queued.set()
            def pump(self):
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    try: self.pending.get(timeout=.05)()
                    except queue.Empty: pass
                    if self.delivered.is_set(): return

        control = Control()
        original = Mock()
        control.WebMessageReceived.handlers.append(original)
        api = SimpleNamespace(import_dropped_documents=Mock(return_value=result or {'documents': [], 'errors': []}, side_effect=error))
        window = SimpleNamespace(original_url='http://127.0.0.1:4321/', _js_api=api,
                                 native=SimpleNamespace(browser=SimpleNamespace(webview=control, on_script_notify=original)),
                                 run_js=Mock(side_effect=lambda _: control.delivered.set()))
        _install_file_drop_transport(window)
        class CoreWebView2File:
            Path = 'C:/disposable/reading.txt'
        event = SimpleNamespace(Source='http://127.0.0.1:4321/',
                                get_WebMessageAsJson=lambda: json.dumps({'type': 'violilt:file-drop', 'id': 'drop123'}),
                                get_AdditionalObjects=lambda: [CoreWebView2File()])
        control.WebMessageReceived.handlers[0](None, event)
        return control, window

    @patch.dict('sys.modules', {'System': SimpleNamespace(Action=lambda callback: callback)})
    def test_drop_success_dispatches_origin_check_and_response_to_ui_thread(self):
        control, window = self.confined_drop({'documents': [{'id': 'fixture'}], 'errors': []})
        control.pump()
        self.assertTrue(control.delivered.is_set())
        self.assertEqual(control.unsafe_reads, 0, 'The import worker read a UI-thread-only WebView2 property.')
        window.run_js.assert_not_called()  # Its synchronous result wait would deadlock the UI thread.
        script = control.core.ExecuteScriptAsync.call_args.args[0]
        self.assertIn('["import_dropped_documents"]["drop123"]', script)
        response = json.loads(script[script.index('(') + 1:-1])
        self.assertEqual(json.loads(response['value'])['documents'], [{'id': 'fixture'}])

    @patch.dict('sys.modules', {'System': SimpleNamespace(Action=lambda callback: callback)})
    def test_drop_error_rejects_on_ui_thread_without_stranding_the_request(self):
        control, window = self.confined_drop(error=ValueError('Unsupported disposable PDF.'))
        control.pump()
        self.assertTrue(control.delivered.is_set())
        self.assertEqual(control.unsafe_reads, 0)
        window.run_js.assert_not_called()
        script = control.core.ExecuteScriptAsync.call_args.args[0]
        response = json.loads(script[script.index('(') + 1:-1])
        self.assertTrue(response['isError'])
        self.assertEqual(json.loads(response['value'])['message'], 'Unsupported disposable PDF.')

    @patch.dict('sys.modules', {'System': SimpleNamespace(Action=lambda callback: callback)})
    def test_drop_response_rechecks_page_origin_when_ui_dispatch_runs(self):
        control, window = self.confined_drop()
        self.assertTrue(control.queued.wait(2), 'The worker did not marshal response delivery to the UI thread.')
        control.core.Source = 'https://external.invalid/'
        control.pending.get_nowait()()
        self.assertEqual(control.unsafe_reads, 0)
        control.core.ExecuteScriptAsync.assert_not_called()
        window.run_js.assert_not_called()

    def test_native_contract_rejects_private_dispatch_and_callback_injection(self):
        window = SimpleNamespace(_js_api=Mock(), _callbacks={'known': Mock()})
        for name in ('_store.save_settings', '__class__', '_window.destroy', 'get_state.__call__',
                     'pywebviewStateUpdate', 'pywebviewMoveWindow', 'console', 'import_dropped_documents'):
            self.assertFalse(_allowed_native_call(window, [name, '[]', 'valid123']))
        for message in (None, {}, ['get_state'], ['get_state', '{}', 'valid'],
                        ['get_state', '[1]', 'valid'], ['get_state', '[]', 'bad"id'],
                        ['get_state', '[]', 'x' * 65], ['get_state', 'invalid', 'valid'],
                        ['pywebviewAsyncCallback', 'null', 'unknown']):
            self.assertFalse(_allowed_native_call(window, message))
        self.assertTrue(_allowed_native_call(window, ['get_state', '[]', 'valid123']))
        self.assertTrue(_allowed_native_call(window, ['save_settings', '[{"theme":"dark"}]', 'valid']))
        self.assertTrue(_allowed_native_call(window, ['pywebviewAsyncCallback', 'null', 'known']))

    @patch.dict('sys.modules', {'System': SimpleNamespace(Action=lambda callback: callback)})
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
        delivered = threading.Event()
        execute = Mock(side_effect=lambda _script: delivered.set())
        event = Event()
        event.handlers.append(original)
        control = SimpleNamespace(WebMessageReceived=event, NavigationStarting=Event(),
                                  CoreWebView2=SimpleNamespace(FrameNavigationStarting=Event(),
                                                              Source='http://127.0.0.1:4321/',
                                                              ExecuteScriptAsync=execute),
                                  BeginInvoke=lambda callback: callback())
        bridge = Mock()
        bridge.import_dropped_documents.return_value = {'documents': [], 'errors': []}
        window = SimpleNamespace(native=SimpleNamespace(browser=SimpleNamespace(
            webview=control, on_script_notify=original)),
            original_url='http://127.0.0.1:4321',
            _js_api=bridge, run_js=Mock(side_effect=lambda _script: delivered.set()))
        _install_file_drop_transport(window)
        _install_file_drop_transport(window)
        self.assertEqual(len(event.handlers), 1)
        args = Mock()
        args.Source = 'http://127.0.0.1:4321/'
        args.get_WebMessageAsJson.return_value = json.dumps(['get_state', '[]', 'normal'])
        event.handlers[0](None, args)
        original.assert_called_once_with(None, args)
        original.reset_mock()
        for name in ('_store.save_settings', '_window.destroy', 'get_state.__call__'):
            args.get_WebMessageAsJson.return_value = json.dumps([name, '[{"theme":"dark"}]', 'private123'])
            event.handlers[0](None, args)
        original.assert_not_called()
        args.get_WebMessageAsJson.return_value = json.dumps({'type': 'violilt:file-drop', 'id': 'request123', 'paths': ['C:/untrusted.md']})
        args.get_AdditionalObjects.return_value = [CoreWebView2File(), object()]
        event.handlers[0](None, args)
        self.assertTrue(delivered.wait(3))
        bridge.import_dropped_documents.assert_called_once_with(['C:/notes/original.md'])
        self.assertTrue(execute.call_args.args[0].startswith('window.pywebview._returnValuesCallbacks["import_dropped_documents"]["request123"]'))

        original.reset_mock()
        bridge.reset_mock()
        for source in ('https://external.example/', 'http://127.0.0.1:4322/',
                       'http://localhost:4321/', 'http://127.0.0.1:4321/media/a.wav'):
            args.Source = source
            args.get_WebMessageAsJson.return_value = json.dumps(['get_state', '[]', 'normal'])
            event.handlers[0](None, args)
            args.get_WebMessageAsJson.return_value = json.dumps({'type': 'violilt:file-drop', 'id': 'request456'})
            event.handlers[0](None, args)
        original.assert_not_called()
        bridge.import_dropped_documents.assert_not_called()
        for target, blocked in [('https://external.example/', True), ('file:///C:/notes/a.md', True),
                                ('http://127.0.0.1:4321/?preview=1', False)]:
            request = SimpleNamespace(Uri=target, Cancel=False)
            control.NavigationStarting.handlers[0](None, request)
            self.assertEqual(request.Cancel, blocked)
        frame = SimpleNamespace(Cancel=False)
        control.CoreWebView2.FrameNavigationStarting.handlers[0](None, frame)
        self.assertTrue(frame.Cancel)

    def test_native_page_validation_rejects_lookalike_origins_and_malformed_ports(self):
        window = SimpleNamespace(original_url='http://127.0.0.1:4321')
        for value in ('http://127.0.0.1:4321@external.example/', 'http://127.0.0.1:4321.external.example/',
                      'http://127.0.0.1:bad/', 'data:text/html,hello', 'about:blank'):
            self.assertFalse(_trusted_page(window, value))
        self.assertTrue(_trusted_page(window, 'http://127.0.0.1:4321/index.html#reading'))

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
