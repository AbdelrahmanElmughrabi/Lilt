"""GPU runtime selection must not authorize code using a self-written marker."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import runtime


class RuntimeTrustTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.good = self.root / 'approved'
        self.good.mkdir()
        self.files = {
            'onnxruntime/__init__.py': b'approved = True\n',
            'onnxruntime/capi/onnxruntime_providers_cuda.dll': b'approved CUDA fixture',
            'nvidia/cudnn/bin/cudnn64_9.dll': b'approved cuDNN fixture',
        }
        for name, body in self.files.items():
            path = self.good / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        self.pins = {name: (len(body), hashlib.sha256(body).hexdigest()) for name, body in self.files.items()}
        self.marker = {'provider': 'CUDAExecutionProvider', 'runtime': '1.24.4',
                       'tested_model': 'kokoro-v1.0.fp16-gpu.onnx'}
        (self.good / 'violilt-runtime.json').write_text(json.dumps(self.marker))
        self.environment = patch.dict(os.environ, {'VIOLILT_GPU_RUNTIME': str(self.good)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        pins = patch.object(runtime, 'APPROVED', self.pins, create=True)
        pins.start()
        self.addCleanup(pins.stop)

    def tearDown(self):
        self.temporary.cleanup()

    def test_a_marker_and_package_name_cannot_approve_another_runtime(self):
        unapproved = self.root / 'unapproved'
        (unapproved / 'onnxruntime').mkdir(parents=True)
        (unapproved / 'onnxruntime/__init__.py').write_text('unapproved = True\n')
        (unapproved / 'violilt-runtime.json').write_text(json.dumps(self.marker))
        with patch.dict(os.environ, {'VIOLILT_GPU_RUNTIME': str(unapproved)}):
            self.assertIsNone(runtime.gpu_runtime_directory())
            self.assertIsNone(runtime.gpu_runtime_info())

    def test_changed_code_and_native_libraries_are_rejected_even_with_preserved_stats(self):
        for name, original in self.files.items():
            with self.subTest(name=name):
                path = self.good / name
                stat = path.stat()
                path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                try:
                    self.assertIsNone(runtime.gpu_runtime_directory())
                finally:
                    path.write_bytes(original)

    def test_extra_imports_dlls_and_bytecode_cannot_shadow_the_cpu_environment(self):
        for name in ('numpy.py', 'onnxruntime/extra.py', 'nvidia/cudnn/bin/unapproved.dll',
                     'onnxruntime/__pycache__/__init__.cpython-312.pyc'):
            with self.subTest(name=name):
                path = self.good / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'inert unapproved fixture')
                try:
                    self.assertIsNone(runtime.gpu_runtime_directory())
                finally:
                    path.unlink()
                    if path.parent.name == '__pycache__':
                        path.parent.rmdir()

    def test_bad_or_changed_markers_do_not_advertise_gpu_availability(self):
        marker = self.good / 'violilt-runtime.json'
        for body in ('{', '[]', json.dumps(self.marker | {'runtime': 'unapproved'}),
                     json.dumps(self.marker | {'provider': 'unapproved'})):
            with self.subTest(body=body):
                marker.write_text(body)
                self.assertIsNone(runtime.gpu_runtime_directory())
                self.assertIsNone(runtime.gpu_runtime_info())

    def test_frozen_app_uses_only_its_verified_bundled_runtime(self):
        executable = self.root / 'application/Violilt.exe'
        executable.parent.mkdir()
        bundled = executable.parent / 'gpu-runtime'
        shutil.copytree(self.good, bundled)
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(executable)):
            self.assertEqual(runtime.gpu_runtime_directory(), bundled)
            with self.assertRaisesRegex(ValueError, 'bundled GPU runtime'):
                runtime.activate_gpu_runtime(self.good)
            (bundled / 'onnxruntime/__init__.py').write_bytes(b'changed')
            self.assertIsNone(runtime.gpu_runtime_directory())

    def test_linked_runtime_root_is_not_a_trusted_folder(self):
        linked = self.root / 'linked'
        if os.name == 'nt':
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(linked), str(self.good)], capture_output=True)
            if result.returncode:
                self.skipTest('Directory junction creation is unavailable in this environment.')
        else:
            linked.symlink_to(self.good, target_is_directory=True)
        with patch.dict(os.environ, {'VIOLILT_GPU_RUNTIME': str(linked)}):
            self.assertIsNone(runtime.gpu_runtime_directory())

    def test_worker_revalidates_its_argument_before_importing_any_runtime_code(self):
        marker = self.root / 'executed.txt'
        (self.good / 'numpy.py').write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n')
        code = '''
import json, queue, sys, threading
from pathlib import Path
from backend import runtime
runtime.APPROVED = {name: tuple(pin) for name, pin in json.loads(sys.argv[2]).items()}
from backend.speech import speech_worker
commands = queue.Queue()
commands.put(None)
try:
    speech_worker(commands, queue.Queue(), threading.Event(), Path(sys.argv[1]))
except ValueError:
    pass
'''
        result = subprocess.run([sys.executable, '-B', '-c', code, str(self.good), json.dumps(self.pins)],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists(), 'Unverified runtime code executed before the worker rejected it.')

    def test_valid_runtime_still_works_after_rejected_candidates(self):
        self.assertEqual(runtime.gpu_runtime_directory(), self.good)
        self.assertEqual(runtime.gpu_runtime_info(), self.marker)
        missing = self.good / 'nvidia/cudnn/bin/cudnn64_9.dll'
        missing.unlink()
        self.assertIsNone(runtime.gpu_runtime_directory())
        missing.write_bytes(self.files['nvidia/cudnn/bin/cudnn64_9.dll'])
        self.assertEqual(runtime.gpu_runtime_directory(), self.good)

    def test_cuda_engine_does_not_scan_or_mutate_path_or_use_default_dll_fallback(self):
        from backend.performance import create_engine
        from unittest.mock import Mock
        foreign = self.root / 'foreign/nvidia/other/bin'
        foreign.mkdir(parents=True)
        ort = Mock()
        ort.get_available_providers.return_value = ['CPUExecutionProvider', 'CUDAExecutionProvider']
        ort.InferenceSession.return_value.get_providers.return_value = ['CUDAExecutionProvider']
        original_path = os.environ.get('PATH', '')
        with patch.dict(sys.modules, {'onnxruntime': ort}), \
             patch('backend.model_trust.verify_file'), \
             patch('backend.kokoro_engine.Kokoro.from_session', return_value='fixture engine'), \
             patch.object(runtime, 'load_cuda_libraries', create=True) as load, \
             patch.object(sys, 'path', sys.path + [str(foreign.parents[2])]):
            try:
                self.assertEqual(create_engine(self.root / 'kokoro-v1.0.fp16-gpu.onnx',
                                 self.root / 'voices-v1.0.bin', {'provider': 'CUDAExecutionProvider',
                                 'device_id': 0, 'threads': 1}), 'fixture engine')
                ort.preload_dlls.assert_not_called()
                self.assertEqual(os.environ.get('PATH', ''), original_path)
                load.assert_called_once_with()
            finally:
                os.environ['PATH'] = original_path

    def test_preparation_copies_only_pinned_files_and_preserves_its_source(self):
        from tools.prepare_gpu_runtime import prepare_runtime
        (self.good / 'numpy.py').write_bytes(b'inert unapproved source extra')
        (self.good / 'violilt-runtime.json').unlink()  # Preparing bytes does not claim a successful CUDA probe.
        before = {path.relative_to(self.good).as_posix(): path.read_bytes()
                  for path in self.good.rglob('*') if path.is_file()}
        output = self.root / 'prepared'
        result = prepare_runtime(self.good, output)
        self.assertEqual(result['files'], len(self.pins))
        self.assertEqual(runtime.verify_gpu_runtime(output), output)
        self.assertFalse((output / 'numpy.py').exists())
        self.assertNotIn('tested_model', json.loads((output / 'violilt-runtime.json').read_text()))
        self.assertEqual(before, {path.relative_to(self.good).as_posix(): path.read_bytes()
                                for path in self.good.rglob('*') if path.is_file()})
        with self.assertRaises(FileExistsError):
            prepare_runtime(self.good, output)

    def test_preparation_rejects_changed_pinned_bytes_and_overlapping_output(self):
        from tools.prepare_gpu_runtime import prepare_runtime
        with self.assertRaisesRegex(ValueError, 'separate'):
            prepare_runtime(self.good, self.good / 'nested')
        (self.good / 'onnxruntime/__init__.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'unapproved GPU runtime'):
            prepare_runtime(self.good, self.root / 'rejected')
        with self.assertRaises(ValueError):
            runtime.verify_gpu_runtime(self.root / 'rejected')


if __name__ == '__main__':
    unittest.main()
