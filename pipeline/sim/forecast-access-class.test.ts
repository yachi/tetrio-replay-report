/**
 * The step model's `access` mechanism, measured from the boards and pinned by name over the whole
 * corpus. THIS FILE IS NOW A REGRESSION GUARD ON THAT BRANCH. It was written as a report of a gap,
 * and its own header said a repair that landed a fifth `Mechanism` SHOULD break it; the repair
 * landed on 2026-08-16 and the break is recorded below in `ACCESS_CLASS`'s two verdicts.
 *
 * `localiseMechanism` decomposes a step into place -> clear -> insert-garbage and asks which of
 * those edits FORMED the slot the T executed into. Its test for the clear is geometric — "a cleared
 * row outside the slot's own rows displaces the slot rigidly and cannot have formed it". That is
 * sound about formation and silent about ACCESS: `bestTspin` is a BFS from spawn, so availability is
 * REACHABILITY, and a clear also raises it by removing an obstruction ABOVE a slot that already
 * exists, cell for cell, and was merely unreachable.
 *
 * ── WHAT THE MODEL USED TO ANSWER, AND WHY IT MATTERED (history — the reason this file exists) ────
 * Before `access`, the model had nowhere to put that, so the verdict turned on an irrelevance —
 * whether the causing piece happened to sit next to the slot:
 *
 *   piece does NOT touch  ->  `unattributed`   honest, and counted in the artefact
 *   piece DOES touch      ->  `placement`      confidently wrong, and counted NOWHERE
 *
 * The second row is the one that reached a reader: 2026-08-09's published report said
 * 「玩家自己落嗰隻棋整出嚟」 — the player's own piece made that slot — of a slot the Z at lock 20
 * provably did not make. `self_built`'s gloss was simply false for it.
 *
 * AND THE COUNTER COULD ONLY EVER SEE HALF THE CLASS, which is why the fix could never have been a
 * tighter pin on `unattributed`. The artefact's `unattributed` counter is pinned in
 * forecast-facts.test.ts; a third event arriving as `placement` would have passed that guard in
 * silence — the same defect one level down, guarding the half that was already honest. This file
 * detects the CLASS from the boards, so it sees both halves and pins every member. That is the
 * point the deleted `step-model-gap.ts` carried, and it lives here now because the class lives here.
 *
 * DETECTION. For each record whose mechanism was localised to a step t > j, re-derive that step's
 * three edits and ask a counterfactual the model never asks:
 *
 *   clearAlone  = bestTspinLines(A minus the cleared rows) >= target
 *                 — the SAME rows deleted from A with the piece never placed. If this reaches the
 *                 target, the clear sufficed on its own, whether or not it formed anything.
 *   pieceAlone  = bestTspinLines(Bpre) >= target
 *                 — mirrors the engine's own branch order, which tests Bpre before it tests B.
 *
 * NOTHING ELSE IS RECOMPUTED. Whether the clear FORMED the slot is read off `rec.mechanism`, not
 * re-derived: an earlier draft reimplemented the strictly-inside geometry, and mutation testing
 * showed the copy was untestable here — widening `min < cr < max` to `<=` changed no result,
 * because no cleared row in this corpus sits on a slot boundary. A replica cannot disagree with an
 * engine it never calls (the `bfs-cap.ts` lesson), so the replica is gone and only the two
 * counterfactuals remain, both of which mutants do kill.
 *
 * The 13 candidates decompose, and the middle row is the one an earlier draft of this file got wrong
 * by folding it into "formed":
 *
 *   7  formed          the engine says `line-clear` — a cleared row IS strictly inside the slot
 *   2  overdetermined  the PIECE alone also sufficed (Bpre >= target) -> engine says `placement`
 *   4  ACCESS          neither — the clear only removed the lid       -> engine says `access`
 *
 * Overdetermined is not a defect: when the placement on its own reaches the target, crediting it is
 * defensible even though the clear would have done too.
 *
 * THE COUNTS WERE UNCHANGED BY THE 2026-08-16 REPAIR — only the last row's verdict moved, from
 * `unattributed`/`placement` to `access`. That is what says the branch went in at the right place:
 * placed before the strictly-inside test the same counterfactual takes all of them and `formed`
 * collapses to 0 (planted and killed — see MUTATION STATUS); placed after `touches` it takes 1 and
 * leaves the confidently-wrong half exactly as it was.
 *
 * THEY DID MOVE WHEN 2026-08-19 ARRIVED, and that is this file working as designed rather than a
 * regression: 9 -> 13 candidates, splitting 2 more `formed` and 2 more ACCESS, with
 * `overdetermined` and `pieceBlocked` unmoved. The class's share of the candidates is flat
 * (2/9 -> 4/13), so a seventh session did not expose a detector that had been mis-firing — the
 * class simply keeps arriving. Both new members were verified by re-deriving the counterfactuals
 * and their controls, not by trusting the engine; the working is beside them in `ACCESS_CLASS`.
 *
 * WHAT THIS FILE DOES NOT COVER: whether `localiseMechanism`'s inside test should be strict or
 * inclusive. No cleared row in this corpus sits on a slot boundary, so the corpus cannot answer it;
 * that is fixture territory (forecast.test.ts), not corpus territory. Said out loud so a green run
 * here is not mistaken for evidence about it.
 *
 * NAMED, NOT BOUNDED — the `DT_ORDER_IN_OPENER` and `CAVE_IN_OPENER_EXCEPTIONS` precedents
 * (pipeline/openers/openers.test.ts) and `check_loo.py`'s ANNOTATED. An inequality would be
 * satisfied by any four such events anywhere; this names these four, so a fifth has to be
 * investigated instead of absorbed, and any of them disappearing or changing verdict fails just as
 * loudly. That is not hypothetical: 2026-08-19 arrived with two new members and failed here rather
 * than passing a bound, which is the entire reason the class is pinned by name.
 *
 * MUTATION STATUS, because "a guard no mutant can kill is decorative" applies to this file too.
 * RE-MEASURED 2026-08-16 against the repaired engine — the previous header claimed 13/10 and three
 * survivors, and that claim was about a file whose ACCESS_CLASS held different verdicts, so it was
 * carried forward rather than re-run. **20 planted, 16 killed, 4 survive.** Every previously-killed
 * mutant is still killed; nothing regressed from killed to surviving.
 *
 * PARTIALLY RE-MEASURED 2026-08-19, when the class grew from two members to four. The 20-mutant
 * figure above is NOT re-stated as covering this file, for precisely the reason the paragraph above
 * records: ACCESS_CLASS changed, so a count measured against the old list is a claim about a
 * different file. What WAS re-run are the five mutants that bear on what changed, all killed:
 * a new entry removed, a new entry's verdict flipped to `placement`, a new entry's lock drifted by
 * one, the list padded with an invented fifth member, and `formed` reverted to its old 5. The
 * remaining fifteen — the counterfactual branches and the engine-branch mutants — were not re-run;
 * they exercise code this change did not touch, and saying so is cheaper than implying coverage
 * that was not measured.
 *
 * Killed (16): both ACCESS_CLASS entries removed, reclassified and drifted separately (6), the list
 * padded with an invented third (1), and every counterfactual branch — clearAlone disabled,
 * clearAlone asked of B instead of A, Bpre dropped, Bpre always taken, the engine-verdict test
 * inverted, and never firing (6). Plus three aimed at the branch this file now guards:
 *
 *   the `access` return DELETED from `localiseMechanism`  — the class reappears exactly as the two
 *                                        rows above predict, `placement/self_built` and
 *                                        `unattributed/self_built`, and BOTH the entry list and the
 *                                        cross-check fail. This is the mutant that makes this file
 *                                        a regression guard rather than a report.
 *   the `access` branch moved BEFORE the strictly-inside test — `formed` 5 -> 0, i.e. it eats the
 *                                        published `forecast_lineclear` numerator. Kills on the
 *                                        decomposition, which is what that test is for.
 *   the two above combined with the widened cross-check (see the survivor) — still killed, but by
 *                                        the entry list ALONE.
 *
 * Four survive. Three are the artefact the previous header named — an assertion that a SET IS EMPTY
 * cannot be killed by disabling whatever would fill it, when on this corpus nothing does:
 *
 *   `pieceBlocked` branch deleted        — no record takes that branch here, so deleting it and
 *                                          asserting 0 are indistinguishable. It guards a case that
 *                                          does not occur yet, the same way forecast.ts's null-slot
 *                                          return is kept "for the type, not the value".
 *   cross-check collector neutered       — `disagreements` is empty, so removing the recorder and
 *   cross-check predicate forced true    — recording nothing look alike.
 *
 * The fourth is new, and it is an honest correction to the reasoning that tightened `check`:
 *
 *   check's ACCESS branch widened back to `access || placement || unattributed`
 *                                        — SURVIVES on this corpus, because the engine says
 *                                          `access` and the disjunction accepts that too. The
 *                                          tightening does buy something — combined with the
 *                                          deleted-branch mutant it is the difference between two
 *                                          tests failing and one — but the kill is carried by
 *                                          ACCESS_CLASS's verdicts either way. So the tightening is
 *                                          correctness, not coverage, and must not be described as
 *                                          the thing that catches a deleted branch.
 *
 * The cross-check is NOT decorative, and that was checked rather than assumed: mutating the replica
 * itself (`Bpre branch always taken`) fails three tests including `the replica can disagree with
 * the engine, and does not`, and so does deleting the engine's `access` return. It fires on the
 * thing it guards — drift between the counterfactuals and `localiseMechanism` — just not on its own
 * deletion.
 *
 * Cost: ~13s, because it replays every case in every session through the oracle. That is the same
 * work forecast-corpus.test.ts does for one session, and the class cannot be measured any other
 * way — the committed artefacts carry counts, not boards.
 */
import { test, expect } from 'bun:test';
import { readdirSync, existsSync } from 'node:fs';
import { bestTspinLines, forecastMetric } from './forecast.ts';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import type { Board } from './vendor/core/srs.ts';

const H = 40;
const SESSIONS_DIR = `${import.meta.dir}/../../sessions`;
// Discovered, never listed. A hardcoded session list is the failure recorded in
// `new-session-checklist`: the newest session is exactly the one a stale list omits, and every
// member of this class has arrived in one of the three most recent sessions — 2026-08-19 alone
// brought two. A list would have hidden them by construction.
const SESSIONS = readdirSync(SESSIONS_DIR)
  .filter(s => existsSync(`${SESSIONS_DIR}/${s}`)
    && readdirSync(`${SESSIONS_DIR}/${s}`).some(f => f.endsWith('.ttrm')))
  .sort();

type Member = {
  session: string; file: string; round: number; user: string;
  lock: number; step: number; mechanism: string; kind: string;
};

/**
 * The four events this corpus contains, with the verdict each receives. The verdict is part of the
 * pin on purpose: it is what turned this file from a report of a gap into a regression guard on the
 * branch that closed it. The first two read `unattributed`/`self_built` and `placement`/`self_built`
 * until 2026-08-16 — the two ways the model used to answer, recorded in the history above — and are
 * the two halves of the class, which is why they are kept in that order. The last two arrived with
 * 2026-08-19 and were `access` from the moment they were first measured, the branch having landed
 * three days earlier.
 */
const ACCESS_CLASS: Member[] = [
  // A T-spin Single at lock 70 cleared row 33 — `LLLIIII.ZZ`, one open column. The slot is at rows
  // 35-37 and rows 34-39 are bit-identical in A = boards[69] and in B, so nothing was formed:
  // deleting row 33 from A ALONE yields the same 2-line slot [36,36,36,37,35] (best 1 -> 2), where
  // deleting rows 31/32/34 instead gives 0/0/1. The clear removed the lid. The T's own cells sit at
  // B-row 33, outside the slot's 35-37 and its +/-1 margin, so `touches` is false — which is why
  // this half used to fall all the way through to `unattributed`.
  { session: '2026-08-14', file: 'replay-2026-08-14-0.ttrm', round: 4, user: 'yachi',
    lock: 74, step: 70, mechanism: 'access', kind: 'path_opened' },
  // The half that was dangerous. The causing piece is a Z (`spin: 'none'`) at rows 21-23 that cleared
  // row 23; the slot is at rows 24-26 and rows 24-39 are bit-identical either side, so again nothing
  // was formed — A minus row 23 alone gives best 0 -> 2, controls on rows 21/22/24 give 0/0/0. The Z
  // used to be credited anyway, because one of its cells lands at B-row 23, which is slot row 24
  // minus one, and `touches` accepts adjacency. The `access` branch is tested BEFORE `touches`, so
  // the adjacency no longer decides it.
  { session: '2026-08-09', file: 'replay-2026-08-09-6.ttrm', round: 7, user: 'pinglamb',
    lock: 24, step: 20, mechanism: 'access', kind: 'path_opened' },
  // ── 2026-08-19 added TWO, which is the event this file was built to catch ──────────────────────
  // Both are the same shape as the two above and were verified the same way, by re-deriving the
  // counterfactuals rather than by trusting the engine's own verdict:
  //
  //            causing piece   cleared   A    A-cleared   Bpre   target   controls (other rows)
  //   r4/l23   L, spin none    row 35    0    2           0      2        32/33/34/36/37 -> all 0
  //   r6/l32   L, spin none    row 36    0    2           1      2        33/34/35/37/38 -> all 0
  //
  // Read the control column first: deleting ANY other single row gives 0, so what raised
  // availability is that row and not the act of deleting a row — the artefact a bare `clearAlone`
  // could not rule out. And the slot PRE-EXISTED cell for cell: every row below the cleared row is
  // occupancy-identical in A and in B (4 of 4, and 3 of 3), so nothing down there was formed. The
  // clear removed the lid, exactly as for the two above.
  //
  // r6 is the more interesting of the pair and is why `overdetermined` is tested by `>= target` and
  // never by `> 0`: its placement alone reaches 1, so the piece did contribute — just not enough.
  // A rule that credited any non-zero contribution to the placement would have swallowed it.
  //
  // NOTED, NOT EXPLAINED: both are yachi, in the same replay file, two rounds apart, both an L with
  // `spin: 'none'` clearing exactly one row against target 2. Four events is still too few to call
  // that anything, and naming a mechanism for it here is how a coincidence becomes a finding.
  { session: '2026-08-19', file: 'replay-2026-08-19-5.ttrm', round: 4, user: 'yachi',
    lock: 23, step: 22, mechanism: 'access', kind: 'path_opened' },
  { session: '2026-08-19', file: 'replay-2026-08-19-5.ttrm', round: 6, user: 'yachi',
    lock: 32, step: 24, mechanism: 'access', kind: 'path_opened' },
];

const key = (m: Member) =>
  `${m.session} ${m.file} r${m.round} ${m.user} lock=${m.lock} step=${m.step} ${m.mechanism}/${m.kind}`;

/** `board` with those rows deleted and the stack shifted down — the same edit `localiseMechanism` makes. */
function withoutRows(board: Board, rows: number[]): Board {
  const out = board.map(r => [...r]) as Board;
  for (const r of [...rows].reverse()) out.splice(r, 1);
  for (let i = 0; i < rows.length; i++) out.unshift(Array(10).fill(null) as never);
  return out;
}

function sweep() {
  const access: Member[] = [];
  const beyondPrefix: Member[] = [];
  const disagreements: string[] = [];
  let localised = 0, clearAlone = 0, formed = 0, overdetermined = 0, pieceBlocked = 0;
  // The two branches this file decides for itself each predict what the engine must already have
  // concluded. Recorded rather than asserted inline, so one drift does not mask the rest of the
  // sweep. This is the only place the counterfactuals and `localiseMechanism` can contradict.
  //
  // `ACCESS` used to be checked as `placement || unattributed` — a disjunction, because before the
  // repair the engine's answer really was either of those depending on `touches`, an irrelevance.
  // It is `access` exactly now: a cross-check that still accepted the two verdicts the repair exists
  // to remove would be strictly weaker than the engine it checks. Measured, not assumed — widening
  // it back SURVIVES the mutation sweep on this corpus, and deleting the engine's `access` branch
  // under the widened version still fails, on ACCESS_CLASS rather than here. So this line is about
  // saying the right thing, not about being the thing that catches a deletion; see MUTATION STATUS.
  const check = (predicted: string, rec: { mechanism?: string }, where: string) => {
    const ok = predicted === 'ACCESS' ? rec.mechanism === 'access' : predicted === rec.mechanism;
    if (!ok) disagreements.push(`${where}: replica says ${predicted}, engine says ${rec.mechanism}`);
  };

  for (const session of SESSIONS) {
    for (const c of loadCases(`${SESSIONS_DIR}/${session}`)) {
      const r = runCaseOracle(c);
      const v = verifiedIndex(r, c.truth);
      if (v < 0) continue;
      for (const rec of forecastMetric(r, true).records) {
        if (rec.mechanismStep === undefined || rec.mechanism === undefined) continue;
        const t = rec.mechanismStep, j = rec.roofFrom ?? -1, target = rec.availAtSpin;
        if (rec.lockIndex <= v) localised++;
        // the walk halted on the roof; there is no causing step to decompose
        if (t <= j) continue;

        const A = r.boards[t - 1]!, lk = r.locks[t]!;
        const Bpre = A.map(row => [...row]) as Board;
        for (const cc of lk.cells) if (cc.row >= 0 && cc.row < H) Bpre[cc.row]![cc.col] = lk.piece as never;
        const cleared = Bpre.map((row, i) => row.every(x => x !== null) ? i : -1).filter(i => i >= 0);
        if (!cleared.length) continue;                       // nothing was cleared at this step

        // Did the clear alone suffice? This is the whole question the model never asks.
        if (bestTspinLines(withoutRows(A, cleared)) < target) continue;
        if (rec.lockIndex <= v) clearAlone++;
        const where = `${session} ${c.file} r${c.round} ${c.user} lock=${rec.lockIndex} step=${t}`;

        // Branch order is the ENGINE's, not a convenient one: `localiseMechanism` tests Bpre before
        // it tests B, so a step where the placement alone already reached the target never reaches
        // the clear's geometry at all. Those are overdetermined, not misattributed — the clear would
        // also have done it, and crediting the piece is defensible.
        if (bestTspinLines(Bpre) >= target) {
          check('placement', rec, where);
          if (rec.lockIndex <= v) overdetermined++;
          continue;
        }

        if (bestTspinLines(withoutRows(Bpre, cleared)) < target) {
          // The clear alone reaches the target but the placement takes it away again. Not seen in
          // this corpus; counted rather than dropped, so it cannot start happening in silence.
          if (rec.lockIndex <= v) pieceBlocked++;
          continue;
        }

        // "Did the clear FORM the slot" is ASKED OF THE ENGINE, not re-derived here. An earlier
        // draft reimplemented `localiseMechanism`'s strictly-inside geometry, and two mutants
        // proved that a mistake: widening `min < cr < max` to `<=` changed nothing (this corpus has
        // no cleared row on a slot boundary, so the duplicate was untestable), and neutering the
        // replica/engine cross-check changed nothing either. A copy of the engine's geometry cannot
        // disagree with it in a way this corpus can see — the `bfs-cap.ts` lesson. So the only
        // things computed here are the two COUNTERFACTUALS the engine never asks (clearAlone above,
        // Bpre here), and the verdict itself comes from `rec.mechanism`.
        if (rec.mechanism === 'line-clear') { if (rec.lockIndex <= v) formed++; continue; }
        check('ACCESS', rec, where);

        const m: Member = { session, file: c.file, round: c.round, user: c.user,
          lock: rec.lockIndex, step: t, mechanism: rec.mechanism, kind: rec.kind };
        (rec.lockIndex <= v ? access : beyondPrefix).push(m);
      }
    }
  }
  return { access, beyondPrefix, disagreements, localised, clearAlone, formed,
           overdetermined, pieceBlocked };
}

const result = sweep();

test('the access class is exactly the four named events, and the engine calls each `access`', () => {
  // Sorted and compared as a SET of keys: an added member, a removed member, a member that moved
  // round or lock, and a member whose verdict changed all fail here. `toEqual` on the strings keeps
  // the failure readable, which matters because the reason lives beside each entry in ACCESS_CLASS.
  expect(result.access.map(key).sort()).toEqual(ACCESS_CLASS.map(key).sort());
  // ...and the list may not be padded with entries the sweep never produced, which is the
  // reciprocal `check_loo.py` keeps for ANNOTATED: an exception satisfied by nothing is stale.
  expect(ACCESS_CLASS.length).toBe(result.access.length);
});

test('the class does not exist beyond the verified prefixes either', () => {
  // If it did, "2 events" would be an artefact of how far the simulator is verified rather than a
  // property of the play, and the count could grow with nothing about the model having changed.
  expect(result.beyondPrefix.map(key)).toEqual([]);
});

test('the 13 candidates decompose 7 formed / 2 overdetermined / 4 access, and nothing else', () => {
  // The numbers that make this a finding rather than a curiosity. 13 records corpus-wide are ones
  // the clear ALONE explains; 7 the model credits to the clear because a cleared row lies strictly
  // inside the slot, 2 more are overdetermined (the placement alone also sufficed, so `placement` is
  // a defensible verdict and the engine tests it first), and 4 are the access class. A detector that
  // fired on everything, or on nothing, would look identical in `access` alone — these are its
  // denominator, its true positives and the branch that pre-empts them.
  //
  // 2026-08-19 MOVED ALL OF THESE, and how it moved them is the reassuring part: +4 candidates
  // splitting 2 formed and 2 access, with `overdetermined` and `pieceBlocked` unchanged. The
  // proportion in the access class is essentially flat (2/9 -> 4/13), so the seventh session did not
  // reveal a detector that had been quietly mis-firing — it added members to a class that keeps
  // arriving at roughly the rate it always has. Before this session the decomposition read
  // 5 / 2 / 2 out of 9, and it had been stable across the 2026-08-16 repair.
  //
  // This is also where the branch ORDER is pinned. Placed before the strictly-inside test the same
  // counterfactual reclassifies all 9, i.e. the published numerator; placed after `touches` it
  // reclassifies 1 and leaves the confidently-wrong half alone. `formed` staying 5 is what says the
  // branch went in between.
  expect(result.clearAlone).toBe(13);
  expect(result.formed).toBe(7);
  expect(result.overdetermined).toBe(2);
  expect(result.formed + result.overdetermined + result.pieceBlocked + result.access.length)
    .toBe(result.clearAlone);
  // Not seen in this corpus, and it must not start silently: the clear suffices, then the piece
  // takes the slot back away. It is a real possibility, not an impossible one.
  expect(result.pieceBlocked).toBe(0);
});

test('the replica can disagree with the engine, and does not', () => {
  // What stops this file being a second implementation that agrees by construction. Each branch
  // above predicts the verdict `localiseMechanism` must already have reached; a drift between the
  // two shows up here rather than silently changing which events land in ACCESS_CLASS. This is the
  // check `bfs-cap.ts` did not have when it printed the same 688 before and after a real change.
  expect(result.disagreements).toEqual([]);
  // and the check must have actually run — over the 13 candidates, not over an empty set
  expect(result.clearAlone).toBeGreaterThan(0);
});

test('the sweep reached the corpus it claims to have swept', () => {
  // Exposure. Every assertion above is over a set that an early `continue` could empty, and an
  // empty set compares equal to an empty expectation — the shape this repo calls a gate that
  // proves nothing while reporting ok. These are REGRESSION PINS in the sense
  // forecast-corpus.test.ts means it: produced by this code, not by an outside oracle.
  // SESSIONS is read off disk (readdirSync above), never listed, so this compares a discovered
  // count against a pin rather than one literal against another — a session arriving fails here,
  // which is the whole job. `localised` is the second half: discovery finding 7 directories says
  // nothing about the sweep having replayed them.
  expect(SESSIONS.length).toBe(7);
  expect(result.localised).toBe(2138);
});
