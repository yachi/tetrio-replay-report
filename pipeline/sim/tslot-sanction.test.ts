/**
 * The unsupported-spin sanction in `tslot-sanction.ts`, on the board that needed it, plus two
 * controls. The cross-check that motivated it (`cross-tslot-count.ts`) needs the cc-oracle binary,
 * so it runs only in CI's oracle-image job; this test pins the classification without it.
 */
import { expect, test } from 'bun:test';
import { H } from './sim.ts';
import { anySpinLines, classify, floatingSpinLines } from './tslot-sanction.ts';

// 2026-11-27 `replay-2026-11-27-01.ttrm` r3 pinglamb board 36 (rows 27-39; everything above empty).
const ROWS = [
  '..X.......', '..XX......', 'XXXX......', 'XXX......X', 'XXX.XXXX.X', 'XXX..XXXXX',
  'XXX..XXXXX', 'XXX.XXXXXX', 'XXX.XXXXXX', 'XXX.XXXXXX', 'XXX.XXXXXX', 'XXX.XXXXXX', 'XXX.XXXXXX',
];
function board(rows: string[]): (string | null)[][] {
  const b: (string | null)[][] = Array.from({ length: H }, () => Array(10).fill(null));
  rows.forEach((r, i) => { b[H - rows.length + i] = [...r].map(c => (c === 'X' ? 'X' : null)); });
  return b;
}

test('the 11-27 board: no resting spin, one unsupported spin completing a line, sanctioned', () => {
  const b = board(ROWS);
  expect(anySpinLines(b)).toBeNull();
  expect(floatingSpinLines(b)).toBe(1);
  const s = classify(b);
  expect(s.stackTop).toBe(27);
  expect(s.sanctioned).toBe(true);
  expect(s.reason).toContain('unsupported');
});

test('control: close the cell under the T and the spin rests, so it is a reachable spin, not a floating one', () => {
  const rows = [...ROWS];
  rows[6] = 'XXX.XXXXXX'; // r33 c4 filled
  const b = board(rows);
  expect(anySpinLines(b)).not.toBeNull();
  expect(classify(b).reason).toContain('IS reachable');
});

test('control: a tall board with no spin position at all stays an unsanctioned false negative', () => {
  const b = board(Array(13).fill('XXXXX.....'));
  expect(anySpinLines(b)).toBeNull();
  expect(floatingSpinLines(b)).toBeNull();
  expect(classify(b).sanctioned).toBe(false);
});
