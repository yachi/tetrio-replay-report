"""建議 — the two coaching columns and the closing 對比 note.

The last big block of hand-written Cantonese still living inside `report.html`.
Like 關鍵時刻 it is almost pure prose, so the win is not that a number stops being
retyped — it is that the words get a name and the structure stops being retyped:

  * `check_prose_figures` reports a bad 約-figure as `prose/coaching.json
    columns.yachi.recs[1]` instead of as an anonymous "report.html hand-written
    prose". Four sessions × two columns × three-to-four recommendations is a lot of
    haystack for a figure that floors the wrong way.
  * the `<span class="rec-num">N</span>` counters were hand-typed in all eight
    columns. They are now positional, so inserting a recommendation cannot leave
    the rest misnumbered — the same fix `moments.py` made for the trivia numbers.
  * the column classes (`for-yachi`, `for-pinglamb`) and the `{player} ——「…」`
    heading were per-report literals. They come from `facts["players"]` now, which
    is where the rest of the pipeline is heading; the *tagline* inside the 「」 is
    the only authored part of the heading, exactly like `hero.py`'s `tags`.

**Raw vs escaped.** Ledes, profile paragraphs, recommendations and the versus note
are inserted as **raw HTML**: they legitimately carry `<span class="badge"
data-claim="…">`, `<strong>` and `<code>`, and they are authored, not input — the
rule `hero.py` and `matches.py` state. The **derived** values — each player's name,
in the heading and in the column's class — are `html.escape`d, so a name out of
`facts.json` can never become markup. The tagline follows `hero.py`'s `tags` and is
raw, because it sits in the same authored sentence as the profile.

**Why the profile's wrapper is derived rather than authored.** A column with one
paragraph renders `<p class="profile">`; two or more render `<div class="profile">`
wrapping a `<p>` each. That is what the four committed reports do, and it is not
cosmetic: 07-22 (the one single-paragraph session) has no `.rec-col .profile p`
rule in its stylesheet, so the div form would drop that paragraph's spacing there.
Keeping the rule here means the JSON only ever says *how many paragraphs*, never
which tag — but note the coupling: giving 07-22 a second paragraph flips the
wrapper and that session's stylesheet would need the `p` rule added with it.

**Tagged items (`sim_recs`).** A column may carry a second list, `sim_recs`: recommendations written
from 定式路線同中盤手法 (`routes_techniques_section.py`), which is simulator output and outside the trust
chain. They render after the proved `recs`, numbered on from them, each with an inline 「未經證明」 tag
linking to that section and no ✓. The loader refuses a badge or `data-claim` inside one, and
`check_routes_techniques` checks every Arabic figure in one is a figure that section prints. When any
column has one, the section carries `SIM_NOTE` and a `<style>` scoped `#coaching .cs-*`.

Apart from that, the section emits no `<style>` of its own — `.rec-grid` / `.rec-col` / `.rec-list`
live in the report's own stylesheet. That is deliberate: 全場之最 once defined
`.rec-grid` for its tile grid and collapsed these two columns into auto-fit ones,
because a generated section's `<style>` is injected into the body and wins at equal
specificity. Nothing to prefix here as long as nothing is added.
"""
import html
import json
import os

from pipeline.claims.build_claims import SIMPLIFIED

TOP_FIELDS = ("eyebrow", "title", "lede", "versus_note")
SHAPE = ('  {"eyebrow": "...", "title": "...", "lede": "...", '
         '"columns": {"<player>": {"tagline": "...", "profile": ["..."], '
         '"recs": ["..."], "sim_recs": ["... (optional)"]}}, "versus_note": "..."}')

# The tag every sim_recs item carries, and the sentence the section carries when any column has one.
SIM_TAG = '<a class="cs-unproven" href="#routes-techniques">未經證明</a>'
SIM_NOTE = ('標住「未經證明」嘅建議，係用上面「定式路線同中盤手法」嗰節嘅模擬器數字寫嘅：'
            '<strong>冇 ✓、唔屬於信任鏈</strong>，啲數喺嗰節逐個搵得返。')
SIM_STYLE = """    <style>
      /* scoped, cs- prefixed: this <style> lands in the body (see the module docstring) */
      #coaching .cs-unproven { display: inline-block; font-size: .72rem; padding: .02rem .4rem;
        margin-right: .4rem; border: 1px dashed currentColor; border-radius: .3rem;
        text-decoration: none; opacity: .8; }
      #coaching .cs-note { font-size: .85rem; opacity: .8; }
    </style>"""


def load_prose(report_dir, facts):
    """Read prose/coaching.json, refusing anything that would silently degrade the page.

    Silently is the operative word: an empty rec list renders an empty `<ol>`, a
    column keyed by a name that is not in this session renders nothing at all, and
    both look like a styling bug rather than a missing file.
    """
    path = os.path.join(report_dir, "prose", "coaching.json")
    if not os.path.exists(path):
        raise SystemExit(
            f"missing {path} — 建議's words are hand-written; write it as\n" + SHAPE)
    with open(path, encoding="utf-8") as fh:
        prose = json.load(fh)

    empty = [f for f in TOP_FIELDS if not (prose.get(f) or "").strip()]
    if empty:
        raise SystemExit(f"{path}: missing or empty {', '.join(empty)}\n" + SHAPE)

    columns = prose.get("columns") or {}
    players = list(facts["players"])
    missing = [p for p in players if p not in columns]
    extra = [p for p in columns if p not in players]
    if missing or extra:
        raise SystemExit(
            f"{path}: columns must cover exactly {players}"
            + (f"; missing {missing}" if missing else "")
            + (f"; unknown {extra}" if extra else ""))

    for p in players:
        col = columns[p]
        if not (col.get("tagline") or "").strip():
            raise SystemExit(f"{path}: column {p} has no tagline — it is the 「」 "
                             "half of the heading and would render as empty quotes")
        for field in ("profile", "recs"):
            items = col.get(field) or []
            if not isinstance(items, list) or not items:
                raise SystemExit(f"{path}: column {p} has no {field} — a list of "
                                 "one or more authored strings is required")
            blank = [i for i, t in enumerate(items, 1) if not (str(t) or "").strip()]
            if blank:
                raise SystemExit(f"{path}: column {p} {field} {blank} empty")
        sim = col.get("sim_recs", [])
        if not isinstance(sim, list) or any(not (str(t) or "").strip() for t in sim):
            raise SystemExit(f"{path}: column {p} sim_recs must be a list of non-empty strings")
        badged = [i for i, t in enumerate(sim, 1) if "data-claim" in t or "badge" in t]
        if badged:
            raise SystemExit(f"{path}: column {p} sim_recs {badged} carry a claim badge — these items "
                             "are simulator output and outside the trust chain")

    # The same guard the claim generator applies: reviews have repeatedly caught
    # 净/实/约 arriving from an editor with the wrong locale.
    text = " ".join([str(prose[f]) for f in TOP_FIELDS]
                    + [str(columns[p]["tagline"]) for p in players]
                    + [str(t) for p in players for f in ("profile", "recs")
                       for t in columns[p][f]]
                    + [str(t) for p in players for t in columns[p].get("sim_recs", [])])
    bad = sorted(set(text) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"{path}: simplified glyph(s) {bad} — this report is "
                         "traditional characters only")
    return prose


def _profile(paragraphs):
    """The profile block: a bare `<p class="profile">` for one paragraph, a
    `<div class="profile">` of `<p>`s for more. See the module docstring."""
    if len(paragraphs) == 1:
        return [f'        <p class="profile">{paragraphs[0]}</p>']
    return (['        <div class="profile">']
            + [f"          <p>{p}</p>" for p in paragraphs]
            + ["        </div>"])


def build(facts, prose):
    columns = prose["columns"]
    tagged = any(columns[p].get("sim_recs") for p in facts["players"])
    out = ['<section id="coaching">'] + ([SIM_STYLE] if tagged else []) + ['  <div class="wrap-wide">',
           f'    <div class="eyebrow">{html.escape(prose["eyebrow"])}</div>',
           f'    <h2 class="section-title">{html.escape(prose["title"])}</h2>',
           f'    <p class="section-lede">{prose["lede"]}</p>']
    if tagged:
        out.append(f'    <p class="cs-note">{SIM_NOTE}</p>')
    out += ['',
           '    <div class="rec-grid">']
    for player in facts["players"]:
        col = columns[player]
        name = html.escape(player)
        out += [
            f'      <div class="rec-col for-{name}">',
            f'        <h3>{name} ——「{col["tagline"]}」</h3>',
        ]
        out += _profile(col["profile"])
        out += ['', '        <ol class="rec-list">']
        for i, rec in enumerate(col["recs"], 1):
            # positional, so inserting a recommendation cannot leave the rest
            # misnumbered — eight hand-typed counters is eight chances to slip
            out.append(f'          <li><span class="rec-num">{i}</span>{rec}</li>')
        for i, rec in enumerate(col.get("sim_recs", []), len(col["recs"]) + 1):
            out.append(f'          <li class="cs-sim"><span class="rec-num">{i}</span>{SIM_TAG}{rec}</li>')
        out += ['        </ol>', '      </div>', '']

    out += ['      <div class="versus-note">',
            f'        {prose["versus_note"]}',
            '      </div>',
            '    </div>', '  </div>', '</section>']
    return "\n".join(out)
