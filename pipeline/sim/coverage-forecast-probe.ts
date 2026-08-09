/**
 * Is the 0 verified forecasts a COVERAGE artifact? Independent test, ignoring garbage. Answer: no.
 *
 * Detection runs on the verified prefix (~13.8% of placements), so the natural worry is that
 * forecasts are simply outside the window. This probes that with algorithms INDEPENDENT of the
 * outgoing-attack-timing gate, and restricted to the line-clear mechanism (garbage cases ignored,
 * since the garbage model is the thing that caps coverage):
 *
 *   1. The repo's own gate ladder. `frame+row` is the BOARD-ONLY oracle — it keeps the ige row
 *      (when+where a clear landed, a board fact) and drops the attack VALUE (a board+table function
 *      a table error can wrongly truncate). It is an independent verification a timing/table error
 *      cannot cut. `frame+amount` drops the row instead (looser). Measured: each widens coverage
 *      (+~140 / +~1,000 placements corpus-wide) and finds 0 line-clear forecasts.
 *   2. The pre-garbage deterministic oracle. Before the first RECEIVED garbage the board is a pure
 *      function of inputs+seed — verifiable with NO garbage model at all, independent of the attack
 *      stream. It extends coverage by +2,192 placements (up to +47% in a session) and finds 0.
 *   3. The absolute ceiling. Run the detector over the ENTIRE round, no prefix at all (100%
 *      coverage, boards past the first garbage are unreliable — this is a generous over-count):
 *      across all four sessions there is exactly ONE forecast_lineclear-labelled event, and the four
 *      clauses reject it. So even at 100% coverage the verified count is 0.
 *
 * Conclusion: the 0 is not a coverage artifact. Line-clear forecasts are absent by nature — real
 * play in this corpus is openers and self-builds — not hidden by the verified prefix. The only way
 * the number moves is a genuine change in play, not a better detector or a wider window.
 *
 *   REPLAY_DIR=sessions/2026-07-22 bun pipeline/sim/coverage-forecast-probe.ts
 */
import { loadCases, runCase, verifiedIndex, type Gate } from './verified-prefix.ts';
import { forecastMetric, isVerifiedForecast } from './forecast.ts';

const GATES: Gate[] = ['frame+amount+row', 'frame+row', 'frame+amount'];
const place: Record<string, number> = {}, fc: Record<string, number> = {};
for (const g of GATES) { place[g] = 0; fc[g] = 0; }
let rounds = 0, pregarbPlace = 0, pregarbFc = 0, ceilingLabelled = 0, ceilingVerified = 0;

for (const c of loadCases()) {
  rounds++;
  const r: any = runCase(c);
  const out = forecastMetric(r, true);
  const lineclear = (rec: any) => isVerifiedForecast(rec) && rec.kind !== 'forecast_garbage';

  for (const g of GATES) {
    const idx = verifiedIndex(r, c.truth, g);
    place[g]! += idx + 1;
    for (const rec of out.records)
      if (lineclear(rec) && rec.lockIndex <= idx && (rec.roofFrom == null || rec.roofFrom <= idx)) fc[g]!++;
  }

  // pre-garbage deterministic region: locks before the first received garbage insertion
  const gfr = c.gin.map((x: any) => x.confirmFrame ?? x.frame).filter((x: any) => x != null);
  const firstGarb = gfr.length ? Math.min(...gfr) : Infinity;
  let preIdx = -1; for (let i = 0; i < r.locks.length; i++) if (r.locks[i].frame < firstGarb) preIdx = i;
  const idx0 = verifiedIndex(r, c.truth, 'frame+amount+row');
  const preVerified = Math.max(preIdx, idx0);
  pregarbPlace += preVerified + 1;
  for (const rec of out.records)
    if (lineclear(rec) && rec.lockIndex <= preVerified && (rec.roofFrom == null || rec.roofFrom <= preVerified)) pregarbFc++;

  // ceiling: whole round, no prefix
  for (const rec of out.records) if (rec.kind === 'forecast_lineclear') { ceilingLabelled++; if (isVerifiedForecast(rec)) ceilingVerified++; }
}

console.log(`rounds ${rounds}`);
console.log(`gate ladder (verified placements / line-clear forecasts, garbage ignored):`);
for (const g of GATES) console.log(`  ${g.padEnd(18)} ${String(place[g]).padStart(5)}   forecasts ${fc[g]}`);
console.log(`pre-garbage oracle:  ${String(pregarbPlace).padStart(5)}   forecasts ${pregarbFc}`);
console.log(`ceiling (100% coverage, full round): forecast_lineclear labelled ${ceilingLabelled}, VERIFIED ${ceilingVerified}`);
