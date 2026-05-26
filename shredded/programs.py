"""Built-in workout programs."""

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class WorkoutDay:
    label: str
    exercises: list[dict[str, Any]]   # [{name, sets, reps, rest_s, note}]


@dataclass
class Program:
    name: str
    weeks: int
    days_per_week: int
    description: str
    # schedule[week][day] -> WorkoutDay (week/day are 1-indexed)
    schedule: dict[int, dict[int, WorkoutDay]]


def _sets_reps(sets: int, reps: str, rest: int = 90, note: str = "") -> dict:
    return {"sets": sets, "reps": reps, "rest_s": rest, "note": note}


def _ex(name: str, sets: int, reps: str, rest: int = 90, note: str = "") -> dict:
    return {"name": name, **_sets_reps(sets, reps, rest, note)}


# ──────────────────────────────────────────────────────────────────────────────
# OPTIMAL SHREDDED — 12-week, 5-day Push/Pull/Legs + Upper + HIIT
# ──────────────────────────────────────────────────────────────────────────────
#   Phase 1 (weeks 1-4):  Hypertrophy foundation
#   Phase 2 (weeks 5-8):  Strength + volume
#   Phase 3 (weeks 9-12): Peak shred (drop sets, supersets, high intensity)
# ──────────────────────────────────────────────────────────────────────────────

def _push(sets_mult: float = 1.0) -> WorkoutDay:
    s = lambda n: max(1, round(n * sets_mult))
    return WorkoutDay("Push (Chest / Shoulders / Triceps)", [
        _ex("Bench Press",          s(4), "6-10",  120, "Progressive overload priority"),
        _ex("Incline Bench Press",  s(3), "8-12",  90),
        _ex("Overhead Press",       s(3), "8-10",  90),
        _ex("Lateral Raise",        s(4), "12-15", 60),
        _ex("Rear Delt Fly",        s(3), "15-20", 60),
        _ex("Tricep Pushdown",      s(3), "10-15", 60),
        _ex("Skull Crusher",        s(3), "10-12", 60),
    ])


def _pull(sets_mult: float = 1.0) -> WorkoutDay:
    s = lambda n: max(1, round(n * sets_mult))
    return WorkoutDay("Pull (Back / Biceps / Rear Delts)", [
        _ex("Deadlift",             s(4), "4-6",   150, "King lift — brace hard"),
        _ex("Pull-Up",              s(4), "6-10",  90,  "Add weight if >10 reps"),
        _ex("Barbell Row",          s(3), "8-10",  90),
        _ex("Lat Pulldown",         s(3), "10-12", 75),
        _ex("Face Pull",            s(3), "15-20", 60,  "Protect rotator cuff"),
        _ex("Bicep Curl",           s(3), "10-12", 60),
        _ex("Hammer Curl",          s(3), "12-15", 60),
    ])


def _legs(sets_mult: float = 1.0) -> WorkoutDay:
    s = lambda n: max(1, round(n * sets_mult))
    return WorkoutDay("Legs (Quads / Hamstrings / Glutes / Calves)", [
        _ex("Back Squat",           s(4), "6-10",  150, "Depth below parallel"),
        _ex("Romanian Deadlift",    s(3), "8-12",  90),
        _ex("Bulgarian Split Squat",s(3), "10-12", 90,  "Per leg"),
        _ex("Leg Curl",             s(3), "12-15", 75),
        _ex("Hip Thrust",           s(3), "12-15", 75),
        _ex("Calf Raise",           s(4), "15-20", 60),
        _ex("Ab Wheel Rollout",     s(3), "8-12",  60),
    ])


def _upper(sets_mult: float = 1.0) -> WorkoutDay:
    s = lambda n: max(1, round(n * sets_mult))
    return WorkoutDay("Upper Body (Full Upper + Core)", [
        _ex("Incline Bench Press",  s(3), "8-10",  90),
        _ex("Cable Row",            s(3), "10-12", 90),
        _ex("Overhead Press",       s(3), "8-10",  90),
        _ex("Dumbbell Row",         s(3), "10-12", 75),
        _ex("Lateral Raise",        s(3), "15",    60),
        _ex("Bicep Curl",           s(2), "12",    60),
        _ex("Tricep Pushdown",      s(2), "12",    60),
        _ex("Hanging Leg Raise",    s(3), "12-15", 60),
        _ex("Plank",                s(3), "60s",   60),
    ])


def _hiit() -> WorkoutDay:
    return WorkoutDay("HIIT Cardio + Core Finisher", [
        {"name": "Jump Rope",    "sets": 5, "reps": "3 min on / 1 min off", "rest_s": 60,  "note": "Keep intensity >80% max HR"},
        {"name": "Burpee",       "sets": 4, "reps": "15",                   "rest_s": 45,  "note": ""},
        {"name": "Battle Ropes", "sets": 4, "reps": "30s",                  "rest_s": 30,  "note": ""},
        {"name": "Box Jump",     "sets": 3, "reps": "10",                   "rest_s": 60,  "note": ""},
        {"name": "Plank",        "sets": 3, "reps": "60s",                  "rest_s": 30,  "note": ""},
        {"name": "Russian Twist","sets": 3, "reps": "20",                   "rest_s": 30,  "note": "Add weight"},
    ])


def _rest() -> WorkoutDay:
    return WorkoutDay("Rest / Active Recovery", [
        {"name": "Cycling",  "sets": 1, "reps": "30-45 min", "rest_s": 0, "note": "Zone 2 — conversational pace"},
    ])


def _build_schedule(push_m: float, pull_m: float, legs_m: float) -> dict:
    # Day layout: Mon=Push, Tue=Pull, Wed=Legs, Thu=Upper, Fri=HIIT, Sat=Rest
    return {
        1: _push(push_m),
        2: _pull(pull_m),
        3: _legs(legs_m),
        4: _upper((push_m + pull_m) / 2),
        5: _hiit(),
        6: _rest(),
    }


def _build_optimal_shredded() -> Program:
    schedule: dict[int, dict[int, WorkoutDay]] = {}

    # Phase 1 — weeks 1-4: moderate volume, learn movements
    for w in range(1, 5):
        schedule[w] = _build_schedule(0.85, 0.85, 0.85)

    # Phase 2 — weeks 5-8: full volume
    for w in range(5, 9):
        schedule[w] = _build_schedule(1.0, 1.0, 1.0)

    # Phase 3 — weeks 9-12: peak intensity (extra sets)
    for w in range(9, 13):
        schedule[w] = _build_schedule(1.15, 1.15, 1.15)

    return Program(
        name="Optimal Shredded",
        weeks=12,
        days_per_week=5,
        description=(
            "12-week science-backed program to maximize fat loss while preserving "
            "and building muscle. Push/Pull/Legs + Upper + HIIT across 5 training "
            "days. Progressive overload every session. Three phases: foundation → "
            "volume → peak intensity."
        ),
        schedule=schedule,
    )


PROGRAMS: dict[str, Program] = {
    "Optimal Shredded": _build_optimal_shredded(),
}
