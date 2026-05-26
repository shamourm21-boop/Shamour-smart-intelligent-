"""Shredded Web App — Flask prototype."""

import json
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, url_for

from shredded.db import init_db
from shredded.exercises import EXERCISE_DB, fuzzy_match
from shredded.programs import PROGRAMS
from shredded import tracker as t

app = Flask(__name__)


def _bootstrap() -> None:
    init_db()
    t.seed_programs_if_needed()


_bootstrap()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _epley(weight: float, reps: int) -> float:
    return round(weight * (1 + reps / 30), 1) if weight and reps else 0.0


def _session_duration(session: dict) -> str:
    if not session.get("finished_at") or not session.get("started_at"):
        return ""
    try:
        start = datetime.fromisoformat(session["started_at"])
        end   = datetime.fromisoformat(session["finished_at"])
        mins  = int((end - start).total_seconds() / 60)
        return f"{mins}m"
    except Exception:
        return ""


# ── Page routes ───────────────────────────────────────────────────────────────

@app.get("/")
def dashboard():
    prog_name = t.get_setting("active_program")
    week      = int(t.get_setting("current_week", "1"))
    day       = int(t.get_setting("current_day",  "1"))
    active    = t.get_active_session()
    recent    = t.list_sessions(limit=5)
    prs       = t.get_prs()[:6]

    today_workout = None
    if prog_name:
        prog_id = t.get_program_id(prog_name)
        if prog_id:
            row = t.get_today_workout(prog_id, week, day)
            if row:
                today_workout = {
                    "label":     row["label"],
                    "week":      week,
                    "day":       day,
                    "exercises": json.loads(row["exercises"]),
                }

    total_sessions = len(t.list_sessions(limit=9999))
    body_stats     = t.get_body_stats(limit=1)
    latest_weight  = body_stats[0]["weight_kg"] if body_stats else None

    return render_template(
        "dashboard.html",
        active=active,
        recent=recent,
        today_workout=today_workout,
        prog_name=prog_name,
        week=week,
        day=day,
        prs=prs,
        total_sessions=total_sessions,
        latest_weight=latest_weight,
        epley=_epley,
        duration=_session_duration,
    )


@app.get("/workout")
def workout():
    active    = t.get_active_session()
    exercises = sorted(EXERCISE_DB.keys())
    sets      = t.get_sets_for_session(active["id"]) if active else []
    # Group sets by exercise for display
    grouped: dict[str, list] = {}
    for s in sets:
        grouped.setdefault(s["exercise"], []).append(s)
    return render_template(
        "workout.html",
        active=active,
        exercises=exercises,
        grouped=grouped,
        sets=sets,
    )


@app.get("/history")
def history():
    sessions = t.list_sessions(limit=30)
    for s in sessions:
        s["duration"] = _session_duration(s)
    return render_template("history.html", sessions=sessions)


@app.get("/history/<int:session_id>")
def session_detail(session_id: int):
    session = t.get_session(session_id)
    if not session:
        return redirect(url_for("history"))
    sets = t.get_sets_for_session(session_id)
    grouped: dict[str, list] = {}
    for s in sets:
        grouped.setdefault(s["exercise"], []).append(s)
    session["duration"] = _session_duration(session)
    return render_template("session_detail.html", session=session, grouped=grouped, epley=_epley)


@app.get("/progress")
def progress():
    exercises = sorted(EXERCISE_DB.keys())
    selected  = request.args.get("exercise", "")
    return render_template("progress.html", exercises=exercises, selected=selected)


@app.get("/prs")
def prs():
    records = t.get_prs()
    return render_template("prs.html", records=records, epley=_epley)


@app.get("/stats")
def stats():
    rows = list(reversed(t.get_body_stats(limit=30)))
    return render_template("stats.html", rows=rows)


@app.get("/program")
def program():
    prog_name = t.get_setting("active_program") or "Optimal Shredded"
    week      = int(t.get_setting("current_week", "1"))
    day       = int(t.get_setting("current_day",  "1"))
    prog      = PROGRAMS.get(prog_name)
    return render_template(
        "program.html",
        prog=prog,
        prog_name=prog_name,
        week=week,
        day=day,
        all_programs=list(PROGRAMS.keys()),
    )


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/api/session/active")
def api_active_session():
    session = t.get_active_session()
    if not session:
        return jsonify(None)
    sets = t.get_sets_for_session(session["id"])
    return jsonify({"session": session, "sets": sets})


@app.post("/api/session/start")
def api_start_session():
    data    = request.get_json(force=True)
    name    = data.get("name", "")
    program = t.get_setting("active_program")
    prog_id = None
    week    = int(t.get_setting("current_week", "1"))
    day     = int(t.get_setting("current_day",  "1"))
    if program:
        prog_id = t.get_program_id(program)
    session_id = t.start_session(name=name, program_id=prog_id, week=week, day=day)
    return jsonify({"id": session_id, "name": name})


@app.post("/api/session/finish")
def api_finish_session():
    data    = request.get_json(force=True)
    session = t.get_active_session()
    if not session:
        return jsonify({"error": "no active session"}), 400
    notes = data.get("notes", "")
    t.finish_session(session["id"], notes)

    # Advance program
    prog_id = session.get("program_id")
    if prog_id:
        with t.get_conn() as conn:
            prog_row = conn.execute("SELECT * FROM programs WHERE id=?", (prog_id,)).fetchone()
        if prog_row:
            dpw   = prog_row["days_per_week"]
            weeks = prog_row["weeks"]
            cur_w = int(t.get_setting("current_week", "1"))
            cur_d = int(t.get_setting("current_day",  "1"))
            next_d = cur_d + 1
            next_w = cur_w
            if next_d > dpw:
                next_d = 1
                next_w = cur_w + 1
            if next_w > weeks:
                next_w = 1
            t.set_setting("current_week", str(next_w))
            t.set_setting("current_day",  str(next_d))

    sets = t.get_sets_for_session(session["id"])
    total_vol = sum((s["weight_kg"] or 0) * (s["reps"] or 0)
                    for s in sets if not s["is_warmup"])
    return jsonify({"id": session["id"], "volume": total_vol, "set_count": len(sets)})


@app.post("/api/set/log")
def api_log_set():
    data       = request.get_json(force=True)
    session    = t.get_active_session()
    if not session:
        return jsonify({"error": "no active session"}), 400
    exercise   = data.get("exercise", "").strip()
    reps       = data.get("reps")
    weight_kg  = data.get("weight_kg")
    duration_s = data.get("duration_s")
    rpe        = data.get("rpe")
    is_warmup  = bool(data.get("is_warmup", False))
    set_num    = t.next_set_number(session["id"], exercise)
    set_id     = t.log_set(
        session_id=session["id"],
        exercise=exercise,
        set_number=set_num,
        reps=reps,
        weight_kg=weight_kg,
        duration_s=duration_s,
        rpe=rpe,
        is_warmup=is_warmup,
    )
    one_rm = _epley(weight_kg or 0, reps or 0)
    return jsonify({"id": set_id, "set_number": set_num, "one_rm": one_rm})


@app.delete("/api/set/<int:set_id>")
def api_delete_set(set_id: int):
    session = t.get_active_session()
    if not session:
        return jsonify({"error": "no active session"}), 400
    with t.get_conn() as conn:
        conn.execute("DELETE FROM sets WHERE id=? AND session_id=?", (set_id, session["id"]))
    return jsonify({"ok": True})


@app.get("/api/sets/<int:session_id>")
def api_get_sets(session_id: int):
    sets = t.get_sets_for_session(session_id)
    return jsonify(sets)


@app.get("/api/progress/<path:exercise>")
def api_progress(exercise: str):
    history = t.get_exercise_history(exercise, limit=40)
    history = list(reversed(history))
    points  = [
        {
            "date":         r["logged_at"][:10],
            "weight_kg":    r["weight_kg"],
            "reps":         r["reps"],
            "estimated_1rm": r["estimated_1rm"],
        }
        for r in history
    ]
    return jsonify(points)


@app.get("/api/stats")
def api_get_stats():
    rows = list(reversed(t.get_body_stats(limit=40)))
    return jsonify(rows)


@app.post("/api/stats/log")
def api_log_stats():
    data = request.get_json(force=True)
    t.log_body_stat(
        weight_kg=data.get("weight_kg"),
        body_fat_pct=data.get("body_fat_pct"),
        chest_cm=data.get("chest_cm"),
        waist_cm=data.get("waist_cm"),
        hips_cm=data.get("hips_cm"),
        arms_cm=data.get("arms_cm"),
        legs_cm=data.get("legs_cm"),
        notes=data.get("notes", ""),
    )
    return jsonify({"ok": True})


@app.get("/api/exercises")
def api_exercises():
    q = request.args.get("q", "")
    if q:
        matches = fuzzy_match(q)
    else:
        matches = sorted(EXERCISE_DB.keys())
    return jsonify(matches)


@app.get("/api/today")
def api_today():
    prog_name = t.get_setting("active_program")
    if not prog_name:
        return jsonify(None)
    prog_id = t.get_program_id(prog_name)
    week    = int(t.get_setting("current_week", "1"))
    day     = int(t.get_setting("current_day",  "1"))
    row     = t.get_today_workout(prog_id, week, day)
    if not row:
        return jsonify(None)
    return jsonify({
        "label":     row["label"],
        "week":      week,
        "day":       day,
        "exercises": json.loads(row["exercises"]),
    })


@app.post("/api/program/set")
def api_program_set():
    data = request.get_json(force=True)
    name = data.get("name", "Optimal Shredded")
    week = int(data.get("week", 1))
    day  = int(data.get("day", 1))
    if name not in PROGRAMS:
        return jsonify({"error": f"Unknown program: {name}"}), 400
    t.set_setting("active_program", name)
    t.set_setting("current_week",   str(week))
    t.set_setting("current_day",    str(day))
    return jsonify({"ok": True, "name": name, "week": week, "day": day})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
