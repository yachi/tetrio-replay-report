/**
 * The shape of an opener's ROUTE PROFILE: everything the shared route classifier (`route-facts.ts`)
 * and the shared demo planner (`route-demos.ts`) need to know about one shiwehi.com route page that
 * is not in its transcribed routes JSON. Types only, no data: each opener's profile lives in its own
 * file (`route-profile-meisou.ts`, `route-profile-honeycup.ts`,
 * `route-profile-mountainous2.ts`, `route-profile-stickspin.ts`), so editing one opener's profile
 * stales that opener's artefacts and nobody else's, while an edit to shared code stales all — the
 * md5 inputs (`hashFiles`) are scoped that way on purpose.
 *
 * ONE implementation per rule. Before this file the 迷走砲 classifier was the only one; a second
 * opener copied from it would be a second implementation of every rule, which is the drift CLAUDE.md
 * names in 「Three backends」. So the rule lives once, here and in the two shared modules, and a
 * profile only says which nodes, which locks and which strings.
 */

/** One bag-1 sampling stage. Stages are tried in order; the first stage whose clean board matches
 *  one of its nodes (by occupancy, as drawn or mirrored, then by colour) decides the round's bag 1. */
export interface Bag1Stage {
  /** tried in this order, as drawn then mirrored; the first colour match wins */
  nodes: string[];
  /** clean-board sampling point: the board after this many locks */
  locks: number;
  /** The hold rule. A match at this stage asserts a hold ONLY when the piece placed at `atLock`
   *  (1-based) is not the mirror-aware `piece` (`mirrorPiece` in a mirrored round): then the round is
   *  `holdNode`; when it IS that piece, it was placed somewhere off the page and the round is the
   *  outcome `elsewhereNode`, whose opportunities are `holdNode`'s. */
  holdSplit?: { piece: string; mirrorPiece: string; atLock: number; holdNode: string; elsewhereNode: string };
}

/** The BAG-1 SPIN STEP (stick spin): the bag-1 stage board is the bag less its T, and the bag's
 *  last lock is that T, into a T-spin the page draws as `U` cells on a child board of the stage node
 *  (`spin_of`). The step is a descent, not a sampling point of its own: after a stage match, the
 *  lock at `atLock` (1-based) must be a T whose spin and line count are `spin` / `lines` and whose
 *  cells are EXACTLY one child's U cells, in the stage match's handedness; then the round's bag-1
 *  node is that child. Any other lock 7 leaves the round at the stage node. The line it clears is
 *  the route's own, so it does not stop the bag-2 sample's no-clear rule. */
export interface Bag1Spin {
  /** the child boards, each with `spin_of` naming a stage node; tried in order */
  nodes: string[];
  atLock: number;
  spin: string;
  lines: number;
}

/** The classifier's artefact strings. Every one ships inside the artefact, so they are byte contract. */
export interface ArtefactText {
  schema: string;
  means: string;
  notEligible: string;
  caveat: string;
}

export interface RouteProfile {
  /** `--opener` key */
  key: string;
  /** error-message prefix ('stray-cannon') — message only, never in an artefact */
  tag: string;
  routesPath: string;
  artefactPath: string;
  demosPath: string;
  /** md5 inputs, each concatenated in order into ONE string field (`emitter_md5`, `planner_md5`) */
  hashFiles: { classifier: string[]; planner: string[] };

  bag1: {
    stages: Bag1Stage[];
    /** a FLAG, never a node: did `stage`'s board match its nodes by OCCUPANCY (colour never decides
     *  it — it is compared with `opener-facts.json`'s `exact`, which is occupancy). Absent: the
     *  opener has no harddrop column to compare with (stick spin), and no flag is recorded. */
    flag?: { field: string; stage: number };
    /** the case key that records the piece placed at the hold stage's `atLock`; absent with no hold
     *  stage (nothing to record) */
    lockPieceField?: string;
    /** the bag-1 spin step, if the page's bag 1 ends on a T-spin */
    spin?: Bag1Spin;
  };
  /** bag 2's board is sampled after this 0-based lock index */
  bag2Lock: number;
  /** 'refuse': no garbage may arrive before a sampling point (迷走砲). 'strip': complete garbage
   *  rows are stripped from the bottom of the bag-2 and snapshot boards before matching, and the
   *  count is recorded in the case (`garbage_rows_stripped`). */
  bag2Garbage: 'refuse' | 'strip';
  /** For a round whose bag 2 matched nothing: compare the board just before its `pcAfter` spin with
   *  every bag-2 board by occupancy and record why it missed (MEASURED, never matched: the case stays
   *  bag-1 only). `subset` = the spin fired before the drawn board was complete; `superset` = the
   *  drawn board plus exactly four cells; `moved` = one piece of it placed elsewhere. Absent: no such
   *  record (迷走砲). `{ nearCells: N }` adds a fourth, last kind, `near`: the bag-2 board(s) nearest by
   *  symmetric cell difference, when that difference is at most N cells (stick spin: yachi's board
   *  with the J and L built otherwise); `true` never computes it. */
  bag2Explain?: boolean | { nearCells: number };
  /** clear events (TST, PC) are looked for in the first eventLocks locks */
  eventLocks: number;
  /** snapshot routes are looked for up to this many locks; a round digest keeps this many */
  snapshotLocks: number;
  /** the bag-3 frame is compared over its bottom pcRows rows */
  pcRows: number;
  /** lines cleared by the Perfect Clear the PC lists draw, counted cumulatively from lock 0 */
  pcLines: number;
  /** the clear the bag-3 frame starts after */
  pcAfter: { piece: string; spin: string; lines: number };
  /** The page's Perfect Clear KINDS, when it draws more than the one `pcAfter` / `pcLines` / `pcRows`
   *  describes (山岳積み2号: a bag-2 4-line PC with no spin before it, the 8-line bag-3 PCs, and a
   *  14-line PC in bag 5). Absent: one kind from those three fields over every bag-3 list (迷走砲,
   *  はちみつ砲). A PC is filed under the kind whose `lines` its cumulative count equals. */
  pcKinds?: PcKind[];

  artefact: ArtefactText;
  /** the artefact's `rules` object, key order included */
  rules(): Record<string, unknown>;
  /** the opener's own named lists, FIRST in the artefact's `lists` (the generic five follow) */
  lists(cases: any[], name: (c: any) => string): Record<string, string[]>;

  /** the demo planner's opener-specific half; absent until an opener's demos exist */
  demos?: DemoProfile;
}

/** One kind of Perfect Clear a route page draws: which lists hold its patterns, where its frame
 *  starts, how many lines it clears counted from lock 0, and how many rows its frame compares. */
export interface PcKind {
  /** the routes JSON `list` ids whose patterns are this kind's */
  lists: string[];
  /** The frame starts after a clear of this shape: the FIRST such clear in the event window (it must
   *  come before the PC) or the LAST one before the PC; `name` is what the off-page reason calls it.
   *  Or `{ locks }`: the frame starts after that many locks, with no spin before it. */
  after: { piece: string; spin: string; lines: number; pick: 'first' | 'last'; name: string } | { locks: number };
  lines: number;
  rows: number;
}

/** A colour reading: a cell group drawn in one piece's colour that can only be another piece. */
export interface PieceReading {
  node: string; drawn: string; reads_as: string; cells: [number, number][]; reason: string;
}

export interface DemoProfile {
  schema: string;
  means: string;
  notEligible: string[];
  caveat: Record<string, string>;
  /** drawn nodes with no demo, and why */
  unbuilt: Record<string, string>;
  pieceReadings: PieceReading[];
  /** the bag-1 half of a node's bag spec: queue constraints, the held piece and where it is held */
  bag1Spec(n: any, routes: any): { before: [string, string][]; early: string | null;
                                   holdPiece: string | null; holdBefore: string | null };
  /** a node no demo builds (an illustration of a group's shared state) → the demo node whose end
   *  state it draws, so a child's chain runs through that demo (はちみつ砲: the five 2.ideal forms
   *  share one after-TST board, drawn once) */
  chainVia?: Record<string, string>;
  /** a lower-case letter a node draws in a T-spin slot, and the lines it must clear (はちみつ砲's PC
   *  patterns draw the TSD's T as a plain `t`; 迷走砲 draws it U). `routes` is the opener's routes JSON,
   *  for a profile whose rule reads another node (山岳積み2号: the empty slot of the pattern's base). */
  spinLetter?(n: any, routes: any): { letter: string; lines: number } | null;
}
