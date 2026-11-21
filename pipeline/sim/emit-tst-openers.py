#!/usr/bin/env python3
"""Merge the tst2bag crate's outputs into analysis/tst-openers.json (constructed, quarantined).

  python3 pipeline/sim/emit-tst-openers.py --shapes-out <counter stdout> --pc4-out <pc4 stdout> \
      [--timing <stderr of a counter run> ...] --out analysis/tst-openers.json

The counter (`pipeline/sim/tst2bag-rs`, binary `tst2bag`) reads one `s<id>|cells|tst` line per shape
(`input_line` below builds it from the shapes file) and prints one JSON object per shape; `pc4`
reads `rows|left` lines and samples the bag-4 Perfect Clear rate. The full recount is far too long
for CI, so the artefact is the committed output of that run and `tst-openers.test.ts` re-runs a
pinned cheap subset byte for byte. The shapes come from pipeline/openers/tst-openers-shapes.json
(`shapes` list only; its other keys are the source checker's).

Per-tiling fields constant over the whole counter output are dropped and recorded in
`dropped_constant`; the tiling `id` is its index in `til` and is dropped too (checked).
`seconds` is the counter's own per-shape wall time from `--timing` files, rounded to 0.01 s, and is
omitted for a shape no timing file names. Wall time is machine-dependent: the test never compares it.

FIXED BAG 1 (`fixed` per shape, added by a second pass over an existing artefact):

  python3 pipeline/sim/emit-tst-openers.py --fixed-input > fixed.in
  FIXED=1 JOBS=4 pipeline/sim/tst2bag-rs/target/release/tst2bag < fixed.in > fixed.out
  python3 pipeline/sim/emit-tst-openers.py --merge-fixed fixed.out --out analysis/tst-openers.json

The base counts let a player adapt BOTH bags to the deal (bag 1 included). `FIXED=1` counts the
other reading: bag 1 is one memorised board (one placement of each of IJLOSZ, the T held), bag 2 is
dealt at random and the player adapts among every tiling that contains that board. For each such
board the counter prints `cum[k]`, the dealt orders (of 5040^2) that end on a tiling whose leftover
is one of the first k+1 `classes`; the classes are the leftovers ordered by their PC chance (best
first, `fixed_input_lines`), so `cum[k] - cum[k-1]` is the deals that finish on class k and no
better one. `fixed.best` is the board with the largest sum of those increments times their PC
chance (ties: the larger cum[-1], then the counter's order); `fixed.til` is the tiling drawn for it
(the best-scoring one containing it); `fixed.cums` keeps every board's cum so the page audit can
re-pick the best.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "pipeline" / "sim"
SHAPES = ROOT / "pipeline" / "openers" / "tst-openers-shapes.json"
CRATES = ["tst2bag-rs", "oracle-rs", "pc-solver-rs"]


def md5(b):
    return hashlib.md5(b).hexdigest()


def emitter_files():
    """tst2bag-rs sources + Cargo.toml, and both dependency crates' sources, sorted by path."""
    fs = [SIM / "tst2bag-rs" / "Cargo.toml"]
    for c in CRATES:
        fs += list((SIM / c / "src").rglob("*.rs"))
    return sorted(fs, key=lambda p: p.relative_to(SIM).as_posix())


def emitter_md5():
    h = hashlib.md5()
    for p in emitter_files():
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def shapes_md5(shapes):
    return md5(canon(shapes).encode())


def input_line(s):
    pt = lambda ps: ";".join(f"{x},{y}" for x, y in ps)
    return f"s{s['id']}|{pt(s['cells'])}|{pt(s['tst'])}"


def timings(paths):
    out = {}
    for p in paths:
        for l in Path(p).read_text().splitlines():
            m = re.fullmatch(r"(s\d+) done in ([\d.]+)(ms|s)", l.strip())
            if m:
                out[m[1]] = float(m[2]) * (1e-3 if m[3] == "ms" else 1)
    return out


def build(shapes, shapes_out, pc4_out, tim):
    by = {}
    for l in shapes_out:
        if l.strip():
            r = json.loads(l)
            assert r["name"] not in by, f"duplicate {r['name']}"
            by[r["name"]] = r
    ids = [f"s{s['id']}" for s in shapes]
    assert sorted(by) == sorted(ids), "counter output does not cover exactly the shapes file"
    tils = [t for r in by.values() for t in r["til"]]
    assert all(t["id"] == i for r in by.values() for i, t in enumerate(r["til"])), "tiling id is not its index"
    assert all(r["ntil"] == len(r["til"]) for r in by.values())
    dropped = {}
    for k in sorted(tils[0]):
        if k == "id":
            continue
        vals = {canon(t[k]) for t in tils}
        if len(vals) == 1:
            dropped[k] = tils[0][k]
    recs = []
    for s in sorted(shapes, key=lambda s: s["id"]):
        r = by[f"s{s['id']}"]
        rec = {"id": s["id"], "rows": r["rows"], "ntil": r["ntil"]}
        if r["name"] in tim:
            rec["seconds"] = round(tim[r["name"]], 2)
        rec["til"] = [{k: v for k, v in t.items() if k != "id" and k not in dropped} for t in r["til"]]
        recs.append(rec)
    pc = {}
    for l in pc4_out:
        if l.strip():
            r = json.loads(l)
            assert r["line"] not in pc, f"duplicate pc4 line {r['line']}"
            pc[r["line"]] = r
    return {
        "schema": "tst-openers/1",
        "report_eligible": False,
        "constructed": True,
        "quarantine": "constructed from the shapes file by an enumerator and a solver; nobody played these boards; no claim id, no badge",
        "emitter_md5": emitter_md5(),
        "shapes_md5": shapes_md5(shapes),
        "dropped_constant": {"per_tiling": dropped, "per_tiling_id": "index in til"},
        "pc4_note": "line = 'rows|left' (the board after the TST and the bag's leftover pieces); sampled, seeded from the line",
        "shapes": recs,
        "pc4": [pc[k] for k in sorted(pc)],
    }


def _page():
    sys.path.insert(0, str(ROOT))
    from pipeline import tst_openers_page as P
    return P


def class_pc(o, idx):
    """leftover -> its PC chance (bag 4, else bag 3), over the shape's two-bag-buildable tilings."""
    P = _page()
    from fractions import Fraction
    pc = {}
    for t in o["til"]:
        if t["B"] <= 0:
            continue
        p4, _ = P.tiling_p4(o, t, idx)
        v = p4 if p4 is not None else Fraction(t["p5"], P.BAG)
        assert pc.setdefault(t["left"], v) == v, f"shape {o['id']}: leftover {t['left']!r} has two PC chances"
    return pc


def class_order(pc):
    return sorted(pc, key=lambda l: (-pc[l], l))


def fixed_input_lines(art, shapes):
    idx = _page().p4_index(art)
    by = {s["id"]: s for s in shapes}
    pt = lambda ps: ";".join(f"{x},{y}" for x, y in ps)
    out = []
    for o in art["shapes"]:
        pc = class_pc(o, idx)
        if pc:
            s = by[o["id"]]
            out.append(f"s{o['id']}|{pt(s['cells'])}|{pt(s['tst'])}|" + ";".join(c or "-" for c in class_order(pc)))
    return out


def fixed_joint(cum, classes, pc):
    prev, j = 0, 0
    for c, k in zip(cum, classes):
        j += (c - prev) * pc[k]
        prev = c
    return j


def merge_fixed(art, lines):
    P = _page()
    idx = P.p4_index(art)
    got = {}
    for l in lines:
        if l.strip():
            r = json.loads(l)
            assert r["name"] not in got, f"duplicate {r['name']}"
            got[r["name"]] = r
    for o in art["shapes"]:
        o.pop("fixed", None)
        pc = class_pc(o, idx)
        r = got.pop(f"s{o['id']}", None)
        assert (r is None) == (not pc), f"shape {o['id']}: fixed output present iff a two-bag tiling exists"
        if r is None:
            continue
        classes = [c for c in r["classes"]]
        assert classes == class_order(pc), f"shape {o['id']}: fixed run used another class order"
        if not r["b1"]:
            o["fixed"] = {"classes": classes, "nb1": 0}
            continue
        best = max(range(len(r["b1"])), key=lambda i: (fixed_joint(r["b1"][i]["cum"], classes, pc), r["b1"][i]["cum"][-1], -i))
        b = r["b1"][best]
        cells = {(k, tuple(sorted(cs))) for k, cs in b["pieces"]}
        cand = [i for i, t in enumerate(o["til"]) if t["B"] > 0 and cells <= {(k, tuple(sorted(cs))) for k, cs in t["pieces"]}]
        assert cand, f"shape {o['id']}: no tiling contains its best bag-1 board"
        til = max(cand, key=lambda i: (P.score(o["til"][i], P.tiling_p4(o, o["til"][i], idx)[0]), o["til"][i]["B"], -i))
        o["fixed"] = {"classes": classes, "nb1": len(r["b1"]), "best": best, "b1": b["pieces"], "ntil": b["ntil"],
                      "til": til, "cums": [x["cum"] for x in r["b1"]]}
    assert not got, f"fixed output names unknown shapes {sorted(got)}"
    art["schema"] = "tst-openers/2"
    art["emitter_md5"] = emitter_md5()
    return art


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shapes-out")
    ap.add_argument("--pc4-out")
    ap.add_argument("--timing", action="append", default=[])
    ap.add_argument("--fixed-input", action="store_true", help="print the FIXED=1 counter's input lines")
    ap.add_argument("--merge-fixed", help="a FIXED=1 counter output to merge into --out (read and rewritten)")
    ap.add_argument("--out")
    a = ap.parse_args()
    art_path = Path(a.out) if a.out else ROOT / "analysis" / "tst-openers.json"
    if a.fixed_input:
        art = json.loads(art_path.read_text())
        print("\n".join(fixed_input_lines(art, json.loads(SHAPES.read_text())["shapes"])))
        return
    if a.merge_fixed:
        art = merge_fixed(json.loads(art_path.read_text()), Path(a.merge_fixed).read_text().splitlines())
        art_path.write_text(json.dumps(art, separators=(",", ":"), ensure_ascii=False) + "\n")
        print(f"merged fixed bag 1 into {art_path}: {sum('fixed' in o for o in art['shapes'])} shapes", file=sys.stderr)
        return
    assert a.shapes_out and a.pc4_out and a.out, "--shapes-out, --pc4-out and --out are required"
    shapes = json.loads(SHAPES.read_text())["shapes"]
    art = build(shapes, Path(a.shapes_out).read_text().splitlines(), Path(a.pc4_out).read_text().splitlines(), timings(a.timing))
    Path(a.out).write_text(json.dumps(art, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"wrote {a.out}: {len(art['shapes'])} shapes, {len(art['pc4'])} pc4 lines, dropped {sorted(art['dropped_constant']['per_tiling'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
