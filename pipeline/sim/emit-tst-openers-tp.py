#!/usr/bin/env python3
"""Emit analysis/tst-openers-tp.json: the T-placed bag-1 ranking (constructed, quarantined).

The counter is `pipeline/sim/tst2bag-tp-rs` (binary `tst2bag-tp`; a sibling of `tst2bag-rs`, which is left untouched so
`analysis/tst-openers.json` and its pins stay current). A bag-1 board here is six pieces in one of two kinds: PLACED
(the T placed, four more of IJLOSZ placed, the sixth kind held; names t<i>) or HELD (the six pieces IJLOSZ placed and the T in
hold, `held == "T"`; names h<i>, listed after every placed board). Both kinds are counted by the same method and ranked together. The ranking counts, for each board, the 5040^2 dealt orders of bags 1 and 2 that
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

HELD BOARDS (schema tst-openers-tp/2) are added on top of the committed placed boards, which are kept verbatim (`--reuse-placed`):

  H1  python3 $E --tpl-input --mirror-out $W/mirror.out > $W/tpl.in             # same lines as O3
  H2  FIXED=1 LASTONLY=1 JOBS=4 $B < $W/tpl.in > $W/lasth.out                   # no TPL: every six-kind board, built count per shape
  H3  python3 $E --multi-input --held --mirror-art --last-held $W/lasth.out > $W/hmulti.in   # held prune (own or mirror ub), h<i> lines
  H4  for n in 0 1 2; do MULTI=1 SDB=$n JOBS=4 $B < $W/hmulti.in > $W/hsd$n.out; done ; MULTI=1 JOBS=4 $B < $W/hmulti.in > $W/hinf.out
  H5  python3 $E --merge --reuse-placed analysis/tst-openers-tp.json --last-held $W/lasth.out --hsd0 $W/hsd0.out --hsd1 $W/hsd1.out \
         --hsd2 $W/hsd2.out --hinf $W/hinf.out --out analysis/tst-openers-tp.json
  H6  python3 $E --validate ; python3 $E --compare-held $W/lasth.out            # compare-held: FIXED_BOARDS order vs tst-openers.json fixed.cums

`--fallback <scratch dir>` writes the same artefact from the scratch outputs with the mirror shapes derived by symmetry
(`mirror.assumed: true`); it exists so a page can be built while O2-O4 run.

FAMILIES (schema tst-openers-tp/4; the hold-swap figure of docs/tst-openers.html). A LAYOUT is a set of seven placements, one of
each of IJLOSTZ, on 28 distinct cells; its VARIANTS are the kept boards that are the layout minus one piece (the piece left out is
the one held: minus the T is a T-held board). A family is a layout with at least two variants in the artefact. With the five-piece
preview the first bag's dealt order o1 is known before any hold decision, so the player picks the variant per o1.

  F1  the bag-1 phase of the counter depends only on the board and o1: the counter's states at the end of phase 0 are
      (soft-drop spent s, the board, the held piece), the held piece is fixed by the board, and a smaller s dominates. So for one
      o1 a board's count is D_k(b - s(o1)) with s(o1) the least soft-drop cost of building the board from that order (or none),
      D_k(r) the bag-2 count of the first k+1 leftover classes with r budget left, and
      cum_b[k] = sum_s n_s D_k(b - s), cum_inf[k] = n_feasible D_k(inf). `pipeline/sim/tst-b1vec-rs` computes s(o1) for every
      board and every one of the 5040 dealt orders; D is solved from the committed `cum` by a triangular solve in which EVERY
      division must be exact (`solve_D`: that exactness is the proof of the identity, no recount of any board is needed).
  F2  with J_v(r) = sum_k (D_k(r) - D_{k-1}(r)) p5_k, the policy picks per o1 the variant maximising J_v(b - s_v(o1)) (ties:
      larger built count, then the earlier name); pc3_F = sum_o1 that maximum, joint_F = pc3_F / 5040^3, built_F = the sum of the
      chosen variants' bag-2 counts over 5040^2. The choice is made per budget.
  F3  a variant pruned from the artefact (upper bound <= 36%) is not in the family, so a family figure is a lower bound
      (`families.complete: false`). Cards and ranks stay per mirror pair by the board's own joint.
  F4  `both` (per family) runs the F2 policy over the variants AND their mirror boards, so each o1 picks the better hand too;
      `pairs` runs it over each board and its mirror board. Each is a superset of either hand's options, so its joint is at least
      either hand's (`validate_families` checks that sandwich).

  B1  python3 $E --b1-input > $W/b1.in ; pipeline/sim/tst-b1vec-rs/target/release/tst-b1vec < $W/b1.in > $W/b1.out     # about 40 s
      python3 $E --b1-merge $W/b1.out                                          # writes analysis/tst-openers-tp-b1.json
  B2  python3 $E --families                                                    # adds `families` to analysis/tst-openers-tp.json (boards untouched)
  B3  python3 $E --check                                                       # CI: the b1 artefact is what the crate gives, the families recompute
      python3 $E --cross-check <tst2bag-tp binary>                             # MULTI=1 B1ONLY=1 SDB=n against the vectors, on sampled boards

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
SCHEMA = "tst-openers-tp/4"
SCHEMA_V2 = "tst-openers-tp/2"
SCHEMA_V1 = "tst-openers-tp/1"
B1_SCHEMA = "tst-openers-tp-b1/1"
B1_OUT = ROOT / "analysis" / "tst-openers-tp-b1.json"
B1_CRATE = "tst-b1vec-rs"
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


def kept_held(boards, cat):
    """Held boards (six pieces IJLOSZ, T in hold): kept if the board's OR its mirror's upper bound exceeds the threshold, so a
    mirror pair is kept together. Returns (keys in name order, ub)."""
    ub = {k: upper_bound(L, cat) for k, L in boards.items()}
    th = Fraction(*THRESH)
    keep = []
    for k in boards:
        assert all(kk != "T" for kk, _ in k), "a T in a held board"
        mk = mirror_board_key(k)
        assert mk != k, "a held board equal to its own mirror"
        if ub[k] > th or (mk in ub and ub[mk] > th):
            keep.append(k)
    keep.sort(key=lambda k: (-ub[k], k))
    return keep, ub


def board_classes(ids, cat):
    """Ranked classes of a board's shape list: [(si, left, p5)] by (-p5, si, left)."""
    cls = [(s["classes"][l], si, l) for si, sid in enumerate(ids) for s in [cat.by[sid]] for l in s["classes"]]
    cls.sort(key=lambda c: (-c[0], c[1], c[2]))
    return [(si, l, p) for p, si, l in cls]


def multi_lines(keep, boards, cat, prefix="t"):
    out = []
    for i, k in enumerate(keep):
        ids = sorted(boards[k])
        b1 = "/".join(f"{kind}:{','.join(map(str, cs))}" for kind, cs in k)
        sh = "#".join(f"{pt(cat.by[sid]['cells'])}|{pt(cat.by[sid]['tst'])}" for sid in ids)
        cl = ";".join(f"{si}:{l or '-'}" for si, l, _ in board_classes(ids, cat))
        out.append(f"{prefix}{i}#{b1}#{sh}#{cl}")
    return out


# ---- the artefact --------------------------------------------------------------------------------------------------
def read_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def assemble(old, shapes, mirror_shapes, assumed, boards, keep, multi):
    """multi: {bkey: {board name: {"ntil","cum"}}} for each budget; boards: key -> {sid: built1}; keep: kept keys in name order.
    Shape lists and class orders are given per board in `plan` (name -> (ids, classes))."""
    raise NotImplementedError


def board_records(plan, results, prefix="t"):
    """Board dicts for `plan`; names `<prefix><i>`, mirrors resolved inside the list. A board with a T in its six pieces is a
    placed board (`held` = the kind in hold); one without is a held board (`held` = "T")."""
    names = {k: f"{prefix}{i}" for i, k in enumerate(p["key"] for p in plan)}
    bd = []
    for i, p in enumerate(plan):
        k = p["key"]
        mk = mirror_board_key(k)
        kinds = {kk for kk, _ in k}
        held = [c for c in "IJLOSZ" if c not in kinds] if "T" in kinds else ["T"]
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
    return bd


def header(shapes, mirror_shapes, assumed, boards, prune):
    return {
        "schema": SCHEMA_V2,
        "report_eligible": False,
        "constructed": True,
        "quarantine": QUARANTINE,
        "md5": {"crate": crate_md5(), "tst_openers": md5(OLD.read_bytes()), "shapes": md5(canon(shapes).encode())},
        "budgets": BUDGETS,
        "prune": prune,
        "mirror": {"id_offset": ID_OFFSET, "suffix": SUFFIX, "assumed": assumed},
        "mirror_shapes": mirror_shapes,
        "boards": boards,
    }


def prune_of(placed, held):
    """placed / held: [boards_total, kept]."""
    return {"threshold": list(THRESH), "boards_total": placed[0] + held[0], "kept": placed[1] + held[1],
            "kinds": {"placed": list(placed), "held": list(held)}}


def mk_artefact(old, shapes, mirror_shapes, assumed, plan, results, prune_total):
    """plan: list of dict(key, ids, classes, built1); results: {bk: {i: {"ntil","cum"}}} by position i in plan."""
    return header(shapes, mirror_shapes, assumed, board_records(plan, results),
                  prune_of([prune_total, len(plan)], [0, 0]))


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
    assert art["schema"] in (SCHEMA_V2, SCHEMA), f"{path}: schema {art['schema']} (need {SCHEMA_V2} or {SCHEMA})"
    assert ("families" in art) == (art["schema"] == SCHEMA), f"{path}: families present iff schema {SCHEMA}"
    assert art["report_eligible"] is False and art["constructed"] is True
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
    nplaced = sum(1 for b in bs if b["held"] != "T")
    pk = art["prune"]["kinds"]
    assert pk["placed"][1] == nplaced and pk["held"][1] == len(bs) - nplaced, "prune.kinds kept counts"
    assert art["prune"]["boards_total"] == pk["placed"][0] + pk["held"][0]
    assert all(b["held"] != "T" for b in bs[:nplaced]) and all(b["held"] == "T" for b in bs[nplaced:]), "placed boards come first"
    seen_keys = set()
    th = Fraction(*THRESH)
    for i, b in enumerate(bs):
        is_held = b["held"] == "T"
        assert b["name"] == (f"h{i - nplaced}" if is_held else f"t{i}")
        key = board_key(b["pieces"])
        assert key not in seen_keys
        seen_keys.add(key)
        if is_held:
            assert sorted(k for k, _ in b["pieces"]) == sorted("IJLOSZ") and len(b["pieces"]) == 6
        else:
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
        ok = upper_bound(L, cat) > th
        if is_held and not ok and b["mirror"] is not None:
            o = names[b["mirror"]]
            ok = upper_bound(dict(zip(o["shapes"], o["built1"])), cat) > th
        assert ok, f"{b['name']}: upper bound under the threshold"
    if art["schema"] == SCHEMA:
        validate_families(art)
    return True


def validate_families(art):
    """The b1 artefact is current, the families recompute from it, and the sandwiches hold."""
    b1 = json.loads(B1_OUT.read_text())
    assert b1["schema"] == B1_SCHEMA
    assert b1["md5"]["boards"] == boards_md5(art["boards"]), "b1 artefact: boards changed"
    assert b1["md5"]["crate"] == b1_crate_md5(), "b1 artefact: crate sources changed"
    assert art["md5"]["b1"] == md5(canon(b1).encode()), "families: b1 artefact changed"
    fams = families_of(art, b1)
    assert fams == art["families"], "families differ from a recomputation"
    bs = {b["name"]: b for b in art["boards"]}
    for f in fams["list"]:
        assert len(f["variants"]) >= 2 and f["variants"] == sorted(f["variants"], key=lambda n: list(bs).index(n))
        for bk in BKEYS:
            js = [joint(bs[v]["cum"][bk], bs[v]["classes"]) for v in f["variants"]]
            bl = [built_of(bs[v]["cum"][bk]) for v in f["variants"]]
            jf, bf = Fraction(f["num"][bk][1], N2 * B), Fraction(f["num"][bk][0], N2)
            assert max(js) <= jf <= min(1, sum(js)), f"{f['variants']} {bk}: joint sandwich"
            assert bf <= min(1, sum(bl)), f"{f['variants']} {bk}: built bound"
            assert sum(f["pick"][bk]) <= B
            # `both`: the variants and their mirror boards; a superset of each hand's options, so at least either hand's joint
            bv = f["both"]["variants"]
            jb = Fraction(f["both"]["num"][bk][1], N2 * B)
            js2 = [joint(bs[v]["cum"][bk], bs[v]["classes"]) for v in bv]
            hands = [jf] + ([Fraction(fams["list"][f["mirror"]]["num"][bk][1], N2 * B)] if f["mirror"] is not None else [])
            assert max(hands) <= jb <= min(1, sum(js2)), f"{bv} {bk}: both sandwich"
            assert sum(f["both"]["pick"][bk]) <= B
    for p in fams["pairs"]:
        a, m = (bs[n] for n in p["boards"])
        assert a["mirror"] == m["name"] and m["mirror"] == a["name"]
        for bk in BKEYS:
            ja, jm = joint(a["cum"][bk], a["classes"]), joint(m["cum"][bk], m["classes"])
            jp = Fraction(p["num"][bk][1], N2 * B)
            assert max(ja, jm) <= jp <= min(1, ja + jm), f"{p['boards']} {bk}: pair sandwich"
            assert sum(p["pick"][bk]) <= B
    assert len(fams["pairs"]) * 2 == len(bs)
    return True


def cross_check_cmd(args):
    """The pinned counter's FCounter, run with MULTI=1 B1ONLY=1 SDB=n, counts 5040 x (orders of cost <= n) per board and class
    prefix: the b1 vectors agree with the counter on a sample of boards."""
    import os, random, subprocess
    art = json.loads(Path(args.out).read_text())
    b1 = json.loads(B1_OUT.read_text())
    vec = b1_vectors(b1)
    old, shapes = load_inputs()
    cat = Cat(old, shapes, art["mirror_shapes"])
    rnd = random.Random(5)
    placed = [b for b in art["boards"] if b["held"] != "T"]
    held = [b for b in art["boards"] if b["held"] == "T"]
    sel = rnd.sample(placed, 10) + rnd.sample(held, 6) + placed[:2]
    lines = []
    for b in sel:
        b1s = "/".join("%s:%s" % (k, ",".join(map(str, cs))) for k, cs in sorted(b["pieces"]))
        sh = "#".join(f"{pt(cat.by[s]['cells'])}|{pt(cat.by[s]['tst'])}" for s in b["shapes"])
        cl = ";".join(f"{si}:{l or '-'}" for si, l, _ in b["classes"])
        lines.append(f"{b['name']}#{b1s}#{sh}#{cl}")
    bad = 0
    for n in (0, 1, 2, None):
        env = dict(os.environ, MULTI="1", B1ONLY="1", JOBS="4")
        if n is not None:
            env["SDB"] = str(n)
        out = subprocess.run([args.cross_check], input="\n".join(lines) + "\n", capture_output=True, text=True, env=env, check=True).stdout
        got = {json.loads(l)["name"]: json.loads(l)["cum"] for l in out.splitlines()}
        for b in sel:
            v = vec[b["name"]]
            feas = int(((v < INFEAS) if n is None else (v <= n)).sum())
            if not got.get(b["name"]) or any(x != B * feas for x in got[b["name"]]):
                bad += 1
                print("MISMATCH", b["name"], n)
    print(f"cross-check: {len(sel)} boards x 4 budgets, mismatches {bad}")
    assert bad == 0


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


def merge_held(args):
    """Keep every placed board of --reuse-placed verbatim, append the held boards counted from the --h* outputs."""
    old, shapes = load_inputs()
    prev = json.loads(Path(args.reuse_placed).read_text())
    assert prev["schema"] in (SCHEMA_V1, SCHEMA_V2, SCHEMA), prev["schema"]
    assert prev["md5"]["crate"] == crate_md5() and prev["md5"]["tst_openers"] == md5(OLD.read_bytes()) \
        and prev["md5"]["shapes"] == md5(canon(shapes).encode()), "the reused artefact is stale"
    placed = [b for b in prev["boards"] if b["held"] != "T"]
    ms = prev["mirror_shapes"]
    cat = Cat(old, shapes, ms)
    boards = boards_from_last(Path(args.last_held).read_text().splitlines())
    keep, _ = kept_held(boards, cat)
    names = {f"h{i}": k for i, k in enumerate(keep)}
    res = {}
    for bk, path in (("0", args.hsd0), ("1", args.hsd1), ("2", args.hsd2), ("inf", args.hinf)):
        res[bk] = {}
        for r in read_jsonl(path):
            assert r["name"] in names and r.get("cum") is not None, f"{path}: bad record {r['name']}"
            i = int(r["name"][1:])
            assert i not in res[bk]
            res[bk][i] = r
        assert sorted(res[bk]) == list(range(len(keep))), f"{path}: does not cover the kept held boards"
    plan = []
    for k in keep:
        ids = sorted(boards[k])
        plan.append(dict(key=k, ids=ids, classes=board_classes(ids, cat), built1=boards[k]))
    hb = board_records(plan, res, "h")
    assert {board_key(b["pieces"]) for b in placed}.isdisjoint({board_key(b["pieces"]) for b in hb})
    pk = prev["prune"].get("kinds", {"placed": [prev["prune"]["boards_total"], prev["prune"]["kept"]]})
    art = header(shapes, ms, prev["mirror"]["assumed"], placed + hb, prune_of(pk["placed"], [len(boards), len(keep)]))
    validate(art, cat_given=cat)
    write_art(art, args.out)
    print(f"wrote {args.out}: {len(placed)} placed + {len(hb)} held boards (of {len(boards)} held candidates)", file=sys.stderr)


def compare_held(args):
    """FIXED_BOARDS order of every original shape's held boards (the --last-held output) against the committed
    analysis/tst-openers.json `fixed.cums[i][-1]`, which counted the same boards with the same engine."""
    old = json.loads(OLD.read_text())
    by = {o["id"]: o for o in old["shapes"]}
    n = bad = 0
    for l in Path(args.compare_held).read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        sid = int(r["name"][1:])
        if sid >= ID_OFFSET:
            continue
        f = by[sid]["fixed"]
        mine = [b["cum"][0] for b in r["b1"]]
        theirs = [c[-1] for c in f["cums"]]
        n += 1
        if mine != theirs:
            bad += 1
            print(f"shape {sid}: differs ({len(mine)} vs {len(theirs)} boards)")
    print(f"compared {n} original shapes, {bad} differ")
    assert n and not bad


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


# ---- hold-swap families (schema /4) ----------------------------------------------------------------------------------
import base64, zlib

INFEAS = 10          # the code of a '.' (no build from this order) in a decoded b1 vector


def b1_crate_md5():
    h = hashlib.md5()
    fs = [SIM / B1_CRATE / "Cargo.toml"] + list((SIM / B1_CRATE / "src").rglob("*.rs")) + list((SIM / "oracle-rs" / "src").rglob("*.rs"))
    for p in sorted(fs, key=lambda p: p.relative_to(SIM).as_posix()):
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


def boards_md5(boards):
    return md5(canon([[b["name"], b["pieces"]] for b in boards]).encode())


def b1_input_lines(art):
    return ["%s#%s" % (b["name"], "/".join("%s:%s" % (k, ",".join(map(str, cs))) for k, cs in b["pieces"]))
            for b in art["boards"]]


def b1_build(art, jsonl):
    """The b1 artefact from the crate's output lines (`{"name","v"}` per board)."""
    vec = {}
    for r in read_jsonl(jsonl):
        assert r["name"] not in vec and len(r["v"]) == B and set(r["v"]) <= set(".0123456789"), r["name"]
        vec[r["name"]] = r["v"]
    assert sorted(vec) == sorted(b["name"] for b in art["boards"]), "the crate output does not cover the boards"
    return {"schema": B1_SCHEMA, "report_eligible": False, "constructed": True,
            "means": "per board and first-bag dealt order (the counter's IOTSZJL recursion order), the least soft-drop cost "
                     "min(s, 9) of building the board from that order with one hold slot, '.' when none; zlib + base64",
            "md5": {"crate": b1_crate_md5(), "boards": boards_md5(art["boards"])},
            "vectors": {n: base64.b64encode(zlib.compress(v.encode(), 9)).decode() for n, v in sorted(vec.items())}}


def b1_vectors(b1):
    import numpy as np
    out = {}
    for n, z in b1["vectors"].items():
        v = zlib.decompress(base64.b64decode(z)).decode()
        assert len(v) == B
        out[n] = np.frombuffer(v.replace(".", chr(48 + INFEAS)).encode(), dtype=np.uint8) - 48
    return out


def solve_D(cum, vec):
    """D by the triangular solve cum_b[k] = sum_s n_s D_k(b - s), n_s the number of first-bag orders with cost s.
    Every division is asserted exact: that IS the proof that a board's count for one order depends only on (board, order).
    Returns (Dfin, Dinf): Dfin[r] the class-cumulative bag-2 counts with r budget left (r = 0..2-smin), Dinf the same unlimited."""
    import numpy as np
    n = np.bincount(vec, minlength=INFEAS + 1)
    nfeas = int(n[:INFEAS].sum())
    ncls = len(cum["inf"])
    assert nfeas > 0
    Dinf = []
    for c in cum["inf"]:
        assert c % nfeas == 0, "inf: cum not divisible by the feasible order count"
        Dinf.append(c // nfeas)
    smin = int(np.nonzero(n[:INFEAS])[0][0])
    Dfin = {}
    for b in (0, 1, 2):
        c = cum[str(b)]
        if b < smin:
            assert all(x == 0 for x in c), f"budget {b} below the least cost {smin} but cum is not 0"
            continue
        row = []
        for k in range(ncls):
            num = c[k] - sum(int(n[s]) * Dfin[b - s][k] for s in range(smin + 1, b + 1))
            assert num % int(n[smin]) == 0, f"b={b} k={k}: inexact division"
            row.append(num // int(n[smin]))
        Dfin[b - smin] = row
    for r, row in Dfin.items():
        assert all(0 <= x <= B for x in row) and all(x <= y for x, y in zip(row, row[1:])), "D range / monotone in k"
        assert all(x <= y for x, y in zip(row, Dinf)), "D finite above D inf"
        if r + 1 in Dfin:
            assert all(x <= y for x, y in zip(row, Dfin[r + 1])), "D not monotone in r"
    return Dfin, Dinf


def j_tables(board, D):
    """Per budget key, (J, built) over the cost code s (0..INFEAS), numpy int64; J_v(r) = sum_k dD_k p5_k, built = D_last(r)."""
    import numpy as np
    Dfin, Dinf = D
    p5 = [c[2] for c in board["classes"]]

    def jb(row):
        prev, j = 0, 0
        for d, p in zip(row, p5):
            j += (d - prev) * p
            prev = d
        return j, row[-1]
    out = {}
    for bk, b in (("0", 0), ("1", 1), ("2", 2), ("inf", None)):
        J = np.zeros(INFEAS + 1, dtype=np.int64)
        Bt = np.zeros(INFEAS + 1, dtype=np.int64)
        for s in range(INFEAS):
            if b is None:
                J[s], Bt[s] = jb(Dinf)
            elif b - s >= 0 and (b - s) in Dfin:
                J[s], Bt[s] = jb(Dfin[b - s])
        out[bk] = (J, Bt)
    return out


def layouts_of(art):
    """{layout (frozenset of 7 (kind, cells)): sorted board indices of the kept boards equal to the layout minus one piece}:
    every set of seven placements, one per kind on 28 disjoint cells, with at least two such kept boards."""
    bs = art["boards"]
    by_key = {board_key(b["pieces"]): i for i, b in enumerate(bs)}
    cores = {}
    for i, b in enumerate(bs):
        ps = [(k, tuple(sorted(cs))) for k, cs in b["pieces"]]
        for j, p in enumerate(ps):
            cores.setdefault(frozenset(ps[:j] + ps[j + 1:]), []).append((i, p))
    lay = set()
    for core, lst in cores.items():
        for a in range(len(lst)):
            for c in range(a + 1, len(lst)):
                pa, pc = lst[a][1], lst[c][1]
                if pa[0] == pc[0]:
                    continue
                cells = [x for _, cs in core for x in cs] + list(pa[1]) + list(pc[1])
                if len(set(cells)) != 28:
                    continue
                lay.add(frozenset(core | {pa, pc}))
    out = {}
    for L in lay:
        vs = sorted(by_key[tuple(sorted(L - {p}))] for p in L if tuple(sorted(L - {p})) in by_key)
        assert len(vs) >= 2
        out[L] = vs
    return out


def families_of(art, b1):
    """The families object (schema /4) recomputed from the boards and the b1 vectors: per layout its variants' figures under
    the policy, and `both`, the same policy over the variants and their mirror boards (each first-bag order picks the better
    hand); `pairs`, the policy over each board and its mirror board."""
    import numpy as np
    bs = art["boards"]
    pos = {b["name"]: i for i, b in enumerate(bs)}
    vec = b1_vectors(b1)
    tabs = {}
    for b in bs:
        tabs[b["name"]] = j_tables(b, solve_D(b["cum"], vec[b["name"]]))
        for bk in BKEYS:       # a one-board family reproduces the board's own figures: the policy identity
            J, Bt = tabs[b["name"]][bk]
            v = vec[b["name"]]
            assert int(Bt[v].sum()) == b["cum"][bk][-1], f"{b['name']} {bk}: built identity"
            assert int(J[v].sum()) == joint(b["cum"][bk], b["classes"]) * N2 * B, f"{b['name']} {bk}: pc3 identity"
    cols = np.arange(B)

    def policy(nm):
        num, pick = {}, {}
        for bk in BKEYS:
            Js = np.stack([tabs[n][bk][0][vec[n]] for n in nm])
            Bs = np.stack([tabs[n][bk][1][vec[n]] for n in nm])
            av = np.stack([(vec[n] < INFEAS) if bk == "inf" else (vec[n] <= int(bk)) for n in nm])
            arg = np.where(av, Js * 8192 + Bs, -1).argmax(axis=0)
            anyav = av.any(axis=0)
            num[bk] = [int(Bs[arg, cols][anyav].sum()), int(Js[arg, cols][anyav].sum())]
            pick[bk] = [int(((arg == t) & anyav).sum()) for t in range(len(nm))]
        return num, pick
    lays = layouts_of(art)
    keys = sorted(lays, key=lambda L: sorted(L))
    index = {L: i for i, L in enumerate(keys)}
    fams = []
    for L in keys:
        nm = [bs[i]["name"] for i in lays[L]]
        num, pick = policy(nm)
        both = sorted(set(nm) | {bs[pos[n]]["mirror"] for n in nm}, key=pos.get)
        bnum, bpick = policy(both)
        ml = frozenset((p[0], tuple(p[1])) for p in mirror_pieces([[k, list(cs)] for k, cs in L]))
        mi = index.get(ml)
        if mi is not None:
            assert set(both) == set(nm) | {bs[i]["name"] for i in lays[keys[mi]]}, "mirror family variants are the mirrors"
        fams.append({"pieces": [[k, list(cs)] for k, cs in sorted(L)], "variants": nm,
                     "mirror": mi, "num": num, "pick": pick,
                     "both": {"variants": both, "num": bnum, "pick": bpick}})
    prs = []
    for b in bs:
        if pos[b["name"]] < pos[b["mirror"]]:
            num, pick = policy([b["name"], b["mirror"]])
            prs.append({"boards": [b["name"], b["mirror"]], "num": num, "pick": pick})
    return {"complete": all(len(f["variants"]) == 7 for f in fams),
            "policy": "per first-bag order, the variant with the larger joint, then built, then the earlier board, at that budget",
            "list": fams, "pairs": prs}


def families_cmd(args):
    art = json.loads(Path(args.out).read_text())
    old_boards = canon(art["boards"])
    b1 = json.loads(B1_OUT.read_text())
    assert b1["md5"]["boards"] == boards_md5(art["boards"]) and b1["md5"]["crate"] == b1_crate_md5(), "b1 artefact is stale"
    fams = families_of(art, b1)
    art["schema"] = SCHEMA
    art["md5"]["b1"] = md5(canon(b1).encode())
    art["families"] = fams
    assert canon(art["boards"]) == old_boards
    validate(art)
    write_art(art, args.out)
    print(f"wrote {args.out}: {len(fams['list'])} families, complete={fams['complete']}", file=sys.stderr)


def check_cmd(args):
    art = json.loads(Path(args.out).read_text())
    validate(art)
    print(f"ok: {len(art['boards'])} boards, {len(art['families']['list'])} families recomputed from the b1 vectors")


def b1_cmd(args):
    art = json.loads(Path(args.out).read_text())
    if args.b1_input:
        print("\n".join(b1_input_lines(art)))
        return
    b1 = b1_build(art, args.b1_merge)
    B1_OUT.write_text(json.dumps(b1, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"wrote {B1_OUT}: {len(b1['vectors'])} vectors", file=sys.stderr)


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
    ap.add_argument("--mirror-art", action="store_true")
    ap.add_argument("--held", action="store_true")
    ap.add_argument("--last-held")
    ap.add_argument("--reuse-placed")
    ap.add_argument("--hsd0")
    ap.add_argument("--hsd1")
    ap.add_argument("--hsd2")
    ap.add_argument("--hinf")
    ap.add_argument("--compare-held")
    ap.add_argument("--b1-input", action="store_true")
    ap.add_argument("--b1-merge")
    ap.add_argument("--families", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--cross-check")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    if a.b1_input or a.b1_merge:
        return b1_cmd(a)
    if a.families:
        return families_cmd(a)
    if a.check:
        return check_cmd(a)
    if a.cross_check:
        return cross_check_cmd(a)
    if a.validate is not None:
        return validate_cmd(a)
    if a.compare_held:
        return compare_held(a)
    if a.merge and a.reuse_placed:
        return merge_held(a)
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
    if a.mirror_art and not a.mirror_out:
        ms = json.loads(OUT.read_text())["mirror_shapes"]
    else:
        ms = build_mirror_shapes(old, shapes, Path(a.mirror_out).read_text().splitlines() if a.mirror_out else None)
    cat = Cat(old, shapes, ms)
    if a.tpl_input:
        print("\n".join(tpl_input_lines(cat)))
        return
    if a.multi_input and a.held:
        boards = boards_from_last(Path(a.last_held).read_text().splitlines())
        keep, _ = kept_held(boards, cat)
        print("\n".join(multi_lines(keep, boards, cat, "h")))
        print(f"{len(boards)} held boards, {len(keep)} kept", file=sys.stderr)
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
