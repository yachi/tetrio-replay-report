"""Generate a claim ledger from a session's facts.json.

    python3 -m pipeline.claims.build_claims sessions/2026-07-24/report/facts.json \
        --out sessions/2026-07-24/report/claims-generated.json

Runs every family in generators.py, assigns stable ids, renders each spec to a Python
predicate (and keeps the spec so codegen.py can render the Dafny lemma from the same
source), then refuses to emit unless:

  * every predicate evaluates True against the facts it was generated from
  * no claim's text contains a Simplified character (the reports are traditional)
  * no two claims are byte-identical

A generated ledger is a floor, not a ceiling: hand-written claims for whatever is
genuinely unique about a session are added alongside it.
"""
import argparse
import json
import sys
import unicodedata

from .generators import FAMILIES
from .spec import to_python

# Characters that are Simplified-only and have appeared in review findings.
SIMPLIFIED = set("净实约见对话说这两来国过时开关闭个们后现点为无产爱东车电龙")


def generate(facts, prefix="G"):
    claims = []
    for fn in FAMILIES:
        produced = fn(facts) or []
        for c in produced:
            claims.append(dict(c))
    for i, c in enumerate(claims, start=1):
        c["id"] = f"{prefix}{i:03d}"
    return claims


def render(claims):
    for c in claims:
        c["python_check"] = to_python(c["spec"])
    return claims


def validate(claims, facts):
    problems = []
    seen = {}
    for c in claims:
        try:
            ok = bool(eval(c["python_check"], {"__builtins__": __builtins__}, {"facts": facts}))
        except Exception as exc:  # noqa: BLE001 - report, do not mask
            problems.append(f"{c['id']} ({c['family']}): predicate raised {exc!r}")
            continue
        if not ok:
            problems.append(f"{c['id']} ({c['family']}): predicate evaluated False")
        bad = sorted(set(c["canto"]) & SIMPLIFIED)
        if bad:
            problems.append(f"{c['id']} ({c['family']}): simplified glyph(s) {bad} in canto")
        for ch in c["canto"]:
            if unicodedata.category(ch) == "Co":
                problems.append(f"{c['id']}: private-use character in canto")
        key = c["python_check"]
        if key in seen:
            problems.append(f"{c['id']} duplicates {seen[key]} (identical predicate)")
        else:
            seen[key] = c["id"]
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("facts", help="path to facts.json")
    ap.add_argument("--out", help="where to write the ledger (default: stdout summary only)")
    ap.add_argument("--prefix", default="G", help="claim id prefix (default G)")
    args = ap.parse_args(argv)

    with open(args.facts, encoding="utf-8") as fh:
        facts = json.load(fh)

    claims = render(generate(facts, args.prefix))
    problems = validate(claims, facts)

    by_family = {}
    for c in claims:
        by_family.setdefault(c["family"], 0)
        by_family[c["family"]] += 1

    print(f"generated {len(claims)} claims from {len(FAMILIES)} families")
    for fam, n in sorted(by_family.items()):
        print(f"  {n:3d}  {fam}")

    if problems:
        print(f"\nREFUSING TO EMIT — {len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print(f"\nall {len(claims)} predicates evaluate True; no simplified glyphs; no duplicates")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(claims, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
