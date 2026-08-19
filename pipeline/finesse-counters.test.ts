/**
 * The finesse counters' units, pinned as a regression.
 *
 * `perfectpieces` counts PIECES; `faults` counts FAULT EVENTS, and one piece can register
 * several. That is why `perfect + faults` exceeds `pieces` in 770 of 900 player-rounds and
 * why no reading of the three counters as one denominator is available. The confusion was
 * live in this repo's own roadmap for a week ("perfect + faults exceeds pieces in 168/168
 * rounds", which was 2026-08-14's player-round count quoted as if it were the corpus), so
 * the invariants that discriminate the two units are asserted here rather than reasoned:
 *
 *   perfect <= pieces           — a per-piece counter cannot outrun the pieces
 *   faults  >= pieces - perfect — every non-perfect piece carries at least one fault event
 *   combo   <= perfect          — the longest run of perfect placements is a run OF them
 *
 * All three hold 900/900, and `perfect + faults == pieces` in exactly 130 of those — the
 * rounds where every faulty piece happened to carry exactly one fault. `< pieces` never
 * happens, which is what makes the second invariant an equality-with-slack rather than a
 * coincidence. (760/760 and 110 before 2026-08-19 joined the corpus.)
 *
 * Session totals are pinned as LITERALS. Re-deriving them from facts.json the way the
 * production code does can only catch a typo — see the `?? 0` that published "zero perfect
 * clears" for five sessions holding 65, whose test agreed because it walked the same wrong
 * path. A future extractor that re-sources these counters from a different object must fail
 * here loudly instead of re-deriving a new set of self-consistent numbers.
 *
 * Run: bun test pipeline/finesse-counters.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { assertCorpusIsEverySessionOnDisk } from './corpus-membership.ts';

// Pinned literals, not a glob: a session that stops being read must fail this file rather
// than shrink the corpus it covers. That guarded removal and not ARRIVAL — a seventh session
// was simply absent from the rows below, every assertion still passed over the six that were
// there, and nothing said the corpus had stopped being the corpus. The membership check under
// the table is the other direction.
const SESSIONS = [
  { dir: '2026-07-22', rounds: 158, strict: 140, equal: 18, faults: 2599, perfect: 12874, pieces: 14517 },
  { dir: '2026-07-24', rounds: 100, strict: 86, equal: 14, faults: 1543, perfect: 8189, pieces: 9187 },
  { dir: '2026-07-28', rounds: 128, strict: 106, equal: 22, faults: 1835, perfect: 9349, pieces: 10472 },
  { dir: '2026-08-01', rounds: 106, strict: 94, equal: 12, faults: 1798, perfect: 9592, pieces: 10728 },
  { dir: '2026-08-09', rounds: 100, strict: 82, equal: 18, faults: 1560, perfect: 8883, pieces: 9882 },
  { dir: '2026-08-14', rounds: 168, strict: 142, equal: 26, faults: 2530, perfect: 14096, pieces: 15707 },
  { dir: '2026-08-19', rounds: 140, strict: 120, equal: 20, faults: 2099, perfect: 10376, pieces: 11638 },
];

// At module scope, not inside a test: a membership check that lives in a test can be skipped
// by whatever skips the test, and the whole point is that it runs before any literal is read.
assertCorpusIsEverySessionOnDisk(`${import.meta.dir}/../sessions`, SESSIONS.map(s => s.dir));

const CORPUS = { rounds: 900, strict: 770, equal: 130, faults: 13964, perfect: 73359, pieces: 82131 };

interface Row {
  session: string; file: string; round: number; who: string;
  pieces: number; perfect: number; faults: number; combo: number;
}

function load(): Row[] {
  const out: Row[] = [];
  for (const s of SESSIONS) {
    const path = `${import.meta.dir}/../sessions/${s.dir}/report/facts.json`;
    const facts = JSON.parse(readFileSync(path, 'utf8'));
    for (const m of facts.matches) {
      for (const r of m.rounds) {
        for (const [who, p] of Object.entries<any>(r.players)) {
          // A missing counter is UNKNOWN, never 0 — `?? 0` on a required field is how a
          // corpus of defaults agrees with itself. Reading it as a number and asserting the
          // type is the guard.
          for (const k of ['pieces', 'finesse_perfect', 'finesse_faults', 'finesse_combo'])
            if (typeof p[k] !== 'number')
              throw new Error(`${s.dir} ${m.file} r${r.index} ${who}: ${k} is not a number`);
          out.push({
            session: s.dir, file: m.file, round: r.index, who,
            pieces: p.pieces, perfect: p.finesse_perfect,
            faults: p.finesse_faults, combo: p.finesse_combo,
          });
        }
      }
    }
  }
  return out;
}

const rows = load();

test('the corpus is the seven sessions, at the pinned player-round counts', () => {
  expect(rows.length).toBe(CORPUS.rounds);
  for (const s of SESSIONS)
    expect(rows.filter(r => r.session === s.dir).length).toBe(s.rounds);
});

test('perfect <= pieces — perfectpieces is a per-PIECE counter', () => {
  const bad = rows.filter(r => r.perfect > r.pieces);
  expect(bad).toEqual([]);
});

test('faults >= pieces - perfect — every non-perfect piece carries at least one fault', () => {
  const bad = rows.filter(r => r.faults < r.pieces - r.perfect);
  expect(bad).toEqual([]);
});

test('combo <= perfect — the longest run of perfect placements is a run OF them', () => {
  const bad = rows.filter(r => r.combo > r.perfect);
  expect(bad).toEqual([]);
});

test('perfect + faults exceeds pieces in 770 of 900, equals it in 130, and never falls short', () => {
  const strict = rows.filter(r => r.perfect + r.faults > r.pieces).length;
  const equal = rows.filter(r => r.perfect + r.faults === r.pieces).length;
  const below = rows.filter(r => r.perfect + r.faults < r.pieces).length;
  expect([strict, equal, below]).toEqual([CORPUS.strict, CORPUS.equal, 0]);
  for (const s of SESSIONS) {
    const mine = rows.filter(r => r.session === s.dir);
    expect([
      mine.filter(r => r.perfect + r.faults > r.pieces).length,
      mine.filter(r => r.perfect + r.faults === r.pieces).length,
      mine.filter(r => r.perfect + r.faults < r.pieces).length,
    ]).toEqual([s.strict, s.equal, 0]);
  }
});

test('session totals are the pinned literals, and none of them is zero', () => {
  for (const s of SESSIONS) {
    const mine = rows.filter(r => r.session === s.dir);
    const sum = (f: (r: Row) => number) => mine.reduce((a, r) => a + f(r), 0);
    expect(sum(r => r.faults)).toBe(s.faults);
    expect(sum(r => r.perfect)).toBe(s.perfect);
    expect(sum(r => r.pieces)).toBe(s.pieces);
    expect(s.faults).toBeGreaterThan(0);
    expect(s.perfect).toBeGreaterThan(0);
  }
  const tot = (f: (r: Row) => number) => rows.reduce((a, r) => a + f(r), 0);
  expect(tot(r => r.faults)).toBe(CORPUS.faults);
  expect(tot(r => r.perfect)).toBe(CORPUS.perfect);
  expect(tot(r => r.pieces)).toBe(CORPUS.pieces);
});

test('the decisive round: one non-perfect piece carrying seven faults', () => {
  // 2026-07-24 replay-2 r0 pinglamb — pieces 30, perfect 29, so exactly ONE piece is not
  // perfect, and it registers 7 faults. `combo` of 29 says the 29 perfect ones are a single
  // run, so the faulty piece is at an end and cannot be split across two pieces. No reading
  // of `faults` as a per-piece counter survives this round.
  const r = rows.find(x => x.session === '2026-07-24'
    && x.file === 'replay-2026-07-24-2.ttrm' && x.round === 0 && x.who === 'pinglamb');
  expect(r).toBeDefined();
  expect([r!.pieces, r!.perfect, r!.combo, r!.faults]).toEqual([30, 29, 29, 7]);
  expect(r!.pieces - r!.perfect).toBe(1);
});

test('a fault-free round is a round of nothing but perfect pieces', () => {
  // The other end of the same argument: with no fault events every piece is perfect, so the
  // longest perfect run is the whole round. 16 rounds, all seven sessions pooled (10 -> 16 when
  // 2026-08-19 joined, contributing 6 of its own).
  const clean = rows.filter(r => r.faults === 0);
  expect(clean.length).toBe(16);
  for (const r of clean) {
    expect(r.perfect).toBe(r.pieces);
    expect(r.combo).toBe(r.perfect);
  }
});

test('the four finesse rates are four different numbers, so a rate must name its denominator', () => {
  // Each of these is a defensible quantity and only one of them is what TETR.IO displays.
  // Pinned so that a section printing "finesse 失誤率 16.8%" beside "10.7% of pieces were
  // faulty" cannot be read as a contradiction, and so that renaming one silently into the
  // other fails here.
  const tot = (f: (r: Row) => number) => rows.reduce((a, r) => a + f(r), 0);
  const faults = tot(r => r.faults), perfect = tot(r => r.perfect), pieces = tot(r => r.pieces);
  const pct = (x: number) => Math.round(x * 10000) / 100;
  // Seven-session figures (2026-08-19 added): 16.83 -> 17.00, 10.65 -> 10.68, 89.35 -> 89.32,
  // 15.85 -> 15.99, 1.58 -> 1.592 — none of the four crosses another's old value.
  expect(pct(faults / pieces)).toBe(17.00);               // fault EVENTS per piece
  expect(pct(1 - perfect / pieces)).toBe(10.68);          // share of pieces that were faulty
  expect(pct(perfect / pieces)).toBe(89.32);              // TETR.IO's own displayed figure
  expect(pct(faults / (faults + perfect))).toBe(15.99);   // on no meaningful denominator
  // and the mechanism behind the gap: fault events per FAULTY piece, > 1 by construction
  expect(Math.round(faults / (pieces - perfect) * 1000) / 1000).toBe(1.592);
  expect(faults / (pieces - perfect)).toBeGreaterThan(1);
});
