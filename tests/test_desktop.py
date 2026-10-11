import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.desktop import install_csp_bridge


class DesktopBridgeTests(unittest.TestCase):
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
