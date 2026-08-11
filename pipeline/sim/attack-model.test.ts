/**
 * TETR.IO's exact attack formula vs the sim's historical fitted approximation.
 *
 * The sim's attack table was fitted against the replay ige oracle, but two pieces were simplified:
 * the b2b bonus was capped at `>=3 ? 2 : 1`, and a comboing single (base+b2b == 0) multiplied 0 and
 * sent nothing. TETR.IO's real formula (skysomorphic/tetrio-attack-calculator) is a LOGARITHMIC b2b
 * level and a `floor(log1p(combo*1.25))` branch for the zero-base combo. Opting into the exact model
 * (`attackModel:'exact'`) reduces the verified-prefix's `amount` cuts and lifts coverage measurably
 * (34.24→36.21, 27.54→28.73, 31.16→32.81 % over three sessions) — this is the biggest single drift
 * lever found, and it is ground-truth-driven (the documented formula), not another fit.
 *
 * It is now the DEFAULT in BEST_OPTS (2026-08-11, +4.2% verified locks corpus-wide). It was opt-in
 * only to keep the quarantined sim artifacts byte-identical; that conservatism was overridden the
 * same way the `hoisted`-DAS fix was — regenerate forecast/opener facts and re-bless the audit pins,
 * since attack amount is board-independent and never touches facts.json. This still pins the exact
 * function itself.
 */
import { test, expect, describe } from 'bun:test';
import { b2bLevel } from './sim.ts';

describe('b2bLevel — TETR.IO logarithmic back-to-back level', () => {
  test('matches the reference b2bCountToLevel boundaries exactly', () => {
    const cases: [number, number][] = [
      [-1, 0], [0, 0], [1, 1], [2, 1], [3, 2], [7, 2], [8, 3], [23, 3],
      [24, 4], [66, 4], [67, 5], [184, 5], [185, 6], [503, 6], [504, 7], [1369, 7], [1370, 8], [99999, 8],
    ];
    for (const [count, level] of cases) expect(b2bLevel(count), `b2b ${count}`).toBe(level);
  });

  test('agrees with the fitted legacy rule exactly for b2b 1-7 (where the sim was already right)', () => {
    // legacy: b2b>0 -> (b2b>=3 ? 2 : 1). The exact level only diverges (upward) at b2b>=8.
    for (let b = 1; b <= 7; b++) expect(b2bLevel(b)).toBe(b >= 3 ? 2 : 1);
    expect(b2bLevel(8)).toBe(3);           // legacy would cap at 2 — the first real divergence
    expect(b2bLevel(8)).toBeGreaterThan(2);
  });

  test('monotonic non-decreasing (a longer b2b chain never sends less bonus)', () => {
    let prev = 0;
    for (let b = 0; b <= 2000; b++) { const l = b2bLevel(b); expect(l).toBeGreaterThanOrEqual(prev); prev = l; }
  });
});
