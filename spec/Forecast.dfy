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

  // ---------------------------------------------------------------------------------------------
  // WELL-FORMEDNESS. Added 2026-08-08 after a probe showed the model admits histories the game
  // cannot produce, and that one of them satisfies the STRICTEST reading of the definition:
  //
  //   Step([5, 5, 5], false, 0)  -- one row, listed three times
  //
  // `CountBelow` and `CountBetween` walk the sequence and count occurrences, so a duplicated row is
  // counted once per copy. That made `ClosedByPlain == 3` from a single line clear, and
  // `IsForecastTriple` -- "a non-spin TRIPLE" -- provable from it. Negative `garbageRows` was
  // admitted too, sinking the field instead of lifting it.
  //
  // No published figure was ever affected: `pipeline/sim/forecast.ts` derives its cleared rows from
  // the board itself (`Bpre.map((row, i) => row.every(...))`), which cannot repeat an index. The gap
  // was between the spec and the thing it specifies -- which is the one gap this file exists to close.
  // ---------------------------------------------------------------------------------------------

  predicate NoDup(s: seq<int>) {
    forall i, j :: 0 <= i < j < |s| ==> s[i] != s[j]
  }

  predicate WellFormedStep(s: Step) {
    && NoDup(s.clearedRows)      // a row can only be removed once
    && s.garbageRows >= 0        // garbage rises; it never sinks the field
  }

  predicate WellFormedHistory(h: History) {
    forall i :: 0 <= i < |h| ==> WellFormedStep(h[i])
  }

  // The rows actually taken from between the pair, as a SET. Cardinality is what forces distinctness.
  function RowsBetween(cleared: seq<int>, a: int, b: int): set<int>
  {
    set i | 0 <= i < |cleared| && a < cleared[i] < b :: cleared[i]
  }

  /**
   * THE theorem clause 4 needs: "n rows were removed from between them" means n DIFFERENT rows.
   *
   * Without `NoDup` this is false, and not academically: `Step([5, 5, 5], false, 0)` makes
   * `ClosedByPlain == 3` and `IsForecastTriple` provable from a single line clear. Deleting the
   * hypothesis makes this proof fail, so the requirement is load-bearing rather than decorative.
   */
  lemma CountBetweenIsDistinctCount(cleared: seq<int>, a: int, b: int)
    requires NoDup(cleared)
    ensures CountBetween(cleared, a, b) == |RowsBetween(cleared, a, b)|
    decreases |cleared|
  {
    if |cleared| == 0 {
      assert RowsBetween(cleared, a, b) == {};
    } else {
      var x := cleared[0];
      var rest := cleared[1..];
      assert NoDup(rest);
      CountBetweenIsDistinctCount(rest, a, b);
      assert x !in rest;
      if a < x < b {
        assert RowsBetween(cleared, a, b) == {x} + RowsBetween(rest, a, b);
        assert x !in RowsBetween(rest, a, b);
      } else {
        assert RowsBetween(cleared, a, b) == RowsBetween(rest, a, b);
      }
    }
  }

  /** The defect, pinned. Both shapes the model used to admit are now rejected by name. */
  lemma ImpossibleStepsAreRejected()
    ensures !WellFormedStep(Step([5, 5, 5], false, 0))    // one row, counted three times
    ensures !WellFormedStep(Step([], false, -1))          // garbage that sinks the field
    ensures WellFormedStep(Step([5, 6, 7], false, 4))     // and a real one still passes
  {
    var dup := [5, 5, 5];
    assert dup[0] == dup[1];          // the witness indices; a negated forall needs them named
    assert !NoDup(dup);
  }

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

  /**
   * Garbage is a RIGID TRANSLATION of everything that survives: it moves every cell by the same
   * amount, so it preserves every pairwise relationship, not merely the one gap that
   * `GarbageNeverClosesAGap` names.
   */
  lemma GarbageIsARigidTranslation(s: Step, a: int, b: int)
    requires WellFormedStep(s)
    requires s.clearedRows == []
    ensures Survives(s, a) && Survives(s, b)
    ensures Advance(s, a) == a - s.garbageRows
    ensures Advance(s, b) - Advance(s, a) == b - a
  { }

  /**
   * ...and the sharper consequence: HOW MUCH garbage arrives cannot change any gap. Two steps that
   * clear the same rows and differ only in garbage are indistinguishable to every gap-based
   * predicate in this file.
   *
   * This is the precise boundary of the model, and it is why the spec cannot adjudicate the
   * implementation's `forecast_garbage` branch (`pipeline/sim/forecast.ts:388`) either way. That
   * branch fires on garbage CONTENT -- the hole in an arriving row becoming the floor of a new slot
   * -- whereas `Step` carries only `garbageRows: int` and no hole column, so arriving garbage is
   * pure translation here. `GarbageAloneCannotMakeAForecast` is therefore not a refutation of that
   * branch; the two are about different mechanisms, and nothing had said so.
   *
   * Measured 2026-08-08: under `insertMode:'immediate'` the implementation emits 13 verified
   * forecasts across the four sessions, every one of them `mechanism = 'garbage'` and every one with
   * `garbageLoadBearing = false`. Representing that at all needs a hole column, which this model
   * deliberately does not have.
   */
  lemma GarbageAmountCannotChangeAnyGap(s1: Step, s2: Step, a: int, b: int)
    requires WellFormedStep(s1) && WellFormedStep(s2)
    requires s1.clearedRows == s2.clearedRows
    requires Survives(s1, a) && Survives(s1, b)
    ensures Survives(s2, a) && Survives(s2, b)
    ensures Advance(s2, b) - Advance(s2, a) == Advance(s1, b) - Advance(s1, a)
  { }

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
  // THE GAP IDENTITY, LIFTED FROM ONE STEP TO A WINDOW OF ANY LENGTH.
  //
  // `GapClosesOnlyByClearsBetween` is the one-step statement. Clause 3 is about a WINDOW, so until
  // 2026-08-09 nothing connected the two: the clause was backed by worked boards only, while
  // clauses 1, 2 and 4 each had a universal. Everything below exists to close that.
  //
  // The induction runs from the FRONT of the window rather than through `TrackSplit` /
  // `RemovedBetweenSplit`. Those split lemmas are what the ground three-step witnesses need, because
  // there the blow-up is in evaluating a concrete history; here `h` is symbolic and the recursion in
  // `Track` and `RemovedBetween` already lines up step for step, so peeling one step off the front
  // discharges it in about a second.
  //
  // WELL-FORMEDNESS IS LOAD-BEARING HERE, and this is the first place it does real work rather than
  // rejecting a nonsense witness. The induction needs the tracked pair to stay ORDERED, and it does
  // so only because a step cannot remove more rows from between two cells than there are rows
  // between them — which is false without `NoDup`, since `Step([5, 5, 5], ...)` removes "three
  // rows" from a one-row gap and swaps the pair over.
  // ---------------------------------------------------------------------------------------------

  // Defined by recursion rather than as `set i | a < i < b :: i`: the comprehension has no term to
  // trigger on, so Dafny warns that it will be brittle, and its cardinality then needs the same
  // induction anyway.
  function IntsBetween(a: int, b: int): set<int>
    decreases b - a
  { if b <= a + 1 then {} else IntsBetween(a, b - 1) + {b - 1} }

  lemma IntsBetweenMembership(a: int, b: int, x: int)
    ensures x in IntsBetween(a, b) <==> a < x < b
    decreases b - a
  { if b <= a + 1 { } else { IntsBetweenMembership(a, b - 1, x); } }

  lemma IntsBetweenCard(a: int, b: int)
    requires a < b
    ensures |IntsBetween(a, b)| == b - a - 1
    decreases b - a
  {
    if b == a + 1 { }
    else {
      IntsBetweenCard(a, b - 1);
      IntsBetweenMembership(a, b - 1, b - 1);   // b-1 is new, so the cardinality goes up by one
    }
  }

  // Dafny 4.11 does NOT know this — `requires s <= t ensures |s| <= |t|` with an empty body fails.
  // Checked before relying on it, because the whole bound below rests on it.
  lemma SubsetCard(s: set<int>, t: set<int>)
    requires s <= t
    ensures |s| <= |t|
    decreases |t|
  {
    if s == t { }
    else {
      var x :| x in t && x !in s;
      assert s <= t - {x};
      SubsetCard(s, t - {x});
    }
  }

  lemma CountBetweenNonNeg(cleared: seq<int>, a: int, b: int)
    ensures CountBetween(cleared, a, b) >= 0
    decreases |cleared|
  { if |cleared| == 0 { } else { CountBetweenNonNeg(cleared[1..], a, b); } }

  /**
   * A step cannot close a gap past zero: at most `b - a - 1` rows lie strictly between two cells, so
   * at most that many can be taken. Pigeonhole, and it needs `NoDup` — `CountBetween` counts
   * OCCURRENCES, so without distinctness a single row listed n times reads as n rows removed.
   */
  lemma CountBetweenIsLessThanTheGap(cleared: seq<int>, a: int, b: int)
    requires NoDup(cleared)
    requires a < b
    ensures 0 <= CountBetween(cleared, a, b) < b - a
  {
    CountBetweenNonNeg(cleared, a, b);
    CountBetweenIsDistinctCount(cleared, a, b);
    IntsBetweenCard(a, b);
    forall x | x in RowsBetween(cleared, a, b)
      ensures x in IntsBetween(a, b)
    { IntsBetweenMembership(a, b, x); }
    SubsetCard(RowsBetween(cleared, a, b), IntsBetween(a, b));
  }

  // `Gone` is absorbing, so a pair that is `At?` at the end of the window was `At?` throughout it.
  lemma TrackGoneStaysGone(h: History, from: int, upto: int)
    requires 0 <= from <= upto <= |h|
    ensures Track(h, from, upto, Gone) == Gone
    decreases upto - from
  { if from == upto { } else { TrackGoneStaysGone(h, from + 1, upto); } }

  lemma RemovedBetweenNonNeg(h: History, from: int, upto: int, a: Tracked, b: Tracked, spins: bool)
    requires 0 <= from <= upto <= |h|
    ensures RemovedBetween(h, from, upto, a, b, spins) >= 0
    decreases upto - from
  {
    if from == upto { }
    else {
      if a.At? && b.At? { CountBetweenNonNeg(h[from].clearedRows, a.row, b.row); }
      RemovedBetweenNonNeg(h, from + 1, upto, TrackStep(h[from], a), TrackStep(h[from], b), spins);
    }
  }

  /**
   * THE WINDOW IDENTITY. Over a window of ANY length, the pair's separation shrinks by exactly the
   * number of rows taken from between them — spin rows and plain rows together, and nothing else.
   *
   * Everything clause 3 says follows from this: `GapClosed` is not an independent property of a
   * history, it is a restatement of "the two counts sum to at least one".
   */
  lemma GapEqualsRowsRemovedBetween(h: History, from: int, upto: int, a: int, b: int)
    requires WellFormedHistory(h)
    requires 0 <= from <= upto <= |h|
    requires a < b
    requires Track(h, from, upto, At(a)).At?
    requires Track(h, from, upto, At(b)).At?
    ensures Track(h, from, upto, At(a)).row < Track(h, from, upto, At(b)).row
    ensures Track(h, from, upto, At(b)).row - Track(h, from, upto, At(a)).row
         == (b - a) - (RemovedBetween(h, from, upto, At(a), At(b), false)
                     + RemovedBetween(h, from, upto, At(a), At(b), true))
    decreases upto - from
  {
    if from == upto { }
    else {
      var s := h[from];
      // Neither cell can go in this step: the walk would then be Gone at the end of the window.
      if !Survives(s, a) {
        assert TrackStep(s, At(a)) == Gone;
        TrackGoneStaysGone(h, from + 1, upto);
        assert false;
      }
      if !Survives(s, b) {
        assert TrackStep(s, At(b)) == Gone;
        TrackGoneStaysGone(h, from + 1, upto);
        assert false;
      }
      GapClosesOnlyByClearsBetween(s, a, b);
      CountBetweenIsLessThanTheGap(s.clearedRows, a, b);   // ... so the pair stays ordered
      GapEqualsRowsRemovedBetween(h, from + 1, upto, Advance(s, a), Advance(s, b));
    }
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
    // Measured at step j's LOCK, i.e. BEFORE step j's own clears — not "just after step j", which is
    // what this said until 2026-08-08. `RoofFinal` is `Track(h, j, k-1, ·)` and `Track` applies h[j],
    // so a row measured after step j would have step j applied to it twice. `ForecastIsSatisfiable`
    // agrees with the code and not with the old comment: it sets roofAt = 25 where step 0 clears row
    // 26, and asserts `Advance(h[0], 25) == 26`.
    roofAt: int,        // overhang's row, at step j's lock
    floorAt: int,       // row of the cell the nose will rest on, at step j's lock
    holeOpenAtJ: bool,  // was the cell directly above that floor already empty at step j?
    spinAtK: bool,      // did the piece at step k finish as a T-spin?
    // The two fields `improved` compares (pipeline/sim/forecast.ts:511-516). See the MODELLING
    // `improved` section for why they are `nat`, why `<= 3`, and why they stay pure extractor input.
    availAtJ: nat,      // bestTspinLines(board at step j's lock)   -- availAtRoof
    availAtK: nat       // bestTspinLines(board at step k-1's lock) -- availAtSpin
  )

  // ---------------------------------------------------------------------------------------------
  // WHICH STEP IS THE T-SPIN, and why `e.k <= |h|` is the answer.
  //
  // `Track(h, e.j, e.k - 1, ·)` needs only `e.k - 1 <= |h|`. `WellFormed` demands `e.k <= |h|`,
  // one tighter than anything in the file used — and that slack is the convention, written down
  // here for the first time: **the T-spin is the lock at index `e.k - 1`**, so it has to exist.
  // The window then applies `h[e.j] .. h[e.k - 2]`, i.e. step j's own clears (the overhang lands,
  // THEN j's rows come out) up to the last step before the spin. That is exactly the set of steps
  // `localiseMechanism` walks in `pipeline/sim/forecast.ts`, offset by the pre-clear measurement
  // of `roofAt`.
  //
  // Until 2026-08-09 `WellFormed` said nothing about `spinAtK` at all, and every witness in both
  // spec files set `e.spinAtK == true` while `h[e.k - 1].wasSpin == false` — the T-spin's own lock,
  // flagged as not a spin. Nothing caught it because the final step is read by nothing: `Track` and
  // `RemovedBetween` both stop before it. So the file carried two sources of truth for "was a spin"
  // and used only one of them.
  //
  // What this does NOT fix: `holeOpenAtJ`, `roofAt` and `floorAt` stay pure extractor input. They
  // are statements about BOARD CONTENT — which cell is empty, which row a cell sits in — and `Step`
  // carries `clearedRows`, `wasSpin` and `garbageRows` and no board at all. There is nothing in `h`
  // to relate them to. Clause 2, on which the corpus result turns, therefore still has zero
  // history-side content, and grounding it is a model change (the same one `forecast_garbage`
  // needs), not a stronger invariant.
  // ---------------------------------------------------------------------------------------------

  predicate WellFormed(h: History, e: Event) {
    && 0 <= e.j < e.k <= |h|
    && e.roofAt < e.floorAt          // the overhang is above the hole's floor
    && e.spinAtK == h[e.k - 1].wasSpin   // clause 1's flag is the history's flag, not a second one
    && e.availAtJ <= 3 && e.availAtK <= 3 // a T occupies at most three rows, so bestTspinLines is in 0..3
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

  /**
   * An overhang placed by the IMMEDIATELY PRECEDING piece can never be a forecast, whatever else
   * happened. With k == j + 1 the tracking window `Track(h, j, k-1, ...)` is empty, so neither cell
   * has moved and the gap is unchanged.
   *
   * This is the spec's counterpart of a behaviour `pipeline/sim/forecast.ts` gets structurally:
   * `localiseMechanism` walks `t` down from `k-1` while `t > j`, so at separation 1 there is no step
   * to attribute and the event falls through to `unattributed`. Stated here as a theorem for ALL
   * histories rather than left as an emergent property of a loop bound.
   *
   * READ THE FIRST SENTENCE AGAINST THE CONVENTION, which was only written down on 2026-08-09 (see
   * `WellFormed`). The T-spin is the lock at index `e.k - 1`, so `e.k == e.j + 1` puts the spin at
   * index `e.j` — the piece that placed the overhang and the piece that spun are the SAME lock, a
   * separation of zero, not "the immediately preceding piece". The lemma is true as stated and the
   * name is kept because renaming it strands references; what is corrected here is the prose, which
   * described the other reading of `k` and had nothing to check it against.
   */
  lemma SeparationOneIsNeverAForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires e.k == e.j + 1
    requires minLines >= 0
    ensures !IsForecast(h, e, minLines)
  { }

  /** ...and its hypotheses are satisfiable, so the lemma above is not vacuously true. */
  lemma SeparationOneIsReachable() returns (h: History, e: Event)
    ensures WellFormedHistory(h) && WellFormed(h, e)
    ensures e.k == e.j + 1 && Tucked(e) && HolePreExisted(e)
  {
    h := [ Step([], true, 0) ];
    e := Event(0, 1, 25, 29, true, true, 0, 0);
  }

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

  /**
   * Clause 1's missing universal. Every other clause has a "...IsNotAForecast" lemma quantified over
   * all histories; clause 1 was backed only by the single board in `NotASpinIsRejected`.
   *
   * The note that used to sit here said `WellFormed` never relates `spinAtK` to `h`, so the spec
   * could prove the predicate READS the flag and never that the flag is right. That is fixed for
   * clause 1 as of 2026-08-09 (see `WellFormed`) and `AForecastIsASpinInTheHistory` below is the
   * statement that was unprovable before. It remains true of clause 2, which is the one the corpus
   * result turns on.
   */
  lemma NotASpinIsNeverAForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires !e.spinAtK
    ensures !IsForecast(h, e, minLines)
    ensures !h[e.k - 1].wasSpin      // ... and the history agrees, which is the new part
  { }

  /**
   * Clause 1, finally said about the HISTORY rather than about a flag: a forecast's step `k - 1`
   * really is a spin. Not provable before the well-formedness relation, at any `minLines`, on any
   * history — `spinAtK` was a free field and `h[e.k - 1].wasSpin` was read by nothing.
   *
   * `ForecastIsSatisfiable` supplies a witness, so this is not vacuous.
   */
  lemma AForecastIsASpinInTheHistory(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires IsForecast(h, e, minLines)
    ensures h[e.k - 1].wasSpin
  { }

  // A roof laid on solid stack that opens up later is downstacking, not forecasting.
  lemma NoPreExistingHoleIsNotAForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires !e.holeOpenAtJ
    ensures !IsForecast(h, e, minLines)
  { }

  // Garbage lifts the pair together, so the opponent cannot close a gap. NOTE the proof route: the
  // body discharges CLAUSE 4 (`ClosedByPlain == 0`, via NoClearsMeansNoRemoval with spins=false),
  // not clause 3. Both clauses do fail on a clear-free window, so the lemma is true either way —
  // but this comment said "clause 3" for the reason and that is not what is proved here.
  lemma GarbageAloneCannotMakeAForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires minLines >= 1
    requires forall i :: e.j <= i < e.k - 1 ==> h[i].clearedRows == []
    ensures !IsForecast(h, e, minLines)
  {
    NoClearsMeansNoRemoval(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), false);
  }

  // ---------------------------------------------------------------------------------------------
  // CLAUSE 3'S UNIVERSALS. Added 2026-08-09; until then clause 3 was the only clause backed by
  // witnesses alone, and the two lemmas that named it (`GapClosesOnlyByClearsBetween`,
  // `GarbageNeverClosesAGap`) were both about a SINGLE step.
  // ---------------------------------------------------------------------------------------------

  /**
   * What clause 3 actually asserts, with the window collapsed away: the gap closes exactly when the
   * pair survives and at least one row was taken from between them. `GapClosed` quantifies over a
   * whole history; the right-hand side is two counts and a survival test.
   *
   * Note the `+ ClosedBySpins` — the C-Spin closes its own gap, so clause 3 is satisfied there and
   * the rejection has to come from clause 4. That is the whole reason the two clauses are separate.
   */
  lemma GapClosedIsExactlyRowsRemoved(h: History, e: Event)
    requires WellFormedHistory(h)
    requires WellFormed(h, e)
    ensures GapClosed(h, e)
        <==> (BothSurvive(h, e) && ClosedByPlain(h, e) + ClosedBySpins(h, e) >= 1)
  {
    if BothSurvive(h, e) {
      GapEqualsRowsRemovedBetween(h, e.j, e.k - 1, e.roofAt, e.floorAt);
    }
  }

  /**
   * The prose claim that clause 3 is redundant beside clause 4 at `minLines >= 1`, as a theorem.
   *
   * It is redundant only GIVEN `BothSurvive`, and that is not a technicality: rows can be taken from
   * between the pair early in the window and the overhang cleared away later, which leaves clause 4
   * satisfied and clause 3 false. So what clause 3 contributes at `minLines >= 1` is precisely
   * "and both cells are still there" — not nothing, but not what the comment on `IsForecastShape`
   * said it was either.
   */
  lemma Clause3FollowsFromClause4(h: History, e: Event, minLines: int)
    requires WellFormedHistory(h)
    requires WellFormed(h, e)
    requires minLines >= 1
    requires BothSurvive(h, e)
    requires ClosedByPlain(h, e) >= minLines
    ensures GapClosed(h, e)
  {
    RemovedBetweenNonNeg(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), true);
    GapClosedIsExactlyRowsRemoved(h, e);
  }

  lemma Clause3IsRedundantAtOneOrMore(h: History, e: Event, minLines: int)
    requires WellFormedHistory(h)
    requires WellFormed(h, e)
    requires minLines >= 1
    requires BothSurvive(h, e)
    ensures IsForecast(h, e, minLines)
        <==> (Tucked(e) && HolePreExisted(e) && ClosedByPlain(h, e) >= minLines)
  {
    if Tucked(e) && HolePreExisted(e) && ClosedByPlain(h, e) >= minLines {
      Clause3FollowsFromClause4(h, e, minLines);
    }
  }

  // The structural half, stated for symmetry with clauses 1, 2 and 4: each of those has a
  // "...IsNeverAForecast" quantified over all histories, and clause 3 had none.
  lemma NoGapClosedIsNeverAForecast(h: History, e: Event, minLines: int)
    requires WellFormed(h, e)
    requires !GapClosed(h, e)
    ensures !IsForecast(h, e, minLines)
  { }

  /**
   * Clause 3's substantive universal, and the one that covers the case the other rejection lemmas
   * leave open: `minLines == 0`, where clause 4 admits everything.
   *
   * Strictly generalises `GapClauseIsLoadBearingAtZero`, which is one board on which nothing was
   * cleared at all. This is every history in which nothing was taken from between the pair — the
   * clears can be arbitrarily large and arbitrarily many, as long as they fall outside the pair —
   * and `GarbageAloneCannotMakeAForecast` does not reach it, both because that lemma requires
   * `minLines >= 1` and because it requires the window to be clear-FREE.
   */
  lemma NothingRemovedIsNotEvenForecastShaped(h: History, e: Event)
    requires WellFormedHistory(h)
    requires WellFormed(h, e)
    requires ClosedByPlain(h, e) == 0 && ClosedBySpins(h, e) == 0
    ensures !GapClosed(h, e)
    ensures !IsForecastShape(h, e)
    ensures forall m: int :: !IsForecast(h, e, m)
  {
    GapClosedIsExactlyRowsRemoved(h, e);
  }

  /**
   * ...and its hypotheses are satisfiable, so the lemma above is not vacuously true. Same discipline
   * as `SeparationOneIsReachable`: `check_spec_vacuity.py` is one-directional and reports "not
   * shown" rather than "healthy", so a universal rejection lemma still needs a board reaching it.
   */
  lemma NothingRemovedIsReachable() returns (h: History, e: Event)
    ensures WellFormedHistory(h) && WellFormed(h, e)
    ensures Tucked(e) && HolePreExisted(e)
    ensures ClosedByPlain(h, e) == 0 && ClosedBySpins(h, e) == 0
  {
    h := [ Step([], false, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 27, true, true, 0, 0);
  }

  // ---------------------------------------------------------------------------------------------
  // MODELLING `improved` (ROADMAP item 7, 2026-08-09).
  //
  // `improved` is the implementation's dominant filter — it performs 653 of the 654 corpus
  // exclusions — and was the single largest thing this spec did not model. It sat on the inventory
  // as BLOCKED on the premise "a finite max needs a bounded position set". That premise is FALSE:
  // `improved` (pipeline/sim/forecast.ts:515) is
  //
  //     availAtSpin > availAtRoof
  //
  // where availAtRoof = bestTspinLines(board at step j) and availAtSpin = bestTspinLines(board at
  // step k-1). `bestTspinLines` is a max over LINE COUNTS, and a T-piece occupies at most three
  // rows, so BOTH sides are in 0..3 whatever the board — the bound is on the max's VALUE, not on
  // the position set the BFS searches. Boundedness of the position set is needed to COMPUTE the max
  // in a terminating search; it is NOT needed to STATE it, and Dafny is being asked to state it.
  //
  // WHAT THIS PROVES, AND WHAT IT DELIBERATELY DOES NOT.
  //
  // `Improved` and `GapClosed` are DIFFERENT predicates, and `ImprovedIsNotGapClosed` proves it in
  // both directions on game-producible inputs. That is the whole claim. It is NOT a proof that
  // `availAtJ`/`availAtK` are computed correctly, nor that `Improved` and clause 3 measure the same
  // thing — they do not, which is exactly why the implementation needs `improved` on TOP of the
  // gap machinery, and why modelling it was worth doing.
  //
  // WHY THE FIELDS STAY ABSTRACT (not grounded in `h` the way `spinAtK` now is). `spinAtK` could be
  // tied to the history because `h[e.k - 1].wasSpin` already carries "was the k-th lock a spin".
  // `availAtJ`/`availAtK` are `bestTspinLines(board)` — statements about which CELLS are filled —
  // and `Step` carries `clearedRows`, `wasSpin`, `garbageRows` and no board at all (the same note
  // sits on `holeOpenAtJ`/`roofAt`/`floorAt` at the `WellFormed` convention above). There is
  // nothing in `h` to derive them from, so grounding them is the board-carrying-`Step` model change
  // that ROADMAP items 4+8 are consolidated around, NOT a stronger invariant. They are therefore
  // the third and fourth pure-extractor fields on `Event`, and the deliverable is scoped to match:
  // a difference theorem, which cannot be mistaken for validation of the search.
  // ---------------------------------------------------------------------------------------------

  // The available T-spin lines rose between the overhang landing and the T going in. `bestTspinLines`
  // is bounded by 3, which `WellFormed` records; the predicate itself only compares the two.
  predicate Improved(e: Event) { e.availAtK > e.availAtJ }

  // THE DIFFERENCE THEOREM, in two halves. `Improved` and `GapClosed` disagree in BOTH directions,
  // so neither is a restatement of the other — on well-formed, game-producible inputs, not merely as
  // symbols. Split across two `returns` lemmas rather than one: evaluating GapClosed (which unfolds
  // Track over the window) for one witness while also carrying the other re-derives enough to time
  // out, the same encoding cost `SpinRowsDoNotCountTowardClause4` records. Each half pins its tracked
  // positions, which is what takes the obligation from a timeout to about a second.
  //
  // These witnesses ARE the anti-vacuity evidence `check_spec_vacuity.py` asks for: a `returns` lemma
  // states its own reachability, following `SeparationOneIsReachable`, instead of leaving the
  // verifier to search for one.

  /**
   * `Improved && !GapClosed`. The available spin ROSE (availAtK 2 > availAtJ 0) while the tracked
   * roof/floor gap did NOT close. This is the real shape behind `improved`'s independence: a slot can
   * open ELSEWHERE on the board (garbage, or a clear outside the pair) and lift `bestTspinLines`
   * without removing anything from between THIS overhang and THIS hole. The history is inert here, so
   * the gap is untouched.
   */
  lemma ImprovedNeedNotCloseTheGap() returns (h: History, e: Event)
    ensures WellFormedHistory(h) && WellFormed(h, e)
    ensures Improved(e) && !GapClosed(h, e)
  {
    h := [ Step([], false, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 27, true, true, 0, 2);
    assert RoofFinal(h, e) == At(25) && FloorFinal(h, e) == At(27);   // separation unchanged at 2
  }

  /**
   * `!Improved && GapClosed`. The tracked gap DID close — one plain row (26) taken from between the
   * pair — while the available spin did NOT rise (availAtK == availAtJ). Clause 3 fires; `Improved`
   * does not. The equality of the two avail fields is what kills the `> -> >=` mutant: under `>=`,
   * `2 >= 2` would make this event `Improved`, contradicting the ensures.
   */
  lemma GapCanCloseWithoutImproving() returns (h: History, e: Event)
    ensures WellFormedHistory(h) && WellFormed(h, e)
    ensures !Improved(e) && GapClosed(h, e)
  {
    h := [ Step([26], false, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 27, true, true, 2, 2);
    assert CountBetween([26], 25, 27) == 1;
    assert RoofFinal(h, e) == At(26) && FloorFinal(h, e) == At(27);   // separation falls 2 -> 1
  }

  /**
   * `Improved` reads ONLY the two `Event` fields — it never consults `h`. Stated as a theorem so an
   * edit that quietly makes `Improved` depend on the history (which would silently change what the
   * predicate means, and what the difference theorem above compares against) fails here. No
   * hypotheses, so `check_spec_vacuity.py` does not probe it; it is a definitional identity.
   */
  lemma ImprovedIsPurelyAnEventProperty(h: History, e: Event)
    ensures Improved(e) <==> e.availAtK > e.availAtJ
  { }

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
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    ensures WellFormed(h, e)
    ensures IsForecastAnyClear(h, e)
    // the exact count is part of the contract, so callers can reason about HOW MUCH was removed
    ensures ClosedByPlain(h, e) == 1
  {
    h := [ Step([26], false, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 27, true, true, 0, 0);
    assert CountBetween([26], 25, 27) == 1;
    assert Advance(h[0], 25) == 26 && Advance(h[0], 27) == 27;
    assert ClosedByPlain(h, e) == 1;
  }

  // The same board, but the clear that lowers the overhang is itself a T-spin — the C-Spin. The
  // gap closes exactly as before and the definition still says no.
  lemma CSpinWitnessIsRejected() returns (h: History, e: Event)
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    ensures WellFormed(h, e)
    ensures GapClosed(h, e)          // the gap really does close ...
    ensures !IsForecastAnyClear(h, e) // ... and it is still not a forecast
  {
    h := [ Step([26], true, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 27, true, true, 0, 0);
    assert CountBetween([26], 25, 27) == 1;
    assert ClosedByPlain(h, e) == 0;
    assert ClosedBySpins(h, e) == 1;
  }

  // And the case the player used to reject the currently-published event: everything else holds,
  // but the hole was not open when the overhang was placed.
  lemma NoHoleWitnessIsRejected() returns (h: History, e: Event)
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    ensures WellFormed(h, e)
    ensures GapClosed(h, e)
    ensures ClosedByPlain(h, e) >= 1
    ensures !IsForecastAnyClear(h, e)
  {
    h := [ Step([26], false, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 27, false, true, 0, 0);
    assert CountBetween([26], 25, 27) == 1;
  }

  // A T that lands without finishing as a spin is not a forecast however perfect the setup was.
  // Without this the `Tucked` clause is decorative: nothing else in the file ever sets spinAtK false.
  lemma NotASpinIsRejected() returns (h: History, e: Event)
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    ensures WellFormed(h, e)
    ensures GapClosed(h, e) && ClosedByPlain(h, e) >= 1 && HolePreExisted(e)
    ensures !IsForecastAnyClear(h, e)
  {
    h := [ Step([26], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 25, 27, true, false, 0, 0);
    assert CountBetween([26], 25, 27) == 1;
  }

  /**
   * THE WINDOW'S RIGHT ENDPOINT, made testable.
   *
   * `WellFormed` fixes the T-spin at index `e.k - 1`, so the window `Track(h, e.j, e.k - 1, ·)`
   * stops just before it and the spin's OWN line clear must not count toward closing the gap — the
   * gap has to be closed already for the T to fit. No witness tested that. Every other witness in
   * this file pads with an inert final step (`Step([], _, 0)`), which `Track` passes through
   * unchanged, so widening the window to `e.k` leaves all of their numbers alone. Measured on the
   * committed spec, that mutation is caught only by two UNIVERSALS whose hypotheses mention the
   * window bound (`SeparationOneIsNeverAForecast`, `GarbageAloneCannotMakeAForecast`) — and four
   * witnesses time out on it, settling nothing. So the endpoint was very nearly free to be off by
   * one, and it was justified only in a comment.
   *
   * Here the spin's own lock takes row 27, which lies between the tracked pair. `ClosedBySpins == 0`
   * and `RoofFinal == At(26)` are both false if the window runs one step longer.
   */
  lemma TheSpinsOwnClearDoesNotCloseTheGap() returns (h: History, e: Event)
    ensures WellFormedHistory(h)
    ensures WellFormed(h, e)
    ensures |h| == 2 && h[e.k - 1] == Step([27], true, 0)   // the T-spin's lock clears a row itself
    ensures RoofFinal(h, e) == At(26) && FloorFinal(h, e) == At(29)
    ensures ClosedBySpins(h, e) == 0                        // ... and that row is not counted
    ensures ClosedByPlain(h, e) == 1
    ensures IsForecastAnyClear(h, e)
  {
    h := [ Step([26], false, 0), Step([27], true, 0) ];
    e := Event(0, 2, 25, 29, true, true, 0, 0);
    assert CountBetween([26], 25, 29) == 1;
    assert Advance(h[0], 25) == 26 && Advance(h[0], 29) == 29;
  }

  // Garbage lifts the pair together and changes nothing between them. Stated on a witness that
  // actually HAS garbage, because every other lemma here sets garbageRows to 0 — which left the
  // `- s.garbageRows` term in `Advance` unpinned and a mutation deleting it undetected.
  lemma GarbageWitnessLeavesTheGapAlone() returns (h: History, e: Event)
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    ensures WellFormed(h, e)
    ensures h[0].garbageRows == 4
    ensures !GapClosed(h, e)              // four rows of garbage, gap unmoved
    ensures !IsForecastAnyClear(h, e)
  {
    h := [ Step([], false, 4), Step([], true, 0) ];
    e := Event(0, 2, 25, 27, true, true, 0, 0);
    assert Advance(h[0], 25) == 21 && Advance(h[0], 27) == 23;
    GarbageNeverClosesAGap(h[0], 25, 27);
  }

  // `GapClosed` looks redundant beside clause 4 — removing a row from between the pair does close
  // the gap — and at minLines >= 1 it ALMOST is. This comment said "it is", flatly, until
  // `Clause3FollowsFromClause4` turned the claim into a theorem and the proof produced the missing
  // hypothesis: the redundancy holds only GIVEN `BothSurvive`. Rows can come out from between the
  // pair early in the window and the overhang be cleared away later, which satisfies clause 4 and
  // falsifies clause 3. So what clause 3 adds at minLines >= 1 is exactly "and both cells are still
  // there". It is load-bearing outright at minLines == 0, the "forecast-shaped regardless of how
  // much was removed" reading, and is kept so that reading stays honest.
  predicate IsForecastShape(h: History, e: Event)
    requires WellFormed(h, e)
  { IsForecast(h, e, 0) }

  lemma GapClauseIsLoadBearingAtZero() returns (h: History, e: Event)
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    ensures WellFormed(h, e)
    ensures Tucked(e) && HolePreExisted(e) && ClosedByPlain(h, e) == 0
    ensures !GapClosed(h, e)
    ensures !IsForecastShape(h, e)        // false ONLY because the gap never closed
  {
    h := [ Step([], false, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 27, true, true, 0, 0);
    // Both tracked positions, pinned. Not decorative: without them the mutant that inverts the
    // gap test sends this obligation past 26 s and the whole mutant reads as UNRESOLVED (see
    // spec/mutate-forecast-spec.sh). With them it fails in 1.3 s, which is what a kill looks like.
    assert RoofFinal(h, e) == At(25) && FloorFinal(h, e) == At(27);
  }

  // The two readings of "triple line(s)" are genuinely different, so the choice cannot be silent.
  lemma TheTwoReadingsDiffer() returns (h: History, e: Event)
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
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

  // A range of consecutive rows repeats nothing — the obligation `WellFormedStep` needs, and the
  // only one of the RangeSeq helpers that was missing. Without it the two PARAMETRIC witnesses were
  // the only two of the ten that could not prove their own history physically possible.
  lemma RangeSeqNoDup(lo: int, n: nat)
    ensures NoDup(RangeSeq(lo, n))
    decreases n
  {
    if n == 0 {
    } else {
      RangeSeqNoDup(lo + 1, n - 1);
      RangeSeqExcludes(lo + 1, n - 1, lo);
      RangeSeqLen(lo + 1, n - 1);
      var rest := RangeSeq(lo + 1, n - 1);
      assert RangeSeq(lo, n) == [lo] + rest;
      forall i, j | 0 <= i < j < |RangeSeq(lo, n)|
        ensures RangeSeq(lo, n)[i] != RangeSeq(lo, n)[j]
      {
        if i == 0 {
          assert RangeSeq(lo, n)[j] == rest[j - 1];
          assert rest[j - 1] in rest;
        } else {
          assert RangeSeq(lo, n)[i] == rest[i - 1] && RangeSeq(lo, n)[j] == rest[j - 1];
        }
      }
    }
  }

  // ... and a cell below it does not move at all.
  lemma RangeSeqNoneBelow(lo: int, n: nat, r: int)
    requires lo + n <= r
    ensures CountBelow(RangeSeq(lo, n), r) == 0
    decreases n
  { if n == 0 { } else { RangeSeqNoneBelow(lo + 1, n - 1, r); } }

  /** ONE non-spin clear of ANY size n >= 1 taken from between the pair is a forecast. */
  lemma AnySizeOfClearIsAForecast(n: nat) returns (h: History, e: Event)
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    requires n >= 1
    ensures WellFormed(h, e)
    ensures |h| == 2 && !h[0].wasSpin && |h[0].clearedRows| == n   // ONE clear, n rows
    ensures ClosedByPlain(h, e) == n
    ensures IsForecastAnyClear(h, e)
    ensures n >= 3 ==> IsForecastTriple(h, e)                      // a Triple or a Tetris also qualifies
  {
    var cleared := RangeSeq(26, n);
    RangeSeqNoDup(26, n);
    RangeSeqLen(26, n);
    RangeSeqExcludes(26, n, 25);
    RangeSeqExcludes(26, n, 26 + n);
    RangeSeqBelow(26, n, 25);
    RangeSeqNoneBelow(26, n, 26 + n);
    RangeSeqBetween(26, n, 25, 26 + n);
    h := [ Step(cleared, false, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 26 + n, true, true, 0, 0);
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
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    ensures WellFormed(h, e)
    ensures |h| == 3 && |h[0].clearedRows| == 2 && |h[1].clearedRows| == 1   // a Double, then a Single
    ensures ClosedByPlain(h, e) == 3
    ensures IsForecastTriple(h, e)
  {
    h := [ Step([26, 27], false, 0), Step([28], false, 0), Step([], true, 0) ];
    e := Event(0, 3, 25, 30, true, true, 0, 0);
  }

  /**
   * A spin and a plain clear in the same window: only the plain rows count toward clause 4.
   *
   * The two counts are established one at a time through `RemovedBetweenSplit`. Asking for both in
   * one lemma re-derives the whole window twice and times out — the same encoding cost recorded on
   * the split lemma above.
   */
  const SPIN_THEN_PLAIN: History := [ Step([26], true, 0), Step([27], false, 0), Step([], true, 0) ]
  const SPIN_THEN_PLAIN_EVENT: Event := Event(0, 3, 25, 29, true, true, 0, 0)

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
    ensures WellFormedHistory(h)   // ADDED: the witness must be a history the game can produce
    requires n >= 1
    ensures WellFormed(h, e)
    ensures |h[0].clearedRows| == n && !h[0].wasSpin
    ensures ClosedByPlain(h, e) == 0
    ensures !GapClosed(h, e)
    ensures !IsForecastAnyClear(h, e)
  {
    var cleared := RangeSeq(30, n);      // strictly below the floor at row 29
    RangeSeqNoDup(30, n);
    RangeSeqLen(30, n);
    RangeSeqExcludes(30, n, 25);
    RangeSeqExcludes(30, n, 29);
    RangeSeqBelow(30, n, 25);
    RangeSeqBelow(30, n, 29);
    RangeSeqBetween(30, n, 29, 30 + n);
    h := [ Step(cleared, false, 0), Step([], true, 0) ];
    e := Event(0, 2, 25, 29, true, true, 0, 0);
    assert CountBetween(cleared, 25, 29) == 0 by { CountBelowSplit(cleared, 25, 29); }
    assert Advance(h[0], 25) == 25 + n && Advance(h[0], 29) == 29 + n;
    assert ClosedByPlain(h, e) == 0;
  }
}
