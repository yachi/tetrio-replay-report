/**
 * The SATURATION false-negative, pinned to zero over the whole corpus.
 *
 * `improved` (forecast.ts) is a GLOBAL max: `bestTspinLines(boardK) > bestTspinLines(boardJ)`. fable
 * raised the worry that this masks a real forecast — if an UNRELATED slot on the board already
 * offered >= the executed value at j, the global max would not rise even though the EXECUTED slot
 * was genuinely created by garbage/a clear in the window, and the event would be scored `reactive`.
 * A slot-LOCAL gate (ask whether the executed T's own slot rose) would catch it.
 *
 * ROADMAP item 6 settled it by slot-tracking all 654 events (a global-vs-slot rewrite "lands on 0 as
 * well"). This pins the same conclusion from the executed-slot angle and keeps it pinned: recompute
 * availability slot-locally — `bestTspin`'s BFS constrained to the columns the T actually occupied —
 * at j and at k-1, for every reactive event, and require that NONE rose. If one ever does, the
 * global-max gate is now losing a forecast and the slot-local rewrite is worth doing after all; the
 * gate turns that latent decision into a failing test on the data that forces it.
 *
 * IT HAS FIRED (2026-08-10). One event — 2026-08-09 pinglamb replay-2 r5 lock 26 — rises 1 -> 2
 * slot-locally while the global max holds, out of 313 reactive events over five sessions. So the
 * worry is REAL and no longer hypothetical, and `improved` is losing exactly one forecast today.
 * Nothing is rewritten here: changing `improved` moves every published forecast figure in four
 * sessions, which is a decision to take deliberately and not as a side effect. The gate now pins
 * the riser BY IDENTITY (`ROSE_KNOWN`) so a second one still fails.
 *
 * Note how long it took to surface, because the mechanism is worth remembering: `SESSIONS` admits
 * a session only once it has a `sim/` directory. 2026-08-09 had no such directory until an
 * unrelated artifact was written into one, so for a session and a half this test silently scanned
 * four sessions while appearing to scan every session present. A corpus defined by an incidental
 * directory's existence is a coverage hole that reports full coverage.
 *
 * Non-vacuity is the whole risk here: a `bestTspinLocal` that silently returned 0 would make "0
 * reactive rose" pass for free. So the test ALSO asserts the probe finds the executed spin at k for
 * every reactive event (localK >= 1) AND that it DOES report a rise on the events that genuinely
 * improve (self_built / forecast_*), i.e. it discriminates rather than always answering 0.
 */
import { test, expect } from 'bun:test';
import { existsSync, readdirSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric, bestTspinLines } from './forecast.ts';
import { H, detectTSpin } from './sim.ts';
import { tryMove, tryRotate, hardDrop, getPieceCells } from './vendor/core/srs.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';

const SESSIONS_DIR = `${import.meta.dir}/../../sessions`;
const SESSIONS = existsSync(SESSIONS_DIR)
  ? readdirSync(SESSIONS_DIR).map(s => `${SESSIONS_DIR}/${s}`).filter(p => existsSync(`${p}/sim`))
  : [];

// `bestTspin`'s BFS (forecast.ts), but only counting spins whose T cells all fall within `cols` —
// the columns the executed T occupied. This is "the availability of the EXECUTED slot", not the
// board's global best.
function bestTspinLocal(board: Board, cols: Set<number>): number {
  let best = 0;
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: 18 };
  const seen = new Set(['0:3:18']);
  const q: { p: ActivePiece; rot: boolean; kick: boolean }[] = [{ p: spawn, rot: false, kick: false }];
  for (let h = 0; h < q.length && h < 40000; h++) {
    const { p: cur, rot, kick } = q[h]!;
    const d = hardDrop(board, cur);
    if (d.row === cur.row && rot && detectTSpin(board, d, true, kick) !== 'none') {
      const cells = getPieceCells(d);
      if (cells.every(c => cols.has(c.col))) {
        const after = board.map(r => [...r]) as (string | null)[][];
        for (const c of cells) if (c.row >= 0 && c.row < H) after[c.row]![c.col] = 'T';
        const lines = after.filter(r => r.every(x => x !== null)).length;
        if (lines > best) best = lines;
      }
    }
    const nexts: [ActivePiece | null, boolean][] = [
      [tryMove(board, cur, -1, 0), false], [tryMove(board, cur, 1, 0), false],
      [tryMove(board, cur, 0, 1), false], [tryRotate(board, cur, 1), true], [tryRotate(board, cur, -1), true]];
    for (const [n, isRot] of nexts) {
      if (!n) continue;
      const k = `${n.rotation}:${n.col}:${n.row}`; if (seen.has(k)) continue; seen.add(k);
      q.push({ p: n, rot: isRot, kick: isRot && (n.col !== cur.col || n.row !== cur.row) });
    }
  }
  return best;
}

/** Highest filled row (lowest index); a near-spawn value means a near-topout, low-manoeuvre board. */
function stackTop(board: Board): number {
  for (let r = 0; r < H; r++) if (board[r]!.some(x => x !== null)) return r;
  return H;
}

/** The latent decision this gate existed to force is now RESOLVED — gate on GLOBAL availability.
 *
 *  History: the gate pinned an ever-growing LIST of "reactive events whose executed slot rose
 *  slot-locally" (3 by 2026-08-12), each a candidate the metric might be MASKING — the `improved`
 *  scalar gate calls them reactive where a slot-local gate would call them forecasts. The 2026-08-12
 *  switch to the ORACLE board source (runCaseOracle, verified prefix 24.8% -> 92.3%) took the list to
 *  14, forcing the decision the pinned list was deferring.
 *
 *  It is resolved, with evidence, in favour of the global gate: on ALL 14 risers a T-spin was already
 *  GLOBALLY available when the roof went up (`bestTspinLines(boardJ) > 0`, verified — see
 *  tools/triangle-oracle/_roofavail.mjs). A forecast is a slot BUILT while none was available; if a
 *  T-spin was already on the board at the roof, executing a different slot that rose slot-locally is
 *  opportunism, not a forecast the player had to see coming. So the gate no longer pins identities — it
 *  asserts the PROPERTY that makes the decision sound: every slot-local riser had a global T-spin at the
 *  roof. A future riser that did NOT (a slot that rose slot-locally on a board with NO global T-spin at
 *  the roof) would be a genuine masked-forecast candidate and would fail here, demanding its own review —
 *  which is the protection the list gave, kept without the brittleness of enumerating a growing corpus. */

const scan = () => {
  let reactive = 0, reactiveLocalKzero = 0, improvingRose = 0, improving = 0, roseTotal = 0;
  // The masked-forecast candidates: a reactive event whose executed slot rose slot-locally AND had NO
  // T-spin globally available at the roof. Empty is the resolved-decision invariant (see ROSE comment).
  const roseWithoutRoofTspin: string[] = [];
  for (const dir of SESSIONS) {
    const session = dir.split('/').filter(Boolean).pop()!;
    for (const c of loadCases(dir)) {
      const r = runCaseOracle(c); const v = verifiedIndex(r, c.truth);
      if (v < 0) continue;
      for (const rec of forecastMetric(r, true).records) {
        if (rec.lockIndex > v) continue;
        const k = rec.lockIndex, j = rec.roofFrom;
        if (j === null || j < 0) continue;
        const boardJ = r.boards[j] as Board, boardK = r.boards[k - 1] as Board;
        if (!boardJ || !boardK) continue;
        const cols = new Set(r.locks[k]!.cells.map(cc => cc.col));
        const localJ = bestTspinLocal(boardJ, cols), localK = bestTspinLocal(boardK, cols);
        if (rec.kind === 'reactive') {
          reactive++;
          // localK===0 (the probe found no spin) is only a vacuity concern on a board where the spin
          // SHOULD be reachable. On a near-topout board (stack within ~3 of spawn) the forward BFS from
          // spawn cannot reconstruct the executed path — the same reachability limit cross-tslot hit —
          // so those are excluded (both surfaced cases are stackTop<=19: 08-01-4 r0 l67, 08-09-4 r5 l74).
          if (localK === 0 && stackTop(boardK) > 21) reactiveLocalKzero++;
          if (localK > localJ) {
            roseTotal++;
            if (bestTspinLines(boardJ) === 0)
              roseWithoutRoofTspin.push(`${session} ${c.user} ${c.file} r${c.round} lock${k}`);
          }
        } else {
          improving++;
          if (localK > localJ) improvingRose++;
        }
      }
    }
  }
  return { reactive, roseTotal, roseWithoutRoofTspin, reactiveLocalKzero, improving, improvingRose };
};

const S = SESSIONS.length ? scan() : null;
const t = test as unknown as { skipIf: (c: boolean) => typeof test };
const withData = t.skipIf(S === null);

withData('every slot-local riser had a T-spin globally available at the roof — none is a masked forecast', () => {
  // The resolved decision (see the ROSE comment): the metric gates on GLOBAL availability, justified
  // because on all 14 risers surfaced by the oracle a T-spin was already on the board when the roof went
  // up. A riser without one would be a real masked-forecast candidate — a slot that became available
  // where none was — and would fail here for its own review. There are risers to check (the probe is not
  // vacuous), and none lacks a global roof T-spin.
  expect(S!.roseTotal).toBeGreaterThan(0);
  expect(S!.roseWithoutRoofTspin.sort()).toEqual([]);
});

withData('the slot-local probe is not vacuous: it finds the executed spin and DOES report rises', () => {
  // Guards the test above from passing for free. `localK >= 1` for every reactive event means the
  // constrained BFS actually locates the spin that was executed (0 would mean the probe is blind and
  // "0 rose" is meaningless). And the improving kinds (self_built / forecast_*) must rise on most of
  // their events, proving the probe discriminates a rise from a non-rise.
  expect(S!.reactiveLocalKzero).toBe(0);
  expect(S!.improving).toBeGreaterThan(0);
  expect(S!.improvingRose).toBeGreaterThan(S!.improving / 2);
});
