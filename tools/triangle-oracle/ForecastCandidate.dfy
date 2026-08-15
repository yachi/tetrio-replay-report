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
// These three were all `oracle-forecast.mjs` finds over the five-session corpus it was written against
// (2026-08-11). Re-running that scan on 2026-08-15's six-session corpus (`bun oracle-forecast.mjs`)
// finds a FOURTH full-round forecast_lineclear candidate: 2026-08-14 yachi 2026-08-14-10 r2 lock19.
// It has NO lemma below — the ground-truth frame-ordering resolution this file does for A/B/C has not
// been run against it, so its clause-2 verdict is UNPROVEN. Do not read "the three candidates" as
// exhaustive over the current corpus.
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
function PlacerVerdict(supportLock: int, roofLock: int): Origin {
  if supportLock > roofLock then ArrivedLater else PreExisted
}
lemma CandidateC_ArrivedLater()
  ensures PlacerVerdict(11, 6) == ArrivedLater
{ assert 11 > 6; }

// ── Headline: of candidates A/B/C, exactly ONE is clause-2 PreExisted, decided by recorded frames
// alone. This ranges over A/B/C ONLY — the three the ground-truth frame-ordering resolution above was
// run against. A fourth full-round forecast_lineclear candidate (2026-08-14 yachi 2026-08-14-10 r2
// lock19, noted above) is NOT covered: its clause-2 verdict is UNPROVEN, so it is neither asserted
// PreExisted nor asserted otherwise here. Do not read this lemma as ranging over the full corpus.
lemma ExactlyOnePreExistedAmongABC()
  ensures Verdict(true, false) == PreExisted    // A: the real forecast (no straddle, present at roof)
  ensures Verdict(true, true)  != PreExisted    // B: survivor, a real straddle => undetermined
  ensures PlacerVerdict(11, 6) != PreExisted    // C: arrived-later (placer support postdates the roof)
{
  CandidateA_PreExisted(644, 1156);
  CandidateB_NotPreExisted(1750);
  CandidateC_ArrivedLater();
}

// ── NON-VACUITY: the window predicate is genuinely two-valued, and the Verdict branches differ on a
// real input difference — none of this collapses to a constant. ─────────────────────────────────────
lemma NonVacuous()
  ensures InWindow(720, 644, 765)                       // a batch confirming @700 (LB 720) WOULD straddle A
  ensures !InWindow(1156, 644, 765)                     // iid2 (LB 1156) provably does not
  ensures Verdict(true, true) == Undetermined && Verdict(true, false) == PreExisted  // branches differ
  ensures Verdict(false, false) == ArrivedLater         // the "no garbage at roof" branch is live too
{ }
