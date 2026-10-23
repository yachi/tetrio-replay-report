/**
 * The oracle cache (oracle-cache.ts) may only ever change how long a test takes, never what it
 * computes. These tests are what hold it to that:
 *
 *   - a cached result is the freshly computed one, deep-equal under strict comparison, for every
 *     case of one session, for both cached functions, read back from disk;
 *   - the key moves when any file under pipeline/sim changes, and with each part of a case's identity;
 *   - everything the cached functions import stays inside pipeline/sim, the tree the key hashes;
 *   - a corrupt or truncated entry is a miss and is recomputed, never decoded into a result;
 *   - ORACLE_CACHE=verify catches an entry that is well-formed but wrong;
 *   - a Case loadCases did not register (a spread copy) is computed, never looked up.
 */
import { test, expect } from 'bun:test';
import { appendFileSync, cpSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric } from './forecast.ts';
import {
  cacheMode, cachedForecastMetric, entryPath, frame, keyOf, stats, treeHash, unframe, withOracleCache,
  type CaseId,
} from './oracle-cache.ts';

const SIM = import.meta.dir;
const SESSION = resolve(SIM, '../../sessions/2026-10-20');   // the corpus's smallest session

/** Run `fn` against a fresh, empty cache directory, restoring the environment after. */
function withTempCache<T>(fn: (dir: string) => T): T {
  const prev = process.env.ORACLE_CACHE_DIR;
  const dir = mkdtempSync(join(tmpdir(), 'oracle-cache-test-'));
  process.env.ORACLE_CACHE_DIR = dir;
  try { return fn(dir); } finally {
    if (prev === undefined) delete process.env.ORACLE_CACHE_DIR; else process.env.ORACLE_CACHE_DIR = prev;
    rmSync(dir, { recursive: true, force: true });
  }
}
const snap = () => ({ ...stats });
/** Every file under `dir`, recursively. */
const filesUnder = (dir: string): string[] => readdirSync(dir, { withFileTypes: true })
  .flatMap(e => e.isDirectory() ? filesUnder(join(dir, e.name)) : [join(dir, e.name)]);
/** The single entry a fresh cache directory holds, and its key. */
function onlyEntry(dir: string): { path: string; key: string } {
  const files = filesUnder(dir);
  expect(files.length).toBe(1);
  return { path: files[0]!, key: files[0]!.split('/').pop()!.replace(/\.bin$/, '') };
}
const delta = (a: typeof stats, b: typeof stats) =>
  Object.fromEntries(Object.keys(a).map(k => [k, (b as any)[k] - (a as any)[k]]));

test('a cached result equals a fresh computation, case by case, for one whole session', () => {
  withTempCache(() => {
    const fresh = withOracleCache(false, () => loadCases(SESSION).map(c => {
      const r = runCaseOracle(c);
      return { r, fm: verifiedIndex(r, c.truth) >= 0 ? forecastMetric(r, true) : null };
    }));
    expect(fresh.length).toBeGreaterThan(0);
    const run = () => withOracleCache('on', () => loadCases(SESSION).map(c => {
      const r = runCaseOracle(c);
      return { r, fm: verifiedIndex(r, c.truth) >= 0 ? cachedForecastMetric(r) : null };
    }));
    const s0 = snap();
    const filled = run();                 // every entry a miss: computed, round-tripped, written
    const s1 = snap();
    const read = run();                   // every entry a hit: read back from disk and decoded
    const s2 = snap();
    const nFm = fresh.filter(x => x.fm).length;
    expect(delta(s0, s1)).toEqual({ hits: 0, misses: fresh.length + nFm, writes: fresh.length + nFm, corrupt: 0, verified: 0 });
    expect(delta(s1, s2)).toEqual({ hits: fresh.length + nFm, misses: 0, writes: 0, corrupt: 0, verified: 0 });
    for (const got of [filled, read]) {
      expect(got.length).toBe(fresh.length);
      got.forEach((g, i) => {
        expect(Bun.deepEquals(g.r, fresh[i]!.r, true)).toBe(true);
        expect(Bun.deepEquals(g.fm, fresh[i]!.fm, true)).toBe(true);
      });
    }
    // two hits are two separate objects: a consumer mutating one cannot reach another
    const again = withOracleCache('on', () => runCaseOracle(loadCases(SESSION)[0]!));
    expect(again).not.toBe(read[0]!.r);
    expect(again.boards[0]).not.toBe(read[0]!.r.boards[0]);
  });
}, 300_000);

test('the key moves when any file under pipeline/sim changes, and with every part of a case', () => {
  const copy = mkdtempSync(join(tmpdir(), 'oracle-cache-tree-'));
  try {
    cpSync(SIM, copy, { recursive: true });
    const h0 = treeHash(copy);
    expect(h0).toBe(treeHash(SIM));                       // the hash is of content, not of location
    const target = join(copy, 'oracle-source.ts');
    const orig = readFileSync(target);
    appendFileSync(target, ' ');
    const h1 = treeHash(copy);
    writeFileSync(target, orig);
    expect(treeHash(copy)).toBe(h0);
    writeFileSync(join(copy, 'vendor', 'new-module.mjs'), 'export {};\n');   // a file nobody listed
    const h2 = treeHash(copy);
    expect(new Set([h0, h1, h2]).size).toBe(3);
    const id: CaseId = { fileSha: 'a'.repeat(64), round: 3, side: 0, user: 'yachi' };
    const keys = [
      keyOf('oracle', id, h0), keyOf('oracle', id, h1), keyOf('oracle', id, h2),
      keyOf('forecastMetric:strict', id, h0),
      keyOf('oracle', { ...id, fileSha: 'b'.repeat(64) }, h0),
      keyOf('oracle', { ...id, round: 4 }, h0),
      keyOf('oracle', { ...id, side: 1 }, h0),
      keyOf('oracle', { ...id, user: 'pinglamb' }, h0),
    ];
    expect(new Set(keys).size).toBe(keys.length);
    expect(keyOf('oracle', id, h0)).toBe(keys[0]!);      // and it is a function of its inputs
  } finally { rmSync(copy, { recursive: true, force: true }); }
});

test('everything the cache stands in for imports only modules inside pipeline/sim', () => {
  // The key hashes pipeline/sim and nothing else, so a module outside it reached from the cached
  // computation could change while the key stays put. Walk the static and dynamic import closure.
  const seen = new Set<string>(), outside: string[] = [], bare: string[] = [];
  const walk = (file: string) => {
    if (seen.has(file)) return;
    seen.add(file);
    const loader = file.endsWith('.ts') ? 'ts' : 'js';
    for (const imp of new Bun.Transpiler({ loader }).scanImports(readFileSync(file, 'utf8'))) {
      const spec = imp.path;
      if (spec.startsWith('node:') || spec.startsWith('bun:')) continue;
      if (!spec.startsWith('.') && !spec.startsWith('/')) { bare.push(`${file}: ${spec}`); continue; }
      const to = Bun.resolveSync(spec, dirname(file));      // throws on an unresolvable import
      if (!to.startsWith(SIM + '/')) { outside.push(`${file}: ${spec}`); continue; }
      walk(to);
    }
  };
  for (const root of ['verified-prefix.ts', 'oracle-source.ts', 'forecast.ts', 'oracle-cache.ts']) walk(join(SIM, root));
  expect(outside).toEqual([]);
  expect(bare).toEqual([]);
  // the closure really does reach the engine, so an empty walk cannot pass this vacuously
  expect([...seen].some(f => f.includes('/vendor/teto/'))).toBe(true);
});

test('a corrupt entry is a miss and is recomputed; a well-formed wrong one is caught by verify', () => {
  withTempCache(() => {
    const cases = withOracleCache('on', () => loadCases(SESSION));   // registered, whatever ORACLE_CACHE says
    const [c0, c1] = [cases[0]!, cases[1]!];
    const fresh0 = withOracleCache(false, () => runCaseOracle(c0));
    withOracleCache('on', () => runCaseOracle(c0));            // fill
    const { path, key } = onlyEntry(process.env.ORACLE_CACHE_DIR!);
    expect(entryPath(key)).toBe(path);
    const good = readFileSync(path);
    expect('payload' in unframe(key, good)).toBe(true);

    // every way of damaging the file is a miss, recomputed to the right answer and rewritten
    const damaged: [string, Buffer][] = [
      ['flipped payload byte', (() => { const b = Buffer.from(good); b[b.length - 5]! ^= 0xff; return b; })()],
      ['truncated', good.subarray(0, good.length - 10)],
      ['bad magic', Buffer.concat([Buffer.from('XXXXXXXX'), good.subarray(8)])],
      ['empty', Buffer.alloc(0)],
    ];
    for (const [what, bytes] of damaged) {
      expect('error' in unframe(key, bytes)).toBe(true);
      writeFileSync(path, bytes);
      const s0 = snap();
      const got = withOracleCache('on', () => runCaseOracle(c0));
      const d = delta(s0, snap());
      expect([what, d.corrupt, d.misses, d.writes]).toEqual([what, 1, 1, 1]);
      expect(Bun.deepEquals(got, fresh0, true)).toBe(true);
      expect(readFileSync(path).equals(good)).toBe(true);           // and the entry is whole again
    }

    // a well-formed entry holding ANOTHER case's result: only `verify` can tell, and it must
    const other = withOracleCache(false, () => runCaseOracle(c1));
    expect(Bun.deepEquals(other, fresh0, true)).toBe(false);
    // its payload, as the module itself encoded it: fill c1 into a scratch directory and lift it
    const otherPayload = (() => {
      const prev = process.env.ORACLE_CACHE_DIR!;
      const scratch = mkdtempSync(join(tmpdir(), 'oracle-cache-other-'));
      process.env.ORACLE_CACHE_DIR = scratch;
      try {
        withOracleCache('on', () => runCaseOracle(c1));
        const e = onlyEntry(scratch), u = unframe(e.key, readFileSync(e.path));
        if (!('payload' in u)) throw new Error(u.error);
        return u.payload;
      } finally { process.env.ORACLE_CACHE_DIR = prev; rmSync(scratch, { recursive: true, force: true }); }
    })();
    writeFileSync(path, frame(key, otherPayload));
    expect('payload' in unframe(key, readFileSync(path))).toBe(true);
    expect(() => withOracleCache('verify', () => runCaseOracle(c0))).toThrow(/differs from a fresh computation/);
    // (and plain `on` would serve it — which is exactly why verify exists and the key is content-derived)
    expect(Bun.deepEquals(withOracleCache('on', () => runCaseOracle(c0)), other, true)).toBe(true);
  });
}, 120_000);

test('a Case loadCases did not register is computed, never looked up', () => {
  withTempCache(() => {
    const c = withOracleCache('on', () => loadCases(SESSION)[0]!);
    // control: the registered Case itself IS looked up, so the zero below is not a cache that never runs
    const sc = snap();
    withOracleCache('on', () => runCaseOracle(c));
    expect(delta(sc, snap()).misses).toBe(1);
    const s0 = snap();
    const r = withOracleCache('on', () => runCaseOracle({ ...c }));
    expect(delta(s0, snap())).toEqual({ hits: 0, misses: 0, writes: 0, corrupt: 0, verified: 0 });
    // and its result carries no case identity, so forecastMetric is not cached either
    const s1 = snap();
    withOracleCache('on', () => cachedForecastMetric(r));
    expect(delta(s1, snap())).toEqual({ hits: 0, misses: 0, writes: 0, corrupt: 0, verified: 0 });
  });
}, 60_000);

test('a registered Case\'s raw replay is frozen, so it cannot drift from the key made at load', () => {
  const c = withOracleCache('on', () => loadCases(SESSION)[0]!);
  expect(Object.isFrozen(c.rawPlayer)).toBe(true);
  expect(Object.isFrozen(c.rawPlayer.replay.events[0])).toBe(true);
  expect(() => { c.rawPlayer.replay.frames = 1; }).toThrow();
  // with the cache off, loadCases is what it always was: nothing frozen
  const d = withOracleCache(false, () => loadCases(SESSION)[0]!);
  expect(Object.isFrozen(d.rawPlayer)).toBe(false);
});

test('the switch: on under bun test by default, off elsewhere, and ORACLE_CACHE overrides both', () => {
  const prev = { c: process.env.ORACLE_CACHE, n: process.env.NODE_ENV };
  try {
    delete process.env.ORACLE_CACHE;
    process.env.NODE_ENV = 'test'; expect(cacheMode()).toBe('on');
    process.env.NODE_ENV = 'production'; expect(cacheMode()).toBe('off');
    delete process.env.NODE_ENV; expect(cacheMode()).toBe('off');
    process.env.NODE_ENV = 'test';
    for (const [v, m] of [['off', 'off'], ['0', 'off'], ['on', 'on'], ['1', 'on'], ['verify', 'verify']] as const) {
      process.env.ORACLE_CACHE = v; expect(cacheMode()).toBe(m);
    }
    process.env.ORACLE_CACHE = 'sometimes'; expect(() => cacheMode()).toThrow(/expected off, on or verify/);
    process.env.ORACLE_CACHE = 'on';
    expect(withOracleCache(false, () => cacheMode())).toBe('off');
    expect(cacheMode()).toBe('on');
  } finally {
    if (prev.c === undefined) delete process.env.ORACLE_CACHE; else process.env.ORACLE_CACHE = prev.c;
    if (prev.n === undefined) delete process.env.NODE_ENV; else process.env.NODE_ENV = prev.n;
  }
});
