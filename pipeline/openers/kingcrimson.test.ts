/**
 * The King Crimson technique artefact (`analysis/kingcrimson-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique kingcrimson`; the rules are the shared `technique-facts.ts`, the
 * profile `technique-profile-kingcrimson.ts`, the shape the gated `pipeline/openers/kingcrimson-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for
 *      every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on each of the page's own drawings of the shape
 *      at its agreement slot, in its recorded hand, and at no other T placement on it; on the page's other boards
 *      nowhere; and over every U-slot board of every committed `*-routes.json` nowhere (the gate's
 *      `routes_fire_none`).
 *   4. THE FOLLOW-UP IS THE STSD PAGE'S: every King Crimson follow-up that fires (the second T, stood into the lower
 *      slot, a full TSD) is a hit of `analysis/stsd-facts.json` at that lock — a second window, written for another
 *      page, reaching the same lock — and every hit's TST lock itself is no hit of any other technique page.
 *   5. WHAT DISCRIMINATES, measured per window part with the T anchored, against the headline.
 *   6. NAMED lists, not bounds; pinned per-player figures; mutants with their symptoms, the equivalent ones named
 *      and asserted to STAY byte-identical.
 *
 * window_off_board is not listed entry by entry: it is every stood T at a TST whose window leaves the board in a
 * hand, a count with a property check (every entry such a T, none a hit).
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { KINGCRIMSON } from '../sim/technique-profile-kingcrimson.ts';
import { TECHNIQUES } from '../sim/techniques.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29', '2026-11-01']);
const ART_PATH = `${import.meta.dir}/../../analysis/kingcrimson-facts.json`;
const STSD_PATH = `${import.meta.dir}/../../analysis/stsd-facts.json`;
const TR = JSON.parse(readFileSync(KINGCRIMSON.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the stood T into the page's TST slot, as drawn (nub right) or mirrored. */
const KINGCRIMSON_HITS: string[] = [
  '2026-10-29 m2r3 pinglamb lock 88 (mirrored)',
];
const FOLLOWUP_NOT_FIRED: string[] = [];
const GARBAGE_IN_WINDOW: string[] = [];
const KINGCRIMSON_IN_OPENER: string[] = [];
const RECON_DROPPED_TSD: string[] = [];
const NOT_QUALIFIED: string[] = [];
/** every fired follow-up, by the STSD artefact's name for its lock: measured, each one an STSD hit */
const STSD_FOLLOWUPS: string[] = [
  '2026-10-29 m2r3 pinglamb lock 89',
];
/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 4, yachi: 8 };

/** Per player: the opportunity (scored full TSTs), split at the 0-based opener window. */
const TST_DENOM = { pinglamb: { all: 1633, in_opener: 1595, mid_game: 38 },
                    yachi: { all: 983, in_opener: 931, mid_game: 52 } };
const HITS = { pinglamb: { all: 1, in_opener: 0, mid_game: 1, mirrored: 1, garbage_in_window: 0 },
               yachi: { all: 0, in_opener: 0, mid_game: 0, mirrored: 0, garbage_in_window: 0 } };
const FOLLOWUP_FIRED = { pinglamb: 1, yachi: 0 };
const QUALIFIED = { pinglamb: 1, yachi: 0 };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {under: {TSS: {pinglamb: 0, yachi: 0}, TSD: {pinglamb: 0, yachi: 0}, mini_TSS: {pinglamb: 0, yachi: 0}, mini_TSD: {pinglamb: 0, yachi: 0}}, ablation: {no_must_empty: {pinglamb: 17, yachi: 31}, no_roof: {pinglamb: 1, yachi: 0}, t_overlap: {pinglamb: 1, yachi: 0}}, orientation_baseline: {pinglamb: 1633, yachi: 983}};
/** What discriminates, measured: full TSTs whose anchored T meets ONE part of the window. `above` is the two
 *  rows over the T (the overhang over the well, then the wall and the open well under it), of which `overhang` is
 *  the top row and `wall` the next; `cleared` the three rows the TST clears; `below` the STSD slot's three rows. */
const PART_ONLY = { above: 2616, overhang: 2616, wall: 2616, cleared: 2616, below: 1 };

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  noRoof: 'the rows over the T admit every scored full TST on the corpus (PART_ONLY.above), so dropping them changes no hit',
  followupNoRowmap: 'the STSD slot lies wholly under the TST\'s cleared rows, so the clear never splits or moves it: the row map is the identity on it',
  followupAnyT: 'the one hit\'s next T is the slot, a scored full TSD, so counting any scored T changes nothing',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(KINGCRIMSON, m, digests());
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
  expect(n).toBe(17205);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the page\'s drawings: once, at the agreement slot, in its hand, nowhere else', () => {
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  const v = TR.variants[0];
  const page = v.agreement.filter((a: any) => byId.has(a.board));
  expect(page.map((a: any) => a.board).sort()).toEqual(['basic', 'empty.kc', 'tki1.kc', 'tki2.kc']);
  // fires_on is the page's boards the window fires on AS DRAWN; the mirrored drawings fire mirrored
  expect(page.filter((a: any) => !a.mirrored).map((a: any) => a.board).sort()).toEqual([...v.fires_on].sort());
  for (const a of page) {
    const board = asBoard(byId.get(a.board).rows, filledCh);
    const lock: Cell[] = a.t_cells.map(([row, col]: number[]) => ({ row, col }));
    expect(fires(board, lock), a.board).toEqual([a.mirrored]);
    const others = tPlacements(board).filter(cs => cs.some(q => !lock.some(x => x.row === q.row && x.col === q.col)));
    for (const cs of others) expect(fires(board, cs), a.board).toEqual([]);
  }
  // the page's boards the gate records as misses: no T placement fires (a spin board read with its U taken out)
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
  expect(v.spin).toBe('TST');
  expect(v.lines).toBe(3);
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [0, 7], cols: [6, 9] });
  expect(v.t_cells).toEqual([[2, 7], [3, 7], [3, 8], [4, 7]]);
  expect(v.followup).toMatchObject({ spin: 'TSD', lines: 2, t_cells_pre_clear: [[5, 7], [6, 7], [6, 8], [7, 7]] });
  // the STSD slot is the TST slot three rows down
  expect(v.followup.t_cells_pre_clear).toEqual(v.t_cells.map(([r, c]: number[]) => [r + 3, c]));
  expect(prepare(TR, v).map(P => P.followupKind)).toEqual(['full:2', 'full:2']);
});

test('named lists: every hit, every follow-up miss, the opener hits, garbage, the hits that fail the build rules', () => {
  const L = art().lists;
  checkNamedList('kingcrimson_hits', L.kingcrimson_hits, KINGCRIMSON_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('kingcrimson_in_opener', L.kingcrimson_in_opener, KINGCRIMSON_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkNamedList('not_qualified', L.not_qualified, NOT_QUALIFIED);
  checkHitPositions(art(), SESSIONS, ROOT, [...KINGCRIMSON_HITS, ...FOLLOWUP_NOT_FIRED, ...GARBAGE_IN_WINDOW]);
  expect(art().hits.length).toBe(KINGCRIMSON_HITS.length);
  expect(L.qualified_hits.length + L.not_qualified.length).toBe(KINGCRIMSON_HITS.length);
});

test('the follow-up is the STSD page\'s: every fired follow-up is an STSD hit at that lock', () => {
  const stsd = JSON.parse(readFileSync(STSD_PATH, 'utf8'));
  const stsdKeys = new Set<string>(stsd.hits.map(hk));
  const fired = art().hits.filter((h: any) => h.followup.fired);
  for (const h of fired) {
    expect(h.followup.lock, qName(h)).toBe(h.lock + 1);
    expect(stsdKeys.has(hk({ ...h, lock: h.followup.lock })), qName(h, h.followup.lock)).toBe(true);
    // in the OTHER hand, measured: the STSD page draws its T with the nub left, harddrop's King Crimson its STSD with
    // the nub right, so the same lock is mirrored on exactly one of the two pages
    const s = stsd.hits.find((x: any) => hk(x) === hk({ ...h, lock: h.followup.lock }));
    expect(s.mirrored, qName(h, h.followup.lock)).toBe(!h.mirrored);
  }
  expect(fired.map((h: any) => qName(h, h.followup.lock))).toEqual(STSD_FOLLOWUPS);
  // and the TST lock itself is no hit of any other technique page (each of their opportunities is not a TST)
  const mine = hitKeys();
  for (const [key, P] of Object.entries(TECHNIQUES)) {
    if (key === 'kingcrimson') continue;
    const hits = JSON.parse(readFileSync(P.artefactPath, 'utf8')).hits;
    expect(hits.filter((x: any) => mine.has(hk(x))), key).toEqual([]);
  }
});

test('window_off_board: pinned per player, every entry a stood T at a full TST whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  for (const u of ['pinglamb', 'yachi'] as const)
    expect(L.filter(x => x.split(' ')[2] === u).length, u).toBe(WINDOW_OFF_BOARD[u]);
  const v = TR.variants[0];
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  const tr = Math.min(...v.t_cells.map((x: number[]) => x[0]!)), tc = v.t_cells[0]![1];
  const want = new Set<string>();
  const hits = hitKeys();
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full' || s.lk.cleared !== 3) continue;
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
  const a = art(), v = a.variants.kingcrimson;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TST, u).toEqual(TST_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u].fired, u).toBe(FOLLOWUP_FIRED[u]);
    expect(v.followup_by_player[u].fired + total(v.followup_by_player[u].not_fired)).toBe((HITS as any)[u].all);
    expect(a.qualify.by_player[u].qualified, u).toBe(QUALIFIED[u]);
  }
  expect(v.controls).toEqual(CONTROLS);
  // every scored full TST stands its T up: the orientation baseline IS the denominator
  for (const u of ['pinglamb', 'yachi'] as const) expect(v.controls.orientation_baseline[u]).toBe(TST_DENOM[u].all);
});

test('what discriminates: each part of the window alone, with the T anchored', () => {
  const v = TR.variants[0];
  const top = Math.min(...v.t_cells.map((x: number[]) => x[0]!));
  const parts: Record<string, (r: number) => boolean> = {
    above: r => r < top, overhang: r => r === top - 2, wall: r => r === top - 1,
    cleared: r => r >= top && r <= top + 2, below: r => r > top + 2,
  };
  const hits = hitKeys();
  const got: Record<string, number> = {};
  for (const [name, keep] of Object.entries(parts)) {
    const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || keep(x.r)) }));
    let n = 0, hitsIn = 0;
    for (const d of digests()) for (const s of scored(d)) {
      if (s.lk.spin !== 'full' || s.lk.cleared !== 3) continue;
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
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.kingcrimson.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.kingcrimson.followup_by_player).map(([u, x]: any) => [u, x.fired])));
  const tst = (a: any, k = 'all') => a.denominators.pinglamb.TST[k] + a.denominators.yachi.TST[k];
  const tss = (a: any) => a.denominators.pinglamb.TSS.all + a.denominators.yachi.TSS.all;
  const b = JSON.parse(base);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };

  let a = mut({ noMirror: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(sum(a, 'all')).toBe(sum(b, 'all') - sum(b, 'mirrored'));

  a = mut({ pastPrefix: true });
  expect(a.denominators.pinglamb.unscored_past_prefix + a.denominators.yachi.unscored_past_prefix).toBe(0);
  expect(tst(a)).toBeGreaterThan(tst(b));

  a = mut({ includeMini: true });
  expect(tss(a)).toBe(tss(b) + b.denominators.pinglamb.mini_TSS.all + b.denominators.yachi.mini_TSS.all);

  // the must-empty cells (the open well, the STSD slot) are what make a TST a King Crimson
  a = mut({ noMustEmpty: true });
  expect(sum(a, 'all')).toBe(total(b.variants.kingcrimson.controls.ablation.no_must_empty));
  expect(sum(a, 'all')).toBeGreaterThan(sum(b, 'all'));

  // the T merely overlapping the window: the same hit, but its follow-up is no longer anchored
  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.kingcrimson.controls.ablation.t_overlap));
  expect(fired(a)).toBe(0);

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  // garbage read as EMPTY: no hit has garbage in its window, so the hits stay; what moves is window_off_board, whose
  // entries leave it when a garbage cell now fails a filled window cell before an off-board cell is reached (the
  // matcher's iteration order; see the header)
  a = mut({ garbageEmpty: true });
  expect(a.hits.map(hk)).toEqual(b.hits.map(hk));
  expect(a.lists.window_off_board.length).toBeLessThan(b.lists.window_off_board.length);
  for (const x of a.lists.window_off_board) expect(b.lists.window_off_board).toContain(x);

  // the slot carried in the drawn columns on a mirrored hit: no mirrored follow-up fires
  a = mut({ followupUnmirrored: true });
  expect(a.hits.map(hk)).toEqual(b.hits.map(hk));
  expect(a.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBe(0);
  expect(b.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBeGreaterThan(0);

  a = mut({ openerLt: true });
  expect(tst(a, 'in_opener')).toBeLessThan(tst(b, 'in_opener'));
  expect(tst(a)).toBe(tst(b));

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);
