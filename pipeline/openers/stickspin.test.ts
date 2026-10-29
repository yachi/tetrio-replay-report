/**
 * The stick spin (SDパフェ) route artefact (`analysis/stickspin-facts.json`, from
 * `pipeline/sim/emit-route-facts.ts --opener stickspin`; the rules are the shared `route-facts.ts`,
 * the profile `route-profile-stickspin.ts`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE CROSS-CHECK, and why it is not the other three pages' one. harddrop's opener transcription
 *      has no stick spin field, so `opener-facts.json` has no `named_openers` column to compare a flag
 *      with, and this profile records no flag. What there is instead is an independent metric that
 *      reads the same rounds from different inputs: the ordering metric's Double-first openers
 *      (`opener-facts.json` `ordering.per_round` `dt_order`, decided on spin lock indices, never on a
 *      board). Both directions are checked, every exception NAMED with a reason the test verifies:
 *        * every Double-first round in the corpus is a stick-spin bag-1 round or in DT_NOT_STICKSPIN
 *          (a DT Cannon first bag; a window holding both orders; or the stick-spin cells with the J
 *          and L split another way, which the colour check refuses);
 *        * every stick-spin bag-1 round whose opener window (0-based locks 0-21) is complete is Double-first or in
 *          STICKSPIN_NOT_DT (no Triple in the window).
 *   3. NAMED lists, not bounds: every entry is a real round, resolved by (file, 0-based round) in that
 *      session's replay-facts.json with its match POSITION, and checked per (session, player).
 *   4. the per-node counts, the mirror split, the bag-1-only breakdown and the case key order are
 *      pinned.
 *   5. mutants: each rule turned off must turn this file red, with the symptom its rule predicts —
 *      and the rules this corpus cannot exercise are NAMED as equivalent, measured, never dropped.
 *
 * COST, accepted explicitly: one more full-corpus `runCaseOracle` digest in the `typescript` job
 * (about a minute), as the other three route tests pay. The mutants reuse ONE digest.
 *
 * Run: bun test pipeline/openers/stickspin.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, digestCorpus, corpus, loadRoutes, stripGarbage, type RoundDigest, type Mutants }
  from '../sim/route-facts.ts';
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

/** Bag 1 matched (six pieces, the page's board) and the 7th lock was NOT a full T-spin Single on a
 *  drawn U slot: the piece, the engine's spin and the lines it cleared. The one round is a T laid
 *  flat on the slot with no spin and no clear. */
const BAG1_SPIN_OFF_PAGE: string[] = ['2026-10-12 m8r4 yachi (T none 0)'];

/** No bag-2 match: the board before the first TSD is NEAREST a bag-2 board by this many cells (two
 *  pieces' worth at most), with the drawn letters missing and the letters on the board instead.
 *  MEASURED, never matched. Every one is 2.sd: in the 4-cell ones yachi builds the page's SD-PC bag 2
 *  with his J laid where the page lays its L and his L stood up in column 8 (0-based, its foot in 9) — the drawn J's two top
 *  cells missing, a J and an L cell extra. The 8-cell ones place the O otherwise too. None is
 *  2.mochi or 2.fire. */
const BAG2_NONE_NEAR: string[] = [
  "2026-09-17 m2r7 yachi under 2.sd, 8 cells (drawn JO missing, JL extra)", "2026-09-18 m6r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-09-19 m3r6 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-09-19 m4r4 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-09-19 m5r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-09-19 m8r3 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-09-19 m8r6 yachi under 2.sd (mirrored), 8 cells (drawn LO missing, JL extra)", "2026-09-19 m9r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-09-19 m9r6 yachi under 2.sd, 8 cells (drawn JO missing, JL extra)", "2026-09-19 m15r5 yachi under 2.sd, 8 cells (drawn JO missing, JL extra)",
  "2026-09-19 m16r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m2r7 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m4r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m4r4 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m4r7 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m4r8 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m5r4 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m5r6 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m6r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m6r8 yachi under 2.sd, 8 cells (drawn JO missing, JL extra)",
  "2026-10-03 m9r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m10r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m10r6 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m10r7 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m11r4 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m13r4 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m14r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m15r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m16r2 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-03 m19r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-03 m19r6 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m1r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m1r7 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m2r2 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m2r3 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m2r6 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m2r7 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m3r1 yachi under 2.sd, 8 cells (drawn JO missing, JL extra)",
  "2026-10-09 m3r8 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m4r4 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m4r8 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m5r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m5r3 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m6r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m7r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m7r2 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m7r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m7r8 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m7r9 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m8r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m8r2 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m8r6 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m8r7 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m9r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m9r3 yachi under 2.sd, 8 cells (drawn JO missing, JL extra)", "2026-10-09 m9r9 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m10r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m10r2 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m10r7 yachi under 2.sd (mirrored), 4 cells (drawn L missing, JL extra)", "2026-10-09 m11r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m11r6 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-09 m12r3 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-09 m12r6 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-12 m1r3 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-12 m3r4 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-12 m7r4 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  // 2026-10-20: two, the usual 4-cell shape (prefixes 43 and 116; m4r1 with six garbage rows stripped).
  "2026-10-20 m2r3 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-20 m4r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  "2026-10-22 m5r5 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
  // 2026-10-29: two, both as drawn, the usual 4-cell shape (prefixes 138 and 117).
  "2026-10-29 m2r1 yachi under 2.sd, 4 cells (drawn J missing, JL extra)", "2026-10-29 m9r9 yachi under 2.sd, 4 cells (drawn J missing, JL extra)",
];
/** A sampled bag 2 that matched nothing and has no near board. The one round: its bag-2 T (the 14th lock)
 *  clears two lines with NO spin, so the first TSD — the board `bag2_near` reads — is the 17th lock, after
 *  three more pieces, 16 cells from any bag-2 board. */
const BAG2_NONE_UNEXPLAINED: string[] = ['2026-10-03 m9r6 yachi'];
/** The six pieces on the drawn cells, but the eight cells the page draws as the J and the L split
 *  between those two pieces another way (the colour check refuses them; occupancy alone would have
 *  matched). pinglamb's four are one shape, mirrored; yachi's four are another, as drawn — two in one
 *  10-03 match and two on 10-20, both of those Double-first (DT_NOT_STICKSPIN `jl_split`) and both SDPC
 *  Spin `bag1.lj` cases on that page. */
const COLOUR_DISAGREE: string[] = [
  '2026-09-18 m6r4 pinglamb bag1@6 bag1.left (mirrored)', '2026-09-18 m7r7 pinglamb bag1@6 bag1.left (mirrored)',
  '2026-09-19 m5r2 pinglamb bag1@6 bag1.left (mirrored)', '2026-09-19 m5r3 pinglamb bag1@6 bag1.left (mirrored)',
  '2026-10-03 m7r7 yachi bag1@6 bag1.left', '2026-10-03 m7r8 yachi bag1@6 bag1.left',
  '2026-10-20 m1r4 yachi bag1@6 bag1.left', '2026-10-20 m3r5 yachi bag1@6 bag1.left',
  '2026-10-29 m1r4 yachi bag1@6 bag1.left', '2026-10-29 m2r5 yachi bag1@6 bag1.left',
];

/** Measured EMPTY: no round reaches a bag-2 board, so nothing is stripped under one, no PC is filed and
 *  no colour is resolved by a branch; the subset / superset / moved kinds explain none of the misses
 *  (the near kind, last, explains them). A first entry is a red build to investigate. */
const BAG2_GARBAGE_STRIPPED: string[] = [];
const BAG2_NONE_TSD_BEFORE_COMPLETE: string[] = [];
const BAG2_NONE_EXTRA_PIECE: string[] = [];
const BAG2_NONE_MOVED_PIECE: string[] = [];
const PC_OFF_PAGE: string[] = [];
const BAG2_HANDEDNESS_MISMATCH: string[] = [];
const MULTI_COLOUR_RESOLVED_BY_BRANCH: string[] = [];
const PC_GARBAGE_IN_WINDOW: string[] = [];

/** Only yachi reaches bag 1, and he mirrors it twice: pinned as a count per player, not a list. */
const MIRRORED_BAG1 = { yachi: 2 };

/** Cases per measured node. EVERY ROUND STOPS AT BAG 1: 75 at bag1.pc (the TSS laid flat), 1 at
 *  bag1.left (no spin), none at bag1.fire (the TSS stood up). The bag-2 and later zeros are COMPARED
 *  (64 bag-2 opportunities; the demos test reaches every board), never "not compared". */
const NODE_CASES: Record<string, number> = {
  'bag1.left': 1, 'bag1.fire': 0, '2.fire#1': 0, '2.fire#2': 0, '2.fire.td#2': 0, '2.fire.td#3': 0,
  '2.fire.td#4': 0, 'bag1.pc': 75, '2.sd': 0, '2.sd.pc#1': 0, '2.sd.pc#2': 0, '2.sd.pc#3': 0, '2.sd.pc#4': 0,
  '2.sd.pc#5': 0, '2.sd.pc#6': 0, '2.sd.pc#7': 0, '2.sd.pc#8': 0, '2.sd.pc#9': 0, '2.sd.pc#10': 0,
  '2.sd.pc#11': 0, '2.sd.pc#12': 0, '2.sd.pc#13': 0, '2.sd.pc#14': 0, '2.sd.pc#15': 0, '2.sd.pc#16': 0,
  '2.sd.pc#17': 0, '2.sd.pc#18': 0, '2.sd.pc#19': 0, '2.sd.tst': 0, '2.sd.imperial': 0, '2.sd.stmb': 0,
  '2.mochi': 0, '2.mochi.i_right': 0, '2.mochi.pc#1': 0, '2.mochi.pc#2': 0, '2.mochi.pc#3': 0,
  '2.mochi.pc#4': 0, '2.mochi.pc#5': 0, '2.mochi.pc#6': 0, '2.mochi.pc#7': 0, '2.mochi.pc#8': 0,
  '2.mochi.pc#9': 0, '2.mochi.pc#10': 0, '2.mochi.pc#11': 0, '2.mochi.pc#12': 0, '2.mochi.pc#13': 0,
  '2.mochi.pc#14': 0,
};
/** Opportunities: bag 1 at 6 locks, the spin step at lock 7, bag 2 at 13 locks. bag1.left's is BOTH
 *  players': pinglamb has no case, and an earlier emitter built its per-player tally from the cases
 *  alone, so his 1259 opportunities vanished and the denominator read 1223 (yachi's). Pinned per player. */
const OPPORTUNITIES: Record<string, number> = { 'bag1.left': 2780, 'bag1.fire': 76, 'bag1.pc': 76, '2.sd': 64 };
const BAG1_OPPORTUNITIES_BY_PLAYER = { pinglamb: 1411, yachi: 1369 };
/** Nodes the classifier cannot compare, and why (from the routes JSON, never a count of 0). */
const UNMEASURED: Record<string, string> = {
  'bag1.right': 'mirror_of: bag1.left', 'bag1.fire.after': 'illustration', '2.fire.tsd': 'illustration',
  '2.fire.td#1': 'unmatchable: 9 non-empty rows > ROWS = 8', '2.fire.bag4': 'text_only', 'bag1.pc.after': 'illustration',
  '2.sd.after': 'illustration', '2.sd.tst.spin': 'illustration', '2.sd.imperial.spin': 'illustration',
  '2.sd.stmb.spin': 'illustration', '2.mochi.after': 'illustration',
};
/** Why the 73 bag-1 rounds stop there, by (bag-1 node, bag 2 sampled?, bag2_near kind and cells). The
 *  eleven unsampled bag1.pc rounds: a clear other than the TSS before lock 13, or a verified prefix
 *  ending first — three of them end AT the TSS (verified_to 6), so nothing after bag 1 is checked. */
const STOPS_AT_BAG1: Record<string, number> = {
  'bag1.left | unsampled | -': 1,
  'bag1.pc | sampled | near 4': 63,
  'bag1.pc | sampled | -': 1,
  'bag1.pc | unsampled | near 4': 1,
  'bag1.pc | unsampled | near 8': 7,
  'bag1.pc | unsampled | -': 3,
};

/** The cross-check's exceptions. Every Double-first round in the corpus that is NOT a stick-spin bag-1
 *  round, and the reason, which the test verifies:
 *    dt_cannon     the cell's first-bag metric has at least that many exact DT Cannon matches
 *                  (08-14, 08-25, 09-17 and 10-03 each hold one; CLAUDE.md names these rounds)
 *    both_orders   the window holds a Triple before AND after the Double (`cspin_order` 1 too)
 *    jl_split      the board at 6 locks is the stick-spin board, as drawn or mirrored, in every cell but
 *                  the eight drawn J and L cells, which hold a J and an L split another way (garbage
 *                  rows under it stripped; 09-18 m13r1 had garbage before lock 6, so it was never
 *                  compared and is not in COLOUR_DISAGREE) */
const DT_NOT_STICKSPIN: Record<string, 'dt_cannon' | 'both_orders' | 'jl_split'> = {
  '2026-08-14 m3r4 yachi': 'dt_cannon',
  '2026-08-25 m9r3 yachi': 'dt_cannon',
  '2026-09-10 m7r3 pinglamb': 'both_orders',
  '2026-09-17 m7r4 yachi': 'dt_cannon',
  '2026-09-18 m2r3 pinglamb': 'both_orders',
  '2026-09-18 m7r7 pinglamb': 'jl_split',
  '2026-09-18 m13r1 pinglamb': 'jl_split',
  '2026-09-19 m5r2 pinglamb': 'jl_split',
  '2026-09-19 m5r3 pinglamb': 'jl_split',
  '2026-10-03 m7r3 yachi': 'dt_cannon',
  '2026-10-03 m7r7 yachi': 'jl_split',
  // 2026-10-20: two more jl_split, both yachi's, as drawn (COLOUR_DISAGREE), prefixes 66 and 150 —
  // the first of his Double-first rounds since 10-03 m7r7 that are not stick-spin bag-1 cases.
  '2026-10-20 m1r4 yachi': 'jl_split',
  '2026-10-20 m3r5 yachi': 'jl_split',
  // 2026-10-22: one dt_cannon, yachi's m2r7 (prefix 61), the session's one exact DT Cannon first bag.
  '2026-10-22 m2r7 yachi': 'dt_cannon',
  // 2026-10-29: two jl_split, both yachi's, as drawn (COLOUR_DISAGREE), prefixes 51 and 32.
  '2026-10-29 m1r4 yachi': 'jl_split',
  '2026-10-29 m2r5 yachi': 'jl_split',
};
/** Stick-spin bag-1 rounds with a COMPLETE opener window (0-based locks 0-21) that are not Double-first: none has a Triple
 *  in the window (the bag1.pc ones a TSD and no TST; bag1.left's 10-12 m8r4 no T-spin at all). */
const STICKSPIN_NOT_DT: string[] = [
  '2026-09-19 m3r6 yachi', '2026-10-03 m2r7 yachi', '2026-10-03 m9r6 yachi', '2026-10-03 m10r1 yachi',
  '2026-10-03 m19r6 yachi', '2026-10-09 m7r5 yachi', '2026-10-09 m9r1 yachi', '2026-10-12 m8r4 yachi',
];
/** Double-first rounds that ARE stick spin, per player: the cross-check's positive count. */
const DT_AND_STICKSPIN = { yachi: 63 };

/** The case object's key order is part of the artefact's bytes. No flag and no lock-7 piece field:
 *  the spin step records the 7th lock itself. */
const CASE_KEYS = ['session', 'file', 'round_index0', 'match', 'round', 'player', 'verified_to', 'bag1', 'bag2',
                   'pc', 'snapshots', 'bag2_near', 'deepest', 'deepest_lock', 'verified'];
const BAG1_KEYS = ['node', 'mirrored', 'lock', 'matched_variants', 'spin'];
const BAG2_KEYS = ['node', 'mirrored', 'lock', 'order_as_drawn', 'conditions_met', 'condition_met',
                   'handedness_matches_bag1', 'garbage_rows_stripped'];

const committedText = () => readFileSync(STICKSPIN.artefactPath, 'utf8');
const committed = () => JSON.parse(committedText());
let DIGESTS: RoundDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(STICKSPIN));

test('the emitter covers exactly the corpus on disk', () => {
  expect(corpus()).toEqual(SESSIONS);
  expect(committed().sessions).toEqual(SESSIONS);
  expect(committed().schema).toBe('stickspin-facts/1');
  expect(committed().report_eligible).toBe(false);
});

test('rebuilding reproduces the committed stickspin-facts.json byte for byte', () => {
  expect(serialise(build(STICKSPIN, {}, digests()))).toBe(committedText());
}, 600_000);

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

test('the cross-check: Double-first openers against stick-spin bag 1, both ways, every exception verified', () => {
  const art = committed();
  const ss = new Map<string, any>(art.cases.map((c: any) => [caseName(c), c]));
  const { rounds, dtCannon } = orderingRounds();
  const dt = [...rounds.entries()].filter(([, r]) => r.dt_order === 1).map(([k]) => k);
  // every Double-first round is stick spin or named
  const notSS = dt.filter(k => !ss.has(k));
  expect(notSS.sort()).toEqual(Object.keys(DT_NOT_STICKSPIN).sort());
  const both: Record<string, number> = {};
  for (const k of dt.filter(k => ss.has(k))) {
    const p = k.split(' ')[2]!;
    both[p] = (both[p] ?? 0) + 1;
    // a Double-first stick-spin round got past its TSS: bag1.pc or bag1.fire, never bag1.left
    expect(['bag1.pc', 'bag1.fire'], k).toContain(ss.get(k).bag1.node);
  }
  expect(both).toEqual(DT_AND_STICKSPIN);
  // and the reasons hold
  const routes = loadRoutes(STICKSPIN.routesPath);
  const left = routes.nodes.find(n => n.id === 'bag1.left')!.rows!.map(r => r.toUpperCase().replace(/-/g, '.'))
    .filter(r => r !== '..........');
  // the page's two handednesses: as drawn, and mirrored (`mirrorRows` swaps J<->L, S<->Z: bag1.right)
  const hands = [left, mirrorRows(left)];
  /** every cell as the page draws it, except that drawn J and L cells may hold either piece — and they
   *  do differ somewhere */
  const jlSplit = (b: string[]) => hands.some(h => h.length === b.length
    && h.every((r, y) => [...r].every((c, x) => c === b[y]![x] || ('JL'.includes(c) && 'JL'.includes(b[y]![x]!))))
    && h.join('/') !== b.join('/'));
  const byName = new Map(digests().map(d => [`${d.session} m${d.match}r${d.round + 1} ${d.user}`, d]));
  const cannons: Record<string, number> = {};
  for (const [k, why] of Object.entries(DT_NOT_STICKSPIN)) {
    const r = rounds.get(k)!;
    if (why === 'dt_cannon') { const cell = roundOf(k).split(' ').filter((_, i) => i !== 1).join(' '); cannons[cell] = (cannons[cell] ?? 0) + 1; }
    if (why === 'both_orders') expect(r.cspin_order, k).toBe(1);
    if (why === 'jl_split') {
      expect(jlSplit(stripGarbage(byName.get(k)!.rows[5]!).rows!), k).toBe(true);
    }
  }
  for (const [cell, n] of Object.entries(cannons)) expect(dtCannon[cell]!, cell).toBeGreaterThanOrEqual(n);
  // every colour-refused stick-spin board that is Double-first is a jl_split entry
  for (const e of COLOUR_DISAGREE) if (rounds.get(roundOf(e))?.dt_order === 1)
    expect(DT_NOT_STICKSPIN[roundOf(e)], e).toBe('jl_split');
  // the converse: every stick-spin round with a complete window is Double-first, or named with no Triple
  const notDt = art.cases.map(caseName).filter((k: string) => rounds.get(k)?.window_complete && rounds.get(k).dt_order !== 1);
  expect(notDt.sort()).toEqual([...STICKSPIN_NOT_DT].sort());
  for (const k of STICKSPIN_NOT_DT) expect(rounds.get(k).tspin_triples_window, k).toBe(0);
});

test('the named lists are exactly what the artefact holds, cell by cell', () => {
  const L = committed().lists;
  const pairs: [string, string[], string[]][] = [
    ['bag1_spin_off_page', L.bag1_spin_off_page, BAG1_SPIN_OFF_PAGE],
    ['bag2_garbage_stripped', L.bag2_garbage_stripped, BAG2_GARBAGE_STRIPPED],
    ['bag2_none_tsd_before_complete', L.bag2_none_tsd_before_complete, BAG2_NONE_TSD_BEFORE_COMPLETE],
    ['bag2_none_extra_piece', L.bag2_none_extra_piece, BAG2_NONE_EXTRA_PIECE],
    ['bag2_none_moved_piece', L.bag2_none_moved_piece, BAG2_NONE_MOVED_PIECE],
    ['bag2_none_near', L.bag2_none_near, BAG2_NONE_NEAR],
    ['bag2_none_unexplained', L.bag2_none_unexplained, BAG2_NONE_UNEXPLAINED],
    ['pc_off_page', L.pc_off_page, PC_OFF_PAGE],
    ['multi_colour_resolved_by_branch', L.multi_colour_resolved_by_branch, MULTI_COLOUR_RESOLVED_BY_BRANCH],
    ['bag2_handedness_mismatch', L.bag2_handedness_mismatch, BAG2_HANDEDNESS_MISMATCH],
    ['colour_disagree', L.colour_disagree, COLOUR_DISAGREE],
    ['pc_garbage_in_window', L.pc_garbage_in_window, PC_GARBAGE_IN_WINDOW],
  ];
  for (const [k, got, want] of pairs) checkNamedList(k, got, want);
  expect(Object.keys(L).sort()).toEqual(pairs.map(p => p[0]).sort());
  // every near entry is 2.sd, four or eight cells
  for (const e of BAG2_NONE_NEAR) expect(e, e).toMatch(/ under 2\.sd( \(mirrored\))?, [48] cells /);
});

test('per-node counts, opportunities, the mirror split and why every round stops at bag 1', () => {
  const art = committed();
  for (const [id, n] of Object.entries(NODE_CASES))
    expect(art.nodes.find((x: any) => x.id === id)?.cases, id).toBe(n);
  for (const [id, n] of Object.entries(OPPORTUNITIES))
    expect(art.nodes.find((x: any) => x.id === id)?.opportunities, id).toBe(n);
  expect(art.nodes.find((x: any) => x.id === 'bag1.left').opportunities_by_player).toEqual(BAG1_OPPORTUNITIES_BY_PLAYER);
  for (const [id, why] of Object.entries(UNMEASURED)) {
    const n = art.nodes.find((x: any) => x.id === id);
    expect(n?.measured, id).toBe(false);
    expect(n.why, id).toBe(why);
  }
  expect(art.nodes.length).toBe(Object.keys(NODE_CASES).length + Object.keys(UNMEASURED).length);
  const routes = JSON.parse(readFileSync(STICKSPIN.routesPath, 'utf8'));
  expect(art.nodes.map((n: any) => n.id)).toEqual(routes.nodes.map((n: any) => n.id));
  expect(art.outcomes).toEqual([]);
  const mirrored: Record<string, number> = {};
  for (const c of art.cases) if (c.bag1.mirrored) mirrored[c.player] = (mirrored[c.player] ?? 0) + 1;
  expect(mirrored).toEqual(MIRRORED_BAG1);
  expect(art.conditions).toEqual({});
  const stops: Record<string, number> = {};
  for (const c of art.cases) {
    expect(c.deepest, caseName(c)).toBe(c.bag1.node);
    const k = `${c.bag1.node} | ${c.bag2 ? 'sampled' : 'unsampled'} | ${c.bag2_near ? `${c.bag2_near.kind} ${c.bag2_near.cells}` : '-'}`;
    stops[k] = (stops[k] ?? 0) + 1;
  }
  expect(stops).toEqual(STOPS_AT_BAG1);
  // a round at bag1.pc / bag1.fire fired its 7th lock on that node's U slot; bag1.left's did not
  for (const c of art.cases) {
    expect(c.bag1.spin, caseName(c)).not.toBeNull();
    expect(c.bag1.spin.node, caseName(c)).toBe(c.bag1.node === 'bag1.left' ? null : c.bag1.node);
    if (c.bag1.spin.node) expect([c.bag1.spin.piece, c.bag1.spin.spin, c.bag1.spin.lines, c.bag1.lock]).toEqual(['T', 'full', 1, 6]);
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
    [...BAG1_SPIN_OFF_PAGE, ...BAG2_NONE_NEAR, ...BAG2_NONE_UNEXPLAINED, ...STICKSPIN_NOT_DT]);
});

test('the near kind is opt-in: without it, every sampled miss is unexplained and nothing else moves', () => {
  const o = build({ ...STICKSPIN, bag2Explain: true }, {}, digests());
  expect(o.lists.bag2_none_near).toEqual([]);
  expect(o.lists.bag2_none_unexplained.length).toBe(64);
  expect(o.nodes).toEqual(committed().nodes);
}, 600_000);

// ── mutants: each must turn this file red ───────────────────────────────────────────────────

const count = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).cases;
const opp = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).opportunities;
const MUTANTS: [string, Mutants, (o: any) => void][] = [
  ['mirroring disabled', { noMirror: true }, o => expect(count(o, 'bag1.pc')).toBe(75 - 2)],
  ['the spin\'s U cells read as drawn in a mirrored round', { spinMirrorUnaware: true }, o => {
    expect(count(o, 'bag1.pc')).toBe(75 - 2);
    expect(o.lists.bag1_spin_off_page.length).toBe(BAG1_SPIN_OFF_PAGE.length + 2);
  }],
  ['the bag-1 TSS stops the bag-2 sample', { spinClearStops: true }, o => {
    expect(opp(o, '2.sd')).toBe(0);
    expect(o.cases.every((c: any) => c.bag2 === null)).toBe(true);
  }],
  ['bag 2 sampled one lock early', { bag2Early: true }, o => {
    expect(opp(o, '2.sd')).not.toBe(OPPORTUNITIES['2.sd']);
    expect(o.cases.filter((c: any) => c.bag2).every((c: any) => c.bag2.lock === 11)).toBe(true);
  }],
  ['garbage refused instead of stripped at bag 2', { noGarbageStrip: true },
   o => expect(opp(o, '2.sd')).toBeLessThan(OPPORTUNITIES['2.sd']!)],
  ['the garbage stop removed', { noGarbageStop: true },
   o => expect(opp(o, 'bag1.left')).toBeGreaterThan(OPPORTUNITIES['bag1.left']!)],
  ['the J<->L / S<->Z swap removed from the mirrored condition', { noSwap: true }, o => {
    const was = new Map(committed().cases.map((c: any) => [caseName(c), c.bag2?.order_as_drawn]));
    expect(o.cases.some((c: any) => c.bag2 && c.bag2.order_as_drawn !== was.get(caseName(c)))).toBe(true);
  }],
];

/** EQUIVALENT on this corpus, measured: each leaves the artefact byte-identical, because the case that
 *  would exercise it never occurs. No hold stage (`zHoldFirst`, `noLock7Test`, `lock7MirrorUnaware`);
 *  no round reaches a bag-2 board, so nothing is scoped by one, and no Perfect Clear falls in a
 *  stick-spin round's first 40 locks (`noColour`, `unscoped`, `pcNeedsBag2`, `noGroupScope`,
 *  `pcLinesOff`); and every stick-spin session's files sort in match order (`matchFromFilename`).
 *  Named, so the day one stops being equivalent is a red build; the rules are exercised by the other
 *  three openers' tests and, for the bag-3 ones, by this opener's demos. */
const EQUIVALENT: (keyof Mutants)[] = ['zHoldFirst', 'noLock7Test', 'lock7MirrorUnaware', 'noColour', 'unscoped',
                                       'pcNeedsBag2', 'noGroupScope', 'pcLinesOff', 'matchFromFilename'];

test('every mutant changes the artefact, with the symptom its rule predicts', () => {
  const base = committedText();
  for (const [what, mut, symptom] of MUTANTS) {
    const o = build(STICKSPIN, mut, digests());
    expect(serialise(o) === base, what).toBe(false);
    symptom(o);
  }
}, 600_000);

test('the mutants this corpus cannot exercise are equivalent, and named', () => {
  const base = committedText();
  for (const m of EQUIVALENT) expect(serialise(build(STICKSPIN, { [m]: true }, digests())), m).toBe(base);
}, 600_000);
