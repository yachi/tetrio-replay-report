// Extract every decision point (one per piece locked) from .ttrm replays through the vendored
// Triangle engine (the repo's reference board source), as JSONL for the cold-clear coach.
//
// Decision i's START state is captured at the falling.lock of piece i-1 (the engine has already
// placed, cleared, inserted garbage, shifted the queue and spawned the next piece by then), or at
// engine creation for i = 0. The PLAYED placement is the falling piece's absolute cells at
// falling.lock.pre of piece i.
import { createEngine } from '../../pipeline/sim/vendor/teto/create-engine.mjs';
import { loadCases, verifiedIndex, runCaseOracle } from '../../pipeline/sim/verified-prefix.ts';
import { writeFileSync } from 'fs';

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
const H = 40;
const up = (s: any) => s == null ? null : String(s).toUpperCase();

const dir = process.env.REPLAY_DIR!;
const out: string[] = [];
const roundsMeta: any[] = [];
for (const c of loadCases(dir)) {
  const player = c.rawPlayer, roundPlayers = c.rawRound;
  const o = player.replay.options;
  const players = roundPlayers.map((p: any) => ({ gameid: p.replay.options.gameid, userid: p.id, username: p.username }));
  const eng: any = createEngine({ ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g }, o.gameid, players);
  const byFrame = new Map<number, any[]>();
  for (const e of player.replay.events) { if (!byFrame.has(e.frame)) byFrame.set(e.frame, []); byFrame.get(e.frame)!.push(e); }

  // global piece sequence + draw pointer, so the bag state at any decision is exact
  const seq: string[] = [];
  let drawn = 0;
  const syncSeq = () => { eng.queue.forEach((p: any, k: number) => { seq[drawn + k] = up(p)!; }); };
  // the first piece spawns inside the constructor, before this hook exists: count it by hand
  if (eng.falling) { seq[0] = up(eng.falling.symbol)!; drawn = 1; syncSeq(); }
  const origNext = eng.nextPiece.bind(eng);
  eng.nextPiece = (...a: any[]) => { drawn++; const r = origNext(...a); syncSeq(); return r; };

  const field = (): string[] => {
    const st = eng.board.state, rows: string[] = [];
    for (let r = 0; r < H; r++) {
      const src = st[(H - 1) - r]; let s = '';
      for (let x = 0; x < 10; x++) { const t = src?.[x]; s += t == null ? '.' : t.mino === 'gb' ? 'G' : String(t.mino).toUpperCase(); }
      rows.push(s);
    }
    return rows;
  };
  const startState = () => ({
    field: field(), current: up(eng.falling.symbol), hold: up(eng.held),
    next: Array.from(eng.queue).slice(0, o.nextcount ?? 5).map(up),
    b2b: eng.stats.b2b, combo: eng.stats.combo, incoming: eng.garbageQueue.size,
    gmult: eng.dynamic?.garbageMultiplier?.get?.() ?? 1, frame: eng.frame,
    drawnIndex: drawn, // index in seq of the CURRENT piece is drawn-1 (the spawn already counted)
  });

  // initial spawn: the engine spawns the first piece on construction or first tick; capture lazily
  let start: any = null;
  const positions: any[] = [];
  let pendingCells: number[][] | null = null, pendingRot = 0, pendingIncoming = 0, tickIncoming = 0;
  let tankAcc = 0;
  let tankList: any[] = [];
  eng.events.on('garbage.tank', (ev: any) => { tankAcc += ev.amount; tankList.push({ amount: ev.amount, column: ev.column, size: ev.size }); });
  eng.events.on('falling.lock.pre', () => {
    pendingCells = eng.falling.absoluteBlocks.map(([x, yUp]: [number, number]) => [x, (H - 1) - yUp]);
    pendingRot = eng.falling.rotation;
    pendingIncoming = tickIncoming;
  });
  eng.events.on('falling.lock', (res: any) => {
    const piece = up(res.mino);
    positions.push({ start, played: { piece, cells: pendingCells, rotation: pendingRot,
      spin: res.spin ?? 'none', lines: res.lines, sent: (res.garbage || []).reduce((a: number, b: number) => a + b, 0),
      frame: eng.frame, tanked: tankAcc, incomingAtLock: pendingIncoming,
      raw: (res.rawGarbage || []).reduce((a: number, b: number) => a + b, 0), tanks: tankList } });
    tankAcc = 0; tankList = [];
    start = startState();
  });
  const maxF = player.replay.frames ?? 20000;
  let topout = false;
  try {
    for (let f = 0; f <= maxF; f++) {
      if (start == null && eng.falling) { syncSeq(); start = startState(); }
      tickIncoming = eng.garbageQueue.size;   // queued garbage as the frame starts (pre-cancel)
      const r = eng.tick(byFrame.get(f) || []);
      if (r && r.topout) { topout = true; break; }
    }
  } catch { topout = true; }

  // verification: (a) the repo's attack-row gate prefix, (b) whole-round counters vs the replay's own
  const sr = runCaseOracle(c);
  const vIdx = verifiedIndex(sr, c.truth, 'frame+row');
  const rs = player.replay.results.stats;
  const roundOk = sr.locks.length === rs.piecesplaced && sr.lines === rs.lines && positions.length === rs.piecesplaced;
  // bag check: every aligned block of 7 in seq must be a permutation
  let bagOk = true;
  for (let b = 0; b + 7 <= seq.length; b += 7) if (new Set(seq.slice(b, b + 7)).size !== 7) bagOk = false;

  roundsMeta.push({ file: c.file, round: c.round, user: c.user, alive: c.alive, locks: positions.length,
    placed: rs.piecesplaced, lines: [sr.lines, rs.lines], vIdx, roundOk, bagOk, seqLen: seq.length, seq: seq.join('') });

  positions.forEach((p, i) => {
    if (!p.start) return;
    const cur = p.start.drawnIndex - 1;              // index of the current piece in seq
    const blk = Math.floor(cur / 7) * 7;
    const bagRemainBeforeCurrent = seq.slice(cur, blk + 7);   // pieces not yet drawn from current bag, incl current
    out.push(JSON.stringify({
      id: `${c.file.replace('replay-', '').replace('.ttrm', '')}/r${c.round}/${c.user}/${i}`,
      file: c.file, round: c.round, user: c.user, lock: i, verified: i <= vIdx, roundOk, bagOk,
      ...p.start, bagRemain: bagRemainBeforeCurrent, seqCurrent: seq[cur], seqIndex: cur,
      played: p.played,
    }));
  });
}
writeFileSync(process.env.OUT!, out.join('\n') + '\n');
writeFileSync(process.env.OUT! + '.rounds.json', JSON.stringify(roundsMeta, null, 1));
console.error('positions', out.length, 'rounds', roundsMeta.length,
  'roundOk', roundsMeta.filter(r => r.roundOk).length, 'bagOk', roundsMeta.filter(r => r.bagOk).length);
