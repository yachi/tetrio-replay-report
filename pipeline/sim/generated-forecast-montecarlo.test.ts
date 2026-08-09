/**
 * Monte Carlo: does a forecast ever arise by CHANCE? Play random games, run the detector, count.
 *
 * The fuzz test proves the detector fires on constructed forecasts. This asks the complementary
 * question at scale: across thousands of real placements of ordinary play, does a forecast appear on
 * its own? A hole-AVOIDING heuristic bot (minimise aggregate height, holes, bumpiness — with random
 * jitter) drives 100 games of up to 150 pieces through the real SRS engine (spawn → move/rotate →
 * hardDrop → lock → clear). Every line-clearing T is GENEROUSLY marked a spin, to give the forecast
 * path maximum opportunity. Then `forecastMetric` runs on each game.
 *
 * Result (seed 7, deterministic): ~3,600 line clears and ~460 line-clearing T-spins are produced,
 * the detector runs on all of them WITHOUT THROWING, and finds **0 verified forecasts** — in fact 0
 * forecast RECORDS, because every one of those T-spins is untucked. That is the mechanism, not luck:
 * a forecast REQUIRES an overhang deliberately laid over a pre-existing hole and opened by an earlier
 * external clear — the exact opposite of the clean stacking a hole-minimiser does. Forecasts do not
 * occur by chance; they are a deliberate act. This is the corpus 0 reproduced from first principles,
 * and independent evidence that the detector does not false-positive on ordinary play.
 */
import { test, expect } from 'bun:test';
import { spawnPiece, tryMove, tryRotate, hardDrop, getPieceCells, isValidPosition, createBoard } from './vendor/core/srs.ts';
import { forecastMetric, isVerifiedForecast } from './forecast.ts';
import { H } from './sim.ts';
import type { PieceType } from './vendor/core/types.ts';

const W = 10;
const PIECES: PieceType[] = ['I', 'O', 'T', 'S', 'Z', 'L', 'J'];
const filled = (c: any) => c !== null;
function mulberry32(a: number) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// board score: lower is better (aggregate height + 4·holes + ½·bumpiness) — a clean-stacking bot
function score(b: any[][]) {
  const hgt = new Array(W).fill(0); let holes = 0;
  for (let c = 0; c < W; c++) { let seen = false; for (let r = 0; r < H; r++) { if (filled(b[r]![c])) { if (!seen) { hgt[c] = H - r; seen = true; } } else if (seen) holes++; } }
  let bump = 0; for (let c = 0; c < W - 1; c++) bump += Math.abs(hgt[c] - hgt[c + 1]);
  return hgt.reduce((a: number, x: number) => a + x, 0) + 4 * holes + 0.5 * bump;
}

function bestPlacement(board: any[][], type: PieceType, rnd: () => number) {
  let best: any = null, bestScore = 1e9;
  for (let rot = 0; rot < 4; rot++) for (let col = -2; col < W; col++) {
    let p: any = { type, rotation: rot as any, col, row: 0 };
    if (!isValidPosition(board as any, p)) continue;
    p = hardDrop(board as any, p);
    const cells = getPieceCells(p);
    if (cells.some(c => c.row < 0 || c.row >= H || c.col < 0 || c.col >= W)) continue;
    const nb = board.map(r => [...r]); for (const c of cells) nb[c.row]![c.col] = type;
    const sc = score(nb) + rnd() * 2;
    if (sc < bestScore) { bestScore = sc; best = { cells, rot }; }
  }
  return best;
}

function game(rnd: () => number, K: number) {
  const board = createBoard().map(r => [...r]) as any[][];
  const prov: (number | null)[][] = board.map(r => r.map(() => null));
  const boards = [board.map(r => [...r])], provSnaps = [prov.map(r => [...r])];
  const locks: any[] = [{ frame: 0, piece: 'I', cells: [], cleared: 0, spin: 'none', allclear: false }];
  let bag: PieceType[] = [];
  const next = () => { if (!bag.length) { bag = [...PIECES]; for (let i = bag.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1));[bag[i], bag[j]] = [bag[j]!, bag[i]!]; } } return bag.pop()!; };
  for (let i = 1; i <= K; i++) {
    const type = next(), bp = bestPlacement(board, type, rnd);
    if (!bp) break;                                    // topped out
    const { cells, rot } = bp;
    for (const c of cells) { board[c.row]![c.col] = type; prov[c.row]![c.col] = i; }
    const full: number[] = [];
    for (let r = 0; r < H; r++) if (board[r]!.every(filled)) full.push(r);
    for (const r of full) { board.splice(r, 1); board.unshift(new Array(W).fill(null)); prov.splice(r, 1); prov.unshift(new Array(W).fill(null)); }
    const spin = (type === 'T' && full.length > 0 && rot !== 0) ? 'full' : 'none';  // generous
    locks.push({ frame: i * 100, piece: type, cells, cleared: full.length, spin, allclear: board.every(r => r.every(c => c === null)) });
    boards.push(board.map(r => [...r])); provSnaps.push(prov.map(r => [...r]));
  }
  return { lines: 0, placed: 0, holds: 0, clears: {}, garbage: { sent: 0, received: 0, cleared: 0, attack: 0 }, topbtb: 0, topcombo: 0,
    boards, records: [], events: [], locks, garbageEvents: [], provSnaps, topout: false } as any;
}

test('Monte Carlo: no forecast arises by chance across ~100 random games', () => {
  const rnd = mulberry32(7);
  const N = 100, K = 150;
  let throws = 0, clears = 0, tSpins = 0, verified = 0;
  for (let g = 0; g < N; g++) {
    let gm: any;
    try { gm = game(rnd, K); } catch { throws++; continue; }
    for (const l of gm.locks) { if (l.cleared > 0) clears++; if (l.spin === 'full') tSpins++; }
    let out: any;
    try { out = forecastMetric(gm, true); } catch { throws++; continue; }
    verified += out.records.filter(isVerifiedForecast).length;
  }
  // engagement: the detector actually saw a lot of play (else "0 forecasts" would be vacuous)
  expect(clears).toBeGreaterThan(1000);
  expect(tSpins).toBeGreaterThan(100);
  // robustness + the finding: no throw, and not one forecast by chance
  expect(throws).toBe(0);
  expect(verified).toBe(0);
}, 30_000);
