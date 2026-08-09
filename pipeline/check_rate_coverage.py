"""Every short round's rate constants must still be pinned by some claim.

    python3 -m pipeline.check_rate_coverage sessions/2026-08-01/report

`generators.QUALIFYING_MS` keeps short rounds out of the APM/VS records, because a
rate over a 12-second round is a sample mean over a small n rather than a peak (see
the constant's own comment, and `analysis/rate_records.R`). That qualifier carves a
hole the moment it is written: the record's "nobody exceeds it" conjuncts stop
ranging over short rounds, so a short round's APM/VS constant can be raised without
falsifying anything. Its only other constraint is "the round's winner had the higher
VS", which every increase preserves.

That is not hypothetical — it shipped for one commit, and `mutation_test.sh` caught
it only because a 14-constant random sample happened to land on `m6_r1_yachi_vs`.
Sampling is the wrong instrument for a hole with a known shape, so this walks the
whole class: every round under the threshold, both players, both rate fields,
mutated in both directions. Each one must falsify some claim.

`unqualified_rate_peaks` is what makes them pass — it keeps the unqualified maximum
in the ledger, bounding every round again, and states it as the burst it is instead
of as a record.
"""
import argparse
import json
import os
import sys

from pipeline import perturb
from pipeline.claims.generators import QUALIFYING_MS

# UPWARD only, and the direction is the whole point.
#
# "Some perturbation is caught" is too weak: "the round's winner had the higher VS"
# catches every DECREASE of a winner's VS, so an any-direction test reports ok even
# with the record ignoring short rounds entirely — measured, by deleting
# `unqualified_rate_peaks` and watching it still pass.
#
# Requiring BOTH directions is too strong, and wrongly so: a round LOSER's VS has
# never been pinned from below in any session, because no claim says a beaten player
# scored at least X — there is no such fact worth stating, and inventing one to make
# a gate green would be writing the claim for the checker rather than the reader.
# That gap predates the qualifier and is not what this file is about.
#
# What the qualifier actually removed is the upper bound: before it, raising any
# rate above the session max falsified the record. That is the property restored by
# `unqualified_rate_peaks`, and the one thing checked here.
UP = (1, 1000, 10**6)
RATE_FIELDS = ("apm_x1000", "vs_x1000")


def _false_claims(claims, facts):
    out = []
    for c in claims:
        try:
            if not eval(c["python_check"], {"facts": facts}):
                out.append(c["id"])
        except Exception:                      # a raising predicate is a falsified one
            out.append(c["id"])
    return out


def _ledgers(report_dir):
    claims = []
    for name in sorted(os.listdir(report_dir)):
        if (name.startswith("claims") and name.endswith(".json")
                and "proof-map" not in name):
            with open(os.path.join(report_dir, name), encoding="utf-8") as fh:
                claims += json.load(fh)
    return claims


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    args = ap.parse_args(argv)

    with open(os.path.join(args.report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    claims = [c for c in _ledgers(args.report_dir) if "python_check" in c]
    if not claims:
        print(f"FAIL {args.report_dir}: no ledger with python_check found", file=sys.stderr)
        return 1

    baseline = _false_claims(claims, facts)
    if baseline:
        print(f"FAIL {args.report_dir}: ledger does not hold on its own facts "
              f"({', '.join(baseline[:5])})", file=sys.stderr)
        return 1

    short = [(mi, ri) for mi, m in enumerate(facts["matches"])
             for ri, r in enumerate(m["rounds"])
             if max(d["lifetime"] for d in r["players"].values()) < QUALIFYING_MS]

    checked, holes = 0, []
    pristine = perturb.fingerprint(facts)
    for mi, ri in short:
        for pl in facts["players"]:
            for f in RATE_FIELDS:
                checked += 1
                base = facts["matches"][mi]["rounds"][ri]["players"][pl][f]
                if not _pinned_from_above(claims, facts, mi, ri, pl, f, base):
                    holes.append(f"m{mi + 1}r{ri + 1} {pl} {f} = {base} "
                                 f"— raising it falsifies no claim")
    # A missed restore would leave later rounds checked against a raised constant, which
    # makes the gate MORE likely to pass — the direction that hides a hole rather than
    # inventing one. Asserted, not assumed.
    assert perturb.unchanged(facts, pristine), \
        "the perturbation sweep did not restore facts — later rounds were judged " \
        "against a corrupted baseline"

    if holes:
        print(f"FAIL {args.report_dir}: {len(holes)} short-round rate constant(s) are "
              f"unconstrained — some claim must bound them, or the qualifier has "
              f"removed them from the proof entirely:", file=sys.stderr)
        for h in holes:
            print(f"  {h}", file=sys.stderr)
        return 1

    print(f"  ok  {len(short)} rounds under {QUALIFYING_MS // 1000}s; raising any of "
          f"their {checked} APM/VS constants falsifies a claim")
    return 0


def _pinned_from_above(claims, facts, mi, ri, pl, f, base):
    """True if SOME increase of this constant falsifies SOME claim.

    Raising the value used to mean `copy.deepcopy(facts)` — a 300-480 KB rebuild to write
    one integer, and 68 % of this gate's runtime. `perturb.perturbed` writes it in place
    and puts it back; `main` fingerprints the tree either side of the whole sweep, because
    a restore that silently misses a site would leave later rounds judged against a
    corrupted baseline. See `pipeline/perturb.py`.
    """
    p = facts["matches"][mi]["rounds"][ri]["players"][pl]
    for d in UP:
        with perturb.perturbed([(p, f, base + d)]):
            if _false_claims(claims, facts):
                return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
