"""SQLite storage for Photobooth v4.0 FASE 1 (stdlib only)."""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "database", "photobooth.db",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    created_at TEXT NOT NULL,
    photo_count INTEGER DEFAULT 0,
    template TEXT DEFAULT '',
    filter TEXT DEFAULT '',
    layout TEXT DEFAULT '',
    file_name TEXT DEFAULT '',
    file_path TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS session_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);
CREATE TABLE IF NOT EXISTS daily_counter (
    day TEXT PRIMARY KEY,
    last_no INTEGER DEFAULT 0
);
"""


def _connect(path=DB_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(path=DB_PATH):
    conn = _connect(path)
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
    return path


def next_session_id(path=DB_PATH):
    now = datetime.now()
    day = now.strftime("%Y%m%d")
    conn = _connect(path)
    try:
        conn.executescript(_SCHEMA)
        cur = conn.execute("SELECT last_no FROM daily_counter WHERE day=?", (day,))
        row = cur.fetchone()
        no = (row[0] if row else 0) + 1
        conn.execute(
            "INSERT OR REPLACE INTO daily_counter(day,last_no) VALUES(?,?)",
            (day, no),
        )
        conn.commit()
    finally:
        conn.close()
    return f"SESSION-{day}-{no:03d}"


def create_session(session_id, photo_count=0, template="", filter_name="",
                   layout="", file_name="", file_path="", path=DB_PATH):
    now = datetime.now()
    conn = _connect(path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO sessions
               (session_id,date,time,created_at,photo_count,template,filter,layout,file_name,file_path)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (session_id, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
             now.isoformat(timespec="seconds"), photo_count, template,
             filter_name, layout, file_name, file_path),
        )
        conn.commit()
    finally:
        conn.close()


def update_session(session_id, path=DB_PATH, **fields):
    allowed = {"photo_count", "template", "filter", "layout", "file_name", "file_path"}
    kv = {k: v for k, v in fields.items() if k in allowed}
    if not kv:
        return
    conn = _connect(path)
    try:
        sets = ",".join(f"{k}=?" for k in kv)
        conn.execute(f"UPDATE sessions SET {sets} WHERE session_id=?",
                     (*kv.values(), session_id))
        conn.commit()
    finally:
        conn.close()


def add_photo(session_id, file_name, file_path, path=DB_PATH):
    conn = _connect(path)
    try:
        conn.execute(
            "INSERT INTO session_photos(session_id,file_name,file_path,created_at)"
            " VALUES(?,?,?,?)",
            (session_id, file_name, file_path,
             datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    finally:
        conn.close()


def list_sessions(limit=100, path=DB_PATH):
    conn = _connect(path)
    try:
        cur = conn.execute(
            "SELECT session_id,date,time,photo_count,template,filter,layout,file_name,file_path"
            " FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
        return cur.fetchall()
    finally:
        conn.close()
