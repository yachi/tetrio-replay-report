"""全消 — the Perfect Clear section, built from proved claims.

A Perfect Clear is the one clear type that reads like a headline and is easy to publish
badly. It is rare (3-12 rounds a session), it is worth a large one-off attack, and a table
of "who got more" invites the reader to finish the sentence with "…so he was winning".
This section prints the finish instead: how many of those rounds each player actually won,
and how many rounds the ONLY player to clear his board went on to lose.

Every figure is read out of the claims' own specs — the operands of the equalities Dafny
proved (`pc_rounds`, `pc_solo_lost`, `clears_allclear`) — never re-derived from facts.json,
so the table cannot print a number the proof does not cover. A session whose claims are
missing gets no section rather than a re-derived one; `build_report.render` skips a builder
that returns None, which is also how a session with no Perfect Clear at all renders.

Sourcing, and why this section is NOT next to the two simulator sections: `clears.allclear`
is read out of the `.ttrm` by `extract.py` and `extract2.ts` independently and compared by
the cross-extractor gate, so it carries the same trust as every other number in the report
body. WHERE in the round a Perfect Clear landed is a different question with a different
source (one simulator) and it lives in the quarantined opener section, which says so.
"""
import html

from pipeline import claim_cards
from pipeline.claims.build_claims import SIMPLIFIED

FIELD = "clears.allclear"

CSS = """
<style>
/* ---------- 全消 (generated) ---------- */
/* Scoped under #perfect-clear, and every class carries the pc- prefix: a generated
   section's <style> is injected into the body, so at equal specificity it beats the
   report's own stylesheet and an unprefixed name silently restyles the host. */
#perfect-clear .pc-scroll { overflow-x: auto; margin: 1.4rem 0 0; }
#perfect-clear .pc-table { width: 100%; border-collapse: collapse; font-size: .86rem;
  min-width: 34rem; }
#perfect-clear .pc-table th, #perfect-clear .pc-table td { padding: .55rem .7rem;
  border-bottom: 1px solid var(--border); text-align: right; }
#perfect-clear .pc-table th:first-child, #perfect-clear .pc-table td:first-child {
  text-align: left; }
#perfect-clear .pc-table thead th { font-family: var(--font-mono); font-size: .64rem;
  letter-spacing: .07em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
/* Columns of figures align vertically, so these ARE tabular — the opposite of the
   standalone display numbers in 全場之最. */
#perfect-clear .pc-table td.pc-num { font-variant-numeric: tabular-nums; }
#perfect-clear .pc-who { display: flex; align-items: center; gap: .45rem; white-space: nowrap; }
#perfect-clear .pc-dot { width: .5rem; height: .5rem; border-radius: 50%; flex: none; }
/* Positional class, legacy token: the four earliest reports' :root predates the
   positional --p1/--p2 slots and only defines --yachi/--pinglamb, and an undefined
   custom property resolves to nothing rather than failing. Same rule build_round_table
   follows for its bar tints. */
#perfect-clear .pc-dot.is-p1 { background: var(--yachi); }
#perfect-clear .pc-dot.is-p2 { background: var(--pinglamb); }
#perfect-clear .pc-cid { font-family: var(--font-mono); font-size: .6rem; color: var(--muted); }
#perfect-clear .pc-find { margin: 1.2rem 0 0; font-size: .92rem; line-height: 1.9; }
#perfect-clear .pc-note { margin: .9rem 0 0; font-size: .8rem; line-height: 1.8;
  color: var(--muted); }
@media print {
  #perfect-clear .pc-scroll { overflow-x: visible; }
}
</style>
"""


def _pairs(spec):
    """[(expr, proved value)] for every `eq(expr, lit(v))` a claim's spec asserts."""
    spec = spec or {}
    xs = spec.get("xs", []) if spec.get("p") == "and" else [spec]
    return [(x["a"], x["b"]["v"]) for x in xs
            if x.get("p") == "eq" and (x.get("b") or {}).get("e") == "lit"]


def _rounds_row(claim):
    """{player, rounds, won, wins, total} from a `pc_rounds` claim, or None."""
    out = {}
    for e, v in _pairs(claim.get("spec")):
        kind = e.get("e")
        if kind == "count_rounds":
            cond = e.get("cond") or {}
            if cond.get("c") == "field_cmp" and cond.get("f") == FIELD:
                out["player"], out["rounds"] = cond["pl"], v
            elif cond.get("c") == "and" and any(x.get("c") == "winner" for x in cond["xs"]):
                out["won"] = v
        elif kind == "count_rounds_won":
            out["wins"] = v
        elif kind == "total_rounds":
            out["total"] = v
    need = {"player", "rounds", "won", "wins", "total"}
    return out if need <= set(out) else None


def _solo_row(claim):
    """{player, solo, lost} from a `pc_solo_lost` claim, or None."""
    out = {}
    for e, v in _pairs(claim.get("spec")):
        cond = e.get("cond") or {}
        if e.get("e") != "count_rounds" or cond.get("c") != "and":
            continue
        mine = [x for x in cond["xs"]
                if x.get("c") == "field_cmp" and x.get("f") == FIELD and x.get("op") == ">"]
        if not mine:
            continue
        out["player"] = mine[0]["pl"]
        out["lost" if any(x.get("c") == "winner" for x in cond["xs"]) else "solo"] = v
    need = {"player", "solo", "lost"}
    return out if need <= set(out) else None


def _totals(claim):
    """{player: All Clears} from the `clears_allclear` claim."""
    return {e["pl"]: v for e, v in _pairs(claim.get("spec"))
            if e.get("e") == "sum_round" and e.get("f") == FIELD}


def collect(report_dir):
    """(rows, total_solo, total_lost) — one row per player, in ledger order."""
    claims = claim_cards.load(report_dir)
    by_family = {}
    for c in claims:
        by_family.setdefault(c["family"], []).append(c)

    totals = {}
    for c in by_family.get("clears_allclear", []):
        totals.update(_totals(c))

    solo = {}
    for c in by_family.get("pc_solo_lost", []):
        r = _solo_row(c)
        if r:
            solo[r["player"]] = dict(r, id=c["id"], verified=c["verified"])

    rows = []
    unread = []
    for c in by_family.get("pc_rounds", []):
        r = _rounds_row(c)
        if not r:
            # The claim is there and its spec is not the shape this reader knows. Dropping it would
            # silently shrink the table — a player's row would just not appear — so it is collected
            # and raised on below. `records.py` has the same rule for a different reason: a claim it
            # cannot read is REPORTED, never quietly skipped.
            unread.append(c["id"])
            continue
        s = solo.get(r["player"])
        rows.append({**r, "total_pc": totals.get(r["player"]),
                     "solo": s["solo"] if s else None, "lost": s["lost"] if s else None,
                     "ids": [c["id"]] + ([s["id"]] if s else []),
                     "verified": c["verified"] and (s["verified"] if s else True)})
    if unread:
        raise SystemExit(
            f"{report_dir}: perfect-clear claims {', '.join(unread)} no longer have the spec shape "
            "pc_section reads, so their rows would be missing from a table that still looks "
            "complete. Update pc_section._rounds_row alongside generators.perfect_clears.")
    return (rows,
            sum(r["solo"] for r in rows if r["solo"] is not None),
            sum(r["lost"] for r in rows if r["lost"] is not None))


def build(facts, report_dir):
    rows, solo_total, lost_total = collect(report_dir)
    if not rows:
        return None
    p1 = facts["players"][0]
    n_rounds = rows[0]["total"]

    out = [CSS, '<section id="perfect-clear">', '  <div class="wrap">',
           '    <div class="eyebrow">全消 · PERFECT CLEAR</div>',
           '    <h2 class="section-title">全消清晒成塊板，然之後呢？</h2>',
           '    <p class="section-lede">Perfect Clear（全消）係成塊板清到一格都冇，'
           '一次過送一大抽出去。呢節唔係擺個「邊個做得多」出嚟就算數——'
           '每行都跟住寫埋<strong>嗰啲局最後贏咗幾多</strong>。'
           '所有數都係由 claim 本身證嗰條等式度攞返嚟（id 喺最後一欄），'
           '唔係喺呢度另外再數一次。</p>',
           '    <div class="pc-scroll">',
           '      <table class="pc-table">',
           '        <thead><tr><th>玩家</th><th>全消次數</th><th>有全消嘅局</th>'
           '<th>嗰啲局贏咗</th><th>成晚贏／打</th><th>淨係佢有全消但輸咗</th>'
           '<th>Claim</th></tr></thead>',
           '        <tbody>']
    for r in rows:
        dot = "is-p1" if r["player"] == p1 else "is-p2"
        tick = "✓" if r["verified"] else "⏳"
        cell = lambda v: "—" if v is None else f"{v:,}"  # noqa: E731
        out += [
            '          <tr>',
            f'            <td><span class="pc-who"><span class="pc-dot {dot}"></span>'
            f'{html.escape(r["player"])}</span></td>',
            f'            <td class="pc-num">{cell(r["total_pc"])}</td>',
            f'            <td class="pc-num">{r["rounds"]:,}</td>',
            f'            <td class="pc-num">{r["won"]:,}</td>',
            f'            <td class="pc-num">{r["wins"]:,} ／ {r["total"]:,}</td>',
            f'            <td class="pc-num">{cell(r["lost"])}</td>',
            f'            <td class="pc-cid">{html.escape(" · ".join(r["ids"]))} {tick}</td>',
            '          </tr>',
        ]
    out += ['        </tbody>', '      </table>', '    </div>']

    # The finding, stated as the count it is. Deliberately not a percentage: the
    # denominator is 3-12 rounds per player and a rate over that reads far more
    # confident than the data is.
    if solo_total:
        out.append(f'    <p class="pc-find">成晚 <strong>{solo_total}</strong> 局係'
                   f'<strong>全場淨係得一個人</strong>做到全消——入面有 '
                   f'<strong>{lost_total}</strong> 局，做到嗰個仲要輸咗。'
                   '清到成塊板係一次過大攻擊，但擺喺一局嘅結果度睇，'
                   '<strong>佢唔係一個決定局數嘅訊號</strong>。')
    # A player with no Perfect Clear has no claim about one, and this section prints only figures a
    # lemma covers — so their row is absent rather than a zero nothing proved. Said out loud only
    # when it actually happens, because a permanent sentence about a case that never occurs is
    # noise, and noise is how the sentences that matter stop being read.
    if len(rows) < len(facts["players"]):
        missing = [p for p in facts["players"] if p not in {r["player"] for r in rows}]
        out.append('    <p class="pc-note">'
                   + "、".join(html.escape(p) for p in missing)
                   + '<strong>成晚一個全消都冇</strong>，所以個表冇佢嗰行——'
                     '呢節每個數都要有一條 claim 證住，冇 claim 就唔會攞個 0 出嚟充數。</p>')
    out.append('    <p class="pc-note">'
               f'讀呢個表要記住三樣嘢。一，<strong>樣本細</strong>：成晚得 {n_rounds} 局，'
               '每個人有全消嘅局數得單位數到十幾局，所以呢度全部寫「幾多局」，'
               '<strong>唔寫百分比</strong>——三局嘅百分比睇落好肯定，其實乜都話唔到。'
               '二，<strong>「全消次數」同「有全消嘅局」唔同</strong>：一局入面可以出多過一次全消，'
               '所以左邊嗰欄大得過右邊嗰欄係正常，唔可以當成同一個數。'
               '三，呢節講嘅係<strong>有冇</strong>出全消，'
               '<strong>唔係幾時</strong>出——「打到第幾手先全消」嗰個問題靠模擬器答，'
               '同呢節唔同來源，喺下面模擬器嗰節（同埋佢自己講明係未經第二個實作核對嘅）。'
               '呢節嘅數全部出自 <code>facts.json</code> 嘅 <code>clears.allclear</code>，'
               '由兩個獨立 parser 各自由 <code>.ttrm</code> 讀一次。</p>')
    out += ['  </div>', '</section>']
    # This section's Cantonese is authored in this module, not in prose/*.json, so no loader's
    # glyph check reaches it — the same hole opener_section closes the same way. 净/实/约 have all
    # been caught in review in this repo before.
    markup = "\n".join(out)
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"pc_section: simplified glyph(s) {bad} — this report is "
                         "traditional-character Cantonese")
    return markup
