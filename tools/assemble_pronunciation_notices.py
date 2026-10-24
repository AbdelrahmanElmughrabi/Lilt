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


def prepare_sources() -> list[dict]:
    SOURCE_CACHE.mkdir(parents=True, exist_ok=True)
    sources = []
    for name in ('num2words', 'certifi', 'tqdm', 'soundfile', 'proxy_tools'):
        version = metadata.version(name)
        url = f'https://pypi.org/pypi/{name}/{version}/json'
        request = urllib.request.Request(url, headers={'User-Agent': 'Violilt-Pronunciation-Evaluation/1'})
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
        artifact = next(item for item in release['urls'] if item['packagetype'] == 'sdist')
        item = fetch(artifact['url'], SOURCE_CACHE / artifact['filename'], artifact['digests']['sha256'])
        sources.append(item | {'component': name, 'version': version, 'metadata_url': url})
    # This is upstream library source for review. It is not asserted to reproduce
    # SoundFile's exact embedded codecs/DLL until its build chain is verified.
    sources.append(fetch('https://codeload.github.com/libsndfile/libsndfile/tar.gz/refs/tags/1.2.2',
                         SOURCE_CACHE / 'libsndfile-1.2.2.tar.gz') |
                   {'component': 'libsndfile', 'version': '1.2.2', 'exact_dll_build_verified': False})
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
    (output / 'MODEL-ATTRIBUTIONS.md').write_text(
        '# Model/data attribution and provenance status\n\n'
        'Kokoro-82M by hexgrad: Apache-2.0. https://huggingface.co/hexgrad/Kokoro-82M\n'
        'ONNX conversion/artifacts supplied through the kokoro-onnx release chain: '
        'https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0\n'
        'The Violilt inference adapter is derived from the MIT kokoro-onnx 0.6.1 wrapper; '
        'it removes the eSpeak/Phonemizer stage and consumes English Misaki phonemes.\n'
        'Misaki 0.9.4 English dictionaries: declared Apache-2.0 coverage in the package; '
        'independent dictionary provenance review remains open. https://github.com/hexgrad/misaki\n'
        'spaCy en_core_web_sm 3.8.0: MIT model; model package notices are retained in python/. '
        'https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0\n\n'
        'Local packaged model SHA-256 values appear in package-audit.json. They identify '
        'the exact local bytes and do not by themselves establish upstream authenticity. '
        'Exact converted weight/voice provenance and applicable modification/NOTICE '
        'mapping remain release gates. The whole distributed voice file is in scope.\n', encoding='utf-8')

    sources = []
    source_manifest = SOURCE_CACHE / 'source-manifest.json'
    if source_manifest.is_file():
        sources = json.loads(source_manifest.read_text(encoding='utf-8'))
        for item in sources:
            source = SOURCE_CACHE / item['filename']
            if not source.is_file() or sha256(source) != item['sha256']:
                raise ValueError(f'Prepared source archive missing or changed: {item["filename"]}')
            destination = output / 'sources' / item['filename']
            destination.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, destination)
        shutil.copyfile(source_manifest, output / 'sources/source-manifest.json')
    else:
        missing.append('Source archives not prepared; run with --download-sources before redistribution.')
    source_readme = output / 'SOURCE-RIGHTS.md'
    source_readme.write_text(
        '# Component source and replacement rights\n\n'
        'num2words source remains under its LGPL terms. certifi/tqdm covered source '
        'remains under the applicable MPL terms (tqdm also has MIT contributions). '
        'Matching unmodified upstream source archives and notices are supplied in sources/. '
        'External runtime Python source is in _internal/num2words, _internal/certifi and '
        '_internal/tqdm when these components are collected. Recipients may inspect, '
        'modify and replace these components under their own licenses. No Violilt terms '
        'may restrict those component rights. Compatible replacements must retain '
        'the relevant public interfaces.\n\n'
        'libsndfile is an external replaceable DLL in _internal/_soundfile_data/. '
        'Supplied upstream libsndfile and SoundFile source archives are review '
        'materials; exact DLL build/embedded codec source remains unresolved. '
        'Replacement testing and full matching LGPL source/build arrangement are '
        'required before external release. These source rights concern third-party '
        'components; independent Violilt application files remain separate.\n', encoding='utf-8')
    report = {'schema': 1, 'status': 'development evaluation; distribution review pending',
              'packages': packages, 'frontend': frontend, 'source_archives': sources,
              'missing_evidence': missing,
              'release_gates': ['model/voice/dictionary provenance', 'exact libsndfile DLL/codec build and corresponding source',
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
