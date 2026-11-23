#!/usr/bin/env python3
"""One worked Perfect Clear per ranked card of docs/tst-openers.html -> analysis/tst-openers-pc-examples.json
(constructed, quarantined, like analysis/tst-openers.json).

  python3 pipeline/sim/emit-tst-pc-examples.py --out analysis/tst-openers-pc-examples.json [--check]
  python3 pipeline/sim/emit-tst-pc-examples.py --tp [--out analysis/tst-openers-tp-pc-examples.json] [--check]

Takes every card's displayed tiling (`tst_openers_page.entries`, the best tiling of each ranked shape, the
two-bag-unbuildable ones left out: their PC is 未計), builds its `rows|left` line and runs the
`pipeline/sim/tst-pcex-rs` binary over them (built here when stale). See that crate's docstring for which
deal and plan it reports; nothing here is a figure, only an example the page draws and its audit replays.
`--tp` does the same for the T-placed ranking (`analysis/tst-openers-tp.json`): the lines are
`tst_openers_tp_page.pcx_lines()` when that module defines it, else `emit-tst-openers-tp.py`'s `pcx_lines()` (every
board above the threshold, its shown class's residue and leftover); mirror shapes are solved on their own residue.
`--check` re-runs it and fails unless the committed artefact is byte-identical.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline import tst_openers_page as P  # noqa: E402
import importlib.util  # noqa: E402

SIM = ROOT / "pipeline" / "sim"
CRATE = SIM / "tst-pcex-rs"
OUT = ROOT / "analysis" / "tst-openers-pc-examples.json"
OUT_TP = ROOT / "analysis" / "tst-openers-tp-pc-examples.json"
TP_ART = ROOT / "analysis" / "tst-openers-tp.json"


def tp_lines():
    try:
        from pipeline import tst_openers_tp_page as TP
        if hasattr(TP, "pcx_lines"):
            return TP.pcx_lines()
    except ImportError:
        pass
    sp = importlib.util.spec_from_file_location("emit_tst_openers_tp", SIM / "emit-tst-openers-tp.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m.pcx_lines()


def md5(b):
    return hashlib.md5(b).hexdigest()


def crate_md5():
    """tst-pcex-rs Cargo.toml and sources, and pc-solver-rs's sources, sorted by path."""
    fs = [CRATE / "Cargo.toml"] + list((CRATE / "src").rglob("*.rs")) + list((SIM / "pc-solver-rs" / "src").rglob("*.rs"))
    h = hashlib.md5()
    for p in sorted(fs, key=lambda p: p.relative_to(SIM).as_posix()):
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


def lines(repo=ROOT):
    art, shp = P.load_inputs(str(repo))
    return [P.line_of(e["o"], P.shown_tiling(e)) for e in P.entries(art, shp) if P.shown_tiling(e)["B"] > 0]


TP_ABOUT = ("One worked Perfect Clear per live class of every ranked board of docs/tst-openers.html (the residue and "
            "leftover of the class): the first bag-3 deal, in a fixed permutation order, the solver clears. There is no "
            "bag-4 example: the T-placed page counts bag 3 only (schema /2 of this artefact drops the `b4` the solver "
            "binary still computes). An example, not a figure: the percentages come from analysis/tst-openers-tp.json. "
            "Plans are the solver's (engine movegen); a plan's cells are in the board as it stands at that step.")


def build(jobs=4, tp=False):
    subprocess.run(["cargo", "build", "--release", "--locked", "--manifest-path", str(CRATE / "Cargo.toml")], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ls = tp_lines() if tp else lines()
    r = subprocess.run([str(CRATE / "target" / "release" / "tst-pcex")], input="\n".join(ls) + "\n", text=True,
                       capture_output=True, check=True, env={"JOBS": str(jobs), "PATH": "/usr/bin:/bin"})
    ex = [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
    assert [e["line"] for e in ex] == ls, "the binary did not answer every line in order"
    if tp:
        ex = [{k: v for k, v in e.items() if k != "b4"} for e in ex]
    art = {
        "schema": "tst-openers-pc-examples/2" if tp else "tst-openers-pc-examples/1",
        "report_eligible": False,
        "constructed": True,
        "about": TP_ABOUT if tp else "One worked Perfect Clear per card of docs/tst-openers.html (the card's displayed tiling): the first "
                 "bag-3 deal, in a fixed permutation order, the solver clears, and the first bag-3 deal it proves "
                 "cannot clear followed by the first bag-4 deal that can. An example, not a figure: the card's "
                 "percentages come from analysis/tst-openers.json. Plans are the solver's (engine movegen); a plan's "
                 "cells are in the board as it stands at that step.",
        "solver": ({"bag3": {"max_rows": 5, "nodes": 2000000}} if tp else
                   {"bag3": {"max_rows": 5, "nodes": 2000000}, "bag4": {"max_rows": 7, "nodes": 20000000}}),
        "md5": ({"crate": crate_md5(), "tst_openers_tp": md5(TP_ART.read_bytes())} if tp else
                {"crate": crate_md5(), "tst_openers": md5((ROOT / "analysis" / "tst-openers.json").read_bytes())}),
        "examples": ex,
    }
    return json.dumps(art, ensure_ascii=False, indent=1) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--tp", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)
    a.out = a.out or str(OUT_TP if a.tp else OUT)
    text = build(a.jobs, a.tp)
    if a.check:
        old = Path(a.out).read_text(encoding="utf-8")
        if old != text:
            print(f"{a.out} is stale: re-run without --check", file=sys.stderr)
            return 1
        print(f"{a.out}: current")
        return 0
    Path(a.out).write_text(text, encoding="utf-8")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
