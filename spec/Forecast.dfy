// Forecast.dfy — what a T-Spin Forecast IS, as a specification.
//
// Hand-written, unlike sessions/*/report/dafny/*.dfy which are generated flat consts. Nothing here
// refers to a session: this file defines the concept, so that the measurement in pipeline/sim can be
// checked against a statement of intent rather than against itself.
//
// The definition is the player's, refined over 2026-08-02 against real boards:
//
//   "putting an overhang over a few lines far of a hole, when the lines between them clear,
//    like 1,2,3,4,5+ cleared by NOT tspin, it becomes a tspin hole"
//   "a tspin, after a non tspin triple line(s) clear"
//
// Four clauses, and each one rejects something the others admit:
//   1. the T-spin is TUCKED   — there is an overhang above it, placed by an identifiable earlier piece
//   2. the HOLE PRE-EXISTS    — the cavity the T's nose ends in was already open when the overhang landed
//   3. the GAP CLOSES         — rows strictly between the overhang and that hole were removed
//   4. by a NON-SPIN CLEAR    — the clear that removed them was not itself a T-spin
//
// Clause 2 is what distinguishes forecasting from ordinary downstacking: without it, a roof laid on
// solid stack that later opens up beneath scores the same as a roof laid deliberately over a gap.
// Clause 4 is what excludes the C-Spin, whose T-Spin Triple is what lowers its own overhang.

module Forecast {

  // ---------------------------------------------------------------------------------------------
  // Board geometry. Row 0 is the top; larger row index is lower on the screen. A cleared row is
  // spliced out and everything ABOVE it falls, so a surviving cell's index INCREASES.
  // ---------------------------------------------------------------------------------------------

  const Width: int := 10

  datatype Cell =
      Empty
    | Stack(placedBy: int)   // placedBy >= 0 : the index of the lock that placed it
    | Garbage                // arrived from the opponent; has no placing lock

  type Row = r: seq<Cell> | |r| == Width witness seq(Width, _ => Empty)
  type Board = seq<Row>

  predicate Filled(c: Cell) { c != Empty }

  // ---------------------------------------------------------------------------------------------
  // One step of play: a piece locks, full rows are removed, then garbage rises. That order is the
  // simulator's (place -> clear -> insert) and it matters: garbage lifts the survivors of the clear.
  // ---------------------------------------------------------------------------------------------

  datatype Step = Step(
    clearedRows: seq<int>,  // pre-clear row indices that were full, so were removed
    wasSpin: bool,          // the locking piece finished as a T-spin
    garbageRows: int        // rows of garbage inserted at the bottom afterwards
  )

  type History = seq<Step>

  // Rows removed from strictly below `r` — the ones that make `r` fall.
  function CountBelow(cleared: seq<int>, r: int): int
    decreases |cleared|
  {
    if |cleared| == 0 then 0
    else (if cleared[0] > r then 1 else 0) + CountBelow(cleared[1..], r)
  }

  // Rows removed from strictly between `a` and `b`.
  function CountBetween(cleared: seq<int>, a: int, b: int): int
    decreases |cleared|
  {
    if |cleared| == 0 then 0
    else (if a < cleared[0] && cleared[0] < b then 1 else 0) + CountBetween(cleared[1..], a, b)
  }

  predicate Survives(s: Step, r: int) { r !in s.clearedRows }

  // Where a surviving cell sits after the step: it falls past every row removed beneath it, then
  // the whole stack is lifted by the garbage that rises under it.
  function Advance(s: Step, r: int): int
    requires Survives(s, r)
  {
    r + CountBelow(s.clearedRows, r) - s.garbageRows
  }

  // ---------------------------------------------------------------------------------------------
  // THE STRUCTURAL FACT the whole measurement rests on.
  //
  // Two cells' vertical separation changes by exactly the number of rows removed from BETWEEN them.
  // Garbage cancels — it lifts both equally — and rows removed above or below both cancel too. So
  // an overhang can be brought down onto a hole by a line clear and by nothing else: no placement
  // moves an existing cell, and garbage only ever pushes the pair up together.
  //
  // This is why "the player set this up in advance" and "a line clear opened it" are not two
  // independent properties. Measured over 649 real events, the off-diagonal was empty; here is the
  // reason it had to be.
  // ---------------------------------------------------------------------------------------------

  lemma CountBelowSplit(cleared: seq<int>, a: int, b: int)
    requires a < b
    requires b !in cleared
    ensures CountBelow(cleared, a) == CountBetween(cleared, a, b) + CountBelow(cleared, b)
    decreases |cleared|
  {
    if |cleared| == 0 {
    } else {
      CountBelowSplit(cleared[1..], a, b);
    }
  }

  lemma GapClosesOnlyByClearsBetween(s: Step, a: int, b: int)
    requires a < b
    requires Survives(s, a) && Survives(s, b)
    ensures Advance(s, b) - Advance(s, a) == (b - a) - CountBetween(s.clearedRows, a, b)
  {
    CountBelowSplit(s.clearedRows, a, b);
  }

  // Corollary, stated separately because it is the sentence the report needs: garbage alone can
  // never close a gap, however much of it arrives.
  lemma GarbageNeverClosesAGap(s: Step, a: int, b: int)
    requires a < b
    requires Survives(s, a) && Survives(s, b)
    requires CountBetween(s.clearedRows, a, b) == 0
    ensures Advance(s, b) - Advance(s, a) == b - a
  {
    GapClosesOnlyByClearsBetween(s, a, b);
  }

  // ---------------------------------------------------------------------------------------------
  // Tracking a cell across a stretch of history.
  // ---------------------------------------------------------------------------------------------

  datatype Tracked = Gone | At(row: int)

  function TrackStep(s: Step, t: Tracked): Tracked {
    match t
    case Gone => Gone
    case At(r) => if Survives(s, r) then At(Advance(s, r)) else Gone
  }

  function Track(h: History, from: int, upto: int, t: Tracked): Tracked
    requires 0 <= from <= upto <= |h|
    decreases upto - from
  {
    if from == upto then t
    else Track(h, from + 1, upto, TrackStep(h[from], t))
  }

  // Rows removed from between the pair over a stretch, split by whether the clearing placement was
  // itself a T-spin. Clause 4 rejects an event whose gap was closed only by spins.
  function RemovedBetween(h: History, from: int, upto: int, a: Tracked, b: Tracked, spins: bool): int
    requires 0 <= from <= upto <= |h|
    decreases upto - from
  {
    if from == upto then 0
    else
      var s := h[from];
      var here :=
        if a.At? && b.At? && a.row < b.row && s.wasSpin == spins
        then CountBetween(s.clearedRows, a.row, b.row) else 0;
      here + RemovedBetween(h, from + 1, upto, TrackStep(s, a), TrackStep(s, b), spins)
  }

  // ---------------------------------------------------------------------------------------------
  // THE DEFINITION.
  //
  // At step k a T lands tucked under an overhang. `roofAt` is the overhang cell's row when its own
  // piece locked at step j; `floorAt` is the row, at that same moment, of the cell the T's nose will
  // eventually come to rest on. `holeOpenAtJ` records whether the cell directly above that floor was
  // ALREADY empty then — the "over a hole" in the player's phrasing.
  //
  // `minLines` is deliberately a parameter. "a non tspin triple line(s) clear" reads either as
  // "a clear of three lines" or as "one or more line clears, none of them a T-spin"; the two are
  // instantiated below rather than one being silently chosen.
  // ---------------------------------------------------------------------------------------------

  datatype Event = Event(
    j: int,             // the step whose piece placed the overhang
    k: int,             // the step whose piece is the T-spin
    roofAt: int,        // overhang's row, measured just after step j
    floorAt: int,       // row of the cell the nose will rest on, measured just after step j
    holeOpenAtJ: bool,  // was the cell directly above that floor already empty at step j?
    spinAtK: bool       // did the piece at step k finish as a T-spin?
  )

  predicate WellFormed(h: History, e: Event) {
    && 0 <= e.j < e.k <= |h|
    && e.roofAt < e.floorAt          // the overhang is above the hole's floor
  }

  predicate Tucked(e: Event) { e.spinAtK }

  predicate HolePreExisted(e: Event) { e.holeOpenAtJ }

  // The pair, followed from just after j to just before k.
  function RoofFinal(h: History, e: Event): Tracked
    requires WellFormed(h, e)
  { Track(h, e.j, e.k - 1, At(e.roofAt)) }

  function FloorFinal(h: History, e: Event): Tracked
    requires WellFormed(h, e)
  { Track(h, e.j, e.k - 1, At(e.floorAt)) }

  predicate BothSurvive(h: History, e: Event)
    requires WellFormed(h, e)
  { RoofFinal(h, e).At? && FloorFinal(h, e).At? }

  predicate GapClosed(h: History, e: Event)
    requires WellFormed(h, e)
  {
    && BothSurvive(h, e)
    && FloorFinal(h, e).row - RoofFinal(h, e).row < e.floorAt - e.roofAt
  }

  function ClosedBySpins(h: History, e: Event): int
    requires WellFormed(h, e)
  { RemovedBetween(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), true) }

  function ClosedByPlain(h: History, e: Event): int
    requires WellFormed(h, e)
  { RemovedBetween(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), false) }

  // ---- the predicate itself --------------------------------------------------------------------

  predicate IsForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
  {
    && Tucked(e)                          // 1. a tucked T-spin was actually executed
    && HolePreExisted(e)                  // 2. the hole was already open when the overhang landed
    && GapClosed(h, e)                    // 3. rows between them were removed
    && ClosedByPlain(h, e) >= minLines    // 4. by clears that were NOT themselves T-spins
  }

  // "one or more line clears, none of them a T-spin"
  predicate IsForecastAnyClear(h: History, e: Event)
    requires WellFormed(h, e)
  { IsForecast(h, e, 1) }

  // "a non-T-spin TRIPLE" — three rows taken from between the overhang and the hole
  predicate IsForecastTriple(h: History, e: Event)
    requires WellFormed(h, e)
  { IsForecast(h, e, 3) }

  lemma TripleIsStricter(h: History, e: Event)
    requires WellFormed(h, e)
    ensures IsForecastTriple(h, e) ==> IsForecastAnyClear(h, e)
  { }

  // ---------------------------------------------------------------------------------------------
  // What the definition REJECTS. These are the confounds found in the corpus, stated as theorems so
  // that a future change to the definition which readmits one of them fails here rather than in a
  // published percentage.
  // ---------------------------------------------------------------------------------------------

  // The C-Spin: its T-Spin Triple is what lowers its own overhang. If every row taken from between
  // the pair came from a spin, this is not a forecast under any reading.
  lemma CSpinIsNotAForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires minLines >= 1
    requires ClosedByPlain(h, e) == 0
    ensures !IsForecast(h, e, minLines)
  { }

  // A roof laid on solid stack that opens up later is downstacking, not forecasting.
  lemma NoPreExistingHoleIsNotAForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires !e.holeOpenAtJ
    ensures !IsForecast(h, e, minLines)
  { }

  // And the reason clause 3 can never be satisfied by the opponent: garbage lifts the pair together.
  lemma GarbageAloneCannotMakeAForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires minLines >= 1
    requires forall i :: e.j <= i < e.k - 1 ==> h[i].clearedRows == []
    ensures !IsForecast(h, e, minLines)
  {
    NoClearsMeansNoRemoval(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), false);
  }

  // ---------------------------------------------------------------------------------------------
  // ANTI-VACUITY. Every lemma above is of the form "this is NOT a forecast", and all of them hold
  // trivially if `IsForecast` is unsatisfiable. A green verifier proves nothing until a witness
  // exists, so here are three: one the definition accepts, and two it rejects for the two distinct
  // reasons that matter. Without these, "30 verified, 0 errors" would be compatible with a
  // definition that is simply always false.
  // ---------------------------------------------------------------------------------------------

  // The shape the player confirmed: an overhang two rows above the floor of an already-open hole,
  // one ordinary line clear takes the row between them, and the T tucks in.
  lemma ForecastIsSatisfiable() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures IsForecastAnyClear(h, e)
    // the exact count is part of the contract, so callers can reason about HOW MUCH was removed
    ensures ClosedByPlain(h, e) == 1
  {
    h := [ Step([26], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 25, 27, true, true);
    assert CountBetween([26], 25, 27) == 1;
    assert Advance(h[0], 25) == 26 && Advance(h[0], 27) == 27;
    assert ClosedByPlain(h, e) == 1;
  }

  // The same board, but the clear that lowers the overhang is itself a T-spin — the C-Spin. The
  // gap closes exactly as before and the definition still says no.
  lemma CSpinWitnessIsRejected() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures GapClosed(h, e)          // the gap really does close ...
    ensures !IsForecastAnyClear(h, e) // ... and it is still not a forecast
  {
    h := [ Step([26], true, 0), Step([], false, 0) ];
    e := Event(0, 2, 25, 27, true, true);
    assert CountBetween([26], 25, 27) == 1;
    assert ClosedByPlain(h, e) == 0;
    assert ClosedBySpins(h, e) == 1;
  }

  // And the case the player used to reject the currently-published event: everything else holds,
  // but the hole was not open when the overhang was placed.
  lemma NoHoleWitnessIsRejected() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures GapClosed(h, e)
    ensures ClosedByPlain(h, e) >= 1
    ensures !IsForecastAnyClear(h, e)
  {
    h := [ Step([26], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 25, 27, false, true);
    assert CountBetween([26], 25, 27) == 1;
  }

  // A T that lands without finishing as a spin is not a forecast however perfect the setup was.
  // Without this the `Tucked` clause is decorative: nothing else in the file ever sets spinAtK false.
  lemma NotASpinIsRejected() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures GapClosed(h, e) && ClosedByPlain(h, e) >= 1 && HolePreExisted(e)
    ensures !IsForecastAnyClear(h, e)
  {
    h := [ Step([26], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 25, 27, true, false);
    assert CountBetween([26], 25, 27) == 1;
  }

  // Garbage lifts the pair together and changes nothing between them. Stated on a witness that
  // actually HAS garbage, because every other lemma here sets garbageRows to 0 — which left the
  // `- s.garbageRows` term in `Advance` unpinned and a mutation deleting it undetected.
  lemma GarbageWitnessLeavesTheGapAlone() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures h[0].garbageRows == 4
    ensures !GapClosed(h, e)              // four rows of garbage, gap unmoved
    ensures !IsForecastAnyClear(h, e)
  {
    h := [ Step([], false, 4), Step([], false, 0) ];
    e := Event(0, 2, 25, 27, true, true);
    assert Advance(h[0], 25) == 21 && Advance(h[0], 27) == 23;
    GarbageNeverClosesAGap(h[0], 25, 27);
  }

  // `GapClosed` looks redundant beside clause 4 — removing a row from between the pair does close
  // the gap — and at minLines >= 1 it is. It is load-bearing at minLines == 0, the "forecast-shaped
  // regardless of how much was removed" reading, and is kept so that reading stays honest.
  predicate IsForecastShape(h: History, e: Event)
    requires WellFormed(h, e)
  { IsForecast(h, e, 0) }

  lemma GapClauseIsLoadBearingAtZero() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures Tucked(e) && HolePreExisted(e) && ClosedByPlain(h, e) == 0
    ensures !GapClosed(h, e)
    ensures !IsForecastShape(h, e)        // false ONLY because the gap never closed
  {
    h := [ Step([], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 25, 27, true, true);
  }

  // The two readings of "triple line(s)" are genuinely different, so the choice cannot be silent.
  lemma TheTwoReadingsDiffer() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures IsForecastAnyClear(h, e) && !IsForecastTriple(h, e)
  {
    h, e := ForecastIsSatisfiable();
    assert ClosedByPlain(h, e) == 1;
  }

  lemma NoClearsMeansNoRemoval(h: History, from: int, upto: int, a: Tracked, b: Tracked, spins: bool)
    requires 0 <= from <= upto <= |h|
    requires forall i :: from <= i < upto ==> h[i].clearedRows == []
    ensures RemovedBetween(h, from, upto, a, b, spins) == 0
    decreases upto - from
  {
    if from == upto {
    } else {
      NoClearsMeansNoRemoval(h, from + 1, upto, TrackStep(h[from], a), TrackStep(h[from], b), spins);
    }
  }

  // ---------------------------------------------------------------------------------------------
  // HOW MANY ROWS THE CLEAR TAKES IS NOT PART OF THE DEFINITION.
  //
  //   "like 1,2,3,4,5+ cleared by NOT tspin, it becomes a tspin hole"
  //
  // Clause 4 counts ROWS taken from strictly between the overhang and the hole. It does not ask how
  // many clears took them, which piece did it, or whether the clear was a Single or a Tetris. That
  // is a claim about the definition, so it is proved here for every n at once rather than on four
  // hand-built boards — four boards would leave "and 5+" open, and the reader would have to trust
  // that the pattern continues.
  //
  // It also pins the other half: rows taken from OUTSIDE the pair move both cells together and
  // close nothing, whatever the size of the clear. That is the `straddle` test the measurement runs.
  // ---------------------------------------------------------------------------------------------

  function RangeSeq(lo: int, n: nat): seq<int>
    decreases n
  { if n == 0 then [] else [lo] + RangeSeq(lo + 1, n - 1) }

  lemma RangeSeqLen(lo: int, n: nat)
    ensures |RangeSeq(lo, n)| == n
    decreases n
  { if n == 0 { } else { RangeSeqLen(lo + 1, n - 1); } }

  lemma RangeSeqExcludes(lo: int, n: nat, r: int)
    requires r < lo || lo + n <= r
    ensures r !in RangeSeq(lo, n)
    decreases n
  { if n == 0 { } else { RangeSeqExcludes(lo + 1, n - 1, r); } }

  // every row of the range lies strictly between a and b
  lemma RangeSeqBetween(lo: int, n: nat, a: int, b: int)
    requires a < lo && lo + n <= b
    ensures CountBetween(RangeSeq(lo, n), a, b) == n
    decreases n
  { if n == 0 { } else { RangeSeqBetween(lo + 1, n - 1, a, b); } }

  // ... so a cell above the whole range falls by exactly n ...
  lemma RangeSeqBelow(lo: int, n: nat, r: int)
    requires r < lo
    ensures CountBelow(RangeSeq(lo, n), r) == n
    decreases n
  { if n == 0 { } else { RangeSeqBelow(lo + 1, n - 1, r); } }

  // ... and a cell below it does not move at all.
  lemma RangeSeqNoneBelow(lo: int, n: nat, r: int)
    requires lo + n <= r
    ensures CountBelow(RangeSeq(lo, n), r) == 0
    decreases n
  { if n == 0 { } else { RangeSeqNoneBelow(lo + 1, n - 1, r); } }

  /** ONE non-spin clear of ANY size n >= 1 taken from between the pair is a forecast. */
  lemma AnySizeOfClearIsAForecast(n: nat) returns (h: History, e: Event)
    requires n >= 1
    ensures WellFormed(h, e)
    ensures |h| == 2 && !h[0].wasSpin && |h[0].clearedRows| == n   // ONE clear, n rows
    ensures ClosedByPlain(h, e) == n
    ensures IsForecastAnyClear(h, e)
    ensures n >= 3 ==> IsForecastTriple(h, e)                      // a Triple or a Tetris also qualifies
  {
    var cleared := RangeSeq(26, n);
    RangeSeqLen(26, n);
    RangeSeqExcludes(26, n, 25);
    RangeSeqExcludes(26, n, 26 + n);
    RangeSeqBelow(26, n, 25);
    RangeSeqNoneBelow(26, n, 26 + n);
    RangeSeqBetween(26, n, 25, 26 + n);
    h := [ Step(cleared, false, 0), Step([], false, 0) ];
    e := Event(0, 2, 25, 26 + n, true, true);
    assert Advance(h[0], 25) == 25 + n;
    assert Advance(h[0], 26 + n) == 26 + n;
    assert RoofFinal(h, e) == At(25 + n) && FloorFinal(h, e) == At(26 + n);
    assert ClosedByPlain(h, e) == n;
  }

  /**
   * Rows accumulate across the window: what a window removes is what its parts remove.
   *
   * This is the general form of "1,2,3,4,5+" — it says clause 4's count is additive over steps, so
   * no arrangement of clears is special. It is also what makes the concrete witnesses below cheap:
   * a THREE-step ground window makes this encoding blow up (>30 s, measured), while every two-step
   * window verifies in well under a second, so longer histories are reasoned about by splitting
   * rather than by unrolling.
   */
  lemma RemovedBetweenSplit(h: History, from: int, mid: int, upto: int, a: Tracked, b: Tracked, spins: bool)
    requires 0 <= from <= mid <= upto <= |h|
    ensures RemovedBetween(h, from, upto, a, b, spins)
         == RemovedBetween(h, from, mid, a, b, spins)
          + RemovedBetween(h, mid, upto, Track(h, from, mid, a), Track(h, from, mid, b), spins)
    decreases mid - from
  {
    if from == mid { }
    else { RemovedBetweenSplit(h, from + 1, mid, upto, TrackStep(h[from], a), TrackStep(h[from], b), spins); }
  }

  lemma TrackSplit(h: History, from: int, mid: int, upto: int, t: Tracked)
    requires 0 <= from <= mid <= upto <= |h|
    ensures Track(h, from, upto, t) == Track(h, mid, upto, Track(h, from, mid, t))
    decreases mid - from
  { if from == mid { } else { TrackSplit(h, from + 1, mid, upto, TrackStep(h[from], t)); } }

  /** A Double and then a Single reach the Triple reading: clause 4 counts ROWS, not clears. */
  lemma RowsAccumulateAcrossClears() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures |h| == 3 && |h[0].clearedRows| == 2 && |h[1].clearedRows| == 1   // a Double, then a Single
    ensures ClosedByPlain(h, e) == 3
    ensures IsForecastTriple(h, e)
  {
    h := [ Step([26, 27], false, 0), Step([28], false, 0), Step([], false, 0) ];
    e := Event(0, 3, 25, 30, true, true);
  }

  /**
   * A spin and a plain clear in the same window: only the plain rows count toward clause 4.
   *
   * The two counts are established one at a time through `RemovedBetweenSplit`. Asking for both in
   * one lemma re-derives the whole window twice and times out — the same encoding cost recorded on
   * the split lemma above.
   */
  const SPIN_THEN_PLAIN: History := [ Step([26], true, 0), Step([27], false, 0), Step([], false, 0) ]
  const SPIN_THEN_PLAIN_EVENT: Event := Event(0, 3, 25, 29, true, true)

  lemma SpinRowsDoNotCountTowardClause4()
    ensures WellFormed(SPIN_THEN_PLAIN, SPIN_THEN_PLAIN_EVENT)
    ensures ClosedByPlain(SPIN_THEN_PLAIN, SPIN_THEN_PLAIN_EVENT) == 1   // only the ordinary clear
  {
    var h, e := SPIN_THEN_PLAIN, SPIN_THEN_PLAIN_EVENT;
    RemovedBetweenSplit(h, 0, 1, 2, At(25), At(29), false);
    assert RemovedBetween(h, 0, 1, At(25), At(29), false) == 0;   // step 0 was a spin
    assert Track(h, 0, 1, At(25)) == At(26) && Track(h, 0, 1, At(29)) == At(29);
    assert RemovedBetween(h, 1, 2, At(26), At(29), false) == 1;
  }

  lemma SpinRowsAreCountedSeparately()
    ensures WellFormed(SPIN_THEN_PLAIN, SPIN_THEN_PLAIN_EVENT)
    ensures ClosedBySpins(SPIN_THEN_PLAIN, SPIN_THEN_PLAIN_EVENT) == 1  // and the spin's row is seen
  {
    var h, e := SPIN_THEN_PLAIN, SPIN_THEN_PLAIN_EVENT;
    RemovedBetweenSplit(h, 0, 1, 2, At(25), At(29), true);
    assert RemovedBetween(h, 0, 1, At(25), At(29), true) == 1;
    assert Track(h, 0, 1, At(25)) == At(26) && Track(h, 0, 1, At(29)) == At(29);
    assert RemovedBetween(h, 1, 2, At(26), At(29), true) == 0;
  }

  // No lemma here states the mixed window's forecast VERDICT: evaluating IsForecast over a two-step
  // window re-derives both counts plus the tracked pair and does not finish inside the time limit.
  // The verdict follows from two lemmas that do verify — AnySizeOfClearIsAForecast(1) says one
  // ordinary row suffices, and CSpinIsNotAForecast says spin rows alone never do.

  /** A Tetris that lands entirely BELOW the hole moves the pair down together and closes nothing. */
  lemma ClearsOutsideThePairCloseNothing(n: nat) returns (h: History, e: Event)
    requires n >= 1
    ensures WellFormed(h, e)
    ensures |h[0].clearedRows| == n && !h[0].wasSpin
    ensures ClosedByPlain(h, e) == 0
    ensures !GapClosed(h, e)
    ensures !IsForecastAnyClear(h, e)
  {
    var cleared := RangeSeq(30, n);      // strictly below the floor at row 29
    RangeSeqLen(30, n);
    RangeSeqExcludes(30, n, 25);
    RangeSeqExcludes(30, n, 29);
    RangeSeqBelow(30, n, 25);
    RangeSeqBelow(30, n, 29);
    RangeSeqBetween(30, n, 29, 30 + n);
    h := [ Step(cleared, false, 0), Step([], false, 0) ];
    e := Event(0, 2, 25, 29, true, true);
    assert CountBetween(cleared, 25, 29) == 0 by { CountBelowSplit(cleared, 25, 29); }
    assert Advance(h[0], 25) == 25 + n && Advance(h[0], 29) == 29 + n;
    assert ClosedByPlain(h, e) == 0;
  }
}
