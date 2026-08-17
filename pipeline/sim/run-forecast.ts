const STRICT = process.env.LOOSE !== '1';
const STRICT_ROWS = process.env.LOOSEROWS !== '1';
/**
 * Run the forecast metric, but ONLY over the verified prefix of each round.
 *
 * The opponent's ige stream gives a per-attack oracle; a T-spin is counted only if it occurs
 * before the first attack divergence, i.e. on a board still provably matching the real game.
 * With STRICT_ROWS (default) the ige row oracle must agree too — 7.4% of attacks match on
 * frame and amount while coming from the wrong board row, and a forecast read off such a
 * board is fiction.
 *
 * The prefix, and therefore this metric's whole sample size, is a function of simulator
 * accuracy. See verified-prefix.ts for the shared gate and the settings.
 */
import { forecastMetric, isVerifiedForecast, zeroKindTotals, type ForecastKind } from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

const byUser:Record<string,{tot:Record<ForecastKind,number>;verified:number;tspins:number;
  verifiedPieces:number;totalPieces:number;seps:number[]}> = {};
let roundsUsed=0, verifiedLocks=0, totalLocks=0;
const ALL:any[]=[];
for (const c of loadCases()) {
  const r = runCase(c);
  const vIdx = verifiedIndex(r, c.truth, STRICT_ROWS);
  const u = c.user;
  // `self_built` was missing from this initialiser, so `tot[rec.kind]++` produced NaN for 388 of
  // the 654 records and the printed breakdown silently failed to sum to the header count. The
  // literal is GONE now rather than extended: `path_opened` arriving would have reproduced the bug
  // exactly, in the file whose own comment describes it, which is the evidence that "remember to
  // add it here too" does not hold. `zeroKindTotals()` derives it from the one kind list.
  byUser[u] ??= {tot:zeroKindTotals(),
                verified:0,tspins:0,verifiedPieces:0,totalPieces:0,seps:[]};
  byUser[u]!.verifiedPieces += vIdx+1; byUser[u]!.totalPieces += c.placed;
  verifiedLocks += vIdx+1; totalLocks += c.placed;
  if (vIdx < 0) continue;
  roundsUsed++;
  const fm = forecastMetric(r, STRICT);
  for (const rec of fm.records) { if (rec.lockIndex > vIdx) continue;
    byUser[u]!.tot[rec.kind]++; byUser[u]!.tspins++; byUser[u]!.seps.push(rec.separation);
    if (isVerifiedForecast(rec)) byUser[u]!.verified++;
    ALL.push({u,...rec}); }
}
console.log(`=== T-Spin Forecast — verified-prefix only ===`);
console.log(`rule: ${STRICT?'strict':'loose'}   gate: ${STRICT_ROWS?'frame+amount+row':'frame+amount'}`);
console.log(`rounds contributing: ${roundsUsed}/158`);
console.log(`board coverage: ${verifiedLocks}/${totalLocks} placements (${(100*verifiedLocks/totalLocks).toFixed(1)}%) provably match the real game\n`);
for(const [u,v] of Object.entries(byUser)){
  // the NUMERATOR is isVerifiedForecast, never a kind test — the kinds say which edit closed the
  // gap and do not carry clauses 2 and 4. See forecast.ts:isVerifiedForecast.
  const fc=v.verified;
  const med=v.seps.length?[...v.seps].sort((a,b)=>a-b)[Math.floor(v.seps.length/2)]:0;
  console.log(`${u}`);
  console.log(`  tucked T-spins on verified board : ${v.tspins}`);
  console.log(`    forecast (garbage)   : ${v.tot.forecast_garbage}`);
  console.log(`    forecast (line clear): ${v.tot.forecast_lineclear}`);
  console.log(`    path_opened          : ${v.tot.path_opened}`);
  console.log(`    self_built           : ${v.tot.self_built}`);
  console.log(`    reactive             : ${v.tot.reactive}`);
  // The breakdown must SUM to the header count. A zeroed tally that silently omits a kind was the
  // original defect; a printer that silently omits one has the same effect on the reader.
  const shown = Object.values(v.tot).reduce((a,b)=>a+b,0);
  if (shown !== v.tspins) throw new Error(`${u}: breakdown sums to ${shown}, header says ${v.tspins}`);
  console.log(`  forecast rate: ${v.tspins?(100*fc/v.tspins).toFixed(1):'n/a'}%   median setup separation: ${med} pieces`);
}

console.log('\n=== robustness cuts ===');
for(const minSep of [1,2,3,5]){
  const sub=ALL.filter(r=>r.separation>=minSep);
  // was `r.kind!=='reactive'`, the idiom isVerifiedForecast exists to abolish: it counted every
  // self_built opener as a forecast and printed 58.0% under a headline rate of 0.0%.
  const fc=sub.filter(isVerifiedForecast).length;
  console.log(`  separation >= ${minSep}: n=${String(sub.length).padStart(3)}  forecast=${String(fc).padStart(3)} (${sub.length?(100*fc/sub.length).toFixed(1):'-'}%)`);
}
const rg=ALL.filter(r=>r.roofIsGarbage);
console.log(`  roof literally IS garbage (strongest signal): ${rg.length}/${ALL.length}`);
console.log(`  separation == 1 (overhang was the immediately preceding piece): ${ALL.filter(r=>r.separation===1).length}`);
const dist:Record<number,number>={}; for(const r of ALL) dist[r.separation]=(dist[r.separation]||0)+1;
console.log('  separation distribution:', Object.entries(dist).sort((a,b)=>+a[0]-+b[0]).slice(0,10).map(([k,v])=>`${k}:${v}`).join(' '));
