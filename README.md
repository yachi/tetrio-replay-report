# tetrio-replay-report

Turn a batch of TETR.IO `.ttrm` replays into a Cantonese match report where **every
number is machine-checked** — extracted twice by independent parsers, written as a
formal claim, and proved with [Dafny](https://dafny.org).

**[📊 Read the reports →](https://yachi.github.io/tetrio-replay-report/)**

| Session | Result | Rounds | Claims proved |
|---|---|---|---|
| [2026-07-22](sessions/2026-07-22) | yachi 6 : 4 pinglamb | 79 over 10 matches | 54 |
| [2026-07-24](sessions/2026-07-24) | yachi 3 : 4 pinglamb | 50 over 7 matches | 52 (+20 for the live report) |

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
sessions/<date>/
  *.ttrm                    raw replays, untouched
  report/
    extract.py, extract2.ts independent extractors  → facts.json / facts2.json
    claims-narrative.json   戰況 claims  (C0xx)
    claims-coaching.json    建議 claims  (R0xx)
    check_claims.py         predicate gate
    codegen_dafny.py        claims + facts → Dafny (zero hand-typed data)
    dafny/*.dfy             generated: flat scalar consts + one lemma per claim
    mutation_test.sh        anti-vacuity gate
    gen_consistency.sh      codegen byte-identity gate
    build_proof_map.py      verifier output → claims-proof-map.json
    build_appendix.py       claims + proof map → report appendix
    report.html             the deliverable, self-contained
    narrative-beats.md      Cantonese prose source
    recommendations.md      coaching prose source
    review-phase2.md        adversarial review of the claim ledgers
    audit-phase5.md         adversarial audit of the finished report
tools/analyzer.html         drop in a .ttrm, get an instant report (runs locally)
bin/verify-session          re-run every gate for one artefact
bin/build-docs              regenerate the GitHub Pages site from the sessions
docs/                       the published site
```

## Adding a session today

1. Drop the `.ttrm` batch into `sessions/<date>/`.
2. Copy `report/` from the most recent session and point the extractors at the new files.
3. Write the claim ledgers, generate Dafny, and run `bin/verify-session` until green.
4. Write the prose, build the report, and run `bin/build-docs`.

Steps 2–3 are still more manual than they should be — see
**[ROADMAP.md](ROADMAP.md)**, whose whole point is collapsing them into one command by
turning the recurring claim families into generators. About 85% of the claims across the
two existing sessions are the same handful of shapes (series and per-match scores, sweeps,
session superlatives, streaks, comeback-under-pressure, per-player aggregates, variance),
so they can be generated instead of hand-written.

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

Code and tooling: [MIT](LICENSE). The replay files and report text describe real matches
between real people — please do not repurpose them to characterise either player outside
this context.
