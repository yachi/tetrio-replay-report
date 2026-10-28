/-!
# T1's model: the engine board, its rowmap, the write and the clear

The definitions only, split out of `RouteOrders.T1` so that `RouteOrders.T1Witness` depends on the
MODEL and not on the proof: `lean/mutate.sh` plants each T1 mutant here, and the witnesses must still
build (and fail on their own `decide`) when the proofs in `T1.lean` stop going through. See `T1.lean`
for what each definition mirrors in the engine.
-/

namespace RouteOrders.T1

/-- One engine row: column ↦ occupied. -/
abbrev Row := Nat → Bool

def setCell (r : Row) (x : Nat) : Row := fun y => if y = x then true else r y
def emptyRow : Row := fun _ => false
/-- `linesOf`: a row is full when each of its `W` columns is occupied. -/
def full (W : Nat) (r : Row) : Bool := (List.range W).all r

/-- The engine board (y-up rows) and its rowmap, two separate lists as in the engine. -/
structure Board where
  rows : List Row
  rowmap : List (Option Nat)

/-- Write one diagram cell `(x, d)` at the engine row whose rowmap entry is `d`. -/
def writeCell (b : Board) (c : Nat × Nat) : Board :=
  { rows := List.zipWith (fun r o => if o = some c.2 then setCell r c.1 else r) b.rows b.rowmap,
    rowmap := b.rowmap }

/-- `applyCells`' clear + `advanceRowmap`: the same full-row indices leave both lists, an empty row
    is pushed per cleared row, and the rowmap is refilled with fresh (`none`) entries to its length. -/
def clearRows (W : Nat) (b : Board) : Board :=
  let keep := (List.zip b.rows b.rowmap).filter (fun p => !full W p.1)
  { rows := keep.map Prod.fst ++ List.replicate (b.rows.length - keep.length) emptyRow,
    rowmap := keep.map Prod.snd ++ List.replicate (b.rowmap.length - keep.length) none }

/-- One lock: write every cell of the group, then clear. -/
def place (W : Nat) (b : Board) (g : List (Nat × Nat)) : Board := clearRows W (g.foldl writeCell b)

def placeAll (W : Nat) (b : Board) (gs : List (List (Nat × Nat))) : Board := gs.foldl (place W) b

/-- The board a bag starts on: the parent's rows, rowmap = their diagram ids (`initialRowmap`). -/
def initial (V : List (Nat × Row)) : Board :=
  { rows := V.map Prod.snd, rowmap := V.map (fun p => some p.1) }

end RouteOrders.T1
