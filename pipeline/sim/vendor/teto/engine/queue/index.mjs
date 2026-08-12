import { rngMap } from "./rng/index.mjs";
export class Queue extends Array {
    seed;
    type;
    bag;
    #minLength;
    repopulateListener = null;
    static get [Symbol.species]() {
        return Array;
    }
    constructor(options){
        super();
        this.seed = options.seed;
        this.type = options.type;
        this.reset();
        this.minLength = options.minLength;
    }
    reset() {
        this.bag = new rngMap[this.type](this.seed);
        this.#repopulate();
    }
    /** @internal */ clear() {
        this.length = 0;
    }
    onRepopulate(listener) {
        this.repopulateListener = listener;
    }
    get minLength() {
        return this.#minLength;
    }
    set minLength(val) {
        this.#minLength = val;
        this.#repopulate();
    }
    get next() {
        return this[0];
    }
    shift() {
        this.#repopulate();
        const val = super.shift();
        return val;
    }
    /** @internal */ repopulateOnce() {
        const newValues = this.bag.next();
        this.push(...newValues);
        return [
            ...newValues
        ];
    }
    #repopulate() {
        const added = [];
        while(this.length < this.minLength){
            added.push(...this.repopulateOnce());
        }
        if (this.repopulateListener && added.length) {
            this.repopulateListener(added);
        }
    }
    snapshot() {
        return {
            value: Array.from(this),
            bag: this.bag.snapshot()
        };
    }
    fromSnapshot(snapshot) {
        this.bag.fromSnapshot(snapshot.bag);
        this.splice(0, this.length, ...snapshot.value);
    }
    raw() {
        return Array.from(this);
    }
}
export * from "./rng/index.mjs";
export * from "./types.mjs";

//# sourceMappingURL=index.js.map