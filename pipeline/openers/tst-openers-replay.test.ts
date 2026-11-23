/**
 * `analysis/tst-openers-tp-replay.json` (emitted by `pipeline/sim/emit-tst-opener-choices.py`): which bag-1 board each
 * player built in every round against the best board the T-placed ranking holds for the dealt order. CONSTRUCTED and
 * quarantined (`report_eligible: false`, no claim id, no badge).
 *
 * This file is the SECOND implementation. It shares nothing with the Python emitter: it decodes the first locks from
 * `sessions/<date>/sim/replay-facts.json` itself (own shape table walk, own queue/hold walk, own order index), and
 * computes J from the committed first-bag vectors and the ranking's `cum` / `classes` with its own triangular solve.
 * What is checked:
 *   (a) the artefact's md5s (ranking, vectors, emitter, every replay-facts) are current;
 *   (b) every player-round's status, order index and matched board equal this file's derivation, and the statuses
 *       partition the rows (one status each, the total equal to the replay-facts player-rounds);
 *   (c) the actual chance of every matched row at every budget, and the repertoire / global best of a sample, equal
 *       this file's J;
 *   (d) four mutants of the derivation (order index off by one, seven locks read instead of six, garbage ignored,
 *       budget '1' read for '2'), each of which must change the result.
 * Run: bun test pipeline/openers/tst-openers-replay.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { inflateSync } from 'node:zlib';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..', '..');
const rd = (p: string) => readFileSync(join(ROOT, ...p.split('/')));
const md5 = (b: Buffer) => createHash('md5').update(b).digest('hex');
const ART = JSON.parse(rd('analysis/tst-openers-tp-replay.json').toString());
const TP_RAW = rd('analysis/tst-openers-tp.json');
const TP = JSON.parse(TP_RAW.toString());
const B1_RAW = rd('analysis/tst-openers-tp-b1.json');
const B1 = JSON.parse(B1_RAW.toString());
const B = 5040, N2 = B * B, INFEAS = 10;
const BKEYS = ['0', '1', '2', 'inf'];

// ---- (a) md5s -------------------------------------------------------------------------------------------------------
test('the artefact names the inputs it was built from', () => {
  expect(ART.schema).toBe('tst-openers-replay/1');
  expect(ART.report_eligible).toBe(false);
  expect(ART.constructed).toBe(true);
  expect(ART.md5.tp).toBe(md5(TP_RAW));
  expect(ART.md5.b1).toBe(md5(B1_RAW));
  expect(ART.md5.emitter).toBe(md5(rd('pipeline/sim/emit-tst-opener-choices.py')));
  const sess = readdirSync(join(ROOT, 'sessions')).filter((s) => { try { readFileSync(join(ROOT, 'sessions', s, 'sim', 'replay-facts.json')); return true; } catch { return false; } }).sort();
  expect(Object.keys(ART.md5.replay_facts).sort()).toEqual(sess);
  expect(ART.sessions).toEqual(sess);
  for (const s of sess) expect(ART.md5.replay_facts[s]).toBe(md5(rd(`sessions/${s}/sim/replay-facts.json`)));
});

// ---- own derivation -------------------------------------------------------------------------------------------------
/** The counter's first-bag recursion order: the permutations of 'IOTSZJL' by position, i.e. lexicographic over that string. */
function perms(s: string): string[] {
  if (s.length <= 1) return [s];
  const out: string[] = [];
  for (let i = 0; i < s.length; i++) for (const t of perms(s.slice(0, i) + s.slice(i + 1))) out.push(s[i] + t);
  return out;
}
const ORDERS = perms('IOTSZJL');
const ORDER_IX = new Map(ORDERS.map((p, i) => [p, i]));
const enc = (cs: Record<string, number[]>) => Object.keys(cs).sort().map((k) => `${k}:${[...cs[k]].sort((a, b) => a - b).join(',')}`).join('/');
const KEPT = new Map<string, string>(TP.boards.map((b: any) => [enc(Object.fromEntries(b.pieces)), b.name]));

type Opts = { first: number; garbage: boolean; orderShift: number };
const BASE: Opts = { first: 6, garbage: true, orderShift: 0 };

function cellsOf(d: any, piece: string, place: any): number[] {
  if (Array.isArray(place)) return place;
  const W = d.board.width, N = W * d.board.rows;
  const k = Math.floor(place / N), a = place % N, ay = Math.floor(a / W), ax = a % W;
  return d.shapes[piece][k].map(([dx, dy]: number[]) => (ay + dy) * W + ax + dx);
}
/** piece placed and hold box after each of the first n locks. */
function walk(seq: string, locks: any[], n: number): { piece: string; hold: string }[] {
  let cur = seq[0], ptr = 1, hold = '';
  const out = [];
  for (let i = 0; i < n; i++) {
    if (locks[i][5]) { if (hold === '') { hold = cur; cur = seq[ptr++]; } else { const t = cur; cur = hold; hold = t; } }
    out.push({ piece: cur, hold });
    cur = seq[ptr++];
  }
  return out;
}
const dirty = (locks: any[], n: number, o: Opts) => locks.slice(0, n).some((l) => l[2] > 0 || (o.garbage && l[4].length > 0));

/** [status, order, board | null] of one player-round. */
function derive(d: any, rnd: any, p: any, o: Opts): [string, number, string | null] {
  const ord = (ORDER_IX.get(rnd.seq.slice(0, 7)) as number) + o.orderShift;
  const L = p.locks, n = o.first;
  if (L.length < n) return ['short_round', ord, null];
  if (dirty(L, n, o)) return ['garbage_or_clear', ord, null];
  const w = walk(rnd.seq, L, n + (L.length > n ? 1 : 0));
  if (w[n - 1].hold) {
    const cs: Record<string, number[]> = {};
    for (let i = 0; i < n; i++) cs[w[i].piece] = (cs[w[i].piece] ?? []).concat(cellsOf(d, w[i].piece, L[i][1]));
    const name = KEPT.get(enc(cs));
    return name ? ['matched', ord, name] : ['not_kept', ord, null];
  }
  if (L.length > n && !dirty(L, n + 1, o) && w[n].hold === '' && [...w.map((x) => x.piece)].sort().join('') === [...rnd.seq.slice(0, 7)].sort().join(''))
    return ['seven_placed_no_hold', ord, null];
  return ['hold_not_bag1', ord, null];
}

const SESS: Record<string, any> = {};
for (const s of ART.sessions) SESS[s] = JSON.parse(rd(`sessions/${s}/sim/replay-facts.json`).toString());
function run(o: Opts) {
  const out: any[] = [];
  for (const s of ART.sessions) for (const rnd of SESS[s].rounds) for (const p of rnd.players) out.push({ s, m: rnd.match, r: rnd.round, u: p.user, ...(() => { const [st, ord, b] = derive(SESS[s], rnd, p, o); return { st, o: ord, b }; })() });
  return out;
}
const sig = (rows: any[]) => rows.map((r) => `${r.s}|${r.m}|${r.r}|${r.u}|${r.st}|${r.o}|${r.b}`).join('\n');
const artSig = ART.rows.map((r: any) => ({ s: r.s, m: r.m, r: r.r, u: r.u, st: r.st, o: r.o, b: r.b }));

test('every status, order and matched board is re-derived', () => {
  const mine = run(BASE);
  expect(mine.length).toBe(ART.rows.length);
  expect(sig(mine)).toBe(sig(artSig));
});

test('the statuses partition the player-rounds', () => {
  const total = ART.sessions.reduce((n: number, s: string) => n + SESS[s].rounds.reduce((m: number, r: any) => m + r.players.length, 0), 0);
  expect(ART.rows.length).toBe(total);
  expect(ART.params.statuses.length).toBe(6);
  let sum = 0;
  for (const st of ART.params.statuses) sum += ART.rows.filter((r: any) => r.st === st).length;
  expect(sum).toBe(total);
  for (const r of ART.rows) {
    expect(ART.params.statuses.includes(r.st)).toBe(true);
    expect(r.j === null).toBe(r.st !== 'matched');
    expect(r.b !== null).toBe(r.st === 'matched');
    expect(r.l !== null).toBe(r.st === 'seven_placed_no_hold');
  }
});

// ---- (c) J ----------------------------------------------------------------------------------------------------------
function b1vec(name: string): number[] {
  const s = inflateSync(Buffer.from(B1.vectors[name], 'base64')).toString();
  expect(s.length).toBe(B);
  return [...s].map((c) => (c === '.' ? INFEAS : c.charCodeAt(0) - 48));
}
/** J by cost code, per budget key: sum_k (D_k - D_{k-1}) * p5_k with D from the triangular solve of cum. */
function jTable(b: any): Record<string, number[]> {
  const vec = b1vec(b.name);
  const n = new Array(INFEAS + 1).fill(0);
  for (const c of vec) n[c]++;
  const nfeas = n.slice(0, INFEAS).reduce((a: number, c: number) => a + c, 0);
  const ncls = b.cum.inf.length, p5 = b.classes.map((c: any) => c[2]);
  const Dinf = b.cum.inf.map((c: number) => { expect(c % nfeas).toBe(0); return c / nfeas; });
  const smin = n.findIndex((c: number, s: number) => s < INFEAS && c > 0);
  const Dfin: Record<number, number[]> = {};
  for (const bud of [0, 1, 2]) {
    if (bud < smin) continue;
    const row: number[] = [];
    for (let k = 0; k < ncls; k++) {
      let num = b.cum[String(bud)][k];
      for (let s = smin + 1; s <= bud; s++) num -= n[s] * Dfin[bud - s][k];
      expect(num % n[smin]).toBe(0);
      row.push(num / n[smin]);
    }
    Dfin[bud - smin] = row;
  }
  const jb = (row: number[]) => { let prev = 0, j = 0; row.forEach((d, i) => { j += (d - prev) * p5[i]; prev = d; }); return j; };
  const out: Record<string, number[]> = {};
  for (const [bk, bud] of [['0', 0], ['1', 1], ['2', 2], ['inf', null]] as [string, number | null][]) {
    out[bk] = Array.from({ length: INFEAS + 1 }, (_, s) => (s >= INFEAS ? 0 : bud === null ? jb(Dinf) : Dfin[bud - s] ? jb(Dfin[bud - s]) : 0));
  }
  return out;
}
const CACHE = new Map<string, { vec: number[]; tab: Record<string, number[]> }>();
const BOARDS = new Map<string, any>(TP.boards.map((b: any) => [b.name, b]));
function jOf(name: string, o: number, bk: string): number {
  let e = CACHE.get(name);
  if (!e) { e = { vec: b1vec(name), tab: jTable(BOARDS.get(name)) }; CACHE.set(name, e); }
  return e.tab[bk][e.vec[o]];
}

test('the actual chance of every matched round, and the bests of a sample, are re-derived', () => {
  const matched = ART.rows.filter((r: any) => r.st === 'matched');
  expect(matched.length).toBeGreaterThan(0);
  for (const r of matched) for (const bk of BKEYS) expect(jOf(r.b, r.o, bk)).toBe(r.j[bk][0]);
  // the repertoire is the boards a player built at least repertoire_min times, this file's own count
  const built: Record<string, Record<string, number>> = {};
  for (const r of matched) { built[r.u] ??= {}; built[r.u][r.b] = (built[r.u][r.b] ?? 0) + 1; }
  for (const u of Object.keys(built)) {
    const rep = Object.keys(built[u]).filter((n) => built[u][n] >= ART.params.repertoire_min).sort();
    expect([...ART.repertoire[u]].sort()).toEqual(rep);
  }
  const names: string[] = TP.boards.map((b: any) => b.name);
  let k = 0;
  for (const r of matched) {
    if (k++ % 40) continue;
    for (const bk of BKEYS) {
      const [a, rj, rb, gj, gb] = r.j[bk];
      const rep = ART.repertoire[r.u];
      const bestRep = Math.max(a, ...rep.map((n: string) => jOf(n, r.o, bk)));
      expect(rj).toBe(bestRep);
      expect(jOf(rb, r.o, bk)).toBe(rj);
      const bestG = Math.max(...names.map((n) => jOf(n, r.o, bk)));
      expect(gj).toBe(bestG);
      expect(jOf(gb, r.o, bk)).toBe(gj);
      expect(gj).toBeGreaterThanOrEqual(rj);
      expect(rj).toBeGreaterThanOrEqual(a);
      expect(a).toBeLessThanOrEqual(N2);
    }
  }
});

// ---- (d) mutants ----------------------------------------------------------------------------------------------------
test('each mutant of the derivation changes the result', () => {
  const base = sig(run(BASE));
  expect(sig(run({ ...BASE, orderShift: 1 }))).not.toBe(base);          // order index off by one
  expect(sig(run({ ...BASE, first: 7 }))).not.toBe(base);               // seven locks instead of six
  expect(sig(run({ ...BASE, garbage: false }))).not.toBe(base);         // garbage ignored
  const matched = ART.rows.filter((r: any) => r.st === 'matched');
  const wrongBudget = matched.filter((r: any) => jOf(r.b, r.o, '1') !== r.j['2'][0]).length;  // budget '1' read for '2'
  expect(wrongBudget).toBeGreaterThan(0);
});
