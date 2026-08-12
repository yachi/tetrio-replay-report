/**
 * Emit the C-Spin and DT Cannon metrics as DATA, one artifact per session.
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
 * THREE METRICS, each paired with the control that says what it is NOT.
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
 * Rates are integers scaled x1000, matching report/facts.json and forecast-facts.json.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex, replayDir } from './verified-prefix.ts';
import { H } from './sim.ts';
import { BOARD_WIDTH } from './vendor/core/types.ts';
import { loadCatalogue, prepare, occGrid, rowsFromBoard, exactMatches, nearest, NAME_SETS }
  from '../openers/match.ts';

/** Three bags. The wiki's C-Spin follow-up is "a Double within about three bags of the Triple", and
 *  a window has to be a number: 21 pieces is that phrase read literally. It is emitted rather than
 *  buried so the section prints the window it actually used, and so widening it is a data change. */
const WINDOW_PIECES = 21;

/** Distance at which two 28-cell boards stop being "the same opener, played slightly differently".
 *  Inherited from `openers/README.md`, where it is what separates the exact/variant bands from the
 *  5-8 band that every real board in this corpus lands in. */
const NEAR_CELLS = 4;

const cat = loadCatalogue();
const prepared = prepare(cat.pages);
const catNames: string[] = [...new Set(cat.pages.map(p => p.name))];

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
interface Round { user: string; verified: number; spinsVerified: { i: number; cleared: number }[];
                  spinsAll: { i: number; cleared: number }[] }

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
  rounds.push({ user: c.user, verified: v, spinsAll,
                spinsVerified: spinsAll.filter(x => x.i <= v) });

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

  // first bag: seven locks, no clear, no garbage, all inside the verified prefix
  if (v < 6) continue;
  let clean = true;
  for (let i = 0; i <= 6; i++) if (r.locks[i]!.cleared > 0) clean = false;
  for (const g of r.garbageEvents) if (g.lockIndex <= 6) clean = false;
  if (!clean) continue;
  const rows = rowsFromBoard(r.boards[6]! as (string | null)[][]);
  if (!rows) continue;
  bags.push({ user: c.user, grid: occGrid(rows) });
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
  console.log('\nnot report-eligible because:');
  for (const w of out.not_eligible_because) console.log(`  - ${w}`);
}
