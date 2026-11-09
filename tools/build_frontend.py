"""Build current frontend source with isolated locked dependencies; preserve old assets."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    policy = json.loads((ROOT / 'packaging/release-runtime.json').read_text())
    dependencies = (ROOT / policy['frontend_directory']).resolve()
    if not dependencies.is_relative_to(ROOT / '.tmp'):
        raise ValueError('Use isolated frontend dependencies inside workspace .tmp.')
    source = ROOT / 'frontend'
    for name in ('package.json', 'package-lock.json'):
        if (source / name).read_bytes() != (dependencies / name).read_bytes():
            raise ValueError(f'Isolated frontend {name} differs. Prepare matching locked dependencies first.')
    expected = json.loads((source / 'package-lock.json').read_text())['packages']['node_modules/dompurify']['version']
    installed = json.loads((dependencies / 'node_modules/dompurify/package.json').read_text())['version']
    if installed != expected:
        raise ValueError('Installed DOMPurify differs from the selected frontend lock.')
    stage = Path(tempfile.mkdtemp(prefix='frontend-release-', dir=ROOT / '.tmp'))
    for entry in source.iterdir():
        if entry.name in {'node_modules', 'dist'}:
            continue
        target = stage / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target)
        else:
            shutil.copyfile(entry, target)
    shutil.copytree(dependencies / 'node_modules', stage / 'node_modules')
    node = shutil.which('node')
    if not node:
        raise ValueError('Node.js is required to build the interface.')
    subprocess.run([node, str(stage / 'node_modules/svelte-check/bin/svelte-check'), '--tsconfig', './tsconfig.json'], cwd=stage, check=True)
    subprocess.run([node, str(stage / 'node_modules/vite/bin/vite.js'), 'build'], cwd=stage, check=True)
    target = source / 'dist'
    backup = ROOT / '.tmp' / ('frontend-dist-before-' + uuid.uuid4().hex)
    # These exact resolved paths stay inside the workspace. Never delete the old
    # assets: a failed promotion restores them, and reviewers can inspect them.
    if target.resolve() != ROOT / 'frontend/dist' or not backup.resolve().is_relative_to(ROOT / '.tmp'):
        raise ValueError('Unexpected frontend promotion path.')
    existed = target.exists()
    if existed:
        target.replace(backup)
    try:
        (stage / 'dist').replace(target)
    except OSError:
        if existed and not target.exists():
            backup.replace(target)
        raise
    records = {path.relative_to(target).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in target.rglob('*') if path.is_file()}
    report = {'current_source': 'frontend', 'dependencies': policy['frontend_directory'],
              'lock_sha256': hashlib.sha256((source / 'package-lock.json').read_bytes()).hexdigest(),
              'preserved_assets': str(backup) if existed else None, 'built_assets': records}
    (stage / 'build-provenance.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'provenance': str(stage / 'build-provenance.json'), 'assets': len(records)}))


if __name__ == '__main__':
    main()
