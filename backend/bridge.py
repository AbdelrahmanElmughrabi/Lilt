from __future__ import annotations

import codecs
import logging
import shutil
import os
import subprocess
import sys
import threading
import tempfile
from pathlib import Path

from .pcm_audio import copy_pcm, open_pcm

from .documents import plain_text_markdown, prepare
from .jobs import public_job
from .limits import MAX_FILE_BATCH, MAX_MARKDOWN_BYTES
from .pdf_import import MAX_PDF_BYTES, extract_pdf_text
from .settings import validate_settings
from .windows_shell import select_file

DOCUMENT_SUFFIXES = {'.md', '.markdown', '.txt', '.pdf'}


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
        pending = getattr(self._jobs, 'pending_storage', lambda: {})()
        recovery = self._store.recovery_summary()
        if isinstance(pending, dict) and pending.get('message'):
            recovery = {'count': recovery['count'] + 1,
                        'message': ' '.join(filter(None, (recovery['message'], pending['message'])))}
            if isinstance(pending.get('job'), dict):
                latest = pending['job']
                if latest['state'] == 'completed':
                    latest = latest | {'state': 'assembling', 'message': pending['message']}
                readings = [latest] + [job for job in readings if job['id'] != latest['id']]
        return {"documents": documents, "jobs": [public_job(job) for job in readings],
                "active": self._jobs.state(), "model": self._models.status(), "settings": self._store.settings(),
                "storage": str(self._store.root), "performance": self._jobs.performance_state(),
                "cache": self._jobs.cache_state(), "recovery": recovery}

    def get_stream(self, key):
        return self._jobs.stream(key)

    def start_benchmark(self):
        return self._jobs.benchmark()

    def stop_benchmark(self):
        return self._jobs.stop_benchmark()

    def warm_engine(self):
        return self._jobs.warmup()

    def release_engine(self):
        return self._jobs.release_engine()

    def clear_cache(self):
        return self._jobs.clear_cache()

    def get_document(self, key):
        with self._lock:
            return self._store.open_document(key)

    def save_document(self, key, markdown):
        with self._lock:
            title = self._store.get('documents', key)['title']
            prepared = prepare(markdown, self._store.settings(), fallback_title=title)
            return self._store.document(markdown, prepared["title"], key=key)

    def new_document(self):
        return self._store.document("# Untitled reading\n\nPut your words here.\n", "Untitled reading")

    def remove_document(self, key):
        with self._lock:
            self._store.get("documents", key)
            self._store.remove("documents", key)
        return True

    def reveal_document(self, key):
        document = self._store.get('documents', key)
        source = document.get('source')
        if not source:
            raise ValueError('This reading has no original file.')
        path = Path(source)
        if not path.is_absolute() or path.suffix.lower() not in DOCUMENT_SUFFIXES or not path.is_file():
            raise ValueError('The original file could not be found. It may have been moved or deleted.')
        return self._reveal_path(path, select=True)

    def reveal_recording(self, key):
        job = self._store.get('jobs', key)
        root = (self._store.root / 'jobs').resolve()
        directory = (root / key).resolve()
        if directory.parent != root:
            raise ValueError('Invalid recording location.')
        audio = directory / 'recording.wav'
        if job.get('state') == 'completed':
            if not audio.is_file() or audio.resolve().parent != directory:
                raise ValueError('The saved recording file could not be found.')
            return self._reveal_path(audio, select=True)
        if not directory.is_dir():
            raise ValueError('This reading has no output folder yet.')
        return self._reveal_path(directory, select=False)

    def _reveal_path(self, path, select):
        if sys.platform != 'win32':
            raise ValueError('Show in File Explorer is available on Windows.')
        explorer = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'explorer.exe'
        try:
            if select:
                select_file(path)
            else:
                subprocess.Popen(f'"{explorer}" "{path}"', shell=False)
        except OSError as exc:
            raise ValueError('File Explorer could not be opened. Try again.') from exc
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
                                                file_types=("Documents (*.md;*.markdown;*.txt;*.pdf)",))
        if not paths:
            return None
        return self._import_document_path(paths[0])

    def import_dropped_documents(self, paths):
        if not isinstance(paths, list) or not paths:
            raise ValueError('Drop a Markdown, TXT or PDF (.md, .markdown, .txt or .pdf) file to add a reading.')
        if len(paths) > MAX_FILE_BATCH:
            raise ValueError(f'Add up to {MAX_FILE_BATCH} files at a time.')
        documents, errors = [], []
        seen = set()
        for source in paths:
            try:
                path = Path(source).resolve()
                identity = os.path.normcase(str(path))
                if identity in seen:
                    continue
                seen.add(identity)
                documents.append(self._import_document_path(path))
            except (OSError, ValueError, TypeError) as exc:
                errors.append({'name': Path(source).name if isinstance(source, str) else 'File',
                               'message': str(exc)})
        return {'documents': documents, 'errors': errors}

    def _import_document_path(self, source):
        path = Path(source).resolve()
        if path.suffix.lower() not in DOCUMENT_SUFFIXES:
            raise ValueError('Choose a Markdown, TXT or PDF (.md, .markdown, .txt or .pdf) file.')
        if not path.is_file():
            raise ValueError('This file could not be found. Drop a file rather than a folder.')
        plain = path.suffix.lower() == '.txt'
        pdf = path.suffix.lower() == '.pdf'
        encoding_error = ('This TXT file must use UTF-8 or UTF-16 with a BOM. Save it as UTF-8 and try again.'
                          if plain else 'This file is not UTF-8. Save it as UTF-8 and try again.')
        try:
            with path.open('rb') as source_file:
                body = source_file.read((MAX_PDF_BYTES if pdf else MAX_MARKDOWN_BYTES) + 1)
            if pdf:
                markdown = plain_text_markdown(extract_pdf_text(body), 'PDF')
            elif len(body) > MAX_MARKDOWN_BYTES:
                raise ValueError('Choose a file up to 2 MB. Split larger files into smaller readings.')
            elif plain:
                if body.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
                    raise ValueError(encoding_error)
                encoding = 'utf-16' if body.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)) else 'utf-8-sig'
                text = body.decode(encoding)
                if '\x00' in text:
                    raise ValueError(encoding_error)
                markdown = plain_text_markdown(text)
            else:
                markdown = body.decode('utf-8-sig')
        except UnicodeDecodeError:
            raise ValueError(encoding_error) from None
        except OSError:
            raise ValueError('This file could not be read. Check that it is available and try again.') from None
        prepared = prepare(markdown, self._store.settings(), path.stem)
        with self._lock:
            return self._store.document(markdown, prepared["title"], source=str(path))

    def prepare_document(self, markdown, options):
        return prepare(markdown, options)

    def save_settings(self, settings):
        with self._lock:
            if not isinstance(settings, dict):
                raise ValueError('Settings must be an object.')
            settings = {key: value for key, value in settings.items() if key != 'benchmark_result'}
            voices = None
            if self._models is not None:
                model = self._models.status()
                if isinstance(model, dict) and model.get('state') == 'ready':
                    voices = model['voices']
            return self._store.save_settings(validate_settings(settings, voices=voices))

    def generate(self, key, markdown, settings):
        with self._lock:
            self.save_settings(settings)
            title = self._store.get('documents', key)['title']
            prepared = prepare(markdown, settings, fallback_title=title)
            document = self._store.document(markdown, prepared["title"], key=key)
            return self._jobs.start(prepared, document, settings["voice"], settings["speed"])

    def preview_voice(self, voice, speed, sample="Every good reading begins with a little curiosity. This is Violilt: your words, out loud."):
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
        filename = re.sub(r'[<>:"/\\|?*]', "", job["title"]).strip()[:100] or "Violilt recording"
        path = self._window.create_file_dialog(webview.FileDialog.SAVE, save_filename=filename + ".wav",
                                               file_types=("WAV audio (*.wav)",))
        if not path:
            return None
        target = Path(path if isinstance(path, str) else path[0])
        if target.suffix.lower() != ".wav":
            target = target.with_suffix(".wav")
        source = self._store.root / "jobs" / key / "recording.wav"
        if target.resolve() == source.resolve():
            with open_pcm(source):
                pass
            return str(target)
        if target.exists() and not self._window.create_confirmation_dialog("Replace recording?", f"Replace {target.name}?"):
            return None
        descriptor, name = tempfile.mkstemp(prefix='.violilt-export-', suffix='.part', dir=target.parent)
        temporary = Path(name)
        os.close(descriptor)
        try:
            copy_pcm(source, temporary)
            with temporary.open('rb+') as copied:
                os.fsync(copied.fileno())
            temporary.replace(target)
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logging.exception('Could not remove an incomplete export temporary file')
        return str(target)

    def setup_model(self):
        with self._jobs.lock:
            if self._jobs.state() or getattr(self._jobs, 'operation', None):
                raise ValueError('Finish the current reading or engine preparation before changing model files.')
            self._jobs.release_engine()
            return self._models.download()

    def import_model(self):
        import webview
        if self._jobs.state() or getattr(self._jobs, 'operation', None):
            raise ValueError("Finish the current reading before changing model files.")
        paths = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if not paths:
            return None
        with self._jobs.lock:
            if self._jobs.state() or getattr(self._jobs, 'operation', None):
                raise ValueError('Finish the current reading or engine preparation before changing model files.')
            self._jobs.release_engine()
            return self._models.import_directory(paths[0])
