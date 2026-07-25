"""Build the per-round data table and inject it into a report.

    python3 -m pipeline.build_round_table sessions/2026-07-24/report

One table per match, two rows per round (one per player), every stat in its own
column with a header. The winner's row is tinted and marked, numerals are
tabular-aligned, the 局 / 時間 / 玩家 columns stay pinned while the stat columns scroll,
and the whole table scrolls inside its own container so the page never scrolls sideways.

Columns beyond the in-game end screen's APM / PPS / VS: pieces, APP (attack per piece),
KPP (keys per piece), DS (downstack per piece), lines, spike, B2B, combo, T-spins,
quads, TSD, TST, perfect clears, finesse rate and faults, attack, garbage sent, queued
vs materialised garbage, garbage cleared, score, and how the round ended.

Everything is derived from facts.json, so the table cannot disagree with the data the
claims are proved against. The section sits between comment markers and is replaced in
place on re-runs, so this is idempotent.
"""
import argparse
import json
import os
import re

START = "<!-- BEGIN generated round-table (pipeline/build_round_table.py) -->"
END = "<!-- END generated round-table -->"

CSS = """
<style>
/* ---------- per-round data table (generated) ---------- */
.rt-match { margin: 0 0 2.2rem; }
.rt-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: .5rem .9rem;
  margin-bottom: .5rem; }
.rt-head .rt-no { font-family: var(--font-mono); font-size: .74rem; letter-spacing: .12em;
  text-transform: uppercase; color: var(--muted); }
.rt-head .rt-score { font-weight: 800; font-size: 1.02rem; font-variant-numeric: tabular-nums; }
.rt-head .rt-who { font-family: var(--font-mono); font-size: .74rem; color: var(--muted); }
.rt-head .rt-agg { font-family: var(--font-mono); font-size: .7rem; color: var(--muted);
  margin-left: auto; font-variant-numeric: tabular-nums; }
.rt-y { color: var(--yachi); } .rt-p { color: var(--pinglamb); }

.rt-scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px;
  background: var(--bg-raised); -webkit-overflow-scrolling: touch; }
table.rt-tbl { border-collapse: separate; border-spacing: 0; width: max-content;
  min-width: 100%; font-variant-numeric: tabular-nums; font-size: .74rem; }
table.rt-tbl th, table.rt-tbl td { padding: .42rem .6rem; text-align: right;
  white-space: nowrap; border-bottom: 1px solid var(--border); }
table.rt-tbl thead th { position: sticky; top: 0; z-index: 3; cursor: pointer;
  user-select: none;
  background: var(--bg-sunken); font-family: var(--font-mono); font-size: .66rem;
  font-weight: 700; letter-spacing: .04em; color: var(--ink-secondary);
  text-transform: uppercase; border-bottom: 1px solid var(--border-strong); }
table.rt-tbl tbody tr:last-child td { border-bottom: none; }
/* Pinned identity columns.
   These MUST be fully opaque: the player tints are translucent, and a translucent
   sticky cell lets the scrolling columns show through underneath it, so the pinned
   name ends up with stat values printed on top of it. Painting the tint as a
   background-image over an opaque background-color composites to something solid. */
.rt-tbl .c-rd, .rt-tbl .c-time, .rt-tbl .c-who { position: sticky; z-index: 2;
  background-color: var(--bg-raised); text-align: left; }
.rt-tbl .c-rd { left: 0; width: 2.4rem; font-family: var(--font-mono); color: var(--muted); }
.rt-tbl .c-time { left: 2.4rem; width: 3.2rem; font-family: var(--font-mono); font-weight: 700; }
.rt-tbl .c-who { left: 5.6rem; width: 5.6rem; font-weight: 700;
  border-right: 1px solid var(--border); }
.rt-tbl thead .c-rd, .rt-tbl thead .c-time, .rt-tbl thead .c-who {
  z-index: 4; background-color: var(--bg-sunken); background-image: none; }
/* a hairline so the pinned block reads as a separate group while scrolling */
.rt-tbl .c-who { box-shadow: 1px 0 0 var(--border); }
/* a round is two rows; separate rounds with a stronger rule */
.rt-tbl tr.rt-round-end td { border-bottom: 1px solid var(--border-strong); }
.rt-tbl tr.rt-w-y td { background: var(--yachi-tint); }
.rt-tbl tr.rt-w-y .c-rd, .rt-tbl tr.rt-w-y .c-time, .rt-tbl tr.rt-w-y .c-who {
  background-color: var(--bg-raised);
  background-image: linear-gradient(var(--yachi-tint-strong), var(--yachi-tint-strong)); }
.rt-tbl tr.rt-w-p td { background: var(--pinglamb-tint); }
.rt-tbl tr.rt-w-p .c-rd, .rt-tbl tr.rt-w-p .c-time, .rt-tbl tr.rt-w-p .c-who {
  background-color: var(--bg-raised);
  background-image: linear-gradient(var(--pinglamb-tint-strong), var(--pinglamb-tint-strong)); }
.rt-tbl tr.rt-loser td { color: var(--ink-secondary); }
/* Hover layer. A 28-column lookup table is unreadable without one: the eye loses
   the row between the pinned name and the column it is reading. */
.rt-tbl tbody tr:hover td { background-image:
  linear-gradient(var(--bg-sunken), var(--bg-sunken)); }
.rt-tbl tbody tr:hover .c-rd, .rt-tbl tbody tr:hover .c-time,
.rt-tbl tbody tr:hover .c-who { background-image:
  linear-gradient(var(--bg-sunken), var(--bg-sunken)); }
/* Identity is a coloured dot plus ink-coloured text, not coloured text: a name
   painted in the series colour is colour-as-information and reads worse. */
.rt-dot { display: inline-block; width: .5rem; height: .5rem; border-radius: 50%;
  margin-right: .35rem; vertical-align: baseline; }
.rt-dot.is-y { background: var(--yachi); }
.rt-dot.is-p { background: var(--pinglamb); }
.rt-tbl .c-who { color: var(--ink); }
/* sort affordance */
.rt-tbl thead th .rt-arrow { opacity: .25; margin-left: .25rem; font-size: .85em; }
.rt-tbl thead th[aria-sort="ascending"] .rt-arrow,
.rt-tbl thead th[aria-sort="descending"] .rt-arrow { opacity: 1; color: var(--accent); }
.rt-tbl thead th:hover { color: var(--ink); }
.rt-oddgroup td { border-bottom-color: var(--border); }
.rt-tbl td.rt-key { font-weight: 700; color: var(--ink); }
.rt-tbl td.c-end { text-align: left; font-family: var(--font-mono); font-size: .68rem;
  color: var(--muted); }
.rt-tbl .rt-win-mark { color: var(--good); font-weight: 700; }
.rt-tbl td.rt-zero { color: var(--muted); opacity: .55; }
.rt-legend { font-size: .8rem; color: var(--muted); margin: 0 0 1.3rem; line-height: 1.75; }
.rt-legend code { font-family: var(--font-mono); font-size: .95em; color: var(--ink-secondary); }
.rt-hint { font-family: var(--font-mono); font-size: .66rem; color: var(--muted);
  margin: .3rem 0 0; }
/* per-piece efficiency findings */
.rt-find { display: grid; gap: .6rem; margin: 0 0 2rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); }
.rt-card { border: 1px solid var(--border); border-left-width: 3px; border-radius: 8px;
  padding: .7rem .85rem; background: var(--bg-raised); }
.rt-card.is-lever { border-left-color: var(--good); }
.rt-card.is-flat { border-left-color: var(--muted); }
.rt-card.is-compare { border-left-color: var(--accent); }
.rt-card.is-compare .rt-verdict { color: var(--accent); }
.rt-card .rt-metric { font-family: var(--font-mono); font-size: .68rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--muted); display: flex; gap: .4rem; align-items: center; }
.rt-card .rt-verdict { font-family: var(--font-mono); font-size: .62rem; padding: .05rem .35rem;
  border-radius: 999px; border: 1px solid currentColor; }
.rt-card.is-lever .rt-verdict { color: var(--good); }
.rt-card.is-flat .rt-verdict { color: var(--muted); }
.rt-card p { margin: .35rem 0 0; font-size: .82rem; line-height: 1.65; }
.rt-card .rt-cid { font-family: var(--font-mono); font-size: .6rem; color: var(--muted); }
</style>
"""

SORT_JS = """
<script>
/* Click a column header to sort that match's rounds by it; click again to reverse;
   a third click restores the original round order. Self-contained, no libraries. */
(function () {
  document.querySelectorAll("table.rt-tbl").forEach(function (table) {
    var body = table.tBodies[0];
    var heads = Array.prototype.slice.call(table.querySelectorAll("thead th"));
    heads.forEach(function (th, idx) {
      th.addEventListener("click", function () {
        var state = th.getAttribute("aria-sort");
        var next = state === "descending" ? "ascending"
                 : state === "ascending" ? "none" : "descending";
        heads.forEach(function (h) { h.removeAttribute("aria-sort"); });
        var rows = Array.prototype.slice.call(body.rows);
        if (next === "none") {
          rows.sort(function (a, b) {
            return (+a.dataset.order) - (+b.dataset.order);
          });
        } else {
          th.setAttribute("aria-sort", next);
          var dir = next === "ascending" ? 1 : -1;
          rows.sort(function (a, b) {
            var x = a.cells[idx].dataset.v, y = b.cells[idx].dataset.v;
            var nx = parseFloat(x), ny = parseFloat(y);
            var cmp = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : String(x).localeCompare(String(y));
            /* stable: fall back to the original order so equal values keep round order */
            return cmp !== 0 ? cmp * dir : (+a.dataset.order) - (+b.dataset.order);
          });
        }
        rows.forEach(function (r) { body.appendChild(r); });
      });
    });
  });
})();
</script>
"""

# (header label, title/explanation) — order defines the columns after the pinned three
COLUMNS = [
    ("APM", "attack per minute"),
    ("PPS", "pieces per second"),
    ("VS", "versus score"),
    ("方塊", "pieces placed"),
    ("APP", "attack per piece"),
    ("KPP", "keypresses per piece"),
    ("DS", "garbage cleared per piece (downstack)"),
    ("清行", "lines cleared"),
    ("SPIKE", "biggest single spike"),
    ("B2B", "longest back-to-back chain"),
    ("COMBO", "longest combo"),
    ("T", "T-spins including ones that cleared nothing"),
    ("QUAD", "quads"),
    ("TSD", "T-spin doubles"),
    ("TST", "T-spin triples"),
    ("PC", "perfect clears"),
    ("FIN%", "perfect-placement rate"),
    ("錯", "finesse faults"),
    ("攻", "attack dealt"),
    ("送", "garbage sent"),
    ("射埋", "attack queued at this player, before cancelling"),
    ("食", "garbage that actually materialised"),
    ("清", "garbage cleared away"),
    ("分", "in-game score"),
    ("結果", "how the round ended for this player"),
]


def fmt_clock(ms):
    total = ms // 1000
    return f"{total // 60}:{total % 60:02d}"


def r1(x):
    return f"{x // 100 / 10:.1f}"


def r2(x):
    return f"{x // 10 / 100:.2f}"


def ratio(num, den, dp=2):
    if not den:
        return "–"
    scale = 10 ** dp
    return f"{(num * scale) // den / scale:.{dp}f}"


def pct(num, den):
    return "–" if not den else f"{(num * 100) // den}%"


END_LABEL = {"winner": "生還", "garbagesmash": "俾垃圾頂爆",
             "topout": "自己頂爆", "forfeit": "投降"}


def cells(p, won):
    """The stat cells for one player in one round, in COLUMNS order."""
    c = p["clears"]
    queued = sum(g["amt"] for g in p["garbage_events"])
    reason = p.get("gameoverreason", "")
    return [
        (r1(p["apm_x1000"]), True),
        (r2(p["pps_x1000"]), True),
        (r1(p["vs_x1000"]), True),
        (str(p["pieces"]), False),
        (ratio(p["garbage_attack"], p["pieces"]), True),
        (ratio(p["inputs"], p["pieces"]), False),
        (ratio(p["garbage_cleared"], p["pieces"]), False),
        (str(p["lines"]), False),
        (str(p["maxspike"]), True),
        (str(p["topbtb"]), False),
        (str(p["topcombo"]), False),
        (str(p["tspins"]), False),
        (str(c["quads"]), False),
        (str(c["tspin_doubles"]), False),
        (str(c["tspin_triples"]), False),
        (str(c["allclear"]), False),
        (pct(p["finesse_perfect"], p["pieces"]), False),
        (str(p["finesse_faults"]), False),
        (str(p["garbage_attack"]), False),
        (str(p["garbagesent"]), False),
        (str(queued), False),
        (str(p["garbagereceived"]), False),
        (str(p["garbage_cleared"]), False),
        (f"{p['score']:,}", False),
        (END_LABEL.get(reason, reason or "–"), False),
    ]


def findings(report_dir):
    """The APP / KPP / DS verdicts from the generated ledger, with proof status.

    These are read from claims-generated.json rather than re-derived here, so the card
    text and the proved lemma are the same statement.
    """
    import glob
    led = os.path.join(report_dir, "claims-generated.json")
    if not os.path.exists(led):
        return []
    with open(led, encoding="utf-8") as fh:
        claims = json.load(fh)
    status = {}
    for pm in glob.glob(os.path.join(report_dir, "claims-generated-proof-map.json")):
        with open(pm, encoding="utf-8") as fh:
            for row in json.load(fh):
                status[row["id"]] = row["status"]
    keep = ("rate_split_", "rate_flat_", "app_decides_rounds", "ds_session",
            "keys_per_piece", "per_piece_")
    out = []
    for c in claims:
        fam = c.get("family", "")
        if not fam.startswith(keep):
            continue
        metric = ("APP" if "garbage_attack" in fam or fam == "app_decides_rounds"
                  else "KPP" if "inputs" in fam or fam == "keys_per_piece"
                  else "DS" if "garbage_cleared" in fam or fam == "ds_session"
                  else "FINESSE")
        # Three kinds, because they answer different questions:
        #   lever      the player's own rate differs between rounds won and lost
        #   flat       it barely differs, so it is not what decides their rounds
        #   compare    one player against the other — says nothing about winning,
        #              and must not be dressed up as if it did
        if fam.startswith("rate_flat_"):
            kind = "flat"
        elif fam.startswith("rate_split_") or fam == "app_decides_rounds":
            kind = "lever"
        else:
            kind = "compare"
        out.append({"id": c["id"], "metric": metric, "kind": kind,
                    "canto": c["canto"],
                    "verified": status.get(c["id"]) == "verified"})
    order = {"APP": 0, "DS": 1, "KPP": 2, "FINESSE": 3}
    rank = {"lever": 0, "flat": 1, "compare": 2}
    out.sort(key=lambda d: (rank[d["kind"]], order.get(d["metric"], 9), d["id"]))
    return out


def build(facts, report_dir=None):
    p1, p2 = facts["players"]
    out = [START, CSS,
           '<section id="rounds">', '  <div class="wrap-wide">',
           '    <div class="eyebrow">逐局數據 · ROUND BY ROUND</div>',
           '    <h2 class="section-title">逐局全數據</h2>',
           '    <p class="rt-legend">',
           '      每局兩行，一行一個玩家，贏嗰行有底色同 ✓。除咗遊戲畫面嘅 APM / PPS / VS，',
           '      仲有：<code>APP</code> 每粒方塊嘅攻擊、<code>KPP</code> 每粒方塊按幾多下、',
           '      <code>DS</code> 每粒方塊清走幾多垃圾、<code>FIN%</code> 完美擺放率同失誤次數、',
           '      <code>射埋</code>（對手射過嚟、未 cancel 嘅攻擊）對 <code>食</code>（真正變成垃圾行）、',
           '      同埋 <code>結果</code>（點收嘅）。',
           '    </p>',
           ]
    cards = findings(report_dir) if report_dir else []
    if cards:
        out += [
            '    <h3 style="font-size:1.05rem;margin:.2rem 0 .3rem">'
            '每粒方塊嘅效率：邊個數真係決定輸贏</h3>',
            '    <p class="rt-legend" style="margin-bottom:.9rem">',
            '      呢幾個判斷係由 pipeline 自動生成、再逐條用 Dafny 證過嘅（claim id 喺下面）。',
            '      <b>決定輸贏</b>／<b>唔係關鍵</b> 係拿同一個玩家「贏嘅局」對「輸嘅局」比出嚟嘅；',
            '      <b>兩人對比</b> 淨係比兩個人嘅高低，講唔到邊個數影響勝負。',
            '    </p>',
            '    <div class="rt-find">',
        ]
        VERDICT = {"lever": ("is-lever", "決定輸贏"),
                   "flat": ("is-flat", "唔係關鍵"),
                   "compare": ("is-compare", "兩人對比")}
        for c in cards:
            cls, verdict = VERDICT[c["kind"]]
            tick = "✓ Dafny 已證" if c["verified"] else "⏳ 待證"
            out.append(f'      <div class="rt-card {cls}">')
            out.append(f'        <div class="rt-metric">{c["metric"]}'
                       f'<span class="rt-verdict">{verdict}</span></div>')
            out.append(f'        <p>{c["canto"]}</p>')
            out.append(f'        <div class="rt-cid">{c["id"]} · {tick}</div>')
            out.append('      </div>')
        out.append('    </div>')
    for mi, m in enumerate(facts["matches"]):
        lb, win = m["leaderboard"], m["winner"]
        out.append('    <div class="rt-match">')
        out.append('      <div class="rt-head">')
        out.append(f'        <span class="rt-no">M{mi + 1}</span>')
        out.append(f'        <span class="rt-score"><span class="rt-y">{p1}</span> '
                   f'{m["score"][p1]}:{m["score"][p2]} '
                   f'<span class="rt-p">{p2}</span></span>')
        out.append(f'        <span class="rt-who">{win} 贏</span>')
        out.append('        <span class="rt-agg">'
                   f'{p1} {r1(lb[p1]["apm_x1000"])}/{r2(lb[p1]["pps_x1000"])}/'
                   f'{r1(lb[p1]["vs_x1000"])} &nbsp;·&nbsp; '
                   f'{p2} {r1(lb[p2]["apm_x1000"])}/{r2(lb[p2]["pps_x1000"])}/'
                   f'{r1(lb[p2]["vs_x1000"])} &nbsp;(APM/PPS/VS)</span>')
        out.append('      </div>')
        out.append('      <div class="rt-scroll">')
        out.append('        <table class="rt-tbl">')
        out.append('          <thead><tr>')
        ARROW = '<span class="rt-arrow">↕</span>'
        out.append(f'            <th class="c-rd" title="round number">局{ARROW}</th>'
                   f'<th class="c-time" title="round length">時間{ARROW}</th>'
                   f'<th class="c-who" title="player">玩家{ARROW}</th>')
        for label, title in COLUMNS:
            cls = ' class="c-end"' if label == "結果" else ""
            out.append(f'            <th{cls} title="{title}">{label}{ARROW}</th>')
        out.append('          </tr></thead>')
        out.append('          <tbody>')
        for ri, r in enumerate(m["rounds"]):
            dur = max(d["lifetime"] for d in r["players"].values())
            for n, pl in enumerate((p1, p2)):
                p = r["players"][pl]
                won = r["winner"] == pl
                classes = []
                if won:
                    classes.append("rt-w-y" if pl == p1 else "rt-w-p")
                else:
                    classes.append("rt-loser")
                if n == 1:
                    classes.append("rt-round-end")
                out.append(f'            <tr class="{" ".join(classes)}" data-order="{ri * 2 + n}">')
                # Every row repeats 局 and 時間 instead of using rowspan: rowspan would
                # pin the pairs together and make the table unsortable.
                out.append(f'              <td class="c-rd" data-v="{ri}">R{ri + 1}</td>')
                out.append(f'              <td class="c-time" data-v="{dur}">{fmt_clock(dur)}</td>')
                dot = "is-y" if pl == p1 else "is-p"
                mark = ' <span class="rt-win-mark">✓</span>' if won else ""
                out.append(f'              <td class="c-who" data-v="{pl}">'
                           f'<span class="rt-dot {dot}"></span>{pl}{mark}</td>')
                for (val, key), (label, _t) in zip(cells(p, won), COLUMNS):
                    cls = []
                    if label == "結果":
                        cls.append("c-end")
                    elif key:
                        cls.append("rt-key")
                    if val in ("0", "–"):
                        cls.append("rt-zero")
                    attr = f' class="{" ".join(cls)}"' if cls else ""
                    # data-v carries the raw value so sorting is numeric, not textual
                    # ("10" must not sort before "9", "1,234" must beat "999")
                    raw = val.replace(",", "").replace("%", "")
                    try:
                        key_v = str(float(raw))
                    except ValueError:
                        key_v = val
                    out.append(f'              <td{attr} data-v="{key_v}">{val}</td>')
                out.append('            </tr>')
        out.append('          </tbody>')
        out.append('        </table>')
        out.append('      </div>')
        out.append('      <p class="rt-hint">← 左右拉睇齊全部欄 · 點欄名可以排序 →</p>')
        out.append('    </div>')
    out += ['  </div>', SORT_JS, '</section>', END]
    return "\n".join(out) + "\n"


def inject(report_path, section):
    with open(report_path, encoding="utf-8") as fh:
        html = fh.read()
    if START in html and END in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: section.rstrip("\n"),
                      html, flags=re.S)
        how = "replaced"
    else:
        anchor = '<section id="appendix">'
        if anchor not in html:
            raise SystemExit(f"cannot find {anchor} in {report_path}")
        html = html.replace(anchor, section + "\n" + anchor, 1)
        how = "inserted before the appendix"
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return how


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report_dir", help="a session's report/ directory")
    args = ap.parse_args(argv)

    with open(os.path.join(args.report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    report_path = os.path.join(args.report_dir, "report.html")
    section = build(facts, args.report_dir)
    how = inject(report_path, section)
    nrounds = sum(len(m["rounds"]) for m in facts["matches"])
    print(f"{how}: {nrounds} rounds x {len(COLUMNS) + 3} columns over "
          f"{len(facts['matches'])} matches -> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
