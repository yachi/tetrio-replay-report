/**
 * 合掌TSDパフェ (Gassho TSD) — the route profile for shiwehi.com's gasshotsd.php, read by the shared
 * classifier (`route-facts.ts`) and the shared demo planner (`route-demos.ts`).
 *
 * Bag 1 is the hole-empty 基本形 at 7 locks (`bag1.left`; the right board is its mirror, the I-early
 * board is the same occupancy coloured differently and is not a stage). The opening TSD is the bag-2
 * T into the 3-wide hole. Bag 2 is sampled after 10 locks (the 3-mino pre-place, index 9): ZJO and
 * SLO share one occupancy and are one group, and so do the two donation drawings. The 9-row 63-stack
 * board and the 10-row REN-after board are unmatchable.
 *
 * NO FLAG and NO HOLD SPLIT. The catalogue entry is the 基本形 by occupancy (`extract_gasshotsd_routes`);
 * nothing here asserts a hold. The cross-check the test makes is that no corpus round's clean 7-lock
 * board is this shape: the artefact's cases are empty, and that emptiness is pinned.
 *
 * The drawn PC bodies are 2 rows (the page's 4ライン, TSD 2 + body 2) and 4 rows (the page's 6ライン,
 * TSD 2 + body 4). `pcKinds` files a Perfect Clear by the cumulative count.
 *
 * A REFERENCE OPENER for this corpus: no round matches bag 1, so there is no node page (an empty one
 * is refused). The overview and the demo page are the site. The day a round matches, the bag-1-only
 * page is added with that case.
 */
import type { RouteProfile } from './route-profile.ts';

const MIRROR = '係原頁左邊基本形左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇';
const SAME = '同基本形佔同一格，只係 I 同上色唔同（原頁話同形）；唔當第二個第一巡形';
const DERIVED = '由上一幅打完 TSD 推導出嚟嘅灰格，原頁冇另畫';
const TALL = '高過分類器嘅八行，冇比對';
const MUTED = '消行走嘅格畫成淺灰 C，示範器唔讀呢個字母做已經砌好嘅格';
const SHADE = '用第二色（h n k m r y u）畫後一袋嘅方塊；一個袋每款得一粒，示範器砌唔到兩粒一樣嘅';
const LATER = '打完 TSD 之後先砌嘅延續，唔係由空盤一個袋砌得完嘅圖';

/** Nodes with a board that get no demo, and why. `bag1.left` is the one demo. */
export const DEMO_UNBUILT: Record<string, string> = {
  'bag1.right': MIRROR,
  'bag1.i_early': SAME,
  '2.tsd': '示意圖：基本形個三格窿畫成 TSD 位，U 當空嘅話同基本形同一格',
  '2.tsd.after': DERIVED,
  '2.pc4#1': MUTED,
  '2.pc4.follow': LATER,
  '2.pc4.next': LATER,
  '2.zjo': MUTED,
  '2.zjo.after': DERIVED,
  '2.slo': MUTED,
  '2.slo.after': DERIVED,
  '2.oz.after': 'OZ 嗰幅 PC 嘅灰格，原頁冇畫設置圖，由幅圖入面嘅 c 格推導',
  '2.oz.pc#1': '兩粒 S 畫成同一個字母（八格 s），一個袋得一粒 S',
  '2.donate.a': LATER,
  '2.donate.b': LATER,
  '2.donate.after': '示意圖：兩幅捐贈圖打完 TSD 之後嘅盤面',
  '2.flat': TALL,
  '2.flat.after': MUTED,
  '2.stsd': MUTED,
  '2.stsd.after': LATER,
  '2.ren': MUTED,
  '2.ren.after': TALL,
  ...Object.fromEntries([1, 2, 3, 4, 5, 6, 7].map(k => [`2.zjo.pc#${k}`, SHADE])),
  ...Object.fromEntries([1, 2, 3, 4, 5].map(k => [`2.slo.pc#${k}`, SHADE])),
  ...Object.fromEntries([1, 2, 3, 4].map(k => [`2.holdi.pc#${k}`, SHADE])),
};

const REPO = `${import.meta.dir}/../..`;
const SIM = import.meta.dir;

export const GASSHOTSD: RouteProfile = {
  key: 'gasshotsd',
  tag: 'gasshotsd',
  routesPath: `${REPO}/pipeline/openers/gasshotsd-routes.json`,
  artefactPath: `${REPO}/analysis/gasshotsd-facts.json`,
  demosPath: `${REPO}/analysis/gasshotsd-demos.json`,
  hashFiles: {
    classifier: [`${SIM}/route-facts.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-gasshotsd.ts`,
                 `${SIM}/emit-route-facts.ts`],
    planner: [`${SIM}/route-demos.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-gasshotsd.ts`,
              `${SIM}/emit-route-demos.ts`],
  },
  bag1: {
    stages: [{ nodes: ['bag1.left'], locks: 7 }],
  },
  bag2Lock: 9,
  bag2Garbage: 'strip',
  bag2Explain: true,
  eventLocks: 40,
  snapshotLocks: 46,
  pcRows: 6,
  pcLines: 6,
  pcAfter: { piece: 'T', spin: 'full', lines: 2 },
  pcKinds: [
    { lists: ['2.pc4'], after: { piece: 'T', spin: 'full', lines: 2, pick: 'first', name: 'TSD' },
      lines: 4, rows: 6 },
    { lists: ['2.zjo.pc', '2.slo.pc', '2.holdi.pc', '2.oz.pc'],
      after: { piece: 'T', spin: 'full', lines: 2, pick: 'first', name: 'TSD' },
      lines: 6, rows: 6 },
  ],
  artefact: {
    schema: 'gasshotsd-facts/1',
    means: 'for every corpus round whose first seven pieces are shiwehi.com\'s 合掌TSDパフェ bag 1 cell for cell '
      + '(as drawn or mirrored, the T stacked and the 3-wide hole empty), the deepest node of that page\'s route '
      + 'tree the round reaches. A reference opener: the corpus does not play it',
    notEligible: 'every board is the vendored Triangle engine\'s; which later shape was built has no second '
      + 'implementation. The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'bag-1 opportunities count rounds that reached 7 locks clean (inside the verified prefix, no clear, no '
      + 'garbage before it). bag 2 is sampled after 10 locks; complete garbage rows are stripped from the bottom first. '
      + 'ZJO and SLO are one occupancy (group 2.preplace), and the two donation drawings are one occupancy. The 4-line '
      + 'PC is a 2-row body after the TSD (cumulative 4); the 6-line PCs are 4-row bodies (cumulative 6). The 9-row '
      + '63-stack board and the 10-row REN-after board are not compared. There is no harddrop field, so no flag. '
      + 'bag2_near is measured against the board before the first TSD, never a match.',
  },
  rules: () => ({
    bag1_locks: 7,
    bag2_lock_index: 9,
    bag2_garbage: 'strip complete garbage rows from the bottom',
    event_locks: 40,
    snapshot_locks: 46,
    pc_kinds: [
      { lists: ['2.pc4'], frame_after: 'the first TSD', lines: 4, rows: 6 },
      { lists: ['2.zjo.pc', '2.slo.pc', '2.holdi.pc', '2.oz.pc'], frame_after: 'the first TSD', lines: 6, rows: 6 },
    ],
    condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
    group_scope: 'ZJO and SLO share one occupancy, so their PC lists are scoped by the group 2.preplace; the two donation drawings likewise',
    bag2_near: 'a bag-1 round with no bag-2 match: the board before its first TSD, by occupancy, against every bag-2 board: a strict '
      + 'subset, that board plus exactly four cells, or that board with one piece\'s four cells moved elsewhere',
  }),
  lists: (cases, name) => ({
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
    schema: 'gasshotsd-demos/1',
    means: 'Constructed replays, one per drawn node of shiwehi.com\'s 合掌TSDパフェ route page that the planner can build '
         + 'from an empty board: the bag-1 基本形. The other drawings are named unbuilt, with the reason. '
         + 'Not a game anyone played and not corpus data.',
    notEligible: ['not a game anyone played; not corpus data',
                  'one engine, no second implementation of the boards'],
    caveat: {
      order: 'Bag 1 places O and S before L, and T before J, which is the page\'s no-hold condition for the left pattern, '
           + 'then the remaining pieces IOTSZJL with those constraints. order_reading records it.',
      hold: 'No demo holds. The page\'s bag 1 is built without a held piece under its stated conditions.',
      chain: 'Only the bag-1 基本形 is built, from an empty board. Later drawings are continuations, second-shade solutions, '
           + 'or taller than eight rows, and are named rather than built.',
      spin: 'The bag-1 demo places no T-spin: the bag-1 T is stacked in the stack, and the opening TSD is the next bag\'s T.',
    },
    unbuilt: DEMO_UNBUILT,
    pieceReadings: [],
    bag1Spec: (_n, routes) => ({ before: routes.bag1.no_hold.all.map((c: any) => c.before), early: null,
                                 holdPiece: null, holdBefore: null }),
  },
};
