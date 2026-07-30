/**
 * VENDORED from github.com/yachi/td-opener-trainer at commit fa596ee — src/core/pieces.ts
 *
 * Not a clean copy. `types.ts` carries a one-line patch that is LOAD-BEARING:
 *   BOARD_VISIBLE_HEIGHT 20 -> 40   (20 visible rows + 20 buffer rows)
 * srs.ts bakes that constant into isValidPosition's floor check, so a fresh clone of the
 * trainer silently locks pieces at row 20 and produces wrong boards without erroring.
 * That patch was uncommitted in the scratchpad clone; vendoring it here is why this
 * directory reproduces and a re-clone would not.
 */
import type { PieceDefinition, PieceType } from './types';

/**
 * SRS piece definitions.
 * Each piece has 4 rotation states (0, R, 2, L) using standard SRS bounding-box coordinates.
 * Coordinates are [col, row] where (0,0) is top-left of the bounding box.
 */
export const PIECE_DEFINITIONS: Record<PieceType, PieceDefinition> = {
  I: {
    type: 'I',
    color: '#00E5FF',
    cells: [
      // State 0
      [[0, 1], [1, 1], [2, 1], [3, 1]],
      // State R
      [[2, 0], [2, 1], [2, 2], [2, 3]],
      // State 2
      [[0, 2], [1, 2], [2, 2], [3, 2]],
      // State L
      [[1, 0], [1, 1], [1, 2], [1, 3]],
    ],
  },
  T: {
    type: 'T',
    color: '#AA00FF',
    cells: [
      // State 0
      [[1, 0], [0, 1], [1, 1], [2, 1]],
      // State R
      [[1, 0], [1, 1], [2, 1], [1, 2]],
      // State 2
      [[0, 1], [1, 1], [2, 1], [1, 2]],
      // State L
      [[1, 0], [0, 1], [1, 1], [1, 2]],
    ],
  },
  O: {
    type: 'O',
    color: '#FFD600',
    cells: [
      // All 4 states identical for O
      [[1, 0], [2, 0], [1, 1], [2, 1]],
      [[1, 0], [2, 0], [1, 1], [2, 1]],
      [[1, 0], [2, 0], [1, 1], [2, 1]],
      [[1, 0], [2, 0], [1, 1], [2, 1]],
    ],
  },
  S: {
    type: 'S',
    color: '#69F0AE',
    cells: [
      // State 0
      [[1, 0], [2, 0], [0, 1], [1, 1]],
      // State R
      [[1, 0], [1, 1], [2, 1], [2, 2]],
      // State 2
      [[1, 1], [2, 1], [0, 2], [1, 2]],
      // State L
      [[0, 0], [0, 1], [1, 1], [1, 2]],
    ],
  },
  Z: {
    type: 'Z',
    color: '#FF1744',
    cells: [
      // State 0
      [[0, 0], [1, 0], [1, 1], [2, 1]],
      // State R
      [[2, 0], [1, 1], [2, 1], [1, 2]],
      // State 2
      [[0, 1], [1, 1], [1, 2], [2, 2]],
      // State L
      [[1, 0], [0, 1], [1, 1], [0, 2]],
    ],
  },
  L: {
    type: 'L',
    color: '#FF9100',
    cells: [
      // State 0
      [[2, 0], [0, 1], [1, 1], [2, 1]],
      // State R
      [[1, 0], [1, 1], [1, 2], [2, 2]],
      // State 2
      [[0, 1], [1, 1], [2, 1], [0, 2]],
      // State L
      [[0, 0], [1, 0], [1, 1], [1, 2]],
    ],
  },
  J: {
    type: 'J',
    color: '#2979FF',
    cells: [
      // State 0
      [[0, 0], [0, 1], [1, 1], [2, 1]],
      // State R
      [[1, 0], [2, 0], [1, 1], [1, 2]],
      // State 2
      [[0, 1], [1, 1], [2, 1], [2, 2]],
      // State L
      [[1, 0], [1, 1], [0, 2], [1, 2]],
    ],
  },
};
