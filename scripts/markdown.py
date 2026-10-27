"""A small Markdown to HTML renderer, plus a code highlighter.

Why this exists rather than a dependency: the whole point of the generated page
is that it opens from disk with no network and no install, and the repository
tooling is standard library only. Rendering happens at BUILD time, so the browser
never has to fetch or parse anything.

This is not a general Markdown implementation. It supports exactly what the
lesson files use, and it is strict about it: anything it does not recognise comes
out as an escaped paragraph rather than being silently dropped.

Supported: ATX headings, paragraphs, bold, italic, inline code, links, fenced
code blocks with a language, pipe tables, blockquotes, horizontal rules, nested
unordered and ordered lists, task list items, and a raw passthrough for fenced
blocks marked `svg`.
"""
from __future__ import annotations

import html
import re

__all__ = ["render", "highlight", "strip_front_matter", "first_heading"]

_CODE_SLOT = "\x00c{}\x00"

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
_FENCE_RE = re.compile(r"^```\s*([A-Za-z0-9_+-]*)\s*$")
_HR_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
_UL_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_TASK_RE = re.compile(r"^\[([ xX])\]\s+(.*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:-]*-[\s|:-]*\|?\s*$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC_RE = re.compile(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])")


# --------------------------------------------------------------------------- #
# Inline
# --------------------------------------------------------------------------- #

def _safe_href(url: str) -> str:
    """Allow relative links, anchors and http(s) only. Everything else is dropped."""
    lowered = url.strip().lower()
    if lowered.startswith(("http://", "https://", "#", "./", "../")):
        return html.escape(url, quote=True)
    if ":" in lowered.split("/")[0]:
        # A scheme we do not allow, javascript: being the one that matters.
        return "#"
    return html.escape(url, quote=True)


def _inline(text: str) -> str:
    """Render inline markup. Code spans are extracted first so nothing rewrites them."""
    spans: list[str] = []

    def take_code(match: re.Match[str]) -> str:
        spans.append(html.escape(match.group(1)))
        return _CODE_SLOT.format(len(spans) - 1)

    text = re.sub(r"`([^`]+)`", take_code, text)
    text = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        external = url.startswith(("http://", "https://"))
        extra = ' target="_blank" rel="noreferrer"' if external else ""
        return f'<a href="{_safe_href(url)}"{extra}>{label}</a>'

    text = _LINK_RE.sub(link, text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)

    for i, code in enumerate(spans):
        text = text.replace(_CODE_SLOT.format(i), f"<code>{code}</code>")
    return text


# --------------------------------------------------------------------------- #
# Highlighting
# --------------------------------------------------------------------------- #

_PY_KEYWORDS = frozenset("""
and as assert async await break class continue def del elif else except finally
for from global if import in is lambda nonlocal not or pass raise return try
while with yield match case
""".split())
_PY_CONSTANTS = frozenset("True False None self cls".split())
_PY_BUILTINS = frozenset("""
print len range int float str bool list dict set tuple sum min max sorted
enumerate zip open isinstance type abs round any all map filter repr format
""".split())

_PY_TOKEN_RE = re.compile(
    r"""(?P<comment>\#[^\n]*)
      | (?P<string>[fruFRUB]{0,2}(?:\"\"\"(?:\\.|[^\\])*?\"\"\"|'''(?:\\.|[^\\])*?'''
                                   |\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'))
      | (?P<decorator>^[ \t]*@[\w.]+)
      | (?P<number>\b\d[\d_]*(?:\.\d+)?\b)
      | (?P<name>[A-Za-z_]\w*)
    """,
    re.VERBOSE | re.MULTILINE | re.DOTALL,
)

_SHELL_TOKEN_RE = re.compile(
    r"""(?P<comment>\#[^\n]*)
      | (?P<string>\"[^\"\n]*\"|'[^'\n]*')
      | (?P<flag>(?<=\s)-{1,2}[A-Za-z][\w-]*)
    """,
    re.VERBOSE,
)


def _wrap(cls: str, text: str) -> str:
    return f'<span class="{cls}">{html.escape(text)}</span>'


def highlight(code: str, lang: str) -> str:
    """Return escaped HTML with highlight spans. Unknown languages are escaped only."""
    lang = (lang or "").lower()
    if lang in ("python", "py"):
        pattern, namer = _PY_TOKEN_RE, "python"
    elif lang in ("bash", "sh", "shell", "powershell", "console"):
        pattern, namer = _SHELL_TOKEN_RE, "shell"
    else:
        return html.escape(code)

    out: list[str] = []
    position = 0
    for match in pattern.finditer(code):
        out.append(html.escape(code[position:match.start()]))
        kind = match.lastgroup or ""
        value = match.group()
        if kind == "comment":
            out.append(_wrap("c", value))
        elif kind == "string":
            out.append(_wrap("s", value))
        elif kind == "decorator":
            out.append(_wrap("d", value))
        elif kind == "number":
            out.append(_wrap("n", value))
        elif kind == "flag":
            out.append(_wrap("d", value))
        elif namer == "python" and kind == "name":
            if value in _PY_KEYWORDS:
                out.append(_wrap("k", value))
            elif value in _PY_CONSTANTS:
                out.append(_wrap("b", value))
            elif value in _PY_BUILTINS:
                out.append(_wrap("f", value))
            else:
                out.append(html.escape(value))
        else:
            out.append(html.escape(value))
        position = match.end()
    out.append(html.escape(code[position:]))
    return "".join(out)


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #

def strip_front_matter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    return text if end == -1 else text[end + 5:]


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) == 1:
            return re.sub(r"[*`]", "", match.group(2)).strip()
    return None


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", re.sub(r"<[^>]+>", "", text)).strip().lower()
    return re.sub(r"[\s_]+", "-", cleaned) or "section"


def _render_table(rows: list[str]) -> str:
    def cells(line: str) -> list[str]:
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [c.strip() for c in line.split("|")]

    header = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    out = ["<table><thead><tr>"]
    out += [f"<th>{_inline(c)}</th>" for c in header]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        out += [f"<td>{_inline(c)}</td>" for c in row]
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def _render_list(items: list[tuple[int, str, str]], start: int, ordered: bool) -> tuple[str, int]:
    """Render one list. items is (indent, kind, text). Returns (html, next index)."""
    base_indent = items[start][0]
    tag = "ol" if ordered else "ul"
    out = [f"<{tag}>"]
    i = start
    while i < len(items):
        indent, kind, text = items[i]
        if indent < base_indent:
            break
        if indent > base_indent:
            nested, i = _render_list(items, i, kind == "ol")
            out.append(nested)
            continue
        if (kind == "ol") != ordered:
            break
        task = _TASK_RE.match(text)
        if task:
            done = task.group(1).lower() == "x"
            mark = "&#9745;" if done else "&#9744;"
            out.append(
                f'<li class="task"><span class="box">{mark}</span> '
                f"{_inline(task.group(2))}</li>"
            )
        else:
            out.append(f"<li>{_inline(text)}</li>")
        i += 1
    out.append(f"</{tag}>")
    return "".join(out), i


def render(text: str) -> str:
    """Render Markdown to HTML. Deterministic: same input, same bytes out."""
    text = strip_front_matter(text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        fence = _FENCE_RE.match(line)
        if fence:
            lang = fence.group(1)
            i += 1
            body: list[str] = []
            while i < n and not _FENCE_RE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # closing fence
            code = "\n".join(body)
            if lang == "svg":
                # Deliberate passthrough: lesson diagrams are authored as inline
                # SVG so they are real figures rather than pictures of text.
                out.append(f'<figure class="diagram">{code}</figure>')
            elif lang:
                out.append(
                    f'<div class="example"><div class="example-head">{html.escape(lang)}'
                    f'</div><pre class="code"><code>{highlight(code, lang)}'
                    f"</code></pre></div>"
                )
            else:
                out.append(f'<pre class="ascii"><code>{html.escape(code)}</code></pre>')
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            body = _inline(heading.group(2))
            anchor = _slug(heading.group(2))
            out.append(f'<h{level} id="{anchor}">{body}</h{level}>')
            i += 1
            continue

        if _HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        if line.lstrip().startswith("> "):
            quoted: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                quoted.append(lines[i].lstrip()[1:].lstrip())
                i += 1
            out.append(f"<blockquote>{_inline(' '.join(quoted))}</blockquote>")
            continue

        if line.lstrip().startswith("|") and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(_render_table(rows))
            continue

        if _UL_RE.match(line) or _OL_RE.match(line):
            items: list[tuple[int, str, str]] = []
            while i < n:
                ul = _UL_RE.match(lines[i])
                ol = _OL_RE.match(lines[i])
                if ul:
                    items.append((len(ul.group(1)), "ul", ul.group(2)))
                elif ol:
                    items.append((len(ol.group(1)), "ol", ol.group(3)))
                elif lines[i].strip() == "" and i + 1 < n and (
                    _UL_RE.match(lines[i + 1]) or _OL_RE.match(lines[i + 1])
                ):
                    pass  # a blank line inside a list
                else:
                    break
                i += 1
            rendered, _ = _render_list(items, 0, items[0][1] == "ol")
            out.append(rendered)
            continue

        paragraph: list[str] = []
        while i < n and lines[i].strip() and not (
            _HEADING_RE.match(lines[i]) or _FENCE_RE.match(lines[i])
            or _HR_RE.match(lines[i]) or _UL_RE.match(lines[i]) or _OL_RE.match(lines[i])
            or lines[i].lstrip().startswith(("> ", "|"))
        ):
            paragraph.append(lines[i].strip())
            i += 1
        if paragraph:
            out.append(f"<p>{_inline(' '.join(paragraph))}</p>")
        else:
            i += 1

    return "\n".join(out)
