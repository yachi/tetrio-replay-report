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
 *      byte-identical, so the day one starts to matter is a red build). There is no control: the one
 *      that stood here (trying the mirror first) could not change a byte by construction — the
 *      matcher throws on a lock matching both — so it was a comment, and `followupUnmirrored` (the
 *      follow-up slot left as drawn on a mirrored hit) is the mutant that tests the mirror instead.
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
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20']);
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
  "2026-10-12 m8r7 pinglamb lock 41 (mirrored)", "2026-10-20 m1r3 yachi lock 10", "2026-10-20 m1r8 pinglamb lock 26 (mirrored)",
  "2026-10-20 m2r4 pinglamb lock 23 (mirrored)", "2026-10-20 m2r6 pinglamb lock 36 (mirrored)", "2026-10-20 m3r2 yachi lock 46 (mirrored)",
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
  "2026-10-12 m8r7 pinglamb lock 41 (t_in_slot_not_tsd at lock 42)", "2026-10-20 m1r3 yachi lock 10 (next_t_elsewhere at lock 17)",
];

const GARBAGE_IN_WINDOW: string[] = [];

const STSD_IN_OPENER: string[] = [
  "2026-08-09 m4r4 yachi lock 12",
  // 2026-10-20 adds the second: yachi's m1r3, a stood T on lock 10 of a prefix verified to 71, no
  // garbage in the window (ZZ / Z / JJ over the slot) — not a prefix-edge effect; its follow-up T went elsewhere (lock 17)
  "2026-10-20 m1r3 yachi lock 10",
];

const WINDOW_OFF_BOARD: string[] = [];

const RECON_DROPPED_TSD: string[] = [];

/** The cross-route rounds MEASURED as a miss inside the drawn continuation, each with its counts. */
const CROSS_ROUTE_NO_HIT: string[] = [
  "2026-10-03 m4r7 yachi (no STSD hit in locks 27-34: 2 T-spin(s), 2 full TSD(s) (first at lock 27), 0 stood; an STSD hit at lock 100, past the continuation)",
  "2026-10-09 m1r5 yachi (no STSD hit in locks 27-34: 3 T-spin(s), 3 full TSD(s) (first at lock 27), 0 stood)",
  "2026-10-09 m4r4 yachi (no STSD hit in locks 27-34: 2 T-spin(s), 2 full TSD(s) (first at lock 27), 0 stood)",
  "2026-10-09 m5r1 yachi (no STSD hit in locks 27-34: 2 T-spin(s), 2 full TSD(s) (first at lock 27), 0 stood)",
  "2026-10-09 m6r5 yachi (no STSD hit in locks 27-34: 2 T-spin(s), 2 full TSD(s) (first at lock 27), 0 stood)",
  "2026-10-09 m7r1 yachi (no STSD hit in locks 27-34: 2 T-spin(s), 2 full TSD(s) (first at lock 27), 0 stood)",
  "2026-10-20 m1r4 yachi (no STSD hit in locks 27-34: 2 T-spin(s), 2 full TSD(s) (first at lock 27), 0 stood)",
  "2026-10-20 m3r5 yachi (no STSD hit in locks 27-34: 2 T-spin(s), 2 full TSD(s) (first at lock 27), 0 stood)",
];

/** The cross-route rounds kept OUT of the denominator, each with the unverified part named. */
const CROSS_ROUTE_UNSCORED: string[] = [
  "2026-10-03 m15r5 yachi (node at lock 26 is past the verified prefix, verified to lock 20)",
  "2026-10-09 m4r8 yachi (continuation runs to lock 34, verified only to lock 29; no hit before it)",
];

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5421, in_opener: 1061, mid_game: 4360 },
                    yachi: { all: 4891, in_opener: 1268, mid_game: 3623 } };
/** Per player: hits, their split, the mirrored ones, the follow-ups that fired. */
const HITS = { pinglamb: { all: 16, in_opener: 0, mid_game: 16, mirrored: 9, garbage_in_window: 0 },
               yachi: { all: 47, in_opener: 2, mid_game: 45, mirrored: 25, garbage_in_window: 0 } };
const FOLLOWUP_FIRED = { pinglamb: 13, yachi: 32 };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 0, yachi: 3 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 39, yachi: 60 }, no_roof: { pinglamb: 16, yachi: 47 },
              t_overlap: { pinglamb: 20, yachi: 49 } },
  orientation_baseline: { pinglamb: 46, yachi: 64 },
};

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  noRoof: 'no scored TSD matches everything but the roof (ablation no_roof equals the headline)',
  garbageEmpty: 'no hit window holds garbage, and no garbage cell sits where the window wants an empty cell at an anchored T',
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
  expect(n).toBe(14538);
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
  checkNamedList('cross_route_unscored', L.cross_route_unscored, CROSS_ROUTE_UNSCORED);
  checkHitPositions(art(), SESSIONS, ROOT,
    [...STSD_HITS, ...FOLLOWUP_NOT_FIRED, ...STSD_IN_OPENER, ...CROSS_ROUTE_NO_HIT, ...CROSS_ROUTE_UNSCORED]);
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
  expect(cr.rounds_reaching_node).toBe(10);
  expect(cr.rounds_scored).toBe(8);
  expect(cr.with_hit).toBe(0);
  // the continuation's last lock, re-derived: the bag harddrop draws the STSD in (3.first.cave.stsd),
  // at seven 0-based locks a bag, ends at lock 7·bag − 1
  const routes = JSON.parse(readFileSync(`${import.meta.dir}/sdpcspin-routes.json`, 'utf8'));
  const stsdNode = routes.nodes.find((n: any) => n.id === '3.first.cave.stsd');
  expect(cr.continuation.last_lock).toBe(7 * stsdNode.bag - 1);
  expect(STSD.crossRoute.continuationLastLock).toBe(cr.continuation.last_lock);
  // each outcome against the route artefact's own verified flag and verified_to: a node the route
  // reached past its prefix is never measured, and is in no denominator
  for (const c of sd.cases) {
    const s = c.snapshots.find((x: any) => x.node === '3.first.cave');
    if (!s) continue;
    const r = cr.by_round.find((x: any) => x.round === `${c.session} m${c.match}r${c.round} ${c.player}`);
    expect(r.node_lock).toBe(s.lock);
    expect(r.outcome === 'node_unverified', r.round).toBe(!s.verified);
    if (r.outcome === 'continuation_unverified') expect(r.verified_to).toBeLessThan(cr.continuation.last_lock);
    if (r.outcome === 'no_hit') expect(r.verified_to).toBeGreaterThanOrEqual(cr.continuation.last_lock);
  }
  // every STSD hit of those rounds after the node is either inside the continuation (hit_lock) or past
  // it (later_hit_lock), and the first one is the one recorded
  for (const r of cr.by_round) {
    const after = art().hits.filter((h: any) => `${h.session} m${h.match}r${h.round} ${h.player}` === r.round
      && h.lock > r.node_lock).map((h: any) => h.lock).sort((a: number, b: number) => a - b);
    expect(r.hit_lock).toBe(after.find((l: number) => l <= cr.continuation.last_lock) ?? null);
    expect(r.later_hit_lock).toBe(after.find((l: number) => l > cr.continuation.last_lock) ?? null);
  }
});

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(30);
  expect(c.rowmap_steps).toBe(252000);
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
  expect(a.cross_route.by_round.every((r: any) => r.later_hit_lock === null)).toBe(true);

  // the follow-up slot left as drawn on a mirrored hit: the hits do not move, the non-mirrored
  // follow-ups do not move, and the mirrored ones lose every fired follow-up
  a = mut({ followupUnmirrored: true });
  expect(a.hits.map((h: any) => `${h.session} ${h.file} ${h.round_index0} ${h.player} ${h.lock}`))
    .toEqual(b.hits.map((h: any) => `${h.session} ${h.file} ${h.round_index0} ${h.player} ${h.lock}`));
  a.hits.forEach((h: any, i: number) => { if (!h.mirrored) expect(h.followup).toEqual(b.hits[i].followup); });
  expect(a.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBe(0);
  expect(b.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBeGreaterThan(0);

  a = mut({ openerLt: true });
  expect(tsd(a, 'in_opener')).toBeLessThan(tsd(b, 'in_opener'));
  expect(tsd(a)).toBe(tsd(b));

  a = mut({ followupNoRowmap: true });
  expect(fired(a)).toBe(0);

  a = mut({ followupAnyT: true });
  expect(fired(a)).toBeGreaterThan(fired(b));

  for (const [m, why] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), `${m}: ${why}`).toBe(base);
}, 600_000);
