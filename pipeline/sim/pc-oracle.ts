/**
 * CLAIM: TETR.IO sends a perfect clear as TWO ige events at the SAME frame — the base line-clear
 * attack, and a separate event of amount exactly 10 for the all-clear bonus.
 *
 * If true, the opponent's ige stream is a per-PC ORACLE: every real perfect clear is locatable in
 * time, which is what the 7-vs-19 question has been missing. It also explains why the verified
 * prefix is 0 in PC rounds — the sim emits one combined attack (1+10=11) and the prefix matcher
 * compares it against the truth's 1, fails, and truncates at the very first clear.
 *
 * RESULT, over all 158 player-rounds: 158/158 exact, 19 predicted vs 19 recorded.
 *
 * The first version of this test additionally required the 10 to share a frame with another
 * attack, and scored 155/158 — the three misses are PCs whose base attack was fully cancelled, so
 * no sibling event exists. Co-location is a coincidence of the common case, not the rule. The rule
 * is `amt === 10`, and the histogram is why it is safe: no ordinary attack in this dataset reaches
 * 9 or 10, and 10 occurs exactly 19 times.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { replayDir } from './verified-prefix.ts';

const DIR = replayDir();

let exact = 0, total = 0, sumReal = 0, sumFound = 0, soloBonus = 0;
const bad: string[] = [];
const amtHist = new Map<number, number>();

for (const f of readdirSync(DIR).filter(x => x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`, 'utf8'));
  d.replay.rounds.forEach((rnd: any, ri: number) => {
    if (rnd.length !== 2) return;
    const P = rnd.map((p: any) => ({ p, rp: p.replay, gameid: p.replay.options.gameid }));
    for (const [me, other] of [[P[0], P[1]], [P[1], P[0]]] as any[]) {
      // every attack THIS player sent, as recorded in the opponent's incoming stream
      const truth = other.rp.events
        .filter((e: any) => e.type === 'ige' && e.data.type === 'interaction'
          && e.data.data?.type === 'garbage' && e.data.data.gameid === me.gameid)
        .map((e: any) => ({ frame: e.data.data.frame ?? e.frame, amt: e.data.data.amt }))
        .sort((a: any, b: any) => a.frame - b.frame);

      const byFrame = new Map<number, number[]>();
      for (const t of truth) { if (!byFrame.has(t.frame)) byFrame.set(t.frame, []); byFrame.get(t.frame)!.push(t.amt); }

      // Refined after measuring: co-location is NOT required. Three PCs had their base attack
      // fully cancelled, so no sibling event exists at that frame — but the bonus 10 is still
      // sent. And no ordinary attack in this dataset ever reaches 10 (the histogram tops out at
      // 8, with nothing at 9). So the rule is simply: amt === 10 is an all-clear bonus.
      const found = truth.filter((t: any) => t.amt === 10).length;
      const coLocated = [...byFrame.values()].filter(a => a.includes(10) && a.length > 1).length;
      if (found !== coLocated) soloBonus += found - coLocated;
      for (const t of truth) amtHist.set(t.amt, (amtHist.get(t.amt) ?? 0) + 1);

      const real = me.rp.results.stats.clears.allclear ?? 0;
      total++;
      sumReal += real; sumFound += found;
      if (found === real) exact++;
      else bad.push(`${f.slice(-9)} r${ri} ${me.p.username}: oracle ${found} vs stats ${real}`);
    }
  });
}

console.log(`player-rounds                     : ${total}`);
console.log(`oracle count == stats.allclear    : ${exact}/${total}  (${(100 * exact / total).toFixed(1)}%)`);
console.log(`total PCs — oracle ${sumFound}, stats ${sumReal}\n`);
if (bad.length) { console.log(`mismatches (${bad.length}):`); for (const b of bad.slice(0, 20)) console.log(`  ${b}`); }
else console.log('NO MISMATCHES: amt===10 is an exact per-round oracle for the perfect clear.');
console.log(`bonuses sent with NO sibling attack at the same frame (base fully cancelled): ${soloBonus}`);

console.log('\nattack-amount histogram across all ige events (is 10 special?):');
const h = [...amtHist.entries()].sort((a, b) => a[0] - b[0]);
for (const [amt, n] of h) console.log(`  amt ${String(amt).padStart(3)} : ${'#'.repeat(Math.min(60, Math.ceil(n / 8)))} ${n}`);
