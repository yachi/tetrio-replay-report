/**
 * 迷走砲 (Stray Cannon) CONSTRUCTED DEMOS: one replay per drawn route node of shiwehi.com's page,
 * built from an empty board by placing the pieces one at a time, and run through the vendored
 * Triangle engine.
 *
 *   bun pipeline/sim/emit-stray-cannon-demos.ts --out analysis/stray-cannon-demos.json
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
 * `emit-stray-cannon-facts.ts` builds exactly that frame from an engine run). The planner carries
 * the inverse, `rowmap` (from `emit-stray-cannon-facts.ts`, beside `composite()`): engine row e is
 * diagram row rowmap[e], and a piece is a candidate only while every row it is drawn on is still
 * on the board.
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
import { ROUTES_PATH, loadRoutes, conditionHolds, initialRowmap, advanceRowmap,
         type RouteNode, type Routes } from './emit-stray-cannon-facts.ts';

/** The page's two inconsistent colourings (`known_discrepancies` in meisou-routes.json): a cell
 *  group drawn in one piece's colour that can only be another piece. Cells are [x, row from the
 *  bottom]. ONE table. The corpus classifier does not apply it: no corpus PC matched either drawing under
 *  this reading (measured when it was written), so colour-matching them as drawn files nothing wrongly. */
export const PIECE_READINGS: { node: string; drawn: string; reads_as: string; cells: [number, number][];
                               reason: string }[] = [
  { node: '2.ideal.pc#16', drawn: 'z', reads_as: 'S', cells: [[1, 2], [2, 2]],
    reason: 'z 有 6 格、s 得 2 格：呢兩格同上面嘅 ss 隔住一行已消嘅行，合埋先係一粒 S' },
  { node: '2.i_early.pc#11', drawn: 'j', reads_as: 'L', cells: [[0, 4], [1, 4], [2, 4]],
    reason: 'j 有 7 格、l 得 1 格：呢三格同下面嘅 l 隔住兩行已消嘅行，合埋先係一粒 L' },
];
/** A node's rows with `PIECE_READINGS` applied. */
export function readRows(id: string, rows: string[]): string[] {
  const out = rows.map(r => [...r]);
  for (const pr of PIECE_READINGS.filter(p => p.node === id))
    for (const [x, d] of pr.cells) {
      const i = rows.length - 1 - d;
      if (out[i]![x] !== pr.drawn) throw new Error(`stray-cannon: ${id} reading cell ${x},${d} is not ${pr.drawn}`);
      out[i]![x] = pr.reads_as.toLowerCase();
    }
  return out.map(r => r.join(''));
}


const REPO = `${import.meta.dir}/../..`;
export const DEMOS_PATH = `${REPO}/analysis/stray-cannon-demos.json`;

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
const emptyGrid = (): Grid => Array.from({ length: ROWS }, () => new Array<string | null>(WIDTH).fill(null));
const cloneGrid = (g: Grid): Grid => g.map(r => [...r]);
const gridKey = (g: Grid) => g.map(r => r.map(c => c ?? '.').join('')).join('/');

/** A fresh demo engine (exported for the test's unit check of `reach`). */
export function newEngine(routes: any) {
  const opts = { ...TL_DEFAULTS, ...DEMO_OPTIONS };
  return createEngine(opts, 'demo', [{ gameid: 'demo', userid: 'demo', username: 'demo' }], demoDate(routes)) as any;
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

/** Every engine-legal resting placement of `piece` on `grid` whose cells are `target`, with the
 *  shortest path to each distinct arrival spin. `no180` (a mutant) drops the 180 edge. */
export function reach(eng: any, grid: Grid, piece: string, target: number[], opts: { no180?: boolean } = {})
  : Path[] {
  eng.board.state = grid.map(r => r.map(c => (c ? { mino: c.toLowerCase(), connections: 0 } : null)));
  eng.held = null;
  eng.initiatePiece(piece.toLowerCase(), true);
  const f = eng.falling;
  const start: St = { x: f.location[0], y: f.location[1], r: f.rotation, spin: null };
  const want = [...target].sort((a, b) => a - b).join(',');
  const prev = new Map<string, [string | null, Edge | null, St]>();
  prev.set(key(start), [null, null, start]);
  const queue: St[] = [start];
  const found: Path[] = [];
  const seenSpin = new Set<string>();
  const rot = (s: St, how: Edge): St | null => {
    f.location = [s.x, s.y]; f.rotation = s.r; f.totalRotations = 0; f.lockResets = 0; f.rotResets = 0;
    eng.lastSpin = null;
    const ok = how === 'CW' ? eng.rotateCW() : how === 'CCW' ? eng.rotateCCW() : eng.rotate180();
    if (!ok) return null;
    const sp = eng.lastSpin == null || eng.lastSpin === 'none' ? null : String(eng.lastSpin);
    return { x: f.location[0], y: f.location[1], r: f.rotation, spin: sp };
  };
  const edges: Edge[] = opts.no180 ? ['L', 'R', 'D', 'CW', 'CCW'] : ['L', 'R', 'D', 'CW', 'CCW', '180'];
  while (queue.length) {
    const s = queue.shift()!;
    const k = key(s);
    if (!fall1(eng, s) && cellsAt(eng, s).join(',') === want && !seenSpin.has(String(s.spin))) {
      seenSpin.add(String(s.spin));
      const es: Edge[] = [];
      for (let c = k; prev.get(c)![0] !== null; c = prev.get(c)![0]!) es.unshift(prev.get(c)![1]!);
      found.push({ edges: es, spin: s.spin, cells: cellsAt(eng, s) });
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
export interface Group { letter: string; piece: string; spinSlot: boolean; cells: [number, number][] }

/** Letters that are NOT this bag's pieces: `c` (an earlier bag), `Z` (the bag-1 Z, drawn in colour
 *  inside a bag-2 board), `-` empty. `U` is this bag's T, fired as a T-spin. */
function groupsOf(n: RouteNode): Group[] {
  // the page's two inconsistent colourings are read as the piece the cells have to be
  const rows = readRows(n.id, n.rows!);
  const by = new Map<string, [number, number][]>();
  rows.forEach((row, i) => [...row].forEach((ch, x) => {
    if (ch === '-' || ch === 'c' || ch === 'Z') return;
    if (!by.has(ch)) by.set(ch, []);
    by.get(ch)!.push([x, rows.length - 1 - i]);
  }));
  const out: Group[] = [];
  for (const [ch, cells] of by) {
    if (ch === 'p') throw new Error(`stray-cannon-demos: ${n.id} has placeholder cells`);
    const piece = ch === 'U' ? 'T' : ch.toUpperCase();
    if (!PIECES.includes(piece)) throw new Error(`stray-cannon-demos: ${n.id} has letter ${ch}`);
    if (cells.length !== 4) throw new Error(`stray-cannon-demos: ${n.id} letter ${ch} has ${cells.length} cells`);
    out.push({ letter: ch, piece, spinSlot: ch === 'U', cells });
  }
  if (new Set(out.map(g => g.piece)).size !== out.length) throw new Error(`stray-cannon-demos: ${n.id} repeats a piece`);
  return out;
}

/** The cells a diagram says are already there when its bag starts (`c`, and the upper-case bag-1 Z). */
function priorOf(n: RouteNode): Set<string> {
  const rows = n.rows!, s = new Set<string>();
  rows.forEach((row, i) => [...row].forEach((ch, x) => {
    if (ch === 'c' || ch === 'Z') s.add(`${x},${rows.length - 1 - i}`);
  }));
  return s;
}

// ── the planner ────────────────────────────────────────────────────────────────────────────────

/** Each field turns ONE rule off; `stray-cannon-demos.test.ts` requires each to go red (or, for
 *  `no180`, states what it measured). */
export interface DemoMutants {
  noRowMap?: boolean;        // diagram rows used as engine rows, no clears accounted for
  noReach?: boolean;         // no search: the target's own rotation dropped straight down
  noSpinCheck?: boolean;     // accept a U lock whatever spin the engine credits
  ignoreConditions?: boolean; // the page's bag-2 order conditions not applied
  no180?: boolean;           // no 180 rotation edge
}

interface Placement { piece: string; cells: number[]; edges: Edge[]; spin: string | null; lines: number;
                      hold: boolean; letter: string }
interface BagPlan { node: string; queue: string; placed: string; unused: string; holds: number;
                    order_reading: string[]; condition: any; met: boolean | null; placements: Placement[] }
interface State { grid: Grid; placements: Placement[]; bags: BagPlan[] }

const SPIN_OF = (s: string | null) => (s === 'normal' ? 2 : s === 'mini' ? 1 : 0);

function linesOf(g: Grid): number[] {
  const out: number[] = [];
  for (let y = 0; y < ROWS; y++) if (g[y]!.every(c => c != null)) out.push(y);
  return out;
}
function applyCells(g: Grid, piece: string, cells: number[]): number[] {
  for (const c of cells) {
    const y = Math.floor(c / WIDTH), x = c % WIDTH;
    if (g[y]![x] != null) throw new Error('stray-cannon-demos: overlap');
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
  /** this bag must end on a Perfect Clear */
  pc: boolean;
  /** pieces that must come before others in the queue (the page's condition), and the early piece */
  before: [string, string][];
  early: string | null;
  /** a piece drawn nowhere on the board that the bag holds instead of placing (bag1.z_hold) */
  holdPiece: string | null;
}

/** Plan one bag on top of `st`. Returns null when no order works. Search: DFS over placement orders
 *  in a fixed priority (the early piece, then the first piece of each `before` pair, then IOTSZJL,
 *  the U last), each step the first engine-reachable resting placement whose spin is the expected
 *  one. The queue is the placement order; the bag's unused piece goes last and is never placed. */
export function planBag(eng: any, st: State, spec: BagSpec, mut: DemoMutants, fail: string[]): State | null {
  const n = spec.node;
  const groups = groupsOf(n);
  // the drawn prior cells must be the board the prefix left, bottom-aligned
  const prior = priorOf(n);
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
    if (!mut.ignoreConditions && spec.before.some(([a]) => a === g.piece)) return -1;
    return PIECES.indexOf(g.piece);
  };
  groups.sort((a, b) => prio(a) - prio(b));
  const memo = new Map<string, Path[]>();
  const t0 = performance.now();

  // the deepest point any order reached, and why each remaining piece could not go there: the
  // failure reason an unbuildable node is published with
  let deepest: { done: string; why: string[] } = { done: '', why: [] };
  const dfs = (grid: Grid, rowmap: number[], left: Group[], done: Placement[], lines: number): Placement[] | null => {
    if (performance.now() - t0 > 60_000) throw new Error(`stray-cannon-demos: ${n.id} search over 60 s`);
    if (!left.length) {
      if (spec.pc && grid.some(r => r.some(c => c != null))) return null;
      return done;
    }
    const why: string[] = [];
    for (const g of left) {
      const P = g.spinSlot ? 'T(U)' : g.piece;
      if (spec.uLast && g.spinSlot && left.length > 1) { why.push(`${P} 要最後先放`); continue; }
      if (!mut.ignoreConditions) {
        // a piece whose `before` partner is still unplaced must wait
        const w = spec.before.find(([a, b]) => b === g.piece && left.some(o => o.piece === a));
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
                    hold: false, letter: g.letter }], lines + cl.length);
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
  // whose arrival it is held at (the bag-1 Z before J: J>Z read the other way round)
  const placed = placements.map(p => p.piece).join('');
  const unused = [...PIECES].filter(p => !placed.includes(p) && p !== spec.holdPiece).join('');
  let queue = placed + unused;
  let holds = 0;
  if (spec.holdPiece) {
    const at = placed.indexOf('J');
    queue = placed.slice(0, at) + spec.holdPiece + placed.slice(at) + unused;
    placements[at]!.hold = true;
    holds = 1;
  }
  if ([...queue].sort().join('') !== [...PIECES].sort().join(''))
    throw new Error(`stray-cannon-demos: ${n.id} bag ${queue} is not a 7-bag`);
  const reading: string[] = [];
  if (spec.early) reading.push(`early:${spec.early}@${queue.indexOf(spec.early) + 1}`);
  for (const [a, b] of spec.before) reading.push(`before:${a}${b}`);
  if (spec.holdPiece) reading.push(`hold:${spec.holdPiece}@${queue.indexOf(spec.holdPiece) + 1}`);
  if (unused) reading.push(`unused:${unused}`);
  const met = n.condition && !n.condition.bag1 ? conditionHolds(n.condition, queue, '') : null;
  const grid = cloneGrid(st.grid);
  for (const p of placements) applyCells(grid, p.piece, p.cells);
  return {
    grid, placements: [...st.placements, ...placements],
    bags: [...st.bags, { node: n.id, queue, placed, unused, holds, order_reading: reading,
                          condition: n.condition ?? null, met, placements }],
  };
}

/** The `noReach` mutant: no search, the target's cells claimed reachable by a plain drop. */
function straightDrop(_eng: any, _grid: Grid, _piece: string, target: number[]): Path[] {
  return [{ edges: [], spin: null, cells: [...target].sort((a, b) => a - b) }];
}

// ── which nodes, in which chain ───────────────────────────────────────────────────────────────

/** Nodes with a board that get no demo, and why. A node the planner cannot build must be named here
 *  with its reason (the test compares this with the artefact both ways), never dropped. */
export const DEMO_UNBUILT: Record<string, string> = {
  '2.ideal.fire.stmb_template': '「p」格冇指定填法；佢嘅例就係 stmb_example 嘅示範',
};

function specFor(n: RouteNode, routes: Routes): BagSpec {
  const byId = new Map(routes.nodes.map(x => [x.id, x]));
  const cond = n.condition;
  const before: [string, string][] = cond?.all ? cond.all.map((c: any) => c.before) : [];
  if (n.bag === 1) {
    const r = (routes as any).bag1;
    return { node: n, uLines: null, uLast: false, pc: false,
             before: n.id === 'bag1.z_right' ? [r.hold_free.before] : [],
             early: r.requires.early, holdPiece: n.id === 'bag1.z_hold' ? 'Z' : null };
  }
  if (n.bag === 2) return { node: n, uLines: 3, uLast: true, pc: false, before,
                            early: cond?.early ?? null, holdPiece: null };
  // bag 3 and the bag after a snapshot
  const isPc = !!n.list;
  void byId;
  return { node: n, uLines: (n as any).has_tsd_slot ? 2 : null, uLast: !isPc, pc: isPc, before: [],
           early: null, holdPiece: null };
}

/** Which nodes get a demo: every node with a drawn board, except `DEMO_UNBUILT`. */
export function demoNodes(routes: Routes): RouteNode[] {
  return routes.nodes.filter(n => n.rows && !(n.id in DEMO_UNBUILT));
}

/** A node's chain of demo nodes, root first: its own ancestors through `parent`, and for a bag-2
 *  board its `base` bag-1 board. */
export function chainOf(n: RouteNode, routes: Routes): RouteNode[] {
  const byId = new Map(routes.nodes.map(x => [x.id, x]));
  const out: RouteNode[] = [];
  let cur: RouteNode | undefined = n;
  while (cur) {
    out.unshift(cur);
    const base = (cur as any).base as string | undefined;
    // `2.ideal.fire.stmb_example` hangs under the image-only `2.ideal.fire`; its board is 2.ideal's bag 3
    const up: string | undefined = cur.bag === 2 ? base : base ?? cur.parent ?? undefined;
    cur = up ? byId.get(up) : undefined;
    if (cur && !cur.rows) throw new Error(`stray-cannon-demos: chain of ${n.id} reaches ${cur.id}, no board`);
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

export function build(mut: DemoMutants = {}) {
  const routes = loadRoutes();
  const eng = newEngine(routes);
  const cache = new Map<string, State | null>();
  const failures: Record<string, string> = {};
  const stateOf = (n: RouteNode): State | null => {
    if (cache.has(n.id)) return cache.get(n.id)!;
    const chain = chainOf(n, routes);
    const parent = chain.length > 1 ? stateOf(chain[chain.length - 2]!) : { grid: emptyGrid(), placements: [], bags: [] };
    let st: State | null = null;
    if (parent) {
      const fail: string[] = [];
      st = planBag(eng, parent, specFor(n, routes), mut, fail);
      if (!st) failures[n.id] = fail.join('; ');
    } else failures[n.id] = `上一層 ${chain[chain.length - 2]!.id} 砌唔到`;
    cache.set(n.id, st);
    return st;
  };

  const demos: any[] = [];
  const unbuilt: { node: string; reason: string }[] =
    Object.entries(DEMO_UNBUILT).map(([node, reason]) => ({ node, reason }));
  for (const n of demoNodes(routes)) {
    const st = stateOf(n);
    if (!st) { unbuilt.push({ node: n.id, reason: failures[n.id]! }); continue; }
    const chain = chainOf(n, routes).map(x => x.id);
    // the queue: the bags, then whole padding bags, cut at the first whole bag that still shows
    // NEXT_SHOWN pieces at every lock (a scripted queue is honest only if a 7-bag could deal it)
    let seq = st.bags.map(b => b.queue).join('');
    const holdsUsed = st.placements.filter(p => p.hold).length;
    while (seq.length < st.placements.length + holdsUsed + NEXT_SHOWN) seq += PAD_BAG;
    const { inputs, frames } = inputsOf(st.placements);
    const { rec, eng: e2 } = runDemo(routes, seq, inputs, frames);

    // THE ARBITER: every lock where the plan put it, with the planned spin and lines
    if (rec.locks.length !== st.placements.length)
      throw new Error(`stray-cannon-demos: ${n.id} engine locked ${rec.locks.length}, planned ${st.placements.length}`);
    st.placements.forEach((p, i) => {
      const lk = rec.locks[i]!;
      const want = encodePlace(p.piece, p.cells);
      if (rec.engineQueue[i]!.piece !== p.piece || JSON.stringify(lk[1]) !== JSON.stringify(want)
          || lk[2] !== p.lines || lk[3] !== SPIN_OF(p.spin) || lk[5] !== (p.hold ? 1 : 0))
        throw new Error(`stray-cannon-demos: ${n.id} lock ${i} (${p.piece}) engine ${JSON.stringify(lk)} `
          + `${rec.engineQueue[i]!.piece}, planned place ${JSON.stringify(want)} lines ${p.lines} spin ${p.spin}`);
    });
    if (!rec.seq.startsWith(seq)) throw new Error(`stray-cannon-demos: ${n.id} engine dealt ${rec.seq}, not ${seq}`);
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
      piece_readings: PIECE_READINGS.filter(p => p.node === n.id),
      end: { lock: rec.locks.length - 1, check: specFor(n, routes).pc ? 'perfect_clear' : 'board' },
    });
  }
  return {
    schema: 'stray-cannon-demos/1',
    report_eligible: false,
    constructed: true,
    means: 'Constructed replays, one per drawn node of shiwehi.com\'s 迷走砲 route page: our own piece queue '
         + 'and key inputs, run from an empty board through the vendored Triangle engine, ending on the '
         + 'page\'s drawn board. Not a game anyone played and not corpus data.',
    not_eligible_because: ['not a game anyone played; not corpus data',
                           'one engine, no second implementation of the boards'],
    caveat: {
      order: 'Where the page does not fix the piece order, the order here is ours: the early piece first, '
           + 'the first piece of each of the page\'s before-pairs next, then IOTSZJL, the T into a drawn U last '
           + 'where the drawing shows U empty. order_reading records it per bag.',
      hold: 'Only bag1.z_hold uses hold: its Z is held when it arrives, just before J. No other demo holds.',
      early: 'The page gives no threshold for "early"; the demo puts the early piece first in its bag.',
      colour_readings: 'Two Perfect Clear drawings colour one piece in another piece\'s colour; the demo builds '
                     + 'the piece the cells have to be (piece_readings).',
      spin: 'Every T-spin kind and line count is the engine\'s verdict on the replayed inputs.',
    },
    engine: { options: DEMO_OPTIONS, kickset: TL_DEFAULTS.kickset, allow180: TL_DEFAULTS.allow180,
              date: demoDate(routes).toISOString(), frames_per_input: FRAMES_PER_INPUT },
    inputs: {
      routes_md5: md5(readFileSync(ROUTES_PATH)),
      planner_md5: md5(readFileSync(import.meta.path)),
      emit_replay_md5: md5(readFileSync(`${import.meta.dir}/emit-replay.ts`)),
      classifier_md5: md5(readFileSync(`${import.meta.dir}/emit-stray-cannon-facts.ts`)),
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
