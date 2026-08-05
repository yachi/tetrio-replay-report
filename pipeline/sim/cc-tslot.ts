/**
 * cold-clear's T-slot detectors, ported from MinusKelvin/cold-clear
 * `bot/src/evaluation/standard.rs` (the `detect_shape!` macro and its six invocations).
 *
 * WHY THIS EXISTS. Every figure the forecast metric publishes rests on `bestTspin` — `improved`,
 * `availAtRoof`, `availAtSpin`, the mechanism walk. Until now `bestTspin` had exactly one
 * implementation and no outside check: `vendor/core/srs.ts` is vendored from the author's own
 * td-opener-trainer, so the rotation layer was self-checking. This is a SECOND METHOD for the same
 * question, arrived at differently — cold-clear matches a taxonomy of named shapes against column
 * heights; we search reachable placements with a BFS and test each resting position.
 *
 * WHAT IT IS NOT. cold-clear's taxonomy is a bot heuristic and deliberately not exhaustive, so
 * "ours finds a slot and this does not" is expected and carries no information (588 boards). The
 * informative direction is the reverse: a shape it recognises that our search cannot reach.
 *
 * Nor is it cold-clear's whole evaluation. `cave_tslot` is omitted — it needs `sonic_drop` and the
 * piece's rotation state rather than a static pattern. So is `cutout_tslot`, which computes how
 * many lines the slot would clear; this reports presence only.
 *
 * ONE DIFFERENCE OF DEFINITION, and it accounts for every disagreement measured. cold-clear scores
 * `tslot[result.lines]` with the array indexed from ZERO — a slot clearing nothing is still worth 8
 * to it. `bestTspinLines` requires at least one line. Across 7,544 verified corpus boards the two
 * disagreed on 73, and on all 73 our engine does find a reachable T-spin that happens to clear no
 * line. Genuine disagreements: none.
 *
 * COORDINATES. cold-clear is y-UP with y=0 the bottom row, and `occupied()` returns true for the
 * walls (x outside 0..9) and the floor (y<0), false above the stack. Ours is row 0 at the top of a
 * 40-row board. Both conversions are below and are the easiest thing here to get wrong.
 *
 * PROVENANCE CAVEAT. This port has not been run against the Rust original — that would need a
 * cargo toolchain. Its column-height convention is unit-tested, and a liveness assertion pins how
 * often it fires, because a port that silently detected nothing would agree with everything.
 */
const H = 40, W = 10;
export const occ = (b: any[][], x: number, y: number): boolean => {
  if (x < 0 || x >= W) return true;          // wall
  if (y < 0) return true;                    // floor
  if (y >= H) return false;                  // sky
  return b[H - 1 - y]![x] !== null;
};
export const colHeight = (b: any[][], x: number): number => {
  for (let r = 0; r < H; r++) if (b[r]![x] !== null) return H - r;
  return 0;
};

type Spec = {
  name: string;
  nCols: number;                                        // width of the column-height window
  require: (b: any[][], x: number, h: number[]) => boolean;
  startY: (h: number[]) => number;
  rows: string[];                                       // '#' filled, '_' empty, '?' don't care
};

/* h[] is the height window starting at x. The macro binds only the NAMED slots; '_' in the
 * heights list is a don't-care column, so the indices below follow each shape's own list. */
const SHAPES: Spec[] = [
  { name: 'sky_tslot_right', nCols: 3,                      // heights [_ h1 h2]
    require: (_b, _x, h) => h[1]! <= h[2]! - 1,
    startY: h => h[2]! + 1,
    rows: ['#??', '_??', '#??'] },
  { name: 'sky_tslot_left', nCols: 3,                       // heights [h1 h2 _]
    require: (_b, _x, h) => h[1]! <= h[0]! - 1,
    startY: h => h[0]! + 1,
    rows: ['??#', '??_', '??#'] },
  { name: 'tst_twist_left', nCols: 3,                       // heights [h1 h2 _]
    require: (b, x, h) => h[0]! <= h[1]! && occ(b, x - 1, h[1]!) === occ(b, x - 1, h[1]! + 1),
    startY: h => h[1]! + 1,
    rows: ['??#', '??_', '??_', '?__', '??_'] },
  { name: 'tst_twist_right', nCols: 3,                      // heights [_ h1 h2]
    require: (b, x, h) => h[2]! <= h[1]! && occ(b, x + 3, h[1]!) === occ(b, x + 3, h[1]! + 1),
    startY: h => h[1]! + 1,
    rows: ['#??', '_??', '_??', '__?', '_??'] },
  { name: 'fin_left', nCols: 4,                             // heights [h1 h2 _ _]
    require: (_b, _x, h) => h[0]! <= h[1]! + 1,
    startY: h => h[1]! + 2,
    rows: ['??##?', '??__?', '??__#', '??__?', '??#_#'] },
  { name: 'fin_right', nCols: 4,                            // heights [_ _ h1 h2]
    require: (b, x, h) => h[3]! <= h[2]! + 1 && occ(b, x - 1, h[2]!) && occ(b, x - 1, h[2]! - 2),
    startY: h => h[2]! + 2,
    rows: ['##??', '__??', '__??', '__??', '_#??'] },
];

/** every detector that fires on this board */
export function ccTslots(b: any[][]): string[] {
  const heights = Array.from({ length: W }, (_, x) => colHeight(b, x));
  const hit: string[] = [];
  for (const s of SHAPES) {
    for (let x = 0; x + s.nCols <= W; x++) {
      const h = heights.slice(x, x + s.nCols);
      if (!s.require(b, x, h)) continue;
      let y = s.startY(h), ok = true;
      for (const row of s.rows) {
        for (let i = 0; i < row.length && ok; i++) {
          const ch = row[i]!;
          if (ch === '?') continue;
          if (occ(b, x + i, y) !== (ch === '#')) ok = false;
        }
        if (!ok) break;
        y -= 1;
      }
      if (ok) { hit.push(`${s.name}@${x}`); break; }
    }
  }
  return hit;
}
