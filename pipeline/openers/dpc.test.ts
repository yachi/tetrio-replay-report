/**
 * The DPC corpus artefact (`analysis/dpc-facts.json`, from `pipeline/sim/emit-dpc-facts.ts`; the rules are
 * `dpc-facts.ts`, the setups the gated `pipeline/openers/dpc-setups.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE ANCHOR: every player-round's PC points equal the replay's own Perfect Clear counter
 *      (`clears.allclear`, twice-extracted), with no exception.
 *   3. EVERY SETUP MATCHES ITSELF: a synthetic two-lock digest per setup (a clear that empties the board, then
 *      the setup's T on its base) is filed under that setup, as drawn and mirrored, and under nothing it is not
 *      `same_as`. That is the check on the frame: the transcription records T cells from the top of the drawn
 *      frame, the corpus from the bottom of a 40-row board, and an off-by-one in either is a miss here.
 *   4. MATCHED is a NAMED list (case, first setup id, mirrored, verified), never a count.
 *   5. MUTANTS, each with its asserted symptom; the ones the corpus cannot tell from the real rules are named
 *      EQUIVALENT, asserted to STAY byte-identical, and killed on the synthetic digests instead.
 *   6. 社畜トレイン: every hit its qualifier calls `dpc` is a case here at the same lock, or named.
 *
 * Run: bun test pipeline/openers/dpc.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, classify, serialise, loadSetups, allclearOf, type DpcMutants } from '../sim/dpc-facts.ts';
import { digestCorpus, type TechDigest } from '../sim/technique-facts.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const ARTEFACT = `${import.meta.dir}/../../analysis/dpc-facts.json`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);
const H = 40, W = 10;

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
const setups = loadSetups();
const committed = () => readFileSync(ARTEFACT, 'utf8');
const caseKey = (c: any) => `${c.session} m${c.match}r${c.round} ${c.player} @${c.lock}`;

/** [case, first setup id of the matched group, mirrored, verified] */
const MATCHED: [string, string, boolean, boolean][] = [
  ['2026-07-22 m1r5 pinglamb @27', 'p01.000', false, false],
  ['2026-07-22 m2r7 yachi @27', 'p01.000', false, false],
  ['2026-07-22 m3r6 pinglamb @27', 'p01.000', false, false],
  ['2026-07-22 m5r4 pinglamb @27', 'p01.000', false, false],
  ['2026-07-22 m6r5 pinglamb @27', 'p01.000', false, false],
  ['2026-07-22 m7r3 yachi @27', 'p01.000', false, false],
  ['2026-07-22 m10r5 pinglamb @27', 'p07.000', false, false],
  ['2026-07-24 m1r4 pinglamb @27', 'p01.000', false, false],
  ['2026-07-24 m5r2 pinglamb @28', 'p07.000', false, false],
  ['2026-07-24 m6r8 pinglamb @27', 'p07.000', false, true],
  ['2026-07-28 m5r3 pinglamb @27', 'p07.000', false, false],
  ['2026-07-28 m7r3 pinglamb @27', 'p01.000', false, false],
  ['2026-07-28 m7r7 yachi @27', 'p01.000', false, false],
  ['2026-08-01 m3r6 pinglamb @27', 'p01.000', false, false],
  ['2026-08-01 m4r7 yachi @27', 'p01.000', false, false],
  ['2026-08-01 m5r2 pinglamb @27', 'p01.000', false, false],
  ['2026-08-01 m7r6 pinglamb @27', 'p07.000', false, false],
  ['2026-08-09 m3r8 pinglamb @27', 'p01.000', false, false],
  ['2026-08-14 m1r8 pinglamb @27', 'p07.000', false, true],
  ['2026-08-19 m4r6 pinglamb @27', 'p01.000', false, false],
  ['2026-08-25 m3r3 pinglamb @27', 'p01.000', false, true],
  ['2026-08-25 m3r7 pinglamb @27', 'p01.000', false, false],
  ['2026-08-25 m3r7 yachi @27', 'p01.000', false, true],
  ['2026-08-25 m6r6 pinglamb @27', 'p01.000', false, true],
  ['2026-08-25 m7r7 pinglamb @27', 'p07.000', false, false],
  ['2026-09-03 m2r1 pinglamb @27', 'p07.000', false, false],
  ['2026-09-11 m1r4 pinglamb @27', 'p01.000', false, true],
  ['2026-09-11 m3r1 pinglamb @27', 'p01.000', false, true],
  ['2026-09-11 m3r1 yachi @27', 'p01.000', false, false],
  ['2026-09-11 m3r2 pinglamb @27', 'p01.000', false, false],
  ['2026-09-11 m5r6 pinglamb @27', 'p01.000', false, false],
  ['2026-09-11 m7r3 pinglamb @27', 'p07.000', false, false],
  ['2026-09-18 m3r4 pinglamb @27', 'p07.000', false, false],
  ['2026-09-18 m4r1 pinglamb @27', 'p07.000', false, false],
  ['2026-09-18 m5r5 pinglamb @27', 'p01.000', false, true],
  ['2026-09-18 m6r7 yachi @27', 'p01.000', false, false],
  ['2026-09-18 m7r5 pinglamb @27', 'p01.000', false, false],
  ['2026-09-18 m11r2 pinglamb @27', 'p07.000', false, false],
  ['2026-09-18 m12r8 pinglamb @27', 'p01.000', false, false],
  ['2026-09-18 m13r3 pinglamb @27', 'p07.000', false, false],
  ['2026-09-18 m13r4 pinglamb @27', 'p07.000', false, false],
  ['2026-09-19 m1r4 pinglamb @27', 'p07.000', false, false],
  ['2026-09-19 m13r1 pinglamb @27', 'p07.000', false, false],
  ['2026-09-19 m13r4 pinglamb @27', 'p07.000', false, false],
  ['2026-09-19 m13r7 pinglamb @27', 'p07.000', false, true],
  ['2026-09-19 m15r7 pinglamb @27', 'p01.000', false, true],
  ['2026-09-19 m15r7 yachi @27', 'p01.000', false, false],
  ['2026-09-19 m16r4 pinglamb @27', 'p01.000', false, false],
  ['2026-09-19 m20r3 pinglamb @27', 'p07.000', false, false],
  ['2026-10-03 m4r6 pinglamb @27', 'p01.000', false, false],
  ['2026-10-03 m5r1 yachi @27', 'p01.000', false, false],
  ['2026-10-03 m9r1 pinglamb @27', 'p07.000', false, true],
  ['2026-10-03 m11r1 pinglamb @27', 'p07.000', false, false],
  ['2026-10-03 m15r2 pinglamb @27', 'p07.000', false, false],
  ['2026-10-03 m20r1 pinglamb @27', 'p07.000', false, false],
  ['2026-10-03 m20r3 pinglamb @27', 'p01.000', false, false],
  ['2026-10-09 m4r6 pinglamb @27', 'p07.000', false, false],
  ['2026-10-09 m9r6 pinglamb @27', 'p01.000', false, false],
  ['2026-10-09 m10r4 pinglamb @27', 'p07.000', false, false],
  ['2026-10-09 m10r9 yachi @27', 'p01.000', false, false],
  ['2026-10-12 m4r4 yachi @27', 'p01.000', false, false],
  ['2026-10-12 m7r2 pinglamb @27', 'p01.000', false, false],
  ['2026-10-12 m7r2 yachi @27', 'p10.003', false, true],
  ['2026-10-20 m2r6 yachi @27', 'p10.003', false, true],
  ['2026-10-20 m3r1 pinglamb @27', 'p07.000', false, false],
  ['2026-10-20 m4r6 pinglamb @27', 'p07.000', false, false],
  ['2026-10-22 m1r4 pinglamb @27', 'p01.000', false, false],
  ['2026-10-22 m1r7 pinglamb @27', 'p07.000', false, false],
  ['2026-10-22 m2r8 pinglamb @27', 'p07.000', false, false],
  ['2026-10-22 m4r4 pinglamb @27', 'p01.000', false, false],
  ['2026-10-22 m5r4 pinglamb @27', 'p07.000', false, false],
  ['2026-10-22 m6r3 pinglamb @27', 'p01.000', false, false],
  ['2026-10-22 m6r5 pinglamb @27', 'p07.000', false, true],
  ['2026-10-22 m7r1 pinglamb @27', 'p01.000', false, false],
  ['2026-10-22 m7r6 pinglamb @27', 'p01.000', false, true],
  ['2026-10-22 m7r7 pinglamb @27', 'p07.000', false, false],
  ['2026-10-22 m7r8 pinglamb @27', 'p07.000', false, false],
  ['2026-10-22 m9r3 pinglamb @27', 'p01.000', false, false],
];

/** 社畜トレイン hits its qualifier calls `dpc` that are NOT a case here, with the reason */
const SHACHIKU_DPC_NOT_A_CASE: Record<string, string> = {
  // the second T-spin after the PC: this artefact's case is the first one, at lock 29
  '2026-07-22 m10r8 yachi @31': 'not_first_tspin',
};

test('byte identity: the committed artefact is what build() produces now', () => {
  expect(serialise(build({}, digests()))).toBe(committed());
}, 600_000);

test('anchor: PC points equal the replay\'s own allclear counter in every player-round', () => {
  const art = JSON.parse(committed());
  expect(art.pc_anchor.disagree).toEqual([]);
  expect(art.pc_anchor.rounds_agree).toBe(art.pc_anchor.rounds);
  expect(art.pc_anchor.pcs_replay).toBeGreaterThan(0);
  const pcs = Object.values(art.by_player).reduce((a: number, p: any) => a + p.pc_points, 0);
  expect(pcs).toBe(art.pc_anchor.pcs_replay);
  // a missing counter throws, never defaults
  const read = allclearOf(ROOT);
  expect(() => read({ ...digests()[0]!, user: 'nobody' })).toThrow(/no clears.allclear/);
}, 600_000);

/** a two-lock digest: an I clearing the bottom row empties the board, then the setup's T on its base */
function synthetic(s: any, mirrored: boolean, shiftT = 0, cleared?: number): TechDigest {
  const base: string[] = s.base.map((r: string) => mirrored ? [...r].reverse().join('') : r);
  const board = [...Array(H - base.length).fill('.'.repeat(W)), ...base.map(r => r.replace(/x/g, 'J'))];
  const top = H - s.frame_rows;
  const cells = s.t_cells.map(([r, c]: [number, number]) => ({ row: top + r, col: (mirrored ? W - 1 - c : c) + shiftT }));
  const empty = { piece: 'I', spin: 'none', cleared: 1, cells: [0, 1, 2, 3].map(c => ({ row: H - 1, col: c })),
                  clearedRows: [H - 1], garbage: 0, mapOk: true };
  const t = { piece: 'T', spin: 'full', cleared: cleared ?? s.lines, cells, clearedRows: [], garbage: 0, mapOk: true };
  return { session: 'synthetic', file: s.id, round: 0, match: 1, user: 'p', v: 1, locks: [empty, t],
           tspins: [{ i: 1, board }] } as any;
}

test('every setup is filed under itself, drawn and mirrored, and only with its same_as group', () => {
  for (const s of setups) for (const mirrored of [false, true]) {
    const cs = classify([synthetic(s, mirrored)], setups).cases;
    expect(cs.length).toBe(1);
    expect(cs[0]!.outcome).toBe('matched');
    expect(cs[0]!.setups).toContain(s.id);
    // a group may also hold setups whose mirror is this shape; never one whose shape differs
    for (const id of cs[0]!.setups) if (id !== s.id && !s.same_as.includes(id)) {
      const o = setups.find(x => x.id === id)!;
      expect([o.base.join('/'), o.base.map(r => [...r].reverse().join('')).join('/')]).toContain(s.base.join('/'));
    }
  }
});

test('matched cases are a named list, and every other case is unmatched (no base-only)', () => {
  const art = JSON.parse(committed());
  const got = art.cases.filter((c: any) => c.outcome === 'matched')
    .map((c: any) => [caseKey(c), c.setups[0], c.mirrored, c.verified]);
  expect(got).toEqual(MATCHED);
  expect(art.cases.filter((c: any) => c.outcome === 'base_only')).toEqual([]);
  for (const c of art.cases) expect(c.lock - c.pc_lock).toBeLessThanOrEqual(art.rules.window_locks);
});

test('mutants on the corpus, each with its symptom', () => {
  const ds = digests();
  const real = classify(ds, setups).cases;
  const key = (cs: any[]) => cs.map(c => `${caseKey(c)} ${c.outcome} ${c.setups.join(',')}`);
  const run = (m: DpcMutants) => classify(ds, setups, m).cases;
  // noMirror: EQUIVALENT in OUTCOME on this corpus, because the video draws every shape a case matched in both
  // hands (くるまDPC and トラックDPC each on a pair of mirrored pages): it only drops, from each matched case, the
  // names that reach it through the mirror. Killed on a synthetic digest below
  expect(real.some(c => c.outcome === 'matched' && c.mirrored)).toBe(false);
  const nm = run({ noMirror: true });
  expect(nm.map(c => `${caseKey(c)} ${c.outcome}`)).toEqual(real.map(c => `${caseKey(c)} ${c.outcome}`));
  expect(nm.some((c, i) => c.setups.length < real[i]!.setups.length)).toBe(true);
  nm.forEach((c, i) => expect(real[i]!.setups).toEqual(expect.arrayContaining(c.setups)));
  // noGarbageStrip: only matches that stood on garbage rows are lost
  const ng = run({ noGarbageStrip: true });
  const lostG = real.filter(c => c.outcome === 'matched' && !ng.some(x => caseKey(x) === caseKey(c) && x.outcome === 'matched'));
  expect(lostG.length).toBeGreaterThan(0);
  expect(lostG.every(c => c.garbage_rows > 0)).toBe(true);
  // a shorter window: only cases whose T is more than 9 locks after the PC go
  const w9 = run({ window: 9 });
  const gone = real.filter(c => !w9.some(x => caseKey(x) === caseKey(c)));
  expect(gone.length).toBeGreaterThan(0);
  expect(gone.every(c => c.lock - c.pc_lock > 9)).toBe(true);
  // EQUIVALENT on this corpus (every base it matches admits one T placement clearing those lines, and no
  // first T-spin falls past the next PC): asserted to stay identical, killed on the synthetic digests below
  for (const m of [{ noTCheck: true }, { noLinesCheck: true }, { ignoreNextPc: true }] as DpcMutants[])
    expect(key(run(m))).toEqual(key(real));
}, 600_000);

test('the equivalent mutants are killed on synthetic digests', () => {
  // the one setup the video draws in one hand only (TSD DPC(Iずらし)): mirrored, it matches only through the mirror
  const one = setups.find(x => x.id === 'p10.003')!;
  const mir = synthetic(one, true);
  expect(classify([mir], setups).cases[0]!.outcome).toBe('matched');
  expect(classify([mir], setups).cases[0]!.mirrored).toBe(true);
  expect(classify([mir], setups, { noMirror: true }).cases[0]!.outcome).not.toBe('matched');
  const s = setups.find(x => x.id === 'p01.000')!;
  // the T one column over (still on the board): the real rules call it base_only, noTCheck a match
  const moved = synthetic(s, false, -1);
  expect(classify([moved], setups).cases[0]!.outcome).toBe('base_only');
  expect(classify([moved], setups, { noTCheck: true }).cases[0]!.outcome).toBe('matched');
  // the engine records one line fewer: base_only for the real rules, a match without the lines check
  const fewer = synthetic(s, false, 0, s.lines - 1);
  expect(classify([fewer], setups).cases[0]!.outcome).toBe('base_only');
  expect(classify([fewer], setups, { noLinesCheck: true }).cases[0]!.outcome).toBe('matched');
  // a second PC between the first and the T: the real rules start the case from the second PC
  const d = synthetic(s, false);
  const again = { ...d.locks[0]! };
  const two = { ...d, locks: [d.locks[0]!, again, d.locks[1]!], tspins: [{ i: 2, board: d.tspins[0]!.board }] } as any;
  expect(classify([two], setups).cases[0]!.pc_lock).toBe(1);
  expect(classify([two], setups, { ignoreNextPc: true }).cases[0]!.pc_lock).toBe(0);
});

test('社畜トレイン: every hit called dpc is a case here at the same lock, or named', () => {
  const art = JSON.parse(committed());
  const sh = JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/shachikutrain-facts.json`, 'utf8'));
  const cases = new Set(art.cases.map(caseKey));
  const missing = sh.hits.filter((h: any) => (h.not_qualified ?? []).includes('dpc')).map(caseKey)
    .filter((k: string) => !cases.has(k));
  expect(missing).toEqual(Object.keys(SHACHIKU_DPC_NOT_A_CASE));
  for (const k of Object.keys(SHACHIKU_DPC_NOT_A_CASE)) {
    const [sess, mr, player] = k.split(' ');
    expect(art.cases.some((c: any) => c.session === sess && `m${c.match}r${c.round}` === mr && c.player === player)).toBe(true);
  }
});
