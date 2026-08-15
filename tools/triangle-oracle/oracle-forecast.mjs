// Drive the project's own forecastMetric from Triangle's FULL-ROUND boards, so forecast detection is not
// truncated by the sim's spurious topouts. Triangle survives every round, so it can supply correct boards
// where the sim died. forecast.ts accepts a hand-built SimResult; we build one from Triangle's lock events.
//
// RIGOUR: validated against the sim's own forecastMetric on the OVERLAP (verified prefix, where both are
// valid). Only if the two agree there do we trust the oracle's full-round extension. A reconstruction bug
// would show up as a mismatch on the overlap, not as a silent false forecast.
//
// STATUS (2026-08-11): VALIDATED and it found something. The roof search reads `provSnaps` (provenance),
// not the board (forecast.ts:608) — passing empty provSnaps dropped every T-spin as untucked. Rebuilt
// provenance (garbage=-1, filled=placer lock, empty=null) and the gate now PASSES: 142/144 surviving
// rounds agree on tucked-T-spin count, totals sim 330 vs oracle 328 (99%), and the oracle reproduces the
// sim's one known forecast (07-28-6 r5) as forecast_lineclear. On that certified reconstruction, the
// FULL-ROUND scan over EVERY round finds 2 forecasts where the sim's drift-truncated detection finds 1:
// the extra one (07-28-3 r5 yachi lock25) sits in a region the sim NEVER saw (it topped out at lock 12).
// UPDATE — bulletproofing DISPROVED the confidence, honestly. Exact provenance (mirroring sim.ts's
// shift/push + splice/unshift, then force-aligning the pattern to the true board) makes the reconstruction
// reproduce the sim's KNOWN survivor BIT-EXACT (07-28-6 r5: lock 32, roofFrom 19, sep 13 — identical), and
// keeps T-spin detection at 99% (330 vs 328). BUT the *additional* forecast candidates in the truncated
// region are NOT STABLE: the full-round count is 2, 2-but-different, or 3 depending on the reconstruction
// variant. `forecast_lineclear` is the strictest gate in the metric (1 in 654), so hidden-region
// candidates sit on the decision boundary and flip with sub-1% provenance differences. CONCLUSION: the
// only SOLID forecast is the survivor, which the sim already detects (it is at the very edge of the
// prefix). Whether the drift truncation hides ADDITIONAL forecasts is UNRESOLVED — the candidates are
// borderline and reconstruction-sensitive, and confirming them needs a 100%-bit-exact full board history,
// which this reconstruction approaches (99%) but does not reach for these ultra-sensitive cases. The
// earlier "truncation hid a forecast" claim was premature; this is the corrected, honest terminus.
//
// SUPERSEDED the same night: ForecastCandidate.dfy resolves clause 2 for these candidates by DIRECT
// FRAME ORDERING against recorded ground-truth confirm frames (bypassing the unstable provenance
// reconstruction above entirely), so the "UNRESOLVED" in the CONCLUSION above no longer holds — read
// ForecastCandidate.dfy for the current, proven verdicts. The figures in this comment block (142/144,
// 330 vs 328, 1 in 654, 99%) are a dated snapshot of the 2026-08-11 investigation over the then-five-
// session corpus and are NOT re-derived here — re-run `bun oracle-forecast.mjs` for today's live
// numbers. Doing so on 2026-08-15 (six sessions) gives PHASE 1 rounds=205, T-spin exact-agree 204/205
// (100%), totals sim=549 oracle=548, and PHASE 2 finds 4 full-round forecast_lineclear candidates (not
// 2-3): the three named in ForecastCandidate.dfy, plus a NEW one this file's driver has not yet been
// run against ForecastCandidate.dfy's ground-truth-frame-ordering method: 2026-08-14 yachi
// 2026-08-14-10 r2 lock19 forecast_lineclear (sim topped out @22 locks). It is UNPROVEN here — no
// clause-2 lemma exists for it yet.
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
  // provenance, evolved EXACTLY like the sim (sim.ts insertGarbage/lockPiece): garbage inserts do
  // prov.shift()+push(garbageRow -1/null); a lock marks piece cells with the lock index then clears
  // full rows with splice()+unshift(nullRow). Garbage and clears are mutually exclusive per lock
  // (garbage only tanks on non-clearing locks), which fixes the operation order.
  const provSnaps = [];
  let prov = emptyBoard();
  const gRowProv = (holeX) => { const r = new Array(10).fill(-1); r[((holeX % 10) + 10) % 10] = null; return r; };
  let pendingCells = null, prevG = 0, hi = 0, curFrame = 0, lockThisFrame = null, hj = 0, prevSnapG = 0; // hj = hole index consumed into prov
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
    if (lockThisFrame) {
      const k = locks.length;
      // (1) mark this piece's cells with the lock index
      for (const c of lockThisFrame.cells) if (c.row >= 0 && c.row < H && c.col >= 0 && c.col < 10) prov[c.row][c.col] = k;
      // (2) clears XOR garbage. clears: remove any row that is now entirely non-null (== a full board row).
      if (lockThisFrame.cleared > 0) {
        for (let r = H - 1; r >= 0; r--) if (prov[r].every((v) => v !== null)) { prov.splice(r, 1); prov.unshift(new Array(10).fill(null)); }
      } else {
        // garbage inserted this lock? the board's garbage-row count rose since the previous snapshot.
        const nowG = engine.board.state.filter((row) => row.filter((t) => t && t.mino === "gb").length >= holeWidth).length;
        const gAdd = Math.max(0, nowG - prevSnapG);
        for (let i = 0; i < gAdd; i++) { prov.shift(); prov.push(gRowProv(holeFIFO[hj++] ?? 0)); }
      }
      const bd = toSimBoard(engine.board.state);
      // Force-align the PATTERN to the true board (evolved placers can drift a cell across a shift):
      // empty->null, garbage->-1, and a filled cell the evolution left null/garbage gets this lock as a
      // fallback placer. Keeps detection (untucked/roofIsGarbage) exact while preserving evolved placers.
      for (let r = 0; r < H; r++) for (let c = 0; c < 10; c++) {
        if (bd[r][c] == null) prov[r][c] = null;
        else if (bd[r][c] === "G") prov[r][c] = -1;
        else if (prov[r][c] == null || prov[r][c] < 0) prov[r][c] = k;
      }
      locks.push({ frame: f, ...lockThisFrame, allclear: false });
      boards.push(bd);
      provSnaps.push(prov.map((r) => [...r]));
      prevSnapG = engine.board.state.filter((row) => row.filter((t) => t && t.mino === "gb").length >= holeWidth).length;
      lockThisFrame = null; pendingCells = null;
    }
    if (res && res.topout) break;
  }
  return { boards, locks, garbageEvents, provSnaps, records: [], topout: false };
}

// ── driver ───────────────────────────────────────────────────────────────────────────────────────────
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
    const parsed = {};
    for (const c of cases) {
      if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`, "utf8"));
      const rp = parsed[c.file].replay.rounds[c.round]; const p = rp.find((x) => x.username === c.user); if (!p) continue;
      let sim; try { sim = runCase(c); } catch { continue; }
      let ora; try { ora = oracleSim(p, rp); } catch { continue; }
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
      // FULL-ROUND forecast scan via the oracle — EVERY round (the oracle survives all), so nothing
      // is skipped by phase. This is the real answer: forecasts over 100% of the material.
      wRounds++;
      const m = forecastMetric(ora, true);
      for (const r of m.records) if (isFc(r.kind)) { wForecasts++; fcHits.push(`${dir.slice(5)} ${c.user} ${c.file.replace('replay-','').replace('.ttrm','')} r${c.round} lock${r.lockIndex} ${r.kind} (sim ${sim.topout ? "topped out @"+(v+1)+" locks" : "survived"})`); }
    }
  }
  console.log(`PHASE 1 — reconstruction validation on surviving rounds (oracle vs sim over overlap):`);
  console.log(`  rounds ${vRounds}   T-spin exact-agree ${tsAgree}/${vRounds} (${(100*tsAgree/vRounds).toFixed(0)}%)   totals sim=${tsSimTot} oracle=${tsOraTot}`);
  console.log(`  FORECAST agreement on overlap: sim=${vSimFc} oracle=${vOraFc}`);
  console.log(`  rounds where the SIM finds a forecast (anywhere in its prefix): ${simSurvivorRounds.length ? simSurvivorRounds.join(" | ") : "none"}`);
  console.log(`\nPHASE 2 — FULL-ROUND forecast scan via the oracle, EVERY round (100% of the material):`);
  console.log(`  rounds ${wRounds}   FORECASTS found: ${wForecasts}   (the sim's truncated detection finds ${simSurvivorRounds.length})`);
  console.log(fcHits.length ? fcHits.map((h) => "  " + h).join("\n") : "  none");
}
