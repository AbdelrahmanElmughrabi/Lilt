"""Exact fixed-link/state/native boundary; no speech imports or real OS opening."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from backend.desktop import _allowed_native_call, _trusted_page

ROOT = Path(__file__).resolve().parents[1]
LINKS = {
    'publisher': 'https://velourvolute.com',
    'app': 'https://velourvolute.com/violilt',
    'privacy': 'https://velourvolute.com/violilt/privacypolicy',
    'support': 'https://velourvolute.com/violilt/support',
}


class PublisherLinksTests(unittest.TestCase):
    def setUp(self):
        source = ast.parse((ROOT / 'backend/bridge.py').read_text(encoding='utf-8'))
        mapping = next(node for node in source.body if isinstance(node, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == 'PUBLISHER_LINKS' for t in node.targets))
        bridge = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == 'Bridge')
        methods = [next(node for node in bridge.body if isinstance(node, ast.FunctionDef) and node.name == name)
                   for name in ('get_state', 'open_publisher_link')]
        self.opener = Mock()
        self.namespace = {'os': SimpleNamespace(startfile=self.opener), 'public_job': lambda job: job}
        # Execute the actual source nodes unchanged with an inert OS opener.
        exec(compile(ast.Module(body=[mapping, *methods], type_ignores=[]), 'backend/bridge.py', 'exec'), self.namespace)
        self.open = lambda ref: self.namespace['open_publisher_link'](None, ref)
        self.assertEqual(self.namespace['PUBLISHER_LINKS'], LINKS)

    def test_fixed_references_open_exact_addresses_and_arbitrary_inputs_are_rejected(self):
        for reference, url in LINKS.items():
            with self.subTest(reference=reference):
                self.assertIs(self.open(reference), True)
                self.opener.assert_called_with(url)
        for invalid in (None, True, 1, [], {}, *LINKS.values(), 'file:///C:/x',
                        'javascript:alert(1)', 'privacy?url=evil', 'PRIVACY', 'support\n'):
            with self.subTest(invalid=invalid):
                self.opener.reset_mock()
                with self.assertRaises(ValueError):
                    self.open(invalid)
                self.opener.assert_not_called()

    def test_open_failure_is_actionable_and_retry_uses_the_same_fixed_address(self):
        self.opener.side_effect = OSError('Synthetic private path')
        with self.assertRaisesRegex(RuntimeError, 'Retry, or copy the address') as result:
            self.open('privacy')
        self.assertNotIn('Synthetic private path', str(result.exception))
        self.opener.side_effect = None
        self.assertIs(self.open('privacy'), True)
        self.assertEqual(self.opener.call_count, 2)

    def test_state_exposes_copyable_addresses_without_allowing_opener_mapping_mutation(self):
        owner = SimpleNamespace(
            _store=SimpleNamespace(all=lambda table: [], settings=lambda: {}, root=Path('fixture'),
                                   recovery_summary=lambda: {'count': 0, 'message': ''}),
            _models=SimpleNamespace(status=lambda: {'state': 'missing', 'voices': []}),
            _jobs=SimpleNamespace(state=lambda: None, performance_state=lambda: None,
                                  cache_state=lambda: {'count': 0, 'bytes': 0}))
        state = self.namespace['get_state'](owner)
        self.assertEqual(state['publisher_links'], LINKS)
        state['publisher_links']['privacy'] = 'https://example.invalid'
        self.open('privacy')
        self.opener.assert_called_once_with(LINKS['privacy'])

    def test_native_contract_accepts_one_reference_and_external_navigation_stays_blocked(self):
        window = SimpleNamespace(_js_api=SimpleNamespace(open_publisher_link=Mock()),
                                 original_url='http://127.0.0.1:41234/')
        self.assertTrue(_allowed_native_call(window, ['open_publisher_link', '["privacy"]', 'publisher1']))
        for params in ('[]', '["privacy", "app"]', '{}'):
            self.assertFalse(_allowed_native_call(window, ['open_publisher_link', params, 'publisher1']))
        for url in LINKS.values():
            self.assertFalse(_trusted_page(window, url))
        self.assertTrue(_trusted_page(window, 'http://127.0.0.1:41234/index.html'))


if __name__ == '__main__':
    unittest.main()
