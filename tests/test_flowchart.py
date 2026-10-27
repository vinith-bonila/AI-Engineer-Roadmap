"""Tests for the build-time SVG flowcharts.

The page cannot load a diagramming library, so these diagrams are plain SVG
emitted from the curriculum. That makes them testable as data rather than as
pictures: one box per phase, one arrow between neighbours, nothing invented.
"""
from __future__ import annotations

import re

import flowchart as fc


def boxes(svg: str) -> list[str]:
    return re.findall(r"<rect[^>]*rx=\"1[02]\"[^>]*>", svg)


def test_one_box_per_phase(doc):
    svg = fc.phase_flowchart(doc)
    assert len(boxes(svg)) == len(doc["phases"])


def test_arrows_connect_neighbours_only(doc):
    svg = fc.phase_flowchart(doc)
    arrows = re.findall(r"<line[^>]*marker-end", svg)
    assert len(arrows) == len(doc["phases"]) - 1


def test_every_phase_title_appears(doc):
    svg = fc.phase_flowchart(doc)
    for phase in doc["phases"]:
        first_word = phase["title"].split()[0]
        assert first_word in svg, f"{phase['title']} is missing from the diagram"


def test_the_diagram_describes_itself_to_a_screen_reader(doc):
    svg = fc.phase_flowchart(doc)
    assert 'role="img"' in svg
    assert 'aria-label="Flowchart of the 13 curriculum phases in order"' in svg


def test_status_is_written_out_not_only_coloured(doc):
    svg = fc.phase_flowchart(doc)
    assert "not started" in svg


def test_colours_are_theme_variables_not_fixed_values(doc):
    svg = fc.phase_flowchart(doc)
    assert "var(--ns-bg)" in svg
    assert "#ffffff" not in svg, "a hardcoded colour would break the dark theme"


def test_progress_bar_is_empty_at_zero_percent(doc):
    svg = fc.phase_flowchart(doc)
    assert svg.count('fill="var(--track)"') == len(doc["phases"])


def test_progress_bar_fills_when_a_topic_is_done(doc):
    phase = doc["phases"][0]
    for topic in phase["topics"]:
        topic["status"] = "done"
    phase["status"] = "done"
    svg = fc.phase_flowchart(doc)
    assert 'fill="var(--dn-br)"' in svg


def test_titles_are_escaped(doc):
    doc["phases"][0]["title"] = 'Tools & <script>alert("x")</script>'
    svg = fc.phase_flowchart(doc)
    assert "<script>" not in svg
    assert "&amp;" in svg


def test_long_titles_are_wrapped_rather_than_overflowing(doc):
    def title_lines(document):
        return len(re.findall(r'font-size="15" font-weight="650"',
                              fc.phase_flowchart(document)))

    before = title_lines(doc)
    doc["phases"][0]["title"] = "A very long phase title " * 4
    assert title_lines(doc) == before + 1, "a long title must wrap onto a second line"


def test_rendering_is_deterministic(doc):
    assert fc.phase_flowchart(doc) == fc.phase_flowchart(doc)


def test_height_grows_with_the_number_of_phases(doc):
    full = fc.phase_flowchart(doc)
    doc["phases"] = doc["phases"][:3]
    short = fc.phase_flowchart(doc)
    def height(svg: str) -> int:
        return int(re.search(r'viewBox="0 0 \d+ (\d+)"', svg).group(1))
    assert height(full) > height(short)


# --------------------------------------------------------------------------- #
# Per-phase diagrams
# --------------------------------------------------------------------------- #

def test_phase_diagram_has_one_box_per_topic(doc):
    phase = doc["phases"][4]
    svg = fc.phase_topic_flowchart(phase)
    assert len(boxes(svg)) == len(phase["topics"])


def test_phase_diagram_numbers_topics_within_the_phase(doc):
    phase = doc["phases"][0]
    svg = fc.phase_topic_flowchart(phase)
    assert "1.1" in svg and f"1.{len(phase['topics'])}" in svg


def test_phase_diagram_shows_the_estimated_time(doc):
    phase = doc["phases"][0]
    svg = fc.phase_topic_flowchart(phase)
    assert f"{phase['topics'][0]['estimated_minutes']} min" in svg


def test_every_phase_produces_a_valid_looking_diagram(doc):
    for phase in doc["phases"]:
        svg = fc.phase_topic_flowchart(phase)
        assert svg.startswith("<svg") and svg.endswith("</svg>")
        assert svg.count("<rect") >= len(phase["topics"])
