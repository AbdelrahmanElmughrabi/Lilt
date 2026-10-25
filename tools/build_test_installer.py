"""Wrap a previously audited app folder in an unsigned per-user test installer.

This does not rebuild the app or establish production redistribution clearance.
Use setup_inno_tools.ps1 first to obtain the pinned, signature-checked compiler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', required=True, type=Path)
    parser.add_argument('--audit-sha256', required=True)
    parser.add_argument('--compiler', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--version', default='1.0.4.0')
    parser.add_argument('--source-commit', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+\.\d+', args.version):
        raise ValueError('Use a four-part numeric package version.')
    if not re.fullmatch(r'[0-9a-f]{40}', args.source_commit):
        raise ValueError('Pin the app payload source commit.')
    root = Path(__file__).resolve().parents[1]
    payload = args.payload.resolve(strict=True)
    output = args.output.resolve()
    if output == payload or output.is_relative_to(payload) or payload.is_relative_to(output):
        raise ValueError('Output and payload must be separate directories.')
    audit_path = payload / 'package-audit.json'
    if digest(audit_path) != args.audit_sha256.lower():
        raise ValueError('Payload audit does not match the explicit pin.')
    audit = json.loads(audit_path.read_text(encoding='utf-8-sig'))
    if audit['status'] != 'pass' or audit['violations']:
        raise ValueError('The existing payload audit must pass.')
    expected = {}
    for item in audit['files']:
        path = PurePosixPath(item['path'])
        if path.is_absolute() or '..' in path.parts or '\\' in item['path'] or ':' in item['path']:
            raise ValueError('Unsafe audit path: ' + item['path'])
        if str(path).casefold() in {name.casefold() for name in expected}:
            raise ValueError('Duplicate audit path: ' + str(path))
        expected[str(path)] = item
    expected['package-audit.json'] = {
        'path': 'package-audit.json', 'bytes': audit_path.stat().st_size,
        'sha256': args.audit_sha256.lower(),
    }
    actual = {}
    for path in payload.rglob('*'):
        # Do not follow symlinks/junctions into unrelated files.
        if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Linked payload item: ' + str(path))
        if path.is_file():
            actual[path.relative_to(payload).as_posix()] = path
    if set(actual) != set(expected):
        raise ValueError('Payload file set differs from the audited input.')
    for name, path in actual.items():
        item = expected[name]
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('Payload changed: ' + name)
    marker = json.loads((payload / 'violilt-candidate.json').read_text(encoding='utf-8-sig'))
    if marker['data_profile'] != 'Violilt-Pronunciation-Evaluation':
        raise ValueError('Expected the existing isolated evaluation data profile.')
    print(json.dumps({'payload_verified': len(actual), 'bytes': sum(x['bytes'] for x in expected.values())}), flush=True)
    output.mkdir(parents=True, exist_ok=False)
    recipe = root / 'packaging/test-installer/Violilt-Test.iss'
    manifest = {
        'schema': 1, 'status': 'compiling', 'private_test_only': True,
        'store_ready': False, 'signed': False, 'version': args.version,
        'payload_source_commit': args.source_commit,
        'payload_audit_sha256': args.audit_sha256.lower(),
        'data_profile': marker['data_profile'],
        'compiler_sha256': digest(args.compiler), 'recipe_sha256': digest(recipe),
        'files': sorted(expected.values(), key=lambda item: item['path']),
    }
    manifest_path = output / 'installer-inventory.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    with (output / 'compiler.log').open('w', encoding='utf-8') as log:
        result = subprocess.run([
            str(args.compiler.resolve(strict=True)), '/Qp',
            '/DPayloadDir=' + str(payload), '/DPackageVersion=' + args.version,
            '/O' + str(output), str(recipe),
        ], stdout=log, stderr=subprocess.STDOUT, check=False)
    manifest['compiler_exit_code'] = result.returncode
    if result.returncode:
        manifest['status'] = 'compile-failed'
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        raise RuntimeError('Installer compile failed; inspect compiler.log.')
    installer = output / f'Violilt-Test-{args.version}-x64-Setup.exe'
    manifest.update(status='built-install-test-pending', installer=installer.name,
                    installer_bytes=installer.stat().st_size, installer_sha256=digest(installer))
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (output / 'SHA256SUMS.txt').write_text(manifest['installer_sha256'] + '  ' + installer.name + '\n', encoding='ascii')
    print(json.dumps({key: manifest[key] for key in ('status', 'installer', 'installer_bytes', 'installer_sha256')}), flush=True)


if __name__ == '__main__':
    main()
