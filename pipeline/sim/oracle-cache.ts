/**
 * A SHARED, CONTENT-ADDRESSED cache of the oracle replay — `verified-prefix.ts`'s `runCaseOracle(c)`
 * and `forecastMetric(r, true)` — so the bun test files that each replay the whole corpus through
 * the vendored engine stop recomputing the identical result 22 times on one runner.
 *
 * WHAT IS CACHED, AND WHY IT IS THE SAME COMPUTATION EVERYWHERE. `runCaseOracle(c)` takes no options
 * and reads no environment: its result is a function of the replay bytes, the code under
 * `pipeline/sim` (the oracle wrapper, the vendored engine) and the bun runtime. The vendored engine
 * also reads the wall clock (`engine/index.mjs` compares `new Date()` against 2025-02-16 and
 * 2025-05-06 when no date is passed, and `oracle-source.ts` passes none), so which side of those two
 * dates "now" is goes into the key as well. `forecastMetric(r, true)` is a pure function of `r` and
 * `pipeline/sim/forecast.ts`.
 *
 * THE KEY: sha256 over the schema version, a hash of EVERY file under `pipeline/sim` (globbed by a
 * recursive readdir, never a hand list — over-inclusive, so a test edit costs a cold cache and never
 * a stale one), `Bun.version`, platform, arch, the date era above, the kind of result, and per case
 * the .ttrm's own sha256, the round index, the side and the username. `oracle-cache.test.ts` checks
 * the import closure of everything this caches stays inside `pipeline/sim`, so an import from
 * outside the hashed root goes red rather than silently staling the key.
 *
 * WHAT BYPASSES IT. Only a Case `loadCases` registered (a WeakMap, so the Case object itself is
 * unchanged) and that still carries its raw replay is ever looked up; a synthetic Case, a spread
 * copy, or a Case from an injected loader computes exactly as before. The hand-port `runCase` is
 * never cached (it takes option bags and a global kickset). Mutants in the route and technique tests
 * act on the digest, after this point; a source mutant changes the tree hash and so the key.
 * Registered Cases' raw replays are deep-frozen, so a consumer that mutated one after loading — which
 * would make a load-time key describe different input — throws instead of reading a stale entry.
 *
 * WHEN IT IS ON. Default ON only under `bun test` (which sets NODE_ENV=test) and OFF everywhere
 * else, so every committed artefact an emitter writes comes from a fresh computation without any
 * emitter (each md5-hashed by its artefacts) being edited. `ORACLE_CACHE=off|0` disables it,
 * `ORACLE_CACHE=on|1` forces it on, `ORACLE_CACHE=verify` reads AND recomputes and throws on any
 * difference. `ORACLE_CACHE_DIR` sets the directory (default `<os.tmpdir()>/tetrio-oracle-cache`).
 *
 * CORRECTNESS OF AN ENTRY. Before every write the encoded bytes are decoded and must
 * `Bun.deepEquals(…, strict)` the computed result, or the call throws (never a silent fallback).
 * Every read checks a magic, the full key echoed in the header, the payload length and its sha256;
 * any failure is a miss: recompute, rewrite, warn. Writes go to a unique temp file in the same
 * directory, are fsynced, then renamed into place, so concurrent fillers in separate processes only
 * ever race to rename identical bytes. Every hit is decoded into fresh objects, so a consumer
 * mutating its result cannot leak into another test file in bun's shared process.
 *
 * Warm the cache from the command line (fills every session, `--jobs` processes at a time):
 *   bun pipeline/sim/oracle-cache.ts --warm [--jobs 4] [sessions/<date> ...]
 */
import { createHash, randomBytes } from 'node:crypto';
import {
  closeSync, existsSync, fsyncSync, mkdirSync, openSync, readdirSync, readFileSync, renameSync,
  statSync, unlinkSync, writeSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join, relative, resolve } from 'node:path';
import { deserialize, serialize } from 'bun:jsc';
import type { SimResult } from './sim.ts';
import { forecastMetric } from './forecast.ts';

/** Bump when the value encoding or the key layout changes. */
export const SCHEMA = 'oracle-cache/1';
const MAGIC = Buffer.from('TTRMORC1', 'latin1');
const SIM_ROOT = import.meta.dir;

export type Mode = 'off' | 'on' | 'verify';
let override: Mode | null = null;

/** The mode in force now: an active `withOracleCache` override, else ORACLE_CACHE, else the default. */
export function cacheMode(): Mode {
  if (override) return override;
  const v = (process.env.ORACLE_CACHE ?? '').trim().toLowerCase();
  if (v === 'off' || v === '0' || v === 'false' || v === 'no') return 'off';
  if (v === 'on' || v === '1' || v === 'true' || v === 'yes') return 'on';
  if (v === 'verify') return 'verify';
  if (v !== '') throw new Error(`ORACLE_CACHE=${v}: expected off, on or verify`);
  return process.env.NODE_ENV === 'test' ? 'on' : 'off';
}

/** Run `fn` with the cache forced to `mode` (`false` = off), restoring the previous mode after. */
export function withOracleCache<T>(mode: Mode | false, fn: () => T): T {
  const prev = override;
  override = mode === false ? 'off' : mode;
  try { return fn(); } finally { override = prev; }
}

export function cacheDir(): string {
  return resolve(process.env.ORACLE_CACHE_DIR || join(tmpdir(), 'tetrio-oracle-cache'));
}

/** Hit/miss counters, for the tests and the warm CLI. */
export const stats = { hits: 0, misses: 0, writes: 0, corrupt: 0, verified: 0 };

// ── the key ──────────────────────────────────────────────────────────────────

/**
 * sha256 over every regular file under `root` (default `pipeline/sim`): sorted relative path, NUL,
 * byte length, NUL, bytes. No hand list, so a new module is covered the day it is added.
 */
export function treeHash(root = SIM_ROOT): string {
  const files: string[] = [];
  const walk = (d: string) => {
    for (const e of readdirSync(d, { withFileTypes: true })) {
      if (e.name === 'node_modules') continue;
      const p = join(d, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.isFile()) files.push(p);
    }
  };
  walk(root);
  const rel = files.map(p => relative(root, p).split('\\').join('/')).sort();
  const h = createHash('sha256');
  for (const r of rel) {
    const b = readFileSync(join(root, r));
    h.update(r); h.update('\0'); h.update(String(b.length)); h.update('\0'); h.update(b);
  }
  return h.digest('hex');
}
let TREE: string | null = null;
const tree = () => (TREE ??= treeHash());

/** The engine's wall-clock branches, as booleans: part of the key, so a fill is never served across them. */
function dateEra(): string {
  const now = new Date();
  return [now >= new Date(2025, 1, 16), now > new Date('2025-05-06T15:00:00-04:00')].map(Number).join('');
}

export interface CaseId { fileSha: string; round: number; side: 0 | 1; user: string }
const IDS = new WeakMap<object, CaseId>();

export function keyOf(kind: string, id: CaseId, treeHashHex = tree()): string {
  return createHash('sha256').update(JSON.stringify([
    SCHEMA, treeHashHex, Bun.version, process.platform, process.arch, dateEra(),
    kind, id.fileSha, id.round, id.side, id.user,
  ])).digest('hex');
}

export const sha256 = (b: Uint8Array) => createHash('sha256').update(b).digest('hex');

function deepFreeze(o: any): void {
  if (o === null || typeof o !== 'object' || Object.isFrozen(o)) return;
  Object.freeze(o);
  for (const k of Object.keys(o)) deepFreeze(o[k]);
}

/**
 * Called by `loadCases` for each Case it builds (only while the cache is not off). Records the
 * Case's identity and deep-freezes its raw replay, which the key is then a statement about.
 */
export function registerCase(c: { rawPlayer?: any; rawRound?: any[] }, id: CaseId): void {
  deepFreeze(c.rawPlayer); deepFreeze(c.rawRound);
  IDS.set(c, id);
}

// ── the value encoding ───────────────────────────────────────────────────────

const ROWS = 40, COLS = 10, CELLS = ROWS * COLS;

/** SimResult → a structured-clone-able object: boards and provSnaps packed as typed arrays. */
function packSim(r: SimResult): unknown {
  const boards = new Uint8Array(r.boards.length * CELLS);
  r.boards.forEach((b, i) => {
    if (b.length !== ROWS) throw new Error(`board ${i}: ${b.length} rows`);
    for (let y = 0; y < ROWS; y++) {
      const row = b[y]!;
      if (row.length !== COLS) throw new Error(`board ${i} row ${y}: ${row.length} cells`);
      for (let x = 0; x < COLS; x++) {
        const v = row[x] as unknown;
        if (v === null) continue;
        if (typeof v !== 'string' || v.length !== 1 || v.charCodeAt(0) === 0 || v.charCodeAt(0) > 255)
          throw new Error(`board ${i} (${y},${x}): unencodable cell ${JSON.stringify(v)}`);
        boards[i * CELLS + y * COLS + x] = v.charCodeAt(0);
      }
    }
  });
  const prov = new Int16Array(r.provSnaps.length * CELLS);
  r.provSnaps.forEach((g, i) => {
    if (g.length !== ROWS) throw new Error(`provSnap ${i}: ${g.length} rows`);
    for (let y = 0; y < ROWS; y++) {
      const row = g[y]!;
      if (row.length !== COLS) throw new Error(`provSnap ${i} row ${y}: ${row.length} cells`);
      for (let x = 0; x < COLS; x++) {
        const v = row[x];
        if (v !== null && !(Number.isInteger(v) && v >= -1 && v <= 32767)) throw new Error(`provSnap ${i}: unencodable ${v}`);
        prov[i * CELLS + y * COLS + x] = v === null ? -2 : v;
      }
    }
  });
  // spread then overwrite keeps every key in its original position
  return { ...r, boards: { n: r.boards.length, cells: boards }, provSnaps: { n: r.provSnaps.length, cells: prov } };
}

function unpackSim(p: any): SimResult {
  const boards: (string | null)[][][] = new Array(p.boards.n);
  const bc: Uint8Array = p.boards.cells;
  for (let i = 0; i < p.boards.n; i++) {
    const b: (string | null)[][] = new Array(ROWS);
    for (let y = 0; y < ROWS; y++) {
      const row: (string | null)[] = new Array(COLS);
      for (let x = 0; x < COLS; x++) { const v = bc[i * CELLS + y * COLS + x]!; row[x] = v === 0 ? null : String.fromCharCode(v); }
      b[y] = row;
    }
    boards[i] = b;
  }
  const prov: (number | null)[][][] = new Array(p.provSnaps.n);
  const pc: Int16Array = p.provSnaps.cells;
  for (let i = 0; i < p.provSnaps.n; i++) {
    const g: (number | null)[][] = new Array(ROWS);
    for (let y = 0; y < ROWS; y++) {
      const row: (number | null)[] = new Array(COLS);
      for (let x = 0; x < COLS; x++) { const v = pc[i * CELLS + y * COLS + x]!; row[x] = v === -2 ? null : v; }
      g[y] = row;
    }
    prov[i] = g;
  }
  return { ...p, boards, provSnaps: prov } as SimResult;
}

interface Codec<T> { encode(v: T): unknown; decode(p: any): T }
const SIM: Codec<SimResult> = { encode: packSim, decode: unpackSim };
const PLAIN: Codec<any> = { encode: v => v, decode: p => p };

// ── storage ──────────────────────────────────────────────────────────────────

export function entryPath(key: string): string {
  return join(cacheDir(), tree().slice(0, 16), key.slice(0, 2), `${key}.bin`);
}

/**
 * The file bytes for `payload` under `key`: magic, header length, JSON header, then the payload
 * gzipped at level 1 (about a tenth of the size, and a few ms per session to inflate). The header's
 * length and sha256 are of the UNCOMPRESSED payload, so they check what is actually deserialised.
 */
export function frame(key: string, payload: Uint8Array): Buffer {
  const header = Buffer.from(JSON.stringify({
    schema: SCHEMA, key, encoding: 'gzip-1', payloadLen: payload.length, payloadSha256: sha256(payload) }));
  const len = Buffer.alloc(4); len.writeUInt32LE(header.length, 0);
  return Buffer.concat([MAGIC, len, header, Bun.gzipSync(payload, { level: 1 })]);
}

/** The payload of a well-formed entry for `key`, or the reason it is not one. */
export function unframe(key: string, buf: Buffer): { payload: Uint8Array } | { error: string } {
  if (buf.length < MAGIC.length + 4 || !buf.subarray(0, MAGIC.length).equals(MAGIC)) return { error: 'bad magic' };
  const hl = buf.readUInt32LE(MAGIC.length), h0 = MAGIC.length + 4;
  if (h0 + hl > buf.length) return { error: 'truncated header' };
  let h: any;
  try { h = JSON.parse(buf.subarray(h0, h0 + hl).toString('utf8')); } catch { return { error: 'unparseable header' }; }
  if (h.schema !== SCHEMA || h.key !== key) return { error: 'key mismatch' };
  if (h.encoding !== 'gzip-1') return { error: `unknown encoding ${h.encoding}` };
  let payload: Uint8Array;
  try { payload = Bun.gunzipSync(buf.subarray(h0 + hl)); } catch { return { error: 'gunzip failed' }; }
  if (payload.length !== h.payloadLen) return { error: 'length mismatch' };
  if (sha256(payload) !== h.payloadSha256) return { error: 'payload sha256 mismatch' };
  return { payload };
}

function atomicWrite(path: string, bytes: Uint8Array): void {
  const dir = join(path, '..');
  mkdirSync(dir, { recursive: true });
  const tmp = `${path}.tmp-${process.pid}-${randomBytes(6).toString('hex')}`;
  const fd = openSync(tmp, 'wx');
  try {
    let off = 0;
    while (off < bytes.length) off += writeSync(fd, bytes, off, bytes.length - off);
    fsyncSync(fd);
  } catch (e) { closeSync(fd); try { unlinkSync(tmp); } catch {} throw e; }
  closeSync(fd);
  renameSync(tmp, path);
}

/** Every unreadable entry is reported (stats.corrupt counts them too); there are none in normal use. */
function warn(msg: string): void {
  console.warn(`[oracle-cache] ${msg} — recomputing`);
}

function cached<T>(kind: string, id: CaseId, codec: Codec<T>, compute: () => T, mode: Mode): T {
  const key = keyOf(kind, id), path = entryPath(key);
  let hit: T | undefined;
  if (existsSync(path)) {
    try {
      const u = unframe(key, readFileSync(path));
      if ('error' in u) { stats.corrupt++; warn(`${path}: ${u.error}`); }
      else hit = codec.decode(deserialize(u.payload));
    } catch (e) { stats.corrupt++; warn(`${path}: ${(e as Error).message}`); hit = undefined; }
  }
  if (hit !== undefined) {
    stats.hits++;
    if (mode === 'verify') {
      const fresh = compute();
      if (!Bun.deepEquals(hit, fresh, true))
        throw new Error(`ORACLE_CACHE=verify: cached ${kind} differs from a fresh computation (${path})`);
      stats.verified++;
    }
    return hit;
  }
  stats.misses++;
  const v = compute();
  // bun:jsc's serialize returns a SharedArrayBuffer; view it as bytes
  const payload = new Uint8Array(serialize(codec.encode(v)));
  const back = codec.decode(deserialize(payload));
  if (!Bun.deepEquals(back, v, true))
    throw new Error(`oracle-cache: ${kind} does not round-trip through its encoding; refusing to write ${path}`);
  atomicWrite(path, frame(key, payload));
  stats.writes++;
  return v;
}

// ── the two cached functions ─────────────────────────────────────────────────

/** The case identity each SimResult the cache returned came from — for `cachedForecastMetric`. */
const ORIGIN = new WeakMap<object, CaseId>();

/**
 * `compute()` (the oracle replay of `c`) through the cache, when `c` is a Case `loadCases`
 * registered and the cache is on; `compute()` itself otherwise.
 */
export function cachedOracle(c: object & { rawPlayer?: any; rawRound?: any[] }, compute: () => SimResult): SimResult {
  const mode = cacheMode(), id = IDS.get(c);
  if (mode === 'off' || !id || !c.rawPlayer || !c.rawRound) return compute();
  const r = cached('oracle', id, SIM, compute, mode);
  ORIGIN.set(r, id);
  return r;
}

/**
 * `forecastMetric(r, true)`, cached when `r` is a result `cachedOracle` returned (and so has a case
 * identity); computed directly otherwise. The caller must not have mutated `r` — the four call
 * sites pass it straight from `runCaseOracle`.
 */
export function cachedForecastMetric(r: SimResult): ReturnType<typeof forecastMetric> {
  const mode = cacheMode(), id = ORIGIN.get(r);
  if (mode === 'off' || !id) return forecastMetric(r, true);
  return cached('forecastMetric:strict', id, PLAIN, () => forecastMetric(r, true), mode);
}

// ── CLI: warm the cache ──────────────────────────────────────────────────────

async function warm(argv: string[]): Promise<void> {
  const jobsAt = argv.indexOf('--jobs');
  const jobs = jobsAt >= 0 ? Number(argv[jobsAt + 1]) : 4;
  const dirs = argv.filter((a, i) => !a.startsWith('--') && !(jobsAt >= 0 && i === jobsAt + 1));
  const repo = resolve(SIM_ROOT, '../..');
  const sessions = dirs.length ? dirs.map(d => resolve(d))
    : readdirSync(join(repo, 'sessions')).map(s => join(repo, 'sessions', s))
        .filter(d => statSync(d).isDirectory() && readdirSync(d).some(f => f.endsWith('.ttrm'))).sort();
  const queue = [...sessions];
  const t0 = performance.now();
  const worker = async () => {
    for (let s = queue.shift(); s; s = queue.shift()) {
      const p = Bun.spawn(['bun', import.meta.path, '--warm-one', s], {
        env: { ...process.env, ORACLE_CACHE: 'on' }, stdout: 'inherit', stderr: 'inherit' });
      if ((await p.exited) !== 0) throw new Error(`warming ${s} failed`);
    }
  };
  await Promise.all(Array.from({ length: Math.max(1, jobs) }, worker));
  console.log(`[oracle-cache] warmed ${sessions.length} sessions in ${((performance.now() - t0) / 1000).toFixed(1)} s into ${cacheDir()}`);
}

async function warmOne(dir: string): Promise<void> {
  const vp = await import('./verified-prefix.ts');
  const t0 = performance.now();
  // the forecast call sites run forecastMetric only on a round with a verified prefix
  for (const c of vp.loadCases(dir)) {
    const r = vp.runCaseOracle(c);
    if (vp.verifiedIndex(r, c.truth) >= 0) cachedForecastMetric(r);
  }
  console.log(`[oracle-cache] ${dir}: ${stats.hits} hit, ${stats.misses} miss in ${((performance.now() - t0) / 1000).toFixed(1)} s`);
}

if (import.meta.main) {
  const argv = process.argv.slice(2);
  if (argv[0] === '--warm-one') await warmOne(argv[1]!);
  else if (argv[0] === '--warm') await warm(argv.slice(1));
  else { console.error('usage: bun pipeline/sim/oracle-cache.ts --warm [--jobs N] [sessions/<date> ...]'); process.exit(2); }
}
