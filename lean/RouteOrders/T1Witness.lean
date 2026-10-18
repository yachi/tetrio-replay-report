import RouteOrders.T1Defs

/-!
# T1's mutants are ORDER-DEPENDENT, on concrete boards (kernel `decide`, no native code)

`mutate.sh` plants each mutant into `T1Defs.clearRows` and counts it killed only when the matching
`*_real` theorem below is refuted by its own `decide` (this module imports only `T1Defs`, so it still
builds when the mutant breaks the proofs in `T1.lean`). These witnesses show the rule is what makes
the theorem TRUE: under each mutant clear, two orders of the same two groups leave different boards,
and under the real clear the same two orders agree (the control). Both witnesses were found by the brute-force probe
`scratchpad/route-orders/lean/t1probe.py`; that probe also measured a third reading of "clear a row
that is not full" — clear every row with ≥ W-1 cells — as order-INDEPENDENT on 117 164 small cases,
which is what the proof predicts: any clear rule that is a function of the row's own content keeps
T1 true, so only a rule that looks at a different row than the one it removes can break it.
-/

namespace RouteOrders.T1.Witness
open RouteOrders.T1

/-- A board as data (rows read over the width), so equality is decidable. -/
def view (W : Nat) (b : Board) : List (List Bool) × List (Option Nat) :=
  (b.rows.map (fun r => (List.range W).map r), b.rowmap)

def placeWith (clr : Board → Board) (b : Board) (g : List (Nat × Nat)) : Board :=
  clr (g.foldl writeCell b)

def placeAllWith (clr : Board → Board) (b : Board) (gs : List (List (Nat × Nat))) : Board :=
  gs.foldl (placeWith clr) b

/-- The witnesses run the model's own `placeAll` when given the model's own clear. -/
theorem placeAllWith_real (W : Nat) : placeAllWith (clearRows W) = placeAll W := rfl

/-- Mutant 1, CLEAR WITHOUT COMPACTION: full rows are emptied where they stand, while the rowmap
    still advances as `advanceRowmap` does — the board and its rowmap fall out of step. -/
def clearInPlace (W : Nat) (b : Board) : Board :=
  { rows := b.rows.map (fun r => if full W r then emptyRow else r),
    rowmap := (clearRows W b).rowmap }

/-- Mutant 2, CLEAR A ROW THAT IS NOT FULL: the row ABOVE each full row is removed (an off-by-one
    in the cleared index), from both lists alike; the full row itself stays. -/
def clearAbove (W : Nat) (b : Board) : Board :=
  let flags := false :: b.rows.map (full W)
  let keep := ((List.zip b.rows b.rowmap).zip flags).filter (fun q => !q.2) |>.map Prod.fst
  { rows := keep.map Prod.fst ++ List.replicate (b.rows.length - keep.length) emptyRow,
    rowmap := keep.map Prod.snd ++ List.replicate (b.rowmap.length - keep.length) none }

-- witness 1: W = 2, two rows each holding one cell; groups [(0,1)] and [(1,0)]
def w1 : Board := initial [(0, fun x => x == 0), (1, fun x => x == 1)]
def w1a : List (List (Nat × Nat)) := [[(0, 1)], [(1, 0)]]
def w1b : List (List (Nat × Nat)) := [[(1, 0)], [(0, 1)]]

theorem w1_real : view 2 (placeAll 2 w1 w1a) = view 2 (placeAll 2 w1 w1b) := by decide
theorem w1_inPlace_order_dependent :
    view 2 (placeAllWith (clearInPlace 2) w1 w1a) ≠ view 2 (placeAllWith (clearInPlace 2) w1 w1b) := by
  decide

-- witness 2: W = 1, three empty rows; groups [(0,2)] and [(0,0)]
def w2 : Board := initial [(0, emptyRow), (1, emptyRow), (2, emptyRow)]
def w2a : List (List (Nat × Nat)) := [[(0, 2)], [(0, 0)]]
def w2b : List (List (Nat × Nat)) := [[(0, 0)], [(0, 2)]]

theorem w2_real : view 1 (placeAll 1 w2 w2a) = view 1 (placeAll 1 w2 w2b) := by decide
theorem w2_above_order_dependent :
    view 1 (placeAllWith (clearAbove 1) w2 w2a) ≠ view 1 (placeAllWith (clearAbove 1) w2 w2b) := by
  decide


/-! ## Axioms gate: no proof-hole axiom, no native-code axiom; only Lean's three standard axioms. -/

/-- info: 'RouteOrders.T1.Witness.w1_real' does not depend on any axioms -/
#guard_msgs in
#print axioms RouteOrders.T1.Witness.w1_real

/-- info: 'RouteOrders.T1.Witness.w1_inPlace_order_dependent' does not depend on any axioms -/
#guard_msgs in
#print axioms RouteOrders.T1.Witness.w1_inPlace_order_dependent

/-- info: 'RouteOrders.T1.Witness.w2_real' does not depend on any axioms -/
#guard_msgs in
#print axioms RouteOrders.T1.Witness.w2_real

/-- info: 'RouteOrders.T1.Witness.w2_above_order_dependent' does not depend on any axioms -/
#guard_msgs in
#print axioms RouteOrders.T1.Witness.w2_above_order_dependent

end RouteOrders.T1.Witness
