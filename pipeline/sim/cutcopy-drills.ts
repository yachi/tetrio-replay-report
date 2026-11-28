/**
 * 千鳥格子練習場's drills: CONSTRUCTED practice boards for the page `docs/practice-cutcopy.html`, built from the
 * boards a 千鳥格子 (Cut Copy) was actually built on, rewound to before the window could fire. The logic lives
 * here; `emit-cutcopy-drills.ts` is argv and file IO only, and `pipeline/openers/cutcopy-drills.test.ts` gates it.
 *
 * Inputs, all committed, each hashed into the artefact:
 *   - the QUALIFYING hits of `analysis/cutcopy-facts.json`, each replayed off its session's `sim/replay-facts.json`
 *     timeline (the board before every lock, the garbage each lock took);
 *   - cold-clear's self-play games, `analysis/cutcopy-selfplay.json` (their committed placements);
 *   - our own engine-built design, `analysis/cutcopy-own.json` (its timeline);
 *   - the page's T-hole build, node `hole.osz` of `pipeline/openers/cutcopy-technique.json` (its grey terrain).
 *
 * THE PRACTICE ENGINE IS THE ONE THAT DECIDES. Every source's lock sequence is re-placed in the page's own engine
 * (`pipeline/cutcopy_practice_engine.js`), each lock as the shortest key path to the same four cells, and the
 * window that engine fires is the corpus matcher's own: the windows are `technique-facts.ts`'s `prepare()` output
 * for the `cutcopy` and `uncut` variants, carried in the artefact and passed to the engine's `setWindows`, never
 * typed. A source the practice engine cannot replay (no path to a lock's cells, the run fails, no build) is dropped
 * with its reason, never repaired.
 *
 * SELECTION IS CODE, AND EVERY CANDIDATE IT REFUSES IS LISTED (`dropped`, with its reason):
 *   - rewind: a drill starts 4 pieces before the first lock after which the window can fire (淺); when that lock
 *     is 6 or more pieces in, a second drill starts at the earliest board kept (深, up to 8 pieces). Our own design
 *     is played from empty only. A cut whose start can already fire is dropped (`already_buildable`);
 *   - a Tetris on the way to the build moves the start to just after it (`skippedTetris`), so a drill never asks
 *     for a Tetris the window does not need;
 *   - exact duplicates (same start, the queue the drill deals and the same need) keep the first;
 *   - garbage luck: a drill with garbage is replayed with every event's hole in each of the 10 columns; when only
 *     the original column lets the build stand, the drill is dropped (`garbage_luck`), because the original column
 *     is the engine's seeded hole and no recording says it was the game's (the caveat in `provenance`).
 * Difficulty is the fewest pieces (any piece, a T placed as a piece included; hold allowed) after which the
 * practice engine finds a window build, searched breadth first and exhaustively up to 3 pieces (`min_by:
 * "practice engine"`); past 3 it is the drill's own need when that is 4 (the solution is a witness), else unknown
 * (極難). The search skips `findBuild` on a board where no window can stand at any offset (`windowCanStand`), which
 * is a necessary condition of a build and so changes no answer, only the time.
 */
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { loadTranscription, prepare } from './technique-facts.ts';
import { minNeedNative } from './cutcopy-native.ts';
import { decodeTimeline, placeCells, queueStates, SHAPES, ROWS, WIDTH, type Lock } from './emit-replay.ts';

const SIM = import.meta.dir;
export const REPO = resolve(SIM, '..', '..');
export const ENGINE_PATH = join(REPO, 'pipeline', 'cutcopy_practice_engine.js');
export const PATHS = {
  transcription: join(REPO, 'pipeline', 'openers', 'cutcopy-technique.json'),
  facts: join(REPO, 'analysis', 'cutcopy-facts.json'),
  selfplay: join(REPO, 'analysis', 'cutcopy-selfplay.json'),
  own: join(REPO, 'analysis', 'cutcopy-own.json'),
  out: join(REPO, 'analysis', 'cutcopy-drills.json'),
};
/** the code the artefact hashes, beside its data inputs */
export const CODE = [join(SIM, 'cutcopy-drills.ts'), join(SIM, 'emit-cutcopy-drills.ts'), ENGINE_PATH,
                     join(SIM, 'technique-facts.ts'), join(SIM, 'emit-replay.ts')];
export const VARIANTS = ['cutcopy', 'uncut'] as const;
export const PAGE_NODE = 'hole.osz';
/** how many pieces before the first buildable lock a drill may start */
export const REWIND = { shallow: 4, deep: 8, deepFrom: 6 } as const;
/** the breadth-first difficulty search's depth, and its frontier cap */
export const MIN_CAP = 3, MIN_FRONTIER = 40000;
export const LABELS: Record<string, string> = { 1: '易', 2: '易', 3: '中', 4: '難' };
export const UNKNOWN_LABEL = '極難';

/** the page engine, one module instance (its window list is module state) */
export const E = createRequire(import.meta.url)(ENGINE_PATH);

type Rows = string[];
type Step = { piece: string; cells: number[][]; garbage?: [number, number][] };
export type Drop = { id: string; reason: string; detail?: string };

const md5 = (p: string) => createHash('md5').update(readFileSync(p)).digest('hex');
const rel = (p: string) => relative(REPO, p);
const emptyRows = (): Rows => Array.from({ length: ROWS }, () => '.'.repeat(WIDTH));

// ── the windows, from the corpus matcher's own prepare() ────────────────────────────────────────

/** Every prepared window of both variants, in the engine's format: box cells first, then `window_extra`
 *  cells (flagged `extra`), the follow-up slot pre-clear, and the box (the same box in both hands). */
export function windowsFor(tr: any) {
  const out: any[] = [];
  for (const id of VARIANTS) {
    const v = tr.variants.find((x: any) => x.id === id);
    if (!v) throw new Error(`cutcopy-drills: no variant ${id} in the transcription`);
    const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
    const nbox = (r1 - r0 + 1) * (c1 - c0 + 1);
    for (const P of prepare(tr, v)) {
      out.push({
        id: P.id, mirrored: P.mirrored,
        T: P.T.map(x => ({ r: x.r, c: x.c })),
        cells: P.cells.map((x, i) => i >= nbox ? { r: x.r, c: x.c, v: x.v, extra: true } : { r: x.r, c: x.c, v: x.v }),
        followup: P.followup.map(x => ({ r: x.r, c: x.c })),
        box: { r0, r1, c0, c1 },
      });
    }
  }
  return out;
}

// ── sources: each a lock sequence (piece, cells y-down, the garbage that came in before it) ─────

const yDownCells = (piece: string, place: Lock[1]) =>
  placeCells(piece, place).map(c => [c % WIDTH, ROWS - 1 - Math.floor(c / WIDTH)]).sort((a, b) => a[0]! - b[0]! || a[1]! - b[1]!);
const yDownRows = (b: (string | null)[][]): Rows => {
  const out: Rows = [];
  for (let y = ROWS - 1; y >= 0; y--) out.push(b[y]!.map(v => v == null ? '.' : v.toUpperCase()).join(''));
  return out;
};

/** a timeline's per-lock steps and the board after each lock */
function timelineSteps(seq: string, locks: Lock[]) {
  const q = queueStates(seq, locks);
  const steps: (Step & { after: Rows })[] = [];
  decodeTimeline(seq, locks, (b, i) => {
    const lk = locks[i]!, piece = q[i]!.piece;
    steps.push({ piece, cells: yDownCells(piece, lk[1]), garbage: lk[4].map(g => [g[0], g[1]] as [number, number]),
                 after: yDownRows(b) });
  });
  return steps;
}

export interface Source {
  base: { id: string; kind: string; title?: string; note?: string };
  source: Record<string, unknown>;
  start: Rows; steps: Step[];
  /** the source lock index the steps start at (the page and our own design: 0) */
  from: number;
}

const replayCache = new Map<string, any>();
function replayFacts(session: string) {
  if (!replayCache.has(session))
    replayCache.set(session, JSON.parse(readFileSync(join(REPO, 'sessions', session, 'sim', 'replay-facts.json'), 'utf8')));
  return replayCache.get(session);
}
export const replayPath = (session: string) => join(REPO, 'sessions', session, 'sim', 'replay-facts.json');

/** the qualifying corpus hits, rewound REWIND.deep locks */
export function corpusSources(facts: any): Source[] {
  const out: Source[] = [];
  for (const h of facts.hits) {
    if (!h.qualifies) continue;
    const rf = replayFacts(h.session);
    const round = rf.rounds.find((r: any) => r.file === h.file && r.round === h.round_index0);
    if (!round) throw new Error(`cutcopy-drills: no round ${h.file} ${h.round_index0} in ${h.session}'s replay facts`);
    const pl = round.players.find((p: any) => p.user === h.player);
    if (!pl) throw new Error(`cutcopy-drills: no player ${h.player} in ${h.file} round ${h.round_index0}`);
    const steps = timelineSteps(round.seq, pl.locks);
    const k = h.lock, f = h.followup.lock, from = Math.max(0, k - REWIND.deep);
    out.push({
      base: { id: `${h.session}-m${h.match}r${h.round}`, kind: 'corpus' },
      source: { kind: 'corpus', session: h.session, file: h.file, match: h.match, round: h.round, player: h.player,
                variant: h.variant, mirrored: h.mirrored, lock: k, followup_lock: f },
      start: from > 0 ? steps[from - 1]!.after : emptyRows(),
      steps: steps.slice(from, f + 1).map(s => ({ piece: s.piece, cells: s.cells, garbage: s.garbage })),
      from,
    });
  }
  return out;
}

/** cold-clear's self-play hits, from their committed placements (y-down cells, no garbage) */
export function selfplaySources(sp: any): Source[] {
  const out: Source[] = [];
  for (const g of sp.games) for (const h of g.hits) {
    const k = h.lock, f = h.followup.lock, from = Math.max(0, k - REWIND.deep);
    const b = Array.from({ length: ROWS }, () => new Array<string>(WIDTH).fill('.'));
    let bstart: Rows | null = null;
    g.placements.forEach((p: any, i: number) => {
      if (i === from) bstart = b.map(r => r.join(''));
      for (const [x, y] of p.cells) b[y]![x] = p.piece;
      for (let y = 0; y < ROWS; y++) if (b[y]!.every(c => c !== '.')) { b.splice(y, 1); b.unshift(new Array(WIDTH).fill('.')); }
    });
    if (!bstart) throw new Error(`cutcopy-drills: self-play ${g.id} has no lock ${from}`);
    out.push({
      base: { id: `sp-${g.seed}-${k}`, kind: 'selfplay' },
      source: { kind: 'selfplay', seed: g.seed, node: g.node, variant: h.variant, mirrored: h.hand === 'mirrored',
                lock: k, followup_lock: f },
      start: bstart,
      steps: g.placements.slice(from, f + 1).map((p: any) => ({ piece: p.piece, cells: p.cells })),
      from,
    });
  }
  return out;
}

/** our own engine-built designs, played from empty */
export function ownSources(own: any): Source[] {
  if (JSON.stringify(own.shapes) !== JSON.stringify(SHAPES))
    throw new Error('cutcopy-drills: the own-design artefact draws its pieces with other shapes than emit-replay.ts');
  return own.demos.map((d: any) => ({
    base: { id: d.node, kind: 'own' },
    source: { kind: 'own', node: d.node, variant: d.variant, lock: d.stood_lock, followup_lock: d.followup_lock },
    start: emptyRows(),
    steps: timelineSteps(d.seq, d.locks).map(s => ({ piece: s.piece, cells: s.cells, garbage: s.garbage })),
    from: 0,
  }));
}

export const PAGE_TITLE = 'T 形窿上面砌';
export const PAGE_NOTE = 'shiwehi：「T 形窿旁邊擺 S（錯開一行），再喺上面擺 O 同 Z」。地形係頁面畫嘅灰色部份。';

/** the page's T-hole build: its grey terrain, the O, S and Z it draws, then the two T's the engine finds */
export function pageSource(tr: any): Source {
  const node = tr.nodes.find((n: any) => n.id === PAGE_NODE);
  if (!node) throw new Error(`cutcopy-drills: no node ${PAGE_NODE}`);
  const rows: string[] = node.rows, off = ROWS - rows.length;
  const start = emptyRows();
  rows.forEach((r, i) => { start[off + i] = [...r].map(ch => ch === 'c' ? 'G' : '.').join(''); });
  const steps: Step[] = [];
  for (const letter of 'osz') {
    const cells: number[][] = [];
    rows.forEach((r, i) => [...r].forEach((ch, x) => { if (ch === letter) cells.push([x, off + i]); }));
    if (cells.length !== 4) throw new Error(`cutcopy-drills: ${PAGE_NODE} draws ${cells.length} '${letter}' cells`);
    steps.push({ piece: letter.toUpperCase(), cells });
  }
  // the T's: the engine's own shortest window build, then the follow-up into its carried slot
  const pz = { mode: 'build', start, queue: steps.map(s => s.piece), events: [] };
  const run = E.newRun(pz);
  for (const st of steps) { const o = place(run.board, st.piece, st.cells, false); if (!o) throw new Error('page: no path'); E.applyLock(run, pz, o.state); }
  const fb = E.findBuild(run.board);
  if (!fb) throw new Error(`cutcopy-drills: ${PAGE_NODE} built by the engine fires no window`);
  steps.push({ piece: 'T', cells: fb.cells });
  E.applyLock(run, pz, fb.state);
  const sec = E.findSecond(run.board, run.slot);
  if (!sec) throw new Error(`cutcopy-drills: ${PAGE_NODE}'s follow-up T is unreachable`);
  steps.push({ piece: 'T', cells: E.lock(run.board, sec.state).cells });
  return { base: { id: 'page-hole', kind: 'page', title: PAGE_TITLE, note: PAGE_NOTE },
           source: { kind: 'page', node: PAGE_NODE }, start, steps, from: 0 };
}

// ── replaying a source in the practice engine ───────────────────────────────────────────────────

/** the shortest key path to exactly these cells (a T prefers a full spin, then a mini) */
export function place(b: any, p: string, cells: number[][], preferFull: boolean) {
  const k = E.key(cells);
  const all = E.placements(b, p).filter((o: any) => E.key(E.cellsOf(o.state.p, o.state.x, o.state.y, o.state.r)) === k);
  const rank: Record<string, number> = { full: 0, mini: 1, none: 2 };
  all.sort((a: any, c: any) => (preferFull ? rank[a.state.spin]! - rank[c.state.spin]! : 0) || a.path.length - c.path.length);
  return all[0] || null;
}
const evOf = (steps: Step[]) => {
  const ev: any[] = [];
  steps.forEach((s, i) => { for (const [col, n] of s.garbage ?? []) ev.push({ kind: 'garbage', before: i, n, col }); });
  return ev;
};
const stateOf = (s: any) => ({ p: s.piece, x: s.x, y: s.y, r: s.r, spin: s.spin });

/** Replay a source in the practice engine. `firstB` is the first lock count after which a window build is
 *  reachable (the lock count at which the T fired, when the build is only seen as the T goes in). */
export function make(src: Source): { pz0: any; sol: any[]; firstB: number } | { reason: string; detail: string } {
  const pz0 = { mode: 'build', start: src.start.map(r => r.toUpperCase()), queue: src.steps.map(s => s.piece), events: evOf(src.steps) };
  const run = E.newRun(pz0), sol: any[] = [];
  let firstB = E.findBuild(run.board) ? 0 : -1;
  for (const st of src.steps) {
    const o = place(run.board, st.piece, st.cells, st.piece === 'T');
    if (!o) return { reason: 'no_path', detail: `lock ${src.from + sol.length} (${st.piece}): the practice engine reaches no path to its cells` };
    const fb = E.applyLock(run, pz0, o.state);
    sol.push({ piece: st.piece, x: o.state.x, y: o.state.y, r: o.state.r, path: o.path, spin: o.state.spin, lines: fb.lines });
    if (run.failed) return { reason: 'run_failed', detail: `lock ${src.from + sol.length - 1}: ${run.failed}` };
    if (firstB < 0 && run.stage === 0 && E.findBuild(run.board)) firstB = sol.length;
    if (run.stage >= 1 && firstB < 0) firstB = sol.length - 1;
  }
  if (firstB < 0 || !run.done) return { reason: 'no_build', detail: `the practice engine fires ${run.done ? 'no window build' : 'no full Cut Copy'} on this sequence` };
  return { pz0, sol, firstB };
}

/** replay a drill's first n solution locks; returns the run */
export function replayN(d: any, n: number) {
  const run = E.newRun(d);
  for (let i = 0; i < n; i++) E.applyLock(run, d, stateOf(d.solution[i]));
  return run;
}
/** the lock count after which the window first becomes buildable (or the T fired), or -1 */
export function firstBuildable(d: any) {
  if (E.findBuild(E.newRun(d).board)) return 0;
  const run = E.newRun(d);
  for (let i = 0; i < d.solution.length; i++) {
    E.applyLock(run, d, stateOf(d.solution[i]));
    if (E.findBuild(run.board) || run.stage >= 1) return i + 1;
  }
  return -1;
}

const rowsOf = (board: any[][]) => board.map(row => row.map((c: any) => c || '.').join(''));

function cut(src: Source, r: { pz0: any; sol: any[]; firstB: number }, s: number, label: string): any | Drop {
  const { pz0, sol, firstB } = r;
  const id = `${src.base.id}@${s}`;
  const run = E.newRun(pz0);
  for (let i = 0; i < s; i++) E.applyLock(run, pz0, stateOf(sol[i]));
  if (E.findBuild(run.board)) return { id, reason: 'already_buildable', detail: `the window can already fire ${s} pieces in` };
  const tr = E.newRun(pz0);
  for (let i = 0; i < firstB; i++) E.applyLock(tr, pz0, stateOf(sol[i]));
  const fbB = E.findBuild(tr.board);
  const d: any = {
    ...src.base, mode: 'build', id,
    start: rowsOf(run.board), queue: pz0.queue.slice(s), hold: null,
    events: pz0.events.filter((e: any) => e.before > s).map((e: any) => ({ ...e, before: e.before - s })),
    need: firstB - s, level: label,
    target: { cells: fbB.m.cells, t: fbB.cells, variant: fbB.m.variant, mirrored: fbB.m.mirrored, at: firstB - s },
    solution: sol.slice(s),
    source: { ...src.source, start_lock: src.from + s },
  };
  const got = firstBuildable(d);
  if (got !== d.need) return { id, reason: 'replay_mismatch', detail: `first buildable after ${got} pieces, not ${d.need}` };
  return d;
}

/** a drill whose way to the build runs through a Tetris starts right after the Tetris instead */
export function skipTetris(d: any): any {
  const k = d.solution.slice(0, d.need).findIndex((s: any) => s.lines === 4);
  if (k < 0) return d;
  const run = replayN(d, k + 1);
  return {
    ...d,
    id: d.id.replace(/@(\d+)$/, (_m: string, a: string) => `@${+a + k + 1}`),
    start: rowsOf(run.board), queue: d.queue.slice(k + 1), need: d.need - k - 1,
    target: { ...d.target, at: d.target.at - k - 1 },
    solution: d.solution.slice(k + 1),
    // events up to and including lock k+1 are on the new start board already
    events: d.events.filter((e: any) => e.before > k + 1).map((e: any) => ({ ...e, before: e.before - k - 1 })),
    source: { ...d.source, start_lock: d.source.start_lock + k + 1 },
    skippedTetris: true,
  };
}

/** which hole columns let the build stand within `need` pieces (every event's hole moved there) */
export function garbageColumns(d: any): number[] {
  const ok: number[] = [];
  for (let c = 0; c < WIDTH; c++) {
    const q = { ...d, events: d.events.map((e: any) => ({ ...e, col: c })) };
    const run = E.newRun(q);
    for (let i = 0; i < d.need; i++) {
      const s = stateOf(d.solution[i]);
      if (!E.legal(run.board, E.cellsOf(s.p, s.x, s.y, s.r))) break;
      E.applyLock(run, q, s);
      if (E.findBuild(run.board)) { ok.push(c); break; }
    }
  }
  return ok;
}

// ── difficulty: the fewest pieces after which a window build is reachable ─────────────────

function kids(st: { run: any; qi: number }, pz: any) {
  const out: { run: any; qi: number }[] = [];
  const r = st.run, cur = pz.queue[st.qi];
  if (!cur) return out;
  const opts: [string, string | null, number][] = [[cur, r.hold, st.qi + 1]];
  if (r.hold == null) { const nx = pz.queue[st.qi + 1]; if (nx) opts.push([nx, cur, st.qi + 2]); }
  else if (r.hold !== cur) opts.push([r.hold, cur, st.qi + 1]);
  for (const [p, h, qi] of opts) {
    const seen = new Set<string>();
    for (const pl of E.placements(r.board, p)) {
      const k = E.key(E.cellsOf(p, pl.state.x, pl.state.y, pl.state.r));
      if (seen.has(k)) continue;
      seen.add(k);
      const run = { ...r, log: [] };
      run.hold = h;
      E.applyLock(run, { ...pz, mode: 'build' }, pl.state);
      out.push({ run, qi });
    }
  }
  return out;
}

/** a necessary condition of `E.findBuild(b)`: some window stands on `b` at some offset, its filled cells filled
 *  and its empty and T cells empty. `findBuild` locks a T and asks `matchWindow`, which reads exactly those cells
 *  at the T's offset, so a board where no offset fits has no build. */
export function windowCanStand(b: any[][]): boolean {
  for (const w of E.windows()) {
    const rs = w.cells.map((q: any) => q.r), cs = w.cells.map((q: any) => q.c);
    const r0 = Math.min(...rs), r1 = Math.max(...rs), c0 = Math.min(...cs), c1 = Math.max(...cs);
    for (let dy = -r0; dy + r1 < E.H; dy++) for (let dx = -c0; dx + c1 < E.W; dx++) {
      let ok = true;
      for (const q of w.cells) {
        const filled = b[q.r + dy]![q.c + dx] !== null;
        if (q.v === '#' ? !filled : filled) { ok = false; break; }
      }
      if (ok) return true;
    }
  }
  return false;
}
const buildable = (b: any[][]) => windowCanStand(b) && !!E.findBuild(b);

/** breadth first over placements of every piece (hold allowed): the depth at which a build first stands, or
 *  `{ beyond: d, cut }` when none within `cap` (cut: a frontier before `cap` passed MIN_FRONTIER and the search
 *  stopped there, so it is not exhaustive; the last level is always searched whole) */
export function minNeedTs(pz: any, cap: number): number | { beyond: number; cut: boolean } {
  let lvl = [{ run: E.newRun(pz), qi: 0 }];
  if (buildable(lvl[0]!.run.board)) return 0;
  for (let d = 1; d <= cap; d++) {
    const nl: typeof lvl = [], seen = new Set<string>();
    for (const s of lvl) for (const k of kids(s, pz)) {
      const key = `${k.qi}|${k.run.hold}|${k.run.board.map((r: any[]) => r.map(c => c ? 1 : 0).join('')).join('')}`;
      if (seen.has(key)) continue;
      seen.add(key);
      if (buildable(k.run.board)) return d;
      if (d < cap) nl.push(k);
    }
    lvl = nl;
    if (d < cap && lvl.length > MIN_FRONTIER) return { beyond: d, cut: true };
  }
  return { beyond: cap, cut: false };
}

/** `minNeedTs`, answered by the Rust port (`cutcopy-native.ts`) unless `CUTCOPY_NATIVE=off`; `cutcopy-native.test.ts`
 *  holds the two equal. */
export function minNeed(pz: any, cap: number): number | { beyond: number; cut: boolean } {
  if (process.env.CUTCOPY_NATIVE === 'off') return minNeedTs(pz, cap);
  const run = E.newRun(pz);
  return minNeedNative(pz, run.board, run.hold, E.windows(), cap, MIN_FRONTIER);
}

export function difficulty(d: any) {
  const cap = Math.min(d.need, MIN_CAP);
  const m = minNeed(d, cap);
  let min: number | null;
  if (typeof m === 'number') min = m;
  else if (!m.cut && d.need === cap + 1) min = d.need;
  else min = null;
  return { label: min == null ? UNKNOWN_LABEL : LABELS[min]!, min, min_by: 'practice engine' };
}

// ── the whole artefact ──────────────────────────────────────────────────────────────────────────

export function build() {
  const tr = loadTranscription(PATHS.transcription);
  const windows = windowsFor(tr);
  E.setWindows(windows);
  const facts = JSON.parse(readFileSync(PATHS.facts, 'utf8'));
  const sp = JSON.parse(readFileSync(PATHS.selfplay, 'utf8'));
  const own = JSON.parse(readFileSync(PATHS.own, 'utf8'));
  const sources = [pageSource(tr), ...corpusSources(facts), ...selfplaySources(sp), ...ownSources(own)];
  const dropped: Drop[] = [];
  let drills: any[] = [];
  for (const src of sources) {
    const r = make(src);
    if ('reason' in r) { dropped.push({ id: src.base.id, reason: r.reason, detail: r.detail }); continue; }
    const B = r.firstB, lv: [string, number][] = [];
    if (src.base.kind === 'own' || src.base.kind === 'page') lv.push([src.base.kind === 'page' ? '淺' : '深', 0]);
    else {
      const sh = Math.max(0, B - REWIND.shallow);
      lv.push(['淺', sh]);
      if (B >= REWIND.deepFrom && sh > 0) lv.push(['深', 0]);
    }
    for (const [label, s] of lv) {
      const d = cut(src, r, s, label);
      if ('reason' in d && !('mode' in d)) dropped.push(d); else drills.push(d);
    }
  }
  // a Tetris on the way moves the start after it; re-check the replay
  drills = drills.map(d => {
    const n = skipTetris(d);
    if (n !== d) {
      const got = firstBuildable(n);
      if (got !== n.need || E.findBuild(E.newRun(n).board)) {
        dropped.push({ id: n.id, reason: 'replay_mismatch', detail: `after the Tetris: first buildable after ${got} pieces, not ${n.need}` });
        return null;
      }
    }
    return n;
  }).filter(Boolean);
  // exact duplicates keep the first
  const seen = new Map<string, string>();
  drills = drills.filter(d => {
    const k = JSON.stringify([d.start, d.queue.slice(0, d.need + 1), d.need, d.events]);
    if (seen.has(k)) { dropped.push({ id: d.id, reason: 'duplicate', detail: `the same start, queue and need as ${seen.get(k)}` }); return false; }
    seen.set(k, d.id);
    return true;
  });
  // garbage luck
  drills = drills.filter(d => {
    // only garbage that lands before the build can decide it
    const early = d.events.filter((e: any) => e.before <= d.need);
    if (!early.length) return true;
    const orig = [...new Set<number>(early.map((e: any) => e.col))].sort((a, b) => a - b);
    const ok = garbageColumns(d);
    if (!orig.every(c => ok.includes(c))) throw new Error(`cutcopy-drills: ${d.id} does not build with its own garbage columns`);
    if (ok.every(c => orig.includes(c))) {
      dropped.push({ id: d.id, reason: 'garbage_luck', detail: `builds only with the hole in column ${orig.join(', ')} of 0-9` });
      return false;
    }
    d.garbage_columns = ok;
    return true;
  });
  // the follow-up straight after the build, and the difficulty
  for (const d of drills) {
    const run = replayN(d, d.need);
    const fb = E.findBuild(run.board);
    E.applyLock(run, d, fb.state);
    d.second = !!E.findSecond(run.board, run.slot);
    d.difficulty = difficulty(d);
  }
  const ORDER = ['id', 'kind', 'title', 'note', 'mode', 'level', 'difficulty', 'need', 'start', 'queue', 'hold', 'events',
                 'garbage_columns', 'skippedTetris', 'target', 'second', 'solution', 'source'];
  drills = drills.map(d => {
    const o: any = {};
    for (const k of ORDER) if (k in d) o[k] = d[k];
    for (const k of Object.keys(d)) if (!(k in o)) throw new Error(`cutcopy-drills: unordered drill field ${k}`);
    return o;
  });
  const sessions = [...new Set<string>(facts.hits.filter((h: any) => h.qualifies).map((h: any) => h.session))].sort();
  const inputs: Record<string, string> = {};
  for (const p of [PATHS.transcription, PATHS.facts, PATHS.selfplay, PATHS.own, ...sessions.map(replayPath)]) inputs[rel(p)] = md5(p);
  const code: Record<string, string> = {};
  for (const p of CODE) code[rel(p)] = md5(p);
  return {
    schema: 'cutcopy-drills/1',
    report_eligible: false,
    constructed: true,
    practice: true,
    technique: 'cutcopy',
    means: 'Practice boards for 千鳥格子練習場 (docs/practice-cutcopy.html): boards a 千鳥格子 was built on (the qualifying corpus hits, cold-clear\'s self-play hits, our own engine-built design, the page\'s T-hole build), rewound to before its window could fire, each with the pieces that came next. Every lock is re-placed in the page\'s own practice engine, which decides whether the window fires; the windows are technique-facts.ts\'s prepare() output for both variants.',
    not_eligible_because: 'constructed practice boards, not corpus measurements: no claim id, no badge, no figure in any count of the corpus.',
    provenance: {
      selection: [
        `rewind: a drill starts ${REWIND.shallow} pieces before the first lock after which the window can fire (淺); when that lock is ${REWIND.deepFrom} or more pieces in, a second drill starts at the earliest board kept, at most ${REWIND.deep} pieces before the hit (深); our own design is played from empty and the page's build from its terrain`,
        'a Tetris on the way to the build moves the start to just after it (skippedTetris)',
        'exact duplicates (start, the queue to the build and one more, need, garbage events) keep the first',
        'garbage luck: a drill with garbage landing before its build is replayed with every hole in each of the 10 columns, and dropped when only its original column lets the build stand',
      ],
      difficulty: `the fewest pieces (any piece, hold allowed) after which the practice engine finds a window build, searched breadth first and exhaustively up to ${MIN_CAP} pieces; past ${MIN_CAP} it is the drill's need when that is ${MIN_CAP + 1} (the solution is a witness), else unknown (${UNKNOWN_LABEL})`,
      garbage_caveat: 'the garbage hole columns are the replay engine\'s seeded-RNG holes: they agree with the game\'s own counters and are never observed directly, so a corpus drill\'s garbage column is the engine\'s, not a recorded one. That is why a drill that builds only with that column is dropped.',
      engine: 'pipeline/cutcopy_practice_engine.js: SRS+ kicks and 180 rotation copied from the oracle crate\'s tables, the T-spin corner rule; not the reference engine, held to it by pipeline/openers/cutcopy-drills.test.ts',
    },
    inputs, code,
    sessions,
    windows,
    counts: { sources: sources.length, drills: drills.length, dropped: dropped.length },
    drills, dropped,
  };
}

export function serialise(out: ReturnType<typeof build>): string {
  const head = JSON.stringify({ ...out, drills: '__DRILLS__', dropped: '__DROPPED__' }, null, 1);
  const list = (xs: any[]) => xs.length ? `[\n${xs.map(x => JSON.stringify(x)).join(',\n')}\n]` : '[]';
  return head.replace('"__DRILLS__"', list(out.drills)).replace('"__DROPPED__"', list(out.dropped)) + '\n';
}
