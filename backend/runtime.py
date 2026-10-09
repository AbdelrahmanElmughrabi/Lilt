"""Optional local CUDA add-on; the small base application remains CPU-capable."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def gpu_runtime_directory():
    explicit = os.environ.get('LILT_GPU_RUNTIME') or os.environ.get('FOLIO_GPU_RUNTIME')
    root = Path(explicit) if explicit else (Path(sys.executable).parent / 'gpu-runtime' if getattr(sys, 'frozen', False)
                                           else Path(__file__).resolve().parents[1] / '.cuda-probe')
    if any((root / name).is_file() for name in ('lilt-runtime.json', 'folio-runtime.json')) and (root / 'onnxruntime' / '__init__.py').is_file():
        return root.resolve()
    return None


def gpu_runtime_info():
    directory = gpu_runtime_directory()
    if not directory:
        return None
    try:
        marker = directory / 'lilt-runtime.json'
        if not marker.is_file():
            marker = directory / 'folio-runtime.json'
        return json.loads(marker.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return None
