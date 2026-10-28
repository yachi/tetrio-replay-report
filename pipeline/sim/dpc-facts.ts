/**
 * DPC: after every Perfect Clear in the corpus, the first T-spin, and which of harddrop's DPC setups (if
 * any) it was fired from. One corpus artefact, `analysis/dpc-facts.json`.
 *
 *   bun pipeline/sim/emit-dpc-facts.ts --out analysis/dpc-facts.json
 *
 * WHY ITS OWN FRAMEWORK. A DPC setup is a WHOLE board built from empty (the left-over piece and two bags),
 * so a technique window (a local shape on a partial stack) is the wrong instrument, and a route page's tree
 * (fixed lock counts from the round's start, behind a bag-1 gate) is the wrong frame: the setup starts at a
 * Perfect Clear, wherever in the round that is. So this matcher reads the same digest the technique pages do
 * (`technique-facts.ts`'s `digestSession`, imported and not edited) and compares whole boards, as the route
 * code does, from a different starting lock.
 *
 * QUARANTINED SIMULATOR OUTPUT (`report_eligible: false`). Every board is the vendored Triangle engine's.
 * The verified prefix usually ends AT or near a Perfect Clear (the game can send a Perfect Clear's attack in
 * more than one packet where the engine sends one, which fails the reconstruction check from there on), so
 * most post-PC boards here are PAST it: each case carries `verified` (the T lock is at or before the verified
 * index), and the page prints both counts. Which board a T went into has no second implementation.
 *
 * THE RULES.
 *   1. A PC point is a lock after which the board is EMPTY, read through the digest's row map (cells in,
 *      cleared rows out, garbage pushed in under), which must reproduce the engine's own next board at every
 *      step (`mapOk`). From the first step it cannot reproduce, no later PC point is read in that round
 *      (`rowmap_stops`, counted). `pc_lines` is the lines cleared since the previous empty board.
 *   2. The case is the FIRST T lock with a spin credit that cleared lines, within `WINDOW` locks after the PC
 *      and before the next PC point. None: the PC point is counted as `no_tspin` and is not a case.
 *   3. The board before that T, garbage rows stripped from the bottom (a bottom row holding only garbage
 *      and empty cells; the count travels as `garbage_rows`), is compared by OCCUPANCY with every setup's
 *      `base` (`dpc-setups.json`), as drawn and mirrored, bottom-aligned; and the T's four cells with the
 *      setup's `t_cells` in the same frame, and its lines with the setup's `lines`. All three: `matched`,
 *      with EVERY setup id carrying that (base, T) — a shape drawn on several pages is one shape. The base
 *      alone: `base_only` (the T went somewhere the page does not draw). Neither: `unmatched`, grouped by
 *      shape (drawn and mirrored are one group, read by the lexically smaller).
 *   4. A garbage cell left after stripping (garbage under a stack the player built) is `garbage_in_board`;
 *      such a board can still match, since garbage is filled.
 *   5. `next_pc`: the next PC point within `WINDOW` locks after the T, or null. `cleared_before`: lines the
 *      player cleared between the PC and the T (an SPC setup clears one).
 *
 * THE ANCHOR. Rule 1's PC points are counted per player-round and compared with the replay's own Perfect
 * Clear counter (`clears.allclear`, which both extractors read into facts.json): `pc_anchor` records how many
 * player-rounds agree and names every one that does not. That licenses WHERE a case starts (a PC the game
 * itself counted); it says nothing about which board followed.
 */
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { digestSession, type TechDigest } from './technique-facts.ts';
import { md5Files, corpus, SESSIONS_ROOT } from './route-facts.ts';

const H = 40, W = 10;
const SIM = import.meta.dir, OPENERS = `${import.meta.dir}/../openers`;
export const SETUPS_PATH = `${OPENERS}/dpc-setups.json`;
export const HASH_FILES = [`${SIM}/dpc-facts.ts`, `${SIM}/emit-dpc-facts.ts`, `${SIM}/technique-facts.ts`,
                           `${SIM}/route-facts.ts`];
/** a setup is the left-over piece and two bags: the T is at most the 15th lock after the PC */
export const WINDOW = 15;
const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

export interface DpcMutants { noMirror?: boolean; noTCheck?: boolean; noLinesCheck?: boolean; noGarbageStrip?: boolean;
                              window?: number; ignoreNextPc?: boolean }

interface Setup { id: string; page: string; heading: string[]; base: string[]; t_cells: [number, number][];
                  frame_rows: number; lines: number; same_as: string[] }

/** occupancy rows, leading empty rows dropped */
const occ = (rows: string[]) => {
  const o = rows.map(r => r.replace(/[^.]/g, 'x'));
  while (o.length && o[0] === '.'.repeat(W)) o.shift();
  return o;
};
const mirror = (rows: string[]) => rows.map(r => [...r].reverse().join(''));
/** a set of (row from the bottom, col) */
const key = (cells: [number, number][]) => cells.map(([r, c]) => `${r},${c}`).sort().join(' ');

export function loadSetups(path = SETUPS_PATH): Setup[] { return JSON.parse(readFileSync(path, 'utf8')).setups; }

/** setups indexed by base string, each with its T cells as rows-from-the-bottom, drawn and mirrored */
function index(setups: Setup[], mut: DpcMutants) {
  const byBase = new Map<string, { id: string; mirrored: boolean; t: string; lines: number }[]>();
  for (const s of setups) {
    const fromBottom = s.t_cells.map(([r, c]) => [s.frame_rows - 1 - r, c] as [number, number]);
    for (const mirrored of mut.noMirror ? [false] : [false, true]) {
      const base = (mirrored ? mirror(s.base) : s.base).join('/');
      const t = key(fromBottom.map(([r, c]) => [r, mirrored ? W - 1 - c : c]));
      const list = byBase.get(base) ?? [];
      list.push({ id: s.id, mirrored, t, lines: s.lines });
      byBase.set(base, list);
    }
  }
  return byBase;
}

export interface Case {
  session: string; file: string; round_index0: number; match: number; round: number; player: string;
  pc_lock: number; pc_lines: number; lock: number; spin: string; lines: number; cleared_before: number;
  garbage_rows: number; garbage_in_board: boolean; verified: boolean; pc_verified: boolean;
  outcome: 'matched' | 'base_only' | 'unmatched'; setups: string[]; mirrored: boolean | null; shape: string;
  next_pc: number | null;
}

/** the replay's own Perfect Clear counter for a digest's player-round (`clears.allclear` in facts.json, read
 *  by both extractors); throws when it is missing, never defaults */
export function allclearOf(root = SESSIONS_ROOT) {
  const facts = new Map<string, any>();
  return (d: TechDigest): number => {
    if (!facts.has(d.session)) facts.set(d.session, JSON.parse(readFileSync(`${root}/${d.session}/report/facts.json`, 'utf8')));
    const m = facts.get(d.session).matches.find((x: any) => x.file === d.file);
    const v = m?.rounds[d.round]?.players[d.user]?.clears?.allclear;
    if (typeof v !== 'number') throw new Error(`dpc: ${d.session} ${d.file} r${d.round} ${d.user}: no clears.allclear`);
    return v;
  };
}

export function classify(digests: TechDigest[], setups: Setup[], mut: DpcMutants = {}, allclear?: (d: TechDigest) => number) {
  const win = mut.window ?? WINDOW;
  const byBase = index(setups, mut);
  const cases: Case[] = [];
  const users = [...new Set(digests.map(d => d.user))].sort();
  const tally = Object.fromEntries(users.map(u => [u, { pc_points: 0, no_tspin: 0, rounds_rowmap_stops: 0 }]));
  const anchor = { rounds: 0, rounds_agree: 0, pcs_replay: 0, disagree: [] as string[] };
  for (const d of digests) {
    // rule 1: PC points through the verified row map
    let g: boolean[][] = Array.from({ length: H }, () => new Array(W).fill(false));
    const empties: { lock: number; lines: number }[] = [];
    let lines = 0;
    for (let k = 0; k < d.locks.length; k++) {
      const lk = d.locks[k]!;
      if (!lk.mapOk) { tally[d.user]!.rounds_rowmap_stops++; break; }
      for (const q of lk.cells) if (q.row >= 0 && q.row < H && q.col >= 0 && q.col < W) g[q.row]![q.col] = true;
      const cl = new Set(lk.clearedRows);
      const kept = g.filter((_, i) => !cl.has(i));
      while (kept.length < H) kept.unshift(new Array(W).fill(false));
      g = kept.slice(lk.garbage);
      for (let i = 0; i < lk.garbage; i++) g.push(new Array(W).fill(true));
      lines += lk.clearedRows.length;
      if (lk.clearedRows.length && g.every(r => r.every(x => !x))) { empties.push({ lock: k, lines }); lines = 0; }
    }
    tally[d.user]!.pc_points += empties.length;
    if (allclear) {
      const want = allclear(d);
      anchor.rounds++; anchor.pcs_replay += want;
      if (want === empties.length) anchor.rounds_agree++;
      else anchor.disagree.push(`${d.session} m${d.match}r${d.round + 1} ${d.user}: ${empties.length} read, ${want} counted`);
    }
    for (let n = 0; n < empties.length; n++) {
      const e = empties[n]!.lock, next = empties[n + 1]?.lock ?? Infinity;
      // rule 2
      const t = d.tspins.find(x => x.i > e && x.i <= e + win && (mut.ignoreNextPc || x.i <= next));
      if (!t) { tally[d.user]!.no_tspin++; continue; }
      const lk = d.locks[t.i]!;
      // rule 3: garbage rows stripped from the bottom
      const rows = [...t.board];
      let garbage_rows = 0;
      while (!mut.noGarbageStrip && rows.length && /^[G.]+$/.test(rows[rows.length - 1]!) && rows[rows.length - 1]!.includes('G')) {
        rows.pop(); garbage_rows++;
      }
      const shape = occ(rows);
      const cells: [number, number][] = lk.cells.map(q => [H - 1 - garbage_rows - q.row, q.col]);
      const tk = key(cells);
      const cands = byBase.get(shape.join('/')) ?? [];
      const hits = cands.filter(c => (mut.noTCheck || c.t === tk) && (mut.noLinesCheck || c.lines === lk.cleared));
      let cleared_before = 0;
      for (let k = e + 1; k < t.i; k++) cleared_before += d.locks[k]!.clearedRows.length;
      const nx = empties.find(x => x.lock > t.i && x.lock <= t.i + win);
      const m = mirror(shape).join('/'), s = shape.join('/');
      cases.push({
        session: d.session, file: d.file, round_index0: d.round, match: d.match, round: d.round + 1, player: d.user,
        pc_lock: e, pc_lines: empties[n]!.lines, lock: t.i, spin: lk.spin, lines: lk.cleared, cleared_before, garbage_rows,
        garbage_in_board: rows.some(r => r.includes('G')), verified: t.i <= d.v, pc_verified: e <= d.v,
        outcome: hits.length ? 'matched' : cands.length ? 'base_only' : 'unmatched',
        setups: [...new Set(hits.map(h => h.id))].sort(),
        // mirrored only when no setup matches as drawn (some pages draw the same shape both ways)
        mirrored: hits.length ? hits.every(h => h.mirrored) : null,
        shape: s < m ? s : m,
        next_pc: nx ? nx.lock : null,
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

export function assemble(cls: ReturnType<typeof classify>, setups: Setup[], sessions: string[], inp: ReturnType<typeof inputs>) {
  const cases = [...cls.cases].sort((a, b) => a.session < b.session ? -1 : a.session > b.session ? 1
    : a.match - b.match || a.round - b.round || (a.player < b.player ? -1 : a.player > b.player ? 1 : 0) || a.lock - b.lock);
  const by_player = Object.fromEntries(cls.users.map(u => {
    const mine = cases.filter(c => c.player === u);
    const count = (f: (c: Case) => boolean) => ({ all: mine.filter(f).length, verified: mine.filter(c => f(c) && c.verified).length });
    return [u, { ...cls.tally[u]!, cases: count(() => true), matched: count(c => c.outcome === 'matched'),
                 base_only: count(c => c.outcome === 'base_only'), unmatched: count(c => c.outcome === 'unmatched'),
                 next_pc: count(c => c.next_pc !== null) }];
  }));
  // per setup group (a shape carried by several setup ids is one group, named by its smallest id)
  const groups = new Map<string, Case[]>();
  for (const c of cases) if (c.outcome === 'matched') groups.set(c.setups[0]!, [...(groups.get(c.setups[0]!) ?? []), c]);
  const by_setup = Object.fromEntries([...groups.keys()].sort().map(k => {
    const cs = groups.get(k)!;
    return [k, { setups: cs[0]!.setups, by_player: Object.fromEntries(cls.users.map(u => [u, cs.filter(c => c.player === u).length])) }];
  }));
  const shapes = new Map<string, Case[]>();
  for (const c of cases) if (c.outcome !== 'matched') shapes.set(c.shape, [...(shapes.get(c.shape) ?? []), c]);
  const unmatched_shapes = [...shapes.entries()].map(([shape, cs]) => ({
    shape: shape.split('/'), outcome: cs[0]!.outcome, cases: cs.length,
    by_player: Object.fromEntries(cls.users.map(u => [u, cs.filter(c => c.player === u).length])),
  })).sort((a, b) => b.cases - a.cases || (a.shape.join('/') < b.shape.join('/') ? -1 : 1));
  return {
    schema: 'dpc-facts/1',
    report_eligible: false,
    means: 'After every Perfect Clear in the corpus, the first T-spin within the window, and which of harddrop\'s DPC setups '
      + '(dpc-setups.json) the board before it was, by occupancy, drawn or mirrored. Simulator output, one engine.',
    caveat: 'Boards are the vendored engine\'s. Most post-PC boards are past the verified prefix (each case carries '
      + '`verified`); which setup a T went into has no second implementation. No claim id, no badge.',
    rules: { window_locks: WINDOW, pc_point: 'board empty after the lock, through the verified row map',
             match: 'occupancy of the board before the T (garbage rows stripped from the bottom) equals a setup base, '
               + 'and the T cells and lines equal the setup\'s, drawn or mirrored, bottom-aligned' },
    setups: setups.length,
    pc_anchor: cls.anchor,
    sessions: sessions.length,
    inputs: inp,
    by_player,
    by_setup,
    unmatched_shapes,
    cases,
  };
}

/** One case per line: diffable. */
export function serialise(out: any): string {
  const { cases, unmatched_shapes, ...rest } = out;
  const head = JSON.stringify({ ...rest, unmatched_shapes: '\u0001', cases: '\u0000' }, null, 1);
  const lines = (xs: any[]) => '[\n' + xs.map(c => '  ' + JSON.stringify(c)).join(',\n') + '\n ]';
  return head.replace('"\\u0001"', lines(unmatched_shapes)).replace('"\\u0000"', lines(cases)) + '\n';
}

export function build(mut: DpcMutants = {}, digests?: TechDigest[]) {
  const sessions = corpus();
  const ds = digests ?? sessions.flatMap(s => digestSession(s));
  const setups = loadSetups();
  return assemble(classify(ds, setups, mut, allclearOf()), setups, sessions, inputs(sessions));
}
