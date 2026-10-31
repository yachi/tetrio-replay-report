/**
 * Which placements each player makes with the most finesse faults — the 最多犯錯嘅 finesse 擺位 section.
 *
 *   REPLAY_DIR=sessions/2026-10-29 bun pipeline/sim/emit-finesse-facts.ts \
 *     --out sessions/2026-10-29/sim/finesse-facts.json
 *
 * TETR.IO publishes no finesse algorithm, so the rule here is FITTED, and the anchor is what licenses
 * printing anything from it. Every player-round is re-run through the vendored Triangle engine
 * (byte-identical to @haelp/teto), and every lock is scored:
 *
 *   - the engine's own input counter `falling.keys` (+1 per left/right keydown, +1 per CW/CCW,
 *     +2 per 180) is what the player spent on the piece;
 *   - the TARGET is the fewest inputs that reach the same cells on an EMPTY board from the spawn
 *     state, by Dijkstra over the engine's own Tetromino and kick table (tap left/right 1, DAS to the
 *     wall 1, CW/CCW 1, 180 2). Cells are keyed by shape (absolute columns, rows relative to the
 *     lowest), so a symmetric piece's orientations that cover the same cells are one placement;
 *   - excess = keys − target. excess > 0 adds `excess` fault events; otherwise the piece is perfect;
 *   - a piece whose own key presses (since the last lock, restarted on hold) include softDrop is
 *     NOT scored and counts as perfect, as is a piece whose cells no empty-board path reaches (a
 *     tuck under an overhang).
 *
 * ANCHOR: per player-round, the engine's perfect-piece count and fault count against the replay's
 * own `results.stats.finesse.perfectpieces` / `.faults`. Where both agree, the rule reproduces
 * TETR.IO's own counters for that round exactly; the rounds where it does not are listed in
 * `anchor.exceptions`, by name, and the test pins them. Which placement carried the faults has no
 * second implementation and no counter to check it against piece by piece, so the artefact says
 * `report_eligible: false`.
 *
 * A placement is (piece, shape index into emit-replay's SHAPES, leftmost column). The artefact carries
 * THIS SESSION's counts only.
 */
import { writeFileSync } from 'node:fs';
import { basename } from 'node:path';
import { loadCases, replayDir } from './verified-prefix.ts';
import { createEngine } from './vendor/teto/create-engine.mjs';
import { TL_DEFAULTS } from './oracle-source.ts';
import { SHAPES } from './emit-replay.ts';

/** Input names, as printed: the engine's key name → the arrow the section draws. */
export const MOVE = {
  moveLeft: '←', moveRight: '→', dasLeft: '⇤', dasRight: '⇥',
  rotateCW: '↻', rotateCCW: '↺', rotate180: '180',
} as const;

type Path = string[];
export type Table = Map<string, { cost: number; path: Path }>;

/** Absolute columns, rows relative to the lowest cell, sorted — the empty-board placement key. */
export function shapeKey(cells: [number, number][]) {
  const my = Math.min(...cells.map(c => c[1]));
  return cells.map(([x, y]) => `${x}:${y - my}`).sort().join(' ');
}

/**
 * The finesse table for one piece: every empty-board placement the engine can reach from spawn, its
 * fewest inputs and one input path achieving it. Dijkstra on (rotation, column); among equal-cost
 * paths the first one popped wins, and the queue order is fixed, so the path is deterministic.
 */
export function finesseTable(eng: any, sym: string): Table {
  const T = eng.falling.constructor;
  const mk = () => new T({ symbol: sym, initialRotation: eng.kickTable?.spawn_rotation?.[sym.toLowerCase()] ?? 0,
    boardWidth: 10, boardHeight: 20 });
  const empty = Array.from({ length: 40 }, () => new Array(10).fill(null));
  const kt = eng.kickTable;
  const key = (t: any) => `${t.rotation},${t.location[0]}`;
  const start = mk();
  const dist = new Map<string, number>(), states = new Map<string, any>(), path = new Map<string, Path>();
  dist.set(key(start), 0); states.set(key(start), start); path.set(key(start), []);
  const q: [number, number, string][] = [[0, 0, key(start)]];
  let seq = 1;
  while (q.length) {
    q.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const [d, , k] = q.shift()!;
    if (d > dist.get(k)!) continue;
    const s = states.get(k);
    const clone = () => { const c = mk(); c.rotation = s.rotation; c.location = [...s.location]; return c; };
    const moves: [any, number, string][] = [];
    { const c = clone(); if (c.moveLeft(empty)) moves.push([c, 1, MOVE.moveLeft]); }
    { const c = clone(); if (c.moveRight(empty)) moves.push([c, 1, MOVE.moveRight]); }
    { const c = clone(); let m = false; while (c.moveLeft(empty)) m = true; if (m) moves.push([c, 1, MOVE.dasLeft]); }
    { const c = clone(); let m = false; while (c.moveRight(empty)) m = true; if (m) moves.push([c, 1, MOVE.dasRight]); }
    for (const [a, cost, name] of [[1, 1, MOVE.rotateCW], [3, 1, MOVE.rotateCCW], [2, 2, MOVE.rotate180]] as [number, number, string][]) {
      const c = clone(); if (c.rotate(empty, kt, a, 2)) moves.push([c, cost, name]);
    }
    for (const [c, cost, name] of moves) {
      const kk = key(c), nd = d + cost;
      if (!dist.has(kk) || nd < dist.get(kk)!) {
        dist.set(kk, nd); states.set(kk, c); path.set(kk, [...path.get(k)!, name]); q.push([nd, seq++, kk]);
      }
    }
  }
  const out: Table = new Map();
  for (const [k, s] of states) {
    const sk = shapeKey(s.absoluteBlocks);
    const d = dist.get(k)!;
    if (!out.has(sk) || d < out.get(sk)!.cost) out.set(sk, { cost: d, path: path.get(k)! });
  }
  return out;
}

/** (piece, shape index, leftmost column) for engine cells (y up from the floor). */
export function placementOf(piece: string, cells: [number, number][]) {
  const mx = Math.min(...cells.map(c => c[0])), my = Math.min(...cells.map(c => c[1]));
  const norm = JSON.stringify(cells.map(([x, y]) => [x - mx, y - my]).sort((a, b) => a[1]! - b[1]! || a[0]! - b[0]!));
  const shape = SHAPES[piece]!.findIndex(s => JSON.stringify(s) === norm);
  if (shape < 0) throw new Error(`emit-finesse-facts: no ${piece} shape for ${norm}`);
  return { shape, col: mx };
}

export type Piece = {
  i: number; piece: string; shape: number; col: number;
  keys: number; target: number | null; scored: boolean; excess: number; moves: string[];
};

/** One player-round through the engine: every lock's input count, its target and the key presses
 *  the player made on that piece. */
/** `mutant` exists for the test only: `scoreSoftDrop` drops the softDrop skip. */
export function runRound(c: any, tables: Map<string, Table>, mutant: { scoreSoftDrop?: boolean } = {}) {
  const player = c.rawPlayer, o = player.replay.options;
  const players = c.rawRound.map((p: any) => ({ gameid: p.replay.options.gameid, userid: p.id, username: p.username }));
  const eng: any = createEngine({ ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g }, o.gameid, players);
  if (!tables.size) for (const s of 'IJLOSTZ') tables.set(s, finesseTable(eng, s));
  // `res.keysPresses` holds only the current frame's keys (the engine flushes its cache every tick),
  // so the cache is replaced after every tick by an array that also records into the piece's list.
  let own: string[] = [];
  const arm = () => {
    const a: any = [];
    a.push = (...x: string[]) => { own.push(...x); return Array.prototype.push.apply(a, x); };
    eng.resCache.keys = a;
  };
  arm();
  eng.events.on('falling.new', (e: any) => { if (e.isHold) own = []; });
  let pre: any = null;
  eng.events.on('falling.lock.pre', () => {
    const f = eng.falling;
    pre = { piece: String(f.symbol).toUpperCase(), keys: f.keys as number,
            cells: f.absoluteBlocks.map((b: number[]) => [b[0], b[1]] as [number, number]) };
  });
  const pieces: Piece[] = [];
  eng.events.on('falling.lock', () => {
    const t = tables.get(pre.piece)!.get(shapeKey(pre.cells));
    const sd = own.includes('softDrop');
    const scored = t !== undefined && (!sd || !!mutant.scoreSoftDrop);
    const excess = scored ? Math.max(0, pre.keys - t!.cost) : 0;
    const { shape, col } = placementOf(pre.piece, pre.cells);
    pieces.push({ i: pieces.length, piece: pre.piece, shape, col, keys: pre.keys, target: t?.cost ?? null, scored, excess,
      moves: own.filter(k => k in MOVE).map(k => (MOVE as any)[k]) });
    own = [];
  });
  const byFrame = new Map<number, any[]>();
  for (const e of player.replay.events) { if (!byFrame.has(e.frame)) byFrame.set(e.frame, []); byFrame.get(e.frame)!.push(e); }
  for (let f = 0; f <= player.replay.frames; f++) { eng.tick(byFrame.get(f) || []); arm(); }
  return pieces;
}

const TOP = 10;

export function build(dir: string, mutant: { scoreSoftDrop?: boolean } = {}) {
  const tables = new Map<string, Table>();
  const anchor = { rounds: 0, agree: 0, unknown: 0, exceptions: [] as any[] };
  const P: Record<string, any> = {};
  const byUser = (a: { user: string }, b: { user: string }) => a.user < b.user ? -1 : a.user > b.user ? 1 : 0;
  for (const c of loadCases(dir) as any[]) {
    const pieces = runRound(c, tables, mutant);
    const fin = c.rawPlayer.replay.results.stats.finesse;
    const perfect = pieces.filter(p => p.excess === 0).length;
    const faults = pieces.reduce((a, p) => a + p.excess, 0);
    anchor.rounds++;
    if (!fin || typeof fin.perfectpieces !== 'number' || typeof fin.faults !== 'number') anchor.unknown++;
    else if (fin.perfectpieces === perfect && fin.faults === faults) anchor.agree++;
    else anchor.exceptions.push({ file: c.file, round: c.round, user: c.user,
      engine: { perfect, faults }, replay: { perfect: fin.perfectpieces, faults: fin.faults } });

    const pl = (P[c.user] ??= { user: c.user, rounds: 0, pieces: 0, scored: 0, faulty: 0, faults: 0,
      not_scored: { soft_drop: 0, no_empty_board_path: 0 }, M: {} as Record<string, any> });
    pl.rounds++; pl.pieces += pieces.length;
    for (const p of pieces) {
      if (!p.scored) { if (p.target === null) pl.not_scored.no_empty_board_path++; else pl.not_scored.soft_drop++; continue; }
      pl.scored++;
      const k = `${p.piece}|${p.shape}|${p.col}`;
      const m = (pl.M[k] ??= { piece: p.piece, shape: p.shape, col: p.col, cells: SHAPES[p.piece]![p.shape],
        target: p.target, optimal: tables.get(p.piece)!.get(shapeKey(SHAPES[p.piece]![p.shape]!.map(
          ([x, y]) => [x + p.col, y] as [number, number])))!.path,
        scored: 0, faulty: 0, faults: 0, seqs: {} as Record<string, number>, example: null as any });
      m.scored++;
      if (p.excess > 0) {
        pl.faulty++; pl.faults += p.excess; m.faulty++; m.faults += p.excess;
        const s = p.moves.join(' ');
        m.seqs[s] = (m.seqs[s] ?? 0) + 1;
        if (!m.example || p.excess > m.example.excess)
          m.example = { file: c.file, round: c.round, lock: p.i, keys: p.keys, excess: p.excess, moves: p.moves };
      }
    }
  }
  const players = Object.values(P).sort(byUser).map((pl: any) => {
    const all = Object.values(pl.M) as any[];
    const ranked = all.filter(m => m.faults > 0).sort((a, b) =>
      b.faults - a.faults || b.faulty - a.faulty || a.piece.localeCompare(b.piece) || a.shape - b.shape || a.col - b.col);
    const { M, ...rest } = pl;
    return { ...rest, placements_scored: all.length, placements_with_faults: ranked.length,
      top: ranked.slice(0, TOP).map(m => {
        const [seq, n] = Object.entries(m.seqs as Record<string, number>)
          .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))[0]!;
        const { seqs, ...o } = m;
        return { ...o, most_common_faulty: { moves: seq ? seq.split(' ') : [], n } };
      }) };
  });
  return {
    schema: 'finesse-facts/1',
    session: basename(dir),
    report_eligible: false,
    source: 'vendored Triangle engine (pipeline/sim/vendor/teto): falling.keys per lock against an empty-board '
      + 'Dijkstra over the engine\'s own Tetromino and kick table',
    rule: 'excess = falling.keys - fewest inputs to the same cells on an empty board (tap 1, DAS-to-wall 1, '
      + 'CW/CCW 1, 180 2); excess > 0 adds excess fault events, else the piece is perfect; a piece whose own '
      + 'key presses include softDrop, or whose cells no empty-board path reaches, is not scored and counts '
      + 'as perfect. The rule is fitted to TETR.IO\'s counters, which publish no algorithm.',
    not_eligible_because: [
      'the rule is fitted, not published by TETR.IO; which placement carried a fault has no second implementation',
    ],
    placement: 'piece + shape index into emit-replay SHAPES (cells from the bottom-left, y up) + leftmost column (0-based)',
    top_n: TOP,
    anchor,
    players,
  };
}

export const serialise = (x: unknown) => JSON.stringify(x, null, 1) + '\n';

if (import.meta.main) {
  const outIx = process.argv.indexOf('--out');
  const dir = replayDir();
  const out = build(dir);
  if (outIx > 0) writeFileSync(process.argv[outIx + 1]!, serialise(out));
  const a = out.anchor;
  console.log(`${out.session}: finesse anchor ${a.agree}/${a.rounds} (unknown ${a.unknown})`);
  for (const e of a.exceptions) console.log('  exception', JSON.stringify(e));
}
