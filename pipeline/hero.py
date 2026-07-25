"""The hero and scoreboard: derived numbers, hand-written words.

The split this module draws is the one the whole P5 phase rests on:

  * **derived** — the date, both player names, the series score, in that order.
    These come from facts.json and are HTML-escaped on the way in, so a value
    can never become markup.
  * **prose** — the headline, each player's tagline, the lede paragraph, and the
    optional kicker in the eyebrow. These are Cantonese written by a person and
    live in `<report_dir>/prose/hero.json`. They are inserted as raw HTML
    because they legitimately contain `<span class="hl-y">`, `<strong>` and
    badge spans; they are authored, not input.

The score renders in `facts["players"]` order — never champion-first. Putting
the winner first once reversed the meaning of a score on the site index.
"""
import html
import json
import os

from pipeline.claims.build_claims import SIMPLIFIED

META_PREFIX = "TETR.IO · 1v1 SERIES REPORT · "
PROSE_FIELDS = ("title", "lede", "tags")


def load_prose(report_dir):
    """Read prose/hero.json, refusing anything that would silently degrade the page."""
    path = os.path.join(report_dir, "prose", "hero.json")
    if not os.path.exists(path):
        raise SystemExit(
            f"missing {path} — the hero's words are hand-written; write it as\n"
            '  {"kicker": "", "title": "...", "tags": {"<player>": "..."}, '
            '"lede": "...", "score_claim": "C001"}')
    with open(path, encoding="utf-8") as fh:
        prose = json.load(fh)
    missing = [k for k in PROSE_FIELDS if not prose.get(k)]
    if missing:
        raise SystemExit(f"{path}: missing or empty {', '.join(missing)}")
    # The same guard the claim generator applies to its Cantonese: reviews have
    # repeatedly caught 净/实/约 arriving from an editor with the wrong locale.
    text = " ".join([prose["title"], prose["lede"], prose.get("kicker", "")]
                    + list(prose["tags"].values()))
    bad = sorted(set(text) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"{path}: simplified glyph(s) {bad} — this report is "
                         "traditional characters only")
    return prose


def session_date(facts, report_dir=None):
    """The session's date, cross-checked against the directory it lives in.

    `ts` is UTC and the session directories are named for the same date, so a
    disagreement means the replays were dropped into the wrong session — worth
    failing over rather than printing a date nobody can trace.
    """
    date = facts["matches"][0]["ts"][:10]
    if report_dir:
        parent = os.path.basename(os.path.dirname(os.path.abspath(report_dir)))
        if len(parent) == 10 and parent[4] == parent[7] == "-" and parent != date:
            raise SystemExit(f"session directory says {parent} but the first replay's "
                             f"ts says {date} — refusing to guess which is right")
    return date


def series_score(facts):
    """Matches won by each player, in `players` order."""
    p1, p2 = facts["players"]
    won = {p1: 0, p2: 0}
    for m in facts["matches"]:
        won[m["winner"]] += 1
    return won[p1], won[p2]


def _block(text, indent):
    """Prose laid out at a fixed indent, one source line per authored line."""
    pad = " " * indent
    return "\n".join(pad + line.strip() for line in text.strip().split("\n"))


def build(facts, prose, report_dir=None):
    p1, p2 = facts["players"]
    s1, s2 = series_score(facts)
    kicker = prose.get("kicker", "").strip()
    meta = META_PREFIX + (f"{kicker} · " if kicker else "") + session_date(facts, report_dir)
    tags = prose["tags"]
    claim = prose.get("score_claim", "C001")
    return f"""<section class="hero">
  <div class="wrap">
    <div class="hero-meta">{meta}</div>
    <h1 class="hero-title">
{_block(prose["title"], 6)}
    </h1>

    <div class="scoreboard">
      <div class="sb-player p-left">
        <div class="sb-name">{html.escape(p1)}</div>
        <div class="sb-tag">{tags[p1]}</div>
      </div>
      <div class="sb-mid">
        <div class="sb-score"><span class="y">{s1}</span><span class="sep">:</span>\
<span class="p">{s2}</span></div>
        <div class="sb-sub">場數 · MATCHES <span class="badge" \
data-claim="{html.escape(claim)}"></span></div>
      </div>
      <div class="sb-player p-right">
        <div class="sb-name">{html.escape(p2)}</div>
        <div class="sb-tag">{tags[p2]}</div>
      </div>
    </div>

    <p class="hero-lede">
{_block(prose["lede"], 6)}
    </p>
  </div>
</section>"""
