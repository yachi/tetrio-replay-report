"""每粒攻擊 — the APP section: attack per piece, six blocks, rendered from facts.json.

    region "app", section id "app", placed right after 數據對決 (stats) and before the
    routes-techniques / moments regions. Built by `build(facts, report_dir)`.

APP is `garbage_attack / pieces`. Every figure here is computed from facts.json (and, for the
two corpus blocks, from the other sessions' facts.json); NONE of it is a proved claim by
default. A block attaches a ✓ badge (`app_common.badge`) only where a generated claim's SPEC
proves exactly the number printed beside it — find it with `app_common.claims_of(ctx, family)`
(e.g. `app_decides_rounds`, `per_piece_garbage_attack`, `rate_split_garbage_attack`) and check
the spec, never the family name alone. The corpus blocks (5, 6) are never badged.

MODULE LAYOUT, and why it is cycle-free
---------------------------------------
    app_svg.py            SVG/markup helpers, printed-figure helpers (num/rate/pct -> fmt)
    app_common.py         block(), badge(), pname(), claims_of(), corpus(), session_date(),
                          P_CLASS, check_glyphs()
    app_blocks_session.py scoreboard(ctx), per_match(ctx), won_lost(ctx)   blocks 1, 4a, 4b
    app_blocks_rounds.py  speed_scatter(ctx), round_strip(ctx)             blocks 2, 3
    app_blocks_corpus.py  break_even(ctx), trend(ctx)                      blocks 5, 6
    app_section.py        build_ctx(), CSS, build()   — imports the three block modules

Block modules import `app_common` and `app_svg` only. They must NEVER import `app_section`.

BLOCK FUNCTIONS
---------------
Each takes `ctx` and returns one string of HTML — the output of
`app_common.block(title, eyebrow, body_html, note_html=None, block_id=None)` — or None
(break_even / trend only: when there is no corpus, i.e. ctx["date"] is None, or too little data).
A block must not emit <section>, <style> or <script>; all CSS lives in this module's CSS block.

    block(title, eyebrow, body_html, note_html=None, block_id=None) -> str
        title, eyebrow: plain text, escaped by block().
        body_html, note_html: trusted markup the block built.
        block_id: short slug -> id="app-<slug>" (use: score, scatter, strip, match, wonlost,
        breakeven, trend).

THE ctx CONTRACT (a plain dict, built once by build_ctx; read-only to blocks)
----------------------------------------------------------------------------
    ctx["facts"]       the session's facts.json, as loaded.
    ctx["report_dir"]  the report directory as passed in.
    ctx["players"]     [name0, name1] — facts["players"] order. EVERY per-player list below is
                       indexed 0/1 in this order. Colour is positional: player i uses
                       app_common.P_CLASS[i] ("ap-p1"/"ap-p2"); never branch on a name.
    ctx["date"]        "YYYY-MM-DD" or None, from app_common.session_date(report_dir):
                       sessions/<date>/report -> <date>; subsets/<date>-<suffix>/report -> <date>;
                       anything else -> None (the corpus blocks then return None).
    ctx["rounds"]      one dict per round, in play order (match position, then round):
        "mi"        0-based index into facts["matches"]
        "ri"        0-based index into that match's rounds
        "match"     match POSITION, 1-based (facts match "index"; this is what m{N} means)
        "round"     round number within the match, 1-based
        "seq"       1-based round number across the whole session
        "winner"    0 or 1 — index into ctx["players"]
        "p"         [stats0, stats1], each {"attack": garbage_attack, "pieces": pieces,
                    "lifetime": lifetime (ms), "apm_x1000", "pps_x1000", "lines"} — ints.
                    PPS for the scatter is pieces * 1000 / lifetime (lifetime is ms).
    ctx["matches"]     one dict per match, in position order:
        "mi", "match" (position, 1-based), "file",
        "winner"    0 or 1
        "score"     [round wins of player 0, of player 1]  (from the match's "score")
        "attack"    [sum garbage_attack per player over the match's rounds]
        "pieces"    [sum pieces per player]
        "rounds"    list of indices into ctx["rounds"] for this match, in order
    ctx["totals"]      [t0, t1], per player over the whole session:
        "attack", "pieces", "lifetime", "rounds" (all rounds played), "wins" (rounds won),
        "won_attack", "won_pieces", "won_rounds"   — over rounds this player WON
        "lost_attack", "lost_pieces", "lost_rounds" — over rounds this player LOST
        "match_wins"
    ctx["claims"]      the generated ledger (claim_cards.load) restricted to the ids the report's
                       claims island carries, with the island's verdict; [] when none.

PRINTED FIGURES
---------------
Every decimal a reader sees (text, tick labels, <title> tooltips) goes through
app_svg.num / rate / pct (-> pipeline.fmt) with an explicit rule and a `site="app_<module>.<what>"`.
Default rule floor (約 = floored); ceil only for an upper bound. Coordinates use app_svg.coord.

CSS VOCABULARY (defined below, scoped under #app; add nothing elsewhere)
------------------------------------------------------------------------
    custom props  --ap-c1/--ap-c2 (player colours), --ap-t1/--ap-t2 (tints)
    legend keys   i.ap-key.ap-k1 / .ap-k2 (dot swatch), svg.ap-keysvg (inline svg swatch)
    text colour   .ap-p1 / .ap-p2           (bold, player colour; pname() uses them)
    svg fill      .ap-f1 / .ap-f2           svg stroke  .ap-s1 / .ap-s2
    hollow mark   .ap-hollow (fill bg, stroke stays from .ap-s1/.ap-s2)
    svg chrome    .ap-svg, .ap-grid, .ap-ax, .ap-tick, .ap-axlabel, .ap-ref (dashed reference line)
    layout        .ap-chart (horizontal scroll wrapper; its svg has a min-width),
                  .ap-chart.ap-narrow (no min-width), .ap-legend, .ap-legend i.ap-key (swatch),
                  .ap-figs (row of big figures), .ap-fig, .ap-big, .ap-sub, .ap-table, .ap-num,
                  .ap-muted
"""
import html
import json
import os
import sys

from pipeline import app_blocks_corpus, app_blocks_rounds, app_blocks_session, appendix, claim_cards
from pipeline.app_common import check_glyphs, session_date
from pipeline.app_svg import rate

EYEBROW = "每粒攻擊 · ATTACK PER PIECE"
TITLE = "每粒攻擊"
LEDE = ("每粒攻擊（APP）＝攻擊行數 ÷ 落咗嘅方塊數。快唔快睇 PPS，重唔重睇 APP，"
        "兩樣乘埋先係 APM。下面每個數都係由 facts.json 直接計出嚟；"
        "淨係有 ✓ 嗰啲先係證明咗嘅 claim，其餘係量度，唔係證明。")
CORPUS_DIVIDER = ("下面兩格量嘅係成個 corpus（截至呢晚為止嘅每個 session），唔係證明。"
                  "APP 高同贏局係有相關，唔係因果：輸家最後嗰幾粒係頂住壓力落嘅，"
                  "本身就會拉低佢嘅 APP。")

CSS = """<style>
/* ---------- 每粒攻擊 (generated) ---------- */
/* Every class carries the ap- prefix and every rule is scoped under #app: a generated
   section's <style> sits in the body and beats the report's stylesheet at equal specificity.
   Player colours fall back to --yachi/--pinglamb because the four earliest reports' :root
   predates the positional --p1/--p2 slots. */
#app { --ap-c1: var(--p1, var(--yachi)); --ap-c2: var(--p2, var(--pinglamb));
  --ap-t1: color-mix(in srgb, var(--ap-c1) 16%, transparent);
  --ap-t2: color-mix(in srgb, var(--ap-c2) 16%, transparent); }
#app .ap-blocks { display: grid; gap: 1.4rem; margin-top: 1.6rem; }
#app .ap-block { background: var(--bg-raised); border: 1px solid var(--border);
  border-radius: 10px; padding: 1.2rem 1.25rem; display: grid; gap: .8rem; min-width: 0; }
#app .ap-eyebrow { font-family: var(--font-mono); font-size: .66rem; letter-spacing: .12em;
  text-transform: uppercase; color: var(--muted); }
#app .ap-title { font-size: 1.08rem; margin: 0; }
#app .ap-body { display: grid; gap: .8rem; min-width: 0; }
#app .ap-note { margin: 0; font-size: .8rem; line-height: 1.8; color: var(--muted);
  border-top: 1px solid var(--border); padding-top: .6rem; }
#app .ap-divider { margin: .6rem 0 0; font-size: .88rem; line-height: 1.8;
  color: var(--ink-secondary); max-width: 68ch; }
#app .ap-p1 { color: var(--ap-c1); font-weight: 700; }
#app .ap-p2 { color: var(--ap-c2); font-weight: 700; }
#app .ap-muted { color: var(--muted); }
#app .ap-figs { display: flex; flex-wrap: wrap; gap: .8rem 2rem; align-items: flex-end; }
#app .ap-fig { display: grid; gap: .1rem; min-width: 0; }
#app .ap-big { font-family: var(--font-mono); font-size: clamp(1.8rem, 5vw, 2.6rem);
  font-weight: 600; line-height: 1.05; font-variant-numeric: tabular-nums; }
#app .ap-sub { font-size: .82rem; color: var(--ink-secondary); }
#app .ap-num { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
#app .ap-table { width: 100%; border-collapse: collapse; font-size: .84rem; }
#app .ap-table th, #app .ap-table td { padding: .4rem .55rem; text-align: right;
  border-bottom: 1px solid var(--border); }
#app .ap-table th:first-child, #app .ap-table td:first-child { text-align: left; }
#app .ap-table thead th { font-family: var(--font-mono); font-size: .62rem; letter-spacing: .07em;
  text-transform: uppercase; color: var(--muted); font-weight: 600; }
#app .ap-legend { display: flex; flex-wrap: wrap; gap: .35rem 1rem; font-size: .8rem;
  color: var(--ink-secondary); }
#app .ap-legend i.ap-key { display: inline-block; width: .65rem; height: .65rem;
  border-radius: 50%; margin-right: .35rem; vertical-align: -.05rem; }
#app .ap-legend i.ap-k1 { background: var(--ap-c1); }
#app .ap-legend i.ap-k2 { background: var(--ap-c2); }
#app .ap-legend svg.ap-keysvg { vertical-align: -1px; margin-right: .35rem; }
#app .ap-chart { width: 100%; overflow-x: auto; }
/* a wide chart (viewBox 720) never shrinks below its native width, so its 11px text stays 11px;
   on a narrow screen it scrolls inside its box, the page does not */
#app .ap-chart .ap-svg { min-width: 720px; }
#app .ap-chart.ap-narrow .ap-svg { min-width: 0; max-width: 560px; }
#app .ap-scrollhint { display: none; font-size: .74rem; color: var(--muted); text-align: center; }
@media (max-width: 820px) {
  #app .ap-scrollhint { display: block; }
  /* the narrow charts (viewBox 480) do shrink: scale their text up so it renders near 11px */
  #app .ap-chart.ap-narrow .ap-svg text { font-size: 17px; }
}
#app .ap-svg { display: block; width: 100%; height: auto; }
#app .ap-svg text { fill: var(--ink-secondary); font-family: var(--font-mono); font-size: 11px; }
#app .ap-svg .ap-axlabel { fill: var(--muted); font-size: 10px; }
#app .ap-svg .ap-grid { stroke: var(--border); stroke-dasharray: 2 3; }
#app .ap-svg .ap-ax { stroke: var(--border-strong); }
#app .ap-svg .ap-ref { stroke: var(--muted); stroke-dasharray: 4 3; fill: none; }
#app .ap-f1 { fill: var(--ap-c1); }
#app .ap-f2 { fill: var(--ap-c2); }
#app .ap-s1 { stroke: var(--ap-c1); }
#app .ap-s2 { stroke: var(--ap-c2); }
#app .ap-hollow { fill: var(--bg-raised); stroke-width: 1.5; }
#app .ap-svg text.ap-halo { paint-order: stroke; stroke: var(--bg-raised); stroke-width: 4px;
  stroke-linejoin: round; }
@media print {
  #app .ap-chart { overflow-x: visible; }
  #app .ap-chart .ap-svg { min-width: 0; }
  #app .ap-scrollhint { display: none; }
}
</style>"""


def build_ctx(facts, report_dir):
    """The ctx dict documented in this module's docstring."""
    players = list(facts["players"])
    if len(players) != 2:
        raise SystemExit(f"每粒攻擊 expects two players, facts has {players}")
    idx = {name: i for i, name in enumerate(players)}

    rounds, matches = [], []
    totals = [{k: 0 for k in ("attack", "pieces", "lifetime", "rounds", "wins",
                              "won_attack", "won_pieces", "won_rounds",
                              "lost_attack", "lost_pieces", "lost_rounds", "match_wins")}
              for _ in players]
    for mi, m in enumerate(facts["matches"]):
        mrow = {"mi": mi, "match": m["index"], "file": m.get("file"),
                "winner": idx[m["winner"]], "score": [m["score"][n] for n in players],
                "attack": [0, 0], "pieces": [0, 0], "rounds": []}
        totals[mrow["winner"]]["match_wins"] += 1
        for ri, r in enumerate(m["rounds"]):
            w = idx[r["winner"]]
            stats = []
            for i, name in enumerate(players):
                s = r["players"][name]
                st = {"attack": s["garbage_attack"], "pieces": s["pieces"],
                      "lifetime": s["lifetime"], "apm_x1000": s["apm_x1000"],
                      "pps_x1000": s["pps_x1000"], "lines": s["lines"]}
                stats.append(st)
                t = totals[i]
                t["attack"] += st["attack"]
                t["pieces"] += st["pieces"]
                t["lifetime"] += st["lifetime"]
                t["rounds"] += 1
                side = "won" if i == w else "lost"
                t[f"{side}_attack"] += st["attack"]
                t[f"{side}_pieces"] += st["pieces"]
                t[f"{side}_rounds"] += 1
                mrow["attack"][i] += st["attack"]
                mrow["pieces"][i] += st["pieces"]
            totals[w]["wins"] += 1
            mrow["rounds"].append(len(rounds))
            rounds.append({"mi": mi, "ri": ri, "match": m["index"], "round": ri + 1,
                           "seq": len(rounds) + 1, "winner": w, "p": stats})
        matches.append(mrow)

    return {"facts": facts, "report_dir": report_dir, "players": players,
            "date": session_date(report_dir), "rounds": rounds, "matches": matches,
            "totals": totals, "claims": _island_claims(report_dir)}


def _island_claims(report_dir):
    """The generated claims a badge here may cite: only those the report's claims island carries
    (appendix._rows — every id the committed claims-proof-map.json covers), with the island's own
    verdict. A claim the island lacks renders an unresolvable badge (check_badge_links), which is
    what 07-22's generated ledger would have produced: its island holds the hand claims only."""
    rows = {r["id"]: r for r in appendix._rows(report_dir)}
    return [dict(c, verified=rows[c["id"]]["status"] == "verified")
            for c in claim_cards.load(report_dir) if c["id"] in rows]


def build(facts, report_dir):
    """The whole region body: <section id="app"> with its CSS and the six blocks."""
    return render(build_ctx(facts, report_dir))


def render(ctx):
    """The region body for an already-built ctx (the selftest renders a renamed ctx)."""
    session_blocks = [app_blocks_session.scoreboard(ctx),
                      app_blocks_rounds.speed_scatter(ctx),
                      app_blocks_rounds.round_strip(ctx),
                      app_blocks_session.per_match(ctx),
                      app_blocks_session.won_lost(ctx)]
    corpus_blocks = [b for b in (app_blocks_corpus.break_even(ctx),
                                 app_blocks_corpus.trend(ctx)) if b]

    out = ['<section id="app">', CSS, '  <div class="wrap-wide">',
           f'    <div class="eyebrow">{html.escape(EYEBROW)}</div>',
           f'    <h2 class="section-title">{html.escape(TITLE)}</h2>',
           f'    <p class="section-lede">{html.escape(LEDE)}</p>',
           '    <div class="ap-blocks">']
    out += [b for b in session_blocks if b]
    if corpus_blocks:
        out.append(f'<p class="ap-divider">{html.escape(CORPUS_DIVIDER)}</p>')
        out += corpus_blocks
    out += ['    </div>', '  </div>', '</section>']
    body = "\n".join(out)
    check_glyphs(body, "每粒攻擊 (pipeline/app_section.py)")
    return body


# ------------------------------------------------------------------ selftest
#
#   python3 -m pipeline.app_section --selftest [sessions/<date>/report]
#
# Four properties, each with a planted mutant that must be caught. A check whose mutant survives
# is reported as a failure, because a gate that cannot fail is a comment.
#   1. determinism   two builds are byte-identical (mutant: a block that reads a clock-like counter)
#   2. name-agnostic every player name renamed throughout facts, claims and corpus renders the same
#                    section up to the rename, and no real name survives the rename (mutants: a
#                    block that branches on a player's NAME, and one that prints a typed name)
#   3. CSS scope     check_generated_css passes on the built report (mutant: an unscoped rule
#                    naming a class the host report uses)
#   4. rounding      check_rounding._uncovered finds no undeclared rounding in the app modules
#                    (mutant: a bare `:.3f` printed figure planted in a copy of a block module)
#   5. subset 今晚   the subset report's trend marks the subset's own APP as 今晚 (mutant: read the
#                    subset as the corpus session, which must trip trend()'s assertion)

_SELFTEST_DEFAULT = "sessions/2026-10-29/report"
_SELFTEST_SUBSET = "subsets/2026-09-18-onform/report"


def _renamer(names):
    alias = {n: f"PLAYER{chr(65 + i)}Q" for i, n in enumerate(names)}

    def walk(o):
        if isinstance(o, dict):
            return {alias.get(k, k): walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        if isinstance(o, tuple):
            return tuple(walk(v) for v in o)
        if isinstance(o, str):
            return alias.get(o, o)
        return o
    return alias, walk


def _renamed_render(ctx):
    """Render ctx with both player names replaced everywhere, then map the names back.

    A real name surviving in the renamed render is a name typed into the code (the shared CSS
    block is left out of that search: its `--yachi` / `--pinglamb` fallbacks are custom-property
    names, not printed names); that returns None, which never equals a render."""
    alias, walk = _renamer(ctx["players"])
    ctx2 = {k: (v if k == "report_dir" else walk(v)) for k, v in ctx.items()}
    real = app_blocks_corpus.corpus      # the name the corpus blocks call
    app_blocks_corpus.corpus = lambda c: [walk(x) for x in real(ctx)]
    try:
        out = render(ctx2)
    finally:
        app_blocks_corpus.corpus = real
    visible = out.replace(CSS, "")                  # CSS names tokens (--yachi), never a player
    if any(name in visible for name in alias):
        return None
    for name, a in alias.items():
        out = out.replace(a, html.escape(name, quote=True))
    return out


def _report_with(report_dir, body):
    """The session's report.html with the app region's body replaced by `body`."""
    from pipeline import region
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    start, end = region.markers("app", "pipeline/build_report.py")
    if start not in doc:
        raise SystemExit(f"{report_dir}: no app region (expected {start!r}); build the report")
    return region.replace(doc, start, end, body)[0]


def selftest(report_dir=_SELFTEST_DEFAULT):
    import shutil
    import tempfile

    from pipeline import app_blocks_session as abs_, check_generated_css, check_rounding
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    ctx = build_ctx(facts, report_dir)
    base = render(ctx)
    failures = []

    def expect(name, clean_ok, mutant_caught):
        print(f"  {'ok' if clean_ok else 'FAIL'}  {name}: clean")
        print(f"  {'ok' if mutant_caught else 'FAIL'}  {name}: mutant caught")
        if not (clean_ok and mutant_caught):
            failures.append(name)

    # 1. determinism
    counter = iter(range(10 ** 6))
    real_sb = abs_.scoreboard
    abs_.scoreboard = lambda c: real_sb(c) + f"<!-- {next(counter)} -->"
    try:
        m1, m2 = render(ctx), render(ctx)
    finally:
        abs_.scoreboard = real_sb
    expect("determinism", render(build_ctx(facts, report_dir)) == base, m1 != m2)

    # 2. name-agnostic
    clean = _renamed_render(ctx) == base
    real_pm = abs_.per_match
    first = ctx["players"][0]
    abs_.per_match = lambda c: real_pm(c) + ("<!-- x -->" if c["players"][0] == first else "")
    try:
        caught = _renamed_render(ctx) != render(ctx)
    finally:
        abs_.per_match = real_pm
    abs_.per_match = lambda c: real_pm(c) + f"<!-- {first} -->"       # a typed name
    try:
        caught = caught and _renamed_render(ctx) is None
    finally:
        abs_.per_match = real_pm
    expect("name-agnostic", clean, caught)

    # 3. CSS scope
    tmp = tempfile.mkdtemp(prefix="app-selftest-")
    try:
        def css_ok(body):
            path = os.path.join(tmp, "report.html")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(_report_with(report_dir, body))
            return all(not unpinned for name, _n, unpinned in check_generated_css.scan(path)
                       if name == "app")
        mutant = base.replace("</style>", ".section-title { color: red; }\n</style>", 1)
        expect("CSS scope", css_ok(base), not css_ok(mutant))

        # 4. rounding: copy every COVERED module into a scratch root, plant a bare :.3f in one
        root = os.path.join(tmp, "root")
        for rel in check_rounding.COVERED:
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            shutil.copy(os.path.join(check_rounding.REPO, rel), os.path.join(root, rel))
        clean_ok = not check_rounding._uncovered(root)
        target = os.path.join(root, "pipeline/app_blocks_session.py")
        with open(target, encoding="utf-8") as fh:
            src = fh.read()
        planted = src.replace('def _note(text_html):\n',
                              'def _note(text_html):\n    _ = f"{1 / 3:.3f}"\n', 1)
        assert planted != src, "rounding mutant did not plant"
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(planted)
        expect("rounding", clean_ok, any(r[0] == "pipeline/app_blocks_session.py"
                                          for r in check_rounding._uncovered(root)))
    finally:
        shutil.rmtree(tmp)

    # 5. subset: a subset report's 「今晚」 trend row is the subset's own totals, not the full
    #    night's (mutant: treat the subset as the corpus session, which keeps the full night's row
    #    and must trip trend()'s own assertion)
    sub = _SELFTEST_SUBSET
    if os.path.isdir(sub):
        from pipeline import app_blocks_corpus as abc_
        with open(os.path.join(sub, "facts.json"), encoding="utf-8") as fh:
            sctx = build_ctx(json.load(fh), sub)
        t = sctx["totals"]
        want = [rate(t[i]["attack"], t[i]["pieces"], 3, site="app_section.selftest")
                for i in (0, 1)]
        out = abc_.trend(sctx) or ""
        clean_ok = all(f"嘅 {w}" in out for w in want) and "subset" in out
        real_ics = abc_.is_corpus_session
        abc_.is_corpus_session = lambda c: True
        try:
            abc_.trend(sctx)
            caught = False
        except AssertionError:
            caught = True
        finally:
            abc_.is_corpus_session = real_ics
        expect("subset 今晚", clean_ok, caught)
    else:
        print(f"  --  subset 今晚: {sub} not present, not checked")

    print(("FAIL " + ", ".join(failures)) if failures else "app_section selftest: all ok")
    return 1 if failures else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] != "--selftest":
        raise SystemExit("usage: python3 -m pipeline.app_section --selftest [report_dir]")
    raise SystemExit(selftest(*args[1:2]))
