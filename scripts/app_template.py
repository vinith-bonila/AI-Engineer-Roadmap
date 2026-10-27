"""The HTML template for roadmap/roadmap.html.

Kept in its own module because it is long, and because build_roadmap.py should stay
readable as a pipeline: load, validate, generate, check, write.

The template is filled by str.replace on the __PLACEHOLDER__ tokens, not by
str.format, so the CSS and JavaScript braces need no escaping.

Everything is inline. No CDN, no remote fonts, no network calls at all: the page
has to work when opened straight off disk with file://.
"""

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Engineer Roadmap</title>
<style>
:root {
  --bg: #f4f6f9; --surface: #ffffff; --surface-2: #eef2f7; --border: #dbe2ea;
  --text: #0f1b2a; --muted: #5a6a7d; --accent: #1f5fa8; --accent-soft: #e7f0fb;
  --accent-text: #ffffff; --focus: #b4480c;
  --ns-bg: #f3f5f8; --ns-br: #8d98a3; --ns-tx: #28313b;
  --ip-bg: #fff3cd; --ip-br: #8a6100; --ip-tx: #3d2b00;
  --nr-bg: #fde2e1; --nr-br: #9b1c1c; --nr-tx: #4a0d0d;
  --dn-bg: #dcf3e3; --dn-br: #15603a; --dn-tx: #06301b;
  --track: #e1e7ee;
  --shadow: 0 1px 2px rgba(16, 32, 50, .06), 0 8px 24px rgba(16, 32, 50, .05);
  --hero-a: #2b1b55; --hero-b: #7b3f8c; --hero-c: #e4804f;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0d1218; --surface: #151c24; --surface-2: #1b242e; --border: #2b3742;
    --text: #e9eef4; --muted: #9bacbd; --accent: #6aa9f0; --accent-soft: #17283b;
    --accent-text: #08121c; --focus: #ffb366;
    --ns-bg: #1b242e; --ns-br: #6c7a87; --ns-tx: #dbe4ee;
    --ip-bg: #3a2d00; --ip-br: #e0b63a; --ip-tx: #ffeab0;
    --nr-bg: #401518; --nr-br: #f08a86; --nr-tx: #ffd9d6;
    --dn-bg: #0f3123; --dn-br: #5ec98e; --dn-tx: #c7f2d9;
    --track: #25303b;
    --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 24px rgba(0, 0, 0, .3);
  }
}
:root[data-theme="dark"] {
  --bg: #0d1218; --surface: #151c24; --surface-2: #1b242e; --border: #2b3742;
  --text: #e9eef4; --muted: #9bacbd; --accent: #6aa9f0; --accent-soft: #17283b;
  --accent-text: #08121c; --focus: #ffb366;
  --ns-bg: #1b242e; --ns-br: #6c7a87; --ns-tx: #dbe4ee;
  --ip-bg: #3a2d00; --ip-br: #e0b63a; --ip-tx: #ffeab0;
  --nr-bg: #401518; --nr-br: #f08a86; --nr-tx: #ffd9d6;
  --dn-bg: #0f3123; --dn-br: #5ec98e; --dn-tx: #c7f2d9;
  --track: #25303b;
  --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 24px rgba(0, 0, 0, .3);
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 15px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
a { color: var(--accent); }
svg { display: block; }
:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; border-radius: 6px; }
.skip { position: absolute; left: -9999px; }
.skip:focus { left: 10px; top: 10px; z-index: 50; background: var(--surface);
  padding: 9px 14px; border: 2px solid var(--focus); border-radius: 8px; }

/* ---- top bar ---------------------------------------------------------- */
.topbar { position: sticky; top: 0; z-index: 30; display: flex; align-items: center;
  gap: 14px; padding: 10px 16px; background: var(--surface);
  border-bottom: 1px solid var(--border); flex-wrap: wrap; }
.brand { display: flex; align-items: center; gap: 10px; font-weight: 700;
  line-height: 1.15; letter-spacing: -.01em; }
.brand .mark { width: 34px; height: 34px; border-radius: 9px; display: grid;
  place-items: center; background: linear-gradient(135deg, var(--hero-b), var(--accent)); color: #fff; }
.brand span { font-size: .95rem; max-width: 9rem; }
.topnav { display: flex; gap: 4px; flex: 1 1 auto; flex-wrap: wrap; }
.topnav button { display: inline-flex; align-items: center; gap: 7px; border: none;
  background: none; color: var(--muted); font: inherit; font-weight: 600;
  padding: 8px 13px; border-radius: 9px; cursor: pointer; }
.topnav button:hover { background: var(--surface-2); color: var(--text); }
.topnav button[aria-current="page"] { background: var(--accent); color: var(--accent-text); }
.searchwrap { position: relative; flex: 0 1 22rem; min-width: 11rem; }
.searchwrap svg { position: absolute; left: 11px; top: 50%; transform: translateY(-50%);
  color: var(--muted); pointer-events: none; }
input[type="search"], select, textarea {
  font: inherit; color: var(--text); background: var(--surface-2);
  border: 1px solid var(--border); border-radius: 10px; padding: 9px 12px; width: 100%; }
input[type="search"] { padding-left: 34px; }
.iconbtn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text);
  width: 36px; height: 36px; border-radius: 9px; display: grid; place-items: center;
  cursor: pointer; }
.iconbtn[aria-pressed="true"] { background: var(--accent); color: var(--accent-text);
  border-color: var(--accent); }
.whoami { display: flex; align-items: center; gap: 9px; font-weight: 600; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--accent);
  color: var(--accent-text); display: grid; place-items: center; font-weight: 700; }

/* ---- shell ------------------------------------------------------------ */
.shell { display: grid; grid-template-columns: 232px minmax(0, 1fr) 300px;
  gap: 18px; padding: 18px 16px 40px; align-items: start; max-width: 1560px; margin: 0 auto; }
.sidebar, .rail { position: sticky; top: 74px; display: flex; flex-direction: column; gap: 14px; }
.sidenav { background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 8px; box-shadow: var(--shadow); }
.sidenav button { width: 100%; display: flex; align-items: center; gap: 10px;
  border: none; background: none; color: var(--text); font: inherit; text-align: left;
  padding: 9px 11px; border-radius: 9px; cursor: pointer; }
.sidenav button:hover { background: var(--surface-2); }
.sidenav button[aria-current="page"] { background: var(--accent-soft); color: var(--accent);
  font-weight: 700; }
.sidenav .sub button { padding-left: 16px; font-size: .86rem; color: var(--muted); }
.sidenav .sub button[aria-current="page"] { color: var(--accent); }
.sidenav .muted-ico { color: var(--muted); display: grid; place-items: center; width: 18px; }

/* ---- cards ------------------------------------------------------------ */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  box-shadow: var(--shadow); }
.card > header { display: flex; align-items: center; justify-content: space-between;
  gap: 10px; padding: 14px 16px 0; flex-wrap: wrap; }
.card h2, .card h3 { margin: 0; font-size: 1rem; letter-spacing: -.01em; }
.card .body { padding: 14px 16px 16px; }
.sub { color: var(--muted); font-size: .86rem; margin: 2px 0 0; }
.stack { display: flex; flex-direction: column; gap: 18px; }
.link { background: none; border: none; color: var(--accent); font: inherit;
  font-weight: 600; cursor: pointer; padding: 0; }
.btn { display: inline-flex; align-items: center; gap: 8px; border: 1px solid var(--accent);
  background: var(--accent); color: var(--accent-text); font: inherit; font-weight: 700;
  padding: 10px 16px; border-radius: 10px; cursor: pointer; }
.btn.ghost { background: var(--surface); color: var(--text); border-color: var(--border); }

/* ---- hero ------------------------------------------------------------- */
.hero { position: relative; overflow: hidden; border-radius: 14px; color: #fff;
  border: 1px solid var(--border); min-height: 198px; display: flex; }
.hero .art { position: absolute; inset: 0; }
.hero .inner { position: relative; padding: 26px 24px; display: flex; gap: 20px;
  align-items: flex-start; justify-content: space-between; width: 100%; flex-wrap: wrap; }
.hero h1 { margin: 0; font-size: clamp(1.6rem, 3.4vw, 2.5rem); letter-spacing: -.02em;
  text-shadow: 0 2px 14px rgba(0, 0, 0, .45); }
.hero h1 em { font-style: normal; color: #ffd9a8; }
.hero p { margin: 6px 0 16px; font-size: 1rem; opacity: .95;
  text-shadow: 0 1px 10px rgba(0, 0, 0, .5); }
.chips { display: flex; gap: 10px; flex-wrap: wrap; }
.chip { display: inline-flex; align-items: center; gap: 8px; background: rgba(12, 16, 28, .5);
  border: 1px solid rgba(255, 255, 255, .22); color: #fff; padding: 8px 12px;
  border-radius: 10px; font-size: .82rem; backdrop-filter: blur(3px); }
.quote { background: rgba(12, 16, 28, .5); border: 1px solid rgba(255, 255, 255, .22);
  border-radius: 12px; padding: 12px 14px; max-width: 16rem; font-size: .85rem;
  backdrop-filter: blur(3px); }
.banner { display: flex; align-items: center; gap: 14px; justify-content: space-between;
  flex-wrap: wrap; background: var(--accent-soft); border: 1px solid var(--border);
  border-radius: 14px; padding: 14px 16px; }

/* ---- phase grid ------------------------------------------------------- */
.phasegrid { display: flex; flex-wrap: wrap; align-items: stretch; gap: 10px; }
.phasecard { flex: 1 1 215px; min-width: 200px; text-align: left; cursor: pointer;
  border: 1px solid var(--border); border-radius: 12px; padding: 12px 13px;
  background: var(--surface-2); color: var(--text); font: inherit;
  display: flex; flex-direction: column; gap: 8px; }
.phasecard:hover { border-color: var(--accent); }
.phasecard .top { display: flex; align-items: center; justify-content: space-between; }
.phasecard .num { font-weight: 800; font-size: 1.05rem; color: var(--muted); }
.phasecard .name { font-weight: 700; line-height: 1.25; }
.phasecard .meta { display: flex; justify-content: space-between; gap: 8px;
  font-size: .76rem; color: var(--muted); }
.arrow { align-self: center; color: var(--muted); flex: 0 0 auto; }
.phasecard[data-status="in_progress"] { background: var(--ip-bg); border-color: var(--ip-br); color: var(--ip-tx); }
.phasecard[data-status="needs_revision"] { background: var(--nr-bg); border-color: var(--nr-br); color: var(--nr-tx); }
.phasecard[data-status="done"] { background: var(--dn-bg); border-color: var(--dn-br); color: var(--dn-tx); }

/* ---- progress bars ---------------------------------------------------- */
.track { height: 8px; background: var(--track); border-radius: 999px; overflow: hidden; }
.track .fill { height: 100%; background: var(--accent); border-radius: 999px; }
.legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: .78rem; color: var(--muted); }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block;
  margin-right: 6px; border: 1px solid var(--border); vertical-align: -1px; }
.dot.not_started { background: var(--ns-bg); border-color: var(--ns-br); }
.dot.in_progress { background: var(--ip-br); }
.dot.needs_revision { background: var(--nr-br); }
.dot.done { background: var(--dn-br); }

/* ---- topic nodes ------------------------------------------------------ */
.grid { display: grid; gap: 9px; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); }
.node { text-align: left; border: 2px solid; border-radius: 10px; padding: 10px 11px;
  font: inherit; cursor: pointer; display: flex; flex-direction: column; gap: 5px;
  min-height: 4.6rem; }
.node .t { font-weight: 650; font-size: .88rem; line-height: 1.3; }
.node .s { font-size: .7rem; text-transform: uppercase; letter-spacing: .06em; font-weight: 700; }
.node .p { font-size: .72rem; }
.node[data-status="not_started"] { background: var(--ns-bg); border-color: var(--ns-br); color: var(--ns-tx); }
.node[data-status="in_progress"] { background: var(--ip-bg); border-color: var(--ip-br); color: var(--ip-tx); }
.node[data-status="needs_revision"] { background: var(--nr-bg); border-color: var(--nr-br); color: var(--nr-tx); }
.node[data-status="done"] { background: var(--dn-bg); border-color: var(--dn-br); color: var(--dn-tx); }
.node[aria-pressed="true"] { box-shadow: 0 0 0 3px var(--accent) inset; }
.node.prereq-highlight { outline: 3px dashed var(--accent); outline-offset: 1px; }

/* ---- misc ------------------------------------------------------------- */
.pill { display: inline-block; font-size: .72rem; font-weight: 700; padding: 2px 9px;
  border-radius: 999px; border: 1px solid currentColor; }
.tag { display: inline-block; font-size: .72rem; padding: 3px 9px; border-radius: 999px;
  background: var(--surface-2); border: 1px solid var(--border); color: var(--muted); }
.rowlist { display: flex; flex-direction: column; gap: 10px; }
.row { display: flex; align-items: center; gap: 11px; }
.row .ico { width: 34px; height: 34px; border-radius: 9px; display: grid; place-items: center;
  background: var(--accent-soft); color: var(--accent); flex: 0 0 auto; }
.row .grow { flex: 1 1 auto; min-width: 0; }
.row .name { font-weight: 650; font-size: .9rem; }
.week { display: flex; justify-content: space-between; gap: 4px; margin-top: 12px; }
.day { text-align: center; font-size: .68rem; color: var(--muted); }
.day .mark { width: 26px; height: 26px; border-radius: 50%; border: 2px solid var(--border);
  display: grid; place-items: center; margin: 0 auto 4px; }
.day.hit .mark { background: var(--dn-bg); border-color: var(--dn-br); color: var(--dn-tx); }
.empty { border: 1px dashed var(--border); border-radius: 12px; padding: 26px 16px;
  text-align: center; color: var(--muted); }
.note { border-left: 3px solid var(--accent); background: var(--surface-2);
  padding: 10px 12px; border-radius: 0 10px 10px 0; font-size: .86rem; color: var(--muted); }
dl { margin: 0; } dt { font-size: .7rem; text-transform: uppercase; letter-spacing: .06em;
  color: var(--muted); margin-top: 12px; font-weight: 700; }
dd { margin: 3px 0 0; }
ul.tight { margin: 4px 0 0; padding-left: 1.1rem; }
table { border-collapse: collapse; width: 100%; font-size: .87rem; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--border); }
th { color: var(--muted); font-size: .74rem; text-transform: uppercase; letter-spacing: .05em; }
footer { border-top: 1px solid var(--border); padding: 16px; color: var(--muted);
  font-size: .84rem; text-align: center; }
.flashcard { border: 1px solid var(--border); border-radius: 14px; padding: 26px 20px;
  background: var(--surface-2); min-height: 150px; display: grid; place-items: center;
  text-align: center; font-size: 1.05rem; font-weight: 600; }
.flashcard .answer { font-weight: 400; font-size: .95rem; color: var(--muted); margin-top: 12px; }

/* Narrow screens last, so same-specificity overrides actually win. */
@media (max-width: 1180px) {
  .shell { grid-template-columns: 206px minmax(0, 1fr); }
  .rail { grid-column: 1 / -1; position: static; flex-direction: row; flex-wrap: wrap; }
  .rail > * { flex: 1 1 260px; }
}
@media (max-width: 820px) {
  .shell { grid-template-columns: minmax(0, 1fr); padding: 14px 12px 36px; }
  .sidebar { position: static; order: 2; }
  .rail { order: 3; }
  main { order: 1; }
  .topnav { order: 3; flex-basis: 100%; }
  .searchwrap { flex: 1 1 100%; order: 2; }
  .brand span { max-width: none; }
  .hero .inner { padding: 20px 16px; }
  .quote { max-width: none; }
  .grid { grid-template-columns: minmax(0, 1fr); }
  .arrow { display: none; }
}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the main content</a>

<header class="topbar">
  <div class="brand"><span class="mark" id="brandmark"></span><span>AI Engineer Roadmap</span></div>
  <nav class="topnav" id="topnav" aria-label="Primary"></nav>
  <div class="searchwrap">
    <span id="searchicon"></span>
    <label class="skip" for="q">Search topics and lessons</label>
    <input id="q" type="search" placeholder="Search topics, lessons..." autocomplete="off">
  </div>
  <button class="iconbtn" id="theme-light" type="button" aria-pressed="false"
          title="Light theme" aria-label="Light theme"></button>
  <button class="iconbtn" id="theme-dark" type="button" aria-pressed="false"
          title="Dark theme" aria-label="Dark theme"></button>
  <div class="whoami"><span class="avatar" id="initial">A</span><span>AI Engineer</span></div>
</header>

<div class="shell">
  <aside class="sidebar">
    <nav class="sidenav" id="sidenav" aria-label="Sections"></nav>
    <div class="card"><div class="body">
      <div class="row" style="margin-bottom:10px">
        <span class="ico" id="goalicon"></span>
        <div class="grow"><div class="name">Your goal</div>
          <div class="sub">Become a job-ready AI engineer</div></div>
      </div>
      <div class="track"><div class="fill" id="goal-fill" role="progressbar"
        aria-label="Overall curriculum progress" aria-valuemin="0" aria-valuemax="100"></div></div>
      <p class="sub" id="goal-text"></p>
    </div></div>
  </aside>

  <main id="main" tabindex="-1"><div id="view"></div></main>

  <aside class="rail" id="rail"></aside>
</div>

<footer>
  <p id="credit">__CREDIT__</p>
  <p>Generated from <code>roadmap/curriculum.json</code>. Structure fetched from
     <code>roadmap.sh/ai-engineer.json</code> on __FETCH_DATE__. Topic structure only;
     no roadmap artwork, styling or descriptive text was copied.</p>
</footer>

<script id="data" type="application/json">__DATA__</script>
<script>
(function () {
  "use strict";

  var DATA = JSON.parse(document.getElementById("data").textContent);
  var LABELS = { not_started: "not started", in_progress: "in progress",
                 needs_revision: "needs revision", done: "done" };
  var SOURCES = { official: "official roadmap", user: "added by me",
                  recommended: "mentor addition" };

  // ---- tiny DOM helpers -------------------------------------------------
  function h(tag, attrs, kids) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "html") n.innerHTML = attrs[k];
      else if (k === "text") n.textContent = attrs[k];
      else if (k === "on") Object.keys(attrs.on).forEach(function (e) {
        n.addEventListener(e, attrs.on[e]);
      });
      else if (k === "style") n.setAttribute("style", attrs[k]);
      else n.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) {
      if (c === null || c === undefined) return;
      n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return n;
  }
  function pct(a, b) { return b === 0 ? 0 : Math.round((1000 * a) / b) / 10; }
  function svg(d, size) {
    return '<svg width="' + (size || 18) + '" height="' + (size || 18) +
      '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>';
  }
  var ICON = {
    home: svg('<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>'),
    map: svg('<path d="M9 3 3 6v15l6-3 6 3 6-3V3l-6 3-6-3z"/><path d="M9 3v15"/><path d="M15 6v15"/>'),
    book: svg('<path d="M4 4h7a3 3 0 0 1 3 3v13a2.5 2.5 0 0 0-2.5-2.5H4z"/><path d="M20 4h-3a3 3 0 0 0-3 3v13a2.5 2.5 0 0 1 2.5-2.5H20z"/>'),
    box: svg('<path d="M12 3 3 7.5v9L12 21l9-4.5v-9L12 3z"/><path d="M3 7.5 12 12l9-4.5"/><path d="M12 12v9"/>'),
    check: svg('<path d="M20 6 9 17l-5-5"/>'),
    chart: svg('<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>'),
    cards: svg('<rect x="3" y="6" width="13" height="14" rx="2"/><path d="M8 3h11a2 2 0 0 1 2 2v12"/>'),
    link: svg('<path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1"/>'),
    info: svg('<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>'),
    search: svg('<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>', 16),
    sun: svg('<circle cx="12" cy="12" r="4.2"/><path d="M12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/>', 17),
    moon: svg('<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/>', 17),
    brain: svg('<path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-1 5.8A3 3 0 0 0 7 19a3 3 0 0 0 5 .8V4.5A2.5 2.5 0 0 0 9 4z"/><path d="M15 4a3 3 0 0 1 3 3 3 3 0 0 1 1 5.8A3 3 0 0 1 17 19a3 3 0 0 1-5 .8"/>', 20),
    flag: svg('<path d="M5 21V4"/><path d="M5 5h12l-2 3.5L17 12H5z"/>'),
    flame: svg('<path d="M12 3s5 4 5 8a5 5 0 0 1-10 0c0-1.5.8-2.8 1.6-3.7C9.4 8.4 12 6 12 3z"/>'),
    arrow: svg('<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>', 16),
    doc: svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'),
    mic: svg('<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/>'),
    card: svg('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/>'),
    bars: svg('<path d="M5 20V9"/><path d="M12 20V4"/><path d="M19 20v-8"/>'),
    target: svg('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>')
  };
  var PROJECT_ICON = { docmind: "doc", "vini-ai": "mic", "payment-recovery-agent": "card",
                       autobi: "bars", "bounded-agent": "box" };

  // ---- indexes ----------------------------------------------------------
  var byId = {}, unlocks = {}, allTopics = [];
  DATA.phases.forEach(function (ph) {
    ph.topics.forEach(function (t) {
      t.phase = ph; byId[t.id] = t; allTopics.push(t);
      (t.prerequisites || []).forEach(function (p) {
        (unlocks[p] = unlocks[p] || []).push(t.id);
      });
    });
  });
  var TOTAL = allTopics.length;
  var COUNTS = { not_started: 0, in_progress: 0, needs_revision: 0, done: 0 };
  allTopics.forEach(function (t) { COUNTS[t.status]++; });
  var MIN_ALL = allTopics.reduce(function (a, t) { return a + t.estimated_minutes; }, 0);
  var MIN_DONE = allTopics.filter(function (t) { return t.status === "done"; })
                          .reduce(function (a, t) { return a + t.estimated_minutes; }, 0);
  var OVERALL = pct(COUNTS.done, TOTAL);

  function available() {
    return allTopics.filter(function (t) {
      return t.status !== "done" && (t.prerequisites || []).every(function (p) {
        return byId[p] && byId[p].status === "done";
      });
    });
  }
  function todayISO() { return new Date().toISOString().slice(0, 10); }
  function daysBetween(a, b) {
    return Math.round((Date.parse(b + "T00:00:00") - Date.parse(a + "T00:00:00")) / 86400000);
  }
  function dueReviews() {
    var today = todayISO(), out = [];
    Object.keys(DATA.reviews || {}).forEach(function (id) {
      var r = DATA.reviews[id];
      if (!r.next_review || !byId[id]) return;
      out.push({ id: id, title: byId[id].title, next: r.next_review,
                 overdue: daysBetween(r.next_review, today) });
    });
    out.sort(function (a, b) { return a.next < b.next ? -1 : a.next > b.next ? 1 : 0; });
    return out;
  }
  function studyDays() {
    var set = {};
    Object.keys(DATA.reviews || {}).forEach(function (id) {
      (DATA.reviews[id].history || []).forEach(function (hrec) { set[hrec.date] = true; });
    });
    (DATA.cards || []).forEach(function (c) { if (c.last_reviewed) set[c.last_reviewed] = true; });
    return set;
  }
  function streak(days) {
    var n = 0, d = new Date();
    if (!days[d.toISOString().slice(0, 10)]) d.setDate(d.getDate() - 1);
    while (days[d.toISOString().slice(0, 10)]) { n++; d.setDate(d.getDate() - 1); }
    return n;
  }

  // ---- shared pieces ----------------------------------------------------
  function bar(percent, label) {
    var fill = h("div", { "class": "fill", role: "progressbar", "aria-label": label,
      "aria-valuemin": "0", "aria-valuemax": "100", "aria-valuenow": String(percent) });
    fill.style.width = percent + "%";
    return h("div", { "class": "track" }, [fill]);
  }
  function card(title, extra, kids) {
    var head = null;
    if (title) {
      head = h("header", null, [h("h2", { text: title })]);
      if (extra) head.appendChild(extra);
    }
    return h("section", { "class": "card" }, [head, h("div", { "class": "body" }, kids)]);
  }
  function statusLegend() {
    return h("div", { "class": "legend" }, Object.keys(LABELS).map(function (s) {
      return h("span", null, [h("span", { "class": "dot " + s }), LABELS[s]]);
    }));
  }
  function topicNode(t, onSelect) {
    var b = h("button", { type: "button", "class": "node", "data-status": t.status,
                          "data-id": t.id, "aria-pressed": "false",
                          on: { click: function () { onSelect(t.id); } } }, [
      h("span", { "class": "t", text: t.phase.order + "." + t.order + " " + t.title }),
      h("span", { "class": "s", text: LABELS[t.status] })
    ]);
    if (t.project_links && t.project_links.length) {
      b.appendChild(h("span", { "class": "p", text: "◆ " + t.project_links.map(function (p) {
        return DATA.project_names[p] || p;
      }).join(", ") }));
    }
    return b;
  }

  // ---- views ------------------------------------------------------------
  var VIEWS = {};

  VIEWS.overview = function () {
    var wrap = h("div", { "class": "stack" });

    var art = h("div", { "class": "art", html:
      // "slice" rather than "none": stretching the viewBox turned the sun into a
      // tall ellipse and skewed the ridges. Cropping the edges is the better trade.
      '<svg width="100%" height="100%" viewBox="0 0 1200 220" preserveAspectRatio="xMidYMid slice" aria-hidden="true">' +
      '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0%" stop-color="var(--hero-a)"/><stop offset="55%" stop-color="var(--hero-b)"/>' +
      '<stop offset="100%" stop-color="var(--hero-c)"/></linearGradient></defs>' +
      '<rect width="1200" height="220" fill="url(#sky)"/>' +
      '<circle cx="980" cy="62" r="30" fill="#ffd9a8" opacity=".85"/>' +
      '<path d="M0 220 L190 96 L330 220Z" fill="#1b1239" opacity=".75"/>' +
      '<path d="M250 220 L470 70 L690 220Z" fill="#241a46" opacity=".8"/>' +
      '<path d="M600 220 L820 108 L1040 220Z" fill="#1b1239" opacity=".7"/>' +
      '<path d="M900 220 L1080 128 L1200 220Z" fill="#241a46" opacity=".8"/>' +
      '<path d="M0 214 C250 180 320 150 520 158 C740 166 820 196 1200 176" stroke="#ffe9c9" ' +
      'stroke-width="5" fill="none" opacity=".55" stroke-dasharray="18 12"/></svg>' });

    var hero = h("div", { "class": "hero" }, [art, h("div", { "class": "inner" }, [
      h("div", null, [
        h("h1", null, ["Your ", h("em", { text: "AI Engineer" }), " journey"]),
        h("p", { text: "Learn. Build. Measure. Explain." }),
        h("div", { "class": "chips" }, [
          h("span", { "class": "chip" }, [h("span", { html: ICON.map }),
            DATA.meta.phase_count + " phases, " + TOTAL + " topics"]),
          h("span", { "class": "chip" }, [h("span", { html: ICON.box }),
            DATA.projects.length + " hands-on projects"]),
          h("span", { "class": "chip" }, [h("span", { html: ICON.check }),
            "Evidence-based progress"])
        ])
      ]),
      h("div", { "class": "quote", text:
        "A topic is only done when the exercise passed, the quiz was scored and you " +
        "explained the concept in your own words." })
    ])]);
    wrap.appendChild(hero);

    var next = available()[0];
    wrap.appendChild(h("div", { "class": "banner" }, [
      h("div", null, [
        h("div", { style: "font-weight:700", text: "Welcome back" }),
        h("div", { "class": "sub", text: next
          ? "Next available: " + next.phase.order + "." + next.order + " " + next.title
          : "Everything with satisfied prerequisites is complete." })
      ]),
      next ? h("button", { "class": "btn", type: "button",
        on: { click: function () { go("#/topic/" + next.id); } } },
        [ "Continue learning ", h("span", { html: ICON.arrow }) ]) : null
    ]));

    var gridCard = card("Curriculum map", h("div", { "class": "legend" }, [
      statusLegend(),
      h("button", { "class": "link", type: "button", text: "Open full roadmap",
                    on: { click: function () { go("#/roadmap"); } } })
    ]), [phaseGrid()]);
    wrap.appendChild(gridCard);

    wrap.appendChild(card("Projects", h("button", { "class": "link", type: "button",
      text: "View all", on: { click: function () { go("#/projects"); } } }),
      [h("div", { "class": "grid" }, DATA.projects.map(projectCard))]));

    return wrap;
  };

  var tidyPhaseGrid = null;
  window.addEventListener("resize", function () {
    if (tidyPhaseGrid) tidyPhaseGrid();
  });

  function phaseGrid() {
    var box = h("div", { "class": "phasegrid" });
    DATA.phases.forEach(function (ph, i) {
      var done = ph.topics.filter(function (t) { return t.status === "done"; }).length;
      var percent = pct(done, ph.topics.length);
      box.appendChild(h("button", { type: "button", "class": "phasecard",
        "data-status": ph.status, "data-phase": ph.id,
        on: { click: function () { go("#/phase/" + ph.id); } } }, [
        h("div", { "class": "top" }, [
          h("span", { "class": "num", text: ("0" + ph.order).slice(-2) }),
          h("span", { "class": "pill", text: LABELS[ph.status] })
        ]),
        h("div", { "class": "name", text: ph.title }),
        bar(percent, "Phase " + ph.order + " progress"),
        h("div", { "class": "meta" }, [
          h("span", { text: done + "/" + ph.topics.length + " topics" }),
          h("span", { text: percent + "%" })
        ])
      ]));
      if (i < DATA.phases.length - 1) {
        box.appendChild(h("span", { "class": "arrow", html: ICON.arrow }));
      }
    });
    // Hide the arrow that would sit at the end of a wrapped row. Compare the two
    // CARDS either side of the arrow: the arrow itself is centred vertically, so
    // its own offsetTop never equals a card's and comparing against it hid them all.
    function tidy() {
      var kids = [].slice.call(box.children);
      kids.forEach(function (el, i) {
        if (!el.classList.contains("arrow")) return;
        var prev = kids[i - 1], nxt = kids[i + 1];
        var sameRow = prev && nxt && prev.offsetTop === nxt.offsetTop;
        el.style.visibility = sameRow ? "visible" : "hidden";
      });
    }
    // Two frames, not one: the grid is still detached when phaseGrid() returns,
    // and a detached element reports offsetTop 0 for everything, which made every
    // arrow look like it was on the same row.
    tidyPhaseGrid = tidy;
    requestAnimationFrame(function () { requestAnimationFrame(tidy); });
    return box;
  }

  function projectCard(p) {
    var phases = (p.primary_phases || []).map(function (id) {
      var ph = DATA.phases.filter(function (x) { return x.id === id; })[0];
      return ph ? "Phase " + ph.order : id;
    }).join(" and ");
    return h("div", { "class": "card", style: "box-shadow:none" }, [
      h("div", { "class": "body" }, [
        h("div", { "class": "row" }, [
          h("span", { "class": "ico", html: ICON[PROJECT_ICON[p.id] || "box"] }),
          h("div", { "class": "grow" }, [
            h("div", { "class": "name", text: p.name }),
            h("div", { "class": "sub", text: phases + (p.state === "new" ? ", new build" : "") })
          ])
        ]),
        h("p", { "class": "sub", text: p.summary }),
        h("div", { "class": "legend", style: "margin-top:8px" },
          (p.tags || []).map(function (t) { return h("span", { "class": "tag", text: t }); })),
        h("p", { "class": "sub", style: "margin-top:8px",
          text: p.path || p.external_url
            ? "Location: " + (p.path || p.external_url)
            : "Location not recorded yet" })
      ])
    ]);
  }

  VIEWS.roadmap = function () {
    var wrap = h("div", { "class": "stack" });
    var controls = h("div", { "class": "legend", style: "gap:10px" }, [
      selectField("status", "Status", [["all", "All statuses"]].concat(
        Object.keys(LABELS).map(function (s) { return [s, LABELS[s]]; }))),
      selectField("source", "Source", [["all", "All sources"]].concat(
        Object.keys(SOURCES).map(function (s) { return [s, SOURCES[s]]; }))),
      selectField("phase", "Phase", [["all", "All phases"]].concat(
        DATA.phases.map(function (p) { return [p.id, "Phase " + p.order + ". " + p.title]; })))
    ]);
    wrap.appendChild(card("Browse " + TOTAL + " topics", null,
      [controls, h("p", { "class": "sub", text:
        "Search from the box at the top. Selecting a topic shows its prerequisites, " +
        "what it unlocks and its lesson." })]));

    var host = h("div", { "class": "stack", id: "topics" });
    wrap.appendChild(host);
    wrap.appendChild(h("div", { "class": "empty", id: "empty", role: "status", text:
      "No topics match this search and filter. Clear the search box or choose All statuses." }));

    DATA.phases.forEach(function (ph) {
      var done = ph.topics.filter(function (t) { return t.status === "done"; }).length;
      host.appendChild(card("Phase " + ph.order + ". " + ph.title,
        h("span", { "class": "sub", text: done + "/" + ph.topics.length + " done" }),
        [h("div", { "class": "grid", "data-phase-grid": ph.id },
          ph.topics.map(function (t) { return topicNode(t, selectTopic); }))]));
    });
    requestAnimationFrame(applyFilters);
    return wrap;
  };

  function selectField(id, label, options) {
    var sel = h("select", { id: "f-" + id, on: { change: applyFilters } },
      options.map(function (o) { return h("option", { value: o[0], text: o[1] }); }));
    if (FILTERS[id]) sel.value = FILTERS[id];
    return h("div", null, [h("label", { "class": "sub", "for": "f-" + id, text: label }), sel]);
  }

  var FILTERS = { status: "all", source: "all", phase: "all" };

  function applyFilters() {
    ["status", "source", "phase"].forEach(function (k) {
      var el = document.getElementById("f-" + k);
      if (el) FILTERS[k] = el.value;
    });
    var term = (document.getElementById("q").value || "").trim().toLowerCase();
    var empty = document.getElementById("empty");
    if (!empty) return;
    var shownTotal = 0;
    DATA.phases.forEach(function (ph) {
      var grid = document.querySelector('[data-phase-grid="' + ph.id + '"]');
      if (!grid) return;
      var shown = 0;
      ph.topics.forEach(function (t) {
        var el = grid.querySelector('[data-id="' + t.id + '"]');
        if (!el) return;
        var hay = (t.title + " " + t.summary + " " + t.id + " " + t.slug).toLowerCase();
        var ok = (term === "" || hay.indexOf(term) !== -1) &&
                 (FILTERS.status === "all" || t.status === FILTERS.status) &&
                 (FILTERS.source === "all" || t.source === FILTERS.source) &&
                 (FILTERS.phase === "all" || ph.id === FILTERS.phase);
        el.style.display = ok ? "" : "none";
        if (ok) shown++;
      });
      grid.closest(".card").style.display = shown ? "" : "none";
      shownTotal += shown;
    });
    empty.style.display = shownTotal === 0 ? "" : "none";
  }

  function selectTopic(id) { go("#/topic/" + id); }

  VIEWS.topic = function (id) {
    var t = byId[id];
    if (!t) return h("div", { "class": "empty", text: "No topic with id " + id });
    var dl = h("dl");
    function row(term, kids) {
      dl.appendChild(h("dt", { text: term }));
      dl.appendChild(h("dd", null, kids));
    }
    row("Summary", [t.summary]);
    row("Phase", [h("button", { "class": "link", type: "button",
      text: "Phase " + t.phase.order + ". " + t.phase.title,
      on: { click: function () { go("#/phase/" + t.phase.id); } } })]);
    row("Learning objectives", [h("ul", { "class": "tight" },
      t.learning_objectives.map(function (o) { return h("li", { text: o }); }))]);
    row("Prerequisites", [(t.prerequisites || []).length
      ? h("ul", { "class": "tight" }, t.prerequisites.map(function (p) {
          var pt = byId[p];
          return h("li", null, [
            h("button", { "class": "link", type: "button",
              text: pt ? pt.phase.order + "." + pt.order + " " + pt.title : p,
              on: { click: function () { go("#/topic/" + p); } } }),
            " - " + (pt ? LABELS[pt.status] : "unknown")
          ]);
        }))
      : "None. This topic can be started immediately."]);
    var next = unlocks[t.id] || [];
    row("Unlocks", [next.length
      ? h("ul", { "class": "tight" }, next.map(function (n) {
          var nt = byId[n];
          return h("li", null, [h("button", { "class": "link", type: "button",
            text: nt ? nt.phase.order + "." + nt.order + " " + nt.title : n,
            on: { click: function () { go("#/topic/" + n); } } })]);
        }))
      : "Nothing depends on this topic."]);
    row("Lesson", [t.scaffolded
      ? h("a", { href: "../" + t.lesson_path, text: "Open lesson.md" })
      : "Not scaffolded yet. The lesson is created when you reach this topic."]);
    var rev = (DATA.reviews || {})[t.id];
    row("Next review", [rev && rev.next_review
      ? rev.next_review + " (interval " + rev.interval_days + " days, reviewed " +
        rev.review_count + " times)"
      : "Not scheduled. Reviews start after the first assessment."]);
    row("Evidence", [evidenceList(t)]);
    if (t.project_links && t.project_links.length) {
      row("Projects", [t.project_links.map(function (p) {
        return DATA.project_names[p] || p;
      }).join(", ")]);
    }

    return h("div", { "class": "stack" }, [
      card(t.phase.order + "." + t.order + " " + t.title,
        h("span", { "class": "pill", text: LABELS[t.status] }),
        [h("p", { "class": "sub", text: t.id + " - " + t.estimated_minutes +
          " minute lesson - " + (SOURCES[t.source] || t.source) }), dl]),
      card("Back", null, [h("button", { "class": "btn ghost", type: "button",
        text: "Back to the roadmap", on: { click: function () { go("#/roadmap"); } } })])
    ]);
  };

  function evidenceList(t) {
    var e = t.evidence || {};
    var ex = e.exercise || {}, qz = e.quiz || {}, exp = e.explanation || {};
    return h("ul", { "class": "tight" }, [
      h("li", { text: "Exercise: " + (ex.passed === true
        ? "passed, " + ex.tests_passed + " tests on " + ex.date : "not recorded") }),
      h("li", { text: "Quiz: " + (qz.percent === null || qz.percent === undefined
        ? "not recorded" : qz.percent + "% on " + qz.date) }),
      h("li", { text: "Explanation: " + (exp.rating === null || exp.rating === undefined
        ? "not rated" : exp.rating + " of 3") })
    ]);
  }

  VIEWS.phase = function (id) {
    var ph = DATA.phases.filter(function (p) { return p.id === id; })[0];
    if (!ph) return h("div", { "class": "empty", text: "No phase with id " + id });
    var done = ph.topics.filter(function (t) { return t.status === "done"; }).length;
    var mins = ph.topics.reduce(function (a, t) { return a + t.estimated_minutes; }, 0);
    return h("div", { "class": "stack" }, [
      card("Phase " + ph.order + ". " + ph.title,
        h("span", { "class": "pill", text: LABELS[ph.status] }), [
        h("p", { "class": "sub", text: ph.description }),
        h("p", { "class": "sub", text: ph.topics.length + " topics, " +
          Math.round(mins / 60 * 10) / 10 + " lesson hours, " + done + " done" }),
        bar(pct(done, ph.topics.length), "Phase " + ph.order + " progress")
      ]),
      card("Topics", null, [h("div", { "class": "grid" },
        ph.topics.map(function (t) { return topicNode(t, selectTopic); }))])
    ]);
  };

  VIEWS.learn = function () {
    var ready = available();
    var scaffolded = allTopics.filter(function (t) { return t.scaffolded; });
    return h("div", { "class": "stack" }, [
      card("Lessons ready to open", null, scaffolded.length ? [
        h("div", { "class": "rowlist" }, scaffolded.map(function (t) {
          return h("div", { "class": "row" }, [
            h("span", { "class": "ico", html: ICON.book }),
            h("div", { "class": "grow" }, [
              h("div", { "class": "name", text: t.phase.order + "." + t.order + " " + t.title }),
              h("div", { "class": "sub", text: t.estimated_minutes + " minutes - " + LABELS[t.status] })
            ]),
            h("a", { "class": "link", href: "../" + t.lesson_path, text: "Open lesson" })
          ]);
        }))
      ] : [h("div", { "class": "empty", text: "No lesson has been scaffolded yet." })]),
      card("Available now", h("span", { "class": "sub",
        text: "prerequisites satisfied" }), [
        h("p", { "class": "sub", text:
          "These are computed from the prerequisite graph, not from a fixed order, which " +
          "is why the just-in-time maths track works without any bookkeeping." }),
        h("div", { "class": "grid" }, ready.slice(0, 12).map(function (t) {
          return topicNode(t, selectTopic);
        }))
      ]),
      card("How a lesson works", null, [
        h("ol", { "class": "tight" }, [
          h("li", { text: "Read lesson.md and run demo.py." }),
          h("li", { text: "Implement the TODOs in exercise.py." }),
          h("li", { text: "Run the lesson's tests until they pass." }),
          h("li", { text: "Answer quiz.md without looking at the answers." }),
          h("li", { text: "Explain the concept in your own words." })
        ]),
        h("p", { "class": "note", text:
          "A topic is marked done only when all four mastery conditions hold. Code that " +
          "passes while you cannot explain it is needs_revision, not done." })
      ])
    ]);
  };

  VIEWS.projects = function () {
    return h("div", { "class": "stack" }, [
      card("Projects", null, [
        h("p", { "class": "sub", text:
          "Four existing projects to measure and improve, and one new build. Their code " +
          "stays in its own repository; this repository holds the baselines, evaluation " +
          "sets and write-ups." }),
        h("div", { "class": "grid" }, DATA.projects.map(projectCard))
      ]),
      card("Topics that exercise a project", null, [
        h("table", null, [
          h("thead", null, [h("tr", null, [h("th", { text: "Topic" }),
            h("th", { text: "Phase" }), h("th", { text: "Project" })])]),
          h("tbody", null, allTopics.filter(function (t) {
            return t.project_links && t.project_links.length;
          }).map(function (t) {
            return h("tr", null, [
              h("td", null, [h("button", { "class": "link", type: "button",
                text: t.phase.order + "." + t.order + " " + t.title,
                on: { click: function () { go("#/topic/" + t.id); } } })]),
              h("td", { text: String(t.phase.order) }),
              h("td", { text: t.project_links.map(function (p) {
                return DATA.project_names[p] || p; }).join(", ") })
            ]);
          }))
        ])
      ]),
      card("Rules", null, [h("ul", { "class": "tight" }, [
        h("li", { text: "Baseline before change. An improvement without one is not an improvement." }),
        h("li", { text: "Simulated results are labelled simulated." }),
        h("li", { text: "No live payment credentials. Mock providers and sandboxes only." }),
        h("li", { text: "Every result records the command that produced it." }),
        h("li", { text: "Every write-up says what the measurement does not cover." })
      ])])
    ]);
  };

  VIEWS.practice = function () {
    var withQuiz = allTopics.filter(function (t) { return t.scaffolded; });
    return h("div", { "class": "stack" }, [
      card("Quizzes", null, withQuiz.length ? [
        h("p", { "class": "sub", text:
          "Each scaffolded topic ships a quiz and a separate answer file. Answer first, " +
          "then open the answers." }),
        h("div", { "class": "rowlist" }, withQuiz.map(function (t) {
          return h("div", { "class": "row" }, [
            h("span", { "class": "ico", html: ICON.check }),
            h("div", { "class": "grow" }, [
              h("div", { "class": "name", text: t.phase.order + "." + t.order + " " + t.title }),
              h("div", { "class": "sub", text: "pass mark " +
                (DATA.meta.foundational_phases.indexOf(t.phase.id) !== -1
                  ? DATA.meta.quiz_threshold.foundational
                  : DATA.meta.quiz_threshold.advanced) + "%" })
            ]),
            h("a", { "class": "link", href: "../" + t.quiz_path, text: "Open quiz" })
          ]);
        }))
      ] : [h("div", { "class": "empty", text: "No quiz has been scaffolded yet." })]),
      card("The mastery gate", null, [
        h("ol", { "class": "tight" }, DATA.meta.mastery_conditions.map(function (c) {
          return h("li", { text: c });
        }))
      ])
    ]);
  };

  var cardIndex = 0, cardFlipped = false;
  VIEWS.flashcards = function () {
    var deck = DATA.cards || [];
    if (!deck.length) {
      return card("Flashcards", null,
        [h("div", { "class": "empty", text: "The deck is empty." })]);
    }
    if (cardIndex >= deck.length) cardIndex = 0;
    var c = deck[cardIndex];
    var face = h("div", { "class": "flashcard" }, [h("div", null, [
      h("div", { text: c.front }),
      cardFlipped ? h("div", { "class": "answer", text: c.back }) : null
    ])]);
    return h("div", { "class": "stack" }, [
      card("Flashcard " + (cardIndex + 1) + " of " + deck.length,
        h("span", { "class": "tag", text: c.topic }), [
        face,
        h("div", { "class": "legend", style: "margin-top:12px;gap:8px" }, [
          h("button", { "class": "btn", type: "button",
            text: cardFlipped ? "Hide the answer" : "Show the answer",
            on: { click: function () { cardFlipped = !cardFlipped; render(); } } }),
          h("button", { "class": "btn ghost", type: "button", text: "Next card",
            on: { click: function () {
              cardIndex = (cardIndex + 1) % deck.length; cardFlipped = false; render();
            } } })
        ]),
        h("p", { "class": "note", text:
          "This page only shows cards. Ratings and scheduling are recorded by " +
          "scripts/review.py, so that one file stays the owner of review state." })
      ]),
      card("Deck", null, [h("table", null, [
        h("thead", null, [h("tr", null, [h("th", { text: "Front" }),
          h("th", { text: "Topic" }), h("th", { text: "Next review" })])]),
        h("tbody", null, deck.map(function (x, i) {
          return h("tr", null, [
            h("td", null, [h("button", { "class": "link", type: "button", text: x.front,
              on: { click: function () { cardIndex = i; cardFlipped = false; render(); } } })]),
            h("td", { text: x.topic }),
            h("td", { text: x.next_review || "never reviewed" })
          ]);
        }))
      ])])
    ]);
  };

  VIEWS.progress = function () {
    var bySource = {};
    allTopics.forEach(function (t) { bySource[t.source] = (bySource[t.source] || 0) + 1; });
    return h("div", { "class": "stack" }, [
      card("Overall", null, [
        h("p", { "class": "sub", text: COUNTS.done + " of " + TOTAL + " topics done (" +
          OVERALL + "%). Effort weighted: " + pct(MIN_DONE, MIN_ALL) + "% of " +
          Math.round(MIN_ALL / 60) + " lesson hours." }),
        bar(OVERALL, "Overall progress"),
        h("p", { "class": "note", text:
          "Only done counts. needs_revision counts as incomplete, deliberately: a topic " +
          "you half know is not something to build on." })
      ]),
      card("By phase", null, [h("table", null, [
        h("thead", null, [h("tr", null, [h("th", { text: "Phase" }), h("th", { text: "Topics" }),
          h("th", { text: "Done" }), h("th", { text: "Hours" }), h("th", { text: "Status" })])]),
        h("tbody", null, DATA.phases.map(function (ph) {
          var done = ph.topics.filter(function (t) { return t.status === "done"; }).length;
          var mins = ph.topics.reduce(function (a, t) { return a + t.estimated_minutes; }, 0);
          return h("tr", null, [
            h("td", null, [h("button", { "class": "link", type: "button",
              text: ph.order + ". " + ph.title,
              on: { click: function () { go("#/phase/" + ph.id); } } })]),
            h("td", { text: String(ph.topics.length) }),
            h("td", { text: String(done) }),
            h("td", { text: String(Math.round(mins / 60 * 10) / 10) }),
            h("td", { text: LABELS[ph.status] })
          ]);
        }))
      ])]),
      card("Where the curriculum came from", null, [h("table", null, [
        h("thead", null, [h("tr", null, [h("th", { text: "Source" }), h("th", { text: "Topics" })])]),
        h("tbody", null, Object.keys(SOURCES).map(function (s) {
          return h("tr", null, [h("td", { text: SOURCES[s] }),
                                h("td", { text: String(bySource[s] || 0) })]);
        }))
      ])])
    ]);
  };

  VIEWS.resources = function () {
    return card("Resources", null, [
      h("ul", { "class": "tight" }, [
        h("li", null, [h("a", { href: "https://roadmap.sh/ai-engineer",
          target: "_blank", rel: "noreferrer", text: "roadmap.sh AI Engineer roadmap" }),
          " - the official topic structure this curriculum is based on"]),
        h("li", null, [h("a", { href: "../roadmap/sources.md", text: "roadmap/sources.md" }),
          " - exactly what was fetched, and every deviation from the official order"]),
        h("li", null, [h("a", { href: "../README.md", text: "README.md" }),
          " - setup, commands and troubleshooting"]),
        h("li", null, [h("a", { href: "../CONTRIBUTING.md", text: "CONTRIBUTING.md" }),
          " - the rules that keep this repository honest"]),
        h("li", null, [h("a", { href: "roadmap.mmd", text: "roadmap.mmd" }),
          " - the full Mermaid graph, all " + TOTAL + " topics and every prerequisite edge"])
      ]),
      h("p", { "class": "note", text:
        "Links are relative to this file. They resolve when the page is opened from " +
        "roadmap/ inside the repository." })
    ]);
  };

  VIEWS.about = function () {
    return h("div", { "class": "stack" }, [
      card("About this page", null, [
        h("p", { text: "Every number here is computed from roadmap/curriculum.json at " +
          "build time. Nothing is typed in by hand, and nothing is estimated." }),
        h("p", { "class": "sub", text:
          "Regenerate it with: python scripts/build_roadmap.py" }),
        h("dl", null, [
          h("dt", { text: "Tracks" }),
          h("dd", null, [h("ul", { "class": "tight" }, DATA.meta.tracks.map(function (t) {
            return h("li", { text: t.name + ": " + t.description });
          }))]),
          h("dt", { text: "Statuses" }),
          h("dd", null, [h("ul", { "class": "tight" }, Object.keys(LABELS).map(function (s) {
            return h("li", { text: LABELS[s] });
          }))]),
          h("dt", { text: "Progress definition" }),
          h("dd", { text: DATA.meta.progress_definition })
        ])
      ]),
      card("Honest by construction", null, [h("ul", { "class": "tight" }, [
        h("li", { text: "Statuses come from the curriculum file, never from this page." }),
        h("li", { text: "The study streak is computed from recorded review dates. With no reviews recorded it is zero, and it says so." }),
        h("li", { text: "Project locations are shown only when they are actually recorded." }),
        h("li", { text: "A lesson link appears only for a topic whose files exist on disk." })
      ])])
    ]);
  };

  // ---- right rail -------------------------------------------------------
  function buildRail() {
    var rail = document.getElementById("rail");
    rail.textContent = "";
    if (ROUTE.view !== "overview") { rail.style.display = "none"; return; }
    rail.style.display = "";

    // Donut.
    var R = 54, C = 2 * Math.PI * R, offset = 0;
    var arcs = ["done", "in_progress", "needs_revision", "not_started"].map(function (s) {
      var frac = TOTAL ? COUNTS[s] / TOTAL : 0;
      var seg = '<circle cx="70" cy="70" r="' + R + '" fill="none" stroke-width="15" ' +
        'stroke="var(--' + ({ done: "dn-br", in_progress: "ip-br",
          needs_revision: "nr-br", not_started: "track" })[s] + ')" ' +
        'stroke-dasharray="' + (frac * C) + ' ' + (C - frac * C) + '" ' +
        'stroke-dashoffset="' + (-offset * C) + '" transform="rotate(-90 70 70)"/>';
      offset += frac;
      return seg;
    }).join("");
    var donut = h("div", { style: "display:flex;gap:14px;align-items:center;flex-wrap:wrap" }, [
      h("div", { style: "position:relative;width:140px;height:140px", html:
        '<svg width="140" height="140" viewBox="0 0 140 140" role="img" ' +
        'aria-label="' + OVERALL + ' percent of topics done">' + arcs + '</svg>' +
        '<div style="position:absolute;inset:0;display:grid;place-items:center;' +
        'font-weight:800;font-size:1.3rem">' + OVERALL + '%</div>' }),
      h("div", { "class": "rowlist", style: "flex:1 1 110px" },
        Object.keys(LABELS).map(function (s) {
          return h("div", { style: "display:flex;justify-content:space-between;gap:8px" }, [
            h("span", null, [h("span", { "class": "dot " + s }), LABELS[s]]),
            h("strong", { text: String(COUNTS[s]) })
          ]);
        }))
    ]);
    rail.appendChild(card("Learning progress", h("button", { "class": "link", type: "button",
      text: "Details", on: { click: function () { go("#/progress"); } } }), [donut]));

    // Streak.
    var days = studyDays(), n = streak(days);
    var names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    var monday = new Date();
    monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
    var week = h("div", { "class": "week" }, names.map(function (nm, i) {
      var d = new Date(monday); d.setDate(monday.getDate() + i);
      var iso = d.toISOString().slice(0, 10);
      var hit = !!days[iso];
      return h("div", { "class": "day" + (hit ? " hit" : ""), title: iso }, [
        h("div", { "class": "mark", html: hit ? ICON.check : "" }), nm
      ]);
    }));
    rail.appendChild(card("Study streak", null, [
      h("div", { "class": "row" }, [
        h("span", { "class": "ico", html: ICON.flame }),
        h("div", { "class": "grow" }, [
          h("div", { style: "font-size:1.4rem;font-weight:800",
                     text: n + (n === 1 ? " day" : " days") }),
          h("div", { "class": "sub", text: n
            ? "Keep it up." : "No reviews recorded yet, so the streak is zero." })
        ])
      ]), week
    ]));

    // Next review.
    var due = dueReviews().slice(0, 4);
    rail.appendChild(card("Next review", due.length
      ? h("button", { "class": "link", type: "button", text: "All",
          on: { click: function () { go("#/progress"); } } })
      : null,
      due.length ? [h("div", { "class": "rowlist" }, due.map(function (r) {
        var when = r.overdue > 0 ? r.overdue + " days overdue"
                 : r.overdue === 0 ? "today" : r.next;
        return h("div", { "class": "row" }, [
          h("span", { "class": "ico", html: ICON.cards }),
          h("div", { "class": "grow" }, [
            h("div", { "class": "name", text: r.title }),
            h("div", { "class": "sub", text: when })
          ])
        ]);
      }))] : [h("p", { "class": "sub", text:
        "Nothing scheduled. Reviews start after a topic's first assessment, so an empty " +
        "queue at the beginning is correct rather than a bug." })]));

    // Projects.
    rail.appendChild(card("Your projects", h("button", { "class": "link", type: "button",
      text: "View all", on: { click: function () { go("#/projects"); } } }),
      [h("div", { "class": "rowlist" }, DATA.projects.map(function (p) {
        var ph = DATA.phases.filter(function (x) {
          return x.id === (p.primary_phases || [])[0]; })[0];
        return h("div", { "class": "row" }, [
          h("span", { "class": "ico", html: ICON[PROJECT_ICON[p.id] || "box"] }),
          h("div", { "class": "grow" }, [
            h("div", { "class": "name", text: p.name }),
            h("div", { "class": "sub", text: ph
              ? "Phase " + ph.order + " - " + LABELS[ph.status] : "unscheduled" })
          ])
        ]);
      }))]));
  }

  // ---- navigation -------------------------------------------------------
  var NAV = [
    { id: "overview", label: "Home", icon: "home", route: "#/overview" },
    { id: "roadmap", label: "Roadmap", icon: "map", route: "#/roadmap" },
    { id: "learn", label: "Learn", icon: "book", route: "#/learn" },
    { id: "projects", label: "Projects", icon: "box", route: "#/projects" },
    { id: "practice", label: "Practice", icon: "check", route: "#/practice" },
    { id: "progress", label: "Progress", icon: "chart", route: "#/progress" }
  ];
  var SIDE = NAV.concat([
    { id: "flashcards", label: "Flashcards", icon: "cards", route: "#/flashcards" },
    { id: "resources", label: "Resources", icon: "link", route: "#/resources" },
    { id: "about", label: "About", icon: "info", route: "#/about" }
  ]);
  var ROUTE = { view: "overview", arg: null };

  function go(hash) {
    if (location.hash === hash) { route(); } else { location.hash = hash; }
  }
  function parse() {
    var parts = (location.hash || "#/overview").replace(/^#\/?/, "").split("/");
    var view = parts[0] || "overview";
    if (!VIEWS[view]) view = "overview";
    return { view: view, arg: parts[1] || null };
  }
  function route() { ROUTE = parse(); render(); }

  function buildNav() {
    var top = document.getElementById("topnav");
    top.textContent = "";
    NAV.forEach(function (item) {
      top.appendChild(h("button", { type: "button",
        on: { click: function () { go(item.route); } } },
        [h("span", { html: ICON[item.icon] }), item.label]));
    });
    var side = document.getElementById("sidenav");
    side.textContent = "";
    SIDE.forEach(function (item) {
      side.appendChild(h("button", { type: "button", "data-nav": item.id,
        on: { click: function () { go(item.route); } } },
        [h("span", { "class": "muted-ico", html: ICON[item.icon] }), item.label]));
      if (item.id === "roadmap") {
        var sub = h("div", { "class": "sub" });
        DATA.phases.forEach(function (ph) {
          sub.appendChild(h("button", { type: "button", "data-phase-nav": ph.id,
            on: { click: function () { go("#/phase/" + ph.id); } },
            text: ("0" + ph.order).slice(-2) + ". " + ph.title }));
        });
        side.appendChild(sub);
      }
    });
  }

  function markNav() {
    [].forEach.call(document.querySelectorAll("#topnav button"), function (b, i) {
      if (NAV[i].id === ROUTE.view) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
    [].forEach.call(document.querySelectorAll("[data-nav]"), function (b) {
      if (b.getAttribute("data-nav") === ROUTE.view) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
    [].forEach.call(document.querySelectorAll("[data-phase-nav]"), function (b) {
      var on = ROUTE.view === "phase" && b.getAttribute("data-phase-nav") === ROUTE.arg;
      if (on) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
  }

  function render() {
    var host = document.getElementById("view");
    host.textContent = "";
    host.appendChild(VIEWS[ROUTE.view](ROUTE.arg));
    markNav();
    buildRail();
    if (ROUTE.view === "roadmap") applyFilters();
  }

  // ---- theme ------------------------------------------------------------
  var mode = "auto";
  try {
    var saved = window.localStorage.getItem("roadmap-theme");
    if (saved === "light" || saved === "dark" || saved === "auto") mode = saved;
  } catch (err) { /* file:// or blocked storage: fall back to the system theme */ }
  function applyTheme() {
    document.documentElement.setAttribute("data-theme", mode);
    document.getElementById("theme-light")
      .setAttribute("aria-pressed", String(mode === "light"));
    document.getElementById("theme-dark")
      .setAttribute("aria-pressed", String(mode === "dark"));
    try { window.localStorage.setItem("roadmap-theme", mode); } catch (err) { /* ignore */ }
  }
  function setTheme(next) { mode = (mode === next) ? "auto" : next; applyTheme(); }

  // ---- boot -------------------------------------------------------------
  document.getElementById("brandmark").innerHTML = ICON.brain;
  document.getElementById("searchicon").innerHTML = ICON.search;
  document.getElementById("goalicon").innerHTML = ICON.flag;
  document.getElementById("theme-light").innerHTML = ICON.sun;
  document.getElementById("theme-dark").innerHTML = ICON.moon;
  document.getElementById("theme-light")
    .addEventListener("click", function () { setTheme("light"); });
  document.getElementById("theme-dark")
    .addEventListener("click", function () { setTheme("dark"); });

  var goalFill = document.getElementById("goal-fill");
  goalFill.style.width = OVERALL + "%";
  goalFill.setAttribute("aria-valuenow", String(OVERALL));
  document.getElementById("goal-text").textContent =
    COUNTS.done + " of " + TOTAL + " topics done (" + OVERALL + "%)";

  document.getElementById("q").addEventListener("input", function () {
    if (ROUTE.view !== "roadmap") go("#/roadmap");
    else applyFilters();
  });
  document.getElementById("q").addEventListener("keydown", function (e) {
    if (e.key === "Escape") { this.value = ""; applyFilters(); }
  });

  window.addEventListener("hashchange", route);
  applyTheme();
  buildNav();
  route();
})();
</script>
</body>
</html>
"""
