/**
 * The Rust port of `forecast.ts`'s `bestTspin` (`pipeline/sim/forecast-rs/`), loaded through bun:ffi.
 * `nativeBestTspin` returns what `bestTspinTs` returns, `rows` and `floor` included
 * (`forecast-native.test.ts`).
 *
 * Only a 40-row, 10-column board is ported; anything else returns `undefined` and the caller runs
 * the TS reference. A cell is filled when it is anything but `null`, which is the test every line of
 * the TS search makes (`!== null`).
 *
 * The library is built with `cargo build --release` the first time it is needed, when it is missing or
 * older than its sources, and loaded once.
 */
import { dlopen, FFIType } from 'bun:ffi';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import type { Board } from './vendor/core/srs.ts';

const CRATE = join(import.meta.dir, 'forecast-rs');
const LIB = join(CRATE, 'target/release/libforecast_rs.so');
const H = 40, W = 10;

function stale(): boolean {
  if (!existsSync(LIB)) return true;
  const t = statSync(LIB).mtimeMs;
  const srcs = [join(CRATE, 'Cargo.toml'), ...readdirSync(join(CRATE, 'src')).map(f => join(CRATE, 'src', f))];
  return srcs.some(f => statSync(f).mtimeMs > t);
}

const SYMBOLS = {
  forecast_best_tspin: { args: [FFIType.ptr, FFIType.ptr], returns: FFIType.i32 },
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

// Typed arrays are passed as arguments, not as ptr() taken once: JSC may move a small typed
// array's storage, which left a cached pointer reading stale memory (pc-solver-native.ts).
const CELLS = new Uint8Array(H * W);
const OUT = new Int32Array(7);

/** `bestTspin` on the native side, or `undefined` when the board is not 40 × 10. */
export function nativeBestTspin(board: Board): { lines: number; rows: number[]; floor: number } | null | undefined {
  if (board.length !== H) return undefined;
  for (let r = 0; r < H; r++) {
    const row = board[r]!;
    if (row.length !== W) return undefined;
    const o = r * W;
    for (let c = 0; c < W; c++) CELLS[o + c] = row[c] === null ? 0 : 1;
  }
  const rc = L().forecast_best_tspin(CELLS, OUT);
  if (rc !== 0) throw new Error(`forecast_best_tspin returned ${rc}`);
  if (OUT[0] === 0) return null;
  return { lines: OUT[0]!, rows: [OUT[2]!, OUT[3]!, OUT[4]!, OUT[5]!, OUT[6]!], floor: OUT[1]! };
}
