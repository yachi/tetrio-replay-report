"""Gate: every claim must be falsifiable by SOME fact base — the per-lemma dual of
`check_smt --mutate`.

    python3 -m pipeline.check_lemma_vacuity sessions/2026-07-24/report
    python3 -m pipeline.check_lemma_vacuity <dir> --probe 12   # wider witness search

`check_smt --mutate` asks a question about **constants**: perturb one, does *some*
claim turn `sat`? That cannot see a decorative **lemma**. If a claim's constants are
load-bearing in a *different* claim, the constant dies there and the sweep reports
"all killed" while the claim itself pins nothing. Measured on a 17-lemma prototype:
per-constant mutation said 32/32 killed, 0 survivors, while 3 of the 17 lemmas were
tautologies — their bounds written with literals (`154 * 317 <= 1000 * 49`) instead
of over the constants. ROADMAP P4 records the same class from the other end:
`total_rounds` rendered to Dafny as a literal, so "the session had 50 rounds" was
the tautology `50 == 50`.

`check_dead_consts` covers the dual case — a constant no lemma reads. Neither gate
covers the other; this one closes the third corner:

| | asks | misses |
|---|---|---|
| `check_smt --mutate` | is this **constant** read by some claim? | a claim that reads nothing |
| `check_dead_consts`  | is this **constant** read by some lemma? | a lemma that reads nothing |
| this                 | is this **claim** falsifiable at all?    | — |

**Why SMT and not Dafny.** The check is inherently O(claims x constants). CLAUDE.md
measures z3 on `claims.smt2` at ~40 ms against Dafny's ~4.6 s for the same claims, so
the Dafny route would cost hours per session. Everything here reuses `check_smt`'s
machinery — its solver table and argv, its line-based parser, its stratified sampler
and its perturbation operator — rather than growing a second copy that drifts.

**Three passes, and the verdict is the second one.**

1. *grounded* — every claim rebuilt from this module's own parse, with the committed
   values pinned, must be present and answer `unsat`. This is the harness checking
   itself: the first version of this gate reported every lemma vacuous because a name
   was mis-extracted and no lemma was ever emitted, and a verifier handed zero lemmas
   prints "0 verified, 0 errors" and exits 0. A verdict is only meaningful once the
   unmutated claim has been seen to hold.
2. *free* — the constants the claim reads become free integers over the realisable
   domain (measurements non-negative — no constant in any committed artefact is
   negative; coded constants restricted to the legend), and the negation is asserted.
   `sat` means some fact base falsifies the claim. **`unsat` means none does: the
   claim is a tautology, and proving it says nothing about the data.**
3. *probe* — the stratified single-constant operator from `check_smt`, run for a
   concrete witness: which real constant, moved to which real value, flips this claim.
   A claim that pass 2 calls falsifiable but no single-constant perturbation reaches
   is reported (`weak`), because the operator the repo's other gates use cannot see it.

Pass 2 subsumes pass 3 logically — if no fact base falsifies a claim then no
perturbation does — so the two disagreeing is a harness bug, and is raised as one.

**Self-validation is not optional.** A uniform verdict (all dead or all alive) is the
signature of a broken harness, never a finding, so three control claims ride through
the identical code path on every run: two deliberately vacuous ones that must be
flagged (a literal-only bound, and a tautology that *does* read a constant — so
"references something" cannot be mistaken for "depends on something"), and one that
pins a real constant and must not be. A green run is discrimination, not silence.
"""
import argparse
import os
import re
import sys
import time

from .check_smt import (CODED, DEFINE, LEGEND, SOLVERS, perturbations, run,
                        solvers_available, stratified)

# Per-query time limit, one entry per name in `check_smt.SOLVERS` — that dict stays
# the single list of solvers and their argv; this only adds the option each one
# spells differently. It is needed because the free-constant pass is genuinely hard:
# z3 answers all 78 of 2026-07-24's claims in 0.2 s, cvc5 needs 60 s and gives up on
# three. Without a limit cvc5 does not terminate on that file at all. A solver with
# no entry here is NAMED and skipped rather than run unbounded, because a gate that
# hangs is worse than one that says what it could not do.
LIMITS = {"z3": "(set-option :timeout {ms})",
          "cvc5": "(set-option :tlimit-per {ms})",
          "yices-smt2": None}

# Constants as codegen_smt names them: m3_r2_yachi_apm, m0_scoreYachi, m4_nrounds.
# Intersected with the file's own definitions before use, so a stray match in a
# comment cannot invent a reference.
NAME = re.compile(r"\bm\d+_[A-Za-z0-9_]+\b")
# `; G014 [round_totals] 53 rounds total; yachi won 28` — the line codegen_smt writes
# above each block. The gloss is what makes a finding readable, so it is parsed, but
# its absence is never fatal: the claim id comes from the `(echo)`, which the solver
# echoes back and is therefore load-bearing.
GLOSS = re.compile(r"^; ([A-Z]\d{3,}) \[[^\]]*\] (.*)$")
# Control ids must satisfy check_smt's CLAIM_ID (`[A-Z]\d{3,}`) or its line-based
# parser drops them, which would silently un-test the harness's only self-test.
CONTROL_LITERAL, CONTROL_TAUTOLOGY, CONTROL_LIVE = "V997", "V998", "V999"
# The symbol a perturbed constant is renamed to inside a probe block. Deliberately
# outside `NAME`'s shape so it can never be mistaken for a fact constant.
MUT = "mutated__"


class Claim:
    """One `(push)/(assert (not ...))/(check-sat)/(pop)` block of claims.smt2."""

    def __init__(self, cid, gloss, asserts, refs, control=None):
        self.id = cid
        self.gloss = gloss
        self.asserts = asserts        # raw lines, verbatim from the artefact
        self.refs = refs              # constants it reads, in file order
        self.control = control        # None, "vacuous" or "live" — the expected verdict


class Artefact:
    def __init__(self, consts, coded, codes, claims):
        self.consts = consts          # {name: value}, in file order
        self.coded = coded            # names the emitter marked with a trailing `; label`
        self.codes = codes            # the legend's integer codes
        self.claims = claims


def parse(text):
    """claims.smt2 -> Artefact. Line-based, like check_smt's answer parser.

    Nothing here reads a value to decide what a constant *is*: coded-ness comes from
    the name the emitter marked, exactly as `check_smt` does it, because detecting it
    by value once reclassified a `topcombo` of 4 as "the code for topout".
    """
    consts = {n: int(v) for n, v in DEFINE.findall(text)}
    coded = {n for n, _v in CODED.findall(text)}
    codes = sorted({int(n) for n, _v in LEGEND.findall(text)})

    claims, lines, gloss = [], text.splitlines(), {}
    for line in lines:
        m = GLOSS.match(line)
        if m:
            gloss[m.group(1)] = m.group(2).strip()

    i = 0
    while i < len(lines):
        if lines[i].strip() != "(push 1)":
            i += 1
            continue
        cid, asserts, j = None, [], i + 1
        while j < len(lines) and lines[j].strip() != "(pop 1)":
            s = lines[j].strip()
            if s.startswith("(echo "):
                cid = s.split('"')[1]
            elif s.startswith("(assert "):
                asserts.append(lines[j])
            j += 1
        if j >= len(lines):
            raise SystemExit("claims.smt2: a (push 1) block is never closed by (pop 1)")
        if cid is None or not asserts:
            raise SystemExit(f"claims.smt2: a block near line {i + 1} has no "
                             f"{'(echo)' if cid is None else '(assert)'} — the parse is "
                             f"wrong, not the artefact")
        refs = [n for n in dict.fromkeys(NAME.findall("\n".join(asserts)))
                if n in consts]
        claims.append(Claim(cid, gloss.get(cid, ""), asserts, refs))
        i = j + 1
    return Artefact(consts, coded, codes, claims)


# --------------------------------------------------------------------------- #
# controls
# --------------------------------------------------------------------------- #


def controls(art):
    """Three claims whose verdicts are known, built from this artefact's own data.

    They are appended to the real claims and run through every pass unchanged, so a
    green report is the harness demonstrating it can tell the two apart rather than
    the harness having found nothing to say.
    """
    measured = [n for n in art.consts if n not in art.coded]
    if not measured:
        raise SystemExit("no measurement constant to build the controls from")
    x = measured[0]
    v = art.consts[x]
    return [
        # The prototype's actual bug: a bound stated over literals, so the lemma
        # holds whatever the session did. 154 * 317 = 48818 <= 49000.
        Claim(CONTROL_LITERAL, "control: a bound written with literals, never over "
              "the constants", ["(assert (not (<= (* 154 317) (* 1000 49))))"], [],
              control="vacuous"),
        # Reads a constant and still proves nothing — so "mentions a constant" is not
        # mistaken for "depends on one". This is the shape a cited-but-unused datum
        # takes, and it is the one a text search for the const name would clear.
        Claim(CONTROL_TAUTOLOGY, f"control: a tautology that does read {x}",
              [f"(assert (not (>= (* {x} {x}) 0)))"], [x], control="vacuous"),
        # Pins one real datum: must survive as live, or the gate flags everything.
        Claim(CONTROL_LIVE, f"control: pins {x} at its committed value",
              [f"(assert (not (= {x} {v})))"], [x], control="live"),
    ]


# --------------------------------------------------------------------------- #
# file builders — one shape, so a parse bug fails the baseline instead of hiding
# --------------------------------------------------------------------------- #


def _domain(art, name):
    """What values this constant may take in a realisable fact base.

    Measurements are non-negative: no `define-fun` in any committed artefact holds a
    negative value (they are counts, durations and rates), so this is read off the
    corpus rather than assumed. Coded constants take a legend code — the same
    restriction `check_smt`'s categorical operator uses, for the same reason: an
    offset produces a value that is not a category at all.
    """
    if name in art.coded:
        return "(assert (or " + " ".join(f"(= {name} {c})" for c in art.codes) + "))"
    return f"(assert (>= {name} 0))"


def _pinned(art, cid, claim, override=None):
    """One push/pop block with the claim's constants **defined** at their values.

    `define-fun` rather than `declare-fun` + `(assert (= x v))`: the two are logically
    the same and the second cost two orders of magnitude, because a definition is
    substituted at parse time while an equality has to be propagated by the solver.
    The first version of this gate used equalities and did not finish one session in
    two minutes; the same work with definitions takes a few seconds.

    `override` is `(name, value)` — the one constant this block perturbs. It is
    written as a fresh symbol substituted into the claim's own text, because the
    original name is already defined in this scope and SMT-LIB has no rebinding.
    """
    out = ["(push 1)", f'(echo "{cid}")']
    for n in claim.refs:
        out.append(f"(define-fun {n} () Int {art.consts[n]})")
    asserts = claim.asserts
    if override:
        name, val = override
        out.append(f"(define-fun {MUT} () Int {val})")
        asserts = [re.sub(rf"\b{name}\b", MUT, a) for a in asserts]
    return out + asserts + ["(check-sat)", "(pop 1)"]


def build_grounded(art, claims):
    """Every claim with its committed values pinned. All must answer `unsat`."""
    lines = ["(set-logic QF_NIA)"]
    for c in claims:
        lines += _pinned(art, c.id, c)
    return "\n".join(lines) + "\n"


def build_free(art, claims, domain=True):
    """Every claim over free constants. `unsat` here means nothing can falsify it."""
    lines = ["(set-logic QF_NIA)"]
    for c in claims:
        lines += ["(push 1)", f'(echo "{c.id}")']
        for n in c.refs:
            lines.append(f"(declare-fun {n} () Int)")
            if domain:
                lines.append(_domain(art, n))
        lines += c.asserts + ["(check-sat)", "(pop 1)"]
    return "\n".join(lines) + "\n"


def build_probes(art, claim, count, seed=7):
    """(text, {probe id: (const, new value)}) — the stratified single-constant sweep.

    The sample is stratified by kind of datum and the perturbations are
    `check_smt`'s, imported rather than re-written: both bugs that gate has had were
    confined to a kind (coded strings, then one-sided measurements), and a second
    implementation of the operator is a second thing to get wrong.
    """
    import random
    picks = stratified([(n, art.consts[n]) for n in claim.refs],
                       min(count, len(claim.refs)), random.Random(seed))
    lines, probes = ["(set-logic QF_NIA)"], {}
    for name, val in picks:
        for new in perturbations(int(val), name in art.coded, art.codes):
            pid = f"P{len(probes) + 1:04d}"
            probes[pid] = (name, new)
            lines += _pinned(art, pid, claim, override=(name, new))
    return "\n".join(lines) + "\n", probes


# --------------------------------------------------------------------------- #
# passes
# --------------------------------------------------------------------------- #


def usable(only=None):
    """The solvers on PATH this gate can bound, and the ones it had to leave out."""
    found = solvers_available(only)
    unknown = [s for s in found if s not in LIMITS]
    if unknown:
        raise SystemExit(f"no per-query time limit known for {', '.join(unknown)} — add "
                         f"it to LIMITS or this gate can hang instead of reporting")
    return ([s for s in found if LIMITS[s]],
            [s for s in SOLVERS if s not in found] +
            [s for s in found if not LIMITS[s]])


def answers(solver, text, expect, ms):
    """{id: answer}, with a solver error or a missing id treated as fatal.

    `check_smt.run` is line-based on purpose — a token-based version once read the
    words inside `(error "logic does not support nonlinear arithmetic")` as claim ids
    and reported a refused file as a file full of kills. Errors are surfaced here as
    a hard stop rather than folded into a verdict.
    """
    pairs, errors = run(solver, LIMITS[solver].format(ms=ms) + "\n" + text)
    if errors:
        raise SystemExit(f"{solver} errored, so nothing was checked: {errors[0]}")
    got = {}
    for cid, ans in pairs:
        if cid is None:
            raise SystemExit(f"{solver} answered {ans!r} with no id in front of it — "
                             f"the echo/check-sat pairing is broken")
        if cid in got:
            raise SystemExit(f"{solver} answered for {cid} twice — duplicate ids")
        got[cid] = ans
    missing = [c for c in expect if c not in got]
    if missing:
        raise SystemExit(f"{solver} never answered for {len(missing)} of {len(expect)} "
                         f"blocks ({', '.join(missing[:5])}) — a file that emits nothing "
                         f"also 'passes'")
    return got


def grounded_pass(art, claims, solvers, ms):
    """Assert every claim exists and holds before any of it is perturbed.

    Run on **every** available solver: it is the cheap pass (0.05 s for a session on
    either solver), and it is the one whose failure invalidates everything after it.
    """
    text = build_grounded(art, claims)
    ids = [c.id for c in claims]
    for solver in solvers:
        got = answers(solver, text, ids, ms)
        wrong = [(c, got[c]) for c in ids if got[c] != "unsat"]
        if wrong:
            sys.stdout.flush()
            for cid, ans in wrong[:5]:
                print(f"FAIL {cid}: {ans} on the unmutated data (expected unsat)",
                      file=sys.stderr)
            raise SystemExit("the baseline does not hold, so no vacuity verdict from "
                             "this run means anything")
    print(f"  ok  baseline — {len(ids)} claims rebuilt from the parse, all unsat "
          f"({', '.join(solvers)})")


def verdict(cid, named):
    """Combine one claim's raw answers. `named` is [(solver, answer)].

    A `sat` is self-certifying — the solver has an assignment of the constants that
    makes the claim false — so one of them settles the question. An `unsat` is a
    claim of absence, and two solvers contradicting each other means neither verdict
    can be reported.
    """
    got = [a for _s, a in named]
    if "sat" in got and "unsat" in got:
        raise SystemExit(f"solvers disagree on {cid}: "
                         f"{', '.join(f'{s}={a}' for s, a in named)} — one of them is "
                         f"wrong and this gate cannot say which")
    return ("falsifiable" if "sat" in got else
            "vacuous" if "unsat" in got else "unknown")


def free_answers(art, claims, solvers, ms, domain=True):
    """{solver: {id: raw answer}} over free constants — no verdict taken yet."""
    ids = [c.id for c in claims]
    text = build_free(art, claims, domain)
    return {s: answers(s, text, ids, ms) for s in solvers}


def in_domain(art, name, val):
    """Is this a value the extractors could actually produce for this constant?

    `check_smt`'s operator does not ask: it escalates a measurement to `v - 1000`,
    which for a value under 1000 is a negative APM. That is deliberate there — it is
    hunting for any constraint at all on a constant — but it means a `sat` from that
    operator is not by itself evidence that a claim says anything about a real
    session. The distinction is what separates the two findings this gate reports.
    """
    return val in art.codes if name in art.coded else val >= 0


class Witness:
    """What the stratified operator found for one claim."""

    def __init__(self, hits, tried):
        self.tried = tried
        self.hits = hits                        # [(const, value)] that turned it sat
        self.real = [h for h in hits if h[2]]   # ... at a value the corpus could hold
        self.best = (self.real or hits or [None])[0]

    def __bool__(self):
        return bool(self.real)


def probe_pass(art, claims, solver, count, ms):
    """{id: Witness} — a concrete perturbation that falsifies each claim.

    One solver invocation per claim rather than one per perturbation: the probes for
    a claim are independent push/pop blocks, so they answer in a single pass.
    """
    out = {}
    for c in claims:
        text, probes = build_probes(art, c, count)
        if not probes:
            out[c.id] = Witness([], 0)
            continue
        got = answers(solver, text, list(probes), ms)
        hits = [(*probes[p], in_domain(art, *probes[p]))
                for p in probes if got[p] == "sat"]
        out[c.id] = Witness(hits, len(probes))
    return out


def check_controls(art, verdicts, witness):
    """The controls must come out as designed, or the run is not evidence of anything."""
    for c in art.claims:
        if not c.control:
            continue
        got = verdicts[c.id]
        want = "vacuous" if c.control == "vacuous" else "live"
        if got != want:
            raise SystemExit(
                f"control {c.id} came out {got}, expected {want} — the harness cannot "
                f"tell a decorative claim from a load-bearing one, so its verdict on "
                f"the real claims is not evidence. ({c.gloss})")
        if c.control == "vacuous" and witness[c.id].hits:
            raise SystemExit(f"control {c.id} is a tautology but a perturbation "
                             f"falsified it — the two passes contradict each other")
        if c.control == "live" and not witness[c.id]:
            raise SystemExit(f"control {c.id} pins a committed value but no "
                             f"perturbation of it falsified the claim")
    print("  ok  controls — 2 planted tautologies flagged, 1 real claim not")


def classify(cid, loose, tight, w):
    """The verdict for one claim, from the two free passes and the witness.

    `loose` is over every integer, `tight` over the values the corpus can hold. The
    two are separate answers because they are separate findings, and because the
    stratified operator escalates past the domain — so a claim can be "killed" by a
    perturbation to a negative APM while no real session falsifies it.
    """
    if loose == "unsat":
        if w.hits:
            raise SystemExit(f"{cid}: no integer assignment falsifies it, yet "
                             f"{w.best[0]}->{w.best[1]} did — the free pass and the "
                             f"probe pass contradict, so neither is trustworthy")
        return "vacuous"
    if tight == "unsat":
        if w.real:
            raise SystemExit(f"{cid}: no realisable fact base falsifies it, yet "
                             f"{w.best[0]}->{w.best[1]} did, and that value is in the "
                             f"domain — the two passes contradict")
        return "unrealisable"
    if w.real:
        return "live"
    return "weak" if "sat" in (loose, tight) else "undecided"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    ap.add_argument("--solver", help="use only this solver")
    ap.add_argument("--probe", type=int, default=8, metavar="N",
                    help="constants to perturb per claim when hunting a witness "
                         "(default 8)")
    ap.add_argument("--limit-ms", type=int, default=3000, metavar="MS",
                    help="per-query solver time limit (default 3000)")
    ap.add_argument("--list", action="store_true",
                    help="print the witness for every claim, not only the findings")
    args = ap.parse_args(argv)

    path = os.path.join(args.report_dir, "claims.smt2")
    if not os.path.exists(path):
        print(f"  --  no {path}, so this artefact carries no spec-rendered claims")
        return 0
    found, absent = usable(args.solver)
    if not found:
        print("FAIL no usable SMT solver on PATH", file=sys.stderr)
        return 1
    ms = args.limit_ms

    started = time.time()
    with open(path, encoding="utf-8") as fh:
        art = parse(fh.read())
    real = list(art.claims)
    if not real:
        print(f"FAIL {path} defines no claims — a file with nothing in it passes every "
              f"check ever written", file=sys.stderr)
        return 1
    planted = controls(art)
    clash = {c.id for c in real} & {c.id for c in planted}
    if clash:
        raise SystemExit(f"control ids collide with real claims: {sorted(clash)}")
    art.claims = real + planted

    grounded_pass(art, art.claims, found, ms)

    # The sweep runs on one solver; anything it does NOT clear is then put to every
    # other solver. A `sat` is self-certifying — it comes with an assignment that
    # falsifies the claim — so one solver finding one is enough. `unsat` is a claim
    # of absence and gets the corroboration, which is where two independent
    # implementations are actually worth their cost. The controls are always among
    # the suspects, so the second solver is exercised on every run rather than only
    # on the day something breaks.
    answer = {}
    for domain in (False, True):
        raw = free_answers(art, art.claims, found[:1], ms, domain=domain)
        got = {c.id: [(found[0], raw[found[0]][c.id])] for c in art.claims}
        suspect = [c for c in art.claims
                   if verdict(c.id, got[c.id]) != "falsifiable"]
        if suspect and len(found) > 1:
            more = free_answers(art, suspect, found[1:], ms, domain=domain)
            for c in suspect:
                got[c.id] += [(s, a[c.id]) for s, a in more.items()]
                verdict(c.id, got[c.id])   # raises if the solvers contradict
            print(f"  ok  {len(suspect)} claim(s) the "
                  f"{'realisable' if domain else 'all-integer'} sweep did not clear "
                  f"re-checked on {', '.join(found[1:])}")
        answer[domain] = {c.id: ("sat" if any(a == "sat" for _s, a in got[c.id]) else
                                 "unsat" if any(a == "unsat" for _s, a in got[c.id])
                                 else "unknown") for c in art.claims}

    witness = probe_pass(art, art.claims, found[0], args.probe, ms)
    verdicts = {c.id: classify(c.id, answer[False][c.id], answer[True][c.id],
                               witness[c.id]) for c in art.claims}
    check_controls(art, verdicts, witness)

    by = {v: [c for c in real if verdicts[c.id] == v]
          for v in ("vacuous", "unrealisable", "undecided", "weak", "live")}

    # Findings go to stderr, progress to stdout; a pipe buffers the two differently,
    # which puts the findings above the run they came from unless stdout is flushed.
    sys.stdout.flush()

    if args.list:
        for c in real:
            w = witness[c.id]
            how = (f"{w.best[0]}->{w.best[1]} ({len(w.real)}/{w.tried} probes)"
                   if w.best else "no witness")
            print(f"      {c.id:6} {verdicts[c.id]:12} {how}")

    for c in by["vacuous"]:
        print(f"FAIL {c.id} is vacuous: no assignment of the constants it reads "
              f"falsifies it, so proving it says nothing about the session — "
              f"{c.gloss}", file=sys.stderr)
    for c in by["unrealisable"]:
        w = witness[c.id]
        how = (f"the only perturbation that reaches it is {w.best[0]}->{w.best[1]}, "
               f"a value no extractor can produce" if w.best else
               "no perturbation reaches it at all")
        print(f"FAIL {c.id} is vacuous over the data: only a fact base outside the "
              f"corpus's domain (measurements below 0, or a code not in the legend) "
              f"falsifies it — {how} — {c.gloss}", file=sys.stderr)
    for c in by["undecided"]:
        print(f"FAIL {c.id} undecided: the solver answered `unknown` over free "
              f"constants and no perturbation falsified it, so this run cannot say "
              f"whether it is vacuous — {c.gloss}", file=sys.stderr)
    for c in by["weak"]:
        print(f"  !!  {c.id} is falsifiable, but no single-constant perturbation "
              f"reaches it ({args.probe} constants tried) — {c.gloss}")

    bad = by["vacuous"] + by["unrealisable"] + by["undecided"]
    if bad:
        print(f"\n{len(bad)} of {len(real)} claims are not pinned by the data. A "
              f"per-constant mutation sweep cannot see this: their constants are "
              f"load-bearing in OTHER claims, so every one of them still dies and the "
              f"sweep reports no survivors.", file=sys.stderr)
    if len(bad) == len(real):
        print("...and that is every claim in the file, which is the signature of a "
              "broken harness rather than a finding — except the controls "
              "discriminated, so read the parse before believing it", file=sys.stderr)

    took = time.time() - started
    print(f"  {'ok ' if not bad else '!! '} {len(by['live'])} of {len(real)} claims "
          f"falsified by a concrete in-domain perturbation, {len(by['weak'])} only by a "
          f"compound one, {len(bad)} not pinned at all ({took:.1f}s, "
          f"{', '.join(found)}, {args.probe} constants probed per claim)")
    for s in absent:
        print(f"  --  {s} not used, so this run is {len(found)}-solver")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
