"""TST 開局排名 — the two-bag TST shapes ranked by how likely a random deal builds them and then clears a
Perfect Clear: `docs/tst-openers.html`.

    python3 -m pipeline.tst_openers_page --out-dir /tmp/tst   # render it somewhere other than docs/
    python3 -m pipeline.tst_openers_page --selftest           # the audit's mutants

Inputs, both committed and nothing else: `analysis/tst-openers.json` (the merged enumeration: per shape its
tilings with their counts, and the sampled bag-4 lines) and `pipeline/openers/tst-openers-shapes.json` (the
shapes: source names, cells, the T's slot, and the `sources` block). The artefact is CONSTRUCTED and
quarantined: nobody played these boards, no claim id, no badge. The audit reuses
`replay_page.audit_quarantine` and adds:

* every ranked shape has exactly one card, in rank order, and every card's four figures are RECOMPUTED from the
  artefact (a second, independent computation, exact fractions). The headline figures are the FIXED-bag-1 ones
  (the artefact's `fixed` block: bag 1 laid one way, bag 2 random, PC over the tilings holding that bag 1); the
  audit re-picks the best bag-1 board from its `cums` by rate x PC and checks the drawn tiling holds it. The
  see-both-bags figure (best single tiling) is printed beside it and re-derived too. It is NOT a strict upper
  bound: a fixed bag 1 may finish on any of several tilings holding it, so the page counts the shapes where the
  fixed rate exceeds it instead of calling it one;
* the inlined data island equals what the renderer builds from the artefact;
* `未計` where the two-bag count is zero (never a `0%` PC), `≈` on every sampled bag-4 figure;
* no simplified glyph, no external request, no markup sink.

ROUNDING: every percentage is FLOORED, never rounded (the repo's 約 convention, `fmt.py`): a figure supporting
a ranking must not read higher than the exact value. Computation is exact (`fractions.Fraction`), so a floor is
never an artefact of float noise; the JS only draws strings this module has already floored.
"""
import argparse
import copy
import html
import json
import math
import os
import re
import sys
from fractions import Fraction

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline.claims.build_claims import SIMPLIFIED

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OVERVIEW = "tst-openers.html"
PREFIX = "tst-openers"
ART_PATH = os.path.join(REPO, "analysis", "tst-openers.json")
SHAPES_PATH = os.path.join(REPO, "pipeline", "openers", "tst-openers-shapes.json")
PCX_PATH = os.path.join(REPO, "analysis", "tst-openers-pc-examples.json")
PROSE_PATH = os.path.join(HERE, "tst_openers_prose.json")
CSS_PATH = os.path.join(HERE, "tst_openers_page.css")
JS_PATH = os.path.join(HERE, "tst_openers_page.js")
DATA_ID = "data"

BAG = math.factorial(7)           # deals of one bag; two bags give BAG ** 2 orders
N2 = BAG * BAG
LEFT_NOTE_MIN = 3                 # a leftover of this many pieces or more makes the PC count approximate
WALL = 2                          # a TST this close to a side wall (cells) counts as 近牆
HID_SHOWN = 6                     # how many hidden wall ranks the filter note names
PC3_SHOWN = 15                    # rows of the 「兩巡易砌又 3 巡 PC 高」 table
COL = dict(I="#2fb8c9", O="#e3b425", T="#9a46d6", S="#4cb648", Z="#d9433d", J="#3b61d6", L="#e5792a")

# the seven tetrominoes as sets of (x, y) offsets, every rotation, normalised to min x = min y = 0
_BASE = dict(I=[(0, 0), (1, 0), (2, 0), (3, 0)], O=[(0, 0), (1, 0), (0, 1), (1, 1)], T=[(0, 0), (1, 0), (2, 0), (1, 1)],
             S=[(0, 0), (1, 0), (1, 1), (2, 1)], Z=[(1, 0), (2, 0), (0, 1), (1, 1)], J=[(0, 0), (1, 0), (2, 0), (0, 1)],
             L=[(0, 0), (1, 0), (2, 0), (2, 1)])


def _norm(cs):
    mx, my = min(x for x, y in cs), min(y for x, y in cs)
    return frozenset((x - mx, y - my) for x, y in cs)


def _rots(cs):
    out, cur = set(), list(cs)
    for _ in range(4):
        out.add(_norm(cur))
        cur = [(y, -x) for x, y in cur]
    return out


SHAPE = {k: _rots(v) for k, v in _BASE.items()}
_PCX = re.compile(r'<details class="pcx" data-line="([^"]*)">(.*?)</details>', re.S)
_PCX_FIG = re.compile(r'<figure data-deal="([A-Z]*)" data-h="(\d+)">(.*?)</figure>', re.S)
_PCX_STEP = re.compile(r'<li data-p="([A-Z])" data-c="([\d,]+)" data-h="([01])">')
_CARD = re.compile(r'<article class="card[^"]*" data-pos="[^"]*" data-card="(\d+)" data-rk="([^"]*)"[^>]*>(.*?)</article>', re.S)
_P3ROW = re.compile(r'<tr data-p3="(\d+)">(.*?)</tr>', re.S)
_P3FIG = re.compile(r'data-g="(\w+)">(.*?)</td>', re.S)
_FIG = re.compile(r'data-f="(\w+)">(.*?)</b>', re.S)
_ISLAND = re.compile(r'<script id="data" type="application/json">(.*?)</script>', re.S)


def _need(cond, msg):
    if not cond:
        raise ValueError(f"tst openers page: {msg}")


def _esc(s):
    return html.escape(str(s), quote=True)


# ------------------------------------------------------------------ figures

def pct(v):
    """A percentage of the exact fraction `v`, FLOORED (see the module note): one decimal from 0.1%, two
    below it, `0%` for exactly zero and `<0.01%` for a positive value that floors to nothing."""
    v = Fraction(v)
    if v == 0:
        return "0%"
    if v >= Fraction(1, 1000):
        n = math.floor(v * 1000)
        return f"{n // 10}.{n % 10}%"
    n = math.floor(v * 10000)
    return "<0.01%" if n == 0 else f"0.{n:02d}%"


def load_inputs(repo=REPO):
    with open(os.path.join(repo, "analysis", "tst-openers.json"), encoding="utf-8") as f:
        art = json.load(f)
    with open(os.path.join(repo, "pipeline", "openers", "tst-openers-shapes.json"), encoding="utf-8") as f:
        shp = json.load(f)
    _need(art.get("report_eligible") is False and art.get("constructed") is True,
          "the artefact is not marked report_eligible: false / constructed: true")
    _need([s["id"] for s in art["shapes"]] == list(range(len(art["shapes"]))), "artefact shape ids are not the index")
    by = {s["id"]: s for s in shp["shapes"]}
    _need(set(by) == {s["id"] for s in art["shapes"]}, "the shapes file and the artefact name different shapes")
    return art, shp


def load_pcx(repo=REPO, art_bytes=None):
    """The worked-PC examples (`pipeline/sim/emit-tst-pc-examples.py`), keyed by `rows|left` line. Refuses an
    artefact built from another `tst-openers.json` than the one on disk."""
    import hashlib
    with open(os.path.join(repo, "analysis", "tst-openers-pc-examples.json"), encoding="utf-8") as f:
        ex = json.load(f)
    _need(ex.get("report_eligible") is False and ex.get("constructed") is True,
          "the PC examples artefact is not marked report_eligible: false / constructed: true")
    if art_bytes is None:
        with open(os.path.join(repo, "analysis", "tst-openers.json"), "rb") as f:
            art_bytes = f.read()
    _need(ex["md5"]["tst_openers"] == hashlib.md5(art_bytes).hexdigest(),
          "the PC examples artefact was built from another analysis/tst-openers.json: re-run emit-tst-pc-examples.py")
    return {e["line"]: e for e in ex["examples"]}


def load_prose(path=PROSE_PATH):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    _need(not (set(text) & SIMPLIFIED), f"the prose carries simplified glyph(s) {sorted(set(text) & SIMPLIFIED)}")
    return json.loads(text)


def p4_index(art):
    """'rows|left' -> its sampled record; a record with no draws is no record (gen.py's `not r['n']`)."""
    return {r["line"]: r for r in art["pc4"] if r["n"]}


def line_of(o, t):
    return ",".join(map(str, o["rows"])) + "|" + t["left"]


def tiling_p4(o, t, idx):
    """(P(PC by bag 4) as an exact fraction or None, draws behind it, 0 when exact)."""
    if t["p5"] >= BAG:
        return Fraction(1), 0
    r = idx.get(line_of(o, t))
    if not r:
        return None, 0
    return Fraction(t["p5"] * r["n"] + (BAG - t["p5"]) * r["ok"], BAG * r["n"]), r["n"]


def score(t, p4):
    """What a tiling is ranked by: its two-bag count times its bag-4 PC chance (the bag-3 chance when none)."""
    return t["B"] * (p4 if p4 is not None else Fraction(t["p5"], BAG))


def fig_strings(t, p4, n4):
    """The four printed figures of one tiling: (two-bag, bag-3 PC, bag-4 PC, joint) as display strings."""
    two = pct(Fraction(t["B"], N2))
    if t["B"] == 0:
        pc3 = pc4 = "未計"
    else:
        pc3 = pct(Fraction(t["p5"], BAG))
        pc4 = "–" if p4 is None else (("≈" + pct(p4)) if n4 else pct(p4))
    return two, pc3, pc4, pct(score(t, p4) / N2)


def class_figs(o, idx):
    """leftover -> (PC Fraction used for ranking, p5, p4 or None, draws behind p4) over the two-bag tilings; a
    leftover's PC does not depend on the tiling (the residue rows are the shape's), which is asserted."""
    out = {}
    for t in o["til"]:
        if t["B"] == 0:
            continue
        p4, n4 = tiling_p4(o, t, idx)
        v = (p4 if p4 is not None else Fraction(t["p5"], BAG), t["p5"], p4, n4)
        _need(out.setdefault(t["left"], v) == v, f"shape {o['id']}: leftover {t['left']!r} has two PC figures")
    return out


def fixed_figs(o, idx):
    """The fixed-bag-1 figures of shape `o` (None when it has no `fixed` block): the bag-1 board is the one the
    artefact picked, bag 2 is random, the player then ends on the best leftover class the deal allows.
    Returns dict(cum, rate, pc3n, pc3d, pc3, pc4, n4, joint, same) with exact fractions; `pc4` is None when a
    contributing class has no bag-4 record (the joint then uses its bag-3 figure, a lower bound)."""
    f = o.get("fixed")
    if not f:
        return None
    if not f["nb1"]:
        return dict(cum=0, rate=Fraction(0), pc3n=0, pc3d=0, pc3=None, pc4=None, n4=0, joint=Fraction(0), same=True)
    cf = class_figs(o, idx)
    cum = f["cums"][f["best"]]
    joint = Fraction(0)
    pc3n = 0
    n4 = 0
    missing = False
    prev = 0
    used = set()
    for k, c in enumerate(f["classes"]):
        d = cum[k] - prev
        prev = cum[k]
        if not d:
            continue
        pc, p5, p4, nn = cf[c]
        used.add(pc)
        joint += d * pc
        pc3n += d * p5
        n4 = max(n4, nn)
        missing |= p4 is None
    tot = cum[-1]
    if not tot:
        return dict(cum=0, rate=Fraction(0), pc3n=0, pc3d=0, pc3=None, pc4=None, n4=0, joint=Fraction(0), same=True)
    return dict(cum=tot, rate=Fraction(tot, N2), pc3n=pc3n, pc3d=tot * BAG, pc3=Fraction(pc3n, tot * BAG),
                pc4=None if missing else joint / tot, n4=n4, joint=joint / N2, same=len(set(v[0] for v in cf.values())) == 1)


def fixed_strings(fx):
    """(rate, bag-3 PC, bag-4 PC, joint) display strings of `fixed_figs`; 未計 where the fixed rate is zero."""
    if fx["cum"] == 0:
        return pct(0), "未計", "未計", pct(0)
    pc4 = "–" if fx["pc4"] is None else (("≈" if fx["n4"] else "") + pct(fx["pc4"]))
    return pct(fx["rate"]), pct(fx["pc3"]), pc4, pct(fx["joint"])


def shown_tiling(e):
    """The tiling a card draws: the fixed run's (the best tiling holding the fixed bag-1 board), else the best."""
    f = e["o"].get("fixed")
    return e["o"]["til"][f["til"]] if f and f["nb1"] and e["fx"]["cum"] else e["best"]


def grid(t):
    g = {}
    for k, cs in t["pieces"]:
        for c in cs:
            g[c] = k
    H = max(c // 10 for c in g) + 1
    return "".join("".join(g.get(y * 10 + x, ".") for x in range(10)) for y in range(H - 1, -1, -1))


def mirror_key(s):
    occ = frozenset(map(tuple, s["cells"]))
    t = frozenset(map(tuple, s["tst"]))
    m = lambda S: frozenset((9 - x, y) for x, y in S)
    a = (tuple(sorted(occ)), tuple(sorted(t)))
    b = (tuple(sorted(m(occ))), tuple(sorted(m(t))))
    return min(a, b)


def entries(art, shp):
    """The ranked list: one entry per shape up to left-right mirroring, sorted by `rank_key` (the fixed-bag-1
    joint first); `best` is the best single tiling (the see-both-bags figure); a shape with no tiling is not ranked."""
    shapes = {s["id"]: s for s in shp["shapes"]}
    idx = p4_index(art)
    rows = {}
    for o in art["shapes"]:
        if not o["til"]:
            continue
        s = shapes[o["id"]]
        scored = [(t, *tiling_p4(o, t, idx)) for t in o["til"]]
        best = max(scored, key=lambda x: (score(x[0], x[1]), x[0]["B"]))
        t, p4, n4 = best
        fx = fixed_figs(o, idx)
        e = dict(s=s, o=o, best=t, p4=p4, n4=n4, joint=score(t, p4) / N2, two=Fraction(t["B"], N2), scored=scored, fx=fx,
                 fjoint=fx["joint"] if fx else Fraction(0))
        k = mirror_key(s)
        if k in rows:
            p = rows[k]
            names = sorted(set(p["names"]) | set(s["names"]))
            p["names"] = names
            p["mirror"] = True
            if rank_key(e) < rank_key(p):
                e["names"], e["mirror"] = names, True
                rows[k] = e
        else:
            e["names"], e["mirror"] = list(s["names"]), False
            rows[k] = e
    return sorted(rows.values(), key=rank_key)


def pc3_rank(F):
    """The 「兩巡易砌又 3 巡 PC 高」 table: full shapes with a fixed figure, ranked by the probability that the
    fixed bag 1 builds the shape AND bag 3 clears (fixed rate × bag-3 PC = pc3n / (N2·BAG)), then by the main
    rank; each row is (main rank, entry, that joint). The figures are the drawn board's (`fixed_figs`)."""
    rows = [(i + 1, e, Fraction(e["fx"]["pc3n"], N2 * BAG)) for i, e in enumerate(F) if e["fx"] and e["fx"]["cum"]]
    rows.sort(key=lambda r: (-r[2], r[0]))
    return rows[:PC3_SHOWN]


def pc3_cells(rk, e, j3):
    """The display strings of one pc3 table row: main rank, fixed rate, bag-3 PC, joint."""
    return [f"#{rk}", pct(e["fx"]["rate"]), pct(e["fx"]["pc3"]), pct(j3)]


def pc3_table(F, PR, full):
    T = PR["pc3_table"]
    head = "".join(f"<th>{_esc(h)}</th>" for h in T["cols"])
    body = []
    for n, (rk, e, j3) in enumerate(pc3_rank(F), 1):
        mk, r, p3, j = pc3_cells(rk, e, j3)
        names = ", ".join(_esc(x) for x in e["names"][:2]) + (PR["names_more"].format(c=len(e["names"])) if len(e["names"]) > 2 else "")
        body.append(f'<tr data-p3="{e["s"]["id"]}"><td class="num">{n}</td><td><a href="#c{e["s"]["id"]}">{names}</a></td>'
                    f'<td class="num" data-g="rate">{r}</td><td class="num" data-g="pc3">{p3}</td>'
                    f'<td class="num j3" data-g="j3">{j}</td><td class="num" data-g="main">{mk}</td></tr>')
    return [f'<h2>{_esc(T["h2"])}</h2>', f'<p class="muted">{T["note"].format(shown=PC3_SHOWN, full=full)}</p>',
            f'<div class="p3w"><table class="p3"><thead><tr>{head}</tr></thead><tbody>', *body, "</tbody></table></div>"]


def audit_pc3(page, F):
    bad = []
    got = [(int(sid), {k: re.sub(r"<[^>]+>", "", v) for k, v in _P3FIG.findall(b)}) for sid, b in _P3ROW.findall(page)]
    want = pc3_rank(F)
    if [g[0] for g in got] != [e["s"]["id"] for _, e, _ in want]:
        bad.append("the 3巡 PC table is not the recomputed ranking")
        return bad
    for (sid, figs), (rk, e, j3) in zip(got, want):
        if [figs.get(k) for k in ("main", "rate", "pc3", "j3")] != pc3_cells(rk, e, j3):
            bad.append(f"3巡 PC table row for shape {sid}: figures are not the recomputed ones")
    return bad


def rank_key(e):
    """Rank by the fixed-bag-1 joint figure, then the see-both-bags joint, then the two-bag count."""
    return (-e["fjoint"], -e["joint"], -e["two"])


def dist(s):
    xs = [x for x, y in s["tst"]]
    return min(min(xs), 9 - max(xs))


def is_me(e):
    return any(x.strip() == "yachi" for x in e["names"])


def structure(ents):
    """full cells, the full list, the partial groups (ordered: the group holding the player first, then by size)."""
    full = max(len(e["s"]["cells"]) for e in ents)
    F = [e for e in ents if len(e["s"]["cells"]) == full]
    P = [e for e in ents if len(e["s"]["cells"]) < full]
    groups = {}
    for e in P:
        groups.setdefault(len(e["s"]["cells"]), []).append(e)
    order = sorted(groups, key=lambda n: (not any(is_me(e) for e in groups[n]), -n))
    me_cells = next((n for n in order if any(is_me(e) for e in groups[n])), 0)
    me = next((i + 1 for i, e in enumerate(groups.get(me_cells, [])) if is_me(e)), 0)
    return full, F, P, groups, order, me_cells, me


def build_data(ents, prose):
    """The island: per shape the player-facing rows (grid, four figure strings, leftover), best first."""
    shapes = {}
    for e in ents:
        rows = sorted(e["scored"], key=lambda x: -score(x[0], x[1]))
        shapes[f"s{e['s']['id']}"] = dict(
            tst=e["s"]["tst"],
            t=[[grid(t), *fig_strings(t, p4, n4), t["left"]] for t, p4, n4 in rows])
    return dict(labels=prose["labels"], filter_default=prose["pos_centre"], shapes=shapes)


# ------------------------------------------------------------------ drawing

def svg(cells, H, cs=14, tst=()):
    W = 10
    r = [f'<svg class="board" width="{W * cs}" height="{H * cs}" viewBox="0 0 {W * cs} {H * cs}" role="img">',
         f'<rect width="{W * cs}" height="{H * cs}" fill="var(--well)"/>']
    for x in range(W):
        for y in range(H):
            r.append(f'<rect x="{x * cs + .5}" y="{(H - 1 - y) * cs + .5}" width="{cs - 1}" height="{cs - 1}" fill="var(--grid)"/>')
    for (x, y), k in cells.items():
        r.append(f'<rect x="{x * cs + .5}" y="{(H - 1 - y) * cs + .5}" width="{cs - 1}" height="{cs - 1}" fill="{COL.get(k, "#8a8f9c")}"/>')
    for (x, y) in tst:
        r.append(f'<rect x="{x * cs + 2}" y="{(H - 1 - y) * cs + 2}" width="{cs - 4}" height="{cs - 4}" fill="none" '
                 f'stroke="#c77dff" stroke-width="2" stroke-dasharray="3 2"/>')
    r.append("</svg>")
    return "".join(r)


def start(left, deal):
    """pc4's start state (tst-pcex-rs `start`): (current, hold, queue). '' is an empty hold."""
    left = list(left)
    if not left:
        return deal[0], "", list(deal[1:])
    if len(left) == 1:
        return left[0], "", list(deal)
    return left[0], left[1], left[2:] + list(deal)


def replay(rows, left, deal, h, plan):
    """Replay one solver plan from scratch. Returns ({(x, y) in the ORIGINAL frame: (piece, step)}, problems).
    Checks: the piece order follows the queue and hold rule of `start`, each placement is four empty cells of
    that piece's shape on the board as it stands, full rows clear, and the board ends empty."""
    bad = []
    cur, hold, q = start(left, deal)
    qi = 0
    board = [r for r in rows] + [0] * max(0, h - len(rows))
    if len(rows) > h:
        bad.append(f"the residue is {len(rows)} rows, taller than the plan's {h}")
    ids = list(range(len(board)))
    out = {}
    for n, (p, cells, held) in enumerate(plan, 1):
        nq = q[qi] if qi < len(q) else ""
        if not held:
            want, cur, qi = cur, nq, qi + 1
        elif not hold:
            want, hold, cur, qi = nq, cur, (q[qi + 1] if qi + 1 < len(q) else ""), qi + 2
        else:
            want, hold, cur, qi = hold, cur, nq, qi + 1
        if p != want:
            bad.append(f"step {n}: placed {p}, the queue and hold give {want or 'nothing'}")
        xy = [(c % 10, c // 10) for c in cells]
        if any(y >= len(board) for x, y in xy) or len(set(xy)) != 4:
            bad.append(f"step {n}: cells {cells} are outside the board or repeat")
            return out, bad
        if _norm(xy) not in SHAPE.get(p, ()):
            bad.append(f"step {n}: cells {cells} are not a {p}")
        for x, y in xy:
            if board[y] >> x & 1:
                bad.append(f"step {n}: cell ({x},{y}) is already filled")
            board[y] |= 1 << x
            out[(x, ids[y])] = (p, n)
        keep = [i for i, r in enumerate(board) if r != 1023]
        board, ids = [board[i] for i in keep], [ids[i] for i in keep]
    if any(board):
        bad.append("the board is not empty at the end")
    return out, bad


def pcx_svg(rows, h, placed, cs=16):
    W = 10
    r = [f'<svg class="board" width="{W * cs}" height="{h * cs}" viewBox="0 0 {W * cs} {h * cs}" role="img">',
         f'<rect width="{W * cs}" height="{h * cs}" fill="var(--well)"/>']
    for y in range(h):
        for x in range(W):
            filled = y < len(rows) and rows[y] >> x & 1
            k, n = ("G", 0) if filled else placed.get((x, y), (None, 0))
            fill = "var(--grid)" if k is None else COL.get(k, "#8a8f9c")
            Y = (h - 1 - y) * cs
            r.append(f'<rect x="{x * cs + .5}" y="{Y + .5}" width="{cs - 1}" height="{cs - 1}" fill="{fill}"/>')
            if n:
                r.append(f'<text x="{x * cs + cs / 2}" y="{Y + cs * .72}" text-anchor="middle" font-size="{cs * .6:.1f}" '
                         f'fill="#fff" font-weight="700">{n}</text>')
    r.append("</svg>")
    return "".join(r)


def pcx_block(rows, left, deal, ex, title, deal_line, C):
    placed, bad = replay(rows, left, deal, ex["h"], ex["plan"])
    _need(not bad, f"PC example {title}: {'; '.join(bad[:3])}")
    steps = "".join(f'<li data-p="{p}" data-c="{",".join(map(str, c))}" data-h="{int(hd)}">'
                    f'<b style="color:{COL[p]}">{p}</b>{_esc(C["pcx_hold"]) if hd else ""}</li>' for p, c, hd in ex["plan"])
    return (f'<figure data-deal="{deal}" data-h="{ex["h"]}"><figcaption><b>{_esc(title)}</b> · {_esc(deal_line)}</figcaption>'
            f'{pcx_svg(rows, ex["h"], placed)}<ol class="steps">{steps}</ol></figure>')


def pcx(e, b, ex, C):
    """The folded worked-PC section of one card (`ex` is its examples-artefact entry)."""
    rows, left = e["o"]["rows"], b["left"]
    lf = C["pcx_left"].format(left=left) if left else ""
    parts = []
    if ex["b3"] is None:
        parts.append(f'<p class="muted sm">{_esc(C["pcx_none3"])}</p>')
    else:
        d = ex["b3"]["deal"]
        parts.append(pcx_block(rows, left, d, ex["b3"], C["pcx_b3"], lf + C["pcx_deal3"].format(d=d), C))
    if b["p5"] >= BAG:
        parts.append(f'<p class="muted sm">{_esc(C["pcx_always3"])}</p>')
    elif ex["b4"] is None:
        parts.append(f'<p class="muted sm">{_esc(C["pcx_none4"])}</p>')
    else:
        d3, d4 = ex["b4"]["deal3"], ex["b4"]["deal4"]
        parts.append(pcx_block(rows, left, d3 + d4, ex["b4"], C["pcx_b4"], lf + C["pcx_deal34"].format(d3=d3, d4=d4), C))
    return (f'<details class="pcx" data-line="{_esc(ex["line"])}"><summary>{_esc(C["pcx"])}</summary>'
            f'<p class="muted sm">{_esc(C["pcx_note"])}</p><div class="pcxb">{"".join(parts)}</div></details>')


def _cells(pieces):
    out = {}
    for k, cs in pieces:
        for c in cs:
            out[(c % 10, c // 10)] = k
    return out


def card(rk, e, PR, badge="", pcxd=None):
    C = PR["card"]
    s, fx = e["s"], e["fx"]
    b = shown_tiling(e)
    cells = _cells(b["pieces"])
    H = max(y for x, y in cells) + 1
    tst = [tuple(t) for t in s["tst"]]
    for t in tst:
        cells.pop(t, None)
    res = {}
    for y, r in enumerate(e["o"]["rows"]):
        for x in range(10):
            if r >> x & 1:
                res[(x, y)] = "G"
    rh = max(4, len(e["o"]["rows"]))
    names = [PR["me_name"] if x.strip() == "yachi" else x.strip() for x in e["names"]]
    shown = ", ".join(_esc(x) for x in names[:4]) + (PR["names_more"].format(c=len(names)) if len(names) > 4 else "")
    d = dist(s)
    pos = PR["pos_centre"] if d >= WALL else PR["pos_wall"]
    left = b["left"] or C["no_left"]
    up_two, _, _, up_joint = fig_strings(e["best"], e["p4"], e["n4"])
    b1 = ""
    if fx is None or fx["cum"] == 0:
        rate, pc3, pc4, joint = pct(0), "未計", "未計", pct(0)
        counts = C["fixed_none"] if fx is None or not e["o"]["fixed"]["nb1"] else C["fixed_zero"]
    else:
        rate, pc3, pc4, joint = fixed_strings(fx)
        bc = _cells(e["o"]["fixed"]["b1"])
        b1 = (f'<div class="small"><div class="lab">{_esc(C["b1_title"])}</div>'
              f'{svg(bc, max(4, max(y for x, y in bc) + 1), 9)}</div>')
        counts = C["counts"].format(cum=f'{fx["cum"]:,}', n2=f"{N2:,}", p3n=f'{fx["pc3n"]:,}', p3d=f'{fx["pc3d"]:,}')
        if fx["n4"]:
            counts += C["counts_sample"].format(n=fx["n4"])
        if fx["same"]:
            counts += C["same_pc"]
    pc4_html = (f'<span title="{_esc(C["sample_title"].format(n=fx["n4"]))}">{_esc(pc4)}</span>'
                if pc4.startswith("≈") else _esc(pc4))
    note = ""
    if fx is None or fx["cum"] == 0:
        note = C["uncounted_note"]
    elif len(b["left"]) >= LEFT_NOTE_MIN:
        note = C["left_note"].format(c=len(b["left"]))
    note = f'<div class="muted sm warn">{_esc(note)}</div>' if note else ""
    cls = " me" if PR["me_name"] in names else ""
    line = C["pos_line"].format(pos=pos, d=d, cells=len(s["cells"]), nt=e["o"]["ntil"], left=left,
                                mirror=C["mirror"] if e["mirror"] else "")
    upper = (f'<div class="muted sm up">{_esc(C["upper"])} <b class="num" data-f="up_two">{up_two}</b> · '
             f'{_esc(C["joint"])} <b class="num" data-f="up_joint">{up_joint}</b></div>')
    return (f'<article class="card{cls}" data-pos="{pos}" data-card="{s["id"]}" data-rk="{_esc(rk)}" id="c{s["id"]}">'
            f'<div class="rk num">{_esc(rk)}</div>{badge}\n'
            f'<div class="bd">{svg(cells, max(H, 8), 15, tst)}<div class="smalls">{b1}<div class="small"><div class="lab">{_esc(C["left_title"])}</div>{svg(res, rh, 9)}</div></div></div>\n'
            f'<div class="meta"><div class="src">{shown}</div>\n'
            f'<div class="stats"><span>{C["two"]} <b class="num" data-f="two">{rate}</b></span>'
            f'<span>{C["pc3"]} <b class="num" data-f="pc3">{_esc(pc3)}</b></span>'
            f'<span>{C["pc4"]} <b class="num" data-f="pc4">{pc4_html}</b></span>'
            f'<span class="j">{C["joint"]} <b class="num" data-f="joint">{joint}</b></span></div>\n'
            f'<div class="muted sm cnt">{_esc(counts)}</div>{upper}{note}\n'
            f'<div class="muted sm">{_esc(line)}</div>\n'
            f'{pcx(e, b, pcxd[line_of(e["o"], b)], C) if pcxd is not None and b["B"] > 0 else ""}'
            f'<details data-s="s{s["id"]}"><summary>{_esc(C["details"].format(nt=e["o"]["ntil"]))}</summary><div class="tl"></div></details></div></article>')


def render(art, shp, PR, pcxd):
    ents = entries(art, shp)
    full, F, P, groups, order, me_cells, me = structure(ents)
    cent = [i + 1 for i, e in enumerate(F) if dist(e["s"]) >= WALL]
    hid = [i + 1 for i, e in enumerate(F) if dist(e["s"]) < WALL and i + 1 < cent[0] + 10]
    sample = max(r["n"] for r in art["pc4"])
    jb = "、".join(k.replace("johnbeak Gamushiro ", "") for k in shp["sources"]["johnbeak"]["fumens"])
    fmt = dict(n=len(ents), n_hd=len(shp["sources"]["harddrop"]["titles"]), jb=jb, sample=sample, full=full, pieces=full // 4,
               nf=len(F), np=len(P), me=me, me_cells=me_cells, nc=len(cent), left_min=LEFT_NOTE_MIN, wall=WALL,
               hid="、".join(f"#{i}" for i in hid[:HID_SHOWN]),
               n_over=sum(1 for e in ents if e["fx"] and e["fx"]["rate"] > Fraction(e["best"]["B"], N2)))
    me_sentence = PR["me_sentence"].format(**fmt) if me else ""
    cards = "\n".join(card(f"#{i + 1}", e, PR, pcxd=pcxd) for i, e in enumerate(F))
    pc = []
    for n in order:
        g = groups[n]
        k = (full - n) // 4
        pc.append(f'<h3 class="gh">{_esc(PR["group_head"].format(n=n, k=k, c=len(g)))}</h3><div class="grid">')
        pc += [card(f"{n}格 #{i + 1}", e, PR, f'<div class="badge">{_esc(PR["group_badge"].format(n=n, k=k))}</div>', pcxd) for i, e in enumerate(g)]
        pc.append("</div>")
    title = PR["title"] + RS.TITLE_MARK
    data = json.dumps(build_data(ents, PR), separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    with open(CSS_PATH, encoding="utf-8") as f:
        css = f.read().strip("\n")
    with open(JS_PATH, encoding="utf-8") as f:
        js = f.read().strip("\n")
    out = ['<!doctype html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
           "<style>", css, "</style></head><body><main>",
           f'<nav class="sm"><a href="index.html">{_esc(PR["back"])}</a></nav>',
           f'<div class="eyebrow">{RS.EYEBROW}</div>', f"<h1>{_esc(title)}</h1>",
           f'<p class="quar">{PR["quarantine"]}</p>']
    out += [f"<p>{t.format(me_sentence=me_sentence, **fmt)}</p>" for t in PR["intro"]]
    out += [f'<p class="muted sm">{_esc(PR["note_names"])}</p>',
            f'<details class="sm"><summary><b>{_esc(PR["reading_summary"])}</b></summary>\n<ul>']
    out += [f"<li>{t.format(**fmt)}</li>" for t in PR["reading"]]
    out += ["</ul></details>",
            f'<div class="bar"><button aria-pressed="true" data-f="{PR["pos_centre"]}">{_esc(PR["filter_centre"].format(**fmt))}</button>'
            f'<button aria-pressed="false" data-f="all">{_esc(PR["filter_all"])}</button></div>',
            f'<p class="muted sm">{_esc(PR["filter_note"].format(**fmt))}</p>',
            *pc3_table(F, PR, full),
            f'<h2>{_esc(PR["h2_full"].format(**fmt))}</h2>', '<div class="grid" id="g">', cards, "</div>",
            f'<h2>{_esc(PR["h2_partial"].format(**fmt))}</h2>',
            f'<p class="muted">{_esc(PR["partial_note"].format(me_top=PR["me_top"].format(**fmt) if me else "", **fmt))}</p>']
    out += pc
    out += ["</main>", f'<script id="{DATA_ID}" type="application/json">{data}</script>', "<script>", js, "</script></body></html>"]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ audit

def expected_upper(o, idx):
    """The see-both-bags figures (two-bag, joint) of shape `o`, by a direct scan for the best tiling."""
    best = None
    for t in o["til"]:
        if t["p5"] >= BAG:
            p4 = Fraction(1)
        else:
            r = idx.get(",".join(str(x) for x in o["rows"]) + "|" + t["left"])
            p4 = None if r is None else Fraction(t["p5"]) / BAG + (1 - Fraction(t["p5"]) / BAG) * Fraction(r["ok"], r["n"])
        sc = t["B"] * (p4 if p4 is not None else Fraction(t["p5"], BAG))
        if best is None or (sc, t["B"]) > (best[0], best[1]["B"]):
            best = (sc, t)
    return [pct(Fraction(best[1]["B"], N2)), pct(best[0] / N2)]


def expected_card(art, sid, idx):
    """A card's figures computed from the artefact alone and by a different route from `fixed_figs`: the best
    bag-1 board re-picked from every board's class counts, each class's PC read straight off a tiling ending
    on it, exact fractions throughout. Returns (fixed four, upper two, problems)."""
    o = art["shapes"][sid]
    bad = []
    f = o.get("fixed")
    up = expected_upper(o, idx)
    if not f or not f["nb1"]:
        return [pct(0), "未計", "未計", pct(0)], up, bad
    pcs = {}
    for t in o["til"]:
        if t["B"] and t["left"] not in pcs:
            if t["p5"] >= BAG:
                pcs[t["left"]] = (Fraction(1), t["p5"], 0, True)
            else:
                r = idx.get(",".join(str(x) for x in o["rows"]) + "|" + t["left"])
                if r is None:
                    pcs[t["left"]] = (Fraction(t["p5"], BAG), t["p5"], 0, False)
                else:
                    pcs[t["left"]] = (Fraction(t["p5"]) / BAG + (1 - Fraction(t["p5"]) / BAG) * Fraction(r["ok"], r["n"]),
                                      t["p5"], r["n"], True)
    def joint_of(cum):
        return sum((cum[k] - (cum[k - 1] if k else 0)) * pcs[c][0] for k, c in enumerate(f["classes"]))
    pick = max(range(len(f["cums"])), key=lambda i: (joint_of(f["cums"][i]), f["cums"][i][-1], -i))
    if pick != f["best"]:
        bad.append(f"shape {sid}: the artefact's best bag-1 board is {f['best']}, re-picked {pick}")
    if [pcs[c][0] for c in f["classes"]] != sorted((pcs[c][0] for c in f["classes"]), reverse=True):
        bad.append(f"shape {sid}: the leftover classes are not ordered by PC")
    t = o["til"][f["til"]]
    if not {(k, tuple(sorted(c))) for k, c in f["b1"]} <= {(k, tuple(sorted(c))) for k, c in t["pieces"]}:
        bad.append(f"shape {sid}: the drawn tiling does not hold the fixed bag-1 board")
    cum = f["cums"][f["best"]]
    tot = cum[-1]
    if not tot:
        return [pct(0), "未計", "未計", pct(0)], up, bad
    j, p3, n4, ok4 = Fraction(0), Fraction(0), 0, True
    for k, c in enumerate(f["classes"]):
        d = cum[k] - (cum[k - 1] if k else 0)
        if d:
            j += d * pcs[c][0]
            p3 += Fraction(d * pcs[c][1], BAG)
            n4 = max(n4, pcs[c][2])
            ok4 &= pcs[c][3]
    pc4 = (("≈" if n4 else "") + pct(j / tot)) if ok4 else "–"
    return [pct(Fraction(tot, N2)), pct(p3 / tot), pc4, pct(j / N2)], up, bad


def audit_pcx(cards, ents, pcxd):
    """Every card whose shape is two-bag buildable carries exactly one worked-PC section for its displayed tiling,
    its figures are the examples artefact's (deal, rows, plan), and every plan replays from the card's residue."""
    bad = []
    by = {e["s"]["id"]: e for e in ents}
    for sid, rk, body in cards:
        e = by[int(sid)]
        b = shown_tiling(e)
        secs = _PCX.findall(body)
        if b["B"] == 0:
            if secs:
                bad.append(f"card {rk}: a worked PC on a shape two bags cannot build")
            continue
        line = line_of(e["o"], b)
        if len(secs) != 1 or html.unescape(secs[0][0]) != line:
            bad.append(f"card {rk}: {len(secs)} worked-PC sections, or not for its displayed tiling")
            continue
        ex = pcxd[line]
        want = []
        if ex["b3"] is not None:
            want.append((ex["b3"]["deal"], ex["b3"]["h"], ex["b3"]["plan"]))
        if b["p5"] < BAG and ex["b4"] is not None:
            want.append((ex["b4"]["deal3"] + ex["b4"]["deal4"], ex["b4"]["h"], ex["b4"]["plan"]))
        got = []
        for deal, h, fb in _PCX_FIG.findall(secs[0][1]):
            plan = [[p, [int(x) for x in c.split(",")], bool(int(hd))] for p, c, hd in _PCX_STEP.findall(fb)]
            got.append((deal, int(h), plan))
            _, why = replay(e["o"]["rows"], b["left"], deal, int(h), plan)
            if why:
                bad.append(f"card {rk}: a worked PC does not replay ({why[0]})")
        norm = lambda w: [(d, h, [[p, list(c), bool(x)] for p, c, x in pl]) for d, h, pl in w]
        if norm(got) != norm(want):
            bad.append(f"card {rk}: the worked PCs are not the examples artefact's")
    return bad


def audit(page, art, shp, PR, pcxd=None):
    bad = RP.audit_quarantine(page, [RS.EYEBROW, RS.NO_CLAIM, PR["quarantine"]], DATA_ID)
    if set(page) & SIMPLIFIED:
        bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
    ents = entries(art, shp)
    idx = p4_index(art)
    cards = _CARD.findall(page)
    full, F, P, groups, order, me_cells, me = structure(ents)
    want = [e["s"]["id"] for e in F] + [e["s"]["id"] for n in order for e in groups[n]]
    got = [int(c[0]) for c in cards]
    if got != want:
        bad.append(f"the cards are not one per ranked shape in rank order (page {len(got)}, artefact {len(want)})")
    for sid, rk, body in cards:
        figs = {k: re.sub(r"<[^>]+>", "", html.unescape(v)) for k, v in _FIG.findall(body)}
        exp, eup, why = expected_card(art, int(sid), idx)
        bad += [f"card {rk}: {w}" for w in why]
        pr = [figs.get(k) for k in ("two", "pc3", "pc4", "joint")]
        if pr != exp:
            bad.append(f"card {rk}: printed figures {pr} are not the recomputed {exp}")
        if [figs.get("up_two"), figs.get("up_joint")] != eup:
            bad.append(f"card {rk}: the see-both-bags figures are not the recomputed {eup}")
        if "未計" in exp and ("0%" in pr[1:3]):
            bad.append(f"card {rk}: a 0% PC where 未計 is required")
        if ("≈" in exp[2]) != ("≈" in (pr[2] or "")):
            bad.append(f"card {rk}: the ≈ of a sampled figure is missing or spurious")
    if pcxd is not None:
        bad += audit_pcx(cards, ents, pcxd)
    bad += audit_pc3(page, F)
    m = _ISLAND.search(page)
    if not m:
        bad.append("no data island")
    else:
        try:
            island = json.loads(m.group(1).replace("<\\/", "</"))
        except ValueError:
            island = None
        if island != build_data(ents, PR):
            bad.append("the data island is not what the artefact builds")
    return bad


# ------------------------------------------------------------------ driver

def render_all(repo=REPO, inputs=None, prose=None):
    art, shp = inputs or load_inputs(repo)
    PR = prose or load_prose()
    pcxd = load_pcx(repo)
    page = render(art, shp, PR, pcxd)
    bad = audit(page, art, shp, PR, pcxd)
    _need(not bad, "; ".join(bad[:5]))
    return {OVERVIEW: page}


def selftest(repo=REPO):
    art, shp = load_inputs(repo)
    PR = load_prose()
    pcxd = load_pcx(repo)
    page = render(art, shp, PR, pcxd)
    killed = survived = 0

    def expect(label, mutated, want):
        nonlocal killed, survived
        bad = audit(mutated, art, shp, PR, pcxd)
        if bool(bad) == want:
            killed += want
            print(f'  {"killed" if want else "passed"}: {label}')
        else:
            survived += 1
            print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

    def sub(pattern, fn, flags=0):
        m = re.search(pattern, page, flags)
        _need(m, f"selftest: nothing to plant at {pattern!r}")
        return page[:m.start(1)] + fn(m.group(1)) + page[m.end(1):]

    expect("the rendered page (control)", page, False)
    expect("the quarantine sentence deleted", page.replace(PR["quarantine"], "", 1), True)
    expect("a claim badge planted", page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), True)
    expect("a card's joint figure edited", sub(r'data-f="joint">(\d)', lambda d: str((int(d) + 1) % 10)), True)
    expect("a card's two-bag figure edited", sub(r'data-f="two">(\d)', lambda d: str((int(d) + 1) % 10)), True)
    m = _CARD.search(page)
    expect("a card dropped", page.replace(m.group(0), "", 1), True)
    expect("a simplified glyph", page.replace("</h1>", "<p>实</p></h1>", 1), True)
    expect("≈ removed from a sampled figure", sub(r'data-f="pc4"><span title="[^"]*">(≈)', lambda _: ""), True)
    _need("未計" in page, "selftest: no 未計 card to plant 0% at")
    expect("0% shown where 未計 is required", sub(r'data-f="pc3">(未計)', lambda _: "0%"), True)
    expect("an island figure edited", sub(r'"t":\[\["[A-Z.]+","[^"]*","[^"]*","[^"]*","(\d)', lambda d: str((int(d) + 1) % 10)), True)
    m = _PCX.search(page)
    expect("a worked-PC section dropped", page.replace(m.group(0), "", 1), True)
    expect("a worked-PC deal letter swapped", sub(r'<figure data-deal="([A-Z]{2})', lambda d: d[::-1] if d[0] != d[1] else "IO"), True)
    expect("a worked-PC cell moved", sub(r'<li data-p="[A-Z]" data-c="(\d+)', lambda c: str((int(c) + 1) % 60)), True)
    expect("a worked-PC hold flag flipped", sub(r'<li data-p="[A-Z]" data-c="[\d,]+" data-h="([01])"', lambda h: "1" if h == "0" else "0"), True)
    expect("a card's see-both-bags figure edited", sub(r'data-f="up_two">(\d)', lambda d: str((int(d) + 1) % 10)), True)
    expect("the fixed figures dropped for the see-both-bags ones",
           page.replace('data-f="two">', 'data-f="two_x">', 1).replace('data-f="up_two">', 'data-f="two">', 1), True)

    worse = copy.deepcopy(art)
    o = next(o for o in worse["shapes"] if o.get("fixed") and o["fixed"]["nb1"] > 1
             and len({c[-1] for c in o["fixed"]["cums"]}) > 1)
    f = o["fixed"]
    f["best"] = next(i for i, c in enumerate(f["cums"]) if c[-1] != f["cums"][f["best"]][-1])
    expect("a worse bag-1 board picked", render(worse, shp, PR, pcxd), True)
    expect("a 3巡 PC table figure edited", sub(r'data-g="j3">(\d)', lambda d: str((int(d) + 1) % 10)), True)
    rows = _P3ROW.findall(page)
    expect("two 3巡 PC table rows swapped",
           page.replace(f'data-p3="{rows[0][0]}"', "data-p3=\"X\"", 1).replace(f'data-p3="{rows[1][0]}"', f'data-p3="{rows[0][0]}"', 1)
           .replace('data-p3="X"', f'data-p3="{rows[1][0]}"', 1), True)
    expect("an external request planted", page.replace("<style>", '<link rel="stylesheet" href="https://x.example/a.css"><style>', 1), True)
    print(f"selftest: {killed} killed, {survived} survived")
    return 1 if survived else 0


def site_card(inputs=None, prose=None):
    art, shp = inputs or load_inputs()
    PR = prose or load_prose()
    return {"href": OVERVIEW, "cases": len(entries(art, shp)), "unit": "個形", "kicker": PR["index_card"]["kicker"],
            "title": PR["overview_title"], "blurb": PR["index_card"]["blurb"]}


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
