# tetrio-replay-report

[![verify](https://github.com/yachi/tetrio-replay-report/actions/workflows/verify.yml/badge.svg)](https://github.com/yachi/tetrio-replay-report/actions/workflows/verify.yml)

Turn a batch of TETR.IO `.ttrm` replays into a Cantonese match report where **every
number is machine-checked** — extracted twice by independent parsers, written as a
formal claim, and proved with [Dafny](https://dafny.org).

**[📊 Read the reports →](https://yachi.github.io/tetrio-replay-report/)**

| Session | Result | Rounds | Claims proved |
|---|---|---|---|
| [2026-07-22](sessions/2026-07-22) | yachi 6 : 4 pinglamb | 79 over 10 matches | 54 |
| [2026-07-24](sessions/2026-07-24) | yachi 3 : 4 pinglamb | 50 over 7 matches | 52 |
| [2026-07-28](sessions/2026-07-28) | yachi 2 : 6 pinglamb | 64 over 8 matches | 85 |
| [2026-08-01](sessions/2026-08-01) | yachi 4 : 3 pinglamb | 53 over 7 matches | 88 |

2026-07-24 also carries a lighter "即場戰報" (`report-2026-07-24.html`) with its own
independent 20-claim proof layer in [`sessions/2026-07-24/proof`](sessions/2026-07-24/proof).
Every fact in it is already covered by the session's full report, so it is kept as a
cross-check artefact — still verified by CI — rather than published as a second report.

---

## Why this exists

Match reports are easy to write and easy to get wrong. A stat gets transcribed with the
wrong polarity, an "average" is quietly a differently-weighted sum, a superlative is only
checked against half the data. So this repo makes every factual sentence carry a claim ID
that links to a Dafny lemma, and refuses to ship a report whose lemmas do not verify.

## What is actually proved (and what is not)

This distinction matters, so it is stated plainly rather than buried:

- **Dafny proves: claim ⇔ extracted data.** Each claim's Cantonese sentence has a matching
  predicate over `facts.json`, translated into a lemma. `dafny verify` proving it means the
  sentence is true *of the extracted dataset*.
- **Dafny does not prove the extraction.** That the dataset faithfully represents the
  `.ttrm` files rests on a different mechanism: **two independently written extractors**
  (Python and TypeScript, authored from a byte-precise schema without seeing each other)
  whose outputs must be identical.
- **Mutation testing keeps the lemmas honest.** A lemma that verifies but pins nothing is
  worthless, so `mutation_test.sh` flips one data literal or predicate constant at a time
  and requires verification to *break* every time. A surviving mutant is a build failure.
  For the same reason, no constant may sit in `Facts.dfy` unread by any lemma: a datum
  nothing depends on is a mutation that can never be killed.
- **The generated claims are also checkable without this pipeline.** The same specs render to
  SMT-LIB 2.6 as `claims.smt2` — facts as definitions, each claim asserted negated, quantifier-
  free integer arithmetic with player names as integer codes so no string theory is needed. Run
  `z3 claims.smt2` (or any QF_NIA-capable SMT-LIB solver) and every answer must be `unsat`. Two
  independent solvers agreeing is the same argument as two independent extractors agreeing.

## The verification chain

```
 10 × .ttrm  ──►  extract.py    ──►  facts.json  ─┐
             └─►  extract2.ts   ──►  facts2.json ─┴─► must be byte-identical
                                        │
                                        ▼
                          claims-*.json  (Cantonese sentence + integer predicate)
                                        │  every predicate must evaluate True
                                        ▼
                          codegen_dafny.py  ──►  Facts.dfy + Claims_*.dfy
                                        │  no hand-typed data; regeneration must be
                                        │  byte-identical to what is committed
                                        ▼
                              dafny verify  ──►  0 errors
                                        │
                                   mutation test  ──►  every mutant killed
                                        │
                                        ▼
                     claims-proof-map.json  (status comes from the verifier, never
                                             stamped optimistically by codegen)
                                        │
                                        ▼
                                   report.html   [C007 ✓] badges → appendix rows
```

Run the whole chain for any session yourself:

```bash
bin/verify-session sessions/2026-07-24/report      # gates 1-5
MUTATION=1 bin/verify-session sessions/2026-07-24/report   # + mutation testing
```

CI runs exactly this on every push, so the badge above is not decorative.

## Repository layout

```
pipeline/
  extract.py, extract2.ts      independent extractors -> facts.json / facts2.json
  claims/spec.py               predicate algebra -> Python and Dafny renderers
  claims/smt.py                the same algebra -> SMT-LIB 2.6
  claims/generators.py         32 claim families
  claims/build_claims.py       facts.json -> claims-generated.json
  claims/equiv.py              exhaustive-mutation coverage measurement
  codegen.py                   facts + claims -> Facts.dfy + Claims.dfy
  codegen_smt.py               facts + claims -> claims.smt2
  check_smt.py                 solve, regenerate and mutate the .smt2
  build_proof_map.py           verifier output -> proof map (never optimistic)
  mutation_test.sh             anti-vacuity gate, with an escalating operator
sessions/<date>/
  *.ttrm                       raw replays, untouched
  report/
    facts.json / facts2.json   the two extractors' output, which must match
    claims-generated.json      generated ledger (canto + predicate + spec)
    claims-narrative.json      hand-written 戰況 claims  (C0xx)
    claims-coaching.json       hand-written 建議 claims  (R0xx)
    dafny/*.dfy                one lemma per claim
    claims.smt2                the generated claims in SMT-LIB 2.6 (QF_NIA) — run
                               it yourself: `z3 claims.smt2`, all answers `unsat`
    claims-proof-map.json      what the verifier actually proved
    report.html                the deliverable, self-contained
    narrative-beats.md         Cantonese prose source
    recommendations.md         coaching prose source
    review-phase2.md           adversarial review of the ledgers
    audit-phase5.md            adversarial audit of the finished report
tools/analyzer.html            drop in a .ttrm, get an instant report (runs locally)
bin/new-session                replays in, verified ledger and proofs out
bin/verify-session             re-run every gate for one artefact
bin/build-docs                 regenerate the Pages site from the sessions
docs/                          the published site
```

## Adding a session

```bash
bin/new-session sessions/2026-08-01 ~/Downloads/replay-batch
```

That extracts the batch twice and compares, generates the claim ledger, generates the
Dafny, verifies it, and records the proof map — failing at the first gate that does not
hold. Then write the Cantonese prose against the generated ledger, add hand-written
claims for whatever is genuinely unique about the session, and run `bin/build-docs`.

### How the claims are generated

A **claim family** locates its own instances in whatever session it is handed — argmax
for superlatives, a scan for streaks, cross-multiplied ratios for per-piece rates — and
builds a **spec**, not a predicate string. `pipeline/claims/spec.py` renders that spec to
a Python predicate *and* to a Dafny `ensures` clause, so the statement that is checked
and the statement that is proved cannot drift apart. 32 families currently cover the
recurring shapes: series and per-match scores, sweeps and shutouts, deciders, streaks
(disclosing any match boundary they cross), session superlatives, per-player ceilings,
comebacks under queued and materialised pressure, cancellation, per-piece rates, clear
mix, integer variance, and situational records.

Coverage is measured rather than asserted. Comparing predicates as strings tells you
nothing, since every predicate is true of the real data, so
`pipeline/claims/equiv.py` applies **every single-value mutation** of the dataset — every
site, and at each site every perturbation kind (34,779 mutants over 7,019 sites on the
10-match session) — and with `--two-site` a second family of **value-preserving moves**,
and only counts a hand-written claim as covered when a generated claim cannot be true
unless it is:

| Session | single-value only | `--two-site match` | `--two-site round` |
|---|---|---|---|
| 2026-07-22 | 43 of 53 testable — **81%** | 42 of 53 — **79%** | 42 of 53 — **79%** |
| 2026-07-24 | 48 of 50 testable — **96%** | 48 of 50 — **96%** | 47 of 50 — **94%** |
| 2026-07-28 | 10 of 10 testable — **100%** | 6 of 10 — **60%** | 6 of 10 — **60%** |
| 2026-08-01 | 13 of 13 testable — **100%** | 12 of 13 — **92%** | 12 of 13 — **92%** |
| 2026-08-09 | 9 of 11 testable — **82%** | 8 of 11 — **73%** | 8 of 11 — **73%** |
| 2026-08-14 | 16 of 19 testable — **84%** | 13 of 19 — **68%** | 13 of 19 — **68%** |

Every figure above is measured, and `pipeline/claims/check_equiv_coverage.py` re-derives
them on push. **Until 2026-08-15 none of that was true**: three of the six sessions had
never been measured in public, every `--two-site` figure quoted was a `match` upper bound,
and the single-value figures were a *seeded sample* — one perturbation kind was drawn per
site, so 2026-07-22 read 85% at the committed seed, 87% at seed 3 and 83% at seed 42, with
the denominator moving too. Enumerating every kind costs ~5× the wall clock and settles
that session at 81%. A figure that moved with an argument nobody varied had been reading as
a property of the data.

Two of these sit below the **≥85%** acceptance gate that P4 declared, and 2026-07-22 —
the session the gate was declared on — is one of them at 81%. That is reported rather than
enforced: one hand claim is worth 10.0 points on 2026-07-28, so no threshold exists that is
both honest and stable, and a floor all six pass would sit at 60% and bless that session's
artefact by definition. The gate compares **verdict sets**, not a percentage.

**2026-07-28's 100% was an artefact, and the second family is what shows it.** Its hand
claims are *windowed* — they compare matches 1-2 against matches 3-8 — and every window sum
draws on the same rounds as the session total meant to imply it, so no single-value change
can falsify one without falsifying the other. A total survives *moving* value between two
rounds, and that takes two changes: shifting half of one match-3 round's `pieces` into a
match-1 round leaves `total_pieces`, `total_garbage_attack` and the efficiency-gap claims
true while flipping "yachi's attack per piece fell after match 2" to false. Under
`--two-site` exactly the four windowed claims (C002, C004, C005, C006) drop out, and the
100% becomes 60%. The generated totals never did imply the windowed claims; the first
family could not see it.

The delta is **half** the source, not all of it. An earlier revision moved the whole value,
which left every source round at 0 — a round with `pieces=0` but 48 lines cleared is not a
dataset either extractor can emit, and a claim falsified only by an impossible dataset is
not evidence. It also inflated the damage: on 2026-07-24 the whole-value family reported a
coverage loss that the legal half-move family does not.

`match` granularity keeps one move per (source match, target match, player, field), and
those moves are a strict **subset** of `round`'s — so a `match` figure bounds the
implications by construction, and the column above is published only because `round` has
now been measured for every session. The bound is on the implications, not on the fraction:
extra mutants also make more claims falsifiable, which moves the denominator, so the two
columns can differ in either direction. The weekly CI job is what re-measures `round`;
the per-push job measures the two cheaper granularities.

Claims that no single mutation can falsify are reported separately rather than counted.
The remainder stay hand-written, which is the point: generation handles the recurring
shapes so attention goes to whatever was actually interesting about that night.

## Data notes

Some field semantics are non-obvious and cost real debugging to establish:

- `lifetime` is **milliseconds**, not frames (verified against `pieces / pps`; assuming
  60 fps frames is off by ~15×).
- `ige` events of type `interaction_confirm` are **queued incoming attack**, before
  cancellation — consistently ~10–20% above `garbagereceived`, which is what actually
  materialised. The reports never conflate the two.
- The raw `tspins` counter includes spins that cleared no lines, so it exceeds the sum of
  the T-spin clear types. Charts and prose say which one they mean.
- Player order in `users` / `leaderboard` is **not stable across files** — always key by
  username.
- In first-to-death 1v1, kills equal round wins by construction; the reports never present
  them as two independent signals.

## Credits & licence

Replays are from matches between **yachi** and **pinglamb**, published with the agreement
of both players.

Code and tooling: [MIT](LICENSE), with one exception — `pipeline/sim/cc-tslot.ts` is a port
of [MinusKelvin/cold-clear](https://github.com/MinusKelvin/cold-clear)'s T-slot detectors and
stays under that project's [MPL-2.0](LICENSES/MPL-2.0.txt), as its own header records. MPL is
file-level copyleft (§3.3), so that one file is MPL and everything else is MIT.

The replay files and report text describe real matches between real people — please do not
repurpose them to characterise either player outside this context.
