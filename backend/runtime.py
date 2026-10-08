"""Optional local CUDA add-on; the small base application remains CPU-capable."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def gpu_runtime_directory():
    explicit = os.environ.get('FOLIO_GPU_RUNTIME')
    root = Path(explicit) if explicit else (Path(sys.executable).parent / 'gpu-runtime' if getattr(sys, 'frozen', False)
                                           else Path(__file__).resolve().parents[1] / '.cuda-probe')
    if (root / 'folio-runtime.json').is_file() and (root / 'onnxruntime' / '__init__.py').is_file():
        return root.resolve()
    return None


def gpu_runtime_info():
    directory = gpu_runtime_directory()
    if not directory:
        return None
    try:
        return json.loads((directory / 'folio-runtime.json').read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return None
