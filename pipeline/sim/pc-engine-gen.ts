/**
 * The engine's own movegen for `pc-solver.ts`: every resting placement the vendored Triangle engine
 * can reach (shift, fall, CW, CCW and 180 through its SRS+ kicks), via `route-demos.ts`'s `reach`
 * BFS. `reach` answers one target at a time from a cached whole search, so this asks it for every
 * candidate cell set that lies inside the frame; slower than the SRS movegen, used only to re-check
 * a "no solution" before it is published.
 */
import { createEngine } from './vendor/teto/create-engine.mjs';
import { TL_DEFAULTS } from './oracle-source.ts';
import { DEMO_OPTIONS, reach } from './route-demos.ts';
import { SHAPES, WIDTH } from './emit-replay.ts';

const eng = createEngine({ ...TL_DEFAULTS, ...DEMO_OPTIONS }, 'demo',
  [{ gameid: 'demo', userid: 'demo', username: 'demo' }], new Date('2026-01-01T00:00:00Z')) as any;

export function enginePlacements(rows: number[], piece: string, H: number): number[][] {
  const grid: (string | null)[][] = Array.from({ length: 40 }, (_, y) =>
    Array.from({ length: WIDTH }, (_, x) => ((rows[y] ?? 0) >> x & 1 ? 'g' : null)));
  const out: number[][] = [];
  for (const shape of SHAPES[piece]!) {
    const w = Math.max(...shape.map(c => c[0])) + 1, h = Math.max(...shape.map(c => c[1])) + 1;
    for (let ay = 0; ay + h <= H; ay++) for (let ax = 0; ax + w <= WIDTH; ax++) {
      const cells = shape.map(([dx, dy]) => (ay + dy) * WIDTH + ax + dx);
      if (cells.some(c => grid[Math.floor(c / WIDTH)]![c % WIDTH])) continue;
      // resting: some cell sits on the floor or a filled cell
      if (!cells.some(c => c < WIDTH || grid[Math.floor(c / WIDTH) - 1]![c % WIDTH])) continue;
      if (reach(eng, grid, piece, cells).length) out.push(cells.sort((a, b) => a - b));
    }
  }
  return out;
}
