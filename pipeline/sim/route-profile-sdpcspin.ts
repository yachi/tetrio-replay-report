/**
 * SDPC Spin — the route profile for harddrop's SDPC_Spin page (the first route page transcribed from
 * harddrop wikitext rather than shiwehi.com; `pipeline/openers/sdpcspin-routes.json`, gated by
 * `extract_sdpcspin_routes.py`), read by the shared classifier (`route-facts.ts`). The rules are the
 * shared ones; this file says which nodes, which locks and which strings:
 *
 *  * Bag 1 is stick spin's shape: a 6-lock STAGE board (the bag less its T) and then the T laid flat
 *    into a T-spin Single on the bag's 7th lock (`bag1.spin`, as stick spin's パフェ派生). The page
 *    draws bag 1 only WITH the T placed, in two colourings of one occupancy (`bag1.lj`, the L under
 *    the J at column 1; `bag1.jl`, the J at column 1 — stick spin's bag1.pc mirrored), so the stage
 *    boards are DERIVED (`bag1.lj.left`, `bag1.jl.left`: each TSS board with its U cells removed) and
 *    each TSS board carries `spin_of` its own stage board. Colour decides at the stage: the two TSS
 *    boards draw the same U cells, so the spin step alone could never tell them apart. The TSS's line
 *    is the route's own, so it does not stop the bag-2 sample.
 *  * NO FLAG, as stick spin and ガムシロ積み: harddrop's opener transcription (`wiki-openers.json`)
 *    draws no SDPC Spin field. `sdpcspin.test.ts` cross-checks against the ordering metric (the route
 *    fires TSS, TSD, then a TST: Double-first) and against stick spin's own bag-1 cases.
 *  * ONE PERFECT CLEAR KIND (`pcKinds`): the Third C-Spin build's 14-line PCs (TSS 1 + TSD 2 + TST 3 +
 *    the Imperial Cross's first TSD 2 + a 6-row body whose last spin is the Imperial Cross's second
 *    TSD), framed after the first 28 locks: the four bags before the body (bag 1's TSS board, 2.tsd,
 *    3.third, 3.third.imperial) each place all seven of their pieces, the Imperial Cross's first TSD
 *    last. NOT 「after the last TSD before the PC」: every pattern roofs its T slot (the body's s/z or
 *    o over it, the stack on both sides), so the body's own TSD always fires BEFORE the PC's last lock
 *    and would be the one picked (measured by the demo planner and re-measured in
 *    `sdpcspin-demos.test.ts`). The frame is 7 rows, not the body's 6: the transcription draws each
 *    pattern with the page's empty row above the body, and `patternMatches` refuses a pattern taller
 *    than its frame, so a 6-row frame could never match one. The default kind would find none: it
 *    reads bag-3 lists, and this one is bag 5.
 *
 * Bag 2 strips garbage (`bag2Garbage: 'strip'`) and a missed bag 2 is explained, never matched
 * (`bag2Explain`), measured against the board before the bag-2 TSD (`pcAfter`). Bag 3 and later are
 * snapshot routes under 2.tsd; the boards taller than the classifier's 8 rows are `unmatchable` in the
 * transcription and never compared.
 *
 * The demo half (`demos`) builds one constructed replay per drawn node (`route-demos.ts`). The page
 * states no bag-1 order, so bag 1's queue is the planner's default priority; 2.tsd hangs under the
 * after-the-TSS illustration through `bag1.jl` (`chainVia`), and the bag-3 builds under the after-the-TSD
 * one through `2.tsd`.
 */
import type { RouteProfile } from './route-profile.ts';

/** Nodes with a board that get no demo, and why: the page's illustrations and the boards that are not
 *  one board state. A node the planner cannot build is the test's to name (`sdpcspin-demos.test.ts`). */
export const DEMO_UNBUILT: Record<string, string> = {
  'bag1.after': '示意圖：TSS 之後嘅盤面（兩種 J/L 顏色消完都係呢幅），即係 bag1.jl 示範打完之後嘅盤面',
  '2.after': '示意圖：TSD 之後嘅盤面，即係 2.tsd 示範打完之後嘅盤面',
  '3.second.cspin.z_early': '同一粒 Z 畫咗兩次（放咗喺 J 上面，原本嘅位用撇號標住）：唔係一個盤面',
  '3.second.cspin.dt#1': 'C-Spin 嘅殘餘用淺色（大寫）畫，但第三巡嗰粒 I 畫成實色，同新嗰粒 I 一齊即係兩粒 I：'
    + '唔係一個巡次嘅砌法（transcription 嘅 known_discrepancies）',
  '3.second.cspin.dt#2': 'C-Spin 嘅殘餘用淺色（大寫）畫，但第三巡嗰粒 I 畫成實色，同新嗰粒 I 一齊即係兩粒 I：'
    + '唔係一個巡次嘅砌法（transcription 嘅 known_discrepancies）',
};

const REPO = `${import.meta.dir}/../..`;
const SIM = import.meta.dir;

export const SDPCSPIN: RouteProfile = {
  key: 'sdpcspin',
  tag: 'sdpcspin',
  routesPath: `${REPO}/pipeline/openers/sdpcspin-routes.json`,
  artefactPath: `${REPO}/analysis/sdpcspin-facts.json`,
  demosPath: `${REPO}/analysis/sdpcspin-demos.json`,
  hashFiles: {
    classifier: [`${SIM}/route-facts.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-sdpcspin.ts`,
                 `${SIM}/emit-route-facts.ts`],
    planner: [`${SIM}/route-demos.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-sdpcspin.ts`,
              `${SIM}/emit-route-demos.ts`],
  },
  bag1: {
    stages: [{ nodes: ['bag1.jl.left', 'bag1.lj.left'], locks: 6 }],
    spin: { nodes: ['bag1.jl', 'bag1.lj'], atLock: 7, spin: 'full', lines: 1 },
  },
  bag2Lock: 12,
  bag2Garbage: 'strip',
  bag2Explain: true,
  eventLocks: 40,
  snapshotLocks: 46,
  pcRows: 6,
  pcLines: 14,
  pcAfter: { piece: 'T', spin: 'full', lines: 2 },
  pcKinds: [
    { lists: ['3.third.imperial.pc'],
      after: { locks: 28 }, lines: 14, rows: 7 },
  ],
  artefact: {
    schema: 'sdpcspin-facts/1',
    means: 'for every corpus round whose first six pieces are harddrop\'s SDPC Spin bag 1 cell for cell (either of the page\'s '
      + 'two J/L colourings, as drawn or mirrored, the T not yet placed), whether its 7th lock fires the T-spin Single laid flat '
      + 'as the page draws it, and the deepest node of that page\'s route tree the round reaches',
    notEligible: 'every board is the vendored Triangle engine\'s; which bag-1 spin and which bag-2 and later shape was built has no second '
      + 'implementation. The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'the page draws bag 1 only with the T placed; the 6-lock stage boards are those boards with the T removed (derived in the '
      + 'transcription). bag-1 opportunities count rounds that reached 6 locks clean (inside the verified prefix, no clear, no garbage '
      + 'before it); the spin step counts those whose 7th lock is inside the verified prefix with no garbage before it, and asserts a '
      + 'node only when that lock is a T on the drawn U slot. bag-2 and snapshot opportunities allow garbage: complete garbage rows are '
      + 'stripped from the bottom of the board first (garbage_rows_stripped), so they count rounds inside the verified prefix with no '
      + 'line cleared by the player before the sample but the bag-1 TSS. There is no harddrop field for this opener, so no flag. '
      + 'Boards taller than 8 rows are not compared. bag2_near is measured against the board before the bag-2 TSD, never a match.',
  },
  rules: () => ({
    bag1_locks: 6, bag1_spin_lock: 7, bag1_spin: 'a full T-spin clearing 1 line on the TSS board\'s U cells, '
      + 'in the bag-1 match\'s handedness and colouring', bag2_lock_index: 12,
    bag2_garbage: 'strip complete garbage rows from the bottom', bag2_route_clear: 'the bag-1 TSS is the route\'s own clear',
    event_locks: 40, snapshot_locks: 46,
    pc_kinds: [{ lists: ['3.third.imperial.pc'], frame_after: 'the first 28 locks (four 7-piece bags, the Imperial Cross\'s first TSD last); '
                 + 'the body\'s own TSD fires before the PC\'s last lock, its slot being roofed',
                 lines: 14, rows: 7, rows_note: 'the 6-row body and the empty row the page draws above it' }],
    condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
    bag2_near: 'a bag-1 round with no bag-2 match: the board before its first TSD, by occupancy, against every bag-2 board: a strict '
      + 'subset (the TSD before the board was complete), that board plus exactly four cells, or that board with one piece\'s four cells moved '
      + 'elsewhere: measured, never a match',
  }),
  lists: (cases, name) => ({
    bag1_spin_off_page: cases.filter(c => c.bag1.spin && !c.bag1.spin.node)
      .map(c => `${name(c)} (${c.bag1.spin.piece} ${c.bag1.spin.spin} ${c.bag1.spin.lines})`),
    bag2_garbage_stripped: cases.filter(c => c.bag2?.node && c.bag2.garbage_rows_stripped > 0)
      .map(c => `${name(c)} (${c.bag2.garbage_rows_stripped})`),
    bag2_none_tsd_before_complete: cases.filter(c => c.bag2_near?.kind === 'subset')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')}`),
    bag2_none_extra_piece: cases.filter(c => c.bag2_near?.kind === 'superset')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')} + ${c.bag2_near.extra}`),
    bag2_none_moved_piece: cases.filter(c => c.bag2_near?.kind === 'moved')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')}, ${c.bag2_near.extra} moved`),
    bag2_none_unexplained: cases.filter(c => c.bag2 && !c.bag2.node && !c.bag2_near).map(name),
  }),
  demos: {
    schema: 'sdpcspin-demos/1',
    means: 'Constructed replays, one per drawn node of harddrop\'s SDPC Spin page: our own piece queue and key inputs, '
         + 'run from an empty board through the vendored Triangle engine, ending on the page\'s drawn board. Not a game '
         + 'anyone played and not corpus data.',
    notEligible: ['not a game anyone played; not corpus data',
                  'one engine, no second implementation of the boards'],
    caveat: {
      order: 'The page fixes no bag-1 order and the order here is ours: IOTSZJL as gravity allows, the T into the U slot '
           + 'last. Later bags put the first piece of each of the page\'s before-pairs first. order_reading records it per bag.',
      hold: 'No demo holds. The page saves the I in its alternate fourth bag and holds the O to tuck after one third-build '
          + 'TSD; the demos deal the saved I last and never place it, and do not tuck.',
      chain: 'bag 1 is drawn in two J/L colourings with one after-the-TSS illustration; 2.tsd runs through bag1.jl (stick spin\'s '
           + 'bag1.pc mirrored), and the bag-3 builds through 2.tsd, the demo that ends on the after-the-TSD illustration. The '
           + 'stage boards bag1.lj.left and bag1.jl.left place six pieces and leave the T unplaced.',
      spin: 'Every T-spin kind and line count is the engine\'s verdict on the replayed inputs.',
    },
    unbuilt: DEMO_UNBUILT,
    pieceReadings: [],
    bag1Spec: () => ({ before: [], early: null, holdPiece: null, holdBefore: null }),
    chainVia: { 'bag1.after': 'bag1.jl', '2.after': '2.tsd' },
  },
};
