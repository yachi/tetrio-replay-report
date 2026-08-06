/**
 * Throwaway: how big are the clears that happen inside a roof -> spin window, and how big was the
 * one that ever formed a slot? If the corpus's 1-of-654 rested on never seeing a Double, Triple or
 * Tetris in a window, that would be a sampling blind spot rather than a result.
 *
 *   bun run clear-sizes.ts sessions/2026-07-22 [...]
 */
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric } from './forecast.ts';

const inWindow: Record<number, number> = {};   // clears strictly between roof and spin
const wholePrefix: Record<number, number> = {};
const causing: Record<number, number> = {};    // the clear at the step that raised availability
let events = 0, windowsWithBig = 0;

for (const session of process.argv.slice(2)) {
  process.env.REPLAY_DIR = session;
  for (const c of loadCases(session)) {
    const r = runCase(c, {});
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (let i = 0; i <= v; i++) {
      const n = r.locks[i]!.cleared;
      if (n > 0) wholePrefix[n] = (wholePrefix[n] ?? 0) + 1;
    }
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v || rec.roofFrom === null) continue;
      events++;
      let big = false;
      for (let i = rec.roofFrom + 1; i < rec.lockIndex; i++) {
        const n = r.locks[i]!.cleared;
        if (n > 0) { inWindow[n] = (inWindow[n] ?? 0) + 1; if (n >= 2) big = true; }
      }
      if (big) windowsWithBig++;
      if (rec.mechanism === 'line-clear' && rec.mechanismStep != null)
        causing[r.locks[rec.mechanismStep]!.cleared] = (causing[r.locks[rec.mechanismStep]!.cleared] ?? 0) + 1;
    }
  }
}

const show = (label: string, m: Record<number, number>) => {
  const tot = Object.values(m).reduce((a, b) => a + b, 0);
  console.log(`${label} (${tot} clears)`);
  for (const n of [1, 2, 3, 4])
    console.log(`  ${n}-row: ${String(m[n] ?? 0).padStart(5)}  ${tot ? ((m[n] ?? 0) / tot * 100).toFixed(1) : '0.0'}%`);
};
show('every clear in the verified prefix', wholePrefix);
show('clears inside a roof -> spin window', inWindow);
show('the clear at the causing step, where the mechanism was a line clear', causing);
console.log(`\n${windowsWithBig} of ${events} windows contain a clear of 2 rows or more`);
