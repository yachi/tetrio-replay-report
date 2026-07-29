# T-Spin Forecast metric — findings, and why it is *not* in the report

Status: **negative result.** The metric is validated as an instrument, but under a mechanically
correct definition it carries no signal — AUC 61.4%, indistinguishable from TSD's 60.9%, which
this project already files under "No signal". Excluded from the report on two independent
grounds: it is simulator-derived, and it does not measure anything.

## What it measures

Per harddrop.com/wiki/T-Spin_Forecast, forecasting is stacking so T-spins *emerge* from line
clears or incoming garbage — the overhang is placed while the slot does not yet exist. Intent is
unobservable, so the metric measures the signature: for each executed T-spin, a provenance grid
(which lock placed each cell; `-1` = garbage) identifies the lock that built the slot's **roof**,
then classifies by what happened between roof-build and execution.

- `forecast_garbage` — garbage rose in that window
- `forecast_lineclear` — a line clear occurred in that window
- `reactive` — the slot was already usable

The `forecast_*` buckets additionally require the strict gate below: no line-clearing T-spin was
available anywhere on the board when the roof was placed.

`separation = k − j` in pieces. Reported as a rate, never a binary claim.

Geometric note that cost a wrong model: **garbage can never be the roof.** It rises from the
bottom, so its role is to *lift* an already-built overhang into a spinnable position, not to
construct one. A "roof is garbage" test fires 0/167 and is dead logic.

## The definition matters more than the measurement

Two rules were implemented. The difference between them is the whole finding.

**Loose** — "a line clear or garbage occurred between roof-build and execution". Wrong, because a
clear five rows below the slot splices nothing.

**Strict** — "was a line-clearing T-spin *already available* when the roof was placed?" If none was,
the slot did not exist and something later created it. Verified against an engine-checked fixture
pair (`splice-demo`): identical overhang and cavity separated by one full row offers **no** T-spin;
remove that row and a clean TSD appears.

A third rule was tried and discarded: "is the cell beneath the roof empty at placement". It returns
reactive for all 167 cases, because a piece placed as an overhang has an empty cell beneath it *by
definition*. Recorded so nobody re-derives it.

| | tucked T-spins | forecast (loose) | forecast (strict) |
|---|---|---|---|
| yachi | 89 | 38 → **42.7%** | 11 → **12.4%** |
| pinglamb | 78 | 27 → **34.6%** | 10 → **12.8%** |

The loose rule showed yachi forecasting ~8 points more than pinglamb. Under the strict rule the
two are **identical within noise**. That gap was an artefact of the rule, not a property of the
players.

## Paired AUC (the repo's own bar for earning a column)

| metric | AUC (strict) | AUC (loose) | n pairs |
|---|---|---|---|
| forecast rate | **61.4%** | 72.7% | 22 (11 ties strict) |
| forecast per piece | 57.7% | 67.3% | 26 (14 ties) |
| forecast count | 52.5% | 53.2% | 79 (61 ties) |
| tucked T-spins | 46.2% | 46.2% | 79 (25 ties) |

Under the loose rule `forecast rate` looked promising — 13W–3L–6T, binomial p = 0.011. **That
signal does not survive the correct definition.** At 61.4% it sits on top of TSD's 60.9%, inside
the no-signal band, with half its pairs now ties.

The most likely reading: the loose rule was largely detecting "a line clear happened recently",
which tracks attacking well, not forecasting. `tucked T-spins` at 46.2% independently reproduces
this project's existing TSD/TST no-signal finding, which is a useful check that the pipeline is
not manufacturing structure.

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

- 14 unit tests on hand-built cases. Mutation testing on the classifier: **6/6 killed** (one
  initially survived — every test had a single roof owner, so `Math.max`→`Math.min` was invisible;
  a two-owner case fixed it). On the strict availability probe: **2/4 killed** — "probe ignores the
  line-clear requirement" and "probe accepts non-rotation landings" both **survive**, because the
  BEFORE/AFTER fixtures cannot distinguish them. Closing those needs a board where a T-spin is
  available but clears nothing, and one where a T lands spin-shaped without rotating. **Not done.**
- On real data, all 167 counted T-spins: BFS-reachable from spawn **167/167**, satisfy the
  3-corner rule **167/167**, physically supported **167/167**
- Negative control: random T placements on the same boards are reachable only **3.6%**, so the
  reachability check discriminates rather than rubber-stamps
- Spin classification externally confirmed for **138/167 (82.6%)** — attack amount is a function
  of (clear type, spin, B2B, combo), and every counted spin sits in a prefix where amounts matched
  ground truth; the other 29 were fully cancelled, leaving no witness

Not done: property-based testing over random boards, coverage measurement on the new lines.

## External golden data: the wiki's own boards

`wiki-tspin-forecast-boards.json` holds all **29 board diagrams** parsed from
harddrop.com/wiki/T-Spin_Forecast, with hierarchical section paths. Provenance is the point — the
boards *and* the expectations come from the wiki, never from this engine.

Parsing notes, each of which cost a wrong reading:
- the page has **no `<br>` between rows**; tiles wrap visually. Row structure was confirmed by
  measuring each image's pixel y-position, which gives exactly 10 columns per row.
- `PTet.png` is the **T** piece (drawn purple). There is no `TTet.png`.
- **`-Tet.png` is a dashed *empty* cell, not a T outline.** It marks a region of interest — the
  well, or the future garbage hole. On the TSD board the dashed cells form an **L** shape, and five
  boards carry a single dashed cell, so reading them as a T placement is wrong.

What the engine finds, checked against what each section *claims*:

| wiki section | best T-spin the engine finds |
|---|---|
| Forecasting T-Spin Singles | **none** |
| Forecasting T-Spin Doubles | **none** |
| Forecasting T-Spin Triples | **none** |
| Forecasting T-Spin Doubles > Garbage | **2 lines** (double) |
| Forecasting T-Spin Triples > Garbage | **3 lines** (triple) |

The non-garbage rows are the striking ones: **every "Forecasting X" setup is a position where no
T-spin is available yet.** That is the premise of forecasting, stated by the wiki's own figures and
independently confirmed by the engine — and it is exactly the predicate the strict classifier tests.
The Garbage sections then land on precisely the spin each section is named for.

One adjacent pair makes the garbage mechanic concrete: identical Z overhang, one extra bottom row
of garbage whose hole sits under the slot, and the same T-spin goes from **1 line to 2**. Garbage
does not build the overhang; it lifts the structure so the existing slot is worth more.

These fixtures raised mutation coverage of the availability probe from 2/4 to 3/4 — the surviving
"probe ignores the line-clear requirement" mutant is killed by the no-T-spin-yet assertions. Two
mutants still survive ("accepts non-rotation landings", "bestTspinLines drops the spin test"); I
could not construct a board that distinguishes them, since reaching a 3-corner position without
rotating appears to require a kick by construction. They may be equivalent mutants — **unproven,
recorded as open.**

Implementation lives outside this repo (session scratchpad): `sim.ts`, `forecast.ts`,
`run-forecast.ts`, `forecast.test.ts`, `validate.ts`, `auc.ts`.
