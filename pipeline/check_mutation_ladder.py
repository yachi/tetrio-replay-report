"""Gate: the two anti-vacuity ladders agree.

    python3 -m pipeline.check_mutation_ladder            # the gate
    python3 -m pipeline.check_mutation_ladder --selftest # its controls

This repo asks one question of its claims twice. `check_smt --mutate` perturbs a
constant in `claims.smt2` and requires some claim to turn `sat`; `mutation_test.sh`
perturbs the same datum in `Facts.dfy` and requires `dafny verify` to fail. Two
implementations of one question is the house method — it is the dual-extractor
argument applied to the proof side — and nothing here proposes collapsing them.

What it does propose is that they must not silently disagree about the OPERATOR, and
until 2026-09-21 they did. `check_smt.perturbations` escalates both ways because many
claims are one-sided; `mutation_test.sh` escalated upward only, `+1` then
`v*10 + 100000`. A one-sided claim with the mutated datum on the winning side survives
every increase, so the Dafny harness reported a constrained datum as an unconstrained
one — a false alarm rather than a vacuous lemma, and a red weekly build on
2026-09-19's `m13_r2_yachi_finesse_perfect`. Both gates were green for months and both
implementations were internally consistent; the prose recording the lesson named SMT
alone, so the document was accurate and the other gate was wrong.

**What would have to be true for this to fire?** Someone edits one ladder and not the
other. No other gate in this repo reads both: `check_smt` never opens the shell script
and `mutation_test.sh` never imports Python. That is the screening question this repo
asks before any new check, and this is a direction nothing else covers.

Two decisions worth keeping:

* **Containment, not equality.** The shell ladder keeps its own `v*10 + 100000` rung,
  which makes it a SUPERSET of the SMT one — and a superset is exactly what keeps the
  repair safe: a kill is the first rung that breaks verification, so no mutant that
  died under the old ladder can survive under the new one. What is enforced is that
  the shell ladder is never WEAKER, i.e. that every SMT rung still appears in it, in
  order. Subsequence rather than set containment, because the order decides which
  perturbation gets reported as the smallest one that falsified something.

* **Scope is MEASUREMENTS, and the categorical side is deliberately not compared.**
  `check_smt.perturbations` answers a coded constant with the other codes, which it can
  do because `claims.smt2` carries a legend. `Facts.dfy` has no legend, so
  `mutation_test.sh` flips a winner to a name no category holds — a different operator
  for a different reason, not drift. Widening this gate to cover it would mean
  asserting an agreement that should not hold.

* **The shell side PRINTS its ladder; this file does not parse it.**
  `mutation_test.sh --ladder <v>` needs no dafny-dir and no dafny. Reading the `for`
  line out of the script instead would be a gate a reformat breaks, which is a gate
  whose normal state is red — the objection this repo already recorded against
  recomputing the repertoire bands.
"""
import os
import subprocess
import sys

from pipeline.check_smt import perturbations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELL = os.path.join(ROOT, "pipeline", "mutation_test.sh")

# Every shape the two ladders can differ on, not a round number of samples: zero (where
# the `0` rung is a no-op on both sides), one and two (where `v - 1` and `v - 1000` go
# negative), the value that produced the red build, the two collision points the shell
# ladder dedups at (`v - 1000 == 0` at 1000, `v + 1000000 == v*10 + 100000` at 100000)
# and their neighbours, and a score-sized value where the two "far up" rungs are far
# apart. A uniform draw would have missed all four boundaries.
VALUES = [0, 1, 2, 12, 156, 999, 1000, 1001, 99_999, 100_000, 100_001, 543_210]


def shell_ladder(value):
    """What `mutation_test.sh` will actually try for `value`, in order."""
    out = subprocess.run(["bash", SHELL, "--ladder", str(value)],
                         capture_output=True, text=True, check=True).stdout
    rungs = [int(tok) for tok in out.split()]
    if not rungs:
        raise SystemExit(f"FAIL {SHELL} --ladder {value} printed nothing")
    return rungs


def is_subsequence(needles, haystack):
    """Every element of `needles`, in that order, somewhere in `haystack`."""
    it = iter(haystack)
    return all(any(h == n for h in it) for n in needles)


def compare(value, shell):
    """None if the shell ladder covers the SMT one for `value`, else why not."""
    smt = perturbations(value, False, [])
    if is_subsequence(smt, shell):
        return None
    missing = [r for r in smt if r not in shell]
    if missing:
        return f"shell ladder drops {missing}"
    return "shell ladder reorders the SMT rungs"


def check():
    bad = 0
    for value in VALUES:
        shell = shell_ladder(value)
        why = compare(value, shell)
        if why:
            print(f"FAIL v={value}: {why}\n"
                  f"     smt   {perturbations(value, False, [])}\n"
                  f"     shell {shell}", file=sys.stderr)
            bad += 1
    if bad:
        print(f"\n{bad} value(s) where mutation_test.sh is WEAKER than "
              "check_smt --mutate: the two gates ask one question and must not "
              "disagree about the operator", file=sys.stderr)
        return 1
    print(f"  ok  mutation ladders agree: mutation_test.sh covers every "
          f"check_smt.perturbations rung, in order, over {len(VALUES)} values")
    return 0


def selftest():
    """A gate nothing can break is a comment. These are the breakages it must catch."""
    cases = [
        # the ladder this harness actually had until 2026-09-21
        ("upward only", lambda v: [v + 1, v * 10 + 100000], 156),
        # the one-sided rung alone is not enough either
        ("no zero, no far-down", lambda v: [v + 1, v - 1, v + 1000, v + 1000000], 156),
        # same rungs, wrong order: the reported "smallest" perturbation would be wrong
        ("reordered", lambda v: list(reversed(perturbations(v, False, []))), 156),
    ]
    bad = 0
    for name, ladder, value in cases:
        if compare(value, ladder(value)) is None:
            print(f"FAIL control '{name}' was not caught at v={value}", file=sys.stderr)
            bad += 1
        else:
            print(f"  ok  control '{name}' caught at v={value}")
    # ... and the live ladder must NOT be caught, or a uniform verdict would hide both
    live = shell_ladder(156)
    if compare(156, live) is not None:
        print("FAIL the live ladder is reported as weak — a uniform verdict is the "
              "signature of a broken harness", file=sys.stderr)
        bad += 1
    else:
        print("  ok  control 'the live ladder' passes")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else check())
