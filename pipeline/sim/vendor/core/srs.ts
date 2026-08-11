/**
 * VENDORED from github.com/yachi/td-opener-trainer at commit fa596ee — src/core/srs.ts
 *
 * Not a clean copy. `types.ts` carries a one-line patch that is LOAD-BEARING:
 *   BOARD_VISIBLE_HEIGHT 20 -> 40   (20 visible rows + 20 buffer rows)
 * srs.ts bakes that constant into isValidPosition's floor check, so a fresh clone of the
 * trainer silently locks pieces at row 20 and produces wrong boards without erroring.
 * That patch was uncommitted in the scratchpad clone; vendoring it here is why this
 * directory reproduces and a re-clone would not.
 */
import type { PieceType } from './types';
import { BOARD_WIDTH, BOARD_VISIBLE_HEIGHT } from './types';
import { PIECE_DEFINITIONS } from './pieces';

// ── Types ──

export type Board = ReadonlyArray<ReadonlyArray<PieceType | null>>;

type MutableBoard = (PieceType | null)[][];

export interface ActivePiece {
  type: PieceType;
  rotation: 0 | 1 | 2 | 3;
  col: number;
  row: number;
}

// ── SRS Kick Tables ──
// Convention: [dx, dy] where +dx = right, +dy = DOWN (row 0 = top)

type KickKey =
  | '0->1' | '1->0'
  | '1->2' | '2->1'
  | '2->3' | '3->2'
  | '3->0' | '0->3';
type KickTable = Record<KickKey, readonly [number, number][]>;

export const JLSZT_KICKS: KickTable = {
  '0->1': [[0, 0], [-1, 0], [-1, -1], [0, +2], [-1, +2]],
  '1->0': [[0, 0], [+1, 0], [+1, +1], [0, -2], [+1, -2]],
  '1->2': [[0, 0], [+1, 0], [+1, +1], [0, -2], [+1, -2]],
  '2->1': [[0, 0], [-1, 0], [-1, -1], [0, +2], [-1, +2]],
  '2->3': [[0, 0], [+1, 0], [+1, -1], [0, +2], [+1, +2]],
  '3->2': [[0, 0], [-1, 0], [-1, +1], [0, -2], [-1, -2]],
  '3->0': [[0, 0], [-1, 0], [-1, +1], [0, -2], [-1, -2]],
  '0->3': [[0, 0], [+1, 0], [+1, -1], [0, +2], [+1, +2]],
};

export const I_KICKS: KickTable = {
  '0->1': [[0, 0], [-2, 0], [+1, 0], [-2, +1], [+1, -2]],
  '1->0': [[0, 0], [+2, 0], [-1, 0], [+2, -1], [-1, +2]],
  '1->2': [[0, 0], [-1, 0], [+2, 0], [-1, -2], [+2, +1]],
  '2->1': [[0, 0], [+1, 0], [-2, 0], [+1, +2], [-2, -1]],
  '2->3': [[0, 0], [+2, 0], [-1, 0], [+2, -1], [-1, +2]],
  '3->2': [[0, 0], [-2, 0], [+1, 0], [-2, +1], [+1, -2]],
  '3->0': [[0, 0], [+1, 0], [-2, 0], [+1, +2], [-2, -1]],
  '0->3': [[0, 0], [-1, 0], [+2, 0], [-1, -2], [+2, +1]],
};

/**
 * LOCAL ADDITION (not from td-opener-trainer): TETR.IO ships "SRS+", which differs from
 * vanilla SRS ONLY for the I piece and ONLY in the ORDER of the kick candidates. Order is
 * load-bearing — the first legal candidate wins, so a reordering lands the piece somewhere
 * else whenever more than one candidate is legal. Transcribed from halp1/triangle
 * src/engine/utils/kicks/data.ts ("SRS+".i_kicks); same [dx, dy] row-down convention.
 * 1->2, 2->3 and 3->0 are identical in both tables and are repeated here verbatim.
 */
export const I_KICKS_PLUS: KickTable = {
  '0->1': [[0, 0], [+1, 0], [-2, 0], [-2, +1], [+1, -2]],
  '1->0': [[0, 0], [-1, 0], [+2, 0], [-1, +2], [+2, -1]],
  '1->2': [[0, 0], [-1, 0], [+2, 0], [-1, -2], [+2, +1]],
  '2->1': [[0, 0], [-2, 0], [+1, 0], [-2, -1], [+1, +2]],
  '2->3': [[0, 0], [+2, 0], [-1, 0], [+2, -1], [-1, +2]],
  '3->2': [[0, 0], [+1, 0], [-2, 0], [+1, -2], [-2, +1]],
  '3->0': [[0, 0], [+1, 0], [-2, 0], [+1, +2], [-2, -1]],
  '0->3': [[0, 0], [-1, 0], [+2, 0], [+2, +1], [-1, -2]],
};

let kicksetName: 'SRS' | 'SRS+' = 'SRS';
export function setKickset(k: 'SRS' | 'SRS+') { kicksetName = k; }

export const O_KICKS: KickTable = {
  '0->1': [[0, 0]],
  '1->0': [[0, 0]],
  '1->2': [[0, 0]],
  '2->1': [[0, 0]],
  '2->3': [[0, 0]],
  '3->2': [[0, 0]],
  '3->0': [[0, 0]],
  '0->3': [[0, 0]],
};

function getKickTable(type: PieceType): KickTable {
  if (type === 'I') return kicksetName === 'SRS+' ? I_KICKS_PLUS : I_KICKS;
  if (type === 'O') return O_KICKS;
  return JLSZT_KICKS;
}

// ── Board ──

export function createBoard(): Board {
  const board: MutableBoard = Array.from({ length: BOARD_VISIBLE_HEIGHT }, () =>
    Array.from({ length: BOARD_WIDTH }, () => null)
  );
  return board;
}

// ── Piece Cells ──

export function getPieceCells(piece: ActivePiece): { col: number; row: number }[] {
  const def = PIECE_DEFINITIONS[piece.type];
  const offsets = def.cells[piece.rotation];
  return offsets.map(([dc, dr]) => ({
    col: piece.col + dc,
    row: piece.row + dr,
  }));
}

// ── Collision Detection ──

export function isValidPosition(board: Board, piece: ActivePiece): boolean {
  const cells = getPieceCells(piece);
  for (const { col, row } of cells) {
    // Out of bounds horizontally
    if (col < 0 || col >= BOARD_WIDTH) return false;
    // Below bottom
    if (row >= BOARD_VISIBLE_HEIGHT) return false;
    // Above top is OK (buffer zone), skip board check
    if (row < 0) continue;
    // Overlapping locked cell
    if (board[row]![col] !== null) return false;
  }
  return true;
}

// ── Movement ──

export function tryMove(board: Board, piece: ActivePiece, dx: number, dy: number): ActivePiece | null {
  const moved: ActivePiece = {
    ...piece,
    col: piece.col + dx,
    row: piece.row + dy,
  };
  return isValidPosition(board, moved) ? moved : null;
}

// ── Rotation with SRS Kicks ──

export function tryRotate(board: Board, piece: ActivePiece, direction: 1 | -1): ActivePiece | null {
  const newRotation = ((piece.rotation + direction + 4) % 4) as 0 | 1 | 2 | 3;
  const kickKey = `${piece.rotation}->${newRotation}` as KickKey;
  const kicks = getKickTable(piece.type)[kickKey];

  for (const [dx, dy] of kicks) {
    const candidate: ActivePiece = {
      ...piece,
      rotation: newRotation,
      col: piece.col + dx,
      row: piece.row + dy,
    };
    if (isValidPosition(board, candidate)) {
      return candidate;
    }
  }
  return null;
}

// ── Hard Drop ──

export function hardDrop(board: Board, piece: ActivePiece): ActivePiece {
  let current = piece;
  while (true) {
    const next = tryMove(board, current, 0, 1);
    if (!next) return current;
    current = next;
  }
}

// ── Lock Piece ──

export function lockPiece(board: Board, piece: ActivePiece): Board {
  const newBoard: MutableBoard = board.map(row => [...row]);
  const cells = getPieceCells(piece);
  for (const { col, row } of cells) {
    if (row >= 0 && row < BOARD_VISIBLE_HEIGHT && col >= 0 && col < BOARD_WIDTH) {
      newBoard[row]![col] = piece.type;
    }
  }
  return newBoard;
}

// ── Spawn ──

export function spawnPiece(type: PieceType): ActivePiece {
  return {
    type,
    rotation: 0,
    col: 3,
    row: 0,
  };
}

// ── Ghost Piece ──

export function getGhostPosition(board: Board, piece: ActivePiece): ActivePiece {
  return hardDrop(board, piece);
}
