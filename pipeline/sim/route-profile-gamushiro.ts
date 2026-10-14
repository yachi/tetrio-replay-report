/**
 * ガムシロ積み (Gamushiro Stacking) — the route profile for shiwehi.com's gamushiro.php, read by the
 * shared classifier (`route-facts.ts`) and the shared demo planner (`route-demos.ts`). The rules are
 * the shared ones; this file says which nodes, which locks and which strings, and needs NO switch the
 * other four profiles do not already have:
 *
 *  * Bag 1 is 山岳積み2号's hold split (the page itself calls the opener 山岳積み2号 with the I moved):
 *    the 7-lock board with the L stood on the O (`bag1.l_top`, drawn only as 基本形 1) first; only if
 *    it misses, the 6-lock L-held board (`bag1.left`, the page's left pattern), split by the piece
 *    placed 7th against the MIRROR-AWARE L (J in a mirrored round). The page's right-hand board is the
 *    left one mirrored (`mirror_of`), so it is never a node of its own.
 *  * NO FLAG, as stick spin. harddrop's opener transcription (`wiki-openers.json`) draws no
 *    Gamushiro field, so `opener-facts.json` has no column to compare one with. The corpus
 *    cross-check `gamushiro.test.ts` makes instead is against the ordering metric: the route fires a
 *    TST first, so every bag-1 round's opener window must be Triple-first, or the round is named.
 *  * TWO PERFECT CLEAR KINDS (`pcKinds`, as 山岳積み2号): the 4-line PC in bag 2 on the L-held board
 *    with no spin before it (`2.pc4`, anchored at `bag1.left`), and the 8-line PCs after the TST
 *    (`2.normal.pc`, anchored at the `2.normal` group).
 *
 * Bag 2 strips garbage (`bag2Garbage: 'strip'`) and a missed bag 2 is explained, never matched
 * (`bag2Explain`), as はちみつ砲 and 山岳積み2号. The 妥協 board and the first Imperial Cross board
 * are taller than the classifier's 8 rows (`unmatchable` in the transcription), so 2.normal#1 and #2
 * are the only bag-2 boards a corpus round can reach; the second Imperial Cross board fits the frame
 * under its blank top row and is compared.
 *
 * A REFERENCE OPENER for this corpus, not one its two players use: the artefact is mostly zeros, and
 * every zero is COMPARED (the classifier reaches every measurable node; the demos test reaches each
 * one through it), never "not compared".
 */
import type { RouteProfile } from './route-profile.ts';

/** Nodes with a board that get no demo, and why. Every reason is the page's own drawing or the
 *  planner's measured failure; a node the planner cannot build must be named here (the test compares
 *  this with the artefact both ways), never dropped. */
export const DEMO_UNBUILT: Record<string, string> = {
  'bag1.right': '係原頁左邊嗰幅第一巡圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  '2.normal.tst': '示意圖：兩個通常形打 TST 嘅位同消嘅三行，即係 2.normal#1 示範最後一粒',
  '2.normal.after': '示意圖：兩個通常形 TST 之後共用嘅盤面，即係 2.normal#1 示範打完之後嘅盤面',
  '2.normal.pc.rest': '「残り55パターン」喺 HTML 註解入面，頁面冇顯示；佢唯一嘅圖係 TST 之後嘅盤面重畫做空白樣板，冇一粒方塊',
  '2.compromise.tst': '示意圖：妥協形打 TST 嘅位同消嘅三行，即係 2.compromise 示範最後一粒',
};

/** PC patterns whose `t` sits in the TSD slot (`t_in_tsd_slot`) but which the engine cannot fire as a
 *  TSD, MEASURED by the planner: the slot is roofed in the row above it by the J's hook (column 3)
 *  and the S (column 4), so the T can only get in before them — and then the S's cell beside the
 *  slot (column 5) is still empty and the two rows do not clear — or after them by a kick the engine
 *  credits as no full T-spin. The demo places that T as a plain T, last, into the PC; the drawing is
 *  the same board either way. A name here is a red build in the demos test until it is measured
 *  again. */
export const TSD_NOT_FIRED: Record<string, string> = {
  '2.normal.pc#3': 'TSD 位上面一行俾 J 嘅鉤（第 3 欄）同 S（第 4 欄）封住：T 要喺佢哋之前入，咁旁邊 S 嗰格（第 5 欄）未有，兩行消唔到；'
    + '之後先入就靠踢牆，引擎唔當係 T-spin。示範將呢粒 T 當普通 T，最後一粒放，打全消',
};

/** Is a PC pattern's `t` the TSD's T? The transcription's `t_in_tsd_slot` — the four t cells are the
 *  flat ttt-over-t shape in the pattern's BOTTOM TWO body rows, where 2.normal.after leaves its only
 *  TSD-shaped gap (a position test, checked by the transcription gate) — less TSD_NOT_FIRED. The page
 *  draws that T as `U` in 基本形 3 (pc#1), which is the reading: a TSD, before the PC. */
export const tsdT = (n: any): boolean => n.t_in_tsd_slot === true && !(n.id in TSD_NOT_FIRED);

const REPO = `${import.meta.dir}/../..`;
const SIM = import.meta.dir;

export const GAMUSHIRO: RouteProfile = {
  key: 'gamushiro',
  tag: 'gamushiro',
  routesPath: `${REPO}/pipeline/openers/gamushiro-routes.json`,
  artefactPath: `${REPO}/analysis/gamushiro-facts.json`,
  demosPath: `${REPO}/analysis/gamushiro-demos.json`,
  hashFiles: {
    classifier: [`${SIM}/route-facts.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-gamushiro.ts`,
                 `${SIM}/emit-route-facts.ts`],
    planner: [`${SIM}/route-demos.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-gamushiro.ts`,
              `${SIM}/emit-route-demos.ts`],
  },
  bag1: {
    stages: [
      { nodes: ['bag1.l_top'], locks: 7 },
      { nodes: ['bag1.left'], locks: 6,
        holdSplit: { piece: 'L', mirrorPiece: 'J', atLock: 7,
                     holdNode: 'bag1.left', elsewhereNode: 'bag1.l_placed_elsewhere' } },
    ],
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
    { lists: ['2.normal.pc'], after: { piece: 'T', spin: 'full', lines: 3, pick: 'first', name: 'TST' },
      lines: 8, rows: 6 },
    { lists: ['2.pc4'], after: { locks: 6 }, lines: 4, rows: 6 },
  ],
  artefact: {
    schema: 'gamushiro-facts/1',
    means: 'for every corpus round whose bag 1 is shiwehi.com\'s ガムシロ積み bag 1 cell for cell (as drawn or mirrored, '
      + 'the L stood on the O at 7 locks or held at 6), the deepest node of that page\'s route tree the round reaches, '
      + 'and how often each node\'s sampling point was reached. A reference opener: the corpus barely plays it',
    notEligible: 'every board is the vendored Triangle engine\'s; which bag-2 and later shape was built has no second implementation. '
      + 'The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'bag-1 opportunities count rounds that reached the sampling point clean (inside the verified prefix, no clear, no garbage before it); '
      + 'bag-2 opportunities allow garbage: complete garbage rows are stripped from the bottom of the board first '
      + '(garbage_rows_stripped), so they count rounds inside the verified prefix with no line cleared by the player before the sample. '
      + 'PC patterns have no separate sampling point and count the rounds that reached their anchor: the bag-1 L-held board for the '
      + '4-line PCs, the 2.normal group for the 8-line ones. A hold is asserted only by the lock-7 piece test. There is no harddrop '
      + 'field for this opener, so no flag. The 妥協 board and the first Imperial Cross board are taller than 8 rows and are not compared. '
      + 'bag2_near is measured against the board before the TST, never a match.',
  },
  rules: () => ({
    bag1_placed_locks: 7, bag1_hold_locks: 6, bag2_lock_index: 12, bag2_garbage: 'strip complete garbage rows from the bottom',
    event_locks: 40, snapshot_locks: 46,
    pc_kinds: [
      { lists: ['2.normal.pc'], frame_after: 'the first TST', lines: 8, rows: 6 },
      { lists: ['2.pc4'], frame_after: '6 locks (the L-held board), no spin', lines: 4, rows: 6 },
    ],
    precedence: 'l_top (7 locks); only if it misses, left (6 locks, the L held) split by the lock-7 piece against the mirror-aware bag-1 L',
    condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
    group_scope: 'the two 2.normal forms share one PC list: PC patterns are scoped by their anchor, the form\'s group',
    bag2_near: 'a bag-1 round with no bag-2 match: the board before its TST, by occupancy, against every bag-2 board: a strict '
      + 'subset (the TST before the board was complete), that board plus exactly four cells, or that board with one piece\'s four cells moved elsewhere',
  }),
  lists: (cases, name) => ({
    l_hold_bag1: cases.filter(c => c.bag1.node === 'bag1.left').map(name),
    l_placed_elsewhere_bag1: cases.filter(c => c.bag1.node === 'bag1.l_placed_elsewhere').map(name),
    bag2_garbage_stripped: cases.filter(c => c.bag2?.node && c.bag2.garbage_rows_stripped > 0)
      .map(c => `${name(c)} (${c.bag2.garbage_rows_stripped})`),
    bag2_none_tst_before_complete: cases.filter(c => c.bag2_near?.kind === 'subset')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')}`),
    bag2_none_extra_piece: cases.filter(c => c.bag2_near?.kind === 'superset')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')} + ${c.bag2_near.extra}`),
    bag2_none_moved_piece: cases.filter(c => c.bag2_near?.kind === 'moved')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')}, ${c.bag2_near.extra} moved`),
    bag2_none_unexplained: cases.filter(c => c.bag2 && !c.bag2.node && !c.bag2_near).map(name),
  }),
  demos: {
    schema: 'gamushiro-demos/1',
    means: 'Constructed replays, one per drawn node of shiwehi.com\'s ガムシロ積み route page: our own piece queue '
         + 'and key inputs, run from an empty board through the vendored Triangle engine, ending on the '
         + 'page\'s drawn board. Not a game anyone played and not corpus data.',
    notEligible: ['not a game anyone played; not corpus data',
                  'one engine, no second implementation of the boards'],
    caveat: {
      order: 'Where the page does not fix the piece order, the order here is ours: the first piece of each of the page\'s '
           + 'before-pairs first (bag 1: J before S and Z before T, the page\'s no-hold conditions for the left pattern, which also '
           + 'put J and Z early as 「%J%Zが早い」 asks), then IOTSZJL, the T into the U slot last. order_reading records it per bag.',
      hold: 'bag1.left holds its L when it arrives (our choice of where: just before the bag\'s S). The hold box is then '
          + 'never empty again: the held L comes out at its slot in bag 2 (the two 通常 forms, the 4-line PCs, the 妥協 form), '
          + 'swapped for the piece that bag places last, which is therefore DEALT at that slot. The 妥協 form\'s trigger '
          + '(T before L and O) is an order of dealing and is met that way: its T arrives fourth, is held, and is fired last '
          + 'as the TST. No other demo holds.',
      chain: 'The 8-line PC patterns and the Imperial Cross boards hang under the page\'s after-the-TST illustration; their '
           + 'demos run through 2.normal#1, the demo that ends on that board. The two 通常 forms are drawn with the TST '
           + 'slot empty and the T on a separate board; the demo fires it there, and so does the 妥協 form.',
      spin: 'Every T-spin kind and line count is the engine\'s verdict on the replayed inputs. The 8-line PC patterns that '
          + 'draw the T flat in the TSD slot fire it as a TSD, except 2.normal.pc#3: the J\'s hook and the S roof its slot, and '
          + 'the planner measured no order in which the engine credits a T-spin clearing those two rows, so its T is placed '
          + 'last, with no spin.',
    },
    unbuilt: DEMO_UNBUILT,
    pieceReadings: [],
    bag1Spec: (n, routes) => {
      const hold = n.id === 'bag1.left';
      return { before: routes.bag1.no_hold.all.map((c: any) => c.before), early: null,
               holdPiece: hold ? 'L' : null, holdBefore: hold ? 'S' : null };
    },
    chainVia: { '2.normal.after': '2.normal#1' },
    spinLetter: n => (tsdT(n) ? { letter: 't', lines: 2 } : null),
  },
};
