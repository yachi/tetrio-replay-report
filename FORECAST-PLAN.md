# T-Spin Forecast — the plan for putting it in the reports

Status: **planned, with the evidence for each step measured rather than argued.** Written
2026-08-02. The findings doc is [`sessions/2026-07-22/forecast-metric.md`](sessions/2026-07-22/forecast-metric.md);
this file is what to *do*, and why each step is safe.

## 0. Problem reframe

"Add the forecast metric to the reports" carries an assumption the data refutes: that forecast is a
*performance* column. It is not — it predicts nothing at any unit of analysis, and this document
records the strongest version of that null yet measured.

The metric is also already *in* a report: `pipeline/forecast_section.py` renders a quarantined,
badge-free section in 2026-07-22, gated by `pipeline/check_forecast_section.py` in CI. So the ask
resolves to two separable things:

* **extend it to the other three sessions** — cheap, and it is what produced every result below;
* **badge it** — impossible today, for a reason no amount of Dafny changes.

What forecast can honestly be is a **descriptive style statistic**: among verified (early-round)
tucked T-spins, both players forecast about one in seven, consistently across four nights.

## 1. The instrument already runs on all four sessions

`verified-prefix.ts:36` has always honoured `REPLAY_DIR`; nobody had pointed it elsewhere. Pointed
at the other three sessions it reproduces 2026-07-22's committed figures exactly (pinglamb 13/97,
yachi 14/115) and costs 0.2–0.3 s per session.

| session | pinglamb | coverage | yachi | coverage |
|---|---|---|---|---|
| 2026-07-22 | 13/97 | 14.4% | 14/115 | 21.1% |
| 2026-07-24 | 12/81 | 19.8% | 11/72 | 17.5% |
| 2026-07-28 | 13/78 | 15.8% | 10/68 | 14.9% |
| 2026-08-01 | 11/61 | 12.6% | 11/82 | 17.7% |
| **pooled** | **49/317 = 15.5%** | 15.4% | **46/337 = 13.6%** | 18.1% |

654 verified T-spins, 95 forecast, **14.5%** overall — 3.1× the sample the published figures rest on.

## 2. What pooling buys, and what it kills

**Pooling is licensed, not merely convenient.** Cross-session heterogeneity is χ² p=0.865
(pinglamb), 0.931 (yachi), 0.978 over all eight cells. A single number is legitimate.

**It buys precision.** Clopper–Pearson: pinglamb [11.7%, 19.9%], yachi [10.2%, 17.8%], both
**14.5% [11.9%, 17.5%]** — interval width 5.5 pp against 14.5 pp on one session. Minimum detectable
between-player gap falls **16.1 pp → 8.6 pp**.

**It kills the round-level column, on held-out data.** The last commit touching the simulator or the
metric is `330774a`, 2026-08-01; the other three sessions were first run through it on 2026-08-02.
The fitting scripts (`fit-opts.ts`, `ab-*.ts`) load from the session directory, so `BEST_OPTS` was
tuned on 2026-07-22 alone — the other three are out of sample for the tuning as well as for the
metric. So 2026-07-22 is exploratory and the rest are confirmatory, and git is the audit trail:

| | W–L–T | decided | win-rate | p |
|---|---|---|---|---|
| 2026-07-22 (exploratory) | 11–5–19 | 16 | 68.8% | 0.210 |
| three unseen sessions | **17–17–43** | 34 | **exactly 50.0%** | **1.000** |
| pooled | 28–22–62 | 50 | 56.0% | 0.480 |

Tie rates are 54.3% and 55.4%, so this is **not** the tie-comparability artefact recorded twice
already in the findings doc. At 50 decided pairs there is **78.2% power against a true 70% effect**
(two-sided). The apparent 58.6% AUC did not survive contact with data it had not been tuned on.

**It does not license a between-player claim.** The gap is 1.8 pp (Fisher p=0.579, difference CI
[−3.9, +7.5] pp), and its **sign flips** under the `frame_clock` config — on 2026-07-22 alone it
never flipped. The level is simulator-robust; the difference is not. The section's existing refusal
to name a higher forecaster (`forecast_section.py:126`) is therefore load-bearing, and now has a
measured reason.

## 3. What Dafny can and cannot do here

Dafny proves *claim ⇔ extracted data*. Whether the simulator matches TETR.IO is an empirical
question about an external system, and no proof assistant settles it.

**In reach, and measured:** a ground-arithmetic layer over the emitted counts — pooled totals as
sums of the four sessions, the three classes partitioning the verified T-spins, floored rates pinned
by cross-multiplication, interval containment and overlap, the stability band. 17 lemmas verify in
**0.62 s** under Dafny 4.11.0 with flat consts and balanced trees; no Boogie hazard at this size.

**Out of reach, closed by name:**

* **Badging the rates.** The data is one simulator's output.
* **A Dafny reference implementation compiled to a second language.** One source, two binaries, and
  the wrong layer — the compiled classifier still consumes the single simulator's provenance grids,
  so the trust boundary moves from "the counts are simulator-derived" to "the provenance grids are
  simulator-derived", i.e. nowhere. It would also launder "Dafny-verified" onto a simulator, which
  is the extraction/simulation blur every audit round in this project has caught.
* **A second simulator, for now.** The dual-*extractor* argument does not transfer: extractors parse
  a recorded, documented format, so byte-agreement ≈ correct reading, whereas two simulators
  agreeing proves a shared *model* of TETR.IO. The binding gate is the game's own `results.stats`
  checksum; a second simulator is only meaningful after that passes.
* **Event-level analysis.** Its pre-declared negative control fires. Pooling makes a confounded
  estimate more precise, not more valid.

The available honesty upgrade is a **second classifier** (`forecast.ts` is 145 lines), consuming the
same board sequences, agreement checked per-T-spin rather than per-count — two wrong classifications
can cancel in an aggregate. It mints no badge; it narrows the single-implementation surface to the
simulator, and should be described in exactly those words.

Cost of the full dual-implementation, for reference: the instrument is **1194 lines** against the
existing dual extractors' 610.

## 4. Four defects, found by trying to write the proof

1. **`emit-forecast-facts.ts:108-112` used `Math.round`** for five x1000 fields, violating the gated
   「約 means the floored value」 convention — yachi 14/115 = 121.739 emitted as `122`, so the report
   printed 12.2% where 12.1% is correct. Neither gate could see it: `check_prose_figures` skips
   generated regions and `check_forecast_section` only checks HTML↔JSON, and both carried the same
   wrong value. Upper bounds must *ceil*, per `_bound_dp`.
2. **Nothing pinned `forecast_rate_x1000` to the counts.** `forecast-facts.test.ts` checked
   integrality, the count partition and CI ordering — never the rate. A corrupted rate passed every
   gate in the repo.
3. **`auc-power.ts:50` `minDetectable` is one-sided** while the document quotes two-sided p-values
   beside it. The published 158/69/37/23/18 table is exactly the one-sided column; two-sided is
   **199/90/49/30/20**.
4. **`forecast.ts:63`'s `4*10*H = 1600` bound is not established.** `vendor/core/srs.ts:129` is
   `if (row < 0) continue`, so any negative row is accepted and the row range is a reachability
   assumption; the T anchor column spans −1..8. The measured max of 688 is real, the derivation is
   not, and the `h < 40000` cap is a **live belt** rather than dead code.

## 5. The plan

**P0 — fix the four defects.** Independent of everything else, and P1 would otherwise propagate
defect 1 into three more sessions. The rate change cascades: emitter → `sim/forecast-facts.json` →
the rendered section → `report/report.html` → `docs/2026-07-22.html`.

**P1 — emit `forecast-facts.json` for the other three sessions. DONE 2026-08-02**
(`7cf7a88`, `0007cf0`, `e5f7a97`, `7b463b8`, `36eb81f`, `917ad7f`, `6cf827d`, `2cf2f27`).
All four sessions carry the section, rendered entirely from their own data. What this diagnosis
got right and what it missed is recorded in §6 below.

*The diagnosis, as written before the work:* **BLOCKED, and the blocker is not the
output path.** `pipeline/forecast_section.py` is a *shared* module, and lines 86–96 hardcode
2026-07-22's statistics into its Cantonese prose: 「AUC 58.6%，p = 0.210」, the event-level
「0.52 attack，95% CI [−0.34, 1.28]」, 「p = 0.848」, the split-half 「0.29（pinglamb）同
0.064（yachi）」 and 「全 158 個 player-round…只有 17.9%」. `emit-forecast-facts.ts`'s
`not_eligible_because` carries the same figures. Emit for another session as things stand and its
report publishes **07-22's statistics as its own** — and `check_forecast_section` **passes**, because
it only checks the per-player table, the 未經證明 string and the absence of badges. That is the
「session-1 numeric leakage into session-2 prose」 class this project has already been bitten by
once. So P1 is: first make the schema carry per-session statistics (or drop the session-specific
numbers from the shared prose), *then* parameterize the output path.

Each session's landing must also be **atomic** — its `forecast-facts.json`, its rebuilt
`report.html` and its rebuilt `docs/` copy in one commit — because `check_forecast_section` flips
behaviour the moment the JSON exists, from "must have no forecast region" to "must match exactly".

### P1, step by step

Six figures are hardcoded in the shared module, and they come from three places:

| figure | source | reusable as-is? |
|---|---|---|
| round AUC 58.6%, p = 0.210 | `pairs.ts` + `auc-power.ts` | yes — already exports `collectRows`/`pairsFor`/`auc` |
| event-level +0.52 attack, CI [−0.34, 1.28], negative control | `forecast-event-level.ts` | no — top-level printer |
| player-level p = 0.848 | `forecast-event-level.ts` | no — top-level printer |
| split-half 0.29 / 0.064 | `validity-checks.ts` | no — top-level printer |
| 158 player-rounds, 17.9% coverage | — | yes — already derivable from the schema |

**Step 0 — the cache key (DONE).** `pairs.ts` keyed its cache `v3|{strict}|rows={strictRows}` with
no replay directory, in a single file beside the code rather than beside the session. One run with
`REPLAY_DIR` pointed elsewhere would have written that session's rows under this one's key, and the
next 07-22 run would have read them back as its own. Latent until the metric went cross-session,
which P1 does. The directory is now in the key and `CACHE_V` went 3 → 4 so no pre-existing entry can
match by accident. Verified: 79 rows for 07-22, 64 for 07-28, no collision.

**Step 1 — make the computations reusable.** Convert `validity-checks.ts` and
`forecast-event-level.ts` from top-level printers into exported functions plus a thin
`import.meta.main` printer, the shape `pairs.ts` already has. Acceptance: each script's stdout is
**byte-identical** before and after. The alternative — a second copy of the statistics inside the
emitter — is the duplication this repo has twice watched drift.

**Step 2 — extend the schema** to `forecast-facts/2` with a `statistics` block: round AUC, W–L–T,
decided pairs and exact p; the event-level difference, its cluster CI, and the negative control's
own difference and CI; player-level p; split-half r per player; coverage and round count. **Every
field nullable, and null must be rendered as an absence**, never as 0 — a later session may have too
few events, and a fabricated zero would be published as fact. This is `claim_cards.round_operand()`'s
rule: a value of the wrong shape yields nothing rather than an invented number.

**Step 3 — render the prose from that block**, so no figure in the module is a literal and each null
has a sentence-level fallback. Fold in the correction that the section's 「樽頸唔係模擬器準唔準，而係
局數唔夠」 claim is **unproven**: the seven-config sweep bounds fitted-parameter sensitivity only, and
model-form error was never probed.

**Step 4 — strengthen the gate, and this is the load-bearing step.**
`check_forecast_section.py` today checks the per-player table, the 未經證明 string and badge absence,
and ignores the method note — which is exactly why the leak passes. Extend it to resolve *every*
figure in the section against the JSON. **Acceptance test: plant 2026-07-22's AUC into 2026-07-24's
rendered section and require the gate to fail.** If it does not, the gate is decorative and P1 is
still blocked, whatever the prose says.

**Step 5 — parameterize the emitter's output path** and emit per session, one atomic commit each.

Steps 0→4 are serial; step 4 can be written against 07-22 while 2 and 3 are in progress, but its
acceptance test needs a real second session.

**P2 — promote `sessions/2026-07-22/sim/` to `pipeline/sim/`. DONE 2026-08-02.** All three
predicted breakages were real and are fixed: `loadCases`' default, the emitter's output path, and
the `.gitignore` pattern. The default was not in one place but **26**, each file carrying its own
copy of ``process.env.REPLAY_DIR ?? `${import.meta.dir}/..` ``; they are now one `replayDir()` that
refuses to guess, because from `pipeline/` that default finds zero replays and `readdirSync`
SUCCEEDS on it — every runner would have computed over zero rounds and emitted zeroes instead of
failing. Proof the move changed no behaviour: the emitter reproduces all four committed artifacts
byte-for-byte, and the suite is 45 pass / 0 fail before and after. Original note follows.

**P2 (original diagnosis).** Note
CI is *not* the coupling: no CI job executes any `sim/*.ts`. The real breakages are `loadCases`'
default `${import.meta.dir}/..` (`verified-prefix.ts:36`) no longer resolving to a session, the
emitter's output path, and `.gitignore:20`'s `sessions/*/sim/pairs-cache.json` pattern silently
ceasing to match. Do it after P1 proves multi-session use, as a pure `git mv` plus path
parameterization with no behaviour change.

Separately and regardless: `pairs-cache.json` is keyed `v3|strict|rows=…` with **no replay
directory in the key** (`pairs.ts:34`), so running any pairs-based script with `REPLAY_DIR` pointed
elsewhere silently poisons 07-22's cache. Add the directory to the key.

**P3 — the pooled figure goes on `docs/`, never inside a session report.** Three reasons: the
section is session-scoped *because* a cross-session graft already shipped as a bug once; pooled
numbers move when session five lands, and a committed report must not contain retroactively-changing
figures; and `docs/` is the only surface whose contract is already "current corpus view". Hard
constraint: it must be emitted by `bin/build-docs` itself and covered by its `--check`, or it sits
outside the only docs gate — which is the exact incident that gate was built for, when the forecast
section existed in the session report and was missing from the published page.

**P4 — the Dafny arithmetic layer, plus a per-lemma vacuity gate.** The gate is not optional: on the
prototype, per-*constant* mutation reported **32/32 killed** while **3 of 17 lemmas were
tautologies** (their bounds written with literals instead of over the constants — the same bug
ROADMAP P4 records as `50 == 50`). `check_dead_consts` covers the dual case, a constant no lemma
reads; neither gate covers the other. The harness needs its own control: a deliberately vacuous
lemma that must be caught, and an assertion that the isolated unmutated lemma reports `1 verified`
before any mutation runs — `dafny verify` on a file with zero lemmas prints "0 verified, 0 errors"
and exits 0, so a uniform verdict means the harness is broken, not that the lemmas are.

**Placement rule for P4, non-negotiable:** every forecast proof artefact lives under `sim/`, never
under `report/`. Three globs misbehave silently otherwise — `bin/build-docs`' `summarize()` sums
every `*proof-map*.json` in the artefact directory into the site index's 「已驗證 claim」 count, so
simulator-derived lemmas would inflate the public verified-claim total; `bin/verify-session:63`
runs `check_claims` over every `claims*.json` against `facts.json`, which forecast fields are not
in; and `:82` globs `proof-map*.json` the same way.

## 5b. OPEN DEFECT — the forecast bucket is substantially the C-Spin opener (2026-08-02)

Raised by the user against the three real examples published in the boards explainer; all three
are C-Spin setups. Verified against the wiki and then measured. **This invalidates the published
14.5% as a measure of forecasting**, and is the most serious defect found in this metric so far.

**What the wiki actually requires.** T-Spin Forecast is "a playing style that predicts and sets up
T-spins in advance. A player stacks so that T-Spins would emerge **from line clears or upcoming
garbage**" — the sub-headings are "In anticipation of an empty garbage column". The emergence
mechanism is part of the definition.

**What a C-Spin is.** "The C-Spin (TKI積み) is a kind of Triple Double Attack... the 'C' shape that
is formed by the J and L... it results in a T-Spin Triple which is usually followed by a T-Spin
Double within three bags. **As an opener**, it is most often built with an ZST core whereas **L and
J are used to build the overhang**." It is a memorised first-bag opener whose overhang is placed,
by construction, before the slot exists — and the slot then emerges from **the player's own
subsequent stacking**, not from garbage or a line clear.

**Why the metric cannot tell them apart.** `forecast.ts` classifies on CO-OCCURRENCE, never
causation: `garbageBetween` is only `r.garbageEvents.some(g => g.lockIndex > j && g.lockIndex <= k)`.
At the measured median separation of ~11 pieces, *some* garbage arriving is close to certain, so any
opener whose overhang predates its slot is labelled `forecast_garbage` by default.

**Measured on 2026-07-22 (212 verified tucked T-spins):**

| cut | forecast rate |
|---|---|
| all verified T-spins | 27/212 = **12.7%** |
| roof placed after piece 8 | 13/153 = 8.5% |
| **roof placed after piece 10** | **4/105 = 3.8%** |
| roof placed after piece 12 | 3/63 = 4.8% |

**85% of forecast roofs are placed within the first 10 pieces**, against 45% for reactive. Removing
the opener collapses the rate from 12.7% to 3.8% — i.e. roughly **five sixths of the forecast bucket
is opener execution**. The line counts corroborate it: the bucket is 16 doubles and 10 triples, which
is exactly the C-Spin's "Triple Double Attack".

**And the garbage label is never directly evidenced: `roofIsGarbage` is true for 0 of 212 T-spins,
including 0 of the 14 `forecast_garbage` events.** Not one slot in the corpus has a roof actually
made of garbage.

**Compounding it, the instrument can only see the opener.** The verified prefix has median length 25
pieces, so the observable window IS the first three bags — precisely where memorised openers live.
This is the same bias `sim/README.md` already records as "systematically the *early* part of each
round", now with a specific consequence.

**Remedies, none applied yet — this changes published figures in four sessions and is the user's
call:**
1. **Require causation, not co-occurrence.** Recompute `tspinAvailable` on a counterfactual board
   with the garbage rows removed; label `forecast_garbage` only if the slot exists WITH the garbage
   and not without it. Same idea for a line clear. This is the correct fix and kills the confound at
   its root.
2. **Report the opener-excluded rate as the headline**, with the full rate as a secondary figure.
3. **Withdraw the level figure** and publish only the null, until (1) exists.

Until one is done, the 14.5% pooled figure and the per-session rates should be read as "tucked
T-spins whose overhang predated the slot", NOT as forecasting.

## 6. What is unresolved, and must be said wherever the figure is printed

**Whether 14.5% is a floor or a ceiling on a whole-round rate is unknown.** Within-prefix quartiles
rise (9.1% → 15.9%); absolute piece-index buckets fall (15.4% → 12.7% → 0). Both views are
confounded, because a forecast requires prior events and the earliest pieces of any round cannot
qualify. Every published figure is scoped to **early-round verified T-spins** and prints its
coverage beside it.

**"Sampling-limited, not simulator-limited" is unproven, not established.** The ±1.1–1.2 pp
seven-config range bounds *fitted-parameter* sensitivity; model-form error was never probed.
`forecast-facts.test.ts` asserts the claim as if it were established, which overstates it.
*Partly addressed 2026-08-02 (`e5f7a97`):* the rendered prose no longer says the bottleneck 「唔係
模擬器準唔準」. It states the ratio it measured and then says outright that the sweep cannot see an
error all seven configs share. The bun guard's name still overstates what it checks; the claim
itself remains unprobed.

### What P2 turned up: a test constant fitted to the tuning session

Making the simulator session-agnostic let its own test suite run somewhere other than
2026-07-22 for the first time, and `ige-y-oracle.test.ts` immediately failed on the other three.
It asserted the ige row oracle agrees with ground truth on `> 90%` of verified attacks, over
`> 200` checked attacks. Measured 2026-08-02:

| session | checked | agreement |
|---|---|---|
| 2026-07-22 (tuning) | 293 | **90.4%** |
| 2026-07-24 | 237 | 80.6% |
| 2026-07-28 | 197 | 86.8% |
| 2026-08-01 | 219 | 82.6% |

2026-07-22 is the session `BEST_OPTS` was fitted on, and it clears its own threshold by 0.4
points. Out of sample the oracle is 4-10 points worse, and 2026-07-28 also falls under the
`checked > 200` floor. Neither constant was ever a specification; both were read off the only
session the test could reach, which is the same defect as the round-level AUC that did not
replicate — and the same one as a gate exercised only against the input it already passes.

The constants are now a labelled regression floor (0.75 agreement, 100 checked) with the real
per-session rates recorded beside them, rather than a re-fit to whichever session is worst.
Mutation-tested so the looser floor is not decorative: an oracle off by one row scores 0-1%
agreement on every session, so genuine breakage still fails by a wide margin.

**This is a real limit on the verified prefix and should be treated as one.** The prefix gate
`frame+amount+row` accepts a placement only if the row oracle agrees, so a ~10-point out-of-sample
drop in that oracle is a drop in the evidence the forecast metric rests on. It is not yet known
whether the disagreements are oracle error or simulator error.

### What P1 taught, beyond its own scope

**A containment gate cannot catch an invented figure, and this one didn't for four sessions.**
`check_forecast_section` verified that every JSON figure *appeared* in the HTML. That passes just as
happily when the section *also* contains figures that came from nowhere — which is what the entire
method note was. Re-rendering and comparing byte-for-byte is complete where containment is sampled,
and it is the argument `verify-session` already makes twice (extractor reproduces facts, codegen
reproduces `.dfy`). Prefer *reproduce and compare* over *look for the expected substring*.

**Hardcoded prose hides two things, and the conclusions are the more dangerous half.** The six
figures were the visible defect. Underneath them sat 「統計結論係：搵唔到效果」, 「negative control
有反應」, 「兩個玩家嘅區間幾乎完全重疊」 and 「攞七個設定」 — *conclusions* asserted without
consulting the data, in a module rendered for every session. Two survived the first pass because they
are true of all four sessions today. **An assertion that happens to hold is indistinguishable from a
derivation until the day it does not**, so it cannot be found by reading the output; only by asking
of each sentence "which field decides this?".

**Both defects the cross-session extension surfaced were in checks, not in the code under test.**
One rounding rule in the emitter's prose and one in its data disagreed only where a correlation went
negative (07-24), and the guard's regex dropped the minus sign. The gate's self-test planted figures
into the whole document, so on any session but 07-22 the plant landed outside the region. Both are
the same lesson: **a check exercised only against the one input it already passes on has never been
shown to fail.** The fix in both cases was to derive the check's inputs from the artefact rather than
write them as constants.

**The corpus answered the round-level question on its own.** All three sessions held out from the
exploratory work read AUC exactly 50.0% with p = 1.000, against 58.6% on the session the metric was
developed on; split-half reliability is negative on three of the four players outside 07-22. The
per-round column does not replicate, and now says so in each session's own numbers.

The one known-missing mechanic cannot currently settle it. `lineclearAre` is plumbed
(`sim.ts:114`, `:335`) but is in no config; adding it moves the rate 14.5% → 10.3% and halves
coverage — yet running the best config *truncated to are34's own prefix* gives **10.3% vs 10.3%**,
so classifications are unchanged and the move is pure prefix-length selection. The mechanism is that
`applyEvent` drops the *action* of a keydown while `f < areUntil` (`sim.ts:396`), including
`hardDrop` at `:414`, which desyncs immediately. (`held.add` runs *before* that return and keyups are
never gated at `:416-423`, so "dropped keyup / DAS corruption" is the wrong explanation.) A config
that were merely more accurate could not verify *less*, so the delay as implemented is farther from
the client, not closer — it is ROADMAP 3c work, not a sensitivity config.

## 7. Provenance of the numbers in this document

The per-session counts for 2026-07-24, 2026-07-28 and 2026-08-01 were computed in-session on
2026-08-02 by pointing the committed instrument at those replay directories. **All four sessions now
have a committed `forecast-facts.json`** (P1, 2026-08-02); the figures quoted in this document
predate those artefacts and were produced by the same instrument, so where the two differ the
committed artefact is authoritative — notably the p-values, which the schema CEILs (0.210 -> 0.211,
0.848 -> 0.849) so that a rounded p never overstates significance. Statistics were computed in R 4.6.1 using
its own exact tests (`binom.test`, `fisher.test`, `prop.test`) rather than hand-rolled tails,
because this project has twice been bitten by a recalled statistical constant.
