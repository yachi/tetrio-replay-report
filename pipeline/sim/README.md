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

bun test forecast.test.ts wiki-fixtures.test.ts property-forecast.test.ts forecast-corpus.test.ts
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

Expected output, all four re-measured against `sessions/2026-07-22` on **2026-08-08**:

| command | result |
|---|---|
| the four test files | 68 pass, 0 fail, 1008 assertions |
| `mutate-forecast.ts` | 42/42 killed |
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

- **Mutation — 24/24.** `mutate-forecast.ts` patches `forecast.ts`, runs the suite, restores.
  The harness validates itself with control mutants: three semantics-preserving edits must
  **survive** and a poison mutant (spawn column 3→9) must **die**. A sweep where everything dies
  is a syntax error, not a passing gate.
- **Attribution is measured.** `strip-tests.ts` removes named tests so a kill can be traced to
  them. Strip the two rotation/spin fixtures and 6 mutants survive; restore them and it is 11/11.
- **Property tests over 932 seeded random boards** (`property-forecast.test.ts`), with an
  anti-vacuity gate: 84 of them must actually offer a line-clearing T-spin, or the suite proves
  nothing. Seeds are MINSTD, so any failure reproduces.
- **External golden data.** `wiki-fixtures.test.ts` reads
  `wiki-tspin-forecast-boards.json` — 29 board diagrams parsed from harddrop.com. The boards
  *and* the expectations come from the wiki, never from this engine. There is one copy of that
  file and this test reads it; do not add a second.
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
| `bfs-cap.ts` | measures how far the BFS runs from its cap (max 688 over 2000 boards) |
| `pairs.ts` | winner-vs-loser pairing, shared by both AUC consumers |
| `run-forecast.ts`, `auc.ts`, `validate.ts` | the runners that produce the published figures |
| `auc-power.ts` | CIs, exact tests, power, and required sample size for those figures |

## Do not quote an AUC from here without `auc-power.ts`

`forecast rate`'s 61.4% rests on **11 decided pairs** — 95% CI [39%, 94%], 31% power against a
true 70% effect. It would need a 9-of-11 sweep to reach p < 0.05. Only `tucked T-spins`
(54 decided pairs, 90% power) supports a genuine negative result.

`auc-power.ts` self-checks its statistics against the defining equations before printing anything.
That check has already caught two real bugs: a Clopper–Pearson upper bound printing 0% because the
bisection assumed an increasing function, and a "textbook" constant recalled from memory that was
wrong in the fourth decimal. Neither was visible in the output.
