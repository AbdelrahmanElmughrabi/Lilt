"""Release-boundary checks: isolate libraries and retain the complete GPU payload."""
import json
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.msix_package import FOUNDATION, PROFILE, REQUIRED, ROOT, prepare, package_version


class MsixPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.payload = self.root / 'payload'
        for name in REQUIRED:
            path = self.payload / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
        executable = bytearray(160)
        executable[:2] = b'MZ'
        struct.pack_into('<I', executable, 0x3c, 128)
        executable[128:134] = b'PE\0\0\x64\x86'
        (self.payload / 'Violilt.exe').write_bytes(executable)
        self.original_marker = json.dumps({'data_profile': 'Violilt-Pronunciation-Evaluation'})
        (self.payload / 'violilt-candidate.json').write_text(self.original_marker, encoding='utf-8')
        (self.payload / 'package-audit.json').write_text(json.dumps({'status': 'pass', 'violations': []}))
        (self.payload / 'gpu-runtime/violilt-runtime.json').write_text(json.dumps({'provider': 'CUDAExecutionProvider'}))
        self.stage = self.root / 'stage'
        assets = self.stage / 'Assets'
        assets.mkdir(parents=True)
        for name in ('StoreLogo.png', 'Square150x150Logo.png', 'Square44x44Logo.png'):
            (assets / name).write_bytes(b'fixture')
        self.config = ROOT / 'packaging/msix/compatibility.json'

    def tearDown(self):
        self.temporary.cleanup()

    def build(self):
        return prepare(self.payload, self.stage, '1.0.0.0', self.config)

    def test_package_isolated_without_mutating_input_and_keeps_cpu_and_gpu(self):
        report = self.build()
        self.assertFalse(report['store_ready'])
        self.assertEqual(report['data_profile'], PROFILE)
        self.assertEqual((self.payload / 'violilt-candidate.json').read_text(), self.original_marker)
        self.assertEqual(json.loads((self.stage / 'violilt-candidate.json').read_text())['data_profile'], PROFILE)
        paths = {entry['path'] for entry in report['files']}
        self.assertIn('App/models/kokoro-v1.0.int8.onnx', paths)
        self.assertIn('App/models/kokoro-v1.0.fp16-gpu.onnx', paths)
        self.assertIn('App/gpu-runtime/onnxruntime/capi/onnxruntime_providers_cuda.dll', paths)
        self.assertNotIn('inventory.json', paths)
        self.assertNotIn('mapping.txt', paths)
        manifest = ET.parse(self.stage / 'AppxManifest.xml').getroot()
        self.assertEqual(manifest.find(f'{{{FOUNDATION}}}Identity').attrib['Name'], 'Violilt.MsixCompatibilityProbe')
        self.assertEqual(manifest.find(f'{{{FOUNDATION}}}Applications/{{{FOUNDATION}}}Application').attrib['Executable'], 'App\\Violilt.exe')

    def test_incomplete_gpu_payload_cannot_be_published_as_cpu_only(self):
        (self.payload / 'gpu-runtime/onnxruntime/capi/onnxruntime_providers_cuda.dll').unlink()
        with self.assertRaisesRegex(ValueError, 'required CPU/GPU'):
            self.build()

    def test_failed_payload_audit_stops_packaging(self):
        (self.payload / 'package-audit.json').write_text(json.dumps({'status': 'fail', 'violations': ['unexpected module']}))
        with self.assertRaisesRegex(ValueError, 'audit must pass'):
            self.build()

    def test_private_library_file_is_rejected(self):
        (self.payload / 'models/library.sqlite3').write_bytes(b'private library')
        with self.assertRaisesRegex(ValueError, 'Private/generated'):
            self.build()

    def test_staging_inside_payload_is_rejected_before_packaging(self):
        with self.assertRaisesRegex(ValueError, 'must be separate'):
            prepare(self.payload, self.payload / 'stage', '1.0.0.0', self.config)

    def test_real_publisher_identity_cannot_be_used_by_compatibility_builder(self):
        config = json.loads(self.config.read_text())
        config['publisher'] = 'CN=Production Publisher'
        custom = self.root / 'config.json'
        custom.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, 'local compatibility identity'):
            prepare(self.payload, self.stage, '1.0.0.0', custom)

    def test_non_x64_executable_is_rejected(self):
        executable = bytearray((self.payload / 'Violilt.exe').read_bytes())
        executable[132:134] = b'\x4c\x01'
        (self.payload / 'Violilt.exe').write_bytes(executable)
        with self.assertRaisesRegex(ValueError, 'x64 executable'):
            self.build()

    def test_version_rejects_reserved_field_and_path_injection(self):
        for version in ('0.1.0.0', '1.0.0.1', '1.0.0', '../1.0.0.0', '65536.0.0.0', '01.0.0.0'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                package_version(version)


if __name__ == '__main__':
    unittest.main()
