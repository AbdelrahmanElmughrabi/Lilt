"""Bounded cache of immutable raw speech sections; recordings are separate."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path

from .pcm_audio import audio_info, copy_pcm


def section_key(text, voice, speed, identity):
    return hashlib.sha256(json.dumps([text, voice, float(speed), identity], ensure_ascii=False).encode()).hexdigest()


class SectionCache:
    def __init__(self, root: Path, limit_mb=256):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.limit = int(limit_mb) * 1024 * 1024

    @staticmethod
    def read_warnings(audio):
        try:
            value = json.loads(Path(audio).with_suffix('.pronunciation.json').read_text(encoding='utf-8'))
            return value if isinstance(value, list) and all(isinstance(item, str) for item in value) else []
        except (OSError, ValueError):
            return []

    @staticmethod
    def write_warnings(audio, warnings):
        destination = Path(audio).with_suffix('.pronunciation.json')
        if not warnings:
            destination.unlink(missing_ok=True)
            return
        temporary = destination.with_suffix('.part')
        temporary.write_text(json.dumps(warnings, ensure_ascii=False), encoding='utf-8')
        temporary.replace(destination)

    def fetch(self, key, destination):
        path = self.root / (key + '.wav')
        if not path.is_file():
            return False
        descriptor, name = tempfile.mkstemp(prefix='.violilt-cache-', suffix='.part', dir=destination.parent)
        os.close(descriptor)
        temporary = Path(name)
        try:
            copy_pcm(path, temporary)
            self.write_warnings(destination, self.read_warnings(path))
            temporary.replace(destination)
            os.utime(path, None)
            return True
        except (FileNotFoundError, ValueError):
            return False
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logging.warning('Could not remove an incomplete cached audio copy')

    def put(self, key, source):
        destination = self.root / (key + '.wav')
        if not destination.exists() or audio_info(destination) is None:
            descriptor, name = tempfile.mkstemp(prefix='.violilt-cache-', suffix='.part', dir=destination.parent)
            os.close(descriptor)
            temporary = Path(name)
            try:
                copy_pcm(source, temporary)
                self.write_warnings(destination, self.read_warnings(source))
                temporary.replace(destination)
            finally:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    logging.warning('Could not remove an incomplete reusable audio copy')
        else:
            self.write_warnings(destination, self.read_warnings(source))
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
            path.with_suffix('.pronunciation.json').unlink(missing_ok=True)
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
            path.with_suffix('.pronunciation.json').unlink(missing_ok=True)
        return self.status()
