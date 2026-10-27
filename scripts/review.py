"""Spaced repetition over topics and flashcards.

Usage:
  python scripts/review.py                   interactive session over everything due
  python scripts/review.py --dry-run         show what is due, change nothing
  python scripts/review.py --topic p01-t01   review one topic regardless of due date
  python scripts/review.py --cards           flashcards only
  python scripts/review.py --topics          topics only
  python scripts/review.py --limit 5         cap the session length
  python scripts/review.py --record p01-t01 correct    non-interactive single result

Interval policy, from curriculum.json review_policy:
  intervals   1, 3, 7, 14, 30 days
  correct     advance to the next interval
  incorrect   reset to the first interval
  partial     repeat the current interval and record the uncertainty

The question is always shown before the answer, and the answer is only revealed
after you commit to a rating. Self-grading only works if you grade before you look.

Standard library only. Safe on missing or malformed data: it reports and exits
nonzero rather than writing something it cannot read back.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curriculum import (  # noqa: E402
    CurriculumError,
    iter_topics,
    load_curriculum,
    load_review_schedule,
    repo_root,
    save_review_schedule,
    validate_review_schedule,
)

RESULTS = ("correct", "incorrect", "partial")
CARDS_RELPATH = "flashcards/cards.csv"
CARD_FIELDS = ("front", "back", "topic", "last_reviewed", "next_review")


# --------------------------------------------------------------------------- #
# Pure scheduling logic. No I/O, so it can be tested directly.
# --------------------------------------------------------------------------- #

def next_interval(current: int | None, result: str, intervals: list[int]) -> int:
    """Return the next interval in days.

    correct   -> the next larger interval, staying at the largest once reached
    incorrect -> back to the first interval
    partial   -> repeat the current interval, or the first if there is none
    """
    if result not in RESULTS:
        raise ValueError(f"result must be one of {RESULTS}, got {result!r}")
    if not intervals:
        raise ValueError("intervals must not be empty")

    if result == "incorrect":
        return intervals[0]
    if current is None or current not in intervals:
        # An unseen topic, or a value no longer in the policy: start over. Partial
        # and correct both land on the first interval, which is the safe direction.
        return intervals[0]
    if result == "partial":
        return current
    position = intervals.index(current)
    return intervals[min(position + 1, len(intervals) - 1)]


def apply_review(
    entry: dict[str, Any] | None,
    result: str,
    today: dt.date,
    intervals: list[int],
    note: str = "",
) -> dict[str, Any]:
    """Return a new schedule entry after a review. Pure: does not mutate the input."""
    entry = dict(entry or {})
    interval = next_interval(entry.get("interval_days"), result, intervals)
    history = list(entry.get("history") or [])
    record: dict[str, Any] = {"date": today.isoformat(), "result": result}
    if note:
        record["note"] = note
    history.append(record)
    recent = [h["result"] for h in history[-5:]]
    return {
        "last_reviewed": today.isoformat(),
        "next_review": (today + dt.timedelta(days=interval)).isoformat(),
        "interval_days": interval,
        "review_count": int(entry.get("review_count") or 0) + 1,
        "recent_performance": recent,
        # Confidence is only asserted when there is evidence for it: three
        # consecutive correct reviews. Otherwise it stays null rather than being
        # invented.
        "confidence": "high" if recent[-3:] == ["correct"] * 3 else None,
        "history": history,
    }


# --------------------------------------------------------------------------- #
# Flashcards
# --------------------------------------------------------------------------- #

def load_cards(root: Path) -> list[dict[str, str]]:
    path = root / CARDS_RELPATH
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = set(CARD_FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise CurriculumError(
                f"{CARDS_RELPATH} is missing column(s): {', '.join(sorted(missing))}"
            )
        return [dict(row) for row in reader if (row.get("front") or "").strip()]


def save_cards(root: Path, cards: list[dict[str, str]]) -> None:
    path = root / CARDS_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CARD_FIELDS))
        writer.writeheader()
        for card in cards:
            writer.writerow({field: card.get(field, "") for field in CARD_FIELDS})


def card_is_due(card: dict[str, str], today: dt.date) -> bool:
    value = (card.get("next_review") or "").strip()
    if not value:
        return True
    try:
        return dt.date.fromisoformat(value) <= today
    except ValueError:
        # An unparseable date is treated as due rather than silently skipped.
        return True


def card_interval(card: dict[str, str]) -> int | None:
    last = (card.get("last_reviewed") or "").strip()
    nxt = (card.get("next_review") or "").strip()
    if not last or not nxt:
        return None
    try:
        return (dt.date.fromisoformat(nxt) - dt.date.fromisoformat(last)).days
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Session
# --------------------------------------------------------------------------- #

def due_topic_ids(
    doc: dict[str, Any], schedule: dict[str, Any], today: dt.date
) -> list[tuple[str, int]]:
    """Topic ids whose review is due, most overdue first."""
    known = {t["id"] for _, t in iter_topics(doc)}
    out = []
    for topic_id, entry in (schedule.get("topics") or {}).items():
        if topic_id not in known:
            continue
        value = entry.get("next_review")
        if not value:
            continue
        try:
            when = dt.date.fromisoformat(value)
        except ValueError:
            continue
        if when <= today:
            out.append((topic_id, (today - when).days))
    out.sort(key=lambda row: (-row[1], row[0]))
    return out


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit("review session cancelled")


def rate() -> str | None:
    """Ask for a rating. Returns None to skip, raises SystemExit to quit."""
    while True:
        answer = ask("  rate [c]orrect / [i]ncorrect / [p]artial / [s]kip / [q]uit: ")
        choice = answer.strip().lower()
        if choice in ("c", "correct"):
            return "correct"
        if choice in ("i", "incorrect"):
            return "incorrect"
        if choice in ("p", "partial"):
            return "partial"
        if choice in ("s", "skip", ""):
            return None
        if choice in ("q", "quit"):
            raise SystemExit(0)
        print("  please answer c, i, p, s or q")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Spaced repetition review session.")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what is due and change nothing")
    parser.add_argument("--topic", help="review this topic id regardless of its due date")
    parser.add_argument("--cards", action="store_true", help="flashcards only")
    parser.add_argument("--topics", action="store_true", help="topics only")
    parser.add_argument("--limit", type=int, help="maximum number of items this session")
    parser.add_argument("--record", nargs=2, metavar=("TOPIC_ID", "RESULT"),
                        help="record one result without prompting")
    parser.add_argument("--date", help="treat this ISO date as today (for testing)")
    parser.add_argument("--root", help="repository root to operate on (default: auto-detect)")
    args = parser.parse_args(argv)

    try:
        root = Path(args.root) if args.root else repo_root()
        doc = load_curriculum(root)
        schedule = load_review_schedule(root)
        cards = load_cards(root)
    except CurriculumError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    problems = validate_review_schedule(doc, schedule)
    if problems.errors:
        print("ERROR: tracker/review_schedule.json is not valid:", file=sys.stderr)
        for message in problems.errors:
            print(f"  - {message}", file=sys.stderr)
        print("\nNothing was written. Fix the file and run again.", file=sys.stderr)
        return 2

    try:
        today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        print(f"ERROR: --date {args.date!r} is not an ISO date", file=sys.stderr)
        return 2

    intervals = list((doc.get("review_policy") or {}).get("intervals_days") or [])
    topics = {t["id"]: t for _, t in iter_topics(doc)}
    schedule.setdefault("topics", {})

    # Non-interactive single result, for automation and tests.
    if args.record:
        topic_id, result = args.record
        if topic_id not in topics:
            print(f"ERROR: unknown topic id {topic_id!r}", file=sys.stderr)
            return 2
        if result not in RESULTS:
            print(f"ERROR: result must be one of {', '.join(RESULTS)}", file=sys.stderr)
            return 2
        entry = apply_review(schedule["topics"].get(topic_id), result, today, intervals)
        if args.dry_run:
            print(f"dry run: {topic_id} would move to interval {entry['interval_days']}d, "
                  f"next review {entry['next_review']}")
            return 0
        schedule["topics"][topic_id] = entry
        save_review_schedule(root, schedule)
        print(f"recorded {result} for {topic_id}: interval {entry['interval_days']}d, "
              f"next review {entry['next_review']}")
        return 0

    want_topics = not args.cards
    want_cards = not args.topics

    due_topics = (
        [(args.topic, 0)] if args.topic
        else (due_topic_ids(doc, schedule, today) if want_topics else [])
    )
    if args.topic and args.topic not in topics:
        print(f"ERROR: unknown topic id {args.topic!r}", file=sys.stderr)
        return 2

    due_cards = [c for c in cards if card_is_due(c, today)] if want_cards else []
    if args.limit is not None:
        due_topics = due_topics[: args.limit]
        due_cards = due_cards[: max(0, args.limit - len(due_topics))]

    print(f"Review session for {today.isoformat()}")
    print(f"  topics due:     {len(due_topics)}")
    print(f"  flashcards due: {len(due_cards)}")

    if not due_topics and not due_cards:
        print()
        print("Nothing is due. Reviews are scheduled after a topic's first assessment,")
        print("so an empty queue early on is expected, not a bug.")
        return 0

    if args.dry_run:
        print()
        for topic_id, overdue in due_topics:
            label = "today" if overdue == 0 else f"{overdue}d overdue"
            print(f"  topic  {topic_id}  {topics[topic_id]['title'][:50]:50s} {label}")
        for card in due_cards:
            print(f"  card   {card.get('topic', '-'):12s} {card['front'][:58]}")
        print()
        print("dry run: nothing was written")
        return 0

    if not sys.stdin.isatty():
        print()
        print("ERROR: no interactive terminal. Use --dry-run to list what is due, or",
              file=sys.stderr)
        print("       --record TOPIC_ID RESULT to record one result non-interactively.",
              file=sys.stderr)
        return 2

    reviewed = 0
    for topic_id, overdue in due_topics:
        topic = topics[topic_id]
        print()
        print("=" * 68)
        print(f"TOPIC  {topic_id}  ({'today' if overdue == 0 else f'{overdue}d overdue'})")
        print(f"  {topic['title']}")
        print()
        print("  Answer out loud before rating yourself:")
        for objective in topic["learning_objectives"]:
            print(f"    - {objective}")
        result = rate()
        if result is None:
            continue
        print(f"  Reference: {topic['summary']}")
        print(f"  Lesson:    {topic['lesson_path']}")
        schedule["topics"][topic_id] = apply_review(
            schedule["topics"].get(topic_id), result, today, intervals
        )
        entry = schedule["topics"][topic_id]
        print(f"  -> interval {entry['interval_days']}d, next review {entry['next_review']}")
        reviewed += 1

    for card in due_cards:
        print()
        print("-" * 68)
        print(f"CARD   [{card.get('topic', '-')}]")
        print(f"  {card['front']}")
        result = rate()
        if result is None:
            continue
        print(f"  Answer: {card['back']}")
        interval = next_interval(card_interval(card), result, intervals)
        card["last_reviewed"] = today.isoformat()
        card["next_review"] = (today + dt.timedelta(days=interval)).isoformat()
        print(f"  -> interval {interval}d, next review {card['next_review']}")
        reviewed += 1

    if reviewed:
        save_review_schedule(root, schedule)
        save_cards(root, cards)
    print()
    print(f"Reviewed {reviewed} item(s). Schedule saved." if reviewed
          else "Nothing rated, so nothing was written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
