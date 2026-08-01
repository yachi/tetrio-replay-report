# T-Spin Forecast metric — findings, and why it is *not* in the report

Status: **a properly powered NULL at every unit of analysis, and excluded.** Three units were
tested — round, event, player — and none shows an effect. More usefully, the ROUND is now known to
be the wrong unit in principle.

**The per-round metric barely correlates with itself.** Split-half reliability (odd vs even rounds,
within player) is **0.29** for pinglamb and **0.064** for yachi. By Spearman–Brown, reaching a
reliability of 0.70 would require aggregating **6** rounds for pinglamb and **34** for yachi. A
quantity that cannot correlate with itself cannot correlate with winning, so at ~1.34 T-spins per
player-round a per-round column is impossible **regardless of simulator coverage** — a stronger
statement than "not significant", and the reason every round-level result here was doomed.

**Selection bias was checked and ruled out.** The verified prefix ends where the simulator diverges,
which plausibly tracks garbage pressure and therefore losing; if so, conditioning on verification
would bias the AUC rather than merely widen it. It does not: winner's verified fraction vs loser's
is 34–36 (exact sign test p = 0.905), correlation with winning 0.026. The verified-prefix analyses
are unbiased, just underpowered.

**Event level (the only well-powered design): no effect, and the negative control fires.** Forecast
T-spins send 4.56 attack vs 4.04 for reactive, difference +0.52 with a cluster-bootstrap 95% CI of
[−0.34, 1.28] — includes zero. But the pre-declared negative control — attack sent in the window
*before the roof was built*, which forecasting cannot influence — shows a **significant** difference
(−0.57, CI [−0.98, −0.07]). The two groups differ before the mechanism could act, so even a
significant primary result could not have been attributed to forecasting. The control did its job.

**Player level: no difference.** pinglamb 13/97 = 13.4%, yachi 14/115 = 12.2%; exact two-sided
binomial against the exposure split, p = 0.848.

Original status follows.

Status (paired AUC, primary estimand): **a properly powered NULL, and excluded.** The metric is validated as an instrument, and
on a design that uses all the data it shows **no association with anything** — not winning, not
attack, not survival, not lines.

The paired-AUC primary estimand remains underpowered (16 decided pairs, p = 0.210). But that design
throws away almost everything: it collapses each round to one bit, then discards 19 of 35 pairs as
ties. A secondary continuous-outcome design over **110 player-rounds** with within-round permutation
inference gives:

| outcome | Pearson r | permutation p |
|---|---|---|
| won the round | **-0.000** | **0.995** |
| garbage sent | -0.193 | 0.640 |
| attack per minute | 0.109 | 0.300 |
| pieces placed | -0.224 | 0.310 |
| lines cleared | -0.207 | 0.871 |

**And that null has a stated power.** Injecting a known winner advantage into the real data and
re-running the same test: +5pp detected 24% of the time, **+10pp 67%, +15pp 94%**, +20pp 98% — so
~80% power at about **+12 percentage points**. The false-positive rate at an injected effect of zero
is 6%, which validates the test rather than assuming it. The observed between-player gap is 3-4
points (yachi 11.9%, pinglamb 15.2%), comfortably inside the null.

So this is no longer "we could not tell". It is: **there is no winner/loser forecast effect larger
than about 12 percentage points, and nothing at all is visible.** It stays out of the report because
it is simulator-derived and because a null does not earn a column — not because it is unmeasured.

Its AUC of 58.6% rests on **16 decided pairs** (11W–5L, plus 19 ties), a 95% CI of **[41%, 89%]**,
45% power against a true 70% effect and **80% power against a true 80% effect**. It still cannot
distinguish itself from TSD's 60.9%, so it stays excluded on two independent grounds: it is
simulator-derived, and it is not measurable at this sample size.

**These supersede an earlier 12-pair / [43%, 95%] / 25%-power reading.** The metric is computed only
on the verified prefix, so its sample size is a function of simulator accuracy; fixing the sub-frame
input clock (`sim/ab-subframe.ts`) moved coverage 13.8% → 17.9% and decided pairs 12 → 16. The gate
is simultaneously *stricter*: it now also requires the ige row oracle to agree
(`sim/ige-y-oracle.ts`), because 7.4% of attacks match on frame and amount while coming from the
wrong board row, and a forecast read off such a board is fiction. More data and better data at once.

**This corrects an earlier "negative result" framing** (see *Power*, below). A null finding and an
underpowered one licence different conclusions: the first says the metric does not work, the second
says this design could not have told you either way. Only `tucked T-spins`, on 55 decided pairs
with 88% power, is a genuine negative result here.

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
| yachi | 115 | 43 → **37.4%** | 14 → **12.2%** |
| pinglamb | 97 | 32 → **33.0%** | 13 → **13.4%** |

The loose rule showed yachi forecasting ~4 points more than pinglamb. Under the strict rule the
two are **identical within noise** — pinglamb is now nominally *ahead*. That gap was an artefact of
the rule, not a property of the players, and it shrank further as simulator coverage improved.

## Paired AUC (the repo's own bar for earning a column)

| metric | AUC (strict) | AUC (loose) | n pairs |
|---|---|---|---|
| forecast rate | **58.6%** | 57.1% | 35 (19 ties strict) |
| forecast per piece | 57.7% | — | 39 (21 ties) |
| forecast count | 52.5% | — | 79 (57 ties) |
| tucked T-spins | 57.0% | 57.0% | 79 (24 ties) |

**The loose→strict "collapse" no longer reproduces.** On the improved simulator the strict rule
scores *higher* than the loose one (58.6% vs 57.1%), reversing the direction the earlier, less
accurate sim showed. The collapse was substantially an artefact of the sim, not of the rule — which
is the same class of error this document already records twice, caught a third time.

## Power — what these AUCs can and cannot support

Run `bun run sim/auc-power.ts`. Its statistics are self-checked against the defining equations
(an early version silently printed an upper bound of 0%, and a Clopper–Pearson value recalled from
memory was wrong by 0.001 — both caught by that check, neither by reading the output).

| metric | AUC | W–L–T | decided | exact p | 95% CI on win-rate | power vs true 70% |
|---|---|---|---|---|---|---|
| forecast rate | 58.6% | 11–5–19 | **16** | 0.210 | **[41%, 89%]** | **45%** |
| forecast per piece | 57.7% | 12–6–21 | 18 | 0.238 | [41%, 87%] | 53% |
| forecast count | 52.5% | 13–9–57 | 22 | 0.523 | [36%, 79%] | 49% |
| tucked T-spins | 57.0% | 33–22–24 | **55** | 0.177 | [46%, 73%] | **88%** |
| separation-weighted | 55.7% | 10–6–19 | 16 | — | — | — |

`forecast rate` would need **12 of 16** — a 75% win-rate — to reach p < 0.05. A design that can
only see an effect that large has not measured a null; it has not measured. `tucked T-spins` is the
opposite case and the contrast is the point: 55 decided pairs, a CI that excludes anything
interesting, 88% power. That one genuinely reproduces the project's TSD/TST no-signal finding.

### "The signal does not survive the correct definition" was the wrong reading

That sentence attributed the loose→strict drop to the definition being corrected. Decomposed:

| | AUC | win-rate among decided | ties |
|---|---|---|---|
| loose | 57.1% | 60.0% | 10 of 35 |
| strict | 58.6% | 68.8% | **19 of 35** |

AUC scores a tie as half a win, so a coarser rule is dragged toward 50% **regardless of its effect
size**. The strict rule doubles the ties (10 → 19) and *still* scores higher, because its win-rate
among decided pairs is far better (68.8% vs 60.0%). The win-rate CIs, [39%, 79%] loose and
[41%, 89%] strict, overlap across nearly their whole range, so at this n the two rules are not
statistically separable either way. The strict rule remains the right rule on geometric grounds —
that argument never depended on the AUC.

*Historical note, kept deliberately:* on the pre-fix simulator this table read loose 75.0% /
strict 63.6%, and the drop was decomposed as 65% tie-mechanism. Both the magnitude and the SIGN of
that drop were simulator artefacts. The decomposition method was sound; the inputs were not.

This is the same error as the original loose/strict finding, one level up: a property of the
instrument read as a property of the world. The first time it was the rule inventing a gap between
players; this time it is the tie-handling inventing a collapse.

### A trap worth recording

On the pre-fix simulator a cluster bootstrap over the 10 matches returned a 95% CI of
**[55.0%, 73.8%]** for `forecast rate` — which excludes 50% and reads as a real signal,
contradicting the exact test's p = 0.146. On the current data it returns **[47.1%, 68.9%]**, which
includes 50% and no longer contradicts anything; the trap did not fire twice. It is recorded
because it *would* have flipped this document's conclusion once. Do not believe it: 10 clusters is far below what a cluster bootstrap needs to attain nominal coverage, and
it is estimating the tie-inclusive AUC rather than the conditional win-rate. The conservative exact
test governs. Reporting only the bootstrap would have flipped this document's conclusion.

The most likely reading: the loose rule was largely detecting "a line clear happened recently",
which tracks attacking well, not forecasting. `tucked T-spins` at 57.0% (55 decided pairs, p = 0.177) independently reproduces
this project's existing TSD/TST no-signal finding, which is a useful check that the pipeline is
not manufacturing structure.

## Why it is not in the report

The invariant is *Dafny proves claim ⇔ extracted data, and the extraction is trusted because two
independent extractors agree byte-for-byte.* These numbers come from **a simulator**, and:

1. There is **no second independent implementation** — the dual-extractor argument does not hold.
2. The simulator **fails its own gate**: 1/158 rounds match all fields. Only *prefixes* are
   verified, using the opponent's ige stream as a per-attack oracle.
3. **Coverage is 17.9%** of placements (2595/14517) across 109/158 rounds, on the strict
   frame+amount+row gate, and it is
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
4. **Enough decided pairs to have power.** This is the binding constraint, and it is now measured
   end to end by `sim/forecast-power-curve.ts` rather than assumed. Real simulator configurations
   spanning a range of accuracy, each carried through to decided pairs:

   | config | coverage | verified T-spins | usable pairs | W–L–T | decided |
   |---|---|---|---|---|---|
   | frame clock (pre-fix) | 13.8% | 172 | 25 | 10–2–13 | 12 |
   | + locktime 30 | 17.1% | 205 | 32 | 11–3–18 | 14 |
   | + blockout strict | 17.4% | 207 | 33 | 10–4–19 | 14 |
   | **BEST, strict rows** | **17.9%** | **212** | **35** | **11–5–19** | **16** |
   | BEST, loose gate | 19.5% | 225 | 35 | 11–7–17 | 18 |

   The exchange rate is **~1 decided pair per point of coverage**. Extrapolating at that rate:

   | if the true effect is | decided pairs needed | implied coverage | vs today |
   |---|---|---|---|
   | 60% win-rate | 158 | **163%** | unreachable |
   | 65% | 69 | 72% | 4.0× |
   | 70% | 37 | 39% | 2.2× |
   | 75% | 23 | 25% | 1.4× |
   | 80% | 18 | 20% | 1.1× |

   **The decisive result: a modest (60%) true effect is unreachable on this dataset at any
   simulator accuracy.** 158 decided pairs cannot be extracted from 79 rounds — the ceiling is 79
   even at 100% coverage. No amount of simulator work fixes that; only more sessions do. A large
   (75–80%) effect, by contrast, is nearly within reach already.

   **Correction — ties are not a granularity problem.** This document previously reasoned that
   "the rate is a ratio of small integers, which is where the ties come from" and proposed a
   finer-grained metric as the lever. Measured: **100% of ties are 0-vs-0**, and the median
   player-round contributes just **one** verified tucked T-spin (mean 1.34; zero in 57/158). A
   `separation-weighted` variant was implemented to test the granularity hypothesis directly and
   decides **exactly the same 16 pairs** at a lower AUC. Ties come from the forecast base rate
   being 12.7% against ~1 T-spin per round, so most players score 0. The only lever is more
   verified T-spins per round — deeper coverage, or more sessions.

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

## The all-clear is its own event — and that gives perfect clears an oracle (2026-07-30)

Chasing the open "sim finds 7 perfect clears, the games had 19" question produced a measured answer
to a different question, and then dissolved the original one.

**TETR.IO does not fold the all-clear bonus into the line-clear attack.** It emits a *second* `ige`
event, of amount exactly **10**, at the same frame, after the base attack. Four rounds show it
plainly — the sim sends one combined number, ground truth sends two:

```
sim sent 11@326    truth  1@326  10@326
sim sent 12@755    truth  2@755  10@755
sim sent 11@646    truth  1@646  10@646
sim sent 12@633    truth  2@633  10@633
```

The bonus *value* (10) was already right; the packaging was wrong. This is why the verified prefix
was **zero in every round containing a perfect clear**: the matcher compared the sim's 11 against
truth's 1, failed, and truncated at the first PC.

**`amt === 10` is therefore an exact oracle for the perfect clear — 158/158 player-rounds, 19
predicted vs 19 recorded** (`sim/pc-oracle.ts`). It is safe because no ordinary attack in this
dataset reaches 9 or 10; the histogram tops out at 8, and 10 occurs exactly 19 times. A first
version of the test also required the 10 to share a frame with a sibling attack and scored 155/158
— the three misses are PCs whose base attack was *fully cancelled*, so no sibling exists.
Co-location is a property of the common case, not the rule.

This matters beyond perfect clears: every attack a player sent is now locatable in time to the
event, including ones a whole-round statistic cannot place.

Fixing the emission (`acEmit: 'separate'`, now the default) moves coverage 13.8% → **14.1%**,
contributing rounds 88 → 89, and shifts the published figures — which is why the numbers earlier in
this document changed.

### The 7-vs-19 gap was a symptom, not a question

With the oracle in hand, the original framing does not survive contact with the data:

| | |
|---|---|
| sim tops out | **151 / 158 rounds** |
| sim clears **zero** lines while the real player cleared some | 39 / 158 |
| median sim/real line ratio | **0.13** |
| sim invents a PC that never happened | **0 / 158** |

The simulator reproduces about an eighth of a round's line clears and dies in 96% of rounds. It
finds 7 of 19 perfect clears for the same reason it finds 13% of line clears: it is not surviving
the round. Nine of the twelve misses occur in rounds the sim *did* simulate past piece 19, and in
several of those it had cleared **no lines at all in 25–29 pieces** — so it is not a perfect-clear
bug, and hunting one would have been fixing a symptom.

The one genuinely diagnostic row is the last: **the sim never invents a perfect clear.** The
all-clear predicate does not over-fire. The board it is asked about is simply wrong.

**Reframed open question**, replacing "why 7 and not 19": *why does the simulator top out in 151 of
158 rounds, and clear nothing at all in 39 of them, when its placement engine is frame-accurate?*
That is one question, and the perfect-clear count is one of several ways to observe it.

## One duplicate deleted (2026-07-30)

`tspinAvailable` was a second, independently written BFS beside `bestTspinLines`. The property
suite found them agreeing on all 932 boards, and the duplication was actively dangerous: the two
copies carried **different BFS caps**, 20000 and 40000. Neither was ever live — the queue only
grows when a fresh `rotation:col:row` key enters `seen`, so it is bounded by `4 * 10 * H = 1600`
states by construction (measured max over 2000 boards: **688**, `bfs-cap.ts`). Equivalence is
structural, not sampled, so `tspinAvailable` is now one line: `bestTspinLines(board) > 0`.

`forecast.ts` 156 → 145 lines, still 11/11 mutation-killed, and the published figures reproduce
**exactly** — yachi 89/11/12.4%, pinglamb 78/10/12.8%, AUC 61.4 / 57.7 / 52.5 / 46.2 (the figures
as they stood that day; they moved when the all-clear emission was fixed, below). The negative
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
