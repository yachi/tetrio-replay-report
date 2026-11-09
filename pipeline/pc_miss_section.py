"""行錯咗嗰一步 — per player, the placement after which a Perfect Clear was no longer possible. The sixth
quarantined section.

Source: the SESSION's `sim/pc-miss-facts.json` (`pipeline/sim/pc-miss.ts`), never facts.json (which
supplies only the player order and each file's match position). Inside two windows of each round (the
12 locks after the opener's T-spin Triple, and the 12 after each Perfect Clear) a PC solver is asked,
before and after every lock, whether the round's own dealt pieces can still clear the board within six
rows; a lock after which the answer turns from yes to no, re-checked with the engine's own movegen, is a
miss. The section prints only the REPORTED misses: a PC existed using the current piece, the hold and the
five-piece preview (no hindsight), and the next lock is inside the verified prefix. Each carries a
category, computed by the emitter: `hole`, `over`, `hold`, `spot` (see `CATEGORIES`).

WHY IT IS QUARANTINED. One solver over one simulator board: whether a PC was possible has no second
implementation and no replay counter, so the section mints no claim ids, carries no ✓ and says so; and a
PC being possible says nothing about whether the player was building one, which it also says.
`check_pc_miss_section.py` keeps those sentences in.

Selection: per player and category, the first `SHOW` misses in artefact order (match, round, lock); the
rest are counted. Every printed figure is an integer count; nothing is rounded.
"""
import html
import json
import os

from pipeline import replay_page, replay_section, video_links
from pipeline.claims.build_claims import SIMPLIFIED

FACTS_REL = os.path.join("sim", "pc-miss-facts.json")
SHOW = 3
FULL = 1023

QUARANTINE_MARKER = "呢節唔屬於信任鏈"
PREVIEW_MARKER = "淨係用嗰陣手上嗰粒、hold 同 5 粒 next 已經做得到全消"
VERIFIED_MARKER = "下一粒喺可核嘅重播範圍入面"
SOLVER_MARKER = "右邊嗰塊板係 solver 搵到嘅其中一個擺法"
CAVEAT_MARKER = "做得到全消唔等於佢想做全消"
SELECT_MARKER = "每類畫頭三粒（按比賽次序）"
REQUIRED = (QUARANTINE_MARKER, PREVIEW_MARKER, VERIFIED_MARKER, SOLVER_MARKER, CAVEAT_MARKER, SELECT_MARKER)
TITLE = "行錯咗嗰一步：搞到全消唔到（未經證明）"

# order is the emitter's precedence (first that applies)
CATEGORIES = (
    ("hole", "蓋住窿", "擺完多咗一格俾蓋住嘅空格。"),
    ("over", "疊得太高", "擺完個盤高過全消要用嗰幾行。"),
    ("hold", "揀錯粒", "應該先擺另一粒（用 hold 換，或者留返遲啲）。"),
    ("spot", "擺錯位", "同一粒，擺第二個位就仲做得到。"),
)
KIND = {"tst": "開局 TST 之後", "pc": "全消之後"}

PIECE = {"I": "#2bb5c9", "O": "#d9b12a", "T": "#9b4fcf", "S": "#4fb043", "Z": "#d9463c",
         "J": "#3a5fd8", "L": "#e5832a", "G": "#8c93a1"}

CSS = """  <style>
    /* Scoped under #pc-miss and every class carries the pm- prefix: a generated section's <style>
       lands in the body and beats the report's own stylesheet. */
    #pc-miss h3 { margin: 2.2rem 0 .3rem; font-size: 1.05rem; }
    #pc-miss h4 { margin: 1.4rem 0 .2rem; font-size: .98rem; }
    #pc-miss .pm-dot { display: inline-block; width: .5rem; height: .5rem; border-radius: 50%;
      margin-right: .4rem; }
    #pc-miss .pm-dot.is-p1 { background: var(--yachi, var(--p1)); }
    #pc-miss .pm-dot.is-p2 { background: var(--pinglamb, var(--p2)); }
    #pc-miss .pm-grid { display: grid; gap: .8rem; margin: .6rem 0 1rem;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 24rem), 1fr)); }
    #pc-miss .pm-card { border: 1px solid var(--rule, rgba(127,127,127,.3)); border-radius: .5rem;
      padding: .7rem .8rem; min-width: 0; }
    #pc-miss .pm-card p { margin: .25rem 0; font-size: .9rem; }
    #pc-miss .pm-head { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .2rem .8rem;
      font-size: .9rem; }
    #pc-miss .pm-tag { font-size: .75rem; opacity: .75; }
    #pc-miss .pm-boards { display: flex; flex-wrap: wrap; gap: .8rem; align-items: flex-end;
      margin: .4rem 0; }
    #pc-miss figure { margin: 0; }
    #pc-miss figcaption { font-size: .8rem; opacity: .8; margin-bottom: .2rem; }
    #pc-miss .pm-board { display: grid; grid-template-columns: repeat(10, .8rem); grid-auto-rows: .8rem;
      gap: 1px; }
    #pc-miss .pm-board span { border-radius: 1px; background: rgba(127,127,127,.15);
      font: 600 .55rem/.8rem var(--mono, ui-monospace, monospace); text-align: center; color: #fff; }
    #pc-miss .pm-board span.pm-hl { outline: 2px solid #e8364f; outline-offset: -2px; }
    #pc-miss .pm-p { display: inline-block; min-width: 1.2em; text-align: center; border-radius: 3px;
      color: #fff; font-family: var(--mono, ui-monospace, monospace); padding: 0 2px; margin-right: 1px; }
    #pc-miss td.pm-num { text-align: right; font-variant-numeric: tabular-nums; }
  </style>"""


def facts_path(report_dir):
    return os.path.join(os.path.dirname(os.path.abspath(report_dir)), FACTS_REL)


def load(report_dir):
    path = facts_path(report_dir)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def reported(m):
    return m["lost_to"] == "placement" and m.get("in_preview") is True and m["verified"] is True


def _fail(msg):
    raise SystemExit(f"pc_miss_section: {msg}")


def chip(p):
    return f'<span class="pm-p" style="background:{PIECE[p]}">{html.escape(p)}</span>'


def board(rows, hl=frozenset(), nums=None, h=None):
    """Rows bottom-up ('.' empty), drawn top-down; `hl` cell indices are outlined."""
    h = h or max([i + 1 for i, r in enumerate(rows) if r.strip(".")] + [1])
    out = []
    for y in range(h - 1, -1, -1):
        r = rows[y] if y < len(rows) else "." * 10
        for x in range(10):
            ch = r[x]
            style = f' style="background:{PIECE[ch]}"' if ch != "." else ""
            cls = ' class="pm-hl"' if (y * 10 + x) in hl else ""
            out.append(f"<span{cls}{style}>{(nums or {}).get((y, x), '')}</span>")
    return f'<div class="pm-board">{"".join(out)}</div>'


def with_placement(grid, cells, piece):
    g = [list(r) for r in grid]
    for c in cells:
        y, x = divmod(c, 10)
        while len(g) <= y:
            g.append(list("." * 10))
        g[y][x] = piece
    return ["".join(r) for r in g]


def composite(grid0, plan, tag):
    """The solver's plan drawn on the board it starts from, in the kept-rows frame: every row the
    plan fills is drawn where it stood, numbered by placement. Refuses a plan that does not clear."""
    pre = [sum(1 << x for x, ch in enumerate(r) if ch != ".") for r in grid0]
    while pre and not pre[-1]:
        pre.pop()
    grid = [list(r) for r in grid0]
    cur = [[i, m] for i, m in enumerate(pre)]
    nxt, nums = len(pre), {}
    for step, p in enumerate(plan, 1):
        for cc in p["cells"]:
            y, x = divmod(cc, 10)
            while len(cur) <= y:
                cur.append([nxt, 0])
                nxt += 1
            o = cur[y][0]
            if cur[y][1] >> x & 1:
                _fail(f"{tag}: plan step {step} overlaps a filled cell")
            cur[y][1] |= 1 << x
            while len(grid) <= o:
                grid.append(list("." * 10))
            grid[o][x] = p["piece"]
            nums[(o, x)] = str(step)
        cur = [r for r in cur if r[1] != FULL]
    if any(r[1] for r in cur):
        _fail(f"{tag}: the plan does not clear the board")
    g = ["".join(r) for r in grid]
    h = max(i + 1 for i, r in enumerate(g) if r.strip("."))
    if any("." in g[i] for i in range(h)):
        _fail(f"{tag}: the plan leaves a hole")
    return board(g, nums=nums, h=h), h


class Locator:
    """Replay-page positions and video times for one session's misses."""

    def __init__(self, session_dir, session):
        self.session = session
        self.data, self.facts = replay_page.load(session_dir)
        self.video = video_links.for_session(session)
        self._cache = {}

    def _round(self, file, rnd):
        key = (file, rnd)
        if key not in self._cache:
            at = [(mi, ri) for mi, mm in enumerate(self.facts["matches"]) if mm["file"] == file
                  for ri, fr in enumerate(mm["rounds"]) if fr["index"] == rnd]
            if len(at) != 1:
                _fail(f"{file} round {rnd} is not one round of facts.json")
            self._cache[key] = (at[0], replay_section.round_payload(self.data, self.facts, *at[0]))
        return self._cache[key]

    def links(self, file, rnd, user, i):
        (mi, _), pl = self._round(file, rnd)
        users = [p["user"] for p in pl["players"]]
        slot = users.index(user)
        mine = [n for n, s in enumerate(pl["order"]) if s == str(slot)]
        t, frames = 0, []
        for lk in pl["players"][slot]["locks"]:
            t += lk[0]
            frames.append(t)
        rep = f"{self.session}-replay.html#{pl['label']}@p{mine[i]}"
        vid = self.video.moment_url(mi + 1, rnd + 1, frames[i]) if self.video else None
        return pl["label"], rep, vid


def card(miss, kind, loc, file, rnd, user):
    st = miss["state"]
    i = miss["i"]
    label, rep, vid = loc.links(file, rnd, user, i)
    comp, h = composite(st["grid"], miss["plan"], f"{loc.session} {label} {user} {i}")
    placed = with_placement(st["grid"], st["cells"], st["piece"])
    seq = " → ".join(chip(p["piece"]) + ("（用 hold 換）" if p["held"] else "") for p in miss["plan"])
    hold = chip(st["hold"]) if st["hold"] else "空"
    vlink = f' · <a href="{html.escape(vid)}" target="_blank" rel="noopener">▶ 影片</a>' if vid else ""
    return "\n".join([
        '      <div class="pm-card">',
        f'        <div class="pm-head"><strong>{html.escape(label)} 第 {i + 1} 粒</strong>'
        f'<span class="pm-tag">{KIND[kind]}</span>'
        f'<span><a href="{html.escape(rep)}">重播呢一步</a>{vlink}</span></div>',
        f'        <p>手上 {chip(st["cur"])}　hold {hold}　next {"".join(chip(p) for p in st["next"])}</p>',
        '        <div class="pm-boards">',
        f'          <figure><figcaption>佢擺咗 {chip(st["piece"])}'
        f'{"（由 hold 拎出嚟）" if st["held"] else ""}</figcaption>'
        f'{board(placed, hl=frozenset(st["cells"]))}</figure>',
        f'          <figure><figcaption>擺完之後</figcaption>{board(miss["after"])}</figure>',
        f'          <figure><figcaption>可以咁擺：{h} 行全消</figcaption>{comp}</figure>',
        '        </div>',
        f'        <p>次序：{seq}</p>',
        '      </div>'])


def tally(data):
    """Per user: windows and PCs per kind, and the reported misses as (kind, round, miss) in order."""
    out = {}
    for r in data["rounds"]:
        u = out.setdefault(r["user"], {"win": {"tst": [0, 0], "pc": [0, 0]}, "misses": []})
        for w in r["windows"]:
            u["win"][w["kind"]][0] += 1
            u["win"][w["kind"]][1] += w["outcome"] == "pc"
            for m in w["misses"]:
                if reported(m):
                    if m.get("category") not in dict((k, 0) for k, _, _ in CATEGORIES):
                        _fail(f"m{r['match']} round {r['round']} {r['user']} lock {m['i']}: "
                              f"reported miss without a category")
                    u["misses"].append((w["kind"], r, m))
                elif "category" in m:
                    _fail(f"a miss that is not reported carries a category")
    return out


def _who(i, user):
    return f'<span class="pm-dot is-p{i + 1}"></span>{html.escape(user)}'


def player_block(i, user, t, loc, heading="h3"):
    win, ms = t["win"], t["misses"]
    by = {k: [x for x in ms if x[2]["category"] == k] for k, _, _ in CATEGORIES}
    nt = sum(1 for x in ms if x[0] == "tst")
    np_ = len(ms) - nt
    body = [f'    <{heading}>{_who(i, user)}</{heading}>',
            f'    <p>開局 TST 之後 {win["tst"][0]} 次，做到全消 {win["tst"][1]} 次，行錯 <strong>{nt}</strong> 粒；'
            f'全消之後 {win["pc"][0]} 次，再全消 {win["pc"][1]} 次，行錯 <strong>{np_}</strong> 粒。</p>']
    if not ms:
        return body + ["    <p>呢晚冇一粒行錯。</p>"]
    body.append("    <table><thead><tr><th>類別</th><th>粒數</th></tr></thead><tbody>"
                + "".join(f'<tr><td>{name}</td><td class="pm-num">{len(by[k])}</td></tr>'
                          for k, name, _ in CATEGORIES) + "</tbody></table>")
    for k, name, why in CATEGORIES:
        if not by[k]:
            continue
        rest = len(by[k]) - SHOW
        body += [f'    <h4>{name}（{len(by[k])} 粒）</h4>', f'    <p>{why}'
                 + (f'下面畫頭 {SHOW} 粒，仲有 {rest} 粒冇畫。' if rest > 0 else "") + '</p>',
                 '    <div class="pm-grid">']
        body += [card(m, kind, loc, r["file"], r["round"], user) for kind, r, m in by[k][:SHOW]]
        body.append('    </div>')
    return body


def method_note(data):
    return [
        '    <div class="method-note">',
        f'      <p><strong>同上面幾節一樣，{QUARANTINE_MARKER}。</strong>'
        '呢節用 replay 模擬器重建每一粒擺之前嘅盤面，再用一個 Perfect Clear solver 試：'
        f'用嗰局真正嘅出牌次序同 hold 規則，{data["maxh"]} 行之內仲有冇擺法清晒個盤。'
        '擺之前得、擺完唔得嘅嗰一粒就係「行錯」；「唔得」再用遊戲引擎自己嘅移動搜尋（包埋 180 度轉）核多次。'
        '冇 claim 編號、冇 ✓ 標記。</p>',
        f'      <p>睇兩段：開局 T-spin Triple 之後嗰 {data["span"]} 粒，同每次全消之後嗰 {data["span"]} 粒。'
        f'只計 {PREVIEW_MARKER}、{VERIFIED_MARKER}、而且冇垃圾行入嚟嘅。'
        f'{SOLVER_MARKER}，唔一定係唯一或者最好；格入面嘅數字係擺嘅次序。</p>',
        f'      <p>{CAVEAT_MARKER}：好多時佢揀咗打 TSD 或者繼續砌。全消之後嗰段，盤面好多時已經超出可核範圍，'
        f'所以嗰段計到嘅粒數少。類別按次序揀第一個啱嘅；{SELECT_MARKER}，紅框係佢嗰粒。</p>',
        '    </div>',
    ]


def section(data, players, loc):
    if data is None:
        return None
    if data.get("report_eligible") is not False:
        _fail("the artefact declares itself report-eligible")
    t = tally(data)
    if sorted(t) != sorted(players):
        _fail(f"artefact players {sorted(t)} are not facts.json's {sorted(players)}")
    body = []
    for i, u in enumerate(players):
        body += player_block(i, u, t[u], loc)
    out = [
        '<section id="pc-miss">',
        CSS,
        '  <div class="wrap-wide">',
        '    <div class="eyebrow">模擬器推導 · 唔屬於信任鏈</div>',
        f'    <h2 class="section-title">{TITLE}</h2>',
        '',
        *method_note(data),
        '',
        *body,
        '  </div>',
        '</section>',
    ]
    markup = "\n".join(out)
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        _fail(f"simplified glyph(s) {bad} — this report is traditional-character Cantonese")
    return markup


def build(facts, report_dir):
    data = load(report_dir)
    if data is None:
        return None
    session_dir = os.path.dirname(os.path.abspath(report_dir))
    if data["session"] != os.path.basename(session_dir):
        _fail(f"artefact session {data['session']} is not {os.path.basename(session_dir)}")
    return section(data, facts["players"], Locator(session_dir, data["session"]))
