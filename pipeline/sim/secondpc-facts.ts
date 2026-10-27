/**
 * Second PC: every four-line Perfect Clear in the corpus that starts from a board a Perfect Clear just
 * emptied, and which of harddrop's Second Perfect Clear setups and solutions (if any) it was. One corpus
 * artefact, `analysis/secondpc-facts.json`.
 *
 *   bun pipeline/sim/emit-secondpc-facts.ts --out analysis/secondpc-facts.json
 *
 * WHY ITS OWN FRAMEWORK, beside the DPC page's. A DPC case is read at ONE board (the board before its T);
 * a second PC is ten pieces from empty into four full rows, so the instrument is the whole placement LAYOUT
 * of those ten pieces in the four-row frame — harddrop draws its solutions exactly that way, with a piece
 * placed after a row under it cleared drawn split across that row (the route pages' kept-rows composite).
 * The digest is `technique-facts.ts`'s `digestSession`, imported and not edited.
 *
 * QUARANTINED SIMULATOR OUTPUT (`report_eligible: false`). Every board is the vendored Triangle engine's,
 * and most boards after a Perfect Clear are past the verified prefix (see the DPC page): each case carries
 * `verified` (its last lock is at or before the verified index), and the page prints both counts.
 *
 * THE RULES.
 *   1. PC points are read exactly as `dpc-facts.ts` reads them (board empty after the lock, through the
 *      digest's row map, which must reproduce the engine's next board; from the first step it cannot, no later
 *      point in that round), and anchored the same way, against `clears.allclear`. The loop is a COPY of that
 *      one (so the DPC artefact's hash does not move); `secondpc.test.ts` holds the two to the same points.
 *   2. A CASE is a pair of consecutive PC points whose second clears exactly four lines. Other pairs are
 *      counted by why they are not cases: `other_lines` (a PC of 2, 6, 8 … lines), `garbage` (garbage came in
 *      between: the frame is no longer the player's own ten pieces). A PC with no next PC is `no_next_pc`.
 *   3. THE LAYOUT. Each lock's cells are written into the four-row frame through the row map: the bottom four
 *      rows of the empty board are frame rows 0-3 (drawn top to bottom), a cleared row leaves the frame order
 *      unchanged and only shifts which current row holds which frame row. Every cell must land in a frame row
 *      (a four-line PC from empty has nowhere else to go; anything else throws) and the frame ends full.
 *   4. A SETUP matches, drawn or mirrored (columns reflected, J↔L and S↔Z), when every drawn setup cell holds
 *      the same piece letter in the layout AND the cells are exactly whole pieces of it (no piece of the layout
 *      half inside the setup). A SOLUTION matches when, on a matched setup, every other cell's letter equals
 *      the drawn solution's. Outcome: `solution` (a drawn setup and its drawn solution), `setup` (a drawn setup,
 *      finished another way), `unmatched` (grouped by layout, drawn and mirrored read by the smaller).
 *   5. `setup_first`: the setup's pieces are the first locks after the PC, in some order (the page's reading of
 *      a setup: the four left-over pieces placed first). Measured, never required. `pieces_before`: locks
 *      placed in the round before the second PC's first piece (10 for the page's own case, PCO into it).
 */
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { digestSession, type TechDigest } from './technique-facts.ts';
import { md5Files, corpus, SESSIONS_ROOT } from './route-facts.ts';
import { allclearOf } from './dpc-facts.ts';

const H = 40, W = 10, ROWS = 4;
const SIM = import.meta.dir, OPENERS = `${import.meta.dir}/../openers`;
export const SETUPS_PATH = `${OPENERS}/secondpc-setups.json`;
export const HASH_FILES = [`${SIM}/secondpc-facts.ts`, `${SIM}/emit-secondpc-facts.ts`, `${SIM}/technique-facts.ts`,
                           `${SIM}/route-facts.ts`, `${SIM}/dpc-facts.ts`];
const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

export interface SecondPcMutants { noMirror?: boolean; noLetterSwap?: boolean; noWholePieces?: boolean }

interface Board { id: string; rows: string[] }
interface Setup { id: string; heading: string[]; rows: string[]; pieces: string; solutions: string[]; same_as: string[] }

const SWAP: Record<string, string> = { J: 'L', L: 'J', S: 'Z', Z: 'S' };
/** a drawn board read into the four-row frame, letters upper case (the page shades a second piece lower case) */
const frame = (rows: string[]) => {
  const body = rows.filter((_, i) => rows.slice(0, i + 1).some(r => r !== '.'.repeat(W)));
  return [...Array(ROWS - body.length).fill('.'.repeat(W)), ...body].map(r => r.toUpperCase());
};
export function mirrorRows(rows: string[], swap = true) {
  return rows.map(r => [...r].reverse().map(ch => swap ? (SWAP[ch] ?? ch) : ch).join(''));
}

export function loadSetups(path = SETUPS_PATH): { setups: Setup[]; boards: Map<string, string[]> } {
  const d = JSON.parse(readFileSync(path, 'utf8'));
  return { setups: d.setups, boards: new Map(d.boards.map((b: Board) => [b.id, frame(b.rows)])) };
}

/** PC points of one digest (rule 1, the copy of dpc-facts.ts's loop), with the lines and garbage since the
 *  previous one, and the layout of the pieces between consecutive points when it is a four-row frame */
export function pcPoints(d: TechDigest) {
  let g: boolean[][] = Array.from({ length: H }, () => new Array(W).fill(false));
  // frame row (0..3, top to bottom) held by each current board row, or -1 above the frame
  const freshMap = () => Array.from({ length: H }, (_, r) => r >= H - ROWS ? r - (H - ROWS) : -1);
  let fr = freshMap();
  let layout: string[][] = Array.from({ length: ROWS }, () => new Array(W).fill('.'));
  let owner: number[][] = Array.from({ length: ROWS }, () => new Array(W).fill(-1));
  let overflow = false;
  const points: { lock: number; lines: number; garbage: number; start: number; layout: string[] | null;
                  owner: number[][] | null }[] = [];
  let lines = 0, garbage = 0, start = 0, stops = false;
  for (let k = 0; k < d.locks.length; k++) {
    const lk = d.locks[k]!;
    if (!lk.mapOk) { stops = true; break; }
    for (const q of lk.cells) {
      if (q.row >= 0 && q.row < H && q.col >= 0 && q.col < W) g[q.row]![q.col] = true;
      const f = q.row >= 0 && q.row < H ? fr[q.row]! : -1;
      if (f < 0) overflow = true;
      else { layout[f]![q.col] = lk.piece.toUpperCase(); owner[f]![q.col] = k; }
    }
    const cl = new Set(lk.clearedRows);
    const kept = g.filter((_, i) => !cl.has(i));
    const keptF = fr.filter((_, i) => !cl.has(i));
    while (kept.length < H) { kept.unshift(new Array(W).fill(false)); keptF.unshift(-1); }
    g = kept.slice(lk.garbage);
    fr = keptF.slice(lk.garbage);
    for (let i = 0; i < lk.garbage; i++) { g.push(new Array(W).fill(true)); fr.push(-1); }
    lines += lk.clearedRows.length;
    garbage += lk.garbage;
    if (lk.clearedRows.length && g.every(r => r.every(x => !x))) {
      const full = !overflow && layout.every(r => r.every(c => c !== '.'));
      points.push({ lock: k, lines, garbage, start, layout: full ? layout.map(r => r.join('')) : null,
                    owner: full ? owner : null });
      lines = 0; garbage = 0; start = k + 1; overflow = false;
      fr = freshMap();
      layout = Array.from({ length: ROWS }, () => new Array(W).fill('.'));
      owner = Array.from({ length: ROWS }, () => new Array(W).fill(-1));
    }
  }
  return { points, stops };
}

/** the setups a layout carries (rule 4), each with how it matched */
function matchSetups(layout: string[], owner: number[][], setups: Setup[], boards: Map<string, string[]>,
                     mut: SecondPcMutants) {
  const out: { id: string; mirrored: boolean; solutions: string[]; locks: number[] }[] = [];
  for (const s of setups) {
    for (const mirrored of mut.noMirror ? [false] : [false, true]) {
      const rows = mirrored ? mirrorRows(frame(s.rows), !mut.noLetterSwap) : frame(s.rows);
      let ok = true;
      const inside = new Set<number>();
      for (let r = 0; r < ROWS && ok; r++) for (let c = 0; c < W && ok; c++) {
        const ch = rows[r]![c]!;
        if (ch === '.') continue;
        if (layout[r]![c] !== ch) ok = false; else inside.add(owner[r]![c]!);
      }
      if (!ok) continue;
      if (!mut.noWholePieces) {
        for (let r = 0; r < ROWS && ok; r++) for (let c = 0; c < W && ok; c++)
          if (inside.has(owner[r]![c]!) && rows[r]![c] === '.') ok = false;
      }
      if (!ok) continue;
      const solutions = s.solutions.filter(id => {
        const sol = mirrored ? mirrorRows(boards.get(id)!, !mut.noLetterSwap) : boards.get(id)!;
        return sol.every((row, r) => [...row].every((ch, c) => ch === 'G' || layout[r]![c] === ch));
      });
      out.push({ id: s.id, mirrored, solutions, locks: [...inside].sort((a, b) => a - b) });
    }
  }
  return out;
}

export interface Case {
  session: string; file: string; round_index0: number; match: number; round: number; player: string;
  prev_pc_lock: number; prev_pc_lines: number; pieces_before: number; first_lock: number; pc_lock: number;
  verified: boolean; outcome: 'solution' | 'setup' | 'unmatched'; setups: string[]; solutions: string[];
  mirrored: boolean | null; setup_first: boolean | null; layout: string[]; shape: string;
}

export function classify(digests: TechDigest[], data: ReturnType<typeof loadSetups>, mut: SecondPcMutants = {},
                         allclear?: (d: TechDigest) => number) {
  const cases: Case[] = [];
  const users = [...new Set(digests.map(d => d.user))].sort();
  const tally = Object.fromEntries(users.map(u => [u, { pc_points: 0, no_next_pc: 0, other_lines: 0, garbage: 0,
                                                         rounds_rowmap_stops: 0 }]));
  const anchor = { rounds: 0, rounds_agree: 0, pcs_replay: 0, disagree: [] as string[] };
  for (const d of digests) {
    const { points, stops } = pcPoints(d);
    if (stops) tally[d.user]!.rounds_rowmap_stops++;
    tally[d.user]!.pc_points += points.length;
    if (allclear) {
      const want = allclear(d);
      anchor.rounds++; anchor.pcs_replay += want;
      if (want === points.length) anchor.rounds_agree++;
      else anchor.disagree.push(`${d.session} m${d.match}r${d.round + 1} ${d.user}: ${points.length} read, ${want} counted`);
    }
    if (points.length) tally[d.user]!.no_next_pc++;
    for (let n = 1; n < points.length; n++) {
      const prev = points[n - 1]!, p = points[n]!;
      if (p.garbage) { tally[d.user]!.garbage++; continue; }
      if (p.lines !== ROWS) { tally[d.user]!.other_lines++; continue; }
      // a four-line PC from empty with no garbage has its forty cells in the bottom four rows, so the layout is
      // full by construction; a miss here is a bug in the frame map, never data
      if (!p.layout) {
        throw new Error(`secondpc: ${d.session} m${d.match}r${d.round + 1} ${d.user} @${p.lock}: a four-line PC whose layout is not the four-row frame`);
      }
      const hits = matchSetups(p.layout, p.owner!, data.setups, data.boards, mut);
      const sols = hits.filter(h => h.solutions.length);
      const best = sols.length ? sols : hits;
      const first = best.length ? best.some(h => h.locks.every(k => k < p.start + h.locks.length)) : null;
      const m = mirrorRows(p.layout).join('/'), s = p.layout.join('/');
      cases.push({
        session: d.session, file: d.file, round_index0: d.round, match: d.match, round: d.round + 1, player: d.user,
        prev_pc_lock: prev.lock, prev_pc_lines: prev.lines, pieces_before: p.start, first_lock: p.start, pc_lock: p.lock,
        verified: p.lock <= d.v, outcome: sols.length ? 'solution' : hits.length ? 'setup' : 'unmatched',
        setups: [...new Set(best.map(h => h.id))].sort(),
        solutions: [...new Set(sols.flatMap(h => h.solutions))].sort(),
        mirrored: best.length ? best.every(h => h.mirrored) : null,
        setup_first: first,
        layout: p.layout,
        shape: s < m ? s : m,
      });
    }
  }
  return { users, tally, cases, anchor };
}

export function inputs(sessions: string[], root = SESSIONS_ROOT) {
  return {
    sessions: sessions.map(s => {
      const dir = `${root}/${s}`;
      const h = createHash('md5');
      for (const f of readdirSync(dir).filter(f => f.endsWith('.ttrm')).sort()) h.update(f).update(readFileSync(`${dir}/${f}`));
      return { session: s, replays_md5: h.digest('hex'), replay_facts_md5: md5(readFileSync(`${dir}/sim/replay-facts.json`)) };
    }),
    setups_md5: md5(readFileSync(SETUPS_PATH)),
    emitter_md5: md5Files(HASH_FILES),
  };
}

export function assemble(cls: ReturnType<typeof classify>, data: ReturnType<typeof loadSetups>, sessions: string[],
                         inp: ReturnType<typeof inputs>) {
  const cases = [...cls.cases].sort((a, b) => a.session < b.session ? -1 : a.session > b.session ? 1
    : a.match - b.match || a.round - b.round || (a.player < b.player ? -1 : a.player > b.player ? 1 : 0) || a.pc_lock - b.pc_lock);
  const by_player = Object.fromEntries(cls.users.map(u => {
    const mine = cases.filter(c => c.player === u);
    const count = (f: (c: Case) => boolean) => ({ all: mine.filter(f).length, verified: mine.filter(c => f(c) && c.verified).length });
    return [u, { ...cls.tally[u]!, cases: count(() => true), solution: count(c => c.outcome === 'solution'),
                 setup: count(c => c.outcome === 'setup'), unmatched: count(c => c.outcome === 'unmatched'),
                 after_ten: count(c => c.pieces_before === 10) }];
  }));
  const groups = new Map<string, Case[]>();
  for (const c of cases) if (c.outcome !== 'unmatched') groups.set(c.setups[0]!, [...(groups.get(c.setups[0]!) ?? []), c]);
  const by_setup = Object.fromEntries([...groups.keys()].sort().map(k => {
    const cs = groups.get(k)!;
    return [k, { cases: cs.length, solution: cs.filter(c => c.outcome === 'solution').length,
                 by_player: Object.fromEntries(cls.users.map(u => [u, cs.filter(c => c.player === u).length])) }];
  }));
  const shapes = new Map<string, Case[]>();
  for (const c of cases) if (c.outcome === 'unmatched') shapes.set(c.shape, [...(shapes.get(c.shape) ?? []), c]);
  const unmatched_layouts = [...shapes.entries()].map(([shape, cs]) => ({
    layout: shape.split('/'), cases: cs.length,
    by_player: Object.fromEntries(cls.users.map(u => [u, cs.filter(c => c.player === u).length])),
  })).sort((a, b) => b.cases - a.cases || (a.layout.join('/') < b.layout.join('/') ? -1 : 1));
  return {
    schema: 'secondpc-facts/1',
    report_eligible: false,
    means: 'Every four-line Perfect Clear in the corpus that starts on a board a Perfect Clear just emptied, its ten pieces\' '
      + 'layout in the four-row frame, and which of harddrop\'s Second Perfect Clear setups and solutions (secondpc-setups.json) '
      + 'it carries, by piece letter, drawn or mirrored. Simulator output, one engine.',
    caveat: 'Boards are the vendored engine\'s. Most boards after a Perfect Clear are past the verified prefix (each case '
      + 'carries `verified`); which layout the player built has no second implementation. No claim id, no badge.',
    rules: { pc_point: 'board empty after the lock, through the verified row map (dpc-facts.ts\'s reading)',
             case: 'consecutive PC points, the second clearing exactly four lines with no garbage in between',
             match: 'every drawn setup cell holds the same piece letter in the layout and is whole pieces of it; a solution '
               + 'when every other cell also equals the drawing; drawn or mirrored (J/L and S/Z swapped)' },
    setups: data.setups.length,
    solutions: data.setups.reduce((n, s) => n + s.solutions.length, 0),
    pc_anchor: cls.anchor,
    sessions: sessions.length,
    inputs: inp,
    by_player,
    by_setup,
    unmatched_layouts,
    cases,
  };
}

/** One case per line: diffable. */
export function serialise(out: any): string {
  const { cases, unmatched_layouts, ...rest } = out;
  const head = JSON.stringify({ ...rest, unmatched_layouts: '\u0001', cases: '\u0000' }, null, 1);
  const lines = (xs: any[]) => '[\n' + xs.map(c => '  ' + JSON.stringify(c)).join(',\n') + '\n ]';
  return head.replace('"\\u0001"', lines(unmatched_layouts)).replace('"\\u0000"', lines(cases)) + '\n';
}

export function build(mut: SecondPcMutants = {}, digests?: TechDigest[]) {
  const sessions = corpus();
  const ds = digests ?? sessions.flatMap(s => digestSession(s));
  const data = loadSetups();
  return assemble(classify(ds, data, mut, allclearOf()), data, sessions, inputs(sessions));
}
