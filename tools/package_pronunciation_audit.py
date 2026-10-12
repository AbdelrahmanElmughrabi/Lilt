"""Audit actual candidate executable/archive content; not a legal-clearance tool."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_MODULES = ('kokoro_onnx', 'phonemizer', 'phonemizer_fork', 'espeakng_loader',
                     'misaki.espeak', 'torch', 'transformers', 'spacy_curated_transformers',
                     'curated_transformers', 'PyInstaller.utils', 'pythonnet._pyinstaller',
                     'webview.__pyinstaller', 'setuptools._vendor.autocommand')


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def audit(package: Path) -> dict:
    executable = package / 'Lilt.exe'
    archive = CArchiveReader(str(executable))
    modules = []
    archive_names = sorted(archive.toc)
    for name in archive_names:
        if archive.toc[name][-1] == 'z':
            modules.extend(archive.open_embedded_archive(name).toc)
    modules = sorted(set(modules))
    violations = [f'Forbidden frozen module: {name}' for name in modules
                  if any(name == prefix or name.startswith(prefix + '.') for prefix in FORBIDDEN_MODULES)]
    files = []
    for path in sorted(package.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(package).as_posix()
        if relative == 'package-audit.json':
            continue
        # Legal source/notice archives may legitimately mention inactive optional
        # dependencies or original upstream licensing; inspect runtime paths.
        if not relative.startswith('third-party/'):
            normalized = relative.lower().replace('-', '_')
            runtime_path = relative.removeprefix('_internal/').removeprefix('gpu-runtime/')
            external_module = runtime_path.rsplit('.', 1)[0].replace('/', '.')
            if any(external_module == prefix or external_module.startswith(prefix + '.') for prefix in FORBIDDEN_MODULES):
                violations.append(f'Forbidden external module: {relative}')
            # Only top-level third-party packages are rejected here. ONNX Runtime
            # has its own MIT `onnxruntime/transformers` optimization subpackage;
            # that name is not the Hugging Face transformers dependency.
            if re.search(r'^(?:_internal/|gpu_runtime/)?(?:phonemizer[^/]*|espeak[^/]*|torch[^/]*|transformers[^/]*)(/|\.|$)', normalized) or re.search(r'(^|/)espeak[^/]*\.dll$', normalized):
                violations.append(f'Forbidden runtime file: {relative}')
            if relative.startswith('gpu-runtime/nvidia/') and path.suffix.lower() in ('.h', '.hpp', '.lib'):
                violations.append(f'GPU development file bundled: {relative}')
        files.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest(path)})
    required = ['lilt-candidate.json', '_internal/misaki/data/us_gold.json', '_internal/misaki/data/us_silver.json',
                '_internal/misaki/data/gb_gold.json', '_internal/misaki/data/gb_silver.json',
                '_internal/num2words/__init__.py', 'third-party/manifest.json',
                'third-party/sources/source-manifest.json', '_internal/_soundfile_data/libsndfile_x64.dll']
    for relative in required:
        if not (package / relative).is_file():
            violations.append(f'Required candidate artifact missing: {relative}')
    for prefix in ('num2words', 'certifi', 'tqdm'):
        if any(name == prefix or name.startswith(prefix + '.') for name in modules):
            violations.append(f'Covered source remains frozen instead of external: {prefix}')
    for prefix in ('misaki', 'spacy', 'thinc', 'regex', 'addict', 'numpy', 'en_core_web_sm', 'num2words'):
        if not list((package / '_internal').glob(prefix + '-*.dist-info')) and not list((package / '_internal').glob(prefix.replace('_', '-') + '-*.dist-info')):
            violations.append(f'Required frozen metadata missing: {prefix}')
    report = {'schema': 1, 'status': 'pass' if not violations else 'fail', 'violations': violations,
              'scope': 'actual executable PYZ modules and package files; legal/artifact provenance review remains pending',
              'archive_entries': archive_names, 'frozen_modules': modules, 'files': files,
              'models': [item for item in files if item['path'].startswith('models/')],
              'limitations': ['Inactive extras in upstream metadata are not active runtime dependencies.',
                              'No automatic inference of every native/vendored component license.',
                              'Successful GPL-path exclusion is not blanket commercial release clearance.']}
    (package / 'package-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=ROOT / 'dist/pronunciation/Lilt')
    arguments = parser.parse_args()
    report = audit(arguments.package.resolve())
    print(json.dumps({'status': report['status'], 'frozen_modules': len(report['frozen_modules']),
                      'files': len(report['files']), 'violations': report['violations']}, indent=2))
    raise SystemExit(0 if report['status'] == 'pass' else 1)


if __name__ == '__main__':
    main()
