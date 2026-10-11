from __future__ import annotations

import shutil
import threading
from pathlib import Path

from .documents import prepare
from .jobs import public_job
from .performance import validate


class Bridge:
    def __init__(self, store, models, jobs):
        self._store, self._models, self._jobs = store, models, jobs
        self._window = None
        self._lock = threading.RLock()

    def get_state(self):
        documents = [{"id": doc["id"], "title": doc["title"], "created": doc["created"],
                      "opened": doc.get("opened"), "source": doc.get("source"),
                      "words": len(doc["markdown"].split())} for doc in self._store.all("documents")]
        documents.sort(key=lambda doc: doc['opened'] or doc['created'], reverse=True)
        readings = sorted(self._store.all('jobs'), key=lambda job: job.get('created', 0), reverse=True)
        return {"documents": documents, "jobs": [public_job(job) for job in readings],
                "active": self._jobs.state(), "model": self._models.status(), "settings": self._store.settings(),
                "storage": str(self._store.root), "performance": self._jobs.performance_state(),
                "cache": self._jobs.cache_state()}

    def get_stream(self, key):
        return self._jobs.stream(key)

    def start_benchmark(self):
        return self._jobs.benchmark()

    def stop_benchmark(self):
        return self._jobs.stop_benchmark()

    def warm_engine(self):
        return self._jobs.warmup()

    def clear_cache(self):
        return self._jobs.clear_cache()

    def get_document(self, key):
        with self._lock:
            return self._store.open_document(key)

    def save_document(self, key, markdown):
        with self._lock:
            prepared = prepare(markdown, self._store.settings())
            return self._store.document(markdown, prepared["title"], key=key)

    def new_document(self):
        return self._store.document("# Untitled reading\n\nPut your words here.\n", "Untitled reading")

    def remove_document(self, key):
        with self._lock:
            self._store.get("documents", key)
            self._store.remove("documents", key)
        return True

    def remove_recording(self, key, delete_audio=False):
        with self._lock, self._jobs.lock:
            active = self._jobs.state()
            if active and active["id"] == key:
                raise ValueError("Stop this reading before removing it.")
            self._store.get("jobs", key)
            directory = (self._store.root / "jobs" / key).resolve()
            if directory.parent != (self._store.root / "jobs").resolve():
                raise ValueError("Invalid recording location.")
            if delete_audio and directory.is_dir():
                shutil.rmtree(directory)
            self._store.remove("jobs", key)
        return True

    def import_document(self):
        import webview
        paths = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=False,
                                                file_types=("Markdown files (*.md;*.markdown)",))
        if not paths:
            return None
        path = Path(paths[0])
        if path.suffix.lower() not in {".md", ".markdown"}:
            raise ValueError("Choose a Markdown (.md or .markdown) file.")
        try:
            markdown = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            raise ValueError("This file is not UTF-8. Save it as UTF-8 and try again.") from None
        prepared = prepare(markdown, self._store.settings(), path.stem)
        return self._store.document(markdown, prepared["title"], source=str(path))

    def prepare_document(self, markdown, options):
        return prepare(markdown, options)

    def save_settings(self, settings):
        with self._lock:
            validate(settings)
            settings = {key: value for key, value in settings.items() if key != 'benchmark_result'}
            if "theme" in settings and settings["theme"] not in {"light", "dark", "system"}:
                raise ValueError("Unknown appearance setting.")
            if "palette" in settings and settings["palette"] not in {"lilt", "classic"}:
                raise ValueError("Unknown theme palette.")
            if "speed" in settings and not 0.5 <= float(settings["speed"]) <= 2:
                raise ValueError("Choose a speed between 0.5× and 2×.")
            return self._store.save_settings(settings)

    def generate(self, key, markdown, settings):
        with self._lock:
            self.save_settings(settings)
            prepared = prepare(markdown, settings)
            document = self._store.document(markdown, prepared["title"], key=key)
            return self._jobs.start(prepared, document, settings["voice"], settings["speed"])

    def preview_voice(self, voice, speed, sample="Every good reading begins with a little curiosity. This is Lilt: your words, out loud."):
        document = {"id": "preview", "title": "A little voice preview", "markdown": sample[:350]}
        return self._jobs.start(prepare(document["markdown"]), document, voice, speed, preview=True)

    def cancel_generation(self):
        return self._jobs.stop()

    def resume_job(self, key):
        job = self._store.get("jobs", key)
        document = {"id": job["document_id"], "title": job["title"], "markdown": job["markdown"]}
        return self._jobs.start(prepare(job["markdown"], job["options"]), document, job["voice"], job["speed"], resume=key)

    def save_position(self, key, position):
        return self._jobs.save_position(key, position)

    def export_recording(self, key):
        import webview
        job = self._store.get("jobs", key)
        if job["state"] != "completed":
            raise ValueError("Finish this recording before exporting it.")
        import re
        filename = re.sub(r'[<>:"/\\|?*]', "", job["title"]).strip()[:100] or "Lilt recording"
        path = self._window.create_file_dialog(webview.FileDialog.SAVE, save_filename=filename + ".wav",
                                               file_types=("WAV audio (*.wav)",))
        if not path:
            return None
        target = Path(path if isinstance(path, str) else path[0])
        if target.suffix.lower() != ".wav":
            target = target.with_suffix(".wav")
        source = self._store.root / "jobs" / key / "recording.wav"
        if target.resolve() == source.resolve():
            return str(target)
        if target.exists() and not self._window.create_confirmation_dialog("Replace recording?", f"Replace {target.name}?"):
            return None
        shutil.copyfile(source, target)
        return str(target)

    def setup_model(self):
        return self._models.download()

    def import_model(self):
        import webview
        if self._jobs.state() or getattr(self._jobs, 'operation', None):
            raise ValueError("Finish the current reading before changing model files.")
        paths = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        return self._models.import_directory(paths[0]) if paths else None
