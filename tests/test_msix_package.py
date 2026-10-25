"""Release-boundary checks: isolate libraries and retain the complete GPU payload."""
import hashlib
import json
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from PyInstaller.archive.writers import CArchiveWriter, ZlibArchiveWriter

from backend.model_trust import APPROVED
from backend import runtime
from tools.msix_package import FOUNDATION, PROFILE, REQUIRED, ROOT, prepare, package_version
from tools.package_pronunciation_audit import audit


class MsixPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.payload = self.root / 'payload'
        for name in REQUIRED:
            path = self.payload / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
        for name in ('misaki/data/us_gold.json', 'misaki/data/us_silver.json',
                     'misaki/data/gb_gold.json', 'misaki/data/gb_silver.json',
                     'num2words/__init__.py'):
            path = self.payload / '_internal' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
        for name in ('misaki', 'spacy', 'thinc', 'regex', 'addict', 'numpy', 'en_core_web_sm', 'num2words'):
            path = self.payload / '_internal' / (name + '-1.0.dist-info')
            path.mkdir(parents=True)
            (path / 'METADATA').write_text('Name: ' + name + '\nVersion: 1.0\n')
        sources = self.payload / 'third-party/sources'
        sources.mkdir()
        (sources / 'source-manifest.json').write_text('{}')
        self.write_executable()
        pins = {}
        for name in APPROVED:
            body = ('approved disposable fixture: ' + name).encode()
            (self.payload / 'models' / name).write_bytes(body)
            pins[name] = (len(body), hashlib.sha256(body).hexdigest())
        self.pin_patch = patch.dict(APPROVED, pins, clear=True)
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)
        self.original_marker = json.dumps({'data_profile': 'Violilt-Pronunciation-Evaluation'})
        (self.payload / 'violilt-candidate.json').write_text(self.original_marker, encoding='utf-8')
        (self.payload / 'package-audit.json').write_text(json.dumps({'status': 'pass', 'violations': []}))
        gpu_root = self.payload / 'gpu-runtime'
        (gpu_root / 'violilt-runtime.json').write_text(json.dumps(runtime.MARKER))
        runtime_pins = {path.relative_to(gpu_root).as_posix():
                        (path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
                        for path in gpu_root.rglob('*') if path.is_file() and path.name != 'violilt-runtime.json'}
        gpu_patch = patch.object(runtime, 'APPROVED', runtime_pins)
        gpu_patch.start()
        self.addCleanup(gpu_patch.stop)
        self.make_stage('stage')
        self.config = ROOT / 'packaging/msix/compatibility.json'

    def make_stage(self, name):
        self.stage = self.root / name
        assets = self.stage / 'Assets'
        assets.mkdir(parents=True)
        for name in ('StoreLogo.png', 'Square150x150Logo.png', 'Square44x44Logo.png'):
            (assets / name).write_bytes(b'fixture')

    def tearDown(self):
        self.temporary.cleanup()

    def build(self):
        return prepare(self.payload, self.stage, '1.0.0.0', self.config)

    def write_executable(self, modules=None):
        inputs = self.root / 'archive-inputs'
        inputs.mkdir(exist_ok=True)
        modules = modules or {'backend.speech': 'from backend.kokoro_engine import Kokoro\n',
                              'backend.pcm_audio': 'def write_pcm16(destination, samples, samplerate=24000): pass\n'}
        entries, code = [], {}
        for name, source in modules.items():
            path = inputs / (name + '.py')
            path.write_text(source)
            entries.append((name, str(path), 'PYMODULE'))
            code[name] = compile(source, str(path), 'exec')
        pyz = inputs / 'PYZ.pyz'
        ZlibArchiveWriter(str(pyz), entries, code_dict=code)
        main = inputs / 'main.py'
        main.write_text('from backend.speech import speech_worker\n')
        archive = inputs / 'package.pkg'
        CArchiveWriter(str(archive), [('PYZ.pyz', str(pyz), False, 'z'),
                                     ('main', str(main), True, 's')], 'python312.dll')
        executable = bytearray(160)
        executable[:2] = b'MZ'
        struct.pack_into('<I', executable, 0x3c, 128)
        executable[128:134] = b'PE\0\0\x64\x86'
        (self.payload / 'Violilt.exe').write_bytes(executable + archive.read_bytes())

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

    def test_changed_cpu_gpu_or_voice_bytes_cannot_reuse_a_passing_audit(self):
        for index, name in enumerate(APPROVED):
            with self.subTest(name=name):
                self.make_stage('model-stage-' + str(index))
                path = self.payload / 'models' / name
                original = path.read_bytes()
                path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                try:
                    with self.assertRaisesRegex(ValueError, 'integrity check'):
                        self.build()
                    self.assertFalse((self.stage / 'mapping.txt').exists())
                    self.assertFalse((self.stage / 'inventory.json').exists())
                finally:
                    path.write_bytes(original)

    def test_changed_gpu_runtime_code_or_dll_cannot_reuse_a_passing_audit(self):
        for index, name in enumerate(('onnxruntime/__init__.py', 'onnxruntime/capi/onnxruntime_providers_cuda.dll')):
            with self.subTest(name=name):
                self.make_stage('runtime-stage-' + str(index))
                path = self.payload / 'gpu-runtime' / name
                original = path.read_bytes()
                path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                try:
                    with self.assertRaisesRegex(ValueError, 'GPU runtime'):
                        self.build()
                    self.assertFalse((self.stage / 'mapping.txt').exists())
                finally:
                    path.write_bytes(original)

    def test_added_espeak_components_cannot_reuse_a_passing_audit(self):
        for index, name in enumerate(('_internal/espeak-ng.dll', '_internal/vendor/espeak-ng-data/phondata',
                                      'gpu-runtime/nested/espeakng_loader/__init__.py',
                                      '_internal/phonemizer_fork/__init__.py')):
            with self.subTest(name=name):
                self.make_stage('component-stage-' + str(index))
                path = self.payload / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'inert disposable marker')
                try:
                    with self.assertRaisesRegex(ValueError, 'audit must pass'):
                        self.build()
                    self.assertFalse((self.stage / 'mapping.txt').exists())
                finally:
                    path.unlink()

    def test_changed_executable_is_checked_for_frozen_modules_and_dormant_imports(self):
        for index, modules in enumerate(({'espeakng_loader': 'pass\n'},
                                         {'backend.speech': 'def unused():\n    import phonemizer\n'})):
            with self.subTest(modules=modules):
                self.make_stage('executable-stage-' + str(index))
                self.write_executable(modules)
                with self.assertRaisesRegex(ValueError, 'audit must pass'):
                    self.build()
                self.assertFalse((self.stage / 'mapping.txt').exists())

    def test_unreadable_executable_archive_cannot_reuse_a_passing_audit(self):
        path = self.payload / 'Violilt.exe'
        path.write_bytes(path.read_bytes()[:160])
        with self.assertRaisesRegex(ValueError, 'audit'):
            self.build()
        self.assertFalse((self.stage / 'mapping.txt').exists())

    def test_payload_changes_after_the_audit_do_not_publish_a_mapping(self):
        for index, name in enumerate(('models/voices-v1.0.bin', '_internal/num2words/__init__.py')):
            with self.subTest(name=name):
                self.make_stage('changed-stage-' + str(index))
                path = self.payload / name
                original = path.read_bytes()

                def change_after_audit(*args, **kwargs):
                    result = audit(*args, **kwargs)
                    path.write_bytes(original + b' changed after audit')
                    return result

                try:
                    with patch('tools.msix_package.audit', side_effect=change_after_audit, create=True):
                        with self.assertRaisesRegex(ValueError, 'changed after its audit'):
                            self.build()
                    self.assertFalse((self.stage / 'mapping.txt').exists())
                    self.assertFalse((self.stage / 'inventory.json').exists())
                finally:
                    path.write_bytes(original)

    def test_fresh_audit_is_staged_without_changing_the_original_payload(self):
        original = {path.relative_to(self.payload).as_posix(): path.read_bytes()
                    for path in self.payload.rglob('*') if path.is_file()}
        report = self.build()
        current = {path.relative_to(self.payload).as_posix(): path.read_bytes()
                   for path in self.payload.rglob('*') if path.is_file()}
        self.assertEqual(current, original)
        self.assertTrue((self.stage / 'package-audit.json').is_file())
        audit = json.loads((self.stage / 'package-audit.json').read_text())
        self.assertEqual(audit['status'], 'pass')
        self.assertIn('backend.speech', audit['frozen_modules'])
        self.assertEqual(audit['violations'], [])
        staged_marker = (self.stage / 'violilt-candidate.json').read_bytes()
        marker = next(item for item in audit['files'] if item['path'] == 'violilt-candidate.json')
        self.assertEqual(marker['sha256'], hashlib.sha256(staged_marker).hexdigest())
        self.assertEqual(report['verified_models'], {name: pin[1] for name, pin in APPROVED.items()})
        mapping = (self.stage / 'mapping.txt').read_text()
        self.assertIn(str(self.stage / 'package-audit.json'), mapping)
        self.assertNotIn(str(self.payload / 'package-audit.json'), mapping)

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


    def test_removed_native_audio_is_rejected_but_legal_text_is_allowed(self):
        legal = self.payload/'third-party/native/libsndfile-historical-LICENSE.txt'
        legal.parent.mkdir(parents=True, exist_ok=True)
        legal.write_text('Preserved historical notice')
        self.assertEqual(audit(self.payload, write_report=False)['violations'], [])
        for relative in ('_internal/other/libsndfile_x64.dll', 'third-party/native/libsndfile_x64.dll'):
            with self.subTest(relative=relative):
                rogue = self.payload/relative
                rogue.parent.mkdir(parents=True, exist_ok=True)
                rogue.write_bytes(b'inert forbidden native fixture')
                try:
                    result = audit(self.payload, write_report=False)
                    self.assertTrue(any('Removed SoundFile/libsndfile runtime file' in v for v in result['violations']))
                finally:
                    rogue.unlink()

    def test_generated_pcm_writer_code_is_required(self):
        self.write_executable({'backend.speech': 'pass\n'})
        result = audit(self.payload, write_report=False)
        self.assertFalse(result['generated_pcm16_writer_present'])
        self.assertTrue(any('Required generated PCM16 writer missing' in v for v in result['violations']))


if __name__ == '__main__':
    unittest.main()
