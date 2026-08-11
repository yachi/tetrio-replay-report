// Profile the pure-PLACEMENT first-divergences (garbage identical at the first bad lock) to see if
// they share a systematic cause — the way `hoisted` explained 146/148 openers. For each, record the
// first-bad lock index, the signed column-centroid shift, and tell-tale inputs in the ~2s before it:
// a held soft-drop, both L+R held at once (the sim deliberately doesn't model L/R release), or a 180.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };
const countG = (s) => (s.match(/G/g) || []).length;
const centroid = (s) => { let sum = 0, n = 0; for (let i = 0; i < s.length; i++) if (s[i] === "#") { sum += i % 10; n++; } return n ? sum / n : 0; };

const lockBucket = {}, shiftHist = {}, tell = { softdrop: 0, bothLR: 0, r180: 0, none: 0 };
let count = 0;
const examples = [];
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
    let bad = -1, s = "", t = "";
    for (let i = 0; i < sim.locks.length; i++) { const f = sim.locks[i].frame, tt = tri.gridAt(f); if (tt === undefined) continue; const ss = encSim(sim.boards[i]); if (ss !== tt) { bad = i; s = ss; t = tt; break; } }
    if (bad < 0) continue;
    const gDiff = countG(s) !== countG(t);
    let pDiff = false; for (let k = 0; k < s.length; k++) if ((s[k] === "#") !== (t[k] === "#")) { pDiff = true; break; }
    if (!(pDiff && !gDiff)) continue; // pure-placement only
    count++;
    const lb = bad === 0 ? "0" : bad <= 3 ? "1-3" : bad <= 8 ? "4-8" : bad <= 20 ? "9-20" : ">20";
    lockBucket[lb] = (lockBucket[lb] || 0) + 1;
    const sh = Math.round((centroid(s) - centroid(t)) * 2) / 2;
    shiftHist[sh] = (shiftHist[sh] || 0) + 1;
    // inputs in the window from the previous lock to this one
    const f0 = bad > 0 ? sim.locks[bad - 1].frame : 0, f1 = sim.locks[bad].frame;
    const evs = player.replay.events.filter((e) => (e.type === "keydown" || e.type === "keyup") && e.frame >= f0 && e.frame <= f1);
    const keys = evs.filter((e) => e.type === "keydown").map((e) => e.data.key);
    const held = new Set(); let bothLR = false;
    for (const e of evs) { if (e.type === "keydown") { held.add(e.data.key); if (held.has("moveLeft") && held.has("moveRight")) bothLR = true; } else held.delete(e.data.key); }
    if (keys.includes("rotate180")) tell.r180++;
    else if (bothLR) tell.bothLR++;
    else if (keys.includes("softDrop")) tell.softdrop++;
    else tell.none++;
    if (examples.length < 12) examples.push(`${dir.slice(5)} ${c.user} ${c.file.replace('replay-','').replace('.ttrm','')} r${c.round} lock${bad} shift=${sh} keys=[${[...new Set(keys)].join(',')}]`);
  }
}
console.log(`pure-placement first-divergences: ${count}`);
console.log(`\nfirst-bad LOCK index:`); for (const k of ["0","1-3","4-8","9-20",">20"]) console.log(`  ${k.padStart(5)}: ${lockBucket[k] || 0}`);
console.log(`\nsigned centroid SHIFT (sim - oracle; >0 = sim further right):`);
for (const k of Object.keys(shiftHist).sort((a,b)=>Number(a)-Number(b))) console.log(`  ${String(k).padStart(5)}: ${shiftHist[k]}`);
console.log(`\nTELL-TALE input in the window before the divergent lock:`);
console.log(`  rotate180 present : ${tell.r180}  (sim has a no-180 blind spot)`);
console.log(`  both L+R held     : ${tell.bothLR}  (sim doesn't model L/R release resume)`);
console.log(`  softDrop present  : ${tell.softdrop}`);
console.log(`  none of the above : ${tell.none}`);
console.log(`\nexamples:`); for (const e of examples) console.log("  " + e);
