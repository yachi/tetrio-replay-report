/**
 * The `y` field on a garbage ige event is a per-attack BOARD-ROW oracle.
 *
 * Derived in probe-ige-y.ts and asserted here:
 *
 *     y === lowestClearedRow - floor((lines - 1) / 2)
 *
 * i.e. the vertical centre of the cleared block, rounded toward the bottom — matching the
 * row at which the client draws the outgoing attack. Evidence (verified-prefix attacks,
 * delta from lowestClearedRow): lines=1 +0 in 10/11; lines=2 +0 in 150/167; lines=3 -1 in
 * 84/87 including 71/71 for full T-spins; lines=4 -1 in 21/29.
 *
 * Why this matters: the attack stream alone gives ~1.7 pre-garbage events per ~19 pieces
 * and only constrains (frame, amount). Adding y constrains WHERE ON THE BOARD the clear
 * happened, so a sim that produces the right attack from the wrong row is now caught.
 * The deviations above are exactly those cases.
 *
 * Caveat on provenance: the rule was read off runs where the sim already matched frame and
 * amount, so it could in principle encode a shared error. Two things argue against that —
 * the majority is overwhelming and clean (71/71), and the residuals are heavy-tailed
 * (+4/+5/+6), which is the shape of occasional sim errors, not of a mis-stated rule.
 */
export function expectedIgeY(lowestClearedRow: number, lines: number): number {
  return lowestClearedRow - Math.floor((lines - 1) / 2);
}

/** Does a sim clear record agree with the ground-truth event's y? */
export function matchesIgeY(clearedRows: number[], lines: number, y: number): boolean {
  if (!clearedRows.length) return false;
  return expectedIgeY(Math.max(...clearedRows), lines) === y;
}
