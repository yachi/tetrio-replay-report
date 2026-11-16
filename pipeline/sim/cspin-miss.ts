/**
 * C-Spin 冇砌: a mid-game hole cold-clear turns into a C-Spin and the player did not.
 *
 *   REPLAY_DIR=sessions/<date> bun pipeline/sim/cspin-miss.ts --windows <cc-input.jsonl>
 *   CC_NODES=40000 COACH_MODE=rollout <cc-coach> < <cc-input.jsonl> > <cc-output.jsonl>
 *   REPLAY_DIR=sessions/<date> bun pipeline/sim/cspin-miss.ts --cc <cc-output.jsonl> \
 *     --out sessions/<date>/sim/cspin-miss-facts.json
 *   REPLAY_DIR=sessions/<date> bun pipeline/sim/cspin-miss.ts --rebuild sessions/<date>/sim/cspin-miss-facts.json
 *
 * The boards are the decision points of `cc-positions.ts` with clutch ON (TETR.IO's default), inside
 * each round's verified prefix. A HOLE on a board is a row with nine filled cells whose empty cell has
 * a filled cell under it and an open column above it. It is STAGE 2 when a side neighbour one row up
 * is empty, that row holds exactly eight filled cells and the cell over the hole is empty: the start
 * of a C-Spin slot with its roof missing. It is STAGE 3 when a full T-spin Triple shaped like one of
 * harddrop's C-Spin boards (`wiki-cspin-boards.json`, as drawn and mirrored) is already reachable
 * through the hole (SRS BFS). A hole is followed lock to lock by its column, its row's cells and its
 * rank among equal rows (so garbage shifting it up keeps it). A WINDOW is opened at the first board
 * where a hole is stage 2, for a hole that appeared after the opener (0-based lock > 21), never
 * reached stage 3, and was later filled or covered by a placement (not by the round or the verified
 * prefix ending). The window runs `K` locks.
 *
 * cold-clear (tools/cc-coach, the pinned rev and patch) plays the window from that board with the
 * round's real queue and the garbage the player really took, lock by lock. Both sides are then read
 * by one CARRIED-CELL rule: follow the hole cell through every line clear and every garbage row; the
 * first placement with a cell on it decides — a T with a full T-spin clearing three is a C-Spin, any
 * other piece fills it. The hole disappearing (its row cleared, or covered over) also decides. A MISS
 * is a window where cold-clear's C-Spin comes and the player's does not.
 *
 * cold-clear's placements up to its decision are committed in the artefact, so the verdicts are
 * re-derived from the artefact and the replay alone (`--rebuild`, `cspin-miss.test.ts`); cold-clear
 * itself is only needed to make new windows. Its placements are a bot's, not a player's: the artefact
 * says `report_eligible: false`, nothing here enters a count, a claim or a badge.
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { loadCases } from './verified-prefix.ts';
import { extractPositions, H } from './cc-positions.ts';
import { detectTSpin } from './sim.ts';
import { tryMove, tryRotate, hardDrop, getPieceCells } from './vendor/core/srs.ts';

export const K = 14;
export const OPENER = 21;
export const GARBAGE_CAP = 8;
export const CC = { rev: '279edd7', nodes: 40000, mode: 'rollout' };
export const HASHED = ['pipeline/sim/cspin-miss.ts', 'pipeline/sim/cc-positions.ts', 'pipeline/sim/wiki-cspin-boards.json',
  'tools/cc-coach/cc-coach.rs', 'tools/cc-coach/cold-clear-coach.patch'];

const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');
type Cell = { row: number; col: number };
type B = (string | null)[][];

// ---- the C-Spin slot shapes -------------------------------------------------------------------
function mask(filled: (r: number, c: number) => boolean, cells: Cell[]) {
  const rs = cells.map(c => c.row), cs = cells.map(c => c.col);
  const own = new Set(cells.map(c => `${c.row}:${c.col}`)); const out: string[] = [];
  for (let r = Math.min(...rs) - 2; r <= Math.max(...rs) + 1; r++) {
    let l = '';
    for (let c = Math.min(...cs) - 1; c <= Math.max(...cs) + 1; c++) l += own.has(`${r}:${c}`) ? '.' : filled(r, c) ? '#' : '.';
    out.push(l);
  }
  return out.join('/');
}
const WIKI = new Set<string>();
for (const o of JSON.parse(readFileSync(new URL('./wiki-cspin-boards.json', import.meta.url), 'utf8'))) {
  if (o.lines !== 3) continue;
  const m = mask((r, c) => {
    if (c < 0 || c > 9) return true;
    const row = o.rows[r]; if (row === undefined) return r >= o.rows.length;
    return row[c] !== '.' && row[c] !== 'P';
  }, o.piece);
  WIKI.add(m); WIKI.add(m.split('/').map((l: string) => [...l].reverse().join('')).join('/'));
}

/** Every full T-spin Triple a T can reach by SRS moves from spawn (cells, deduplicated). */
export function tsts(board: B): Cell[][] {
  const res: Cell[][] = []; const seen = new Set<string>(); const out = new Set<string>();
  const q: any[] = [{ p: { type: 'T', rotation: 0, col: 3, row: 18 }, rot: false, kick: false }]; seen.add('0:3:18:0');
  for (let h = 0; h < q.length && h < 40000; h++) {
    const { p, rot, kick } = q[h];
    const d = hardDrop(board as any, p);
    if (d.row === p.row && rot && detectTSpin(board as any, d, true, kick) === 'full') {
      const cells = getPieceCells(d); const set = new Set(cells.map(c => `${c.row}:${c.col}`));
      let lines = 0;
      for (let r = 0; r < H; r++) if (board[r].every((x, c) => x !== null || set.has(`${r}:${c}`))) lines++;
      const key = cells.map(c => `${c.row}:${c.col}`).sort().join(',');
      if (lines === 3 && !out.has(key)) { out.add(key); res.push(cells); }
    }
    for (const [n, isRot] of [[tryMove(board as any, p, -1, 0), false], [tryMove(board as any, p, 1, 0), false],
      [tryMove(board as any, p, 0, 1), false], [tryRotate(board as any, p, 1), true], [tryRotate(board as any, p, -1), true]] as any) {
      if (!n) continue;
      const k = `${n.rotation}:${n.col}:${n.row}:${isRot ? 1 : 0}`;
      if (seen.has(k)) continue; seen.add(k);
      q.push({ p: n, rot: isRot, kick: isRot && (n.col !== p.col || n.row !== p.row) });
    }
  }
  return res;
}
const cnt = (row: (string | null)[]) => row.reduce((a, x) => a + (x !== null ? 1 : 0), 0);
const maybe = (counts: number[]) => { for (let r = 0; r + 2 < counts.length; r++) if (counts[r] === 9 && counts[r + 1] === 8 && counts[r + 2] === 9) return true; return false; };
/** The reachable full TSTs whose surroundings are one of harddrop's C-Spin boards. */
export function slots(board: B): Cell[][] {
  if (!maybe(board.map(cnt))) return [];
  const filled = (r: number, c: number) => c < 0 || c > 9 || r >= H ? true : r < 0 ? false : board[r][c] !== null;
  return tsts(board).filter(t => WIKI.has(mask(filled, t)));
}
export const toBoard = (f: string[]): B => {
  const rows = f.length < H ? [...Array(H - f.length).fill('.'.repeat(10)), ...f] : f;
  return rows.map(s => [...s].map(ch => ch === '.' ? null : ch));
};
const isF = (b: B, r: number, c: number) => c < 0 || c > 9 || r >= H ? true : r < 0 ? false : b[r][c] !== null;

export type Hole = { key: string; r: number; c: number; stage: 1 | 2 | 3; garbage: boolean };
/** The holes of one board (see the header for the stages). */
export function holes(b: B, opts: { noSlotCheck?: boolean } = {}): Hole[] {
  const counts = b.map(cnt); const res: Hole[] = []; let sl: Cell[][] | null = null;
  const rank = new Map<string, number>();
  for (let r = 1; r < H; r++) {
    if (counts[r] !== 9) continue;
    const c = b[r].findIndex(x => x === null);
    if (!isF(b, r + 1, c)) continue;
    let open = true; for (let i = 0; i < r; i++) if (b[i][c] !== null) { open = false; break; }
    let A = false, Bst = false;
    if (open) for (const d of [-1, 1]) {
      const nc = c + d; if (nc < 0 || nc > 9) continue;
      if (b[r - 1][nc] === null) { A = true; if (counts[r - 1] === 8 && b[r - 1][c] === null) Bst = true; }
    }
    let C = false;
    if (!opts.noSlotCheck && maybe(counts.slice(Math.max(0, r - 2), r + 1))) {
      if (sl === null) sl = slots(b);
      C = sl.some(t => t.some(x => x.row === r && x.col === c));
    }
    if (!A && !C) continue;
    const rs = b[r].map(x => x ?? '.').join('');
    const k0 = `${c}|${rs}`; const n = rank.get(k0) ?? 0; rank.set(k0, n + 1);
    res.push({ key: `${k0}|${n}`, r, c, stage: C ? 3 : Bst ? 2 : 1, garbage: rs.includes('G') });
  }
  return res;
}

// ---- the carried cell -----------------------------------------------------------------------
const norm = (rows: string[]) => rows.map(r => r.replace(/[^.]/g, '#'));
const pad = (f: string[]) => [...Array(H - f.length).fill('.'.repeat(10)), ...f];
const trim = (f: string[]) => { let i = 0; while (i < f.length - 1 && f[i] === '.'.repeat(10)) i++; return f.slice(i); };
/** Lock `cells` ([x, y] top-index) into a 40-row board and clear: the board and the cleared rows. */
export function lockClear(board: string[], cells: number[][], mark: string): { after: string[]; full: number[] } {
  const b = board.map(r => [...r]);
  for (const [x, y] of cells) b[y][x] = mark;
  const full: number[] = []; b.forEach((r, y) => { if (r.every(ch => ch !== '.')) full.push(y); });
  const kept = b.filter((_, y) => !full.includes(y)).map(r => r.join(''));
  return { after: [...Array(full.length).fill('.'.repeat(10)), ...kept], full };
}
/** Where the carried cell's row goes: null if its row was cleared. */
const carryRow = (r: number, full: number[], g: number) => full.includes(r) ? null : r + full.filter(y => y > r).length - g;

export type Verdict = { fire: number | null; why: string | null; at: number | null };
/** cold-clear's side: its committed steps, garbage rows rebuilt from their hole columns. */
export function ccVerdict(field: string[], hole: [number, number], steps: any[], check?: (j: number, board: string[]) => void,
  opts: { anySpin?: boolean } = {}): Verdict & { boards: string[][] } {
  let [r, c] = hole; let board = pad(field); const boards: string[][] = [];
  for (let j = 0; j < steps.length; j++) {
    const s = steps[j];
    if (s.dead) return { fire: null, why: 'dead', at: j, boards };
    if (s.cells.some(([x, y]: number[]) => x === c && y === r)) {
      if (s.piece === 'T' && (opts.anySpin || s.tspin === 'Full') && s.lines === 3) return { fire: j, why: null, at: j, boards };
      return { fire: null, why: `filled by ${s.piece}`, at: j, boards };
    }
    const { after, full } = lockClear(board, s.cells, s.piece);
    const g = s.garbage_cols.length;
    const next = [...after.slice(g), ...s.garbage_cols.map((gc: number) => 'G'.repeat(gc) + '.' + 'G'.repeat(9 - gc))];
    check?.(j, next);
    boards.push(next);
    const nr = carryRow(r, full, g);
    if (nr === null || nr < 0) return { fire: null, why: 'hole gone', at: j, boards };
    r = nr; board = next;
    if (board[r][c] !== '.') return { fire: null, why: 'hole gone', at: j, boards };
  }
  return { fire: null, why: 'window ended', at: null, boards };
}
/** The player's side, over the recorded decision points (garbage found by matching the next board). */
export function humanVerdict(ps: any[], k: number, hole: [number, number], opts: { anySpin?: boolean } = {}): Verdict {
  let [r, c] = hole;
  for (let j = 0; j < K; j++) {
    const p = ps[k + j], pl = p.played;
    if (pl.cells.some(([x, y]: number[]) => x === c && y === r)) {
      if (pl.piece === 'T' && (opts.anySpin || pl.spin === 'normal') && pl.lines === 3) return { fire: j, why: null, at: j };
      return { fire: null, why: `filled by ${pl.piece}`, at: j };
    }
    const nxt = ps[k + j + 1];
    if (!nxt) return { fire: null, why: 'round ended', at: j };
    const { after, full } = lockClear(p.field, pl.cells, '#');
    const nf = norm(nxt.field); let g = 0;
    while (g <= 12 && norm(after.slice(g)).join('/') !== nf.slice(0, H - g).join('/')) g++;
    if (g > 12) throw new Error(`board mismatch at ${p.id}`);
    const nr = carryRow(r, full, g);
    if (nr === null || nr < 0 || nxt.field[nr][c] !== '.') return { fire: null, why: 'hole gone', at: j };
    r = nr;
  }
  return { fire: null, why: 'window ended', at: null };
}

// ---- windows ---------------------------------------------------------------------------------
export type Win = { id: string; file: string; round: number; user: string; lock: number; hole: [number, number];
  garbage: boolean; start: number };
/** Every window of one round's decision points, and the episodes skipped for a short round. */
export function windows(ps: any[], meta: any, opts: { noSlotCheck?: boolean; openerAt?: number } = {}): { wins: Win[]; short: number } {
  const last = ps.findLastIndex((p: any) => p.verified);
  const alive = new Map<string, any>(); const done: any[] = [];
  for (let j = 0; j <= last; j++) {
    const hs = holes(toBoard(ps[j].field), opts); const now = new Map(hs.map(h => [h.key, h]));
    for (const [key, e] of alive) {
      if (now.has(key)) continue;
      const pl = ps[j - 1].played; const inCol = pl.cells.some(([x]: number[]) => x === e.c);
      e.cause = pl.piece === 'T' && pl.spin !== 'none' && inCol ? 'tspin' : inCol ? 'filled' : 'blocked';
      done.push(e); alive.delete(key);
    }
    for (const h of hs) {
      const e = alive.get(h.key);
      if (e) { e.maxStage = Math.max(e.maxStage, h.stage); if (h.stage === 2 && e.k === undefined) { e.k = j; e.r = h.r; } }
      else alive.set(h.key, { c: h.c, start: j, garbage: h.garbage, maxStage: h.stage, ...(h.stage === 2 ? { k: j, r: h.r } : {}) });
    }
  }
  const wins: Win[] = []; let short = 0;
  for (const e of done) {
    if (e.start <= (opts.openerAt ?? OPENER) || e.maxStage !== 2 || e.cause === 'tspin') continue;
    if (e.k + K >= ps.length) { short++; continue; }
    wins.push({ id: `${meta.file}/${meta.round}/${meta.user}/${e.k}/${e.c}`, file: meta.file, round: meta.round, user: meta.user,
      lock: e.k, hole: [e.r, e.c], garbage: e.garbage, start: e.start });
  }
  wins.sort((a, b) => a.lock - b.lock || a.hole[1] - b.hole[1]);
  return { wins, short };
}
/** cold-clear's input for one window (the coach's rollout format). */
export function ccInput(w: Win, ps: any[], meta: any): any {
  const st: any = { ...ps[w.lock] }; delete st.played;
  const dec = ps.slice(w.lock, w.lock + K);
  const cur = st.seqIndex, nn = st.next.length;
  st.id = w.id; st.future = [...meta.seq.slice(cur + 1 + nn, cur + 1 + nn + K + 2)];
  st.k = K; st.garbage_cap = GARBAGE_CAP; st.record_fields = true;
  st.garbage_schedule = dec.map((p: any) => p.played.tanks);
  st.incoming_schedule = dec.map((p: any) => p.incoming);
  st.player_window = dec.map((p: any) => ({ piece: p.played.piece, lines: p.played.lines, spin: p.played.spin, cells: p.played.cells }));
  return st;
}
/** At each of the player's T locks before their decision: was a C-Spin already ready? */
export function readyAtT(ps: any[], k: number, upto: number): number[] {
  const out: number[] = [];
  for (let j = 0; j <= upto && j < K; j++) if (ps[k + j].played.piece === 'T' && slots(toBoard(ps[k + j].field)).length) out.push(j);
  return out;
}

// ---- the artefact ----------------------------------------------------------------------------
type Round = { ps: any[]; meta: any };
export function rounds(dir: string): Round[] {
  process.env.REPLAY_DIR = dir;
  return loadCases(dir).map((c: any) => { const { positions, meta } = extractPositions(c, { clutch: true }); return { ps: positions, meta }; });
}
const packStep = (s: any) => s.dead ? { dead: true } : { piece: s.piece, cells: s.cells, hold: s.hold, tspin: s.tspin, lines: s.lines, garbage_cols: s.garbage_cols };

export function build(dir: string, rs: Round[], cc: Map<string, any[]>, opts: { checkFields?: boolean } = {}): any {
  const session = dir.split('/').filter(Boolean).pop()!;
  const out: any[] = []; const cases: any[] = []; let nWin = 0, short = 0;
  const tally: Record<string, any> = {};
  for (const { ps, meta } of rs) {
    const w = windows(ps, meta); short += w.short;
    for (const win of w.wins) {
      nWin++;
      const raw = cc.get(win.id);
      if (!raw) throw new Error(`no cold-clear output for ${win.id}`);
      const field = ps[win.lock].field;
      const v = ccVerdict(field, win.hole, raw, opts.checkFields ? (j, b) => {
        if (norm(b).join('/') !== norm(pad(raw[j].field)).join('/')) throw new Error(`rebuilt board != cold-clear's at ${win.id} step ${j}`);
      } : undefined);
      const end = v.at ?? K - 1;
      const steps = raw.slice(0, Math.min(raw.length, end + 1)).map(packStep);
      const hu = humanVerdict(ps, win.lock, win.hole);
      const t = tally[win.user] ??= { windows: 0, cc: 0, miss: 0, both: 0, human_only: 0 };
      t.windows++; if (v.fire !== null) t.cc++;
      const kind = v.fire !== null ? (hu.fire !== null ? 'both' : 'miss') : hu.fire !== null ? 'human_only' : null;
      if (kind) t[kind]++;
      const rec: any = { id: win.id, lock: win.lock, hole: win.hole, garbage: win.garbage, cc: { fire: v.fire, why: v.why, at: v.at, steps },
        human: hu };
      if (kind === 'miss') {
        rec.ready_at_t = readyAtT(ps, win.lock, hu.fire ?? K - 1);
        const st = ps[win.lock];
        cases.push({ id: win.id, file: win.file, round: win.round, user: win.user, lock: win.lock, hole: win.hole, garbage: win.garbage,
          field: trim(st.field), current: st.current, hold: st.hold, next: st.next,
          cc_boards: v.boards.map(trim), human: ps.slice(win.lock, win.lock + K).map((p: any) => ({ piece: p.played.piece, cells: p.played.cells, spin: p.played.spin, lines: p.played.lines })),
          human_boards: ps.slice(win.lock + 1, win.lock + K + 1).map((p: any) => trim(p.field)) });
      }
      out.push(rec);
    }
  }
  const md5s: Record<string, string> = {};
  for (const f of HASHED) md5s[f] = md5(readFileSync(f));
  const ttrm: Record<string, string> = {};
  for (const r of rs) ttrm[r.meta.file] ??= md5(readFileSync(`${dir}/${r.meta.file}`));
  return {
    schema: 'cspin-miss/1', session, report_eligible: false,
    note: "Simulator and bot output. cold-clear's placements are a bot's, not a player's; nothing here is in a count, a claim or a badge.",
    rules: { window_locks: K, opener_locks: OPENER, garbage_cap: GARBAGE_CAP, clutch: true, cold_clear: CC,
      hole: 'a row with 9 filled cells, a filled cell under its empty cell and the column open above it',
      stage2: 'a side neighbour one row up is empty, that row holds 8 filled cells and the cell over the hole is empty',
      stage3: "a full TST through the hole, reachable by SRS BFS, matching one of harddrop's C-Spin boards (as drawn and mirrored)",
      window: 'opened at the first stage-2 board, for a hole that appeared after the opener, never reached stage 3 and was filled or covered by a placement',
      verdict: 'the hole cell is carried through every clear and garbage row; the first placement on it decides: a T with a full T-spin clearing 3 is a C-Spin' },
    md5: { files: md5s, ttrm },
    counts: { windows: nWin, skipped_short: short, by_player: tally },
    cases, windows: out,
  };
}
export function stringify(a: any): string {
  const { windows: ws, cases, ...head } = a;
  const body = JSON.stringify(head, null, 1).replace(/\n}$/, '');
  return `${body},\n "cases": [\n${cases.map((c: any) => '  ' + JSON.stringify(c)).join(',\n')}\n ],\n "windows": [\n${ws.map((w: any) => '  ' + JSON.stringify(w)).join(',\n')}\n ]\n}\n`;
}
/** cold-clear's committed steps out of an artefact, by window id. */
export const committedSteps = (a: any) => new Map<string, any[]>(a.windows.map((w: any) => [w.id, w.cc.steps]));

if (import.meta.main) {
  const dir = process.env.REPLAY_DIR!; const arg = (n: string) => { const i = process.argv.indexOf(n); return i < 0 ? null : process.argv[i + 1]; };
  if (!dir) throw new Error('REPLAY_DIR is required');
  const rs = rounds(dir);
  if (arg('--windows')) {
    const lines: string[] = [];
    for (const r of rs) for (const w of windows(r.ps, r.meta).wins) lines.push(JSON.stringify(ccInput(w, r.ps, r.meta)));
    writeFileSync(arg('--windows')!, lines.join('\n') + '\n');
    console.error(`${lines.length} windows`);
  } else if (arg('--cc')) {
    const cc = new Map<string, any[]>();
    for (const l of readFileSync(arg('--cc')!, 'utf8').split('\n')) if (l.trim()) { const o = JSON.parse(l); cc.set(o.id, o.steps); }
    const a = build(dir, rs, cc, { checkFields: true });
    writeFileSync(arg('--out')!, stringify(a));
    console.error(JSON.stringify(a.counts));
  } else if (arg('--rebuild')) {
    const path = arg('--rebuild')!; const old = readFileSync(path, 'utf8');
    const s = stringify(build(dir, rs, committedSteps(JSON.parse(old))));
    if (s !== old) { console.error(`${path}: rebuild differs`); process.exit(1); }
    console.error(`${path}: rebuilt byte for byte`);
  } else throw new Error('one of --windows, --cc, --rebuild');
}
