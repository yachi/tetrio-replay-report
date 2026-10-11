/**
 * 迷走砲 (Stray Cannon) route classifier: the deepest node of shiwehi.com's route tree that each
 * corpus round reaches, over every session at once.
 *
 *   bun pipeline/sim/emit-stray-cannon-facts.ts --out analysis/stray-cannon-facts.json
 *
 * QUARANTINED SIMULATOR OUTPUT (`report_eligible: false`). Every board here is the vendored Triangle
 * engine's (`runCaseOracle`), scoped by `verifiedIndex`, exactly the machinery `emit-opener-facts.ts`
 * uses. Which bag-2 and bag-3 shape was built has no second implementation, so nothing downstream
 * may carry a claim id or a ✓ for it. The route boards are `pipeline/openers/meisou-routes.json`
 * (gated by `extract_meisou_routes.py`); the rules below are the plan's, and each one is a mutant
 * in `pipeline/openers/stray-cannon.test.ts` that must turn the test red.
 *
 * THE WALK. Bag 1 and bag 2 are a descent that stops at the first failing node; bag-3 Perfect Clear
 * detection is NOT part of that descent and runs for every round whose bag 1 matched.
 *
 *  1. Bag 1, PLACED FIRST. The clean board after 7 locks against `bag1.z_right`, then `bag1.z_left`,
 *     as drawn and mirrored; the first match wins. Only when neither matches is the clean board
 *     after 6 locks compared with `bag1.z_hold`, and then the piece placed at lock 7 (0-based 6) is
 *     read and compared with the MIRROR-AWARE bag-1 Z (Z as drawn, S when the 6-lock match was
 *     mirrored). Not that piece -> `bag1.z_hold`, the only node that asserts a hold, because only
 *     here does the predicate test one. That piece -> the outcome `bag1.z_placed_elsewhere`. The
 *     reverse precedence (6 locks first) was revision 2's, and it named a hold the predicate never
 *     tested. `matched_at_6` is a FLAG, not a node: the 6-lock field matched, whatever the node.
 *  2. Bag 2. The clean board after 13 pieces (0-based lock 12), inside the verified prefix and
 *     before any garbage, against all five bag-2 boards. Handedness is measured independently of
 *     bag 1. The page's condition (「J before O」, …) is read off the round's own bag-2 order from
 *     `replay-facts.json`'s `seq`, with J<->L and S<->Z swapped first in a mirrored round, so the
 *     condition is always tested in the handedness the page draws.
 *  3. Bag 3. (a) An 8-line Perfect Clear (TST -> ... -> PC, 8 lines cumulative) is compared, by
 *     COLOUR, in a frame that keeps every row cleared after the TST, against the patterns of the
 *     round's own bag-2 branch FIRST; more than one match after that scoping throws. A PC with no
 *     bag-2 match, or matching none of its branch's patterns, is off the page. (b) The non-PC
 *     snapshot routes (TST donate, STSD) are matched only under their own branch.
 *
 * Variants are keyed `node` and never `kind`, and nothing counts nodes with an inline filter of
 * that field (`check_forecast_numerator`).
 *
 * STALENESS. The artefact records the md5 of every session's replays and replay-facts.json, of
 * `meisou-routes.json`, and of this file, so it goes stale loudly when a session lands, the data
 * moves or the code changes: `stray-cannon.test.ts` rebuilds it byte for byte.
 */
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { rowsFromBoard, occGrid, mirrorRows, keyOf, ROWS } from '../openers/match.ts';
import { discoverCorpus } from '../corpus-membership.ts';

const REPO = `${import.meta.dir}/../..`;
export const ROUTES_PATH = `${REPO}/pipeline/openers/meisou-routes.json`;
export const ARTEFACT_PATH = `${REPO}/analysis/stray-cannon-facts.json`;

/** Bag-1 sampling points: the Z-placed variants are drawn at 7 locks, the Z-held one at 6. */
export const BAG1_PLACED_LOCKS = 7;
export const BAG1_HOLD_LOCKS = 6;
/** Bag 2 is drawn after 13 pieces: the 0-based lock index of its board. */
export const BAG2_LOCK = 12;
/** Clear events (TST, PC) are looked for in the first EVENT_LOCKS locks (the probe's window). */
export const EVENT_LOCKS = 40;
/** Snapshot routes are looked for up to this many locks; a round digest keeps this many. */
export const SNAPSHOT_LOCKS = 46;
/** The bag-3 frame is compared over its bottom PC_ROWS rows; every PC pattern is at most this tall. */
export const PC_ROWS = 6;
/** Lines cleared by the first 8-line PC (TST 3 + TSD 2 + PC 3). */
export const PC_LINES = 8;

// ── round digests: everything `classify` reads, so the mutants in the test cost no re-simulation ──

export interface DigestLock {
  piece: string; cells: { col: number; row: number }[]; cleared: number; spin: string;
  allclear: boolean; clearedRows: number[];
}
export interface RoundDigest {
  session: string; file: string; round: number; user: string;
  /** the round's position in the session, from replay-facts.json (the label every page uses) */
  match: number;
  /** the 1-based index of `file` in a filename sort: never the label; kept for the mutant only */
  file_sort_index: number;
  /** the bag-2 piece order (7 letters), from replay-facts.json's `seq` */
  bag2_order: string;
  v: number; height: number; garbage: number[]; n_locks: number;
  locks: DigestLock[];
  /** trimmed board rows after each lock ('.' empty), null for an empty board */
  rows: (string[] | null)[];
}

function md5(buf: string | Buffer): string { return createHash('md5').update(buf).digest('hex'); }

/** One session through the oracle, reduced to what the classifier reads. */
export function digestSession(session: string, root = `${REPO}/sessions`): RoundDigest[] {
  const dir = `${root}/${session}`;
  const rf = JSON.parse(readFileSync(`${dir}/sim/replay-facts.json`, 'utf8'));
  const pos = new Map<string, { match: number; seq: string }>();
  for (const r of rf.rounds) pos.set(`${r.file}#${r.round}`, { match: r.match, seq: r.seq });
  const files = readdirSync(dir).filter(f => f.endsWith('.ttrm')).sort();
  const out: RoundDigest[] = [];
  for (const c of loadCases(dir)) {
    const p = pos.get(`${c.file}#${c.round}`);
    if (!p) throw new Error(`stray-cannon: ${session} ${c.file} r${c.round} has no replay-facts entry`);
    const r = runCaseOracle(c);
    const v = verifiedIndex(r, c.truth);
    const n = Math.min(r.locks.length, SNAPSHOT_LOCKS);
    const locks: DigestLock[] = [];
    const rows: (string[] | null)[] = [];
    for (let i = 0; i < n; i++) {
      const l = r.locks[i]!;
      locks.push({ piece: l.piece, cells: l.cells.map(q => ({ col: q.col, row: q.row })), cleared: l.cleared,
        spin: l.spin, allclear: l.allclear, clearedRows: [...(r.records[i]?.clearedRows ?? [])] });
      rows.push(rowsFromBoard(r.boards[i] as (string | null)[][]));
    }
    out.push({ session, file: c.file, round: c.round, user: c.user, match: p.match,
      file_sort_index: files.indexOf(c.file) + 1, bag2_order: p.seq.slice(7, 14),
      v, height: r.boards[0]?.length ?? 40, garbage: r.garbageEvents.map(g => g.lockIndex),
      n_locks: r.locks.length, locks, rows });
  }
  return out;
}

// ── the route boards ──────────────────────────────────────────────────────────────────────────

export interface RouteNode {
  id: string; bag: number; parent: string | null; rows?: string[]; node_kind?: string;
  unmatchable?: string; list?: string; condition?: any; locks?: number;
}
export interface Routes { nodes: RouteNode[] }
export function loadRoutes(path = ROUTES_PATH): Routes { return JSON.parse(readFileSync(path, 'utf8')); }

/** A board diagram prepared for exact matching: occupancy as drawn and mirrored, plus its colours. */
interface Diagram { id: string; rows: string[]; grid: string; mgrid: string }
const occOf = (rows: string[]) => rows.map(r => [...r].map(ch => (ch === '-' || ch === 'U') ? '.' : '#').join(''));
function diagram(n: RouteNode): Diagram {
  const occ = occOf(n.rows!);
  return { id: n.id, rows: n.rows!, grid: keyOf(occGrid(occ)), mgrid: keyOf(occGrid(mirrorRows(occ))) };
}
const measurable = (n: RouteNode) => !!n.rows && !n.unmatchable && !n.node_kind;

/** Colour check of an occupancy match: every letter (either case; upper-case Z is the bag-1 Z)
 *  must be that piece, `c` any filled cell. Mirroring swaps L<->J and S<->Z. */
function colourAgrees(board: string[], d: Diagram, mirrored: boolean): boolean {
  let pr = d.rows.map(x => x.toUpperCase());
  if (mirrored) pr = mirrorRows(pr);
  const pad = (a: string[]) => [...Array(Math.max(0, ROWS - a.length)).fill('----------'), ...a].slice(-ROWS);
  const A = pad(board.map(x => x.replace(/\./g, '-'))), B = pad(pr);
  for (let i = 0; i < ROWS; i++) for (let k = 0; k < 10; k++) {
    const b = B[i]![k]!;
    if (b !== '-' && b !== 'C' && b !== 'U' && A[i]![k] !== b) return false;
  }
  return true;
}

// ── the classifier ───────────────────────────────────────────────────────────────────────────

/** Each field turns ONE rule off; `stray-cannon.test.ts` requires every one of them to go red. */
export interface Mutants {
  noMirror?: boolean;            // compare as drawn only
  bag2Early?: boolean;           // sample bag 2 one lock early
  zHoldFirst?: boolean;          // revision 2's precedence: the 6-lock field before the placed ones
  noLock7Test?: boolean;         // every 6-lock-only match is a hold
  lock7MirrorUnaware?: boolean;  // the bag-1 Z is Z even in a mirrored round
  noSwap?: boolean;              // test the page condition on the raw order in a mirrored round
  noColour?: boolean;            // bag-3 patterns by occupancy only
  unscoped?: boolean;            // bag-3 candidates from every branch
  pcNeedsBag2?: boolean;         // PC detection only under a matched bag 2
  matchFromFilename?: boolean;   // label rounds by filename-sort index
  noGarbageStop?: boolean;       // ignore garbage before a sampling point
}

interface Match { id: string; mirrored: boolean; colour: boolean }

function matchAgainst(rows: string[] | null, ds: Diagram[], mut: Mutants): Match[] {
  if (!rows || rows.length > ROWS) return [];
  const g = keyOf(occGrid(rows));
  const out: Match[] = [];
  for (const d of ds) {
    const drawn = g === d.grid, mirror = !mut.noMirror && g === d.mgrid;
    if (!drawn && !mirror) continue;
    out.push({ id: d.id, mirrored: !drawn, colour: colourAgrees(rows, d, !drawn) });
  }
  return out;
}

const SWAP: Record<string, string> = { J: 'L', L: 'J', S: 'Z', Z: 'S' };
export function conditionHolds(cond: any, order: string, bag1: string): boolean | null {
  if (!cond) return null;
  if (cond.all) {
    for (const c of cond.all) {
      const [a, b] = c.before as [string, string];
      const ia = order.indexOf(a), ib = order.indexOf(b);
      if (ia < 0 || ib < 0) throw new Error(`stray-cannon: bag-2 order ${order} lacks ${a} or ${b}`);
      if (!(ia < ib)) return false;
    }
    return true;
  }
  if (cond.bag1) return bag1 === cond.bag1;
  // `{"early": "I"}`: the page gives no threshold for "early", so the condition is not decidable
  return null;
}

export interface Classified {
  cases: any[];
  opportunities: Record<string, Record<string, number>>;
  colour_disagree: string[];
  pc_garbage_in_window: string[];
  multi_resolved_by_branch: string[];
}

const label = (d: RoundDigest, mut: Mutants) =>
  `${d.session} m${mut.matchFromFilename ? d.file_sort_index : d.match}r${d.round + 1} ${d.user}`;

/** Classify every digested round. Pure: the same digests and mutants give the same output. */
export function classify(digests: RoundDigest[], routes: Routes, mut: Mutants = {}): Classified {
  const nodes = routes.nodes;
  const byId = new Map(nodes.map(n => [n.id, n]));
  const D = (id: string) => diagram(byId.get(id)!);
  const placed = [D('bag1.z_right'), D('bag1.z_left')];
  const hold = D('bag1.z_hold');
  const bag2 = nodes.filter(n => n.bag === 2 && measurable(n)).map(diagram);
  const patterns = nodes.filter(n => n.list && measurable(n));
  const snapshots = nodes.filter(n => n.bag === 3 && !n.list && measurable(n));

  const opp: Record<string, Record<string, number>> = {};
  const bump = (id: string, user: string) => { (opp[id] ??= {})[user] = (opp[id]![user] ?? 0) + 1; };
  const colourDisagree: string[] = [], pcGarbage: string[] = [], multi: string[] = [];
  const cases: any[] = [];

  for (const d of digests) {
    const garbageBefore = (n: number) => !mut.noGarbageStop && d.garbage.some(g => g < n);
    const clean = (n: number) => {
      if (d.v < n - 1 || garbageBefore(n) || d.n_locks < n) return false;
      for (let i = 0; i < n; i++) if (d.locks[i]!.cleared > 0) return false;
      return !!d.rows[n - 1];
    };
    const tag = label(d, mut);
    const keep = (ms: Match[], where: string) => {
      for (const m of ms) if (!m.colour) colourDisagree.push(`${tag} ${where} ${m.id}${m.mirrored ? ' (mirrored)' : ''}`);
      return ms.filter(m => m.colour);
    };

    // ── bag 1 ──
    const c7 = clean(BAG1_PLACED_LOCKS), c6 = clean(BAG1_HOLD_LOCKS);
    if (c7) { bump('bag1.z_right', d.user); bump('bag1.z_left', d.user); }
    if (c6) bump('bag1.z_hold', d.user);
    const at7 = c7 ? keep(matchAgainst(d.rows[BAG1_PLACED_LOCKS - 1]!, placed, mut), 'bag1@7') : [];
    // the flag is occupancy, like emit-opener-facts' `exact`: colour never decides it
    const at6all = c6 ? matchAgainst(d.rows[BAG1_HOLD_LOCKS - 1]!, [hold], mut) : [];
    const at6 = keep(at6all, 'bag1@6');
    let node: string | null = null, mirrored = false, lock = -1;
    const lock7 = d.locks[BAG1_PLACED_LOCKS - 1]?.piece ?? null;
    const fallback = () => {
      if (!at6.length) return false;
      mirrored = at6[0]!.mirrored; lock = BAG1_HOLD_LOCKS - 1;
      const z = mirrored && !mut.lock7MirrorUnaware ? 'S' : 'Z';
      node = mut.noLock7Test || lock7 !== z ? 'bag1.z_hold' : 'bag1.z_placed_elsewhere';
      if (node === 'bag1.z_placed_elsewhere') lock = BAG1_PLACED_LOCKS - 1;
      return true;
    };
    if (mut.zHoldFirst && fallback()) { /* revision 2's order */ }
    else if (at7.length) { node = at7[0]!.id; mirrored = at7[0]!.mirrored; lock = BAG1_PLACED_LOCKS - 1; }
    else fallback();
    if (!node) continue;

    const c: any = {
      session: d.session, file: d.file, round_index0: d.round,
      match: mut.matchFromFilename ? d.file_sort_index : d.match, round: d.round + 1, player: d.user,
      verified_to: d.v,
      bag1: { node, mirrored, lock, lock7_piece: lock7, matched_at_6: at6all.length > 0,
              matched_variants: [...at7.map(m => m.id + (m.mirrored ? ' (mirrored)' : '') + ' @7'),
                                 ...at6.map(m => m.id + (m.mirrored ? ' (mirrored)' : '') + ' @6')] },
      bag2: null as any, pc: null as any, snapshots: [] as any[],
    };
    let deepest = node, deepestLock = lock;

    // ── bag 2 ──
    const L2 = mut.bag2Early ? BAG2_LOCK - 1 : BAG2_LOCK;
    let branch: string | null = null;
    if (clean(L2 + 1)) {
      for (const b of bag2) bump(b.id, d.user);
      const hits = keep(matchAgainst(d.rows[L2]!, bag2, mut), 'bag2');
      if (hits.length > 1) throw new Error(`stray-cannon: ${tag} matches ${hits.length} bag-2 boards`);
      const m = hits[0];
      const flip = m ? m.mirrored : mirrored;
      const order = flip && !mut.noSwap ? [...d.bag2_order].map(x => SWAP[x] ?? x).join('') : d.bag2_order;
      const met = nodes.filter(n => n.bag === 2 && n.condition && conditionHolds(n.condition, order, node!) === true)
        .map(n => n.id);
      c.bag2 = { node: m?.id ?? null, mirrored: m ? m.mirrored : null, lock: L2,
        order_as_drawn: order, conditions_met: met,
        condition_met: m ? conditionHolds(byId.get(m.id)!.condition, order, node) : null,
        handedness_matches_bag1: m ? m.mirrored === mirrored : null };
      if (m) {
        branch = m.id; deepest = m.id; deepestLock = L2;
        for (const p of patterns) if (p.parent === branch) bump(p.id, d.user);
      }
    }

    // ── bag 3 (a): 8-line Perfect Clear, for every round whose bag 1 matched ──
    let cum = 0; const ev: { i: number; piece: string; spin: string; lines: number; cum: number; pc: boolean }[] = [];
    for (let i = 0; i < Math.min(d.locks.length, EVENT_LOCKS); i++) {
      const l = d.locks[i]!; cum += l.cleared;
      if (l.cleared > 0) ev.push({ i, piece: l.piece, spin: l.spin, lines: l.cleared, cum, pc: l.allclear });
    }
    const tst = ev.find(e => e.piece === 'T' && e.spin === 'full' && e.lines === 3);
    const pc = ev.find(e => e.pc);
    if (pc && pc.cum === PC_LINES && !(mut.pcNeedsBag2 && !branch)) {
      const rec: any = { lock: pc.i, verified: pc.i <= d.v, node: null, mirrored: null, off_page_under: null };
      if (!tst || tst.i >= pc.i) {
        rec.off_page_under = `${deepest}.other`; rec.reason = 'no TST before the PC';
      } else if (!mut.noGarbageStop && d.garbage.some(g => g > tst.i && g <= pc.i)) {
        pcGarbage.push(tag); rec.reason = 'garbage between the TST and the PC';
      } else {
        const comp = composite(d, tst.i, pc.i);
        const test = (ns: RouteNode[]) => {
          const hit: { id: string; mirrored: boolean }[] = [];
          for (const p of ns) for (const mir of [false, true]) {
            if (mir && mut.noMirror) continue;
            if (patternMatches(comp, p.rows!, mir, !mut.noColour)) hit.push({ id: p.id, mirrored: mir });
          }
          return hit;
        };
        const scope = mut.unscoped ? patterns : branch ? patterns.filter(p => p.parent === branch) : [];
        const hits = test(scope);
        if (hits.length > 1)
          throw new Error(`stray-cannon: ${tag} PC matches ${hits.map(h => h.id + (h.mirrored ? '(m)' : '')).join(', ')}`);
        if (hits.length === 1 && test(patterns).length > 1) multi.push(tag);
        if (hits[0]) {
          rec.node = hits[0].id; rec.mirrored = hits[0].mirrored;
          deepest = hits[0].id; deepestLock = pc.i;
        } else rec.off_page_under = `${deepest}.other`;
      }
      c.pc = rec;
    }

    // ── bag 3 (b): snapshot routes, only under their own branch ──
    if (branch) {
      let parent: string = branch, from = L2 + 1;
      for (;;) {
        const child = snapshots.find(s => s.parent === parent);
        if (!child) break;
        const dg = diagram(child);
        let found = -1, fm = false;
        for (let i = from; i < d.locks.length; i++) {
          if (garbageBefore(i + 1)) break;
          const hit = keep(matchAgainst(d.rows[i]!, [dg], mut), 'snapshot');
          if (hit.length) { found = i; fm = hit[0]!.mirrored; break; }
        }
        bump(child.id, d.user);
        if (found < 0) break;
        c.snapshots.push({ node: child.id, lock: found, mirrored: fm, verified: found <= d.v });
        if (!c.pc?.node) { deepest = child.id; deepestLock = found; }
        parent = child.id; from = found + 1;
      }
    }

    c.deepest = deepest; c.deepest_lock = deepestLock; c.verified = deepestLock <= d.v;
    cases.push(c);
  }
  // label order, never load order: loadCases sorts by FILENAME, which is not the match position
  cases.sort((a, b) => a.session.localeCompare(b.session) || a.match - b.match
    || a.round_index0 - b.round_index0 || a.player.localeCompare(b.player));
  return { cases, opportunities: opp, colour_disagree: colourDisagree.sort(),
           pc_garbage_in_window: pcGarbage.sort(), multi_resolved_by_branch: multi.sort() };
}

/** The bag-3 frame: the board after the TST, then every later piece placed into it with every row
 *  it clears KEPT, up to and including the PC lock. Bottom PC_ROWS rows, top to bottom; pre-TST
 *  cells lower-case (`g` for garbage), later pieces upper-case. */
export function composite(d: RoundDigest, tstI: number, end: number): string[] {
  const H = d.height;
  const trimmed = d.rows[tstI] ?? [];
  const full: string[] = [...Array(H - trimmed.length).fill('..........'), ...trimmed];
  const vrows: string[][] = [];
  for (let rr = H - 1; rr >= 0; rr--)
    vrows.push([...full[rr]!].map(ch => ch === '.' ? '-' : /[IOTSZJL]/.test(ch) ? ch.toLowerCase() : 'g'));
  let vmap = Array.from({ length: H }, (_, rr) => H - 1 - rr);
  for (let j = tstI + 1; j <= end; j++) {
    const l = d.locks[j]!;
    for (const q of l.cells) {
      if (q.row < 0 || q.row >= H) throw new Error(`stray-cannon: ${d.session} ${d.file} r${d.round} lock ${j} off the board`);
      const vr = vrows[vmap[q.row]!]!;
      if (vr[q.col] !== '-') throw new Error(`stray-cannon: ${d.session} ${d.file} r${d.round} lock ${j} overlaps`);
      vr[q.col] = l.piece;
    }
    const cl = new Set(l.clearedRows);
    if (cl.size) {
      const nm: number[] = new Array(H); let k = H - 1;
      for (let rr = H - 1; rr >= 0; rr--) { if (cl.has(rr)) continue; nm[k--] = vmap[rr]!; }
      while (k >= 0) { vrows.push(Array(10).fill('-')); nm[k--] = vrows.length - 1; }
      vmap = nm;
    }
  }
  return vrows.slice(0, PC_ROWS).reverse().map(x => x.join(''));
}

/** The inverse of `composite()`'s `vmap`, for a builder rather than a reader: which diagram row each
 *  engine row (y-UP) is, starting bottom-aligned when a bag starts. `stray-cannon-demos.ts` places
 *  a piece only while every row it is drawn on is still on the board. One sibling of the frame rule,
 *  beside it, so the two cannot drift. */
export const initialRowmap = (rows = 40): number[] => Array.from({ length: rows }, (_, e) => e);
/** After a lock clears `cleared` (pre-clear y-UP rows): those rows' ids leave, fresh ids (never a
 *  diagram row) enter at the top. */
export function advanceRowmap(rowmap: number[], cleared: number[]): number[] {
  const cl = new Set(cleared);
  const keep = rowmap.filter((_, e) => !cl.has(e));
  let fresh = Math.max(1000, ...rowmap) + 1;
  while (keep.length < rowmap.length) keep.push(fresh++);
  return keep;
}

/** A PC pattern against the frame: `U` is the T, `c` a pre-TST cell, a letter that piece (placed
 *  before or after the TST). With `colour` off, only occupancy and the `c` cells are compared. */
export function patternMatches(comp: string[], rows: string[], mirrored: boolean, colour: boolean): boolean {
  let pr = rows.map(x => x.toUpperCase().replace(/U/g, 'T'));
  if (mirrored) pr = mirrorRows(pr);
  if (pr.length > PC_ROWS) return false;
  const pad = [...Array(PC_ROWS - pr.length).fill('----------'), ...pr];
  for (let i = 0; i < PC_ROWS; i++) for (let k = 0; k < 10; k++) {
    const a = comp[i]![k]!, b = pad[i]![k]!;
    if (b === '-') { if (a !== '-') return false; continue; }
    if (a === '-') return false;
    if (b === 'C') { if (/[A-Z]/.test(a)) return false; continue; }
    if (colour && a.toUpperCase() !== b) return false;
  }
  return true;
}

// ── the artefact ─────────────────────────────────────────────────────────────────────────────

export function inputs(sessions: string[], root = `${REPO}/sessions`) {
  return {
    sessions: sessions.map(s => {
      const dir = `${root}/${s}`;
      const h = createHash('md5');
      for (const f of readdirSync(dir).filter(f => f.endsWith('.ttrm')).sort()) h.update(f).update(readFileSync(`${dir}/${f}`));
      return { session: s, replays_md5: h.digest('hex'), replay_facts_md5: md5(readFileSync(`${dir}/sim/replay-facts.json`)) };
    }),
    routes_md5: md5(readFileSync(ROUTES_PATH)),
    emitter_md5: md5(readFileSync(import.meta.path)),
  };
}

/** Assemble the artefact from classified rounds. */
export function assemble(cls: Classified, routes: Routes, sessions: string[], inp: ReturnType<typeof inputs>) {
  const users = [...new Set(cls.cases.map(c => c.player))].sort();
  const perUser = () => Object.fromEntries(users.map(u => [u, 0])) as Record<string, number>;
  const tally: Record<string, { cases: Record<string, number>; other: Record<string, number> }> = {};
  const T = (id: string) => (tally[id] ??= { cases: perUser(), other: perUser() });
  const nodeIds = [...routes.nodes.map(n => n.id), 'bag1.z_placed_elsewhere'];
  for (const id of nodeIds) T(id);
  for (const c of cls.cases) {
    const path: string[] = [c.bag1.node];
    if (c.bag2?.node) path.push(c.bag2.node);
    for (const s of c.snapshots) path.push(s.node);
    if (c.pc?.node) path.push(c.pc.node);
    for (const id of path) T(id).cases[c.player]!++;
    if (c.pc?.off_page_under) T(c.pc.off_page_under.replace(/\.other$/, '')).other[c.player]!++;
  }
  const byId = new Map(routes.nodes.map(n => [n.id, n]));
  const nodes = nodeIds.map(id => {
    const n = byId.get(id);
    const measured = id === 'bag1.z_placed_elsewhere' || (!!n && measurable(n));
    const t = tally[id]!;
    const sum = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
    const oppSrc = id === 'bag1.z_placed_elsewhere' ? cls.opportunities['bag1.z_hold'] : cls.opportunities[id];
    const opp = Object.fromEntries(users.map(u => [u, oppSrc?.[u] ?? 0]));
    return measured
      ? { id, measured: true, page_node: !!n, cases: sum(t.cases), cases_by_player: t.cases,
          opportunities: sum(opp), opportunities_by_player: opp,
          pc_off_page: sum(t.other), pc_off_page_by_player: t.other }
      : { id, measured: false, why: n?.unmatchable ? `unmatchable: ${n.unmatchable}` : `${n?.node_kind}` };
  });
  // page condition vs branch actually built, per branch, in the handedness the page draws
  const conditions: Record<string, Record<string, number>> = {};
  for (const c of cls.cases) {
    if (!c.bag2?.node) continue;
    const k = c.bag2.conditions_met.join('+') || '(none)';
    (conditions[c.bag2.node] ??= {})[k] = (conditions[c.bag2.node]![k] ?? 0) + 1;
  }
  for (const k of Object.keys(conditions)) conditions[k] = Object.fromEntries(Object.entries(conditions[k]!).sort());
  const name = (c: any) => `${c.session} m${c.match}r${c.round} ${c.player}`;
  return {
    schema: 'stray-cannon-facts/1',
    report_eligible: false,
    means: 'for every corpus round whose bag 1 is shiwehi.com\'s 迷走砲 bag 1 cell for cell (as drawn or mirrored), '
      + 'the deepest node of that page\'s route tree the round reaches, and how often each node\'s sampling point was reached clean',
    not_eligible_because: 'every board is the vendored Triangle engine\'s; which bag-2 and bag-3 shape was built has no second implementation. '
      + 'The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'opportunities count rounds that reached a node\'s sampling point clean (inside the verified prefix, no clear, no garbage before it); '
      + 'bag-3 nodes have no separate sampling point and count the rounds that reached their parent. A hold is asserted only by the lock-7 piece test.',
    rules: {
      bag1_placed_locks: BAG1_PLACED_LOCKS, bag1_hold_locks: BAG1_HOLD_LOCKS, bag2_lock_index: BAG2_LOCK,
      event_locks: EVENT_LOCKS, snapshot_locks: SNAPSHOT_LOCKS, pc_rows: PC_ROWS, pc_lines: PC_LINES,
      precedence: 'z_right, then z_left (7 locks); only if neither, z_hold (6 locks) split by the lock-7 piece against the mirror-aware bag-1 Z',
      condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
    },
    inputs: inp,
    sessions,
    outcomes: ['bag1.z_placed_elsewhere'],
    nodes,
    conditions,
    lists: {
      z_hold_bag1: cls.cases.filter(c => c.bag1.node === 'bag1.z_hold').map(name),
      z_placed_elsewhere_bag1: cls.cases.filter(c => c.bag1.node === 'bag1.z_placed_elsewhere').map(name),
      z_left_bag1: cls.cases.filter(c => c.bag1.node === 'bag1.z_left').map(name),
      i_early: cls.cases.filter(c => c.bag2?.node === '2.i_early').map(c => name(c) + (c.bag2.mirrored ? ' (mirrored)' : '')),
      tst_donate: cls.cases.filter(c => c.snapshots.some((s: any) => s.node === '2.normal_OS.tst_donate')).map(name),
      pc_off_page: cls.cases.filter(c => c.pc?.off_page_under).map(c => `${name(c)} under ${c.pc.off_page_under}`),
      bag2_handedness_mismatch: cls.cases.filter(c => c.bag2?.handedness_matches_bag1 === false).map(name),
      multi_colour_resolved_by_branch: cls.multi_resolved_by_branch,
      colour_disagree: cls.colour_disagree,
      pc_garbage_in_window: cls.pc_garbage_in_window,
    },
    cases: cls.cases,
  };
}

/** One case per line: diffable, and a third the size of a fully indented dump. */
export function serialise(out: any): string {
  const { cases, ...rest } = out;
  const head = JSON.stringify({ ...rest, cases: '\u0000' }, null, 1);
  return head.replace('"\\u0000"', '[\n' + cases.map((c: any) => '  ' + JSON.stringify(c)).join(',\n') + '\n ]') + '\n';
}

export function corpus(): string[] { return discoverCorpus(`${REPO}/sessions`); }

export function build(mut: Mutants = {}, digests?: RoundDigest[]) {
  const sessions = corpus();
  const ds = digests ?? sessions.flatMap(s => digestSession(s));
  const routes = loadRoutes();
  return assemble(classify(ds, routes, mut), routes, sessions, inputs(sessions));
}

if (import.meta.main) {
  const outIx = process.argv.indexOf('--out');
  const text = serialise(build());
  if (outIx > 0) writeFileSync(process.argv[outIx + 1]!, text);
  else process.stdout.write(text);
}
