# T-Spin Forecast metric — findings, and why it is *not* in the report

Status: **measured, validated as an instrument, deliberately excluded from the badge-linked
report.** Read the exclusion argument before deciding to promote it.

## What it measures

Per harddrop.com/wiki/T-Spin_Forecast, forecasting is stacking so T-spins *emerge* from line
clears or incoming garbage — the overhang is placed while the slot does not yet exist. Intent is
unobservable, so the metric measures the signature: for each executed T-spin, a provenance grid
(which lock placed each cell; `-1` = garbage) identifies the lock that built the slot's **roof**,
then classifies by what happened between roof-build and execution.

- `forecast_garbage` — garbage rose in that window
- `forecast_lineclear` — a line clear occurred in that window
- `reactive` — neither; the slot was already usable

`separation = k − j` in pieces. Reported as a rate, never a binary claim.

Geometric note that cost a wrong model: **garbage can never be the roof.** It rises from the
bottom, so its role is to *lift* an already-built overhang into a spinnable position, not to
construct one. A "roof is garbage" test fires 0/167 and is dead logic.

## Result (2026-07-22, verified prefixes only)

| | tucked T-spins | forecast (garbage) | forecast (clear) | reactive | rate |
|---|---|---|---|---|---|
| yachi | 89 | 15 | 23 | 51 | **42.7%** |
| pinglamb | 78 | 15 | 12 | 51 | **34.6%** |

Rate rises monotonically with setup separation — 38.9% (sep≥1) → 45.5% (≥2) → 51.6% (≥3) →
63.0% (≥5) — the direction intent predicts, and not something the implementation was fitted to.

## Paired AUC (the repo's own bar for earning a column)

| metric | AUC | n pairs |
|---|---|---|
| forecast rate | **72.7%** | 22 (6 ties) |
| forecast per piece | 67.3% | 26 (5 ties) |
| forecast count | 53.2% | 79 (36 ties) |
| tucked T-spins | 46.2% | 79 (25 ties) |

`forecast rate` is 13W–3L–6T, one-sided binomial **p = 0.011**, Wilson 95% CI **57.0–93.4%**.
So it clears the "no signal" band that already contains TSD (60.9) and TST (55.8), but its
interval is wide and it does not approach the strong band (APM 94.6, VS 100). Suggestive, not
established.

## Why it is not in the report

The invariant is *Dafny proves claim ⇔ extracted data, and the extraction is trusted because two
independent extractors agree byte-for-byte.* These numbers come from **a simulator**, and:

1. There is **no second independent implementation** — the dual-extractor argument does not hold.
2. The simulator **fails its own gate**: 1/158 rounds match all fields. Only *prefixes* are
   verified, using the opponent's ige stream as a per-attack oracle.
3. **Coverage is 13.8%** of placements (2001/14517) across 88/158 rounds, and it is
   systematically the *early* part of every round — opener/early-midgame, when garbage pressure
   is lightest. Not a match-level rate.

Badging a simulator output would blur simulation into extraction, which is the exact failure
every audit round in this project has caught. A numeric section without badges breaks the
"every countable statement needs a claim id" rule instead. Both doors are shut on purpose.

## What would make it report-eligible

1. Sim passes the full gate — all 158 rounds exact on lines / pieces / holds / clears breakdown /
   finesse / garbage.* / topbtb. Currently blocked on post-garbage divergence (attack match
   collapses from 100% pre-garbage to ~6% after).
2. A **second independent sim implementation**, agreeing byte-for-byte on the emitted
   per-round forecast counts — the dual-extractor rule applied to derived data.
3. Forecast counts land in `facts.json` as data; claims then written as specs like any other.
4. Re-run the AUC probe on the full (unbiased) sample before it earns a column — the current
   n=22 could move a long way.

## Validation performed on the instrument

- 10 unit tests on hand-built cases; **6/6 mutants killed** (one initially survived — every test
  had a single roof owner, so `Math.max`→`Math.min` was invisible; a two-owner case fixed it)
- On real data, all 167 counted T-spins: BFS-reachable from spawn **167/167**, satisfy the
  3-corner rule **167/167**, physically supported **167/167**
- Negative control: random T placements on the same boards are reachable only **3.6%**, so the
  reachability check discriminates rather than rubber-stamps
- Spin classification externally confirmed for **138/167 (82.6%)** — attack amount is a function
  of (clear type, spin, B2B, combo), and every counted spin sits in a prefix where amounts matched
  ground truth; the other 29 were fully cancelled, leaving no witness

Not done: property-based testing over random boards, coverage measurement on the new lines.

Implementation lives outside this repo (session scratchpad): `sim.ts`, `forecast.ts`,
`run-forecast.ts`, `forecast.test.ts`, `validate.ts`, `auc.ts`.
