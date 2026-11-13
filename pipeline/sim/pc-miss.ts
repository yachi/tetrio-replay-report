/**
 * Which placement made a perfect clear impossible?
 *
 *   REPLAY_DIR=sessions/<date> bun pipeline/sim/pc-miss.ts --out sessions/<date>/sim/pc-miss-facts.json
 *
 * Two kinds of WINDOW per (round, player), each at most `SPAN` locks long and ending at the first
 * Perfect Clear inside it:
 *   - `tst`: after the opener's T-spin Triple (a full spin clearing 3 at lock <= 21, 0-based), where
 *     the opener routes draw their 8-line PC;
 *   - `pc`:  after each Perfect Clear (the next PC, a DPC or a second PC).
 * Inside a window every board at most `MAXH` rows tall is handed to the solver (`pc-solver.ts`),
 * which answers with the round's own dealt sequence (hindsight). A MISS is a lock i where a PC was
 * possible before it and not after it, lock i did not itself perfect-clear, and lock i+1 brought no
 * garbage (garbage is reported separately). Every "not after" is re-checked with the engine's own
 * movegen (`pc-engine-gen.ts`, which has 180); a miss is then marked `in_preview` when a PC existed
 * using only the current piece, the hold and the five pieces of the preview, and `verified` when
 * lock i+1 is inside the round's verified prefix.
 *
 * A `pc`-window miss is a DPC miss and is reported on a different footing (`dpcReported`): in hindsight,
 * when the next lock is inside the split-tolerant verified prefix (`resumedIndex`).
 *
 * A `placement` miss that is `in_preview` and `verified` is a REPORTED miss and carries a `category`
 * (first that applies): `hole` the placement covered an empty cell; `over` the stack after it is
 * taller than the frame the solver's PC used; `hold` the solver's first piece is not the piece placed
 * (play another piece, through hold or by order); `spot` the same piece, somewhere else.
 *
 * Simulator output on the replay-facts timeline: quarantined, like every sim/ artefact — no claim
 * id, no badge, no figure in any count. One run of the 22 sessions took about 3.5 CPU-hours, so the
 * per-session artefact is committed and `pc-miss.test.ts` rebuilds the shortest session byte for byte.
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { placeCells, WIDTH } from './emit-replay.ts';
import { solve, frames, height, setMovegen, type Placement } from './pc-solver.ts';
import { enginePlacements } from './pc-engine-gen.ts';
import { matchesIgeY } from './ige-y-oracle.ts';

type Lock = [number, number | number[], number, number, [number, number][], number, number, number];

export const MAXH = 6;
export const SPAN = 12;
export const PREVIEW = 5;
const NODES = 3_000_000;
/** The files whose md5 the artefact records. Imports from emit-replay.ts / route-demos.ts are not
 *  hashed (an edit there would stale every artefact for a 3.5-hour rerun); the byte rebuild of one
 *  session in pc-miss.test.ts is what catches a behaviour change through them. */
export const HASHED = ['pipeline/sim/pc-miss.ts', 'pipeline/sim/pc-solver.ts', 'pipeline/sim/pc-engine-gen.ts'];

const md5 = (p: string) => createHash('md5').update(readFileSync(p)).digest('hex');
const md5Files = (ps: string[]) => { const h = createHash('md5'); for (const p of ps) h.update(readFileSync(p)); return h.digest('hex'); };

const toMasks = (b: (string | null)[][]) => {
  const m = b.map(r => r.reduce((a, c, x) => a | (c != null ? 1 << x : 0), 0));
  let h = m.length; while (h && !m[h - 1]) h--;
  return m.slice(0, h);
};

/** Covered empty cells: an empty cell with a filled cell above it in the same column. */
export function holes(g: string[]): number {
  let h = 0;
  for (let x = 0; x < WIDTH; x++) {
    let seen = false;
    for (let y = g.length - 1; y >= 0; y--) {
      if (g[y]![x] !== '.') seen = true;
      else if (seen) h++;
    }
  }
  return h;
}
export const stackHeight = (g: string[]) => g.reduce((a, r, i) => (/[^.]/.test(r) ? i + 1 : a), 0);

/** The board (rows bottom-up, '.' empty) with the placement's cells drawn in, before any clear. */
export function withPlacement(grid: string[], cells: number[], piece: string): string[] {
  const g = grid.map(r => [...r]);
  for (const c of cells) {
    const y = Math.floor(c / WIDTH), x = c % WIDTH;
    while (g.length <= y) g.push([...'.'.repeat(WIDTH)]);
    g[y]![x] = piece;
  }
  return g.map(r => r.join(''));
}

export function category(st: { grid: string[]; cells: number[]; piece: string }, planH: number, firstPiece: string) {
  const g = withPlacement(st.grid, st.cells, st.piece);
  if (holes(g) > holes(st.grid)) return 'hole';
  if (stackHeight(g) > planH) return 'over';
  return firstPiece !== st.piece ? 'hold' : 'spot';
}

/** The opponent's recorded incoming garbage aimed at `user` in one round: the attacks the verified
 *  prefix compares against (`verified-prefix.ts` loadCases' `truth`, read the same way). */
export function truthFor(ttrm: any, round: number, user: string): { frame: number; amt: number; y: number }[] {
  const rnd = ttrm.replay.rounds[round];
  const me = rnd.find((p: any) => p.username === user), other = rnd.find((p: any) => p.username !== user);
  return other.replay.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction'
    && e.data.data?.type === 'garbage' && e.data.data.gameid === me.replay.options.gameid)
    .map((e: any) => ({ frame: e.data.data.frame ?? e.frame, amt: e.data.data.amt, y: e.data.data.y }))
    .sort((a: any, b: any) => a.frame - b.frame);
}

export interface SentLock { frame: number; sent: number; lines: number; rows: number[]; pc: boolean }

/**
 * The verified-prefix walk (`verifiedBoundary`, frame+amount+row) over this timeline's own attacks, with
 * ONE tolerance: a Perfect Clear the engine sends as one attack may match the game's packets at that
 * frame when they sum to it, each on the cleared rows (the game sends the clear and its All Clear bonus
 * separately, e.g. 1 + 10 where the engine sends 11). `split: false` is the plain walk, which must
 * reproduce replay-facts' `verified_to` (pc-miss.test.ts checks it on every player). Returns the index
 * of the last lock at or before the last matched attack (-1 if none).
 */
export function resumedIndex(locks: SentLock[], truth: { frame: number; amt: number; y: number }[], split = true): number {
  let vf = -1, j = 0;
  for (const a of locks) {
    if (a.sent <= 0) continue;
    const b = truth[j];
    if (!b || Math.abs(a.frame - b.frame) > 25) break;
    const rowOk = (y: number) => a.lines === 0 || matchesIgeY(a.rows, a.lines, y);
    if (a.sent === b.amt && rowOk(b.y)) { j++; vf = a.frame; continue; }
    if (!split || !a.pc) break;
    let k = j, sum = 0;
    while (k < truth.length && truth[k]!.frame === b.frame && sum < a.sent && rowOk(truth[k]!.y)) sum += truth[k++]!.amt;
    if (k - j < 2 || sum !== a.sent) break;
    j = k; vf = a.frame;
  }
  let idx = -1;
  for (let k = 0; k < locks.length; k++) if (locks[k]!.frame <= vf) idx = k;
  return idx;
}

type V = { ok: true; H: number; plan: Placement[] } | { ok: false } | { ok: null };
function check(rows: number[], cur: string, hold: string, seq: string, ptr: number, memo: Map<string, any>): V {
  let unknown = false;
  for (const H of frames(rows, MAXH)) {
    let v;
    try { v = solve(rows, H, cur, hold, seq, ptr, memo, { nodes: NODES }); }
    catch { unknown = true; continue; }
    if (v.ok === true) return { ok: true, H, plan: v.plan };
    if (v.ok === null) unknown = true;
  }
  return unknown ? { ok: null } : { ok: false };
}
/** A DPC miss (a `pc` window: after a Perfect Clear) is reported in HINDSIGHT — a PC after a PC
 *  needs about 15 pieces and the preview shows 7, so `in_preview` almost never holds there — when its
 *  next lock is inside the split-tolerant verified prefix (`resumedIndex`). */
export const dpcReported = (kind: string, m: any) => kind === 'pc' && m.lost_to === 'placement' && m.verified_resumed === true;
const fits = (rows: number[]) => height(rows) <= MAXH && frames(rows, MAXH).length > 0;

export function build(dir: string, log: (s: string) => void = () => {}) {
  const RF = JSON.parse(readFileSync(`${dir}/sim/replay-facts.json`, 'utf8'));
  const ttrms = new Map<string, any>();
  const out: any[] = [];
  for (const rd of RF.rounds) {
    for (const P of rd.players) {
      if (!P.admission.ok) continue;
      const seq: string = rd.seq;
      const locks: Lock[] = P.locks;
      const board: (string | null)[][] = Array.from({ length: 40 }, () => new Array(WIDTH).fill(null));
      let cur = seq[0]!, ptr = 1, hold = '';
      const st: any[] = [];
      const sent: SentLock[] = [];
      let frame = 0;
      for (let i = 0; i < locks.length; i++) {
        const lk = locks[i]!;
        for (const [col, amt] of lk[4]) {
          const rows = Array.from({ length: amt }, () => { const r = new Array<string | null>(WIDTH).fill('G'); r[col] = null; return r; });
          board.splice(0, 0, ...rows); board.splice(40 - amt - 1, amt);
        }
        const pre = toMasks(board);
        const grid = board.slice(0, MAXH).map(r => r.map(c => c ?? '.').join(''));
        const s: any = { i, pre, grid, cur, hold, ptr, garbageIn: lk[4].length > 0, held: !!lk[5], lines: lk[2], spin: lk[3] };
        if (lk[5]) { if (hold === '') { hold = cur; cur = seq[ptr++]!; } else { const t = hold; hold = cur; cur = t; } }
        s.piece = cur;
        s.cells = placeCells(cur, lk[1]);
        for (const c of s.cells) board[Math.floor(c / WIDTH)]![c % WIDTH] = cur;
        const full: number[] = [];
        for (let y = 0; y < 40; y++) if (board[y]!.every(v => v != null)) full.push(y);
        for (let k = full.length - 1; k >= 0; k--) { board.splice(full[k]!, 1); board.push(new Array(WIDTH).fill(null)); }
        cur = seq[ptr++]!;
        s.pc = board[0]!.every(v => v == null);
        st.push(s);
        frame += lk[0];
        sent.push({ frame, sent: lk[7], lines: lk[2], rows: full.map(y => 39 - y), pc: s.pc });
      }
      if (!ttrms.has(rd.file)) ttrms.set(rd.file, JSON.parse(readFileSync(`${dir}/${rd.file}`, 'utf8')));
      const truth = truthFor(ttrms.get(rd.file), rd.round, P.user);
      const plain = resumedIndex(sent, truth, false);
      if (plain !== P.prefix.verified_to)
        throw new Error(`${rd.file} r${rd.round} ${P.user}: plain walk ${plain} != verified_to ${P.prefix.verified_to}`);
      const resumed = resumedIndex(sent, truth);
      const wins: { kind: string; start: number; end: number }[] = [];
      const tst = st.findIndex(s => s.i <= 21 && s.spin === 2 && s.lines === 3);
      const pcs = st.filter(s => s.pc).map(s => s.i);
      const endAt = (start: number) => { const p = pcs.find(x => x > start); return Math.min(p ?? Infinity, start + SPAN, st.length - 1); };
      if (tst >= 0) wins.push({ kind: 'tst', start: tst, end: endAt(tst) });
      for (const p of pcs) if (p + 1 < st.length) wins.push({ kind: 'pc', start: p, end: endAt(p) });
      const memo = new Map<string, any>();
      const verdict = (s: any): V | null => {
        if (s.v !== undefined) return s.v;
        s.v = fits(s.pre) ? check(s.pre, s.cur, s.hold, seq, s.ptr, memo) : null;
        return s.v;
      };
      const verified = P.prefix.verified_to;
      const rw: any[] = [];
      for (const w of wins) {
        const ev: any[] = [];
        for (let i = w.start + 1; i <= w.end; i++) ev.push(verdict(st[i]));
        const pcLock = st[w.end]!.pc && w.end > w.start ? w.end : null;
        const misses: any[] = [];
        for (let i = w.start + 1; i < w.end; i++) {
          const a = st[i], b = st[i + 1];
          if (a.v?.ok !== true || a.pc || b.v?.ok === true) continue;
          const m: any = { i, verified: i + 1 < verified, verified_resumed: i + 1 < resumed };
          if (b.garbageIn) m.lost_to = 'garbage';
          else if (b.v?.ok === null) m.lost_to = 'unknown';
          else {
            let e: V = { ok: false };
            if (fits(b.pre)) { setMovegen(enginePlacements); e = check(b.pre, b.cur, b.hold, seq, b.ptr, new Map()); setMovegen(null); }
            m.lost_to = e.ok === true ? 'engine_disagrees' : e.ok === null ? 'unknown' : 'placement';
          }
          if (m.lost_to === 'placement') {
            const vis = check(a.pre, a.cur, a.hold, seq.slice(0, a.ptr + PREVIEW), a.ptr, new Map());
            m.in_preview = vis.ok === true;
            m.state = { grid: a.grid, cur: a.cur, hold: a.hold, next: seq.slice(a.ptr, a.ptr + PREVIEW), piece: a.piece, held: a.held, cells: a.cells, lines: a.lines };
            m.after = b.grid;
            const use = (vis.ok === true ? vis : a.v) as { H: number; plan: Placement[] };
            m.plan = use.plan;
            m.plan_H = use.H;
            // a hindsight plan uses pieces past the preview: carry them, so the plan can be dealt
            if (!m.in_preview) m.state.later = seq.slice(a.ptr + PREVIEW, a.ptr + PREVIEW + use.plan.length);
            if ((m.in_preview && m.verified) || dpcReported(w.kind, m)) m.category = category(m.state, m.plan_H, m.plan[0].piece);
          }
          misses.push(m);
        }
        const evaluated = ev.filter(v => v != null).length;
        const outcome = pcLock != null ? 'pc'
          : misses.some(m => m.lost_to === 'placement') ? 'lost_placement'
          : misses.length ? 'lost_other'
          : !ev.some(v => v?.ok === true) ? (evaluated ? 'never' : 'not_evaluated') : 'possible_to_end';
        rw.push({ ...w, pcLock, outcome, misses });
      }
      out.push({ match: rd.match, round: rd.round, file: rd.file, user: P.user, verified_to: verified, verified_resumed_to: resumed, windows: rw });
    }
    log(`m${rd.match}r${rd.round + 1}`);
  }
  return {
    schema: 'pc-miss-facts/1',
    session: RF.session,
    report_eligible: false,
    not_eligible_because: ['one solver over one simulator board: which placement lost the Perfect Clear has no second implementation'],
    rule: 'a placement miss: a PC was possible before the lock (hindsight, the round\'s dealt sequence, frame <= '
      + `${MAXH} rows) and not after it (re-checked with the engine's own movegen, 180 included), the lock did not `
      + 'itself perfect-clear and the next lock brought no garbage. Reported when in_preview (a PC existed using only '
      + `the current piece, the hold and the ${PREVIEW}-piece preview) and verified (the next lock is inside the verified prefix).`,
    dpc_rule: 'a DPC miss: a placement miss inside a pc window (the locks after a Perfect Clear), reported in '
      + 'HINDSIGHT (the PC used pieces the preview had not shown yet; in_preview says when it did not need to) '
      + 'when verified_resumed: the next lock is inside the verified prefix re-walked with one tolerance, a '
      + 'Perfect Clear the engine sends as one attack matching the game\'s packets at that frame when they sum '
      + 'to it (the game sends the clear and its All Clear bonus apart). verified_resumed_to is that walk\'s '
      + 'last lock; without the tolerance the walk reproduces verified_to on every player.',
    categories: {
      hole: 'the placement covered an empty cell',
      over: 'the stack after the placement is taller than the frame of the solver\'s PC',
      hold: 'the solver\'s first piece is not the piece placed',
      spot: 'the same piece, placed somewhere else',
    },
    caveat: 'a PC being possible does not mean the player was building one',
    maxh: MAXH, span: SPAN, preview: PREVIEW, nodes: NODES,
    md5: { replay_facts: md5(`${dir}/sim/replay-facts.json`), ttrm: md5Files([...ttrms.keys()].sort().map(f => `${dir}/${f}`)), ...Object.fromEntries(HASHED.map(p => [p, md5(p)])) },
    rounds: out,
  };
}

export const serialise = (x: unknown) => JSON.stringify(x, null, 1) + '\n';

if (import.meta.main) {
  const outIx = process.argv.indexOf('--out');
  const t0 = performance.now();
  const res = build(process.env.REPLAY_DIR!, s => console.error(`${s} ${Math.round((performance.now() - t0) / 1000)}s`));
  if (outIx > 0) writeFileSync(process.argv[outIx + 1]!, serialise(res));
}
