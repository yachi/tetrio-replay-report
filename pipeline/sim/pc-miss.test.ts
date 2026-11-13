/**
 * pc-miss.ts → sessions/<date>/sim/pc-miss-facts.json: the committed artefacts are what the code makes.
 *   bun test pipeline/sim/pc-miss.test.ts
 *
 * A full rebuild of the corpus takes about 3.5 CPU-hours, so: every artefact's recorded md5s must equal
 * the current files' (an edit to the solver, the movegen or the emitter, or a re-emitted replay-facts.json,
 * stales every artefact loudly), and the shortest session is rebuilt byte for byte here, which is what
 * catches a behaviour change through the unhashed imports (emit-replay.ts, route-demos.ts).
 */
import { expect, test } from 'bun:test';
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { build, category, HASHED, holes, resumedIndex, serialise, stackHeight } from './pc-miss.ts';

const md5 = (p: string) => createHash('md5').update(readFileSync(p)).digest('hex');
const sessions = readdirSync('sessions').filter(d => existsSync(`sessions/${d}/sim/replay-facts.json`)).sort();
const REBUILD = '2026-10-20';

test('every session with replay facts has a pc-miss artefact', () => {
  const missing = sessions.filter(d => !existsSync(`sessions/${d}/sim/pc-miss-facts.json`));
  expect(missing).toEqual([]);
});

test('every artefact records the md5s of the current inputs and code', () => {
  for (const d of sessions) {
    const a = JSON.parse(readFileSync(`sessions/${d}/sim/pc-miss-facts.json`, 'utf8'));
    expect(a.session).toBe(d);
    expect(a.report_eligible).toBe(false);
    expect(a.md5.replay_facts).toBe(md5(`sessions/${d}/sim/replay-facts.json`));
    for (const p of HASHED) expect([d, p, a.md5[p]]).toEqual([d, p, md5(p)]);
    const files = [...new Set<string>(a.rounds.map((r: any) => r.file))].sort();
    const h = createHash('md5');
    for (const f of files) h.update(readFileSync(`sessions/${d}/${f}`));
    expect([d, a.md5.ttrm]).toEqual([d, h.digest('hex')]);
    // the split-tolerant prefix never ends before the plain one, and DPC misses are judged by it
    for (const r of a.rounds) {
      expect(r.verified_resumed_to).toBeGreaterThanOrEqual(r.verified_to ?? -1);
      for (const w of r.windows) for (const m of w.misses) {
        expect(m.verified_resumed).toBe(m.i + 1 < r.verified_resumed_to);
        const rep = w.kind === 'pc' ? m.lost_to === 'placement' && m.verified_resumed
          : m.lost_to === 'placement' && m.in_preview && m.verified;
        expect([d, r.match, r.round, r.user, m.i, 'category' in m]).toEqual([d, r.match, r.round, r.user, m.i, !!rep]);
      }
    }
  }
});

test('resumedIndex: the plain walk stops at a split PC packet, the split walk takes it', () => {
  const rows = [0, 1, 2, 3];
  const locks = [
    { frame: 100, sent: 2, lines: 2, rows: [0, 1], pc: false },
    { frame: 200, sent: 0, lines: 0, rows: [], pc: false },
    { frame: 300, sent: 11, lines: 4, rows, pc: true },
    { frame: 400, sent: 4, lines: 4, rows, pc: false },
    { frame: 500, sent: 0, lines: 0, rows: [], pc: false },
  ];
  const yOf = (r: number[], n: number) => Math.max(...r) - Math.floor((n - 1) / 2);
  const truth = [{ frame: 101, amt: 2, y: yOf([0, 1], 2) }, { frame: 300, amt: 1, y: yOf(rows, 4) },
    { frame: 300, amt: 10, y: yOf(rows, 4) }, { frame: 402, amt: 4, y: yOf(rows, 4) }];
  expect(resumedIndex(locks, truth, false)).toBe(0);
  expect(resumedIndex(locks, truth)).toBe(3);
  // not a PC lock: no split allowed
  expect(resumedIndex(locks.map(l => ({ ...l, pc: false })), truth)).toBe(0);
  // packets that do not sum to the sent amount stop the walk
  expect(resumedIndex(locks, truth.map((t, i) => (i === 2 ? { ...t, amt: 9 } : t)))).toBe(0);
  // a packet on the wrong row stops it
  expect(resumedIndex(locks, truth.map((t, i) => (i === 2 ? { ...t, y: t.y + 3 } : t)))).toBe(0);
});

test(`${REBUILD} rebuilds byte for byte`, () => {
  const got = serialise(build(`sessions/${REBUILD}`));
  expect(got).toBe(readFileSync(`sessions/${REBUILD}/sim/pc-miss-facts.json`, 'utf8'));
}, 600_000);

test('categories: hole before over before hold before spot', () => {
  const grid = ['GGGGGGGG..', 'GGGGGGGG..'];
  const o = { grid, cells: [8, 9, 18, 19], piece: 'O' };   // an O into the bottom of the well
  expect(stackHeight(grid)).toBe(2);
  expect(category(o, 2, 'O')).toBe('spot');
  expect(category(o, 2, 'I')).toBe('hold');
  expect(category(o, 1, 'O')).toBe('over');
  // an O one row up, over the well's mouth, covers two empty cells
  expect(holes(['GGGGGGGG..'])).toBe(0);
  expect(category({ grid: ['GGGGGGGG..'], cells: [18, 19, 28, 29], piece: 'O' }, 6, 'O')).toBe('hole');
});
