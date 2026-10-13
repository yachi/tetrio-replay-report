"""定式路線頁 — the shared ROUTE PAGES renderer: for one shiwehi.com opener route page (迷走砲,
はちみつ砲, …) one overview, one replay page per bag-2 node (plus `bag1-only`), and the constructed
demo page, each audited before it is returned.

    python3 -m pipeline.stray_cannon_page --out-dir /tmp/sc   # 迷走砲's pages, through its shim
    python3 -m pipeline.stray_cannon_page --selftest          # its audit's mutants

ONE RENDERER, ONE AUDIT. A `RouteSite` is this module bound to one opener's `RouteSiteProfile`
(file names, schemas, node orders, which node earns 「hold」, which selftest targets) and its prose
file; everything else — the board SVGs, the quarantine rules, the completeness rules, the demo end-
state check — is written once here. `stray_cannon_page.py` is 迷走砲's shim and keeps its CLI.

Inputs, all committed: the opener's routes JSON (transcribed and gated through
`pipeline/openers/route_transcription.py`), its corpus artefact (which round reached which route
node, `pipeline/sim/route-facts.ts`), its demo artefact (`pipeline/sim/route-demos.ts`), and each
session's `sim/replay-facts.json` + `report/facts.json` (the replay payloads, through
`replay_section.round_payload` — the same function the per-session replay page calls). Pure Python,
so `bin/build-docs` can render it in the `docs` job, which has no bun.

PAGES. `<prefix>.html` draws every route node with its count and indexes every case; it embeds no
player. `<prefix>-<slug>.html` holds every case whose bag 2 went to one node (or, for `bag1-only`,
to none), each with the shared `replay_player.js`, mounted one at a time by `stray_cannon_page.js`
(shared by every opener, and inlined verbatim). No name ends in `-replay.html`: `bin/build-docs`
owns that suffix.

QUARANTINE. Simulator output, the same tier as the replay pages: no claim ids, no ✓, no
`data-claim`, and the artefact must say `report_eligible: false`. The audit reuses
`replay_page.audit_quarantine` / `audit_player` — one copy of each rule — and adds the route pages'
own completeness rules: every route node and outcome appears with a count or a reason it has none,
every case is embedded exactly once on a node page and indexed exactly once on the overview, the
only `%` are inside quoted source text, and 「hold」 appears only where the hold-split predicate
earns it (the profile's `hold_node`).

FIGURES. Counts only, rendered from the artefacts, always as 「N / M」 with the denominator; the
source page's percentages appear only inside its quoted text. No rate is computed here, so no
rounding rule is exercised.
"""
import argparse
import html
import json
import os
import re
from dataclasses import dataclass, field

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline.claims.build_claims import SIMPLIFIED

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
#: the page script every opener shares, inlined verbatim (its bytes ship in every page)
PAGE_JS = os.path.join(HERE, "stray_cannon_page.js")

DATA_ID = "scp-data"
TEMPLATE_ID = "scp-player-tpl"
# Fields every round payload carries identically; inlined once per page. `session` is NOT one:
# a page holds rounds from every session, so it stays in each payload.
SHARED = ("shapes", "width", "rows", "visible", "next", "flag_words")

CELL = 14
PIECE_CLASS = {"i": "i", "o": "o", "t": "t", "s": "s", "z": "z", "j": "j", "l": "l",
               "c": "c", "U": "u", "Z": "zz", "p": "p"}
# An opener whose transcription uses other letters (はちみつ砲's held J, the cleared-row C, the REN
# region B) adds them through its profile's `cell_classes`, and their CSS through `extra_css`, so a
# letter one opener draws never changes another opener's bytes.

# visible-text extraction for the % and 「hold」 rules
_SCRIPT = re.compile(r"<script\b.*?</script>|<style\b.*?</style>|<template\b.*?</template>", re.S)
_SRC_QUOTE = re.compile(r'<q class="scp-src">.*?</q>', re.S)
_DEMO_HOLD_SPAN = re.compile(r'<span class="scp-hold" data-demo="([a-z0-9-]+)">[^<]*</span>')
_DEMO_BLOCK = re.compile(r'data-demo-node="([^"]+)" data-demo="(built|unbuilt)"')
_TAG = re.compile(r"<[^>]+>")
_HOLD = re.compile(r"hold", re.I)
_NODE_BLOCK = re.compile(r'data-node="([^"]+)" data-status="([a-z_]+)"')
_CASE_ROW = re.compile(r'data-case="([^"]+)"')
_ISLAND = re.compile(r'<script type="application/json" id="' + DATA_ID + r'">(.*?)</script>', re.S)

#: the line count a bag-2 board's T-spin clears, from the node's `spin`
SPIN_LINES = {"TSS": 1, "TSD": 2, "TST": 3}


def _need(cond, msg):
    if not cond:
        raise SystemExit(f"route_page: {msg}")


def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def case_key(c):
    return f"{c['session']}-m{c['match']}r{c['round']}-{c['player']}"


def round_key(c):
    return f"{c['session']}-m{c['match']}r{c['round']}"


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
    raise SystemExit(f"route_page: slot {slot} has no lock {lock}")


def _esc(s):
    return html.escape(str(s))


def _src(text):
    """Quoted source text: the ONLY place a % may appear."""
    return f'<q class="scp-src">{_esc(text)}</q>'


def board_svg(rows, label, classes=PIECE_CLASS):
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
            _need(ch in classes, f"{label}: unknown cell {ch!r}")
            out.append(f'<rect class="scb-{classes[ch]}" x="{x * CELL + 1}" y="{y * CELL + 1}" '
                       f'width="{CELL - 2}" height="{CELL - 2}"/>')
    out.append("</svg>")
    return "".join(out)


def _source_line(routes):
    src, terms = routes["source"], routes["terms"]
    return (f'  <p class="scp-src-line">來源：<a href="{_esc(src["url"])}">{_esc(src["title"])}'
            f'（shiwehi.com）</a>，原頁 {_esc(src["updated"])} 版，{_esc(src["fetched"])} 讀取；'
            f'<a href="{_esc(terms["url"])}">使用條款</a>（非商業用途，註明出處）。</p>')


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


def demo_slug(nid):
    """`2.ideal.pc#3` -> `demo-ideal-pc3`: the ONE spelling of a demo's anchor, hash and island key."""
    s = nid[2:] if nid.startswith("2.") else nid
    return "demo-" + re.sub(r"[._]+", "-", s.replace("#", "")).lower()


def _shows(board, rows, u_empty):
    """Does a y-UP board show `rows` (bottom-aligned)? `c` any filled cell, `U` empty (the slot)
    or a T, a letter that piece, `-` empty; nothing above the drawing."""
    h = len(rows)
    for y, line in enumerate(board):
        for x, v in enumerate(line):
            ch = rows[h - 1 - y][x] if y < h else "-"
            if ch == "-" or (ch == "U" and u_empty):
                if v is not None:
                    return False
            elif v is None or (ch != "c" and v != ("T" if ch == "U" else ch.upper())):
                return False
    return True


def _read_rows(rows, readings):
    out = [list(r) for r in rows]
    for rd in readings:
        for x, d in rd["cells"]:
            i = len(rows) - 1 - d
            _need(out[i][x] == rd["drawn"], f"reading cell {x},{d} is not {rd['drawn']}")
            out[i][x] = rd["reads_as"].lower()
    return ["".join(r) for r in out]


def _composite_ok(demo, data, start, rows, readings):
    """The kept-rows frame from lock `start` on (every row cleared after it stays drawn) against a
    Perfect Clear pattern: `c` a cell there before `start`, a letter or U the piece placed after."""
    width = data["board"]["width"]
    vrows, vmap = None, None
    for i, (piece, full, board) in enumerate(RS.decode_boards(data, demo["seq"], demo["locks"],
                                                             RS.NEXT_SHOWN)):
        if i == start - 1:
            vrows = [[(v.lower() if v else "-") for v in line] for line in board]
            vmap = list(range(len(vrows)))
            continue
        if i < start:
            continue
        # the piece's own cells: what this board has that the frame does not, read through vmap
        cells = RS._place_cells(data["shapes"], width, data["board"]["rows"], piece, demo["locks"][i][1])
        for c in cells:
            y, x = divmod(c, width)
            _need(vrows[vmap[y]][x] == "-", f"{demo['node']}: lock {i} overlaps in the frame")
            vrows[vmap[y]][x] = piece
        if full:
            keep = [vmap[y] for y in range(len(vmap)) if y not in full]
            while len(keep) < len(vmap):
                vrows.append(["-"] * width)
                keep.append(len(vrows) - 1)
            vmap = keep
    rd = _read_rows(rows, readings)
    h = len(rd)
    for d, line in enumerate(vrows):
        for x, a in enumerate(line):
            b = rd[h - 1 - d][x] if d < h else "-"
            if b == "-":
                if a != "-":
                    return False
            elif b == "c":
                if a == "-" or a.isupper():
                    return False
            elif a != ("T" if b == "U" else b.upper()):
                return False
    return True


def _visible(page):
    return _SCRIPT.sub("", page)


def _drop_line(page, needle):
    lines = page.split("\n")
    hit = [i for i, l in enumerate(lines) if needle in l]
    if not hit:
        return page
    del lines[hit[0]]
    return "\n".join(lines)


def case_count(art):
    return len(art["cases"])


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


@dataclass
class RouteSiteProfile:
    """One opener's half of the route pages. Every field is something the shared renderer cannot
    derive; the strings a reader sees live in the prose file, not here."""
    #: the module name failures are reported under (its shim)
    module: str
    #: docs file prefix: `<prefix>.html`, `<prefix>-<slug>.html`, `<prefix>-demos.html`
    prefix: str
    routes_rel: str
    facts_rel: str
    demos_rel: str
    prose_path: str
    routes_schema: str
    facts_schema: str
    demos_schema: str
    page_schema: str
    #: (slug, bag-2 node or None): a case goes to the page of its bag-2 node; none -> bag1-only
    node_pages: tuple
    bag1_order: tuple
    bag2_order: tuple
    #: the bag-2 nodes (or groups) whose bag-3 subtrees the overview draws, in order
    bag3_parents: tuple
    #: the one node that asserts a hold, its held piece, and the prose key of its heading. None: the
    #: page asserts no hold anywhere (stick spin), so 「hold」 may appear only in the bag-1 sentence
    hold_node: str | None
    hold_piece: str
    hold_heading_key: str
    #: the case flag compared with the 六個具名定式 column, the opener-facts key, the prose key. None
    #: (flag_field and harddrop_key): no harddrop column exists (stick spin); the prose key is then
    #: formatted with the bag-1 total and `cases`, the bag-1 nodes' case counts, and nothing else
    flag_field: str | None
    harddrop_key: str | None
    flag_prose: str
    #: route-JSON `bag1` keys quoted on the overview's 第一巡 section
    bag1_quote_keys: tuple
    #: non-board nodes drawn at the top of the overview, and the quotes printed above them
    overview_nodes: tuple
    overview_quote_ids: tuple
    #: a derived bag-1 board (drawn nowhere on its own) goes after this node on the demo page
    derived_after: str
    #: bag 2 is drawn after this many pieces: its board is at this 0-based lock index
    bag2_lock: int
    pc_lines: int
    #: node ids and page names the selftest plants its mutants into
    selftest_targets: dict = field(default_factory=dict)
    #: bag-2 boards that are not branches (illustrations of a branch's T-spin), drawn under 第二巡
    #: after `bag2_order` instead of under their parent in 第三巡
    bag2_extra: tuple = ()
    #: board letters beyond PIECE_CLASS, and the CSS for them (empty: the page's CSS is untouched)
    cell_classes: dict = field(default_factory=dict)
    extra_css: str = ""
    #: the largest a rendered page may be, in bytes (0: no limit). A page over it is a render failure,
    #: never a truncation: split the page instead.
    max_page_bytes: int = 0
    #: the `near_note` format keys and the artefact list each one counts (はちみつ砲 and 山岳積み2号 name
    #: theirs after the TST; stick spin after the TSD, plus its `near` and `unexplained` kinds)
    near_lists: tuple = (("subset", "bag2_none_tst_before_complete"), ("superset", "bag2_none_extra_piece"),
                         ("moved", "bag2_none_moved_piece"), ("stripped", "bag2_garbage_stripped"))


class RouteSite:
    """The route pages of one opener: this module's renderer and audit bound to one profile."""

    def __init__(self, p: RouteSiteProfile):
        self.p = p
        self.ROUTES_REL, self.FACTS_REL, self.DEMOS_REL = p.routes_rel, p.facts_rel, p.demos_rel
        self.OVERVIEW = f"{p.prefix}.html"
        self.DEMO_PAGE = f"{p.prefix}-demos.html"
        self.NODE_PAGES, self.BAG1_ORDER, self.BAG2_ORDER = p.node_pages, p.bag1_order, p.bag2_order
        self.PROSE = self.load_prose(p.prose_path)
        PS = self.PS = self.PROSE["page_sentences"]
        self.PAGE_SENTENCES = (PS["source"], PS["exact"], PS["bag3"], PS["bag1"], PS["mirror"], PS["our_reading"])
        # The overview embeds no player, so the two sentences about the player's timeline are not its to carry.
        self.OVERVIEW_REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, RS.HOLE_SENTENCE) + self.PAGE_SENTENCES
        self.NODE_REQUIRED = RS.REQUIRED + self.PAGE_SENTENCES
        self.DP = self.PROSE["demo"]
        DS = self.DS = self.DP["sentences"]
        # The demo page carries no garbage, no verified prefix and no admission flags, so HOLE_SENTENCE,
        # BOUNDARY_SENTENCE and FLAG_WORDS are NOT its to carry: requiring them would make it assert things
        # that are not about it. What it must say is that nobody played these.
        self.DEMO_SENTENCES = (DS["demo"], DS["engine"], DS["order"], DS["mirror"], DS["rule"])
        self.DEMO_REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, PS["source"]) + self.DEMO_SENTENCES
        # visible-text extraction for the 「hold」 rule and the demo links: per site
        self._HOLD_SPAN = (re.compile(r'<span class="scp-hold" data-node="' + re.escape(p.hold_node)
                                      + r'">[^<]*</span>') if p.hold_node else re.compile(r"(?!)"))
        self._DEMO_LINK = re.compile(r'href="' + re.escape(self.DEMO_PAGE) + r'#(demo-[a-z0-9-]+)"')
        self.CLASSES = {**PIECE_CLASS, **p.cell_classes}
        #: a bag-2 node -> the group its page is named by (filled from the routes in check_inputs)
        self.GROUP = {}
        #: list id -> the transcription's list (filled from the routes in demo_problems)
        self.LISTS = {}

    def bag1_only_slug(self):
        slugs = [s for s, n in self.NODE_PAGES if n is None]
        self._need(len(slugs) == 1, f"the profile names {len(slugs)} bag1-only pages")
        return slugs[0]

    def load_prose(self, path):
        with open(path, encoding="utf-8") as fh:
            prose = json.load(fh)
        for s in _walk_strings(prose):
            self._no_simplified(s, os.path.basename(path))
        return prose

    # ------------------------------------------------------------ inputs

    def _need(self, cond, msg):
        if not cond:
            raise SystemExit(f"{self.p.module}: {msg}")

    def _no_simplified(self, text, where):
        bad = sorted(set(text) & SIMPLIFIED)
        self._need(not bad, f"{where}: simplified glyph(s) {bad} — this report is traditional-character Cantonese")
        return text

    def load_inputs(self, repo=REPO):
        """(routes, facts artefact, {session: (replay data, facts.json, opener-facts)})."""
        with open(os.path.join(repo, self.ROUTES_REL), encoding="utf-8") as fh:
            routes = json.load(fh)
        with open(os.path.join(repo, self.FACTS_REL), encoding="utf-8") as fh:
            art = json.load(fh)
        sessions = {}
        for s in art["sessions"]:
            sdir = os.path.join(repo, "sessions", s)
            data, facts = RP.load(sdir)
            self._need(data is not None, f"{s} has no {RS.FACTS_REL}")
            with open(os.path.join(sdir, "sim", "opener-facts.json"), encoding="utf-8") as fh:
                opener = json.load(fh)
            sessions[s] = (data, facts, opener)
        return routes, art, sessions

    def check_inputs(self, routes, art):
        self._need(routes.get("schema") == self.p.routes_schema, f"unknown routes schema {routes.get('schema')!r}")
        self._need(art.get("schema") == self.p.facts_schema, f"unknown facts schema {art.get('schema')!r}")
        self._need(art.get("report_eligible") is False,
              f"{os.path.basename(self.FACTS_REL)} must declare report_eligible: false — simulator boards are not "
              "trust-chain data")
        route_ids = [n["id"] for n in routes["nodes"]]
        fact_ids = [n["id"] for n in art["nodes"]]
        self._need(len(set(fact_ids)) == len(fact_ids), "duplicate node ids in the facts artefact")
        self._need(set(fact_ids) == set(route_ids) | set(art["outcomes"]),
              "the facts artefact's nodes are not the routes' nodes plus its outcomes: "
              f"{sorted(set(fact_ids) ^ (set(route_ids) | set(art['outcomes'])))}")
        self.GROUP = {n["id"]: n["group"] for n in routes["nodes"] if n.get("group")}

    def members(self, nid, art):
        """A node's own id, or for a group (はちみつ砲's 2.ideal) the facts nodes that belong to it."""
        if nid in self.GROUP.values():
            return [n["id"] for n in art["nodes"] if self.GROUP.get(n["id"]) == nid]
        return [nid]

    def cases_of(self, nid, art):
        """Cases at a node, or summed over a group's members; 0 for an unmeasured node."""
        fnodes = {n["id"]: n for n in art["nodes"]}
        return sum(fnodes[m].get("cases", 0) for m in self.members(nid, art))

    def page_of(self, c):
        b2 = (c.get("bag2") or {}).get("node")
        b2 = self.GROUP.get(b2, b2)
        for slug, node in self.NODE_PAGES:
            if node == b2:
                return slug
        raise SystemExit(f"{self.p.module}: {case_key(c)} went to {b2!r}, which has no page")

    def _round_payload(self, sessions, c):
        data, facts, _op = sessions[c["session"]]
        RS.check_artefact(data)
        for mi, m in enumerate(facts["matches"]):
            if m["file"] != c["file"]:
                continue
            for ri, r in enumerate(m["rounds"]):
                if r["index"] == c["round_index0"]:
                    pl = RS.round_payload(data, facts, mi, ri)
                    self._need(pl["match"] == c["match"] and pl["round"] == c["round"],
                          f"{case_key(c)}: facts.json puts it at m{pl['match']}r{pl['round']}")
                    return pl
        raise SystemExit(f"{self.p.module}: {case_key(c)} ({c['file']} round {c['round_index0']}) "
                         "is not in its session's facts.json")

    def node_name(self, nid, routes_by_id):
        names = self.PROSE["names"]
        if nid in names:
            return names[nid]
        if nid.endswith(".other"):
            parent = nid[:-len(".other")]
            return names["other"].format(parent=self.node_name(parent, routes_by_id))
        n = routes_by_id.get(nid)
        self._need(n is not None, f"no name for node {nid!r}")
        if "list" in n:
            return names["pc"].format(parent=self.node_name(n["parent"], routes_by_id), k=n["index"])
        raise SystemExit(f"{self.p.module}: no Cantonese name for {nid!r} in the prose file")

    def _condition_words(self, cond):
        if not cond:
            return ""
        if "all" in cond:
            words = "，".join(f"{a} 早過 {b}" for a, b in (x["before"] for x in cond["all"]))
            # a condition the page states only as an example (はちみつ砲's 「など」) says so wherever it is shown
            return words + self.PROSE["illustrative"] if cond.get("illustrative") else words
        if "early" in cond:
            return f"{cond['early']} 早（原頁冇講幾早先算）"
        if "bag1" in cond:
            return f"第一巡係「{self.PROSE['names'][cond['bag1']]}」"
        raise SystemExit(f"{self.p.module}: unknown condition {cond!r}")

    def status_of(self, fn):
        """(status, words) for one facts node. Every node has exactly one."""
        if not fn["measured"]:
            why = fn["why"]
            kind = ("unmatchable" if why.startswith("unmatchable")
                    else "mirror_of" if why.startswith("mirror_of") else why)
            self._need(kind in self.PROSE["status_words"], f"{fn['id']}: unknown reason {why!r}")
            words = self.PROSE["status_words"][kind]
            if kind == "unmatchable":
                words += "：" + self.PROSE["unmatchable_reasons"][fn["id"]]
            return kind, words
        if fn["cases"] == 0:
            return "empty", self.PROSE["empty_node"].format(m=fn["opportunities"])
        by = "、".join(f"{_esc(u)} {n}" for u, n in sorted(fn["cases_by_player"].items()))
        return "count", f"{fn['cases']} / {fn['opportunities']}（{by}）"

    def node_block(self, nid, fn, routes_by_id, href=None, extra="", demo=""):
        """One route node, one line: name, status, board if transcribed. `data-node` + `data-status`
        are what the completeness audit reads."""
        st, words = self.status_of(fn)
        rn = routes_by_id.get(nid, {})
        name = self.node_name(nid, routes_by_id)
        if nid == self.p.hold_node:
            title = (f'<span class="scp-hold" data-node="{_esc(nid)}">'
                     f'{_esc(self.PROSE[self.p.hold_heading_key])}</span>')
        else:
            title = _esc(name)
        if href:
            title = f'<a href="{_esc(href)}">{title}</a>'
        bits = [f'<div class="scp-node" data-node="{_esc(nid)}" data-status="{st}">',
                f'<h4 class="scp-name">{title}</h4>']
        if rn.get("label_jp"):
            bits.append(f'<p class="scp-jp">原頁：{_src(rn["label_jp"])}</p>')
        if "rows" in rn:
            bits.append(board_svg(rn["rows"], name, self.CLASSES))
        if rn.get("listed_under"):
            bits.append(f'<p class="scp-tag">{_esc(self.PROSE["listed_under"][rn["listed_under"]])}</p>')
        if rn.get("condition"):
            bits.append(f'<p class="scp-cond">條件：{_esc(self._condition_words(rn["condition"]))}；'
                        f'原文 {_src(rn["condition_verbatim"])}</p>')
        if rn.get("text_verbatim"):
            bits.append(f'<p class="scp-cond">原文 {_src(rn["text_verbatim"])}</p>')
        bits.append(f'<p class="scp-count">{words}</p>')
        if demo:
            bits.append(demo)
        if extra:
            bits.append(extra)
        bits.append("</div>")
        return "".join(bits)

    def _head(self, title, desc, users, with_player):
        css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), PAGE_CSS.strip("\n")]
        if self.p.extra_css:
            css.append(self.p.extra_css.strip("\n"))
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

    def _method_note(self, include_player):
        lines = ['  <div class="method-note">',
                 '    <p><strong>呢版唔屬於信任鏈。</strong>每個盤面都係<strong>一個 replay 模擬器</strong>'
                 '（Triangle 引擎）重跑操作記錄推導出嚟，冇第二份獨立實作；邊一局對到邊一步亦係由佢推出嚟。'
                 f'所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        lines += [f"    <p>{s}</p>" for s in self.PAGE_SENTENCES]
        lines.append(f"    <p>{RS.HOLE_SENTENCE}</p>")
        if include_player:
            lines += [f"    <p>{RS.DROP_SENTENCE}</p>", f"    <p>{RS.BOUNDARY_SENTENCE}</p>",
                      '    <p>每一局都會核成局總數同 <code>facts.json</code> 夾唔夾；有一項唔夾，嗰局就會寫'
                      f'「{RS.FLAG_WORDS}」。</p>']
        lines.append("  </div>")
        return lines

    def render_overview(self, routes, art, sessions, page_href, demos):
        by_id = {n["id"]: n for n in routes["nodes"]}
        fnodes = {n["id"]: n for n in art["nodes"]}
        cases = sorted(art["cases"], key=lambda c: (c["session"], c["match"], c["round"], c["player"]))
        title = f"{self.PROSE['overview_title']}{RS.TITLE_MARK}"
        shown = set()

        def block(nid, href=None, extra=""):
            shown.add(nid)
            return "    " + self.node_block(nid, fnodes[nid], by_id, href, extra, self.demo_link(nid, demos, by_id))

        out = self._head(title, self.PROSE["overview_desc"], [], False)
        out += ['  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a></nav>',
                '  <header class="scp-head">',
                f'    <div class="eyebrow">{RS.EYEBROW}</div>',
                f'    <h1 class="section-title">{_esc(title)}</h1>',
                f'    <p>{_esc(self.PROSE["overview_lede"])}</p>',
                _source_line(routes),
                '  </header>']
        out += self._method_note(False)
        out.append(f'  <p class="scp-quote"><a href="{self.DEMO_PAGE}">{_esc(self.DP["title"])}</a>：'
                   f'{_esc(self.DP["overview_note"])}</p>')
        mq = {q["id"]: q for q in routes["quotes"]}
        for qid in self.p.overview_quote_ids:
            if qid in mq:
                out.append(f'  <p class="scp-quote">原頁：{_src(mq[qid]["verbatim"])}</p>')
        out.append('  <div class="scp-grid">')
        for nid in self.p.overview_nodes:
            out.append(block(nid))
        out.append("  </div>")

        # 基本形
        out += ['  <section class="scp-sec" id="basic"><h2>基本形</h2><div class="scp-grid">']
        for b in routes["basic_form"]:
            nm = self.node_name(b["same_as"], by_id)
            out.append(f'    <div class="scp-basic"><h4 class="scp-name">{_esc(nm)}</h4>'
                       f'{board_svg(b["rows"], nm, self.CLASSES)}</div>')
        out.append("  </div></section>")

        # 第一巡
        b1 = routes["bag1"]
        total = sum(fnodes[n].get("cases", 0) for n in self.BAG1_ORDER)
        flag = self.p.flag_field
        m6 = sum(1 for c in art["cases"] if c["bag1"][flag]) if flag else 0
        table = 0
        for s, (_d, _f, op) in (sessions.items() if flag else ()):
            sc = [o for o in op["named_openers"]["openers"] if o["key"] == self.p.harddrop_key]
            self._need(len(sc) == 1, f"{s}: opener-facts.json has {len(sc)} {self.p.harddrop_key} entries")
            table += sum(p["exact"] for p in sc[0]["players"])
        out += ['  <section class="scp-sec" id="bag1"><h2>第一巡</h2>',
                f'  <p class="scp-quote">原頁：{" ".join(_src(b1[k]) for k in self.p.bag1_quote_keys)}</p>',
                '  <div class="scp-grid">']
        for nid in self.BAG1_ORDER:
            out.append(block(nid, f"{self.p.prefix}-{self.bag1_only_slug()}.html#g-{nid}" if fnodes[nid].get("cases") else None))
        out.append("  </div>")
        fp = self.p.flag_prose
        if flag:
            extra = sum(1 for c in art["cases"] if not c["bag1"][flag])
            self._need(total == m6 + extra, f"bag-1 nodes hold {total} cases, {flag} splits them {m6} + {extra}")
            out.append("  <p>" + _esc(self.PROSE[fp].format(
                table=table, m6=m6, total=total, extra=extra,
                same=self.PROSE[fp + "_same"] if table == m6 else self.PROSE[fp + "_differ"])) + "</p>")
        else:
            self._need(total == len(art["cases"]), f"bag-1 nodes hold {total} cases, the artefact {len(art['cases'])}")
            out.append("  <p>" + _esc(self.PROSE[fp].format(
                total=total, cases={n: fnodes[n].get("cases", 0) for n in self.BAG1_ORDER})) + "</p>")
        out.append("  </section>")

        # 第二巡
        slug_of = {n: s for s, n in self.NODE_PAGES}
        slug_of.update({m: slug_of[g] for m, g in self.GROUP.items() if g in slug_of})
        out += ['  <section class="scp-sec" id="bag2"><h2>第二巡</h2><div class="scp-grid">']
        for nid in self.BAG2_ORDER:
            href = f"{self.p.prefix}-{slug_of[nid]}.html" if nid in slug_of and fnodes[nid]["cases"] else None
            out.append(block(nid, href))
        for nid in self.p.bag2_extra:
            out.append(block(nid))
        out.append("  </div>")
        if "bag2_note" in self.PROSE:
            out.append(f'  <p>{_esc(self.PROSE["bag2_note"])}</p>')
        cond = art["conditions"]
        cols = [n for n in self.BAG2_ORDER if any(n in v for v in cond.values())]
        out += ['  <table class="scp-table"><caption>' + _esc(self.PROSE["conditions_caption"]) + "</caption>",
                "    <tr><th>實際砌咗</th>" + "".join(f"<th>{_esc(self.node_name(c, by_id))}</th>" for c in cols)
                + f"<th>{_esc(self.PROSE['conditions_none'])}</th></tr>"]
        for built in self.BAG2_ORDER:
            n_built = fnodes[built]["cases"]
            if not n_built:
                continue
            row = cond.get(built, {})
            rest = n_built - sum(row.get(c, 0) for c in cols)
            self._need(rest >= 0, f"{built}: condition tallies exceed its cases")
            out.append(f"    <tr><th>{_esc(self.node_name(built, by_id))}（{n_built}）</th>"
                       + "".join(f"<td>{row.get(c, 0)}</td>" for c in cols) + f"<td>{rest}</td></tr>")
        out.append("  </table>")
        if "near_note" in self.PROSE:
            L = art["lists"]
            out.append("  <p>" + _esc(self.PROSE["near_note"].format(
                none=sum(1 for c in art["cases"] if not (c.get("bag2") or {}).get("node")),
                matched=sum(1 for c in art["cases"] if (c.get("bag2") or {}).get("node")),
                **{k: len(L[li]) for k, li in self.p.near_lists})) + "</p>")
        mism = art["lists"]["bag2_handedness_mismatch"]
        if mism:
            out.append(f"  <h3>{_esc(self.PROSE['handedness_heading'])}</h3><ul>"
                       + "".join(f"<li>{_esc(x)}</li>" for x in mism) + "</ul>")
        out.append("  </section>")

        # 第三巡
        out += ['  <section class="scp-sec" id="bag3"><h2>第三巡</h2>']
        lists = {l["id"]: l for l in routes["lists"]}
        for parent in self.p.bag3_parents:
            kids = [n["id"] for n in routes["nodes"] if (n.get("parent") == parent
                    or (n.get("parent") or "").startswith(parent + ".")) and n["id"] not in shown]
            if not kids:
                continue
            href = (f"{self.p.prefix}-{slug_of[parent]}.html" if parent in slug_of and self.cases_of(parent, art)
                    else None)
            out.append(f"  <h3>{_esc(self.node_name(parent, by_id))}</h3>")
            li = lists.get(parent + ".pc")
            if li and (parent + ".pc") in mq:
                out.append(f'  <p class="scp-quote">原頁：{_src(mq[parent + ".pc"]["verbatim"])}</p>')
            out.append('  <div class="scp-grid">')
            for k in kids:
                out.append(block(k, f"{href}#g-{k}" if href and fnodes[k].get("cases") else None))
            out.append("  </div>")
        if "bag3_note" in self.PROSE:
            out.append(f'  <p>{_esc(self.PROSE["bag3_note"])}</p>')
        out.append(f"  <h3>{_esc(self.PROSE['off_page_heading'])}</h3>")
        out.append(f"  <p>{_esc(self.PROSE['off_page_note'])}</p><ul>")
        for c in cases:
            if c.get("pc") and c["pc"].get("off_page_under"):
                g = c["pc"]["off_page_under"]
                out.append(f'    <li><a href="{self.p.prefix}-{self.page_of(c)}.html#{round_key(c)}@p{{POS:{case_key(c)}}}">'
                           f'{_esc(c["session"])} m{c["match"]}r{c["round"]} · {_esc(c["player"])}</a>'
                           f'：{_esc(self.node_name(g, by_id))}</li>')
        out.append("  </ul>")
        out.append(f"  <h3>{_esc(self.PROSE['discrepancy_heading'])}</h3><ul>")
        for d in routes["known_discrepancies"]:
            words = self.PROSE["discrepancies"][d["id"]]
            li = lists.get(d["id"].split(":")[0])
            if li:
                words = words.format(stated=li["stated_pattern_count"], drawn=li["drawn"],
                                     shown=li["shown"], rest=li["rest_stated"])
            out.append(f"    <li>{_esc(words)}</li>")
        out.append("  </ul></section>")

        # 個案索引
        out += [f'  <section class="scp-sec" id="cases"><h2>{_esc(self.PROSE["index_heading"])}</h2>',
                f'  <p>{_esc(self.PROSE["index_note"])}</p>',
                '  <div class="scp-index-wrap"><table class="scp-table scp-index">',
                "    <tr><th>日子</th><th>場·局</th><th>玩家</th><th>左右</th><th>去到邊一步</th><th>核對</th></tr>"]
        for c in cases:
            g = group_of(c)
            ver = "已核" if c["verified"] else self.PROSE["unverified"]
            out.append(f'    <tr data-case="{_esc(case_key(c))}"><td>{_esc(c["session"])}</td>'
                       f'<td>m{c["match"]}r{c["round"]}</td><td>{_esc(c["player"])}</td>'
                       f'<td>{"反轉" if c["bag1"]["mirrored"] else "原樣"}</td>'
                       f'<td><a href="{self.p.prefix}-{self.page_of(c)}.html#{round_key(c)}@p{{POS:{case_key(c)}}}">'
                       f'{_esc(self.node_name(g, by_id))}</a></td><td>{_esc(ver)}</td></tr>')
        out.append("  </table></div></section>")

        missing = set(fnodes) - shown
        self._need(not missing, f"the overview does not place node(s) {sorted(missing)}")
        island = {"schema": self.p.page_schema, "report_eligible": False,
                  "nodes": {n["id"]: {k: n[k] for k in ("cases", "opportunities") if k in n}
                            for n in art["nodes"]}}
        out += _tail(island)
        page = "\n".join(out)
        return re.sub(r"\{POS:([^}]+)\}", lambda m: str(page_href[m.group(1)]), page)

    def _subtree(self, slug, node, art):
        if node is None:
            return [n for n in self.BAG1_ORDER]
        return self.members(node, art) + [n["id"] for n in art["nodes"] if n["id"].startswith(node + ".")]

    def render_node_page(self, slug, node, routes, art, sessions, payloads, demos):
        """One bag-2 node's page: every case under it, each with its replay. Returns (page, {case: pos})."""
        by_id = {n["id"]: n for n in routes["nodes"]}
        fnodes = {n["id"]: n for n in art["nodes"]}
        mine = sorted((c for c in art["cases"] if self.page_of(c) == slug),
                      key=lambda c: (c["session"], c["match"], c["round"], c["player"]))
        self._need(mine, f"{slug}: no cases")
        name = self.node_name(node, by_id) if node else self.PROSE["bag1_only_name"]
        title = f"{self.PROSE['opener_name']} {name}{RS.TITLE_MARK}"

        shared, rounds, case_rows, pos_of = None, {}, [], {}
        users = None
        for c in mine:
            rk = round_key(c)
            pl = payloads[rk]
            if shared is None:
                shared = {k: pl[k] for k in SHARED}
            self._need(all(pl[k] == shared[k] for k in SHARED), f"{rk}: a shared field differs")
            u = [p["user"] for p in pl["players"]]
            users = users or u
            self._need(u == users, f"{rk}: player order {u} differs from {users} — slot colours would swap")
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
        order = self._subtree(slug, node, art)
        order += sorted(g for g in groups if g not in order)
        for g in groups:
            self._need(g in order, f"{slug}: group {g!r} has no place on the page")

        with open(PAGE_JS, encoding="utf-8") as fh:
            page_js = fh.read().rstrip()
        self._need("</script" not in page_js.lower(), "stray_cannon_page.js may not contain a closing script tag")
        out = self._head(title, self.PROSE["node_page_desc"].format(opener=self.PROSE["opener_name"], name=name),
                         users, True)
        out += ['  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a>'
                f'<a href="{self.OVERVIEW}">{_esc(self.PROSE["overview_title"])}</a></nav>',
                '  <header class="scp-head">',
                f'    <div class="eyebrow">{RS.EYEBROW}</div>',
                f'    <h1 class="section-title">{_esc(title)}</h1>',
                "    <p>" + _esc(self.PROSE["bag1_only_lede"] if node is None
                                 else self.PROSE["node_page_lede"].format(name=name)) + "</p>",
                _source_line(routes),
                '  </header>']
        out += self._method_note(True)
        out += [f'  <section id="{RS.SECTION_ID}" aria-labelledby="rpg-now">',
                '    <h2 class="rpg-now" id="rpg-now" aria-live="polite"></h2>',
                f'    <p class="scp-idle">{_esc(self.PROSE["idle"])}</p>',
                '    <p class="rpg-notes"></p>',
                f'    <p class="rpg-flag" hidden>{RS.FLAG_WORDS}</p>',
                f'    <p class="rpg-missing" hidden>{_esc(self.PROSE["missing"])}</p>',
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
                out.append("    " + self.node_block(g, fn, by_id, demo=self.demo_link(g, demos, by_id)))
            else:
                out.append(f'    <div class="scp-node" data-node="{_esc(g)}" data-status="count">'
                           f'<h4 class="scp-name">{_esc(self.node_name(g, by_id))}</h4>'
                           f'<p class="scp-count">{len(rows)}</p></div>')
            if rows:
                out.append(f"    <h3>停喺呢一步嘅個案（{len(rows)}）</h3>")
                out.append('    <ul class="scp-cases">')
                for c, row in rows:
                    tag = " · 左右反轉" if c["bag1"]["mirrored"] else ""
                    near = c.get("bag2_near")
                    if near:
                        tag += " · " + self.PROSE["near_words"][near["kind"]].format(
                            groups="、".join(self.node_name(g, by_id) for g in near["groups"]), extra=near.get("extra") or "",
                            missing=near.get("missing") or "", cells=near.get("cells"))
                    unv = (f' · <span class="scp-unv">{_esc(self.PROSE["unverified"])}</span>'
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

    def load_demos(self, repo=REPO):
        with open(os.path.join(repo, self.DEMOS_REL), encoding="utf-8") as fh:
            return json.load(fh)

    def demo_problems(self, demos, routes):
        """The page's own check of the demo artefact, a second implementation of the end state the bun
        test checks: every board node has one demo or one unbuilt reason, and each demo — decoded with
        this module's decoder — ends where its drawing says (bag 1: the drawing; bag 2: the drawing with
        the U empty after 13 pieces, then the T into it; a PC pattern: the kept-rows frame, then an
        empty board after 8 lines; a mid-route drawing: the board before its U, then the T)."""
        bad = []
        if demos.get("schema") != self.p.demos_schema:
            return [f"unknown demos schema {demos.get('schema')!r}"]
        if demos.get("report_eligible") is not False or demos.get("constructed") is not True:
            return [f"{os.path.basename(self.DEMOS_REL)} must declare report_eligible: false and constructed: true"]
        by_id = {n["id"]: n for n in routes["nodes"]}
        self.LISTS = {li["id"]: li for li in routes["lists"]}
        built = [d["node"] for d in demos["demos"]]
        unbuilt = [u["node"] for u in demos["unbuilt"]]
        for n in routes["nodes"]:
            k = built.count(n["id"]) + unbuilt.count(n["id"])
            if "rows" in n and k != 1:
                bad.append(f"{n['id']}: {k} demo/unbuilt entries, want exactly one")
            if "rows" not in n and k:
                bad.append(f"{n['id']}: a demo for a node with no board")
        for nid in built + unbuilt:
            if nid not in by_id:
                bad.append(f"{nid}: not a route node")
        if len({demo_slug(x) for x in built}) != len(built):
            bad.append("two demos share a slug")
        for d in demos["demos"]:
            bad += self._demo_end(d, demos, by_id)
        return bad

    def _demo_end(self, d, data, by_id):
        n = by_id.get(d["node"])
        if n is None:
            return []
        locks = d["locks"]
        try:
            steps = [(p, list(f), [list(r) for r in b])
                     for p, f, b in RS.decode_boards(data, d["seq"], locks, RS.NEXT_SHOWN)]
            hold = RS.queue_states(d["seq"], locks, RS.NEXT_SHOWN)[-1][1]
        except SystemExit as e:
            return [f"{d['node']}: does not decode: {e}"]
        last = len(locks) - 1
        lines = sum(lk[2] for lk in locks)
        where = d["node"]
        if n["bag"] == 1 and any("U" in r for r in n["rows"]):
            # stick spin's bag-1 boards draw the T as U: the board before the last lock is the drawing
            # with the U empty, and the last lock is the drawn spin
            if not _shows(steps[last - 1][2], n["rows"], True):
                return [f"{where}: the board before the T is not the drawing"]
            if locks[last][3] != 2 or locks[last][2] != SPIN_LINES.get(n.get("spin")):
                return [f"{where}: the last lock is not the drawing's {n.get('spin')}"]
        elif n["bag"] == 1:
            if not _shows(steps[last][2], n["rows"], False):
                return [f"{where}: the final board is not the drawing"]
            if n["id"] == self.p.hold_node and hold != self.p.hold_piece:
                return [f"{where}: {self.p.hold_piece} is not in the hold box"]
        elif "list" in n:
            # a list checked BEFORE the bag-2 rule: 山岳積み2号 draws a PC list in bag 2 (2.pc4). Its line
            # count is the transcription's own (`total_lines`, else `pc_lines`) where it has one, the
            # profile's otherwise — the other two openers' lists carry neither
            want = self.pc_lines_of(n["list"])
            if any(v for row in steps[last][2] for v in row) or lines != want:
                return [f"{where}: does not end on an {want}-line Perfect Clear"]
            start = sum(len(b["placed"]) for b in d["bags"][:-1])
            if not _composite_ok(d, data, start, n["rows"], d.get("piece_readings", [])):
                return [f"{where}: the kept-rows frame is not the pattern"]
        elif n["bag"] == 2:
            b2 = self.p.bag2_lock
            if last != b2 + 1 or not _shows(steps[b2][2], n["rows"], True):
                return [f"{where}: the board after {b2 + 1} pieces is not the drawing"]
            want = SPIN_LINES.get(n.get("spin"))
            if locks[b2 + 1][3] != 2 or locks[b2 + 1][2] != want:
                return [f"{where}: lock {b2 + 2} is not the drawing's {n.get('spin')}"]
        elif n.get("spin_board"):
            # a board past bag 2 drawn with its slot empty and the T on a separate board (stick spin's
            # fallbacks): the board before the last lock is the drawing, the last lock the drawn spin
            if not _shows(steps[last - 1][2], n["rows"], True):
                return [f"{where}: the board before the T is not the drawing"]
            if locks[last][3] != 2 or locks[last][2] != SPIN_LINES.get(n.get("spin")):
                return [f"{where}: the last lock is not the drawing's {n.get('spin')}"]
        elif not any("U" in r for r in n["rows"]):
            if not _shows(steps[last][2], n["rows"], False):
                return [f"{where}: the final board is not the drawing"]
        else:
            if not _shows(steps[last - 1][2], n["rows"], True) or locks[last][3] != 2:
                return [f"{where}: the board before the U is not the drawing, or the T did not spin"]
        return []

    def pc_lines_of(self, list_id):
        """The lines a whole demo clears on its way to a list's Perfect Clear."""
        li = self.LISTS.get(list_id, {})
        return li.get("total_lines", li.get("pc_lines", self.p.pc_lines))

    def demo_link(self, nid, demos, routes_by_id):
        """The one line a node block on the overview and the node pages carries about its demo."""
        if "rows" not in routes_by_id.get(nid, {}):
            return ""
        if any(d["node"] == nid for d in demos["demos"]):
            return (f'<p class="scp-demo"><a href="{self.DEMO_PAGE}#{demo_slug(nid)}">'
                    f'{_esc(self.DP["link"])}</a></p>')
        return f'<p class="scp-demo">{_esc(self.DP["link_unbuilt"])}</p>'

    def _order_words(self, tok, held_slug, unused=""):
        kind, _, rest = tok.partition(":")
        w = self.DP["order_words"]
        if kind == "early":
            p, k = rest.split("@")
            return _esc(w["early"].format(p=p, k=k))
        if kind == "before":
            return _esc(w["before"].format(a=rest[0], b=rest[1]))
        if kind == "hold" and " out@" in rest:
            # the hold box was already full: `J out@4` (out at the 4th placement), `T out@next`
            p, k = rest.split(" out@")
            # `next` is the next piece DEALT: the next bag's first when this bag places all its pieces,
            # else this bag's first unused one, which then stays held (山岳積み2号's 4-line PCs)
            if k == "next" and unused:
                words = w["hold_out_next_unused"].format(p=p, q=unused[0])
            elif k == "next":
                words = w["hold_out_next"].format(p=p)
            else:
                words = w["hold_out"].format(p=p, k=k)
            return f'<span class="scp-hold" data-demo="{held_slug}">{_esc(words)}</span>'
        if kind == "hold":
            p, k = rest.split("@")
            return (f'<span class="scp-hold" data-demo="{held_slug}">'
                    f'{_esc(w["hold"].format(p=p, k=k))}</span>')
        if kind == "held":
            return f'<span class="scp-hold" data-demo="{held_slug}">{_esc(w["held"].format(p=rest))}</span>'
        if kind == "unused":
            return _esc(w["unused"].format(p=rest))
        raise SystemExit(f"{self.p.module}: unknown order reading {tok!r}")

    def _chain_words(self, chain, routes_by_id):
        """The chain as words; a PC pattern by its own short name, since its full name repeats its parent."""
        return self.DP["chain"].format(chain=" → ".join(
            f"PC 第 {routes_by_id[c]['index']} 款" if "list" in routes_by_id[c] else self.node_name(c, routes_by_id)
            for c in chain))

    def _demo_payload(self, d, demos, routes_by_id, name):
        locks = d["locks"]
        moments = []
        for e in d["events"]:
            q = e["lock"] + 1
            if e["kind"] == "PC":
                label = self.DP["pc"].format(n=q, lines=e["lines"])
                moments.append([q, 0, "pc", label])
            else:
                nm = RS.SPIN_NAMES.get((e["spin"], e["lines"]))
                self._need(nm is not None, f"{d['node']}: spin {e['spin']} with {e['lines']} lines has no name")
                moments.append([q, 0, "tspin", self.DP["spin"].format(n=q, name=nm)])
        notes = [self._chain_words(d["chain"], routes_by_id)]
        for b in d["bags"]:
            notes.append(self.DP["bag"].format(name=self.node_name(b["node"], routes_by_id), queue=b["queue"]))
        return {"label": demo_slug(d["node"]), "title": self.DP["now"].format(name=name),
                "seq": d["seq"], "order": "0" * len(locks), "winner": None,
                "players": [{"user": self.DP["user"], "slot": 0, "ending": None, "frames": d["frames"],
                             "pieces": len(locks), "locks": locks, "ge": [],
                             "verified_to": None, "after": None, "failed_at": None}],
                "moments": moments, "flags": [], "notes": notes}

    def render_demo_page(self, routes, demos):
        """`<prefix>-demos.html`: every drawn node's constructed demo, one player at a time."""
        by_id = {n["id"]: n for n in routes["nodes"]}
        bad = self.demo_problems(demos, routes)
        self._need(not bad, "; ".join(bad))
        built = {d["node"]: d for d in demos["demos"]}
        unbuilt = {u["node"]: u["reason"] for u in demos["unbuilt"]}
        order = [i for i in routes["page_order"] if i in by_id]
        for n in routes["nodes"]:
            if "rows" in n and n["id"] not in order:
                # a derived board (迷走砲's bag1.z_left) goes after the board it is derived beside
                order.insert(order.index(self.p.derived_after) + 1 if n["bag"] == 1 else len(order), n["id"])
        title = f"{self.DP['title']}{RS.TITLE_MARK}"
        shared = {"shapes": demos["shapes"], "width": demos["board"]["width"], "rows": demos["board"]["rows"],
                  "visible": demos["board"]["visible_rows"], "next": RS.NEXT_SHOWN, "flag_words": RS.FLAG_WORDS}
        rounds = {}
        with open(PAGE_JS, encoding="utf-8") as fh:
            page_js = fh.read().rstrip()
        self._need("</script" not in page_js.lower(), "stray_cannon_page.js may not contain a closing script tag")
        out = self._head(title, self.DP["desc"],
                    [self.DP["user"]], True)
        out += ['  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a>'
                f'<a href="{self.OVERVIEW}">{_esc(self.PROSE["overview_title"])}</a></nav>',
                '  <header class="scp-head">',
                f'    <div class="eyebrow">{RS.EYEBROW}</div>',
                f'    <h1 class="section-title">{_esc(title)}</h1>',
                f'    <p>{_esc(self.DP["lede"])}</p>',
                _source_line(routes),
                '  </header>',
                '  <div class="method-note">',
                f'    <p><strong>呢版唔屬於信任鏈，亦唔係對局。</strong>所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in (self.PS["source"],) + self.DEMO_SENTENCES]
        out.append("  </div>")
        out += [f'  <section id="{RS.SECTION_ID}" aria-labelledby="rpg-now">',
                '    <h2 class="rpg-now" id="rpg-now" aria-live="polite"></h2>',
                f'    <p class="scp-idle">{_esc(self.DP["idle"])}</p>',
                '    <p class="rpg-notes"></p>',
                f'    <p class="rpg-flag" hidden>{RS.FLAG_WORDS}</p>',
                f'    <p class="rpg-missing" hidden>{_esc(self.PROSE["missing"])}</p>',
                '    <noscript><p>重播要開 JavaScript 先用到。</p></noscript>',
                '    <div class="rpg-host"></div>',
                f'    <template id="{TEMPLATE_ID}">',
                *["  " + line for line in RS.player_box("", [self.DP["user"]], bands=False)],
                '    </template>',
                '  </section>',
                '  <div class="scp-grid scd-grid">']
        basic_k = {b["id"]: k + 1 for k, b in enumerate(routes["basic_form"])}
        for nid in order:
            n = by_id[nid]
            name = self.node_name(nid, by_id)
            slug = demo_slug(nid)
            if nid in built:
                d = built[nid]
                held = any(lk[5] for lk in d["locks"])
                rounds[slug] = self._demo_payload(d, demos, by_id, name)
                bits = [f'    <div class="scp-node" id="{slug}" data-demo-node="{_esc(nid)}" data-demo="built">',
                        f'<h4 class="scp-name">{_esc(name)}</h4>', board_svg(n["rows"], name, self.CLASSES),
                        f'<p><a class="scp-case" href="#{slug}" data-round="{slug}">{_esc(self.DP["play"])}</a></p>',
                        f'<p class="scp-tag">{_esc(self._chain_words(d["chain"], by_id))}</p>']
                for b in d["bags"]:
                    words = [self._order_words(t, slug, b["unused"]) for t in b["order_reading"]]
                    cond = by_id[b["node"]].get("condition")
                    met = (_esc(self.DP["met"].format(cond=self._condition_words(cond)))
                           if cond and "all" in cond and b["met"] else "")
                    bits.append(f'<p class="scp-cond">{_esc(self.DP["bag"].format(name=self.node_name(b["node"], by_id), queue=b["queue"]))}'
                                f'{met}{"；" + "；".join(words) if words else ""}</p>')
                ev = "，".join(m[3] for m in rounds[slug]["moments"])
                if ev:
                    bits.append(f'<p class="scp-cond">{_esc(self.DP["events"].format(events=ev))}</p>')
                for b in d["also"]:
                    bits.append(f'<p class="scp-tag">{_esc(self.DP["also"].format(k=basic_k[b]))}</p>')
                for rd in d["piece_readings"]:
                    bits.append(f'<p class="scp-tag">{_esc(self.DP["reading"].format(reason=rd["reason"]))}</p>')
                if any(t.startswith(("hold:", "held:")) for b in d["bags"] for t in b["order_reading"]) and not held:
                    raise SystemExit(f"{self.p.module}: {nid} names a hold its inputs never make")
                bits.append("</div>")
                out.append("".join(bits))
            else:
                self._need(nid in unbuilt, f"{nid}: neither a demo nor an unbuilt reason")
                out.append(f'    <div class="scp-node" id="{slug}" data-demo-node="{_esc(nid)}" data-demo="unbuilt">'
                           f'<h4 class="scp-name">{_esc(name)}</h4>{board_svg(n["rows"], name, self.CLASSES)}'
                           f'<p class="scp-count">{_esc(self.DP["unbuilt"].format(reason=unbuilt[nid]))}</p></div>')
        out.append("  </div>")
        island = {"shared": shared, "rounds": rounds,
                  "cases": [{"case": k, "round": k} for k in rounds]}
        out += _tail(island, (RS.player_js(), page_js))
        return "\n".join(out)

    def audit_demo_page(self, page, demos, routes):
        """The quarantine and player rules (one copy each, from replay_page), the 「hold」 rule widened
        only to demos whose inputs hold, completeness, and the end-state check run on what the page
        actually EMBEDS (its island), not on the artefact it was rendered from."""
        held = {demo_slug(d["node"]) for d in demos["demos"] if any(lk[5] for lk in d["locks"])}
        bad = (RP.audit_quarantine(page, self.DEMO_REQUIRED, DATA_ID) + RP.audit_player(page)
               + self.audit_text(page, held))
        blocks = _DEMO_BLOCK.findall(page)
        seen = [nid for nid, _st in blocks]
        if len(seen) != len(set(seen)):
            bad.append("a demo node appears twice on the demo page")
        want = {d["node"]: "built" for d in demos["demos"]}
        want.update({u["node"]: "unbuilt" for u in demos["unbuilt"]})
        if dict(blocks) != want:
            bad.append(f"the demo page's blocks are not every demo and every unbuilt node "
                       f"({sorted(set(dict(blocks).items()) ^ set(want.items()))[:3]})")
        m = _ISLAND.search(page)
        if not m:
            return bad + ["no data island on the demo page"]
        island = json.loads(m.group(1))
        if sorted(island["rounds"]) != sorted(demo_slug(d["node"]) for d in demos["demos"]):
            bad.append("the demo page does not embed every demo exactly once")
        by_id = {n["id"]: n for n in routes["nodes"]}
        for d in demos["demos"]:
            r = island["rounds"].get(demo_slug(d["node"]))
            if r is None:
                continue
            shown = dict(d, seq=r["seq"], locks=r["players"][0]["locks"])
            bad += [f"embedded {x}" for x in self._demo_end(shown, demos, by_id)]
        return bad

    def render_all(self, repo=REPO, inputs=None, demos=None):
        """{file name: page} for the overview, every node page and the demo page, each audited, plus
        the cross-page rules: every case is embedded once and indexed once, every demo link resolves."""
        routes, art, sessions = inputs or self.load_inputs(repo)
        demos = demos if demos is not None else self.load_demos(repo)
        self.check_inputs(routes, art)
        payloads = {}
        for c in art["cases"]:
            rk = round_key(c)
            if rk not in payloads:
                payloads[rk] = self._round_payload(sessions, c)
        pages, pos_of = {}, {}
        for slug, node in self.NODE_PAGES:
            page, pos = self.render_node_page(slug, node, routes, art, sessions, payloads, demos)
            pages[f"{self.p.prefix}-{slug}.html"] = page
            pos_of.update(pos)
        pages[self.OVERVIEW] = self.render_overview(routes, art, sessions, pos_of, demos)
        pages[self.DEMO_PAGE] = self.render_demo_page(routes, demos)
        for name, page in pages.items():
            self._no_simplified(page, name)
            size = len(page.encode())
            self._need(not self.p.max_page_bytes or size <= self.p.max_page_bytes,
                       f"{name} is {size} bytes, over the profile's {self.p.max_page_bytes}: split the page, "
                       "never drop cases")
        bad = self.audit_all(pages, art, demos, routes)
        self._need(not bad, "; ".join(bad))
        return pages

    def audit_text(self, page, held=()):
        """The %, 「hold」 and simplified-glyph rules, over the page's visible text. `held`: the demo
        slugs whose inputs press hold — only their own `scp-hold` span may say it."""
        bad = []
        vis = _visible(page)
        vis = _DEMO_HOLD_SPAN.sub(lambda m: "" if m.group(1) in held else m.group(0), vis)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        if "%" in _TAG.sub("", _SRC_QUOTE.sub("", vis)):
            bad.append("a % outside quoted source text — this page prints counts, never computed rates")
        held = _TAG.sub("", self._HOLD_SPAN.sub("", vis).replace(self.PS["bag1"], ""))
        if _HOLD.search(held):
            bad.append(f"「hold」 outside the {self.p.hold_node} row and the bag-1 sentence — only the hold-split "
                       "test earns it")
        return bad

    def audit_overview(self, page, art):
        bad = RP.audit_quarantine(page, self.OVERVIEW_REQUIRED, DATA_ID) + self.audit_text(page)
        want = {n["id"]: self.status_of(n)[0] for n in art["nodes"]}
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

    def audit_node_page(self, page, slug, node, art):
        bad = RP.audit_quarantine(page, self.NODE_REQUIRED, DATA_ID) + RP.audit_player(page) + self.audit_text(page)
        got = dict(_NODE_BLOCK.findall(page))
        for nid in self._subtree(slug, node, art):
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

    def audit_all(self, pages, art, demos, routes):
        bad = self.audit_overview(pages[self.OVERVIEW], art) + self.audit_demo_page(pages[self.DEMO_PAGE], demos, routes)
        built = {demo_slug(d["node"]) for d in demos["demos"]}
        for name, page in pages.items():
            for slug in self._DEMO_LINK.findall(page):
                if slug not in built:
                    bad.append(f"{name}: a link to {slug}, which is no demo")
        seen = []
        for slug, node in self.NODE_PAGES:
            page = pages[f"{self.p.prefix}-{slug}.html"]
            bad += self.audit_node_page(page, slug, node, art)
            seen += _CASE_ROW.findall(page)
        keys = sorted(case_key(c) for c in art["cases"])
        if sorted(seen) != keys:
            bad.append(f"the node pages do not embed every case exactly once ({len(seen)} embedded, "
                       f"{len(keys)} cases)")
        return bad

    def _selftest(self):
        inputs = self.load_inputs(REPO)
        art = inputs[1]
        demos = self.load_demos(REPO)
        routes0 = inputs[0]
        pages = self.render_all(REPO, inputs, demos)
        ov = pages[self.OVERVIEW]
        T = self.p.selftest_targets
        by_id = {n["id"]: n for n in routes0["nodes"]}
        ideal = f"{self.p.prefix}-{T['node_page']}.html"
        held = self.p.hold_piece
        elsewhere = T["elsewhere_node"]
        nohold = T["demo_never_holds"]
        nohold_h = f'data-demo="built"><h4 class="scp-name">{_esc(self.node_name(nohold, by_id))}'
        cases = [("control: the rendered pages", None, None, None)]

        def m(name, page_name, new, want):
            cases.append((name, page_name, new, want))

        m("a dropped route node", self.OVERVIEW, _drop_line(ov, f'data-node="{T["empty_node"]}"'), "missing from the overview")
        m("a dropped text_only node", self.OVERVIEW, _drop_line(ov, f'data-node="{T["text_only"]}"'), f'{T["text_only"]} is missing')
        m("a dropped unmatchable node", self.OVERVIEW, _drop_line(ov, f'data-node="{T["unmatchable"]}"'), f'{T["unmatchable"]} is missing')
        m("a dropped node on a node page", ideal, _drop_line(pages[ideal], f'data-node="{T["node_page_node"]}"'),
          f"missing from {T['node_page']}")
        first = art["cases"][0]
        m("a dropped case row on a node page", f"{self.p.prefix}-{self.page_of(first)}.html",
          _drop_line(pages[f"{self.p.prefix}-{self.page_of(first)}.html"], f'data-case="{case_key(first)}"'), "exactly once")
        m("a dropped case in the overview index", self.OVERVIEW, _drop_line(ov, f'data-case="{case_key(first)}"'), "every case exactly once")
        m("a claim badge", self.OVERVIEW, ov.replace(RS.TITLE_MARK, RS.TITLE_MARK + '<span class="claim-badge">✓</span>', 1), "claim badge")
        m("a data-claim on a node page", ideal, pages[ideal].replace('class="scp-cases"', 'class="scp-cases" data-claim="C001"', 1), "claim badge")
        m("an external src=", ideal, pages[ideal].replace("<script>", '<script src="x.js"></script><script>', 1), "external request")
        m("an innerHTML assignment", ideal, pages[ideal].replace('"use strict";', '"use strict"; document.body.innerHTML = "";', 1), "assigns markup")
        m("a simplified glyph", self.OVERVIEW, ov.replace("第一巡</h2>", "第一巡这</h2>", 1), "simplified glyph")
        m("a second data island", self.OVERVIEW, ov.replace("</body>", f'<script type="application/json" id="{DATA_ID}">{{}}</script></body>', 1), "data island")
        m("a computed percentage", self.OVERVIEW, re.sub(r'(<p class="scp-count">\d+ / \d+)', r"\1（12.5%）", ov, count=1), "a % outside quoted")
        m("an unguarded writeHash(p) on a node page", ideal, pages[ideal].replace("if (!playing) writeHash(p)", "writeHash(p)", 1), "while playing")
        m("QUIET_BEFORE_DESTROY reordered", ideal, pages[ideal].replace(
            RP.QUIET_BEFORE_DESTROY, "if (handle) { handle.destroy(); handle = null; }\n    quiet = true;", 1), "OLD round")
        m(f"「hold」 added to the {elsewhere.split('.')[-1]} row", self.OVERVIEW, re.sub(
            r'(data-node="' + re.escape(elsewhere) + r'".*?<p class="scp-count">)', r"\1hold 咗 " + held + " · ",
            ov, count=1),
          "「hold」 outside")
        m("a node page missing BOUNDARY_SENTENCE", ideal, pages[ideal].replace(RS.BOUNDARY_SENTENCE, ""), "quarantine sentence")
        m("a node page missing a PAGE_SENTENCE", ideal, pages[ideal].replace(self.PS["mirror"], ""), "quarantine sentence")
        m("a status that disagrees with the artefact", self.OVERVIEW, ov.replace(
            f'data-node="{T["empty_node"]}" data-status="empty"', f'data-node="{T["empty_node"]}" data-status="count"', 1),
          "the artefact says")
        dp = pages[self.DEMO_PAGE]
        m("the demo page missing its not-a-game sentence", self.DEMO_PAGE, dp.replace(self.DS["demo"], ""), "quarantine sentence")
        m("a data-claim in a demo block", self.DEMO_PAGE, dp.replace('data-demo="built">', 'data-demo="built" data-claim="C001">', 1), "claim badge")
        m("a demo block dropped", self.DEMO_PAGE, _drop_line(dp, f'data-demo-node="{T["demo_built"]}"'), "blocks are not every demo")
        m("an unbuilt reason dropped", self.DEMO_PAGE, _drop_line(dp, f'data-demo-node="{T["demo_unbuilt"]}"'),
          "blocks are not every demo")
        m("「hold」 on a demo that never holds", self.DEMO_PAGE, dp.replace(
            nohold_h + '</h4>',
            nohold_h + f'<span class="scp-hold" data-demo="{demo_slug(nohold)}">hold</span></h4>', 1),
          "「hold」 outside")
        m("an innerHTML assignment on the demo page", self.DEMO_PAGE, dp.replace('"use strict";', '"use strict"; document.body.innerHTML = "";', 1), "assigns markup")

        def moved(page):
            mm = _ISLAND.search(page)
            isl = json.loads(mm.group(1))
            lk = isl["rounds"][demo_slug(T["demo_built"])]["players"][0]["locks"]
            lk[-1][1] += 1
            return page[:mm.start(1)] + _island(isl) + page[mm.end(1):]
        m("a demo's last lock moved one column (the page's own board check)", self.DEMO_PAGE, moved(dp),
          f"embedded {T['demo_built']}")
        built_slug = demo_slug(T["demo_built"])
        m("a broken demo link on the overview", self.OVERVIEW, ov.replace(f"{self.DEMO_PAGE}#{built_slug}",
                                                                          f"{self.DEMO_PAGE}#{built_slug}99", 1), "which is no demo")

        ok = True
        for name, page_name, new, want in cases:
            if page_name is None:
                found = self.audit_all(pages, art, demos, routes0)
                good = not found
                applied = True
            else:
                applied = new != pages[page_name]
                found = self.audit_all({**pages, page_name: new}, art, demos, routes0)
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
            self.render_all(REPO, (routes, eligible, sessions))
            print("  BAD a report-eligible artefact rendered")
            ok = False
        except SystemExit as e:
            refused += 1
            print(f"  ok  a report-eligible artefact is refused: {str(e)[:60]}…")
        lost = json.loads(json.dumps(art0))
        lost["nodes"] = [n for n in lost["nodes"] if n["id"] != T["text_only"]]
        try:
            self.render_all(REPO, (routes, lost, sessions))
            print("  BAD an artefact missing a route node rendered")
            ok = False
        except SystemExit as e:
            refused += 1
            print(f"  ok  an artefact missing a route node is refused: {str(e)[:60]}…")
        # the artefact check: a demo whose last lock is moved, and one a node page no longer gets
        bent = json.loads(json.dumps(demos))
        d3 = next(d for d in bent["demos"] if d["node"] == T["demo_built"])
        d3["locks"][-1][1] += 1
        gone = json.loads(json.dumps(demos))
        gone["demos"] = [d for d in gone["demos"] if d["node"] != T["demo_missing"]]
        for what, a, want in (("a demo artefact's last lock moved", bent, T["demo_built"]),
                              ("a demo artefact missing a node", gone, T["demo_missing"])):
            got = self.demo_problems(a, routes0)
            good = any(want in g for g in got)
            ok &= good
            refused += 1
            print(f"  {'ok ' if good else 'BAD'} {what}: {got[:1]}")
        # demos whose last lock is a spin the end check reads off the lock (stick spin's bag-1 TSS boards
        # and its fallbacks fired into a separate spin board): the spin flag cleared must fail them
        for nid in T.get("demo_spin_last", ()):
            flat = json.loads(json.dumps(demos))
            dd = next(d for d in flat["demos"] if d["node"] == nid)
            dd["locks"][-1][3] = 0
            got = self.demo_problems(flat, routes0)
            good = any(nid in g and "is not the drawing's" in g for g in got)
            ok &= good
            refused += 1
            print(f"  {'ok ' if good else 'BAD'} {nid}'s last lock no longer a spin: {got[:1]}")
        # a list with its own line count (山岳積み2号's 4-line and 14-line PCs): checked at the profile's
        # count instead, its demos must fail — the per-list rule is not decorative
        # (a list whose own count equals the profile's — stick spin's 8 — makes that mutant equivalent, so
        # only the lists whose count DIFFERS are planted)
        own = [li["id"] for li in routes0["lists"] if ("total_lines" in li or "pc_lines" in li)
               and self.pc_lines_of(li["id"]) != self.p.pc_lines]
        if own:
            keep = self.pc_lines_of
            self.pc_lines_of = lambda _lid: self.p.pc_lines
            try:
                got = self.demo_problems(demos, routes0)
            finally:
                self.pc_lines_of = keep
            good = any(f"-line Perfect Clear" in g for g in got)
            ok &= good
            refused += 1
            print(f"  {'ok ' if good else 'BAD'} lists {own} checked at {self.p.pc_lines} lines: {got[:1]}")
        print(f"{'ok ' if ok else 'FAIL'} {self.p.module} selftest: {len(cases) - 1 + refused} "
              f"corruptions, {'all caught' if ok else 'SOME MISSED'}")
        return 0 if ok else 1

    def main(self, argv=None, doc=None):
        ap = argparse.ArgumentParser(description=(doc or __doc__).splitlines()[0])
        ap.add_argument("--out-dir")
        ap.add_argument("--selftest", action="store_true")
        a = ap.parse_args(argv)
        if a.selftest:
            return self._selftest()
        if not a.out_dir:
            ap.error("need --out-dir, or --selftest")
        os.makedirs(a.out_dir, exist_ok=True)
        for name, page in self.render_all(REPO).items():
            with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as fh:
                fh.write(page)
            print(f"wrote {os.path.join(a.out_dir, name)} ({len(page.encode())} bytes)")
        return 0

