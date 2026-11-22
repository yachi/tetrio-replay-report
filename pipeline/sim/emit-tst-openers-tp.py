#!/usr/bin/env python3
"""Emit analysis/tst-openers-tp.json: the T-placed bag-1 ranking (constructed, quarantined).

The counter is `pipeline/sim/tst2bag-tp-rs` (binary `tst2bag-tp`; a sibling of `tst2bag-rs`, which is left untouched so
`analysis/tst-openers.json` and its pins stay current). A bag-1 board here is six pieces: the T placed, four more of
IJLOSZ placed, and the sixth kind held. The ranking counts, for each board, the 5040^2 dealt orders of bags 1 and 2 that
finish on ANY of the 234 shapes (121 transcribed + 113 mirrors) holding that board, and the bag-3 Perfect Clear chance
of the leftover (`p5`, out of 5040). Everything below is offline (about 1.5 h on 4 cores) and never runs in CI;
`tst-openers-tp.test.ts` re-runs a pinned cheap subset and checks the artefact's invariants.

  B=pipeline/sim/tst2bag-tp-rs/target/release/tst2bag-tp ; E=pipeline/sim/emit-tst-openers-tp.py ; W=/tmp/tp3

  O1  python3 $E --shape-input > $W/mirror.in                                   # s<1000+id>|cells|tst, the 113 mirror shapes
  O2  JOBS=4 $B < $W/mirror.in > $W/mirror.out                                  # true A/B/p5 of every mirror tiling (default mode)
  O3  python3 $E --tpl-input --mirror-out $W/mirror.out > $W/tpl.in             # FIXED lines for all shapes with a class
      FIXED=1 TPL=1 LASTONLY=1 JOBS=4 $B < $W/tpl.in > $W/last.out               # per shape and T-placed board: built count
  O4  python3 $E --multi-input --last $W/last.out --mirror-out $W/mirror.out > $W/multi.in   # ub prune, one MULTI line per kept board
      for n in 0 1 2; do MULTI=1 SDB=$n JOBS=4 $B < $W/multi.in > $W/sd$n.out; done        # soft-drop budgets 0, 1, 2
      MULTI=1 JOBS=4 $B < $W/multi.in > $W/inf.out                                          # unlimited
  O5  python3 $E --merge --last $W/last.out --mirror-out $W/mirror.out --sd0 $W/sd0.out --sd1 $W/sd1.out \\
         --sd2 $W/sd2.out --inf $W/inf.out --out analysis/tst-openers-tp.json
  O6  python3 $E --compare-scratch <dir>                                        # one-off, against the earlier scratch run
      python3 $E --validate [analysis/tst-openers-tp.json]                      # Python-side invariants (the TS test is independent)

`--fallback <scratch dir>` writes the same artefact from the scratch outputs with the mirror shapes derived by symmetry
(`mirror.assumed: true`); it exists so a page can be built while O2-O4 run.

MIRRORING. A mirror is x -> 9 - x with J<->L, S<->Z (`mirror_shape` / `mirror_pieces`, the one implementation here; the
TS test and the page audit each re-implement it). Mirror shapes are not added to `tst-openers-shapes.json` (they have no
recorded drawing for the shape gate to re-read): the emitter derives them, id `1000 + id`, a shape whose mirror is already
in the catalogue skipped. The engine is NOT exactly mirror-symmetric (oracle-rs kick order / spawn column), so mirror
boards and shapes are counted for real and may differ from their partner.

BOARD NAMES `t<i>` are regenerated on every run: kept boards ordered by upper bound descending, then board key. The
test pins boards by their pieces, never their names.

UPPER BOUND. For a board listed by shapes S with single-shape built counts b_s (the LASTONLY run) and best leftover
chance m_s = max p5 / 5040: ub = min( min(1, sum b_s/5040^2) * max m_s , sum (b_s/5040^2) * m_s ), exact Fractions.
pc3 of the union is at most ub for every budget, so a board with ub <= 9/25 can never exceed 36%: ranks are complete
above 36% and nowhere below it.
"""
import argparse, hashlib, json, sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "pipeline" / "sim"
SHAPES = ROOT / "pipeline" / "openers" / "tst-openers-shapes.json"
OLD = ROOT / "analysis" / "tst-openers.json"
OUT = ROOT / "analysis" / "tst-openers-tp.json"
CRATES = ["tst2bag-tp-rs", "oracle-rs", "pc-solver-rs"]
SCHEMA = "tst-openers-tp/1"
B = 5040
N2 = B * B
THRESH = (9, 25)
BUDGETS = [0, 1, 2, None]
BKEYS = ["0", "1", "2", "inf"]
ORDER = "IJLOSTZ"
SW = {"J": "L", "L": "J", "S": "Z", "Z": "S"}
ID_OFFSET = 1000
SUFFIX = "（鏡像）"
QUARANTINE = ("constructed from the shapes file by an enumerator and a solver; nobody played these boards; "
              "no claim id, no badge")


def md5(b):
    return hashlib.md5(b).hexdigest()


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def emitter_files():
    fs = [SIM / "tst2bag-tp-rs" / "Cargo.toml"]
    for c in CRATES:
        fs += list((SIM / c / "src").rglob("*.rs"))
    return sorted(fs, key=lambda p: p.relative_to(SIM).as_posix())


def crate_md5():
    h = hashlib.md5()
    for p in emitter_files():
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


# ---- mirroring -----------------------------------------------------------------------------------------------------
def mirror_piece(k):
    return SW.get(k, k)


def mirror_cell(c):
    return (c // 10) * 10 + 9 - c % 10


def mirror_pieces(ps):
    """Pieces [[kind, [cells]]...] mirrored, each piece's cells sorted, pieces sorted by (kind, cells)."""
    return sorted(([mirror_piece(k), sorted(mirror_cell(c) for c in cs)] for k, cs in ps), key=lambda p: (p[0], p[1]))


def mirror_shape(s):
    return {"cells": sorted([9 - x, y] for x, y in s["cells"]), "tst": sorted([9 - x, y] for x, y in s["tst"])}


def shape_key(s):
    return (tuple(sorted(map(tuple, s["cells"]))), tuple(sorted(map(tuple, s["tst"]))))


def left_of(pieces):
    """The counter's `left`: kinds in IJLOSTZ order, each up to twice (the TST's T counts as a used T)."""
    out = ""
    for k in ORDER:
        used = sum(1 for p in pieces if p[0] == k) + (1 if k == "T" else 0)
        out += k * max(0, 2 - used)
    return out


def sort_left(l):
    return "".join(sorted(l, key=ORDER.index))


def piece_set(ps):
    return frozenset((k, tuple(sorted(cs))) for k, cs in ps)


def board_key(pieces):
    return tuple(sorted((k, tuple(sorted(cs))) for k, cs in pieces))


def mirror_board_key(key):
    return board_key(mirror_pieces([[k, list(cs)] for k, cs in key]))


def pt(ps):
    return ";".join(f"{x},{y}" for x, y in ps)


# ---- catalogue -----------------------------------------------------------------------------------------------------
def load_inputs():
    old = json.loads(OLD.read_text())
    shapes = json.loads(SHAPES.read_text())["shapes"]
    return old, shapes


def mirror_catalogue(shapes):
    """The mirror shapes: id 1000 + id, names suffixed, skipping a shape whose mirror is already present."""
    have = {shape_key(s) for s in shapes}
    out = []
    for s in shapes:
        m = mirror_shape(s)
        if shape_key(m) in have:
            continue
        have.add(shape_key(m))
        out.append({"id": ID_OFFSET + s["id"], "mirror_of": s["id"], "names": [n + SUFFIX for n in s["names"]],
                    "cells": m["cells"], "tst": m["tst"]})
    return out


def shape_input_lines(shapes):
    return [f"s{m['id']}|{pt(m['cells'])}|{pt(m['tst'])}" for m in mirror_catalogue(shapes)]


def align_mirror_til(o, mrec):
    """The mirror shape's tilings in the ORIGINAL's `til` order: [[A, B, p5], ...] from the counter's own output."""
    by = {piece_set(t["pieces"]): t for t in mrec["til"]}
    assert len(by) == len(mrec["til"]) == len(o["til"]), f"mirror of shape {o['id']}: tiling count differs"
    out = []
    for t in o["til"]:
        mt = by[piece_set(mirror_pieces(t["pieces"]))]
        assert mt["left"] == sort_left("".join(mirror_piece(c) for c in t["left"])), f"shape {o['id']}: mirror leftover differs"
        out.append([mt["A"], mt["B"], mt["p5"]])
    return out


def build_mirror_shapes(old, shapes, mirror_out):
    """[{id, mirror_of, til}] ; mirror_out is the O2 counter output lines, or None for the symmetry assumption."""
    by_old = {o["id"]: o for o in old["shapes"]}
    got = {}
    if mirror_out is not None:
        for l in mirror_out:
            if l.strip():
                r = json.loads(l)
                assert r["name"] not in got
                got[r["name"]] = r
    out = []
    for m in mirror_catalogue(shapes):
        o = by_old[m["mirror_of"]]
        if mirror_out is None:
            til = [[t["A"], t["B"], t["p5"]] for t in o["til"]]
        else:
            til = align_mirror_til(o, got.pop(f"s{m['id']}"))
        out.append({"id": m["id"], "mirror_of": m["mirror_of"], "til": til})
    assert not got, f"mirror output names unknown shapes {sorted(got)}"
    return out


class Cat:
    """id -> {cells, tst, til:[{pieces, left, A, B, p5}], classes: {left: p5}, maxp5}."""

    def __init__(self, old, shapes, mirror_shapes):
        self.by = {}
        so = {s["id"]: s for s in shapes}
        oo = {o["id"]: o for o in old["shapes"]}
        for s in shapes:
            o = oo[s["id"]]
            self._add(s["id"], s["cells"], s["tst"],
                      [dict(pieces=t["pieces"], left=t["left"], A=t["A"], B=t["B"], p5=t["p5"]) for t in o["til"]])
        mc = {m["id"]: m for m in mirror_catalogue(shapes)}
        for ms in mirror_shapes:
            m = mc[ms["id"]]
            o = oo[ms["mirror_of"]]
            til = []
            for t, (a, b, p5) in zip(o["til"], ms["til"]):
                til.append(dict(pieces=mirror_pieces(t["pieces"]), left=sort_left("".join(mirror_piece(c) for c in t["left"])), A=a, B=b, p5=p5))
            self._add(m["id"], m["cells"], m["tst"], til)
        assert len(self.by) == len(shapes) + len(mc)

    def _add(self, sid, cells, tst, til):
        cl = {}
        for t in til:
            if t["B"] > 0:
                assert cl.setdefault(t["left"], t["p5"]) == t["p5"], f"shape {sid}: leftover {t['left']!r} has two p5"
        self.by[sid] = dict(id=sid, cells=cells, tst=tst, til=til, classes=cl, maxp5=Fraction(max(cl.values()), B) if cl else Fraction(0))


def tpl_input_lines(cat):
    out = []
    for sid in sorted(cat.by):
        s = cat.by[sid]
        if s["classes"]:
            cl = sorted(s["classes"], key=lambda l: (-s["classes"][l], l))
            out.append(f"s{sid}|{pt(s['cells'])}|{pt(s['tst'])}|" + ";".join(c or "-" for c in cl))
    return out


# ---- boards, upper bound, MULTI lines ------------------------------------------------------------------------------
def boards_from_last(lines):
    """board key -> {shape id: built count of that shape alone}."""
    out = {}
    for l in lines:
        if not l.strip():
            continue
        r = json.loads(l)
        sid = int(r["name"][1:])
        for b in r["b1"]:
            k = board_key(b["pieces"])
            assert len(b["cum"]) == 1
            assert sid not in out.setdefault(k, {}), "board listed twice for a shape"
            out[k][sid] = b["cum"][0]
    return out


def upper_bound(L, cat):
    bs = {sid: Fraction(b, N2) for sid, b in L.items()}
    mp = {sid: cat.by[sid]["maxp5"] for sid in L}
    s = sum(bs.values())
    return min(min(Fraction(1), s) * max(mp.values()), sum(bs[i] * mp[i] for i in bs))


def kept_boards(boards, cat):
    ub = {k: upper_bound(L, cat) for k, L in boards.items()}
    keep = [k for k in boards if ub[k] > Fraction(*THRESH)]
    keep.sort(key=lambda k: (-ub[k], k))
    return keep, ub


def board_classes(ids, cat):
    """Ranked classes of a board's shape list: [(si, left, p5)] by (-p5, si, left)."""
    cls = [(s["classes"][l], si, l) for si, sid in enumerate(ids) for s in [cat.by[sid]] for l in s["classes"]]
    cls.sort(key=lambda c: (-c[0], c[1], c[2]))
    return [(si, l, p) for p, si, l in cls]


def multi_lines(keep, boards, cat):
    out = []
    for i, k in enumerate(keep):
        ids = sorted(boards[k])
        b1 = "/".join(f"{kind}:{','.join(map(str, cs))}" for kind, cs in k)
        sh = "#".join(f"{pt(cat.by[sid]['cells'])}|{pt(cat.by[sid]['tst'])}" for sid in ids)
        cl = ";".join(f"{si}:{l or '-'}" for si, l, _ in board_classes(ids, cat))
        out.append(f"t{i}#{b1}#{sh}#{cl}")
    return out


# ---- the artefact --------------------------------------------------------------------------------------------------
def read_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def assemble(old, shapes, mirror_shapes, assumed, boards, keep, multi):
    """multi: {bkey: {board name: {"ntil","cum"}}} for each budget; boards: key -> {sid: built1}; keep: kept keys in name order.
    Shape lists and class orders are given per board in `plan` (name -> (ids, classes))."""
    raise NotImplementedError


def mk_artefact(old, shapes, mirror_shapes, assumed, plan, results, prune_total):
    """plan: list of dict(key, ids, classes, built1); results: {bk: {i: {"ntil","cum"}}} by position i in plan."""
    names = {k: f"t{i}" for i, k in enumerate(p["key"] for p in plan)}
    bd = []
    for i, p in enumerate(plan):
        k = p["key"]
        mk = mirror_board_key(k)
        held = [c for c in "IJLOSZ" if c not in {kk for kk, _ in k}]
        assert len(held) == 1
        ntils = {results[bk][i]["ntil"] for bk in BKEYS}
        assert len(ntils) == 1, f"board {i}: ntil differs between budgets"
        bd.append({
            "name": names[k],
            "pieces": [[kk, list(cs)] for kk, cs in k],
            "held": held[0],
            "mirror": names.get(mk),
            "shapes": p["ids"],
            "built1": [p["built1"][sid] for sid in p["ids"]],
            "classes": [[si, l, v] for si, l, v in p["classes"]],
            "ntil": ntils.pop(),
            "cum": {bk: results[bk][i]["cum"] for bk in BKEYS},
        })
    return {
        "schema": SCHEMA,
        "report_eligible": False,
        "constructed": True,
        "quarantine": QUARANTINE,
        "md5": {"crate": crate_md5(), "tst_openers": md5(OLD.read_bytes()), "shapes": md5(canon(shapes).encode())},
        "budgets": BUDGETS,
        "prune": {"threshold": list(THRESH), "boards_total": prune_total, "kept": len(plan)},
        "mirror": {"id_offset": ID_OFFSET, "suffix": SUFFIX, "assumed": assumed},
        "mirror_shapes": mirror_shapes,
        "boards": bd,
    }


def write_art(art, path):
    Path(path).write_text(json.dumps(art, separators=(",", ":"), ensure_ascii=False) + "\n")


def merge(args):
    old, shapes = load_inputs()
    mout = Path(args.mirror_out).read_text().splitlines()
    ms = build_mirror_shapes(old, shapes, mout)
    cat = Cat(old, shapes, ms)
    boards = boards_from_last(Path(args.last).read_text().splitlines())
    keep, _ = kept_boards(boards, cat)
    names = {f"t{i}": k for i, k in enumerate(keep)}
    res = {}
    for bk, path in (("0", args.sd0), ("1", args.sd1), ("2", args.sd2), ("inf", args.inf)):
        res[bk] = {}
        for r in read_jsonl(path):
            assert r["name"] in names and r.get("cum") is not None, f"{path}: bad record {r['name']}"
            i = int(r["name"][1:])
            assert i not in res[bk]
            res[bk][i] = r
        assert sorted(res[bk]) == list(range(len(keep))), f"{path}: does not cover the kept boards"
    plan = []
    for k in keep:
        ids = sorted(boards[k])
        plan.append(dict(key=k, ids=ids, classes=board_classes(ids, cat), built1=boards[k]))
    art = mk_artefact(old, shapes, ms, False, plan, res, len(boards))
    validate(art, cat_given=cat)
    write_art(art, args.out)
    print(f"wrote {args.out}: {len(keep)} boards of {len(boards)}", file=sys.stderr)


def fallback(args):
    old, shapes = load_inputs()
    d = Path(args.fallback)
    ms = build_mirror_shapes(old, shapes, None)
    cat = Cat(old, shapes, ms)
    boards = boards_from_last((d / "last.out").read_text().splitlines())
    keep, _ = kept_boards(boards, cat)
    meta = json.loads((d / "multi-meta.json").read_text())
    sc_in = {}
    for l in (d / "multi.in").read_text().splitlines():
        f = l.split("#")
        sc_in[f[0]] = f
    sc_by_key = {board_key(m["entry"]["board"]): m for m in meta}
    assert set(sc_by_key) == set(keep), f"scratch kept {len(sc_by_key)} boards, the exact prune keeps {len(keep)}"
    sc_res = {}
    for bk, fn in (("0", "sd0.out"), ("1", "sd1.out"), ("2", "sd2.out"), ("inf", "multi.out")):
        sc_res[bk] = {r["name"]: r for r in read_jsonl(d / fn)}
    plan, res = [], {bk: {} for bk in BKEYS}
    dead = 0
    for i, k in enumerate(keep):
        m = sc_by_key[k]
        ids = m["ids"]  # scratch shape order: the cum arrays follow the scratch class order
        assert sorted(ids) == sorted(boards[k]), f"board {i}: shape lists differ"
        f = sc_in[m["name"]]
        cl = []
        for tok in f[-1].split(";"):
            si, l = tok.split(":")
            si = int(si)
            l = "" if l == "-" else l
            ls = sort_left(l)
            if ls != l:
                dead += 1
            p5 = cat.by[ids[si]]["classes"][ls]
            cl.append((si, ls, p5))
        assert [c[2] for c in cl] == m["p5"], f"board {i}: class p5 list differs"
        plan.append(dict(key=k, ids=ids, classes=cl, built1=boards[k]))
        for bk in BKEYS:
            r = sc_res[bk][m["name"]]
            assert r["cum"] is not None and len(r["cum"]) == len(cl)
            res[bk][i] = r
    art = mk_artefact(old, shapes, ms, True, plan, res, len(boards))
    validate(art, cat_given=cat)
    write_art(art, args.out)
    print(f"wrote {args.out}: {len(keep)} boards of {len(boards)} (assumed mirrors; {dead} scratch classes had unsorted leftovers)", file=sys.stderr)


# ---- figures and validation ----------------------------------------------------------------------------------------
def joint(cum, classes):
    prev, num = 0, 0
    for c, (_, _, p5) in zip(cum, classes):
        num += (c - prev) * p5
        prev = c
    return Fraction(num, N2 * B)


def built_of(cum):
    return Fraction(cum[-1], N2)


def validate(art, cat_given=None, path="artefact"):
    """Python-side invariants. Raises AssertionError; the TS test re-checks them independently and more."""
    assert art["schema"] == SCHEMA and art["report_eligible"] is False and art["constructed"] is True
    old, shapes = load_inputs()
    cat = cat_given or Cat(old, shapes, art["mirror_shapes"])
    assert art["md5"]["tst_openers"] == md5(OLD.read_bytes()), "tst-openers.json changed"
    assert art["md5"]["shapes"] == md5(canon(shapes).encode()), "shapes file changed"
    assert art["md5"]["crate"] == crate_md5(), "crate sources changed"
    miss = {m["id"] for m in mirror_catalogue(shapes)}
    assert {m["id"] for m in art["mirror_shapes"]} == miss and len(miss) == len(art["mirror_shapes"])
    bs = art["boards"]
    names = {b["name"]: b for b in bs}
    assert len(names) == len(bs) == art["prune"]["kept"]
    seen_keys = set()
    for i, b in enumerate(bs):
        assert b["name"] == f"t{i}"
        key = board_key(b["pieces"])
        assert key not in seen_keys
        seen_keys.add(key)
        assert len(b["pieces"]) == 6 and sorted(k for k, _ in b["pieces"]) == sorted("T" + "IJLOSZ".replace(b["held"], ""))
        cells = [c for _, cs in b["pieces"] for c in cs]
        assert len(cells) == 24 and len(set(cells)) == 24
        if b["mirror"] is not None:
            assert names[b["mirror"]]["mirror"] == b["name"]
            assert board_key(names[b["mirror"]]["pieces"]) == mirror_board_key(key)
        assert b["shapes"] == sorted(b["shapes"]) or art["mirror"]["assumed"]
        cls = board_classes(b["shapes"], cat) if not art["mirror"]["assumed"] else None
        got = [(si, l, p) for si, l, p in b["classes"]]
        if cls is not None:
            assert got == cls, f"{b['name']}: classes differ"
        else:
            assert sorted(got) == sorted(board_classes(b["shapes"], cat))
        prev_b = None
        for bk in BKEYS:
            c = b["cum"][bk]
            assert len(c) == len(got) and all(x <= y for x, y in zip(c, c[1:])) and c[-1] <= N2
            if prev_b:
                assert all(x <= y for x, y in zip(prev_b, c)), f"{b['name']}: budgets not monotone"
            prev_b = c
        assert max(b["built1"]) <= b["cum"]["inf"][-1] <= sum(b["built1"]), f"{b['name']}: built bounds"
        L = dict(zip(b["shapes"], b["built1"]))
        assert upper_bound(L, cat) > Fraction(*THRESH)
    return True


def residue_rows(cells, tst):
    """Residue rows by the definition (shape + the TST's cells, minus the full rows, trailing empty rows dropped)."""
    allc = {y * 10 + x for x, y in cells} | {y * 10 + x for x, y in tst}
    rows = []
    for y in range(12):
        n = [x for x in range(10) if y * 10 + x in allc]
        if len(n) != 10:
            rows.append(sum(1 << x for x in n))
    while rows and rows[-1] == 0:
        rows.pop()
    return rows


def shown_class_index(b):
    """Index of the class with the largest (cum_inf[k] - cum_inf[k-1]) * p5[k]; ties to the earlier class."""
    cum, prev, best, bi = b["cum"]["inf"], 0, -1, 0
    for k, (c, (_, _, p5)) in enumerate(zip(cum, b["classes"])):
        v = (c - prev) * p5
        prev = c
        if v > best:
            best, bi = v, k
    return bi


def pcx_lines(art=None):
    """`rows|left` lines for the worked PCs: for every board whose joint (unlimited) chance exceeds the threshold, the
    residue of its shown class's shape and that leftover. Deduplicated, in board order. The page's own `pcx_lines()`
    (pipeline/tst_openers_tp_page.py) takes precedence in emit-tst-pc-examples.py when the module defines it."""
    art = art or json.loads(OUT.read_text())
    old, shapes = load_inputs()
    cat = Cat(old, shapes, art["mirror_shapes"])
    out, seen = [], set()
    for b in art["boards"]:
        if joint(b["cum"]["inf"], b["classes"]) <= Fraction(*THRESH):
            continue
        si, left, _ = b["classes"][shown_class_index(b)]
        s = cat.by[b["shapes"][si]]
        line = ",".join(map(str, residue_rows(s["cells"], s["tst"]))) + "|" + left
        if line not in seen:
            seen.add(line)
            out.append(line)
    return out


def validate_cmd(args):
    art = json.loads(Path(args.validate or OUT).read_text())
    validate(art)
    print(f"ok: {len(art['boards'])} boards, mirror.assumed={art['mirror']['assumed']}", file=sys.stderr)


# ---- O6 ------------------------------------------------------------------------------------------------------------
def compare_scratch(args):
    d = Path(args.compare_scratch)
    art = json.loads(OUT.read_text())
    meta = json.loads((d / "multi-meta.json").read_text())
    sc = {}
    for bk, fn in (("0", "sd0.out"), ("1", "sd1.out"), ("2", "sd2.out"), ("inf", "multi.out")):
        sc[bk] = {r["name"]: r for r in read_jsonl(d / fn)}
    mine = {board_key(b["pieces"]): b for b in art["boards"]}
    theirs = {board_key(m["entry"]["board"]): m for m in meta}
    print(f"kept: mine {len(mine)}, scratch {len(theirs)}, same set {set(mine) == set(theirs)}")
    diffs = {"orig": 0, "mirror": 0}
    n_orig = n_mir = 0
    pair_diff = []
    rows = []
    for k, b in mine.items():
        m = theirs.get(k)
        if m is None:
            continue
        touches_mirror = any(sid >= ID_OFFSET for sid in b["shapes"])
        cls_mine = [(si, l, p) for si, l, p in b["classes"]]
        differ = False
        det = {}
        for bk in BKEYS:
            r = sc[bk][m["name"]]
            jm = joint(b["cum"][bk], cls_mine)
            js = Fraction(sum((c - pc) * p for c, pc, p in zip(r["cum"], [0] + r["cum"][:-1], m["p5"])), N2 * B)
            det[bk] = (jm, js, b["cum"][bk][-1], r["cum"][-1])
            if jm != js or b["cum"][bk][-1] != r["cum"][-1]:
                differ = True
        if b["ntil"] != sc["inf"][m["name"]]["ntil"]:
            differ = True
        if touches_mirror:
            n_mir += 1
        else:
            n_orig += 1
        if differ:
            diffs["mirror" if touches_mirror else "orig"] += 1
        rows.append((b["name"], k, differ, touches_mirror, det))
    print(f"boards without mirror shapes: {n_orig} (differ {diffs['orig']}); touching mirror shapes: {n_mir} (differ {diffs['mirror']})")
    byname = {b["name"]: b for b in art["boards"]}
    for name, k, differ, tm, det in rows:
        b = byname[name]
        if b["mirror"] and differ:
            pass
    # mirror pairs whose figures differ from each other
    seen = set()
    for b in art["boards"]:
        if b["mirror"] is None or b["name"] in seen or b["mirror"] == b["name"]:
            continue
        o = byname[b["mirror"]]
        seen |= {b["name"], o["name"]}
        fb = [joint(b["cum"][bk], [tuple(c) for c in b["classes"]]) for bk in BKEYS]
        fo = [joint(o["cum"][bk], [tuple(c) for c in o["classes"]]) for bk in BKEYS]
        cb = [b["cum"][bk][-1] for bk in BKEYS]
        co = [o["cum"][bk][-1] for bk in BKEYS]
        if fb != fo or cb != co:
            pair_diff.append((b["name"], o["name"], [float(x) for x in fb], [float(x) for x in fo]))
    print(f"mirror pairs: {len(seen) // 2}, differing: {len(pair_diff)}")
    for p in pair_diff[:40]:
        print("  pair", p[0], p[1], [round(x * 100, 3) for x in p[2]], [round(x * 100, 3) for x in p[3]])
    top = sorted(art["boards"], key=lambda b: -joint(b["cum"]["inf"], [tuple(c) for c in b["classes"]]))
    print("top 10 by unlimited pc3 (pair duplicates listed):")
    for b in top[:10]:
        cl = [tuple(c) for c in b["classes"]]
        f = [joint(b["cum"][bk], cl) for bk in BKEYS]
        print(f"  {b['name']:>5} mirror {b['mirror']}  built {float(built_of(b['cum']['inf'])) * 100:.2f}%  pc3 inf {float(f[3]) * 100:.2f}  <=2 {float(f[2]) * 100:.2f}  <=1 {float(f[1]) * 100:.2f}  0 {float(f[0]) * 100:.2f}")
    # scratch top for comparison
    ts = []
    for m in meta:
        r = sc["inf"][m["name"]]
        ts.append((sum((c - pc) * p for c, pc, p in zip(r["cum"], [0] + r["cum"][:-1], m["p5"])) / (N2 * B), m["name"]))
    ts.sort(reverse=True)
    print("scratch top 10:", [(n, round(v * 100, 2)) for v, n in ts[:10]])
    n204 = sum(1 for b in art["boards"] if joint(b["cum"]["inf"], [tuple(c) for c in b["classes"]]) > Fraction(9, 25))
    print("boards with unlimited pc3 > 36%:", n204)
    # pairs deduped top 5
    def pair_top(boards_):
        out, seen = [], set()
        for fval, name, mname in boards_:
            if name in seen:
                continue
            seen |= {name, mname}
            out.append((fval, name))
        return out
    mine_pairs = pair_top([(joint(b["cum"]["inf"], [tuple(c) for c in b["classes"]]), b["name"], b["mirror"]) for b in top])
    print("deduped top 5 (mine):", [(n, round(float(v) * 100, 2)) for v, n in mine_pairs[:5]])
    kmine = {b["name"]: board_key(b["pieces"]) for b in art["boards"]}
    scratch_pairs = []
    seen = set()
    for v, n in ts:
        k = board_key(next(m for m in meta if m["name"] == n)["entry"]["board"])
        if k in seen:
            continue
        seen |= {k, mirror_board_key(k)}
        scratch_pairs.append((v, k))
    sc_top = [k for _, k in scratch_pairs[:5]]
    my_top = [kmine[n] for _, n in mine_pairs[:5]]
    same = [(k in sc_top) for k in my_top]
    print("deduped top 5 same boards as scratch (as pairs):", all(any(k == s or k == mirror_board_key(s) for s in sc_top) for k in my_top))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shape-input", action="store_true")
    ap.add_argument("--tpl-input", action="store_true")
    ap.add_argument("--multi-input", action="store_true")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--fallback")
    ap.add_argument("--compare-scratch")
    ap.add_argument("--validate", nargs="?", const="")
    ap.add_argument("--mirror-out")
    ap.add_argument("--last")
    ap.add_argument("--sd0")
    ap.add_argument("--sd1")
    ap.add_argument("--sd2")
    ap.add_argument("--inf")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    if a.validate is not None:
        return validate_cmd(a)
    if a.compare_scratch:
        return compare_scratch(a)
    if a.fallback:
        return fallback(a)
    old, shapes = load_inputs()
    if a.shape_input:
        print("\n".join(shape_input_lines(shapes)))
        return
    if a.merge:
        return merge(a)
    ms = build_mirror_shapes(old, shapes, Path(a.mirror_out).read_text().splitlines() if a.mirror_out else None)
    cat = Cat(old, shapes, ms)
    if a.tpl_input:
        print("\n".join(tpl_input_lines(cat)))
        return
    if a.multi_input:
        boards = boards_from_last(Path(a.last).read_text().splitlines())
        keep, _ = kept_boards(boards, cat)
        print("\n".join(multi_lines(keep, boards, cat)))
        print(f"{len(boards)} boards, {len(keep)} kept", file=sys.stderr)
        return
    ap.error("no action")


if __name__ == "__main__":
    main()
