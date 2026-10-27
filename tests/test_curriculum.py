"""Tests for the curriculum data and its validator.

These do not assert that files exist. They assert that the validator catches the
mistakes a human editing curriculum.json by hand would actually make.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import curriculum as cur


# --------------------------------------------------------------------------- #
# The real file must be valid
# --------------------------------------------------------------------------- #

def test_real_curriculum_validates_cleanly(doc, root):
    result = cur.validate(doc, root)
    assert result.ok, "roadmap/curriculum.json has validation errors:\n" + "\n".join(
        result.errors
    )


def test_real_review_schedule_validates_cleanly(doc, root):
    schedule = cur.load_review_schedule(root)
    result = cur.validate_review_schedule(doc, schedule)
    assert result.ok, "\n".join(result.errors)


def test_everything_starts_not_started_until_assessed(doc):
    """A topic with any other status must carry evidence. Nothing is done by default."""
    for _, topic in cur.iter_topics(doc):
        if topic["status"] == "done":
            threshold = cur.quiz_threshold(doc, topic["id"].split("-")[0])
            ok, missing = cur.evidence_complete(topic, threshold)
            assert ok, f"{topic['id']} is done without evidence: {missing}"


def test_ids_and_slugs_are_globally_unique(doc):
    topic_ids = [t["id"] for _, t in cur.iter_topics(doc)]
    slugs = [t["slug"] for _, t in cur.iter_topics(doc)]
    lesson_ids = [t["lesson_id"] for _, t in cur.iter_topics(doc)]
    assert len(topic_ids) == len(set(topic_ids))
    assert len(slugs) == len(set(slugs))
    assert len(lesson_ids) == len(set(lesson_ids))


def test_every_topic_has_a_phase_prefixed_id(doc):
    for phase, topic in cur.iter_topics(doc):
        assert topic["id"].startswith(phase["id"] + "-"), (
            f"{topic['id']} does not belong to phase {phase['id']} by its id"
        )


def test_lesson_paths_live_under_their_phase_directory(doc):
    for phase, topic in cur.iter_topics(doc):
        for field in cur.PATH_FIELDS:
            assert topic[field].startswith(phase["directory"] + "/"), (
                f"{topic['id']}.{field} is outside {phase['directory']}"
            )


def test_scaffolded_topics_have_their_files_on_disk(doc, root):
    scaffolded = [t for _, t in cur.iter_topics(doc) if t["scaffolded"]]
    assert scaffolded, "at least one topic should be scaffolded"
    for topic in scaffolded:
        for field in cur.PATH_FIELDS:
            assert (root / topic[field]).is_file(), f"missing {topic[field]}"


def test_prerequisites_never_point_forward(doc):
    order = {t["id"]: i for i, (_, t) in enumerate(cur.iter_topics(doc))}
    for _, topic in cur.iter_topics(doc):
        for prereq in topic["prerequisites"]:
            assert order[prereq] < order[topic["id"]], (
                f"{topic['id']} requires {prereq}, which comes later"
            )


def test_phase_one_has_an_entry_point_with_no_prerequisites(doc):
    first = doc["phases"][0]["topics"][0]
    assert first["prerequisites"] == [], (
        "the first topic must be startable, or nothing can ever begin"
    )


# --------------------------------------------------------------------------- #
# The validator must reject broken edits
# --------------------------------------------------------------------------- #

def test_invalid_status_is_rejected(doc, root):
    doc["phases"][0]["topics"][0]["status"] = "almost_done"
    result = cur.validate(doc, root)
    assert any("invalid status" in e for e in result.errors)


def test_missing_prerequisite_is_rejected(doc, root):
    doc["phases"][0]["topics"][1]["prerequisites"] = ["p99-t99"]
    result = cur.validate(doc, root)
    assert any("does not exist" in e for e in result.errors)


def test_duplicate_topic_id_is_rejected(doc, root):
    topics = doc["phases"][0]["topics"]
    topics[1]["id"] = topics[0]["id"]
    result = cur.validate(doc, root)
    assert any("duplicate topic id" in e for e in result.errors)


def test_dependency_cycle_is_reported_with_the_cycle(doc, root):
    a = doc["phases"][0]["topics"][0]
    b = doc["phases"][0]["topics"][1]
    a["prerequisites"] = [b["id"]]
    b["prerequisites"] = [a["id"]]
    result = cur.validate(doc, root)
    cycle_errors = [e for e in result.errors if e.startswith("dependency cycle")]
    assert cycle_errors, "a cycle must be reported, not silently drawn"
    assert a["id"] in cycle_errors[0] and b["id"] in cycle_errors[0], (
        "the error must name the topics in the cycle so it can be fixed"
    )


def test_self_prerequisite_is_rejected(doc, root):
    topic = doc["phases"][0]["topics"][0]
    topic["prerequisites"] = [topic["id"]]
    result = cur.validate(doc, root)
    assert any("itself as a prerequisite" in e for e in result.errors)


@pytest.mark.parametrize("bad", [
    "/absolute/lesson.md",
    "phases/../../etc/passwd",
    "phases\\01-foundations\\lesson.md",
    "",
])
def test_unsafe_lesson_paths_are_rejected(doc, root, bad):
    doc["phases"][0]["topics"][0]["lesson_path"] = bad
    result = cur.validate(doc, root)
    assert any("lesson_path" in e for e in result.errors), f"{bad!r} was accepted"


def test_wrong_phase_order_is_rejected(doc, root):
    doc["phases"][0]["order"] = 7
    result = cur.validate(doc, root)
    assert any("order is 7" in e for e in result.errors)


def test_wrong_topic_order_is_rejected(doc, root):
    doc["phases"][0]["topics"][2]["order"] = 99
    result = cur.validate(doc, root)
    assert any("order is 99" in e for e in result.errors)


def test_unknown_project_link_is_rejected(doc, root):
    doc["phases"][0]["topics"][0]["project_links"] = ["nonexistent-project"]
    result = cur.validate(doc, root)
    assert any("not a known project" in e for e in result.errors)


def test_project_links_resolve_for_every_topic(doc):
    known = {p["id"] for p in doc["projects"]}
    for _, topic in cur.iter_topics(doc):
        for link in topic["project_links"]:
            assert link in known


def test_review_intervals_must_match_policy(doc, root):
    doc["phases"][0]["topics"][0]["review"]["intervals_days"] = [1, 2, 4]
    result = cur.validate(doc, root)
    assert any("do not match the repository policy" in e for e in result.errors)


def test_done_without_evidence_is_rejected(doc, root):
    doc["phases"][0]["topics"][0]["status"] = "done"
    result = cur.validate(doc, root)
    assert any("mastery gate is not met" in e for e in result.errors), (
        "status must never be settable without evidence"
    )


def test_done_with_full_evidence_is_accepted(doc, root):
    topic = doc["phases"][0]["topics"][0]
    topic["status"] = "done"
    topic["evidence"] = {
        "exercise": {"passed": True, "command": "python -m pytest ...",
                     "tests_passed": 28, "tests_failed": 0, "date": "2026-10-27"},
        "quiz": {"score": 85, "max": 100, "percent": 85, "date": "2026-10-27"},
        "explanation": {"rating": 2, "note": "explained in own words", "date": "2026-10-27"},
        "transfer": {"demonstrated": True, "note": "applied to a new system"},
    }
    doc["phases"][0]["status"] = cur.derive_phase_status(doc["phases"][0]["topics"])
    result = cur.validate(doc, root)
    gate_errors = [e for e in result.errors if "mastery gate" in e]
    assert not gate_errors, gate_errors


def test_quiz_below_threshold_blocks_done(doc, root):
    topic = doc["phases"][0]["topics"][0]
    topic["status"] = "done"
    topic["evidence"] = {
        "exercise": {"passed": True, "command": "x", "tests_passed": 1,
                     "tests_failed": 0, "date": "2026-10-27"},
        "quiz": {"score": 60, "max": 100, "percent": 60, "date": "2026-10-27"},
        "explanation": {"rating": 3, "note": "", "date": "2026-10-27"},
        "transfer": {"demonstrated": True, "note": ""},
    }
    doc["phases"][0]["status"] = cur.derive_phase_status(doc["phases"][0]["topics"])
    result = cur.validate(doc, root)
    assert any("below the 80 threshold" in e for e in result.errors)


def test_explanation_rating_below_two_blocks_done(doc, root):
    topic = doc["phases"][0]["topics"][0]
    topic["status"] = "done"
    topic["evidence"] = {
        "exercise": {"passed": True, "command": "x", "tests_passed": 1,
                     "tests_failed": 0, "date": "2026-10-27"},
        "quiz": {"score": 100, "max": 100, "percent": 100, "date": "2026-10-27"},
        "explanation": {"rating": 1, "note": "recited the definition",
                        "date": "2026-10-27"},
        "transfer": {"demonstrated": False, "note": ""},
    }
    doc["phases"][0]["status"] = cur.derive_phase_status(doc["phases"][0]["topics"])
    result = cur.validate(doc, root)
    assert any("explanation rating 1 is below 2" in e for e in result.errors), (
        "code that passes with no explanation is not mastery"
    )


def test_status_on_an_unscaffolded_topic_is_rejected(doc, root):
    topic = doc["phases"][0]["topics"][5]
    assert topic["scaffolded"] is False
    topic["status"] = "in_progress"
    doc["phases"][0]["status"] = cur.derive_phase_status(doc["phases"][0]["topics"])
    result = cur.validate(doc, root)
    assert any("nothing to have worked on" in e for e in result.errors)


# --------------------------------------------------------------------------- #
# Derived values
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("statuses,expected", [
    (["not_started", "not_started"], "not_started"),
    (["done", "done"], "done"),
    (["done", "not_started"], "in_progress"),
    (["in_progress", "not_started"], "in_progress"),
    (["done", "needs_revision"], "needs_revision"),
    (["needs_revision", "not_started"], "needs_revision"),
    ([], "not_started"),
])
def test_phase_status_is_derived_deterministically(statuses, expected):
    topics = [{"status": s} for s in statuses]
    assert cur.derive_phase_status(topics) == expected


def test_needs_revision_dominates_even_when_most_is_done():
    topics = [{"status": "done"}] * 20 + [{"status": "needs_revision"}]
    assert cur.derive_phase_status(topics) == "needs_revision", (
        "a phase with an unresolved gap is not 'in progress', it needs revision"
    )


def test_progress_counts_only_done():
    phase = {"topics": [
        {"status": "done", "estimated_minutes": 60},
        {"status": "needs_revision", "estimated_minutes": 30},
        {"status": "in_progress", "estimated_minutes": 10},
        {"status": "not_started", "estimated_minutes": 100},
    ]}
    progress = cur.phase_progress(phase)
    assert progress.done == 1
    assert progress.total == 4
    assert progress.minutes_done == 60
    assert progress.minutes_total == 200
    assert progress.topic_percent == 25.0
    assert progress.effort_percent == 30.0


def test_progress_on_empty_phase_does_not_divide_by_zero():
    progress = cur.phase_progress({"topics": []})
    assert progress.topic_percent == 0.0
    assert progress.effort_percent == 0.0


def test_overall_progress_starts_at_zero(doc):
    progress = cur.overall_progress(doc)
    assert progress.done == 0
    assert progress.total == sum(len(p["topics"]) for p in doc["phases"])
    assert progress.topic_percent == 0.0


def test_next_actionable_respects_prerequisites(doc):
    available = cur.next_actionable_topics(doc, limit=50)
    ids = {t["id"] for t in available}
    first = doc["phases"][0]["topics"][0]
    assert first["id"] in ids, "the entry point must be available from the start"
    index = cur.topic_index(doc)
    for topic in available:
        for prereq in topic["prerequisites"]:
            assert index[prereq]["status"] == "done", (
                f"{topic['id']} was offered with an unfinished prerequisite"
            )


def test_completing_a_prerequisite_unlocks_the_next_topic(doc):
    first = doc["phases"][0]["topics"][0]
    second = doc["phases"][0]["topics"][1]
    assert first["id"] in second["prerequisites"]
    assert second["id"] not in {t["id"] for t in cur.next_actionable_topics(doc, 50)}
    first["status"] = "done"
    assert second["id"] in {t["id"] for t in cur.next_actionable_topics(doc, 50)}


def test_mermaid_ids_are_safe_identifiers(doc):
    for _, topic in cur.iter_topics(doc):
        node = cur.mermaid_id(topic["id"])
        assert node.replace("_", "").isalnum()
        assert not node[0].isdigit()


# --------------------------------------------------------------------------- #
# Review schedule validation
# --------------------------------------------------------------------------- #

def test_non_iso_review_date_is_rejected(doc):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {first: {"next_review": "27/10/2026", "interval_days": 1}}}
    result = cur.validate_review_schedule(doc, schedule)
    assert any("not an ISO 8601 date" in e for e in result.errors)


def test_unknown_topic_in_schedule_is_rejected(doc):
    schedule = {"topics": {"p42-t01": {"next_review": "2026-11-01"}}}
    result = cur.validate_review_schedule(doc, schedule)
    assert any("unknown topic id" in e for e in result.errors)


def test_interval_outside_policy_is_rejected(doc):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {first: {"interval_days": 5}}}
    result = cur.validate_review_schedule(doc, schedule)
    assert any("not one of the policy intervals" in e for e in result.errors)


def test_bad_history_result_is_rejected(doc):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {first: {
        "interval_days": 1,
        "history": [{"date": "2026-10-27", "result": "sort of"}],
    }}}
    result = cur.validate_review_schedule(doc, schedule)
    assert any("must be correct, incorrect or partial" in e for e in result.errors)


def test_valid_schedule_entry_is_accepted(doc):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {first: {
        "last_reviewed": "2026-10-27",
        "next_review": "2026-10-28",
        "interval_days": 1,
        "review_count": 1,
        "history": [{"date": "2026-10-27", "result": "partial"}],
    }}}
    result = cur.validate_review_schedule(doc, schedule)
    assert result.ok, result.errors


# --------------------------------------------------------------------------- #
# Loading failures
# --------------------------------------------------------------------------- #

def test_malformed_json_raises_with_a_line_number(tmp_path: Path):
    (tmp_path / "roadmap").mkdir()
    (tmp_path / "roadmap" / "curriculum.json").write_text('{"phases": [,]}', encoding="utf-8")
    with pytest.raises(cur.CurriculumError) as excinfo:
        cur.load_curriculum(tmp_path)
    assert "line" in str(excinfo.value)


def test_missing_curriculum_raises(tmp_path: Path):
    with pytest.raises(cur.CurriculumError):
        cur.load_curriculum(tmp_path)


def test_missing_review_schedule_is_an_empty_schedule_not_an_error(tmp_path: Path):
    assert cur.load_review_schedule(tmp_path)["topics"] == {}


def test_malformed_review_schedule_raises(tmp_path: Path):
    (tmp_path / "tracker").mkdir()
    (tmp_path / "tracker" / "review_schedule.json").write_text("{nope}", encoding="utf-8")
    with pytest.raises(cur.CurriculumError):
        cur.load_review_schedule(tmp_path)


def test_review_schedule_without_topics_object_raises(tmp_path: Path):
    (tmp_path / "tracker").mkdir()
    (tmp_path / "tracker" / "review_schedule.json").write_text(
        json.dumps({"schema_version": "1.0.0"}), encoding="utf-8"
    )
    with pytest.raises(cur.CurriculumError):
        cur.load_review_schedule(tmp_path)
