/**
 * The boards drawn for spec/ForecastExamples.dfy, checked against the rules of the game.
 *
 * The Dafny file proves what the DEFINITION says about seven situations. It says nothing about
 * whether those situations can occur, because it models rows and not geometry — and a board that
 * cannot occur is a worked example that teaches something false.
 *
 * Two gates, in increasing strength:
 *
 *   1. consistency — ten columns wide, the rows marked `clears` are exactly the complete ones, each
 *      panel follows from the one before it by the single edit it claims (a lock, a splice, or a
 *      garbage insert), and each added piece is a real tetromino orientation resting on something.
 *
 *   2. reachability — the piece can actually GET there, under SRS with its kick tables. This is the
 *      one that matters: a sealed cavity can have exactly the shape of a piece and still be
 *      impossible to enter, because a kick moves a piece at most two cells from a position it was
 *      already legally in. The first board drawn for example D failed here — its T-Spin Triple well
 *      was walled on all four sides — and no amount of shape checking would have caught it.
 */
import { test, expect } from 'bun:test';
import { EXAMPLES } from './example-boards.ts';
import { reach } from './srs-reach.ts';

const W = 10;
const full = (row: string) => ![...row].some(ch => ch === '.');
const alignBottom = (a: string[], b: string[]) => {
  const n = Math.min(a.length, b.length);
  return [a.slice(a.length - n), b.slice(b.length - n)] as const;
};

const BASE: Record<string, string[]> = {
  I: ['XXXX'], O: ['XX', 'XX'], T: ['XXX', '.X.'], S: ['.XX', 'XX.'],
  Z: ['XX.', '.XX'], J: ['X..', 'XXX'], L: ['..X', 'XXX'],
};
const rot = (g: string[]): string[] => {
  const h = g.length, w = g[0]!.length;
  return Array.from({ length: w }, (_, r) => Array.from({ length: h }, (_, c) => g[h - 1 - c]![r]!).join(''));
};
const norm = (cells: [number, number][]) => {
  const r0 = Math.min(...cells.map(c => c[0])), c0 = Math.min(...cells.map(c => c[1]));
  return cells.map(([r, c]) => `${r - r0},${c - c0}`).sort().join(' ');
};
const SHAPES: Record<string, Set<string>> = {};
for (const [p, base] of Object.entries(BASE)) {
  SHAPES[p] = new Set();
  let g = base;
  for (let i = 0; i < 4; i++) {
    const cells: [number, number][] = [];
    g.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'X') cells.push([r, c]); }));
    SHAPES[p]!.add(norm(cells));
    g = rot(g);
  }
}

/** The cells panel `i` adds to panel `i-1`, and the board they were added to. */
const placement = (ex: any, i: number) => {
  const p = ex.panels[i], prev = ex.panels[i - 1];
  const grow = p.rows.length - prev.rows.length;
  const board = grow > 0 ? [...Array(grow).fill('.'.repeat(W)), ...prev.rows] : [...prev.rows];
  const added: [number, number][] = [];
  for (let r = 0; r < p.rows.length; r++) for (let c = 0; c < W; c++)
    if (p.rows[r][c] === p.add && board[r]![c] === '.') added.push([r, c]);
  return { board, added, piece: (p.add as string).toUpperCase() };
};

for (const ex of EXAMPLES as any[]) {
  test(`example ${ex.id}: every panel is a legal board`, () => {
    ex.panels.forEach((p: any, i: number) => {
      const at = `${ex.id}.${i + 1}`;
      for (const row of p.rows) expect(`${at} ${row}`).toBe(`${at} ${row.slice(0, W)}`);
      for (const row of p.rows) expect(row.length).toBe(W);

      // the `clears` list is a claim about the panel, so it must match the panel
      const complete = p.rows.map((r: string, n: number) => full(r) ? n : -1).filter((n: number) => n >= 0);
      expect({ at, complete }).toEqual({ at, complete: p.clears ?? [] });

      if (p.hole) expect(`${at} ${p.rows[p.hole[0]][p.hole[1]]}`).toBe(`${at} .`);
      if (p.floor) expect(p.rows[p.floor[0]][p.floor[1]]).not.toBe('.');
      if (p.roof) {
        expect(p.rows[p.roof[0]][p.roof[1]]).not.toBe('.');
        expect(`${at} under the overhang: ${p.rows[p.roof[0] + 1]?.[p.roof[1]]}`)
          .toBe(`${at} under the overhang: .`);
      }
      if (i === 0) return;

      const prev = ex.panels[i - 1];
      if (p.add) {
        const { added, piece } = placement(ex, i);
        const [a, b] = alignBottom(prev.rows, p.rows);
        for (let r = 0; r < a.length; r++) for (let c = 0; c < W; c++)
          if (a[r]![c] !== b[r]![c])
            expect(`${at} (${r},${c}) ${a[r]![c]}->${b[r]![c]}`).toBe(`${at} (${r},${c}) .->${p.add}`);
        expect(`${at} cells added`).toBe(`${at} cells added`);
        expect(added.length).toBe(4);
        expect(`${at} ${norm(added)}`).toBe(`${at} ${[...SHAPES[piece]!].find(s => s === norm(added))}`);
      } else if (prev.clears?.length) {
        const want = prev.rows.filter((_: string, r: number) => !prev.clears.includes(r));
        expect(`${at}\n` + p.rows.join('\n')).toBe(`${at}\n` + want.join('\n'));
      } else {
        // garbage rises: the previous board sits unchanged on top of new rows with one hole each
        expect(p.rows.length).toBeGreaterThan(prev.rows.length);
        expect(p.rows.slice(0, prev.rows.length)).toEqual(prev.rows);
        for (const row of p.rows.slice(prev.rows.length)) {
          expect([...row].filter(ch => ch === '.').length).toBe(1);
          expect([...row].every(ch => ch === '.' || ch === 'G')).toBe(true);
        }
      }
    });
  });

  test(`example ${ex.id}: every piece can be got there`, () => {
    ex.panels.forEach((p: any, i: number) => {
      if (!p.add) return;
      const { board, added, piece } = placement(ex, i);
      const res: any = reach(board, piece, added);
      expect(`${ex.id}.${i + 1} ${piece} reachable`).toBe(`${ex.id}.${i + 1} ${piece} reachable`);
      expect({ at: `${ex.id}.${i + 1}`, piece, reachable: res.ok }).toEqual(
        { at: `${ex.id}.${i + 1}`, piece, reachable: true });
      // a T-spin is a spin because the piece could not have been dropped or slid into place
      if (piece === 'T' && (p.clears?.length ?? 0) >= 2)
        expect({ at: `${ex.id}.${i + 1}`, rotationOnly: res.viaRotationOnly }).toEqual(
          { at: `${ex.id}.${i + 1}`, rotationOnly: true });
    });
  });
}

test('the Event separations in the Dafny lemmas are the ones the boards draw', () => {
  for (const ex of EXAMPLES as any[]) {
    const first = ex.panels.find((p: any) => p.roof && p.floor);
    if (!first) continue;
    const m = /roofAt := (\d+), floorAt := (\d+)/.exec(ex.event)!;
    expect({ id: ex.id, sep: Number(m[2]) - Number(m[1]) })
      .toEqual({ id: ex.id, sep: first.floor[0] - first.roof[0] });
  }
});
