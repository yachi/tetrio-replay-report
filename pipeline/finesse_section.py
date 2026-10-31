"""最多犯錯嘅 finesse 擺位 — per player, the placements with the most finesse faults. The fifth quarantined
section.

Source: the SESSION's `sim/finesse-facts.json` (`pipeline/sim/emit-finesse-facts.ts`), never facts.json
(which supplies only the player order and each file's match position). Every lock of every round is
re-run through the vendored Triangle engine, the inputs the player spent on the piece (`falling.keys`)
are compared with the fewest inputs that reach the same cells on an empty board, and the excess is a
fault event. A placement is (piece, orientation, leftmost column).

WHY IT IS QUARANTINED. TETR.IO publishes no finesse algorithm, so the rule is fitted: it reproduces
the replay's own `finesse.perfectpieces` and `finesse.faults` exactly in most player-rounds, and the
section prints that anchor, with every round where it does not, beside the tables. Which PLACEMENT a
fault belongs to has no counter to check it against, so the section mints no claim ids, carries no ✓
and says so. `check_finesse_section.py` is the gate that keeps those sentences in.

Units, because the replay's own two counters are on two units (CLAUDE.md, the finesse bullet): the
ranking is by FAULT EVENTS, and one piece can carry several, so each card prints both the events and
the pieces that carried them. Every printed figure is an integer count; nothing is rounded.
"""
import html
import json
import os

from pipeline.claims.build_claims import SIMPLIFIED

FACTS_REL = os.path.join("sim", "finesse-facts.json")
SHOW = 5

QUARANTINE_MARKER = "呢節唔屬於信任鏈"
ANCHOR_MARKER = "同 TETR.IO 自己數嘅 finesse 一樣"
FITTED_MARKER = "條規則係對住 TETR.IO 嘅數砌出嚟"
NOT_SCORED_MARKER = "有撳 soft drop 嘅方塊唔計"
UNIT_MARKER = "一粒可以多按幾下"
REQUIRED = (QUARANTINE_MARKER, ANCHOR_MARKER, FITTED_MARKER, NOT_SCORED_MARKER, UNIT_MARKER)
TITLE = "最多犯錯嘅 finesse 擺位（未經證明）"

CSS = """  <style>
    /* Scoped under #finesse-placements and every class carries the fp- prefix: a generated
       section's <style> lands in the body and beats the report's own stylesheet. */
    #finesse-placements h3 { margin: 2.2rem 0 .3rem; font-size: 1.05rem; }
    #finesse-placements .fp-dot { display: inline-block; width: .5rem; height: .5rem;
      border-radius: 50%; margin-right: .4rem; }
    #finesse-placements .fp-dot.is-p1, #finesse-placements .fp-cell.is-p1 { background: var(--yachi); }
    #finesse-placements .fp-dot.is-p2, #finesse-placements .fp-cell.is-p2 { background: var(--pinglamb); }
    #finesse-placements .fp-grid { display: grid; gap: .8rem;
      grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr)); margin: .6rem 0 1rem; }
    #finesse-placements .fp-card { border: 1px solid var(--rule, rgba(127,127,127,.3));
      border-radius: .5rem; padding: .7rem .8rem; }
    #finesse-placements .fp-rank { font-size: .8rem; opacity: .7; }
    #finesse-placements .fp-board { display: grid; grid-template-columns: repeat(10, 1fr);
      gap: 1px; margin: .4rem 0 .5rem; max-width: 12rem; }
    #finesse-placements .fp-board span { aspect-ratio: 1; border-radius: 2px;
      background: rgba(127,127,127,.12); }
    #finesse-placements .fp-board span.fp-cell { opacity: 1; }
    #finesse-placements .fp-keys { font-family: var(--mono, ui-monospace, monospace);
      letter-spacing: .15em; }
    #finesse-placements .fp-card p { margin: .2rem 0; font-size: .9rem; }
    #finesse-placements td.fp-num { text-align: right; font-variant-numeric: tabular-nums; }
  </style>"""

# the emitter's SHAPES (cells from the bottom-left, y up), read from the artefact per placement
ARROWS = "←→ 撳一下；⇤⇥ 撳住推到牆；↻↺ 順／逆時針轉；180 轉半圈（算兩下）"


def facts_path(report_dir):
    return os.path.join(os.path.dirname(os.path.abspath(report_dir)), FACTS_REL)


def load(report_dir):
    path = facts_path(report_dir)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _order(data, players):
    by = {p["user"]: p for p in data["players"]}
    if sorted(by) != sorted(players):
        raise SystemExit(f"finesse_section: artefact players {sorted(by)} are not facts.json's "
                         f"{sorted(players)}")
    return [by[u] for u in players]


def _who(i, user):
    return f'<span class="fp-dot is-p{i + 1}"></span>{html.escape(user)}'


def _keys(moves):
    return "（冇按，原位落）" if not moves else " ".join(html.escape(m) for m in moves)


def board(m, slot):
    """A 10-wide strip, as tall as the piece, with the piece's cells filled at its column."""
    cells = {(m["col"] + x, y) for x, y in m["cells"]}
    h = max(y for _, y in m["cells"]) + 1
    out = []
    for y in reversed(range(h)):
        for x in range(10):
            out.append(f'<span class="fp-cell is-p{slot}"></span>' if (x, y) in cells else "<span></span>")
    label = f'{m["piece"]} 由左邊數第 {m["col"] + 1} 格起'
    return f'<div class="fp-board" role="img" aria-label="{html.escape(label)}">{"".join(out)}</div>'


def _card(rank, m, slot, pos):
    ex = m["example"]
    where = f'm{pos[ex["file"]]}r{ex["round"] + 1}'
    common = m["most_common_faulty"]
    return "\n".join([
        '      <div class="fp-card">',
        f'        <div class="fp-rank">第 {rank} 位</div>',
        f'        <strong>{html.escape(m["piece"])}</strong>，由左邊數第 {m["col"] + 1} 格起',
        f'        {board(m, slot)}',
        f'        <p>多按 <strong>{m["faults"]}</strong> 下，分佈喺 {m["faulty"]} 粒；'
        f'呢個位一共放咗 {m["scored"]} 粒。</p>',
        f'        <p>最少按法（{m["target"]} 下）：<span class="fp-keys">{_keys(m["optimal"])}</span></p>',
        f'        <p>最常見錯法（{common["n"]} 粒）：<span class="fp-keys">{_keys(common["moves"])}</span></p>',
        f'        <p>錯得最多嗰粒：{where} 佢第 {ex["lock"] + 1} 粒，按咗 {ex["keys"]} 下。</p>',
        '      </div>'])


def _anchor_note(data):
    a = data["anchor"]
    s = (f"逐局計返嘅完美粒數同多按次數，<strong>{a['agree']} / {a['rounds']}</strong> 個 player-round "
         f"{ANCHOR_MARKER}（replay 嘅 <code>finesse.perfectpieces</code> 同 <code>finesse.faults</code>）")
    if a["unknown"]:
        s += f"，另外 {a['unknown']} 個冇 counter、當未知"
    if not a["exceptions"]:
        return s + "。"
    return s + "；唔一樣嘅係 " + "、".join(
        f"<code>{html.escape(e['file'])}</code> 第 {e['round'] + 1} 局 {html.escape(e['user'])}"
        f"（完美 {e['engine']['perfect']} 對 {e['replay']['perfect']}，多按 {e['engine']['faults']} 對 "
        f"{e['replay']['faults']}）" for e in a["exceptions"]) + "。"


def section(data, players, positions):
    if data is None:
        return None
    ps = _order(data, players)
    body = []
    for i, p in enumerate(ps):
        ns = p["not_scored"]
        body += [f'    <h3>{_who(i, p["user"])}</h3>',
                 f'    <p>計咗 {p["scored"]} 粒，其中 {p["faulty"]} 粒有多按，加埋多按咗 '
                 f'<strong>{p["faults"]}</strong> 下；有多按嘅擺位有 {p["placements_with_faults"]} 個。'
                 f'冇計嘅：{ns["soft_drop"]} 粒有撳 soft drop'
                 + (f'，{ns["no_empty_board_path"]} 粒係空板去唔到嘅位' if ns["no_empty_board_path"] else "")
                 + '。</p>']
        top = p["top"][:SHOW]
        if not top:
            body.append("    <p>呢晚冇一個擺位有多按。</p>")
            continue
        body.append('    <div class="fp-grid">')
        body += [_card(r + 1, m, i + 1, positions) for r, m in enumerate(top)]
        body.append('    </div>')

    out = [
        '<section id="finesse-placements">',
        CSS,
        '  <div class="wrap-wide">',
        '    <div class="eyebrow">模擬器推導 · 唔屬於信任鏈</div>',
        f'    <h2 class="section-title">{TITLE}</h2>',
        '',
        '    <div class="method-note">',
        f'      <p><strong>同上面幾節一樣，{QUARANTINE_MARKER}。</strong>'
        '呢節將每一局用 replay 模擬器（vendored Triangle 引擎）由頭重跑，逐粒數返玩家用咗幾多下'
        '左右同轉，再同「喺空板由出生位置去同一個位最少要幾多下」比較；多出嚟嘅就係 finesse 錯。'
        '冇 claim 編號、冇 ✓ 標記。</p>',
        f'      <p>TETR.IO 冇公開佢點計 finesse，所以{FITTED_MARKER}：{NOT_SCORED_MARKER}'
        f'（當完美），空板去唔到嘅位（塞入去嘅）都唔計。{_anchor_note(data)}'
        '每粒錯喺邊個位就冇第二份實作對過。</p>',
        f'      <p>排名按多按嘅下數，{UNIT_MARKER}，所以每格都印埋係幾多粒。'
        f'擺位 = 方塊 + 方向 + 最左嗰格喺邊。箭咀：{ARROWS}。'
        '「最常見錯法」入面每個箭咀係撳落一次，撳住推都係一次。'
        '最少按法可以多過一種，呢度印其中一種。</p>',
        '    </div>',
        '',
        *body,
        '  </div>',
        '</section>',
    ]
    markup = "\n".join(out)
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"finesse_section: simplified glyph(s) {bad} — this report is "
                         "traditional-character Cantonese")
    return markup


def positions(facts):
    return {m["file"]: m["index"] for m in facts["matches"]}


def build(facts, report_dir):
    return section(load(report_dir), facts["players"], positions(facts))
