"""Local logging/export boundaries using synthetic files and fake native UI."""
from contextlib import contextmanager
import importlib
import io
import json
import logging
import os
from pathlib import Path
import stat
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import uuid
import wave

from backend.bridge import Bridge
from backend.storage import Store

EXPORT_ERROR = 'The recording could not be exported. Choose an available, writable folder and try again.'
PRIVATE = 'R05_PRIVATE_PATH_TITLE_TEXT_CANARY'


class LocalLoggingTests(unittest.TestCase):
    def setUp(self):
        owned = os.environ.get('VIOLILT_LOG_TEST_ROOT')
        if owned:
            self.root = Path(owned) / self._testMethodName
            self.root.mkdir(parents=True, exist_ok=False)
        else:
            temporary = tempfile.TemporaryDirectory(prefix='violilt-logging-test-')
            self.addCleanup(temporary.cleanup)
            self.root = Path(temporary.name)
        self.stderr = io.StringIO()
        self.stderr_patch = patch('sys.stderr', self.stderr)
        self.stderr_patch.start()
        self.loggers = []
        for logger in (logging.getLogger(), logging.getLogger('pywebview')):
            self.loggers.append((logger, logger.handlers[:], logger.level, logger.propagate))

    def tearDown(self):
        for logger, handlers, level, propagate in self.loggers:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                if handler not in handlers:
                    handler.close()
            for handler in handlers:
                logger.addHandler(handler)
            logger.setLevel(level)
            logger.propagate = propagate
        self.stderr_patch.stop()

    def configure(self, **kwargs):
        module = importlib.import_module('backend.local_logging')
        return module, module.configure_local_logging(self.root, **kwargs)

    def records(self):
        return [json.loads(line) for name in ('violilt-events.log', 'violilt-events.log.1', 'violilt-events.log.2')
                for path in (self.root / name,)
                if path.is_file() for line in path.read_text(encoding='utf-8').splitlines()]

    def test_fixed_events_keep_operation_but_exclude_paths_arguments_and_tracebacks(self):
        module, _ = self.configure()
        try:
            raise OSError(28, PRIVATE, str(self.root / PRIVATE))
        except OSError:
            logging.exception('Recording progress or speed-test settings could not be saved')
        logging.getLogger(PRIVATE).error('Error %s', PRIVATE, extra={'document': PRIVATE})
        record = self.records()[0]
        self.assertEqual(record['event'], 'recording_persistence_failed')
        self.assertEqual(record['errno'], 28)
        text = ''.join(path.read_text(encoding='utf-8') for path in self.root.glob(module.LOG_NAME + '*'))
        self.assertNotIn(PRIVATE, text)
        self.assertNotIn(str(self.root), text)
        self.assertNotIn('Traceback', text)
        self.assertEqual(len(self.records()), 2)

    def test_unknown_oversized_messages_are_bounded_without_formatting_objects(self):
        module, _ = self.configure()

        class Message:
            def __str__(self):
                raise AssertionError('Free-form message object was rendered')

        logging.error(Message())
        logging.error(PRIVATE * 100_000)
        lines = (self.root / module.LOG_NAME).read_bytes().splitlines(keepends=True)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(len(line) <= module.MAX_RECORD_BYTES for line in lines))
        self.assertTrue(all(json.loads(line)['event'] == 'unclassified_event' for line in lines))
        self.assertNotIn(PRIVATE.encode(), b''.join(lines))

    def test_error_storm_rolls_over_only_the_three_owned_files(self):
        module, _ = self.configure(max_bytes=1024)
        unrelated = self.root / 'violilt-events.log.keep'
        unrelated.write_bytes(b'Keep unrelated copy')
        for _ in range(100):
            logging.error(PRIVATE)
        owned = [self.root / name for name in module.LOG_NAMES]
        self.assertTrue(all(path.exists() for path in owned))
        self.assertTrue(all(path.stat().st_size <= 1024 for path in owned))
        self.assertEqual(unrelated.read_bytes(), b'Keep unrelated copy')
        self.assertNotIn(PRIVATE.encode(), b''.join(path.read_bytes() for path in owned))
        self.assertTrue(self.records())

    def test_production_boundary_rolls_before_a_record_exceeds_one_mib(self):
        module, _ = self.configure()
        self.assertEqual(module.MAX_LOG_BYTES, 1024 * 1024)
        active = self.root / module.LOG_NAME
        active.write_bytes(b'x' * module.MAX_LOG_BYTES)
        logging.error('Startup voice preparation failed')
        self.assertLessEqual(active.stat().st_size, module.MAX_LOG_BYTES)
        self.assertEqual((self.root / (module.LOG_NAME + '.1')).stat().st_size, module.MAX_LOG_BYTES)

    def test_startup_expiry_keeps_recent_future_legacy_and_unknown_files(self):
        module = importlib.import_module('backend.local_logging')
        now = time.time()
        for name in module.LOG_NAMES:
            (self.root / name).write_bytes(b'Synthetic older managed log')
        os.utime(self.root / module.LOG_NAMES[0], (now - 15 * 86400,) * 2)
        os.utime(self.root / module.LOG_NAMES[1], (now - 13 * 86400,) * 2)
        os.utime(self.root / module.LOG_NAMES[2], (now + 86400,) * 2)
        legacy = self.root / 'violilt.log'
        legacy.write_bytes(PRIVATE.encode())
        os.utime(legacy, (now - 100 * 86400,) * 2)
        unknown = self.root / 'violilt-events.log.old'
        unknown.write_bytes(b'Keep unknown')
        self.configure(now=now)
        self.assertFalse((self.root / module.LOG_NAME).exists())
        self.assertTrue((self.root / module.LOG_NAMES[1]).exists())
        self.assertTrue((self.root / module.LOG_NAMES[2]).exists())
        self.assertEqual(legacy.read_bytes(), PRIVATE.encode())
        self.assertEqual(unknown.read_bytes(), b'Keep unknown')

    def test_directory_and_simulated_multiply_linked_candidates_are_preserved_and_reported(self):
        module = importlib.import_module('backend.local_logging')
        active = self.root / module.LOG_NAME
        active.mkdir()
        _, handler = self.configure()
        logging.error(PRIVATE)
        self.assertTrue(active.is_dir())
        self.assertTrue(handler.last_error)
        active.rmdir()
        external = self.root / 'synthetic-protected.txt'
        external.write_bytes(PRIVATE.encode())
        active.write_bytes(external.read_bytes())
        original = Path.lstat

        def multiply_linked(path):
            value = original(path)
            if path == active:
                return SimpleNamespace(st_mode=value.st_mode, st_nlink=2, st_size=value.st_size,
                                       st_mtime=value.st_mtime, st_file_attributes=0)
            return value

        with patch.object(Path, 'lstat', multiply_linked):
            logging.error(PRIVATE)
        self.assertEqual(external.read_bytes(), PRIVATE.encode())
        self.assertEqual(active.read_bytes(), PRIVATE.encode())
        self.assertTrue(handler.last_error)

    def test_simulated_windows_reparse_metadata_stops_before_file_changes(self):
        module = importlib.import_module('backend.local_logging')
        active = self.root / module.LOG_NAME
        active.write_bytes(b'Preserve synthetic reparse target')
        original = Path.lstat

        def reparse(path):
            value = original(path)
            if path == active:
                return SimpleNamespace(st_mode=value.st_mode, st_nlink=1, st_size=value.st_size,
                                       st_mtime=value.st_mtime, st_file_attributes=0x400)
            return value

        with patch.object(Path, 'lstat', reparse):
            _, handler = self.configure()
            logging.error(PRIVATE)
        self.assertTrue(handler.last_error)
        self.assertEqual(active.read_bytes(), b'Preserve synthetic reparse target')
        self.assertNotIn(PRIVATE, self.stderr.getvalue())

    def test_denied_expiry_reports_failure_and_retains_the_file(self):
        module = importlib.import_module('backend.local_logging')
        old = self.root / module.LOG_NAME
        old.write_bytes(b'Preserve denied old managed file')
        os.utime(old, (time.time() - 15 * 86400,) * 2)
        with patch.object(Path, 'unlink', side_effect=PermissionError(PRIVATE)):
            _, handler = self.configure()
        self.assertTrue(handler.last_error)
        self.assertEqual(old.read_bytes(), b'Preserve denied old managed file')
        self.assertNotIn(PRIVATE, self.stderr.getvalue())

    def test_denied_write_is_nonfatal_warns_once_and_later_recovers(self):
        module, handler = self.configure()
        original = Path.open

        def denied(path, *args, **kwargs):
            if path.name == module.LOG_NAME:
                raise PermissionError(PRIVATE)
            return original(path, *args, **kwargs)

        with patch.object(Path, 'open', denied):
            logging.error(PRIVATE)
            logging.error(PRIVATE)
        self.assertTrue(handler.last_error)
        self.assertEqual(self.stderr.getvalue().count('Local diagnostic logging is unavailable'), 1)
        logging.error('Startup voice preparation failed')
        self.assertIsNone(handler.last_error)
        self.assertEqual(self.records()[0]['event'], 'startup_voice_preparation_failed')
        self.assertNotIn(PRIVATE, self.stderr.getvalue())

    def test_denied_rotation_does_not_append_past_the_cap(self):
        module, handler = self.configure(max_bytes=1024)
        active = self.root / module.LOG_NAME
        active.write_bytes(b'x' * 1024)
        with patch.object(Path, 'replace', side_effect=PermissionError(PRIVATE)):
            logging.error(PRIVATE)
        self.assertEqual(active.stat().st_size, 1024)
        self.assertTrue(handler.last_error)
        self.assertNotIn(PRIVATE, self.stderr.getvalue())

    def test_configuration_replaces_raw_handlers_and_pywebview_reuses_safe_console(self):
        raw = io.StringIO()
        logging.getLogger().addHandler(logging.StreamHandler(raw))
        logging.getLogger('pywebview').addHandler(logging.StreamHandler(raw))
        module, first = self.configure()
        _, second = self.configure()
        self.assertNotIn(first, logging.getLogger().handlers)
        self.assertEqual(logging.getLogger().handlers, [second])
        self.assertEqual(len(logging.getLogger('pywebview').handlers), 1)
        logging.getLogger('pywebview').error(PRIVATE)
        self.assertEqual(raw.getvalue(), '')
        self.assertNotIn(PRIVATE, self.stderr.getvalue())
        self.assertEqual(self.records()[0]['component'], 'webview')

    def recording(self, target):
        store = Store(self.root / 'library')
        key = uuid.uuid4().hex
        source = store.root / 'jobs' / key / 'recording.wav'
        source.parent.mkdir()
        with wave.open(str(source), 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(24000)
            audio.writeframes(b'\x01\x00' * 24)
        store.put('jobs', {'id': key, 'state': 'completed', 'title': 'Synthetic recording'})
        bridge = Bridge(store, None, None)
        bridge._window = SimpleNamespace(create_file_dialog=lambda *a, **k: (str(target),),
                                         create_confirmation_dialog=lambda *a: True)
        return bridge, key, source

    @contextmanager
    def fake_webview(self):
        with patch.dict(sys.modules, {'webview': SimpleNamespace(FileDialog=SimpleNamespace(SAVE='save'))}):
            yield

    def test_missing_export_destination_excludes_the_private_path(self):
        target = self.root / PRIVATE / 'export.wav'
        bridge, key, source = self.recording(target)
        original = source.read_bytes()
        with self.fake_webview(), self.assertRaises(FileNotFoundError) as caught:
            bridge.export_recording(key)
        self.assertNotIn(PRIVATE, str(caught.exception))
        self.assertEqual(str(caught.exception), EXPORT_ERROR)
        self.assertTrue(caught.exception.__suppress_context__)
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse(target.exists())

    def test_permission_export_error_preserves_type_and_existing_bytes(self):
        target = self.root / 'export.wav'
        target.write_bytes(b'Existing complete export')
        bridge, key, source = self.recording(target)
        original = source.read_bytes()
        with self.fake_webview(), patch('backend.bridge.tempfile.mkstemp', side_effect=PermissionError(PRIVATE)), \
             self.assertRaises(PermissionError) as caught:
            bridge.export_recording(key)
        self.assertEqual(str(caught.exception), EXPORT_ERROR)
        self.assertTrue(caught.exception.__suppress_context__)
        self.assertEqual(target.read_bytes(), b'Existing complete export')
        self.assertEqual(source.read_bytes(), original)

    def test_success_and_declined_replace_keep_the_staged_export_contract(self):
        target = self.root / 'export.wav'
        bridge, key, source = self.recording(target)
        with self.fake_webview():
            self.assertEqual(bridge.export_recording(key), str(target))
            self.assertEqual(target.read_bytes(), source.read_bytes())
            target.write_bytes(b'Keep declined export')
            bridge._window.create_confirmation_dialog = lambda *a: False
            self.assertIsNone(bridge.export_recording(key))
        self.assertEqual(target.read_bytes(), b'Keep declined export')
        self.assertEqual(list(self.root.glob('.violilt-export-*')), [])

    def test_blocking_and_interrupted_export_keep_type_guidance_and_original_bytes(self):
        module, _ = self.configure()
        target = self.root / (PRIVATE + '.wav')
        target.write_bytes(b'Previous complete export')
        bridge, key, source = self.recording(target)
        original = source.read_bytes()

        for error_type, code in ((BlockingIOError, 11), (InterruptedError, 4)):
            with self.subTest(error_type=error_type.__name__):
                def partial(_source, destination):
                    Path(destination).write_bytes(b'partial')
                    raise error_type(code, PRIVATE, str(target))

                with self.fake_webview(), patch('backend.bridge.copy_pcm', side_effect=partial), \
                     self.assertRaises(OSError) as caught:
                    bridge.export_recording(key)
                self.assertIs(type(caught.exception), error_type)
                self.assertEqual(str(caught.exception), EXPORT_ERROR)
                self.assertTrue(caught.exception.__suppress_context__)
                self.assertNotIn(PRIVATE, str(caught.exception))
                self.assertEqual(target.read_bytes(), b'Previous complete export')
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(list(self.root.glob('.violilt-export-*')), [])
                self.assertNotIn(PRIVATE, (self.root / module.LOG_NAME).read_text(encoding='utf-8'))
                self.assertNotIn(PRIVATE, self.stderr.getvalue())

    def test_partial_copy_and_final_replace_failures_preserve_original_files(self):
        target = self.root / 'export.wav'
        target.write_bytes(b'Previous complete export')
        bridge, key, source = self.recording(target)
        original = source.read_bytes()

        def partial(_source, destination):
            Path(destination).write_bytes(b'partial')
            raise OSError(28, PRIVATE)

        for name, failure in [('backend.bridge.copy_pcm', partial), ('pathlib.Path.replace', PermissionError(PRIVATE))]:
            with self.subTest(operation=name), self.fake_webview(), patch(name, side_effect=failure), \
                 self.assertRaises(OSError) as caught:
                bridge.export_recording(key)
            self.assertEqual(str(caught.exception), EXPORT_ERROR)
            self.assertEqual(target.read_bytes(), b'Previous complete export')
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(list(self.root.glob('.violilt-export-*')), [])

    def test_real_dispatcher_returns_useful_export_error_without_destination_canary(self):
        module, _ = self.configure()
        from webview.util import js_bridge_call
        target = self.root / PRIVATE / 'export.wav'
        bridge, key, source = self.recording(target)
        callbacks = []
        delivered = threading.Event()

        def receive(code):
            callbacks.append(code)
            delivered.set()

        window = SimpleNamespace(_functions={'export_recording': bridge.export_recording}, _js_api=None,
                                 evaluate_js=receive)
        js_bridge_call(window, 'export_recording', [key], 'r05logging')
        self.assertTrue(delivered.wait(5))
        callback = callbacks[0]
        (self.root / 'callback.js').write_text(callback, encoding='utf-8')
        self.assertIn('isError: true', callback)
        self.assertIn('FileNotFoundError', callback)
        self.assertIn(EXPORT_ERROR, callback)
        self.assertNotIn(PRIVATE, callback)
        self.assertNotIn(PRIVATE, self.stderr.getvalue())
        self.assertNotIn(PRIVATE, (self.root / module.LOG_NAME).read_text(encoding='utf-8'))
        self.assertEqual(self.records()[0]['event'], 'recording_export_failed')
        self.assertTrue(source.exists())
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
