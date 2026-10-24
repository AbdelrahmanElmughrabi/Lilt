"""Exercise the exact Bridge opener method without loading speech/native modules."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from backend.desktop import _allowed_native_call, _trusted_page

ROOT = Path(__file__).resolve().parents[1]
LINKS = {
    'privacy-statement': 'https://privacy.microsoft.com/privacystatement',
    'smartscreen': 'https://learn.microsoft.com/en-us/legal/microsoft-edge/privacy#smartscreen',
}


class MicrosoftPrivacyLinksTests(unittest.TestCase):
    def setUp(self):
        source = ast.parse((ROOT / 'backend/bridge.py').read_text(encoding='utf-8'))
        mapping = next(node for node in source.body if isinstance(node, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == 'MICROSOFT_PRIVACY_LINKS' for t in node.targets))
        bridge = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == 'Bridge')
        method = next(node for node in bridge.body if isinstance(node, ast.FunctionDef) and node.name == 'open_microsoft_privacy')
        self.opener = Mock()
        namespace = {'os': SimpleNamespace(startfile=self.opener)}
        # Compile these source nodes unchanged; all OS opening is replaced.
        exec(compile(ast.Module(body=[mapping, method], type_ignores=[]), 'backend/bridge.py', 'exec'), namespace)
        self.open = lambda reference: namespace['open_microsoft_privacy'](None, reference)
        self.assertEqual(namespace['MICROSOFT_PRIVACY_LINKS'], LINKS)

    def test_only_fixed_references_reach_os_opener(self):
        for reference, url in LINKS.items():
            with self.subTest(reference=reference):
                self.assertIs(self.open(reference), True)
                self.opener.assert_called_with(url)
        for invalid in (None, True, 1, [], {}, 'https://example.org', 'file:///C:/x',
                        'privacy-statement?url=evil', 'PRIVACY-STATEMENT', 'smartscreen\n'):
            with self.subTest(invalid=invalid):
                self.opener.reset_mock()
                with self.assertRaises(ValueError):
                    self.open(invalid)
                self.opener.assert_not_called()

    def test_open_failure_is_actionable_and_retry_uses_same_fixed_link(self):
        self.opener.side_effect = OSError('synthetic private path must not be shown')
        with self.assertRaisesRegex(RuntimeError, 'Retry, or copy the address') as result:
            self.open('smartscreen')
        self.assertNotIn('synthetic private path', str(result.exception))
        self.opener.side_effect = None
        self.assertIs(self.open('smartscreen'), True)
        self.assertEqual(self.opener.call_count, 2)

    def test_native_contract_and_navigation_stay_confined(self):
        window = SimpleNamespace(_js_api=SimpleNamespace(open_microsoft_privacy=Mock()),
                                 original_url='http://127.0.0.1:41234/')
        for reference in LINKS:
            self.assertTrue(_allowed_native_call(window, ['open_microsoft_privacy', json.dumps([reference]), 'notice1']))
        for params in ('[]', '["smartscreen", "other"]', '{}'):
            self.assertFalse(_allowed_native_call(window, ['open_microsoft_privacy', params, 'notice1']))
        for url in (*LINKS.values(), 'https://example.org', 'file:///C:/x', 'http://127.0.0.1:41235/'):
            self.assertFalse(_trusted_page(window, url))
        self.assertTrue(_trusted_page(window, 'http://127.0.0.1:41234/index.html'))


if __name__ == '__main__':
    unittest.main()
