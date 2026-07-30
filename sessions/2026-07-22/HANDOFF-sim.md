# Handoff — TETR.IO replay simulator

Written 2026-07-30 at the end of a long session. Read this before touching the simulator.

## The one open question

**The simulator finds 7 perfect clears; the real games had 19.**

That is the sharpest unexplained fact and it is a *board* question, not a scoring one. Start here.
Everything else below is either settled or a dead end, and re-deriving any of it is wasted time.

## Status

Goal of the session — a T-Spin Forecast metric — is **done**: implemented, mutation-tested 5/5,
validated against external wiki fixtures, and answered (negative result, AUC 61.4%, no signal).
See `forecast-metric.md`. The simulator is a by-product that does not yet pass its gate:
**7/158 rounds survive, 1/158 exact on all fields.**

## Settled — do not re-investigate

| Thing | Status |
|---|---|
| Piece RNG | MINSTD `16807 % 2147483647`, Fisher-Yates **descending**, bag order **`ZLOSIJT`**. 158/158 |
| Frame clock | exactly 60 fps. `frames == finaltime_ms * 0.06`, 158/158. The client's own frame counter agrees |
| Incoming garbage content | `amt` / `x` (hole column) / `size` are in the `ige` payload. No RNG derivation |
| Outgoing attack timeline | recoverable from the **opponent's** ige stream. 156/158 vs `garbage.sent` |
| Attack table | **confirmed**: TSD 4, TST 6, quad 4, single 0, double 1, TSS 2; B2B +1/+1/+2; combo is a **multiplier** `floor(atk * (1 + 0.25*combo))` |
| Placement engine | **correct**. Three frame-accurate captures (346, 421, 458) match the real board cell-for-cell, including an empty board |
| Handling / IRS / IHS | correct as-is. `irs:"tap"` fires only on a fresh press — modelling held-key pre-rotation made results 3x worse |
| ARE / `lineclear_are` | real options, but modelling them as input-dropping is **wrong**; 0 is optimal, so TETR.IO buffers inputs across them |
| All-clear scoring | four variants swept, all within 5 points. Not the bug |
| Reverse engineering | **closed on all four routes**: `bootstrap.js` is a loader with zero game terms; the runtime bundle is a packed `blob:`; `app.asar` is an Electron shell + openpgp with **no game code**; community bot docs give option semantics but no defaults |

## Four diagnoses that were wrong

Recorded because each looked well-supported at the time:

1. "DAS/ARR is broken" — placement was always fine
2. "The attack table is wrong" — it was right
3. "A line-clear delay is the bug" — **retracted**, ARE refuted it (commit `791f567` still states this; fix it)
4. "The sim scores a phantom perfect clear" — reality got the PC too (verified at frame 458)

The common error: inferring board divergence from *attack* mismatches. Attack values depend on B2B
and combo chains, so one bad clear cascades — a mismatch says something broke *earlier*, not here.

## The method that works

Search over **time**, not over hypotheses. Six hypothesis sweeps (158 rounds each) found nothing;
three frame-accurate board comparisons found more.

1. **Bisect** with the opponent's ige stream — it timestamps every attack you send, giving a
   per-attack oracle. This already narrows divergences to **single pieces**.
2. **Capture ground truth from the TETR.IO client.** It is the only reference implementation.
   Drop the `.ttrm` in, open the round, press **Space** — the transport exposes a **frame counter**.
   Drag the playhead on the bar at `y≈742`; frame ≈ x ÷ 0.766. **Short drags do not register — use a
   long sweep.** Then zoom on the board and read it.
3. Compare against `cmp421.ts`, which prints the sim's board for any frame.

Literature: deterministic-lockstep desync debugging (per-tick checksums, per-subsystem hashing) and
ddmin (Zeller & Hildebrandt, IEEE TSE 2002).

## Traps

- **Look before you fit.** `lineclear_are`, `garbagespeed`, `garbagecap` are documented options.
  Several sweeps here fitted constants that were available as data.
- **`interaction` and `interaction_confirm` are distinct events.** Sum `interaction` only.
- **Never gate on a single field.** Gating on `lines` alone produced a false pass early on.
- **Apply the game's invariants to any synthesised board.** A mutation search returned boards with
  already-full rows — states the game cannot reach — which would have certified a mutant as equivalent.
- Formal proof cannot help: Dafny proves *claim ⇔ extracted data*. Whether the sim matches TETR.IO
  is empirical, and only the replay oracle can answer it.

## Where the code is

Session scratchpad (outside this repo): `sim.ts`, `forecast.ts`, `forecast.test.ts`,
`wiki-fixtures.test.ts`, `cmp421.ts`, `target.ts`, plus sweep scripts. `wiki-tspin-forecast-boards.json`
(29 external fixture boards) **is** committed here.

## Uncommitted / unpushed

- `791f567` is local only — **push it**, then retract its line-clear-delay conclusion
- Unrecorded: the ARE refutation, the reverse-engineering dead end, the all-clear sweep,
  and the frame-458 capture that disproved the phantom perfect clear
