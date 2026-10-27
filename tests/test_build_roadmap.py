"""Tests for the roadmap generators.

The generators are tested in memory wherever possible, so the suite does not
depend on generated files already existing. Two tests shell out, to check the
real exit codes and the idempotency guarantee.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import build_roadmap as br
import curriculum as cur

# Topic nodes are declared at exactly eight spaces of indentation inside their
# phase subgraph. Anchoring matters: an unanchored "t_\w+" also matches the
# tail of "leg_not_started", which is how this regex was wrong the first time.
TOPIC_NODE_RE = re.compile(r'^ {8}(t_\w+)\["(.*?)"\]$', re.MULTILINE)


@pytest.fixture
def projects(doc):
    return {p["id"]: p["name"] for p in doc["projects"]}


@pytest.fixture
def mmd(doc, projects):
    return br.build_mermaid_full(doc, projects)


@pytest.fixture
def html(doc, root):
    """The real page, built the way build_roadmap.main builds it."""
    return br.build_html(
        doc,
        cur.load_review_schedule(root),
        None,
        br.collect_lessons(doc, root),
    )


# --------------------------------------------------------------------------- #
# Mermaid
# --------------------------------------------------------------------------- #

def test_every_topic_appears_exactly_once_as_a_mermaid_node(doc, mmd):
    for _, topic in cur.iter_topics(doc):
        node = cur.mermaid_id(topic["id"])
        assert mmd.count(f'{node}["') == 1, f"{topic['id']} is not a single node"


def test_every_phase_is_a_subgraph(doc, mmd):
    for phase in doc["phases"]:
        assert f'subgraph {phase["id"].upper()}[' in mmd


def test_edge_count_matches_the_prerequisite_count(doc, mmd):
    expected = sum(len(t["prerequisites"]) for _, t in cur.iter_topics(doc))
    edges = re.findall(r"^    t_\w+ --> t_\w+$", mmd, flags=re.MULTILINE)
    assert len(edges) == expected, "every prerequisite must become exactly one edge"


def test_every_edge_references_declared_nodes(mmd):
    declared = {m[0] for m in TOPIC_NODE_RE.findall(mmd)}
    for source, target in re.findall(r"^    (t_\w+) --> (t_\w+)$", mmd, flags=re.MULTILINE):
        assert source in declared, f"edge from undeclared node {source}"
        assert target in declared, f"edge to undeclared node {target}"


def test_all_four_status_classes_are_defined(mmd):
    for status in ("sNotStarted", "sInProgress", "sNeedsRevision", "sDone"):
        assert f"classDef {status} " in mmd


def test_every_node_is_assigned_a_status_class(mmd):
    declared = {m[0] for m in TOPIC_NODE_RE.findall(mmd)}
    assigned = set(re.findall(r"^    class (t_\w+) s\w+;$", mmd, flags=re.MULTILINE))
    assert declared == assigned, f"unclassed nodes: {sorted(declared - assigned)}"


def test_status_is_also_in_the_label_not_only_in_the_colour(doc, mmd):
    """Accessibility: colour alone must never carry the status."""
    labels = dict(TOPIC_NODE_RE.findall(mmd))
    for _, topic in cur.iter_topics(doc):
        label = labels[cur.mermaid_id(topic["id"])]
        expected = br.STATUS_LABELS[topic["status"]]
        assert f"[{expected}]" in label, f"{topic['id']} label has no textual status"


def test_legend_covers_every_status_and_credits_the_source(mmd):
    assert 'subgraph LEGEND["Legend"]' in mmd
    for status in br.STATUS_LABELS:
        assert f"leg_{status}[" in mmd
    assert br.CREDIT in mmd


def test_project_markers_appear_on_linked_topics(doc, mmd, projects):
    labels = dict(TOPIC_NODE_RE.findall(mmd))
    linked = [t for _, t in cur.iter_topics(doc) if t["project_links"]]
    assert linked, "some topics should be linked to projects"
    for topic in linked:
        label = labels[cur.mermaid_id(topic["id"])]
        for link in topic["project_links"]:
            assert projects[link] in label


def test_labels_never_contain_a_raw_quote(mmd):
    for _, label in TOPIC_NODE_RE.findall(mmd):
        assert '"' not in label, "an unescaped quote would break the Mermaid parse"


def test_mermaid_declares_a_flowchart_direction(mmd):
    assert mmd.splitlines()[3] == "flowchart TD"


def test_overview_has_one_node_per_phase_and_a_chain(doc):
    overview = br.build_mermaid_overview(doc)
    nodes = re.findall(r"^    (P\d+)\[\"", overview, flags=re.MULTILINE)
    assert len(nodes) == len(doc["phases"])
    edges = re.findall(r"^    (P\d+) --> (P\d+)$", overview, flags=re.MULTILINE)
    assert len(edges) == len(doc["phases"]) - 1, "phases form a single chain"


# --------------------------------------------------------------------------- #
# Parity and link checks
# --------------------------------------------------------------------------- #

def test_parity_check_catches_a_dropped_topic(doc, mmd, html):
    assert br.check_output_parity(doc, mmd, html) == []
    victim = doc["phases"][3]["topics"][2]
    broken = mmd.replace(f'{cur.mermaid_id(victim["id"])}["', "dropped[\"", 1)
    problems = br.check_output_parity(doc, broken, html)
    assert any(victim["id"] in p for p in problems), (
        "silently dropping a topic must fail the build"
    )


def test_parity_check_catches_a_duplicated_topic(doc, mmd, html):
    node = cur.mermaid_id(doc["phases"][0]["topics"][0]["id"])
    broken = mmd + f'\n    {node}["duplicate"]\n'
    problems = br.check_output_parity(doc, broken, html)
    assert any("appears 2 times" in p for p in problems)


def test_lesson_link_check_catches_a_missing_file(doc, root, tmp_path):
    assert br.check_lesson_links(doc, root) == []
    problems = br.check_lesson_links(doc, tmp_path)
    assert problems, "a scaffolded lesson that is not on disk must be reported"


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #

def test_html_contains_every_topic(doc, html):
    for _, topic in cur.iter_topics(doc):
        assert f'"{topic["id"]}"' in html


def test_embedded_data_is_valid_json_and_complete(doc, html):
    block = re.search(
        r'<script id="data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert block, "the data block must be present"
    payload = json.loads(block.group(1))
    assert len(payload["phases"]) == len(doc["phases"])
    ids = [t["id"] for p in payload["phases"] for t in p["topics"]]
    assert ids == [t["id"] for _, t in cur.iter_topics(doc)], (
        "topic order in the HTML must match the canonical order"
    )


def test_html_has_no_remote_resources(html):
    """It must work over file:// with no network. No CDN, no remote fonts."""
    for pattern in (r'src\s*=\s*"https?://', r"<link\b", r'@import\b',
                    r"cdn\.", r"googleapis", r"unpkg", r"jsdelivr"):
        assert not re.search(pattern, html, re.IGNORECASE), (
            f"found a remote resource matching {pattern!r}"
        )


def test_the_only_external_urls_are_the_attribution_and_the_svg_namespace(html):
    """An SVG namespace is an identifier, not an address: nothing fetches it."""
    urls = {u.rstrip("\\") for u in re.findall(r"https?://[^\s\"'<>)]+", html)}
    assert urls <= {
        "https://roadmap.sh/ai-engineer",
        "http://www.w3.org/2000/svg",
    }, f"unexpected URLs: {urls}"


def test_nothing_is_loaded_over_the_network(html):
    for pattern in (r"src\s*=\s*\"https?://", r"url\(\s*['\"]?https?://",
                    r"<link", r"@import"):
        assert not re.search(pattern, html, re.IGNORECASE), (
            f"found a network load matching {pattern!r}"
        )


def test_footer_credit_is_exactly_the_required_string(html):
    assert br.CREDIT == "Topic structure based on roadmap.sh/ai-engineer"
    assert f'<p id="credit">{br.CREDIT}</p>' in html


def test_html_declares_the_required_controls(html):
    for marker in (
        'id="q"', 'type="search"',        # search
        'id="topnav"', 'id="sidenav"',    # navigation
        'id="view"', 'id="rail"',         # the routed view and the summary rail
        'id="theme-light"', 'id="theme-dark"',
        'role="progressbar"', 'id="goal-fill"',
        'id="credit"',
        'class="skip"',                   # skip link for keyboard users
    ):
        assert marker in html, f"missing {marker}"


def test_every_view_is_present_in_the_bundle(html):
    for view in ("overview", "roadmap", "learn", "projects", "practice",
                 "flashcards", "progress", "resources", "about", "topic", "phase"):
        assert f"VIEWS.{view} =" in html, f"no {view} view"


def test_the_empty_state_is_rendered_and_announced(html):
    assert 'id: "empty", role: "status"' in html
    assert "No topics match this search and filter" in html


def test_html_nodes_are_buttons_so_they_are_keyboard_reachable(html):
    assert 'h("button", { type: "button", "class": "node"' in html
    assert '"aria-pressed": "false"' in html


def test_html_supports_light_and_dark_themes(html):
    assert "prefers-color-scheme: dark" in html
    assert ':root[data-theme="dark"]' in html
    assert ':root:not([data-theme="light"])' in html


def test_html_is_responsive_at_phone_width(html):
    assert 'name="viewport"' in html
    assert "@media (max-width: 820px)" in html
    assert "@media (max-width: 1180px)" in html


def test_lesson_links_are_relative_to_the_html_location(doc, html):
    assert '"../" + t.lesson_path' in html
    scaffolded = [t for _, t in cur.iter_topics(doc) if t["scaffolded"]][0]
    assert scaffolded["lesson_path"].startswith("phases/"), (
        "paths are repo-relative, and the HTML prefixes '../' because it lives in roadmap/"
    )


def test_html_reports_review_dates_from_the_schedule(doc):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {first: {
        "next_review": "2026-11-03", "interval_days": 3, "review_count": 2,
    }}}
    html = br.build_html(doc, schedule)
    assert "2026-11-03" in html


def test_closing_script_tags_in_data_are_neutralised(doc, root):
    doc["phases"][0]["topics"][0]["summary"] = "a </script> injection attempt"
    html = br.build_html(doc, cur.load_review_schedule(root))
    block = re.search(
        r'<script id="data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    payload = json.loads(block.group(1))
    assert payload["phases"][0]["topics"][0]["summary"] == "a </script> injection attempt"


# --------------------------------------------------------------------------- #
# README injection and file writing
# --------------------------------------------------------------------------- #

def test_update_readme_replaces_only_the_generated_block(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Title\n\nkeep me\n\n"
        f"{br.README_BEGIN}\n\n```mermaid\nold\n```\n\n{br.README_END}\n\n"
        "keep me too\n",
        encoding="utf-8",
    )
    message = br.update_readme(tmp_path, "flowchart TD\n    A --> B\n")
    text = readme.read_text(encoding="utf-8")
    assert "updated" in message
    assert "keep me" in text and "keep me too" in text
    assert "old" not in text
    assert "A --> B" in text


def test_update_readme_is_idempotent(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(f"{br.README_BEGIN}\n\n```mermaid\nx\n```\n\n{br.README_END}\n",
                      encoding="utf-8")
    overview = "flowchart TD\n    A --> B\n"
    br.update_readme(tmp_path, overview)
    first = readme.read_text(encoding="utf-8")
    message = br.update_readme(tmp_path, overview)
    assert readme.read_text(encoding="utf-8") == first
    assert "already up to date" in message


def test_update_readme_without_markers_changes_nothing(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text("# No markers here\n", encoding="utf-8")
    message = br.update_readme(tmp_path, "flowchart TD\n")
    assert "no generated-overview markers" in message
    assert readme.read_text(encoding="utf-8") == "# No markers here\n"


def test_write_if_changed_skips_identical_content(tmp_path: Path):
    target = tmp_path / "out.txt"
    assert br.write_if_changed(target, "hello") is True
    assert br.write_if_changed(target, "hello") is False
    assert br.write_if_changed(target, "goodbye") is True


# --------------------------------------------------------------------------- #
# CLI behaviour
# --------------------------------------------------------------------------- #

def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "build_roadmap.py"), *args],
        capture_output=True, text=True, cwd=str(root), input="",
    )


def test_check_mode_succeeds_and_writes_nothing(root: Path):
    before = sorted(p.name for p in (root / "roadmap").iterdir())
    result = _run(root, "--check")
    assert result.returncode == 0, result.stderr
    assert "nothing written" in result.stdout
    assert sorted(p.name for p in (root / "roadmap").iterdir()) == before


def test_build_reports_counts_and_output_paths(root: Path, raw_curriculum):
    result = _run(root)
    assert result.returncode == 0, result.stderr
    expected = sum(len(p["topics"]) for p in raw_curriculum["phases"])
    assert f"topics:      {expected}" in result.stdout
    assert f"phases:      {len(raw_curriculum['phases'])}" in result.stdout
    assert "roadmap/roadmap.mmd" in result.stdout
    assert "roadmap/roadmap.html" in result.stdout
    assert "validation:  passed" in result.stdout


def test_running_the_build_twice_changes_nothing(root: Path):
    """Idempotency: no timestamps, no reordering, no churn."""
    _run(root)
    targets = [root / "roadmap" / name
               for name in ("roadmap.mmd", "roadmap-overview.mmd", "roadmap.html")]
    first = {t.name: hashlib.sha256(t.read_bytes()).hexdigest() for t in targets}
    result = _run(root)
    assert result.returncode == 0
    second = {t.name: hashlib.sha256(t.read_bytes()).hexdigest() for t in targets}
    assert first == second
    for name in first:
        assert f"unchanged: roadmap/{name}" in result.stdout


def test_invalid_curriculum_fails_with_a_nonzero_exit_and_writes_nothing(
    root: Path, tmp_path: Path, raw_curriculum
):
    fake = tmp_path / "repo"
    (fake / "roadmap").mkdir(parents=True)
    (fake / "scripts").mkdir()
    for name in ("curriculum.py", "build_roadmap.py", "app_template.py",
                 "review.py", "markdown.py", "flowchart.py"):
        shutil.copy(root / "scripts" / name, fake / "scripts" / name)

    broken = json.loads(json.dumps(raw_curriculum))
    broken["phases"][0]["topics"][1]["prerequisites"] = ["p99-t99"]
    (fake / "roadmap" / "curriculum.json").write_text(
        json.dumps(broken, indent=2), encoding="utf-8"
    )

    result = subprocess.run(
        [sys.executable, str(fake / "scripts" / "build_roadmap.py"), "--root", str(fake)],
        capture_output=True, text=True, cwd=str(fake), input="",
    )
    assert result.returncode == 1
    assert "p99-t99" in result.stderr
    assert "Nothing was written" in result.stderr
    assert not (fake / "roadmap" / "roadmap.mmd").exists()
    assert not (fake / "roadmap" / "roadmap.html").exists()


def test_a_cycle_is_reported_instead_of_a_misleading_diagram(
    root: Path, tmp_path: Path, raw_curriculum
):
    fake = tmp_path / "repo"
    (fake / "roadmap").mkdir(parents=True)
    (fake / "scripts").mkdir()
    for name in ("curriculum.py", "build_roadmap.py", "app_template.py",
                 "review.py", "markdown.py", "flowchart.py"):
        shutil.copy(root / "scripts" / name, fake / "scripts" / name)

    broken = json.loads(json.dumps(raw_curriculum))
    first, second = broken["phases"][0]["topics"][0], broken["phases"][0]["topics"][1]
    first["prerequisites"] = [second["id"]]
    second["prerequisites"] = [first["id"]]
    (fake / "roadmap" / "curriculum.json").write_text(
        json.dumps(broken, indent=2), encoding="utf-8"
    )

    result = subprocess.run(
        [sys.executable, str(fake / "scripts" / "build_roadmap.py"), "--root", str(fake)],
        capture_output=True, text=True, cwd=str(fake), input="",
    )
    assert result.returncode == 1
    assert "dependency cycle" in result.stderr
    assert not (fake / "roadmap" / "roadmap.html").exists()


# --------------------------------------------------------------------------- #
# Regression: escaping must not destroy the markup inside labels
# --------------------------------------------------------------------------- #

def test_labels_keep_a_real_line_break(doc, mmd):
    """_mm_text must be applied to text segments, not to a finished label."""
    assert "&lt;br/&gt;" not in mmd, (
        "the line break was escaped into literal text, so every label is one run-on line"
    )
    for _, label in TOPIC_NODE_RE.findall(mmd):
        assert "<br/>" in label


def test_project_marker_stays_a_character_entity(doc, mmd):
    assert "&amp;#9670;" not in mmd, "the diamond entity was double-escaped"
    assert "&#9670;" in mmd


def test_overview_labels_also_keep_their_line_break(doc):
    overview = br.build_mermaid_overview(doc)
    assert "&lt;br/&gt;" not in overview
    assert overview.count("<br/>") == len(doc["phases"])


def test_an_ampersand_in_a_title_is_still_escaped(doc, projects):
    doc["phases"][0]["topics"][0]["title"] = "Tools & Function Calling"
    mmd = br.build_mermaid_full(doc, projects)
    labels = dict(TOPIC_NODE_RE.findall(mmd))
    assert "Tools &amp; Function Calling" in labels[cur.mermaid_id("p01-t01")]


def test_the_narrow_screen_overrides_come_after_the_rules_they_override(html):
    """Same specificity means source order decides. This caught a real bug."""
    sticky = html.index(".sidebar, .rail { position: sticky;")
    override = html.index(".sidebar { position: static;")
    assert override > sticky, (
        "the responsive override must come after the desktop rule or it never applies"
    )


# --------------------------------------------------------------------------- #
# The page shows only what the data supports
# --------------------------------------------------------------------------- #

def _payload(html: str) -> dict:
    block = re.search(
        r'<script id="data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    return json.loads(block.group(1))


def test_the_deck_is_embedded_for_the_flashcard_view(doc, root):
    cards = [{"front": "q1", "back": "a1", "topic": "p01-t01",
              "last_reviewed": "", "next_review": ""}]
    payload = _payload(br.build_html(doc, cur.load_review_schedule(root), cards))
    assert payload["cards"] == cards


def test_no_deck_means_an_empty_list_not_a_crash(doc, root):
    payload = _payload(br.build_html(doc, cur.load_review_schedule(root)))
    assert payload["cards"] == []


def test_projects_are_embedded_with_their_tags(doc, root):
    payload = _payload(br.build_html(doc, cur.load_review_schedule(root)))
    assert len(payload["projects"]) == len(doc["projects"])
    for project in payload["projects"]:
        assert project["tags"], f"{project['id']} has no tags"


def test_review_state_is_embedded_read_only(doc, root, html):
    first = doc["phases"][0]["topics"][0]["id"]
    schedule = {"topics": {first: {"next_review": "2026-11-03", "interval_days": 3,
                                   "review_count": 2, "history": []}}}
    payload = _payload(br.build_html(doc, schedule))
    assert payload["reviews"][first]["next_review"] == "2026-11-03"
    assert "localStorage.setItem(\"roadmap-theme\"" in html, (
        "the only thing the page writes is the theme preference"
    )


def test_the_page_states_a_zero_streak_honestly(html):
    assert "No reviews recorded yet, so the streak is zero." in html
    assert "function streak(" in html, "the streak must be computed, never written in"


def test_status_counts_come_from_the_data_not_from_the_markup(doc, root):
    payload = _payload(br.build_html(doc, cur.load_review_schedule(root)))
    statuses = [t["status"] for p in payload["phases"] for t in p["topics"]]
    assert statuses == [t["status"] for _, t in cur.iter_topics(doc)]


def test_mastery_conditions_are_carried_into_the_page(doc, root):
    payload = _payload(br.build_html(doc, cur.load_review_schedule(root)))
    assert len(payload["meta"]["mastery_conditions"]) == 4


def test_evidence_is_exposed_so_a_claim_can_be_checked(doc, root):
    payload = _payload(br.build_html(doc, cur.load_review_schedule(root)))
    first = payload["phases"][0]["topics"][0]
    assert first["evidence"]["quiz"]["percent"] is None


# --------------------------------------------------------------------------- #
# Lessons are rendered into the page at build time
# --------------------------------------------------------------------------- #

def test_only_scaffolded_topics_get_a_lesson(doc, root):
    lessons = br.collect_lessons(doc, root)
    scaffolded = {t["id"] for _, t in cur.iter_topics(doc) if t["scaffolded"]}
    assert set(lessons) == scaffolded


def test_a_lesson_carries_rendered_html_not_markdown(doc, root):
    entry = br.collect_lessons(doc, root)["p01-t01"]
    assert "<h1" in entry["html"] and "<h2" in entry["html"]
    assert "```" not in entry["html"]
    assert entry["headings"], "the in-page contents needs the section headings"


def test_a_lesson_carries_its_demo_exercise_and_quiz(doc, root):
    entry = br.collect_lessons(doc, root)["p01-t01"]
    assert '<span class="k">def</span>' in entry["demo_code"]
    assert '<span class="k">def</span>' in entry["exercise_code"]
    assert "validate_input" in entry["demo_output"]
    assert "<h3" in entry["quiz_html"] or "<h1" in entry["quiz_html"]
    assert entry["answers_html"]


def test_lesson_commands_point_at_real_files(doc, root):
    entry = br.collect_lessons(doc, root)["p01-t01"]
    demo = entry["commands"]["demo"].split(" ", 1)[1]
    assert (root / demo).is_file()
    assert entry["commands"]["tests"].startswith("python -m pytest ")


def test_a_missing_optional_file_is_none_not_a_crash(doc, root, tmp_path):
    """demo_output.txt is optional: a lesson without one must still build."""
    entry = br.collect_lessons(doc, root)["p01-t01"]
    assert entry["demo_output"] is not None
    doc["phases"][0]["topics"][0]["scaffolded"] = False
    assert br.collect_lessons(doc, root) == {}


def test_the_page_embeds_the_lessons(doc, root, html):
    payload = _payload(html)
    assert "p01-t01" in payload["lessons"]
    assert "VIEWS.lesson =" in html


def test_the_page_embeds_the_flowcharts(doc, root):
    payload = _payload(br.build_html(doc, cur.load_review_schedule(root)))
    assert payload["flowchart"].startswith("<svg")
    for phase in payload["phases"]:
        assert phase["flowchart"].startswith("<svg")


def test_lesson_links_open_the_rendered_view_not_the_raw_file(html):
    assert 'go("#/lesson/" + t.id)' in html, (
        "the whole point of rendering is that a lesson opens in the page"
    )
