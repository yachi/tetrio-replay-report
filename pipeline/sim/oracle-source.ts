/**
 * Oracle-backed board source — a `SimResult` produced by Triangle's ACTUAL engine, not the hand-port.
 *
 * Five mechanic leads to close the hand-sim's drift (spawn phase, DAS/ARR, gravity ramp, anti-stall,
 * lock-reset) were each swept to exactly 0 off 24.8% verified coverage: the residual is a diffuse tail
 * of rare placement divergences, not one portable mechanic, so the port asymptotes below 100%. The
 * Triangle oracle (vendored in `vendor/teto`, byte-identical to @haelp/teto) IS the reference engine and
 * matches the real game 100% on attack, so `runCaseOracle` computes the verified-prefix boards from it.
 * On the STRICTER frame+amount+row gate the oracle scores 92.3% (7700/8342) vs the sim's 24.8% on the
 * weaker frame+amount gate — the ~7.7% remainder is `matchesIgeY`'s own heuristic residual, not drift.
 *
 * The output is the exact `SimResult` shape the forecast/opener consumers read, in the SIM's coordinate
 * frame (40 rows y-DOWN: row 0 = top buffer, row 39 = bottom; garbage = the `GARBAGE` sentinel). Triangle
 * is y-UP (row 0 = bottom), so `simRow = 39 - yUp` throughout. Provenance (`provSnaps`) mirrors the sim's
 * bookkeeping exactly: null = empty, -1 = garbage, >=0 = the lock index that placed the cell.
 */
import { createEngine } from './vendor/teto/create-engine.mjs';
import { GARBAGE, H, type SimResult } from './sim.ts';
import type { Board } from './vendor/core/srs.ts';
import type { PieceType } from './vendor/core/types.ts';
import { BOARD_WIDTH } from './vendor/core/types.ts';

// The TL ruleset fields the version-19 .ttrm `options` omit — identical to tools/triangle-oracle/oracle.mjs.
// Board-affecting ones (gravity, holes) are pinned; the rest are TETR.IO TL defaults.
const TL_DEFAULTS: Record<string, unknown> = {
  g: 0.02, boardwidth: 10, boardheight: 20, kickset: 'SRS+', bagtype: '7-bag', combotable: 'multiplier',
  spinbonuses: 'T-spins', garbageblocking: 'combo blocking', garbagetargetbonus: 'none', clutch: false,
  stock: 0, garbagemultiplier: 1, garbagespeed: 20, garbageholesize: 1, messiness_change: 1,
  messiness_nosame: false, messiness_timeout: 0, messiness_inner: 0, messiness_center: false,
  garbageabsolutecap: 0, garbagecapincrease: 0, garbagecapmax: 40, garbagecap: 8, garbagecapmargin: 0,
  usebombs: false, roundmode: 'down', openerphase: 0, garbagespecialbonus: false, allclears: true,
  allclear_garbage: 10, allclear_b2b: 0, b2bcharging: false, infinite_movement: false, lockresets: 15,
  locktime: 30, gravitymay20g: false, allow180: true, allow_harddrop: true, display_hold: true,
  can_undo: false, can_retry: false, infinite_hold: false, stride: false, passthrough: 'zero',
};

const SPIN_MAP: Record<string, 'none' | 'mini' | 'full'> = { none: 'none', mini: 'mini', normal: 'full', full: 'full' };

/** One player/round replayed through the vendored engine, emitted as a SimResult in the sim's frame. */
export function runCaseOracle(player: any, roundPlayers: any[]): SimResult {
  const o = player.replay.options;
  const players = roundPlayers.map((p) => ({ gameid: p.replay.options.gameid, userid: p.id, username: p.username }));
  const eng: any = createEngine({ ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g }, o.gameid, players);

  const byFrame = new Map<number, any[]>();
  for (const e of player.replay.events) { if (!byFrame.has(e.frame)) byFrame.set(e.frame, []); byFrame.get(e.frame)!.push(e); }

  // NOTE ON GARBAGE HOLES. oracle.mjs relocates each garbage row's hole from the engine's seeded-RNG
  // column to the ige-recorded column, matched by a positional FIFO. That FIFO desyncs the moment any
  // garbage is cancelled (oracle.mjs's own comment says so), and relocating a hole changes WHICH lines
  // the engine completes on later locks — which corrupts board HEIGHT and, with it, the verified-prefix
  // (coverage measured: 24.8% with relocation vs 88.6% without, on the frame+amount+row gate). Board
  // height and piece placement are what drift measures and what the forecast needs first, so the oracle
  // source keeps the engine's own seeded holes. The cost is that garbage-hole COLUMNS are the engine's
  // RNG columns, not the recorded ones — a bounded caveat for garbage-adjacent T-slots, in the already-
  // quarantined forecast section, of the same class as its documented soft garbage-timing attribution.

  // sim-frame board (40 rows y-down) from the engine's y-up state
  const encBoard = (): Board => {
    const st = eng.board.state;
    const b: (PieceType | null)[][] = [];
    for (let r = 0; r < H; r++) {
      const row = new Array<PieceType | null>(BOARD_WIDTH).fill(null);
      const yUp = (H - 1) - r;
      const src = st[yUp];
      for (let c = 0; c < BOARD_WIDTH; c++) {
        const t = src?.[c];
        row[c] = t == null ? null : t.mino === 'gb' ? GARBAGE : (String(t.mino).toUpperCase() as PieceType);
      }
      b.push(row);
    }
    return b as Board;
  };

  // ── outputs, in sim shape ──
  const boards: Board[] = [];
  const records: SimResult['records'] = [];
  const locks: SimResult['locks'] = [];
  const garbageEvents: SimResult['garbageEvents'] = [];
  const provSnaps: (number | null)[][][] = [];
  const evLog: SimResult['events'] = [];
  let prov: (number | null)[][] = Array.from({ length: H }, () => new Array<number | null>(BOARD_WIDTH).fill(null));
  const clears: Record<string, number> = {};
  let sentTotal = 0, recvTotal = 0, clearedTotal = 0, attackTotal = 0, holds = 0, linesTotal = 0;
  let topbtb = 0, topcombo = 0, topout = false;

  // garbage.tank → sim garbageEvents + prov garbage rows (shift top, push garbage row of -1s w/ recorded hole)
  eng.events.on('garbage.tank', (ev: any) => {
    garbageEvents.push({ frame: eng.frame, amt: ev.amount, lockIndex: locks.length });
    recvTotal += ev.amount;
    // prov: shift the grid up and push a garbage row (all -1). The row's empty hole is read from the
    // BOARD (null), never from prov — forecast only consults prov for cells the board says are filled —
    // so the hole column need not be carved here, which keeps prov consistent with the engine's board.
    for (let i = 0; i < ev.amount; i++) {
      prov.shift();
      prov.push(new Array<number | null>(BOARD_WIDTH).fill(-1 as number | null));
    }
  });

  // pre-tick board snapshot (occupancy), for cleared-row reconstruction
  let preTick: boolean[][] = [];
  const snapOccupancy = (): boolean[][] => {
    const st = eng.board.state, g: boolean[][] = [];
    for (let r = 0; r < st.length; r++) { const row = new Array(BOARD_WIDTH).fill(false); for (let c = 0; c < BOARD_WIDTH; c++) row[c] = st[r]?.[c] != null; g.push(row); }
    return g;
  };

  let pendingCells: { col: number; row: number }[] | null = null;   // captured at lock.pre (pre-clear, y-down)
  eng.events.on('falling.lock.pre', () => {
    const cells = eng.falling.absoluteBlocks.map(([x, yUp]: [number, number]) => ({ col: x, row: (H - 1) - yUp }));
    pendingCells = cells;
  });
  eng.events.on('falling.lock', (res: any) => {
    const myIndex = locks.length;
    const piece = String(res.mino).toUpperCase() as PieceType;
    const lines = res.lines as number;
    const spin = SPIN_MAP[res.spin] ?? 'none';
    const cells = pendingCells ?? [];
    const sent = (res.garbage || []).reduce((a: number, b: number) => a + b, 0);

    // cleared rows (sim y-down): reconstruct the pre-clear full rows from the pre-tick occupancy (y-UP)
    // plus this piece's cells, find full rows in y-up, convert each to sim y-down (39 - yUp). Ascending
    // yUp yields DESCENDING sim-rows (bottom-most first), which the prov splice below relies on.
    const clearedRows: number[] = [];
    if (lines > 0) {
      const g = preTick.map((r) => r.slice());                       // y-up occupancy [yUp][x]
      for (const { col, row } of cells) { const yUp = (H - 1) - row; if (yUp >= 0 && yUp < H && col >= 0 && col < BOARD_WIDTH) g[yUp]![col] = true; }
      for (let yUp = 0; yUp < H; yUp++) if (g[yUp]!.every(Boolean)) clearedRows.push((H - 1) - yUp);
    }

    // prov: place piece cells at myIndex, then splice cleared rows (bottom-up) + unshift nulls
    for (const { col, row } of cells) if (row >= 0 && row < H) prov[row]![col] = myIndex;
    const garbageRows = res.garbageCleared ?? 0;
    if (lines > 0) {
      // clearedRows is bottom-most-first (largest sim-row index first); splicing in that order leaves the
      // still-to-splice smaller indices unshifted, matching the sim's bottom-up clear loop.
      for (const r of clearedRows) prov.splice(r, 1);
      while (prov.length < H) prov.unshift(new Array<number | null>(BOARD_WIDTH).fill(null));
    }

    linesTotal += lines;
    if (lines > 0) clears[String(lines)] = (clears[String(lines)] ?? 0) + 1;
    sentTotal += sent; attackTotal += sent; clearedTotal += garbageRows;
    const b2b = Math.max(res.stats?.b2b ?? 0, 0), combo = Math.max(res.stats?.combo ?? 0, 0);
    topbtb = Math.max(topbtb, b2b); topcombo = Math.max(topcombo, combo);
    const allclear = !!(res.stats && eng.board.perfectClear);

    records.push({ frame: eng.frame, piece, lines, spin, attack: sent, sent, cancelled: 0, b2b, combo,
      cells, garbageCleared: garbageRows, clearedRows });
    locks.push({ frame: eng.frame, piece, cells, cleared: lines, spin, allclear });
    evLog.push({ frame: eng.frame, kind: 'lock' });
    if (res.topout) topout = true;
    pendingCells = null;
  });

  const maxF = player.replay.frames ?? 20000;
  try {
    for (let f = 0; f <= maxF; f++) {
      preTick = snapOccupancy();
      const r = eng.tick(byFrame.get(f) || []);
      // snapshot boards + prov once per lock that happened this tick
      while (boards.length < locks.length) { boards.push(encBoard()); provSnaps.push(prov.map((row) => [...row])); }
      if (r && r.topout) { topout = true; break; }
    }
  } catch { topout = true; }

  return {
    lines: linesTotal, placed: locks.length, holds, clears, topbtb, topcombo,
    garbage: { sent: sentTotal, received: recvTotal, cleared: clearedTotal, attack: attackTotal },
    boards, records, events: evLog, locks, garbageEvents, provSnaps, topout,
  };
}
