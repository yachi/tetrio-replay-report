import RouteOrders.HoldDefs
import RouteOrders.HoldMutants

/-!
# T2's and T4's mutants DISAGREE with the real procedure, on concrete toy DAGs (kernel `decide`)

`Discriminate.lean` shows each mutant changes a count on the committed data, but by `native_decide`,
and it says nothing about the SPECIFICATION side of T2. These witnesses do both, in the kernel:

* each T2 specification mutant — `Step` without (c), `Step` with `'*'` placeable, `Step` with a hold
  move that places nothing — is written as a relation (`StepM`, one rule changed per flag of
  `HoldMutants.Mut`, so the flags mean the same thing here as in the counts), and on a toy DAG the
  mutated relation's reachability and the real `acc` disagree;
* the T4 mutant — the procedure without case (c), which is `HoldMutants.accM {noHoldFirst := true}` —
  accepts a toy order in one hold mode and not the other, where the real `acc` accepts it in both.

Each witness is a conjunction whose REAL half (`acc`, `acceptsEmpty`, `acceptsNext` as defined in
`HoldDefs`) is proved by `decide`. That is the half `lean/mutate.sh` refutes: it plants each mutant
into `HoldDefs.acc` and requires the matching witness here to fail. This module imports only the
model, never `Hold.lean`'s proofs, so it still builds — and fails on its own `decide` — when the
planted mutant breaks those proofs.

`stepM_default` ties the relation family to the specification: with every flag off, `StepM` IS
`Step`, so each mutated relation is `Step` with exactly one rule changed.
-/

namespace RouteOrders.HoldWitness
open RouteOrders.Hold RouteOrders.HoldMutants

/-! ## The mutated specifications -/

/-- `Step` with the rules switched by `m`: (c) removed under `noHoldFirst`; `'*'` placeable as any
    group the DAG allows under `starWild`; a hold move without a placement (the current token enters
    the hold, discarding any held one) under `holdOnly`. -/
inductive StepM (m : Mut) (D : Dag) : St → St → Prop
  | play {s t r h g} : t ≠ .star → D.groupOf t = some g → D.can s g = true →
      StepM m D (s, t :: r, h) (s ||| bit g, r, h)
  | swap {s t r th g} : th ≠ .star → D.groupOf th = some g → D.can s g = true →
      StepM m D (s, t :: r, some th) (s ||| bit g, r, some t)
  | holdFirst {s t t' r g} : m.noHoldFirst = false → t ≠ .star → t' ≠ .star →
      D.groupOf t' = some g → D.can s g = true →
      StepM m D (s, t :: t' :: r, none) (s ||| bit g, r, some t)
  | playStar {s r h g} : m.starWild = true → D.can s g = true →
      StepM m D (s, .star :: r, h) (s ||| bit g, r, h)
  | holdOnly {s t r h} : m.holdOnly = true → t ≠ .star →
      StepM m D (s, t :: r, h) (s, r, some t)

inductive StarM (m : Mut) (D : Dag) : St → St → Prop
  | refl (x : St) : StarM m D x x
  | step {x y z : St} : StepM m D x y → StarM m D y z → StarM m D x z

def ReachesM (m : Mut) (D : Dag) (x : St) : Prop := ∃ r h, StarM m D x (D.full, r, h)

/-- With every flag off the family is the specification itself. -/
theorem stepM_default (D : Dag) (x y : St) : StepM {} D x y ↔ Step D x y := by
  constructor
  · intro h
    cases h with
    | play ht hg hc => exact Step.play ht hg hc
    | swap ht hg hc => exact Step.swap ht hg hc
    | holdFirst _ ht ht' hg hc => exact Step.holdFirst ht ht' hg hc
    | playStar hm => exact absurd hm (by decide)
    | holdOnly hm => exact absurd hm (by decide)
  · intro h
    cases h with
    | play ht hg hc => exact StepM.play ht hg hc
    | swap ht hg hc => exact StepM.swap ht hg hc
    | holdFirst ht ht' hg hc => exact StepM.holdFirst rfl ht ht' hg hc

/-! ## Soundness of the mutant procedure for its relation (for the negative witness)

A mutated relation that does NOT reach is shown by its own procedure `accM m` rejecting: every move
of `StepM m` keeps `accM m` true. (`starWild` is excluded: `accM` tries only groups `< 7` there, and
no negative witness below needs it.) -/

theorem place_of {D : Dag} {s g : Nat} {t : Tok} (ht : t ≠ .star) (hg : D.groupOf t = some g)
    (hc : D.can s g = true) : place D s t = some (s ||| bit g) := by
  simp [place, ht, hg, hc]

theorem accM_of_step {m : Mut} (hm : m.starWild = false) {D : Dag} {x y : St} (hs : StepM m D x y)
    (hy : accM m D y.1 y.2.1 y.2.2 = true) : accM m D x.1 x.2.1 x.2.2 = true := by
  cases hs with
  | @play s t r h g ht hg hc =>
    simp only at hy ⊢
    rw [accM.eq_def]; simp only []; rw [place_of ht hg hc]; simp [hy]
  | @swap s t r th g ht hg hc =>
    simp only at hy ⊢
    rw [accM.eq_def]; simp only []; rw [place_of ht hg hc]; simp [hy]
  | @holdFirst s t t' r g hf ht ht' hg hc =>
    simp only at hy ⊢
    rw [accM.eq_def]; simp only []; rw [place_of ht' hg hc]; simp [hy, hf, ht]
  | playStar hw => rw [hm] at hw; cases hw
  | @holdOnly s t r h ho ht =>
    simp only at hy ⊢
    rw [accM.eq_def]; simp [hy, ho, ht]

theorem accM_of_full (m : Mut) (D : Dag) (s : Nat) (r : List Tok) (h : Option Tok) (hs : s = D.full) :
    accM m D s r h = true := by
  subst hs
  cases r with
  | nil => rw [accM.eq_def]; simp
  | cons t r => rw [accM.eq_def]; simp

theorem accM_of_star {m : Mut} (hm : m.starWild = false) {D : Dag} {x y : St}
    (hst : StarM m D x y) (hy : y.1 = D.full) : accM m D x.1 x.2.1 x.2.2 = true := by
  induction hst with
  | refl x => exact accM_of_full m D _ _ _ hy
  | step hxy _ ih => exact accM_of_step hm hxy (ih hy)

theorem accM_of_reaches {m : Mut} (hm : m.starWild = false) {D : Dag} {x : St}
    (h : ReachesM m D x) : accM m D x.1 x.2.1 x.2.2 = true := by
  obtain ⟨r, hh, hst⟩ := h
  exact accM_of_star hm hst rfl

/-! ## The toy DAG

Two groups: `a` is group 0, `b` is group 1, `c` places no group (a token the DAG has no edge for).
Edges: `b` on the empty board, then `a` on `{b}`; the full set is `{a, b}` = 3. -/

def toy : Dag where
  groupOf := fun t => match t with
    | .piece 'a' => some 0
    | .piece 'b' => some 1
    | _ => none
  can := fun s g => (s == 0 && g == 1) || (s == 2 && g == 0)
  full := 3

def pa : Tok := .piece 'a'
def pb : Tok := .piece 'b'
def pc : Tok := .piece 'c'

/-! ## T2 witnesses: the mutated relation against the real procedure -/

/-- `Step` WITHOUT case (c). Dealt `a, b`: `a` cannot go first, so only holding it and placing `b`
    gets anywhere. The real procedure accepts; the mutated relation never reaches the full set. -/
theorem noHoldFirst_witness :
    acc toy 0 [pa, pb, .star] none = true ∧ ¬ ReachesM {noHoldFirst := true} toy (0, [pa, pb, .star], none) := by
  refine ⟨by decide, fun h => ?_⟩
  have := accM_of_reaches rfl h
  revert this; decide

/-- `Step` WITH `'*'` placeable. Dealt `b` alone: after it only `'*'` is left, which the real rules
    may hold but never place. The real procedure rejects; the mutated relation places `'*'` as `a`. -/
theorem playStar_witness :
    acc toy 0 [pb, .star] none = false ∧ ReachesM {starWild := true} toy (0, [pb, .star], none) := by
  refine ⟨by decide, [], none, ?_⟩
  refine StarM.step (y := (2, [.star], none)) (StepM.play (g := 1) (by decide) (by decide) (by decide)) ?_
  exact StarM.step (StepM.playStar (g := 0) rfl (by decide)) (StarM.refl _)

/-- `Step` WITH a hold move that places nothing. Dealt `c, c, b, a`: two tokens with no group come
    first, and the real rules can set aside only one of them (case (c) must place the next token).
    The real procedure rejects; the mutated relation discards both and places `b`, `a`. -/
theorem holdOnly_witness :
    acc toy 0 [pc, pc, pb, pa, .star] none = false ∧
      ReachesM {holdOnly := true} toy (0, [pc, pc, pb, pa, .star], none) := by
  refine ⟨by decide, [.star], some pc, ?_⟩
  refine StarM.step (StepM.holdOnly rfl (by decide)) ?_
  refine StarM.step (StepM.holdOnly rfl (by decide)) ?_
  refine StarM.step (y := (2, [pa, .star], some pc)) (StepM.play (g := 1) (by decide) (by decide) (by decide)) ?_
  exact StarM.step (StepM.play (g := 0) (by decide) (by decide) (by decide)) (StarM.refl _)

/-! ## T4 witness: the procedure without case (c) breaks the equality of the two hold modes -/

/-- Dealt `a, b`. Without case (c) the empty-hold mode rejects (`a` cannot go first and cannot be
    set aside) while the next-held mode, which starts with `a` already held, accepts. The real
    procedure accepts in both modes, as T4 says it must. -/
theorem noCaseC_T4_witness :
    accM {noHoldFirst := true} toy 0 (streamOf ['a', 'b']) none = false ∧
      accM {noHoldFirst := true} toy 0 (streamOf ['b']) (some pa) = true ∧
      acceptsEmpty toy true ['a', 'b'] = true ∧ acceptsNext toy true ['a', 'b'] = true := by
  decide


/-! ## Axioms gate: no proof-hole axiom, no native-code axiom; only Lean's three standard axioms. -/

/-- info: 'RouteOrders.HoldWitness.stepM_default' depends on axioms: [propext] -/
#guard_msgs in
#print axioms RouteOrders.HoldWitness.stepM_default

/-- info: 'RouteOrders.HoldWitness.noHoldFirst_witness' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.HoldWitness.noHoldFirst_witness

/-- info: 'RouteOrders.HoldWitness.playStar_witness' depends on axioms: [propext] -/
#guard_msgs in
#print axioms RouteOrders.HoldWitness.playStar_witness

/-- info: 'RouteOrders.HoldWitness.holdOnly_witness' depends on axioms: [propext] -/
#guard_msgs in
#print axioms RouteOrders.HoldWitness.holdOnly_witness

/-- info: 'RouteOrders.HoldWitness.noCaseC_T4_witness' depends on axioms: [propext] -/
#guard_msgs in
#print axioms RouteOrders.HoldWitness.noCaseC_T4_witness

end RouteOrders.HoldWitness
