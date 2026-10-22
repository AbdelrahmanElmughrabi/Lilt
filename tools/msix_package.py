"""Prepare a mapping-based MSIX compatibility package without copying its GPU payload.

This deliberately supports a local test identity only. Store identity and legal
release clearance are separate gates; this tool cannot produce a production build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))

from PyInstaller.archive.readers import ArchiveReadError

from backend.model_trust import APPROVED, verify_file
from tools.package_pronunciation_audit import audit

FOUNDATION = 'http://schemas.microsoft.com/appx/manifest/foundation/windows10'
UAP = 'http://schemas.microsoft.com/appx/manifest/uap/windows10'
UAP10 = 'http://schemas.microsoft.com/appx/manifest/uap/windows10/10'
RESCAP = 'http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities'
PROFILE = 'Violilt-MSIX-Compatibility'
TEST_PUBLISHER = 'CN=Violilt Local MSIX Compatibility, OID.2.25.311729368913984317654407730594956997722=1'
DIRECTORIES = {'_internal', 'models', 'gpu-runtime', 'third-party'}
ROOT_FILES = {'Violilt.exe', 'violilt-candidate.json', 'violilt-build.json', 'package-audit.json'}
REQUIRED = (
    'Violilt.exe', 'violilt-candidate.json', 'package-audit.json',
    'models/kokoro-v1.0.int8.onnx', 'models/kokoro-v1.0.fp16-gpu.onnx', 'models/voices-v1.0.bin',
    'gpu-runtime/violilt-runtime.json', 'gpu-runtime/onnxruntime/__init__.py',
    'gpu-runtime/onnxruntime/capi/onnxruntime_providers_cuda.dll', 'third-party/manifest.json',
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def package_version(value: str) -> str:
    if not re.fullmatch(r'\d+\.\d+\.\d+\.0', value):
        raise ValueError('Use a four-part Store version with a zero fourth component.')
    numbers = [int(part) for part in value.split('.')]
    if not 1 <= numbers[0] <= 65535 or any(part > 65535 for part in numbers):
        raise ValueError('Package version components are outside the Store range.')
    canonical = '.'.join(map(str, numbers))
    if canonical != value:
        raise ValueError('Use a canonical version without leading zeros so artifact and manifest versions match.')
    return canonical


def require_x64(path: Path):
    with path.open('rb') as stream:
        if stream.read(2) != b'MZ':
            raise ValueError('The payload executable is not a Windows PE file.')
        stream.seek(0x3c)
        pointer = stream.read(4)
        if len(pointer) != 4:
            raise ValueError('Invalid executable header.')
        stream.seek(struct.unpack('<I', pointer)[0])
        if stream.read(6) != b'PE\0\0\x64\x86':
            raise ValueError('This compatibility package requires an x64 executable.')


def payload_files(payload: Path):
    for path in sorted(payload.rglob('*')):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError(f'Reparse points are not allowed in package input: {path.name}')
        if not path.resolve().is_relative_to(payload):
            raise ValueError('Package input escapes the payload directory.')
        relative = path.relative_to(payload)
        if relative.parts[0] not in DIRECTORIES | ROOT_FILES:
            raise ValueError(f'Unexpected top-level payload entry: {relative.parts[0]}')
        if not path.is_file() or '__pycache__' in relative.parts:
            continue
        if path.name in {'violilt-candidate.json', 'package-audit.json'} and len(relative.parts) == 1:
            continue  # Map the isolated marker and fresh audit from staging.
        if (path.suffix.lower() in {'.sqlite', '.sqlite3', '.db', '.wav', '.mp3', '.log', '.pfx'}
                or path.name == '.env' or path.name.startswith('.env.')
                or any(character in str(path) for character in ('"', '\n', '\r'))):
            raise ValueError(f'Private/generated content is not allowed in package input: {relative}')
        yield path, 'App/' + relative.as_posix()


def manifest(config: dict, version: str, windows_version: str) -> bytes:
    ET.register_namespace('', FOUNDATION)
    ET.register_namespace('uap', UAP)
    ET.register_namespace('uap10', UAP10)
    ET.register_namespace('rescap', RESCAP)
    def add(parent, name, attributes=None, text=None, namespace=FOUNDATION):
        element = ET.SubElement(parent, f'{{{namespace}}}{name}', attributes or {})
        element.text = text
        return element
    package = ET.Element(f'{{{FOUNDATION}}}Package', {'IgnorableNamespaces': 'uap uap10 rescap'})
    add(package, 'Identity', {'Name': config['identity_name'], 'Publisher': config['publisher'],
                             'Version': version, 'ProcessorArchitecture': 'x64'})
    properties = add(package, 'Properties')
    for name, value in [('DisplayName', config['display_name']),
                        ('PublisherDisplayName', config['publisher_display_name']),
                        ('Description', config['description']), ('Logo', 'Assets/StoreLogo.png')]:
        add(properties, name, text=value)
    add(add(package, 'Resources'), 'Resource', {'Language': 'en-US'})
    add(add(package, 'Dependencies'), 'TargetDeviceFamily', {
        'Name': 'Windows.Desktop', 'MinVersion': config['min_version'], 'MaxVersionTested': windows_version})
    application = add(add(package, 'Applications'), 'Application', {
        'Id': 'Violilt', 'Executable': 'App\\Violilt.exe',
        f'{{{UAP10}}}RuntimeBehavior': 'packagedClassicApp', f'{{{UAP10}}}TrustLevel': 'mediumIL'})
    add(application, 'VisualElements', {
        'DisplayName': config['display_name'], 'Description': config['description'],
        'Square150x150Logo': 'Assets/Square150x150Logo.png',
        'Square44x44Logo': 'Assets/Square44x44Logo.png', 'BackgroundColor': 'transparent'}, namespace=UAP)
    add(add(package, 'Capabilities'), 'Capability', {'Name': 'runFullTrust'}, namespace=RESCAP)
    ET.indent(package)
    return ET.tostring(package, encoding='utf-8', xml_declaration=True)


def prepare(payload: Path, stage: Path, version: str, config_path: Path) -> dict:
    payload, stage = payload.resolve(), stage.resolve()
    version = package_version(version)
    if stage.is_relative_to(payload) or payload.is_relative_to(stage):
        raise ValueError('Staging and payload directories must be separate.')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if (config.get('compatibility_only') is not True or config.get('data_profile') != PROFILE
            or config.get('identity_name') != 'Violilt.MsixCompatibilityProbe'
            or config.get('publisher') != TEST_PUBLISHER):
        raise ValueError('Only the explicit local compatibility identity is supported.')
    for name in REQUIRED:
        path = payload / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(payload):
            raise ValueError(f'Missing/unsafe required CPU/GPU payload file: {name}')
    require_x64(payload / 'Violilt.exe')
    previous_audit = json.loads((payload / 'package-audit.json').read_text(encoding='utf-8'))
    if previous_audit.get('status') != 'pass' or previous_audit.get('violations'):
        raise ValueError('The actual executable/package audit must pass before packaging.')
    runtime = json.loads((payload / 'gpu-runtime/violilt-runtime.json').read_text(encoding='utf-8'))
    if runtime.get('provider') != 'CUDAExecutionProvider':
        raise ValueError('The GPU runtime must have a successful CUDA probe marker.')
    files = list(payload_files(payload))
    verified_models = {name: verify_file(payload / 'models' / name) for name in APPROVED}
    try:
        current_audit = audit(payload, write_report=False)
    except (ArchiveReadError, OSError, ValueError, EOFError, TypeError) as error:
        raise ValueError('The actual executable/package audit could not read this payload.') from error
    if current_audit['status'] != 'pass' or current_audit['violations']:
        raise ValueError('The actual executable/package audit must pass before packaging: '
                         + '; '.join(current_audit['violations']))
    audited_files = {item['path']: item for item in current_audit['files']}
    for name, expected in verified_models.items():
        if audited_files['models/' + name]['sha256'] != expected:
            raise ValueError('The model files changed during the package audit. Retry with an unchanged payload.')
    stage.mkdir(parents=True, exist_ok=True)
    if (stage / 'mapping.txt').exists():
        raise ValueError('Use a new staging directory; existing package inputs will not be overwritten.')
    for name in ('StoreLogo.png', 'Square150x150Logo.png', 'Square44x44Logo.png'):
        path = stage / 'Assets' / name
        if not path.is_file():
            raise ValueError(f'Missing generated package asset: {name}')
        files.append((path, 'Assets/' + name))
    marker = stage / 'violilt-candidate.json'
    marker.write_text(json.dumps({'data_profile': PROFILE, 'development': True,
                                  'compatibility_only': True}, indent=2), encoding='utf-8')
    files.append((marker, 'App/violilt-candidate.json'))
    # The mapped marker is deliberately different from the portable marker.
    # Record the bytes shipped by this package and leave its input untouched.
    audited_files['violilt-candidate.json'] = {
        'path': 'violilt-candidate.json', 'bytes': marker.stat().st_size, 'sha256': digest(marker)}
    mapped_paths = {target.removeprefix('App/') for _source, target in files if target.startswith('App/')}
    current_audit['files'] = [item for name, item in audited_files.items() if name in mapped_paths]
    current_audit['models'] = [item for item in current_audit['files'] if item['path'].startswith('models/')]
    staged_audit = stage / 'package-audit.json'
    staged_audit.write_text(json.dumps(current_audit, indent=2), encoding='utf-8')
    files.append((staged_audit, 'App/package-audit.json'))
    windows = sys.getwindowsversion() if sys.platform == 'win32' else None
    windows_version = f'{windows.major}.{windows.minor}.{windows.build}.0' if windows else '10.0.19041.0'
    package_manifest = stage / 'AppxManifest.xml'
    package_manifest.write_bytes(manifest(config, version, windows_version))
    files.append((package_manifest, 'AppxManifest.xml'))
    inventory = [{'path': target, 'bytes': source.stat().st_size, 'sha256': digest(source)}
                 for source, target in files]
    for item in inventory:
        if item['path'].startswith('App/') and item['path'] != 'App/package-audit.json':
            expected = audited_files.get(item['path'].removeprefix('App/'))
            if expected is None or (item['bytes'], item['sha256']) != (expected['bytes'], expected['sha256']):
                raise ValueError('The payload changed after its audit. Retry with an unchanged payload.')
    # Do not place this absolute-path mapping inside the distributed package.
    (stage / 'mapping.txt').write_text('[Files]\n' + ''.join(
        f'"{source}" "{target.replace(chr(47), chr(92))}"\n' for source, target in files), encoding='utf-8')
    report = {'schema': 1, 'compatibility_only': True, 'store_ready': False,
              'identity_name': config['identity_name'], 'publisher': config['publisher'],
              'version': version, 'architecture': 'x64', 'data_profile': PROFILE,
              'cpu_included': True, 'nvidia_included': True, 'gpu_runtime': runtime,
              'verified_models': verified_models,
              'file_count': len(files), 'payload_bytes': sum(item['bytes'] for item in inventory),
              'executable_sha256': digest(payload / 'Violilt.exe'), 'files': inventory,
              'remaining_gates': ['Installed MSIX CPU/GPU tests', 'Real Store identity',
                                  'Redistribution review', 'Security/data hardening', 'Store certification']}
    (stage / 'inventory.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--config', type=Path, default=ROOT / 'packaging/msix/compatibility.json')
    args = parser.parse_args()
    report = prepare(args.payload, args.stage, args.version, args.config)
    print(json.dumps({key: value for key, value in report.items() if key != 'files'}))


if __name__ == '__main__':
    main()
