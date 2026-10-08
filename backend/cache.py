"""Bounded cache of immutable raw speech sections; recordings are separate."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path


def section_key(text, voice, speed, identity):
    return hashlib.sha256(json.dumps([text, voice, float(speed), identity], ensure_ascii=False).encode()).hexdigest()


def audio_info(path):
    import soundfile as sf
    try:
        info = sf.info(path)
        return info if info.frames > 0 and info.channels == 1 and info.samplerate == 24000 and info.subtype == 'PCM_16' else None
    except (OSError, RuntimeError):
        return None


class SectionCache:
    def __init__(self, root: Path, limit_mb=256):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.limit = int(limit_mb) * 1024 * 1024

    def fetch(self, key, destination):
        path = self.root / (key + '.wav')
        if not audio_info(path):
            return False
        temporary = destination.with_suffix('.cache-part')
        shutil.copyfile(path, temporary)
        temporary.replace(destination)
        os.utime(path, None)
        return True

    def put(self, key, source):
        destination = self.root / (key + '.wav')
        if not destination.exists():
            temporary = destination.with_suffix('.part')
            shutil.copyfile(source, temporary)
            temporary.replace(destination)
        self.prune()

    def files(self):
        return [path for path in self.root.iterdir() if path.is_file() and re.fullmatch(r'[a-f0-9]{64}\.wav', path.name)]

    def prune(self):
        files = sorted(self.files(), key=lambda path: path.stat().st_mtime)
        total = sum(path.stat().st_size for path in files)
        for path in files:
            if total <= self.limit:
                break
            size = path.stat().st_size
            path.unlink()
            total -= size

    def status(self):
        files = self.files()
        sizes = []
        for path in files:
            try:
                sizes.append(path.stat().st_size)
            except FileNotFoundError:
                pass
        return {'count': len(sizes), 'bytes': sum(sizes), 'limit_mb': self.limit // 1048576}

    def clear(self):
        # Only this app's flat, known section files are removed.
        for path in self.files():
            path.unlink()
        return self.status()
