"""Prepare only the exact, pinned Windows runtime in its isolated project folder."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use an existing public runtime archive instead of downloading.')
    args = parser.parse_args()
    policy = json.loads((ROOT / 'packaging/release-runtime.json').read_text())
    artifact = policy['artifact']
    base = (ROOT / policy['runtime_directory']).resolve()
    if not base.is_relative_to(ROOT / '.tmp') or base.name != 'python':
        raise ValueError('Runtime must have its own python folder inside workspace .tmp.')
    if not base.exists():
        archive = args.archive or ROOT / '.tmp/release-runtime-downloads' / urllib.parse.unquote(artifact['url'].rsplit('/', 1)[1])
        if not archive.exists():
            archive.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(artifact['url'], timeout=45) as source, archive.open('xb') as output:
                total = 0
                while block := source.read(1024 * 1024):
                    total += len(block)
                    if total > artifact['bytes']:
                        raise ValueError('Runtime download exceeds expected size.')
                    output.write(block)
        digest = hashlib.sha256()
        with archive.open('rb') as source:
            while block := source.read(1024 * 1024): digest.update(block)
        if archive.stat().st_size != artifact['bytes'] or digest.hexdigest() != artifact['sha256']:
            raise ValueError('Runtime archive differs from the pinned official artifact.')
        destination = base.parent
        destination.mkdir(parents=True, exist_ok=False)
        with tarfile.open(archive) as bundle:
            members = bundle.getmembers()
            if len(members) > 25_000:
                raise ValueError('Too many runtime archive entries.')
            total = 0
            for member in members:
                name = PurePosixPath(member.name)
                if name.is_absolute() or '..' in name.parts or not name.parts or name.parts[0] != 'python' or any(':' in part or '\\' in part for part in name.parts):
                    raise ValueError('Unsafe runtime archive path.')
                target = destination.joinpath(*name.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    total += member.size
                    if total > 500_000_000 or member.size > 100_000_000:
                        raise ValueError('Runtime expansion exceeds limits.')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.extractfile(member) as source, target.open('xb') as output:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
                else:
                    raise ValueError('Runtime links/special files are not accepted.')
    # Existing or newly extracted runtimes must pass the same actual-byte check.
    subprocess.run([str(base / 'python.exe'), '-B', str(ROOT / 'tools/verify_release_runtime.py')], check=True)


if __name__ == '__main__': main()
