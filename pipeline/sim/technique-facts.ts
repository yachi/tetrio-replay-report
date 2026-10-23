/**
 * The shared TECHNIQUE MATCHER: for one shiwehi.com mid-game technique page (STSD, …), every scored
 * T-spin in the corpus at which the page's local shape stood, over every session at once. The
 * technique-specific part is a `TechniqueProfile` (`technique-profile.ts`) plus the technique's gated
 * transcription (`*-technique.json`); every RULE is here, once.
 *
 *   bun pipeline/sim/emit-technique-facts.ts --technique stsd --out analysis/stsd-facts.json
 *
 * WHY THIS IS NOT A ROUTE PAGE. `route-facts.ts` compares WHOLE boards (bottom-aligned, at most 8
 * rows) at fixed lock counts from an empty board, behind a bag-1 gate, on a digest truncated at the
 * profile's `snapshotLocks`. A mid-game shape sits on a partial stack at any lock, so none of that
 * applies. This file IMPORTS from the route code (`md5Files`, `corpus`, `SESSIONS_ROOT`) and edits
 * none of it: no route artefact's hash line moves because a technique exists.
 *
 * QUARANTINED SIMULATOR OUTPUT (`report_eligible: false`). Every board is the vendored Triangle
 * engine's (`runCaseOracle`), scoped by `verifiedIndex`. Which local shape a T went into has no second
 * implementation on the corpus side, so nothing downstream carries a claim id or a ✓.
 *
 * THE DENOMINATOR (the opportunity). A lock is SCORED when it is a T with an engine spin credit
 * (`full` or `mini`) that cleared lines, at or before the verified index, and passes the
 * RECONSTRUCTION CHECK: the per-lock board snapshot plus the lock's cells must make exactly the rows
 * the engine recorded clearing. That loop is the THIRD copy of `emit-opener-facts.ts`'s (its donation /
 * cave pass, and `dualVerdict`), kept as a copy so that emitter is not edited; `stsd.test.ts` holds the
 * two to the same count in every session (`check.by_session` against `donation.check`), which is the
 * gate on the duplication. The profile's `opportunity` (STSD: a full T-spin Double) is the headline
 * denominator; `controlSpins` are counted beside it. Opener / mid-game split: 0-based lock index
 * `<= WINDOW_PIECES` (imported), the convention `emit-opener-facts.ts` uses — `emit-attack-facts.ts`
 * counts from 1, so the two disagree by one lock about the window's last piece (CLAUDE.md, 「C-Spin
 * 同 DT 砲」); this artefact says which one it uses.
 *
 * THE PREDICATE (`windowMatch`; its Python twin is `technique_transcription.window_fires`, and the
 * test holds the two to one answer over every routes board). Frame: the 40-row oracle board BEFORE
 * the lock, row 0 the top.
 *   1. ANCHOR ON THE T. The lock's cells must equal the variant's T cells (mirrored: columns reflected
 *      inside the window) under exactly one translation, which also fixes the orientation. No other
 *      offset is tried.
 *   2. The window moves with it. A window cell off the board is no match (counted, `window_off_board`).
 *   3. Inside the window, a drawn-filled cell must be filled (a piece letter or garbage — garbage is
 *      FILLED: the profile's `garbage` rule) and a drawn-empty cell empty. Colour is never compared.
 *   4. Outside the window nothing is read. The cleared rows' cells right of it are entailed by the
 *      clear itself (the NaiveClauseForced lesson); the transcription gate's window rule (c) is what
 *      makes leaving them out safe.
 * Both orientations are tried and a lock matching BOTH throws (an asymmetric T cannot), so the order
 * they are tried in cannot change an answer — there is no control for it, because one that cannot
 * fail is a comment. What the mirror CAN get wrong is the follow-up slot, which must be reflected
 * with the window: the `followupUnmirrored` mutant leaves it as drawn on mirrored hits.
 *
 * THE FOLLOW-UP (the technique's payoff). From a hit at lock i, the variant's follow-up slot (its
 * pre-clear cells, from the transcription) is carried through lock i's clear and every later lock's
 * clear and garbage insertion up to the NEXT T lock j. Every step is VERIFIED: the digest records,
 * per lock, whether "previous board + this lock's cells, cleared rows removed, then the lock's
 * garbage rows pushed in under it" reproduces the engine's own next board (garbage with
 * `lockIndex === k` lands after lock k's clear — measured, not assumed). A step it cannot reproduce
 * stops the follow-up as `rowmap_unverified`, never guessed. `fired` iff lock j's cells are the
 * carried slot and lock j is a scored full TSD; otherwise the first reason that applies.
 *
 * THE PAYOFF (a variant with `payoff` in place of `followup`; exactly one of the two, or the
 * transcription is refused). 欄干 (Parapet) promises no second T-spin: its TSD (or TSS) re-opens a well
 * under the T's arm, and every source draws or states the next step as a Tetris into it. So the
 * variant names a WELL CELL (`payoff.well_cell_pre_clear`, reflected with the window when mirrored)
 * and `wellPayoff` carries it exactly as the follow-up slot is carried: through lock i's clear and
 * every later lock's clear and garbage insertion, each step verified (`rowmap_unverified`
 * otherwise). It stops at the FIRST later lock that puts any cell in the well's column, and the
 * first reason that applies is the outcome: `past_verified` (that lock is past the verified index);
 * `well_covered` (no cell at or below the carried row: the well was roofed over); `well_filled_not_i`;
 * `i_in_well_not_quad` (an I in the well that the engine does not record clearing 4 lines); else
 * fired. `slot_off_board` and `round_ended` as for the follow-up. What the window already entails is
 * NOT a payoff: that the column re-opens and that the well is at least 2 deep are decided inside the
 * window by construction (its must-empty cells and its cleared rows), so a check on either could
 * never fail; a quad into the kept well is decided by nothing in the window. A payoff hit also
 * carries `well_depth`: the empty cells from the well cell down to the first filled cell or the
 * floor, on the board before the lock, garbage filled.
 *
 * THE OPPORTUNITY PER VARIANT. A variant is measured at the spin its transcription names
 * (`spin`/`lines`: TSS 1, TSD 2, TST 3, checked against each other); that spin must be the profile's
 * `opportunity` or one of its `controlSpins`, and under a variant whose opportunity is not the
 * profile's, the profile's opportunity becomes one of that variant's controls in its place. Every
 * earlier technique has one TSD variant, so for them nothing moves.
 *
 * CONTROLS, computed in the same pass so the headline is never printed without them: the same window
 * at the control spins; three ablations at the opportunity (`no_must_empty`, `no_roof`, `t_overlap`:
 * the T need not be the window's T, only overlap a window that matches the board with the T in); and
 * the orientation baseline (opportunities whose T is stood up at all).
 */
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { WINDOW_PIECES } from './opener-window.ts';
import { md5Files, corpus, SESSIONS_ROOT } from './route-facts.ts';
import type { TechniqueProfile, SpinKind } from './technique-profile.ts';

const H = 40, W = 10;
const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

// ── digests: everything `classify` reads, so the mutants in a test cost no re-simulation ──────────

export interface Cell { row: number; col: number }
export interface LockLite {
  piece: string; spin: string; cleared: number; cells: Cell[]; clearedRows: number[];
  /** garbage rows inserted during this lock (after its clear) */
  garbage: number;
  /** "board before + cells, cleared rows out, garbage in" reproduces the engine's board after */
  mapOk: boolean;
}
export interface TSpinLock { i: number; board: string[] }
export interface TechDigest {
  session: string; file: string; round: number; match: number; user: string;
  v: number; locks: LockLite[];
  /** every T lock with a spin credit that cleared, with the board BEFORE it ('.' empty, a piece
   *  letter, 'G' garbage) — inside the verified prefix or not, so the `pastPrefix` mutant can read it */
  tspins: TSpinLock[];
}

const rowsOf = (b: any[][] | undefined): string[] =>
  b ? b.map(r => r.map((x: any) => x == null ? '.' : String(x)).join('')) : Array(H).fill('.'.repeat(W));

/** One session through the oracle, reduced to what the matcher reads. Technique-independent. */
export function digestSession(session: string, root = SESSIONS_ROOT): TechDigest[] {
  const dir = `${root}/${session}`;
  const rf = JSON.parse(readFileSync(`${dir}/sim/replay-facts.json`, 'utf8'));
  const pos = new Map<string, number>();
  for (const r of rf.rounds) pos.set(`${r.file}#${r.round}`, r.match);
  const out: TechDigest[] = [];
  for (const c of loadCases(dir)) {
    const match = pos.get(`${c.file}#${c.round}`);
    if (match === undefined) throw new Error(`technique: ${session} ${c.file} r${c.round} has no replay-facts entry`);
    const r = runCaseOracle(c);
    const v = verifiedIndex(r, c.truth);
    const G = new Array(r.locks.length).fill(0);
    for (const g of r.garbageEvents) if (g.lockIndex < G.length) G[g.lockIndex] += g.amt;
    const locks: LockLite[] = [];
    const tspins: TSpinLock[] = [];
    for (let k = 0; k < r.locks.length; k++) {
      const lk = r.locks[k]!;
      const clearedRows = [...(r.records[k]?.clearedRows ?? [])];
      const before = k > 0 ? rowsOf(r.boards[k - 1] as any) : rowsOf(undefined);
      const after = r.boards[k] ? rowsOf(r.boards[k] as any) : null;
      // the row map, verified against the engine's own next board (occupancy, above the garbage)
      let mapOk = false;
      if (after) {
        const g = before.map(s => s.split('').map(x => x !== '.'));
        for (const q of lk.cells) if (q.row >= 0 && q.row < H && q.col >= 0 && q.col < W) g[q.row]![q.col] = true;
        const cl = new Set(clearedRows);
        const kept = g.filter((_, i) => !cl.has(i));
        while (kept.length < H) kept.unshift(new Array(W).fill(false));
        const pred = kept.slice(G[k]);
        mapOk = pred.every((row, i) => row.every((x, cc) => x === (after[i]![cc] !== '.')));
      }
      locks.push({ piece: lk.piece, spin: lk.spin, cleared: lk.cleared,
                   cells: lk.cells.map(q => ({ row: q.row, col: q.col })), clearedRows, garbage: G[k], mapOk });
      if (lk.piece === 'T' && lk.spin !== 'none' && lk.cleared > 0) tspins.push({ i: k, board: before });
    }
    out.push({ session, file: c.file, round: c.round, match, user: c.user, v, locks, tspins });
  }
  return out;
}

export const digestCorpus = (sessions = corpus()) => sessions.flatMap(s => digestSession(s));

const kindKey = (spin: string, lines: number) => `${spin === 'mini' ? 'mini' : 'full'}:${lines}`;

// ── the transcription ────────────────────────────────────────────────────────────────────────────

export interface Variant {
  id: string; board: string; spin: string; lines: number;
  window: { rows: [number, number]; cols: [number, number] };
  t_cells: [number, number][];
  /** cells OUTSIDE the box the window also reads, filled or empty as drawn (千鳥格子's overhang over the
   *  second slot, which the drawings agree on although the rest of its row does not); mirrored with the box */
  window_extra?: { cells: [number, number][]; note: string };
  /** the second T-spin the page draws (STSD …); exactly one of `followup` and `payoff` */
  followup?: { board: string; spin: string; lines: number; t_cells_pre_clear: [number, number][];
               t_cells_after: [number, number][] };
  /** the Tetris into the well the spin keeps open (欄干); exactly one of `followup` and `payoff` */
  payoff?: { kind: 'well_quad'; board: string; piece: 'I'; lines: 4; well_cell_pre_clear: [number, number];
             well_cell_after: [number, number]; note: string };
}
interface WinCell { r: number; c: number; v: 'T' | '#' | '.' }
export interface Prepared { id: string; mirrored: boolean; cells: WinCell[]; T: WinCell[]; roofTop: number;
                            followup: { r: number; c: number }[]; followupKind: string;
                            /** the payoff's well cell (pre-clear), mirrored with the window */
                            well?: { r: number; c: number } }

export function loadTranscription(path: string) { return JSON.parse(readFileSync(path, 'utf8')); }

/** A variant's window, as drawn and mirrored, in its board's frame (row 0 the top). */
export function prepare(tr: any, v: Variant): Prepared[] {
  const rows: string[] = tr.nodes.find((n: any) => n.id === v.board).rows;
  const emptyLetters: string = tr.empty_letters ?? '';
  const empty = (ch: string) => ch === '-' || emptyLetters.includes(ch);
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  const tc = new Set(v.t_cells.map(([r, c]) => `${r},${c}`));
  if (!v.followup === !v.payoff)
    throw new Error(`technique: variant ${v.id} carries ${v.followup ? 'both' : 'neither'} of followup and payoff`);
  if (v.payoff && v.payoff.kind !== 'well_quad') throw new Error(`technique: variant ${v.id} payoff kind ${v.payoff.kind}`);
  return [false, true].map(mirrored => {
    const mc = (c: number) => mirrored ? c0 + (c1 - c) : c;
    const cells: WinCell[] = [];
    for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++)
      cells.push({ r, c: mc(c), v: tc.has(`${r},${c}`) ? 'T' : empty(rows[r]![c]!) ? '.' : '#' });
    for (const [r, c] of v.window_extra?.cells ?? []) {
      if (r >= r0 && r <= r1 && c >= c0 && c <= c1) throw new Error(`technique: ${v.id}'s window_extra cell ${r},${c} is inside the box`);
      cells.push({ r, c: mc(c), v: empty(rows[r]![c]!) ? '.' : '#' });
    }
    const T = cells.filter(x => x.v === 'T');
    const P: Prepared = { id: v.id, mirrored, cells, T, roofTop: Math.min(...T.map(x => x.r)),
             followup: v.followup ? v.followup.t_cells_pre_clear.map(([r, c]) => ({ r, c: mc(c) })) : [],
             // the follow-up is a full T-spin clearing the transcription's `followup.lines`
             followupKind: v.followup ? kindKey('full', v.followup.lines) : '' };
    if (v.payoff) P.well = { r: v.payoff.well_cell_pre_clear[0], c: mc(v.payoff.well_cell_pre_clear[1]) };
    return P;
  });
}

// ── the predicate ────────────────────────────────────────────────────────────────────────────────

export interface Mutants {
  noMirror?: boolean; followupUnmirrored?: boolean; noRecon?: boolean; pastPrefix?: boolean;
  includeMini?: boolean; noMustEmpty?: boolean; noRoof?: boolean; tOverlap?: boolean;
  garbageEmpty?: boolean; rowAnchorOff1?: boolean; openerLt?: boolean;
  followupNoRowmap?: boolean; followupAnyT?: boolean;
  /** the payoff fires on the first piece in the well, whatever it is; on any I in the well, quad or not */
  payoffAnyPiece?: boolean; payoffNoQuad?: boolean;
}
type Clause = { mustEmpty: boolean; roof: boolean; garbageFilled: boolean; rowOff: number };

/** THE PREDICATE. `board` is the board before the lock, `cells` the lock's cells. Returns the offset
 *  on a match, `null` when the T fits but the window leaves the board, `false` otherwise. */
export function windowMatch(board: string[], cells: Cell[], P: Prepared,
                            cl: Clause = { mustEmpty: true, roof: true, garbageFilled: true, rowOff: 0 }):
    { dr: number; dc: number } | null | false {
  if (cells.length !== P.T.length) return false;
  const dr = Math.min(...cells.map(q => q.row)) - Math.min(...P.T.map(x => x.r)) + cl.rowOff;
  const dc = Math.min(...cells.map(q => q.col)) - Math.min(...P.T.map(x => x.c));
  const want = new Set(P.T.map(x => `${x.r + dr},${x.c + dc}`));
  if (!cells.every(q => want.has(`${q.row},${q.col}`))) return false;
  for (const x of P.cells) {
    const R = x.r + dr, C = x.c + dc;
    if (R < 0 || R >= board.length || C < 0 || C >= W) return null;
    if (x.v === 'T') continue;
    if (!cl.roof && x.r < P.roofTop) continue;
    const ch = board[R]![C]!;
    const filled = ch !== '.' && (cl.garbageFilled || ch !== 'G');
    if (x.v === '#' && !filled) return false;
    if (x.v === '.' && filled && cl.mustEmpty) return false;
  }
  return { dr, dc };
}

/** The `t_overlap` ablation: no anchor. Any placement of the window (as drawn or mirrored) that
 *  matches the board WITH the T in (T cells read as must-be-filled) and holds at least one of the
 *  lock's cells. */
function overlapMatch(withT: boolean[][], cells: Cell[], Ps: Prepared[]): boolean {
  const rows = cells.map(q => q.row), cols = cells.map(q => q.col);
  for (const P of Ps) {
    const pr = P.cells.map(x => x.r), pc = P.cells.map(x => x.c);
    // only offsets that put at least one lock cell inside the window
    for (let dr = Math.min(...rows) - Math.max(...pr); dr <= Math.max(...rows) - Math.min(...pr); dr++)
    for (let dc = Math.min(...cols) - Math.max(...pc); dc <= Math.max(...cols) - Math.min(...pc); dc++) {
      let ok = true, holds = false;
      for (const x of P.cells) {
        const R = x.r + dr, C = x.c + dc;
        if (R < 0 || R >= H || C < 0 || C >= W) { ok = false; break; }
        const f = withT[R]![C]!;
        if ((x.v === '.') === f) { ok = false; break; }
      }
      if (!ok) continue;
      for (const q of cells) if (P.cells.some(x => x.r + dr === q.row && x.c + dc === q.col)) holds = true;
      if (holds) return true;
    }
  }
  return false;
}

const isStood = (cells: Cell[]) => {
  const rs = new Set(cells.map(q => q.row)), cs = new Set(cells.map(q => q.col));
  return rs.size === 3 && cs.size === 2;
};

// ── classification ───────────────────────────────────────────────────────────────────────────────

const KIND_NAME: Record<string, string> = { 'full:1': 'TSS', 'full:2': 'TSD', 'full:3': 'TST' };
const kindName = (k: string) => KIND_NAME[k] ?? `T-spin ${k}`;
const SPIN_LINES: Record<string, number> = { TSS: 1, TSD: 2, TST: 3 };

/** The opportunity a variant is measured at: the full T-spin its transcription names, which must be
 *  the profile's opportunity or one of its control spins. */
function variantOpp(tag: string, v: Variant, opp: string, ctl: { key: string }[]): string {
  if (SPIN_LINES[v.spin] !== v.lines) throw new Error(`${tag}: variant ${v.id} is a ${v.spin} clearing ${v.lines} line(s)`);
  const key = kindKey('full', v.lines);
  if (key !== opp && !ctl.some(c => c.key === key))
    throw new Error(`${tag}: variant ${v.id}'s ${v.spin} is neither the opportunity nor a control spin`);
  return key;
}

export interface Hit {
  session: string; file: string; round_index0: number; match: number; round: number; player: string;
  variant: string; lock: number; in_opener: boolean; mirrored: boolean; garbage_in_window: boolean;
  window_letters: string[]; verified_to: number;
  followup: { lock: number | null; fired: boolean; reason: string | null };
  /** a payoff variant's hit only: the empty cells under the well cell, before the lock */
  well_depth?: number;
  /** a profile with a `qualify` hook only: whether the hit was built as the technique, and every rule it fails */
  qualifies?: boolean; not_qualified?: string[];
}

const sameSet = (a: Cell[], b: { r: number; c: number }[]) =>
  a.length === b.length && b.every(x => a.some(q => q.row === x.r && q.col === x.c));

/** The follow-up from a hit at lock `i` with offset (dr, dc): see the header. */
function followup(d: TechDigest, i: number, P: Prepared, off: { dr: number; dc: number }, mut: Mutants,
                  scored: Map<number, { kind: string; recon: boolean }>) {
  // the `followupUnmirrored` mutant: on a mirrored hit, reflect the slot back to the drawn columns
  const wc = P.cells.map(x => x.c), span = Math.min(...wc) + Math.max(...wc);
  const unmirror = mut.followupUnmirrored && P.mirrored;
  let slot = P.followup.map(x => ({ r: x.r + off.dr, c: (unmirror ? span - x.c : x.c) + off.dc }));
  const step = (lk: LockLite) => {
    if (mut.followupNoRowmap) return;
    slot = slot.map(x => ({ r: x.r + lk.clearedRows.filter(y => y > x.r).length - lk.garbage, c: x.c }));
  };
  const at = (lock: number | null, reason: string | null, fired = false) => ({ lock, fired, reason });
  if (!d.locks[i]!.mapOk) return at(i, 'rowmap_unverified');
  step(d.locks[i]!);
  for (let k = i + 1; k < d.locks.length; k++) {
    const lk = d.locks[k]!;
    if (lk.piece === 'T') {
      if (k > d.v && !mut.pastPrefix) return at(k, 'past_verified');
      const s = scored.get(k);
      if (mut.followupAnyT && s?.recon) return at(k, null, true);
      if (!sameSet(lk.cells, slot)) return at(k, 'next_t_elsewhere');
      if (!s || s.kind !== P.followupKind) return at(k, 't_in_slot_not_tsd');
      if (!s.recon) return at(k, 'recon_dropped');
      return at(k, null, true);
    }
    if (lk.cells.some(q => slot.some(x => x.r === q.row && x.c === q.col))) return at(k, 'slot_filled_before_t');
    if (!lk.mapOk) return at(k, 'rowmap_unverified');
    step(lk);
    if (slot.some(x => x.r < 0)) return at(k, 'slot_off_board');
  }
  return at(null, 'round_ended');
}

/** The payoff from a hit at lock `i` with offset (dr, dc): the well cell carried to the first later
 *  lock that puts a cell in its column (see the header). */
function wellPayoff(d: TechDigest, i: number, P: Prepared, off: { dr: number; dc: number }, mut: Mutants) {
  const wc = P.cells.map(x => x.c), span = Math.min(...wc) + Math.max(...wc);
  const unmirror = mut.followupUnmirrored && P.mirrored;
  let well = { r: P.well!.r + off.dr, c: (unmirror ? span - P.well!.c : P.well!.c) + off.dc };
  const step = (lk: LockLite) => {
    if (mut.followupNoRowmap) return;
    well = { r: well.r + lk.clearedRows.filter(y => y > well.r).length - lk.garbage, c: well.c };
  };
  const at = (lock: number | null, reason: string | null, fired = false) => ({ lock, fired, reason });
  if (!d.locks[i]!.mapOk) return at(i, 'rowmap_unverified');
  step(d.locks[i]!);
  for (let k = i + 1; k < d.locks.length; k++) {
    const lk = d.locks[k]!;
    const inCol = lk.cells.filter(q => q.col === well.c);
    if (inCol.length) {
      if (k > d.v && !mut.pastPrefix) return at(k, 'past_verified');
      if (!inCol.some(q => q.row >= well.r)) return at(k, 'well_covered');
      if (mut.payoffAnyPiece) return at(k, null, true);
      if (lk.piece !== 'I') return at(k, 'well_filled_not_i');
      if (lk.cleared !== 4 && !mut.payoffNoQuad) return at(k, 'i_in_well_not_quad');
      return at(k, null, true);
    }
    if (!lk.mapOk) return at(k, 'rowmap_unverified');
    step(lk);
    if (well.r < 0) return at(k, 'slot_off_board');
  }
  return at(null, 'round_ended');
}

/** The empty cells from the well cell down to the first filled cell or the floor ('G' filled). */
function wellDepth(board: string[], P: Prepared, off: { dr: number; dc: number }): number {
  const c = P.well!.c + off.dc;
  let n = 0;
  for (let r = P.well!.r + off.dr; r < board.length && board[r]![c] === '.'; r++) n++;
  return n;
}

export interface Classified {
  users: string[];
  denominators: Record<string, any>;
  hits: Hit[];
  perVariant: Record<string, any>;
  check: any;
  offBoard: string[];
  reconDropped: string[];
  /** recon-dropped spins at a variant opportunity other than the profile's, by its kind name */
  reconOther: Record<string, string[]>;
  /** each variant's opportunity, by kind name */
  variantOpps: Record<string, string>;
}

export const caseName = (h: { session: string; match: number; round: number; player: string }) =>
  `${h.session} m${h.match}r${h.round} ${h.player}`;

export function classify(P: TechniqueProfile, tr: any, digests: TechDigest[], mut: Mutants = {}): Classified {
  const variants: Variant[] = tr.variants;
  const preps = variants.map(v => prepare(tr, v));
  const users = [...new Set(digests.map(d => d.user))].sort();
  const per = <T>(f: () => T) => Object.fromEntries(users.map(u => [u, f()])) as Record<string, T>;
  const split = () => ({ all: 0, in_opener: 0, mid_game: 0 });
  const opp = kindKey(P.opportunity.spin, P.opportunity.lines);
  const ctl = P.controlSpins.map(c => ({ name: c.name, key: kindKey(c.kind.spin, c.kind.lines) }));
  // each variant's opportunity, and its controls: the profile's controls less its own spin, with the
  // profile's opportunity in its place (for a variant measured at the opportunity: exactly `ctl`)
  const vOpps = variants.map(v => variantOpp(P.tag, v, opp, ctl));
  const unders = vOpps.map(vo => [{ name: kindName(opp), key: opp }, ...ctl].filter(c => c.key !== vo));
  const otherOpps = [...new Set(vOpps.filter(k => k !== opp))];
  const denominators = per(() => ({
    [kindName(opp)]: split(),
    ...Object.fromEntries(ctl.map(c => [c.name, split()])),
    other_scored: 0, recon_disagreed: 0, unscored_past_prefix: 0,
  } as Record<string, any>));
  const inOpener = (i: number) => mut.openerLt ? i < WINDOW_PIECES : i <= WINDOW_PIECES;
  const bySession: Record<string, { tspin_clears: number; reconstruction_disagreed: number;
                                    players: Record<string, number> }> = {};
  let agreed = 0, disagreed = 0, rowmapSteps = 0, rowmapBad = 0;
  const hits: Hit[] = [];
  const offBoard: string[] = [], reconDropped: string[] = [];
  const reconOther: Record<string, string[]> = Object.fromEntries(otherOpps.map(k => [k, []]));
  const pv = Object.fromEntries(variants.map((v, vi) => [v.id, {
    hits: per(() => ({ all: 0, in_opener: 0, mid_game: 0, mirrored: 0, garbage_in_window: 0 })),
    followup: per(() => ({ fired: 0, not_fired: {} as Record<string, number> })),
    under: Object.fromEntries(unders[vi]!.map(c => [c.name, per(() => 0)])),
    ablation: { no_must_empty: per(() => 0), no_roof: per(() => 0), t_overlap: per(() => 0) },
    orientation_baseline: per(() => 0),
  }]));

  for (const d of digests) {
    for (const lk of d.locks) { rowmapSteps++; if (!lk.mapOk) rowmapBad++; }
    const name = caseName({ session: d.session, match: d.match, round: d.round + 1, player: d.user });
    const S = (bySession[d.session] ??= { tspin_clears: 0, reconstruction_disagreed: 0, players: {} });
    S.players[d.user] ??= 0;   // every player of the session is present, so a missing one is a defect
    // pass 1: the scored set (licence + reconstruction check), and the denominators
    const scored = new Map<number, { kind: string; recon: boolean }>();
    const withTs = new Map<number, boolean[][]>();
    for (const t of d.tspins) {
      const lk = d.locks[t.i]!;
      const inPrefix = t.i <= d.v;
      if (!inPrefix && !mut.pastPrefix) { denominators[d.user]!.unscored_past_prefix++; continue; }
      const withT = t.board.map(s => s.split('').map(x => x !== '.'));
      for (const q of lk.cells) if (q.row >= 0 && q.row < H && q.col >= 0 && q.col < W) withT[q.row]![q.col] = true;
      const mine: number[] = [];
      for (let rr = 0; rr < H; rr++) if (withT[rr]!.every(Boolean)) mine.push(rr);
      const theirs = [...lk.clearedRows].sort((a, b) => a - b);
      const agrees = mine.length === theirs.length && mine.every((x, k) => x === theirs[k]);
      // counted exactly as emit-opener-facts.ts counts `donation.check`: a disagreement, or an
      // agreement on a non-empty set of rows (an agreed empty set is neither)
      if (inPrefix && !agrees) { S.tspin_clears++; S.reconstruction_disagreed++; }
      else if (inPrefix && mine.length) { S.tspin_clears++; S.players[d.user] = (S.players[d.user] ?? 0) + 1; }
      const recon = mut.noRecon ? true : agrees;
      if (!recon) {
        disagreed++; denominators[d.user]!.recon_disagreed++;
        if (lk.spin === 'full' && lk.cleared === 2) reconDropped.push(`${name} lock ${t.i}`);
        const ko = kindKey(lk.spin, lk.cleared);
        if (reconOther[ko]) reconOther[ko]!.push(`${name} lock ${t.i}`);
        scored.set(t.i, { kind: kindKey(lk.spin, lk.cleared), recon: false });
        continue;
      }
      if (!mine.length && !mut.noRecon) continue;
      agreed++;
      let key = kindKey(lk.spin, lk.cleared);
      if (mut.includeMini && lk.spin === 'mini') key = kindKey('full', lk.cleared);
      scored.set(t.i, { kind: key, recon: true });
      withTs.set(t.i, withT);
      const D = denominators[d.user]!;
      const tgt = key === opp ? D[kindName(opp)] : ctl.find(c => c.key === key) ? D[ctl.find(c => c.key === key)!.name] : null;
      if (tgt) { tgt.all++; tgt[inOpener(t.i) ? 'in_opener' : 'mid_game']++; } else D.other_scored++;
    }
    // pass 2: the window at every scored spin
    for (const t of d.tspins) {
      const s = scored.get(t.i);
      if (!s || !s.recon) continue;
      const lk = d.locks[t.i]!;
      for (let vi = 0; vi < variants.length; vi++) {
        const v = variants[vi]!, Ps = preps[vi]!, rec = pv[v.id]!, vOpp = vOpps[vi]!, under = unders[vi]!;
        const cl: Clause = { mustEmpty: !mut.noMustEmpty, roof: !mut.noRoof, garbageFilled: !mut.garbageEmpty,
                             rowOff: mut.rowAnchorOff1 ? 1 : 0 };
        const order = [Ps[0]!, Ps[1]!];
        let found: { P: Prepared; off: { dr: number; dc: number } } | null = null, off = false;
        const tryAll = (c: Clause) => {
          let f: typeof found = null, o = false;
          for (const Pp of order) {
            if (Pp.mirrored && mut.noMirror) continue;
            const m = windowMatch(t.board, lk.cells, Pp, c);
            if (m === null) o = true;
            else if (m) { if (f) throw new Error(`${P.tag}: ${name} lock ${t.i} matches as drawn AND mirrored`); f = { P: Pp, off: m }; }
          }
          return { f, o };
        };
        let base = tryAll(cl);
        if (mut.tOverlap && s.kind === vOpp) {
          base = { f: overlapMatch(withTs.get(t.i)!, lk.cells, Ps) ? { P: Ps[0]!, off: { dr: 0, dc: 0 } } : null, o: false };
        }
        found = base.f; off = base.o;
        if (s.kind === vOpp) {
          const strict = { mustEmpty: true, roof: true, garbageFilled: true, rowOff: 0 };
          const ab = (c: Clause) => Ps.some(Pp => !!windowMatch(t.board, lk.cells, Pp, c));
          if (ab({ ...strict, mustEmpty: false })) rec.ablation.no_must_empty[d.user]++;
          if (ab({ ...strict, roof: false })) rec.ablation.no_roof[d.user]++;
          if (overlapMatch(withTs.get(t.i)!, lk.cells, Ps)) rec.ablation.t_overlap[d.user]++;
          if (isStood(lk.cells)) rec.orientation_baseline[d.user]++;
          if (off && !found) offBoard.push(`${name} lock ${t.i}${variants.length > 1 ? ` (${v.id})` : ''}`);
        }
        if (!found) continue;
        const c = under.find(x => x.key === s.kind);
        if (c) { rec.under[c.name][d.user]++; continue; }
        if (s.kind !== vOpp) continue;
        // a hit
        const { P: Pp, off: o } = found;
        const rs = Pp.cells.map(x => x.r + o.dr), cs = Pp.cells.map(x => x.c + o.dc);
        const R0 = Math.min(...rs), R1 = Math.max(...rs), C0 = Math.min(...cs), C1 = Math.max(...cs);
        const letters: string[] = [];
        for (let r = R0; r <= R1; r++) letters.push(t.board[r]!.slice(C0, C1 + 1));
        const g = Pp.cells.some(x => x.v === '#' && t.board[x.r + o.dr]![x.c + o.dc] === 'G');
        const fu = mut.tOverlap ? { lock: null, fired: false, reason: 'not_anchored' }
          : Pp.well ? wellPayoff(d, t.i, Pp, o, mut) : followup(d, t.i, Pp, o, mut, scored);
        const h: Hit = { session: d.session, file: d.file, round_index0: d.round, match: d.match, round: d.round + 1,
          player: d.user, variant: v.id, lock: t.i, in_opener: inOpener(t.i), mirrored: Pp.mirrored,
          garbage_in_window: g, window_letters: letters, verified_to: d.v, followup: fu,
          ...(Pp.well ? { well_depth: wellDepth(t.board, Pp, o) } : {}) };
        hits.push(h);
        const hb = rec.hits[d.user]!;
        hb.all++; hb[h.in_opener ? 'in_opener' : 'mid_game']++;
        if (h.mirrored) hb.mirrored++;
        if (g) hb.garbage_in_window++;
        const fb = rec.followup[d.user]!;
        if (fu.fired) fb.fired++; else fb.not_fired[fu.reason!] = (fb.not_fired[fu.reason!] ?? 0) + 1;
      }
    }
  }
  for (const v of Object.values(pv)) for (const u of users) {
    v.followup[u]!.not_fired = Object.fromEntries(Object.entries(v.followup[u]!.not_fired).sort());
  }
  for (const s of Object.values(bySession))
    s.players = Object.fromEntries(Object.entries(s.players).sort());
  return {
    users, denominators, hits, perVariant: pv, offBoard, reconDropped,
    reconOther: Object.fromEntries(Object.entries(reconOther).map(([k, l]) => [kindName(k), l])),
    variantOpps: Object.fromEntries(variants.map((v, vi) => [v.id, kindName(vOpps[vi]!)])),
    check: { tspin_clears_scored: agreed + disagreed, reconstruction_agreed: agreed,
             reconstruction_disagreed: disagreed, rowmap_steps: rowmapSteps, rowmap_unverified: rowmapBad,
             by_session: Object.fromEntries(Object.entries(bySession).sort()) },
  };
}

// ── the cross-route (a route artefact's rounds that reached a node drawing this technique next) ───

export interface CrossRoute {
  key: string; artefact: string; node: string; note: string;
  /** The last 0-based lock of the drawn continuation: a hit after it is not the drawing (recorded as
   *  `later_hit_lock`, never counted). The profile states where it comes from; the test re-derives it. */
  continuationLastLock: number; continuationNote: string;
}

/** A cross-route row's outcome. Only `hit` and `no_hit` are MEASURED, so only they are in the
 *  denominator: a node the route reached past its verified prefix (`node_unverified`), or a
 *  continuation whose verified prefix ends before its last lock with no hit inside it
 *  (`continuation_unverified`), is named with that reason and kept out of M. */
export type CrossOutcome = 'hit' | 'no_hit' | 'node_unverified' | 'continuation_unverified';

export function crossRoute(cr: CrossRoute, digests: TechDigest[], hits: Hit[], tag: string) {
  const art = JSON.parse(readFileSync(cr.artefact, 'utf8'));
  const rows: { round: string; node_lock: number; verified_to: number; outcome: CrossOutcome;
                hit_lock: number | null; later_hit_lock: number | null;
                tspins: number | null; tsd: number | null; tsd_stood: number | null; first_tsd: number | null }[] = [];
  const last = cr.continuationLastLock;
  for (const c of art.cases) {
    const s = c.snapshots.find((x: any) => x.node === cr.node);
    if (!s) continue;
    if (typeof s.verified !== 'boolean') throw new Error(`${tag}: cross-route snapshot without a verified flag`);
    const d = digests.find(x => x.session === c.session && x.file === c.file && x.round === c.round_index0 && x.user === c.player);
    if (!d) throw new Error(`${tag}: cross-route ${c.session} ${c.file} r${c.round_index0} ${c.player} is in no digest`);
    const name = caseName({ session: d.session, match: d.match, round: d.round + 1, player: d.user });
    const mine = hits.filter(x => x.session === d.session && x.file === d.file && x.round_index0 === d.round
      && x.player === d.user && x.lock > s.lock).sort((a, b) => a.lock - b.lock);
    const inside = mine.find(x => x.lock <= last) ?? null;
    const later = mine.find(x => x.lock > last) ?? null;
    let outcome: CrossOutcome;
    let counts = { tspins: null as number | null, tsd: null as number | null, tsd_stood: null as number | null,
                   first_tsd: null as number | null };
    if (!s.verified || s.lock > d.v) outcome = 'node_unverified';
    else if (inside) outcome = 'hit';
    else if (d.v < last) outcome = 'continuation_unverified';
    else {
      // the measured miss: every scored-or-not T-spin of the round inside the continuation
      outcome = 'no_hit';
      const after = d.tspins.filter(t => t.i > s.lock && t.i <= last);
      const tsd = after.filter(t => d.locks[t.i]!.spin === 'full' && d.locks[t.i]!.cleared === 2);
      counts = { tspins: after.length, tsd: tsd.length, tsd_stood: tsd.filter(t => isStood(d.locks[t.i]!.cells)).length,
                 first_tsd: tsd[0]?.i ?? null };
    }
    rows.push({ round: name, node_lock: s.lock, verified_to: d.v, outcome,
                hit_lock: inside ? inside.lock : null, later_hit_lock: later ? later.lock : null, ...counts });
  }
  rows.sort((a, b) => a.round < b.round ? -1 : a.round > b.round ? 1 : 0);
  const scored = rows.filter(r => r.outcome === 'hit' || r.outcome === 'no_hit');
  return { source: cr.artefact.replace(/^.*\/analysis\//, 'analysis/'), node: cr.node, note: cr.note,
           continuation: { last_lock: last, note: cr.continuationNote },
           rounds_reaching_node: rows.length, rounds_scored: scored.length,
           with_hit: scored.filter(r => r.outcome === 'hit').length, by_round: rows };
}

/** One English line per cross-route row, for the named lists. */
export function crossRouteLine(r: ReturnType<typeof crossRoute>['by_round'][number], last: number): string {
  const later = r.later_hit_lock !== null ? `; an STSD hit at lock ${r.later_hit_lock}, past the continuation` : '';
  switch (r.outcome) {
    case 'hit': return `${r.round} (STSD hit at lock ${r.hit_lock})`;
    case 'node_unverified': return `${r.round} (node at lock ${r.node_lock} is past the verified prefix, verified to lock ${r.verified_to}${later})`;
    case 'continuation_unverified':
      return `${r.round} (continuation runs to lock ${last}, verified only to lock ${r.verified_to}; no hit before it${later})`;
    case 'no_hit':
      return `${r.round} (no STSD hit in locks ${r.node_lock + 1}-${last}: ${r.tspins} T-spin(s), ${r.tsd} full TSD(s)`
        + `${r.first_tsd !== null ? ` (first at lock ${r.first_tsd})` : ''}, ${r.tsd_stood} stood${later})`;
  }
}

// ── the artefact ─────────────────────────────────────────────────────────────────────────────────

export function inputs(P: TechniqueProfile & { crossRoute?: CrossRoute }, sessions: string[], root = SESSIONS_ROOT) {
  return {
    sessions: sessions.map(s => {
      const dir = `${root}/${s}`;
      const h = createHash('md5');
      for (const f of readdirSync(dir).filter(f => f.endsWith('.ttrm')).sort()) h.update(f).update(readFileSync(`${dir}/${f}`));
      return { session: s, replays_md5: h.digest('hex'), replay_facts_md5: md5(readFileSync(`${dir}/sim/replay-facts.json`)) };
    }),
    transcription_md5: md5(readFileSync(P.transcriptionPath)),
    emitter_md5: md5Files(P.hashFiles.classifier),
    ...(P.crossRoute ? { cross_route_md5: md5(readFileSync(P.crossRoute.artefact)) } : {}),
  };
}

export function assemble(P: TechniqueProfile & { crossRoute?: CrossRoute }, cls: Classified, digests: TechDigest[],
                         sessions: string[], inp: ReturnType<typeof inputs>) {
  const hits = [...cls.hits].sort((a, b) => a.session < b.session ? -1 : a.session > b.session ? 1
    : a.match - b.match || a.round - b.round || (a.player < b.player ? -1 : a.player > b.player ? 1 : 0) || a.lock - b.lock);
  const name = (h: any) => caseName(h);
  const variants = Object.fromEntries(Object.entries(cls.perVariant).map(([id, v]: [string, any]) => [id, {
    hits_by_player: v.hits, followup_by_player: v.followup,
    controls: { under: v.under, ablation: v.ablation, orientation_baseline: v.orientation_baseline },
  }]));
  const cr = P.crossRoute ? crossRoute(P.crossRoute, digests, hits, P.tag) : null;
  // the profile's optional `qualify` hook: each hit gains `qualifies` / `not_qualified`, and the artefact
  // a per-player tally and two lists (a profile without the hook is untouched)
  let qualify: any = null;
  if (P.qualify) {
    const byKey = new Map(digests.map(d => [`${d.session}|${d.file}|${d.round}|${d.user}`, d]));
    const tally: Record<string, { qualified: number; not_qualified: Record<string, number> }> =
      Object.fromEntries(cls.users.map(u => [u, { qualified: 0, not_qualified: {} }]));
    for (const h of hits) {
      const d = byKey.get(`${h.session}|${h.file}|${h.round_index0}|${h.player}`);
      if (!d) throw new Error(`${P.tag}: ${caseName(h)} lock ${h.lock} has no digest`);
      Object.assign(h, P.qualify.check(h, d));
      const t = tally[h.player]!;
      if (h.qualifies) t.qualified++;
      for (const r of h.not_qualified!) t.not_qualified[r] = (t.not_qualified[r] ?? 0) + 1;
    }
    for (const t of Object.values(tally)) t.not_qualified = Object.fromEntries(Object.entries(t.not_qualified).sort());
    qualify = { rules: P.qualify.rules, by_player: tally };
  }
  return {
    schema: P.artefact.schema,
    report_eligible: false,
    technique: P.key,
    means: P.artefact.means,
    not_eligible_because: P.artefact.notEligible,
    caveat: P.artefact.caveat,
    rules: P.rules(),
    inputs: inp,
    sessions,
    window_pieces: WINDOW_PIECES,
    window_rule: `0-based lock index <= ${WINDOW_PIECES} is in_opener (emit-opener-facts.ts's convention; emit-attack-facts.ts counts from 1)`,
    opportunity: `${P.opportunity.spin} T-spin clearing ${P.opportunity.lines} line(s)`,
    ...(Object.keys(cls.reconOther).length ? { variant_opportunities: cls.variantOpps } : {}),
    denominators: cls.denominators,
    check: cls.check,
    variants,
    ...(cr ? { cross_route: cr } : {}),
    ...(qualify ? { qualify } : {}),
    lists: {
      ...P.lists(hits, name),
      ...(qualify ? {
        qualified_hits: hits.filter(h => h.qualifies).map(h => `${name(h)} lock ${h.lock}`),
        not_qualified: hits.filter(h => !h.qualifies).map(h => `${name(h)} lock ${h.lock} (${h.not_qualified!.join(', ')})`),
      } : {}),
      window_off_board: cls.offBoard,
      recon_dropped_tsd: cls.reconDropped,
      ...Object.fromEntries(Object.entries(cls.reconOther).map(([k, l]) => [`recon_dropped_${k.toLowerCase()}`, l])),
      ...(cr ? {
        cross_route_no_hit: cr.by_round.filter(r => r.outcome === 'no_hit').map(r => crossRouteLine(r, cr.continuation.last_lock)),
        cross_route_unscored: cr.by_round.filter(r => r.outcome === 'node_unverified' || r.outcome === 'continuation_unverified')
          .map(r => crossRouteLine(r, cr.continuation.last_lock)),
      } : {}),
    },
    hits,
  };
}

/** One hit per line: diffable. */
export function serialise(out: any): string {
  const { hits, ...rest } = out;
  const head = JSON.stringify({ ...rest, hits: '\u0000' }, null, 1);
  return head.replace('"\\u0000"', '[\n' + hits.map((c: any) => '  ' + JSON.stringify(c)).join(',\n') + '\n ]') + '\n';
}

export function build(P: TechniqueProfile & { crossRoute?: CrossRoute }, mut: Mutants = {}, digests?: TechDigest[]) {
  const sessions = corpus();
  const ds = digests ?? digestCorpus(sessions);
  const tr = loadTranscription(P.transcriptionPath);
  return assemble(P, classify(P, tr, ds, mut), ds, sessions, inputs(P, sessions));
}

export type { SpinKind };
