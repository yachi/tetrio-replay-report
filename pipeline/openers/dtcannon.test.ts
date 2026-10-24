/**
 * The 途中DT砲 (mid-game DT Cannon) technique artefact (`analysis/dtcannon-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique dtcannon`; the rules are the shared `technique-facts.ts`, the
 * profile `technique-profile-dtcannon.ts`, the shape the gated `pipeline/openers/dtcannon-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for
 *      every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on each of the page's own drawings of the shape
 *      at its agreement slot, as drawn, and at no other T placement on it; and over every U-slot board of every
 *      committed `*-routes.json` it fires on exactly the boards the gate records (harddrop SDPC Spin's two DT
 *      Cannon continuations, another site, mirrored).
 *   4. THE OPENER HITS ARE THE ORDERING METRIC'S DT ROUNDS: every hit inside the opener window is a round whose
 *      opener window runs Double before Triple (`opener-facts.json` `ordering.per_round` `dt_order`), which is
 *      a second input — the order of two spin locks — reaching the same rounds as the board shape.
 *   5. WHAT DISCRIMINATES, measured per window part with the T anchored, against the headline.
 *   6. THE OTHER FLAT-T WINDOWS (STMB Cave, ダブルダガー, BT砲, 千鳥格子, 社畜トレイン, 欄干, 階段のドネイト): anchored
 *      on the same T, this window clashes with each of theirs on a cell in every pairing of hands, and no lock
 *      is a hit of this page and of theirs.
 *   7. NAMED lists, not bounds; pinned per-player figures; mutants with their symptoms, the equivalent ones named
 *      and asserted to STAY byte-identical.
 *
 * window_off_board is not listed entry by entry: it is every flat, nub-down T at a TSD whose window leaves the
 * board before the matcher found a mismatch (the window reaches four rows above the T, one under its nub and
 * the wall column), pinned per player as a count with a property check (STMB Cave's treatment).
 *
 * Run: bun test pipeline/openers/dtcannon.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { DTCANNON } from '../sim/technique-profile-dtcannon.ts';
import { TECHNIQUES } from '../sim/techniques.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);
const ART_PATH = `${import.meta.dir}/../../analysis/dtcannon-facts.json`;
const TR = JSON.parse(readFileSync(DTCANNON.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the flat T into the page's window, as drawn (the TST slot right of the wall column) or mirrored. */
const DTCANNON_HITS: string[] = [
  '2026-08-09 m6r7 yachi lock 208',
  '2026-08-14 m3r4 yachi lock 13',
  '2026-08-19 m1r6 yachi lock 33',
  '2026-08-19 m7r6 yachi lock 27 (mirrored)',
  '2026-08-25 m9r3 yachi lock 13',
  '2026-09-11 m1r1 yachi lock 184 (mirrored)',
  '2026-09-11 m4r5 yachi lock 107',
  '2026-09-17 m3r4 yachi lock 45 (mirrored)',
  '2026-09-17 m6r7 yachi lock 90',
  '2026-09-17 m7r4 yachi lock 13',
  '2026-09-17 m7r4 yachi lock 103 (mirrored)',
  '2026-09-18 m4r2 yachi lock 40 (mirrored)',
  '2026-09-18 m17r9 yachi lock 59',
  '2026-09-19 m1r2 yachi lock 59',
  '2026-10-03 m7r3 yachi lock 14',
  '2026-10-03 m8r4 yachi lock 99',
  '2026-10-09 m2r6 yachi lock 36 (mirrored)',
  '2026-10-12 m4r6 yachi lock 70 (mirrored)',
  '2026-10-22 m1r2 yachi lock 59 (mirrored)',
  '2026-10-22 m2r7 yachi lock 13',
];
const FOLLOWUP_NOT_FIRED: string[] = [
  '2026-09-17 m6r7 yachi lock 90 (next_t_elsewhere at lock 96)',
  '2026-09-17 m7r4 yachi lock 103 (past_verified at lock 111)',
];
const GARBAGE_IN_WINDOW: string[] = [
  '2026-09-11 m1r1 yachi lock 184',
  '2026-09-11 m4r5 yachi lock 107',
  '2026-09-17 m3r4 yachi lock 45',
  '2026-09-19 m1r2 yachi lock 59',
  '2026-10-09 m2r6 yachi lock 36',
  '2026-10-12 m4r6 yachi lock 70',
  '2026-10-22 m1r2 yachi lock 59',
];
const DTCANNON_IN_OPENER: string[] = [
  '2026-08-14 m3r4 yachi lock 13',
  '2026-08-25 m9r3 yachi lock 13',
  '2026-09-17 m7r4 yachi lock 13',
  '2026-10-03 m7r3 yachi lock 14',
  '2026-10-22 m2r7 yachi lock 13',
];
const RECON_DROPPED_TSD: string[] = [];
/** the hits that fail the build rules (`technique-qualify.ts`), with the rules they fail */
const NOT_QUALIFIED: string[] = [
  '2026-09-11 m4r5 yachi lock 107 (ownership_unverified)',
];
/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 701, yachi: 535 };

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5636, in_opener: 1113, mid_game: 4523 },
                    yachi: { all: 5100, in_opener: 1317, mid_game: 3783 } };
const HITS = {pinglamb: {all: 0, in_opener: 0, mid_game: 0, mirrored: 0, garbage_in_window: 0}, yachi: {all: 20, in_opener: 5, mid_game: 15, mirrored: 8, garbage_in_window: 7}};
const FOLLOWUP_FIRED = { pinglamb: 0, yachi: 18 };
const QUALIFIED = { pinglamb: 0, yachi: 19 };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {under: {TSS: {pinglamb: 0, yachi: 0}, TST: {pinglamb: 0, yachi: 0}, mini_TSS: {pinglamb: 0, yachi: 0}, mini_TSD: {pinglamb: 0, yachi: 0}}, ablation: {no_must_empty: {pinglamb: 0, yachi: 21}, no_roof: {pinglamb: 2353, yachi: 2163}, t_overlap: {pinglamb: 0, yachi: 20}}, orientation_baseline: {pinglamb: 52, yachi: 67}};
/** What discriminates, measured: full TSDs whose anchored T meets ONE part of the window. `above` is the four
 *  rows over the T (the overhang over the TST stem, its second cell, the stem walled both sides, the nub row of
 *  the TST slot), of which `overhang` is the top two and `tst_side` the next two; `cleared` the two rows the TSD
 *  clears; `below` the stem's bottom cell under the nub and its two walls. */
const PART_ONLY = { above: 21, overhang: 23, tst_side: 21, cleared: 10617, below: 4516 };

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  followupAnyT: 'the one hit whose next T missed the slot (next_t_elsewhere) placed a T that scored no T-spin, so counting any scored T changes nothing',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(DTCANNON, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;
const hk = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
const hitKeys = () => new Set<string>(art().hits.map(hk));
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
  expect(n).toBe(15141);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the page\'s drawings: once, at the agreement slot, as drawn, nowhere else', () => {
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  const v = TR.variants[0];
  const page = v.agreement.filter((a: any) => byId.has(a.board));
  expect(page.map((a: any) => a.board).sort()).toEqual([...v.fires_on].sort());
  expect(page.length).toBe(8);
  for (const a of page) {
    const board = asBoard(byId.get(a.board).rows, ch => ch !== '-' && ch !== 'U');
    const lock: Cell[] = a.t_cells.map(([row, col]: number[]) => ({ row, col }));
    expect(fires(board, lock), a.board).toEqual([false]);
    const others = tPlacements(board).filter(cs => cs.some(q => !lock.some(x => x.row === q.row && x.col === q.col)));
    for (const cs of others) expect(fires(board, cs), a.board).toEqual([]);
  }
  // the page's boards the gate records as misses: no T placement fires (a spin board read with its U taken out),
  // except one, measured: dtdt.tst draws the first DT's TST with the second DT already stacked above it, and the
  // window fires, as drawn, at that second DT's TSD slot (a T there completes two rows) — DTDT is two DT Cannons
  const SECOND_DT: Record<string, string> = { 'dtdt.tst': '5,6 5,7 5,8 6,7' };
  for (const id of v.misses) {
    const board = asBoard(byId.get(id).rows, ch => ch !== '-' && ch !== 'U');
    const got = tPlacements(board).filter(cs => fires(board, cs).length)
      .map(cs => { expect(fires(board, cs), id).toEqual([false]); return cs.map(q => `${q.row},${q.col}`).sort().join(' '); });
    expect(got, id).toEqual(SECOND_DT[id] ? [SECOND_DT[id]] : []);
    if (SECOND_DT[id]) {
      const t = new Set(SECOND_DT[id].split(' '));
      const full = board.filter((row, r) => [...row].every((ch, c) => ch === 'X' || t.has(`${r},${c}`))).length;
      expect(full, id).toBe(2);
    }
  }
});

test('the Python twin on the routes: windowMatch fires on exactly the routes boards the gate records', () => {
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
  const want = [...TR.cross_source.fires, ...(TR.cross_source.also ?? [])]
    .map((e: any) => `${e.file} ${e.node} ${e.variant} ${e.mirrored}`);
  expect(got.sort()).toEqual(want.sort());
  expect(want).toEqual(['sdpcspin-routes.json 3.second.cspin.dt#1 dtcannon true',
                        'sdpcspin-routes.json 3.second.cspin.dt#2 dtcannon true']);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [1, 7], cols: [0, 3] });
  expect(v.t_cells).toEqual([[5, 1], [5, 2], [5, 3], [6, 2]]);
  expect(v.followup).toMatchObject({ spin: 'TST', lines: 3, t_cells_pre_clear: [[3, 2], [4, 1], [4, 2], [7, 2]] });
  expect(TR.empty_letters).toBe('');
  expect(prepare(TR, v).map(P => P.followupKind)).toEqual(['full:3', 'full:3']);
});

test('named lists: every hit, every follow-up miss, the opener hits, garbage, the hits that fail the build rules', () => {
  const L = art().lists;
  checkNamedList('dtcannon_hits', L.dtcannon_hits, DTCANNON_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('dtcannon_in_opener', L.dtcannon_in_opener, DTCANNON_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkNamedList('not_qualified', L.not_qualified, NOT_QUALIFIED);
  checkHitPositions(art(), SESSIONS, ROOT, [...DTCANNON_HITS, ...FOLLOWUP_NOT_FIRED, ...GARBAGE_IN_WINDOW]);
  expect(art().hits.length).toBe(DTCANNON_HITS.length);
  expect(L.qualified_hits.length + L.not_qualified.length).toBe(DTCANNON_HITS.length);
});

test('the opener hits are the ordering metric\'s Double-first rounds: a second input reaching the same rounds', () => {
  const op = art().hits.filter((h: any) => h.in_opener);
  expect(op.length).toBe(DTCANNON_IN_OPENER.length);
  for (const h of op) {
    const of = JSON.parse(readFileSync(`${ROOT}/${h.session}/sim/opener-facts.json`, 'utf8'));
    const r = of.ordering.per_round.find((x: any) => x.file === h.file && x.round === h.round_index0 && x.user === h.player);
    expect(r, `${h.session} ${h.file} ${h.round_index0}`).toBeDefined();
    expect(r.window_complete).toBe(true);
    expect(r.dt_order, `${h.session} ${h.file} ${h.round_index0}`).toBe(1);
    // and the TST the page draws next fired, which is the Triple the ordering metric saw second
    expect(h.followup.fired).toBe(true);
  }
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
}, 600_000);

test('pinned: denominators, hits, follow-ups, qualify, controls', () => {
  const a = art(), v = a.variants.dtcannon;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TSD, u).toEqual(TSD_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u].fired, u).toBe(FOLLOWUP_FIRED[u]);
    expect(v.followup_by_player[u].fired + total(v.followup_by_player[u].not_fired)).toBe((HITS as any)[u].all);
    expect(a.qualify.by_player[u].qualified, u).toBe(QUALIFIED[u]);
  }
  expect(v.controls).toEqual(CONTROLS);
});

test('what discriminates: each part of the window alone, with the T anchored', () => {
  const v = TR.variants[0];
  const [top] = v.t_cells[0]!;          // the T's row; the nub row is under it
  const parts: Record<string, (r: number) => boolean> = {
    above: r => r < top, overhang: r => r <= top - 3, tst_side: r => r === top - 2 || r === top - 1,
    cleared: r => r === top || r === top + 1, below: r => r > top + 1,
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
}, 600_000);

test('the other flat-T windows are not this: a clash in every pairing of hands, and no shared hit', () => {
  const norm = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  const mine = prepare(TR, TR.variants[0]).map(norm);
  const mineHits = hitKeys();
  const seen: string[] = [];
  for (const key of ['stmbcave', 'doubledagger', 'btcannon', 'cutcopy', 'shachikutrain', 'parapet', 'kaidan']) {
    const other = TECHNIQUES[key]!;
    const tr = JSON.parse(readFileSync(other.transcriptionPath, 'utf8'));
    for (const ov of tr.variants) {
      const theirs = prepare(tr, ov).map(norm);
      if (theirs[0]!.T !== mine[0]!.T) continue;      // a stood T: never the same lock as this page's
      seen.push(`${key}:${ov.id}`);
      for (const a of mine) for (const b of theirs) {
        const clash = [...a.cells].filter(([k, x]) => b.cells.has(k) && b.cells.get(k) !== x && x !== 'T');
        expect(clash.length, `${key}:${ov.id}`).toBeGreaterThan(0);
      }
    }
    const hits = JSON.parse(readFileSync(other.artefactPath, 'utf8')).hits;
    expect(hits.filter((h: any) => mineHits.has(hk(h))), key).toEqual([]);
  }
  expect(seen).toEqual(['stmbcave:stmbcave', 'doubledagger:doubledagger', 'btcannon:btcannon', 'cutcopy:cutcopy',
                        'cutcopy:uncut', 'shachikutrain:shachikutrain', 'parapet:parapet', 'kaidan:kaidan']);
});

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.dtcannon.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.dtcannon.followup_by_player).map(([u, x]: any) => [u, x.fired])));
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

  a = mut({ includeMini: true });
  expect(tss(a)).toBe(tss(b) + b.denominators.pinglamb.mini_TSS.all + b.denominators.yachi.mini_TSS.all);

  a = mut({ noMustEmpty: true });
  expect(sum(a, 'all')).toBe(total(b.variants.dtcannon.controls.ablation.no_must_empty));
  // the window less its roof (the overhang and the stem's walls) is symmetric about the T, so a lock matches both
  // hands: refused (the no_roof control counts per hand and does not throw)
  expect(() => run({ noRoof: true })).toThrow(/matches as drawn AND mirrored/);
  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.dtcannon.controls.ablation.t_overlap));

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  // garbage read as EMPTY: exactly the hits with garbage in their window are lost
  a = mut({ garbageEmpty: true });
  expect(a.hits.map(hk)).toEqual(b.hits.filter((h: any) => !h.garbage_in_window).map(hk));

  // the slot carried in the drawn columns on a mirrored hit: no mirrored follow-up fires
  a = mut({ followupUnmirrored: true });
  expect(a.hits.map(hk)).toEqual(b.hits.map(hk));
  expect(a.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBe(0);
  expect(b.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBeGreaterThan(0);

  // no row map: the TST slot is split by the TSD's own two cleared rows, so it is never joined and nothing fires
  a = mut({ followupNoRowmap: true });
  expect(a.hits.map(hk)).toEqual(b.hits.map(hk));
  expect(fired(a)).toBe(0);

  a = mut({ openerLt: true });
  expect(tsd(a, 'in_opener')).toBeLessThan(tsd(b, 'in_opener'));
  expect(tsd(a)).toBe(tsd(b));

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);
