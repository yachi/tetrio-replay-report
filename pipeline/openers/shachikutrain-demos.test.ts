/**
 * The 社畜トレイン (Shachiku Train) constructed demos (`analysis/shachikutrain-demos.json`, from
 * `pipeline/sim/emit-technique-demos.ts --technique shachikutrain`; the planner is the shared `technique-demos.ts`,
 * Shachiku Train's half is `technique-demos-shachikutrain.ts`).
 *
 * NO DEMO IS BUILT, and that is the measurement this file pins. The page draws its terrains grey; each chain is
 * planned, and the planner stops it at its first failing check. This test re-derives every reason from the
 * transcription on its own:
 *
 *   * the basic form's terrain and the TST-terrain build's hold an ODD number of cells, so no board built from empty
 *     is either (every lock adds 4 cells and every clear removes 10) — a proof, not a planner limit;
 *   * the STSD-terrain build's terrain is a multiple of four and HAS tilings by tetrominoes (re-derived here, all
 *     seven kinds, unlimited), but none under the planner's dealing (each kind at most twice in two bags, less the
 *     page's own Z, O, S and L, no T) — a limit of the dealing, worded by the planner as one;
 *   * DT社畜 draws three cells of its L (the fourth is under the drawing's bottom edge), so the planner cannot read
 *     its pieces; and it is drawn MIRRORED, so even built, the as-drawn window the planner fires would not fit it
 *     (measured: none as drawn, one mirrored);
 *   * the 4x2 build is not a chain: its terrain has no tiling AT ALL (the hollow cuts it into two connected parts of
 *     six cells each), which is the profile's reason; given the chain, the planner would stop earlier, at the pale S
 *     (`r`), which it reads as a piece R — measured here, and the reason it is not a chain.
 *
 * The profile's own reasons (the boards standing on another board) are checked against the transcription's own
 * fields (`on`, `after_of`). The day a demo is built, `demos` stops being empty here and the demo page's prose
 * (which says none is) must be re-read.
 *
 * The planner's mutants are all measured EQUIVALENT here (no chain reaches the move search, the arbiter or the
 * spin check) and asserted byte-identical, so the day one starts to matter is a red build.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/shachikutrain-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { SHAPES, WIDTH } from '../sim/emit-replay.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { SHACHIKUTRAIN } from '../sim/technique-profile-shachikutrain.ts';
import { SHACHIKUTRAIN_DEMOS } from '../sim/technique-demos-shachikutrain.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/shachikutrain-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(SHACHIKUTRAIN_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === SHACHIKUTRAIN_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';
const NO_COVER = '地形冇一個由非 T 方塊（每款最多兩粒）砌成嘅鋪法';
const W4 = `元地形有 12 格，係 4 嘅倍數，但中間個窪將佢分開做左右兩舊、每舊 6 格，冇一個由方塊鋪得出嘅鋪法：${LIMIT}`;
const DT = '頁面嘅 L 畫咗 3 格，唔係一粒';

/** Boards no demo stands on, and the reason the artefact gives: the planner's measured reasons for its four chains,
 *  the profile's for the 4x2 build and for every board standing on another. */
const DEMO_UNBUILT: Record<string, string> = {
  'basic': `basic.build 砌唔到：地形有 41 格，係單數：${ODD}`,
  'basic.build': `地形有 41 格，係單數：${ODD}`,
  'basic.roofed': '係 basic.spin 消完行再加一粒 Z 嘅盤面（由 basic.second 推出嚟），同一個原因冇示範',
  'basic.second': '係 basic.roofed 上面打嘅第二下 TSD，同一個原因冇示範',
  'basic.spin': '係 basic.build 上面打嘅 TSD：basic.build 砌唔到，所以呢幅都冇示範',
  'dt': DT,
  'dt.terrain': `dt 砌唔到：${DT}`,
  't3': `t3.build 砌唔到：地形有 29 格，係單數：${ODD}`,
  't3.after': '係 t3.spin 消完行之後嘅盤面，同一個原因冇示範',
  't3.build': `地形有 29 格，係單數：${ODD}`,
  't3.spin': '係 t3.build 上面打嘅 TSD：t3.build 砌唔到，所以呢幅都冇示範',
  'u2': `u2.build 砌唔到：${NO_COVER}`,
  'u2.after': '係 u2.spin 消完行之後嘅盤面，同一個原因冇示範',
  'u2.build': NO_COVER,
  'u2.spin': '係 u2.build 上面打嘅 TSD：u2.build 砌唔到，所以呢幅都冇示範',
  'w4': `w4.build 砌唔到：${W4}`,
  'w4.build': W4,
  'w4.roofed': '係 w4.spin 消完行再加一粒 I 同一粒 Z 嘅盤面（由 w4.second 推出嚟），同一個原因冇示範',
  'w4.second': '係 w4.roofed 上面打嘅第二下 TSD，同一個原因冇示範',
  'w4.spin': '係 w4.build 上面打嘅 TSD：w4.build 砌唔到，所以呢幅都冇示範',
};

const fresh = build(SHACHIKUTRAIN, SHACHIKUTRAIN_DEMOS);
const cellsOf = (id: string) => new Set(drawnCells(byId.get(id).rows, TR.empty_letters).keys());

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
  expect(SHACHIKUTRAIN_DEMOS.chains).toEqual([{ node: 'basic.build', terrain: 'basic' },
                                              { node: 'u2.build', terrain: 'u2' },
                                              { node: 't3.build', terrain: 't3' },
                                              { node: 'dt', terrain: 'dt.terrain' }]);
});

test('the planner\'s reasons, re-derived from the transcription', () => {
  // the basic form's terrain and the TST build's: odd, a proof
  expect(cellsOf('basic').size).toBe(41);
  expect(cellsOf('t3').size).toBe(29);
  // the STSD build's terrain: tileable in general, not under the planner's dealing (no T, each kind at most twice,
  // less the page's own Z, O, S and L)
  const u2 = cellsOf('u2');
  expect(u2.size).toBe(28);
  expect(parts(u2).map(p => p.size).sort((a, b) => a - b)).toEqual([8, 20]);
  expect(tilings(u2)).toBeGreaterThan(0);
  expect(tilings(u2, { T: 0, I: 2, J: 2, L: 1, O: 1, S: 1, Z: 1 })).toBe(0);
  expect(byId.get('u2.build').adds).toBe('losz');
  // the control: the same search finds tilings where there are some (a 4x2 block)
  expect(tilings(new Set([0, 1, 2, 3, 10, 11, 12, 13]), { T: 0, I: 2, J: 2, L: 1, O: 1, S: 1, Z: 1 })).toBeGreaterThan(0);
  // DT社畜: three L cells, and drawn mirrored (the as-drawn window does not fit it)
  expect([...byId.get('dt').rows.join('')].filter((ch: string) => ch === 'l').length).toBe(3);
  expect(fits(byId.get('dt').rows)).toEqual({ drawn: 0, mirrored: 1 });
  expect(fits(byId.get('basic.build').rows)).toEqual({ drawn: 1, mirrored: 0 });
  // the 4x2 build's terrain: no tiling at all, two parts of six
  const w4 = cellsOf('w4');
  expect(w4.size).toBe(12);
  expect(parts(w4).map(p => p.size)).toEqual([6, 6]);
  expect(tilings(w4)).toBe(0);
  expect(DEMO_UNBUILT['w4.build']).toContain(`${w4.size} 格`);
  // ... and given it as a chain, the planner stops at the pale S first (why it is not a chain)
  const { w4: _a, 'w4.build': _b, ...rest } = SHACHIKUTRAIN_DEMOS.unbuilt;
  const asChain = build(SHACHIKUTRAIN, { ...SHACHIKUTRAIN_DEMOS, unbuilt: rest,
    chains: [...SHACHIKUTRAIN_DEMOS.chains, { node: 'w4.build', terrain: 'w4' }] });
  expect(asChain.unbuilt.find((u: any) => u.node === 'w4.build')!.reason).toBe('頁面嘅 R 唔係 R 嘅形');
  expect(byId.get('w4.build').adds).toContain('r');
  // the profile's reasons: the boards each names, by the transcription's own fields
  for (const [id, on] of [['basic.spin', 'basic.build'], ['basic.second', 'basic.roofed'], ['w4.spin', 'w4.build'],
                          ['w4.second', 'w4.roofed'], ['u2.spin', 'u2.build'], ['t3.spin', 't3.build']])
    expect(byId.get(id).on, id).toBe(on);
  expect(byId.get('u2.after').after_of).toBe('u2.spin');
  expect(byId.get('t3.after').after_of).toBe('t3.spin');
  expect(byId.get('dt').on).toBe('dt.terrain');
});

const T = 300_000;

/** MEASURED EQUIVALENT: every chain stops at a check on the drawing itself (a cell count, a piece, no cover under
 *  the dealing), before the planner's move search, its spin check or the engine arbiter, so none of their mutants
 *  can change a byte. Asserted byte-identical: the day a chain gets past those checks, these turn red. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(SHACHIKUTRAIN, SHACHIKUTRAIN_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);
