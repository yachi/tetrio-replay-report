/**
 * The Rust port of `oracle-source.ts`'s replay (`pipeline/sim/oracle-rs/`, the vendored Triangle engine
 * restricted to the paths that harness reaches), loaded through bun:ffi. `runCaseOracleNative` returns a
 * SimResult whose JSON.stringify equals `runCaseOracleTs`'s byte for byte (`oracle-native.test.ts`).
 *
 * Only the rule set the corpus plays is ported. Anything else is refused here with an `unsupported`
 * error before the engine runs, never approximated: the TS engine stays the reference for those.
 *
 * The library is built with `cargo build --release` the first time it is needed, when it is missing or
 * older than its sources, and loaded once.
 */
import { dlopen, FFIType } from 'bun:ffi';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { GARBAGE, type SimResult } from './sim.ts';
import type { Board } from './vendor/core/srs.ts';
import type { PieceType } from './vendor/core/types.ts';

const CRATE = join(import.meta.dir, 'oracle-rs');
const LIB = join(CRATE, 'target/release/liboracle_rs.so');

/** Piece order of the crate (src/data.rs, from gen-oracle-rs-data.ts): code = index (+1 on a board). */
const PIECE = ['I', 'J', 'L', 'O', 'S', 'T', 'Z'] as PieceType[];
const SPIN = ['none', 'mini', 'full'] as const;
const KEY: Record<string, number> = {
  moveLeft: 0, moveRight: 1, softDrop: 2, rotateCCW: 3, rotateCW: 4, rotate180: 5, hardDrop: 6, hold: 7,
};
const NO_KEY = 255;   // any other key: the engine runs its processSubframe and nothing else
const SNAP = 400;     // 40 rows × 10 columns

function stale(): boolean {
  if (!existsSync(LIB)) return true;
  const t = statSync(LIB).mtimeMs;
  const srcs = [join(CRATE, 'Cargo.toml'), ...readdirSync(join(CRATE, 'src')).map(f => join(CRATE, 'src', f))];
  return srcs.some(f => statSync(f).mtimeMs > t);
}

const SYMBOLS = {
  oracle_run: { args: [FFIType.ptr, FFIType.u32, FFIType.ptr, FFIType.u32], returns: FFIType.ptr },
  oracle_out_len: { args: [FFIType.ptr], returns: FFIType.f64 },
  oracle_out_copy: { args: [FFIType.ptr, FFIType.ptr, FFIType.u32], returns: FFIType.i32 },
  oracle_free: { args: [FFIType.ptr], returns: FFIType.void },
  oracle_log1p: { args: [FFIType.f64], returns: FFIType.f64 },
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

/** The crate's `ln_1p`, for the bit-identity test against Math.log1p. */
export const nativeLog1p = (x: number): number => L().oracle_log1p(x);

const unsupported = (what: string): never => { throw new Error(`oracle-native: unsupported ${what}`); };
const num = (v: unknown, what: string): number =>
  (typeof v === 'number' && Number.isFinite(v) ? v : unsupported(`${what} = ${String(v)}`));
const is = (v: unknown, want: unknown, what: string) => { if (v !== want) unsupported(`${what} = ${String(v)}`); };

/** The engine options in the crate's `Opts` field order (src/ffi.rs). */
function encodeOpts(flat: any, maxF: number): Float64Array {
  is(flat.kickset, 'SRS+', 'kickset'); is(flat.bagtype, '7-bag', 'bagtype'); is(flat.spinbonuses, 'T-spins', 'spinbonuses');
  is(flat.combotable, 'multiplier', 'combotable'); is(flat.garbagetargetbonus, 'none', 'garbagetargetbonus');
  is(flat.roundmode, 'down', 'roundmode'); is(flat.boardwidth, 10, 'boardwidth'); is(flat.boardheight, 20, 'boardheight');
  if (flat.usebombs) unsupported('usebombs'); if (flat.garbagespecialbonus) unsupported('garbagespecialbonus');
  if (flat.b2bcharging) unsupported('b2bcharging'); if (flat.can_undo) unsupported('can_undo'); if (flat.can_retry) unsupported('can_retry');
  // createEngine is called without a date, so the engine reads the clock: the 2025-05-06 garbage queue, no opener phase
  const now = new Date();
  if (!(now > new Date('2025-05-06T15:00:00-04:00')) || now < new Date(2025, 1, 16)) unsupported('date era');
  const h = flat.handling;
  if (h == null || typeof h !== 'object') unsupported('handling');
  is(h.irs, 'tap', 'handling.irs'); is(h.ihs, 'tap', 'handling.ihs');
  const B = (v: unknown) => (v ? 1 : 0);
  return new Float64Array([
    num(flat.seed, 'seed'), num(flat.gameid, 'gameid'),
    num(flat.g, 'g'), num(flat.gincrease, 'gincrease'), num(flat.gmargin, 'gmargin'),
    num(flat.garbagemultiplier, 'garbagemultiplier'), num(flat.garbageincrease, 'garbageincrease'), num(flat.garbagemargin, 'garbagemargin'),
    num(flat.garbagecap, 'garbagecap'), num(flat.garbagecapincrease, 'garbagecapincrease'), num(flat.garbagecapmargin, 'garbagecapmargin'),
    num(flat.garbagecapmax, 'garbagecapmax'), num(flat.garbageabsolutecap, 'garbageabsolutecap'),
    num(flat.garbagespeed, 'garbagespeed'), num(flat.garbageholesize, 'garbageholesize'),
    num(flat.messiness_change, 'messiness_change'), num(flat.messiness_inner, 'messiness_inner'), num(flat.messiness_timeout, 'messiness_timeout'),
    B(flat.messiness_nosame), B(flat.messiness_center ?? false), num(flat.openerphase, 'openerphase'),
    B(flat.allclears), num(flat.allclear_garbage, 'allclear_garbage'), num(flat.allclear_b2b, 'allclear_b2b'), B(flat.b2bchaining),
    flat.clutch !== false ? 1 : 0, num(flat.lockresets, 'lockresets'), num(flat.locktime, 'locktime'),
    B(flat.infinite_movement), B(flat.gravitymay20g ?? false),
    B(flat.allow180), flat.allow_harddrop !== false ? 1 : 0, B(flat.display_hold), B(flat.infinite_hold),
    num(h.arr, 'handling.arr'), num(h.das, 'handling.das'), num(h.dcd, 'handling.dcd'), num(h.sdf, 'handling.sdf'),
    B(h.safelock), B(h.cancel), B(h.may20g),
    maxF, ['consistent', 'zero'].includes(flat.passthrough) ? 1 : 0,
  ]);
}

/** The events the harness hands the engine (integer frames 0..maxF, replay order), as src/ffi.rs reads them. */
function encodeEvents(events: any[], maxF: number, network: boolean): Float64Array {
  const out: number[] = [];
  for (const e of events) {
    const f = e.frame;
    if (typeof f !== 'number' || !Number.isInteger(f) || f < 0 || f > maxF) continue;   // never handed to tick
    if (e.type === 'keydown' || e.type === 'keyup') {
      const d = e.data ?? unsupported(`${e.type} without data`);
      const sub = num(d.subframe, `${e.type}.subframe`);
      const key = typeof d.key === 'string' && Object.hasOwn(KEY, d.key) ? KEY[d.key]! : NO_KEY;
      if (e.type === 'keydown') out.push(f, 1, sub, key, d.hoisted ? 1 : 0);
      else out.push(f, 2, sub, key);
    } else if (e.type === 'ige') {
      const t = e.data?.type, d = e.data?.data;
      if (t === 'interaction') {
        if (d?.type === 'garbage') {
          out.push(f, 3, num(d.gameid, 'ige gameid'), network ? num(d.ackiid, 'ige ackiid') : 0,
            num(d.amt, 'ige amt'), num(d.iid, 'ige iid'), num(d.size, 'ige size'));
        } else if (d == null) unsupported('interaction without data');
      } else if (t === 'interaction_confirm') {
        if (d?.type === 'garbage') out.push(f, 4, num(d.iid, 'confirm iid'), num(d.gameid, 'confirm gameid'), f);
        else if (d == null) unsupported('interaction_confirm without data');
      } else if (t === 'target') {
        const ids = d?.targets;
        if (!Array.isArray(ids)) unsupported('target without a targets array');
        out.push(f, 5, ids.length, ...ids.map((x: unknown) => num(x, 'target id')));
      } else if (t == null) unsupported('ige without a type');
    }
  }
  return new Float64Array(out);
}

/** `runCaseOracleTs` (oracle-source.ts) through the Rust engine; `defaults` is its TL_DEFAULTS. */
export function runCaseOracleNative(player: any, defaults: Record<string, unknown>): SimResult {
  const o = player.replay.options;
  const flat: any = { ...defaults, ...o, g: o.g ?? defaults.g };
  const maxF = player.replay.frames ?? 20000;
  if (typeof maxF !== 'number' || !Number.isInteger(maxF) || maxF > 1e7) unsupported(`frames = ${String(maxF)}`);
  const opts = encodeOpts(flat, maxF);
  const evs = encodeEvents(player.replay.events, maxF, opts[42] === 1);

  const S = L();
  const hnd = S.oracle_run(opts, opts.length, evs.length ? evs : null, evs.length);
  if (hnd == null) throw new Error('oracle-native: oracle_run returned null');
  let d: Float64Array;
  try {
    const n = S.oracle_out_len(hnd);
    d = new Float64Array(n);
    if (S.oracle_out_copy(hnd, d, n) !== n) throw new Error('oracle-native: output copy failed');
  } finally { S.oracle_free(hnd); }

  const status = d[0]!;
  if (status === 2) throw new Error('oracle-source: a clearing lock with no pre-tick snapshot');
  if (status !== 0) throw new Error(`oracle-native: the engine refused its input (status ${status})`);
  const topout = d[1] === 1, nLocks = d[2]!, nGarbage = d[3]!, nSnaps = d[4]!;
  let p = 5;

  const records: SimResult['records'] = [], locks: SimResult['locks'] = [], evLog: SimResult['events'] = [];
  const snapOf: number[] = [];
  const clears: Record<string, number> = {};
  let linesTotal = 0, sentTotal = 0, clearedTotal = 0, topbtb = 0, topcombo = 0;
  for (let i = 0; i < nLocks; i++) {
    const frame = d[p]!, piece = PIECE[d[p + 1]!]!, lines = d[p + 2]!, spin = SPIN[d[p + 3]!]!, sent = d[p + 4]!;
    const b2b = d[p + 5]!, combo = d[p + 6]!, garbageCleared = d[p + 7]!, allclear = d[p + 8] === 1;
    snapOf.push(d[p + 9]!);
    p += 10;
    const cells: { col: number; row: number }[] = [];
    for (let k = 0; k < 4; k++) { cells.push({ col: d[p]!, row: d[p + 1]! }); p += 2; }
    const nc = d[p++]!, clearedRows: number[] = [];
    for (let k = 0; k < nc; k++) clearedRows.push(d[p++]!);
    linesTotal += lines;
    if (lines > 0) clears[String(lines)] = (clears[String(lines)] ?? 0) + 1;
    sentTotal += sent; clearedTotal += garbageCleared;
    topbtb = Math.max(topbtb, b2b); topcombo = Math.max(topcombo, combo);
    records.push({ frame, piece, lines, spin, attack: sent, sent, cancelled: 0, b2b, combo, cells, garbageCleared, clearedRows });
    locks.push({ frame, piece, cells, cleared: lines, spin, allclear });
    evLog.push({ frame, kind: 'lock' });
  }
  const garbageEvents: SimResult['garbageEvents'] = [];
  let recvTotal = 0;
  for (let i = 0; i < nGarbage; i++) {
    garbageEvents.push({ frame: d[p]!, amt: d[p + 1]!, lockIndex: d[p + 2]! });
    recvTotal += d[p + 1]!;
    p += 3;
  }
  const snapBase = p;
  if (snapBase + nSnaps * 2 * SNAP !== d.length) throw new Error('oracle-native: output length mismatch');
  const boards: Board[] = [], provSnaps: (number | null)[][][] = [];
  for (let i = 0; i < nLocks; i++) {
    const s = snapOf[i]!;
    if (s < 0) break;
    const at = snapBase + s * 2 * SNAP;
    const b: (PieceType | null)[][] = [], g: (number | null)[][] = [];
    for (let r = 0; r < 40; r++) {
      const row = new Array<PieceType | null>(10), prow = new Array<number | null>(10);
      for (let c = 0; c < 10; c++) {
        const v = d[at + r * 10 + c]!;
        row[c] = v === 0 ? null : v === 8 ? GARBAGE : PIECE[v - 1]!;
        const q = d[at + SNAP + r * 10 + c]!;
        prow[c] = q === -2 ? null : q;
      }
      b.push(row); g.push(prow);
    }
    boards.push(b as Board); provSnaps.push(g);
  }
  return {
    lines: linesTotal, placed: locks.length, holds: 0, clears, topbtb, topcombo,
    garbage: { sent: sentTotal, received: recvTotal, cleared: clearedTotal, attack: sentTotal },
    boards, records, events: evLog, locks, garbageEvents, provSnaps, topout,
  };
}
