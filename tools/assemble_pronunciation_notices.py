"""Prepare versioned notices/source for the isolated candidate, without modifying baseline files.

This collects conservatively from the build environment. The package audit records
actual frozen modules separately; notice collection is not distribution clearance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import re
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CACHE = ROOT / '.tmp' / 'pronunciation-sources'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r'[^a-zA-Z0-9._-]', '-', value)


def fetch(url: str, destination: Path, expected_sha256: str | None = None) -> dict:
    if not destination.exists():
        request = urllib.request.Request(url, headers={'User-Agent': 'Violilt-Pronunciation-Evaluation/1'})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read(100_000_001)
        if len(payload) > 100_000_000:
            raise ValueError('Source archive exceeds the download size limit.')
        digest = hashlib.sha256(payload).hexdigest()
        if expected_sha256 and digest != expected_sha256:
            raise ValueError(f'Source digest mismatch: {destination.name}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    digest = sha256(destination)
    if expected_sha256 and digest != expected_sha256:
        raise ValueError(f'Cached source digest mismatch: {destination.name}')
    return {'filename': destination.name, 'url': url, 'sha256': digest,
            'upstream_sha256_verified': bool(expected_sha256)}


EIGEN_COMPONENT = 'onnxruntime-eigen'


def eigen_source_spec() -> dict:
    spec_path = ROOT / 'thirdparty/ort-eigen/source.json'
    if not spec_path.is_file():
        raise ValueError('Required Eigen source specification is missing.')
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    for item in [spec['archive'], *spec['support_files']]:
        for field in ('filename', 'cache_filename'):
            name = item[field]
            if not name or Path(name).name != name or '/' in name or '\\' in name:
                raise ValueError('Eigen source filenames must be plain basenames.')
    return spec


def check_eigen_material(path: Path, item: dict, *, archive: bool = False) -> None:
    if not path.is_file() or path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
        raise ValueError(f'Eigen source material missing or changed: {item["filename"]}')
    if archive:
        with path.open('rb') as stream:
            actual_sha1 = hashlib.file_digest(stream, 'sha1').hexdigest()
        if actual_sha1 != item['upstream_sha1']:
            raise ValueError('Eigen archive differs from the upstream declared SHA-1.')


def eigen_source_record(spec: dict) -> dict:
    archive = spec['archive']
    return {
        'component': EIGEN_COMPONENT, 'version': spec['source_revision'],
        'filename': archive['cache_filename'], 'url': archive['url'],
        'bytes': archive['bytes'], 'sha256': archive['sha256'],
        'sha1': archive['upstream_sha1'],
        # SHA-256 is a reviewed local capture pin, not an upstream-published digest.
        'upstream_sha256_verified': False, 'upstream_sha1_verified': True,
        'sha256_provenance': spec['sha256_provenance'],
        'runtime_tags': spec['runtime_tags'], 'association_limit': spec['association_limit'],
        'output_directory': 'onnxruntime-eigen', 'patch_order': spec['patch_order'],
        'support_files': spec['support_files'], 'official_release_texts': spec['official_release_texts'],
    }


def prepare_eigen_source() -> dict:
    spec = eigen_source_spec()
    support_root = ROOT / 'thirdparty/ort-eigen'
    for item in spec['support_files']:
        check_eigen_material(support_root / item['filename'], item)
    archive = spec['archive']
    # fetch() reports bool(expected_sha256). Do not propagate that generic flag:
    # this expected SHA-256 is locally recorded; only SHA-1 was upstream-declared.
    fetch(archive['url'], SOURCE_CACHE / archive['cache_filename'], archive['sha256'])
    check_eigen_material(SOURCE_CACHE / archive['cache_filename'], archive, archive=True)
    SOURCE_CACHE.mkdir(parents=True, exist_ok=True)
    for item in spec['support_files']:
        target = SOURCE_CACHE / item['cache_filename']
        if target.exists():
            check_eigen_material(target, item)
        else:
            shutil.copyfile(support_root / item['filename'], target)
            check_eigen_material(target, item)
    return eigen_source_record(spec)


def collect_eigen_source(output: Path, sources: list[dict]) -> None:
    spec = eigen_source_spec()
    expected = eigen_source_record(spec)
    records = [item for item in sources if item.get('component') == EIGEN_COMPONENT]
    if len(records) != 1 or records[0] != expected:
        raise ValueError('Required Eigen source record missing or differs from the reviewed specification; prepare sources before packaging.')
    materials = [spec['archive'], *spec['support_files']]
    for index, item in enumerate(materials):
        check_eigen_material(SOURCE_CACHE / item['cache_filename'], item, archive=index == 0)
    destination = output / 'sources/onnxruntime-eigen'
    destination.mkdir(parents=True, exist_ok=True)
    for item in materials:
        target = destination / item['filename']
        shutil.copyfile(SOURCE_CACHE / item['cache_filename'], target)
        check_eigen_material(target, item)
    (destination / 'source-manifest.json').write_text(json.dumps(expected, indent=2), encoding='utf-8')


def prepare_sources() -> list[dict]:
    SOURCE_CACHE.mkdir(parents=True, exist_ok=True)
    sources = []
    for name in ('num2words', 'certifi', 'tqdm', 'proxy_tools'):
        version = metadata.version(name)
        url = f'https://pypi.org/pypi/{name}/{version}/json'
        request = urllib.request.Request(url, headers={'User-Agent': 'Violilt-Pronunciation-Evaluation/1'})
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
        artifact = next(item for item in release['urls'] if item['packagetype'] == 'sdist')
        item = fetch(artifact['url'], SOURCE_CACHE / artifact['filename'], artifact['digests']['sha256'])
        sources.append(item | {'component': name, 'version': version, 'metadata_url': url})
    # Keep already cached legacy review materials; never fetch a removed native
    # dependency or require its installed metadata. Do not delete prior evidence.
    previous = SOURCE_CACHE / 'source-manifest.json'
    for item in json.loads(previous.read_text(encoding='utf-8')) if previous.is_file() else []:
        if item['component'] in {'soundfile', 'libsndfile'}:
            source = SOURCE_CACHE / item['filename']
            if not source.is_file() or sha256(source) != item['sha256']:
                raise ValueError('Retained legacy audio source archive is missing or changed.')
            sources.append(item)
    sources.append(prepare_eigen_source())
    (SOURCE_CACHE / 'source-manifest.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')
    return sources


def assemble(output: Path, frontend_directory: Path | None = None) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    packages = []
    missing = []
    source_records = json.loads((SOURCE_CACHE / 'source-manifest.json').read_text(encoding='utf-8')) if (SOURCE_CACHE / 'source-manifest.json').is_file() else []
    for distribution in sorted(metadata.distributions(), key=lambda item: item.metadata['Name'].lower()):
        name, version = distribution.metadata['Name'], distribution.version
        if name.lower() == 'pip':
            continue
        records = []
        for entry in distribution.files or []:
            source = Path(distribution.locate_file(entry))
            if not source.is_file() or not re.search('license|licence|copying|notice|eula', source.name, re.I):
                continue
            # Preserve relative names, because NumPy/setuptools have many similarly
            # named vendored notices. Never collapse them into a single LICENSE.
            parts = [safe_name(part) for part in Path(str(entry)).parts if part not in ('.', '..')]
            destination = output / 'python' / safe_name(f'{name}-{version}') / Path(*parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            records.append({'path': destination.relative_to(output).as_posix(), 'sha256': sha256(source)})
        # Some wheels omit upstream LICENSE files; recover them from the matching
        # digest-verified source distribution without changing the environment.
        if not records:
            supplement = ROOT / 'thirdparty/licenses' / safe_name(f'{name}-{version}-LICENSE.txt')
            if supplement.is_file():
                destination = output / 'python' / safe_name(f'{name}-{version}') / 'upstream-LICENSE.txt'
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(supplement, destination)
                records.append({'path': destination.relative_to(output).as_posix(), 'sha256': sha256(supplement),
                                'origin': 'checked-in upstream notice; provenance in thirdparty/licenses/README.md'})
        if not records:
            source_record = next((item for item in source_records if item['component'].replace('_', '-').lower() == name.replace('_', '-').lower() and item['version'] == version), None)
            if source_record:
                with tarfile.open(SOURCE_CACHE / source_record['filename']) as archive:
                    for member in archive.getmembers():
                        if not member.isfile() or not re.search('license|licence|copying|notice', Path(member.name).name, re.I):
                            continue
                        source = archive.extractfile(member)
                        if source is None:
                            continue
                        payload = source.read()
                        destination = output / 'python' / safe_name(f'{name}-{version}') / safe_name(member.name)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(payload)
                        records.append({'path': destination.relative_to(output).as_posix(), 'sha256': hashlib.sha256(payload).hexdigest(),
                                        'origin': source_record['filename']})
        if not records:
            missing.append(f'No installed notice file identified for {name}=={version}.')
        packages.append({'name': name, 'version': version,
                         'license_declaration': distribution.metadata.get('License-Expression') or distribution.metadata.get('License'),
                         'project_urls': distribution.metadata.get_all('Project-URL', []), 'notices': records,
                         'scope': 'installed build environment; actual inclusion recorded by package audit'})

    frontend = []
    frontend_directory = frontend_directory or ROOT / 'frontend'
    if (frontend_directory / 'package-lock.json').read_bytes() != (ROOT / 'frontend/package-lock.json').read_bytes():
        raise ValueError('Frontend notice inputs differ from the canonical lock.')
    frontend_lock = json.loads((ROOT / 'frontend' / 'package-lock.json').read_text(encoding='utf-8'))
    for location, record in frontend_lock['packages'].items():
        if not location:
            continue
        folder = frontend_directory / location
        installed_metadata = folder / 'package.json'
        if installed_metadata.is_file() and json.loads(installed_metadata.read_text(encoding='utf-8')).get('version') != record.get('version'):
            raise ValueError(f'Installed frontend notice version differs from the lock: {location}')
        names = []
        for source in sorted(folder.glob('*')):
            if not source.is_file() or not re.search('license|licence|copying|notice', source.name, re.I):
                continue
            destination = output / 'frontend' / safe_name(location) / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            names.append(destination.relative_to(output).as_posix())
        frontend.append({'location': location, 'version': record.get('version'),
                         'license_declaration': record.get('license'), 'notices': names,
                         'scope': 'conservative complete frontend build lock'})

    native = output / 'native'
    native.mkdir(exist_ok=True)
    additional = {
        'Python-LICENSE.txt': Path(sys.base_prefix) / 'LICENSE.txt',
        # Supplement the runtime license with separate embedded-library and
        # stdlib attributions. These fixed inputs follow the selected runtime;
        # source/recipe references are not exact compiled-build attestations.
        'Expat-2.8.5-COPYING.txt': ROOT / 'thirdparty/licenses/Expat-2.8.5-COPYING.txt',
        'base-runtime-libffi-LICENSE.txt': ROOT / 'thirdparty/licenses/CPython-source-deps-16fad485-libffi-LICENSE.txt',
        'CFFI-2.1.1-embedded-libffi-LICENSE.txt': ROOT / 'thirdparty/licenses/CFFI-2.1.1-embedded-libffi-LICENSE.txt',
        'CPython-3.12.15-stdlib-notices.rst': ROOT / 'thirdparty/licenses/CPython-3.12.15-stdlib-notices.rst',
        'CPython-3.12-mpdecimal-LICENSE.txt': ROOT / 'thirdparty/licenses/CPython-3.12-mpdecimal-LICENSE.txt',
        'LGPL-2.1.txt': ROOT / 'thirdparty/licenses/LGPL-2.1.txt',
        'MPL-2.0.txt': ROOT / 'thirdparty/licenses/MPL-2.0.txt',
        'DOMPurify-3.4.17-license-choice.txt': ROOT / 'thirdparty/licenses/DOMPurify-3.4.17-license-choice.txt',
        'WebView2-SDK-LICENSE.txt': ROOT / 'thirdparty/licenses/WebView2-SDK-1.0.3856.49-LICENSE.txt',
        'WebView2-SDK-NOTICE.txt': ROOT / 'thirdparty/licenses/WebView2-SDK-1.0.3856.49-NOTICE.txt',
        'Microsoft-VC-runtime-NOTICE.txt': ROOT / 'thirdparty/licenses/Microsoft-VC-runtime-NOTICE.txt',
        'NVIDIA-CUDA-12.9.2-terms.txt': ROOT / 'thirdparty/licenses/NVIDIA-CUDA-12.9.2-terms.txt',
        'NVIDIA-cuDNN-9.27-terms.txt': ROOT / 'thirdparty/licenses/NVIDIA-cuDNN-9.27-terms.txt',
        'NVIDIA-nvJitLink-LICENSE.txt': ROOT / 'thirdparty/licenses/NVIDIA-nvJitLink-LICENSE.txt',
        'kokoro-onnx-MIT-LICENSE.txt': ROOT / 'thirdparty/licenses/kokoro-onnx-0.6.1-LICENSE.txt',
        'librosa-trim-NOTICE.txt': ROOT / 'thirdparty/licenses/librosa-trim-NOTICE.txt',
        # Full Apache-2.0 terms are identical; provenance and attribution below are
        # kept separately from this standard license text.
        'Apache-2.0.txt': Path(metadata.distribution('misaki').locate_file('misaki-0.9.4.dist-info/licenses/LICENSE')),
    }
    for label, source in additional.items():
        if source.is_file():
            shutil.copyfile(source, native / label)
        else:
            missing.append(f'Missing additional notice evidence: {label}.')
    shutil.copyfile(ROOT / 'thirdparty/PRONUNCIATION-CANDIDATE.md', output / 'README.md')

    sources = []
    source_manifest = SOURCE_CACHE / 'source-manifest.json'
    if source_manifest.is_file():
        sources = json.loads(source_manifest.read_text(encoding='utf-8'))
        collect_eigen_source(output, sources)
        for item in sources:
            if item.get('component') == EIGEN_COMPONENT:
                continue  # Complete archive/support files are copied to their nested source folder.
            source = SOURCE_CACHE / item['filename']
            if not source.is_file() or sha256(source) != item['sha256']:
                raise ValueError(f'Prepared source archive missing or changed: {item["filename"]}')
            destination = output / 'sources' / item['filename']
            destination.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, destination)
        shutil.copyfile(source_manifest, output / 'sources/source-manifest.json')
    else:
        collect_eigen_source(output, [])  # Required covered source fails explicitly when not prepared.
        missing.append('Source archives not prepared; run with --download-sources before redistribution.')
    # Versioned source/attribution inputs are reviewed beside the collector.
    # Their truthful development limits and full notices must survive packaging.
    component_documents = {
        'MODEL-ATTRIBUTIONS.md': ROOT / 'thirdparty/MODEL-ATTRIBUTIONS.md',
        'SOURCE-RIGHTS.md': ROOT / 'thirdparty/COMPONENT-SOURCE.md',
        'LIBRARY-REPLACEMENT.md': ROOT / 'thirdparty/LIBRARY-REPLACEMENT.md',
        'NVIDIA-TERMS.md': ROOT / 'thirdparty/NVIDIA-TERMS.md',
    }
    for label, source in component_documents.items():
        if source.is_file():
            shutil.copyfile(source, output / label)
        else:
            missing.append(f'Missing component document: {label}.')
    report = {'schema': 1, 'status': 'development evaluation; distribution review pending',
              'packages': packages, 'frontend': frontend, 'source_archives': sources,
              'missing_evidence': missing,
              'release_gates': ['final model/voice/data inclusion and attribution fulfillment', 'actual payload excludes removed SoundFile/libsndfile runtime',
                                'Microsoft native runtime redistribution authority', 'optional NVIDIA exact artifact/EULA mapping',
                                'complete native/vendor inspection and eventual EULA rights']}
    report['files'] = [{'path': path.relative_to(output).as_posix(), 'sha256': sha256(path), 'bytes': path.stat().st_size}
                       for path in sorted(output.rglob('*')) if path.is_file() and path.name != 'manifest.json']
    (output / 'manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.tmp/pronunciation-notices')
    parser.add_argument('--frontend-directory', type=Path, default=ROOT / 'frontend', help='Locked frontend dependencies used for this build')
    parser.add_argument('--download-sources', action='store_true', help='Download exact upstream component source archives; needs network access')
    arguments = parser.parse_args()
    if arguments.download_sources:
        prepare_sources()
    report = assemble(arguments.output.resolve(), arguments.frontend_directory.resolve())
    print(json.dumps({'packages': len(report['packages']), 'notice_files': len(report['files']),
                      'source_archives': len(report['source_archives']), 'missing_evidence': report['missing_evidence'],
                      'status': report['status']}, indent=2))


if __name__ == '__main__':
    main()
