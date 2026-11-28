/**
 * The Rust port (`pipeline/sim/srs-bfs-rs`, bun:ffi) of the BFS over the vendored SRS primitives that
 * `cross-movegen.test.ts` (`ourReachable`) and `cross-tspin.test.ts` (`spinCandidates`) both run: the
 * `isValidPosition` / `tryMove` / `tryRotate` / `hardDrop` of `vendor/core/srs.ts`, expanded left, right,
 * down, CW, CCW from the spawn. It is OUR side of those two differentials only: cold-clear's answer (the
 * `cc-oracle` binary, `cc-tspin.ts`'s rule and kick index) and `detectTSpin` stay TypeScript, so neither
 * test ever compares a piece of code with its own port.
 *
 * `SRS_BFS_NATIVE` selects: unset or `on` = Rust (builds the crate on first use when it is missing or
 * older than its sources, and throws if that fails); `off` = the TS BFS each test still carries as the
 * reference; `auto` = Rust when the crate loads, else the TS BFS with a warning on stderr (for a runner that
 * may have no cargo — `oracle-image`). `srs-bfs-native.test.ts` holds the two answers equal.
 */
import { dlopen, FFIType, ptr } from 'bun:ffi';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import type { Board, ActivePiece } from './vendor/core/srs.ts';
import { tryMove, tryRotate, hardDrop, isValidPosition, setKickset } from './vendor/core/srs.ts';
import type { PieceType } from './vendor/core/types.ts';

const CRATE = join(import.meta.dir, 'srs-bfs-rs');
const LIB = join(CRATE, 'target/release/libsrs_bfs_rs.so');
const PIECE = 'ITOSZLJ';
const W = 10, H = 40;
const CAP = 1 << 18;

const SYMBOLS = {
  srs_bfs: { args: [FFIType.ptr, FFIType.u32, FFIType.u32, FFIType.i32, FFIType.i32, FFIType.u32, FFIType.ptr, FFIType.u32], returns: FFIType.i32 },
} as const;
let lib: ReturnType<typeof dlopen<typeof SYMBOLS>>['symbols'] | null = null;
const out = new Int32Array(CAP);
const grid = new Uint8Array(W * H);

function stale(): boolean {
  if (!existsSync(LIB)) return true;
  const t = statSync(LIB).mtimeMs;
  const srcs = [join(CRATE, 'Cargo.toml'), ...readdirSync(join(CRATE, 'src')).map(f => join(CRATE, 'src', f))];
  return srcs.some(f => statSync(f).mtimeMs > t);
}
function load() {
  if (lib) return lib;
  if (stale()) {
    const r = Bun.spawnSync(['cargo', 'build', '--release', '--manifest-path', join(CRATE, 'Cargo.toml')], { stderr: 'pipe' });
    if (r.exitCode !== 0) throw new Error(`cargo build failed:\n${r.stderr.toString()}`);
  }
  lib = dlopen(LIB, SYMBOLS).symbols;
  return lib;
}

let resolved: boolean | null = null;
/** Whether the callers should use the Rust search (resolved once per process). */
export function srsBfsNative(): boolean {
  if (resolved !== null) return resolved;
  const m = process.env.SRS_BFS_NATIVE ?? 'on';
  if (m === 'off') return (resolved = false);
  if (m === 'auto') {
    try { load(); return (resolved = true); }
    catch (e) { console.error(`SRS_BFS_NATIVE=auto: Rust search unavailable, using the TS BFS (${String(e).split('\n')[0]})`); return (resolved = false); }
  }
  if (m !== 'on') throw new Error(`SRS_BFS_NATIVE=${m}: expected on, off or auto`);
  load();
  return (resolved = true);
}

function run(board: ReadonlyArray<ReadonlyArray<string | null>>, type: string, plus: boolean,
             col: number, row: number, mode: 0 | 1): Int32Array {
  const S = load();
  for (let y = 0; y < H; y++) { const r = board[y]!; for (let x = 0; x < W; x++) grid[y * W + x] = r[x] ? 1 : 0; }
  const p = PIECE.indexOf(type);
  if (p < 0) throw new Error(`srs-bfs-native: piece ${type}`);
  const n = S.srs_bfs(ptr(grid), p, plus ? 1 : 0, col, row, mode, ptr(out), CAP);
  if (n < 0) throw new Error(`srs-bfs-native: srs_bfs returned ${n}`);
  return out.subarray(0, n);
}

/** Every distinct hard-dropped state of the BFS from the spawn, as [rotation, col, row] in first-seen order. */
export function nativeDrops(board: ReadonlyArray<ReadonlyArray<string | null>>, type: string,
                            col = 3, row = 18, plus = false): [number, number, number][] {
  const d = run(board, type, plus, col, row, 0);
  const o: [number, number, number][] = [];
  for (let i = 0; i < d.length; i += 3) o.push([d[i]!, d[i + 1]!, d[i + 2]!]);
  return o;
}

/**
 * Every rotation that rests where it lands (cannot fall one row), over the visited states in BFS order,
 * CW before CCW: [preRot, preCol, preRow, postRot, postCol, postRow], not deduplicated.
 */
export function nativeSpinEdges(board: ReadonlyArray<ReadonlyArray<string | null>>, type: string,
                                col = 3, row = 18, plus = false): number[][] {
  const d = run(board, type, plus, col, row, 1);
  const o: number[][] = [];
  for (let i = 0; i < d.length; i += 6) o.push([d[i]!, d[i + 1]!, d[i + 2]!, d[i + 3]!, d[i + 4]!, d[i + 5]!]);
  return o;
}

// ── the TS reference: the BFS exactly as both tests carried it before the port ───────────────────

function bfsTs(board: Board, type: PieceType, col: number, row: number, visit: (cur: ActivePiece) => void): void {
  const spawn: ActivePiece = { type, rotation: 0, col, row };
  if (!isValidPosition(board, spawn)) return;
  const seen = new Set<string>();
  const key = (p: ActivePiece) => `${p.rotation}:${p.col}:${p.row}`;
  const q: ActivePiece[] = [spawn];
  seen.add(key(spawn));
  for (let h = 0; h < q.length; h++) {
    const cur = q[h]!;
    visit(cur);
    for (const n of [tryMove(board, cur, -1, 0), tryMove(board, cur, 1, 0), tryMove(board, cur, 0, 1),
                     tryRotate(board, cur, 1), tryRotate(board, cur, -1)]) {
      if (n && !seen.has(key(n))) { seen.add(key(n)); q.push(n); }
    }
  }
}

/** `nativeDrops`' answer from the vendored TS primitives (sets the kickset, as both tests did). */
export function tsDrops(board: Board, type: PieceType, col = 3, row = 18, plus = false): [number, number, number][] {
  setKickset(plus ? 'SRS+' : 'SRS');
  const seen = new Set<string>(), o: [number, number, number][] = [];
  bfsTs(board, type, col, row, cur => {
    const d = hardDrop(board, cur);
    const k = `${d.rotation}:${d.col}:${d.row}`;
    if (!seen.has(k)) { seen.add(k); o.push([d.rotation, d.col, d.row]); }
  });
  return o;
}

/** `nativeSpinEdges`' answer from the vendored TS primitives. */
export function tsSpinEdges(board: Board, type: PieceType, col = 3, row = 18, plus = false): number[][] {
  setKickset(plus ? 'SRS+' : 'SRS');
  const o: number[][] = [];
  bfsTs(board, type, col, row, cur => {
    for (const dir of [1, -1] as const) {
      const post = tryRotate(board, cur, dir);
      if (!post) continue;
      if (tryMove(board, post, 0, 1) !== null) continue;
      o.push([cur.rotation, cur.col, cur.row, post.rotation, post.col, post.row]);
    }
  });
  return o;
}

/** The answer both tests use: Rust unless `SRS_BFS_NATIVE=off`. */
export function drops(board: Board, type: PieceType, col = 3, row = 18, plus = false) {
  return srsBfsNative() ? nativeDrops(board, type, col, row, plus) : tsDrops(board, type, col, row, plus);
}
export function spinEdges(board: Board, type: PieceType, col = 3, row = 18, plus = false) {
  return srsBfsNative() ? nativeSpinEdges(board, type, col, row, plus) : tsSpinEdges(board, type, col, row, plus);
}
