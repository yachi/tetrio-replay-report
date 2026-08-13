/**
 * Emit the opener metrics as DATA, one artifact per session — C-Spin and DT Cannon by the order
 * of their two T-spins, and six NAMED openers by the shape of the opening board.
 *
 *   REPLAY_DIR=sessions/2026-08-09 bun pipeline/sim/emit-opener-facts.ts \
 *     --out sessions/2026-08-09/sim/opener-facts.json
 *
 * QUARANTINED, exactly like sim/forecast-facts.json and for the same reason: every number here
 * comes from ONE replay simulator, and this repo's trust argument is two independently written
 * extractors agreeing byte-for-byte. There is no second simulator, so that argument does not reach
 * these numbers. The file therefore carries `report_eligible: false`, the section it feeds mints no
 * claim ids and no ✓ badges, and none of it may be merged into report/facts.json.
 *
 * EIGHT METRICS, each paired with the control that says what it is NOT.
 *
 * 1. FIRST BAG vs the community catalogue. After seven locks with no clear and no garbage a board
 *    holds exactly 28 cells; `openers/match.ts` compares it with every catalogue page at that cell
 *    count, as drawn and mirrored. Reported as a Hamming-distance histogram per named set.
 *
 *    The control is SET CHOICE. A distance reported over one name set cannot be told apart from an
 *    artefact of picking that set — and the C-Spin set is genuinely doubtful (see `isCSpin`: its
 *    three members are `Fake C-Spin`, `Secspin` and an `SDPC-Spin` compound). So every set is
 *    reported, narrow and widest, with its member names, and the finding is whether the answer
 *    MOVES between them. Measured over all five sessions it does not: the nearest C-Spin page and
 *    the nearest DT page both sit at 6 cells whichever reading is taken.
 *
 * 2. ORDERING — which of the two T-spins comes first. This is the one metric that separates the two
 *    openers by DEFINITION rather than by geometry, and it is the reason this artifact exists:
 *
 *      DT Cannon  is a Double THEN a Triple  (開幕DT砲 — "Double Triple Cannon").
 *      C-Spin     is a Triple THEN a Double  (the wiki's follow-up, within about three bags).
 *
 *    So the same pair of events, in the two orders, names the two openers. No board comparison is
 *    involved and no catalogue coverage bounds it.
 *
 *    The control is EXPOSURE: a round is only counted once it holds both a T-spin Double and a
 *    T-spin Triple IN THE OPENER, so "0 in DT order" is over rounds that demonstrably had the material
 *    for either order. The order is scored over the opener window (a spin's lock index <= WINDOW_PIECES
 *    = 21 = 3 bags): the C-Spin/DT distinction is an OPENING technique, and over a whole round these
 *    players throw ordinary T-spin doubles by the dozen, so "did any triple precede any double" becomes
 *    a statement about playstyle, not the opener. The hand-sim's short verified prefix hid this by
 *    truncating to the opening; the oracle board source reaches the whole round, so the window is now
 *    explicit. `ordering_full_round` applies the same opener window over the whole simulated round;
 *    both agree (cspin_order === rounds_with_both, dt_order == 0, five sessions).
 *
 * 3. SLOT GEOMETRY vs harddrop.com/wiki/C-Spin's own 38 drawn placements. For each verified T-spin
 *    the local shape the T tucked into is extracted and compared with the article's.
 *
 *    The control is the CROSS-TAB BY LINES, and it is why this metric must never be published as a
 *    C-Spin count. Roughly nine in ten Triples match the window and roughly one in ten Doubles do —
 *    which is what "this is a T-spin Triple slot" looks like, not what "this is the C-Spin opener"
 *    looks like. The number is emitted so the section can SHOW that, not so it can claim the spins.
 *
 * 4. NAMED OPENERS — Honey Cup, Stray Cannon, Mountainous Stacking 1/2/3, TKI-3 and the Perfect
 *    Clear Opener, each against its own drawings (`openers/wiki-openers.json` plus every clean
 *    catalogue page of the same opener). This is the metric that answers "which opener", where
 *    (2) can only answer "which class".
 *
 *    Two controls, because this metric has two ways of lying.
 *
 *    The BASELINE says which column may be read. Scored against the openers a player is NOT
 *    playing, the `<= NEAR_CELLS` band is reached about as often as against the opener in
 *    question — these boards sit 3-4 cells from almost any opener page — so that column
 *    discriminates nothing and only an EXACT match separates. Both are emitted side by side so
 *    the section can show it rather than assert it.
 *
 *    The OPPORTUNITY COUNT is the denominator. An opener is only scored on boards sampled at the
 *    lock count it is DRAWN at, and `occupancy_aliases` / `round_overlap` name the openers whose
 *    columns are the same rounds twice (Mountainous Stacking 1 and 2 are one shape built from
 *    different pieces, which a filled/empty grid cannot tell apart).
 *
 * 5. ORDERING CLASS — the control on (2), transcribed from harddrop's own category listing.
 *    "A Triple before a Double" is the signature of 38 catalogued openers, C-Spin and Honey Cup
 *    among them, so (2) names a CLASS and never a member. This was found by measuring (4): a
 *    session running Honey Cup every round produces exactly the 221-of-221 that had been read as
 *    a C-Spin result.
 *
 * 6. PERFECT CLEAR TIMING — where in the round each perfect clear landed. The control is the count
 *    itself, checked per round against the replay's own `clears.allclear` (`perfectClearTiming`).
 *
 * 7-8. DONATION and STMB CAVE — two per-T-spin BOARD-STATE techniques, neither of them an opener.
 *    Both are scored over the verified prefix and both are licensed by the same reconstruction
 *    check (`reconstructionCheck`): the per-lock board snapshot plus the lock's cells must make
 *    exactly the rows full that the engine independently recorded clearing. Their controls are on
 *    `donationMetric` (the b2b split and the well provenance) and `stmbCaveMetric` (the depth
 *    histogram and the same shape under a Triple).
 *
 * Rates are integers scaled x1000, matching report/facts.json and forecast-facts.json.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex, replayDir } from './verified-prefix.ts';
import { H } from './sim.ts';
import { BOARD_WIDTH } from './vendor/core/types.ts';
import { loadCatalogue, prepare, occGrid, rowsFromBoard, exactMatches, nearest, NAME_SETS,
         loadWikiOpeners, openerPages, hasFullRow } from '../openers/match.ts';

/** Three bags. The wiki's C-Spin follow-up is "a Double within about three bags of the Triple", and
 *  a window has to be a number: 21 pieces is that phrase read literally. It is emitted rather than
 *  buried so the section prints the window it actually used, and so widening it is a data change. */
const WINDOW_PIECES = 21;

/** Distance at which two 28-cell boards stop being "the same opener, played slightly differently".
 *  Inherited from `openers/README.md`, where it is what separates the exact/variant bands from the
 *  5-8 band that every real board in this corpus lands in. */
const NEAR_CELLS = 4;

/** Lock counts at which the opening board is sampled and offered to the matcher.
 *
 *  This used to be 7 alone, and 7 alone was a COVERAGE BUG rather than a choice. A player who keeps
 *  a piece in hold through bag 1 has locked SIX pieces when the bag is done, and that is how
 *  harddrop draws four of the six openers named here — Stray Cannon ("keep either S or Z in hold"),
 *  Mountainous Stacking 1/2/3, TKI-3. A 24-cell field can never equal a 28-cell board, so those
 *  openers were not scoring zero: they were never being compared. The same blind spot hid 75 of the
 *  catalogue's 299 clean pages, including the PCO setup that keeps the I piece on hold.
 *
 *  6 and 7 are the two lock counts a first bag can end on (hold used, or not). */
const OPENER_LOCKS = [6, 7] as const;

const cat = loadCatalogue();
const prepared = prepare(cat.pages);
const catNames: string[] = [...new Set(cat.pages.map(p => p.name))];

/** harddrop's own drawings and its own category listing (pipeline/openers/wiki-openers.json). */
const wiki = loadWikiOpeners();
const tdc = wiki.triple_double_category;
/** How many catalogue pages could never match a real opening board because a full row would have
 *  cleared. Emitted, not just asserted, because it is the size of the metric's blind spot. */
const catClean = prepared.filter(p => !hasFullRow(p.page.rows)).length;

const WIKI_CSPIN = JSON.parse(readFileSync(`${import.meta.dir}/wiki-cspin-boards.json`, 'utf8')) as
  { rows: string[]; piece: { row: number; col: number }[]; lines: number }[];

/** filled/empty mask of the window around `cells`, with those cells forced empty — i.e. what the
 *  board looked like just before the piece went in. Same frame as `cspin-match.ts` so the two
 *  agree: rows [minRow-2 .. maxRow+1] x cols [minCol-1 .. maxCol+1]. */
function mask(filled: (r: number, c: number) => boolean, cells: { row: number; col: number }[]) {
  const rs = cells.map(c => c.row), cs = cells.map(c => c.col);
  const own = new Set(cells.map(c => `${c.row}:${c.col}`));
  const out: string[] = [];
  for (let r = Math.min(...rs) - 2; r <= Math.max(...rs) + 1; r++) {
    let line = '';
    for (let c = Math.min(...cs) - 1; c <= Math.max(...cs) + 1; c++)
      line += own.has(`${r}:${c}`) ? '.' : filled(r, c) ? '#' : '.';
    out.push(line);
  }
  return out;
}

const wikiMasks = WIKI_CSPIN.map(o => {
  const m = mask((r, c) => {
    if (c < 0 || c >= BOARD_WIDTH) return true;          // walls read as filled, same as a real field
    const row = o.rows[r];
    if (row === undefined) return r >= o.rows.length;    // below the drawing = floor
    return row[c] !== '.' && row[c] !== 'P';
  }, o.piece);
  return { mask: m, mirror: m.map(l => [...l].reverse().join('')) };
});

/** Cells of empty column beneath the plug for the shape to be a DONATION rather than a bump.
 *  4 exactly, and it is harddrop's number rather than a threshold chosen here: of the 20 named
 *  setups the article draws, 17 leave a four-cell well under the plug and 3 leave five — never
 *  three, never six or more. Four is therefore the floor the drawings support. */
export const DONATION_CAVITY = 4;
/** How many of the well's cavity rows must be walled on both sides. The DEEPEST 4, not all of
 *  them: the article's TSS L Donation leaves its topmost cavity row open on one side, so requiring
 *  every cavity row to be walled drops a setup harddrop itself draws as a donation. */
export const DONATION_WALLED_ROWS = 4;
/** Narrowest gap harddrop calls a CAVE. Its Basic Structures are drawn three columns wide; two is
 *  an ordinary overhang, which every board in this corpus produces constantly. */
export const CAVE_MIN_WIDTH = 3;

/** filled/empty view of a simulated board — the frame both board-state metrics work in. An absent
 *  board (lock 0 has none before it) reads as an empty field rather than throwing. */
const occupancyOf = (b: (string | null)[][] | undefined): boolean[][] =>
  Array.from({ length: H }, (_, r) =>
    Array.from({ length: BOARD_WIDTH }, (_, c) => (b ? b[r]?.[c] != null : false)));

/** A column's CAVITY: the empty cells strictly below its lowest filled cell, down to the floor.
 *  `lowest` is -1 for a wholly empty column, in which case the cavity is reported as 0 — an empty
 *  column has no plug above it and so is not a well anybody donated into. */
export function cavity(g: boolean[][], col: number, h: number) {
  let lowest = -1;
  for (let r = 0; r < h; r++) if (g[r]![col]) lowest = r;
  if (lowest < 0) return { cavity: 0, lowest };
  let n = 0;
  for (let r = lowest + 1; r < h; r++) if (!g[r]![col]) n++;
  return { cavity: n, lowest };
}

/**
 * DONATION (harddrop.com/wiki/Donation) — the well columns this T-spin clear donated into.
 *
 * THE NAIVE FORM DISCRIMINATES NOTHING, and that is the trap this predicate is written around.
 * "The well column is filled through the rows the spin cleared" is FORCED BY ARITHMETIC: a full
 * row requires every column filled, so the naive test fires on 70-89% of all T-spin clears and
 * says only that a line was cleared. All of the power is in the RE-OPENING clause — EVERY filled
 * cell of the column must lie in a cleared row, so once the clear resolves the column is open from
 * the surface to the floor again, which is what makes the plug a loan rather than a wall.
 *
 * The T's own slot is excluded, but only when the T occupies the column in EVERY cleared row: a
 * column the T touches in just one of them can still be the well, and is in 3 of the article's 20
 * named setups.
 */
export function donationCols(withT: boolean[][], cleared: number[], t: { row: number; col: number }[], h: number) {
  const inCleared = new Set(cleared);
  const tByCol = new Map<number, Set<number>>();
  for (const q of t) {
    if (!tByCol.has(q.col)) tByCol.set(q.col, new Set());
    tByCol.get(q.col)!.add(q.row);
  }
  const out: { col: number; cavity: number }[] = [];
  for (let c = 0; c < BOARD_WIDTH; c++) {
    const tRows = tByCol.get(c);
    if (tRows && cleared.every(r => tRows.has(r))) continue;   // the T's own slot, not a plug
    let inR = 0, outR = 0;
    for (let r = 0; r < h; r++) {
      if (!withT[r]![c]) continue;
      inCleared.has(r) ? inR++ : outR++;
    }
    if (inR === 0 || outR > 0) continue;                       // the re-opening clause
    const { cavity: cav, lowest } = cavity(withT, c, h);
    if (cav < DONATION_CAVITY) continue;
    const deep: number[] = [];
    for (let r = h - 1; r > lowest && deep.length < DONATION_WALLED_ROWS; r--) if (!withT[r]![c]) deep.push(r);
    const walled = deep.every(r =>
      (c === 0 || withT[r]![c - 1]) && (c === BOARD_WIDTH - 1 || withT[r]![c + 1]));
    if (!walled) continue;
    out.push({ col: c, cavity: cav });
  }
  return out;
}

/**
 * STMB CAVE (harddrop.com/wiki/STMB_Cave) — the widest >= 3-wide empty run under a T-spin Double.
 *
 * TWO THINGS THE DRAWINGS CORRECT, and both were got wrong before them:
 *
 *   - The cave is OFFSET from the T, sharing only two of its three columns, so the test is OVERLAP
 *     with the T's column span and never CONTAINMENT. Containment misses all six of the article's
 *     drawn Basic Structures.
 *   - The cave is NOT tested for being roofed, because that test is vacuous: the cave's roof is the
 *     nub row, which the Double has just completed. A full row roofs everything beneath it by
 *     definition — measured, 0 of 2378 real T-spin Doubles in this corpus have an unroofed one.
 *
 * `minDepth` is the shallowest column of the run, and it is the thing to read: a 3-wide run one row
 * deep is a dimple, not a cave.
 */
export function caveAt(withT: boolean[][], cleared: number[], t: { col: number }[], h: number) {
  if (cleared.length !== 2) return null;                        // a Double, by definition
  const under = Math.max(...cleared) + 1;                       // the row beneath the lower cleared row
  if (under >= h) return null;
  const tc = new Set(t.map(q => q.col));
  let best: { width: number; minDepth: number } | null = null;
  let c = 0;
  while (c < BOARD_WIDTH) {
    if (withT[under]![c]) { c++; continue; }
    let e = c;
    while (e < BOARD_WIDTH && !withT[under]![e]) e++;
    const width = e - c;
    let overlaps = false;
    for (let k = c; k < e; k++) if (tc.has(k)) overlaps = true;
    if (overlaps && width >= CAVE_MIN_WIDTH) {
      let minDepth = Infinity;
      for (let k = c; k < e; k++) {
        let d = 0;
        for (let r = under; r < h && !withT[r]![k]; r++) d++;
        minDepth = Math.min(minDepth, d);
      }
      if (!best || width > best.width) best = { width, minDepth };
    }
    c = e;
  }
  return best;
}

/** The cave metric's own control: the same >= 3-wide gap under the cleared rows, with the T's span
 *  ignored. Run under a TRIPLE, where such a gap is ordinary TST residue and nobody calls it a cave. */
function wideGapUnder(withT: boolean[][], cleared: number[], h: number) {
  const under = Math.max(...cleared) + 1;
  if (under >= h) return false;
  let c = 0;
  while (c < BOARD_WIDTH) {
    if (withT[under]![c]) { c++; continue; }
    let e = c;
    while (e < BOARD_WIDTH && !withT[under]![e]) e++;
    if (e - c >= CAVE_MIN_WIDTH) return true;
    c = e;
  }
  return false;
}

const BANDS = ['0', '1-2', '3-4', '5-8', '9-14', '15+'] as const;
const band = (d: number) => (d === 0 ? '0' : d <= 2 ? '1-2' : d <= 4 ? '3-4' : d <= 8 ? '5-8' : d <= 14 ? '9-14' : '15+');
const emptyBands = () => Object.fromEntries(BANDS.map(b => [b, 0])) as Record<string, number>;

const median = (xs: number[]) => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)]!;
};
/** x/n as an integer per mille, or null when n is 0. Never 0 — a rate with no denominator is an
 *  ABSENCE, and printing 0 for it would publish "measured, and it is exactly nothing". */
const rate = (x: number, n: number) => (n ? Math.floor((x / n) * 1000) : null);

// ── the sets, with their members, so a reader can audit what every number ranges over ──────────
const sets = NAME_SETS.map(s => {
  const names = catNames.filter(s.test);
  return { ...s, names, pages: prepared.filter(p => s.test(p.name)) };
});

// ── walk the session ───────────────────────────────────────────────────────────────────────────
interface Bag { user: string; grid: string[] }
/** an opening board sampled after `locks` locks, with no clear and no garbage before it.
 *  `round` indexes `rounds`, so a shape match can be cross-tabbed against what that round did. */
interface CleanBoard { user: string; round: number; locks: number; grid: string[] }
interface Round { user: string; verified: number; spinsVerified: { i: number; cleared: number }[];
                  spinsAll: { i: number; cleared: number }[];
                  /** 0-based lock indices at which the simulated board came out empty. */
                  pcLocks: number[];
                  /** the same round's Perfect Clear count from `results.stats.clears`, i.e. the
                   *  replay's own tally. null when the replay did not carry the counter, which is
                   *  an UNKNOWN and must not be compared against the simulator as if it were 0. */
                  pcReal: number | null }
/** One verified T-spin CLEAR, with everything the two board-state metrics read off it. Collected
 *  once in the session walk because both metrics need the same three sources to line up: the
 *  pre-lock board, the lock's own cells, and the engine's own record of which rows went. */
interface TSpinClear {
  user: string; lines: number;
  /** the lock index this clear happened at, so both techniques can be split by the opener window.
   *  Carried because "is this an opening technique or a mid-game one" was a question the artifact
   *  ASSERTED rather than answered: harddrop files both pages under `Mid-game T-Spin setups`, and
   *  a citation is not a measurement. */
  lock: number;
  /** the donation well this clear opened, if any — the first one, on the corpus's every event the
   *  only one. `garbageWell` is the well's PROVENANCE and `plug` splits harddrop's own Natural
   *  from its Other Examples: null when the plugging lock cannot be identified. */
  donation: { cavity: number; garbageWell: boolean; plug: 'natural' | 'b2b_breaking' | null } | null;
  /** the widest >= 3-wide gap under a Double that overlaps the T's columns (metric 8) */
  cave: { width: number; minDepth: number } | null;
  /** the control: the same gap width under a Triple, where it is TST residue rather than a cave */
  wideGapUnderTriple: boolean;
}

/**
 * The whole artifact for one session directory, as a value.
 *
 * Exported rather than run at module scope so `openers.test.ts` can assert that rebuilding a
 * session reproduces its COMMITTED opener-facts.json byte for byte. That is the same discipline
 * every other artifact in this repo is held to — the extractor must reproduce facts.json, codegen
 * must reproduce the .dfy, the ledger must reproduce itself — and a simulator artifact that no
 * gate can re-derive is a file nobody can check.
 */
export function build(dir: string) {
const bags: Bag[] = [];
const cleanBoards: CleanBoard[] = [];
const rounds: Round[] = [];
const spinWindows: { user: string; lines: number; drawn: boolean; mirrored: boolean }[] = [];
const tspinClears: TSpinClear[] = [];
/** The licensing check on metrics 7 and 8 — see `reconstructionCheck`. */
let reconAgreed = 0, reconDisagreed = 0;
let roundsTotal = 0;

for (const c of loadCases(dir)) {
  roundsTotal++;
  const r = runCaseOracle(c);
  const v = verifiedIndex(r, c.truth);

  const spinsAll = r.locks
    .map((lk, i) => ({ i, cleared: lk.cleared, spin: lk.spin }))
    .filter(x => x.spin !== 'none' && x.cleared > 0)     // detectTSpin returns 'none' unless the piece is a T
    .map(({ i, cleared }) => ({ i, cleared }));
  const acReal = c.clears.allclear;
  rounds.push({ user: c.user, verified: v, spinsAll,
                spinsVerified: spinsAll.filter(x => x.i <= v),
                pcLocks: r.locks.flatMap((lk, i) => (lk as { allclear?: boolean }).allclear ? [i] : []),
                pcReal: typeof acReal === 'number' ? acReal : null });

  // slot geometry, over the verified prefix only
  for (const s of spinsAll) {
    if (s.i > v) continue;
    const lk = r.locks[s.i]!;
    const board = r.boards[s.i - 1];                     // pre-lock board; lock 0 has none to read
    if (!board) continue;
    const m = mask((row, col) =>
      col < 0 || col >= BOARD_WIDTH || row >= H ? true : row < 0 ? false : board[row]![col] !== null,
      lk.cells);
    const eq = (a: string[]) => a.length === m.length && a.every((l, i) => l === m[i]);
    spinWindows.push({ user: c.user, lines: s.cleared,
                       drawn: wikiMasks.some(w => eq(w.mask)),
                       mirrored: wikiMasks.some(w => eq(w.mirror)) });
  }

  // metrics 7 & 8 — the two board-state techniques, over the same verified prefix as the geometry
  // above. Both read the board the T went into, so both are collected in one pass.
  for (let i = 0; i < r.locks.length; i++) {
    const lk = r.locks[i]!;
    if (lk.piece !== 'T' || lk.spin === 'none' || lk.cleared === 0 || i > v) continue;
    const withT = occupancyOf(i > 0 ? (r.boards[i - 1] as (string | null)[][] | undefined) : undefined);
    for (const q of lk.cells)
      if (q.row >= 0 && q.row < H && q.col >= 0 && q.col < BOARD_WIDTH) withT[q.row]![q.col] = true;

    // THE LICENSING CHECK. `withT` is the per-lock board snapshot plus this lock's cells; the rows
    // it makes full must be exactly the rows the engine recorded clearing, which it derived from a
    // different state (its pre-tick occupancy). Two sources, so their agreement is a real gate and
    // not a tautology — and a clear they disagree about is dropped rather than scored.
    const mine: number[] = [];
    for (let rr = 0; rr < H; rr++) if (withT[rr]!.every(Boolean)) mine.push(rr);
    const theirs = [...(r.records[i]?.clearedRows ?? [])].sort((a, b) => a - b);
    if (!(mine.length === theirs.length && mine.every((x, k) => x === theirs[k]))) { reconDisagreed++; continue; }
    if (!mine.length) continue;
    reconAgreed++;

    const wells = donationCols(withT, mine, lk.cells, H);
    let donation: TSpinClear['donation'] = null;
    if (wells.length) {
      const w = wells[0]!;
      const prov = i > 0 ? r.provSnaps[i - 1] : undefined;
      // WELL PROVENANCE. A well ROW is garbage-derived when that row's FILLED cells are mostly
      // garbage. Never test the well cell itself for the -1 garbage tag: it is EMPTY by
      // construction and so carries null, which made an earlier pass report every well in the
      // corpus as self-built — a guard that can never fire reads exactly like a measurement.
      let garbageWell = false;
      for (let rr = 0; rr < H && !garbageWell; rr++) {
        if (withT[rr]![w.col]) continue;
        let filled = 0, gb = 0;
        for (let cc = 0; cc < BOARD_WIDTH; cc++) {
          const q = prov?.[rr]?.[cc];
          if (q != null) { filled++; if (q === -1) gb++; }
        }
        if (filled > 0 && gb * 2 >= filled) garbageWell = true;
      }
      // harddrop's own division: a Natural Donation plugs with a lock that cleared nothing, the
      // Other Examples plug with one that cleared a row and so broke the back-to-back chain.
      const plugLock = prov?.[mine[0]!]?.[w.col];
      const plug = typeof plugLock === 'number' && plugLock >= 0 && r.locks[plugLock]
        ? (r.locks[plugLock]!.cleared > 0 ? 'b2b_breaking' as const : 'natural' as const)
        : null;
      donation = { cavity: w.cavity, garbageWell, plug };
    }

    tspinClears.push({ user: c.user, lines: lk.cleared, lock: i, donation,
                       cave: caveAt(withT, mine, lk.cells, H),
                       wideGapUnderTriple: lk.cleared === 3 && wideGapUnder(withT, mine, H) });
  }

  // The opening board after n locks, for each n an opener can end its first bag on: no line clear
  // and no garbage before that point, and the whole prefix inside the verified window.
  for (const n of OPENER_LOCKS) {
    if (v < n - 1) continue;
    let clean = true;
    for (let i = 0; i < n; i++) if (r.locks[i]!.cleared > 0) clean = false;
    for (const g of r.garbageEvents) if (g.lockIndex < n) clean = false;
    if (!clean) continue;
    const board = r.boards[n - 1];
    if (!board) continue;
    const rows = rowsFromBoard(board as (string | null)[][]);
    if (!rows) continue;
    cleanBoards.push({ user: c.user, round: rounds.length - 1, locks: n, grid: occGrid(rows) });
    // `bags` is the seven-lock series the original first-bag metric is defined over. Kept as its
    // own list rather than filtered out of `cleanBoards` at each use, so that metric's numbers are
    // provably untouched by the widening: five sessions re-emit byte-identical first_bag blocks.
    if (n === 7) bags.push({ user: c.user, grid: occGrid(rows) });
  }
}

const users = [...new Set(rounds.map(r => r.user))].sort();

// ── metric 1: first bag vs the catalogue ───────────────────────────────────────────────────────
function firstBagFor(user: string) {
  const mine = bags.filter(b => b.user === user);
  const exact = new Map<string, number>();
  for (const b of mine) {
    const hit = exactMatches(b.grid, prepared);
    // count ROUNDS per name: a symmetric field matches both as drawn and mirrored, and counting
    // entries would double every one of them
    for (const n of new Set([...hit.asDrawn, ...hit.asMirror]))
      exact.set(n, (exact.get(n) ?? 0) + 1);
  }

  const per = (pages: typeof prepared) => {
    const bandsOut = emptyBands();
    let min: number | null = null, within = 0;
    for (const b of mine) {
      const d = nearest(b.grid, pages).d;
      if (!Number.isFinite(d)) continue;                 // no page at this cell count to compare with
      bandsOut[band(d)]!++;
      if (min === null || d < min) min = d;
      if (d <= NEAR_CELLS) within++;
    }
    return { min_cells: min, within_threshold: within, bands: bandsOut };
  };

  return {
    user,
    clean_first_bags: mine.length,
    exact_matches: [...exact].sort((a, b) => b[1] - a[1]).map(([name, r]) => ({ name, rounds: r })),
    nearest: {
      any: per(prepared),
      ...Object.fromEntries(sets.map(s => [s.key, per(s.pages)])),
    },
  };
}

// ── metric 2: ordering ─────────────────────────────────────────────────────────────────────────
// The order is scored over the OPENER window (a spin's lock index <= WINDOW_PIECES = 21 = 3 bags, the
// wiki's C-Spin follow-up span). This is load-bearing: the C-Spin/DT distinction is an OPENING technique,
// and over a whole round these players throw ordinary T-spin doubles by the dozen, so "did any triple
// precede any double" is a statement about playstyle, not the opener. The hand-sim's short verified prefix
// hid this by truncating to the opening; the oracle board source (runCaseOracle) reaches the whole round,
// so the window must be made explicit. Measured (oracle, five sessions): at the opener window every round
// holding both spins runs the C-Spin order — cspin_order === rounds_with_both, dt_order == 0 — while over
// the whole prefix 7 rounds show a late-game double-before-triple that is not a DT Cannon.
function orderingFor(user: string, pick: (r: Round) => { i: number; cleared: number }[]) {
  const mine = rounds.filter(r => r.user === user && r.verified >= 0);
  const inOpener = (x: { i: number }) => x.i <= WINDOW_PIECES;
  const D = (r: Round) => pick(r).filter(x => x.cleared === 2 && inOpener(x));
  const T = (r: Round) => pick(r).filter(x => x.cleared === 3 && inOpener(x));
  const ordered = (a: { i: number }[], b: { i: number }[], win: number | null) =>
    a.some(x => b.some(y => x.i < y.i && (win === null || y.i - x.i <= win)));
  const both = mine.filter(r => D(r).length && T(r).length);
  const firstT = mine.filter(r => T(r).length).map(r => Math.min(...T(r).map(x => x.i)));
  return {
    user,
    rounds_scored: mine.length,
    rounds_with_tspin_double: mine.filter(r => D(r).length).length,
    rounds_with_tspin_triple: mine.filter(r => T(r).length).length,
    rounds_with_both: both.length,
    dt_order: both.filter(r => ordered(D(r), T(r), null)).length,
    cspin_order: both.filter(r => ordered(T(r), D(r), null)).length,
    dt_order_within_window: both.filter(r => ordered(D(r), T(r), WINDOW_PIECES)).length,
    cspin_order_within_window: both.filter(r => ordered(T(r), D(r), WINDOW_PIECES)).length,
    first_triple_lock: { min: firstT.length ? Math.min(...firstT) : null,
                         median: median(firstT),
                         max: firstT.length ? Math.max(...firstT) : null },
    mid_game: midGameOrderingFor(user, pick),
  };
}

/**
 * THE SAME ORDERING, OUTSIDE the opener window — the control the window itself never had.
 *
 * Every count above is taken over spins at lock <= WINDOW_PIECES, so "354 of 354 rounds ran
 * Triple-first" is a statement about openings that the artifact previously gave a reader no way to
 * check. It could equally have been a statement about how these players throw T-spins at any point
 * in a round, and the two readings imply completely different things about the C-Spin.
 *
 * They come apart when measured. Over five sessions the opener window holds 354 rounds with both
 * spins and NOT ONE runs Double-first; outside it the order is mixed in both directions. So the
 * window is doing real work, and this block is what shows it rather than asserting it.
 *
 * ITS DENOMINATOR IS SMALL AND THAT IS THE POINT OF REPORTING IT AS COUNTS. Only nine rounds in the
 * whole corpus hold both spin types after piece 21 — rounds usually end first, and the verified
 * prefix truncates what is left — so a percentage over them would read far more confident than the
 * data is. Same rule the 全消 section follows for its 3-12 round denominators.
 */
function midGameOrderingFor(user: string, pick: (r: Round) => { i: number; cleared: number }[]) {
  const mine = rounds.filter(r => r.user === user && r.verified >= 0);
  const after = (r: Round, lines: number) =>
    pick(r).filter(x => x.cleared === lines && x.i > WINDOW_PIECES);
  const both = mine.filter(r => after(r, 2).length && after(r, 3).length);
  const first = (a: { i: number }[], b: { i: number }[]) => a.some(x => b.some(y => x.i < y.i));
  return {
    rounds_with_both: both.length,
    cspin_order: both.filter(r => first(after(r, 3), after(r, 2))).length,
    dt_order: both.filter(r => first(after(r, 2), after(r, 3))).length,
    means: 'the same two orderings scored on spins AFTER the opener window, which is the control on '
         + 'the counts beside them: inside the window the corpus is unanimous, outside it the order '
         + 'goes both ways. Counts, never a rate — the whole corpus holds only a handful of rounds '
         + 'with both spin types this late',
  };
}

// ── metric 4: the named openers ────────────────────────────────────────────────────────────────
// One row per opener the report talks about, scored the same way for all of them: the player's
// clean opening boards against that opener's own drawings.
//
// THE CONTROL IS THE OPPORTUNITY COUNT, and it is `boards_scored`. A rate needs a denominator and
// the denominator here is not "rounds" — it is "rounds whose opening board was sampled at a lock
// count this opener is even drawn at". Stray Cannon is drawn at six locks, so a round that never
// produced a clean six-lock board cannot show a Stray Cannon and must not be counted against it.
// Printing `0 of 522 rounds` where the truth is `0 of 431 comparable boards` would be inventing
// evidence of absence out of a sampling gap — which is precisely the bug OPENER_LOCKS just fixed.
/** The opener's payoff, scored over VERIFIED spins inside the opener window.
 *
 *  Verified, not merely simulated: a T-spin the simulator believes in has no second source, so the
 *  window where the sim is checked against the replay's own garbage record is the only place its
 *  spins may be counted from.
 *
 *  The Perfect Clear flag is the exception, and it earns it by measurement rather than by argument
 *  — see `perfectClearTiming`, which checks the simulator's per-round count against the replay's own
 *  `results.stats.clears.allclear` for every player-round in the session and publishes the result.
 *  Over the five committed sessions that check is 592/592 rounds and 65/65 Perfect Clears.
 *
 *  (An earlier revision of this comment said the opposite — that the flag reported clears the
 *  session did not have. That reading came from a facts.json lookup one level too shallow, which
 *  returned zero for every session; the sessions hold 65 Perfect Clears between them and the flag
 *  found exactly those. The lesson kept from it is in `sessionPerfectClears`: a bound must fail
 *  loudly rather than quietly report the zero it never read.)
 *
 *  Triple-before-Double is the signature of the whole `Triple Double openers` category — see
 *  `ordering_class` for why it can never name which member was played. */
const openedTripleFirst = (r: Round) => {
  const s = r.spinsVerified.filter(x => x.i <= WINDOW_PIECES);
  const t = s.filter(x => x.cleared === 3), d = s.filter(x => x.cleared === 2);
  return t.some(x => d.some(y => x.i < y.i));
};
/** TKI-3's payoff is the opening T-spin Double it is named for (開幕TSD), not a Triple Double. */
const openedDouble = (r: Round) =>
  r.spinsVerified.some(x => x.i <= WINDOW_PIECES && x.cleared === 2);

/** harddrop defines the Perfect Clear Opener by an outcome and gives the deadline in pieces: "a
 *  Perfect Clear in the first 4 lines of a game (10 dropped pieces)". Ten locks is that sentence
 *  read literally, and it is a much tighter window than WINDOW_PIECES — an opener that has to
 *  finish inside one and a half bags is not the same kind of claim as one with three bags. */
const PCO_LOCKS = 10;
/** PCO's payoff: the board came out empty inside harddrop's own ten-piece deadline. Scored off the
 *  simulator's lock indices, whose per-round COUNT is checked against the replay in
 *  `perfectClearTiming` — the position within the round is the only part with no second source. */
const openedPerfectClear = (r: Round) => r.pcLocks.some(i => i < PCO_LOCKS);

function namedOpenerFor(op: ReturnType<typeof loadWikiOpeners>['openers'][number]) {
  const pool = openerPages(op, prepared);
  const locks = new Set(pool.locks);
  const inTD = tdc.members.includes(op.page);

  // THE BASELINE, and the reason `within_threshold` may not be read as a hit rate. Every clean
  // catalogue page at the same lock counts, minus this opener's own fields: what a board scores
  // against openers it is NOT playing. Measured, these boards sit 3-4 cells from almost any opener
  // page, so the <=4 band is ~90% for everything and discriminates nothing; only an EXACT match
  // separates the openers. Emitting the baseline is what lets a reader see that, instead of
  // reading 89% as "89% Honey Cup".
  const own = new Set(pool.pages.flatMap(p => [p.grid.join('/'), p.mirror.join('/')]));
  const control = prepared.filter(p =>
    locks.has(p.cells / 4) && !hasFullRow(p.page.rows)
    && !own.has(p.grid.join('/')) && !own.has(p.mirror.join('/')));

  const players = users.map(user => {
    const mine = cleanBoards.filter(b => b.user === user && locks.has(b.locks));
    const bandsOut = emptyBands();
    let min: number | null = null, within = 0, exact = 0, baseExact = 0, baseWithin = 0;
    const matched: number[] = [];
    for (const b of mine) {
      const d = nearest(b.grid, pool.pages).d;
      if (Number.isFinite(d)) {
        bandsOut[band(d)]!++;
        if (min === null || d < min) min = d;
        if (d <= NEAR_CELLS) within++;
        if (d === 0) { exact++; matched.push(b.round); }
      }
      const c = nearest(b.grid, control).d;
      if (Number.isFinite(c)) { if (c === 0) baseExact++; if (c <= NEAR_CELLS) baseWithin++; }
    }
    // The outcome check: of the boards that ARE this opener's field, how many went on to do what
    // the opener is for? A shape with no outcome behind it is a coincidence of stacking.
    const rs = [...new Set(matched)].map(i => rounds[i]!);
    const did = inTD ? rs.filter(openedTripleFirst).length
              : op.key === 'tki_3' ? rs.filter(openedDouble).length
              : op.key === 'pco' ? rs.filter(openedPerfectClear).length
              : null;
    return {
      user, boards_scored: mine.length,
      exact, min_cells: min,
      within_threshold: within, share_x1000: rate(within, mine.length),
      bands: bandsOut,
      baseline: { exact: baseExact, within_threshold: baseWithin, pages: control.length },
      matched_rounds: rs.length,
      matched_and_delivered: did,
      _rounds: [...new Set(matched)],
    };
  });
  // Which OTHER named openers this one cannot be told apart from. Occupancy is the key that
  // decides (see match.ts), and Mountainous Stacking 1 and 2 are drawn from different pieces into
  // the SAME first-bag shape — they differ in which piece is held, which a filled/empty grid
  // cannot see. Their rows are therefore identical in every session, and a reader summing the
  // table would count one opening twice. Derived by comparing the fields, never typed in, so a
  // redrawn wiki page changes the alias list instead of leaving a stale note behind.
  const keys = new Set(pool.pages.flatMap(p => [p.grid.join('/'), p.mirror.join('/')]));
  const aliases = wiki.openers
    .filter(o => o.key !== op.key)
    .filter(o => openerPages(o, prepared).pages
      .some(p => keys.has(p.grid.join('/')) || keys.has(p.mirror.join('/'))))
    .map(o => o.wiki);

  return {
    key: op.key, wiki: op.wiki, jp: op.jp, page: op.page, url: op.url, wiki_says: op.wiki_says,
    in_triple_double_category: inTD,
    /** named openers with an identical first-bag field — their columns are not independent */
    occupancy_aliases: aliases,
    delivers: inTD ? `a T-spin Triple before a T-spin Double within ${WINDOW_PIECES} pieces`
            : op.key === 'tki_3' ? `a T-spin Double within ${WINDOW_PIECES} pieces`
            : op.key === 'pco' ? `a perfect clear within ${PCO_LOCKS} locks`
            : null,
    drawn_at_locks: pool.locks,
    pages: pool.source,
    players,
  };
}

/**
 * The bound on the PCO row, taken from the VERIFIED source rather than from the simulator.
 *
 * PCO is the one opener here defined by an event instead of a picture — harddrop calls it "a
 * Perfect Clear in the first 4 lines of a game (10 dropped pieces)" — so its shape metric begs to
 * be checked against whether the perfect clear actually arrived. The simulator cannot answer that:
 * see `openedTripleFirst` for the measurement that says so.
 *
 * `clears.allclear` in the .ttrm can answer it, and both independent extractors already read it
 * into facts.json. So the count is taken from there and reported as a CEILING: a session with zero
 * perfect clears cannot contain a completed PCO however many boards match its field, and that
 * sentence is worth more than any similarity score.
 *
 * Returns null when facts.json is absent (bin/new-session emits the replays before the report), so
 * a missing bound reads as "not known here" and never as "zero".
 *
 * ABSENT AND ZERO ARE DIFFERENT, and the first version of this function did not distinguish them.
 * It read `rd.players[u].allclear` — one level too shallow, the counter lives under `clears` — and
 * `?? 0` turned every lookup of an undefined field into a legitimate-looking zero. All five sessions
 * published "not one Perfect Clear all night" while the .ttrm files hold 62 of them. Nothing caught
 * it: the value was in range, the artefact regenerated byte-identically, and the test recomputed the
 * total down the SAME wrong path, so it agreed with itself.
 *
 * So the shape below declares `clears.allclear` REQUIRED, which makes the shallow read a type error,
 * and the loop throws on a non-number instead of defaulting. A required field that goes missing has
 * to be loud; the quiet reading of it is indistinguishable from data.
 */
function sessionPerfectClears(dir: string) {
  let facts: { matches: { rounds: { players: Record<string, { clears: { allclear: number } }> }[] }[] };
  try {
    facts = JSON.parse(readFileSync(`${dir}/report/facts.json`, 'utf8'));
  } catch {
    return null;
  }
  const per: Record<string, number> = {};
  for (const m of facts.matches)
    for (const rd of m.rounds)
      for (const [user, st] of Object.entries(rd.players)) {
        const v = st.clears?.allclear;
        if (typeof v !== 'number')
          throw new Error(`facts.json: players.${user}.clears.allclear is not a number — `
                        + `the bound must fail loudly rather than report a zero it did not read`);
        per[user] = (per[user] ?? 0) + v;
      }
  return {
    source: 'report/facts.json (clears.allclear, read independently by extract.py and extract2.ts)',
    means: 'an upper bound on completed Perfect Clear Openers: a session cannot hold more completed '
         + 'PCOs than it holds perfect clears, whatever the opening fields looked like — and a '
         + 'session with none cannot hold one at all. Which of them arrived early enough to BE a '
         + 'PCO is `perfect_clear_timing`, and that answer comes from the simulator',
    per_player: Object.fromEntries(users.map(u => [u, per[u] ?? 0])),
  };
}

/**
 * ── metric 6: WHEN the Perfect Clear arrived ───────────────────────────────────────────────────
 *
 * The report's own 全消 section already counts Perfect Clears, twice-extracted and Dafny-proved. It
 * cannot say *when* one landed, because facts.json stores counts and nothing about ordering. That
 * is the question PCO is defined by — harddrop's deadline is ten dropped pieces — so it is worth
 * asking, and only the simulator can answer it.
 *
 * THE CONTROL IS THE COUNT ITSELF, and it is the strongest one in this file. A simulator flag has
 * no second implementation to be checked against, but this particular flag has something almost as
 * good: the same quantity, per round, in the replay's own `results.stats.clears.allclear` — the
 * field both extractors read into facts.json. So every player-round is compared, the totals are
 * published beside the timing, and `by_lock` is emitted as null when a single round disagrees.
 * Timing that no count agrees with is a number with nothing behind it.
 *
 * A round whose replay carries no allclear counter is UNKNOWN, not zero: it is counted in
 * `unknown_rounds` and excluded from `rounds_agreeing`, so a corpus that stopped carrying the field
 * reads as unchecked rather than as perfect agreement.
 *
 * Positions are published as PIECE NUMBERS (1-based), which is how harddrop's ten-piece deadline is
 * written; `pcLocks` is 0-based internally.
 */
function perfectClearTiming() {
  let agree = 0, unknown = 0, sim = 0, real = 0;
  for (const r of rounds) {
    sim += r.pcLocks.length;
    if (r.pcReal === null) { unknown++; continue; }
    real += r.pcReal;
    if (r.pcReal === r.pcLocks.length) agree++;
  }
  const checked = rounds.length - unknown;
  const ok = checked > 0 && agree === checked;
  const players = users.map(user => {
    const mine = rounds.filter(r => r.user === user);
    const at = mine.flatMap(r => r.pcLocks.map(i => i + 1)).sort((a, b) => a - b);
    const hist: Record<string, number> = {};
    for (const p of at) hist[String(p)] = (hist[String(p)] ?? 0) + 1;
    return {
      user,
      perfect_clears: mine.reduce((s, r) => s + (r.pcReal ?? 0), 0),
      rounds_with_one: mine.filter(r => (r.pcReal ?? 0) > 0).length,
      // null rather than {} when the check failed: an empty histogram would render as
      // "measured, and nothing was there", which is the opposite of "not established".
      by_piece: ok ? hist : null,
      median_piece: ok ? median(at) : null,
      within_pco_window: ok ? at.filter(p => p <= PCO_LOCKS).length : null,
    };
  });
  return {
    source: 'the oracle board source (runCaseOracle), checked per round against the replay\'s own '
          + 'results.stats.clears.allclear — the field extract.py and extract2.ts read into facts.json',
    pco_window_locks: PCO_LOCKS,
    check: { player_rounds: rounds.length, checked, unknown_rounds: unknown,
             rounds_agreeing: agree, agrees: ok,
             perfect_clears_sim: sim, perfect_clears_replay: real },
    players,
  };
}

/**
 * The check that licenses metrics 7 and 8, in the same shape `perfect_clear_timing` publishes its
 * own: a per-event comparison of two states that were built separately, emitted rather than
 * asserted. `withT` (the per-lock board snapshot plus the lock's cells) must make exactly the rows
 * full that the engine's pre-tick occupancy said it cleared. Over the five committed sessions it
 * does on every one of them; a clear they disagree about is dropped, never scored.
 */
const reconstructionCheck = () => ({
  tspin_clears: reconAgreed + reconDisagreed,
  reconstruction_agreed: reconAgreed,
  reconstruction_disagreed: reconDisagreed,
  agrees: reconDisagreed === 0 && reconAgreed > 0,
});

// ── metric 7: DONATION ─────────────────────────────────────────────────────────────────────────
// THE CONTROL IS THE TWO SPLITS, and neither may be dropped. The b2b split reproduces harddrop's
// own Natural-vs-Other-Examples division from the plugging lock; the provenance split says whose
// well it was. Both matter because the corpus answers them the same way every time — all of these
// wells are garbage-derived — which is exactly the finding, and also the caveat (see below).
function donationMetric() {
  return {
    source: 'harddrop.com/wiki/Donation',
    definition: 'plugging the well with a piece so a T-spin can clear the rows across it, the clear '
              + 'then re-opening the well surface-to-floor — the plug is a loan, not a wall',
    cavity_cells: DONATION_CAVITY,
    walled_deepest_rows: DONATION_WALLED_ROWS,
    scope: 'verified prefix',
    check: reconstructionCheck(),
    players: users.map(user => {
      const mine = tspinClears.filter(e => e.user === user);
      const d = mine.filter(e => e.donation).map(e => e.donation!);
      return {
        user,
        tspin_clears_scored: mine.length,
        donations: d.length,
        self_built_well: d.filter(x => !x.garbageWell).length,
        garbage_derived_well: d.filter(x => x.garbageWell).length,
        natural: d.filter(x => x.plug === 'natural').length,
        b2b_breaking: d.filter(x => x.plug === 'b2b_breaking').length,
        plug_unknown: d.filter(x => x.plug === null).length,
        // where in the round the donations fell. harddrop files Donation under `Mid-game T-Spin
        // setups`, and this is the measurement behind that citation rather than a repetition of it.
        in_opener: mine.filter(e => e.donation && e.lock <= WINDOW_PIECES).length,
        mid_game: mine.filter(e => e.donation && e.lock > WINDOW_PIECES).length,
      };
    }),
    opener_window_pieces: WINDOW_PIECES,
    means: 'how many verified T-spin clears were fired across a plugged well that the clear then '
         + 're-opened — every filled cell of that column lay inside the cleared rows, with at least '
         + `${DONATION_CAVITY} empty cells walled beneath it. The naive reading of the technique `
         + '("the well was filled through the cleared rows") is FORCED BY ARITHMETIC — a full row '
         + 'requires every column filled — and fires on 70-89% of all T-spin clears; the discriminating '
         + 'clause is the re-opening, and that is what is counted here',
    caveat: 'every donation in this corpus sits on a GARBAGE-derived well, and the oracle board '
          + 'source keeps the engine\'s own seeded-RNG hole columns, which disagree with the '
          + 'ige-recorded columns 97 of 103 times (see oracle-source.ts). So the count says the board '
          + 'offered this shape that often; it does not establish WHICH column any one donation used, '
          + 'and it may never be read as "this player donated into that well"',
  };
}

// ── metric 8: STMB CAVE ────────────────────────────────────────────────────────────────────────
// THE CONTROL IS THE CROSS-TAB, in two directions, and this metric may not be printed without both:
//   - by DEPTH: nearly every >=3-wide hit is ONE ROW deep, which is a dimple and not a cave. The
//     width count on its own reads as dozens of STMB caves; the depth histogram beside it says how
//     many are genuine (1 in 592 player-rounds, five sessions).
//   - by LINES: the same >=3-wide gap appears under T-spin TRIPLES at a comparable rate, where it
//     is ordinary TST residue that nobody calls a cave. A shape that fires as often under the spin
//     the technique is NOT about is a shape test, not a technique test.
function stmbCaveMetric() {
  const wide = tspinClears.filter(e => e.cave && e.cave.width >= CAVE_MIN_WIDTH);
  const hist = (xs: number[]) => {
    const h: Record<string, number> = {};
    for (const x of xs) h[String(x)] = (h[String(x)] ?? 0) + 1;
    return h;
  };
  const triples = tspinClears.filter(e => e.lines === 3);
  return {
    source: 'harddrop.com/wiki/STMB_Cave',
    definition: 'a floating T-spin Double placed over a cave at least three columns wide — the cave '
              + 'is OFFSET from the T, sharing two of its three columns, so the test is overlap with '
              + 'the T\'s span and never containment',
    min_width: CAVE_MIN_WIDTH,
    scope: 'verified prefix',
    players: users.map(user => {
      const mine = tspinClears.filter(e => e.user === user);
      const w = mine.filter(e => e.cave && e.cave.width >= CAVE_MIN_WIDTH);
      return {
        user,
        tspin_doubles_scored: mine.filter(e => e.lines === 2).length,
        width_ge_3: w.length,
        min_depth_ge_2: w.filter(e => e.cave!.minDepth >= 2).length,
        // Measured, five sessions: every single cave falls OUTSIDE the opener window — 0 in, 30
        // out. That is this metric's cleanest result, and it is the one number here that confirms
        // harddrop's own filing of the technique instead of citing it.
        in_opener: w.filter(e => e.lock <= WINDOW_PIECES).length,
        mid_game: w.filter(e => e.lock > WINDOW_PIECES).length,
      };
    }),
    opener_window_pieces: WINDOW_PIECES,
    width_histogram: hist(wide.map(e => e.cave!.width)),
    min_depth_histogram: hist(wide.map(e => e.cave!.minDepth)),
    triple_control: {
      tspin_triples_scored: triples.length,
      width_ge_3: triples.filter(e => e.wideGapUnderTriple).length,
    },
    means: 'how many verified T-spin Doubles landed over a >= 3-wide gap overlapping the T\'s '
         + 'columns. Read it against BOTH controls beside it and never on its own: '
         + '`min_depth_histogram` says how deep those gaps were, and a one-row-deep 3-wide gap is a '
         + 'dimple rather than a cave; `triple_control` counts the same shape under T-spin Triples, '
         + 'where it is ordinary TST residue',
  };
}

// ── metric 3: slot geometry, cross-tabbed by lines (the control) ───────────────────────────────
function slotRows() {
  const out = [];
  for (const lines of [1, 2, 3]) {
    const es = spinWindows.filter(e => e.lines === lines);
    const hit = es.filter(e => e.drawn || e.mirrored).length;
    out.push({ lines, n: es.length,
               drawn: es.filter(e => e.drawn).length,
               mirrored: es.filter(e => e.mirrored).length,
               matched: hit, share_x1000: rate(hit, es.length) });
  }
  return out;
}

// ── assemble ───────────────────────────────────────────────────────────────────────────────────
const session = dir.split('/').filter(Boolean).pop()!;
const ordering = users.map(u => orderingFor(u, r => r.spinsVerified));
const orderingFull = users.map(u => orderingFor(u, r => r.spinsAll));
const namedRaw = wiki.openers.map(namedOpenerFor);

/**
 * How many ROUNDS each pair of named openers both claim — the control that says the columns are
 * not independent and must not be summed.
 *
 * Two ways a round lands in two columns, and only the first is a drawing coincidence:
 *   - identical fields (`occupancy_aliases`): Mountainous Stacking 1 and 2 are the same bag-1
 *     shape built from different pieces, so every round matching one matches the other;
 *   - different LOCK COUNTS: an opener drawn at six locks and one drawn at seven are compared
 *     against two different snapshots of the same round, so a round can genuinely be on its way to
 *     one shape at six locks and be the other at seven.
 * Neither is an error. Publishing a table whose rows sum past the round count without saying so
 * would be.
 */
const overlap = (() => {
  const keys = namedRaw.map(o => o.key);
  const setOf = (o: typeof namedRaw[number]) =>
    new Set(o.players.flatMap(p => p._rounds));
  const out: Record<string, Record<string, number>> = {};
  for (let i = 0; i < namedRaw.length; i++) {
    const a = setOf(namedRaw[i]!);
    if (!a.size) continue;
    const row: Record<string, number> = {};
    for (let j = 0; j < namedRaw.length; j++) {
      if (i === j) continue;
      const shared = [...setOf(namedRaw[j]!)].filter(r => a.has(r)).length;
      if (shared) row[keys[j]!] = shared;
    }
    if (Object.keys(row).length) out[keys[i]!] = row;
  }
  return out;
})();

/** `_rounds` is working state for the overlap matrix, not a published field. */
const named = namedRaw.map(o => ({
  ...o,
  players: o.players.map(({ _rounds, ...p }) => p),
}));

/** Every reason this artifact is not report-eligible, DERIVED rather than typed, so it cannot
 *  describe a state the data has left. */
function notEligibleBecause() {
  const why = [
    'simulator-derived: no second independent implementation (dual-extractor rule unmet)',
    'the first-bag metric is bounded by CATALOGUE COVERAGE, not by the matcher: a null means '
    + '"not these catalogued pages", never "not this opener"',
  ];
  const tot = slotRows().reduce((a, r) => a + r.n, 0);
  const three = slotRows().find(r => r.lines === 3);
  const two = slotRows().find(r => r.lines === 2);
  if (three?.share_x1000 != null && two?.share_x1000 != null)
    why.push('the slot-geometry match is a SHAPE test, not an opener test: '
      + `${(three.share_x1000 / 10).toFixed(1)}% of Triples match the wiki window against `
      + `${(two.share_x1000 / 10).toFixed(1)}% of Doubles, over ${tot} verified T-spins`);
  const scored = ordering.reduce((a, p) => a + p.rounds_scored, 0);
  const covered = ordering.reduce((a, p) => a + p.rounds_with_both, 0);
  why.push(`the ordering metric is scored on ${covered} of ${scored} rounds — those holding both a `
    + 'T-spin Double and a T-spin Triple; rounds with only one of the two cannot show an order');
  why.push(`the ordering metric names a CLASS, not an opener: harddrop files ${tdc.members.length} `
    + `openers under "${tdc.name}" — C-Spin, Honey Cup, Stray Cannon and Mountainous Stacking `
    + 'among them — and every one of them opens Triple-before-Double');
  why.push(`the named-opener match is bounded by how each opener is DRAWN: ${catClean} of `
    + `${cat.pages.length} catalogue pages are free of a full row and so could ever equal a `
    + 'no-clear opening board; TKI-3 has 12 catalogue pages and none of them qualify, which is '
    + 'why harddrop\'s own diagrams are carried alongside');
  const don = donationMetric().players.reduce((a, p) => a + p.donations, 0);
  const gb = donationMetric().players.reduce((a, p) => a + p.garbage_derived_well, 0);
  why.push(`the donation metric is bounded by the oracle's GARBAGE HOLE COLUMNS: ${gb} of ${don} `
    + 'donations here sit on a garbage-derived well, and the oracle keeps the engine\'s own '
    + 'seeded-RNG hole columns, which disagree with the ige-recorded ones 97 of 103 times '
    + '(oracle-source.ts) — so the shape is counted, but which column any one donation used is not '
    + 'established');
  return why;
}

return {
  schema: 'opener-facts/1',
  report_eligible: false,
  not_eligible_because: notEligibleBecause(),
  session,
  gate: 'frame+amount+row (ige row oracle must agree)',
  // Boards come from the vendored Triangle engine (runCaseOracle), byte-identical to @haelp/teto — NOT
  // the hand-sim, whose BEST_OPTS fit only ~24.8% of attacks vs the oracle's 92.3% on this same gate.
  board_source: 'triangle-oracle (vendored @haelp/teto, byte-identical)',
  window_pieces: WINDOW_PIECES,
  near_cells: NEAR_CELLS,
  definitions: {
    dt_order: 'a T-spin Double before a T-spin Triple — DT Cannon (開幕DT砲) by definition',
    cspin_order: 'a T-spin Triple before a T-spin Double — the C-Spin follow-up by definition',
  },
  catalogue: {
    source: cat.provenance.source,
    commit: cat.provenance.commit,
    data_json_sha256: cat.provenance.data_json_sha256,
    pages: cat.pages.length,
    openers: catNames.length,
    sets: Object.fromEntries(sets.map(s =>
      [s.key, { label: s.label, openers: s.names.length, pages: s.pages.length, names: s.names }])),
  },
  wiki_cspin: { source: 'harddrop.com/wiki/C-Spin', placements: WIKI_CSPIN.length },
  first_bag: {
    rounds: roundsTotal,
    clean: bags.length,
    players: users.map(firstBagFor),
  },
  ordering: { scope: 'verified prefix', players: ordering },
  ordering_full_round: { scope: 'whole simulated round, verification NOT required', players: orderingFull },
  slot_geometry: { source: 'harddrop.com/wiki/C-Spin', placements: WIKI_CSPIN.length, rows: slotRows() },

  /** The control on the ordering metric, and the reason it may not be printed as a C-Spin count.
   *
   *  `cspin_order` counts "a T-spin Triple before a T-spin Double in the opener". harddrop keeps a
   *  category for exactly that shape — `Triple Double openers`, 38 of them — and C-Spin is one
   *  member of it, alongside Honey Cup, Stray Cannon and Mountainous Stacking. So the number
   *  identifies the CLASS and cannot distinguish its members; a session that ran Honey Cup every
   *  round would produce precisely the same 221-of-221.
   *
   *  This is transcribed from harddrop's category page rather than assembled here, because a class
   *  this repo drew for itself would be a class chosen to fit the result. */
  ordering_class: {
    source: tdc.url, name: tdc.name, says: tdc.says, openers: tdc.members.length,
    members: tdc.members,
    means: 'a Triple-before-Double opening is the signature of this whole category, not of any one '
         + 'opener in it — the ordering metric cannot name which member was played',
  },

  /** Per-opener coverage and match, one row per opener the report names. */
  named_openers: {
    source: wiki.source,
    why_a_second_source: wiki.why,
    provenance: wiki.provenance,
    catalogue_pages: cat.pages.length,
    catalogue_pages_clean: catClean,
    sampled_at_locks: [...OPENER_LOCKS],
    /** rounds claimed by two openers at once — see the comment on `overlap` */
    round_overlap: overlap,
    boards: {
      total: cleanBoards.length,
      by_locks: Object.fromEntries(OPENER_LOCKS.map(n =>
        [n, cleanBoards.filter(b => b.locks === n).length])),
    },
    openers: named,
  },

  /** The ceiling on the PCO row, from the verified extractors rather than from this simulator. */
  session_perfect_clears: sessionPerfectClears(dir),

  /** WHERE in the round each Perfect Clear landed, with the per-round count check that licenses
   *  publishing it at all. See `perfectClearTiming`. */
  perfect_clear_timing: perfectClearTiming(),

  /** Two per-T-spin BOARD-STATE techniques — neither is an opener, both are the same quarantined
   *  tier as the slot geometry above. See `donationMetric` / `stmbCaveMetric` for the controls each
   *  ships with, and `donation.caveat` for the bound the oracle's garbage hole columns put on them. */
  donation: donationMetric(),
  stmb_cave: stmbCaveMetric(),
};
}

/** Exactly the bytes the artifact file holds, so the CLI and the reproducibility test compare the
 *  same thing. Trailing newline included: the committed files have one, and a test that stringified
 *  without it would report drift on every session forever. */
export const serialise = (data: ReturnType<typeof build>) => JSON.stringify(data, null, 2) + '\n';

if (import.meta.main) {
  // `--out <path>` is REQUIRED and the replays come from REPLAY_DIR, for the reason spelled out in
  // emit-forecast-facts.ts: a positional default would write the artifact next to the CODE, where
  // no session reads it and where a wrong invocation looks like a success.
  //
  // argv is read HERE and not at module scope: this file is imported by openers.test.ts, and a
  // top-level throw on a missing argument would make the whole suite fail to load — the same trap
  // run-openers.ts documents.
  const argv = process.argv.slice(2);
  const oi = argv.indexOf('--out');
  if (oi === -1 || !argv[oi + 1])
    throw new Error('--out <path> is required, e.g.\n'
      + '  REPLAY_DIR=sessions/2026-08-09 bun pipeline/sim/emit-opener-facts.ts \\\n'
      + '    --out sessions/2026-08-09/sim/opener-facts.json');
  const out = build(replayDir());
  writeFileSync(argv[oi + 1]!, serialise(out));
  console.log(`wrote ${argv[oi + 1]}  (session ${out.session})\n`);

  console.log(`first bag: ${out.first_bag.clean} clean of ${out.first_bag.rounds} rounds`);
  for (const p of out.first_bag.players)
    console.log(`  ${p.user.padEnd(10)} n=${String(p.clean_first_bags).padStart(3)}  `
      + NAME_SETS.map(s => `${s.key} min=${(p.nearest as any)[s.key].min_cells} `
        + `<=${out.near_cells}:${(p.nearest as any)[s.key].within_threshold}`).join('  '));
  console.log(`\nordering (verified prefix), window ${out.window_pieces} pieces:`);
  for (const p of out.ordering.players)
    console.log(`  ${p.user.padEnd(10)} both=${String(p.rounds_with_both).padStart(3)}  `
      + `C-Spin order (T then D)=${String(p.cspin_order).padStart(3)}  `
      + `DT order (D then T)=${String(p.dt_order).padStart(3)}  `
      + `first Triple lock min/med/max=${p.first_triple_lock.min}/${p.first_triple_lock.median}/${p.first_triple_lock.max}`);
  console.log('\nslot geometry vs the wiki C-Spin window (the control is the spread across lines):');
  for (const r of out.slot_geometry.rows)
    console.log(`  ${r.lines}-line  n=${String(r.n).padStart(4)}  matched=${String(r.matched).padStart(4)}  `
      + `${r.share_x1000 === null ? 'n/a' : (r.share_x1000 / 10).toFixed(1) + '%'}`);
  console.log(`\nnamed openers (${out.named_openers.boards.total} clean opening boards, `
    + `by locks ${JSON.stringify(out.named_openers.boards.by_locks)}):`);
  for (const o of out.named_openers.openers) {
    const src = o.pages;
    console.log(`  ${o.key.padEnd(14)} drawn at ${JSON.stringify(o.drawn_at_locks)} `
      + `(wiki ${src.wiki_fields}, catalogue ${src.catalogue_clean}/${src.catalogue_named} clean)`);
    for (const p of o.players)
      console.log(`      ${p.user.padEnd(10)} n=${String(p.boards_scored).padStart(3)}  `
        + `exact=${String(p.exact).padStart(3)} (baseline ${p.baseline.exact})  min=${p.min_cells}  `
        + `<=${out.near_cells}:${p.within_threshold} (baseline ${p.baseline.within_threshold})  `
        + `delivered=${p.matched_and_delivered}/${p.matched_rounds}`);
  }
  console.log('\nPCO ceiling (verified source): '
    + (out.session_perfect_clears
       ? JSON.stringify(out.session_perfect_clears.per_player) + ' perfect clears in the session'
       : 'facts.json not present — not known here'));
  const dk = out.donation.check;
  console.log(`\ndonation / STMB cave (verified prefix; reconstruction ${dk.reconstruction_agreed}/`
    + `${dk.tspin_clears}, disagreements ${dk.reconstruction_disagreed}):`);
  for (const p of out.donation.players)
    console.log(`  ${p.user.padEnd(10)} n=${String(p.tspin_clears_scored).padStart(4)}  `
      + `donations=${String(p.donations).padStart(3)} (garbage well ${p.garbage_derived_well}, `
      + `self-built ${p.self_built_well}; natural ${p.natural}, b2b-breaking ${p.b2b_breaking})`);
  for (const p of out.stmb_cave.players)
    console.log(`  ${p.user.padEnd(10)} TSD=${String(p.tspin_doubles_scored).padStart(4)}  `
      + `cave >=${out.stmb_cave.min_width} wide=${String(p.width_ge_3).padStart(3)}  `
      + `of which >=2 deep=${p.min_depth_ge_2}`);
  console.log(`  control: the same >=${out.stmb_cave.min_width}-wide gap under a Triple — `
    + `${out.stmb_cave.triple_control.width_ge_3} of ${out.stmb_cave.triple_control.tspin_triples_scored}`
    + `   min-depth hist ${JSON.stringify(out.stmb_cave.min_depth_histogram)}`);
  console.log(`\nordering control: ${out.ordering_class.openers} openers share the `
    + `Triple-before-Double signature (${out.ordering_class.name})`);
  console.log('\nnot report-eligible because:');
  for (const w of out.not_eligible_because) console.log(`  - ${w}`);
}
