/**
 * The Cave TSS to TST technique artefact (`analysis/cavetsstst-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique cavetsstst`; the rules are the shared `technique-facts.ts`, the
 * profile `technique-profile-cavetsstst.ts`, the shape the gated `pipeline/openers/cavetsstst-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for
 *      every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on the page's drawing of the shape and on the
 *      short's at their slots, in their hands, and at no other T placement on them; on the page's other boards
 *      nowhere; and over every U-slot board of every committed `*-routes.json` nowhere (the gate's
 *      `routes_fire_none`).
 *   4. THE CREDIT: the opportunity is a MINI TSS (the engine's credit for this slot), so the profile's opportunity
 *      and the transcription's `credit` agree, and no hit's lock is a hit of another technique page.
 *   5. WHAT DISCRIMINATES, measured per window part with the T anchored, against the headline.
 *   6. NAMED lists, not bounds; pinned per-player figures; mutants with their symptoms, the equivalent ones named
 *      and asserted to STAY byte-identical.
 *
 * window_off_board is not listed entry by entry: it is every stood T at a mini TSS whose window leaves the board
 * in a hand, a count with a property check (every entry such a T, none a hit).
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { CAVETSSTST } from '../sim/technique-profile-cavetsstst.ts';
import { TECHNIQUES } from '../sim/techniques.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29', '2026-11-01', '2026-11-05']);
const ART_PATH = `${import.meta.dir}/../../analysis/cavetsstst-facts.json`;
const TR = JSON.parse(readFileSync(CAVETSSTST.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the stood T into the page's cave, as drawn (nub right) or mirrored. */
const CAVETSSTST_HITS: string[] = [
  '2026-08-14 m4r4 pinglamb lock 76 (mirrored)',
];
const FOLLOWUP_NOT_FIRED: string[] = [
  '2026-08-14 m4r4 pinglamb lock 76 (slot_filled_before_t at lock 79)',
];
const GARBAGE_IN_WINDOW: string[] = [];
const CAVETSSTST_IN_OPENER: string[] = [];
const RECON_DROPPED_TSD: string[] = [];
const NOT_QUALIFIED: string[] = [];
/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 183, yachi: 67 };

/** Per player: the opportunity (scored mini TSSs), split at the 0-based opener window. */
const OPP_DENOM = { pinglamb: { all: 391, in_opener: 16, mid_game: 375 },
                    yachi: { all: 99, in_opener: 9, mid_game: 90 } };
const HITS = { pinglamb: { all: 1, in_opener: 0, mid_game: 1, mirrored: 1, garbage_in_window: 0 },
               yachi: { all: 0, in_opener: 0, mid_game: 0, mirrored: 0, garbage_in_window: 0 } };
const FOLLOWUP_FIRED = { pinglamb: 0, yachi: 0 };
const QUALIFIED = { pinglamb: 1, yachi: 0 };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {under: {TSS: {pinglamb: 0, yachi: 0}, TSD: {pinglamb: 0, yachi: 0}, TST: {pinglamb: 0, yachi: 0}, mini_TSD: {pinglamb: 0, yachi: 0}}, ablation: {no_must_empty: {pinglamb: 1, yachi: 0}, no_roof: {pinglamb: 173, yachi: 18}, t_overlap: {pinglamb: 1, yachi: 0}}, orientation_baseline: {pinglamb: 356, yachi: 87}};
/** What discriminates, measured: mini TSSs whose anchored T meets ONE part of the window. `overhang` is the row
 *  over the T (the L laid over the cave); `beside` the T's two upper rows (the cave's wall and the open cells
 *  where the TST goes); `cleared` the row the TSS clears. */
const PART_ONLY = { overhang: 1, beside: 191, cleared: 193 };

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  noMustEmpty: 'the ablation no_must_empty admits exactly the one hit: the only must-empty cells are the TST stem and the cell beside the T, and every other mini TSS stood T is stopped by a filled cell first',
  garbageEmpty: 'no hit has garbage in its window (garbage_in_window is empty)',
  followupAnyT: 'the one hit\'s follow-up stops at slot_filled_before_t, before any T is compared with the slot',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(CAVETSSTST, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;
const hk = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
const hitKeys = () => new Set<string>(art().hits.map(hk));
const keyOf = (d: TechDigest, lock: number) => `${d.session}|${d.file}|${d.round}|${d.user}|${lock}`;
const qName = (h: any, lock = h.lock) => `${h.session} m${h.match}r${h.round} ${h.player} lock ${lock}`;

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

/** A stood T: its stem's top cell and the side its nub points to (+1 right, -1 left), or null. */
function stemOf(cells: { row: number; col: number }[]) {
  const cols = [...new Set(cells.map(q => q.col))];
  if (cols.length !== 2) return null;
  const stemCol = cols.find(c => cells.filter(q => q.col === c).length === 3);
  if (stemCol === undefined) return null;
  const stem = cells.filter(q => q.col === stemCol).map(q => q.row).sort((a, b) => a - b);
  const nub = cells.find(q => q.col !== stemCol)!;
  if (stem[1] !== stem[0]! + 1 || stem[2] !== stem[0]! + 2 || nub.row !== stem[1]) return null;
  return { row: stem[0]!, col: stemCol, side: nub.col - stemCol };
}

const asBoard = (rows: string[], filled: (ch: string) => boolean) =>
  rows.map(r => [...r].map(ch => filled(ch) ? 'X' : '.').join(''));
/** every flat or stood T placement on a board, resting or not: the window anchors on the cells alone */
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
const filledCh = (ch: string) => ch !== '-' && ch !== 'U';

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
  expect(n).toBe(17949);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the drawings: harddrop\'s board and the short\'s, once each, at the slot, nowhere else', () => {
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  const v = TR.variants[0];
  expect(v.agreement.map((a: any) => a.board)).toEqual(['tss']);
  expect([...v.fires_on]).toEqual(['tss']);
  const vid = TR.cross_source.video;
  const drawings = [
    ...v.agreement.map((a: any) => ({ id: a.board, rows: byId.get(a.board).rows, t: a.t_cells, mirrored: a.mirrored })),
    { id: 'short', rows: vid.rows, t: vid.t_cells, mirrored: false },
  ];
  for (const a of drawings) {
    const board = asBoard(a.rows, filledCh);
    const lock: Cell[] = a.t.map(([row, col]: number[]) => ({ row, col }));
    expect(fires(board, lock), a.id).toEqual([a.mirrored]);
    const others = tPlacements(board).filter(cs => cs.some(q => !lock.some(x => x.row === q.row && x.col === q.col)));
    for (const cs of others) expect(fires(board, cs), a.id).toEqual([]);
  }
  // the spin board, its U taken out, fires at the U
  const sp = byId.get(v.board);
  const spLock: Cell[] = sp.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));
  expect(fires(asBoard(sp.rows, filledCh), spLock)).toEqual([false]);
  // the page's boards the gate records as misses: no T placement fires
  for (const id of v.misses) {
    const board = asBoard(byId.get(id).rows, filledCh);
    expect(tPlacements(board).filter(cs => fires(board, cs).length).length, id).toBe(0);
  }
});

test('the Python twin on the routes: windowMatch fires on no routes board (the gate\'s routes_fire_none)', () => {
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
  expect(got).toEqual([]);
  expect(TR.cross_source.routes_fire_none).toBeTruthy();
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.spin).toBe('TSS');
  expect(v.lines).toBe(1);
  expect(v.credit).toBe('mini');
  expect(CAVETSSTST.opportunity).toEqual({ spin: v.credit, lines: v.lines });
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [2, 5], cols: [0, 3] });
  expect(v.t_cells).toEqual([[3, 1], [4, 1], [4, 2], [5, 1]]);
  expect(v.followup).toMatchObject({ spin: 'TST', lines: 3, t_cells_pre_clear: [[2, 3], [3, 2], [3, 3], [4, 3]] });
  expect(prepare(TR, v).map(P => P.followupKind)).toEqual(['full:3', 'full:3']);
  expect(art().opportunity).toBe('mini T-spin clearing 1 line(s)');
});

test('named lists: every hit, every follow-up miss, the opener hits, garbage, the hits that fail the build rules', () => {
  const L = art().lists;
  checkNamedList('cavetsstst_hits', L.cavetsstst_hits, CAVETSSTST_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('cavetsstst_in_opener', L.cavetsstst_in_opener, CAVETSSTST_IN_OPENER);
  checkNamedList('not_qualified', L.not_qualified, NOT_QUALIFIED);
  checkHitPositions(art(), SESSIONS, ROOT, [...CAVETSSTST_HITS, ...FOLLOWUP_NOT_FIRED, ...GARBAGE_IN_WINDOW]);
  expect(art().hits.length).toBe(CAVETSSTST_HITS.length);
  expect(L.qualified_hits.length + L.not_qualified.length).toBe(CAVETSSTST_HITS.length);
});

test('no hit is a hit of another technique page (their opportunities are full spins; this one a mini TSS)', () => {
  const mine = hitKeys();
  for (const [key, P] of Object.entries(TECHNIQUES)) {
    if (key === 'cavetsstst') continue;
    const hits = JSON.parse(readFileSync(P.artefactPath, 'utf8')).hits;
    expect(hits.filter((x: any) => mine.has(hk(x))), key).toEqual([]);
  }
});

test('window_off_board: pinned per player, every entry a stood T at a mini TSS whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  for (const u of ['pinglamb', 'yachi'] as const)
    expect(L.filter(x => x.split(' ')[2] === u).length, u).toBe(WINDOW_OFF_BOARD[u]);
  const v = TR.variants[0];
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  const tr = Math.min(...v.t_cells.map((x: number[]) => x[0]!)), tc = v.t_cells[0]![1];
  const want = new Set<string>();
  const hits = hitKeys();
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'mini' || s.lk.cleared !== 1) continue;
    const st = stemOf(s.lk.cells);
    if (!st || hits.has(keyOf(d, s.i))) continue;
    const rowsOff = st.row + (r0 - tr) < 0 || st.row + (r1 - tr) >= H;
    const drawnOff = rowsOff || st.col + (c0 - tc) < 0 || st.col + (c1 - tc) > 9;
    const mirrOff = rowsOff || st.col - (c1 - tc) < 0 || st.col - (c0 - tc) > 9;
    if (drawnOff || mirrOff) want.add(nameOf(d, s.i));
  }
  for (const x of L) expect(want.has(x), x).toBe(true);
  expect(new Set(L).size).toBe(L.length);
}, 600_000);

test('pinned: denominators, hits, follow-ups, qualify, controls', () => {
  const a = art(), v = a.variants.cavetsstst;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].mini_TSS, u).toEqual(OPP_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u].fired, u).toBe(FOLLOWUP_FIRED[u]);
    expect(v.followup_by_player[u].fired + total(v.followup_by_player[u].not_fired)).toBe((HITS as any)[u].all);
    expect(a.qualify.by_player[u].qualified, u).toBe(QUALIFIED[u]);
  }
  expect(v.controls).toEqual(CONTROLS);
});

test('what discriminates: each part of the window alone, with the T anchored', () => {
  const v = TR.variants[0];
  const top = Math.min(...v.t_cells.map((x: number[]) => x[0]!));
  const bottom = Math.max(...v.t_cells.map((x: number[]) => x[0]!));
  const parts: Record<string, (r: number) => boolean> = {
    overhang: r => r < top, beside: r => r >= top && r < bottom, cleared: r => r === bottom,
  };
  const hits = hitKeys();
  const got: Record<string, number> = {};
  for (const [name, keep] of Object.entries(parts)) {
    const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || keep(x.r)) }));
    let n = 0, hitsIn = 0;
    for (const d of digests()) for (const s of scored(d)) {
      if (s.lk.spin !== 'mini' || s.lk.cleared !== 1) continue;
      if (!preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) continue;
      n++;
      if (hits.has(keyOf(d, s.i))) hitsIn++;
    }
    expect(hitsIn, name).toBe(art().hits.length);   // every hit passes each weaker predicate
    got[name] = n;
  }
  expect(got).toEqual(PART_ONLY);
}, 600_000);

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.cavetsstst.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const opp = (a: any, k = 'all') => a.denominators.pinglamb.mini_TSS[k] + a.denominators.yachi.mini_TSS[k];
  const tss = (a: any) => a.denominators.pinglamb.TSS.all + a.denominators.yachi.TSS.all;
  const b = JSON.parse(base);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };

  let a = mut({ noMirror: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(sum(a, 'all')).toBe(sum(b, 'all') - sum(b, 'mirrored'));

  a = mut({ pastPrefix: true });
  expect(a.denominators.pinglamb.unscored_past_prefix + a.denominators.yachi.unscored_past_prefix).toBe(0);
  expect(opp(a)).toBeGreaterThan(opp(b));

  // a mini read as a full spin: the opportunity empties into the TSS control, and with it every hit
  a = mut({ includeMini: true });
  expect(tss(a)).toBe(tss(b) + opp(b));
  expect(opp(a)).toBe(0);
  expect(sum(a, 'all')).toBe(0);

  expect(sum(b, 'all')).toBe(total(b.variants.cavetsstst.controls.ablation.no_must_empty));

  // the T merely overlapping the window: the one hit is found in the first hand tried, unanchored
  a = mut({ tOverlap: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(a.variants.cavetsstst.followup_by_player.pinglamb.not_fired).toEqual({ not_anchored: 1 });

  // the follow-up carried in the wrong hand, or without the row map: the next T is looked for elsewhere
  for (const m of [{ followupUnmirrored: true }, { followupNoRowmap: true }]) {
    a = mut(m);
    expect(a.variants.cavetsstst.followup_by_player.pinglamb.not_fired, JSON.stringify(m)).toEqual({ next_t_elsewhere: 1 });
  }

  a = mut({ noRoof: true });
  expect(sum(a, 'all')).toBe(total(b.variants.cavetsstst.controls.ablation.no_roof));
  expect(sum(a, 'all')).toBeGreaterThan(sum(b, 'all'));

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  a = mut({ openerLt: true });
  expect(opp(a, 'in_opener')).toBeLessThan(opp(b, 'in_opener'));
  expect(opp(a)).toBe(opp(b));

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);
