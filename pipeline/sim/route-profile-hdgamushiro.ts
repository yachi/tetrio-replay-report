/**
 * ガムシロ積み, harddrop's version (`Gamushiro_Stacking`, pinned revision) — the route profile read by
 * the shared classifier (`route-facts.ts`) and the shared demo planner (`route-demos.ts`). It is the
 * same opener as `route-profile-gamushiro.ts` (shiwehi.com's page) drawn by another site, so it uses
 * the same switches and adds none:
 *
 *  * Bag 1 is the same hold split: the 7-lock board with the L stood on the O (`bag1.l_top`) first;
 *    only if it misses, the 6-lock L-held board (`bag1.left`), split by the piece placed 7th against
 *    the MIRROR-AWARE L. harddrop draws both boards and their mirrors (`mirror_of`), never nodes of
 *    their own here.
 *  * NO FLAG, as on shiwehi's page: no 六個具名定式 column draws ガムシロ積み.
 *  * ONE PERFECT CLEAR KIND: the 8-line PCs after the first TST, one list per form family (A1 and A2
 *    share one occupancy and one list, `group: 2.a`; B and C have one form each). harddrop draws no
 *    4-line PC in bag 2. Form D is ten rows tall and `unmatchable`.
 *
 * Bag 2 strips garbage and a missed bag 2 is explained, never matched, as on shiwehi's page. Since
 * harddrop's A1 and the first L → O patterns are shiwehi's own boards (the transcription gate checks
 * them cell for cell, `routes-file:`), those nodes' counts must equal shiwehi's artefact's, and
 * `hdgamushiro.test.ts` checks it.
 */
import type { RouteProfile } from './route-profile.ts';

/** Nodes with a board that get no demo, and why. */
export const DEMO_UNBUILT: Record<string, string> = {
  'bag1.right': '係 harddrop 第一巡 6 粒圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  'bag1.l_top_right': '係 harddrop 第一巡 7 粒圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  '2.a.redraw': '示意圖：A1 打 TST 前嘅盤面重畫，即係 2.a1 示範最後一粒之前',
  '2.a.after': '示意圖：A1、A2 打完 TST 之後共用嘅盤面，即係 2.a1 示範打完之後嘅盤面',
  '2.b.redraw': '示意圖：B 打 TST 前嘅盤面重畫，即係 2.b 示範最後一粒之前',
  '2.b.after': '示意圖：B 打完 TST 之後嘅盤面，即係 2.b 示範打完之後嘅盤面',
  '2.c.redraw': '示意圖：C 打 TST 前嘅盤面重畫，即係 2.c 示範最後一粒之前',
  '2.c.after': '示意圖：C 打完 TST 之後嘅盤面，即係 2.c 示範打完之後嘅盤面',
};

/** PC patterns whose `t` sits in the TSD slot but which the engine cannot fire as a TSD, MEASURED by
 *  the planner. 2.a.pc#3 is shiwehi's 2.normal.pc#3 cell for cell (the gate checks it), and the
 *  reason is the same; 2.b.pc#2 and 2.c.pc#1 are harddrop's alone. A name here is a red build in the
 *  demos test until it is measured again. */
export const TSD_NOT_FIRED: Record<string, string> = {
  '2.a.pc#3': 'TSD 位上面一行俾 J 嘅鉤（第 3 欄）同 S（第 4 欄）封住：T 要喺佢哋之前入，咁旁邊 S 嗰格（第 5 欄）未有，兩行消唔到；'
    + '之後先入就靠踢牆，引擎唔當係 T-spin。示範將呢粒 T 當普通 T，最後一粒放，打全消',
  '2.b.pc#2': 'planner 量度：放完 LZSJI 之後 T 行得到 TSD 位，但引擎判嘅唔係消兩行嘅 full T-spin。示範將呢粒 T 當普通 T，最後一粒放，打全消',
  '2.c.pc#1': 'planner 量度：放完 LSJOI 之後 T 行得到 TSD 位，但引擎判嘅唔係消兩行嘅 full T-spin。示範將呢粒 T 當普通 T，最後一粒放，打全消',
};

export const tsdT = (n: any): boolean => n.t_in_tsd_slot === true && !(n.id in TSD_NOT_FIRED);

const REPO = `${import.meta.dir}/../..`;
const SIM = import.meta.dir;
const LISTS = ['2.a.pc', '2.b.pc', '2.c.pc'];

export const HDGAMUSHIRO: RouteProfile = {
  key: 'hdgamushiro',
  tag: 'hdgamushiro',
  routesPath: `${REPO}/pipeline/openers/hdgamushiro-routes.json`,
  artefactPath: `${REPO}/analysis/hdgamushiro-facts.json`,
  demosPath: `${REPO}/analysis/hdgamushiro-demos.json`,
  hashFiles: {
    classifier: [`${SIM}/route-facts.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-hdgamushiro.ts`,
                 `${SIM}/emit-route-facts.ts`],
    planner: [`${SIM}/route-demos.ts`, `${SIM}/route-profile.ts`, `${SIM}/route-profile-hdgamushiro.ts`,
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
    { lists: LISTS, after: { piece: 'T', spin: 'full', lines: 3, pick: 'first', name: 'TST' }, lines: 8, rows: 6 },
  ],
  artefact: {
    schema: 'hdgamushiro-facts/1',
    means: 'for every corpus round whose bag 1 is harddrop\'s Gamushiro Stacking bag 1 cell for cell (as drawn or mirrored, '
      + 'the L stood on the O at 7 locks or held at 6), the deepest node of that page\'s second-bag forms and third-bag '
      + 'Perfect Clears the round reaches, and how often each node\'s sampling point was reached. A reference opener: '
      + 'the corpus barely plays it',
    notEligible: 'every board is the vendored Triangle engine\'s; which bag-2 and later shape was built has no second implementation. '
      + 'The Perfect Clear COUNT is anchored by perfect_clear_timing, the shape is not.',
    caveat: 'bag-1 opportunities count rounds that reached the sampling point clean (inside the verified prefix, no clear, no garbage before it); '
      + 'bag-2 opportunities allow garbage: complete garbage rows are stripped from the bottom of the board first '
      + '(garbage_rows_stripped). PC patterns have no separate sampling point and count the rounds that reached their anchor, '
      + 'the form family. A hold is asserted only by the lock-7 piece test. There is no harddrop opener field for this '
      + 'opener, so no flag. Form D is taller than 8 rows and is not compared. Only the page\'s second bag and its 8-line '
      + 'Perfect Clears are transcribed; its other continuations are not. bag2_near is measured against the board before '
      + 'the TST, never a match.',
  },
  rules: () => ({
    bag1_placed_locks: 7, bag1_hold_locks: 6, bag2_lock_index: 12, bag2_garbage: 'strip complete garbage rows from the bottom',
    event_locks: 40, snapshot_locks: 46,
    pc_kinds: [{ lists: LISTS, frame_after: 'the first TST', lines: 8, rows: 6 }],
    precedence: 'l_top (7 locks); only if it misses, left (6 locks, the L held) split by the lock-7 piece against the mirror-aware bag-1 L',
    condition_handedness: 'a mirrored round\'s bag-2 order is read with J<->L and S<->Z swapped',
    group_scope: 'Forms A1 and A2 share one PC list: PC patterns are scoped by their anchor, the form\'s group',
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
    schema: 'hdgamushiro-demos/1',
    means: 'Constructed replays, one per drawn node of harddrop\'s Gamushiro Stacking second bag and 8-line Perfect Clears: '
         + 'our own piece queue and key inputs, run from an empty board through the vendored Triangle engine, ending on the '
         + 'page\'s drawn board. Not a game anyone played and not corpus data.',
    notEligible: ['not a game anyone played; not corpus data',
                  'one engine, no second implementation of the boards'],
    caveat: {
      order: 'The page states one bag-1 order (J before S). Everything else is ours: the first piece of each before-pair '
           + 'first, then IOTSZJL, the T into the U slot last. order_reading records it per bag. The page\'s arrows (L → O and '
           + 'so on) name the forms and are not read as orders: Form A2\'s board contradicts its arrow.',
      hold: 'bag1.left holds its L when it arrives (our choice of where: just before the bag\'s S). The hold box is then '
          + 'never empty again: the held L comes out at its slot in bag 2, swapped for the piece that bag places last.',
      chain: 'The 8-line PC patterns hang under each form family\'s after-the-TST board; their demos run through the form '
           + 'whose TST leaves it (A1 for the A family).',
      spin: 'Every T-spin kind and line count is the engine\'s verdict on the replayed inputs. PC patterns that draw the T flat '
          + 'in the TSD slot fire it as a TSD, except those named in TSD_NOT_FIRED, whose T is placed last, with no spin.',
    },
    unbuilt: DEMO_UNBUILT,
    pieceReadings: [],
    bag1Spec: (n, routes) => {
      const hold = n.id === 'bag1.left';
      return { before: routes.bag1.requires.all.map((c: any) => c.before), early: null,
               holdPiece: hold ? 'L' : null, holdBefore: hold ? 'S' : null };
    },
    chainVia: { '2.a.after': '2.a1', '2.b.after': '2.b', '2.c.after': '2.c' },
    spinLetter: n => (tsdT(n) ? { letter: 't', lines: 2 } : null),
  },
};
