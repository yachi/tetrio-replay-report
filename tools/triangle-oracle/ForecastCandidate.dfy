// QUARANTINED-ANALYSIS PROOF — NOT a published claim. This lives under tools/triangle-oracle (the
// sim/oracle analysis home), never spec/, and carries NO claim id and NO report badge: the forecast
// section is sim-derived and quarantined by design. What it proves is the DECISION LOGIC of clause 2,
// so a human argument about the three candidates cannot smuggle in an unsound step (Dafny already
// rejected one — the "no LB in window => no straddle" over-approximation on line-count grounds).
//
// The frame constants are recorded ground truth from the .ttrm (interaction_confirm frames) and the
// Triangle-oracle lock frames, cross-checked against the recorded OUTGOING ige attack stream, which
// matches the oracle frame+amount-exact through lock 17 (roof f644 sent 4, T f765 sent 5, quad f817
// sent 5) — so the board carrying candidate A is verified at the forecast itself, not merely modelled.
// Reproduce: tools/triangle-oracle/probe-resolve-candidates.mjs (frame ordering) and
// probe-oracle-verify.mjs (attack-stream match).
//
// Clause-2 (floorOrigin) verdict for three of the full-round forecast_lineclear candidates the Triangle
// oracle finds, decided from ground-truth recorded frames + documented garbagespeed=20 ALONE — the
// linkage from frames to verdict is PROVEN, not asserted in comments. This is the exact part of the
// forecast decision that provenance reconstruction left unstable.
//
// ── WITHDRAWN 2026-08-16: A's and C's ROOF LOCKS WERE MISATTRIBUTED, AND SO WERE THEIR FRAMES ────
// These three, and the fourth candidate (2026-08-14 yachi 2026-08-14-10 r2 lock19) this header used
// to flag as UNPROVEN, are all `oracle-forecast.mjs` finds. That file rolls its OWN provenance by
// mirroring the engine's shift/splice with a force-align fallback (`:105-112`);
// `pipeline/sim/oracle-source.ts` replaced that a day later (2026-08-12, `a53a952`) with exact
// cell-identity provenance, and the tool was never moved onto it. Measured over six sessions by
// `pipeline/sim/check_provenance.ts`: the tool names an IMPOSSIBLE placer — a lock whose piece is
// not the letter the board draws in that cell — for **544 of 2024 (26.9%)** roof cells, against
// **0 of 4202** for `oracle-source.ts` and **0 of 1988** for the `sim.ts` hand-port.
//
// Three of the four candidates are among those 544, and each is caught by the letter alone:
//
//   | cand | roof cell | board draws | tool blames | that lock's piece | published source |
//   |------|-----------|-------------|-------------|-------------------|------------------|
//   | A    | r31 c6    | Z           | lock 12     | **T**             | lock 8, a Z      |
//   | C    | r23 c7    | L           | lock 6      | **I**             | lock 16, an L    |
//   | D    | r30 c3    | S           | lock 12     | **T**             | lock 10, an S    |
//   | B    | r33 c3    | L           | lock 19     | L — admissible    | lock 19, the same|
//
// So the frame constants below are not what their comments say. A's "roof 644" is lock 12's frame;
// A's roof is lock 8, frame **269**. C's `PlacerVerdict(11, 6)` is the tool's (support, roof); the
// published pair is (6, **16**) — the opposite order. Under `oracle-source.ts` A, C and D are all
// `reactive` (availability 2->2, 1->1 and 2->1 respectively; it FELL for D), so clause 2 is never
// reached for any of them and no clause-2 verdict about them is a fact about this corpus.
//
// **B is untouched.** Its roof is lock 19, piece L, frame 996 under BOTH sources, bit-identical, and
// it remains `forecast_lineclear` with `floorOrigin = arrived-later`. `CandidateB_NotPreExisted` is
// the only candidate lemma below that is instantiated by the published boards.
//
// Nothing published moves: none of A/C/D was ever inside `forecast-facts.json`, which is computed
// over `runCaseOracle` and the verified prefix.
//
// Model of forecast.ts:floorOrigin garbage branch (lines 333-343), for a garbage support cell:
//   after   := (no garbage present at the roof frame)      => it must have arrived later
//   unknown := (some garbage insertion straddles (roof,T]) => undecidable
//   verdict := after ? ArrivedLater : unknown ? Undetermined : PreExisted
//
// Ground-truth facts used:
//  (1) a garbage batch's TRUE insertion frame >= confirm + garbagespeed (the next-lock gate only delays);
//  (2) the 6-row / hole-col-6 block observed on the oracle board at the roof lock is recorded batch iid1
//      (amt 6, x 6) — a board observation, the one axiom, everything else is arithmetic.

datatype Origin = PreExisted | ArrivedLater | Undetermined
datatype Batch = Batch(confirm: int)

// documented garbagespeed. Measured 2026-08-15 (`bun drift-speed-sweep.mjs`'s per-session table, six
// sessions): the verified-prefix sweep's outright peak in 4 of 6 sessions (07-22, 07-24, 07-28,
// 08-14) and TIED for peak in the other 2 (2026-08-01 ties speed 18 at 2793 locks each; 2026-08-09
// ties speed 22 at 2740 locks each) — a reversal of this file's original (2026-08-11, five-session)
// claim that 20 was the sweep peak in all five, which drift-speed-sweep.mjs's own history shows was
// NOT true when written (the sweep then peaked at ~28, never 20); later sim fixes
// (documented-garbagespeed default, the garbage-cancel protocol port, locktime 60->30) are what made
// it true. See drift-speed-sweep.mjs.
const SPEED: int := 20

function InsertLB(b: Batch): int { b.confirm + SPEED }   // earliest possible insertion frame

// A real insertion frame lands in the roof->T window.
predicate InWindow(insert: int, rf: int, tf: int) { rf < insert <= tf }

// verdict as a function of the two ground-truth predicates
function Verdict(garbagePresentAtRoof: bool, straddles: bool): Origin {
  if !garbagePresentAtRoof then ArrivedLater
  else if straddles then Undetermined
  else PreExisted
}

// SOUND soundness lemma (the one Dafny accepts): a batch whose insertion LOWER BOUND already exceeds tf
// cannot insert inside (rf, tf], because the next-lock gate only ever DELAYS (real insertion >= LB).
// This is the only sound direction — the converse ("LB <= rf => no straddle") is FALSE (the gate can
// push a pre-roof-LB batch into the window), and Dafny rejected it, which is why iid1 below leans on a
// board OBSERVATION instead of on its LB.
lemma LBAfterWindow_NoStraddle(b: Batch, rf: int, tf: int, realInsert: int)
  requires realInsert >= InsertLB(b)     // gate only delays
  requires InsertLB(b) > tf
  ensures !InWindow(realInsert, rf, tf)
{ }

// ── Candidate A: 2026-07-28-2 r3 pinglamb, T lock 15 — roof 644, T 765 ───────────────────────────────
// UNINSTANTIATED (2026-08-16). The arithmetic below is sound and Dafny still checks it; what is
// withdrawn is the reading that 644 is candidate A's roof frame. 644 is lock 12's frame, and lock 12
// is not A's roof — it is a T, and the roof cell r31c6 is drawn Z. A's roof is lock 8, frame 269, and
// at lock 8 the availability is already 2, so A is `reactive` and never reaches clause 2 at all.
// Kept, not deleted, because the SHAPE it proves — present-at-roof plus no straddle implies
// PreExisted — is what `floorOrigin`'s garbage branch does and is still the thing being modelled.
// It is no longer called by the headline lemma, and it must not be re-instantiated with these
// constants: the observation in its `requires` was made about the wrong lock.
//
// Two batches bracket the window. iid1 (confirm 536): the 6-row hole-col-6 block OBSERVED on the oracle
// board at the roof lock 12; lock 12 CLEARS, so garbage cannot insert on it => iid1 inserted strictly
// BEFORE frame 644 => a1 <= 644, not in (644,765]. iid2 (confirm 1136): LB 1156 > 765 => never in window.
lemma CandidateA_PreExisted(a1: int, a2: int)
  requires a1 <= 644                              // OBSERVATION: iid1 present at the roof (before the window)
  requires a2 >= InsertLB(Batch(1136))            // iid2 real insertion is at least its LB
  ensures !InWindow(a1, 644, 765)                 // iid1 does not straddle
  ensures !InWindow(a2, 644, 765)                 // iid2 does not straddle
  ensures Verdict(true, false) == PreExisted      // present-at-roof && no straddle => PreExisted
{
  assert InsertLB(Batch(1136)) == 1156;
  LBAfterWindow_NoStraddle(Batch(1136), 644, 765, a2);
}

// ── Candidate B: 2026-07-28-6 r5 pinglamb, T lock 32 (old "survivor") — roof 996, T 1827 ─────────────
// A batch confirms at 1718 -> LB 1738. Its real insertion is >= 1738, and Triangle in fact inserts it at
// 1750 — inside (996,1827]. A straddle is REAL here, so the verdict is Undetermined, never PreExisted.
lemma CandidateB_NotPreExisted(a: int)
  requires a >= InsertLB(Batch(1718))
  requires a <= 1827                              // observed: it inserts before the T (Triangle @ 1750)
  ensures InWindow(a, 996, 1827)                  // a real straddle
  ensures Verdict(true, true) != PreExisted
{
  assert InsertLB(Batch(1718)) == 1738;
  assert 996 < 1738 <= a;                         // a >= 1738 > 996, and a <= 1827
}

// ── Candidate C: 2026-07-28-3 r5 yachi, T lock 25 — support is a PLACER at lock 11, roof lock 6 ──────
// A support piece whose lock index exceeds the roof's postdates the roof: ArrivedLater, garbage aside.
// The FUNCTION is the model of that rule and stands. `CandidateC_ArrivedLater` below is
// UNINSTANTIATED (2026-08-16) for the same reason as A: (11, 6) are `oracle-forecast.mjs`'s numbers,
// and its roof lock 6 is an I while the roof cell r23c7 is drawn L. Under `oracle-source.ts` the roof
// is lock 16 (an L) and the support is lock 6, i.e. the pair is (6, 16) — the opposite ORDER, so the
// rule would return PreExisted on the real numbers. It returns nothing at all in practice: with the
// roof at 16 the availability is 1 -> 1, so C is `reactive` and clause 2 is never asked.
function PlacerVerdict(supportLock: int, roofLock: int): Origin {
  if supportLock > roofLock then ArrivedLater else PreExisted
}
lemma CandidateC_ArrivedLater()
  ensures PlacerVerdict(11, 6) == ArrivedLater
{ assert 11 > 6; }

// ── PLACER ADMISSIBILITY — the test that withdrew A, C and D, and needs no frames at all ───────────
//
// A provenance index is a claim about WHICH LOCK put a cell where it is. The cell also carries the
// piece letter the board draws. Those two are the same fact stated twice, so they must agree — and
// this is decidable from one board snapshot, with no second engine, no frames and no replay. It is
// the cheapest check in the whole forecast chain and it was never run until 2026-08-16.
datatype Piece = I | J | L | O | S | T | Z

predicate AdmissiblePlacer(drawn: Piece, placer: Piece) { drawn == placer }

// An inadmissible placer does not merely make the roof index wrong; it makes every quantity DERIVED
// from that index — the roof frame, `availAtRoof`, the (support, roof) pair — a value read off a
// different lock. So the clause-2 machinery above cannot be instantiated with it.
lemma RoofProvenanceInadmissible_A() ensures !AdmissiblePlacer(Z, T) { }   // r31c6 is Z; lock 12 is T
lemma RoofProvenanceInadmissible_C() ensures !AdmissiblePlacer(L, I) { }   // r23c7 is L; lock  6 is I
lemma RoofProvenanceInadmissible_D() ensures !AdmissiblePlacer(S, T) { }   // r30c3 is S; lock 12 is T
lemma RoofProvenanceAdmissible_B()  ensures  AdmissiblePlacer(L, L) { }    // r33c3 is L; lock 19 is L

// ── Headline: of candidates A/B/C/D, NONE is clause-2 PreExisted ──────────────────────────────────
//
// Renamed from `ExactlyOnePreExistedAmongABC` on 2026-08-16, because withdrawing A leaves no
// PreExisted disjunct and a lemma named for one would be the overstatement this file exists to stop.
// It is NOT renamed back to an unscoped `ExactlyOnePreExisted`: the scoping the previous session
// added was right, and what changed is the count, not the scope.
//
// What survives is B, whose roof lock is identical under both board sources, plus the reason A, C
// and D are not here — their roof provenance is inadmissible, so no clause-2 verdict was ever
// established for them. `Verdict(true, false) == PreExisted` is still a true statement about the
// MODEL and is retained in `NonVacuous` below; what is withdrawn is any claim that a candidate in
// this corpus instantiates it.
lemma NonePreExistedAmongABCD()
  ensures Verdict(true, true) != PreExisted     // B: survivor, a real straddle => undetermined
  ensures !AdmissiblePlacer(Z, T)               // A: roof provenance inadmissible, verdict withdrawn
  ensures !AdmissiblePlacer(L, I)               // C: likewise
  ensures !AdmissiblePlacer(S, T)               // D: likewise
  ensures  AdmissiblePlacer(L, L)               // ...and B's is not, which is why B alone survives
{
  CandidateB_NotPreExisted(1750);
  RoofProvenanceInadmissible_A();
  RoofProvenanceInadmissible_C();
  RoofProvenanceInadmissible_D();
  RoofProvenanceAdmissible_B();
}

// ── NON-VACUITY: the window predicate is genuinely two-valued, and the Verdict branches differ on a
// real input difference — none of this collapses to a constant. ─────────────────────────────────────
lemma NonVacuous()
  ensures InWindow(720, 644, 765)                       // a batch confirming @700 (LB 720) WOULD straddle
  ensures !InWindow(1156, 644, 765)                     // a batch with LB 1156 provably does not
  ensures Verdict(true, true) == Undetermined && Verdict(true, false) == PreExisted  // branches differ
  ensures Verdict(false, false) == ArrivedLater         // the "no garbage at roof" branch is live too
  // ...and the admissibility test is two-valued rather than a constant `false` dressed up as a
  // finding. Three of this corpus's four candidates fail it and one passes; a predicate that failed
  // on everything would have withdrawn B too, which would have been the tell that it was broken.
  ensures !AdmissiblePlacer(S, T) && AdmissiblePlacer(L, L)
{ }
