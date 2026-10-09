from __future__ import annotations

import hashlib
import json
import shutil
import threading
import urllib.request
from pathlib import Path

RELEASE = "https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.0"
FILES = ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin")
GPU_FILE = "kokoro-v1.0.fp16-gpu.onnx"


class Models:
    def __init__(self, root: Path, bundled: Path | None = None):
        self.install_root = root
        self.root = bundled if bundled and all((bundled / name).is_file() for name in FILES) else root
        self.lock = threading.RLock()
        self.progress = {"state": "missing", "percent": 0, "message": "Download the local voice engine to get started."}
        self.voices = []
        self._refresh()

    def _refresh(self):
        if all((self.root / name).is_file() for name in FILES):
            try:
                import numpy as np
                with np.load(self.root / FILES[1], allow_pickle=False) as voices:
                    self.voices = [voice for voice in sorted(voices.keys()) if voice.startswith(("af_", "am_", "bf_", "bm_"))]
                if not self.voices or (self.root / FILES[0]).stat().st_size < 1_000_000:
                    raise ValueError("The model files are incomplete.")
                self.progress = {"state": "ready", "percent": 100, "message": "Ready for local generation."}
            except Exception as error:
                self.progress = {"state": "error", "percent": 0, "message": str(error)}

    def status(self):
        with self.lock:
            return self.progress.copy() | {"voices": self.voices.copy()}

    def download(self):
        with self.lock:
            if self.progress["state"] in {"ready", "downloading"}:
                return self.status()
            self.progress = {"state": "downloading", "percent": 0, "message": "Connecting to the model repository…"}
        threading.Thread(target=self._download, daemon=True).start()
        return self.status()

    def _open(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": "Lilt-Desktop/0.1"})
        return urllib.request.urlopen(request, timeout=45)

    def _download(self):
        try:
            with self._open(RELEASE) as response:
                assets = {item["name"]: item for item in json.load(response)["assets"]}
            total = sum(assets[name]["size"] for name in FILES)
            downloaded = 0
            for name in FILES:
                asset = assets[name]
                path = self.install_root / name
                temporary = path.with_suffix(path.suffix + ".download")
                digest = hashlib.sha256()
                with self._open(asset["browser_download_url"]) as response, temporary.open("wb") as output:
                    while block := response.read(1024 * 1024):
                        output.write(block)
                        digest.update(block)
                        downloaded += len(block)
                        with self.lock:
                            self.progress = {"state": "downloading", "percent": round(downloaded * 100 / total),
                                             "message": f"Downloading voice engine · {downloaded // 1_000_000} / {total // 1_000_000} MB"}
                if temporary.stat().st_size != asset["size"]:
                    raise ValueError("The download was incomplete. Please retry.")
                expected = asset.get("digest")
                if expected and expected != f"sha256:{digest.hexdigest()}":
                    raise ValueError("The model download failed its integrity check. Please retry.")
                temporary.replace(path)
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
            for name in FILES:
                target = self.install_root / name
                if source.resolve() != self.install_root.resolve():
                    temporary = target.with_suffix(target.suffix + ".import")
                    shutil.copyfile(source / name, temporary)
                    temporary.replace(target)
            self.root = self.install_root
            self._refresh()
            return self.status()
