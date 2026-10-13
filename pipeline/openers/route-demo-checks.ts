/**
 * The checks every opener's CONSTRUCTED-DEMO test makes (`stray-cannon-demos.test.ts`,
 * `honey-cup-demos.test.ts`), written ONCE and parameterised by the opener's profile and its named
 * lists. A check kept in two test files drifts the way a rule kept in two gates does; what stays in
 * each test file is what only that opener has: its named lists, its data mutants (which plant into
 * its own node ids) and any opener-only assertion.
 *
 *   2. re-run: every demo's queue and key inputs, fed to a fresh engine through `instrumentEngine`,
 *      lock exactly the committed locks. That is the reachability witness.
 *   3. the corpus classifier agrees: each demo, digested like a corpus round, reaches the node it
 *      demonstrates (a colour reading: off the page by colour as drawn, on it as read).
 *   4. board equality against the drawing, independent of the classifier: the U is empty on the
 *      drawn board and fired next (into the spin board's U cells, where a node has one); a PC pattern
 *      is the kept-rows composite and ends empty.
 *   5. spins: every spin-slot lock (U, or the profile's spin letter) is a full T-spin, every other T
 *      none; the line counts the drawing does not fix are a NAMED list, compared both ways.
 *   6. the queue is whole 7-bags, each bag satisfies its node's page condition, holds match flags.
 *   7. a child demo's locks start with its parent's.
 *   8. completeness: every node with a board has one demo or one unbuilt entry with its reason.
 */
import { readFileSync } from 'node:fs';
import { runDemo, readRows as readRowsWith, spinBoardCells, PIECES } from '../sim/route-demos.ts';
import { decodeTimeline, queueStates, placeCells, WIDTH, ROWS, type Lock } from '../sim/emit-replay.ts';
import { classify, composite, patternMatches, conditionHolds, loadRoutes, kindsOf, frameStart,
         type RoundDigest, type Routes } from '../sim/route-facts.ts';
import type { RouteProfile } from '../sim/route-profile.ts';
import { rowsFromBoard } from './match.ts';

/** One opener's demo lists: the reasons a board node has no demo, the spin-slot line counts the
 *  drawing does not fix, the plain-T spin exceptions, and the colour-read drawings. */
export interface DemoLists {
  unbuilt: Record<string, string>;
  spinLines: Record<string, number>;
  spinExceptions: string[];
  pieceReadings: string[];
  /** the bag-1 node whose demo ends with a piece in the hold box, and that piece */
  hold: { node: string; piece: string };
}

const T_OF = (letter: string) => (letter === 'U' ? 'T' : letter.toUpperCase());
/** The line count a node's named spin fires (山岳積み2号's TSD snapshot boards). */
const SPIN_LINES: Record<string, number> = { TSS: 1, TSD: 2, TST: 3 };

/** Boards after every lock, y-UP. */
export function boards(d: any): (string | null)[][][] {
  const out: (string | null)[][][] = [];
  decodeTimeline(d.seq, d.locks as Lock[], b => out.push(b.map(r => [...r])));
  return out;
}

/** Does a y-UP board show `rows` (bottom-aligned)? `c` any filled cell, `U` empty (the slot), a
 *  letter that piece, `-` empty; nothing above the drawing. */
export function shows(board: (string | null)[][], rows: string[], uEmpty: boolean): boolean {
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < WIDTH; x++) {
    const i = rows.length - 1 - y;
    const ch = i >= 0 ? rows[i]![x]! : '-';
    const v = board[y]![x];
    if (ch === '-' || (ch === 'U' && uEmpty)) { if (v != null) return false; continue; }
    if (v == null) return false;
    if (ch === 'c') continue;
    if (v !== T_OF(ch)) return false;
  }
  return true;
}

/** The demo as a corpus round digest: no recorded game, so there is no prefix to verify (v is the
 *  last lock) and no garbage. */
export function digestOf(d: any): RoundDigest {
  const locks: RoundDigest['locks'] = [], rows: RoundDigest['rows'] = [];
  const q = queueStates(d.seq, d.locks);
  const spin = ['none', 'mini', 'full'];
  decodeTimeline(d.seq, d.locks, (b, i, cleared) => {
    const lk = d.locks[i];
    locks.push({ piece: q[i]!.piece,
      cells: placeCells(q[i]!.piece, lk[1]).map(c => ({ col: c % WIDTH, row: ROWS - 1 - Math.floor(c / WIDTH) })),
      cleared: lk[2], spin: spin[lk[3]]!, allclear: lk[2] > 0 && b.every(r => r.every(c => c == null)),
      clearedRows: cleared.map(y => ROWS - 1 - y) });
    rows.push(rowsFromBoard([...b].reverse().map(r => r.map(c => c))));
  });
  return { session: 'demo', file: d.node, round: 0, user: 'demo', match: 0, file_sort_index: 0,
           bag2_order: d.seq.slice(7, 14), v: d.locks.length - 1, height: ROWS, garbage: [],
           n_locks: d.locks.length, locks, rows };
}

/** The checks for one opener, bound to its profile and lists. */
export function demoChecks(P: RouteProfile, L: DemoLists) {
  const routes: Routes = loadRoutes(P.routesPath);
  const byId = new Map(routes.nodes.map(n => [n.id, n]));
  const readings = P.demos!.pieceReadings;
  const readRows = (id: string, rows: string[]) => readRowsWith(id, rows, readings, P.tag);
  const b1 = (d: any) => byId.get(d.bags[0].node)!.bag === 1;
  const spinLetter = (n: any) => P.demos!.spinLetter?.(n, routes) ?? null;
  const kinds = kindsOf(P, routes);
  const kindOf = (n: any) => kinds.find(k => k.lists.includes(n.list))!;

  /** Every check that reads one demo. Returns the first failure, or null. */
  function checkDemo(d: any, all: Map<string, any>): string | null {
    const n = byId.get(d.node);
    if (!n?.rows) return `${d.node}: not a board node`;
    // 6. whole 7-bags, holds, conditions
    if (d.seq.length % 7) return `${d.node}: seq is not whole bags`;
    for (let k = 0; k < d.seq.length; k += 7)
      if ([...d.seq.slice(k, k + 7)].sort().join('') !== [...PIECES].sort().join('')) return `${d.node}: bag ${k / 7} not a 7-bag`;
    if (d.bags.map((b: any) => b.queue).join('') !== d.seq.slice(0, 7 * d.bags.length)) return `${d.node}: bags are not the seq`;
    if (d.bags.reduce((a: number, b: any) => a + b.holds, 0) !== d.locks.filter((l: any) => l[5]).length)
      return `${d.node}: holds do not match the held flags`;
    for (const b of d.bags) {
      const c = byId.get(b.node)!.condition;
      if (c?.all && conditionHolds(c, b.queue, '') !== true) return `${b.node}: queue ${b.queue} breaks the page condition`;
      if (c?.early && b.queue[0] !== c.early) return `${b.node}: ${c.early} is not first in ${b.queue}`;
    }
    // a bag-1 early piece is a single letter (迷走砲, はちみつ砲); 山岳積み2号's is an example pair of
    // alternatives, applied as its `before` pair (checked with the page conditions above)
    const early = (routes as any).bag1.requires.early;
    if (typeof early === 'string' && b1(d) && d.bags[0].queue[0] !== early) return `${d.node}: bag 1 not ${early} first`;
    // 2. re-run
    let rr;
    try { rr = runDemo(routes, d.seq, d.inputs, d.frames).rec; } catch (e) { return `${d.node}: re-run threw ${e}`; }
    if (JSON.stringify(rr.locks) !== JSON.stringify(d.locks)) return `${d.node}: re-run locks differ`;
    // 7. prefix sharing
    if (d.parent) {
      const p = all.get(d.parent);
      if (!p) return `${d.node}: parent ${d.parent} has no demo`;
      if (JSON.stringify(d.locks.slice(0, p.locks.length)) !== JSON.stringify(p.locks)) return `${d.node}: prefix differs from ${d.parent}`;
      if (d.seq.slice(0, p.locks.length) !== p.seq.slice(0, p.locks.length)) return `${d.node}: seq prefix differs`;
    }
    // 5. spins
    const q = queueStates(d.seq, d.locks);
    const bagOf = (i: number) => byId.get(d.bags[d.bags.findIndex((_: any, k: number) =>
      d.bags.slice(0, k + 1).reduce((a: number, b: any) => a + b.placed.length, 0) > i)].node)! as any;
    for (let i = 0; i < d.locks.length; i++) {
      const Lt = d.letters[i], lk = d.locks[i];
      if (T_OF(Lt) !== q[i]!.piece) return `${d.node}: lock ${i} letter ${Lt} vs piece ${q[i]!.piece}`;
      const bn = bagOf(i);
      const sl = spinLetter(bn);
      if (Lt === 'U' || (sl && Lt === sl.letter)) {
        if (lk[3] !== 2) return `${d.node}: spin-slot lock ${i} spin ${lk[3]}`;
        const want = bn.bag === 2 && !bn.list ? 3 : bn.has_tsd_slot ? 2 : sl ? sl.lines
          : SPIN_LINES[bn.spin] ?? L.spinLines[bn.id];
        if (want === undefined || lk[2] !== want) return `${d.node}: spin-slot lock ${i} cleared ${lk[2]}, want ${want}`;
      } else if (q[i]!.piece === 'T' && lk[3] !== 0 && !L.spinExceptions.includes(d.node)) return `${d.node}: t lock ${i} spun`;
    }
    // 4. board equality
    const B = boards(d);
    const last = d.locks.length - 1;
    if (n.bag === 1) {
      if (!shows(B[last]!, n.rows, false)) return `${d.node}: final board is not the drawing`;
      if (n.id === L.hold.node && q[last]!.hold !== L.hold.piece) return `${d.node}: ${L.hold.piece} is not in the hold box`;
    } else if (n.list) {
      if (B[last]!.some(r => r.some(c => c != null))) return `${d.node}: last lock is not a Perfect Clear`;
      const lines = kindOf(n).lines;
      if (d.locks.reduce((a: number, l: any) => a + l[2], 0) !== lines) return `${d.node}: not ${lines} lines`;
    } else if (n.bag === 2) {
      if (!shows(B[12]!, n.rows, true)) return `${d.node}: board after 13 pieces is not the drawing`;
      if (d.letters[13] !== 'U' || last !== 13) return `${d.node}: lock 14 is not the U`;
      const sc = spinBoardCells(n, routes, P.tag);
      if (sc.length) {
        // y-UP cells; nothing has cleared before the TST, so engine row = diagram row from the bottom
        const got = placeCells('T', d.locks[13][1]).map(c => `${c % WIDTH},${Math.floor(c / WIDTH)}`).sort();
        const want = sc.map(([x, dd]) => `${x},${dd}`).sort();
        if (JSON.stringify(got) !== JSON.stringify(want)) return `${d.node}: the TST is not in the spin board's U cells`;
      }
    } else if (!n.rows.some(r => r.includes('U'))) {
      // nothing to fire: the demo ends on the drawing (はちみつ砲's L roof, with its T still held). An
      // UNMATCHABLE board with a U (山岳積み2号's 9-row 4巡目 boards) is fired like any other: it is
      // too tall for the classifier, not for the demo
      if (!shows(B[last]!, n.rows, false)) return `${d.node}: final board is not the drawing`;
    } else {
      if (!shows(B[last - 1]!, n.rows, true)) return `${d.node}: board before the U is not the drawing`;
      if (d.letters[last] !== 'U') return `${d.node}: last lock is not the U`;
    }
    // 3. the classifier
    const c = classify(P, [digestOf(d)], routes).cases[0];
    if (!c) return `${d.node}: classifier found no bag 1`;
    if (n.bag === 1 && c.bag1.node !== n.id) return `${d.node}: classifier bag 1 ${c.bag1.node}`;
    if (n.bag === 2 && !n.list && (c.bag2?.node !== n.id || c.bag2.condition_met === false)) return `${d.node}: classifier bag 2 ${c.bag2?.node}`;
    if (n.list) {
      const dg = digestOf(d);
      const k = kindOf(n);
      const ev = dg.locks.map((l, i) => ({ i, piece: l.piece, spin: l.spin, lines: l.cleared })).filter(e => e.lines > 0);
      const fs = frameStart(k, ev, last);
      if ('none' in fs) return `${d.node}: ${fs.none}`;
      const comp = composite(dg, fs.at, last, k.rows, P.tag);
      if (!patternMatches(comp, readRows(n.id, n.rows), false, true, k.rows)) return `${d.node}: composite is not the pattern`;
      if (L.pieceReadings.includes(n.id)) {
        if (c.pc?.node === n.id) return `${d.node}: colour reading not needed?`;
      } else if (c.pc?.node !== n.id) return `${d.node}: classifier PC ${c.pc?.node} ${c.pc?.off_page_under}`;
    }
    if (n.bag >= 3 && !n.list && !n.unmatchable && !c.snapshots.some((s: any) => s.node === n.id))
      return `${d.node}: classifier snapshot missing`;
    return null;
  }

  /** Completeness: every board node has exactly one demo or one unbuilt entry. */
  function checkComplete(art: any): string | null {
    const demos = new Map<string, number>();
    for (const d of art.demos) demos.set(d.node, (demos.get(d.node) ?? 0) + 1);
    const unb = Object.fromEntries(art.unbuilt.map((u: any) => [u.node, u.reason]));
    if (JSON.stringify(unb) !== JSON.stringify(L.unbuilt)
        && JSON.stringify(Object.entries(unb).sort()) !== JSON.stringify(Object.entries(L.unbuilt).sort()))
      return `unbuilt ${JSON.stringify(unb)}`;
    for (const n of routes.nodes) {
      if (!n.rows) { if (demos.has(n.id)) return `${n.id}: demo for a node with no board`; continue; }
      const k = (demos.get(n.id) ?? 0) + (n.id in unb ? 1 : 0);
      if (k !== 1) return `${n.id}: ${k} demos/unbuilt entries`;
    }
    for (const id of demos.keys()) if (!byId.has(id)) return `${id}: not a route node`;
    return null;
  }

  function checkAll(art: any): string | null {
    const c = checkComplete(art);
    if (c) return c;
    const all = new Map<string, any>(art.demos.map((d: any) => [d.node, d]));
    for (const d of art.demos) { const e = checkDemo(d, all); if (e) return e; }
    if (JSON.stringify(art.demos.flatMap((d: any) => d.piece_readings.map((p: any) => p.node)).sort())
        !== JSON.stringify([...L.pieceReadings].sort())) return 'piece readings list differs';
    return null;
  }

  const committedText = () => readFileSync(P.demosPath, 'utf8');
  return { routes, byId, readRows, checkDemo, checkComplete, checkAll, committedText,
           committed: () => JSON.parse(committedText()) };
}
