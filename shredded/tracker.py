"""Workout session CRUD operations."""

from typing import Optional
import json

from .db import get_conn


# ── Sessions ──────────────────────────────────────────────────────────────────

def start_session(name: str = "", program_id: Optional[int] = None,
                  week: Optional[int] = None, day: Optional[int] = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (name, program_id, week, day) VALUES (?,?,?,?)",
            (name, program_id, week, day),
        )
        return cur.lastrowid


def finish_session(session_id: int, notes: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET finished_at=datetime('now'), notes=? WHERE id=?",
            (notes, session_id),
        )


def get_active_session() -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE finished_at IS NULL ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_session(session_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else None


def list_sessions(limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT s.*,
                   COUNT(st.id)                            AS set_count,
                   SUM(st.weight_kg * COALESCE(st.reps,0)) AS volume
            FROM sessions s
            LEFT JOIN sets st ON st.session_id = s.id AND st.is_warmup=0
            WHERE s.finished_at IS NOT NULL
            GROUP BY s.id
            ORDER BY s.started_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── Sets ──────────────────────────────────────────────────────────────────────

def log_set(session_id: int, exercise: str, set_number: int,
            reps: Optional[int] = None, weight_kg: Optional[float] = None,
            duration_s: Optional[int] = None, rpe: Optional[float] = None,
            is_warmup: bool = False) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO sets
               (session_id, exercise, set_number, reps, weight_kg, duration_s, rpe, is_warmup)
               VALUES (?,?,?,?,?,?,?,?)""",
            (session_id, exercise, set_number, reps, weight_kg, duration_s, rpe, int(is_warmup)),
        )
        return cur.lastrowid


def get_sets_for_session(session_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sets WHERE session_id=? ORDER BY logged_at",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def next_set_number(session_id: int, exercise: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(set_number) FROM sets WHERE session_id=? AND exercise=?",
            (session_id, exercise),
        ).fetchone()
        return (row[0] or 0) + 1


# ── Personal Records ──────────────────────────────────────────────────────────

def get_prs(exercises: Optional[list[str]] = None) -> list[dict]:
    """Return best set per exercise, ordered by estimated 1RM (Epley)."""
    with get_conn() as conn:
        filter_clause = ""
        params: list = []
        if exercises:
            placeholders = ",".join("?" * len(exercises))
            filter_clause = f"WHERE s.exercise IN ({placeholders})"
            params = list(exercises)

        rows = conn.execute(f"""
            SELECT s.exercise,
                   s.weight_kg,
                   s.reps,
                   s.duration_s,
                   s.logged_at,
                   s.weight_kg * (1 + s.reps / 30.0) AS estimated_1rm
            FROM sets s
            JOIN sessions ss ON ss.id = s.session_id
            {filter_clause}
            WHERE s.is_warmup = 0
            GROUP BY s.exercise
            HAVING estimated_1rm = MAX(s.weight_kg * (1 + s.reps / 30.0))
               OR  (s.weight_kg IS NULL AND s.reps = MAX(s.reps))
               OR  (s.reps IS NULL      AND s.duration_s = MAX(s.duration_s))
            ORDER BY s.exercise
        """, params).fetchall()
        return [dict(r) for r in rows]


def get_exercise_history(exercise: str, limit: int = 30) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT s.logged_at,
                   s.weight_kg,
                   s.reps,
                   s.duration_s,
                   s.weight_kg * (1 + COALESCE(s.reps,0) / 30.0) AS estimated_1rm
            FROM sets s
            JOIN sessions ss ON ss.id = s.session_id
            WHERE s.exercise = ? AND s.is_warmup = 0
            ORDER BY s.logged_at DESC
            LIMIT ?
        """, (exercise, limit)).fetchall()
        return [dict(r) for r in rows]


# ── Body Stats ────────────────────────────────────────────────────────────────

def log_body_stat(weight_kg: Optional[float] = None,
                  body_fat_pct: Optional[float] = None,
                  chest_cm: Optional[float] = None,
                  waist_cm: Optional[float] = None,
                  hips_cm: Optional[float] = None,
                  arms_cm: Optional[float] = None,
                  legs_cm: Optional[float] = None,
                  notes: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO body_stats
               (weight_kg, body_fat_pct, chest_cm, waist_cm, hips_cm, arms_cm, legs_cm, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (weight_kg, body_fat_pct, chest_cm, waist_cm, hips_cm, arms_cm, legs_cm, notes),
        )
        return cur.lastrowid


def get_body_stats(limit: int = 30) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM body_stats ORDER BY logged_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM user_settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default


def set_setting(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_settings (key, value) VALUES (?,?)",
            (key, value),
        )


# ── Program Management ────────────────────────────────────────────────────────

def seed_programs_if_needed() -> None:
    """Insert built-in programs into DB on first run."""
    import json
    from .programs import PROGRAMS

    with get_conn() as conn:
        for prog_name, prog in PROGRAMS.items():
            existing = conn.execute(
                "SELECT id FROM programs WHERE name=?", (prog_name,)
            ).fetchone()
            if existing:
                continue
            cur = conn.execute(
                "INSERT INTO programs (name, weeks, days_per_week, description) VALUES (?,?,?,?)",
                (prog.name, prog.weeks, prog.days_per_week, prog.description),
            )
            prog_id = cur.lastrowid
            for week, days in prog.schedule.items():
                for day, workout in days.items():
                    conn.execute(
                        "INSERT INTO program_workouts (program_id, week, day, label, exercises) VALUES (?,?,?,?,?)",
                        (prog_id, week, day, workout.label, json.dumps(workout.exercises)),
                    )


def get_program_id(name: str) -> Optional[int]:
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM programs WHERE name=?", (name,)).fetchone()
        return row[0] if row else None


def get_today_workout(program_id: int, week: int, day: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM program_workouts WHERE program_id=? AND week=? AND day=?",
            (program_id, week, day),
        ).fetchone()
        return dict(row) if row else None
