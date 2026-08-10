// BfsKey.dfy — the visited-set key of `bestTspin`'s BFS (pipeline/sim/forecast.ts:97), as a
// statement about SEARCH, not about Tetris.
//
// =================================== SCOPE — READ THIS FIRST ===================================
//
// This file proves properties of a GRAPH SEARCH ALGORITHM over an abstract state space. It does
// NOT prove anything about Tetris, TETR.IO, SRS kicks, `detectTSpin`, board geometry, or the
// forecast metric — and nothing here makes the forecast metric "Dafny-verified". The forecast
// section is quarantined (one simulator, no second independent implementation, no claim ids, no
// ✓ badges) and this file does not change that. Per the repo's central invariant: Dafny proves
// "claim ⇔ model", never the extraction — here the model is the search, and the bridge from
// `forecast.ts`'s concrete loop to this model is an argument in comments, not a proof.
//
// THE FINDING. forecast.ts keys its visited set on the position triple (rotation, col, row)
// alone (`seenOrMark`, :91-117, dedup at :147), but the T-spin test at :123 also reads `rot` and
// `kick` — HOW the state was entered. If a shift or soft drop reaches a position first, a later
// arrival at the same position by (kicked) rotation is discarded, and a genuine T-spin there is
// never tested. Cold Clear 2 keys on `Placement`, which includes spin, and does not lose it.
//
// WHAT IS PROVED (of the abstract search):
//   1. PositionKeyedNeverFindsMore — for EVERY exploration order, the pair set a position-keyed
//      search discovers is a subset of what the arrival-keyed search discovers.
//   2. MetricMonotone — hence for ANY nat-valued valuation of (state, arrival) pairs (read: the
//      lines a detected T-spin would clear), the position-keyed maximum is <= the arrival-keyed
//      maximum. The fix can only raise the reported availability, never lower it. This is the
//      theorem behind the measurement "191 of 8,995 boards gain, 0 lose".
//   3. TheFixIsNotVacuous — a concrete graph in the foreacast_022 shape (one position reachable
//      both by a shift and by a kicked rotation, the valuation firing only on the rotation
//      arrival) where the inequality is STRICT under the shift-first order, plus two valid
//      position-keyed runs of the SAME graph discovering DIFFERENT pair sets (order-dependence
//      made concrete). Mandatory: this repo has shipped tautological lemmas before.
//   4. ArrivalKeyedQueueBound / ConcreteQueueCap — the arrival-keyed queue holds at most
//      3 * |states| entries (Arrival has exactly 3 values: ByMove, ByRotate(false),
//      ByRotate(true)), so under the code comment's OWN side condition (rows in [-2, 39], hence
//      at most 4*10*42 = 1680 states) the new cap is 5040, still under the h < 40000 belt.
//   Plus ArrivalKeyedIsOrderIndependent: arrival-keyed discovery is the reachable pair set, the
//   same for every exploration order — the property position keying lacks.
//
// WHAT IS NOT PROVED:
//   - that forecast.ts's loop refines ValidPositionKeyedRun, or that the patched copy refines
//     ValidArrivalKeyedRun. That bridge is by inspection: successors depend on the state alone
//     (`tryMove`/`tryRotate` read cur's position, never its history), every dequeued node was
//     enqueued via a real edge, and a completed (uncapped) search is successor-closed.
//   - the side condition |states| <= 1680. Rows are NOT engine-bounded (srs.ts:129 skips row < 0
//     instead of rejecting it); 1680 is forecast.ts:159-179's CONDITIONAL bound and stays an
//     assumption here, taken as a `requires`. The measured max is 688 states over 2000 boards.
//   - anything about which valuation the real test computes: `P` is universally quantified.
//
// MODEL FIDELITY. A "run" here is the sequence of nodes in discovery order, constrained only by
// (a) it starts at the spawn node, (b) every later node was discovered along a real edge from an
// earlier node, (c) the dedup discipline (states for position keying, pairs for arrival keying),
// (d) successor closure (the search ran to completion — the h-cap is what lemma 4 is about).
// This is deliberately MORE permissive than FIFO order: the theorems quantify over every
// exploration order, so they cover the real BFS as one instance.
//
// dafny verify spec/BfsKey.dfy      — Dafny 4.11.0; output gated by .github/workflows/verify.yml
// bash spec/mutate-bfskey.sh        — every planted mutant must die
// ================================================================================================

module BfsKey {

  // -----------------------------------------------------------------------------------------
  // How a state was ENTERED. forecast.ts:119-148 carries exactly this beside each queued
  // placement: `rot` (the producing edge was a rotation) and `kick` (that rotation displaced
  // the piece). ByMove covers shifts and soft drops; the spawn node is ByMove (:119 seeds
  // rot=false, kick=false). Three values, and lemma 4's constant 3 is THIS datatype's size.
  // -----------------------------------------------------------------------------------------
  datatype Arrival = ByMove | ByRotate(kick: bool)

  // A discovered node: a state plus the arrival it was discovered with. `S` abstracts the
  // (rotation, col, row) triple; nothing below depends on what a state is.
  datatype SNode<S> = SNode(s: S, a: Arrival)

  // The successor relation. G(s) is every (state, arrival) edge out of s — the up-to-five
  // moves at forecast.ts:142-144, each tagged with how it enters its target. Successors depend
  // on the STATE alone, exactly as in the code: `tryMove`/`tryRotate` read cur's position and
  // the (fixed) board, never how cur was reached. That assumption is load-bearing and true.
  type Graph<!S(==)> = S -> set<SNode<S>>

  // The pair set a run discovered.
  ghost function NodesOf<S>(run: seq<SNode<S>>): set<SNode<S>> {
    set i | 0 <= i < |run| :: run[i]
  }

  // -----------------------------------------------------------------------------------------
  // Runs. Shared skeleton: starts at the spawn node, and every later node entered the run
  // along a REAL edge from an earlier node — which is all any worklist algorithm guarantees,
  // whatever its order. This clause alone gives soundness.
  // -----------------------------------------------------------------------------------------
  // The run predicates are `opaque` for a measured reason, not style: their closure clauses
  // and the NodesOf comprehension feed each other's quantifier triggers, and a lemma that
  // carries them in context WITHOUT needing their bodies — MetricMonotone — hands Z3 a
  // matching loop. Measured 2026-08-10 on the mutant that strengthens MetricMonotone's
  // ensures to `<`: with these transparent it runs >300 s (UNRESOLVED under the mutation
  // harness's timeout rule, which is not a kill); opaque, it dies in 3 s, and the baseline is
  // unchanged at ~2 s. Every lemma that DOES unfold one says so with a `reveal`.
  ghost opaque predicate ParentLinked<S>(G: Graph<S>, start: S, run: seq<SNode<S>>) {
    && |run| > 0
    && run[0] == SNode(start, ByMove)
    && forall i :: 1 <= i < |run| ==> exists j :: 0 <= j < i && run[i] in G(run[j].s)
  }

  // The SHIPPED discipline: dedup on the state alone. A state appears once, with whichever
  // arrival won the race — that race is the exploration order, which is why this run's node
  // set is order-DEPENDENT. Closure is on STATES: a successor state already seen is skipped,
  // however it was re-entered (forecast.ts:147).
  //
  // Stated honestly: the dedup and closure clauses here are MODEL FIDELITY, not load-bearing —
  // every theorem about this run needs only ParentLinked (soundness quantifies over MORE runs
  // without them, so dropping them would make theorems 1-2 strictly stronger). A weakening
  // mutant on either clause therefore survives BY CONSTRUCTION and none is planted; what the
  // mutation harness does pin is that the predicate as written is satisfiable (the witness
  // builds two of these runs) and that the theorems die when their own clauses are touched.
  ghost opaque predicate ValidPositionKeyedRun<S>(G: Graph<S>, start: S, run: seq<SNode<S>>) {
    && ParentLinked(G, start, run)
    && (forall i, j :: 0 <= i < j < |run| ==> run[i].s != run[j].s)
    && (forall i, n :: 0 <= i < |run| && n in G(run[i].s) ==>
          exists j :: 0 <= j < |run| && run[j].s == n.s)
  }

  // The FIX: dedup on the (state, arrival) PAIR, so a position reached first by a shift is
  // still explored later by rotation. Closure is on PAIRS — every edge out of a discovered
  // state is discovered. This is what makes the node set order-independent (proved below).
  ghost opaque predicate ValidArrivalKeyedRun<S>(G: Graph<S>, start: S, run: seq<SNode<S>>) {
    && ParentLinked(G, start, run)
    && (forall i, j :: 0 <= i < j < |run| ==> run[i] != run[j])
    && (forall i, n :: 0 <= i < |run| && n in G(run[i].s) ==> n in NodesOf(run))
  }

  // -----------------------------------------------------------------------------------------
  // Ground truth: reachability along real edge paths, independent of any algorithm.
  // -----------------------------------------------------------------------------------------
  ghost predicate IsPath<S>(G: Graph<S>, start: S, p: seq<SNode<S>>) {
    && |p| > 0
    && p[0] == SNode(start, ByMove)
    && forall i :: 1 <= i < |p| ==> p[i] in G(p[i-1].s)
  }

  ghost predicate Reaches<S(!new)>(G: Graph<S>, start: S, n: SNode<S>) {
    exists p: seq<SNode<S>> :: IsPath(G, start, p) && p[|p|-1] == n
  }

  // SOUNDNESS of any parent-linked run: everything discovered is genuinely reachable. Holds
  // for BOTH disciplines — a search only follows real edges, whatever it dedups on.
  lemma RunNodeIsReachable<S(!new)>(G: Graph<S>, start: S, run: seq<SNode<S>>, i: int)
    requires ParentLinked(G, start, run)
    requires 0 <= i < |run|
    ensures Reaches(G, start, run[i])
    decreases i
  {
    reveal ParentLinked();
    if i == 0 {
      assert IsPath(G, start, [run[0]]);
    } else {
      var j :| 0 <= j < i && run[i] in G(run[j].s);
      RunNodeIsReachable(G, start, run, j);
      var p :| IsPath(G, start, p) && p[|p|-1] == run[j];
      var q := p + [run[i]];
      assert q[|q|-2] == p[|p|-1];
      assert forall t {:trigger q[t]} :: 0 <= t < |p| ==> q[t] == p[t];
      assert IsPath(G, start, q);
    }
  }

  // COMPLETENESS of the arrival-keyed run at the PAIR level: everything reachable is
  // discovered. Induction on the path; the step is exactly the pair-closure clause. This is
  // the direction the shipped key LACKS — under state closure, the induction dies at the
  // final edge, because the state being present says nothing about which arrival it is
  // present with.
  lemma ReachableIsInArrivalRun<S(!new)>(
      G: Graph<S>, start: S, run: seq<SNode<S>>, n: SNode<S>, p: seq<SNode<S>>)
    requires ValidArrivalKeyedRun(G, start, run)
    requires IsPath(G, start, p) && p[|p|-1] == n
    ensures n in NodesOf(run)
    decreases |p|
  {
    reveal ValidArrivalKeyedRun(), ParentLinked();
    if |p| == 1 {
      assert n == run[0];
      assert run[0] in NodesOf(run);
    } else {
      var pre := p[..|p|-1];
      assert forall t {:trigger pre[t]} :: 0 <= t < |pre| ==> pre[t] == p[t];
      assert IsPath(G, start, pre);
      ReachableIsInArrivalRun(G, start, run, p[|p|-2], pre);
      var j :| 0 <= j < |run| && run[j] == p[|p|-2];
      assert n in G(run[j].s);
    }
  }

  // COMPLETENESS of the position-keyed run at the STATE level: every reachable state appears,
  // under SOME arrival. The induction step is where "successors depend only on the state"
  // does its work — the path's predecessor may sit in the run with a DIFFERENT arrival than
  // the path used, but Graph's very type (S -> set) makes G(run[j].s) the same set, so the
  // edge is still available. In forecast.ts terms: `tryMove`/`tryRotate` read the position,
  // never how it was reached, so the shipped search misses PAIRS, never POSITIONS. This is
  // what makes both the states-agree lemma and the unconditional 3x bound true.
  lemma ReachableStateIsInPositionRun<S(!new)>(
      G: Graph<S>, start: S, run: seq<SNode<S>>, n: SNode<S>, p: seq<SNode<S>>)
    requires ValidPositionKeyedRun(G, start, run)
    requires IsPath(G, start, p) && p[|p|-1] == n
    ensures exists j :: 0 <= j < |run| && run[j].s == n.s
    decreases |p|
  {
    reveal ValidPositionKeyedRun(), ParentLinked();
    if |p| == 1 {
      assert run[0].s == n.s;
    } else {
      var pre := p[..|p|-1];
      assert forall t {:trigger pre[t]} :: 0 <= t < |pre| ==> pre[t] == p[t];
      assert IsPath(G, start, pre);
      ReachableStateIsInPositionRun(G, start, run, p[|p|-2], pre);
      var j :| 0 <= j < |run| && run[j].s == p[|p|-2].s;
      assert n in G(run[j].s);
    }
  }

  // ===========================================================================================
  // THEOREM 1 — soundness / superset. For EVERY exploration order of both searches, the
  // position-keyed search discovers a subset of the arrival-keyed pairs. The fix loses nothing.
  // ===========================================================================================
  lemma PositionKeyedNeverFindsMore<S(!new)>(
      G: Graph<S>, start: S, posRun: seq<SNode<S>>, arrRun: seq<SNode<S>>)
    requires ValidPositionKeyedRun(G, start, posRun)
    requires ValidArrivalKeyedRun(G, start, arrRun)
    ensures NodesOf(posRun) <= NodesOf(arrRun)
  {
    reveal ValidPositionKeyedRun();
    forall n | n in NodesOf(posRun) ensures n in NodesOf(arrRun) {
      var i :| 0 <= i < |posRun| && posRun[i] == n;
      RunNodeIsReachable(G, start, posRun, i);
      var p :| IsPath(G, start, p) && p[|p|-1] == n;
      ReachableIsInArrivalRun(G, start, arrRun, n, p);
    }
  }

  // The arrival-keyed set is exactly reachability, hence the SAME for every exploration order.
  // Position keying has no such lemma, and TheFixIsNotVacuous exhibits two of its runs that
  // really do disagree.
  lemma ArrivalKeyedIsOrderIndependent<S(!new)>(
      G: Graph<S>, start: S, run1: seq<SNode<S>>, run2: seq<SNode<S>>)
    requires ValidArrivalKeyedRun(G, start, run1)
    requires ValidArrivalKeyedRun(G, start, run2)
    ensures NodesOf(run1) == NodesOf(run2)
  {
    reveal ValidArrivalKeyedRun();
    forall n | n in NodesOf(run1) ensures n in NodesOf(run2) {
      var i :| 0 <= i < |run1| && run1[i] == n;
      RunNodeIsReachable(G, start, run1, i);
      var p :| IsPath(G, start, p) && p[|p|-1] == n;
      ReachableIsInArrivalRun(G, start, run2, n, p);
    }
    forall n | n in NodesOf(run2) ensures n in NodesOf(run1) {
      var i :| 0 <= i < |run2| && run2[i] == n;
      RunNodeIsReachable(G, start, run2, i);
      var p :| IsPath(G, start, p) && p[|p|-1] == n;
      ReachableIsInArrivalRun(G, start, run1, n, p);
    }
  }

  // ===========================================================================================
  // THEOREM 2 — monotonicity of any maximised metric. `P` abstracts "lines this detection
  // would clear" (forecast.ts:123-140 keeps a running best over discovered nodes); the theorem
  // holds for EVERY nat-valued P, so it does not depend on what the T-spin test computes.
  // This turns the measurement "0 of 8,995 boards lose availability" into: none CAN.
  // ===========================================================================================
  // Consumers reason from the three ensures alone; the body exists to prove them.
  ghost function MaxOver<S>(ns: set<SNode<S>>, P: SNode<S> -> nat): nat
    ensures forall n :: n in ns ==> P(n) <= MaxOver(ns, P)
    ensures ns != {} ==> exists n :: n in ns && P(n) == MaxOver(ns, P)
    ensures ns == {} ==> MaxOver(ns, P) == 0
    decreases ns
  {
    if ns == {} then 0
    else
      var m :| m in ns;
      var rest := MaxOver(ns - {m}, P);
      if P(m) >= rest then P(m) else rest
  }

  lemma MaxOverMonotone<S>(a: set<SNode<S>>, b: set<SNode<S>>, P: SNode<S> -> nat)
    requires a <= b
    ensures MaxOver(a, P) <= MaxOver(b, P)
  {
    if a != {} {
      var n :| n in a && P(n) == MaxOver(a, P);
    }
  }

  lemma MetricMonotone<S(!new)>(
      G: Graph<S>, start: S, posRun: seq<SNode<S>>, arrRun: seq<SNode<S>>, P: SNode<S> -> nat)
    requires ValidPositionKeyedRun(G, start, posRun)
    requires ValidArrivalKeyedRun(G, start, arrRun)
    ensures MaxOver(NodesOf(posRun), P) <= MaxOver(NodesOf(arrRun), P)
  {
    PositionKeyedNeverFindsMore(G, start, posRun, arrRun);
    MaxOverMonotone(NodesOf(posRun), NodesOf(arrRun), P);
  }

  // ===========================================================================================
  // THEOREM 3 — non-vacuity. The smallest graph in the foreacast_022 shape: state 1 reachable
  // from the spawn BOTH by a shift (ByMove) AND by a kicked rotation (ByRotate(true)), and the
  // valuation fires only on the rotation arrival — detectTSpin at :123 requires `rot`. Under
  // the shift-first order the position-keyed search records state 1 as ByMove, discards the
  // rotation re-entry, and reports 0; the arrival-keyed search keeps both and reports 1.
  // STRICT inequality, so Theorem 2 is not a tautology. And the rotation-first order yields a
  // second valid position-keyed run with a DIFFERENT pair set: the shipped key's answer
  // depends on the race, which is the order-dependence claim made concrete.
  // ===========================================================================================
  lemma TheFixIsNotVacuous()
  {
    reveal ValidPositionKeyedRun(), ValidArrivalKeyedRun(), ParentLinked();
    var none: set<SNode<int>> := {};
    var G: Graph<int> :=
      (s: int) => if s == 0 then {SNode(1, ByMove), SNode(1, ByRotate(true))} else none;
    var start := 0;

    // the shift wins the race: state 1 is marked visited as ByMove, the rotation is discarded
    var posRun := [SNode(0, ByMove), SNode(1, ByMove)];
    // the rotation wins the race instead: same graph, same discipline, different pair set
    var posRunB := [SNode(0, ByMove), SNode(1, ByRotate(true))];
    // the fix: both arrivals at state 1 are explored
    var arrRun := [SNode(0, ByMove), SNode(1, ByMove), SNode(1, ByRotate(true))];

    assert posRun[1] in G(posRun[0].s);
    assert posRunB[1] in G(posRunB[0].s);
    assert arrRun[1] in G(arrRun[0].s) && arrRun[2] in G(arrRun[0].s);
    assert forall n <- G(1) :: false;
    assert arrRun[1] in NodesOf(arrRun) && arrRun[2] in NodesOf(arrRun);
    assert posRun[1] in NodesOf(posRun) && posRunB[1] in NodesOf(posRunB);
    assert ValidPositionKeyedRun(G, start, posRun);
    assert ValidPositionKeyedRun(G, start, posRunB);
    assert ValidArrivalKeyedRun(G, start, arrRun);

    // the valuation: only the kicked-rotation arrival at state 1 is a detected T-spin
    var P: SNode<int> -> nat := n => if n == SNode(1, ByRotate(true)) then 1 else 0;

    // the arrival-keyed search finds it...
    assert SNode(1, ByRotate(true)) == arrRun[2];
    assert SNode(1, ByRotate(true)) in NodesOf(arrRun);
    assert P(SNode(1, ByRotate(true))) == 1;
    var mArr := MaxOver(NodesOf(arrRun), P);
    assert mArr >= 1;
    assert forall n: SNode<int> :: P(n) <= 1;
    assert mArr == 1;

    // ...and under the shift-first order the position-keyed search reports NOTHING
    assert NodesOf(posRun) == {SNode(0, ByMove), SNode(1, ByMove)};
    var mPos := MaxOver(NodesOf(posRun), P);
    var w :| w in NodesOf(posRun) && P(w) == mPos;
    assert mPos == 0;

    // strictly less: the subset inequality of Theorem 2 is not always an equality
    assert mPos < mArr;

    // order-dependence: two valid position-keyed runs of the SAME graph, different pair sets
    assert SNode(1, ByRotate(true)) in NodesOf(posRunB);
    assert SNode(1, ByRotate(true)) !in NodesOf(posRun);
    assert NodesOf(posRun) != NodesOf(posRunB);
  }

  // ===========================================================================================
  // THEOREM 4 — the new queue bound. Every enqueue is a fresh KEY; the shipped key space is
  // |states|, the fixed key space is |states| * |Arrival|, and Arrival has exactly 3 values.
  // So the queue-length bound the code comment derives (forecast.ts:159-179) must be re-derived
  // under the new key: it TRIPLES. Under that comment's own side condition — rows in [-2, 39],
  // hence at most 4*10*42 = 1680 states — the arrival-keyed queue holds at most 5040 entries.
  // 5040 < 40000, so the h-cap belt still holds slack; but the comment's "1680" arithmetic is
  // WRONG for the new key and must say 5040. (The side condition itself is an assumption — see
  // the header — which is why it appears below as a `requires`, not as a proved fact.)
  // ===========================================================================================
  ghost function AllArrivals(): set<Arrival> { {ByMove, ByRotate(false), ByRotate(true)} }

  lemma ArrivalHasThreeValues(a: Arrival)
    ensures a in AllArrivals()
    ensures |AllArrivals()| == 3
  {
  }

  ghost function NodesOver<S>(SS: set<S>): set<SNode<S>> {
    set s, a | s in SS && a in AllArrivals() :: SNode(s, a)
  }

  lemma NodesOverCard<S>(SS: set<S>)
    ensures |NodesOver(SS)| == 3 * |SS|
    decreases SS
  {
    if SS == {} {
      assert NodesOver(SS) == {};
    } else {
      var x :| x in SS;
      var rest := SS - {x};
      NodesOverCard(rest);
      var trio := {SNode(x, ByMove), SNode(x, ByRotate(false)), SNode(x, ByRotate(true))};
      assert NodesOver(SS) == NodesOver(rest) + trio;
      assert NodesOver(rest) !! trio;
      assert |trio| == 3;
    }
  }

  lemma SubsetCard<T>(a: set<T>, b: set<T>)
    requires a <= b
    ensures |a| <= |b|
    decreases a
  {
    if a != {} {
      var x :| x in a;
      SubsetCard(a - {x}, b - {x});
    }
  }

  lemma DistinctSeqCard<S>(run: seq<SNode<S>>)
    requires forall i, j :: 0 <= i < j < |run| ==> run[i] != run[j]
    ensures |NodesOf(run)| == |run|
  {
    if |run| > 0 {
      var pre := run[..|run|-1];
      DistinctSeqCard(pre);
      assert run[|run|-1] !in NodesOf(pre);
      assert NodesOf(run) == NodesOf(pre) + {run[|run|-1]};
    }
  }

  // Every queue entry is a distinct (state, arrival) pair, so the queue — hence the loop index
  // h — is bounded by 3 * |states that occur|.
  lemma ArrivalKeyedQueueBound<S>(G: Graph<S>, start: S, run: seq<SNode<S>>, SS: set<S>)
    requires ValidArrivalKeyedRun(G, start, run)
    requires forall i :: 0 <= i < |run| ==> run[i].s in SS
    ensures |run| <= 3 * |SS|
  {
    reveal ValidArrivalKeyedRun();
    DistinctSeqCard(run);
    forall n | n in NodesOf(run) ensures n in NodesOver(SS) {
      ArrivalHasThreeValues(n.a);
      var i :| 0 <= i < |run| && run[i] == n;
    }
    SubsetCard(NodesOf(run), NodesOver(SS));
    NodesOverCard(SS);
  }

  // The concrete number, derived THROUGH the theorem rather than asserted: if the states stay
  // within the code comment's conditional 1680, the arrival-keyed queue stays within 5040.
  lemma ConcreteQueueCap<S>(G: Graph<S>, start: S, run: seq<SNode<S>>, SS: set<S>)
    requires ValidArrivalKeyedRun(G, start, run)
    requires forall i :: 0 <= i < |run| ==> run[i].s in SS
    requires |SS| <= 1680       // forecast.ts's conditional 4*10*42 — an ASSUMPTION, see header
    ensures |run| <= 5040       // 3 * 1680; the h < 40000 belt keeps 7.9x slack
  {
    ArrivalKeyedQueueBound(G, start, run, SS);
  }
}
