/**
 * The ハンバーガー (Hamburger) technique artefact (`analysis/hamburger-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique hamburger`; the rules are the shared `technique-facts.ts`, the
 * profile `technique-profile-hamburger.ts`, the cover field `hamburger-cover.ts`, the shape the gated
 * `pipeline/openers/hamburger-technique.json`, read off harddrop's Hamburger page).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count, as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on every agreement drawing once, at its slot, and
 *      over every U-slot board of every committed `*-routes.json` exactly where the gate's `cross_source.fires` says.
 *   4. THE OPENER: a hit in the opener window is counted, never filtered, and every SDPC Spin / stick spin bag-1 TSS
 *      case is a hit at its spin lock and the other way round; the hits that are such cases are named.
 *   5. THE COVER (yachi: 「用S/Z 砌hamburger 先算，除非有其他完整piece 砌到」): every hit's `cover` re-derived from its
 *      digest; a qualifying hit's cover is whole pieces; the ones not one S or Z are named.
 *   6. OVERLAPS with the other pages, measured: 欄干's TSS (a stood T) and Cave TSS 接 TST (a mini) share no hit; the
 *      common hits with 基本的なドネイト's TSS rule pinned.
 *   7. WHAT DISCRIMINATES, per window part with the T anchored; pinned per-player figures; named lists.
 *   8. mutants, each with its symptom; the equivalent ones named and asserted to STAY byte-identical.
 *
 * The payoff's `well_covered` / `well_filled_not_i` are the page's Repeat (another layer stacked over the well),
 * not a failure; they are pinned as counts beside `fired`.
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { HAMBURGER } from '../sim/technique-profile-hamburger.ts';
import { hamburgerCover, withMidGameOnly } from '../sim/hamburger-cover.ts';
import { TECHNIQUES } from '../sim/techniques.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29', '2026-11-01', '2026-11-05', '2026-11-17', '2026-11-19']);
const ART_PATH = `${import.meta.dir}/../../analysis/hamburger-facts.json`;
const TR = JSON.parse(readFileSync(HAMBURGER.transcriptionPath, 'utf8'));
const H = 40;
const USERS = ['pinglamb', 'yachi'] as const;

/** Every hit that is an SDPC Spin or stick spin bag-1 TSS case, at that case's spin lock (the route artefacts'). */
const OPENER_ROUTE_HITS: string[] = [
  '2026-09-17 m2r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-18 m6r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-18 m6r4 pinglamb lock 6 (sdpcspin)',
  '2026-09-18 m7r7 pinglamb lock 6 (sdpcspin)',
  '2026-09-19 m3r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-19 m4r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-19 m5r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-19 m5r2 pinglamb lock 6 (sdpcspin)',
  '2026-09-19 m5r3 pinglamb lock 6 (sdpcspin)',
  '2026-09-19 m8r3 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-19 m8r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-19 m9r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-19 m9r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-19 m15r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-09-19 m16r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m2r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m2r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m4r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m4r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m4r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m4r8 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m5r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m5r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m6r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m6r8 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m7r7 yachi lock 6 (sdpcspin)',
  '2026-10-03 m9r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m9r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m10r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m10r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m10r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m11r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m11r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m13r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m14r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m15r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m16r2 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m17r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m19r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-03 m19r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m1r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m1r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m2r2 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m2r3 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m2r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m2r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m3r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m3r8 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m4r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m4r8 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m5r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m5r3 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m6r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m7r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m7r2 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m7r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m7r8 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m7r9 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m8r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m8r2 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m8r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m8r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m9r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m9r3 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m9r9 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m10r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m10r2 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m10r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m11r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m11r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m12r3 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-09 m12r6 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-12 m1r3 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-12 m3r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-12 m7r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-20 m1r4 yachi lock 6 (sdpcspin)',
  '2026-10-20 m2r3 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-20 m3r5 yachi lock 6 (sdpcspin)',
  '2026-10-20 m4r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-22 m5r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-29 m1r4 yachi lock 6 (sdpcspin)',
  '2026-10-29 m2r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-10-29 m2r5 yachi lock 6 (sdpcspin)',
  '2026-10-29 m9r9 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-01 m1r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-01 m4r2 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-01 m4r5 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-01 m9r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-01 m10r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-01 m11r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-01 m14r6 yachi lock 6 (sdpcspin)',
  '2026-11-05 m3r3 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-05 m4r7 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-05 m6r1 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-05 m7r2 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-05 m8r8 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-19 m4r4 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-19 m4r11 yachi lock 6 (sdpcspin+stickspin)',
  '2026-11-19 m4r14 yachi lock 6 (sdpcspin+stickspin)',
];
const OPENER_OTHER_HITS: string[] = [
  '2026-08-09 m6r7 yachi lock 19',
  '2026-09-11 m2r1 yachi lock 21',
  '2026-09-17 m2r6 yachi lock 9',
  '2026-09-18 m13r1 pinglamb lock 6',
  '2026-09-18 m16r7 yachi lock 10',
  '2026-10-29 m1r1 yachi lock 13',
  '2026-11-01 m18r5 yachi lock 19',
];
const QUALIFIED_MID_GAME: string[] = [
  '2026-08-25 m6r7 pinglamb lock 115',
  '2026-09-18 m3r2 yachi lock 66',
  '2026-09-18 m8r1 yachi lock 38',
  '2026-09-18 m11r1 yachi lock 207',
  '2026-09-19 m10r2 pinglamb lock 27',
  '2026-10-03 m10r6 yachi lock 28',
  '2026-11-01 m14r3 yachi lock 54',
  '2026-11-01 m14r4 pinglamb lock 91',
];
const COVER_NOT_ONE_SZ_OR_NULL: string[] = [
  '2026-08-19 m9r4 yachi lock 35 (null)',
  '2026-08-25 m6r7 pinglamb lock 115 (complete_pieces)',
  '2026-09-03 m3r6 yachi lock 136 (null)',
  '2026-09-18 m11r1 yachi lock 207 (complete_pieces)',
  '2026-11-01 m14r4 pinglamb lock 91 (complete_pieces)',
];
/** The hits whose T is the LAST verified lock of its round (lock == verified_to). The shared scoring loop scores a lock
 *  up to and including the verified index; the coordinator's scratch probe (ownership at the lock before the T, over the
 *  two cover cells) scored only locks strictly inside it, so it found exactly these eight fewer hits, and on every other
 *  hit its cover reading (one S/Z, other whole pieces, fragment or garbage, unverified) is this artefact's. Named, not
 *  explained away: the difference is which edge of the verified prefix counts. */
const AT_VERIFIED_EDGE: string[] = [
  '2026-08-19 m9r4 yachi lock 35 (null)',
  '2026-09-18 m8r1 yachi lock 38 (one_sz)',
  '2026-09-18 m11r1 yachi lock 207 (complete_pieces)',
  '2026-10-03 m2r4 yachi lock 6 (one_sz)',
  '2026-10-03 m11r7 yachi lock 6 (one_sz)',
  '2026-10-03 m17r4 yachi lock 6 (one_sz)',
  '2026-10-09 m2r3 yachi lock 6 (one_sz)',
  '2026-10-12 m7r5 yachi lock 84 (not_complete)',
];
const QUALIFIED_PAYOFF_FIRED: string[] = [
  '2026-11-01 m14r4 pinglamb lock 91',
];

const OPP_DENOM = { pinglamb: { all: 807, in_opener: 110, mid_game: 697 }, yachi: { all: 1305, in_opener: 313, mid_game: 992 } };
const HITS = { pinglamb: { all: 42, in_opener: 5, mid_game: 37, mirrored: 13, garbage_in_window: 32 },
               yachi: { all: 187, in_opener: 101, mid_game: 86, mirrored: 143, garbage_in_window: 70 } };
/** the payoff: `well_covered` / `well_filled_not_i` are another layer of the stacking (the page's Repeat) */
const PAYOFF = { pinglamb: { fired: 23, not_fired: { i_in_well_not_quad: 5, well_covered: 3, well_filled_not_i: 11 } },
                 yachi: { fired: 35, not_fired: { i_in_well_not_quad: 15, past_verified: 7, round_ended: 1, well_covered: 17, well_filled_not_i: 112 } } };
const QUALIFY = { pinglamb: { qualified: 3, not_qualified: { dpc: 1, fragment: 28, garbage_in_shape: 6, in_opener: 5 } },
                  yachi: { qualified: 5, not_qualified: { dpc: 1, fragment: 72, garbage_in_shape: 11, in_opener: 101, ownership_unverified: 2 } } };
/** cover kind per player, over every hit and over the qualifying ones */
const COVER: Record<string, any> = {
  pinglamb: { all: { complete_pieces: 2, not_complete: 33, one_sz: 7 }, qualified: { complete_pieces: 2, one_sz: 1 } },
  yachi: { all: { complete_pieces: 1, not_complete: 83, null: 2, one_sz: 101 }, qualified: { complete_pieces: 1, one_sz: 4 } },
};
const CONTROLS = {under: {TSD: {pinglamb: 0, yachi: 0}, TST: {pinglamb: 0, yachi: 0}, mini_TSS: {pinglamb: 0, yachi: 0}, mini_TSD: {pinglamb: 0, yachi: 0}}, ablation: {no_must_empty: {pinglamb: 344, yachi: 499}, no_roof: {pinglamb: 42, yachi: 188}, t_overlap: {pinglamb: 46, yachi: 191}}, orientation_baseline: {pinglamb: 178, yachi: 520}};
/** full TSSs whose anchored T meets ONE row of the window: `above` the row over the arms, `arms` the T's arm row,
 *  `cleared` the row the TSS clears (the cover and the nub), `below` the hole row under it */
const PART_ONLY: Record<string, number> = { above: 874, arms: 530, cleared: 1261, below: 294 };
/** [this page's hits that are hits there, this page's hits], per other technique artefact that shares any */
const COMMON: Record<string, number> = { basicdonating: 110 };

const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  followupAnyT: 'a payoff variant has no follow-up T to compare',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(HAMBURGER, m, digests());
const hk = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
const keyOf = (d: TechDigest, lock: number) => `${d.session}|${d.file}|${d.round}|${d.user}|${lock}`;
const qName = (h: any) => `${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock}`;

function scored(d: TechDigest) {
  const out: { i: number; lk: TechDigest['locks'][number]; board: string[] }[] = [];
  for (const t of d.tspins) {
    if (t.i > d.v) continue;
    const lk = d.locks[t.i]!;
    const withT = t.board.map(s => [...s].map(x => x !== '.'));
    for (const q of lk.cells) withT[q.row]![q.col] = true;
    const rows: number[] = [];
    for (let r = 0; r < H; r++) if (withT[r]!.every(Boolean)) rows.push(r);
    const theirs = [...lk.clearedRows].sort((a, b) => a - b);
    if (rows.length !== theirs.length || !rows.every((x, k) => x === theirs[k]) || !rows.length) continue;
    out.push({ i: t.i, lk, board: t.board });
  }
  return out;
}
const asBoard = (rows: string[]) => rows.map(r => [...r].map(ch => ch === '-' || ch === 'U' ? '.' : 'X').join(''));
function tPlacements(board: string[]) {
  const shapes = [[[0, 0], [0, 1], [0, 2], [1, 1]], [[0, 1], [1, 0], [1, 1], [1, 2]],
                  [[0, 0], [1, 0], [2, 0], [1, 1]], [[0, 1], [1, 0], [1, 1], [2, 1]]];
  const out: Cell[][] = [];
  for (const sh of shapes) for (let r = 0; r < board.length; r++) for (let c = 0; c < 10; c++) {
    const cells = sh.map(([dr, dc]) => ({ row: r + dr!, col: c + dc! }));
    if (cells.every(q => q.row < board.length && q.col < 10 && board[q.row]![q.col] === '.')) out.push(cells);
  }
  return out;
}
const fires = (board: string[], lock: Cell[]) =>
  prepare(TR, TR.variants[0]).filter(P => !!windowMatch(board, lock, P)).map(P => P.mirrored);

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 600_000);

test('quarantined: report_eligible false, no claim ids, one variant, a payoff and no follow-up', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
  expect(a.cross_route).toBeUndefined();
  const v = TR.variants[0];
  expect(TR.variants.length).toBe(1);
  expect([v.id, v.spin, v.lines, v.window_basis]).toEqual(['hamburger', 'TSS', 1, 'agreement']);
  expect(v.window).toEqual({ rows: [1, 4], cols: [0, 4] });
  expect(v.t_cells).toEqual([[2, 1], [2, 2], [2, 3], [3, 2]]);
  expect(v.payoff).toMatchObject({ kind: 'well_quad', piece: 'I', lines: 4, well_cell_pre_clear: [4, 0] });
  expect(v.followup).toBeUndefined();
  expect(HAMBURGER.opportunity).toEqual({ spin: 'full', lines: 1 });
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  expect(checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT)).toBe(18623);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the drawings: every agreement drawing once, at its slot, in its hand, nowhere else', () => {
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  const v = TR.variants[0];
  expect(v.agreement.map((a: any) => a.board)).toEqual(['terrain', 'zbuild', 'repeat']);
  for (const a of v.agreement) {
    const board = asBoard(byId.get(a.board).rows);
    const lock: Cell[] = a.t_cells.map(([row, col]: number[]) => ({ row, col }));
    expect(fires(board, lock), a.board).toEqual([a.mirrored]);
    const others = tPlacements(board).filter(cs => cs.some(q => !lock.some(x => x.row === q.row && x.col === q.col)));
    for (const cs of others) expect(fires(board, cs), a.board).toEqual([]);
  }
});

test('the Python twin on the routes: windowMatch fires exactly where cross_source.fires records', () => {
  const preps = prepare(TR, TR.variants[0]);
  const got: string[] = [];
  const dir = `${import.meta.dir}`;
  for (const f of readdirSync(dir).filter(x => x.endsWith('-routes.json')).sort()) {
    for (const n of JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const cells = n.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));
      if (cells.length !== 4) continue;
      for (const P of preps) if (windowMatch(asBoard(n.rows), cells, P)) got.push(`${f} ${n.id} ${P.mirrored}`);
    }
  }
  expect(got.sort()).toEqual(TR.cross_source.fires.map((x: any) => `${x.file} ${x.node} ${x.mirrored}`).sort());
});

test('the opener: every SDPC Spin / stick spin bag-1 TSS case is a hit at its spin lock, and those hits are named', () => {
  const a = art();
  const route = new Map<string, string[]>();
  for (const f of ['sdpcspin', 'stickspin']) {
    for (const c of JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/${f}-facts.json`, 'utf8')).cases) {
      if (c.bag1?.spin?.spin !== 'full') continue;
      const k = `${c.session}|${c.file}|${c.round_index0}|${c.player}|${c.bag1.lock}`;
      route.set(k, [...(route.get(k) ?? []), f]);
    }
  }
  const mine = new Set<string>(a.hits.map(hk));
  for (const k of route.keys()) expect(mine.has(k), k).toBe(true);
  const named = a.hits.filter((h: any) => route.has(hk(h))).map((h: any) => `${qName(h)} (${route.get(hk(h))!.sort().join('+')})`);
  expect(named).toEqual(OPENER_ROUTE_HITS);
  // every one is in the opener window; the other opener hits are named too
  expect(a.hits.filter((h: any) => route.has(hk(h))).every((h: any) => h.in_opener)).toBe(true);
  expect(a.hits.filter((h: any) => h.in_opener && !route.has(hk(h))).map(qName)).toEqual(OPENER_OTHER_HITS);
  expect(a.lists.hamburger_in_opener.length).toBe(OPENER_ROUTE_HITS.length + OPENER_OTHER_HITS.length);
});

test('mid-game only: every opener hit fails in_opener and nothing else fails it; the wrapper adds exactly that', () => {
  const a = art();
  for (const h of a.hits) expect(h.not_qualified.includes('in_opener'), qName(h)).toBe(h.in_opener);
  expect(a.hits.some((h: any) => h.qualifies && h.in_opener)).toBe(false);
  const inner = (h: any) => ({ qualifies: false, not_qualified: ['x'] });
  const ok = (h: any) => ({ qualifies: true, not_qualified: [] });
  expect(withMidGameOnly(ok)({ in_opener: true }, null)).toEqual({ qualifies: false, not_qualified: ['in_opener'] });
  expect(withMidGameOnly(ok)({ in_opener: false }, null)).toEqual({ qualifies: true, not_qualified: [] });
  expect(withMidGameOnly(inner)({ in_opener: true }, null)).toEqual({ qualifies: false, not_qualified: ['x', 'in_opener'] });
});

test('the cover: re-derived from every digest; whole pieces on every qualifying hit; the split pinned', () => {
  const a = art();
  const byKey = new Map(digests().map(d => [`${d.file}|${d.round}|${d.user}`, d]));
  for (const h of a.hits) {
    const d = byKey.get(`${h.file}|${h.round_index0}|${h.player}`)!;
    expect(hamburgerCover(h, d), qName(h)).toBe(h.cover);
    if (h.qualifies) expect(['one_sz', 'complete_pieces'], qName(h)).toContain(h.cover);
    if (h.cover === 'not_complete') expect(h.qualifies, qName(h)).toBe(false);
  }
  expect(a.hits.filter((h: any) => h.cover === 'complete_pieces' || h.cover === null).map((h: any) => `${qName(h)} (${h.cover})`))
    .toEqual(COVER_NOT_ONE_SZ_OR_NULL);
  const tally: Record<string, any> = {};
  for (const u of USERS) {
    const hs = a.hits.filter((h: any) => h.player === u);
    const t = (xs: any[]) => { const o: Record<string, number> = {}; for (const h of xs) o[String(h.cover)] = (o[String(h.cover)] ?? 0) + 1; return o; };
    tally[u] = { all: t(hs), qualified: t(hs.filter((h: any) => h.qualifies)) };
  }
  expect(tally).toEqual(COVER);
  expect(a.lists.cover_one_sz.length).toBe(a.hits.filter((h: any) => h.cover === 'one_sz').length);
  expect(a.hits.filter((h: any) => h.lock === h.verified_to).map((h: any) => `${qName(h)} (${h.cover})`).sort())
    .toEqual([...AT_VERIFIED_EDGE].sort());
}, 600_000);

test('overlaps: 欄干 TSS and Cave TSS 接 TST share no hit; the common hits with the other artefacts pinned', () => {
  const mine = new Set<string>(art().hits.map(hk));
  const common: Record<string, number> = {};
  for (const [key, P] of Object.entries(TECHNIQUES)) {
    if (key === 'hamburger') continue;
    const n = JSON.parse(readFileSync(P.artefactPath, 'utf8')).hits.filter((x: any) => mine.has(hk(x))).length;
    if (n) common[key] = n;
  }
  expect(common).toEqual(COMMON);
  expect(common.parapet ?? 0).toBe(0);
  expect(common.cavetsstst ?? 0).toBe(0);
});

test('named lists: hits, payoffs, qualifying; every hit resolves to its match position', () => {
  const a = art(), L = a.lists;
  expect(L.hamburger_hits.length).toBe(a.hits.length);
  expect(L.qualified_hits.length + L.not_qualified.length).toBe(a.hits.length);
  expect(new Set(a.hits.map(hk)).size).toBe(a.hits.length);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, []);
  checkHitPositions(a, SESSIONS, ROOT, []);
  expect(a.hits.filter((h: any) => h.qualifies && !h.in_opener).map(qName)).toEqual(QUALIFIED_MID_GAME);
  expect(a.hits.filter((h: any) => h.qualifies && h.followup.fired).map(qName)).toEqual(QUALIFIED_PAYOFF_FIRED);
});

test('pinned: denominators, hits, payoffs, qualify, controls', () => {
  const a = art(), v = a.variants.hamburger;
  for (const u of USERS) {
    expect(a.denominators[u].TSS, u).toEqual(OPP_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u], u).toEqual(PAYOFF[u]);
    expect(v.followup_by_player[u].fired + total(v.followup_by_player[u].not_fired)).toBe(HITS[u].all);
    expect(a.qualify.by_player[u], u).toEqual(QUALIFY[u]);
  }
  expect(v.controls).toEqual(CONTROLS);
});

test('what discriminates: each row of the window alone, with the T anchored', () => {
  const v = TR.variants[0];
  const top = Math.min(...v.t_cells.map((x: number[]) => x[0]!));
  const parts: Record<string, (r: number) => boolean> = {
    above: r => r < top, arms: r => r === top, cleared: r => r === top + 1, below: r => r > top + 1,
  };
  const hits = new Set<string>(art().hits.map(hk));
  const got: Record<string, number> = {};
  for (const [name, keep] of Object.entries(parts)) {
    const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || keep(x.r)) }));
    let n = 0, hitsIn = 0;
    for (const d of digests()) for (const s of scored(d)) {
      if (s.lk.spin !== 'full' || s.lk.cleared !== 1) continue;
      if (!preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) continue;
      n++;
      if (hits.has(keyOf(d, s.i))) hitsIn++;
    }
    expect(hitsIn, name).toBe(art().hits.length);
    got[name] = n;
  }
  expect(got).toEqual(PART_ONLY);
}, 600_000);

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const b = JSON.parse(base);
  const sum = (a: any, k: string) => USERS.reduce((s, u) => s + a.variants.hamburger.hits_by_player[u][k], 0);
  const fired = (a: any) => USERS.reduce((s, u) => s + a.variants.hamburger.followup_by_player[u].fired, 0);
  const nf = (a: any, r: string) => USERS.reduce((s, u) => s + (a.variants.hamburger.followup_by_player[u].not_fired[r] ?? 0), 0);
  const opp = (a: any, k = 'all') => USERS.reduce((s, u) => s + a.denominators[u].TSS[k], 0);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };

  let a = mut({ noMirror: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(sum(a, 'all')).toBe(sum(b, 'all') - sum(b, 'mirrored'));

  a = mut({ pastPrefix: true });
  expect(opp(a)).toBeGreaterThan(opp(b));

  a = mut({ includeMini: true });
  expect(opp(a)).toBeGreaterThan(opp(b));
  expect(sum(a, 'all')).toBe(sum(b, 'all'));

  a = mut({ noMustEmpty: true });
  expect(sum(a, 'all')).toBe(total(b.variants.hamburger.controls.ablation.no_must_empty));
  a = mut({ noRoof: true });
  expect(sum(a, 'all')).toBe(total(b.variants.hamburger.controls.ablation.no_roof));
  a = mut({ tOverlap: true });
  expect(fired(a)).toBe(0);
  expect(nf(a, 'not_anchored')).toBe(sum(a, 'all'));
  a = mut({ garbageEmpty: true });
  expect(sum(a, 'garbage_in_window')).toBe(0);
  expect(sum(a, 'all')).toBeLessThan(sum(b, 'all'));
  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);
  a = mut({ openerLt: true });
  expect(opp(a, 'in_opener')).toBeLessThan(opp(b, 'in_opener'));
  expect(opp(a)).toBe(opp(b));

  // the payoff: the well carried in the wrong hand, or without the row map, or any piece / any I fires it
  for (const m of [{ followupUnmirrored: true }, { followupNoRowmap: true }]) {
    a = mut(m);
    expect(fired(a), JSON.stringify(m)).toBeLessThan(fired(b));
  }
  a = mut({ payoffAnyPiece: true });
  expect(nf(a, 'well_filled_not_i') + nf(a, 'i_in_well_not_quad')).toBe(0);
  expect(fired(a)).toBe(fired(b) + nf(b, 'well_filled_not_i') + nf(b, 'i_in_well_not_quad'));
  a = mut({ payoffNoQuad: true });
  expect(nf(a, 'i_in_well_not_quad')).toBe(0);
  expect(fired(a)).toBe(fired(b) + nf(b, 'i_in_well_not_quad'));

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 1_200_000);
