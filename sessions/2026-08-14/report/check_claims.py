#!/usr/bin/env python3
"""Verify every claim's python_check evaluates True against facts.json.
Usage: python3 check_claims.py claims-coaching.json [facts.json]
"""
import json, sys, math, statistics

def main():
    claims_path = sys.argv[1] if len(sys.argv) > 1 else 'claims-coaching.json'
    facts_path = sys.argv[2] if len(sys.argv) > 2 else 'facts.json'
    facts = json.load(open(facts_path))
    claims = json.load(open(claims_path))
    env = {'facts': facts, 'math': math, 'statistics': statistics}
    npass = nfail = 0
    for c in claims:
        cid = c.get('id', '?')
        try:
            res = eval(c['python_check'], env)
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
