# T-Spin Forecast metric — findings, and why it is *not* in the report

Status: **inconclusive, and excluded.** The metric is validated as an instrument. Its AUC of 61.4%
rests on **11 decided pairs** (8W–3L, plus 11 ties), a 95% CI of **[39%, 94%]**, and 31% power
against a true 70% effect — so it can distinguish neither "no signal" from "strong signal" nor
itself from TSD's 60.9%. Excluded from the report on two independent grounds: it is
simulator-derived, and it is not measurable at this sample size.

**This corrects an earlier "negative result" framing** (see *Power*, below). A null finding and an
underpowered one licence different conclusions: the first says the metric does not work, the second
says this design could not have told you either way. Only `tucked T-spins`, on 54 decided pairs
with 90% power, is a genuine negative result here.

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

Under the loose rule `forecast rate` looked promising — 13W–3L–6T, binomial p = 0.011. At 61.4%
the strict rule sits on top of TSD's 60.9%, inside the no-signal band, with half its pairs now ties.

## Power — what these AUCs can and cannot support

Run `bun run sim/auc-power.ts`. Its statistics are self-checked against the defining equations
(an early version silently printed an upper bound of 0%, and a Clopper–Pearson value recalled from
memory was wrong by 0.001 — both caught by that check, neither by reading the output).

| metric | AUC | W–L–T | decided | exact p | 95% CI on win-rate | power vs true 70% |
|---|---|---|---|---|---|---|
| forecast rate | 61.4% | 8–3–11 | **11** | 0.227 | **[39%, 94%]** | **31%** |
| forecast per piece | 57.7% | 8–4–14 | 12 | 0.388 | [35%, 90%] | 25% |
| forecast count | 52.5% | 11–7–61 | 18 | 0.481 | [36%, 83%] | 53% |
| tucked T-spins | 46.2% | 24–30–25 | **54** | 0.497 | [31%, 59%] | **90%** |

`forecast rate` would need **9 of 11** — an 82% win-rate — to reach p < 0.05. A design that can
only see an effect that large has not measured a null; it has not measured. `tucked T-spins` is the
opposite case and the contrast is the point: 54 decided pairs, a CI that excludes anything
interesting, 90% power. That one genuinely reproduces the project's TSD/TST no-signal finding.

### "The signal does not survive the correct definition" was the wrong reading

That sentence attributed the loose→strict drop to the definition being corrected. Decomposed:

| | AUC | win-rate among decided | ties |
|---|---|---|---|
| loose | 72.7% | 81.3% | 6 of 22 |
| strict | 61.4% | 72.7% | **11 of 22** |

AUC scores a tie as half a win, so a coarser rule is dragged toward 50% **regardless of its effect
size**. Carry loose's effect size onto strict's tie structure and AUC is 65.6% — so of the
11.4-point drop, **7.1 points (63%) is the tie mechanism** and only 4.3 points is the effect
estimate moving. The win-rate CIs, [54%, 96%] loose and [39%, 94%] strict, overlap across nearly
their whole range. *At this n, "the effect went away" and "the rule resolves less" are not
separable.* The strict rule is still the right rule — that argument was always geometric, not
statistical — but the AUC drop is not the evidence for it.

This is the same error as the original loose/strict finding, one level up: a property of the
instrument read as a property of the world. The first time it was the rule inventing a gap between
players; this time it is the tie-handling inventing a collapse.

### A trap worth recording

A cluster bootstrap over the 10 matches returns a 95% CI of **[52.8%, 70.4%]** for `forecast rate`
— which excludes 50% and reads as a real signal, contradicting the exact test's p = 0.227. Do not
believe it: 10 clusters is far below what a cluster bootstrap needs to attain nominal coverage, and
it is estimating the tie-inclusive AUC rather than the conditional win-rate. The conservative exact
test governs. Reporting only the bootstrap would have flipped this document's conclusion.

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
4. **Enough decided pairs to have power.** This is now the binding constraint, and it is
   quantified — `auc-power.ts` computes the sample size for 80% power at the observed 50% tie rate:

   | if the true effect is | decided pairs needed | total pairs | vs current |
   |---|---|---|---|
   | 60% win-rate | 158 | 316 | 14× |
   | 65% | 69 | 138 | 6× |
   | 70% | 37 | 74 | 3× |
   | 80% | 18 | 36 | 2× |

   The 07-22 set yields 22 usable pairs from 158 rounds, because coverage is a verified *prefix*.
   **More sessions alone will not fix this**: at a 50% tie rate, half of every future pair is
   discarded too. The lever is either a finer-grained metric (the rate is a ratio of small integers,
   which is where the ties come from) or a simulator that verifies deeper into each round — i.e.
   item 1 is not just a correctness prerequisite, it is the power prerequisite.

## Validation performed on the instrument

- 14 unit tests on hand-built cases. Mutation testing on the classifier: **6/6 killed** (one
  initially survived — every test had a single roof owner, so `Math.max`→`Math.min` was invisible;
  a two-owner case fixed it).
- **Mutation, re-measured 2026-07-30: 11/11 killed** across the whole instrument (`mutate-forecast.ts`).
  The harness is itself validated by control mutants — three semantics-preserving edits **survive**
  and a poison mutant (spawn column 3→9) **dies**, so a green sweep is discrimination, not a
  syntax error killing everything.
  Attribution was measured, not assumed: strip the two rotation/spin fixtures and **6 mutants
  survive**; restore them and it is 11/11. See the correction at the end of the wiki section.
- On real data, all 167 counted T-spins: BFS-reachable from spawn **167/167**, satisfy the
  3-corner rule **167/167**, physically supported **167/167**
- Negative control: random T placements on the same boards are reachable only **3.6%**, so the
  reachability check discriminates rather than rubber-stamps
- Spin classification externally confirmed for **138/167 (82.6%)** — attack amount is a function
  of (clear type, spin, B2B, combo), and every counted spin sits in a prefix where amounts matched
  ground truth; the other 29 were fully cancelled, leaving no witness

- **Property-based testing over random boards, done 2026-07-30** (`property-forecast.test.ts`):
  932 boards from three domain-shaped generators (stack profiles, garbage rows, sparse noise),
  seeded with the same MINSTD as the piece RNG so any failure is reproducible. Boards containing a
  full row are discarded as unreachable states. Properties held: availability ≡ `bestTspinLines > 0`,
  a T-spin clears at most 3 lines, neither probe mutates its input, results are deterministic, and
  an empty board offers nothing. An anti-vacuity gate asserts the sample is not inert — **84/932**
  boards actually offer a line-clearing T-spin, so the suite is exercising the predicate.
- **Coverage, done 2026-07-30**: `bun test --coverage` reports **100% of functions and lines** on
  `forecast.ts`.

Still not done: nothing on the instrument. The remaining gaps are all in the simulator underneath it.

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
"probe ignores the line-clear requirement" mutant is killed by the no-T-spin-yet assertions.

**Correction (2026-07-30). The two mutants recorded here as possibly-equivalent are killable, and
were already dead when this paragraph was written.** The claim was that reaching a 3-corner position
without rotating "appears to require a kick by construction". That is false: a *vertical* T slides
down a one-wide channel and comes to rest with three corners filled, having never rotated — its last
action is a downward move, so it is a placement, not a spin. Two fixtures encoding exactly that
(`37:[3,4] 38:[3,4] 39:[4]`, and a T rotated into a well that clears a line with only two corners)
are in `wiki-fixtures.test.ts`, whose mtime is **29 Jul 13:03 — seven minutes after this file's
12:56**. The tests were written and the paragraph was never revisited.

The lesson is not about T-spin geometry. **"I could not construct X" was recorded as a property of
X rather than of the search** — the earlier attempt (`find-mut2.ts`) swept only rows 37-39 with ≤4
empty columns drawn from columns 2-7, a space that happens to exclude the one-wide vertical channel.
An exhausted search bounded that narrowly is evidence about the bound, not about the claim.

## One duplicate deleted (2026-07-30)

`tspinAvailable` was a second, independently written BFS beside `bestTspinLines`. The property
suite found them agreeing on all 932 boards, and the duplication was actively dangerous: the two
copies carried **different BFS caps**, 20000 and 40000. Neither was ever live — the queue only
grows when a fresh `rotation:col:row` key enters `seen`, so it is bounded by `4 * 10 * H = 1600`
states by construction (measured max over 2000 boards: **688**, `bfs-cap.ts`). Equivalence is
structural, not sampled, so `tspinAvailable` is now one line: `bestTspinLines(board) > 0`.

`forecast.ts` 156 → 145 lines, still 11/11 mutation-killed, and the published figures reproduce
**exactly** — yachi 89/11/12.4%, pinglamb 78/10/12.8%, AUC 61.4 / 57.7 / 52.5 / 46.2. The negative
result is unchanged; it now rests on half as much code.

## Where the implementation lives

[`sim/`](sim/), committed 2026-07-30 — see its README for how to re-run every figure above.

Until then it lived only in a `/private/tmp` session scratchpad belonging to a session that had
ended, i.e. every number here was reproducible only from files one reboot from deletion. That is
the same failure this project guards against everywhere else: a claim whose evidence cannot be
re-run is a claim on trust. The ~45 exploratory probe scripts were deliberately left behind; only
the reproducible core is committed.

One thing the move surfaced: the engine under the simulator is a **patched** copy of
td-opener-trainer `fa596ee` — `BOARD_VISIBLE_HEIGHT` 20 → 40, which `srs.ts` bakes into its floor
check. The patch was uncommitted in the scratchpad clone, so a re-clone would have locked pieces at
row 20 and produced wrong boards **without erroring**. It is vendored into `sim/vendor/core/` with
that noted in the files themselves.
