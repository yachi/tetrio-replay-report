/**
 * The 意外 T-spin (accidental TST) technique artefact (`analysis/accidental-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique accidental`; the rules are the shared `technique-facts.ts`, the
 * detector `technique-profile-accidental.ts`, the exclusions `accidental-qualify.ts`, the drawings the gated
 * `pipeline/openers/accidental-technique.json`).
 *
 * yachi's rule (2026-11-20): 「打完一個T-spin,佢清行之前 TST 嗰四格係被蓋住嘅。清完之後,嗰四格啱啱變成一個露天嘅TST位。
 * 再加多一粒就即食tst」. One variant, `tst`, `window_basis: spin_rule`: a full TST at lock j; the previous T-spin i of
 * the round cleared lines; no T locks between them; j's four T cells were covered before i's clear and empty right
 * after it, on rows that stood then. Relaxed 2026-11-21 (yachi's video failed the earlier overhang reading): at least
 * one T column's top cell is open to the sky right after i's clear (ACCESS), and over every such column the lowest
 * filled cell above the T before j belongs to a piece placed after i (ROOF; any number of roof pieces).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count.
 *   3. THE DETECTOR, re-derived by a second implementation: the profile maps j's cells BACK through each lock's row
 *      map; this file plays the board FORWARD from i, tagging every cell with where it came from, checks the played
 *      board equals the digest's board before j, and reads the clauses off the tags. Every hit and every ablation
 *      count, and each hit's prev_spin_lock and roof_locks, must agree.
 *   4. THE QUALIFY VERDICTS, re-derived from the digests.
 *   5. `other_page` against the other technique artefacts' own hits, keyed by round.
 *   6. pinned figures and named lists; the hits by name.
 *
 * The two implementations disagreed once while this file was written (2026-11-21): under `no_next_t` the profile let a
 * T cell land on a row i's own clear brought in empty and called it covered. The profile was fixed; the rule ("none
 * is a new row") was always the forward one's.
 */import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, digestCorpus, type Mutants, type TechDigest } from '../sim/technique-facts.ts';
import { ACCIDENTAL } from '../sim/technique-profile-accidental.ts';
import { accidentalQualifier, OTHER_PAGES, type AccidentalQualifyMutants } from '../sim/accidental-qualify.ts';
import { TECHNIQUES } from '../sim/techniques.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29', '2026-11-01', '2026-11-05', '2026-11-17', '2026-11-19']);
const ART_PATH = `${import.meta.dir}/../../analysis/accidental-facts.json`;
const OPENERS = import.meta.dir;
const ANALYSIS = `${import.meta.dir}/../../analysis`;
const TR = JSON.parse(readFileSync(ACCIDENTAL.transcriptionPath, 'utf8'));
const H = 40;
const USERS = ['pinglamb', 'yachi'] as const;

/** Every hit, by name, in artefact order. */
const HIT_NAMES: string[] = [
  '2026-07-22 m7r8 yachi lock 65 tst',
  '2026-09-17 m5r6 yachi lock 160 tst',
  '2026-09-19 m8r5 yachi lock 78 tst',
  '2026-10-03 m1r1 yachi lock 32 tst',
  '2026-10-03 m9r1 yachi lock 102 tst',
  '2026-10-09 m4r4 pinglamb lock 24 tst',
  '2026-10-09 m8r2 yachi lock 37 tst',
  '2026-10-12 m1r2 pinglamb lock 24 tst',
  '2026-10-22 m6r7 pinglamb lock 32 tst',
  '2026-10-22 m8r5 yachi lock 39 tst',
  '2026-11-17 m2r6 pinglamb lock 29 tst',
  '2026-11-17 m3r2 pinglamb lock 308 tst',
];
/** The hits that are not some opener route's own continuation (the other two are, `opener_route`). */
const NOT_QUALIFIED = ['2026-10-09 m4r4 pinglamb lock 24 tst', '2026-10-12 m1r2 pinglamb lock 24 tst'];
const QUALIFIED = HIT_NAMES.filter(n => !NOT_QUALIFIED.includes(n));
/** each hit's previous T-spin and roof pieces, by lock */
const RULE: Record<string, [number, number[]]> = {
  '2026-07-22 m7r8 yachi lock 65 tst': [50, [56, 60]],
  '2026-09-17 m5r6 yachi lock 160 tst': [147, [150, 159]],
  '2026-09-19 m8r5 yachi lock 78 tst': [73, [74, 77]],
  '2026-10-03 m1r1 yachi lock 32 tst': [26, [28, 31]],
  '2026-10-03 m9r1 yachi lock 102 tst': [94, [96, 101]],
  '2026-10-09 m4r4 pinglamb lock 24 tst': [17, [19]],
  '2026-10-09 m8r2 yachi lock 37 tst': [30, [32, 35]],
  '2026-10-12 m1r2 pinglamb lock 24 tst': [17, [18]],
  '2026-10-22 m6r7 pinglamb lock 32 tst': [27, [29, 31]],
  '2026-10-22 m8r5 yachi lock 39 tst': [33, [34, 35]],
  '2026-11-17 m2r6 pinglamb lock 29 tst': [15, [18]],
  '2026-11-17 m3r2 pinglamb lock 308 tst': [303, [304, 307]],
};

const DENOM = {
  pinglamb: { TST: { all: 1773, in_opener: 1730, mid_game: 43 } },
  yachi: { TST: { all: 1083, in_opener: 1022, mid_game: 61 } },
};
const HITS = { pinglamb: { all: 5, in_opener: 0, mid_game: 5, garbage_in_window: 4 },
               yachi: { all: 7, in_opener: 0, mid_game: 7, garbage_in_window: 7 } };
const QUALIFY = { pinglamb: { qualified: 3, not_qualified: { opener_route: 2 } }, yachi: { qualified: 7, not_qualified: {} } };
/** each clause dropped, at the opportunity; no_access and no_new_roof both equal the headline on this corpus
 *  (measured equivalents: every candidate passing the other clauses already has an open T column with a new roof) */
const ABLATION = { no_next_t: { pinglamb: 7, yachi: 8 }, no_exposed: { pinglamb: 235, yachi: 94 },
                   no_access: { pinglamb: 5, yachi: 7 }, no_new_roof: { pinglamb: 5, yachi: 7 } };
type Abl = '' | keyof typeof ABLATION;

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const run = (m: Mutants) => build(ACCIDENTAL, m, digests());
const hk = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
const keyOf = (d: TechDigest, lock: number) => `${d.session}|${d.file}|${d.round}|${d.user}|${lock}`;
const qName = (h: any) => `${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock} ${h.variant}`;
const qualified = () => art().hits.filter((h: any) => h.qualifies);

function scored(d: TechDigest) {
  const out: { i: number; lk: TechDigest['locks'][number] }[] = [];
  for (const t of d.tspins) {
    if (t.i > d.v) continue;
    const lk = d.locks[t.i]!;
    const withT = t.board.map(s => [...s].map(x => x !== '.'));
    for (const q of lk.cells) withT[q.row]![q.col] = true;
    const rows: number[] = [];
    for (let r = 0; r < H; r++) if (withT[r]!.every(Boolean)) rows.push(r);
    const theirs = [...lk.clearedRows].sort((a, b) => a - b);
    if (rows.length !== theirs.length || !rows.every((x, k) => x === theirs[k]) || !rows.length) continue;
    out.push({ i: t.i, lk });
  }
  return out;
}
const W = 10;
/** The rule, played FORWARD (independent of the profile's backward row map). From the board before i with i's T,
 *  every cell tagged `o:<row>`; i's clear (new rows `n`), then i's garbage (`g`), then each lock k to j-1 placing
 *  cells tagged `k:<k>`. The played board must equal the digest's board before j (garbage rows aside). */
function forward(d: TechDigest, j: number, abl: Abl): { i: number; roofs: number[] } | null {
  const lj = d.locks[j]!;
  if (lj.spin !== 'full' || lj.cleared !== 3) return null;
  const q = d.tspins.findIndex(t => t.i === j);
  if (q < 1) return null;
  const ti = d.tspins[q - 1]!, i = ti.i, li = d.locks[i]!;
  if (li.cleared < 1) return null;
  if (d.locks.slice(i, j).some(l => !l.mapOk)) return null;
  if (abl !== 'no_next_t' && d.locks.slice(i + 1, j).some(l => l.piece === 'T')) return null;
  const before = ti.board.map(r => [...r]);
  for (const c of li.cells) before[c.row]![c.col] = 'T';
  type Cell = { occ: boolean; tag: string };
  let grid: Cell[][] = before.map((r, row) => r.map(x => ({ occ: x !== '.', tag: `o:${row}` })));
  const step = (cells: { row: number; col: number }[], cleared: number[], garbage: number, owner: string | null) => {
    if (owner) for (const c of cells) grid[c.row]![c.col] = { occ: true, tag: owner };
    const cl = new Set(cleared);
    let g = grid.filter((_, r) => !cl.has(r));
    while (g.length < H) g.unshift(Array.from({ length: W }, () => ({ occ: false, tag: 'n' })));
    g = g.slice(garbage);
    while (g.length < H) g.push(Array.from({ length: W }, () => ({ occ: true, tag: 'g' })));
    grid = g;
  };
  step([], li.clearedRows, 0, null);
  const afterI = grid.map(r => r.map(c => ({ ...c })));
  step([], [], li.garbage, null);
  for (let k = i + 1; k < j; k++) { const l = d.locks[k]!; step(l.cells, l.clearedRows, l.garbage, `k:${k}`); }
  const tj = d.tspins[q]!.board;
  for (let r = 0; r < H; r++) for (let c = 0; c < W; c++) {
    if (grid[r]![c]!.tag === 'g') continue;
    if (grid[r]![c]!.occ !== (tj[r]![c] !== '.')) throw new Error(`desync ${d.session} ${d.file} ${d.round} ${d.user} j${j}`);
  }
  const src = lj.cells.map(c => grid[c.row]![c.col]!.tag);
  if (!src.every(t => t.startsWith('o:'))) return null;
  const orig = lj.cells.map((c, x) => ({ row: +src[x]!.slice(2), col: c.col }));
  const isT = (r: number, c: number) => orig.some(o => o.row === r && o.col === c);
  const pos = orig.map(o => {
    for (let r = 0; r < H; r++) if (afterI[r]![o.col]!.tag === `o:${o.row}`) return { row: r, col: o.col };
    return null;
  });
  if (pos.some(p => !p)) return null;
  if (pos.some(p => afterI[p!.row]![p!.col]!.occ)) return null;
  const covered = orig.some(o => { for (let r = 0; r <= o.row; r++) if (before[r]![o.col] !== '.' && !isT(r, o.col)) return true; return false; });
  if (abl !== 'no_exposed' && !covered) return null;
  const cols = [...new Set(lj.cells.map(c => c.col))];
  const tops = cols.map(col => pos.filter(p => p!.col === col).reduce((m, p) => (p!.row < m.row ? p! : m)));
  const opened = tops.filter(t => {
    for (let r = 0; r < t.row; r++) if (afterI[r]![t.col]!.occ) return false;
    return true;
  });
  const access = abl === 'no_access' ? tops : opened;
  if (!access.length) return null;
  const roofs = new Set<number>();
  for (const t of access) {
    const top = Math.min(...lj.cells.filter(c => c.col === t.col).map(c => c.row));
    for (let r = top - 1; r >= 0; r--) {
      const x = grid[r]![t.col]!;
      if (!x.occ) continue;
      if (x.tag.startsWith('k:')) roofs.add(+x.tag.slice(2));
      break;
    }
  }
  if (abl !== 'no_new_roof' && roofs.size === 0) return null;
  return { i, roofs: [...roofs].sort((x, y) => x - y) };
}

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 600_000);

test('quarantined: report_eligible false, no claim ids, one spin_rule variant with no follow-up and no payoff', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
  expect(TR.variants.map((v: any) => [v.id, v.spin, v.lines, v.window_basis])).toEqual([['tst', 'TST', 3, 'spin_rule']]);
  for (const v of TR.variants) { expect(v.followup).toBeUndefined(); expect(v.payoff).toBeUndefined(); }
  expect(Object.keys(a.variants)).toEqual(['tst']);
  expect(ACCIDENTAL.opportunity).toEqual({ spin: 'full', lines: 3 });
  for (const h of a.hits) expect(h.followup, qName(h)).toEqual({ lock: null, fired: false, reason: 'no_followup' });
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  expect(checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT)).toBe(18623);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the detector, re-derived forward: the hits, their previous spin and roof, and every ablation count', () => {
  const a = art();
  for (const abl of ['', ...Object.keys(ABLATION)] as Abl[]) {
    const by: Record<string, number> = { pinglamb: 0, yachi: 0 };
    const want = new Map<string, [number, number[]]>();
    for (const d of digests()) for (const s of scored(d)) {
      const m = forward(d, s.i, abl);
      if (!m) continue;
      by[d.user]!++;
      if (!abl) want.set(keyOf(d, s.i), [m.i, m.roofs]);
    }
    if (abl) {
      expect(by, abl).toEqual(ABLATION[abl]);
      expect(a.variants.tst.controls.ablation[abl], abl).toEqual(ABLATION[abl]);
      continue;
    }
    const got = new Map<string, [number, number[]]>(a.hits.map((h: any) =>
      [hk(h), [h.rule.prev_spin_lock, h.rule.roof_locks]]));
    expect(got.size).toBe(a.hits.length);
    expect([...got.entries()].sort()).toEqual([...want.entries()].sort());
  }
}, 1_200_000);

test('each hit: its previous T-spin cleared lines, no T between, roof pieces placed after it, a box over the T', () => {
  const byKey = new Map(digests().map(d => [`${d.file}|${d.round}|${d.user}`, d]));
  for (const h of art().hits) {
    const d = byKey.get(`${h.file}|${h.round_index0}|${h.player}`)!;
    const [i, roofs] = RULE[qName(h)]!;
    expect([h.rule.prev_spin_lock, h.rule.roof_locks], qName(h)).toEqual([i, roofs]);
    expect(d.locks[i]!.cleared, qName(h)).toBeGreaterThan(0);
    expect(d.tspins.some(t => t.i === i), qName(h)).toBe(true);
    expect(d.locks.slice(i + 1, h.lock).some(l => l.piece === 'T'), qName(h)).toBe(false);
    expect(roofs.length, qName(h)).toBeGreaterThan(0);
    expect([...roofs].sort((x, y) => x - y), qName(h)).toEqual(roofs);
    for (const k of roofs) expect(k > i && k < h.lock, qName(h)).toBe(true);
    expect(h.rule.t_cells.length, qName(h)).toBe(4);
    expect(h.rule.box.cols, qName(h)).toEqual([0, 9]);
  }
}, 600_000);

test('the qualify verdicts, re-derived; two hits are an opener route\'s own, and only that rule turned off adds them', () => {
  const byKey = new Map(digests().map(d => [`${d.file}|${d.round}|${d.user}`, d]));
  const verdicts = (m: AccidentalQualifyMutants) => {
    const q = accidentalQualifier(OPENERS, ANALYSIS, m);
    return art().hits.map((h: any) => q(h, byKey.get(`${h.file}|${h.round_index0}|${h.player}`)!));
  };
  const base = verdicts({});
  art().hits.forEach((h: any, k: number) => {
    expect(base[k].qualifies, qName(h)).toBe(h.qualifies);
    expect(base[k].not_qualified, qName(h)).toEqual(h.not_qualified);
  });
  const nq = art().hits.filter((h: any) => !h.qualifies);
  expect(nq.map(qName)).toEqual(NOT_QUALIFIED);
  for (const h of nq) expect(h.not_qualified, qName(h)).toEqual(['opener_route']);
  for (const m of ['noOpener', 'noOtherPage', 'noOpenerRoute', 'noOpenerSpin'] as (keyof AccidentalQualifyMutants)[])
    expect(verdicts({ [m]: true }).filter(x => x.qualifies).length, m)
      .toBe(m === 'noOpenerRoute' ? art().hits.length : QUALIFIED.length);
}, 600_000);

test('mid-game only: in_opener is exactly the opener window', () => {
  for (const h of art().hits) expect(h.not_qualified.includes('in_opener'), qName(h)).toBe(h.in_opener);
  expect(qualified().every((h: any) => !h.in_opener)).toBe(true);
});

test('other_page against the other artefacts: no hit is another page\'s, keyed by round', () => {
  const mine = new Map<string, any>(art().hits.map((h: any) => [hk(h), h]));
  for (const k of OTHER_PAGES) {
    const P = (TECHNIQUES as any)[k];
    for (const x of JSON.parse(readFileSync(P.artefactPath, 'utf8')).hits)
      if (mine.has(hk(x))) expect(mine.get(hk(x)).not_qualified, `${k} ${hk(x)}`).toContain('other_page');
  }
});

test('named lists: the hits by name, every hit resolves to its match position', () => {
  const a = art(), L = a.lists;
  expect(L.accidental_hits).toEqual(HIT_NAMES);
  expect(L.accidental_qualified).toEqual(QUALIFIED);
  expect(L.qualified_hits.length + L.not_qualified.length).toBe(a.hits.length);
  expect(new Set(a.hits.map(hk)).size).toBe(a.hits.length);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, []);
  checkNamedList('window_off_board', L.window_off_board, []);
  checkHitPositions(a, SESSIONS, ROOT, []);
  expect(qualified().map(qName)).toEqual(QUALIFIED);
});

test('pinned: denominators, hits, qualify, controls', () => {
  const a = art();
  for (const u of USERS) {
    expect(a.denominators[u].TST, u).toEqual(DENOM[u].TST);
    expect(a.qualify.by_player[u], u).toEqual(QUALIFY[u]);
    expect(a.variants.tst.hits_by_player[u], u).toMatchObject(HITS[u]);
    expect(a.variants.tst.controls.orientation_baseline[u], u).toBe(DENOM[u].TST.all);
    for (const [k, by] of Object.entries(a.variants.tst.controls.under)) expect((by as any)[u], `${k} ${u}`).toBe(0);
  }
  expect(a.variants.tst.controls.ablation).toEqual(ABLATION);
});

test('mutants: each shared rule with a symptom here; the rest named equivalent', () => {
  const base = serialise(run({}));
  const b = JSON.parse(base);
  const opp = (a: any, s: string, k = 'all') => USERS.reduce((x, u) => x + a.denominators[u][s][k], 0);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  let a = mut({ pastPrefix: true });
  expect(opp(a, 'TST')).toBeGreaterThan(opp(b, 'TST'));
  a = mut({ openerLt: true });
  expect(opp(a, 'TST', 'in_opener')).toBeLessThan(opp(b, 'TST', 'in_opener'));
  // a spin_rule variant reads no window, so the window mutants cannot reach it
  for (const m of ['noMirror', 'noMustEmpty', 'noRoof', 'garbageEmpty', 'rowAnchorOff1', 'noRecon'] as (keyof Mutants)[])
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 1_200_000);
