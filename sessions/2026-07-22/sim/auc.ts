/**
 * Does forecast rate predict who won the round? Same paired-AUC probe the repo uses.
 *
 * Pairing lives in pairs.ts, shared with auc-power.ts — there is one implementation of
 * "winner's value vs loser's value" and both consumers read it.
 *
 * Read this alongside auc-power.ts before quoting any number here. `forecast rate` rests on 11
 * decided pairs; its AUC is not comparable at face value to a figure computed over 129 rounds.
 */
import { collectRows, pairsFor, auc, METRICS, type Metric } from './pairs.ts';

const STRICT = process.env.LOOSE !== '1';
const rows = collectRows(STRICT);
console.log(`rounds with a decided winner and verified data on both sides: ${rows.length}\n`);

for (const m of METRICS) {
  const P = pairsFor(rows, m as Metric);
  if (!P.length) { console.log(`  ${m.padEnd(20)} no usable pairs`); continue; }
  const a = auc(P);
  console.log(`  ${m.padEnd(20)} AUC ${a.auc.toFixed(1)}%   (n=${a.n} pairs, ${a.ties} ties)`);
}
console.log(`\nreference from repo CLAUDE.md — TSD 60.9 · TST 55.8 are already filed under "No signal"`);
console.log(`power: only "tucked T-spins" (54 decided pairs) is adequately powered — see auc-power.ts`);
