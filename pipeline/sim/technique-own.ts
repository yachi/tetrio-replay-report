/**
 * OUR OWN DESIGNS of a mid-game technique: boards nobody drew, found by a search and played by the engine.
 *
 *   bun pipeline/sim/emit-technique-own.ts --technique cutcopy --out analysis/cutcopy-own.json
 *
 * NOT CORPUS DATA AND NOT A SOURCE'S DRAWING. The demo planner (`technique-demos.ts`) can only build a terrain
 * a source drew, and for 千鳥格子 it builds none of them (every drawing is the wrong cell count, or mirrored). So
 * this file asks the question the other way round: which boards, built from an empty board by real pieces out
 * of a 7-bag, carry the variant's window and let the engine play both T-spins? Every board it publishes is
 * ours, and the artefact says `report_eligible: false`, `constructed: true` and `own: true`.
 *
 * THE SEARCH, in four steps, every one deterministic (no clock, no random draw):
 *
 * 1. Place the variant's window, AS DRAWN, at every column offset the profile names, its bottom row on the
 *    floor. Its cells are fixed: drawn-filled cells MUST be filled, drawn-empty cells and the T's cells must
 *    be empty. Outside the window, the rows the stood T clears must be full; the other window rows, and the
 *    profile's rows above the window, MAY be filled.
 * 2. Enumerate every set of tetrominoes that covers every must-fill cell, only on may-fill cells, with at most
 *    two of each non-T kind and every non-T kind at least once — the dealing rule below forces both — lowest
 *    must-fill cell first. Two covers with the same cells are one candidate.
 * 3. Hand each candidate, smallest first, to the SHARED planner (`technique-demos.ts`'s `build`), as a board
 *    added to the transcription in memory: the planner chooses its own cover and order, the engine plays the
 *    script, and the arbiter, the round trip and `reachProblems` check it exactly as for a drawn board. A
 *    search is capped by a COUNT of steps (`maxSteps`), so a candidate over it is reported the same way on
 *    every machine.
 * 4. Stop at an offset once `pick` candidates have built, or `maxTried` have been tried, and publish the ones
 *    built. The outcome of every candidate TRIED is counted by kind; the rest were never tried, and the artefact
 *    says how many.
 *
 * THE DEALING is the planner's (bag 1: six terrain pieces then its T, held; bag 2: the rest of the terrain,
 * its T swapped for the held one and fired, the fillers, the piece that swaps the follow-up T out). That is
 * why a terrain here holds no T and at most twelve pieces, and it is a limit of this search, not of the
 * technique: a real game deals T's into the stack as well.
 */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { build as buildDemos } from './technique-demos.ts';
import { SHAPES, WIDTH } from './emit-replay.ts';
import { md5Files } from './route-facts.ts';
import { loadTranscription, type Variant } from './technique-facts.ts';
import type { TechniqueProfile } from './technique-profile.ts';
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

export interface OwnProfile {
  key: string;
  tag: string;
  artefactPath: string;
  /** the files `search_md5` hashes: an edit to any of them stales the artefact */
  hashFiles: string[];
  /** the variant whose window every board carries, as drawn */
  variant: string;
  /** window column offsets tried (the window's left column on the board) */
  offsets: number[];
  /** rows above the window a cover may use */
  rowsAbove: number;
  /** pieces beyond the six bag-1 pieces a cover may use */
  maxExtra: number;
  /** each candidate's search cap, in planner steps */
  maxSteps: number;
  /** candidates tried at most per offset; the rest are counted as not tried */
  maxTried: number;
  /** boards published per offset */
  pick: number;
  artefact: { schema: string; means: string; notEligible: string; caveat: string };
  rules(): string[];
}

const KINDS = ['I', 'J', 'L', 'O', 'S', 'Z'];

/** The variant's window as drawn: per window cell (row from the window's top, column from its left) 'T', '#'
 *  (filled) or '.' (empty), its height and width, and the window rows the stood T clears. */
export function windowGrid(tr: any, v: Variant) {
  const rows: string[] = tr.nodes.find((n: any) => n.id === v.board).rows;
  const empties: string = tr.empty_letters ?? '';
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  const tc = new Set(v.t_cells.map(([r, c]: [number, number]) => `${r},${c}`));
  const g: string[] = [];
  for (let r = r0; r <= r1; r++) {
    let line = '';
    for (let c = c0; c <= c1; c++) {
      const ch = rows[r]![c]!;
      line += tc.has(`${r},${c}`) ? 'T' : (ch === '-' || empties.includes(ch) ? '.' : '#');
    }
    g.push(line);
  }
  const cleared = [...new Set(v.t_cells.map(([r]: [number, number]) => r - r0))].sort((a, b) => a - b);
  if (cleared.length !== v.lines) throw new Error(`own: ${v.id}'s T spans ${cleared.length} rows, it clears ${v.lines}`);
  return { g, h: r1 - r0 + 1, w: c1 - c0 + 1, cleared };
}

/** Step 1 and 2: the candidate terrains at one offset, each as y-UP cell indices, smallest first. */
export function candidates(tr: any, v: Variant, off: number, rowsAbove: number, maxExtra: number): number[][] {
  const { g, h, w, cleared } = windowGrid(tr, v);
  if (off < 0 || off + w > WIDTH) throw new Error(`own: offset ${off} puts the window off the board`);
  const H = h + rowsAbove;
  const id = (x: number, y: number) => y * WIDTH + x;
  const must = new Set<number>(), may = new Set<number>();
  g.forEach((line, i) => [...line].forEach((ch, j) => { if (ch === '#') must.add(id(off + j, h - 1 - i)); }));
  for (let i = 0; i < h; i++) for (let x = 0; x < WIDTH; x++) {
    if (x >= off && x < off + w) continue;
    (cleared.includes(i) ? must : may).add(id(x, h - 1 - i));
  }
  for (let y = h; y < H; y++) for (let x = 0; x < WIDTH; x++) may.add(id(x, y));
  // the window's cells outside its box (`window_extra`), read as drawn like the box's own
  const rows: string[] = tr.nodes.find((n: any) => n.id === v.board).rows;
  const empties: string = tr.empty_letters ?? '';
  for (const [r, c] of v.window_extra?.cells ?? []) {
    const x = off + c - v.window.cols[0], y = h - 1 - (r - v.window.rows[0]);
    if (x < 0 || x >= WIDTH || y < 0 || y >= H) throw new Error(`own: ${v.id}'s window_extra cell ${r},${c} is outside the search's rows`);
    const ch = rows[r]![c]!;
    may.delete(id(x, y));
    if (!(ch === '-' || empties.includes(ch))) must.add(id(x, y));
  }
  const fits = (allowed: Set<number>, kind: string, at: number) => {
    const out: number[][] = [];
    for (const shape of SHAPES[kind]!) for (const [ox, oy] of shape) {
      const ax = at % WIDTH - ox, ay = Math.floor(at / WIDTH) - oy;
      const cs = shape.map(([dx, dy]) => [ax + dx, ay + dy] as [number, number]);
      if (cs.some(([x, y]) => x < 0 || x >= WIDTH || y < 0 || y >= H)) continue;
      const ix = cs.map(([x, y]) => id(x, y)).sort((a, b) => a - b);
      if (ix.every(c => allowed.has(c)) && !out.some(o => o.join() === ix.join())) out.push(ix);
    }
    return out;
  };
  const found = new Map<string, number[]>();
  const rec = (free: Set<number>, used: Record<string, number>, cells: number[], left: Set<number>) => {
    const n = Object.values(used).reduce((a, b) => a + b, 0);
    if (n > 6 + maxExtra) return;
    if (!left.size) {
      const missing = KINDS.filter(k => !used[k]);
      if (!missing.length) {
        const sorted = [...cells].sort((a, b) => a - b);
        found.set(sorted.join(), sorted);
        return;
      }
      if (n + missing.length > 6 + maxExtra) return;
      // a missing kind goes on may-fill cells, lowest anchor first
      const k = missing[0]!;
      for (const c of [...free].sort((a, b) => a - b)) for (const p of fits(free, k, c)) {
        if (Math.min(...p) !== c) continue;
        rec(new Set([...free].filter(x => !p.includes(x))), { ...used, [k]: 1 }, [...cells, ...p], left);
      }
      return;
    }
    const low = Math.min(...left);
    for (const k of KINDS) {
      if ((used[k] ?? 0) >= 2) continue;
      for (const p of fits(free, k, low))
        rec(new Set([...free].filter(x => !p.includes(x))), { ...used, [k]: (used[k] ?? 0) + 1 }, [...cells, ...p],
            new Set([...left].filter(x => !p.includes(x))));
    }
  };
  rec(new Set([...must, ...may]), {}, [], new Set(must));
  return [...found.values()].sort((a, b) => a.length - b.length || (a.join() < b.join() ? -1 : 1));
}

/** A y-UP cell set as rows top first ('c' filled), from the highest filled row down to the floor. */
export function rowsOf(cells: number[]): string[] {
  const set = new Set(cells), top = Math.max(...cells.map(c => Math.floor(c / WIDTH)));
  const out: string[] = [];
  for (let y = top; y >= 0; y--) {
    let s = '';
    for (let x = 0; x < WIDTH; x++) s += set.has(y * WIDTH + x) ? 'c' : '-';
    out.push(s);
  }
  return out;
}

/** The planner's reason for a candidate it could not build, as a kind. */
function outcomeKind(reason: string): string {
  if (reason.startsWith('搜尋超過')) return 'over_budget';
  if (reason.startsWith('地形冇一個')) return 'no_cover';
  if (reason.includes('個鋪法都唔得')) {
    if (reason.includes('第二下 TSD') || reason.includes('第二粒 T')) return 'no_followup';
    if (reason.includes('企直嘅 T') || reason.includes('個窗口對到')) return 'no_stood_t';
    return 'no_order';
  }
  return 'other';
}

/** One candidate through the shared planner: the demo, or the planner's reason. */
export function planOwn(P: TechniqueProfile, DP: TechniqueDemoProfile, tr: any, id: string, rows: string[],
                        maxSteps: number): { demo: any | null; reason: string; out: any } {
  // the board twice: the planner's chain is a build board over its terrain, and a board of ours has no page
  // pieces, so the two are the same drawing under two ids (each reached once)
  const t2 = { ...tr, nodes: [...tr.nodes, { id, kind: 'own', rows }, { id: `${id}.terrain`, kind: 'own', rows }] };
  const DP2: TechniqueDemoProfile = { ...DP, chains: [{ node: id, terrain: `${id}.terrain` }],
    unbuilt: Object.fromEntries(tr.nodes.map((n: any) => [n.id, 'a drawn board: not planned here'])) };
  const out = buildDemos(P, DP2, {}, { tr: t2, maxSteps });
  const demo = out.demos.find((d: any) => d.node === id) ?? null;
  const reason = demo ? '' : out.unbuilt.find((u: any) => u.node === id).reason;
  return { demo, reason, out };
}

/** One offset of the search (steps 1-4): its candidates, the outcome of every one TRIED, the boards it publishes.
 *  The emitter runs the offsets in parallel processes and `assemble` puts them back in profile order, so the
 *  artefact does not depend on which finished first. */
export function searchOffset(P: TechniqueProfile, DP: TechniqueDemoProfile, OP: OwnProfile, off: number) {
  const tr = loadTranscription(DP.transcriptionPath);
  const v: Variant = tr.variants.find((x: Variant) => x.id === OP.variant);
  if (!v) throw new Error(`${OP.tag}-own: no variant ${OP.variant}`);
  const cands = candidates(tr, v, off, OP.rowsAbove, OP.maxExtra);
  const outcomes: Record<string, number> = {};
  const built: string[] = [];
  const boards: any[] = [], demos: any[] = [];
  let shared: any = null, tried = 0;
  for (const [i, cells] of cands.entries()) {
    if (built.length >= OP.pick || tried >= OP.maxTried) break;
    tried++;
    const id = `own.${off}.${i + 1}`;
    const rows = rowsOf(cells);
    const r = planOwn(P, DP, tr, id, rows, OP.maxSteps);
    const k = r.demo ? 'built' : outcomeKind(r.reason);
    outcomes[k] = (outcomes[k] ?? 0) + 1;
    if (process.env.OWN_PROGRESS && (tried % 50 === 0 || r.demo)) console.error(`  offset ${off}: ${tried} tried, last ${id} ${k}`);
    if (!r.demo) continue;
    built.push(id);
    if (!shared) shared = { engine: r.out.engine, board: r.out.board, lock_fields: r.out.lock_fields, shapes: r.out.shapes };
    boards.push({ id, offset: off, candidate: i + 1, cells: cells.length, rows });
    demos.push(r.demo);
  }
  return { per_offset: { offset: off, candidates: cands.length, tried, not_tried: cands.length - tried, outcomes, built },
           boards, demos, shared };
}

/** The artefact, from every offset's part in profile order. */
export function assemble(P: TechniqueProfile, DP: TechniqueDemoProfile, OP: OwnProfile, parts: any[]) {
  const tr = loadTranscription(DP.transcriptionPath);
  const v: Variant = tr.variants.find((x: Variant) => x.id === OP.variant);
  const offs = parts.map(p => p.per_offset.offset);
  if (offs.join() !== OP.offsets.join()) throw new Error(`${OP.tag}-own: parts for offsets ${offs}, want ${OP.offsets}`);
  const shared = parts.find(p => p.shared)?.shared ?? null;
  return {
    schema: OP.artefact.schema,
    report_eligible: false,
    constructed: true,
    own: true,
    technique: OP.key,
    means: OP.artefact.means,
    not_eligible_because: OP.artefact.notEligible,
    caveat: OP.artefact.caveat,
    rules: OP.rules(),
    search: { variant: OP.variant, window: windowGrid(tr, v).g, window_extra: v.window_extra?.cells ?? [], offsets: OP.offsets, rows_above: OP.rowsAbove,
              max_extra: OP.maxExtra, max_steps: OP.maxSteps, max_tried: OP.maxTried, pick: OP.pick,
              per_offset: parts.map(p => p.per_offset) },
    engine: shared?.engine ?? null,
    inputs: {
      transcription_md5: md5(readFileSync(DP.transcriptionPath)),
      search_md5: md5Files(OP.hashFiles),
      planner_md5: md5Files(DP.hashFiles.planner),
      classifier_md5: md5Files(P.hashFiles.classifier),
    },
    board: shared?.board ?? null,
    lock_fields: shared?.lock_fields ?? null,
    shapes: shared?.shapes ?? null,
    boards: parts.flatMap(p => p.boards),
    demos: parts.flatMap(p => p.demos),
  };
}

/** The whole search in one process (the test's OWN_FULL rebuild). */
export function build(P: TechniqueProfile, DP: TechniqueDemoProfile, OP: OwnProfile) {
  return assemble(P, DP, OP, OP.offsets.map(o => searchOffset(P, DP, OP, o)));
}

/** One demo per line, as the demo artefact is written. */
export function serialise(out: any): string {
  const { demos, ...rest } = out;
  const head = JSON.stringify({ ...rest, demos: '\u0000' }, null, 1);
  return head.replace('"\\u0000"', '[\n' + demos.map((d: any) => '  ' + JSON.stringify(d)).join(',\n') + '\n ]') + '\n';
}
