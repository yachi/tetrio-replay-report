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
to turn some claim `sat`. Without it, a file of vacuous claims would pass.

The operator depends on what the constant *is*:

* **measurements** escalate in BOTH directions — +1, -1, +1000, -1000, far up, then
  0 — because many predicates pin a displayed value to a band on purpose
  (`135000 <= v < 136000` survives +1 by design), and many others are one-sided.
  `m4_r3_pinglamb_inputs` feeds "yachi's keys-per-piece is lower than pinglamb's":
  raising pinglamb's keypresses keeps that true no matter how far, and only
  lowering it falsifies anything. An increase-only operator called it a survivor.
* **categorical codes** (the string legend: a winner, a game-over reason) are
  perturbed to *another code*, never by an offset. Claims over these count members
  of a category, so moving `5` (winner) to `6` changes no count — the round was not
  being counted either way. Moving it to `3` (garbagesmash) is the mutation that
  means something. CI caught exactly this: `m5_r2_yachi_gameoverreason` survived
  every numeric offset while G065 ("42 rounds ended by garbagesmash, 8 by topout")
  went on holding, because none of 6, 1005 or 10⁶ is a death reason either.
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

# Every SMT-LIB 2 front end worth trying, in order of preference, with the argv
# each one needs. They genuinely differ: z3 reads stdin only with `-in`, cvc5 needs
# `--incremental` before it will honour the push/pop this file uses, and yices2's
# binary is called `yices-smt2`. The file is passed as a path, which all of them
# accept, rather than piped.
SOLVERS = {"z3": [],
           "cvc5": ["--incremental"],
           "yices-smt2": ["--incremental"]}
DEFINE = re.compile(r"^\(define-fun (\w+) \(\) Int (-?\d+)\)", re.M)
# The legend codegen_smt writes above the definitions: `; 3 = garbagesmash`.
LEGEND = re.compile(r"^; (\d+) = (\S+)$", re.M)
# A coded constant is marked by the trailing label the emitter writes:
#   (define-fun m5_r2_yachi_gameoverreason () Int 5)  ; winner
# Detecting them by NAME is the point: an earlier version detected them by whether
# the VALUE fell in the code range, which quietly reclassified small measurements —
# a topcombo of 4 was "the code for topout" and got mutated to 1/2/3/5, none of
# which crosses the `> 6` threshold its claim tests. Six real measurements looked
# like survivors because of it.
CODED = re.compile(r"^\(define-fun (\w+) \(\) Int (-?\d+)\)\s+; \S+", re.M)
# Claim ids as the ledgers assign them: C001, R014, G077.
CLAIM_ID = re.compile(r"[A-Z]\d{3,}")


def solvers_available(only=None):
    if only:
        return [only] if shutil.which(only) else []
    return [s for s in SOLVERS if shutil.which(s)]


def argv_for(solver, path):
    return [solver, *SOLVERS.get(solver, []), path]


def run(solver, text):
    """([(claim id, answer)], [solver errors]) — line-based, on purpose.

    An earlier token-based version treated the words inside `(error "logic does not
    support nonlinear arithmetic")` as claim ids and answers, so a file the solver
    had REFUSED read as a file full of kills. Errors are now collected and are a
    failure in their own right.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".smt2", encoding="utf-8",
                                     delete=False) as fh:
        fh.write(text)
        tmp = fh.name
    try:
        proc = subprocess.run(argv_for(solver, tmp), capture_output=True, text=True)
    finally:
        os.unlink(tmp)
    pairs, errors, pending = [], [], None
    for line in (proc.stdout + "\n" + proc.stderr).splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("(error") or line.startswith("error"):
            errors.append(line[:120])
        elif line in ("sat", "unsat", "unknown"):
            pairs.append((pending, line))
            pending = None
        elif CLAIM_ID.fullmatch(line.strip('"')):
            pending = line.strip('"')
    if not pairs and proc.returncode != 0 and not errors:
        raise SystemExit(f"{solver} failed: {proc.stderr.strip()[:200]}")
    return pairs, errors


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
        pairs, errors = run(solver, text)
        for err in errors[:5]:
            print(f"FAIL {solver}: {err}", file=sys.stderr)
        if errors:
            print(f"FAIL {solver} reported {len(errors)} error(s) — the file was not "
                  f"fully answered", file=sys.stderr)
            bad += len(errors)
            continue
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


def perturbations(value, coded, codes):
    """The values worth trying for this constant, in order.

    A categorical code gets the other codes; a measurement gets escalating offsets.
    `coded` says which it is — read from the constant's name, never its value.
    """
    if coded:
        return [c for c in sorted(codes) if c != value]
    tries = [value + 1, value - 1, value + 1000, value - 1000,
             value + 10 ** 6, 0]
    seen, out = {value}, []
    for t in tries:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def field_of(name):
    """The kind of datum a constant name denotes: `topcombo`, `winner`, `ge`, ...

    Both mutation bugs this gate has had were confined to a KIND — coded strings,
    then one-sided measurements — so the sample is stratified by kind rather than
    drawn uniformly, where a whole kind can go untouched.
    """
    stem = re.sub(r"^m\d+_(r\d+_)?", "", name)
    stem = re.sub(r"^(yachi|pinglamb)_", "", stem)
    stem = re.sub(r"^lb_(yachi|pinglamb)_", "lb_", stem)
    stem = re.sub(r"^score(Yachi|Pinglamb)$", "score", stem)
    return re.sub(r"ge\d+$", "ge", stem)


def stratified(consts, count, rng):
    """`count` constants, spread across kinds: round-robin over shuffled groups."""
    groups = {}
    for name, val in consts:
        groups.setdefault(field_of(name), []).append((name, val))
    for g in groups.values():
        rng.shuffle(g)
    picks, order = [], sorted(groups)
    while len(picks) < count and any(groups[k] for k in order):
        for k in order:
            if groups[k]:
                picks.append(groups[k].pop())
                if len(picks) == count:
                    break
    return picks


def mutate(path, count, only=None, seed=7):
    """Perturb constants; each must falsify at least one claim."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    codes = {int(n) for n, _v in LEGEND.findall(text)}
    coded_names = {n for n, _v in CODED.findall(text)}
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
    picks = stratified(consts, min(count, len(consts)), rng)
    survivors = []
    for name, val in picks:
        v = int(val)
        killed_by = None
        coded = name in coded_names
        for new in perturbations(v, coded, codes):
            probe = text.replace(f"(define-fun {name} () Int {val})",
                                 f"(define-fun {name} () Int {new})", 1)
            pairs, errors = run(solver, probe)
            if errors:
                raise SystemExit(f"{solver} errored on a mutant: {errors[0]}")
            hits = [cid for cid, ans in pairs if ans == "sat"]
            if hits:
                killed_by = (new, hits[:3], len(hits))
                break
        if killed_by:
            new, ids, n = killed_by
            how = f"->{new}" if coded else f"+{new - v}"
            print(f"  ok  {name} {how} falsifies {n} claim(s) {ids}")
        else:
            survivors.append(name)
            print(f"FAIL {name} survives every perturbation — no claim depends on it",
                  file=sys.stderr)
    if survivors:
        print(f"\n{len(survivors)} constant(s) no claim depends on: a mutation that "
              "cannot be killed means the data is decorative", file=sys.stderr)
        return 1
    kinds = len({field_of(n) for n, _v in picks})
    print(f"  ok  mutation: {len(picks)}/{len(picks)} perturbations falsified a claim "
          f"across {kinds} kinds of datum")
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
