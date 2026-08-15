// Quantify the STRENGTH of the dual-backed agreement between the project sim (pipeline/sim/sim.ts)
// and the Triangle oracle (./oracle.mjs), by splitting it on whether the agreeing cells could have
// agreed for free.
//
// THE SHARED INPUT IS CONCRETE: the replay's own recorded garbage hole column `x`, carried by the
// ige `interaction` events. Both engines write that same recorded column verbatim —
//   - sim.ts:276-283   insertGarbage() fills the row with GARBAGE, then punches row[(x+s) % 10] = null
//   - oracle.mjs:63-75 injectHoles() overwrites Triangle's own re-rolled column with the recorded
//                      `x`, paired back to its batch by `iid`
// and `size` is 1 in every ige garbage event of this corpus, so an as-inserted garbage row is nine
// 'G' cells plus a hole at column `x`: a pure function of the shared input on BOTH sides, with no
// derivation logic on either. Agreement on those cells is FORCED — it would hold between two engines
// that agreed about nothing else. So each dual-backed finding is split by the board it reads:
//
//   INDEPENDENT  — garbage-free board at the finding's lock. NO cell of the compared string came from
//                  the shared input, so the agreement is entirely between two clean-room derivations
//                  (movement/gravity/lock/clear). The label is sound because `hasG` scans exactly the
//                  rows 20..39 that `encSim` encodes: "no 'G'" really does mean "no forced cell in
//                  the string that was compared". Keep those two ranges equal or the label lies.
//   COUPLED      — garbage present. WEAKER evidence, not absent evidence, and the distinction is the
//                  whole point: a coupled board is only PARTLY forced. The stack above the garbage is
//                  derived by both engines, and whole-board agreement still requires all of it to
//                  match. How much is actually forced is MEASURED and printed below rather than
//                  asserted here — a share quoted in a comment is a share nothing checks, and this
//                  file previously cited a proof that did not exist.
//
//                  The printed non-'G' share is an UPPER BOUND on independence, not a measure of it.
//                  It counts a cell as independent when its TYPE is not garbage, but a stack cell's
//                  ROW INDEX is a function of how many garbage rows were inserted — i.e. of the same
//                  shared input — so some of what it counts is coupled through position even though
//                  it is not coupled through type. The 'G' side is conservative in the argument's
//                  favour; this side is not. The load-bearing figure is the share of boards that are
//                  WHOLLY forced, which is bounded below by nothing and measures out near zero.
//
// NOT TRANSFERABLE TO THE SHIPPED ORACLE: `runCaseOracle` (pipeline/sim/oracle-source.ts:48) keeps
// Triangle's own seeded-RNG hole columns instead of injecting the recorded ones, so its garbage cells
// are NOT a shared input and this INDEPENDENT/COUPLED split says nothing about it.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
import { forecastMetric } from "../../pipeline/sim/forecast.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };
const hasG = (b) => { for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) if (b[r][c] === "G") return true; return false; };
const OPENER_WINDOW = 21;
// Wilson 95% lower bound on a proportion — the conservative read of a rate.
const wilsonLo = (k, n) => { if (!n) return 0; const z = 1.96, p = k / n, d = 1 + z * z / n; return ((p + z * z / (2 * n) - z * Math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / d); };

// forecast events: total / dual / dual&independent / dual&coupled
const fc = { total: 0, dual: 0, indep: 0, coupled: 0 };
// opener rounds: dual / dual&independent(window garbage-free) / dual&coupled
const op = { rounds: 0, dual: 0, indep: 0, coupled: 0 };
// prefix locks baseline
const px = { total: 0, dual: 0, gfree: 0, dualGfree: 0 };
// composition of the COUPLED boards: how much of one is the forced garbage, how much is still
// derived. Computed, not quoted, so "coupled" can never be read as "uninformative".
const cp = { boards: 0, cells: 0, g: 0, occ: 0, occG: 0, allForced: 0 };
const cpAccum = (b) => {
  cp.boards++; let occ = 0, occG = 0;
  for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) {
    const cell = b[r][c]; cp.cells++;
    if (cell === "G") cp.g++;
    if (cell != null) { occ++; if (cell === "G") occG++; }
  }
  cp.occ += occ; cp.occG += occG;
  if (occ > 0 && occG === occ) cp.allForced++;   // the only boards agreement is wholly forced on
};

for (const dir of dirs) {
  let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
  const parsed = {};
  for (const c of cases) {
    if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`, "utf8"));
    const rp = parsed[c.file].replay.rounds[c.round];
    const player = rp.find((p) => p.username === c.user);
    if (!player) continue;
    let sim, tri; try { sim = runCase(c); } catch { continue; } if (!sim.locks.length) continue;
    try { tri = replayRound(player, rp, { untilFrame: c.frames + 2 }); } catch { continue; }
    const v = verifiedIndex(sim, c.truth); if (v < 0) continue;

    let firstBad = Infinity;
    for (let i = 0; i < sim.locks.length; i++) { const t = tri.gridAt(sim.locks[i].frame); if (t === undefined) continue; if (encSim(sim.boards[i]) !== t) { firstBad = i; break; } }
    const dualTop = Math.min(v, firstBad - 1);

    for (let i = 0; i <= v && i < sim.boards.length; i++) { px.total++; const g = hasG(sim.boards[i]); if (!g) px.gfree++; if (i <= dualTop) { px.dual++; if (!g) px.dualGfree++; else cpAccum(sim.boards[i]); } }

    for (const rec of forecastMetric(sim, true).records) {
      if (rec.lockIndex > v) continue;
      fc.total++;
      if (rec.lockIndex <= dualTop) {
        fc.dual++;
        const b = sim.boards[rec.lockIndex]; // board the event reads
        if (b && hasG(b)) fc.coupled++; else fc.indep++;
      }
    }

    const win = Math.min(OPENER_WINDOW - 1, v);
    op.rounds++;
    if (dualTop >= win) {
      op.dual++;
      let anyG = false; for (let i = 0; i <= win; i++) if (sim.boards[i] && hasG(sim.boards[i])) { anyG = true; break; }
      if (anyG) op.coupled++; else op.indep++;
    }
  }
}

const pct = (a, b) => b ? (100 * a / b).toFixed(1) : "—";
const line = (label, k, n) => `  ${label.padEnd(34)} ${String(k).padStart(5)}/${String(n).padStart(5)}  ${pct(k, n).padStart(5)}%   (Wilson 95% lower ${(100 * wilsonLo(k, n)).toFixed(1)}%)`;
console.log("VALUE OF THE DUAL-BACKING, decomposed by independence (INDEPENDENT = no cell of the compared board came from the replay's recorded hole column)\n");
console.log("verified-prefix locks");
console.log(line("bit-exact (dual)", px.dual, px.total));
console.log(line("  of which garbage-free (INDEP)", px.dualGfree, px.dual));
console.log(line("garbage-free overall (baseline)", px.gfree, px.total));
console.log("\nFORECAST events");
console.log(line("dual-backed", fc.dual, fc.total));
console.log(line("  INDEPENDENT (garbage-free board)", fc.indep, fc.total));
console.log(line("  COUPLED (garbage on board)", fc.coupled, fc.total));
console.log(`  independent share of dual-backed: ${pct(fc.indep, fc.dual)}%`);
console.log("\nOPENER rounds (opening window)");
console.log(line("dual-backed", op.dual, op.rounds));
console.log(line("  INDEPENDENT (garbage-free window)", op.indep, op.rounds));
console.log(line("  COUPLED (garbage in window)", op.coupled, op.rounds));
console.log(`  independent share of dual-backed: ${pct(op.indep, op.dual)}%`);

// Why COUPLED is weaker evidence and not absent evidence: if agreement on a coupled board were
// "uninformative", essentially every occupied cell would have to be a forced 'G'. It is not.
console.log(`\nCOUPLED board composition (${cp.boards} dual-backed boards carrying garbage)`);
console.log(line("forced 'G' of all cells", cp.g, cp.cells));
console.log(line("forced 'G' of OCCUPIED cells", cp.occG, cp.occ));
console.log(line("boards wholly forced (occupied all G)", cp.allForced, cp.boards));
console.log(`  so AT MOST ${pct(cp.occ - cp.occG, cp.occ)}% of a coupled board's occupied cells are independently derived`);
console.log(`  (upper bound: a stack cell's row index still depends on how many garbage rows went in).`);
