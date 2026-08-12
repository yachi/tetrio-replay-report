# Oracle-as-board-source — the drift-0 reframe

## Problem reframe (L9)

**Given problem:** "fix sim drift 0" — make the hand-ported `pipeline/sim/sim.ts` reproduce the
real game exactly.

**Reframed:** the sim only exists to produce the *verified-prefix boards* that feed the
quarantined forecast/opener sections. Five mechanic leads (spawn, DAS/ARR, gravity ramp,
anti-stall, lock-reset) were falsified this session — each gains 0 off sim-gap 24.8%. The
residual is a diffuse tail of rare placement divergences, not one portable mechanic, so the
port asymptotes below 100%. But **the Triangle oracle (@haelp/teto) IS the reference engine and
matches the real game 100% on attack.** So don't perfect the port — *use Triangle's code as the
board source*. That is literally "drift 0, according to triangle code."

## Empirical proof (Phase 2.5 — done, `tools/triangle-oracle/_oracleproof2.mjs`)

Oracle-derived records `{frame, sent, lines, clearedRows}` run through the SAME `verifiedIndex`,
on the STRICTER `frame+amount+row` gate:

| session | oracle (row gate) | full-round |
|---|---|---|
| 07-22 | 88.6% | 140/158 |
| 07-24 | 94.4% | 93/100 |
| 07-28 | 94.5% | 114/128 |
| 08-01 | 92.4% | 94/106 |
| 08-09 | 93.4% | 87/100 |
| **corpus** | **7700/8342 = 92.3%** | **528/592 = 89.2%** |

vs the sim: **24.8%** on the *weaker* frame+amount gate, 12.7% exhaustive. The remaining 7.7% is
the `matchesIgeY` heuristic's own documented residuals (+4/+5/+6), not board drift.

## Design

Add `runCaseOracle(c): SimResult` — a Triangle-backed adapter producing the exact `SimResult`
shape, then swap `verified-prefix.ts`'s `runCase` to use it (keep the sim behind a flag for the
differential probes). Consumers (forecast-corpus, cross-tslot, openers) are unchanged — they read
`r.boards`, `r.locks`, `r.records` transparently.

Adapter extraction from Triangle (per `#lock` res + `falling.lock.pre`):
- `records[]`: `{frame: eng.frame, sent: sum(res.garbage), lines: res.lines, spin, cells,
  clearedRows}` — clearedRows from (pre-tick board snapshot + piece cells) → full rows → y-down.
- `locks[]`: `{frame, piece: res.mino, cells (y-down), cleared: res.lines, spin: map(res.spin),
  allclear}`.
- `boards[]`: `eng.board.state` after each lock, y-up→y-down 40-row, `gb`→'G', mino→letter.
- garbage hole injection: reuse `oracle.mjs`'s recorded-`x` machinery (Triangle re-rolls holes).

Coordinate contract: y-down row = 39 − y_up (board 40, visible 20). Cells `{col:x, row:39−y_up}`.
Spin map: Triangle `'none'|'normal'|'mini'` → sim `'none'|'full'|'mini'`.

## Validation gates before re-blessing

1. Oracle adapter boards MUST equal the sim's boards bit-for-bit through the deterministic prefix
   (where both are already validated — 28/28 locks on 07-22 r0). A mismatch there is an adapter
   coordinate bug, not a drift win.
2. Then re-bless: cross-tslot total, forecast-corpus buckets/floors, openers clean/sbTriple,
   forecast-saturation, opener-facts.json byte-repro. Each re-bless is a decision, recorded.
3. `facts.json` stays byte-untouched (dual-extractor invariant; sim/oracle feed only quarantined
   sections).

## Invariant shift (state honestly in the report/README)

The quarantined sections move from "one hand-written simulator" to "the reference engine itself."
That is a STRONGER single source (matches real 100%), but it is still ONE source — the quarantine
(no claim ids, no ✓ badges, nothing merged to facts.json) stays exactly as-is.
