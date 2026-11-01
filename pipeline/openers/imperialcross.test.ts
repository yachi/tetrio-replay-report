/**
 * The Imperial Cross technique artefact (`analysis/imperialcross-facts.json`, from `pipeline/sim/emit-technique-facts.ts
 * --technique imperialcross`; the rules are the shared `technique-facts.ts`, the profile
 * `technique-profile-imperialcross.ts`, the shape the gated `pipeline/openers/imperialcross-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and
 *      for every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN: `windowMatch` over every U-slot board of every committed `*-routes.json` fires on
 *      exactly the boards the gate records (`cross_source.fires` + `also`).
 *   4. THE ROUTE ARTEFACTS: no corpus round reached an Imperial Cross node of any route page (named, empty);
 *      the one SDPC Spin round that reached the node's parent (`3.third`) is measured over the bag harddrop
 *      draws the Imperial Cross in, and named with what happened there.
 *   5. STSD IS NOT THIS: both pages stand a T up, and anchored on the same T the two windows disagree on a
 *      cell (re-derived from both transcriptions), so the two hit sets cannot share a lock; and they do not.
 *   6. WHAT DISCRIMINATES: the T anchored and the cross's filled cells admit more than the headline; either the
 *      empty arm or the overhang alone brings it back to the headline (both measured).
 *   7. NAMED lists, not bounds; pinned per-player figures; mutants (the equivalent ones named, measured,
 *      asserted to STAY byte-identical).
 *
 * Run: bun test pipeline/openers/imperialcross.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest }
  from '../sim/technique-facts.ts';
import { IMPERIALCROSS } from '../sim/technique-profile-imperialcross.ts';
import { STSD } from '../sim/technique-profile-stsd.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29', '2026-11-01']);
const ART_PATH = `${import.meta.dir}/../../analysis/imperialcross-facts.json`;
const TR = JSON.parse(readFileSync(IMPERIALCROSS.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the stood T into the page's window, as drawn (nub right) or mirrored (nub left). */
const IMPERIALCROSS_HITS: string[] = [
  "2026-08-09 m5r8 pinglamb lock 86", "2026-08-14 m8r1 yachi lock 38 (mirrored)", "2026-08-14 m8r3 yachi lock 17",
  "2026-08-19 m6r1 pinglamb lock 24 (mirrored)", "2026-08-19 m10r5 pinglamb lock 25 (mirrored)",
  "2026-09-11 m1r4 pinglamb lock 94 (mirrored)", "2026-09-11 m4r2 yachi lock 124 (mirrored)",
  "2026-09-18 m11r1 pinglamb lock 17 (mirrored)", "2026-09-18 m18r3 pinglamb lock 22",
  "2026-10-03 m11r3 pinglamb lock 72 (mirrored)", "2026-10-29 m4r8 yachi lock 25 (mirrored)",
  "2026-11-01 m2r4 pinglamb lock 59",
];
const FOLLOWUP_NOT_FIRED: string[] = [
  "2026-08-19 m6r1 pinglamb lock 24 (slot_filled_before_t at lock 25)", "2026-08-19 m10r5 pinglamb lock 25 (round_ended)",
  "2026-09-18 m18r3 pinglamb lock 22 (slot_filled_before_t at lock 29)",
  "2026-10-29 m4r8 yachi lock 25 (slot_filled_before_t at lock 29)",
];
const IMPERIALCROSS_IN_OPENER: string[] = ["2026-08-14 m8r3 yachi lock 17", "2026-09-18 m11r1 pinglamb lock 17"];
const GARBAGE_IN_WINDOW: string[] = ["2026-08-14 m8r1 yachi lock 38"];
const RECON_DROPPED_TSD: string[] = [];
/** The full TSDs whose stood T fits the window's T but whose window leaves the board before a cell of it
 *  failed (the matcher's reading order): named, every one checked to be such a T below. */
const WINDOW_OFF_BOARD: string[] = [
  "2026-07-22 m1r1 pinglamb lock 19", "2026-07-24 m6r8 pinglamb lock 64", "2026-08-01 m5r4 pinglamb lock 19",
  "2026-08-09 m3r1 pinglamb lock 19", "2026-08-09 m5r8 yachi lock 82", "2026-08-14 m4r2 pinglamb lock 19",
  "2026-08-14 m8r4 pinglamb lock 20", "2026-08-19 m10r5 pinglamb lock 20", "2026-08-19 m4r1 pinglamb lock 20",
  "2026-08-19 m6r1 pinglamb lock 20", "2026-08-19 m6r6 pinglamb lock 20", "2026-09-10 m4r4 pinglamb lock 20",
  "2026-09-17 m2r1 pinglamb lock 20", "2026-09-18 m18r3 pinglamb lock 19", "2026-10-22 m1r5 pinglamb lock 20",
  "2026-10-22 m8r1 pinglamb lock 123", "2026-10-29 m3r2 pinglamb lock 20",
  "2026-11-01 m2r3 yachi lock 87", "2026-11-01 m6r3 yachi lock 119",
];

/** No corpus round reached an Imperial Cross node of any route page; the one SDPC Spin round that reached
 *  the node's parent, measured over the bag harddrop draws the Imperial Cross in. */
const ROUTE_IMPERIAL_REACHED: string[] = [];
const SDPC_THIRD_ROUNDS: string[] = [
  "2026-09-19 m5r3 pinglamb (3.third at lock 19; no Imperial Cross hit in locks 20-27: 1 full TSD(s) (lock 24), 0 stood)",
];

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 6396, in_opener: 1254, mid_game: 5142 },
                    yachi: { all: 5783, in_opener: 1491, mid_game: 4292 } };
/** Per player: hits, their split, the mirrored ones, the follow-ups that fired. */
const HITS = { pinglamb: { all: 8, in_opener: 1, mid_game: 7, mirrored: 5, garbage_in_window: 0 },
               yachi: { all: 4, in_opener: 1, mid_game: 3, mirrored: 3, garbage_in_window: 1 } };
const FOLLOWUP_FIRED = { pinglamb: 5, yachi: 3 };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 1, yachi: 0 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 8, yachi: 4 }, no_roof: { pinglamb: 8, yachi: 4 },
              t_overlap: { pinglamb: 8, yachi: 4 } },
  orientation_baseline: { pinglamb: 63, yachi: 80 },
};
/** What discriminates: the T anchored plus only the filled cells of the cross's three rows admits this many
 *  full TSDs that are not hits. The no_roof ablation (the cross's rows with the empty arm) and the
 *  no_must_empty one (every filled cell, the overhang's included) each give the headline exactly, so on this
 *  corpus EITHER the empty arm OR the overhang is enough, and with neither the window is this much weaker. */
const CROSS_FILLED_ONLY = 32;

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  noMustEmpty: 'no stood T at a full TSD meets every filled cell of the window and fails an empty one (the no_must_empty ablation equals the headline)',
  noRoof: 'no stood T at a full TSD meets the cross\'s rows and fails the overhang (the no_roof ablation equals the headline)',
  followupAnyT: 'every follow-up that did not fire stopped before any next T (a filled slot, or the round ended)',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(IMPERIALCROSS, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;
const hitKeys = () => new Set(art().hits.map((h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`));
const keyOf = (d: TechDigest, lock: number) => `${d.session}|${d.file}|${d.round}|${d.user}|${lock}`;

/** Every scored T-spin, exactly as the matcher scores it: inside the prefix, the reconstruction agreeing
 *  on a non-empty set of rows. */
function scored(d: TechDigest) {
  const out: { i: number; rows: number[]; lk: TechDigest['locks'][number]; board: string[] }[] = [];
  for (const t of d.tspins) {
    if (t.i > d.v) continue;
    const lk = d.locks[t.i]!;
    const withT = t.board.map(s => [...s].map(x => x !== '.'));
    for (const q of lk.cells) withT[q.row]![q.col] = true;
    const rows: number[] = [];
    for (let r = 0; r < H; r++) if (withT[r]!.every(Boolean)) rows.push(r);
    const theirs = [...lk.clearedRows].sort((a, b) => a - b);
    if (rows.length !== theirs.length || !rows.every((x, k) => x === theirs[k]) || !rows.length) continue;
    out.push({ i: t.i, rows, lk, board: t.board });
  }
  return out;
}

/** A stood T: its stem column and the side its nub points to, or null. */
function stoodOf(cells: { row: number; col: number }[]) {
  const cs = [...new Set(cells.map(q => q.col))].sort((a, b) => a - b);
  const rs = [...new Set(cells.map(q => q.row))].sort((a, b) => a - b);
  if (cs.length !== 2 || rs.length !== 3) return null;
  const nub = cells.find(q => cells.filter(x => x.col === q.col).length === 1)!;
  const stem = cs.find(c => c !== nub.col)!;
  if (nub.row !== rs[1]) return null;
  return { stem, top: rs[0]!, dir: nub.col > stem ? 1 : -1 };
}

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 600_000);

test('quarantined: report_eligible false, no claim ids', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
  expect(a.cross_route).toBeUndefined();
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  const n = checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT);
  expect(n).toBe(17205);
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
  expect(want.length).toBe(2);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [1, 5], cols: [0, 3] });
  expect(v.t_cells).toEqual([[3, 2], [4, 2], [4, 3], [5, 2]]);
  expect(v.followup.lines).toBe(2);
  expect(v.followup.drawn_lines).toBe(1);
  expect(TR.empty_letters).toBe('B');
});

test('named lists: every hit, every follow-up miss, the opener hits, garbage, off the board', () => {
  const L = art().lists;
  checkNamedList('imperialcross_hits', L.imperialcross_hits, IMPERIALCROSS_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('imperialcross_in_opener', L.imperialcross_in_opener, IMPERIALCROSS_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkNamedList('window_off_board', L.window_off_board, WINDOW_OFF_BOARD);
  checkHitPositions(art(), SESSIONS, ROOT, [...IMPERIALCROSS_HITS, ...FOLLOWUP_NOT_FIRED, ...IMPERIALCROSS_IN_OPENER,
                                            ...GARBAGE_IN_WINDOW]);
  expect(art().hits.length).toBe(IMPERIALCROSS_HITS.length);
});

test('window_off_board: every entry a stood T at a full TSD whose window leaves the board, not a hit', () => {
  const v = TR.variants[0];
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  // in the spin board's frame the stem is column 2, the T's top row 3, the nub to the right (+1)
  const S = 2, TOP = 3;
  const hits = hitKeys();
  const want = new Set<string>();
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
    const st = stoodOf(s.lk.cells);
    if (!st || hits.has(keyOf(d, s.i))) continue;
    const rowsOff = st.top + (r0 - TOP) < 0 || st.top + (r1 - TOP) >= H;
    // as drawn (nub right): columns stem-2 .. stem+1; mirrored (nub left): stem-1 .. stem+2
    const off = st.dir === 1 ? st.stem + (c0 - S) < 0 || st.stem + (c1 - S) > 9
                             : st.stem - (c1 - S) < 0 || st.stem - (c0 - S) > 9;
    if (rowsOff || off) want.add(nameOf(d, s.i));
  }
  for (const x of WINDOW_OFF_BOARD) expect(want.has(x), x).toBe(true);
});

test('pinned: denominators, hits, follow-ups, controls', () => {
  const a = art(), v = a.variants.imperialcross;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TSD, u).toEqual(TSD_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u].fired, u).toBe(FOLLOWUP_FIRED[u]);
    expect(v.followup_by_player[u].fired + total(v.followup_by_player[u].not_fired)).toBe(HITS[u].all);
  }
  expect(v.controls).toEqual(CONTROLS);
  // every hit is a stood T: the orientation baseline holds them all
  for (const u of ['pinglamb', 'yachi'] as const) expect(v.controls.orientation_baseline[u]).toBeGreaterThanOrEqual(HITS[u].all);
});

test('STSD is not this: anchored on the same stood T, the two windows disagree, and no lock is a hit of both', () => {
  const st = JSON.parse(readFileSync(STSD.transcriptionPath, 'utf8'));
  const ic = prepare(TR, TR.variants[0]), sd = prepare(st, st.variants[0]);
  // anchor both on one T (the nub-left one: STSD as drawn, Imperial Cross mirrored), then compare every
  // cell both windows read
  const norm = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  const a = norm(sd[0]!), b = norm(ic[1]!);
  expect(a.T).toBe(b.T);
  const clash = [...a.cells].filter(([k, v]) => b.cells.has(k) && b.cells.get(k) !== v && v !== 'T');
  expect(clash.length).toBeGreaterThan(0);
  // and the measured intersection
  const sh = JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/stsd-facts.json`, 'utf8')).hits;
  const k = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
  const mine = hitKeys();
  expect(sh.filter((h: any) => mine.has(k(h)))).toEqual([]);
});

test('what discriminates: the T anchored with the cross\'s filled cells alone, against the headline', () => {
  const v = TR.variants[0];
  const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || (x.v === '#' && x.r >= 3)) }));
  const extra: string[] = [];
  const hits = hitKeys();
  let got = 0;
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
    if (!preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) continue;
    got++;
    if (!hits.has(keyOf(d, s.i))) extra.push(nameOf(d, s.i));
  }
  // every hit passes the weaker predicate; what it adds is the overhang's and the empty cells' work
  expect(got - extra.length).toBe(art().hits.length);
  expect(extra.length).toBe(CROSS_FILLED_ONLY);
  // and either half alone restores the headline: the two ablations that drop the other half
  const ab = art().variants.imperialcross.controls.ablation;
  expect(total(ab.no_roof)).toBe(art().hits.length);
  expect(total(ab.no_must_empty)).toBe(art().hits.length);
});

test('cross-check: the route artefacts\' rounds that reached an Imperial Cross node, or its SDPC Spin parent', () => {
  const A = `${import.meta.dir}/../../analysis`;
  const reached: string[] = [];
  // the scan reads EVERY string of a case (snapshots, pc, deepest, bag2 …), not one field: a node recorded in a
  // field this test did not name, or a renamed field, must not empty the scan while the named list is empty.
  // `snapshots` is required, never defaulted: a case without it is a red build, not a case with none.
  const strings = (o: any, path: string, out: [string, string][]) => {
    if (typeof o === 'string') out.push([path, o]);
    else if (Array.isArray(o)) o.forEach((x, i) => strings(x, `${path}[${i}]`, out));
    else if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) strings(v, path ? `${path}.${k}` : k, out);
    return out;
  };
  const files = readdirSync(A).filter(x => /^(sdpcspin|stickspin|gamushiro|honey-cup|mountainous2|stray-cannon)-facts\.json$/.test(x)).sort();
  expect(files.length).toBe(6);
  for (const f of files) {
    const cases = JSON.parse(readFileSync(`${A}/${f}`, 'utf8')).cases;
    expect(Array.isArray(cases) && cases.length > 0, f).toBe(true);
    for (const c of cases) {
      expect(Array.isArray(c.snapshots), `${f} ${c.session} m${c.match}r${c.round} ${c.player}: no snapshots`).toBe(true);
      for (const [p, s] of strings(c, '', [])) if (/imperial/.test(s)) reached.push(`${f} ${c.session} m${c.match}r${c.round} ${c.player} ${p}=${s}`);
    }
  }
  // control: the scan's pattern names real route nodes on each route page that draws an Imperial Cross, so an
  // empty result is a measurement over nodes that exist, not a regex that can match nothing
  for (const o of ['gamushiro', 'sdpcspin', 'stickspin'])
    expect(JSON.parse(readFileSync(`${import.meta.dir}/${o}-routes.json`, 'utf8')).nodes
      .some((n: any) => /imperial/.test(n.id)), o).toBe(true);
  checkNamedList('route_imperial_reached', reached, ROUTE_IMPERIAL_REACHED);
  // the SDPC Spin parent: harddrop draws the Imperial Cross in bag 4 of the route, so the drawn continuation
  // ends at the last lock of bag 4 (0-based, seven locks a bag)
  const routes = JSON.parse(readFileSync(`${import.meta.dir}/sdpcspin-routes.json`, 'utf8'));
  const node = routes.nodes.find((n: any) => n.id === '3.third.imperial');
  expect(node.parent).toBe('3.third');
  const last = 7 * node.bag - 1;
  const sd = JSON.parse(readFileSync(`${A}/sdpcspin-facts.json`, 'utf8'));
  const hits = hitKeys();
  const out: string[] = [];
  for (const c of sd.cases) {
    const s = c.snapshots.find((x: any) => x.node === '3.third');
    if (!s) continue;
    const d = digests().find(x => x.session === c.session && x.file === c.file && x.round === c.round_index0 && x.user === c.player)!;
    expect(d, `${c.session} ${c.file} ${c.round_index0}`).toBeDefined();
    expect(s.verified && s.lock <= d.v && last <= d.v).toBe(true);
    const inside = [...hits].filter(k => k.startsWith(`${d.session}|${d.file}|${d.round}|${d.user}|`))
      .map(k => +k.split('|')[4]!).filter(l => l > s.lock && l <= last);
    const tsd = d.tspins.filter(t => t.i > s.lock && t.i <= last && d.locks[t.i]!.spin === 'full' && d.locks[t.i]!.cleared === 2);
    const stood = tsd.filter(t => stoodOf(d.locks[t.i]!.cells)).length;
    out.push(`${d.session} m${d.match}r${d.round + 1} ${d.user} (3.third at lock ${s.lock}; `
      + (inside.length ? `Imperial Cross hit at lock ${inside[0]})`
         : `no Imperial Cross hit in locks ${s.lock + 1}-${last}: ${tsd.length} full TSD(s)`
           + `${tsd.length ? ` (lock ${tsd.map(t => t.i).join(', ')})` : ''}, ${stood} stood)`));
  }
  checkNamedList('sdpc_third_rounds', out, SDPC_THIRD_ROUNDS);
});

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(32);
  expect(c.rowmap_steps).toBe(300597);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.imperialcross.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.imperialcross.followup_by_player).map(([u, x]: any) => [u, x.fired])));
  const tsd = (a: any, k = 'all') => a.denominators.pinglamb.TSD[k] + a.denominators.yachi.TSD[k];
  const tss = (a: any) => a.denominators.pinglamb.TSS.all + a.denominators.yachi.TSS.all;
  const b = JSON.parse(base);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  const k = (h: any) => `${h.session} ${h.file} ${h.round_index0} ${h.player} ${h.lock}`;
  let a = mut({ noMirror: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(sum(a, 'all')).toBe(sum(b, 'all') - sum(b, 'mirrored'));

  a = mut({ pastPrefix: true });
  expect(a.denominators.pinglamb.unscored_past_prefix + a.denominators.yachi.unscored_past_prefix).toBe(0);
  expect(tsd(a)).toBeGreaterThan(tsd(b));
  expect(sum(a, 'all')).toBeGreaterThan(sum(b, 'all'));
  const replayTotal = SESSIONS.reduce((s, x) => s + JSON.parse(readFileSync(`${ROOT}/${x}/sim/opener-facts.json`, 'utf8'))
    .donation.counter_anchor.tspin_clears_replay, 0);
  expect(a.check.tspin_clears_scored).toBe(replayTotal);

  a = mut({ includeMini: true });
  expect(tss(a)).toBe(tss(b) + b.denominators.pinglamb.mini_TSS.all + b.denominators.yachi.mini_TSS.all);

  // no anchor: the count is the t_overlap ablation's — which on this corpus EQUALS the headline (measured), so
  // that line alone cannot tell the mutant from the baseline. What does: with no anchor there is no window
  // offset, so nothing can leave the board and no follow-up can be carried (every hit is `not_anchored`).
  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.imperialcross.controls.ablation.t_overlap));
  expect(a.lists.window_off_board).toEqual([]);
  expect(b.lists.window_off_board.length).toBeGreaterThan(0);
  expect(fired(a)).toBe(0);
  expect(fired(b)).toBeGreaterThan(0);
  expect(a.hits.length).toBeGreaterThan(0);
  expect(a.hits.every((h: any) => h.followup.reason === 'not_anchored')).toBe(true);

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  // garbage read as EMPTY: the one hit with garbage in its window is lost (its window needs those cells filled)
  a = mut({ garbageEmpty: true });
  expect(a.hits.map(k)).toEqual(b.hits.filter((h: any) => !h.garbage_in_window).map(k));

  a = mut({ followupUnmirrored: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  a.hits.forEach((h: any, i: number) => { if (!h.mirrored) expect(h.followup).toEqual(b.hits[i].followup); });
  expect(a.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBe(0);
  expect(b.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBeGreaterThan(0);

  a = mut({ openerLt: true });
  expect(tsd(a, 'in_opener')).toBeLessThan(tsd(b, 'in_opener'));
  expect(tsd(a)).toBe(tsd(b));

  // no row map: the hit's OWN clear straddles the slot (one cleared row between the slot's arm and its top,
  // one under it), so without the map not one follow-up lands
  a = mut({ followupNoRowmap: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBe(0);
  expect(fired(b)).toBeGreaterThan(0);

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);
