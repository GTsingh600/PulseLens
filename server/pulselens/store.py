"""Session storage: one folder per session (SPEC 4.1) plus a SQLite `sessions` index.

All file I/O for session bundles goes through here. Session IDs are validated against a strict
pattern before any path is built, so a crafted ID can't escape `data/sessions/`.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
import threading
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from pulselens.models import SessionMeta, SessionResults

SESSION_ID_RE = re.compile(r"^s_\d{8}_\d{6}_[0-9a-f]{4}$")
JSONL_STREAMS = ("frames", "pulses", "sensors", "events")
UPDATABLE_COLUMNS = ("state", "route", "profile_measured", "label_set", "chain_head")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id         TEXT PRIMARY KEY,
    created_server_iso TEXT NOT NULL,
    updated_server_iso TEXT NOT NULL,
    mode               TEXT NOT NULL,
    product            TEXT NOT NULL,
    state              TEXT NOT NULL DEFAULT 'created',
    route              TEXT,
    profile_measured   TEXT,
    label_set          TEXT,
    chain_head         TEXT
);
"""


def server_now_iso() -> str:
    """Server wall-clock time with offset. For audit only, never for echo maths."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def new_session_id(now: datetime | None = None) -> str:
    now = now or datetime.now().astimezone()
    return f"s_{now:%Y%m%d_%H%M%S}_{secrets.token_hex(2)}"


class InvalidSessionId(ValueError):
    pass


class SessionStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.sessions_dir = self.root / "sessions"
        self.db_path = self.root / "pulselens.sqlite3"
        self._lock = threading.Lock()
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript(_SCHEMA)

    # -- paths ---------------------------------------------------------------

    def session_dir(self, session_id: str) -> Path:
        if not SESSION_ID_RE.match(session_id):
            raise InvalidSessionId(session_id)
        return self.sessions_dir / session_id

    def exists(self, session_id: str) -> bool:
        return self.session_dir(session_id).is_dir()

    # -- lifecycle -----------------------------------------------------------

    def create(self, meta: SessionMeta) -> Path:
        d = self.session_dir(meta.session_id)
        (d / "frames").mkdir(parents=True, exist_ok=False)
        for stream in JSONL_STREAMS:
            (d / f"{stream}.jsonl").touch()
        self.write_meta(meta)
        now = server_now_iso()
        with self._db() as db:
            db.execute(
                "INSERT INTO sessions (session_id, created_server_iso, updated_server_iso, mode, product, "
                "label_set) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    meta.session_id,
                    meta.created_server_iso,
                    now,
                    meta.mode,
                    meta.product,
                    meta.label.set if meta.label else None,
                ),
            )
        return d

    def update(self, session_id: str, **fields: Any) -> None:
        bad = set(fields) - set(UPDATABLE_COLUMNS)
        if bad:
            raise ValueError(f"not updatable: {sorted(bad)}")
        self.session_dir(session_id)  # validates id
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._db() as db:
            db.execute(
                f"UPDATE sessions SET {cols}, updated_server_iso = ? WHERE session_id = ?",
                (*fields.values(), server_now_iso(), session_id),
            )

    def get_row(self, session_id: str) -> dict[str, Any] | None:
        self.session_dir(session_id)
        with self._db() as db:
            row = db.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._db() as db:
            rows = db.execute("SELECT * FROM sessions ORDER BY created_server_iso DESC").fetchall()
        return [dict(r) for r in rows]

    # -- bundle files --------------------------------------------------------

    def write_meta(self, meta: SessionMeta) -> None:
        self._write_json(self.session_dir(meta.session_id) / "meta.json", meta)

    def read_meta(self, session_id: str) -> SessionMeta:
        path = self.session_dir(session_id) / "meta.json"
        return SessionMeta.model_validate_json(path.read_text(encoding="utf-8"))

    def write_results(self, session_id: str, results: SessionResults) -> None:
        self._write_json(self.session_dir(session_id) / "results.json", results)

    def read_results(self, session_id: str) -> SessionResults | None:
        path = self.session_dir(session_id) / "results.json"
        if not path.exists():
            return None
        return SessionResults.model_validate_json(path.read_text(encoding="utf-8"))

    def write_frame(self, session_id: str, index: int, jpeg: bytes) -> str:
        if index < 0:
            raise ValueError("frame index must be >= 0")
        name = f"{index:06d}.jpg"
        (self.session_dir(session_id) / "frames" / name).write_bytes(jpeg)
        return name

    def append_jsonl(
        self, session_id: str, stream: str, records: Iterable[BaseModel | dict[str, Any]]
    ) -> int:
        path = self._stream_path(session_id, stream)
        lines = [
            (r.model_dump_json() if isinstance(r, BaseModel) else json.dumps(r, separators=(",", ":"))) + "\n"
            for r in records
        ]
        with self._lock, open(path, "a", encoding="utf-8", newline="\n") as f:
            f.writelines(lines)
        return len(lines)

    def read_jsonl(self, session_id: str, stream: str) -> list[dict[str, Any]]:
        path = self._stream_path(session_id, stream)
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    # -- internals -----------------------------------------------------------

    def _stream_path(self, session_id: str, stream: str) -> Path:
        if stream not in JSONL_STREAMS:
            raise ValueError(f"unknown stream {stream!r}")
        return self.session_dir(session_id) / f"{stream}.jsonl"

    @staticmethod
    def _write_json(path: Path, model: BaseModel) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp, path)

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()
