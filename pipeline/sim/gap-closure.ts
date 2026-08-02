/**
 * A SECOND, independent opinion on the forecast count, built from the player's definition rather
 * than from the metric's.
 *
 * `forecast.ts` asks which of a single step's three edits raised the best available T-spin. This
 * asks a different question entirely, in the words the definition is usually given in: *an overhang
 * is placed several rows above a hole; the lines between them clear; it becomes a T-spin hole.*
 * That has an exact geometric signature — the vertical distance between two specific cells, the
 * overhang and the cell the T lands on, can only shrink when a row BETWEEN them is removed. Nothing
 * else in the game moves them relative to one another: filling cells beneath the overhang does not
 * lower it, and garbage lifts both together.
 *
 * Two consequences worth stating, because they are not obvious:
 *
 *   1. "the overhang was set up in advance" and "the slot emerged from a line clear" are the SAME
 *      event, not two independent properties. An overhang placed above its final resting place can
 *      only be brought down by a clear, so one implies the other. Measured over the corpus, the two
 *      predicates agree on all 649 resolvable events with both off-diagonal cells empty.
 *   2. A clear that is itself a T-SPIN does not count. Without that exclusion the test fires 181
 *      times, and 180 of those are one shape: a T-spin triple removing three rows beneath an
 *      overhang laid down in the second bag. That is the C-Spin — "a T-Spin Triple which is usually
 *      followed by a T-Spin Double within three bags" — i.e. the opener, scoring itself as
 *      foresight, which is the confound this whole instrument exists to keep out.
 *
 * With the exclusion the corpus yields exactly one event, and it is the same one `forecastMetric`
 * reaches by localising the mechanism to a single step. The two share no code and no reasoning.
 */
import { H } from './sim.ts';
import type { SimResult } from './sim.ts';
import type { ForecastRecord } from './forecast.ts';

const rowsWithGarbage = (b: (string | null)[][]) =>
  b.reduce((n, row) => n + (row.some(c => c === 'G') ? 1 : 0), 0);

/** what one step did to row positions: which rows filled, and how far garbage lifted the stack */
function stepEffect(r: SimResult, t: number) {
  // lock 0 has no predecessor board; the field before it is empty
  const A = t > 0 ? r.boards[t - 1]! : Array.from({ length: H }, () => new Array(10).fill(null));
  const lk = r.locks[t]!;
  const Bpre = (A as (string | null)[][]).map(x => [...x]);
  for (const c of lk.cells) if (c.row >= 0 && c.row < H) Bpre[c.row]![c.col] = lk.piece;
  const cleared = Bpre.map((row, i) => row.every(x => x !== null) ? i : -1).filter(i => i >= 0);
  const B = Bpre.map(x => [...x]);
  for (const row of [...cleared].reverse()) B.splice(row, 1);
  for (let i = 0; i < cleared.length; i++) B.unshift(new Array(10).fill(null));
  return { cleared, g: rowsWithGarbage(r.boards[t]! as (string | null)[][]) - rowsWithGarbage(B), spin: lk.spin };
}

/** where a cell at `row` sits after step t; null if that step's clear destroyed it */
const forward = (row: number, cleared: number[], g: number) =>
  cleared.includes(row) ? null : row + cleared.filter(c => c > row).length - g;

/**
 * Follow one cell from the step that placed it to just before `to`.
 *
 * `locks[from].cells` are PRE-clear, PRE-garbage coordinates, so the placing step's own effect has
 * to be applied before the walk starts. Omitting it lost 38 of 654 events — 30 of them purely
 * because garbage rose on the same step the overhang landed — and those losses looked like
 * untrackable data rather than like a bug.
 */
function follow(r: SimResult, row: number, from: number, to: number): number[] | null {
  const e0 = stepEffect(r, from);
  const start = forward(row, e0.cleared, e0.g);
  if (start === null || start < 0 || start >= H) return null;
  const path = [start];
  for (let t = from + 1; t <= to; t++) {
    const e = stepEffect(r, t);
    const n = forward(path[path.length - 1]!, e.cleared, e.g);
    if (n === null || n < 0 || n >= H) return null;
    path.push(n);
  }
  return path;
}

export interface GapClosure {
  /** rows removed from between the overhang and the landing cell by ORDINARY clears */
  plainRows: number;
  /** rows removed by clears that were themselves T-spins — excluded from the verdict */
  spinRows: number;
  /** the definition's verdict: the lines between them cleared, and not by a T-spin */
  forecast: boolean;
}

/**
 * Returns null when the pair cannot be identified — chiefly when the T lands on GARBAGE, which has
 * no placing lock to trace. That is a real hole rather than a rounding error: 5 events of 654 sit
 * in it, two of them with garbage that is load-bearing at execution, so this instrument is silent
 * on exactly the case the wiki calls "in anticipation of an empty garbage column".
 */
export function gapClosure(r: SimResult, rec: ForecastRecord): GapClosure | null {
  const k = rec.lockIndex, j = rec.roofFrom;
  if (j == null || j < 0) return null;
  const lk = r.locks[k]!, exec = r.boards[k - 1]!, prov = r.provSnaps[k - 1]!;

  let roofRow = -1, col = -1;
  for (const cell of lk.cells) {
    const above = cell.row - 1;
    if (above >= 0 && prov[above]![cell.col] === j) { roofRow = above; col = cell.col; break; }
  }
  if (roofRow < 0) return null;

  let floorRow = -1;
  for (let y = roofRow + 1; y < H; y++) if (exec[y]![col] != null) { floorRow = y; break; }
  if (floorRow < 0) return null;
  const f = prov[floorRow]![col]!;
  if (f < 0) return null;                      // the landing cell is garbage — see the note above

  // A lock may place several cells in one column, so identify by which one ENDS in the right
  // place rather than by provenance alone. Provenance is shared; the path is not.
  const pick = (lock: number, end: number) => {
    for (const cell of r.locks[lock]!.cells) {
      if (cell.col !== col) continue;
      const p = follow(r, cell.row, lock, k - 1);
      if (p && p[p.length - 1] === end) return p;
    }
    return null;
  };
  const roofPath = pick(j, roofRow), floorPath = pick(f, floorRow);
  if (!roofPath || !floorPath) return null;

  const t0 = Math.max(j, f);
  let plainRows = 0, spinRows = 0;
  for (let t = t0 + 1; t <= k - 1; t++) {
    const e = stepEffect(r, t);
    if (!e.cleared.length) continue;
    const a = roofPath[t - 1 - j]!, b = floorPath[t - 1 - f]!;   // positions BEFORE this step
    const between = e.cleared.filter(cr => cr > Math.min(a, b) && cr < Math.max(a, b)).length;
    if (e.spin !== 'none') spinRows += between; else plainRows += between;
  }
  return { plainRows, spinRows, forecast: plainRows > 0 };
}
