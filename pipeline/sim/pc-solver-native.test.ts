/**
 * The Rust port (`pc-solver-native.ts`) against `pc-solver.ts`, on every board of one session's
 * replay-facts walked the way pc-miss.ts `build()` walks them:
 *   1. `placements`: for every pre-board <= MAXH rows, every piece and every frame H, the native
 *      list equals the TS list, order included;
 *   2. `check`: pc-miss.ts's `check` (copied here: it is not exported) against `nativeCheck`, the
 *      memo shared across every check of a round-player in both, over every state that fits, in
 *      order; plus the preview check (sliced sequence, fresh memo) on every such state, and the
 *      engine-movegen check where pc-miss.ts would run one.
 * Equality is JSON.stringify of the verdicts. Timing TS vs native is printed for 2.
 */
import { expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import { placeCells, WIDTH } from './emit-replay.ts';
import { solve, frames, height, placements, setMovegen, type Placement } from './pc-solver.ts';
import { enginePlacements } from './pc-engine-gen.ts';
import { MAXH, PREVIEW } from './pc-miss.ts';
import { nativeCheck, nativePlacements, newMemo, freeMemo } from './pc-solver-native.ts';

const SESSION = process.env.PC_NATIVE_SESSION ?? '2026-10-20';
/** The TS side of the check test takes about 13 minutes over a whole night, so by default it runs over
 *  the first SAMPLE round-players; PC_NATIVE_FULL=1 runs them all. The md5-pinned artefacts are the
 *  full-corpus check: pc-miss.test.ts rebuilds 10-20 natively, byte for byte. */
const SAMPLE = process.env.PC_NATIVE_FULL ? Infinity : 4;
const NODES = 3_000_000;
const PIECES = 'IOTSZJL';

type V = { ok: true; H: number; plan: Placement[] } | { ok: false } | { ok: null };
/** pc-miss.ts `check`, verbatim. */
function tsCheck(rows: number[], cur: string, hold: string, seq: string, ptr: number, memo: Map<string, any>): V {
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

const toMasks = (b: (string | null)[][]) => {
  const m = b.map(r => r.reduce((a, c, x) => a | (c != null ? 1 << x : 0), 0));
  let h = m.length; while (h && !m[h - 1]) h--;
  return m.slice(0, h);
};

interface St { pre: number[]; cur: string; hold: string; ptr: number; garbageIn: boolean }
/** pc-miss.ts build()'s walk, reduced to what the checks read. */
function states(dir: string): { seq: string; st: St[] }[] {
  const RF = JSON.parse(readFileSync(`${dir}/sim/replay-facts.json`, 'utf8'));
  const out: { seq: string; st: St[] }[] = [];
  for (const rd of RF.rounds) for (const P of rd.players) {
    if (!P.admission.ok) continue;
    const seq: string = rd.seq;
    const board: (string | null)[][] = Array.from({ length: 40 }, () => new Array(WIDTH).fill(null));
    let cur = seq[0]!, ptr = 1, hold = '';
    const st: St[] = [];
    for (const lk of P.locks) {
      for (const [col, amt] of lk[4]) {
        const rows = Array.from({ length: amt }, () => { const r = new Array<string | null>(WIDTH).fill('G'); r[col] = null; return r; });
        board.splice(0, 0, ...rows); board.splice(40 - amt - 1, amt);
      }
      st.push({ pre: toMasks(board), cur, hold, ptr, garbageIn: lk[4].length > 0 });
      if (lk[5]) { if (hold === '') { hold = cur; cur = seq[ptr++]!; } else { const t = hold; hold = cur; cur = t; } }
      for (const c of placeCells(cur, lk[1])) board[Math.floor(c / WIDTH)]![c % WIDTH] = cur;
      const full: number[] = [];
      for (let y = 0; y < 40; y++) if (board[y]!.every(v => v != null)) full.push(y);
      for (let k = full.length - 1; k >= 0; k--) { board.splice(full[k]!, 1); board.push(new Array(WIDTH).fill(null)); }
      cur = seq[ptr++]!;
    }
    out.push({ seq, st });
  }
  return out;
}

const RP = states(`sessions/${SESSION}`);

test('placements: native list equals pc-solver.ts placements, order included', () => {
  let n = 0, bad = 0;
  for (const { st } of RP) for (const s of st) {
    if (height(s.pre) > MAXH) continue;
    for (const H of frames(s.pre, MAXH)) for (const p of PIECES) {
      const a = JSON.stringify(placements(s.pre, p, H)), b = JSON.stringify(nativePlacements(s.pre, p, H));
      n++;
      if (a !== b) { bad++; if (bad < 5) console.error('placements differ', s.pre, p, H, a, b); }
    }
  }
  console.log(`placements compared: ${n}`);
  expect(n).toBeGreaterThan(1000);
  expect(bad).toBe(0);
}, 600_000);

test('check: native equals pc-miss.ts check, shared memo per round-player', () => {
  let n = 0, bad = 0, tTs = 0, tNa = 0, nPrev = 0, nEng = 0;
  const kinds: Record<string, number> = {};
  const cmp = (a: V, b: unknown, what: string) => {
    const x = JSON.stringify(a), y = JSON.stringify(b);
    if (x !== y) { bad++; if (bad < 5) console.error(what, x, y); }
  };
  for (const { seq, st } of RP.slice(0, SAMPLE)) {
    const memo = new Map<string, any>();
    const nm = newMemo();
    const v: (V | null)[] = [];
    for (const s of st) {
      if (!fits(s.pre)) { v.push(null); continue; }
      let t = performance.now();
      const a = tsCheck(s.pre, s.cur, s.hold, seq, s.ptr, memo);
      tTs += performance.now() - t; t = performance.now();
      const b = nativeCheck(s.pre, s.cur, s.hold, seq, s.ptr, nm, { maxH: MAXH, nodes: NODES, engine: false });
      tNa += performance.now() - t;
      cmp(a, b, 'shared'); n++; v.push(a);
      kinds[String(a.ok)] = (kinds[String(a.ok)] ?? 0) + 1;
      // the preview check: sliced sequence, fresh memo
      const ps = seq.slice(0, s.ptr + PREVIEW);
      t = performance.now();
      const c = tsCheck(s.pre, s.cur, s.hold, ps, s.ptr, new Map());
      tTs += performance.now() - t; t = performance.now();
      const d = nativeCheck(s.pre, s.cur, s.hold, ps, s.ptr, null, { maxH: MAXH, nodes: NODES, engine: false });
      tNa += performance.now() - t;
      cmp(c, d, 'preview'); nPrev++;
    }
    freeMemo(nm);
    // the engine re-check, where pc-miss.ts runs one: a PC possible before a lock and not after it
    for (let i = 0; i + 1 < st.length; i++) {
      const a = v[i], b = v[i + 1], s = st[i + 1]!;
      if (a?.ok !== true || b?.ok === true || b == null || b.ok === null || s.garbageIn) continue;
      setMovegen(enginePlacements);
      const e = tsCheck(s.pre, s.cur, s.hold, seq, s.ptr, new Map());
      setMovegen(null);
      const f = nativeCheck(s.pre, s.cur, s.hold, seq, s.ptr, null, { maxH: MAXH, nodes: NODES, engine: true });
      cmp(e, f, 'engine'); nEng++;
    }
  }
  console.log(`checks: ${n} shared-memo (${JSON.stringify(kinds)}), ${nPrev} preview, ${nEng} engine; `
    + `TS ${(tTs / 1000).toFixed(1)} s, native ${(tNa / 1000).toFixed(1)} s, ${(tTs / tNa).toFixed(1)}x`);
  expect(n).toBeGreaterThan(SAMPLE === Infinity ? 100 : 10);
  expect(bad).toBe(0);
}, 3_600_000);
