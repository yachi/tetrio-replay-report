/**
 * Which placement made a perfect clear impossible? For every lock of every (round, player) whose
 * board fits inside a 4-row frame, ask the solver (`pc-solver.ts`) whether a PC is still possible
 * with the pieces the round actually dealt (hindsight: the whole sequence, not just the preview).
 *
 *   REPLAY_DIR=sessions/<date> bun pipeline/sim/pc-miss.ts --out <json>
 *
 * A "miss" is a lock i where a PC was possible before it, not after it, the lock itself did not
 * perfect-clear, and no garbage arrived between (garbage arriving is counted separately).
 * Simulator output on the replay-facts timeline: quarantined, like every sim/ artefact.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { placeCells, WIDTH } from './emit-replay.ts';
import { solve, frames, filled, height, setMovegen, type Placement } from './pc-solver.ts';
import { enginePlacements } from './pc-engine-gen.ts';

type Lock = [number, number | number[], number, number, [number, number][], number, number, number];

const argv = process.argv.slice(2);
const dir = process.env.REPLAY_DIR!;
const outPath = argv[argv.indexOf('--out') + 1]!;
const RF = JSON.parse(readFileSync(`${dir}/sim/replay-facts.json`, 'utf8'));

const FULL = (1 << WIDTH) - 1;
const MAXH = Number(process.env.PC_MAXH ?? 6);
const toMasks = (b: (string | null)[][]) => {
  const m = b.map(r => r.reduce((a, c, x) => a | (c != null ? 1 << x : 0), 0));
  let h = m.length; while (h && !m[h - 1]) h--;
  return m.slice(0, h);
};
const hasGarbage = (b: (string | null)[][], H: number) => b.slice(0, H).some(r => r.includes('G'));

function check(rows: number[], cur: string, hold: string, seq: string, ptr: number, memo: Map<string, any>) {
  let unknown = false;
  for (const H of frames(rows, MAXH)) {
    const b = { nodes: 3_000_000 };
    let v;
    try { v = solve(rows, H, cur, hold, seq, ptr, memo, b); }
    catch { unknown = true; continue; }
    if (v.ok === true) return { ok: true as const, H, plan: v.plan };
    if (v.ok === null) unknown = true;
  }
  return unknown ? { ok: null } : { ok: false as const };
}

const out: any[] = [];
const t0 = performance.now();
for (const rd of RF.rounds) {
  for (const P of rd.players) {
    if (!P.admission.ok) continue;
    const seq: string = rd.seq;
    const locks: Lock[] = P.locks;
    const board: (string | null)[][] = Array.from({ length: 40 }, () => new Array(WIDTH).fill(null));
    let cur = seq[0]!, ptr = 1, hold = '';
    const memo = new Map<string, any>();
    const states: any[] = [];
    const tst = locks.findIndex((l, j) => j <= 21 && l[3] === 2 && l[2] === 3);
    const winEnd = tst < 0 ? -1 : tst + 12;
    for (let i = 0; i < locks.length; i++) {
      const lk = locks[i]!;
      // garbage first (the engine's own splice, as decodeTimeline)
      for (const [col, amt] of lk[4]) {
        const rows = Array.from({ length: amt }, () => { const r = new Array<string | null>(WIDTH).fill('G'); r[col] = null; return r; });
        board.splice(0, 0, ...rows); board.splice(40 - amt - 1, amt);
      }
      const pre = toMasks(board);
      const preGrid = board.slice(0, 6).map(r => r.map(c => c ?? '.').join(''));
      const preCur = cur, preHold = hold, prePtr = ptr;
      // the decision
      if (lk[5]) { if (hold === '') { hold = cur; cur = seq[ptr++]!; } else { const t = hold; hold = cur; cur = t; } }
      const piece = cur;
      const cells = placeCells(piece, lk[1]);
      for (const c of cells) board[Math.floor(c / WIDTH)]![c % WIDTH] = piece;
      const full: number[] = [];
      for (let y = 0; y < 40; y++) if (board[y]!.every(v => v != null)) full.push(y);
      for (let k = full.length - 1; k >= 0; k--) { board.splice(full[k]!, 1); board.push(new Array(WIDTH).fill(null)); }
      cur = seq[ptr++]!;
      const pc = board[0]!.every(v => v == null);
      let v: any = null;
      const inWin = tst >= 0 && i > tst && i <= winEnd;
      if (inWin && height(pre) <= MAXH && frames(pre, MAXH).length) v = check(pre, preCur, preHold, seq, prePtr, memo);
      states.push({ i, inWin, preGrid, pre, next: seq.slice(prePtr, prePtr + 5), garbageIn: lk[4].length > 0, cur: preCur, hold: preHold, ptr: prePtr, piece, held: !!lk[5],
                    cells, lines: lk[2], pc, verdict: v ? { ok: v.ok, H: v.H ?? null, plan: v.plan ?? null } : null });
    }
    // misses
    for (let i = 0; i + 1 < states.length; i++) {
      const a = states[i], b = states[i + 1];
      if (a.verdict?.ok !== true || a.pc) continue;
      // state right after lock i, before lock i+1's garbage: recompute if lock i+1 brought garbage
      let after = b.verdict;
      let afterRows = b.pre;
      if (b.garbageIn) {
        // board after lock i without the garbage: rebuild from a.pre + a's cells
        afterRows = null;
      }
      if (after?.ok === true) continue;
      if (b.garbageIn) { a.lostTo = 'garbage'; continue; }
      if (after == null) after = { ok: false };   // board left the 4-row frame
      if (after.ok === null) { a.lostTo = 'unknown'; continue; }
      // re-check "no PC" with the engine's own movegen (adds the 180 rotation)
      const vb = b.verdict ? null : undefined;
      if (height(b.pre) <= MAXH && frames(b.pre, MAXH).length) {
        setMovegen(enginePlacements);
        const e = check(b.pre, b.cur, b.hold, seq, b.ptr, new Map());
        setMovegen(null);
        if (e.ok === true) { a.lostTo = 'engine_disagrees'; a.engine = e; continue; }
        if (e.ok === null) { a.lostTo = 'unknown'; continue; }
      }
      a.lostTo = 'placement';
    }
    // stop the window at the first PC after the TST
    const firstPc = states.findIndex(s => s.pc && s.i > tst);
    const pcLock = firstPc >= 0 ? states[firstPc].i : null;
    out.push({ match: rd.match, round: rd.round, file: rd.file, user: P.user, verified_to: P.prefix.verified_to,
               tst: tst < 0 ? null : tst, pcLock, frames: locks.map(l => l[0]),
               states: states.filter(s => s.inWin || (tst >= 0 && s.i === tst)) });
  }
  console.error(`m${rd.match}r${rd.round + 1} ${Math.round((performance.now() - t0) / 1000)}s`);
}
writeFileSync(outPath, JSON.stringify({ session: RF.session, rounds: out }));
