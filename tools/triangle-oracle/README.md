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
   column. The replay records the true hole as `x` on each garbage `interaction` event, so we inject it
   onto the board once per insertion (garbage inserts only on non-clearing locks).

With these, the oracle is **bit-exact vs the sim through the deterministic + main garbage phase**
(28/28 locks to frame 1371 on 2026-07-22 r0 yachi) and, where checked against a live capture, **more
faithful than the sim** in the topout flood (77.5% vs 59.5% at frame 1422 — the sim over-inserts endgame
garbage).

## Reading the drift map — caveats

`driftmap.mjs` prints per-session `%exact` (bit-exact locks, sim vs oracle) and lists cases that diverge
before the final 20% of the round. It is a **disagreement map, not a certified sim-bug list**:

- Corpus-wide `%exact` ≈ 39.5%, close to the sim's own ~34% verified-prefix vs the real ige — consistent
  with the oracle tracking reality about as well as the real oracle, headlessly.
- Options are identical across files, so early divergences are **not** a per-game ruleset mismatch; they
  are genuine sim-vs-oracle *model* differences (movement/handling edge cases). Which engine is right at
  any given divergence needs a **live spot-check** for that round.
- Holes and gravity are pinned, so board *occupancy* is sound; `garbagespeed`/`garbagecap` are still
  best-effort, so garbage *timing* attribution is soft.

To make this a certified drift oracle rather than a disagreement map: pin `garbagespeed`/cap and validate a
sample of the early-divergence cases against fresh live captures.
