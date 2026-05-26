"""Shredded CLI — the optimal fitness tracker."""

import json
import sys
from typing import Optional

import typer
from rich.prompt import Prompt, Confirm
from rich.console import Console

from . import __version__
from .db import init_db
from . import tracker as t
from . import display as d
from .exercises import fuzzy_match, get_or_create
from .programs import PROGRAMS

app = typer.Typer(
    name="shredded",
    help="The optimal fitness tracker. Get absolutely shredded.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def _bootstrap() -> None:
    init_db()
    t.seed_programs_if_needed()


# ── start ──────────────────────────────────────────────────────────────────────

@app.command()
def start(
    name: str = typer.Option("", "--name", "-n", help="Workout name / label"),
    program: str = typer.Option("", "--program", "-p", help="Program name to follow"),
    week: int = typer.Option(0, "--week", "-w", help="Program week (1-based)"),
    day: int = typer.Option(0, "--day", "-d", help="Program day  (1-based)"),
) -> None:
    """Start a new workout session."""
    _bootstrap()

    active = t.get_active_session()
    if active:
        console.print(f"[yellow]Warning:[/yellow] Session '{active['name'] or active['id']}' already active (started {active['started_at'][:16]}). Finish it first with [bold]shredded finish[/bold].")
        raise typer.Exit(1)

    # Resolve program context
    prog_id: Optional[int] = None
    prog_week: Optional[int] = None
    prog_day: Optional[int] = None

    if not program:
        saved = t.get_setting("active_program")
        if saved:
            program = saved

    if program:
        prog_id = t.get_program_id(program)
        if not prog_id:
            console.print(f"[red]Program '{program}' not found.[/red]")
            raise typer.Exit(1)
        prog_week = week if week > 0 else int(t.get_setting("current_week", "1"))
        prog_day  = day  if day  > 0 else int(t.get_setting("current_day",  "1"))

        workout = t.get_today_workout(prog_id, prog_week, prog_day)
        if workout:
            exercises = json.loads(workout["exercises"])
            d.workout_plan_table(workout["label"], exercises, prog_week, prog_day)
            if not name:
                name = workout["label"]

    session_id = t.start_session(name=name, program_id=prog_id, week=prog_week, day=prog_day)
    console.print(f"\n[bold green]Session started![/bold green]  ID: {session_id}  Name: [bold]{name or '(unnamed)'}[/bold]")
    console.print("Log sets with [bold]shredded log[/bold], finish with [bold]shredded finish[/bold].\n")


# ── log ────────────────────────────────────────────────────────────────────────

@app.command()
def log(
    exercise: str = typer.Argument("", help="Exercise name (partial OK)"),
    reps: int = typer.Option(0, "--reps", "-r"),
    weight: float = typer.Option(0.0, "--weight", "-w", help="Weight in kg"),
    duration: int = typer.Option(0, "--duration", "-d", help="Duration in seconds (timed exercises)"),
    rpe: float = typer.Option(0.0, "--rpe", help="Rate of Perceived Exertion (1-10)"),
    warmup: bool = typer.Option(False, "--warmup", "-W", help="Mark as warm-up set"),
    sets: int = typer.Option(1, "--sets", "-s", help="Log multiple identical sets at once"),
) -> None:
    """Log a set (or multiple sets) to the active session."""
    _bootstrap()

    session = t.get_active_session()
    if not session:
        console.print("[red]No active session. Run [bold]shredded start[/bold] first.[/red]")
        raise typer.Exit(1)

    # Resolve exercise name
    if not exercise:
        exercise = Prompt.ask("Exercise name")
    matches = fuzzy_match(exercise)
    if len(matches) == 1:
        exercise = matches[0]
    elif len(matches) > 1 and exercise not in matches:
        console.print("Multiple matches:")
        for i, m in enumerate(matches[:8], 1):
            console.print(f"  {i}. {m}")
        idx = Prompt.ask("Pick number (or enter name)", default="1")
        try:
            exercise = matches[int(idx) - 1]
        except (ValueError, IndexError):
            exercise = idx  # user typed a full name

    ex_info = get_or_create(exercise)
    if reps == 0 and duration == 0:
        if ex_info.is_timed:
            duration = int(Prompt.ask("Duration (seconds)"))
        else:
            reps = int(Prompt.ask("Reps"))
    if weight == 0.0 and not ex_info.is_timed and reps > 0:
        w_str = Prompt.ask("Weight (kg, 0 = bodyweight)", default="0")
        weight = float(w_str)

    for _ in range(sets):
        set_num = t.next_set_number(session["id"], exercise)
        t.log_set(
            session_id=session["id"],
            exercise=exercise,
            set_number=set_num,
            reps=reps if reps > 0 else None,
            weight_kg=weight if weight > 0 else None,
            duration_s=duration if duration > 0 else None,
            rpe=rpe if rpe > 0 else None,
            is_warmup=warmup,
        )

    tag = "[dim](warmup)[/dim]" if warmup else ""
    weight_str = f" @ {weight}kg" if weight > 0 else ""
    dur_str    = f" {duration}s"  if duration > 0 else ""
    reps_str   = f" × {reps}"    if reps > 0 else ""
    label = f"Set {t.next_set_number(session['id'], exercise) - 1}"
    if sets > 1:
        label = f"{sets} sets"
    console.print(f"[green]✓[/green] {label} — [bold]{exercise}[/bold]{reps_str}{dur_str}{weight_str} {tag}")


# ── finish ─────────────────────────────────────────────────────────────────────

@app.command()
def finish(
    notes: str = typer.Option("", "--notes", "-n", help="Post-workout notes"),
) -> None:
    """Finish the active workout session and print a summary."""
    _bootstrap()

    session = t.get_active_session()
    if not session:
        console.print("[red]No active session.[/red]")
        raise typer.Exit(1)

    if not notes:
        notes = Prompt.ask("Any notes? (leave blank to skip)", default="")

    t.finish_session(session["id"], notes)

    sets = t.get_sets_for_session(session["id"])
    d.session_summary(session, sets)

    # Advance program day/week
    if session.get("program_id"):
        prog_id   = session["program_id"]
        cur_week  = int(t.get_setting("current_week", "1"))
        cur_day   = int(t.get_setting("current_day",  "1"))

        prog_row = None
        with t.get_conn() as conn:
            prog_row = conn.execute("SELECT * FROM programs WHERE id=?", (prog_id,)).fetchone()

        if prog_row:
            dpw = prog_row["days_per_week"]
            weeks = prog_row["weeks"]
            next_day  = cur_day + 1
            next_week = cur_week
            if next_day > dpw:
                next_day  = 1
                next_week = cur_week + 1
            if next_week > weeks:
                next_week = 1  # restart

            t.set_setting("current_week", str(next_week))
            t.set_setting("current_day",  str(next_day))
            console.print(f"[dim]Program advanced → Week {next_week}, Day {next_day}[/dim]")

    console.print("[bold green]Great work! Session saved.[/bold green]\n")


# ── history ────────────────────────────────────────────────────────────────────

@app.command()
def history(
    limit: int = typer.Option(15, "--limit", "-l", help="Number of sessions to show"),
) -> None:
    """Show workout history."""
    _bootstrap()
    sessions = t.list_sessions(limit=limit)
    if not sessions:
        console.print("[dim]No completed sessions yet. Run [bold]shredded start[/bold] to begin![/dim]")
        return
    d.history_table(sessions)


# ── prs ─────────────────────────────────────────────────────────────────────

@app.command()
def prs(
    exercise: str = typer.Argument("", help="Filter to a specific exercise"),
) -> None:
    """Display personal records for all (or a specific) exercise."""
    _bootstrap()
    filters = [exercise] if exercise else None
    records = t.get_prs(filters)
    if not records:
        console.print("[dim]No records yet. Log some sets![/dim]")
        return
    d.pr_table(records)


# ── progress ───────────────────────────────────────────────────────────────────

@app.command()
def progress(
    exercise: str = typer.Argument("", help="Exercise to chart"),
    stat: str = typer.Option("weight", "--stat", "-s",
                             help="body-weight | body-fat | waist | volume"),
) -> None:
    """Plot a progress chart for an exercise or body stat."""
    _bootstrap()

    if exercise:
        history_rows = t.get_exercise_history(exercise, limit=40)
        history_rows = list(reversed(history_rows))
        if not history_rows:
            console.print(f"[dim]No data for '{exercise}'.[/dim]")
            return
        points = [(r["logged_at"], r["estimated_1rm"] or r["weight_kg"] or 0)
                  for r in history_rows if r["weight_kg"]]
        d.ascii_chart(f"{exercise} — Estimated 1RM", points, unit=" kg")
        return

    body = t.get_body_stats(limit=40)
    body = list(reversed(body))
    if not body:
        console.print("[dim]No body stats yet. Use [bold]shredded stats log[/bold] to add.[/dim]")
        return

    stat_map = {
        "weight":   ("weight_kg",    "Body Weight",   " kg"),
        "body-fat": ("body_fat_pct", "Body Fat %",    "%"),
        "waist":    ("waist_cm",     "Waist",         " cm"),
        "volume":   ("weight_kg",    "Body Weight",   " kg"),
    }
    col, title, unit = stat_map.get(stat, ("weight_kg", "Body Weight", " kg"))
    points = [(r["logged_at"], r[col]) for r in body if r[col] is not None]
    d.ascii_chart(title, points, unit=unit)


# ── stats ──────────────────────────────────────────────────────────────────────

stats_app = typer.Typer(help="Body stats sub-commands.", add_completion=False)
app.add_typer(stats_app, name="stats")


@stats_app.command("log")
def stats_log(
    weight: float = typer.Option(0.0, "--weight", "-w", help="Body weight (kg)"),
    body_fat: float = typer.Option(0.0, "--body-fat", "-b", help="Body fat %"),
    waist: float = typer.Option(0.0, "--waist", help="Waist circumference (cm)"),
    chest: float = typer.Option(0.0, "--chest", help="Chest circumference (cm)"),
    hips: float = typer.Option(0.0, "--hips",  help="Hip circumference (cm)"),
    arms: float = typer.Option(0.0, "--arms",  help="Arm circumference (cm)"),
    legs: float = typer.Option(0.0, "--legs",  help="Leg circumference (cm)"),
    notes: str  = typer.Option("",  "--notes", help="Notes"),
) -> None:
    """Log today's body measurements."""
    _bootstrap()
    if weight == 0.0 and body_fat == 0.0 and waist == 0.0 and chest == 0.0:
        weight   = float(Prompt.ask("Body weight (kg, 0 to skip)", default="0") or 0)
        body_fat = float(Prompt.ask("Body fat % (0 to skip)",      default="0") or 0)
        waist    = float(Prompt.ask("Waist cm (0 to skip)",         default="0") or 0)
        chest    = float(Prompt.ask("Chest cm (0 to skip)",         default="0") or 0)
        arms     = float(Prompt.ask("Arms cm (0 to skip)",          default="0") or 0)
        legs     = float(Prompt.ask("Legs cm (0 to skip)",          default="0") or 0)

    t.log_body_stat(
        weight_kg=weight or None,
        body_fat_pct=body_fat or None,
        chest_cm=chest or None,
        waist_cm=waist or None,
        arms_cm=arms or None,
        legs_cm=legs or None,
        notes=notes,
    )
    console.print("[green]✓ Body stats saved.[/green]")


@stats_app.command("show")
def stats_show(limit: int = typer.Option(10, "--limit", "-l")) -> None:
    """Show body stat history."""
    _bootstrap()
    rows = t.get_body_stats(limit=limit)
    if not rows:
        console.print("[dim]No body stats yet. Use [bold]shredded stats log[/bold].[/dim]")
        return
    d.body_stats_table(list(reversed(rows)))


# ── program ────────────────────────────────────────────────────────────────────

prog_app = typer.Typer(help="Program management.", add_completion=False)
app.add_typer(prog_app, name="program")


@prog_app.command("list")
def program_list() -> None:
    """List available programs."""
    _bootstrap()
    for name, p in PROGRAMS.items():
        console.print(f"[bold red]{name}[/bold red]  ({p.weeks} weeks, {p.days_per_week} days/week)")
        console.print(f"  [dim]{p.description}[/dim]\n")


@prog_app.command("set")
def program_set(
    name: str = typer.Argument("Optimal Shredded"),
    week: int = typer.Option(1, "--week", "-w"),
    day:  int = typer.Option(1, "--day",  "-d"),
) -> None:
    """Activate a program and set the starting week/day."""
    _bootstrap()
    if name not in PROGRAMS:
        console.print(f"[red]Unknown program '{name}'. Available: {', '.join(PROGRAMS)}[/red]")
        raise typer.Exit(1)
    t.set_setting("active_program", name)
    t.set_setting("current_week",   str(week))
    t.set_setting("current_day",    str(day))
    console.print(f"[green]✓ Active program set to [bold]{name}[/bold] — Week {week}, Day {day}[/green]")


@prog_app.command("today")
def program_today() -> None:
    """Show today's planned workout from the active program."""
    _bootstrap()
    prog_name = t.get_setting("active_program")
    if not prog_name:
        console.print("[yellow]No program active. Run [bold]shredded program set[/bold].[/yellow]")
        raise typer.Exit(1)

    prog_id = t.get_program_id(prog_name)
    week    = int(t.get_setting("current_week", "1"))
    day     = int(t.get_setting("current_day",  "1"))
    workout = t.get_today_workout(prog_id, week, day)

    if not workout:
        console.print(f"[dim]No workout found for Week {week} Day {day}.[/dim]")
        return

    exercises = json.loads(workout["exercises"])
    d.workout_plan_table(workout["label"], exercises, week, day)


# ── version ────────────────────────────────────────────────────────────────────

@app.command()
def version() -> None:
    """Show version."""
    console.print(f"Shredded v{__version__}")


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    d.banner()
    app()


if __name__ == "__main__":
    main()
