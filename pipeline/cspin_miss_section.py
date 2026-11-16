"""C-Spin 冇砌 — per player, the holes under the stack where cold-clear builds a C-Spin and the player
did not. The eighth quarantined section, in the 練乜 tier after 行錯咗嗰一步.

Source: the SESSION's `sim/cspin-miss-facts.json` (`pipeline/sim/cspin-miss.ts`), never facts.json
(which supplies only the player order and each file's match position). A hole is a row with nine filled
cells, a filled cell under its empty one and the column open above; a window opens on the first board
where the hole is one step from a C-Spin slot (a side neighbour one row up empty, that row holding eight
cells, the cell over the hole empty), for a hole that appeared after the opener, never became a slot
and was then filled or covered. cold-clear plays 14 pieces from that board with the round's own pieces
and garbage; the hole cell is carried through every clear and garbage row, and the first placement on
it decides. A case is a window where cold-clear's decision is a T with a full T-spin clearing three and
the player's is not.

WHY IT IS QUARANTINED. One simulator and one bot: whether cold-clear builds a C-Spin has no second
implementation, and a bot's line is not a standard answer, so the section mints no claim ids, carries no
✓ and says so; `check_cspin_miss_section.py` keeps those sentences in. Every case is drawn; every printed
figure is an integer count.
"""
import html
import json
import os

from pipeline import replay_section
from pipeline.claims.build_claims import SIMPLIFIED
from pipeline.pc_miss_section import PIECE, Locator, chip

FACTS_REL = os.path.join("sim", "cspin-miss-facts.json")
H = 40

QUARANTINE_MARKER = "呢節唔屬於信任鏈"
BOT_MARKER = "cold-clear 係 bot，佢嘅擺法唔係標準答案"
WINDOW_MARKER = "只計開局之後先出現、未砌成 C-Spin 位就俾人填咗或者蓋住嘅窿"
SAME_MARKER = "cold-clear 用嗰局真係派嘅粒同真係嚟嘅垃圾"
READY_MARKER = "佢落 T 嗰陣 C-Spin 位都未砌好，所以唔係 misdrop"
REQUIRED = (QUARANTINE_MARKER, BOT_MARKER, WINDOW_MARKER, SAME_MARKER, READY_MARKER)
TITLE = "C-Spin 冇砌：cold-clear 會砌嘅窿（未經證明）"

CSS = """  <style>
    /* Scoped under #cspin-miss and every class carries the cm- prefix: a generated section's <style>
       lands in the body and beats the report's own stylesheet. */
    #cspin-miss h3 { margin: 2.2rem 0 .3rem; font-size: 1.05rem; }
    #cspin-miss .cm-dot { display: inline-block; width: .5rem; height: .5rem; border-radius: 50%;
      margin-right: .4rem; }
    #cspin-miss .cm-dot.is-p1 { background: var(--yachi, var(--p1)); }
    #cspin-miss .cm-dot.is-p2 { background: var(--pinglamb, var(--p2)); }
    #cspin-miss .cm-grid { display: grid; gap: .8rem; margin: .6rem 0 1rem;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 24rem), 1fr)); }
    #cspin-miss .cm-card { border: 1px solid var(--rule, rgba(127,127,127,.3)); border-radius: .5rem;
      padding: .7rem .8rem; min-width: 0; }
    #cspin-miss .cm-card p { margin: .25rem 0; font-size: .9rem; }
    #cspin-miss .cm-head { display: flex; flex-wrap: wrap; justify-content: space-between; gap: .2rem .8rem;
      font-size: .9rem; }
    #cspin-miss .cm-tag { font-size: .75rem; opacity: .75; }
    #cspin-miss .cm-boards { display: flex; flex-wrap: wrap; gap: .8rem; align-items: flex-end; margin: .4rem 0; }
    #cspin-miss figure { margin: 0; }
    #cspin-miss figcaption { font-size: .8rem; opacity: .8; margin-bottom: .2rem; }
    #cspin-miss .cm-board { display: grid; grid-template-columns: repeat(10, .8rem); grid-auto-rows: .8rem;
      gap: 1px; }
    #cspin-miss .cm-board span { border-radius: 1px; background: rgba(127,127,127,.15); }
    #cspin-miss .cm-board span.cm-hole { outline: 2px solid #e8364f; outline-offset: -2px; }
    #cspin-miss .cm-board span.cm-new { outline: 2px solid #fff; outline-offset: -2px; }
    #cspin-miss .cm-board span.cm-full { filter: brightness(1.6) saturate(.6); }
    #cspin-miss .pm-p { display: inline-block; min-width: 1.2em; text-align: center; border-radius: 3px;
      color: #fff; font-family: var(--mono, ui-monospace, monospace); padding: 0 2px; margin-right: 1px; }
    #cspin-miss td.cm-num { text-align: right; font-variant-numeric: tabular-nums; }
    #cspin-miss .cm-ctl { display: flex; flex-wrap: wrap; gap: .25rem; align-items: center; margin-top: .3rem; }
    #cspin-miss .cm-ctl button { font: .8rem/1 var(--mono, ui-monospace, monospace); padding: .3rem .45rem;
      min-width: 2rem; border: 1px solid var(--rule, rgba(127,127,127,.4)); border-radius: 4px;
      background: transparent; color: inherit; cursor: pointer; }
    #cspin-miss .cm-ctl button.cm-play { min-width: 3.2rem; }
    #cspin-miss .cm-ctl[hidden] { display: none; }
    #cspin-miss .cm-step { font-size: .75rem; min-height: 1.4em; margin: .2rem 0 0; white-space: nowrap; }
  </style>"""


def facts_path(report_dir):
    return os.path.join(os.path.dirname(os.path.abspath(report_dir)), FACTS_REL)


def load(report_dir):
    path = facts_path(report_dir)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _fail(msg):
    raise SystemExit(f"cspin_miss_section: {msg}")


# ---- the board, in the emitter's frame: 40 rows top-down, cells [x, y] -----------------------
def pad(rows):
    return ["." * 10] * (H - len(rows)) + list(rows)


def lock_clear(board, cells, mark):
    g = [list(r) for r in board]
    for x, y in cells:
        if not (0 <= x < 10 and 0 <= y < H) or g[y][x] != ".":
            _fail(f"a placement at {x},{y} is off the board or on a filled cell")
        g[y][x] = mark
    full = [y for y in range(H) if "." not in g[y]]
    kept = ["".join(r) for y, r in enumerate(g) if y not in full]
    return ["." * 10] * len(full) + kept, full


def occ(rows):
    return ["".join("." if ch == "." else "#" for ch in r) for r in rows]


def shift(after, nxt):
    """The garbage rows that came in after a lock: the g with after[g:] == nxt[:H-g] by occupancy."""
    a, n = occ(after), occ(nxt)
    for g in range(13):
        if a[g:] == n[:H - g]:
            return g
    return None


def carry(r, full, g):
    return None if r in full else r + sum(1 for y in full if y > r) - g


def ladder(start, boards, steps, hole, tag):
    """The steps in order, each on the board before it: (board, cells, piece, hold, row of the hole,
    full rows, garbage rows that came after). Every board after a lock must be the next committed one."""
    out = []
    board = pad(start)
    r, c = hole
    for j, s in enumerate(steps):
        after, full = lock_clear(board, s["cells"], s["piece"])
        out.append({"board": board, "cells": s["cells"], "piece": s["piece"], "hold": s.get("hold"),
                    "hole": (r, c) if r is not None else None, "full": full})
        if j + 1 >= len(steps):
            out[-1]["after"] = after
            break
        nxt = pad(boards[j])
        g = len(s["garbage_cols"]) if "garbage_cols" in s else shift(after, nxt)
        if g is None:
            _fail(f"{tag}: the board after step {j + 1} is not the next committed board")
        if "garbage_cols" in s:
            built = after[g:] + ["G" * gc + "." + "G" * (9 - gc) for gc in s["garbage_cols"]]
            if built != nxt:
                _fail(f"{tag}: cold-clear's board after step {j + 1} is not the committed one")
        elif occ(after[g:]) != occ(nxt[:H - g]):
            _fail(f"{tag}: the player's board after step {j + 1} is not the committed one")
        out[-1]["garbage"] = g
        if r is not None:
            r = carry(r, full, g)
            if r is not None and (r < 0 or nxt[r][c] != "."):
                r = None
        board = nxt
    return out


def _top(rows):
    return next((y for y, row in enumerate(rows) if row.strip(".")), H)


def frames(ld, final_cap):
    """Each step drawn on its board with the piece placed (`n` its cells, `f` full rows, `o` the hole);
    the last frame is the board after the last lock. All frames share one height, bottom-aligned."""
    shots = []
    for k, st in enumerate(ld):
        g = [list(r) for r in st["board"]]
        for x, y in st["cells"]:
            g[y][x] = st["piece"]
        cap = [f"第 {k + 1} 粒 ", {"p": st["piece"]}, "（用 hold）" if st["hold"] else ""]
        if k and ld[k - 1].get("garbage"):
            cap = [f"收咗 {ld[k - 1]['garbage']} 行垃圾　"] + cap
        shots.append((["".join(r) for r in g], st["cells"], st["full"], st["hole"], cap))
    last = ld[-1]
    shots.append((last["after"], [], [], None, list(final_cap)))
    h = max(4, max(H - _top(b) for b, *_ in shots))
    base = H - h
    out = []
    for b, cells, full, hole, cap in shots:
        out.append({"b": "".join(b[base:]), "n": sorted((y - base) * 10 + x for x, y in cells),
                    "f": sorted(y - base for y in full),
                    "o": (hole[0] - base) * 10 + hole[1] if hole else -1, "c": cap})
    return h, out


def draw(fr, h):
    nw, fl = set(fr["n"]), set(fr["f"])
    out = []
    for i, ch in enumerate(fr["b"]):
        cls = " ".join(c for c, on in (("cm-new", i in nw), ("cm-full", i // 10 in fl and ch != "."),
                                       ("cm-hole", i == fr["o"])) if on)
        style = f' style="background:{PIECE[ch]}"' if ch != "." else ""
        out.append(f'<span{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}{style}></span>')
    if len(out) != h * 10:
        _fail("a frame is not its board's height")
    return f'<div class="cm-board">{"".join(out)}</div>'


CONTROLS = ('<div class="cm-ctl" hidden><button type="button" data-act="start" aria-label="由頭">⏮</button>'
            '<button type="button" data-act="back" aria-label="上一步">◀</button>'
            '<button type="button" class="cm-play" data-act="play">示範</button>'
            '<button type="button" data-act="fwd" aria-label="下一步">▶</button></div>'
            '<p class="cm-step" aria-live="polite"></p>')


def anim(h, fr, static, caption):
    data = html.escape(json.dumps({"h": h, "fr": fr}, ensure_ascii=False, separators=(",", ":")), quote=True)
    return (f'<figure class="cm-anim" data-frames="{data}"><figcaption>{caption}</figcaption>'
            f'{draw(fr[static], h)}{CONTROLS}</figure>')


def lookup(data):
    return {w["id"]: w for w in data["windows"]}


def cc_side(case, w):
    steps = w["cc"]["steps"][: w["cc"]["at"] + 1]
    tag = case["id"]
    ld = ladder(case["field"], case["cc_boards"], steps, case["hole"], tag)
    t = ld[-1]
    if t["piece"] != "T" or len(t["full"]) != 3 or not t["hole"] or [t["hole"][1], t["hole"][0]] not in [list(x) for x in t["cells"]]:
        _fail(f"{tag}: cold-clear's last step is not a T clearing 3 through the hole")
    return ld


def human_side(case):
    hu = case["human_verdict"]
    n = (hu["at"] if hu["at"] is not None else len(case["human"]) - 1) + 1
    return ladder(case["field"], case["human_boards"], case["human"][:n], case["hole"], case["id"] + " (player)")


def card(case, w, loc):
    case = dict(case, human_verdict=w["human"])
    label, rep, vid = loc.links(case["file"], case["round"], case["user"], case["lock"])
    hu = w["human"]
    at = hu["at"]
    _, rep_at, vid_at = loc.links(case["file"], case["round"], case["user"], case["lock"] + (at or 0))
    cl = cc_side(case, w)
    h1, f1 = frames(cl, ["C-Spin！清 3 行"])
    pl = human_side(case)
    last = pl[-1]
    why = hu["why"] or ""
    end = (f"擺 {last['piece']} 落個窿" if why.startswith("filled by") else
           "個窿冇咗" if why == "hole gone" else "14 粒都冇用到個窿")
    h2, f2 = frames(pl, [end])
    hold = chip(case["hold"]) if case["hold"] else "空"
    vlink = (f' · <a href="{html.escape(vid)}" target="_blank" rel="noopener">▶ 影片</a>' if vid else "")
    where = "垃圾行入面" if case["garbage"] else "自己疊嘅行入面"
    you = (f"佢第 {at + 1} 粒擺 {chip(last['piece'])} 落個窿" if why.startswith("filled by") else
           f"佢第 {at + 1} 粒之後個窿冇咗（清走或者蓋住）" if why == "hole gone" else "佢 14 粒都冇用個窿")
    return "\n".join([
        '      <div class="cm-card">',
        f'        <div class="cm-head"><strong>{html.escape(label)} 第 {case["lock"] + 1} 粒起</strong>'
        f'<span class="cm-tag">{where}</span>'
        f'<span><a href="{html.escape(rep)}">重播呢一刻</a>{vlink}</span></div>',
        f'        <p>手上 {chip(case["current"])}　hold {hold}　next {"".join(chip(p) for p in case["next"])}</p>',
        '        <div class="cm-boards">',
        f'          {anim(h1, f1, len(f1) - 2, f"cold-clear：第 {len(cl)} 粒打 C-Spin")}',
        f'          {anim(h2, f2, len(f2) - 2, "佢嘅擺法")}',
        '        </div>',
        f'        <p>紅框係個窿。{you}（<a href="{html.escape(rep_at)}">重播</a>）。</p>',
        '      </div>'])


SCRIPT = r"""  <script>
(function () {
  var COL = %s;
  function mount(fig) {
    var data = JSON.parse(fig.getAttribute("data-frames"));
    var grid = fig.querySelector(".cm-board"), cells = grid.children;
    var ctl = fig.querySelector(".cm-ctl"), out = fig.querySelector(".cm-step");
    var play = ctl.querySelector('[data-act="play"]');
    var orig = [];
    for (var i = 0; i < cells.length; i++) orig.push([cells[i].getAttribute("style"), cells[i].className]);
    var pos = -1, timer = null;
    function chip(p) {
      var s = document.createElement("span");
      s.className = "pm-p"; s.style.background = COL[p]; s.textContent = p; return s;
    }
    function draw() {
      out.textContent = "";
      if (pos < 0) {
        for (var i = 0; i < cells.length; i++) {
          var o = orig[i];
          if (o[0] === null) cells[i].removeAttribute("style"); else cells[i].setAttribute("style", o[0]);
          cells[i].className = o[1];
        }
        return;
      }
      var f = data.fr[pos], nw = {}, fl = {};
      f.n.forEach(function (k) { nw[k] = 1; });
      f.f.forEach(function (r) { fl[r] = 1; });
      for (var j = 0; j < cells.length; j++) {
        var ch = f.b.charAt(j);
        if (ch === ".") cells[j].removeAttribute("style"); else cells[j].style.background = COL[ch];
        cells[j].className = (nw[j] ? "cm-new" : "") + (fl[Math.floor(j / 10)] && ch !== "." ? " cm-full" : "")
          + (j === f.o ? " cm-hole" : "");
      }
      f.c.forEach(function (c) { out.appendChild(typeof c === "string" ? document.createTextNode(c) : chip(c.p)); });
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } play.textContent = pos < 0 ? "示範" : "播"; }
    function go(p) { pos = Math.max(-1, Math.min(data.fr.length - 1, p)); draw(); }
    function tick() { if (pos >= data.fr.length - 1) { stop(); return; } go(pos + 1); }
    ctl.addEventListener("click", function (e) {
      var a = e.target.getAttribute && e.target.getAttribute("data-act");
      if (!a) return;
      if (a === "play") {
        if (timer) { stop(); return; }
        if (pos >= data.fr.length - 1) go(-1);
        go(pos + 1); timer = setInterval(tick, 650); play.textContent = "停";
        return;
      }
      stop();
      if (a === "start") go(-1);
      else if (a === "back") go(pos - 1);
      else if (a === "fwd") go(pos + 1);
      stop();
    });
    ctl.hidden = false;
  }
  var figs = document.querySelectorAll("#cspin-miss .cm-anim");
  for (var i = 0; i < figs.length; i++) mount(figs[i]);
})();
  </script>""" % json.dumps(PIECE, sort_keys=True)


def _who(i, user):
    return f'<span class="cm-dot is-p{i + 1}"></span>{html.escape(user)}'


def player_block(i, user, t, cases, wins, loc):
    body = [f'    <h3>{_who(i, user)}</h3>',
            f'    <p>{t["windows"]} 個窿；cold-clear 喺 {t["cc"]} 個砌到 C-Spin，佢自己都砌到 {t["both"]} 個；'
            f'cold-clear 砌到而佢冇：<strong>{t["miss"]}</strong> 個。</p>']
    mine = [c for c in cases if c["user"] == user]
    if len(mine) != t["miss"]:
        _fail(f"{user}: {len(mine)} cases against a tally of {t['miss']}")
    if not mine:
        return body + ["    <p>呢晚冇一個。</p>"]
    body.append('    <div class="cm-grid">')
    body += [card(c, wins[c["id"]], loc) for c in mine]
    body.append('    </div>')
    return body


def method_note(data):
    r = data["rules"]
    return [
        '    <div class="method-note">',
        f'      <p><strong>同其他模擬器推導嘅幾節一樣，{QUARANTINE_MARKER}。</strong>'
        '呢節搵盤底嘅窿：一行得一格空、空格下面有嘢、上面通天。窿隔籬上一行再空一格，就差少少可以砌成 C-Spin 位'
        '（harddrop 嘅 C-Spin 圖）。'
        f'{WINDOW_MARKER}。由嗰塊板開始叫 cold-clear 行 {r["window_locks"]} 粒，'
        f'{SAME_MARKER}；個窿跟住清行同垃圾郁，第一粒擺落個窿嘅決定結果。'
        '冇 claim 編號、冇 ✓ 標記。</p>',
        f'      <p>下面每張卡都係 cold-clear 用 T 打 full T-spin 清 3 行（C-Spin）而佢冇嘅窿。'
        f'{READY_MARKER}。{BOT_MARKER}，佢有時用 hold 等一粒遲啲先嚟嘅 T；兩塊板都可以撳「示範」逐粒睇。</p>',
        '    </div>',
    ]


def section(data, players, loc):
    if data is None:
        return None
    if data.get("report_eligible") is not False:
        _fail("the artefact declares itself report-eligible")
    t = data["counts"]["by_player"]
    if sorted(t) != sorted(players):
        _fail(f"artefact players {sorted(t)} are not facts.json's {sorted(players)}")
    wins = lookup(data)
    for c in data["cases"]:
        if wins[c["id"]].get("ready_at_t"):
            _fail(f"{c['id']}: a C-Spin slot was ready at one of the player's T's")
    body = []
    for i, u in enumerate(players):
        body += player_block(i, u, t[u], data["cases"], wins, loc)
    out = [
        '<section id="cspin-miss">',
        CSS,
        '  <div class="wrap-wide">',
        '    <div class="eyebrow">模擬器同 bot 推導 · 唔屬於信任鏈</div>',
        f'    <h2 class="section-title">{TITLE}</h2>',
        '',
        *method_note(data),
        '',
        *body,
        '  </div>',
        SCRIPT,
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
