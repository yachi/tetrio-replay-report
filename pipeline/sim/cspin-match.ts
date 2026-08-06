/**
 * Is a given executed T-spin the C-Spin's spin?
 *
 * The oracle is harddrop.com/wiki/C-Spin's own diagrams (`wiki-cspin-boards.json`, 38 placements,
 * `P` marking the T). For each, the local shape around the piece is extracted as a filled/empty
 * mask — rows [minRow-2 .. maxRow+1] x cols [minCol-1 .. maxCol+1], with the piece's own cells read
 * as EMPTY, which is what the board looked like before it went in. The same window is taken from a
 * real board just before its spin. Equal masks = the same slot, wherever it sits on the field.
 *
 * What this can and cannot say: a match means the geometry the T tucked into is the one the C-Spin
 * article draws. It does NOT by itself prove the player was running the opener — for that, the
 * timing (which bag) and the follow-up are reported alongside, unjudged.
 *
 *   bun run cspin-match.ts <session> <file> <round> <user>
 */
import { readFileSync } from 'node:fs';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric } from './forecast.ts';
import { H } from './sim.ts';

const CSPIN = JSON.parse(readFileSync(`${import.meta.dir}/wiki-cspin-boards.json`, 'utf8')) as
  { rows: string[]; piece: { row: number; col: number }[]; lines: number }[];

/** filled/empty mask of the window around `cells`, with those cells forced empty */
function mask(filled: (r: number, c: number) => boolean, cells: { row: number; col: number }[]) {
  const rs = cells.map(c => c.row), cs = cells.map(c => c.col);
  const r0 = Math.min(...rs) - 2, r1 = Math.max(...rs) + 1;
  const c0 = Math.min(...cs) - 1, c1 = Math.max(...cs) + 1;
  const own = new Set(cells.map(c => `${c.row}:${c.col}`));
  const out: string[] = [];
  for (let r = r0; r <= r1; r++) {
    let line = '';
    for (let c = c0; c <= c1; c++)
      line += own.has(`${r}:${c}`) ? '.' : filled(r, c) ? '#' : '.';
    out.push(line);
  }
  return out;
}

const wikiMasks = CSPIN.map((o, i) => {
  const off = 0;                                   // diagram rows are their own frame
  const filled = (r: number, c: number) => {
    if (c < 0 || c > 9) return true;               // walls read as filled, same as a real field
    const row = o.rows[r - off];
    if (row === undefined) return r >= o.rows.length;   // below the drawing = floor
    return row[c] !== '.' && row[c] !== 'P';
  };
  const m = mask(filled, o.piece);
  // The article draws one handedness. A mirrored board is the same opener played the other way, so
  // the flipped window counts as a match and is reported as such rather than folded in silently.
  return { i, lines: o.lines, mask: m, mirror: m.map(l => [...l].reverse().join('')) };
});

const [session, file, roundS, user] = process.argv.slice(2);
if (!session || !file || !roundS || !user) throw new Error('usage: <session> <file> <round> <user>');
process.env.REPLAY_DIR = session;
const c = loadCases(session).find(x => x.file === file && x.round === Number(roundS) && x.user === user);
if (!c) throw new Error('no such round');
const r = runCase(c, {});
const v = verifiedIndex(r, c.truth);
const { records } = forecastMetric(r, true);

console.log(`${c.user} ${c.file} r${c.round} · verified through lock ${v}\n`);
for (const rec of records) {
  if (rec.lockIndex > v) continue;
  const k = rec.lockIndex, lk = r.locks[k]!;
  const board = r.boards[k - 1]!;
  const filled = (row: number, col: number) =>
    col < 0 || col > 9 || row >= H ? true : row < 0 ? false : board[row]![col] !== null;
  const m = mask(filled, lk.cells);
  const eq = (a: string[]) => a.length === m.length && a.every((l, i) => l === m[i]);
  const hits = wikiMasks.filter(w => eq(w.mask));
  const mirrored = wikiMasks.filter(w => eq(w.mirror));
  const roofPiece = rec.roofFrom !== null ? r.locks[rec.roofFrom]!.piece : null;
  console.log(`lock ${k}  ${lk.cleared}-line ${lk.spin} spin  kind ${rec.kind}  roof lock ${rec.roofFrom}`
    + ` (${roofPiece})  separation ${rec.separation}`);
  console.log(`  slot window:\n${m.map(l => '    ' + l).join('\n')}`);
  console.log(`  identical window, as drawn: `
    + (hits.length ? `${hits.length} diagrams — ` + hits.slice(0, 6).map(h => `#${h.i}/${h.lines}L`).join(' ') : 'none'));
  console.log(`  identical window, mirrored: `
    + (mirrored.length ? `${mirrored.length} diagrams — ` + mirrored.slice(0, 6).map(h => `#${h.i}/${h.lines}L`).join(' ') : 'none'));
}

// the opener's second half: a Double following the Triple, within three bags of the round's start
const spins = r.locks.map((lk: any, i: number) => ({ i, cleared: lk.cleared, spin: lk.spin }))
  .filter((x: any) => x.spin !== 'none' && x.cleared > 0 && x.i <= v);
console.log(`\nevery verified spin in the round: `
  + (spins.length ? spins.map((s: any) => `lock ${s.i}: ${s.cleared} lines`).join(' · ') : 'none'));
console.log(`opening pieces: ${r.locks.slice(0, 14).map((l: any) => l.piece).join('')}`);
