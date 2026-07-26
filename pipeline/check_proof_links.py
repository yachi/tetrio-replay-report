"""Gate: every proof-map entry must name a lemma that actually exists.

    python3 -m pipeline.check_proof_links sessions/2026-07-24/report
    python3 -m pipeline.check_proof_links <dir> --map claims-generated-proof-map.json \
        --dafny-dir "$RUNNER_TEMP/dfy"

A badge in the report links a claim to its lemma through this map. Nothing checked
that the lemma was still there, and `codegen` derives lemma *names* from each
claim's `english_gloss` — so editing a gloss renames the lemma and silently
strands the map's entry. That happened: correcting rounded figures in 14 glosses
left 8 entries pointing at names that no longer existed, while the verifier still
reported 0 errors and the status gate still counted 54/54 verified. A link to a
nonexistent lemma is exactly the decorative proof this repo exists to prevent.

The generated ledger's lemmas are not committed — CI generates and verifies them
into a temp directory — so its map is only checked when `--map` names it together
with the `--dafny-dir` they were generated into. That exclusion is explicit rather
than a silent skip.
"""
import argparse
import glob
import json
import os
import re
import sys

GENERATED_MAP = "claims-generated-proof-map.json"
LEMMA = re.compile(r"^\s*lemma\s+([A-Za-z0-9_]+)\s*\(", re.M)


def lemmas_in(dafny_dir):
    names = set()
    for path in sorted(glob.glob(os.path.join(dafny_dir, "*.dfy"))):
        with open(path, encoding="utf-8") as fh:
            names.update(LEMMA.findall(fh.read()))
    return names


def rows_of(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else [dict(v, id=k) for k, v in data.items()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    ap.add_argument("--dafny-dir", help="default <report_dir>/dafny")
    ap.add_argument("--map", action="append", dest="maps",
                    help="proof map filename; repeatable. Default: every "
                         f"*proof-map*.json except {GENERATED_MAP}")
    args = ap.parse_args(argv)

    dafny_dir = args.dafny_dir or os.path.join(args.report_dir, "dafny")
    names = lemmas_in(dafny_dir)
    if not names:
        print(f"FAIL no lemmas found in {dafny_dir}", file=sys.stderr)
        return 1

    if args.maps:
        maps = [os.path.join(args.report_dir, m) for m in args.maps]
    else:
        maps = [p for p in sorted(glob.glob(os.path.join(args.report_dir, "*proof-map*.json")))
                if os.path.basename(p) != GENERATED_MAP]
        skipped = [p for p in sorted(glob.glob(os.path.join(args.report_dir, "*proof-map*.json")))
                   if os.path.basename(p) == GENERATED_MAP]
        for p in skipped:
            print(f"  --  {os.path.basename(p)} not checked here — its lemmas are "
                  "generated, not committed (CI checks it against the generated dir)")

    bad = 0
    for path in maps:
        if not os.path.exists(path):
            print(f"FAIL {path} does not exist", file=sys.stderr)
            bad += 1
            continue
        rows = rows_of(path)
        named = [r for r in rows if r.get("lemma")]
        stale = [r for r in named if r["lemma"] not in names]
        for r in stale:
            print(f"FAIL {os.path.basename(path)} {r['id']}: lemma "
                  f"{r['lemma']!r} is not in {dafny_dir}", file=sys.stderr)
        bad += len(stale)
        if not stale:
            print(f"  ok  {os.path.basename(path)} — {len(named)}/{len(rows)} entries "
                  f"name a lemma, all present in {os.path.basename(dafny_dir)}")
    if bad:
        print(f"\n{bad} proof link(s) point at a lemma that does not exist — "
              "rebuild the proof map from real verifier output", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
