/**
 * The engine runs of emit-attack-facts.ts and emit-finesse-facts.ts through the Rust engine
 * (`pipeline/sim/oracle-rs/src/facts.rs`), loaded through bun:ffi. `runFactsNative` ticks one
 * player-round to `replay.frames` and returns, per lock, what those two emitters' hooks read off the
 * TS engine: the piece, its `falling.keys`, its cells and the soft-drop flag at `falling.lock.pre`; the
 * lines, spin, b2b, combo, garbageCleared, Perfect Clear and `rawGarbage` of `falling.lock`; and the
 * keys pressed on the piece. Each emitter's `runRound` turns these into its own records, so the rules
 * (classify, split, the finesse table) stay in TypeScript, one copy each.
 *
 * The rule set is `oracle-native.ts`'s, checked by its `encodeOpts` with the wall clock (the date the
 * two emitters' createEngine defaults to); anything else is refused before the engine runs, never
 * approximated. `attack-native.test.ts` and `finesse-native.test.ts` hold each emitter's `runRound`
 * equal to its TS reference; ATTACK_NATIVE=off / FINESSE_NATIVE=off select the reference.
 */
import { dlopen, FFIType } from 'bun:ffi';
import { TL_DEFAULTS } from './oracle-source.ts';
import { buildIfStale, encodeEvents, encodeOpts, LIB } from './oracle-native.ts';

const PIECE = 'IJLOSTZ';
const SPIN = ['none', 'mini', 'normal'] as const;
/** oracle-native.ts's key codes, back to the engine's key names (255: a key the engine ignores). */
const KEY_NAME = ['moveLeft', 'moveRight', 'softDrop', 'rotateCCW', 'rotateCW', 'rotate180', 'hardDrop', 'hold'];

const SYMBOLS = {
  facts_run: { args: [FFIType.ptr, FFIType.u32, FFIType.ptr, FFIType.u32], returns: FFIType.ptr },
  facts_f_len: { args: [FFIType.ptr], returns: FFIType.f64 },
  facts_f_copy: { args: [FFIType.ptr, FFIType.ptr, FFIType.u32], returns: FFIType.i32 },
  facts_free: { args: [FFIType.ptr], returns: FFIType.void },
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
  4: 'the engine threw while building',
};

export type NativeLock = {
  piece: string; keys: number; softDrop: boolean; cells: [number, number][];
  lines: number; spin: typeof SPIN[number]; b2b: number; combo: number; garbageCleared: number;
  allclear: boolean; rawGarbage: number[]; own: string[];
};

/** One player-round: its locks, and whether a tick threw (the round ends there; the locks before stand). */
export function runFactsNative(player: any, maxF: number): { locks: NativeLock[]; threw: boolean } {
  const o = player.replay.options;
  const flat: any = { ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g };
  if (!Number.isInteger(maxF) || maxF > 1e7) throw new Error(`facts-native: unsupported frames = ${maxF}`);
  const opts = encodeOpts(flat, maxF);
  const evs = encodeEvents(player.replay.events, maxF, opts[42] === 1);

  const S = L();
  const h = S.facts_run(opts, opts.length, evs.length ? evs : null, evs.length);
  if (h == null) throw new Error('facts-native: facts_run returned null');
  let d: Float64Array;
  try {
    const nf = S.facts_f_len(h);
    d = new Float64Array(nf);
    if (S.facts_f_copy(h, d, nf) !== nf) throw new Error('facts-native: output copy failed');
  } finally { S.facts_free(h); }

  const status = d[0]!;
  if (status !== 0) throw new Error(`facts-native: ${STATUS[status] ?? `status ${status}`}`);
  const threw = d[1] === 1, n = d[2]!;
  const locks: NativeLock[] = [];
  let p = 3;
  for (let i = 0; i < n; i++) {
    const piece = PIECE[d[p]!]!, keys = d[p + 1]!, softDrop = d[p + 2] === 1;
    const cells: [number, number][] = [];
    for (let k = 0; k < 4; k++) cells.push([d[p + 3 + 2 * k]!, d[p + 4 + 2 * k]!]);
    p += 11;
    const lines = d[p]!, spin = SPIN[d[p + 1]!]!, b2b = d[p + 2]!, combo = d[p + 3]!, garbageCleared = d[p + 4]!;
    const allclear = d[p + 5] === 1;
    p += 6;
    const nr = d[p++]!, rawGarbage: number[] = [];
    for (let k = 0; k < nr; k++) rawGarbage.push(d[p++]!);
    const no = d[p++]!, own: string[] = [];
    for (let k = 0; k < no; k++) { const c = d[p++]!; own.push(KEY_NAME[c] ?? `key${c}`); }
    locks.push({ piece, keys, softDrop, cells, lines, spin, b2b, combo, garbageCleared, allclear, rawGarbage, own });
  }
  if (p !== d.length) throw new Error('facts-native: output length mismatch');
  return { locks, threw };
}
