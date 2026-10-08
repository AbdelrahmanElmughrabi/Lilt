from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


def data_directory():
    if os.environ.get("FOLIO_DATA_DIR"):
        return Path(os.environ["FOLIO_DATA_DIR"]).resolve()
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Folio"


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
        defaults = {"theme": "light", "voice": "af_heart", "speed": 1.0, "include_code": False,
                    "heading_pause": 0.6, "paragraph_pause": 0.3} | DEFAULTS
        with self.connect() as connection:
            defaults.update({key: json.loads(value) for key, value in connection.execute("SELECT key, value FROM settings")})
        return defaults

    def save_settings(self, settings):
        from .performance import DEFAULTS
        allowed = {"theme", "voice", "speed", "include_code", "heading_pause", "paragraph_pause", 'benchmark_result'} | set(DEFAULTS)
        with self.connect() as connection:
            for key, value in settings.items():
                if key in allowed:
                    connection.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, json.dumps(value)))
        return self.settings()

    def document(self, markdown, title, source=None, key=None):
        old = self.get("documents", key) if key else {}
        return self.put("documents", {"id": key or uuid.uuid4().hex, "markdown": markdown, "title": title,
                                      "source": source or old.get("source"), "created": old.get("created", time.time())})
