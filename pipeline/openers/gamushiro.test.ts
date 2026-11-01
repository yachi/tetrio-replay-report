/**
 * The ガムシロ積み (Gamushiro Stacking) route artefact (`analysis/gamushiro-facts.json`, from
 * `pipeline/sim/emit-route-facts.ts --opener gamushiro`; the rules are the shared `route-facts.ts`,
 * the profile `route-profile-gamushiro.ts`).
 *
 * A REFERENCE OPENER, not one this corpus plays: it is しゃけごはん's most-used opener, and over the
 * whole corpus exactly ONE round reaches its bag 1. Every other count in the artefact is a compared
 * zero, and this file pins them as zeros so that the day a second round arrives is a red build.
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE CROSS-CHECK. harddrop's opener transcription draws no Gamushiro field, so
 *      `opener-facts.json` has no `named_openers` column to compare a flag with (stick spin's case),
 *      and this profile records no flag. The independent metric that reads the same rounds from other
 *      inputs is the ordering metric (`opener-facts.json` `ordering.per_round`, decided on spin lock
 *      indices, never on a board). The page's route fires a TST first (TST → TSD → PC, and harddrop
 *      files the opener under Category:Triple Double openers), so every bag-1 round whose opener
 *      window (0-based locks 0-21) is complete must hold a Triple in the window and must NOT be
 *      Double-first; and it must be Triple-first (`cspin_order` 1) or NAMED with a reason this test
 *      verifies against the round's own locks. Only that direction is checked: Triple-first rounds
 *      are most of the corpus (the C-Spin order is the class, not this opener), so the converse would
 *      be a list of a thousand non-Gamushiro rounds and test nothing.
 *   3. NAMED lists, not bounds: every entry is a real round, resolved by (file, 0-based round) in that
 *      session's replay-facts.json with its match POSITION, and checked per (session, player).
 *   4. the per-node counts, opportunities, the mirror split and the case key order are pinned.
 *   5. mutants: each rule turned off must turn this file red, with the symptom its rule predicts —
 *      and the rules this corpus cannot exercise are NAMED as equivalent, measured, never dropped.
 *
 * COST, accepted explicitly: one more full-corpus `runCaseOracle` digest in the `typescript` job
 * (about a minute), as the other four route tests pay. The mutants reuse ONE digest.
 *
 * Run: bun test pipeline/openers/gamushiro.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, digestCorpus, corpus, kindsOf, loadRoutes, type RoundDigest, type Mutants }
  from '../sim/route-facts.ts';
import { GAMUSHIRO } from '../sim/route-profile-gamushiro.ts';
import { WINDOW_PIECES } from '../sim/opener-window.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { caseName, checkNamedList, checkPositions } from './route-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22',
   '2026-10-29', '2026-11-01']);

/** THE ONE CASE. yachi, 2026-07-22 m5r8 (`replay-2026-07-22-5.ttrm`, 0-based round 7): the page's
 *  bag 1 with the L stood on the O (bag1.l_top, 7 locks) — his 6-lock board is also the L-held
 *  board (`matched_variants`), and his 7th piece IS the L, so the placed board wins. Bag 2 is sampled
 *  (13 locks, no garbage, no clear) and matches neither 通常 form: his O sits in the cells the page
 *  gives the S, his S stands up above it, and the right-hand tower is his bag-1 L under his bag-2 L
 *  with no O on top. His TST (lock 15, 0-based) then fires into exactly the page's TST slot, after a
 *  T and a J were stacked on the board, so no subset / superset / moved explanation applies. */
const THE_CASE = '2026-07-22 m5r8 yachi';

/** No bag-2 match and no explanation of the three kinds (the board before the TST is 1 cell short
 *  of a 通常 form and 9 cells over it: see THE_CASE). MEASURED, never matched. */
const BAG2_NONE_UNEXPLAINED: string[] = [THE_CASE];

/** Measured EMPTY. No bag-1 round is the L-held board alone (the one 6-lock match placed its L 7th
 *  onto the 7-lock board), none reaches a bag-2 board, so nothing is stripped under one, no PC is filed
 *  and no colour is resolved by a group; the subset / superset / moved kinds explain nothing. A first
 *  entry is a red build to investigate. */
const L_HOLD_BAG1: string[] = [];
const L_PLACED_ELSEWHERE_BAG1: string[] = [];
const BAG2_GARBAGE_STRIPPED: string[] = [];
const BAG2_NONE_TST_BEFORE_COMPLETE: string[] = [];
const BAG2_NONE_EXTRA_PIECE: string[] = [];
const BAG2_NONE_MOVED_PIECE: string[] = [];
const PC_OFF_PAGE: string[] = [];
const BAG2_HANDEDNESS_MISMATCH: string[] = [];
const MULTI_COLOUR_RESOLVED_BY_GROUP: string[] = [];
const COLOUR_DISAGREE: string[] = [];
const PC_GARBAGE_IN_WINDOW: string[] = [];

/** Nobody mirrors it: the one case is as drawn. Pinned as a count per player (empty), not a list. */
const MIRRORED_BAG1 = {};

/** Cases per measured node: one round at bag1.l_top, every other node a COMPARED zero (the classifier
 *  samples every one of them; the demos test reaches each through it), never "not compared". */
const NODE_CASES: Record<string, number> = {
  'bag1.left': 0, 'bag1.l_top': 1, 'bag1.l_placed_elsewhere': 0,
  '2.pc4#1': 0, '2.pc4#2': 0, '2.pc4#3': 0, '2.normal#1': 0, '2.normal#2': 0,
  '2.normal.pc#1': 0, '2.normal.pc#2': 0, '2.normal.pc#3': 0, '2.normal.pc#4': 0, '2.normal.pc#5': 0,
  '2.normal.pc#6': 0, '2.normal.pc#7': 0, '2.normal.pc#8': 0, '2.normal.imperial#2': 0,
};
/** Opportunities, per player: bag 1 at 6 and 7 locks clean; bag 2 at 13 locks (the one case). The
 *  PC patterns count the rounds that reached their anchor, so they are zero with the bag-2 boards. */
const OPPORTUNITIES: Record<string, Record<string, number>> = {
  'bag1.left': { pinglamb: 1533, yachi: 1491 },
  'bag1.l_top': { pinglamb: 1461, yachi: 1154 },
  'bag1.l_placed_elsewhere': { pinglamb: 1533, yachi: 1491 },
  '2.normal#1': { pinglamb: 0, yachi: 1 },
  '2.normal#2': { pinglamb: 0, yachi: 1 },
  '2.pc4#1': { pinglamb: 0, yachi: 0 },
  '2.normal.pc#1': { pinglamb: 0, yachi: 0 },
  '2.normal.imperial#2': { pinglamb: 0, yachi: 0 },
};
/** Nodes the classifier cannot compare, and why (from the routes JSON, never a count of 0). */
const UNMEASURED: Record<string, string> = {
  'bag1.right': 'mirror_of: bag1.left', '2.normal.tst': 'illustration', '2.normal.after': 'illustration',
  '2.normal.pc.rest': 'unmatchable: inside an HTML comment, so not on the rendered page; it is 2.normal.after redrawn as an empty template that was never filled (checked)',
  '2.normal.imperial#1': 'unmatchable: 9 non-empty rows > ROWS = 8',
  '2.compromise': 'unmatchable: 10 non-empty rows > ROWS = 8',
  '2.compromise.tst': 'unmatchable: 10 non-empty rows > ROWS = 8',
};

/** The cross-check's exceptions: bag-1 rounds with a complete window that are NOT Triple-first, and
 *  why, which the test verifies on the round's own locks:
 *    tsd_after_window  the window holds the TST (fired into the page's 2.normal.tst slot) and no T-spin
 *                      Double; the round's first TSD comes after the window's last lock (21, 0-based),
 *                      so the ordering metric has no pair to order. THE_CASE: TST on lock 15, TSD on 25. */
const NOT_TRIPLE_FIRST: Record<string, 'tsd_after_window'> = { [THE_CASE]: 'tsd_after_window' };

/** The case object's key order is part of the artefact's bytes. No flag (no harddrop field). */
const CASE_KEYS = ['session', 'file', 'round_index0', 'match', 'round', 'player', 'verified_to', 'bag1', 'bag2',
                   'pc', 'snapshots', 'bag2_near', 'deepest', 'deepest_lock', 'verified'];
const BAG1_KEYS = ['node', 'mirrored', 'lock', 'lock7_piece', 'matched_variants'];
const BAG2_KEYS = ['node', 'mirrored', 'lock', 'order_as_drawn', 'conditions_met', 'condition_met',
                   'handedness_matches_bag1', 'garbage_rows_stripped'];

const committedText = () => readFileSync(GAMUSHIRO.artefactPath, 'utf8');
const committed = () => JSON.parse(committedText());
let DIGESTS: RoundDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(GAMUSHIRO));
const nameOf = (d: RoundDigest) => `${d.session} m${d.match}r${d.round + 1} ${d.user}`;

test('the emitter covers exactly the corpus on disk', () => {
  expect(corpus()).toEqual(SESSIONS);
  expect(committed().sessions).toEqual(SESSIONS);
  expect(committed().schema).toBe('gamushiro-facts/1');
  expect(committed().report_eligible).toBe(false);
});

test('rebuilding reproduces the committed gamushiro-facts.json byte for byte', () => {
  expect(serialise(build(GAMUSHIRO, {}, digests()))).toBe(committedText());
}, 600_000);

test('the two PC kinds cover every route list once', () => {
  const routes = loadRoutes(GAMUSHIRO.routesPath);
  expect(kindsOf(GAMUSHIRO, routes).map(k => [k.lists, k.lines, k.patterns.length]))
    .toEqual([[['2.normal.pc'], 8, 8], [['2.pc4'], 4, 3]]);
  expect(() => kindsOf({ ...GAMUSHIRO, pcKinds: GAMUSHIRO.pcKinds!.slice(1) }, routes)).toThrow(/pcKinds name lists/);
});

/** Every round of the ordering metric, by name, from each session's opener-facts.json. */
function orderingRounds() {
  const out = new Map<string, any>();
  for (const s of SESSIONS) {
    const of = JSON.parse(readFileSync(`${ROOT}/${s}/sim/opener-facts.json`, 'utf8'));
    const rf = JSON.parse(readFileSync(`${ROOT}/${s}/sim/replay-facts.json`, 'utf8'));
    const pos = new Map<string, number>(rf.rounds.map((r: any) => [`${r.file}#${r.round}`, r.match]));
    for (const r of of.ordering.per_round)
      out.set(`${s} m${pos.get(`${r.file}#${r.round}`)}r${r.round + 1} ${r.user}`, r);
  }
  return out;
}

test('the cross-check: every bag-1 round with a complete window holds a Triple and is not Double-first; '
   + 'Triple-first or named, every exception verified', () => {
  const art = committed();
  const rounds = orderingRounds();
  const complete = art.cases.map(caseName).filter((k: string) => rounds.get(k)?.window_complete);
  // the one case's window is complete, so the check is not vacuous
  expect(complete).toEqual([THE_CASE]);
  for (const k of complete) {
    const r = rounds.get(k);
    expect(r.dt_order, k).toBe(0);
    expect(r.tspin_triples_window, k).toBeGreaterThanOrEqual(1);
  }
  const notTripleFirst = complete.filter((k: string) => rounds.get(k).cspin_order !== 1);
  expect(notTripleFirst.sort()).toEqual(Object.keys(NOT_TRIPLE_FIRST).sort());
  // the reasons hold, on the round's own locks
  const routes = loadRoutes(GAMUSHIRO.routesPath);
  const tst = routes.nodes.find(n => n.id === '2.normal.tst')!.rows!;
  const slot = tst.flatMap((r, i) => [...r].map((ch, x) => (ch === 'U' ? `${x},${tst.length - 1 - i}` : null)))
    .filter(Boolean).sort().join(' ');
  const byName = new Map(digests().map(d => [nameOf(d), d]));
  for (const [k, why] of Object.entries(NOT_TRIPLE_FIRST)) {
    expect(why).toBe('tsd_after_window');
    const d = byName.get(k)!;
    const first = (lines: number) => d.locks.findIndex(l => l.piece === 'T' && l.spin === 'full' && l.cleared === lines);
    const iT = first(3), iD = first(2);
    expect([iT >= 0 && iT <= WINDOW_PIECES, iD > WINDOW_PIECES], k).toEqual([true, true]);
    expect(rounds.get(k).tspin_doubles_window, k).toBe(0);
    // the TST is the page's: its cells are 2.normal.tst's U cells (no garbage before it, bottom-aligned)
    expect(d.garbage.every(g => g > iT), k).toBe(true);
    const got = d.locks[iT]!.cells.map(q => `${q.col},${d.height - 1 - q.row}`).sort().join(' ');
    expect(got, k).toBe(slot);
  }
}, 600_000);

test('the named lists are exactly what the artefact holds, cell by cell', () => {
  const L = committed().lists;
  const pairs: [string, string[], string[]][] = [
    ['l_hold_bag1', L.l_hold_bag1, L_HOLD_BAG1],
    ['l_placed_elsewhere_bag1', L.l_placed_elsewhere_bag1, L_PLACED_ELSEWHERE_BAG1],
    ['bag2_garbage_stripped', L.bag2_garbage_stripped, BAG2_GARBAGE_STRIPPED],
    ['bag2_none_tst_before_complete', L.bag2_none_tst_before_complete, BAG2_NONE_TST_BEFORE_COMPLETE],
    ['bag2_none_extra_piece', L.bag2_none_extra_piece, BAG2_NONE_EXTRA_PIECE],
    ['bag2_none_moved_piece', L.bag2_none_moved_piece, BAG2_NONE_MOVED_PIECE],
    ['bag2_none_unexplained', L.bag2_none_unexplained, BAG2_NONE_UNEXPLAINED],
    ['pc_off_page', L.pc_off_page, PC_OFF_PAGE],
    ['multi_colour_resolved_by_branch', L.multi_colour_resolved_by_branch, MULTI_COLOUR_RESOLVED_BY_GROUP],
    ['bag2_handedness_mismatch', L.bag2_handedness_mismatch, BAG2_HANDEDNESS_MISMATCH],
    ['colour_disagree', L.colour_disagree, COLOUR_DISAGREE],
    ['pc_garbage_in_window', L.pc_garbage_in_window, PC_GARBAGE_IN_WINDOW],
  ];
  for (const [k, got, want] of pairs) checkNamedList(k, got, want);
  expect(Object.keys(L).sort()).toEqual(pairs.map(p => p[0]).sort());
});

test('per-node counts, opportunities, the mirror split and the one case', () => {
  const art = committed();
  for (const [id, n] of Object.entries(NODE_CASES))
    expect(art.nodes.find((x: any) => x.id === id)?.cases, id).toBe(n);
  for (const [id, o] of Object.entries(OPPORTUNITIES))
    expect(art.nodes.find((x: any) => x.id === id)?.opportunities_by_player, id).toEqual(o);
  for (const [id, why] of Object.entries(UNMEASURED)) {
    const n = art.nodes.find((x: any) => x.id === id);
    expect(n?.measured, id).toBe(false);
    expect(n.why, id).toBe(why);
  }
  expect(art.nodes.length).toBe(Object.keys(NODE_CASES).length + Object.keys(UNMEASURED).length);
  const routes = JSON.parse(readFileSync(GAMUSHIRO.routesPath, 'utf8'));
  expect(art.nodes.map((n: any) => n.id)).toEqual([...routes.nodes.map((n: any) => n.id), 'bag1.l_placed_elsewhere']);
  expect(art.outcomes).toEqual(['bag1.l_placed_elsewhere']);
  const mirrored: Record<string, number> = {};
  for (const c of art.cases) if (c.bag1.mirrored) mirrored[c.player] = (mirrored[c.player] ?? 0) + 1;
  expect(mirrored).toEqual(MIRRORED_BAG1);
  expect(art.conditions).toEqual({});
  // the one case: the placed board wins over the held one, its 7th piece is the L, bag 2 is sampled
  // and matches nothing, its order meets 2.normal#2's page condition and it built neither form
  expect(art.cases.map(caseName)).toEqual([THE_CASE]);
  const c = art.cases[0];
  expect([c.bag1.node, c.bag1.mirrored, c.bag1.lock, c.bag1.lock7_piece, c.bag1.matched_variants])
    .toEqual(['bag1.l_top', false, 6, 'L', ['bag1.l_top @7', 'bag1.left @6']]);
  expect([c.bag2.node, c.bag2.lock, c.bag2.order_as_drawn, c.bag2.conditions_met, c.bag2.garbage_rows_stripped])
    .toEqual([null, 12, 'ZJOTSLI', ['2.normal#2'], 0]);
  expect([c.pc, c.snapshots, c.bag2_near, c.deepest, c.verified]).toEqual([null, [], null, 'bag1.l_top', true]);
});

test('the case key order is pinned', () => {
  for (const c of committed().cases) {
    expect(Object.keys(c)).toEqual(CASE_KEYS);
    expect(Object.keys(c.bag1)).toEqual(BAG1_KEYS);
    if (c.bag2) expect(Object.keys(c.bag2)).toEqual(BAG2_KEYS);
  }
});

test('every case and every named entry resolves to a real round with its match POSITION', () => {
  checkPositions(committed(), SESSIONS, ROOT, [...BAG2_NONE_UNEXPLAINED, ...Object.keys(NOT_TRIPLE_FIRST)]);
});

// ── mutants: each must turn this file red ───────────────────────────────────────────────────

const count = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).cases;
const opp = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).opportunities;
const MUTANTS: [string, Mutants, (o: any) => void][] = [
  ['the hold stage tried before the placed one', { zHoldFirst: true }, o => {
    // the one case placed its L 7th: tried first, the 6-lock board files it as an outcome, not l_top
    expect(count(o, 'bag1.l_top')).toBe(0);
    expect(o.lists.l_placed_elsewhere_bag1).toEqual([THE_CASE]);
  }],
  ['bag 2 sampled one lock early', { bag2Early: true },
   o => expect(o.cases.map((c: any) => c.bag2?.lock)).toEqual([11])],
  ['garbage refused instead of stripped at bag 2', { noGarbageStrip: true },
   o => expect(o.cases.every((c: any) => !c.bag2 || !('garbage_rows_stripped' in c.bag2))).toBe(true)],
  ['the garbage stop removed', { noGarbageStop: true }, o => {
    expect(opp(o, 'bag1.left')).toBeGreaterThan(opp(committed(), 'bag1.left'));
    expect(opp(o, 'bag1.l_top')).toBeGreaterThan(opp(committed(), 'bag1.l_top'));
  }],
  ['match taken from the filename-sort index', { matchFromFilename: true },
   o => expect(o.lists.bag2_none_unexplained).not.toEqual(BAG2_NONE_UNEXPLAINED)],
];

/** EQUIVALENT on this corpus, measured: each leaves the artefact byte-identical, because the case that
 *  would exercise it never occurs. The one case is as drawn (`noMirror`, `lock7MirrorUnaware`,
 *  `noSwap`), it matches the placed board first so the hold split never decides (`noLock7Test`), and
 *  no round reaches a bag-2 board or a PC pattern (`noColour`, `unscoped`, `pcNeedsBag2`,
 *  `noGroupScope`, `pcLinesOff`); there is no bag-1 spin step (`spinMirrorUnaware`, `spinClearStops`).
 *  Named, so the day one stops being equivalent is a red build; the rules are exercised by the other
 *  four openers' tests and, for the bag-2 and PC ones, by this opener's demos. */
const EQUIVALENT: (keyof Mutants)[] = ['noMirror', 'noLock7Test', 'lock7MirrorUnaware', 'noSwap', 'noColour',
                                       'unscoped', 'pcNeedsBag2', 'noGroupScope', 'pcLinesOff', 'spinMirrorUnaware',
                                       'spinClearStops'];

test('every mutant changes the artefact, with the symptom its rule predicts', () => {
  const base = committedText();
  for (const [what, mut, symptom] of MUTANTS) {
    const o = build(GAMUSHIRO, mut, digests());
    expect(serialise(o) === base, what).toBe(false);
    symptom(o);
  }
}, 600_000);

test('the mutants this corpus cannot exercise are equivalent, and named', () => {
  const base = committedText();
  for (const m of EQUIVALENT) expect(serialise(build(GAMUSHIRO, { [m]: true }, digests())), m).toBe(base);
}, 600_000);
