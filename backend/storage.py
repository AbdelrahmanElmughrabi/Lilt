from __future__ import annotations

import json
import hashlib
import math
import os
import shutil
import sqlite3
import stat
import tempfile
import time
import uuid
from contextlib import closing, contextmanager
from pathlib import Path

from .settings import defaults as default_settings, validate_settings

SCHEMA_VERSION = 1
LIBRARY_FOLDERS = {'jobs', 'models', 'previews', 'section-cache', 'backups'}
LIBRARY_FILES = {'migration.json'}
MAX_LIBRARY_IMPORT_BYTES = 100 * 1024 ** 3
MAX_LIBRARY_IMPORT_FILES = 100_000


class UnsupportedLibraryVersion(ValueError):
    pass


ISOLATED_DATA_PROFILES = {
    "Violilt-Pronunciation-Evaluation": "VIOLILT_EVALUATION_DATA_DIR",
    "Violilt-MSIX-Compatibility": "VIOLILT_MSIX_TEST_DATA_DIR",
}


def data_directory(profile=None):
    if profile:
        if profile not in ISOLATED_DATA_PROFILES:
            raise ValueError("Unknown app data profile.")
        override = os.environ.get(ISOLATED_DATA_PROFILES[profile])
        if override:
            return Path(override).resolve()
        parent = Path(os.environ["LOCALAPPDATA"]) if os.environ.get("LOCALAPPDATA") else Path.home()
        return parent / profile
    override = os.environ.get("VIOLILT_DATA_DIR")
    if override:
        return Path(override).resolve()
    parent = Path(os.environ["LOCALAPPDATA"]) if os.environ.get("LOCALAPPDATA") else Path.home()
    root = parent / "Violilt"
    previous = os.environ.get("VIOLILT_IMPORT_DATA_DIR")
    if (root / "library.sqlite3").is_file() or not previous:
        return root
    return import_library(Path(previous), root)


def import_library(previous: Path, destination: Path):
    """Copy an explicitly selected library without modifying its original files."""
    if previous.exists() and _reparse(previous):
        raise ValueError('Choose the original library folder rather than a link or junction.')
    legacy, root = previous.resolve(), destination.resolve()
    if legacy == root or legacy.is_relative_to(root) or root.is_relative_to(legacy):
        raise ValueError("Source and destination libraries must be separate folders.")
    if not (legacy / "library.sqlite3").is_file():
        raise ValueError("The selected source folder does not contain a library.")
    if root.exists():
        raise FileExistsError("The Violilt data folder already exists. Choose an unused folder before importing your existing library.")
    from .instance import library_lock
    with library_lock(legacy):
        return _import_library_locked(legacy, root)


def _reparse(path):
    value = path.lstat()
    return stat.S_ISLNK(value.st_mode) or bool(getattr(value, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def _library_snapshot(legacy):
    snapshot = {}
    total = 0
    entries = 0

    def visit(path):
        nonlocal total, entries
        entries += 1
        if entries > MAX_LIBRARY_IMPORT_FILES:
            raise ValueError('This library has too many files to import in one operation.')
        if _reparse(path) or not path.resolve().is_relative_to(legacy):
            raise ValueError('The selected library contains a link or junction. Import a library containing ordinary files and folders.')
        value = path.stat()
        relative = path.relative_to(legacy).as_posix()
        if len(path.relative_to(legacy).parts) > 64:
            raise ValueError('This library contains folders nested too deeply to import.')
        snapshot[relative] = (value.st_size, value.st_mtime_ns, value.st_ctime_ns, value.st_ino)
        if path.is_dir():
            for child in path.iterdir():
                visit(child)
        elif path.is_file():
            total += value.st_size
            if total > MAX_LIBRARY_IMPORT_BYTES:
                raise ValueError('This library exceeds the 100 GB import limit.')
        else:
            raise ValueError('The selected library contains an unsupported file.')

    for path in legacy.iterdir():
        if _reparse(path):
            raise ValueError('The selected library contains a link or junction. Import a library containing ordinary files and folders.')
        if (path.name in LIBRARY_FOLDERS | LIBRARY_FILES
                or path.name in {'library.sqlite3', 'library.sqlite3-wal', 'library.sqlite3-shm', 'library.sqlite3-journal'}):
            visit(path)
    return snapshot, total


def _import_library_locked(legacy, root):
    before, total = _library_snapshot(legacy)
    root.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root.parent).free < total + 64 * 1024 ** 2:
        raise ValueError('There is not enough free space to import this library. Free some space and try again.')
    staging = Path(tempfile.mkdtemp(prefix=".violilt-migration-", dir=root.parent))
    try:
        # Stage a complete copy; the original remains available as a backup.
        # WebView's expendable browser cache may contain locked files.
        for source in legacy.iterdir():
            if source.name not in LIBRARY_FOLDERS | LIBRARY_FILES:
                continue
            target = staging / source.name
            def checked_copy(path, destination):
                path = Path(path)
                if _reparse(path) or not path.resolve().is_relative_to(legacy):
                    raise ValueError('The selected library changed or contains a link or junction.')
                expected = before.get(path.relative_to(legacy).as_posix())
                if expected is None:
                    raise ValueError('The source library changed during import. Close its app and retry.')
                remaining = expected[0]
                with path.open('rb') as source_file, Path(destination).open('xb') as target_file:
                    while block := source_file.read(min(1024 * 1024, remaining + 1)):
                        remaining -= len(block)
                        if remaining < 0:
                            raise ValueError('The source library changed during import. Close its app and retry.')
                        target_file.write(block)
                if remaining:
                    raise ValueError('The source library changed during import. Close its app and retry.')
                shutil.copystat(path, destination)
                return str(destination)

            def checked_directory(path, names):
                for name in names:
                    child = Path(path) / name
                    if _reparse(child) or not child.resolve().is_relative_to(legacy):
                        raise ValueError('The selected library changed or contains a link or junction.')
                return []

            if source.is_dir():
                shutil.copytree(source, target, copy_function=checked_copy, ignore=checked_directory)
            else:
                checked_copy(source, target)
        with closing(sqlite3.connect(f"{(legacy / 'library.sqlite3').as_uri()}?mode=ro", uri=True)) as source_db:
            if source_db.execute('PRAGMA user_version').fetchone()[0] > SCHEMA_VERSION:
                raise UnsupportedLibraryVersion('This library was saved by a newer Violilt version. Its files have been kept.')
            with closing(sqlite3.connect(staging / "library.sqlite3")) as target_db:
                source_db.backup(target_db)
                if target_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("The existing library could not be migrated safely.")
                palette = target_db.execute("SELECT value FROM settings WHERE key = 'palette'").fetchone()
                try:
                    old_palette = json.loads(palette[0]) if palette else None
                except (ValueError, TypeError):
                    old_palette = None
                if palette and old_palette not in ('violilt', 'classic'):
                    target_db.execute("UPDATE settings SET value = ? WHERE key = 'palette'", (json.dumps('violilt'),))
                    target_db.commit()
        after, _ = _library_snapshot(legacy)
        if before != after:
            raise ValueError('The source library changed during import. Close its app and retry. The original library has been kept.')
        (staging / "migration.json").write_text(json.dumps({"from": str(legacy), "completed": time.time()}), encoding="utf-8")
        staging.rename(root)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return root


class Store:
    def __init__(self, root: Path):
        self.root = root
        for folder in (root, root / "jobs", root / "models", root / "previews"):
            folder.mkdir(parents=True, exist_ok=True)
        self.db = root / "library.sqlite3"
        with self.connect() as connection:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            if version > SCHEMA_VERSION:
                raise UnsupportedLibraryVersion('This library was saved by a newer Violilt version. Open it with that version; its files have been kept.')
            if version < SCHEMA_VERSION:
                existing = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
                if existing:
                    # Back up before starting the migration transaction, including
                    # committed WAL contents. Never overwrite an earlier backup.
                    self._backup(connection, f'before-v{SCHEMA_VERSION}')
                connection.execute('BEGIN IMMEDIATE')
                for statement in (
                    'CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, body TEXT NOT NULL, updated REAL NOT NULL)',
                    'CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, body TEXT NOT NULL, updated REAL NOT NULL)',
                    'CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)',
                    'CREATE TABLE IF NOT EXISTS recovery_rows (fingerprint TEXT PRIMARY KEY, collection TEXT NOT NULL, item_key TEXT NOT NULL, body BLOB NOT NULL, reason TEXT NOT NULL, saved REAL NOT NULL)',
                ):
                    connection.execute(statement)
                connection.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')

    def _backup(self, connection, label):
        folder = self.root / 'backups'
        folder.mkdir(exist_ok=True)
        target = folder / f'library-{label}-{uuid.uuid4().hex}.sqlite3'
        try:
            with closing(sqlite3.connect(target)) as destination:
                connection.backup(destination)
                if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('The library backup could not be verified. The upgrade was not applied.')
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target

    def backup(self):
        with self.connect() as connection:
            return self._backup(connection, 'snapshot')

    def _quarantine(self, collection, key, body, reason):
        raw = body if isinstance(body, bytes) else str(body).encode('utf-8')
        fingerprint = hashlib.sha256(collection.encode() + b'\0' + str(key).encode() + b'\0' + raw).hexdigest()
        with self.connect() as connection:
            connection.execute('INSERT OR IGNORE INTO recovery_rows VALUES (?, ?, ?, ?, ?, ?)',
                               (fingerprint, collection, str(key), body, reason, time.time()))

    def recovery_summary(self):
        with self.connect() as connection:
            count = connection.execute('SELECT COUNT(*) FROM recovery_rows').fetchone()[0]
        return {'count': count, 'message': ('Some saved items could not be loaded. Their original data is kept for recovery. '
                'Back up your library and contact support before attempting a repair.') if count else ''}

    def _decode_record(self, table, key, body):
        try:
            item = json.loads(body)
            if not isinstance(item, dict) or item.get('id') != key:
                raise ValueError('Invalid saved item identity.')
            if table == 'documents':
                if (not isinstance(item.get('title'), str) or not isinstance(item.get('markdown'), str)
                        or isinstance(item.get('created'), bool) or not isinstance(item.get('created'), (int, float))
                        or not math.isfinite(item['created'])):
                    raise ValueError('Invalid saved reading.')
            elif not isinstance(item.get('state'), str):
                raise ValueError('Invalid saved recording.')
            return item
        except (ValueError, TypeError, UnicodeError, RecursionError) as error:
            self._quarantine(table, key, body, 'The saved item has invalid JSON or fields.')
            raise ValueError('This saved item needs recovery. Its original data has been kept.') from error

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db, timeout=15)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def put(self, table, item):
        if table not in {"documents", "jobs"}:
            raise ValueError("Invalid collection")
        with self.connect() as connection:
            connection.execute(f"INSERT OR REPLACE INTO {table} VALUES (?, ?, ?)",
                               (item["id"], json.dumps(item, ensure_ascii=False), time.time()))
        return item

    def get(self, table, key):
        if table not in {"documents", "jobs"}:
            raise ValueError("Invalid collection")
        with self.connect() as connection:
            row = connection.execute(f"SELECT body FROM {table} WHERE id = ?", (key,)).fetchone()
        if not row:
            raise ValueError("This item is no longer in your library.")
        return self._decode_record(table, key, row[0])

    def all(self, table):
        if table not in {"documents", "jobs"}:
            raise ValueError("Invalid collection")
        with self.connect() as connection:
            rows = connection.execute(f"SELECT id, body FROM {table} ORDER BY updated DESC").fetchall()
        items = []
        for key, body in rows:
            try:
                items.append(self._decode_record(table, key, body))
            except ValueError:
                continue
        return items

    def remove(self, table, key):
        if table not in {"documents", "jobs"}:
            raise ValueError("Invalid collection")
        with self.connect() as connection:
            connection.execute(f"DELETE FROM {table} WHERE id = ?", (key,))

    def settings(self):
        defaults = default_settings()
        with self.connect() as connection:
            rows = connection.execute('SELECT key, value FROM settings').fetchall()
        for key, raw in rows:
            try:
                value = json.loads(raw)
                defaults.update(validate_settings({key: value}, internal=True))
            except (ValueError, TypeError, UnicodeError, RecursionError):
                self._quarantine('settings', key, raw, 'The saved preference has invalid JSON or fields.')
        return defaults

    def save_settings(self, settings):
        settings = validate_settings(settings, internal=True)
        with self.connect() as connection:
            for key, value in settings.items():
                connection.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, json.dumps(value, allow_nan=False)))
        return self.settings()

    def document(self, markdown, title, source=None, key=None):
        from .limits import markdown_text
        markdown_text(markdown)
        old = self.get("documents", key) if key else {}
        now = time.time()
        return self.put("documents", {"id": key or uuid.uuid4().hex, "markdown": markdown, "title": title,
                                      "source": source or old.get("source"), "created": old.get("created", now),
                                      "opened": old.get("opened") if old else now})

    def open_document(self, key):
        document = self.get('documents', key)
        document['opened'] = time.time()
        return self.put('documents', document)
