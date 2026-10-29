/**
 * The 千鳥格子 (Cut Copy) technique artefact (`analysis/cutcopy-facts.json`, from `pipeline/sim/emit-technique-facts.ts
 * --technique cutcopy`; the rules are the shared `technique-facts.ts`, the profile `technique-profile-cutcopy.ts`, the
 * shape the gated `pipeline/openers/cutcopy-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for
 *      every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on each of harddrop's Cut_copy drawings the gate
 *      records, and on the Cut Copy harddrop's BT_Cannon page draws (read out of `btcannon-technique.json`) — once,
 *      at its drawn T, in its recorded hand, and at no other T placement; at no drawn T the gate names as a miss;
 *      on each no-T board the gate records, at its recorded placement; on this page's own drawings at their
 *      agreement slots; on the T-hole build with its Z left out, nowhere (the page's 「Z may go in after the first
 *      T-spin」, which the window refuses: the overhang must stand before the first TSD); and on no routes board (the gate's `cross_source.fires` is
 *      empty, with its reason).
 *   4. STMB CAVE, ダブルダガー AND BT砲 ARE NOT THIS: all four lay the T flat, nub down; anchored on the same T this
 *      window clashes with each of theirs on a cell in every pairing of hands (re-derived from the transcriptions),
 *      so no lock is a hit of two of them, and none is.
 *   5. WHAT DISCRIMINATES: measured per window part, with the T anchored (the row above the T, the cleared rows,
 *      the row under them), against the headline: no single part gives it. The cleared rows are entailed by the
 *      clear and do no work; the row below cuts them down by at least ten times and the rows above (with the
 *      overhang) by ten times more again — both asserted — so those two are what discriminate.
 *   6. NAMED lists, not bounds; pinned per-player figures; mutants, each with its asserted symptom (the one
 *      equivalent mutants named, measured, asserted to STAY byte-identical).
 *   7. THE FOLLOW-UP on the page's own drawings: the TSD into `basic.spin`'s slot, then the T into the slot
 *      `second.spin` draws, as a two-lock digest, as drawn and mirrored — it fires, and the follow-up mutants
 *      break it there as they do on the corpus.
 *
 *   8. THE SECOND VARIANT (`uncut`, harddrop's second generic type, its board an external node): its window fires on each
 *      of its harddrop drawings at the drawn T and nowhere else, clashes with the first type's on a cell, and its
 *      follow-up search fires on harddrop's own drawing as a two-lock digest, as drawn and mirrored. Its corpus hits
 *      are a named list like the first type's — measured EMPTY — and its controls and per-part counts are pinned.
 *   9. TETRISちゃんねる: its two agreement boards fire the first type's window at their slots, and its 江戸城 (009) is ONE
 *      Cut Copy: the middle T's outer slot has no overhang, so the window fires there only when read without its
 *      `window_extra` — the TS twin of the gate's measurement. On the corpus, a hit whose
 *      follow-up is itself a hit is a named list (`followup_is_a_hit`), measured EMPTY.
 *
 * window_off_board is not listed entry by entry: it is every flat, nub-down T at a TSD whose window leaves the
 * board before the matcher found a mismatch (the window reaches two columns past one end of the T and three past
 * the other), thousands of them. It is pinned per player as a count, and every entry is checked to be such a T
 * with its window off the board in at least one hand and not a hit (STMB Cave's treatment, for the same reason).
 *
 * Run: bun test pipeline/openers/cutcopy.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, classify, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { CUTCOPY } from '../sim/technique-profile-cutcopy.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { DOUBLEDAGGER } from '../sim/technique-profile-doubledagger.ts';
import { BTCANNON } from '../sim/technique-profile-btcannon.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29']);
const ART_PATH = `${import.meta.dir}/../../analysis/cutcopy-facts.json`;
const TR = JSON.parse(readFileSync(CUTCOPY.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the flat T into the page's window, as drawn (roof over the T's right end) or mirrored. */
const CUTCOPY_HITS: string[] = [
  "2026-09-18 m16r2 yachi lock 215 (mirrored)",
  "2026-10-20 m2r1 yachi lock 117",
];
const FOLLOWUP_NOT_FIRED: string[] = [
  "2026-09-18 m16r2 yachi lock 215 (slot_filled_before_t at lock 216)",
];
const GARBAGE_IN_WINDOW: string[] = [
  "2026-10-20 m2r1 yachi lock 117",
];
const CUTCOPY_IN_OPENER: string[] = [];
const RECON_DROPPED_TSD: string[] = [];
/** The second variant's hits (harddrop's second type): measured, none. */
const UNCUT_HITS: string[] = [];
/** A hit whose follow-up fired at a lock that is itself a hit (two Cut Copies in a row): measured, none. */
const FOLLOWUP_IS_A_HIT: string[] = [];
/** window_off_board, per variant and player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD: Record<string, Record<string, number>> = {
  cutcopy: { pinglamb: 1832, yachi: 1869 }, uncut: { pinglamb: 2263, yachi: 2287 },
};

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5884, in_opener: 1162, mid_game: 4722 },
                    yachi: { all: 5340, in_opener: 1375, mid_game: 3965 } };
/** Per player: hits, their split, the mirrored ones, the ones with garbage in the window, the follow-ups. */
const HITS = { pinglamb: {all:  0,  in_opener:  0,  mid_game:  0,  mirrored:  0,  garbage_in_window:  0},
               yachi: {all:  2,  in_opener:  0,  mid_game:  2,  mirrored:  1,  garbage_in_window:  1} };
const FOLLOWUP = {
  pinglamb: {fired:  0,  not_fired:  {}},
  yachi: {fired:  1,  not_fired:  {slot_filled_before_t:  1}},
};
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 0, yachi: 0 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: {pinglamb:  288,  yachi:  174}, no_roof: {pinglamb:  454,  yachi:  380},
              t_overlap: {pinglamb:  6,  yachi:  5} },
  orientation_baseline: { pinglamb: 54, yachi: 73 },
};
/** What discriminates, measured: full TSDs (not only hits) whose anchored T meets ONE part of the window — the
 *  row above the T (the outer slot's arms, the wall beside them, the roof and the cell beyond it) with the
 *  overhang over it (`window_extra`), the two rows the TSD clears, or the row under them (the outer slot's nub cell,
 *  walled). The cleared rows are entailed by the clear and admit every flat, nub-down full TSD whose window is on
 *  the board, so they do no work. The row below cuts that down by at least ten times, and the rows above (the
 *  overhang among them) by at least ten times more again (both asserted where PART_ONLY is checked); neither alone
 *  reaches the headline, so those two are what discriminate. The
 *  `no_roof` ablation (the window less the row above the T) is exactly `below`. */
const PART_ONLY = { above: 31, cleared: 9794, below: 834 };
/** The second variant (harddrop's second type), pinned the same way: its hits (none), its follow-ups, its controls,
 *  and the full TSDs each part of its window admits with the T anchored (the row above the T, the cleared rows, the
 *  two rows of the second slot under them). */
const HITS_UNCUT = { pinglamb: { all: 0, in_opener: 0, mid_game: 0, mirrored: 0, garbage_in_window: 0 },
                     yachi: { all: 0, in_opener: 0, mid_game: 0, mirrored: 0, garbage_in_window: 0 } };
const FOLLOWUP_UNCUT = { pinglamb: { fired: 0, not_fired: {} }, yachi: { fired: 0, not_fired: {} } };
const CONTROLS_UNCUT = {
  under: { TSS: { pinglamb: 0, yachi: 0 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 750, yachi: 480 }, no_roof: { pinglamb: 1, yachi: 8 },
              t_overlap: { pinglamb: 18, yachi: 5 } },
  orientation_baseline: { pinglamb: 54, yachi: 73 },
};
const PART_ONLY_UNCUT = { above: 4718, cleared: 9794, below: 9 };
/** The second type and STMB Cave are a RELATION, not a clash: anchored on the same flat T in OPPOSITE hands their
 *  windows agree on every cell both read (the STMB Cave page's own 「連続してTSD」 board is the second type, mirrored).
 *  The corpus locks that are hits of both: measured, none (the second type has no hit). */
const STMBCAVE_ALSO_UNCUT: string[] = [];

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  followupUnmirrored: 'no mirrored hit\'s follow-up fires: the one mirrored hit\'s slot is filled before its next T, '
    + 'which reads the same in either hand (killed on the page\'s own two-lock digest instead)',
  followupAnyT: 'every hit\'s next T either fires the full TSD or finds its slot filled first, so accepting any T '
    + 'spin changes no follow-up (killed on the page\'s own two-lock digest instead)',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(CUTCOPY, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;
const hitKeys = (a: any = art()) => new Set(a.hits.map((h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`));
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

/** A drawing (rows top first) in the matcher's frame: `filled` says which letters are filled. */
function asBoard(rows: string[], filled: (ch: string) => boolean) {
  return rows.map(r => [...r].map(ch => filled(ch) ? 'X' : '.').join(''));
}
const cellsOf = (slot: number[][]): Cell[] => slot.map(([row, col]) => ({ row: row!, col: col! }));
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
const firesV = (board: string[], lock: Cell[], vi = 0) =>
  prepare(TR, TR.variants[vi]).filter(P => !!windowMatch(board, lock, P)).map(P => P.mirrored);
const fires = (board: string[], lock: Cell[]) => firesV(board, lock, 0);
/** every variant's window at one placement: [variant, hand] */
const firesAny = (board: string[], lock: Cell[]) =>
  TR.variants.flatMap((v: any, vi: number) => firesV(board, lock, vi).map(m => [v.id, m]));
const same = (a: Cell[], b: Cell[]) => a.length === b.length && a.every(q => b.some(x => x.row === q.row && x.col === q.col));

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
  expect(n).toBe(15834);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the drawings: windowMatch fires where the gate records it, and nowhere else', () => {
  const hd = TR.cross_source.harddrop;
  const pre = (rows: string[]) => asBoard(rows, ch => ch !== '-' && ch !== 'U');
  // harddrop's Cut_copy drawings: once, the recorded variant's window, at the drawn T, in the recorded hand; no window
  // at any other placement
  expect(hd.drawings.map((d: any) => d.variant).sort()).toEqual([...Array(5).fill('cutcopy'), ...Array(8).fill('uncut')]);
  for (const vid of ['cutcopy', 'uncut'])
    expect(hd.drawings.filter((d: any) => d.section === 'Generic Structures' && d.variant === vid).length, vid).toBe(1);
  for (const d of hd.drawings) {
    const board = pre(d.rows), lock = cellsOf(d.slot);
    expect(firesAny(board, lock), `table ${d.table} board ${d.board}`).toEqual([[d.variant, d.mirrored]]);
    for (const cs of tPlacements(board).filter(cs => !same(cs, lock)))
      expect(firesAny(board, cs), `table ${d.table} board ${d.board}`).toEqual([]);
  }
  // every other drawn T on the page: no window fires at it
  expect(hd.drawn_t_not_fired.length).toBe(8);
  for (const d of hd.drawn_t_not_fired)
    expect(firesAny(pre(d.rows), cellsOf(d.slot)), `table ${d.table} board ${d.board}`).toEqual([]);
  // its boards with no T drawn: the recorded variant's window fires at the recorded placement, in the recorded hand
  expect(hd.fires_without_slot.length).toBe(5);
  for (const d of hd.fires_without_slot)
    expect(firesAny(pre(d.rows), cellsOf(d.slot)), `table ${d.table} board ${d.board}`).toEqual([[d.variant, d.mirrored]]);
  // the Cut Copy harddrop's BT_Cannon page draws, read out of the BT砲 transcription by (table, board)
  const bc = TR.cross_source.bt_cannon;
  const bt = JSON.parse(readFileSync(`${import.meta.dir}/${bc.file}`, 'utf8')).cross_source.harddrop;
  const btBoards = [...bt.drawings, ...bt.drawn_t_not_fired, ...bt.fires_without_slot];
  const e = btBoards.filter((x: any) => x.table === bc.table && x.board === bc.board);
  expect(e.length).toBe(1);
  expect(e[0].note.toLowerCase()).toContain('cut copy');
  const lockOf = (rows: string[]) => rows.flatMap((r, i) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));
  const fired = btBoards.filter((x: any) => {
    const board = pre(x.rows), lock = lockOf(x.rows);
    return lock.length ? fires(board, lock).length > 0 : tPlacements(board).some(cs => fires(board, cs).length);
  }).map((x: any) => `${x.table},${x.board}`);
  expect(fired).toEqual([`${bc.table},${bc.board}`]);
  expect(firesAny(pre(e[0].rows), lockOf(e[0].rows))).toEqual([['cutcopy', bc.mirrored]]);
  expect(btBoards.filter((x: any) => {
    const board = pre(x.rows), lock = lockOf(x.rows);
    return lock.length ? firesV(board, lock, 1).length > 0 : tPlacements(board).some(cs => firesV(board, cs, 1).length);
  })).toEqual([]);
  // this page's own drawings of the shape, each at its agreement slot, in its hand
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  const v = TR.variants[0];
  expect(v.agreement.map((a: any) => [a.board, a.mirrored]).sort())
    .toEqual([...v.fires_on.map((b: string) => [b, false]), ...v.fires_mirrored.map((b: string) => [b, true])].sort());
  for (const a of v.agreement) {
    const board = asBoard(byId.get(a.board).rows, ch => ch !== '-');
    expect(fires(board, cellsOf(a.t_cells)), a.board).toEqual([a.mirrored]);
  }
  // not expressed: the T-hole build with its Z left out (the page lets it go in after the first T-spin)
  const ne = v.not_expressed[0];
  expect([ne.board, ne.less]).toEqual(['hole.osz', 'z']);
  const less = asBoard(byId.get(ne.board).rows, ch => ch !== '-' && !ne.less.includes(ch));
  expect(tPlacements(less).filter(cs => firesAny(less, cs).length)).toEqual([]);
  // and on no routes board (the gate records none, with its reason)
  const got: string[] = [];
  const dir = `${import.meta.dir}`;
  for (const f of readdirSync(dir).filter(x => x.endsWith('-routes.json')).sort()) {
    for (const n of JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const cells = lockOf(n.rows);
      if (cells.length !== 4) continue;
      if (firesAny(pre(n.rows), cells).length) got.push(`${f} ${n.id}`);
    }
  }
  expect(got).toEqual([]);
  expect(TR.cross_source.fires).toEqual([]);
  expect(TR.cross_source.also).toEqual([]);
  expect(TR.cross_source.routes_fire_none.length).toBeGreaterThan(0);
});

test('Tetrisちゃんねる: its agreement boards fire the first type\'s window at their slots, and 江戸城 is one Cut Copy (its middle slot has no overhang)', () => {
  const tc = TR.cross_source.tetrisch;
  const img = (n: string) => tc.images.find((x: any) => x.file === `cutcopy_${n}.jpg`).rows as string[];
  const read = (rows: string[]) => asBoard(rows, ch => ch !== '.');
  for (const n of Object.keys(tc.slots)) {
    const board = read(img(n)), lock = cellsOf(tc.slots[n]);
    expect(firesAny(board, lock), n).toEqual([['cutcopy', false]]);
    for (const cs of tPlacements(board).filter(cs => !same(cs, lock))) expect(firesAny(board, cs), n).toEqual([]);
  }
  // the basic sequence's slot is 003's T, and the boards after each TSD fire no window anywhere
  const tOf = (rows: string[]) => rows.flatMap((r, row) => [...r].flatMap((ch, col) => ch === 'T' ? [{ row, col }] : []));
  expect(same(cellsOf(tc.slots[tc.basic.terrain]), tOf(img(tc.basic.spin)))).toBe(true);
  for (const n of [tc.basic.after, tc.basic.second_after]) {
    const board = read(img(n));
    expect(tPlacements(board).filter(cs => firesAny(board, cs).length), n).toEqual([]);
  }
  // 江戸城: the innermost T fires the window; on the board it leaves, the middle T's outer slot has no overhang, so
  // the window fires nowhere — read WITHOUT its `window_extra` (the overhang) it fires MIRRORED at exactly one
  // placement, the carried follow-up slot; then the last TSD, which leaves the board empty. One Cut Copy, not two.
  const place = (board: string[], cells: Cell[]) => {
    const g = board.map(r => [...r]);
    for (const q of cells) { expect(g[q.row]![q.col]).toBe('.'); g[q.row]![q.col] = 'X'; }
    const full = g.flatMap((r, i) => r.every(x => x !== '.') ? [i] : []);
    return { full, after: [...Array(full.length).fill('.'.repeat(10)), ...g.filter((_, i) => !full.includes(i)).map(r => r.join(''))] };
  };
  const bare = { ...TR.variants[0], window_extra: undefined };
  const firesBare = (board: string[], lock: Cell[]) =>
    prepare(TR, bare).filter(P => !!windowMatch(board, lock, P)).map(P => P.mirrored);
  let board = read(img(tc.edo.image));
  const first = cellsOf(tc.slots[tc.edo.image]);
  expect(firesAny(board, first)).toEqual([['cutcopy', false]]);
  const s1 = place(board, first);
  expect(s1.full.length).toBe(2);
  board = s1.after;
  expect(tPlacements(board).filter(cs => firesAny(board, cs).length)).toEqual([]);
  const second = tPlacements(board).filter(cs => firesBare(board, cs).length);
  expect(second.length).toBe(1);
  expect(firesBare(board, second[0]!)).toEqual([true]);
  const s2 = place(board, second[0]!);
  expect(s2.full.length).toBe(2);
  board = s2.after;
  expect(tPlacements(board).filter(cs => firesAny(board, cs).length)).toEqual([]);
  const last = tPlacements(board).filter(cs => place(board, cs).full.length === 2);
  expect(last.length).toBe(1);
  expect(place(board, last[0]!).after.every(r => r === '.'.repeat(10))).toBe(true);
  expect(tc.edo.tsds).toBe(3);
  expect(tc.edo.hits).toBe(1);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [2, 5], cols: [4, 9] });
  expect(v.t_cells).toEqual([[3, 6], [3, 7], [3, 8], [4, 7]]);
  expect(v.roof_cells).toEqual([[2, 4], [2, 8], [2, 9]]);
  // the outer slot's overhang, read outside the box (yachi's reading: it is placed before the first T-spin)
  expect(v.window_extra.cells).toEqual([[1, 5]]);
  expect(v.window_extra.note.length).toBeGreaterThan(0);
  expect(v.followup).toMatchObject({ spin: 'TSD', lines: 2, t_cells_pre_clear: [[2, 5], [2, 6], [2, 7], [5, 6]] });
  expect(TR.empty_letters).toBe('');
  expect(prepare(TR, v).map(P => P.followupKind)).toEqual(['full:2', 'full:2']);
  // the second variant: harddrop's second type, on its external board
  expect(TR.variants.map((x: any) => x.id)).toEqual(['cutcopy', 'uncut']);
  const u = TR.variants[1];
  expect(TR.nodes.find((n: any) => n.id === u.board).external).toBe('harddrop');
  expect(TR.page_order).not.toContain(u.board);
  expect(u.window_basis).toBe('agreement');
  expect(u.window).toEqual({ rows: [1, 5], cols: [0, 5] });
  expect(u.t_cells).toEqual(v.t_cells.map(([r, c]: number[]) => [r! - 1, c! - 4]));
  expect(u.followup).toMatchObject({ spin: 'TSD', lines: 2, t_cells_pre_clear: [[4, 1], [4, 2], [4, 3], [5, 2]] });
  expect(prepare(TR, u).map(P => P.followupKind)).toEqual(['full:2', 'full:2']);
});

test('named lists: every hit, every follow-up miss, the opener hits, garbage, the empty lists', () => {
  const L = art().lists;
  checkNamedList('cutcopy_hits', L.cutcopy_hits, CUTCOPY_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('cutcopy_in_opener', L.cutcopy_in_opener, CUTCOPY_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkNamedList('uncut_hits', L.uncut_hits, UNCUT_HITS);
  checkNamedList('followup_is_a_hit', L.followup_is_a_hit, FOLLOWUP_IS_A_HIT);
  checkHitPositions(art(), SESSIONS, ROOT, [...CUTCOPY_HITS, ...UNCUT_HITS, ...FOLLOWUP_NOT_FIRED, ...GARBAGE_IN_WINDOW,
                                            ...CUTCOPY_IN_OPENER]);
  expect(art().hits.length).toBe(CUTCOPY_HITS.length + UNCUT_HITS.length);
  // no lock is a hit of both variants
  const keys = art().hits.map((h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`);
  expect(new Set(keys).size).toBe(keys.length);
});

test('window_off_board: pinned per variant and player, every entry a flat nub-down T whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  // a lock is off the board for one variant whatever the other found there
  const hits = new Set(art().hits.map((h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}|${h.variant}`));
  for (const v of TR.variants) {
    const mine = L.filter(x => x.endsWith(` (${v.id})`)).map(x => x.slice(0, -` (${v.id})`.length));
    for (const u of ['pinglamb', 'yachi'] as const)
      expect(mine.filter(x => x.split(' ')[2] === u).length, `${v.id} ${u}`).toBe(WINDOW_OFF_BOARD[v.id]![u]);
    // the window's rows and columns, its `window_extra` cells (the first type's overhang) included
    const ex: [number, number][] = v.window_extra?.cells ?? [];
    const r0 = Math.min(v.window.rows[0], ...ex.map(x => x[0])), r1 = Math.max(v.window.rows[1], ...ex.map(x => x[0]));
    const c0 = Math.min(v.window.cols[0], ...ex.map(x => x[1])), c1 = Math.max(v.window.cols[1], ...ex.map(x => x[1]));
    const [nr, nc] = v.t_cells.reduce((a: number[], b: number[]) => (b[0]! > a[0]! ? b : a));
    const want = new Set<string>();
    for (const d of digests()) for (const s of scored(d)) {
      if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
      const n = nubOf(s.lk.cells);
      if (!n || hits.has(`${keyOf(d, s.i)}|${v.id}`)) continue;
      const rowsOff = n.row + (r0 - nr) < 0 || n.row + (r1 - nr) >= H;
      const drawnOff = rowsOff || n.col + (c0 - nc) < 0 || n.col + (c1 - nc) > 9;
      const mirrOff = rowsOff || n.col - (c1 - nc) < 0 || n.col - (c0 - nc) > 9;
      if (drawnOff || mirrOff) want.add(nameOf(d, s.i));
    }
    for (const x of mine) expect(want.has(x), `${v.id} ${x}`).toBe(true);
    expect(new Set(mine).size).toBe(mine.length);
  }
  expect(L.every(x => TR.variants.some((v: any) => x.endsWith(` (${v.id})`)))).toBe(true);
}, 600_000);

test('pinned: denominators, hits, follow-ups, controls', () => {
  const a = art(), v = a.variants.cutcopy;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TSD, u).toEqual(TSD_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u], u).toEqual(FOLLOWUP[u]);
    expect(FOLLOWUP[u].fired + total(FOLLOWUP[u].not_fired)).toBe(HITS[u].all);
  }
  expect(v.controls).toEqual(CONTROLS);
  for (const k of ['no_must_empty', 'no_roof'] as const)
    for (const u of ['pinglamb', 'yachi'] as const) expect(v.controls.ablation[k][u]).toBeGreaterThanOrEqual(HITS[u].all);
  const w = a.variants.uncut;
  expect(Object.keys(a.variants)).toEqual(['cutcopy', 'uncut']);
  expect(w.hits_by_player).toEqual(HITS_UNCUT);
  expect(w.followup_by_player).toEqual(FOLLOWUP_UNCUT);
  expect(w.controls).toEqual(CONTROLS_UNCUT);
});

test('STMB Cave, Double Dagger and BT砲 are not this: anchored on the same flat T, the windows clash in every pairing', () => {
  const norm = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  const mine = hitKeys();
  // the two variants against each other, in every pairing of hands
  for (const a of prepare(TR, TR.variants[0]).map(norm)) for (const b of prepare(TR, TR.variants[1]).map(norm)) {
    expect(a.T).toBe(b.T);
    expect([...a.cells].filter(([k, v]) => b.cells.has(k) && b.cells.get(k) !== v && v !== 'T').length).toBeGreaterThan(0);
  }
  for (const other of [STMBCAVE, DOUBLEDAGGER, BTCANNON]) {
    const tr = JSON.parse(readFileSync(other.transcriptionPath, 'utf8'));
    for (const mv of TR.variants)
    for (const [ia, a] of prepare(TR, mv).map(norm).entries())
    for (const [ib, b] of prepare(tr, tr.variants[0]).map(norm).entries()) {
      expect(a.T, other.key).toBe(b.T);
      const clash = [...a.cells].filter(([k, v]) => b.cells.has(k) && b.cells.get(k) !== v && v !== 'T');
      // the one relation: the second type against STMB Cave in opposite hands
      if (mv.id === 'uncut' && other === STMBCAVE && ia !== ib) expect(clash, `${mv.id} ${other.key}`).toEqual([]);
      else expect(clash.length, `${mv.id} ${other.key}`).toBeGreaterThan(0);
    }
    if (other === STMBCAVE) {
      const k2 = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
      const both = JSON.parse(readFileSync(other.artefactPath, 'utf8')).hits
        .filter((h: any) => art().hits.some((x: any) => x.variant === 'uncut' && k2(x) === k2(h)))
        .map((h: any) => `${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock}`);
      checkNamedList('stmbcave_also_uncut', both, STMBCAVE_ALSO_UNCUT);
    }
    const theirs = JSON.parse(readFileSync(other.artefactPath, 'utf8')).hits;
    const k = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
    expect(theirs.filter((h: any) => mine.has(k(h))), other.key).toEqual([]);
  }
});

test('what discriminates, the second type: each part of its window alone, with the T anchored', () => {
  const v = TR.variants[1];
  const [top] = v.t_cells[0]!;
  const parts: Record<keyof typeof PART_ONLY_UNCUT, (r: number) => boolean> = {
    above: r => r < top, cleared: r => r === top || r === top + 1, below: r => r > top + 1,
  };
  const got: Record<string, number> = {};
  for (const [name, keep] of Object.entries(parts)) {
    const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || keep(x.r)) }));
    let n = 0;
    for (const d of digests()) for (const s of scored(d)) {
      if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
      if (preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) n++;
    }
    got[name] = n;
  }
  expect(got).toEqual(PART_ONLY_UNCUT);
  // the no_roof ablation (the window less the row above the T) is exactly the `below` part with the cleared rows
  expect(total(art().variants.uncut.controls.ablation.no_roof)).toBe(PART_ONLY_UNCUT.below);
}, 600_000);

test('what discriminates: each part of the window alone, with the T anchored, against the headline', () => {
  const v = TR.variants[0];
  const [top] = v.t_cells[0]!;          // the T's row; the nub row is under it
  const parts: Record<keyof typeof PART_ONLY, (r: number) => boolean> = {
    above: r => r < top, cleared: r => r === top || r === top + 1, below: r => r > top + 1,
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
  for (const n of Object.values(PART_ONLY)) expect(n).toBeGreaterThan(art().hits.length);
  // what the comment above claims: the row below cuts the cleared rows by at least ten times, the row above by less
  expect(PART_ONLY.cleared).toBeGreaterThanOrEqual(10 * PART_ONLY.below);
  expect(PART_ONLY.below).toBeGreaterThanOrEqual(10 * PART_ONLY.above);
  // the no_roof ablation (the window less the row above the T) is exactly the `below` part
  expect(total(art().variants.cutcopy.controls.ablation.no_roof)).toBe(PART_ONLY.below);
}, 600_000);

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(31);
  expect(c.rowmap_steps).toBe(275898);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.cutcopy.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.cutcopy.followup_by_player).map(([u, x]: any) => [u, x.fired])));
  const tsd = (a: any, k = 'all') => a.denominators.pinglamb.TSD[k] + a.denominators.yachi.TSD[k];
  const tss = (a: any) => a.denominators.pinglamb.TSS.all + a.denominators.yachi.TSS.all;
  const b = JSON.parse(base);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  const k = (h: any) => `${h.session} ${h.file} ${h.round_index0} ${h.player} ${h.lock}`;
  // the first type's hits (the second type's are measured separately below)
  const cc = (x: any) => x.hits.filter((h: any) => h.variant === 'cutcopy');
  const un = (x: any, key = 'all') => total(Object.fromEntries(Object.entries(x.variants.uncut.hits_by_player)
    .map(([u, y]: any) => [u, y[key]])));

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

  // without the must-empty cells, or without the row above the T, the window is weaker and its hits are the
  // ablation's; the T's hand is still decided (no lock matches both)
  // without the must-empty cells the second type's window is symmetric about the T and a lock matches both hands,
  // which the matcher refuses (as ダブルダガー's does); the first type, measured on its own, still decides its hand
  expect(() => run({ noMustEmpty: true })).toThrow(/matches as drawn AND mirrored/);
  const firstOnly = classify(CUTCOPY, { ...TR, variants: [TR.variants[0]] }, digests(), { noMustEmpty: true });
  expect(firstOnly.hits.length).toBe(total(b.variants.cutcopy.controls.ablation.no_must_empty));
  a = mut({ noRoof: true });
  expect(sum(a, 'all')).toBe(total(b.variants.cutcopy.controls.ablation.no_roof));
  expect(sum(a, 'all')).toBe(PART_ONLY.below);
  // the second type's whole corpus absence is its row above the T: without it, its ablation's hits appear
  expect(un(a)).toBe(total(b.variants.uncut.controls.ablation.no_roof));
  expect(un(a)).toBeGreaterThan(0);

  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.cutcopy.controls.ablation.t_overlap));

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  // garbage read as EMPTY: exactly the hits with garbage in their window are lost
  a = mut({ garbageEmpty: true });
  expect(cc(a).map(k)).toEqual(cc(b).filter((h: any) => !h.garbage_in_window).map(k));

  // followupUnmirrored is EQUIVALENT on the corpus now (see EQUIVALENT): the one mirrored hit's slot is filled before
  // its next T in either hand. It is still killed on the page's own two-lock digest (below).
  expect(b.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBe(0);

  a = mut({ openerLt: true });
  expect(tsd(a, 'in_opener')).toBeLessThan(tsd(b, 'in_opener'));
  expect(tsd(a)).toBe(tsd(b));

  // no row map: the hit's own clear lies BETWEEN the slot's arms and its nub, so the slot is never joined and
  // no follow-up fires; the hits are the same
  a = mut({ followupNoRowmap: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBe(0);
  expect(fired(b)).toBeGreaterThan(0);

  // followupAnyT is EQUIVALENT on the corpus now (see EQUIVALENT); it is killed on the page's own digest (below)

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);

/** The page's own TSD → TSD, as a two-lock digest: the board `basic.spin` draws (its T the lock, every other
 *  drawn cell filled), the TSD's clear, then the T into the slot `second.spin` draws. */
function pageDigest(mirrored: boolean, secondSpin = 'full'): TechDigest {
  const node = (id: string) => TR.nodes.find((n: any) => n.id === id).rows as string[];
  const flip = (row: string) => mirrored ? [...row].reverse().join('') : row;
  const pad = (rows: string[]) => [...Array(H - rows.length).fill('.'.repeat(10)), ...rows.map(flip)];
  const read = (rows: string[]) => pad(rows.map(r => [...r].map(ch => ch === '-' || ch === 'T' ? '.' : 'S').join('')));
  const tCells = (rows: string[]): Cell[] => pad(rows).flatMap((r, row) => [...r].flatMap((ch, col) => ch === 'T' ? [{ row, col }] : []));
  const place = (board: string[], cells: Cell[]) => {
    const g = board.map(r => [...r]);
    for (const q of cells) { expect(g[q.row]![q.col]).toBe('.'); g[q.row]![q.col] = 'T'; }
    const full = g.flatMap((r, i) => r.every(x => x !== '.') ? [i] : []);
    const kept = g.filter((_, i) => !full.includes(i)).map(r => r.join(''));
    return { full, after: [...Array(full.length).fill('.'.repeat(10)), ...kept] };
  };
  const b0 = read(node('basic.spin')), t0 = tCells(node('basic.spin'));
  const s0 = place(b0, t0);
  // the board the TSD leaves is the derived after board, letter for letter in occupancy
  expect(s0.after).toEqual(read(node('basic.after')));
  const t1 = tCells(node('second.spin'));
  const s1 = place(s0.after, t1);
  expect([s0.full.length, s1.full.length]).toEqual([2, 2]);
  const lock = (cells: Cell[], spin: string, rows: number[]) =>
    ({ piece: 'T', spin, cleared: rows.length, cells, clearedRows: rows, garbage: 0, mapOk: true });
  return { session: 'page', file: 'cutcopy.php', round: 0, match: 1, user: 'page', v: 1,
           locks: [lock(t0, 'full', s0.full), lock(t1, secondSpin, s1.full)],
           tspins: [{ i: 0, board: b0 }, { i: 1, board: s0.after }] };
}

test('the follow-up search on the page\'s own TSD → TSD: fires as drawn and mirrored, and each follow-up mutant breaks it', () => {
  const fu = (mirrored: boolean, m: Mutants = {}, spin = 'full') => {
    const c = classify(CUTCOPY, TR, [pageDigest(mirrored, spin)], m);
    expect(c.hits.length).toBe(1);
    expect(c.hits[0]!.mirrored).toBe(mirrored);
    return c.hits[0]!.followup;
  };
  for (const m of [false, true]) {
    expect(fu(m)).toEqual({ lock: 1, fired: true, reason: null });
    // no row map: the TSD's two cleared rows split the slot, so it is never joined
    expect(fu(m, { followupNoRowmap: true }).fired).toBe(false);
    // a T in the slot that is not a full TSD: refused, and fired by a follow-up that accepts any T
    expect(fu(m, {}, 'mini')).toEqual({ lock: 1, fired: false, reason: 't_in_slot_not_tsd' });
    expect(fu(m, { followupAnyT: true }, 'mini').fired).toBe(true);
  }
  // the slot carried in the drawn columns on a mirrored hit: the mirrored second TSD lands elsewhere
  expect(fu(false, { followupUnmirrored: true }).fired).toBe(true);
  expect(fu(true, { followupUnmirrored: true })).toEqual({ lock: 1, fired: false, reason: 'next_t_elsewhere' });
});

/** harddrop's second type, as a two-lock digest on its own drawing (the external node `uncut.spin`, its T the lock,
 *  every other drawn cell filled), the TSD's clear, then the T into the second slot `uncut.after` leaves open. */
function uncutDigest(mirrored: boolean, secondSpin = 'full'): TechDigest {
  const node = (id: string) => TR.nodes.find((n: any) => n.id === id).rows as string[];
  const u = TR.variants[1];
  const flip = (row: string) => mirrored ? [...row].reverse().join('') : row;
  const pad = (rows: string[]) => [...Array(H - rows.length).fill('.'.repeat(10)), ...rows.map(flip)];
  const read = (rows: string[]) => pad(rows.map(r => [...r].map(ch => ch === '-' || ch === 'T' ? '.' : 'S').join('')));
  const tCells = (rows: string[]): Cell[] => pad(rows).flatMap((r, row) => [...r].flatMap((ch, col) => ch === 'T' ? [{ row, col }] : []));
  const after = node(u.followup.board);
  const slotRows = after.map((r, i) => [...r].map((_, c) =>
    u.followup.t_cells_after.some(([rr, cc]: number[]) => rr === i && cc === c) ? 'T' : '-').join(''));
  const place = (board: string[], cells: Cell[]) => {
    const g = board.map(r => [...r]);
    for (const q of cells) { expect(g[q.row]![q.col]).toBe('.'); g[q.row]![q.col] = 'T'; }
    const full = g.flatMap((r, i) => r.every(x => x !== '.') ? [i] : []);
    const kept = g.filter((_, i) => !full.includes(i)).map(r => r.join(''));
    return { full, after: [...Array(full.length).fill('.'.repeat(10)), ...kept] };
  };
  const b0 = read(node(u.board)), t0 = tCells(node(u.board));
  const s0 = place(b0, t0);
  // the board the TSD leaves is the drawn after board, in occupancy
  expect(s0.after).toEqual(read(after));
  const t1 = tCells(slotRows);
  const s1 = place(s0.after, t1);
  expect([s0.full.length, s1.full.length]).toEqual([2, 2]);
  const lock = (cells: Cell[], spin: string, rows: number[]) =>
    ({ piece: 'T', spin, cleared: rows.length, cells, clearedRows: rows, garbage: 0, mapOk: true });
  return { session: 'harddrop', file: 'Cut_copy', round: 0, match: 1, user: 'page', v: 1,
           locks: [lock(t0, 'full', s0.full), lock(t1, secondSpin, s1.full)],
           tspins: [{ i: 0, board: b0 }, { i: 1, board: s0.after }] };
}

test('the second type\'s follow-up search on harddrop\'s own drawing: fires as drawn and mirrored, and its mutants', () => {
  const fu = (mirrored: boolean, m: Mutants = {}, spin = 'full') => {
    const c = classify(CUTCOPY, TR, [uncutDigest(mirrored, spin)], m);
    expect(c.hits.map(h => [h.variant, h.lock, h.mirrored])).toEqual([['uncut', 0, mirrored]]);
    return c.hits[0]!.followup;
  };
  for (const m of [false, true]) {
    expect(fu(m)).toEqual({ lock: 1, fired: true, reason: null });
    // the second slot lies under both cleared rows, so the row map moves none of its cells: the mutant that drops
    // it is EQUIVALENT on this variant (measured), unlike the first type's split slot
    expect(fu(m, { followupNoRowmap: true })).toEqual({ lock: 1, fired: true, reason: null });
    expect(fu(m, {}, 'mini')).toEqual({ lock: 1, fired: false, reason: 't_in_slot_not_tsd' });
    expect(fu(m, { followupAnyT: true }, 'mini').fired).toBe(true);
  }
  expect(fu(false, { followupUnmirrored: true }).fired).toBe(true);
  expect(fu(true, { followupUnmirrored: true })).toEqual({ lock: 1, fired: false, reason: 'next_t_elsewhere' });
});
