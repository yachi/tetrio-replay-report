/**
 * The Rust `reach()` search (`reach-native.ts`, `oracle-rs/src/reach.rs`) against the TypeScript one it replaces
 * (`route-demos.ts`'s `searchAll` with `impl: 'ts'`): on every (engine, board, piece, no180) the demo planners ask,
 * the two Maps must be equal as JSON — every resting placement's cells, in discovery order, and each one's paths
 * (edges, arrival spin, cells), in order, with the same per-spin dedup.
 *
 * The queries are collected, not invented: `REACH_QUERIES.record` sees every cache miss while the committed demo
 * planners run. By default that is two openers (SDPC Spin, stick spin) and two techniques (STSD's demos, 千鳥格子's); with
 * REACH_NATIVE_FULL=1 (set on the weekly run) it is every opener with demos, every technique demo profile and the SDPC
 * loop demos. Both modes also re-plan our own 千鳥格子 designs from their published boards (the technique planner on a
 * board it builds; 千鳥格子's own drawings build none). A query another build already cached is asked once, so a
 * source's count is the queries it asked first. The counts are printed, not pinned. A second test compares the two
 * on generated ragged boards, every piece, with and without the 180 edge.
 *
 * Run: bun test pipeline/sim/reach-native.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build as buildRoute, newEngine, REACH_QUERIES, searchAll } from './route-demos.ts';
import { build as buildTechnique } from './technique-demos.ts';
import { build as buildLoop } from './sdpc-loop-demos.ts';
import { planOwn } from './technique-own.ts';
import { OPENERS } from './route-openers.ts';
import { TECHNIQUES, TECHNIQUE_DEMOS, TECHNIQUE_OWN } from './techniques.ts';
import { nativeEligible } from './reach-native.ts';

const FULL = process.env.REACH_NATIVE_FULL === '1';
const OPENER_KEYS = FULL ? Object.keys(OPENERS).filter(k => OPENERS[k]!.demos) : ['sdpcspin', 'stickspin'];
const TECHNIQUE_KEYS = FULL ? Object.keys(TECHNIQUE_DEMOS) : ['stsd', 'cutcopy'];

interface Q { eng: any; state: (string | null)[][]; piece: string; no180: boolean; from: string }

function collect(): Q[] {
  const seen = new Set<string>();
  const qs: Q[] = [];
  let from = '';
  const engs = new Map<any, number>();
  REACH_QUERIES.record = (eng, state, piece, no180) => {
    if (!engs.has(eng)) engs.set(eng, engs.size);
    const k = `${engs.get(eng)}|${no180 ? 1 : 0}|${piece}|${state.map(r => r.map(c => c ?? '.').join('')).join('/')}`;
    if (seen.has(k)) return;
    seen.add(k);
    qs.push({ eng, state: state.map(r => [...r]), piece, no180, from });
  };
  try {
    for (const k of OPENER_KEYS) { from = `opener ${k}`; buildRoute(OPENERS[k]!); }
    for (const k of TECHNIQUE_KEYS) { from = `technique ${k}`; buildTechnique(TECHNIQUES[k]!, TECHNIQUE_DEMOS[k]!); }
    if (FULL) { from = 'sdpc loop'; buildLoop(); }
    {
      for (const [k, OP] of Object.entries(TECHNIQUE_OWN)) {
        from = `own ${k}`;
        const DP = TECHNIQUE_DEMOS[k]!;
        const tr = JSON.parse(readFileSync(DP.transcriptionPath, 'utf8'));
        const art = JSON.parse(readFileSync(OP.artefactPath, 'utf8'));
        for (const b of art.boards) planOwn(TECHNIQUES[k]!, DP, tr, b.id, b.rows, OP.maxSteps);
      }
    }
  } finally { REACH_QUERIES.record = null; }
  return qs;
}

const asJson = (m: Map<string, any>) => JSON.stringify([...m]);

test(`native reach() equals the TS search on every query the demo planners ask${FULL ? ' (full)' : ''}`, () => {
  const qs = collect();
  expect(qs.length).toBeGreaterThan(0);
  const by = new Map<string, number>();
  let paths = 0;
  for (const q of qs) {
    expect(nativeEligible(q.eng, q.state)).toBe(true);
    const ts = searchAll(q.eng, q.state, q.piece, { no180: q.no180 }, 'ts');
    const nat = searchAll(q.eng, q.state, q.piece, { no180: q.no180 }, 'native');
    const a = asJson(ts), b = asJson(nat);
    if (a !== b) throw new Error(`reach mismatch (${q.from}, piece ${q.piece}, no180 ${q.no180})`);
    by.set(q.from, (by.get(q.from) ?? 0) + 1);
    for (const l of ts.values()) paths += l.length;
  }
  console.error(`reach-native: ${qs.length} distinct queries, ${paths} paths, equal; `
    + [...by].map(([k, v]) => `${k} ${v}`).join(', '));
}, FULL ? 3_600_000 : 300_000);

test('native reach() equals the TS search on generated boards, every piece, with and without 180', () => {
  // boards the planners never ask: ragged stacks with holes and overhangs, from a fixed LCG (no clock, no Math.random)
  const eng = newEngine({ source: { fetched: '2026-01-01' } });
  let seed = 12345;
  const rnd = (n: number) => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };
  let n = 0;
  for (let b = 0; b < (FULL ? 400 : 40); b++) {
    const state: (string | null)[][] = Array.from({ length: 40 }, () => new Array(10).fill(null));
    for (let x = 0; x < 10; x++) {
      const h = rnd(b % 4 === 0 ? 12 : 7);
      for (let y = 0; y < h; y++) if (rnd(6) > 0) state[y]![x] = 'g';
    }
    for (const piece of 'ijlostz') for (const no180 of [false, true]) {
      const a = asJson(searchAll(eng, state, piece, { no180 }, 'ts'));
      const c = asJson(searchAll(eng, state, piece, { no180 }, 'native'));
      if (a !== c) throw new Error(`reach mismatch on generated board ${b}, piece ${piece}, no180 ${no180}`);
      n++;
    }
  }
  console.error(`reach-native: ${n} generated queries, equal`);
}, FULL ? 1_800_000 : 120_000);
