/**
 * The SDPC Spin route artefact (`analysis/sdpcspin-facts.json`, from
 * `pipeline/sim/emit-route-facts.ts --opener sdpcspin`; the rules are the shared `route-facts.ts`, the
 * profile `route-profile-sdpcspin.ts`, the routes harddrop's SDPC_Spin page transcribed in
 * `sdpcspin-routes.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. TWO CROSS-CHECKS, because there is no harddrop field to compare a flag with (as stick spin):
 *        * against STICK SPIN's artefact (`stickspin-facts.json`): SDPC Spin's bag 1 is stick spin's
 *          bag 1 laid flat, in one more J/L colouring. Every stick-spin bag-1 case is an SDPC Spin
 *          bag-1 case at the corresponding node (bag1.pc ↔ bag1.jl, bag1.left ↔ bag1.jl.left), in the
 *          OPPOSITE handedness (the page draws stick spin's bag1.pc mirrored), with the same 7th lock;
 *          the SDPC Spin cases stick spin lacks are exactly stick spin's colour-refused rounds, all at
 *          the other colouring (bag1.lj / bag1.lj.left). And every round stick spin explained as
 *          「near 2.sd」 is an SDPC Spin bag-2 round or named here with its reason.
 *        * against the ORDERING metric (`opener-facts.json` `ordering.per_round` `dt_order`, decided on
 *          spin lock indices, never on a board): the route fires TSS, TSD, then a TST, so every
 *          Double-first round is an SDPC Spin round or named in DT_NOT_SDPCSPIN with a reason the test
 *          verifies, and every SDPC Spin round with a complete window is Double-first or named with no
 *          Triple in it.
 *   3. NAMED lists, not bounds: every entry is a real round, resolved by (file, 0-based round) in that
 *      session's replay-facts.json with its match POSITION, and checked per (session, player).
 *   4. the per-node counts, the opportunities, the mirror split, why every round stops where it does,
 *      and the case key order are pinned.
 *   5. mutants: each rule turned off must turn this file red, with the symptom its rule predicts —
 *      and the rules this corpus cannot exercise are NAMED as equivalent, measured, never dropped.
 *
 * COST, accepted explicitly: one more full-corpus `runCaseOracle` digest in the `typescript` job
 * (about half a minute), as the other route tests pay. The mutants reuse ONE digest.
 *
 * Run: bun test pipeline/openers/sdpcspin.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, digestCorpus, corpus, loadRoutes, stripGarbage, type RoundDigest, type Mutants }
  from '../sim/route-facts.ts';
import { SDPCSPIN } from '../sim/route-profile-sdpcspin.ts';
import { STICKSPIN } from '../sim/route-profile-stickspin.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { caseName, checkNamedList, checkPositions, roundOf } from './route-facts-checks.ts';
import { mirrorRows } from './match.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22',
   '2026-10-29']);

/** Bag 1 matched (six pieces, either colouring) and the 7th lock was NOT the drawn TSS: the piece, the
 *  engine's spin and the lines it cleared. Both are stick spin's too: 10-12 m8r4 lays its T flat on the
 *  slot with no spin, 10-03 m7r8 places a J there. */
const BAG1_SPIN_OFF_PAGE: string[] = ['2026-10-03 m7r8 yachi (J none 0)', '2026-10-12 m8r4 yachi (T none 0)'];
/** Bag 2 matched with complete garbage rows stripped from under it (the count in brackets). */
const BAG2_GARBAGE_STRIPPED: string[] = [
  '2026-09-18 m6r4 pinglamb (9)', '2026-09-18 m7r7 pinglamb (6)', '2026-09-19 m3r6 yachi (12)',
  '2026-09-19 m5r2 pinglamb (4)', '2026-10-03 m4r4 yachi (6)', '2026-10-03 m4r7 yachi (2)', '2026-10-03 m5r4 yachi (6)',
  '2026-10-03 m10r1 yachi (12)', '2026-10-03 m19r6 yachi (6)', '2026-10-09 m2r2 yachi (6)', '2026-10-09 m7r8 yachi (6)',
  '2026-10-09 m8r1 yachi (6)', '2026-10-09 m10r2 yachi (6)', '2026-10-09 m10r7 yachi (6)', '2026-10-09 m11r1 yachi (4)',
  // 2026-10-20: one, yachi's m4r1 (prefix 116), which then reaches 3.first at lock 19.
  '2026-10-20 m4r1 yachi (6)',
  '2026-10-22 m5r5 yachi (6)',
];
/** No bag-2 sample, and the board before the bag-2 TSD is a strict SUBSET of 2.tsd: the T fired on the
 *  12th lock (0-based index 12) with one bag-2 piece still to come, so the 13-lock sample already holds
 *  a clear that is not the route's own. MEASURED, never matched. */
const BAG2_NONE_TSD_BEFORE_COMPLETE: string[] = [
  '2026-09-17 m2r7 yachi under 2.tsd', '2026-09-19 m8r6 yachi under 2.tsd', '2026-09-19 m9r6 yachi under 2.tsd',
  '2026-09-19 m15r5 yachi under 2.tsd', '2026-10-03 m6r8 yachi under 2.tsd', '2026-10-09 m3r1 yachi under 2.tsd',
  '2026-10-09 m9r3 yachi under 2.tsd',
];
/** A sampled bag 2 that matched nothing and is no subset, superset or moved piece of 2.tsd: its bag-2 T
 *  clears two lines with NO spin (stick spin names it for the same reason). */
const BAG2_NONE_UNEXPLAINED: string[] = ['2026-10-03 m9r6 yachi'];

/** Measured EMPTY. A first entry is a red build to investigate. */
const BAG2_NONE_EXTRA_PIECE: string[] = [];
const BAG2_NONE_MOVED_PIECE: string[] = [];
const PC_OFF_PAGE: string[] = [];
const BAG2_HANDEDNESS_MISMATCH: string[] = [];
const MULTI_COLOUR_RESOLVED_BY_BRANCH: string[] = [];
const COLOUR_DISAGREE: string[] = [];
const PC_GARBAGE_IN_WINDOW: string[] = [];

/** Rounds that reached 2.tsd and no bag-3 board, with the reason the test MEASURES (`stopAt2tsd`):
 *    tst_before_complete  a full 3-line T-spin fired while the board before it was a strict subset of a
 *                         3.build board (one or two bag-3 pieces placed after the TST, so no lock holds
 *                         the drawn board)
 *    tst_off_page         a full 3-line T-spin fired on a board that is no subset of any 3.build board (09-18
 *                         m7r7: the bag-3 I stood at the right wall, not in column 0)
 *    no_tst               no full 3-line T-spin in the event window after bag 2 */
const STOPS_AT_2TSD: Record<string, 'tst_before_complete' | 'tst_off_page' | 'no_tst'> = {
  '2026-09-18 m6r4 pinglamb': 'no_tst', '2026-09-18 m7r7 pinglamb': 'tst_off_page',
  '2026-09-19 m3r6 yachi': 'no_tst', '2026-09-19 m4r4 yachi': 'tst_before_complete',
  '2026-09-19 m16r1 yachi': 'tst_before_complete', '2026-10-03 m2r7 yachi': 'no_tst',
  '2026-10-03 m5r4 yachi': 'tst_before_complete', '2026-10-03 m5r6 yachi': 'tst_before_complete',
  '2026-10-03 m10r1 yachi': 'no_tst', '2026-10-03 m14r1 yachi': 'tst_before_complete',
  '2026-10-03 m19r6 yachi': 'no_tst', '2026-10-09 m1r7 yachi': 'tst_before_complete',
  '2026-10-09 m2r6 yachi': 'tst_before_complete', '2026-10-09 m7r5 yachi': 'no_tst',
  '2026-10-09 m7r9 yachi': 'tst_before_complete', '2026-10-09 m10r2 yachi': 'tst_before_complete',
  '2026-10-09 m10r7 yachi': 'tst_before_complete', '2026-10-09 m11r1 yachi': 'tst_before_complete',
  '2026-10-29 m1r4 yachi': 'tst_before_complete',
};

/** Cases whose deepest node lies past the verified prefix: recorded, `verified: false`. */
const DEEPEST_UNVERIFIED: string[] = ['2026-10-03 m15r5 yachi', '2026-10-03 m16r2 yachi'];

/** Bag 1 by player and handedness: yachi mirrors it in 80 of 82 (stick spin's 2 of 78 the other way
 *  round, because the page draws stick spin's board mirrored); pinglamb's four are all as drawn. */
const MIRRORED_BAG1 = { yachi: 80 };

/** Cases per measured node. The bag-3 and later zeros are COMPARED, never "not compared". */
const NODE_CASES: Record<string, number> = {
  // 2026-10-20 adds four, all yachi's and all mirrored: two bag1.lj (m1r4, m3r5 — stick spin's two new
  // COLOUR_DISAGREE boards) and two bag1.jl (m2r3, m4r1); every one reaches 2.tsd and 3.first, and the
  // two bag1.lj rounds go on to 3.first.cave at lock 26.
  // 2026-10-22 adds one, yachi's m5r5, mirrored bag1.jl, 2.tsd with six garbage rows stripped
  // (BAG2_GARBAGE_STRIPPED), 3.first at lock 19 (prefix 40); no cave.
  // 2026-10-29 adds four, all yachi's and all mirrored: two bag1.lj (m1r4, m2r5 — stick spin's two new
  // COLOUR_DISAGREE boards) and two bag1.jl (m2r1, m9r9); all four reach 2.tsd, and all but m1r4
  // (STOPS_AT_2TSD) reach 3.first at lock 19; no cave.
  'bag1.lj.left': 1, 'bag1.lj': 9, 'bag1.jl.left': 1, 'bag1.jl': 75, '2.tsd': 72, '3.first': 51, '3.second': 1,
  '3.third': 1, '3.first.cave': 10, '3.first.cave.stsd.next': 0, '3.first.trinity': 0, '3.first.trinity.tsd': 0,
  '3.first.trinity.tss': 0, '3.second.cspin': 0, '3.second.alt#1': 0, '3.second.alt#2': 0, '3.second.cspin.dt#1': 0,
  '3.second.cspin.dt#2': 0, '3.second.cspin.o_first#1': 0, '3.second.cspin.o_first#2': 0,
  '3.second.cspin.l_first#1': 0, '3.second.cspin.l_first#2': 0, '3.second.cspin.l_first#3': 0,
  '3.second.cspin.l_first#4': 0, '3.third.imperial': 0, '3.third.imperial.pc#1': 0, '3.third.imperial.pc#2': 0,
  '3.third.imperial.pc#3': 0, '3.third.imperial.pc#4': 0, '3.third.transition#1': 0, '3.third.transition#2': 0,
};
/** A node whose 0 is STRUCTURAL, not measured: no round can ever be filed under it, and why. The
 *  classifier takes the sibling a round reaches first, and the board the Trinity's own TSD leaves
 *  (3.first.trinity.tsd) is passed on the way to its TSS, so every round that reaches the TSS board is
 *  filed under the TSD (the demo test's CLASSIFIER_SIBLING measures it on the TSS demo). So this 0 is
 *  not evidence that nobody played the TSS; it cannot move. */
const STRUCTURAL_ZERO: Record<string, string> = {
  '3.first.trinity.tss': 'sibling of 3.first.trinity.tsd, which every round reaching it passes first',
};
/** Opportunities per player: bag 1 at 6 locks (both stage boards share them), the TSS at lock 7, bag 2
 *  at 13 locks, the bag-3 boards and the PC patterns under 2.tsd, bag 4 and 5 under the board reached. */
const OPPORTUNITIES: Record<string, Record<string, number>> = {
  'bag1.lj.left': { pinglamb: 1411, yachi: 1369 }, 'bag1.jl.left': { pinglamb: 1411, yachi: 1369 },
  'bag1.lj': { pinglamb: 4, yachi: 6 }, 'bag1.jl': { pinglamb: 0, yachi: 76 }, '2.tsd': { pinglamb: 4, yachi: 69 },
  '3.first': { pinglamb: 4, yachi: 68 }, '3.second': { pinglamb: 4, yachi: 68 }, '3.third': { pinglamb: 4, yachi: 68 },
  '3.first.cave': { pinglamb: 0, yachi: 51 }, '3.first.trinity': { pinglamb: 0, yachi: 10 },
  '3.second.cspin': { pinglamb: 1, yachi: 0 }, '3.second.alt#1': { pinglamb: 1, yachi: 0 },
  '3.second.alt#2': { pinglamb: 1, yachi: 0 }, '3.third.imperial': { pinglamb: 1, yachi: 0 },
  '3.third.transition#1': { pinglamb: 1, yachi: 0 }, '3.third.transition#2': { pinglamb: 1, yachi: 0 },
  '3.third.imperial.pc#1': { pinglamb: 4, yachi: 68 },
};
/** Nodes the classifier cannot compare, and why (from the routes JSON, never a count of 0). */
const UNMEASURED: Record<string, string> = {
  'bag1.after': 'illustration', '2.after': 'illustration',
  '3.first.cave.stsd': 'unmatchable: 9 non-empty rows > ROWS = 8', '3.first.trinity.donate': 'text_only',
  '3.second.cspin.z_early': 'unmatchable: draws one Z twice (on the J, and its usual cells marked with apostrophes): '
    + 'not one board state; and 9 non-empty rows > ROWS = 8',
  '3.second.alt.pc12': 'text_only', '3.second.alt.transition': 'text_only',
  '3.second.cspin.first#1': 'unmatchable: 9 non-empty rows > ROWS = 8',
  '3.second.cspin.first#2': 'unmatchable: 9 non-empty rows > ROWS = 8',
};
/** Where every case stops, by (deepest node, bag 2 sampled?, bag2_near kind). */
const STOPS: Record<string, number> = {
  '3.first.cave | sampled | -': 10, '3.first | sampled | -': 41, '3.second | sampled | -': 1, '3.third | sampled | -': 1,
  '2.tsd | sampled | -': 19,
  'bag1.jl | sampled | -': 1,         // 10-03 m9r6: BAG2_NONE_UNEXPLAINED
  'bag1.jl | unsampled | subset': 7,  // BAG2_NONE_TSD_BEFORE_COMPLETE
  'bag1.jl | unsampled | -': 4,       // a verified prefix ending at the TSS (verified_to 6): 10-03 m2r4, m11r7, m17r4, 10-09 m2r3
  'bag1.jl.left | unsampled | -': 1, 'bag1.lj.left | unsampled | -': 1,  // BAG1_SPIN_OFF_PAGE
};

/** The ordering cross-check's exceptions: every Double-first round that is NOT an SDPC Spin case, and
 *  why, which the test verifies:
 *    dt_cannon       the cell's first-bag metric has at least that many exact DT Cannon matches
 *    both_orders     the window holds a Triple before AND after the Double (`cspin_order` 1 too)
 *    garbage_bag1    garbage arrived before lock 6, so bag 1 was never compared (stick spin's jl_split
 *                    09-18 m13r1: its board under the garbage is bag1.lj) */
const DT_NOT_SDPCSPIN: Record<string, 'dt_cannon' | 'both_orders' | 'garbage_bag1'> = {
  '2026-08-14 m3r4 yachi': 'dt_cannon',
  '2026-08-25 m9r3 yachi': 'dt_cannon',
  '2026-09-10 m7r3 pinglamb': 'both_orders',
  '2026-09-17 m7r4 yachi': 'dt_cannon',
  '2026-09-18 m2r3 pinglamb': 'both_orders',
  '2026-09-18 m13r1 pinglamb': 'garbage_bag1',
  '2026-10-03 m7r3 yachi': 'dt_cannon',
  '2026-10-22 m2r7 yachi': 'dt_cannon',   // the session's one exact DT Cannon first bag (prefix 61)
};
/** SDPC Spin rounds with a COMPLETE opener window (0-based locks 0-21) that are not Double-first: none
 *  holds a Triple in the window. Stick spin's eight (its STICKSPIN_NOT_DT) and pinglamb's 09-18 m6r4, a
 *  bag1.lj round stick spin's colour check refused; the 2.tsd ones are STOPS_AT_2TSD's no_tst rounds. */
const SDPCSPIN_NOT_DT: string[] = [
  '2026-09-18 m6r4 pinglamb', '2026-09-19 m3r6 yachi', '2026-10-03 m2r7 yachi', '2026-10-03 m9r6 yachi',
  '2026-10-03 m10r1 yachi', '2026-10-03 m19r6 yachi', '2026-10-09 m7r5 yachi', '2026-10-09 m9r1 yachi',
  '2026-10-12 m8r4 yachi',
];
/** Double-first rounds that ARE SDPC Spin, per player: the ordering cross-check's positive count. */
const DT_AND_SDPCSPIN: Record<string, number> = { pinglamb: 3, yachi: 68 };

/** Stick spin's 「near 2.sd」 rounds that are NOT SDPC Spin bag-2 cases, and their SDPC Spin deepest node:
 *  seven are BAG2_NONE_TSD_BEFORE_COMPLETE, and 10-09 m2r3's verified prefix ends at its TSS (stick spin
 *  explains it on the oracle board past the prefix, which bag 2 here never samples). */
const STICKSPIN_NEAR_NOT_2TSD: Record<string, string> = {
  '2026-09-17 m2r7 yachi': 'bag1.jl', '2026-09-19 m8r6 yachi': 'bag1.jl', '2026-09-19 m9r6 yachi': 'bag1.jl',
  '2026-09-19 m15r5 yachi': 'bag1.jl', '2026-10-03 m6r8 yachi': 'bag1.jl', '2026-10-09 m2r3 yachi': 'bag1.jl',
  '2026-10-09 m3r1 yachi': 'bag1.jl', '2026-10-09 m9r3 yachi': 'bag1.jl',
};

/** The case object's key order is part of the artefact's bytes. */
const CASE_KEYS = ['session', 'file', 'round_index0', 'match', 'round', 'player', 'verified_to', 'bag1', 'bag2',
                   'pc', 'snapshots', 'bag2_near', 'deepest', 'deepest_lock', 'verified'];
const BAG1_KEYS = ['node', 'mirrored', 'lock', 'matched_variants', 'spin'];
const BAG2_KEYS = ['node', 'mirrored', 'lock', 'order_as_drawn', 'conditions_met', 'condition_met',
                   'handedness_matches_bag1', 'garbage_rows_stripped'];

const committedText = () => readFileSync(SDPCSPIN.artefactPath, 'utf8');
const committed = () => JSON.parse(committedText());
let DIGESTS: RoundDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SDPCSPIN));

test('the emitter covers exactly the corpus on disk', () => {
  expect(corpus()).toEqual(SESSIONS);
  expect(committed().sessions).toEqual(SESSIONS);
  expect(committed().schema).toBe('sdpcspin-facts/1');
  expect(committed().report_eligible).toBe(false);
});

test('rebuilding reproduces the committed sdpcspin-facts.json byte for byte', () => {
  expect(serialise(build(SDPCSPIN, {}, digests()))).toBe(committedText());
}, 600_000);

test('the profile and the routes agree: derived 6-lock stage boards, each TSS board spin_of its own', () => {
  const routes = loadRoutes(SDPCSPIN.routesPath) as any;
  const by = new Map<string, any>(routes.nodes.map((n: any) => [n.id, n]));
  expect(SDPCSPIN.bag1.stages.map(s => s.nodes)).toEqual([['bag1.jl.left', 'bag1.lj.left']]);
  for (const id of SDPCSPIN.bag1.spin!.nodes) {
    const n = by.get(id), left = by.get(n.spin_of);
    expect(left?.locks, id).toBe(6);
    // the stage board is the TSS board with its T removed, letter for letter
    expect(left.rows, id).toEqual(n.rows.map((r: string) => r.replace(/U/g, '-')));
  }
});

/** The stick spin artefact's cases by name. */
const stickspin = () => JSON.parse(readFileSync(STICKSPIN.artefactPath, 'utf8'));

test('the stick spin cross-check: the same bag-1 rounds, the other handedness, every difference named', () => {
  const sd = new Map<string, any>(committed().cases.map((c: any) => [caseName(c), c]));
  const ssArt = stickspin();
  const ss = new Map<string, any>(ssArt.cases.map((c: any) => [caseName(c), c]));
  const NODE: Record<string, string> = { 'bag1.pc': 'bag1.jl', 'bag1.left': 'bag1.jl.left' };
  for (const [k, c] of ss) {
    const d = sd.get(k);
    expect(d, k).toBeDefined();
    expect(d.bag1.node, k).toBe(NODE[c.bag1.node]);
    expect(d.bag1.mirrored, k).toBe(!c.bag1.mirrored);
    expect(d.bag1.spin, k).toEqual({ ...c.bag1.spin, node: c.bag1.spin.node ? NODE[c.bag1.spin.node] : null });
  }
  // the SDPC Spin cases stick spin lacks are exactly its colour-refused bag-1 boards, at the other colouring
  const extra = [...sd.keys()].filter(k => !ss.has(k)).sort();
  expect(extra).toEqual([...new Set(ssArt.lists.colour_disagree.map(roundOf))].sort());
  for (const k of extra) expect(['bag1.lj', 'bag1.lj.left'], k).toContain(sd.get(k).bag1.node);
  // every round stick spin explained as near its 2.sd is an SDPC Spin bag-2 round, or named
  const near = ssArt.lists.bag2_none_near.map(roundOf) as string[];
  const not2 = near.filter(k => sd.get(k)?.bag2?.node !== '2.tsd');
  expect(Object.fromEntries(not2.sort().map(k => [k, sd.get(k)?.deepest ?? null]))).toEqual(STICKSPIN_NEAR_NOT_2TSD);
});

/** Every round of the ordering metric, by name, from each session's opener-facts.json. */
function orderingRounds() {
  const out = new Map<string, any>();
  const dtCannon: Record<string, number> = {};
  for (const s of SESSIONS) {
    const of = JSON.parse(readFileSync(`${ROOT}/${s}/sim/opener-facts.json`, 'utf8'));
    const rf = JSON.parse(readFileSync(`${ROOT}/${s}/sim/replay-facts.json`, 'utf8'));
    const pos = new Map<string, number>(rf.rounds.map((r: any) => [`${r.file}#${r.round}`, r.match]));
    for (const r of of.ordering.per_round)
      out.set(`${s} m${pos.get(`${r.file}#${r.round}`)}r${r.round + 1} ${r.user}`, { ...r, session: s });
    for (const p of of.first_bag.players)
      dtCannon[`${s} ${p.user}`] = p.exact_matches.filter((m: any) => m.name.startsWith('DT Cannon'))
        .reduce((a: number, m: any) => a + m.rounds, 0);
  }
  return { rounds: out, dtCannon };
}

test('the ordering cross-check: Double-first openers against SDPC Spin bag 1, both ways, every exception verified', () => {
  const art = committed();
  const sd = new Map<string, any>(art.cases.map((c: any) => [caseName(c), c]));
  const { rounds, dtCannon } = orderingRounds();
  const dt = [...rounds.entries()].filter(([, r]) => r.dt_order === 1).map(([k]) => k);
  expect(dt.filter(k => !sd.has(k)).sort()).toEqual(Object.keys(DT_NOT_SDPCSPIN).sort());
  const both: Record<string, number> = {};
  for (const k of dt.filter(k => sd.has(k))) {
    const p = k.split(' ')[2]!;
    both[p] = (both[p] ?? 0) + 1;
    // a Double-first SDPC Spin round got past its TSS
    expect(['bag1.jl', 'bag1.lj'], k).toContain(sd.get(k).bag1.node);
  }
  expect(both).toEqual(DT_AND_SDPCSPIN);
  const byName = new Map(digests().map(d => [`${d.session} m${d.match}r${d.round + 1} ${d.user}`, d]));
  const routes = loadRoutes(SDPCSPIN.routesPath);
  const lj = routes.nodes.find(n => n.id === 'bag1.lj.left')!.rows!.map(r => r.toUpperCase().replace(/-/g, '.'))
    .filter(r => r !== '..........');
  const cannons: Record<string, number> = {};
  for (const [k, why] of Object.entries(DT_NOT_SDPCSPIN)) {
    const r = rounds.get(k)!;
    if (why === 'dt_cannon') { const cell = roundOf(k).split(' ').filter((_, i) => i !== 1).join(' '); cannons[cell] = (cannons[cell] ?? 0) + 1; }
    if (why === 'both_orders') expect(r.cspin_order, k).toBe(1);
    if (why === 'garbage_bag1') {
      const d = byName.get(k)!;
      expect(d.garbage.some(g => g < 6), k).toBe(true);
      // under the garbage, the board at 6 locks is the bag1.lj colouring, as drawn or mirrored
      const b = stripGarbage(d.rows[5]!).rows!;
      expect([lj, mirrorRows(lj)].some(h => h.join('/') === b.join('/')), k).toBe(true);
    }
  }
  for (const [cell, n] of Object.entries(cannons)) expect(dtCannon[cell]!, cell).toBeGreaterThanOrEqual(n);
  // the converse: every SDPC Spin round with a complete window is Double-first, or named with no Triple
  const notDt = art.cases.map(caseName).filter((k: string) => rounds.get(k)?.window_complete && rounds.get(k).dt_order !== 1);
  expect(notDt.sort()).toEqual([...SDPCSPIN_NOT_DT].sort());
  for (const k of SDPCSPIN_NOT_DT) expect(rounds.get(k).tspin_triples_window, k).toBe(0);
  // every no_tst stop at 2.tsd is one of them
  for (const [k, why] of Object.entries(STOPS_AT_2TSD)) if (why === 'no_tst') expect(SDPCSPIN_NOT_DT, k).toContain(k);
});

test('the named lists are exactly what the artefact holds, cell by cell', () => {
  const L = committed().lists;
  const pairs: [string, string[], string[]][] = [
    ['bag1_spin_off_page', L.bag1_spin_off_page, BAG1_SPIN_OFF_PAGE],
    ['bag2_garbage_stripped', L.bag2_garbage_stripped, BAG2_GARBAGE_STRIPPED],
    ['bag2_none_tsd_before_complete', L.bag2_none_tsd_before_complete, BAG2_NONE_TSD_BEFORE_COMPLETE],
    ['bag2_none_extra_piece', L.bag2_none_extra_piece, BAG2_NONE_EXTRA_PIECE],
    ['bag2_none_moved_piece', L.bag2_none_moved_piece, BAG2_NONE_MOVED_PIECE],
    ['bag2_none_unexplained', L.bag2_none_unexplained, BAG2_NONE_UNEXPLAINED],
    ['pc_off_page', L.pc_off_page, PC_OFF_PAGE],
    ['multi_colour_resolved_by_branch', L.multi_colour_resolved_by_branch, MULTI_COLOUR_RESOLVED_BY_BRANCH],
    ['bag2_handedness_mismatch', L.bag2_handedness_mismatch, BAG2_HANDEDNESS_MISMATCH],
    ['colour_disagree', L.colour_disagree, COLOUR_DISAGREE],
    ['pc_garbage_in_window', L.pc_garbage_in_window, PC_GARBAGE_IN_WINDOW],
  ];
  for (const [k, got, want] of pairs) checkNamedList(k, got, want);
  expect(Object.keys(L).sort()).toEqual(pairs.map(p => p[0]).sort());
  checkNamedList('deepest unverified', committed().cases.filter((c: any) => !c.verified).map(caseName), DEEPEST_UNVERIFIED);
});

/** occupancy cells of a bottom-aligned board, `.`/`-`/`U` empty */
const occ = (rows: string[], h = 12) => {
  const s = new Set<number>();
  [...Array(Math.max(0, h - rows.length)).fill('..........'), ...rows]
    .forEach((r, y) => [...r].forEach((ch, x) => { if (!'.-U'.includes(ch)) s.add(y * 10 + x); }));
  return s;
};

test('why every round that reached 2.tsd and no bag-3 board stops there, measured', () => {
  const art = committed();
  const routes = loadRoutes(SDPCSPIN.routesPath);
  const builds = routes.nodes.filter(n => n.group === '3.build');
  const byName = new Map(digests().map(d => [`${d.session} m${d.match}r${d.round + 1} ${d.user}`, d]));
  const got: Record<string, string> = {};
  for (const c of art.cases.filter((c: any) => c.deepest === '2.tsd')) {
    const k = caseName(c), d = byName.get(k)!;
    const tst = d.locks.findIndex((l, i) => i > c.bag2.lock && i < SDPCSPIN.eventLocks
      && l.piece === 'T' && l.spin === 'full' && l.cleared === 3);
    if (tst < 0) { got[k] = 'no_tst'; continue; }
    const pre = stripGarbage(d.rows[tst - 1]!).rows!;
    const mine = occ(pre);
    const subset = builds.some(b => {
      const th = occ(c.bag2.mirrored ? mirrorRows(b.rows!) : b.rows!);
      return [...mine].every(q => th.has(q)) && th.size > mine.size;
    });
    got[k] = subset ? 'tst_before_complete' : 'tst_off_page';
  }
  expect(got).toEqual(STOPS_AT_2TSD);
});

test('per-node counts, opportunities, the mirror split and where every round stops', () => {
  const art = committed();
  for (const [id, n] of Object.entries(NODE_CASES))
    expect(art.nodes.find((x: any) => x.id === id)?.cases, id).toBe(n);
  for (const id of Object.keys(STRUCTURAL_ZERO)) expect(NODE_CASES[id], `${id} is a structural zero`).toBe(0);
  for (const [id, o] of Object.entries(OPPORTUNITIES))
    expect(art.nodes.find((x: any) => x.id === id)?.opportunities_by_player, id).toEqual(o);
  for (const [id, why] of Object.entries(UNMEASURED)) {
    const n = art.nodes.find((x: any) => x.id === id);
    expect(n?.measured, id).toBe(false);
    expect(n.why, id).toBe(why);
  }
  expect(art.nodes.length).toBe(Object.keys(NODE_CASES).length + Object.keys(UNMEASURED).length);
  const routes = JSON.parse(readFileSync(SDPCSPIN.routesPath, 'utf8'));
  expect(art.nodes.map((n: any) => n.id)).toEqual(routes.nodes.map((n: any) => n.id));
  expect(art.outcomes).toEqual([]);
  const mirrored: Record<string, number> = {};
  for (const c of art.cases) if (c.bag1.mirrored) mirrored[c.player] = (mirrored[c.player] ?? 0) + 1;
  expect(mirrored).toEqual(MIRRORED_BAG1);
  // 2.tsd states no condition, so every case's set of met conditions is empty
  expect(Object.keys(art.conditions)).toEqual(['2.tsd']);
  expect(Object.keys(art.conditions['2.tsd'])).toEqual(['(none)']);
  const stops: Record<string, number> = {};
  for (const c of art.cases) {
    const k = `${c.deepest} | ${c.bag2 ? 'sampled' : 'unsampled'} | ${c.bag2_near ? c.bag2_near.kind : '-'}`;
    stops[k] = (stops[k] ?? 0) + 1;
    if (k === 'bag1.jl | unsampled | -') expect(c.verified_to, caseName(c)).toBe(6);
  }
  expect(stops).toEqual(STOPS);
  // a round at bag1.jl / bag1.lj fired its 7th lock on the drawn U slot; a round at a stage board did not,
  // and only a round past its TSS reaches bag 2
  for (const c of art.cases) {
    expect(c.bag1.spin, caseName(c)).not.toBeNull();
    expect(c.bag1.spin.node, caseName(c)).toBe(c.bag1.node.endsWith('.left') ? null : c.bag1.node);
    if (c.bag1.spin.node) expect([c.bag1.spin.piece, c.bag1.spin.spin, c.bag1.spin.lines, c.bag1.lock]).toEqual(['T', 'full', 1, 6]);
    else expect(c.bag2, caseName(c)).toBeNull();
  }
});

test('the case key order is pinned', () => {
  for (const c of committed().cases) {
    expect(Object.keys(c)).toEqual(CASE_KEYS);
    expect(Object.keys(c.bag1)).toEqual(BAG1_KEYS);
    if (c.bag2) expect(Object.keys(c.bag2)).toEqual(BAG2_KEYS);
  }
});

test('every case and every named entry resolves to a real round with its match POSITION', () => {
  checkPositions(committed(), SESSIONS, ROOT,
    [...BAG1_SPIN_OFF_PAGE, ...BAG2_GARBAGE_STRIPPED, ...BAG2_NONE_TSD_BEFORE_COMPLETE, ...BAG2_NONE_UNEXPLAINED,
     ...DEEPEST_UNVERIFIED, ...Object.keys(STOPS_AT_2TSD), ...SDPCSPIN_NOT_DT]);
});

// ── mutants: each must turn this file red ───────────────────────────────────────────────────

const count = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).cases;
const opp = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).opportunities;
const MUTANTS: [string, Mutants, (o: any) => void][] = [
  ['mirroring disabled', { noMirror: true }, o => expect(count(o, 'bag1.jl')).toBe(2)],
  ['the spin\'s U cells read as drawn in a mirrored round', { spinMirrorUnaware: true }, o => {
    expect(count(o, 'bag1.jl')).toBe(2);
    expect(o.lists.bag1_spin_off_page.length).toBe(BAG1_SPIN_OFF_PAGE.length + 78);
  }],
  ['the bag-1 TSS stops the bag-2 sample', { spinClearStops: true }, o => {
    expect(opp(o, '2.tsd')).toBe(0);
    expect(o.cases.every((c: any) => c.bag2 === null)).toBe(true);
  }],
  ['bag 2 sampled one lock early', { bag2Early: true }, o => {
    expect(count(o, '2.tsd')).toBe(0);
    expect(o.cases.filter((c: any) => c.bag2).every((c: any) => c.bag2.lock === 11)).toBe(true);
  }],
  ['garbage refused instead of stripped at bag 2', { noGarbageStrip: true },
   o => expect(opp(o, '2.tsd')).toBeLessThan(73)],
  ['the garbage stop removed', { noGarbageStop: true },
   o => expect(opp(o, 'bag1.jl.left')).toBeGreaterThan(2780)],
  ['the J<->L / S<->Z swap removed from the mirrored condition', { noSwap: true }, o => {
    const was = new Map(committed().cases.map((c: any) => [caseName(c), c.bag2?.order_as_drawn]));
    expect(o.cases.some((c: any) => c.bag2 && c.bag2.order_as_drawn !== was.get(caseName(c)))).toBe(true);
  }],
];

/** EQUIVALENT on this corpus, measured: each leaves the artefact byte-identical, because the case that
 *  would exercise it never occurs. No hold stage (`zHoldFirst`, `noLock7Test`, `lock7MirrorUnaware`);
 *  no Perfect Clear in an SDPC Spin round's first 40 locks reaches the 14-line count, and no bag-2
 *  board has a group of its own (`noColour`, `unscoped`, `pcNeedsBag2`, `noGroupScope`, `pcLinesOff`);
 *  and every SDPC Spin session's files sort in match order (`matchFromFilename`). Named, so the day one
 *  stops being equivalent is a red build; the rules are exercised by the other openers' tests. */
const EQUIVALENT: (keyof Mutants)[] = ['zHoldFirst', 'noLock7Test', 'lock7MirrorUnaware', 'noColour', 'unscoped',
                                       'pcNeedsBag2', 'noGroupScope', 'pcLinesOff', 'matchFromFilename'];

test('every mutant changes the artefact, with the symptom its rule predicts', () => {
  const base = committedText();
  for (const [what, mut, symptom] of MUTANTS) {
    const o = build(SDPCSPIN, mut, digests());
    expect(serialise(o) === base, what).toBe(false);
    symptom(o);
  }
}, 600_000);

test('the mutants this corpus cannot exercise are equivalent, and named', () => {
  const base = committedText();
  for (const m of EQUIVALENT) expect(serialise(build(SDPCSPIN, { [m]: true }, digests())), m).toBe(base);
}, 600_000);
