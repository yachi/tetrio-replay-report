/**
 * Emit many corpus artefacts from ONE oracle pass: the route facts of every opener off one route digest,
 * and the technique facts of every technique, plus the DPC and Second PC facts, off one technique digest.
 * `bin/emit-corpus` runs this for those nodes; `bin/emit-corpus --unbatched` runs each node's own entry
 * file instead, and the two must write the same bytes (`emit-corpus-batch.test.ts`, and
 * `bin/emit-corpus --check` both ways).
 *
 * WHY.  Each of those entry files rebuilds a corpus digest (every round through the oracle, the verified
 * prefix, per-lock rows) that does not depend on the opener or technique: the route digest depends only on
 * the profile's `snapshotLocks` (and `tag`, which only names the profile in an error), the technique digest
 * on nothing. Rebuilt twenty-two times it was most of `bin/emit-corpus`'s cost. Every `build()` already
 * takes the digests as a parameter (the tests pass them for their mutants), so this file only computes
 * each digest once and hands it on.
 *
 * WHAT THIS FILE MUST NOT BE.  It is hashed into nothing: no profile names it in `hashFiles`, and it must
 * never be added to one, nor may batch mode be put into an entry file (`emit-route-facts.ts`,
 * `emit-technique-facts.ts`, ...), which every artefact hashes as its `emitter_md5`. So an artefact
 * written here records the md5 of an entry file that did not literally run; the two routes are the same
 * `build()` and `serialise()` calls, which is what the byte comparisons above establish.
 *
 * SHARING IS GUARDED.  Openers are grouped by `snapshotLocks`, one route digest per distinct value (today
 * all share one). Each digest is deep-frozen before the first build, so a build that wrote into a shared
 * digest would throw rather than hand the next build a different input.
 *
 *   bun pipeline/sim/emit-corpus-batch.ts --job <name>:<kind>:<key>:<out> [--job ...] [--wait <name> ...]
 *
 * <kind> is route (key: an OPENERS key), technique (a TECHNIQUES key), dpc or secondpc (key `-`). It
 * prints one line per event on stdout, for `bin/emit-corpus` to read as they come:
 *
 *   DIGEST <route|technique> <seconds>     a digest was built
 *   DONE <name> <seconds>                  <out> written; seconds are the build alone
 *   FAILED <name> <json message>           its build threw; the others still run
 *   WAIT <name>                            (only for --wait jobs) reads one stdin line: GO, or SKIP to
 *   SKIPPED <name>                         leave it unbuilt, e.g. because an input it reads failed
 *
 * A --wait job is built after the jobs without one, so the digest and the other builds overlap whatever
 * it waits for (in `bin/emit-corpus`, the route facts 基本的なドネイト and STSD read from analysis/).
 */
import { writeFileSync, readSync } from 'node:fs';
import * as RF from './route-facts.ts';
import * as TF from './technique-facts.ts';
import * as DPC from './dpc-facts.ts';
import * as SPC from './secondpc-facts.ts';
import { OPENERS } from './route-openers.ts';
import { TECHNIQUES } from './techniques.ts';

export type Kind = 'route' | 'technique' | 'dpc' | 'secondpc';
export interface Job { name: string; kind: Kind; key: string; out: string; wait?: boolean }

export type Event =
  | { ev: 'DIGEST'; group: 'route' | 'technique'; seconds: number }
  | { ev: 'DONE'; name: string; seconds: number; text: string }
  | { ev: 'FAILED'; name: string; message: string }
  | { ev: 'SKIPPED'; name: string };

/** Freeze every object reachable from `x`, so a write into a shared digest throws (modules are strict). */
export function deepFreeze<T>(x: T): T {
  const stack: any[] = [x];
  while (stack.length) {
    const o = stack.pop();
    if (o === null || typeof o !== 'object' || Object.isFrozen(o)) continue;
    Object.freeze(o);
    for (const v of Object.values(o)) if (v !== null && typeof v === 'object') stack.push(v);
  }
  return x;
}

const sec = (t: number) => (performance.now() - t) / 1000;

function profileOf(j: Job) {
  if (j.kind === 'route') {
    const P = OPENERS[j.key];
    if (!P) throw new Error(`emit-corpus-batch: unknown opener ${j.key}; known: ${Object.keys(OPENERS).join(', ')}`);
    return P;
  }
  if (j.kind === 'technique') {
    const P = TECHNIQUES[j.key];
    if (!P) throw new Error(`emit-corpus-batch: unknown technique ${j.key}; known: ${Object.keys(TECHNIQUES).join(', ')}`);
    return P;
  }
  if (j.kind !== 'dpc' && j.kind !== 'secondpc') throw new Error(`emit-corpus-batch: unknown kind ${j.kind}`);
  return null;
}

/** Group route jobs by `snapshotLocks`: one digest is shared only between openers that keep as many locks. */
export function routeGroups(jobs: Job[], openers: Record<string, { snapshotLocks: number }> = OPENERS): Map<number, Job[]> {
  const g = new Map<number, Job[]>();
  for (const j of jobs.filter(j => j.kind === 'route')) {
    const n = openers[j.key]?.snapshotLocks;
    if (typeof n !== 'number') throw new Error(`emit-corpus-batch: opener ${j.key} has no snapshotLocks`);
    g.set(n, [...(g.get(n) ?? []), j]);
  }
  return g;
}

/** Build every job, yielding events. `gate(job)` is asked before a `wait` job; false leaves it unbuilt.
 *  `builders` and `techniqueDigest` are injectable so a test can plant a build that writes into the
 *  digest without building a real one. */
export function* run(jobs: Job[], gate: (j: Job) => boolean = () => true,
                     builders: Partial<Record<Kind, (j: Job, d: any) => string>> = {},
                     techniqueDigest: () => any = () => TF.digestCorpus()): Generator<Event> {
  const seen = new Set<string>();
  for (const j of jobs) {
    if (seen.has(j.name)) throw new Error(`emit-corpus-batch: job ${j.name} given twice`);
    seen.add(j.name);
    profileOf(j);                                         // unknown keys fail before any digest is built
  }
  const B: Record<Kind, (j: Job, d: any) => string> = {
    route: (j, d) => RF.serialise(RF.build(OPENERS[j.key]!, {}, d)),
    technique: (j, d) => TF.serialise(TF.build(TECHNIQUES[j.key]!, {}, d)),
    dpc: (_j, d) => DPC.serialise(DPC.build({}, d)),
    secondpc: (_j, d) => SPC.serialise(SPC.build({}, d)),
    ...builders,
  };
  const order = (xs: Job[]) => [...xs.filter(j => !j.wait), ...xs.filter(j => j.wait)];
  function* buildAll(xs: Job[], d: any): Generator<Event> {
    for (const j of order(xs)) {
      if (j.wait && !gate(j)) { yield { ev: 'SKIPPED', name: j.name }; continue; }
      const t = performance.now();
      let text: string;
      try { text = B[j.kind](j, d); }
      catch (e: any) { yield { ev: 'FAILED', name: j.name, message: String(e?.stack ?? e) }; continue; }
      yield { ev: 'DONE', name: j.name, seconds: sec(t), text };
    }
  }
  for (const xs of routeGroups(jobs).values()) {
    const t = performance.now();
    const d = deepFreeze(RF.digestCorpus(OPENERS[xs[0]!.key]!));
    yield { ev: 'DIGEST', group: 'route', seconds: sec(t) };
    yield* buildAll(xs, d);
  }
  const tech = jobs.filter(j => j.kind !== 'route');
  if (tech.length) {
    const t = performance.now();
    const d = deepFreeze(techniqueDigest());
    yield { ev: 'DIGEST', group: 'technique', seconds: sec(t) };
    yield* buildAll(tech, d);
  }
}

export function parseJob(s: string): Job {
  const m = /^([^:]+):(route|technique|dpc|secondpc):([^:]+):(.+)$/.exec(s);
  if (!m) throw new Error(`emit-corpus-batch: --job wants <name>:<kind>:<key>:<out>, got ${s}`);
  return { name: m[1]!, kind: m[2] as Kind, key: m[3]!, out: m[4]! };
}

/** One line from stdin, read synchronously (the protocol is strictly one answer per WAIT). */
function readLine(): string {
  const buf = Buffer.alloc(1);
  let s = '';
  for (;;) {
    let n = 0;
    try { n = readSync(0, buf, 0, 1, null); }
    catch (e: any) { if (e?.code === 'EAGAIN') continue; throw e; }
    if (n === 0) return s;
    const c = buf.toString('utf8');
    if (c === '\n') return s;
    s += c;
  }
}

if (import.meta.main) {
  const argv = process.argv.slice(2);
  const jobs: Job[] = [];
  const waits = new Set<string>();
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--job') jobs.push(parseJob(argv[++i]!));
    else if (argv[i] === '--wait') waits.add(argv[++i]!);
    else throw new Error(`emit-corpus-batch: unknown argument ${argv[i]}`);
  }
  for (const w of waits) {
    const j = jobs.find(j => j.name === w);
    if (!j) throw new Error(`emit-corpus-batch: --wait ${w} names no job`);
    j.wait = true;
  }
  const out = (s: string) => process.stdout.write(s + '\n');
  const gate = (j: Job) => { out(`WAIT ${j.name}`); return readLine().trim() === 'GO'; };
  let failed = false;
  for (const e of run(jobs, gate)) {
    if (e.ev === 'DIGEST') out(`DIGEST ${e.group} ${e.seconds.toFixed(2)}`);
    else if (e.ev === 'DONE') {
      writeFileSync(jobs.find(j => j.name === e.name)!.out, e.text);
      out(`DONE ${e.name} ${e.seconds.toFixed(2)}`);
    } else if (e.ev === 'FAILED') { failed = true; out(`FAILED ${e.name} ${JSON.stringify(e.message)}`); }
    else out(`SKIPPED ${e.name}`);
  }
  process.exit(failed ? 1 : 0);
}
