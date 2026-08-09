/**
 * LINE-COUNT differential: our `bestTspinLines` vs the ORIGINAL cold-clear's `cutout_tslot`, over
 * every verified-prefix board of the REPLAY_DIR session.
 *
 * `cross-tslot.test.ts` cross-checks slot PRESENCE against our hand PORT (`ccTslots`). This checks
 * the LINE COUNT — the quantity the forecast metric actually consumes (`availAtRoof`, `availAtSpin`,
 * `improved`) — against the compiled Rust `cc-oracle`, the only outside authority for it. Until this
 * existed the count was validated only against our own second BFS.
 *
 * Two things are genuine disagreements and fail the gate:
 *   - a COUNT mismatch where both sides find a slot (a real miscount), and
 *   - cc finds a line-clearing slot we score 0 (a false negative in our detector).
 * One thing is NOT a disagreement and is reported, not failed: boards where WE find a line-clearing
 * T-spin cold-clear's six NAMED opener detectors (sky/tst/fin/cave) do not. cold-clear's set is a
 * curated opener vocabulary; our BFS answers the general question. A plain T-spin single into a well
 * is real and reachable yet is none of those named shapes — measured 588 such boards across the
 * four sessions, every one a genuine hard-drop-reachable spin.
 *
 *   REPLAY_DIR=sessions/2026-07-22 bun pipeline/sim/cross-tslot-count.ts ./result/bin/cc-oracle
 */
import { spawnSync } from 'node:child_process';
import { bestTspinLines } from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

const oracle = process.argv[2];
if (!oracle) { console.error('usage: cross-tslot-count.ts <path to cc-oracle>'); process.exit(2); }

const ours: number[] = [];
const boards: string[] = [];
for (const c of loadCases()) {
  const r = runCase(c);
  const v = verifiedIndex(r, c.truth);
  for (let s = 0; s <= v; s++) {
    const b = (r.boards as unknown as Record<number, (number | null)[][]>)[s];
    if (!b) continue;
    ours.push(bestTspinLines(b as never));
    boards.push(b.map(row => row.map(x => (x === null ? '.' : 'X')).join('')).join('\n'));
  }
}

const res = spawnSync(oracle, { input: boards.join('\n') + '\n', encoding: 'utf8', maxBuffer: 1 << 28 });
if (res.status !== 0) { console.error('cc-oracle failed:', res.stderr); process.exit(2); }
const cc = res.stdout.split('\n').filter(l => l.trim()).map(l => JSON.parse(l).lines as number);

if (cc.length !== ours.length) { console.error(`length mismatch: ours ${ours.length}, cc ${cc.length}`); process.exit(2); }

let miscount = 0, falseNeg = 0, bothPos = 0, oursOnly = 0;
for (let i = 0; i < ours.length; i++) {
  if (ours[i]! > 0 && cc[i]! > 0) { bothPos++; if (ours[i] !== cc[i]) miscount++; }
  else if (ours[i] === 0 && cc[i]! > 0) falseNeg++;
  else if (ours[i]! > 0 && cc[i] === 0) oursOnly++;
}

console.log(`${ours.length} boards | both find a slot: ${bothPos}, counts match: ${bothPos - miscount}`
  + ` | miscounts: ${miscount} | false negatives (cc>0, ours=0): ${falseNeg}`
  + ` | general spins beyond cold-clear's named shapes: ${oursOnly}`);

if (miscount || falseNeg) {
  console.error(`FAIL: ${miscount} miscount(s) and ${falseNeg} false negative(s) vs the Rust original`);
  process.exit(1);
}
console.log('ok — every line count agrees with cold-clear, and no line-clearing slot is missed');
