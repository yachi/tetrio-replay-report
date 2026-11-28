/**
 * The Rust port of `cutcopy-drills.ts`'s `minNeed` search (`pipeline/sim/cutcopy-rs`, a dependency-free crate of its own: the practice
 * engine's placement BFS, lock, window match and carry, and the breadth-first search over pieces), loaded through
 * bun:ffi. It builds the way `forecast-native.ts` does: `cargo build --release` on first use, when the library is missing or
 * older than its sources. (Its own crate and not oracle-rs, because the TST opener artefacts pin the md5 of every
 * oracle-rs source, and a new file there would stale hours of recount.) `minNeedTs` in `cutcopy-drills.ts` stays the reference;
 * `CUTCOPY_NATIVE=off` selects it, and `cutcopy-native.test.ts` holds the two equal.
 */
import { dlopen, FFIType, ptr } from 'bun:ffi';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const CRATE = join(import.meta.dir, 'cutcopy-rs');
const LIB = join(CRATE, 'target/release/libcutcopy_rs.so');
const PIECES = 'IJLOSTZ';

function stale(): boolean {
  if (!existsSync(LIB)) return true;
  const t = statSync(LIB).mtimeMs;
  const srcs = [join(CRATE, 'Cargo.toml'), ...readdirSync(join(CRATE, 'src')).map(f => join(CRATE, 'src', f))];
  return srcs.some(f => statSync(f).mtimeMs > t);
}

const SYMBOLS = {
  cutcopy_min_need: {
    args: [FFIType.ptr, FFIType.ptr, FFIType.u32, FFIType.u32, FFIType.ptr, FFIType.u32, FFIType.ptr, FFIType.u32, FFIType.u32, FFIType.u32],
    returns: FFIType.i32,
  },
} as const;
let lib: ReturnType<typeof dlopen<typeof SYMBOLS>>['symbols'] | null = null;
function L() {
  if (lib) return lib;
  if (stale()) {
    const r = Bun.spawnSync(['cargo', 'build', '--release', '--manifest-path', join(CRATE, 'Cargo.toml')], { stderr: 'pipe' });
    if (r.exitCode !== 0) throw new Error(`cargo build failed:\n${r.stderr.toString()}`);
  }
  lib = dlopen(LIB, SYMBOLS).symbols;
  return lib;
}

/** the windows as the crate reads them: n, then per window T (4 × r,c), cells (n × r,c,v: '#' 0, '.' 1, 'T' 2), followup (n × r,c) */
export function flattenWindows(ws: any[]): Int32Array {
  const a: number[] = [ws.length];
  for (const w of ws) {
    if (w.T.length !== 4) throw new Error('a window T is not four cells');
    for (const t of w.T) a.push(t.r, t.c);
    a.push(w.cells.length);
    for (const q of w.cells) {
      const v = q.v === '#' ? 0 : q.v === '.' ? 1 : q.v === 'T' ? 2 : -1;
      if (v < 0) throw new Error(`window cell ${q.v}`);
      a.push(q.r, q.c, v);
    }
    a.push(w.followup.length);
    for (const f of w.followup) a.push(f.r, f.c);
  }
  return Int32Array.from(a);
}

/** `minNeed`'s answer: the depth, or `{ beyond, cut }`. `board` is `E.newRun(pz).board` (null = empty). */
export function minNeedNative(pz: any, board: (string | null)[][], hold: string | null, windows: any[], cap: number, frontier: number):
  number | { beyond: number; cut: boolean } {
  const b = new Uint8Array(400);
  for (let y = 0; y < 40; y++) for (let x = 0; x < 10; x++) b[y * 10 + x] = board[y]![x] !== null ? 1 : 0;
  const q = Uint8Array.from(pz.queue as string[], (c: string) => { const i = PIECES.indexOf(c); if (i < 0) throw new Error(`piece ${c}`); return i; });
  const ev = (pz.events || []).filter((e: any) => e.kind === 'garbage');
  const evs = Int32Array.from(ev.flatMap((e: any) => [e.before, e.n, e.col]).concat([0]));
  const wins = flattenWindows(windows);
  const h = hold == null ? 255 : PIECES.indexOf(hold);
  const r = L().cutcopy_min_need(ptr(b), ptr(q.length ? q : new Uint8Array(1)), q.length, h, ptr(evs), ev.length, ptr(wins), wins.length, cap, frontier);
  if (r >= 0) return r;
  const v = -1 - r;
  return { beyond: v >> 1, cut: (v & 1) === 1 };
}
