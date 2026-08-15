"""Emit a fresh report.html shell and TODO prose, so a session starts from nothing.

    python3 -m pipeline.skeleton sessions/2026-08-08/report

Until now a new session's `report.html` was **copied from the previous session and
hand-edited**. That is how all four committed reports were made, and it is why each
one carries the previous one's mistakes: the small-multiples' "decisive round"
markers said `r.g === 14 || r.g === 26` in three separate reports, because 07-24's
two extreme rounds were copied forward twice without being recomputed.

This module owns the part **no generator owns** — the `<head>`, the `<style>`, the
inline `<script>`, the `<footer>`, and the empty marker regions in document order.
Everything between those markers is then filled by:

    python3 -m pipeline.build_report <report_dir>
    python3 -m pipeline.build_round_table <report_dir>

so the skeleton is written once and never re-run over a live report (it refuses to
overwrite an existing `report.html`; `--force` is for rebuilding a scratch copy).

## Where the region list comes from

`LAYOUT` is document order — the one thing `build_report.SECTIONS` cannot supply,
because `SECTIONS` is *build* order (`chart-data` is built early and lands late).
But every name in `SECTIONS` must appear in `LAYOUT` or in `SELF_INSERTING`, and
`_check_coverage()` fails the build otherwise. Adding a section to `build_report`
without placing it here is therefore an error at skeleton time, not a region that
silently renders empty. That gate fired the first time it was run — `matches`
became a generated region between this file being written and being run.

A `LAYOUT` region whose name `build_report` does **not** own emits fallback markup
instead of a marker pair: a hand-written TODO section. That keeps this file useful
while sections are still being lifted out of the HTML — the same skeleton emits a
marker pair the day the generator lands, with no edit here. Today every entry has a
generator, so no fallback is reachable; one that is reached prints a warning,
because a hand-written `<section>` is exactly what `check_report_shell` refuses.

## Players

The shell is parameterised by `facts["players"]` order. Colour is **positional** —
`--p1` / `--p2` — and the pair itself is unchanged (`dataviz`'s palette validator
passes it on all six checks in both modes; CLAUDE.md: colour is not the thing to
change). What stops being hardcoded is every *name*: the winner/pip/coaching CSS
selectors are emitted from `facts`, and the inline script reads `CD.players` by
position everywhere instead of naming `yachi` and `pinglamb` in 31 places.

`--yachi` / `--pinglamb` survive as **aliases of the two slots**, because
`pipeline/records.py` and `pipeline/build_round_table.py` emit `var(--yachi)`
literally into their own generated CSS. Those two modules are still name-bound;
until they are parameterised the alias is what makes a session with a different
pair render in the right colours rather than in no colour at all.
"""
import argparse
import json
import os

from pipeline import build_report, build_round_table, region

# The producer string `build_report.render` stamps into every marker it owns; the
# marker pair itself is read back out of `build_report.SECTIONS` so an entry with
# its own pair (the claims island) is honoured. If this string ever disagrees with
# build_report's, the skeleton's pairs stop matching and build_report *inserts* a
# second region beside the first. `bin/new-session` runs build_report immediately
# after the skeleton, where that shows up as "inserted:" instead of "replaced:".
PRODUCER = "pipeline/build_report.py"

TODO = "TODO"


# --------------------------------------------------------------------------- CSS

def _css_ident(name):
    """A username as a CSS class suffix (`.rec-col.for-<name>`)."""
    return "".join(c if (c.isalnum() or c in "-_") else "-" for c in name)


def _attr(value):
    """A username inside a quoted CSS attribute selector."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _player_rules(players):
    """The three rule families that select on a player's *name*.

    They are the reason the stylesheet could not be shared between sessions: the
    inline script writes the real username into `data-winner` / `data-w`, and
    `coaching.py` builds `for-<name>` from `facts["players"]`, so the selectors
    have to name the same two people the data does.
    """
    winner, pip, rec = [], [], []
    for i, p in enumerate(players, 1):
        winner.append(f'  .match-card[data-winner="{_attr(p)}"] {{ --accent: var(--p{i}); }}')
        pip.append(f'  .pip[data-w="{_attr(p)}"] {{ background: var(--p{i}); }}')
        rec.append(f'  .rec-col.for-{_css_ident(p)} {{ --accent: var(--p{i}); }}')
    return "\n".join(winner), "\n".join(pip), "\n".join(rec)


CSS = """<style>
  /* ============================= TOKENS ============================= */
  :root {
    --bg: #f5f6fa;
    --bg-raised: #ffffff;
    --bg-sunken: #eceef5;
    --ink: #12141c;
    --ink-secondary: #4b4f5e;
    --muted: #8a8fa3;
    --border: rgba(18, 20, 28, 0.10);
    --border-strong: rgba(18, 20, 28, 0.18);

    /* Player colour is POSITIONAL: slot 1 and slot 2, in facts["players"] order.
       The pair is the validated one — `node scripts/validate_palette.js` passes it
       on all six checks in both modes, so colour is not the thing to change. */
    --p1: #0e8f9e;
    --p1-tint: rgba(14, 143, 158, 0.10);
    --p1-tint-strong: rgba(14, 143, 158, 0.20);
    --p2: #7c3aed;
    --p2-tint: rgba(124, 58, 237, 0.10);
    --p2-tint-strong: rgba(124, 58, 237, 0.20);

    /* Aliases, not a second palette. pipeline/records.py and
       pipeline/build_round_table.py emit `var(--yachi)` / `var(--pinglamb)`
       literally into the CSS of the regions they own, so the two slots have to
       answer to those names as well. A session with a different pair still gets
       slot 1 and slot 2 here, which is the whole point of the indirection. */
    --yachi: var(--p1);
    --yachi-tint: var(--p1-tint);
    --yachi-tint-strong: var(--p1-tint-strong);
    --pinglamb: var(--p2);
    --pinglamb-tint: var(--p2-tint);
    --pinglamb-tint-strong: var(--p2-tint-strong);

    --good: #0ca30c;
    --good-tint: rgba(12, 163, 12, 0.12);
    --pending: #c98500;
    --pending-tint: rgba(201, 133, 0, 0.12);
    --spotlight: #b8860b;
    --spotlight-tint: rgba(184, 134, 11, 0.12);
    --spotlight-tint-strong: rgba(184, 134, 11, 0.22);

    --grid-line: #e1e0d9;
    --shadow: 0 1px 2px rgba(18,20,28,0.04), 0 8px 24px rgba(18,20,28,0.06);

    --font-cjk: "PingFang HK", "Noto Sans HK", "Microsoft JhengHei", "Heiti TC",
      -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --font-mono: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas,
      "Liberation Mono", monospace;

    --content-w: 900px;
    --wide-w: 1180px;
  }

  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0a0d13;
      --bg-raised: #141924;
      --bg-sunken: #10141d;
      --ink: #edeff7;
      --ink-secondary: #b7bcce;
      --muted: #6e7488;
      --border: rgba(255, 255, 255, 0.09);
      --border-strong: rgba(255, 255, 255, 0.17);

      --p1: #1caa9e;
      --p1-tint: rgba(28, 170, 158, 0.16);
      --p1-tint-strong: rgba(28, 170, 158, 0.28);
      --p2: #9678e8;
      --p2-tint: rgba(150, 120, 232, 0.18);
      --p2-tint-strong: rgba(150, 120, 232, 0.30);

      --good: #23c923;
      --good-tint: rgba(35, 201, 35, 0.16);
      --pending: #fab219;
      --pending-tint: rgba(250, 178, 25, 0.16);
      --spotlight: #e8b94a;
      --spotlight-tint: rgba(232, 185, 74, 0.16);
      --spotlight-tint-strong: rgba(232, 185, 74, 0.26);

      --grid-line: #262b38;
      --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 12px 32px rgba(0,0,0,0.35);
    }
  }
  :root[data-theme="dark"] {
    --bg: #0a0d13; --bg-raised: #141924; --bg-sunken: #10141d;
    --ink: #edeff7; --ink-secondary: #b7bcce; --muted: #6e7488;
    --border: rgba(255, 255, 255, 0.09); --border-strong: rgba(255, 255, 255, 0.17);
    --p1: #1caa9e; --p1-tint: rgba(28, 170, 158, 0.16); --p1-tint-strong: rgba(28, 170, 158, 0.28);
    --p2: #9678e8; --p2-tint: rgba(150, 120, 232, 0.18); --p2-tint-strong: rgba(150, 120, 232, 0.30);
    --good: #23c923; --good-tint: rgba(35, 201, 35, 0.16);
    --pending: #fab219; --pending-tint: rgba(250, 178, 25, 0.16);
    --spotlight: #e8b94a; --spotlight-tint: rgba(232, 185, 74, 0.16); --spotlight-tint-strong: rgba(232, 185, 74, 0.26);
    --grid-line: #262b38; --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 12px 32px rgba(0,0,0,0.35);
  }
  :root[data-theme="light"] {
    --bg: #f5f6fa; --bg-raised: #ffffff; --bg-sunken: #eceef5;
    --ink: #12141c; --ink-secondary: #4b4f5e; --muted: #8a8fa3;
    --border: rgba(18, 20, 28, 0.10); --border-strong: rgba(18, 20, 28, 0.18);
    --p1: #0e8f9e; --p1-tint: rgba(14, 143, 158, 0.10); --p1-tint-strong: rgba(14, 143, 158, 0.20);
    --p2: #7c3aed; --p2-tint: rgba(124, 58, 237, 0.10); --p2-tint-strong: rgba(124, 58, 237, 0.20);
    --good: #0ca30c; --good-tint: rgba(12, 163, 12, 0.12);
    --pending: #c98500; --pending-tint: rgba(201, 133, 0, 0.12);
    --spotlight: #b8860b; --spotlight-tint: rgba(184, 134, 11, 0.12); --spotlight-tint-strong: rgba(184, 134, 11, 0.22);
    --grid-line: #e1e0d9; --shadow: 0 1px 2px rgba(18,20,28,0.04), 0 8px 24px rgba(18,20,28,0.06);
  }

  /* ============================= RESET / BASE ============================= */
  * { box-sizing: border-box; }
  html { color-scheme: light dark; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: var(--font-cjk);
    font-size: 17px;
    line-height: 1.75;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
  }
  h1, h2, h3, h4 { text-wrap: balance; margin: 0; font-family: var(--font-cjk); }
  p { margin: 0 0 1em; }
  p:last-child { margin-bottom: 0; }
  a { color: inherit; }
  .mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
  ::selection { background: var(--p2-tint-strong); }

  @media (prefers-reduced-motion: reduce) {
    * { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; scroll-behavior: auto !important; }
  }

  /* ============================= LAYOUT SHELL ============================= */
  .wrap { max-width: var(--content-w); margin: 0 auto; padding: 0 24px; }
  .wrap-wide { max-width: var(--wide-w); margin: 0 auto; padding: 0 24px; }

  section { padding: 72px 0; }
  section + section { border-top: 1px solid var(--border); }

  .eyebrow {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
  }
  .eyebrow::before {
    content: "";
    width: 22px; height: 2px;
    background: linear-gradient(90deg, var(--p1), var(--p2));
    display: inline-block;
    border-radius: 2px;
  }
  .section-title { font-size: clamp(1.6rem, 3vw, 2.2rem); font-weight: 800; letter-spacing: -0.01em; }
  .section-lede { color: var(--ink-secondary); font-size: 1.05rem; max-width: 62ch; margin-top: 14px; }

  /* ============================= HERO ============================= */
  .hero {
    position: relative;
    padding: 96px 0 72px;
    background:
      radial-gradient(ellipse 900px 420px at 18% -10%, var(--p1-tint), transparent 60%),
      radial-gradient(ellipse 900px 420px at 84% 0%, var(--p2-tint), transparent 60%);
    overflow: hidden;
  }
  .hero-blocks {
    position: absolute; inset: 0; pointer-events: none; opacity: 0.5;
  }
  .hero-meta {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--muted);
    letter-spacing: 0.04em;
    margin-bottom: 28px;
  }
  .hero-title {
    font-size: clamp(1.9rem, 4.4vw, 3rem);
    font-weight: 800;
    letter-spacing: -0.015em;
    line-height: 1.28;
    max-width: 24ch;
  }
  .hero-title .hl-y { color: var(--p1); }
  .hero-title .hl-p { color: var(--p2); }

  .scoreboard {
    margin-top: 44px;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 20px;
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 30px clamp(16px, 4vw, 44px);
    box-shadow: var(--shadow);
  }
  .sb-player { display: flex; flex-direction: column; gap: 6px; }
  .sb-player.p-right { align-items: flex-end; text-align: right; }
  .sb-name { font-size: clamp(1.1rem, 2.4vw, 1.5rem); font-weight: 800; }
  .sb-player.p-left .sb-name { color: var(--p1); }
  .sb-player.p-right .sb-name { color: var(--p2); }
  .sb-tag { font-family: var(--font-mono); font-size: 0.76rem; color: var(--muted); letter-spacing: 0.06em; }
  .sb-mid { text-align: center; }
  .sb-score {
    font-family: var(--font-mono);
    font-weight: 800;
    font-size: clamp(2.6rem, 8vw, 4.4rem);
    letter-spacing: -0.02em;
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }
  .sb-score .sep { color: var(--muted); font-weight: 500; padding: 0 0.06em; }
  .sb-score .y { color: var(--p1); }
  .sb-score .p { color: var(--p2); }
  .sb-sub { margin-top: 6px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--muted); }

  .hero-lede { margin-top: 30px; max-width: 68ch; color: var(--ink-secondary); font-size: 1.06rem; }
  .hero-lede strong { color: var(--ink); font-weight: 700; }

  /* ============================= BADGE (claim chip) ============================= */
  .badge {
    display: inline-flex;
    align-items: baseline;
    gap: 0.28em;
    font-family: var(--font-mono);
    font-size: 0.68em;
    font-weight: 700;
    letter-spacing: 0.02em;
    padding: 0.12em 0.5em;
    margin: 0 0.1em;
    border-radius: 999px;
    border: 1px solid var(--border-strong);
    background: var(--bg-sunken);
    color: var(--ink-secondary);
    text-decoration: none;
    vertical-align: 0.5em;
    line-height: 1;
    white-space: nowrap;
    cursor: pointer;
  }
  .badge[data-status="verified"] { border-color: color-mix(in srgb, var(--good) 55%, var(--border-strong)); background: var(--good-tint); color: var(--good); }
  .badge[data-status="pending"] { border-color: color-mix(in srgb, var(--pending) 45%, var(--border-strong)); background: var(--pending-tint); color: var(--pending); }
  .badge:hover { filter: brightness(1.08); }
  .badge .ic { font-size: 0.95em; }

  /* ============================= MATCH TIMELINE ============================= */
  .timeline { display: flex; flex-direction: column; gap: 20px; margin-top: 48px; }
  .match-card {
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 28px clamp(18px, 3.4vw, 34px);
    position: relative;
    overflow: hidden;
    opacity: 0;
    transform: translateY(14px);
    transition: opacity 0.5s ease, transform 0.5s ease;
  }
  .match-card.in-view { opacity: 1; transform: translateY(0); }
  .match-card::before {
    content: "";
    position: absolute; left: 0; top: 0; bottom: 0; width: 5px;
    background: var(--accent);
  }
@@WINNER_ACCENTS@@
  .match-card.hero-match {
    background: linear-gradient(155deg, var(--spotlight-tint), var(--bg-raised) 42%);
    border-color: color-mix(in srgb, var(--spotlight) 40%, var(--border));
  }
  .match-card.hero-match::before { background: var(--spotlight); width: 6px; }

  .mc-head {
    display: flex; align-items: baseline; justify-content: space-between; gap: 16px;
    flex-wrap: wrap;
  }
  .mc-idx { font-family: var(--font-mono); color: var(--muted); font-size: 0.85rem; letter-spacing: 0.06em; }
  .mc-title { font-size: 1.24rem; font-weight: 800; margin-top: 4px; }
  .mc-score {
    font-family: var(--font-mono); font-weight: 800; font-size: 1.5rem;
    font-variant-numeric: tabular-nums; white-space: nowrap;
  }
  .mc-score .y { color: var(--p1); }
  .mc-score .p { color: var(--p2); }
  .mc-score .sep { color: var(--muted); font-weight: 500; }

  .pip-trail { display: flex; gap: 5px; margin: 16px 0 18px; flex-wrap: wrap; }
  .pip {
    width: 15px; height: 15px; border-radius: 4px;
    display: inline-block;
  }
@@PIP_COLOURS@@
  .pip[title] { cursor: default; }

  .mc-body { color: var(--ink-secondary); font-size: 0.98rem; }
  .mc-body strong { color: var(--ink); font-weight: 700; }

  .match-card.hero-match .mc-title { font-size: 1.5rem; }
  .hero-flag {
    display: inline-flex; align-items: center; gap: 6px;
    font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.08em;
    color: var(--spotlight); background: var(--spotlight-tint-strong);
    border: 1px solid color-mix(in srgb, var(--spotlight) 50%, transparent);
    padding: 4px 10px; border-radius: 999px; margin-bottom: 10px;
  }

  blockquote.closer {
    margin: 40px 0 0; padding: 26px 30px; border-radius: 16px;
    background: linear-gradient(120deg, var(--p1-tint), var(--p2-tint));
    border: 1px solid var(--border);
    font-size: 1.06rem; color: var(--ink);
    font-weight: 600;
  }

  /* ============================= CHARTS ============================= */
  .legend-row {
    display: flex; gap: 22px; align-items: center; margin: 30px 0 26px; flex-wrap: wrap;
    font-family: var(--font-mono); font-size: 0.82rem; color: var(--ink-secondary);
  }
  .legend-row .sw { display: inline-flex; align-items: center; gap: 7px; }
  .legend-row .dot { width: 10px; height: 10px; border-radius: 3px; }
  .legend-row .dot.y { background: var(--p1); }
  .legend-row .dot.p { background: var(--p2); }

  .chart-panel {
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: clamp(16px, 3vw, 30px);
    margin-top: 28px;
  }
  .chart-panel h3 { font-size: 1.1rem; font-weight: 800; margin-bottom: 4px; }
  .chart-panel .cap { color: var(--muted); font-size: 0.86rem; margin-bottom: 18px; }
  .chart-panel .footnote { color: var(--muted); font-size: 0.78rem; margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--border); }
  .scroll-x { overflow-x: auto; }

  .sm-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 14px;
  }
  .sm-cell {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 12px 6px;
    background: var(--bg-sunken);
  }
  .sm-cell-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }
  .sm-cell-title { font-family: var(--font-mono); font-size: 0.78rem; font-weight: 700; color: var(--ink); }
  .sm-cell-score { font-family: var(--font-mono); font-size: 0.72rem; color: var(--muted); }
  .sm-cell svg { display: block; width: 100%; height: auto; }

  svg text { font-family: var(--font-mono); fill: var(--muted); }
  .axis-line { stroke: var(--grid-line); stroke-width: 1; }
  .grid-line { stroke: var(--grid-line); stroke-width: 1; stroke-dasharray: 2 3; }

  /* ============================= STAT GRID (關鍵時刻) ============================= */
  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 34px; }
  .stat-card {
    background: var(--bg-raised); border: 1px solid var(--border); border-radius: 16px;
    padding: 22px 22px 20px;
  }
  .stat-card .k { font-family: var(--font-mono); font-size: 0.74rem; letter-spacing: 0.08em; color: var(--muted); text-transform: uppercase; }
  .stat-card .v { font-family: var(--font-mono); font-weight: 800; font-size: 1.85rem; margin: 8px 0 10px; letter-spacing: -0.01em; }
  .stat-card .d { font-size: 0.92rem; color: var(--ink-secondary); }
  .stat-card.accent-y { border-top: 3px solid var(--p1); }
  .stat-card.accent-p { border-top: 3px solid var(--p2); }
  .stat-card.accent-g { border-top: 3px solid var(--spotlight); }

  .trivia-list { margin-top: 30px; display: flex; flex-direction: column; gap: 14px; }
  .trivia-item {
    display: flex; gap: 14px; align-items: flex-start;
    padding: 16px 18px; border: 1px solid var(--border); border-radius: 14px; background: var(--bg-raised);
  }
  .trivia-item .num { font-family: var(--font-mono); font-weight: 800; color: var(--muted); font-size: 0.9rem; padding-top: 2px; }
  .trivia-item .txt { color: var(--ink-secondary); }
  .trivia-item .txt strong { color: var(--ink); }

  /* ============================= RECOMMENDATIONS ============================= */
  .rec-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; margin-top: 40px; }
  @media (max-width: 760px) { .rec-grid { grid-template-columns: 1fr; } }
  .rec-col {
    background: var(--bg-raised); border: 1px solid var(--border); border-radius: 18px;
    padding: 26px clamp(18px, 3vw, 30px); border-top: 4px solid var(--accent);
  }
@@REC_COLS@@
  .rec-col h3 { font-size: 1.2rem; font-weight: 800; color: var(--accent); }
  .rec-col .profile { margin-top: 10px; color: var(--ink-secondary); font-size: 0.96rem; }
  .rec-col .profile p { margin-bottom: 0.85em; }
  .rec-col .profile strong { color: var(--ink); }
  .rec-list { list-style: none; margin: 20px 0 0; padding: 0; display: flex; flex-direction: column; gap: 16px; }
  .rec-list li {
    padding-top: 14px; border-top: 1px dashed var(--border);
    color: var(--ink-secondary); font-size: 0.95rem;
  }
  .rec-list li:first-child { border-top: none; padding-top: 0; }
  .rec-list li strong { color: var(--ink); }
  .rec-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 22px; height: 22px; border-radius: 7px; background: var(--accent);
    color: #fff; font-family: var(--font-mono); font-weight: 800; font-size: 0.78rem;
    margin-right: 8px; vertical-align: -4px;
  }
  .versus-note {
    margin-top: 26px; padding: 18px 20px; border-radius: 14px; background: var(--bg-sunken);
    color: var(--ink-secondary); font-size: 0.95rem; grid-column: 1 / -1;
  }

  /* ============================= APPENDIX ============================= */
  .method-note {
    margin-top: 34px; padding: 22px 26px; border-radius: 16px;
    background: var(--bg-raised); border: 1px solid var(--border);
    color: var(--ink-secondary); font-size: 0.98rem;
  }
  .method-note .chain { display: flex; flex-direction: column; gap: 10px; margin: 16px 0; }
  .chain-step { display: flex; gap: 12px; align-items: flex-start; }
  .chain-step .n {
    flex: none; width: 26px; height: 26px; border-radius: 8px;
    background: var(--bg-sunken); border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-family: var(--font-mono); font-size: 0.78rem; font-weight: 800; color: var(--ink-secondary);
  }
  #status-line {
    font-family: var(--font-mono); font-size: 0.86rem; margin-top: 16px;
    display: inline-flex; align-items: center; gap: 8px;
    padding: 8px 14px; border-radius: 999px; background: var(--pending-tint); color: var(--pending);
    border: 1px solid color-mix(in srgb, var(--pending) 40%, transparent);
  }
  #status-line[data-all-verified="true"] { background: var(--good-tint); color: var(--good); border-color: color-mix(in srgb, var(--good) 40%, transparent); }

  table.appendix-table {
    width: 100%; border-collapse: collapse; margin-top: 26px; min-width: 880px;
    font-size: 0.92rem;
  }
  table.appendix-table th, table.appendix-table td {
    text-align: left; padding: 11px 14px; border-bottom: 1px solid var(--border);
    vertical-align: top;
  }
  table.appendix-table thead th {
    font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--muted); border-bottom: 1px solid var(--border-strong); position: sticky; top: 0; background: var(--bg-raised);
  }
  table.appendix-table td.id-cell { font-family: var(--font-mono); font-weight: 700; white-space: nowrap; }
  table.appendix-table td.canto-cell { max-width: 46ch; }
  table.appendix-table td.gloss-cell { max-width: 34ch; color: var(--ink-secondary); font-size: 0.88rem; }
  table.appendix-table td.lemma-cell { font-family: var(--font-mono); font-size: 0.84rem; color: var(--ink-secondary); white-space: nowrap; }
  table.appendix-table tr[id] { scroll-margin-top: 20px; }
  table.appendix-table tr:target { background: var(--p2-tint); }
  .status-pill {
    display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px;
    font-family: var(--font-mono); font-size: 0.78rem; font-weight: 700; white-space: nowrap;
  }
  .status-pill[data-status="verified"] { background: var(--good-tint); color: var(--good); }
  .status-pill[data-status="pending"] { background: var(--pending-tint); color: var(--pending); }

  footer.report-footer {
    padding: 40px 0 60px; text-align: center; color: var(--muted); font-size: 0.86rem;
    font-family: var(--font-mono);
  }
</style>"""


# ---------------------------------------------------------------------- SCRIPT

SCRIPT = r"""<script>
(function () {
  "use strict";

  var CD = JSON.parse(document.getElementById("chart-data").textContent);
  var MATCH_COPY_DATA = JSON.parse(document.getElementById("match-copy").textContent);
  var MATCH_COPY = MATCH_COPY_DATA.cards;
  /* Players by position, never by name. The island carries the pair, so every
     renderer below works for any two players instead of only these two. */
  var PLAYERS = CD.players;
  var CLAIMS = null; // populated after claims-data parse below
  var CLAIM_MAP = {};

  /* Colour is positional too: slot i of PLAYERS paints with --p{i+1}. The
     stylesheet defines those; --yachi / --pinglamb survive only as aliases for
     the regions whose generators still emit those names. */
  function slotColour(i) { return "var(--p" + (i + 1) + ")"; }

  function parseClaimsData() {
    var raw = JSON.parse(document.getElementById("claims-data").textContent);
    CLAIMS = raw;
    CLAIM_MAP = {};
    (raw.claims || []).forEach(function (c) { CLAIM_MAP[c.id] = c; });
  }

  /* The two rounds the small multiples draw with a bigger dot: the session's
     longest and its shortest. These were two hand-typed `r.g === N` literals per
     report, and copying a report forward copied them — three of the four committed
     reports carry 07-24's pair, marking two unremarkable rounds while the real
     marathon went unmarked. `chart_data.extreme_rounds` derives them, so they sit
     inside `build_report --check` rather than in a script nothing regenerates. */
  var EXTREME = CD.extreme_rounds || {};

  // ---------- badge rendering ----------
  function statusIcon(status) { return status === "verified" ? "✓" : "⏳"; }

  function renderInlineBadge(el) {
    var id = el.getAttribute("data-claim");
    var c = CLAIM_MAP[id];
    var status = c ? c.status : "pending";
    el.setAttribute("data-status", status);
    el.setAttribute("href", "#claim-" + id);
    while (el.firstChild) el.removeChild(el.firstChild);
    var ic = document.createElement("span");
    ic.className = "ic";
    ic.textContent = statusIcon(status);
    el.appendChild(ic);
    el.appendChild(document.createTextNode(id));
    if (c) el.setAttribute("title", c.english_gloss || "");
  }

  function renderAllBadges(root) {
    (root || document).querySelectorAll(".badge[data-claim]").forEach(function (el) {
      if (el.tagName.toLowerCase() !== "a") {
        var a = document.createElement("a");
        for (var i = 0; i < el.attributes.length; i++) {
          a.setAttribute(el.attributes[i].name, el.attributes[i].value);
        }
        a.className = el.className;
        el.replaceWith(a);
        el = a;
      }
      renderInlineBadge(el);
    });
  }

  // expand <b>C007</b> shorthand inside injected match-copy html into real badge anchors
  function expandShorthandBadges(html) {
    return html.replace(/<b>([CGR]\d{3})<\/b>/g, function (_, id) {
      return '<span class="badge" data-claim="' + id + '"></span>';
    });
  }


  // ---------- match timeline ----------
  function buildPipTrail(matchIndex) {
    var rounds = CD.round_series.filter(function (r) { return r.match === matchIndex; });
    var wrap = document.createElement("div");
    wrap.className = "pip-trail";
    rounds.forEach(function (r) {
      var pip = document.createElement("span");
      pip.className = "pip";
      pip.setAttribute("data-w", r.winner);
      pip.title = "第" + (r.round_in_match + 1) + "局 · " + r.winner + " 贏";
      wrap.appendChild(pip);
    });
    return wrap;
  }

  function renderTimeline() {
    var timeline = document.getElementById("timeline");
    CD.per_match.forEach(function (m) {
      var copy = MATCH_COPY[String(m.index)];
      var card = document.createElement("article");
      card.className = "match-card reveal" +
        (m.index === MATCH_COPY_DATA.hero_match ? " hero-match" : "");
      card.setAttribute("data-winner", m.winner);

      var head = document.createElement("div");
      head.className = "mc-head";

      var titleWrap = document.createElement("div");
      var idx = document.createElement("div");
      idx.className = "mc-idx";
      idx.textContent = "第 " + m.index + " 場 · MATCH " + m.index;
      titleWrap.appendChild(idx);

      if (copy.flag) {
        var flag = document.createElement("div");
        flag.className = "hero-flag";
        flag.textContent = "🏆 " + copy.flag;
        titleWrap.appendChild(flag);
      }

      var title = document.createElement("div");
      title.className = "mc-title";
      title.textContent = copy.title;
      titleWrap.appendChild(title);
      head.appendChild(titleWrap);

      var score = document.createElement("div");
      score.className = "mc-score";
      /* Built as nodes, not as an innerHTML string. The values here come from
         facts.json, but assembling markup by concatenation is exactly how a
         value becomes markup, so the pattern is not kept around. */
      [["y", m.score[PLAYERS[0]]], ["sep", ":"], ["p", m.score[PLAYERS[1]]]]
        .forEach(function (pair) {
          var span = document.createElement("span");
          span.className = pair[0];
          span.textContent = pair[1];
          score.appendChild(span);
        });
      if (MATCH_COPY_DATA.score_claim) {
        score.appendChild(document.createTextNode(" "));
        var scoreBadge = document.createElement("span");
        scoreBadge.className = "badge";
        scoreBadge.setAttribute("data-claim", MATCH_COPY_DATA.score_claim);
        score.appendChild(scoreBadge);
      }
      head.appendChild(score);

      card.appendChild(head);
      card.appendChild(buildPipTrail(m.index));

      var body = document.createElement("div");
      body.className = "mc-body";
      body.innerHTML = "<p>" + expandShorthandBadges(copy.body) + "</p>";
      card.appendChild(body);

      timeline.appendChild(card);
    });

    renderAllBadges(timeline);

    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches && "IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add("in-view"); io.unobserve(e.target); }
        });
      }, { threshold: 0.12 });
      document.querySelectorAll(".match-card").forEach(function (el) { io.observe(el); });
    } else {
      document.querySelectorAll(".match-card").forEach(function (el) { el.classList.add("in-view"); });
    }
  }

  // ---------- SVG helpers ----------
  var SVGNS = "http://www.w3.org/2000/svg";
  function svgEl(tag, attrs) {
    var el = document.createElementNS(SVGNS, tag);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  // ---------- chart: per-match VS small multiples ----------
  function renderVsSmallMultiples() {
    var grid = document.getElementById("vs-small-multiples");
    if (!grid) return;
    var W = 260, H = 130, PAD_L = 30, PAD_R = 10, PAD_T = 10, PAD_B = 20;
    var plotW = W - PAD_L - PAD_R, plotH = H - PAD_T - PAD_B;

    CD.per_match.forEach(function (m) {
      var rounds = CD.round_series.filter(function (r) { return r.match === m.index; });
      var maxVs = 0;
      rounds.forEach(function (r) {
        PLAYERS.forEach(function (p) { maxVs = Math.max(maxVs, r[p].vs); });
      });
      maxVs = Math.ceil(maxVs / 20) * 20;

      var cell = document.createElement("div");
      cell.className = "sm-cell";

      var head = document.createElement("div");
      head.className = "sm-cell-head";
      var t = document.createElement("div"); t.className = "sm-cell-title"; t.textContent = "m" + m.index;
      var s = document.createElement("div"); s.className = "sm-cell-score";
      s.textContent = m.score[PLAYERS[0]] + ":" + m.score[PLAYERS[1]];
      head.appendChild(t); head.appendChild(s);
      cell.appendChild(head);

      var svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "m" + m.index + " vs score per round" });

      function xAt(i) { return PAD_L + (rounds.length === 1 ? 0 : (i / (rounds.length - 1)) * plotW); }
      function yAt(v) { return PAD_T + plotH - (v / maxVs) * plotH; }

      // gridline baseline
      svg.appendChild(svgEl("line", { class: "axis-line", x1: PAD_L, x2: W - PAD_R, y1: PAD_T + plotH, y2: PAD_T + plotH }));
      // y tick label (max)
      var maxLabel = svgEl("text", { x: 2, y: PAD_T + 4, "font-size": 8 });
      maxLabel.textContent = Math.round(maxVs);
      svg.appendChild(maxLabel);
      var zeroLabel = svgEl("text", { x: 2, y: PAD_T + plotH + 3, "font-size": 8 });
      zeroLabel.textContent = "0";
      svg.appendChild(zeroLabel);

      PLAYERS.forEach(function (p, pi) {
        var pts = rounds.map(function (r, i) { return xAt(i) + "," + yAt(r[p].vs); }).join(" ");
        svg.appendChild(svgEl("polyline", {
          points: pts, fill: "none",
          stroke: slotColour(pi), "stroke-width": 2,
          "stroke-linecap": "round", "stroke-linejoin": "round"
        }));
        rounds.forEach(function (r, i) {
          var isLast = i === rounds.length - 1;
          // last round of the match, or the session's longest / shortest round
          var isDecisive = isLast || r.g === EXTREME.longest_g || r.g === EXTREME.shortest_g;
          var c = svgEl("circle", {
            cx: xAt(i), cy: yAt(r[p].vs), r: isDecisive ? 3.4 : 2.2,
            fill: slotColour(pi),
            stroke: "var(--bg-raised)", "stroke-width": isDecisive ? 1.5 : 0
          });
          var title = svgEl("title", {});
          title.textContent = p + " · 第" + (i + 1) + "局 · vs " + r[p].vs.toFixed(1);
          c.appendChild(title);
          svg.appendChild(c);
        });
      });

      cell.appendChild(svg);
      grid.appendChild(cell);
    });
  }

  // ---------- chart: clears grouped bar ----------
  function renderClearsBar() {
    var mount = document.getElementById("clears-bar-chart");
    if (!mount) return;
    var cats = [
      { key: "singles", label: "Single" },
      { key: "doubles", label: "Double" },
      { key: "triples", label: "Triple" },
      { key: "quads", label: "Quad" },
      { key: "tspin_singles", label: "TSS" },
      { key: "tspin_doubles", label: "TSD" },
      { key: "tspin_triples", label: "TST" }
    ];
    var gc = CD.grouped_clears;
    var maxVal = 0;
    cats.forEach(function (c) {
      PLAYERS.forEach(function (p) { maxVal = Math.max(maxVal, gc[p][c.key]); });
    });
    maxVal = Math.ceil(maxVal / 100) * 100;

    var groupW = 96, barW = 30, gap = 4, PAD_L = 40, PAD_T = 26, PAD_B = 30;
    var plotH = 230;
    var W = PAD_L + cats.length * groupW + 20, H = PAD_T + plotH + PAD_B;

    var svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, style: "width:100%;min-width:" + W + "px;height:auto;" });

    // gridlines
    var steps = 4;
    for (var s = 0; s <= steps; s++) {
      var val = (maxVal / steps) * s;
      var y = PAD_T + plotH - (val / maxVal) * plotH;
      svg.appendChild(svgEl("line", { class: "grid-line", x1: PAD_L, x2: W - 10, y1: y, y2: y }));
      var lbl = svgEl("text", { x: PAD_L - 8, y: y + 3, "font-size": 9, "text-anchor": "end" });
      lbl.textContent = Math.round(val);
      svg.appendChild(lbl);
    }
    svg.appendChild(svgEl("line", { class: "axis-line", x1: PAD_L, x2: W - 10, y1: PAD_T + plotH, y2: PAD_T + plotH }));

    cats.forEach(function (c, i) {
      var gx = PAD_L + i * groupW + groupW / 2;
      PLAYERS.forEach(function (p, pi) {
        var v = gc[p][c.key];
        var barH = (v / maxVal) * plotH;
        var bx = gx - barW - gap / 2 + pi * (barW + gap);
        var by = PAD_T + plotH - barH;
        svg.appendChild(svgEl("rect", {
          x: bx, y: by, width: barW, height: Math.max(barH, 1),
          rx: 4, ry: 4, fill: slotColour(pi)
        }));
        var valLabel = svgEl("text", { x: bx + barW / 2, y: by - 5, "font-size": 9.5, "text-anchor": "middle", fill: "var(--ink-secondary)" });
        valLabel.setAttribute("font-family", "var(--font-mono)");
        valLabel.textContent = v;
        svg.appendChild(valLabel);
        var t = svgEl("title", {});
        t.textContent = p + " · " + c.label + " · " + v;
        var hit = svgEl("rect", { x: bx, y: PAD_T, width: barW, height: plotH, fill: "transparent" });
        hit.appendChild(t);
        svg.appendChild(hit);
      });
      var catLabel = svgEl("text", { x: gx, y: PAD_T + plotH + 18, "font-size": 10.5, "text-anchor": "middle", "font-weight": "700", fill: "var(--ink)" });
      catLabel.textContent = c.label;
      svg.appendChild(catLabel);
    });

    mount.appendChild(svg);
  }

  // ---------- chart: tale of the tape (dumbbell rows, independent scales) ----------
  function renderTapeChart() {
    var mount = document.getElementById("tape-chart");
    if (!mount) return;
    var t = CD.totals;
    /* One row = one measure, read out of each player's totals by the same
       accessor. The row no longer carries a `y` and a `p` key, which is what tied
       this chart to two particular usernames. */
    var rows = [
      { label: "落子總數（粒）", get: function (s) { return s.pieces; }, fmt: function (v) { return Math.round(v); } },
      { label: "每粒攻擊", get: function (s) { return s.attack_per_piece; }, fmt: function (v) { return v.toFixed(3); } },
      { label: "總攻擊行數", get: function (s) { return s.garbage_attack; }, fmt: function (v) { return Math.round(v); } },
      { label: "清垃圾行數", get: function (s) { return s.garbage_cleared; }, fmt: function (v) { return Math.round(v); } },
      { label: "finesse 失誤率", get: function (s) { return s.finesse_fault_rate; }, fmt: function (v) { return (v * 100).toFixed(1) + "%"; }, lowerBetter: true },
      { label: "hold 使用率", get: function (s) { return s.hold_rate; }, fmt: function (v) { return (v * 100).toFixed(1) + "%"; } }
    ];

    var W = 640, rowH = 60, PAD_L = 150, PAD_R = 70, PAD_T = 14;
    var plotW = W - PAD_L - PAD_R;
    var H = PAD_T * 2 + rows.length * rowH;
    var svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, style: "width:100%;min-width:520px;height:auto;" });

    rows.forEach(function (r, i) {
      var vals = PLAYERS.map(function (p) { return r.get(t[p]); });
      var cy = PAD_T + i * rowH + rowH / 2;
      var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
      var span = hi - lo || 1;
      var padFrac = 0.28;
      var loX = lo - span * padFrac, hiX = hi + span * padFrac;
      function xAt(v) { return PAD_L + ((v - loX) / (hiX - loX)) * plotW; }

      var rowLabel = svgEl("text", { x: 0, y: cy + 4, "font-size": 11.5, fill: "var(--ink)", "font-weight": "600" });
      rowLabel.textContent = r.label;
      svg.appendChild(rowLabel);

      svg.appendChild(svgEl("line", {
        x1: xAt(lo), x2: xAt(hi), y1: cy, y2: cy,
        stroke: "var(--border-strong)", "stroke-width": 2, "stroke-linecap": "round"
      }));

      // which slot this row favours — bolded, not coloured differently
      var best = 0;
      vals.forEach(function (v, si) {
        if (r.lowerBetter ? v < vals[best] : v > vals[best]) best = si;
      });

      PLAYERS.forEach(function (p, pi) {
        var v = vals[pi];
        var c = svgEl("circle", { cx: xAt(v), cy: cy, r: 6, fill: slotColour(pi), stroke: "var(--bg-raised)", "stroke-width": 2 });
        var ti = svgEl("title", {}); ti.textContent = p + " · " + r.fmt(v); c.appendChild(ti);
        svg.appendChild(c);

        // slot 1's figure sits above the row, slot 2's below, so they never collide
        var label = svgEl("text", {
          x: xAt(v), y: cy + (pi === 0 ? -14 : 20), "font-size": 10,
          "text-anchor": "middle", fill: slotColour(pi),
          "font-weight": best === pi ? "800" : "500"
        });
        label.setAttribute("font-family", "var(--font-mono)");
        label.textContent = r.fmt(v);
        svg.appendChild(label);
      });
    });

    mount.appendChild(svg);
  }

  // ---------- boot ----------
  document.addEventListener("DOMContentLoaded", function () {
    parseClaimsData();
    renderTimeline();
    renderVsSmallMultiples();
    renderClearsBar();
    renderTapeChart();
    renderAllBadges(document); // catch remaining static badges (hero, stats, coaching, moments)
  });
})();
</script>"""


# ---------------------------------------------------------------------- LAYOUT

def _matches_fallback(facts):
    """Used only while `build_report` does not own the `matches` region."""
    n = len(facts["matches"])
    return f"""<section id="matches">
  <div class="wrap">
    <div class="eyebrow">{TODO} · 戰況直擊</div>
    <h2 class="section-title">{TODO} — {n} 場戰況</h2>
    <p class="section-lede">{TODO}：呢一段導言未寫。</p>

    <div class="timeline" id="timeline"></div>

    <blockquote class="closer">{TODO}：呢句收結未寫。</blockquote>
  </div>
</section>"""


def _stats_fallback(facts):
    """Used only while `build_report` does not own the `stats` region."""
    return f"""<section id="stats">
  <div class="wrap-wide">
    <div class="eyebrow">{TODO} · 數據對決</div>
    <h2 class="section-title">數據對決</h2>
    <p class="section-lede">{TODO}：呢一段未寫。</p>

    <div class="legend-row">
""" + "\n".join(
        f'      <span class="sw"><span class="dot {cls}"></span>{p}</span>'
        for cls, p in zip(("y", "p"), facts["players"])) + f"""
    </div>

    <div class="chart-panel">
      <h3>{TODO} — 逐場 VS 走勢</h3>
      <p class="cap">{TODO}：呢句圖說未寫。</p>
      <div class="sm-grid" id="vs-small-multiples"></div>
    </div>

    <div class="chart-panel">
      <h3>{TODO} — 清行類型分布</h3>
      <p class="cap">{TODO}：呢句圖說未寫。</p>
      <div class="scroll-x"><div id="clears-bar-chart"></div></div>
    </div>

    <div class="chart-panel">
      <h3>{TODO} — 身手大比拼</h3>
      <p class="cap">{TODO}：呢句圖說未寫。</p>
      <div class="scroll-x"><div id="tape-chart"></div></div>
    </div>
  </div>
</section>"""


def _coaching_fallback(facts):
    """Used only while `build_report` does not own the `coaching` region."""
    cols = []
    for p in facts["players"]:
        cols.append(f"""      <div class="rec-col for-{_css_ident(p)}">
        <h3>{p} ——「{TODO}」</h3>
        <p class="profile">{TODO}：呢一段側寫未寫。</p>
        <ol class="rec-list">
          <li><span class="rec-num">1</span>{TODO}：呢條建議未寫。</li>
        </ol>
      </div>""")
    return f"""<section id="coaching">
  <div class="wrap-wide">
    <div class="eyebrow">{TODO} · 教練分析</div>
    <h2 class="section-title">俾兩位嘅建議</h2>
    <p class="section-lede">{TODO}：呢一段未寫。</p>

    <div class="rec-grid">
""" + "\n\n".join(cols) + f"""

      <div class="versus-note">{TODO}：呢一段總結未寫。</div>
    </div>
  </div>
</section>"""


# Document order. Each entry is one of:
#   ("html",   callable(facts) -> str)          literal shell this module owns
#   ("region", name, fallback|None)             a build_report region; `fallback`
#                                               is emitted instead of the marker
#                                               pair while build_report does not
#                                               own that name yet
#   ("markers", start, end)                     a pre-existing pair owned elsewhere
LAYOUT = [
    ("comment", "HERO"),
    ("region", "hero", None),
    ("comment", "戰況"),
    ("region", "matches", _matches_fallback),
    ("comment", "數據對決"),
    ("region", "stats", _stats_fallback),
    ("comment", "關鍵時刻"),
    ("region", "moments", None),
    ("comment", "全場之最"),
    ("region", "records", None),
    ("comment", "建議"),
    ("region", "coaching", _coaching_fallback),
    ("comment", "逐局全數據"),
    ("markers", build_round_table.START, build_round_table.END),
    ("comment", "證明附錄"),
    ("region", "appendix", None),
    ("html", lambda facts: _footer(facts)),
    ("comment", "DATA ISLANDS"),
    ("region", "chart-data", None),
    ("region", "claims-data", None),
    ("region", "match-copy", None),
    ("html", lambda _facts: SCRIPT),
]

# Regions `build_report` inserts against an anchor this skeleton already emits, so
# they need no empty pair here. Each entry says why, because "it is missing" and
# "it is deliberately absent" look identical in the output.
SELF_INSERTING = {
    "perfect-clear": "conditional — `generators.perfect_clears` emits nothing for a session "
                     "with no All Clear, so `pc_section.build` returns None and an empty pair "
                     "here would trip build_report's stale-region guard; it inserts the block "
                     "before the coaching region's BEGIN marker",
    "forecast": "conditional — only a session with sim/forecast-facts.json gets one; "
                "build_report inserts it before the footer anchor",
    "openers": "conditional — only a session with sim/opener-facts.json gets one; "
               "build_report inserts it before the footer anchor, after forecast",
}


def _check_coverage():
    """Every region `build_report` owns must be placed here, or named as self-inserting.

    Without this, adding a section to `build_report.SECTIONS` and forgetting it
    here produces a report whose new section is simply absent — no error, no empty
    region, nothing to notice. A skeleton that can silently omit a section is worse
    than no skeleton, because the omission is invisible in the rendered page.
    """
    placed = {e[1] for e in LAYOUT if e[0] == "region"}
    owned = {name for name, _a, _b, _m in build_report.SECTIONS}
    missing = sorted(owned - placed - set(SELF_INSERTING))
    if missing:
        raise SystemExit(
            f"pipeline/skeleton.py: build_report.SECTIONS owns {missing} but LAYOUT "
            "does not place it. Add it to LAYOUT in document order (or to "
            "SELF_INSERTING with the reason) — otherwise a new session's report "
            "silently has no such section.")
    return placed, owned


def _markers(name):
    """The marker pair `build_report` uses for `name`, or None if it owns no such region."""
    for n, _anchor, _build, markers in build_report.SECTIONS:
        if n == name:
            return markers or region.markers(name, PRODUCER)
    return None


def _footer(facts):
    p1, p2 = facts["players"]
    date = facts["matches"][0]["ts"][:10]
    return (f'<footer class="report-footer">\n'
            f"  {p1} vs {p2} · {date} · report.html generated from facts.json + "
            f"claims ledgers · pipeline/build_report.py keeps this in sync\n"
            f"</footer>")


def build(facts):
    """The whole shell, as a string. Every generated region is present but empty."""
    _check_coverage()
    p1, p2 = facts["players"]
    n = len(facts["matches"])
    winner, pip, rec = _player_rules(facts["players"])
    css = (CSS.replace("@@WINNER_ACCENTS@@", winner)
              .replace("@@PIP_COLOURS@@", pip)
              .replace("@@REC_COLS@@", rec))

    out = ['<meta charset="utf-8" />\n'
           f"<title>{p1} vs {p2} — {n} 場戰報</title>\n"
           '<meta name="viewport" content="width=device-width, initial-scale=1" />',
           css]
    for entry in LAYOUT:
        kind = entry[0]
        if kind == "comment":
            out.append(f"<!-- ============================= {entry[1]} "
                       "============================= -->")
            continue
        if kind == "html":
            out.append(entry[1](facts))
            continue
        if kind == "markers":
            out.append(f"{entry[1]}\n{entry[2]}")
            continue
        name, fallback = entry[1], entry[2]
        pair = _markers(name)
        if pair is None:
            if fallback is None:
                raise SystemExit(
                    f"pipeline/skeleton.py: LAYOUT places region {name!r}, but "
                    "build_report owns no such section and no fallback markup was "
                    "given — the report would have a hole there")
            out.append(fallback(facts))
            continue
        out.append(f"{pair[0]}\n{pair[1]}")
    return "\n\n".join(out) + "\n"


# ------------------------------------------------------------------ PROSE STUBS

def _series_claim(report_dir):
    """The claim id the hero's score badge cites, read out of the generated ledger.

    Not a constant: `C001` is a hand claim that a fresh session does not have yet,
    and a badge citing a claim that does not exist renders `⏳ C001` — which reads
    as "still being proved" rather than as "wrong id" and is exactly what
    `check_badge_links` exists to refuse. `series_result` is the family that states
    the final score, and it is the first generated claim in all four sessions.
    """
    path = os.path.join(report_dir, "claims-generated.json")
    if not os.path.exists(path):
        raise SystemExit(f"missing {path} — run `python3 -m pipeline.claims."
                         "build_claims` before the skeleton, so the hero's score "
                         "badge can cite a claim that exists")
    with open(path, encoding="utf-8") as fh:
        for c in json.load(fh):
            if c.get("family") == "series_result":
                return c["id"]
    raise SystemExit(f"{path} has no `series_result` claim — the hero's score badge "
                     "has nothing to cite; write prose/hero.json's score_claim by hand")


def _stub_hero(facts, report_dir):
    p1, p2 = facts["players"]
    return {
        "kicker": "",
        "title": f'{TODO} — 大標題未寫（<span class="hl-y">{p1}</span> '
                 f'vs <span class="hl-p">{p2}</span>）',
        "tags": {p1: f"{TODO} · TAGLINE", p2: f"{TODO} · TAGLINE"},
        "lede": f"{TODO}：呢一段導言未寫。要講今晚嘅主線，每句數得出嚟嘅嘢帶返 claim id。",
        "score_claim": _series_claim(report_dir),
    }


def _stub_matches(facts, _report_dir):
    idx = [m["index"] for m in facts["matches"]]
    return {
        "eyebrow": f"{TODO} · 戰況直擊",
        "title": f"{TODO} — {len(idx)} 場戰況",
        "lede": f"{TODO}：呢一段導言未寫。",
        "closer": f"{TODO}：呢句收結未寫。",
        "hero_match": idx[-1],
        "score_claim": None,
        "cards": {str(i): {"title": f"{TODO} — 第 {i} 場標題未寫",
                           "flag": None,
                           "body": f"{TODO}：第 {i} 場嘅文字未寫。"}
                  for i in idx},
    }


def _stub_moments(facts, _report_dir):
    return {
        "eyebrow": f"{TODO} · 關鍵時刻",
        "title": f"{TODO} — 呢一節嘅標題未寫",
        "cards": [{"accent": accent,
                   "label": f"{TODO} LABEL",
                   "value": "—",
                   "body": f"{TODO}：呢張卡嘅文字未寫。"}
                  for accent in ("y", "p", "g")],
        "trivia": [f"{TODO}：呢條冷知識未寫。"],
    }


def _stub_stats(facts, _report_dir):
    panels = [("vs-small-multiples", "sm-grid", False, "逐場 VS 走勢"),
              ("clears-bar-chart", None, True, "清行類型分布"),
              ("tape-chart", None, True, "身手大比拼")]
    return {
        "eyebrow": f"{TODO} · 數據對決",
        "title": "數據對決",
        "lede": f"{TODO}：呢一段未寫。",
        "panels": [{"heading": f"{TODO} — {heading}",
                    "caps": [f"{TODO}：呢句圖說未寫。"],
                    "footnote": None,
                    "mount": {"id": mid, "class": cls, "scroll_x": scroll}}
                   for mid, cls, scroll, heading in panels],
    }


def _stub_coaching(facts, _report_dir):
    return {
        "eyebrow": f"{TODO} · 教練分析",
        "title": "俾兩位嘅建議",
        "lede": f"{TODO}：呢一段未寫。",
        "columns": {p: {"tagline": f"{TODO} 風格未寫",
                        "profile": [f"{TODO}：{p} 嘅側寫未寫。"],
                        "recs": [f"{TODO}：{p} 嘅第一條建議未寫。"]}
                    for p in facts["players"]},
        "versus_note": f"{TODO}：呢一段總結未寫。",
    }


# filename -> (builder, consumers). A consumer is a callable the *owning module*
# runs against this file when `build_report` renders — `load_prose`, and where the
# module validates more on the way out (`matches.section` requires the section's
# heading and lede, which `matches.load_prose` does not), that too.
#
# Every consumer is run against the stub the moment it is written. A stub its own
# reader refuses is worse than no stub: `build_report` would die on a file this
# module had just produced, one step later and with no clue where it came from. The
# shapes live in five modules that are still moving, so asserting beats remembering
# — and it did: `matches.json` grew four section fields between this file being
# written and being run, and this is what said so.
def _prose_stubs():
    from pipeline import hero, matches, moments
    stubs = [
        ("hero.json", _stub_hero, [
            lambda d, f: hero.build(f, hero.load_prose(d), d)]),
        ("matches.json", _stub_matches, [
            lambda d, f: matches.build(f, matches.load_prose(d, f)),
            lambda d, f: matches.section(f, matches.load_prose(d, f))]),
        ("moments.json", _stub_moments, [
            lambda d, f: moments.build(f, moments.load_prose(d))]),
    ]
    # Owned by modules that may not exist yet; a stub is written only when the
    # module that reads it does, so this file is useful mid-migration.
    try:
        from pipeline import stats_section
        stubs.append(("stats.json", _stub_stats, [
            lambda d, f: stats_section.build(f, stats_section.load_prose(d))]))
    except ImportError:
        pass
    try:
        from pipeline import coaching
        stubs.append(("coaching.json", _stub_coaching, [
            lambda d, f: coaching.build(f, coaching.load_prose(d, f))]))
    except ImportError:
        pass
    return stubs


def write_prose(report_dir, facts):
    """Write every missing prose stub. Returns (written, kept)."""
    prose_dir = os.path.join(report_dir, "prose")
    os.makedirs(prose_dir, exist_ok=True)
    written, kept = [], []
    for name, builder, consumers in _prose_stubs():
        path = os.path.join(prose_dir, name)
        if os.path.exists(path):
            kept.append(path)
            continue
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(builder(facts, report_dir), fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        for consume in consumers:   # the stub must satisfy every reader it has
            consume(report_dir, facts)
        written.append(path)
    return written, kept


# ------------------------------------------------------------------------- CLI

def hand_written():
    """What a person still has to write, in the order they will meet it."""
    return [
        "the <title> in report.html — derived as `<p1> vs <p2> — N 場戰報`; edit it "
        "if the session has a kicker (「第四回合」). The only prose left in the HTML.",
        "prose/hero.json — kicker, headline, both taglines, lede",
        "prose/matches.json — the 戰況 heading, lede and closer, one card per match, "
        "plus hero_match and score_claim",
        "prose/moments.json — 關鍵時刻's cards and trivia",
        "prose/stats.json — 數據對決's lede, panel headings and captions",
        "prose/coaching.json — both columns' taglines, profiles and recommendations",
        "narrative-beats.md / recommendations.md — the drafting surface for the above",
        "hand_claims.py — whatever is genuinely unique to this session",
    ]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir", help="a session's report/ directory")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing report.html (prose is never overwritten)")
    args = ap.parse_args(argv)

    facts_path = os.path.join(args.report_dir, "facts.json")
    if not os.path.exists(facts_path):
        raise SystemExit(f"missing {facts_path} — extract the replays first")
    with open(facts_path, encoding="utf-8") as fh:
        facts = json.load(fh)

    report_path = os.path.join(args.report_dir, "report.html")
    if os.path.exists(report_path) and not args.force:
        print(f"ok  {report_path} exists — left untouched "
              "(the skeleton is for a session that has none)")
        return 0

    # Rendered before the file is opened. `open(..., "w")` truncates on entry, so
    # building inside the `with` left an EMPTY report.html behind whenever build()
    # raised — and the next run would then see a report.html and skip the step.
    shell = build(facts)
    written, kept = write_prose(args.report_dir, facts)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(shell)

    placed, owned = _check_coverage()
    print(f"wrote {report_path}")
    print(f"      regions: {', '.join(sorted(placed & owned))}")
    if placed - owned:
        print(f"      !!  {', '.join(sorted(placed - owned))} emitted as hand-written "
              "TODO markup — no generator owns them yet, so "
              "`python3 -m pipeline.check_report_shell` will fail until one does")
    for p in written:
        print(f"wrote {p}")
    for p in kept:
        print(f"kept  {p} (already written)")
    print("\nnext:")
    print(f"  python3 -m pipeline.build_report {args.report_dir}")
    print(f"  python3 -m pipeline.build_round_table {args.report_dir}")
    print("\nstill hand-written:")
    for item in hand_written():
        print(f"  · {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
