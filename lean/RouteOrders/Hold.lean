import RouteOrders.HoldDefs

/-!
# T2 and T4 — the hold search of `route-orders.ts` `accepts()`

No Tetris rule appears here. A node is DATA: which group a dealt token is (`groupOf`), and which
groups the engine can place on the board of a placed set (`can s g`, the DAG's edges — the
artefact's `[subset, group]` pairs, plus "g is not yet in s"). Every theorem below holds for EVERY
such `Dag`; `RouteOrders.Counts` instantiates it with the committed artefact's nodes.

The stream is the bag's dealt order followed by one token of the next bag, `*`, which may enter the
hold and is never placed. A state is (placed set `s`, the rest of the stream `r`, the hold `h`); the
rest of the stream is `stream.drop i` for the task's stream index `i`, which is the form the
recursion runs on.

* `Step` is the SPECIFICATION: three nondeterministic moves (a) place the current token, (b) with
  a held token, place it and hold the current one (which may be `*`), (c) with an empty hold and a
  current token that is not `*`, hold it and place the next one. `*` is never placed.
* `acc` is the DECISION PROCEDURE, written as `accepts()`'s inner `go`. `go` also keeps a `seen`
  set; that memo is sound only because every move consumes stream, so a state is never revisited
  while it is still being decided — `acc` is the same recursion without it.

T2: `acc` returns true iff the relation reaches the full set (`acc_iff_reaches`).
T4: starting with an empty hold accepts exactly the orders that starting with the first piece
already held does (`empty_eq_next`), so the artefact's two modes must have equal counts.
-/

namespace RouteOrders.Hold

theorem place_some {D : Dag} {s s' : Nat} {t : Tok} :
    place D s t = some s' ↔ t ≠ .star ∧ ∃ g, D.groupOf t = some g ∧ D.can s g = true ∧ s' = s ||| bit g := by
  unfold place
  by_cases ht : t = .star
  · simp [ht]
  · simp only [ht, ite_false, ne_eq, not_false_eq_true, true_and]
    cases hg : D.groupOf t with
    | none => simp
    | some g =>
      cases hc : D.can s g with
      | false => simp [hc]
      | true =>
        simp only [hc, ite_true, Option.some.injEq, true_and, exists_eq_left']
        exact eq_comm

theorem place_star (D : Dag) (s : Nat) : place D s .star = none := by simp [place]

/-! Equation lemmas, one per shape of (stream, hold); proofs rewrite with these and never unfold
`acc` wholesale. -/

theorem acc_nil (D : Dag) (s : Nat) (h : Option Tok) : acc D s [] h = (s == D.full) := by
  rw [acc.eq_1]

theorem acc_some (D : Dag) (s : Nat) (t : Tok) (r : List Tok) (th : Tok) :
    acc D s (t :: r) (some th) =
      ((s == D.full || (match place D s t with | some s' => acc D s' r (some th) | none => false))
        || (match place D s th with | some s' => acc D s' r (some t) | none => false)) := by
  rw [acc.eq_2]; simp; rfl

theorem acc_none_one (D : Dag) (s : Nat) (t : Tok) :
    acc D s [t] none =
      (s == D.full || (match place D s t with | some s' => acc D s' [] none | none => false)) := by
  rw [acc.eq_4]
  · simp; rfl
  · intro _ _ _ h; cases h

theorem acc_none_two (D : Dag) (s : Nat) (t t' : Tok) (r : List Tok) :
    acc D s (t :: t' :: r) none =
      ((s == D.full || (match place D s t with | some s' => acc D s' (t' :: r) none | none => false))
        || ((t != .star) && (match place D s t' with | some s' => acc D s' r (some t) | none => false))) := by
  rw [acc.eq_3]; simp; rfl

theorem acc_of_full (D : Dag) (s : Nat) (r : List Tok) (h : Option Tok) (hs : s = D.full) :
    acc D s r h = true := by
  subst hs
  match r, h with
  | [], _ => simp [acc_nil]
  | _ :: _, some _ => simp [acc_some]
  | [_], none => simp [acc_none_one]
  | _ :: _ :: _, none => simp [acc_none_two]

/-- One move of the specification never loses acceptance. -/
theorem acc_of_step {D : Dag} {x y : St} (hs : Step D x y) (hy : acc D y.1 y.2.1 y.2.2 = true) :
    acc D x.1 x.2.1 x.2.2 = true := by
  cases hs with
  | @play s t r h g ht hg hc =>
    have hp : place D s t = some (s ||| bit g) := place_some.2 ⟨ht, g, hg, hc, rfl⟩
    simp only at hy ⊢
    match r, h with
    | _, some th => rw [acc_some, hp]; simp [hy]
    | [], none => rw [acc_none_one, hp]; simp [hy]
    | _ :: _, none => rw [acc_none_two, hp]; simp [hy]
  | @swap s t r th g ht hg hc =>
    have hp : place D s th = some (s ||| bit g) := place_some.2 ⟨ht, g, hg, hc, rfl⟩
    simp only at hy ⊢
    rw [acc_some, hp]; simp [hy]
  | @holdFirst s t t' r g ht ht' hg hc =>
    have hp : place D s t' = some (s ||| bit g) := place_some.2 ⟨ht', g, hg, hc, rfl⟩
    simp only at hy ⊢
    rw [acc_none_two, hp]; simp [hy, ht]

theorem acc_of_star {D : Dag} {x y : St} (hst : Star D x y) (hy : y.1 = D.full) :
    acc D x.1 x.2.1 x.2.2 = true := by
  induction hst with
  | refl x => exact acc_of_full D _ _ _ hy
  | step hxy _ ih => exact acc_of_step hxy (ih hy)

theorem acc_of_reaches {D : Dag} {x : St} (h : Reaches D x) : acc D x.1 x.2.1 x.2.2 = true := by
  obtain ⟨r, hh, hst⟩ := h
  exact acc_of_star hst rfl

theorem reaches_of_step {D : Dag} {x y : St} (hs : Step D x y) (hy : Reaches D y) : Reaches D x := by
  obtain ⟨r, h, hst⟩ := hy
  exact ⟨r, h, Star.step hs hst⟩

theorem reaches_of_acc (D : Dag) : ∀ (s : Nat) (r : List Tok) (h : Option Tok),
    acc D s r h = true → Reaches D (s, r, h)
  | s, [], h, ha => by
    rw [acc_nil, beq_iff_eq] at ha
    exact ⟨[], h, ha ▸ Star.refl _⟩
  | s, t :: r, some th, ha => by
    rw [acc_some] at ha
    simp only [Bool.or_eq_true, beq_iff_eq] at ha
    rcases ha with (hf | ha) | ha
    · exact ⟨t :: r, some th, hf ▸ Star.refl _⟩
    · cases hp : place D s t with
      | none => simp [hp] at ha
      | some s' =>
        simp only [hp] at ha
        obtain ⟨ht, g, hg, hc, rfl⟩ := place_some.1 hp
        exact reaches_of_step (Step.play ht hg hc) (reaches_of_acc D _ r (some th) ha)
    · cases hp : place D s th with
      | none => simp [hp] at ha
      | some s' =>
        simp only [hp] at ha
        obtain ⟨ht, g, hg, hc, rfl⟩ := place_some.1 hp
        exact reaches_of_step (Step.swap ht hg hc) (reaches_of_acc D _ r (some t) ha)
  | s, [t], none, ha => by
    rw [acc_none_one] at ha
    simp only [Bool.or_eq_true, beq_iff_eq] at ha
    rcases ha with hf | ha
    · exact ⟨[t], none, hf ▸ Star.refl _⟩
    · cases hp : place D s t with
      | none => simp [hp] at ha
      | some s' =>
        simp only [hp] at ha
        obtain ⟨ht, g, hg, hc, rfl⟩ := place_some.1 hp
        exact reaches_of_step (Step.play ht hg hc) (reaches_of_acc D _ [] none ha)
  | s, t :: t' :: r, none, ha => by
    rw [acc_none_two] at ha
    simp only [Bool.or_eq_true, beq_iff_eq, Bool.and_eq_true, bne_iff_ne, ne_eq] at ha
    rcases ha with (hf | ha) | ⟨hts, ha⟩
    · exact ⟨t :: t' :: r, none, hf ▸ Star.refl _⟩
    · cases hp : place D s t with
      | none => simp [hp] at ha
      | some s' =>
        simp only [hp] at ha
        obtain ⟨ht, g, hg, hc, rfl⟩ := place_some.1 hp
        exact reaches_of_step (Step.play ht hg hc) (reaches_of_acc D _ (t' :: r) none ha)
    · cases hp : place D s t' with
      | none => simp [hp] at ha
      | some s' =>
        simp only [hp] at ha
        obtain ⟨ht', g, hg, hc, rfl⟩ := place_some.1 hp
        exact reaches_of_step (Step.holdFirst hts ht' hg hc) (reaches_of_acc D _ r (some t) ha)

/-- **T2.** The recursive decision procedure decides the specification's reachability. -/
theorem acc_iff_reaches (D : Dag) (s : Nat) (r : List Tok) (h : Option Tok) :
    acc D s r h = true ↔ Reaches D (s, r, h) :=
  ⟨reaches_of_acc D s r h, fun hr => acc_of_reaches hr⟩

/-- T2 at the level of a node: accepting is reaching the full set, and the full board is right. -/
theorem acceptsEmpty_iff (D : Dag) (fullOk : Bool) (q : List Char) :
    acceptsEmpty D fullOk q = true ↔ fullOk = true ∧ Reaches D (0, streamOf q, none) := by
  simp [acceptsEmpty, acc_iff_reaches]

theorem acceptsNext_iff (D : Dag) (fullOk : Bool) (c : Char) (q : List Char) :
    acceptsNext D fullOk (c :: q) = true ↔ fullOk = true ∧ Reaches D (0, streamOf q, some (.piece c)) := by
  simp [acceptsNext, acc_iff_reaches]

/-! ## T4 -/

/-- Holding the current token from an empty hold, without placing, changes nothing — on a stream
    that ends in `*` and holds no other `*`. (False for an arbitrary list: see the comment in
    `acc_cons_none`'s proof.) -/
theorem acc_cons_none (D : Dag) : ∀ (Q : List Tok) (s : Nat) (t : Tok), t ≠ .star →
    (∀ u ∈ Q, u ≠ .star) →
    acc D s (t :: (Q ++ [.star])) none = acc D s (Q ++ [.star]) (some t)
  | [], s, t, _, _ => by
    simp only [List.nil_append]
    rw [acc_none_two, acc_some, place_star]
    cases hp : place D s t with
    | none => simp
    | some s' => simp [acc_none_one, acc_nil, place_star]
  | t' :: Q, s, t, ht, hQ => by
    have ht' : t' ≠ .star := hQ t' List.mem_cons_self
    have hQ' : ∀ u ∈ Q, u ≠ .star := fun u hu => hQ u (List.mem_cons_of_mem _ hu)
    have ih := fun s' => acc_cons_none D Q s' t' ht' hQ'
    have htb : (t != .star) = true := by simp [ht]
    simp only [List.cons_append] at ih ⊢
    rw [acc_none_two, acc_some, htb, Bool.true_and]
    cases hp : place D s t with
    | none =>
      cases place D s t' <;> simp
    | some s' =>
      simp only [ih s']
      cases place D s t' with
      | none => simp
      | some s'' =>
        simp only
        cases (s == D.full) <;> cases acc D s'' (Q ++ [Tok.star]) (some t) <;>
          cases acc D s' (Q ++ [Tok.star]) (some t') <;> rfl

/-- **T4.** For every dealt order, the empty-hold mode and the next-held mode agree. -/
theorem empty_eq_next (D : Dag) (fullOk : Bool) (q : List Char) (hq : q ≠ []) :
    acceptsEmpty D fullOk q = acceptsNext D fullOk q := by
  cases q with
  | nil => exact absurd rfl hq
  | cons c q =>
    simp only [acceptsEmpty, acceptsNext, streamOf, List.map_cons, List.cons_append]
    rw [acc_cons_none D (q.map .piece) 0 (.piece c) (by simp) (by simp)]

/-- T4 as the artefact's two counts: over any list of non-empty orders, the counts are equal. -/
theorem count_empty_eq_next (D : Dag) (fullOk : Bool) (orders : List (List Char))
    (h : ∀ q ∈ orders, q ≠ []) :
    (orders.filter (acceptsEmpty D fullOk)).length = (orders.filter (acceptsNext D fullOk)).length := by
  rw [List.filter_congr (fun q hq => empty_eq_next D fullOk q (h q hq))]


/-! ## Axioms gate: no proof-hole axiom, no native-code axiom; only Lean's three standard axioms. -/

/-- info: 'RouteOrders.Hold.acc_iff_reaches' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.Hold.acc_iff_reaches

/-- info: 'RouteOrders.Hold.acceptsEmpty_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.Hold.acceptsEmpty_iff

/-- info: 'RouteOrders.Hold.acceptsNext_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.Hold.acceptsNext_iff

/-- info: 'RouteOrders.Hold.acc_cons_none' depends on axioms: [propext] -/
#guard_msgs in
#print axioms RouteOrders.Hold.acc_cons_none

/-- info: 'RouteOrders.Hold.empty_eq_next' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.Hold.empty_eq_next

/-- info: 'RouteOrders.Hold.count_empty_eq_next' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms RouteOrders.Hold.count_empty_eq_next

end RouteOrders.Hold
