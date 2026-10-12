/**
 * 迷走砲 (Stray Cannon) — the route profile for shiwehi.com's meisou.php, read by the shared
 * classifier (`route-facts.ts`) and the shared demo planner (`route-demos.ts`). Every 迷走砲-specific
 * constant, string and named rule of the two modules lives here, moved verbatim from the files that
 * held them before the generalisation (`emit-stray-cannon-facts.ts`, `stray-cannon-demos.ts`, now
 * shims). The strings ship inside `analysis/stray-cannon-facts.json` and `-demos.json`, so they are
 * byte contract: `stray-cannon.test.ts` and `stray-cannon-demos.test.ts` rebuild both byte for byte.
 */
import type { RouteProfile, PieceReading } from './route-profile.ts';

const REPO = `${import.meta.dir}/../..`;
const SIM = import.meta.dir;

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

/** The page's two inconsistent colourings (`known_discrepancies` in meisou-routes.json): a cell
 *  group drawn in one piece's colour that can only be another piece. Cells are [x, row from the
 *  bottom]. ONE table. The corpus classifier does not apply it: no corpus PC matched either drawing under
 *  this reading (measured when it was written), so colour-matching them as drawn files nothing wrongly. */
export const PIECE_READINGS: PieceReading[] = [
  { node: '2.ideal.pc#16', drawn: 'z', reads_as: 'S', cells: [[1, 2], [2, 2]],
    reason: 'z 有 6 格、s 得 2 格：呢兩格同上面嘅 ss 隔住一行已消嘅行，合埋先係一粒 S' },
  { node: '2.i_early.pc#11', drawn: 'j', reads_as: 'L', cells: [[0, 4], [1, 4], [2, 4]],
    reason: 'j 有 7 格、l 得 1 格：呢三格同下面嘅 l 隔住兩行已消嘅行，合埋先係一粒 L' },
];

/** Nodes with a board that get no demo, and why. A node the planner cannot build must be named here
 *  with its reason (the test compares this with the artefact both ways), never dropped. */
export const DEMO_UNBUILT: Record<string, string> = {
  '2.ideal.fire.stmb_template': '「p」格冇指定填法；佢嘅例就係 stmb_example 嘅示範',
};

export const MEISOU: RouteProfile = {
  key: 'meisou',
  tag: 'stray-cannon',
  routesPath: `${REPO}/pipeline/openers/meisou-routes.json`,
  artefactPath: `${REPO}/analysis/stray-cannon-facts.json`,
  demosPath: `${REPO}/analysis/stray-cannon-demos.json`,
  hashFiles: {
    classifier: [`${SIM}/route-facts.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-meisou.ts`,
                 `${SIM}/emit-stray-cannon-facts.ts`],
    planner: [`${SIM}/route-demos.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-meisou.ts`,
              `${SIM}/stray-cannon-demos.ts`],
  },
  bag1: {
    stages: [
      { nodes: ['bag1.z_right', 'bag1.z_left'], locks: BAG1_PLACED_LOCKS },
      { nodes: ['bag1.z_hold'], locks: BAG1_HOLD_LOCKS,
        holdSplit: { piece: 'Z', mirrorPiece: 'S', atLock: BAG1_PLACED_LOCKS,
                     holdNode: 'bag1.z_hold', elsewhereNode: 'bag1.z_placed_elsewhere' } },
    ],
    flag: { field: 'matched_at_6', stage: 1 },
    lockPieceField: 'lock7_piece',
  },
  bag2Lock: BAG2_LOCK,
  bag2Garbage: 'refuse',
  eventLocks: EVENT_LOCKS,
  snapshotLocks: SNAPSHOT_LOCKS,
  pcRows: PC_ROWS,
  pcLines: PC_LINES,
  pcAfter: { piece: 'T', spin: 'full', lines: 3 },
  artefact: {
    schema: 'stray-cannon-facts/1',
    means: 'for every corpus round whose bag 1 is shiwehi.com\'s 迷走砲 bag 1 cell for cell (as drawn or mirrored), '
      + 'the deepest node of that page\'s route tree the round reaches, and how often each node\'s sampling point was reached clean',
    notEligible: 'every board is the vendored Triangle engine\'s; which bag-2 and bag-3 shape was built has no second implementation. '
      + 'The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'opportunities count rounds that reached a node\'s sampling point clean (inside the verified prefix, no clear, no garbage before it); '
      + 'bag-3 nodes have no separate sampling point and count the rounds that reached their parent. A hold is asserted only by the lock-7 piece test.',
  },
  rules: () => ({
    bag1_placed_locks: BAG1_PLACED_LOCKS, bag1_hold_locks: BAG1_HOLD_LOCKS, bag2_lock_index: BAG2_LOCK,
    event_locks: EVENT_LOCKS, snapshot_locks: SNAPSHOT_LOCKS, pc_rows: PC_ROWS, pc_lines: PC_LINES,
    precedence: 'z_right, then z_left (7 locks); only if neither, z_hold (6 locks) split by the lock-7 piece against the mirror-aware bag-1 Z',
    condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
  }),
  lists: (cases, name) => ({
    z_hold_bag1: cases.filter(c => c.bag1.node === 'bag1.z_hold').map(name),
    z_placed_elsewhere_bag1: cases.filter(c => c.bag1.node === 'bag1.z_placed_elsewhere').map(name),
    z_left_bag1: cases.filter(c => c.bag1.node === 'bag1.z_left').map(name),
    i_early: cases.filter(c => c.bag2?.node === '2.i_early').map(c => name(c) + (c.bag2.mirrored ? ' (mirrored)' : '')),
    tst_donate: cases.filter(c => c.snapshots.some((s: any) => s.node === '2.normal_OS.tst_donate')).map(name),
  }),
  demos: {
    schema: 'stray-cannon-demos/1',
    means: 'Constructed replays, one per drawn node of shiwehi.com\'s 迷走砲 route page: our own piece queue '
         + 'and key inputs, run from an empty board through the vendored Triangle engine, ending on the '
         + 'page\'s drawn board. Not a game anyone played and not corpus data.',
    notEligible: ['not a game anyone played; not corpus data',
                  'one engine, no second implementation of the boards'],
    caveat: {
      order: 'Where the page does not fix the piece order, the order here is ours: the early piece first, '
           + 'the first piece of each of the page\'s before-pairs next, then IOTSZJL, the T into a drawn U last '
           + 'where the drawing shows U empty. order_reading records it per bag.',
      hold: 'Only bag1.z_hold uses hold: its Z is held when it arrives, just before J. No other demo holds.',
      early: 'The page gives no threshold for "early"; the demo puts the early piece first in its bag.',
      colour_readings: 'Two Perfect Clear drawings colour one piece in another piece\'s colour; the demo builds '
                     + 'the piece the cells have to be (piece_readings).',
      spin: 'Every T-spin kind and line count is the engine\'s verdict on the replayed inputs.',
    },
    unbuilt: DEMO_UNBUILT,
    pieceReadings: PIECE_READINGS,
    bag1Spec: (n, routes) => {
      const r = routes.bag1;
      return { before: n.id === 'bag1.z_right' ? [r.hold_free.before] : [], early: r.requires.early,
               holdPiece: n.id === 'bag1.z_hold' ? 'Z' : null, holdBefore: n.id === 'bag1.z_hold' ? 'J' : null };
    },
  },
};
