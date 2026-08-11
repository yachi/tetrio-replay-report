// Drive the project's own forecastMetric from Triangle's FULL-ROUND boards, so forecast detection is not
// truncated by the sim's spurious topouts. Triangle survives every round, so it can supply correct boards
// where the sim died. forecast.ts accepts a hand-built SimResult; we build one from Triangle's lock events.
//
// RIGOUR: validated against the sim's own forecastMetric on the OVERLAP (verified prefix, where both are
// valid). Only if the two agree there do we trust the oracle's full-round extension. A reconstruction bug
// would show up as a mismatch on the overlap, not as a silent false forecast.
//
// STATUS (2026-08-11): the validation gate REFUSES this reconstruction — over 156 surviving rounds it
// finds 0 tucked T-spins where the sim finds 330 (13% round-agreement). The captured locks/spins/boards
// look individually correct (e.g. a real T-spin-double slot), but forecastMetric drops them as UNTUCKED:
// its roof search walks BACKWARD through earlier boards, and the oracle's earlier garbage/hole timing
// differs enough from the sim's that the roof is not re-found. Faithfully reconstructing the full board
// HISTORY (not just per-lock snapshots) is the missing piece. So this tool's PHASE 2 "0 forecasts" is NOT
// trustworthy — it is 0 because it detects ~0 tucked T-spins, a reconstruction gap, not a real finding.
// The TRUSTWORTHY answer stays the sim's own full-round scan on surviving rounds: +70 T-spins, 0 forecasts
// (see the inline probe in the session log). Kept as a scaffold; the gate is the honest part.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
import { forecastMetric } from "../../pipeline/sim/forecast.ts";
const Game = Classes.Game;

const TL_DEFAULTS = { g:0.02, boardwidth:10, boardheight:20, kickset:"SRS+", bagtype:"7-bag", combotable:"multiplier", spinbonuses:"T-spins", garbageblocking:"combo blocking", garbagetargetbonus:"none", clutch:false, stock:0, garbagemultiplier:1, garbagespeed:20, garbageholesize:1, messiness_change:1, messiness_nosame:false, messiness_timeout:0, messiness_inner:0, messiness_center:false, garbageabsolutecap:0, garbagecapincrease:0, garbagecapmax:40, garbagecap:8, garbagecapmargin:0, usebombs:false, roundmode:"down", openerphase:0, garbagespecialbonus:false, allclears:true, allclear_garbage:10, allclear_b2b:0, b2bcharging:false, infinite_movement:false, lockresets:15, locktime:30, gravitymay20g:false, allow180:true, allow_harddrop:true, display_hold:true, can_undo:false, can_retry:false, infinite_hold:false, stride:false, passthrough:"zero" };
const H = 40;
const emptyBoard = () => Array.from({ length: H }, () => new Array(10).fill(null));
// Triangle board.state (y-up, row0=bottom, tile {mino}) -> sim Board (row0=top, 'G'|letter|null)
const toSimBoard = (st) => { const b = emptyBoard(); for (let y = 0; y < st.length && y < H; y++) { const sr = 39 - y; for (let c = 0; c < 10; c++) { const t = st[y]?.[c]; b[sr][c] = t == null ? null : (t.mino === "gb" ? "G" : String(t.mino).toUpperCase()); } } return b; };

// Build a SimResult from Triangle for one round/player. holes injected from recorded ige x (as in oracle.mjs).
export function oracleSim(player, roundPlayers) {
  const o = player.replay.options;
  const players = roundPlayers.map((p) => ({ gameid: p.replay.options.gameid, userid: p.id, username: p.username }));
  const byFrame = new Map();
  for (const e of player.replay.events) { if (!byFrame.has(e.frame)) byFrame.set(e.frame, []); byFrame.get(e.frame).push(e); }
  const loads = player.replay.events.filter((e) => e.type === "ige" && e.data?.data?.type === "garbage" && e.data.type === "interaction").map((e) => ({ amt: e.data.data.amt, x: e.data.data.x, iid: e.data.data.iid }));
  const iidToX = new Map(loads.map((l) => [l.iid, l.x]));
  const engine = Game.createEngine({ ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g }, o.gameid, players);
  const holeWidth = 10 - (o.garbageholesize ?? 1);
  const gbTile = () => ({ mino: "gb", connections: 0 });
  const holeFIFO = [];
  engine.events.on("garbage.tank", (ev) => { const x = iidToX.has(ev.iid) ? iidToX.get(ev.iid) : ev.column; for (let i = 0; i < ev.amount; i++) holeFIFO.push(x); });

  const boards = [], locks = [], garbageEvents = [];
  let pendingCells = null, prevG = 0, hi = 0, curFrame = 0, lockThisFrame = null;
  // capture the locking piece's cells (Triangle y-up -> sim row) just before nextPiece
  engine.events.on("falling.lock.pre", () => { try { pendingCells = engine.falling.absoluteBlocks.map(([x, y]) => ({ col: x, row: 39 - y })); } catch { pendingCells = []; } });
  // the lock's clear/spin come from the falling.lock event, NOT the tick return (which is flushRes).
  // Triangle's spin values are 'none' | 'normal' (full T-spin) | 'mini'.
  engine.events.on("falling.lock", (res) => { const spin = res.spin === "mini" ? "mini" : (res.spin && res.spin !== "none") ? "full" : "none"; lockThisFrame = { piece: String(res.mino).toUpperCase(), cleared: res.lines | 0, spin, cells: pendingCells || [] }; });
  engine.events.on("garbage.tank", (ev) => { garbageEvents.push({ frame: curFrame, amt: ev.amount, lockIndex: locks.length }); });
  const gRowIdx = () => { const st = engine.board.state, idx = []; for (let r = 0; r < st.length; r++) if (st[r].filter((t) => t && t.mino === "gb").length >= holeWidth) idx.push(r); return idx; };
  const injectHoles = () => { const idx = gRowIdx(); if (idx.length > prevG) { const K = idx.length - prevG, st = engine.board.state, bottomK = idx.slice(0, K); for (let k = 0; k < K; k++) { const r = bottomK[k], wantX = holeFIFO[hi + k]; const cur = st[r].findIndex((t) => t == null || t.mino !== "gb"); if (wantX != null && cur !== wantX) { st[r][cur] = gbTile(); st[r][wantX] = null; } } hi += K; } prevG = idx.length; };

  const total = player.replay.frames ?? 4000;
  for (let f = 0; f <= total; f++) {
    curFrame = f;
    const res = engine.tick(byFrame.get(f) || []);
    injectHoles();
    if (lockThisFrame) { locks.push({ frame: f, ...lockThisFrame, allclear: false }); boards.push(toSimBoard(engine.board.state)); lockThisFrame = null; pendingCells = null; }
    if (res && res.topout) break;
  }
  // provSnaps: best-effort — piece cells marked by lock index, garbage/empty null. (validated on overlap.)
  const provSnaps = boards.map(() => emptyBoard());
  return { boards, locks, garbageEvents, provSnaps, records: [], topout: false };
}

// ── driver ───────────────────────────────────────────────────────────────────────────────────────────
if (import.meta.main) {
  const ROOT = fileURLToPath(new URL("../../", import.meta.url)); const SESS = `${ROOT}sessions`;
  const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
  const isFc = (kind) => kind === "forecast_lineclear" || kind === "forecast_garbage";
  // Phase 1: VALIDATE on overlap (surviving-sim rounds, verified prefix): oracle vs sim T-spin records agree?
  let vRounds = 0, tsAgree = 0, tsSimTot = 0, tsOraTot = 0;
  // Phase 2: full-round forecast scan on winner-topout rounds via oracle
  let wRounds = 0, wForecasts = 0; const fcHits = [];
  for (const dir of dirs) {
    let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
    const parsed = {};
    for (const c of cases) {
      if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`, "utf8"));
      const rp = parsed[c.file].replay.rounds[c.round]; const p = rp.find((x) => x.username === c.user); if (!p) continue;
      let sim; try { sim = runCase(c); } catch { continue; }
      let ora; try { ora = oracleSim(p, rp); } catch { continue; }
      const v = verifiedIndex(sim, c.truth);
      if (!sim.topout) {
        // overlap validation: count tucked T-spin RECORDS in [0..v] for both, over matching lock frames
        const simRec = forecastMetric(sim, true).records.filter((r) => r.lockIndex <= v).length;
        const oraRec = forecastMetric(ora, true).records.filter((r) => ora.locks[r.lockIndex] && ora.locks[r.lockIndex].frame <= sim.locks[Math.min(v, sim.locks.length - 1)].frame).length;
        vRounds++; tsSimTot += simRec; tsOraTot += oraRec; if (simRec === oraRec) tsAgree++;
      } else if (p.alive === true) {
        wRounds++;
        const m = forecastMetric(ora, true);
        for (const r of m.records) if (isFc(r.kind)) { wForecasts++; fcHits.push(`${dir.slice(5)} ${c.user} ${c.file.replace('replay-','').replace('.ttrm','')} r${c.round} lock${r.lockIndex} ${r.kind}`); }
      }
    }
  }
  console.log(`PHASE 1 — reconstruction validation on surviving rounds (oracle vs sim tucked-T-spin count over overlap):`);
  console.log(`  rounds ${vRounds}   exact-agree ${tsAgree}/${vRounds} (${(100*tsAgree/vRounds).toFixed(0)}%)   totals sim=${tsSimTot} oracle=${tsOraTot}`);
  console.log(`\nPHASE 2 — FULL-ROUND forecast scan on winner-topout rounds (the previously-blind 80%):`);
  console.log(`  rounds ${wRounds}   FORECASTS found: ${wForecasts}`);
  console.log(fcHits.length ? fcHits.slice(0, 20).join("\n") : "  none — 0 forecasts over the full round, even the hidden region");
}
