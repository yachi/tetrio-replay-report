// ForecastExamples.dfy — seven worked boards, each verdict machine-checked.
//
// Forecast.dfy states the definition and proves the general facts. This file does the opposite: it
// fixes seven concrete situations and asks the definition what it says about each. Every example is
// a `returns (h, e)` lemma, so a verdict here is a proof obligation, not a comment.
//
// The seven are chosen so that each of the four clauses is the SOLE reason for a rejection at least
// once, and so that the two readings of "triple line(s)" are separated by a real board. Examples
// A, C, D and F are the same situation differing in a single field each — one Event flag or one
// Step flag — so every rejection is provably caused by its clause. See the minimality lemmas at
// the bottom. The BOARDS drawn alongside are checked separately: every placement is a real
// tetromino orientation, resting on something, and reachable under SRS with its kick tables. That
// last check is not decorative — it rejected the first board drawn for example D outright.
//
// Row numbering matches Forecast.dfy: row 0 is the TOP, larger index is lower on the screen. The
// boards drawn alongside this file use a 22-row field, so the bottom row is 21:
//
//        row 15 ..JJ......   <- the overhang (the J's foot at column 3)
//        row 16 XXJ...XXX.      the row the T's bar will occupy
//        rows 17,18,19          three rows that are complete except column 9
//        row 20 XXXX.XXXXX      the T's nose ends here  (the HOLE, column 4)
//        row 21 .XXXXXXXXX      the cell it rests on    (the FLOOR, column 4)
//
// so roofAt = 15, floorAt = 21, and after three rows are taken from between them the pair sits at
// 18 and 21 — separation 3, which is exactly the geometry of a T-Spin Double: roof, bar, nose,
// floor on four consecutive rows.

include "Forecast.dfy"

module ForecastExamples {
  import opened Forecast

  // ===============================================================================================
  // ACCEPTED
  // ===============================================================================================

  // A. The player's own sentence, executed. An overhang lands six rows above an already-open hole;
  //    a vertical I completes the three rows between them; that clear is not a T-spin; the T tucks
  //    in for a Double. This is a forecast under BOTH readings.
  lemma ExampleA_PlainTripleClosesTheGap() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures IsForecastTriple(h, e) && IsForecastAnyClear(h, e) && IsForecastShape(h, e)
    ensures ClosedByPlain(h, e) == 3 && ClosedBySpins(h, e) == 0
    ensures h == [ Step([17, 18, 19], false, 0), Step([], false, 0) ] && e == Event(0, 2, 15, 21, true, true)
    ensures e.floorAt - e.roofAt == 6                        // before
    ensures BothSurvive(h, e)
    ensures FloorFinal(h, e).row - RoofFinal(h, e).row == 3  // after: the T-Spin Double geometry
  {
    h := [ Step([17, 18, 19], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 15, 21, true, true);
    assert CountBetween([17, 18, 19], 15, 21) == 3;
    assert Advance(h[0], 15) == 18 && Advance(h[0], 21) == 21;
  }

  // B. The same shape with ONE row between the overhang and the hole, taken by an ordinary Single.
  //    "a non tspin triple line(s) clear" has to decide whether this counts, and the two readings
  //    disagree here — which is why Forecast.dfy takes minLines as a parameter instead of guessing.
  lemma ExampleB_ASingleIsEnoughOnlyUnderTheLooseReading() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures IsForecastAnyClear(h, e)     // "one or more clears, none of them a T-spin"
    ensures !IsForecastTriple(h, e)      // "a clear of three lines"
    ensures ClosedByPlain(h, e) == 1
    ensures h == [ Step([19], false, 0), Step([], false, 0) ] && e == Event(0, 2, 17, 21, true, true)
  {
    h := [ Step([19], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 17, 21, true, true);
    assert CountBetween([19], 17, 21) == 1;
    assert Advance(h[0], 17) == 18 && Advance(h[0], 21) == 21;
  }

  // ===============================================================================================
  // REJECTED — one clause each
  // ===============================================================================================

  // C. Clause 2. Byte-for-byte example A, except that the cell the T's nose comes to rest on is a
  //    garbage cell that had not arrived when the overhang was placed. The gap really does close,
  //    and an ordinary triple really does close it — the roof was simply not laid over anything.
  //    This is the shape of the event the metric currently publishes, and the player rejected it.
  lemma ExampleC_TheFloorArrivedAfterTheRoof() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures GapClosed(h, e) && ClosedByPlain(h, e) == 3   // clauses 1, 3 and 4 all hold
    ensures !HolePreExisted(e)
    ensures !IsForecastAnyClear(h, e) && !IsForecastShape(h, e)
    ensures h == [ Step([17, 18, 19], false, 0), Step([], false, 0) ] && e == Event(0, 2, 15, 21, false, true)
  {
    h := [ Step([17, 18, 19], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 15, 21, false, true);
    assert CountBetween([17, 18, 19], 15, 21) == 3;
  }

  // Example D's board needs one more placement than the others: a filler that seals the column the
  // first T came down through. It clears nothing and takes no garbage, and this says that such a
  // placement is invisible to every clause — it moves no tracked cell and contributes to no count.
  // That is why D's history below has two steps and its drawing has an extra piece: the model is
  // not omitting something that could matter.
  lemma InertPlacementsAreInvisible(h: History, from: int, upto: int, a: Tracked, b: Tracked, spins: bool)
    requires 0 <= from <= upto <= |h|
    requires forall i :: from <= i < upto ==> h[i].clearedRows == [] && h[i].garbageRows == 0
    ensures RemovedBetween(h, from, upto, a, b, spins) == 0
    ensures Track(h, from, upto, a) == a
    decreases upto - from
  {
    if from == upto {
    } else {
      assert TrackStep(h[from], a) == a;
      NoClearsMeansNoRemoval(h, from, upto, a, b, spins);
      InertPlacementsAreInvisible(h, from + 1, upto, a, b, spins);
    }
  }

  // D. Clause 4. The C-Spin: the three rows are taken by a T-Spin Triple, so the overhang is
  //    lowered onto its slot by the player's own spin. Nothing was forecast — the setup and the
  //    thing that resolved it are the same memorised opener.
  //
  //    Unlike C and F this is NOT example A with one field changed, for a geometric reason worth
  //    recording. The board that carries the SECOND spin has its bar row complete apart from the
  //    three-wide pocket, and such a row roofs everything beneath it: a search over every T
  //    placement under it found no reachable spin at all. So the drawn board leaves one further
  //    column of that row open for the first T to descend through, and a filler piece closes it
  //    before the second T arrives. That filler clears nothing and takes no garbage, so by
  //    InertPlacementsAreInvisible it is not a step this model can see, and the history below is
  //    still example A's with one flag flipped.
  lemma ExampleD_TheCSpinLowersItsOwnRoof() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures GapClosed(h, e) && HolePreExisted(e) && Tucked(e)
    ensures ClosedBySpins(h, e) == 3 && ClosedByPlain(h, e) == 0
    ensures !IsForecastAnyClear(h, e)
    ensures h == [ Step([17, 18, 19], true, 0), Step([], false, 0) ]
         && e == Event(0, 2, 15, 21, true, true)
  {
    h := [ Step([17, 18, 19], true, 0), Step([], false, 0) ];
    e := Event(0, 2, 15, 21, true, true);
    assert CountBetween([17, 18, 19], 15, 21) == 3;
    CSpinIsNotAForecast(h, e, 1);
  }

  // E. Clause 3, the version that actually occurs. A board where nothing happens fails clause 3
  //    trivially — that is example G, and it is not worth two examples. This is the one that is:
  //    a line DOES clear and garbage DOES arrive, both from outside the interval between the
  //    overhang and the hole. The clear drops the pair by one together, the garbage lifts it by
  //    four together, and the distance between them is exactly what it was. No slot.
  //
  //    This is the shape that made the co-occurrence rule wrong. Over a window of the corpus's
  //    median length, SOME clear or SOME garbage arriving is close to certain, so "something
  //    happened during the window" is nearly a tautology; only "a row went from BETWEEN them"
  //    carries information. That is what the straddle test measures, and it is the shape 85 of
  //    the 86 audited line-clear events turned out to have.
  lemma ExampleE_AClearAndGarbageBothFromOutside() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures h[0].clearedRows == [21] && h[0].garbageRows == 4   // both confounds present at once
    ensures HolePreExisted(e) && Tucked(e)
    ensures BothSurvive(h, e)
    ensures CountBetween(h[0].clearedRows, e.roofAt, e.floorAt) == 0
    ensures FloorFinal(h, e).row - RoofFinal(h, e).row == e.floorAt - e.roofAt
    ensures ClosedByPlain(h, e) == 0
    ensures !GapClosed(h, e) && !IsForecastShape(h, e)
    ensures h == [ Step([21], false, 4), Step([], false, 0) ] && e == Event(0, 2, 16, 20, true, true)
  {
    h := [ Step([21], false, 4), Step([], false, 0) ];
    e := Event(0, 2, 16, 20, true, true);
    assert CountBetween([21], 16, 20) == 0;
    // both absolute positions, not only their difference: a mutation dropping the `- garbageRows`
    // term in Advance moves the pair together too, so the difference alone would not see it
    assert Advance(h[0], 16) == 13 && Advance(h[0], 20) == 17;
    GarbageNeverClosesAGap(h[0], 16, 20);
  }

  // F. Clause 1. The setup is example A in full — overhang over a pre-existing hole, gap closed by
  //    an ordinary triple — but the T is dropped flat on the stack instead of being tucked in.
  //    A forecast is a thing a player DOES, not a shape a board passes through.
  lemma ExampleF_ThePerfectSetupThatWasNeverSpun() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures HolePreExisted(e) && GapClosed(h, e) && ClosedByPlain(h, e) == 3
    ensures !Tucked(e) && !IsForecastShape(h, e)
    ensures h == [ Step([17, 18, 19], false, 0), Step([], false, 0) ] && e == Event(0, 2, 15, 21, true, false)
  {
    h := [ Step([17, 18, 19], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 15, 21, true, false);
    assert CountBetween([17, 18, 19], 15, 21) == 3;
  }

  // G. Clause 3, the player's version, and the overwhelming majority of real events: the slot is
  //    already complete the moment the overhang lands. Roof, bar row, nose and floor sit on four
  //    consecutive rows at step j, so there is nothing between the pair to remove. Rejected even at
  //    minLines == 0, which is the only reading under which clause 3 is load-bearing at all.
  lemma ExampleG_TheSlotWasCompleteWhenTheRoofLanded() returns (h: History, e: Event)
    ensures WellFormed(h, e)
    ensures Tucked(e) && HolePreExisted(e)
    ensures e.floorAt - e.roofAt == 3
    ensures ClosedByPlain(h, e) == 0 && !GapClosed(h, e)
    ensures !IsForecastShape(h, e)
  {
    h := [ Step([], false, 0), Step([], false, 0) ];
    e := Event(0, 2, 18, 21, true, true);
  }

  // ===============================================================================================
  // MINIMALITY. C, D and F each differ from A in exactly ONE field, so each rejection is caused by
  // its clause and nothing else. Stated as equalities on the datatype rather than in prose, so a
  // future edit that quietly changes a second field fails here.
  // ===============================================================================================

  lemma OnlyClause2SeparatesAFromC()
    ensures exists hA: History, eA: Event, hC: History, eC: Event ::
      (WellFormed(hA, eA) && WellFormed(hC, eC)
          && hA == hC && eC == eA.(holeOpenAtJ := false)
          && IsForecastTriple(hA, eA) && !IsForecastShape(hC, eC))
  {
    var hA, eA := ExampleA_PlainTripleClosesTheGap();
    var hC, eC := ExampleC_TheFloorArrivedAfterTheRoof();
    assert hA == hC && eC == eA.(holeOpenAtJ := false);
  }

  // D's drawn board needs one extra placement, so its own history is a step longer than A's. The
  // clause-4 claim does not depend on that: flipping wasSpin on A's history alone, with A's event
  // unchanged, already flips the verdict. Returned rather than asserted existentially, so the
  // witness is the lemma's own output instead of something the verifier has to go looking for.
  lemma OnlyClause4SeparatesAFromD() returns (hA: History, eA: Event, hD: History, eD: Event)
    ensures WellFormed(hA, eA) && WellFormed(hD, eD)
    ensures |hA| == 2 && eA == eD && hD == [hA[0].(wasSpin := true), hA[1]]
    ensures IsForecastTriple(hA, eA) && !IsForecastAnyClear(hD, eD)
  {
    hA, eA := ExampleA_PlainTripleClosesTheGap();
    hD, eD := ExampleD_TheCSpinLowersItsOwnRoof();
  }

  lemma OnlyClause1SeparatesAFromF()
    ensures exists hA: History, eA: Event, hF: History, eF: Event ::
      (WellFormed(hA, eA) && WellFormed(hF, eF)
          && hA == hF && eF == eA.(spinAtK := false)
          && IsForecastTriple(hA, eA) && !IsForecastShape(hF, eF))
  {
    var hA, eA := ExampleA_PlainTripleClosesTheGap();
    var hF, eF := ExampleF_ThePerfectSetupThatWasNeverSpun();
    assert hA == hF && eF == eA.(spinAtK := false);
  }

  // And the pair that is NOT a single-field edit: B differs from A in the history, not the event,
  // which is what makes it a statement about the reading rather than about the board.
  lemma TheReadingIsAChoiceAboutHowManyRows()
    ensures exists hA: History, eA: Event, hB: History, eB: Event ::
      (WellFormed(hA, eA) && WellFormed(hB, eB)
          && ClosedByPlain(hA, eA) == 3 && ClosedByPlain(hB, eB) == 1
          && IsForecastAnyClear(hA, eA) && IsForecastAnyClear(hB, eB)
          && IsForecastTriple(hA, eA) && !IsForecastTriple(hB, eB))
  {
    var hA, eA := ExampleA_PlainTripleClosesTheGap();
    var hB, eB := ExampleB_ASingleIsEnoughOnlyUnderTheLooseReading();
  }
}
