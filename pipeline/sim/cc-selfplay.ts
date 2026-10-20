/**
 * Cold-clear SELF-PLAY games, replayed through the repo's engine: the core both the research pilot
 * (`tools/cc-coach/cutcopy-selfplay.ts`) and the committed artefact (`emit-cutcopy-selfplay.ts` →
 * `analysis/cutcopy-selfplay.json`, tested by `pipeline/openers/cutcopy-selfplay.test.ts`) read.
 *
 * A game is what `tools/cc-coach/cc-coach.rs` writes in COACH_MODE=selfplay: the dealt `queue` and every
 * placement cold-clear made as {piece, hold, cells [x, row-top-down], kind, tspin, lines}. Nobody played these
 * games: a bot played them alone, from an empty board, with no garbage. They are not corpus data.
 *
 * THE ENGINE IS THE ARBITER. Each game is replayed through the vendored Triangle engine (TETR.IO's TL ruleset at
 * g = 0, the demo planner's own `newEngine`), with the dealt queue spliced in exactly as `route-demos.runDemo`
 * does. For every placement the path is found by the planner's own `reach` (a BFS over the engine's moves, SRS+
 * kicks, 180 allowed) on a scratch engine, turned into key events by `inputsOf`, and played; the lock the ENGINE
 * records is what is scored. A placement the engine cannot reproduce — the piece is not the one falling after
 * the hold, no engine path reaches the cells, the engine's cells or lines differ from cold-clear's — CUTS the
 * game there (its board would no longer be cold-clear's), and the cut is returned with its reason. A spin-credit
 * disagreement (cold-clear's T-spin rule against the engine's) is returned and does not cut: the engine's credit
 * is what the matcher reads. For a T the path is CHOSEN: the first `reach` path whose engine spin equals
 * cold-clear's, else the first path.
 *
 * Every replayed game is also recorded through `emit-replay.instrumentEngine` — the hooks a corpus round and a
 * constructed demo are recorded by — so the same run yields the timeline a page player decodes.
 */
import { newEngine, reach, inputsOf } from './route-demos.ts';
import { instrumentEngine, type Lock } from './emit-replay.ts';
import type { LockLite, TSpinLock, TechDigest } from './technique-facts.ts';

export const H = 40, W = 10;
/** `newEngine` dates the engine from a routes file's fetch date; there is none here, so a fixed one (the
 *  pilot's). Changing it changes the engine's options date and therefore every timeline: it is hashed with
 *  this file. */
export const SELFPLAY_ENGINE_ROUTES = { source: { fetched: '2026-10-20' } };
const SPIN_OF_CC: Record<string, string | null> = { Full: 'normal', Mini: 'mini', None: null };

/** An engine board ([y-UP][x] of tiles) as rows top first: '.' empty, 'G' garbage, a piece letter. */
export const rowsOf = (st: any[][]): string[] => {
  const out: string[] = [];
  for (let r = 0; r < H; r++) {
    const src = st[(H - 1) - r]; let s = '';
    for (let x = 0; x < W; x++) { const t = src?.[x]; s += t == null ? '.' : t.mino === 'gb' ? 'G' : String(t.mino).toUpperCase(); }
    out.push(s);
  }
  return out;
};
const gridOf = (st: any[][]) => Array.from({ length: H }, (_, y) =>
  Array.from({ length: W }, (_, x) => { const t = st[y]?.[x]; return t == null ? null : String(t.mino); }));

/** One placement as cc-coach writes it (only the fields the replay reads). */
export interface CcStep { piece: string; hold: boolean; cells: [number, number][]; lines: number; tspin: string;
                          kind: string; dead?: boolean }
export interface CcGame { seed: number; queue: string; steps: CcStep[]; final_field?: string[]; id?: string; nodes?: number }

export interface Replayed {
  /** every placement up to the cut was reproduced */
  ok: boolean;
  cut: { why: string; where: string } | null;
  /** placements cold-clear made (dead ones dropped), and whether any was dead */
  steps: CcStep[];
  dead: boolean;
  /** per replayed T placement whose engine spin differs from cold-clear's */
  spinDisagreements: string[];
  locks: LockLite[];
  tspins: TSpinLock[];
  /** the engine's final board, rows top first, when the game completed */
  finalRows: string[] | null;
  /** the timeline, as `instrumentEngine` records it, and the queue the engine dealt from; `engineStates` /
   *  `engineQueue` are the engine's own board and piece after every lock, for `assertRoundTrip` */
  timeline: { seq: string; locks: Lock[]; frames: number; engineStates: string[];
              engineQueue: { piece: string; hold: string }[] };
}

/** Replay one game's placements (all of them, or the first `limit`) through the engine. */
export function replayGame(g: CcGame, limit?: number): Replayed {
  const seq: string = g.queue;
  const all = g.steps.filter(s => !s.dead);
  const steps = limit === undefined ? all : all.slice(0, limit);
  const scratch = newEngine(SELFPLAY_ENGINE_ROUTES);
  const eng = newEngine(SELFPLAY_ENGINE_ROUTES);
  eng.queue.splice(0, eng.queue.length, ...[...seq.slice(1)].map(c => c.toLowerCase()));
  eng.initiatePiece(seq[0]!.toLowerCase());
  const rec = instrumentEngine(eng);
  // NB: at 'falling.lock.pre' the engine has ALREADY locked and cleared (index.mjs emits it after the
  // clear), so the board BEFORE the lock is taken before the step's inputs are played; only the piece's
  // pre-clear cells are read at lock.pre (the falling piece still sits where it locked).
  let pre: { board: string[]; cells: { row: number; col: number }[] } | null = null;
  let boardBefore: string[] = [];
  let lockRes: any = null;
  eng.events.on('falling.lock.pre', () => {
    pre = { board: boardBefore,
            cells: eng.falling.absoluteBlocks.map(([x, y]: [number, number]) => ({ row: (H - 1) - y, col: x })) };
  });
  eng.events.on('falling.lock', (res: any) => { lockRes = res; });
  let frame = 0;
  const tickTo = (events: any[], until: number) => {
    const by = new Map<number, any[]>();
    for (const e of events) { if (!by.has(e.frame)) by.set(e.frame, []); by.get(e.frame)!.push(e); }
    for (; frame <= until; frame++) eng.tick(by.get(frame) || []);
  };
  const locks: LockLite[] = [], tspins: TSpinLock[] = [], spinDisagreements: string[] = [];
  let cut: Replayed['cut'] = null;
  for (let j = 0; j < steps.length; j++) {
    const s = steps[j]!;
    const where = `seed ${g.seed} lock ${j}`;
    // which piece will be placed: after a hold, the held piece (or the next in the queue if none)
    const cur = String(eng.falling.symbol).toUpperCase();
    const placed = s.hold ? (eng.held != null ? String(eng.held).toUpperCase() : String(eng.queue[0]).toUpperCase()) : cur;
    if (placed !== s.piece) { cut = { why: 'piece_mismatch', where: `${where} cc ${s.piece} engine ${placed}` }; break; }
    const target = s.cells.map(([x, r]) => ((H - 1) - r) * W + x);
    const paths = reach(scratch, gridOf(eng.board.state), s.piece, target);
    if (!paths.length) { cut = { why: 'no_engine_path', where: `${where} ${s.piece} ${JSON.stringify(s.cells)}` }; break; }
    const want = SPIN_OF_CC[s.tspin] ?? null;
    const path = s.piece === 'T' ? (paths.find(p => p.spin === want) ?? paths[0]!) : paths[0]!;
    const { inputs, frames } = inputsOf([{ hold: s.hold, edges: path.edges } as any]);
    const base = frame;
    pre = null; lockRes = null; boardBefore = rowsOf(eng.board.state);
    tickTo(inputs.map(([f, type, k]) => ({ frame: base + f, type, data: { key: k, subframe: 0 } })), base + frames);
    if (!lockRes || !pre) { cut = { why: 'no_lock', where }; break; }
    const p = pre as { board: string[]; cells: { row: number; col: number }[] };
    const got = p.cells.map(q => ((H - 1) - q.row) * W + q.col).sort((a, b) => a - b).join(',');
    if (got !== [...target].sort((a, b) => a - b).join(',')) { cut = { why: 'cells_mismatch', where }; break; }
    if (lockRes.lines !== s.lines) { cut = { why: 'lines_mismatch', where: `${where} cc ${s.lines} engine ${lockRes.lines}` }; break; }
    const espin = lockRes.spin === 'none' ? null : lockRes.spin === 'mini' ? 'mini' : 'normal';
    if (s.piece === 'T' && espin !== want)
      spinDisagreements.push(`${where} cc ${s.kind}/${s.tspin} engine ${lockRes.spin} lines ${lockRes.lines}`);
    // the row map, checked against the engine's own board after the lock (no garbage in self-play)
    const g2 = p.board.map(r => [...r].map(c => c !== '.'));
    for (const q of p.cells) if (q.row >= 0 && q.row < H) g2[q.row]![q.col] = true;
    const clearedRows: number[] = [];
    for (let r = 0; r < H; r++) if (g2[r]!.every(Boolean)) clearedRows.push(r);
    const kept = g2.filter((_, r) => !clearedRows.includes(r));
    while (kept.length < H) kept.unshift(new Array(W).fill(false));
    const after = rowsOf(eng.board.state);
    const mapOk = kept.every((row, r) => row.every((x, c) => x === (after[r]![c] !== '.')));
    const spin = lockRes.spin === 'none' ? 'none' : lockRes.spin === 'mini' ? 'mini' : 'full';
    locks.push({ piece: s.piece, spin, cleared: lockRes.lines, cells: p.cells, clearedRows, garbage: 0, mapOk });
    if (s.piece === 'T' && spin !== 'none' && lockRes.lines > 0) tspins.push({ i: j, board: p.board });
  }
  return { ok: cut === null, cut, steps, dead: g.steps.some(s => s.dead), spinDisagreements, locks, tspins,
           finalRows: cut === null ? rowsOf(eng.board.state) : null,
           timeline: { seq, locks: rec.locks, frames: frame - 1, engineStates: rec.engineStates,
                       engineQueue: rec.engineQueue } };
}

/** A replayed game as the corpus classifier's digest: no garbage, every lock "verified" (the prefix is the
 *  engine's own replay). */
export function digestOf(g: CcGame, r: Replayed, index: number): TechDigest {
  return { session: 'selfplay', file: `seed-${g.seed}`, round: 0, match: index + 1, user: 'cold-clear',
           v: r.locks.length - 1, locks: r.locks, tspins: r.tspins };
}
