// Triangle.js-based headless TETR.IO board oracle.
// Replays one round/player of a .ttrm through @haelp/teto's Engine, with the two calibrated fixes:
//   (1) sane gravity (the version-19 .ttrm omits `g`), (2) inject the replay's recorded garbage hole
//       column `x` (the engine re-rolls holes from its own seeded RNG and ignores the ige-recorded x).
// Validated bit-exact vs the project sim through the deterministic + main garbage phase (28/28 locks to
// frame 1371 on 2026-07-22 r0 yachi), and closer to the LIVE engine than the sim in the topout flood
// (77.5% vs 59.5% at frame 1422). Returns per-frame board grids (top-down, 10x20, chars '.'/G/#).
import { Classes } from "@haelp/teto";
const Game = Classes.Game;

// TETR.IO/TL ruleset fields the version-19 replay `options` does not carry. Holes and gravity are the
// only board-affecting ones that are pinned elsewhere (holes injected below, gravity forced sane);
// garbagespeed/cap remain best-effort, so garbage TIMING attribution is soft (see README).
const TL_DEFAULTS = {
  g: 0.02, boardwidth: 10, boardheight: 20, kickset: "SRS+", bagtype: "7-bag", combotable: "multiplier",
  spinbonuses: "T-spins", garbageblocking: "combo blocking", garbagetargetbonus: "none", clutch: false,
  stock: 0, garbagemultiplier: 1, garbagespeed: 20, garbageholesize: 1, messiness_change: 1,
  messiness_nosame: false, messiness_timeout: 0, messiness_inner: 0, messiness_center: false,
  garbageabsolutecap: 0, garbagecapincrease: 0, garbagecapmax: 40, garbagecap: 8, garbagecapmargin: 0,
  usebombs: false, roundmode: "down", openerphase: 0, garbagespecialbonus: false, allclears: true,
  allclear_garbage: 10, allclear_b2b: 0, b2bcharging: false, infinite_movement: false, lockresets: 15,
  locktime: 30, gravitymay20g: false, allow180: true, allow_harddrop: true, display_hold: true,
  can_undo: false, can_retry: false, infinite_hold: false, stride: false, passthrough: "zero",
};

// player      = one entry of d.replay.rounds[r] (has .replay.{options,events,frames}, .username, .alive)
// roundPlayers = the whole round array (both players; used for opponent gameids)
export function replayRound(player, roundPlayers, { untilFrame = null } = {}) {
  const o = player.replay.options;
  const players = roundPlayers.map((p) => ({ gameid: p.replay.options.gameid, userid: p.id, username: p.username }));
  const byFrame = new Map();
  for (const e of player.replay.events) { if (!byFrame.has(e.frame)) byFrame.set(e.frame, []); byFrame.get(e.frame).push(e); }
  // recorded garbage batches from the ige `interaction` events, keyed by batch id (`iid`). Pairing
  // holes by iid — not by a blind oldest-first FIFO over every recorded line — is the ONLY reliable
  // scheme: most recorded garbage is CANCELLED before it inserts (the loads sum to far more lines
  // than a 20-high board holds), and a positional FIFO desyncs permanently at the first cancel,
  // handing every later insertion an earlier, cancelled batch's hole column.
  const loads = player.replay.events
    .filter((e) => e.type === "ige" && e.data?.data?.type === "garbage" && e.data.type === "interaction")
    .map((e) => ({ amt: e.data.data.amt, x: e.data.data.x, iid: e.data.data.iid }));
  const iidToX = new Map(loads.map((l) => [l.iid, l.x]));

  const engine = Game.createEngine({ ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g }, o.gameid, players);
  // Holes of garbage that ACTUALLY inserts, in insertion order — Triangle emits `garbage.tank` per
  // inserted batch (cancelled batches never tank), carrying the batch `iid` we map back to the
  // recorded hole `x`. Accumulated during each tick, consumed by injectHoles after it. Falls back to
  // Triangle's own re-rolled column only for an iid the recording somehow lacks.
  const holeFIFO = [];
  engine.events.on("garbage.tank", (ev) => {
    const x = iidToX.has(ev.iid) ? iidToX.get(ev.iid) : ev.column;
    for (let i = 0; i < ev.amount; i++) holeFIFO.push(x);
  });
  const holeWidth = 10 - (o.garbageholesize ?? 1);
  const gbTile = () => ({ mino: "gb", connections: 0 });
  const gRowIdx = () => {
    const st = engine.board.state, idx = [];
    for (let r = 0; r < st.length; r++) if (st[r].filter((t) => t && t.mino === "gb").length >= holeWidth) idx.push(r);
    return idx;
  };
  // Assign holes ONCE per insertion (garbage inserts only on non-clearing locks, so a garbage-row-count
  // INCREASE is pure insertion). New rows are at the bottom (row 0 = floor); consume the FIFO in order.
  let prevG = 0, hi = 0;
  const injectHoles = () => {
    const idx = gRowIdx();
    if (idx.length > prevG) {
      const K = idx.length - prevG, st = engine.board.state, bottomK = idx.slice(0, K);
      for (let k = 0; k < K; k++) {
        const r = bottomK[k], wantX = holeFIFO[hi + k];
        const curHole = st[r].findIndex((t) => t == null || t.mino !== "gb");
        if (wantX != null && curHole !== wantX) { st[r][curHole] = gbTile(); st[r][wantX] = null; }
      }
      hi += K;
    }
    prevG = idx.length;
  };
  const enc = () => {
    const st = engine.board.state;
    let out = "";
    for (let vr = 0; vr < 20; vr++) { const r = 19 - vr; for (let c = 0; c < 10; c++) { const t = st[r]?.[c]; out += t == null ? "." : t.mino === "gb" ? "G" : "#"; } }
    return out;
  };

  const total = untilFrame ?? player.replay.frames ?? 2000;
  const grids = new Map();
  for (let f = 0; f <= total; f++) { engine.tick(byFrame.get(f) || []); injectHoles(); grids.set(f, enc()); }
  return { grids, gridAt: (f) => grids.get(f), frames: total, garbageLoads: loads, alive: player.alive };
}
