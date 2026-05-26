"""Rich terminal display utilities."""

from datetime import datetime, date
from typing import Optional, Any
import math

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.text import Text
from rich.style import Style

console = Console()

BRAND = "[bold red]SHREDDED[/bold red]"
ACCENT = "red"


def banner() -> None:
    art = Text("""
  ███████╗██╗  ██╗██████╗ ███████╗██████╗ ██████╗ ███████╗██████╗
  ██╔════╝██║  ██║██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗
  ███████╗███████║██████╔╝█████╗  ██║  ██║██║  ██║█████╗  ██║  ██║
  ╚════██║██╔══██║██╔══██╗██╔══╝  ██║  ██║██║  ██║██╔══╝  ██║  ██║
  ███████║██║  ██║██║  ██║███████╗██████╔╝██████╔╝███████╗██████╔╝
  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═════╝ ╚══════╝╚═════╝
""", style="bold red")
    console.print(art)
    console.print("[dim]  The Optimal Fitness Tracker  •  Get Absolutely Shredded[/dim]\n")


def workout_plan_table(day_label: str, exercises: list[dict], week: int, day: int) -> None:
    console.print(Panel(
        f"[bold]Week {week}  •  Day {day}[/bold]  —  {day_label}",
        style=ACCENT, box=box.HEAVY_HEAD,
    ))

    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style=f"bold {ACCENT}")
    t.add_column("#",        style="dim",         width=3)
    t.add_column("Exercise", style="bold white",  min_width=28)
    t.add_column("Sets",     justify="center",    width=6)
    t.add_column("Reps",     justify="center",    width=10)
    t.add_column("Rest",     justify="center",    width=8)
    t.add_column("Note",     style="dim italic",  min_width=20)

    for i, ex in enumerate(exercises, 1):
        rest = ex.get("rest_s", 90)
        rest_str = f"{rest}s" if rest > 0 else "—"
        t.add_row(
            str(i),
            ex["name"],
            str(ex.get("sets", "")),
            str(ex.get("reps", "")),
            rest_str,
            ex.get("note", ""),
        )

    console.print(t)


def session_summary(session: dict, sets: list[dict]) -> None:
    exercises = {}
    for s in sets:
        exercises.setdefault(s["exercise"], []).append(s)

    console.print(Panel(
        f"[bold]{session['name'] or 'Workout'}[/bold]  •  {session['started_at'][:10]}",
        style=ACCENT, box=box.HEAVY_HEAD,
    ))

    t = Table(box=box.SIMPLE_HEAVY, header_style=f"bold {ACCENT}")
    t.add_column("Exercise",  style="bold white", min_width=28)
    t.add_column("Sets",      justify="center", width=6)
    t.add_column("Volume",    justify="right",  width=12)
    t.add_column("Best Set",  justify="center", width=14)

    for ex_name, ex_sets in exercises.items():
        work_sets = [s for s in ex_sets if not s["is_warmup"]]
        if not work_sets:
            work_sets = ex_sets
        volume = sum((s["weight_kg"] or 0) * (s["reps"] or 0) for s in work_sets)
        best = max(work_sets, key=lambda s: (s["weight_kg"] or 0) * (s["reps"] or 1))
        best_str = (
            f"{best['weight_kg']}kg × {best['reps']}"
            if best["weight_kg"] and best["reps"]
            else (f"{best['reps']} reps" if best["reps"] else f"{best['duration_s']}s")
        )
        t.add_row(
            ex_name,
            str(len(work_sets)),
            f"{volume:.0f} kg" if volume else "—",
            best_str,
        )

    console.print(t)
    total_vol = sum(
        (s["weight_kg"] or 0) * (s["reps"] or 0) for s in sets if not s["is_warmup"]
    )
    console.print(f"  [dim]Total volume: [bold]{total_vol:.0f} kg[/bold]  •  {len(sets)} sets logged[/dim]\n")


def history_table(sessions: list[dict]) -> None:
    t = Table(title="Workout History", box=box.SIMPLE_HEAVY, header_style=f"bold {ACCENT}")
    t.add_column("Date",     width=12)
    t.add_column("Workout",  min_width=24)
    t.add_column("Duration", justify="right", width=10)
    t.add_column("Sets",     justify="center", width=6)
    t.add_column("Volume",   justify="right",  width=12)

    for s in sessions:
        dur = ""
        if s["finished_at"] and s["started_at"]:
            try:
                start = datetime.fromisoformat(s["started_at"])
                end   = datetime.fromisoformat(s["finished_at"])
                mins  = int((end - start).total_seconds() / 60)
                dur   = f"{mins}m"
            except Exception:
                pass
        t.add_row(
            s["started_at"][:10],
            s["name"] or "—",
            dur or "—",
            str(s["set_count"] or 0),
            f"{s['volume'] or 0:.0f} kg" if s["volume"] else "—",
        )

    console.print(t)


def pr_table(prs: list[dict]) -> None:
    t = Table(title="Personal Records", box=box.SIMPLE_HEAVY, header_style=f"bold {ACCENT}")
    t.add_column("Exercise",   style="bold white", min_width=28)
    t.add_column("1RM Est.",   justify="right",    width=12)
    t.add_column("Best Set",   justify="center",   width=16)
    t.add_column("Date",       width=12)

    for row in prs:
        one_rm = ""
        if row["weight_kg"] and row["reps"]:
            # Epley formula
            est = row["weight_kg"] * (1 + row["reps"] / 30)
            one_rm = f"~{est:.1f} kg"
        best = (
            f"{row['weight_kg']}kg × {row['reps']}"
            if row["weight_kg"] and row["reps"]
            else (f"{row['reps']} reps" if row["reps"] else f"{row['duration_s']}s")
        )
        t.add_row(row["exercise"], one_rm, best, row["logged_at"][:10])

    console.print(t)


def body_stats_table(stats: list[dict]) -> None:
    t = Table(title="Body Stats", box=box.SIMPLE_HEAVY, header_style=f"bold {ACCENT}")
    t.add_column("Date",     width=12)
    t.add_column("Weight",   justify="right", width=10)
    t.add_column("Body Fat", justify="right", width=10)
    t.add_column("Waist",    justify="right", width=10)
    t.add_column("Chest",    justify="right", width=10)
    t.add_column("Arms",     justify="right", width=10)

    for s in stats:
        t.add_row(
            s["logged_at"][:10],
            f"{s['weight_kg']} kg" if s["weight_kg"] else "—",
            f"{s['body_fat_pct']}%" if s["body_fat_pct"] else "—",
            f"{s['waist_cm']} cm"  if s["waist_cm"]    else "—",
            f"{s['chest_cm']} cm"  if s["chest_cm"]    else "—",
            f"{s['arms_cm']} cm"   if s["arms_cm"]     else "—",
        )

    console.print(t)


def ascii_chart(title: str, points: list[tuple[str, float]], unit: str = "") -> None:
    """Simple sparkline-style terminal chart."""
    if not points:
        console.print("[dim]No data yet.[/dim]")
        return

    values = [v for _, v in points]
    labels = [l for l, _ in points]
    lo, hi = min(values), max(values)
    span = hi - lo or 1.0
    height = 8
    width = min(len(values), 60)
    chart_vals = values[-width:]
    chart_labs = labels[-width:]

    rows = []
    for row in range(height, 0, -1):
        threshold = lo + (row / height) * span
        line = ""
        for v in chart_vals:
            if v >= threshold:
                line += "█"
            elif v >= threshold - span / height:
                line += "▄"
            else:
                line += " "
        rows.append(line)

    console.print(f"\n[bold {ACCENT}]{title}[/bold {ACCENT}]")
    axis_hi = f"{hi:.1f}{unit}"
    axis_lo = f"{lo:.1f}{unit}"
    pad = max(len(axis_hi), len(axis_lo))
    for i, row_str in enumerate(rows):
        if i == 0:
            console.print(f"  {axis_hi:>{pad}} │[red]{row_str}[/red]")
        elif i == height - 1:
            console.print(f"  {axis_lo:>{pad}} │[red]{row_str}[/red]")
        else:
            console.print(f"  {'':>{pad}} │[red]{row_str}[/red]")

    console.print(f"  {'':>{pad}} └{'─' * len(chart_vals)}")
    # Show first and last date labels
    if chart_labs:
        first, last = chart_labs[0][:10], chart_labs[-1][:10]
        gap = len(chart_labs) - len(first) - len(last)
        if gap > 0:
            console.print(f"  {'':>{pad}}  {first}{' ' * gap}{last}")
        else:
            console.print(f"  {'':>{pad}}  {first}  {last}")
    console.print()
