/**
 * cspin-miss.ts → sessions/<date>/sim/cspin-miss-facts.json: the committed artefacts are what the code makes.
 *   bun test pipeline/sim/cspin-miss.test.ts
 *
 * cold-clear's search is the slow half and is not re-run here: each artefact commits cold-clear's own steps
 * for every window, and the rest (the windows, the hole carried through clears and garbage, both verdicts,
 * the boards the cards draw) is rebuilt from the replays and those steps, byte for byte, for every session.
 * The md5s catch an edit to the emitter, the position extractor, the C-Spin boards or the coach harness.
 */
import { expect, test } from 'bun:test';
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { build, ccVerdict, committedSteps, HASHED, humanVerdict, rounds, stringify, windows } from './cspin-miss.ts';

const md5 = (p: string) => createHash('md5').update(readFileSync(p)).digest('hex');
const sessions = readdirSync('sessions').filter(d => existsSync(`sessions/${d}/sim/replay-facts.json`)).sort();
const art = (d: string) => JSON.parse(readFileSync(`sessions/${d}/sim/cspin-miss-facts.json`, 'utf8'));
const MUTANT = '2026-10-20';

test('every session with replay facts has a cspin-miss artefact', () => {
  expect(sessions.filter(d => !existsSync(`sessions/${d}/sim/cspin-miss-facts.json`))).toEqual([]);
});

test('every artefact records the md5s of the current code and replays, and stays quarantined', () => {
  for (const d of sessions) {
    const a = art(d);
    expect([d, a.session, a.report_eligible]).toEqual([d, d, false]);
    for (const p of HASHED) expect([d, p, a.md5.files[p]]).toEqual([d, p, md5(p)]);
    for (const [f, h] of Object.entries(a.md5.ttrm)) expect([d, f, h]).toEqual([d, f, md5(`sessions/${d}/${f}`)]);
  }
});

test('no case had a C-Spin slot ready at one of the player\'s T\'s (none is a misdrop)', () => {
  for (const d of sessions) for (const w of art(d).windows) if (w.ready_at_t) expect([d, w.id, w.ready_at_t]).toEqual([d, w.id, []]);
});

test('every artefact rebuilds byte for byte from the replays and cold-clear\'s committed steps', () => {
  for (const d of sessions) {
    const path = `sessions/${d}/sim/cspin-miss-facts.json`;
    const old = readFileSync(path, 'utf8');
    expect([d, stringify(build(`sessions/${d}`, rounds(`sessions/${d}`), committedSteps(JSON.parse(old))))]).toEqual([d, old]);
  }
}, 600_000);

// Mutants on one session: each rule, turned off, must move the committed result.
test('mutants: the opener cut decides something; the slot check and the full-spin rule are named equivalents', () => {
  const rs = rounds(`sessions/${MUTANT}`);
  const a = art(MUTANT);
  const ids = (o: any) => rs.flatMap(r => windows(r.ps, r.meta, o).wins.map(w => w.id)).sort();
  const base = ids({});
  expect(base).toEqual(a.windows.map((w: any) => w.id).sort());
  // noSlotCheck: measured EQUIVALENT on 10-20 (and on 07-24, 09-03, 09-10, 10-09, 10-12 by hand): a hole that reached
  // a ready C-Spin slot was fired through or filled while still stage 2, so dropping stage 3 adds no window.
  expect(['noSlotCheck', ids({ noSlotCheck: true }).join('|') !== base.join('|')]).toEqual(['noSlotCheck', NO_SLOT_MOVES]);
  expect(ids({ openerAt: 0 })).not.toEqual(base);
  // anySpin: a T clearing 3 without a full T-spin would count. Measured over the committed windows: it
  // must change at least one verdict, the player's or cold-clear's.
  let moved = 0;
  const byId = new Map(a.windows.map((w: any) => [w.id, w]));
  for (const r of rs) for (const w of windows(r.ps, r.meta).wins) {
    const c = byId.get(w.id) as any;
    const hu = humanVerdict(r.ps, w.lock, w.hole, { anySpin: true });
    const cc = ccVerdict(r.ps[w.lock].field, w.hole, c.cc.steps, undefined, { anySpin: true });
    if (hu.fire !== c.human.fire || cc.fire !== c.cc.fire) moved++;
  }
  expect(['anySpin', moved]).toEqual(['anySpin', ANY_SPIN_MOVED]);
}, 120_000);

// A T that clears 3 through a C-Spin hole without a full T-spin: measured on 10-20. 0 makes anySpin an
// EQUIVALENT mutant on that night, named here so the day it stops being one is a red build.
const ANY_SPIN_MOVED = 0;
const NO_SLOT_MOVES = false;
