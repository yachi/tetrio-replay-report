/**
 * Which placement made a perfect clear impossible?
 *
 *   REPLAY_DIR=sessions/<date> bun pipeline/sim/pc-miss.ts --out <json>
 *
 * Two kinds of WINDOW per (round, player), each at most `SPAN` locks long and ending at the first
 * Perfect Clear inside it:
 *   - `tst`: after the opener's T-spin Triple (a full spin clearing 3 at lock <= 21, 0-based), where
 *     the opener routes draw their 8-line PC;
 *   - `pc`:  after each Perfect Clear (the next PC, a DPC or a second PC).
 * Inside a window every board at most `MAXH` rows tall is handed to the solver (`pc-solver.ts`),
 * which answers with the round's own dealt sequence (hindsight). A MISS is a lock i where a PC was
 * possible before it and not after it, lock i did not itself perfect-clear, and lock i+1 brought no
 * garbage (garbage is reported separately). Every "not after" is re-checked with the engine's own
 * movegen (`pc-engine-gen.ts`, which has 180); a miss is then marked `in_preview` when a PC existed
 * using only the current piece, the hold and the five pieces of the preview, and `verified` when
 * lock i+1 is inside the round's verified prefix.
 *
 * Simulator output on the replay-facts timeline: quarantined, like every sim/ artefact — no claim
 * id, no badge, no figure in any report.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { placeCells, WIDTH } from './emit-replay.ts';
import { solve, frames, height, setMovegen, type Placement } from './pc-solver.ts';
import { enginePlacements } from './pc-engine-gen.ts';

type Lock = [number, number | number[], number, number, [number, number][], number, number, number];

const argv = process.argv.slice(2);
const dir = process.env.REPLAY_DIR!;
const outPath = argv[argv.indexOf('--out') + 1]!;
const RF = JSON.parse(readFileSync(`${dir}/sim/replay-facts.json`, 'utf8'));
export const MAXH = Number(process.env.PC_MAXH ?? 6);
export const SPAN = 12;
export const PREVIEW = 5;
const NODES = 3_000_000;

const toMasks = (b: (string | null)[][]) => {
  const m = b.map(r => r.reduce((a, c, x) => a | (c != null ? 1 << x : 0), 0));
  let h = m.length; while (h && !m[h - 1]) h--;
  return m.slice(0, h);
};

type V = { ok: true; H: number; plan: Placement[] } | { ok: false } | { ok: null };
function check(rows: number[], cur: string, hold: string, seq: string, ptr: number, memo: Map<string, any>): V {
  let unknown = false;
  for (const H of frames(rows, MAXH)) {
    let v;
    try { v = solve(rows, H, cur, hold, seq, ptr, memo, { nodes: NODES }); }
    catch { unknown = true; continue; }
    if (v.ok === true) return { ok: true, H, plan: v.plan };
    if (v.ok === null) unknown = true;
  }
  return unknown ? { ok: null } : { ok: false };
}
const fits = (rows: number[]) => height(rows) <= MAXH && frames(rows, MAXH).length > 0;

const out: any[] = [];
const t0 = performance.now();
for (const rd of RF.rounds) {
  for (const P of rd.players) {
    if (!P.admission.ok) continue;
    const seq: string = rd.seq;
    const locks: Lock[] = P.locks;
    const board: (string | null)[][] = Array.from({ length: 40 }, () => new Array(WIDTH).fill(null));
    let cur = seq[0]!, ptr = 1, hold = '';
    const st: any[] = [];
    for (let i = 0; i < locks.length; i++) {
      const lk = locks[i]!;
      for (const [col, amt] of lk[4]) {
        const rows = Array.from({ length: amt }, () => { const r = new Array<string | null>(WIDTH).fill('G'); r[col] = null; return r; });
        board.splice(0, 0, ...rows); board.splice(40 - amt - 1, amt);
      }
      const pre = toMasks(board);
      const grid = board.slice(0, MAXH).map(r => r.map(c => c ?? '.').join(''));
      const s: any = { i, pre, grid, cur, hold, ptr, garbageIn: lk[4].length > 0, held: !!lk[5], lines: lk[2], spin: lk[3] };
      if (lk[5]) { if (hold === '') { hold = cur; cur = seq[ptr++]!; } else { const t = hold; hold = cur; cur = t; } }
      s.piece = cur;
      s.cells = placeCells(cur, lk[1]);
      for (const c of s.cells) board[Math.floor(c / WIDTH)]![c % WIDTH] = cur;
      const full: number[] = [];
      for (let y = 0; y < 40; y++) if (board[y]!.every(v => v != null)) full.push(y);
      for (let k = full.length - 1; k >= 0; k--) { board.splice(full[k]!, 1); board.push(new Array(WIDTH).fill(null)); }
      cur = seq[ptr++]!;
      s.pc = board[0]!.every(v => v == null);
      st.push(s);
    }
    // windows
    const wins: { kind: string; start: number; end: number }[] = [];
    const tst = st.findIndex(s => s.i <= 21 && s.spin === 2 && s.lines === 3);
    const pcs = st.filter(s => s.pc).map(s => s.i);
    const endAt = (start: number) => { const p = pcs.find(x => x > start); return Math.min(p ?? Infinity, start + SPAN, st.length - 1); };
    if (tst >= 0) wins.push({ kind: 'tst', start: tst, end: endAt(tst) });
    for (const p of pcs) if (p + 1 < st.length) wins.push({ kind: 'pc', start: p, end: endAt(p) });
    const memo = new Map<string, any>();
    const verdict = (s: any): V | null => {
      if (s.v !== undefined) return s.v;
      s.v = fits(s.pre) ? check(s.pre, s.cur, s.hold, seq, s.ptr, memo) : null;
      return s.v;
    };
    const verified = P.prefix.verified_to;
    const rw: any[] = [];
    for (const w of wins) {
      const ev: any[] = [];
      for (let i = w.start + 1; i <= w.end; i++) ev.push(verdict(st[i]));
      const pcLock = st[w.end]!.pc && w.end > w.start ? w.end : null;
      const misses: any[] = [];
      for (let i = w.start + 1; i < w.end; i++) {
        const a = st[i], b = st[i + 1];
        if (a.v?.ok !== true || a.pc || b.v?.ok === true) continue;
        const m: any = { i, verified: i + 1 < verified };
        if (b.garbageIn) m.lost_to = 'garbage';
        else if (b.v?.ok === null) m.lost_to = 'unknown';
        else {
          let e: V = { ok: false };
          if (fits(b.pre)) { setMovegen(enginePlacements); e = check(b.pre, b.cur, b.hold, seq, b.ptr, new Map()); setMovegen(null); }
          m.lost_to = e.ok === true ? 'engine_disagrees' : e.ok === null ? 'unknown' : 'placement';
        }
        if (m.lost_to === 'placement') {
          const vis = check(a.pre, a.cur, a.hold, seq.slice(0, a.ptr + PREVIEW), a.ptr, new Map());
          m.in_preview = vis.ok === true;
          m.state = { grid: a.grid, cur: a.cur, hold: a.hold, next: seq.slice(a.ptr, a.ptr + PREVIEW), piece: a.piece, held: a.held, cells: a.cells, lines: a.lines };
          m.after = b.grid;
          m.plan = (vis.ok === true ? vis : a.v).plan;
          m.plan_H = (vis.ok === true ? vis : a.v).H;
        }
        misses.push(m);
      }
      const evaluated = ev.filter(v => v != null).length;
      const outcome = pcLock != null ? 'pc'
        : misses.some(m => m.lost_to === 'placement') ? 'lost_placement'
        : misses.length ? 'lost_other'
        : !ev.some(v => v?.ok === true) ? (evaluated ? 'never' : 'not_evaluated') : 'possible_to_end';
      rw.push({ ...w, pcLock, outcome, misses });
    }
    out.push({ match: rd.match, round: rd.round, file: rd.file, user: P.user, verified_to: verified, windows: rw });
  }
  console.error(`m${rd.match}r${rd.round + 1} ${Math.round((performance.now() - t0) / 1000)}s`);
}
writeFileSync(outPath, JSON.stringify({ session: RF.session, maxh: MAXH, span: SPAN, preview: PREVIEW, rounds: out }));
