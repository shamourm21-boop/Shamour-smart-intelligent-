"""SQLite database layer for Shredded."""

import sqlite3
from pathlib import Path
from typing import Optional
import os

DB_PATH = Path(os.environ.get("SHREDDED_DB", Path.home() / ".shredded" / "data.db"))


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT,
                started_at  TEXT NOT NULL DEFAULT (datetime('now')),
                finished_at TEXT,
                notes       TEXT,
                program_id  INTEGER REFERENCES programs(id),
                week        INTEGER,
                day         INTEGER
            );

            CREATE TABLE IF NOT EXISTS sets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                exercise    TEXT NOT NULL,
                set_number  INTEGER NOT NULL,
                reps        INTEGER,
                weight_kg   REAL,
                duration_s  INTEGER,
                rpe         REAL,
                is_warmup   INTEGER NOT NULL DEFAULT 0,
                logged_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS body_stats (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                logged_at   TEXT NOT NULL DEFAULT (date('now')),
                weight_kg   REAL,
                body_fat_pct REAL,
                chest_cm    REAL,
                waist_cm    REAL,
                hips_cm     REAL,
                arms_cm     REAL,
                legs_cm     REAL,
                notes       TEXT
            );

            CREATE TABLE IF NOT EXISTS programs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                weeks       INTEGER NOT NULL,
                days_per_week INTEGER NOT NULL,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS program_workouts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id  INTEGER NOT NULL REFERENCES programs(id),
                week        INTEGER NOT NULL,
                day         INTEGER NOT NULL,
                label       TEXT NOT NULL,
                exercises   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
        """)
