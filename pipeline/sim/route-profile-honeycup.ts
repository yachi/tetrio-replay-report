/**
 * はちみつ砲 (Honey Cup) — the route profile for shiwehi.com's honeycup.php, read by the shared
 * classifier (`route-facts.ts`). The rules are the shared ones; this file says which nodes, which
 * locks and which strings, and the two places this page needs a rule 迷走砲 does not:
 *
 *  * BAG 2 STRIPS GARBAGE (`bag2Garbage: 'strip'`). Garbage arrives before the 13th lock in a large
 *    share of Honey Cup rounds (measured by the probe that preceded this file: without the strip most
 *    of the matches it finds are lost), and the classifier compares boards bottom-aligned. So a
 *    complete garbage row under the bag-2 board is stripped before matching, the count travels in the
 *    case (`garbage_rows_stripped`), and a bag-2 OPPORTUNITY here is "inside the verified prefix, no
 *    line cleared by the player before the sample" — garbage allowed. 迷走砲 stays on 'refuse'.
 *  * A MISSED BAG 2 IS EXPLAINED, NOT MATCHED (`bag2Explain`): the board before the TST against every
 *    bag-2 board by occupancy, so the bag-1-only rounds carry a measured reason (the TST came before
 *    the drawn board was complete, four extra cells sit on it, or one piece of it went elsewhere)
 *    without relaxing the route.
 *
 * Bag 1 reuses 迷走砲's hold split with J for Z: the 7-lock board (`bag1.j_right`, harddrop's Honey
 * Cup field) first; only if it misses, the 6-lock held-J board, split by the piece placed 7th against
 * the MIRROR-AWARE J (L in a mirrored round). The page's right-hand bag-1 board is the left one
 * mirrored (`mirror_of`), so it is never a node of its own. The FLAG `matched_harddrop` is the 7-lock
 * board matched by occupancy, compared in the test with `opener-facts.json`'s `honey_cup` `exact`.
 */
import type { RouteProfile } from './route-profile.ts';

/** Nodes with a board that get no demo, and why. Every reason is the page's own drawing or the
 *  planner's measured failure; a node the planner cannot build must be named here (the test compares
 *  this with the artefact both ways), never dropped. */
export const DEMO_UNBUILT: Record<string, string> = {
  'bag1.l_hold': '係「第一巡 六粒形」左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  '2.ideal.tst': '示意圖：五個理想形共用嘅 TST，每個 2.ideal#k 示範嘅最後一粒就係呢下 TST',
  '2.ideal.after_tst': '示意圖：TST 之後嘅盤面，即係每個 2.ideal#k 示範打完之後嘅盤面',
  '2.compromise.tst': '示意圖：2.compromise 示範嘅最後一粒就係呢下 TST',
  '2.ideal.fire.stmb_template': '「p」格冇指定填法；佢嘅例就係 stmb_example 嘅示範',
  '2.ideal.ren4': '「B」格係我哋嘅讀法（REN 區，13 格，唔係一粒粒方塊），冇得逐粒砌',
};

const REPO = `${import.meta.dir}/../..`;
const SIM = import.meta.dir;

export const HONEYCUP: RouteProfile = {
  key: 'honeycup',
  tag: 'honey-cup',
  routesPath: `${REPO}/pipeline/openers/honeycup-routes.json`,
  artefactPath: `${REPO}/analysis/honey-cup-facts.json`,
  demosPath: `${REPO}/analysis/honey-cup-demos.json`,
  hashFiles: {
    classifier: [`${SIM}/route-facts.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-honeycup.ts`,
                 `${SIM}/emit-route-facts.ts`],
    planner: [`${SIM}/route-demos.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-honeycup.ts`,
              `${SIM}/emit-route-demos.ts`],
  },
  bag1: {
    stages: [
      { nodes: ['bag1.j_right'], locks: 7 },
      { nodes: ['bag1.j_hold'], locks: 6,
        holdSplit: { piece: 'J', mirrorPiece: 'L', atLock: 7,
                     holdNode: 'bag1.j_hold', elsewhereNode: 'bag1.j_placed_elsewhere' } },
    ],
    flag: { field: 'matched_harddrop', stage: 0 },
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
  artefact: {
    schema: 'honey-cup-facts/1',
    means: 'for every corpus round whose bag 1 is shiwehi.com\'s はちみつ砲 bag 1 cell for cell (as drawn or mirrored), '
      + 'the deepest node of that page\'s route tree the round reaches, and how often each node\'s sampling point was reached',
    notEligible: 'every board is the vendored Triangle engine\'s; which bag-2 and bag-3 shape was built has no second implementation. '
      + 'The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'bag-1 opportunities count rounds that reached the sampling point clean (inside the verified prefix, no clear, no garbage before it); '
      + 'bag-2 and snapshot opportunities allow garbage: complete garbage rows are stripped from the bottom of the board first '
      + '(garbage_rows_stripped), so they count rounds inside the verified prefix with no line cleared by the player before the sample. '
      + 'Bag-3 nodes have no separate sampling point and count the rounds that reached their parent. '
      + 'A hold is asserted only by the lock-7 piece test. The compromise form\'s order condition is the page\'s example (など), '
      + 'recorded as condition_met and never the reason a form was built. bag2_near is measured against the board before the TST, '
      + 'never a match.',
  },
  rules: () => ({
    bag1_placed_locks: 7, bag1_hold_locks: 6, bag2_lock_index: 12, bag2_garbage: 'strip complete garbage rows from the bottom',
    event_locks: 40, snapshot_locks: 46, pc_rows: 6, pc_lines: 8,
    precedence: 'j_right (7 locks); only if it misses, j_hold (6 locks) split by the lock-7 piece against the mirror-aware bag-1 J',
    condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
    group_scope: 'the five 2.ideal forms share one PC list: bag-3 patterns are scoped by the form\'s group',
    bag2_near: 'a bag-1 round with no bag-2 match: the board before its TST, by occupancy, against every bag-2 board: a strict '
      + 'subset (the TST before the board was complete), that board plus exactly four cells, or that board with one piece\'s four cells moved elsewhere',
  }),
  lists: (cases, name) => ({
    j_hold_bag1: cases.filter(c => c.bag1.node === 'bag1.j_hold').map(name),
    j_placed_elsewhere_bag1: cases.filter(c => c.bag1.node === 'bag1.j_placed_elsewhere').map(name),
    tst_donate: cases.filter(c => c.snapshots.some((s: any) => s.node === '2.compromise.tst_donate')).map(name),
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
    schema: 'honey-cup-demos/1',
    means: 'Constructed replays, one per drawn node of shiwehi.com\'s はちみつ砲 route page: our own piece queue '
         + 'and key inputs, run from an empty board through the vendored Triangle engine, ending on the '
         + 'page\'s drawn board. Not a game anyone played and not corpus data.',
    notEligible: ['not a game anyone played; not corpus data',
                  'one engine, no second implementation of the boards'],
    caveat: {
      order: 'Where the page does not fix the piece order, the order here is ours: the early piece first, '
           + 'the first piece of each of the page\'s before-pairs next, then IOTSZJL, the T into the TST slot last. '
           + 'order_reading records it per bag.',
      hold: 'bag1.j_hold holds its J when it arrives, just after L (the page: the later of J and L is held). The '
          + 'hold box is then never empty again: in bag 2 the held J comes out when the T arrives, and the T comes '
          + 'out for the TST when the next bag\'s first piece arrives; in a Perfect Clear bag that piece is the '
          + 'one the pattern does not use, and it stays held.',
      early: 'The page gives no threshold for "early"; the demo puts the early piece first in its bag.',
      spin_board: 'The page draws each bag-2 form with the TST slot empty and the T on a separate board '
                + '(spin_board); the demo fires the T into that board\'s U cells.',
      ideal_chain: 'The fifteen Perfect Clear patterns hang under the five 2.ideal forms, which all leave the '
                 + 'same board after the TST (2.ideal.after_tst); their demos run through 2.ideal#1.',
      spin: 'Every T-spin kind and line count is the engine\'s verdict on the replayed inputs.',
    },
    unbuilt: DEMO_UNBUILT,
    pieceReadings: [],
    bag1Spec: (n, routes) => {
      const r = routes.bag1, hold = n.id === 'bag1.j_hold';
      const chain: string[] = r.hold_free.applies_to === n.id ? r.hold_free.before : [];
      return { before: chain.slice(1).map((b, i) => [chain[i]!, b] as [string, string]), early: r.requires.early,
               holdPiece: hold ? 'J' : null, holdBefore: hold ? 'O' : null };
    },
    chainVia: { '2.ideal.after_tst': '2.ideal#1' },
    spinLetter: n => (n.t_in_tsd_slot ? { letter: 't', lines: 2 } : null),
  },
};
