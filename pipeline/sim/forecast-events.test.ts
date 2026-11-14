/**
 * analysis/forecast-events.json, the Forecast page's list of every counted T-spin Forecast, is a
 * second copy of emit-forecast-facts.ts's tally loop. This holds the copy to the original: the
 * committed artefact rebuilds byte for byte, and its per-(session, player) counts equal every
 * sessions/<date>/sim/forecast-facts.json's `forecast_total`.
 */
import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, sessions } from './emit-forecast-events.ts';
import { SESSIONS_ROOT } from './route-facts.ts';

const REL = `${import.meta.dir}/../../analysis/forecast-events.json`;
const committed = JSON.parse(readFileSync(REL, 'utf8'));

describe('forecast-events.json', () => {
  test('quarantined and nonempty', () => {
    expect(committed.report_eligible).toBe(false);
    expect(committed.events.length).toBeGreaterThan(0);
  });

  test('every count equals forecast-facts.json, per session and player', () => {
    const tally = new Map<string, { total: number; lineclear: number; garbage: number }>();
    for (const e of committed.events) {
      const k = `${e.session} ${e.player}`;
      const t = tally.get(k) ?? { total: 0, lineclear: 0, garbage: 0 };
      t.total++;
      if (e.kind === 'forecast_lineclear') t.lineclear++;
      else if (e.kind === 'forecast_garbage') t.garbage++;
      else throw new Error(`${k}: unknown kind ${e.kind}`);
      tally.set(k, t);
    }
    let seen = 0;
    for (const s of sessions()) {
      const ff = JSON.parse(readFileSync(`${SESSIONS_ROOT}/${s}/sim/forecast-facts.json`, 'utf8'));
      for (const p of ff.players) {
        const t = tally.get(`${s} ${p.user}`) ?? { total: 0, lineclear: 0, garbage: 0 };
        // forecast_total is the isVerifiedForecast count; forecast_lineclear / _garbage count the
        // kinds before that filter, so they bound this artefact's split rather than equal it.
        expect([s, p.user, t.total]).toEqual([s, p.user, p.forecast_total]);
        expect(t.lineclear).toBeLessThanOrEqual(p.forecast_lineclear);
        expect(t.garbage).toBeLessThanOrEqual(p.forecast_garbage);
        if (t.total) seen++;
      }
    }
    expect(seen).toBe(tally.size);
  });

  test('the committed artefact rebuilds byte for byte', () => {
    expect(JSON.stringify(build(), null, 1) + '\n').toBe(readFileSync(REL, 'utf8'));
  }, 1_800_000);
});
