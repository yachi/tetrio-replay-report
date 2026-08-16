/**
 * Guards on the emitted forecast facts artifact.
 *
 * The point of these is that the artifact must never quietly become MORE confident than the
 * evidence: it is simulator-derived, so its eligibility flag and its reasons are load-bearing
 * and are asserted here rather than left to review.
 */
import { test, expect, describe } from 'bun:test';
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { UNATTRIBUTED_STEP_MODEL_GAP as SHARED_UNATTRIBUTED_STEP_MODEL_GAP } from './step-model-gap.ts';

// FORECAST_FACTS points the whole file at one session's artifact, so one guard covers every
// emitted artifact rather than only the session it happens to live beside. The emitter is
// shared (`--out` + REPLAY_DIR); its guards have to be too, or three of the four artifacts
// ship unchecked.
//
// The default was `${import.meta.dir}/forecast-facts.json`, which resolved only because this
// test lived inside 2026-07-22. From pipeline/sim there is no artifact beside the code, so it
// DISCOVERS them — naming a session here would quietly re-privilege one inside what is now
// shared code, which is the whole thing this move exists to end.
//
// ── AND IT RUNS OVER ALL OF THEM, NOT `DISCOVERED[0]` (2026-08-16) ───────────────────────────────
// Discovering every artifact and then checking `DISCOVERED[0]` is discovery in name only: sorted,
// [0] is always the OLDEST session, so for six sessions this file re-checked 2026-07-22 six times
// and no other artifact was ever read by a default run. It shipped that way, and it hid a live
// violation — 2026-08-14's `unattributed` is 1, against the invariant asserted below, and has been
// since the session's first commit (d845b3f). Running `FORECAST_FACTS` per session by hand is what
// found it, i.e. the guard depended on somebody remembering to loop; that is the failure mode this
// loop removes. `FORECAST_FACTS` still narrows to one artifact for a fast iteration.
const SESSIONS = `${import.meta.dir}/../../sessions`;
const SESSION_DIRS = readdirSync(SESSIONS, { withFileTypes: true })
  .filter(d => d.isDirectory()).map(d => d.name).sort();
const DISCOVERED = SESSION_DIRS
  .map(s => `${SESSIONS}/${s}/sim/forecast-facts.json`)
  .filter(existsSync);
const OVERRIDE = process.env.FORECAST_FACTS;
const ARTEFACTS = OVERRIDE ? [OVERRIDE] : DISCOVERED;
if (!ARTEFACTS.length) throw new Error('no sessions/*/sim/forecast-facts.json found, and FORECAST_FACTS is unset');

// Covering "every artifact discovery happened to find" is the weaker of the two statements, and it
// is the one that goes quiet when a session ships without its artifact — a session directory with
// no forecast-facts.json subtracts itself from the corpus AND from the guard in one step, which is
// the shape recorded in `sim-test-corpus-silently-under-covers`. Name the sessions, not the files.
test('every session directory has an artifact for the loop below to check', () => {
  if (OVERRIDE) return;   // deliberately narrowed to one; coverage is not the question being asked
  const missing = SESSION_DIRS.filter(s => !existsSync(`${SESSIONS}/${s}/sim/forecast-facts.json`));
  expect(missing).toEqual([]);
  expect(DISCOVERED.length).toBe(SESSION_DIRS.length);
});

/**
 * The one improvement in six sessions that the step model cannot explain, named rather than
 * excused by a bound. The full trace, its controls and its corpus counts are at the assertion
 * that consumes this, in `counts are internally consistent and integers`.
 *
 * Shape borrowed from `DT_ORDER_IN_OPENER` in pipeline/openers/openers.test.ts, and for its
 * reason: `expect(x).toBe(known)` is exact in BOTH directions, so a second such event fails and
 * so does this one vanishing. `toBeLessThanOrEqual(1)` would be satisfied by any single
 * unexplained improvement anywhere in the corpus, which is the investigation this list exists to
 * force. The reciprocal — an entry that stops naming a real event — is checked separately below,
 * because a session that is renamed or removed would otherwise take its own exception with it.
 */
// The list itself lives in step-model-gap.ts, because forecast-corpus.test.ts needs the same
// events summed per session and a hand-written mirror of it is one fact in two places.
const UNATTRIBUTED_STEP_MODEL_GAP = SHARED_UNATTRIBUTED_STEP_MODEL_GAP;

// The other direction, and it cannot be folded into the loop above: the loop only visits sessions
// that EXIST, so an entry naming a session that was renamed or dropped is never consulted and its
// exception silently stops being tested. Same reciprocal `check_loo.py` keeps for ANNOTATED — a
// case that stops crossing has to come off the list, not sit there being satisfied by nothing.
test('every UNATTRIBUTED_STEP_MODEL_GAP entry still names a real event', () => {
  if (OVERRIDE) return;   // one artifact in view; the list as a whole is not what is being asked
  for (const [s, byUser] of Object.entries(UNATTRIBUTED_STEP_MODEL_GAP)) {
    const path = `${SESSIONS}/${s}/sim/forecast-facts.json`;
    expect([s, existsSync(path)]).toEqual([s, true]);
    const d = JSON.parse(readFileSync(path, 'utf8'));
    for (const [user, n] of Object.entries(byUser)) {
      const p = d.players.find((x: any) => x.user === user);
      expect([s, user, p !== undefined]).toEqual([s, user, true]);
      // an entry pinned at 0 would be an exception excusing nothing — take it out instead
      expect(n).toBeGreaterThan(0);
      expect([s, user, p.unattributed]).toEqual([s, user, n]);
    }
  }
});

for (const PATH of ARTEFACTS) {
  const SESSION = PATH.split('/').slice(-3, -2)[0] ?? PATH;
  describe(SESSION, () => {
  const load = () => JSON.parse(readFileSync(PATH, 'utf8'));

  test('the artifact exists and declares itself ineligible for the report', () => {
    expect(existsSync(PATH)).toBe(true);
    const d = JSON.parse(readFileSync(PATH, 'utf8'));
    expect(d.schema).toBe('forecast-facts/8');
    // simulator-derived data must never be promoted to a report claim without the
    // dual-extractor rule being satisfied; this flag is the guard
    expect(d.report_eligible).toBe(false);
    expect(d.not_eligible_because.length).toBeGreaterThanOrEqual(3);
    // Counting reasons without reading them is the shape of check that let a stale reliability
    // figure survive: a session whose rate is identically 0 must SAY the per-round rate has no
    // variance, not silently drop the line when the numerator stops firing.
    if (d.statistics.reliability && d.players.every((p: any) => p.forecast_rate_x1000 === 0))
      expect(d.not_eligible_because.join(' ')).toContain('identically 0');
  });

  test('reliability is computed on the same numerator as the published rate', () => {
    const d = load();
    const rel = d.statistics.reliability;
    if (!rel) return;
    // A rate of 0 for every player means the per-round rate is CONSTANT, so a correlation over it
    // is undefined and `pearson` returns null. A number here would mean the reliability block was
    // computed from a different predicate than the one behind forecast_rate_x1000 — which is exactly
    // how the superseded kind!=='reactive' numerator kept publishing a figure the metric had dropped.
    if (d.players.every((p: any) => p.forecast_rate_x1000 === 0)) {
      for (const v of Object.values(rel.split_half_r_x1000)) expect(v).toBeNull();
      for (const v of Object.values(rel.rounds_for_r70)) expect(v).toBeNull();
    }
  });

  test('the session block accounts for the coverage the report quotes', () => {
    const s = load().session;
    for (const k of ['player_rounds', 'verified_placements', 'total_placements'])
      expect(Number.isInteger(s[k])).toBe(true);
    expect(s.verified_placements).toBeLessThanOrEqual(s.total_placements);
    // coverage floors, like every other printed figure
    expect(s.coverage_x1000 * s.total_placements).toBeLessThanOrEqual(1000 * s.verified_placements);
    expect(1000 * s.verified_placements).toBeLessThan((s.coverage_x1000 + 1) * s.total_placements);
  });

  test('every statistics block is present or explicitly null — never absent', () => {
    const st = load().statistics;
    // A missing key reads as `undefined` in the renderer and would render as an empty string
    // rather than as an absence. The contract is that the key always exists.
    for (const k of ['round', 'event', 'player', 'reliability']) expect(k in st).toBe(true);
  });

  test('intervals contain their point estimate, and bounds widened rather than tightened', () => {
    const st = load().statistics;
    const cs = [st.event?.attack, st.event?.lines, st.event?.balance?.stack_height,
                st.event?.balance?.garbage_pressure, st.event?.negative_control].filter(Boolean);
    // With zero VERIFIED forecasts there is no forecast arm, so every cluster contrast is
    // legitimately null — there is nothing to compare reactive events against. Assert that
    // explicitly rather than letting an empty list pass as if the checks had run: an empty
    // sample silently satisfying a for-loop is how a gate proves nothing while reporting ok.
    // An arm too small to have a mean worth comparing yields null contrasts, exactly as an empty
    // arm does. The threshold lives in `forecast-event-level.ts`; asserting on the emitted
    // `forecast_n` here keeps the artifact honest without importing the simulator into a guard.
    const forecastN = st.event?.forecast_n ?? 0;
    if (forecastN < 5) { expect(cs.length).toBe(0); return; }
    expect(cs.length).toBeGreaterThan(0);
    for (const c of cs) {
      // Negative differences are legal here — this is a signed contrast, not a rate. A consumer
      // that assumes non-negative would silently mis-order the bounds.
      expect(c.ci95_lo_x1000).toBeLessThanOrEqual(c.diff_x1000);
      expect(c.ci95_hi_x1000).toBeGreaterThanOrEqual(c.diff_x1000);
      // `excludes_zero` must be computed from the interval, not asserted alongside it
      expect(c.excludes_zero).toBe(c.ci95_lo_x1000 > 0 || c.ci95_hi_x1000 < 0);
    }
  });

  test('the negative control fires exactly when its own interval excludes zero', () => {
    const nc = load().statistics.event?.negative_control;
    if (!nc) return;
    // This is the guard that keeps the confound honest: `fires` true means the difference also
    // appears in a window the mechanism cannot reach, so the primary is measuring context.
    expect(nc.fires).toBe(nc.excludes_zero);
  });

  test('p-values CEIL, because a p rounded down overstates significance', () => {
    const st = load().statistics;
    // Reconstructed from the counts the same p was computed over: the ceiled x1000 value must be
    // the smallest integer at or above 1000p, so p > (v-1)/1000. Checked against the DEFINING
    // inequality rather than a remembered constant.
    const r = st.round;
    if (r?.exact_p_x1000 != null) {
      expect(Number.isInteger(r.exact_p_x1000)).toBe(true);
      expect(r.exact_p_x1000).toBeGreaterThan(0);      // a p of exactly 0 would floor-print as 0.000
      expect(r.exact_p_x1000).toBeLessThanOrEqual(1000);
      expect(r.decided).toBe(r.wins + r.losses);
    }
    if (st.player?.exact_p_x1000 != null) {
      expect(Number.isInteger(st.player.exact_p_x1000)).toBe(true);
      expect(st.player.k).toBeLessThanOrEqual(st.player.n);
    }
  });

  test('reliability reports unreachable as null, not as a large number of rounds', () => {
    const rel = load().statistics.reliability;
    if (!rel) return;
    for (const [u, r] of Object.entries(rel.split_half_r_x1000) as [string, number | null][]) {
      const need = rel.rounds_for_r70[u];
      // r <= 0 means NO amount of aggregation reaches 0.70. That is a different statement from
      // "it takes many rounds" and must not be rendered as a round count.
      if (r === null || r <= 0) { expect(need).toBe(null); continue; }
      expect(Number.isInteger(need)).toBe(true);
      // Type alone is not a guard: `999` passed `isInteger` and said nothing about whether the
      // count came from Spearman-Brown at all. Reconstruct it. The emitted r is FLOORED to
      // x1000, so the true r lies in [r, r+1)/1000; need(r) = ceil((T/(1-T)) * (1-r)/r) is
      // decreasing in r, so the true count is bracketed by evaluating at both ends.
      const T = 0.7, sb = (x: number) => Math.ceil((T / (1 - T)) * (1 - x) / x);
      expect(need).toBeGreaterThanOrEqual(sb((r + 1) / 1000));
      expect(need).toBeLessThanOrEqual(sb(r / 1000));
    }
  });

  test('the derived reasons quote this session, not a remembered one', () => {
    const d = load();
    const joined = d.not_eligible_because.join(' ');
    const rel = d.statistics.reliability;
    if (rel) {
      // Every reliability the reason string names must be one this session actually measured.
      // The minus sign is not optional in this pattern: a correlation may be negative, and a
      // regex that skipped it read "-0.132" as 0.132 and compared it to -0.133. That miss is
      // how the two-roundings bug reached a committed artifact.
      for (const m of joined.matchAll(/(-?[0-9]\.[0-9]{3}) \(([^)]+)\)/g)) {
        const [, val, user] = m;
        expect(rel.split_half_r_x1000[user!]).not.toBe(undefined);
        // exact, not approximate: both sides must come from the SAME rounding of r11
        expect(rel.split_half_r_x1000[user!]! / 1000).toBe(Number(val));
      }
    }
    // and every p it names must match the emitted one to the digit it prints
    const ps = [...joined.matchAll(/p=([0-9]\.[0-9]{3})/g)].map(m => Number(m[1]));
    const emitted = [d.statistics.round?.exact_p_x1000, d.statistics.player?.exact_p_x1000]
      .filter(v => v != null).map(v => v / 1000);
    for (const p of ps) expect(emitted).toContain(p);
  });

  test('counts are internally consistent and integers', () => {
    const d = JSON.parse(readFileSync(PATH, 'utf8'));
    expect(d.players.length).toBe(2);
    for (const p of d.players) {
      // `mechanism_established` is the two MECHANISM-ESTABLISHED kinds; self_built must never be
      // folded in — that is the opener case, and folding it back is precisely the over-count this
      // schema exists to correct. `forecast_total` then applies clause 2 (the hole pre-existed) ON
      // TOP, so it is a subset: forecast_total <= mechanism_established, equal only when clause 2
      // rejects nothing. The old assertion `forecast_total === fg + fl` asserted the stronger thing
      // and is FALSE on 2026-07-28 (pinglamb's one line-clear event has a floor that arrived later,
      // so clause 2 rejects it: mechanism_established 1, forecast_total 0). It never fired because
      // this file checks 2026-07-22 by default, where clause 2 rejects nothing. Corrected + widened
      // to every session (FORECAST_FACTS) here.
      expect(p.mechanism_established).toBe(p.forecast_garbage + p.forecast_lineclear);
      expect(p.forecast_total).toBeLessThanOrEqual(p.mechanism_established);
      expect(p.verified_tspins).toBe(
        p.forecast_garbage + p.forecast_lineclear + p.self_built + p.reactive);
      // The DENOMINATOR's scope, gated (schema 8). `verified_tspins` is the TUCKED, line-clearing
      // T-spins; `admitted_lineclearing_tspins` is EVERY line-clearing verifiable T-spin, so the
      // difference is exactly the untucked and the snapshot-less. Without this the report could go
      // back to calling `verified_tspins` "all verifiable T-spins" — the numerator had a gate for
      // weeks while this leg had none, which is how the numerator bug hid. Also pins the drop counts
      // as non-negative integers so a mislabelled or double-counted drop is a test failure.
      for (const k of ['admitted_lineclearing_tspins', 'tspins_excluded_untucked',
                       'tspins_excluded_no_snapshot', 'tspins_excluded_zero_clear']) {
        expect(Number.isInteger(p[k])).toBe(true);
        expect(p[k]).toBeGreaterThanOrEqual(0);
      }
      expect(p.admitted_lineclearing_tspins).toBe(
        p.verified_tspins + p.tspins_excluded_untucked + p.tspins_excluded_no_snapshot);
      // An improvement the step model cannot explain is a defect in the model, not a category.
      // If this ever exceeds 0, the buckets below it stop meaning what they say.
      //
      // ── IT EXCEEDS 0 ONCE, AND THAT ONCE IS NAMED (2026-08-16) ──────────────────────────────
      // 2026-08-14 yachi is 1, and has been since that session's first commit (d845b3f). Pinned
      // by name in UNATTRIBUTED_STEP_MODEL_GAP above, NOT relaxed to a bound, because the event
      // was traced and the model really is missing an edit:
      //
      //   replay-2026-08-14-0.ttrm r4 (m1r5) yachi, lock 74, a T-spin Double. Roof at lock 64,
      //   availability 1 -> 2, causing step localised to lock 70. The slot the T executed into
      //   is at rows 35-37, and rows 34-39 are bit-identical in A = boards[69] and in B.
      //   Deleting row 33 from A ALONE — no piece cells, no other edit — already yields that
      //   same 2-line slot:
      //       A                      best=1  rows [32,32,32,33,31]
      //       A minus row 33 (no T)  best=2  rows [36,36,36,37,35]
      //       A minus row 31/32/34   best=0 / 0 / 1     (controls: not "any deletion helps")
      //   So the clear did not FORM the slot — it removed the lid over one that already existed
      //   and was unreachable. `bestTspin` is a BFS from spawn, so its availability is
      //   REACHABILITY, and `localiseMechanism`'s geometric rule ("a cleared row outside the
      //   slot displaced it rigidly and cannot have formed it", forecast.ts:494) is sound about
      //   formation and silent about access. There is no bucket for it, so it falls through.
      //
      // The reason the entry is one line and the hole is bigger than one line: `unattributed`
      // DETECTS ONLY HALF OF ITS OWN CLASS. Sweeping all six sessions for "the cleared rows
      // ALONE reach the target, and no cleared row lies strictly inside the slot" finds 2 events
      // among 1789 localised records (3926 records in the verified prefixes; the rest are never
      // localised at all), and 0 beyond the prefixes, so this is not a coverage artefact:
      //
      //   2026-08-14 …-0.ttrm r4 yachi lock 74  -> `unattributed`   (piece does not touch)
      //   2026-08-09 …-6.ttrm r7 pinglamb lock 24 -> `placement`    (piece touches)
      //
      // The 08-09 one is a Z (`spin: none`) at rows 21-23 that cleared row 23, opening a slot at
      // rows 24-26; A minus row 23 alone gives best=2 where the three controls give 0. It is
      // reported as `placement` — self_built — purely because a lock cell at B-row 23 is adjacent
      // to slot row 24 and so satisfies `touches`; the Z's cells are provably not in the slot. So
      // the same defect yields a confident WRONG verdict when the piece happens to sit beside the
      // slot, and an honest "don't know" only when it does not. Only the honest half reaches this
      // assertion, which is why the ROADMAP item is about the mechanism and this list is about the
      // one event that surfaces.
      //
      // No published rate moves under any repair: 08-14's event is rejected by clause 4 (the
      // closing clear at lock 70 was itself a T-spin) and 08-09's by clause 2 (floorOrigin
      // `arrived-later`), so `forecast_total` stays 0 either way. What a repair WOULD move is the
      // `self_built` count the report prints as 「玩家自己落嗰隻棋整出嚟」 — a gloss already false
      // for the 08-09 event — so it is a published-figure decision, not a test fix.
      const known = UNATTRIBUTED_STEP_MODEL_GAP[SESSION]?.[p.user] ?? 0;
      expect([SESSION, p.user, p.unattributed]).toEqual([SESSION, p.user, known]);
      expect(p.verified_placements).toBeLessThanOrEqual(p.total_placements);
      for (const k of ['forecast_rate_x1000','sampling_ci95_lo_x1000','sampling_ci95_hi_x1000'])
        expect(Number.isInteger(p[k])).toBe(true);
      // the point estimate must lie inside its own interval
      expect(p.sampling_ci95_lo_x1000).toBeLessThanOrEqual(p.forecast_rate_x1000);
      expect(p.sampling_ci95_hi_x1000).toBeGreaterThanOrEqual(p.forecast_rate_x1000);
      // A 0% lower bound was once a real bisection bug. With k = 0 forecasts it is the CORRECT
      // Clopper-Pearson answer (asserted exactly). With k > 0 the EXACT lower bound is positive, but
      // floored to x1000 it can STILL be 0 for a single forecast in a large sample — yachi 07-28 has 1
      // forecast in hundreds of T-spins (rate 0.3%), whose CP lower bound (~0.008%) floors to 0. So the
      // floored guard is only asserted for k = 0; for k > 0 the real invariant kept is that the interval
      // brackets the rate (asserted just above), which a bisection bug returning a spurious 0 would break.
      if (p.forecast_total === 0) expect(p.sampling_ci95_lo_x1000).toBe(0);
      expect(p.sampling_ci95_hi_x1000).toBeLessThan(1000);
    }
  });

  test('the rate is the floored quotient of the counts it is printed beside', () => {
    const d = JSON.parse(readFileSync(PATH, 'utf8'));
    for (const p of d.players) {
      // Every other gate here checks the rate's SHAPE — integral, inside its interval, ordered.
      // None of them reads the counts, so a rate that had drifted from them passed the lot.
      // Cross-multiplied so the check is exact integer arithmetic, and so it pins the floor
      // rather than merely a tolerance: r <= 1000*fc/n < r+1 has exactly one solution.
      const r = p.forecast_rate_x1000, n = p.verified_tspins, fc = p.forecast_total;
      expect(r * n).toBeLessThanOrEqual(1000 * fc);
      expect(1000 * fc).toBeLessThan((r + 1) * n);
    }
  });

  test('the simulator range brackets the rate it is printed beside', () => {
    const d = JSON.parse(readFileSync(PATH, 'utf8'));
    for (const p of d.players) {
      // `best` is one of the seven swept configs and is the config the rate itself comes from, so
      // the range must contain it. It briefly did not: the sweep kept measuring the garbage bucket
      // after the printed rate became garbage + line-clear, and the section rendered a non-zero
      // rate beside a zero-width range without any gate objecting.
      expect(p.simulator_range_lo_x1000).toBeLessThanOrEqual(p.forecast_rate_x1000);
      expect(p.simulator_range_hi_x1000).toBeGreaterThanOrEqual(p.forecast_rate_x1000);
    }
  });

  test('simulator uncertainty is smaller than sampling uncertainty', () => {
    const d = JSON.parse(readFileSync(PATH, 'utf8'));
    for (const p of d.players) {
      const sim = p.simulator_range_hi_x1000 - p.simulator_range_lo_x1000;
      const samp = p.sampling_ci95_hi_x1000 - p.sampling_ci95_lo_x1000;
      // If this ever flips, the simulator has become the binding constraint on this number
      // and more simulator work would be worth doing. Today it is not.
      expect(sim).toBeLessThan(samp);
    }
  });

  test('the sensitivity sweep is the set the prose describes', () => {
    const d = load();
    // 2026-08-12: the board source is the vendored Triangle engine (reference for the real game), which
    // has no sim OPTIONS to sweep, so the multi-config robustness range collapses to a single authoritative
    // config. Changing the sweep still must fail here and force the sentence to be rewritten.
    expect(d.simulator_configs_for_range).toEqual(['triangle-oracle']);
  });

  test('the two players\' intervals overlap — no difference is claimed', () => {
    const d = JSON.parse(readFileSync(PATH, 'utf8'));
    const [a, b] = d.players;
    const overlap = Math.min(a.sampling_ci95_hi_x1000, b.sampling_ci95_hi_x1000)
                  - Math.max(a.sampling_ci95_lo_x1000, b.sampling_ci95_lo_x1000);
    expect(overlap).toBeGreaterThan(0);
  });
  });
}
