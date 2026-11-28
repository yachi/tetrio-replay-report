/**
 * The 合掌TSDパフェ (Gassho TSD) route artefact (`analysis/gasshotsd-facts.json`, from
 * `pipeline/sim/emit-route-facts.ts --opener gasshotsd`).
 *
 * A REFERENCE OPENER the corpus does not play: zero rounds match the hole-empty 基本形 at 7 locks,
 * by colour or even by occupancy (no colour disagreement). Every other count is a compared zero.
 * The first match is a red build, and so is a change in the bag-1 opportunity split.
 *
 * Run: bun test pipeline/openers/gasshotsd.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, digestCorpus, type Mutants } from '../sim/route-facts.ts';
import { GASSHOTSD } from '../sim/route-profile-gasshotsd.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22',
   '2026-10-29', '2026-11-01', '2026-11-05', '2026-11-17', '2026-11-19', '2026-11-23', '2026-11-24',
   '2026-11-25', '2026-11-26', '2026-11-27']);

/** Clean 7-lock rounds that were compared and were not the 基本形. Pinned per player. */
const BAG1_OPPORTUNITIES = { pinglamb: 1920, yachi: 1562 };

const EMPTY_LISTS = ['bag2_garbage_stripped', 'bag2_none_tsd_before_complete', 'bag2_none_extra_piece',
  'bag2_none_moved_piece', 'bag2_none_unexplained', 'pc_off_page', 'bag2_handedness_mismatch',
  'multi_colour_resolved_by_branch', 'colour_disagree', 'pc_garbage_in_window'];

const committedText = () => readFileSync(GASSHOTSD.artefactPath, 'utf8');
const committed = () => JSON.parse(committedText());

let DIGESTS: ReturnType<typeof digestCorpus> | null = null;
const digests = () => (DIGESTS ??= digestCorpus(GASSHOTSD));

test('the corpus list is every session on disk', () => {
  expect(committed().sessions).toEqual(SESSIONS);
});

test('rebuilding reproduces the committed gasshotsd-facts.json byte for byte', () => {
  expect(serialise(build(GASSHOTSD, {}, digests()))).toBe(committedText());
}, 120_000);

test('no round matches, and the bag-1 opportunity split is pinned', () => {
  const art = committed();
  expect(art.report_eligible).toBe(false);
  expect(art.cases).toEqual([]);
  expect(art.outcomes).toEqual([]);
  expect(art.conditions).toEqual({});
  const routes = JSON.parse(readFileSync(GASSHOTSD.routesPath, 'utf8'));
  expect(art.nodes.map((n: any) => n.id)).toEqual(routes.nodes.map((n: any) => n.id));
  const bag1 = art.nodes.find((n: any) => n.id === 'bag1.left');
  expect(bag1.cases).toBe(0);
  expect(bag1.opportunities_by_player).toEqual(BAG1_OPPORTUNITIES);
  for (const n of art.nodes) {
    if (!n.measured) {
      expect(n.why, n.id).toMatch(/^(unmatchable: |mirror_of: |illustration|same_shape|image_only|text_only)/);
      continue;
    }
    if (n.id === 'bag1.left') continue;
    expect(n.cases, n.id).toBe(0);
    expect(n.opportunities, n.id).toBe(0);
  }
  for (const k of EMPTY_LISTS) expect(art.lists[k], k).toEqual([]);
  expect(Object.keys(art.lists).sort()).toEqual([...EMPTY_LISTS].sort());
});

const EQUIVALENT: (keyof Mutants)[] = ['noMirror', 'bag2Early', 'noLock7Test', 'lock7MirrorUnaware', 'noSwap',
  'noColour', 'unscoped', 'pcNeedsBag2', 'matchFromFilename', 'noGroupScope', 'noGarbageStrip', 'pcLinesOff',
  'spinMirrorUnaware', 'spinClearStops', 'zHoldFirst'];

test('ignoring garbage before the sample adds bag-1 opportunities', () => {
  const o = build(GASSHOTSD, { noGarbageStop: true }, digests());
  const opp = o.nodes.find((n: any) => n.id === 'bag1.left').opportunities;
  expect(opp).toBeGreaterThan(BAG1_OPPORTUNITIES.pinglamb + BAG1_OPPORTUNITIES.yachi);
  expect(o.cases).toEqual([]);
}, 120_000);

test('the mutants this corpus cannot exercise are equivalent, and named', () => {
  const base = committedText();
  for (const m of EQUIVALENT)
    expect(serialise(build(GASSHOTSD, { [m]: true } as Mutants, digests())), m).toBe(base);
}, 180_000);
