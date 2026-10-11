"""迷走砲 全路線 — the Stray Cannon route pages: one overview plus one replay page per bag-2 node.

    python3 -m pipeline.stray_cannon_page --out-dir /tmp/sc   # render every page into a directory
    python3 -m pipeline.stray_cannon_page --selftest          # the audit's mutants

Inputs, all committed: `pipeline/openers/meisou-routes.json` (the shiwehi.com page, transcribed and
gated by `extract_meisou_routes`), `analysis/stray-cannon-facts.json` (which corpus round reached
which route node, written by `pipeline/sim/emit-stray-cannon-facts.ts`), and each session's
`sim/replay-facts.json` + `report/facts.json` (the replay payloads, through
`replay_section.round_payload` — the same function the per-session replay page calls). Pure Python,
so `bin/build-docs` can render it in the `docs` job, which has no bun.

PAGES. `stray-cannon.html` draws every route node with its count and indexes every case; it embeds
no player. `stray-cannon-<slug>.html` holds every case whose bag 2 went to one node (or, for
`bag1-only`, to none), each with the shared `replay_player.js`, mounted one at a time by
`stray_cannon_page.js`. No name ends in `-replay.html`: `bin/build-docs` owns that suffix.

QUARANTINE. Simulator output, the same tier as the replay pages: no claim ids, no ✓, no
`data-claim`, and the artefact must say `report_eligible: false`. The audit reuses
`replay_page.audit_quarantine` / `audit_player` — one copy of each rule — and adds this page's own
completeness rules: every route node and outcome appears with a count or a reason it has none, every
case is embedded exactly once on a node page and indexed exactly once on the overview, the only `%`
are inside quoted source text, and 「hold」 appears only where the lock-7 predicate earns it.

FIGURES. Counts only, rendered from the artefacts, always as 「N / M」 with the denominator; the
source page's percentages appear only inside its quoted text. No rate is computed here, so no
rounding rule is exercised.
"""
import argparse
import html
import json
import os
import re
import sys

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline.claims.build_claims import SIMPLIFIED

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ROUTES_REL = os.path.join("pipeline", "openers", "meisou-routes.json")
FACTS_REL = os.path.join("analysis", "stray-cannon-facts.json")
PROSE_PATH = os.path.join(HERE, "stray_cannon_prose.json")
PAGE_JS = os.path.join(HERE, "stray_cannon_page.js")

OVERVIEW = "stray-cannon.html"
DATA_ID = "scp-data"
TEMPLATE_ID = "scp-player-tpl"
# (slug, bag-2 node or None). A case goes to the page of its bag-2 node; no bag-2 match -> bag1-only.
NODE_PAGES = (("bag1-only", None), ("ideal", "2.ideal"), ("normal-os", "2.normal_OS"),
              ("normal-so", "2.normal_SO"), ("i-early", "2.i_early"))
# Fields every round payload carries identically; inlined once per page. `session` is NOT one:
# a page holds rounds from every session, so it stays in each payload.
SHARED = ("shapes", "width", "rows", "visible", "next", "flag_words")
BAG2_ORDER = ("2.ideal", "2.normal_OS", "2.normal_SO", "2.i_early", "2.z_left")
BAG1_ORDER = ("bag1.z_right", "bag1.z_left", "bag1.z_hold", "bag1.z_placed_elsewhere")

CELL = 14
PIECE_CLASS = {"i": "i", "o": "o", "t": "t", "s": "s", "z": "z", "j": "j", "l": "l",
               "c": "c", "U": "u", "Z": "zz", "p": "p"}

# visible-text extraction for the % and 「hold」 rules
_SCRIPT = re.compile(r"<script\b.*?</script>|<style\b.*?</style>|<template\b.*?</template>", re.S)
_SRC_QUOTE = re.compile(r'<q class="scp-src">.*?</q>', re.S)
_HOLD_SPAN = re.compile(r'<span class="scp-hold" data-node="bag1\.z_hold">[^<]*</span>')
_TAG = re.compile(r"<[^>]+>")
_HOLD = re.compile(r"hold", re.I)
_NODE_BLOCK = re.compile(r'data-node="([^"]+)" data-status="([a-z_]+)"')
_CASE_ROW = re.compile(r'data-case="([^"]+)"')
_ISLAND = re.compile(r'<script type="application/json" id="' + DATA_ID + r'">(.*?)</script>', re.S)


def _need(cond, msg):
    if not cond:
        raise SystemExit(f"stray_cannon_page: {msg}")


def _no_simplified(text, where):
    bad = sorted(set(text) & SIMPLIFIED)
    _need(not bad, f"{where}: simplified glyph(s) {bad} — this report is traditional-character Cantonese")
    return text


def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def load_prose(path=PROSE_PATH):
    with open(path, encoding="utf-8") as fh:
        prose = json.load(fh)
    for s in _walk_strings(prose):
        _no_simplified(s, os.path.basename(path))
    return prose


PROSE = load_prose()
PS = PROSE["page_sentences"]
PAGE_SENTENCES = (PS["source"], PS["exact"], PS["bag3"], PS["bag1"], PS["mirror"], PS["our_reading"])
# The overview embeds no player, so the two sentences about the player's timeline are not its to carry.
OVERVIEW_REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, RS.HOLE_SENTENCE) + PAGE_SENTENCES
NODE_REQUIRED = RS.REQUIRED + PAGE_SENTENCES


# ---------------------------------------------------------------- inputs

def load_inputs(repo=REPO):
    """(routes, facts artefact, {session: (replay data, facts.json, opener-facts)})."""
    with open(os.path.join(repo, ROUTES_REL), encoding="utf-8") as fh:
        routes = json.load(fh)
    with open(os.path.join(repo, FACTS_REL), encoding="utf-8") as fh:
        art = json.load(fh)
    sessions = {}
    for s in art["sessions"]:
        sdir = os.path.join(repo, "sessions", s)
        data, facts = RP.load(sdir)
        _need(data is not None, f"{s} has no {RS.FACTS_REL}")
        with open(os.path.join(sdir, "sim", "opener-facts.json"), encoding="utf-8") as fh:
            opener = json.load(fh)
        sessions[s] = (data, facts, opener)
    return routes, art, sessions


def check_inputs(routes, art):
    _need(routes.get("schema") == "meisou-routes/1", f"unknown routes schema {routes.get('schema')!r}")
    _need(art.get("schema") == "stray-cannon-facts/1", f"unknown facts schema {art.get('schema')!r}")
    _need(art.get("report_eligible") is False,
          "stray-cannon-facts.json must declare report_eligible: false — simulator boards are not "
          "trust-chain data")
    route_ids = [n["id"] for n in routes["nodes"]]
    fact_ids = [n["id"] for n in art["nodes"]]
    _need(len(set(fact_ids)) == len(fact_ids), "duplicate node ids in the facts artefact")
    _need(set(fact_ids) == set(route_ids) | set(art["outcomes"]),
          "the facts artefact's nodes are not the routes' nodes plus its outcomes: "
          f"{sorted(set(fact_ids) ^ (set(route_ids) | set(art['outcomes'])))}")


def case_key(c):
    return f"{c['session']}-m{c['match']}r{c['round']}-{c['player']}"


def round_key(c):
    return f"{c['session']}-m{c['match']}r{c['round']}"


def page_of(c):
    b2 = (c.get("bag2") or {}).get("node")
    for slug, node in NODE_PAGES:
        if node == b2:
            return slug
    raise SystemExit(f"stray_cannon_page: {case_key(c)} went to {b2!r}, which has no page")


def group_of(c):
    """The node a case is listed under on its page: the off-page PC pseudo-node, else the deepest."""
    pc = c.get("pc")
    if pc and pc.get("off_page_under"):
        return pc["off_page_under"]
    return c["deepest"]


def start_lock(c):
    """The lock a case's replay opens after: its PC, else its deepest node's lock."""
    pc = c.get("pc")
    return pc["lock"] if pc else c["deepest_lock"]


def _pos_after(order, slot, lock):
    """Merged position just after player `slot`'s lock `lock` (0-based) — round_payload's `pos`."""
    seen = -1
    for n, s in enumerate(order):
        if s == str(slot):
            seen += 1
            if seen == lock:
                return n + 1
    raise SystemExit(f"stray_cannon_page: slot {slot} has no lock {lock}")


def _round_payload(sessions, c):
    data, facts, _op = sessions[c["session"]]
    RS.check_artefact(data)
    for mi, m in enumerate(facts["matches"]):
        if m["file"] != c["file"]:
            continue
        for ri, r in enumerate(m["rounds"]):
            if r["index"] == c["round_index0"]:
                pl = RS.round_payload(data, facts, mi, ri)
                _need(pl["match"] == c["match"] and pl["round"] == c["round"],
                      f"{case_key(c)}: facts.json puts it at m{pl['match']}r{pl['round']}")
                return pl
    raise SystemExit(f"stray_cannon_page: {case_key(c)} ({c['file']} round {c['round_index0']}) "
                     "is not in its session's facts.json")


# ---------------------------------------------------------------- words

def _esc(s):
    return html.escape(str(s))


def node_name(nid, routes_by_id):
    names = PROSE["names"]
    if nid in names:
        return names[nid]
    if nid.endswith(".other"):
        parent = nid[:-len(".other")]
        return names["other"].format(parent=node_name(parent, routes_by_id))
    n = routes_by_id.get(nid)
    _need(n is not None, f"no name for node {nid!r}")
    if "list" in n:
        return names["pc"].format(parent=node_name(n["parent"], routes_by_id), k=n["index"])
    raise SystemExit(f"stray_cannon_page: no Cantonese name for {nid!r} in the prose file")


def _condition_words(cond):
    if not cond:
        return ""
    if "all" in cond:
        return "，".join(f"{a} 早過 {b}" for a, b in (x["before"] for x in cond["all"]))
    if "early" in cond:
        return f"{cond['early']} 早（原頁冇講幾早先算）"
    if "bag1" in cond:
        return f"第一巡係「{PROSE['names'][cond['bag1']]}」"
    raise SystemExit(f"stray_cannon_page: unknown condition {cond!r}")


def _src(text):
    """Quoted source text: the ONLY place a % may appear."""
    return f'<q class="scp-src">{_esc(text)}</q>'


# ---------------------------------------------------------------- boards

def board_svg(rows, label):
    """A transcribed board as inline SVG (no src, no url): rows top->bottom, 10 columns."""
    h, w = len(rows), len(rows[0])
    out = [f'<svg class="scb" viewBox="0 0 {w * CELL} {h * CELL}" width="{w * CELL}" '
           f'height="{h * CELL}" role="img" aria-label="{_esc(label)}">'
           f'<rect class="scb-bg" x="0" y="0" width="{w * CELL}" height="{h * CELL}"/>']
    for y, row in enumerate(rows):
        _need(len(row) == w, f"{label}: ragged board")
        for x, ch in enumerate(row):
            if ch == "-":
                continue
            _need(ch in PIECE_CLASS, f"{label}: unknown cell {ch!r}")
            out.append(f'<rect class="scb-{PIECE_CLASS[ch]}" x="{x * CELL + 1}" y="{y * CELL + 1}" '
                       f'width="{CELL - 2}" height="{CELL - 2}"/>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- node status

def status_of(fn):
    """(status, words) for one facts node. Every node has exactly one."""
    if not fn["measured"]:
        why = fn["why"]
        kind = "unmatchable" if why.startswith("unmatchable") else why
        _need(kind in PROSE["status_words"], f"{fn['id']}: unknown reason {why!r}")
        words = PROSE["status_words"][kind]
        if kind == "unmatchable":
            words += "：" + PROSE["unmatchable_reasons"][fn["id"]]
        return kind, words
    if fn["cases"] == 0:
        return "empty", PROSE["empty_node"].format(m=fn["opportunities"])
    by = "、".join(f"{_esc(u)} {n}" for u, n in sorted(fn["cases_by_player"].items()))
    return "count", f"{fn['cases']} / {fn['opportunities']}（{by}）"


def node_block(nid, fn, routes_by_id, href=None, extra=""):
    """One route node, one line: name, status, board if transcribed. `data-node` + `data-status`
    are what the completeness audit reads."""
    st, words = status_of(fn)
    rn = routes_by_id.get(nid, {})
    name = node_name(nid, routes_by_id)
    if nid == "bag1.z_hold":
        title = f'<span class="scp-hold" data-node="bag1.z_hold">{_esc(PROSE["z_hold_heading"])}</span>'
    else:
        title = _esc(name)
    if href:
        title = f'<a href="{_esc(href)}">{title}</a>'
    bits = [f'<div class="scp-node" data-node="{_esc(nid)}" data-status="{st}">',
            f'<h4 class="scp-name">{title}</h4>']
    if rn.get("label_jp"):
        bits.append(f'<p class="scp-jp">原頁：{_src(rn["label_jp"])}</p>')
    if "rows" in rn:
        bits.append(board_svg(rn["rows"], name))
    if rn.get("listed_under"):
        bits.append(f'<p class="scp-tag">{_esc(PROSE["listed_under"][rn["listed_under"]])}</p>')
    if rn.get("condition"):
        bits.append(f'<p class="scp-cond">條件：{_esc(_condition_words(rn["condition"]))}；'
                    f'原文 {_src(rn["condition_verbatim"])}</p>')
    if rn.get("text_verbatim"):
        bits.append(f'<p class="scp-cond">原文 {_src(rn["text_verbatim"])}</p>')
    bits.append(f'<p class="scp-count">{words}</p>')
    if extra:
        bits.append(extra)
    bits.append("</div>")
    return "".join(bits)


# ---------------------------------------------------------------- page shell

PAGE_CSS = """
  .scp-top { display: flex; gap: 1rem; flex-wrap: wrap; padding: 14px 0 0; font-size: .85rem; font-family: var(--font-mono); }
  .scp-top a { color: var(--ink-secondary); }
  .scp-head { padding: 22px 0 6px; }
  .scp-src-line { font-size: .85rem; color: var(--ink-secondary); margin: 0; }
  .scp-sec { margin: 2rem 0 0; }
  .scp-sec > h2 { font-size: 1.25rem; margin: 0 0 .5rem; }
  .scp-sec h3 { font-size: 1rem; margin: 1.4rem 0 .4rem; }
  .scp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(12.5rem, 1fr)); gap: .8rem; }
  .scp-node { padding: .7rem; border: 1px solid var(--border); border-radius: 10px; background: var(--bg-raised); min-width: 0; }
  .scp-name { font-size: .92rem; margin: 0 0 .3rem; }
  .scp-name a { text-decoration: underline; }
  .scp-jp, .scp-tag, .scp-cond { font-size: .78rem; color: var(--ink-secondary); margin: .25rem 0; }
  .scp-count { font: 600 .85rem var(--font-mono); margin: .35rem 0 0; font-variant-numeric: tabular-nums; }
  .scp-node[data-status="empty"] .scp-count, .scp-node[data-status="image_only"] .scp-count,
  .scp-node[data-status="text_only"] .scp-count, .scp-node[data-status="unmatchable"] .scp-count { font-family: var(--font-cjk); font-weight: 400; color: var(--muted); }
  .scb { display: block; max-width: 100%; height: auto; margin: .3rem 0; }
  .scb-bg { fill: var(--bg-sunken); }
  .scb-i { fill: #3fb8c4; } .scb-o { fill: #d9b638; } .scb-t { fill: #9b5fd0; } .scb-s { fill: #4caf50; }
  .scb-z { fill: #d64f4a; } .scb-j { fill: #4a72d1; } .scb-l { fill: #e08a35; }
  .scb-c { fill: var(--muted); opacity: .55; }
  .scb-u { fill: none; stroke: #9b5fd0; stroke-width: 2; stroke-dasharray: 3 2; }
  .scb-zz { fill: #d64f4a; stroke: var(--ink); stroke-width: 1.5; }
  .scb-p { fill: none; stroke: var(--muted); stroke-width: 1.5; stroke-dasharray: 2 2; }
  .scp-quote { font-size: .85rem; color: var(--ink-secondary); }
  .scp-table { border-collapse: collapse; font-size: .82rem; margin: .4rem 0; font-variant-numeric: tabular-nums; }
  .scp-table th, .scp-table td { border: 1px solid var(--border); padding: .25rem .5rem; text-align: left; }
  .scp-table caption { caption-side: bottom; font-size: .78rem; color: var(--ink-secondary); text-align: left; padding-top: .3rem; }
  .scp-index-wrap { overflow-x: auto; }
  .scp-cases { list-style: none; padding: 0; margin: .4rem 0 0; display: flex; flex-wrap: wrap; gap: .35rem; }
  .scp-case { display: inline-block; font: .78rem var(--font-mono); padding: .25rem .5rem; border: 1px solid var(--border); border-radius: 6px; color: var(--ink-secondary); text-decoration: none; }
  .scp-case[aria-current="true"] { border-color: var(--ink); color: var(--ink); font-weight: 700; }
  .scp-case .scp-unv { color: var(--pending); }
  .scp-idle { font-size: .9rem; color: var(--muted); }
  .scp-idle[hidden] { display: none; }
  @media (max-width: 640px) { .scp-grid { grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); } }
"""


def _head(title, desc, users, with_player):
    css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), PAGE_CSS.strip("\n")]
    if with_player:
        css += [RS._color_css([{"user": u} for u in users]), RS.CSS.strip("\n")]
    return [
        "<!doctype html>",
        '<html lang="zh-HK">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_esc(title)}</title>",
        f'<meta name="description" content="{_esc(desc)}">',
        "<style>",
        "  " + "\n".join(css),
        "</style>",
        "</head>",
        "<body>",
        '<div class="wrap-wide">',
    ]


def _source_line(routes):
    src, terms = routes["source"], routes["terms"]
    return (f'  <p class="scp-src-line">來源：<a href="{_esc(src["url"])}">{_esc(src["title"])}'
            f'（shiwehi.com）</a>，原頁 {_esc(src["updated"])} 版，{_esc(src["fetched"])} 讀取；'
            f'<a href="{_esc(terms["url"])}">使用條款</a>（非商業用途，註明出處）。</p>')


def _method_note(include_player):
    lines = ['  <div class="method-note">',
             '    <p><strong>呢版唔屬於信任鏈。</strong>每個盤面都係<strong>一個 replay 模擬器</strong>'
             '（Triangle 引擎）重跑操作記錄推導出嚟，冇第二份獨立實作；邊一局對到邊一步亦係由佢推出嚟。'
             f'所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
    lines += [f"    <p>{s}</p>" for s in PAGE_SENTENCES]
    lines.append(f"    <p>{RS.HOLE_SENTENCE}</p>")
    if include_player:
        lines += [f"    <p>{RS.DROP_SENTENCE}</p>", f"    <p>{RS.BOUNDARY_SENTENCE}</p>",
                  '    <p>每一局都會核成局總數同 <code>facts.json</code> 夾唔夾；有一項唔夾，嗰局就會寫'
                  f'「{RS.FLAG_WORDS}」。</p>']
    lines.append("  </div>")
    return lines


def _island(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def _tail(island, js=()):
    out = ["  <footer><p>模擬器推導嘅路線分類同重播，唔屬於信任鏈；"
           "Dafny 證明嘅係戰報入面嘅 claim，唔係呢度嘅盤面。</p></footer>",
           "</div>",
           f'<script type="application/json" id="{DATA_ID}">{_island(island)}</script>']
    out += ["<script>\n" + j + "\n</script>" for j in js]
    out += ["</body>", "</html>", ""]
    return out


# ---------------------------------------------------------------- overview

def render_overview(routes, art, sessions, page_href):
    by_id = {n["id"]: n for n in routes["nodes"]}
    fnodes = {n["id"]: n for n in art["nodes"]}
    cases = sorted(art["cases"], key=lambda c: (c["session"], c["match"], c["round"], c["player"]))
    title = f"{PROSE['overview_title']}{RS.TITLE_MARK}"
    shown = set()

    def block(nid, href=None, extra=""):
        shown.add(nid)
        return "    " + node_block(nid, fnodes[nid], by_id, href, extra)

    out = _head(title, "迷走砲每條路線同 corpus 入面對到嘅局：模擬器推導，唔屬於信任鏈。", [], False)
    out += ['  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a></nav>',
            '  <header class="scp-head">',
            f'    <div class="eyebrow">{RS.EYEBROW}</div>',
            f'    <h1 class="section-title">{_esc(title)}</h1>',
            f'    <p>{_esc(PROSE["overview_lede"])}</p>',
            _source_line(routes),
            '  </header>']
    out += _method_note(False)
    mq = {q["id"]: q for q in routes["quotes"]}
    if "overview.max_damage" in mq:
        out.append(f'  <p class="scp-quote">原頁：{_src(mq["overview.max_damage"]["verbatim"])}</p>')
    out.append('  <div class="scp-grid">')
    for nid in ("overview.derivation_map", "overview.video"):
        out.append(block(nid))
    out.append("  </div>")

    # 基本形
    out += ['  <section class="scp-sec" id="basic"><h2>基本形</h2><div class="scp-grid">']
    for b in routes["basic_form"]:
        nm = node_name(b["same_as"], by_id)
        out.append(f'    <div class="scp-basic"><h4 class="scp-name">{_esc(nm)}</h4>'
                   f'{board_svg(b["rows"], nm)}</div>')
    out.append("  </div></section>")

    # 第一巡
    b1 = routes["bag1"]
    total = sum(fnodes[n]["cases"] for n in BAG1_ORDER)
    m6 = sum(1 for c in art["cases"] if c["bag1"]["matched_at_6"])
    table = 0
    for s, (_d, _f, op) in sessions.items():
        sc = [o for o in op["named_openers"]["openers"] if o["key"] == "stray_cannon"]
        _need(len(sc) == 1, f"{s}: opener-facts.json has {len(sc)} stray_cannon entries")
        table += sum(p["exact"] for p in sc[0]["players"])
    out += ['  <section class="scp-sec" id="bag1"><h2>第一巡</h2>',
            f'  <p class="scp-quote">原頁：{_src(b1["requires_verbatim"])} {_src(b1["z_note_verbatim"])}</p>',
            '  <div class="scp-grid">']
    for nid in BAG1_ORDER:
        out.append(block(nid, f"stray-cannon-bag1-only.html#g-{nid}" if fnodes[nid]["cases"] else None))
    out.append("  </div>")
    extra = sum(1 for c in art["cases"] if not c["bag1"]["matched_at_6"])
    _need(total == m6 + extra, f"bag-1 nodes hold {total} cases, matched_at_6 splits them {m6} + {extra}")
    out.append("  <p>" + _esc(PROSE["matched_at_6"].format(
        table=table, m6=m6, total=total, extra=extra,
        same=PROSE["matched_at_6_same"] if table == m6 else PROSE["matched_at_6_differ"])) + "</p>")
    out.append("  </section>")

    # 第二巡
    slug_of = {n: s for s, n in NODE_PAGES}
    out += ['  <section class="scp-sec" id="bag2"><h2>第二巡</h2><div class="scp-grid">']
    for nid in BAG2_ORDER:
        href = f"stray-cannon-{slug_of[nid]}.html" if nid in slug_of and fnodes[nid]["cases"] else None
        out.append(block(nid, href))
    out.append("  </div>")
    cond = art["conditions"]
    cols = [n for n in BAG2_ORDER if any(n in v for v in cond.values())]
    out += ['  <table class="scp-table"><caption>' + _esc(PROSE["conditions_caption"]) + "</caption>",
            "    <tr><th>實際砌咗</th>" + "".join(f"<th>{_esc(node_name(c, by_id))}</th>" for c in cols)
            + f"<th>{_esc(PROSE['conditions_none'])}</th></tr>"]
    for built in BAG2_ORDER:
        n_built = fnodes[built]["cases"]
        if not n_built:
            continue
        row = cond.get(built, {})
        rest = n_built - sum(row.values())
        _need(rest >= 0, f"{built}: condition tallies exceed its cases")
        out.append(f"    <tr><th>{_esc(node_name(built, by_id))}（{n_built}）</th>"
                   + "".join(f"<td>{row.get(c, 0)}</td>" for c in cols) + f"<td>{rest}</td></tr>")
    out.append("  </table>")
    mism = art["lists"]["bag2_handedness_mismatch"]
    if mism:
        out.append(f"  <h3>{_esc(PROSE['handedness_heading'])}</h3><ul>"
                   + "".join(f"<li>{_esc(x)}</li>" for x in mism) + "</ul>")
    out.append("  </section>")

    # 第三巡
    out += ['  <section class="scp-sec" id="bag3"><h2>第三巡</h2>']
    lists = {l["id"]: l for l in routes["lists"]}
    for parent in BAG2_ORDER:
        kids = [n["id"] for n in routes["nodes"] if n.get("parent") == parent
                or (n.get("parent") or "").startswith(parent + ".")]
        if not kids:
            continue
        href = f"stray-cannon-{slug_of[parent]}.html" if parent in slug_of and fnodes[parent]["cases"] else None
        out.append(f"  <h3>{_esc(node_name(parent, by_id))}</h3>")
        li = lists.get(parent + ".pc")
        if li and (parent + ".pc") in mq:
            out.append(f'  <p class="scp-quote">原頁：{_src(mq[parent + ".pc"]["verbatim"])}</p>')
        out.append('  <div class="scp-grid">')
        for k in kids:
            out.append(block(k, f"{href}#g-{k}" if href and fnodes[k].get("cases") else None))
        out.append("  </div>")
    out.append(f"  <h3>{_esc(PROSE['off_page_heading'])}</h3>")
    out.append(f"  <p>{_esc(PROSE['off_page_note'])}</p><ul>")
    for c in cases:
        if c.get("pc") and c["pc"].get("off_page_under"):
            g = c["pc"]["off_page_under"]
            out.append(f'    <li><a href="stray-cannon-{page_of(c)}.html#{round_key(c)}@p{{POS:{case_key(c)}}}">'
                       f'{_esc(c["session"])} m{c["match"]}r{c["round"]} · {_esc(c["player"])}</a>'
                       f'：{_esc(node_name(g, by_id))}</li>')
    out.append("  </ul>")
    out.append(f"  <h3>{_esc(PROSE['discrepancy_heading'])}</h3><ul>")
    for d in routes["known_discrepancies"]:
        words = PROSE["discrepancies"][d["id"]]
        li = lists.get(d["id"].split(":")[0])
        if li:
            words = words.format(stated=li["stated_pattern_count"], drawn=li["drawn"],
                                 shown=li["shown"], rest=li["rest_stated"])
        out.append(f"    <li>{_esc(words)}</li>")
    out.append("  </ul></section>")

    # 個案索引
    out += [f'  <section class="scp-sec" id="cases"><h2>{_esc(PROSE["index_heading"])}</h2>',
            f'  <p>{_esc(PROSE["index_note"])}</p>',
            '  <div class="scp-index-wrap"><table class="scp-table scp-index">',
            "    <tr><th>日子</th><th>場·局</th><th>玩家</th><th>左右</th><th>去到邊一步</th><th>核對</th></tr>"]
    for c in cases:
        g = group_of(c)
        ver = "已核" if c["verified"] else PROSE["unverified"]
        out.append(f'    <tr data-case="{_esc(case_key(c))}"><td>{_esc(c["session"])}</td>'
                   f'<td>m{c["match"]}r{c["round"]}</td><td>{_esc(c["player"])}</td>'
                   f'<td>{"反轉" if c["bag1"]["mirrored"] else "原樣"}</td>'
                   f'<td><a href="stray-cannon-{page_of(c)}.html#{round_key(c)}@p{{POS:{case_key(c)}}}">'
                   f'{_esc(node_name(g, by_id))}</a></td><td>{_esc(ver)}</td></tr>')
    out.append("  </table></div></section>")

    missing = set(fnodes) - shown
    _need(not missing, f"the overview does not place node(s) {sorted(missing)}")
    island = {"schema": "stray-cannon-page/1", "report_eligible": False,
              "nodes": {n["id"]: {k: n[k] for k in ("cases", "opportunities") if k in n}
                        for n in art["nodes"]}}
    out += _tail(island)
    page = "\n".join(out)
    return re.sub(r"\{POS:([^}]+)\}", lambda m: str(page_href[m.group(1)]), page)


# ---------------------------------------------------------------- node pages

def _subtree(slug, node, art):
    if node is None:
        return [n for n in BAG1_ORDER]
    return [node] + [n["id"] for n in art["nodes"] if n["id"].startswith(node + ".")]


def render_node_page(slug, node, routes, art, sessions, payloads):
    """One bag-2 node's page: every case under it, each with its replay. Returns (page, {case: pos})."""
    by_id = {n["id"]: n for n in routes["nodes"]}
    fnodes = {n["id"]: n for n in art["nodes"]}
    mine = sorted((c for c in art["cases"] if page_of(c) == slug),
                  key=lambda c: (c["session"], c["match"], c["round"], c["player"]))
    _need(mine, f"{slug}: no cases")
    name = node_name(node, by_id) if node else "第一巡之後冇對到第二巡"
    title = f"迷走砲 {name}{RS.TITLE_MARK}"

    shared, rounds, case_rows, pos_of = None, {}, [], {}
    users = None
    for c in mine:
        rk = round_key(c)
        pl = payloads[rk]
        if shared is None:
            shared = {k: pl[k] for k in SHARED}
        _need(all(pl[k] == shared[k] for k in SHARED), f"{rk}: a shared field differs")
        u = [p["user"] for p in pl["players"]]
        users = users or u
        _need(u == users, f"{rk}: player order {u} differs from {users} — slot colours would swap")
        if rk not in rounds:
            lean = {k: v for k, v in pl.items() if k not in SHARED}
            lean["label"] = rk
            lean["notes"] = [RS._player_note(p, esc=str) for p in pl["players"]]
            rounds[rk] = lean
        slot = u.index(c["player"])
        pos = _pos_after(pl["order"], slot, start_lock(c))
        pos_of[case_key(c)] = pos
        case_rows.append({"case": case_key(c), "round": rk, "player": c["player"], "pos": pos,
                          "group": group_of(c)})

    groups = {}
    for c, row in zip(mine, case_rows):
        groups.setdefault(row["group"], []).append((c, row))
    order = _subtree(slug, node, art)
    order += sorted(g for g in groups if g not in order)
    for g in groups:
        _need(g in order, f"{slug}: group {g!r} has no place on the page")

    with open(PAGE_JS, encoding="utf-8") as fh:
        page_js = fh.read().rstrip()
    _need("</script" not in page_js.lower(), "stray_cannon_page.js may not contain a closing script tag")
    out = _head(title, f"迷走砲 {name}：每個個案嘅模擬重播，模擬器推導，唔屬於信任鏈。", users, True)
    out += ['  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a>'
            f'<a href="{OVERVIEW}">迷走砲 全路線</a></nav>',
            '  <header class="scp-head">',
            f'    <div class="eyebrow">{RS.EYEBROW}</div>',
            f'    <h1 class="section-title">{_esc(title)}</h1>',
            "    <p>" + _esc(PROSE["bag1_only_lede"] if node is None
                             else PROSE["node_page_lede"].format(name=name)) + "</p>",
            _source_line(routes),
            '  </header>']
    out += _method_note(True)
    out += [f'  <section id="{RS.SECTION_ID}" aria-labelledby="rpg-now">',
            '    <h2 class="rpg-now" id="rpg-now" aria-live="polite"></h2>',
            f'    <p class="scp-idle">{_esc(PROSE["idle"])}</p>',
            '    <p class="rpg-notes"></p>',
            f'    <p class="rpg-flag" hidden>{RS.FLAG_WORDS}</p>',
            f'    <p class="rpg-missing" hidden>{_esc(PROSE["missing"])}</p>',
            '    <noscript><p>重播要開 JavaScript 先用到。</p></noscript>',
            '    <div class="rpg-host"></div>',
            f'    <template id="{TEMPLATE_ID}">',
            *["  " + line for line in RS.player_box("", users)],
            '    </template>',
            '  </section>']
    for g in order:
        rows = groups.get(g, [])
        fn = fnodes.get(g)
        out.append(f'  <section class="scp-sec" id="g-{_esc(g)}">')
        if fn is not None:
            out.append("    " + node_block(g, fn, by_id))
        else:
            out.append(f'    <div class="scp-node" data-node="{_esc(g)}" data-status="count">'
                       f'<h4 class="scp-name">{_esc(node_name(g, by_id))}</h4>'
                       f'<p class="scp-count">{len(rows)}</p></div>')
        if rows:
            out.append(f"    <h3>停喺呢一步嘅個案（{len(rows)}）</h3>")
            out.append('    <ul class="scp-cases">')
            for c, row in rows:
                tag = " · 左右反轉" if c["bag1"]["mirrored"] else ""
                unv = (f' · <span class="scp-unv">{_esc(PROSE["unverified"])}</span>'
                       if not c["verified"] else "")
                out.append(f'      <li data-case="{_esc(row["case"])}"><a class="scp-case" '
                           f'href="#{row["round"]}@p{row["pos"]}" data-round="{row["round"]}">'
                           f'{_esc(c["session"])} m{c["match"]}r{c["round"]} · {_esc(c["player"])}'
                           f'{tag}{unv}</a></li>')
            out.append("    </ul>")
        out.append("  </section>")
    island = {"shared": shared, "rounds": rounds, "cases": case_rows}
    out += _tail(island, (RS.player_js(), page_js))
    return "\n".join(out), pos_of


# ---------------------------------------------------------------- render all

def render_all(repo=REPO, inputs=None):
    """{file name: page} for the overview and every node page, each audited, plus the cross-page
    rule that every case is embedded once and indexed once."""
    routes, art, sessions = inputs or load_inputs(repo)
    check_inputs(routes, art)
    payloads = {}
    for c in art["cases"]:
        rk = round_key(c)
        if rk not in payloads:
            payloads[rk] = _round_payload(sessions, c)
    pages, pos_of = {}, {}
    for slug, node in NODE_PAGES:
        page, pos = render_node_page(slug, node, routes, art, sessions, payloads)
        pages[f"stray-cannon-{slug}.html"] = page
        pos_of.update(pos)
    pages[OVERVIEW] = render_overview(routes, art, sessions, pos_of)
    for name, page in pages.items():
        _no_simplified(page, name)
    bad = audit_all(pages, art)
    _need(not bad, "; ".join(bad))
    return pages


def case_count(art):
    return len(art["cases"])


# ---------------------------------------------------------------- the audit

def _visible(page):
    return _SCRIPT.sub("", page)


def audit_text(page):
    """The %, 「hold」 and simplified-glyph rules, over the page's visible text."""
    bad = []
    vis = _visible(page)
    if set(page) & SIMPLIFIED:
        bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
    if "%" in _TAG.sub("", _SRC_QUOTE.sub("", vis)):
        bad.append("a % outside quoted source text — this page prints counts, never computed rates")
    held = _TAG.sub("", _HOLD_SPAN.sub("", vis).replace(PS["bag1"], ""))
    if _HOLD.search(held):
        bad.append("「hold」 outside the z_hold row and the bag-1 sentence — only the lock-7 test earns it")
    return bad


def audit_overview(page, art):
    bad = RP.audit_quarantine(page, OVERVIEW_REQUIRED, DATA_ID) + audit_text(page)
    want = {n["id"]: status_of(n)[0] for n in art["nodes"]}
    got = {}
    for nid, st in _NODE_BLOCK.findall(page):
        if nid in got:
            bad.append(f"node {nid} appears twice on the overview")
        got[nid] = st
    for nid, st in want.items():
        if nid not in got:
            bad.append(f"route node {nid} is missing from the overview")
        elif got[nid] != st:
            bad.append(f"route node {nid} shows status {got[nid]}, the artefact says {st}")
    rows = _CASE_ROW.findall(page)
    keys = sorted(case_key(c) for c in art["cases"])
    if sorted(rows) != keys:
        bad.append(f"the case index does not list every case exactly once "
                   f"({len(rows)} rows, {len(keys)} cases)")
    return bad


def audit_node_page(page, slug, node, art):
    bad = RP.audit_quarantine(page, NODE_REQUIRED, DATA_ID) + RP.audit_player(page) + audit_text(page)
    got = dict(_NODE_BLOCK.findall(page))
    for nid in _subtree(slug, node, art):
        if nid not in got:
            bad.append(f"route node {nid} is missing from {slug}")
    m = _ISLAND.search(page)
    if not m:
        return bad + ["no data island"]
    island = json.loads(m.group(1))
    rows = _CASE_ROW.findall(page)
    if sorted(rows) != sorted(r["case"] for r in island["cases"]):
        bad.append(f"{slug}: the case list and the data island disagree ({len(rows)} rows, "
                   f"{len(island['cases'])} embedded)")
    if len(set(rows)) != len(rows):
        bad.append(f"{slug}: a case is listed twice")
    for r in island["cases"]:
        if r["round"] not in island["rounds"]:
            bad.append(f"{slug}: case {r['case']} has no embedded replay")
    return bad


def audit_all(pages, art):
    bad = audit_overview(pages[OVERVIEW], art)
    seen = []
    for slug, node in NODE_PAGES:
        page = pages[f"stray-cannon-{slug}.html"]
        bad += audit_node_page(page, slug, node, art)
        seen += _CASE_ROW.findall(page)
    keys = sorted(case_key(c) for c in art["cases"])
    if sorted(seen) != keys:
        bad.append(f"the node pages do not embed every case exactly once ({len(seen)} embedded, "
                   f"{len(keys)} cases)")
    return bad


# ---------------------------------------------------------------- selftest

def _drop_line(page, needle):
    lines = page.split("\n")
    hit = [i for i, l in enumerate(lines) if needle in l]
    if not hit:
        return page
    del lines[hit[0]]
    return "\n".join(lines)


def _selftest():
    inputs = load_inputs(REPO)
    art = inputs[1]
    pages = render_all(REPO, inputs)
    ov = pages[OVERVIEW]
    ideal = "stray-cannon-ideal.html"
    cases = [("control: the rendered pages", None, None, None)]

    def m(name, page_name, new, want):
        cases.append((name, page_name, new, want))

    m("a dropped route node", OVERVIEW, _drop_line(ov, 'data-node="2.ideal.pc#7"'), "missing from the overview")
    m("a dropped text_only node", OVERVIEW, _drop_line(ov, 'data-node="2.ideal.ren4"'), "2.ideal.ren4 is missing")
    m("a dropped unmatchable node", OVERVIEW, _drop_line(ov, 'data-node="2.ideal.fire.stmb_example"'), "stmb_example is missing")
    m("a dropped node on a node page", ideal, _drop_line(pages[ideal], 'data-node="2.ideal.pc#16"'), "missing from ideal")
    first = art["cases"][0]
    m("a dropped case row on a node page", f"stray-cannon-{page_of(first)}.html",
      _drop_line(pages[f"stray-cannon-{page_of(first)}.html"], f'data-case="{case_key(first)}"'), "exactly once")
    m("a dropped case in the overview index", OVERVIEW, _drop_line(ov, f'data-case="{case_key(first)}"'), "every case exactly once")
    m("a claim badge", OVERVIEW, ov.replace(RS.TITLE_MARK, RS.TITLE_MARK + '<span class="claim-badge">✓</span>', 1), "claim badge")
    m("a data-claim on a node page", ideal, pages[ideal].replace('class="scp-cases"', 'class="scp-cases" data-claim="C001"', 1), "claim badge")
    m("an external src=", ideal, pages[ideal].replace("<script>", '<script src="x.js"></script><script>', 1), "external request")
    m("an innerHTML assignment", ideal, pages[ideal].replace('"use strict";', '"use strict"; document.body.innerHTML = "";', 1), "assigns markup")
    m("a simplified glyph", OVERVIEW, ov.replace("第一巡</h2>", "第一巡这</h2>", 1), "simplified glyph")
    m("a second data island", OVERVIEW, ov.replace("</body>", f'<script type="application/json" id="{DATA_ID}">{{}}</script></body>', 1), "data island")
    m("a computed percentage", OVERVIEW, re.sub(r'(<p class="scp-count">\d+ / \d+)', r"\1（12.5%）", ov, count=1), "a % outside quoted")
    m("an unguarded writeHash(p) on a node page", ideal, pages[ideal].replace("if (!playing) writeHash(p)", "writeHash(p)", 1), "while playing")
    m("QUIET_BEFORE_DESTROY reordered", ideal, pages[ideal].replace(
        RP.QUIET_BEFORE_DESTROY, "if (handle) { handle.destroy(); handle = null; }\n    quiet = true;", 1), "OLD round")
    m("「hold」 added to the z_placed_elsewhere row", OVERVIEW, re.sub(
        r'(data-node="bag1\.z_placed_elsewhere".*?<p class="scp-count">)', r"\1hold 咗 Z · ", ov, count=1),
      "「hold」 outside")
    m("a node page missing BOUNDARY_SENTENCE", ideal, pages[ideal].replace(RS.BOUNDARY_SENTENCE, ""), "quarantine sentence")
    m("a node page missing a PAGE_SENTENCE", ideal, pages[ideal].replace(PS["mirror"], ""), "quarantine sentence")
    m("a status that disagrees with the artefact", OVERVIEW, ov.replace(
        'data-node="2.ideal.pc#7" data-status="empty"', 'data-node="2.ideal.pc#7" data-status="count"', 1), "the artefact says")

    ok = True
    for name, page_name, new, want in cases:
        if page_name is None:
            found = audit_all(pages, art)
            good = not found
            applied = True
        else:
            applied = new != pages[page_name]
            found = audit_all({**pages, page_name: new}, art)
            good = applied and any(want in f for f in found)
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if found else 'accepted'}"
              f"{'' if applied else '  <- the mutant did not apply'}")
    # render refusals
    routes, art0, sessions = inputs
    eligible = json.loads(json.dumps(art0))
    eligible["report_eligible"] = True
    refused = 0
    try:
        render_all(REPO, (routes, eligible, sessions))
        print("  BAD a report-eligible artefact rendered")
        ok = False
    except SystemExit as e:
        refused += 1
        print(f"  ok  a report-eligible artefact is refused: {str(e)[:60]}…")
    lost = json.loads(json.dumps(art0))
    lost["nodes"] = [n for n in lost["nodes"] if n["id"] != "2.ideal.ren4"]
    try:
        render_all(REPO, (routes, lost, sessions))
        print("  BAD an artefact missing a route node rendered")
        ok = False
    except SystemExit as e:
        refused += 1
        print(f"  ok  an artefact missing a route node is refused: {str(e)[:60]}…")
    print(f"{'ok ' if ok else 'FAIL'} stray_cannon_page selftest: {len(cases) - 1 + refused} "
          f"corruptions, {'all caught' if ok else 'SOME MISSED'}")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not a.out_dir:
        ap.error("need --out-dir, or --selftest")
    os.makedirs(a.out_dir, exist_ok=True)
    for name, page in render_all(REPO).items():
        with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(page)
        print(f"wrote {os.path.join(a.out_dir, name)} ({len(page.encode())} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
