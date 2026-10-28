/**
 * The Double Dagger constructed demos (`analysis/doubledagger-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique doubledagger`; the planner is the shared `technique-demos.ts`, Double Dagger's half is
 * `technique-demos-doubledagger.ts`).
 *
 * NO DEMO IS BUILT, and that is the measurement this file pins. The page draws its terrains grey; each chain
 * is planned, and the planner stops it at its first failing check. This test re-derives every reason from
 * the transcription on its own:
 *
 *   * the TSD-shape build's terrain (the TSD shape plus the muted stack the page tells the player to fill)
 *     and the bare cross hold an ODD number of cells, so no board built from empty is either of them (every
 *     lock adds 4 cells and every clear removes 10) — a proof, not a planner limit;
 *   * the basic form, the cross-shape build's terrain and the three feature boards are even but not multiples
 *     of four — a limit of THIS planner, which never clears a line, worded as one;
 *   * the cross-shape build is drawn MIRRORED, so even built, the as-drawn window the planner fires would not
 *     fit it (measured: none as drawn, one mirrored).
 *
 * The profile's own reasons (the boards standing on another board's demo, the インペリアルクロス board that is
 * not this technique) are checked against the transcription's own fields (`spin_of`, `after_of`, `on`,
 * `same_occupancy_as`, the variant's `misses` and `not_expressed`). The day a demo is built, `demos` stops
 * being empty here and the demo page's prose (which says none is) must be re-read.
 *
 * The planner's mutants are all measured EQUIVALENT here (no chain reaches the move search, the arbiter or
 * the spin check) and asserted byte-identical, so the day one starts to matter is a red build.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/doubledagger-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { encodePlace } from '../sim/emit-replay.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { DOUBLEDAGGER } from '../sim/technique-profile-doubledagger.ts';
import { DOUBLEDAGGER_DEMOS } from '../sim/technique-demos-doubledagger.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/doubledagger-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(DOUBLEDAGGER_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === DOUBLEDAGGER_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';

/** Boards no demo stands on, and the reason the artefact gives: thirteen are the profile's, four the
 *  planner's measured reasons for its two chains. */
const DEMO_UNBUILT: Record<string, string> = {
  'basic': `基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形（暗灰格當空）：有 34 格，唔係 4 嘅倍數：${LIMIT}`,
  'basic.after': '係 basic.spin 之後嘅盤面，同一個原因冇示範',
  'basic.spin': '係基本形上面打嘅 T：基本形砌唔到，所以呢幅都冇示範',
  'cross.imperial': '呢幅係インペリアルクロス，唔係呢個手法；佢企喺 cross.imperial.terrain 上面',
  'cross.imperial.terrain': 'cross.imperial 嘅地形：cross.imperial 唔係呢個手法，所以冇示範',
  'cross.terrain': `十字形元地形有 25 格，係單數：${ODD}`,
  'cross.z': `地形有 30 格，唔係 4 嘅倍數：${LIMIT}`,
  'cross.z.terrain': `cross.z 砌唔到：地形有 30 格，唔係 4 嘅倍數：${LIMIT}`,
  'line.after': '係 line.spin 之後嘅盤面，同一個原因冇示範',
  'line.spin': `係特徵圖，冇畫頁面嘅方塊：拎走粒 T 之後有 42 格，唔係 4 嘅倍數：${LIMIT}；而且個窗口喺呢幅唔對到（兩個位中間有一行）`,
  'multi': `係特徵圖，冇畫頁面嘅方塊：有 58 格，唔係 4 嘅倍數：${LIMIT}`,
  'tetris.after': '係 tetris.spin 之後嘅盤面，同一個原因冇示範',
  'tetris.spin': `係特徵圖，冇畫頁面嘅方塊：拎走條 I 之後有 70 格，唔係 4 嘅倍數：${LIMIT}`,
  'tsd.pink': '係 TSD 形元地形標住粉紅格嘅同一幅（佔格一樣），同一個原因冇示範',
  'tsd.sj': `地形有 27 格，係單數：${ODD}`,
  'tsd.sj.terrain': `tsd.sj 砌唔到：地形有 27 格，係單數：${ODD}`,
  'tsd.terrain': 'TSD 形元地形本身冇呢個手法（個窗口喺度唔對到）；示範要企嘅係 tsd.sj 連埋原頁叫人隨便填嗰啲淺色格嘅地形，嗰幅點解砌唔到寫喺 tsd.sj 度',
};

const fresh = build(DOUBLEDAGGER, DOUBLEDAGGER_DEMOS);
const count = (id: string, drop = '') => [...drawnCells(byId.get(id).rows, TR.empty_letters).values()]
  .filter(ch => !drop.includes(ch)).length;
const cells = (rows: string[], letters: string) => [...drawnCells(rows, TR.empty_letters)]
  .filter(([, ch]) => letters.includes(ch)).map(([c]) => c).sort((a, b) => a - b);
/** every T placement on a drawn board at which the window fires, as drawn and mirrored */
function fits(rows: string[]) {
  const board = rows.map((r: string) => [...r].map(ch => ch === '-' || TR.empty_letters.includes(ch) ? '.' : 'X').join(''));
  const out = { drawn: 0, mirrored: 0 };
  const seen = new Set<string>();
  for (let r = 0; r + 1 < board.length; r++) for (let c = 1; c + 1 < 10; c++) {
    const T = [{ row: r, col: c - 1 }, { row: r, col: c }, { row: r, col: c + 1 }, { row: r + 1, col: c }];
    if (T.some(q => board[q.row]![q.col] !== '.') || seen.has(`${r},${c}`)) continue;
    seen.add(`${r},${c}`);
    const [d, m] = prepare(TR, V);
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
  expect(DOUBLEDAGGER_DEMOS.chains).toEqual([{ node: 'tsd.sj', terrain: 'tsd.sj.terrain' },
                                             { node: 'cross.z', terrain: 'cross.z.terrain' }]);
});

test('the planner\'s reasons, re-derived from the transcription', () => {
  // the two chains' terrains: odd (a proof) and even but not 4n (a planner limit)
  expect(count('tsd.sj.terrain')).toBe(27);
  expect(count('cross.z.terrain')).toBe(30);
  // their page pieces are whole pieces of their letters, so the cell count is the first thing that fails
  const sj = byId.get('tsd.sj').rows, cz = byId.get('cross.z').rows;
  expect(() => encodePlace('S', cells(sj, 's'))).not.toThrow();
  expect(() => encodePlace('J', cells(sj, 'j'))).not.toThrow();
  expect(() => encodePlace('Z', cells(cz, 'z'))).not.toThrow();
  // the cross-shape build is drawn mirrored: the as-drawn window the planner fires does not fit it
  expect(fits(cz)).toEqual({ drawn: 0, mirrored: 1 });
  expect(fits(sj)).toEqual({ drawn: 1, mirrored: 0 });
  // the boards with no page pieces, each with the count its reason prints (B and p read as empty; a spin
  // board less its spin piece)
  const none = (id: string) => [...byId.get(id).rows.join('')].filter((ch: string) => /[a-z]/.test(ch) && !'cp'.includes(ch));
  for (const id of ['basic', 'tetris.spin', 'line.spin', 'multi', 'cross.terrain']) expect(none(id), id).toEqual([]);
  expect(count('basic')).toBe(34);
  expect(count('cross.terrain')).toBe(25);
  expect(count('multi')).toBe(58);
  expect(count('tetris.spin', 'Ii')).toBe(70);
  expect(count('line.spin', 'Tt')).toBe(42);
  for (const [id, n] of [['basic', 34], ['multi', 58], ['tetris.spin', 70], ['line.spin', 42]] as const) {
    expect(n % 2).toBe(0);
    expect(n % 4).not.toBe(0);
    expect(DEMO_UNBUILT[id]).toContain(`${n} 格`);
  }
  expect(count('cross.terrain') % 2).toBe(1);
  // the profile's reasons: the boards each names, by the transcription's own fields
  expect(byId.get('basic.spin').spin_of).toBe('basic');
  expect(byId.get('basic.after').after_of).toBe('basic.spin');
  expect(byId.get('tetris.after').after_of).toBe('tetris.spin');
  expect(byId.get('line.after').after_of).toBe('line.spin');
  expect(byId.get('tsd.pink').same_occupancy_as).toBe('tsd.terrain');
  expect(byId.get('cross.imperial').on).toBe('cross.imperial.terrain');
  expect(V.misses).toContain('cross.imperial');
  expect(V.misses).toContain('tsd.terrain');
  expect(V.not_expressed.map((e: any) => e.board)).toEqual(['line.spin']);
});

const T = 300_000;

/** MEASURED EQUIVALENT: every chain stops at a cell count, before the planner's move search, its spin check or
 *  the engine arbiter, so none of their mutants can change a byte. Asserted byte-identical: the day a chain gets
 *  past those checks, these turn red. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(DOUBLEDAGGER, DOUBLEDAGGER_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);
