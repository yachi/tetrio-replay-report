/**
 * Every counted T-spin Forecast in the corpus, one row each, for the 中盤手法 Forecast page
 * (pipeline/forecast_page.py → docs/forecast.html).
 *
 * The per-session sim/forecast-facts.json tallies the same events per player; this artefact lists
 * them so a page can link each one to its replay moment. It runs the SAME loop as
 * emit-forecast-facts.ts's `tally` (oracle engine, verified prefix, `forecastMetric(r, true)`,
 * `isVerifiedForecast`), and forecast-events.test.ts holds its per-(session, player) counts equal to
 * every forecast-facts.json's `forecast_total`, which is the gate on that copy.
 *
 * Simulator output, quarantined like forecast-facts.json: `report_eligible: false`, no claim ids.
 *
 *   bun pipeline/sim/emit-forecast-events.ts --out analysis/forecast-events.json
 */
import { readFileSync, readdirSync, writeFileSync, existsSync } from 'node:fs';
import { forecastMetric, isVerifiedForecast } from './forecast.ts';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { SESSIONS_ROOT, md5Files } from './route-facts.ts';

export interface ForecastEvent {
  session: string; file: string; round_index0: number; match: number; round: number; player: string;
  /** the T lock (0-based, the player's own lock index), and the lock that placed the roof */
  lock: number; roof_lock: number | null; lines: number; kind: string; separation: number;
  mechanism: string | null; mechanism_step: number | null;
}

export function sessions(root = SESSIONS_ROOT): string[] {
  return readdirSync(root).filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d)
    && existsSync(`${root}/${d}/report/facts.json`)).sort();
}

export function eventsFor(session: string, root = SESSIONS_ROOT): ForecastEvent[] {
  const facts = JSON.parse(readFileSync(`${root}/${session}/report/facts.json`, 'utf8'));
  const pos = new Map<string, number>(facts.matches.map((m: any) => [m.file, m.index]));
  const out: ForecastEvent[] = [];
  for (const c of loadCases(`${root}/${session}`)) {
    const r = runCaseOracle(c);
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v || !isVerifiedForecast(rec)) continue;
      const match = pos.get(c.file);
      if (match === undefined) throw new Error(`${session} ${c.file}: not in facts.json`);
      out.push({ session, file: c.file, round_index0: c.round, match, round: c.round + 1, player: c.user,
        lock: rec.lockIndex, roof_lock: rec.roofFrom, lines: rec.lines, kind: rec.kind,
        separation: rec.separation, mechanism: rec.mechanism ?? null, mechanism_step: rec.mechanismStep ?? null });
    }
  }
  return out;
}

export function build(root = SESSIONS_ROOT) {
  const events = sessions(root).flatMap(s => eventsFor(s, root));
  return {
    schema: 'forecast-events/1',
    report_eligible: false,
    note: 'Every T-spin Forecast forecastMetric counts (isVerifiedForecast) inside the verified prefix, '
      + 'one row each. Simulator output: one engine, no second implementation, so no claim id.',
    md5: md5Files([`${import.meta.dir}/forecast.ts`, `${import.meta.dir}/emit-forecast-events.ts`]),
    events,
  };
}

if (import.meta.main) {
  const i = process.argv.indexOf('--out');
  if (i < 0) throw new Error('usage: --out <file>');
  writeFileSync(process.argv[i + 1]!, JSON.stringify(build(), null, 1) + '\n');
}
