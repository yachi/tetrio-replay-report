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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shapes-out", required=True)
    ap.add_argument("--pc4-out", required=True)
    ap.add_argument("--timing", action="append", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    shapes = json.loads(SHAPES.read_text())["shapes"]
    art = build(shapes, Path(a.shapes_out).read_text().splitlines(), Path(a.pc4_out).read_text().splitlines(), timings(a.timing))
    Path(a.out).write_text(json.dumps(art, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"wrote {a.out}: {len(art['shapes'])} shapes, {len(art['pc4'])} pc4 lines, dropped {sorted(art['dropped_constant']['per_tiling'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
