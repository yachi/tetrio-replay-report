/**
 * `check_provenance.ts` under `bun test`, which is the only thing CI runs for `pipeline/sim`.
 *
 * The gate itself is argued in `check_provenance.ts`. This file exists so it cannot become a
 * manual-only gate — the class that let `tools/triangle-oracle/dual-backed.json` sit green through
 * two regenerations that moved every figure the README published from it, and that let `equiv.py`'s
 * coverage table be run by hand once on two of six sessions.
 *
 * Three legs, in the order that matters:
 *   1. the planted mutants — a gate whose selftest has stopped firing gates nothing — including
 *      the three CENSUS mutants, which are about cases that never entered the sweep rather than
 *      about a provenance map that is wrong;
 *   2. the corpus, over BOTH published board sources, with the census's denominator compared
 *      against an independent count of the cases on disk;
 *   3. the roof cells specifically, because that is the subset `forecastMetric` reads and it is
 *      where the defect this gate was written for lived.
 *
 * What none of the three can say is that every placer is CORRECT — the `letter` rule separates the
 * seven piece types and nothing finer, so a misattribution to a same-letter lock is admissible by
 * construction. See the header of `check_provenance.ts`; the figures are upper bounds on the defect,
 * and the wording "no impossible placer" is deliberate.
 *
 * There is no live control against the reconstruction that motivated the gate: it was deleted from
 * `tools/triangle-oracle/oracle-forecast.mjs` in the same change, having measured 544/2024 roof
 * cells (26.9%) and 1 191 905/3 811 813 placed cells (31.3%) inadmissible. Its stand-in is the
 * planted mutant named `the 2026-08-11 defect` in leg 1.
 */
import { test, expect } from 'bun:test';
import { provenanceViolations, roofAdmissibility, selftest, sessionDirs, sweep, sweepFailures } from './check_provenance.ts';

const ROOT = `${import.meta.dir}/../..`;
const DIRS = sessionDirs(ROOT);
const SOURCES = ['oracle-source.ts (published)', 'sim.ts hand-port (published)'];

test('the gate still fires: every planted mutant is caught', async () => {
  const lines: string[] = [];
  expect(await selftest(s => lines.push(s))).toBe(0);
  // A selftest that silently stopped planting anything would also return 0.
  expect(lines.filter(l => l.startsWith('  ok ')).length).toBeGreaterThanOrEqual(12);
});

test('sessions are globbed off disk, and an empty glob is a failure rather than a clean sweep', () => {
  expect(DIRS.length).toBeGreaterThan(0);
  expect(sessionDirs(`${ROOT}/pipeline`)).toEqual([]);
});

test('every placer both published board sources name is admissible, over every session on disk', async () => {
  const { loadCases } = await import('./verified-prefix.ts');
  const casesOnDisk = DIRS.reduce((n, d) => n + loadCases(d).length, 0);
  const results = await sweep(DIRS, SOURCES);
  expect(results.map(r => r.source)).toEqual(SOURCES);
  for (const r of results) {
    // Not merely "no violations": a source that produced no cells would also report none.
    expect(r.rounds).toBeGreaterThan(0);
    expect(r.placed).toBeGreaterThan(1_000_000);
    expect(r.roof).toBeGreaterThan(0);
    // The census's own denominator. The bounds above only catch a TOTAL die-off; a partial one —
    // 40% of rounds starting to throw — passes every one of them while shrinking the population
    // silently. `casesOnDisk` is an INDEPENDENT count: `loadCases` is what feeds the sweep but it
    // is not the builder, so "every case on disk was built" is a real comparison rather than the
    // sweep agreeing with itself. 760 is a floor, not a pin — a seventh session may only raise it,
    // so this needs no edit when one lands, while a corpus that shrank still fails.
    expect({ source: r.source, skipped: r.skipped, skips: r.skips, covered: r.rounds === casesOnDisk })
      .toEqual({ source: r.source, skipped: 0, skips: [], covered: true });
    expect(r.rounds).toBeGreaterThanOrEqual(760);
    expect({ source: r.source, hits: r.hits.slice(0, 3), counts: r.counts, roofBad: r.roofBad })
      .toEqual({ source: r.source, hits: [], roofBad: 0, counts: {
        'letter': 0, 'out-of-range': 0, 'future-placer': 0, 'prov-on-empty': 0,
        'null-on-filled': 0, 'placer-on-garbage': 0, 'garbage-on-placed': 0 } });
    // ...and the verdict the CLI actually exits on, so the two cannot drift apart.
    expect({ source: r.source, why: sweepFailures(r) }).toEqual({ source: r.source, why: [] });
  }
}, 600_000);

test('the roof cell of 2026-08-14 yachi r2 lock 19 names an S, and lock 10 is an S', async () => {
  // The one candidate this gate was written out of. Pinned as a literal rather than re-derived,
  // because a test that re-derives a value the way the code does can only catch a typo.
  const { loadCases, runCaseOracle, runCase } = await import('./verified-prefix.ts');
  const dir = `${ROOT}/sessions/2026-08-14`;
  const c = loadCases(dir).find(x =>
    x.file === 'replay-2026-08-14-10.ttrm' && x.round === 2 && x.user === 'yachi');
  expect(c).toBeDefined();
  for (const mk of [runCaseOracle, runCase]) {
    const r = mk(c!);
    expect(r.locks[19]!.piece).toBe('T' as never);
    expect(r.locks[10]!.piece).toBe('S' as never);
    expect(r.locks[12]!.piece).toBe('T' as never);
    // roof cell: directly above the T's own cell at (row 31, col 3)
    expect(r.boards[18]![30]![3]).toBe('S' as never);
    expect(r.provSnaps[18]![30]![3]).toBe(10);      // the S, not the T at lock 12
    expect(provenanceViolations(r).counts.letter).toBe(0);
    expect(roofAdmissibility(r).bad).toBe(0);
  }
}, 60_000);
