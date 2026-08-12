import { deepCopy } from "../index.mjs";
import { legal, performKick } from "../kicks/index.mjs";
import { tetrominoes } from "./data.mjs";
export class Tetromino {
    #rotation;
    symbol;
    states;
    location;
    locking;
    lockResets;
    rotResets;
    safeLock;
    highestY;
    fallingRotations;
    totalRotations;
    irs;
    ihs;
    aox;
    aoy;
    keys;
    #legalAt(board, x, y) {
        const blocks = this.blocks;
        const abs = new Array(blocks.length);
        for(let i = 0; i < blocks.length; i++){
            const block = blocks[i];
            abs[i] = [
                block[0] + x,
                -block[1] + y
            ];
        }
        return legal(abs, board);
    }
    constructor(options){
        this.rotation = options.initialRotation;
        this.symbol = options.symbol;
        const tetromino = tetrominoes[this.symbol.toLowerCase()];
        this.states = tetromino.matrix.data;
        this.location = [
            Math.floor(options.boardWidth / 2 - tetromino.matrix.w / 2),
            options.boardHeight + 2.04
        ];
        // other stuff
        this.locking = 0;
        this.lockResets = 0;
        this.rotResets = 0;
        this.safeLock = options.from?.safeLock ?? 0;
        this.highestY = options.boardHeight + 2;
        this.fallingRotations = 0;
        this.totalRotations = 0;
        this.irs = options.from?.irs ?? 0;
        this.ihs = options.from?.ihs ?? false;
        this.aox = 0;
        this.aoy = 0;
        this.keys = 0;
    }
    get blocks() {
        return this.states[Math.min(this.rotation, this.states.length)];
    }
    get absoluteBlocks() {
        const blocks = this.blocks;
        const abs = new Array(blocks.length);
        const x = this.location[0];
        const y = this.y;
        for(let i = 0; i < blocks.length; i++){
            const block = blocks[i];
            abs[i] = [
                block[0] + x,
                -block[1] + y
            ];
        }
        return abs;
    }
    absoluteAt({ x = this.location[0], y = this.location[1], rotation = this.rotation }) {
        const normalizedRotation = (rotation % 4 + 4) % 4;
        const state = this.states[normalizedRotation];
        const abs = new Array(state.length);
        const yFloor = Math.floor(y);
        for(let i = 0; i < state.length; i++){
            const block = state[i];
            abs[i] = [
                block[0] + x,
                -block[1] + yFloor
            ];
        }
        return abs;
    }
    get rotation() {
        return this.#rotation % 4;
    }
    set rotation(value) {
        this.#rotation = value % 4;
    }
    get x() {
        return this.location[0];
    }
    set x(value) {
        this.location[0] = value;
    }
    get y() {
        return Math.floor(this.location[1]);
    }
    set y(value) {
        this.location[1] = value;
    }
    isStupidSpinPosition(board) {
        return !this.#legalAt(board, this.location[0], this.y - 1);
    }
    isAllSpinPosition(board) {
        return !this.#legalAt(board, this.location[0] - 1, this.y) && !this.#legalAt(board, this.location[0] + 1, this.y) && !this.#legalAt(board, this.location[0], this.y + 1) && !this.#legalAt(board, this.location[0], this.y - 1);
    }
    rotate(board, kickTable, amt, maxMovement) {
        const rotatedBlocks = this.states[(this.rotation + amt) % 4];
        const kickRes = performKick(kickTable, this.symbol, this.location, [
            this.aox,
            this.aoy
        ], maxMovement, rotatedBlocks, this.rotation, (this.rotation + amt) % 4, board);
        if (typeof kickRes === "object") {
            this.location = [
                ...kickRes.newLocation
            ];
        }
        if (kickRes) {
            this.rotation = this.rotation + amt;
            return kickRes;
        }
        return false;
    }
    moveRight(board) {
        if (this.#legalAt(board, this.location[0] + 1, this.y)) {
            this.location[0]++;
            return true;
        }
        return false;
    }
    moveLeft(board) {
        if (this.#legalAt(board, this.location[0] - 1, this.y)) {
            this.location[0]--;
            return true;
        }
        return false;
    }
    dasRight(board) {
        if (this.moveRight(board)) {
            while(this.moveRight(board)){
            /* empty */ }
            return true;
        }
        return false;
    }
    dasLeft(board) {
        if (this.moveLeft(board)) {
            while(this.moveLeft(board)){
            /* empty */ }
            return true;
        }
        return false;
    }
    softDrop(board) {
        const start = this.location[1];
        while(this.#legalAt(board, this.location[0], this.y - 1)){
            this.location[1]--;
        }
        return start !== this.location[1];
    }
    snapshot() {
        return {
            aox: this.aox,
            aoy: this.aoy,
            fallingRotations: this.fallingRotations,
            highestY: this.highestY,
            ihs: this.ihs,
            irs: this.irs,
            keys: this.keys,
            rotation: this.rotation,
            location: deepCopy(this.location),
            locking: this.locking,
            lockResets: this.lockResets,
            rotResets: this.rotResets,
            safeLock: this.safeLock,
            symbol: this.symbol,
            totalRotations: this.totalRotations
        };
    }
}
export * from "./data.mjs";
export * from "./types.mjs";

//# sourceMappingURL=index.js.map