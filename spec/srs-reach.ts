/**
 * Can the piece actually GET there?
 *
 * check-boards.ts asked whether each drawn placement is a real tetromino resting on something. That
 * is necessary and nowhere near sufficient: a sealed cavity can have exactly the shape of a piece and
 * still be unreachable, because SRS kicks move a piece by at most two cells from a position it was
 * already legally in.
 *
 * So this does a full reachability search: seed with every collision-free position entirely above the
 * stack (more generous than any real spawn rule), then BFS over left / right / soft-drop / CW / CCW
 * with the SRS kick tables, and report whether the drawn placement is among the positions that can be
 * reached AND locked. If it is reachable, it also reports whether it could only be reached by a
 * rotation — which is what makes a T-spin a spin rather than a drop.
 */
const KICK_JLSTZ: Record<string, [number, number][]> = {
  // (x, y) with y up-positive, exactly as the guideline tables are written
  '0R': [[0, 0], [-1, 0], [-1, 1], [0, -2], [-1, -2]],
  'R0': [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
  'R2': [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
  '2R': [[0, 0], [-1, 0], [-1, 1], [0, -2], [-1, -2]],
  '2L': [[0, 0], [1, 0], [1, 1], [0, -2], [1, -2]],
  'L2': [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
  'L0': [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
  '0L': [[0, 0], [1, 0], [1, 1], [0, -2], [1, -2]],
};
const KICK_I: Record<string, [number, number][]> = {
  '0R': [[0, 0], [-2, 0], [1, 0], [-2, -1], [1, 2]],
  'R0': [[0, 0], [2, 0], [-1, 0], [2, 1], [-1, -2]],
  'R2': [[0, 0], [-1, 0], [2, 0], [-1, 2], [2, -1]],
  '2R': [[0, 0], [1, 0], [-2, 0], [1, -2], [-2, 1]],
  '2L': [[0, 0], [2, 0], [-1, 0], [2, 1], [-1, -2]],
  'L2': [[0, 0], [-2, 0], [1, 0], [-2, -1], [1, 2]],
  'L0': [[0, 0], [1, 0], [-2, 0], [1, -2], [-2, 1]],
  '0L': [[0, 0], [-1, 0], [2, 0], [-1, 2], [2, -1]],
};

type Cells = [number, number][];
const SHAPES: Record<string, Record<string, Cells>> = {
  T: { '0': [[0, 1], [1, 0], [1, 1], [1, 2]], 'R': [[0, 1], [1, 1], [1, 2], [2, 1]],
       '2': [[1, 0], [1, 1], [1, 2], [2, 1]], 'L': [[0, 1], [1, 0], [1, 1], [2, 1]] },
  J: { '0': [[0, 0], [1, 0], [1, 1], [1, 2]], 'R': [[0, 1], [0, 2], [1, 1], [2, 1]],
       '2': [[1, 0], [1, 1], [1, 2], [2, 2]], 'L': [[0, 1], [1, 1], [2, 0], [2, 1]] },
  L: { '0': [[0, 2], [1, 0], [1, 1], [1, 2]], 'R': [[0, 1], [1, 1], [2, 1], [2, 2]],
       '2': [[1, 0], [1, 1], [1, 2], [2, 0]], 'L': [[0, 0], [0, 1], [1, 1], [2, 1]] },
  S: { '0': [[0, 1], [0, 2], [1, 0], [1, 1]], 'R': [[0, 1], [1, 1], [1, 2], [2, 2]],
       '2': [[1, 1], [1, 2], [2, 0], [2, 1]], 'L': [[0, 0], [1, 0], [1, 1], [2, 1]] },
  Z: { '0': [[0, 0], [0, 1], [1, 1], [1, 2]], 'R': [[0, 2], [1, 1], [1, 2], [2, 1]],
       '2': [[1, 0], [1, 1], [2, 1], [2, 2]], 'L': [[0, 1], [1, 0], [1, 1], [2, 0]] },
  O: { '0': [[0, 0], [0, 1], [1, 0], [1, 1]], 'R': [[0, 0], [0, 1], [1, 0], [1, 1]],
       '2': [[0, 0], [0, 1], [1, 0], [1, 1]], 'L': [[0, 0], [0, 1], [1, 0], [1, 1]] },
  I: { '0': [[1, 0], [1, 1], [1, 2], [1, 3]], 'R': [[0, 2], [1, 2], [2, 2], [3, 2]],
       '2': [[2, 0], [2, 1], [2, 2], [2, 3]], 'L': [[0, 1], [1, 1], [2, 1], [3, 1]] },
};
const ST = ['0', 'R', '2', 'L'];
const CW: Record<string, string> = { '0': 'R', 'R': '2', '2': 'L', 'L': '0' };
const CCW: Record<string, string> = { '0': 'L', 'L': '2', '2': 'R', 'R': '0' };

export type Placement = { piece: string; state: string; r: number; c: number };

export function reach(board: string[], piece: string, target: Cells) {
  const H = board.length, W = 10;
  const filled = (r: number, c: number) =>
    c < 0 || c >= W || r >= H ? true : (r < 0 ? false : board[r]![c] !== '.');
  const cellsOf = (s: string, r: number, c: number): Cells =>
    SHAPES[piece]![s]!.map(([dr, dc]) => [r + dr, c + dc] as [number, number]);
  const ok = (s: string, r: number, c: number) => cellsOf(s, r, c).every(([y, x]) => !filled(y, x));
  const key = (s: string, r: number, c: number) => `${s}|${r}|${c}`;
  const kicks = piece === 'I' ? KICK_I : KICK_JLSTZ;

  // where the drawn placement sits, as (state, r, c)
  const want = new Set(target.map(([r, c]) => `${r},${c}`));
  let goal: Placement | null = null;
  for (const s of ST) for (let r = -4; r < H; r++) for (let c = -3; c < W; c++) {
    const cs = cellsOf(s, r, c);
    if (cs.length === 4 && cs.every(([y, x]) => want.has(`${y},${x}`))) { goal = { piece, state: s, r, c }; break; }
  }
  if (!goal) return { ok: false, why: 'the four drawn cells are not any orientation of ' + piece };

  // seed: every collision-free position strictly above the stack
  const topFilled = board.findIndex(row => [...row].some(ch => ch !== '.'));
  const ceiling = topFilled < 0 ? H : topFilled;
  const seen = new Set<string>(), q: [string, number, number][] = [];
  for (const s of ST) for (let c = -3; c < W; c++) {
    const r = -4;
    if (ok(s, r, c) && cellsOf(s, r, c).every(([y]) => y < ceiling)) {
      seen.add(key(s, r, c)); q.push([s, r, c]);
    }
  }

  const rotate = (s: string, r: number, c: number, dir: 'cw' | 'ccw') => {
    const to = dir === 'cw' ? CW[s]! : CCW[s]!;
    for (const [x, y] of kicks[s + to]!) {           // (x, y) -> (dr, dc) = (-y, x)
      const nr = r - y, nc = c + x;
      if (ok(to, nr, nc)) return [to, nr, nc, x, y] as const;
    }
    return null;
  };

  let reachedGoal = false, viaRotationOnly = true, droppedIn = false;
  while (q.length) {
    const [s, r, c] = q.shift()!;
    if (s === goal.state && r === goal.r && c === goal.c) reachedGoal = true;
    const moves: [string, number, number, string][] = [];
    if (ok(s, r, c - 1)) moves.push([s, r, c - 1, 'left']);
    if (ok(s, r, c + 1)) moves.push([s, r, c + 1, 'right']);
    if (ok(s, r + 1, c)) moves.push([s, r + 1, c, 'drop']);
    for (const dir of ['cw', 'ccw'] as const) {
      const k = rotate(s, r, c, dir);
      if (k) moves.push([k[0], k[1], k[2], dir]);
    }
    for (const [ns, nr, nc, how] of moves) {
      if (ns === goal.state && nr === goal.r && nc === goal.c && how !== 'cw' && how !== 'ccw')
        droppedIn = true;
      const kk = key(ns, nr, nc);
      if (!seen.has(kk)) { seen.add(kk); q.push([ns, nr, nc]); }
    }
  }
  if (reachedGoal) viaRotationOnly = !droppedIn;
  const locks = !ok(goal.state, goal.r + 1, goal.c);
  return { ok: reachedGoal && locks, goal, reachedGoal, locks, viaRotationOnly };
}
