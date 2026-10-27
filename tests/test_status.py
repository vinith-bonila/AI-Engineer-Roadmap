"""Tests for the status report: the numbers, the priority logic and the CLI."""
from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import curriculum as cur
import status as st

TODAY = dt.date(2026, 10, 27)


# --------------------------------------------------------------------------- #
# Numbers
# --------------------------------------------------------------------------- #

def test_collect_reports_zero_progress_on_a_fresh_curriculum(doc):
    data = st.collect(doc, {"topics": {}}, TODAY)
    assert data["overall"]["done"] == 0
    assert data["overall"]["topic_percent"] == 0.0
    assert data["overall"]["total"] == sum(len(p["topics"]) for p in doc["phases"])
    assert data["in_progress"] == []
    assert data["needs_revision"] == []


def test_completing_a_topic_moves_both_metrics(doc):
    first = doc["phases"][0]["topics"][0]
    first["status"] = "done"
    doc["phases"][0]["status"] = cur.derive_phase_status(doc["phases"][0]["topics"])
    data = st.collect(doc, {"topics": {}}, TODAY)
    assert data["overall"]["done"] == 1
    assert data["overall"]["topic_percent"] > 0
    assert data["overall"]["effort_percent"] > 0
    assert data["phases"][0]["status"] == "in_progress"


def test_needs_revision_is_listed_and_not_counted_as_progress(doc):
    topic = doc["phases"][0]["topics"][0]
    topic["status"] = "needs_revision"
    data = st.collect(doc, {"topics": {}}, TODAY)
    assert data["overall"]["done"] == 0
    assert data["needs_revision"] == [{"id": topic["id"], "title": topic["title"]}]


def test_effort_weighting_differs_from_topic_counting(doc):
    """Finishing a long topic should move the effort metric more than a short one."""
    phase = doc["phases"][0]
    longest = max(phase["topics"], key=lambda t: t["estimated_minutes"])
    shortest = min(phase["topics"], key=lambda t: t["estimated_minutes"])
    assert longest["estimated_minutes"] != shortest["estimated_minutes"]

    longest["status"] = "done"
    with_long = st.collect(doc, {"topics": {}}, TODAY)["overall"]
    longest["status"] = "not_started"
    shortest["status"] = "done"
    with_short = st.collect(doc, {"topics": {}}, TODAY)["overall"]

    assert with_long["topic_percent"] == with_short["topic_percent"]
    assert with_long["effort_percent"] > with_short["effort_percent"]


def test_due_reviews_are_sorted_most_overdue_first(doc):
    ids = [t["id"] for _, t in cur.iter_topics(doc)][:3]
    schedule = {"topics": {
        ids[0]: {"next_review": "2026-10-26"},
        ids[1]: {"next_review": "2026-10-10"},
        ids[2]: {"next_review": "2026-12-01"},
    }}
    rows = st.due_reviews(doc, schedule, TODAY)
    assert [r[0] for r in rows] == [ids[1], ids[0]]
    assert rows[0][2] == 17


def test_future_reviews_are_not_due(doc):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {first: {"next_review": "2026-10-28"}}}
    assert st.due_reviews(doc, schedule, TODAY) == []


# --------------------------------------------------------------------------- #
# Priority logic
# --------------------------------------------------------------------------- #

def test_due_reviews_outrank_everything_else():
    message = st.recommend(
        due=[{"id": "p01-t01", "title": "x", "days_overdue": 4}],
        needs_revision=[{"id": "p01-t02", "title": "y"}],
        in_progress=[{"id": "p01-t03", "title": "z"}],
        actionable=[{"id": "p01-t04", "title": "w", "scaffolded": True}],
    )
    assert "review.py" in message and "4 day" in message


def test_revision_outranks_starting_something_new():
    message = st.recommend(
        due=[],
        needs_revision=[{"id": "p01-t02", "title": "Lists"}],
        in_progress=[{"id": "p01-t03", "title": "Dicts"}],
        actionable=[{"id": "p01-t04", "title": "Sets", "scaffolded": True}],
    )
    assert "Revise p01-t02" in message


def test_finishing_in_progress_outranks_starting_new():
    message = st.recommend(
        due=[], needs_revision=[],
        in_progress=[{"id": "p01-t03", "title": "Dicts"}],
        actionable=[{"id": "p01-t04", "title": "Sets", "scaffolded": True}],
    )
    assert "Finish p01-t03" in message


def test_unscaffolded_next_topic_tells_you_to_say_start_lesson():
    message = st.recommend(
        due=[], needs_revision=[], in_progress=[],
        actionable=[{"id": "p02-t01", "title": "Vectors", "scaffolded": False}],
    )
    assert "start lesson" in message


def test_nothing_left_is_stated_plainly():
    message = st.recommend(due=[], needs_revision=[], in_progress=[], actionable=[])
    assert "complete" in message


def test_the_fresh_repository_recommends_the_first_lesson(doc):
    data = st.collect(doc, {"topics": {}}, TODAY)
    assert "p01-t01" in data["recommended_action"]


# --------------------------------------------------------------------------- #
# Progress bar rendering
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("percent,filled", [(0, 0), (50, 14), (100, 28)])
def test_bar_fills_proportionally(percent, filled):
    rendered = st.bar(percent)
    assert rendered.count("#") == filled
    assert len(rendered) == st.BAR_WIDTH + 2


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

@pytest.fixture
def fake_repo(root: Path, tmp_path: Path) -> Path:
    fake = tmp_path / "repo"
    for sub in ("scripts", "roadmap", "tracker"):
        (fake / sub).mkdir(parents=True)
    for name in ("curriculum.py", "status.py"):
        shutil.copy(root / "scripts" / name, fake / "scripts" / name)
    shutil.copy(root / "roadmap" / "curriculum.json", fake / "roadmap" / "curriculum.json")
    shutil.copy(root / "tracker" / "review_schedule.json",
                fake / "tracker" / "review_schedule.json")
    return fake


def _status(fake: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(fake / "scripts" / "status.py"), "--root", str(fake), *args],
        capture_output=True, text=True, cwd=str(fake), input="",
    )


def test_default_output_reports_overall_and_every_phase(fake_repo: Path, raw_curriculum):
    result = _status(fake_repo)
    assert result.returncode == 0, result.stderr
    assert "overall" in result.stdout
    for phase in raw_curriculum["phases"]:
        assert phase["title"][:40] in result.stdout
    assert "Next action" in result.stdout


def test_phase_filter_shows_one_phase_only(fake_repo: Path, raw_curriculum):
    result = _status(fake_repo, "--phase", "5")
    assert result.returncode == 0
    assert raw_curriculum["phases"][4]["title"][:40] in result.stdout
    assert raw_curriculum["phases"][0]["title"][:40] not in result.stdout


def test_unknown_phase_number_fails_clearly(fake_repo: Path):
    result = _status(fake_repo, "--phase", "99")
    assert result.returncode == 2
    assert "no phase numbered 99" in result.stderr


def test_json_output_is_parseable(fake_repo: Path, raw_curriculum):
    result = _status(fake_repo, "--json", "--date", "2026-10-27")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["as_of"] == "2026-10-27"
    assert data["overall"]["total"] == sum(
        len(p["topics"]) for p in raw_curriculum["phases"]
    )
    assert len(data["phases"]) == len(raw_curriculum["phases"])


def test_show_revision_is_empty_and_says_so(fake_repo: Path):
    result = _status(fake_repo, "--show-revision")
    assert result.returncode == 0
    assert "Nothing needs revision" in result.stdout


def test_due_flag_reports_an_empty_queue(fake_repo: Path):
    result = _status(fake_repo, "--due")
    assert result.returncode == 0
    assert "No reviews are due" in result.stdout


def test_missing_curriculum_exits_two(tmp_path: Path, root: Path):
    empty = tmp_path / "empty"
    (empty / "scripts").mkdir(parents=True)
    for name in ("curriculum.py", "status.py"):
        shutil.copy(root / "scripts" / name, empty / "scripts" / name)
    result = subprocess.run(
        [sys.executable, str(empty / "scripts" / "status.py"), "--root", str(empty)],
        capture_output=True, text=True, cwd=str(empty), input="",
    )
    assert result.returncode == 2
    assert "cannot read" in result.stderr
