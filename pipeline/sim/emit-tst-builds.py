#!/usr/bin/env python3
"""One engine-played build per (ranked card, class) of docs/tst-openers.html -> analysis/tst-openers-tp-builds.json
(constructed, quarantined, like analysis/tst-openers-tp.json).

  python3 pipeline/sim/emit-tst-builds.py [--out analysis/tst-openers-tp-builds.json] [--check]

For every ranked card and every live class, the page draws one tiling (`tst_openers_tp_page.holders`). This feeds that
tiling to `pipeline/sim/tst-build-rs` (built here when stale): bag 1 is the card's six pieces, the rest of the tiling after it, and
the binary returns a placement ORDER (bag 1 first) in which the engine's own movegen (`oracle-rs` reach, SRS+, 180)
reaches every piece from spawn, with the fewest soft-drop placements, and whether the T then reaches the TST slot with a
full spin. It is an order the engine can play, not the order pieces are dealt. Nothing here is a figure.
`--check` re-runs it and fails unless the committed artefact is byte-identical.
"""
import argparse, hashlib, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline import tst_openers_tp_page as TP  # noqa: E402

SIM = ROOT / "pipeline" / "sim"
CRATE = SIM / "tst-build-rs"
OUT = ROOT / "analysis" / "tst-openers-tp-builds.json"
JOBS = 4


def md5(b):
    return hashlib.md5(b).hexdigest()


def crate_md5():
    fs = [CRATE / "Cargo.toml"] + list((CRATE / "src").rglob("*.rs")) + list((SIM / "oracle-rs" / "src").rglob("*.rs"))
    h = hashlib.md5()
    for p in sorted(fs, key=lambda p: p.relative_to(SIM).as_posix()):
        h.update(f"{p.relative_to(SIM).as_posix()}\0{md5(p.read_bytes())}\n".encode())
    return h.hexdigest()


def key(card, i):
    return f"{card}#{i}"


def lines(repo=ROOT):
    art, cat = TP.load_inputs(str(repo))
    out = []
    for r, _ in TP.ranked(art, cat):
        bs = TP.piece_set(r["pieces"])
        for i, t in sorted(TP.holders(cat, r).items()):
            s = cat[r["shapes"][r["classes"][i][0]]]
            b1 = [p for p in t["pieces"] if (p[0], tuple(sorted(p[1]))) in bs]
            b2 = [p for p in t["pieces"] if (p[0], tuple(sorted(p[1]))) not in bs]
            assert len(b1) == len(bs), f"{r['name']} class {i}: the tiling does not hold the board"
            enc = lambda ps: ";".join(f"{k}:{','.join(map(str, sorted(cs)))}" for k, cs in ps)
            tst = ",".join(str(y * 10 + x) for x, y in sorted(s["tst"]))
            out.append(f"{key(r['name'], i)}|{enc(b1)}|{enc(b2)}|{tst}")
    return out


def build():
    subprocess.run(["cargo", "build", "--release", "--locked", "--manifest-path", str(CRATE / "Cargo.toml")], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ls = lines()
    exe = str(CRATE / "target" / "release" / "tst-build")
    chunks = [ls[i::JOBS] for i in range(JOBS)]
    run = lambda c: subprocess.run([exe], input="\n".join(c) + "\n", text=True, capture_output=True, check=True).stdout
    with ThreadPoolExecutor(JOBS) as ex:
        outs = list(ex.map(run, chunks))
    by = {}
    for o in outs:
        for l in o.splitlines():
            if l.strip():
                g = json.loads(l)
                by[g["id"]] = g
    got = [by[l.split("|", 1)[0]] for l in ls]
    assert [g["id"] for g in got] == [l.split("|", 1)[0] for l in ls], "the binary did not answer every line in order"
    with open(ROOT / "analysis" / "tst-openers-tp.json", "rb") as f:
        tp = md5(f.read())
    return {
        "schema": "tst-openers-tp-builds/1",
        "report_eligible": False,
        "constructed": True,
        "about": ("Per ranked card and live class of docs/tst-openers.html, a placement order of the drawn tiling (bag 1 "
                  "first) that the engine's own movegen plays from spawn, with the fewest soft-drop placements, and "
                  "whether the T then reaches the TST slot with a full spin. A placement order, not a deal order."),
        "md5": {"crate": crate_md5(), "tst_openers_tp": tp},
        "builds": {g["id"]: {"order": g["order"], "sd": g["sd"], "tst": g["tst"]} for g in got},
    }


def dump(a):
    return json.dumps(a, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    s = dump(build())
    if a.check:
        if Path(a.out).read_text(encoding="utf-8") != s:
            sys.exit(f"{a.out} is stale: re-run pipeline/sim/emit-tst-builds.py")
        print(f"{a.out} is current")
        return
    Path(a.out).write_text(s, encoding="utf-8")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
