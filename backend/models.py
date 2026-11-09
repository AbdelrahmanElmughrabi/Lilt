from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import urllib.request
from pathlib import Path

from .model_trust import APPROVED, DOWNLOAD_ROOT, RELEASE, verify_file
FILES = ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin")
GPU_FILE = "kokoro-v1.0.fp16-gpu.onnx"


class Models:
    def __init__(self, root: Path, bundled: Path | None = None):
        self.install_root = root
        self.root = bundled if bundled and all((bundled / name).is_file() for name in FILES) else root
        self.lock = threading.RLock()
        self.progress = {"state": "missing", "percent": 0, "message": "Download the local voice engine to get started."}
        self.voices = []
        self.gpu_verified = False
        self.gpu_error = ''
        try:
            self._recover()
            self._refresh()
        except (OSError, ValueError) as error:
            self.progress = {'state': 'error', 'percent': 0, 'message': str(error)}

    def _refresh(self):
        self.voices = []
        self.gpu_verified = False
        self.gpu_error = ''
        if all((self.root / name).is_file() for name in FILES):
            try:
                for name in FILES:
                    verify_file(self.root / name)
                import numpy as np
                with np.load(self.root / FILES[1], allow_pickle=False) as voices:
                    self.voices = [voice for voice in sorted(voices.keys()) if voice.startswith(("af_", "am_", "bf_", "bm_"))]
                if not self.voices:
                    raise ValueError("The model files are incomplete.")
                if (self.root / GPU_FILE).is_file():
                    try:
                        verify_file(self.root / GPU_FILE)
                        self.gpu_verified = True
                    except (OSError, ValueError) as error:
                        self.gpu_error = str(error)
                self.progress = {"state": "ready", "percent": 100, "message": "Ready for local generation."}
            except Exception as error:
                self.progress = {"state": "error", "percent": 0, "message": str(error)}

    def status(self):
        with self.lock:
            return self.progress.copy() | {"voices": self.voices.copy(), 'gpu_error': self.gpu_error,
                                           'download_bytes': sum(APPROVED[name][0] for name in FILES)}

    def download(self):
        with self.lock:
            if self.progress["state"] in {"ready", "downloading"}:
                return self.status()
            self.progress = {"state": "downloading", "percent": 0, "message": "Connecting to the model repository…"}
        threading.Thread(target=self._download, daemon=True).start()
        return self.status()

    def _open(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": "Violilt-Desktop/0.1"})
        return urllib.request.urlopen(request, timeout=45)

    def _download(self):
        try:
            self.install_root.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.model-stage-', dir=self.install_root) as directory:
                staging = Path(directory)
                total = sum(APPROVED[name][0] for name in FILES)
                downloaded = 0
                for name in FILES:
                    size = 0
                    with self._open(DOWNLOAD_ROOT + name) as response, (staging / name).open('wb') as output:
                        while block := response.read(1024 * 1024):
                            size += len(block)
                            if size > APPROVED[name][0]:
                                raise ValueError('The model download exceeds its approved size.')
                            output.write(block)
                            downloaded += len(block)
                            with self.lock:
                                self.progress = {'state': 'downloading', 'percent': round(downloaded * 100 / total),
                                                 'message': f'Downloading voice engine · {downloaded // 1_000_000} / {total // 1_000_000} MB'}
                    verify_file(staging / name)
                with self.lock:
                    self._activate(staging, list(FILES))
            with self.lock:
                self.root = self.install_root
                self._refresh()
        except Exception as error:
            with self.lock:
                self.progress = {"state": "error", "percent": 0, "message": f"Couldn't download the model: {error}"}

    def import_directory(self, directory):
        with self.lock:
            if self.progress["state"] == "downloading":
                raise ValueError("Wait for the current download to finish.")
            source = Path(directory)
            for name in FILES:
                if not (source / name).is_file():
                    raise ValueError(f"The selected folder needs {name}.")
            names = list(FILES) + ([GPU_FILE] if (source / GPU_FILE).is_file() else [])
            self.install_root.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.model-stage-', dir=self.install_root) as directory:
                staging = Path(directory)
                for name in names:
                    verify_file(source / name)
                    shutil.copyfile(source / name, staging / name)
                    verify_file(staging / name)
                self._activate(staging, names)
            self.root = self.install_root
            self._refresh()
            return self.status()

    def _journal(self, directory, record):
        temporary = directory / 'state.part'
        with temporary.open('w', encoding='utf-8') as output:
            json.dump(record, output)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(directory / 'state.json')

    def _recover(self):
        transaction = self.install_root / '.model-rollback'
        if not transaction.exists():
            return
        journal = transaction / 'state.json'
        if not journal.is_file():
            # No destination is changed until the durable journal is written.
            shutil.rmtree(transaction)
            return
        record = json.loads(journal.read_text(encoding='utf-8'))
        if not isinstance(record, dict):
            raise ValueError('The interrupted model change needs recovery. Its backup files have been kept.')
        names, previous = record.get('names'), record.get('previous')
        if (not isinstance(names, list) or not isinstance(previous, list) or not names
                or any(not isinstance(name, str) or name not in APPROVED for name in names) or len(set(names)) != len(names)
                or any(name not in names for name in previous) or record.get('state') not in {'pending', 'committed'}):
            raise ValueError('The interrupted model change needs recovery. Its backup files have been kept.')
        if record['state'] == 'pending':
            # Copy rather than move backups: retrying after another interruption
            # restores the same complete previous set.
            for name in names:
                target = self.install_root / name
                if name in previous:
                    temporary = transaction / (name + '.restore')
                    shutil.copyfile(transaction / name, temporary)
                    temporary.replace(target)
                else:
                    target.unlink(missing_ok=True)
        shutil.rmtree(transaction)

    @staticmethod
    def _sync(path):
        with path.open('ab') as output:
            output.flush()
            os.fsync(output.fileno())

    def _activate(self, staging, names):
        self._recover()
        for name in names:
            verify_file(staging / name)
            self._sync(staging / name)
        transaction = self.install_root / '.model-rollback'
        transaction.mkdir()
        previous = [name for name in names if (self.install_root / name).is_file()]
        record = {'names': names, 'previous': previous, 'state': 'pending'}
        try:
            for name in previous:
                shutil.copyfile(self.install_root / name, transaction / name)
                self._sync(transaction / name)
            self._journal(transaction, record)
            for name in names:
                (staging / name).replace(self.install_root / name)
            self._journal(transaction, record | {'state': 'committed'})
        except Exception:
            self._recover()
            raise
        self._recover()
