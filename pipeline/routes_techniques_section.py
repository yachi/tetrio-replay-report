"""定式路線同中盤手法 — the night's opener routes and mid-game techniques, early in the report.

    python3 -m pipeline.build_report sessions/<date>/report      # renders it with every other region
    python3 -m pipeline.check_routes_techniques sessions/<date>/report [--selftest]

The opener route pages (`docs/<opener>.html`) and the mid-game technique pages (`docs/<technique>.html`)
are corpus-wide. This section reads the same corpus artefacts (`analysis/<x>-facts.json`, the lists in
`pipeline.sites`) and prints ONE night's slice of them, right after 數據對決, so the report's own
analysis and the tagged 建議 items (`coaching.py`'s `sim_recs`) can point at them.

QUARANTINE. Simulator output, exactly like the four sections below the trust chain: one engine, no
second implementation, so no claim ids, no ✓ and no `data-claim` anywhere in the region. It sits ABOVE
the trust chain's 關鍵時刻 / 全場之最 / 建議 only because the 建議 items that cite it need something
earlier in the page to point at; its eyebrow, title and the `REQUIRED` sentences say which tier it is,
and `check_routes_techniques` fails the build if one goes missing.

WHAT EACH CELL COUNTS.
* A route row counts this night's rounds whose board matched that page's bag-1 drawing (the route
  artefact's cases), then how many of those reached bag 2, bag 3 or later, and a drawn Perfect Clear —
  each only where the stage is inside the round's verified prefix, the rule `replay_labels` labels by.
  The denominator is the night's rounds, which every player plays.
* A technique row counts the hits of one variant. The denominator is the night's scored T-spin
  Doubles (`sim/opener-facts.json` `stmb_cave.players[].tspin_doubles_scored`, the loop the technique
  tests hold their own scored count to); a TSS variant has no per-night scored count anywhere, so the
  cell says so instead of inventing one. The second line is the follow-up the page draws (the second
  T-spin, or 欄干 / 階段's Tetris into the re-opened well), how many fired, the reasons the rest did
  not, and opener against mid-game.
* The per-match strip lists what matched in each match; the winner's cell is underlined.

No win rate is printed: per night an opener or technique has a handful of rounds, the 全消 section's
rule about denominators.

Every figure is an integer count read off the artefacts; `figures()` is the set the region prints,
which is what the tagged 建議 items' numbers are checked against.
"""
import html
import json
import os
import re

from pipeline import region

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "routes-techniques"
EYEBROW = "模擬器推導 · 唔屬於信任鏈"
TITLE = "定式路線同中盤手法（未經證明）"

# The licences for the tables. Deleting one is what `check_routes_techniques --selftest` plants.
REQUIRED = (
    "冇 claim 編號、冇 ✓ 標記",
    "<strong>冇對到唔代表冇打過</strong>",
    "<strong>stick spin 同 SDPC Spin 第一巡係同一個板</strong>",
    "<strong>呢節唔會報「打咗某個定式嗰啲局贏幾多成」</strong>",
)

SHORT = {"迷走砲": "迷走", "はちみつ砲": "はちみつ", "山岳積み2號": "山岳2", "山岳積み2号": "山岳2",
         "stick spin（SDパフェ）": "stick", "ガムシロ積み": "ガムシロ", "SDPC Spin": "SDPC"}

# Each follow-up reason the technique artefacts emit, in the cell's words. An unknown reason is a
# build error: a new code must be worded here, never printed raw.
REASON = {
    "slot_filled_before_t": "個位俾其他棋填咗",
    "next_t_elsewhere": "下一粒 T 落咗第二度",
    "round_ended": "局完咗",
    "t_in_slot_not_tsd": "T 入咗位但唔係 TSD",
    "well_filled_not_i": "條井俾 I 以外嘅棋填咗",
    "i_in_well_not_quad": "I 入咗井但唔係 Tetris",
    "well_covered": "條井俾棋蓋住咗",
    "past_verified": "出咗可核範圍",
    "slot_off_board": "個位出咗界",
    "rowmap_unverified": "對唔返行",
}

STYLE = """  <style>
    /* Scoped under the section id with an rs- prefix: a generated section's <style> lands in the
       body and beats the report's own stylesheet at equal specificity. */
    #routes-techniques h3 { margin: 2.2rem 0 .1rem; font-size: 1.05rem; }
    #routes-techniques .rs-sub { font-size: .78rem; opacity: .75; }
    #routes-techniques .rs-zero { opacity: .45; }
    #routes-techniques .rs-chip { display: inline-block; font-size: .72rem; padding: .05rem .35rem;
      margin: .1rem; border-radius: .3rem; white-space: nowrap; }
    #routes-techniques .rs-o { background: color-mix(in srgb, var(--p1) 22%, transparent); }
    #routes-techniques .rs-t { background: color-mix(in srgb, var(--p2) 22%, transparent); }
    #routes-techniques td.rs-won { box-shadow: inset 0 -3px 0 currentColor; }
  </style>"""


DASH = '<span class="rs-zero">—</span>'


def _need(cond, msg):
    if not cond:
        raise SystemExit(f"routes_techniques_section: {msg}")


def session_of(report_dir):
    """The night a report directory belongs to, or None when it is not `sessions/<date>/report`
    (a filtered subset carries no sim/ directory and is not in any corpus artefact)."""
    d = os.path.dirname(os.path.abspath(report_dir))
    if os.path.basename(os.path.dirname(d)) != "sessions":
        return None
    if not os.path.exists(os.path.join(d, "sim", "opener-facts.json")):
        return None
    return os.path.basename(d)


def load(report_dir, repo=REPO):
    """Everything the section reads, or None for a report that has no such section."""
    session = session_of(report_dir)
    if session is None:
        return None
    from pipeline import replay_labels
    from pipeline.sites import TECHNIQUE_SITES
    routes, techs = replay_labels.load_sources(repo)
    for s in routes + techs:
        _need(session in s.sessions, f"{s.rel} does not cover {session}: re-emit it")
    with open(os.path.join(repo, "sessions", session, "sim", "opener-facts.json"), encoding="utf-8") as fh:
        of = json.load(fh)
    _need(of.get("report_eligible") is False, "sim/opener-facts.json must declare report_eligible: false")
    sites = {s.OVERVIEW: s for s in TECHNIQUE_SITES}
    for s in sites.values():
        s._repo = repo
    return {"session": session, "routes": routes, "techs": techs, "sites": sites,
            "tsd": {p["user"]: p["tspin_doubles_scored"] for p in of["stmb_cave"]["players"]}}


def _depth(src, c):
    """The deepest bag a route case reached inside its verified prefix, and whether its drawn Perfect
    Clear is verified. The stage rule `replay_labels` labels by."""
    v, best = c["verified_to"], 0
    if c["bag1"]["lock"] - 1 <= v:
        best = 1
    b2 = c.get("bag2")
    if b2 and b2.get("node") and b2["lock"] <= v:
        best = max(best, src.nodes[b2["node"]]["bag"])
    for s in c["snapshots"]:
        if s["verified"]:
            best = max(best, src.nodes[s["node"]]["bag"])
    pc = bool(c.get("pc") and c["pc"].get("node") and c["pc"]["verified"])
    return best, pc


def _variant_name(t, vid, var):
    if len(t.variants) == 1:
        return t.name
    if var.get("well"):
        # 基本的なドネイト: one window per hole distance from the T's arm
        return f"{t.name}（窿離 T {var['well']['offset']} 欄）"
    spins = {v["spin"] for v in t.variants.values()}
    if len(spins) > 1:
        return f"{t.name}（{var['spin']}）"
    return f"{t.name}（{'harddrop 第二型' if vid == 'uncut' else '基本型'}）"


def compute(facts, data):
    """The night's figures as plain data: per route and per technique variant, per player."""
    S, players = data["session"], list(facts["players"])
    nrounds = sum(len(m["rounds"]) for m in facts["matches"])
    strip = {}

    def tag(m, p, kind, x):
        lst = strip.setdefault((m, p), [])
        if (kind, x) not in lst:
            lst.append((kind, x))

    routes = []
    for r in data["routes"]:
        row = {"name": r.name, "href": r.href, "cells": {}}
        for p in players:
            mine = [c for c in r.art["cases"] if c["session"] == S and c["player"] == p]
            if not mine:
                row["cells"][p] = None
                continue
            reach, pcs = [0, 0, 0], 0
            for c in mine:
                d, pc = _depth(r, c)
                for k in range(3):
                    reach[k] += d >= k + 1
                pcs += pc
                tag(c["match"], p, "o", SHORT.get(r.name, r.name))
            first = min(mine, key=lambda c: (c["match"], c["round"]))
            row["cells"][p] = {"cases": len(mine), "reach": reach, "pc": pcs,
                               "first": f"m{first['match']}r{first['round']}"}
        routes.append(row)

    techs = []
    for t in data["techs"]:
        site = data["sites"][t.href]
        hs = [h for h in t.art["hits"] if h["session"] == S]
        for vid, var in t.variants.items():
            row = {"name": _variant_name(t, vid, var), "short": t.name, "href": t.href,
                   "spin": var["spin"], "payoff": bool(var.get("payoff")), "cells": {}}
            for p in players:
                mine = [h for h in hs if h["variant"] == vid and h["player"] == p]
                den = data["tsd"][p] if var["spin"] == "TSD" else None
                # A technique whose artefact carries `qualify` (社畜トレイン) counts only the hits that pass
                # its build rules; the rest are the shape alone, printed beside the cell and never as hits.
                shape_only = None
                if t.art.get("qualify"):
                    shape_only = sum(1 for h in mine if not h["qualifies"])
                    mine = [h for h in mine if h["qualifies"]]
                if not mine:
                    row["cells"][p] = {"hits": 0, "den": den, "shape_only": shape_only}
                    continue
                reasons = {}
                for h in mine:
                    fu = h.get("followup") or {}
                    if not fu.get("fired"):
                        rs = fu.get("reason")
                        _need(rs in REASON, f"{t.rel}: follow-up reason {rs!r} has no wording")
                        reasons[rs] = reasons.get(rs, 0) + 1
                    tag(h["match"], p, "t", t.name)
                first = min(mine, key=lambda h: (h["match"], h["round"], h["lock"]))
                op = sum(1 for h in mine if h["in_opener"])
                row["cells"][p] = {
                    "hits": len(mine), "den": den,
                    "fired": len(mine) - sum(reasons.values()), "reasons": reasons,
                    "opener": op, "mid": len(mine) - op,
                    "shape_only": shape_only,
                    "first": f"m{first['match']}r{first['round']}", "href": site.replay_href(first)}
            techs.append(row)

    return {"session": S, "players": players, "nrounds": nrounds, "routes": routes, "techs": techs,
            "strip": strip, "nmatch": len(facts["matches"]),
            "winners": [m.get("winner") for m in facts["matches"]]}


def _route_cell(c, nrounds, session):
    if c is None:
        return f'<td class="mono rs-zero">0 / {nrounds} 局</td>'
    parts = [f"第一巡 <b>{c['reach'][0]}</b>"]
    if c["reach"][1]:
        parts.append(f"第二巡 <b>{c['reach'][1]}</b>")
    if c["reach"][2]:
        parts.append(f"第三巡或之後 <b>{c['reach'][2]}</b>")
    if c["pc"]:
        parts.append(f"全消 <b>{c['pc']}</b>")
    href = html.escape(f"{session}-replay.html#{c['first']}")
    return (f'<td class="mono"><b>{c["cases"]}</b> / {nrounds} 局<br>'
            f'<span class="rs-sub">{" → ".join(parts)}</span><br>'
            f'<a class="rs-sub" href="{href}">睇第一局（{c["first"]}）</a></td>')


def _tech_cell(c, spin, payoff):
    den = (f" / {c['den']} 個 TSD" if c["den"] is not None
           else f"（{spin}，今晚冇可核 {spin} 總數）")
    shape = (f"<br><span class=\"rs-sub\">另外 {c['shape_only']} 次個形對到但唔算砌出嚟"
             f"（唔係完整方塊、有垃圾、同另一個手法重疊或者係 DPC，規則見手法頁）</span>" if c.get("shape_only") else "")
    if not c["hits"]:
        return f'<td class="mono rs-zero">0{den}{shape}</td>'
    follow = "Tetris" if payoff else "第二個 T-spin"
    sub = f"接到 {follow} {c['fired']} 次 · 開局 {c['opener']} · 中盤 {c['mid']}"
    miss = ""
    if c["reasons"]:
        miss = ("<br><span class=\"rs-sub\">冇接到：" + " · ".join(
            f"{REASON[k]} {n}" for k, n in sorted(c["reasons"].items(), key=lambda kv: (-kv[1], kv[0])))
            + "</span>")
    href = html.escape(c["href"])
    return (f'<td class="mono"><b>{c["hits"]}</b>{den}<br><span class="rs-sub">{sub}</span>{miss}{shape}<br>'
            f'<a class="rs-sub" href="{href}">睇第一次（{c["first"]}，落 T 之前）</a></td>')


def section(d):
    e = html.escape
    pl = d["players"]
    head = "".join(f"<th>{e(p)}</th>" for p in pl)
    route_rows = "".join(
        f'<tr><td><a href="{e(r["href"])}">{e(r["name"])}</a></td>'
        + "".join(_route_cell(r["cells"][p], d["nrounds"], d["session"]) for p in pl) + "</tr>"
        for r in d["routes"])
    tech_rows = "".join(
        f'<tr><td><a href="{e(t["href"])}">{e(t["name"])}</a></td>'
        + "".join(_tech_cell(t["cells"][p], t["spin"], t["payoff"]) for p in pl) + "</tr>"
        for t in d["techs"])
    strip_rows = []
    for p in pl:
        tds = []
        for mi in range(1, d["nmatch"] + 1):
            tags = d["strip"].get((mi, p), [])
            inner = "".join(f'<span class="rs-chip rs-o">{e(x)}</span>' for k, x in tags if k == "o")
            inner += "".join(f'<span class="rs-chip rs-t">{e(x)}</span>' for k, x in tags if k == "t")
            won = ' class="rs-won"' if d["winners"][mi - 1] == p else ""
            tds.append(f"<td{won}>{inner or DASH}</td>")
        strip_rows.append(f"<tr><th>{e(p)}</th>{''.join(tds)}</tr>")
    mhead = "".join(f"<th>第 {i} 場</th>" for i in range(1, d["nmatch"] + 1))
    r = REQUIRED
    return f"""<section id="routes-techniques">
{STYLE}
  <div class="wrap-wide">
    <div class="eyebrow">{EYEBROW}</div>
    <h2 class="section-title">{TITLE}</h2>
    <div class="method-note">
      <p>呢節嘅數同下面 C-Spin 同 DT 砲一樣，嚟自<strong>一個 replay 模擬器</strong>，得一份實作，所以{r[0]}。數字嚟自<a href="index.html">定式路線頁同中盤手法頁</a>嗰批 artefact，淨係計可核範圍入面嘅板。下面「俾兩位嘅建議」入面標住「未經證明」嘅幾條，就係用呢節嘅數寫嘅。</p>
      <p><strong>對到</strong>係指個板逐格對得上嗰頁畫嘅圖，或者中盤手法個窗口全中；{r[1]}——砌法同圖差一兩格、或者可核範圍去唔到咁遠，都會冇記錄。</p>
    </div>

    <h3>一 · 開局路線</h3>
    <div class="method-note"><p>每格係嗰位玩家今晚有幾多局個開局對到嗰頁第一巡嘅圖（分母係今晚嘅局數），跟住有幾多局喺可核範圍入面行到第二巡、第三巡或之後，或者打出嗰頁畫嘅全消。{r[2]}，所以兩行可以係同一批局，唔可以加埋一齊。</p></div>
    <div class="scroll-x"><table class="appendix-table">
      <thead><tr><th>定式</th>{head}</tr></thead>
      <tbody>{route_rows}</tbody>
    </table></div>

    <h3>二 · 中盤手法</h3>
    <div class="method-note"><p>每格係嗰位玩家今晚有幾多個 T-spin 落之前個形對到嗰個手法，分母係今晚可核嘅 TSD 總數（TSS 嘅形冇每晚嘅總數，就照講）。下面一行係有幾多次接到嗰頁畫嘅下一步（第二個 T-spin，或者欄干同階段嘅 Tetris）、冇接到嘅原因，同埋喺開局（頭 22 手）定中盤。連結直接開去重播頁、落嗰粒 T 之前嗰一刻。</p></div>
    <div class="scroll-x"><table class="appendix-table">
      <thead><tr><th>手法</th>{head}</tr></thead>
      <tbody>{tech_rows}</tbody>
    </table></div>

    <h3>三 · 逐場</h3>
    <div class="method-note"><p>每格係嗰場出現過嘅定式（<span class="rs-chip rs-o">開局</span>）同手法（<span class="rs-chip rs-t">中盤</span>）；底線係嗰場贏咗。「—」係冇對到，唔係冇打。</p></div>
    <div class="scroll-x"><table class="appendix-table">
      <thead><tr><th></th>{mhead}</tr></thead>
      <tbody>{''.join(strip_rows)}</tbody>
    </table></div>
    <div class="method-note"><p>{r[3]}：每晚每個定式同手法得幾局到十幾局，百分比睇落會比啲數撐得住嘅自信好多，同全消嗰節唔肯報率係同一個規矩。</p></div>
  </div>
</section>"""


def build(facts, report_dir, repo=REPO):
    data = load(report_dir, repo)
    if data is None:
        return None
    return section(compute(facts, data))


_TAG = re.compile(r"<[^>]+>")
_NUM = re.compile(r"\d+")


def visible(text):
    return html.unescape(_TAG.sub(" ", text))


def numbers(text):
    """Every Arabic-digit run in the visible text."""
    return set(_NUM.findall(visible(text)))


def figures(body):
    """The figures a rendered region prints — the pool the tagged 建議 items are checked against."""
    return numbers(body)


def region_body(doc):
    start, end = region.markers(NAME, "pipeline/build_report.py")
    if start not in doc:
        return None
    i = doc.index(start) + len(start)
    return doc[i:doc.index(end, i)]
