#!/usr/bin/env python3
"""Verify every claim's python_check evaluates True against facts.json.

    python3 -m pipeline.check_claims claims-coaching.json [facts.json]

Run it as a module, not as a script path: the evaluator is shared with
`claims.equiv` and `claims.build_claims` (see `pipeline/claims/evaluate.py` for why
there is exactly one of it), so this file imports from its own package.

There used to be eight byte-identical copies of this checker — one per session
artefact, plus `tools/` and this one — and `bin/verify-session` preferred whichever
copy sat in the directory it was checking. Eight copies of a gate is eight chances
for the gate to differ from itself.
"""
import json, sys

from .claims.evaluate import ClaimEvaluator

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    claims_path = argv[0] if len(argv) > 0 else 'claims-coaching.json'
    facts_path = argv[1] if len(argv) > 1 else 'facts.json'
    facts = json.load(open(facts_path))
    claims = json.load(open(claims_path))
    evaluate = ClaimEvaluator(facts)
    npass = nfail = 0
    for c in claims:
        cid = c.get('id', '?')
        try:
            res = evaluate(c['python_check'])
        except Exception as e:
            print(f"FAIL {cid}: ERROR {type(e).__name__}: {e}")
            nfail += 1
            continue
        if res is True:
            npass += 1
            print(f"PASS {cid}: {c['english_gloss']}")
        else:
            print(f"FAIL {cid}: check returned {res!r} (not True)")
            nfail += 1
    print(f"\n{npass}/{len(claims)} claims pass, {nfail} fail")
    sys.exit(1 if nfail else 0)

if __name__ == '__main__':
    main()
