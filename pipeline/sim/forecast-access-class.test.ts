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
 *   inside      = some cleared row lies strictly inside the slot found in B  (the model's own test)
 *
 * `clearAlone && !inside` is the access class. The discriminator has a real working set rather than
 * a token one: 9 records corpus-wide are `clearAlone`, and `inside` correctly attributes 7 of them
 * to the clear. The 2 it misses are named below.
 *
 * NAMED, NOT BOUNDED — the `DT_ORDER_IN_OPENER` precedent (pipeline/openers/openers.test.ts) and
 * `check_loo.py`'s ANNOTATED. An inequality would be satisfied by any two such events anywhere;
 * this names these two, so a third has to be investigated instead of absorbed, and either of them
 * disappearing or changing verdict fails just as loudly. A repair that lands a fifth `Mechanism`
 * SHOULD break this test — that is the point, and the list is where the repair gets recorded.
 *
 * Cost: ~13s, because it replays every case in every session through the oracle. That is the same
 * work forecast-corpus.test.ts does for one session, and the class cannot be measured any other
 * way — the committed artefacts carry counts, not boards.
 */
import { test, expect } from 'bun:test';
import { readdirSync, existsSync } from 'node:fs';
import { bestTspin, bestTspinLines, forecastMetric } from './forecast.ts';
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
  let localised = 0, clearAlone = 0, formed = 0, pieceBlocked = 0;

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

        const B = withoutRows(Bpre, cleared);
        if (bestTspinLines(B) < target) {
          // The clear alone reaches the target but the placement takes it away again. Not seen in
          // this corpus; counted rather than dropped, so it cannot start happening in silence.
          if (rec.lockIndex <= v) pieceBlocked++;
          continue;
        }

        // The model's own test: a cleared row strictly inside the slot means the clear FORMED it,
        // which `localiseMechanism` already attributes correctly.
        const slot = bestTspin(B)!;
        const back = (rB: number) => {
          for (let p = 0; p < H; p++) if (p + cleared.filter(cr => cr > p).length === rB) return p;
          return rB;
        };
        const ps = slot.rows.map(back);
        if (cleared.some(cr => cr > Math.min(...ps) && cr < Math.max(...ps))) {
          if (rec.lockIndex <= v) formed++;
          continue;
        }

        const m: Member = { session, file: c.file, round: c.round, user: c.user,
          lock: rec.lockIndex, step: t, mechanism: rec.mechanism, kind: rec.kind };
        (rec.lockIndex <= v ? access : beyondPrefix).push(m);
      }
    }
  }
  return { access, beyondPrefix, localised, clearAlone, formed, pieceBlocked };
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

test('the strictly-inside test is doing real work — 7 of 9 attributed, 2 missed', () => {
  // The number that makes this a finding rather than a curiosity. 9 records corpus-wide are ones
  // the clear ALONE explains; the model's geometric test correctly credits the clear in 7 of them
  // and misses the 2 named above. A detector that fired on everything, or on nothing, would look
  // the same in `access` alone — these are its denominator and its true positives.
  expect(result.clearAlone).toBe(9);
  expect(result.formed).toBe(7);
  expect(result.formed + result.access.length).toBe(result.clearAlone);
  // Not seen in this corpus, and it must not start silently: the clear suffices, then the piece
  // takes the slot back away. It is a real possibility, not an impossible one.
  expect(result.pieceBlocked).toBe(0);
});

test('the sweep reached the corpus it claims to have swept', () => {
  // Exposure. Every assertion above is over a set that an early `continue` could empty, and an
  // empty set compares equal to an empty expectation — the shape this repo calls a gate that
  // proves nothing while reporting ok. These are REGRESSION PINS in the sense
  // forecast-corpus.test.ts means it: produced by this code, not by an outside oracle.
  expect(SESSIONS.length).toBe(6);
  expect(result.localised).toBe(1789);
});
