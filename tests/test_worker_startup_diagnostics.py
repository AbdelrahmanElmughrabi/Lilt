"""Synchronous worker/parent startup seams; no native runtime or child process."""
from contextlib import contextmanager
import copy
import importlib
import importlib.abc
import importlib.util
import inspect
import io
from pathlib import Path
import queue
import sqlite3
import sys
import tempfile
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from backend.jobs import Jobs
from backend import runtime_diagnostics, speech
from backend.storage import Store


MESSAGE = ("The voice runtime's diagnostic settings could not be applied. "
           "Restart Violilt; if this continues, repair the installation.")


class Channel:
    def __init__(self):
        self.closed = False
        self.cancelled_join = False

    def cancel_join_thread(self):
        self.cancelled_join = True

    def close(self):
        self.closed = True


class Process:
    def __init__(self, *, target=None, args=(), daemon=True):
        self.target, self.args = target, args
        self.alive, self.closed = False, False

    def start(self):
        self.alive = True

    def is_alive(self):
        return self.alive

    def join(self, timeout):
        pass

    def close(self):
        self.closed = True


class Context:
    Queue = Channel
    Event = staticmethod(threading.Event)
    Process = Process


class WorkerStartupDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'library')
        self.store.save_settings({'model_release': 'keep'})
        self.jobs = jobs = Jobs.__new__(Jobs)
        jobs.store = self.store
        jobs.lock = threading.RLock()
        jobs.context = Context()
        jobs.commands, jobs.events = Channel(), Channel()
        jobs.cancel, jobs.diagnostics_failed = threading.Event(), threading.Event()
        jobs.process = Process()
        jobs.active = jobs.operation = None
        jobs.idle_since = None
        jobs.releasing = jobs.closing = False
        jobs.release_error = jobs.persistence_error = ''
        jobs._pending_job = jobs._pending_benchmark = None
        jobs._persistence_retry_at = 0
        jobs._idle_storage_error = False
        jobs.performance = SimpleNamespace(warmup={'state': 'loading'},
            benchmark={'state': 'running', 'results': [{'label': 'kept partial fixture'}]})

    def reading(self):
        item = {'id': 'synthetic-reading', 'state': 'preparing', 'completed': 1,
                'total': 3, 'sections': [{'index': 0, 'start': 0, 'duration': 1, 'pause': 0}],
                'available_duration': 1, 'position': .5, 'message': 'Preparing.'}
        self.store.put('jobs', item)
        self.jobs.active = copy.deepcopy(item)
        return item

    def listen(self, action=None):
        """Exactly one controlled queue outcome followed by a closing timeout."""
        channel = self.jobs.events
        calls = 0

        def get(timeout):
            nonlocal calls
            calls += 1
            if calls > 1:
                self.jobs.closing = True
            elif action:
                return action()
            raise queue.Empty()

        channel.get = get
        factory = self.jobs.context.Queue
        def replacement_channel():
            created = factory()
            created.get = get
            return created
        with patch.object(self.jobs.context, 'Queue', side_effect=replacement_channel):
            self.jobs._listen()
        self.jobs.closing = False

    def controlled_worker(self, flag, *, api='raises', directory=None):
        self.assertIn('diagnostics_failed', inspect.signature(speech.speech_worker).parameters,
                      'Worker startup must accept the dedicated failure channel.')
        ort = ModuleType('onnxruntime')
        if api != 'missing':
            ort.disable_telemetry_events = None if api == 'noncallable' else Mock(
                side_effect=OSError('SYNTHETIC_PRIVATE_VENDOR at C:/SYNTHETIC_PRIVATE_PATH'))
        commands, events = Mock(), Mock()
        with patch.dict(sys.modules, {'onnxruntime': ort}), \
             patch('backend.runtime.activate_gpu_runtime') as activate:
            self.assertIsNone(speech.speech_worker(commands, events, threading.Event(), directory, flag))
        activate.assert_called_once_with(directory) if directory else activate.assert_not_called()
        commands.get.assert_not_called()
        events.put.assert_not_called()

    def test_worker_control_failure_signals_before_commands_or_dependencies(self):
        original_import = __import__
        dependencies = []

        def guarded_import(name, *args, **kwargs):
            if name in {'numpy', 'soundfile', 'backend.kokoro_engine'}:
                dependencies.append(name)
                raise AssertionError('Numeric/audio/inference dependency reached after failure.')
            return original_import(name, *args, **kwargs)

        for api in ('missing', 'noncallable', 'raises'):
            for directory in (None, 'verified-synthetic-gpu'):
                with self.subTest(api=api, directory=directory):
                    flag = threading.Event()
                    with patch('builtins.__import__', side_effect=guarded_import):
                        self.controlled_worker(flag, api=api, directory=directory)
                    self.assertTrue(flag.is_set())
                    self.assertEqual(dependencies, [])

    def test_worker_trust_and_import_failures_keep_existing_failure_route(self):
        self.assertIn('diagnostics_failed', inspect.signature(speech.speech_worker).parameters)
        flag, commands, events = threading.Event(), Mock(), Mock()
        for error, directory in ((ValueError('synthetic trust rejection'), 'synthetic-addon'),
                                 (ImportError('synthetic runtime import failure'), None)):
            with self.subTest(error=type(error).__name__), \
                 patch('backend.runtime.activate_gpu_runtime', side_effect=error) as activation, \
                 patch.object(runtime_diagnostics, 'load_onnx_runtime', side_effect=error) as load:
                with self.assertRaises(type(error)) as caught:
                    speech.speech_worker(commands, events, threading.Event(), directory, flag)
                self.assertIs(caught.exception, error)
                if directory:
                    load.assert_not_called()
                else:
                    activation.assert_not_called()
                self.assertFalse(flag.is_set())
                commands.get.assert_not_called()
                events.put.assert_not_called()

    def test_reading_failure_keeps_saved_sections_and_fixed_guidance(self):
        item = self.reading()
        self.jobs.diagnostics_failed.set()
        self.listen()
        saved = self.store.get('jobs', item['id'])
        self.assertEqual((saved['state'], saved['message']), ('failed', MESSAGE))
        for field in ('completed', 'sections', 'available_duration', 'position'):
            self.assertEqual(saved[field], item[field])
        self.assertIsNone(self.jobs.active)
        self.assertEqual(self.jobs.persistence_error, '')

    def test_warmup_and_benchmark_failure_guidance_survives_idle_release(self):
        self.store.save_settings({'model_release': 'immediate'})
        for operation in ('warmup', 'benchmark'):
            with self.subTest(operation=operation):
                self.jobs.operation = operation
                self.jobs.process = Process()
                self.jobs.diagnostics_failed.set()
                partial = copy.deepcopy(self.jobs.performance.benchmark['results'])
                self.listen()
                state = getattr(self.jobs.performance, operation)
                self.assertEqual((state['state'], state['message']), ('failed', MESSAGE))
                self.assertEqual(self.jobs.performance.benchmark['results'], partial)
                self.assertIsNone(self.jobs.operation)
                self.assertIsNone(self.jobs.process)
                self.assertFalse(self.jobs.diagnostics_failed.is_set())
                self.assertIsNone(self.jobs._pending_benchmark)

    def test_timeout_then_worker_exit_uses_signal_before_generic_diagnosis(self):
        for operation in ('generate', 'warmup', 'benchmark'):
            with self.subTest(operation=operation):
                if operation == 'generate':
                    item = self.reading()
                else:
                    self.jobs.operation = operation
                self.jobs.process.alive = True
                self.jobs.diagnostics_failed.clear()

                def worker_exits_during_timeout():
                    self.controlled_worker(self.jobs.diagnostics_failed)
                    self.jobs.process.alive = False
                    raise queue.Empty()

                self.listen(worker_exits_during_timeout)
                state = (self.store.get('jobs', item['id']) if operation == 'generate'
                         else getattr(self.jobs.performance, operation))
                self.assertEqual((state['state'], state['message']), ('failed', MESSAGE))

    def test_unexpected_worker_death_keeps_generic_recovery(self):
        item = self.reading()
        self.jobs.operation = 'warmup'
        self.listen()
        self.assertEqual(self.store.get('jobs', item['id'])['message'],
                         'The speech process stopped. Your completed sections are saved.')
        self.assertEqual(self.jobs.performance.warmup,
                         {'state': 'failed', 'message': 'The speech process stopped. You can try again.'})
        self.assertIsNone(self.jobs.active)
        self.assertIsNone(self.jobs.operation)

    def test_replacement_resets_signal_and_passes_current_channels(self):
        old_process = self.jobs.process
        old_channels = (self.jobs.commands, self.jobs.events)
        old_flag = self.jobs.diagnostics_failed
        old_flag.set()
        with patch('backend.jobs.gpu_runtime_directory', return_value='verified-synthetic-gpu'):
            self.jobs._worker()
        self.assertTrue(old_process.closed)
        self.assertTrue(all(channel.closed and channel.cancelled_join for channel in old_channels))
        self.assertIsNot(self.jobs.diagnostics_failed, old_flag)
        self.assertFalse(self.jobs.diagnostics_failed.is_set())
        self.assertIs(self.jobs.process.target, speech.speech_worker)
        self.assertEqual(self.jobs.process.args,
            (self.jobs.commands, self.jobs.events, self.jobs.cancel,
             'verified-synthetic-gpu', self.jobs.diagnostics_failed))
        self.jobs.operation = 'benchmark'
        self.jobs.process.alive = False
        self.listen()
        self.assertEqual(self.jobs.performance.benchmark['message'],
                         'The speech process stopped. You can try again.')

    def test_retired_queue_and_signal_cannot_fail_new_operation(self):
        old_flag = self.jobs.diagnostics_failed
        self.jobs.operation = 'warmup'

        def replace_during_old_read():
            self.jobs._reset_channels()
            self.jobs.process = Process()
            self.jobs.process.alive = True
            old_flag.set()
            # End on the next current-queue read after verifying its state.
            def current_read(timeout):
                self.assertEqual(self.jobs.operation, 'warmup')
                self.assertEqual(self.jobs.performance.warmup, {'state': 'loading'})
                self.jobs.closing = True
                raise queue.Empty()
            self.jobs.events.get = current_read
            return {'kind': 'warmup', 'state': 'failed', 'message': 'retired fixture event'}

        self.listen(replace_during_old_read)
        self.assertIsNot(self.jobs.diagnostics_failed, old_flag)
        self.assertFalse(self.jobs.diagnostics_failed.is_set())
        self.assertEqual(self.jobs.performance.warmup, {'state': 'loading'})

    def test_failed_progress_write_retains_guidance_for_retry(self):
        item = self.reading()
        self.jobs.diagnostics_failed.set()
        with patch.object(self.store, 'put', side_effect=sqlite3.OperationalError('synthetic full')):
            self.listen()
        self.assertIsNone(self.jobs.active)
        self.assertEqual(self.jobs._pending_job['message'], MESSAGE)
        self.assertEqual(self.jobs._pending_job['state'], 'failed')
        self.assertTrue(self.jobs.persistence_error)
        self.assertEqual(self.store.get('jobs', item['id'])['state'], 'preparing')
        self.jobs._flush_persistence(force=True)
        self.assertEqual(self.store.get('jobs', item['id'])['message'], MESSAGE)
        self.assertEqual(self.jobs.persistence_error, '')

    def test_shutdown_keeps_interrupted_state(self):
        item = self.reading()
        self.jobs.diagnostics_failed.set()
        self.jobs.close()
        self.jobs._listen()
        saved = self.store.get('jobs', item['id'])
        self.assertEqual(saved['state'], 'interrupted')
        self.assertEqual(saved['message'], 'Continue this reading when you return.')
        self.assertEqual(saved['sections'], item['sections'])

    @contextmanager
    def diagnostic_test_copy(self):
        name = '_r05_setup_cleanup_fixture'
        source = Path(__file__).with_name('test_runtime_diagnostics.py')
        spec = importlib.util.spec_from_file_location(name, source)
        module = importlib.util.module_from_spec(spec)
        before = list(sys.meta_path)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
            module.BLOCKED_ROOTS = {'_r05_unrelated_fixture_import'}
            yield module, before
        finally:
            # A failing negative baseline must not contaminate subsequent cases.
            sys.meta_path[:] = before
            sys.modules.pop(name, None)
            sys.modules.pop('_r05_unrelated_fixture_import', None)

    def nested_case(self, module, method):
        probe = type('FixtureProbe', (unittest.TestCase,),
                     {'__module__': module.__name__, 'test_probe': method})
        return unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([probe('test_probe')]))

    def test_failed_module_setup_restores_import_guard(self):
        with self.diagnostic_test_copy() as (module, before):
            def fail_import(name):
                self.assertIn(module.native_guard, sys.meta_path)
                raise RuntimeError('SYNTHETIC_ORIGINAL_SETUP_FAILURE')

            with patch.object(module.importlib, 'import_module', side_effect=fail_import):
                result = self.nested_case(module, lambda case: self.fail('Body reached after setup failure.'))
            self.assertEqual(result.testsRun, 0)
            self.assertEqual(len(result.errors), 1)
            self.assertIn('SYNTHETIC_ORIGINAL_SETUP_FAILURE', result.errors[0][1])
            self.assertEqual(sys.meta_path, before)

            class InertFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname == '_r05_unrelated_fixture_import':
                        return importlib.util.spec_from_loader(fullname, self)
                def create_module(self, spec):
                    return None
                def exec_module(self, imported):
                    imported.synthetic = True

            finder = InertFinder()
            sys.meta_path.append(finder)
            self.assertTrue(importlib.import_module('_r05_unrelated_fixture_import').synthetic)
            sys.meta_path.remove(finder)
            self.assertEqual(sys.meta_path, before)

    def test_failed_module_teardown_keeps_assertion_and_cleanup(self):
        with self.diagnostic_test_copy() as (module, before):
            def blocked_attempt(case):
                module.native_guard.attempts.append('synthetic_blocked_attempt')
            with patch.object(module.importlib, 'import_module', return_value=SimpleNamespace()):
                result = self.nested_case(module, blocked_attempt)
            self.assertEqual(result.testsRun, 1)
            self.assertEqual(len(result.errors), 1)
            self.assertIn('Blocked real imports: synthetic_blocked_attempt', result.errors[0][1])
            self.assertEqual(sys.meta_path, before)
            module.remove_native_guard()
            module.remove_native_guard()
            self.assertEqual(sys.meta_path, before)

    @contextmanager
    def replacement_reading(self, policy='keep'):
        """Fresh operation state and fake IPC; execute actual admission methods."""
        self.store.save_settings({'model_release': policy})
        self.jobs.active = self.jobs.operation = self.jobs.process = None
        self.jobs.closing = False
        self.jobs.cache_root = self.store.root / 'section-cache'
        self.jobs.commands, self.jobs.events = Channel(), Channel()
        self.jobs.commands.put = Mock()
        self.jobs.cancel, self.jobs.diagnostics_failed = threading.Event(), threading.Event()
        self.jobs.models = SimpleNamespace(root=self.store.root / 'models',
            status=lambda: {'state': 'ready', 'voices': ['af_heart']})
        config = {'model': 'synthetic-model.onnx', 'provider': 'CPUExecutionProvider',
                  'device_id': -1, 'threads': 1, 'label': 'Synthetic CPU'}
        self.jobs.performance.resolve = Mock(return_value=config)
        self.jobs.performance.candidates = Mock(return_value=[config])
        self.jobs._audio_identity = Mock(return_value=['synthetic-audio-identity'])
        self.jobs.performance.warmup = {}
        self.jobs.performance.benchmark = {'state': 'idle', 'results': []}
        document = {'id': 'synthetic-source', 'title': 'Synthetic source',
                    'markdown': 'A synthetic replacement reading.'}
        prepared = {'chunks': [{'text': document['markdown'], 'pause': 0}],
                    'words': 5, 'options': {}, 'unread_symbols': []}
        factory = self.jobs.context.Queue

        def channel():
            created = factory()
            created.put = Mock()
            return created

        with patch.object(self.jobs.context, 'Queue', side_effect=channel), \
             patch('backend.jobs.gpu_runtime_directory', return_value=None), \
             patch('backend.jobs.pronunciation_identity', return_value={'fixture': True}):
            yield SimpleNamespace(document=document, prepared=prepared)

    def complete_replacement(self, key):
        self.listen(lambda: {'id': key, 'state': 'completed', 'completed': 1,
                             'duration': .1, 'message': 'Synthetic reading completed.'})
        self.assertEqual(self.store.get('jobs', key)['state'], 'completed')
        self.assertIsNone(self.jobs.active)

    def test_failed_warmup_replacement_settles_reason_and_reading_completes(self):
        for diagnostic_failure in (True, False):
            with self.subTest(diagnostic_failure=diagnostic_failure), self.replacement_reading() as fixture:
                self.assertTrue(self.jobs.warmup())
                old_process, old_flag = self.jobs.process, self.jobs.diagnostics_failed
                old_commands, old_events = self.jobs.commands, self.jobs.events
                if diagnostic_failure:
                    old_flag.set()
                old_process.alive = False
                reading = self.jobs.start(fixture.prepared, fixture.document, 'af_heart', 1)
                expected = MESSAGE if diagnostic_failure else 'The speech process stopped. You can try again.'
                self.assertEqual(self.jobs.performance.warmup, {'state': 'failed', 'message': expected})
                self.assertIsNone(self.jobs.operation)
                self.assertTrue(old_process.closed and old_commands.closed and old_events.closed)
                self.assertIsNot(self.jobs.diagnostics_failed, old_flag)
                self.assertFalse(self.jobs.diagnostics_failed.is_set())
                self.assertTrue(self.jobs.process.is_alive())
                command = self.jobs.commands.put.call_args.args[0]
                self.assertEqual((command['kind'], command['job']['id']), ('generate', reading['id']))
                self.assertEqual(self.jobs.active['state'], 'preparing')
                self.complete_replacement(reading['id'])
                self.assertIsNone(self.jobs.operation)
                self.assertEqual(self.jobs.performance.warmup['message'], expected)

    def test_warmup_replacement_restores_preparation_benchmark_and_release_controls(self):
        for action in ('warmup', 'benchmark', 'manual_release', 'automatic_release'):
            policy = 'immediate' if action == 'automatic_release' else 'keep'
            with self.subTest(action=action), self.replacement_reading(policy) as fixture:
                self.assertTrue(self.jobs.warmup())
                self.jobs.diagnostics_failed.set()
                self.jobs.process.alive = False
                reading = self.jobs.start(fixture.prepared, fixture.document, 'af_heart', 1)
                process = self.jobs.process
                with patch.object(process, 'join', side_effect=lambda timeout: setattr(process, 'alive', False)):
                    self.complete_replacement(reading['id'])
                    self.assertIsNone(self.jobs.operation, 'Retired warmup must not own the replacement reading.')
                    if action in {'warmup', 'benchmark'}:
                        self.assertTrue(getattr(self.jobs, action)())
                        self.assertEqual(self.jobs.operation, action)
                        self.assertEqual(self.jobs.commands.put.call_args.args[0]['kind'], action)
                    else:
                        if action == 'manual_release':
                            self.assertTrue(self.jobs.release_engine())
                        self.assertIsNone(self.jobs.process)
                        self.assertEqual(self.jobs.performance.warmup, {'state': 'failed', 'message': MESSAGE})

    def test_retirement_settlement_does_not_capture_live_or_fresh_operations(self):
        for mode in ('live_warmup', 'fresh_warmup', 'fresh_benchmark'):
            with self.subTest(mode=mode), self.replacement_reading() as fixture:
                self.assertTrue(self.jobs.warmup())
                if mode == 'live_warmup':
                    process = self.jobs.process
                    reading = self.jobs.start(fixture.prepared, fixture.document, 'af_heart', 1)
                    self.assertIs(self.jobs.process, process)
                    self.assertEqual(self.jobs.operation, 'warmup')
                    self.assertEqual(self.jobs.performance.warmup['state'], 'loading')
                    self.listen(lambda: {'kind': 'warmup', 'state': 'ready', 'message': 'Synthetic preparation ready.'})
                    self.assertIsNone(self.jobs.operation)
                    self.complete_replacement(reading['id'])
                else:
                    # An already observed old failure must not fail a newly
                    # assigned preparation/speed test during channel rotation.
                    self.jobs.operation = None
                    self.jobs.performance.warmup = {'state': 'failed', 'message': MESSAGE}
                    self.jobs.diagnostics_failed.set()
                    self.jobs.process.alive = False
                    action = mode.removeprefix('fresh_')
                    self.assertTrue(getattr(self.jobs, action)())
                    self.assertEqual(self.jobs.operation, action)
                    expected_state = 'loading' if action == 'warmup' else 'running'
                    self.assertEqual(getattr(self.jobs.performance, action)['state'], expected_state)
                    self.assertFalse(self.jobs.diagnostics_failed.is_set())


if __name__ == '__main__':
    unittest.main()
