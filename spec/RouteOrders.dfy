// RouteOrders.dfy — the mathematics under pipeline/sim/route-orders.ts, and ONLY the mathematics.
//
// =================================== SCOPE — READ THIS FIRST ===================================
//
// route-orders.ts answers "which of the 5040 dealt orders let a player with one hold slot build a
// drawn route node". It splits that in two, and only the second half is proved anywhere:
//
//   ENGINE (NOT proved, NOT modelled here): which group can be placed on which subset's board — the
//   DAG edges `[subset, group]` in analysis/<opener>-orders.json. Those come from one engine's
//   `reach()` (kicks, spins, the planner's uLast / uFiresBefore / line-count rules). This file takes
//   the edges as DATA. Nothing here models kicks, reachability, gravity or spins.
//
//   MATHEMATICS (proved here):
//     T1  ORDER INDEPENDENCE of the SEQUENTIAL lock process (write a group's cells through the
//         rowmap, remove every full row, add empty rows on top, advance the rowmap exactly as
//         route-facts.ts `advanceRowmap` does). For cell-disjoint groups that avoid the initial
//         board, EVERY permutation of a set of groups is placeable at every step and leaves the same
//         engine board and rowmap. Stated over the process, not over a set-union board (which would
//         make it vacuous): the proof goes through a normal form `Canon(S)` and the step lemma
//         `LockStep(Canon(S), g) == Canon(With(S, g))`, which a no-compaction or clear-a-non-full-row
//         mutant breaks (mutate-routeorders.sh), and `T1Witness` pins a concrete run where a row
//         clears and the row above it must shift down.
//     T2  HOLD SEARCH. `Reach` is the nondeterministic step relation over (placed set s, stream
//         index i, hold h), stream = order ++ ['*']: (a) place stream[i]; (b) hold full: place the
//         held piece, stream[i] goes to the hold; (c) hold empty, stream[i] != '*': hold stream[i]
//         and place stream[i+1]. '*' is never placed. `Acc` is the recursive decision procedure of
//         route-orders.ts `accepts()` (same guard order), `Go` is its seen-set DFS exactly as the TS
//         writes it, and AccIffReach + Go's postcondition prove both decide `Reach`.
//     T4  EMPTY HOLD == NEXT HELD: for every order Q (no '*', |Q| >= 1),
//         Accepts(Q, empty hold) == Accepts(Q[1..], hold = Q[0]). Core: Acc(s, i, none) ==
//         Acc(s, i+1, stream[i]). `NoHoldFirstBreaksT4` exhibits a DAG and order where the variant
//         without case (c) violates it, so T4 is a fact about case (c), not a tautology.
//     T3  (counts) is not in this file: spec/RouteOrdersCount.dfy runs `AcceptsMemo` (proved equal to
//         `Accepts` below) over the committed DAGs, via spec/route_orders_data.py --check.
//
// MODEL FIDELITY (by inspection, not proved):
//   - an engine row is ERow(rid, cells): `rid` is the rowmap entry of that engine row
//     (rowmap[e] in route-facts.ts), `cells` the engine grid row (0 = empty, else a piece colour).
//     Keeping the two zipped is exactly `advanceRowmap`'s `rowmap.filter((_, e) => !cl.has(e))`
//     paired with applyCells' `g.splice(cl[k], 1)`: both drop the SAME indices, the full rows.
//   - `Place` writes every engine row whose rid is d; route-demos.ts writes rowmap.indexOf(d).
//     The two agree because rids are distinct (increasing) in every reachable state (CanonLabelsIncreasing).
//   - `Compact` = applyCells' splice-descending-then-push (filter out full rows, pad empties on
//     top) + advanceRowmap (fresh = max(1000, ...rowmap) + 1, then fresh++). Requires R <= 1000 so
//     a fresh label (>= 1001) is never a diagram row; route-facts.ts uses R = 40.
//   - the TS `accepts()` computes ONE group per token (`groupOf`); `Acc` quantifies over g with
//     `Fits`, which for a non-'*' token holds for that one group only. `GroupOf` takes the FIRST
//     dealt index where the TS Map keeps the LAST; route_orders_data.py refuses a node with two
//     dealt groups of one piece, so they coincide on every node it feeds through.
//   - `Mut` carries the runtime mutant switches the T3 runner uses (route-orders.ts `OrderMutants`
//     plus `holdNoPlace`). Every theorem is stated at NoMut.
//
// dafny verify spec/RouteOrders.dfy       — Dafny 4.11.0
// bash spec/mutate-routeorders.sh         — every planted mutant must die
// python3 spec/check_spec_vacuity.py spec/RouteOrders.dfy
// ================================================================================================
module RouteOrders {

  // ── T2 / T4: the hold search ───────────────────────────────────────────────────────────────

  datatype Hold = Empty | Held(t: char)

  // k groups; pieces[j] is group j's piece letter; carried is the index of the group a whole-bag
  // parent carried in the hold ('C' token), or -1; edge[s][g]: group g is placeable on board(s);
  // fullOk: the full set's board is the drawing.
  datatype Dag = Dag(k: nat, pieces: seq<char>, carried: int, edge: seq<seq<bool>>, fullOk: bool)

  datatype Mut = Mut(noSwap: bool, noHoldFirst: bool, placeStar: bool, noStar: bool, holdNoPlace: bool)

  const NoMut: Mut := Mut(false, false, false, false, false)

  datatype Key = Key(s: nat, i: nat, h: Hold)

  function Pow2(n: nat): nat
    ensures Pow2(n) >= 1
  {
    if n == 0 then 1 else 2 * Pow2(n - 1)
  }

  function FullSet(d: Dag): int
  {
    Pow2(d.k) - 1
  }

  function Bit(s: nat, g: nat): bool
  {
    (s / Pow2(g)) % 2 == 1
  }

  function DealtIndex(d: Dag, tok: char, j: nat): int
    decreases |d.pieces| - j
  {
    if j >= |d.pieces| then -1
    else if j != d.carried && d.pieces[j] == tok then j
    else DealtIndex(d, tok, j + 1)
  }

  // route-orders.ts groupOf: 'C' -> the carried group, '*' -> none, a piece -> its dealt group
  function GroupOf(d: Dag, tok: char): int
  {
    if tok == 'C' then d.carried
    else if tok == '*' then -1
    else DealtIndex(d, tok, 0)
  }

  // the edge test `can(g)`: unplaced, and the DAG has the edge s -> s + g
  predicate Can(d: Dag, s: nat, g: int)
  {
    0 <= g < d.k && s < |d.edge| && g < |d.edge[s]| && !Bit(s, g) && d.edge[s][g]
  }

  // which group a token may be placed as. A non-'*' token: exactly GroupOf. '*': none, unless the
  // placeStar mutant is on, which lets the next bag's piece stand in for any group.
  predicate Fits(d: Dag, m: Mut, tok: char, g: int)
  {
    if tok == '*' then m.placeStar else GroupOf(d, tok) == g
  }

  // the decision procedure: route-orders.ts `go`, without the seen set (Go below has it)
  function Acc(d: Dag, m: Mut, st: seq<char>, s: nat, i: nat, h: Hold): bool
    decreases |st| - i
  {
    if s == FullSet(d) then true
    else if i >= |st| then false
    else
      (exists g | 0 <= g < d.k :: Fits(d, m, st[i], g) && Can(d, s, g) && Acc(d, m, st, s + Pow2(g), i + 1, h))
      || (h.Held? && !m.noSwap && exists g | 0 <= g < d.k :: Fits(d, m, h.t, g) && Can(d, s, g) && Acc(d, m, st, s + Pow2(g), i + 1, Held(st[i])))
      || (h.Empty? && !m.noHoldFirst && st[i] != '*' && i + 1 < |st| && exists g | 0 <= g < d.k :: Fits(d, m, st[i + 1], g) && Can(d, s, g) && Acc(d, m, st, s + Pow2(g), i + 2, Held(st[i])))
      || (m.holdNoPlace && Acc(d, m, st, s, i + 1, Held(st[i])))
  }

  function Stream(m: Mut, order: seq<char>): seq<char>
  {
    if m.noStar then order else order + ['*']
  }

  function Accepts(d: Dag, m: Mut, order: seq<char>, h0: Hold): bool
  {
    d.fullOk && Acc(d, m, Stream(m, order), 0, 0, h0)
  }

  // ── the relation ──

  datatype Move = PlaceCur(g: int) | Swap(g: int) | HoldFirst(g: int)

  predicate StepOk(d: Dag, st: seq<char>, c: Key, mv: Move)
  {
    match mv
    case PlaceCur(g) => c.i < |st| && st[c.i] != '*' && GroupOf(d, st[c.i]) == g && Can(d, c.s, g)
    case Swap(g) => c.h.Held? && c.i < |st| && c.h.t != '*' && GroupOf(d, c.h.t) == g && Can(d, c.s, g)
    case HoldFirst(g) => c.h.Empty? && c.i + 1 < |st| && st[c.i] != '*' && st[c.i + 1] != '*' && GroupOf(d, st[c.i + 1]) == g && Can(d, c.s, g)
  }

  function Next(st: seq<char>, c: Key, mv: Move): Key
    requires 0 <= mv.g && c.i < |st|
  {
    match mv
    case PlaceCur(g) => Key(c.s + Pow2(g), c.i + 1, c.h)
    case Swap(g) => Key(c.s + Pow2(g), c.i + 1, Held(st[c.i]))
    case HoldFirst(g) => Key(c.s + Pow2(g), c.i + 2, Held(st[c.i]))
  }

  // the move list ms, applied from c, is legal at every step and ends with every group placed
  predicate Reaches(d: Dag, st: seq<char>, c: Key, ms: seq<Move>)
    decreases |ms|
  {
    if |ms| == 0 then c.s == FullSet(d)
    else StepOk(d, st, c, ms[0]) && Reaches(d, st, Next(st, c, ms[0]), ms[1..])
  }

  ghost predicate Reach(d: Dag, st: seq<char>, c: Key)
  {
    exists ms :: Reaches(d, st, c, ms)
  }

  // ── T2: the procedure decides the relation ──

  // ReachToAcc and AccToReach carry {:isolate_assertions} and name every step's facts in their own
  // assert so that a mutant breaking one case fails THAT assertion as a real error. As one VC each,
  // the two mutants that break a single case of the relation (no case (c); a hold step that places
  // nothing) left the theorem a TIMEOUT and only a witness lemma failed (measured 2026-10-18, 60 s).
  lemma {:isolate_assertions} ReachToAcc(d: Dag, st: seq<char>, c: Key, ms: seq<Move>)
    requires Reaches(d, st, c, ms)
    ensures Acc(d, NoMut, st, c.s, c.i, c.h)
    decreases |ms|
  {
    if c.s == FullSet(d) || |ms| == 0 {
    } else {
      var mv := ms[0];
      var c2 := Next(st, c, mv);
      ReachToAcc(d, st, c2, ms[1..]);
      match mv
      case PlaceCur(g) => assert Fits(d, NoMut, st[c.i], g) && Can(d, c.s, g);
      case Swap(g) => assert Fits(d, NoMut, c.h.t, g) && Can(d, c.s, g);
      case HoldFirst(g) => assert Fits(d, NoMut, st[c.i + 1], g) && Can(d, c.s, g);
    }
  }

  // one legal move, then a legal tail, is a legal move list: the step every case of AccToReach takes
  lemma ReachesCons(d: Dag, st: seq<char>, c: Key, mv: Move, rest: seq<Move>)
    requires 0 <= mv.g && c.i < |st|
    requires StepOk(d, st, c, mv)
    requires Reaches(d, st, Next(st, c, mv), rest)
    ensures Reaches(d, st, c, [mv] + rest)
  {
    assert ([mv] + rest)[1..] == rest;
  }

  lemma {:isolate_assertions} AccToReach(d: Dag, st: seq<char>, c: Key) returns (ms: seq<Move>)
    requires Acc(d, NoMut, st, c.s, c.i, c.h)
    ensures Reaches(d, st, c, ms)
    decreases |st| - c.i
  {
    if c.s == FullSet(d) {
      ms := [];
    } else if exists g | 0 <= g < d.k :: Fits(d, NoMut, st[c.i], g) && Can(d, c.s, g) && Acc(d, NoMut, st, c.s + Pow2(g), c.i + 1, c.h) {
      var g :| 0 <= g < d.k && Fits(d, NoMut, st[c.i], g) && Can(d, c.s, g) && Acc(d, NoMut, st, c.s + Pow2(g), c.i + 1, c.h);
      assert StepOk(d, st, c, PlaceCur(g));
      var rest := AccToReach(d, st, Key(c.s + Pow2(g), c.i + 1, c.h));
      ReachesCons(d, st, c, PlaceCur(g), rest);
      ms := [PlaceCur(g)] + rest;
    } else if c.h.Held? && exists g | 0 <= g < d.k :: Fits(d, NoMut, c.h.t, g) && Can(d, c.s, g) && Acc(d, NoMut, st, c.s + Pow2(g), c.i + 1, Held(st[c.i])) {
      var g :| 0 <= g < d.k && Fits(d, NoMut, c.h.t, g) && Can(d, c.s, g) && Acc(d, NoMut, st, c.s + Pow2(g), c.i + 1, Held(st[c.i]));
      assert StepOk(d, st, c, Swap(g));
      var rest := AccToReach(d, st, Key(c.s + Pow2(g), c.i + 1, Held(st[c.i])));
      ReachesCons(d, st, c, Swap(g), rest);
      ms := [Swap(g)] + rest;
    } else {
      assert c.h.Empty? && st[c.i] != '*' && c.i + 1 < |st|;
      var g :| 0 <= g < d.k && Fits(d, NoMut, st[c.i + 1], g) && Can(d, c.s, g) && Acc(d, NoMut, st, c.s + Pow2(g), c.i + 2, Held(st[c.i]));
      assert st[c.i + 1] != '*' && GroupOf(d, st[c.i + 1]) == g;
      assert StepOk(d, st, c, HoldFirst(g));
      var rest := AccToReach(d, st, Key(c.s + Pow2(g), c.i + 2, Held(st[c.i])));
      ReachesCons(d, st, c, HoldFirst(g), rest);
      ms := [HoldFirst(g)] + rest;
    }
  }

  lemma AccIffReach(d: Dag, st: seq<char>, c: Key)
    ensures Acc(d, NoMut, st, c.s, c.i, c.h) <==> Reach(d, st, c)
  {
    if Acc(d, NoMut, st, c.s, c.i, c.h) {
      var ms := AccToReach(d, st, c);
    }
    if Reach(d, st, c) {
      var ms :| Reaches(d, st, c, ms);
      ReachToAcc(d, st, c, ms);
    }
  }

  // T2 at the level route-orders.ts reports: a node accepts an order iff full_ok and the relation
  // reaches the full set from (empty set, stream index 0, the starting hold)
  lemma AcceptsIffReach(d: Dag, order: seq<char>, h0: Hold)
    ensures Accepts(d, NoMut, order, h0) <==> d.fullOk && Reach(d, order + ['*'], Key(0, 0, h0))
  {
    AccIffReach(d, order + ['*'], Key(0, 0, h0));
  }

  // ── the seen-set DFS, exactly as route-orders.ts `go` writes it ──
  //
  // TS: `if (s === full) return true; if (seen.has(key)) return false; seen.add(key); ...`. A key in
  // `seen` with an index >= the caller's is one whose search already returned false (any true return
  // propagates straight to the top), and a search only ever visits keys of larger index, so the
  // keys of in-progress ancestors (smaller index) are never consulted. That is the invariant.

  ghost predicate SeenFalseFrom(d: Dag, m: Mut, st: seq<char>, seen: set<Key>, i: nat)
  {
    forall q :: q in seen && q.i >= i ==> !Acc(d, m, st, q.s, q.i, q.h)
  }

  method {:isolate_assertions} Go(d: Dag, m: Mut, st: seq<char>, s: nat, i: nat, h: Hold, seen0: set<Key>) returns (r: bool, seen: set<Key>)
    requires SeenFalseFrom(d, m, st, seen0, i)
    ensures r == Acc(d, m, st, s, i, h)
    ensures forall q :: q in seen ==> q in seen0 || q.i >= i
    ensures !r ==> SeenFalseFrom(d, m, st, seen, i)
    decreases |st| - i
  {
    seen := seen0;
    if s == FullSet(d) { return true, seen; }
    var key := Key(s, i, h);
    if key in seen { return false, seen; }
    seen := seen + {key};
    if i >= |st| { return false, seen; }
    var cur := st[i];
    // (a) place the current piece
    var g := 0;
    while g < d.k
      invariant 0 <= g <= d.k
      invariant SeenFalseFrom(d, m, st, seen, i + 1)
      invariant forall q :: q in seen ==> q in seen0 || q == key || q.i >= i + 1
      invariant forall g' | 0 <= g' < g :: !(Fits(d, m, cur, g') && Can(d, s, g') && Acc(d, m, st, s + Pow2(g'), i + 1, h))
    {
      if Fits(d, m, cur, g) && Can(d, s, g) {
        var r1;
        r1, seen := Go(d, m, st, s + Pow2(g), i + 1, h, seen);
        if r1 { return true, seen; }
      }
      g := g + 1;
    }
    // (b) swap: place the held piece, the current one goes into the hold
    if h.Held? && !m.noSwap {
      g := 0;
      while g < d.k
        invariant 0 <= g <= d.k
        invariant SeenFalseFrom(d, m, st, seen, i + 1)
        invariant forall q :: q in seen ==> q in seen0 || q == key || q.i >= i + 1
        invariant forall g' | 0 <= g' < g :: !(Fits(d, m, h.t, g') && Can(d, s, g') && Acc(d, m, st, s + Pow2(g'), i + 1, Held(cur)))
      {
        if Fits(d, m, h.t, g) && Can(d, s, g) {
          var r1;
          r1, seen := Go(d, m, st, s + Pow2(g), i + 1, Held(cur), seen);
          if r1 { return true, seen; }
        }
        g := g + 1;
      }
    }
    // (c) hold empty: hold the current piece, place the next one
    if h.Empty? && !m.noHoldFirst && cur != '*' && i + 1 < |st| {
      g := 0;
      while g < d.k
        invariant 0 <= g <= d.k
        invariant SeenFalseFrom(d, m, st, seen, i + 1)
        invariant forall q :: q in seen ==> q in seen0 || q == key || q.i >= i + 1
        invariant forall g' | 0 <= g' < g :: !(Fits(d, m, st[i + 1], g') && Can(d, s, g') && Acc(d, m, st, s + Pow2(g'), i + 2, Held(cur)))
      {
        if Fits(d, m, st[i + 1], g) && Can(d, s, g) {
          var r1;
          r1, seen := Go(d, m, st, s + Pow2(g), i + 2, Held(cur), seen);
          if r1 { return true, seen; }
        }
        g := g + 1;
      }
    }
    // the holdNoPlace mutant only
    if m.holdNoPlace {
      var r1;
      r1, seen := Go(d, m, st, s, i + 1, Held(cur), seen);
      if r1 { return true, seen; }
    }
    assert !Acc(d, m, st, s, i, h);
    return false, seen;
  }

  method AcceptsMemo(d: Dag, m: Mut, order: seq<char>, h0: Hold) returns (r: bool)
    ensures r == Accepts(d, m, order, h0)
  {
    if !d.fullOk { return false; }
    var seen;
    r, seen := Go(d, m, Stream(m, order), 0, 0, h0, {});
  }

  // ── T4: an empty hold accepts exactly what "the next piece already held" accepts ──

  ghost predicate StarOnlyLast(st: seq<char>)
  {
    |st| > 0 && st[|st| - 1] == '*' && forall j :: 0 <= j < |st| - 1 ==> st[j] != '*'
  }

  lemma HoldIsDeferral(d: Dag, st: seq<char>, s: nat, i: nat)
    requires StarOnlyLast(st)
    requires i < |st|
    ensures Acc(d, NoMut, st, s, i, Empty) == Acc(d, NoMut, st, s, i + 1, Held(st[i]))
    decreases |st| - i
  {
    if s == FullSet(d) || i == |st| - 1 {
    } else {
      // (a) on the left pairs with (b) on the right: place st[i] now, or swap it out of the hold
      // one step later — which by induction is the same as having an empty hold at i + 1
      forall g | 0 <= g < d.k && Fits(d, NoMut, st[i], g) && Can(d, s, g)
        ensures Acc(d, NoMut, st, s + Pow2(g), i + 1, Empty) == Acc(d, NoMut, st, s + Pow2(g), i + 2, Held(st[i + 1]))
      {
        HoldIsDeferral(d, st, s + Pow2(g), i + 1);
      }
      // (c) on the left is (a) on the right, literally
    }
  }

  lemma ShiftStream(d: Dag, m: Mut, st: seq<char>, s: nat, i: nat, h: Hold)
    requires |st| > 0
    ensures Acc(d, m, st, s, i + 1, h) == Acc(d, m, st[1..], s, i, h)
    decreases |st| - i
  {
    if s == FullSet(d) || i + 1 >= |st| {
    } else {
      var t := st[1..];
      assert t[i] == st[i + 1];
      if i + 2 < |st| { assert t[i + 1] == st[i + 2]; }
      forall g | 0 <= g < d.k
        ensures Acc(d, m, st, s + Pow2(g), i + 2, h) == Acc(d, m, t, s + Pow2(g), i + 1, h)
        ensures Acc(d, m, st, s + Pow2(g), i + 2, Held(st[i + 1])) == Acc(d, m, t, s + Pow2(g), i + 1, Held(t[i]))
        ensures Acc(d, m, st, s + Pow2(g), i + 3, Held(st[i + 1])) == Acc(d, m, t, s + Pow2(g), i + 2, Held(t[i]))
      {
        ShiftStream(d, m, st, s + Pow2(g), i + 1, h);
        ShiftStream(d, m, st, s + Pow2(g), i + 1, Held(st[i + 1]));
        ShiftStream(d, m, st, s + Pow2(g), i + 2, Held(st[i + 1]));
      }
      ShiftStream(d, m, st, s, i + 1, Held(st[i + 1]));
    }
  }

  lemma EmptyHoldIsNextHeld(d: Dag, q: seq<char>)
    requires |q| > 0
    requires forall j :: 0 <= j < |q| ==> q[j] != '*'
    ensures Accepts(d, NoMut, q, Empty) == Accepts(d, NoMut, q[1..], Held(q[0]))
  {
    var st := q + ['*'];
    assert StarOnlyLast(st);
    HoldIsDeferral(d, st, 0, 0);
    ShiftStream(d, NoMut, st, 0, 0, Held(q[0]));
    assert st[1..] == q[1..] + ['*'];
  }

  // ── witnesses: no T2 / T4 lemma above is a statement about a constant ──

  // one group, the T, placeable on the empty set: k = 1, edge[0][0], full set 1
  function OneT(): Dag
  {
    Dag(1, ['T'], -1, [[true], [false]], true)
  }

  lemma T2Witness()
  {
    var d := OneT();
    assert FullSet(d) == 1;
    assert GroupOf(d, 'T') == 0;
    assert GroupOf(d, 'I') == -1;
    assert Can(d, 0, 0);
    // "T": accepted by (a) alone
    assert Acc(d, NoMut, ['T', '*'], 1, 1, Empty);
    assert Accepts(d, NoMut, ['T'], Empty);
    assert Reaches(d, ['T', '*'], Key(0, 0, Empty), [PlaceCur(0)]);
    // "IT": only (c) builds it — hold the I, place the T
    assert Fits(d, NoMut, 'T', 0);
    assert Acc(d, NoMut, ['I', 'T', '*'], 1, 2, Held('I'));
    assert Accepts(d, NoMut, ['I', 'T'], Empty);
    assert Reaches(d, ['I', 'T', '*'], Key(0, 0, Empty), [HoldFirst(0)]);
    // T held, stream "I": only (b) builds it — swap the T out
    assert Acc(d, NoMut, ['I', '*'], 1, 1, Held('I'));
    assert Accepts(d, NoMut, ['I'], Held('T'));
    assert Reaches(d, ['I', '*'], Key(0, 0, Held('T')), [Swap(0)]);
    // and a rejection: "IO" with an empty hold — the T is never dealt
    assert !Acc(d, NoMut, ['I', 'O', '*'], 0, 3, Held('I'));
    assert !Acc(d, NoMut, ['I', 'O', '*'], 0, 2, Held('I'));
    assert !Acc(d, NoMut, ['I', 'O', '*'], 0, 1, Empty);
    assert !Acc(d, NoMut, ['I', 'O', '*'], 0, 0, Empty);
    assert !Accepts(d, NoMut, ['I', 'O'], Empty);
    // the '*' is never placed: T held, stream "": the swap pulls the '*' into the hold
    assert Accepts(d, NoMut, [], Held('T'));
    assert !Acc(d, NoMut, ['*'], 0, 0, Empty);
  }

  // the relation itself, read with no help from Acc: with a junk piece in the hold and the T only
  // AFTER the O, there is no first move at all — the held I cannot be placed, the O cannot be
  // placed, and a full hold forbids (c). So the relation rejects it, and a relation that let the
  // player drop the held piece without placing anything would not.
  lemma JunkHoldHasNoMove()
  {
    var d := OneT();
    var st := ['O', 'T', '*'];
    var c := Key(0, 0, Held('I'));
    assert GroupOf(d, 'O') == -1 && GroupOf(d, 'I') == -1;
    forall mv: Move
      ensures !StepOk(d, st, c, mv)
    {
    }
    forall ms: seq<Move>
      ensures !Reaches(d, st, c, ms)
    {
      if |ms| > 0 { assert !StepOk(d, st, c, ms[0]); }
    }
    assert !Reach(d, st, c);
    // and Acc agrees, as T2 says it must
    assert !Acc(d, NoMut, st, 0, 0, Held('I'));
  }

  // T4 is a fact about case (c): drop it and an empty hold rejects "IT" while "T held, then I"
  // ... accepts the same deal
  lemma NoHoldFirstBreaksT4()
    ensures exists d: Dag, q: seq<char> :: |q| > 0 && Accepts(d, Mut(false, true, false, false, false), q, Empty) != Accepts(d, Mut(false, true, false, false, false), q[1..], Held(q[0]))
  {
    var d := OneT();
    var m := Mut(false, true, false, false, false);
    var q := ['I', 'T'];
    assert q[1..] == ['T'];
    assert Fits(d, m, 'T', 0) && Can(d, 0, 0);
    assert Acc(d, m, ['T', '*'], 1, 1, Held('I'));
    assert Acc(d, m, ['T', '*'], 0, 0, Held('I'));
    assert Accepts(d, m, q[1..], Held(q[0]));
    assert !Acc(d, m, ['I', 'T', '*'], 0, 0, Empty);
    assert !Accepts(d, m, q, Empty);
  }


  // ── T1: order independence of the SEQUENTIAL lock process ─────────────────────────────────

  // a group's cell in DIAGRAM coordinates: column x, diagram row d (0 = bottom, as y-UP)
  datatype Cell = Cell(x: int, d: int)
  // one placement group: its cells and its colour (the piece letter, as a nonzero code)
  datatype Grp = Grp(cells: set<Cell>, col: int)
  // one engine row: `label` is rowmap[e] for this engine row e, `cells` the grid row (0 = empty)
  datatype ERow = ERow(rid: int, cells: seq<int>)

  // advanceRowmap: `let fresh = Math.max(1000, ...rowmap) + 1`
  const FRESH_FLOOR: int := 1000

  function Max(a: int, b: int): int
  {
    if a >= b then a else b
  }

  function Zeros(w: nat): seq<int>
  {
    seq(w, _ => 0)
  }

  // linesOf: a row is cleared when every cell is filled
  predicate FullRow(r: seq<int>)
  {
    forall x :: 0 <= x < |r| ==> r[x] != 0
  }

  // referenced only by spec/mutate-routeorders.sh ("clear a row that is not full"): one cell short
  predicate NearFullRow(r: seq<int>)
  {
    Filled(r) + 1 >= |r|
  }

  function Filled(r: seq<int>): nat
    decreases |r|
  {
    if |r| == 0 then 0 else (if r[0] != 0 then 1 else 0) + Filled(r[1..])
  }

  // applyCells' write, through the rowmap: the cell (x, d) lands in the engine row whose label is d
  function PlaceRow(r: ERow, g: Grp): ERow
  {
    ERow(r.rid, seq(|r.cells|, x requires 0 <= x < |r.cells| => if Cell(x, r.rid) in g.cells then g.col else r.cells[x]))
  }

  function Place(e: seq<ERow>, g: Grp): seq<ERow>
  {
    seq(|e|, j requires 0 <= j < |e| => PlaceRow(e[j], g))
  }

  // the rows a lock leaves on the board, bottom to top (applyCells' splice of every full row)
  function KeepRows(e: seq<ERow>): seq<ERow>
    ensures |KeepRows(e)| <= |e|
    decreases |e|
  {
    if |e| == 0 then [] else (if FullRow(e[0].cells) then [] else [e[0]]) + KeepRows(e[1..])
  }

  // Math.max(1000, ...rowmap)
  function MaxLabel(e: seq<ERow>): int
    decreases |e|
  {
    if |e| == 0 then FRESH_FLOOR else Max(e[0].rid, MaxLabel(e[1..]))
  }

  // n empty rows on top, labelled f, f + 1, ... (`keep.push(fresh++)`, `g.push(new Array(WIDTH))`)
  function FreshRows(f: int, n: nat, w: nat): seq<ERow>
  {
    seq(n, j => ERow(f + j, Zeros(w)))
  }

  // compaction + advanceRowmap, one step
  function Compact(e: seq<ERow>, w: nat): seq<ERow>
  {
    KeepRows(e) + FreshRows(MaxLabel(e) + 1, |e| - |KeepRows(e)|, w)
  }

  // referenced only by spec/mutate-routeorders.sh ("clear without compaction"): empty a full row in
  // place, nothing shifts and the rowmap does not move
  function ClearInPlace(e: seq<ERow>, w: nat): seq<ERow>
  {
    seq(|e|, j requires 0 <= j < |e| => if FullRow(e[j].cells) then ERow(e[j].rid, Zeros(w)) else e[j])
  }

  function LockStep(e: seq<ERow>, g: Grp, w: nat): seq<ERow>
  {
    Compact(Place(e, g), w)
  }

  // place the groups in the order p, one lock at a time
  function Run(e: seq<ERow>, G: seq<Grp>, p: seq<nat>, w: nat): seq<ERow>
    decreases |p|
  {
    if |p| == 0 then e
    else if p[0] < |G| then Run(LockStep(e, G[p[0]], w), G, p[1..], w)
    else e
  }

  // route-orders.ts nodeDag's guards: every cell's diagram row is still on the board
  // (`rowmap.indexOf(d) >= 0`) and the target cell is empty
  ghost predicate Placeable(e: seq<ERow>, g: Grp)
  {
    forall c :: c in g.cells ==> exists j :: 0 <= j < |e| && e[j].rid == c.d && 0 <= c.x < |e[j].cells| && e[j].cells[c.x] == 0
  }

  ghost predicate AllPlaceable(e: seq<ERow>, G: seq<Grp>, p: seq<nat>, w: nat)
    decreases |p|
  {
    if |p| == 0 then true
    else p[0] < |G| && Placeable(e, G[p[0]]) && AllPlaceable(LockStep(e, G[p[0]], w), G, p[1..], w)
  }

  // the starting engine state: the parent's board, rowmap the identity (initialRowmap)
  function Init(B0: seq<seq<int>>): seq<ERow>
  {
    seq(|B0|, d requires 0 <= d < |B0| => ERow(d, B0[d]))
  }

  ghost predicate T1Hyp(B0: seq<seq<int>>, G: seq<Grp>, w: nat)
  {
    0 < w && 0 < |B0| <= FRESH_FLOOR
    && (forall d :: 0 <= d < |B0| ==> |B0[d]| == w && !FullRow(B0[d]))
    && (forall j :: 0 <= j < |G| ==> G[j].col != 0)
    && (forall j, c :: 0 <= j < |G| && c in G[j].cells ==> 0 <= c.x < w && 0 <= c.d < |B0| && B0[c.d][c.x] == 0)
    && (forall a, b, c :: 0 <= a < |G| && 0 <= b < |G| && a != b && c in G[a].cells ==> c !in G[b].cells)
  }

  function NoGroups(): set<nat>
  {
    {}
  }

  function With(S: set<nat>, g: nat): set<nat>
  {
    S + {g}
  }

  function SetOf(p: seq<nat>): set<nat>
  {
    set x: nat | x in p
  }

  ghost predicate ValidOrder(G: seq<Grp>, p: seq<nat>)
  {
    (forall j :: 0 <= j < |p| ==> p[j] < |G|) && (forall a, b :: 0 <= a < b < |p| ==> p[a] != p[b])
  }

  // ── the normal form: a function of the SET placed ──

  function Own(G: seq<Grp>, S: set<nat>, c: Cell, j: nat): int
    decreases |G| - j
  {
    if j >= |G| then 0 else if j in S && c in G[j].cells then G[j].col else Own(G, S, c, j + 1)
  }

  // the diagram row d after the groups S: the parent's cells plus the groups' cells
  function Comp(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, d: int, w: nat): seq<int>
  {
    seq(w, x requires 0 <= x < w => if 0 <= d < |B0| && x < |B0[d]| && B0[d][x] != 0 then B0[d][x] else Own(G, S, Cell(x, d), 0))
  }

  // the diagram rows d .. |B0|-1 not full after S, as engine rows labelled by their diagram row
  function Kept(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, w: nat, d: nat): seq<ERow>
    ensures d <= |B0| ==> |Kept(B0, G, S, w, d)| <= |B0| - d
    decreases |B0| - d
  {
    if d >= |B0| then []
    else (if FullRow(Comp(B0, G, S, d, w)) then [] else [ERow(d, Comp(B0, G, S, d, w))]) + Kept(B0, G, S, w, d + 1)
  }

  // the same rows, kept by S's fullness, holding S2's contents (the board just after a write)
  function KeptMixed(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, S2: set<nat>, w: nat, d: nat): seq<ERow>
    decreases |B0| - d
  {
    if d >= |B0| then []
    else (if FullRow(Comp(B0, G, S, d, w)) then [] else [ERow(d, Comp(B0, G, S2, d, w))]) + KeptMixed(B0, G, S, S2, w, d + 1)
  }

  function Canon(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, w: nat): seq<ERow>
  {
    Kept(B0, G, S, w, 0) + FreshRows(FRESH_FLOOR + 1, |B0| - |Kept(B0, G, S, w, 0)|, w)
  }

  // ── ownership ──

  lemma OwnIs(G: seq<Grp>, S: set<nat>, c: Cell, g: nat, j: nat)
    requires j <= g < |G| && g in S && c in G[g].cells
    requires forall a, b :: 0 <= a < |G| && 0 <= b < |G| && a != b && c in G[a].cells ==> c !in G[b].cells
    ensures Own(G, S, c, j) == G[g].col
    decreases g - j
  {
    if j < g { OwnIs(G, S, c, g, j + 1); }
  }

  lemma OwnNone(G: seq<Grp>, S: set<nat>, c: Cell, j: nat)
    requires forall a :: j <= a < |G| && a in S ==> c !in G[a].cells
    ensures Own(G, S, c, j) == 0
    decreases |G| - j
  {
    if j < |G| { OwnNone(G, S, c, j + 1); }
  }

  lemma OwnAddOther(G: seq<Grp>, S: set<nat>, c: Cell, g: nat, j: nat)
    requires g < |G| && c !in G[g].cells
    ensures Own(G, With(S, g), c, j) == Own(G, S, c, j)
    decreases |G| - j
  {
    if j < |G| { OwnAddOther(G, S, c, g, j + 1); }
  }

  // ── one lock on the normal form ──

  lemma CompAdd(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, g: nat, w: nat, d: nat)
    requires T1Hyp(B0, G, w) && g < |G| && g !in S && d < |B0|
    ensures PlaceRow(ERow(d, Comp(B0, G, S, d, w)), G[g]) == ERow(d, Comp(B0, G, With(S, g), d, w))
    ensures FullRow(Comp(B0, G, S, d, w)) ==> FullRow(Comp(B0, G, With(S, g), d, w))
  {
    var a := PlaceRow(ERow(d, Comp(B0, G, S, d, w)), G[g]).cells;
    var b := Comp(B0, G, With(S, g), d, w);
    forall x | 0 <= x < w
      ensures a[x] == b[x]
      ensures Comp(B0, G, S, d, w)[x] != 0 ==> b[x] != 0
    {
      var c := Cell(x, d);
      if c in G[g].cells {
        OwnIs(G, With(S, g), c, g, 0);
      } else {
        OwnAddOther(G, S, c, g, 0);
      }
    }
  }

  lemma KeepConcat(a: seq<ERow>, b: seq<ERow>)
    ensures KeepRows(a + b) == KeepRows(a) + KeepRows(b)
    decreases |a|
  {
    if |a| > 0 {
      assert (a + b)[1..] == a[1..] + b;
      KeepConcat(a[1..], b);
    } else {
      assert a + b == b;
    }
  }

  lemma PlaceConcat(a: seq<ERow>, b: seq<ERow>, g: Grp)
    ensures Place(a + b, g) == Place(a, g) + Place(b, g)
  {
  }

  lemma PlaceKept(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, g: nat, w: nat, d: nat)
    requires T1Hyp(B0, G, w) && g < |G| && g !in S
    ensures Place(Kept(B0, G, S, w, d), G[g]) == KeptMixed(B0, G, S, With(S, g), w, d)
    decreases |B0| - d
  {
    if d < |B0| {
      var head := if FullRow(Comp(B0, G, S, d, w)) then [] else [ERow(d, Comp(B0, G, S, d, w))];
      PlaceConcat(head, Kept(B0, G, S, w, d + 1), G[g]);
      CompAdd(B0, G, S, g, w, d);
      PlaceKept(B0, G, S, g, w, d + 1);
    }
  }

  lemma KeepMixed(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, g: nat, w: nat, d: nat)
    requires T1Hyp(B0, G, w) && g < |G| && g !in S
    ensures KeepRows(KeptMixed(B0, G, S, With(S, g), w, d)) == Kept(B0, G, With(S, g), w, d)
    decreases |B0| - d
  {
    if d < |B0| {
      var head := if FullRow(Comp(B0, G, S, d, w)) then [] else [ERow(d, Comp(B0, G, With(S, g), d, w))];
      KeepConcat(head, KeptMixed(B0, G, S, With(S, g), w, d + 1));
      CompAdd(B0, G, S, g, w, d);
      KeepMixed(B0, G, S, g, w, d + 1);
    }
  }

  lemma PlaceFresh(f: int, n: nat, w: nat, g: Grp)
    requires forall c :: c in g.cells ==> c.d < f
    ensures Place(FreshRows(f, n, w), g) == FreshRows(f, n, w)
  {
    var e := FreshRows(f, n, w);
    forall j | 0 <= j < n
      ensures PlaceRow(e[j], g) == e[j]
    {
      forall x | 0 <= x < w
        ensures PlaceRow(e[j], g).cells[x] == e[j].cells[x]
      {
        if Cell(x, f + j) in g.cells { assert Cell(x, f + j).d < f; }
      }
    }
  }

  lemma KeepFresh(f: int, n: nat, w: nat)
    requires 0 < w
    ensures KeepRows(FreshRows(f, n, w)) == FreshRows(f, n, w)
    decreases n
  {
    if n > 0 {
      var e := FreshRows(f, n, w);
      assert e[0].cells[0] == 0;
      assert e[1..] == FreshRows(f + 1, n - 1, w);
      KeepFresh(f + 1, n - 1, w);
    }
  }

  lemma MaxFresh(f: int, n: nat, w: nat)
    requires f > FRESH_FLOOR
    ensures MaxLabel(FreshRows(f, n, w)) == if n == 0 then FRESH_FLOOR else f + n - 1
    decreases n
  {
    if n > 0 {
      assert FreshRows(f, n, w)[1..] == FreshRows(f + 1, n - 1, w);
      MaxFresh(f + 1, n - 1, w);
    }
  }

  lemma MaxLow(a: seq<ERow>, b: seq<ERow>)
    requires forall j :: 0 <= j < |a| ==> a[j].rid <= FRESH_FLOOR
    ensures MaxLabel(a + b) == MaxLabel(b) || (|b| == 0 && MaxLabel(a + b) == FRESH_FLOOR)
    ensures MaxLabel(b) >= FRESH_FLOOR
    decreases |a|
  {
    if |a| > 0 {
      assert (a + b)[1..] == a[1..] + b;
      MaxLow(a[1..], b);
    } else {
      assert a + b == b;
    }
    MaxGeFloor(b);
  }

  lemma MaxGeFloor(e: seq<ERow>)
    ensures MaxLabel(e) >= FRESH_FLOOR
    decreases |e|
  {
    if |e| > 0 { MaxGeFloor(e[1..]); }
  }

  lemma KeptMixedLabels(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, S2: set<nat>, w: nat, d: nat)
    requires |B0| <= FRESH_FLOOR
    ensures forall j :: 0 <= j < |KeptMixed(B0, G, S, S2, w, d)| ==> d <= KeptMixed(B0, G, S, S2, w, d)[j].rid < |B0|
    decreases |B0| - d
  {
    if d < |B0| { KeptMixedLabels(B0, G, S, S2, w, d + 1); }
  }

  lemma KeptLabels(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, w: nat, d: nat)
    ensures forall j :: 0 <= j < |Kept(B0, G, S, w, d)| ==> d <= Kept(B0, G, S, w, d)[j].rid < |B0|
    ensures forall a, b :: 0 <= a < b < |Kept(B0, G, S, w, d)| ==> Kept(B0, G, S, w, d)[a].rid < Kept(B0, G, S, w, d)[b].rid
    decreases |B0| - d
  {
    if d < |B0| { KeptLabels(B0, G, S, w, d + 1); }
  }

  // THE STEP LEMMA: one lock on the normal form of S is the normal form of With(S, g)
  lemma LockCanon(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, g: nat, w: nat)
    requires T1Hyp(B0, G, w)
    requires g < |G| && g !in S
    ensures LockStep(Canon(B0, G, S, w), G[g], w) == Canon(B0, G, With(S, g), w)
  {
    var R := |B0|;
    var K := Kept(B0, G, S, w, 0);
    var c := R - |K|;
    var F := FreshRows(FRESH_FLOOR + 1, c, w);
    var KM := KeptMixed(B0, G, S, With(S, g), w, 0);
    var K2 := Kept(B0, G, With(S, g), w, 0);
    PlaceConcat(K, F, G[g]);
    PlaceKept(B0, G, S, g, w, 0);
    PlaceFresh(FRESH_FLOOR + 1, c, w, G[g]);
    var P := Place(Canon(B0, G, S, w), G[g]);
    assert P == KM + F;
    KeepConcat(KM, F);
    KeepMixed(B0, G, S, g, w, 0);
    KeepFresh(FRESH_FLOOR + 1, c, w);
    assert KeepRows(P) == K2 + F;
    KeptMixedLabels(B0, G, S, With(S, g), w, 0);
    MaxLow(KM, F);
    MaxFresh(FRESH_FLOOR + 1, c, w);
    assert MaxLabel(P) + 1 == FRESH_FLOOR + 1 + c;
    var n := |P| - |KeepRows(P)|;
    assert FreshRows(FRESH_FLOOR + 1, c, w) + FreshRows(FRESH_FLOOR + 1 + c, n, w) == FreshRows(FRESH_FLOOR + 1, c + n, w);
  }

  lemma KeptHas(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, w: nat, d0: nat, d: nat)
    requires d0 <= d < |B0| && !FullRow(Comp(B0, G, S, d, w))
    ensures exists j :: 0 <= j < |Kept(B0, G, S, w, d0)| && Kept(B0, G, S, w, d0)[j] == ERow(d, Comp(B0, G, S, d, w))
    decreases d - d0
  {
    if d0 < d {
      KeptHas(B0, G, S, w, d0 + 1, d);
      var j :| 0 <= j < |Kept(B0, G, S, w, d0 + 1)| && Kept(B0, G, S, w, d0 + 1)[j] == ERow(d, Comp(B0, G, S, d, w));
      var head := if FullRow(Comp(B0, G, S, d0, w)) then [] else [ERow(d0, Comp(B0, G, S, d0, w))];
      assert Kept(B0, G, S, w, d0)[|head| + j] == ERow(d, Comp(B0, G, S, d, w));
    } else {
      assert Kept(B0, G, S, w, d0)[0] == ERow(d, Comp(B0, G, S, d, w));
    }
  }

  // every row an unplaced group draws on is still on the board, at an empty cell
  lemma CanonPlaceable(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, g: nat, w: nat)
    requires T1Hyp(B0, G, w)
    requires g < |G| && g !in S
    ensures Placeable(Canon(B0, G, S, w), G[g])
  {
    var e := Canon(B0, G, S, w);
    forall c | c in G[g].cells
      ensures exists j :: 0 <= j < |e| && e[j].rid == c.d && 0 <= c.x < |e[j].cells| && e[j].cells[c.x] == 0
    {
      OwnNone(G, S, c, 0);
      assert Comp(B0, G, S, c.d, w)[c.x] == 0;
      KeptHas(B0, G, S, w, 0, c.d);
      var j :| 0 <= j < |Kept(B0, G, S, w, 0)| && Kept(B0, G, S, w, 0)[j] == ERow(c.d, Comp(B0, G, S, c.d, w));
      assert e[j] == Kept(B0, G, S, w, 0)[j];
    }
  }

  // labels are strictly increasing on every reachable state, so Place's "every row labelled d" is
  // route-demos.ts's `rowmap.indexOf(d)`
  lemma CanonLabelsIncreasing(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, w: nat)
    requires |B0| <= FRESH_FLOOR
    ensures forall a, b :: 0 <= a < b < |Canon(B0, G, S, w)| ==> Canon(B0, G, S, w)[a].rid < Canon(B0, G, S, w)[b].rid
  {
    KeptLabels(B0, G, S, w, 0);
  }

  lemma KeptEmpty(B0: seq<seq<int>>, G: seq<Grp>, w: nat, d: nat)
    requires T1Hyp(B0, G, w) && d <= |B0|
    ensures Kept(B0, G, NoGroups(), w, d) == Init(B0)[d..]
    decreases |B0| - d
  {
    if d < |B0| {
      forall x | 0 <= x < w
        ensures Comp(B0, G, NoGroups(), d, w)[x] == B0[d][x]
      {
        OwnNone(G, NoGroups(), Cell(x, d), 0);
      }
      assert Comp(B0, G, NoGroups(), d, w) == B0[d];
      KeptEmpty(B0, G, w, d + 1);
      assert Init(B0)[d..] == [ERow(d, B0[d])] + Init(B0)[d + 1..];
    }
  }

  lemma InitCanon(B0: seq<seq<int>>, G: seq<Grp>, w: nat)
    requires T1Hyp(B0, G, w)
    ensures Init(B0) == Canon(B0, G, NoGroups(), w)
  {
    KeptEmpty(B0, G, w, 0);
  }

  lemma RunFrom(B0: seq<seq<int>>, G: seq<Grp>, S: set<nat>, p: seq<nat>, w: nat)
    requires T1Hyp(B0, G, w)
    requires ValidOrder(G, p)
    requires forall j :: 0 <= j < |p| ==> p[j] !in S
    ensures AllPlaceable(Canon(B0, G, S, w), G, p, w)
    ensures Run(Canon(B0, G, S, w), G, p, w) == Canon(B0, G, S + SetOf(p), w)
    decreases |p|
  {
    if |p| == 0 {
      assert S + SetOf(p) == S;
    } else {
      var g := p[0];
      var e := Canon(B0, G, S, w);
      CanonPlaceable(B0, G, S, g, w);
      LockCanon(B0, G, S, g, w);
      var e2 := LockStep(e, G[g], w);
      assert e2 == Canon(B0, G, With(S, g), w);
      assert ValidOrder(G, p[1..]);
      assert forall j :: 0 <= j < |p[1..]| ==> p[1..][j] !in With(S, g);
      RunFrom(B0, G, With(S, g), p[1..], w);
      assert Run(e, G, p, w) == Run(e2, G, p[1..], w);
      assert AllPlaceable(e, G, p, w) == (Placeable(e, G[g]) && AllPlaceable(e2, G, p[1..], w));
      assert p == [g] + p[1..];
      assert SetOf(p) == {g} + SetOf(p[1..]);
      assert With(S, g) + SetOf(p[1..]) == S + SetOf(p);
    }
  }

  // T1: the process is defined for every valid order, and leaves the normal form of the SET
  lemma RunIsCanon(B0: seq<seq<int>>, G: seq<Grp>, p: seq<nat>, w: nat)
    requires T1Hyp(B0, G, w)
    requires ValidOrder(G, p)
    ensures AllPlaceable(Init(B0), G, p, w)
    ensures Run(Init(B0), G, p, w) == Canon(B0, G, SetOf(p), w)
  {
    InitCanon(B0, G, w);
    var e: set<nat> := {};
    RunFrom(B0, G, e, p, w);
    assert e + SetOf(p) == SetOf(p);
    assert Run(Init(B0), G, p, w) == Run(Canon(B0, G, e, w), G, p, w);
  }

  // T1 as route-orders.ts uses it: two orders of one set leave one engine board and rowmap
  lemma OrderIndependence(B0: seq<seq<int>>, G: seq<Grp>, p: seq<nat>, q: seq<nat>, w: nat)
    requires T1Hyp(B0, G, w)
    requires ValidOrder(G, p) && ValidOrder(G, q)
    requires SetOf(p) == SetOf(q)
    ensures AllPlaceable(Init(B0), G, p, w) && AllPlaceable(Init(B0), G, q, w)
    ensures Run(Init(B0), G, p, w) == Run(Init(B0), G, q, w)
  {
    RunIsCanon(B0, G, p, w);
    RunIsCanon(B0, G, q, w);
  }

  // ── T1 witnesses: the theorem is about a process that really shifts rows ──

  // 2 wide, 3 tall. The parent left one cell at (0, row 0). Group 0 completes row 0, group 1 sits
  // on diagram row 1. Placing group 0 first CLEARS row 0, so diagram row 1 moves down to engine
  // row 0 and a fresh row 1001 enters on top; group 1 must then be written at engine row 0. The
  // other order writes it at engine row 1 and then shifts it. Both end on one board and rowmap.
  lemma T1Witness()
  {
    var B0: seq<seq<int>> := [[1, 0], [0, 0], [0, 0]];
    var G := [Grp({Cell(1, 0)}, 2), Grp({Cell(0, 1)}, 3)];
    var w: nat := 2;
    var want := [ERow(1, [3, 0]), ERow(2, [0, 0]), ERow(1001, [0, 0])];
    var e0 := Init(B0);
    assert e0 == [ERow(0, [1, 0]), ERow(1, [0, 0]), ERow(2, [0, 0])];
    assert !FullRow([1, 0]) by { assert [1, 0][1] == 0; }
    assert !FullRow([0, 0]) by { assert [0, 0][1] == 0; }
    assert !FullRow([3, 0]) by { assert [3, 0][1] == 0; }
    assert FullRow([1, 2]);

    // order 0, 1
    var p01 := Place(e0, G[0]);
    assert p01[0].cells == [1, 2];
    assert p01[1].cells == [0, 0];
    assert p01[2].cells == [0, 0];
    assert p01 == [ERow(0, [1, 2]), ERow(1, [0, 0]), ERow(2, [0, 0])];
    assert p01[1..] == [ERow(1, [0, 0]), ERow(2, [0, 0])];
    assert p01[1..][1..] == [ERow(2, [0, 0])];
    assert p01[1..][1..][1..] == [];
    assert KeepRows(p01[1..][1..]) == [ERow(2, [0, 0])];
    assert KeepRows(p01[1..]) == [ERow(1, [0, 0]), ERow(2, [0, 0])];
    assert KeepRows(p01) == [ERow(1, [0, 0]), ERow(2, [0, 0])];
    assert MaxLabel(p01[1..][1..]) == 1000;
    assert MaxLabel(p01[1..]) == 1000;
    assert MaxLabel(p01) == 1000;
    assert Zeros(2) == [0, 0];
    assert FreshRows(1001, 1, 2) == [ERow(1001, [0, 0])];
    var a1 := LockStep(e0, G[0], w);
    assert a1 == [ERow(1, [0, 0]), ERow(2, [0, 0]), ERow(1001, [0, 0])];   // row 1 shifted DOWN
    var a2p := Place(a1, G[1]);
    assert a2p[0].cells == [3, 0];
    assert a2p[1].cells == [0, 0];
    assert a2p[2].cells == [0, 0];
    assert a2p == want;
    assert want[1..] == [ERow(2, [0, 0]), ERow(1001, [0, 0])];
    assert want[1..][1..] == [ERow(1001, [0, 0])];
    assert KeepRows(want) == want;
    assert MaxLabel(want) == 1001;
    assert LockStep(a1, G[1], w) == want;
    assert [0, 1][1..] == [1];
    assert Run(e0, G, [0, 1], w) == want;

    // order 1, 0
    var p10 := Place(e0, G[1]);
    assert p10[0].cells == [1, 0];
    assert p10[1].cells == [3, 0];
    assert p10[2].cells == [0, 0];
    assert p10 == [ERow(0, [1, 0]), ERow(1, [3, 0]), ERow(2, [0, 0])];
    assert p10[1..] == [ERow(1, [3, 0]), ERow(2, [0, 0])];
    assert p10[1..][1..] == [ERow(2, [0, 0])];
    assert KeepRows(p10) == p10;
    assert MaxLabel(p10) == 1000;
    var b1 := LockStep(e0, G[1], w);
    assert b1 == p10;
    var b2p := Place(b1, G[0]);
    assert b2p[0].cells == [1, 2];
    assert b2p[1].cells == [3, 0];
    assert b2p[2].cells == [0, 0];
    assert b2p == [ERow(0, [1, 2]), ERow(1, [3, 0]), ERow(2, [0, 0])];
    assert b2p[1..] == [ERow(1, [3, 0]), ERow(2, [0, 0])];
    assert b2p[1..][1..] == [ERow(2, [0, 0])];
    assert KeepRows(b2p) == [ERow(1, [3, 0]), ERow(2, [0, 0])];
    assert MaxLabel(b2p) == 1000;
    assert LockStep(b1, G[0], w) == want;
    assert [1, 0][1..] == [0];
    assert Run(e0, G, [1, 0], w) == want;

    // and the instance satisfies every hypothesis of T1, so T1 speaks about it
    assert T1Hyp(B0, G, w);
    assert ValidOrder(G, [0, 1]) && ValidOrder(G, [1, 0]);
    assert SetOf([0, 1]) == SetOf([1, 0]);
    OrderIndependence(B0, G, [0, 1], [1, 0], w);
  }

  // CONTROL: drop cell-disjointness and the order matters — two groups claiming one cell leave
  // whichever colour went in last. The hypothesis is load-bearing, not decoration.
  lemma OverlapControl()
  {
    var B0: seq<seq<int>> := [[0, 0]];
    var G := [Grp({Cell(0, 0)}, 2), Grp({Cell(0, 0)}, 3)];
    var w: nat := 2;
    var e0 := Init(B0);
    assert e0 == [ERow(0, [0, 0])];
    assert !FullRow([2, 0]) by { assert [2, 0][1] == 0; }
    assert !FullRow([3, 0]) by { assert [3, 0][1] == 0; }
    var a := Place(Place(e0, G[0]), G[1]);
    assert Place(e0, G[0])[0].cells == [2, 0];
    assert LockStep(e0, G[0], w) == [ERow(0, [2, 0])];
    assert Place(LockStep(e0, G[0], w), G[1])[0].cells == [3, 0];
    assert LockStep(LockStep(e0, G[0], w), G[1], w) == [ERow(0, [3, 0])];
    assert Place(e0, G[1])[0].cells == [3, 0];
    assert LockStep(e0, G[1], w) == [ERow(0, [3, 0])];
    assert Place(LockStep(e0, G[1], w), G[0])[0].cells == [2, 0];
    assert LockStep(LockStep(e0, G[1], w), G[0], w) == [ERow(0, [2, 0])];
    assert [0, 1][1..] == [1] && [1, 0][1..] == [0];
    assert Run(e0, G, [0, 1], w) != Run(e0, G, [1, 0], w);
    assert !T1Hyp(B0, G, w);
  }
}
