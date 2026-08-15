# triangle-oracle — headless TETR.IO board oracle (validation tool)

An **isolated** validation tool for the simulator-drift work. It replays a `.ttrm` round through
[Triangle.js](https://github.com/Genius6942/triangle) (`@haelp/teto`, MIT) — the community's clean-room
reimplementation of the TETR.IO engine — to produce a per-frame ground-truth board, then diffs the
project's own `pipeline/sim` against it.

**Isolation is deliberate.** `@haelp/teto` pulls ~161 packages; they live only in this directory's own
`node_modules` and never touch the main project's deps, lockfile, or CI. The main pipeline is unchanged.

```bash
cd tools/triangle-oracle
bun install
bun driftmap.mjs      # sim vs oracle across all sessions, one table
```

## Why this exists

The `.ttrm` records inputs + the ige stream but **no board snapshots**, so the sim's garbage model had no
independent board to check against. Two other oracles were tried first: Cold Clear (a placement bot — no
clock, can't model garbage timing) and pixel-capturing the live TETR.IO client (works, but manual,
browser-bound, and anti-tamper-adjacent). Triangle is the headless, deterministic, batchable answer.

## How it's calibrated (see `oracle.mjs`)

Triangle is faithful out of the box for movement/gravity/lock/line-clear, but two things must be fixed to
match these specific replays:

1. **Gravity** — the version-19 `.ttrm` `options` omits `g`; force a sane value (hard-drops make the exact
   value irrelevant, but a missing one desyncs).
2. **Garbage hole column** — Triangle re-rolls holes from its own seeded RNG and ignores the ige-recorded
   column. The replay records the true hole as `x` on each garbage `interaction` event, keyed by batch
   `iid`. We pair holes to Triangle's OWN `garbage.tank` events (which fire per batch that actually
   inserts, carrying the `iid`) and look the recorded `x` up by `iid`. A blind oldest-first FIFO over
   every recorded line does NOT work: most recorded garbage is CANCELLED before it inserts — the loads
   sum to far more lines than a 20-high board holds — so a positional FIFO desyncs at the first cancel
   and hands every later insertion an earlier, cancelled batch's hole. Keying by `iid` off the tank
   events excludes cancelled batches structurally.

With these, the oracle is **bit-exact vs the sim through the deterministic + main garbage phase**
(28/28 locks to frame 1371 on 2026-07-22 r0 yachi) and, where checked against a live capture, **more
faithful than the sim** in the topout flood (77.5% vs 59.5% at frame 1422 — the sim over-inserts endgame
garbage).

## Reading the drift map — caveats

`driftmap.mjs` prints per-session `%exact` (bit-exact locks, sim vs oracle) and lists cases that diverge
before the final 20% of the round. It is a **disagreement map, not a certified sim-bug list**:

- Corpus-wide `%exact` ≈ 63.3% (was 39.5% before the `hoisted`-DAS and iid hole-pairing fixes), and
  95.3% over the verified prefix alone — the whole-round figure is dragged down by the topout flood past
  the prefix.
- Options are identical across files, so early divergences are **not** a per-game ruleset mismatch; they
  are genuine sim-vs-oracle *model* differences (movement/handling edge cases). Which engine is right at
  any given divergence needs a **live spot-check** for that round.
- Holes (column AND cancellation-correct pairing) and gravity are pinned, so board *occupancy* is sound;
  `garbagespeed`/`garbagecap` are still best-effort, so garbage *timing* — how many lines stand by a given
  frame — is the dominant residual and the last thing needing live calibration.

To make this a certified drift oracle rather than a disagreement map: pin `garbagespeed`/cap and validate a
sample of the early-divergence cases against fresh live captures.

## What it has already found

The disagreement map is not just a number — following it to a root cause found a real sim bug.

```bash
bun scan-lock0.mjs     # how often the OPENING piece diverges sim-vs-oracle (was 25%)
bun scan-hoisted.mjs   # correlate those divergences with the replay's `hoisted` DAS flag
bun diag.mjs <file> <round> <user> [n]   # dump sim vs oracle boards at the first n divergent locks
```

`scan-lock0` showed 148/592 openers (25%) diverged; `scan-hoisted` showed 146 of them carried a
`hoisted: true` opening move-key. `.ttrm` keydowns set that flag when the client recorded the direction
as ALREADY held when the piece spawned — DAS is pre-charged, so the piece slams to the wall. The sim
dropped the flag and treated it as a fresh tap, stopping one cell short. Honoring it cut opening
divergences 148 -> 3 and lifted corpus bit-exact 39.5% -> 49.6%. The ground truth was the client's own
recorded flag; no live capture was needed. (See `pipeline/sim/hoisted-das.test.ts`.)

```bash
bun scan-firstdiv.mjs   # classify the NEXT divergence class after openings (it's garbage-timing)
bun cross-extract.mjs   # how much of each quarantined section two engines agree on (dual-backed)
```

`scan-firstdiv` showed the remaining divergences are dominated by garbage-insertion TIMING, not
placement — no second `hoisted` to find. `cross-extract` then measured Triangle as a SECOND EXTRACTOR:
over the verified prefix, sim and Triangle agree bit-exact on **96.2%** of locks, backing **96.2%** of
forecast events and **94.8%** of opener rounds with an independent engine — the dual-implementation
evidence the quarantined sections are missing. Building that check exposed the oracle's own hole-pairing
bug (the FIFO-vs-iid issue fixed above): before it, the one surviving forecast (`forecast_lineclear`)
was flagged non-dual purely because the oracle mis-paired a garbage hole. The sim matched ground truth
throughout — the bug was the oracle's.

**That event is no longer dual-backed, and the regression is the point.** Under the reference-engine
board source, 2026-07-28's `forecast_lineclear` reads **0/1** where the hole-pairing fix had made it
1/1; the corpus's other one, 2026-08-14's, reads 1/1. Nothing about the hole-pairing fix changed — the
board underneath it did. A figure quoted for a *named single event* is the most fragile kind there is,
because the event survives the change and only its verdict moves.

## The dual-backed manifest — checkable two-engine confirmation

`cross-extract.mjs` emits `dual-backed.json`, a committed, byte-stable record of how much of each
quarantined section two independent engines agree on:

```bash
bun cross-extract.mjs                             # print the coverage table
bun cross-extract.mjs --out ./dual-backed.json    # (re)write the manifest
bun cross-extract.mjs --check                     # reproducibility gate: fail if the committed file is stale
```

It is a **tools** artifact, deliberately: computing it needs @haelp/teto (161 pkgs), so the main CI does
not rebuild it and its `--check` gate lives here, not in `pipeline/`. Counts are stored as integers so the
JSON is byte-stable; percentages are derived at read time. The manifest is engine AGREEMENT, **not** a
Dafny proof — it carries no claim id and no ✓ badge, and never merges into `facts.json`. It is the data
layer for a possible `✓ two-engine` marker in the forecast/opener sections; wiring that into the published
report is a separate decision, because the report is pipeline-built (no oracle) and every report artifact
is held to CI-reproducibility, which a manifest needing the oracle cannot meet.

### A gate nobody runs is a gate that fails silently — this one had, for three deltas

The `--check` above is real and it works: run today against the manifest as committed, it exited 1.
It had been exiting 1 for a long time, and because it is manual-only *by design*, nothing noticed.
Three separate staleness deltas had stacked up behind it, and the prose above quoted the oldest:

| # | cause | locks bit-exact |
|---|---|---|
| 0 | figures as first written (`08ed03c`) — correct at the time | 95.3% |
| 1 | `842f7c0` regenerated the manifest after the exact-attack default; prose not updated | → 94.9% |
| 2 | the reference-engine board source landed; manifest **never** regenerated | → 95.9% |
| 3 | the sixth session (2026-08-14) added | → 96.2% |

Only delta 3 is the one a "new session" checklist would catch. Delta 1 is prose left behind by a
regeneration, delta 2 is an artefact left behind by a *source* change — and delta 2 is the large one.

**The manifest's own structure is what proves delta 2 is source drift and not the new session.**
`cross-extract.mjs` builds a fresh `S` per session directory; nothing crosses sessions except the
global total. So adding 2026-08-14 *cannot* change the other five blocks — and all five changed
(2026-07-22's `prefix_locks` 3620 → 4443). That argument needs no git archaeology, only the loop.

Two consequences for anyone regenerating this file:

- **Re-derive the prose in the same commit as the artefact.** Every figure in the paragraphs above is
  a percentage the JSON does not store (counts are stored precisely so the file stays byte-stable),
  so nothing mechanically ties prose to manifest. `--check` gates the JSON and gates nothing else.
- **Run `--check` after anything touching `pipeline/sim/verified-prefix.ts`, `pipeline/sim/forecast.ts`
  or `oracle.mjs`** — the three modules `cross-extract.mjs` imports. A change to any of them
  invalidates this manifest without touching a single file under `tools/`.
