"""A release build must reject an older or changed selected interpreter."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.verify_release_runtime import verify


class ReleaseRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'core.dll').write_bytes(b'selected runtime fixture')
        self.observed = {'python': '3.12.15', 'bits': 64, 'expat': 'expat_2.8.5',
                         'openssl': 'OpenSSL 3.5.9 29 Sep 2026'}
        self.policy = {'expected': self.observed.copy(),
                       'native_files': {'core.dll': hashlib.sha256(b'selected runtime fixture').hexdigest()},
                       'expat_disposition': {'status': 'independent review pending'}}

    def test_matching_selected_inputs_return_the_disposition_without_claiming_a_patch(self):
        result = verify(self.policy, self.root, self.observed)
        self.assertEqual(result['native_files_verified'], 1)
        self.assertEqual(result['expat_disposition']['status'], 'independent review pending')

    def test_old_wrong_architecture_or_unreviewed_component_versions_fail(self):
        for key, value in (('python', '3.12.14'), ('bits', 32), ('expat', 'expat_2.8.3'),
                           ('openssl', 'OpenSSL 3.5.8')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify(self.policy, self.root, self.observed | {key: value})

    def test_changed_or_missing_native_bytes_fail(self):
        (self.root / 'core.dll').write_bytes(b'changed')
        with self.assertRaises(ValueError): verify(self.policy, self.root, self.observed)
        (self.root / 'core.dll').unlink()
        with self.assertRaises(OSError): verify(self.policy, self.root, self.observed)

    def test_pin_cannot_escape_the_runtime_base(self):
        policy = copy.deepcopy(self.policy)
        policy['native_files'] = {'../outside.dll': '0' * 64}
        with self.assertRaises(ValueError): verify(policy, self.root, self.observed)


if __name__ == '__main__': unittest.main()
