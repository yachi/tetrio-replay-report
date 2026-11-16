/**
 * `runPlayer` (emit-replay.ts) through the Rust engine (`pipeline/sim/oracle-rs/src/trace.rs`), loaded
 * through bun:ffi. `runPlayerNative` returns a value whose JSON.stringify equals the TS `runPlayer`'s
 * byte for byte (`replay-native.test.ts`): the same lock tuples, engine board keys, queue reads, piece
 * sequence and counters `instrumentEngine` records.
 *
 * The rule set is `oracle-native.ts`'s, checked by its `encodeOpts` with the replay's own date (the date
 * emit-replay.ts hands createEngine); anything else is refused before the engine runs, never approximated.
 * emit-replay.ts uses this unless REPLAY_NATIVE=off, which keeps the TS engine as the reference.
 */
import { dlopen, FFIType } from 'bun:ffi';
import { TL_DEFAULTS } from './oracle-source.ts';
import { buildIfStale, encodeEvents, encodeOpts, LIB } from './oracle-native.ts';
import { encodePlace, type runPlayerTs } from './emit-replay.ts';

const PIECE = 'IJLOSTZ';
const KEY_LEN = 40 * 10 + 39;   // engineKey: 40 rows of 10, joined by '/'

const SYMBOLS = {
  replay_run: { args: [FFIType.ptr, FFIType.u32, FFIType.ptr, FFIType.u32], returns: FFIType.ptr },
  replay_f_len: { args: [FFIType.ptr], returns: FFIType.f64 },
  replay_s_len: { args: [FFIType.ptr], returns: FFIType.f64 },
  replay_f_copy: { args: [FFIType.ptr, FFIType.ptr, FFIType.u32], returns: FFIType.i32 },
  replay_s_copy: { args: [FFIType.ptr, FFIType.ptr, FFIType.u32], returns: FFIType.i32 },
  replay_free: { args: [FFIType.ptr], returns: FFIType.void },
} as const;
let lib: ReturnType<typeof dlopen<typeof SYMBOLS>>['symbols'] | null = null;
function L() {
  if (lib) return lib;
  buildIfStale();
  lib = dlopen(LIB, SYMBOLS).symbols;
  return lib;
}

const STATUS: Record<number, string> = {
  2: 'a clearing lock with no pre-tick snapshot',
  3: 'the engine refused its input',
  4: 'the engine threw',
  5: 'unsupported garbage shape (size other than 1)',
};

export function runPlayerNative(player: any, _roundPlayers: any[], date: Date): ReturnType<typeof runPlayerTs> {
  const o = player.replay.options;
  const flat: any = { ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g };
  const maxF = player.replay.frames;
  if (typeof maxF !== 'number') throw new Error('replay.frames missing');
  if (!Number.isInteger(maxF) || maxF > 1e7) throw new Error(`replay-native: unsupported frames = ${maxF}`);
  const opts = encodeOpts(flat, maxF, date);
  const evs = encodeEvents(player.replay.events, maxF, opts[42] === 1);

  const S = L();
  const h = S.replay_run(opts, opts.length, evs.length ? evs : null, evs.length);
  if (h == null) throw new Error('replay-native: replay_run returned null');
  let d: Float64Array, s: Uint8Array;
  try {
    const nf = S.replay_f_len(h), ns = S.replay_s_len(h);
    d = new Float64Array(nf); s = new Uint8Array(ns);
    if (S.replay_f_copy(h, d, nf) !== nf || S.replay_s_copy(h, s, ns) !== ns) throw new Error('replay-native: output copy failed');
  } finally { S.replay_free(h); }

  const status = d[0]!;
  if (status !== 0) throw new Error(`replay-native: ${STATUS[status] ?? `status ${status}`}`);
  const nLocks = d[1]!, drawn = d[2]!, holdsTotal = d[3]!, pcs = d[4]!, top = d[5]!, garbageCleared = d[6]!, seqLen = d[7]!;
  const text = new TextDecoder().decode(s);
  const seq = text.slice(0, seqLen);
  if (text.length !== seqLen + nLocks * KEY_LEN) throw new Error('replay-native: output length mismatch');

  const locks: any[] = [], engineStates: string[] = [], engineQueue: { piece: string; hold: string }[] = [];
  let p = 8;
  for (let i = 0; i < nLocks; i++) {
    const dframe = d[p]!, lines = d[p + 1]!, spin = d[p + 2]!, held = d[p + 3]!, attack = d[p + 4]!, sent = d[p + 5]!;
    const piece = PIECE[d[p + 6]!]!, hold = d[p + 7]! < 0 ? '' : PIECE[d[p + 7]!]!, nc = d[p + 8]!;
    p += 9;
    const cells: number[] = [];
    for (let k = 0; k < nc; k++) cells.push(d[p++]!);
    const ng = d[p++]!, garbage: [number | null, number][] = [];
    for (let k = 0; k < ng; k++) { const c = d[p]!; garbage.push([Number.isNaN(c) ? null : c, d[p + 1]!]); p += 2; }
    locks.push([dframe, encodePlace(piece, cells), lines, spin, garbage, held, attack, sent]);
    engineQueue.push({ piece, hold });
    engineStates.push(text.slice(seqLen + i * KEY_LEN, seqLen + (i + 1) * KEY_LEN));
  }
  if (p !== d.length) throw new Error('replay-native: output length mismatch');
  return { locks, engineStates, engineQueue, seq, drawn, holdsTotal, pcs,
           engineTopLock: top < 0 ? null : top, garbageCleared } as ReturnType<typeof runPlayerTs>;
}
