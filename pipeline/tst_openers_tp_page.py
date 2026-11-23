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
import copy
import hashlib
import html
import json
import os
import re
import shutil
import sys
import tempfile
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
DATA_ID = OP.DATA_ID
BAG, N2, WALL = OP.BAG, OP.N2, OP.WALL
pct, _esc, _need = OP.pct, OP._esc, OP._need
BK = ["0", "1", "2", "inf"]          # the soft-drop budgets of the artefact, in its order
BK_SHOWN = "inf"                     # the budget the page opens on
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
    _need(art["schema"] == "tst-openers-tp/4" and art["report_eligible"] is False and art["constructed"] is True
          and "families" in art,
          "the artefact is not tst-openers-tp/4 (with families) marked report_eligible: false / constructed: true")
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
    return art, cat


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
    d = deltas(b, BK_SHOWN)
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
    return (-routed(cat, b), sum(1 for s in b["shapes"] if s >= ID_OFFSET), -figs(b, BK_SHOWN)[2], b["name"])


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
    return sorted(seen.values(), key=lambda i: (-lst[i]["num"][BK_SHOWN][1], i))


def fam_block(r, m, fam, rkmap, cat, art, PR):
    """The card's best family: each variant's own joint per budget, its rank and the orders the policy gives it, then the
    family's own line (a lower bound: variants the pruning dropped are missing)."""
    C = PR["card"]
    by_name, rep_of = fam
    idx = card_layouts(r, m, art, by_name)
    if not idx:
        return ""
    lst = art["families"]["list"]
    L = lst[idx[0]]
    byn = {b["name"]: b for b in art["boards"]}
    sfx = art["mirror"]["suffix"]
    head = "".join(f"<th>{_esc(h)}</th>" for h in C["fam_cols"])

    def spans(vals):
        return "".join(f'<span data-fl="{k}"{"" if k == BK_SHOWN else " hidden"}>{v}</span>' for k, v in zip(BK, vals))
    rows = []
    for j, vn in enumerate(L["variants"]):
        v = byn[vn]
        rep = rep_of[vn]
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
                + '<td class="num">–</td>'
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
    rows = [(r, p) for r, p in pairs(art, cat) if figs(r, BK_SHOWN)[2] > th]
    rows.sort(key=lambda x: (-figs(x[0], BK_SHOWN)[2], x[0]["name"]))
    return rows


def unranked(art, cat):
    th = threshold(art)
    return [(r, p) for r, p in pairs(art, cat) if figs(r, BK_SHOWN)[2] <= th]


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


CL_KEYS = ("pcx_b3", "pcx_left", "pcx_deal3", "pcx_hold", "pcx_none3",
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


def build_data(art, cat, R, PR, builds, pcxd):
    rk, od = rank_data(art, R)
    cards, px = {}, {}
    for n, (r, _p) in enumerate(R):
        s = cat[r["shapes"][r["classes"][shown_class(r)][0]]]
        lv = live(r)
        bb, xx = [], []
        for i in lv:
            si, left, p5 = r["classes"][i]
            b = builds.get(f'{r["name"]}#{i}')
            bb.append([[[k, list(c), sd] for k, c, sd in b["order"]], b["sd"]] if b else None)
            ln = class_line(cat, r, i)
            xx.append([tst_cells(cat[r["shapes"][si]]), ln, int(p5 >= BAG)])
            if ln not in px:
                px[ln] = px_entry(cat[r["shapes"][si]]["rows"], left, pcxd.get(ln))
        cards[r["name"]] = dict(tst=s["tst"], f=strings(r), rk={k: rk[k][n] for k in BK}, o={k: od[k][n] for k in BK},
                                t=card_rows(cat, r), n1=len(r["pieces"]), b=bb, x=xx, kind=r["kind"],
                                cnt={k: counts_line(r, k, PR["card"]) for k in BK})
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


def card(rkt, r, m, cat, art, PR, pcxd, famh=""):
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
    stats = (f'<span>{C["two"]} <b class="num" data-f="two">{fs[0]}</b></span>'
             f'<span>{C["pc3"]} <b class="num" data-f="pc3">{_esc(fs[1])}</b></span>'
             f'<span class="j">{C["joint"]} <b class="num" data-f="joint">{fs[2]}</b></span>')
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
def title_parts(cat, b, sfx):
    """(route openers' Japanese names in ROUTE order, other names, has yachi's own shape) over ALL the board's shapes; a
    mirror shape's name loses the mirror suffix so it counts as its original."""
    routes, others, me = [], [], False
    for sid in b["shapes"]:
        for n in cat[sid]["names"]:
            n = n[:-len(sfx)] if sfx and n.endswith(sfx) else n
            if n.strip() == "yachi":
                me = True
                continue
            k = route_of(n)
            if k:
                if k not in routes:
                    routes.append(k)
            elif n not in others:
                others.append(n)
    routes.sort(key=list(ROUTE).index)
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


def render(art, cat, PR, pcxd, builds=None):
    builds = builds if builds is not None else load_builds()
    R, U = ranked(art, cat), unranked(art, cat)
    fm = fmt_for(art, cat, R, U)
    fm["mirror_state"] = PR["mirror_assumed" if art["mirror"]["assumed"] else "mirror_counted"]
    rk0 = rank_data(art, R)[0][BK_SHOWN]
    fam = families(art, cat)
    rkmap = {r["name"]: rk0[n] for n, (r, _) in enumerate(R)}
    cards = "\n".join(card(rk0[n], r, m, cat, art, PR, pcxd, fam_block(r, m, fam, rkmap, cat, art, PR))
                       for n, (r, m) in enumerate(R))
    title = PR["title"] + RS.TITLE_MARK
    data = json.dumps(build_data(art, cat, R, PR, builds, pcxd), separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    with open(OP.CSS_PATH, encoding="utf-8") as f:
        css = f.read().strip("\n")
    with open(CSS_PATH, encoding="utf-8") as f:
        css += "\n" + f.read().strip("\n")
    with open(JS_PATH, encoding="utf-8") as f:
        js = f.read().strip("\n")
    sdb = "".join(f'<button aria-pressed="{"true" if k == BK_SHOWN else "false"}" data-b="{k}">{_esc(PR["card"]["bk_" + k])}</button>'
                  for k in ("inf", "2", "1", "0"))
    out = ['<!doctype html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
           "<style>", css, "</style></head><body><main>",
           f'<nav class="sm"><a href="index.html">{_esc(PR["back"])}</a></nav>',
           f'<div class="eyebrow">{RS.EYEBROW}</div>', f"<h1>{_esc(title)}</h1>",
           f'<p class="quar">{PR["quarantine"]}</p>',
           f'<p class="ref">{PR["held_note"]} <a href="{HELD_PAGE}">{PR["to_held"]}</a></p>']
    out += [f"<p>{t.format(**fm)}</p>" for t in PR["intro"]]
    out += [f'<details class="sm"><summary><b>{_esc(PR["reading_summary"])}</b></summary>\n<ul>']
    out += [f"<li>{t.format(**fm)}</li>" for t in PR["reading"]]
    out += ["</ul></details>",
            f'<div class="bar" data-bar="pos"><button aria-pressed="true" data-f="{PR["pos_centre"]}">{_esc(PR["filter_centre"].format(**fm))}</button>'
            f'<button aria-pressed="false" data-f="all">{_esc(PR["filter_all"])}</button></div>',
            kind_bar(R, PR),
            f'<div class="bar" data-bar="sd"><span class="muted sm">{_esc(PR["sd_bar"])}</span>{sdb}</div>',
            f'<p class="muted sm">{_esc(PR["filter_note"].format(**fm))}</p>',
            *top_table(art, cat, R, PR),
            f'<h2>{_esc(PR["h2_cards"].format(**fm))}</h2>', '<div class="grid" id="g">', cards, "</div>",
            *inc_table(art, cat, U, PR)]
    out += ["</main>", f'<script id="{DATA_ID}" type="application/json">{data}</script>', "<script>", js, "</script></body></html>"]
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
    if F.get("complete") is not False:
        bad.append("families.complete is not false: the pruned variants are missing, so the figures are lower bounds")
    byn = {b["name"]: b for b in art["boards"]}
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
            if bn > pn // 1 * 0 + N2 or (bn == 0) != (pn == 0):
                bad.append(f"{tag}: built / PC counts at budget {k} disagree")
        for a, b2 in zip(BK, BK[1:]):
            if L["num"][a][1] > L["num"][b2][1]:
                bad.append(f"{tag}: the family PC counts are not monotone from budget {a} to {b2}")


def audit(page, art, cat, PR, pcxd=None, builds=None):
    builds = builds if builds is not None else load_builds()
    pcxd = pcxd if pcxd is not None else load_pcx()
    bad = RP.audit_quarantine(page, [RS.EYEBROW, RS.NO_CLAIM, PR["quarantine"]], DATA_ID)
    if PR["held_note"] not in page or f'<a href="{HELD_PAGE}">' not in page:
        bad.append("the note or the link to the reference page is missing")
    if set(page) & SIMPLIFIED:
        bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
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
            L = art["families"]["list"][idx[0]]
            fbody = fb.group(2)
            rows = re.findall(r'<tr data-fv="(\w+)">(.*?)</tr>', fbody, re.S)
            if [x for x, _ in rows] != L["variants"]:
                bad.append(f"card {name}: the family rows {[x for x, _ in rows]} are not the layout's {L['variants']}")
            byn = {b["name"]: b for b in art["boards"]}
            for j, (vn, rb) in enumerate(rows):
                v = byn.get(vn)
                got = dict(re.findall(r'data-fg="(\w+)">(.*?)</td>', rb))
                if v is None or got != {k: ex_strings(v)[k][2] for k in BK}:
                    bad.append(f"card {name}: family variant {vn}'s figures are not its recomputed joints")
                pk = dict(re.findall(r'data-fl="(\w+)"[^>]*>(\d+)</span>', rb))
                if pk != {k: str(L["pick"][k][j]) for k in BK}:
                    bad.append(f"card {name}: family variant {vn}'s picked orders are not the artefact's")
            ff = re.search(r'<tr data-ffam="1">(.*?)</tr>', fbody, re.S)
            if not ff:
                bad.append(f"card {name}: the family row is missing")
            else:
                got = dict(re.findall(r'data-ff="(\w+)">(.*?)</td>', ff.group(1)))
                if got != {k: fam_strings(L, k)[2] for k in BK}:
                    bad.append(f"card {name}: the family joints are not the recomputed ones")
                tot = dict(re.findall(r'data-fl="(\w+)"[^>]*>(\d+)</span>', ff.group(1)))
                if tot != {k: str(sum(L["pick"][k])) for k in BK}:
                    bad.append(f"card {name}: the family's built-order totals are not the picks' sum")
            lm = re.search(r'data-fline="1">(.*?)</p>', fbody, re.S)
            want = {k: PR["card"]["fam_line"].format(a=fam_strings(L, k)[0], b=fam_strings(L, k)[1], c=fam_strings(L, k)[2]) for k in BK}
            got = {k: html.unescape(v) for k, v in re.findall(r'data-fl="(\w+)"[^>]*>(.*?)</span>', lm.group(1))} if lm else {}
            if got != want:
                bad.append(f"card {name}: the family line is not the recomputed one")
            bm = re.search(r'data-fboth="1">(.*?)</p>', fbody, re.S)
            wb = {k: PR["card"]["fam_both"].format(a=fam_strings(L["both"], k)[0], b=fam_strings(L["both"], k)[1],
                                                    c=fam_strings(L["both"], k)[2]) for k in BK}
            gb = {k: html.unescape(v) for k, v in re.findall(r'data-fl="(\w+)"[^>]*>(.*?)</span>', bm.group(1))} if bm else {}
            if gb != wb:
                bad.append(f"card {name}: the family's with-mirror line is not the recomputed one")
            mir = {byn[x]["mirror"] for x in L["variants"]}
            if set(L["both"]["variants"]) != set(L["variants"]) | mir:
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
        if island != build_data(art, cat, R, PR, builds, pcxd):
            bad.append("the data island is not what the artefact builds")
        if island:
            bad += audit_builds(island, R, cat, pcxd)
        if island == build_data(art, cat, R, PR, builds, pcxd):
            for n, (r, _) in enumerate(R):
                c = island["cards"][r["name"]]
                if c["cnt"] != {k: ex_counts(r, k, PR["card"]) for k in BK}:
                    bad.append(f"island card {r['name']}: the counts lines are not the recomputed ones")
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


# ------------------------------------------------------------------ driver

def render_all(repo=REPO, inputs=None, prose=None):
    art, cat = inputs or load_inputs(repo)
    PR = prose or load_prose()
    pcxd = load_pcx(repo)
    page = render(art, cat, PR, pcxd)
    bad = audit(page, art, cat, PR, pcxd)
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
    page = render(art, cat, PR, pcxd)
    killed = survived = 0

    builds = load_builds(repo)

    def expect(label, mutated, want, a=None, c=None, bd=None, px=None):
        nonlocal killed, survived
        bad = audit(mutated, a or art, c or cat, PR, px or pcxd, bd or builds)
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
    expect("the reference note deleted", page.replace(PR["held_note"], "", 1), True)
    expect("the link to the reference page deleted", page.replace(f'<a href="{HELD_PAGE}">', "<a>", 1), True)
    expect("a claim badge planted", page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), True)
    expect("a simplified glyph", page.replace("</h1>", "<p>实</p></h1>", 1), True)
    expect("an external request planted", page.replace("<style>", '<link rel="stylesheet" href="https://x.example/a.css"><style>', 1), True)
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
    expect("a wrong bag-1 name in the artefact", render(worse, cat, PR, pcxd), True)
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
    expect("a family's picked-order count edited", sub(r'data-fl="inf">(\d)', bump), True)
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
    w["families"]["complete"] = True
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
    expect("a budget count above the unlimited one", render(worse, cat, PR, pcxd), True, a=worse)
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
