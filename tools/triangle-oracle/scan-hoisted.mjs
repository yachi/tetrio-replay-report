// Correlate lock-0 divergence with a HOISTED opening move-key.
// Hypothesis: the sim drops event.data.hoisted, so it treats a DAS-charged (held-across-spawn)
// direction as a fresh tap and under-shifts. If so, lock-0 divergences should be exactly the
// cases whose first pre-lock move-key is hoisted.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };

// hoisted move-key present before the first lock?
const firstLockHoisted = (player, lockFrame) => {
  for (const e of player.replay.events) {
    if (e.frame > lockFrame) break;
    if (e.type === "keydown" && (e.data?.key === "moveLeft" || e.data?.key === "moveRight") && e.data?.hoisted) return true;
  }
  return false;
};

let n = 0;
const tbl = { "div&hoist": 0, "div&plain": 0, "ok&hoist": 0, "ok&plain": 0 };
for (const dir of dirs) {
  let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
  const parsed = {};
  for (const c of cases) {
    if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`, "utf8"));
    const rp = parsed[c.file].replay.rounds[c.round];
    const player = rp.find((p) => p.username === c.user);
    if (!player) continue;
    let sim, tri; try { sim = runCase(c); } catch { continue; } if (!sim.locks.length) continue;
    const lf = sim.locks[0].frame;
    try { tri = replayRound(player, rp, { untilFrame: lf + 2 }); } catch { continue; }
    const t = tri.gridAt(lf); if (t === undefined) continue;
    n++;
    const div = encSim(sim.boards[0]) !== t;
    const hoist = firstLockHoisted(player, lf);
    tbl[`${div ? "div" : "ok"}&${hoist ? "hoist" : "plain"}`]++;
  }
}
console.log(`opening pieces analysed: ${n}`);
console.log("                    hoisted   plain");
console.log(`  DIVERGE (sim≠oracle)  ${String(tbl["div&hoist"]).padStart(4)}    ${String(tbl["div&plain"]).padStart(4)}`);
console.log(`  AGREE   (sim=oracle)  ${String(tbl["ok&hoist"]).padStart(4)}    ${String(tbl["ok&plain"]).padStart(4)}`);
console.log(`\nIf the hypothesis holds: DIVERGE≈hoisted, AGREE≈plain (few plain divergences, few hoisted agreements).`);
