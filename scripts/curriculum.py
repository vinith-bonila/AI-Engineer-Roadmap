"""Loading, validation and derived calculations for roadmap/curriculum.json.

curriculum.json is the single source of truth for the curriculum. Every other
artefact in this repository - the Mermaid diagram, the interactive HTML roadmap,
the status report and the review scheduler - is derived from it.

Standard library only, on purpose. Nothing here needs installing.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

VALID_STATUSES = ("not_started", "in_progress", "needs_revision", "done")
VALID_SOURCES = ("official", "user", "recommended")
COMPLETE_STATUSES = ("done",)

PATH_FIELDS = (
    "lesson_path",
    "exercise_path",
    "test_path",
    "quiz_path",
    "quiz_answers_path",
)

CURRICULUM_RELPATH = "roadmap/curriculum.json"
REVIEW_RELPATH = "tracker/review_schedule.json"


class CurriculumError(Exception):
    """Raised when the curriculum cannot be loaded or is structurally invalid."""


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def repo_root(start: Path | None = None) -> Path:
    """Find the repository root by walking up until curriculum.json is found."""
    here = (start or Path(__file__)).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / CURRICULUM_RELPATH).is_file():
            return candidate
    raise CurriculumError(
        f"could not find {CURRICULUM_RELPATH} in {here} or any parent directory"
    )


def load_curriculum(root: Path) -> dict[str, Any]:
    path = root / CURRICULUM_RELPATH
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CurriculumError(f"cannot read {path}: {exc}") from exc
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CurriculumError(
            f"{CURRICULUM_RELPATH} is not valid JSON: line {exc.lineno} column "
            f"{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(doc, dict):
        raise CurriculumError(f"{CURRICULUM_RELPATH} must contain a JSON object")
    return doc


def load_review_schedule(root: Path) -> dict[str, Any]:
    """Load the review schedule. A missing file is an empty schedule, not an error."""
    path = root / REVIEW_RELPATH
    if not path.is_file():
        return {"schema_version": "1.0.0", "topics": {}}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CurriculumError(
            f"{REVIEW_RELPATH} is not valid JSON: line {exc.lineno}: {exc.msg}"
        ) from exc
    if not isinstance(doc, dict) or not isinstance(doc.get("topics"), dict):
        raise CurriculumError(f"{REVIEW_RELPATH} must be an object with a 'topics' object")
    return doc


def save_review_schedule(root: Path, doc: dict[str, Any]) -> None:
    path = root / REVIEW_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" everywhere a generator writes: a build on Windows and a build
    # on Linux must produce byte-identical files, or the idempotency guarantee
    # only holds on one machine.
    path.write_text(
        json.dumps(doc, indent=2, sort_keys=False) + "\n",
        encoding="utf-8", newline="\n",
    )


# --------------------------------------------------------------------------- #
# Traversal helpers
# --------------------------------------------------------------------------- #

def iter_phases(doc: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for phase in doc.get("phases", []):
        yield phase


def iter_topics(doc: dict[str, Any]) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield (phase, topic) pairs in canonical order."""
    for phase in iter_phases(doc):
        for topic in phase.get("topics", []):
            yield phase, topic


def topic_index(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {topic["id"]: topic for _, topic in iter_topics(doc) if "id" in topic}


def mermaid_id(topic_id: str) -> str:
    """A Mermaid-safe node identifier. Topic ids use hyphens, which Mermaid dislikes."""
    return "t_" + topic_id.replace("-", "_")


# --------------------------------------------------------------------------- #
# Derived values
# --------------------------------------------------------------------------- #

def derive_phase_status(topics: list[dict[str, Any]]) -> str:
    """Phase status is always derived from its topics, never hand-edited.

    Rule (documented in curriculum.json progress_policy.phase_status_rule):
      any needs_revision -> needs_revision
      all done           -> done
      any done or in_progress -> in_progress
      otherwise          -> not_started
    """
    statuses = [t.get("status") for t in topics]
    if not statuses:
        return "not_started"
    if any(s == "needs_revision" for s in statuses):
        return "needs_revision"
    if all(s == "done" for s in statuses):
        return "done"
    if any(s in ("done", "in_progress") for s in statuses):
        return "in_progress"
    return "not_started"


@dataclass
class Progress:
    done: int
    total: int
    minutes_done: int
    minutes_total: int

    @property
    def topic_percent(self) -> float:
        return 0.0 if self.total == 0 else 100.0 * self.done / self.total

    @property
    def effort_percent(self) -> float:
        return 0.0 if self.minutes_total == 0 else 100.0 * self.minutes_done / self.minutes_total


def phase_progress(phase: dict[str, Any]) -> Progress:
    topics = phase.get("topics", [])
    done = [t for t in topics if t.get("status") in COMPLETE_STATUSES]
    return Progress(
        done=len(done),
        total=len(topics),
        minutes_done=sum(int(t.get("estimated_minutes", 0)) for t in done),
        minutes_total=sum(int(t.get("estimated_minutes", 0)) for t in topics),
    )


def overall_progress(doc: dict[str, Any]) -> Progress:
    totals = Progress(0, 0, 0, 0)
    for phase in iter_phases(doc):
        p = phase_progress(phase)
        totals = Progress(
            totals.done + p.done,
            totals.total + p.total,
            totals.minutes_done + p.minutes_done,
            totals.minutes_total + p.minutes_total,
        )
    return totals


def evidence_complete(topic: dict[str, Any], threshold: int) -> tuple[bool, list[str]]:
    """Check the mastery gate. Returns (ok, list of missing conditions)."""
    missing: list[str] = []
    ev = topic.get("evidence") or {}
    exercise = ev.get("exercise") or {}
    quiz = ev.get("quiz") or {}
    explanation = ev.get("explanation") or {}

    if exercise.get("passed") is not True:
        missing.append("exercise tests not recorded as passing")
    if not exercise.get("command"):
        missing.append("no exercise command recorded")
    percent = quiz.get("percent")
    if percent is None:
        missing.append("no quiz score recorded")
    elif percent < threshold:
        missing.append(f"quiz score {percent} is below the {threshold} threshold")
    rating = explanation.get("rating")
    if rating is None:
        missing.append("no explanation rating recorded")
    elif rating < 2:
        missing.append(f"explanation rating {rating} is below 2")
    return (not missing, missing)


def quiz_threshold(doc: dict[str, Any], phase_id: str) -> int:
    policy = doc.get("mastery_policy") or {}
    thresholds = policy.get("quiz_threshold_percent") or {}
    foundational = policy.get("foundational_phases") or []
    key = "foundational" if phase_id in foundational else "advanced"
    return int(thresholds.get(key, 80))


def next_actionable_topics(doc: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    """Topics that are not complete and whose prerequisites are all done.

    This is what makes Track A and Track B both work: eligibility comes from the
    prerequisite graph, not from a hardcoded phase order.
    """
    index = topic_index(doc)
    result = []
    for _, topic in iter_topics(doc):
        if topic.get("status") in COMPLETE_STATUSES:
            continue
        prereqs = topic.get("prerequisites", [])
        if all(index.get(p, {}).get("status") in COMPLETE_STATUSES for p in prereqs):
            result.append(topic)
        if len(result) >= limit:
            break
    return result


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _is_safe_relpath(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("/") or value.startswith("\\"):
        return False
    if "\\" in value or ":" in value:
        return False
    parts = value.split("/")
    return ".." not in parts and "" not in parts


def _is_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        _dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    """Return one cycle as a list of node ids, or None. Deterministic order."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {node: WHITE for node in graph}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        colour[node] = GREY
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in colour:
                continue  # missing node reported separately
            if colour[nxt] == GREY:
                start = stack.index(nxt)
                return [*stack[start:], nxt]
            if colour[nxt] == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        colour[node] = BLACK
        return None

    for node in graph:
        if colour[node] == WHITE:
            found = visit(node)
            if found:
                return found
    return None


def validate(doc: dict[str, Any], root: Path, check_files: bool = True) -> ValidationResult:
    """Validate the curriculum document. Collects every error rather than failing fast."""
    result = ValidationResult()

    for key in ("schema_version", "phases", "projects", "progress_policy", "review_policy"):
        if key not in doc:
            result.error(f"top level: missing required key {key!r}")

    phases = doc.get("phases")
    if not isinstance(phases, list) or not phases:
        result.error("top level: 'phases' must be a non-empty list")
        return result

    projects = doc.get("projects") or []
    project_ids = set()
    for i, project in enumerate(projects):
        pid = project.get("id")
        if not pid:
            result.error(f"projects[{i}]: missing id")
            continue
        if pid in project_ids:
            result.error(f"projects: duplicate project id {pid!r}")
        project_ids.add(pid)
        url = project.get("external_url")
        if url is not None and not (
            isinstance(url, str) and url.startswith(("http://", "https://"))
        ):
            result.error(f"project {pid!r}: external_url must be null or an http(s) URL")
        path = project.get("path")
        if path is not None and check_files and not (root / path).exists():
            result.warn(f"project {pid!r}: path {path!r} does not exist yet")

    phase_ids: set[str] = set()
    topic_ids: set[str] = set()
    lesson_ids: set[str] = set()
    slugs: set[str] = set()
    graph: dict[str, list[str]] = {}
    sequence: dict[str, int] = {}
    position = 0
    intervals_policy = (doc.get("review_policy") or {}).get("intervals_days")

    for pi, phase in enumerate(phases):
        pid = phase.get("id")
        label = pid or f"phases[{pi}]"

        if not pid:
            result.error(f"phases[{pi}]: missing id")
        elif pid in phase_ids:
            result.error(f"duplicate phase id {pid!r}")
        else:
            phase_ids.add(pid)

        if phase.get("order") != pi + 1:
            result.error(
                f"phase {label}: order is {phase.get('order')!r} but should be {pi + 1} "
                "(phase order must be 1-based and match list position)"
            )
        if phase.get("status") not in VALID_STATUSES:
            result.error(f"phase {label}: invalid status {phase.get('status')!r}")

        expected_status = derive_phase_status(phase.get("topics", []))
        if phase.get("status") != expected_status:
            result.error(
                f"phase {label}: status {phase.get('status')!r} does not match the derived "
                f"status {expected_status!r}; run build_roadmap.py to recompute"
            )

        directory = phase.get("directory")
        if not _is_safe_relpath(directory):
            result.error(f"phase {label}: directory {directory!r} is not a safe relative path")

        topics = phase.get("topics")
        if not isinstance(topics, list) or not topics:
            result.error(f"phase {label}: 'topics' must be a non-empty list")
            continue

        for ti, topic in enumerate(topics):
            tid = topic.get("id")
            tlabel = tid or f"{label}.topics[{ti}]"

            if not tid:
                result.error(f"{label}.topics[{ti}]: missing id")
            elif tid in topic_ids:
                result.error(f"duplicate topic id {tid!r}")
            else:
                topic_ids.add(tid)
                sequence[tid] = position
                graph[tid] = list(topic.get("prerequisites", []))
            position += 1

            slug = topic.get("slug")
            if not slug:
                result.error(f"topic {tlabel}: missing slug")
            elif slug in slugs:
                result.error(f"duplicate topic slug {slug!r}")
            else:
                slugs.add(slug)

            lesson_id = topic.get("lesson_id")
            if not lesson_id:
                result.error(f"topic {tlabel}: missing lesson_id")
            elif lesson_id in lesson_ids:
                result.error(f"duplicate lesson id {lesson_id!r}")
            else:
                lesson_ids.add(lesson_id)

            if topic.get("order") != ti + 1:
                result.error(
                    f"topic {tlabel}: order is {topic.get('order')!r} but should be {ti + 1}"
                )
            if topic.get("status") not in VALID_STATUSES:
                result.error(f"topic {tlabel}: invalid status {topic.get('status')!r}")
            if topic.get("source") not in VALID_SOURCES:
                result.error(f"topic {tlabel}: invalid source {topic.get('source')!r}")
            if not isinstance(topic.get("estimated_minutes"), int) or topic["estimated_minutes"] <= 0:
                result.error(f"topic {tlabel}: estimated_minutes must be a positive integer")
            if not topic.get("title"):
                result.error(f"topic {tlabel}: missing title")
            if not topic.get("summary"):
                result.error(f"topic {tlabel}: missing summary")
            objectives = topic.get("learning_objectives")
            if not isinstance(objectives, list) or len(objectives) < 2:
                result.error(f"topic {tlabel}: needs at least two learning objectives")

            for pf in PATH_FIELDS:
                value = topic.get(pf)
                if not _is_safe_relpath(value):
                    result.error(f"topic {tlabel}: {pf} {value!r} is not a safe relative path")
                    continue
                if not value.startswith(f"{directory}/"):
                    result.error(
                        f"topic {tlabel}: {pf} {value!r} is not inside the phase directory "
                        f"{directory!r}"
                    )

            scaffolded = topic.get("scaffolded")
            if not isinstance(scaffolded, bool):
                result.error(f"topic {tlabel}: scaffolded must be a boolean")
            elif scaffolded and check_files:
                for pf in PATH_FIELDS:
                    value = topic.get(pf)
                    if _is_safe_relpath(value) and not (root / value).is_file():
                        result.error(
                            f"topic {tlabel}: marked scaffolded but {pf} {value!r} does not exist"
                        )
            elif not scaffolded and topic.get("status") != "not_started":
                result.error(
                    f"topic {tlabel}: status {topic.get('status')!r} but the topic is not "
                    "scaffolded, so there is nothing to have worked on"
                )

            for link in topic.get("project_links", []):
                if link not in project_ids:
                    result.error(f"topic {tlabel}: project_link {link!r} is not a known project")

            review = topic.get("review") or {}
            if not isinstance(review.get("required"), bool):
                result.error(f"topic {tlabel}: review.required must be a boolean")
            intervals = review.get("intervals_days")
            if not isinstance(intervals, list) or not intervals:
                result.error(f"topic {tlabel}: review.intervals_days must be a non-empty list")
            else:
                if any(not isinstance(v, int) or v <= 0 for v in intervals):
                    result.error(f"topic {tlabel}: review intervals must be positive integers")
                elif intervals != sorted(intervals):
                    result.error(f"topic {tlabel}: review intervals must be ascending")
                if intervals_policy is not None and intervals != intervals_policy:
                    result.error(
                        f"topic {tlabel}: review intervals {intervals} do not match the "
                        f"repository policy {intervals_policy}"
                    )

            if topic.get("status") == "done":
                ok, missing = evidence_complete(topic, quiz_threshold(doc, pid or ""))
                if not ok:
                    result.error(
                        f"topic {tlabel}: status is done but the mastery gate is not met: "
                        + "; ".join(missing)
                    )

    # Prerequisites
    for tid, prereqs in graph.items():
        if not isinstance(prereqs, list):
            result.error(f"topic {tid}: prerequisites must be a list")
            continue
        seen = set()
        for prereq in prereqs:
            if prereq == tid:
                result.error(f"topic {tid}: lists itself as a prerequisite")
                continue
            if prereq in seen:
                result.error(f"topic {tid}: duplicate prerequisite {prereq!r}")
            seen.add(prereq)
            if prereq not in topic_ids:
                result.error(f"topic {tid}: prerequisite {prereq!r} does not exist")
            elif sequence.get(prereq, -1) > sequence.get(tid, -1):
                result.error(
                    f"topic {tid}: prerequisite {prereq!r} comes later in the curriculum, "
                    "which makes the reading order impossible"
                )

    cycle = _find_cycle(graph)
    if cycle:
        result.error("dependency cycle: " + " -> ".join(cycle))

    return result


def validate_review_schedule(
    doc: dict[str, Any], schedule: dict[str, Any]
) -> ValidationResult:
    result = ValidationResult()
    known = set(topic_index(doc))
    intervals_policy = (doc.get("review_policy") or {}).get("intervals_days") or []

    for tid, entry in (schedule.get("topics") or {}).items():
        if tid not in known:
            result.error(f"review schedule: unknown topic id {tid!r}")
            continue
        if not isinstance(entry, dict):
            result.error(f"review schedule: entry for {tid!r} must be an object")
            continue
        for key in ("last_reviewed", "next_review"):
            value = entry.get(key)
            if value is not None and not _is_iso_date(value):
                result.error(
                    f"review schedule {tid}: {key} {value!r} is not an ISO 8601 date "
                    "(YYYY-MM-DD)"
                )
        interval = entry.get("interval_days")
        if interval is not None:
            if not isinstance(interval, int) or interval <= 0:
                result.error(f"review schedule {tid}: interval_days must be a positive integer")
            elif intervals_policy and interval not in intervals_policy:
                result.error(
                    f"review schedule {tid}: interval_days {interval} is not one of the "
                    f"policy intervals {intervals_policy}"
                )
        count = entry.get("review_count")
        if count is not None and (not isinstance(count, int) or count < 0):
            result.error(f"review schedule {tid}: review_count must be a non-negative integer")
        history = entry.get("history")
        if history is not None and not isinstance(history, list):
            result.error(f"review schedule {tid}: history must be a list")
        for i, record in enumerate(history or []):
            if not isinstance(record, dict):
                result.error(f"review schedule {tid}: history[{i}] must be an object")
                continue
            if not _is_iso_date(record.get("date")):
                result.error(f"review schedule {tid}: history[{i}].date is not an ISO 8601 date")
            if record.get("result") not in ("correct", "incorrect", "partial"):
                result.error(
                    f"review schedule {tid}: history[{i}].result must be correct, "
                    "incorrect or partial"
                )
    return result
