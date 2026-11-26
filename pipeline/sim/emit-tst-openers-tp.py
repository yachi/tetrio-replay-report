#!/usr/bin/env python3
"""Emit analysis/tst-openers-tp.json: the T-placed bag-1 ranking (constructed, quarantined).

The counter is `pipeline/sim/tst2bag-tp-rs` (binary `tst2bag-tp`; a sibling of `tst2bag-rs`, which is left untouched so
`analysis/tst-openers.json` and its pins stay current). A bag-1 board here is six pieces in one of two kinds: PLACED
(the T placed, four more of IJLOSZ placed, the sixth kind held; names t<i>) or HELD (the six pieces IJLOSZ placed and the T in
hold, `held == "T"`; names h<i>, listed after every placed board). Both kinds are counted by the same method and ranked together. The ranking counts, for each board, the 5040^2 dealt orders of bags 1 and 2 that
finish on ANY of the 246 shapes (127 transcribed + 119 mirrors) holding that board, and the bag-3 Perfect Clear chance
of the leftover (`p5`, out of 5040). Everything below is offline (about 1.5 h on 4 cores) and never runs in CI;
`tst-openers-tp.test.ts` re-runs a pinned cheap subset and checks the artefact's invariants.

  B=pipeline/sim/tst2bag-tp-rs/target/release/tst2bag-tp ; E=pipeline/sim/emit-tst-openers-tp.py ; W=/tmp/tp3

  O1  python3 $E --shape-input > $W/mirror.in                                   # s<1000+id>|cells|tst, the 119 mirror shapes
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

FAMILIES (schema tst-openers-tp/5; the hold-swap figure of docs/tst-openers.html). A LAYOUT is a set of seven placements, one of
each of IJLOSTZ, on 28 distinct cells; its VARIANTS are the kept boards that are the layout minus one piece (the piece left out is
the one held: minus the T is a T-held board). A family is a layout with at least one KEPT variant and at least two variants,
counting the candidate boards the prune dropped (the x boards, below). With the five-piece
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
  F3  a variant pruned from the ranking (upper bound <= 36%) is still counted: every candidate board of the counter's
      enumeration that is a listed layout less one piece is an x board in `analysis/tst-openers-tp-x.json`, with its own cum
      (built by F1 forwards from tst-d's D and its own first-bag vector), so `families.complete` is true. Cards and ranks stay
      per mirror pair by the board's own joint; an x board has no card and no rank.
  F4  `both` (per family) runs the F2 policy over the variants AND their mirror boards, so each o1 picks the better hand too;
      `pairs` runs it over each board and its mirror board. Each is a superset of either hand's options, so its joint is at least
      either hand's (`validate_families` checks that sandwich).

  B1  python3 $E --b1-input > $W/b1.in ; pipeline/sim/tst-b1vec-rs/target/release/tst-b1vec < $W/b1.in > $W/b1.out     # about 40 s
      python3 $E --b1-merge $W/b1.out                                          # writes analysis/tst-openers-tp-b1.json
  B2  python3 $E --families                                                    # adds `families` to analysis/tst-openers-tp.json (boards untouched)
  B3  python3 $E --check                                                       # CI: the b1 artefact is what the crate gives, the families recompute
      python3 $E --cross-check <tst2bag-tp binary>                             # MULTI=1 B1ONLY=1 SDB=n against the vectors, on sampled boards
  S1  python3 $E --sets                                                        # writes analysis/tst-openers-tp-sets.json via pipeline/sim/tst-sets-rs (about 5 s)
  T1  python3 $E --tsd-input > $W/tsd.in ; pipeline/sim/tst-tsd-rs/target/release/tst-tsd < $W/tsd.in > $W/tsd.out   # offline, about 30 min on 4 cores
      python3 $E --tsd $W/tsd.out ; python3 $E --tsd-check                   # writes / checks analysis/tst-openers-tp-tsd.json (TST->TSD->PC, bag 3 only)
  S2  python3 $E --sets-check                                                  # CI: byte-compares a fresh crate run, recomputes every set, pick and tree in numpy (about 30 s)

THE X BOARDS (schema tst-openers-tp-x/1, md5 in the main artefact's md5.x; offline, about 25 min on 4 cores):

  X1  FIXED=1 FIXED_BOARDS=1 TPL=1 JOBS=4 $B < $W/tpl.in > $W/T.out ; FIXED=1 FIXED_BOARDS=1 JOBS=4 $B < $W/tpl.in > $W/H.out
      python3 $E --cand-merge $W/T.out $W/H.out --cand-out $W/cand.json        # every candidate board's shape list (totals = prune.kinds)
  X2  python3 $E --x-input --cand $W/cand.json > $W/x.in                        # one MULTI line per x board of a listed layout
      python3 $E --x-input --kept > $W/kept.in                                  # the same lines for the kept boards
  X3  D=pipeline/sim/tst-d-rs/target/release/tst-d ; JOBS=4 $D < $W/kept.in > $W/kept.out ; python3 $E --x-verify $W/kept.out
                                                                                # HARD GATE: F1 from tst-d's D == committed cum, every kept board
  X4  JOBS=4 $D < $W/x.in > $W/x.out ; tst-b1vec over the x boards' b1 lines > $W/xb1.out
      python3 $E --x-merge $W/x.out $W/xb1.out --cand $W/cand.json             # writes analysis/tst-openers-tp-x.json
  X5  python3 $E --families ; python3 $E --x-compare ; python3 $E --check      # x-compare: no family figure fell against the kept-only run

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
import argparse, collections, hashlib, json, sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "pipeline" / "sim"
SHAPES = ROOT / "pipeline" / "openers" / "tst-openers-shapes.json"
OLD = ROOT / "analysis" / "tst-openers.json"
OUT = ROOT / "analysis" / "tst-openers-tp.json"
CRATES = ["tst2bag-tp-rs", "oracle-rs", "pc-solver-rs"]
SCHEMA = "tst-openers-tp/5"
SCHEMA_V4 = "tst-openers-tp/4"
SCHEMA_V2 = "tst-openers-tp/2"
SCHEMA_V1 = "tst-openers-tp/1"
B1_SCHEMA = "tst-openers-tp-b1/1"
B1_OUT = ROOT / "analysis" / "tst-openers-tp-b1.json"
B1_CRATE = "tst-b1vec-rs"
X_SCHEMA = "tst-openers-tp-x/1"
X_OUT = ROOT / "analysis" / "tst-openers-tp-x.json"
D_CRATE = "tst-d-rs"
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


def multi_line(name, k, ids, cat):
    ids = sorted(ids)
    b1 = "/".join(f"{kind}:{','.join(map(str, cs))}" for kind, cs in k)
    sh = "#".join(f"{pt(cat.by[sid]['cells'])}|{pt(cat.by[sid]['tst'])}" for sid in ids)
    cl = ";".join(f"{si}:{l or '-'}" for si, l, _ in board_classes(ids, cat))
    return f"{name}#{b1}#{sh}#{cl}"


def multi_lines(keep, boards, cat, prefix="t"):
    return [multi_line(f"{prefix}{i}", k, boards[k], cat) for i, k in enumerate(keep)]


# ---- candidates (every enumerated board, kept or pruned) and the closure over layouts ---------------------------------
def boards_from_list(lines):
    """board key -> {shape id: 0} from a FIXED_BOARDS output (no counts: cum is empty)."""
    out = {}
    for l in lines:
        if not l.strip():
            continue
        r = json.loads(l)
        sid = int(r["name"][1:])
        for b in r["b1"]:
            k = board_key(b["pieces"])
            assert sid not in out.setdefault(k, {}), "board listed twice for a shape"
            out[k][sid] = 0
    return out


def cand_merge_cmd(args):
    art = json.loads(OUT.read_text())
    T = boards_from_list(Path(args.cand_merge[0]).read_text().splitlines())
    H = boards_from_list(Path(args.cand_merge[1]).read_text().splitlines())
    tot = art["prune"]["kinds"]
    assert all("T" in {k for k, _ in key} for key in T) and not any("T" in {k for k, _ in key} for key in H)
    assert [len(T), len(H)] == [tot["placed"][0], tot["held"][0]], (len(T), len(H), tot)
    cand = {**T, **H}
    for b in art["boards"]:
        k = board_key(b["pieces"])
        assert sorted(cand[k]) == b["shapes"], b["name"]
    rows = [{"pieces": [[kk, list(cs)] for kk, cs in k], "shapes": sorted(L)} for k, L in sorted(cand.items())]
    Path(args.cand_out).write_text(json.dumps(rows))
    print(f"ok: {len(T)} placed, {len(H)} held candidates; all {len(art['boards'])} kept boards agree on their shape lists")


def load_cand(path):
    return {board_key(r["pieces"]): r["shapes"] for r in json.loads(Path(path).read_text())}


def closure(art, cand):
    """(layouts, xkeys): layouts (7 placements on 28 cells) having at least one kept variant, and the sorted candidate
    boards that are variants of those layouts and not kept."""
    kept = {board_key(b["pieces"]) for b in art["boards"]}
    cores = {}
    for k in cand:
        for j in range(len(k)):
            cores.setdefault(k[:j] + k[j + 1:], []).append(k[j])
    lay = set()
    for k in kept:
        for j in range(len(k)):
            core = k[:j] + k[j + 1:]
            for p in cores[core]:
                if p[0] == k[j][0]:
                    continue
                cells = [x for _, cs in core for x in cs] + list(k[j][1]) + list(p[1])
                if len(set(cells)) == 28:
                    lay.add(frozenset(core + (k[j], p)))
    xk = set()
    for L in lay:
        for p in L:
            v = tuple(sorted(L - {p}))
            if v in cand and v not in kept:
                xk.add(v)
    return lay, sorted(xk)


def x_cmd(args):
    art = json.loads(OUT.read_text())
    old, shapes = load_inputs()
    cat = Cat(old, shapes, art["mirror_shapes"])
    if args.kept:
        print("\n".join(multi_line(b["name"], board_key(b["pieces"]), b["shapes"], cat) for b in art["boards"]))
        return
    cand = load_cand(args.cand)
    lay, xk = closure(art, cand)
    print("\n".join(multi_line(f"x{i}", k, cand[k], cat) for i, k in enumerate(xk)))
    nt = sum(1 for k in xk if any(kk == "T" for kk, _ in k))
    nomir = sum(1 for k in cand if mirror_board_key(k) not in cand)
    xnomir = sum(1 for k in xk if mirror_board_key(k) not in cand)
    print(f"layouts {len(lay)}; extra boards {len(xk)} (placed {nt}, held {len(xk) - nt}); candidates with no candidate mirror: "
          f"{nomir} of {len(cand)}, among the extra boards {xnomir}", file=sys.stderr)


# ---- the extra boards: every candidate variant of a family layout that the prune left out -------------------------------
def d_crate_md5():
    h = hashlib.md5()
    fs = [SIM / D_CRATE / "Cargo.toml"] + list((SIM / D_CRATE / "src").rglob("*.rs")) + list((SIM / "oracle-rs" / "src").rglob("*.rs"))
    for p in sorted(fs, key=lambda p: p.relative_to(SIM).as_posix()):
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


def cum_from_D(D, vec):
    """F1 forwards: cum_b[k] = sum_s n_s D[b - s][k] (b = 0..2), cum_inf[k] = n_feasible D[3][k]."""
    n = [0] * (INFEAS + 1)
    for c in vec:
        n[c] += 1
    nfeas = sum(n[:INFEAS])
    out = {}
    for b in (0, 1, 2):
        out[str(b)] = [sum(n[s] * D[b - s][k] for s in range(b + 1)) for k in range(len(D[0]))]
    out["inf"] = [nfeas * d for d in D[3]]
    return out


def x_merge_cmd(args):
    """analysis/tst-openers-tp-x.json from tst-d's output over the x lines and tst-b1vec's over the same boards."""
    art = json.loads(OUT.read_text())
    old, shapes = load_inputs()
    cat = Cat(old, shapes, art["mirror_shapes"])
    cand = load_cand(args.cand)
    lay, xk = closure(art, cand)
    names = {k: f"x{i}" for i, k in enumerate(xk)}
    kept = {board_key(b["pieces"]): b["name"] for b in art["boards"]}
    D = {r["name"]: r for r in read_jsonl(args.x_merge[0])}
    V = {}
    for r in read_jsonl(args.x_merge[1]):
        assert r["name"] not in V and len(r["v"]) == B and set(r["v"]) <= set(".0123456789"), r["name"]
        V[r["name"]] = r["v"]
    assert sorted(D) == sorted(V) == sorted(names.values()), "the crate outputs do not cover the extra boards"
    boards = []
    for k in xk:
        nm = names[k]
        ids = cand[k]
        r = D[nm]
        assert r["D"] is not None, f"{nm}: no tiling holds a candidate board"
        cls = board_classes(ids, cat)
        assert all(len(row) == len(cls) for row in r["D"]) and len(r["D"]) == 4
        vec = bytes(ord(ch) - 48 for ch in V[nm].replace(".", chr(48 + INFEAS)))
        mk = mirror_board_key(k)
        mir = names.get(mk) or kept.get(mk)
        assert mir is not None, f"{nm}: its mirror is neither kept nor extra"
        kinds = {kk for kk, _ in k}
        held = [c for c in "IJLOSZ" if c not in kinds] if "T" in kinds else ["T"]
        boards.append({"name": nm, "pieces": [[kk, list(cs)] for kk, cs in k], "held": held[0], "mirror": mir,
                       "shapes": list(ids), "classes": [[si, l, v] for si, l, v in cls], "ntil": r["ntil"],
                       "cum": cum_from_D(r["D"], vec)})
    nt = sum(1 for k in cand if any(kk == "T" for kk, _ in k))
    x = {"schema": X_SCHEMA, "report_eligible": False, "constructed": True,
         "means": "every candidate bag-1 board (enumerated, upper bound at or under the threshold) that is a variant of a family "
                  "layout with a kept variant: its cum per budget from tst-d's bag-2 counts D and its own first-bag vector (F1), and "
                  "that vector (per first-bag order the least soft-drop cost min(s, 9), '.' when none; zlib + base64)",
         "md5": {"crate": d_crate_md5(), "b1crate": b1_crate_md5(), "boards": boards_md5(art["boards"]),
                 "tst_openers": md5(OLD.read_bytes()), "shapes": md5(canon(shapes).encode())},
         "candidates": {"placed": nt, "held": len(cand) - nt},
         "layouts": len(lay),
         "boards": boards,
         "vectors": {n: base64.b64encode(zlib.compress(v.encode(), 9)).decode() for n, v in sorted(V.items())}}
    for b in boards:     # the forward F1 solves back: the same exactness the kept boards are held to
        if any(c != "." for c in V[b["name"]]):
            solve_D(b["cum"], bytes(ord(ch) - 48 for ch in V[b["name"]].replace(".", chr(48 + INFEAS))))
    X_OUT.write_text(json.dumps(x, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"wrote {X_OUT}: {len(boards)} extra boards over {len(lay)} layouts", file=sys.stderr)


def x_verify_cmd(args):
    """Hard gate before trusting tst-d: on the kept boards, F1 forwards from tst-d's D and the committed b1 vectors gives
    the committed cum and ntil, exactly."""
    art = json.loads(OUT.read_text())
    vec = b1_vectors(json.loads(B1_OUT.read_text()))
    got = {r["name"]: r for r in read_jsonl(args.x_verify)}
    bad = 0
    for b in art["boards"]:
        r = got[b["name"]]
        if r["D"] is None or r["ntil"] != b["ntil"] or cum_from_D(r["D"], vec[b["name"]]) != b["cum"]:
            bad += 1
            print("MISMATCH", b["name"])
    print(f"x-verify: {len(art['boards'])} kept boards, mismatches {bad}")
    assert bad == 0


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
    x = load_x(art)
    assert art["md5"]["x"] == md5(canon(x).encode()), "families: x artefact changed"
    fams = families_of(art, b1, x)
    assert fams == art["families"], "families differ from a recomputation"
    assert fams["complete"] is True
    bs = {b["name"]: b for b in art["boards"] + x["boards"]}
    order = {n: i for i, n in enumerate(bs)}
    for f in fams["list"]:
        assert len(f["variants"]) >= 2 and f["variants"] == sorted(f["variants"], key=order.get)
        assert f["variants"][0] in order and order[f["variants"][0]] < len(art["boards"]), "a family with no kept variant"
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
    assert len(fams["pairs"]) * 2 == len(art["boards"])  # pairs are kept boards only
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
    """{board: bytes of B cost codes 0..INFEAS} (stdlib only: CI installs no numpy)."""
    out = {}
    for n, z in b1["vectors"].items():
        v = zlib.decompress(base64.b64decode(z)).decode()
        assert len(v) == B
        out[n] = bytes(ord(ch) - 48 for ch in v.replace(".", chr(48 + INFEAS)))
    return out


def solve_D(cum, vec):
    """D by the triangular solve cum_b[k] = sum_s n_s D_k(b - s), n_s the number of first-bag orders with cost s.
    Every division is asserted exact: that IS the proof that a board's count for one order depends only on (board, order).
    Returns (Dfin, Dinf): Dfin[r] the class-cumulative bag-2 counts with r budget left (r = 0..2-smin), Dinf the same unlimited."""
    n = [0] * (INFEAS + 1)
    for c in vec:
        n[c] += 1
    nfeas = sum(n[:INFEAS])
    ncls = len(cum["inf"])
    assert nfeas > 0
    Dinf = []
    for c in cum["inf"]:
        assert c % nfeas == 0, "inf: cum not divisible by the feasible order count"
        Dinf.append(c // nfeas)
    smin = next(s for s in range(INFEAS) if n[s])
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


def j_tables(board, D, p=None):
    """Per budget key, (J, built) over the cost code s (0..INFEAS), lists of ints; J_v(r) = sum_k dD_k p_k, built = D_last(r).
    p defaults to the classes' own p5 (a bag-3 PC of any kind); the TST->TSD->PC objective passes the classes' pt3."""
    Dfin, Dinf = D
    p5 = [c[2] for c in board["classes"]] if p is None else p

    def jb(row):
        prev, j = 0, 0
        for d, p in zip(row, p5):
            j += (d - prev) * p
            prev = d
        return j, row[-1]
    out = {}
    for bk, b in (("0", 0), ("1", 1), ("2", 2), ("inf", None)):
        J = [0] * (INFEAS + 1)
        Bt = [0] * (INFEAS + 1)
        for s in range(INFEAS):
            if b is None:
                J[s], Bt[s] = jb(Dinf)
            elif b - s >= 0 and (b - s) in Dfin:
                J[s], Bt[s] = jb(Dfin[b - s])
        out[bk] = (J, Bt)
    return out


def layouts_of(bs, nkept):
    """{layout (frozenset of 7 (kind, cells)): sorted indices into `bs` of the boards equal to the layout minus one piece}:
    every set of seven placements, one per kind on 28 disjoint cells, with at least two such boards of which at least one is
    among the first `nkept` (the kept boards; the rest are the extra boards)."""
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
        if vs[0] < nkept:
            out[L] = vs
    return out


def families_of(art, b1, x=None):
    """The families object recomputed from the boards, the b1 vectors and (schema /5) the extra boards with their own vectors:
    per layout its variants' figures under the policy, and `both`, the same policy over the variants and their mirror boards
    (each first-bag order picks the better hand); `pairs`, the policy over each kept board and its mirror board. With `x` every
    candidate variant of every layout is present (`complete`); without it a family holds its kept variants only."""
    kept = art["boards"]
    bs = kept + (x["boards"] if x else [])
    pos = {b["name"]: i for i, b in enumerate(bs)}
    vec = b1_vectors(b1)
    if x:
        vec.update(b1_vectors(x))
    tabs = {}
    for b in bs:
        if all(c == INFEAS for c in vec[b["name"]]):      # an extra board no first-bag order builds: it adds nothing
            assert all(v == 0 for bk in BKEYS for v in b["cum"][bk]), b["name"]
            tabs[b["name"]] = {bk: ([0] * (INFEAS + 1), [0] * (INFEAS + 1)) for bk in BKEYS}
            continue
        tabs[b["name"]] = j_tables(b, solve_D(b["cum"], vec[b["name"]]))
        for bk in BKEYS:       # a one-board family reproduces the board's own figures: the policy identity
            J, Bt = tabs[b["name"]][bk]
            v = vec[b["name"]]
            cnt = [0] * (INFEAS + 1)
            for c in v:
                cnt[c] += 1
            assert sum(cnt[s] * Bt[s] for s in range(INFEAS + 1)) == b["cum"][bk][-1], f"{b['name']} {bk}: built identity"
            assert sum(cnt[s] * J[s] for s in range(INFEAS + 1)) == joint(b["cum"][bk], b["classes"]) * N2 * B, \
                f"{b['name']} {bk}: pc3 identity"

    def policy(nm):
        """Per budget, each first-bag order picks the available variant with the largest J*8192 + built (ties to the
        earlier one); an order no variant can build adds nothing. Stdlib only: CI installs no numpy."""
        num, pick = {}, {}
        vs = [vec[n] for n in nm]
        cnt = collections.Counter(zip(*vs))  # identical first-bag-order columns pick identically
        for bk in BKEYS:
            lim = INFEAS - 1 if bk == "inf" else int(bk)
            keys = [[(tabs[n][bk][0][s] * 8192 + tabs[n][bk][1][s]) if s <= lim else -1 for s in range(INFEAS + 1)]
                    for n in nm]
            Jt = [tabs[n][bk][0] for n in nm]
            Bt = [tabs[n][bk][1] for n in nm]
            tb = tj = 0
            pk = [0] * len(nm)
            for cols, w in cnt.items():
                best, arg = -1, -1
                for t, c in enumerate(cols):
                    k = keys[t][c]
                    if k > best:
                        best, arg = k, t
                if arg < 0:
                    continue
                c = cols[arg]
                tb += w * Bt[arg][c]
                tj += w * Jt[arg][c]
                pk[arg] += w
            num[bk] = [tb, tj]
            pick[bk] = pk
        return num, pick
    lays = layouts_of(bs, len(kept))
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
    for b in kept:
        if pos[b["name"]] < pos[b["mirror"]]:
            num, pick = policy([b["name"], b["mirror"]])
            prs.append({"boards": [b["name"], b["mirror"]], "num": num, "pick": pick})
    return {"complete": x is not None,
            "policy": "per first-bag order, the variant with the larger joint, then built, then the earlier board, at that budget",
            "list": fams, "pairs": prs}


def load_x(art):
    """The extra-board artefact, checked current against the kept boards and the two crates."""
    x = json.loads(X_OUT.read_text())
    assert x["schema"] == X_SCHEMA and x["report_eligible"] is False and x["constructed"] is True
    assert x["md5"]["boards"] == boards_md5(art["boards"]), "x artefact: kept boards changed"
    assert x["md5"]["crate"] == d_crate_md5(), "x artefact: tst-d crate sources changed"
    assert x["md5"]["b1crate"] == b1_crate_md5(), "x artefact: tst-b1vec crate sources changed"
    assert x["md5"]["tst_openers"] == md5(OLD.read_bytes()) and x["md5"]["shapes"] == md5(canon(load_inputs()[1]).encode())
    assert sorted(x["vectors"]) == sorted(b["name"] for b in x["boards"])
    kept = {b["name"] for b in art["boards"]}
    names = {b["name"] for b in x["boards"]}
    for b in x["boards"]:
        assert b["mirror"] in kept or b["mirror"] in names, b["name"]
    return x


def x_compare_cmd(args):
    """One-off: every family's joint and both-joint with the extra boards is at least the kept-only figure (a superset of
    options), and how many families moved."""
    art = json.loads(Path(args.out).read_text())
    b1 = json.loads(B1_OUT.read_text())
    a = families_of(art, b1)
    c = families_of(art, b1, load_x(art))
    old = {canon(f["pieces"]): f for f in a["list"]}
    moved = new = 0
    for f in c["list"]:
        o = old.get(canon(f["pieces"]))
        if o is None:
            new += 1
            continue
        for bk in BKEYS:
            assert f["num"][bk][1] >= o["num"][bk][1] and f["both"]["num"][bk][1] >= o["both"]["num"][bk][1], f["variants"]
        moved += f["num"] != o["num"] or f["both"]["num"] != o["both"]["num"]
    assert set(old) <= {canon(f["pieces"]) for f in c["list"]}
    print(f"x-compare: {len(a['list'])} kept-only families, {len(c['list'])} complete ({new} new), {moved} moved; none fell")


def families_cmd(args):
    art = json.loads(Path(args.out).read_text())
    old_boards = canon(art["boards"])
    b1 = json.loads(B1_OUT.read_text())
    assert b1["md5"]["boards"] == boards_md5(art["boards"]) and b1["md5"]["crate"] == b1_crate_md5(), "b1 artefact is stale"
    x = load_x(art)
    fams = families_of(art, b1, x)
    art["schema"] = SCHEMA
    art["md5"]["b1"] = md5(canon(b1).encode())
    art["md5"]["x"] = md5(canon(x).encode())
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


# ---- learn-these-boards sets (tst-openers-tp-sets/1) ----------------------------------------------------------------------
import subprocess

TSD_SCHEMA = "tst-openers-tp-tsd/1"
TSD_OUT = ROOT / "analysis" / "tst-openers-tp-tsd.json"
TSD_CRATE = "tst-tsd-rs"


def tsd_crate_md5():
    h = hashlib.md5()
    fs = [SIM / TSD_CRATE / "Cargo.toml", SIM / TSD_CRATE / "Cargo.lock"]
    for c in (TSD_CRATE, "oracle-rs", "pc-solver-rs"):
        fs += list((SIM / c / "src").rglob("*.rs"))
    for p in sorted(set(fs), key=lambda p: p.relative_to(SIM).as_posix()):
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


def tsd_line_map():
    """({board name: {live class index: `rows|left` line}}, the page's loaded artefact), the page's own live/class_line, so
    the lines the crate is asked about are the lines the page's tilings name."""
    sys.path.insert(0, str(ROOT))
    from pipeline import tst_openers_tp_page as P
    art, cat = P.load_inputs()
    m = {}
    for b in art["boards"] + art["xboards"]:
        m[b["name"]] = {i: P.class_line(cat, b, i) for i in P.live(b)}
    return m, art


def tsd_input_lines():
    m, _ = tsd_line_map()
    return sorted({l for v in m.values() for l in v.values()})


def tsd_input_md5s(art=None):
    return {"tst_openers_tp": md5(canon(json.loads(OUT.read_text())).encode()), "x": md5(X_OUT.read_bytes()),
            "tst_openers": md5(OLD.read_bytes()), "shapes": md5(canon(load_inputs()[1]).encode())}


def tsd_merge_cmd(args):
    """--tsd <crate output>: the crate's per-line JSON -> analysis/tst-openers-tp-tsd.json."""
    m, pa = tsd_line_map()
    want = set(tsd_input_lines())
    rows = {}
    bad = 0
    for ln in Path(args.tsd).read_text().splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        assert r["line"] not in rows, "duplicate line " + r["line"]
        bad += r["bad_plans"]
        rows[r["line"]] = {"p5": r["p5"], "p5u": r["p5u"], "pt3": r["pt3"], "pt3u": r["pt3u"]}
    assert set(rows) == want, "crate output does not cover exactly the live lines (%d of %d)" % (len(rows), len(want))
    assert bad == 0, "the crate reports %d plans its own replay refused" % bad
    out = {"schema": TSD_SCHEMA, "report_eligible": False, "constructed": True,
           "means": QUARANTINE + ". Per live (shape residue rows, leftover) line: p5 = how many of the 5040 bag-3 dealt orders the Perfect Clear "
                    "solver clears (the same figure as the class p5 of tst-openers-tp.json), pt3 = how many orders have SOME Perfect Clear plan holding a full T-spin Double "
                    "(a T placement the engine credits as spin code 2 and that clears exactly two rows; it may be the PC's own last lock), found by a "
                    "separate search within the same node budget, so pt3 <= p5 is checked, not built in; pt3u is the number of orders that search "
                    "could not decide (0 when pt3 is exact). Bag 4 is not counted.",
           "den": B,
           "md5": {**tsd_input_md5s(), "crate": tsd_crate_md5()},
           "bad_plans": bad, "lines": {k: rows[k] for k in sorted(rows)}}
    TSD_OUT.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"wrote {TSD_OUT} ({len(rows)} lines)", file=sys.stderr)


def tsd_load_check():
    t = json.loads(TSD_OUT.read_text())
    assert t["schema"] == TSD_SCHEMA and t["report_eligible"] is False and t["constructed"] is True
    assert t["md5"] == {**tsd_input_md5s(), "crate": tsd_crate_md5()}, "analysis/tst-openers-tp-tsd.json is stale"
    return t


def tsd_load_lines():
    return tsd_load_check()["lines"]


def tsd_pt(art):
    """{board name: per-class pt3 vector} for the boards of the pooled artefact; a class that is not live has none (0)."""
    m, _ = tsd_line_map()
    lines = tsd_load_lines()
    out = {}
    for b in art["boards"]:
        live = m[b["name"]]
        out[b["name"]] = [lines[live[i]]["pt3"] if i in live else 0 for i in range(len(b["classes"]))]
    return out


def tsd_check_cmd(args):
    t = tsd_load_check()
    m, pa = tsd_line_map()
    lines = t["lines"]
    assert t["bad_plans"] == 0
    assert set(lines) == set(tsd_input_lines()), "lines are not the live lines"
    bad_u = 0
    for b in pa["boards"] + pa["xboards"]:
        for i, ln in m[b["name"]].items():
            r = lines[ln]
            assert r["p5"] == b["classes"][i][2], f"{b['name']} class {i}: crate p5 {r['p5']} != artefact {b['classes'][i][2]}"
            assert 0 <= r["pt3"] <= r["p5"] <= B, ln
            bad_u += r["pt3u"]
    print(f"ok: {len(lines)} lines, p5 equals the artefact's class p5, pt3 <= p5; undecided orders {bad_u}")


SETS_SCHEMA = "tst-openers-tp-sets/4"
SETS_OUT = ROOT / "analysis" / "tst-openers-tp-sets.json"
SETS_CRATE = "tst-sets-rs"
KINDS = "IOTSZJL"
FEATURES = [f"{KINDS[i]}<{KINDS[j]}" for i in range(7) for j in range(i + 1, 7)] + [f"first={k}" for k in KINDS]
SH = 13                                          # key = J << 13 | built (built <= 5040 < 8192)


def sets_crate_md5():
    h = hashlib.md5()
    fs = [SIM / SETS_CRATE / "Cargo.toml", SIM / SETS_CRATE / "Cargo.lock"] + list((SIM / SETS_CRATE / "src").rglob("*.rs"))
    for p in sorted(fs, key=lambda p: p.relative_to(SIM).as_posix()):
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


def board_tables(art, b1, pt=None):
    """{name: {bk: (J[0..10], Bt[0..10])}} and {name: b1 vector (numpy uint8, INFEAS for '.')}. `pt` {name: per-class p vector}
    swaps the objective (default: each class's p5)."""
    vec = b1_vectors(b1)
    zero = {bk: ([0] * (INFEAS + 1), [0] * (INFEAS + 1)) for bk in BKEYS}
    out = {}
    for b in art["boards"]:
        if set(vec[b["name"]]) == {INFEAS}:      # no first-bag order builds it: nothing to solve, all zero
            assert all(c == 0 for bk in BKEYS for c in b["cum"][bk]), b["name"]
            out[b["name"]] = zero
        else:
            out[b["name"]] = j_tables(b, solve_D(b["cum"], vec[b["name"]]), None if pt is None else pt[b["name"]])
    return out, vec


def mates(bs):
    """position of each pooled board's mirror (its own position for a self-mirror board, or one whose mirror is in neither artefact)."""
    keys = {}
    for i, b in enumerate(bs):
        k = board_key(b["pieces"])
        assert k not in keys, "duplicate board " + b["name"]
        keys[k] = i
    return [keys.get(mirror_board_key(board_key(b["pieces"])), i) for i, b in enumerate(bs)]


def sets_input_lines(art, b1, pt=None):
    tabs, _ = board_tables(art, b1, pt)
    mt = mates(art["boards"])
    assert all(mt[mt[i]] == i for i in range(len(mt))), "mirror is not an involution on the pool"
    raw = {n: zlib.decompress(base64.b64decode(z)).decode() for n, z in b1["vectors"].items()}
    out = []
    for i, b in enumerate(art["boards"]):
        f = ["%s/%s" % (",".join(str(int(x)) for x in tabs[b["name"]][bk][0][:INFEAS]),
                        ",".join(str(int(x)) for x in tabs[b["name"]][bk][1][:INFEAS])) for bk in BKEYS]
        out.append("|".join([b["name"], raw[b["name"]]] + f + [str(mt[i])]))
    return out


def sets_crate_run(art, b1, pt=None):
    r = subprocess.run(["cargo", "build", "--release", "--locked", "--quiet", "--manifest-path", str(SIM / SETS_CRATE / "Cargo.toml")],
                       capture_output=True, text=True)
    assert r.returncode == 0, "cargo build of tst-sets-rs failed:\n" + r.stderr
    exe = SIM / SETS_CRATE / "target" / "release" / "tst-sets"
    r = subprocess.run([str(exe)], input="\n".join(sets_input_lines(art, b1, pt)) + "\n", capture_output=True, text=True)
    assert r.returncode == 0, "tst-sets failed:\n" + r.stderr
    sys.stderr.write(r.stderr)
    return json.loads(r.stdout)


def sets_artefact(art, b1, raw, rawt):
    """`raw` is the crate run with the pc3 objective (any bag-3 PC, the top level of the artefact), `rawt` the run with the
    TST->TSD->PC objective (the `tsd` block; inside it the field called pc3 is that objective's count)."""
    bs = art["boards"]

    def brd(i):
        b = bs[i]
        return {"pos": i, "name": b["name"], "held": b.get("held"), "pieces": b["pieces"]}

    pr = raw["pairs"]
    assert rawt["pairs"] == pr and rawt["cands"] == raw["cands"], "the two objectives list different candidates"
    single = sum(1 for p in pr if len(p) == 1)
    selfm = sum(1 for p in pr if len(p) == 1 and board_key(bs[p[0]]["pieces"]) == mirror_board_key(board_key(bs[p[0]]["pieces"])))

    def blk(raw):
        def setrec(r):
            return {"pairs": [pr[c] for c in r["set"]], "boards": [brd(i) for i in r["ub"]], "pc3": r["pc3"], "built": r["built"]}

        def node(n):
            return {"m": n["m"]} if "m" in n else {"f": n["f"], "feature": FEATURES[n["f"]], "y": node(n["y"]), "n": node(n["n"])}
        budgets = {}
        for bk in BKEYS:
            r = raw["budgets"][bk]
            ex = {str(e["k"]): setrec(e) for e in r["exact"]}
            rule = {}
            for t in r["trees"]:
                rule[str(t["depth"])] = {"pc3": t["pc3"], "built": t["built"], "differs": t["differs"], "unbuildable": t["unbuildable"],
                                         "loss_pc3": ex["3"]["pc3"] - t["pc3"], "loss_built": ex["3"]["built"] - t["built"], "tree": node(t["tree"])}
            budgets[bk] = {"reduced": r["reduced"],
                           "dominated": {"count": len(r["dominated"]), "md5": md5(canon(r["dominated"]).encode())},
                           "exact": ex,
                           "greedy": {str(g["k"]): setrec(g) for g in r["greedy"]},
                           "from_exact3": {str(g["k"]): setrec(g) for g in r["from_exact3"]},
                           "picks": r["picks"], "rule": rule}
        fx = raw["fixed"]
        return budgets, {"budget": fx["budget"], "pairs": [pr[c] for c in fx["set"]], "boards": [brd(i) for i in fx["ub"]], "values": fx["values"]}
    budgets, fixed = blk(raw)
    tb, tf = blk(rawt)
    return {"schema": SETS_SCHEMA, "report_eligible": False, "constructed": True, "complete": False,
            "means": QUARANTINE + " Per soft-drop budget, the set of k mirror pairs (learning a shape includes its mirror; a pair is the board and its mirror, one board when they coincide or the mirror is in neither artefact) maximising the number of "
                     "(first-bag order, bag-2 deal, bag-3 deal) triples that build and get a bag-3 Perfect Clear when the best member "
                     "of the union is picked for each first-bag order; exact over the boards counted in the two artefacts (the kept boards and the x boards); a board in neither is uncounted.",
            "rules": {"pair": "a candidate is {board, its mirror} (one board when they coincide or the mirror is in neither artefact); k counts pairs and a set is the union of their boards",
                      "pick": "over the boards of the union, larger (J, built), ties to the earlier board position; none when no board builds within the budget",
                      "set": "larger pc3, then larger built, then the smaller tuple of pair positions (a pair sits at its smaller board position)",
                      "dominance": "u is dropped when v has key >= key_u on every order (key = J*8192+built, 0 when unavailable) and "
                                   "the keys differ somewhere or v is earlier; the dominator recorded is the earliest non-dominated one",
                      "exact": "k = 1, 2 by scan, k = 3 by branch and bound on f(abc) <= f(ab) + min(f(ac) - f(a), f(bc) - f(b)) over pc3",
                      "greedy": "best (pc3, built) added each step, ties to the smaller position; from_exact3 extends the exact triple",
                      "tree": "optimal depth <= d over the 28 features, leaf = member maximising the leaf's (sum J, sum built)"},
            "den": {"pc3": B ** 3, "built": B ** 2},
            "features": FEATURES,
            "md5": {"crate": sets_crate_md5(), "art": md5(canon(art["kept"]).encode()), "b1": md5(canon(b1["kept"]).encode()),
                    "x": md5(X_OUT.read_bytes()), "tsd": md5(TSD_OUT.read_bytes())},
            "cands": raw["cands"], "selfmirror": selfm, "mirror_missing": single - selfm,
            "boards": len(bs), "kept": len(art["kept"]["boards"]), "x": len(art["boards"]) - len(art["kept"]["boards"]),
            "budgets": budgets,
            "fixed": fixed,
            "tsd": {"means": "the same search with J counted over the (first-bag order, bag-2 deal, bag-3 deal) triples whose bag-3 Perfect Clear plan "
                             "contains a full T-spin Double (analysis/tst-openers-tp-tsd.json); inside this block the field named pc3 is that count. "
                             "Only bag-3 Perfect Clears are counted, bag 4 is not.",
                    "cands": rawt["cands"], "selfmirror": selfm, "mirror_missing": single - selfm,
                    "budgets": tb, "fixed": tf}}


def perms_order():
    out = []

    def r(p, rest):
        if not rest:
            out.append("".join(p))
            return
        for i in range(len(rest)):
            c = rest[i]
            r(p + [c], rest[:i] + rest[i + 1:])
    r([], list(KINDS))
    return out


def sets_load():
    art = json.loads(OUT.read_text())
    b1 = json.loads(B1_OUT.read_text())
    assert b1["md5"]["boards"] == boards_md5(art["boards"]) and b1["md5"]["crate"] == b1_crate_md5(), "b1 artefact is stale"
    x = load_x(art)
    pooled = {**art, "boards": art["boards"] + x["boards"], "kept": art}
    pb1 = {**b1, "vectors": {**b1["vectors"], **x["vectors"]}, "kept": b1}
    return pooled, pb1


def sets_cmd(args):
    art, b1 = sets_load()
    if args.sets_input:
        print("\n".join(sets_input_lines(art, b1, tsd_pt(art) if args.tsd_objective else None)))
        return
    raw = sets_crate_run(art, b1)
    rawt = sets_crate_run(art, b1, tsd_pt(art))
    out = sets_artefact(art, b1, raw, rawt)
    SETS_OUT.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"wrote {SETS_OUT}", file=sys.stderr)


def sets_check_cmd(args):
    art, b1 = sets_load()
    raw = sets_crate_run(art, b1)
    pt = tsd_pt(art)
    rawt = sets_crate_run(art, b1, pt)
    want = json.dumps(sets_artefact(art, b1, raw, rawt), separators=(",", ":"), ensure_ascii=False) + "\n"
    assert SETS_OUT.read_text() == want, "analysis/tst-openers-tp-sets.json is not what the crate runs build"
    sets_check_obj(art, b1, raw, None)
    sets_check_obj(art, b1, rawt, pt)


def sets_check_obj(art, b1, raw, pt):
    import numpy as np
    bs = art["boards"]
    nb = len(bs)
    tabs, vec = board_tables(art, b1, pt)
    # the candidates: every board is in exactly one pair, a pair is {board, its mirror} (found here by the mirror key, not by the
    # crate's mate list), and the pairs are listed at their smaller board position
    pr = raw["pairs"]
    bykey = {board_key(b["pieces"]): i for i, b in enumerate(bs)}
    exp = []
    for i, b in enumerate(bs):
        m = bykey.get(mirror_board_key(board_key(b["pieces"])), i)
        if m >= i:
            exp.append([i] if m == i else [i, m])
    assert pr == exp, "pairs are not {board, mirror}"
    assert sorted(i for p_ in pr for i in p_) == list(range(nb)), "pairs do not partition the boards"
    n = len(pr)
    pos = np.arange(n)
    P = perms_order()
    assert len(P) == B and len(set(P)) == B
    feat = np.array([[(p.index(KINDS[i]) < p.index(KINDS[j])) for i in range(7) for j in range(i + 1, 7)] +
                     [p[0] == k for k in KINDS] for p in P], dtype=bool)          # B x 28
    notes = []

    def val_of(key):                       # the (pc3, built) of an order-wise max key array
        return int((key >> SH).sum()), int((key & 8191).sum())

    for bk in BKEYS:
        r = raw["budgets"][bk]
        lim = INFEAS - 1 if bk == "inf" else int(bk)
        Jb = np.stack([np.array(tabs[b["name"]][bk][0])[np.frombuffer(vec[b["name"]], dtype=np.uint8)] for b in bs]).astype(np.int64)
        Btb = np.stack([np.array(tabs[b["name"]][bk][1])[np.frombuffer(vec[b["name"]], dtype=np.uint8)] for b in bs]).astype(np.int64)
        avb = np.stack([np.frombuffer(vec[b["name"]], dtype=np.uint8) <= lim for b in bs])
        Jb = np.where(avb, Jb, 0); Btb = np.where(avb, Btb, 0)
        assert Btb.max() < 8192
        keyb = np.where(avb, (Jb << SH) | Btb, 0)                 # per board
        key = np.stack([keyb[p_].max(0) for p_ in pr])             # per candidate: the best key over the pair's boards
        J = key >> SH
        # dominance, pointwise: every listed claim, and no non-listed board is dominated
        dom = {u: v for u, v in r["dominated"]}
        assert len(dom) == len(r["dominated"])

        def dominated_by(v, u):
            return bool((key[v] >= key[u]).all()) and (bool((key[v] != key[u]).any()) or v < u)
        reduced = [i for i in range(n) if i not in dom]
        assert len(reduced) == r["reduced"]
        for u, v in dom.items():
            assert v in reduced and dominated_by(v, u), f"dominance claim {u} <- {v} fails ({bk})"
            assert not any(dominated_by(w, u) for w in reduced if w < v), f"dominator of {u} is not the earliest ({bk})"
        for u in reduced:
            ge = (key >= key[u]).all(1) & (((key != key[u]).any(1)) | (pos < u))
            ge[u] = False
            assert not ge.any(), f"board {u} is dominated but not listed ({bk})"
        red = np.array(reduced)

        def setval(s):
            return val_of(key[list(s)].max(0))

        def union_of(s):
            return sorted({i for c in s for i in pr[c]})

        def check_set(rec, k):
            s = rec["set"]
            assert s == sorted(s) and len(s) == k and len(set(s)) == k
            assert setval(s) == (rec["pc3"], rec["built"]), f"set value wrong ({bk}, {s})"
            assert rec["ub"] == union_of(s), f"union of boards wrong ({bk}, {s})"

        for e in r["exact"]:
            check_set(e, e["k"])
        ex = {e["k"]: e for e in r["exact"]}
        # k = 1 over every board, k = 2 over every pair of the full list
        v1 = [(val_of(key[i]), i) for i in range(n)]
        m1 = max(v for v, _ in v1)
        assert m1 == (ex[1]["pc3"], ex[1]["built"])
        assert ex[1]["set"] == [min(i for v, i in v1 if v == m1 and i in set(reduced))]
        bestp = (-1, -1); bestl = []
        J32 = J.astype(np.int32)
        for a in range(n):
            pp = np.maximum(J32[a], J32[a + 1:]).sum(1, dtype=np.int64)       # pc3 of every pair (a, b > a), from J alone
            for t in np.nonzero(pp >= bestp[0])[0]:
                mk = np.maximum(key[a], key[a + 1 + int(t)])
                v = val_of(mk)
                assert v[0] == int(pp[t])
                if v > bestp:
                    bestp, bestl = v, []
                if v == bestp:
                    bestl.append((a, a + 1 + int(t)))
        assert bestp == (ex[2]["pc3"], ex[2]["built"]), f"a better pair exists ({bk})"
        rs = set(reduced)
        assert ex[2]["set"] == list(min(t for t in bestl if t[0] in rs and t[1] in rs)), f"pair tie rule ({bk})"
        # k = 3, by an independent certificate over the reduced list: every triple has either an upper bound under the reported
        # pc3 (f(abc) <= f(ab) + min(f(ac) - f(a), f(bc) - f(b)), by submodularity of a sum of maxima) or is valued exactly
        Jr = J32[red]; m = len(red)
        f1 = Jr.sum(1, dtype=np.int64)
        F2 = np.stack([np.maximum(Jr[a], Jr).sum(1, dtype=np.int64) for a in range(m)])
        t3 = (ex[3]["pc3"], ex[3]["built"])
        surv = 0; best3 = []
        for a in range(m):
            ub = F2[a][:, None] + np.minimum(F2[a][None, :] - f1[a], F2 - f1[:, None])     # [b, c]
            ok = np.triu(np.ones((m, m), dtype=bool), 1) & (ub >= t3[0])
            ok[: a + 1] = False
            ok[:, : a + 1] = False
            for b_, c_ in zip(*np.nonzero(ok)):
                surv += 1
                v = setval([red[a], red[b_], red[c_]])
                assert v <= t3, f"a better triple exists ({bk}): {[red[a], red[b_], red[c_]]}"
                if v == t3:
                    best3.append([int(red[a]), int(red[b_]), int(red[c_])])
        assert min(best3) == ex[3]["set"], f"triple tie rule ({bk})"
        notes.append(f"{bk}: reduced {m}, triple certificate evaluated {surv} of {m*(m-1)*(m-2)//6}")
        # greedy chains: every step the argmax over all boards, the first of the tied reduced boards
        def step_ok(prev, rec, k):
            s = rec["set"]
            assert set(prev) <= set(s) and len(s) == k
            new = (set(s) - set(prev)).pop()
            cur = key[prev].max(0) if prev else np.zeros(B, dtype=np.int64)
            mk = np.maximum(cur, key)
            vs = list(zip((mk >> SH).sum(1).tolist(), (mk & 8191).sum(1).tolist()))
            top = max(vs)
            assert top == (rec["pc3"], rec["built"]), f"greedy step {k} is not the best ({bk})"
            assert new == min(i for i in reduced if vs[i] == top and i not in prev), f"greedy step {k} tie rule ({bk})"
        prev = []
        for g in r["greedy"]:
            check_set(g, g["k"]); step_ok(prev, g, g["k"]); prev = g["set"]
        prev = ex[3]["set"]
        for g in r["from_exact3"]:
            check_set(g, g["k"]); step_ok(prev, g, g["k"]); prev = g["set"]
        # picks
        s3 = ex[3]["set"]
        ub = union_of(s3)
        assert r["ub"] == ub
        kk = np.where(avb[ub], keyb[ub] + 1, 0)                    # first strictly larger wins = earliest position
        arg = kk.argmax(0)
        pk = np.where(kk.max(0) > 0, arg, -1)
        assert r["picks"] == "".join("x" if x < 0 else str(int(x)) for x in pk), f"picks string ({bk})"
        # rule trees: walk every order, recompute the figures and each leaf's label; depth 1 by brute force
        sub = np.stack([np.where(avb[i], (Jb[i] << 26) + Btb[i], 0) for i in ub]).astype(object)
        nu = len(ub)
        exv = (ex[3]["pc3"], ex[3]["built"])

        def walk(nd, idx):
            """-> member per order of idx (array), checking leaf labels."""
            out = np.full(len(idx), -1)
            if "m" in nd:
                tot = [sub[mm][idx].sum() for mm in range(nu)]
                assert nd["m"] == max(range(nu), key=lambda mm: (tot[mm], -mm)), f"leaf label ({bk})"
                out[:] = nd["m"]
                return out
            f = nd["f"]
            yes = feat[idx, f]
            assert yes.any() and (~yes).any(), "a split with an empty side"
            out[yes] = walk(nd["y"], idx[yes]); out[~yes] = walk(nd["n"], idx[~yes])
            return out
        for d in ("1", "2", "3"):
            t = raw["budgets"][bk]["trees"][int(d) - 1]
            assert t["depth"] == int(d)
            mem = walk(t["tree"], np.arange(B))
            ids = np.array(ub)[mem]
            avail = avb[ids, np.arange(B)]
            p = int((Jb[ids, np.arange(B)]).sum()); b_ = int(Btb[ids, np.arange(B)].sum())
            assert (p, b_) == (t["pc3"], t["built"]), f"rule value depth {d} ({bk})"
            assert int((~avail).sum()) == t["unbuildable"]
            assert int(((pk >= 0) & (pk != mem)).sum()) == t["differs"]
            assert (p, b_) <= exv
            assert depth_of(t["tree"]) <= int(d)
        t1 = raw["budgets"][bk]["trees"][0]
        best1 = max(sub[mm].sum() for mm in range(nu))
        for f in range(28):
            y = feat[:, f]
            if y.any() and (~y).any():
                best1 = max(best1, max(sub[mm][y].sum() for mm in range(nu)) + max(sub[mm][~y].sum() for mm in range(nu)))
        assert (t1["pc3"], t1["built"]) == (int(best1 >> 26), int(best1 & ((1 << 26) - 1))), f"depth-1 tree is not optimal ({bk})"
    fx = raw["fixed"]
    s = fx["set"]
    assert s == raw["budgets"]["2"]["exact"][2]["set"]
    assert fx["ub"] == sorted({i for c in s for i in pr[c]})
    for bk in BKEYS:
        lim = INFEAS - 1 if bk == "inf" else int(bk)
        K = np.stack([np.where(np.frombuffer(vec[b["name"]], dtype=np.uint8) <= lim, (np.array(tabs[b["name"]][bk][0])[np.frombuffer(vec[b["name"]], dtype=np.uint8)].astype(np.int64) << SH) | np.array(tabs[b["name"]][bk][1])[np.frombuffer(vec[b["name"]], dtype=np.uint8)], 0) for b in (bs[i] for i in fx["ub"])])
        v = val_of(K.max(0))
        assert fx["values"][bk] == {"pc3": v[0], "built": v[1]}, f"fixed value ({bk})"
    print("ok: " + "; ".join(notes))
    print("ok: sets artefact equals the crate run; every set value, pick, greedy step, pair, dominance claim, triple certificate and tree recomputed")


def depth_of(nd):
    return 0 if "m" in nd else 1 + max(depth_of(nd["y"]), depth_of(nd["n"]))


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
    ap.add_argument("--sets", action="store_true")
    ap.add_argument("--sets-input", action="store_true")
    ap.add_argument("--sets-check", action="store_true")
    ap.add_argument("--tsd")
    ap.add_argument("--tsd-input", action="store_true")
    ap.add_argument("--tsd-check", action="store_true")
    ap.add_argument("--tsd-objective", action="store_true")
    ap.add_argument("--cross-check")
    ap.add_argument("--cand-merge", nargs=2, metavar=("T_OUT", "H_OUT"))
    ap.add_argument("--cand-out", default="cand.json")
    ap.add_argument("--cand", default="cand.json")
    ap.add_argument("--x-input", action="store_true")
    ap.add_argument("--kept", action="store_true")
    ap.add_argument("--x-merge", nargs=2, metavar=("X_OUT", "XB1_OUT"))
    ap.add_argument("--x-verify")
    ap.add_argument("--x-compare", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    if a.cand_merge:
        return cand_merge_cmd(a)
    if a.x_input:
        return x_cmd(a)
    if a.x_merge:
        return x_merge_cmd(a)
    if a.x_verify:
        return x_verify_cmd(a)
    if a.x_compare:
        return x_compare_cmd(a)
    if a.tsd_input:
        print("\n".join(tsd_input_lines()))
        return
    if a.tsd:
        return tsd_merge_cmd(a)
    if a.tsd_check:
        return tsd_check_cmd(a)
    if a.sets_check:
        return sets_check_cmd(a)
    if a.sets or a.sets_input:
        return sets_cmd(a)
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
