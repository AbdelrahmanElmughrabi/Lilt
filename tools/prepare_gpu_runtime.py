"""Copy only approved GPU runtime files into a new, verified runtime folder."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))

from backend import runtime


def prepare_runtime(source, destination):
    source, destination = runtime.plain_path(source), runtime.plain_path(destination)
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError('Source and prepared runtime folders must be separate.')
    if (source / 'violilt-runtime.json').exists():
        runtime.read_runtime_marker(source)
    destination.mkdir(parents=True, exist_ok=False)
    for name, (size, expected) in runtime.APPROVED.items():
        original = runtime.plain_path(source / name)
        if not original.is_relative_to(source) or not original.is_file() or original.stat().st_size != size:
            raise ValueError(f'Missing or unapproved GPU runtime file: {name}')
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        digest, copied = hashlib.sha256(), 0
        with original.open('rb') as reader, target.open('xb') as writer:
            for block in iter(lambda: reader.read(1024 * 1024), b''):
                copied += len(block)
                if copied > size:
                    raise ValueError(f'GPU runtime file changed while preparing it: {name}')
                digest.update(block)
                writer.write(block)
        if copied != size or digest.hexdigest() != expected:
            raise ValueError(f'GPU runtime integrity check failed: {name}')
    (destination / 'violilt-runtime.json').write_text(json.dumps(runtime.MARKER), encoding='utf-8')
    runtime.verify_gpu_runtime(destination)
    return {'directory': str(destination), 'files': len(runtime.APPROVED),
            'runtime': runtime.RUNTIME_VERSION, 'bytes': sum(pin[0] for pin in runtime.APPROVED.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / '.cuda-probe')
    parser.add_argument('--output', type=Path, default=ROOT / '.tmp/pronunciation-gpu-runtime')
    parser.add_argument('--verify', type=Path, help='Check an existing prepared runtime without changing it')
    args = parser.parse_args()
    if args.verify:
        print(json.dumps({'verified': str(runtime.verify_gpu_runtime(args.verify))}))
    else:
        print(json.dumps(prepare_runtime(args.source, args.output)))


if __name__ == '__main__':
    main()
