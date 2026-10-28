/-!
# T2/T4's model: tokens, the DAG, the specification `Step`, and the procedure `acc`

The definitions only, split out of `RouteOrders.Hold` so that `RouteOrders.HoldWitness` (and the
mutant procedures in `RouteOrders.HoldMutants`) depend on the MODEL and not on the proofs:
`lean/mutate.sh` plants each T2/T4 mutant into `acc` here, and the witnesses must still build, and
fail on their own `decide`, when the proofs in `Hold.lean` stop going through. `Hold.lean` says what
each definition is.
-/

namespace RouteOrders.Hold

inductive Tok where
  | piece (c : Char)
  | carried
  | star
  deriving DecidableEq, Repr

structure Dag where
  /-- the group a token places, if any (a dealt piece letter, or the carried token) -/
  groupOf : Tok → Option Nat
  /-- the DAG: group `g` can be placed on the board of placed set `s` -/
  can : Nat → Nat → Bool
  full : Nat

def bit (g : Nat) : Nat := 1 <<< g

abbrev St := Nat × List Tok × Option Tok

/-- The specification: one placement per move. -/
inductive Step (D : Dag) : St → St → Prop
  /-- (a) place the current token -/
  | play {s t r h g} : t ≠ .star → D.groupOf t = some g → D.can s g = true →
      Step D (s, t :: r, h) (s ||| bit g, r, h)
  /-- (b) place the held token, hold the current one -/
  | swap {s t r th g} : th ≠ .star → D.groupOf th = some g → D.can s g = true →
      Step D (s, t :: r, some th) (s ||| bit g, r, some t)
  /-- (c) hold empty: hold the current token, place the next one -/
  | holdFirst {s t t' r g} : t ≠ .star → t' ≠ .star → D.groupOf t' = some g → D.can s g = true →
      Step D (s, t :: t' :: r, none) (s ||| bit g, r, some t)

/-- Reflexive-transitive closure (no Mathlib). -/
inductive Star (D : Dag) : St → St → Prop
  | refl (x : St) : Star D x x
  | step {x y z : St} : Step D x y → Star D y z → Star D x z

def Reaches (D : Dag) (x : St) : Prop := ∃ r h, Star D x (D.full, r, h)

/-! ## The decision procedure -/

def place (D : Dag) (s : Nat) (t : Tok) : Option Nat :=
  if t = .star then none
  else match D.groupOf t with
    | some g => if D.can s g then some (s ||| bit g) else none
    | none => none

def acc (D : Dag) : Nat → List Tok → Option Tok → Bool
  | s, [], _ => s == D.full
  | s, t :: r, h =>
    (s == D.full)
    || (match place D s t with
        | some s' => acc D s' r h
        | none => false)
    || (match h with
        | some th => (match place D s th with
            | some s' => acc D s' r (some t)
            | none => false)
        | none => false)
    || (match h, r with
        | none, t' :: r' => (t != .star) && (match place D s t' with
            | some s' => acc D s' r' (some t)
            | none => false)
        | _, _ => false)

/-- A dealt order's stream: the bag's pieces, then the next bag's token. -/
def streamOf (q : List Char) : List Tok := q.map .piece ++ [.star]

/-- `accepts(dag, q, null)` and `accepts(dag, q.slice(1), q[0])`, with `full_ok`. -/
def acceptsEmpty (D : Dag) (fullOk : Bool) (q : List Char) : Bool :=
  fullOk && acc D 0 (streamOf q) none

def acceptsNext (D : Dag) (fullOk : Bool) : List Char → Bool
  | c :: q => fullOk && acc D 0 (streamOf q) (some (.piece c))
  | [] => fullOk && acc D 0 (streamOf []) none

end RouteOrders.Hold
