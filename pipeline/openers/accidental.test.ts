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
 * filled cell above the T before j belongs to a piece placed after i (ROOF; any number of roof pieces). Tightened
 * the same day (yachi: 「影片食完tst ,擺完頂就食得，唔洗點砌，啲examples 要砌好多，唔算」; chose 「收緊版(0 個)」): the
 * slot box (the T rows and the row under them, the T's columns and one each side) must be complete right after i's
 * clear, so only the roof is built between the two spins (SLOT BUILT). The corpus then holds NO hit; the fourteen the
 * relaxed rule found all had slot walls built after i, and are pinned here as `SLOT_BUILT_AFTER`, re-derived under the
 * `no_slot_built` ablation and run through the qualify hook as the LOOSE profile, so the rules stay exercised.
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
import { ACCIDENTAL, accidentalDetect } from '../sim/technique-profile-accidental.ts';
import { accidentalQualifier, OTHER_PAGES, type AccidentalQualifyMutants } from '../sim/accidental-qualify.ts';
import { TECHNIQUES } from '../sim/techniques.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29', '2026-11-01', '2026-11-05', '2026-11-17', '2026-11-19', '2026-11-23', '2026-11-24', '2026-11-25', '2026-11-27']);
const ART_PATH = `${import.meta.dir}/../../analysis/accidental-facts.json`;
const OPENERS = import.meta.dir;
const ANALYSIS = `${import.meta.dir}/../../analysis`;
const TR = JSON.parse(readFileSync(ACCIDENTAL.transcriptionPath, 'utf8'));
const H = 40;
const USERS = ['pinglamb', 'yachi'] as const;

/** Every hit, by name, in artefact order: none, since the slot-built clause. */
const HIT_NAMES: string[] = [];
/** The hits of the rule without its slot-built clause (the `no_slot_built` ablation, and the LOOSE profile below), in
 *  artefact order: every one had a wall cell of its slot placed between the two spins. */
const SLOT_BUILT_AFTER: string[] = [
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
  '2026-11-24 m5r1 yachi lock 42 tst',
  '2026-11-25 m5r6 yachi lock 162 tst',
];
/** Of the LOOSE hits, the two that are some opener route's own continuation (`opener_route`). */
const LOOSE_NOT_QUALIFIED = ['2026-10-09 m4r4 pinglamb lock 24 tst', '2026-10-12 m1r2 pinglamb lock 24 tst'];
const LOOSE_QUALIFIED = SLOT_BUILT_AFTER.filter(n => !LOOSE_NOT_QUALIFIED.includes(n));
const QUALIFIED: string[] = [];
/** each LOOSE hit's previous T-spin and roof pieces, by lock */
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
  '2026-11-24 m5r1 yachi lock 42 tst': [30, [37, 38]],
  '2026-11-25 m5r6 yachi lock 162 tst': [157, [160, 161]],
};

const DENOM = {
  pinglamb: { TST: { all: 2008, in_opener: 1960, mid_game: 48 } },
  yachi: { TST: { all: 1245, in_opener: 1176, mid_game: 69 } },
};
const HITS = { pinglamb: { all: 0, in_opener: 0, mid_game: 0, garbage_in_window: 0 },
               yachi: { all: 0, in_opener: 0, mid_game: 0, garbage_in_window: 0 } };
const QUALIFY = { pinglamb: { qualified: 0, not_qualified: {} }, yachi: { qualified: 0, not_qualified: {} } };
/** each clause dropped, at the opportunity. Only no_slot_built admits anything (the fourteen SLOT_BUILT_AFTER); the
 *  others equal the headline, 0, on this corpus, because every candidate they admit still fails slot-built */
const ABLATION = { no_next_t: { pinglamb: 0, yachi: 0 }, no_exposed: { pinglamb: 0, yachi: 0 },
                   no_access: { pinglamb: 0, yachi: 0 }, no_new_roof: { pinglamb: 0, yachi: 0 },
                   no_slot_built: { pinglamb: 5, yachi: 9 } };
type Abl = '' | keyof typeof ABLATION;

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const run = (m: Mutants) => build(ACCIDENTAL, m, digests());
/** the rule without its slot-built clause: the headline reads it as the `no_slot_built` ablation, every ablation as
 *  itself plus that one */
const LOOSE = { ...ACCIDENTAL, detect: { ...ACCIDENTAL.detect,
  match: ((d: any, jx: number, w: unknown, T: any, rows: number[], abl?: string, v?: string) =>
    accidentalDetect(d, jx, w, T, rows, abl ?? 'no_slot_built', v)) as any } };
let LOOSE_ART: any = null;
const looseArt = () => (LOOSE_ART ??= JSON.parse(serialise(build(LOOSE as any, {}, digests()))));
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
  // SLOT BUILT: every filled non-T cell of the slot box before j stood there before i (tag o:)
  if (abl !== 'no_slot_built') {
    const rs = lj.cells.map(c => c.row), cs = lj.cells.map(c => c.col);
    const r1 = Math.max(...rs), c0 = Math.max(0, Math.min(...cs) - 1), c1 = Math.min(W - 1, Math.max(...cs) + 1);
    for (let r = Math.min(...rs); r <= Math.min(H - 1, r1 + 1); r++) for (let c = c0; c <= c1; c++) {
      const x = grid[r]![c]!;
      if (!x.occ || lj.cells.some(t => t.row === r && t.col === c)) continue;
      if (!x.tag.startsWith('o:')) return null;
    }
  }
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
  expect(checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT)).toBe(20947);
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
      if (!abl || abl === 'no_slot_built') want.set(keyOf(d, s.i), [m.i, m.roofs]);
    }
    if (abl) {
      expect(by, abl).toEqual(ABLATION[abl]);
      expect(a.variants.tst.controls.ablation[abl], abl).toEqual(ABLATION[abl]);
      if (abl === 'no_slot_built') {
        const lg = new Map<string, [number, number[]]>(looseArt().hits.map((h: any) =>
          [hk(h), [h.rule.prev_spin_lock, h.rule.roof_locks]]));
        expect([...lg.entries()].sort()).toEqual([...want.entries()].sort());
      }
      continue;
    }
    const got = new Map<string, [number, number[]]>(a.hits.map((h: any) =>
      [hk(h), [h.rule.prev_spin_lock, h.rule.roof_locks]]));
    expect(got.size).toBe(a.hits.length);
    expect([...got.entries()].sort()).toEqual([...want.entries()].sort());
  }
}, 1_200_000);

test('each LOOSE hit: its previous T-spin cleared lines, no T between, roof pieces after it, a slot wall built after it', () => {
  const byKey = new Map(digests().map(d => [`${d.file}|${d.round}|${d.user}`, d]));
  expect(looseArt().lists.accidental_hits).toEqual(SLOT_BUILT_AFTER);
  for (const h of looseArt().hits) {
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
    // the clause the headline adds is what refuses it
    const lk = d.locks[h.lock]!;
    expect(accidentalDetect(d, h.lock, null, lk.cells, lk.clearedRows, undefined, 'tst'), qName(h)).toBeNull();
    expect(accidentalDetect(d, h.lock, null, lk.cells, lk.clearedRows, 'no_slot_built', 'tst'), qName(h)).not.toBeNull();
  }
}, 600_000);

test('the qualify verdicts on the LOOSE hits, re-derived; two are an opener route\'s own, and only that rule turned off adds them', () => {
  const byKey = new Map(digests().map(d => [`${d.file}|${d.round}|${d.user}`, d]));
  const L = looseArt().hits;
  const verdicts = (m: AccidentalQualifyMutants) => {
    const q = accidentalQualifier(OPENERS, ANALYSIS, m);
    return L.map((h: any) => q(h, byKey.get(`${h.file}|${h.round_index0}|${h.player}`)!));
  };
  const base = verdicts({});
  L.forEach((h: any, k: number) => {
    expect(base[k].qualifies, qName(h)).toBe(h.qualifies);
    expect(base[k].not_qualified, qName(h)).toEqual(h.not_qualified);
  });
  const nq = L.filter((h: any) => !h.qualifies);
  expect(nq.map(qName)).toEqual(LOOSE_NOT_QUALIFIED);
  expect(L.filter((h: any) => h.qualifies).map(qName)).toEqual(LOOSE_QUALIFIED);
  for (const h of nq) expect(h.not_qualified, qName(h)).toEqual(['opener_route']);
  for (const m of ['noOpener', 'noOtherPage', 'noOpenerRoute', 'noOpenerSpin'] as (keyof AccidentalQualifyMutants)[])
    expect(verdicts({ [m]: true }).filter(x => x.qualifies).length, m)
      .toBe(m === 'noOpenerRoute' ? L.length : LOOSE_QUALIFIED.length);
}, 600_000);

test('mid-game only: in_opener is exactly the opener window', () => {
  for (const h of [...art().hits, ...looseArt().hits]) expect(h.not_qualified.includes('in_opener'), qName(h)).toBe(h.in_opener);
  expect(qualified().every((h: any) => !h.in_opener)).toBe(true);
});

test('other_page against the other artefacts: no hit is another page\'s, keyed by round', () => {
  const mine = new Map<string, any>(looseArt().hits.map((h: any) => [hk(h), h]));
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
