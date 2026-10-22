"""Verify the optional CUDA add-on before exposing its code or native libraries."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import sys
from pathlib import Path

from .gpu_trust import APPROVED, RUNTIME_VERSION

MARKER = {'provider': 'CUDAExecutionProvider', 'runtime': RUNTIME_VERSION}
_ACTIVE_RUNTIME = None
_DLL_DIRECTORIES = []
_DLL_HANDLES = []
_CUDA_DLLS = (
    'nvidia/cublas/bin/cublasLt64_12.dll', 'nvidia/cublas/bin/cublas64_12.dll',
    'nvidia/cufft/bin/cufft64_11.dll', 'nvidia/cuda_runtime/bin/cudart64_12.dll',
    'nvidia/cudnn/bin/cudnn_engines_runtime_compiled64_9.dll',
    'nvidia/cudnn/bin/cudnn_engines_precompiled64_9.dll',
    'nvidia/cudnn/bin/cudnn_heuristic64_9.dll', 'nvidia/cudnn/bin/cudnn_ops64_9.dll',
    'nvidia/cudnn/bin/cudnn_adv64_9.dll', 'nvidia/cudnn/bin/cudnn_graph64_9.dll',
    'nvidia/cudnn/bin/cudnn64_9.dll',
)


def plain_path(path):
    """Reject reparse points before resolving them, including ancestor junctions."""
    path = Path(path).absolute()
    for entry in (path, *path.parents):
        if entry.is_symlink() or (hasattr(entry, 'is_junction') and entry.is_junction()):
            raise ValueError('Reparse points are not allowed in the GPU runtime.')
        if entry.exists() and getattr(entry.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Reparse points are not allowed in the GPU runtime.')
    return path.resolve()


def verify_runtime_file(root, name):
    root = plain_path(root)
    path = plain_path(root / name)
    size, expected = APPROVED[name]
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size != size:
        raise ValueError(f'Missing or unapproved GPU runtime file: {name}')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise ValueError(f'GPU runtime integrity check failed: {name}')
    return path


def read_runtime_marker(root):
    marker = plain_path(Path(root) / 'violilt-runtime.json')
    if marker.stat().st_size > 4096:
        raise ValueError('The GPU runtime marker is too large.')
    value = json.loads(marker.read_text(encoding='utf-8'))
    if (not isinstance(value, dict) or any(value.get(key) != expected for key, expected in MARKER.items())
            or set(value) - (set(MARKER) | {'tested_model'})
            or ('tested_model' in value and value['tested_model'] != 'kokoro-v1.0.fp16-gpu.onnx')):
        raise ValueError('The GPU runtime marker is invalid or unsupported.')
    return value


def verify_gpu_runtime(root):
    root = plain_path(root)
    if not root.is_dir():
        raise ValueError('The approved GPU runtime is missing.')
    allowed = set(APPROVED) | {'violilt-runtime.json'}
    directories = {parent.as_posix() for name in allowed for parent in Path(name).parents}
    found = set()
    for directory, children, files in os.walk(root, followlinks=False):
        for name in children + files:
            path = Path(directory) / name
            plain_path(path)
            relative = path.relative_to(root).as_posix()
            if path.is_dir():
                if relative not in directories:
                    raise ValueError(f'Unexpected GPU runtime directory: {relative}')
            elif path.is_file():
                found.add(relative)
    if found != allowed:
        raise ValueError('The GPU runtime contains missing or unapproved files.')
    read_runtime_marker(root)
    for name in APPROVED:
        verify_runtime_file(root, name)
    return root


def gpu_runtime_directory():
    # A shipped application cannot be redirected by the caller's environment.
    if getattr(sys, 'frozen', False):
        root = Path(sys.executable).parent / 'gpu-runtime'
    else:
        explicit = os.environ.get('VIOLILT_GPU_RUNTIME')
        root = Path(explicit) if explicit else Path(__file__).resolve().parents[1] / '.tmp/pronunciation-gpu-runtime'
    try:
        return verify_gpu_runtime(root)
    except (ValueError, OSError, UnicodeError, RuntimeError):
        return None  # An invalid optional runtime must leave the CPU path usable.


def gpu_runtime_info():
    directory = gpu_runtime_directory()
    try:
        return read_runtime_marker(directory) if directory else None
    except (ValueError, OSError, UnicodeError):
        return None


def activate_gpu_runtime(directory):
    """Worker-side verification; never trust a directory passed by the parent."""
    global _ACTIVE_RUNTIME
    if getattr(sys, 'frozen', False) and plain_path(directory) != plain_path(Path(sys.executable).parent / 'gpu-runtime'):
        raise ValueError('A packaged voice process can use only its bundled GPU runtime.')
    root = verify_gpu_runtime(directory)
    loaded = sys.modules.get('onnxruntime')
    if loaded is not None and Path(loaded.__file__).resolve() != root / 'onnxruntime/__init__.py':
        raise ValueError('Another ONNX runtime is already loaded. Restart the voice process.')
    if _ACTIVE_RUNTIME is not None and _ACTIVE_RUNTIME != root:
        raise ValueError('The GPU runtime cannot change inside a voice process.')
    bins = sorted({(root / name).parent for name in APPROVED if name.endswith('.dll')})
    handles = []
    try:
        for folder in bins:
            handles.append(os.add_dll_directory(str(folder)))
        # Apply the same restricted search to DLLs loaded later by vendor code.
        # This changes only this voice/helper process, never the user's OS policy.
        kernel = ctypes.WinDLL('kernel32.dll', winmode=0x800)
        restrict_search = kernel.SetDefaultDllDirectories
        restrict_search.argtypes = [ctypes.c_uint32]
        restrict_search.restype = ctypes.c_bool
        if not restrict_search(0xC00):  # Registered directories and System32 only.
            raise OSError('Could not restrict DLL dependency search.')
    except (AttributeError, OSError):
        for handle in handles:
            handle.close()
        raise ValueError('The approved GPU runtime requires Windows DLL-directory support.') from None
    _DLL_DIRECTORIES.extend(handles)  # Keep registrations alive for deferred cuDNN loads.
    sys.dont_write_bytecode = True  # Bytecode is deliberately excluded from the approved payload.
    sys.path.insert(0, str(root))
    _ACTIVE_RUNTIME = root
    return root


def load_cuda_libraries():
    if _ACTIVE_RUNTIME is None:
        raise ValueError('A verified NVIDIA runtime is required. Choose CPU or repair the GPU runtime.')
    # Activation already verified every file before exposing this folder. A
    # second full hash here duplicates that work without making it immutable.
    root = _ACTIVE_RUNTIME
    if _DLL_HANDLES:
        return
    # Use absolute paths and exclude PATH/current-directory DLL fallback. Only
    # registered runtime directories, the DLL's own directory and System32 apply.
    handles = [ctypes.WinDLL(str(root / name), winmode=0xD00) for name in _CUDA_DLLS]
    _DLL_HANDLES.extend(handles)
