/**
 * The Rust port of `route-demos.ts`'s `reach()` search (`pipeline/sim/oracle-rs/src/reach.rs`, beside the
 * crate's copy of the Triangle engine's kick tables), loaded through bun:ffi. `searchNative` returns the
 * same Map as the TS search (`searchAll(…, 'ts')`) — every resting placement's cells → its paths, in discovery order —
 * which `reach-native.test.ts` holds equal on every (board, piece) the demo emitters ask.
 *
 * Only what the demo engine does is ported: SRS+ kicks, the "T-spins" rule, a 10 × 40 board.
 * `nativeEligible` refuses any other engine, and `route-demos.ts` then runs the TS search. The start state
 * (where `initiatePiece` put the piece, clutch and all) is the TS engine's own, passed in.
 *
 * The library is the oracle's (`oracle-native.ts` builds it the same way: `cargo build --release` on first
 * use, when it is missing or older than its sources).
 */
import { dlopen, FFIType, ptr } from 'bun:ffi';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const CRATE = join(import.meta.dir, 'oracle-rs');
const LIB = join(CRATE, 'target/release/liboracle_rs.so');
/** The crate's piece order (src/data.rs). */
const PIECE = 'ijlostz';
const EDGE = ['L', 'R', 'D', 'CW', 'CCW', '180'] as const;
const SPIN = [null, 'mini', 'normal'] as const;
const W = 10, H = 40;

function stale(): boolean {
  if (!existsSync(LIB)) return true;
  const t = statSync(LIB).mtimeMs;
  const srcs = [join(CRATE, 'Cargo.toml'), ...readdirSync(join(CRATE, 'src')).map(f => join(CRATE, 'src', f))];
  return srcs.some(f => statSync(f).mtimeMs > t);
}

const SYMBOLS = {
  reach_run: { args: [FFIType.ptr, FFIType.u32, FFIType.f64, FFIType.f64, FFIType.u32, FFIType.u32], returns: FFIType.ptr },
  reach_out_len: { args: [FFIType.ptr], returns: FFIType.f64 },
  reach_out_copy: { args: [FFIType.ptr, FFIType.ptr, FFIType.u32], returns: FFIType.i32 },
  reach_free: { args: [FFIType.ptr], returns: FFIType.void },
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

/** Whether the native search answers for this engine and board exactly as the TS one would. */
export function nativeEligible(eng: any, state: (string | null)[][]): boolean {
  return eng.kickTableName === 'SRS+' && eng.gameOptions?.spinBonuses === 'T-spins'
    && eng.board?.width === W && eng.board?.fullHeight === H
    && state.length === H && state.every(r => r.length === W);
}

export interface NPath { edges: string[]; spin: string | null; cells: number[] }

/** The whole search from (sx, sy, sr): per resting placement's cells (sorted, joined), its paths. */
export function searchNative(state: (string | null)[][], piece: string, sx: number, sy: number, sr: number,
                             no180: boolean): Map<string, NPath[]> {
  const S = L();
  const p = PIECE.indexOf(piece.toLowerCase());
  if (p < 0) throw new Error(`reach-native: piece ${piece}`);
  const board = new Uint8Array(W * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (state[y]![x]) board[y * W + x] = 1;
  const h = S.reach_run(ptr(board), p, sx, sy, sr, no180 ? 1 : 0);
  if (h == null) throw new Error('reach-native: reach_run returned null');
  let d: Uint16Array;
  try {
    const n = S.reach_out_len(h);
    d = new Uint16Array(Math.max(1, n));
    if (S.reach_out_copy(h, ptr(d), n) !== n) throw new Error('reach-native: output copy failed');
    d = d.subarray(0, n);
  } finally { S.reach_free(h); }
  const found = new Map<string, NPath[]>();
  for (let i = 0; i < d.length;) {
    const cells = [d[i]!, d[i + 1]!, d[i + 2]!, d[i + 3]!];
    const spin = SPIN[d[i + 4]!]!;
    const ne = d[i + 5]!;
    const edges: string[] = [];
    for (let j = 0; j < ne; j++) edges.push(EDGE[d[i + 6 + j]!]!);
    i += 6 + ne;
    const ck = cells.join(',');
    let list = found.get(ck);
    if (!list) found.set(ck, list = []);
    list.push({ edges, spin, cells });
  }
  return found;
}
