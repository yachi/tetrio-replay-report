/**
 * The Rust port of `minNeed` (`pipeline/sim/oracle-rs/src/cutcopy.rs`, via `cutcopy-native.ts`) must answer exactly as
 * the TS reference `minNeedTs` does: the same depth, the same `{ beyond, cut }`. The drills' difficulty (and so
 * `analysis/cutcopy-drills.json`) rests on it. Every committed drill is asked at caps 1-3 under `CUTCOPY_NATIVE_FULL=1`
 * (the weekly run sets it); by default cap 3, the slow reference search, is asked on a stride only.
 */
import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import { loadTranscription } from '../sim/technique-facts.ts';
import { minNeedTs, windowsFor, E, PATHS, MIN_FRONTIER } from '../sim/cutcopy-drills.ts';
import { minNeedNative } from '../sim/cutcopy-native.ts';

const FULL = process.env.CUTCOPY_NATIVE_FULL === '1';
const A = JSON.parse(readFileSync(PATHS.out, 'utf8'));
const WINDOWS = windowsFor(loadTranscription(PATHS.transcription));
E.setWindows(WINDOWS);

const native = (d: any, cap: number, windows = WINDOWS, frontier = MIN_FRONTIER) => {
  const run = E.newRun(d);
  return minNeedNative(d, run.board, run.hold, windows, cap, frontier);
};

describe('cutcopy minNeed: Rust == TS', () => {
  test('every drill, caps 1-3 (cap 3 on a stride unless FULL)', () => {
    let n = 0;
    A.drills.forEach((d: any, i: number) => {
      for (const cap of [1, 2, 3]) {
        if (cap === 3 && !FULL && i % 4 !== 0) continue;
        expect(native(d, cap)).toEqual(minNeedTs(d, cap));
        n++;
      }
    });
    expect(n).toBeGreaterThan(30);
    console.log(`cutcopy-native: ${n} (drill, cap) cases equal${FULL ? ' (full)' : ''}`);
  }, 900_000);

  test('controls: the answers are not all one kind', () => {
    const seen = new Set(A.drills.map((d: any) => JSON.stringify(native(d, 3))));
    expect(seen.size).toBeGreaterThan(1);
    // no window: nothing is ever buildable, both say beyond
    E.setWindows([]);
    try { for (const d of A.drills.slice(0, 3)) expect(native(d, 2, [])).toEqual(minNeedTs(d, 2)); }
    finally { E.setWindows(WINDOWS); }
    // a tiny frontier cuts the search where the cap would not
    const cut = A.drills.map((d: any) => native(d, 3, WINDOWS, 1)).filter((r: any) => typeof r !== 'number' && r.cut);
    expect(cut.length).toBeGreaterThan(0);
  }, 120_000);
});
