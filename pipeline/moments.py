"""關鍵時刻 — the highlight cards and the trivia list.

Same split as the hero and the match cards: the *words* are hand-written Cantonese
and live in `<report_dir>/prose/moments.json`, and everything derivable is derived.

Which is not much, and that is the point of moving it. This section is almost pure
authored prose, so the win is not that a number stops being retyped — it is that the
prose stops living inside `report.html`:

  * `check_prose_figures` reports a bad 約-figure as `prose/moments.json card2.body`
    instead of as an anonymous "report.html hand-written prose", which is the
    difference between a name and a search
  * the trivia numbers (01, 02, 03) were typed by hand in every report and are now
    positional, so inserting an item cannot renumber the rest wrong
  * `check_badge_links` already refuses a citation that resolves to nothing; with the
    copy in a JSON file the same claim ids are greppable per field

Card bodies and trivia lines are inserted as raw HTML because they legitimately
contain `<span class="badge">`, `<strong>` and `<code>`. They are authored, not
input — the same rule `matches.py` states. Labels and values ARE escaped: they are
short display strings with no reason to carry markup.

The accents are the report's own card variants (`accent-y`, `accent-p`, `accent-g`,
or none), named by player rather than colour everywhere else in this pipeline; here
they are a presentational choice the author makes per card, so the prose carries the
letter and this module validates it against the stylesheet's set.
"""
import html
import json
import os

from pipeline.claims.build_claims import SIMPLIFIED

ACCENTS = {"y", "p", "g", None, ""}
CARD_FIELDS = ("label", "value", "body")


def load_prose(report_dir):
    path = os.path.join(report_dir, "prose", "moments.json")
    if not os.path.exists(path):
        raise SystemExit(
            f"missing {path} — 關鍵時刻's words are hand-written; write it as\n"
            '  {"eyebrow": "...", "title": "...", '
            '"cards": [{"accent": "y", "label": ..., "value": ..., "body": ...}], '
            '"trivia": ["..."]}')
    with open(path, encoding="utf-8") as fh:
        prose = json.load(fh)

    cards = prose.get("cards") or []
    if not cards:
        raise SystemExit(f"{path}: no cards — the section would render empty")
    for i, c in enumerate(cards, 1):
        empty = [f for f in CARD_FIELDS if not (c.get(f) or "").strip()]
        if empty:
            raise SystemExit(f"{path}: card {i} has empty {', '.join(empty)}")
        if c.get("accent") not in ACCENTS:
            raise SystemExit(f"{path}: card {i} has accent {c['accent']!r}; the "
                             f"stylesheet defines {sorted(a for a in ACCENTS if a)}")
    if not (prose.get("eyebrow") or "").strip() or not (prose.get("title") or "").strip():
        raise SystemExit(f"{path}: eyebrow and title are both required")

    # The same guard the claim generator applies: reviews have repeatedly caught
    # 净/实/约 arriving from an editor with the wrong locale.
    text = " ".join([prose["eyebrow"], prose["title"]]
                    + [str(c.get(f) or "") for c in cards for f in CARD_FIELDS]
                    + [str(t) for t in (prose.get("trivia") or [])])
    bad = sorted(set(text) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"{path}: simplified glyph(s) {bad} — this report is "
                         "traditional characters only")
    return prose


def build(facts, prose):
    out = ['<section id="moments">', '  <div class="wrap">',
           f'    <div class="eyebrow">{html.escape(prose["eyebrow"])}</div>',
           f'    <h2 class="section-title">{html.escape(prose["title"])}</h2>',
           '',
           '    <div class="stat-grid">']
    for c in prose["cards"]:
        accent = f' accent-{c["accent"]}' if c.get("accent") else ""
        out += [
            f'      <div class="stat-card{accent}">',
            f'        <div class="k">{html.escape(c["label"])}</div>',
            f'        <div class="v mono">{html.escape(c["value"])}</div>',
            f'        <div class="d">{c["body"]}</div>',
            '      </div>',
        ]
    out.append('    </div>')

    trivia = prose.get("trivia") or []
    if trivia:
        out.append('')
        out.append('    <div class="trivia-list">')
        for i, t in enumerate(trivia, 1):
            out += [
                '      <div class="trivia-item">',
                # positional, so inserting an item cannot leave the rest misnumbered
                f'        <div class="num">{i:02d}</div>',
                f'        <div class="txt">{t}</div>',
                '      </div>',
            ]
        out.append('    </div>')
    out += ['  </div>', '</section>']
    return "\n".join(out)
