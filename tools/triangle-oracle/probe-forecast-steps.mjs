// For every mechanism-established forecast, emit the board at each STAGE of the forecast story:
//   roof     — boards[j]   : the roof is up, the slot cannot clear yet (avail@roof, ~0)
//   before   — boards[t-1] : just before the line clear that opens the slot
//   open     — boards[t]   : the clear has opened the slot (avail rises)
//   drop     — boards[k-1] : the board the T drops into (T overlaid)
//   result   — boards[k]   : the T-spin has cleared its lines
// Each forecast's stages share ONE vertical crop window, so the stack visibly drops a row when a
// line clears. Read-only; JSON to stdout.
import { readdirSync, existsSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex } from '../../pipeline/sim/verified-prefix.ts';
import { forecastMetric, isVerifiedForecast, bestTspinLines } from '../../pipeline/sim/forecast.ts';

const SESSIONS_DIR = `${import.meta.dirname}/../../sessions`;
const SESSIONS = readdirSync(SESSIONS_DIR).map(s => `${SESSIONS_DIR}/${s}`)
  .filter(p => existsSync(`${p}/sim`)).sort();

const W = 10, HH = 40;

function occRange(board, extra) {
  let top = HH, bot = -1;
  for (let r = 0; r < HH; r++) {
    const on = board[r].some(x => x !== null) || extra.some(c => c.row === r);
    if (on) { if (r < top) top = r; bot = r; }
  }
  return [top, bot];
}

function cropAt(board, top, bot, overlay) {
  const tset = new Set((overlay || []).map(c => `${c.col},${c.row}`));
  const rows = [];
  for (let r = top; r <= bot; r++) {
    let line = '';
    for (let c = 0; c < W; c++) {
      if (tset.has(`${c},${r}`)) { line += '*'; continue; }   // executed T-spin
      const v = board[r][c];
      line += v === null ? '.' : (v === 'G' ? 'G' : String(v));
    }
    rows.push(line);
  }
  return rows;
}

const out = [];
for (const dir of SESSIONS) {
  const session = dir.split('/').pop();
  for (const c of loadCases(dir)) {
    const r = runCaseOracle(c);
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v) continue;
      if (rec.kind !== 'forecast_lineclear' && rec.kind !== 'forecast_garbage') continue;
      const k = rec.lockIndex, j = rec.roofFrom, t = rec.mechanismStep;
      const Tcells = r.locks[k].cells.map(cc => ({ col: cc.col, row: cc.row }));

      // build the ordered, de-duplicated stage list
      const raw = [];
      if (j != null && j >= 0) raw.push(['roof', j, null]);
      if (t != null && t - 1 >= 0 && t - 1 !== j) raw.push(['before', t - 1, null]);
      if (t != null && t >= 0) raw.push(['open', t, null]);
      raw.push(['drop', k - 1, Tcells]);
      raw.push(['result', k, null]);
      // drop consecutive duplicate board indices (keep the later, more informative role)
      const stages = [];
      for (const s of raw) {
        const prev = stages[stages.length - 1];
        if (prev && prev[1] === s[1]) stages[stages.length - 1] = s; else stages.push(s);
      }

      // one shared vertical window across all stage boards (so a clear visibly drops the stack)
      let top = HH, bot = -1;
      for (const [, idx, ov] of stages) {
        const [tt, bb] = occRange(r.boards[idx], ov || []);
        if (bb < 0) continue;
        if (tt < top) top = tt; if (bb > bot) bot = bb;
      }
      top = Math.max(0, top - 1); bot = Math.min(HH - 1, bot + 1);

      const steps = stages.map(([role, idx, ov]) => ({
        role, lockIndex: idx,
        avail: bestTspinLines(r.boards[idx]),
        board: cropAt(r.boards[idx], top, bot, ov),
      }));

      out.push({
        session, file: c.file, round: c.round, user: c.user,
        lockIndex: k, frame: rec.frame, kind: rec.kind, lines: rec.lines, spin: rec.spin,
        separation: rec.separation, roofFrom: j, mechanismStep: t,
        availAtRoof: rec.availAtRoof, availAtSpin: rec.availAtSpin,
        floorOrigin: rec.floorOrigin, closingClearWasSpin: rec.closingClearWasSpin,
        verified: isVerifiedForecast(rec), steps,
      });
    }
  }
}
process.stdout.write(JSON.stringify(out, null, 2));
