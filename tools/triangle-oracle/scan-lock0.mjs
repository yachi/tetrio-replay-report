// How often does the FIRST lock (opening piece, no garbage possible) diverge sim vs oracle?
// A lock-0 divergence is the cleanest possible signal: identical inputs, no garbage, pure handling/spawn.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };

// how far is the piece's filled mass shifted between the two boards? report signed column-centroid delta
const centroid = (s) => { let sum = 0, n = 0; for (let i = 0; i < s.length; i++) if (s[i] !== ".") { sum += i % 10; n++; } return n ? sum / n : null; };

let total = 0, div = 0, lateLock = 0; const shifts = {}, lateBy = {};
for (const dir of dirs) {
  let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
  const parsed = {};
  for (const c of cases) {
    if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`, "utf8"));
    const rp = parsed[c.file].replay.rounds[c.round];
    const player = rp.find((p) => p.username === c.user);
    if (!player) continue;
    let sim, tri; try { sim = runCase(c); } catch { continue; } try { tri = replayRound(player, rp, { untilFrame: sim.locks[0]?.frame + 2 }); } catch { continue; }
    if (!sim.locks.length) continue;
    total++;
    const f = sim.locks[0].frame, t = tri.gridAt(f);
    if (t === undefined) continue;
    const s = encSim(sim.boards[0]);
    if (s !== t) {
      // SAME PLACEMENT, LATER LOCK is not a divergence, and conflating the two sent a reader
      // chasing a "movement/spawn edge case" that does not exist. The sample above is taken at
      // `sim.locks[0].frame + 2`, a tolerance with no derivation behind it; when the oracle locks
      // more than 2 frames after the sim its board is still EMPTY at that instant, which encodes as
      // a total mismatch and buckets as centroid "?" (nothing to take a centroid of). Measured
      // 2026-08-17: the corpus's single lock-0 mismatch is exactly this — 2026-07-22
      // `replay-2026-07-22-2.ttrm` r0 pinglamb, sim locks S at frame 1028, oracle lays the SAME two
      // rows at 1032. So re-ask at a wider window before calling it a divergence, and count the two
      // outcomes separately: a late lock is a lock-TIMING question (the `garbagespeed`/cap item),
      // a differing placement is a handling/spawn one.
      let late = false;
      for (const df of [4, 6, 10, 20, 45, 90]) {
        let t2; try { t2 = replayRound(player, rp, { untilFrame: f + df }).gridAt(f + df); } catch { break; }
        if (t2 === undefined) continue;
        if (t2 === s) { late = true; lateBy[df] = (lateBy[df] || 0) + 1; break; }
        if (t2 !== ".".repeat(200)) break;   // it locked something ELSE — a real divergence
      }
      if (late) { lateLock++; continue; }
      div++;
      const cs = centroid(s), ct = centroid(t);
      const d = cs != null && ct != null ? Math.round((cs - ct) * 2) / 2 : "?";
      shifts[d] = (shifts[d] || 0) + 1;
    }
  }
}
console.log(`lock-0 (opening piece) PLACEMENT divergences: ${div}/${total} cases (${(100*div/total).toFixed(1)}%)`);
console.log(`lock-0 same placement but LATER lock (not a divergence): ${lateLock}/${total}`);
for (const k of Object.keys(lateBy).sort((a, b) => Number(a) - Number(b))) console.log(`  within +${k} frames: ${lateBy[k]}`);
console.log("signed centroid shift (sim − oracle), col units — >0 = sim is further RIGHT:");
for (const k of Object.keys(shifts).sort((a, b) => Number(a) - Number(b))) console.log(`  ${String(k).padStart(5)}: ${shifts[k]}`);
