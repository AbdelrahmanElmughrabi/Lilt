"""Local, optional Windows GPU-engine readings for the speech worker only."""
from __future__ import annotations

import ctypes
import math
import os
import threading
import time

SAMPLE_SECONDS = 1.0
MAX_AGE_SECONDS = 3.0
IDLE_SECONDS = 5.0
RETRY_SECONDS = 5.0
MAX_RETRY_SECONDS = 30.0
MORE_DATA = 0x800007D2
NO_DATA = 0x800007D5
NOT_READY = {NO_DATA, 0x800007D1, 0xC0000BBA}  # No instance / no valid rate sample yet.
FORMAT_DOUBLE = 0x200


class _Number(ctypes.Union):
    _fields_ = [('double', ctypes.c_double), ('large', ctypes.c_int64)]


class _Value(ctypes.Structure):
    _fields_ = [('status', ctypes.c_uint32), ('number', _Number)]


class _Item(ctypes.Structure):
    _fields_ = [('name', ctypes.c_wchar_p), ('value', _Value)]


def busiest_engine(pid, readings):
    """Task Manager-style busiest engine; never add independent percentages."""
    values = [value for name, status, value in readings
              if name and name.startswith(f'pid_{pid}_') and status in (0, 1)
              and math.isfinite(value) and 0 <= value <= 100]
    return round(max(values), 1) if values else None


class _GpuQuery:
    def __init__(self, pid):
        if os.name != 'nt':
            raise OSError('Windows GPU counters are unavailable.')
        # System32-only loading avoids searching the project or current PATH.
        self.library = ctypes.WinDLL('pdh.dll', winmode=0x800)
        signatures = {
            'PdhOpenQueryW': [ctypes.c_wchar_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)],
            'PdhAddEnglishCounterW': [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)],
            'PdhCollectQueryData': [ctypes.c_void_p],
            'PdhGetFormattedCounterArrayW': [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32),
                                            ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p],
            'PdhCloseQuery': [ctypes.c_void_p],
        }
        for name, arguments in signatures.items():
            function = getattr(self.library, name)
            function.argtypes, function.restype = arguments, ctypes.c_uint32
        self.query, self.counter = ctypes.c_void_p(), ctypes.c_void_p()
        try:
            self._check(self.library.PdhOpenQueryW(None, 0, ctypes.byref(self.query)))
            self._check(self.library.PdhAddEnglishCounterW(
                self.query, rf'\GPU Engine(pid_{pid}_*)\Utilization Percentage', 0, ctypes.byref(self.counter)))
            # A rate needs a baseline and a later sample. No context may exist
            # yet while the model loads; keep the query for subsequent samples.
            self._check(self.library.PdhCollectQueryData(self.query), allow_no_data=True)
        except (OSError, ValueError):
            self.close()
            raise

    @staticmethod
    def _check(status, allow_no_data=False):
        if status != 0 and not (allow_no_data and status in NOT_READY):
            raise OSError(f'Windows GPU counter unavailable (0x{status:08x}).')

    def read(self):
        status = self.library.PdhCollectQueryData(self.query)
        if status in NOT_READY:
            return []
        self._check(status)
        # The wildcard list can change between sizing and reading. Start the
        # sizing call again, with a bounded allocation and number of retries.
        for _ in range(3):
            size, count = ctypes.c_uint32(), ctypes.c_uint32()
            status = self.library.PdhGetFormattedCounterArrayW(
                self.counter, FORMAT_DOUBLE, ctypes.byref(size), ctypes.byref(count), None)
            if status in NOT_READY or (status == 0 and not count.value):
                return []
            if status != MORE_DATA:
                self._check(status)
            if not 0 < size.value <= 16 * 1024 * 1024:
                raise OSError('Windows GPU counter buffer is unavailable.')
            buffer = ctypes.create_string_buffer(size.value)
            status = self.library.PdhGetFormattedCounterArrayW(
                self.counter, FORMAT_DOUBLE, ctypes.byref(size), ctypes.byref(count), buffer)
            if status == MORE_DATA:
                continue
            if status in NOT_READY:
                return []
            self._check(status)
            if count.value * ctypes.sizeof(_Item) > len(buffer):
                raise OSError('Windows GPU counter buffer is invalid.')
            items = ctypes.cast(buffer, ctypes.POINTER(_Item))
            return [(items[index].name, items[index].value.status, items[index].value.number.double)
                    for index in range(count.value)]
        raise OSError('Windows GPU counters changed during sampling.')

    def close(self):
        if self.query:
            self.library.PdhCloseQuery(self.query)
            self.query = ctypes.c_void_p()


class GpuUsage:
    """Sample off the bridge thread; publish fresh readings without blocking it."""
    def __init__(self):
        self._lock = threading.Lock()
        self._pid, self._percent, self._updated = None, None, None
        self._requested = 0.0
        self._stop = threading.Event()

    def read(self, pid):
        pid = pid if type(pid) is int and pid > 0 else None
        with self._lock:
            self._requested = time.monotonic()
            if pid != self._pid:
                self._stop.set()
                self._pid, self._percent, self._updated = pid, None, None
                self._stop = threading.Event()
                if pid is not None:
                    threading.Thread(target=self._poll, args=(pid, self._stop), daemon=True,
                                     name='violilt-gpu-usage').start()
            return self._percent if self._updated is not None and self._requested - self._updated <= MAX_AGE_SECONDS else None

    def _poll(self, pid, stop):
        query = None
        retry_at, retry_delay = 0.0, RETRY_SECONDS
        try:
            while not stop.is_set():
                with self._lock:
                    if self._stop is not stop:
                        break
                    if time.monotonic() - self._requested > IDLE_SECONDS:
                        self._pid, self._percent, self._updated = None, None, None
                        break
                try:
                    if query is None:
                        if time.monotonic() >= retry_at:
                            # Opening takes the rate baseline; read on a later tick.
                            query = _GpuQuery(pid)
                    else:
                        percent = busiest_engine(pid, query.read())
                        retry_delay = RETRY_SECONDS
                        with self._lock:
                            # An old query must not overwrite a restarted worker's data.
                            if self._stop is stop:
                                self._percent, self._updated = percent, time.monotonic()
                except (OSError, ValueError):
                    if query is not None:
                        query.close()
                        query = None
                    retry_at = time.monotonic() + retry_delay
                    retry_delay = min(retry_delay * 2, MAX_RETRY_SECONDS)
                    with self._lock:
                        if self._stop is stop:
                            self._percent, self._updated = None, None
                # Keep cancellation and idle cleanup responsive during backoff.
                if stop.wait(SAMPLE_SECONDS):
                    break
        finally:
            if query is not None:
                query.close()
