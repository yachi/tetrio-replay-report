/**
 * VENDORED from github.com/yachi/td-opener-trainer at commit fa596ee — src/core/types.ts
 *
 * Not a clean copy. `types.ts` carries a one-line patch that is LOAD-BEARING:
 *   BOARD_VISIBLE_HEIGHT 20 -> 40   (20 visible rows + 20 buffer rows)
 * srs.ts bakes that constant into isValidPosition's floor check, so a fresh clone of the
 * trainer silently locks pieces at row 20 and produces wrong boards without erroring.
 * That patch was uncommitted in the scratchpad clone; vendoring it here is why this
 * directory reproduces and a re-clone would not.
 */
export type PieceType = 'I' | 'T' | 'O' | 'S' | 'Z' | 'L' | 'J';
export type Offset = readonly [col: number, row: number];

export interface PieceDefinition {
  readonly type: PieceType;
  readonly cells: readonly [
    readonly Offset[],
    readonly Offset[],
    readonly Offset[],
    readonly Offset[],
  ];
  readonly color: string;
}

export const BOARD_WIDTH = 10;
export const BOARD_VISIBLE_HEIGHT = 40; // PROBE PATCH: 20 visible + 20 buffer
export const ALL_PIECE_TYPES: readonly PieceType[] = [
  'I',
  'T',
  'O',
  'S',
  'Z',
  'L',
  'J',
];
