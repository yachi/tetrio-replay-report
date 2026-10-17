/**
 * The STSD technique artefact (`analysis/stsd-facts.json`, from `pipeline/sim/emit-technique-facts.ts
 * --technique stsd`; the rules are the shared `technique-facts.ts`, the profile
 * `technique-profile-stsd.ts`, the shape the gated `pipeline/openers/stsd-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now (its `inputs` carry the
 *      md5 of every session's replays and replay-facts, the transcription, the emitter files and the
 *      cross-route artefact, so any of them moving is a red build here).
 *   2. THE THIRD COPY OF THE T-SPIN LOOP. The scored set is re-derived in `technique-facts.ts` rather
 *      than imported from `emit-opener-facts.ts` (which is not edited), so it is held to that emitter's
 *      own count in every session and for every player (`donation.check`, `donation.players`).
 *   3. THE PYTHON TWIN. The window predicate is written twice — `windowMatch` here, `window_fires` in
 *      `technique_transcription.py` — and both run over every U-slot board of every committed
 *      `*-routes.json`; this test requires the TS one to reproduce exactly the boards the gate records
 *      (`cross_source.fires` + `cross_source.also`).
 *   4. NAMED lists, not bounds: every entry is a real round, resolved by (file, 0-based round) in that
 *      session's replay-facts.json with its match POSITION, and checked per (session, player).
 *   5. pinned per-player figures: the denominators, the hits and their split, the follow-up.
 *   6. mutants: each rule turned off must turn this file red with the symptom its rule predicts; the
 *      rules this corpus cannot exercise are NAMED as equivalent (measured, and asserted to stay
 *      byte-identical, so the day one starts to matter is a red build); `tryMirrorFirst` is a control.
 *
 * COST, accepted explicitly: one more full-corpus `runCaseOracle` digest in the `typescript` job
 * (about a minute and a half), as the route tests pay. The mutants reuse ONE digest.
 *
 * Run: bun test pipeline/openers/stsd.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest }
  from '../sim/technique-facts.ts';
import { STSD } from '../sim/technique-profile-stsd.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12']);
const ART_PATH = `${import.meta.dir}/../../analysis/stsd-facts.json`;
const TR = JSON.parse(readFileSync(STSD.transcriptionPath, 'utf8'));

/** Every hit: the stood T into the page's window, as drawn or mirrored. */
const STSD_HITS: string[] = [
  "2026-07-22 m4r1 yachi lock 105 (mirrored)", "2026-07-22 m5r8 pinglamb lock 25", "2026-07-22 m9r5 yachi lock 178 (mirrored)",
  "2026-07-22 m9r6 yachi lock 30", "2026-07-24 m2r1 yachi lock 32 (mirrored)", "2026-07-24 m6r8 pinglamb lock 64 (mirrored)",
  "2026-07-28 m2r1 yachi lock 64 (mirrored)", "2026-07-28 m8r8 yachi lock 97", "2026-08-01 m2r3 yachi lock 58",
  "2026-08-01 m6r1 yachi lock 132", "2026-08-09 m2r6 pinglamb lock 26", "2026-08-09 m4r4 yachi lock 12 (mirrored)",
  "2026-08-09 m5r7 yachi lock 166", "2026-08-09 m5r8 yachi lock 82 (mirrored)", "2026-08-14 m8r3 yachi lock 48",
  "2026-08-14 m10r1 yachi lock 112", "2026-08-14 m10r8 yachi lock 73 (mirrored)", "2026-08-14 m11r2 yachi lock 248 (mirrored)",
  "2026-08-14 m11r3 yachi lock 96 (mirrored)", "2026-08-14 m11r5 yachi lock 166 (mirrored)", "2026-08-19 m2r2 pinglamb lock 46 (mirrored)",
  "2026-08-25 m3r7 yachi lock 59", "2026-08-25 m7r4 pinglamb lock 37", "2026-08-25 m7r4 yachi lock 95 (mirrored)",
  "2026-08-25 m8r6 yachi lock 190", "2026-08-25 m9r2 yachi lock 39", "2026-09-10 m2r8 yachi lock 49",
  "2026-09-11 m1r4 yachi lock 138", "2026-09-11 m2r5 yachi lock 150", "2026-09-11 m3r4 yachi lock 39",
  "2026-09-17 m4r3 yachi lock 44 (mirrored)", "2026-09-18 m2r1 pinglamb lock 46 (mirrored)", "2026-09-18 m8r4 yachi lock 25",
  "2026-09-18 m8r5 yachi lock 39 (mirrored)", "2026-09-18 m11r1 yachi lock 122", "2026-09-18 m11r6 yachi lock 220 (mirrored)",
  "2026-09-18 m13r4 yachi lock 39 (mirrored)", "2026-09-18 m14r3 yachi lock 54 (mirrored)", "2026-09-18 m17r6 yachi lock 122 (mirrored)",
  "2026-09-18 m18r4 yachi lock 126 (mirrored)", "2026-09-19 m5r7 yachi lock 72 (mirrored)", "2026-09-19 m6r2 yachi lock 104 (mirrored)",
  "2026-09-19 m10r8 yachi lock 67 (mirrored)", "2026-09-19 m13r3 yachi lock 210 (mirrored)", "2026-09-19 m13r7 yachi lock 68",
  "2026-09-19 m14r3 yachi lock 102", "2026-09-19 m14r3 yachi lock 136 (mirrored)", "2026-09-19 m14r5 pinglamb lock 25",
  "2026-09-19 m15r6 yachi lock 43", "2026-09-19 m17r6 pinglamb lock 110", "2026-10-03 m4r7 yachi lock 100",
  "2026-10-03 m13r5 yachi lock 75", "2026-10-03 m17r3 pinglamb lock 143 (mirrored)", "2026-10-09 m4r2 pinglamb lock 73",
  "2026-10-12 m1r1 pinglamb lock 66", "2026-10-12 m2r1 pinglamb lock 24 (mirrored)", "2026-10-12 m5r3 yachi lock 46 (mirrored)",
  "2026-10-12 m8r7 pinglamb lock 41 (mirrored)",
];

const FOLLOWUP_NOT_FIRED: string[] = [
  "2026-07-28 m2r1 yachi lock 64 (t_in_slot_not_tsd at lock 67)", "2026-08-09 m5r8 yachi lock 82 (slot_filled_before_t at lock 83)",
  "2026-08-14 m8r3 yachi lock 48 (next_t_elsewhere at lock 50)", "2026-08-14 m10r8 yachi lock 73 (slot_filled_before_t at lock 75)",
  "2026-08-25 m8r6 yachi lock 190 (slot_filled_before_t at lock 195)", "2026-09-11 m1r4 yachi lock 138 (next_t_elsewhere at lock 142)",
  "2026-09-17 m4r3 yachi lock 44 (slot_filled_before_t at lock 48)", "2026-09-18 m2r1 pinglamb lock 46 (slot_filled_before_t at lock 47)",
  "2026-09-18 m11r6 yachi lock 220 (next_t_elsewhere at lock 227)", "2026-09-18 m14r3 yachi lock 54 (next_t_elsewhere at lock 61)",
  "2026-09-18 m17r6 yachi lock 122 (slot_filled_before_t at lock 127)", "2026-09-19 m5r7 yachi lock 72 (slot_filled_before_t at lock 74)",
  "2026-09-19 m10r8 yachi lock 67 (slot_filled_before_t at lock 69)", "2026-09-19 m14r3 yachi lock 136 (slot_filled_before_t at lock 137)",
  "2026-10-03 m4r7 yachi lock 100 (next_t_elsewhere at lock 109)", "2026-10-12 m1r1 pinglamb lock 66 (t_in_slot_not_tsd at lock 75)",
  "2026-10-12 m8r7 pinglamb lock 41 (t_in_slot_not_tsd at lock 42)",
];

const GARBAGE_IN_WINDOW: string[] = [];

const STSD_IN_OPENER: string[] = [
  "2026-08-09 m4r4 yachi lock 12",
];

const WINDOW_OFF_BOARD: string[] = [];

const RECON_DROPPED_TSD: string[] = [];

const CROSS_ROUTE_NO_HIT: string[] = [
  "2026-10-03 m15r5 yachi (no T-spin after the node, verified to lock 20)",
  "2026-10-09 m1r5 yachi (3 full TSD(s) after the node (first at lock 27), 0 stood, none in the window; verified to lock 39)",
  "2026-10-09 m4r4 yachi (5 full TSD(s) after the node (first at lock 27), 0 stood, none in the window; verified to lock 125)",
  "2026-10-09 m4r8 yachi (2 full TSD(s) after the node (first at lock 27), 0 stood, none in the window; verified to lock 29)",
  "2026-10-09 m5r1 yachi (6 full TSD(s) after the node (first at lock 27), 0 stood, none in the window; verified to lock 106)",
  "2026-10-09 m6r5 yachi (4 full TSD(s) after the node (first at lock 27), 0 stood, none in the window; verified to lock 78)",
  "2026-10-09 m7r1 yachi (2 full TSD(s) after the node (first at lock 27), 0 stood, none in the window; verified to lock 37)",
];

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5307, in_opener: 1043, mid_game: 4264 },
                    yachi: { all: 4751, in_opener: 1242, mid_game: 3509 } };
/** Per player: hits, their split, the mirrored ones, the follow-ups that fired. */
const HITS = { pinglamb: { all: 13, in_opener: 0, mid_game: 13, mirrored: 6, garbage_in_window: 0 },
               yachi: { all: 45, in_opener: 1, mid_game: 44, mirrored: 24, garbage_in_window: 0 } };
const FOLLOWUP_FIRED = { pinglamb: 10, yachi: 31 };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 0, yachi: 3 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 36, yachi: 57 }, no_roof: { pinglamb: 13, yachi: 45 },
              t_overlap: { pinglamb: 17, yachi: 46 } },
  orientation_baseline: { pinglamb: 43, yachi: 61 },
};

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  noRoof: 'no scored TSD matches everything but the roof (ablation no_roof equals the headline)',
  garbageEmpty: 'no hit window holds garbage, and no garbage cell sits where the window wants an empty cell at an anchored T',
};
/** Controls: must not change a byte. */
const CONTROL_MUTANTS: Record<string, string> = {
  tryMirrorFirst: 'an asymmetric T cannot match both as drawn and mirrored (the matcher throws if it does)',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(STSD, m, digests());

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 600_000);

test('quarantined: report_eligible false, no claim ids', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  const n = checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT);
  expect(n).toBe(14176);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin: windowMatch fires on exactly the routes boards the gate records', () => {
  const preps = TR.variants.flatMap((v: any) => prepare(TR, v));
  const got: string[] = [];
  const dir = `${import.meta.dir}`;
  for (const f of readdirSync(dir).filter(x => x.endsWith('-routes.json')).sort()) {
    for (const n of JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const cells = n.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));
      if (cells.length !== 4) continue;
      const board = n.rows.map((r: string) => [...r].map(ch => ch === '-' || ch === 'U' ? '.' : 'X').join(''));
      for (const P of preps) if (windowMatch(board, cells, P)) got.push(`${f} ${n.id} ${P.id} ${P.mirrored}`);
    }
  }
  const want = [...TR.cross_source.fires, ...TR.cross_source.also]
    .map((e: any) => `${e.file} ${e.node} ${e.variant} ${e.mirrored}`);
  expect(got.sort()).toEqual(want.sort());
  expect(want.length).toBe(3);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window).toEqual({ rows: [1, 5], cols: [0, 3] });
  expect(v.t_cells).toEqual([[3, 2], [4, 1], [4, 2], [5, 2]]);
});

test('named lists: every hit, every follow-up miss, the opener hits, the empty lists', () => {
  const L = art().lists;
  checkNamedList('stsd_hits', L.stsd_hits, STSD_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('stsd_in_opener', L.stsd_in_opener, STSD_IN_OPENER);
  checkNamedList('window_off_board', L.window_off_board, WINDOW_OFF_BOARD);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkNamedList('cross_route_no_hit', L.cross_route_no_hit, CROSS_ROUTE_NO_HIT);
  checkHitPositions(art(), SESSIONS, ROOT, [...STSD_HITS, ...FOLLOWUP_NOT_FIRED, ...STSD_IN_OPENER, ...CROSS_ROUTE_NO_HIT]);
  expect(art().hits.length).toBe(STSD_HITS.length);
});

test('pinned: denominators, hits, follow-ups, controls', () => {
  const a = art(), v = a.variants.stsd;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TSD, u).toEqual(TSD_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u].fired, u).toBe(FOLLOWUP_FIRED[u]);
    // every hit is one fired follow-up or one named miss
    expect(v.followup_by_player[u].fired + total(v.followup_by_player[u].not_fired)).toBe(HITS[u].all);
  }
  expect(v.controls).toEqual(CONTROLS);
  // the headline can never exceed an ablation that only drops a clause
  for (const k of ['no_must_empty', 'no_roof'] as const)
    for (const u of ['pinglamb', 'yachi'] as const) expect(v.controls.ablation[k][u]).toBeGreaterThanOrEqual(HITS[u].all);
});

test('cross-route: the SDPC Spin rounds that reached its STMB Cave, from that artefact itself', () => {
  const sd = JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/sdpcspin-facts.json`, 'utf8'));
  const want = sd.cases.filter((c: any) => c.snapshots.some((s: any) => s.node === '3.first.cave'))
    .map((c: any) => `${c.session} m${c.match}r${c.round} ${c.player}`).sort();
  const cr = art().cross_route;
  expect(cr.by_round.map((r: any) => r.round).sort()).toEqual(want);
  expect(cr.rounds).toBe(8);
  expect(cr.with_hit_after).toBe(1);
  // the hit after the cave is one of the STSD hits
  for (const r of cr.by_round.filter((x: any) => x.hit_lock !== null))
    expect(STSD_HITS).toContain(`${r.round} lock ${r.hit_lock}` + (art().hits.find((h: any) =>
      `${h.session} m${h.match}r${h.round} ${h.player}` === r.round && h.lock === r.hit_lock).mirrored ? ' (mirrored)' : ''));
});

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(30);
  expect(c.rowmap_steps).toBe(245899);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.stsd.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.stsd.followup_by_player).map(([u, x]: any) => [u, x.fired])));
  const tsd = (a: any, k = 'all') => a.denominators.pinglamb.TSD[k] + a.denominators.yachi.TSD[k];
  const tss = (a: any) => a.denominators.pinglamb.TSS.all + a.denominators.yachi.TSS.all;
  const b = JSON.parse(base);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };

  let a = mut({ noMirror: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(sum(a, 'all')).toBe(sum(b, 'all') - sum(b, 'mirrored'));

  a = mut({ pastPrefix: true });
  expect(a.denominators.pinglamb.unscored_past_prefix + a.denominators.yachi.unscored_past_prefix).toBe(0);
  expect(tsd(a)).toBeGreaterThan(tsd(b));
  // the whole round: the replay counters' own total (opener-facts tspin_counter_check)
  const replayTotal = SESSIONS.reduce((s, x) => s + JSON.parse(readFileSync(`${ROOT}/${x}/sim/opener-facts.json`, 'utf8'))
    .donation.counter_anchor.tspin_clears_replay, 0);
  expect(a.check.tspin_clears_scored).toBe(replayTotal);

  a = mut({ includeMini: true });
  expect(tss(a)).toBe(tss(b) + b.denominators.pinglamb.mini_TSS.all + b.denominators.yachi.mini_TSS.all);

  a = mut({ noMustEmpty: true });
  expect(sum(a, 'all')).toBe(total(b.variants.stsd.controls.ablation.no_must_empty));
  expect(sum(a, 'all')).toBeGreaterThan(sum(b, 'all'));

  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.stsd.controls.ablation.t_overlap));

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);
  expect(a.cross_route.with_hit_after).toBe(0);

  a = mut({ openerLt: true });
  expect(tsd(a, 'in_opener')).toBeLessThan(tsd(b, 'in_opener'));
  expect(tsd(a)).toBe(tsd(b));

  a = mut({ followupNoRowmap: true });
  expect(fired(a)).toBe(0);

  a = mut({ followupAnyT: true });
  expect(fired(a)).toBeGreaterThan(fired(b));

  for (const [m, why] of Object.entries({ ...EQUIVALENT, ...CONTROL_MUTANTS }))
    expect(serialise(run({ [m]: true } as Mutants)), `${m}: ${why}`).toBe(base);
}, 600_000);
