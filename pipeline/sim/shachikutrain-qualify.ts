/**
 * Which 社畜トレイン (Shachiku Train) hits were BUILT as one, not merely shaped like one: the profile's
 * `qualify` hook (`technique-profile.ts`), read by `technique-facts.ts`'s `assemble`. The window says the
 * shape stood at the T; these four rules, agreed with yachi on 2026-10-23 while reviewing the hit list,
 * say whether the shape is the page's technique. A hit failing any of them stays in `hits` (the shape
 * did stand) with `qualifies: false` and every rule it fails named in `not_qualified`.
 *
 *   1. `fragment` / `garbage_in_shape`: the cells the page draws as its S and L (`basic.spin`'s `s` and
 *      `l`, mirrored with the window) are each a cell of a COMPLETE piece — all four of its cells still
 *      on the board before the T — never a fragment a line clear left, and never garbage. Every drawing
 *      on shiwehi.com and harddrop builds the shape from whole pieces; a shape pieced together from what
 *      clears and garbage left is the shape by accident.
 *   2. `kaidan_window`: the 階段のドネイト (Kaidan) window does not fire at the same T. The two windows
 *      clash on no cell (kaidan.test.ts, SHACHIKUTRAIN_ALSO_KAIDAN), so a lock both fire on is read as a
 *      Kaidan, never as both.
 *   3. `dpc`: no Perfect Clear within `DPC_LOCKS` locks before or after the T. A TSD fired a few pieces
 *      after the board was emptied is the DPC setup (the pieces left after a Perfect Clear opener built into a
 *      TSD and a second Perfect Clear), and one that empties the board shortly after is that setup completed;
 *      either way it is not the page's two-TSD donation. The window cannot tell them apart: every hit that
 *      passed rules 1 and 2 when this was measured had emptied the board at lock 19 and fired its T at lock 27
 *      to 29, and none of them reached the second Perfect Clear (the per-hit evidence is the artefact's).
 *
 * Piece ownership is tracked through the digest's own row map (cells in, cleared rows out, garbage rows
 * pushed in under, exactly `digestSession`'s `mapOk` rule), and every step must reproduce the board the
 * matcher read: ownership at the hit is checked cell for cell against the T's board-before, and a step the
 * row map could not verify makes the hit `ownership_unverified` rather than guessed.
 */
import type { Hit, TechDigest } from './technique-facts.ts';
import { loadTranscription, prepare, windowMatch } from './technique-facts.ts';

const H = 40, W = 10;
/** two 7-bags: a DPC's Perfect Clear comes within the bag after its TSD */
export const DPC_LOCKS = 14;

export interface QualifyMutants { allowFragments?: boolean; allowGarbage?: boolean; noKaidan?: boolean; noDpc?: boolean; dpcAfterOnly?: boolean;
                                  dpcLocks?: number }

/** The S and L cells of the page's spin board, relative to the T's nub, as drawn. */
export function shapeOffsets(tr: any): { dr: number; dc: number; letter: string }[] {
  const v = tr.variants[0];
  const rows: string[] = tr.nodes.find((n: any) => n.id === v.board).rows;
  const tc: [number, number][] = v.t_cells;
  const nr = Math.max(...tc.map(([r]) => r)), nc = tc.find(([r]) => r === nr)![1];
  const out: { dr: number; dc: number; letter: string }[] = [];
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) {
    const ch = rows[r]![c]!;
    if (ch === 's' || ch === 'l') out.push({ dr: r - nr, dc: c - nc, letter: ch });
  }
  return out;
}

/** The owner grid after each lock from 0 to `upTo`, stopping before the first lock whose row map the
 *  digest could not verify (`bad`). -2 is empty, -1 garbage, k the lock that placed the cell. */
export function owners(d: TechDigest, upTo: number): { boards: number[][][]; bad: number | null } {
  let g: number[][] = Array.from({ length: H }, () => new Array(W).fill(-2));
  const boards: number[][][] = [];
  for (let k = 0; k <= upTo && k < d.locks.length; k++) {
    const lk = d.locks[k]!;
    if (!lk.mapOk) return { boards, bad: k };
    for (const q of lk.cells) if (q.row >= 0 && q.row < H && q.col >= 0 && q.col < W) g[q.row]![q.col] = k;
    const cl = new Set(lk.clearedRows);
    const kept = g.filter((_, i) => !cl.has(i));
    while (kept.length < H) kept.unshift(new Array(W).fill(-2));
    g = kept.slice(lk.garbage);
    // a garbage row, hole included: the digest records how many rows, not where the hole is
    for (let i = 0; i < lk.garbage; i++) g.push(new Array(W).fill(-1));
    boards.push(g.map(r => [...r]));
  }
  return { boards, bad: null };
}

export function qualifier(transcriptionPath: string, kaidanPath: string, mut: QualifyMutants = {}) {
  const tr = loadTranscription(transcriptionPath);
  const shape = shapeOffsets(tr);
  const kd = loadTranscription(kaidanPath);
  const kPreps = kd.variants.flatMap((v: any) => prepare(kd, v));
  const dpcLocks = mut.dpcLocks ?? DPC_LOCKS;
  return (h: Hit, d: TechDigest): { qualifies: boolean; not_qualified: string[] } => {
    const reasons: string[] = [];
    const lk = d.locks[h.lock]!;
    const t = d.tspins.find(x => x.i === h.lock)!;
    // ownership up to the T and DPC_LOCKS past it; up to the lock before the T it must be verified, and
    // it must be the board the matcher read
    const own = owners(d, h.lock + dpcLocks);
    if (own.bad !== null && own.bad < h.lock) return { qualifies: false, not_qualified: ['ownership_unverified'] };
    const g = h.lock > 0 ? own.boards[h.lock - 1]! : Array.from({ length: H }, () => new Array(W).fill(-2));
    for (let r = 0; r < H; r++) for (let c = 0; c < W; c++) {
      const ch = t.board[r]![c]!, o = g[r]![c]!;
      // a garbage row's hole is read as garbage here (the digest records rows, not hole columns)
      const ok = ch === '.' ? o === -2 || (o === -1 && t.board[r]!.includes('G')) : ch === 'G' ? o === -1 : o >= 0 && d.locks[o]!.piece === ch;
      if (!ok) throw new Error(`shachikutrain qualify: ${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock}: `
        + `ownership disagrees with the board at ${r},${c} (${ch} vs ${o})`);
    }
    // 1. the S and L cells: complete pieces only
    const nub = lk.cells.reduce((a, b) => b.row > a.row ? b : a);
    const sgn = h.mirrored ? -1 : 1;
    const count = new Map<number, number>();
    for (const row of g) for (const o of row) if (o >= 0) count.set(o, (count.get(o) ?? 0) + 1);
    let frag = false, garb = false, empty = false;
    for (const x of shape) {
      const o = g[nub.row + x.dr]![nub.col + sgn * x.dc]!;
      if (o === -1) garb = true;
      // the window requires these cells filled, so this fires only under a matcher mutant that weakens it
      else if (o < 0) empty = true;
      else if (count.get(o)! < 4) frag = true;
    }
    if (empty) reasons.push('shape_cell_empty');
    if (frag && !mut.allowFragments) reasons.push('fragment');
    if (garb && !mut.allowGarbage) reasons.push('garbage_in_shape');
    // 2. the Kaidan window at the same T
    if (!mut.noKaidan && kPreps.some((P: any) => !!windowMatch(t.board, lk.cells, P))) reasons.push('kaidan_window');
    // 3. a Perfect Clear within DPC_LOCKS locks before or after the T (after: as far as the row map is
    //    verified; before: the board at a lock before the T, verified above)
    if (!mut.noDpc) {
      const empty = (k: number) => own.boards[k]!.every(row => row.every(o => o === -2));
      for (let k = Math.max(0, h.lock - dpcLocks); k <= h.lock + dpcLocks && k < own.boards.length; k++)
        if ((k >= h.lock || !mut.dpcAfterOnly) && empty(k)) { reasons.push('dpc'); break; }
    }
    return { qualifies: reasons.length === 0, not_qualified: reasons };
  };
}
