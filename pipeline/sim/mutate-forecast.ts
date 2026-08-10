/**
 * Mutation harness for the forecast instrument.
 *
 * The doc claims "2/4 killed -> 3/4, two still survive". That was recorded by hand.
 * This measures it: patch forecast.ts, run the suite, restore, report.
 *
 * A surviving mutant is either a missing test or a proven-equivalent mutant.
 * "Probably equivalent" is not a status this project accepts.
 */
import { readFileSync, writeFileSync, copyFileSync, unlinkSync } from 'node:fs';
import { execSync } from 'node:child_process';

const SRC = './forecast.ts';
const BAK = './forecast.ts.mutbak';

const GUARD = `if (d.row === cur.row && rot && detectTSpin(board, d, true, kick) !== 'none') {`;
//                occurrence 1 = bestTspinLines, occurrence 2 = tspinAvailable

/**
 * What the sweep asserts about a mutant, not what it observes. `killed` is the default and is
 * what every entry below expects; `survived` declares a CONTROL — a semantics-preserving edit
 * that the suite must NOT be able to detect, so a control that starts dying is as much a failure
 * as a real mutant that starts surviving.
 *
 * The gate compares observed against expected. That is the only formulation that can hold both
 * kinds at once: a blanket "any survivor fails" cannot express a control, and a blanket "count
 * the kills" cannot express that a control dying means the harness has stopped controlling for
 * anything. It also gives STALE somewhere to sit — "never ran" matches no expectation at all.
 *
 * NOTE FOR ANYONE ADDING A CONTROL. `pipeline/sim/README.md` currently states that this harness
 * "validates itself with control mutants: three semantics-preserving edits must survive and a
 * poison mutant (spawn column 3→9) must die". No such entry has ever existed in this file — not
 * at 0dde1d8, the commit that wrote that sentence (11 entries, no control field, no spawn
 * mutant), and not now. Every entry below is a real defect injection and all of them die. The
 * README sentence describes a regime that was never built here, which is why its companion
 * claim "a sweep where everything dies is a syntax error" would condemn every honest run this
 * harness has ever produced. The mechanism is now here if someone wants to build it for real.
 */
type Verdict = 'killed' | 'survived';

interface Mutant {
  name: string; note: string; find: string; nth: number; repl: string;
  /** defaults to `'killed'`; set `'survived'` to declare a control */
  expect?: Verdict;
}

const MUTANTS: Mutant[] = [
  // --- bestTspinLines ---
  { name: 'best/no-rotation', note: 'accepts landings whose last action was not a rotation',
    find: GUARD, nth: 1, repl: `if (d.row === cur.row && detectTSpin(board, d, true, kick) !== 'none') {` },
  { name: 'best/no-spin-test', note: 'any line-clearing T landing counts, spin-shaped or not',
    find: GUARD, nth: 1, repl: `if (d.row === cur.row && rot) {` },
  { name: 'best/no-landing-test', note: 'counts positions the piece floats above',
    find: GUARD, nth: 1, repl: `if (rot && detectTSpin(board, d, true, kick) !== 'none') {` },
  { name: 'best/mini-counts-as-full', note: 'ignores the mini/full distinction',
    find: GUARD, nth: 1, repl: `if (d.row === cur.row && rot && detectTSpin(board, d, true, kick) !== 'nope') {` },

  // --- tspinAvailable (a one-liner over bestTspinLines since the duplicate BFS was deleted) ---
  { name: 'avail/threshold-off-by-one', note: 'a board with no T-spin reports one available',
    find: `  return bestTspinLines(board) > 0;`, nth: 1,
    repl: `  return bestTspinLines(board) >= 0;` },
  { name: 'avail/inverted', note: 'availability answers the opposite question',
    find: `  return bestTspinLines(board) > 0;`, nth: 1,
    repl: `  return !(bestTspinLines(board) > 0);` },
  { name: 'avail/requires-multiline', note: 'single-line T-spins do not count as available',
    find: `  return bestTspinLines(board) > 0;`, nth: 1,
    repl: `  return bestTspinLines(board) > 1;` },

  // --- the line-clear requirement now lives only in bestTspinLines ---
  { name: 'best/no-lineclear-req', note: 'a T-spin that clears nothing counts',
    find: `      if (lines > best) {
        best = lines;`, nth: 1,
    repl: `      if (lines >= best) {
        best = Math.max(lines, 1);` },

  // --- forecastMetric classifier ---
  { name: 'metric/roof-oldest-builder', note: 'roof attributed to the earliest placer, not the latest',
    find: `const j = placers.length ? Math.max(...placers) : -1;`, nth: 1,
    repl: `const j = placers.length ? Math.min(...placers) : -1;` },
  { name: 'metric/improve-inverted', note: 'the improvement test answers the opposite question',
    find: `      ? availAtSpin > availAtRoof`, nth: 1,
    repl: `      ? availAtSpin < availAtRoof` },
  { name: 'metric/improve-nonstrict', note: 'any change counts as an improvement',
    find: `      ? availAtSpin > availAtRoof`, nth: 1,
    repl: `      ? availAtSpin >= availAtRoof` },
  { name: 'metric/strict-disabled', note: 'silently falls back to the loose co-occurrence rule',
    find: `    const improved = (strict && determinable)`, nth: 1,
    repl: `    const improved = (false && determinable)` },

  // --- the mechanism localisation: which STEP raised the availability, and which of that step's
  //     three edits did it. These are the mutants that matter most: the whole 2026-08-02
  //     correction is that co-occurrence was standing in for causation, so a harness that cannot
  //     kill a reversion to co-occurrence would not have caught the original defect either.
  { name: 'metric/lineclear-co-occurrence', note: 'THE original defect: a clear in the window counts',
    find: `      : loc!.mechanism === 'line-clear' ? 'forecast_lineclear'`, nth: 1,
    repl: `      : clearBetween ? 'forecast_lineclear'` },
  { name: 'metric/garbage-step-co-occurrence', note: 'garbage anywhere in the window counts',
    find: `      : loc!.mechanism === 'garbage' ? 'forecast_garbage'`, nth: 1,
    repl: `      : garbageBetween ? 'forecast_garbage'` },
  { name: 'metric/localise-no-straddle', note: 'any clear at the step FORMED the slot',
    find: `    if (clearedRows.some(cr => cr > Math.min(...ps) && cr < Math.max(...ps)))`, nth: 1,
    repl: `    if (clearedRows.length > 0)` },
  { name: 'metric/localise-straddle-inverted', note: 'the slot-spanning test answers the opposite',
    find: `    if (clearedRows.some(cr => cr > Math.min(...ps) && cr < Math.max(...ps)))`, nth: 1,
    repl: `    if (!clearedRows.some(cr => cr > Math.min(...ps) && cr < Math.max(...ps)))` },
  // Was unlisted for months as "equivalent for every step in the corpus": with no clear at the
  // causing step B IS Bpre, so the next branch runs the identical test, and all 388 placement
  // attributions land on steps that cleared nothing. The shape that separates them — a step that
  // both places and clears, where Bpre already meets the target AND the post-clear best slot
  // straddles the cleared row — is now built by hand in forecast.test.ts, so the mutant is live.
  { name: 'metric/localise-skip-placement', note: 'a placement that already sufficed is credited to the clear',
    find: `  if (bestTspinLines(Bpre) >= target) return { step: t, mechanism: 'placement' };`, nth: 1,
    repl: `  if (false) return { step: t, mechanism: 'placement' };` },
  { name: 'metric/localise-unattributed-guessed', note: 'an unexplained improvement defaults to the piece',
    find: `    return { step: t, mechanism: touches ? 'placement' : 'unattributed' };`, nth: 1,
    repl: `    return { step: t, mechanism: 'placement' };` },
  // `metric/localise-garbage-unguarded` (dropping `&& garbageArrived`) is EQUIVALENT, and the
  // proof is the reconstruction assertion above it: with no garbage inserted B is asserted equal
  // to C, so avail(C) = avail(B), and control only reaches that line once avail(B) < target. The
  // guard therefore cannot change an outcome. It stays in the source as documentation of the
  // branch's precondition; it is not listed here, because a mutant nothing can kill is noise
  // that trains the reader to expect survivors.
  { name: 'metric/localise-first-step', note: 'blames the step after the roof rather than the causing one',
    find: `  while (t > j && avail(t - 1) >= target) t--;`, nth: 1,
    repl: `  while (t > j + 1) t--;` },
  { name: 'metric/localise-any-rise', note: 'stops at the last rise, not the level that HELD to execution',
    find: `  while (t > j && avail(t - 1) >= target) t--;`, nth: 1,
    repl: `  while (t > j && avail(t - 1) >= avail(t)) t--;` },
  { name: 'metric/reconstruction-unchecked', note: 'the step model may silently disagree with the game',
    find: `    if (!B.every((row, i) => row.every((c, x) => c === C[i]![x])))`, nth: 1,
    repl: `    if (false)` },
  // The garbage arm of the same assertion. It did not exist as a mutant because it did not exist as
  // a check: the reconstruction was guarded by `!garbageArrived`, so the one branch that can violate
  // the step model was the one branch never tested. Under insertMode:'immediate' that returned 13
  // verified forecasts across four sessions in silence.
  { name: 'metric/reconstruction-unchecked-under-garbage', note: 'garbage steps skip the step model',
    find: `    if (shift < 0)`, nth: 1,
    repl: `    if (false)` },
  { name: 'metric/lift-shift-unbounded', note: 'a shift matching vacuously at the bottom of the field',
    find: `      if (!C.slice(H - s).every(row => row.some(c => (c as unknown as string) === 'G'))) continue;`, nth: 1,
    repl: `      if (false) continue;` },

  // --- clause 2: was there a hole to close onto when the roof went up? -----------------------
  { name: 'metric/clause2-dropped', note: 'THE pre-2026-08-03 defect: mechanism alone counts',
    find: `  && holePreExisted(r.floorOrigin ?? 'undetermined') === true`, nth: 1,
    repl: `  && true` },

  // --- clause 4: was the closing clear itself a T-spin? --------------------------------------
  { name: 'metric/clause4-dropped', note: 'THE pre-2026-08-06 defect: a spin closing its own gap counts',
    find: `  && r.closingClearWasSpin !== true;`, nth: 1,
    repl: `  && true;` },
  { name: 'metric/clause4-inverted', note: 'only spin-closed gaps count',
    find: `  && r.closingClearWasSpin !== true;`, nth: 1,
    repl: `  && r.closingClearWasSpin === true;` },
  { name: 'metric/clause4-mini-allowed', note: 'a mini T-spin closing the gap is treated as an ordinary clear',
    find: `      ? r.locks[loc.step]!.spin !== 'none' : undefined;`, nth: 1,
    repl: `      ? r.locks[loc.step]!.spin === 'full' : undefined;` },
  { name: 'metric/clause2-inverted', note: 'a floor that arrived later counts and one that was there does not',
    find: `  o === 'undetermined' ? null : o === 'pre-existed';`, nth: 1,
    repl: `  o === 'undetermined' ? null : o !== 'pre-existed';` },
  { name: 'metric/clause2-undecided-passes', note: 'an undecidable floor is counted as a pass',
    find: `  o === 'undetermined' ? null : o === 'pre-existed';`, nth: 1,
    repl: `  o === 'undetermined' ? true : o === 'pre-existed';` },
  { name: 'metric/clause2-roof-excluded', note: 'a floor placed BY the roof piece stops counting',
    find: `    if (p >= 0) { if (p > j) after = true; continue; }`, nth: 1,
    repl: `    if (p >= 0) { if (p >= j) after = true; continue; }` },
  { name: 'metric/clause2-garbage-always-old', note: 'any garbage floor is assumed to predate the roof',
    find: `    if (garbageRows(j) === 0) after = true;`, nth: 1,
    repl: `    if (garbageRows(j) === 0) after = false;` },

  // Clause 2 reads EVERY cell holding the piece up, not the deepest row alone. These guard that:
  // the nose-only reading was a proper subset of the genuine supports in all 654 events, and the
  // `'field-floor'` verdict it needed to cover its blind spot named a case — a piece held up by
  // the playfield bottom ALONE — that occurs zero times in 654 events across seven configs.
  { name: 'metric/clause2-nose-row-only', note: 'reverts to reading only the cells under the deepest row',
    find: `  for (const c of lk.cells) {
    const below = c.row + 1;`, nth: 1,
    repl: `  const noseRow = Math.max(...lk.cells.map(c => c.row));
  for (const c of lk.cells.filter(c => c.row === noseRow)) {
    const below = c.row + 1;` },
  { name: 'metric/clause2-unsupported-passes', note: 'a piece resting on nothing is called pre-existing',
    find: `  if (provs.length === 0) return onFloor ? 'pre-existed' : 'undetermined';`, nth: 1,
    repl: `  if (provs.length === 0) return 'pre-existed';` },
  // There was a `metric/clause2-self-support` mutant here, guarding an `own.has(...)` skip for a
  // cell of the T sitting below another. It survived, and the reason is that the guard could not
  // do anything: `prev` is the snapshot BEFORE the lock, so those cells are still empty and the
  // null test already skips them. Measured 953 firings, 0 non-null. The guard was deleted rather
  // than given a test — a mutant nothing can kill is a line nothing needs.
  { name: 'metric/clause2-after-loses-to-unknown', note: 'a support that postdates the roof is reported undecidable',
    find: `  return after ? 'arrived-later' : unknown ? 'undetermined' : 'pre-existed';`, nth: 1,
    repl: `  return unknown ? 'undetermined' : after ? 'arrived-later' : 'pre-existed';` },

  // --- the execution-time counterfactual. It no longer classifies anything, but it is still
  //     RECORDED as an independent second opinion on the garbage branch, and the tests assert
  //     it — so these mutants stay live and guard the oracle rather than the classifier.
  { name: 'metric/garbage-co-occurrence', note: 'reverts to "garbage arrived", the original bug',
    find: `    const garbageLoadBearing = !!(boardK && arrivedSince.size
      && bestTspinLines(withoutRows(boardK, arrivedSince)) < availAtSpin);`, nth: 1,
    repl: `    const garbageLoadBearing = !!garbageBetween;` },
  { name: 'metric/garbage-causal-inverted', note: 'load-bearing test inverted',
    find: `      && bestTspinLines(withoutRows(boardK, arrivedSince)) < availAtSpin);`, nth: 1,
    repl: `      && bestTspinLines(withoutRows(boardK, arrivedSince)) >= availAtSpin);` },
  { name: 'metric/withoutRows-noop', note: 'the counterfactual board is the same board',
    find: `  const kept = board.filter((_, i) => !rows.has(i));`, nth: 1,
    repl: `  const kept = board.filter(() => true);` },
  // The deletion set. `deletion-set-unrestricted` is the defect this replaced: strip every garbage
  // row rather than the ones that arrived after the roof, and the slot's own floor goes with them.
  { name: 'metric/deletion-set-unrestricted', note: 'deletes all garbage, not the post-roof arrivals',
    find: `    const arrivedSince = boardK ? garbageArrivedAfter(r, j, k) : new Set<number>();`, nth: 1,
    repl: `    const arrivedSince = new Set<number>((boardK ?? []).flatMap((row, i) =>
      row.some(c => (c as unknown as string) === 'G') ? [i] : []));` },
  { name: 'metric/deletion-set-ignores-clears', note: 'the window walk does not carry marks past a clear',
    find: `      if (Bpre[row]!.every(x => x !== null)) { Bpre.splice(row, 1); post.splice(row, 1); }`, nth: 1,
    repl: `      if (false) { Bpre.splice(row, 1); post.splice(row, 1); }` },
  { name: 'metric/deletion-set-no-shift', note: 'inserted rows do not push the stack off the top',
    find: `      if (g.lockIndex === t) post = post.slice(g.amt).concat(new Array<boolean>(g.amt).fill(true));`, nth: 1,
    repl: `      if (g.lockIndex === t) post = post.concat(new Array<boolean>(g.amt).fill(true)).slice(0, H);` },
  { name: 'metric/deletion-set-trusts-events', note: 'marks rows the events claim without checking the board',
    find: `    p && boardK[i]!.some(c => (c as unknown as string) === 'G') ? [i] : []));`, nth: 1,
    repl: `    p ? [i] : []));` },
  { name: 'metric/self-built-counted', note: 'openers rejoin the forecast bucket',
    find: `  (r.kind === 'forecast_garbage' || r.kind === 'forecast_lineclear')`, nth: 1,
    repl: `  (r.kind !== 'reactive')` },

  // localiseMechanism's two out-of-contract guards. Unreachable from `forecastMetric` but the
  // function is exported and forecast.test.ts calls it directly with a hand-chosen j and target;
  // at those arguments both are live, and without them the function invents a mechanism instead
  // of declining to name one. See the two contract tests in forecast.test.ts.
  { name: 'localise/roof-at-previous-lock', note: 'a roof at k-1 leaves no window, yet a step gets blamed',
    find: `  if (t <= j) return { step: t, mechanism: 'unattributed' };`, nth: 1,
    repl: `  if (false) return { step: t, mechanism: 'unattributed' };` },
  { name: 'localise/garbage-target-unchecked', note: 'garbage is credited for a target the step never reached',
    find: `  if (avail(t) >= target && garbageArrived) return { step: t, mechanism: 'garbage' };`, nth: 1,
    repl: `  if (garbageArrived) return { step: t, mechanism: 'garbage' };` },
  { name: 'localise/garbage-unguarded', note: 'both conjuncts dropped; the tail unattributed return goes dead',
    find: `  if (avail(t) >= target && garbageArrived) return { step: t, mechanism: 'garbage' };`, nth: 1,
    repl: `  if (true) return { step: t, mechanism: 'garbage' };` },

  // An executed MINI must be classified exactly as the executed full spin is — nothing reads
  // lk.spin except the admission test and the record's own field. Pinned by the mini tests.
  //
  // RE-TARGETED. This searched for `if (lk.spin === 'none' || lk.cleared === 0) continue;`, one
  // line that no longer exists: the admission test was split so a zero-clearing spin could be
  // COUNTED into `drops.zeroClear` instead of silently `continue`d. The mini half of that test is
  // now its own line, and that is the line this mutant has always been about — the find string
  // moved, the mutant did not. Read the old entry to see why: it mutated `=== 'none'` to
  // `!== 'full'` and carried `|| lk.cleared === 0` IDENTICALLY on both sides, so the zero-clear
  // half was never part of the mutation, only part of the line.
  //
  // The find string deliberately stops at the semicolon and does not include the trailing
  // `// not a T-spin at all` comment, even though matching the full line would be more literal.
  // A find string that spans a comment is strandable by an editorial pass over that comment —
  // which is the exact failure this entry is being repaired FROM, just with a different trigger.
  // Ending at the code keeps the mutant robust and leaves the comment and its column padding
  // untouched for free, rather than obliging the replacement to reproduce them.
  { name: 'metric/executed-mini-excluded', note: 'a mini executed spin is dropped before it can be a forecast',
    find: `    if (lk.spin === 'none') continue;`, nth: 1,
    repl: `    if (lk.spin !== 'full') continue;` },
  // The other half of that split, which the combined line's mutant never reached: its replacement
  // kept `|| lk.cleared === 0`, so the line-clear requirement on the ADMISSION side has never been
  // mutated. Dropping it admits spins that cleared nothing into the tucked record set and empties
  // the `zeroClear` drop bucket the split exists to publish.
  { name: 'metric/zero-clear-admitted', note: 'a spin that cleared nothing is admitted to the record set',
    find: `    if (lk.cleared === 0) { drops.zeroClear.push(k); continue; }`, nth: 1,
    repl: `    if (false) { drops.zeroClear.push(k); continue; }` },
  { name: 'metric/executed-mini-not-verified', note: 'a mini is refused a verified-forecast kind that a full spin would get',
    find: `  (r.kind === 'forecast_garbage' || r.kind === 'forecast_lineclear')`, nth: 1,
    repl: `  r.spin !== 'mini' && (r.kind === 'forecast_garbage' || r.kind === 'forecast_lineclear')` },

  // The undecidable-clause-2 count exists so a zero rate cannot hide an undecidable case;
  // silencing it is the failure it guards against. Pinned by the clause-2-undetermined test.
  { name: 'metric/clause2-undecided-unreported', note: 'the undecidable-clause-2 count is forced to zero',
    find: `    && holePreExisted(x.floorOrigin ?? 'undetermined') === null).length;`, nth: 1,
    repl: `    && false).length;` },

  // A roof with no placer (j = -1) has no boards[-1]; the pre-board is empty. Reverting to the
  // bare index dereference throws on a garbage roof. Pinned by the j = -1 test.
  { name: 'metric/garbage-arrived-no-empty-preboard', note: 'the j = -1 pre-board reads boards[-1] instead of an empty field',
    find: `    const Bpre = (r.boards[t - 1] ?? emptyBoard()).map(row => [...row]) as Board;`, nth: 1,
    repl: `    const Bpre = r.boards[t - 1]!.map(row => [...row]) as Board;` },
];

function replaceNth(src: string, find: string, nth: number, repl: string): string {
  let idx = -1;
  for (let i = 0; i < nth; i++) {
    idx = src.indexOf(find, idx + 1);
    if (idx === -1) throw new Error(`occurrence ${nth} of ${JSON.stringify(find.slice(0, 50))} not found`);
  }
  return src.slice(0, idx) + repl + src.slice(idx + find.length);
}

// forecast-corpus.test.ts is in the default set deliberately. Hand-built fixtures cannot reach
// the shapes 654 real events do, and two mutants survived the fixture-only suite while changing
// the corpus classification — which is the failure mode that matters, since the corpus is what
// the report quotes.
const TESTS = process.argv.slice(2).length ? process.argv.slice(2)
  : ['forecast.test.ts', 'wiki-fixtures.test.ts', 'forecast-corpus.test.ts'];
const original = readFileSync(SRC, 'utf8');
copyFileSync(SRC, BAK);

/**
 * Restore on ANY exit, not just the happy path.
 *
 * This harness mutates `forecast.ts` IN PLACE and restored it only after the sweep finished. A
 * crash on 2026-08-02 therefore left `Math.min(...placers)` sitting in the committed source where
 * `Math.max` belongs — a live mutation, invisible to `git status` only because nothing looked.
 * It was caught by a unit test, but every command run in between was executing mutated code.
 *
 * Two things make that recoverable now: the restore is unconditional, and the backup is only
 * taken when the file is known-good. Note the second-order trap that made the first diagnosis
 * hard — re-running the harness copies the ALREADY-MUTATED source into the backup, so
 * `diff forecast.ts forecast.ts.mutbak` comes back identical and looks like proof of health.
 * Compare against git, not against the backup.
 *
 * KNOWN HAZARD, NOT FIXED — unconditional is not the same as safe. `original` is read ONCE at
 * startup and every restore path writes that snapshot back with no check that the file moved
 * underneath it. So a concurrent editor loses their work: anything written to `forecast.ts`
 * after the sweep starts is silently reverted when it ends, and `git status` reads the same
 * either way because the file is modified in both worlds. This is strictly worse than the abort
 * this file was just repaired for — that one lost a summary, this one loses source. The fix is a
 * guard that compares the file against the snapshot before restoring and REFUSES rather than
 * clobbers. Deliberately out of scope for this branch; do not run this harness against a
 * worktree anyone else is editing until it exists.
 */
let restored = false;
const restore = () => {
  if (restored) return;
  restored = true;
  writeFileSync(SRC, original);
};
process.on('exit', restore);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP'] as const) process.on(sig, () => { restore(); process.exit(130); });
process.on('uncaughtException', e => { restore(); console.error(e); process.exit(1); });

// baseline must be green, or every mutant "dies" for the wrong reason
try {
  execSync(`bun test ${TESTS.join(' ')}`, { stdio: 'pipe' });
} catch {
  console.error('BASELINE IS RED — fix the suite before mutating.');
  process.exit(1);
}
console.log(`baseline green over ${TESTS.join(', ')}\n`);

/**
 * A find string that no longer occurs is a mutant that never RAN, and the sweep used to be unable
 * to say so. `replaceNth` threw out of the loop; the exit handler restored the file; the run ended
 * after 45 `killed` lines with no summary at all — which reads like a clean finish, not like four
 * mutants going unmeasured. `metric/executed-mini-excluded` sat stale that way for weeks, and took
 * the three entries after it down with it, their kill status simply unknown.
 *
 * So a miss is recorded, the sweep CONTINUES through the rest, and the run fails at the end with
 * every stale entry named: a mutant that cannot be applied is not a mutant that was killed, and
 * the kill count must be reported over the mutants that actually ran.
 */
const mismatched: { m: Mutant; observed: Verdict; expected: Verdict }[] = [];
const stale: { m: Mutant; why: string }[] = [];
let killedCount = 0, controlsHeld = 0;
for (const m of MUTANTS) {
  let mutated: string;
  try {
    mutated = replaceNth(original, m.find, m.nth, m.repl);
  } catch (e) {
    stale.push({ m, why: (e as Error).message });
    console.log(`   STALE    ${m.name.padEnd(26)} ${m.note}`);
    continue;
  }
  writeFileSync(SRC, mutated);
  let killed = false;
  try { execSync(`bun test ${TESTS.join(' ')}`, { stdio: 'pipe' }); }
  catch { killed = true; }

  const observed: Verdict = killed ? 'killed' : 'survived';
  const expected = m.expect ?? 'killed';
  if (observed === expected) {
    if (observed === 'killed') killedCount++; else controlsHeld++;
    console.log(`  ${observed.padEnd(9)} ${m.name.padEnd(26)} ${m.note}${expected === 'survived' ? '   [control held]' : ''}`);
  } else {
    mismatched.push({ m, observed, expected });
    console.log(`! ${observed.toUpperCase().padEnd(9)} ${m.name.padEnd(26)} ${m.note}   ← expected to be ${expected}`);
  }
}
writeFileSync(SRC, original);
unlinkSync(BAK);

const ran = MUTANTS.length - stale.length;
console.log(`\n${killedCount}/${ran} killed, ${controlsHeld} control(s) held, ${mismatched.length} mismatched${
  stale.length ? `, ${stale.length} of ${MUTANTS.length} never ran` : ''}`);
if (mismatched.length) {
  console.log('\nVERDICT MISMATCH — the observed outcome is not the asserted one:');
  for (const x of mismatched) {
    console.log(x.observed === 'survived'
      ? `  - ${x.m.name} SURVIVED but must die: it needs a killing test or an equivalence proof. ${x.m.note}`
      : `  - ${x.m.name} was KILLED but is declared a control: it is no longer semantics-preserving, so it controls for nothing. ${x.m.note}`);
  }
}
if (stale.length) {
  console.log('\nSTALE — the find string no longer occurs in forecast.ts, so these were never applied.');
  console.log('Re-target each onto the line that now carries the behaviour its name describes; do not');
  console.log('delete it, because an unapplied mutant is a hole, not a passing check:');
  for (const s of stale) console.log(`  - ${s.m.name}: ${s.why}`);
}
if (mismatched.length || stale.length) process.exit(1);
