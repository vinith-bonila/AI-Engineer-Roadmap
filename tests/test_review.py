"""Tests for the spaced repetition scheduler and its CLI."""
from __future__ import annotations

import csv
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import review as rv

INTERVALS = [1, 3, 7, 14, 30]
TODAY = dt.date(2026, 10, 27)


# --------------------------------------------------------------------------- #
# Interval policy
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("current,expected", [
    (None, 1), (1, 3), (3, 7), (7, 14), (14, 30),
])
def test_correct_advances_one_step(current, expected):
    assert rv.next_interval(current, "correct", INTERVALS) == expected


def test_correct_at_the_largest_interval_stays_there():
    assert rv.next_interval(30, "correct", INTERVALS) == 30


@pytest.mark.parametrize("current", [None, 1, 3, 7, 14, 30])
def test_incorrect_always_resets_to_one_day(current):
    assert rv.next_interval(current, "incorrect", INTERVALS) == 1


@pytest.mark.parametrize("current", [1, 3, 7, 14, 30])
def test_partial_repeats_the_current_interval(current):
    assert rv.next_interval(current, "partial", INTERVALS) == current, (
        "a half-remembered answer is not progress and not failure"
    )


def test_partial_on_an_unseen_topic_starts_at_the_first_interval():
    assert rv.next_interval(None, "partial", INTERVALS) == 1


def test_an_interval_no_longer_in_policy_restarts_safely():
    assert rv.next_interval(5, "correct", INTERVALS) == 1, (
        "a stale interval must not silently become the largest one"
    )


def test_unknown_result_is_rejected():
    with pytest.raises(ValueError):
        rv.next_interval(1, "maybe", INTERVALS)


def test_empty_interval_policy_is_rejected():
    with pytest.raises(ValueError):
        rv.next_interval(1, "correct", [])


# --------------------------------------------------------------------------- #
# apply_review
# --------------------------------------------------------------------------- #

def test_first_review_creates_a_complete_entry():
    entry = rv.apply_review(None, "correct", TODAY, INTERVALS)
    assert entry["last_reviewed"] == "2026-10-27"
    assert entry["next_review"] == "2026-10-28"
    assert entry["interval_days"] == 1
    assert entry["review_count"] == 1
    assert entry["recent_performance"] == ["correct"]
    assert entry["history"] == [{"date": "2026-10-27", "result": "correct"}]


def test_next_review_is_today_plus_the_interval():
    entry = rv.apply_review({"interval_days": 7, "review_count": 3}, "correct",
                            TODAY, INTERVALS)
    assert entry["interval_days"] == 14
    assert entry["next_review"] == (TODAY + dt.timedelta(days=14)).isoformat()
    assert entry["review_count"] == 4


def test_apply_review_does_not_mutate_the_input():
    original = {"interval_days": 3, "review_count": 1, "history": []}
    snapshot = json.dumps(original, sort_keys=True)
    rv.apply_review(original, "incorrect", TODAY, INTERVALS)
    assert json.dumps(original, sort_keys=True) == snapshot


def test_history_accumulates_in_order():
    entry = None
    for result in ("correct", "incorrect", "partial"):
        entry = rv.apply_review(entry, result, TODAY, INTERVALS)
    assert [h["result"] for h in entry["history"]] == ["correct", "incorrect", "partial"]
    assert entry["review_count"] == 3


def test_recent_performance_keeps_the_last_five_only():
    entry = None
    for _ in range(8):
        entry = rv.apply_review(entry, "correct", TODAY, INTERVALS)
    assert len(entry["recent_performance"]) == 5
    assert len(entry["history"]) == 8


def test_confidence_requires_three_consecutive_correct_reviews():
    entry = rv.apply_review(None, "correct", TODAY, INTERVALS)
    assert entry["confidence"] is None
    entry = rv.apply_review(entry, "correct", TODAY, INTERVALS)
    assert entry["confidence"] is None
    entry = rv.apply_review(entry, "correct", TODAY, INTERVALS)
    assert entry["confidence"] == "high"
    entry = rv.apply_review(entry, "partial", TODAY, INTERVALS)
    assert entry["confidence"] is None, "one shaky review withdraws the claim"


def test_a_note_is_recorded_when_given():
    entry = rv.apply_review(None, "partial", TODAY, INTERVALS, note="mixed up top-k")
    assert entry["history"][0]["note"] == "mixed up top-k"


def test_no_note_key_when_there_is_no_note():
    entry = rv.apply_review(None, "correct", TODAY, INTERVALS)
    assert "note" not in entry["history"][0]


# --------------------------------------------------------------------------- #
# Due detection
# --------------------------------------------------------------------------- #

def test_due_topics_are_sorted_most_overdue_first(doc):
    ids = [t["id"] for _, t in __import__("curriculum").iter_topics(doc)][:3]
    schedule = {"topics": {
        ids[0]: {"next_review": "2026-10-26"},
        ids[1]: {"next_review": "2026-10-20"},
        ids[2]: {"next_review": "2026-11-30"},
    }}
    due = rv.due_topic_ids(doc, schedule, TODAY)
    assert [row[0] for row in due] == [ids[1], ids[0]]
    assert due[0][1] == 7


def test_a_review_due_today_counts_as_due(doc):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {first: {"next_review": TODAY.isoformat()}}}
    assert rv.due_topic_ids(doc, schedule, TODAY) == [(first, 0)]


def test_unknown_and_unparseable_entries_are_skipped_not_crashed(doc):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {
        "p99-t99": {"next_review": "2026-10-01"},
        first: {"next_review": "not-a-date"},
    }}
    assert rv.due_topic_ids(doc, schedule, TODAY) == []


# --------------------------------------------------------------------------- #
# Flashcards
# --------------------------------------------------------------------------- #

def test_a_card_never_reviewed_is_due():
    assert rv.card_is_due({"next_review": ""}, TODAY) is True


def test_a_card_scheduled_in_the_future_is_not_due():
    assert rv.card_is_due({"next_review": "2026-12-01"}, TODAY) is False


def test_a_card_with_a_corrupt_date_is_treated_as_due():
    assert rv.card_is_due({"next_review": "31/12/2026"}, TODAY) is True


def test_card_interval_is_derived_from_its_two_dates():
    assert rv.card_interval(
        {"last_reviewed": "2026-10-20", "next_review": "2026-10-27"}
    ) == 7
    assert rv.card_interval({"last_reviewed": "", "next_review": ""}) is None


def test_cards_round_trip_through_csv_with_commas_and_quotes(tmp_path: Path):
    cards = [{
        "front": 'What does "top-p" do, exactly?',
        "back": "It keeps the smallest set of tokens whose probabilities sum to p.",
        "topic": "p04-t06",
        "last_reviewed": "2026-10-27",
        "next_review": "2026-10-30",
    }]
    rv.save_cards(tmp_path, cards)
    assert rv.load_cards(tmp_path) == cards


def test_blank_rows_are_ignored_when_loading(tmp_path: Path):
    path = tmp_path / "flashcards" / "cards.csv"
    path.parent.mkdir(parents=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(list(rv.CARD_FIELDS))
        writer.writerow(["real", "answer", "p01-t01", "", ""])
        writer.writerow(["", "", "", "", ""])
    assert len(rv.load_cards(tmp_path)) == 1


def test_a_missing_column_is_reported_clearly(tmp_path: Path):
    path = tmp_path / "flashcards" / "cards.csv"
    path.parent.mkdir(parents=True)
    path.write_text("front,back\nq,a\n", encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        rv.load_cards(tmp_path)
    assert "missing column" in str(excinfo.value)


def test_missing_cards_file_is_an_empty_deck(tmp_path: Path):
    assert rv.load_cards(tmp_path) == []


def test_the_shipped_deck_loads_and_points_at_real_topics(root: Path, doc):
    cards = rv.load_cards(root)
    assert cards, "the repository ships a starter deck"
    known = {t["id"] for _, t in __import__("curriculum").iter_topics(doc)}
    for card in cards:
        assert card["topic"] in known, f"card points at unknown topic {card['topic']}"
        assert card["back"].strip(), "a card with no answer teaches nothing"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

@pytest.fixture
def fake_repo(root: Path, tmp_path: Path) -> Path:
    """A throwaway copy, so CLI tests never touch the real tracker files."""
    fake = tmp_path / "repo"
    for sub in ("scripts", "roadmap", "tracker", "flashcards"):
        (fake / sub).mkdir(parents=True)
    for name in ("curriculum.py", "review.py", "status.py"):
        shutil.copy(root / "scripts" / name, fake / "scripts" / name)
    shutil.copy(root / "roadmap" / "curriculum.json", fake / "roadmap" / "curriculum.json")
    shutil.copy(root / "tracker" / "review_schedule.json",
                fake / "tracker" / "review_schedule.json")
    shutil.copy(root / "flashcards" / "cards.csv", fake / "flashcards" / "cards.csv")
    return fake


def _review(fake: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(fake / "scripts" / "review.py"), "--root", str(fake), *args],
        capture_output=True, text=True, cwd=str(fake), input="",
    )


def test_record_writes_the_schedule(fake_repo: Path):
    result = _review(fake_repo, "--record", "p01-t01", "correct", "--date", "2026-10-27")
    assert result.returncode == 0, result.stderr
    schedule = json.loads(
        (fake_repo / "tracker" / "review_schedule.json").read_text(encoding="utf-8")
    )
    entry = schedule["topics"]["p01-t01"]
    assert entry["interval_days"] == 1
    assert entry["next_review"] == "2026-10-28"


def test_two_correct_reviews_advance_the_interval(fake_repo: Path):
    _review(fake_repo, "--record", "p01-t01", "correct", "--date", "2026-10-27")
    _review(fake_repo, "--record", "p01-t01", "correct", "--date", "2026-10-28")
    schedule = json.loads(
        (fake_repo / "tracker" / "review_schedule.json").read_text(encoding="utf-8")
    )
    entry = schedule["topics"]["p01-t01"]
    assert entry["interval_days"] == 3
    assert entry["next_review"] == "2026-10-31"
    assert entry["review_count"] == 2


def test_an_incorrect_review_resets_a_long_interval(fake_repo: Path):
    for date in ("2026-10-01", "2026-10-02", "2026-10-05"):
        _review(fake_repo, "--record", "p01-t01", "correct", "--date", date)
    _review(fake_repo, "--record", "p01-t01", "incorrect", "--date", "2026-10-12")
    schedule = json.loads(
        (fake_repo / "tracker" / "review_schedule.json").read_text(encoding="utf-8")
    )
    assert schedule["topics"]["p01-t01"]["interval_days"] == 1


def test_dry_run_writes_nothing(fake_repo: Path):
    path = fake_repo / "tracker" / "review_schedule.json"
    before = path.read_text(encoding="utf-8")
    result = _review(fake_repo, "--record", "p01-t01", "correct",
                     "--date", "2026-10-27", "--dry-run")
    assert result.returncode == 0
    assert "dry run" in result.stdout
    assert path.read_text(encoding="utf-8") == before


def test_dry_run_lists_what_is_due(fake_repo: Path):
    _review(fake_repo, "--record", "p01-t01", "correct", "--date", "2026-10-27")
    result = _review(fake_repo, "--dry-run", "--date", "2026-11-10")
    assert result.returncode == 0
    assert "p01-t01" in result.stdout
    assert "nothing was written" in result.stdout


def test_empty_queue_is_reported_as_normal_not_as_an_error(fake_repo: Path):
    result = _review(fake_repo, "--topics", "--dry-run", "--date", "2026-10-27")
    assert result.returncode == 0
    assert "Nothing is due" in result.stdout


def test_unknown_topic_is_rejected(fake_repo: Path):
    result = _review(fake_repo, "--record", "p99-t99", "correct")
    assert result.returncode == 2
    assert "unknown topic id" in result.stderr


def test_invalid_result_is_rejected(fake_repo: Path):
    result = _review(fake_repo, "--record", "p01-t01", "sort-of")
    assert result.returncode == 2
    assert "result must be one of" in result.stderr


def test_bad_date_is_rejected(fake_repo: Path):
    result = _review(fake_repo, "--dry-run", "--date", "27-10-2026")
    assert result.returncode == 2
    assert "not an ISO date" in result.stderr


def test_a_corrupt_schedule_refuses_to_write(fake_repo: Path):
    (fake_repo / "tracker" / "review_schedule.json").write_text(
        json.dumps({"topics": {"p01-t01": {"next_review": "27/10/2026"}}}),
        encoding="utf-8",
    )
    result = _review(fake_repo, "--record", "p01-t01", "correct", "--date", "2026-10-27")
    assert result.returncode == 2
    assert "not valid" in result.stderr
    assert "Nothing was written" in result.stderr


def test_non_interactive_session_explains_the_alternatives(fake_repo: Path):
    _review(fake_repo, "--record", "p01-t01", "correct", "--date", "2026-10-27")
    result = _review(fake_repo, "--topics", "--date", "2026-11-10")
    assert result.returncode == 2
    assert "--dry-run" in result.stderr and "--record" in result.stderr


def test_limit_caps_the_session(fake_repo: Path):
    result = _review(fake_repo, "--cards", "--dry-run", "--limit", "2",
                     "--date", "2026-10-27")
    assert result.returncode == 0
    assert result.stdout.count("  card   ") == 2
