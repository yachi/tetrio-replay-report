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

interface Mutant { name: string; note: string; find: string; nth: number; repl: string }

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
    find: `      if (lines > best) best = lines;`, nth: 1,
    repl: `      best = Math.max(best, Math.max(lines, 1));` },

  // --- forecastMetric classifier ---
  { name: 'metric/roof-oldest-builder', note: 'roof attributed to the earliest placer, not the latest',
    find: `const j = placers.length ? Math.max(...placers) : -1;`, nth: 1,
    repl: `const j = placers.length ? Math.min(...placers) : -1;` },
  { name: 'metric/strict-gate-inverted', note: 'strict gate answers the opposite question',
    find: `if (boardJ) { determinable = true; slotOpenedLater = !tspinAvailable(boardJ); }`, nth: 1,
    repl: `if (boardJ) { determinable = true; slotOpenedLater = tspinAvailable(boardJ); }` },
  { name: 'metric/strict-disabled', note: 'silently falls back to the loose rule',
    find: `const opened = strict && determinable ? slotOpenedLater : (clearBetween || garbageBetween);`, nth: 1,
    repl: `const opened = (clearBetween || garbageBetween);` },
];

function replaceNth(src: string, find: string, nth: number, repl: string): string {
  let idx = -1;
  for (let i = 0; i < nth; i++) {
    idx = src.indexOf(find, idx + 1);
    if (idx === -1) throw new Error(`occurrence ${nth} of ${JSON.stringify(find.slice(0, 50))} not found`);
  }
  return src.slice(0, idx) + repl + src.slice(idx + find.length);
}

const TESTS = process.argv.slice(2).length ? process.argv.slice(2) : ['forecast.test.ts', 'wiki-fixtures.test.ts'];
const original = readFileSync(SRC, 'utf8');
copyFileSync(SRC, BAK);

// baseline must be green, or every mutant "dies" for the wrong reason
try {
  execSync(`bun test ${TESTS.join(' ')}`, { stdio: 'pipe' });
} catch {
  console.error('BASELINE IS RED — fix the suite before mutating.');
  process.exit(1);
}
console.log(`baseline green over ${TESTS.join(', ')}\n`);

const survivors: Mutant[] = [];
for (const m of MUTANTS) {
  writeFileSync(SRC, replaceNth(original, m.find, m.nth, m.repl));
  let killed = false;
  try { execSync(`bun test ${TESTS.join(' ')}`, { stdio: 'pipe' }); }
  catch { killed = true; }
  console.log(`${killed ? '  killed  ' : 'SURVIVED  '} ${m.name.padEnd(26)} ${m.note}`);
  if (!killed) survivors.push(m);
}
writeFileSync(SRC, original);
unlinkSync(BAK);

console.log(`\n${MUTANTS.length - survivors.length}/${MUTANTS.length} killed`);
if (survivors.length) {
  console.log('\nsurvivors — each needs a killing test or an equivalence proof:');
  for (const s of survivors) console.log(`  - ${s.name}: ${s.note}`);
}
