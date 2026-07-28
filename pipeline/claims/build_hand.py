"""Build a session's hand-written claim ledger from a spec-carrying module.

    python3 -m pipeline.claims.build_hand sessions/2026-07-28/report/hand_claims.py \
        --facts sessions/2026-07-28/report/facts.json \
        --out sessions/2026-07-28/report/claims-narrative.json

Hand claims are the ones a generator cannot produce: they say what was *interesting*
about a particular night. What they are not is a different kind of artefact — they
carry a `spec` exactly like a generated claim, so `codegen` and `codegen_smt` render
them to Dafny and SMT-LIB with no per-session emitter. The 07-22 and 07-24 sessions
predate this and each needed a hand-written ~500-line codegen_dafny.py; those stay as
they are, and this is the path for every session after them.

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
import sys

from .build_claims import validate
from .spec import to_python


def load_module(path):
    spec = importlib.util.spec_from_file_location("hand_claims", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {path} as a module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("module", help="the session's hand_claims.py")
    ap.add_argument("--facts", required=True)
    ap.add_argument("--out")
    args = ap.parse_args(argv)

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
