"""Bounded local event logs; never serialize free-form errors or user content."""
from __future__ import annotations

import errno
import json
import logging
import math
from pathlib import Path
import stat
import sys
import time

LOG_NAME = 'violilt-events.log'
LOG_NAMES = (LOG_NAME, LOG_NAME + '.1', LOG_NAME + '.2')
MAX_LOG_BYTES = 1024 * 1024
MAX_RECORD_BYTES = 4096
RETENTION_SECONDS = 14 * 86400
LOG_FAILURE = 'Local diagnostic logging is unavailable. Readings and recordings can still be used.'

_EVENTS = {
    'Startup voice preparation failed': 'startup_voice_preparation_failed',
    'Could not read the idle memory policy; retaining the worker': 'idle_memory_policy_failed',
    'Reusable audio could not be accessed; keeping the library available': 'cache_access_failed',
    'Recording progress or speed-test settings could not be saved': 'recording_persistence_failed',
    'Could not save recovery bookkeeping; original rows are retained': 'recovery_bookkeeping_failed',
    'Could not remove an incomplete export temporary file': 'export_temporary_cleanup_failed',
    'Recording export failed': 'recording_export_failed',
    'Could not remove an incomplete cached audio copy': 'cache_temporary_cleanup_failed',
    'Could not remove an incomplete reusable audio copy': 'cache_temporary_cleanup_failed',
    'Reusable audio cache is unavailable; generating without cache': 'worker_cache_unavailable',
    'Reusable audio could not be read; generating without cache': 'worker_cache_read_failed',
    'Reusable audio could not be stored; continuing without cache': 'worker_cache_write_failed',
    'Could not request a safe window close': 'close_request_failed',
    'Could not dispatch a safe window close': 'close_dispatch_failed',
    'Could not finish a safe window close': 'close_finish_failed',
    'Could not dispatch window close completion': 'close_completion_failed',
}


def _notice():
    try:
        if sys.stderr is not None:
            sys.stderr.write(LOG_FAILURE + '\n')
            sys.stderr.flush()
    except Exception:
        # A console may not exist in the packaged app. Never echo the raw record.
        pass


class EventFormatter(logging.Formatter):
    def format(self, record):
        timestamp = 'unknown'
        if type(record.created) in (int, float) and math.isfinite(record.created):
            try:
                timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(record.created))
            except (OSError, OverflowError, ValueError):
                pass
        component = 'webview' if record.name == 'pywebview' else 'app' if record.name == 'root' else 'dependency'
        event = _EVENTS.get(record.msg, 'unclassified_event') if type(record.msg) is str else 'unclassified_event'
        severity = {10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ERROR', 50: 'CRITICAL'}.get(record.levelno, 'OTHER')
        body = {'time': timestamp, 'level': severity, 'component': component, 'event': event}
        error = record.exc_info[1] if isinstance(record.exc_info, tuple) and len(record.exc_info) == 3 else None
        if isinstance(error, OSError):
            for name in ('errno', 'winerror'):
                value = getattr(error, name, None)
                if type(value) is int and 0 <= value <= 0xFFFFFFFF:
                    body[name] = value
        rendered = json.dumps(body, ensure_ascii=True, separators=(',', ':'))
        if len(rendered.encode('utf-8')) + 1 > MAX_RECORD_BYTES:
            return '{"time":"unknown","level":"ERROR","component":"app","event":"log_record_unavailable"}'
        return rendered


def _ordinary(info, *, directory=False):
    valid_kind = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    return (valid_kind and not getattr(info, 'st_file_attributes', 0) & 0x400
            and (directory or info.st_nlink == 1))


class BoundedLocalHandler(logging.Handler):
    def __init__(self, root, *, max_bytes=MAX_LOG_BYTES, now=None):
        super().__init__(logging.INFO)
        if type(max_bytes) is not int or not 512 <= max_bytes <= MAX_LOG_BYTES:
            raise ValueError('Invalid local event-log bound.')
        self.root = Path(root).absolute()
        self.max_bytes = max_bytes
        self.last_error = None
        self._warned = False
        self.setFormatter(EventFormatter())
        try:
            self._expire(time.time() if now is None else now)
        except OSError:
            self._failed()

    def _failed(self):
        self.last_error = LOG_FAILURE
        if not self._warned:
            self._warned = True
            _notice()

    def _files(self):
        if '..' in self.root.parts:
            raise OSError(errno.EINVAL, 'Invalid log directory.')
        for directory in (self.root, *self.root.parents):
            if not _ordinary(directory.lstat(), directory=True):
                raise OSError(errno.EINVAL, 'Unsafe log directory.')
        found = {}
        for name in LOG_NAMES:
            path = self.root / name
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if not _ordinary(info):
                raise OSError(errno.EINVAL, 'Unsafe log file.')
            found[name] = info
        return found

    def _bounded(self, files):
        if any(info.st_size > self.max_bytes for info in files.values()):
            raise OSError(errno.EFBIG, 'Existing event log exceeds the bound.')

    def _expire(self, now):
        for name, info in self._files().items():
            if info.st_mtime < now - RETENTION_SECONDS:
                (self.root / name).unlink()
        self._bounded(self._files())

    def _rotate(self):
        files = self._files()
        if LOG_NAMES[2] in files:
            (self.root / LOG_NAMES[2]).unlink()
        if LOG_NAMES[1] in files:
            (self.root / LOG_NAMES[1]).replace(self.root / LOG_NAMES[2])
        if LOG_NAME in files:
            (self.root / LOG_NAME).replace(self.root / LOG_NAMES[1])

    def emit(self, record):
        try:
            payload = (self.format(record) + '\n').encode('utf-8')
            files = self._files()
            self._bounded(files)
            if len(payload) > min(MAX_RECORD_BYTES, self.max_bytes):
                raise OSError(errno.EFBIG, 'Event record exceeds the bound.')
            if LOG_NAME in files and files[LOG_NAME].st_size + len(payload) > self.max_bytes:
                self._rotate()
            files = self._files()
            if LOG_NAME in files and files[LOG_NAME].st_size + len(payload) > self.max_bytes:
                raise OSError(errno.EFBIG, 'Event log changed during rotation.')
            with (self.root / LOG_NAME).open('ab') as stream:
                stream.write(payload)
            self.last_error = None
            self._warned = False
        except OSError:
            self._failed()


class _EventConsoleHandler(logging.StreamHandler):
    def handleError(self, record):
        _notice()


def configure_local_logging(root, *, max_bytes=MAX_LOG_BYTES, now=None):
    """Configure this standalone process; legacy violilt.log is left untouched."""
    handler = BoundedLocalHandler(root, max_bytes=max_bytes, now=now)
    application = logging.getLogger()
    webview = logging.getLogger('pywebview')
    for logger in (application, webview):
        for previous in logger.handlers[:]:
            logger.removeHandler(previous)
            previous.close()
        logger.setLevel(logging.INFO)
    application.addHandler(handler)
    console = _EventConsoleHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(EventFormatter())
    webview.addHandler(console)
    webview.propagate = True
    return handler
