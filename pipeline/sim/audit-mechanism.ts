/**
 * Reports the mechanism behind every improved forecast event, across the simulator sweep.
 *
 * It does no analysis of its own — `forecastMetric` records `mechanism` and `mechanismStep` on
 * every record, and this reads them. It was written the other way round, with its own copy of the
 * board walk, and that copy is exactly the divergence `tspinAvailable` warns about further up: two
 * implementations of the same BFS in this directory once carried different caps. The first version
 * of this file also used a cruder rule than the metric ended up with ("the last step availability
 * rose" rather than "the step where the level was reached and held") and attributed 7 events to
 * garbage that the corrected rule attributes to a placement. A second opinion that is merely an
 * older opinion is worse than none.
 *
 * What it still does independently is vary the SIMULATOR: a mechanism that exists only at one set
 * of settings is a property of the settings, not of the player.
 *
 *   bun audit-mechanism.ts sessions/2026-07-28 [...]        # the fitted settings
 *   CONFIG=vanilla_srs bun audit-mechanism.ts sessions/...  # one of the seven swept configs
 */
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric } from './forecast.ts';

const SESSIONS = process.argv.slice(2);
if (!SESSIONS.length) throw new Error('usage: bun audit-mechanism.ts <session dir> [...]');

const CONFIGS: Record<string, any> = {
  best: {}, vanilla_srs: { kickset: 'SRS' }, strict_blockout: { blockout: 'strict' },
  locktime30: { locktime: 30 }, gravity05: { gravity: 0.05 },
  reference_queue: { queue: 'reference' }, frame_clock: { subframe: false },
};
const CFG = process.env.CONFIG ?? 'best';
if (!(CFG in CONFIGS)) throw new Error(`unknown CONFIG ${CFG}; one of ${Object.keys(CONFIGS)}`);

const byMechanism: Record<string, number> = {};
const named: string[] = [];

for (const session of SESSIONS) {
  process.env.REPLAY_DIR = session;
  for (const c of loadCases(session)) {
    const r = runCase(c, CONFIGS[CFG]);
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v || !rec.mechanism) continue;
      byMechanism[rec.mechanism] = (byMechanism[rec.mechanism] ?? 0) + 1;
      if (rec.mechanism === 'garbage' || rec.mechanism === 'line-clear' || rec.mechanism === 'unattributed')
        named.push(`  ${rec.mechanism.padEnd(12)} ${session} ${c.user} ${c.file} r${c.round}`
          + ` lock ${rec.lockIndex} roof ${rec.roofFrom} step ${rec.mechanismStep}`
          + ` avail ${rec.availAtRoof}->${rec.availAtSpin}`);
    }
  }
}

const total = Object.values(byMechanism).reduce((a, b) => a + b, 0);
console.log(`\n${total} improved events under CONFIG=${CFG}\n`);
for (const [m, n] of Object.entries(byMechanism).sort((a, b) => b[1] - a[1]))
  console.log(`  ${String(n).padStart(4)}  ${m}`);
if (named.length) { console.log('\nevery event with an external mechanism, or none:'); named.forEach(l => console.log(l)); }
