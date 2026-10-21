"""Approved Kokoro release bytes, independently fetched on 21 October 2026.

Source: thewh1teagle/kokoro-onnx release model-files-v1.0. The upstream
API omits asset digests. Pins are part of the reviewed application code and
must change deliberately with a new model release; remote metadata cannot
silently approve different bytes. Integrity does not establish license rights.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

RELEASE = 'https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.0'
DOWNLOAD_ROOT = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
APPROVED = {
    'kokoro-v1.0.int8.onnx': (92361271, '6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb'),
    'kokoro-v1.0.fp16-gpu.onnx': (177464787, 'c1610a859f3bdea01107e73e50100685af38fff88f5cd8e5c56df109ec880204'),
    'voices-v1.0.bin': (28214398, 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'),
}


def verify_file(path, name=None):
    path = Path(path)
    name = name or path.name
    if name not in APPROVED:
        raise ValueError('This model release is not approved by Violilt.')
    size, expected = APPROVED[name]
    if not path.is_file() or path.stat().st_size != size:
        raise ValueError(f'{name} is incomplete or is not the approved release. Import the approved model files again.')
    digest = hashlib.sha256()
    read = 0
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            read += len(block)
            if read > size:
                raise ValueError(f'{name} changed during its integrity check.')
            digest.update(block)
    if digest.hexdigest() != expected:
        raise ValueError(f'{name} failed its integrity check. Import the approved model files again.')
    return expected
