/**
 * The BT砲 (途中BT) technique artefact (`analysis/btcannon-facts.json`, from `pipeline/sim/emit-technique-facts.ts
 * --technique btcannon`; the rules are the shared `technique-facts.ts`, the profile `technique-profile-btcannon.ts`,
 * the shape the gated `pipeline/openers/btcannon-technique.json`).
 *
 * THE CORPUS HOLDS NO HIT, and that is the measurement this file pins: not one scored full TSD in the seventeen
 * sessions stood in the page's window. A zero is only worth publishing if the predicate could have fired, so the
 * file proves that it does, on drawings it did not choose:
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for
 *      every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on each of harddrop's BT_Cannon drawings the gate
 *      records — once, at its drawn T, in its recorded hand, and at no other T placement — on each of its no-T
 *      boards at some placement, on each of this page's own drawings of the shape as drawn, and on no routes board
 *      (the gate's `cross_source.fires` is empty, with its reason).
 *   4. WHAT DISCRIMINATES, measured per window part with the T anchored: the rows above the T alone admit no full
 *      TSD of the corpus, the cleared rows (entailed by the clear) almost all, the row under them some.
 *   5. STMB CAVE AND ダブルダガー ARE NOT THIS: all three lay the T flat, nub down; anchored on the same T this
 *      window clashes with each of theirs on a cell in every pairing of hands (re-derived from the transcriptions).
 *   6. NAMED lists, all empty but window_off_board (pinned per player, every entry checked); pinned denominators
 *      and controls; mutants, the ones that cannot move a byte here named EQUIVALENT with their reason and asserted
 *      to stay byte-identical.
 *   7. THE FOLLOW-UP, which no corpus hit exercises: run on the page's own TSD → TST as a two-lock digest, as
 *      drawn and mirrored, it fires, and each follow-up mutant (equivalent on the corpus) breaks it there.
 *
 * window_off_board is not listed entry by entry: it is every flat, nub-down T at a TSD whose window leaves the
 * board before the matcher found a mismatch (the window reaches four rows above the T and one under its nub),
 * pinned per player as a count with a property check (STMB Cave's treatment, for the same reason).
 *
 * Run: bun test pipeline/openers/btcannon.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, classify, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { BTCANNON } from '../sim/technique-profile-btcannon.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { DOUBLEDAGGER } from '../sim/technique-profile-doubledagger.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12']);
const ART_PATH = `${import.meta.dir}/../../analysis/btcannon-facts.json`;
const TR = JSON.parse(readFileSync(BTCANNON.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: none. Each list is still checked as a named list, so the first hit is a red build. */
const BTCANNON_HITS: string[] = [];
const FOLLOWUP_NOT_FIRED: string[] = [];
const GARBAGE_IN_WINDOW: string[] = [];
const BTCANNON_IN_OPENER: string[] = [];
const RECON_DROPPED_TSD: string[] = [];
/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 667, yachi: 501 };

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5307, in_opener: 1043, mid_game: 4264 },
                    yachi: { all: 4751, in_opener: 1242, mid_game: 3509 } };
const HITS = { pinglamb: { all: 0, in_opener: 0, mid_game: 0, mirrored: 0, garbage_in_window: 0 },
               yachi: { all: 0, in_opener: 0, mid_game: 0, mirrored: 0, garbage_in_window: 0 } };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 0, yachi: 0 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 0, yachi: 0 }, no_roof: { pinglamb: 492, yachi: 393 },
              t_overlap: { pinglamb: 0, yachi: 18 } },
  orientation_baseline: { pinglamb: 43, yachi: 61 },
};
/** What discriminates, measured: full TSDs whose anchored T meets ONE part of the window. `above` is rows 0-3
 *  (the TST's overhang, the cell over the slot, the TST slot beside the cell over the T's middle, the roof), of
 *  which `overhang` is rows 0-1 and `tst_side` rows 2-3; `cleared` the two rows the TSD clears; `below` the TST
 *  slot's bottom cell and its two walls. No full TSD of the corpus has the rows above the T as the page draws
 *  them, and that alone is the headline's zero: the `no_roof` ablation (the window less those rows) is `below`. */
const PART_ONLY = { above: 0, overhang: 64, tst_side: 0, cleared: 9954, below: 885 };

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  followupUnmirrored: 'there is no hit, so no follow-up to carry (killed on the page\'s own TSD → TST, below)',
  followupNoRowmap: 'there is no hit, so no follow-up to carry (killed on the page\'s own TSD → TST, below)',
  followupAnyT: 'there is no hit, so no follow-up to carry (killed on the page\'s own TSD → TST, below)',
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  noMustEmpty: 'the window\'s filled cells alone already match no full TSD (the no_must_empty ablation is 0 / M), '
    + 'and the matcher meets a filled-cell mismatch before it could leave the board on every flat T it reads',
  garbageEmpty: 'garbage read as empty turns no window cell from a mismatch into a match or the other way on this '
    + 'corpus: no hit, and the same off-board entries',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(BTCANNON, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;

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

/** A drawing (rows top first; `U` the drawn T, read as the lock) in the matcher's frame. */
function asBoard(rows: string[], filled: (ch: string) => boolean) {
  return rows.map(r => [...r].map(ch => filled(ch) ? 'X' : '.').join(''));
}
const lockOf = (rows: string[]): Cell[] =>
  rows.flatMap((r, i) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));
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
  expect(n).toBe(14176);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the drawings: windowMatch fires on every drawing the gate records, and on no routes board', () => {
  const hd = TR.cross_source.harddrop;
  // harddrop's drawings with a drawn T: once, at the drawn T, in the recorded hand; at no other placement
  expect(hd.drawings.length).toBe(15);
  expect(hd.drawings.filter((d: any) => d.section === 'Mid-game BT Cannon').length).toBe(7);
  for (const d of hd.drawings) {
    const board = asBoard(d.rows, ch => ch !== '-' && ch !== 'U');
    const lock = lockOf(d.rows);
    expect(fires(board, lock), `table ${d.table} board ${d.board}`).toEqual([d.mirrored]);
    const others = tPlacements(board).filter(cs => cs.some(q => !lock.some(x => x.row === q.row && x.col === q.col)));
    for (const cs of others) expect(fires(board, cs), `table ${d.table} board ${d.board}`).toEqual([]);
  }
  // its boards with no T drawn: the window fires at some placement
  expect(hd.fires_without_slot.length).toBe(7);
  for (const d of hd.fires_without_slot) {
    const board = asBoard(d.rows, ch => ch !== '-');
    expect(tPlacements(board).some(cs => fires(board, cs).length), `table ${d.table} board ${d.board}`).toBe(true);
  }
  // this page's own drawings of the shape, each at its agreement slot, as drawn
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  const v = TR.variants[0];
  expect(v.agreement.map((a: any) => a.board).sort()).toEqual([...v.fires_on].sort());
  for (const a of v.agreement) {
    const board = asBoard(byId.get(a.board).rows, ch => ch !== '-');
    expect(fires(board, a.t_cells.map(([row, col]: number[]) => ({ row, col }))), a.board).toEqual([false]);
  }
  // and on no routes board (the gate records none, with its reason)
  const got: string[] = [];
  const dir = `${import.meta.dir}`;
  for (const f of readdirSync(dir).filter(x => x.endsWith('-routes.json')).sort()) {
    for (const n of JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const cells = lockOf(n.rows);
      if (cells.length !== 4) continue;
      if (fires(asBoard(n.rows, ch => ch !== '-' && ch !== 'U'), cells).length) got.push(`${f} ${n.id}`);
    }
  }
  expect(got).toEqual([]);
  expect(TR.cross_source.fires).toEqual([]);
  expect(TR.cross_source.also).toEqual([]);
  expect(TR.cross_source.routes_fire_none.length).toBeGreaterThan(0);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [0, 6], cols: [0, 3] });
  expect(v.t_cells).toEqual([[4, 1], [4, 2], [4, 3], [5, 2]]);
  expect(v.followup).toMatchObject({ spin: 'TST', lines: 3, t_cells_pre_clear: [[2, 1], [3, 1], [3, 2], [6, 1]] });
  expect(TR.empty_letters).toBe('');
  // the follow-up is a TST, so the matcher's follow-up kind is a full three-line spin
  expect(prepare(TR, v).map(P => P.followupKind)).toEqual(['full:3', 'full:3']);
});

test('named lists: no hit, no follow-up miss, no opener hit, no garbage, no dropped TSD', () => {
  const L = art().lists;
  checkNamedList('btcannon_hits', L.btcannon_hits, BTCANNON_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('btcannon_in_opener', L.btcannon_in_opener, BTCANNON_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  expect(art().hits).toEqual([]);
});

test('window_off_board: pinned per player, every entry a flat nub-down T whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  for (const u of ['pinglamb', 'yachi'] as const)
    expect(L.filter(x => x.split(' ')[2] === u).length, u).toBe(WINDOW_OFF_BOARD[u]);
  const v = TR.variants[0];
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  const [nr, nc] = v.t_cells.reduce((a: number[], b: number[]) => (b[0]! > a[0]! ? b : a));
  const want = new Set<string>();
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
    const n = nubOf(s.lk.cells);
    if (!n) continue;
    const rowsOff = n.row + (r0 - nr) < 0 || n.row + (r1 - nr) >= H;
    const drawnOff = rowsOff || n.col + (c0 - nc) < 0 || n.col + (c1 - nc) > 9;
    const mirrOff = rowsOff || n.col - (c1 - nc) < 0 || n.col - (c0 - nc) > 9;
    if (drawnOff || mirrOff) want.add(nameOf(d, s.i));
  }
  for (const x of L) expect(want.has(x), x).toBe(true);
  expect(new Set(L).size).toBe(L.length);
}, 600_000);

test('pinned: denominators, hits, follow-ups, controls', () => {
  const a = art(), v = a.variants.btcannon;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TSD, u).toEqual(TSD_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u], u).toEqual({ fired: 0, not_fired: {} });
  }
  expect(v.controls).toEqual(CONTROLS);
});

test('what discriminates: each part of the window alone, with the T anchored', () => {
  const v = TR.variants[0];
  const [top] = v.t_cells[0]!;          // the T's row; the nub row is under it
  const parts: Record<keyof typeof PART_ONLY, (r: number) => boolean> = {
    above: r => r < top, overhang: r => r <= top - 3, tst_side: r => r === top - 2 || r === top - 1,
    cleared: r => r === top || r === top + 1, below: r => r > top + 1,
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
  expect(got).toEqual(PART_ONLY);
  // the no_roof ablation (the window less the rows above the T) is exactly the `below` part
  expect(total(art().variants.btcannon.controls.ablation.no_roof)).toBe(PART_ONLY.below);
}, 600_000);

test('STMB Cave and Double Dagger are not this: anchored on the same flat T, the windows clash in every pairing', () => {
  const norm = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  for (const other of [STMBCAVE, DOUBLEDAGGER]) {
    const tr = JSON.parse(readFileSync(other.transcriptionPath, 'utf8'));
    for (const a of prepare(TR, TR.variants[0]).map(norm)) for (const b of prepare(tr, tr.variants[0]).map(norm)) {
      expect(a.T, other.key).toBe(b.T);
      const clash = [...a.cells].filter(([k, v]) => b.cells.has(k) && b.cells.get(k) !== v && v !== 'T');
      expect(clash.length, other.key).toBeGreaterThan(0);
    }
  }
});

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(30);
  expect(c.rowmap_steps).toBe(245899);
});

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.btcannon.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const tsd = (a: any, k = 'all') => a.denominators.pinglamb.TSD[k] + a.denominators.yachi.TSD[k];
  const tss = (a: any) => a.denominators.pinglamb.TSS.all + a.denominators.yachi.TSS.all;
  const b = JSON.parse(base);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };

  // as drawn only: the mirrored windows that leave the board are no longer read, so the off-board list shrinks
  let a = mut({ noMirror: true });
  expect(sum(a, 'all')).toBe(0);
  expect(a.lists.window_off_board.length).toBeLessThan(b.lists.window_off_board.length);

  a = mut({ pastPrefix: true });
  expect(a.denominators.pinglamb.unscored_past_prefix + a.denominators.yachi.unscored_past_prefix).toBe(0);
  expect(tsd(a)).toBeGreaterThan(tsd(b));
  const replayTotal = SESSIONS.reduce((s, x) => s + JSON.parse(readFileSync(`${ROOT}/${x}/sim/opener-facts.json`, 'utf8'))
    .donation.counter_anchor.tspin_clears_replay, 0);
  expect(a.check.tspin_clears_scored).toBe(replayTotal);

  a = mut({ includeMini: true });
  expect(tss(a)).toBe(tss(b) + b.denominators.pinglamb.mini_TSS.all + b.denominators.yachi.mini_TSS.all);

  // without the rows above the T, the window is the `below` part: the no_roof ablation becomes the headline
  a = mut({ noRoof: true });
  expect(sum(a, 'all')).toBe(total(b.variants.btcannon.controls.ablation.no_roof));
  expect(sum(a, 'all')).toBeGreaterThan(0);

  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.btcannon.controls.ablation.t_overlap));
  expect(sum(a, 'all')).toBeGreaterThan(0);

  // the anchor one row off: the window never matches the T it is anchored on, so nothing reaches the board's edge
  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);
  expect(a.lists.window_off_board).toEqual([]);

  a = mut({ openerLt: true });
  expect(tsd(a, 'in_opener')).toBeLessThan(tsd(b, 'in_opener'));
  expect(tsd(a)).toBe(tsd(b));

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);

/** The page's own TSD → TST, as a two-lock digest: the board `basic.spin` draws (its U the T, every drawn cell
 *  filled), the TSD's clear, then the T into the slot `tst.spin` draws. The corpus holds no hit, so the
 *  follow-up search (the row map joining the TST slot the TSD's clear splits, and the `full:3` kind) runs
 *  nowhere on it; this runs it, as drawn and mirrored, on a board where it can succeed and fail. */
function pageDigest(mirrored: boolean, tstSpin = 'full'): TechDigest {
  const node = (id: string) => TR.nodes.find((n: any) => n.id === id).rows as string[];
  const flip = (row: string) => mirrored ? [...row].reverse().join('') : row;
  const pad = (rows: string[]) => [...Array(H - rows.length).fill('.'.repeat(10)), ...rows.map(flip)];
  const read = (rows: string[]) => pad(rows.map(r => [...r].map(ch => ch === '-' || ch === 'U' ? '.' : 'S').join('')));
  const uCells = (rows: string[]): Cell[] => pad(rows).flatMap((r, row) => [...r].flatMap((ch, col) => ch === 'U' ? [{ row, col }] : []));
  const place = (board: string[], cells: Cell[]) => {
    const g = board.map(r => [...r]);
    for (const q of cells) { expect(g[q.row]![q.col]).toBe('.'); g[q.row]![q.col] = 'T'; }
    const full = g.flatMap((r, i) => r.every(x => x !== '.') ? [i] : []);
    const kept = g.filter((_, i) => !full.includes(i)).map(r => r.join(''));
    return { full, after: [...Array(full.length).fill('.'.repeat(10)), ...kept] };
  };
  const b0 = read(node('basic.spin')), t0 = uCells(node('basic.spin'));
  const s0 = place(b0, t0);
  // the board the TSD leaves is the derived after board, letter for letter in occupancy
  expect(s0.after).toEqual(read(node('basic.after')));
  const t1 = uCells(node('tst.spin'));
  const s1 = place(s0.after, t1);
  expect([s0.full.length, s1.full.length]).toEqual([2, 3]);
  const lock = (cells: Cell[], spin: string, rows: number[]) =>
    ({ piece: 'T', spin, cleared: rows.length, cells, clearedRows: rows, garbage: 0, mapOk: true });
  return { session: 'page', file: 'btcannon.php', round: 0, match: 1, user: 'page', v: 1,
           locks: [lock(t0, 'full', s0.full), lock(t1, tstSpin, s1.full)],
           tspins: [{ i: 0, board: b0 }, { i: 1, board: s0.after }] };
}

test('the follow-up search on the page\'s own TSD → TST: fires as drawn and mirrored, and each follow-up mutant breaks it', () => {
  const fu = (mirrored: boolean, m: Mutants = {}, tstSpin = 'full') => {
    const c = classify(BTCANNON, TR, [pageDigest(mirrored, tstSpin)], m);
    expect(c.hits.length).toBe(1);
    expect(c.hits[0]!.mirrored).toBe(mirrored);
    return c.hits[0]!.followup;
  };
  for (const m of [false, true]) {
    expect(fu(m)).toEqual({ lock: 1, fired: true, reason: null });
    // no row map: the TSD's two cleared rows split the TST slot, so the slot is never joined
    expect(fu(m, { followupNoRowmap: true }).fired).toBe(false);
    // a T in the slot that is not a full TST: refused, and fired by a follow-up that accepts any T
    expect(fu(m, {}, 'mini')).toEqual({ lock: 1, fired: false, reason: 't_in_slot_not_tsd' });
    expect(fu(m, { followupAnyT: true }, 'mini').fired).toBe(true);
  }
  // the slot carried in the drawn columns on a mirrored hit: the mirrored TST lands elsewhere
  expect(fu(false, { followupUnmirrored: true }).fired).toBe(true);
  expect(fu(true, { followupUnmirrored: true })).toEqual({ lock: 1, fired: false, reason: 'next_t_elsewhere' });
});
