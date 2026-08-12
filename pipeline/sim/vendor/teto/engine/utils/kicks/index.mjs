import { kicks } from "./data.mjs";
export { kicks as kickData };
export const legal = (blocks, board)=>{
    if (board.length === 0) return false;
    const boardWidth = board[0].length;
    const boardHeight = board.length;
    for(let i = 0; i < blocks.length; i++){
        const block = blocks[i];
        const x = block[0];
        const y = block[1];
        if (x < 0) return false;
        if (x >= boardWidth) return false;
        if (y < 0) return false;
        if (y >= boardHeight) return false;
        if (board[y][x]) return false;
    }
    return true;
};
export const performKick = (kicktable, piece, pieceLocation, ao, maxMovement, blocks, startRotation, endRotation, board)=>{
    try {
        const floorPieceY = Math.floor(pieceLocation[1]);
        const baseX = pieceLocation[0] - ao[0];
        const baseY = floorPieceY - ao[1];
        const initialBlocks = new Array(blocks.length);
        for(let i = 0; i < blocks.length; i++){
            const block = blocks[i];
            initialBlocks[i] = [
                baseX + block[0],
                baseY - block[1]
            ];
        }
        if (legal(initialBlocks, board)) return true;
        const kickID = `${startRotation}${endRotation}`;
        const table = kicks[kicktable];
        const customKicksetID = `${piece.toLowerCase()}_kicks`;
        const kickset = customKicksetID in table ? table[customKicksetID][kickID] : table.kicks[kickID];
        const testBlocks = new Array(blocks.length);
        for(let i = 0; i < kickset.length; i++){
            const [dx, dy] = kickset[i];
            const newY = maxMovement ? pieceLocation[1] - dy - ao[1] : Math.ceil(pieceLocation[1]) - 0.1 - dy - ao[1];
            const floorNewY = Math.floor(newY);
            const movedBaseX = baseX + dx;
            for(let j = 0; j < blocks.length; j++){
                const block = blocks[j];
                testBlocks[j] = [
                    movedBaseX + block[0],
                    floorNewY - block[1]
                ];
            }
            if (legal(testBlocks, board)) {
                return {
                    newLocation: [
                        pieceLocation[0] + dx - ao[0],
                        newY
                    ],
                    kick: [
                        dx,
                        -dy
                    ],
                    id: kickID,
                    index: i
                };
            }
        }
        return false;
    } catch  {
        return false;
    }
};

//# sourceMappingURL=index.js.map