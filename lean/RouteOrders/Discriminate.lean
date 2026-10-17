import RouteOrders.HoldMutants
import RouteOrders.Generated.SdpcspinData

/-!
# T3's discrimination check: does the committed data tell each T2/T4 mutant apart?

Computed by `HoldMutants.accM` over every node of the artefact (`native_decide`, so these trust the
compiler exactly as the T3 counts do). `lake exe measure` prints the per-node table.
-/

namespace RouteOrders.Discriminate
open RouteOrders.NodeData RouteOrders.Generated RouteOrders.HoldMutants

/-- Control: `accM` with every rule on reproduces every published count, both modes. -/
theorem control_reproduces :
    nodes.all (fun n => countMutEmpty {} n == n.artEmpty && countMutNext {} n == n.artNext) = true := by
  native_decide

/-- Dropping case (c) changes a published count. -/
theorem noHoldFirst_discriminated :
    nodes.any (fun n => countMutEmpty {noHoldFirst := true} n != n.artEmpty
                     || countMutNext {noHoldFirst := true} n != n.artNext) = true := by
  native_decide

/-- …and makes T4 false on the data: the empty-hold count and the next-held count come apart. -/
theorem noHoldFirst_breaks_T4 :
    nodes.any (fun n => countMutEmpty {noHoldFirst := true} n != countMutNext {noHoldFirst := true} n)
      = true := by
  native_decide

/-- A hold move without a placement changes a published count. -/
theorem holdOnly_discriminated :
    nodes.any (fun n => countMutEmpty {holdOnly := true} n != n.artEmpty
                     || countMutNext {holdOnly := true} n != n.artNext) = true := by
  native_decide

/-- Placing `*` (as any group) is EQUIVALENT on this data, and this theorem pins that measurement so
    a future artefact on which it discriminates fails the build instead of passing silently. The
    reason is a count, not luck: `*` is the 8th token, so it can only be reached after all 7 dealt
    tokens, of which at most one is unplaced (the hold has one slot and nothing else discards a
    piece). A node with fewer than 7 groups is full before that; a node with 7 has 6 placed and the
    7th piece in the hold, where move (b) places it with the same result. Only a carried group (none
    in this artefact) could change that. -/
theorem starWild_equivalent_on_data :
    nodes.all (fun n => countMutEmpty {starWild := true} n == n.artEmpty
                     && countMutNext {starWild := true} n == n.artNext) = true := by
  native_decide


/-! ## Axioms gate: these TRUST THE COMPILER — each carries its own `native_decide` axiom, and
nothing else beyond Lean's three standard axioms (no proof-hole axiom). -/

/-- info: 'RouteOrders.Discriminate.control_reproduces' depends on axioms: [propext,
 Classical.choice,
 Quot.sound,
 control_reproduces._native.native_decide.ax_1_1] -/
#guard_msgs in
#print axioms RouteOrders.Discriminate.control_reproduces

/-- info: 'RouteOrders.Discriminate.noHoldFirst_discriminated' depends on axioms: [propext,
 Classical.choice,
 Quot.sound,
 noHoldFirst_discriminated._native.native_decide.ax_1_1] -/
#guard_msgs in
#print axioms RouteOrders.Discriminate.noHoldFirst_discriminated

/-- info: 'RouteOrders.Discriminate.noHoldFirst_breaks_T4' depends on axioms: [propext,
 Classical.choice,
 Quot.sound,
 noHoldFirst_breaks_T4._native.native_decide.ax_1_1] -/
#guard_msgs in
#print axioms RouteOrders.Discriminate.noHoldFirst_breaks_T4

/-- info: 'RouteOrders.Discriminate.holdOnly_discriminated' depends on axioms: [propext,
 Classical.choice,
 Quot.sound,
 holdOnly_discriminated._native.native_decide.ax_1_1] -/
#guard_msgs in
#print axioms RouteOrders.Discriminate.holdOnly_discriminated

/-- info: 'RouteOrders.Discriminate.starWild_equivalent_on_data' depends on axioms: [propext,
 Classical.choice,
 Quot.sound,
 starWild_equivalent_on_data._native.native_decide.ax_1_1] -/
#guard_msgs in
#print axioms RouteOrders.Discriminate.starWild_equivalent_on_data

end RouteOrders.Discriminate
