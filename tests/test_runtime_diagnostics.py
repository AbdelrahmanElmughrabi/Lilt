"""Source integration checks; real ONNX, audio and hardware imports are forbidden."""
import builtins
from contextlib import contextmanager, ExitStack
import importlib
import importlib.abc
from pathlib import Path
import queue
import sys
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ERROR_MESSAGE = ("The voice runtime's diagnostic settings could not be applied. "
                 "Restart Violilt; if this continues, repair the installation.")
BLOCKED_ROOTS = {'onnxruntime', 'numpy', 'soundfile', 'psutil', 'webview', 'spacy', 'misaki'}
performance = speech = runtime = pronunciation = model_trust = None


class NativeImportGuard(importlib.abc.MetaPathFinder):
    def __init__(self):
        self.attempts = []

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in BLOCKED_ROOTS:
            self.attempts.append(fullname)
            raise AssertionError('Real third-party/native import forbidden: ' + fullname)
        return None


native_guard = NativeImportGuard()


def remove_native_guard():
    while native_guard in sys.meta_path:
        sys.meta_path.remove(native_guard)


def setUpModule():
    global performance, speech, runtime, pronunciation, model_trust
    # A broader suite can already have these dependencies loaded. The fixtures
    # shadow and restore them; forbid new real imports during this module only.
    sys.meta_path.insert(0, native_guard)
    unittest.addModuleCleanup(remove_native_guard)
    performance = importlib.import_module('backend.performance')
    speech = importlib.import_module('backend.speech')
    runtime = importlib.import_module('backend.runtime')
    pronunciation = importlib.import_module('backend.pronunciation')
    model_trust = importlib.import_module('backend.model_trust')


def tearDownModule():
    if native_guard.attempts:
        raise AssertionError('Blocked real imports: ' + ', '.join(native_guard.attempts))


def fake_runtime(label, ledger, api='ok'):
    ort = ModuleType('onnxruntime')
    ort.__version__ = label
    ort.__file__ = 'SYNTHETIC_RUNTIME/' + label + '/__init__.py'
    ort.requests = 0
    ort.sessions = []
    ort.options = []

    def disable():
        ledger.append('control:' + label)
        if api == 'raises':
            raise OSError('SYNTHETIC_PRIVATE_CONTENT at C:/SYNTHETIC_PRIVATE_PATH')
        ort.requests += 1

    if api != 'missing':
        ort.disable_telemetry_events = None if api == 'noncallable' else disable

    def require_control(event):
        ledger.append(event)
        if ort.requests == 0:
            raise AssertionError(event + ' happened before the diagnostic-control request')

    def providers():
        require_control('providers')
        return ['CPUExecutionProvider', 'CUDAExecutionProvider']

    def options():
        require_control('options')
        result = SimpleNamespace(entries={})
        result.add_session_config_entry = lambda key, value: result.entries.update({key: value})
        ort.options.append(result)
        return result

    def session(model, *, sess_options, providers):
        require_control('session')
        selected = [item[0] if isinstance(item, tuple) else item for item in providers]
        result = SimpleNamespace(get_providers=lambda: selected,
                                 disable_fallback=Mock(side_effect=lambda: ledger.append('no-fallback')))
        ort.sessions.append((model, sess_options, providers, result))
        return result

    ort.get_available_providers = Mock(side_effect=providers)
    ort.SessionOptions = Mock(side_effect=options)
    ort.InferenceSession = Mock(side_effect=session)
    ort.ExecutionMode = SimpleNamespace(ORT_SEQUENTIAL='sequential-fixture')
    ort.GraphOptimizationLevel = SimpleNamespace(ORT_ENABLE_ALL='all-fixture')
    return ort


class KokoroModule(ModuleType):
    def __init__(self, ort, ledger, engine):
        super().__init__('backend.kokoro_engine')
        self.ort, self.ledger = ort, ledger
        self.engine = engine

    def __getattr__(self, name):
        if name != 'Kokoro':
            raise AttributeError(name)
        self.ledger.append('kokoro-import')
        if self.ort.requests == 0:
            raise AssertionError('Kokoro imported before the diagnostic-control request')
        return SimpleNamespace(from_session=Mock(return_value=self.engine))


class RuntimeDiagnosticsTests(unittest.TestCase):
    @contextmanager
    def fixture(self, *, label='cpu-fixture', api='ok'):
        ledger = []
        ort = fake_runtime(label, ledger, api)
        engine = object()
        modules = {name: ModuleType(name) for name in ('numpy', 'soundfile', 'psutil')}
        modules['psutil'].cpu_count = lambda logical=True: 8 if logical else 4
        modules['onnxruntime'] = ort
        modules['backend.kokoro_engine'] = KokoroModule(ort, ledger, engine)
        original_import = builtins.__import__

        def traced_import(name, *args, **kwargs):
            if name == 'onnxruntime':
                ledger.append('import:' + sys.modules['onnxruntime'].__version__)
            if name in {'numpy', 'soundfile'}:
                ledger.append('dependency:' + name)
                if sys.modules['onnxruntime'].requests == 0:
                    raise AssertionError(name + ' imported before the diagnostic-control request')
            return original_import(name, *args, **kwargs)

        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, modules))
            stack.enter_context(patch('builtins.__import__', side_effect=traced_import))
            stack.enter_context(patch.object(performance, 'gpu_adapters', return_value=[]))
            stack.enter_context(patch.object(performance, 'GpuUsage', return_value=object()))
            stack.enter_context(patch.object(runtime, 'gpu_runtime_info', return_value=None))
            stack.enter_context(patch.object(pronunciation, 'pronunciation_identity', return_value={'fixture': True}))
            yield SimpleNamespace(ort=ort, ledger=ledger, engine=engine)
        self.assertEqual(native_guard.attempts, [])

    def run_worker_entry(self, runtime_directory=None):
        commands, events = queue.Queue(), queue.Queue()
        commands.put(None)
        self.assertIsNone(speech.speech_worker(commands, events, threading.Event(), runtime_directory))
        self.assertTrue(events.empty())

    def create_fixture_engine(self, provider='CPUExecutionProvider'):
        model = performance.GPU_FILE if provider == 'CUDAExecutionProvider' else performance.FILES[0]
        return performance.create_engine(Path(model), Path(performance.FILES[1]),
                                         {'provider': provider, 'device_id': 2, 'cuda_device': 1, 'threads': 2})

    def test_parent_requests_control_before_provider_enumeration(self):
        with self.fixture() as fixture:
            parent = performance.Performance(object(), object())
            self.assertEqual(parent.runtime, 'cpu-fixture')
            self.assertEqual(parent.providers, ['CPUExecutionProvider', 'CUDAExecutionProvider'])
            self.assertEqual(fixture.ort.requests, 1)
            self.assertLess(fixture.ledger.index('control:cpu-fixture'), fixture.ledger.index('providers'))
            fixture.ort.InferenceSession.assert_not_called()

    def test_engine_preserves_trust_cuda_options_and_provider_contract(self):
        for provider in ('CPUExecutionProvider', 'CUDAExecutionProvider'):
            with self.subTest(provider=provider), self.fixture() as fixture:
                with patch.object(model_trust, 'verify_file', side_effect=lambda path: fixture.ledger.append('verify:' + path.name)), \
                     patch.object(runtime, 'load_cuda_libraries', side_effect=lambda: fixture.ledger.append('cuda-load')) as cuda:
                    self.assertIs(self.create_fixture_engine(provider), fixture.engine)
                ledger = fixture.ledger
                self.assertLess(ledger.index('verify:' + performance.FILES[1]), ledger.index('control:cpu-fixture'))
                self.assertLess(ledger.index('control:cpu-fixture'), ledger.index('kokoro-import'))
                self.assertLess(ledger.index('kokoro-import'), ledger.index('options'))
                self.assertLess(ledger.index('options'), ledger.index('session'))
                self.assertEqual(fixture.ort.options[0].intra_op_num_threads, 2)
                self.assertEqual(fixture.ort.options[0].entries, {'session.intra_op.allow_spinning': '0'})
                self.assertFalse(fixture.ort.options[0].enable_profiling)
                selected = fixture.ort.sessions[0][2]
                fixture.ort.sessions[0][3].disable_fallback.assert_called_once_with()
                if provider == 'CUDAExecutionProvider':
                    cuda.assert_called_once_with()
                    self.assertLess(ledger.index('cuda-load'), ledger.index('control:cpu-fixture'))
                    self.assertEqual(selected, [('CUDAExecutionProvider', {'device_id': '1',
                                     'cudnn_conv_algo_search': 'HEURISTIC', 'do_copy_in_default_stream': '1'}),
                                               'CPUExecutionProvider'])
                else:
                    cuda.assert_not_called()
                    self.assertEqual(selected, ['CPUExecutionProvider'])

    def test_worker_activates_selected_gpu_before_control_and_dependencies(self):
        with self.fixture(label='gpu-fixture') as fixture:
            def activate(directory):
                self.assertEqual(directory, 'verified-fixture-directory')
                self.assertEqual(fixture.ort.requests, 0)
                self.assertEqual(fixture.ledger, [])
                fixture.ledger.append('activate')

            with patch.object(runtime, 'activate_gpu_runtime', side_effect=activate) as activation:
                self.run_worker_entry('verified-fixture-directory')
            activation.assert_called_once_with('verified-fixture-directory')
            self.assertLess(fixture.ledger.index('activate'), fixture.ledger.index('import:gpu-fixture'))
            self.assertLess(fixture.ledger.index('control:gpu-fixture'), fixture.ledger.index('dependency:numpy'))
            self.assertLess(fixture.ledger.index('control:gpu-fixture'), fixture.ledger.index('dependency:soundfile'))
            fixture.ort.InferenceSession.assert_not_called()

    def test_worker_without_addon_retains_selected_cpu_module(self):
        with self.fixture() as fixture, patch.object(runtime, 'activate_gpu_runtime') as activation:
            self.run_worker_entry()
            activation.assert_not_called()
            self.assertIs(sys.modules['onnxruntime'], fixture.ort)
            self.assertEqual(fixture.ort.requests, 1)
            self.assertEqual(fixture.ledger[0], 'import:cpu-fixture')

    def test_each_worker_entry_repeats_control_without_a_process_success_cache(self):
        # Synchronous entry seams, not actual spawned/replacement-process evidence.
        for label in ('cpu-fixture', 'gpu-fixture'):
            with self.subTest(module=label), self.fixture(label=label) as fixture:
                self.run_worker_entry()
                self.run_worker_entry()
                self.assertEqual(fixture.ort.requests, 2)
                self.assertIs(sys.modules['onnxruntime'], fixture.ort)

    def check_control_failure(self, api):
        for boundary in ('parent', 'engine', 'worker'):
            with self.subTest(api=api, boundary=boundary), self.fixture(api=api) as fixture, \
                 patch.object(model_trust, 'verify_file'):
                with self.assertRaises(RuntimeError) as caught:
                    if boundary == 'parent':
                        performance.Performance(object(), object())
                    elif boundary == 'engine':
                        self.create_fixture_engine()
                    else:
                        self.run_worker_entry()
                self.assertEqual(str(caught.exception), ERROR_MESSAGE)
                self.assertTrue(caught.exception.__suppress_context__)
                self.assertNotIn('SYNTHETIC_PRIVATE', str(caught.exception))
                self.assertIs(sys.modules['onnxruntime'], fixture.ort)
                self.assertEqual(fixture.ort.requests, 0)
                fixture.ort.get_available_providers.assert_not_called()
                fixture.ort.SessionOptions.assert_not_called()
                fixture.ort.InferenceSession.assert_not_called()
                self.assertFalse(any(item.startswith('dependency:') for item in fixture.ledger))
                self.assertNotIn('kokoro-import', fixture.ledger)

    def test_missing_or_noncallable_api_prevents_parent_engine_and_worker_initialization(self):
        for api in ('missing', 'noncallable'):
            self.check_control_failure(api)

    def test_raising_api_prevents_initialization_and_excludes_raw_failure_details(self):
        self.check_control_failure('raises')

    def test_real_model_and_gpu_trust_rejection_precedes_runtime_exposure(self):
        absent = Path(__file__).resolve().parents[1] / '.tmp/r05-control-a-20261023-8f4c2d91/absent-runtime'
        self.assertFalse(absent.exists())
        with self.fixture() as fixture:
            with self.assertRaisesRegex(ValueError, 'approved model'):
                performance.create_engine(Path('unapproved.onnx'), Path(performance.FILES[1]), {})
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                performance.create_engine(absent / performance.FILES[0], absent / performance.FILES[1], {})
            with self.assertRaisesRegex(ValueError, 'runtime is missing'):
                self.run_worker_entry(absent)
            self.assertEqual(fixture.ledger, [])
            self.assertEqual(fixture.ort.requests, 0)
            self.assertIs(sys.modules['onnxruntime'], fixture.ort)


if __name__ == '__main__':
    unittest.main()
