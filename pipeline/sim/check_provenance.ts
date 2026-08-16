/**
 * Gate: a `SimResult`'s provenance map must be ADMISSIBLE against its own boards and locks.
 *
 *     bun pipeline/sim/check_provenance.ts --selftest        # plant one mutant per rule, require catches
 *     bun pipeline/sim/check_provenance.ts                   # every sessions/* holding .ttrm
 *     bun pipeline/sim/check_provenance.ts sessions/2026-08-14
 *
 * `provSnaps[k][row][col]` claims WHO put that cell there: `null` = empty, `-1` = garbage, and
 * `>= 0` = the index of the lock that placed it. Everything clause 2 (`floorOrigin`) and the roof
 * search (`forecastMetric`) decide is read out of that number — and until this file existed nothing
 * asked whether the number could be true. It is checkable without a second engine, without frames
 * and without the replay: **a cell placed by lock p must carry lock p's own piece letter.** Six
 * further rules fall out of the same walk and cost nothing; each is named and each has a planted
 * mutant below, because a rule no mutant can kill is decorative.
 *
 * ── WHY IT EXISTS ────────────────────────────────────────────────────────────────────────────────
 * `tools/triangle-oracle/oracle-forecast.mjs` rolled its own provenance by mirroring the engine's
 * shift/splice with a force-align fallback. `pipeline/sim/oracle-source.ts` replaced that a day
 * later (2026-08-12, `a53a952`) with exact cell-identity provenance — a WeakMap tag on the engine's
 * own stable cell objects — and the tool was never moved onto it. Measured over the six-session
 * corpus on 2026-08-16, by this file's `letter` rule, against the tool AS IT THEN STOOD:
 *
 *   | source                                       | roof cells | placed cells        |
 *   |----------------------------------------------|------------|---------------------|
 *   | oracle-forecast.mjs's own reconstruction     | **544 / 2024 (26.9%)** | 1 191 905 / 3 811 813 (31.3%) |
 *   | pipeline/sim/oracle-source.ts (published)    | 0 / 4202   | 0 / 1 848 048       |
 *   | pipeline/sim/sim.ts hand-port (published)    | 0 / 1988   | 0 / 1 601 735       |
 *
 * That defect produced a fourth `forecast_lineclear` candidate (2026-08-14 yachi `2026-08-14-10` r2
 * lock 19) whose roof it attributed to lock 12 — a **T** — for a cell the board itself draws as
 * **S**. Under either published source the roof is lock 10, an S, availability FELL 2 -> 1, and the
 * event is `reactive`.
 *
 * **The 26.9% column has no live control any more, and that is deliberate**: the reconstruction it
 * measures was DELETED in the same change (`oracle-forecast.mjs` now takes its boards from
 * `oracle-source.ts`), so there is nothing left in the repo for this gate to fire on. The standing
 * control is the planted mutant named `the 2026-08-11 defect` in `selftest` below, which is that
 * failure in miniature. Re-running the table needs `git show` of the pre-2026-08-16 file plus
 * `@haelp/teto` from npm, which no CI job installs.
 *
 * ── WHY A MODULE + CLI + `bun test`, AND NOT A PYTHON CHECKER ────────────────────────────────────
 * The subject is a `SimResult`: TypeScript objects held in memory by the same process that builds
 * them. A Python gate would have to serialise 28 million cells per run and would then be gating its
 * own serialiser as much as the thing under test. The consumers this protects (`forecast.ts`'s roof
 * search, `floorOrigin`) are TS and already run under `bun test`.
 *
 * It is a module first so `provenance.test.ts` can drive it inside CI's existing `bun test` step
 * with no workflow entry to forget — the manual-only-gate class this repo has been bitten by twice
 * (`dual-backed.json`, `equiv.py`'s coverage table). The CLI exists so the mutants are runnable and
 * nameable in isolation, and so a single session can be swept while working on it.
 *
 * ── WHAT `letter` CANNOT SEE, AND WHY THE WORDING IS "IMPOSSIBLE PLACER" ─────────────────────────
 * The rule compares a placer's piece against the letter the board draws, so it separates the seven
 * letters and nothing finer. A cell misattributed to a DIFFERENT lock of the SAME letter is
 * admissible under every rule here and always will be — with seven piece types, roughly 1 in 7 of a
 * uniformly wrong attribution is invisible to it. That is why every figure this gate produces is
 * worded as "no placer is IMPOSSIBLE", never as "every placer is correct": `0 of 4202` is an upper
 * bound on the defect it was written for, not a proof of the map. Deciding same-letter attribution
 * needs cell identity — which is exactly what `oracle-source.ts` builds and what the deleted
 * reconstruction did not have — so the honest check on it is that source's own WeakMap tagging, not
 * a rule in this file. Do not upgrade the wording anywhere it appears (here, `provenance.test.ts`,
 * ROADMAP) without building that second decision procedure first.
 */
import { existsSync, readdirSync } from 'node:fs';
import { GARBAGE, H, type SimResult } from './sim.ts';
import { BOARD_WIDTH } from './vendor/core/types.ts';

export type RuleName =
  | 'letter'            // a placer's piece must be the letter the board draws
  | 'out-of-range'      // a placer index must name a lock that exists
  | 'future-placer'     // ...one that had already happened, modulo same-tick locks
  | 'prov-on-empty'     // an empty cell has no placer
  | 'null-on-filled'    // a filled cell has one
  | 'placer-on-garbage' // garbage is `-1`, never a lock index
  | 'garbage-on-placed';// and `-1` is garbage, never a placed cell

export interface Violation {
  rule: RuleName; lock: number; row: number; col: number;
  prov: number | null; letter: string | null; placer: string | null;
}

/**
 * Every way `r.provSnaps` can contradict `r.boards` and `r.locks`, in one walk.
 *
 * `stop` bounds the report so a systematically broken reconstruction does not print a million
 * lines; the COUNT is not bounded, so a caller can still say how bad it is.
 */
export function provenanceViolations(r: SimResult, stop = 40): { hits: Violation[]; counts: Record<RuleName, number>; cells: number; placed: number } {
  const counts = {
    'letter': 0, 'out-of-range': 0, 'future-placer': 0, 'prov-on-empty': 0,
    'null-on-filled': 0, 'placer-on-garbage': 0, 'garbage-on-placed': 0,
  } as Record<RuleName, number>;
  const hits: Violation[] = [];
  // `cells` is every grid slot walked; `placed` is the subset carrying a placer index, which is the
  // only honest denominator for `letter` — a rate over empty cells is a rate over rows of nothing.
  let cells = 0, placed = 0;
  const add = (rule: RuleName, lock: number, row: number, col: number, prov: number | null, letter: string | null) => {
    counts[rule]++;
    if (hits.length < stop)
      hits.push({ rule, lock, row, col, prov, letter, placer: prov !== null && prov >= 0 ? (r.locks[prov]?.piece ?? null) : null });
  };

  for (let k = 0; k < r.provSnaps.length; k++) {
    const snap = r.provSnaps[k], bd = r.boards[k];
    if (!snap || !bd) continue;
    for (let row = 0; row < H; row++) for (let col = 0; col < BOARD_WIDTH; col++) {
      const p = snap[row]?.[col] ?? null;
      const L = (bd[row]?.[col] ?? null) as string | null;
      cells++;
      if (L === null) { if (p !== null) add('prov-on-empty', k, row, col, p, L); continue; }
      if (p === null) { add('null-on-filled', k, row, col, p, L); continue; }
      if (L === (GARBAGE as unknown as string)) { if (p !== -1) add('placer-on-garbage', k, row, col, p, L); continue; }
      if (p === -1) { add('garbage-on-placed', k, row, col, p, L); continue; }
      placed++;
      const placer = r.locks[p];
      if (!placer) { add('out-of-range', k, row, col, p, L); continue; }
      // A placer index above the snapshot index is a lock that had not happened yet — EXCEPT when
      // the two locks share a frame. `oracle-source.ts` snapshots once per tick (`while
      // (boards.length < locks.length)`), so when two pieces lock in one tick the earlier one's
      // snapshot is taken after the later one has already tagged its cells. Measured over the
      // six-session corpus: 16 cells, all of them in 4 rounds where `locks[k].frame ===
      // locks[k+1].frame`, and they reach 0 of 4202 forecast records. Written as the mechanism
      // rather than as a list of four rounds so a seventh session needs no edit — and the escape
      // hatch has teeth in the other direction: delete it and the corpus fails this gate.
      if (p > k && placer.frame !== r.locks[k]?.frame) { add('future-placer', k, row, col, p, L); continue; }
      if (placer.piece !== L) add('letter', k, row, col, p, L);
    }
  }
  return { hits, counts, cells, placed };
}

/** The roof cells `forecastMetric` actually reads, and whether each names an admissible placer. */
export function roofAdmissibility(r: SimResult): { roof: number; bad: number; hits: Violation[] } {
  const hits: Violation[] = [];
  let roof = 0;
  for (let k = 1; k < r.locks.length; k++) {
    const lk = r.locks[k]!;
    if (lk.spin === 'none' || lk.cleared === 0) continue;
    const prev = r.provSnaps[k - 1];
    if (!prev) continue;
    const cellsAbove: { row: number; col: number; p: number }[] = [];
    for (const c of lk.cells) {
      const above = c.row - 1;
      if (above < 0 || above >= H) continue;
      const p = prev[above]?.[c.col];
      if (p === null || p === undefined) continue;
      cellsAbove.push({ row: above, col: c.col, p });
    }
    if (cellsAbove.length === 0) continue;         // untucked — forecastMetric drops it
    for (const { row, col, p } of cellsAbove) {
      if (p < 0) continue;                          // garbage sentinel: no piece to check
      roof++;
      const L = (r.boards[k - 1]?.[row]?.[col] ?? null) as string | null;
      if (L === null || L === (GARBAGE as unknown as string)) continue;
      const placer = r.locks[p];
      if (placer && placer.piece !== L)
        hits.push({ rule: 'letter', lock: k, row, col, prov: p, letter: L, placer: placer.piece });
    }
  }
  return { roof, bad: hits.length, hits };
}

// ── the fixture the mutants are planted into ─────────────────────────────────────────────────────

const blankGrid = <T,>(v: T): T[][] => Array.from({ length: H }, () => new Array(BOARD_WIDTH).fill(v));

/**
 * A three-lock round, built by hand: an O at the bottom-left, an S beside it, a T that tucks under
 * the S — the shape the whole clause-2 argument runs on. It is deliberately NOT produced by any
 * engine, so a mutant that breaks an engine cannot also fix this fixture.
 */
export function fixture(): SimResult {
  const boards = [blankGrid<string | null>(null), blankGrid<string | null>(null), blankGrid<string | null>(null)];
  const prov = [blankGrid<number | null>(null), blankGrid<number | null>(null), blankGrid<number | null>(null)];
  const paint = (from: number, cells: { row: number; col: number }[], letter: string, lock: number) => {
    for (let k = from; k < 3; k++) for (const c of cells) { boards[k]![c.row]![c.col] = letter; prov[k]![c.row]![c.col] = lock; }
  };
  const oCells = [{ row: 39, col: 0 }, { row: 39, col: 1 }, { row: 38, col: 0 }, { row: 38, col: 1 }];
  const sCells = [{ row: 38, col: 2 }, { row: 38, col: 3 }, { row: 37, col: 3 }, { row: 37, col: 4 }];
  const tCells = [{ row: 39, col: 3 }, { row: 39, col: 2 }, { row: 39, col: 4 }, { row: 38, col: 4 }];
  paint(0, oCells, 'O', 0);
  paint(1, sCells, 'S', 1);
  paint(2, tCells, 'T', 2);
  // two garbage rows under everything would move the stack; instead a single garbage cell in a
  // column nothing else uses, so the garbage rules have something to be right about.
  for (let k = 0; k < 3; k++) { boards[k]![39]![9] = GARBAGE as unknown as string; prov[k]![39]![9] = -1; }
  return {
    lines: 0, placed: 3, holds: 0, clears: {}, topbtb: 0, topcombo: 0,
    garbage: { sent: 0, received: 0, cleared: 0, attack: 0 },
    boards: boards as unknown as SimResult['boards'],
    records: [], events: [],
    locks: [
      { frame: 10, piece: 'O' as any, cells: oCells, cleared: 0, spin: 'none', allclear: false },
      { frame: 20, piece: 'S' as any, cells: sCells, cleared: 0, spin: 'none', allclear: false },
      { frame: 30, piece: 'T' as any, cells: tCells, cleared: 1, spin: 'full', allclear: false },
    ],
    garbageEvents: [], provSnaps: prov, topout: false,
  };
}

const clone = (r: SimResult): SimResult => ({
  ...r,
  boards: r.boards.map(b => b.map(row => [...row])) as SimResult['boards'],
  provSnaps: r.provSnaps.map(s => s.map(row => [...row])),
  locks: r.locks.map(l => ({ ...l, cells: l.cells.map(c => ({ ...c })) })),
});

// ── selftest ─────────────────────────────────────────────────────────────────────────────────────

/**
 * One planted mutant PER RULE, enumerated by name.
 *
 * Derived mutants would let a rule ship with nothing proving it fires
 * (`check_opener_section.py:505-506` makes the same point). The positive control comes first: a
 * clean fixture must report NOTHING, because a checker that fails on everything catches every
 * mutant below and gates nothing at all.
 */
export async function selftest(log: (s: string) => void = console.log): Promise<number> {
  // `via` names WHICH detector has to fire, not merely that something did. Accepting either would
  // let the roof reader rot behind the full-grid walk, which is the one place a narrowing would not
  // show up — the roof cells are the subset `forecastMetric` reads.
  type Via = 'full' | 'roof' | null;
  const cases: [string, RuleName | null, Via, (r: SimResult) => void][] = [
    ['control: the clean fixture is admissible', null, null, () => {}],
    ['a placer names a lock whose piece is a different letter (the 2026-08-11 defect)', 'letter', 'full',
      r => { r.provSnaps[2]![37]![3] = 2; }],                        // the S roof cell blamed on the T
    ['a placer names a lock index past the end of `locks`', 'out-of-range', 'full',
      r => { r.provSnaps[2]![37]![3] = 9; }],
    ['a placer names a lock that had not happened at that snapshot', 'future-placer', 'full',
      r => { r.provSnaps[1]![38]![2] = 2; }],
    ['an empty cell carries a placer', 'prov-on-empty', 'full',
      r => { r.provSnaps[2]![20]![5] = 1; }],
    ['a filled cell carries none', 'null-on-filled', 'full',
      r => { r.provSnaps[2]![37]![3] = null; }],
    ['a garbage cell is attributed to a lock', 'placer-on-garbage', 'full',
      r => { r.provSnaps[2]![39]![9] = 2; }],
    ['a placed cell carries the garbage sentinel', 'garbage-on-placed', 'full',
      r => { r.provSnaps[2]![37]![3] = -1; }],
    // The escape hatch is not a licence to be wrong: a genuine same-frame pair is admitted, and
    // that admission is what makes the corpus's 16 cells pass. Its own mutant is the corpus (see
    // the comment on the rule) — here it only has to not fire.
    ['control: a same-tick placer is admitted', null, null,
      r => { r.locks[2]!.frame = r.locks[1]!.frame; r.provSnaps[1]![38]![2] = 2; r.boards[1]![38]![2] = 'T'; }],
    // The roof entry point, on the snapshot the T actually reads (k-1 = 1) and at a cell directly
    // above one of the T's own — the exact read that misnamed candidate D's roof. Requiring `roof`
    // rather than "either detector" is what makes this case worth having: the first version planted
    // at (37,3), which IS an inadmissible cell but is NOT above the T, so the full-grid walk caught
    // it and the roof reader never saw it. The two sets really are different.
    ['the ROOF reader catches a wrong-letter placer on the snapshot the T reads', 'letter', 'roof',
      r => { r.provSnaps[1]![38]![3] = 0; }],   // the S at (38,3) — above the T's (39,3) — blamed on the O
  ];

  let ok = true, planted = 0;
  for (const [name, rule, via, mutate] of cases) {
    const r = clone(fixture());
    mutate(r);
    const full = provenanceViolations(r);
    const roof = roofAdmissibility(r);
    const fired = rule === null ? (full.hits.length === 0 && roof.bad === 0)
      : via === 'roof' ? roof.bad > 0 : full.counts[rule] > 0;
    if (rule !== null) planted++;
    ok &&= fired;
    log(`  ${fired ? 'ok ' : 'BAD'} ${name}`);
  }
  // The fixture must be a real workout for the roof reader, or every `letter` mutant above is
  // being caught by the full-grid walk alone and the roof entry point is untested.
  const base = roofAdmissibility(fixture());
  const covers = base.roof > 0 && base.bad === 0;
  ok &&= covers;
  log(`  ${covers ? 'ok ' : 'BAD'} control: the fixture exercises the roof reader (${base.roof} roof cells, ${base.bad} bad)`);

  // ── the CENSUS, which the seven rules above say nothing about ──────────────────────────────────
  //
  // Every mutant above breaks a provenance map that WAS built. None of them can reach the other
  // failure mode: a builder that throws, whose case then never enters the sweep at all. A full
  // die-off used to print `ok ... 0 placed cells over 0 rounds` and exit 0; a PARTIAL one printed a
  // smaller, still-clean census with nothing naming what fell out — and the corpus test's bounds
  // (`rounds > 0`, `placed > 1M`) only ever caught the extreme. These three cases plant the
  // die-offs directly, over synthetic cases and builders, so they cost no disk and no engine.
  const dead = () => { throw new Error('planted: the builder died'); };
  const censusCases: [string, boolean, (c: number) => SimResult][] = [
    ['control: a census that builds every case is clean', false, () => clone(fixture())],
    ['a builder that throws on EVERY case fails instead of reporting a clean sweep of nothing', true, dead],
    ['a builder that throws on SOME cases fails rather than shrinking its own denominator', true,
      (c: number) => (c % 2 ? dead() : clone(fixture()))],
  ];
  for (const [name, mustFail, mk] of censusCases) {
    const [res] = await sweep(['planted'], ['planted'], {
      builders: { planted: mk }, load: () => [1, 2, 3, 4],
    });
    const why = sweepFailures(res!);
    const fired = mustFail ? why.length > 0 : why.length === 0;
    ok &&= fired;
    planted += mustFail ? 1 : 0;
    log(`  ${fired ? 'ok ' : 'BAD'} ${name} (${res!.rounds} built, ${res!.skipped} skipped)`);
  }

  log(`${ok ? 'ok ' : 'FAIL'} selftest ${planted} planted mutants, ${ok ? 'all caught' : 'SOME MISSED'}`);
  return ok ? 0 : 1;
}

// ── corpus sweep ─────────────────────────────────────────────────────────────────────────────────

export interface SourceResult {
  source: string; rounds: number; cells: number; placed: number; roof: number; roofBad: number;
  counts: Record<RuleName, number>; hits: Violation[];
  /** cases whose builder threw, so this source produced no provenance map for them at all */
  skipped: number; skips: { case: string; error: string }[];
}

/** Every `sessions/*` holding a `.ttrm`. Globbed, never listed — a seventh session needs no edit. */
export function sessionDirs(root: string): string[] {
  const base = `${root}/sessions`;
  if (!existsSync(base)) return [];
  return readdirSync(base)
    .map(d => `${base}/${d}`)
    .filter(d => existsSync(d) && readdirSync(d).some(f => f.endsWith('.ttrm')))
    .sort();
}

/** `builders`/`load` are injection points for the selftest only; production passes neither. */
export async function sweep(
  dirs: string[], sources: string[],
  opts: { builders?: Record<string, (c: any) => SimResult>; load?: (dir: string) => any[] } = {},
): Promise<SourceResult[]> {
  const vp = await import('./verified-prefix.ts');
  const build: Record<string, (c: any) => SimResult> = opts.builders ?? {
    'oracle-source.ts (published)': vp.runCaseOracle,
    'sim.ts hand-port (published)': vp.runCase,
  };
  const loadCases = opts.load ?? vp.loadCases;
  const out: SourceResult[] = [];
  for (const source of sources) {
    const mk = build[source]!;
    const acc: SourceResult = {
      source, rounds: 0, cells: 0, placed: 0, roof: 0, roofBad: 0, hits: [], skipped: 0, skips: [],
      counts: { 'letter': 0, 'out-of-range': 0, 'future-placer': 0, 'prov-on-empty': 0, 'null-on-filled': 0, 'placer-on-garbage': 0, 'garbage-on-placed': 0 },
    };
    for (const dir of dirs) for (const c of loadCases(dir)) {
      let r: SimResult;
      // A builder that throws produces no provenance map, so this case is NOT swept — it is
      // missing from the census. It used to be a bare `continue`, which is the same shape as the
      // `?? 0` that published "no perfect clears" for five sessions: the denominator shrinks and
      // the printed line reads exactly like a clean sweep. `codegen.py:76-78`'s rule is to NAME
      // what was left out; `sweepFailures` then refuses to call the run clean at all.
      try { r = mk(c); } catch (e) {
        acc.skipped++;
        if (acc.skips.length < 20)
          acc.skips.push({ case: `${c?.file ?? '?'} r${c?.round ?? '?'} ${c?.user ?? '?'}`, error: (e as Error).message });
        continue;
      }
      acc.rounds++;
      const v = provenanceViolations(r);
      const roof = roofAdmissibility(r);
      acc.cells += v.cells; acc.placed += v.placed; acc.roof += roof.roof; acc.roofBad += roof.bad;
      for (const k of Object.keys(acc.counts) as RuleName[]) acc.counts[k] += v.counts[k];
      for (const h of [...v.hits, ...roof.hits]) if (acc.hits.length < 20) acc.hits.push(h);
    }
    out.push(acc);
  }
  return out;
}

/**
 * Everything that makes a swept source a failure, named — the one place the CLI, the test and the
 * selftest agree on what "clean" means.
 *
 * The skip floor is ZERO, not a tolerance: measured 2026-08-16 over the six-session corpus, both
 * published sources build all 760 rounds, 0 throws. So any skip is a regression in the builder, and
 * a gate that tolerated a few would be picking its own denominator.
 */
export function sweepFailures(res: SourceResult): string[] {
  const out: string[] = [];
  const total = Object.values(res.counts).reduce((a, b) => a + b, 0);
  if (total) out.push(`${total} inadmissible cells of ${res.placed} placed`);
  if (res.roofBad) out.push(`${res.roofBad} of ${res.roof} roof cells inadmissible`);
  // A sweep of nothing reports no violations, which is the vacuous-clean shape the CLI's directory
  // guards cover for an empty glob and this covers for a full die-off.
  if (res.rounds === 0) out.push('0 rounds were built — a sweep over nothing reports no violations');
  if (res.skipped)
    out.push(`${res.skipped} case(s) were dropped because the builder threw, so the census covers `
      + `${res.rounds} of ${res.rounds + res.skipped} rounds: `
      + res.skips.map(s => `${s.case} (${s.error})`).join('; '));
  return out;
}

// ── CLI ──────────────────────────────────────────────────────────────────────────────────────────

if (import.meta.main) {
  const argv = process.argv.slice(2);
  const root = `${import.meta.dir}/../..`;

  if (argv.includes('--selftest')) process.exit(await selftest());

  const named = argv.filter(a => !a.startsWith('--'));
  const dirs = named.length ? named : sessionDirs(root);
  // Absence is a failure, never a skip: an empty glob, or a named directory with no replays in it,
  // reads exactly like a clean sweep — 0 violations over 0 cells, printed as `ok `.
  if (dirs.length === 0) {
    console.error('FAIL no sessions/* directory holds a .ttrm — the sweep would report 0 violations over 0 cells');
    process.exit(1);
  }
  for (const d of dirs) {
    if (!existsSync(d) || !readdirSync(d).some(f => f.endsWith('.ttrm'))) {
      console.error(`FAIL ${d} holds no .ttrm replay — a sweep over it would be vacuously clean`);
      process.exit(1);
    }
  }

  let bad = 0;
  for (const res of await sweep(dirs, ['oracle-source.ts (published)', 'sim.ts hand-port (published)'])) {
    const why = sweepFailures(res);
    if (why.length) {
      bad = 1;
      for (const h of res.hits)
        console.error(`FAIL ${res.source}: ${h.rule} at lock ${h.lock} r${h.row}c${h.col} — prov ${h.prov} (${h.placer}) on a ${h.letter}`);
      for (const w of why) console.error(`FAIL ${res.source}: ${w}`);
    } else {
      // `0 skipped` is printed on a CLEAN run too, deliberately: a census that says how many cases
      // it could not build is the only way a later partial die-off reads as a change.
      console.log(`  ok  ${res.source}: ${res.placed} placed cells over ${res.rounds} rounds (${res.cells} walked), `
        + `${res.roof} roof cells, 0 skipped, every placer admissible`);
    }
  }

  process.exit(bad);
}
