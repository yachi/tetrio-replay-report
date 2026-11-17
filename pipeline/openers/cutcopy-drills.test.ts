/**
 * 千鳥格子練習場's drills (`pipeline/sim/cutcopy-drills.ts` → `analysis/cutcopy-drills.json`) and the page's
 * practice engine (`pipeline/cutcopy_practice_engine.js`).
 *
 *   - the committed artefact rebuilds byte for byte, and its md5s are current;
 *   - the drills are a NAMED list, with each one's difficulty, and every refused candidate is named with its reason;
 *   - per drill: the start fires no window, every solution lock is reachable by the reference engine (route-demos
 *     `reach`), after exactly `need` pieces a full T-spin Double fires the corpus matcher's `windowMatch` in the
 *     stated variant and hand, and its follow-up slot carries;
 *   - a differential: on every board the drills pass through, for every T placement the practice engine finds, its
 *     `matchWindow` answers as `windowMatch` does, and its spin and lines are the reference engine's; both answers
 *     must occur. The practice engine's placements are a subset of the reference engine's;
 *   - four mutants the differential must catch: a flipped window cell, a dropped mirror, a dropped window_extra cell
 *     and a broken kick;
 *   - headless replay: every drill passes at exactly `need` through the practice engine's own run.
 * The playwright runs in tools/cutcopy-practice/ are manual and are not a gate.
 */
import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { relative } from 'node:path';
import { loadTranscription, prepare, windowMatch } from '../sim/technique-facts.ts';
import { newEngine, reach } from '../sim/route-demos.ts';
import { build, serialise, windowsFor, replayN, firstBuildable, E, PATHS, REPO, CODE, VARIANTS } from '../sim/cutcopy-drills.ts';

const committed = readFileSync(PATHS.out, 'utf8');
const A = JSON.parse(committed);
const tr = loadTranscription(PATHS.transcription);
const WINDOWS = windowsFor(tr);
E.setWindows(WINDOWS);
const PREPARED = VARIANTS.flatMap(id => prepare(tr, tr.variants.find((v: any) => v.id === id)));
const ENG = newEngine(tr);
const H = 40, W = 10;

/** the drills and their difficulty, by name: a new, lost or re-rated drill is a red build to read */
const DRILLS: Record<string, [string, number | null]> = {
  'page-hole@0': ['中', 3],
  '2026-10-20-m2r1@4': ['易', 1],
  '2026-10-20-m2r1@0': ['易', 1],
  'sp-83-58@2': ['難', 4],
  'sp-83-58@0': ['極難', null],
  'sp-136-83@4': ['中', 3],
  'sp-136-83@0': ['極難', null],
  'sp-173-193@2': ['難', 4],
  'sp-173-193@0': ['極難', null],
  'sp-176-80@4': ['難', 4],
  'sp-176-80@2': ['極難', null],
  'sp-193-26@3': ['難', 4],
  'sp-193-26@2': ['極難', null],
  'sp-195-135@5': ['中', 3],
  'own.3.184@0': ['極難', null],
};
/** every candidate the selection refused, with its reason */
const DROPPED: Record<string, string> = {
  'sp-195-135@5': 'duplicate',
  '2026-11-01-m4r2@1': 'garbage_luck',
};

const stateOf = (s: any) => ({ p: s.piece, x: s.x, y: s.y, r: s.r, spin: s.spin });
const rowsOf = (b: any[][]) => b.map(r => r.map(c => c ?? '.').join(''));
const yUpGrid = (b: any[][]) => { const g: (string | null)[][] = []; for (let y = H - 1; y >= 0; y--) g.push(b[y]!.map(c => c ?? null)); return g; };
const yUpCells = (cells: number[][]) => cells.map(([x, y]) => (H - 1 - y!) * W + x!);
const SPIN = (s: string) => s === 'full' ? 'normal' : s === 'mini' ? 'mini' : null;
const linesOf = (b: any[][], cells: number[][]) => {
  const nb = b.map(r => r.slice()); for (const [x, y] of cells) nb[y!]![x!] = 'T';
  return nb.filter(r => r.every((c: any) => c !== null)).length;
};
/** the corpus matcher's answer: the first prepared window (both variants, both hands) that fires */
function reference(b: any[][], cells: number[][]) {
  const board = rowsOf(b), cs = cells.map(([x, y]) => ({ row: y!, col: x! }));
  for (const P of PREPARED) {
    const m = windowMatch(board, cs as any, P);
    if (m) return { variant: P.id, mirrored: P.mirrored, follow: P.followup.map(f => [f.c + m.dc, f.r + m.dr]) };
  }
  return null;
}

/** every board a drill passes through (before each solution lock, and before the T at need) */
function boardsOf(d: any) {
  const out: any[][][] = [], run = E.newRun(d);
  out.push(E.cloneBoard(run.board));
  for (let i = 0; i < d.need; i++) { E.applyLock(run, d, stateOf(d.solution[i])); out.push(E.cloneBoard(run.board)); }
  return out;
}
/** the differential's boards: every drill board, plus each firing board with its window_extra cells emptied (a
 *  control for the overhang rule, which no drill board need exercise on its own) */
function differentialBoards() {
  const boards = A.drills.flatMap(boardsOf);
  const extra = WINDOWS.flatMap((w: any) => w.cells.filter((c: any) => c.extra));
  const out = [...boards];
  for (const b of boards) {
    const fb = E.findBuild(b);
    if (!fb) continue;
    const nb = E.cloneBoard(b);
    for (const [x, y, ch] of fb.m.cells) if (ch === 'X') nb[y][x] = null;
    out.push(nb);
  }
  if (!extra.length) throw new Error('no window_extra cell to control');
  return out;
}
const DIFF_BOARDS = differentialBoards();

/** the differential: disagreements, and how often the window fired / did not */
function differential(boards = DIFF_BOARDS) {
  const bad: string[] = [];
  let fired = 0, notFired = 0, placements = 0;
  boards.forEach((b, bi) => {
    const grid = yUpGrid(b);
    for (const pl of E.placements(b, 'T')) {
      placements++;
      const cells = E.cellsOf('T', pl.state.x, pl.state.y, pl.state.r);
      const page = E.matchWindow(b, cells), ref = reference(b, cells);
      if (!!page !== !!ref) bad.push(`board ${bi} T ${E.key(cells)}: page ${page ? page.variant : 'none'}, matcher ${ref ? ref.variant : 'none'}`);
      else if (page && (page.variant !== ref!.variant || page.mirrored !== ref!.mirrored || E.key(page.follow) !== E.key(ref!.follow)))
        bad.push(`board ${bi} T ${E.key(cells)}: page ${page.variant}/${page.mirrored}, matcher ${ref!.variant}/${ref!.mirrored}`);
      if (ref) fired++; else notFired++;
      const paths = reach(ENG, grid, 'T', yUpCells(cells));
      if (!paths.some(p => p.spin === SPIN(pl.state.spin)))
        bad.push(`board ${bi} T ${E.key(cells)}: page spin ${pl.state.spin}, reference ${paths.map(p => p.spin).join('/') || 'unreachable'}`);
      if (E.lock(b, pl.state).lines !== linesOf(b, cells)) bad.push(`board ${bi} T ${E.key(cells)}: lines`);
    }
  });
  return { bad, fired, notFired, placements };
}
/** every placement of every piece the practice engine finds is one the reference engine reaches, spin included */
function subset(boards = DIFF_BOARDS.slice(0, 40)) {
  const bad: string[] = [];
  boards.forEach((b, bi) => {
    const grid = yUpGrid(b);
    for (const p of E.P) for (const pl of E.placements(b, p)) {
      const cells = E.cellsOf(p, pl.state.x, pl.state.y, pl.state.r);
      if (!reach(ENG, grid, p, yUpCells(cells)).some(q => q.spin === (p === 'T' ? SPIN(pl.state.spin) : q.spin)))
        bad.push(`board ${bi} ${p} ${E.key(cells)} ${pl.state.spin}`);
    }
  });
  return bad;
}

describe('cutcopy drills: the artefact', () => {
  test('rebuilds byte for byte', () => {
    expect(serialise(build())).toBe(committed);
    E.setWindows(WINDOWS);
  }, 1_800_000);

  test('md5s are current and the quarantine flags are set', () => {
    const md5 = (p: string) => createHash('md5').update(readFileSync(`${REPO}/${p}`)).digest('hex');
    for (const [p, h] of Object.entries(A.inputs)) expect(`${p} ${md5(p)}`).toBe(`${p} ${h}`);
    for (const [p, h] of Object.entries(A.code)) expect(`${p} ${md5(p)}`).toBe(`${p} ${h}`);
    expect(Object.keys(A.code)).toEqual(CODE.map(p => relative(REPO, p)));
    expect([A.schema, A.report_eligible, A.constructed, A.practice]).toEqual(['cutcopy-drills/1', false, true, true]);
    expect(A.provenance.garbage_caveat).toContain('seeded-RNG');
  });

  test('the windows are prepare()\'s, both variants, both hands', () => {
    expect(A.windows).toEqual(WINDOWS);
    expect(new Set(A.windows.map((w: any) => `${w.id}/${w.mirrored}`))).toEqual(new Set(['cutcopy/false', 'cutcopy/true', 'uncut/false', 'uncut/true']));
    expect(A.windows.some((w: any) => w.cells.some((c: any) => c.extra))).toBe(true);
  });

  test('the named drills and their difficulty', () => {
    expect(Object.fromEntries(A.drills.map((d: any) => [d.id, [d.difficulty.label, d.difficulty.min]]))).toEqual(DRILLS);
    for (const d of A.drills) expect(d.difficulty.min_by).toBe('practice engine');
  });

  test('every refused candidate is named with its reason', () => {
    expect(Object.fromEntries(A.dropped.map((d: any) => [d.id, d.reason]))).toEqual(DROPPED);
    expect(A.counts).toEqual({ sources: A.counts.sources, drills: A.drills.length, dropped: A.dropped.length });
  });
});

describe('cutcopy drills: per drill', () => {
  for (const d of A.drills) {
    test(`${d.id}: no build at the start, reachable, fires in its variant and hand at need, carries`, () => {
      expect(E.findBuild(E.newRun(d).board)).toBeNull();
      // every solution lock, on the board before it, is reachable by the reference engine with its spin
      const run = E.newRun(d);
      for (const s of d.solution.slice(0, d.need)) {
        const cells = E.cellsOf(s.piece, s.x, s.y, s.r);
        expect(E.legal(run.board, cells)).toBe(true);
        const paths = reach(ENG, yUpGrid(run.board), s.piece, yUpCells(cells));
        expect(paths.length).toBeGreaterThan(0);
        if (s.piece === 'T') expect(paths.some(p => p.spin === SPIN(s.spin))).toBe(true);
        E.applyLock(run, d, stateOf(s));
      }
      // after need pieces: a full T-spin Double the matcher fires, in the stated variant and hand
      const fb = E.findBuild(run.board);
      expect(fb).not.toBeNull();
      const res = E.lock(run.board, fb.state);
      expect([res.spin, res.lines]).toEqual(['full', 2]);
      expect(reach(ENG, yUpGrid(run.board), 'T', yUpCells(res.cells)).some(p => p.spin === 'normal')).toBe(true);
      const P = PREPARED.find(p => p.id === d.target.variant && p.mirrored === d.target.mirrored)!;
      expect(windowMatch(rowsOf(run.board), res.cells.map(([x, y]: number[]) => ({ row: y, col: x })) as any, P)).toBeTruthy();
      expect([fb.m.variant, fb.m.mirrored]).toEqual([d.target.variant, d.target.mirrored]);
      // the follow-up slot carries through the clear (and through any garbage after it)
      E.applyLock(run, d, fb.state);
      expect(run.stage).toBe(1);
      expect(run.slot).not.toBeNull();
      expect(run.slot.length).toBe(4);
      expect(!!E.findSecond(run.board, run.slot)).toBe(d.second);
      // the source a drill names is one of the artefact's inputs
      expect(['corpus', 'selfplay', 'own', 'page']).toContain(d.source.kind);
    });
  }
});

describe('cutcopy drills: the practice engine against the reference', () => {
  test('differential: matchWindow == windowMatch, spin and lines == the reference engine\'s', () => {
    const r = differential();
    expect(r.bad).toEqual([]);
    expect(r.fired).toBeGreaterThan(0);
    expect(r.notFired).toBeGreaterThan(0);
    console.log(`differential: ${DIFF_BOARDS.length} boards, ${r.placements} T placements, ${r.fired} fired, ${r.notFired} not`);
  }, 600_000);

  test('the practice engine\'s placements are a subset of the reference engine\'s', () => {
    expect(subset()).toEqual([]);
  }, 600_000);

  describe('mutants the differential must catch', () => {
    const withWindows = (ws: any[], f: () => void) => { E.setWindows(ws); try { f(); } finally { E.setWindows(WINDOWS); } };
    test('a flipped window cell', () => {
      const ws = structuredClone(WINDOWS);
      const w = ws.find((x: any) => x.id === 'cutcopy' && !x.mirrored);
      w.cells.find((c: any) => c.v === '#').v = '.';
      withWindows(ws, () => expect(differential().bad.length).toBeGreaterThan(0));
    }, 600_000);
    test('a dropped mirror', () => {
      withWindows(WINDOWS.filter((w: any) => !w.mirrored), () => expect(differential().bad.length).toBeGreaterThan(0));
    }, 600_000);
    test('a dropped window_extra cell', () => {
      const ws = structuredClone(WINDOWS).map((w: any) => ({ ...w, cells: w.cells.filter((c: any) => !c.extra) }));
      withWindows(ws, () => expect(differential().bad.length).toBeGreaterThan(0));
    }, 600_000);
    // a kick with its x offsets negated (transition id 4); measured: ids 4, 6, 7, 12, 13 and 14 each break a
    // T placement on the drill boards, the others reach none. A DROPPED kick only removes placements, which the
    // subset check cannot see by construction, so the mutant changes a kick rather than removing one.
    test('a broken kick', () => {
      const KX = E.KICKS[1], id = 4, saved = KX[id];
      KX[id] = saved.map(([dx, dy]: number[]) => [-dx, dy]);
      try { expect(differential().bad.length + subset().length).toBeGreaterThan(0); }
      finally { KX[id] = saved; }
    }, 600_000);
  });
});

describe('cutcopy drills: headless replay', () => {
  for (const d of A.drills) {
    test(`${d.id} passes at exactly need = ${d.need}`, () => {
      expect(firstBuildable(d)).toBe(d.need);
      const run = replayN(d, d.need);
      expect(run.failed).toBeNull();
      const fb = E.findBuild(run.board);
      E.applyLock(run, d, fb.state);
      expect(run.stage).toBe(1);
      if (d.second) {
        const sec = E.findSecond(run.board, run.slot);
        E.applyLock(run, d, sec.state);
        expect(run.done).toBe(true);
      }
    });
  }
});
