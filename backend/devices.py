"""Small Windows DXGI adapter inventory; no driver changes or shell commands."""
from __future__ import annotations

import ctypes
import os
import uuid


def gpu_adapters():
    if os.name != 'nt':
        return []
    from ctypes import wintypes

    class LUID(ctypes.Structure):
        _fields_ = [('low', wintypes.DWORD), ('high', wintypes.LONG)]

    class Description(ctypes.Structure):
        _fields_ = [('name', wintypes.WCHAR * 128), ('vendor', wintypes.UINT),
                    ('device', wintypes.UINT), ('subsystem', wintypes.UINT), ('revision', wintypes.UINT),
                    ('video_memory', ctypes.c_size_t), ('system_memory', ctypes.c_size_t),
                    ('shared_memory', ctypes.c_size_t), ('luid', LUID), ('flags', wintypes.UINT)]

    def call(pointer, index, result, *types):
        vtable = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        return ctypes.WINFUNCTYPE(result, ctypes.c_void_p, *types)(vtable[index])

    factory = ctypes.c_void_p()
    adapters = []
    try:
        identifier = (ctypes.c_byte * 16).from_buffer_copy(uuid.UUID('770aae78-f26f-4dba-a829-253c83d1b387').bytes_le)
        library = ctypes.WinDLL('dxgi')
        library.CreateDXGIFactory1.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        library.CreateDXGIFactory1.restype = ctypes.c_long
        if library.CreateDXGIFactory1(ctypes.byref(identifier), ctypes.byref(factory)) < 0:
            return []
        index = 0
        while True:
            adapter = ctypes.c_void_p()
            result = call(factory, 12, ctypes.c_long, wintypes.UINT, ctypes.POINTER(ctypes.c_void_p))(factory, index, ctypes.byref(adapter))
            if result < 0:
                break
            try:
                description = Description()
                if call(adapter, 10, ctypes.c_long, ctypes.POINTER(Description))(adapter, ctypes.byref(description)) >= 0 and not description.flags & 2:
                    adapters.append({'id': index, 'name': description.name, 'memory_mb': description.video_memory // 1048576})
            finally:
                call(adapter, 2, wintypes.ULONG)(adapter)
            index += 1
    except (OSError, ValueError):
        return []
    finally:
        if factory:
            call(factory, 2, wintypes.ULONG)(factory)
    return adapters
