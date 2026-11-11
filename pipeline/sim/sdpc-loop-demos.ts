/**
 * The SDPC LOOP, CONSTRUCTED AND RUN THROUGH THE ENGINE: every combination of stick spin's SD Perfect
 * Clear (or もっちパフェ) and とんぼ's DPC catalogue that closes the loop, built from an empty board and
 * replayed piece by piece.
 *
 *   bun pipeline/sim/emit-sdpc-loop-demos.ts --out analysis/sdpc-loop-demos.json
 *
 * NOT CORPUS DATA, and not the video: nobody played these games. The queue and the key inputs are OURS.
 * The artefact says `report_eligible: false` and `constructed: true`; nothing drawn from it carries a
 * claim id, a ✓ or a `data-claim`.
 *
 * THE TWO HALVES.
 *   1. The SD half is stick spin's committed demo of a `2.sd.pc#N` / `2.mochi.pc#N` node
 *      (`analysis/stickspin-demos.json`): bag 1, bag 2 and six pieces of bag 3, 20 locks, no hold,
 *      ending on a Perfect Clear. Bag 3's seventh piece is dealt LAST and never placed: that is the
 *      leftover the DPC starts from.
 *   2. The DPC half is planned here from `pipeline/openers/dpc-setups.json`, as drawn and mirrored
 *      (J↔L, S↔Z): the leftover is placed FIRST on the empty board (it is the falling piece the moment
 *      the SD Perfect Clear locks, and nothing is held), then bag 4's six other pieces in whatever
 *      order the engine can play them, then bag 4's T into a full T-spin Double, then bag 5's seven
 *      pieces into the drawn 4-line Perfect Clear. 1 + 7 + 7 = 15 locks.
 *   20 + 15 = 35 = five whole bags, so the board is empty at a bag boundary and the loop can repeat.
 *
 * A combination is a pair (SD node, DPC Perfect Clear in one hand) whose leftover letters agree. A
 * mirrored loop is the mirror of an unmirrored one, so the SD half is taken as drawn only; that covers
 * every loop up to a mirror, and the artefact says so.
 *
 * THE ENGINE IS THE ARBITER. Each DPC plan is first proved on its own (a fresh engine, the leftover on
 * an empty board); then every combination is replayed WHOLE — the SD demo's own inputs followed by the
 * DPC inputs — on one fresh engine, and `build()` throws unless the first 20 locks equal the SD demo's
 * committed locks, the next 15 land where the plan put them with the planned spin and lines, the
 * dealt queue is five whole 7-bags, the board is empty after lock 19 and after lock 34, and the hold is
 * never used. A DPC that the planner cannot build is published with the planner's measured reason.
 */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { assertRoundTrip, encodePlace, SHAPES, LOCK_FIELDS, NEXT_SHOWN, WIDTH, ROWS, VISIBLE_ROWS }
  from './emit-replay.ts';
import { newEngine, reach, applyCells, emptyGrid, cloneGrid, inputsOf, runDemo, demoDate, DEMO_OPTIONS,
         FRAMES_PER_INPUT, type Edge } from './route-demos.ts';
import { TL_DEFAULTS } from './oracle-source.ts';
import { initialRowmap, advanceRowmap } from './route-facts.ts';

const ROOT = `${import.meta.dir}/../..`;
export const PATHS = {
  stickspinRoutes: `${ROOT}/pipeline/openers/stickspin-routes.json`,
  stickspinDemos: `${ROOT}/analysis/stickspin-demos.json`,
  dpcSetups: `${ROOT}/pipeline/openers/dpc-setups.json`,
  loopRead: `${ROOT}/pipeline/openers/sdpc-loop.json`,
};
const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

type Grid = (string | null)[][];
interface Placement { piece: string; cells: number[]; edges: Edge[]; spin: string | null; lines: number;
                      hold: boolean; letter: string }
interface Piece { letter: string; cells: [number, number][] }   // [x, yUp] in its drawing

const MIRROR: Record<string, string> = { J: 'L', L: 'J', S: 'Z', Z: 'S' };
const mirrorRows = (rows: string[]) => rows.map(r => [...r].reverse().map(c => MIRROR[c] ?? c).join(''));
/** A drawing's rows, top row first, with every all-empty row above the content dropped. */
const content = (rows: string[]) => { const i = rows.findIndex(r => /[^.]/.test(r)); return rows.slice(i); };
const SPIN_OF = (s: string | null) => (s === 'normal' ? 2 : s === 'mini' ? 1 : 0);

/** Every way to cut one letter's cells into whole tetrominoes of that letter (exact cover). */
function tilings(letter: string, cells: [number, number][]): [number, number][][][] {
  const key = (c: [number, number]) => `${c[0]},${c[1]}`;
  const left = new Set(cells.map(key));
  const shapes = SHAPES[letter]!;
  const out: [number, number][][][] = [];
  const go = (acc: [number, number][][]) => {
    if (left.size === 0) { out.push(acc.map(p => p.map(c => [...c] as [number, number]))); return; }
    // the lowest-then-leftmost free cell must be some piece's lowest-then-leftmost cell
    const first = [...left].map(s => s.split(',').map(Number) as [number, number])
      .sort((a, b) => a[1] - b[1] || a[0] - b[0])[0]!;
    for (const sh of shapes) {
      const [ax, ay] = sh[0]!;
      const pc = sh.map(([x, y]) => [x - ax + first[0], y - ay + first[1]] as [number, number]);
      if (!pc.every(c => left.has(key(c)))) continue;
      pc.forEach(c => left.delete(key(c)));
      go([...acc, pc]);
      pc.forEach(c => left.add(key(c)));
    }
  };
  go([]);
  return out;
}

/** A drawing (top row first) → its pieces, y-up from the drawing's bottom row. `G` is not a piece. */
function piecesOf(rows: string[], what: string): Piece[] {
  const by = new Map<string, [number, number][]>();
  const n = rows.length;
  rows.forEach((r, i) => [...r].forEach((c, x) => {
    if (c === '.' || c === 'G') return;
    if (!by.has(c)) by.set(c, []);
    by.get(c)!.push([x, n - 1 - i]);
  }));
  const out: Piece[] = [];
  for (const [letter, cells] of [...by].sort()) {
    // one piece of a letter is taken as drawn: a PC drawing is a kept-rows composite, so a piece placed
    // after a clear spans the rows it fell through (the row map places it); two of a letter are cut
    if (cells.length === 4) { out.push({ letter, cells }); continue; }
    const t = tilings(letter, cells);
    if (t.length !== 1) throw new Error(`sdpc-loop: ${what} ${letter} cuts into whole pieces ${t.length} ways`);
    for (const p of t[0]!) out.push({ letter, cells: p });
  }
  return out;
}

const gridCell = (x: number, y: number) => y * WIDTH + x;

// ── one DPC: setup + TSD + PC, from the leftover on an empty board ─────────────────────────────

export interface DpcPlan { placements: Placement[]; queue4: string; queue5: string; leftover: string;
                           first: number[] }

/** Place `pieces` (y in the drawing's own frame, mapped through `rowmap`) in some order on `g`. DFS
 *  over orders; each step the first engine-reachable resting placement, a T only as a full spin. */
function dfsBag(eng: any, g: Grid, rowmap: number[], pieces: Piece[], fixedFirst: number | null,
                lastT: { lines: number } | null, wantEmpty: boolean, fail: string[],
                before: [string, string] | null = null):
  { placements: Placement[]; grid: Grid; rowmap: number[] } | null {
  const n = pieces.length;
  let best = 0, bestWhy = '';
  const go = (grid: Grid, rm: number[], used: number, acc: Placement[]): any => {
    if (used === (1 << n) - 1) {
      if (wantEmpty && grid.some(r => r.some(c => c != null))) { bestWhy = 'board not empty at the end'; return null; }
      return { placements: acc, grid, rowmap: rm };
    }
    const order = acc.length === 0 && fixedFirst != null ? [fixedFirst] : [...Array(n).keys()];
    for (const i of order) {
      if (used & (1 << i)) continue;
      const p = pieces[i]!;
      const isLastT = lastT && p.letter === 'T';
      // the page's order, read as: in the bag after the leftover, A is dealt before B
      if (before && fixedFirst != null && acc.length > 0 && p.letter === before[1]
          && !acc.slice(1).some(a => a.letter === before[0])) continue;
      if (isLastT && used !== ((1 << n) - 1) - (1 << i)) continue;   // the TSD's T goes last
      const target: number[] = [];
      let ok = true;
      for (const [x, y] of p.cells) {
        const e = rm.indexOf(y);
        if (e < 0) { ok = false; break; }
        if (grid[e]![x] != null) { ok = false; break; }
        target.push(gridCell(x, e));
      }
      if (!ok) continue;
      const paths = reach(eng, grid, p.letter, target);
      const path = isLastT ? paths.find(q => q.spin === 'normal') : (paths.find(q => q.spin == null) ?? paths[0]);
      if (!path) {
        if (acc.length + 1 > best) { best = acc.length + 1; bestWhy = `${p.letter} unreachable after ${acc.map(a => a.letter).join('') || '(nothing)'}`
          + (isLastT && paths.length ? ` (only as ${paths.map(q => q.spin ?? 'no spin').join('/')})` : ''); }
        continue;
      }
      const g2 = cloneGrid(grid);
      const cleared = applyCells(g2, p.letter, path.cells);
      if (isLastT && cleared.length !== lastT!.lines) {
        if (acc.length + 1 > best) { best = acc.length + 1; bestWhy = `T clears ${cleared.length}, not ${lastT!.lines}`; }
        continue;
      }
      const pl: Placement = { piece: p.letter, cells: path.cells, edges: path.edges, spin: path.spin,
                              lines: cleared.length, hold: false, letter: p.letter };
      const r = go(g2, advanceRowmap(rm, cleared), used | (1 << i), [...acc, pl]);
      if (r) return r;
    }
    return null;
  };
  const r = go(g, rowmap, 0, []);
  if (!r) fail.push(bestWhy || 'no order');
  return r;
}

export function planDpc(eng: any, setupRows: string[], tCells: [number, number][], pcRows: string[],
                        fail: string[], before: [string, string] | null = null): DpcPlan | null {
  const sRows = content(setupRows);   // the setup drawing, bottom row = engine row 0
  const setup = piecesOf(sRows, 'setup');
  const counts = new Map<string, number>();
  setup.forEach(p => counts.set(p.letter, (counts.get(p.letter) ?? 0) + 1));
  const twice = [...counts].filter(([, k]) => k === 2).map(([l]) => l);
  if (setup.length !== 7 || twice.length !== 1 || counts.has('T'))
    throw new Error(`sdpc-loop: setup is not one leftover + IOSZJL (${[...counts]})`);
  const leftover = twice[0]!;
  const h = sRows.length;
  const T: Piece = { letter: 'T', cells: tCells.map(([r, c]) => [c, h - 1 - r] as [number, number]) };
  const pc = piecesOf(content(pcRows), 'pc');
  // the setup pieces and the T, the leftover first (either component may be bag 3's)
  const idx = setup.map((p, i) => [p, i] as const).filter(([p]) => p.letter === leftover).map(([, i]) => i);
  const reasons: string[] = [];
  for (const firstIx of idx) {
    const f1: string[] = [];
    const s = dfsBag(eng, emptyGrid(), initialRowmap(ROWS), [...setup, T], firstIx, { lines: 2 }, false, f1, before);
    if (!s) { reasons.push(`leftover = the ${leftover} at ${JSON.stringify(setup[firstIx]!.cells)}: setup ${f1.join('')}`); continue; }
    // the PC frame: the residue after the TSD is the PC drawing's G cells, bottom-aligned
    const pRows = content(pcRows);
    const ph = pRows.length;
    for (let y = 0; y < ROWS; y++) for (let x = 0; x < WIDTH; x++) {
      const drawn = y < ph ? pRows[ph - 1 - y]![x] === 'G' : false;
      if ((s.grid[y]![x] != null) !== drawn) throw new Error(`sdpc-loop: residue after the TSD is not the PC drawing's G at (${x},${y})`);
    }
    const f2: string[] = [];
    const p = dfsBag(eng, s.grid, initialRowmap(ROWS), pc, null, null, true, f2);
    if (!p) { reasons.push(`setup built, PC ${f2.join('')}`); continue; }
    const placements = [...s.placements, ...p.placements];
    return { placements, leftover, first: setup[firstIx]!.cells.map(([x, y]) => gridCell(x, y)),
             queue4: s.placements.slice(1).map(q => q.letter).join(''),
             queue5: p.placements.map(q => q.letter).join('') };
  }
  fail.push(reasons.join('; '));
  return null;
}

// ── the whole loop ─────────────────────────────────────────────────────────────────────────────

const PAD_BAG = 'IJLOSTZ';
const isBag = (s: string) => s.length === 7 && [...s].sort().join('') === 'IJLOSTZ';

export function build() {
  const routes = JSON.parse(readFileSync(PATHS.stickspinRoutes, 'utf8'));
  const sdDemos = JSON.parse(readFileSync(PATHS.stickspinDemos, 'utf8'));
  const dpc = JSON.parse(readFileSync(PATHS.dpcSetups, 'utf8'));
  const boardOf = new Map<string, any>(dpc.boards.map((b: any) => [b.id, b]));
  const eng = newEngine(routes);

  // the DPC halves, every Perfect Clear of every setup in both hands; identical drawings once
  const halves: any[] = [];
  const unbuilt: any[] = [];
  const seen = new Map<string, string>();
  for (const s of dpc.setups) {
    for (const pcId of s.pcs) {
      for (const mirrored of [false, true]) {
        let sRows: string[] = boardOf.get(s.id).rows, pRows: string[] = boardOf.get(pcId).rows;
        let t: [number, number][] = s.t_cells.map(([r, c]: number[]) => [r, c]);
        if (mirrored) { sRows = mirrorRows(sRows); pRows = mirrorRows(pRows); t = t.map(([r, c]) => [r, WIDTH - 1 - c]); }
        const id = `${pcId}${mirrored ? '.mirror' : ''}`;
        const k = JSON.stringify([sRows, pRows]);
        if (seen.has(k)) { unbuilt.push({ dpc: id, same_as: seen.get(k), reason: 'same drawings, letter for letter' }); continue; }
        seen.set(k, id);
        // the page's order condition (「O>Z」), mirrored with the board; tried first, then dropped
        const m = /([IOTSZJL])>([IOTSZJL])/.exec(s.heading[1] ?? '');
        const cond = m ? [m[1]!, m[2]!].map(c => (mirrored ? MIRROR[c] ?? c : c)) as [string, string] : null;
        const fail: string[] = [];
        let plan = cond ? planDpc(eng, sRows, t, pRows, fail, cond) : null;
        const met = cond ? plan != null : null;
        if (!plan) plan = planDpc(eng, sRows, t, pRows, fail);
        const head = { dpc: id, setup: s.id, pc: pcId, mirrored, page: s.page, heading: s.heading,
                       condition: cond ? `${cond[0]}>${cond[1]}` : null };
        if (!plan) { unbuilt.push({ ...head, reason: fail.join('; ') }); continue; }
        // the DPC half proved on its own: a fresh engine, the leftover on an empty board
        const dIn = inputsOf(plan.placements);
        let dseq = plan.leftover + plan.queue4 + plan.queue5;
        while (dseq.length < 15 + NEXT_SHOWN) dseq += PAD_BAG;
        const { rec } = runDemo(routes, dseq, dIn.inputs as any, dIn.frames);
        plan.placements.forEach((p, i) => {
          const lk = rec.locks[i]!;
          if (JSON.stringify(lk[1]) !== JSON.stringify(encodePlace(p.piece, p.cells)) || lk[2] !== p.lines
              || lk[3] !== SPIN_OF(p.spin) || lk[5] !== 0)
            throw new Error(`sdpc-loop: ${id} alone, lock ${i} engine ${JSON.stringify(lk)}`);
        });
        halves.push({ ...head, condition_met: met, plan, inputs: dIn.inputs, frames: dIn.frames });
      }
    }
  }

  // the SD halves: every committed SD / もっち Perfect Clear demo
  const sds = sdDemos.demos.filter((d: any) => /^2\.(sd|mochi)\.pc#\d+$/.test(d.node));
  const loops: any[] = [];
  for (const sd of sds) {
    if (sd.locks.length !== 20 || sd.locks.some((l: any) => l[5]) || sd.bags.length !== 3)
      throw new Error(`sdpc-loop: SD demo ${sd.node} is not 20 locks without hold over 3 bags`);
    const leftover = sd.bags[2].unused;
    if (leftover.length !== 1 || !sd.seq.startsWith(sd.bags.map((b: any) => b.queue).join('')))
      throw new Error(`sdpc-loop: SD demo ${sd.node} leftover ${leftover}`);
    for (const half of halves) {
      if (half.plan.leftover !== leftover) continue;
      const pl: Placement[] = half.plan.placements;
      const bags = [sd.bags[0].queue, sd.bags[1].queue, sd.bags[2].queue, half.plan.queue4, half.plan.queue5];
      if (!bags.every(isBag)) throw new Error(`sdpc-loop: ${sd.node} + ${half.dpc} bags ${bags}`);
      let seq = bags.join('');
      while (seq.length < 35 + NEXT_SHOWN) seq += PAD_BAG;
      const inputs = [...sd.inputs, ...half.inputs.map(([f, t, k]: any) => [f + sd.frames, t, k])];
      const frames = sd.frames + half.frames;
      const { rec, eng: e2 } = runDemo(routes, seq, inputs as any, frames);
      const where = `${sd.node} + ${half.dpc}`;
      // THE ARBITER
      if (rec.locks.length !== 35) throw new Error(`sdpc-loop: ${where} engine locked ${rec.locks.length}`);
      for (let i = 0; i < 20; i++)
        if (JSON.stringify(rec.locks[i]) !== JSON.stringify(sd.locks[i]))
          throw new Error(`sdpc-loop: ${where} lock ${i} is not the SD demo's`);
      pl.forEach((p, j) => {
        const i = 20 + j, lk = rec.locks[i]!;
        if (rec.engineQueue[i]!.piece !== p.piece || JSON.stringify(lk[1]) !== JSON.stringify(encodePlace(p.piece, p.cells))
            || lk[2] !== p.lines || lk[3] !== SPIN_OF(p.spin) || lk[5] !== 0)
          throw new Error(`sdpc-loop: ${where} lock ${i} (${p.piece}) engine ${JSON.stringify(lk)}, planned ${p.cells} ${p.lines} ${p.spin}`);
      });
      if (!rec.seq.startsWith(seq)) throw new Error(`sdpc-loop: ${where} engine dealt ${rec.seq}`);
      assertRoundTrip(`sdpc-loop ${where}`, seq, { locks: rec.locks, engineStates: rec.engineStates,
                                                   engineQueue: rec.engineQueue } as any);
      if (!e2.board.perfectClear || e2.board.state.some((r: any) => r.some((c: any) => c)))
        throw new Error(`sdpc-loop: ${where} board not empty after lock 34`);
      // the spins and clears, as the engine credited them
      const events: any[] = [];
      let cum = 0;
      rec.locks.forEach((lk: any, i: number) => {
        cum += lk[2];
        if (lk[3] > 0 && lk[2] > 0)
          events.push({ lock: i, kind: (lk[3] === 1 ? 'mini ' : '') + (['', 'TSS', 'TSD', 'TST'][lk[2]] ?? ''), spin: lk[3], lines: lk[2] });
        if (i === 19 || i === 34) { events.push({ lock: i, kind: 'PC', lines: lk[2], half_lines: cum }); cum = 0; }
      });
      const kinds = events.map(e => e.kind).join(' ');
      if (kinds !== 'TSS TSD PC TSD PC')
        throw new Error(`sdpc-loop: ${where} events ${kinds}`);
      loops.push({
        id: `${sd.node}+${half.dpc}`, sd: sd.node, dpc: half.dpc, setup: half.setup, pc: half.pc,
        mirrored: half.mirrored, leftover, seq, bags, frames, locks: rec.locks, events,
      });
    }
  }
  const leftovers = (xs: any[], f: (x: any) => string) =>
    Object.fromEntries([...new Set(xs.map(f))].sort().map(l => [l, xs.filter(x => f(x) === l).length]));
  return {
    schema: 'sdpc-loop-demos/1',
    report_eligible: false,
    constructed: true,
    means: 'Every combination of stick spin\'s SD Perfect Clear (and もっちパフェ) with とんぼ\'s DPC catalogue that '
      + 'closes the 35-piece loop, built from an empty board and replayed through the engine: 20 locks of the SD demo, '
      + 'then the leftover, bag 4 and its T into a T-spin Double, then bag 5 into a 4-line Perfect Clear.',
    not_eligible_because: 'nobody played these games: the queue and the inputs are ours, chosen by the planner',
    caveat: 'The SD half is taken as drawn only; a mirrored loop is the mirror of one of these. Bag 4 deals its T '
      + 'last and nothing is ever held, so a combination listed as unbuilt is unbuilt under THIS dealing.',
    engine: { options: DEMO_OPTIONS, kickset: TL_DEFAULTS.kickset, allow180: TL_DEFAULTS.allow180,
              date: demoDate(routes).toISOString(), frames_per_input: FRAMES_PER_INPUT },
    inputs: {
      stickspin_demos_md5: md5(readFileSync(PATHS.stickspinDemos)),
      dpc_setups_md5: md5(readFileSync(PATHS.dpcSetups)),
      planner_md5: md5(readFileSync(`${import.meta.dir}/sdpc-loop-demos.ts`)),
      route_demos_md5: md5(readFileSync(`${import.meta.dir}/route-demos.ts`)),
      emit_replay_md5: md5(readFileSync(`${import.meta.dir}/emit-replay.ts`)),
    },
    board: { width: WIDTH, rows: ROWS, visible_rows: VISIBLE_ROWS,
             coords: 'y-UP: row 0 is the bottom row', cell: 'yUp * width + x' },
    lock_fields: LOCK_FIELDS,
    shapes: SHAPES,
    counts: {
      sd_halves: sds.length,
      sd_by_leftover: leftovers(sds, d => d.bags[2].unused),
      dpc_halves_built: halves.length,
      dpc_condition: { met: halves.filter(h => h.condition_met === true).length,
                       not_met: halves.filter(h => h.condition_met === false).length,
                       none: halves.filter(h => h.condition_met == null).length },
      dpc_by_leftover: leftovers(halves, h => h.plan.leftover),
      dpc_unbuilt: unbuilt.filter(u => !u.same_as).length,
      dpc_duplicates: unbuilt.filter(u => u.same_as).length,
      loops: loops.length,
    },
    inputs_note: 'A loop\'s inputs are its SD demo\'s `inputs` (analysis/stickspin-demos.json) followed by its DPC '
      + 'half\'s `inputs` shifted by the SD demo\'s `frames`; `frames` is the sum.',
    dpc_halves: halves.map(h => ({ dpc: h.dpc, setup: h.setup, pc: h.pc, mirrored: h.mirrored, page: h.page,
                                   heading: h.heading, condition: h.condition, condition_met: h.condition_met,
                                   leftover: h.plan.leftover, queue4: h.plan.queue4, queue5: h.plan.queue5,
                                   frames: h.frames, inputs: h.inputs })),
    dpc_unbuilt: unbuilt,
    loops,
  };
}

export function serialise(out: any): string {
  const { loops, ...rest } = out;
  const head = JSON.stringify({ ...rest, loops: '\u0000' }, null, 1);
  return head.replace('"\\u0000"', '[\n' + loops.map((d: any) => '  ' + JSON.stringify(d)).join(',\n') + '\n ]') + '\n';
}
