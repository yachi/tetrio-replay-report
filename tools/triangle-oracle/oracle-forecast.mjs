// Drive the project's own forecastMetric from the Triangle oracle's FULL-ROUND boards, so forecast
// detection is not truncated by the hand-port's spurious topouts. `forecast.ts` accepts any
// SimResult; the boards come from `pipeline/sim/oracle-source.ts` (`runCaseOracle`), which is the
// same source the published forecast section uses.
//
// ── 2026-08-16: THIS FILE'S OWN BOARD RECONSTRUCTION IS DELETED. READ THIS BEFORE RESURRECTING IT ──
//
// Until today this file built its own SimResult from `@haelp/teto`: its own provenance (mirroring
// the engine's shift/splice with a force-align fallback) and its own garbage-hole relocation
// (`injectHoles`, moving the hole in the LIVE engine board to the ige-recorded column). Both are
// wrong, and both were already known to be wrong somewhere else in the repo:
//
//  * PROVENANCE. `pipeline/sim/oracle-source.ts` replaced the mirroring approach on 2026-08-12
//    (`a53a952`, "95% -> 100%") with exact cell identity — a WeakMap tag on the engine's own stable
//    cell objects, which survive its splices — and this file was never moved onto it. Measured over
//    the six-session corpus by `pipeline/sim/check_provenance.ts`, the deleted code named an
//    IMPOSSIBLE placer (a lock whose piece is not the letter the board draws in that cell) for
//    **544 of 2024 (26.9%)** roof cells and **1 191 905 of 3 811 813 (31.3%)** placed cells, against
//    **0** for both published board sources.
//  * HOLE RELOCATION. `oracle-source.ts:48-58` records engine-side relocation as VERIFIED DEAD —
//    moving a hole in the live board changes which lines the engine later completes, and coverage
//    goes 88.6% -> 23%. The effect here was blunt: over the same corpus the deleted code produced
//    **90 078** locks where the replays record **70 493** pieces placed. It was not surviving rounds
//    the hand-port died in; it was running 28% past the end of rounds that had finished.
//    `runCaseOracle` gives **70 500** — seven locks off the game's own count over 760 rounds.
//
// What that cost: this file's PHASE 2 reported four full-round `forecast_lineclear` candidates, and
// three of the four (A, C and the 2026-08-14 one) rest on a roof cell attributed to a lock of the
// wrong piece. Under the published board source all three are `reactive`. See
// `ForecastCandidate.dfy`, whose headline lemma was withdrawn on the same evidence.
//
// Nothing published was affected: `forecast-facts.json` has always been computed over
// `runCaseOracle` and the verified prefix, never over this file.
//
// The figures in the historical comment block this replaced (142/144, 330 vs 328, 1 in 654, 99%,
// "PHASE 2 finds 4") were all produced by the deleted reconstruction and are not carried forward.
// Run the driver for live ones. What it says now is the cleanest evidence the deletion was right:
// PHASE 1 went 204/205 rounds and 549-vs-548 T-spin records to **205/205 and 549 = 549**. The old
// code's "99%" was read as reconstruction noise for four days; it was the reconstruction being
// wrong, and the two implementations that share no code agree exactly once it is gone.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, runCaseOracle, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
import { forecastMetric } from "../../pipeline/sim/forecast.ts";

// ── driver ───────────────────────────────────────────────────────────────────────────────────────
if (import.meta.main) {
  const ROOT = fileURLToPath(new URL("../../", import.meta.url)); const SESS = `${ROOT}sessions`;
  const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
  const isFc = (kind) => kind === "forecast_lineclear" || kind === "forecast_garbage";
  // Phase 1: VALIDATE on overlap (surviving-sim rounds, verified prefix): oracle vs sim T-spin records agree?
  let vRounds = 0, tsAgree = 0, tsSimTot = 0, tsOraTot = 0, vSimFc = 0, vOraFc = 0;
  const simSurvivorRounds = [];
  // Phase 2: full-round forecast scan on winner-topout rounds via oracle
  let wRounds = 0, wForecasts = 0; const fcHits = [];
  for (const dir of dirs) {
    let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
    for (const c of cases) {
      let sim; try { sim = runCase(c); } catch { continue; }
      let ora; try { ora = runCaseOracle(c); } catch { continue; }
      const v = verifiedIndex(sim, c.truth);
      const simFc = forecastMetric(sim, true).records.filter((r) => r.lockIndex <= v && isFc(r.kind)).length;
      if (simFc > 0) simSurvivorRounds.push(`${dir.slice(5)} ${c.user} r${c.round} topout=${sim.topout}`);
      // VALIDATION (surviving rounds only, where the sim covers the full round too): T-spin counts agree?
      if (!sim.topout && v >= 0 && sim.locks.length) {
        const cutFrame = sim.locks[Math.min(v, sim.locks.length - 1)].frame;
        const simRec = forecastMetric(sim, true).records.filter((r) => r.lockIndex <= v).length;
        const oraRecs = forecastMetric(ora, true).records.filter((r) => ora.locks[r.lockIndex] && ora.locks[r.lockIndex].frame <= cutFrame);
        vRounds++; tsSimTot += simRec; tsOraTot += oraRecs.length; if (simRec === oraRecs.length) tsAgree++;
        vSimFc += simFc; vOraFc += oraRecs.filter((r) => isFc(r.kind)).length;
      }
      // FULL-ROUND forecast scan via the oracle — EVERY round, so nothing is skipped by phase.
      // "Full round" means the round as the GAME played it: `runCaseOracle` ends where the replay
      // does (70 500 locks against the replays' own 70 493 over six sessions). The reconstruction
      // this replaced ran to 90 078 and called the overrun `100% of the material`.
      wRounds++;
      const m = forecastMetric(ora, true);
      for (const r of m.records) if (isFc(r.kind)) { wForecasts++; fcHits.push(`${dir.slice(5)} ${c.user} ${c.file.replace('replay-','').replace('.ttrm','')} r${c.round} lock${r.lockIndex} ${r.kind} floor=${r.floorOrigin} (sim ${sim.topout ? "topped out @"+(v+1)+" locks" : "survived"})`); }
    }
  }
  console.log(`PHASE 1 — reconstruction validation on surviving rounds (oracle vs sim over overlap):`);
  console.log(`  rounds ${vRounds}   T-spin exact-agree ${tsAgree}/${vRounds} (${(100*tsAgree/vRounds).toFixed(0)}%)   totals sim=${tsSimTot} oracle=${tsOraTot}`);
  console.log(`  FORECAST agreement on overlap: sim=${vSimFc} oracle=${vOraFc}`);
  console.log(`  rounds where the SIM finds a forecast (anywhere in its prefix): ${simSurvivorRounds.length ? simSurvivorRounds.join(" | ") : "none"}`);
  console.log(`\nPHASE 2 — FULL-ROUND forecast scan via the oracle, EVERY round:`);
  console.log(`  rounds ${wRounds}   forecast-KIND records: ${wForecasts}   (the sim's truncated detection finds ${simSurvivorRounds.length})`);
  console.log(`  NOTE: a forecast KIND is not a verified forecast — clause 2 (floorOrigin) and clause 4`);
  console.log(`  still apply, and \`isVerifiedForecast\` is what the published numerator uses.`);
  console.log(fcHits.length ? fcHits.map((h) => "  " + h).join("\n") : "  none");
}
