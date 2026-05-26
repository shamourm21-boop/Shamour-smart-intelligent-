# SHREDDED — The Optimal Fitness Tracker

A terminal-based workout tracker built to get you absolutely shredded.  
Track sessions, log sets, monitor personal records, chart progress, and follow the built-in 12-week **Optimal Shredded** program.

---

## Features

- **Session tracking** — start/finish workouts with volume and duration summary
- **Set logging** — reps, weight, duration, RPE, warm-up flag
- **Personal records** — auto-tracked with estimated 1RM (Epley formula)
- **Body stats** — weight, body fat %, and circumference measurements over time
- **Progress charts** — ASCII sparkline charts for any exercise or body stat
- **12-week Optimal Shredded program** — science-backed Push/Pull/Legs + Upper + HIIT
  - Phase 1 (weeks 1–4): Hypertrophy foundation
  - Phase 2 (weeks 5–8): Full volume
  - Phase 3 (weeks 9–12): Peak intensity

---

## Install

```bash
pip install rich typer
python -m shredded version      # verify it works
```

---

## Quick Start

```bash
# Activate the 12-week program
python -m shredded program set "Optimal Shredded"

# See today's workout
python -m shredded program today

# Start a session (auto-loads today's plan)
python -m shredded start

# Log sets during your workout
python -m shredded log "Bench Press" --reps 8 --weight 100
python -m shredded log "Bench Press" --reps 8 --weight 100   # set 2
python -m shredded log "Pull-Up" --reps 10                   # bodyweight
python -m shredded log "Plank" --duration 60                 # timed

# Finish and see your summary
python -m shredded finish

# Review progress
python -m shredded history
python -m shredded prs
python -m shredded progress "Bench Press"

# Log body stats
python -m shredded stats log --weight 85.5 --body-fat 18.2 --waist 82
python -m shredded progress --stat body-weight
```

---

## Commands

| Command | Description |
|---|---|
| `start` | Start a workout session |
| `log <exercise>` | Log a set to the active session |
| `finish` | Finish the session, print summary |
| `history` | View recent sessions |
| `prs [exercise]` | Personal records with estimated 1RM |
| `progress <exercise>` | ASCII chart for exercise or body stat |
| `stats log` | Log body measurements |
| `stats show` | View measurement history |
| `program list` | List available programs |
| `program set <name>` | Activate a program |
| `program today` | View today's planned workout |

### `log` options

| Flag | Description |
|---|---|
| `--reps / -r` | Number of reps |
| `--weight / -w` | Weight in kg |
| `--duration / -d` | Duration in seconds (timed exercises) |
| `--rpe` | Rate of Perceived Exertion (1–10) |
| `--warmup / -W` | Mark as warm-up set |
| `--sets / -s` | Log N identical sets at once |

---

## The Optimal Shredded Program

**5 days/week · 12 weeks · 3 phases**

| Day | Workout |
|---|---|
| Monday | Push — Chest / Shoulders / Triceps |
| Tuesday | Pull — Back / Biceps / Rear Delts |
| Wednesday | Legs — Quads / Hamstrings / Glutes / Calves |
| Thursday | Upper Body — Full upper + Core |
| Friday | HIIT Cardio + Core Finisher |
| Saturday | Rest / Active Recovery |

**Progressive overload every session. Add weight whenever you hit the top of the rep range.**

---

## Data Storage

Data is stored in a local SQLite database at `~/.shredded/data.db`.  
Override with the `SHREDDED_DB` environment variable.
