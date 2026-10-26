/**
 * THE DONATION RULE that 基本的なドネイト (basic donating) is matched by, in place of a window (yachi, 2026-10-26:
 * 「Donation 係少少架空切tspin，遮住窿，架空，但TSpin後會開返啲遮左嘅窿」; 「冇main hole 都得，但架空完再TSpin 要清返
 * 架空咗嘅piece」). A piece is laid over empty cells so that it overhangs them inside the rows the T-spin clears; the
 * clear takes the overhang away and the cells under it are open from the top again. Any column, any depth, any
 * distance from the T: the page draws holes 1 to 6 columns from the T's arm, and the windows that matched those
 * distances alone (k1..k6) are retired.
 *
 * Frame: the 40-row board BEFORE the lock, row 0 the top. `withT` is that board with the lock's cells added; `C` the
 * rows the lock clears. A column c DONATES when, at the topmost cell e of c that is empty, outside C and directly under
 * a cell of C:
 *   1. every filled cell of c above e lies in C (so after the clear c is empty from the top down to e and below);
 *   2. each of those cells is the T or a cell of a COMPLETE piece — all four of its cells on the board before the T,
 *      never garbage (yachi, 2026-10-25: 「要完整pieces」);
 *   3. the cell directly above e is not the T: a hole covered only by the T's own nub is a plain T-spin (yachi,
 *      2026-10-26: 「呢個係普通tspin」).
 * The covering piece may keep cells above C (yachi, 2026-10-26: 「算」) as long as rule 1 holds in column c; a column
 * whose covering pieces all lie inside C is `cover: 'cleared'`, otherwise `cover: 'kept'`. A lock DONATES when at least
 * one column does. Which column is the hit's own (its payoff well and its thumbnail): the nearest to the T's columns,
 * then the leftmost.
 *
 * The ablations relax one rule each, for the controls: `allow_t_nub` drops rule 3, `allow_fragment` drops rule 2,
 * `no_reopen` drops rule 1. The occupancy half (rules 1 and 3) has a Python twin, `technique_transcription.rule_fires`,
 * which the facts test holds to this one over every board of the transcription (ownership is not drawn, so the twin
 * cannot read rule 2).
 */
import { owners } from './shachikutrain-qualify.ts';
import type { Cell, TechDigest } from './technique-facts.ts';

const H = 40, W = 10;

export type RuleAblation = 'allow_t_nub' | 'allow_fragment' | 'no_reopen';
export const RULE_ABLATIONS: RuleAblation[] = ['allow_t_nub', 'allow_fragment', 'no_reopen'];

export interface DonationColumn {
  col: number;
  /** the topmost empty cell under the overhang, row 0 the top */
  hole_row: number;
  /** empty cells from the hole down to the first filled cell or the floor (garbage filled) */
  depth: number;
  cover: 'cleared' | 'kept';
}

export interface RuleMatch {
  columns: DonationColumn[];
  /** the hit's own column's hole cell (the payoff's well) */
  well: { r: number; c: number };
  /** the thumbnail box: the T, the hit's column from the row over C to the row under its hole */
  box: { rows: [number, number]; cols: [number, number] };
}

/**
 * Every donating column at one lock. `own` is the ownership grid before the lock (`owners`: -2 empty, -1 garbage, a
 * lock index otherwise) or null when it could not be verified, in which case rule 2 cannot be read and no column
 * donates (unless it is ablated).
 */
export function donationColumns(withT: boolean[][], tcells: Cell[], C: Set<number>, own: number[][] | null,
                                abl?: RuleAblation): DonationColumn[] {
  const isT = new Set(tcells.map(q => q.row * W + q.col));
  const size = new Map<number, number>();
  const rowsOf = new Map<number, Set<number>>();
  if (own) for (let r = 0; r < H; r++) for (let c = 0; c < W; c++) {
    const k = own[r]![c]!;
    if (k < 0) continue;
    size.set(k, (size.get(k) ?? 0) + 1);
    (rowsOf.get(k) ?? rowsOf.set(k, new Set()).get(k)!).add(r);
  }
  const out: DonationColumn[] = [];
  for (let c = 0; c < W; c++) {
    let e = -1;
    for (let r = 1; r < H; r++) if (!withT[r]![c] && !C.has(r) && withT[r - 1]![c] && C.has(r - 1)) { e = r; break; }
    if (e < 0) continue;
    if (isT.has((e - 1) * W + c) && abl !== 'allow_t_nub') continue;
    let ok = true, kept = false;
    for (let r = 0; r < e && ok; r++) {
      if (!withT[r]![c]) continue;
      if (!C.has(r) && abl !== 'no_reopen') { ok = false; break; }
      if (isT.has(r * W + c)) continue;
      if (abl === 'allow_fragment') continue;
      if (!own) { ok = false; break; }
      const k = own[r]![c]!;
      if (k < 0 || size.get(k) !== 4) { ok = false; break; }
      if ([...rowsOf.get(k)!].some(x => !C.has(x))) kept = true;
    }
    if (!ok) continue;
    let depth = 0;
    for (let r = e; r < H && !withT[r]![c]; r++) depth++;
    out.push({ col: c, hole_row: e, depth, cover: kept ? 'kept' : 'cleared' });
  }
  return out;
}

/** The hit at one lock, or null: the donating columns, the hit's own column (the nearest to the T, then the leftmost)
 *  and its thumbnail box. */
export function ruleMatch(withT: boolean[][], tcells: Cell[], C: Set<number>, own: number[][] | null,
                          abl?: RuleAblation): RuleMatch | null {
  const cols = donationColumns(withT, tcells, C, own, abl);
  if (!cols.length) return null;
  const tc = tcells.map(q => q.col), tr = tcells.map(q => q.row);
  const lo = Math.min(...tc), hi = Math.max(...tc);
  const dist = (c: number) => c < lo ? lo - c : c > hi ? c - hi : 0;
  const own0 = [...cols].sort((a, b) => dist(a.col) - dist(b.col) || a.col - b.col)[0]!;
  const top = Math.min(...tr, ...[...C]) - 1;
  const r0 = Math.max(0, top), r1 = Math.min(H - 1, Math.max(Math.max(...tr), own0.hole_row) + 1);
  return { columns: cols, well: { r: own0.hole_row, c: own0.col },
           box: { rows: [r0, r1], cols: [Math.min(lo, own0.col), Math.max(hi, own0.col)] } };
}

/** The detector a profile hands the matcher: ownership is read once per digest (`owners`, verified step by step). */
export function donationDetector() {
  const cache = new WeakMap<TechDigest, ReturnType<typeof owners>>();
  return (d: TechDigest, i: number, withT: boolean[][], cells: Cell[], rows: number[], abl?: RuleAblation) => {
    let o = cache.get(d);
    if (!o) { o = owners(d, d.locks.length - 1); cache.set(d, o); }
    const own = i === 0 ? Array.from({ length: H }, () => new Array(W).fill(-2))
      : (o.bad !== null && o.bad <= i - 1) ? null : o.boards[i - 1]!;
    return ruleMatch(withT, cells, new Set(rows), own, abl);
  };
}
