"""TST 開局排名（T 先擺 / T 留 hold）: the bag-1 boards with the T placed AND the bag-1 boards with the T held, ranked
TOGETHER by how likely a random deal builds ANY two-bag TST shape holding the board and then clears a bag-3 Perfect Clear:
`docs/tst-openers.html`. A board is `kind` "placed" (six pieces, one of them the T, one other piece held) or "held" (the six
pieces IJLOSZ, the T in hold: `held == "T"`); one competition rank per budget over both kinds, and the kind bar only hides
cards, it never renumbers a rank.

    python3 -m pipeline.tst_openers_tp_page --out-dir /tmp/tst   # render it somewhere other than docs/
    python3 -m pipeline.tst_openers_tp_page --selftest           # the audit's mutants

The earlier ranking (T held in bag 1, one shape per card) is `pipeline/tst_openers_page.py`, kept as the reference page
`docs/tst-openers-held.html`. This page keeps that page's UX (cards with board drawings, a 「睇晒」 detail row per card,
folded worked Perfect Clears, a filter bar, a ranking table) and reuses its drawing, replay and rounding functions
instead of copying them.

Inputs: `analysis/tst-openers-tp.json` (the counter's per-board cumulative counts, `pipeline/sim/emit-tst-openers-tp.py`),
`analysis/tst-openers.json` and `pipeline/openers/tst-openers-shapes.json` (the shapes: names, cells, tilings, residue
rows) and `analysis/tst-openers-tp-pc-examples.json` (the worked PCs). The artefact is CONSTRUCTED and quarantined:
nobody played these boards, no claim id, no badge. Nothing is stored as a figure: built = cum_inf[-1] / 5040^2 and
the bag-3 PC chance of a budget k is sum(delta_k * p5) / 5040^3, from `cum` and `classes`.

The audit (inside `render_all`) reuses `replay_page.audit_quarantine` and adds: the cards are exactly the ranked pairs
in order; every card figure, every budget, the mirror board's figures, the ranks (printed only above the pruning
threshold, where ranks are complete) and the orders are RECOMPUTED by a second route straight from `cum` and `classes`;
the artefact's `classes` equal what the shapes' tilings holding the board give; the drawn tiling holds the board; every
worked PC replays from the card's residue; the printed pruning numbers are the artefact's; the data island is what the
renderer builds; no simplified glyph, no external request, no markup sink.

ROUNDING: every percentage is FLOORED (`tst_openers_page.pct`), computed in exact fractions.
"""
import collections
import glob
import argparse
import base64
import copy
import hashlib
import itertools
from decimal import Decimal
import html
import itertools
import json
import os
import re
import shutil
import sys
import tempfile
import zlib
from html.parser import HTMLParser
from fractions import Fraction

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import tst_openers_page as OP
from pipeline.claims.build_claims import SIMPLIFIED

HERE = OP.HERE
REPO = OP.REPO
OVERVIEW = "tst-openers.html"
HELD_PAGE = OP.OVERVIEW
PREFIX = OP.PREFIX
ART_PATH = os.path.join(REPO, "analysis", "tst-openers-tp.json")
PCX_PATH = os.path.join(REPO, "analysis", "tst-openers-tp-pc-examples.json")
PROSE_PATH = os.path.join(HERE, "tst_openers_tp_prose.json")
CSS_PATH = os.path.join(HERE, "tst_openers_tp_page.css")
JS_PATH = os.path.join(HERE, "tst_openers_tp_page.js")
SX_CSS_PATH = os.path.join(HERE, "tst_openers_tp_sets.css")
SX_JS_PATH = os.path.join(HERE, "tst_openers_tp_sets.js")
DATA_ID = OP.DATA_ID
BAG, N2, WALL = OP.BAG, OP.N2, OP.WALL
pct, _esc, _need = OP.pct, OP._esc, OP._need
BK = ["0", "1", "2", "inf"]          # the soft-drop budgets of the artefact, in its order
BK_SHOWN = "2"                       # the budget the page opens on (yachi 2026-11-23: 最多兩次 soft drop)
BK_SET = "inf"                       # the budget that decides which boards are ranked, the drawn class and family order
TABLE_BK = "1"                       # the budget the table ranks by
TABLE_SHOWN = 15
ORDER = "IJLOSTZ"
SW = {"J": "L", "L": "J", "S": "Z", "Z": "S"}
ID_OFFSET = 1000
KINDS = ("placed", "held")
_CARDKIND = re.compile(r'<article class="card[^"]*" data-pos="[^"]*" data-card="([^"]+)" data-rk="[^"]*" data-kind="(\w+)"')
_KBTN = re.compile(r'<button aria-pressed="\w+" data-k="(\w+)">(.*?)</button>', re.S)
_CARD = re.compile(r'<article class="card[^"]*" data-pos="[^"]*" data-card="([^"]+)" data-rk="([^"]*)"[^>]*>(.*?)</article>', re.S)
_TROW = re.compile(r'<tr data-p3="([^"]+)">(.*?)</tr>', re.S)
_IROW = re.compile(r'<tr data-inc="([^"]+)">(.*?)</tr>', re.S)
_G = re.compile(r'data-g="(\w+)">(.*?)</td>', re.S)
_PR = re.compile(r'<b data-pr="(\w+)">(.*?)</b>', re.S)
_MIR = re.compile(r'<div class="muted sm mir" data-same="([01])">(.*?)</div>', re.S)
_MF = re.compile(r'<b data-m="(\w+)">(.*?)</b>', re.S)


# ------------------------------------------------------------------ the catalogue (originals + mirrors)

def mirror_kind(k):
    return SW.get(k, k)


def mirror_cell(c):
    return (c // 10) * 10 + 9 - c % 10


def mirror_pieces(ps):
    return sorted(([mirror_kind(k), sorted(mirror_cell(c) for c in cs)] for k, cs in ps), key=lambda p: (p[0], p[1]))


def mirror_left(l):
    return "".join(sorted((mirror_kind(c) for c in l), key=ORDER.index))


def mirror_row(r):
    return int(format(r, "010b")[::-1], 2)


def piece_set(ps):
    return frozenset((k, tuple(sorted(cs))) for k, cs in ps)


def load_inputs(repo=REPO):
    """(artefact, catalogue): `catalogue[sid]` = dict(names, cells, tst, rows, til=[dict(pieces, left, B, p5, set)]) for the
    121 transcribed shapes and the mirror shapes the artefact lists (id 1000 + the original's), the mirror's tilings in the
    original's order with the counter's own B and p5. Refuses an artefact built from other inputs."""
    with open(os.path.join(repo, "analysis", "tst-openers-tp.json"), "rb") as f:
        raw = f.read()
    art = json.loads(raw)
    _need(art["schema"] == "tst-openers-tp/5" and art["report_eligible"] is False and art["constructed"] is True
          and "families" in art,
          "the artefact is not tst-openers-tp/5 (with families) marked report_eligible: false / constructed: true")
    with open(os.path.join(repo, "analysis", "tst-openers-tp-x.json"), encoding="utf-8") as f:
        x = json.load(f)
    _need(x["schema"] == "tst-openers-tp-x/1" and x["report_eligible"] is False and x["constructed"] is True
          and art["md5"].get("x") == hashlib.md5(json.dumps(x, sort_keys=True, separators=(",", ":"),
                                                             ensure_ascii=False).encode()).hexdigest(),
          "analysis/tst-openers-tp.json's families were built from another analysis/tst-openers-tp-x.json")
    with open(os.path.join(repo, "analysis", "tst-openers.json"), "rb") as f:
        old_raw = f.read()
    _need(art["md5"]["tst_openers"] == hashlib.md5(old_raw).hexdigest(),
          "analysis/tst-openers-tp.json was built from another analysis/tst-openers.json")
    old = json.loads(old_raw)
    with open(os.path.join(repo, "pipeline", "openers", "tst-openers-shapes.json"), encoding="utf-8") as f:
        shp = json.load(f)
    by = {s["id"]: s for s in shp["shapes"]}
    cat = {}
    for o in old["shapes"]:
        s = by[o["id"]]
        cat[o["id"]] = dict(names=list(s["names"]), cells=s["cells"], tst=s["tst"], rows=o["rows"],
                            til=[dict(pieces=t["pieces"], left=t["left"], B=t["B"], p5=t["p5"], set=piece_set(t["pieces"]))
                                 for t in o["til"]])
    sfx = art["mirror"]["suffix"]
    for ms in art["mirror_shapes"]:
        o = cat[ms["mirror_of"]]
        _need(ms["id"] == ID_OFFSET + ms["mirror_of"] and len(ms["til"]) == len(o["til"]), f"mirror shape {ms['id']} does not align")
        til = []
        for t, (_a, b, p5) in zip(o["til"], ms["til"]):
            ps = mirror_pieces(t["pieces"])
            til.append(dict(pieces=ps, left=mirror_left(t["left"]), B=b, p5=p5, set=piece_set(ps)))
        cat[ms["id"]] = dict(names=[n + sfx for n in o["names"]], cells=sorted([9 - x, y] for x, y in o["cells"]),
                             tst=sorted([9 - x, y] for x, y in o["tst"]), rows=[mirror_row(r) for r in o["rows"]], til=til)
    lib = bag1_library(repo)
    for b in art["boards"]:
        _need(all(s in cat for s in b["shapes"]), f"board {b['name']} names a shape outside the catalogue")
        b["kind"] = "held" if b["held"] == "T" else "placed"
        b["b1"] = bag1_names(b, lib)
    for b in x["boards"]:
        _need(all(s in cat for s in b["shapes"]), f"extra board {b['name']} names a shape outside the catalogue")
        b["kind"] = "held" if b["held"] == "T" else "placed"
        b["b1"] = bag1_names(b, lib)
    art["xboards"] = x["boards"]
    return art, cat


def all_boards(art):
    """name -> board over the kept boards and the extra ones (`analysis/tst-openers-tp-x.json`: the variants of a family
    layout the pruning dropped, counted so the family figures are exact). Extra boards have no card and no rank."""
    by = {b["name"]: b for b in art["boards"]}
    for b in art.get("xboards", []):
        by[b["name"]] = b
    return by


def load_prose(path=PROSE_PATH):
    return OP.load_prose(path)


def load_pcx(repo=REPO):
    """The worked PCs of this page (`emit-tst-pc-examples.py --tp`), keyed by `rows|left`; refuses an artefact built from
    another analysis/tst-openers-tp.json."""
    with open(os.path.join(repo, "analysis", "tst-openers-tp-pc-examples.json"), encoding="utf-8") as f:
        ex = json.load(f)
    _need(ex.get("report_eligible") is False and ex.get("constructed") is True,
          "the PC examples artefact is not marked report_eligible: false / constructed: true")
    with open(os.path.join(repo, "analysis", "tst-openers-tp.json"), "rb") as f:
        _need(ex["md5"]["tst_openers_tp"] == hashlib.md5(f.read()).hexdigest(),
              "the PC examples artefact was built from another analysis/tst-openers-tp.json: re-run emit-tst-pc-examples.py --tp")
    return {e["line"]: e for e in ex["examples"]}


def load_builds(repo=REPO):
    """The engine-checked placement order of every live class (`emit-tst-builds.py`), keyed `<card>#<class index>`;
    refuses an artefact built from another analysis/tst-openers-tp.json."""
    with open(os.path.join(repo, "analysis", "tst-openers-tp-builds.json"), encoding="utf-8") as f:
        bd = json.load(f)
    _need(bd.get("report_eligible") is False and bd.get("constructed") is True,
          "the builds artefact is not marked report_eligible: false / constructed: true")
    with open(os.path.join(repo, "analysis", "tst-openers-tp.json"), "rb") as f:
        _need(bd["md5"]["tst_openers_tp"] == hashlib.md5(f.read()).hexdigest(),
              "the builds artefact was built from another analysis/tst-openers-tp.json: re-run emit-tst-builds.py")
    for key, v in bd["builds"].items():
        _need(v.get("order") is not None, f"build {key}: the engine found no placement order")
        _need(v.get("tst") is True, f"build {key}: the engine did not confirm the T reaches the TST slot with a full spin")
    return bd["builds"]


def load_orders(repo=REPO):
    """Which dealt orders of bag 2 build each live class (`emit-tst-orders.py`), keyed `<card>#<class index>`; refuses an
    artefact built from another analysis/tst-openers-tp.json."""
    with open(os.path.join(repo, "analysis", "tst-openers-tp-orders.json"), encoding="utf-8") as f:
        od = json.load(f)
    _need(od.get("report_eligible") is False and od.get("constructed") is True,
          "the orders artefact is not marked report_eligible: false / constructed: true")
    with open(os.path.join(repo, "analysis", "tst-openers-tp.json"), "rb") as f:
        _need(od["md5"]["tst_openers_tp"] == hashlib.md5(f.read()).hexdigest(),
              "the orders artefact was built from another analysis/tst-openers-tp.json: re-run emit-tst-orders.py")
    _need(od["pairs"] == ["".join(p) for p in itertools.combinations("IJLOSTZ", 2)], "the orders artefact's pair list")
    _need(od.get("schema") == "tst-openers-tp-orders/4", "the orders artefact's schema: re-run emit-tst-orders.py")
    _need(set(od.get("no180") or {}) == {"orders", "plans"}, "the orders artefact has no no180 section")
    for tag, sec, pairs in (("", od, True), ("no180 ", od["no180"], False)):
        if not pairs:
            _need(set(sec["orders"]) == set(od["orders"]) and set(sec["plans"]) == set(od["plans"]),
                  "the no180 section's keys are not the 180 section's")
        for key, v in sec["orders"].items():
            n = v["n"]
            _need(len(n) == 4 and 0 <= n[0] <= n[1] <= n[2] <= n[3] <= BAG, f"{tag}orders {key}: n must be non-decreasing in 0..5040")
            if pairs:
                _need(n[3] > 0, f"orders {key}: a live class no order builds")
                _need(len(v["pairs"]) == 21 and all(0 <= a <= n[3] for a in v["pairs"]), f"orders {key}: a pair count out of 0..n_inf")
            else:
                _need("pairs" not in v, f"{tag}orders {key}: pairs")
        for card, pl in sec["plans"].items():
            _need(set(pl) == {"steps", "else", "open", "none"}, f"{tag}plan {card}: keys")
            for i, rs, tot in pl["steps"]:
                _need(f"{card}#{i}" in sec["orders"] and rs and tot == sum(n for _c, n in rs), f"{tag}plan {card}: step {i}")
            _need(pl["else"] is None or f'{card}#{pl["else"][0]}' in sec["orders"], f"{tag}plan {card}: the else class")
    return od


def card_plan(od, r):
    """The card's decision list for the island: {s: [[tile j, rules, total], ...], e: [tile j, n] or None, o: open,
    z: none}, a class index read as its tile's position among the live classes. `od` is a section of the orders artefact:
    the artefact itself (180 allowed) or its `no180` part."""
    lv = live(r)
    pl = od["plans"][r["name"]]
    return dict(s=[[lv.index(i), rs, tot] for i, rs, tot in pl["steps"]],
                e=[lv.index(pl["else"][0]), pl["else"][1]] if pl["else"] else None, o=pl["open"], z=pl["none"])


_PERMS = None


def order_perms():
    """IOTSZJL's permutations in the counter's order (remove the i-th of the rest, recurse): order i of `w`."""
    global _PERMS
    if _PERMS is None:
        out = []

        def r(pre, rest):
            if not rest:
                out.append(pre)
                return
            for i in range(len(rest)):
                r(pre + rest[i], rest[:i] + rest[i + 1:])
        r("", "IOTSZJL")
        _PERMS = out
    return _PERMS


# ------------------------------------------------------------------ figures

def deltas(b, k):
    c = b["cum"][k]
    return [c[i] - (c[i - 1] if i else 0) for i in range(len(c))]


def figs(b, k):
    """(built, pc3n, joint) of board `b` at budget `k`, exact: built = cum[-1] / 5040^2, joint = sum(delta * p5) / 5040^3
    (the chance that bag 1 as drawn and a random bag 2 build a shape AND bag 3 clears), pc3 = joint / built."""
    d = deltas(b, k)
    n = sum(d[i] * p5 for i, (_s, _l, p5) in enumerate(b["classes"]))
    return Fraction(b["cum"][k][-1], N2), n, Fraction(n, N2 * BAG)


def strings(b):
    """budget -> (two-bag built, bag-3 PC given built, joint) display strings; 未計 where nothing is built."""
    out = {}
    for k in BK:
        built, n, joint = figs(b, k)
        out[k] = [pct(built), pct(Fraction(n, b["cum"][k][-1] * BAG)) if built else "未計", pct(joint)]
    return out


def tstrings(b, pt):
    """budget -> [TST->TSD->PC given built, TST->TSD->PC joint] display strings, `pt` the per-class count of the 5040 bag-3
    orders whose PC plan holds a full T-spin Double (analysis/tst-openers-tp-tsd.json); 未計 where nothing is built."""
    out = {}
    for k in BK:
        d = deltas(b, k)
        n = sum(x * p for x, p in zip(d, pt))
        out[k] = [pct(Fraction(n, b["cum"][k][-1] * BAG)) if b["cum"][k][-1] else "未計", pct(Fraction(n, N2 * BAG))]
    return out


def live(b):
    """The classes some budget ends a deal on (a nonzero delta): the artefact lists every leftover class of every shape
    the board is listed by, and a class no tiling holding the board has gets no deal."""
    ds = [deltas(b, k) for k in BK]
    return [i for i in range(len(b["classes"])) if any(d[i] for d in ds)]


def holders(cat, b):
    """class index -> the first tiling (of the class's shape) that holds the board, has that leftover and a nonzero count;
    only for the live classes."""
    bs = piece_set(b["pieces"])
    out = {}
    for i in live(b):
        si, left, p5 = b["classes"][i]
        for t in cat[b["shapes"][si]]["til"]:
            if t["B"] > 0 and t["left"] == left and t["p5"] == p5 and bs <= t["set"]:
                out[i] = t
                break
    return out


def shown_class(b):
    """The class a card draws: the largest share of the joint (delta_inf * p5), the earliest on a tie."""
    d = deltas(b, BK_SET)
    return max(range(len(d)), key=lambda i: (d[i] * b["classes"][i][2], -i))


def mirror_index(art):
    by = {b["name"]: b for b in art["boards"]}
    for b in art["boards"]:
        m = by[b["mirror"]]
        _need(m["mirror"] == b["name"] and m is not b and mirror_board_key(b) == board_key(m["pieces"]),
              f"board {b['name']}: the mirror is not an involution onto the mirrored pieces")
    return by


def board_key(ps):
    return tuple(sorted((k, tuple(sorted(cs))) for k, cs in ps))


def mirror_board_key(b):
    return board_key(mirror_pieces(b["pieces"]))


ROUTE = {"meisou": "迷走砲", "honeycup": "はちみつ砲", "mountainous2": "山岳積み2号", "stickspin": "stick spin",
         "gamushiro": "ガムシロ積み", "hdgamushiro": "ガムシロ積み（harddrop）", "sdpcspin": "SDPC Spin"}


def route_of(name):
    """The route-page key a shape name starts with (`meisou 2.ideal` -> meisou), else None."""
    w = name.split(" ", 1)[0]
    return w if w in ROUTE else None


# --- bag 1: which named opener's first bag the board is -------------------------------------------------------------
B1_SW = {"J": "L", "L": "J", "S": "Z", "Z": "S"}
B1_WIKI = {"山岳積み2": "山岳積み2号", "山岳積み3": "山岳積み3号"}


def _b1_cells(rows):
    """{(x, y): LETTER} of a drawing, y counted from its bottom row."""
    out = {}
    for i, r in enumerate(rows):
        for x, c in enumerate(r):
            if c not in "-._ ":
                out[(x, len(rows) - 1 - i)] = c.upper()
    return out


def _b1_norm(cells):
    my = min(y for _, y in cells)
    return frozenset(((x, y - my), c) for (x, y), c in cells.items())


def _b1_mirror(cells, swap=True):
    return {(9 - x, y): (B1_SW.get(c, c) if swap else c) for (x, y), c in cells.items()}


def _b1_cat_name(n):
    """`ITO Cannon {JP: 糸砲} / Mountainous Stacking {…}` -> `ITO Cannon / Mountainous Stacking`."""
    return " / ".join(re.sub(r"\s*\{.*?\}", "", part).strip() for part in n.split(" / "))


def bag1_library(repo=REPO):
    """[(name, source, by_letter, normalised drawing, kind)] of every named opener's bag-1 board, as drawn and mirrored:
    route pages and harddrop's fields by letter, Ivan's catalogue by occupancy only. A 24-cell drawing holding a T is a
    `placed` board (the T is one of the six pieces); a 24-cell drawing with NO T, and a 28-cell drawing less its T cells,
    is a `held` board (the six pieces IJLOSZ, the T in hold). A held entry is matched only to held boards."""
    lib = []

    def add(nm, src, by_letter, c, cc_swap=True):
        n = len(c)
        has_t = "T" in c.values()
        if n == 24 and has_t:
            kinds = [("placed", c)]
        elif n == 24:
            kinds = [("held", c)]
        elif n == 28 and has_t:
            kinds = [("held", {p: v for p, v in c.items() if v != "T"})]
        else:
            return None
        for kind, cc0 in kinds:
            if len(cc0) != 24:
                continue
            for cc in (cc0, _b1_mirror(cc0, cc_swap)):
                lib.append((nm, src, by_letter, _b1_norm(cc), kind))
        return True

    for fn in sorted(glob.glob(os.path.join(repo, "pipeline", "openers", "*-routes.json"))):
        key = os.path.basename(fn)[:-len("-routes.json")]
        if key not in ROUTE:
            continue
        with open(fn, encoding="utf-8") as f:
            r = json.load(f)
        for n in r["nodes"]:
            if n.get("bag") != 1 or "rows" not in n:
                continue
            c = _b1_cells(n["rows"])
            add(ROUTE[key].replace("（harddrop）", ""), "route", True, c)
    with open(os.path.join(repo, "pipeline", "openers", "wiki-openers.json"), encoding="utf-8") as f:
        w = json.load(f)
    for op in w["openers"]:
        for fd in op["fields"]:
            add(B1_WIKI.get(op["jp"], op["jp"]), "harddrop", True, _b1_cells(fd["rows"]))
    with open(os.path.join(repo, "pipeline", "openers", "opener-fields.json"), encoding="utf-8") as f:
        o = json.load(f)
    for pg in o["pages"]:
        c = _b1_cells(pg["rows"])
        if len(c) != 24 or any(v == 10 for v in collections.Counter(y for _, y in c).values()):
            continue
        # the catalogue draws occupancy only (no letters), so a 24-cell page is the same shape for either kind
        for kd in KINDS:
            for cc in (c, _b1_mirror(c, False)):
                lib.append((_b1_cat_name(pg["name"]), "catalogue", False, _b1_norm(cc), kd))
    return lib


def bag1_names(b, lib):
    """(names whose bag 1 equals the board letter for letter, catalogue names equal by occupancy only), each deduplicated."""
    c = {}
    for k, cs in b["pieces"]:
        for i in cs:
            c[(i % 10, i // 10)] = k
    f = _b1_norm(c)
    occ = frozenset(p for p, _ in f)
    ex, same = [], []
    for nm, _src, by_letter, d, kd in lib:
        if kd != b["kind"]:
            continue
        if by_letter and d == f and nm not in ex:
            ex.append(nm)
        elif not by_letter and frozenset(p for p, _ in d) == occ and nm not in same:
            same.append(nm)
    return ex, same


def routed(cat, b):
    """How many of the board's source (non-mirror) shapes carry a route-page name."""
    return sum(1 for s in b["shapes"] if s < ID_OFFSET and any(route_of(n) for n in cat[s]["names"]))


def rep_key(b, cat):
    return (-routed(cat, b), sum(1 for s in b["shapes"] if s >= ID_OFFSET), -figs(b, BK_SET)[2], b["name"])


def pairs(art, cat):
    """One entry per mirror pair: (representative, partner). The representative is the board with more source shapes that
    have a route-page name (so the card carries the opener's name), then the one listed by fewer mirror shapes (so the
    drawn source diagram is the one a person recognises), then the higher unlimited joint, then the name."""
    by = mirror_index(art)
    seen, out = set(), []
    for b in art["boards"]:
        if b["name"] in seen:
            continue
        m = by[b["mirror"]]
        seen |= {b["name"], m["name"]}
        r, p = sorted([b, m], key=lambda x: rep_key(x, cat))
        out.append((r, p))
    return out


def swap_keys(b):
    """The board's hold-swap keys: for each placed non-T piece X, (the other pieces with their cells, {X, held}). Two boards
    sharing a key are the same board but one piece, which one board places and the other holds: a hold swap."""
    ps = {k: tuple(sorted(c)) for k, c in b["pieces"]}
    out = set()
    for x in ps:
        if x == "T":
            continue
        out.add((tuple(sorted((k, c) for k, c in ps.items() if k != x)), frozenset({x, b["held"]})))
    return out


def fam_figs(L, k):
    """(built, pc3n, joint) of family layout `L` at budget `k`, exact: built = built_n / 5040^2, joint = pc3_n / 5040^3.
    The artefact's own counts under the joint-maximising policy; the policy is the artefact's `families.policy`."""
    bn, pn = L["num"][k]
    return Fraction(bn, N2), pn, Fraction(pn, N2 * BAG)


def fam_strings(L, k):
    """(built, PC given built, joint) display strings of a family at budget `k`, floored; 未計 where nothing is built."""
    built, n, joint = fam_figs(L, k)
    bn = L["num"][k][0]
    return [pct(built), pct(Fraction(n, bn * BAG)) if bn else "未計", pct(joint)]


def pair_of(art, a, b):
    """The artefact's `families.pairs` entry of the mirror pair {a, b}: the policy over the two hands."""
    for P in art["families"]["pairs"]:
        if set(P["boards"]) == {a, b}:
            return P
    raise KeyError((a, b))


def fl_spans(fmt, L):
    """One span per budget (`data-fl`, the budget bar switches them) of a `fam_line`-shaped sentence over policy counts `L`."""
    return "".join(f'<span data-fl="{k}"{"" if k == BK_SHOWN else " hidden"}>'
                   f'{_esc(fmt.format(a=fam_strings(L, k)[0], b=fam_strings(L, k)[1], c=fam_strings(L, k)[2]))}</span>' for k in BK)


def families(art, cat):
    """Hold-swap families are the artefact's layouts (`families.list`). Returns (name -> indices of the layouts listing the
    board, name -> its pair's representative board). The artefact is read, never recomputed here: the family counts need the
    bag-1 vectors (`analysis/tst-openers-tp-b1.json`), which the emitter's `--validate` and the test recompute."""
    by_name = {}
    for i, L in enumerate(art["families"]["list"]):
        for n in L["variants"]:
            by_name.setdefault(n, []).append(i)
    rep_of = {}
    for r, p in pairs(art, cat):
        rep_of[r["name"]] = r
        rep_of[p["name"]] = r
    return by_name, rep_of


def card_layouts(r, m, art, by_name):
    """The layouts of a card's mirror pair, one per mirror class, the best first (larger joint at the opening budget,
    then the lower index)."""
    lst = art["families"]["list"]
    seen = {}
    for i in sorted(set(by_name.get(r["name"], [])) | set(by_name.get(m["name"], []))):
        seen.setdefault(min(i, lst[i]["mirror"]), i)
    return sorted(seen.values(), key=lambda i: (-lst[i]["num"][BK_SET][1], i))


def fam_block(r, m, fam, rkmap, cat, art, PR):
    """The card's best family: each variant's own joint per budget, its rank and the orders the policy gives it, then the
    family's own line. A variant the pruning dropped (an extra board) prints its own joint, no rank and no link."""
    C = PR["card"]
    by_name, rep_of = fam
    idx = card_layouts(r, m, art, by_name)
    if not idx:
        return ""
    lst = art["families"]["list"]
    L = lst[idx[0]]
    byn = all_boards(art)
    sfx = art["mirror"]["suffix"]
    head = "".join(f"<th>{_esc(h)}</th>" for h in C["fam_cols"])

    def spans(vals):
        return "".join(f'<span data-fl="{k}"{"" if k == BK_SHOWN else " hidden"}>{v}</span>' for k, v in zip(BK, vals))
    rows = []
    for j, vn in enumerate(L["variants"]):
        v = byn[vn]
        rep = rep_of.get(vn, v)
        rk = rkmap.get(rep["name"], "–")
        if v is not rep:
            rk = C["fam_mirror"].format(rk=rk)
        nm = _esc(board_title(cat, v, sfx, PR))
        if rep["name"] in rkmap and rep is not r:
            nm = f'<a href="#c{rep["name"]}">{nm}</a>'
        rows.append(f'<tr data-fv="{vn}"><td>{nm}</td>'
                    + "".join(f'<td class="num" data-fg="{k}">{pct(figs(v, k)[2])}</td>' for k in BK)
                    + f'<td class="num" data-fr="1">{rk}</td>'
                    + f'<td class="num" data-fp="1">{spans([L["pick"][k][j] for k in BK])}</td></tr>')
    rows.append(f'<tr data-ffam="1"><td><b>{_esc(C["fam_row"])}</b></td>'
                + "".join(f'<td class="num" data-ff="{k}">{fam_strings(L, k)[2]}</td>' for k in BK)
                + '<td class="num"></td>'
                + f'<td class="num" data-fs="1">{spans([sum(L["pick"][k]) for k in BK])}</td></tr>')
    line = "".join(f'<span data-fl="{k}"{"" if k == BK_SHOWN else " hidden"}>{_esc(C["fam_line"].format(a=fam_strings(L, k)[0], b=fam_strings(L, k)[1], c=fam_strings(L, k)[2]))}</span>'
                   for k in BK)
    both = f'<p class="sm fboth" data-fboth="1">{fl_spans(C["fam_both"], L["both"])}</p>'
    other = f'<p class="muted sm" data-fother="1">{_esc(C["fam_other"].format(n=len(idx) - 1))}</p>' if len(idx) > 1 else ""
    return (f'<details class="fam" data-fam="{idx[0]}"><summary>{_esc(C["fam_summary"].format(n=len(L["variants"])))}</summary>'
            f'<p class="muted sm">{_esc(C["fam_note"])}</p>'
            f'<div class="p3w"><table class="p3"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<p class="muted sm" data-fline="1">{line}</p>{both}{other}</details>')


def threshold(art):
    return Fraction(*art["prune"]["threshold"])


def ranked(art, cat):
    """The ranked pairs: those whose representative's unlimited joint is above the pruning threshold, best first. Above
    the threshold every board was counted, so a rank there is complete; at or below it uncounted boards could be higher."""
    th = threshold(art)
    rows = [(r, p) for r, p in pairs(art, cat) if figs(r, BK_SET)[2] > th]
    rows.sort(key=lambda x: (-figs(x[0], BK_SET)[2], x[0]["name"]))
    return rows


def unranked(art, cat):
    th = threshold(art)
    return [(r, p) for r, p in pairs(art, cat) if figs(r, BK_SET)[2] <= th]


def rank_data(art, R):
    """budget -> (rank strings by position in `R`, card order by position). A rank is 1 + the number of ranked pairs with
    a strictly larger joint at that budget, printed only above the threshold."""
    th = threshold(art)
    rk, od = {}, {}
    for k in BK:
        j = [figs(r, k)[2] for r, _ in R]
        rk[k] = [("#" + str(1 + sum(1 for x in j if x > j[i]))) if j[i] > th else "–" for i in range(len(R))]
        pos = sorted(range(len(R)), key=lambda i: (-j[i], i))
        od[k] = [pos.index(i) for i in range(len(R))]
    return rk, od


def card_rows(cat, b):
    """The detail rows of a card: per class its drawn tiling (bag-1 pieces solid, bag-2 lowercase), the shape's first name,
    the leftover, p5 and the share of all N2 deals that END on the class per budget (floored)."""
    bs = piece_set(b["pieces"])
    hd = holders(cat, b)
    ds = {k: deltas(b, k) for k in BK}
    rows = []
    for i in live(b):
        si, left, p5 = b["classes"][i]
        t = hd[i]
        rows.append([grid(t, bs), cat[b["shapes"][si]]["names"][0], left or "–", pct(Fraction(p5, BAG)),
                     *[pct(Fraction(ds[k][i], N2)) for k in BK]])
    return rows


def grid(t, bs):
    g = {}
    for k, cs in t["pieces"]:
        mine = (k, tuple(sorted(cs))) in bs
        for c in cs:
            g[c] = k if mine else k.lower()
    H = max(g) // 10 + 1
    return "".join("".join(g.get(y * 10 + x, ".") for x in range(10)) for y in range(H - 1, -1, -1))


def counts_line(b, k, C):
    """The counts under a card's figures at budget `k`: deals that build a shape, and the bag-3 PC fraction (exact ints)."""
    cum = b["cum"][k][-1]
    n = sum(d * p5 for d, (_s, _l, p5) in zip(deltas(b, k), b["classes"]))
    return C["counts"].format(bk=C["bk_" + k], cum=f"{cum:,}", n2=f"{N2:,}", p3n=f"{n:,}", p3d=f"{cum * BAG:,}")


CL_KEYS = ("od_title", "od_n", "od_n0", "od_held", "od_how", "od_before", "od_and", "od_count", "od_rmore", "od_note", "pl_title", "pl_if", "pl_or", "pl_then", "pl_else", "pl_always", "pl_open", "pl_none", "pl_here", "pl_tile", "pl_r180", "pl_n180", "pl_n180_note", "pl_n180_none", "pcx_b3", "pcx_left", "pcx_deal3", "pcx_hold", "pcx_none3",
           "cl_hint", "bo_title", "bo_note", "bo_b1", "bo_rest", "bo_tst", "bo_sd", "bo_step", "bo_first", "bo_prev", "bo_next",
           "bo_last", "bo_pc", "bo_pc_note", "bo_none", "bo_nobuild", "an_v3", "an_play", "an_pause", "an_speed",
           "an_slow", "an_mid", "an_fast", "an_seek", "an_clear", "an_left", "an_pcg", "an_pc_step", "an_pc_done", "an_static")


def tst_cells(s):
    """The T's cells of shape `s` (y*10+x, y=0 the floor), sorted."""
    return sorted(y * 10 + x for x, y in s["tst"])


def px_entry(rows, left, ex):
    """The island's worked PC of one line: residue rows, leftover, and per example its deal, height, the placed cells in the
    original frame ([x, y, piece, step]) and the plan's steps."""
    def one(deal, d, h, plan):
        placed, _ = OP.replay(rows, left, deal, h, plan)
        return [d, h, sorted([x, y, p, n] for (x, y), (p, n) in placed.items()), [[p, list(c), int(hd)] for p, c, hd in plan]]
    b3 = ex and ex["b3"]
    return dict(r=list(rows), l=left,
                b3=one(b3["deal"], [b3["deal"]], b3["h"], b3["plan"]) if b3 else None)


def build_data(art, cat, R, PR, builds, pcxd, orders, pt=None):
    rk, od = rank_data(art, R)
    cards, px = {}, {}
    for n, (r, _p) in enumerate(R):
        s = cat[r["shapes"][r["classes"][shown_class(r)][0]]]
        lv = live(r)
        bb, xx, oo, o1 = [], [], [], []
        for i in lv:
            si, left, p5 = r["classes"][i]
            b = builds.get(f'{r["name"]}#{i}')
            bb.append([[[k, list(c), sd] for k, c, sd in b["order"]], b["sd"]] if b else None)
            ln = class_line(cat, r, i)
            xx.append([tst_cells(cat[r["shapes"][si]]), ln, int(p5 >= BAG)])
            ky = f'{r["name"]}#{i}'
            nv = orders["orders"].get(ky, {}).get("n")
            if nv:
                oo.append([nv[0], nv[3], r["held"]])
            else:
                oo.append(None)
            n1 = orders["no180"]["orders"].get(ky, {}).get("n")
            o1.append([n1[0], n1[3], r["held"]] if n1 else None)
            if ln not in px:
                px[ln] = px_entry(cat[r["shapes"][si]]["rows"], left, pcxd.get(ln))
        cards[r["name"]] = dict(tst=s["tst"], f=strings(r), rk={k: rk[k][n] for k in BK}, o={k: od[k][n] for k in BK},
                                t=card_rows(cat, r), n1=len(r["pieces"]), b=bb, x=xx, d=oo, pl=card_plan(orders, r),
                                d1=o1, pl1=card_plan(orders["no180"], r), kind=r["kind"],
                                cnt={k: counts_line(r, k, PR["card"]) for k in BK})
        if pt is not None:
            cards[r["name"]]["ft"] = tstrings(r, pt[r["name"]])
    return dict(labels=PR["labels"], bk=BK, filter_default=PR["pos_centre"], kind_default=KIND_DEFAULT, sd_default=BK_SHOWN, cards=cards, px=px,
                cl={k: PR["card"][k] for k in CL_KEYS})


# ------------------------------------------------------------------ pcx lines

def shown_line(cat, b):
    """`rows|left` of the card's drawn class: the shape's residue rows and the leftover."""
    i = shown_class(b)
    s = cat[b["shapes"][b["classes"][i][0]]]
    return ",".join(map(str, s["rows"])) + "|" + b["classes"][i][1]


def class_line(cat, b, i):
    """`rows|left` of class `i` of board `b`: its shape's residue rows and the leftover."""
    s = cat[b["shapes"][b["classes"][i][0]]]
    return ",".join(map(str, s["rows"])) + "|" + b["classes"][i][1]


def pcx_lines(art=None, repo=REPO):
    """The worked-PC line of every live class of every ranked card (the shown one first), unique, in card order
    (`emit-tst-pc-examples.py --tp` solves these)."""
    a, cat = load_inputs(repo)
    seen, out = set(), []
    for r, _ in ranked(art or a, cat):
        for ln in [shown_line(cat, r)] + [class_line(cat, r, i) for i in live(r)]:
            if ln not in seen:
                seen.add(ln)
                out.append(ln)
    return out


# ------------------------------------------------------------------ drawing

def svg2(cells, H, cs=15, tst=()):
    """`tst_openers_page.svg` with lower-case letters (bag-2 pieces) drawn lighter than the upper-case bag-1 ones."""
    W = 10
    r = [f'<svg class="board" width="{W * cs}" height="{H * cs}" viewBox="0 0 {W * cs} {H * cs}" role="img">',
         f'<rect width="{W * cs}" height="{H * cs}" fill="var(--well)"/>']
    for x in range(W):
        for y in range(H):
            r.append(f'<rect x="{x * cs + .5}" y="{(H - 1 - y) * cs + .5}" width="{cs - 1}" height="{cs - 1}" fill="var(--grid)"/>')
    for (x, y), k in cells.items():
        op = "" if k.isupper() else ' opacity=".55"'
        r.append(f'<rect x="{x * cs + .5}" y="{(H - 1 - y) * cs + .5}" width="{cs - 1}" height="{cs - 1}" '
                 f'fill="{OP.COL.get(k.upper(), "#8a8f9c")}"{op}/>')
    for (x, y) in tst:
        r.append(f'<rect x="{x * cs + 2}" y="{(H - 1 - y) * cs + 2}" width="{cs - 4}" height="{cs - 4}" fill="none" '
                 f'stroke="#c77dff" stroke-width="2" stroke-dasharray="3 2"/>')
    r.append("</svg>")
    return "".join(r)


def mirror_line(b, m, C):
    """The mirror board's line: `same` when its four-budget figures equal the card's, else its own figures per budget."""
    fb, fm = strings(b), strings(m)
    if fb == fm:
        return f'<div class="muted sm mir" data-same="1">{_esc(C["mirror_same"].format(name=m["name"]))}</div>'
    parts = "".join(f'{_esc(C["bk_" + k])} <b data-m="{k}">{_esc(" · ".join(fm[k]))}</b>　' for k in BK)
    return (f'<div class="muted sm mir" data-same="0">{_esc(C["mirror_diff"].format(name=m["name"]))} {parts}</div>')


def pcx3(rows, left, ex, C):
    """The folded worked-PC section of one card: the bag-3 example only (this page counts no 4th bag). The figure and its
    parts are the shared `OP.pcx_block`, so the held page's and this page's audit read one markup."""
    lf = C["pcx_left"].format(left=left) if left else ""
    if ex["b3"] is None:
        part = f'<p class="muted sm">{_esc(C["pcx_none3"])}</p>'
    else:
        d = ex["b3"]["deal"]
        part = OP.pcx_block(rows, left, d, ex["b3"], C["pcx_b3"], lf + C["pcx_deal3"].format(d=d), C)
    return (f'<details class="pcx" data-line="{_esc(ex["line"])}"><summary>{_esc(C["pcx"])}</summary>'
            f'<p class="muted sm">{_esc(C["pcx_note"])}</p><div class="pcxb">{part}</div></details>')


def card(rkt, r, m, cat, art, PR, pcxd, famh="", pt=None):
    C = PR["card"]
    ci = shown_class(r)
    si, left, p5 = r["classes"][ci]
    s = cat[r["shapes"][si]]
    t = holders(cat, r)[ci]
    bs = piece_set(r["pieces"])
    cells = {}
    for k, cs in t["pieces"]:
        for c in cs:
            cells[(c % 10, c // 10)] = k if (k, tuple(sorted(cs))) in bs else k.lower()
    H = max(y for x, y in cells) + 1
    tst = [tuple(x) for x in s["tst"]]
    b1 = {}
    for k, cs in r["pieces"]:
        for c in cs:
            b1[(c % 10, c // 10)] = k
    res = {(x, y): "G" for y, row in enumerate(s["rows"]) for x in range(10) if row >> x & 1}
    d = OP.dist(s)
    pos = PR["pos_centre"] if d >= WALL else PR["pos_wall"]
    fs = strings(r)[BK_SHOWN]
    sd = strings(r)
    built, pc3n, _j = figs(r, BK_SHOWN)
    cnt = counts_line(r, BK_SHOWN, C)
    shown = _esc(board_title(cat, r, art["mirror"]["suffix"], PR))
    me = title_parts(cat, r, art["mirror"]["suffix"])[2]
    line = C["pos_line"].format(pos=pos, d=d, cells=len(s["cells"]), left=left or C["no_left"], nc=len(live(r)),
                                ns=len(r["shapes"]))
    rows = s["rows"]
    sline = ",".join(map(str, rows)) + "|" + left
    pcx = ""
    if sline in pcxd:
        pcx = pcx3(rows, left, pcxd[sline], C)
    ft = tstrings(r, pt)[BK_SHOWN]
    stats = (f'<span>{C["two"]} <b class="num" data-f="two">{fs[0]}</b></span>'
             f'<span>{C["pc3"]} <b class="num" data-f="pc3">{_esc(fs[1])}</b></span>'
             f'<span class="j">{C["joint"]} <b class="num" data-f="joint">{fs[2]}</b></span>'
             f'<span>{C["tsd"]} <b class="num" data-f="tsd">{_esc(ft[0])}</b></span>'
             f'<span class="j">{C["tsdj"]} <b class="num" data-f="tsdj">{ft[1]}</b></span>')
    sdl = " · ".join(f'{_esc(C["bk_" + k])} <b class="num" data-f="sd{k}">{sd[k][2]}</b>' for k in ("0", "1", "2"))
    b1t = C["b1_title_held"] if r["kind"] == "held" else C["b1_title"].format(held=r["held"])
    return (f'<article class="card{" me" if me else ""}" data-pos="{pos}" data-card="{r["name"]}" data-rk="{rkt}" data-kind="{r["kind"]}" id="c{r["name"]}">'
            f'<div class="rk num">{rkt}</div>\n'
            f'<div class="bd">{svg2(cells, max(H, 8), 15, tst)}<div class="smalls">'
            f'<div class="small"><div class="lab">{_esc(b1t)}</div>{OP.svg(b1, max(4, max(y for x, y in b1) + 1), 9)}</div>'
            f'<div class="small"><div class="lab">{_esc(C["left_title"])}</div>{OP.svg(res, max(4, len(rows)), 9)}</div></div></div>\n'
            f'<div class="meta"><span class="kc kc-{r["kind"]}" data-kc="1">{_esc(C["kind_" + r["kind"]])}</span><div class="src">{shown}</div>\n'
            f'<div class="stats">{stats}</div>\n'
            f'<div class="sm pairl" data-pair="1">{fl_spans(C["pair_line"], pair_of(art, r["name"], m["name"]))}</div>\n'
            f'<div class="muted sm sdl">{_esc(C["sd_line"])} {sdl}</div>\n'
            f'<div class="muted sm cnt" data-cnt="1">{_esc(cnt)}</div>\n'
            f'<div class="muted sm">{_esc(line)}</div>\n{b1_line(r, C)}{mirror_line(r, m, C)}\n{famh}{pcx}'
            f'<details data-s="{r["name"]}"><summary>{_esc(C["details"].format(nc=len(live(r))))}</summary><div class="tl"></div></details>'
            f'</div></article>')


def b1_line(b, C):
    """The card's bag-1 sentence: the openers whose bag 1 this board is, else the catalogue pages of the same shape."""
    ex, same = b.get("b1", ([], []))
    if ex:
        t = C["b1_exact"].format(n="、".join(ex))
        if same:
            t += C["b1_also"].format(n="；".join(same))
    elif same:
        t = C["b1_same"].format(n="；".join(same))
    else:
        t = C["b1_none"]
    return f'<div class="muted sm b1" data-b1="{_esc("|".join(ex))}" data-b1s="{_esc("|".join(same))}">{_esc(t)}</div>\n'
ROUTE_FAMILY = {"hdgamushiro": "gamushiro"}   # one opener drawn by two sites: counted once, ガムシロ積み named first


def title_parts(cat, b, sfx):
    """(route openers' Japanese names, other names, has yachi's own shape) over ALL the board's shapes; a mirror shape's name
    loses the mirror suffix so it counts as its original. Routes are ordered: an opener whose bag 1 this board IS first, then
    by how many of the board's shapes carry that opener (so one stray shape of another route does not name the board), then
    ROUTE order."""
    routes, others, me, cnt = [], [], False, {}
    for sid in b["shapes"]:
        seen = set()
        for n in (cat[sid]["names"] if sid in cat else []):
            n = n[:-len(sfx)] if sfx and n.endswith(sfx) else n
            if n.strip() == "yachi":
                me = True
                continue
            k = route_of(n)
            if k:
                f = ROUTE_FAMILY.get(k, k)
                if f not in seen:
                    seen.add(f)
                    cnt[f] = cnt.get(f, 0) + 1
                if k not in routes:
                    routes.append(k)
            elif n not in others:
                others.append(n)
    b1 = set(b.get("b1", ([], []))[0])
    routes.sort(key=lambda k: (ROUTE[k] not in b1, -cnt[ROUTE_FAMILY.get(k, k)], list(ROUTE).index(k)))
    return [ROUTE[k] for k in routes], others, me


def board_title(cat, b, sfx, PR):
    """The card's title: named route openers first, then the other names (two at most), then `等 N 個圖`, then the hold."""
    rt, ot, me = title_parts(cat, b, sfx)
    names = rt + ot
    shown = names[:4]
    more = PR["names_more"].format(c=len(names)) if len(names) > len(shown) else ""
    if me:
        shown = shown[:3] + [PR["me_name"]]
    ex, same = b.get("b1", ([], []))
    pre = PR["b1_prefix"].format(n="、".join(ex)) if ex else (PR["b1_prefix_same"].format(n="、".join(same)) if same else "")
    return pre + ", ".join(shown) + more + PR["card"]["hold_tag"].format(held=b["held"])


def top_table(art, cat, R, PR):
    T = PR["sd_table"]
    rk, od = rank_data(art, R)
    order = sorted(range(len(R)), key=lambda i: (-figs(R[i][0], TABLE_BK)[2], i))[:TABLE_SHOWN]
    head = "".join(f"<th>{_esc(h)}</th>" for h in T["cols"])
    body = []
    for n, i in enumerate(order, 1):
        r = R[i][0]
        sh = board_title(cat, r, art["mirror"]["suffix"], PR)
        body.append(f'<tr data-p3="{r["name"]}"><td class="num">{n}</td><td><a href="#c{r["name"]}">{_esc(sh)}</a></td>'
                    + "".join(f'<td class="num{" j3" if k == TABLE_BK else ""}" data-g="{k}">{pct(figs(r, k)[2])}</td>' for k in BK)
                    + f'<td class="num" data-g="main">{rk[BK_SHOWN][i]}</td></tr>')
    return [f'<h2>{_esc(T["h2"])}</h2>', f'<p class="muted">{T["note"].format(shown=TABLE_SHOWN)}</p>',
            f'<div class="p3w"><table class="p3"><thead><tr>{head}</tr></thead><tbody>', *body, "</tbody></table></div>"]


def inc_table(art, cat, U, PR):
    T = PR["inc_table"]
    head = "".join(f"<th>{_esc(h)}</th>" for h in T["cols"])
    body = []
    for r, _ in U:
        sh = board_title(cat, r, art["mirror"]["suffix"], PR)
        body.append(f'<tr data-inc="{r["name"]}"><td>{_esc(sh)}</td>'
                    + "".join(f'<td class="num" data-g="{k}">{pct(figs(r, k)[2])}</td>' for k in BK) + "</tr>")
    return [f'<details class="inc"><summary><b>{_esc(T["summary"].format(n=len(U)))}</b></summary>',
            f'<p class="muted sm">{T["note"].format(thr=thr_text(art))}</p>',
            f'<div class="p3w"><table class="p3"><thead><tr>{head}</tr></thead><tbody>', *body, "</tbody></table></div></details>"]


def thr_text(art):
    return f"{float(threshold(art)) * 100:g}%"


def kind_counts(R):
    """kind -> how many ranked cards (mirror pairs) are of it."""
    return {k: sum(1 for r, _ in R if r["kind"] == k) for k in KINDS}


def pr_figs(art):
    """The printed pruning figures by `data-pr` key, from the artefact: the totals and each kind's boards and kept."""
    pr = art["prune"]
    kd = pr["kinds"]
    return {"boards_total": pr["boards_total"], "kept": pr["kept"],
            "boards_placed": kd["placed"][0], "kept_placed": kd["placed"][1],
            "boards_held": kd["held"][0], "kept_held": kd["held"][1]}


def fmt_for(art, cat, R, U):
    pr = art["prune"]
    nsrc = sum(1 for k in cat if k < ID_OFFSET)
    pf = pr_figs(art)
    kc = kind_counts(R)
    return dict(boards=f'<b data-pr="boards_total">{pr["boards_total"]}</b>', kept=f'<b data-pr="kept">{pr["kept"]}</b>',
                boards_placed=f'<b data-pr="boards_placed">{pf["boards_placed"]}</b>',
                kept_placed=f'<b data-pr="kept_placed">{pf["kept_placed"]}</b>',
                boards_held=f'<b data-pr="boards_held">{pf["boards_held"]}</b>',
                kept_held=f'<b data-pr="kept_held">{pf["kept_held"]}</b>',
                dropped=pr["boards_total"] - pr["kept"], thr=thr_text(art), nshapes=len(cat), nsrc=nsrc, nmir=len(cat) - nsrc,
                nr=len(R), nu=len(U), npairs=len(R) + len(U), nc=sum(1 for r, _ in R if OP.dist(cat[r["shapes"][r["classes"][shown_class(r)][0]]]) >= WALL),
                nr_placed=kc["placed"], nr_held=kc["held"],
                wall=WALL, mirror_state=None)


KIND_DEFAULT = "all"


def kind_labels(R, PR):
    """The kind bar's button texts by key: all, placed, held (the counts are the ranked cards of each kind)."""
    kc = kind_counts(R)
    return {"all": PR["kind_all"].format(n=len(R)), "placed": PR["kind_placed"].format(n=kc["placed"]),
            "held": PR["kind_held"].format(n=kc["held"])}


def kind_bar(R, PR):
    lb = kind_labels(R, PR)
    btn = "".join(f'<button aria-pressed="{"true" if k == KIND_DEFAULT else "false"}" data-k="{k}">{_esc(lb[k])}</button>'
                  for k in ("all", "placed", "held"))
    return f'<div class="bar" data-bar="kind">{btn}</div>'


# ------------------------------------------------------------------ 學邊幾個: the learn-these-boards section

SETS_ID = "sdata"
P7 = "IOTSZJL"                       # the counter's first-bag recursion alphabet; an order's index is its rank in this alphabet
INFEAS = 10                          # the cost code of "no build" in the tables below
FIX_IDX = (0, 1, 719, 720, 2519, 5039)
FEATURES7 = [f"{P7[i]}<{P7[j]}" for i in range(7) for j in range(i + 1, 7)] + [f"first={k}" for k in P7]
RULE_WITHIN = Fraction(1, 100)       # the rule is the shallowest (depth 2, else 3) within this much joint of the best set
_SX = re.compile(r'<section class="sx" id="sx">(.*?)</section>', re.S)
_SXBK = re.compile(r'<!--sx:bk (\w+)-->(.*?)<!--/sx:bk-->', re.S)
_SXROW = re.compile(r'<tr data-r="(\w+):(\d)"><td>(.*?)</td><td data-c="j">(.*?)</td><td data-c="b">(.*?)</td>'
                    r'<td data-c="g">(.*?)</td></tr>\s*<tr class="sx-n"><td colspan="4" data-names="([^"]*)">(.*?)</td></tr>', re.S)
_SXFIG = re.compile(r'<figure class="sx-m" data-bd="(\w+)" data-share="(\d+)">(.*?)</figure>', re.S)
_SXLEAD = re.compile(r'<p class="sx-lead" data-lead="1">(.*?)</p>', re.S)
_SXFX = re.compile(r'<p class="sx-fx" data-fx="1">(.*?)</p>', re.S)
_SXRULE = re.compile(r'<div class="sx-r" data-depth="(\d)">(.*?)</div>\s*<p class="sx-loss" data-loss="1">(.*?)</p>', re.S)
_SXQ = re.compile(r'<span data-q="([^"]+)">(.*?)</span>', re.S)
_SXLEAF = re.compile(r'<span data-leaf="(\d)">(.*?)</span>', re.S)
_SXISL = re.compile(r'<script id="sdata" type="application/json">(.*?)</script>', re.S)


def _canon_md5(x):
    return hashlib.md5(json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def load_sets(repo=REPO):
    """The learn-these-boards artefact and the first-bag cost vectors (name -> 5040-char string, '.' = no build); refuses
    either when it was built from another artefact."""
    def rd(n):
        with open(os.path.join(repo, "analysis", n), encoding="utf-8") as f:
            return json.load(f)
    S, A, B1 = rd("tst-openers-tp-sets.json"), rd("tst-openers-tp.json"), rd("tst-openers-tp-b1.json")
    with open(os.path.join(repo, "analysis", "tst-openers-tp-tsd.json"), "rb") as f:
        traw = f.read()
    TS = json.loads(traw)
    _need(TS["schema"] == "tst-openers-tp-tsd/1" and TS["report_eligible"] is False and TS["constructed"] is True,
          "the tsd artefact is not tst-openers-tp-tsd/1 marked report_eligible: false / constructed: true")
    _need(S["md5"]["tsd"] == hashlib.md5(traw).hexdigest(),
          "analysis/tst-openers-tp-sets.json was built from another tst-openers-tp-tsd.json: re-run emit-tst-openers-tp.py --sets")
    with open(os.path.join(repo, "analysis", "tst-openers-tp-x.json"), "rb") as f:
        xraw = f.read()
    X = json.loads(xraw)
    _need(X["schema"] == "tst-openers-tp-x/1" and X["report_eligible"] is False and X["constructed"] is True,
          "the x artefact is not tst-openers-tp-x/1 marked report_eligible: false / constructed: true")
    _need(S["md5"]["x"] == hashlib.md5(xraw).hexdigest(),
          "analysis/tst-openers-tp-sets.json was built from another tst-openers-tp-x.json: re-run emit-tst-openers-tp.py --sets")
    _need(S["schema"] == "tst-openers-tp-sets/4" and S["report_eligible"] is False and S["constructed"] is True,
          "the sets artefact is not tst-openers-tp-sets/4 marked report_eligible: false / constructed: true")
    _need(S["md5"]["art"] == _canon_md5(A) and S["md5"]["b1"] == _canon_md5(B1),
          "analysis/tst-openers-tp-sets.json was built from another tst-openers-tp.json or -b1.json: re-run emit-tst-openers-tp.py --sets")
    _need(S["features"] == FEATURES7 and S["den"] == {"pc3": BAG ** 3, "built": BAG ** 2}, "the sets artefact's features or denominators moved")
    _need(S["fixed"]["budget"] == "2" and set(S["budgets"]) == set(BK), "the sets artefact's fixed budget or budgets moved")
    vecs = {n: zlib.decompress(base64.b64decode(z)).decode() for n, z in {**B1["vectors"], **X["vectors"]}.items()}
    _need(all(len(v) == BAG for v in vecs.values()), "a first-bag vector is not 5040 long")
    _need(S["x"] == len(X["boards"]) and S["boards"] == len(A["boards"]) + len(X["boards"]),
          "the sets artefact's board counts do not match the kept and x boards")
    _need(S["tsd"]["fixed"]["budget"] == "2" and set(S["tsd"]["budgets"]) == set(BK), "the tsd sets' fixed budget or budgets moved")
    art, cat = load_inputs(repo)
    lines = TS["lines"]
    pt = {}
    for b in art["boards"] + art["xboards"]:
        lv = set(live(b))
        vec = []
        for i in range(len(b["classes"])):
            if i in lv:
                r = lines[class_line(cat, b, i)]
                _need(r["p5"] == b["classes"][i][2] and 0 <= r["pt3"] <= r["p5"] and r["pt3u"] == 0,
                      f"the tsd line of {b['name']} class {i} disagrees with the artefact's p5")
                vec.append(r["pt3"])
            else:
                vec.append(0)
        pt[b["name"]] = vec
    St = {**S, "budgets": S["tsd"]["budgets"], "fixed": S["tsd"]["fixed"], "cands": S["tsd"]["cands"]}
    return {"S": St, "Sref": S, "vecs": vecs, "X": X, "pt": pt}


def _members(S, bk, k):
    bb = S["budgets"][bk]
    d = bb["exact"] if str(k) in bb["exact"] else bb["from_exact3"]
    return d[str(k)]


def _solve_d(cum, v):
    n = [0] * (INFEAS + 1)
    for x in v:
        n[x] += 1
    nf = sum(n[:INFEAS])
    Dinf = []
    for c in cum["inf"]:
        _need(c % nf == 0, "cum_inf is not divisible by the feasible count")
        Dinf.append(c // nf)
    smin = min(s for s in range(INFEAS) if n[s])
    Dfin = {}
    for b in (0, 1, 2):
        if b < smin:
            continue
        row = []
        for k, c in enumerate(cum[str(b)]):
            t = c - sum(n[s] * Dfin[b - s][k] for s in range(smin + 1, b + 1))
            _need(t % n[smin] == 0, "a soft-drop count is not divisible")
            row.append(t // n[smin])
        Dfin[b - smin] = row
    return Dfin, Dinf


def _jt(b, D, p=None):
    Dfin, Dinf = D
    p5 = p if p is not None else [c[2] for c in b["classes"]]

    def jb(row):
        prev = j = 0
        for d, p in zip(row, p5):
            j += (d - prev) * p
            prev = d
        return j, row[-1]
    out = {}
    for bk, bb in (("0", 0), ("1", 1), ("2", 2), ("inf", None)):
        J, Bt = [0] * (INFEAS + 1), [0] * (INFEAS + 1)
        for s in range(INFEAS):
            if bb is None:
                J[s], Bt[s] = jb(Dinf)
            elif bb - s >= 0 and (bb - s) in Dfin:
                J[s], Bt[s] = jb(Dfin[bb - s])
        out[bk] = (J, Bt)
    return out


def set_tables(art_by, L, names):
    """name -> (cost list, {budget: (J[0..10], built[0..10])}) for the boards `names`."""
    T = {}
    for n in names:
        v = [INFEAS if c == "." else int(c) for c in L["vecs"][n]]
        if all(c == INFEAS for c in v):
            z = [0] * (INFEAS + 1)
            T[n] = (v, {bk: (z, z) for bk in BK})
        else:
            T[n] = (v, _jt(art_by[n], _solve_d(art_by[n]["cum"], v), (L.get("pt") or {}).get(n)))
    return T


def _lim(bk):
    return INFEAS - 1 if bk == "inf" else int(bk)


def set_picks(T, names, bk):
    """(picks string, pc3, built): per first-bag order the member with the larger (J, built) within the budget, the earlier on
    a tie, 'x' where none builds."""
    lim, out, pc, bt = _lim(bk), [], 0, 0
    for o in range(BAG):
        best, bi = None, -1
        for i, n in enumerate(names):
            v, tab = T[n]
            s = v[o]
            if s <= lim:
                key = (tab[bk][0][s] << 13 | tab[bk][1][s]) + 1
                if best is None or key > best:
                    best, bi = key, i
        if bi < 0:
            out.append("x")
        else:
            v, tab = T[names[bi]]
            out.append(str(bi))
            pc += tab[bk][0][v[o]]
            bt += tab[bk][1][v[o]]
    return "".join(out), pc, bt


def all_perms():
    return ["".join(p) for p in itertools.permutations(P7)]


def feat_holds(f, o):
    if f.startswith("first="):
        return o[0] == f[6]
    a, b = f.split("<")
    return o.index(a) < o.index(b)


def tree_leaf(t, o):
    while "m" not in t:
        t = t["y"] if feat_holds(t["feature"], o) else t["n"]
    return t["m"]


def sx_names(S):
    """Every board the section names."""
    ns = set()
    for bb in S["budgets"].values():
        for g in (bb["exact"], bb["from_exact3"]):
            for v in g.values():
                ns |= {x["name"] for x in v["boards"]}
    ns |= {x["name"] for x in S["fixed"]["boards"]}
    return sorted(ns)


def short_label(cat, b, sfx):
    rt, ot, _me = title_parts(cat, b, sfx)
    names = rt + ot
    return names[0] if names else b["name"]


def sx_label(cat, b, sfx, PR):
    """A board's name for people: its first catalogue name (route names first) and the held piece; the id stays secondary."""
    return short_label(cat, b, sfx) + PR["card"]["hold_tag"].format(held=b["held"])


def sx_set_names(cat, by, names, sfx, PR):
    """The display names of a set: a board and its mirror (both in the set, same first name) are one 「X左右手」, else each
    board's own label."""
    out, done = [], set()
    for n in names:
        if n in done:
            continue
        b = by[n]
        m = b["mirror"]
        if m in names and m != n and short_label(cat, by[m], sfx) == short_label(cat, b, sfx):
            done |= {n, m}
            out.append(short_label(cat, b, sfx) + PR["sets"]["lr"])
        else:
            done.add(n)
            out.append(sx_label(cat, b, sfx, PR))
    return out


def lead_parts(cat, by, sfx, PR, S, bk):
    """The names for the lead sentence (the best single pair and the best two pairs) when the best single pair is not among the
    best two; else None. A pair is a board and its mirror."""
    e1, e2 = _members(S, bk, 1), _members(S, bk, 2)
    a, pair = [x["name"] for x in e1["boards"]], [x["name"] for x in e2["boards"]]
    if set(a) <= set(pair):
        return None
    return ("＋".join(sx_set_names(cat, by, a, sfx, PR)), Fraction(e1["pc3"], BAG ** 3),
            "＋".join(sx_set_names(cat, by, pair, sfx, PR)), Fraction(e2["pc3"], BAG ** 3))


def sx_ids(names):
    return f'<span class="sx-id">{_esc(" ".join(names))}</span>'


def sx_pics(cat, b, sfx):
    rt, ot, me = title_parts(cat, b, sfx)
    return len(rt) + len(ot) + (1 if me else 0)


def disp_dec(s):
    """The number in a printed percentage string such as `93.1%`."""
    _need(s.endswith("%") and not s.startswith("<"), f"cannot read the printed figure {s!r}")
    return Decimal(s[:-1])


def gain_text(prev_s, cur_s, SP):
    """The gain between two printed rows, in percentage points, from the printed (floored) figures themselves."""
    if prev_s is None:
        return "–"
    d = disp_dec(cur_s) - disp_dec(prev_s)
    return SP["gain"].format(d=f"{d:f}")


def chip(k):
    return f'<i class="chip c-{k}">{k}</i>'


def q_html(f, SP):
    if f.startswith("first="):
        return SP["q_first"].format(a=chip(f[6]))
    a, b = f.split("<")
    return SP["q_before"].format(a=chip(a), b=chip(b))


def tree_html(t, labels, SP):
    if "m" in t:
        return f'<span data-leaf="{t["m"]}">{SP["leaf"].format(n=_esc(labels[t["m"]]))}</span>'
    return (f'<span data-q="{t["feature"]}">{q_html(t["feature"], SP)}</span><ul>'
            f'<li data-a="y"><b>{_esc(SP["rule_yes"])}</b>{tree_html(t["y"], labels, SP)}</li>'
            f'<li data-a="n"><b>{_esc(SP["rule_no"])}</b>{tree_html(t["n"], labels, SP)}</li></ul>')


def ceil2(points):
    """A number of percentage points (a Fraction), ceiled to two decimals, as text."""
    c = -((-points * 100).numerator // (points * 100).denominator)
    return f"{c // 100}.{c % 100:02d}"


def rule_depth(rules, den):
    """The printed depth: 2 when its joint loss is within RULE_WITHIN of 5040^3, else 3."""
    return "2" if Fraction(rules["2"]["loss_pc3"], den) <= RULE_WITHIN else "3"


def lead_html(SP, a, x, b, y):
    return SP["lead"].format(a=_esc(a), x=pct(x), b=_esc(b), y=pct(y))


def fixed_html(SP, same, names, fx, gap):
    j, bu = pct(Fraction(fx["pc3"], BAG ** 3)), pct(Fraction(fx["built"], BAG ** 2))
    if same:
        return SP["fixed_same"].format(j=j, b=bu)
    return SP["fixed"].format(names=_esc("、".join(names)), j=j, b=bu, g=pct(gap))


def sx_row_html(bk, k, m, prev_s, X):
    """One ladder row: figures floored to the printed percentage, the gain taken from the PRINTED rows, then the set's names."""
    cat, by, sfx, PR = X
    SP = PR["sets"]
    js, bs = pct(Fraction(m["pc3"], BAG ** 3)), pct(Fraction(m["built"], BAG ** 2))
    nm = [x["name"] for x in m["boards"]]
    return (f'<tr data-r="{bk}:{k}"><td>{_esc(SP["k_label"].format(k=k))}</td><td data-c="j">{js}</td>'
            f'<td data-c="b">{bs}</td><td data-c="g">{gain_text(prev_s, js, SP)}</td></tr>\n'
            f'<tr class="sx-n"><td colspan="4" data-names="{" ".join(nm)}">{_esc("、".join(sx_set_names(cat, by, nm, sfx, PR)))} '
            f'{sx_ids(nm)}</td></tr>')


SX_T_KEYS = ("lk_none_yet", "lk_pick", "lk_cost", "lk_fig", "lk_others", "lk_unbuildable", "lk_nopick", "lk_fail", "lk_seq",
             "to_card", "mirror_card", "no_card")
SX_KS = ("1", "2", "3")
SX_K0 = "2"                          # the lookup opens on the best two boards


def sx_members(S, bk, k):
    return [x["name"] for x in _members(S, bk, int(k))["boards"]]


def sets_data(art_by, L):
    """The cost tables of every board the section names, the picks of the best 1, 2 and 3 boards per budget (the same rule
    for each k) and each of the best three's pick counts. The recomputed k=3 picks must equal the artefact's own."""
    S = L["S"]
    T = set_tables(art_by, L, sx_names(S))
    picks, shares = {}, {}
    for bk in BK:
        picks[bk] = {k: set_picks(T, sx_members(S, bk, k), bk)[0] for k in SX_KS}
        _need(picks[bk]["3"] == S["budgets"][bk]["picks"], f"the recomputed picks of the best three at budget {bk} are not the artefact's")
        shares[bk] = [picks[bk]["3"].count(str(i)) for i in range(len(sx_members(S, bk, 3)))]
    return T, picks, shares


def sx_link(n, reps, rep_of):
    if n in reps:
        return ["c", n]
    if n in rep_of:
        return ["m", rep_of[n]]
    return None


def sets_island(PR, L, T, picks, fixtures, X, R, by):
    S, SP = L["S"], PR["sets"]
    cat, _by, sfx, _PR = X
    mem = {bk: {k: sx_members(S, bk, k) for k in SX_KS} for bk in BK}
    names = sorted({n for v in mem.values() for w in v.values() for n in w})
    reps = {r["name"] for r, _ in R}
    rep_of = {p["name"]: r["name"] for r, p in R}
    lk = {n: sx_link(n, reps, rep_of) for n in names}
    lab = {n: sx_label(cat, by[n], sfx, PR) for n in names}
    for v in lk.values():
        if v:
            lab.setdefault(v[1], sx_label(cat, by[v[1]], sfx, PR))
    return {"ord": P7, "fix": fixtures, "bk": BK, "shown": BK_SHOWN, "ks": list(SX_KS), "k0": SX_K0, "m": mem, "p": picks,
            "col": OP.COL, "lb": lab, "lk": lk,
            "bd": {n: {"v": L["vecs"][n], "c": by[n]["pieces"]} for n in names},
            "f": {bk: {n: [[pct(Fraction(T[n][1][bk][1][s], BAG)), pct(Fraction(T[n][1][bk][0][s], BAG ** 2))]
                           if s <= _lim(bk) else None for s in range(INFEAS)]
                       for n in sorted({n for w in mem[bk].values() for n in w})} for bk in BK},
            "t": {k: SP[k] for k in SX_T_KEYS}}


def S_ref(L):
    return L["Sref"]


def ref_rows(Sr, bk, SP, cat, by, sfx, PR, ex):
    """The reference rows: the best 1, 2 and 3 boards by the any-bag-3-PC count (`ex(names)` -> (picks, pc3, built))."""
    rows = []
    for k in (1, 2, 3):
        m = _members(Sr, bk, k)
        nm = [x["name"] for x in m["boards"]]
        e = ex(nm)
        rows.append(f'<tr data-ref="{bk}:{k}"><td>{html.escape(SP["k_label"].format(k=k), quote=False)}</td>'
                    f'<td class="num">{pct(Fraction(e[1], BAG ** 3))}</td><td class="num">{pct(Fraction(e[2], BAG ** 2))}</td>'
                    f'<td>{html.escape("、".join(sx_set_names(cat, by, nm, sfx, PR)), quote=False)}</td></tr>')
    return rows


def ref_html(Sr, bk, SP, cat, by, sfx, PR, ex=None):
    """The folded reference of the budget: the sets the earlier objective (any bag-3 Perfect Clear) picks."""
    if ex is None:
        def ex(nm):
            return (None, sum_pc(Sr, bk, nm), sum_built(Sr, bk, nm))
    rows = ref_rows(Sr, bk, SP, cat, by, sfx, PR, ex)
    head = "".join(f"<th>{_esc(c)}</th>" for c in SP["ref_cols"])
    return (f'<details class="sx-ref" data-refbk="{bk}"><summary>{_esc(SP["ref_summary"])}</summary><p class="muted sm">{SP["ref_note"]}</p>'
            f'<table class="sx-t"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></details>')


def sum_pc(Sr, bk, nm):
    for k in (1, 2, 3):
        m = _members(Sr, bk, k)
        if [x["name"] for x in m["boards"]] == nm:
            return m["pc3"]
    raise ValueError("a reference set is not the artefact's")


def sum_built(Sr, bk, nm):
    for k in (1, 2, 3):
        m = _members(Sr, bk, k)
        if [x["name"] for x in m["boards"]] == nm:
            return m["built"]
    raise ValueError("a reference set is not the artefact's")


def sets_block(art, cat, PR, L, R):
    """The 學邊幾個 section and its island: per budget the exact ladder for 1-3 boards (4-5 folded, greedy from the exact
    three), the best three drawn with their share of the 5040 first-bag orders, the sentence where the best single board is
    not in the best pair, the fixed set, the shallow rule and the lookup. Returns (section html, island json text)."""
    S, SP, sfx = L["S"], PR["sets"], art["mirror"]["suffix"]
    by = {b["name"]: b for b in list(art["boards"]) + list(L["X"]["boards"])}
    X = (cat, by, sfx, PR)
    T, picks, shares = sets_data(by, L)
    reps = {r["name"] for r, _ in R}
    rep_of = {p["name"]: r["name"] for r, p in R}
    den3, den2 = BAG ** 3, BAG ** 2
    P = all_perms()
    fixtures = [[P[i], i] for i in FIX_IDX]
    fxn = [x["name"] for x in S["fixed"]["boards"]]
    parts = [f'<section class="sx" id="sx"><h2>{_esc(SP["h2"])}</h2><p>{SP["intro"]}</p><p>{SP["figs"]}</p>',
             f'<p class="muted sm">{SP["lower"].format(thr=thr_text(art))}</p><p class="muted sm">{SP["built_note"]}</p>',
             f'<p class="muted sm">{_esc(SP["sd_hint"])}</p>']
    for bk in BK:
        bb = S["budgets"][bk]
        sh = bk == BK_SHOWN
        parts.append(f'<!--sx:bk {bk}-->\n<div class="sx-bk" data-bk="{bk}"{"" if sh else " hidden"}>')
        head = "".join(f"<th>{_esc(c)}</th>" for c in SP["cols"])
        rows, prev = [], None
        for k in (1, 2, 3):
            m = _members(S, bk, k)
            rows.append(sx_row_html(bk, k, m, prev, X))
            prev = pct(Fraction(m["pc3"], den3))
        ext = []
        for k in (4, 5):
            m = _members(S, bk, k)
            ext.append(sx_row_html(bk, k, m, prev, X))
            prev = pct(Fraction(m["pc3"], den3))
        parts.append(f'<table class="sx-t"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>')
        parts.append(f'<details class="sx-x"><summary>{_esc(SP["ext_summary"])}</summary><table class="sx-t"><tbody>'
                     f'{"".join(ext)}</tbody></table></details><p class="muted sm">{_esc(SP["best_note"])}</p>')
        lp = lead_parts(cat, by, sfx, PR, S, bk)
        if lp:
            parts.append(f'<p class="sx-lead" data-lead="1">{lead_html(SP, *lp)}</p>')
        mem = [x["name"] for x in _members(S, bk, 3)["boards"]]
        figs_ = []
        for i, n in enumerate(mem):
            b = by[n]
            cells = {}
            for k, cs in b["pieces"]:
                for c in cs:
                    cells[(c % 10, c // 10)] = k
            H = max(4, max(y for _x, y in cells) + 1)
            links = []
            if n in reps:
                links.append(f'<a href="#c{n}">{_esc(SP["to_card"])}</a>')
            elif n in rep_of:
                links.append(f'<a href="#c{rep_of[n]}">{_esc(SP["to_card"])}</a> {_esc(SP["mirror_card"].format(m=sx_label(cat, by[rep_of[n]], sfx, PR)))}')
            else:
                links.append(_esc(SP["no_card"]))
            if b["mirror"] in mem:
                links.append(_esc(SP["mirror_in"].format(m=sx_label(cat, by[b["mirror"]], sfx, PR))))
            figs_.append(f'<figure class="sx-m" data-bd="{n}" data-share="{shares[bk][i]}">{svg2(cells, H, 15)}<figcaption>'
                         f'<div class="sx-tt"><b>{_esc(sx_label(cat, b, sfx, PR))}</b> {sx_ids([n])}</div>'
                         f'<div class="muted sm" data-np="{sx_pics(cat, b, sfx)}">{_esc(SP["n_pics"].format(c=sx_pics(cat, b, sfx)))}</div>'
                         f'<div class="sx-sh">{_esc(SP["share"].format(n=shares[bk][i], p=pct(Fraction(shares[bk][i], BAG))))}</div>'
                         f'<div class="sx-lnk">{"<br>".join(links)}</div></figcaption></figure>')
        parts.append(f'<h3>{_esc(SP["boards_h"])}</h3><div class="sx-g">{"".join(figs_)}</div>')
        fx = S["fixed"]["values"][bk]
        e3 = _members(S, bk, 3)
        parts.append(f'<p class="sx-fx" data-fx="1">{fixed_html(SP, set(mem) == set(fxn), sx_set_names(cat, by, fxn, sfx, PR), fx, Fraction(e3["pc3"] - fx["pc3"], den3))}</p>')
        d = rule_depth(bb["rule"], den3)
        r = bb["rule"][d]
        labels = [sx_label(cat, by[n], sfx, PR) for n in mem]
        parts.append(f'<h3>{_esc(SP["rule_h"])}</h3><p>{_esc(SP["rule_intro"].format(d=d))}</p>')
        parts.append(f'<div class="sx-r" data-depth="{d}">{tree_html(r["tree"], labels, SP)}</div>\n'
                     f'<p class="sx-loss" data-loss="1">{rule_loss_html(SP, r, e3, den3, den2)}</p>')
        parts.append(ref_html(S_ref(L), bk, SP, cat, by, sfx, PR))
        parts.append("</div>\n<!--/sx:bk-->")
    pb = "".join(f'<button class="c-{k}" data-p="{k}">{k}</button>' for k in P7)
    kb = "".join(f'<button data-k="{k}" aria-pressed="{"true" if k == SX_K0 else "false"}">{_esc(SP["lk_k"].format(k=k))}</button>' for k in SX_KS)
    parts.append(f'<div class="sx-lk"><h3>{_esc(SP["lk_h"])}</h3><p class="muted sm">{_esc(SP["lk_hint"])}</p>'
                 f'<div class="sx-kb" role="group" aria-label="{_esc(SP["lk_k_h"])}"><span class="muted sm">{_esc(SP["lk_k_h"])}</span>{kb}</div>'
                 f'<div class="sx-pb">{pb}<button class="sx-rs" data-p="reset">{_esc(SP["lk_reset"])}</button></div>'
                 f'<div class="sx-seq" aria-live="polite"></div><div class="sx-out"></div></div></section>')
    isl = sets_island(PR, L, T, picks, fixtures, X, R, by)
    return "\n".join(parts), json.dumps(isl, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")


def rule_loss_html(SP, r, e3, den3, den2):
    return SP["rule_loss"].format(j=pct(Fraction(r["pc3"], den3)), b=pct(Fraction(r["built"], den2)),
                                  l=ceil2(Fraction(e3["pc3"] - r["pc3"], den3) * 100), df=r["differs"], un=r["unbuildable"])




def render(art, cat, PR, pcxd, builds=None, L=None, orders=None):
    builds = builds if builds is not None else load_builds()
    L = L if L is not None else load_sets()
    orders = orders if orders is not None else load_orders()
    R, U = ranked(art, cat), unranked(art, cat)
    fm = fmt_for(art, cat, R, U)
    fm["mirror_state"] = PR["mirror_assumed" if art["mirror"]["assumed"] else "mirror_counted"]
    rk0 = rank_data(art, R)[0][BK_SHOWN]
    fam = families(art, cat)
    rkmap = {r["name"]: rk0[n] for n, (r, _) in enumerate(R)}
    cards = "\n".join(card(rk0[n], r, m, cat, art, PR, pcxd, fam_block(r, m, fam, rkmap, cat, art, PR), L["pt"][r["name"]])
                       for n, (r, m) in enumerate(R))
    title = PR["title"] + RS.TITLE_MARK
    data = json.dumps(build_data(art, cat, R, PR, builds, pcxd, orders, L["pt"]), separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    with open(OP.CSS_PATH, encoding="utf-8") as f:
        css = f.read().strip("\n")
    with open(CSS_PATH, encoding="utf-8") as f:
        css += "\n" + f.read().strip("\n")
    with open(SX_CSS_PATH, encoding="utf-8") as f:
        css += "\n" + f.read().strip("\n")
    with open(JS_PATH, encoding="utf-8") as f:
        js = f.read().strip("\n")
    with open(SX_JS_PATH, encoding="utf-8") as f:
        sxjs = f.read().strip("\n")
    sxhtml, sxisl = sets_block(art, cat, PR, L, R)
    sdb = "".join(f'<button aria-pressed="{"true" if k == BK_SHOWN else "false"}" data-b="{k}">{_esc(PR["card"]["bk_" + k])}</button>'
                  for k in ("inf", "2", "1", "0"))
    out = ['<!doctype html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
           "<style>", css, "</style></head><body><main>",
           f'<nav class="sm"><a href="index.html">{_esc(PR["back"])}</a></nav>',
           f'<div class="eyebrow">{RS.EYEBROW}</div>', f"<h1>{_esc(title)}</h1>",
           f'<p class="quar">{PR["quarantine"]}</p>',
           f'<p class="ref">{PR["held_note"]} <a href="{HELD_PAGE}">{PR["to_held"]}</a></p>']
    out += [f'<div class="bar" data-bar="sd"><span class="muted sm">{_esc(PR["sd_bar"])}</span>{sdb}</div>', sxhtml]
    out += [f"<p>{t.format(**fm)}</p>" for t in PR["intro"]]
    out += [f'<details class="sm"><summary><b>{_esc(PR["reading_summary"])}</b></summary>\n<ul>']
    out += [f"<li>{t.format(**fm)}</li>" for t in PR["reading"]]
    out += ["</ul></details>",
            f'<div class="bar" data-bar="pos"><button aria-pressed="true" data-f="{PR["pos_centre"]}">{_esc(PR["filter_centre"].format(**fm))}</button>'
            f'<button aria-pressed="false" data-f="all">{_esc(PR["filter_all"])}</button></div>',
            kind_bar(R, PR),
            f'<p class="muted sm">{_esc(PR["filter_note"].format(**fm))}</p>',
            *top_table(art, cat, R, PR),
            f'<h2>{_esc(PR["h2_cards"].format(**fm))}</h2>', '<div class="grid" id="g">', cards, "</div>",
            *inc_table(art, cat, U, PR)]
    out += ["</main>", f'<script id="{DATA_ID}" type="application/json">{data}</script>',
            f'<script id="{SETS_ID}" type="application/json">{sxisl}</script>', "<script>", js, "</script>", "<script>", sxjs, "</script></body></html>"]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ audit (a second route, straight from cum and classes)

def ex_strings(b):
    """Independent recomputation of `strings`: explicit loops over the classes, exact fractions."""
    out = {}
    for k in BK:
        cum, prev, num = b["cum"][k], 0, 0
        for i, (_s, _l, p5) in enumerate(b["classes"]):
            num += (cum[i] - prev) * p5
            prev = cum[i]
        tot = cum[-1]
        out[k] = [pct(Fraction(tot, 5040 * 5040)), pct(Fraction(num, tot * 5040)) if tot else "未計", pct(Fraction(num, 5040 ** 3))]
    return out


def ex_tstrings(b, pt):
    """Independent recomputation of `tstrings`: explicit loops over the classes, exact fractions."""
    out = {}
    for k in BK:
        cum, prev, num = b["cum"][k], 0, 0
        for i in range(len(b["classes"])):
            num += (cum[i] - prev) * pt[i]
            prev = cum[i]
        tot = cum[-1]
        out[k] = [pct(Fraction(num, tot * 5040)) if tot else "未計", pct(Fraction(num, 5040 ** 3))]
    return out


def ex_classes(cat, b):
    """The (shape index, leftover, p5) set the listed shapes' own tilings give (every leftover of a buildable tiling), in
    the stated order (-p5, shape index, leftover)."""
    got = set()
    for si, sid in enumerate(b["shapes"]):
        for t in cat[sid]["til"]:
            if t["B"] > 0:
                got.add((si, t["left"], t["p5"]))
    return sorted(got, key=lambda c: (-c[2], c[0], c[1]))


def ex_counts(b, k, C):
    """Independent recomputation of `counts_line`: explicit loops over the classes."""
    prev, num = 0, 0
    for i, (_s, _l, p5) in enumerate(b["classes"]):
        num += (b["cum"][k][i] - prev) * p5
        prev = b["cum"][k][i]
    tot = b["cum"][k][-1]
    return f'{C["bk_" + k]}：{tot:,} / {5040 * 5040:,} 種兩包派牌砌得成 · 3 巡 PC {num:,} / {tot * 5040:,}'


def audit_pcx(cards, R, cat, pcxd):
    bad = []
    by = {r["name"]: r for r, _ in R}
    for name, rk, body in cards:
        r = by[name]
        i = shown_class(r)
        s = cat[r["shapes"][r["classes"][i][0]]]
        left, p5 = r["classes"][i][1], r["classes"][i][2]
        line = ",".join(map(str, s["rows"])) + "|" + left
        secs = OP._PCX.findall(body)
        if line not in pcxd:
            if secs:
                bad.append(f"card {rk}: a worked PC with no examples-artefact entry")
            continue
        if len(secs) != 1 or html.unescape(secs[0][0]) != line:
            bad.append(f"card {rk}: {len(secs)} worked-PC sections, or not for its displayed class")
            continue
        ex = pcxd[line]
        want = []
        if ex["b3"] is not None:
            want.append((ex["b3"]["deal"], ex["b3"]["h"], ex["b3"]["plan"]))
        got = []
        for deal, h, fb in OP._PCX_FIG.findall(secs[0][1]):
            plan = [[p, [int(x) for x in c.split(",")], bool(int(hd))] for p, c, hd in OP._PCX_STEP.findall(fb)]
            got.append((deal, int(h), plan))
            _, why = OP.replay(s["rows"], left, deal, int(h), plan)
            if why:
                bad.append(f"card {rk}: a worked PC does not replay ({why[0]})")
        norm = lambda w: [(d, h, [[p, list(c), bool(x)] for p, c, x in pl]) for d, h, pl in w]
        if norm(got) != norm(want):
            bad.append(f"card {rk}: the worked PCs are not the examples artefact's")
    return bad


def audit_builds(island, R, cat, pcxd):
    """A second reading of every class's build and worked PC in the island: the build is the class's drawn tiling, bag 1
    first, whole pieces, no overlap, with the soft-drop total its pieces' sum; the T cells are a T, off the build; and every
    worked PC replays from the class's residue to the placed cells the island draws, with the examples artefact's plan."""
    bad = []
    for r, _ in R:
        name = r["name"]
        c = island["cards"].get(name)
        if c is None:
            bad.append(f"island card {name}: missing")
            continue
        lv = live(r)
        if c.get("n1") != len(r["pieces"]):
            bad.append(f"island card {name}: the bag-1 piece count is not the board's")
        if c.get("kind") != r["kind"]:
            bad.append(f"island card {name}: the kind is not the board's")
        if len(c.get("b", [])) != len(lv) or len(c.get("x", [])) != len(lv):
            bad.append(f"island card {name}: not one build per live class")
            continue
        for j, i in enumerate(lv):
            si, left, p5 = r["classes"][i]
            tag = f"island card {name} class {j + 1}"
            if c["b"][j] is None:
                bad.append(f"{tag}: no build")
                continue
            order, sd = c["b"][j]
            b1 = frozenset((k, tuple(sorted(cs))) for k, cs, _ in order[:c["n1"]])
            if b1 != piece_set(r["pieces"]):
                bad.append(f"{tag}: the build does not place the bag-1 board first")
            nT = sum(1 for k, _cs, _ in order[:c["n1"]] if k == "T")
            if nT != (0 if r["kind"] == "held" else 1):
                bad.append(f"{tag}: the bag-1 steps of a {r['kind']} board hold {nT} T")
            seen = set()
            for k, cs, _ in order:
                if len(cs) != 4 or OP._norm([(q % 10, q // 10) for q in cs]) not in OP.SHAPE.get(k, ()):
                    bad.append(f"{tag}: a build step is not a whole {k}")
                if seen & set(cs):
                    bad.append(f"{tag}: two build steps overlap")
                seen |= set(cs)
            g = c["t"][j][0]
            H = len(g) // 10
            drawn = {(H - 1 - q // 10) * 10 + q % 10: ch.upper() for q, ch in enumerate(g) if ch != "."}
            built = {q: k for k, cs, _ in order for q in cs}
            if built != drawn:
                bad.append(f"{tag}: the build is not the class's drawn tiling")
            if sd != sum(x for _, _, x in order):
                bad.append(f"{tag}: the soft-drop total is not its steps' sum")
            occ = set()
            for k, cs, x in order:
                if not any(q < 10 or (q - 10 in occ and q - 10 not in cs) for q in cs):
                    bad.append(f"{tag}: a {k} step rests on nothing")
                over = any(q2 in occ for q in cs for q2 in range(q + 10, 120, 10) if q2 not in cs)
                if x != int(over):
                    bad.append(f"{tag}: a {k} step's soft-drop flag is not whether a filled cell stands over it")
                occ |= set(cs)
            tc, ln, a3 = c["x"][j]
            s = cat[r["shapes"][si]]
            if tc != tst_cells(s) or set(tc) & set(built) or OP._norm([(q % 10, q // 10) for q in tc]) not in OP.SHAPE["T"]:
                bad.append(f"{tag}: the TST cells are not the shape's T, or overlap the build")
            if ln != class_line(cat, r, i) or a3 != int(p5 >= BAG):
                bad.append(f"{tag}: the worked-PC line or the every-deal flag is not the class's")
            if ln not in island["px"]:
                bad.append(f"{tag}: no worked-PC entry for its line")
    for ln, e in island.get("px", {}).items():
        rows = [int(v) for v in ln.split("|")[0].split(",")]
        left = ln.split("|")[1]
        ex = pcxd.get(ln)
        if e["r"] != rows or e["l"] != left:
            bad.append(f"worked PC {ln}: its residue or leftover is not its line's")
        for key, part in (("b3", ex and ex["b3"]),):
            got = e.get(key)
            if (got is None) != (part is None):
                bad.append(f"worked PC {ln}: the {key} example is not the artefact's")
                continue
            if got is None:
                continue
            d, h, placed, steps = got
            plan = [[p, list(cs), bool(hd)] for p, cs, hd in steps]
            if plan != [[p, list(cs), bool(hd)] for p, cs, hd in part["plan"]] or h != part["h"]:
                bad.append(f"worked PC {ln}: the {key} steps are not the artefact's plan")
            want_d = [part["deal"]]
            if d != want_d:
                bad.append(f"worked PC {ln}: the {key} deal is not the artefact's")
            pl, why = OP.replay(rows, left, "".join(d), h, plan)
            if why:
                bad.append(f"worked PC {ln}: the {key} example does not replay ({why[0]})")
            if sorted([x, y, p, n] for (x, y), (p, n) in pl.items()) != placed:
                bad.append(f"worked PC {ln}: the {key} drawing is not what its steps place")
    return bad


def _b1_grid_check(b, names, lib):
    """A second reading: each named bag 1, drawn as text rows bottom-aligned, equals the board's own text rows, as drawn or
    mirrored by reversing each row and swapping J/L and S/Z letters."""
    def text(cells):
        my = min(y for _, y in cells)
        h = max(y for _, y in cells) - my + 1
        return ["".join(cells.get((x, y + my), ".") for x in range(10)) for y in range(h)]
    c = {}
    for k, cs in b["pieces"]:
        for i in cs:
            c[(i % 10, i // 10)] = k
    mine = text(c)
    flip = ["".join(B1_SW.get(ch, ch) for ch in row[::-1]) for row in mine]
    for nm in names:
        ok = False
        for n2, _src, by_letter, d, kd in lib:
            if kd == b["kind"] and n2 == nm and by_letter and text(dict(d)) in (mine, flip):
                ok = True
        if not ok:
            return False
    return True
def audit_layouts(art, bad):
    """The artefact's family layouts, re-checked from its boards: seven placements one per kind on 28 disjoint cells, every
    variant a kept board equal to the layout less one piece, the mirror symmetric, the policy's figures between the best
    variant and the sum of the variants (the sandwich), picks within the 5040 first-bag orders, the PC count monotone in the
    budget (built is not: the policy maximises the joint, so it may pick a variant that builds less)."""
    F = art["families"]
    if F.get("complete") is not True:
        bad.append("families.complete is not true: the pruned variants must be counted for the family figures to be exact")
    byn = all_boards(art)
    lst = F["list"]
    for i, L in enumerate(lst):
        tag = f"layout {i}"
        ks = [k for k, _ in L["pieces"]]
        cells = [c for _, cs in L["pieces"] for c in cs]
        if sorted(ks) != sorted("IJLOSTZ") or len(cells) != 28 or len(set(cells)) != 28:
            bad.append(f"{tag}: not seven placements, one per kind, on 28 disjoint cells")
        if not (0 <= L["mirror"] < len(lst)) or lst[L["mirror"]]["mirror"] != i or lst[L["mirror"]]["variants"] == [] :
            bad.append(f"{tag}: the mirror layout does not point back")
        want = {k: tuple(sorted(c)) for k, c in L["pieces"]}
        vs = []
        for vn in L["variants"]:
            v = byn.get(vn)
            if v is None:
                bad.append(f"{tag}: variant {vn} is not a board of the artefact")
                continue
            vs.append(v)
            have = {k: tuple(sorted(c)) for k, c in v["pieces"]}
            if have != {k: c for k, c in want.items() if k != v["held"]}:
                bad.append(f"{tag}: variant {vn} is not the layout less its held piece {v['held']}")
        if len(set(L["variants"])) < 2 or len({v["held"] for v in vs}) != len(vs):
            bad.append(f"{tag}: fewer than two variants, or two holding the same piece")
        for k in BK:
            bn, pn = L["num"][k]
            js = [Fraction(figs(v, k)[1], N2 * BAG) for v in vs]
            bs = [figs(v, k)[0] for v in vs]
            joint, built = Fraction(pn, N2 * BAG), Fraction(bn, N2)
            if len(L["pick"][k]) != len(vs) or sum(L["pick"][k]) > BAG or any(x < 0 for x in L["pick"][k]):
                bad.append(f"{tag}: the picked orders at budget {k} are not within the {BAG} first-bag orders")
            if vs and not (max(js) <= joint <= min(Fraction(1), sum(js))):
                bad.append(f"{tag}: the family joint at budget {k} is outside the sandwich of its variants")
            if vs and not (built <= min(Fraction(1), sum(bs))):
                bad.append(f"{tag}: the family built at budget {k} exceeds the sum of its variants")
            if bn > N2 or (pn > 0 and bn == 0):  # a family can build at a budget whose classes never clear (PC 0)
                bad.append(f"{tag}: built / PC counts at budget {k} disagree")
        for a, b2 in zip(BK, BK[1:]):
            if L["num"][a][1] > L["num"][b2][1]:
                bad.append(f"{tag}: the family PC counts are not monotone from budget {a} to {b2}")


def audit_orders(island, R, orders):
    """Each card's decision list and each live class's order line, re-read from the orders artefact by a second route.
    From `w` (the set of orders that build a class, read against this module's own permutation table): its size is n_inf
    and positive, the 21 pair counts are the artefact's, the island line is (n0, n_inf, held). The plan is walked with U,
    the orders not yet decided, starting as every order some live class builds: `none` is the rest of the 5040; the
    steps name live classes in increasing order; every rule is non-empty, valid (every order of U it matches builds the
    step's class), minimal (dropping any precedence breaks that) and matches exactly its recorded number of orders of U,
    which it then decides; a step's total is its rules' sum; the else class comes after every step and builds all of U;
    `open` is what is left; and the island plan is the artefact's with classes read as tile positions. The no-180 section
    (island `d1`, `pl1`) is audited the same way, without pair counts, with a class allowed no order at all, and every
    order it builds a class with must build that class with 180 too."""
    bad = []
    P = order_perms()
    pos = [{c: i for i, c in enumerate(o)} for o in P]
    pre = {a + b: sum(1 << k for k in range(BAG) if pos[k][a] < pos[k][b]) for a in "IJLOSTZ" for b in "IJLOSTZ" if a != b}
    full = (1 << BAG) - 1

    def conj(c):
        m = full
        for q in c:
            m &= pre[q]
        return m
    pc = lambda x: bin(x).count("1")
    for r, _ in R:
        c = island["cards"].get(r["name"], {})
        lv = live(r)
        w180 = {}
        for sec, dk, pk, sname in ((orders, "d", "pl", ""), (orders["no180"], "d1", "pl1", " (no 180)")):
            main = sec is orders
            if len(c.get(dk) or []) != len(lv):
                bad.append(f"island card {r['name']}{sname}: one order line per live class")
                continue
            ws = {}
            for i, d in zip(lv, c[dk]):
                v = sec["orders"].get(f'{r["name"]}#{i}')
                tag = f"island card {r['name']} class {i}{sname}"
                if not d or not v or len(d) != 3:
                    bad.append(f"{tag}: no order line")
                    continue
                w = int.from_bytes(base64.b64decode(v["w"]), "little")
                ni = v["n"][3]
                if pc(w) != ni or (main and ni <= 0) or w & ~full:
                    bad.append(f"{tag}: w is not the n_inf orders")
                    continue
                ws[i] = w
                if main:
                    w180[i] = w
                    if [pc(w & pre[q]) for q in orders["pairs"]] != v["pairs"]:
                        bad.append(f"{tag}: the pair counts are not w's")
                elif i in w180 and w & ~w180[i]:
                    bad.append(f"{tag}: an order builds the class without 180 but not with it")
                if d != [v["n"][0], ni, r["held"]]:
                    bad.append(f"{tag}: the order line is not (n0, n_inf, held)")
            tag = f"island card {r['name']} plan{sname}"
            pl = sec["plans"].get(r["name"])
            if pl is None or len(ws) != len(lv):
                bad.append(f"{tag}: no plan")
                continue
            U = 0
            for w in ws.values():
                U |= w
            if pl["none"] != pc(full & ~U):
                bad.append(f"{tag}: the never-built count")
            last = -1
            for i, rs, tot in pl["steps"]:
                if i not in ws or lv.index(i) <= last:
                    bad.append(f"{tag}: step class {i} is not a live class after the last step")
                    continue
                last = lv.index(i)
                w = ws[i]
                if not rs or tot != sum(n for _c, n in rs):
                    bad.append(f"{tag}: step {i}'s total")
                for cj, n in rs:
                    if not cj or len(set(cj)) != len(cj) or len(cj) > 3 or any(q not in pre for q in cj):
                        bad.append(f"{tag}: step {i} rule {cj} is malformed")
                        continue
                    m = conj(cj)
                    if m & U & ~w:
                        bad.append(f"{tag}: step {i} rule {','.join(cj)} matches an order that does not build the class")
                        continue
                    for q in cj:
                        if len(cj) > 1 and not conj([x for x in cj if x != q]) & U & ~w:
                            bad.append(f"{tag}: step {i} rule {','.join(cj)} is not minimal")
                    if pc(m & U) != n or n <= 0:
                        bad.append(f"{tag}: step {i} rule {','.join(cj)}'s count")
                    U &= ~m
            if pl["else"] is not None:
                i, n = pl["else"]
                if i not in ws or lv.index(i) <= last or U & ~ws[i] or n != pc(U):
                    bad.append(f"{tag}: the else class does not build every order left")
                else:
                    U = 0
            if pl["open"] != pc(U):
                bad.append(f"{tag}: the open count")
            if c.get(pk) != card_plan(sec, r):
                bad.append(f"{tag}: the island plan is not the artefact's")
    return bad


def audit(page, art, cat, PR, pcxd=None, builds=None, L=None, orders=None):
    builds = builds if builds is not None else load_builds()
    L = L if L is not None else load_sets()
    orders = orders if orders is not None else load_orders()
    pcxd = pcxd if pcxd is not None else load_pcx()
    bad = RP.audit_quarantine(page, [RS.EYEBROW, RS.NO_CLAIM, PR["quarantine"]], DATA_ID)
    bad += audit_sets(page, art, cat, PR, L)
    if PR["held_note"] not in page or f'<a href="{HELD_PAGE}">' not in page:
        bad.append("the note or the link to the reference page is missing")
    if set(page) & SIMPLIFIED:
        bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
    # every prose key the script reads from D.cl must be one the island carries
    used = set(re.findall(r"D\.cl\.(\w+)", page))
    if used - set(CL_KEYS):
        bad.append(f"the script reads prose key(s) {sorted(used - set(CL_KEYS))} the island does not carry")
    R, U = ranked(art, cat), unranked(art, cat)
    b1lib = bag1_library()
    th = threshold(art)
    by = mirror_index(art)
    cards = _CARD.findall(page)
    if [c[0] for c in cards] != [r["name"] for r, _ in R]:
        bad.append(f"the cards are not the ranked pairs in rank order (page {len(cards)}, artefact {len(R)})")
        return bad
    # the pruning numbers and the mirror sentence
    pr = {k: v for k, v in _PR.findall(page)}
    want_pr = {k: str(v) for k, v in pr_figs(art).items()}
    if pr != want_pr:
        bad.append(f"the printed pruning numbers {pr} are not the artefact's {want_pr}")
    # the artefact's per-kind pruning numbers are its own boards': kept = the boards of that kind, placed ones first
    kd = art["prune"]["kinds"]
    for k in KINDS:
        if sum(1 for b in art["boards"] if b["kind"] == k) != kd[k][1] or kd[k][1] > kd[k][0]:
            bad.append(f"the artefact's pruning numbers for kind {k} {kd[k]} are not its boards'")
    if kd["placed"][0] + kd["held"][0] != art["prune"]["boards_total"] or kd["placed"][1] + kd["held"][1] != art["prune"]["kept"]:
        bad.append("the artefact's pruning totals are not the sum over its kinds")
    kinds_seq = [b["kind"] for b in art["boards"]]
    if kinds_seq != sorted(kinds_seq, key=KINDS.index):
        bad.append("the artefact's boards are not the placed ones first")
    for b in art["boards"]:
        letters = sorted(k for k, _ in b["pieces"])
        if b["kind"] == "held":
            if letters != sorted("IJLOSZ") or b["held"] != "T" or not b["name"].startswith("h"):
                bad.append(f"board {b['name']}: a held board is not the six pieces IJLOSZ with the T in hold")
        elif letters.count("T") != 1 or b["held"] == "T" or not b["name"].startswith("t") or len(set(letters)) != len(letters):
            bad.append(f"board {b['name']}: a placed board is not six distinct pieces with exactly one T")
        if by[b["mirror"]]["kind"] != b["kind"]:
            bad.append(f"board {b['name']}: its mirror is of the other kind")
    # the kind attribute of every card and the kind bar's counts
    ck = dict(_CARDKIND.findall(page))
    if ck != {r["name"]: r["kind"] for r, _ in R}:
        bad.append("a card's data-kind is not its board's kind in the artefact")
    kb = {k: html.unescape(v) for k, v in _KBTN.findall(page)}
    if kb != kind_labels(R, PR):
        bad.append(f"the kind bar {kb} is not the recomputed {kind_labels(R, PR)}")
    for name, body in ((n, b) for n, _rk, b in cards):
        rr = next(r for r, _ in R if r["name"] == name)
        if f'<span class="kc kc-{rr["kind"]}" data-kc="1">{_esc(PR["card"]["kind_" + rr["kind"]])}</span>' not in body:
            bad.append(f"card {name}: the kind chip is missing or of the other kind")
    if PR["mirror_assumed" if art["mirror"]["assumed"] else "mirror_counted"] not in page:
        bad.append("the mirror sentence does not match the artefact's `mirror.assumed`")
    # the artefact's own invariants a page figure rests on
    seen = set()
    for r, _ in R:
        if ex_classes(cat, r) != [tuple(c) for c in r["classes"]]:
            bad.append(f"board {r['name']}: the artefact's classes are not what its shapes' tilings give")
        if len(holders(cat, r)) != len(live(r)):
            bad.append(f"board {r['name']}: a class that ends deals has no tiling holding the board")
        for k in BK:
            c = r["cum"][k]
            if any(c[i] > c[i + 1] for i in range(len(c) - 1)) or c[-1] > N2:
                bad.append(f"board {r['name']}: cum[{k}] is not a non-decreasing count within 5040^2")
        for a, b2 in zip(BK, BK[1:]):
            if r["cum"][a][-1] > r["cum"][b2][-1]:
                bad.append(f"board {r['name']}: the soft-drop budgets are not monotone")
    rk, od = rank_data(art, R)
    fam = families(art, cat)
    audit_layouts(art, bad)
    if "4 巡" in page or "第 4 包" in page:
        bad.append("the page mentions a 4th bag: this page counts bag 3 only")
    rkm = {r["name"]: rk[BK_SHOWN][i] for i, (r, _) in enumerate(R)}
    for n, (name, rkt, body) in enumerate(cards):
        r, m = R[n]
        f = {k: re.sub(r"<[^>]+>", "", html.unescape(v)) for k, v in OP._FIG.findall(body)}
        ex = ex_strings(r)
        want = ex[BK_SHOWN]
        if [f.get("two"), f.get("pc3"), f.get("joint")] != want:
            bad.append(f"card {name}: printed figures {[f.get('two'), f.get('pc3'), f.get('joint')]} are not the recomputed {want}")
        if [f.get("tsd"), f.get("tsdj")] != ex_tstrings(r, L["pt"][name])[BK_SHOWN]:
            bad.append(f"card {name}: the TST->TSD->PC figures are not the recomputed ones")
        if any(not 0 <= q <= c[2] for q, c in zip(L["pt"][name], r["classes"])):
            bad.append(f"card {name}: a TST->TSD->PC count is over the class's any-PC count")
        if [f.get("sd0"), f.get("sd1"), f.get("sd2")] != [ex[k][2] for k in ("0", "1", "2")]:
            bad.append(f"card {name}: the soft-drop line is not the recomputed one")
        if "未計" in want and "0%" in (f.get("pc3"),):
            bad.append(f"card {name}: a 0% PC where 未計 is required")
        cm = re.search(r'data-cnt="1">(.*?)</div>', body, re.S)
        if not cm or html.unescape(cm.group(1)) != ex_counts(r, BK_SHOWN, PR["card"]):
            bad.append(f"card {name}: the counts line is not the recomputed one at the opening budget")
        sm = re.search(r'<div class="src">(.*?)</div>', body, re.S)
        src = html.unescape(sm.group(1)) if sm else ""
        body_src = re.sub(r"^【[^】]*】", "", src)
        for sid in r["shapes"]:
            for nm in cat[sid]["names"]:
                if sid < ID_OFFSET and route_of(nm) and ROUTE[route_of(nm)] not in body_src and len(body_src.split(", ")) < 4:
                    bad.append(f"card {name}: the title lacks the route opener {ROUTE[route_of(nm)]}")
        bm = re.search(r'data-b1="([^"]*)" data-b1s="([^"]*)"', body)
        b1x, b1s = bag1_names(r, b1lib)
        if not bm or [html.unescape(bm.group(1)), html.unescape(bm.group(2))] != ["|".join(b1x), "|".join(b1s)]:
            bad.append(f"card {name}: the bag-1 names are not the recomputed {b1x} / {b1s}")
        for nm in b1x:
            if PR["b1_prefix"].format(n="、".join(b1x)) not in src:
                bad.append(f"card {name}: the title lacks the bag-1 opener {nm}")
        if b1x and not _b1_grid_check(r, b1x, b1lib):
            bad.append(f"card {name}: a named bag 1 does not draw the same board cell for cell")
        if f'（hold {r["held"]}）' not in src:
            bad.append(f"card {name}: the title does not name the hold piece")
        if rkt != rk[BK_SHOWN][n]:
            bad.append(f"card {name}: the opening rank {rkt} is not the recomputed {rk[BK_SHOWN][n]}")
        shown_rk = re.search(r'<div class="rk num">(.*?)</div>', page[page.index(f'data-card="{name}"'):], re.S).group(1)
        if shown_rk != rkt:
            bad.append(f"card {name}: the rank badge and its data-rk differ")
        mm = _MIR.search(body)
        em = ex_strings(m)
        if not mm or (mm.group(1) == "1") != (em == ex):
            bad.append(f"card {name}: the mirror line says the wrong thing about the mirror board")
        elif mm.group(1) == "0":
            got = {k: v for k, v in _MF.findall(mm.group(2))}
            if got != {k: " · ".join(em[k]) for k in BK}:
                bad.append(f"card {name}: the mirror board's figures are not the recomputed ones")
        if by[r["mirror"]] is not m:
            bad.append(f"card {name}: the mirror board is not the artefact's")
        # the with-mirror pair line: the policy over the card's board and its mirror board
        pm = re.search(r'data-pair="1">(.*?)</div>', body, re.S)
        try:
            PP = pair_of(art, r["name"], m["name"])
        except KeyError:
            PP = None
        if PP is None or not pm:
            bad.append(f"card {name}: the with-mirror pair line or its artefact entry is missing")
        else:
            wp = {k: PR["card"]["pair_line"].format(a=fam_strings(PP, k)[0], b=fam_strings(PP, k)[1], c=fam_strings(PP, k)[2])
                  for k in BK}
            gp = {k: html.unescape(v) for k, v in re.findall(r'data-fl="(\w+)"[^>]*>(.*?)</span>', pm.group(1))}
            if gp != wp:
                bad.append(f"card {name}: the with-mirror pair line is not the recomputed one")
            jp = Fraction(PP["num"][BK_SHOWN][1], N2 * BAG)
            if jp < max(figs(r, BK_SHOWN)[2], figs(m, BK_SHOWN)[2]):
                bad.append(f"card {name}: the with-mirror joint is below a hand's own")
        # the hold-swap family: the card's best layout, its variants' own joints, its policy figures
        fb = re.search(r'<details class="fam" data-fam="(\d+)">(.*?)</details>', body, re.S)
        idx = card_layouts(r, m, art, fam[0])
        if not idx:
            if fb:
                bad.append(f"card {name}: a family block on a board with no layout")
        elif not fb or int(fb.group(1)) != idx[0]:
            bad.append(f"card {name}: the family block is missing or is not the best layout {idx[0]}")
        else:
            FL = art["families"]["list"][idx[0]]
            fbody = fb.group(2)
            rows = re.findall(r'<tr data-fv="(\w+)">(.*?)</tr>', fbody, re.S)
            if [x for x, _ in rows] != FL["variants"]:
                bad.append(f"card {name}: the family rows {[x for x, _ in rows]} are not the layout's {FL['variants']}")
            byn = all_boards(art)
            for j, (vn, rb) in enumerate(rows):
                v = byn.get(vn)
                got = dict(re.findall(r'data-fg="(\w+)">(.*?)</td>', rb))
                if v is None or got != {k: ex_strings(v)[k][2] for k in BK}:
                    bad.append(f"card {name}: family variant {vn}'s figures are not its recomputed joints")
                if vn not in {b["name"] for b in art["boards"]} and ("<a " in rb or 'data-fr="1">–</td>' not in rb):
                    bad.append(f"card {name}: family variant {vn} has no card, so it takes no rank and no link")
                pk = dict(re.findall(r'data-fl="(\w+)"[^>]*>(\d+)</span>', rb))
                if pk != {k: str(FL["pick"][k][j]) for k in BK}:
                    bad.append(f"card {name}: family variant {vn}'s picked orders are not the artefact's")
            ff = re.search(r'<tr data-ffam="1">(.*?)</tr>', fbody, re.S)
            if not ff:
                bad.append(f"card {name}: the family row is missing")
            else:
                got = dict(re.findall(r'data-ff="(\w+)">(.*?)</td>', ff.group(1)))
                if got != {k: fam_strings(FL, k)[2] for k in BK}:
                    bad.append(f"card {name}: the family joints are not the recomputed ones")
                tot = dict(re.findall(r'data-fl="(\w+)"[^>]*>(\d+)</span>', ff.group(1)))
                if tot != {k: str(sum(FL["pick"][k])) for k in BK}:
                    bad.append(f"card {name}: the family's built-order totals are not the picks' sum")
            lm = re.search(r'data-fline="1">(.*?)</p>', fbody, re.S)
            want = {k: PR["card"]["fam_line"].format(a=fam_strings(FL, k)[0], b=fam_strings(FL, k)[1], c=fam_strings(FL, k)[2]) for k in BK}
            got = {k: html.unescape(v) for k, v in re.findall(r'data-fl="(\w+)"[^>]*>(.*?)</span>', lm.group(1))} if lm else {}
            if got != want:
                bad.append(f"card {name}: the family line is not the recomputed one")
            bm = re.search(r'data-fboth="1">(.*?)</p>', fbody, re.S)
            wb = {k: PR["card"]["fam_both"].format(a=fam_strings(FL["both"], k)[0], b=fam_strings(FL["both"], k)[1],
                                                    c=fam_strings(FL["both"], k)[2]) for k in BK}
            gb = {k: html.unescape(v) for k, v in re.findall(r'data-fl="(\w+)"[^>]*>(.*?)</span>', bm.group(1))} if bm else {}
            if gb != wb:
                bad.append(f"card {name}: the family's with-mirror line is not the recomputed one")
            mir = {byn[x]["mirror"] for x in FL["variants"]}
            if set(FL["both"]["variants"]) != set(FL["variants"]) | mir:
                bad.append(f"card {name}: the family's with-mirror variants are not the variants and their mirror boards")
            om = re.search(r'data-fother="1">(.*?)</p>', fbody, re.S)
            if (len(idx) > 1) != bool(om) or (om and html.unescape(om.group(1)) != PR["card"]["fam_other"].format(n=len(idx) - 1)):
                bad.append(f"card {name}: the note on the other layouts is wrong")
    for k in BK:
        j = [Fraction(sum((r["cum"][k][i] - (r["cum"][k][i - 1] if i else 0)) * r["classes"][i][2] for i in range(len(r["classes"]))), N2 * BAG)
             for r, _ in R]
        for i, (r, _) in enumerate(R):
            if (rk[k][i] != "–") != (j[i] > th):
                bad.append(f"board {r['name']}: a rank at budget {k} is printed at or below the threshold, or missing above it")
        if sorted(od[k]) != list(range(len(R))) or [i for i, _ in sorted(enumerate(od[k]), key=lambda x: x[1])] != \
                sorted(range(len(R)), key=lambda i: (-j[i], i)):
            bad.append(f"budget {k}: the card order is not by that budget's figure")
    bad += audit_pcx(cards, R, cat, pcxd)
    # the ranking table and the folded table
    got = [(n, {k: re.sub(r"<[^>]+>", "", v) for k, v in _G.findall(b)}) for n, b in _TROW.findall(page)]
    exp_order = sorted(range(len(R)), key=lambda i: (-sum((R[i][0]["cum"][TABLE_BK][j] - (R[i][0]["cum"][TABLE_BK][j - 1] if j else 0)) * R[i][0]["classes"][j][2]
                                                          for j in range(len(R[i][0]["classes"]))), i))[:TABLE_SHOWN]
    if [g[0] for g in got] != [R[i][0]["name"] for i in exp_order]:
        bad.append("the ranking table is not the recomputed ranking")
    else:
        for (name, fg), i in zip(got, exp_order):
            ex = ex_strings(R[i][0])
            if [fg.get(k) for k in BK] != [ex[k][2] for k in BK] or fg.get("main") != rk[BK_SHOWN][i]:
                bad.append(f"ranking table row {name}: figures are not the recomputed ones")
    gi = [(n, {k: re.sub(r"<[^>]+>", "", v) for k, v in _G.findall(b)}) for n, b in _IROW.findall(page)]
    if [g[0] for g in gi] != [r["name"] for r, _ in U]:
        bad.append("the unranked table is not the artefact's unranked pairs")
    else:
        for (name, fg), (r, _) in zip(gi, U):
            ex = ex_strings(r)
            if [fg.get(k) for k in BK] != [ex[k][2] for k in BK]:
                bad.append(f"unranked table row {name}: figures are not the recomputed ones")
    # the island
    m = OP._ISLAND.search(page)
    if not m:
        bad.append("no data island")
    else:
        try:
            island = json.loads(m.group(1).replace("<\\/", "</"))
        except ValueError:
            island = None
        if island != build_data(art, cat, R, PR, builds, pcxd, orders, L["pt"]):
            bad.append("the data island is not what the artefact builds")
        if island:
            bad += audit_builds(island, R, cat, pcxd)
            bad += audit_orders(island, R, orders)
        if island == build_data(art, cat, R, PR, builds, pcxd, orders, L["pt"]):
            for n, (r, _) in enumerate(R):
                c = island["cards"][r["name"]]
                if c["cnt"] != {k: ex_counts(r, k, PR["card"]) for k in BK}:
                    bad.append(f"island card {r['name']}: the counts lines are not the recomputed ones")
                if c["ft"] != ex_tstrings(r, L["pt"][r["name"]]):
                    bad.append(f"island card {r['name']}: the TST->TSD->PC figures are not the recomputed ones")
                if c["f"] != ex_strings(r):
                    bad.append(f"island card {r['name']}: figures are not the recomputed ones")
                lv = live(r)
                if len(c["t"]) != len(lv):
                    bad.append(f"island card {r['name']}: not one row per live class")
                bs = piece_set(r["pieces"])
                for row, (si, left, p5) in zip(c["t"], [r["classes"][i] for i in lv]):
                    g = row[0]
                    up = {(i, ch) for i, ch in enumerate(g) if ch.isupper()}
                    H = len(g) // 10
                    cells = {(H - 1 - i // 10) * 10 + i % 10: ch for i, ch in enumerate(g) if ch != "."}
                    own = {cc: k for k, cs in r["pieces"] for cc in cs}
                    if {cc: ch for cc, ch in cells.items() if ch.isupper()} != own:
                        bad.append(f"island card {r['name']}: a row's bag-1 pieces are not the board's")
                    ok = any(set(cells) == {cc for _, cs in t["pieces"] for cc in cs} and bs <= t["set"] and t["left"] == left
                             for t in cat[r["shapes"][si]]["til"] if t["B"] > 0)
                    if not ok:
                        bad.append(f"island card {r['name']}: a row's drawing is not a tiling of its shape holding the board")
                    if row[2] != (left or "–") or row[3] != pct(Fraction(p5, BAG)):
                        bad.append(f"island card {r['name']}: a row's leftover or p5 is not the class's")
                ds = {k: deltas(r, k) for k in BK}
                for ri, row in zip(lv, c["t"]):
                    if row[4:] != [pct(Fraction(ds[k][ri], N2)) for k in BK]:
                        bad.append(f"island card {r['name']}: a row's share of the deals is not the recomputed one")
    return bad



# ------------------------------------------------------------------ audit of the 學邊幾個 section

class _TreeParse(HTMLParser):
    """The rule's nested lines as a token list: ('q', feature), ('leaf', member), ('li', a), ('/li',), ('ul',), ('/ul',)."""
    def __init__(self):
        super().__init__()
        self.tok = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "span" and "data-q" in a:
            self.tok.append(("q", a["data-q"]))
        elif tag == "span" and "data-leaf" in a:
            self.tok.append(("leaf", int(a["data-leaf"])))
        elif tag == "li":
            self.tok.append(("li", a.get("data-a")))
        elif tag == "ul":
            self.tok.append(("ul",))

    def handle_endtag(self, tag):
        if tag in ("li", "ul"):
            self.tok.append(("/" + tag,))


def parse_rule(body):
    """The decision tree a rule block's markup says, or None when it is not a well-formed binary tree."""
    p = _TreeParse()
    p.feed(body)
    tk, pos = p.tok, [0]

    def peek():
        return tk[pos[0]] if pos[0] < len(tk) else ("end",)

    def eat(k):
        if peek()[0] != k:
            raise ValueError(k)
        pos[0] += 1
        return tk[pos[0] - 1]

    def node():
        if peek()[0] == "leaf":
            return {"m": eat("leaf")[1]}
        f = eat("q")[1]
        eat("ul")
        kids = {}
        for a in ("y", "n"):
            eat("li")
            if tk[pos[0] - 1][1] != a:
                raise ValueError("li")
            kids[a] = node()
            eat("/li")
        eat("/ul")
        return {"f": f, "feature": f, "y": kids["y"], "n": kids["n"]}
    try:
        n = node()
    except ValueError:
        return None
    return n if pos[0] == len(tk) else None


def ex_set(art_by, vecs, names, bk, pt=None):
    """A second route to a set's picks: per-order tables rebuilt from the cumulative counts with exact fractions, the
    forward identity cum_b = sum_s n_s * D(b - s) checked on the way, ties to the earlier member. Returns (picks, pc3, built)."""
    lim = _lim(bk)
    tabs = []
    for n in names:
        b, v = art_by[n], [INFEAS if c == "." else int(c) for c in vecs[n]]
        cnt = collections.Counter(v)
        try:
            Dfin, Dinf = _solve_d(b["cum"], v)
        except ValueError:
            return None
        for bb in (0, 1, 2):
            if any(c * 1 for c in b["cum"][str(bb)]):
                for k, c in enumerate(b["cum"][str(bb)]):
                    if sum(cnt[s] * Dfin[bb - s][k] for s in range(bb + 1) if (bb - s) in Dfin) != c:
                        return None
        p5 = pt[n] if pt else [c[2] for c in b["classes"]]

        def at(row):
            d0, j = 0, 0
            for d, p in zip(row, p5):
                j += (d - d0) * p
                d0 = d
            return j, row[-1]
        tabs.append((v, {s: at(Dinf if bk == "inf" else Dfin[int(bk) - s]) for s in range(INFEAS)
                         if s <= lim and (bk == "inf" or (int(bk) - s) in Dfin)}))
    out, pc, bt = [], 0, 0
    for o in range(BAG):
        best = None
        for i, (v, tab) in enumerate(tabs):
            if v[o] in tab and (best is None or tab[v[o]] > best[1]):
                best = (i, tab[v[o]])
        if best is None:
            out.append("x")
        else:
            out.append(str(best[0]))
            pc += best[1][0]
            bt += best[1][1]
    return "".join(out), pc, bt


_SX_MEMO = {}


def audit_sets(page, art, cat, PR, L):
    sx = page[page.find('<section class="sx"'):page.find("</section>", page.find('<section class="sx"')) + 10]
    isl = _SXISL.search(page)
    bar = page.find('<div class="bar" data-bar="sd">') > page.find("<main>")
    key = (hashlib.sha256((sx + (isl.group(1) if isl else "") + str(bar) + str(page.count('<div class="bar" data-bar="sd">'))
                           + str(page.find('<div class="bar" data-bar="sd">') > page.find('<section class="sx"'))).encode()).digest(),
           id(L["S"]), json.dumps(art["boards"][:1], sort_keys=True), hashlib.md5(json.dumps(art, sort_keys=True).encode()).digest())
    if key not in _SX_MEMO:
        try:
            _SX_MEMO[key] = _audit_sets(page, art, cat, PR, L)
        except ValueError as e:
            _SX_MEMO[key] = [f"the 學邊幾個 audit cannot recompute from the artefact: {e}"]
    return list(_SX_MEMO[key])


def _audit_sets(page, art, cat, PR, L):
    S, SP, bad = L["S"], PR["sets"], []
    sec = _SX.findall(page)
    if len(sec) != 1:
        return ["the 學邊幾個 section is not on the page exactly once"]
    body = sec[0]
    if page.count('<div class="bar" data-bar="sd">') != 1 or page.find('<div class="bar" data-bar="sd">') > page.find('<section class="sx"'):
        bad.append("the soft-drop bar is not once, above the 學邊幾個 section")
    by = {b["name"]: b for b in list(art["boards"]) + list(L["X"]["boards"])}
    names_at = [b["name"] for b in list(art["boards"]) + list(L["X"]["boards"])]
    posn = {n: i for i, n in enumerate(names_at)}
    R = ranked(art, cat)
    reps = {r["name"] for r, _ in R}
    rep_of = {p["name"]: r["name"] for r, p in R}
    sfx = art["mirror"]["suffix"]
    blocks = _SXBK.findall(body)
    if [b[0] for b in blocks] != BK:
        return bad + ["the section does not hold one block per soft-drop budget, in order"]
    ix = _SXISL.findall(page)
    isl = None
    if len(ix) == 1:
        try:
            isl = json.loads(ix[0].replace("<\\/", "</"))
        except ValueError:
            isl = None
    if isl is None:
        bad.append("the section's island is missing or not JSON")
    picks_ex = {}
    for bk, blk in blocks:
        bb = S["budgets"][bk]
        rows = {(k, int(i)): (a, j, b, g, nm, tx) for k, i, a, j, b, g, nm, tx in _SXROW.findall(blk)}
        prev = None
        for k in (1, 2, 3, 4, 5):
            m = _members(S, bk, k)
            nm = [x["name"] for x in m["boards"]]
            if len(m["pairs"]) != k or sorted(i for q in m["pairs"] for i in q) != sorted(posn[n] for n in nm) or \
                    any(len(q) == 2 and by[names_at[q[0]]]["mirror"] != names_at[q[1]] for q in m["pairs"]):
                bad.append(f"{bk}/{k}: the set is not {k} mirror pairs whose boards are the listed ones")
            got = rows.get((bk, k))
            ex = ex_set(by, L["vecs"], nm, bk, L.get("pt"))
            if ex is None:
                bad.append(f"{bk}/{k}: a board's cumulative counts do not satisfy the soft-drop identity")
                continue
            if (ex[1], ex[2]) != (m["pc3"], m["built"]):
                bad.append(f"{bk}/{k}: the set's recomputed figures are not the artefact's")
            js = pct(Fraction(ex[1], BAG ** 3))
            want = (html.escape(SP["k_label"].format(k=k), quote=False), js, pct(Fraction(ex[2], BAG ** 2)),
                    gain_text(prev, js, SP), " ".join(nm),
                    html.escape("、".join(sx_set_names(cat, by, nm, sfx, PR)), quote=False) + " " + sx_ids(nm))
            if got is None or tuple(got) != tuple(want):
                bad.append(f"{bk}/{k}: the ladder row is not the recomputed one")
            prev = js
        wantref = ref_html(L["Sref"], bk, SP, cat, by, sfx, PR, lambda nm: ex_set(by, L["vecs"], nm, bk) or (None, 0, 0))
        if blk.count('<details class="sx-ref"') != 1 or wantref not in blk:
            bad.append(f"{bk}: the folded reference sets are not the any-PC objective's recomputed ones")
        e1, e2, e3 = (_members(S, bk, k) for k in (1, 2, 3))
        mem = [x["name"] for x in e3["boards"]]
        pk = ex_set(by, L["vecs"], mem, bk, L.get("pt"))
        picks_ex[bk] = pk[0] if pk else None
        lead = _SXLEAD.findall(blk)
        lp = lead_parts(cat, by, sfx, PR, S, bk)
        wl = [lead_html(SP, *lp)] if lp else []
        if lead != wl:
            bad.append(f"{bk}: the lead sentence is not the one the ladder gives")
        figs_ = _SXFIG.findall(blk)
        if [f[0] for f in figs_] != mem:
            bad.append(f"{bk}: the drawn boards are not the best three")
        for i, (n, sh, fb) in enumerate(figs_):
            if pk and int(sh) != pk[0].count(str(i)):
                bad.append(f"{bk}: {n}'s share of orders is not the recomputed one")
            if html.unescape(fb).count(pct(Fraction(int(sh), BAG))) < 1 or SP["share"].format(n=sh, p=pct(Fraction(int(sh), BAG))) not in html.unescape(fb):
                bad.append(f"{bk}: {n}'s share sentence is not the figure's")
            card = f'href="#c{n if n in reps else rep_of.get(n, "")}"'
            if (n in reps or n in rep_of) != (card in fb) or (n in rep_of and n not in reps and rep_of[n] not in html.unescape(fb)):
                bad.append(f"{bk}: {n}'s card link is wrong")
            if by[n]["mirror"] in mem and SP["mirror_in"].format(m=sx_label(cat, by[by[n]["mirror"]], sfx, PR)) not in html.unescape(fb):
                bad.append(f"{bk}: {n} does not say it mirrors {by[n]['mirror']}")
            if f'<b>{html.escape(sx_label(cat, by[n], sfx, PR), quote=False)}</b> {sx_ids([n])}' not in fb:
                bad.append(f"{bk}: {n}'s heading is not its opener-and-hand name with the id beside it")
            if f'data-np="{sx_pics(cat, by[n], sfx)}"' not in fb:
                bad.append(f"{bk}: {n}'s picture count is not the catalogue's")
            cells = len(re.findall(r"<rect", fb))
            if cells < 28:
                bad.append(f"{bk}: {n}'s drawing holds fewer than its 28 cells")
        fx = _SXFX.findall(blk)
        fxn = [x["name"] for x in S["fixed"]["boards"]]
        fv = ex_set(by, L["vecs"], fxn, bk, L.get("pt"))
        want = fixed_html(SP, set(mem) == set(fxn), sx_set_names(cat, by, fxn, sfx, PR), {"pc3": fv[1], "built": fv[2]} if fv else {"pc3": 0, "built": 0},
                          Fraction(e3["pc3"] - fv[1], BAG ** 3) if fv else 0)
        if fx != [want] or not fv or (fv[1], fv[2]) != (S["fixed"]["values"][bk]["pc3"], S["fixed"]["values"][bk]["built"]):
            bad.append(f"{bk}: the fixed-set sentence is not the recomputed one")
        rl = _SXRULE.findall(blk)
        if len(rl) != 1:
            bad.append(f"{bk}: not exactly one rule")
            continue
        depth, rbody, loss = rl[0]
        tree = parse_rule(rbody)
        d = rule_depth(bb["rule"], BAG ** 3)
        if tree is None or depth != d:
            bad.append(f"{bk}: the rule's tree is malformed or not the printed depth")
            continue
        labels = [sx_label(cat, by[n], sfx, PR) for n in mem]
        if tree_html(tree, labels, SP) != rbody:
            bad.append(f"{bk}: the rule's wording is not the tree's")
        # evaluate the tree the page prints on every order, with positions rather than the artefact's feature code
        def holds(f, o):
            return o[0] == f[6] if f.startswith("first=") else o.find(f[0]) < o.find(f[2])
        pcs = bts = diff = unb = 0
        v = [[INFEAS if c == "." else int(c) for c in L["vecs"][n]] for n in mem]
        T = set_tables(by, L, mem)
        if pk:
            for o, p in enumerate(all_perms()):
                t = tree
                while "m" not in t:
                    t = t["y"] if holds(t["feature"], p) else t["n"]
                c = v[t["m"]][o]
                diff += pk[0][o] != "x" and str(t["m"]) != pk[0][o]
                if c > _lim(bk):
                    unb += 1
                else:
                    pcs += T[mem[t["m"]]][1][bk][0][c]
                    bts += T[mem[t["m"]]][1][bk][1][c]
            r = {"pc3": pcs, "built": bts, "differs": diff, "unbuildable": unb}
            if any(r[k] != bb["rule"][d][k] for k in r):
                bad.append(f"{bk}: the rule's recomputed figures are not the artefact's")
            if loss != rule_loss_html(SP, r, e3, BAG ** 3, BAG ** 2):
                bad.append(f"{bk}: the rule's loss sentence is not the recomputed one")
        if isl and len(figs_) == len(mem) and isl["m"].get(bk, {}).get("3") != mem:
            bad.append(f"{bk}: the lookup's members are not the best three")
    if isl:
        P = all_perms()
        if isl["fix"] != [[P[i], i] for i in FIX_IDX] or any(P.index(p) != i for p, i in isl["fix"]):
            bad.append("the lookup's order-index fixtures are not the permutation ranks")
        if isl.get("ks") != list(SX_KS) or isl.get("k0") != SX_K0 or "2" not in isl.get("ks", []):
            bad.append("the lookup's choices of how many boards to learn are not 1, 2, 3 opening on 2")
        mem = {bk: {k: sx_members(S, bk, k) for k in SX_KS} for bk in BK}
        if isl["m"] != mem:
            bad.append("the lookup's board sets for 1, 2 and 3 boards are not the artefact's")
        for bk in BK:
            for k in SX_KS:
                pk = ex_set(by, L["vecs"], mem[bk][k], bk, L.get("pt"))
                if not pk or isl["p"].get(bk, {}).get(k) != pk[0]:
                    bad.append(f"the lookup's pick string for the best {k} at budget {bk} is not the recomputed one")
            if isl["p"].get(bk, {}).get("3") != S["budgets"][bk]["picks"]:
                bad.append(f"the lookup's best-three picks at budget {bk} are not the artefact's")
        allm = sorted({n for v in mem.values() for w in v.values() for n in w})
        if isl["bd"] != {n: {"v": L["vecs"][n], "c": by[n]["pieces"]} for n in allm}:
            bad.append("the lookup's cost vectors or board cells are not the artefact's")
        lk = {n: sx_link(n, reps, rep_of) for n in allm}
        if isl["lk"] != lk:
            bad.append("the lookup's card links are not the page's cards")
        lb = {n: sx_label(cat, by[n], sfx, PR) for n in allm}
        for v in lk.values():
            if v:
                lb.setdefault(v[1], sx_label(cat, by[v[1]], sfx, PR))
        if isl["lb"] != lb:
            bad.append("the lookup's board names are not each board's opener-and-hand name")
        T = set_tables(by, L, sx_names(S))
        for bk in BK:
            if set(isl["f"].get(bk, {})) != {n for w in mem[bk].values() for n in w}:
                bad.append(f"the lookup's figures at budget {bk} do not name the boards of the three choices")
                continue
            for n in isl["f"][bk]:
                for s in range(INFEAS):
                    f = isl["f"][bk][n][s]
                    w = None if s > _lim(bk) else [pct(Fraction(T[n][1][bk][1][s], BAG)), pct(Fraction(T[n][1][bk][0][s], BAG ** 2))]
                    if f != w:
                        bad.append(f"the lookup's figure for {n} at {bk}/{s} is not the recomputed one")
        if isl["t"] != {k: SP[k] for k in SX_T_KEYS}:
            bad.append("the lookup's texts are not the prose's")
        tg = re.findall(r'<button data-k="(\d)" aria-pressed="(\w+)">', body)
        if tg != [(k, "true" if k == SX_K0 else "false") for k in SX_KS]:
            bad.append("the lookup's 1 / 2 / 3 toggle is not there, or does not open on 2")
    for w in ("至少", "逐個組合窮舉", "窮舉"):
        if w in re.sub(r"<[^>]+>", "", body).replace(SP["best_note"], ""):
            bad.append(f"the section says {w!r}")
    if SP["best_note"] not in html.unescape(body):
        bad.append("the section lacks the sentence that says which sets are exhaustive and which are proven by bound")
    return bad


# ------------------------------------------------------------------ driver

def render_all(repo=REPO, inputs=None, prose=None):
    art, cat = inputs or load_inputs(repo)
    PR = prose or load_prose()
    pcxd = load_pcx(repo)
    L = load_sets(repo)
    page = render(art, cat, PR, pcxd, L=L)
    bad = audit(page, art, cat, PR, pcxd, L=L)
    _need(not bad, "; ".join(bad[:5]))
    return {OVERVIEW: page}


def site_card(inputs=None, prose=None):
    art, cat = inputs or load_inputs()
    PR = prose or load_prose()
    return {"href": OVERVIEW, "cases": len(ranked(art, cat)), "unit": "個板", "kicker": PR["index_card"]["kicker"],
            "title": PR["overview_title"], "blurb": PR["index_card"]["blurb"]}


def selftest(repo=REPO):
    art, cat = load_inputs(repo)
    PR = load_prose()
    pcxd = load_pcx(repo)
    Lsets = load_sets(repo)
    page = render(art, cat, PR, pcxd, L=Lsets)
    killed = survived = 0

    def rnd(a):
        # a corrupted artefact may be refused by the section's own tables; the audit is then asked about the clean page
        try:
            return render(a, cat, PR, pcxd, L=Lsets)
        except ValueError:
            return page

    builds = load_builds(repo)

    def expect(label, mutated, want, a=None, c=None, bd=None, px=None, L=None):
        nonlocal killed, survived
        bad = audit(mutated, a or art, c or cat, PR, px or pcxd, bd or builds, L or Lsets)
        if bool(bad) == want:
            killed += want
            print(f'  {"killed" if want else "passed"}: {label}')
        else:
            survived += 1
            print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

    def sub(pattern, fn, flags=0, text=None):
        text = page if text is None else text
        m = re.search(pattern, text, flags)
        _need(m, f"selftest: nothing to plant at {pattern!r}")
        return text[:m.start(1)] + fn(m.group(1)) + text[m.end(1):]

    bump = lambda d: str((int(d) + 1) % 10)
    expect("the rendered page (control)", page, False)
    expect("the quarantine sentence deleted", page.replace(PR["quarantine"], "", 1), True)
    # TST->TSD->PC
    expect("a card's TST->TSD->PC figure edited", sub(r'data-f="tsd">(?:<[^>]*>)*(\d)', bump), True)
    expect("a reference row figure edited", sub(r'data-ref="0:2"><td>[^<]*</td><td class="num">(\d)', bump), True)
    n0 = next(iter(Lsets["pt"]))
    ptb = {**Lsets["pt"], n0: [q + 10 ** 6 for q in Lsets["pt"][n0]]}
    expect("a pt3 above p5 in the tsd lines", page, True, L={**Lsets, "pt": ptb})
    expect("the objectives swapped (any-PC sets as the main ones)", page, True, L={**Lsets, "S": Lsets["Sref"]})
    expect("the folded reference block dropped", re.sub(r'<details class="sx-ref".*?</details>', "", page, count=1, flags=re.S), True)
    expect("the reference note deleted", page.replace(PR["held_note"], "", 1), True)
    expect("the link to the reference page deleted", page.replace(f'<a href="{HELD_PAGE}">', "<a>", 1), True)
    expect("a claim badge planted", page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), True)
    expect("a simplified glyph", page.replace("</h1>", "<p>实</p></h1>", 1), True)
    expect("an external request planted", page.replace("<style>", '<link rel="stylesheet" href="https://x.example/a.css"><style>', 1), True)
    expect("the script reads a prose key the island does not carry", page.replace("D.cl.pl_r180", "D.cl.pl_r180x", 1), True)
    # 學邊幾個
    sxp = page[page.index('<section class="sx"'):page.index("</section>", page.index('<section class="sx"'))]
    expect("a ladder joint figure edited", sub(r'data-r="2:2"><td>[^<]*</td><td data-c="j">(\d)', bump), True)
    expect("a ladder built figure edited", sub(r'data-r="2:3"><td>[^<]*</td><td data-c="j">[^<]*</td><td data-c="b">(\d)', bump), True)
    expect("a ladder board name changed", sub(r'<td colspan="4" data-names="(t\d+)', lambda s: s + "9"), True)
    expect("a board's share of orders edited", sub(r'data-share="(\d)', bump), True)
    if 'data-k="lx"' in page:  # the lead sentence exists only when the best single pair is not among the best two
        expect("the lead sentence's figure edited", sub(r'data-k="lx">(\d)', bump), True)
    expect("the fixed-set figure edited", sub(r'data-k="f[jb]">(\d)', bump), True)
    expect("a rule leaf swapped", sub(r'data-leaf="(\d)"', lambda d: str((int(d) + 1) % 3)), True)
    for kk in SX_KS:
        expect(f"a lookup pick of the best {kk} edited", sub(r'"p":\{"0":\{[^}]*?"' + kk + r'":"(.)', lambda c: "1" if c != "1" else "2"), True)
    expect("a lookup set of boards edited", sub(r'"m":\{"0":\{"1":\["(t\d+)', lambda n: n + "9"), True)
    expect("a lookup board name edited", sub(r'"lb":\{"t\d+":"([^"]{2})', lambda c: "XX"), True)
    expect("a lookup board cell edited", sub(r'"c":\[\["[A-Z]",\[(\d+)', lambda d: str(int(d) + 1)), True)
    expect("a lookup card link edited", sub(r'"lk":\{"t\d+":\["(.)', lambda c: "m" if c != "m" else "c"), True)
    expect("the lookup's 1/2/3 toggle dropped", re.sub(r'<button data-k="1" aria-pressed="false">.*?</button>', "", page, count=1), True)
    expect("the lookup opening on 3", page.replace('data-k="2" aria-pressed="true"', 'data-k="2" aria-pressed="false"', 1), True)
    expect("a ladder board shown by its bare id", sub(r'<td colspan="4" data-names="[^"]*">(.*?) <span class="sx-id">', lambda t: "t105"), True)
    expect("a figure heading shown by its bare id", sub(r'<div class="sx-tt"><b>(.*?)</b>', lambda t: "t105"), True)
    expect("a ladder gain not the printed difference", sub(r'data-c="g">\+(\d)', bump), True)
    expect("the bound-proof sentence replaced by an exhaustive claim", page.replace(PR["sets"]["best_note"], "三者都係逐個組合窮舉。", 1), True)
    expect("a per-set figure called at-least", sxp and page.replace(PR["sets"]["built_note"], "砌到係至少數。", 1), True)
    expect("a lookup fixture index edited", sub(r'"fix":\[\["[A-Z]+",(\d+)', lambda d: str(int(d) + 1)), True)
    expect("a lookup cost vector edited", sub(r'"bd":\{"t\d+":\{"v":"(.)', lambda c: "9" if c != "9" else "8"), True)
    expect("a card's joint figure edited", sub(r'data-f="joint">(\d)', bump), True)
    expect("a card's two-bag figure edited", sub(r'data-f="two">(\d)', bump), True)
    expect("a card's bag-3 PC figure edited", sub(r'data-f="pc3">(\d)', bump), True)
    expect("a counts line edited", sub(r'data-cnt="1">[^<]*?(\d)', bump), True)
    expect("the route name dropped from card 1's title", sub(r'<div class="src">(.*?)</div>', lambda s: s.replace("迷走砲, ", "", 1)), True)
    expect("a bag-1 opener name dropped from a title", sub(r'<div class="src">(.*?)</div>', lambda t: t.replace(PR["b1_prefix"].format(n="迷走砲"), "", 1)), True)
    expect("a bag-1 name line emptied", re.sub(r'data-b1="[^"]+"', 'data-b1=""', page, count=1), True)
    expect("a bag-1 name planted on an unnamed board", re.sub(r'data-b1="" data-b1s=""', 'data-b1="迷走砲" data-b1s=""', page, count=1), True)
    worse = copy.deepcopy(art)
    for b in worse["boards"]:
        if b["b1"][0] and b["name"] == ranked(art, cat)[0][0]["name"]:
            b["b1"] = (["山岳積み"], [])
            break
    expect("a wrong bag-1 name in the artefact", rnd(worse), True)
    expect("a hold tag dropped from a title", sub(r'<div class="src">(.*?)</div>', lambda s: re.sub("（hold .）", "", s)), True)
    flip = lambda k: "held" if k == "placed" else "placed"
    expect("a card's data-kind flipped", sub(r'data-kind="(\w+)"', flip), True)
    expect("a card's kind chip flipped", sub(r'class="kc kc-(\w+)"', flip), True)
    expect("a kind-bar count edited", sub(r'data-k="held">[^<]*?(\d)', bump), True)
    expect("a kind-bar count edited (T placed)", sub(r'data-k="placed">[^<]*?(\d)', bump), True)
    expect("a held pruning number edited", sub(r'data-pr="kept_held">(\d)', bump), True)
    expect("a held boards total edited", sub(r'data-pr="boards_held">(\d)', bump), True)
    expect("a placed pruning number edited", sub(r'data-pr="kept_placed">(\d)', bump), True)
    worse = copy.deepcopy(art)
    hb = next(b for b in worse["boards"] if b["kind"] == "held")
    hb["held"] = "S"
    expect("a held board given held S", page, True, a=worse)
    worse = copy.deepcopy(art)
    pb = next(b for b in worse["boards"] if b["kind"] == "placed")
    pb["held"] = "T"
    expect("a placed board given held T", page, True, a=worse)
    worse = copy.deepcopy(art)
    worse["prune"]["kinds"]["held"][1] += 1
    worse["prune"]["kept"] += 1
    expect("the held pruning count edited in the artefact", page, True, a=worse)
    expect("an island card's kind flipped", sub(r'"kind":"(\w+)"', flip), True)
    expect("the kind bar deleted", re.sub(r'<div class="bar" data-bar="kind">.*?</div>', "", page, count=1, flags=re.S), True)
    expect("an island counts line edited", sub(r'"cnt":\{"0":"[^"]*?(\d)', bump), True)
    expect("a soft-drop line figure edited", sub(r'data-f="sd1">(\d)', bump), True)
    expect("a soft-drop line figure edited (budget 0)", sub(r'data-f="sd0">(\d)', bump), True)
    expect("a family variant's figure edited", sub(r'data-fg="1">(\d)', bump), True)
    expect("a family row dropped", sub(r'<details class="fam"[^>]*>.*?(<tr data-fv="\w+">.*?</tr>)', lambda t: "", re.S), True)
    expect("a family's joint edited", sub(r'data-ff="inf">(\d)', bump), True)
    expect("a family's picked-order count edited", sub(r'data-fl="' + BK_SHOWN + r'">(\d)', bump), True)
    expect("a family's line edited", sub(r'data-fline="1"><span data-fl="0" hidden>[^<]*?(\d)', bump), True)
    expect("a with-mirror pair line edited", sub(r'data-pair="1"><span data-fl="0" hidden>[^<]*?(\d)', bump), True)
    expect("a with-mirror pair line deleted", re.sub(r'<div class="sm pairl" data-pair="1">.*?</div>', "", page, count=1, flags=re.S), True)
    expect("a family's with-mirror line edited", sub(r'data-fboth="1"><span data-fl="0" hidden>[^<]*?(\d)', bump), True)
    w = copy.deepcopy(art)
    w["families"]["pairs"][0]["num"]["inf"][1] += 10 ** 12
    expect("an edited pair joint in the artefact", page, True, a=w)
    expect("a family table deleted", re.sub(r'<details class="fam".*?</details>', "", page, count=1, flags=re.S), True)
    expect("a family pointed at another layout", sub(r'data-fam="(\d+)"', lambda h: "999"), True)
    shown = int(re.search(r'data-fam="(\d+)"', page).group(1))
    w = copy.deepcopy(art)
    w["families"]["list"][0]["num"]["inf"][1] += 10 ** 12
    expect("an edited family joint in the artefact", page, True, a=w)
    w = copy.deepcopy(art)
    w["families"]["list"][shown]["num"]["inf"][0] += N2 // 100
    expect("an edited family built count in the artefact", page, True, a=w)
    w = copy.deepcopy(art)
    w["families"]["list"][shown]["pick"]["inf"][0] += 1
    expect("an edited family pick count in the artefact", page, True, a=w)
    w = copy.deepcopy(art)
    w["families"]["list"][0]["variants"].pop()
    w["families"]["list"][0]["pick"]["inf"].pop()
    expect("a family variant dropped from the artefact", page, True, a=w)
    w = copy.deepcopy(art)
    L0 = w["families"]["list"][0]
    L0["variants"][0] = next(b["name"] for b in art["boards"] if b["name"] not in L0["variants"])
    expect("a family variant that is not a hold swap of the layout", page, True, a=w)
    w = copy.deepcopy(art)
    w["families"]["complete"] = False
    expect("families.complete flipped", page, True, a=w)
    expect("a 4th-bag word on the page", page.replace("</body>", "<p>4 巡</p></body>", 1), True)
    m = _CARD.search(page)
    expect("a card dropped", page.replace(m.group(0), "", 1), True)
    expect("a card's rank edited", page.replace(f'data-rk="{m.group(2)}"', 'data-rk="#999"', 1), True)
    expect("the pruning count edited", sub(r'data-pr="kept">(\d)', bump), True)
    expect("the boards total edited", sub(r'data-pr="boards_total">(\d)', bump), True)
    expect("the mirror sentence swapped", page.replace(PR["mirror_assumed" if art["mirror"]["assumed"] else "mirror_counted"],
                                                       PR["mirror_counted" if art["mirror"]["assumed"] else "mirror_assumed"], 1), True)
    expect("a mirror line falsified", re.sub(r'data-same="1"', 'data-same="0"', page, count=1), True)
    expect("a ranking table figure edited", re.sub(r'(<tr data-p3="[^"]+">.*?data-g="inf">)(\d)', lambda mm: mm.group(1) + bump(mm.group(2)), page, count=1, flags=re.S), True)
    expect("an unranked table figure edited", re.sub(r'(<tr data-inc="[^"]+">.*?data-g="inf">)(\d)', lambda mm: mm.group(1) + bump(mm.group(2)), page, count=1, flags=re.S), True)
    rows = _TROW.findall(page)
    expect("two ranking table rows swapped",
           page.replace(f'data-p3="{rows[0][0]}"', 'data-p3="X"', 1).replace(f'data-p3="{rows[1][0]}"', f'data-p3="{rows[0][0]}"', 1)
           .replace('data-p3="X"', f'data-p3="{rows[1][0]}"', 1), True)
    expect("an island figure edited", sub(r'"f":\{"0":\["(\d)', bump), True)
    expect("an island detail row share edited", sub(r'"t":\[\["[A-Za-z.]+","[^"]*","[^"]*","[^"]*","(\d)', bump), True)
    m = OP._ISLAND.search(page)
    isl = json.loads(m.group(1).replace("<\\/", "</"))
    k0 = next(k for k, v in isl["cards"].items() if v["o"]["1"] != v["o"]["0"])
    isl["cards"][k0]["o"]["1"], isl["cards"][k0]["o"]["0"] = isl["cards"][k0]["o"]["0"], isl["cards"][k0]["o"]["1"]
    expect("two budget orders swapped", page[:m.start(1)] + json.dumps(isl, separators=(",", ":"), ensure_ascii=False)
           .replace("</", "<\\/") + page[m.end(1):], True)
    isl = json.loads(m.group(1).replace("<\\/", "</"))
    kr = next(k for k, v in isl["cards"].items() if v["rk"]["0"] == "–")
    isl["cards"][kr]["rk"]["0"] = "#1"
    expect("a rank printed below the threshold", page[:m.start(1)] + json.dumps(isl, separators=(",", ":"), ensure_ascii=False)
           .replace("</", "<\\/") + page[m.end(1):], True)
    m2 = OP._PCX.search(page)
    expect("a worked-PC section dropped", page.replace(m2.group(0), "", 1), True)
    expect("a worked-PC deal letter swapped", sub(r'<figure data-deal="([A-Z]{2})', lambda d: d[::-1] if d[0] != d[1] else "IO"), True)
    expect("a worked-PC cell moved", sub(r'<li data-p="[A-Z]" data-c="(\d+)', lambda c: str((int(c) + 1) % 60)), True)
    expect("a worked-PC hold flag flipped", sub(r'<li data-p="[A-Z]" data-c="[\d,]+" data-h="([01])"', lambda h: "1" if h == "0" else "0"), True)

    worse = copy.deepcopy(art)
    b = next(b for b in worse["boards"] if len(b["classes"]) > 1 and b["name"] == ranked(art, cat)[0][0]["name"])
    b["classes"][0][2] -= 1
    expect("a class's p5 edited in the artefact", render(art, cat, PR, pcxd), True, a=worse)
    worse = copy.deepcopy(art)
    r0 = ranked(art, cat)[0][0]["name"]
    b = next(b for b in worse["boards"] if b["name"] == r0)
    b["cum"]["inf"][-1] += 7
    expect("a cumulative count edited after rendering", page, True, a=worse)
    worse = copy.deepcopy(art)
    b = next(b for b in worse["boards"] if b["name"] == r0)
    b["cum"]["0"][-1] = b["cum"]["inf"][-1] + 1
    expect("a budget count above the unlimited one", rnd(worse), True, a=worse)
    worse = copy.deepcopy(art)
    b = next(b for b in worse["boards"] if b["name"] == r0)
    b["classes"].reverse()
    expect("classes reordered", page, True, a=worse)
    worse = copy.deepcopy(art)
    worse["prune"]["kept"] += 1
    expect("the pruning count edited in the artefact", page, True, a=worse)
    # the builds and worked PCs: rendered from corrupted inputs, so only audit_builds can see it
    k0 = f'{ranked(art, cat)[0][0]["name"]}#{live(ranked(art, cat)[0][0])[0]}'
    bd = copy.deepcopy(builds)
    o = bd[k0]["order"]
    o[-1][1] = [q + 1 for q in o[-1][1]]
    expect("a build piece moved", render(art, cat, PR, pcxd, bd), True, bd=bd)
    bd = copy.deepcopy(builds)
    o = bd[k0]["order"]
    n1 = len(ranked(art, cat)[0][0]["pieces"])
    o[0], o[n1] = o[n1], o[0]
    expect("bag 1 not placed first", render(art, cat, PR, pcxd, bd), True, bd=bd)
    bd = copy.deepcopy(builds)
    bd[k0]["order"][0][2] += 1
    expect("a soft-drop count edited", render(art, cat, PR, pcxd, bd), True, bd=bd)
    bd = copy.deepcopy(builds)
    rests = lambda cs, occ: any(q < 10 or (q - 10 in occ and q - 10 not in cs) for q in cs)
    o, sw = next((v["order"], i) for v in bd.values() for i in range(len(v["order"]) - 1)
                 if not rests(v["order"][i + 1][1], {q for _, cs, _ in v["order"][:i] for q in cs}))
    o[sw], o[sw + 1] = o[sw + 1], o[sw]
    expect("two build steps swapped so one floats", render(art, cat, PR, pcxd, bd), True, bd=bd)
    bd = copy.deepcopy(builds)
    kk, o = next((k, v["order"]) for k, v in bd.items()
                 if any(x for _, _, x in v["order"]) and not all(x for _, _, x in v["order"]))
    a = next(i for i, st in enumerate(o) if st[2])
    z = next(i for i, st in enumerate(o) if not st[2])
    o[a][2], o[z][2] = 0, 1
    expect("a soft drop moved to another step, total unchanged", render(art, cat, PR, pcxd, bd), True, bd=bd)
    hk = next((r for r, _ in ranked(art, cat) if r["kind"] == "held"), None)
    if hk is None:
        print("  skipped: a held build with a T in its first six steps (no ranked held card)")
    else:
        bd = copy.deepcopy(builds)
        kh = f'{hk["name"]}#{live(hk)[0]}'
        bd[kh]["order"][0][0] = "T"
        expect("a held build with a T in its first six steps", render(art, cat, PR, pcxd, bd), True, bd=bd)
    bd = copy.deepcopy(builds)
    del bd[k0]
    expect("a build missing", render(art, cat, PR, pcxd, bd), True, bd=bd)
    px = copy.deepcopy(pcxd)
    shown = {shown_line(cat, r) for r, _ in ranked(art, cat)}
    ln = next(k for k, v in px.items() if v["b3"] and k not in shown)
    pl = px[ln]["b3"]["plan"]
    pl[0][1] = [q + 1 for q in pl[0][1]]
    expect("a class's worked-PC step moved", render(art, cat, PR, px), True, px=px)
    m = OP._ISLAND.search(page)
    isl = json.loads(m.group(1).replace("<\\/", "</"))
    e = next(v for v in isl["px"].values() if v["b3"])
    e["b3"][2][0][0] = (e["b3"][2][0][0] + 1) % 10
    expect("a class's worked-PC drawing moved in the island", page[:m.start(1)] + json.dumps(isl, separators=(",", ":"),
           ensure_ascii=False).replace("</", "<\\/") + page[m.end(1):], True)
    bdj = os.path.join(repo, "analysis", "tst-openers-tp-builds.json")
    try:
        bad_md5 = json.load(open(bdj))
        bad_md5["md5"]["tst_openers_tp"] = "0" * 32
        tmp = os.path.join(tempfile.mkdtemp(), "analysis")
        os.makedirs(tmp)
        json.dump(bad_md5, open(os.path.join(tmp, "tst-openers-tp-builds.json"), "w"))
        for f in ("tst-openers-tp.json",):
            shutil.copy(os.path.join(repo, "analysis", f), tmp)
        load_builds(os.path.dirname(tmp))
        survived += 1
        print("  SURVIVED: a stale builds artefact", file=sys.stderr)
    except Exception:
        killed += 1
        print("  killed: a stale builds artefact")
    for label, edit in (("a build the engine did not confirm reaches the TST", lambda v: v.update(tst=False)),
                        ("a build with no placement order", lambda v: v.update(order=None))):
        try:
            bad_b = json.load(open(bdj))
            edit(next(iter(bad_b["builds"].values())))
            tmp = os.path.join(tempfile.mkdtemp(), "analysis")
            os.makedirs(tmp)
            json.dump(bad_b, open(os.path.join(tmp, "tst-openers-tp-builds.json"), "w"))
            shutil.copy(os.path.join(repo, "analysis", "tst-openers-tp.json"), tmp)
            load_builds(os.path.dirname(tmp))
            survived += 1
            print(f"  SURVIVED: {label}", file=sys.stderr)
        except Exception:
            killed += 1
            print(f"  killed: {label}")
    # the orders artefact and the order lines
    odj = os.path.join(repo, "analysis", "tst-openers-tp-orders.json")
    try:
        bad_o = json.load(open(odj))
        bad_o["md5"]["tst_openers_tp"] = "0" * 32
        tmp = os.path.join(tempfile.mkdtemp(), "analysis")
        os.makedirs(tmp)
        json.dump(bad_o, open(os.path.join(tmp, "tst-openers-tp-orders.json"), "w"))
        shutil.copy(os.path.join(repo, "analysis", "tst-openers-tp.json"), tmp)
        load_orders(os.path.dirname(tmp))
        survived += 1
        print("  SURVIVED: a stale orders artefact", file=sys.stderr)
    except Exception:
        killed += 1
        print("  killed: a stale orders artefact")
    orders = load_orders(repo)
    R = ranked(art, cat)
    good = build_data(art, cat, R, PR, builds, pcxd, orders)
    if audit_orders(good, R, orders):
        survived += 1
        print("  SURVIVED (control fails): the order lines as built", file=sys.stderr)

    def island_mut(label, edit):
        nonlocal killed, survived
        isl = copy.deepcopy(good)
        if edit(isl) is False:
            print(f"  NOT PLANTED: {label}", file=sys.stderr)
            survived += 1
            return
        if audit_orders(isl, R, orders):
            killed += 1
            print(f"  killed: {label}")
        else:
            survived += 1
            print(f"  SURVIVED: {label}", file=sys.stderr)

    def first(pred):
        for nm, c in isl_iter(good):
            for j, d in enumerate(c["d"]):
                if pred(d):
                    return nm, j
        return None

    def isl_iter(isl):
        return [(r["name"], isl["cards"][r["name"]]) for r, _ in R]

    def at(pred, f):
        hit = first(pred)
        if not hit:
            return lambda isl: False
        nm, j = hit
        return lambda isl: f(isl["cards"][nm]["d"][j])
    island_mut("n_inf edited", at(lambda d: True, lambda d: d.__setitem__(1, d[1] - 1)))
    island_mut("n0 edited", at(lambda d: d[0] > 0, lambda d: d.__setitem__(0, d[0] - 1)))
    island_mut("the held kind edited", at(lambda d: True, lambda d: d.__setitem__(2, "I" if d[2] != "I" else "O")))
    island_mut("a plan step's tile moved", lambda isl: next((c["pl"]["s"][0].__setitem__(0, c["pl"]["s"][0][0] + 1)
                                                          for _n, c in isl_iter(isl) if c["pl"]["s"]), False))
    island_mut("a plan's else dropped", lambda isl: next((c["pl"].__setitem__("e", None)
                                                         for _n, c in isl_iter(isl) if c["pl"]["e"]), False))

    def art_mut(label, edit, sec=False):
        nonlocal killed, survived
        od = copy.deepcopy(orders)
        S = od["no180"] if sec else od
        label = label + (" (no 180)" if sec else "")
        for card, pl in S["plans"].items():
            if edit(pl, S, card) is not False:
                break
        else:
            print(f"  NOT PLANTED: {label}", file=sys.stderr)
            survived += 1
            return
        if audit_orders(build_data(art, cat, R, PR, builds, pcxd, od), R, od):
            killed += 1
            print(f"  killed: {label}")
        else:
            survived += 1
            print(f"  SURVIVED: {label}", file=sys.stderr)
    ranked_names = {r["name"] for r, _ in R}

    def w_flip(pl, od, card):
        if card not in ranked_names or not pl["steps"]:
            return False
        v = od["orders"][f'{card}#{pl["steps"][0][0]}']
        w = bytearray(base64.b64decode(v["w"]))
        w[0] ^= 1
        v["w"] = base64.b64encode(bytes(w)).decode()

    def r_pair(pl, od, card):  # a rule's precedence reversed: then it is invalid or its count moves
        if card not in ranked_names or not pl["steps"]:
            return False
        rl = pl["steps"][0][1][0]
        rl[0][0] = rl[0][0][::-1]

    def r_count(pl, od, card):
        if card not in ranked_names or not pl["steps"]:
            return False
        st = pl["steps"][0]
        st[1][0][1] -= 1
        st[2] -= 1

    def r_extra(pl, od, card):  # a precedence added that the rule already implies: not minimal
        if card not in ranked_names:
            return False
        for st in pl["steps"]:
            for rl in st[1]:
                if len(rl[0]) < 3:
                    a, b = rl[0][0]
                    x = next(k for k in "IJLOSTZ" if k not in (a, b))
                    if a + x not in rl[0] and x + b not in rl[0]:
                        rl[0] = rl[0] + [a + x, x + b] if len(rl[0]) == 1 else rl[0] + [a + x]
                        if len(rl[0]) > 3:
                            return False
                        return
        return False

    def s_swap(pl, od, card):
        if card not in ranked_names or len(pl["steps"]) < 2:
            return False
        pl["steps"][0], pl["steps"][1] = pl["steps"][1], pl["steps"][0]

    def s_drop(pl, od, card):  # a step dropped: the else no longer builds everything left
        if card not in ranked_names or not pl["steps"] or not pl["else"]:
            return False
        pl["steps"].pop(0)

    def e_count(pl, od, card):
        if card not in ranked_names or not pl["else"]:
            return False
        pl["else"][1] += 1

    def e_class(pl, od, card):  # the else moved to an earlier live class that does not build all of what is left
        if card not in ranked_names or not pl["else"] or not pl["steps"]:
            return False
        pl["else"][0] = pl["steps"][-1][0]

    def o_count(pl, od, card):
        if card not in ranked_names:
            return False
        pl["open"] += 1

    def z_count(pl, od, card):
        if card not in ranked_names:
            return False
        pl["none"] += 1
    for sec in (False, True):
        art_mut("a w bit flipped", w_flip, sec)
        art_mut("a rule's precedence reversed", r_pair, sec)
        art_mut("a rule's count edited", r_count, sec)
        art_mut("a non-minimal rule", r_extra, sec)
        art_mut("two steps swapped", s_swap, sec)
        art_mut("a step dropped", s_drop, sec)
        art_mut("the else count edited", e_count, sec)
        art_mut("the else moved to a step's class", e_class, sec)
        art_mut("the open count edited", o_count, sec)
        art_mut("the never-built count edited", z_count, sec)

    def no180_gains(pl, od, card):  # the no-180 w gains an order the 180 w lacks
        if card not in ranked_names or not pl["steps"]:
            return False
        k = f'{card}#{pl["steps"][0][0]}'
        w = int.from_bytes(base64.b64decode(orders["orders"][k]["w"]), "little")
        miss = next((i for i in range(BAG) if not w >> i & 1), None)
        if miss is None:
            return False
        v = od["orders"][k]
        w0 = int.from_bytes(base64.b64decode(v["w"]), "little") | 1 << miss
        v["w"] = base64.b64encode(w0.to_bytes(BAG // 8, "little")).decode()
        v["n"] = [x + 1 for x in v["n"]]
    art_mut("an order built without 180 but not with it", no180_gains, True)

    def swap_sec(isl):  # the two sections' lines and plans swapped on a card where they differ
        for _n, c in isl_iter(isl):
            if c["d"] != c["d1"] and c["pl"] != c["pl1"]:
                c["d"], c["d1"], c["pl"], c["pl1"] = c["d1"], c["d"], c["pl1"], c["pl"]
                return
        return False
    island_mut("the 180 and no-180 lines swapped", swap_sec)
    island_mut("a no-180 plan step's tile moved", lambda isl: next((c["pl1"]["s"][0].__setitem__(0, c["pl1"]["s"][0][0] + 1)
                                                                  for _n, c in isl_iter(isl) if c["pl1"]["s"]), False))
    island_mut("a no-180 n_inf edited", lambda isl: next((c["d1"][0].__setitem__(1, c["d1"][0][1] + 1)
                                                         for _n, c in isl_iter(isl) if c["d1"] and c["d1"][0]), False))
    expect("an order line edited in the orders artefact",
           render(art, cat, PR, pcxd, None, L=Lsets, orders={**orders, "orders": {**orders["orders"], next(iter(orders["orders"])):
                                                                  {**next(iter(orders["orders"].values())), "n": [0, 0, 0, 1]}}}),
           True)
    print(f"selftest: {killed} killed, {survived} survived")
    return 1 if survived else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    d = a.out_dir or os.path.join(REPO, "docs")
    os.makedirs(d, exist_ok=True)
    for name, page in render_all().items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"wrote {os.path.join(d, name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
