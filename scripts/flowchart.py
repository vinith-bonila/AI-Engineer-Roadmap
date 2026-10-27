"""Build-time SVG flowcharts.

The page has to work with no network, so it cannot load a diagramming library.
These functions emit plain SVG from the curriculum data instead: deterministic,
themable through CSS variables, and about 20 KB for the whole curriculum.

Colours come from the same CSS custom properties the rest of the page uses, so a
diagram follows the light and dark themes without a second palette.
"""
from __future__ import annotations

import html
from typing import Any

STATUS_FILL = {
    "not_started": "var(--ns-bg)",
    "in_progress": "var(--ip-bg)",
    "needs_revision": "var(--nr-bg)",
    "done": "var(--dn-bg)",
}
STATUS_STROKE = {
    "not_started": "var(--ns-br)",
    "in_progress": "var(--ip-br)",
    "needs_revision": "var(--nr-br)",
    "done": "var(--dn-br)",
}
STATUS_TEXT = {
    "not_started": "var(--ns-tx)",
    "in_progress": "var(--ip-tx)",
    "needs_revision": "var(--nr-tx)",
    "done": "var(--dn-tx)",
}
STATUS_LABEL = {
    "not_started": "not started",
    "in_progress": "in progress",
    "needs_revision": "needs revision",
    "done": "done",
}


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _wrap(text: str, limit: int) -> list[str]:
    """Greedy word wrap, so a long phase title does not run out of its box."""
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def phase_flowchart(doc: dict[str, Any]) -> str:
    """A top-down flowchart of the phases, with progress and status on each box."""
    phases = doc.get("phases", [])
    box_w, box_h, gap, pad = 560, 96, 34, 22
    width = box_w + pad * 2
    height = pad * 2 + len(phases) * box_h + max(0, len(phases) - 1) * gap

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Flowchart of the {len(phases)} curriculum phases in order" '
        'xmlns="http://www.w3.org/2000/svg" class="flowchart">',
        '<defs><marker id="fc-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0 0 L10 5 L0 10 z" fill="var(--muted)"/></marker></defs>',
    ]

    for index, phase in enumerate(phases):
        top = pad + index * (box_h + gap)
        status = phase.get("status", "not_started")
        topics = phase.get("topics", [])
        done = sum(1 for t in topics if t.get("status") == "done")
        percent = 0 if not topics else round(100 * done / len(topics))

        parts.append(
            f'<rect x="{pad}" y="{top}" width="{box_w}" height="{box_h}" rx="12" '
            f'fill="{STATUS_FILL[status]}" stroke="{STATUS_STROKE[status]}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{pad + 18}" y="{top + 32}" font-size="22" font-weight="700" '
            f'fill="{STATUS_TEXT[status]}" opacity=".55">{index + 1:02d}</text>'
        )

        title_lines = _wrap(phase.get("title", ""), 42)[:2]
        for line_index, line in enumerate(title_lines):
            parts.append(
                f'<text x="{pad + 56}" y="{top + 28 + line_index * 19}" font-size="15" '
                f'font-weight="650" fill="{STATUS_TEXT[status]}">{_esc(line)}</text>'
            )

        meta = f"{len(topics)} topics - {done} done - {STATUS_LABEL[status]}"
        parts.append(
            f'<text x="{pad + 56}" y="{top + box_h - 26}" font-size="12.5" '
            f'fill="{STATUS_TEXT[status]}" opacity=".8">{_esc(meta)}</text>'
        )

        bar_x, bar_y, bar_w = pad + 56, top + box_h - 17, box_w - 76
        parts.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="7" rx="3.5" '
            'fill="var(--track)"/>'
        )
        if percent:
            parts.append(
                f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w * percent / 100:.1f}" '
                f'height="7" rx="3.5" fill="{STATUS_STROKE[status]}"/>'
            )

        if index < len(phases) - 1:
            x = pad + box_w / 2
            parts.append(
                f'<line x1="{x}" y1="{top + box_h}" x2="{x}" y2="{top + box_h + gap - 4}" '
                'stroke="var(--muted)" stroke-width="2" marker-end="url(#fc-arrow)"/>'
            )

    parts.append("</svg>")
    return "".join(parts)


def phase_topic_flowchart(phase: dict[str, Any]) -> str:
    """A flowchart of one phase: its topics in order, with the prerequisite chain."""
    topics = phase.get("topics", [])
    box_w, box_h, gap, pad = 420, 54, 24, 18
    width = box_w + pad * 2
    height = pad * 2 + len(topics) * box_h + max(0, len(topics) - 1) * gap

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Flowchart of the {len(topics)} topics in '
        f'{_esc(phase.get("title", ""))}" '
        'xmlns="http://www.w3.org/2000/svg" class="flowchart">',
        '<defs><marker id="tc-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0 0 L10 5 L0 10 z" fill="var(--muted)"/></marker></defs>',
    ]

    for index, topic in enumerate(topics):
        top = pad + index * (box_h + gap)
        status = topic.get("status", "not_started")
        parts.append(
            f'<rect x="{pad}" y="{top}" width="{box_w}" height="{box_h}" rx="10" '
            f'fill="{STATUS_FILL[status]}" stroke="{STATUS_STROKE[status]}" stroke-width="2"/>'
        )
        label = f"{phase['order']}.{topic['order']}  {topic['title']}"
        for line_index, line in enumerate(_wrap(label, 46)[:2]):
            parts.append(
                f'<text x="{pad + 14}" y="{top + 22 + line_index * 17}" font-size="13" '
                f'font-weight="600" fill="{STATUS_TEXT[status]}">{_esc(line)}</text>'
            )
        parts.append(
            f'<text x="{pad + 14}" y="{top + box_h - 10}" font-size="11" '
            f'fill="{STATUS_TEXT[status]}" opacity=".75">'
            f'{_esc(STATUS_LABEL[status])} - {topic["estimated_minutes"]} min</text>'
        )
        if index < len(topics) - 1:
            x = pad + box_w / 2
            parts.append(
                f'<line x1="{x}" y1="{top + box_h}" x2="{x}" y2="{top + box_h + gap - 4}" '
                'stroke="var(--muted)" stroke-width="2" marker-end="url(#tc-arrow)"/>'
            )

    parts.append("</svg>")
    return "".join(parts)
