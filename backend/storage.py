from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import time
import uuid
from contextlib import closing, contextmanager
from pathlib import Path


def data_directory():
    # Keep the old override usable for existing development scripts.
    override = os.environ.get("LILT_DATA_DIR") or os.environ.get("FOLIO_DATA_DIR")
    if override:
        return Path(override).resolve()
    parent = Path(os.environ["LOCALAPPDATA"]) if os.environ.get("LOCALAPPDATA") else Path.home()
    root, legacy = parent / "Lilt", parent / "Folio"
    if (root / "library.sqlite3").is_file() or not (legacy / "library.sqlite3").is_file():
        return root
    if root.exists():
        raise FileExistsError("The Lilt data folder already exists without a library. Move it aside before migrating your existing library.")
    staging = Path(tempfile.mkdtemp(prefix=".lilt-migration-", dir=parent))
    try:
        # Stage a complete copy; the original remains available as a backup.
        # WebView's expendable browser cache may contain locked files.
        for source in legacy.iterdir():
            if source.name in {"webview", "library.sqlite3", "library.sqlite3-wal", "library.sqlite3-shm", "library.sqlite3-journal"}:
                continue
            target = staging / ("lilt.log" if source.name == "folio.log" else source.name)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        with closing(sqlite3.connect(f"{(legacy / 'library.sqlite3').as_uri()}?mode=ro", uri=True)) as source_db:
            with closing(sqlite3.connect(staging / "library.sqlite3")) as target_db:
                source_db.backup(target_db)
                if target_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("The existing library could not be migrated safely.")
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
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, body TEXT NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, body TEXT NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)

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
        return json.loads(row[0])

    def all(self, table):
        if table not in {"documents", "jobs"}:
            raise ValueError("Invalid collection")
        with self.connect() as connection:
            rows = connection.execute(f"SELECT body FROM {table} ORDER BY updated DESC").fetchall()
        return [json.loads(row[0]) for row in rows]

    def remove(self, table, key):
        if table not in {"documents", "jobs"}:
            raise ValueError("Invalid collection")
        with self.connect() as connection:
            connection.execute(f"DELETE FROM {table} WHERE id = ?", (key,))

    def settings(self):
        from .performance import DEFAULTS
        defaults = {"theme": "light", "palette": "lilt", "voice": "af_heart", "speed": 1.0, "include_code": False,
                    "heading_pause": 0.6, "paragraph_pause": 0.3} | DEFAULTS
        with self.connect() as connection:
            defaults.update({key: json.loads(value) for key, value in connection.execute("SELECT key, value FROM settings")})
        return defaults

    def save_settings(self, settings):
        from .performance import DEFAULTS
        allowed = {"theme", "palette", "voice", "speed", "include_code", "heading_pause", "paragraph_pause", 'benchmark_result'} | set(DEFAULTS)
        with self.connect() as connection:
            for key, value in settings.items():
                if key in allowed:
                    connection.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, json.dumps(value)))
        return self.settings()

    def document(self, markdown, title, source=None, key=None):
        old = self.get("documents", key) if key else {}
        now = time.time()
        return self.put("documents", {"id": key or uuid.uuid4().hex, "markdown": markdown, "title": title,
                                      "source": source or old.get("source"), "created": old.get("created", now),
                                      "opened": old.get("opened") if old else now})

    def open_document(self, key):
        document = self.get('documents', key)
        document['opened'] = time.time()
        return self.put('documents', document)
