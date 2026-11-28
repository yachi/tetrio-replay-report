/**
 * The T-placed bag-1 ranking (`analysis/tst-openers-tp.json`, merged by `pipeline/sim/emit-tst-openers-tp.py` from the
 * Rust counter `pipeline/sim/tst2bag-tp-rs`). CONSTRUCTED and quarantined: nobody played these boards,
 * `report_eligible: false`, no claim id, no badge.
 *
 * The full recount takes about an hour and a half on four cores, so it is never re-run here. What is checked:
 *   (a) the artefact's three md5s (crate sources, the old artefact's bytes, the shapes) are current;
 *   (b) invariants written here in TypeScript, with this file's own mirror function, over every board;
 *   (c) a mutant per invariant, each of which must trip it;
 *   (d) a PINNED set of boards re-run as MULTI lines at soft-drop budgets 0, 1, 2 and unlimited equal `cum`;
 *   (e) two cheap original shapes re-run with TPL+LASTONLY equal `built1` on every board listing them;
 *   (f) the symmetry probe: the mirrors of five cheap shapes re-run in default mode equal `mirror_shapes[].til`;
 *   (g) the HELD boards (six pieces IJLOSZ, the T in hold, names h<i>, after every placed board t<i>): cheap shapes re-run with
 *       FIXED+LASTONLY equal `built1` on every held board listing them, and every held original-shape `built1` is a count the
 *       committed analysis/tst-openers.json holds (its `fixed.cums`), checked without cargo.
 * (d)-(f) build the crate on first use and skip loudly without cargo. Run: bun test pipeline/openers/tst-openers-tp.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..', '..');
const SIM = join(ROOT, 'pipeline', 'sim');
const ART = JSON.parse(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp.json'), 'utf8'));
const OLD_PATH = join(ROOT, 'analysis', 'tst-openers.json');
const OLD = JSON.parse(readFileSync(OLD_PATH, 'utf8'));
const SHAPES: any[] = JSON.parse(readFileSync(join(ROOT, 'pipeline', 'openers', 'tst-openers-shapes.json'), 'utf8')).shapes;
const B1 = JSON.parse(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp-b1.json'), 'utf8'));
const X = JSON.parse(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp-x.json'), 'utf8'));
const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');
const B = 5040, N2 = B * B;
const ORDER = 'IJLOSTZ';
const clone = <T>(x: T): T => JSON.parse(JSON.stringify(x));

/** Boards re-run in (d), pinned by their pieces (names are regenerated on every emit). Cheap: one or two shapes each. */
const PINNED_BOARDS = [
  'I:9,19,29,39/J:0,1,2,10/L:7,8,17,27/O:35,36,45,46/T:6,15,16,26/Z:4,5,13,14',
  'I:9,19,29,39/J:0,1,2,10/O:48,49,58,59/S:11,20,21,30/T:8,17,18,28/Z:6,7,15,16',
  'I:7,17,27,37/J:0,1,2,10/L:8,9,18,28/O:35,36,45,46/T:6,15,16,26/Z:4,5,13,14',
  'I:9,19,29,39/J:0,1,2,10/L:3,4,13,23/O:48,49,58,59/S:11,20,21,30/T:8,17,18,28',
  'I:0,10,20,30/J:5,6,16,26/L:7,8,9,19/O:40,41,50,51/S:2,3,13,14/T:1,11,12,21',
  'I:0,10,20,30/J:5,6,16,26/L:7,8,9,19/S:2,3,13,14/T:1,11,12,21/Z:18,28,29,39',
];
/** HELD boards (six pieces, the T in hold) re-run in (d) too: the Honey Cup board (shapes 0 and 1) and a one-shape board. */
const PINNED_HELD = [
  'I:1,11,21,31/J:28,29,39,49/L:2,3,12,22/O:8,9,18,19/S:32,41,42,51/Z:5,6,14,15',
  'I:0,10,20,30/J:5,6,16,26/L:7,8,9,19/O:40,41,50,51/S:2,3,13,14/Z:18,28,29,39',
];
/** Original shapes re-run in (g) with FIXED+LASTONLY (no TPL): their held boards' built1. */
const PINNED_G = [0, 1, 107];
/** Original shapes re-run in (e) and whose mirrors are re-run in (f). */
const PINNED_E = [98, 81];
const PINNED_F = [98, 81, 46, 47, 119];

// ---- helpers (this file's own mirror and tiling arithmetic) ----------------------------------------------------------
const SW: Record<string, string> = { J: 'L', L: 'J', S: 'Z', Z: 'S' };
const mk = (k: string) => SW[k] ?? k;
const mc = (c: number) => Math.floor(c / 10) * 10 + 9 - (c % 10);
type Pc = [string, number[]];
const sortPcs = (ps: Pc[]): Pc[] => ps.map(([k, cs]) => [k, [...cs].sort((a, b) => a - b)] as Pc).sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1].join() < b[1].join() ? -1 : a[1].join() > b[1].join() ? 1 : 0));
const mirrorPcs = (ps: Pc[]): Pc[] => sortPcs(ps.map(([k, cs]) => [mk(k), cs.map(mc)] as Pc));
const keyOf = (ps: Pc[]) => sortPcs(ps).map(([k, cs]) => `${k}:${cs.join(',')}`).join('/');
/** Python's json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False) for the ints, strings, lists, objects
 * and booleans the artefacts hold (no floats). */
const canonJson = (x: any): string => Array.isArray(x) ? `[${x.map(canonJson).join(',')}]`
  : x !== null && typeof x === 'object' ? `{${Object.keys(x).sort().map((k) => `${JSON.stringify(k)}:${canonJson(x[k])}`).join(',')}}`
  : JSON.stringify(x);
const pieceKeys = (ps: Pc[]) => new Set(ps.map(([k, cs]) => `${k}:${[...cs].sort((a, b) => a - b).join(',')}`));
const sortLeft = (l: string) => [...l].sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b)).join('');
const leftOf = (ps: Pc[]) => [...ORDER].map((k) => k.repeat(Math.max(0, 2 - ps.filter((p) => p[0] === k).length - (k === 'T' ? 1 : 0)))).join('');
const pts = (ps: number[][]) => ps.map((p) => p.join(',')).join(';');
const idxs = (ps: number[][]) => ps.map(([x, y]) => y * 10 + x).sort((a, b) => a - b);
const shapeKey = (s: { cells: number[][]; tst: number[][] }) => JSON.stringify([idxs(s.cells), idxs(s.tst)]);

interface Til { pieces: Pc[]; left: string; A: number; B: number; p5: number }
interface Cat { id: number; cells: number[][]; tst: number[][]; til: Til[]; classes: Map<string, number> }

/** The 246-shape catalogue: the 127 transcribed shapes (tilings from the old artefact) and the mirrors of those whose mirror is absent. */
function catalogue(art: any): Map<number, Cat> {
  const by = new Map<number, Cat>();
  const add = (id: number, cells: number[][], tst: number[][], til: Til[]) => {
    const classes = new Map<string, number>();
    for (const t of til) if (t.B > 0) classes.set(t.left, t.p5);
    by.set(id, { id, cells, tst, til, classes });
  };
  const oldBy = new Map<number, any>(OLD.shapes.map((o: any) => [o.id, o]));
  for (const s of SHAPES) add(s.id, s.cells, s.tst, oldBy.get(s.id).til.map((t: any) => ({ pieces: t.pieces, left: t.left, A: t.A, B: t.B, p5: t.p5 })));
  const have = new Set(SHAPES.map(shapeKey));
  for (const ms of art.mirror_shapes) {
    const s = SHAPES.find((x) => x.id === ms.mirror_of)!;
    const cells = s.cells.map(([x, y]: number[]) => [9 - x, y]).sort((a: number[], b: number[]) => a[0] - b[0] || a[1] - b[1]);
    const tst = s.tst.map(([x, y]: number[]) => [9 - x, y]).sort((a: number[], b: number[]) => a[0] - b[0] || a[1] - b[1]);
    const o = oldBy.get(ms.mirror_of);
    add(ms.id, cells, tst, o.til.map((t: any, i: number) => ({ pieces: mirrorPcs(t.pieces), left: sortLeft([...t.left].map(mk).join('')), A: ms.til[i][0], B: ms.til[i][1], p5: ms.til[i][2] })));
    have.add(shapeKey({ cells, tst }));
  }
  return by;
}
const holds = (t: Til, board: Pc[]) => { const ks = pieceKeys(t.pieces); return board.every(([k, cs]) => ks.has(`${k}:${[...cs].sort((a, b) => a - b).join(',')}`)); };
const classesOf = (ids: number[], cat: Map<number, Cat>): [number, string, number][] => {
  const out: [number, string, number][] = [];
  ids.forEach((sid, si) => cat.get(sid)!.classes.forEach((p5, l) => out.push([si, l, p5])));
  return out.sort((a, b) => b[2] - a[2] || a[0] - b[0] || (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
};
/** ub > 9/25, exactly: min(min(N2, sum b) * maxP, sum b_i * maxp5_i) / (N2 * 5040). */
function ubExceeds(ids: number[], built1: number[], cat: Map<number, Cat>): boolean {
  const mp = ids.map((id) => Math.max(0, ...cat.get(id)!.classes.values()));
  const sum = built1.reduce((a, b) => a + b, 0);
  const maxP = Math.max(...mp);
  const a = BigInt(Math.min(N2, sum)) * BigInt(maxP);
  const b = built1.reduce((s, x, i) => s + BigInt(x) * BigInt(mp[i]!), 0n);
  const num = a < b ? a : b;
  return num * 25n > 9n * BigInt(N2) * BigInt(B);
}

// ---- (a) hashes --------------------------------------------------------------------------------------------------
function canon(x: any): string {
  if (Array.isArray(x)) return '[' + x.map(canon).join(',') + ']';
  if (x && typeof x === 'object') return '{' + Object.keys(x).sort().map((k) => JSON.stringify(k) + ':' + canon(x[k])).join(',') + '}';
  return JSON.stringify(x);
}
function crateMd5(): string {
  const files = ['tst2bag-tp-rs/Cargo.toml'];
  for (const c of ['tst2bag-tp-rs', 'oracle-rs', 'pc-solver-rs'])
    for (const f of readdirSync(join(SIM, c, 'src'), { recursive: true }) as string[]) if (f.endsWith('.rs')) files.push(`${c}/src/${f}`);
  files.sort();
  const h = createHash('md5');
  for (const f of files) h.update(`${f}\0${md5(readFileSync(join(SIM, f)))}\n`);
  return h.digest('hex');
}
test('(a) the three md5s are current and the artefact is quarantined', () => {
  expect(ART.md5.crate).toBe(crateMd5());
  expect(ART.md5.tst_openers).toBe(md5(readFileSync(OLD_PATH)));
  expect(ART.md5.shapes).toBe(md5(canon(SHAPES)));
  expect(ART.report_eligible).toBe(false);
  expect(ART.constructed).toBe(true);
  expect(ART.schema).toBe('tst-openers-tp/5');
  expect(ART.md5.b1).toBe(md5(canon(B1)));
});

// ---- (b) invariants ----------------------------------------------------------------------------------------------
const KINDS = 'IJLOSZ';
function problems(art: any, only?: number[]): string[] {
  const bad: string[] = [];
  const cat = catalogue(art);
  // mirror_shapes cover exactly the shapes whose mirror is absent
  const have = new Set(SHAPES.map(shapeKey));
  const want = new Map<number, number>();
  const seenMirror = new Set<string>();
  for (const s of SHAPES) {
    const m = { cells: s.cells.map(([x, y]: number[]) => [9 - x, y]), tst: s.tst.map(([x, y]: number[]) => [9 - x, y]) };
    const k = shapeKey(m);
    if (have.has(k) || seenMirror.has(k)) continue;
    seenMirror.add(k);
    want.set(1000 + s.id, s.id);
  }
  const got = new Map<number, number>(art.mirror_shapes.map((m: any) => [m.id, m.mirror_of]));
  if (JSON.stringify([...want].sort()) !== JSON.stringify([...got].sort()) || got.size !== art.mirror_shapes.length) bad.push('mirror_shapes');
  if (art.mirror_shapes.some((m: any) => !Array.isArray(m.til) || m.til.length !== OLD.shapes.find((o: any) => o.id === m.mirror_of)?.til.length)) bad.push('mirror_shapes til');
  if (art.prune.kept !== art.boards.length) bad.push('prune kept');
  // prune.kinds: placed boards first, then held; kept counts equal what the list holds, totals add up
  const nPlaced = art.boards.filter((b: any) => b.held !== 'T').length;
  const nHeld = art.boards.length - nPlaced;
  const pk = art.prune.kinds;
  if (!pk || pk.placed?.[1] !== nPlaced || pk.held?.[1] !== nHeld) bad.push('prune kinds kept');
  if (!pk || art.prune.boards_total !== pk.placed[0] + pk.held[0] || art.prune.kept !== pk.placed[1] + pk.held[1]) bad.push('prune kinds total');
  if (!pk || pk.placed[1] > pk.placed[0] || pk.held[1] > pk.held[0]) bad.push('prune kinds order');
  if (art.boards.slice(0, nPlaced).some((b: any) => b.held === 'T') || art.boards.slice(nPlaced).some((b: any) => b.held !== 'T')) bad.push('kind order');
  const keys = new Map<string, any>();
  art.boards.forEach((b: any) => keys.set(keyOf(b.pieces), b));
  art.boards.forEach((b: any, i: number) => {
    if (only && !only.includes(i)) return;
    const tag = (t: string) => bad.push(`${t} ${b.name}`);
    const isHeld = b.held === 'T';
    if (b.name !== (isHeld ? `h${i - nPlaced}` : `t${i}`)) tag('name');
    // six disjoint tetrominoes of the declared kinds, exactly one T, held is the missing kind
    const pcs: Pc[] = b.pieces;
    const kinds = pcs.map((p) => p[0]).sort().join('');
    const held = b.held;
    if (isHeld) { if (kinds !== [...KINDS].sort().join('')) tag('kinds'); }
    else if (!KINDS.includes(held) || kinds !== [...'T' + KINDS.replace(held, '')].sort().join('')) tag('kinds');
    const cells = pcs.flatMap((p) => p[1]);
    if (cells.length !== 24 || new Set(cells).size !== 24 || cells.some((c: number) => c < 0 || c >= 120)) tag('cells');
    for (const [k, cs] of pcs) if (cs.length !== 4 || !cs.every((c) => c % 10 < 10)) tag('piece');
    // every listed shape has a tiling holding the board, ntil counts them, classes are exactly the B>0 set in order
    let ntil = 0;
    if (!b.shapes.every((id: number) => cat.has(id))) { tag('shape id'); return; }
    if (new Set(b.shapes).size !== b.shapes.length) tag('shape dup');
    for (const id of b.shapes) {
      const n = cat.get(id)!.til.filter((t) => holds(t, pcs)).length;
      if (n === 0) tag('shape no tiling');
      ntil += n;
    }
    if (b.ntil !== ntil) tag('ntil');
    // classes: every (shape, leftover, p5) over the listed shapes' tilings with B > 0 (not only those holding the board), ranked
    const exp = classesOf(b.shapes, cat);
    const gotc: [number, string, number][] = b.classes.map((c: any) => [c[0], c[1], c[2]]);
    if (JSON.stringify([...gotc].sort()) !== JSON.stringify([...exp].sort())) tag('classes');
    else if (!art.mirror.assumed && JSON.stringify(gotc) !== JSON.stringify(exp)) tag('classes order');
    // cum: lengths, non-decreasing, at most N2, monotone across budgets
    let prev: number[] | null = null;
    for (const bk of ['0', '1', '2', 'inf']) {
      const c: number[] = b.cum[bk];
      if (c.length !== b.classes.length || c.some((x, j) => j > 0 && x < c[j - 1]!) || c.some((x) => x < 0 || x > N2)) tag('cum');
      if (prev && prev.some((x, j) => x > c[j]!)) tag('budgets');
      prev = c;
    }
    const inf = b.cum.inf;
    const sum = b.built1.reduce((a: number, x: number) => a + x, 0);
    if (b.built1.length !== b.shapes.length || !(Math.max(...b.built1) <= inf[inf.length - 1] && inf[inf.length - 1] <= sum)) tag('built1');
    // a held board is kept if its own or its mirror's bound exceeds the threshold; a placed board by its own
    const ownUb = ubExceeds(b.shapes, b.built1, cat);
    const mb = isHeld && b.mirror ? art.boards.find((x: any) => x.name === b.mirror) : null;
    if (!ownUb && !(mb && mb.shapes.every((id: number) => cat.has(id)) && ubExceeds(mb.shapes, mb.built1, cat))) tag('ub');
  });
  if (keys.size !== art.boards.length) bad.push('duplicate board');
  // mirror: an involution onto the mirrored pieces
  art.boards.forEach((b: any) => {
    const mk2 = keyOf(mirrorPcs(b.pieces));
    const other = keys.get(mk2);
    if ((other?.name ?? null) !== (b.mirror ?? null)) bad.push(`mirror ${b.name}`);
    if (other && other.mirror !== b.name) bad.push(`mirror involution ${b.name}`);
  });
  return bad;
}

test('(b) invariants hold over every board', () => {
  expect(problems(ART)).toEqual([]);
  expect(ART.boards.length).toBeGreaterThan(0);
  expect(ART.boards.length).toBe(ART.prune.kept);
}, 60_000);

// ---- (c) mutants -------------------------------------------------------------------------------------------------
test('(c) each invariant has a mutant that fires', () => {
  // per-board checks run on a few boards only (the mutants touch the first board and one mirror pair); the whole-artefact checks always run
  const mi = ART.boards.findIndex((b: any) => b.mirror !== null);
  const SUBSET = [0, 1, mi];
  const fires = (f: (a: any) => void, tag: string) => {
    const a = clone(ART);
    f(a);
    expect(problems(a, SUBSET).some((p) => p.startsWith(tag))).toBe(true);
  };
  const first = (a: any) => a.boards[0];
  const withMirror = (a: any) => a.boards.find((b: any) => b.mirror !== null);
  const hi = ART.boards.findIndex((b: any) => b.held === 'T');
  const firstHeld = (a: any) => a.boards.find((b: any) => b.held === 'T');
  const SUB_H = hi >= 0 ? [...SUBSET, hi] : SUBSET;
  const firesH = (f: (a: any) => void, tag: string) => {
    if (hi < 0) return;
    const a = clone(ART);
    f(a);
    expect(problems(a, SUB_H).some((p) => p.startsWith(tag))).toBe(true);
  };
  fires((a) => { first(a).name = 'tX'; }, 'name');
  firesH((a) => { firstHeld(a).name = 'h999'; }, 'name');
  firesH((a) => { firstHeld(a).held = 'I'; }, 'kinds');
  firesH((a) => { firstHeld(a).pieces[0][0] = 'T'; }, 'kinds');
  firesH((a) => { firstHeld(a).built1 = firstHeld(a).built1.map(() => 0); const m = a.boards.find((x: any) => x.name === firstHeld(a).mirror); if (m) m.built1 = m.built1.map(() => 0); }, 'ub');
  firesH((a) => { a.prune.kinds.held[1] += 1; }, 'prune kinds kept');
  firesH((a) => { a.prune.kinds.placed[0] += 1; }, 'prune kinds total');
  firesH((a) => { a.prune.kinds.held[0] = a.prune.kinds.held[1] - 1; a.prune.boards_total = a.prune.kinds.placed[0] + a.prune.kinds.held[0]; }, 'prune kinds order');
  firesH((a) => { const h = a.boards.findIndex((b: any) => b.held === 'T'); [a.boards[0], a.boards[h]] = [a.boards[h], a.boards[0]]; }, 'kind order');
  fires((a) => { first(a).held = first(a).held === 'I' ? 'J' : 'I'; }, 'kinds');
  fires((a) => { first(a).pieces[0][1][0] = first(a).pieces[1][1][0]; }, 'cells');
  fires((a) => { first(a).pieces[0][1].pop(); }, 'piece');
  fires((a) => { first(a).shapes.push(first(a).shapes[0]); }, 'shape dup');
  fires((a) => { first(a).ntil += 1; }, 'ntil');
  fires((a) => { first(a).classes.pop(); for (const k of ['0', '1', '2', 'inf']) first(a).cum[k].pop(); }, 'classes');
  fires((a) => { first(a).classes[0][2] += 1; }, 'classes');
  if (!ART.mirror.assumed) fires((a) => { const c = first(a).classes; [c[0], c[1]] = [c[1], c[0]]; }, 'classes order');
  fires((a) => { first(a).cum.inf[0] = N2 + 1; }, 'cum');
  fires((a) => { const c = first(a).cum.inf; c[1] = c[c.length - 1] + 1; }, 'cum');
  fires((a) => { first(a).cum['0'] = first(a).cum.inf.map((x: number) => x + 1); }, 'budgets');
  fires((a) => { first(a).built1[0] = first(a).cum.inf[first(a).cum.inf.length - 1] + 1; }, 'built1');
  fires((a) => { first(a).built1 = first(a).built1.map(() => 1); }, 'built1');
  fires((a) => { first(a).built1 = first(a).built1.map(() => 0); }, 'ub');
  fires((a) => { withMirror(a).mirror = null; }, 'mirror');
  fires((a) => { const b = withMirror(a); const o = a.boards.find((x: any) => x.name !== b.name && x.name !== b.mirror); b.mirror = o.name; }, 'mirror');
  fires((a) => { a.mirror_shapes.pop(); }, 'mirror_shapes');
  fires((a) => { a.prune.kept += 1; }, 'prune kept');
  fires((a) => { a.boards.push(clone(a.boards[0])); }, 'duplicate board');
}, 120_000);

// ---- the crate ----------------------------------------------------------------------------------------------------
const CRATE = join(SIM, 'tst2bag-tp-rs');
let CRATE_BIN: string | null | undefined;   // built once (synchronously, before any test awaits), shared by every test
function crateBin(): string | null {
  if (CRATE_BIN !== undefined) return CRATE_BIN;
  const bin = join(CRATE, 'target', 'release', 'tst2bag-tp');
  const r = Bun.spawnSync(['cargo', 'build', '--release', '--manifest-path', join(CRATE, 'Cargo.toml')], { stderr: 'pipe' });
  return (CRATE_BIN = r.exitCode === 0 && existsSync(bin) ? bin : null);
}
/** Runs the binary asynchronously, so the tests that call it can run concurrently (each is a separate Rust process). */
const spawnLines = async (bin: string, input: string, env: Record<string, string>) => {
  const pr = Bun.spawn([bin], { stdin: Buffer.from(input), stdout: 'pipe', stderr: 'pipe', env: { ...process.env, ...env } });
  const [out, , code] = await Promise.all([new Response(pr.stdout).text(), new Response(pr.stderr).text(), pr.exited]);
  expect(code).toBe(0);
  return out;
};
const run = async (bin: string, lines: string[], env: Record<string, string>) =>
  (await spawnLines(bin, lines.join('\n') + '\n', { JOBS: '2', ...env })).trim().split('\n').map((l) => JSON.parse(l));
const CAT = catalogue(ART);

test.concurrent('(d) pinned boards re-run as MULTI lines equal cum at every soft-drop budget', async () => {
  const bin = crateBin();
  if (!bin) { console.warn('SKIPPED (d): cargo is unavailable or the crate failed to build; the recount is NOT re-checked'); return; }
  const boards = [...PINNED_BOARDS, ...PINNED_HELD].map((k) => ART.boards.find((b: any) => keyOf(b.pieces) === k));
  expect(boards.every((b: any) => b)).toBe(true);
  expect(boards.filter((b: any) => b.held === 'T').length).toBe(PINNED_HELD.length);
  const lines = boards.map((b: any, i: number) => {
    const b1 = [...b.pieces].map(([k, cs]: Pc) => `${k}:${cs.join(',')}`).join('/');
    const sh = b.shapes.map((id: number) => `${pts(CAT.get(id)!.cells)}|${pts(CAT.get(id)!.tst)}`).join('#');
    const cl = b.classes.map(([si, l]: [number, string]) => `${si}:${l || '-'}`).join(';');
    return `p${i}#${b1}#${sh}#${cl}`;
  });
  const runs = ([['0', { SDB: '0' }], ['1', { SDB: '1' }], ['2', { SDB: '2' }], ['inf', {}]] as [string, Record<string, string>][])
    .map(([bk, env]) => run(bin, lines, { MULTI: '1', ...env }).then((got) => [bk, got] as [string, any[]]));
  for (const [bk, got] of await Promise.all(runs)) {
    boards.forEach((b: any, i: number) => {
      const g = got.find((x: any) => x.name === `p${i}`);
      expect({ ntil: g.ntil, cum: g.cum }).toEqual({ ntil: b.ntil, cum: b.cum[bk] });
    });
  }
}, 300_000);

test.concurrent('(e) TPL+LASTONLY of two cheap original shapes equals built1 on every board listing them', async () => {
  const bin = crateBin();
  if (!bin) { console.warn('SKIPPED (e): cargo is unavailable or the crate failed to build; built1 is NOT re-checked'); return; }
  const lines = PINNED_E.map((id) => {
    const c = CAT.get(id)!;
    const cl = [...c.classes].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1)).map(([l]) => l || '-');
    return `s${id}|${pts(c.cells)}|${pts(c.tst)}|${cl.join(';')}`;
  });
  const got = await run(bin, lines, { FIXED: '1', TPL: '1', LASTONLY: '1' });
  let checked = 0;
  for (const id of PINNED_E) {
    const g = got.find((x: any) => x.name === `s${id}`);
    const by = new Map<string, number>(g.b1.map((b: any) => [keyOf(b.pieces), b.cum[b.cum.length - 1]]));
    for (const b of ART.boards.filter((x: any) => x.held !== 'T')) {
      const j = b.shapes.indexOf(id);
      if (j < 0) continue;
      expect(by.get(keyOf(b.pieces))).toBe(b.built1[j]);
      checked++;
    }
  }
  expect(checked).toBeGreaterThan(0);
}, 300_000);

test.concurrent('(g) held boards: FIXED+LASTONLY of cheap shapes equals built1, and every held built1 is a count tst-openers.json holds', async () => {
  const held = ART.boards.filter((b: any) => b.held === 'T');
  expect(held.length).toBeGreaterThan(0);
  // cargo-free: a held board of an original shape is one of that shape's FIXED boards, whose last cum is built1
  const lasts = new Map<number, Set<number>>(OLD.shapes.map((o: any) => [o.id, new Set<number>((o.fixed?.cums ?? []).map((c: number[]) => c[c.length - 1]))]));
  let seen = 0;
  for (const b of held) b.shapes.forEach((id: number, j: number) => {
    if (id >= 1000) return;
    expect(lasts.get(id)!.has(b.built1[j])).toBe(true);
    seen++;
  });
  expect(seen).toBeGreaterThan(0);
  const bin = crateBin();
  if (!bin) { console.warn('SKIPPED (g, re-run half): cargo is unavailable or the crate failed to build; held built1 is NOT re-run'); return; }
  const lines = PINNED_G.map((id) => {
    const c = CAT.get(id)!;
    const cl = [...c.classes].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1)).map(([l]) => l || '-');
    return `s${id}|${pts(c.cells)}|${pts(c.tst)}|${cl.join(';')}`;
  });
  const got = await run(bin, lines, { FIXED: '1', LASTONLY: '1' });
  let checked = 0;
  for (const id of PINNED_G) {
    const g = got.find((x: any) => x.name === `s${id}`);
    const by = new Map<string, number>(g.b1.map((b: any) => [keyOf(b.pieces), b.cum[b.cum.length - 1]]));
    for (const b of held) {
      const j = b.shapes.indexOf(id);
      if (j < 0) continue;
      expect(by.get(keyOf(b.pieces))).toBe(b.built1[j]);
      checked++;
    }
  }
  expect(checked).toBeGreaterThan(0);
}, 300_000);

test.concurrent('(f) symmetry probe: the mirrors of five cheap shapes re-run in default mode equal mirror_shapes', async () => {
  const bin = crateBin();
  if (!bin) { console.warn('SKIPPED (f): cargo is unavailable or the crate failed to build; the mirrors are NOT re-checked'); return; }
  const recs = PINNED_F.map((id) => ART.mirror_shapes.find((m: any) => m.mirror_of === id)).filter((m: any) => m);
  expect(recs.length).toBeGreaterThan(0);
  const lines = recs.map((m: any) => { const c = CAT.get(m.id)!; return `s${m.id}|${pts(c.cells)}|${pts(c.tst)}`; });
  const got = await run(bin, lines, {});
  for (const m of recs) {
    const g = got.find((x: any) => x.name === `s${m.id}`);
    const c = CAT.get(m.id)!;
    const by = new Map<string, any>(g.til.map((t: any) => [[...pieceKeys(t.pieces)].sort().join('|'), t]));
    expect(g.til.length).toBe(c.til.length);
    c.til.forEach((t, i) => {
      const r = by.get([...pieceKeys(t.pieces)].sort().join('|'));
      expect(r).toBeTruthy();
      expect([r.A, r.B, r.p5]).toEqual(m.til[i]);
      expect(r.left).toBe(t.left);
    });
  }
}, 300_000);

test('the pinned boards exist', () => {
  for (const k of PINNED_BOARDS) expect(ART.boards.some((b: any) => keyOf(b.pieces) === k)).toBe(true);
  for (const k of PINNED_HELD) expect(ART.boards.some((b: any) => b.held === 'T' && keyOf(b.pieces) === k)).toBe(true);
  for (const id of PINNED_F) expect(OLD.shapes.some((o: any) => o.id === id)).toBe(true);
});

// ---- (h) the hold-swap families: the first-bag vectors and the policy, recomputed in TypeScript -------------------------
// The identity cum_b[k] = sum_s n_s D_k(b - s) (n_s = first-bag orders of cost s) is solved for D with every division
// asserted exact; the family figures are then recomputed from D and the vectors with this file's own code, and the
// layouts are re-derived with a second implementation of "the kept boards equal to a 7-placement layout less one piece".
import { inflateSync } from 'node:zlib';
const INFEAS = 10;
const BKEYS = ['0', '1', '2', 'inf'];
/** one board's first-bag cost vector: the inflated string, '.' (infeasible) -> INFEAS, else the digit. */
const vecU8 = (name: string, into?: Uint8Array): Uint8Array => {
  const s = inflateSync(Buffer.from(B1.vectors[name] ?? X.vectors[name], 'base64'));
  expect(s.length).toBe(B);
  const o = into ?? new Uint8Array(B);
  for (let i = 0; i < B; i++) { const c = s[i]!; o[i] = c === 46 ? INFEAS : c - 48; }
  return o;
};
const vecOf = (name: string): number[] => Array.from(vecU8(name));
function tables(b: any, v: Uint8Array) {
  const n = new Array(INFEAS + 1).fill(0);
  for (const x of v) n[x]++;
  const nfeas = B - n[INFEAS];
  const ncls = b.cum.inf.length;
  if (nfeas === 0) {   // no first-bag order builds it: every count is zero, and so is every table
    for (const bk of BKEYS) expect(b.cum[bk].every((x: number) => x === 0)).toBe(true);
    const z = () => new Array(INFEAS + 1).fill(0);
    return { out: Object.fromEntries(BKEYS.map((bk) => [bk, [z(), z()]])), n };
  }
  const Dinf = b.cum.inf.map((c: number) => { expect(c % nfeas).toBe(0); return c / nfeas; });
  const smin = n.findIndex((x: number, s: number) => s < INFEAS && x > 0);
  const Dfin: Record<number, number[]> = {};
  for (const bud of [0, 1, 2]) {
    const c = b.cum[String(bud)];
    if (bud < smin) { expect(c.every((x: number) => x === 0)).toBe(true); continue; }
    const row: number[] = [];
    for (let k = 0; k < ncls; k++) {
      let num = c[k];
      for (let s = smin + 1; s <= bud; s++) num -= n[s] * Dfin[bud - s][k];
      expect(num % n[smin]).toBe(0);
      row.push(num / n[smin]);
    }
    Dfin[bud - smin] = row;
  }
  const p5 = b.classes.map((c: any) => c[2]);
  const jb = (row: number[]): [number, number] => { let prev = 0, j = 0; row.forEach((d, i) => { j += (d - prev) * p5[i]; prev = d; }); return [j, row[row.length - 1]]; };
  const out: Record<string, [number[], number[]]> = {};
  for (const bk of BKEYS) {
    const J = new Array(INFEAS + 1).fill(0), Bt = new Array(INFEAS + 1).fill(0);
    for (let s = 0; s < INFEAS; s++) {
      const r = bk === 'inf' ? null : Number(bk) - s;
      const row = bk === 'inf' ? Dinf : r! >= 0 ? Dfin[r!] : undefined;
      if (row) [J[s], Bt[s]] = jb(row);
    }
    out[bk] = [J, Bt];
  }
  return { out, n };
}
const bkey = (ps: Pc[]) => keyOf(ps);
test('(h) every family figure is recomputed from the boards and the first-bag vectors', () => {
  const F = ART.families;
  expect(F.complete).toBe(true);
  // the kept boards and the extra ones (the variants the pruning dropped, analysis/tst-openers-tp-x.json)
  expect(X.schema).toBe('tst-openers-tp-x/1');
  expect(ART.md5.x).toBe(md5(canonJson(X)));
  const ALL: any[] = [...ART.boards, ...X.boards];
  const kept = new Set<string>(ART.boards.map((b: any) => b.name));
  const byName = new Map<string, any>(ALL.map((b: any) => [b.name, b]));
  // the vectors and tables are the module-level VEC / STAT over POOL (the same boards in the same order),
  // computed once for this test and (j) rather than twice
  expect(POOL.map((b: any) => b.name)).toEqual(ALL.map((b: any) => b.name));
  const vec = new Map<string, Uint8Array>(), tab = new Map<string, any>();
  for (const [i, b] of ALL.entries()) {
    const v = VEC[i]!; vec.set(b.name, v);
    const t = STAT[i]; tab.set(b.name, t.out);
    for (const bk of BKEYS) {   // a one-board family reproduces the board's own figures
      let bsum = 0, jsum = 0;
      const Jo = t.out[bk][0], Bo = t.out[bk][1];
      for (let o = 0; o < B; o++) { const x = v[o]!; bsum += Bo[x]; jsum += Jo[x]; }
      expect(bsum).toBe(b.cum[bk][b.cum[bk].length - 1]);
      let n = 0, prev = 0;
      b.cum[bk].forEach((c: number, i: number) => { n += (c - prev) * b.classes[i][2]; prev = c; });
      expect(jsum).toBe(n);
    }
  }
  // layouts, second implementation: group by (layout less one piece), then every pair that completes a layout
  const keptKeys = new Set<string>(ART.boards.map((b: any) => keyOf(b.pieces)));
  const lay = new Map<string, Set<string>>();
  const cores = new Map<string, { name: string; p: Pc }[]>();
  for (const b of ALL) b.pieces.forEach((p: Pc, j: number) => {
    const rest = sortPcs(b.pieces.filter((_: Pc, i: number) => i !== j));
    const k = bkey(rest);
    (cores.get(k) ?? cores.set(k, []).get(k)!).push({ name: b.name, p: sortPcs([p])[0] });
  });
  for (const [k, lst] of cores) for (let a = 0; a < lst.length; a++) for (let c = a + 1; c < lst.length; c++) {
    if (lst[a].p[0] === lst[c].p[0]) continue;
    const base = k.split('/').map((t) => { const [kk, cs] = t.split(':'); return [kk, cs.split(',').map(Number)] as Pc; });
    const all = sortPcs([...base, lst[a].p, lst[c].p]);
    if (new Set(all.flatMap(([, cs]) => cs)).size !== 28) continue;
    // a layout counts only if some variant of it (the layout less one piece) is a kept board
    if (!all.some((_, i) => keptKeys.has(bkey(all.filter((_2, j) => j !== i))))) continue;
    (lay.get(bkey(all)) ?? lay.set(bkey(all), new Set()).get(bkey(all))!);
  }
  const byKey = new Map<string, string>(ALL.map((b: any) => [keyOf(b.pieces), b.name]));
  const idxOf = new Map<string, number>(ALL.map((b: any, i: number) => [b.name, i] as [string, number]));
  const check = (names: string[], num: any, pk: any) => {
    const ids = names.map((n) => idxOf.get(n)!);
    for (const bk of BKEYS) {
      let bn = 0, pn = 0;
      const pick = names.map(() => 0);
      const T = keysOf(bk);
      for (let o = 0; o < B; o++) {
        let best = -1, arg = -1, ax = 0;
        for (let t = 0; t < ids.length; t++) {
          const ix = ids[t]! * W11 + V[ids[t]! * B + o]!;
          const key = T.KT[ix]!;      // -1 when the cost exceeds the budget
          if (key > best) { best = key; arg = t; ax = ix; }
        }
        if (arg < 0) continue;
        bn += T.BT[ax]!; pn += T.JT[ax]!; pick[arg]++;
      }
      expect([bn, pn]).toEqual(num[bk]);
      expect(pick).toEqual(pk[bk]);
    }
  };
  expect(lay.size).toBe(F.list.length);
  const listed = new Set(F.list.map((L: any) => bkey(L.pieces)));
  for (const k of lay.keys()) expect(listed.has(k)).toBe(true);
  const order = new Map<string, number>(ALL.map((b: any, i: number) => [b.name, i]));
  // boards by their set of six pieces (a board's pieces are distinct), to find the boards equal to a layout less one piece
  const bySet = new Map<string, string[]>();
  for (const b of ALL) { const ks = pieceKeys(b.pieces); if (ks.size === 6) { const k = [...ks].sort().join('/'); (bySet.get(k) ?? bySet.set(k, []).get(k)!).push(b.name); } }
  for (const L of F.list) {
    const names: string[] = L.variants;
    expect(names.length).toBeGreaterThanOrEqual(2);
    // each variant is the layout less one piece, and every kept such board is listed
    const want = new Set<string>();
    const all = pieceKeys(L.pieces);
    expect(all.size).toBeLessThanOrEqual(7);
    const alls = [...all];
    // the six-piece subsets of the layout: itself when it has six pieces, each drop-one when it has seven
    const subsets = all.size === 6 ? [alls] : alls.map((_, d) => alls.filter((_2, q) => q !== d));
    if (all.size >= 6) for (const sub of subsets) for (const n of bySet.get([...sub].sort().join('/')) ?? []) want.add(n);
    expect(names.some((n) => kept.has(n))).toBe(true);
    expect(new Set(names)).toEqual(want);
    check(names, L.num, L.pick);
    // `both`: the variants and every variant's mirror board (independently, by mirroring each variant's pieces)
    const both = new Set(names);
    for (const n of names) both.add(byKey.get(keyOf(mirrorPcs(byName.get(n).pieces)))!);
    expect(L.both.variants).toEqual([...both].sort((a, b) => order.get(a)! - order.get(b)!));
    check(L.both.variants, L.both.num, L.both.pick);
    for (const bk of BKEYS) expect(L.both.num[bk][1]).toBeGreaterThanOrEqual(L.num[bk][1]);
  }
  // `pairs`: every board with its mirror board, once
  expect(F.pairs.length * 2).toBe(ART.boards.length);
  const seen = new Set<string>();
  for (const P of F.pairs) {
    const [a, m] = P.boards;
    expect(byKey.get(keyOf(mirrorPcs(byName.get(a).pieces)))).toBe(m);
    seen.add(a); seen.add(m);
    check(P.boards, P.num, P.pick);
  }
  expect(seen.size).toBe(ART.boards.length);
}, 300_000);

test.concurrent('(i) cross-crate: the pinned counter with B1ONLY counts 5040 x the orders each vector says build the board', async () => {
  const bin = crateBin();
  if (!bin) { console.warn('SKIPPED (i): cargo is unavailable or the crate failed to build; the b1 vectors are NOT re-checked'); return; }
  const boards = [...PINNED_BOARDS, ...PINNED_HELD].map((k) => ART.boards.find((b: any) => keyOf(b.pieces) === k));
  const lines = boards.map((b: any, i: number) => {
    const b1 = [...b.pieces].map(([k, cs]: Pc) => `${k}:${cs.join(',')}`).join('/');
    const sh = b.shapes.map((id: number) => `${pts(CAT.get(id)!.cells)}|${pts(CAT.get(id)!.tst)}`).join('#');
    const cl = b.classes.map(([si, l]: [number, string]) => `${si}:${l || '-'}`).join(';');
    return `p${i}#${b1}#${sh}#${cl}`;
  });
  const runs = ([[0, { SDB: '0' }], [1, { SDB: '1' }], [2, { SDB: '2' }], [INFEAS, {}]] as [number, Record<string, string>][])
    .map(([n, env]) => run(bin, lines, { MULTI: '1', B1ONLY: '1', ...env }).then((got) => [n, got] as [number, any[]]));
  for (const [n, got] of await Promise.all(runs)) {
    boards.forEach((b: any, i: number) => {
      const g = got.find((x: any) => x.name === `p${i}`);
      const v = vecOf(b.name);
      const cnt = v.filter((x) => (n === INFEAS ? x < INFEAS : x <= n)).length;
      expect(g.cum[g.cum.length - 1]).toBe(B * cnt);
    });
  }
}, 300_000);

// ---- (j) the learn-these-boards sets (analysis/tst-openers-tp-sets.json) ------------------------------------------------
// Everything below is recomputed here, in TypeScript, from the section-(h) tables (J and built per first-bag cost code) and
// the first-bag vectors: every set's value, the greedy steps and k=1 over all boards, k=2 optimality (bounded exhaustive),
// the picks string and every rule tree. Triple optimality is NOT re-derived here (the numpy certificate and the crate's own unit
// test against brute force carry it). The part that needs the tst-sets crate skips loudly without cargo.
const SETS = JSON.parse(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp-sets.json'), 'utf8'));
const KINDS_J = 'IOTSZJL';
const SETS_CRATE = join(SIM, 'tst-sets-rs');
function setsCrateMd5(): string {
  const files = ['tst-sets-rs/Cargo.lock', 'tst-sets-rs/Cargo.toml'];
  for (const f of readdirSync(join(SETS_CRATE, 'src'), { recursive: true }) as string[]) if (f.endsWith('.rs')) files.push(`tst-sets-rs/src/${f}`);
  files.sort();
  const h = createHash('md5');
  for (const f of files) h.update(`${f}\0${md5(readFileSync(join(SIM, f)))}\n`);
  return h.digest('hex');
}
function permsJ(): string[] {
  const out: string[] = [];
  const r = (p: string[], rest: string[]) => {
    if (!rest.length) { out.push(p.join('')); return; }
    for (let i = 0; i < rest.length; i++) r([...p, rest[i]!], [...rest.slice(0, i), ...rest.slice(i + 1)]);
  };
  r([], [...KINDS_J]);
  return out;
}
const PERMS = permsJ();
const FEAT_NAMES: string[] = [];
for (let i = 0; i < 7; i++) for (let j = i + 1; j < 7; j++) FEAT_NAMES.push(`${KINDS_J[i]}<${KINDS_J[j]}`);
for (const k of KINDS_J) FEAT_NAMES.push(`first=${k}`);
const FEAT: boolean[][] = FEAT_NAMES.map((nm) => PERMS.map((p) => nm.startsWith('first=') ? p[0] === nm[6] : p.indexOf(nm[0]!) < p.indexOf(nm[2]!)));
const POOL: any[] = [...ART.boards, ...X.boards];
/** A learned shape is a mirror pair (the board and its mirror); a self-mirror board, or one with no mirror in the pool, is a pair of one.
 * Re-derived here from this file's own mirror function, never read from the artefact. */
const pbkey = (b: any) => `${keyOf(b.pieces)}|${b.held ?? ''}`;
const POSOF = new Map<string, number>(POOL.map((b: any, i: number) => [pbkey(b), i] as [string, number]));
const MATE: number[] = POOL.map((b: any, i: number) => POSOF.get(`${keyOf(mirrorPcs(b.pieces))}|${mk(b.held ?? '')}`) ?? i);
const CANDS: number[][] = [];
POOL.forEach((_: any, i: number) => { const m = MATE[i]!; if (m >= i) CANDS.push(m === i ? [i] : [i, m]); });
const CIDX = new Map<string, number>(CANDS.map((c, n) => [c.join(','), n] as [string, number]));
const unionOf = (cs: number[][]) => [...new Set(cs.flat())].sort((a, b) => a - b);
/** every board's vector, flat: board i is VEC[i] = V.subarray(i * B, (i + 1) * B). */
const NB = POOL.length;
const V = new Uint8Array(NB * B);
const VEC: Uint8Array[] = POOL.map((b: any, i: number) => vecU8(b.name, V.subarray(i * B, (i + 1) * B)));
const STAT = POOL.map((b: any, i: number) => tables(b, VEC[i]!));
/** Per-budget tables over every board, flat: for board i and first-bag cost code c (0..INFEAS), index i * 11 + c.
 * KT is the key J*8192+built, or -1 when the code is not built in the budget (c > lim); JT and BT are J and built for the
 * code, whether or not it is built (only read once the key is >= 0). Computed here from the per-code tables with this
 * file's own cost rule; nothing of size boards x orders beyond the vectors themselves is held. */
type Tab = { KT: Float64Array; JT: Float64Array; BT: Float64Array };
function tabFor(bk: string): Tab {
  const lim = bk === 'inf' ? INFEAS - 1 : Number(bk);
  const W = INFEAS + 1;
  const KT = new Float64Array(NB * W), JT = new Float64Array(NB * W), BT = new Float64Array(NB * W);
  for (let i = 0; i < NB; i++) {
    const [J, Bt] = STAT[i].out[bk];
    for (let c = 0; c < W; c++) {
      expect(Bt[c]).toBeLessThan(8192);
      JT[i * W + c] = J[c]; BT[i * W + c] = Bt[c];
      KT[i * W + c] = c <= lim ? J[c] * 8192 + Bt[c] : -1;
    }
  }
  return { KT, JT, BT };
}
const KCACHE = new Map<string, Tab>();   // four budgets x 3 Float64Array(boards x 11): about 10 MB each
const keysOf = (bk: string): Tab => KCACHE.get(bk) ?? KCACHE.set(bk, tabFor(bk)).get(bk)!;
const W11 = INFEAS + 1;
/** the best-keyed board of `set` at order o, as an index into the flat tables (-1 when none builds it). */
function bestAt(T: Tab, set: number[], o: number): number {
  let best = -1, a = -1;
  for (let m = 0; m < set.length; m++) {
    const i = set[m]!, ix = i * W11 + V[i * B + o]!, kk = T.KT[ix]!;
    if (kk > best) { best = kk; a = ix; }
  }
  return a;
}
function valOf(T: Tab, set: number[]): [number, number] {
  let p = 0, bu = 0;
  for (let o = 0; o < B; o++) {
    const a = bestAt(T, set, o);
    if (a >= 0) { p += T.JT[a]!; bu += T.BT[a]!; }
  }
  return [p, bu];
}
function picksOf(T: Tab, set: number[]): number[] {
  const out: number[] = [];
  for (let o = 0; o < B; o++) {
    let best = -1, a = -1;
    set.forEach((i, m) => { const kk = T.KT[i * W11 + V[i * B + o]!]!; if (kk > best) { best = kk; a = m; } });
    out.push(a);
  }
  return out;
}
/** Per candidate and order: CIX the flat table index of the best-keyed board of the candidate (-1 when none builds it), and
 * CJ its J (-1 likewise). The key is J-major, so the winner's J is the largest J among the built boards. Buffers are reused. */
let CIXBUF: Int32Array | null = null, CJBUF: Int32Array | null = null;
function candTables(T: Tab): [Int32Array, Int32Array] {
  const cix = (CIXBUF ??= new Int32Array(CANDS.length * B)), cj = (CJBUF ??= new Int32Array(CANDS.length * B));
  CANDS.forEach((c, n) => {
    for (let o = 0; o < B; o++) {
      let m = -1, bi = -1, bkey = -1;
      for (let q = 0; q < c.length; q++) {
        const ix = c[q]! * W11 + V[c[q]! * B + o]!;
        const kk = T.KT[ix]!;
        if (kk > bkey) { bkey = kk; bi = ix; }
        if (kk >= 0 && T.JT[ix]! > m) m = T.JT[ix]!;
      }
      cix[n * B + o] = bi; cj[n * B + o] = m;
    }
  });
  return [cix, cj];
}
function walkTree(nd: any, idx: number[], T: Tab, set: number[], mem: number[]) {
  if ('m' in nd) {
    const tot = set.map((i) => idx.reduce((s, o) => { const ix = i * W11 + V[i * B + o]!; return s + (T.KT[ix]! >= 0 ? T.JT[ix]! * 2 ** 26 + T.BT[ix]! : 0); }, 0));
    let bm = 0;
    tot.forEach((t: number, m: number) => { if (t > tot[bm]!) bm = m; });
    expect(nd.m).toBe(bm);
    for (const o of idx) mem[o] = nd.m;
    return;
  }
  const y = idx.filter((o) => FEAT[nd.f]![o]), n = idx.filter((o) => !FEAT[nd.f]![o]);
  expect(y.length > 0 && n.length > 0).toBe(true);
  expect(nd.feature).toBe(FEAT_NAMES[nd.f]);
  walkTree(nd.y, y, T, set, mem); walkTree(nd.n, n, T, set, mem);
}
const depthOf = (nd: any): number => ('m' in nd ? 0 : 1 + Math.max(depthOf(nd.y), depthOf(nd.n)));

test('(j) pins: the sets crate, the artefact and the b1 vectors it was built from are current; flags', () => {
  expect(SETS.schema).toBe('tst-openers-tp-sets/4');
  expect(SETS.md5.tsd).toBe(md5(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp-tsd.json'))));
  expect(SETS.constructed).toBe(true);
  expect(SETS.report_eligible).toBe(false);
  expect(SETS.complete).toBe(false);
  expect(SETS.md5.crate).toBe(setsCrateMd5());
  expect(SETS.md5.b1).toBe(md5(canon(B1)));
  expect(SETS.md5.art).toBe(md5(canon(ART)));
  expect(SETS.md5.x).toBe(md5(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp-x.json'))));
  expect(SETS.features).toEqual(FEAT_NAMES);
  expect(SETS.cands).toBe(CANDS.length);
  expect(SETS.selfmirror).toBe(CANDS.filter((c) => c.length === 1 && MATE[c[0]!] === c[0] && POSOF.has(`${keyOf(mirrorPcs(POOL[c[0]!].pieces))}|${mk(POOL[c[0]!].held ?? '')}`)).length);
  expect(SETS.mirror_missing).toBe(CANDS.filter((c) => c.length === 1 && !POSOF.has(`${keyOf(mirrorPcs(POOL[c[0]!].pieces))}|${mk(POOL[c[0]!].held ?? '')}`)).length);
  expect(SETS.den.pc3).toBe(B ** 3);
  expect(SETS.den.built).toBe(B ** 2);
  const m = clone(SETS); m.md5.crate = 'x';
  expect(m.md5.crate === setsCrateMd5()).toBe(false);          // mutant: a stale crate pin is seen
  expect(PERMS.length).toBe(B);
  expect(PERMS[0]).toBe('IOTSZJL');
  expect(PERMS[B - 1]).toBe('LJZSTOI');                         // order indexing fixture: identity first, reverse last
  expect(new Set(PERMS).size).toBe(B);
});

test('(j) every set value, greedy step, k=1 optimum, k=2 optimum, pick string and rule tree is recomputed here', () => {
  for (const bk of BKEYS) {
    const K = keysOf(bk), r = SETS.budgets[bk];
    const pos = (rec: any) => rec.boards.map((x: any) => x.pos);
    const chk = (rec: any) => {
      for (const x of rec.boards) {
        expect(POOL[x.pos].name).toBe(x.name);
        expect(keyOf(POOL[x.pos].pieces)).toBe(keyOf(x.pieces));
      }
      // k mirror pairs, each a candidate of this file's own derivation, whose union is the listed boards
      for (const pr of rec.pairs) expect(CIDX.has([...pr].join(','))).toBe(true);
      expect(pos(rec)).toEqual(unionOf(rec.pairs));
      expect(valOf(K, pos(rec))).toEqual([rec.pc3, rec.built]);
    };
    for (const k of ['1', '2', '3']) { chk(r.exact[k]); expect(r.exact[k].pairs.length).toBe(Number(k)); }
    for (const k of ['1', '2', '3', '4', '5']) { chk(r.greedy[k]); expect(r.greedy[k].pairs.length).toBe(Number(k)); }
    for (const k of ['4', '5']) chk(r.from_exact3[k]);
    // exact >= greedy
    for (const k of ['1', '2', '3']) { const e = r.exact[k], g = r.greedy[k]; expect(e.pc3 > g.pc3 || (e.pc3 === g.pc3 && e.built >= g.built)).toBe(true); }
    // k = 1 over all pair candidates
    const f1 = CANDS.map((c) => valOf(K, c));
    let best = 0;
    f1.forEach((v: number[], i: number) => { const bv = f1[best]!; if (v[0]! > bv[0]! || (v[0] === bv[0] && v[1]! > bv[1]!)) best = i; });
    expect(r.exact['1'].pairs).toEqual([CANDS[best]]);
    // k = 2: bounded exhaustive over pairs of candidates (f(ab) <= f(a) + f(b)), pc3 only. A pair's value at an order is the
    // better of the two candidates' keys, and the key is J-major, so it is the larger J (-1 where neither builds it).
    const [CIX, CJ] = candTables(K);
    const order = f1.map((_: any, i: number) => i).sort((a: number, b: number) => f1[b]![0]! - f1[a]![0]!);
    let top = 0;
    for (let x = 0; x < order.length; x++) {
      const a = order[x]!;
      if (f1[a]![0]! * 2 < top) break;
      const ca = CJ.subarray(a * B, (a + 1) * B);
      for (let y = x + 1; y < order.length; y++) {
        const b = order[y]!;
        if (f1[a]![0]! + f1[b]![0]! < top) break;
        const cb = CJ.subarray(b * B, (b + 1) * B);
        let p = 0;
        for (let o = 0; o < B; o++) {
          const ja = ca[o]!, jb = cb[o]!;
          const m = ja > jb ? ja : jb;
          if (m > 0) p += m;
        }
        if (p > top) top = p;
      }
    }
    expect(top).toBe(r.exact['2'].pc3);
    // greedy step k = argmax over all pair candidates of the grown set (the union of boards). The grown set's value is the
    // base set's plus, at each order where the candidate's best key beats the base set's, the candidate's J and built minus the base's.
    for (const k of [2, 3, 4, 5]) {
      const prev: number[][] = r.greedy[String(k - 1)].pairs;
      const base = unionOf(prev);
      const bk0 = new Float64Array(B), bj0 = new Float64Array(B), bb0 = new Float64Array(B);
      let P0 = 0, B0 = 0;
      for (let o = 0; o < B; o++) {
        const a = bestAt(K, base, o);
        if (a < 0) { bk0[o] = -1; continue; }
        bk0[o] = K.KT[a]!; bj0[o] = K.JT[a]!; bb0[o] = K.BT[a]!; P0 += bj0[o]!; B0 += bb0[o]!;
      }
      let bp = -1, bb = -1;
      for (let c = 0; c < CANDS.length; c++) {
        if (prev.some((q: number[]) => q.join(',') === CANDS[c]!.join(','))) continue;
        let p = P0, b = B0;
        for (let o = 0, q = c * B; o < B; o++, q++) {
          const a = CIX[q]!;
          if (a >= 0 && K.KT[a]! > bk0[o]!) { p += K.JT[a]! - bj0[o]!; b += K.BT[a]! - bb0[o]!; }
        }
        if (p > bp || (p === bp && b > bb)) { bp = p; bb = b; }
      }
      expect([bp, bb]).toEqual([r.greedy[String(k)].pc3, r.greedy[String(k)].built]);
    }
    // picks and trees over the exact triple
    const s3 = pos(r.exact['3']);
    expect(r.picks).toBe(picksOf(K, s3).map((x) => (x < 0 ? 'x' : String(x))).join(''));
    const pk = picksOf(K, s3);
    for (const d of [1, 2, 3]) {
      const rule = r.rule[String(d)], mem: number[] = new Array(B).fill(-1);
      walkTree(rule.tree, [...Array(B).keys()], K, s3, mem);
      let p = 0, b = 0, unb = 0, diff = 0;
      for (let o = 0; o < B; o++) {
        const i = s3[mem[o]!]!;
        const ix = i * W11 + V[i * B + o]!;
        if (K.KT[ix]! >= 0) { p += K.JT[ix]!; b += K.BT[ix]!; } else unb++;
        if (pk[o]! >= 0 && pk[o] !== mem[o]) diff++;
      }
      expect([p, b, unb, diff]).toEqual([rule.pc3, rule.built, rule.unbuildable, rule.differs]);
      expect(depthOf(rule.tree)).toBeLessThanOrEqual(d);
      expect(rule.loss_pc3).toBe(r.exact['3'].pc3 - rule.pc3);
      expect(rule.loss_built).toBe(r.exact['3'].built - rule.built);
      // mutant: a wrong leaf label is caught by the walker
      if (d === 1) {
        const bad = clone(rule.tree); bad.m = (bad.m + 1) % 3;
        if ('m' in bad) expect(() => walkTree(bad, [...Array(B).keys()], K, s3, mem.slice())).toThrow();
      }
    }
    // mutants: a perturbed value and a flipped pick char are both unequal to the recomputation
    expect(valOf(K, pos(r.exact['3']).slice(0, 2))).not.toEqual([r.exact['3'].pc3, r.exact['3'].built]);
    expect(r.picks.replace(/./, (c: string) => (c === '0' ? '1' : '0'))).not.toBe(picksOf(K, s3).map((x) => (x < 0 ? 'x' : String(x))).join(''));
  }
}, 600_000);

test('(j) the fixed set (budget 2 exact triple) is valued at every budget, and pinned by pieces', () => {
  const fx = SETS.fixed, p = fx.boards.map((x: any) => x.pos);
  expect(p).toEqual(SETS.budgets['2'].exact['3'].boards.map((x: any) => x.pos));
  expect(fx.pairs).toEqual(SETS.budgets['2'].exact['3'].pairs);
  const want = ['I:2,12,22,32/L:7,8,9,19/O:0,1,10,11/S:4,5,15,16/T:3,13,14,23/Z:18,28,29,39', 'I:7,17,27,37/J:0,1,2,10/O:8,9,18,19/S:11,20,21,30/T:6,15,16,26/Z:4,5,13,14', 'I:10,20,30,40/J:8,9,19,29/O:21,22,31,32/S:0,1,11,12/T:5,15,16,25/Z:7,17,18,28', 'I:19,29,39,49/L:0,1,10,20/O:27,28,37,38/S:2,11,12,21/T:4,13,14,24/Z:8,9,17,18', 'I:10,20,30,40/J:8,9,19,29/L:50,51,60,70/O:21,22,31,32/S:0,1,11,12/T:5,15,16,25', 'I:19,29,39,49/J:58,59,69,79/L:0,1,10,20/O:27,28,37,38/T:4,13,14,24/Z:8,9,17,18'];
  expect(fx.boards.map((x: any) => keyOf(x.pieces))).toEqual(want);
  for (const bk of BKEYS) expect(valOf(keysOf(bk), p)).toEqual([fx.values[bk].pc3, fx.values[bk].built]);
  expect(valOf(keysOf('0'), p)).not.toEqual([fx.values['1'].pc3, fx.values['1'].built]);
});

test('(j) cross-crate: the tst-sets binary on input built here reproduces the artefact (skipped without cargo)', () => {
  const r0 = Bun.spawnSync(['cargo', 'build', '--release', '--locked', '--quiet', '--manifest-path', join(SETS_CRATE, 'Cargo.toml')], { stderr: 'pipe' });
  const bin = join(SETS_CRATE, 'target', 'release', 'tst-sets');
  if (r0.exitCode !== 0 || !existsSync(bin)) { console.warn('SKIPPED (j): cargo is unavailable or tst-sets failed to build; the sets are NOT re-run through the crate'); return; }
  const lines = POOL.map((b: any, i: number) => {
    const raw = inflateSync(Buffer.from(B1.vectors[b.name] ?? X.vectors[b.name], 'base64')).toString();
    const f = BKEYS.map((bk) => `${STAT[i].out[bk][0].slice(0, INFEAS).join(',')}/${STAT[i].out[bk][1].slice(0, INFEAS).join(',')}`);
    return [b.name, raw, ...f, String(MATE[i])].join('|');
  });
  const r = Bun.spawnSync([bin], { stdin: Buffer.from(lines.join('\n') + '\n'), stderr: 'pipe' });
  expect(r.exitCode).toBe(0);
  const out = JSON.parse(r.stdout.toString());
  for (const bk of BKEYS) {
    const g = out.budgets[bk], a = SETS.budgets[bk];
    expect(g.exact.map((s: any) => s.ub)).toEqual([1, 2, 3].map((k) => a.exact[String(k)].boards.map((x: any) => x.pos)));
    expect(g.greedy.map((s: any) => s.ub)).toEqual([1, 2, 3, 4, 5].map((k) => a.greedy[String(k)].boards.map((x: any) => x.pos)));
  }
}, 300_000);

// ---- (k) TST -> TSD -> PC (analysis/tst-openers-tp-tsd.json) -------------------------------------------------------------
const TSD = JSON.parse(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp-tsd.json'), 'utf8'));
const TSD_CRATE = join(SIM, 'tst-tsd-rs');
function tsdCrateMd5(): string {
  const files = ['tst-tsd-rs/Cargo.lock', 'tst-tsd-rs/Cargo.toml'];
  for (const c of ['tst-tsd-rs', 'oracle-rs', 'pc-solver-rs'])
    for (const f of readdirSync(join(SIM, c, 'src'), { recursive: true }) as string[]) if (f.endsWith('.rs')) files.push(`${c}/src/${f}`);
  const h = createHash('md5');
  for (const f of [...new Set(files)].sort()) h.update(`${f}\0${md5(readFileSync(join(SIM, f)))}\n`);
  return h.digest('hex');
}

test('(k) pins: the tsd artefact is current, flagged constructed, and pt3 <= p5 <= 5040 on every line', () => {
  expect(TSD.schema).toBe('tst-openers-tp-tsd/1');
  expect(TSD.constructed).toBe(true);
  expect(TSD.report_eligible).toBe(false);
  expect(TSD.den).toBe(B);
  expect(TSD.bad_plans).toBe(0);
  expect(TSD.md5.crate).toBe(tsdCrateMd5());
  expect(TSD.md5.tst_openers_tp).toBe(md5(canon(JSON.parse(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp.json'), 'utf8')))));
  expect(TSD.md5.x).toBe(md5(readFileSync(join(ROOT, 'analysis', 'tst-openers-tp-x.json'))));
  const ls = Object.values(TSD.lines) as any[];
  expect(ls.length).toBeGreaterThan(0);
  for (const r of ls) expect(0 <= r.pt3 && r.pt3 <= r.p5 && r.p5 <= B).toBe(true);
});

test('(k) pilot lines re-run through the tst-tsd binary reproduce the artefact (skipped without cargo)', () => {
  const r0 = Bun.spawnSync(['cargo', 'build', '--release', '--locked', '--quiet', '--manifest-path', join(TSD_CRATE, 'Cargo.toml')], { stderr: 'pipe' });
  const bin = join(TSD_CRATE, 'target', 'release', 'tst-tsd');
  if (r0.exitCode !== 0 || !existsSync(bin)) { console.warn('SKIPPED (k): cargo is unavailable or tst-tsd failed to build; pt3 is NOT re-run'); return; }
  // the cheapest lines: the fewest leftover pieces solve fastest
  const keys = Object.keys(TSD.lines).sort((a, b) => Number(b.split('|')[1]!.length < a.split('|')[1]!.length) - Number(a.split('|')[1]!.length < b.split('|')[1]!.length)).slice(0, 3);
  const r = Bun.spawnSync([bin], { stdin: Buffer.from(keys.join('\n') + '\n'), stderr: 'pipe' });
  expect(r.exitCode).toBe(0);
  const got = r.stdout.toString().trim().split('\n').map((l) => JSON.parse(l));
  expect(got.length).toBe(keys.length);
  for (const g of got) {
    const a = TSD.lines[g.line];
    expect([g.p5, g.p5u, g.pt3, g.pt3u]).toEqual([a.p5, a.p5u, a.pt3, a.pt3u]);
  }
}, 600_000);
