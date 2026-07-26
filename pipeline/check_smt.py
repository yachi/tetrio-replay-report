"""Gate: every claim in a session's claims.smt2 must answer `unsat`.

    python3 -m pipeline.check_smt sessions/2026-07-24/report
    python3 -m pipeline.check_smt <dir> --regen          # byte-identity with codegen
    python3 -m pipeline.check_smt <dir> --mutate 8       # anti-vacuity

`unsat` on the negation means the claim holds on this data. A `sat` means it is
false; `unknown` means the solver gave up, which counts as a failure here — an
unanswered claim must never read as a proved one.

Every solver found on PATH is run, and each must agree. That is the point of the
SMT backend: two independently implemented solvers checking one standard file is a
stronger statement than one toolchain checking its own output, in the same way two
extractors agreeing beats one extractor being careful.

`--mutate` perturbs constants in the committed file and requires each perturbation
to turn some claim `sat`. Without it, a file of vacuous claims would pass. The
perturbation escalates (+1, then past the nearest band edge, then far away) because
many predicates pin a *displayed* value and so hold across a range on purpose —
`135000 <= v < 136000` survives +1 by design, and calling that a survivor would be
a false alarm.
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys

SOLVERS = ("z3", "cvc5")
DEFINE = re.compile(r"^\(define-fun (\w+) \(\) Int (-?\d+)\)$", re.M)


def solvers_available(only=None):
    if only:
        return [only] if shutil.which(only) else []
    return [s for s in SOLVERS if shutil.which(s)]


def run(solver, text):
    """[(claim id, answer)] in file order."""
    proc = subprocess.run([solver, "-in"], input=text, capture_output=True, text=True)
    out = proc.stdout.split()
    pairs, pending = [], None
    for tok in out:
        if tok in ("sat", "unsat", "unknown"):
            pairs.append((pending, tok))
            pending = None
        else:
            pending = tok.strip('"')
    if not pairs and proc.returncode != 0:
        raise SystemExit(f"{solver} failed: {proc.stderr.strip()[:200]}")
    return pairs


def check(path, only=None):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    found = solvers_available(only)
    if not found:
        print(f"FAIL no SMT solver on PATH (looked for {', '.join(SOLVERS)})",
              file=sys.stderr)
        return 1
    missing = [s for s in SOLVERS if s not in found]
    bad = 0
    for solver in found:
        pairs = run(solver, text)
        wrong = [(cid, ans) for cid, ans in pairs if ans != "unsat"]
        for cid, ans in wrong:
            print(f"FAIL {os.path.basename(path)} {cid}: {ans} (expected unsat)",
                  file=sys.stderr)
        bad += len(wrong)
        if not wrong:
            print(f"  ok  {solver} — {len(pairs)} claims, all unsat")
    for s in missing:
        print(f"  --  {s} not installed, so this run is single-solver")
    return 1 if bad else 0


def regen(report_dir):
    """The committed file must be exactly what codegen emits now."""
    from . import codegen_smt
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    with open(os.path.join(report_dir, "claims-generated.json"), encoding="utf-8") as fh:
        claims = json.load(fh)
    text, _ = codegen_smt.emit(facts, claims)
    path = os.path.join(report_dir, "claims.smt2")
    with open(path, encoding="utf-8") as fh:
        committed = fh.read()
    if text != committed:
        print(f"FAIL {path} is not what codegen_smt emits — regenerate it",
              file=sys.stderr)
        return 1
    print(f"  ok  {os.path.basename(path)} reproduces byte-for-byte from facts.json")
    return 0


def mutate(path, count, only=None, seed=7):
    """Perturb constants; each must falsify at least one claim."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    consts = DEFINE.findall(text)
    if not consts:
        print("FAIL no integer constants to mutate", file=sys.stderr)
        return 1
    found = solvers_available(only)
    if not found:
        print("FAIL no SMT solver on PATH", file=sys.stderr)
        return 1
    solver = found[0]
    rng = random.Random(seed)
    picks = rng.sample(consts, min(count, len(consts)))
    survivors = []
    for name, val in picks:
        v = int(val)
        killed_by = None
        # Escalate: many predicates pin a displayed value to a band on purpose, so
        # +1 legitimately keeps them true. Only a datum that survives every step is
        # a real survivor.
        for step in (1, 1000, max(abs(v) * 2, 10 ** 6)):
            probe = text.replace(f"(define-fun {name} () Int {val})",
                                 f"(define-fun {name} () Int {v + step})", 1)
            pairs = run(solver, probe)
            hits = [cid for cid, ans in pairs if ans == "sat"]
            if hits:
                killed_by = (step, hits[:3], len(hits))
                break
        if killed_by:
            step, ids, n = killed_by
            print(f"  ok  {name} +{step} falsifies {n} claim(s) {ids}")
        else:
            survivors.append(name)
            print(f"FAIL {name} survives every perturbation — no claim depends on it",
                  file=sys.stderr)
    if survivors:
        print(f"\n{len(survivors)} constant(s) no claim depends on: a mutation that "
              "cannot be killed means the data is decorative", file=sys.stderr)
        return 1
    print(f"  ok  mutation: {len(picks)}/{len(picks)} perturbations falsified a claim")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    ap.add_argument("--solver", help="use only this solver")
    ap.add_argument("--regen", action="store_true",
                    help="also check the file reproduces from facts.json")
    ap.add_argument("--mutate", type=int, metavar="N",
                    help="also perturb N constants and require each to break a claim")
    args = ap.parse_args(argv)

    path = os.path.join(args.report_dir, "claims.smt2")
    if not os.path.exists(path):
        print(f"FAIL {path} does not exist — run pipeline.codegen_smt", file=sys.stderr)
        return 1

    rc = check(path, args.solver)
    if args.regen:
        rc |= regen(args.report_dir)
    if args.mutate:
        rc |= mutate(path, args.mutate, args.solver)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
