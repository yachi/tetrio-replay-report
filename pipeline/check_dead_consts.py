"""Gate: every constant in a Dafny artefact must be read by some lemma.

    python3 -m pipeline.check_dead_consts sessions/2026-07-24/report

A const no lemma reads is data the proofs do not depend on. Mutating it can never
break verification, so the anti-vacuity gate reports a survivor that means nothing
— and a reader counting 4,533 constants in `Facts.dfy` over-estimates how much of
the dataset the proofs actually pin down.

`pipeline/codegen.py` has filtered the generated ledger this way from the start.
The two per-session `codegen_dafny.py` scripts did not, and shipped 157 dead
`_alive` booleans (2026-07-22) and 6 dead index/count consts (2026-07-24) until
2026-07-26. This keeps that from coming back.
"""
import argparse
import glob
import os
import re
import sys

CONST = re.compile(r"^const (\w+)\s*:", re.M)
LEMMA_FILE = re.compile(r"Claims.*\.dfy$")


def scan(dafny_dir):
    """(consts, dead) — names declared, and those no lemma file mentions."""
    consts, lemma_text = {}, []
    for path in sorted(glob.glob(os.path.join(dafny_dir, "*.dfy"))):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for name in CONST.findall(text):
            consts[name] = os.path.basename(path)
        if LEMMA_FILE.search(os.path.basename(path)):
            lemma_text.append(text)
    body = " ".join(lemma_text)
    dead = sorted(n for n in consts if not re.search(rf"\b{n}\b", body))
    return consts, dead


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    ap.add_argument("--dafny-dir", help="default <report_dir>/dafny")
    args = ap.parse_args(argv)

    dafny_dir = args.dafny_dir or os.path.join(args.report_dir, "dafny")
    if not os.path.isdir(dafny_dir):
        print(f"  --  no {dafny_dir}, nothing to check")
        return 0
    consts, dead = scan(dafny_dir)
    if not consts:
        print(f"FAIL no constants found in {dafny_dir}", file=sys.stderr)
        return 1
    for name in dead[:20]:
        print(f"FAIL {name} ({consts[name]}) is read by no lemma", file=sys.stderr)
    if dead:
        if len(dead) > 20:
            print(f"FAIL … and {len(dead) - 20} more", file=sys.stderr)
        print(f"\n{len(dead)} of {len(consts)} constants are dead: a mutation of one "
              "can never be killed, so the anti-vacuity gate would report meaningless "
              "survivors", file=sys.stderr)
        return 1
    print(f"  ok  all {len(consts)} constants are read by a lemma")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
