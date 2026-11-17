/**
 * emit-corpus-batch.ts writes the same bytes as each node's own entry file.
 *
 * The batch shares two digests across twenty-two `build()` calls, so what has to hold is that sharing
 * changes nothing: (1) every batched artefact equals the committed one, which each node's own test
 * rebuilds through its own `build()` and `bin/emit-corpus --check --unbatched` rebuilds through its
 * entry file; (2) for one node of each kind, the entry file run as a separate process right now writes
 * the same bytes as the batch (so (1) is not merely two stale copies agreeing); (3) a build that wrote
 * into the shared digest would throw instead of passing a different input on; (4) openers that keep a
 * different number of locks never share a digest; (5) no profile hashes the batch file, so adding it
 * moved no artefact's md5s and editing it never will.
 */
import { describe, expect, test } from 'bun:test';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, join } from 'node:path';
import { deepFreeze, routeGroups, run, type Job } from './emit-corpus-batch.ts';
import { OPENERS } from './route-openers.ts';
import { TECHNIQUES, TECHNIQUE_DEMOS, TECHNIQUE_OWN } from './techniques.ts';

const REPO = `${import.meta.dir}/../..`;
const BATCH = 'pipeline/sim/emit-corpus-batch.ts';

const jobsInto = (dir: string): Job[] => [
  ...Object.entries(OPENERS).map(([k, P]) => ({ name: basename(P.artefactPath, '.json'), kind: 'route' as const, key: k,
                                               out: join(dir, basename(P.artefactPath)) })),
  ...Object.entries(TECHNIQUES).map(([k, P]) => ({ name: basename(P.artefactPath, '.json'), kind: 'technique' as const,
                                                  key: k, out: join(dir, basename(P.artefactPath)) })),
  { name: 'dpc-facts', kind: 'dpc', key: '-', out: join(dir, 'dpc-facts.json') },
  { name: 'secondpc-facts', kind: 'secondpc', key: '-', out: join(dir, 'secondpc-facts.json') },
];

describe('emit-corpus-batch', () => {
  test('no profile hashes the batch file (it is not any artefact\'s input)', () => {
    const all = [...Object.values(OPENERS), ...Object.values(TECHNIQUES), ...Object.values(TECHNIQUE_DEMOS),
                 ...Object.values(TECHNIQUE_OWN)] as any[];
    for (const P of all) {
      const hashed = Object.values(P.hashFiles ?? {}).flat().map(String);
      expect(hashed.filter(f => f.includes('emit-corpus-batch'))).toEqual([]);
    }
  });

  test('openers with different snapshotLocks get different digests', () => {
    const jobs: Job[] = [{ name: 'a', kind: 'route', key: 'x', out: '' }, { name: 'b', kind: 'route', key: 'y', out: '' },
                         { name: 'c', kind: 'route', key: 'z', out: '' }];
    const g = routeGroups(jobs, { x: { snapshotLocks: 46 }, y: { snapshotLocks: 40 }, z: { snapshotLocks: 46 } });
    expect([...g.entries()].map(([n, js]) => [n, js.map(j => j.name)])).toEqual([[46, ['a', 'c']], [40, ['b']]]);
    expect(() => routeGroups([{ name: 'a', kind: 'route', key: 'x', out: '' }], { x: {} as any })).toThrow();
    // today every opener keeps one count, so one route digest is built
    expect(routeGroups(jobsInto('/x')).size).toBe(1);
  });

  test('a write into a frozen digest throws', () => {
    const d = deepFreeze([{ locks: [{ rows: ['b', 'a'] }] }]) as any;
    expect(() => { d[0].locks[0].rows[0] = 'b'; }).toThrow();
    expect(() => { d[0].locks.push({}); }).toThrow();
    expect(() => { d[0].locks[0].rows.sort(); }).toThrow();
  });

  test('a job given twice, or an unknown key, fails before any digest is built', () => {
    const j: Job = { name: 'a', kind: 'dpc', key: '-', out: '' };
    expect(() => [...run([j, j])]).toThrow(/twice/);
    expect(() => [...run([{ name: 'b', kind: 'technique', key: 'nope', out: '' }])]).toThrow(/unknown technique/);
  });

  test('batch == committed for all twenty-two, and == the entry file run on its own for one of each kind', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'emit-corpus-batch-'));
    try {
      const jobs = jobsInto(dir);
      // the entry files, each in its own process, at the same time as the batch below
      const single = [
        ['honey-cup-facts.json', ['pipeline/sim/emit-route-facts.ts', '--opener', 'honeycup']],
        ['cavetsstst-facts.json', ['pipeline/sim/emit-technique-facts.ts', '--technique', 'cavetsstst']],
        ['secondpc-facts.json', ['pipeline/sim/emit-secondpc-facts.ts']],
      ] as const;
      const procs = single.map(([out, argv]) => Bun.spawn(['bun', ...argv, '--out', join(dir, `single-${out}`)],
                                                           { cwd: REPO, stdout: 'ignore', stderr: 'pipe' }));
      const batch = Bun.spawn(['bun', BATCH, ...jobs.flatMap(j => ['--job', `${j.name}:${j.kind}:${j.key}:${j.out}`])],
                              { cwd: REPO, stdout: 'pipe', stderr: 'pipe', stdin: 'ignore' });
      const [code, said] = [await batch.exited, await new Response(batch.stdout).text()];
      expect({ code, stderr: code ? await new Response(batch.stderr).text() : '' }).toEqual({ code: 0, stderr: '' });
      const lines = said.trim().split('\n');
      expect(lines.filter(l => l.startsWith('DIGEST')).map(l => l.split(' ')[1])).toEqual(['route', 'technique']);
      expect(lines.filter(l => l.startsWith('DONE')).map(l => l.split(' ')[1]).sort())
        .toEqual(jobs.map(j => j.name).sort());
      const differs = jobs.filter(j => readFileSync(j.out, 'utf8') !== readFileSync(`${REPO}/analysis/${basename(j.out)}`, 'utf8'));
      expect(differs.map(j => j.name)).toEqual([]);
      for (const [i, [out]] of single.entries()) {
        expect(await procs[i]!.exited).toBe(0);
        expect(readFileSync(join(dir, `single-${out}`), 'utf8') === readFileSync(join(dir, out), 'utf8')).toBe(true);
      }
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  }, 900_000);

  test('a WAIT answered SKIP leaves the job unbuilt, and the others still run', () => {
    // a build is injected, so no digest needs to be real: dpc/secondpc share the technique group
    const ev = [...run([{ name: 'w', kind: 'dpc', key: '-', out: '', wait: true },
                        { name: 'n', kind: 'secondpc', key: '-', out: '' }],
                       () => false, { dpc: () => 'D', secondpc: () => 'S' }, () => [])];
    expect(ev.map(e => [e.ev, (e as any).name ?? (e as any).group])).toEqual([['DIGEST', 'technique'], ['DONE', 'n'], ['SKIPPED', 'w']]);
  });

  test('a build that writes into the shared digest fails that job, and the next build still gets it unchanged', () => {
    const seen: any[] = [];
    const ev = [...run([{ name: 'bad', kind: 'dpc', key: '-', out: '' }, { name: 'ok', kind: 'secondpc', key: '-', out: '' }],
                       undefined,
                       { dpc: (_j, d) => { d.push(1); return 'x'; }, secondpc: (_j, d) => { seen.push(d.length); return 'y'; } },
                       () => [{ a: 1 }])];
    expect(ev.map(e => e.ev)).toEqual(['DIGEST', 'FAILED', 'DONE']);
    expect(seen).toEqual([1]);
  });
});
