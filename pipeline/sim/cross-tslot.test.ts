/**
 * The availability probe, cross-checked by a second METHOD rather than a second run of itself.
 *
 * `bestTspin` is what every published forecast figure is computed from, and it had no outside
 * check: the SRS layer it sits on is vendored from the author's own repo. `cc-tslot.ts` ports
 * cold-clear's shape detectors, which answer the same question by matching named patterns against
 * column heights instead of searching reachable placements. Agreement between two methods that
 * share no code is worth more than any number of assertions about one of them.
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { ccTslots, colHeight, occ } from './cc-tslot.ts';
import { bestTspinLines } from './forecast.ts';
import { H } from './sim.ts';
import { classify } from './tslot-sanction.ts';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { assertCorpusIsEverySessionOnDisk, sessionsOnDisk } from '../corpus-membership.ts';

const W = 10;
const mk = (rows: string[]) => {
  const b = Array.from({ length: H }, () => new Array<any>(W).fill(null));
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.' && ch !== 'P') b[off + i]![c] = 'I'; }));
  return b;
};

test('the coordinate conversion, which is the easiest thing in the port to get wrong', () => {
  const b = mk(["..........", "#.........", "#....#####"]);
  expect(colHeight(b, 0)).toBe(2);      // filled in the bottom two rows
  expect(colHeight(b, 1)).toBe(0);      // empty column
  expect(colHeight(b, 5)).toBe(1);      // filled in the bottom row only
  expect(occ(b, -1, 5)).toBe(true);     // wall
  expect(occ(b, 3, -1)).toBe(true);     // floor
  expect(occ(b, 3, 39)).toBe(false);    // sky
  expect(occ(b, 0, 0)).toBe(true);      // bottom-left, filled
});

// The near-topout sanction used to be written out here — `anySpinLines`, `stackTop` and the rule
// combining them. It now lives in `tslot-sanction.ts`, because the same rule has to hold in the two
// CI gates (`cross-tslot-count.ts`, `cross-tslot-multi.ts`) that were pointed at this file's board
// source on 2026-08-17. Three copies of one sanction is three sanctions.

// Every session, not a list that stopped being every session. This stood at four from 2026-08-12
// to 2026-08-15 while 08-09 and 08-14 joined the corpus, so 134 rounds sat outside the only check
// that compares this count against an implementation we did not write — and nothing went red,
// because a shorter list is indistinguishable from a clean run.
//
// KEPT AS A LIST AND CHECKED AGAINST DISK, where the three sibling cross-* files were globbed
// outright. The difference is the last assertion in this file: `toBe(61656)` pins the corpus's
// total board count, so a literal here DOES depend on which sessions are read. Globbing would
// cover a seventh session silently and leave that pin to fail with a bare number; the membership
// check fails first and names the session, which is the difference between "re-bless 61656" and
// "work out why 61656 moved".
//
// The empty case stays a SKIP rather than a throw — this file has always supported a checkout with
// no sessions, which is what `realData` below expresses — so `sessionsOnDisk` is called directly
// instead of `discoverCorpus`.
const SESSIONS_DIR = `${import.meta.dir}/../../sessions`;
const SESSIONS = (sessionsOnDisk(SESSIONS_DIR).length
  ? assertCorpusIsEverySessionOnDisk(SESSIONS_DIR,
      ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14'])
  : []).map(s => `${SESSIONS_DIR}/${s}`);
const t = test as unknown as { skipIf: (c: boolean) => typeof test };
const realData = t.skipIf(SESSIONS.length === 0);

realData('two methods, no shared code, disagree on nothing across the corpus', () => {
  let both = 0, oursOnly = 0, ccOnly = 0, neither = 0;
  const unexplained: string[] = [];
  for (const session of SESSIONS) {
    process.env.REPLAY_DIR = session;
    for (const c of loadCases(session)) {
      const r = runCaseOracle(c);
      const v = verifiedIndex(r, c.truth);
      if (v < 0) continue;
      for (let step = 0; step <= v; step++) {
        const b = r.boards[step]! as any;
        const ours = bestTspinLines(b) > 0, cc = ccTslots(b).length > 0;
        if (ours && cc) both++;
        else if (ours) oursOnly++;
        else if (cc) {
          ccOnly++;
          // The shared sanction (tslot-sanction.ts) says whether a slot cold-clear names and our
          // search cannot reach is explained — a spin IS reachable and merely clears nothing, or the
          // stack is near-topout where a height pattern and a reachability search legitimately part
          // ways. Anything else is a false negative in the instrument every published figure rests on.
          const s = classify(b);
          if (!s.sanctioned)
            unexplained.push(`${c.file} r${c.round} ${c.user} lock ${step}: ${ccTslots(b).join(',')}`
              + ` [${s.reason}]`);
        } else neither++;
      }
    }
  }
  // A shape cold-clear recognises that our search cannot reach at all would be a real defect in
  // the probe every published figure rests on. There are none.
  expect(unexplained).toEqual([]);

  // Anti-vacuity: a port that silently detected nothing would agree with everything above. These
  // pin that both methods are actually firing, and roughly how often.
  expect(both).toBeGreaterThan(1500);
  expect(ccOnly).toBeGreaterThan(50);
  // 2026-08-12: switched from the hand-sim to the ORACLE board source (runCaseOracle, the vendored
  // Triangle engine). Verified prefix jumped 24.8% -> 92.3%, so the denominator grew 13319 -> 39033 as
  // the far longer prefix admits many more verified boards per round. The differential above
  // (unexplained == []) is what this test guards; this total is the anti-vacuity denominator.
  // 2026-08-15: 39033 -> 61656, purely from adding 2026-08-09 and 2026-08-14 to SESSIONS above —
  // no code changed, the list had simply stopped being every session. Worth stating what the extra
  // 22623 boards bought, since a denominator growing is not by itself a result: `unexplained` is
  // still EMPTY over them, so the two implementations disagree on nothing across a corpus half
  // again as large. That is the claim this file exists to make, now made over six sessions.
  expect(both + oursOnly + ccOnly + neither).toBe(61656);
});
