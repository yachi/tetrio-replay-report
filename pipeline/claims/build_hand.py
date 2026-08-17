"""Build a session's hand-written claim ledger from a spec-carrying module.

    python3 -m pipeline.claims.build_hand sessions/2026-07-28/report/hand_claims.py \
        --facts sessions/2026-07-28/report/facts.json \
        --out sessions/2026-07-28/report/claims-narrative.json

Hand claims are the ones a generator cannot produce: they say what was *interesting*
about a particular night. What they are not is a different kind of artefact — they
carry a `spec` exactly like a generated claim, so `codegen` and `codegen_smt` render
them to Dafny and SMT-LIB with no per-session emitter. This is now the path for EVERY
session: 07-22 and 07-24 each used to carry a hand-written ~500-line codegen_dafny.py
that spelled every bound out a second time, and both are gone.

A session may hold more than one hand ledger — 07-22 and 07-24 split theirs into
narrative and coaching — so the module-to-ledger mapping is `hand_ledgers()` below
rather than the single `hand_claims.py` the guard used to look for. That guard was
written when one name covered every case, and it does not fail on a name it does not
recognise: it *skips*, which would have left both ported sessions' ledgers with
nothing checking they still match their modules.

The module names a list `CLAIMS`, each entry a dict of:

    id             C001, C002, ... (unique across all of the session's ledgers)
    category       score / style / moment — what the report groups it under
    canto          the Hong Kong Cantonese sentence, traditional characters
    english_gloss  the sentence codegen turns into the lemma name
    spec           built with pipeline.claims.spec constructors

Validation is deliberately the same as the generated ledger's: every predicate must
evaluate True against the facts, no Simplified glyphs, no duplicate predicates. A
claim that does not hold is a refusal to emit, never a warning.
"""
import argparse
import importlib.util
import json
import os
import sys

from .build_claims import validate
from .spec import to_python


def hand_ledgers(report_dir):
    """Every (module, ledger) pair a session's hand claims are built through.

        hand_claims.py           -> claims-narrative.json
        hand_claims_coaching.py  -> claims-coaching.json

    THE COVERAGE ASSERTION IS THE POINT, not the naming convention. A hand ledger with
    no module behind it is a file nothing regenerates, so nothing can catch it drifting
    from the data — which is the state 07-22 and 07-24 were in for their whole life, and
    the state the old `[ -f hand_claims.py ]` guard would have quietly restored the
    moment a session split its ledger in two. So an unmatched ledger raises here rather
    than being skipped, and the caller iterates whatever this returns instead of naming
    a file.
    """
    names = sorted(os.listdir(report_dir))
    pairs, claimed = [], set()
    for n in names:
        if not (n.startswith("hand_claims") and n.endswith(".py")):
            continue
        suffix = n[len("hand_claims"):-len(".py")]
        ledger = "claims-narrative.json" if not suffix else f"claims{suffix.replace('_', '-')}.json"
        if ledger not in names:
            raise SystemExit(f"{report_dir}/{n} builds {ledger}, which does not exist")
        pairs.append((os.path.join(report_dir, n), os.path.join(report_dir, ledger)))
        claimed.add(ledger)
    orphans = [n for n in names
               if n.startswith("claims") and n.endswith(".json")
               and "proof-map" not in n and n != "claims-generated.json"
               and n not in claimed]
    if orphans:
        raise SystemExit(f"{report_dir}: hand ledger(s) with no module to rebuild them: "
                         + ", ".join(orphans))
    return pairs


def load_module(path):
    spec = importlib.util.spec_from_file_location("hand_claims", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {path} as a module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def selftest():
    """Prove `hand_ledgers` refuses both ways round, on synthetic directories.

    The two mutants are the two halves of the coverage assertion, and each is the
    shape of a real defect: a ledger nothing rebuilds (07-22's and 07-24's state
    before the port) and a module whose output was renamed out from under it. The
    controls exist because a check that raised on everything would pass the mutants
    for free — one is the ordinary one-module session, the other proves proof maps
    are not mistaken for hand ledgers.
    """
    import tempfile
    cases = [
        (["hand_claims.py", "claims-narrative.json", "claims-generated.json"], False,
         "control — the ordinary one-module session"),
        (["claims-generated.json", "claims-generated-proof-map.json",
          "claims-proof-map.json", "hand_claims.py", "claims-narrative.json"], False,
         "control — proof maps are not hand ledgers"),
        (["claims-narrative.json", "claims-coaching.json", "hand_claims_narrative.py"], True,
         "mutant — a hand ledger with no module to rebuild it"),
        (["hand_claims.py", "claims-generated.json"], True,
         "mutant — a module whose ledger does not exist"),
    ]
    bad = 0
    for files, want_raise, label in cases:
        d = tempfile.mkdtemp()
        for f in files:
            open(os.path.join(d, f), "w").close()
        try:
            hand_ledgers(d)
            raised = False
        except SystemExit:
            raised = True
        ok = raised == want_raise
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    if bad:
        print(f"SELFTEST FAILED — {bad} case(s)", file=sys.stderr)
        return 1
    print(f"selftest: {len(cases)}/{len(cases)} cases as expected "
          "(2 mutants raise, 2 controls do not)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("module", nargs="?", help="the session's hand_claims*.py")
    ap.add_argument("--facts")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true",
                    help="prove hand_ledgers' coverage assertion has teeth, then exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.module or not args.facts:
        ap.error("module and --facts are required unless --selftest is given")

    with open(args.facts, encoding="utf-8") as fh:
        facts = json.load(fh)

    claims = [dict(c) for c in load_module(args.module).CLAIMS]
    for c in claims:
        c["python_check"] = to_python(c["spec"])

    ids = [c["id"] for c in claims]
    problems = validate(claims, facts)
    problems += [f"duplicate id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]

    print(f"built {len(claims)} hand claims from {args.module}")
    if problems:
        print(f"\nREFUSING TO EMIT — {len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print(f"all {len(claims)} predicates evaluate True; no simplified glyphs; no duplicates")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(claims, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
