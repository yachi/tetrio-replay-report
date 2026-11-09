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
import { build, category, HASHED, holes, serialise, stackHeight } from './pc-miss.ts';

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
  }
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
