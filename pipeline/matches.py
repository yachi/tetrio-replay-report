"""The match-card copy island: one card per match, prose keyed by match index.

Same split as the hero — the card's numbers (score, winner, the per-round pip
trail) already come from the chart-data island; what a person writes is the
title, the optional 🏆 flag and the body paragraph. Those live in
`<report_dir>/prose/matches.json`:

    {
      "hero_match": 10,          // which card gets the spotlight treatment
      "score_claim": "C026",     // optional badge appended to every card's score
      "cards": {"1": {"title": ..., "flag": null, "body": ...}, ...}
    }

`hero_match` and `score_claim` used to be constants inside each report's inline
script (`m.index === 7`, a hard-coded `data-claim="C026"`), which is why the
script could not be shared between sessions. They are editorial choices, so they
belong with the prose rather than in code.

The card bodies use the report's badge shorthand (`<b>C001</b>`), expanded by
`expandShorthandBadges` in the page, so they are HTML written by a person and are
inserted as such. Every match must have a card: a session where match 6 silently
has no copy would render an empty card, and nothing else would notice.
"""
import html
import json
import os

from pipeline.claims.build_claims import SIMPLIFIED

CARD_FIELDS = ("title", "body")


def load_prose(report_dir, facts):
    path = os.path.join(report_dir, "prose", "matches.json")
    if not os.path.exists(path):
        raise SystemExit(
            f"missing {path} — the match cards' words are hand-written; write it as\n"
            '  {"hero_match": <index>, "score_claim": null, '
            '"cards": {"1": {"title": ..., "flag": null, "body": ...}, ...}}')
    with open(path, encoding="utf-8") as fh:
        prose = json.load(fh)

    cards = prose.get("cards") or {}
    expected = [str(m["index"]) for m in facts["matches"]]
    missing = [i for i in expected if i not in cards]
    extra = [i for i in cards if i not in expected]
    if missing or extra:
        raise SystemExit(
            f"{path}: cards must cover exactly matches {expected[0]}–{expected[-1]}"
            + (f"; missing {missing}" if missing else "")
            + (f"; unknown {extra}" if extra else ""))
    for idx in expected:
        empty = [f for f in CARD_FIELDS if not (cards[idx].get(f) or "").strip()]
        if empty:
            raise SystemExit(f"{path}: card {idx} has empty {', '.join(empty)}")

    hero = prose.get("hero_match")
    if hero is not None and str(hero) not in expected:
        raise SystemExit(f"{path}: hero_match {hero} is not one of matches "
                         f"{expected[0]}–{expected[-1]}")

    text = " ".join(str(c.get(f) or "") for c in cards.values()
                    for f in ("title", "flag", "body"))
    bad = sorted(set(text) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"{path}: simplified glyph(s) {bad} — this report is "
                         "traditional characters only")
    return prose


SECTION_FIELDS = ("eyebrow", "title", "lede")


def section(facts, prose):
    """The 戰況 section itself — the frame the timeline renders into.

    The cards come from the island below and are assembled in the browser; what
    lives here is the wrapper plus the two pieces of authored prose around it, the
    lede and the closing blockquote.

    This was the last hand-written `<section>` in the report body, which is worth
    stating plainly: "the body is fully generated" got written down while it was
    true of every OTHER section, because the claim was checked by reading the
    SECTIONS list rather than by scanning the document for sections outside a
    marker region. The scan is now `pipeline/check_report_shell.py`.

    `closer` is optional — it is an editorial flourish and not every session has
    one. The heading and lede are not, because a section missing its heading is a
    broken page rather than a plainer one.
    """
    missing = [f for f in SECTION_FIELDS if not (prose.get(f) or "").strip()]
    if missing:
        raise SystemExit(f"prose/matches.json: missing or empty {', '.join(missing)} "
                         f"— 戰況's heading and lede are required")
    out = ['<section id="matches">', '  <div class="wrap">',
           f'    <div class="eyebrow">{html.escape(prose["eyebrow"])}</div>',
           f'    <h2 class="section-title">{html.escape(prose["title"])}</h2>',
           f'    <p class="section-lede">{prose["lede"]}</p>',
           '',
           '    <div class="timeline" id="timeline"></div>']
    if (prose.get("closer") or "").strip():
        out += ['', f'    <blockquote class="closer">{prose["closer"]}</blockquote>']
    out += ['  </div>', '</section>']
    return "\n".join(out)


def build(facts, prose):
    """The island the page's timeline renderer reads."""
    payload = {"hero_match": prose.get("hero_match"),
               "score_claim": prose.get("score_claim"),
               "cards": {str(m["index"]): {
                   "title": prose["cards"][str(m["index"])]["title"],
                   "flag": prose["cards"][str(m["index"])].get("flag"),
                   "body": prose["cards"][str(m["index"])]["body"],
               } for m in facts["matches"]}}
    return ('<script type="application/json" id="match-copy">\n'
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n</script>")
