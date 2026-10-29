/**
 * stick spin (SDパフェ) — the route profile for shiwehi.com's stickspin.php, read by the shared
 * classifier (`route-facts.ts`) and the shared demo planner (`route-demos.ts`). The rules are the
 * shared ones; this file says which nodes, which locks and which strings, and the two things this
 * page needs that the other three do not:
 *
 *  * A BAG-1 SPIN STEP (`bag1.spin`). Bag 1 is six pieces (`bag1.left`, 6 locks; the page's right
 *    board is its mirror) and then the T, into a T-spin Single on the bag's 7th lock: stood up
 *    (`bag1.fire`, 火力派生) or laid flat (`bag1.pc`, パフェ派生). The two children draw the same six
 *    pieces with the T as `U`, so a board cannot tell them apart before the spin and the board after
 *    it has cleared a row; the step reads the 7th lock's own cells instead (exactly one child's U
 *    cells, in the bag-1 match's handedness, a full T-spin clearing one line). That clear is the
 *    route's own, so the bag-2 sample's no-clear rule does not stop on it.
 *  * NO FLAG. harddrop's opener transcription (`wiki-openers.json`) has no stick spin field, so
 *    `opener-facts.json` has no column to compare a flag with (`bag1.flag` absent). The cross-check
 *    `stickspin.test.ts` makes instead is against the ordering metric: every Double-first opener of
 *    yachi's from 09-17 on (`opener-facts.json` `ordering.per_round` `dt_order`) is a stick-spin
 *    bag-1 round or a NAMED exception, and every stick-spin bag-1 round of his with a verified window
 *    is Double-first or named.
 *
 * Bag 2 strips garbage as はちみつ砲 and 山岳積み2号 do (`bag2Garbage: 'strip'`), and a missed bag 2
 * is explained, never matched (`bag2Explain`): the board before the round's first TSD against every
 * bag-2 board. The PC lists are the 8-line ones (TSS 1 + TSD 2 + a 5-row body), framed after the TSD.
 */
import type { RouteProfile, PieceReading } from './route-profile.ts';

/** The page's one colour slip (`2.mochi.pc#13:colour` in the transcription): the L's fourth cell,
 *  across the row that clears under it, drawn in the J's colour. Read as the L it has to be, by the
 *  demo only; the corpus classifier matches the drawing as drawn. */
export const PIECE_READINGS: PieceReading[] = [
  { node: '2.mochi.pc#13', drawn: 'j', reads_as: 'L', cells: [[9, 1]],
    reason: 'j 有 5 格、l 得 3 格：呢一格同上面嘅 l 隔住一行已消嘅行，合埋先係一粒 L' },
];

/** Nodes with a board that get no demo, and why. Every reason is the page's own drawing or the
 *  planner's measured failure; a node the planner cannot build must be named here (the test compares
 *  this with the artefact both ways), never dropped. */
export const DEMO_UNBUILT: Record<string, string> = {
  'bag1.right': '係原頁左邊嗰幅第一巡圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  'bag1.fire.after': '示意圖：TSS 之後嘅盤面，即係 bag1.fire 示範打完之後嘅盤面',
  'bag1.pc.after': '示意圖：TSS 之後嘅盤面，即係 bag1.pc 示範打完之後嘅盤面',
  '2.fire.tsd': '示意圖：兩個火力派生 2巡目形打 TSD 嘅位，即係 2.fire#1 示範最後一粒',
  '2.sd.after': '示意圖：TSD 之後嘅盤面，即係 2.sd 示範打完之後嘅盤面',
  '2.sd.tst.spin': '示意圖：TST 嘅位同消嘅行，即係 2.sd.tst 示範最後一粒',
  '2.sd.imperial.spin': '示意圖：Imperial Cross 嘅 TSD 位同消嘅兩行，即係 2.sd.imperial 示範最後一粒',
  '2.sd.stmb.spin': '示意圖：STMB Cave 嘅 TSD 位同消嘅行，即係 2.sd.stmb 示範最後一粒',
  '2.mochi.after': '示意圖：TSD 之後嘅盤面，即係 2.mochi 示範打完之後嘅盤面',
};

/** Two SDパフェ PC patterns whose `t` the engine can only place as a full T-spin Single. Both stand
 *  the T upright in the column-6 well under the bag-2 J: on the board just before it, `reach()`
 *  finds no plain or mini arrival at the drawn cells, only a rotation with three corners filled, so
 *  the engine credits a full TSS clearing one line. The page draws a plain `t`; reading it as the
 *  bag's spin slot is OUR READING. `stickspin-demos.test.ts` measures it on the committed boards and,
 *  with the reading removed, has the planner search every order of the PC bag and fail on exactly
 *  these two (a hand probe of 2026-10-28 found no set of pieces placed after a plain T that builds
 *  either). */
export const PC_T_TSS = new Set(['2.sd.pc#7', '2.sd.pc#16']);

const REPO = `${import.meta.dir}/../..`;
const SIM = import.meta.dir;

export const STICKSPIN: RouteProfile = {
  key: 'stickspin',
  tag: 'stickspin',
  routesPath: `${REPO}/pipeline/openers/stickspin-routes.json`,
  artefactPath: `${REPO}/analysis/stickspin-facts.json`,
  demosPath: `${REPO}/analysis/stickspin-demos.json`,
  hashFiles: {
    classifier: [`${SIM}/route-facts.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-stickspin.ts`,
                 `${SIM}/emit-route-facts.ts`],
    planner: [`${SIM}/route-demos.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-stickspin.ts`,
              `${SIM}/emit-route-demos.ts`],
  },
  bag1: {
    stages: [{ nodes: ['bag1.left'], locks: 6 }],
    spin: { nodes: ['bag1.fire', 'bag1.pc'], atLock: 7, spin: 'full', lines: 1 },
  },
  bag2Lock: 12,
  bag2Garbage: 'strip',
  bag2Explain: { nearCells: 8 },
  eventLocks: 40,
  snapshotLocks: 46,
  pcRows: 6,
  pcLines: 8,
  pcAfter: { piece: 'T', spin: 'full', lines: 2 },
  artefact: {
    schema: 'stickspin-facts/1',
    means: 'for every corpus round whose first six pieces are shiwehi.com\'s stick spin (SDパフェ) bag 1 cell for cell '
      + '(as drawn or mirrored, the T not yet placed), whether its 7th lock fires the T-spin Single stood up (火力派生) or '
      + 'laid flat (パフェ派生) as the page draws it, and the deepest node of that page\'s route tree the round reaches',
    notEligible: 'every board is the vendored Triangle engine\'s; which bag-1 spin and which bag-2 and later shape was built has no second '
      + 'implementation. The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'bag-1 opportunities count rounds that reached 6 locks clean (inside the verified prefix, no clear, no garbage before it); the '
      + 'spin step counts those whose 7th lock is inside the verified prefix with no garbage before it, and asserts a node only when '
      + 'that lock is a T on exactly one drawn U slot. bag-2 and snapshot opportunities allow garbage: complete garbage rows are '
      + 'stripped from the bottom of the board first (garbage_rows_stripped), so they count rounds inside the verified prefix with no '
      + 'line cleared by the player before the sample but the bag-1 TSS. There is no harddrop field for this opener, so no flag. '
      + 'bag2_near is measured against the board before the first TSD, never a match.',
  },
  rules: () => ({
    bag1_locks: 6, bag1_spin_lock: 7, bag1_spin: 'a full T-spin clearing 1 line on exactly one child board\'s U cells, '
      + 'in the bag-1 match\'s handedness', bag2_lock_index: 12,
    bag2_garbage: 'strip complete garbage rows from the bottom', bag2_route_clear: 'the bag-1 TSS is the route\'s own clear',
    event_locks: 40, snapshot_locks: 46, pc_rows: 6, pc_lines: 8, pc_frame_after: 'the first TSD',
    condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
    bag2_near: 'a bag-1 round with no bag-2 match: the board before its first TSD, by occupancy, against every bag-2 board: a strict '
      + 'subset (the TSD before the board was complete), that board plus exactly four cells, that board with one piece\'s four cells moved elsewhere, '
      + 'or else the nearest bag-2 board(s) when they differ by at most 8 cells (two pieces\' worth): measured, never a match',
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
    bag2_none_near: cases.filter(c => c.bag2_near?.kind === 'near')
      .map(c => `${name(c)} under ${c.bag2_near.groups.join('+')}${c.bag2_near.mirrored ? ' (mirrored)' : ''}, `
        + `${c.bag2_near.cells} cells (drawn ${c.bag2_near.missing} missing, ${c.bag2_near.extra} extra)`),
    bag2_none_unexplained: cases.filter(c => c.bag2 && !c.bag2.node && !c.bag2_near).map(name),
  }),
  demos: {
    schema: 'stickspin-demos/1',
    means: 'Constructed replays, one per drawn node of shiwehi.com\'s stick spin (SDパフェ) route page: our own piece queue '
         + 'and key inputs, run from an empty board through the vendored Triangle engine, ending on the '
         + 'page\'s drawn board. Not a game anyone played and not corpus data.',
    notEligible: ['not a game anyone played; not corpus data',
                  'one engine, no second implementation of the boards'],
    caveat: {
      order: 'Where the page does not fix the piece order, the order here is ours: the first piece of each of the page\'s '
           + 'before-pairs first (bag 1: O before Z and J before L, the page\'s no-hold conditions for the left pattern), then '
           + 'IOTSZJL, the T into the U slot last. order_reading records it per bag.',
      hold: 'No demo holds: the page\'s bag 1 is built without hold under its stated conditions, and nothing later is drawn held.',
      chain: 'Bag 2 hangs under the page\'s after-the-TSS illustrations and the PC patterns under its after-the-TSD ones; their '
           + 'demos run through the demo that ends on that board (bag1.fire, bag1.pc, 2.sd, 2.mochi). The fallback boards '
           + '(TST, Imperial Cross, STMB Cave) are drawn with the slot empty and the T on a separate board; the demo fires it there.',
      spin: 'Every T-spin kind and line count is the engine\'s verdict on the replayed inputs. In 2.sd.pc#7 and 2.sd.pc#16 the '
          + 'page draws a plain t that can only go in by a rotation the engine credits as a full T-spin Single, so those two '
          + 'fire it as a TSS before the Perfect Clear (our reading; every other PC pattern places its T without a spin).',
    },
    unbuilt: DEMO_UNBUILT,
    pieceReadings: PIECE_READINGS,
    spinLetter: n => (PC_T_TSS.has(n.id) ? { letter: 't', lines: 1 } : null),
    bag1Spec: (_n, routes) => ({ before: routes.bag1.no_hold.all.map((c: any) => c.before), early: null,
                                 holdPiece: null, holdBefore: null }),
    chainVia: {
      'bag1.fire.after': 'bag1.fire',
      'bag1.pc.after': 'bag1.pc',
      '2.sd.after': '2.sd',
      '2.mochi.after': '2.mochi',
    },
  },
};
