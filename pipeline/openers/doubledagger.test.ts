/**
 * The Double Dagger technique artefact (`analysis/doubledagger-facts.json`, from `pipeline/sim/emit-technique-facts.ts
 * --technique doubledagger`; the rules are the shared `technique-facts.ts`, the profile
 * `technique-profile-doubledagger.ts`, the shape the gated `pipeline/openers/doubledagger-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and
 *      for every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN: `windowMatch` over every U-slot board of every committed `*-routes.json` fires on
 *      exactly the boards the gate records (`cross_source.fires` + `also`): harddrop's SDPC Spin, another
 *      author, draws this shape in its second C-Spin build.
 *   4. THE ROUTE ARTEFACTS: the one SDPC Spin round that reached that build (`3.second`) is measured over the
 *      bag harddrop draws the shape in, and named with what happened there.
 *   5. STMB CAVE IS NOT THIS: both pages lay the T flat, nub down; anchored on the same T the two windows
 *      disagree on a cell (re-derived from both transcriptions), so the two hit sets cannot share a lock, and
 *      they do not.
 *   6. WHAT DISCRIMINATES: measured per window part, with the T anchored (the cleared rows alone, the overhang
 *      row alone, the lower slot alone), against the headline.
 *   7. NAMED lists, not bounds; pinned per-player figures; mutants (the equivalent ones named, measured,
 *      asserted to STAY byte-identical).
 *
 * window_off_board is not listed entry by entry: it is every flat, nub-down T at a TSD whose window leaves the
 * board before the matcher found a mismatch, thousands of them (the window holds two rows under the nub). It
 * is pinned per player as a count, and every entry is checked to be such a T with its window off the board in
 * at least one hand and not a hit (STMB Cave's treatment, for the same reason).
 *
 * Run: bun test pipeline/openers/doubledagger.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest }
  from '../sim/technique-facts.ts';
import { DOUBLEDAGGER } from '../sim/technique-profile-doubledagger.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12']);
const ART_PATH = `${import.meta.dir}/../../analysis/doubledagger-facts.json`;
const TR = JSON.parse(readFileSync(DOUBLEDAGGER.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the flat T into the page's window, as drawn (overhang left) or mirrored (overhang right). */
const DOUBLEDAGGER_HITS: string[] = [
  "2026-07-24 m2r3 pinglamb lock 131 (mirrored)", "2026-07-24 m6r5 pinglamb lock 67 (mirrored)",
  "2026-07-28 m7r1 yachi lock 98 (mirrored)", "2026-07-28 m7r6 pinglamb lock 33 (mirrored)",
  "2026-08-01 m1r4 pinglamb lock 34 (mirrored)", "2026-08-01 m3r5 pinglamb lock 24 (mirrored)",
  "2026-08-01 m3r7 pinglamb lock 35", "2026-08-01 m3r8 pinglamb lock 34 (mirrored)", "2026-08-01 m5r7 pinglamb lock 60",
  "2026-08-09 m6r2 pinglamb lock 82", "2026-08-09 m6r2 pinglamb lock 93 (mirrored)", "2026-08-14 m3r4 yachi lock 208",
  "2026-08-14 m4r5 yachi lock 47", "2026-08-14 m4r8 yachi lock 83 (mirrored)", "2026-08-14 m10r6 yachi lock 23",
  "2026-08-19 m2r5 pinglamb lock 37", "2026-08-19 m4r1 pinglamb lock 25 (mirrored)", "2026-08-25 m2r7 pinglamb lock 116",
  "2026-09-03 m2r2 pinglamb lock 81", "2026-09-03 m4r2 pinglamb lock 67 (mirrored)", "2026-09-10 m5r9 pinglamb lock 36",
  "2026-09-11 m2r5 pinglamb lock 133 (mirrored)", "2026-09-11 m2r6 pinglamb lock 50 (mirrored)",
  "2026-09-11 m4r1 pinglamb lock 148", "2026-09-11 m4r2 yachi lock 26 (mirrored)",
  "2026-09-17 m7r4 pinglamb lock 48 (mirrored)", "2026-09-18 m9r3 yachi lock 202 (mirrored)",
  "2026-09-18 m15r1 yachi lock 64 (mirrored)", "2026-09-19 m1r8 pinglamb lock 64 (mirrored)",
  "2026-09-19 m2r3 pinglamb lock 45 (mirrored)", "2026-09-19 m14r6 pinglamb lock 37",
  "2026-09-19 m17r2 pinglamb lock 32 (mirrored)", "2026-10-03 m7r7 yachi lock 80 (mirrored)",
  "2026-10-09 m1r9 yachi lock 45 (mirrored)", "2026-10-09 m4r7 pinglamb lock 89 (mirrored)",
  "2026-10-09 m6r5 pinglamb lock 36 (mirrored)", "2026-10-09 m7r5 pinglamb lock 37", "2026-10-09 m11r3 yachi lock 74",
];
const FOLLOWUP_NOT_FIRED: string[] = [
  "2026-08-01 m3r8 pinglamb lock 34 (slot_filled_before_t at lock 38)",
  "2026-08-14 m3r4 yachi lock 208 (past_verified at lock 213)",
  "2026-08-14 m10r6 yachi lock 23 (next_t_elsewhere at lock 26)",
  "2026-08-25 m2r7 pinglamb lock 116 (slot_filled_before_t at lock 117)",
  "2026-09-19 m14r6 pinglamb lock 37 (round_ended)",
  "2026-10-09 m1r9 yachi lock 45 (slot_filled_before_t at lock 46)",
  "2026-10-09 m6r5 pinglamb lock 36 (slot_filled_before_t at lock 43)",
];
const GARBAGE_IN_WINDOW: string[] = [
  "2026-07-24 m2r3 pinglamb lock 131", "2026-08-09 m6r2 pinglamb lock 82", "2026-08-14 m3r4 yachi lock 208",
  "2026-08-14 m4r8 yachi lock 83", "2026-08-19 m2r5 pinglamb lock 37", "2026-09-03 m4r2 pinglamb lock 67",
  "2026-09-19 m1r8 pinglamb lock 64", "2026-09-19 m2r3 pinglamb lock 45",
];
const DOUBLEDAGGER_IN_OPENER: string[] = [];
const RECON_DROPPED_TSD: string[] = [];
/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 1284, yachi: 1329 };

/** The one SDPC Spin round that reached the second C-Spin build (`3.second`), measured over the bag harddrop
 *  draws the Double Dagger boards in. */
const SDPC_SECOND_ROUNDS: string[] = [
  "2026-09-19 m5r2 pinglamb (3.second at lock 19, verified to lock 73; no Double Dagger hit in locks 20-34: 2 full TSD(s) (lock 27, 33), 2 flat nub-down)",
];

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5307, in_opener: 1043, mid_game: 4264 },
                    yachi: { all: 4751, in_opener: 1242, mid_game: 3509 } };
/** Per player: hits, their split, the mirrored ones, the follow-ups that fired. */
const HITS = { pinglamb: { all: 27, in_opener: 0, mid_game: 27, mirrored: 17, garbage_in_window: 6 },
               yachi: { all: 11, in_opener: 0, mid_game: 11, mirrored: 7, garbage_in_window: 2 } };
const FOLLOWUP_FIRED = { pinglamb: 23, yachi: 8 };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 2, yachi: 1 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 3221, yachi: 2749 }, no_roof: { pinglamb: 27, yachi: 11 },
              t_overlap: { pinglamb: 36, yachi: 11 } },
  orientation_baseline: { pinglamb: 43, yachi: 61 },
};
/** What discriminates, measured: full TSDs (not only hits) whose anchored T meets ONE part of the window —
 *  the two cleared rows, the overhang row above them, or the lower slot under them. The lower slot alone gives
 *  exactly the headline's hits; the cleared rows (entailed by the clear) and the overhang row (which a TSD slot
 *  nearly always has) admit almost every full TSD. The overhang still has work to do: it is what tells the two
 *  hands apart (the `noRoof` mutant makes a lock match both, and the matcher refuses it). */
const PART_ONLY = { cleared: 9954, overhang: 9952, lower: 38 };

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(DOUBLEDAGGER, m, digests());
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

/** A flat T pointing down: its nub, or null. */
function nubOf(cells: { row: number; col: number }[]) {
  const top = Math.min(...cells.map(q => q.row));
  const up = cells.filter(q => q.row === top), down = cells.filter(q => q.row !== top);
  if (up.length !== 3 || down.length !== 1) return null;
  const n = down[0]!, cs = up.map(q => q.col).sort((a, b) => a - b);
  if (n.row !== top + 1 || cs[0] !== n.col - 1 || cs[2] !== n.col + 1) return null;
  return n;
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
  expect(want.length).toBe(4);
  expect(TR.cross_source.labelled_not_fired).toEqual([]);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window_basis).toBeUndefined();
  expect(v.window).toEqual({ rows: [1, 5], cols: [2, 5] });
  expect(v.t_cells).toEqual([[2, 3], [2, 4], [2, 5], [3, 4]]);
  expect(v.roof_cells).toEqual([[1, 2], [1, 3]]);
  expect(v.followup.t_cells_pre_clear).toEqual([[4, 3], [4, 4], [4, 5], [5, 4]]);
  expect(TR.empty_letters).toBe('Bp');
  // the window the matcher prepares reads the empty letters as empty: no B or p cell is a must-be-filled one
  const P = prepare(TR, v)[0]!;
  const spin = TR.nodes.find((n: any) => n.id === v.board).rows;
  for (const x of P.cells) if (x.v === '#') expect(spin[x.r][x.c]).not.toMatch(/[-Bp]/);
});

test('named lists: every hit, every follow-up miss, the opener hits, garbage, the empty lists', () => {
  const L = art().lists;
  checkNamedList('doubledagger_hits', L.doubledagger_hits, DOUBLEDAGGER_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('doubledagger_in_opener', L.doubledagger_in_opener, DOUBLEDAGGER_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkHitPositions(art(), SESSIONS, ROOT, [...DOUBLEDAGGER_HITS, ...FOLLOWUP_NOT_FIRED, ...GARBAGE_IN_WINDOW]);
  expect(art().hits.length).toBe(DOUBLEDAGGER_HITS.length);
});

test('window_off_board: pinned per player, every entry a flat nub-down T whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  for (const u of ['pinglamb', 'yachi'] as const)
    expect(L.filter(x => x.split(' ')[2] === u).length, u).toBe(WINDOW_OFF_BOARD[u]);
  const v = TR.variants[0];
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  const [nr, nc] = v.t_cells.reduce((a: number[], b: number[]) => (b[0]! > a[0]! ? b : a));
  const want = new Set<string>();
  const hits = hitKeys();
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
    const n = nubOf(s.lk.cells);
    if (!n || hits.has(keyOf(d, s.i))) continue;
    const rowsOff = n.row + (r0 - nr) < 0 || n.row + (r1 - nr) >= H;
    const drawnOff = rowsOff || n.col + (c0 - nc) < 0 || n.col + (c1 - nc) > 9;
    const mirrOff = rowsOff || n.col - (c1 - nc) < 0 || n.col - (c0 - nc) > 9;
    if (drawnOff || mirrOff) want.add(nameOf(d, s.i));
  }
  for (const x of L) expect(want.has(x), x).toBe(true);
  expect(new Set(L).size).toBe(L.length);
});

test('pinned: denominators, hits, follow-ups, controls', () => {
  const a = art(), v = a.variants.doubledagger;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TSD, u).toEqual(TSD_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u].fired, u).toBe(FOLLOWUP_FIRED[u]);
    expect(v.followup_by_player[u].fired + total(v.followup_by_player[u].not_fired)).toBe(HITS[u].all);
  }
  expect(v.controls).toEqual(CONTROLS);
  for (const k of ['no_must_empty', 'no_roof'] as const)
    for (const u of ['pinglamb', 'yachi'] as const) expect(v.controls.ablation[k][u]).toBeGreaterThanOrEqual(HITS[u].all);
});

test('STMB Cave is not this: anchored on the same flat T, the two windows disagree, and no lock is a hit of both', () => {
  const st = JSON.parse(readFileSync(STMBCAVE.transcriptionPath, 'utf8'));
  const norm = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  // every pairing of hands: the T is symmetric, so each window in each hand against the other in each hand
  for (const a of prepare(TR, TR.variants[0]).map(norm)) for (const b of prepare(st, st.variants[0]).map(norm)) {
    expect(a.T).toBe(b.T);
    const clash = [...a.cells].filter(([k, v]) => b.cells.has(k) && b.cells.get(k) !== v && v !== 'T');
    expect(clash.length).toBeGreaterThan(0);
  }
  const sh = JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/stmbcave-facts.json`, 'utf8')).hits;
  const k = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
  const mine = hitKeys();
  expect(sh.filter((h: any) => mine.has(k(h)))).toEqual([]);
});

test('what discriminates: each part of the window alone, with the T anchored, against the headline', () => {
  const v = TR.variants[0];
  const [top] = v.t_cells[0]!;          // the T's row; the nub row is under it
  const parts: Record<keyof typeof PART_ONLY, (r: number) => boolean> = {
    cleared: r => r === top || r === top + 1, overhang: r => r < top, lower: r => r > top + 1,
  };
  const hits = hitKeys();
  const got: Record<string, number> = {};
  for (const [name, keep] of Object.entries(parts)) {
    const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || keep(x.r)) }));
    let n = 0, hitsIn = 0;
    for (const d of digests()) for (const s of scored(d)) {
      if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
      if (!preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) continue;
      n++;
      if (hits.has(keyOf(d, s.i))) hitsIn++;
    }
    expect(hitsIn, name).toBe(art().hits.length);   // every hit passes each weaker predicate
    got[name] = n;
  }
  expect(got).toEqual(PART_ONLY);
  expect(PART_ONLY.lower).toBe(art().hits.length);
  // and the overhang row is decided by the rest on this corpus: the no_roof ablation equals the headline
  const ab = art().variants.doubledagger.controls.ablation;
  expect(total(ab.no_roof)).toBe(art().hits.length);
});

test('cross-check: the SDPC Spin round that reached the second C-Spin build, over the bag the shape is drawn in', () => {
  const A = `${import.meta.dir}/../../analysis`;
  const routes = JSON.parse(readFileSync(`${import.meta.dir}/sdpcspin-routes.json`, 'utf8'));
  const drawn = TR.cross_source.fires.map((e: any) => routes.nodes.find((n: any) => n.id === e.node));
  // every board harddrop draws the shape on is a bag-5 board of the same build
  expect(new Set(drawn.map((n: any) => n.bag))).toEqual(new Set([5]));
  expect(new Set(drawn.map((n: any) => n.parent))).toEqual(new Set(['3.second.cspin']));
  const build = routes.nodes.find((n: any) => n.id === '3.second.cspin');
  expect(build.parent).toBe('3.second');
  const last = 7 * 5 - 1;
  const sd = JSON.parse(readFileSync(`${A}/sdpcspin-facts.json`, 'utf8'));
  const hits = hitKeys();
  const out: string[] = [];
  for (const c of sd.cases) {
    const s = c.snapshots.find((x: any) => x.node === '3.second');
    if (!s) continue;
    const d = digests().find(x => x.session === c.session && x.file === c.file && x.round === c.round_index0 && x.user === c.player)!;
    expect(d, `${c.session} ${c.file} ${c.round_index0}`).toBeDefined();
    const inside = [...hits].filter(k => k.startsWith(`${d.session}|${d.file}|${d.round}|${d.user}|`))
      .map(k => +k.split('|')[4]!).filter(l => l > s.lock && l <= last);
    const tsd = d.tspins.filter(t => t.i > s.lock && t.i <= last && d.locks[t.i]!.spin === 'full' && d.locks[t.i]!.cleared === 2);
    const flat = tsd.filter(t => nubOf(d.locks[t.i]!.cells)).length;
    out.push(`${d.session} m${d.match}r${d.round + 1} ${d.user} (3.second at lock ${s.lock}, verified to lock ${d.v}; `
      + (!s.verified || s.lock > d.v ? 'node past the verified prefix)'
         : inside.length ? `Double Dagger hit at lock ${inside[0]})`
         : `no Double Dagger hit in locks ${s.lock + 1}-${last}: ${tsd.length} full TSD(s)`
           + `${tsd.length ? ` (lock ${tsd.map(t => t.i).join(', ')})` : ''}, ${flat} flat nub-down)`));
  }
  checkNamedList('sdpc_second_rounds', out, SDPC_SECOND_ROUNDS);
});

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(30);
  expect(c.rowmap_steps).toBe(245899);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.doubledagger.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.doubledagger.followup_by_player).map(([u, x]: any) => [u, x.fired])));
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
  const replayTotal = SESSIONS.reduce((s, x) => s + JSON.parse(readFileSync(`${ROOT}/${x}/sim/opener-facts.json`, 'utf8'))
    .donation.counter_anchor.tspin_clears_replay, 0);
  expect(a.check.tspin_clears_scored).toBe(replayTotal);

  a = mut({ includeMini: true });
  expect(tss(a)).toBe(tss(b) + b.denominators.pinglamb.mini_TSS.all + b.denominators.yachi.mini_TSS.all);

  // the flat T is symmetric: without the must-empty cells, or without the overhang row above the T, a lock
  // with both of the lower slot's walls filled matches both hands, and the matcher refuses it — the overhang
  // decides no hit (the no_roof ablation equals the headline) but it is half of what decides the HAND
  expect(() => run({ noMustEmpty: true })).toThrow(/matches as drawn AND mirrored/);
  expect(() => run({ noRoof: true })).toThrow(/matches as drawn AND mirrored/);

  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.doubledagger.controls.ablation.t_overlap));

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  // garbage read as EMPTY: exactly the hits with garbage in their window are lost
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

  // no row map: the hit's own clear is ABOVE the slot (it does not move it), so only a later clear or a garbage
  // row can; the hits are the same and only the follow-ups that needed one move. Measured: some that fired
  // stop firing, and none fires that did not
  a = mut({ followupNoRowmap: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBeLessThan(fired(b));
  expect(fired(a)).toBeGreaterThan(0);
  expect(a.hits.every((h: any, i: number) => !h.followup.fired || b.hits[i].followup.fired)).toBe(true);

  a = mut({ followupAnyT: true });
  expect(fired(a)).toBeGreaterThan(fired(b));

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);
