/**
 * The step model's fourth mechanism, pinned by name over the whole corpus.
 *
 * `localiseMechanism` decomposes a step into place -> clear -> insert-garbage and asks which of
 * those edits FORMED the slot the T executed into. Its test for the clear is geometric and stated
 * at forecast.ts:494 — "a cleared row outside the slot's own rows displaces the slot rigidly and
 * cannot have formed it". That is sound about formation and silent about ACCESS: `bestTspin` is a
 * BFS from spawn, so availability is REACHABILITY, and a clear also raises it by removing an
 * obstruction ABOVE a slot that already exists, cell for cell, and was merely unreachable.
 *
 * The model has nowhere to put that, so it lands in one of two places depending on an irrelevance
 * — whether the causing piece happens to sit next to the slot:
 *
 *   piece does NOT touch  ->  `unattributed`   honest, and counted in the artefact
 *   piece DOES touch      ->  `placement`      confidently wrong, and counted NOWHERE
 *
 * WHICH IS WHY THIS FILE EXISTS AND WHY IT DOES NOT KEY ON `unattributed`. The artefact's
 * `unattributed` counter is pinned in forecast-facts.test.ts, but it can only ever see the honest
 * half. A third event of this class arriving as `placement` would pass that guard in silence — the
 * same defect one level down. This detects the CLASS from the boards and pins every member.
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
 * The 9 candidates decompose, and the middle row is the one an earlier draft of this file got wrong
 * by folding it into "formed":
 *
 *   5  formed          the engine says `line-clear` — a cleared row IS strictly inside the slot  OK
 *   2  overdetermined  the PIECE alone also sufficed (Bpre >= target) -> engine says `placement`  OK
 *   2  ACCESS          neither — the clear only removed the lid       -> `unattributed`/`placement` GAP
 *
 * Overdetermined is not a defect: when the placement on its own reaches the target, crediting it is
 * defensible even though the clear would have done too. Only the last row is the model gap.
 *
 * WHAT THIS FILE DOES NOT COVER: whether `localiseMechanism`'s inside test should be strict or
 * inclusive. No cleared row in this corpus sits on a slot boundary, so the corpus cannot answer it;
 * that is fixture territory (forecast.test.ts), not corpus territory. Said out loud so a green run
 * here is not mistaken for evidence about it.
 *
 * NAMED, NOT BOUNDED — the `DT_ORDER_IN_OPENER` precedent (pipeline/openers/openers.test.ts) and
 * `check_loo.py`'s ANNOTATED. An inequality would be satisfied by any two such events anywhere;
 * this names these two, so a third has to be investigated instead of absorbed, and either of them
 * disappearing or changing verdict fails just as loudly. A repair that lands a fifth `Mechanism`
 * SHOULD break this test — that is the point, and the list is where the repair gets recorded.
 *
 * MUTATION STATUS, because "a guard no mutant can kill is decorative" applies to this file too.
 * 13 mutants planted, 10 killed — every entry in ACCESS_CLASS (removed, reclassified, drifted,
 * padded) and every counterfactual branch (clearAlone disabled, clearAlone asked of B instead of A,
 * Bpre dropped, Bpre always taken, the engine-verdict test inverted, and never firing).
 *
 * Three survive, and all three are the same artefact — an assertion that a SET IS EMPTY cannot be
 * killed by disabling whatever would fill it, when on this corpus nothing does:
 *
 *   `pieceBlocked` branch deleted        — no record takes that branch here, so deleting it and
 *                                          asserting 0 are indistinguishable. It guards a case that
 *                                          does not occur yet, the same way forecast.ts:571's
 *                                          null-slot return is kept "for the type, not the value".
 *   cross-check collector neutered       — `disagreements` is empty, so removing the recorder and
 *   cross-check predicate forced true    — recording nothing look alike.
 *
 * The cross-check is NOT decorative, and that was checked rather than assumed: mutating the replica
 * itself (`Bpre branch always taken`) fails three tests including `the replica can disagree with
 * the engine, and does not`. It fires on the thing it guards — drift between the counterfactuals
 * and `localiseMechanism` — just not on its own deletion.
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
// `new-session-checklist`: the newest session is exactly the one a stale list omits, and this
// corpus's only two members both arrived in the two most recent sessions.
const SESSIONS = readdirSync(SESSIONS_DIR)
  .filter(s => existsSync(`${SESSIONS_DIR}/${s}`)
    && readdirSync(`${SESSIONS_DIR}/${s}`).some(f => f.endsWith('.ttrm')))
  .sort();

type Member = {
  session: string; file: string; round: number; user: string;
  lock: number; step: number; mechanism: string; kind: string;
};

/**
 * The two events this corpus contains, with the verdict each currently receives. The verdict is
 * part of the pin on purpose: 08-09's `placement` is the wrong half of the defect, and if a repair
 * reclassifies it, this list must be edited rather than quietly continuing to pass.
 */
const ACCESS_CLASS: Member[] = [
  // A T-spin Single at lock 70 cleared row 33 — `LLLIIII.ZZ`, one open column. The slot is at rows
  // 35-37 and rows 34-39 are bit-identical in A = boards[69] and in B, so nothing was formed:
  // deleting row 33 from A ALONE yields the same 2-line slot [36,36,36,37,35] (best 1 -> 2), where
  // deleting rows 31/32/34 instead gives 0/0/1. The clear removed the lid. The T's own cells sit at
  // B-row 33, outside the slot's 35-37 and its +/-1 margin, so `touches` is false.
  { session: '2026-08-14', file: 'replay-2026-08-14-0.ttrm', round: 4, user: 'yachi',
    lock: 74, step: 70, mechanism: 'unattributed', kind: 'self_built' },
  // The dangerous half. The causing piece is a Z (`spin: 'none'`) at rows 21-23 that cleared row 23;
  // the slot is at rows 24-26 and rows 24-39 are bit-identical either side, so again nothing was
  // formed — A minus row 23 alone gives best 0 -> 2, controls on rows 21/22/24 give 0/0/0. The Z is
  // credited anyway because one of its cells lands at B-row 23, which is slot row 24 minus one, and
  // `touches` accepts adjacency. The report prints this event inside 「玩家自己落嗰隻棋整出嚟」.
  { session: '2026-08-09', file: 'replay-2026-08-09-6.ttrm', round: 7, user: 'pinglamb',
    lock: 24, step: 20, mechanism: 'placement', kind: 'self_built' },
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
  const check = (predicted: string, rec: { mechanism?: string }, where: string) => {
    const ok = predicted === 'ACCESS'
      ? rec.mechanism === 'placement' || rec.mechanism === 'unattributed'
      : predicted === rec.mechanism;
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

test('the access class is exactly the two named events — a third fails, a missing one fails', () => {
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

test('the model attributes 7 of the 9 candidates defensibly, and misses 2', () => {
  // The numbers that make this a finding rather than a curiosity. 9 records corpus-wide are ones
  // the clear ALONE explains; 5 the model credits to the clear correctly, 2 more are overdetermined
  // (the placement alone also sufficed, so `placement` is a defensible verdict), and 2 are the gap.
  // A detector that fired on everything, or on nothing, would look identical in `access` alone —
  // these are its denominator, its true positives and the branch that pre-empts them.
  expect(result.clearAlone).toBe(9);
  expect(result.formed).toBe(5);
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
  // and the check must have actually run — over the 9 candidates, not over an empty set
  expect(result.clearAlone).toBeGreaterThan(0);
});

test('the sweep reached the corpus it claims to have swept', () => {
  // Exposure. Every assertion above is over a set that an early `continue` could empty, and an
  // empty set compares equal to an empty expectation — the shape this repo calls a gate that
  // proves nothing while reporting ok. These are REGRESSION PINS in the sense
  // forecast-corpus.test.ts means it: produced by this code, not by an outside oracle.
  expect(SESSIONS.length).toBe(6);
  expect(result.localised).toBe(1789);
});
