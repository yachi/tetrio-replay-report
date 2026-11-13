/**
 * The Rust port of `enginePlacements` (pipeline/sim/pc-solver-rs/src/engine_gen.rs) against the TS one
 * (pc-engine-gen.ts), list for list, order included. Cases: every pre-lock board `pc-miss.ts`'s
 * `build()` constructs (admitted player-rounds, at most MAXH rows, `frames` non-empty) in a few
 * sessions, for all seven pieces and every H in `frames(rows, MAXH)`; then random boards (sparse and
 * dense, so overhangs, tucks and spin-only slots occur) and hand-built slots (a T-spin triple slot, an
 * S/Z tuck, a slot only a 180 reaches). The Rust side runs through the `engine_gen_dump` binary, which
 * includes engine_gen.rs by path, so this test does not depend on the crate's FFI.
 *
 *   bun test pipeline/sim/pc-engine-gen-native.test.ts
 *   ENGINE_GEN_SESSIONS=2026-10-20,2026-09-19 bun test ...   (default: 10-20 only; the three-session run took about 105 s)
 */
import { test, expect } from 'bun:test';
import { existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { placeCells, WIDTH } from './emit-replay.ts';
import { frames, height } from './pc-solver.ts';
import { enginePlacements } from './pc-engine-gen.ts';
import { MAXH } from './pc-miss.ts';

const CRATE = 'pipeline/sim/pc-solver-rs';
const BIN = `${CRATE}/target/release/engine_gen_dump`;
const SESSIONS = (process.env.ENGINE_GEN_SESSIONS ?? '2026-10-20').split(',');
const PIECES = 'IJLOSZT';
const hasCargo = spawnSync('cargo', ['--version']).status === 0;

type Case = { rows: number[]; piece: string; H: number };

const toMasks = (b: (string | null)[][]) => {
  const m = b.map(r => r.reduce((a, c, x) => a | (c != null ? 1 << x : 0), 0));
  let h = m.length; while (h && !m[h - 1]) h--;
  return m.slice(0, h);
};

/** The pre-lock boards of `pc-miss.ts`'s `build()` (its board walk, copied: importing `build` runs
 *  the solver), kept when `fits` would keep them. */
function sessionBoards(dir: string): number[][] {
  const RF = JSON.parse(readFileSync(`${dir}/sim/replay-facts.json`, 'utf8'));
  const out: number[][] = [];
  for (const rd of RF.rounds) for (const P of rd.players) {
    if (!P.admission.ok) continue;
    const seq: string = rd.seq;
    const board: (string | null)[][] = Array.from({ length: 40 }, () => new Array(WIDTH).fill(null));
    let cur = seq[0]!, ptr = 1, hold = '';
    for (const lk of P.locks) {
      for (const [col, amt] of lk[4]) {
        const rows = Array.from({ length: amt }, () => { const r = new Array<string | null>(WIDTH).fill('G'); r[col] = null; return r; });
        board.splice(0, 0, ...rows); board.splice(40 - amt - 1, amt);
      }
      const pre = toMasks(board);
      if (height(pre) <= MAXH && frames(pre, MAXH).length > 0) out.push(pre);
      if (lk[5]) { if (hold === '') { hold = cur; cur = seq[ptr++]!; } else { const t = hold; hold = cur; cur = t; } }
      for (const c of placeCells(cur, lk[1])) board[Math.floor(c / WIDTH)]![c % WIDTH] = cur;
      const full: number[] = [];
      for (let y = 0; y < 40; y++) if (board[y]!.every(v => v != null)) full.push(y);
      for (let k = full.length - 1; k >= 0; k--) { board.splice(full[k]!, 1); board.push(new Array(WIDTH).fill(null)); }
      cur = seq[ptr++]!;
    }
  }
  return out;
}

/** Park–Miller, so the random boards are the same every run. */
function rng(seed: number) { let s = seed; return () => (s = s * 16807 % 2147483647) / 2147483647; }

function randomBoards(n: number): number[][] {
  const r = rng(12345), out: number[][] = [];
  for (let i = 0; i < n; i++) {
    const h = 1 + Math.floor(r() * MAXH), dens = [0.25, 0.5, 0.7, 0.85][i % 4]!;
    const rows: number[] = [];
    for (let y = 0; y < h; y++) {
      let m = 0;
      for (let x = 0; x < WIDTH; x++) if (r() < dens) m |= 1 << x;
      rows.push(m === 1023 ? m & ~(1 << Math.floor(r() * WIDTH)) : m);
    }
    while (rows.length && !rows[rows.length - 1]) rows.pop();
    out.push(rows);
  }
  return out;
}

/** Rows drawn top-down, '#' filled. */
const draw = (...lines: string[]) => lines.reverse().map(l => [...l].reduce((a, c, x) => a | (c === '#' ? 1 << x : 0), 0));
const HAND: number[][] = [
  // a T-spin triple slot (reached by a kick through the overhang)
  draw('###.......', '##........', '##.#######', '##..######', '##.#######'),
  // a T-spin double slot
  draw('##........', '#...######', '##.#######'),
  // S and Z tucks under an overhang
  draw('......####', '.....#####', '..........', '#.#.......'),
  draw('####......', '#####.....', '..........', '.......#.#'),
  // a slot a 180 reaches (an L/J under a lip), and an I under a roof
  draw('#########.', '#.........', '#..#######'),
  draw('..........', '####......', '..........', '##########'.slice(0, 6) + '....'),
  // closed-roof pockets
  draw('##########'.replace(/#/g, '#').slice(0, 9) + '.', '..........', '##.....###'),
];

test('engine_placements (Rust) equals enginePlacements (TS) list for list', () => {
  if (!hasCargo) { console.log('cargo not found: skipped'); return; }
  const b = spawnSync('cargo', ['build', '--release', '--quiet', '--bin', 'engine_gen_dump'], { cwd: CRATE, encoding: 'utf8' });
  expect(b.status, b.stderr).toBe(0);

  const boards: { src: string; rows: number[] }[] = [];
  for (const s of SESSIONS) {
    const dir = `sessions/${s}`;
    if (!existsSync(`${dir}/sim/replay-facts.json`)) throw new Error(`no replay-facts for ${s}`);
    for (const rows of sessionBoards(dir)) boards.push({ src: s, rows });
  }
  for (const rows of randomBoards(1500)) boards.push({ src: 'random', rows });
  for (const rows of HAND) boards.push({ src: 'hand', rows });

  const seen = new Set<string>(), cases: (Case & { src: string })[] = [];
  for (const { src, rows } of boards) {
    const hs = src === 'session' || SESSIONS.includes(src) ? frames(rows, MAXH)
      : Array.from({ length: MAXH - Math.max(height(rows), 1) + 1 }, (_, i) => Math.max(height(rows), 1) + i);
    for (const piece of PIECES) for (const H of hs) {
      const k = `${rows.join(',')}|${piece}|${H}`;
      if (seen.has(k)) continue;
      seen.add(k);
      cases.push({ rows, piece, H, src });
    }
  }

  const t0 = performance.now();
  const ts = cases.map(c => enginePlacements(c.rows, c.piece, c.H));
  const tsMs = performance.now() - t0;

  const input = cases.map(c => `${c.piece} ${c.H} ${c.rows.join(' ')}`).join('\n') + '\n';
  const r = spawnSync(BIN, ['--time'], { input, encoding: 'utf8', maxBuffer: 1 << 30 });
  expect(r.status, r.stderr).toBe(0);
  const lines = r.stdout.split('\n');
  const rustUs = Number(/rust_us (\d+)/.exec(r.stderr)![1]);

  const bad: string[] = [];
  let placements = 0;
  cases.forEach((c, i) => {
    const want = ts[i]!.map(p => p.join(',')).join(';');
    placements += ts[i]!.length;
    if (lines[i] !== want && bad.length < 20) bad.push(`${c.src} ${c.piece} H=${c.H} rows=[${c.rows}]\n  ts:   ${want}\n  rust: ${lines[i]}`);
  });
  const bySrc: Record<string, number> = {};
  for (const c of cases) bySrc[c.src] = (bySrc[c.src] ?? 0) + 1;
  console.log(`cases ${cases.length} (${JSON.stringify(bySrc)}), boards ${boards.length}, placements ${placements}; ` +
    `TS ${tsMs.toFixed(0)} ms, Rust ${(rustUs / 1000).toFixed(1)} ms`);
  expect(bad, bad.join('\n')).toEqual([]);
}, 3_600_000);
