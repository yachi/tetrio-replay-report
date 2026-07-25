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
table.rt-tbl th, table.rt-tbl td { padding: .3rem .5rem; text-align: right;
  white-space: nowrap; border-bottom: 1px solid var(--border); }
table.rt-tbl thead th { position: sticky; top: 0; z-index: 3;
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
.rt-tbl td.rt-key { font-weight: 700; color: var(--ink); }
.rt-tbl td.c-end { text-align: left; font-family: var(--font-mono); font-size: .68rem;
  color: var(--muted); }
.rt-tbl .rt-win-mark { color: var(--good); font-weight: 700; }
.rt-tbl td.rt-zero { color: var(--muted); opacity: .55; }
.rt-legend { font-size: .8rem; color: var(--muted); margin: 0 0 1.3rem; line-height: 1.75; }
.rt-legend code { font-family: var(--font-mono); font-size: .95em; color: var(--ink-secondary); }
.rt-hint { font-family: var(--font-mono); font-size: .66rem; color: var(--muted);
  margin: .3rem 0 0; }
</style>
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


def build(facts):
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
        out.append('            <th class="c-rd">局</th>'
                   '<th class="c-time">時間</th><th class="c-who">玩家</th>')
        for label, title in COLUMNS:
            cls = ' class="c-end"' if label == "結果" else ""
            out.append(f'            <th{cls} title="{title}">{label}</th>')
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
                out.append(f'            <tr class="{" ".join(classes)}">')
                if n == 0:
                    out.append(f'              <td class="c-rd" rowspan="2">R{ri + 1}</td>')
                    out.append(f'              <td class="c-time" rowspan="2">{fmt_clock(dur)}</td>')
                colour = "rt-y" if pl == p1 else "rt-p"
                mark = ' <span class="rt-win-mark">✓</span>' if won else ""
                out.append(f'              <td class="c-who"><span class="{colour}">{pl}</span>{mark}</td>')
                for (val, key), (label, _t) in zip(cells(p, won), COLUMNS):
                    cls = []
                    if label == "結果":
                        cls.append("c-end")
                    elif key:
                        cls.append("rt-key")
                    if val in ("0", "–"):
                        cls.append("rt-zero")
                    attr = f' class="{" ".join(cls)}"' if cls else ""
                    out.append(f'              <td{attr}>{val}</td>')
                out.append('            </tr>')
        out.append('          </tbody>')
        out.append('        </table>')
        out.append('      </div>')
        out.append('      <p class="rt-hint">← 表可以左右拉睇齊全部欄 →</p>')
        out.append('    </div>')
    out += ['  </div>', '</section>', END]
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
    section = build(facts)
    how = inject(report_path, section)
    nrounds = sum(len(m["rounds"]) for m in facts["matches"])
    print(f"{how}: {nrounds} rounds x {len(COLUMNS) + 3} columns over "
          f"{len(facts['matches'])} matches -> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
