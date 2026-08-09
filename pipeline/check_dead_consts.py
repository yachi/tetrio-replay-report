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
WORD = re.compile(r"\w+")


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
    # One pass over the lemma text, not one pass PER CONST.
    #
    # This used to be `re.search(rf"\b{n}\b", body)` inside the comprehension: O(|consts| x
    # |body|), with a fresh regex compiled each time. At 4 757 consts against ~600 KB of
    # Claims text that is 9.1 s per session, x4 sessions in the CI matrix, and it is the
    # slowest Python gate in the repo by two orders of magnitude.
    #
    # Searching many patterns in one pass is what Aho-Corasick is for (CACM 18(6), 1975),
    # but building an automaton is more than this input needs. Every pattern here is
    # `\b<name>\b` where the name is `\w+`, and `\b` between `\w` and `\W` is exactly a
    # token boundary — so `\b{n}\b` matches iff `n` occurs as a whole `\w+` token. Split the
    # body into its tokens once, hash them, and each const is an O(1) membership test.
    # Same answer by the definition of `\b`, not by an approximation of it.
    #
    # It relies on every const name being `\w+`, which the CONST regex above guarantees by
    # construction — it cannot capture a name containing anything else.
    tokens = set(WORD.findall(body))
    dead = sorted(n for n in consts if n not in tokens)
    return consts, dead


def selftest():
    """Plant each thing that can go wrong and require `scan` to notice.

    This gate answers a membership question, and the fast path answers it by tokenising
    the lemma text once instead of running a regex per const. A tokeniser that is subtly
    too GENEROUS turns the gate silently green — `all N constants are read` is what a
    working run prints too — so the substring cases below are the point of this test, not
    padding. The old per-const `\\b{n}\\b` search is what they pin the behaviour to.
    """
    import tempfile

    cases = [
        # (Facts.dfy body, Claims.dfy body, expected dead names)
        ("const alive_one: int := 1\n", "lemma L() ensures alive_one == 1 {}\n", []),
        ("const lonely: int := 1\n", "lemma L() ensures 1 == 1 {}\n", ["lonely"]),
        # A const whose name is a PREFIX of a token that does appear. `\b abc \b` does not
        # match inside `abcd`, so `abc` is dead — a tokeniser that used `in` on the raw
        # text would call it live and hide a real dead const.
        ("const abc: int := 1\n", "lemma L() ensures abcd == 1 {}\n", ["abc"]),
        # ...and the suffix direction, which a naive `endswith`/substring check also misses.
        ("const bcd: int := 1\n", "lemma L() ensures abcd == 1 {}\n", ["bcd"]),
        # Adjacent to punctuation on both sides is a genuine read: `(x)` tokenises to `x`.
        ("const x9: int := 1\n", "lemma L() ensures (x9)+1 == 2 {}\n", []),
        # Only Claims*.dfy counts as lemma text — a const mentioned solely in Facts.dfy
        # is still dead, which is the rule the file has always enforced.
        ("const only_here: int := 1\n// only_here\n", "lemma L() ensures 1 == 1 {}\n",
         ["only_here"]),
    ]
    failures = 0
    for i, (facts, claims, want) in enumerate(cases, 1):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "Facts.dfy"), "w", encoding="utf-8") as fh:
                fh.write(facts)
            with open(os.path.join(d, "Claims.dfy"), "w", encoding="utf-8") as fh:
                fh.write(claims)
            _, dead = scan(d)
        if dead != want:
            print(f"SELFTEST {i} FAIL: dead={dead}, want={want}", file=sys.stderr)
            failures += 1
    if failures:
        print(f"selftest: {failures} of {len(cases)} cases failed", file=sys.stderr)
        return 1
    print(f"  ok  selftest: {len(cases)} planted cases, "
          "including prefix/suffix substrings, all classified correctly")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir", nargs="?")
    ap.add_argument("--dafny-dir", help="default <report_dir>/dafny")
    ap.add_argument("--selftest", action="store_true",
                    help="check the gate can still fail, then exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.report_dir:
        ap.error("report_dir is required unless --selftest is given")

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
