// Scan every session, collect every DETECTED forecast (mechanism-established: forecast_lineclear /
// forecast_garbage) over the verified prefix, tag which survive all four clauses (isVerifiedForecast),
// and emit board snapshots so an HTML page can draw each one. Read-only; writes JSON to stdout.
import { readdirSync, existsSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex } from '../../pipeline/sim/verified-prefix.ts';
import { forecastMetric, isVerifiedForecast } from '../../pipeline/sim/forecast.ts';

const SESSIONS_DIR = `${import.meta.dirname}/../../sessions`;
const SESSIONS = readdirSync(SESSIONS_DIR)
  .map(s => `${SESSIONS_DIR}/${s}`)
  .filter(p => existsSync(`${p}/sim`) && existsSync(p))
  .sort();

// board[k-1] is 40 rows y-down; crop to the occupied region for a compact diagram.
function cropBoard(board, extraCells) {
  const H = board.length, W = board[0].length;
  let top = H, bot = -1;
  const occ = (r) => board[r].some(x => x !== null) || extraCells.some(c => c.row === r);
  for (let r = 0; r < H; r++) if (occ(r)) { if (r < top) top = r; bot = r; }
  if (bot < 0) return { rows: [], top: 0 };
  top = Math.max(0, top - 1);
  bot = Math.min(H - 1, bot + 1);
  const rows = [];
  for (let r = top; r <= bot; r++) {
    const row = [];
    for (let c = 0; c < W; c++) {
      const v = board[r][c];
      row.push(v === null ? '.' : (v === 'G' ? 'G' : String(v)));
    }
    rows.push(row.join(''));
  }
  return { rows, top };
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
      const k = rec.lockIndex;
      const board = r.boards[k - 1];               // the board the T dropped into
      const cells = r.locks[k].cells;              // the executed T's cells (y-down)
      const crop = cropBoard(board, cells);
      out.push({
        session, file: c.file, round: c.round, user: c.user,
        lockIndex: k, frame: rec.frame, kind: rec.kind,
        lines: rec.lines, spin: rec.spin, separation: rec.separation,
        roofFrom: rec.roofFrom, availAtRoof: rec.availAtRoof, availAtSpin: rec.availAtSpin,
        floorOrigin: rec.floorOrigin, closingClearWasSpin: rec.closingClearWasSpin,
        verified: isVerifiedForecast(rec),
        board: crop.rows, boardTop: crop.top,
        cells: cells.map(cc => ({ col: cc.col, row: cc.row })),
      });
    }
  }
}
process.stdout.write(JSON.stringify(out, null, 2));
