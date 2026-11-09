"""Fail before packaging if the selected release interpreter/native inputs drift."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import ssl
import struct
import sys
import xml.parsers.expat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / 'packaging/release-runtime.json'


def observed_runtime():
    return {'python': platform.python_version(), 'implementation': platform.python_implementation(),
            'platform': sys.platform, 'bits': struct.calcsize('P') * 8,
            'abi': sys.implementation.cache_tag, 'openssl': ssl.OPENSSL_VERSION,
            'expat': xml.parsers.expat.EXPAT_VERSION}


def verify(policy, base, observed):
    for key, expected in policy['expected'].items():
        if observed.get(key) != expected:
            raise ValueError(f'Release runtime {key} mismatch: expected {expected!r}, found {observed.get(key)!r}.')
    base = Path(base).resolve()
    for name, expected in policy['native_files'].items():
        path = (base / name).resolve()
        if not path.is_relative_to(base):
            raise ValueError('Runtime pin leaves its base directory.')
        digest = hashlib.sha256()
        with path.open('rb') as source:
            while block := source.read(1024 * 1024):
                digest.update(block)
        if digest.hexdigest() != expected:
            raise ValueError(f'Release runtime bytes do not match the selected artifact: {name}')
    return observed | {'native_files_verified': len(policy['native_files']),
                       'expat_disposition': policy['expat_disposition']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, default=POLICY)
    args = parser.parse_args()
    result = verify(json.loads(args.policy.read_text()), Path(sys.base_prefix), observed_runtime())
    print(json.dumps(result))


if __name__ == '__main__':
    main()
