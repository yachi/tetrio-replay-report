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
 * FIVE METRICS, each paired with the control that says what it is NOT.
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
  console.log(`\nordering control: ${out.ordering_class.openers} openers share the `
    + `Triple-before-Double signature (${out.ordering_class.name})`);
  console.log('\nnot report-eligible because:');
  for (const w of out.not_eligible_because) console.log(`  - ${w}`);
}
