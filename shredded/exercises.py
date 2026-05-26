"""Exercise library with categories, muscles, and defaults."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Exercise:
    name: str
    category: str          # strength | cardio | mobility
    muscles: list[str]
    is_timed: bool = False  # True = uses duration, False = uses reps


EXERCISE_DB: dict[str, Exercise] = {e.name: e for e in [
    # ── Compound Push ──────────────────────────────────────────────────────
    Exercise("Bench Press",           "strength", ["chest", "triceps", "front delt"]),
    Exercise("Incline Bench Press",   "strength", ["upper chest", "triceps", "front delt"]),
    Exercise("Overhead Press",        "strength", ["front delt", "triceps", "upper chest"]),
    Exercise("Dips",                  "strength", ["chest", "triceps"]),
    Exercise("Push-Up",               "strength", ["chest", "triceps", "front delt"]),
    Exercise("Pike Push-Up",          "strength", ["front delt", "triceps"]),

    # ── Compound Pull ──────────────────────────────────────────────────────
    Exercise("Deadlift",              "strength", ["glutes", "hamstrings", "back", "traps"]),
    Exercise("Romanian Deadlift",     "strength", ["hamstrings", "glutes", "lower back"]),
    Exercise("Pull-Up",               "strength", ["lats", "biceps", "rear delt"]),
    Exercise("Chin-Up",               "strength", ["lats", "biceps"]),
    Exercise("Barbell Row",           "strength", ["back", "rear delt", "biceps"]),
    Exercise("Dumbbell Row",          "strength", ["back", "rear delt", "biceps"]),
    Exercise("Cable Row",             "strength", ["back", "rear delt", "biceps"]),
    Exercise("Lat Pulldown",          "strength", ["lats", "biceps"]),
    Exercise("Face Pull",             "strength", ["rear delt", "rotator cuff"]),

    # ── Legs ───────────────────────────────────────────────────────────────
    Exercise("Back Squat",            "strength", ["quads", "glutes", "hamstrings"]),
    Exercise("Front Squat",           "strength", ["quads", "glutes"]),
    Exercise("Bulgarian Split Squat", "strength", ["quads", "glutes", "hamstrings"]),
    Exercise("Leg Press",             "strength", ["quads", "glutes", "hamstrings"]),
    Exercise("Lunges",                "strength", ["quads", "glutes", "hamstrings"]),
    Exercise("Hip Thrust",            "strength", ["glutes", "hamstrings"]),
    Exercise("Leg Curl",              "strength", ["hamstrings"]),
    Exercise("Leg Extension",         "strength", ["quads"]),
    Exercise("Calf Raise",            "strength", ["calves"]),

    # ── Isolation ──────────────────────────────────────────────────────────
    Exercise("Bicep Curl",            "strength", ["biceps"]),
    Exercise("Hammer Curl",           "strength", ["biceps", "brachialis"]),
    Exercise("Tricep Pushdown",       "strength", ["triceps"]),
    Exercise("Skull Crusher",         "strength", ["triceps"]),
    Exercise("Lateral Raise",         "strength", ["side delt"]),
    Exercise("Rear Delt Fly",         "strength", ["rear delt"]),

    # ── Core ───────────────────────────────────────────────────────────────
    Exercise("Plank",                 "strength", ["core", "abs"], is_timed=True),
    Exercise("Ab Wheel Rollout",      "strength", ["core", "abs"]),
    Exercise("Hanging Leg Raise",     "strength", ["abs", "hip flexors"]),
    Exercise("Cable Crunch",          "strength", ["abs"]),
    Exercise("Russian Twist",         "strength", ["obliques", "abs"]),

    # ── Cardio ─────────────────────────────────────────────────────────────
    Exercise("HIIT Sprint",           "cardio",   ["cardio", "legs"], is_timed=True),
    Exercise("Jump Rope",             "cardio",   ["cardio", "calves"], is_timed=True),
    Exercise("Box Jump",              "cardio",   ["cardio", "quads", "glutes"]),
    Exercise("Burpee",                "cardio",   ["cardio", "full body"]),
    Exercise("Battle Ropes",          "cardio",   ["cardio", "shoulders", "core"], is_timed=True),
    Exercise("Rowing Machine",        "cardio",   ["cardio", "back", "legs"], is_timed=True),
    Exercise("Cycling",               "cardio",   ["cardio", "legs"], is_timed=True),
    Exercise("Running",               "cardio",   ["cardio", "legs"], is_timed=True),
]}


def fuzzy_match(query: str) -> list[str]:
    """Return exercise names that contain the query (case-insensitive)."""
    q = query.lower()
    return [name for name in EXERCISE_DB if q in name.lower()]


def get_or_create(name: str) -> Exercise:
    """Return a known exercise or create a generic one."""
    if name in EXERCISE_DB:
        return EXERCISE_DB[name]
    return Exercise(name, "strength", ["unknown"])
