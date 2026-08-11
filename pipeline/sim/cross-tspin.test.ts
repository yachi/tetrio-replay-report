/**
 * T-SPIN CLASSIFICATION differential: our `sim.ts` `detectTSpin` vs the ORIGINAL cold-clear's
 * `rotate()` T-spin rule (ported in `cc-tspin.ts`). An EXACT gate on the none-vs-spin boundary, plus
 * a LEDGER of the ONE place the two rules diverge by design.
 *
 * WHY THIS EXISTS. `detectTSpin` (`sim.ts:93`) labels every T lock none/mini/full; that label feeds
 * `clears.*`, the fitted attack table and the forecast admission test, and it had one implementation
 * and no outside check. `cc-tspin.ts` is a second method transcribed from cold-clear's Rust. This
 * drives both rules over T placements reached BY ROTATION and pins:
 *
 *  - GATE, exact: the NONE-vs-SPIN boundary is the SAME function. Both use the identical four
 *    diagonal corners of the T centre and the same `total >= 3` gate; our detectTSpin's front
 *    corners are cold-clear's `mini_tspin_corners` for every orientation. A disagreement here is a
 *    real bug in the gate or the coordinate conversion. Measured: 0.
 *  - LEDGER, not a gate: mini-vs-full. Ours upgrades mini→full on ANY kick; cold-clear only on the
 *    LAST kick (index 4). So every disagreement is exactly `ours=full ∧ cc=mini ∧ i ∈ {1,2,3}`, and
 *    the reverse (`ours=mini ∧ cc=full`) is impossible — cold-clear-full needs `mini==2` or `i==4`,
 *    and both make ours full too. TETR.IO replays, not cold-clear, are ground truth for which rule
 *    is right (engine-verification-plan risk R5), so this MEASURES the divergence, it does not fail
 *    on it. The confusion matrix and counts are pinned byte-stable for the fixed seeded corpus.
 *
 * KICK INDEX. cold-clear sets `tspin` during `rotate()`, keyed on which of its 5 kick candidates it
 * used. Our `tryRotate` returns only the piece, but the candidate is recoverable as the first entry
 * of `ccKicks` (== `JLSZT_KICKS` for T, gated by `cross-srs-tables.test.ts`) matching the observed
 * displacement — sound because a duplicate-displacement earlier candidate would have been the one
 * `tryRotate` returned. `ccKickIndex` does this; `i >= 1` is our engine's own `usedKick`.
 *
 * ANTI-VACUITY. A differential that finds no spins agrees vacuously (the `cc-tslot.ts` house rule),
 * so the spin count, the presence of the last-kick branch (i==4), and a non-empty ledger are pinned.
 */
import { test, expect, describe } from 'bun:test';
import { existsSync } from 'node:fs';
import { emptyBoard, H, detectTSpin } from './sim.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';
import { tryMove, tryRotate, isValidPosition, setKickset } from './vendor/core/srs.ts';
import type { PieceType } from './vendor/core/types.ts';
import { occ, ccTspin, ccKickIndex } from './cc-tspin.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

const W = 10;
type Rot = 0 | 1 | 2 | 3;

/**
 * T placements reached BY ROTATION: a 0G-complete BFS over the SRS primitives (the shape
 * `forecast.ts` bestTspin walks), collecting every state whose last action was a rotation that then
 * rests in place, carrying the kick index its rotation used. Deduped on (resting state, i) — the
 * same placement reached with a different kick index is a distinct classification case, because
 * cold-clear's verdict depends on i.
 */
function spinCandidates(board: Board): { piece: ActivePiece; i: number }[] {
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: 18 };
  if (!isValidPosition(board, spawn)) return [];
  const out: { piece: ActivePiece; i: number }[] = [];
  const seen = new Set<string>(), dedup = new Set<string>();
  const key = (p: ActivePiece) => `${p.rotation}:${p.col}:${p.row}`;
  const q: ActivePiece[] = [spawn];
  seen.add(key(spawn));
  for (let h = 0; h < q.length; h++) {
    const cur = q[h]!;
    for (const dir of [1, -1] as const) {
      const post = tryRotate(board, cur, dir);
      if (!post) continue;
      if (tryMove(board, post, 0, 1) !== null) continue;   // still falls -> not resting here
      const i = ccKickIndex('T', cur.rotation as Rot, post.rotation as Rot, post.col - cur.col, post.row - cur.row);
      const dk = `${key(post)}:${i}`;
      if (!dedup.has(dk)) { dedup.add(dk); out.push({ piece: post, i }); }
    }
    for (const n of [tryMove(board, cur, -1, 0), tryMove(board, cur, 1, 0), tryMove(board, cur, 0, 1),
                     tryRotate(board, cur, 1), tryRotate(board, cur, -1)]) {
      if (n && !seen.has(key(n))) { seen.add(key(n)); q.push(n); }
    }
  }
  return out;
}

function randomBoards(seed: number, n: number, maxH: number): Board[] {
  let t = seed % 2147483647; if (t <= 0) t += 2147483646;
  const rnd = () => (t = (16807 * t) % 2147483647) / 2147483647;
  const boards: Board[] = [];
  for (let i = 0; i < n; i++) {
    const b = emptyBoard().map(r => [...r]) as (PieceType | null)[][];
    for (let c = 0; c < W; c++) {
      const hh = Math.floor(rnd() * (maxH + 1));
      for (let k = 0; k < hh; k++) { const row = H - 1 - k; if (rnd() < 0.78) b[row]![c] = 'I'; }
    }
    boards.push(b as Board);
  }
  return boards;
}

interface Stats {
  total: number; spins: number; noneVsSpin: number;
  confusion: Record<string, number>; iDist: Record<number, number>;
  ledger: number; unexplained: number; reverse: number; fullFull: number; examples: string[];
}
function runCorpus(boards: Board[]): Stats {
  setKickset('SRS');
  const s: Stats = { total: 0, spins: 0, noneVsSpin: 0, confusion: {}, iDist: {}, ledger: 0, unexplained: 0, reverse: 0, fullFull: 0, examples: [] };
  for (const b of boards) {
    for (const { piece, i } of spinCandidates(b)) {
      s.total++;
      s.iDist[i] = (s.iDist[i] ?? 0) + 1;
      const ours = detectTSpin(b, piece, true, i >= 1);
      const cc = ccTspin(b, piece, i);
      s.confusion[`${ours}/${cc}`] = (s.confusion[`${ours}/${cc}`] ?? 0) + 1;
      const oS = ours !== 'none', cS = cc !== 'none';
      if (oS !== cS) s.noneVsSpin++;
      if (oS) s.spins++;
      if (ours === 'full' && cc === 'full') s.fullFull++;
      if (oS && cS && ours !== cc) {
        if (ours === 'full' && cc === 'mini') {
          s.ledger++;
          if (!(i >= 1 && i <= 3) && s.examples.length < 5)
            (s.unexplained++, s.examples.push(`UNEXPLAINED ours=full cc=mini i=${i} rot=${piece.rotation} col=${piece.col} row=${piece.row}`));
          else if (!(i >= 1 && i <= 3)) s.unexplained++;
        } else if (ours === 'mini' && cc === 'full') {
          s.reverse++;
          if (s.examples.length < 5) s.examples.push(`REVERSE ours=mini cc=full i=${i} rot=${piece.rotation} col=${piece.col} row=${piece.row}`);
        }
      }
    }
  }
  return s;
}

// ── L1: the coordinate conversion, unit-tested FIRST (risk R1) ───────────────────────────────────
describe('cc-tspin occupancy conversion', () => {
  test('occ: walls and floor occupied, sky empty, a placed cell reads occupied', () => {
    const b = emptyBoard().map(r => [...r]) as (PieceType | null)[][];
    b[39]![4] = 'T';
    expect(occ(b as Board, -1, 20)).toBe(true);   // left wall
    expect(occ(b as Board, 10, 20)).toBe(true);   // right wall
    expect(occ(b as Board, 5, H)).toBe(true);     // floor (below the 40-row board)
    expect(occ(b as Board, 5, -1)).toBe(false);   // sky (above the board)
    expect(occ(b as Board, 4, 39)).toBe(true);    // the placed cell — POSITIVE detection
    expect(occ(b as Board, 5, 39)).toBe(false);   // empty neighbour
  });
});

// ── the differential over the seeded overhang corpus (deterministic, pinned) ─────────────────────
describe('detectTSpin vs cold-clear rotate() over seeded overhang boards', () => {
  const CORPUS = [...randomBoards(12345, 1500, 12), ...randomBoards(67890, 1500, 18), ...randomBoards(999, 1000, 8)];
  const s = runCorpus(CORPUS);

  test('GATE: none-vs-spin agrees EXACTLY (0 disagreements; no cross-terms in the confusion matrix)', () => {
    expect(s.noneVsSpin, `none-vs-spin boundary disagreed — a real bug in the 3-corner gate or the conversion.\nconfusion=${JSON.stringify(s.confusion)}`).toBe(0);
    // ours=mini ∧ cc=full is proven impossible; its presence would be a real finding.
    expect(s.reverse, s.examples.join('\n')).toBe(0);
    expect(Object.keys(s.confusion).sort()).toEqual(['full/full', 'full/mini', 'mini/mini', 'none/none']);
  });

  test('LEDGER: every mini/full disagreement is explained by ours-any-kick vs cc-last-kick (i in 1..3)', () => {
    expect(s.unexplained, s.examples.join('\n')).toBe(0);
  });

  test('LEDGER is byte-stable (pinned counts for this fixed corpus)', () => {
    // A diff here means the rule or the generator changed — re-measure and re-pin deliberately,
    // never to make the test pass. These are this differential's own deterministic output over a
    // seeded corpus (a regression snapshot), not golden data from an external oracle.
    expect({
      total: s.total, spins: s.spins, ledger: s.ledger, fullFull: s.fullFull,
      i0: s.iDist[0], i1: s.iDist[1], i2: s.iDist[2], i3: s.iDist[3], i4: s.iDist[4],
      confusion: s.confusion,
    }).toEqual(LEDGER);
  });

  test('ANTI-VACUITY: many spins produced, the last-kick branch exercised, ledger non-empty', () => {
    expect(s.spins).toBeGreaterThan(1000);
    expect(s.iDist[4]).toBeGreaterThan(0);
    expect(s.ledger).toBeGreaterThan(0);
    expect(s.fullFull).toBeGreaterThan(0);
  });
});

// ── the two invariants also hold on REAL game boards (verified-prefix corpus, guarded) ───────────
// Session list explicit, not globbed (memory: sim-test-corpus-silently-under-covers).
const SIM_SESSIONS = ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09']
  .map(d => `${import.meta.dir}/../../sessions/${d}`).filter(existsSync);

describe.skipIf(SIM_SESSIONS.length === 0)('detectTSpin vs cold-clear rotate() over real verified-prefix boards', () => {
  test('every verified-prefix board of all sessions: none-vs-spin exact, ledger fully explained', () => {
    setKickset('SRS');
    const boards: Board[] = [];
    for (const session of SIM_SESSIONS) {
      process.env.REPLAY_DIR = session;
      let n = 0;
      for (const c of loadCases(session)) {
        const r = runCase(c, {});
        const v = verifiedIndex(r, c.truth);
        for (let step = 0; step <= v; step++) { boards.push(r.boards[step]!); n++; }
      }
      expect(n, `${session.split('/').pop()} contributed 0 verified-prefix boards`).toBeGreaterThan(0);
    }
    const s = runCorpus(boards);
    expect(s.noneVsSpin, `confusion=${JSON.stringify(s.confusion)}`).toBe(0);
    expect(s.reverse, s.examples.join('\n')).toBe(0);
    expect(s.unexplained, s.examples.join('\n')).toBe(0);
    expect(s.spins).toBeGreaterThan(0);
  }, 300_000);
});

// Pinned ledger for the seeded corpus above (re-measure deliberately if the rule/generator changes).
const LEDGER = {
  total: 208751, spins: 10549, ledger: 5949, fullFull: 2524,
  i0: 130019, i1: 52699, i2: 9687, i3: 10422, i4: 5924,
  confusion: { 'none/none': 198202, 'full/mini': 5949, 'full/full': 2524, 'mini/mini': 2076 } as Record<string, number>,
};
