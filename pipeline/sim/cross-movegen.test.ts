/**
 * MOVEGEN differential: our engine's reachable resting-placement set vs the ORIGINAL cold-clear's
 * `libtetris::find_moves`, over every piece.
 *
 * WHY THIS EXISTS. `forecast.ts` `bestTspin` is a 0G-complete BFS over the SRS primitives
 * (`tryMove`/`tryRotate`/`hardDrop`/`isValidPosition`), and every published forecast/opener figure
 * rests on it. Until now its reachable set had exactly one authority — a second copy of the same
 * BFS. The arrival-key defect (fixed `0b0aaf6`, `spec/BfsKey.dfy`) was a reachability bug this class
 * of check exists to catch: a placement that is really reachable but the search missed it. This
 * differentials the SET itself against cold-clear's mover, arrived at independently (a heap-ordered
 * finesse search vs our breadth BFS). Because `bestTspin` only ever walks a T, the other six pieces
 * are exercised here for the first time — this is also what finally covers the non-T kick slices of
 * `JLSZT_KICKS`/`I_KICKS` behaviorally (a transposed kick entry diverges the reachable set).
 *
 * THE ORACLE is the real Rust binary at `$CC_ORACLE` (built `nix build .#cc-oracle`) run with
 * `CC_ORACLE_MOVES=1`; see `nix/cold-clear-oracle/cc-oracle.rs`. It answers with
 * `MovementMode::ZeroGComplete`; skipped when the binary is absent, exactly like
 * `cross-tslot-count.ts` needs its oracle path.
 *
 * THE INVARIANT IS SUBSET, NOT EQUALITY — and which direction is load-bearing is the whole point.
 * cold-clear's mover (`libtetris::find_moves`) only shifts the piece horizontally at REST heights:
 * it has no "down one cell", only `SonicDrop`, so it reaches a tuck by drop→shift→drop. Our BFS
 * moves down one cell at a time and may shift sideways at ANY height, which is the faithful model of
 * 0G reachability in a real game (soft drop + free horizontal movement). So our set is a strict
 * SUPERSET: `find_moves` misses mid-height tucks under overhangs that a player can actually reach.
 * That direction (`ours \ cc`) is EXPECTED and carries no information — the same asymmetry
 * `cross-tslot.ts` records for the named-shape detectors. The INFORMATIVE direction is the reverse:
 * a placement cold-clear reaches that our BFS does NOT (`cc \ ours`) is a reachability FALSE
 * NEGATIVE — precisely the arrival-key bug class (`spec/BfsKey.dfy`) this gate exists to catch. So
 * the gate is `cc ⊆ ours`; `ours \ cc` is measured and reported, never failed.
 *
 * SPAWN CONVENTION (risk R3). We spawn at bounding-box col 3, row 18; cold-clear spawns at its own
 * x=4,y=19(/20). On boards whose stack reaches the spawn area the two spawn cell-sets differ and the
 * subset could break for a reason that is NOT an engine bug. So the random corpus caps column
 * heights at 18 (top filled row >= 22, spawn rows 18-21 always clear) while still exceeding
 * cold-clear's height-16 fast-path threshold, so the non-fast mover is exercised.
 *
 * ANTI-VACUITY. A mover that reaches nothing agrees with everything (the `cc-tslot.ts` house rule);
 * `cc ⊆ ours` is satisfied vacuously when cc is empty. So the test pins that the cold-clear side is
 * large (many placements had to be re-reached) AND that `ours \ cc` is non-empty (the overhang
 * corpus really does exercise the mid-height tucks the subset direction is about).
 */
import { test, expect, describe } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { emptyBoard, H } from './sim.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';
import { tryMove, tryRotate, hardDrop, getPieceCells, isValidPosition, setKickset } from './vendor/core/srs.ts';
import type { PieceType } from './vendor/core/types.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

const W = 10;
const PIECES: PieceType[] = ['I', 'T', 'O', 'S', 'Z', 'L', 'J'];
// Resolved from THIS file, never an absolute path into one checkout. The default was
// `/Users/yachi/github/tetrio-replay-report/result/bin/cc-oracle`, so in a worktree the BFS was
// differentialled against a binary built from a different tree — measured: with CC_ORACLE unset
// this file did not skip, it ran and passed through that other checkout's `result` symlink.
// Same class as `analysis/rate_records.R`'s absolute `repo`, which silently measured the other
// tree's sessions. Both symlinks happened to resolve to the same nix store path, so it was
// latent rather than wrong today.
//
// Still a SKIP and not a failure when the binary is absent: the `typescript` job runs the whole
// suite with no CC_ORACLE and no nix, so a hard failure here would turn that job red for a
// dependency it is not meant to have. `oracle-image` sets CC_ORACLE explicitly and is unchanged.
const ORACLE = process.env.CC_ORACLE ?? `${import.meta.dir}/../../result/bin/cc-oracle`;
const HAVE_ORACLE = existsSync(ORACLE);

// Canonical key for a placement = its four occupied [col,row] cells, sorted (row, col).
function keyOfCells(cells: { col: number; row: number }[]): string {
  return cells.map(c => [c.col, c.row] as [number, number])
    .sort((a, b) => a[1] - b[1] || a[0] - b[0]).map(c => `${c[0]},${c[1]}`).join('|');
}
function keyOfPairs(pairs: [number, number][]): string {
  return pairs.slice().sort((a, b) => a[1] - b[1] || a[0] - b[0]).map(c => `${c[0]},${c[1]}`).join('|');
}

/** Our reachable resting placements via a 0G-complete BFS over the engine primitives. */
export function ourReachable(board: Board, type: PieceType): Set<string> {
  setKickset('SRS');
  const spawn: ActivePiece = { type, rotation: 0, col: 3, row: 18 };
  const out = new Set<string>();
  if (!isValidPosition(board, spawn)) return out;
  const seen = new Set<string>();
  const key = (p: ActivePiece) => `${p.rotation}:${p.col}:${p.row}`;
  const q: ActivePiece[] = [spawn];
  seen.add(key(spawn));
  for (let h = 0; h < q.length; h++) {
    const cur = q[h]!;
    out.add(keyOfCells(getPieceCells(hardDrop(board, cur))));
    for (const n of [tryMove(board, cur, -1, 0), tryMove(board, cur, 1, 0), tryMove(board, cur, 0, 1),
                     tryRotate(board, cur, 1), tryRotate(board, cur, -1)]) {
      if (n && !seen.has(key(n))) { seen.add(key(n)); q.push(n); }
    }
  }
  return out;
}

const boardToRows = (b: Board) => b.map(r => r.map(x => (x === null ? '.' : 'X')).join('')).join('\n');

/** Batch every (board,piece) case through ONE oracle invocation; returns the parsed sets in order. */
function ccReachableBatch(cases: { board: Board; type: PieceType }[]): Set<string>[] {
  const input = cases.map(c => c.type + '\n' + boardToRows(c.board)).join('\n') + '\n';
  const res = spawnSync(ORACLE, { input, encoding: 'utf8', env: { ...process.env, CC_ORACLE_MOVES: '1' }, maxBuffer: 1 << 28 });
  if (res.status !== 0) throw new Error('cc-oracle failed: ' + res.stderr);
  const lines = res.stdout.split('\n').filter(l => l.trim());
  if (lines.length !== cases.length) throw new Error(`oracle returned ${lines.length} lines for ${cases.length} cases`);
  return lines.map(l => {
    const o = JSON.parse(l) as { placements: [number, number][][] };
    return new Set(o.placements.map(keyOfPairs));
  });
}

// Seeded MINSTD board generator (reproducible failures), heights capped so both spawns stay clear.
function randomBoards(seed: number, n: number, maxH: number): Board[] {
  let t = seed % 2147483647; if (t <= 0) t += 2147483646;
  const rnd = () => (t = (16807 * t) % 2147483647) / 2147483647;
  const boards: Board[] = [];
  for (let i = 0; i < n; i++) {
    const b = emptyBoard().map(r => [...r]) as (PieceType | null)[][];
    for (let c = 0; c < W; c++) {
      const h = Math.floor(rnd() * (maxH + 1));           // column height 0..maxH
      for (let k = 0; k < h; k++) {
        const row = H - 1 - k;
        if (rnd() < 0.78) b[row]![c] = 'I';                 // ~22% holes -> overhangs, tuck/spin tests
      }
    }
    boards.push(b as Board);
  }
  return boards;
}

function compareAll(cases: { board: Board; type: PieceType }[]) {
  const cc = ccReachableBatch(cases);
  let ccTotal = 0, oursOnlyTotal = 0, ccOnlyTotal = 0, ccOnlyCases = 0;
  const examples: string[] = [];
  for (let i = 0; i < cases.length; i++) {
    const ours = ourReachable(cases[i]!.board, cases[i]!.type);
    const theirs = cc[i]!;
    ccTotal += theirs.size;
    const ccOnly = [...theirs].filter(x => !ours.has(x));   // the false-negative direction (gated)
    const oursOnly = [...ours].filter(x => !theirs.has(x)); // mid-height tucks (expected, reported)
    oursOnlyTotal += oursOnly.length;
    if (ccOnly.length) {
      ccOnlyCases++;
      if (examples.length < 5) examples.push(
        `case#${i} ${cases[i]!.type}: cc-only (a placement cold-clear reaches, our BFS MISSES) = ${ccOnly.slice(0, 4).join(' ')}\n` +
        boardToRows(cases[i]!.board).split('\n').filter(r => r.includes('X')).join('\n'));
    }
  }
  return { ccTotal, oursOnlyTotal, ccOnlyTotal, ccOnlyCases, examples };
}

describe.skipIf(!HAVE_ORACLE)('reachable placements vs real cold-clear find_moves', () => {
  test('empty board: every piece reaches EXACTLY cold-clear\'s set (no overhangs, so no superset)', () => {
    // With no overhangs there are no mid-height tucks, so the two models coincide exactly here.
    const cases = PIECES.map(type => ({ board: emptyBoard(), type }));
    const { ccTotal, oursOnlyTotal, ccOnlyTotal } = compareAll(cases);
    expect(ccOnlyTotal).toBe(0);
    expect(oursOnlyTotal).toBe(0);
    expect(ccTotal).toBeGreaterThan(100);   // 34+17+9+17+17+34+34 = 162 distinct placements
  });

  test('2000 seeded overhang boards x 7 pieces: cc ⊆ ours (0 false negatives), superset non-vacuous', () => {
    // Three height regimes, two of them >= 16 to exercise cold-clear's non-fast mover.
    const boards = [...randomBoards(12345, 800, 12), ...randomBoards(67890, 800, 18), ...randomBoards(999, 400, 8)];
    const cases = boards.flatMap(board => PIECES.map(type => ({ board, type })));
    const { ccTotal, oursOnlyTotal, ccOnlyTotal, ccOnlyCases, examples } = compareAll(cases);
    // THE GATE: our BFS reaches every placement real cold-clear reaches (no reachability false negatives).
    expect(ccOnlyTotal, `${ccOnlyCases} case(s) where cold-clear reaches a placement our BFS misses:\n${examples.join('\n---\n')}`).toBe(0);
    // anti-vacuity: cold-clear re-reached a large set, and the overhang corpus really does drive
    // the mid-height tucks that make ours a strict superset (else this would be a vacuous subset).
    expect(ccTotal).toBeGreaterThan(cases.length * 5);
    expect(oursOnlyTotal).toBeGreaterThan(0);
  }, 120_000);
});

// The random-board legs above exercise the tables broadly but prove nothing about the boards the
// forecast metric actually runs on. This leg is item 3's corpus requirement (engine-verification-plan
// § Item 3): every verified-prefix board of every session, the piece bestTspin actually walks. Session
// list is explicit, not globbed (memory: sim-test-corpus-silently-under-covers) — a new session's
// directory existing is not enough to be included; it must be named here.
const SIM_SESSIONS = ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14']
  .map(s => `${import.meta.dir}/../../sessions/${s}`).filter(existsSync);

describe.skipIf(!HAVE_ORACLE || SIM_SESSIONS.length === 0)(
  'reachable placements vs real cold-clear over the verified-prefix corpus (real game boards, T piece)',
  () => {
    test('every verified-prefix board of all six sessions: cc ⊆ ours (0 false negatives)', () => {
      const perSession: Record<string, number> = {};
      const cases: { board: Board; type: PieceType }[] = [];
      for (const session of SIM_SESSIONS) {
        const name = session.split('/').pop()!;
        process.env.REPLAY_DIR = session;
        let n = 0;
        for (const c of loadCases(session)) {
          const r = runCase(c, {});
          const v = verifiedIndex(r, c.truth);
          for (let step = 0; step <= v; step++) { cases.push({ board: r.boards[step]!, type: 'T' }); n++; }
        }
        perSession[name] = n;
        // A session contributing zero boards has silently fallen out of the corpus, not just this one.
        expect(n, `${name} contributed 0 verified-prefix boards`).toBeGreaterThan(0);
      }
      const { ccTotal, oursOnlyTotal, ccOnlyTotal, ccOnlyCases, examples } = compareAll(cases);
      const summary = Object.entries(perSession).map(([k, v]) => `${k}: ${v}`).join(', ');
      // THE GATE, over real game boards this time: our BFS reaches every T-placement cold-clear reaches.
      expect(ccOnlyTotal,
        `${ccOnlyCases} case(s) where cold-clear reaches a T-placement our BFS misses ` +
        `(corpus: ${summary}):\n${examples.join('\n---\n')}`).toBe(0);
      // Anti-vacuity, derived from the session list rather than one hardcoded grand total (risk R8 —
      // cross-tslot.test.ts:99's literal 7544 predates session five and would have silently stayed
      // right had a session's contribution shrunk instead of grown).
      expect(cases.length, summary).toBeGreaterThan(SIM_SESSIONS.length * 200);
      expect(ccTotal).toBeGreaterThan(cases.length);
      expect(oursOnlyTotal).toBeGreaterThan(0);       // real boards have overhangs/tucks too
    }, 300_000);
  },
);
