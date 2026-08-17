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

// DIRECTION MATTERS, and treating both directions as one "miscount" was a bug in this gate that
// only wider coverage could expose. When both sides report a slot they have not necessarily found
// the SAME slot: cc reports the count for its best NAMED shape, ours reports the best placement its
// BFS can reach. So a difference is only a defect in one direction.
//
//   ours < cc   we under-count, or missed a better slot cc found. A REAL failure — cc is the
//               outside authority for the number the forecast metric consumes.
//   ours > cc   we found a reachable placement clearing more lines than cc's best named shape.
//               That is the SAME fact `oursOnly` (cc == 0) already tolerates and reports — the
//               curated opener vocabulary vs the general question — just on a board where cc's
//               vocabulary happens to match something too. Reported, not failed.
//
// This fired on exactly ONE board in 20 226 across six sessions, and the arithmetic was checked by
// hand before the rule was written rather than after: 2026-08-09 `replay-2026-08-09-2.ttrm` r5
// pinglamb board 18, ours 2 against cc's 1 (`tst_twist_left`). Rows 38 and 39 read `XXX...XXXX` and
// `XXXX.XXXXX`, i.e. r38 is missing exactly c3/c4/c5 and r39 exactly c4 — so a T at r38 c3-c5 with
// its nose at r39 c4 completes both rows. Two lines is the right answer and cc's 1 is its own
// different placement. Had the count gone the other way this would have stayed a failure.
let underCount = 0, falseNeg = 0, bothPos = 0, oursOnly = 0, overNamed = 0;
for (let i = 0; i < ours.length; i++) {
  if (ours[i]! > 0 && cc[i]! > 0) {
    bothPos++;
    if (ours[i]! < cc[i]!) underCount++;
    else if (ours[i]! > cc[i]!) overNamed++;
  } else if (ours[i] === 0 && cc[i]! > 0) falseNeg++;
  else if (ours[i]! > 0 && cc[i] === 0) oursOnly++;
}

console.log(`${ours.length} boards | both find a slot: ${bothPos}, counts match: ${bothPos - underCount - overNamed}`
  + ` | UNDER-counts (ours < cc): ${underCount} | false negatives (cc>0, ours=0): ${falseNeg}`
  + ` | ours clears more than cc's named shape: ${overNamed}`
  + ` | general spins beyond cold-clear's named shapes: ${oursOnly}`);

if (underCount || falseNeg) {
  console.error(`FAIL: ${underCount} under-count(s) and ${falseNeg} false negative(s) vs the Rust original`);
  process.exit(1);
}
console.log('ok — we never count fewer lines than cold-clear, and no line-clearing slot is missed');
