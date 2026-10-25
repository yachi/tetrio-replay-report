/**
 * The two donation-shaped technique tests' shared half (欄干's `parapet.test.ts` and 階段のドネイト's
 * `kaidan.test.ts`): the scored T-spin loop as the matcher scores it, and harddrop's Donation predicate
 * re-implemented from `emit-opener-facts.ts`'s `donationCols` at its shipped clauses (importing that file runs a
 * session). Written once so the two tests ask one question one way; unhashed, so no artefact moves with it.
 *
 * Since 2026-10-25 (yachi: follow harddrop, but complete pieces) there is no T-column exclusion, and a plug cell in
 * the cleared rows that is not the T must belong to a piece whose four cells are all on the board: `own` is the
 * ownership grid before the T (`shachikutrain-qualify.ts`'s `owners`, -1 garbage, -2 empty, k the lock index), and
 * `null` when the digest cannot reproduce it, which fails the clause rather than passing it.
 */
import type { TechDigest, Cell } from '../sim/technique-facts.ts';

export const H = 40;
export const W = 10;

/** Every scored T-spin, exactly as the matcher scores it: inside the prefix, the reconstruction agreeing on a
 *  non-empty set of rows. */
export function scored(d: TechDigest) {
  const out: { i: number; rows: number[]; lk: TechDigest['locks'][number]; board: string[]; withT: boolean[][] }[] = [];
  for (const t of d.tspins) {
    if (t.i > d.v) continue;
    const lk = d.locks[t.i]!;
    const withT = t.board.map(s => [...s].map(x => x !== '.'));
    for (const q of lk.cells) withT[q.row]![q.col] = true;
    const rows: number[] = [];
    for (let r = 0; r < H; r++) if (withT[r]!.every(Boolean)) rows.push(r);
    const theirs = [...lk.clearedRows].sort((a, b) => a - b);
    if (rows.length !== theirs.length || !rows.every((x, k) => x === theirs[k]) || !rows.length) continue;
    out.push({ i: t.i, rows, lk, board: t.board, withT });
  }
  return out;
}

/** DONATION (harddrop.com/wiki/Donation): the verdict for one column, or the first clause it fails. */
export function donationVerdict(withT: boolean[][], cleared: number[], t: Cell[], c: number,
                                own: number[][] | null) {
  const inC = new Set(cleared);
  let inR = 0, outR = 0;
  for (let r = 0; r < H; r++) { if (!withT[r]![c]) continue; inC.has(r) ? inR++ : outR++; }
  if (inR === 0) return 'naive';
  if (outR > 0) return 'filled_above_window';
  let lowest = -1;
  for (let r = 0; r < H; r++) if (withT[r]![c]) lowest = r;
  let cav = 0;
  for (let r = lowest + 1; r < H; r++) if (!withT[r]![c]) cav++;
  if (cav < 4) return 'cavity_lt4';
  const deep: number[] = [];
  for (let r = H - 1; r > lowest && deep.length < 4; r--) if (!withT[r]![c]) deep.push(r);
  if (!deep.every(r => (c === 0 || withT[r]![c - 1]) && (c === W - 1 || withT[r]![c + 1]))) return 'not_walled';
  const isT = new Set(t.map(q => q.row * W + q.col));
  for (const r of cleared) {
    if (isT.has(r * W + c)) continue;
    const k = own?.[r]?.[c];
    if (k === undefined || k < 0) return 'incomplete';
    let n = 0;
    for (const row of own!) for (const v of row) if (v === k) n++;
    if (n !== 4) return 'incomplete';
  }
  return 'donation';
}
