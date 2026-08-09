/**
 * Reachability differential over the external example corpora.
 *
 * The detector's whole numerator rests on `bestTspin`'s BFS: `avail(t) = bestTspinLines(boards[t])`.
 * If that BFS cannot REACH a T-spin that is really executable, `avail` under-reads, a genuine
 * improvement is scored `reactive`, and a real forecast is lost — a false negative that suppresses
 * the count. The C-Spin fixtures already found three such misses (`UNREACHABLE = {31,35,37}`, the
 * engine has no 180 rotation).
 *
 * This is the one false-negative source the captured examples can test WITHOUT synthesising a full
 * SimResult (which would be hand-data): every example frame that DRAWS an executed, line-clearing
 * T-spin is a witness that "a T-spin of N lines is reachable on this board". We strip the T and ask
 * the engine to re-find it. A shortfall is a reachability false negative.
 *
 * Read-only. Prints a table; exits non-zero if any executed spin is unreachable (so it can gate).
 */
import { bestTspin } from './forecast.ts';
import { emptyBoard, H } from './sim.ts';
import { readFileSync } from 'node:fs';
import type { Board, PieceType } from './vendor/core/srs.ts';

const W = 10;
type Frame = { id: string; rows: string[] };

// Place a bottom-aligned ASCII frame into a full H-tall board. '.' empty; a T-cell keeps 'T';
// every other non-'.' glyph is anonymous stack. Returns the board plus the T-cell coords.
function toBoard(rows: string[]): { board: PieceType[][]; tCells: { r: number; c: number }[] } {
  const board = emptyBoard().map(r => [...r]) as any[][];
  const off = H - rows.length;
  const tCells: { r: number; c: number }[] = [];
  rows.forEach((line, i) => [...line].forEach((ch, c) => {
    if (ch === '.') return;
    const r = off + i;
    board[r]![c] = ch === 'T' ? 'T' : 'I';
    if (ch === 'T') tCells.push({ r, c });
  }));
  return { board, tCells };
}

const rowFull = (board: any[][], r: number) => board[r]!.every(cell => cell !== null);

// The lines an executed T clears = rows that are full AND contain one of the T's own cells.
function executedLines(board: any[][], tCells: { r: number; c: number }[]): number {
  const tRows = new Set(tCells.map(t => t.r));
  let n = 0;
  for (const r of tRows) if (rowFull(board, r)) n++;
  return n;
}

function stripT(board: PieceType[][], tCells: { r: number; c: number }[]): Board {
  const b = board.map(r => [...r]);
  for (const t of tCells) b[t.r]![t.c] = null as any;
  return b as Board;
}

function loadFrames(): Frame[] {
  const out: Frame[] = [];
  const jp = JSON.parse(readFileSync(`${import.meta.dir}/jp-forecast-boards.json`, 'utf8'))
    .boards as { img: string; rows: string[] }[];
  for (const b of jp) out.push({ id: `jp/${b.img}`, rows: b.rows });
  const four = JSON.parse(readFileSync(`${import.meta.dir}/four-forecast-boards.json`, 'utf8'))
    .boards as { section: string; page: number; rows: string[] }[];
  for (const b of four) out.push({ id: `four/${b.section}#${b.page}`, rows: b.rows });
  return out;
}

// Cells this frame ADDS to the previous one (bottom-aligned): filled now, empty before. The witness
// we want is the frame where the T is the NEWLY placed piece — the moment of execution — not a later
// frame where the same T sits buried under pieces stacked on top (whose slot is legitimately gone).
function addedTCells(prev: string[] | null, cur: string[]):
    { r: number; c: number }[] | null {
  const { board, tCells } = toBoard(cur);
  if (tCells.length === 0) return null;
  if (!prev) return null;
  // bottom-align previous frame into the same H board
  const prevB = toBoard(prev).board;
  const isT = new Set(tCells.map(t => `${t.r},${t.c}`));
  // every added cell (filled now, empty before) must be a T cell, and every T cell must be added:
  // i.e. the T is exactly the new piece.
  for (let r = 0; r < H; r++) for (let c = 0; c < W; c++) {
    const now = board[r]![c] !== null, before = prevB[r]![c] !== null;
    if (now && !before && !isT.has(`${r},${c}`)) return null;   // added a non-T cell → T isn't the new piece
    if (isT.has(`${r},${c}`) && before) return null;             // a T cell already existed → T is old/buried
  }
  return tCells;
}

type Result = { id: string; expect: number; reached: number; ok: boolean };

function run(): { checked: Result[]; skipped: string[] } {
  const frames = loadFrames();
  const checked: Result[] = [];
  const skipped: string[] = [];
  for (let i = 0; i < frames.length; i++) {
    const f = frames[i]!;
    const prev = i > 0 ? frames[i - 1]!.rows : null;
    const tCells = addedTCells(prev, f.rows);
    if (!tCells) { skipped.push(f.id); continue; }
    const { board } = toBoard(f.rows);
    const expect = Math.max(1, executedLines(board, tCells));  // >=1; full count when rows shown complete
    const before = stripT(board, tCells);
    const reached = bestTspin(before)?.lines ?? 0;
    checked.push({ id: f.id, expect, reached, ok: reached >= expect });
  }
  return { checked, skipped };
}

export { run };
export type { Result };

if (import.meta.main) {
  const { checked, skipped } = run();
  const misses = checked.filter(r => !r.ok);
  console.log(`reachability differential over external forecast examples`);
  console.log(`  executed-spin witnesses checked: ${checked.length}`);
  console.log(`  skipped (not a newly-placed line-clearing T): ${skipped.length}`);
  for (const r of checked) {
    console.log(`  ${r.ok ? 'OK  ' : 'MISS'} ${r.id.padEnd(28)} needs >=${r.expect}  engine reaches ${r.reached}`);
  }
  if (misses.length) {
    console.log(`\n${misses.length} REACHABILITY FALSE NEGATIVE(S): the engine cannot reach a spin the example executes.`);
    for (const m of misses) console.log(`  ${m.id}: example needs >=${m.expect}, engine best ${m.reached}`);
    process.exit(1);
  }
  console.log(`\nno reachability miss — the engine reaches every executed spin drawn in the corpora`);
}
