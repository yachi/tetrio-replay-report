/**
 * The 千鳥格子 (Cut Copy) constructed demos (`analysis/cutcopy-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique cutcopy`; the planner is the shared `technique-demos.ts`, Cut Copy's half is
 * `technique-demos-cutcopy.ts`).
 *
 * NO DEMO IS BUILT, and that is the measurement this file pins. The page draws its terrains grey; each chain is
 * planned, and the planner stops it at its first failing check. This test re-derives every reason from the
 * transcription on its own:
 *
 *   * the third-column build's terrain holds an ODD number of cells, so no board built from empty is it (every
 *     lock adds 4 cells and every clear removes 10) — a proof, not a planner limit;
 *   * the T-hole build's terrain is a multiple of four and has no tiling by tetrominoes AT ALL (re-derived here
 *     by an exact-cover search over all seven kinds, unlimited): the hole cuts its cells into two connected parts,
 *     and the one right of the hole holds six. So it is reachable only through line clears, which this planner
 *     never makes; the planner's own words for it are 「no cover under its dealing」, which is true and weaker;
 *   * the basic form is even but not a multiple of four — a limit of THIS planner, which never clears a line;
 *   * both builds are drawn MIRRORED, so even built, the as-drawn window the planner fires would not fit them
 *     (measured: none as drawn, one mirrored, on each).
 *
 * The profile's own reasons (the boards standing on another board's demo) are checked against the transcription's
 * own fields (`spin_of`, `on`). The day a demo is built, `demos` stops being empty here and the demo page's prose
 * (which says none is) must be re-read.
 *
 * The planner's mutants are all measured EQUIVALENT here (no chain reaches the move search, the arbiter or the
 * spin check) and asserted byte-identical, so the day one starts to matter is a red build.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/cutcopy-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { SHAPES, WIDTH } from '../sim/emit-replay.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { CUTCOPY } from '../sim/technique-profile-cutcopy.ts';
import { CUTCOPY_DEMOS } from '../sim/technique-demos-cutcopy.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/cutcopy-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(CUTCOPY_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === CUTCOPY_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';
const NO_COVER = '地形冇一個由非 T 方塊（每款最多兩粒）砌成嘅鋪法';

/** Boards no demo stands on, and the reason the artefact gives: four are the profile's, four the planner's
 *  measured reasons for its two chains. */
const DEMO_UNBUILT: Record<string, string> = {
  'basic': `基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形：有 34 格，唔係 4 嘅倍數：${LIMIT}`,
  'basic.after': '係 basic.spin 之後嘅盤面（由 second.spin 推出嚟），同一個原因冇示範',
  'basic.spin': '係基本形上面打嘅 TSD：基本形砌唔到，所以呢幅都冇示範',
  'col3.jz': `地形有 25 格，係單數：${ODD}`,
  'col3.terrain': `col3.jz 砌唔到：地形有 25 格，係單數：${ODD}`,
  'hole.osz': NO_COVER,
  'hole.terrain': `hole.osz 砌唔到：${NO_COVER}`,
  'second.spin': '係 basic.after 上面打嘅第二下 TSD，同一個原因冇示範',
};

const fresh = build(CUTCOPY, CUTCOPY_DEMOS);
const count = (id: string, drop = '') => [...drawnCells(byId.get(id).rows, TR.empty_letters).values()]
  .filter(ch => !drop.includes(ch)).length;

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

/** every flat, nub-down T placement on a drawn board at which the window fires, as drawn and mirrored */
function fits(rows: string[]) {
  const board = rows.map((r: string) => [...r].map(ch => ch === '-' ? '.' : 'X').join(''));
  const out = { drawn: 0, mirrored: 0 };
  const [d, m] = prepare(TR, V);
  for (let r = 0; r + 1 < board.length; r++) for (let c = 1; c + 1 < 10; c++) {
    const T = [{ row: r, col: c - 1 }, { row: r, col: c }, { row: r, col: c + 1 }, { row: r + 1, col: c }];
    if (T.some(q => board[q.row]![q.col] !== '.')) continue;
    if (windowMatch(board, T, d!)) out.drawn++;
    if (windowMatch(board, T, m!)) out.mirrored++;
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
  expect(CUTCOPY_DEMOS.chains).toEqual([{ node: 'hole.osz', terrain: 'hole.terrain' },
                                        { node: 'col3.jz', terrain: 'col3.terrain' }]);
});

test('the planner\'s reasons, re-derived from the transcription', () => {
  // the third-column build's terrain: odd, a proof
  expect(count('col3.terrain')).toBe(25);
  // the T-hole build's terrain: a multiple of four with no tiling at all, under the planner's dealing (no T,
  // each kind at most twice, less the page's own O, S and Z) or under none
  const hole = new Set(drawnCells(byId.get('hole.terrain').rows, TR.empty_letters).keys());
  expect(hole.size).toBe(24);
  expect(tilings(hole)).toBe(0);
  expect(tilings(hole, { T: 0, I: 2, J: 2, L: 2, O: 1, S: 1, Z: 1 })).toBe(0);
  // why: the hole cuts it into two connected parts, and neither is a multiple of four
  expect(parts(hole).map(p => p.size).sort((a, b) => a - b)).toEqual([6, 18]);
  // the page's own pieces are exactly one O, one S and one Z
  expect(byId.get('hole.osz').adds).toBe('osz');
  // the control: the same search finds tilings where there are some (a 4x2 block: two I's, two O's, ...)
  expect(tilings(new Set([0, 1, 2, 3, 10, 11, 12, 13]))).toBeGreaterThan(0);
  expect(tilings(new Set([0, 1, 2, 3, 10, 11, 12, 13]), { T: 0, I: 2, J: 2, L: 2, O: 1, S: 1, Z: 1 })).toBeGreaterThan(0);
  // the basic form: even, not a multiple of four, and no page pieces
  expect([...byId.get('basic').rows.join('')].filter((ch: string) => ch !== '-' && ch !== 'c')).toEqual([]);
  expect(count('basic')).toBe(34);
  expect(DEMO_UNBUILT.basic).toContain(`${count('basic')} 格`);
  // both builds are drawn mirrored: the as-drawn window the planner fires does not fit them
  expect(fits(byId.get('hole.osz').rows)).toEqual({ drawn: 0, mirrored: 1 });
  expect(fits(byId.get('col3.jz').rows)).toEqual({ drawn: 0, mirrored: 1 });
  expect(fits(byId.get('basic').rows)).toEqual({ drawn: 1, mirrored: 0 });
  // the profile's reasons: the boards each names, by the transcription's own fields
  expect(byId.get('basic.spin').spin_of).toBe('basic');
  expect(byId.get('second.spin').spin_of).toBe('basic.after');
  expect(byId.get('second.spin').on).toBe('basic.after');
  expect(byId.get('hole.osz').on).toBe('hole.terrain');
  expect(byId.get('col3.jz').on).toBe('col3.terrain');
});

const T = 300_000;

/** MEASURED EQUIVALENT: every chain stops at a check on the drawing itself (no cover under the dealing, or a cell
 *  count), before the planner's move search, its spin check or the engine arbiter, so none of their mutants can
 *  change a byte. Asserted byte-identical: the day a chain gets past those checks, these turn red. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(CUTCOPY, CUTCOPY_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);
