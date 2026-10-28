/**
 * The 欄干 (Parapet) constructed demos (`analysis/parapet-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique parapet`; the planner is the shared `technique-demos.ts`, Parapet's half is
 * `technique-demos-parapet.ts`).
 *
 * NO DEMO IS BUILT, and that is the measurement this file pins. The page draws its terrains grey; the one chain (the
 * O-roof basic form) is planned, and the planner stops it at its first failing check. This test re-derives every
 * reason from the transcription on its own:
 *
 *   * the O-roof form's terrain is a multiple of four and has no tiling by tetrominoes AT ALL (re-derived here by an
 *     exact-cover search over all seven kinds, unlimited): the well under the slot and the L's stem cut its cells
 *     into two connected parts, and neither holds a multiple of four. So it is reachable only through line clears,
 *     which this planner never makes; the planner's own words for it are 「no cover under its dealing」, which is true
 *     and weaker;
 *   * the Z-roof form's terrain is even but not a multiple of four — a limit of THIS planner, which never clears a
 *     line — and the four boards the page draws on that form (the TSD, the TSS and what each leaves) stand on it.
 *
 * THE PAYOFF BRANCH, EXERCISED. A variant with a payoff in place of a follow-up ends its demo on the stood T; that is
 * a shared-planner branch (`technique-demos.ts`, `tail`) that no committed chain reaches, so it is run here on a
 * SYNTHETIC copy of the transcription whose O-roof terrain we widened until it tiles (written to a temporary file,
 * never committed or published): the engine arbiter accepts the plan, the demo ends on one full TSD, nothing is
 * swapped out of the hold for a second T, and every board it claims it stands on is on its own decoded timeline.
 *
 * The planner's mutants are all measured EQUIVALENT on the committed artefact (no chain reaches the move search, the
 * arbiter or the spin check) and asserted byte-identical, so the day one starts to matter is a red build.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/parapet-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { build, serialise, drawnCells, reachProblems, type DemoMutants } from '../sim/technique-demos.ts';
import { SHAPES, WIDTH } from '../sim/emit-replay.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { PARAPET } from '../sim/technique-profile-parapet.ts';
import { PARAPET_DEMOS } from '../sim/technique-demos-parapet.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/parapet-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(PARAPET_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === PARAPET_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const NO_COVER = '地形冇一個由非 T 方塊（每款最多兩粒）砌成嘅鋪法';
const ON_Z = '企喺 Z 頂嘅基本形（basic.z）上面：嗰幅砌唔到，所以呢幅都冇示範';

/** Boards no demo stands on, and the reason the artefact gives: six are the profile's, two the planner's measured
 *  reason for its one chain. */
const DEMO_UNBUILT: Record<string, string> = {
  'basic.o': NO_COVER,
  'basic.o.terrain': `basic.o 砌唔到：${NO_COVER}`,
  'basic.z': `佢嘅元地形（basic.z.terrain）有 30 格，唔係 4 嘅倍數：${LIMIT}`,
  'basic.z.terrain': `Z 頂基本形嘅元地形有 30 格，唔係 4 嘅倍數：${LIMIT}`,
  'tsd.after': '係 tsd.spin 之後嘅盤面，同一個原因冇示範',
  'tsd.spin': `TSD ${ON_Z}`,
  'tss.after': '係 tss.spin 之後嘅盤面，同一個原因冇示範',
  'tss.spin': `TSS ${ON_Z}`,
};

const fresh = build(PARAPET, PARAPET_DEMOS);
const count = (id: string) => drawnCells(byId.get(id).rows, TR.empty_letters).size;

/** Every tiling of `cells` (y-UP engine indices) by tetrominoes, at most `limit[kind]` of each kind (absent:
 *  unlimited; 0: none). */
function tilings(cells: Set<number>, limit: Record<string, number> = {}, cap = 1000): number {
  let n = 0;
  const go = (left: Set<number>, used: Record<string, number>) => {
    if (n >= cap) return;
    if (!left.size) { n++; return; }
    const low = [...left].sort((a, b) => Math.floor(a / WIDTH) - Math.floor(b / WIDTH) || a - b)[0]!;
    const seen = new Set<string>();
    for (const kind of Object.keys(SHAPES)) {
      if ((used[kind] ?? 0) >= (limit[kind] ?? Infinity)) continue;
      for (const shape of SHAPES[kind]!) for (const [ox, oy] of shape) {
        const ax = (low % WIDTH) - ox, ay = Math.floor(low / WIDTH) - oy;
        const cs = shape.map(([dx, dy]: [number, number]) => [ax + dx, ay + dy]);
        if (cs.some(([x]) => x < 0 || x >= WIDTH)) continue;
        const idx = cs.map(([x, y]) => y * WIDTH + x).sort((a, b) => a - b);
        if (seen.has(`${kind}:${idx.join()}`) || !idx.every(c => left.has(c))) continue;
        seen.add(`${kind}:${idx.join()}`);
        go(new Set([...left].filter(c => !idx.includes(c))), { ...used, [kind]: (used[kind] ?? 0) + 1 });
      }
    }
  };
  go(cells, {});
  return n;
}

/** The 4-connected parts of a set of cells (y-UP engine indices). */
function parts(cells: Set<number>): Set<number>[] {
  const left = new Set(cells), out: Set<number>[] = [];
  while (left.size) {
    const first = [...left][0]!, part = new Set<number>([first]), stack = [first];
    left.delete(first);
    while (stack.length) {
      const c = stack.pop()!, x = c % WIDTH;
      for (const n of [x > 0 ? c - 1 : -1, x < WIDTH - 1 ? c + 1 : -1, c - WIDTH, c + WIDTH])
        if (n >= 0 && left.has(n)) { left.delete(n); part.add(n); stack.push(n); }
    }
    out.push(part);
  }
  return out;
}

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(fresh)).toBe(committedText);
});

test('quarantined and constructed; no demo built; every board unbuilt exactly once with its reason', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.demos).toEqual([]);
  const unbuilt = Object.fromEntries(committed.unbuilt.map((u: any) => [u.node, u.reason]));
  expect(Object.entries(unbuilt).sort()).toEqual(Object.entries(DEMO_UNBUILT).sort());
  expect(committed.unbuilt.length).toBe(TR.nodes.length);
  expect(Object.keys(unbuilt).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
  expect(PARAPET_DEMOS.chains).toEqual([{ node: 'basic.o', terrain: 'basic.o.terrain' }]);
  expect(PARAPET_DEMOS.variant).toBe('parapet');
});

test('the planner\'s reasons, re-derived from the transcription', () => {
  // the O-roof terrain: a multiple of four with no tiling at all, under the planner's dealing (no T, each kind at
  // most twice) or under none
  const o = new Set(drawnCells(byId.get('basic.o.terrain').rows, TR.empty_letters).keys());
  expect(o.size).toBe(32);
  expect(tilings(o)).toBe(0);
  expect(tilings(o, { T: 0, I: 2, J: 2, L: 2, O: 2, S: 2, Z: 2 })).toBe(0);
  // why: the well and the L's stem cut it into two connected parts, and neither is a multiple of four
  expect(parts(o).map(p => p.size).sort((a, b) => a - b)).toEqual([7, 25]);
  // the control: the same search finds tilings where there are some (a 4x2 block)
  expect(tilings(new Set([0, 1, 2, 3, 10, 11, 12, 13]))).toBeGreaterThan(0);
  // the Z-roof terrain: even, not a multiple of four
  expect(count('basic.z.terrain')).toBe(30);
  expect(DEMO_UNBUILT['basic.z.terrain']).toContain(`${count('basic.z.terrain')} 格`);
  expect(DEMO_UNBUILT['basic.z']).toContain(`${count('basic.z.terrain')} 格`);
  // the page's pieces: an L and the roof (a Z, or an O)
  expect([byId.get('basic.z').adds, byId.get('basic.o').adds]).toEqual(['lz', 'lo']);
  expect([byId.get('basic.z').on, byId.get('basic.o').on]).toEqual(['basic.z.terrain', 'basic.o.terrain']);
  // the profile's reasons: the boards each names, by the transcription's own fields
  expect([byId.get('tsd.spin').spin_of, byId.get('tss.spin').spin_of]).toEqual(['basic.z', 'basic.z']);
  expect([byId.get('tsd.after').after_of, byId.get('tss.after').after_of]).toEqual(['tsd.spin', 'tss.spin']);
  // the window the planner fires fits the O-roof form once, as drawn
  const board = byId.get('basic.o').rows.map((r: string) => [...r].map(ch => ch === '-' ? '.' : 'X').join(''));
  const T = V.t_cells.map(([row, col]: number[]) => ({ row, col }));
  expect(prepare(TR, V).map(P => !!windowMatch(board, T, P))).toEqual([true, false]);
});

const T = 300_000;

/** MEASURED EQUIVALENT: the one chain stops at a check on the drawing itself (no cover), before the planner's move
 *  search, its spin check or the engine arbiter, so none of their mutants can change a byte. Asserted byte-identical:
 *  the day the chain gets past those checks, these turn red. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(PARAPET, PARAPET_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);

/** A synthetic transcription: Parapet's, with the O-roof terrain widened (column 0 from row 1 down, and three cells
 *  right of the roof) so it tiles. Never committed, never published: it exists to run the payoff branch. */
function synthetic(): { path: string; dir: string } {
  const tr = JSON.parse(JSON.stringify(TR));
  const set = (id: string, rows: string[]) => { tr.nodes.find((n: any) => n.id === id).rows = rows; };
  set('basic.o', ['c---oo----', 'cl--oo-ccc', 'cl---ccccc', 'cll-cccccc', 'cc-ccccccc', 'cc-ccccccc']);
  set('basic.o.terrain', ['c---------', 'c------ccc', 'c----ccccc', 'c---cccccc', 'cc-ccccccc', 'cc-ccccccc']);
  const dir = mkdtempSync(`${tmpdir()}/parapet-demos-`);
  const path = `${dir}/synthetic-technique.json`;
  writeFileSync(path, JSON.stringify(tr));
  return { path, dir };
}

test('the payoff branch on a synthetic terrain: the demo ends on one full TSD, nothing swapped out for a second T', () => {
  const { path, dir } = synthetic();
  try {
    const out = build(PARAPET, { ...PARAPET_DEMOS, transcriptionPath: path });
    expect(out.demos.length).toBe(1);
    const d = out.demos[0];
    const tr = JSON.parse(readFileSync(path, 'utf8'));
    expect(reachProblems(tr, tr.variants.find((v: any) => v.id === 'parapet'), d)).toEqual([]);
    expect(d.followup_lock).toBeNull();
    expect(d.stood_lock).toBe(d.locks.length - 1);
    expect(d.roles.endsWith('S')).toBe(true);
    expect(d.roles.includes('F')).toBe(false);
    expect(d.swap).toBe('');
    expect(d.events).toEqual([{ lock: d.stood_lock, kind: 'TSD', spin: 2, lines: 2 }]);
    expect(d.reaches.map((r: any) => [r.node, r.check])).toEqual([['basic.o.terrain', 'board'], ['basic.o', 'board']]);
    for (const b of d.bags) expect([...b].sort().join('')).toBe('IJLOSTZ');
    // the mutant the arbiter exists for: the terrain's pieces not played, the plan refused
    expect(() => build(PARAPET, { ...PARAPET_DEMOS, transcriptionPath: path }, { baseSeeded: true })).toThrow();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}, T);
