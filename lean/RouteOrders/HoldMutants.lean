import RouteOrders.NodeData

/-!
# The T2/T4 mutants as PROCEDURES, for T3's discrimination check

`mutate.sh` plants each mutant into the SPECIFICATION (`Hold.Step`) and requires the build to fail.
That shows a proof depends on the rule; it does not show the committed data can tell the rule apart.
This module answers the second question: `accM` is `Hold.acc` with one rule changed per flag, and
`RouteOrders.Discriminate` counts every node under each flag against the artefact.

* `noHoldFirst` — case (c) dropped: an empty hold cannot take the current piece.
* `starWild` — `*` may be placed, as any group the DAG allows (it is the unknown next-bag piece).
  The same rule as the TS mutant `placeStar` and Dafny's `placeStar`; all three measure it equivalent
  on the committed data.
* `holdOnly` — a hold move without a placement: the current piece enters the hold (discarding any
  held piece) and nothing is placed.
-/

namespace RouteOrders.HoldMutants
open RouteOrders.Hold RouteOrders.NodeData

structure Mut where
  noHoldFirst : Bool := false
  starWild : Bool := false
  holdOnly : Bool := false

def accM (m : Mut) (D : Dag) : Nat → List Tok → Option Tok → Bool
  | s, [], _ => s == D.full
  | s, t :: r, h =>
    (s == D.full)
    || (match place D s t with
        | some s' => accM m D s' r h
        | none => false)
    || (m.starWild && t == .star &&
        (List.range 7).any (fun g => D.can s g && accM m D (s ||| bit g) r h))
    || (match h with
        | some th => (match place D s th with
            | some s' => accM m D s' r (some t)
            | none => false)
        | none => false)
    || (!m.noHoldFirst && match h, r with
        | none, t' :: r' => (t != .star) && (match place D s t' with
            | some s' => accM m D s' r' (some t)
            | none => false)
        | _, _ => false)
    || (m.holdOnly && t != .star && accM m D s r (some t))

def countMutEmpty (m : Mut) (n : Node) : Nat :=
  (allOrders.filter (fun q => n.fullOk && accM m (dagOf n) 0 (streamOf q) none)).length

def countMutNext (m : Mut) (n : Node) : Nat :=
  (allOrders.filter (fun q => match q with
    | c :: q' => n.fullOk && accM m (dagOf n) 0 (streamOf q') (some (.piece c))
    | [] => false)).length

end RouteOrders.HoldMutants
