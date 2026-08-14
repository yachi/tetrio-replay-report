// Two structural claims about the board-state predicates of pipeline/sim/emit-opener-facts.ts,
// stated and PROVED rather than measured:
//
//   1. The NAIVE Donation clause ("the well column is filled through the rows the spin cleared",
//      the `inR > 0` half of line 277) is ENTAILED by the cleared-rows-are-full precondition that
//      both call sites establish (emit-opener-facts.ts:511-516 via the reconstruction gate, and
//      dualVerdict :222-224 by construction). It therefore holds at EVERY column of EVERY scored
//      clear and carries no discriminating power: deleting it from the per-column accept condition
//      changes nothing (NaiveConjunctRedundant). The re-opening clause (`outR == 0`) is NOT
//      entailed — the mutation script proves the asymmetry by checking that the same lemma with
//      the re-opening clause deleted instead FAILS to verify.
//
//   2. The STMB cave's ROOF test is vacuous: the row directly above the cave (`under - 1`) is
//      `max(cleared)`, a row the Double just completed, which the same precondition makes FULL —
//      so every column of the board is roofed at that row (RoofForced, stated for ANY column
//      range, not just cave runs), and conjoining a roof test to the cave predicate yields an
//      equivalent predicate (RoofCannotDiscriminate).
//
// HONESTY NOTES, so the lemmas are read for what they are:
//   - The precondition `ClearedRowsFull` is established at both CALL SITES, not inside
//     `donationCols` / `caveAt` themselves. A future caller passing cleared rows that are not
//     full in `withT` would make the naive clause discriminating again; the lemmas say nothing
//     about that caller.
//   - RoofForced does not need the MAXIMALITY of `under - 1`, only its membership in `cleared`
//     (any full row above the run roofs it). `IsMaxCleared` is kept because caveAt:307 computes
//     `under = Math.max(...cleared) + 1`, and the spec mirrors the code, not the weakest
//     hypothesis. The same goes for `|cleared| == 2` (caveAt:306).
//   - `Walled` / `CavityCount` / `TSlotExcluded` appear identically on both sides of the
//     equivalences, so no lemma depends on their internals; they are mirrored so the accept
//     condition proved about is the one the code runs, not a tidied-up fragment of it.
module OpenerBoard {

  const DONATION_CAVITY: nat := 4      // emit-opener-facts.ts:163
  const DONATION_WALLED_ROWS: nat := 4 // emit-opener-facts.ts:167
  const CAVE_MIN_WIDTH: nat := 3       // emit-opener-facts.ts:170

  type Grid = seq<seq<bool>>

  datatype Cell = Cell(row: int, col: int)

  ghost predicate Wf(g: Grid, h: nat, w: nat)
  {
    |g| == h && h > 0 && w > 0 && (forall r :: 0 <= r < h ==> |g[r]| == w)
  }

  ghost predicate RowFull(g: Grid, h: nat, w: nat, r: int)
    requires Wf(g, h, w) && 0 <= r < h
  {
    forall c :: 0 <= c < w ==> g[r][c]
  }

  // The precondition both call sites establish: `cleared` is nonempty and every row in it is a
  // FULL row of withT (emit-opener-facts.ts:511-516 collects `mine` as exactly the full rows and
  // gates on the engine's own record; dualVerdict :222-224 does the same by construction).
  ghost predicate ClearedRowsFull(g: Grid, h: nat, w: nat, cleared: set<int>)
    requires Wf(g, h, w)
  {
    |cleared| > 0 && forall r :: r in cleared ==> 0 <= r < h && RowFull(g, h, w, r)
  }

  // The WEAKER precondition (rows in range but not necessarily full) — referenced only by the
  // mutation script, which swaps it in and confirms every lemma resting on fullness then fails.
  ghost predicate ClearedInRange(g: Grid, h: nat, w: nat, cleared: set<int>)
    requires Wf(g, h, w)
  {
    |cleared| > 0 && forall r :: r in cleared ==> 0 <= r < h
  }

  // ── donationCols, emit-opener-facts.ts:261-288, per column ─────────────────────────────────

  // inR / outR of the loop at :272-276: the filled cells of column c, split by membership of
  // their row in `cleared`. |FilledIn| == inR and |FilledOut| == outR.
  ghost function FilledIn(g: Grid, h: nat, w: nat, cleared: set<int>, c: int): set<int>
    requires Wf(g, h, w) && 0 <= c < w
  {
    set r | 0 <= r < h && r in cleared && g[r][c]
  }

  ghost function FilledOut(g: Grid, h: nat, w: nat, cleared: set<int>, c: int): set<int>
    requires Wf(g, h, w) && 0 <= c < w
  {
    set r | 0 <= r < h && r !in cleared && g[r][c]
  }

  // cavity(), :238-245. The TS scan keeps the LAST filled row of the column, i.e. the maximal
  // index; LowestFilled(g,h,w,c,r) is that scan over rows [0, r), -1 when the column is empty.
  ghost function LowestFilled(g: Grid, h: nat, w: nat, c: int, r: nat): int
    requires Wf(g, h, w) && 0 <= c < w && r <= h
    ensures -1 <= LowestFilled(g, h, w, c, r) < r
    ensures LowestFilled(g, h, w, c, r) >= 0 ==> g[LowestFilled(g, h, w, c, r)][c]
    ensures forall x :: LowestFilled(g, h, w, c, r) < x < r ==> !g[x][c]
  {
    if r == 0 then -1
    else if g[r-1][c] then r - 1
    else LowestFilled(g, h, w, c, r-1)
  }

  // the counting loop of :242-243, rows [r, h)
  ghost function CountEmptyBelow(g: Grid, h: nat, w: nat, c: int, r: int): nat
    requires Wf(g, h, w) && 0 <= c < w && 0 <= r <= h
    decreases h - r
  {
    if r >= h then 0 else (if !g[r][c] then 1 else 0) + CountEmptyBelow(g, h, w, c, r + 1)
  }

  ghost function CavityCount(g: Grid, h: nat, w: nat, c: int): nat
    requires Wf(g, h, w) && 0 <= c < w
  {
    var lo := LowestFilled(g, h, w, c, h);
    if lo < 0 then 0 else CountEmptyBelow(g, h, w, c, lo + 1)
  }

  // the deepest-rows scan of :280-281: from the floor upward, at most k empty rows above `lo`
  ghost function DeepRows(g: Grid, h: nat, w: nat, c: int, r: int, lo: int, k: nat): seq<int>
    requires Wf(g, h, w) && 0 <= c < w && -1 <= lo && r < h
    decreases r - lo
    ensures forall x :: x in DeepRows(g, h, w, c, r, lo, k) ==> lo < x <= r && !g[x][c]
  {
    if r <= lo || k == 0 then []
    else if !g[r][c] then [r] + DeepRows(g, h, w, c, r - 1, lo, k - 1)
    else DeepRows(g, h, w, c, r - 1, lo, k)
  }

  // :282-283 — the board edge counts as a wall
  ghost predicate Walled(g: Grid, h: nat, w: nat, c: int)
    requires Wf(g, h, w) && 0 <= c < w
  {
    var lo := LowestFilled(g, h, w, c, h);
    forall x :: x in DeepRows(g, h, w, c, h - 1, lo, DONATION_WALLED_ROWS) ==>
      (c == 0 || g[x][c - 1]) && (c == w - 1 || g[x][c + 1])
  }

  // :263-271 — the T's own slot: excluded only when the T occupies column c in EVERY cleared row
  ghost function TRowsAt(t: seq<Cell>, c: int): set<int>
  {
    set q | q in t && q.col == c :: q.row
  }

  ghost predicate TSlotExcluded(cleared: set<int>, t: seq<Cell>, c: int)
  {
    |TRowsAt(t, c)| > 0 && forall r :: r in cleared ==> r in TRowsAt(t, c)
  }

  // The per-column accept condition of the donationCols loop, :269-285, verbatim.
  ghost predicate DonationColPass(g: Grid, h: nat, w: nat, cleared: set<int>, t: seq<Cell>, c: int)
    requires Wf(g, h, w) && 0 <= c < w
  {
    && !TSlotExcluded(cleared, t, c)                 // :271
    && |FilledIn(g, h, w, cleared, c)| > 0           // :277  inR > 0   — the NAIVE clause
    && |FilledOut(g, h, w, cleared, c)| == 0         // :277  outR == 0 — the RE-OPENING clause
    && CavityCount(g, h, w, c) >= DONATION_CAVITY    // :279
    && Walled(g, h, w, c)                            // :282-284
  }

  // The same condition with the NAIVE clause deleted.
  ghost predicate DonationColPassNoNaive(g: Grid, h: nat, w: nat, cleared: set<int>, t: seq<Cell>, c: int)
    requires Wf(g, h, w) && 0 <= c < w
  {
    && !TSlotExcluded(cleared, t, c)
    && |FilledOut(g, h, w, cleared, c)| == 0
    && CavityCount(g, h, w, c) >= DONATION_CAVITY
    && Walled(g, h, w, c)
  }

  // The same condition with the RE-OPENING clause deleted instead — referenced only by the
  // mutation script: claiming DonationColPass <==> THIS must FAIL, which is the proof that the
  // two clauses of line 277 are not symmetric.
  ghost predicate DonationColPassNoReopen(g: Grid, h: nat, w: nat, cleared: set<int>, t: seq<Cell>, c: int)
    requires Wf(g, h, w) && 0 <= c < w
  {
    && !TSlotExcluded(cleared, t, c)
    && |FilledIn(g, h, w, cleared, c)| > 0
    && CavityCount(g, h, w, c) >= DONATION_CAVITY
    && Walled(g, h, w, c)
  }

  // ── claim 1: the naive clause is forced by arithmetic ──────────────────────────────────────

  // A full row requires every column filled, so every cleared row is filled at EVERY column:
  // FilledIn(c) is exactly `cleared` no matter which column is asked about.
  lemma NaiveClauseForced(g: Grid, h: nat, w: nat, cleared: set<int>, c: int)
    requires Wf(g, h, w)
    requires ClearedRowsFull(g, h, w, cleared)
    requires 0 <= c < w
    ensures forall r :: r in cleared ==> g[r][c]
    ensures FilledIn(g, h, w, cleared, c) == cleared
    ensures |FilledIn(g, h, w, cleared, c)| > 0
  {
    assert forall r :: r in cleared ==> 0 <= r < h && g[r][c];
    assert forall r :: r in FilledIn(g, h, w, cleared, c) <==> r in cleared;
    assert FilledIn(g, h, w, cleared, c) == cleared;
  }

  // Line 277's `inR === 0` guard is dead code: no column of any scored clear can take that branch.
  lemma NaiveGuardUnreachable(g: Grid, h: nat, w: nat, cleared: set<int>)
    requires Wf(g, h, w)
    requires ClearedRowsFull(g, h, w, cleared)
    ensures forall c :: 0 <= c < w ==> |FilledIn(g, h, w, cleared, c)| > 0
  {
    forall c | 0 <= c < w
      ensures |FilledIn(g, h, w, cleared, c)| > 0
    {
      NaiveClauseForced(g, h, w, cleared, c);
    }
  }

  // Deleting the naive clause from the accept condition changes nothing: it is not an
  // independent constraint. (Deleting the RE-OPENING clause instead is NOT provable — the
  // mutation script checks that this very lemma, retargeted at DonationColPassNoReopen, fails.)
  lemma NaiveConjunctRedundant(g: Grid, h: nat, w: nat, cleared: set<int>, t: seq<Cell>, c: int)
    requires Wf(g, h, w)
    requires ClearedRowsFull(g, h, w, cleared)
    requires 0 <= c < w
    ensures DonationColPass(g, h, w, cleared, t, c) <==> DonationColPassNoNaive(g, h, w, cleared, t, c)
  {
    NaiveClauseForced(g, h, w, cleared, c);
  }

  // ── caveAt, emit-opener-facts.ts:305-331 ───────────────────────────────────────────────────

  ghost function TColsOf(t: seq<Cell>): set<int>
  {
    set q | q in t :: q.col
  }

  // caveAt:307 — `under = Math.max(...cleared) + 1`, characterised rather than computed
  ghost predicate IsMaxCleared(cleared: set<int>, m: int)
  {
    m in cleared && forall x :: x in cleared ==> x <= m
  }

  // A run the caveAt loop accepts (:312-319): an empty run [c, e) at the row beneath the lower
  // cleared row, at least CAVE_MIN_WIDTH wide, overlapping the T's column span.
  ghost predicate CaveRun(g: Grid, h: nat, w: nat, under: int, t: seq<Cell>, c: int, e: int)
    requires Wf(g, h, w) && 0 <= under < h
  {
    && 0 <= c < e <= w
    && (forall k :: c <= k < e ==> !g[under][k])
    && e - c >= CAVE_MIN_WIDTH
    && (exists k :: c <= k < e && k in TColsOf(t))
  }

  // column k is covered somewhere strictly above row `under`
  ghost predicate Covered(g: Grid, h: nat, w: nat, under: int, k: int)
    requires Wf(g, h, w) && 0 <= under <= h && 0 <= k < w
  {
    exists r :: 0 <= r < under && g[r][k]
  }

  // The roof test caveAt deliberately does NOT run: every column of [c, e) is covered somewhere
  // strictly above row `under`. (Guarded on 0 <= k < w so the predicate is total in c and e.)
  ghost predicate Roofed(g: Grid, h: nat, w: nat, under: int, c: int, e: int)
    requires Wf(g, h, w) && 0 <= under <= h
  {
    forall k {:trigger Covered(g, h, w, under, k)} ::
      c <= k < e && 0 <= k < w ==> Covered(g, h, w, under, k)
  }

  // ── claim 2: the roof condition cannot fire ────────────────────────────────────────────────

  // The nub row the Double just completed (`under - 1 = max(cleared)`) is FULL, and it lies
  // directly above the cave — so it roofs EVERY column range, cave or not. Note the conclusion
  // does not assume the run is empty, wide, or overlapping: the roof is forced for the whole
  // board, which is the precise sense in which a roof test discriminates nothing.
  lemma RoofForced(g: Grid, h: nat, w: nat, cleared: set<int>, under: int, c: int, e: int)
    requires Wf(g, h, w)
    requires ClearedRowsFull(g, h, w, cleared)
    requires |cleared| == 2
    requires IsMaxCleared(cleared, under - 1)
    requires under < h
    requires 0 <= c <= e <= w
    ensures Roofed(g, h, w, under, c, e)
  {
    assert under - 1 in cleared;
    assert RowFull(g, h, w, under - 1);
    forall k | c <= k < e && 0 <= k < w
      ensures Covered(g, h, w, under, k)
    {
      assert g[under - 1][k];
    }
  }

  // Conjoining a roof test to the cave predicate yields an EQUIVALENT predicate: the guard the
  // drawings dropped is a guard nothing can fire.
  lemma RoofCannotDiscriminate(g: Grid, h: nat, w: nat, cleared: set<int>, t: seq<Cell>, under: int, c: int, e: int)
    requires Wf(g, h, w)
    requires ClearedRowsFull(g, h, w, cleared)
    requires |cleared| == 2
    requires IsMaxCleared(cleared, under - 1)
    requires 0 <= under < h
    ensures CaveRun(g, h, w, under, t, c, e) <==> CaveRun(g, h, w, under, t, c, e) && Roofed(g, h, w, under, c, e)
  {
    if CaveRun(g, h, w, under, t, c, e) {
      RoofForced(g, h, w, cleared, under, c, e);
    }
  }

  // ── non-vacuity witnesses ──────────────────────────────────────────────────────────────────
  // A lemma whose hypotheses cannot be satisfied proves nothing (spec/check_spec_vacuity.py is
  // this repo's rule). These two lemmas exhibit concrete boards satisfying every hypothesis
  // above, on which the guarded predicates are TRUE at one column and FALSE at another — so no
  // equivalence proved here is an equivalence between constants.

  lemma DonationWitness()
  {
    // a 3-wide, 6-tall board: row 0 is the cleared row; column 1 is a classic 5-deep well,
    // walled by columns 0 and 2
    var g: Grid := [
      [true, true,  true ],   // row 0 — the cleared row, full
      [true, false, true ],   // row 1
      [true, false, true ],   // row 2
      [true, false, true ],   // row 3
      [true, false, true ],   // row 4
      [true, false, true ]    // row 5 — the floor
    ];
    var h: nat := 6;
    var w: nat := 3;
    var cleared := {0};
    var t: seq<Cell> := [];
    assert Wf(g, h, w);
    assert RowFull(g, h, w, 0);
    assert ClearedRowsFull(g, h, w, cleared);

    // column 1 PASSES, with and without the naive clause
    assert 0 in FilledIn(g, h, w, cleared, 1);
    assert FilledOut(g, h, w, cleared, 1) == {};
    assert LowestFilled(g, h, w, 1, 1) == 0;
    assert LowestFilled(g, h, w, 1, 2) == 0;
    assert LowestFilled(g, h, w, 1, 3) == 0;
    assert LowestFilled(g, h, w, 1, 4) == 0;
    assert LowestFilled(g, h, w, 1, 5) == 0;
    assert LowestFilled(g, h, w, 1, 6) == 0;
    assert CountEmptyBelow(g, h, w, 1, 6) == 0;
    assert CountEmptyBelow(g, h, w, 1, 5) == 1;
    assert CountEmptyBelow(g, h, w, 1, 4) == 2;
    assert CountEmptyBelow(g, h, w, 1, 3) == 3;
    assert CountEmptyBelow(g, h, w, 1, 2) == 4;
    assert CountEmptyBelow(g, h, w, 1, 1) == 5;
    assert CavityCount(g, h, w, 1) == 5;
    assert DeepRows(g, h, w, 1, 1, 0, 0) == [];
    assert DeepRows(g, h, w, 1, 2, 0, 1) == [2];
    assert DeepRows(g, h, w, 1, 3, 0, 2) == [3, 2];
    assert DeepRows(g, h, w, 1, 4, 0, 3) == [4, 3, 2];
    assert DeepRows(g, h, w, 1, 5, 0, 4) == [5, 4, 3, 2];
    assert Walled(g, h, w, 1);
    assert !TSlotExcluded(cleared, t, 1);
    assert DonationColPass(g, h, w, cleared, t, 1);

    // column 0 FAILS (filled outside the cleared rows) — the predicate is not constant, and the
    // equivalence lemma is exercised on both a passing and a failing column
    assert 1 in FilledOut(g, h, w, cleared, 0);
    assert !DonationColPass(g, h, w, cleared, t, 0);
    NaiveConjunctRedundant(g, h, w, cleared, t, 1);
    NaiveConjunctRedundant(g, h, w, cleared, t, 0);
  }

  lemma CaveWitness()
  {
    // a 4-wide, 4-tall board: rows 0-1 are the Double's two cleared rows, the 4-wide empty run
    // at row 2 is the cave, and the T overlaps columns 1 and 2
    var g: Grid := [
      [true,  true,  true,  true ],   // row 0 — cleared
      [true,  true,  true,  true ],   // row 1 — cleared: the nub row the Double completed
      [false, false, false, false],   // row 2 — the cave
      [false, false, false, false]    // row 3
    ];
    var h: nat := 4;
    var w: nat := 4;
    var cleared := {0, 1};
    var t := [Cell(2, 1), Cell(2, 2)];
    var under := 2;
    assert Wf(g, h, w);
    assert RowFull(g, h, w, 0);
    assert RowFull(g, h, w, 1);
    assert ClearedRowsFull(g, h, w, cleared);
    assert |cleared| == 2;
    assert IsMaxCleared(cleared, 1);
    assert t[0] in t && t[0].col == 1;
    assert 1 in TColsOf(t);
    assert CaveRun(g, h, w, under, t, 0, 4);
    RoofForced(g, h, w, cleared, under, 0, 4);
    assert Roofed(g, h, w, under, 0, 4);
    RoofCannotDiscriminate(g, h, w, cleared, t, under, 0, 4);

    // a board whose row `under` is filled has no run at all — CaveRun is not constant either
    var g2: Grid := [
      [true,  true,  true,  true ],
      [true,  true,  true,  true ],
      [true,  true,  true,  true ],   // row 2 filled: no cave
      [false, false, false, false]
    ];
    assert Wf(g2, h, w);
    assert g2[2][0];
    assert !CaveRun(g2, h, w, under, t, 0, 4);
  }
}
