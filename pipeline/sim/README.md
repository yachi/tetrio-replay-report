# `sim/` — the T-Spin Forecast instrument

The code behind [`sessions/2026-07-22/forecast-metric.md`](../../sessions/2026-07-22/forecast-metric.md). Committed 2026-07-30 because
every number in that document was, until then, reproducible only from a `/private/tmp` scratchpad
belonging to a session that had ended.

**This is not part of the report pipeline.** Nothing here feeds `facts.json`, no claim cites it,
and CI does not run it. It is deliberately excluded — see *Why it is not in the report* in the
findings doc. It lives here so the negative result stays checkable, not so it can be promoted.

## Running it

Requires `bun`. No install step; there are no dependencies.

This code is **session-agnostic**: it lives in `pipeline/` and is pointed at a session, rather
than living inside one. Every runner therefore needs `REPLAY_DIR`.

```fish
cd pipeline/sim
set -x REPLAY_DIR (git rev-parse --show-toplevel)/sessions/2026-07-22

bun test forecast.test.ts wiki-fixtures.test.ts property-forecast.test.ts forecast-corpus.test.ts arrival-key.test.ts
bun run mutate-forecast.ts   # defaults to the fixture files PLUS forecast-corpus.test.ts
bun run board-metrics.ts ../../sessions/2026-07-22   # ROADMAP triage of board-derived metrics
bun run run-forecast.ts
bun run auc.ts
bun run auc-power.ts     # read this before quoting any AUC
bun run bfs-cap.ts
```

Emitting a session's forecast artifact — `--out` is required, because this code no longer
belongs to a session and must not guess which one you mean:

```fish
REPLAY_DIR=sessions/2026-07-24 bun pipeline/sim/emit-forecast-facts.ts \
    --out sessions/2026-07-24/sim/forecast-facts.json
```

`REPLAY_DIR` is resolved by `replayDir()` in `verified-prefix.ts`, which **fails** when it is
unset, missing, or contains no `.ttrm`. It used to default to `../`, which only worked because
this directory sat inside a session; from `pipeline/sim` that default would have found zero
replays and every runner would have computed over zero rounds and reported zeroes rather than
erroring.

`LOOSE=1` switches the classifier to the discarded loose rule, for comparison only.
Pairing is simulated once and cached to `pairs-cache.json` (gitignored; delete to force a re-run).
The cache key includes the replay directory, so pointing `REPLAY_DIR` at another session cannot
poison this one's entry.

Expected output, all four re-measured against `sessions/2026-07-22` on **2026-08-10**:

| command | result |
|---|---|
| the `bun test` line above | 103 pass, 0 fail, 8200 assertions, **8 files** |
| `mutate-forecast.ts` | 50/50 killed |
| `run-forecast.ts` | pinglamb 97 tucked / 0 forecast / 0.0% · yachi 115 / 0 / 0.0% |
| `auc.ts` | 50.0 · 50.0 · 50.0 · 57.0 · 50.0 — every forecast metric ties now that the rate is 0 |

The `run-forecast.ts` row read `pinglamb 97 tucked / 13 forecast / 13.4%` until 2026-08-08, while
the row directly beneath it said "every forecast metric ties now that the rate is 0" — the same
table asserting both 13.4% and 0 at once. Two separate bugs in that runner produced the 13.4%: its
per-user totals omitted a `self_built` key, so `tot[rec.kind]++` was `NaN` for 388 of 654 records and
the printed breakdown did not sum to its own header; and both the rate and the robustness cuts
counted `kind !== 'reactive'`, the idiom `isVerifiedForecast` exists to abolish, which scores every
opener as a forecast. Both now route through `isVerifiedForecast`. **Nothing re-runs this table, so
it goes stale silently — re-measure it whenever you touch the metric.**

The bottom two rows moved since they were written on 2026-07-30, and the table said nothing
about it because nothing re-runs it. What changed:

* `run-forecast.ts` read `yachi 89 / 11 / 12.4% · pinglamb 78 / 10 / 12.8%`. The counts grew
  because the verified prefix did; the rates moved because the emitted rate now FLOORS rather
  than rounds. Note the two columns had also been printed in the opposite order to the runner's
  own output, which prints pinglamb first.
* `auc.ts` read `61.4 · 57.7 · 52.5 · 46.2` — four values for what is now **five** metrics, so
  the row could not be lined up against the output even in principle once `separation-weighted`
  was added. `forecast rate` is 58.6%, not 61.4%.

These are a regression reference, not golden data: they record what this repo's own runners
produce, so re-measuring them is correct. The wiki fixtures are the opposite — an external
oracle that must never be regenerated from this engine. Re-measure this table whenever the gate,
the rounding, or the metric set changes, and date it.

## What is verified, and how

- **Mutation — 50/50.** `mutate-forecast.ts` patches `forecast.ts`, runs the suite, restores.

  **This file used to claim the harness validated itself with control mutants — "three
  semantics-preserving edits must survive and a poison mutant (spawn column 3→9) must die". No
  such mutants exist, and none ever did.** At `0dde1d8`, the commit that wrote that sentence, the
  harness held 11 entries and contained neither the word `spawn` nor any notion of a control; at
  `2911eb8` it held 49, still with no `spawn` and no expected-verdict field. `git log --all -S`
  finds no such entry in any commit. The sentence described a regime nobody built, and its
  companion — "a sweep where everything dies is a syntax error, not a passing gate" — condemned
  every honest run this harness has ever produced, since with no controls **50/50 killed is the
  correct result**. It was false on the day it was written and survived because it reads exactly
  like the kind of thing this project does do.

  The machinery now exists even though the controls do not: each entry carries an optional
  `expect`, defaulting to `killed`, and the run fails when any observed verdict differs from its
  expected one — so a killed control fails as loudly as a surviving mutant. That is what makes a
  control *possible*, and it forces an equivalence claim to be declared rather than tolerated,
  which is this file's own doctrine: a surviving mutant is either a missing test or a
  proven-equivalent mutant, and "probably equivalent" is not a status this project accepts.
  Adding the controls is open work.

  Two failure modes it could not report until 2026-08-10, both of which had already bitten it.
  A find string that no longer matches used to throw and **abort the sweep mid-list**, after
  printing a wall of `killed` lines and no summary — which reads exactly like success. It had been
  doing that at mutant 46 of 49 for some time, so mutants 46-49 had never run at all and the
  count quoted here was stale in both numbers. A stale entry is now reported as `STALE`, the sweep
  continues, and the run exits non-zero naming every one — because **a mutant that cannot be
  applied is not a mutant that was killed, and the old output could not tell you which happened.**
  The run also now fails when any mutant's observed verdict differs from its **expected** verdict,
  which is stricter than "a survivor fails" and is what keeps the controls honest: a killed
  control is as much a failure as a surviving mutant.

  **Do not run this against the worktree while anyone is editing `forecast.ts`.** It snapshots the
  file at startup and restores that snapshot unconditionally at the end, with no check that the
  file moved underneath it — so a concurrent write is silently overwritten. For the same reason a
  planted mutant sitting in the tree is indistinguishable from ordinary work by every summary
  statistic: a one-line mutation is exactly `+1/-1` on `git diff --stat`, and a test run against a
  planted tree reports plausible failures that are not regressions. Both traps were hit on
  2026-08-10. Verify restoration with `cmp` against a pre-sweep copy, never with "the tests pass
  again".
- **Attribution is measured.** `strip-tests.ts` removes named tests so a kill can be traced to
  them. Strip the two rotation/spin fixtures and 6 mutants survive; restore them and it is 11/11.
- **Property tests over 932 seeded random boards** (`property-forecast.test.ts`), with an
  anti-vacuity gate: 84 of them must actually offer a line-clearing T-spin, or the suite proves
  nothing. Seeds are MINSTD, so any failure reproduces.
- **External golden data.** `wiki-fixtures.test.ts` reads
  `wiki-tspin-forecast-boards.json` — 29 board diagrams parsed from harddrop.com. The boards
  *and* the expectations come from the wiki, never from this engine. There is one copy of that
  file and this test reads it; do not add a second.
- **A second, Japanese corpus.** `jp-forecast.test.ts` reads `jp-forecast-boards.json` — the 38
  T-Spin Forecast (予報の技法) diagrams from Tetrisちゃんねる. Harddrop encodes its boards as HTML
  cell-tables, so they parse from text; this page ships JPEGs, so the grids are read by a
  deterministic pixel sampler (`extract_jp_forecast.py`) over the images committed under
  `spec/fixtures/jp-forecast/` — never by eye, so it is not single-source hand data. The bun test
  is the CI gate (integrity, image binding, palette coverage, three human-read golden anchors);
  `python3 -m pipeline.sim.extract_jp_forecast` re-extracts byte-identically from the images
  (needs Pillow). These are step-by-step setup frames with no per-board label, so — unlike the
  harddrop set — the section-premise spin checks do not apply and are deliberately not asserted.
- **A third, four.lol corpus.** `four-forecast.test.ts` reads `four-forecast-boards.json` — 26
  frames decoded from the nine forecast-section **fumen** codes in `four-forecast-fumens.json`
  (four.lol's board diagrams are fumen-backed, credited to kazu). Capturing at the fumen layer
  sidesteps four.lol's build-hashed styled-component DOM entirely: the fumens are stable authored
  content, decoded by the `py_fumen` library (`extract_four_forecast.py`) — a trusted third-party
  decoder, so any fumen tool reproduces the same boards. Same conventions and caveats as the JP set.

### Do the external examples let us detect MORE forecasts? (2026-08-09) — no, and it is proven

The three corpora were then turned on the detector itself, to hunt for a false negative — a real
forecast the metric misses, which is the only honest way the count could rise (loosening the
definition just re-imports the co-occurrence bug). Two probes, both committed:

- **Reachability** (`reachability-external.test.ts`, driver `reachability-external.ts`). The numerator
  rests on `bestTspin` finding every executable spin; if it under-reads `avail(t)`, a real
  improvement is scored `reactive`. Every JP / four.lol frame that draws a newly-placed,
  line-clearing T witnesses a reachable spin — strip the T and the engine must re-find it. Result:
  **0 misses** across all witnesses. The engine's reachability is complete on the corpora (the three
  C-Spin diagrams `wiki-fixtures` marks `UNREACHABLE` need a 180 the players never press, and none is
  an executed spin here).
- **Clause logic** (`lift-external.test.ts`). The cleanest genuine forecast the corpora draw —
  Tetrisちゃんねる's `foreacast_004..009` (Z overhang → an L that clears the opening row → a T tuck) —
  is lifted into a `SimResult` and run through the real `forecastMetric` (`localiseMechanism`'s step
  assertions throw on a bad lift, so the verdict can't be faked). It classifies **`reactive` at
  `separation === 1`**: the cell roofing the T was placed by the same lock that cleared the row, so no
  step lies between roof and tuck. That is the concrete instance of the machine-checked theorem
  `spec/Forecast.dfy:SeparationOneIsNeverAForecast` (`k == j+1 ⇒ !IsForecast`), witnessed in
  `spec/ForecastExamples.dfy:ExternalForecastExampleReducesToSeparationOne`. A second named exemplar,
  JP `foreacast_029..031`, gives the *other* honest outcome the sweep lumps together — an **untucked
  self-build** (the T fills an open right-side well, nothing roofing it), which the detector records
  as **no forecast at all**.

**All 64 external frames were then audited for a liftable multi-step forecast (2026-08-09), so "that
is all of them" is measured, not asserted.** Exactly three draw a newly-placed line-clearing T (JP
008/031/037); `004..009` is the only one that lifts as a faithful single-piece-per-step sequence, and
it is reactive/sep-1. JP 031 is the untucked self-build above; JP 037's tuck is real but its roofing O
is drawn in the *same* frame as two other pieces, so it can't be lifted as named steps without
inventing frames — and its roof is in the immediately-prior frame regardless (sep-1). four.lol is the
same: every executed spin is a single-frame tuck (sep-1, covered by the sweep) or a multi-piece
illustration jump. **No additional named lift can surface a separation ≥2 forecast — the corpora do
not draw one beyond `004..009`.**

So the examples **corroborate** the 0-of-654 count rather than raise it: the detector reaches every
spin they draw and is provably right to reject the one forecast they draw cleanly. Detecting more
would require extending the **verified prefix** (only 13.8% of placements, systematically early-round)
— a simulator-fidelity project (the line-clear-delay attack model), not something the examples reach.

### Can sequence alignment extend the verified prefix? (measured: no)

`prefix-alignment-probe.ts` tests the obvious academic lever: `verifiedIndex` cuts the prefix at the
first POSITIONAL mismatch of the outgoing-vs-received attack streams, so a single divergence truncates
the rest — exactly what global sequence alignment (Needleman–Wunsch) / DTW exist to survive. The
honest guardrail: a placement is verified only if its board matches, witnessed by the attack's
amount+row, and the streams are 1:1 — so alignment may relax only the timing, never amount+row.
Measured over all four sessions, that maximal honest relaxation recovers **+2 attacks total and 0
extra forecasts**; the LCS-with-gaps ceiling (+81) is illusory because every gap is a non-1:1 match,
i.e. a genuine board divergence. The one avenue timing-relaxation can't reach — **perfect-clear
re-anchoring** (restart a verified interval at a mutual all-clear, where both boards are provably
empty, an exact mid-round oracle) — is measured too: across all four sessions it yields **1 valid
re-anchored interval and unlocks 0 forecasts** (bounded because the sim reproduces only ~7 of the
~19 real PCs). So both honest alignment avenues are exhausted. The greedy break is a real board
error, not a timing artifact, so no alignment/DTW/HMM/PC-re-anchor can extend coverage — the wall is
the garbage-insertion model (system identification of the line-clear delay, which isn't even in the
replay options and must be estimated), not the prefix gate.

### Is the 0 a coverage artifact? Independent test, ignoring garbage (answer: no)

`coverage-forecast-probe.ts` attacks the question from the other side: extend coverage by algorithms
INDEPENDENT of the attack-timing gate, ignore garbage (the mechanism that caps coverage), and count
line-clear forecasts. Three levers: the repo's BOARD-ONLY `frame+row` gate (drops the attack-table
constraint a table error can wrongly truncate; +~140 placements); the **pre-garbage deterministic
oracle** (before the first received garbage the board is a pure function of inputs+seed, verifiable
with no garbage model — +2,192 placements, up to +47% in a session); and the absolute ceiling (the
whole round, 100% coverage). Every one finds **0 verified line-clear forecasts**, and at the ceiling
there is exactly **1 forecast_lineclear-labelled event across all four sessions, clause-rejected**.
So the 0 is not hidden by the verified prefix — line-clear forecasts are absent by nature (this
corpus is openers and self-builds). The count moves only with a genuine change in play.

### Positive control: the detector DOES fire on a generated forecast

Every test above is a negative control (real play, correctly not counted), which leaves open the
worry that the 0 is a broken always-rejecting detector. `generated-forecast.test.ts` closes it: it
GENERATES the spec's canonical forecast — Example A, J overhang over a pre-existing hole, a vertical
I clearing the three rows between (non-spin), a T tuck for a Double — lifts it into a SimResult, runs
the real `forecastMetric`, and it **verifies (forecast_lineclear, separation 2)**. Example B (a
single) verifies too; F (T never spun) and G (slot pre-complete, separation 1) are rejected — and all
four match the verdict the Dafny spec proves. So the corpus 0 is a true negative: the detector fires
on a real forecast, it just never sees one in these replays. This is the one place the repo's three
representations — ledger data, Dafny proof, and the simulator detector — are shown to agree on live
boards.

`generated-forecast-fuzz.test.ts` scales that to **100 generated examples** under a seeded PRNG:
four base shapes (A, B genuine; F, G near-misses), each drawn with a random horizontal mirror and a
random overhang piece, lifted and run through the real detector. **100/100 classified correctly** —
every genuine forecast detected (both handedness, via the mirror axis), every near-miss rejected.
The corpus 0 is a true negative at scale, not a blind spot.

`generated-forecast-montecarlo.test.ts` asks the complementary question — does a forecast arise by
**chance**? A hole-avoiding heuristic bot (minimise aggregate height, holes and bumpiness, with
jitter) plays 100 games of up to 150 pieces through the real SRS engine (spawn → move/rotate →
hardDrop → lock → clear), and every line-clearing T is *generously* marked a spin to give the
forecast path maximum opportunity. Deterministic (seed 7): ~3,600 line clears and ~460 line-clearing
T-spins are produced, `forecastMetric` runs on all of them **without throwing**, and finds **0
forecast records / 0 verified forecasts**. That is the mechanism, not luck — a forecast requires an
overhang deliberately laid over a *pre-existing* hole and opened by an *earlier external* clear, the
exact opposite of the clean stacking a hole-minimiser does. Forecasts are a deliberate act; they do
not occur by chance. This reproduces the corpus 0 from first principles and shows the detector does
not false-positive on ordinary play.

### Forecast example sources swept (2026-08-09)

The question "is that every forecast example on the internet?" has been asked and answered, so it
is recorded here rather than re-litigated. The three corpora above (harddrop 29, harddrop/C-Spin 38,
Tetrisちゃんねる 38, four.lol 26) are the distinct machine-capturable example sets found. What was
checked and NOT captured, with the reason:

- **tetris.wiki/T-Spin_Forecast** — the modern Hard Drop relaunch. Its 23 `<playfield>` diagrams
  were parsed from `?action=raw` and compared cell-by-cell (wildcarding the don't-care columns):
  all 23 are contained in harddrop's 29. A strict subset — nothing new.
- **tetris.fandom.com/wiki/T-Spin_Forecast** — a Hard Drop mirror, and egress-blocked (403). Its
  content duplicates the harddrop page.
- **namu.wiki (KO), tetris.huijiwiki.com / zhihu (ZH), winternebs TETRIS-FAQ, Galactoid, YouTube** —
  prose, general-T-spin, or video; no distinct forecast example-board collection. TETRIS-FAQ embeds
  four.lol/fumen rather than carrying its own boards.
- **Coverage** — 100% of lines and functions in `forecast.ts`.

## Two hazards worth knowing before you trust output

**`vendor/core/` is a patched copy, not a clean one.** It comes from
`github.com/yachi/td-opener-trainer` at `fa596ee`, with `BOARD_VISIBLE_HEIGHT` changed from 20 to
40 (20 visible + 20 buffer). `srs.ts` bakes that constant into `isValidPosition`'s floor check, so
a fresh clone of the trainer **silently** locks pieces at row 20 and yields wrong boards with no
error. The patch was uncommitted in the original scratchpad clone. Vendoring is what makes this
directory reproduce; re-cloning upstream would not.

**Coverage is 13.8% of placements, and it is biased.** The simulator matches the real game on
2001/14517 placements across 88/158 rounds, and those are systematically the *early* part of each
round, when garbage pressure is lightest. Every figure here is a verified-prefix figure, not a
match-level rate. `validate.ts` is what establishes which prefixes are trustworthy.

## Files

| | |
|---|---|
| `sim.ts` | the replay simulator — RNG, board, attack table, garbage |
| `forecast.ts` | the metric: `bestTspin`, `localiseMechanism`, `forecastMetric` |
| `audit-mechanism.ts` | reports which mechanism raised each improved event, across the sweep |
| `forecast-boards.ts` | re-export shim so fixtures import one surface |
| `*.test.ts` | unit, external-golden, and property suites |
| `mutate-forecast.ts`, `strip-tests.ts` | mutation harness and kill attribution |
| `bfs-cap.ts` | how far the BFS runs from its cap — but against a REPLICA of the search, see below |
| `pairs.ts` | winner-vs-loser pairing, shared by both AUC consumers |
| `run-forecast.ts`, `auc.ts`, `validate.ts` | the runners that produce the published figures |
| `auc-power.ts` | CIs, exact tests, power, and required sample size for those figures |

## `bfs-cap.ts` measures a replica, and its number is a state count

**It does not import `forecast.ts`.** Its imports are `sim.ts` and `vendor/core/srs.ts`; it walks
its own copy of the search. So whatever it prints is structurally blind to any change in the real
BFS — it cannot disagree with an engine it never calls, and an agreement it reports across two
variants of that engine is therefore worth nothing as evidence. Point it at the real `bestTspin`
before quoting it again.

The figure it used to be quoted for, `max 688 over 2000 boards`, is also easy to read as the wrong
quantity: it is the **largest number of states any sampled board reached**, which is what the
20000 / 40000 caps are counted in. It is not a bound on queue length, and it is sampled evidence
rather than a proof — the file's own header says so, and says the caps stay live belts because of
it.

## Do not quote an AUC from here without `auc-power.ts`

`forecast rate`'s 61.4% rests on **11 decided pairs** — 95% CI [39%, 94%], 31% power against a
true 70% effect. It would need a 9-of-11 sweep to reach p < 0.05. Only `tucked T-spins`
(54 decided pairs, 90% power) supports a genuine negative result.

`auc-power.ts` self-checks its statistics against the defining equations before printing anything.
That check has already caught two real bugs: a Clopper–Pearson upper bound printing 0% because the
bisection assumed an increasing function, and a "textbook" constant recalled from memory that was
wrong in the fourth decimal. Neither was visible in the output.
