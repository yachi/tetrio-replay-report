/**
 * How much of the corpus tucks into the C-Spin's own slot geometry?
 *
 * Same window test as `cspin-match.ts`, run over every verified tucked T-spin in the four sessions
 * and cross-tabulated by kind. The point of running it over EVERYTHING is the control: if every
 * Triple matches, the test is measuring "this is a Triple", not "this is the C-Spin", and the
 * cross-tab is what makes that visible instead of letting a single matching example stand in for a
 * finding.
 *
 *   bun run cspin-corpus.ts sessions/2026-07-22 [...]
 */
import { readFileSync } from 'node:fs';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric } from './forecast.ts';
import { H } from './sim.ts';

const CSPIN = JSON.parse(readFileSync(`${import.meta.dir}/wiki-cspin-boards.json`, 'utf8')) as
  { rows: string[]; piece: { row: number; col: number }[]; lines: number }[];

function mask(filled: (r: number, c: number) => boolean, cells: { row: number; col: number }[]) {
  const rs = cells.map(c => c.row), cs = cells.map(c => c.col);
  const own = new Set(cells.map(c => `${c.row}:${c.col}`));
  const out: string[] = [];
  for (let r = Math.min(...rs) - 2; r <= Math.max(...rs) + 1; r++) {
    let line = '';
    for (let c = Math.min(...cs) - 1; c <= Math.max(...cs) + 1; c++)
      line += own.has(`${r}:${c}`) ? '.' : filled(r, c) ? '#' : '.';
    out.push(line);
  }
  return out;
}

const WIKI = CSPIN.map((o, i) => {
  const m = mask((r, c) => {
    if (c < 0 || c > 9) return true;
    const row = o.rows[r];
    if (row === undefined) return r >= o.rows.length;
    return row[c] !== '.' && row[c] !== 'P';
  }, o.piece);
  return { i, lines: o.lines, mask: m, mirror: m.map(l => [...l].reverse().join('')) };
});

// every event, so the same array answers the cross-tab and any single-event lookup
const events: any[] = [];
const key = (kind: string, lines: number) => `${kind} · ${lines}-line`;
const tally: Record<string, { n: number; drawn: number; mirrored: number; early: number; roofs: number[] }> = {};
const shapes: Record<string, number> = {};

for (const session of process.argv.slice(2)) {
  process.env.REPLAY_DIR = session;
  for (const c of loadCases(session)) {
    const r = runCase(c, {});
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v) continue;
      const lk = r.locks[rec.lockIndex]!, board = r.boards[rec.lockIndex - 1]!;
      const m = mask((row, col) =>
        col < 0 || col > 9 || row >= H ? true : row < 0 ? false : board[row]![col] !== null, lk.cells);
      const eq = (a: string[]) => a.length === m.length && a.every((l, i) => l === m[i]);
      const drawn = WIKI.some(w => eq(w.mask)), mirrored = WIKI.some(w => eq(w.mirror));
      const kk = key(rec.kind, rec.lines);
      const t = tally[kk] ??= { n: 0, drawn: 0, mirrored: 0, early: 0, roofs: [] as number[] };
      t.n++; if (drawn) t.drawn++; if (mirrored) t.mirrored++;
      if (rec.roofFrom !== null) { t.roofs.push(rec.roofFrom); if (rec.roofFrom <= 10) t.early++; }
      if (rec.lines === 3) shapes[m.join('/')] = (shapes[m.join('/')] ?? 0) + 1;
      events.push({ session: session.split('/').pop(), user: c.user, file: c.file, round: c.round,
        lock: rec.lockIndex, kind: rec.kind, lines: rec.lines, roof: rec.roofFrom,
        roofPiece: rec.roofFrom !== null ? r.locks[rec.roofFrom]!.piece : null,
        separation: rec.separation, drawn, mirrored, window: m });
    }
  }
}

if (process.env.JSON) {
  const wik = WIKI.filter(w => w.lines === 3)[0]!;
  console.log(JSON.stringify({ events, wikiWindow: wik.mask, wikiWindowMirror: wik.mirror,
    wikiDiagrams: WIKI.length }));
  process.exit(0);
}

const pc = (xs: number[], p: number) => { const s = [...xs].sort((a, b) => a - b); return s.length ? s[Math.min(s.length - 1, Math.floor(p * s.length))]! : NaN; };
const med = (xs: number[]) => { const s = [...xs].sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)]! : NaN; };
console.log('kind · lines                 n   C-Spin window (drawn/mirrored)  share   roof<=10   roof median');
for (const [k, t] of Object.entries(tally).sort())
  console.log(`  ${k.padEnd(26)} ${String(t.n).padStart(4)}   ${String(t.drawn).padStart(4)} / `
    + `${String(t.mirrored).padStart(4)}   ${((t.drawn + t.mirrored) / t.n * 100).toFixed(1).padStart(6)}%`
    + `   ${String(t.early).padStart(4)}/${t.n}   ${String(med(t.roofs)).padStart(6)}`
    + `   roof p10/p25/p75/p90 ${pc(t.roofs, .1)}/${pc(t.roofs, .25)}/${pc(t.roofs, .75)}/${pc(t.roofs, .9)}`);

const distinct = Object.entries(shapes).sort((a, b) => b[1] - a[1]);
console.log(`\ndistinct slot windows among 3-line spins: ${distinct.length}`);
for (const [s, n] of distinct.slice(0, 6)) console.log(`  ${String(n).padStart(4)}  ${s}`);
