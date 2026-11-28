/**
 * The 合掌TSDパフェ constructed demos (`analysis/gasshotsd-demos.json`).
 *
 * One demo is built: the bag-1 基本形, from an empty board, with no held piece. Every other drawing
 * is named unbuilt (mirror, same occupancy, second shade, muted C, a continuation, or taller than
 * eight rows). The shared checks are `route-demo-checks.ts`.
 *
 * Run: bun test pipeline/openers/gasshotsd-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { build as buildFor, serialise } from '../sim/route-demos.ts';
import { GASSHOTSD, DEMO_UNBUILT } from '../sim/route-profile-gasshotsd.ts';
import { demoChecks } from './route-demo-checks.ts';

const C = demoChecks(GASSHOTSD, {
  unbuilt: DEMO_UNBUILT, spinLines: {}, spinExceptions: [], pieceReadings: [],
});

let BUILT: string | null = null;
const built = () => (BUILT ??= serialise(buildFor(GASSHOTSD)));

test('rebuilding reproduces the committed gasshotsd-demos.json byte for byte', () => {
  expect(built()).toBe(C.committedText());
}, 120_000);

test('the bag-1 demo re-runs and ends on the 基本形; everything else is named unbuilt', () => {
  const art = C.committed();
  expect(art.report_eligible).toBe(false);
  expect(art.constructed).toBe(true);
  expect(art.demos.map((d: any) => d.node)).toEqual(['bag1.left']);
  expect(C.checkAll(art)).toBeNull();
  const d = art.demos[0];
  expect(d.locks.some((l: any) => l[5])).toBe(false);
  expect(d.locks.length).toBe(7);
  expect(d.events).toEqual([]);
});
