/**
 * The shared CONSTRUCTED-DEMO PLANNER for the route pages: one replay per drawn route node of a
 * shiwehi.com opener page, built from an empty board by placing the pieces one at a time, and run
 * through the vendored Triangle engine. The opener-specific half (the bag-1 queue rule, the held
 * piece, the colour readings, the unbuilt nodes and the artefact's strings) is the profile's
 * `demos` (`route-profile.ts`); every rule is here, once.
 *
 *   bun pipeline/sim/emit-route-demos.ts --opener <key> --out <artefact>
 *   bun pipeline/sim/emit-stray-cannon-demos.ts --out analysis/stray-cannon-demos.json   # 迷走砲's shim
 *
 * NOT CORPUS DATA. Nobody played these games: the piece queue, the hold and the key inputs are OURS,
 * chosen by the planner below. The artefact says `report_eligible: false` and `constructed: true`,
 * and nothing that draws from it carries a claim id, a ✓ or a `data-claim`.
 *
 * THE ENGINE IS THE ARBITER; THE PLANNER ONLY PROPOSES. For each piece the planner searches the
 * engine's own move space (its `performKick` through `eng.rotateCW/CCW/180`, SRS+ with 180, lateral
 * steps and one-row drops, gravity support at the end) for a path from the engine's spawn state to
 * the drawn cells. The chosen paths become key events (`keydown`/`keyup`), and `build()` then replays
 * the whole input script on a fresh engine through `instrumentEngine` — the hooks `emit-replay.ts`
 * records every corpus lock with — and THROWS unless every lock lands on the planned cells with the
 * planned spin and line count. A planner bug can therefore never reach the artefact.
 *
 * THE ROW MAP. A route diagram is a kept-rows composite: rows that clear mid-bag stay drawn, and a
 * piece placed after a clear is drawn above the rows it fell through (`composite()` in
 * `route-facts.ts` builds exactly that frame from an engine run). The planner carries the inverse,
 * `rowmap` (from `route-facts.ts`, beside `composite()`): engine row e is diagram row rowmap[e], and
 * a piece is a candidate only while every row it is drawn on is still on the board.
 *
 * A `U` ON THE DRAWN BOARD IS THE SLOT THE T GOES INTO: the demo fires it, and the board just before
 * that lock is the drawing (bag 2 and the snapshot routes). In a Perfect Clear pattern the U is
 * placed wherever the order allows, and the last lock must be the Perfect Clear.
 */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createEngine } from './vendor/teto/create-engine.mjs';
import { legal } from './vendor/teto/engine/utils/kicks/index.mjs';
import { TL_DEFAULTS } from './oracle-source.ts';
import { instrumentEngine, assertRoundTrip, encodePlace, placeCells, queueStates, LOCK_FIELDS, SHAPES,
         NEXT_SHOWN, WIDTH, ROWS, VISIBLE_ROWS, type Lock } from './emit-replay.ts';
import { loadRoutes, conditionHolds, initialRowmap, advanceRowmap, md5Files,
         type RouteNode, type Routes } from './route-facts.ts';
import type { RouteProfile, DemoProfile, PieceReading } from './route-profile.ts';

/** A node's rows with the profile's colour readings applied (a cell group drawn in one piece's
 *  colour that can only be another piece). */
export function readRows(id: string, rows: string[], readings: PieceReading[], tag = 'route'): string[] {
  const out = rows.map(r => [...r]);
  for (const pr of readings.filter(p => p.node === id))
    for (const [x, d] of pr.cells) {
      const i = rows.length - 1 - d;
      if (out[i]![x] !== pr.drawn) throw new Error(`${tag}: ${id} reading cell ${x},${d} is not ${pr.drawn}`);
      out[i]![x] = pr.reads_as.toLowerCase();
    }
  return out.map(r => r.join(''));
}

/** The profile's demo half, or a loud failure: an opener without one has no demos yet. */
export function demoProfile(P: RouteProfile): DemoProfile {
  if (!P.demos) throw new Error(`${P.tag}-demos: the ${P.key} profile has no demos`);
  return P.demos;
}

/** Frames between one input and the next (a tap is held for one frame of them). */
export const FRAMES_PER_INPUT = 4;
/** The engine options every demo runs under: TETR.IO's TL ruleset with gravity off, so a piece moves
 *  only when an input moves it. Recorded in the artefact. */
export const DEMO_HANDLING = { das: 8, arr: 2, sdf: 20, dcd: 0, safelock: false, cancel: false,
                               irs: 'off', ihs: 'off', may20g: false };
export const DEMO_OPTIONS = { g: 0, gincrease: 0, gmargin: 0, seed: 0, handling: DEMO_HANDLING };
/** The engine's date: the day the route page was fetched (`source.fetched`), never the wall clock. */
export const demoDate = (routes: any) => new Date(`${routes.source.fetched}T00:00:00Z`);
export const PIECES = 'IOTSZJL';
/** Padding bags after the last bag a demo uses: whole bags in this fixed order. */
const PAD_BAG = 'IJLOSTZ';

// ── the board, y-UP, [y][x] holding a piece letter or null ────────────────────────────────────

type Grid = (string | null)[][];
export const emptyGrid = (): Grid => Array.from({ length: ROWS }, () => new Array<string | null>(WIDTH).fill(null));
export const cloneGrid = (g: Grid): Grid => g.map(r => [...r]);
export const gridKey = (g: Grid) => g.map(r => r.map(c => c ?? '.').join('')).join('/');

/** A fresh demo engine (exported for the test's unit check of `reach`). */
export function newEngine(routes: any) {
  const opts = { ...TL_DEFAULTS, ...DEMO_OPTIONS };
  const date = demoDate(routes);
  const eng = createEngine(opts, 'demo', [{ gameid: 'demo', userid: 'demo', username: 'demo' }], date) as any;
  // what the engine was built from, so `reach`'s cache can share a search between two engines built alike
  ENGINE_SIG.set(eng, `${JSON.stringify(opts)}|${date.toISOString()}`);
  return eng;
}

// ── reachability: a BFS over the engine's own moves ─────────────────────────────────────────────

/** One search state: the piece's location exactly as the engine holds it (y is fractional), its
 *  rotation, and the spin the engine would credit if it locked now (`lastSpin`: set by a rotation,
 *  cleared by a fall, KEPT by a sideways step — the engine's own rule, so it is part of the key). */
interface St { x: number; y: number; r: number; spin: string | null }
export type Edge = 'L' | 'R' | 'CW' | 'CCW' | '180' | 'D';
export interface Path { edges: Edge[]; spin: string | null; cells: number[] }
const key = (s: St) => `${s.r},${s.x},${Math.floor(s.y)},${s.spin}`;

/** The engine's one-row fall (`#__internal_fall(1)`), copied operation for operation, so a search
 *  state's fractional y is the one the engine will hold. */
function fall1(eng: any, s: St): St | null {
  let y1 = Math.round(1e6 * (s.y - 1)) / 1e6, y2 = s.y - 1;
  if (y1 % 1 === 0) y1 -= 1e-6;
  if (y2 % 1 === 0) y2 += 2e-6;
  const f = eng.falling;
  if (!legal(f.absoluteAt({ x: s.x, y: y1, rotation: s.r }), eng.board.state)
      || !legal(f.absoluteAt({ x: s.x, y: y2, rotation: s.r }), eng.board.state)) return null;
  return { x: s.x, y: y1, r: s.r, spin: null };
}
const cellsAt = (eng: any, s: St) =>
  eng.falling.absoluteAt({ x: s.x, y: s.y, rotation: s.r }).map(([x, y]: [number, number]) => y * WIDTH + x)
    .sort((a: number, b: number) => a - b);

/** `reach`'s cache: per engine build (`newEngine`'s options and date; an engine not built there keys by its
 *  own identity), per (board as the engine holds it, piece, no180), the whole search's answer — every resting
 *  placement's cells (sorted, joined) → the paths `reach` would return for that target, in discovery order.
 *  The BFS never reads the target (it only filters by it at the end), so one search answers every target on
 *  that board. Bounded: least recently used entries are dropped past `REACH_CACHE_MAX`. */
const ENGINE_SIG = new WeakMap<object, string>();
const ENGINE_OWN = new WeakMap<object, Map<string, Map<string, Path[]>>>();
const SIG_CACHE = new Map<string, Map<string, Map<string, Path[]>>>();
const REACH_CACHE_MAX = 4096;
function engineCache(eng: any): Map<string, Map<string, Path[]>> {
  const sig = ENGINE_SIG.get(eng);
  if (sig === undefined) {
    let c = ENGINE_OWN.get(eng);
    if (!c) ENGINE_OWN.set(eng, c = new Map());
    return c;
  }
  let c = SIG_CACHE.get(sig);
  if (!c) SIG_CACHE.set(sig, c = new Map());
  return c;
}
const copyPath = (p: Path): Path => ({ edges: [...p.edges], spin: p.spin, cells: [...p.cells] });

/** Every engine-legal resting placement of `piece` on `grid` whose cells are `target`, with the
 *  shortest path to each distinct arrival spin. `no180` (a mutant) drops the 180 edge. */
export function reach(eng: any, grid: Grid, piece: string, target: number[], opts: { no180?: boolean } = {})
  : Path[] {
  const state = grid.map(r => r.map(c => (c ? c.toLowerCase() : null)));
  const ck = `${opts.no180 ? 1 : 0}|${piece.toLowerCase()}|${state.map(r => r.map(c => c ?? '.').join('')).join('/')}`;
  const cache = engineCache(eng);
  let all = cache.get(ck);
  if (all) { cache.delete(ck); cache.set(ck, all); }
  else {
    all = searchAll(eng, state, piece, opts);
    cache.set(ck, all);
    if (cache.size > REACH_CACHE_MAX) cache.delete(cache.keys().next().value!);
  }
  const want = [...target].sort((a, b) => a - b).join(',');
  return (all.get(want) ?? []).map(copyPath);
}

/** The whole BFS behind `reach`, for every target at once: per resting placement's cells, the shortest path to
 *  each distinct arrival spin, in the order the search finds them. */
function searchAll(eng: any, state: (string | null)[][], piece: string, opts: { no180?: boolean })
  : Map<string, Path[]> {
  eng.board.state = state.map(r => r.map(c => (c ? { mino: c, connections: 0 } : null)));
  eng.held = null;
  eng.initiatePiece(piece.toLowerCase(), true);
  const f = eng.falling;
  const start: St = { x: f.location[0], y: f.location[1], r: f.rotation, spin: null };
  const prev = new Map<string, [string | null, Edge | null, St]>();
  prev.set(key(start), [null, null, start]);
  const queue: St[] = [start];
  const found = new Map<string, Path[]>();
  const seenSpin = new Map<string, Set<string>>();
  const rot = (s: St, how: Edge): St | null => {
    f.location = [s.x, s.y]; f.rotation = s.r; f.totalRotations = 0; f.lockResets = 0; f.rotResets = 0;
    eng.lastSpin = null;
    const ok = how === 'CW' ? eng.rotateCW() : how === 'CCW' ? eng.rotateCCW() : eng.rotate180();
    if (!ok) return null;
    const sp = eng.lastSpin == null || eng.lastSpin === 'none' ? null : String(eng.lastSpin);
    return { x: f.location[0], y: f.location[1], r: f.rotation, spin: sp };
  };
  const edges: Edge[] = opts.no180 ? ['L', 'R', 'D', 'CW', 'CCW'] : ['L', 'R', 'D', 'CW', 'CCW', '180'];
  for (let qi = 0; qi < queue.length; qi++) {
    const s = queue[qi]!;
    const k = key(s);
    if (!fall1(eng, s)) {
      const cells = cellsAt(eng, s);
      const ck = cells.join(',');
      let seen = seenSpin.get(ck);
      if (!seen) seenSpin.set(ck, seen = new Set());
      if (!seen.has(String(s.spin))) {
        seen.add(String(s.spin));
        const es: Edge[] = [];
        for (let c = k; prev.get(c)![0] !== null; c = prev.get(c)![0]!) es.unshift(prev.get(c)![1]!);
        let list = found.get(ck);
        if (!list) found.set(ck, list = []);
        list.push({ edges: es, spin: s.spin, cells });
      }
    }
    for (const e of edges) {
      let n: St | null;
      if (e === 'L' || e === 'R') {
        const nx = s.x + (e === 'L' ? -1 : 1);
        n = legal(f.absoluteAt({ x: nx, y: s.y, rotation: s.r }), eng.board.state) ? { ...s, x: nx } : null;
      } else if (e === 'D') n = fall1(eng, s);
      else n = rot(s, e);
      if (!n) continue;
      const nk = key(n);
      if (prev.has(nk)) continue;
      prev.set(nk, [k, e, n]);
      queue.push(n);
    }
  }
  return found;
}

// ── route diagrams → per-bag placement targets ──────────────────────────────────────────────────

/** One piece of a bag: the diagram cells drawn in its letter, as [x, diagram row from the bottom]. */
export interface Group { letter: string; piece: string; spinSlot: boolean; cells: [number, number][];
                         /** a piece of an EARLIER bag carried in the hold and placed in this one (はちみつ砲's
                          *  upper-case J): it is not one of this bag's dealt pieces */
                         carried?: boolean }

/** A PRIOR-BAG letter: an upper-case piece letter drawn in colour inside a later bag's board (the
 *  迷走砲 bag-1 Z inside a bag-2 board). `U` is this bag's T slot, `C`/`B` are shading, never pieces. */
const isPrior = (ch: string) => /^[A-Z]$/.test(ch) && !'UCB'.includes(ch);

/** What a bag's board is read against besides its own rows: the piece the hold carries in from an
 *  earlier bag (its upper-case letter is then placed in this bag, not already there), the lower-case
 *  letter the profile says is drawn in a spin slot, and the U cells of a separate spin board. */
interface Reading { carried: string | null; spinLetter: string | null; spinCells: [number, number][] }
const NO_READING: Reading = { carried: null, spinLetter: null, spinCells: [] };

/** Letters that are NOT this bag's pieces: `c` (an earlier bag), a prior-bag letter, `-` empty. `U`
 *  is this bag's T, fired as a T-spin. */
export function groupsOf(n: RouteNode, readings: PieceReading[], tag: string, rd: Reading = NO_READING): Group[] {
  // the page's inconsistent colourings are read as the piece the cells have to be
  const rows = readRows(n.id, n.rows!, readings, tag);
  const by = new Map<string, [number, number][]>();
  rows.forEach((row, i) => [...row].forEach((ch, x) => {
    if (ch === '-' || ch === 'c' || (isPrior(ch) && ch !== rd.carried)) return;
    if (!by.has(ch)) by.set(ch, []);
    by.get(ch)!.push([x, rows.length - 1 - i]);
  }));
  if (rd.spinCells.length) {
    if (by.has('U')) throw new Error(`${tag}-demos: ${n.id} draws U and has a spin board`);
    by.set('U', rd.spinCells);
  }
  const out: Group[] = [];
  for (const [ch, cells] of by) {
    if (ch === 'p') throw new Error(`${tag}-demos: ${n.id} has placeholder cells`);
    const piece = ch === 'U' ? 'T' : ch.toUpperCase();
    if (!PIECES.includes(piece)) throw new Error(`${tag}-demos: ${n.id} has letter ${ch}`);
    if (cells.length !== 4) throw new Error(`${tag}-demos: ${n.id} letter ${ch} has ${cells.length} cells`);
    const g: Group = { letter: ch, piece, spinSlot: ch === 'U' || ch === rd.spinLetter, cells };
    if (ch === rd.carried) g.carried = true;
    out.push(g);
  }
  const dealt = out.filter(g => !g.carried);
  if (new Set(dealt.map(g => g.piece)).size !== dealt.length) throw new Error(`${tag}-demos: ${n.id} repeats a piece`);
  return out;
}

/** The cells a diagram says are already there when its bag starts (`c`, and the prior-bag letters
 *  other than the one the hold carries in). */
function priorOf(n: RouteNode, carried: string | null = null): Set<string> {
  const rows = n.rows!, s = new Set<string>();
  rows.forEach((row, i) => [...row].forEach((ch, x) => {
    if (ch === 'c' || (isPrior(ch) && ch !== carried)) s.add(`${x},${rows.length - 1 - i}`);
  }));
  return s;
}

/** The U cells of a node's separate spin board (`spin_board`: はちみつ砲 draws its bag-2 boards with
 *  the TST slot empty and the T on a board of its own), [x, row from the bottom]; each must be empty
 *  on the node's own board. None when the node has no spin board. */
export function spinBoardCells(n: RouteNode, routes: Routes, tag = 'route'): [number, number][] {
  const id = (n as any).spin_board as string | undefined;
  if (!id) return [];
  const b = routes.nodes.find(x => x.id === id);
  if (!b?.rows) throw new Error(`${tag}-demos: ${n.id} spin board ${id} has no board`);
  if (b.rows.length !== n.rows!.length) throw new Error(`${tag}-demos: ${n.id} spin board ${id} is another height`);
  const out: [number, number][] = [];
  b.rows.forEach((row, i) => [...row].forEach((ch, x) => {
    if (ch !== 'U') return;
    if (n.rows![i]![x] !== '-') throw new Error(`${tag}-demos: ${n.id} spin cell ${x},${b.rows!.length - 1 - i} is drawn`);
    out.push([x, b.rows!.length - 1 - i]);
  }));
  return out;
}

// ── the planner ────────────────────────────────────────────────────────────────────────────────

/** Each field turns ONE rule off; each opener's demo test requires each to go red (or, for
 *  `no180`, states what it measured). */
export interface DemoMutants {
  noRowMap?: boolean;        // diagram rows used as engine rows, no clears accounted for
  noReach?: boolean;         // no search: the target's own rotation dropped straight down
  noSpinCheck?: boolean;     // accept a U lock whatever spin the engine credits
  ignoreConditions?: boolean; // the page's bag-2 order conditions not applied
  no180?: boolean;           // no 180 rotation edge
  noSwapDeal?: boolean;      // a `before` pair read in placement order: the swap slot never deals the T early
  noUBefore?: boolean;       // the profile's `uFiresBefore` ignored: the U always goes last
}

interface Placement { piece: string; cells: number[]; edges: Edge[]; spin: string | null; lines: number;
                      hold: boolean; letter: string; carried?: boolean }
interface BagPlan { node: string; queue: string; placed: string; unused: string; holds: number;
                    order_reading: string[]; condition: any; met: boolean | null; placements: Placement[] }
/** `held`: the piece in the hold box when the bag ends. `heldNext`: the hold box holds the NEXT bag's
 *  first piece (the bag's last placement came out of the hold when that piece arrived); which piece
 *  it is, the next bag decides. */
interface State { grid: Grid; placements: Placement[]; bags: BagPlan[]; held?: string | null; heldNext?: boolean }

const SPIN_OF = (s: string | null) => (s === 'normal' ? 2 : s === 'mini' ? 1 : 0);

function linesOf(g: Grid): number[] {
  const out: number[] = [];
  for (let y = 0; y < ROWS; y++) if (g[y]!.every(c => c != null)) out.push(y);
  return out;
}
export function applyCells(g: Grid, piece: string, cells: number[]): number[] {
  for (const c of cells) {
    const y = Math.floor(c / WIDTH), x = c % WIDTH;
    if (g[y]![x] != null) throw new Error('route-demos: overlap');
    g[y]![x] = piece;
  }
  const cl = linesOf(g);
  for (let k = cl.length - 1; k >= 0; k--) { g.splice(cl[k]!, 1); g.push(new Array(WIDTH).fill(null)); }
  return cl;
}

export interface BagSpec {
  node: RouteNode;
  /** expected line count of the U lock (TST 3 on a bag-2 board, TSD 2 where the slot is a TSD) */
  uLines: number | null;
  /** the U must be the bag's last placement (bag 2 and the snapshot routes) */
  uLast: boolean;
  /** pieces that come AFTER the U although `uLast` (the profile's `uFiresBefore`) */
  uBefore?: string[];
  /** this bag must end on a Perfect Clear */
  pc: boolean;
  /** pieces that must come before others in the queue (the page's condition), and the early piece */
  before: [string, string][];
  early: string | null;
  /** a piece drawn nowhere on the board that the bag holds instead of placing (迷走砲's bag1.z_hold) */
  holdPiece: string | null;
  /** the held piece arrives just before this one, and is held on arrival */
  holdBefore: string | null;
  /** the U cells of the node's separate spin board, if it has one */
  spinCells?: [number, number][];
  /** a lower-case letter the drawing puts in a T-spin slot (はちみつ砲's PC `t` in the TSD slot) */
  spinLetter?: string | null;
}

/** Plan one bag on top of `st`. Returns null when no order works. Search: DFS over placement orders
 *  in a fixed priority (the early piece, then the first piece of each `before` pair, then IOTSZJL,
 *  the U last), each step the first engine-reachable resting placement whose spin is the expected
 *  one. The queue is the placement order; the bag's unused piece goes last and is never placed. */
export function planBag(P: RouteProfile, eng: any, st: State, spec: BagSpec, mut: DemoMutants,
                        fail: string[]): State | null {
  const n = spec.node;
  const carriedIn = st.held && !st.heldNext ? st.held : null;
  const groups = groupsOf(n, demoProfile(P).pieceReadings, P.tag,
    { carried: carriedIn, spinLetter: spec.spinLetter ?? null, spinCells: spec.spinCells ?? [] });
  // the drawn prior cells must be the board the prefix left, bottom-aligned
  const prior = priorOf(n, carriedIn);
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < WIDTH; x++) {
    const drawn = prior.has(`${x},${y}`), there = st.grid[y]![x] != null;
    if (drawn !== there) {
      fail.push(`畫咗嘅舊格唔係上一層示範留低嘅盤面（第 ${x} 欄，由底數第 ${y} 行）`);
      return null;
    }
  }
  const prio = (g: Group) => {
    if (g.spinSlot) return 100;
    if (spec.early === g.piece) return -2;
    if (!mut.ignoreConditions && !g.carried && spec.before.some(([a]) => a === g.piece)) return -1;
    return PIECES.indexOf(g.piece);
  };
  groups.sort((a, b) => prio(a) - prio(b));
  const memo = new Map<string, Path[]>();
  const t0 = performance.now();
  // A `before` pair is an order of DEALING, and with the hold box full the queue below deals the
  // bag's last placement (the spin's T) at the swap slot, not at the end: where a carried piece comes
  // out of the hold, or first of all when every piece is placed. So the T counts as dealt once that
  // slot is reached (ガムシロ積み's 妥協 form: the T arrives before L and O and is held, the bag-1 L
  // comes out). The test is the queue builder's own rule, read early, never a second reading of it.
  const dealtPieces = groups.filter(g => !g.carried).map(g => g.piece);
  const holdSwaps = !!carriedIn || (!!st.heldNext && [...PIECES].every(p => dealtPieces.includes(p)));
  const dealtEarly = (o: Group, done: Placement[]) => !mut.noSwapDeal &&
    spec.uLast && !!o.spinSlot && holdSwaps && (!carriedIn || done.some(p => p.carried));
  // a piece the profile's `uFiresBefore` places after the U (empty for every other opener)
  const uBefore = mut.noUBefore ? [] : spec.uBefore ?? [];
  const afterU = (o: Group) => !o.spinSlot && !o.carried && uBefore.includes(o.piece);

  // the deepest point any order reached, and why each remaining piece could not go there: the
  // failure reason an unbuildable node is published with
  let deepest: { done: string; why: string[] } = { done: '', why: [] };
  const dfs = (grid: Grid, rowmap: number[], left: Group[], done: Placement[], lines: number): Placement[] | null => {
    if (performance.now() - t0 > 60_000) throw new Error(`${P.tag}-demos: ${n.id} search over 60 s`);
    if (!left.length) {
      if (spec.pc && grid.some(r => r.some(c => c != null))) return null;
      return done;
    }
    const why: string[] = [];
    for (const g of left) {
      const P = g.spinSlot ? 'T(U)' : g.piece;
      if (spec.uLast && g.spinSlot && left.some(o => o !== g && !afterU(o))) { why.push(`${P} 要最後先放`); continue; }
      // a piece the profile reads as placed after the U waits for it (SDPC Spin's C-Spin Z)
      if (afterU(g) && left.some(o => o.spinSlot)) { why.push(`${P} 要等 T(U)`); continue; }
      if (!mut.ignoreConditions && !g.carried) {
        // a piece whose `before` partner is still unplaced must wait (a carried piece was dealt earlier)
        const w = spec.before.find(([a, b]) => b === g.piece &&
          left.some(o => !o.carried && o.piece === a && !dealtEarly(o, done)));
        if (w) { why.push(`${P} 要等 ${w[0]}`); continue; }
      }
      const target: number[] = [];
      let ok = true;
      for (const [x, d] of g.cells) {
        const e = mut.noRowMap ? d : rowmap.indexOf(d);
        if (e < 0) { ok = false; break; }
        target.push(e * WIDTH + x);
      }
      if (!ok) { why.push(`${P} 畫喺一行已經消咗嘅行`); continue; }
      if (target.some(c => grid[Math.floor(c / WIDTH)]![c % WIDTH] != null)) { why.push(`${P} 嘅格已有嘢`); continue; }
      let shape = true;
      try { encodePlace(g.piece, target); } catch { shape = false; }
      if (!shape) { why.push(`${P} 中間隔住嘅行未消，未成形`); continue; }
      const mk = `${gridKey(grid)}|${g.piece}|${[...target].sort((a, b) => a - b)}`;
      let paths = memo.get(mk);
      if (!paths) {
        paths = mut.noReach ? straightDrop(eng, grid, g.piece, target) : reach(eng, grid, g.piece, target, mut);
        memo.set(mk, paths);
      }
      const wantSpin = (p: Path) => g.spinSlot ? (mut.noSpinCheck || p.spin === 'normal') : (g.piece !== 'T' || p.spin === null);
      const cand = paths.filter(wantSpin).sort((a, b) => a.edges.length - b.edges.length);
      if (!paths.length) { why.push(`${P} 由出生位行唔到去`); continue; }
      if (!cand.length) { why.push(`${P} 行到去但引擎判嘅 spin 唔啱`); continue; }
      const p = cand[0]!;   // one path per placement: a different path to the same cells changes nothing
      const ng = cloneGrid(grid);
      const cl = applyCells(ng, g.piece, p.cells);
      if (g.spinSlot && spec.uLines != null && !mut.noSpinCheck && cl.length !== spec.uLines) {
        why.push(`${P} 消 ${cl.length} 行唔係 ${spec.uLines} 行`); continue;
      }
      const nrm = mut.noRowMap ? rowmap : advanceRowmap(rowmap, cl);
      const r = dfs(ng, nrm, left.filter(o => o !== g),
        [...done, { piece: g.piece, cells: p.cells, edges: p.edges, spin: p.spin, lines: cl.length,
                    hold: false, letter: g.letter, ...(g.carried ? { carried: true } : {}) }], lines + cl.length);
      if (r) return r;
      why.push(`${P} 放咗之後其餘放唔晒`);
    }
    if (done.length >= deepest.done.length)
      deepest = { done: done.map(p => p.letter === 'U' ? 'T' : p.piece).join(''), why };
    return null;
  };
  const placements = dfs(cloneGrid(st.grid), initialRowmap(), groups, [], 0);
  if (!placements) {
    fail.push(`最遠放到 ${deepest.done || '（一粒都未放）'}；之後：${deepest.why.join('；')}`);
    return null;
  }

  // the queue: placement order, the unused piece last; a held piece goes just before the piece
  // whose arrival it is held at (迷走砲: the bag-1 Z before J, J>Z read the other way round)
  const placed = placements.map(p => p.piece).join('');
  let queue: string, unused: string, holds = 0;
  let heldOut: string | null = spec.holdPiece, heldNext = false;
  const reading: string[] = [];
  if (!st.held && !st.heldNext) {
    unused = [...PIECES].filter(p => !placed.includes(p) && p !== spec.holdPiece).join('');
    queue = placed + unused;
    if (spec.holdPiece) {
      const at = placed.indexOf(spec.holdBefore!);
      if (at < 0) throw new Error(`${P.tag}-demos: ${n.id} holds ${spec.holdPiece} before ${spec.holdBefore}, which is not placed`);
      queue = placed.slice(0, at) + spec.holdPiece + placed.slice(at) + unused;
      placements[at]!.hold = true;
      holds = 1;
    }
  } else {
    // THE HOLD BOX IS ALREADY OCCUPIED when this bag starts, and it can never be emptied again: a
    // piece comes out of it only by swapping another in. Either a piece of an earlier bag is carried
    // in (`carriedIn`, drawn upper-case and placed here), or the last bag's final placement came out
    // when THIS bag's first piece arrived (`heldNext`). The rule, one swap scheme for both: the held
    // piece comes out at its slot in the placement order, swapped for the piece this bag places LAST
    // (which therefore arrives at that slot), and that last piece comes out of the hold when the next
    // bag's first piece arrives. A `heldNext` piece the bag does not place is its unused piece, and
    // simply stays held.
    if (spec.holdPiece) throw new Error(`${P.tag}-demos: ${n.id} holds a piece with the hold box full`);
    const last = placements.length - 1;
    const dealtPlaced = placements.filter(p => !p.carried).map(p => p.piece).join('');
    let free = [...PIECES].filter(p => !dealtPlaced.includes(p));
    let head = '', swapAt = -1;
    if (carriedIn) {
      swapAt = placements.findIndex(p => p.carried);
      if (swapAt < 0) throw new Error(`${P.tag}-demos: ${n.id} carries ${carriedIn} in the hold and never places it`);
    } else if (free.length) {
      head = free[0]!; free = free.slice(1);   // the unused piece: dealt first, already in the hold
    } else {
      head = placements[0]!.piece; swapAt = 0; // every piece placed: the first one waited in the hold
    }
    unused = free.join('');
    let body = placements.map(p => p.piece);
    if (swapAt >= 0) {
      placements[swapAt]!.hold = true;
      placements[last]!.hold = true;
      holds = swapAt === last ? 1 : 2;
      // the last piece arrives at the swap slot; a carried piece was dealt in an earlier bag and a
      // `heldNext` one is `head`, so the last slot itself deals nothing
      if (swapAt !== last) body[swapAt] = placements[last]!.piece;
      body = body.slice(0, last);
      reading.push(`hold:${placements[swapAt]!.piece} out@${swapAt + 1}`);
      if (swapAt !== last) reading.push(`hold:${placements[last]!.piece} out@next`);
      heldOut = null; heldNext = true;
    } else { heldOut = head; reading.push(`held:${head}`); }
    queue = head + body.join('') + unused;
  }
  if ([...queue].sort().join('') !== [...PIECES].sort().join(''))
    throw new Error(`${P.tag}-demos: ${n.id} bag ${queue} is not a 7-bag`);
  const lead: string[] = [];
  if (spec.early) lead.push(`early:${spec.early}@${queue.indexOf(spec.early) + 1}`);
  for (const [a, b] of spec.before) lead.push(`before:${a}${b}`);
  if (spec.holdPiece) lead.push(`hold:${spec.holdPiece}@${queue.indexOf(spec.holdPiece) + 1}`);
  if (unused) reading.push(`unused:${unused}`);
  if (uBefore.length) reading.push(`u_before:${uBefore.join('')}`);
  reading.unshift(...lead);
  const met = n.condition && !n.condition.bag1 ? conditionHolds(n.condition, queue, '') : null;
  const grid = cloneGrid(st.grid);
  for (const p of placements) applyCells(grid, p.piece, p.cells);
  return {
    grid, placements: [...st.placements, ...placements],
    bags: [...st.bags, { node: n.id, queue, placed, unused, holds, order_reading: reading,
                          condition: n.condition ?? null, met, placements }],
    held: heldOut, heldNext,
  };
}

/** The `noReach` mutant: no search, the target's cells claimed reachable by a plain drop. */
function straightDrop(_eng: any, _grid: Grid, _piece: string, target: number[]): Path[] {
  return [{ edges: [], spin: null, cells: [...target].sort((a, b) => a - b) }];
}

// ── which nodes, in which chain ───────────────────────────────────────────────────────────────

/** The line count a bag-2 board's U fires, from the node's `spin`. */
const SPIN_LINES: Record<string, number> = { TSS: 1, TSD: 2, TST: 3 };

export function specFor(P: RouteProfile, n: RouteNode, routes: Routes): BagSpec {
  const cond = n.condition;
  const before: [string, string][] = cond?.all ? cond.all.map((c: any) => c.before) : [];
  if (n.bag === 1) {
    // a bag-1 board that draws a U (stick spin's TSS) fires it last, with the page's named spin
    const spin = (n as any).spin as string | undefined;
    const fires = n.rows!.some(r => r.includes('U'));
    if (fires && !(spin && spin in SPIN_LINES)) throw new Error(`${P.tag}-demos: ${n.id} draws a U and names no spin`);
    return { node: n, uLines: fires ? SPIN_LINES[spin!]! : null, uLast: fires, pc: false,
             ...demoProfile(P).bag1Spec(n, routes) };
  }
  // a list drawn in bag 2 (山岳積み2号's 4-line PCs) is a Perfect Clear pattern, not a bag-2 board
  if (n.bag === 2 && !n.list) {
    const spin = (n as any).spin as string | undefined;
    if (!spin || !(spin in SPIN_LINES)) throw new Error(`${P.tag}-demos: ${n.id} has no bag-2 spin`);
    const spinCells = spinBoardCells(n, routes, P.tag);
    return { node: n, uLines: SPIN_LINES[spin]!, uLast: true, pc: false, before,
             early: cond?.early ?? null, holdPiece: null, holdBefore: null, ...(spinCells.length ? { spinCells } : {}) };
  }
  // bag 3 and the bag after a snapshot (a snapshot board's `spin`, where the page names one, fixes
  // its U's line count: 山岳積み2号's TSD boards)
  const isPc = !!n.list;
  const sl = demoProfile(P).spinLetter?.(n, routes) ?? null;
  const named = (n as any).spin as string | undefined;
  const uLines = (n as any).has_tsd_slot ? 2 : sl ? sl.lines : named && named in SPIN_LINES ? SPIN_LINES[named]! : null;
  // a later board drawn with its slot empty and the T on a separate spin board (stick spin's TST,
  // Imperial Cross and STMB Cave fallbacks) fires into that board's U cells, as bag 2 does
  const spinCells = isPc ? [] : spinBoardCells(n, routes, P.tag);
  const uBefore = demoProfile(P).uFiresBefore?.[n.id];
  if (uBefore && isPc) throw new Error(`${P.tag}-demos: ${n.id} is a Perfect Clear pattern and names uFiresBefore`);
  return { node: n, uLines, uLast: !isPc, pc: isPc, ...(uBefore ? { uBefore } : {}),
           before: [], early: null, holdPiece: null, holdBefore: null, ...(sl ? { spinLetter: sl.letter } : {}),
           ...(spinCells.length ? { spinCells } : {}) };
}

/** Which nodes get a demo: every node with a drawn board, except the profile's unbuilt ones. */
export function demoNodes(P: RouteProfile, routes: Routes): RouteNode[] {
  const unbuilt = demoProfile(P).unbuilt;
  return routes.nodes.filter(n => n.rows && !(n.id in unbuilt));
}

/** A node's chain of demo nodes, root first: its own ancestors through `parent`, and for a bag-2
 *  board its `base` bag-1 board. A bag-1 board is a whole bag from an empty board, so its chain is
 *  itself (stick spin's `bag1.fire` names `bag1.left` as its parent: the same bag, less the T). */
export function chainOf(n: RouteNode, routes: Routes, tag = 'route', via: Record<string, string> = {}): RouteNode[] {
  const byId = new Map(routes.nodes.map(x => [x.id, x]));
  const out: RouteNode[] = [];
  let cur: RouteNode | undefined = n;
  while (cur) {
    out.unshift(cur);
    const base = (cur as any).base as string | undefined;
    // 迷走砲's `2.ideal.fire.stmb_example` hangs under the image-only `2.ideal.fire`; its board is 2.ideal's bag 3
    const up0: string | undefined = cur.bag === 1 ? undefined : cur.bag === 2 ? base : base ?? cur.parent ?? undefined;
    // a board no demo builds (an illustration of a group's shared state) stands for a demo node
    const up = up0 && up0 in via ? via[up0] : up0;
    cur = up ? byId.get(up) : undefined;
    if (cur && !cur.rows) throw new Error(`${tag}-demos: chain of ${n.id} reaches ${cur.id}, no board`);
  }
  return out;
}

// ── inputs and the replay ─────────────────────────────────────────────────────────────────────

const KEY_OF: Record<Exclude<Edge, 'D'>, string> = { L: 'moveLeft', R: 'moveRight', CW: 'rotateCW',
                                                     CCW: 'rotateCCW', '180': 'rotate180' };
type Input = [number, 'keydown' | 'keyup', string];

/** Placements → key events at fixed spacing. A tap is one frame down; a run of `D` edges is one
 *  soft drop held for exactly that many frames (one row a frame at g = 0, sdf 20); the lock is a
 *  hard drop from where the piece rests. */
export function inputsOf(placements: Placement[]): { inputs: Input[]; frames: number } {
  const out: Input[] = [];
  let f = FRAMES_PER_INPUT;
  const tap = (k: string) => { out.push([f, 'keydown', k], [f + 1, 'keyup', k]); f += FRAMES_PER_INPUT; };
  for (const p of placements) {
    if (p.hold) tap('hold');
    for (let i = 0; i < p.edges.length;) {
      const e = p.edges[i]!;
      if (e !== 'D') { tap(KEY_OF[e]); i++; continue; }
      let k = 0;
      while (p.edges[i] === 'D') { k++; i++; }
      out.push([f, 'keydown', 'softDrop'], [f + k, 'keyup', 'softDrop']);
      f += k + FRAMES_PER_INPUT;
    }
    tap('hardDrop');
  }
  return { inputs: out, frames: f };
}

/** Run a demo's queue and inputs on a fresh engine through `instrumentEngine`. Exported: the test
 *  re-runs every committed demo with it. */
export function runDemo(routes: any, seq: string, inputs: Input[], frames: number) {
  const eng = newEngine(routes);
  eng.queue.splice(0, eng.queue.length, ...[...seq.slice(1)].map(c => c.toLowerCase()));
  eng.initiatePiece(seq[0]!.toLowerCase());
  const rec = instrumentEngine(eng);
  const by = new Map<number, any[]>();
  for (const [fr, type, k] of inputs) {
    if (!by.has(fr)) by.set(fr, []);
    by.get(fr)!.push({ frame: fr, type, data: { key: k, subframe: 0 } });
  }
  for (let fr = 0; fr <= frames; fr++) eng.tick(by.get(fr) || []);
  return { rec, eng };
}

// ── build ──────────────────────────────────────────────────────────────────────────────────────

const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

export function build(P: RouteProfile, mut: DemoMutants = {}) {
  const DP = demoProfile(P);
  const routes = loadRoutes(P.routesPath);
  const eng = newEngine(routes);
  const cache = new Map<string, State | null>();
  const failures: Record<string, string> = {};
  const stateOf = (n: RouteNode): State | null => {
    if (cache.has(n.id)) return cache.get(n.id)!;
    const chain = chainOf(n, routes, P.tag, DP.chainVia);
    const parent: State | null = chain.length > 1 ? stateOf(chain[chain.length - 2]!) : { grid: emptyGrid(), placements: [], bags: [] };
    let st: State | null = null;
    if (parent) {
      const fail: string[] = [];
      st = planBag(P, eng, parent, specFor(P, n, routes), mut, fail);
      if (!st) failures[n.id] = fail.join('; ');
    } else failures[n.id] = `上一層 ${chain[chain.length - 2]!.id} 砌唔到`;
    cache.set(n.id, st);
    return st;
  };

  const demos: any[] = [];
  const unbuilt: { node: string; reason: string }[] =
    Object.entries(DP.unbuilt).map(([node, reason]) => ({ node, reason }));
  for (const n of demoNodes(P, routes)) {
    const st = stateOf(n);
    if (!st) { unbuilt.push({ node: n.id, reason: failures[n.id]! }); continue; }
    const chain = chainOf(n, routes, P.tag, DP.chainVia).map(x => x.id);
    // the queue: the bags, then whole padding bags, cut at the first whole bag that still shows
    // NEXT_SHOWN pieces at every lock (a scripted queue is honest only if a 7-bag could deal it)
    let seq = st.bags.map(b => b.queue).join('');
    const holdsUsed = st.placements.filter(p => p.hold).length;
    while (seq.length < st.placements.length + holdsUsed + NEXT_SHOWN) seq += PAD_BAG;
    const { inputs, frames } = inputsOf(st.placements);
    const { rec, eng: e2 } = runDemo(routes, seq, inputs, frames);

    // THE ARBITER: every lock where the plan put it, with the planned spin and lines
    if (rec.locks.length !== st.placements.length)
      throw new Error(`${P.tag}-demos: ${n.id} engine locked ${rec.locks.length}, planned ${st.placements.length}`);
    st.placements.forEach((p, i) => {
      const lk = rec.locks[i]!;
      const want = encodePlace(p.piece, p.cells);
      if (rec.engineQueue[i]!.piece !== p.piece || JSON.stringify(lk[1]) !== JSON.stringify(want)
          || lk[2] !== p.lines || lk[3] !== SPIN_OF(p.spin) || lk[5] !== (p.hold ? 1 : 0))
        throw new Error(`${P.tag}-demos: ${n.id} lock ${i} (${p.piece}) engine ${JSON.stringify(lk)} `
          + `${rec.engineQueue[i]!.piece}, planned place ${JSON.stringify(want)} lines ${p.lines} spin ${p.spin}`);
    });
    if (!rec.seq.startsWith(seq)) throw new Error(`${P.tag}-demos: ${n.id} engine dealt ${rec.seq}, not ${seq}`);
    assertRoundTrip(`demo ${n.id}`, seq, { locks: rec.locks, engineStates: rec.engineStates,
                                           engineQueue: rec.engineQueue } as any);
    const pc = e2.board.perfectClear;

    const events: any[] = [];
    let cum = 0;
    rec.locks.forEach((lk, i) => {
      cum += lk[2];
      if (lk[3] > 0 && lk[2] > 0)
        events.push({ lock: i, kind: (lk[3] === 1 ? 'mini ' : '') + (['', 'TSS', 'TSD', 'TST'][lk[2]] ?? `T${lk[2]}`),
                      spin: lk[3], lines: lk[2] });
      if (lk[2] > 0 && i === rec.locks.length - 1 && pc) events.push({ lock: i, kind: 'PC', lines: cum });
    });
    demos.push({
      node: n.id, parent: chain.length > 1 ? chain[chain.length - 2] : null, chain,
      also: ((routes as any).basic_form ?? []).filter((b: any) => b.same_as === n.id).map((b: any) => b.id),
      seq,
      letters: st.placements.map(p => p.letter).join(''),
      bags: st.bags.map(b => ({ node: b.node, queue: b.queue, placed: b.placed, unused: b.unused, holds: b.holds,
                                condition: b.condition, met: b.met, order_reading: b.order_reading })),
      inputs, frames,
      locks: rec.locks,
      events,
      piece_readings: DP.pieceReadings.filter(p => p.node === n.id),
      end: { lock: rec.locks.length - 1, check: specFor(P, n, routes).pc ? 'perfect_clear' : 'board' },
    });
  }
  return {
    schema: DP.schema,
    report_eligible: false,
    constructed: true,
    means: DP.means,
    not_eligible_because: DP.notEligible,
    caveat: DP.caveat,
    engine: { options: DEMO_OPTIONS, kickset: TL_DEFAULTS.kickset, allow180: TL_DEFAULTS.allow180,
              date: demoDate(routes).toISOString(), frames_per_input: FRAMES_PER_INPUT },
    inputs: {
      routes_md5: md5(readFileSync(P.routesPath)),
      planner_md5: md5Files(P.hashFiles.planner),
      emit_replay_md5: md5(readFileSync(`${import.meta.dir}/emit-replay.ts`)),
      classifier_md5: md5Files(P.hashFiles.classifier),
    },
    board: { width: WIDTH, rows: ROWS, visible_rows: VISIBLE_ROWS,
             coords: 'y-UP: row 0 is the bottom row', cell: 'yUp * width + x' },
    lock_fields: LOCK_FIELDS,
    shapes: SHAPES,
    demos,
    unbuilt,
  };
}

export { placeCells, queueStates };
export type { Lock };

/** One demo per line, metadata pretty-printed. */
export function serialise(out: any): string {
  const { demos, ...rest } = out;
  const head = JSON.stringify({ ...rest, demos: '\u0000' }, null, 1);
  return head.replace('"\\u0000"', '[\n' + demos.map((d: any) => '  ' + JSON.stringify(d)).join(',\n') + '\n ]') + '\n';
}
