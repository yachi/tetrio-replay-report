/**
 * The shared ROUTE CLASSIFIER: for one shiwehi.com opener route page (迷走砲, はちみつ砲, …), the
 * deepest node of its route tree that each corpus round reaches, over every session at once. The
 * opener-specific part — which nodes, which locks, which strings — is a `RouteProfile`
 * (`route-profile.ts`); every RULE is here, once.
 *
 *   bun pipeline/sim/emit-route-facts.ts --opener <key> --out <artefact>
 *   bun pipeline/sim/emit-stray-cannon-facts.ts --out analysis/stray-cannon-facts.json   # 迷走砲's shim
 *
 * QUARANTINED SIMULATOR OUTPUT (`report_eligible: false`). Every board here is the vendored Triangle
 * engine's (`runCaseOracle`), scoped by `verifiedIndex`, exactly the machinery `emit-opener-facts.ts`
 * uses. Which bag-2 and bag-3 shape was built has no second implementation, so nothing downstream
 * may carry a claim id or a ✓ for it. The route boards are each opener's routes JSON (gated by its
 * `extract_*_routes.py` through `route_transcription.py`); each rule below is a mutant in that
 * opener's test, which must turn red.
 *
 * THE WALK. Bag 1 and bag 2 are a descent that stops at the first failing node; bag-3 Perfect Clear
 * detection is NOT part of that descent and runs for every round whose bag 1 matched.
 *
 *  1. Bag 1: the profile's STAGES in order (迷走砲: the Z-placed boards at 7 locks, then the Z-held
 *     board at 6). A stage compares its clean board with its nodes, as drawn and mirrored; the first
 *     stage with a colour match decides. A stage with a HOLD SPLIT asserts a hold only when the piece
 *     placed at its `atLock` is not the MIRROR-AWARE held piece; when it is, the round is the outcome
 *     `elsewhereNode` (the piece was placed somewhere off the page). The profile's `flag` is a FLAG,
 *     not a node: its stage matched by occupancy, whatever the node.
 *  2. Bag 2. The board after the profile's `bag2Lock`, inside the verified prefix, against every
 *     bag-2 board. More than one colour match throws. Handedness is measured independently of bag 1.
 *     The page's condition is read off the round's own bag-2 order from `replay-facts.json`'s `seq`,
 *     with J<->L and S<->Z swapped first in a mirrored round. Garbage: `refuse` (no garbage before the
 *     sample) or `strip` (complete garbage rows stripped from the bottom first).
 *  3. Bag 3. (a) A Perfect Clear of `pcLines` cumulative lines after the profile's `pcAfter` clear
 *     (a TST) is compared, by COLOUR, in a frame that keeps every row cleared after it, against the
 *     patterns whose `parent` is the round's bag-2 node's GROUP (`group` on the node, else its id);
 *     more than one match after that scoping throws. (b) The non-PC snapshot routes are matched only
 *     under their own branch; where a node has several snapshot children, the earliest found wins.
 *
 * Variants are keyed `node` and never `kind`, and nothing counts nodes with an inline filter of
 * that field (`check_forecast_numerator`).
 *
 * STALENESS. The artefact records the md5 of every session's replays and replay-facts.json, of the
 * routes JSON, and of the profile's `hashFiles.classifier` (this file, the profile type, the
 * opener's profile and its entry file), so it goes stale loudly when a session lands, the data moves
 * or the code changes.
 */
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { rowsFromBoard, occGrid, mirrorRows, keyOf, ROWS } from '../openers/match.ts';
import { discoverCorpus } from '../corpus-membership.ts';
import type { RouteProfile } from './route-profile.ts';

export const REPO = `${import.meta.dir}/../..`;
export const SESSIONS_ROOT = `${REPO}/sessions`;

// ── round digests: everything `classify` reads, so the mutants in a test cost no re-simulation ──

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
  /** trimmed board rows after each lock ('.' empty, 'G' garbage), null for an empty board */
  rows: (string[] | null)[];
}

function md5(buf: string | Buffer): string { return createHash('md5').update(buf).digest('hex'); }

/** One session through the oracle, reduced to what the classifier reads. Opener-independent but for
 *  how many locks it keeps, so two openers with the same `snapshotLocks` can share one digest. */
export function digestSession(session: string, root = SESSIONS_ROOT,
                              opts: { snapshotLocks: number; tag: string }): RoundDigest[] {
  const dir = `${root}/${session}`;
  const rf = JSON.parse(readFileSync(`${dir}/sim/replay-facts.json`, 'utf8'));
  const pos = new Map<string, { match: number; seq: string }>();
  for (const r of rf.rounds) pos.set(`${r.file}#${r.round}`, { match: r.match, seq: r.seq });
  const files = readdirSync(dir).filter(f => f.endsWith('.ttrm')).sort();
  const out: RoundDigest[] = [];
  for (const c of loadCases(dir)) {
    const p = pos.get(`${c.file}#${c.round}`);
    if (!p) throw new Error(`${opts.tag}: ${session} ${c.file} r${c.round} has no replay-facts entry`);
    const r = runCaseOracle(c);
    const v = verifiedIndex(r, c.truth);
    const n = Math.min(r.locks.length, opts.snapshotLocks);
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
  /** several bag-2 boards sharing one bag-3 list: the lists and snapshots hang off the group */
  group?: string;
  /** a node that is another node mirrored: counted there, never matched on its own */
  mirror_of?: string;
}
export interface Routes { nodes: RouteNode[] }
export function loadRoutes(path: string): Routes { return JSON.parse(readFileSync(path, 'utf8')); }

/** A board diagram prepared for exact matching: occupancy as drawn and mirrored, plus its colours. */
interface Diagram { id: string; rows: string[]; grid: string; mgrid: string }
const occOf = (rows: string[]) => rows.map(r => [...r].map(ch => (ch === '-' || ch === 'U') ? '.' : '#').join(''));
function diagram(n: RouteNode): Diagram {
  const occ = occOf(n.rows!);
  return { id: n.id, rows: n.rows!, grid: keyOf(occGrid(occ)), mgrid: keyOf(occGrid(mirrorRows(occ))) };
}
export const measurable = (n: RouteNode) => !!n.rows && !n.unmatchable && !n.node_kind && !n.mirror_of;

/** Colour check of an occupancy match: every letter (either case; an upper-case letter is a piece of
 *  an earlier bag, drawn in colour) must be that piece, `c` any filled cell. Mirroring swaps L<->J and
 *  S<->Z. */
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

/** Complete garbage rows stripped from the bottom of a trimmed board (`bag2Garbage: 'strip'`): a row
 *  is stripped only when every filled cell in it is garbage. A board with garbage left anywhere else
 *  is not comparable (null). */
export function stripGarbage(rows: string[] | null): { rows: string[] | null; stripped: number } {
  if (!rows) return { rows: null, stripped: 0 };
  let k = rows.length, stripped = 0;
  while (k > 0 && rows[k - 1]!.includes('G') && /^[.G]+$/.test(rows[k - 1]!)) { k--; stripped++; }
  const left = rows.slice(0, k);
  if (!left.length || left.some(r => r.includes('G'))) return { rows: null, stripped };
  return { rows: left, stripped };
}

// ── the classifier ───────────────────────────────────────────────────────────────────────────

/** Each field turns ONE rule off; each opener's test requires the ones it exercises to go red. */
export interface Mutants {
  noMirror?: boolean;            // compare as drawn only
  bag2Early?: boolean;           // sample bag 2 one lock early
  zHoldFirst?: boolean;          // the hold stage before the placed ones (迷走砲 revision 2's order)
  noLock7Test?: boolean;         // every hold-stage match is a hold (no lock-N piece test)
  lock7MirrorUnaware?: boolean;  // the held piece is the drawn letter even in a mirrored round
  noSwap?: boolean;              // test the page condition on the raw order in a mirrored round
  noColour?: boolean;            // bag-3 patterns by occupancy only
  unscoped?: boolean;            // bag-3 candidates from every branch
  pcNeedsBag2?: boolean;         // PC detection only under a matched bag 2
  matchFromFilename?: boolean;   // label rounds by filename-sort index
  noGarbageStop?: boolean;       // ignore garbage before a sampling point
  noGroupScope?: boolean;        // scope bag-3 lists by the bag-2 node id, not its group
  noGarbageStrip?: boolean;      // a 'strip' profile refuses garbage like a 'refuse' one
  pcLinesOff?: boolean;          // any Perfect Clear, whatever its cumulative line count
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

/** `bag2Explain` compares boards up to this tall (a drawing is at most ROWS; the extra piece is not). */
const NEAR_ROWS = 12;

const SWAP: Record<string, string> = { J: 'L', L: 'J', S: 'Z', Z: 'S' };
export function conditionHolds(cond: any, order: string, bag1: string, tag = 'route'): boolean | null {
  if (!cond) return null;
  if (cond.all) {
    for (const c of cond.all) {
      const [a, b] = c.before as [string, string];
      const ia = order.indexOf(a), ib = order.indexOf(b);
      if (ia < 0 || ib < 0) throw new Error(`${tag}: bag-2 order ${order} lacks ${a} or ${b}`);
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
export function classify(P: RouteProfile, digests: RoundDigest[], routes: Routes, mut: Mutants = {}): Classified {
  const nodes = routes.nodes;
  const byId = new Map(nodes.map(n => [n.id, n]));
  const D = (id: string) => diagram(byId.get(id)!);
  const stages = P.bag1.stages.map(s => ({ ...s, diagrams: s.nodes.map(D) }));
  const holdStage = stages.find(s => s.holdSplit);
  const bag2 = nodes.filter(n => n.bag === 2 && measurable(n)).map(diagram);
  const patterns = nodes.filter(n => n.list && n.bag === 3 && measurable(n));
  const snapshots = nodes.filter(n => n.bag === 3 && !n.list && measurable(n));
  const groupOf = (id: string) => mut.noGroupScope ? id : (byId.get(id)?.group ?? id);
  const strip = P.bag2Garbage === 'strip' && !mut.noGarbageStrip;

  const opp: Record<string, Record<string, number>> = {};
  const bump = (id: string, user: string) => { (opp[id] ??= {})[user] = (opp[id]![user] ?? 0) + 1; };
  const colourDisagree: string[] = [], pcGarbage: string[] = [], multi: string[] = [];
  const cases: any[] = [];

  for (const d of digests) {
    const garbageBefore = (n: number) => !mut.noGarbageStop && d.garbage.some(g => g < n);
    const noClearBefore = (n: number) => {
      if (d.v < n - 1 || d.n_locks < n) return false;
      for (let i = 0; i < n; i++) if (d.locks[i]!.cleared > 0) return false;
      return !!d.rows[n - 1];
    };
    const clean = (n: number) => !garbageBefore(n) && noClearBefore(n);
    /** the board compared at lock index i past bag 1: as is ('refuse'), or garbage-stripped */
    const board = (i: number) => strip ? stripGarbage(d.rows[i] ?? null) : { rows: d.rows[i] ?? null, stripped: 0 };
    const tag = label(d, mut);
    // a colour disagreement is a match by occupancy that NO candidate of the same call agrees with
    // in colour: sibling boards sharing one occupancy (はちみつ砲's five bag-2 variants) are decided
    // by colour, and the siblings that lose are not disagreements
    const keep = (ms: Match[], where: string) => {
      const agree = ms.filter(m => m.colour);
      if (!agree.length)
        for (const m of ms) colourDisagree.push(`${tag} ${where} ${m.id}${m.mirrored ? ' (mirrored)' : ''}`);
      return agree;
    };
    /** `bag2Explain`: the board before the spin at lock `spinAt`, by occupancy against every bag-2
     *  board, in this order of preference: a strict SUBSET (the spin came before the drawn board was
     *  complete); a SUPERSET by exactly four cells (a piece's worth, whichever pieces they belong to);
     *  or one piece MOVED (the drawn board
     *  less four cells of one piece, plus four cells of that same piece elsewhere). Reported by GROUP,
     *  since sibling forms share one occupancy; `extra` is the letters of the cells off the drawing. */
    const explainMiss = (spinAt: number) => {
      if (spinAt < 1) return null;
      // taller than a drawing is allowed here: an extra piece stood on top is what this looks for
      const pre = board(spinAt - 1).rows;
      if (!pre || pre.length > NEAR_ROWS) return null;
      const padded = [...Array(NEAR_ROWS - pre.length).fill('..........'), ...pre];
      const mine = new Set<number>();
      padded.forEach((r, y) => [...r].forEach((ch, x) => { if (ch !== '.') mine.add(y * 10 + x); }));
      const letters = (qs: number[], rows: string[]) => [...new Set(qs.map(q => rows[Math.floor(q / 10)]![q % 10]!))].sort().join('');
      const hits: { kind: string; group: string; mirrored: boolean; cells: number; extra: string }[] = [];
      for (const dg of bag2) for (const mir of [false, true]) {
        if (mir && mut.noMirror) continue;
        const drawn = (mir ? mirrorRows(dg.rows.map(x => x.toUpperCase())) : dg.rows.map(x => x.toUpperCase()));
        const dpad = [...Array(NEAR_ROWS - drawn.length).fill('----------'), ...drawn];
        const theirs = new Set<number>();
        dpad.forEach((r, y) => [...r].forEach((ch, x) => { if (ch !== '-' && ch !== 'U') theirs.add(y * 10 + x); }));
        const missing = [...theirs].filter(q => !mine.has(q)), extra = [...mine].filter(q => !theirs.has(q));
        const hit = (kind: string, cells: number) =>
          hits.push({ kind, group: groupOf(dg.id), mirrored: mir, cells, extra: letters(extra, padded) });
        if (extra.length === 0 && missing.length > 0) hit('subset', missing.length);
        else if (missing.length === 0 && extra.length === 4) hit('superset', 4);
        else if (missing.length === 4 && extra.length === 4) {
          const was = letters(missing, dpad), now = letters(extra, padded);
          if (was.length === 1 && was === now) hit('moved', 4);
        }
      }
      for (const kind of ['subset', 'superset', 'moved']) {
        const hs = hits.filter(h => h.kind === kind);
        if (!hs.length) continue;
        return { kind, groups: [...new Set(hs.map(x => x.group))], mirrored: hs[0]!.mirrored,
                 lock: spinAt - 1, cells: hs[0]!.cells, extra: hs[0]!.extra };
      }
      return null;
    };

    // ── bag 1 ──
    const seen = stages.map(s => {
      const ok = clean(s.locks);
      if (ok) for (const id of s.nodes) bump(id, d.user);
      const all = ok ? matchAgainst(d.rows[s.locks - 1]!, s.diagrams, mut) : [];
      return { s, all, kept: keep(all, `bag1@${s.locks}`) };
    });
    let node: string | null = null, mirrored = false, lock = -1;
    const hs = holdStage?.holdSplit;
    const lockPiece = hs ? d.locks[hs.atLock - 1]?.piece ?? null : null;
    const order = mut.zHoldFirst ? [...seen.filter(x => x.s.holdSplit), ...seen.filter(x => !x.s.holdSplit)] : seen;
    for (const x of order) {
      if (!x.kept.length) continue;
      mirrored = x.kept[0]!.mirrored; lock = x.s.locks - 1;
      const h = x.s.holdSplit;
      if (h) {
        const held = mirrored && !mut.lock7MirrorUnaware ? h.mirrorPiece : h.piece;
        node = mut.noLock7Test || lockPiece !== held ? h.holdNode : h.elsewhereNode;
        if (node === h.elsewhereNode) lock = h.atLock - 1;
      } else node = x.kept[0]!.id;
      break;
    }
    if (!node) continue;
    const flagStage = seen[P.bag1.flag.stage]!;

    const c: any = {
      session: d.session, file: d.file, round_index0: d.round,
      match: mut.matchFromFilename ? d.file_sort_index : d.match, round: d.round + 1, player: d.user,
      verified_to: d.v,
      bag1: { node, mirrored, lock, [P.bag1.lockPieceField]: lockPiece, [P.bag1.flag.field]: flagStage.all.length > 0,
              matched_variants: seen.flatMap(x => x.kept.map(m => m.id + (m.mirrored ? ' (mirrored)' : '') + ` @${x.s.locks}`)) },
      bag2: null as any, pc: null as any, snapshots: [] as any[],
    };
    let deepest = node, deepestLock = lock;

    // ── bag 2 ──
    const L2 = mut.bag2Early ? P.bag2Lock - 1 : P.bag2Lock;
    let branch: string | null = null;
    if (strip ? noClearBefore(L2 + 1) : clean(L2 + 1)) {
      for (const b of bag2) bump(b.id, d.user);
      const bd = board(L2);
      const hits = keep(matchAgainst(bd.rows, bag2, mut), 'bag2');
      if (hits.length > 1) throw new Error(`${P.tag}: ${tag} matches ${hits.length} bag-2 boards`);
      const m = hits[0];
      const flip = m ? m.mirrored : mirrored;
      const order = flip && !mut.noSwap ? [...d.bag2_order].map(x => SWAP[x] ?? x).join('') : d.bag2_order;
      const met = nodes.filter(n => n.bag === 2 && n.condition && conditionHolds(n.condition, order, node!, P.tag) === true)
        .map(n => n.id);
      c.bag2 = { node: m?.id ?? null, mirrored: m ? m.mirrored : null, lock: L2,
        order_as_drawn: order, conditions_met: met,
        condition_met: m ? conditionHolds(byId.get(m.id)!.condition, order, node, P.tag) : null,
        handedness_matches_bag1: m ? m.mirrored === mirrored : null };
      if (strip) c.bag2.garbage_rows_stripped = bd.stripped;
      if (m) {
        branch = m.id; deepest = m.id; deepestLock = L2;
        for (const p of patterns) if (p.parent === groupOf(branch)) bump(p.id, d.user);
      }
    }

    // ── bag 3 (a): the Perfect Clear, for every round whose bag 1 matched ──
    let cum = 0; const ev: { i: number; piece: string; spin: string; lines: number; cum: number; pc: boolean }[] = [];
    for (let i = 0; i < Math.min(d.locks.length, P.eventLocks); i++) {
      const l = d.locks[i]!; cum += l.cleared;
      if (l.cleared > 0) ev.push({ i, piece: l.piece, spin: l.spin, lines: l.cleared, cum, pc: l.allclear });
    }
    const A = P.pcAfter;
    const tst = ev.find(e => e.piece === A.piece && e.spin === A.spin && e.lines === A.lines);
    const pc = ev.find(e => e.pc);
    if (pc && (mut.pcLinesOff || pc.cum === P.pcLines) && !(mut.pcNeedsBag2 && !branch)) {
      const rec: any = { lock: pc.i, verified: pc.i <= d.v, node: null, mirrored: null, off_page_under: null };
      if (!tst || tst.i >= pc.i) {
        rec.off_page_under = `${deepest}.other`; rec.reason = 'no TST before the PC';
      } else if (!mut.noGarbageStop && d.garbage.some(g => g > tst.i && g <= pc.i)) {
        pcGarbage.push(tag); rec.reason = 'garbage between the TST and the PC';
      } else {
        const comp = composite(d, tst.i, pc.i, P.pcRows, P.tag);
        const test = (ns: RouteNode[]) => {
          const hit: { id: string; mirrored: boolean }[] = [];
          for (const p of ns) for (const mir of [false, true]) {
            if (mir && mut.noMirror) continue;
            if (patternMatches(comp, p.rows!, mir, !mut.noColour, P.pcRows)) hit.push({ id: p.id, mirrored: mir });
          }
          return hit;
        };
        const scope = mut.unscoped ? patterns : branch ? patterns.filter(p => p.parent === groupOf(branch!)) : [];
        const hits = test(scope);
        if (hits.length > 1)
          throw new Error(`${P.tag}: ${tag} PC matches ${hits.map(h => h.id + (h.mirrored ? '(m)' : '')).join(', ')}`);
        if (hits.length === 1 && test(patterns).length > 1) multi.push(tag);
        if (hits[0]) {
          rec.node = hits[0].id; rec.mirrored = hits[0].mirrored;
          deepest = hits[0].id; deepestLock = pc.i;
        } else rec.off_page_under = `${deepest}.other`;
      }
      c.pc = rec;
    }

    // ── bag 2, missed: why (measured against the board before the spin, never a match) ──
    if (P.bag2Explain) c.bag2_near = branch ? null : explainMiss(tst ? tst.i : -1);

    // ── bag 3 (b): snapshot routes, only under their own branch ──
    if (branch) {
      let parent: string = groupOf(branch), from = L2 + 1;
      for (;;) {
        const kids = snapshots.filter(s => s.parent === parent);
        if (!kids.length) break;
        let best: { id: string; found: number; fm: boolean } | null = null;
        for (const child of kids) {
          const dg = diagram(child);
          let found = -1, fm = false;
          for (let i = from; i < d.locks.length; i++) {
            if (!strip && garbageBefore(i + 1)) break;
            const hit = keep(matchAgainst(board(i).rows, [dg], mut), 'snapshot');
            if (hit.length) { found = i; fm = hit[0]!.mirrored; break; }
          }
          bump(child.id, d.user);
          if (found >= 0 && (!best || found < best.found)) best = { id: child.id, found, fm };
        }
        if (!best) break;
        c.snapshots.push({ node: best.id, lock: best.found, mirrored: best.fm, verified: best.found <= d.v });
        if (!c.pc?.node) { deepest = best.id; deepestLock = best.found; }
        parent = best.id; from = best.found + 1;
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
 *  it clears KEPT, up to and including the PC lock. Bottom `pcRows` rows, top to bottom; pre-TST
 *  cells lower-case (`g` for garbage), later pieces upper-case. */
export function composite(d: RoundDigest, tstI: number, end: number, pcRows: number, tag = 'route'): string[] {
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
      if (q.row < 0 || q.row >= H) throw new Error(`${tag}: ${d.session} ${d.file} r${d.round} lock ${j} off the board`);
      const vr = vrows[vmap[q.row]!]!;
      if (vr[q.col] !== '-') throw new Error(`${tag}: ${d.session} ${d.file} r${d.round} lock ${j} overlaps`);
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
  return vrows.slice(0, pcRows).reverse().map(x => x.join(''));
}

/** The inverse of `composite()`'s `vmap`, for a builder rather than a reader: which diagram row each
 *  engine row (y-UP) is, starting bottom-aligned when a bag starts. `route-demos.ts` places a piece
 *  only while every row it is drawn on is still on the board. One sibling of the frame rule, beside
 *  it, so the two cannot drift. */
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
export function patternMatches(comp: string[], rows: string[], mirrored: boolean, colour: boolean, pcRows: number): boolean {
  let pr = rows.map(x => x.toUpperCase().replace(/U/g, 'T'));
  if (mirrored) pr = mirrorRows(pr);
  if (pr.length > pcRows) return false;
  const pad = [...Array(pcRows - pr.length).fill('----------'), ...pr];
  for (let i = 0; i < pcRows; i++) for (let k = 0; k < 10; k++) {
    const a = comp[i]![k]!, b = pad[i]![k]!;
    if (b === '-') { if (a !== '-') return false; continue; }
    if (a === '-') return false;
    if (b === 'C') { if (/[A-Z]/.test(a)) return false; continue; }
    if (colour && a.toUpperCase() !== b) return false;
  }
  return true;
}

// ── the artefact ─────────────────────────────────────────────────────────────────────────────

/** md5 of several files, concatenated in order: ONE string, so a field keeps its shape. */
export function md5Files(paths: string[]): string {
  const h = createHash('md5');
  for (const p of paths) h.update(readFileSync(p));
  return h.digest('hex');
}

export function inputs(P: RouteProfile, sessions: string[], root = SESSIONS_ROOT) {
  return {
    sessions: sessions.map(s => {
      const dir = `${root}/${s}`;
      const h = createHash('md5');
      for (const f of readdirSync(dir).filter(f => f.endsWith('.ttrm')).sort()) h.update(f).update(readFileSync(`${dir}/${f}`));
      return { session: s, replays_md5: h.digest('hex'), replay_facts_md5: md5(readFileSync(`${dir}/sim/replay-facts.json`)) };
    }),
    routes_md5: md5(readFileSync(P.routesPath)),
    emitter_md5: md5Files(P.hashFiles.classifier),
  };
}

/** The outcomes a profile's hold split can produce: an id that is not a route node, and the node its
 *  opportunities are borrowed from. */
export const outcomesOf = (P: RouteProfile) =>
  P.bag1.stages.filter(s => s.holdSplit).map(s => ({ id: s.holdSplit!.elsewhereNode, from: s.holdSplit!.holdNode }));

/** Assemble the artefact from classified rounds. */
export function assemble(P: RouteProfile, cls: Classified, routes: Routes, sessions: string[],
                         inp: ReturnType<typeof inputs>) {
  const users = [...new Set(cls.cases.map(c => c.player))].sort();
  const perUser = () => Object.fromEntries(users.map(u => [u, 0])) as Record<string, number>;
  const tally: Record<string, { cases: Record<string, number>; other: Record<string, number> }> = {};
  const T = (id: string) => (tally[id] ??= { cases: perUser(), other: perUser() });
  const outcomes = outcomesOf(P);
  const nodeIds = [...routes.nodes.map(n => n.id), ...outcomes.map(o => o.id)];
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
    const outcome = outcomes.find(o => o.id === id);
    const measured = !!outcome || (!!n && measurable(n));
    const t = tally[id]!;
    const sum = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
    const oppSrc = outcome ? cls.opportunities[outcome.from] : cls.opportunities[id];
    const opp = Object.fromEntries(users.map(u => [u, oppSrc?.[u] ?? 0]));
    return measured
      ? { id, measured: true, page_node: !!n, cases: sum(t.cases), cases_by_player: t.cases,
          opportunities: sum(opp), opportunities_by_player: opp,
          pc_off_page: sum(t.other), pc_off_page_by_player: t.other }
      : { id, measured: false, why: n?.unmatchable ? `unmatchable: ${n.unmatchable}`
          : n?.mirror_of ? `mirror_of: ${n.mirror_of}` : `${n?.node_kind}` };
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
    schema: P.artefact.schema,
    report_eligible: false,
    means: P.artefact.means,
    not_eligible_because: P.artefact.notEligible,
    caveat: P.artefact.caveat,
    rules: P.rules(),
    inputs: inp,
    sessions,
    outcomes: outcomes.map(o => o.id),
    nodes,
    conditions,
    lists: {
      ...P.lists(cls.cases, name),
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

export function corpus(): string[] { return discoverCorpus(SESSIONS_ROOT); }

/** A profile's corpus digests (one oracle run per round). */
export const digestCorpus = (P: RouteProfile, sessions = corpus()) =>
  sessions.flatMap(s => digestSession(s, SESSIONS_ROOT, { snapshotLocks: P.snapshotLocks, tag: P.tag }));

export function build(P: RouteProfile, mut: Mutants = {}, digests?: RoundDigest[]) {
  const sessions = corpus();
  const ds = digests ?? digestCorpus(P, sessions);
  const routes = loadRoutes(P.routesPath);
  return assemble(P, classify(P, ds, routes, mut), routes, sessions, inputs(P, sessions));
}
