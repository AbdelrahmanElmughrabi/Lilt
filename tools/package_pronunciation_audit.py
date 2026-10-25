"""Audit actual candidate executable/archive content; not a legal-clearance tool."""
from __future__ import annotations

import argparse
import dis
import hashlib
import json
import marshal
import re
import sys
import types
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))

from backend.runtime import verify_gpu_runtime
FORBIDDEN_MODULES = ('soundfile', '_soundfile', '_soundfile_data', 'kokoro_onnx', 'phonemizer', 'phonemizer_fork', 'espeakng_loader',
                     'misaki.espeak', 'torch', 'transformers', 'spacy_curated_transformers',
                     'curated_transformers', 'PyInstaller.utils', 'pythonnet._pyinstaller',
                     'webview.__pyinstaller', 'setuptools._vendor.autocommand')
DEVELOPMENT_MODULES = ('tools', 'tests')
REMOVED_PRONUNCIATION = ('kokoro_onnx', 'phonemizer', 'phonemizer_fork', 'espeakng_loader', 'misaki.espeak')

REMOVED_AUDIO = ('soundfile', '_soundfile', '_soundfile_data')


def removed_imports(code, prohibited=REMOVED_PRONUNCIATION):
    """Inspect nested functions too; an absent package can still have dormant imports."""
    found = set()
    source_module = ''
    for instruction in dis.get_instructions(code):
        if instruction.opname == 'IMPORT_NAME':
            source_module = instruction.argval
            name = source_module
        elif instruction.opname == 'IMPORT_FROM':
            name = source_module + '.' + instruction.argval
        else:
            continue
        found.update(prefix for prefix in prohibited
                     if name == prefix or name.startswith(prefix + '.'))
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            found.update(removed_imports(value, prohibited))
    return found


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def audit(package: Path, *, write_report: bool = True) -> dict:
    executable = package / 'Violilt.exe'
    archive = CArchiveReader(str(executable))
    modules = []
    obsolete_imports = []
    audio_imports = []
    pcm_writer_present = False
    archive_names = sorted(archive.toc)
    for name in archive_names:
        if archive.toc[name][-1] == 'z':
            pyz = archive.open_embedded_archive(name)
            modules.extend(pyz.toc)
            for module in pyz.toc:
                if module == 'backend' or module.startswith('backend.'):
                    code = pyz.extract(module)
                    if isinstance(code, types.CodeType):
                        obsolete_imports.extend(f'{module}: {target}' for target in sorted(removed_imports(code)))
                        audio_imports.extend(f'{module}: {target}' for target in sorted(removed_imports(code, REMOVED_AUDIO)))
                        if module == 'backend.pcm_audio':
                            pcm_writer_present = any(isinstance(value, types.CodeType) and value.co_name == 'write_pcm16'
                                                     for value in code.co_consts)
        elif name == 'main':
            code = marshal.loads(archive.extract(name))
            obsolete_imports.extend(f'main: {target}' for target in sorted(removed_imports(code)))
            audio_imports.extend(f'main: {target}' for target in sorted(removed_imports(code, REMOVED_AUDIO)))
    modules = sorted(set(modules))
    violations = [f'Forbidden frozen module: {name}' for name in modules
                  if any(name == prefix or name.startswith(prefix + '.') for prefix in (*FORBIDDEN_MODULES, *DEVELOPMENT_MODULES))]
    violations.extend(f'Removed pronunciation import in shipped app code: {item}' for item in obsolete_imports)
    violations.extend(f'Removed native audio import in shipped app code: {item}' for item in audio_imports)
    if not pcm_writer_present:
        violations.append('Required generated PCM16 writer missing: backend.pcm_audio.write_pcm16')
    files = []
    for path in sorted(package.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(package).as_posix()
        if relative == 'package-audit.json':
            continue
        # A native binary is still redistributed if misplaced among legal
        # materials. Preserve license/source text, never exempt a physical DLL.
        if path.name.lower().startswith('libsndfile') and path.suffix.lower() in {'.dll', '.pyd', '.so', '.dylib'}:
            violations.append(f'Removed SoundFile/libsndfile runtime file: {relative}')
        # Legal source/notice archives may legitimately mention inactive optional
        # dependencies or original upstream licensing; inspect runtime paths.
        if not relative.startswith('third-party/'):
            normalized = relative.lower().replace('-', '_')
            if (path.name.lower().startswith('libsndfile')
                    or any(part.lower().replace('-', '_').startswith(('soundfile_', 'soundfile.', '_soundfile'))
                           for part in relative.split('/'))):
                violations.append(f'Removed SoundFile/libsndfile runtime file: {relative}')
            runtime_path = relative.removeprefix('_internal/').removeprefix('gpu-runtime/')
            external_module = runtime_path.rsplit('.', 1)[0].replace('/', '.')
            if any(external_module == prefix or external_module.startswith(prefix + '.') for prefix in (*FORBIDDEN_MODULES, *DEVELOPMENT_MODULES)):
                violations.append(f'Forbidden external module: {relative}')
            # Only top-level third-party packages are rejected here. ONNX Runtime
            # has its own MIT `onnxruntime/transformers` optimization subpackage;
            # that name is not the Hugging Face transformers dependency.
            if (re.search(r'^(?:_internal/|gpu_runtime/)?(?:torch[^/]*|transformers[^/]*)(/|\.|$)', normalized)
                    or re.search(r'(^|/)(?:phonemizer[^/]*|espeak[^/]*)(/|\.|$)', normalized)):
                violations.append(f'Forbidden runtime file: {relative}')
            if relative.startswith('gpu-runtime/nvidia/') and path.suffix.lower() in ('.h', '.hpp', '.lib'):
                violations.append(f'GPU development file bundled: {relative}')
        files.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest(path)})
    required = ['violilt-candidate.json', '_internal/misaki/data/us_gold.json', '_internal/misaki/data/us_silver.json',
                '_internal/misaki/data/gb_gold.json', '_internal/misaki/data/gb_silver.json',
                '_internal/num2words/__init__.py', 'third-party/manifest.json',
                'third-party/sources/source-manifest.json']
    for relative in required:
        if not (package / relative).is_file():
            violations.append(f'Required candidate artifact missing: {relative}')
    for prefix in ('num2words', 'certifi', 'tqdm'):
        if any(name == prefix or name.startswith(prefix + '.') for name in modules):
            violations.append(f'Covered source remains frozen instead of external: {prefix}')
    for prefix in ('misaki', 'spacy', 'thinc', 'regex', 'addict', 'numpy', 'en_core_web_sm', 'num2words'):
        if not list((package / '_internal').glob(prefix + '-*.dist-info')) and not list((package / '_internal').glob(prefix.replace('_', '-') + '-*.dist-info')):
            violations.append(f'Required frozen metadata missing: {prefix}')
    if (package / 'gpu-runtime').exists():
        try:
            verify_gpu_runtime(package / 'gpu-runtime')
        except (ValueError, OSError, UnicodeError, RuntimeError) as error:
            violations.append(f'GPU runtime verification failed: {error}')
    report = {'schema': 1, 'status': 'pass' if not violations else 'fail', 'violations': violations,
              'scope': 'actual executable PYZ modules and package files; legal/artifact provenance review remains pending',
              'archive_entries': archive_names, 'frozen_modules': modules, 'files': files,
              'removed_pronunciation_imports': obsolete_imports,
              'removed_audio_imports': audio_imports, 'generated_pcm16_writer_present': pcm_writer_present,
              'models': [item for item in files if item['path'].startswith('models/')],
              'limitations': ['Inactive extras in upstream metadata are not active runtime dependencies.',
                              'No automatic inference of every native/vendored component license.',
                              'Successful GPL-path exclusion is not blanket commercial release clearance.']}
    if write_report:
        (package / 'package-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=ROOT / 'dist/pronunciation/Violilt')
    arguments = parser.parse_args()
    report = audit(arguments.package.resolve())
    print(json.dumps({'status': report['status'], 'frozen_modules': len(report['frozen_modules']),
                      'files': len(report['files']), 'violations': report['violations']}, indent=2))
    raise SystemExit(0 if report['status'] == 'pass' else 1)


if __name__ == '__main__':
    main()
