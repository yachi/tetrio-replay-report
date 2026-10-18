/**
 * The shared CONSTRUCTED-DEMO planner for the mid-game technique pages (STSD, …): for each of the
 * profile's chains, one replay from an EMPTY board that builds the page's terrain out of real pieces,
 * adds the page's own pieces, fires the technique's stood T into the window the corpus matcher reads,
 * and — where the page draws one — fires the follow-up T-spin it promises.
 *
 *   bun pipeline/sim/emit-technique-demos.ts --technique stsd --out analysis/stsd-demos.json
 *
 * NOT CORPUS DATA. Nobody played these games: the queue, the hold and the key inputs are OURS. The
 * artefact says `report_eligible: false` and `constructed: true`, and nothing that draws from it
 * carries a claim id, a ✓ or a `data-claim`.
 *
 * WHY THIS IS NOT `route-demos.ts`. A route demo plans one drawn bag on the board the previous bag
 * left, from an empty board up. A technique page draws its shape on a partial stack whose grey cells
 * are no piece in particular, so the planner first has to CHOOSE pieces for them (an exact cover of
 * the terrain by tetrominoes, every one reachable from spawn, no line cleared). This file imports the
 * route planner's engine-move search (`reach`), its input scheduler (`inputsOf`) and its replay
 * (`runDemo`) and edits none of them: no route artefact's hash line moves because a technique exists.
 *
 * THE BASE IS BUILT, NEVER SEEDED. Every decoder in this repo (`decodeTimeline`, the page's
 * `replay_section.decode_boards`, the inlined player) starts from an empty board, and the only thing
 * a timeline can insert is a one-hole garbage row. So the terrain's grey cells are pieces we chose,
 * and the page says so beside every demo. A terrain is published as unbuilt with the planner's
 * reason when its cell count is ODD (every lock adds 4 cells and every line clear removes 10, so a
 * board reachable from empty always holds an even count — a proof, not a planner limit), when it is
 * even but not a multiple of four (reachable only through line clears, which THIS planner never makes
 * — a limit of the planner, worded as one), or when no order of reachable pieces covers it.
 *
 * THE DEALING, one scheme for every chain. The stood T and the follow-up T are two consecutive
 * T-spins, so two T's have to arrive close together, and a 7-bag deals one per bag. So: bag 1's T is
 * dealt LAST in bag 1 and held on arrival; the first piece of bag 2 is placed in its stead; when bag
 * 2's T arrives it is swapped for the held one, which is fired as the stood T; the follow-up T waits
 * in the hold until the next piece arrives and is swapped out. Hence at least seven pieces before
 * the stood T (bag 1's six other pieces, then bag 2's first), and every piece between and after comes
 * from bag 2 once each. A chain with fewer is unbuilt, with that reason.
 *
 * THE ENGINE IS THE ARBITER; THE PLANNER ONLY PROPOSES. The whole script is replayed on a fresh
 * engine through `instrumentEngine` (via `runDemo`), and `build()` throws unless every lock lands on
 * the planned cells with the planned spin, line count and hold flag, and the timeline round-trips.
 */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { reach, inputsOf, runDemo, newEngine, DEMO_OPTIONS, FRAMES_PER_INPUT, PIECES, demoDate,
         type Path } from './route-demos.ts';
import { assertRoundTrip, encodePlace, placeCells, decodeTimeline, queueStates, SHAPES, LOCK_FIELDS, NEXT_SHOWN,
         WIDTH, ROWS, VISIBLE_ROWS, type Lock } from './emit-replay.ts';
import { TL_DEFAULTS } from './oracle-source.ts';
import { md5Files } from './route-facts.ts';
import { loadTranscription, prepare, windowMatch, type Variant, type Cell } from './technique-facts.ts';
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';
import type { TechniqueProfile } from './technique-profile.ts';

const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');
/** Padding bags after the last bag a demo uses: whole bags in this fixed order (route-demos.ts's). */
const PAD_BAG = 'IJLOSTZ';
/** one letter per lock in a demo's `roles`: terrain (ours), page piece, stood T, filler (ours), follow-up T */
export const ROLE_CODE = { base: 'b', page: 'p', stsd: 'S', fill: 'f', followup: 'F' } as const;
const SPIN_OF = (s: string | null) => (s === 'normal' ? 2 : s === 'mini' ? 1 : 0);

type Grid = (string | null)[][];
const emptyGrid = (): Grid => Array.from({ length: ROWS }, () => new Array<string | null>(WIDTH).fill(null));
const cloneGrid = (g: Grid): Grid => g.map(r => [...r]);
const gridKey = (g: Grid) => g.map(r => r.map(c => c ?? '.').join('')).join('/');

export interface DemoMutants {
  /** the planner trusts a straight drop to every target, and the spin it wants for a T (the engine
   *  arbiter must then refuse) */
  noReach?: boolean;
  /** the stood and the follow-up T accepted whatever spin the engine credits (the test's spin check
   *  must then fail) */
  noSpinCheck?: boolean;
  /** the terrain's pieces dropped from the input script after planning (the base taken as given):
   *  the engine starts from an empty board, so the arbiter must refuse */
  baseSeeded?: boolean;
  /** the 180 rotation dropped from the move search (a control: no demo needs one) */
  no180?: boolean;
}

/** A placement, in the shape `route-demos.ts`'s `inputsOf` reads. `role` is ours. */
export interface Placement { piece: string; cells: number[]; edges: Path['edges']; spin: string | null;
                             lines: number; hold: boolean; letter: string;
                             role: 'base' | 'page' | 'stsd' | 'fill' | 'followup' }

// ── drawings, bottom-aligned on the engine's floor ───────────────────────────────────────────────

/** A drawing's cells as y-UP engine cell indices → the drawn letter (empty letters dropped). */
export function drawnCells(rows: string[], emptyLetters: string): Map<number, string> {
  const out = new Map<number, string>();
  const h = rows.length;
  rows.forEach((row, i) => [...row].forEach((ch, x) => {
    if (ch !== '-' && !emptyLetters.includes(ch)) out.set((h - 1 - i) * WIDTH + x, ch);
  }));
  return out;
}

/** Does the y-UP `grid` show `rows` (bottom-aligned)? `exact`: every cell, at every height, as drawn
 *  (`c` or an upper-case letter any filled cell, a lower-case piece letter that piece, empty empty).
 *  `window`: inside the columns `cols` the same; outside them only drawn-filled ⇒ filled (the
 *  page's after board assumes the right side stacked up, our reading — see the artefact's rules). */
export function shows(grid: (string | null)[][], rows: string[], emptyLetters: string,
                      mode: 'exact' | 'window' = 'exact', cols: [number, number] = [0, WIDTH - 1]): boolean {
  const h = rows.length;
  for (let y = 0; y < grid.length; y++) for (let x = 0; x < WIDTH; x++) {
    const ch = y < h ? rows[h - 1 - y]![x]! : '-';
    const v = grid[y]![x] ?? null;
    const strict = mode === 'exact' || (x >= cols[0] && x <= cols[1]);
    if (ch === '-' || emptyLetters.includes(ch)) {
      if (strict && v !== null) return false;
    } else if (v === null) return false;
    else if (strict && /^[a-z]$/.test(ch) && ch !== 'c' && v !== ch.toUpperCase()) return false;
  }
  return true;
}

// ── tetromino placements inside a set of cells ──────────────────────────────────────────────────

function placementsIn(allowed: Set<number>, kind: string, mustCover: number): number[][] {
  const out: number[][] = [];
  for (const shape of SHAPES[kind]!) {
    for (const [ox, oy] of shape) {
      // anchor so that this shape cell lands on `mustCover`
      const ax = (mustCover % WIDTH) - ox, ay = Math.floor(mustCover / WIDTH) - oy;
      const cells = shape.map(([dx, dy]) => [ax + dx, ay + dy] as [number, number]);
      if (cells.some(([x, y]) => x < 0 || x >= WIDTH || y < 0 || y >= ROWS)) continue;
      const idx = cells.map(([x, y]) => y * WIDTH + x).sort((a, b) => a - b);
      if (idx.every(c => allowed.has(c)) && !out.some(o => o.join() === idx.join())) out.push(idx);
    }
  }
  return out;
}

function applyCells(g: Grid, piece: string, cells: number[]): number[] {
  for (const c of cells) {
    const y = Math.floor(c / WIDTH), x = c % WIDTH;
    if (g[y]![x] != null) throw new Error('technique-demos: overlap');
    g[y]![x] = piece;
  }
  const cl: number[] = [];
  for (let y = 0; y < ROWS; y++) if (g[y]!.every(c => c != null)) cl.push(y);
  for (let k = cl.length - 1; k >= 0; k--) { g.splice(cl[k]!, 1); g.push(new Array(WIDTH).fill(null)); }
  return cl;
}

/** The 40-row board top-first ('.' empty), and cells as rows top-first: the frame `windowMatch` reads. */
const topFirst = (g: Grid) => [...g].reverse().map(r => r.map(c => c ?? '.').join(''));
const asCells = (cells: number[]): Cell[] =>
  cells.map(c => ({ row: ROWS - 1 - Math.floor(c / WIDTH), col: c % WIDTH }));

// ── the plan ─────────────────────────────────────────────────────────────────────────────────────

interface Plan { placements: Placement[]; baseLocks: number; preT: number; stood: number; follow: number | null;
                 offset: { dr: number; dc: number } }

function planChain(DP: TechniqueDemoProfile, tr: any, v: Variant, chain: { node: string; terrain: string },
                   eng: any, mut: DemoMutants): { plan: Plan | null; reason: string } {
  const byId = new Map<string, any>(tr.nodes.map((n: any) => [n.id, n]));
  const empties: string = tr.empty_letters ?? '';
  const build = byId.get(chain.node), terrain = byId.get(chain.terrain);
  if (!build || !terrain) throw new Error(`${DP.tag}-demos: chain ${chain.node} names a board the transcription lacks`);
  const terr = drawnCells(terrain.rows, empties);
  const drawn = drawnCells(build.rows, empties);
  // the page's own pieces: the build board's lower-case letters, one group per letter
  const page: { piece: string; cells: number[] }[] = [];
  for (const letter of [...new Set([...drawn.values()].filter(ch => /^[a-z]$/.test(ch) && ch !== 'c'))].sort())
    page.push({ piece: letter.toUpperCase(), cells: [...drawn].filter(([, ch]) => ch === letter).map(([c]) => c).sort((a, b) => a - b) });
  for (const p of page) {
    if (p.cells.length !== 4) return { plan: null, reason: `頁面嘅 ${p.piece} 畫咗 ${p.cells.length} 格，唔係一粒` };
    try { encodePlace(p.piece, p.cells); } catch { return { plan: null, reason: `頁面嘅 ${p.piece} 唔係 ${p.piece} 嘅形` }; }
  }
  // the build board less its page pieces must be the terrain, cell for cell
  const rest = [...drawn.keys()].filter(c => !page.some(p => p.cells.includes(c))).sort((a, b) => a - b);
  if (rest.join() !== [...terr.keys()].sort((a, b) => a - b).join())
    throw new Error(`${DP.tag}-demos: ${chain.node} less its page pieces is not ${chain.terrain}`);
  // parity: each lock adds 4 cells, each line clear removes 10, so an empty board only ever reaches an
  // EVEN count. Odd is a proof; even-but-not-4n needs a clear, which this planner never makes.
  if (terr.size % 2) return { plan: null,
    reason: `地形有 ${terr.size} 格，係單數：每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出` };
  if (terr.size % 4) return { plan: null,
    reason: `地形有 ${terr.size} 格，唔係 4 嘅倍數：要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）` };
  const nBase = terr.size / 4, preT = nBase + page.length;
  if (preT < 7) return { plan: null, reason: `T 之前得 ${preT} 粒；我哋嘅發牌（第一巡嘅 T 留喺 hold）要最少 7 粒` };

  const memo = new Map<string, Path[]>();
  const paths = (grid: Grid, piece: string, target: number[]): Path[] => {
    const k = `${gridKey(grid)}|${piece}|${target.join()}`;
    let p = memo.get(k);
    if (!p) {
      // the `noReach` mutant: a straight drop to every target, credited the spin the plan wants
      p = mut.noReach ? [{ edges: [], spin: piece === 'T' ? 'normal' : null, cells: [...target] }]
                      : reach(eng, grid, piece, target, { no180: mut.no180 });
      memo.set(k, p);
    }
    return p;
  };
  const t0 = performance.now();
  let deepest = { done: '', why: [] as string[] };
  const prep = prepare(tr, v)[0]!;   // demos are as drawn; the mirror is the page's 左右反轉
  const winCols: [number, number] = v.window.cols;

  /** the kinds bag `idx` may deal: bag 1 is placements 0..5 then its T; bag 2 the rest */
  const kindOk = (done: Placement[], kind: string) => {
    if (kind === 'T') return false;
    const idx = done.length;
    const b1 = done.slice(0, 6).map(p => p.piece), b2 = done.slice(6).map(p => p.piece);
    return idx < 6 ? !b1.includes(kind) : !b2.includes(kind);
  };

  const tail = (grid: Grid, done: Placement[]): Plan | null => {
    // ── the stood T: the one T placement on this board at which the corpus window matches ──
    const board = topFirst(grid);
    const fits: { cells: number[]; off: { dr: number; dc: number } }[] = [];
    const empty = new Set<number>();
    for (let c = 0; c < ROWS * WIDTH; c++) if (grid[Math.floor(c / WIDTH)]![c % WIDTH] == null) empty.add(c);
    const seen = new Set<string>();
    for (const c of empty) for (const cells of placementsIn(empty, 'T', c)) {
      if (seen.has(cells.join())) continue;
      seen.add(cells.join());
      const m = windowMatch(board, asCells(cells), prep);
      if (m) fits.push({ cells, off: m });
    }
    if (fits.length !== 1) { deepest = { done: done.map(p => p.piece).join(''), why: [`個窗口對到 ${fits.length} 個 T 位，唔係啱啱一個`] }; return null; }
    const st = fits[0]!;
    const sp = paths(grid, 'T', st.cells).filter(p => mut.noSpinCheck || p.spin === 'normal').sort((a, b) => a.edges.length - b.edges.length);
    if (!sp.length) { deepest = { done: done.map(p => p.piece).join(''), why: ['企直嘅 T 行唔到入去（或者引擎唔判 T-spin）'] }; return null; }
    const g1 = cloneGrid(grid);
    const cl = applyCells(g1, 'T', sp[0]!.cells);
    if (!mut.noSpinCheck && cl.length !== v.lines) { deepest = { done: done.map(p => p.piece).join(''), why: [`企直嘅 T 消 ${cl.length} 行，唔係 ${v.lines} 行`] }; return null; }
    const stood: Placement = { piece: 'T', cells: sp[0]!.cells, edges: sp[0]!.edges, spin: sp[0]!.spin,
                               lines: cl.length, hold: true, letter: 'T', role: 'stsd' };
    const after1 = [...done, stood];
    // ── the follow-up slot, carried through the stood T's clear (top-first rows, as the matcher does) ──
    const clTop = cl.map(y => ROWS - 1 - y);
    const slot = prep.followup.map(x => ({ r: x.r + st.off.dr, c: x.c + st.off.dc }))
      .map(x => ({ r: x.r + clTop.filter(y => y > x.r).length, c: x.c }))
      .map(x => (ROWS - 1 - x.r) * WIDTH + x.c).sort((a, b) => a - b);
    if (slot.some(c => g1[Math.floor(c / WIDTH)]![c % WIDTH] != null)) {
      deepest = { done: after1.map(p => p.piece).join(''), why: ['第二下 TSD 嘅位已經有嘢'] }; return null;
    }
    const slotRows = [...new Set(slot.map(c => Math.floor(c / WIDTH)))];
    const missing = new Set<number>();
    for (const y of slotRows) for (let x = 0; x < WIDTH; x++) {
      const c = y * WIDTH + x;
      if (!slot.includes(c) && g1[y]![x] == null) missing.add(c);
    }
    const c0 = winCols[0] + st.off.dc, c1 = winCols[1] + st.off.dc;
    const lowY = Math.min(...slotRows);
    const fill = (g: Grid, d: Placement[], miss: Set<number>): Plan | null => {
      if (performance.now() - t0 > 120_000) throw new Error(`${DP.tag}-demos: ${chain.node} search over 120 s`);
      if (!miss.size) {
        // the bag-2 piece whose arrival swaps the follow-up T out of the hold must exist
        const used2 = d.slice(6).filter(p => p.role !== 'stsd').map(p => p.piece);
        if ([...PIECES].filter(k => k !== 'T' && !used2.includes(k)).length < 1) return null;
        const fp = paths(g, 'T', slot).filter(p => mut.noSpinCheck || p.spin === 'normal').sort((a, b) => a.edges.length - b.edges.length);
        if (!fp.length) { deepest = { done: d.map(p => p.piece).join(''), why: ['第二粒 T 行唔到入個 TSD 位（或者引擎唔判 T-spin）'] }; return null; }
        const g2 = cloneGrid(g);
        const cl2 = applyCells(g2, 'T', fp[0]!.cells);
        if (!mut.noSpinCheck && cl2.length !== v.followup.lines) {
          deepest = { done: d.map(p => p.piece).join(''), why: [`第二粒 T 消 ${cl2.length} 行，唔係 ${v.followup.lines} 行`] }; return null;
        }
        const fu: Placement = { piece: 'T', cells: fp[0]!.cells, edges: fp[0]!.edges, spin: fp[0]!.spin,
                                lines: cl2.length, hold: true, letter: 't', role: 'followup' };
        return { placements: [...d, fu], baseLocks: nBase, preT: done.length,
                 stood: done.length, follow: d.length, offset: st.off };
      }
      const low = [...miss].sort((a, b) => Math.floor(a / WIDTH) - Math.floor(b / WIDTH) || a - b)[0]!;
      const allowed = new Set<number>(miss);
      for (let c = 0; c < ROWS * WIDTH; c++) {
        const y = Math.floor(c / WIDTH), x = c % WIDTH;
        if (g[y]![x] == null && !slot.includes(c) && y >= lowY && (x < c0 || x > c1)) allowed.add(c);
      }
      for (const kind of PIECES) {
        const used2 = d.slice(6).filter(p => p.role !== 'stsd').map(p => p.piece);
        if (kind === 'T' || used2.includes(kind)) continue;
        for (const cells of placementsIn(allowed, kind, low)) {
          const ps = paths(g, kind, cells);
          if (!ps.length) continue;
          const p = [...ps].sort((a, b) => a.edges.length - b.edges.length)[0]!;
          const ng = cloneGrid(g);
          if (applyCells(ng, kind, p.cells).length) continue;
          const nm = new Set([...miss].filter(c => !cells.includes(c)));
          const r = fill(ng, [...d, { piece: kind, cells: p.cells, edges: p.edges, spin: p.spin, lines: 0,
                                      hold: false, letter: 'f', role: 'fill' }], nm);
          if (r) return r;
        }
      }
      if (d.length >= deepest.done.length) deepest = { done: d.map(p => p.piece).join(''), why: ['填唔到第二下 TSD 要嘅行'] };
      return null;
    };
    return fill(g1, after1, missing);
  };

  // ── the terrain: every exact cover of its grey cells by non-T pieces, each kind at most twice (once
  // a bag), enumerated lowest cell first; then, per cover, every placement ORDER the engine can play
  // (any remaining piece that is reachable and resting now), the page's pieces after the terrain so the
  // terrain stands on its own at one lock ──
  type Piece = { piece: string; cells: number[] };
  const covers: Piece[][] = [];
  const cover = (left: Set<number>, used: Record<string, number>, out: Piece[]) => {
    if (covers.length >= 5000) return;
    if (!left.size) { covers.push(out); return; }
    const low = [...left].sort((a, b) => Math.floor(a / WIDTH) - Math.floor(b / WIDTH) || a - b)[0]!;
    for (const kind of PIECES) {
      if (kind === 'T' || (used[kind] ?? 0) >= 2) continue;
      // the page's pieces come out of the same two bags
      if ((used[kind] ?? 0) + page.filter(p => p.piece === kind).length >= 2) continue;
      for (const cells of placementsIn(left, kind, low))
        cover(new Set([...left].filter(c => !cells.includes(c))), { ...used, [kind]: (used[kind] ?? 0) + 1 },
              [...out, { piece: kind, cells }]);
    }
  };
  cover(new Set(terr.keys()), {}, []);
  if (!covers.length) return { plan: null, reason: `地形冇一個由非 T 方塊（每款最多兩粒）砌成嘅鋪法` };

  // a state that failed once fails again: the same grid, the same kinds dealt from each bag, the
  // same pieces left to place
  const failed = new Set<string>();
  const stateKey = (grid: Grid, done: Placement[], left: Piece[]) => `${gridKey(grid)}|${done.length}|`
    + `${done.slice(0, 6).map(p => p.piece).sort().join('')}|${done.slice(6).map(p => p.piece).sort().join('')}|`
    + left.map(q => `${q.piece}${q.cells.join('.')}`).sort().join(',');
  const dfs = (grid: Grid, done: Placement[], baseLeft: Piece[], pageLeft: Piece[]): Plan | null => {
    if (performance.now() - t0 > 120_000) throw new Error(`${DP.tag}-demos: ${chain.node} search over 120 s`);
    const sk = stateKey(grid, done, [...baseLeft, ...pageLeft]);
    if (failed.has(sk)) return null;
    const r0 = dfs1(grid, done, baseLeft, pageLeft);
    if (!r0) failed.add(sk);
    return r0;
  };
  const dfs1 = (grid: Grid, done: Placement[], baseLeft: Piece[], pageLeft: Piece[]): Plan | null => {
    if (!baseLeft.length && !pageLeft.length) return tail(grid, done);
    const why: string[] = [];
    const cands = baseLeft.length ? baseLeft.map(q => ({ ...q, role: 'base' as const }))
                                  : pageLeft.map(q => ({ ...q, role: 'page' as const }));
    for (const cd of cands) {
      if (!kindOk(done, cd.piece)) { why.push(`${cd.piece} 呢一巡已經出過`); continue; }
      const ps = paths(grid, cd.piece, cd.cells);
      if (!ps.length) { why.push(`${cd.piece} 由出生位行唔到去`); continue; }
      const p = [...ps].sort((a, b) => a.edges.length - b.edges.length)[0]!;
      const ng = cloneGrid(grid);
      if (applyCells(ng, cd.piece, p.cells).length) { why.push(`${cd.piece} 會消行`); continue; }
      const r = dfs(ng, [...done, { piece: cd.piece, cells: p.cells, edges: p.edges, spin: p.spin, lines: 0,
                                    hold: done.length === 6, letter: cd.role === 'base' ? 'c' : cd.piece.toLowerCase(),
                                    role: cd.role }],
                    cd.role === 'base' ? baseLeft.filter(q => q.cells !== cd.cells) : baseLeft,
                    cd.role === 'page' ? pageLeft.filter(q => q.cells !== cd.cells) : pageLeft);
      if (r) return r;
    }
    if (done.length >= deepest.done.length && why.length) deepest = { done: done.map(p => p.piece).join(''), why: [...new Set(why)] };
    return null;
  };

  for (const cv of covers) {
    const found = dfs(emptyGrid(), [], cv, page);
    if (found) return { plan: found, reason: '' };
  }
  return { plan: null, reason: `${covers.length} 個鋪法都唔得；最遠放到 ${deepest.done || '（一粒都未放）'}；之後：${deepest.why.join('；')}` };
}

/** The dealt queue for a plan: bag 1 = placements 0..5 then its T (held on arrival); bag 2 = the
 *  piece placed in the T's stead, the pieces before the stood T, bag 2's T (swapped for the held one),
 *  the fillers, the piece whose arrival swaps the follow-up T out, the rest unused. */
function queueOf(pl: Placement[], tag: string) {
  const preT = pl.findIndex(p => p.role === 'stsd');
  const b1 = pl.slice(0, 6).map(p => p.piece).join('') + 'T';
  const before = pl.slice(6, preT).map(p => p.piece).join('');
  const fills = pl.filter(p => p.role === 'fill').map(p => p.piece).join('');
  const used = before + 'T' + fills;
  const free = [...PIECES].filter(k => !used.includes(k));
  const hasFollow = pl.some(p => p.role === 'followup');
  const swap = hasFollow ? free.shift()! : '';
  const b2 = before + 'T' + fills + swap + free.join('');
  for (const b of [b1, b2])
    if ([...b].sort().join('') !== [...PIECES].sort().join('')) throw new Error(`${tag}-demos: bag ${b} is not a 7-bag`);
  return { bags: [b1, b2], swap, unused: free.join('') };
}

export function build(P: TechniqueProfile, DP: TechniqueDemoProfile, mut: DemoMutants = {}) {
  const tr = loadTranscription(DP.transcriptionPath);
  const v: Variant = tr.variants.find((x: Variant) => x.id === DP.variant);
  if (!v) throw new Error(`${DP.tag}-demos: no variant ${DP.variant}`);
  const empties: string = tr.empty_letters ?? '';
  const byId = new Map<string, any>(tr.nodes.map((n: any) => [n.id, n]));
  const eng = newEngine(tr);
  const demos: any[] = [];
  const unbuilt: { node: string; reason: string }[] =
    Object.entries(DP.unbuilt).map(([node, reason]) => ({ node, reason }));
  for (const chain of DP.chains) {
    const { plan, reason } = planChain(DP, tr, v, chain, eng, mut);
    if (!plan) { unbuilt.push({ node: chain.node, reason }, { node: chain.terrain, reason: `${chain.node} 砌唔到：${reason}` }); continue; }
    const pl = plan.placements;
    const q = queueOf(pl, DP.tag);
    let seq = q.bags.join('');
    const holds = pl.filter(p => p.hold).length;
    while (seq.length < pl.length + holds + NEXT_SHOWN) seq += PAD_BAG;
    // the `baseSeeded` mutant plays the script without the terrain's pieces
    const script = mut.baseSeeded ? pl.filter(p => p.role !== 'base') : pl;
    const { inputs, frames } = inputsOf(script as any);
    const { rec } = runDemo(tr, seq, inputs, frames);
    // THE ARBITER
    pl.forEach((p, i) => {
      const lk = rec.locks[i];
      if (!lk) throw new Error(`${DP.tag}-demos: ${chain.node} engine locked ${rec.locks.length}, planned ${pl.length}`);
      const want = encodePlace(p.piece, p.cells);
      if (rec.engineQueue[i]!.piece !== p.piece || JSON.stringify(lk[1]) !== JSON.stringify(want)
          || lk[2] !== p.lines || lk[3] !== SPIN_OF(p.spin) || lk[5] !== (p.hold ? 1 : 0))
        throw new Error(`${DP.tag}-demos: ${chain.node} lock ${i} (${p.piece}) engine ${JSON.stringify(lk)} `
          + `${rec.engineQueue[i]!.piece}, planned place ${JSON.stringify(want)} lines ${p.lines} spin ${p.spin}`);
    });
    if (rec.locks.length !== pl.length)
      throw new Error(`${DP.tag}-demos: ${chain.node} engine locked ${rec.locks.length}, planned ${pl.length}`);
    if (!rec.seq.startsWith(seq)) throw new Error(`${DP.tag}-demos: ${chain.node} engine dealt ${rec.seq}, not ${seq}`);
    assertRoundTrip(`demo ${chain.node}`, seq, { locks: rec.locks, engineStates: rec.engineStates,
                                                 engineQueue: rec.engineQueue } as any);
    const events = rec.locks.flatMap((lk: Lock, i: number) => lk[3] > 0 && lk[2] > 0
      ? [{ lock: i, kind: (lk[3] === 1 ? 'mini ' : '') + (['', 'TSS', 'TSD', 'TST'][lk[2]] ?? `T${lk[2]}`), spin: lk[3], lines: lk[2] }]
      : []);
    // what the demo stands on, checked here against the planner's grid and again, independently, by
    // the test (decodeTimeline) and the page (replay_section.decode_boards)
    const reaches = reachesOf(tr, chain, plan);
    const bad = reachProblems(tr, v, { seq, locks: rec.locks, reaches, offset: plan.offset });
    if (bad.length) throw new Error(`${DP.tag}-demos: ${chain.node}: ${bad.join('; ')}`);
    demos.push({
      node: chain.node, terrain: chain.terrain, variant: v.id,
      seq, roles: pl.map(p => ROLE_CODE[p.role]).join(''),
      bags: q.bags, swap: q.swap, unused: q.unused,
      base_locks: plan.baseLocks, stood_lock: plan.stood, followup_lock: plan.follow,
      offset: plan.offset, reaches,
      inputs, frames, locks: rec.locks, events,
    });
  }
  // every drawn board: one demo stands on it, or it is unbuilt with a reason
  const reached = new Set(demos.flatMap(d => d.reaches.map((r: any) => r.node)));
  for (const n of tr.nodes) {
    const k = (reached.has(n.id) ? 1 : 0) + unbuilt.filter(u => u.node === n.id).length;
    if (k !== 1) throw new Error(`${DP.tag}-demos: ${n.id} is reached by a demo and/or unbuilt ${k} times, want exactly once`);
  }
  return {
    schema: DP.artefact.schema,
    report_eligible: false,
    constructed: true,
    technique: DP.key,
    means: DP.artefact.means,
    not_eligible_because: DP.artefact.notEligible,
    caveat: DP.artefact.caveat,
    rules: DP.rules(),
    engine: { options: DEMO_OPTIONS, kickset: TL_DEFAULTS.kickset, allow180: TL_DEFAULTS.allow180,
              date: demoDate(tr).toISOString(), frames_per_input: FRAMES_PER_INPUT },
    inputs: {
      transcription_md5: md5(readFileSync(DP.transcriptionPath)),
      planner_md5: md5Files(DP.hashFiles.planner),
      emit_replay_md5: md5(readFileSync(`${import.meta.dir}/emit-replay.ts`)),
      classifier_md5: md5Files(P.hashFiles.classifier),
    },
    board: { width: WIDTH, rows: ROWS, visible_rows: VISIBLE_ROWS,
             coords: 'y-UP: row 0 is the bottom row', cell: 'yUp * width + x' },
    lock_fields: LOCK_FIELDS,
    shapes: SHAPES,
    demos,
    unbuilt: unbuilt.sort((a, b) => a.node < b.node ? -1 : 1),
  };
}

/** The boards a demo stands on, each with the lock after which it stands and how it is compared:
 *  `board` exact (the terrain after the last base lock; the build board, and any board the gate
 *  checked to be the same occupancy, before the stood T); `spin` the stood T's lock is that spin
 *  board's T; `after` the board before the follow-up, compared exactly inside the variant's window
 *  columns and filled-where-drawn outside them, the follow-up's lock being the drawn slot. */
function reachesOf(tr: any, chain: { node: string; terrain: string }, plan: Plan) {
  const nodes: any[] = tr.nodes;
  const out: { node: string; lock: number; check: 'board' | 'spin' | 'after' }[] = [];
  if (plan.baseLocks > 0) out.push({ node: chain.terrain, lock: plan.baseLocks - 1, check: 'board' });
  const same = [chain.node, ...nodes.filter(n => n.id === chain.node && n.same_occupancy_as).map(n => n.same_occupancy_as)];
  for (const id of same) out.push({ node: id, lock: plan.preT - 1, check: 'board' });
  for (const s of nodes.filter(n => n.kind === 'spin' && same.includes(n.spin_of) && !n.spin_piece)) {
    out.push({ node: s.id, lock: plan.stood, check: 'spin' });
    for (const a of nodes.filter(n => n.kind === 'after' && n.after_of === s.id))
      if (plan.follow !== null) out.push({ node: a.id, lock: plan.follow, check: 'after' });
  }
  return out;
}

/** A drawing's cells in one letter set, bottom-aligned, as y-UP cell indices. */
const lettersAt = (rows: string[], letters: string) => {
  const h = rows.length, out: number[] = [];
  rows.forEach((row, i) => [...row].forEach((ch, x) => { if (letters.includes(ch)) out.push((h - 1 - i) * WIDTH + x); }));
  return out.sort((a, b) => a - b);
};

/** Every `reaches` entry of one demo, checked on its own decoded timeline (`decodeTimeline`, from an
 *  empty board). Exported: the test runs it on every committed demo; the page's Python check is a
 *  second implementation of the same rules. */
export function reachProblems(tr: any, v: Variant, d: { seq: string; locks: Lock[]; reaches: any[];
                                                        offset: { dr: number; dc: number } }): string[] {
  const byId = new Map<string, any>(tr.nodes.map((n: any) => [n.id, n]));
  const empties: string = tr.empty_letters ?? '';
  const boards: (string | null)[][][] = [];
  try { decodeTimeline(d.seq, d.locks, (b, i) => { boards[i] = b.map(r => [...r]); }); }
  catch (e) { return [`does not decode: ${(e as Error).message}`]; }
  const q = queueStates(d.seq, d.locks);
  const cellsOf = (i: number) => [...placeCells(q[i]!.piece, d.locks[i]![1])].sort((a, b) => a - b);
  const bad: string[] = [];
  for (const r of d.reaches) {
    const n = byId.get(r.node);
    if (!n) { bad.push(`${r.node}: no such board`); continue; }
    const lk = d.locks[r.lock];
    if (!lk) { bad.push(`${r.node}: no lock ${r.lock}`); continue; }
    if (r.check === 'board') {
      if (!shows(boards[r.lock]!, n.rows, empties)) bad.push(`${r.node}: the board after lock ${r.lock + 1} is not the drawing`);
    } else if (r.check === 'spin') {
      const base = byId.get(n.spin_of);
      if (q[r.lock]!.piece !== 'T' || lk[3] !== 2 || lk[2] !== n.lines) bad.push(`${r.node}: lock ${r.lock + 1} is not a full ${n.spin}`);
      else if (cellsOf(r.lock).join() !== lettersAt(n.rows, 'Tt').join()) bad.push(`${r.node}: lock ${r.lock + 1} is not the drawn T`);
      else if (!shows(boards[r.lock - 1]!, base.rows, empties)) bad.push(`${r.node}: the board before lock ${r.lock + 1} is not ${base.id}`);
    } else if (r.check === 'after') {
      const cols: [number, number] = [v.window.cols[0] + d.offset.dc, v.window.cols[1] + d.offset.dc];
      const h = n.rows.length;
      const slot = v.followup.t_cells_after.map(([row, col]: [number, number]) => (h - 1 - row) * WIDTH + col)
        .sort((a: number, b: number) => a - b);
      if (q[r.lock]!.piece !== 'T' || lk[3] !== 2 || lk[2] !== v.followup.lines) bad.push(`${r.node}: lock ${r.lock + 1} is not a full ${v.followup.spin}`);
      else if (cellsOf(r.lock).join() !== slot.join()) bad.push(`${r.node}: lock ${r.lock + 1} is not the drawn follow-up slot`);
      else if (!shows(boards[r.lock - 1]!, n.rows, empties, 'window', cols)) bad.push(`${r.node}: the board before lock ${r.lock + 1} does not show the drawing`);
    } else bad.push(`${r.node}: unknown check ${r.check}`);
  }
  return bad;
}

/** One demo per line, metadata pretty-printed. */
export function serialise(out: any): string {
  const { demos, ...rest } = out;
  const head = JSON.stringify({ ...rest, demos: '\u0000' }, null, 1);
  return head.replace('"\\u0000"', '[\n' + demos.map((d: any) => '  ' + JSON.stringify(d)).join(',\n') + '\n ]') + '\n';
}
