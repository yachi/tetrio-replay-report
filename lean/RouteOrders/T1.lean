import RouteOrders.T1Defs

/-!
# T1 — order independence of placing a drawing's piece groups

The ENGINE half of `pipeline/sim/route-orders.ts` builds, per drawn route node, a DAG over subsets of
the drawing's piece groups, and relies on one fact to make that a DAG over SUBSETS rather than over
sequences: the board after placing a set of groups does not depend on the order they went in. This
file proves that fact over the SEQUENTIAL process the engine runs, mirroring

* `applyCells` (`route-demos.ts`): write every cell of the piece, then remove every full row and push
  one empty row on top per removed row (compaction);
* `initialRowmap` / `advanceRowmap` (`route-facts.ts`): the rowmap is a list aligned with the engine
  rows, holding the diagram row each engine row is; it starts as the identity, and after a clear the
  cleared rows' entries leave and fresh entries (never a diagram row) are pushed on top;
* `nodeDag` (`route-orders.ts`): a group's diagram cell `(x, d)` is written at engine row
  `rowmap.indexOf(d)`.

Two modelling choices, both stated rather than hidden:

* A fresh rowmap entry is `none`. The engine uses `max(1000, …rowmap) + 1`, a number that is never a
  diagram row (diagram rows are < 40), so the only thing the engine ever does with it — look up a
  diagram row and not find it — is what `none` does.
* `writeCell` writes the engine row(s) whose rowmap entry is `some d`. `write_eq_set_idxOf` proves
  that this IS `rows.set (rowmap.idxOf (some d))` whenever `some d` occurs at most once in the rowmap,
  and `canon_rowmap_once` proves every board this process reaches has that property when the initial
  diagram rows are distinct (they are: `initialRowmap` is `0, 1, …, H-1`); `placeAllIdx_eq_placeAll`
  lifts that from one cell to the whole process (every cell written at `rowmap.indexOf(d)`). A cell whose diagram row
  has already cleared writes nothing here; `nodeDag` refuses that edge (`if (e < 0) return`), and the
  theorem below holds for every sequence, so in particular for the ones the engine accepts.

The theorem needs no disjointness hypothesis: writes only ever set a cell, so overlapping cells
commute too. (`applyCells` throws on an overlap, and `nodeDag` refuses an occupied target before
calling it, so the engine never meets one.)

Proof shape: every reachable board is `canon W V` — the virtual diagram (initial rows with every
placed cell added) with its full rows filtered out and empty rows padded on top — and `V` depends
only on the SET of cells placed. So two permutations of the same groups reach one board.
-/

namespace RouteOrders.T1

/-! ## The canonical form -/

/-- The virtual diagram with the cells `cs` added (diagram row ids kept). -/
def addCells (V : List (Nat × Row)) (cs : List (Nat × Nat)) : List (Nat × Row) :=
  V.map (fun p => (p.1, fun x => p.2 x || decide ((x, p.1) ∈ cs)))

def canon (W : Nat) (V : List (Nat × Row)) : Board :=
  let keep := V.filter (fun p => !full W p.2)
  { rows := keep.map Prod.snd ++ List.replicate (V.length - keep.length) emptyRow,
    rowmap := keep.map (fun p => some p.1) ++ List.replicate (V.length - keep.length) none }

/-! The zipped view: one list of (row, rowmap entry) pairs. Only a proof device — the model (`T1Defs.lean`)
keeps the two lists apart, which is what lets a desynchronising mutant be stated at all. -/

abbrev Z := List (Row × Option Nat)

def ofZ (C : Z) : Board := { rows := C.map Prod.fst, rowmap := C.map Prod.snd }

def e0 : Row × Option Nat := (emptyRow, none)
def emb (p : Nat × Row) : Row × Option Nat := (p.2, some p.1)

def wc (c : Nat × Nat) (p : Row × Option Nat) : Row × Option Nat :=
  (if p.2 = some c.2 then setCell p.1 c.1 else p.1, p.2)

def wg (cs : List (Nat × Nat)) (p : Row × Option Nat) : Row × Option Nat :=
  match p.2 with
  | some d => (fun x => p.1 x || decide ((x, d) ∈ cs), p.2)
  | none => p

def ad (cs : List (Nat × Nat)) (p : Nat × Row) : Nat × Row :=
  (p.1, fun x => p.2 x || decide ((x, p.1) ∈ cs))

def clearZ (W : Nat) (C : Z) : Z :=
  let keep := C.filter (fun p => !full W p.1)
  keep ++ List.replicate (C.length - keep.length) e0

def canonZ (W : Nat) (V : List (Nat × Row)) : Z :=
  let keep := V.filter (fun p => !full W p.2)
  keep.map emb ++ List.replicate (V.length - keep.length) e0

theorem zipWith_fst_snd {γ : Type} (f : Row → Option Nat → γ) (C : Z) :
    List.zipWith f (C.map Prod.fst) (C.map Prod.snd) = C.map (fun p => f p.1 p.2) := by
  induction C with
  | nil => rfl
  | cons p C ih => simp [ih]

theorem zip_fst_snd (C : Z) : List.zip (C.map Prod.fst) (C.map Prod.snd) = C := by
  induction C with
  | nil => rfl
  | cons p C ih => simp [ih]

theorem ofZ_canonZ (W : Nat) (V : List (Nat × Row)) : ofZ (canonZ W V) = canon W V := by
  simp [ofZ, canonZ, canon, List.map_append, List.map_map, Function.comp_def, emb, e0]

theorem writeCell_ofZ (C : Z) (c : Nat × Nat) : writeCell (ofZ C) c = ofZ (C.map (wc c)) := by
  simp only [writeCell, ofZ, zipWith_fst_snd, List.map_map]
  constructor <;> rfl

theorem wg_nil (p : Row × Option Nat) : wg [] p = p := by
  rcases p with ⟨r, o⟩
  cases o with
  | none => rfl
  | some d => simp [wg]

theorem wg_wc (c : Nat × Nat) (g : List (Nat × Nat)) (p : Row × Option Nat) :
    wg g (wc c p) = wg (c :: g) p := by
  rcases p with ⟨r, o⟩
  rcases c with ⟨cx, cd⟩
  cases o with
  | none => simp [wg, wc]
  | some d =>
    simp only [wg, wc]
    congr 1
    funext x
    by_cases hd : d = cd
    · subst hd
      by_cases hx : x = cx
      · subst hx; simp [setCell]
      · simp [setCell, hx]
    · simp [hd]

theorem foldl_write (g : List (Nat × Nat)) (C : Z) :
    g.foldl writeCell (ofZ C) = ofZ (C.map (wg g)) := by
  induction g generalizing C with
  | nil => simp only [List.foldl_nil]; rw [show (wg []) = id from funext wg_nil, List.map_id]
  | cons c g ih =>
    simp only [List.foldl_cons, writeCell_ofZ, ih, List.map_map]
    congr 2
    funext p
    exact wg_wc c g p

theorem clearRows_ofZ (W : Nat) (C : Z) : clearRows W (ofZ C) = ofZ (clearZ W C) := by
  simp [clearRows, ofZ, clearZ, zip_fst_snd, List.map_append, e0]

theorem full_mono (W : Nat) (r : Row) (b : Nat → Bool) (h : full W r = true) :
    full W (fun x => r x || b x) = true := by
  simp only [full, List.all_eq_true] at *
  intro x hx
  simp [h x hx]

theorem not_full_empty (W : Nat) (hW : 0 < W) : full W emptyRow = false := by
  simp only [full]
  rw [Bool.eq_false_iff]
  intro h
  rw [List.all_eq_true] at h
  exact absurd (h 0 (List.mem_range.2 hW)) (by decide)

theorem step (W : Nat) (hW : 0 < W) (V : List (Nat × Row)) (g : List (Nat × Nat)) :
    clearZ W ((canonZ W V).map (wg g)) = canonZ W (V.map (ad g)) := by
  have hwe : ∀ p, wg g (emb p) = emb (ad g p) := fun _ => rfl
  have hw0 : wg g e0 = e0 := rfl
  have he0 : (!full W e0.1) = true := by
    simp [e0, not_full_empty W hW]
  -- the row filter after adding cells: rows already full stay full, so pre-filtering is redundant
  have hff : ((V.filter (fun p => !full W p.2)).map (ad g)).filter (fun p => !full W p.2)
      = (V.map (ad g)).filter (fun p => !full W p.2) := by
    rw [List.filter_map, List.filter_map, List.filter_filter]
    congr 1
    apply List.filter_congr
    intro p _
    simp only [Function.comp_def, ad]
    cases hp : full W p.2
    · simp
    · simp [full_mono W p.2 _ hp]
  have hlen1 : ((V.map (ad g)).filter (fun p => !full W p.2)).length
      ≤ (V.filter (fun p => !full W p.2)).length := by
    rw [← hff]
    exact Nat.le_trans (List.length_filter_le _ _) (by simp)
  have hlen2 : (V.filter (fun p => !full W p.2)).length ≤ V.length := List.length_filter_le _ _
  simp only [canonZ, clearZ, List.map_append, List.map_map, List.map_replicate]
  have hm : (wg g ∘ emb) = (emb ∘ ad g) := by funext p; rfl
  rw [hm, hw0, List.filter_append, List.filter_replicate]
  simp only [he0, ite_true]
  rw [← List.map_map, List.filter_map]
  have hfe : ((fun p : Row × Option Nat => !full W p.1) ∘ emb) = (fun p : Nat × Row => !full W p.2) := by
    funext p; rfl
  rw [hfe, hff]
  simp only [List.append_assoc, List.replicate_append_replicate, List.length_append,
    List.length_map, List.length_replicate]
  congr 2
  omega

theorem place_canon (W : Nat) (hW : 0 < W) (V : List (Nat × Row)) (g : List (Nat × Nat)) :
    place W (canon W V) g = canon W (addCells V g) := by
  rw [place, ← ofZ_canonZ, foldl_write, clearRows_ofZ, step W hW, ofZ_canonZ]
  rfl

theorem addCells_nil (V : List (Nat × Row)) : addCells V [] = V := by
  simp [addCells]

theorem addCells_append (V : List (Nat × Row)) (g h : List (Nat × Nat)) :
    addCells (addCells V g) h = addCells V (g ++ h) := by
  simp only [addCells, List.map_map]
  congr 1
  funext p
  simp [Bool.or_assoc]

theorem placeAll_canon (W : Nat) (hW : 0 < W) (gs : List (List (Nat × Nat))) :
    ∀ V, placeAll W (canon W V) gs = canon W (addCells V gs.flatten) := by
  induction gs with
  | nil => intro V; simp [placeAll, addCells_nil]
  | cons g gs ih =>
    intro V
    simp only [placeAll, List.foldl_cons] at *
    rw [place_canon W hW, ih, addCells_append, List.flatten_cons]

theorem initial_eq_canon (W : Nat) (V : List (Nat × Row)) (h : ∀ p ∈ V, full W p.2 = false) :
    initial V = canon W V := by
  have hf : V.filter (fun p => !full W p.2) = V := by
    rw [List.filter_eq_self]; intro p hp; simp [h p hp]
  simp [initial, canon, hf]

/-- **T1.** From a board with no full row (any parent `applyCells` left), placing any permutation of
    the same list of groups leaves the same engine board AND the same rowmap. -/
theorem order_independent (W : Nat) (hW : 0 < W) (V : List (Nat × Row))
    (hV : ∀ p ∈ V, full W p.2 = false) (gs₁ gs₂ : List (List (Nat × Nat))) (hp : gs₁.Perm gs₂) :
    placeAll W (initial V) gs₁ = placeAll W (initial V) gs₂ := by
  rw [initial_eq_canon W V hV, placeAll_canon W hW, placeAll_canon W hW]
  congr 1
  simp only [addCells]
  congr 1
  funext p
  congr 1
  funext x
  congr 1
  simp only [List.mem_flatten, hp.mem_iff]

/-! ## The write is `rows.set (rowmap.indexOf d)` on every reachable board -/

theorem zipWith_absent (x d : Nat) : ∀ (rows : List Row) (rm : List (Option Nat)),
    rows.length = rm.length → some d ∉ rm →
    List.zipWith (fun r o => if o = some d then setCell r x else r) rows rm = rows
  | [], _, _, _ => by simp
  | _ :: _, [], hl, _ => by simp at hl
  | r :: rows, o :: rm, hl, hm => by
    have ho : o ≠ some d := fun h => hm (h ▸ List.mem_cons_self)
    have hm' : some d ∉ rm := fun h => hm (List.mem_cons_of_mem _ h)
    simp only [List.zipWith_cons_cons, ho, ite_false]
    rw [zipWith_absent x d rows rm (by simpa using hl) hm']

/-- The model's write (every row whose rowmap entry is `d`) is the engine's write at
    `rowmap.indexOf(d)` whenever `d` occurs at most once in the rowmap. When `d` is absent,
    `idxOf` is the length, `set` is a no-op, and so is the write (the engine refuses that edge). -/
theorem write_eq_set_idxOf (x d : Nat) : ∀ (rows : List Row) (rm : List (Option Nat)),
    rows.length = rm.length → rm.count (some d) ≤ 1 →
    List.zipWith (fun r o => if o = some d then setCell r x else r) rows rm
      = rows.set (rm.idxOf (some d)) (setCell (rows.getD (rm.idxOf (some d)) emptyRow) x)
  | [], _, _, _ => by simp
  | _ :: _, [], hl, _ => by simp at hl
  | r :: rows, o :: rm, hl, hc => by
    by_cases ho : o = some d
    · subst ho
      have h0 : rm.count (some d) = 0 := by simp at hc; omega
      rw [List.count_eq_zero] at h0
      simp only [List.zipWith_cons_cons, ite_true, List.idxOf_cons_self, List.set_cons_zero,
        List.getD_cons_zero]
      rw [zipWith_absent x d rows rm (by simpa using hl) h0]
    · have hne : (o == some d) = false := by simp [ho]
      simp only [List.zipWith_cons_cons, ho, ite_false, List.idxOf_cons, hne, Bool.false_eq_true,
        List.set_cons_succ, List.getD_cons_succ]
      rw [List.count_cons_of_ne ho] at hc
      rw [write_eq_set_idxOf x d rows rm (by simpa using hl) hc]

theorem canon_rowmap_once (W : Nat) (V : List (Nat × Row)) (hV : (V.map Prod.fst).Nodup) (d : Nat) :
    (canon W V).rowmap.count (some d) ≤ 1 := by
  have hsub : ((V.filter (fun p => !full W p.2)).map Prod.fst).Sublist (V.map Prod.fst) :=
    (List.filter_sublist).map _
  have hnd : (((V.filter (fun p => !full W p.2)).map Prod.fst).map some).Nodup :=
    (hsub.nodup hV).map some (fun _ _ h h' => h (Option.some.inj h'))
  simp only [List.map_map, Function.comp_def] at hnd
  simp only [canon, List.count_append, List.count_replicate]
  have : (none == some d) = false := rfl
  rw [this]
  simp only [Bool.false_eq_true, ite_false, Nat.add_zero]
  rw [hnd.count]
  split <;> omega

theorem canon_length (W : Nat) (V : List (Nat × Row)) :
    (canon W V).rows.length = (canon W V).rowmap.length := by
  simp [canon]

/-- On every board the process reaches from `initial V` (distinct diagram rows, no full row),
    `writeCell` is exactly the engine's write at `rowmap.indexOf(d)`. -/
theorem reachable_write_is_indexOf (W : Nat) (hW : 0 < W) (V : List (Nat × Row))
    (hV : ∀ p ∈ V, full W p.2 = false) (hnd : (V.map Prod.fst).Nodup)
    (gs : List (List (Nat × Nat))) (x d : Nat) :
    let b := placeAll W (initial V) gs
    (writeCell b (x, d)).rows
      = b.rows.set (b.rowmap.idxOf (some d)) (setCell (b.rows.getD (b.rowmap.idxOf (some d)) emptyRow) x) := by
  intro b
  have hb : b = canon W (addCells V gs.flatten) := by
    simp only [b]; rw [initial_eq_canon W V hV, placeAll_canon W hW]
  have hnd' : ((addCells V gs.flatten).map Prod.fst).Nodup := by
    simpa [addCells, List.map_map, Function.comp_def] using hnd
  rw [hb]
  exact write_eq_set_idxOf x d _ _ (canon_length W _) (canon_rowmap_once W _ hnd' d)


/-! ## The whole process, written with the engine's `indexOf` write

`reachable_write_is_indexOf` is about one cell on a reachable board. This closes the link for the
whole sequential process: write every cell at `rowmap.indexOf(d)` (as `nodeDag` does), clear after each
group, and the board is the model's, for every list of groups. -/

/-- `nodeDag`'s write: cell `(x, d)` goes to engine row `rowmap.indexOf(d)` (a no-op when `d` has
    cleared: `idxOf` is then the length and `set` changes nothing). -/
def writeIdx (b : Board) (c : Nat × Nat) : Board :=
  { rows := b.rows.set (b.rowmap.idxOf (some c.2))
      (setCell (b.rows.getD (b.rowmap.idxOf (some c.2)) emptyRow) c.1),
    rowmap := b.rowmap }

def placeIdx (W : Nat) (b : Board) (g : List (Nat × Nat)) : Board := clearRows W (g.foldl writeIdx b)

def placeAllIdx (W : Nat) (b : Board) (gs : List (List (Nat × Nat))) : Board := gs.foldl (placeIdx W) b

/-- Writing a group cell by cell keeps the rowmap, so the at-most-once property holds at every
    cell, and each `indexOf` write is the model's. -/
theorem foldl_writeIdx (g : List (Nat × Nat)) : ∀ b : Board,
    b.rows.length = b.rowmap.length → (∀ d, b.rowmap.count (some d) ≤ 1) →
    g.foldl writeIdx b = g.foldl writeCell b := by
  induction g with
  | nil => intros; rfl
  | cons c g ih =>
    intro b hl hc
    have he : writeIdx b c = writeCell b c := by
      simp only [writeIdx, writeCell]
      rw [write_eq_set_idxOf c.1 c.2 b.rows b.rowmap hl (hc c.2)]
    simp only [List.foldl_cons, he]
    exact ih _ (by simp [writeCell, hl]) hc

theorem placeIdx_canon (W : Nat) (V : List (Nat × Row)) (hV : (V.map Prod.fst).Nodup)
    (g : List (Nat × Nat)) : placeIdx W (canon W V) g = place W (canon W V) g := by
  simp only [placeIdx, place]
  rw [foldl_writeIdx g _ (canon_length W V) (canon_rowmap_once W V hV)]

theorem placeAllIdx_canon (W : Nat) (hW : 0 < W) (gs : List (List (Nat × Nat))) :
    ∀ V : List (Nat × Row), (V.map Prod.fst).Nodup →
      placeAllIdx W (canon W V) gs = placeAll W (canon W V) gs := by
  induction gs with
  | nil => intros; rfl
  | cons g gs ih =>
    intro V hnd
    have hnd' : ((addCells V g).map Prod.fst).Nodup := by
      simpa [addCells, List.map_map, Function.comp_def] using hnd
    simp only [placeAllIdx, placeAll, List.foldl_cons] at ih ⊢
    rw [placeIdx_canon W V hnd g, place_canon W hW]
    exact ih _ hnd'

/-- The engine's `indexOf` process and the model agree on every list of groups, from any board the
    bag can start on (distinct diagram rows, no full row). -/
theorem placeAllIdx_eq_placeAll (W : Nat) (hW : 0 < W) (V : List (Nat × Row))
    (hV : ∀ p ∈ V, full W p.2 = false) (hnd : (V.map Prod.fst).Nodup)
    (gs : List (List (Nat × Nat))) :
    placeAllIdx W (initial V) gs = placeAll W (initial V) gs := by
  rw [initial_eq_canon W V hV]
  exact placeAllIdx_canon W hW gs V hnd

/-! ## Axioms gate: no proof-hole axiom, no native-code axiom; only Lean's three standard axioms. -/

/-- info: 'RouteOrders.T1.order_independent' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.T1.order_independent

/-- info: 'RouteOrders.T1.place_canon' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.T1.place_canon

/-- info: 'RouteOrders.T1.reachable_write_is_indexOf' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.T1.reachable_write_is_indexOf

/-- info: 'RouteOrders.T1.placeAllIdx_eq_placeAll' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.T1.placeAllIdx_eq_placeAll

end RouteOrders.T1
