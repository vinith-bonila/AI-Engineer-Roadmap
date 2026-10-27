"""Report learning progress from roadmap/curriculum.json and tracker/review_schedule.json.

Usage:
  python scripts/status.py                  overall and per-phase progress
  python scripts/status.py --phase 1        one phase in detail
  python scripts/status.py --show-revision  only the topics needing revision
  python scripts/status.py --due            only the reviews that are due
  python scripts/status.py --json           machine-readable output

Progress is reported two ways, both defined in curriculum.json progress_policy:
  topic completion   done topics / total topics          (the primary metric)
  effort weighted    done lesson minutes / all minutes   (secondary)

Only status 'done' counts as complete. 'needs_revision' counts as incomplete, on
purpose: a topic you half know is not progress you can build on.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curriculum import (  # noqa: E402
    CurriculumError,
    iter_phases,
    iter_topics,
    load_curriculum,
    load_review_schedule,
    next_actionable_topics,
    overall_progress,
    phase_progress,
    repo_root,
)

BAR_WIDTH = 28


def bar(percent: float, width: int = BAR_WIDTH) -> str:
    filled = int(round(percent / 100 * width))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def due_reviews(
    doc: dict[str, Any], schedule: dict[str, Any], today: dt.date
) -> list[tuple[str, str, int]]:
    """Return (topic_id, title, days_overdue), most overdue first."""
    titles = {t["id"]: t["title"] for _, t in iter_topics(doc)}
    out = []
    for topic_id, entry in (schedule.get("topics") or {}).items():
        nxt = entry.get("next_review")
        if not nxt or topic_id not in titles:
            continue
        try:
            when = dt.date.fromisoformat(nxt)
        except ValueError:
            continue
        if when <= today:
            out.append((topic_id, titles[topic_id], (today - when).days))
    out.sort(key=lambda row: (-row[2], row[0]))
    return out


def collect(doc: dict[str, Any], schedule: dict[str, Any], today: dt.date) -> dict[str, Any]:
    overall = overall_progress(doc)
    phases = []
    for phase in iter_phases(doc):
        p = phase_progress(phase)
        phases.append({
            "id": phase["id"],
            "order": phase["order"],
            "title": phase["title"],
            "status": phase["status"],
            "done": p.done,
            "total": p.total,
            "topic_percent": round(p.topic_percent, 1),
            "effort_percent": round(p.effort_percent, 1),
        })
    in_progress = [
        {"id": t["id"], "title": t["title"]}
        for _, t in iter_topics(doc) if t["status"] == "in_progress"
    ]
    needs_revision = [
        {"id": t["id"], "title": t["title"]}
        for _, t in iter_topics(doc) if t["status"] == "needs_revision"
    ]
    actionable = [
        {"id": t["id"], "title": t["title"], "scaffolded": t["scaffolded"]}
        for t in next_actionable_topics(doc, limit=5)
    ]
    due = [
        {"id": tid, "title": title, "days_overdue": overdue}
        for tid, title, overdue in due_reviews(doc, schedule, today)
    ]
    return {
        "as_of": today.isoformat(),
        "overall": {
            "done": overall.done,
            "total": overall.total,
            "topic_percent": round(overall.topic_percent, 1),
            "effort_percent": round(overall.effort_percent, 1),
            "lesson_hours_total": round(overall.minutes_total / 60, 1),
            "lesson_hours_done": round(overall.minutes_done / 60, 1),
        },
        "phases": phases,
        "in_progress": in_progress,
        "needs_revision": needs_revision,
        "next_actionable": actionable,
        "due_reviews": due,
        "recommended_action": recommend(due, needs_revision, in_progress, actionable),
    }


def recommend(
    due: list[dict[str, Any]],
    needs_revision: list[dict[str, Any]],
    in_progress: list[dict[str, Any]],
    actionable: list[dict[str, Any]],
) -> str:
    """Deterministic priority order: reviews, then revision, then finish, then start."""
    if due:
        return (
            f"Run 'python scripts/review.py' first. {len(due)} review(s) are due, "
            f"the most overdue by {due[0]['days_overdue']} day(s)."
        )
    if needs_revision:
        first = needs_revision[0]
        return f"Revise {first['id']} {first['title']} before starting anything new."
    if in_progress:
        first = in_progress[0]
        return f"Finish {first['id']} {first['title']}, which is still in progress."
    if actionable:
        first = actionable[0]
        if not first["scaffolded"]:
            return (
                f"Say 'start lesson' to scaffold and begin {first['id']} {first['title']}."
            )
        return f"Start {first['id']} {first['title']}; its lesson is already scaffolded."
    return "Everything with satisfied prerequisites is complete."


def render(data: dict[str, Any], phase_filter: int | None) -> None:
    ov = data["overall"]
    print("AI Engineering Curriculum - progress")
    print(f"as of {data['as_of']}")
    print()
    print(f"  overall   {bar(ov['topic_percent'])} {ov['done']}/{ov['total']} topics "
          f"({ov['topic_percent']}%)")
    print(f"  effort    {bar(ov['effort_percent'])} {ov['effort_percent']}% of "
          f"{ov['lesson_hours_total']} lesson hours")
    print()
    print("Phases")
    for phase in data["phases"]:
        if phase_filter is not None and phase["order"] != phase_filter:
            continue
        print(f"  {phase['order']:2d}. {phase['title'][:46]:46s} "
              f"{bar(phase['topic_percent'], 16)} {phase['done']:3d}/{phase['total']:<3d} "
              f"{phase['status']}")

    if data["in_progress"]:
        print()
        print("In progress")
        for topic in data["in_progress"]:
            print(f"  {topic['id']}  {topic['title']}")

    if data["needs_revision"]:
        print()
        print("Needs revision")
        for topic in data["needs_revision"]:
            print(f"  {topic['id']}  {topic['title']}")

    if data["due_reviews"]:
        print()
        print("Reviews due")
        for row in data["due_reviews"]:
            overdue = "today" if row["days_overdue"] == 0 else f"{row['days_overdue']}d overdue"
            print(f"  {row['id']}  {row['title'][:46]:46s} {overdue}")

    if data["next_actionable"]:
        print()
        print("Available now (prerequisites satisfied)")
        for topic in data["next_actionable"]:
            flag = "" if topic["scaffolded"] else "  (not scaffolded yet)"
            print(f"  {topic['id']}  {topic['title']}{flag}")

    print()
    print("Next action")
    print(f"  {data['recommended_action']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report learning progress.")
    parser.add_argument("--phase", type=int, help="show only this phase number")
    parser.add_argument("--show-revision", action="store_true",
                        help="list only the topics needing revision")
    parser.add_argument("--due", action="store_true",
                        help="list only the reviews that are due")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--date", help="treat this ISO date as today (for testing)")
    parser.add_argument("--root", help="repository root to operate on (default: auto-detect)")
    args = parser.parse_args(argv)

    try:
        root = Path(args.root) if args.root else repo_root()
        doc = load_curriculum(root)
        schedule = load_review_schedule(root)
    except CurriculumError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        print(f"ERROR: --date {args.date!r} is not an ISO date (YYYY-MM-DD)",
              file=sys.stderr)
        return 2

    if args.phase is not None and not any(
        p["order"] == args.phase for p in doc["phases"]
    ):
        print(f"ERROR: no phase numbered {args.phase}", file=sys.stderr)
        return 2

    data = collect(doc, schedule, today)

    if args.json:
        print(json.dumps(data, indent=2))
        return 0

    if args.show_revision:
        if not data["needs_revision"]:
            print("Nothing needs revision.")
        for topic in data["needs_revision"]:
            print(f"{topic['id']}  {topic['title']}")
        return 0

    if args.due:
        if not data["due_reviews"]:
            print("No reviews are due.")
        for row in data["due_reviews"]:
            print(f"{row['id']}  {row['title']}  {row['days_overdue']}d overdue")
        return 0

    render(data, args.phase)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
