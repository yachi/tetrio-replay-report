"""Build the per-round data section and inject it into a report.

    python3 -m pipeline.build_round_table sessions/2026-07-24/report

Renders every round of every match in the TETR.IO end-screen layout — each player's
APM / PPS / VS in a coloured bar with the round duration between them, winner bright and
loser dimmed — and adds the stats that screen leaves out: pieces, attack per piece, keys
per piece, downstack, spike, B2B, combo, T-spins, quads, finesse, and the queued vs
materialised garbage split. The loser's bar also carries how the round ended.

Everything is derived from facts.json, so the table cannot disagree with the data the
claims are proved against. Re-run after regenerating facts.json.

The section is delimited by HTML comment markers and replaced in place on re-runs, so
this is idempotent.
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
.rt-match { margin: 0 0 2.4rem; }
.rt-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: .55rem .9rem;
  padding: 0 0 .5rem; border-bottom: 1px solid var(--border); margin-bottom: .85rem; }
.rt-head .rt-no { font-family: var(--font-mono); font-size: .78rem; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted); }
/* usernames are lowercase; never uppercase them */
.rt-head .rt-who { font-family: var(--font-mono); font-size: .78rem; color: var(--muted); }
.rt-head .rt-score { font-weight: 800; font-size: 1.05rem; font-variant-numeric: tabular-nums; }
.rt-head .rt-agg { font-family: var(--font-mono); font-size: .74rem; color: var(--muted);
  margin-left: auto; font-variant-numeric: tabular-nums; }
.rt-y { color: var(--yachi); } .rt-p { color: var(--pinglamb); }

.rt-row { display: grid; grid-template-columns: 1fr auto 1fr; gap: .5rem;
  align-items: stretch; margin-bottom: .5rem; }
.rt-side { border-radius: 10px; padding: .5rem .7rem; border: 1px solid var(--border);
  display: flex; flex-direction: column; gap: .28rem; min-width: 0; }
.rt-side.rt-left { text-align: right; background: var(--yachi-tint); }
.rt-side.rt-right { text-align: left; background: var(--pinglamb-tint); }
.rt-side.rt-win.rt-left { background: var(--yachi-tint-strong); border-color: var(--yachi); }
.rt-side.rt-win.rt-right { background: var(--pinglamb-tint-strong); border-color: var(--pinglamb); }
.rt-side.rt-lose { opacity: .62; }
.rt-rates { font-family: var(--font-mono); font-size: .82rem; font-weight: 700;
  font-variant-numeric: tabular-nums; letter-spacing: -.01em; }
.rt-rates span { color: var(--muted); font-weight: 500; font-size: .72rem; }
.rt-extra { font-family: var(--font-mono); font-size: .68rem; color: var(--ink-secondary);
  font-variant-numeric: tabular-nums; line-height: 1.5; word-break: break-word; }
.rt-extra b { font-weight: 700; color: var(--ink); }
.rt-dead { color: var(--muted); font-style: italic; }
.rt-mid { display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-width: 3.4rem; padding: 0 .2rem; }
.rt-clock { font-family: var(--font-mono); font-weight: 700; font-size: .86rem;
  font-variant-numeric: tabular-nums; }
.rt-rd { font-family: var(--font-mono); font-size: .64rem; color: var(--muted); }
.rt-legend { font-size: .78rem; color: var(--muted); margin: 0 0 1.4rem; line-height: 1.7; }
.rt-legend code { font-family: var(--font-mono); font-size: .95em; color: var(--ink-secondary); }
@media (max-width: 720px) {
  .rt-row { grid-template-columns: 1fr; }
  .rt-side.rt-left, .rt-side.rt-right { text-align: left; }
  .rt-mid { flex-direction: row; gap: .5rem; justify-content: flex-start; padding: .1rem 0; }
}
</style>
"""


def fmt_clock(ms):
    total = ms // 1000
    return f"{total // 60}:{total % 60:02d}"


def r1(x_x1000):
    """x1000 int -> one decimal place, floored (the project's 約 convention)."""
    return f"{x_x1000 // 100 / 10:.1f}"


def r2(x_x1000):
    return f"{x_x1000 // 10 / 100:.2f}"


def ratio(num, den, dp=2):
    """num/den floored to dp decimals, as a string; '-' when den is 0."""
    if not den:
        return "-"
    scale = 10 ** dp
    return f"{(num * scale) // den / scale:.{dp}f}"


def pct(num, den):
    if not den:
        return "-"
    return f"{(num * 100) // den}%"


def extras(p):
    """The stats the in-game end screen does not show."""
    c = p["clears"]
    queued = sum(g["amt"] for g in p["garbage_events"])
    bits = [
        f"<b>{p['pieces']}</b>P",
        f"APP <b>{ratio(p['garbage_attack'], p['pieces'])}</b>",
        f"KPP <b>{ratio(p['inputs'], p['pieces'])}</b>",
        f"DS <b>{ratio(p['garbage_cleared'], p['pieces'])}</b>",
        f"{p['lines']}行",
        f"spike <b>{p['maxspike']}</b>",
        f"B2B {p['topbtb']}",
        f"combo {p['topcombo']}",
        f"T {p['tspins']}",
        f"quad {c['quads']}",
        f"TSD {c['tspin_doubles']}",
        f"TST {c['tspin_triples']}",
    ]
    if c["allclear"]:
        bits.append(f"PC <b>{c['allclear']}</b>")
    bits += [
        f"finesse {pct(p['finesse_perfect'], p['pieces'])}({p['finesse_faults']}錯)",
        f"攻 {p['garbage_attack']}",
        f"送 {p['garbagesent']}",
        f"射埋 {queued}→食 {p['garbagereceived']}",
        f"清 {p['garbage_cleared']}",
        f"分 {p['score']:,}",
    ]
    return " · ".join(bits)


def build(facts):
    p1, p2 = facts["players"]
    out = [START, CSS,
           '<section id="rounds">', '  <div class="wrap-wide">',
           '    <div class="eyebrow">逐局數據 · ROUND BY ROUND</div>',
           '    <h2 class="section-title">逐局全數據</h2>',
           '    <p class="rt-legend">',
           f'      每一局兩邊嘅 APM / PPS / VS 同局長，贏嗰邊亮色。下面一行係遊戲畫面唔會顯示嘅數：',
           '      <code>P</code> 方塊數、<code>APP</code> 每粒方塊嘅攻擊、<code>KPP</code> 每粒方塊嘅按鍵、',
           '      <code>DS</code> 每粒方塊清走嘅垃圾、spike / B2B / combo 上限、T-spin 同 quad 數、',
           '      finesse 完美率（同失誤次數）、攻擊量、送出垃圾、',
           '      <code>射埋</code>（對手射過嚟嘅攻擊，未 cancel）→ <code>食</code>（真正變成垃圾行嘅）、',
           '      清走嘅垃圾、同埋分數。輸嗰邊會標埋係點死嘅。',
           '    </p>',
           ]
    for mi, m in enumerate(facts["matches"]):
        lb = m["leaderboard"]
        win = m["winner"]
        out.append('    <div class="rt-match">')
        out.append('      <div class="rt-head">')
        out.append(f'        <span class="rt-no">M{mi + 1}</span>')
        out.append(f'        <span class="rt-score"><span class="rt-y">{p1}</span> '
                   f'{m["score"][p1]}:{m["score"][p2]} '
                   f'<span class="rt-p">{p2}</span></span>')
        out.append(f'        <span class="rt-who">{win} 贏</span>')
        out.append('        <span class="rt-agg">'
                   f'{p1} {r1(lb[p1]["apm_x1000"])} APM · {r2(lb[p1]["pps_x1000"])} PPS · '
                   f'{r1(lb[p1]["vs_x1000"])} VS &nbsp;|&nbsp; '
                   f'{p2} {r1(lb[p2]["apm_x1000"])} APM · {r2(lb[p2]["pps_x1000"])} PPS · '
                   f'{r1(lb[p2]["vs_x1000"])} VS</span>')
        out.append('      </div>')
        for ri, r in enumerate(m["rounds"]):
            dur = max(d["lifetime"] for d in r["players"].values())
            out.append('      <div class="rt-row">')
            for pl, side in ((p1, "rt-left"), (p2, "rt-right")):
                p = r["players"][pl]
                won = r["winner"] == pl
                cls = f"rt-side {side} {'rt-win' if won else 'rt-lose'}"
                death = ""
                if not won and p.get("gameoverreason"):
                    death = f' <span class="rt-dead">({p["gameoverreason"]})</span>'
                out.append(f'        <div class="{cls}">')
                out.append(f'          <div class="rt-rates">{r1(p["apm_x1000"])} <span>APM</span> · '
                           f'{r2(p["pps_x1000"])} <span>PPS</span> · '
                           f'{r1(p["vs_x1000"])} <span>VS</span>{death}</div>')
                out.append(f'          <div class="rt-extra">{extras(p)}</div>')
                out.append('        </div>')
                if side == "rt-left":
                    out.append('        <div class="rt-mid">')
                    out.append(f'          <div class="rt-clock">{fmt_clock(dur)}</div>')
                    out.append(f'          <div class="rt-rd">R{ri + 1}</div>')
                    out.append('        </div>')
            out.append('      </div>')
        out.append('    </div>')
    out += ['  </div>', '</section>', END]
    return "\n".join(out) + "\n"


def inject(report_path, section):
    with open(report_path, encoding="utf-8") as fh:
        html = fh.read()
    if START in html and END in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), section.rstrip("\n"),
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

    facts_path = os.path.join(args.report_dir, "facts.json")
    report_path = os.path.join(args.report_dir, "report.html")
    with open(facts_path, encoding="utf-8") as fh:
        facts = json.load(fh)

    section = build(facts)
    how = inject(report_path, section)
    nrounds = sum(len(m["rounds"]) for m in facts["matches"])
    print(f"{how}: {nrounds} rounds over {len(facts['matches'])} matches "
          f"({len(section)} bytes) -> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
