"""Tests for the Markdown renderer and the code highlighter.

The renderer runs at build time and its output goes straight into the page as
HTML, so the thing that matters most here is that text from a lesson file can
never become markup.
"""
from __future__ import annotations

import re

import pytest

import markdown as md


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("level", [1, 2, 3, 4, 5, 6])
def test_headings_render_at_their_level_with_an_anchor(level):
    out = md.render("#" * level + " Hello There")
    assert out == f'<h{level} id="hello-there">Hello There</h{level}>'


def test_paragraphs_join_wrapped_lines():
    assert md.render("one\ntwo\n\nthree") == "<p>one two</p>\n<p>three</p>"


def test_horizontal_rule():
    assert "<hr>" in md.render("a\n\n---\n\nb")


def test_blockquote():
    assert md.render("> quoted text") == "<blockquote>quoted text</blockquote>"


def test_unordered_list():
    out = md.render("- one\n- two")
    assert out == "<ul><li>one</li><li>two</li></ul>"


def test_ordered_list():
    out = md.render("1. one\n2. two")
    assert out == "<ol><li>one</li><li>two</li></ol>"


def test_nested_list_is_nested_not_flattened():
    out = md.render("- outer\n  - inner\n- outer two")
    assert out.count("<ul>") == 2
    assert "<ul><li>inner</li></ul>" in out


def test_task_list_items_get_a_checkbox():
    out = md.render("- [ ] not done\n- [x] done")
    assert out.count('class="task"') == 2
    assert "&#9744;" in out and "&#9745;" in out


def test_table_renders_a_real_table():
    out = md.render("| a | b |\n|---|---|\n| 1 | 2 |")
    assert out.count("<th>") == 2
    assert out.count("<td>") == 2
    assert "<thead>" in out and "<tbody>" in out


def test_table_cells_keep_inline_markup():
    out = md.render("| a | b |\n|---|---|\n| **bold** | `code` |")
    assert "<strong>bold</strong>" in out
    assert "<code>code</code>" in out


# --------------------------------------------------------------------------- #
# Inline
# --------------------------------------------------------------------------- #

def test_bold_and_italic():
    out = md.render("a **bold** and *italic* word")
    assert "<strong>bold</strong>" in out
    assert "<em>italic</em>" in out


def test_underscores_inside_identifiers_are_left_alone():
    out = md.render("the variable some_long_name stays intact")
    assert "some_long_name" in out
    assert "<em>" not in out


def test_asterisks_inside_words_do_not_become_italics():
    assert "<em>" not in md.render("2*3*4")


def test_inline_code_is_not_reinterpreted():
    out = md.render("use `**not bold**` here")
    assert "<code>**not bold**</code>" in out
    assert "<strong>" not in out


def test_relative_links_stay_relative():
    out = md.render("[file](exercise.py)")
    assert '<a href="exercise.py">file</a>' in out


def test_external_links_open_in_a_new_tab_safely():
    out = md.render("[site](https://example.com/x)")
    assert 'target="_blank"' in out and 'rel="noreferrer"' in out


# --------------------------------------------------------------------------- #
# Safety: lesson text must never become markup
# --------------------------------------------------------------------------- #

def test_raw_html_in_a_lesson_is_escaped():
    out = md.render("a <script>alert(1)</script> b")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_javascript_urls_are_neutralised():
    out = md.render("[click](javascript:alert(1))")
    assert "javascript:" not in out
    assert 'href="#"' in out


def test_html_inside_a_code_fence_is_escaped():
    out = md.render("```\n<img onerror=x>\n```")
    assert "<img" not in out
    assert "&lt;img" in out


def test_ampersands_and_angle_brackets_in_text_are_escaped():
    out = md.render("5 < 6 & 7 > 2")
    assert "&lt; 6 &amp; 7 &gt;" in out


def test_an_svg_fence_is_passed_through_on_purpose():
    out = md.render('```svg\n<svg><rect x="1"/></svg>\n```')
    assert '<figure class="diagram"><svg><rect x="1"/></svg></figure>' == out


# --------------------------------------------------------------------------- #
# Code blocks
# --------------------------------------------------------------------------- #

def test_fenced_block_with_a_language_becomes_an_example_box():
    out = md.render("```python\nx = 1\n```")
    assert 'class="example"' in out
    assert 'class="example-head">python<' in out
    assert 'class="code"' in out


def test_fenced_block_without_a_language_is_preformatted_text():
    out = md.render("```\n  +---+\n  | a |\n  +---+\n```")
    assert 'class="ascii"' in out
    assert "+---+" in out


def test_ascii_diagram_keeps_its_spacing():
    diagram = "A --> B\n  |\n  v\n  C"
    out = md.render("```\n" + diagram + "\n```")
    # The arrow is escaped, as it must be; the layout is what has to survive.
    assert "A --&gt; B\n  |\n  v\n  C" in out


# --------------------------------------------------------------------------- #
# Highlighting
# --------------------------------------------------------------------------- #

def test_python_keywords_strings_and_comments_are_marked_up():
    out = md.highlight('def f():\n    return "hi"  # note\n', "python")
    assert '<span class="k">def</span>' in out
    assert '<span class="s">&quot;hi&quot;</span>' in out
    assert '<span class="c"># note</span>' in out


def test_highlighting_escapes_before_it_colours():
    out = md.highlight('x = "<script>"', "python")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_a_hash_inside_a_string_is_not_a_comment():
    out = md.highlight('x = "# not a comment"', "python")
    assert '<span class="c">' not in out


def test_unknown_language_is_escaped_and_left_alone():
    out = md.highlight("a < b", "brainfuck")
    assert out == "a &lt; b"
    assert "<span" not in out


def test_shell_comments_and_flags():
    out = md.highlight("python -m pytest  # run them", "bash")
    assert '<span class="c"># run them</span>' in out
    assert '<span class="d">-m</span>' in out


def test_highlighting_preserves_the_original_text():
    source = 'def f(x):\n    # c\n    return x + 1\n'
    plain = re.sub(r"<[^>]+>", "", md.highlight(source, "python"))
    plain = plain.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
    plain = plain.replace("&amp;", "&")
    assert plain == source, "highlighting must not add or drop a character"


# --------------------------------------------------------------------------- #
# Whole documents
# --------------------------------------------------------------------------- #

def test_rendering_is_deterministic():
    source = "# T\n\ntext **b**\n\n- a\n- b\n\n| x | y |\n|---|---|\n| 1 | 2 |\n"
    assert md.render(source) == md.render(source)


def test_front_matter_is_stripped():
    assert md.strip_front_matter("---\ntitle: x\n---\nbody") == "body"


def test_text_without_front_matter_is_untouched():
    assert md.strip_front_matter("# body") == "# body"


def test_first_heading_is_found():
    assert md.first_heading("intro\n\n# The Title\n\n## Sub") == "The Title"


def test_crlf_input_renders_the_same_as_lf():
    assert md.render("# a\n\nb\n") == md.render("# a\r\n\r\nb\r\n")


def test_the_real_lesson_renders_without_leaving_markdown_behind(root):
    source = (root / "phases" / "01-foundations" /
              "01-complete-map-of-ai-engineering" / "lesson.md").read_text(encoding="utf-8")
    out = md.render(source)
    assert len(out) > 10000
    assert "```" not in out, "an unclosed fence would swallow the rest of the lesson"
    assert "](" not in out, "a link was not converted"
    assert out.count("<h2") >= 10
    assert "<table>" in out and "<ul>" in out and 'class="ascii"' in out
