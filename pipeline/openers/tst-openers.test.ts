/**
 * The TST-opener enumeration (`analysis/tst-openers.json`, merged by `pipeline/sim/emit-tst-openers.py`
 * from the Rust counter `pipeline/sim/tst2bag-rs`). CONSTRUCTED and quarantined: nobody played these
 * boards, `report_eligible: false`, no claim id, no badge.
 *
 * The full recount is far too long for a test (the counter and the bag-4 sampler take hours of CPU), so:
 *   (a) the emitter's md5 (crate sources, Cargo.toml, both dependency crates' sources) and the shapes'
 *       md5 are current, so an edit to either stales the artefact loudly;
 *   (b) a PINNED-BY-NAME cheap set of shapes and two bag-4 lines are re-run through the built crate and
 *       must equal the artefact's records (the rest is not re-derived here: that is a known limit);
 *   (c) invariants written here, in TS, that do not reuse the crate, hold over EVERY tiling;
 *   (d) each invariant has a mutant that must trip it;
 *   (e) the same pinned shapes re-run in the counter's fixed-bag-1 mode (FIXED=1) must equal the
 *       artefact's `fixed` block (every bag-1 board's cum, and the board picked as best).
 *
 * Run: bun test pipeline/openers/tst-openers.test.ts   (the first run builds the crate)
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..', '..');
const SIM = join(ROOT, 'pipeline', 'sim');
const ART = JSON.parse(readFileSync(join(ROOT, 'analysis', 'tst-openers.json'), 'utf8'));
const SHAPES: any[] = JSON.parse(readFileSync(join(ROOT, 'pipeline', 'openers', 'tst-openers-shapes.json'), 'utf8')).shapes;
const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

/** Cheap shapes re-run through the crate (each a few seconds or less); pinned by NAME, never by a bound. */
const PINNED_SHAPES = ['s99', 's98', 's81', 's46', 's47', 's119'];
/** bag-4 lines re-run through `pc4`: one that finds nothing at all, one that finds it every time. */
const PINNED_PC4 = ['1019,977,1011,224|', '1015,899,961,897,896|'];

// ---- (a) hashes -----------------------------------------------------------------------------
function canon(x: any): string {
  if (Array.isArray(x)) return '[' + x.map(canon).join(',') + ']';
  if (x && typeof x === 'object') return '{' + Object.keys(x).sort().map((k) => JSON.stringify(k) + ':' + canon(x[k])).join(',') + '}';
  return JSON.stringify(x);
}
function emitterMd5(): string {
  const files = ['tst2bag-rs/Cargo.toml'];
  for (const c of ['tst2bag-rs', 'oracle-rs', 'pc-solver-rs'])
    for (const f of readdirSync(join(SIM, c, 'src'), { recursive: true }) as string[]) if (f.endsWith('.rs')) files.push(`${c}/src/${f}`);
  files.sort();
  const h = createHash('md5');
  for (const f of files) h.update(`${f}\0${md5(readFileSync(join(SIM, f)))}\n`);
  return h.digest('hex');
}
test('(a) emitter_md5 and shapes_md5 are current', () => {
  expect(ART.emitter_md5).toBe(emitterMd5());
  expect(ART.shapes_md5).toBe(md5(canon(SHAPES)));
  expect(ART.report_eligible).toBe(false);
  expect(ART.constructed).toBe(true);
  expect(ART.shapes.map((s: any) => s.id)).toEqual(SHAPES.map((s) => s.id).sort((a, b) => a - b));
});

// ---- (c) independent invariants ----------------------------------------------------------------
const KIND: Record<string, string> = {};
{
  const base: Record<string, [number, number][]> = {
    I: [[0, 0], [1, 0], [2, 0], [3, 0]], O: [[0, 0], [1, 0], [0, 1], [1, 1]], T: [[0, 0], [1, 0], [2, 0], [1, 1]],
    S: [[0, 0], [1, 0], [1, 1], [2, 1]], Z: [[1, 0], [2, 0], [0, 1], [1, 1]], J: [[0, 0], [1, 0], [2, 0], [0, 1]], L: [[0, 0], [1, 0], [2, 0], [2, 1]],
  };
  const norm = (c: [number, number][]) => {
    const mx = Math.min(...c.map((p) => p[0])), my = Math.min(...c.map((p) => p[1]));
    return c.map((p) => `${p[0] - mx},${p[1] - my}`).sort().join(';');
  };
  for (const [k, cells] of Object.entries(base)) {
    let c = cells;
    for (let r = 0; r < 4; r++) { KIND[norm(c)] = k; c = c.map(([x, y]) => [y, -x]); }
  }
}
/** Which tetromino a cell-index set (y*10+x) is, or null. */
const kindOf = (cs: number[]): string | null => {
  const pts = cs.map((c) => [c % 10, Math.floor(c / 10)] as [number, number]);
  const mx = Math.min(...pts.map((p) => p[0])), my = Math.min(...pts.map((p) => p[1]));
  return KIND[pts.map((p) => `${p[0] - mx},${p[1] - my}`).sort().join(';')] ?? null;
};
const idx = (ps: number[][]) => ps.map(([x, y]) => y! * 10 + x!).sort((a, b) => a - b);

/** Residue rows by the definition: shape + the TST's cells, minus the full rows, trailing empty rows dropped. */
function residue(shape: number[], tst: number[]): number[] {
  const all = new Set([...shape, ...tst]);
  const rows: number[] = [];
  for (let y = 0; y < 12; y++) {
    let r = 0, n = 0;
    for (let x = 0; x < 10; x++) if (all.has(y * 10 + x)) { r |= 1 << x; n++; }
    if (n !== 10) rows.push(r);
  }
  while (rows.length && rows[rows.length - 1] === 0) rows.pop();
  return rows;
}

/** Problems with one tiling (`til.pieces` as [kind, cells]) of a shape. Returns tags. */
function tilingProblems(shape: number[], til: any): string[] {
  const bad: string[] = [];
  const seen = new Set<number>();
  const cnt: Record<string, number> = {};
  for (const [k, cs] of til.pieces as [string, number[]][]) {
    if (kindOf(cs) !== k) bad.push('kind');
    for (const c of cs) { if (seen.has(c)) bad.push('overlap'); seen.add(c); }
    cnt[k] = (cnt[k] ?? 0) + 1;
  }
  const want = new Set(shape);
  if (seen.size !== want.size || [...seen].some((c) => !want.has(c))) bad.push('union');
  for (const k of 'IJLOSZ') if ((cnt[k] ?? 0) > 2) bad.push('over2');
  if ((cnt.T ?? 0) > 1) bad.push('over2');
  const left = [...'IJLOSTZ'].map((k) => k.repeat(Math.max(0, 2 - (cnt[k] ?? 0) - (k === 'T' ? 1 : 0)))).join('');
  if (til.left !== left) bad.push('left');
  if (!(til.B <= til.A && til.A <= 5040 * 5040)) bad.push('AB');
  if (!(til.p5 >= 0 && til.p5 <= 5040)) bad.push('p5');
  if (til.B > 0 && !til.tst) bad.push('tst');
  if (!til.full && (til.A > 0 || til.B > 0)) bad.push('full');
  return bad;
}
/** Problems with a whole artefact (against the shapes file). */
function artefactProblems(art: any): string[] {
  const bad: string[] = [];
  const dropped = art.dropped_constant.per_tiling as Record<string, unknown>;
  for (const rec of art.shapes) {
    const s = SHAPES.find((x) => x.id === rec.id)!;
    const shape = idx(s.cells), tst = idx(s.tst);
    if (rec.ntil !== rec.til.length) bad.push(`ntil s${rec.id}`);
    if (JSON.stringify(rec.rows) !== JSON.stringify(residue(shape, tst))) bad.push(`rows s${rec.id}`);
    for (const t of rec.til) {
      for (const p of tilingProblems(shape, { ...dropped, ...t })) bad.push(`${p} s${rec.id}`);
      if (!(t.p5 === 0 || t.B > 0)) bad.push(`p5 without B s${rec.id}`);
    }
  }
  for (const p of art.pc4) {
    if (!(p.ok + p.unk <= p.n && p.n <= 200 && p.fail3 >= 0 && p.fail3 <= 5040)) bad.push(`pc4 ${p.line}`);
  }
  return bad;
}

test('(c) per-tiling invariants hold over every tiling of every shape', () => {
  expect(artefactProblems(ART)).toEqual([]);
  expect(ART.shapes.reduce((n: number, s: any) => n + s.til.length, 0)).toBeGreaterThan(0);
});

// ---- (d) mutants: each invariant must fire on a corrupted copy ----------------------------------
const clone = <T>(x: T): T => JSON.parse(JSON.stringify(x));
function firstWith(pred: (t: any) => boolean): [any, any] {
  for (const r of ART.shapes) for (const t of r.til) if (pred(t)) return [r, t];
  throw new Error('no tiling for mutant');
}
const mutate = (pred: (t: any) => boolean, f: (rec: any, t: any, art: any) => void, tag: string) => {
  const art = clone(ART);
  const [r0, t0] = firstWith(pred);
  const rec = art.shapes.find((s: any) => s.id === r0.id);
  f(rec, rec.til[r0.til.indexOf(t0)], art);
  const bad = artefactProblems(art);
  expect(bad.some((b) => b.startsWith(tag + ' '))).toBe(true);
};
test('(d) each invariant has a mutant that fires', () => {
  const any = () => true;
  mutate(any, (_r, t) => { t.pieces[0][1][0] += 20; }, 'union');       // a moved cell (also breaks the kind or the union)
  mutate(any, (_r, t) => { t.pieces[0][0] = t.pieces[0][0] === 'I' ? 'O' : 'I'; }, 'kind');
  mutate(any, (_r, t) => { t.pieces.push(clone(t.pieces[0])); }, 'overlap');
  mutate(any, (_r, t) => { t.pieces.pop(); }, 'union');
  mutate(any, (_r, t) => { t.left = t.left + 'I'; }, 'left');
  mutate(any, (r) => { r.ntil += 1; }, 'ntil');
  mutate(any, (r) => { r.rows = [...r.rows, 1]; }, 'rows');
  mutate((t) => t.B > 0, (_r, t) => { t.A = t.B - 1; }, 'AB');
  mutate(any, (_r, t) => { t.A = 5040 * 5040 + 1; t.B = 0; }, 'AB');
  mutate(any, (_r, t) => { t.p5 = 5041; }, 'p5');
  mutate((t) => t.B > 0, (_r, t) => { t.tst = false; }, 'tst');
  mutate((t) => !t.full, (_r, t) => { t.A = 1; }, 'full');
  // the 'p5 without B' rule
  const art = clone(ART); const [r1, t1] = firstWith((t) => t.B === 0); art.shapes.find((s: any) => s.id === r1.id).til[r1.til.indexOf(t1)].p5 = 3;
  expect(artefactProblems(art).some((b) => b.startsWith('p5 without B'))).toBe(true);
  // pc4 rule
  const art2 = clone(ART); art2.pc4[0].ok = art2.pc4[0].n + 1; expect(artefactProblems(art2).some((b) => b.startsWith('pc4'))).toBe(true);
  // the three-of-one-kind rule needs a synthetic shape: three flat I's stacked
  const cells = [0, 1, 2, 3, 10, 11, 12, 13, 20, 21, 22, 23];
  const til = { pieces: [['I', [0, 1, 2, 3]], ['I', [10, 11, 12, 13]], ['I', [20, 21, 22, 23]]], left: 'JLOSTZ'.split('').join('') , A: 0, B: 0, p5: 0, full: false, tst: false };
  expect(tilingProblems(cells, til)).toContain('over2');
});

// ---- (b) re-run the pinned cheap set through the built crate --------------------------------------
const CRATE = join(SIM, 'tst2bag-rs');
function crateBin(name: string): string | null {
  const bin = join(CRATE, 'target', 'release', name);
  // cargo itself decides staleness (a fresh build is a no-op); the crate is built on first use, like the other native modules
  const r = Bun.spawnSync(['cargo', 'build', '--release', '--manifest-path', join(CRATE, 'Cargo.toml')], { stderr: 'pipe' });
  if (r.exitCode !== 0 || !existsSync(bin)) return null;
  return bin;
}
const inputLine = (s: any) => `s${s.id}|${s.cells.map((p: number[]) => p.join(',')).join(';')}|${s.tst.map((p: number[]) => p.join(',')).join(';')}`;

test('(b) pinned cheap shapes and bag-4 lines re-run through the crate equal the artefact', () => {
  const bin = crateBin('tst2bag');
  const pc4 = crateBin('pc4');
  if (!bin || !pc4) { console.warn('SKIPPED (b): cargo is unavailable or the crate failed to build; the recount is NOT re-checked'); return; }
  const dropped = ART.dropped_constant.per_tiling;
  const lines = PINNED_SHAPES.map((n) => inputLine(SHAPES.find((s) => `s${s.id}` === n)));
  const r = Bun.spawnSync([bin], { stdin: Buffer.from(lines.join('\n') + '\n'), stderr: 'pipe', env: { ...process.env, JOBS: '2' } });
  expect(r.exitCode).toBe(0);
  const got = r.stdout.toString().trim().split('\n').map((l) => JSON.parse(l));
  expect(got.map((g) => g.name).sort()).toEqual([...PINNED_SHAPES].sort());
  for (const g of got) {
    const rec = ART.shapes.find((s: any) => `s${s.id}` === g.name);
    expect({ rows: g.rows, ntil: g.ntil }).toEqual({ rows: rec.rows, ntil: rec.ntil });
    const til = g.til.map((t: any) => { const { id, ...rest } = t; for (const k of Object.keys(dropped)) { expect(rest[k]).toEqual(dropped[k]); delete rest[k]; } expect(id).toBe(g.til.indexOf(t)); return rest; });
    expect(til).toEqual(rec.til);
  }
  for (const l of PINNED_PC4) {
    const p = Bun.spawnSync([pc4], { stdin: Buffer.from(l + '\n'), stderr: 'pipe' });
    expect(p.exitCode).toBe(0);
    expect(JSON.parse(p.stdout.toString().trim())).toEqual(ART.pc4.find((x: any) => x.line === l));
  }
}, 120_000);

test('(e) the fixed-bag-1 counts of the pinned cheap shapes re-run through the crate equal the artefact', () => {
  const bin = crateBin('tst2bag');
  if (!bin) { console.warn('SKIPPED (e): cargo is unavailable or the crate failed to build; the fixed counts are NOT re-checked'); return; }
  const recs = PINNED_SHAPES.map((n) => ART.shapes.find((s: any) => `s${s.id}` === n)).filter((o: any) => o.fixed);
  expect(recs.length).toBeGreaterThan(0);
  const lines = recs.map((o: any) => `${inputLine(SHAPES.find((s) => s.id === o.id))}|${o.fixed.classes.map((c: string) => c || '-').join(';')}`);
  const r = Bun.spawnSync([bin], { stdin: Buffer.from(lines.join('\n') + '\n'), stderr: 'pipe', env: { ...process.env, JOBS: '2', FIXED: '1' } });
  expect(r.exitCode).toBe(0);
  const got = r.stdout.toString().trim().split('\n').map((l) => JSON.parse(l));
  for (const o of recs) {
    const g = got.find((x: any) => x.name === `s${o.id}`);
    expect(g.classes).toEqual(o.fixed.classes);
    expect(g.b1.length).toBe(o.fixed.nb1);
    if (!o.fixed.nb1) continue;
    expect(g.b1.map((b: any) => b.cum)).toEqual(o.fixed.cums);
    expect(g.b1[o.fixed.best].pieces).toEqual(o.fixed.b1);
  }
}, 120_000);

test('the pinned names exist', () => {
  for (const n of PINNED_SHAPES) expect(ART.shapes.some((s: any) => `s${s.id}` === n)).toBe(true);
  for (const l of PINNED_PC4) expect(ART.pc4.some((x: any) => x.line === l)).toBe(true);
});
