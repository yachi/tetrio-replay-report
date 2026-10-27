/**
 * The 基本的なドネイト (basic donating) technique artefact (`analysis/basicdonating-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique basicdonating`; the rules are the shared `technique-facts.ts`, the
 * donation rule `basicdonating-rule.ts`, the profile `technique-profile-basicdonating.ts`, the qualify rule
 * `basicdonating-qualify.ts`, the drawings the gated `pipeline/openers/basicdonating-technique.json`).
 *
 * Since 2026-10-26 the page is matched by yachi's donation rule, not by windows: a piece overhangs empty cells inside
 * the rows the T-spin clears, and the clear opens them again; any column, any depth; the covering cells the T or
 * complete pieces; a hole under the T's nub alone is a plain T-spin.
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count, as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `donationColumns` (TS, ownership ablated: the drawings carry none) fires on
 *      every board of the page exactly where the gate's `rule_accounting` records it, with the same holes, misses
 *      exactly the spin boards `rule_not_fired` names, and over every routes board's U slot that clears two rows fires
 *      exactly where `cross_source` records it.
 *   4. THE RULE ITSELF on synthetic boards: each clause bites, and each ablation lets exactly its case through.
 *   5. THE OTHER PAGES: `other_page` holds iff the hit is a hit of another technique artefact; the common hits pinned.
 *   6. THE QUALIFY RULE re-derived from the digests; with it off every hit qualifies.
 *   7. pinned per player: denominators, hits, payoffs, controls, the qualify tally, per session.
 *   8. matcher mutants, each with its asserted symptom.
 *
 * Run: bun test pipeline/openers/basicdonating.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, type Mutants, type TechDigest, type Cell } from '../sim/technique-facts.ts';
import { BASICDONATING } from '../sim/technique-profile-basicdonating.ts';
import { donationQualifier, OTHER_PAGES } from '../sim/basicdonating-qualify.ts';
import { donationColumns, ruleMatch, RULE_ABLATIONS } from '../sim/basicdonating-rule.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);
const ART_PATH = `${import.meta.dir}/../../analysis/basicdonating-facts.json`;
const TR = JSON.parse(readFileSync(BASICDONATING.transcriptionPath, 'utf8'));
const USERS = ['pinglamb', 'yachi'] as const;
const H = 40, W = 10;

/** Per player: the opportunities (scored full TSDs), split at the 0-based opener window. */
const DENOM: Record<string, any> = {"pinglamb": {"all": 5636, "in_opener": 1113, "mid_game": 4523}, "yachi": {"all": 5100, "in_opener": 1317, "mid_game": 3783}};
const HITS: Record<string, any> = {"pinglamb": {"all": 374, "in_opener": 109, "mid_game": 265, "mirrored": 0, "garbage_in_window": 122}, "yachi": {"all": 343, "in_opener": 43, "mid_game": 300, "mirrored": 0, "garbage_in_window": 140}};
/** The payoff (stored under `followup_by_player`, the shared artefact key). */
const PAYOFF: Record<string, any> = {"pinglamb": {"fired": 34, "not_fired": {"i_in_well_not_quad": 19, "past_verified": 15, "round_ended": 10, "well_covered": 28, "well_filled_not_i": 268}}, "yachi": {"fired": 61, "not_fired": {"i_in_well_not_quad": 28, "past_verified": 9, "round_ended": 7, "well_covered": 50, "well_filled_not_i": 188}}};
/** The same rule at the other scored spins, and with each clause dropped at the opportunity. */
const CONTROLS = {"under": {"TSS": {"pinglamb": 32, "yachi": 137}, "TST": {"pinglamb": 1399, "yachi": 748}, "mini_TSS": {"pinglamb": 5, "yachi": 3}, "mini_TSD": {"pinglamb": 0, "yachi": 0}}, "ablation": {"allow_t_nub": {"pinglamb": 374, "yachi": 343}, "allow_fragment": {"pinglamb": 426, "yachi": 396}, "no_reopen": {"pinglamb": 436, "yachi": 479}, "allow_late_hole": {"pinglamb": 477, "yachi": 445}}, "orientation_baseline": {"pinglamb": 52, "yachi": 67}};
const QUALIFY: Record<string, any> = {"pinglamb": {"qualified": 263, "not_qualified": {"other_page": 111}}, "yachi": {"qualified": 180, "not_qualified": {"other_page": 163}}};
/** Qualifying hits per session (the list itself is `lists.qualified_hits`, held to `hits` below). */
const QUALIFIED_BY_SESSION: Record<string, number> = {'2026-07-22': 26, '2026-07-24': 15, '2026-07-28': 15, '2026-08-01': 25, '2026-08-09': 22, '2026-08-14': 35, '2026-08-19': 32, '2026-08-25': 25, '2026-09-03': 7, '2026-09-10': 22, '2026-09-11': 10, '2026-09-17': 8, '2026-09-18': 32, '2026-09-19': 53, '2026-10-03': 46, '2026-10-09': 38, '2026-10-12': 16, '2026-10-20': 9, '2026-10-22': 7};
/** How many donating columns a hit has, and how each column's covering pieces sit (inside the cleared rows or not). */
const COLUMNS = { per_hit: { 1: 569, 2: 147, 3: 1 }, cover: { cleared: 429, kept: 437 } };
/** Per other technique artefact: [its T's that are a donation here, its T's]. None is contained whole: a page's
 *  window does not read the ownership of its covering cells, and many of its hits cover with garbage or a fragment. */
const COMMON: Record<string, [number, number]> = {
  stsd: [0, 68], stmbcave: [129, 133], imperialcross: [6, 10], doubledagger: [34, 38], btcannon: [0, 0],
  cutcopy: [0, 2], shachikutrain: [37, 96], parapet: [7, 259], kaidan: [76, 167], dtcannon: [0, 20],
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(BASICDONATING, m, digests());
const hitKey = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
const dKey = (d: TechDigest) => `${d.session}|${d.file}|${d.round}|${d.user}`;
const hitName = (h: any) => `${h.session} m${h.match}r${h.round} ${h.player} ${h.variant} lock ${h.lock}`;

/** a drawing padded on top to the 40-row frame; `t` its T cells (moved into the frame), `off` the row shift */
function frame(rows: string[], t: [number, number][], filled: (ch: string) => boolean) {
  const off = H - rows.length;
  const withT = Array.from({ length: H }, (_, r) => Array.from({ length: W }, (_, c) =>
    r >= off && filled(rows[r - off]![c]!)));
  const tc = t.map(([r, c]) => ({ row: r + off, col: c }));
  for (const q of tc) withT[q.row]![q.col] = true;
  const C = new Set<number>();
  for (let r = 0; r < H; r++) if (withT[r]!.every(Boolean)) C.add(r);
  return { withT, tc, C, off };
}
/** every resting T placement on a drawn board (the gate's `t_placements`) */
function restingT(b: string[], filled: (ch: string) => boolean): [number, number][][] {
  const shapes = [[[0, 0], [0, 1], [0, 2], [1, 1]], [[0, 1], [1, 0], [1, 1], [1, 2]],
                  [[0, 0], [1, 0], [2, 0], [1, 1]], [[0, 1], [1, 0], [1, 1], [2, 1]]];
  const out: [number, number][][] = [];
  for (const sh of shapes) for (let r = 0; r < b.length; r++) for (let c = 0; c < W; c++) {
    const cs = sh.map(([dr, dc]) => [r + dr!, c + dc!] as [number, number]);
    if (!cs.every(([y, x]) => y < b.length && x < W && !filled(b[y]![x]!))) continue;
    if (cs.some(([y, x]) => y + 1 === b.length || filled(b[y + 1]![x]!))) out.push(cs);
  }
  return out;
}
const tKey = (cs: number[][]) => JSON.stringify([...cs].sort((x, y) => x[0]! - y[0]! || x[1]! - y[1]!));

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 900_000);

test('quarantined: report_eligible false, no claim ids, one rule variant, no window, the payoff harddrop\'s', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
  expect(a.cross_route).toBeUndefined();
  expect(Object.keys(a.variants)).toEqual(['rule']);
  expect(TR.variants.map((v: any) => [v.id, v.window_basis, v.spin, v.lines])).toEqual([['rule', 'rule', 'TSD', 2]]);
  const v = TR.variants[0];
  expect(v.payoff).toMatchObject({ kind: 'well_quad', piece: 'I', lines: 4 });
  expect(v.payoff.note).toContain('harddrop');
  expect(v.followup).toBeUndefined();
  expect(v.roof_cells).toEqual([]);
  // the controls are the rule's three ablations, not the window ablations
  expect(Object.keys(a.variants.rule.controls.ablation)).toEqual(RULE_ABLATIONS);
  // every hit carries its donating columns, and its own column is the payoff's well (the nearest to the T)
  for (const h of a.hits) {
    expect(h.mirrored, hitName(h)).toBe(false);
    expect(h.donation.columns.length, hitName(h)).toBeGreaterThan(0);
  }
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  expect(checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT)).toBe(15141);
  expect(art().check.reconstruction_disagreed).toBe(0);
  expect(art().check.rowmap_unverified).toBe(30);
  expect(art().check.rowmap_steps).toBe(264047);
});

test('the Python twin on the drawings: the rule fires where the gate records it, with its holes, and nowhere else', () => {
  const filled = (ch: string) => ch !== '-';
  const got = new Map<string, number[][]>(), spinFired = new Set<string>();
  for (const n of TR.nodes) {
    let b: string[], cands: [number, number][][];
    if (n.kind === 'spin') {
      const p = (n.spin_piece ?? 'T') as string;
      const sc = n.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) =>
        ch === p || ch === p.toLowerCase() ? [[i, c] as [number, number]] : []));
      const drop = new Set(sc.map(([r, c]: number[]) => `${r},${c}`));
      b = n.rows.map((r: string, i: number) => [...r].map((ch, c) => drop.has(`${i},${c}`) ? '-' : ch).join(''));
      cands = [sc];
    } else if (n.kind === 'base') {
      b = n.rows;
      cands = restingT(b, filled).filter(cs => frame(b, cs, filled).C.size === 2);
    } else continue;
    for (const cs of cands) {
      const f = frame(b, cs, filled);
      const cols = donationColumns(f.withT, f.tc, f.C, null, 'allow_fragment');
      if (!cols.length) continue;
      got.set(`${n.id} ${tKey(cs)}`, cols.map(x => [x.hole_row - f.off, x.col]).sort((x, y) => x[0]! - y[0]! || x[1]! - y[1]!));
      if (n.kind === 'spin') spinFired.add(n.id);
    }
  }
  const rec = new Map<string, number[][]>();
  for (const d of TR.variants[0].drawings) rec.set(`${d.board} ${tKey(d.t_cells)}`, d.holes);
  expect([...got.keys()].sort()).toEqual([...rec.keys()].sort());
  for (const [k, holes] of got) expect(holes, k).toEqual(rec.get(k)!);
  const spins = TR.nodes.filter((n: any) => n.kind === 'spin').map((n: any) => n.id);
  expect(spins.filter((id: string) => !spinFired.has(id)).sort()).toEqual(TR.rule_not_fired.map((e: any) => e.board).sort());
  expect(TR.rule_not_fired.map((e: any) => e.board).sort()).toEqual(['intro.l3', 'nub.hd']);
  // the routes boards, at their U slots that clear exactly two rows (`U` the spin cell, every other letter filled)
  const routes: string[] = [];
  for (const file of readdirSync(import.meta.dir).filter(x => x.endsWith('-routes.json')).sort())
    for (const n of JSON.parse(readFileSync(`${import.meta.dir}/${file}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const u = n.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'U' ? [[i, c] as [number, number]] : []));
      if (u.length !== 4) continue;
      const f = frame(n.rows, u, ch => ch !== '-' && ch !== 'U');
      if (f.C.size !== 2) continue;
      if (donationColumns(f.withT, f.tc, f.C, null, 'allow_fragment').length) routes.push(`${file} ${n.id}`);
    }
  const xs = TR.cross_source;
  expect(routes.sort()).toEqual([...xs.fires, ...xs.also].map((e: any) => `${e.file} ${e.node}`).sort());
}, 120_000);

/** A synthetic 40-row board, bottom-aligned: '.' empty, 'X' garbage, 'T' the lock, any other letter one piece. */
function synth(rows: string[], ownOverride: Record<string, number> = {}) {
  const off = H - rows.length;
  const withT = Array.from({ length: H }, () => new Array(W).fill(false));
  const own = Array.from({ length: H }, () => new Array(W).fill(-2));
  const tc: Cell[] = [];
  rows.forEach((row, i) => [...row].forEach((ch, c) => {
    const r = i + off;
    if (ch === '.') return;
    withT[r]![c] = true;
    if (ch === 'T') { tc.push({ row: r, col: c }); return; }
    own[r]![c] = ch === 'X' ? -1 : (ownOverride[ch] ?? ch.charCodeAt(0));
  }));
  const C = new Set<number>();
  for (let r = 0; r < H; r++) if (withT[r]!.every(Boolean)) C.add(r);
  return { withT, own, tc, C };
}
const cols = (s: ReturnType<typeof synth>, abl?: any) =>
  donationColumns(s.withT, s.tc, s.C, s.own, abl).map(x => `${x.col}:${x.depth}:${x.cover}`);

test('the rule on synthetic boards: each clause bites, and each ablation lets exactly its case through', () => {
  // an O over a hole in column 1, inside the two rows the TSD clears: a donation, its cover cleared
  const o = synth(['XOOTTTXXXX', 'XOOXTXXXXX', 'X.XXXXXXXX', 'X.XXXXXXXX']);
  expect(o.C.size).toBe(2);
  expect(cols(o)).toEqual(['1:2:cleared']);
  expect(ruleMatch(o.withT, o.tc, o.C, o.own)!.well).toEqual({ r: H - 2, c: 1 });
  // the same cells as garbage, or as a fragment of a piece: no donation (rule 2), unless allow_fragment
  const g = synth(['XXXTTTXXXX', 'XXXXTXXXXX', 'X.XXXXXXXX']);
  expect(cols(g)).toEqual([]);
  expect(cols(g, 'allow_fragment')).toEqual(['1:1:cleared']);
  const fr = synth(['XOOTTTXXXX', 'XPPXTXXXXX', 'X.XXXXXXXX']);
  expect(cols(fr)).toEqual([]);
  expect(cols(fr, 'allow_fragment')).toEqual(['1:1:cleared']);
  // a vertical Z keeping a cell above the cleared rows (not in column 1): still a donation, its cover kept
  const z = synth(['..Z.......', 'XZZTTTXXXX', 'XZXXTXXXXX', 'X.XXXXXXXX']);
  expect(cols(z)).toEqual(['1:1:kept']);
  // a piece cell above the cleared rows IN column 1: the clear does not open it (rule 1), unless no_reopen
  const k = synth(['IIII......', 'XOOTTTXXXX', 'XOOXTXXXXX', 'X.XXXXXXXX']);
  expect(cols(k)).toEqual([]);
  expect(cols(k, 'no_reopen')).toEqual(['1:1:kept']);
  // a hole covered only by the T's nub: a plain T-spin (rule 3), unless allow_t_nub
  const n = synth(['XXXTTTXXXX', 'XXXXTXXXXX', 'XXXX.XXXXX']);
  expect(cols(n)).toEqual([]);
  expect(cols(n, 'allow_t_nub')).toEqual(['4:1:cleared']);
  // ownership not verified: rule 2 cannot be read, so nothing donates
  expect(donationColumns(o.withT, o.tc, o.C, null)).toEqual([]);
  // the hole came first (rule 4): it is read for the piece directly over the hole, and a false or unreadable answer
  // stops the column, unless allow_late_hole
  const asked: number[] = [];
  const late = (k: number) => (asked.push(k), false);
  expect(donationColumns(o.withT, o.tc, o.C, o.own, undefined, late)).toEqual([]);
  expect(asked).toEqual([o.own![H - 3]![1]!]);
  expect(donationColumns(o.withT, o.tc, o.C, o.own, 'allow_late_hole', late).map(x => x.col)).toEqual([1]);
  expect(donationColumns(o.withT, o.tc, o.C, o.own, undefined, () => null)).toEqual([]);
  expect(donationColumns(o.withT, o.tc, o.C, o.own, undefined, () => true).map(x => x.col)).toEqual([1]);
  // the own column is the nearest to the T, then the leftmost
  const two = synth(['OOXTTTXXXX', 'OOXXTXXXXX', '..XXXXXXXX']);
  const m = ruleMatch(two.withT, two.tc, two.C, two.own)!;
  expect(m.columns.map(x => x.col)).toEqual([0, 1]);
  expect(m.well).toEqual({ r: H - 1, c: 1 });
  expect(m.box).toEqual({ rows: [H - 4, H - 1], cols: [1, 5] });
});

test('named lists: the qualifying hits are the hits that qualify; every hit resolves to its match position', () => {
  const a = art();
  const q = a.hits.filter((h: any) => h.qualifies);
  expect(a.lists.qualified_hits.length).toBe(q.length);
  // a T is counted once
  expect(new Set(a.hits.map(hitKey)).size).toBe(a.hits.length);
  checkNamedList('recon_dropped_tsd', a.lists.recon_dropped_tsd, []);
  checkNamedList('window_off_board', a.lists.window_off_board, []);
  expect(a.lists.basicdonating_hits.length).toBe(a.hits.length);
  checkHitPositions(a, SESSIONS, ROOT, []);
  const by: Record<string, number> = {};
  for (const h of q) by[h.session] = (by[h.session] ?? 0) + 1;
  expect(by).toEqual(QUALIFIED_BY_SESSION);
});

test('pinned: denominators, hits, payoffs, controls, columns, the qualify tally, per player', () => {
  const a = art();
  for (const u of USERS) expect(a.denominators[u].TSD, u).toEqual(DENOM[u]);
  expect(a.variants.rule.controls).toEqual(CONTROLS);
  for (const u of USERS) {
    expect(a.variants.rule.hits_by_player[u], u).toEqual(HITS[u]);
    expect(a.variants.rule.followup_by_player[u], u).toEqual(PAYOFF[u]);
    expect(PAYOFF[u].fired + total(PAYOFF[u].not_fired)).toBe(HITS[u].all);
    // an ablation only relaxes: it fires on every hit and more
    for (const ab of RULE_ABLATIONS) expect(CONTROLS.ablation[ab][u]).toBeGreaterThanOrEqual(HITS[u].all);
    const hs = a.hits.filter((h: any) => h.player === u);
    const tally: Record<string, number> = {};
    for (const h of hs) for (const r of h.not_qualified) tally[r] = (tally[r] ?? 0) + 1;
    expect({ qualified: hs.filter((h: any) => h.qualifies).length, not_qualified: tally }, u).toEqual(QUALIFY[u]);
  }
  const per: Record<number, number> = {}, cover: Record<string, number> = {};
  for (const h of a.hits) {
    per[h.donation.columns.length] = (per[h.donation.columns.length] ?? 0) + 1;
    for (const c of h.donation.columns) cover[c.cover] = (cover[c.cover] ?? 0) + 1;
  }
  expect({ per_hit: per, cover }).toEqual(COLUMNS as any);
});

test('the other pages: other_page iff the T is a hit of another artefact; the common hits, pinned', () => {
  const a = art();
  const mine = new Set(a.hits.map(hitKey));
  const theirs: Record<string, Set<string>> = {};
  for (const k of OTHER_PAGES)
    theirs[k] = new Set(JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/${k}-facts.json`, 'utf8')).hits.map(hitKey));
  const common: Record<string, [number, number]> = {};
  for (const k of OTHER_PAGES) common[k] = [[...theirs[k]!].filter(x => mine.has(x)).length, theirs[k]!.size];
  expect(common).toEqual(COMMON);
  for (const h of a.hits)
    expect(h.not_qualified.includes('other_page'), hitName(h)).toBe(OTHER_PAGES.some(k => theirs[k]!.has(hitKey(h))));
});

test('the qualify rule, re-derived from the digests; with it off every hit qualifies', () => {
  const a = art();
  const byD = new Map(digests().map(d => [dKey(d), d]));
  for (const [mut, all] of [[{}, false], [{ noOtherPage: true }, true]] as const) {
    const q = donationQualifier(import.meta.dir, mut);
    a.hits.forEach((h: any) => {
      const v = q(h, byD.get(`${h.session}|${h.file}|${h.round_index0}|${h.player}`)!);
      if (all) expect(v.qualifies, hitName(h)).toBe(true);
      else expect([v.qualifies, v.not_qualified], hitName(h)).toEqual([h.qualifies, h.not_qualified]);
    });
  }
}, 600_000);

test('mutants: each one turns this red with its own symptom', () => {
  const base = serialise(run({}));
  const b = JSON.parse(base);
  const fired = (a: any) => USERS.reduce((m, u) => m + a.variants.rule.followup_by_player[u].fired, 0);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  const k = (h: any) => hitKey(h);

  // MEASURED EQUIVALENT: a rule variant has no window to mirror; the rule reads both sides of the T alike
  expect(serialise(run({ noMirror: true }))).toBe(base);

  // MEASURED EQUIVALENT: garbage read as empty is a window rule; the rule reads the board the engine holds, and its
  // clause 2 reads garbage off the ownership grid, which the mutant does not touch
  expect(serialise(run({ garbageEmpty: true }))).toBe(base);

  let a: any;
  // the payoff mutants: the hits never move, only the payoffs
  a = mut({ payoffAnyPiece: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBeGreaterThan(fired(b));
  expect(a.hits.filter((h: any) => ['well_filled_not_i', 'i_in_well_not_quad'].includes(h.followup.reason)).length).toBe(0);
  a = mut({ payoffNoQuad: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBe(fired(b) + b.hits.filter((h: any) => h.followup.reason === 'i_in_well_not_quad').length);
}, 1_800_000);
