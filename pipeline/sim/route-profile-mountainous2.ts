/**
 * 山岳積み2号 (Mountainous Stacking 2) — the route profile for shiwehi.com's mountainous2.php, read by
 * the shared classifier (`route-facts.ts`) and the shared demo planner (`route-demos.ts`). The rules
 * are the shared ones; this file says which nodes, which locks and which strings, and the one thing
 * this page needs that 迷走砲 and はちみつ砲 do not:
 *
 *  * THREE PERFECT CLEAR KINDS (`pcKinds`). The page draws a 4-line PC in bag 2 on the L-held board
 *    with no spin before it (`2.pc4`), the 8-line bag-3 PCs after the TST (`2.ideal.pc`,
 *    `2.normal.pc`, as the other two pages), and a 14-line PC in bag 5 whose frame starts after the
 *    bag-4 TSD (`2.compromise.fire5.pc`, 8 rows tall). A corpus PC is filed under the kind whose
 *    cumulative line count it has; each kind's patterns are scoped by their ANCHOR (the bag-1 node
 *    for `2.pc4`, the bag-2 group for the rest — `2.compromise` for the 5-bag line, whose bag-3 and
 *    bag-4 parents are an unmatchable 9-row group).
 *
 * Bag 1 reuses the hold split with L: the 7-lock board (`bag1.l_top`, the page's drawing, the L stood
 * on end) first; only if it misses, the 6-lock L-held board (`bag1.l_hold`, derived in the
 * transcription as `bag1.l_top` less its four `l` cells), split by the piece placed 7th against the
 * MIRROR-AWARE L (J in a mirrored round). The page's right-hand bag-1 board is the left one mirrored
 * (`mirror_of`), so it is never a node of its own. The FLAG `matched_harddrop` is the 6-LOCK board
 * matched by occupancy — harddrop's Mountainous Stacking 2 field is the L-held board, unlike Honey
 * Cup's — compared in the test with `opener-facts.json`'s `mountainous_2` `exact`.
 *
 * Bag 2 strips garbage as はちみつ砲 does (`bag2Garbage: 'strip'`), and a missed bag 2 is explained,
 * never matched (`bag2Explain`).
 */
import type { RouteProfile } from './route-profile.ts';

/** Nodes with a board that get no demo, and why. Every reason is the page's own drawing or the
 *  planner's measured failure; a node the planner cannot build must be named here (the test compares
 *  this with the artefact both ways), never dropped. */
export const DEMO_UNBUILT: Record<string, string> = {
  'bag1.j_top': '係原頁左邊嗰幅第一巡圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  '2.ideal.after': '示意圖：TST 之後嘅盤面，即係 2.ideal 示範打完之後嘅盤面',
  '2.normal.after': '示意圖：三個通常形 TST 之後共用嘅盤面，即係 2.normal#1 示範打完之後嘅盤面',
  '2.compromise.after': '示意圖：TST 之後嘅盤面，即係 2.compromise 示範打完之後嘅盤面',
  '2.compromise.fire5.after': '示意圖：兩個 5巡パフェ 3巡目形 TSD 之後共用嘅盤面，即係 2.compromise.fire5#1 示範打完之後嘅盤面',
  '2.compromise.fire5.bag4.after': '示意圖：兩個 4巡目形 TSD 之後共用嘅盤面，即係 2.compromise.fire5.bag4#1 示範打完之後嘅盤面',
};

/** Is a PC pattern's `t` the TSD's T? Only where its four cells are EXACTLY the empty cells of its
 *  base board's bottom two rows (the page's TSD slot, `ccc---cccc` over `cccc-ccccc`). The
 *  transcription's `t_in_tsd_slot` is the flat ttt-over-t SHAPE anywhere, which is the TSD on はちみつ砲
 *  but not here: 2.normal.pc#5/#6, the 4-line PC #3 and four 5巡目 PCs draw that shape on the
 *  surface, where the engine credits no spin (measured by the planner: with the shape rule they are
 *  unbuildable as spins), and the transcription's own `2.normal.pc:no_tsd` names #5/#6 as not in
 *  the slot. */
export function tsdT(n: any, routes: any): boolean {
  if (!n.list || !n.rows) return false;
  const base = routes.nodes.find((x: any) => x.id === n.base);
  if (!base?.rows) return false;
  const at = (rows: string[], ch: (c: string) => boolean) => {
    const out: string[] = [];
    rows.slice(-2).forEach((r, i) => [...r].forEach((c, x) => { if (ch(c)) out.push(`${x},${i}`); }));
    return out.sort().join(' ');
  };
  const slot = at(base.rows, c => c === '-');
  const t = (n.rows as string[]).flatMap((r, i) => [...r].map((c, x) => (c === 't' ? `${x},${i}` : null)))
    .filter(Boolean).length;
  return t === 4 && slot.split(' ').length === 4 && at(n.rows, c => c === 't') === slot;
}

const REPO = `${import.meta.dir}/../..`;
const SIM = import.meta.dir;

export const MOUNTAINOUS2: RouteProfile = {
  key: 'mountainous2',
  tag: 'mountainous2',
  routesPath: `${REPO}/pipeline/openers/mountainous2-routes.json`,
  artefactPath: `${REPO}/analysis/mountainous2-facts.json`,
  demosPath: `${REPO}/analysis/mountainous2-demos.json`,
  hashFiles: {
    classifier: [`${SIM}/route-facts.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-mountainous2.ts`,
                 `${SIM}/emit-route-facts.ts`],
    planner: [`${SIM}/route-demos.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-mountainous2.ts`,
              `${SIM}/emit-route-demos.ts`],
  },
  bag1: {
    stages: [
      { nodes: ['bag1.l_top'], locks: 7 },
      { nodes: ['bag1.l_hold'], locks: 6,
        holdSplit: { piece: 'L', mirrorPiece: 'J', atLock: 7,
                     holdNode: 'bag1.l_hold', elsewhereNode: 'bag1.l_placed_elsewhere' } },
    ],
    flag: { field: 'matched_harddrop', stage: 1 },
    lockPieceField: 'lock7_piece',
  },
  bag2Lock: 12,
  bag2Garbage: 'strip',
  bag2Explain: true,
  eventLocks: 40,
  snapshotLocks: 46,
  pcRows: 6,
  pcLines: 8,
  pcAfter: { piece: 'T', spin: 'full', lines: 3 },
  pcKinds: [
    { lists: ['2.ideal.pc', '2.normal.pc'], after: { piece: 'T', spin: 'full', lines: 3, pick: 'first', name: 'TST' },
      lines: 8, rows: 6 },
    { lists: ['2.pc4'], after: { locks: 6 }, lines: 4, rows: 6 },
    { lists: ['2.compromise.fire5.pc'], after: { piece: 'T', spin: 'full', lines: 2, pick: 'last', name: 'TSD' },
      lines: 14, rows: 8 },
  ],
  artefact: {
    schema: 'mountainous2-facts/1',
    means: 'for every corpus round whose bag 1 is shiwehi.com\'s 山岳積み2号 bag 1 cell for cell (as drawn or mirrored, '
      + 'the L stood on end at 7 locks or held at 6), the deepest node of that page\'s route tree the round reaches, '
      + 'and how often each node\'s sampling point was reached',
    notEligible: 'every board is the vendored Triangle engine\'s; which bag-2 and later shape was built has no second implementation. '
      + 'The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'bag-1 opportunities count rounds that reached the sampling point clean (inside the verified prefix, no clear, no garbage before it); '
      + 'bag-2 and snapshot opportunities allow garbage: complete garbage rows are stripped from the bottom of the board first '
      + '(garbage_rows_stripped), so they count rounds inside the verified prefix with no line cleared by the player before the sample. '
      + 'PC patterns have no separate sampling point and count the rounds that reached their anchor: the bag-1 L-held board for the '
      + '4-line PCs, the bag-2 group for the rest (2.compromise for the 5-bag line, whose own bag-3 and bag-4 boards are a 9-row group). '
      + 'A hold is asserted only by the lock-7 piece test. The page\'s order readings (%S%O, %O%S) are ours. bag2_near is measured '
      + 'against the board before the TST, never a match.',
  },
  rules: () => ({
    bag1_placed_locks: 7, bag1_hold_locks: 6, bag2_lock_index: 12, bag2_garbage: 'strip complete garbage rows from the bottom',
    event_locks: 40, snapshot_locks: 46,
    pc_kinds: [
      { lists: ['2.ideal.pc', '2.normal.pc'], frame_after: 'the first TST', lines: 8, rows: 6 },
      { lists: ['2.pc4'], frame_after: '6 locks (the L-held board), no spin', lines: 4, rows: 6 },
      { lists: ['2.compromise.fire5.pc'], frame_after: 'the last TSD before the PC', lines: 14, rows: 8 },
    ],
    precedence: 'l_top (7 locks); only if it misses, l_hold (6 locks) split by the lock-7 piece against the mirror-aware bag-1 L',
    condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
    group_scope: 'the three 2.normal forms share one PC list: PC patterns are scoped by their anchor, the form\'s group',
    bag2_near: 'a bag-1 round with no bag-2 match: the board before its TST, by occupancy, against every bag-2 board: a strict '
      + 'subset (the TST before the board was complete), that board plus exactly four cells, or that board with one piece\'s four cells moved elsewhere',
  }),
  lists: (cases, name) => ({
    l_hold_bag1: cases.filter(c => c.bag1.node === 'bag1.l_hold').map(name),
    l_placed_elsewhere_bag1: cases.filter(c => c.bag1.node === 'bag1.l_placed_elsewhere').map(name),
    bag2_garbage_stripped: cases.filter(c => c.bag2?.node && c.bag2.garbage_rows_stripped > 0)
      .map(c => `${name(c)} (${c.bag2.garbage_rows_stripped})`),
    bag2_none_tst_before_complete: cases.filter(c => c.bag2_near?.kind === 'subset')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')}`),
    bag2_none_extra_piece: cases.filter(c => c.bag2_near?.kind === 'superset')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')} + ${c.bag2_near.extra}`),
    bag2_none_moved_piece: cases.filter(c => c.bag2_near?.kind === 'moved')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')}, ${c.bag2_near.extra} moved`),
  }),
  demos: {
    schema: 'mountainous2-demos/1',
    means: 'Constructed replays, one per drawn node of shiwehi.com\'s 山岳積み2号 route page: our own piece queue '
         + 'and key inputs, run from an empty board through the vendored Triangle engine, ending on the '
         + 'page\'s drawn board. Not a game anyone played and not corpus data.',
    notEligible: ['not a game anyone played; not corpus data',
                  'one engine, no second implementation of the boards'],
    caveat: {
      order: 'Where the page does not fix the piece order, the order here is ours: the first piece of each of the page\'s '
           + 'before-pairs first (bag 1: J before Z, one of the page\'s two example conditions), then IOTSZJL, the T into the '
           + 'U slot last. order_reading records it per bag.',
      hold: 'bag1.l_hold holds its L when it arrives (our choice of where: just before the bag\'s Z). The hold box is then '
          + 'never empty again: the held L comes out at its slot in bag 2 (2.normal#3, the 4-line PCs), swapped for the '
          + 'piece that bag places last. No other demo holds.',
      early: 'The page\'s bag-1 condition is an example (%J>%Z or %L%S early) that its next sentence widens; the demo '
           + 'uses J before Z.',
      chain: 'The PC patterns and later boards hang under the page\'s after-the-spin illustrations; their demos run '
           + 'through the demo that ends on that board (2.normal#1 for the three 通常形 forms, form 1 for each 5巡パフェ pair).',
      spin: 'Every T-spin kind and line count is the engine\'s verdict on the replayed inputs.',
    },
    unbuilt: DEMO_UNBUILT,
    pieceReadings: [],
    bag1Spec: (n, _routes) => {
      const hold = n.id === 'bag1.l_hold';
      return { before: [['J', 'Z']], early: null, holdPiece: hold ? 'L' : null, holdBefore: hold ? 'Z' : null };
    },
    chainVia: {
      '2.ideal.after': '2.ideal',
      '2.normal.after': '2.normal#1',
      '2.compromise.after': '2.compromise',
      '2.compromise.fire5.after': '2.compromise.fire5#1',
      '2.compromise.fire5.bag4.after': '2.compromise.fire5.bag4#1',
    },
    spinLetter: (n, routes) => (tsdT(n, routes) ? { letter: 't', lines: 2 } : null),
  },
};
