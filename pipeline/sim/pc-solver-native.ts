/**
 * The Rust port of `pc-solver.ts` (`pipeline/sim/pc-solver-rs/`), loaded through bun:ffi. Every
 * answer equals the TS one, placement order and plan included (`pc-solver-native.test.ts`).
 *
 * `nativeCheck` is pc-miss.ts's `check` in one call: every frame up to `maxH`, a fresh `nodes`
 * budget per frame, a budget exhaustion marks the answer unknown and goes on to the next frame.
 * A memo is an opaque handle (`newMemo`/`freeMemo`), shared across the checks of one round-player
 * exactly like pc-miss.ts's Map; `null` uses a fresh one for that call.
 *
 * The library is built with `cargo build --release` when it is missing or older than its sources.
 */
import { dlopen, FFIType, type Pointer } from 'bun:ffi';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

export interface Placement { piece: string; cells: number[]; held: boolean }
export type NativeVerdict = { ok: true; H: number; plan: Placement[] } | { ok: false } | { ok: null };
export type Memo = Pointer;

const CRATE = join(import.meta.dir, 'pc-solver-rs');
const LIB = join(CRATE, 'target/release/libpc_solver_rs.so');

function stale(): boolean {
  if (!existsSync(LIB)) return true;
  const t = statSync(LIB).mtimeMs;
  const srcs = [join(CRATE, 'Cargo.toml'), ...readdirSync(join(CRATE, 'src')).map(f => join(CRATE, 'src', f))];
  return srcs.some(f => statSync(f).mtimeMs > t);
}
if (stale()) {
  const r = Bun.spawnSync(['cargo', 'build', '--release', '--manifest-path', join(CRATE, 'Cargo.toml')], { stderr: 'pipe' });
  if (r.exitCode !== 0) throw new Error(`cargo build failed:\n${r.stderr.toString()}`);
}

const { symbols: L } = dlopen(LIB, {
  pc_memo_new: { args: [], returns: FFIType.ptr },
  pc_memo_free: { args: [FFIType.ptr], returns: FFIType.void },
  pc_memo_len: { args: [FFIType.ptr], returns: FFIType.f64 },
  pc_check: {
    args: [FFIType.ptr, FFIType.u32, FFIType.u8, FFIType.u8, FFIType.ptr, FFIType.u32, FFIType.i32,
           FFIType.ptr, FFIType.i32, FFIType.i32, FFIType.i32, FFIType.ptr, FFIType.u32],
    returns: FFIType.i32,
  },
  pc_placements: {
    args: [FFIType.ptr, FFIType.u32, FFIType.u8, FFIType.i32, FFIType.i32, FFIType.ptr, FFIType.u32],
    returns: FFIType.i32,
  },
});

export const newMemo = (): Memo => L.pc_memo_new()!;
export const freeMemo = (m: Memo) => L.pc_memo_free(m);
export const memoSize = (m: Memo) => L.pc_memo_len(m);

// Typed arrays are passed as arguments, not as ptr() taken once: JSC may move a small typed
// array's storage, which left a cached pointer reading stale memory.
const OUT = new Int32Array(2 + 6 * 256);
const PL_OUT = new Int32Array(4 * 4096);
const ROWS = new Uint16Array(64);
let seqBuf = new Uint8Array(4096);

const code = (p: string | undefined) => (p ? p.charCodeAt(0) : 0);
function putRows(rows: number[]) {
  if (rows.length > ROWS.length) throw new Error('board too tall');
  for (let i = 0; i < rows.length; i++) ROWS[i] = rows[i]!;
}
function putSeq(seq: string) {
  if (seq.length > seqBuf.length) { seqBuf = new Uint8Array(seq.length * 2); }
  for (let i = 0; i < seq.length; i++) seqBuf[i] = seq.charCodeAt(i);
}

export function nativeCheck(rows: number[], cur: string, hold: string, seq: string, ptrIx: number, memo: Memo | null,
                            opts: { maxH: number; nodes: number; engine: boolean }): NativeVerdict {
  putRows(rows); putSeq(seq);
  const r = L.pc_check(ROWS, rows.length, code(cur), code(hold), seqBuf, seq.length, ptrIx, memo,
                       opts.maxH, opts.nodes, opts.engine ? 1 : 0, OUT, OUT.length);
  if (r === 0) return { ok: false };
  if (r === 2) return { ok: null };
  if (r !== 1) throw new Error(`pc_check returned ${r}`);
  const H = OUT[0]!, n = OUT[1]!, plan: Placement[] = [];
  for (let i = 0; i < n; i++) {
    const b = 2 + 6 * i;
    plan.push({ piece: String.fromCharCode(OUT[b]!), cells: [OUT[b + 2]!, OUT[b + 3]!, OUT[b + 4]!, OUT[b + 5]!], held: OUT[b + 1] === 1 });
  }
  return { ok: true, H, plan };
}

/** pc-solver.ts `placements` (or the engine movegen), for the equivalence test. */
export function nativePlacements(rows: number[], piece: string, H: number, engine = false): number[][] {
  putRows(rows);
  const n = L.pc_placements(ROWS, rows.length, code(piece), H, engine ? 1 : 0, PL_OUT, PL_OUT.length);
  if (n < 0) throw new Error('placements buffer too small');
  const out: number[][] = [];
  for (let i = 0; i < n; i++) out.push([PL_OUT[4 * i]!, PL_OUT[4 * i + 1]!, PL_OUT[4 * i + 2]!, PL_OUT[4 * i + 3]!]);
  return out;
}
