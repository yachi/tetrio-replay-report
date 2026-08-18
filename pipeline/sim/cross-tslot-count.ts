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
 * is real and reachable yet is none of those named shapes — measured 5,587 such boards across the
 * six sessions, every one a genuine hard-drop-reachable spin.
 *
 * BOARD SOURCE: `runCaseOracle`, the vendored Triangle engine — the same source the published
 * forecast metric consumes (`emit-forecast-facts.ts`) and the same one `cross-tslot.test.ts` switched
 * to on 2026-08-12. This gate was left on the hand-port `runCase` until 2026-08-17, so the only
 * outside authority for `bestTspinLines` was checked on 20,226 boards while the metric consumed
 * 61,656 — a third of them. Widening it is what makes the near-topout sanction below load-bearing:
 * at the hand-port's shorter prefix there were no false negatives with or without it.
 *
 *   REPLAY_DIR=sessions/2026-07-22 bun pipeline/sim/cross-tslot-count.ts ./result/bin/cc-oracle
 */
import { spawnSync } from 'node:child_process';
import { bestTspinLines } from './forecast.ts';
import { classify } from './tslot-sanction.ts';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';

const oracle = process.argv[2];
if (!oracle) { console.error('usage: cross-tslot-count.ts <path to cc-oracle>'); process.exit(2); }

const ours: number[] = [];
const boards: string[] = [];
// The board itself, kept because the near-topout sanction has to be evaluated on it AFTER the
// oracle has answered — and the oracle is one batched spawn over every board.
const cells: (number | null)[][][] = [];
const where: string[] = [];
for (const c of loadCases()) {
  const r = runCaseOracle(c);
  const v = verifiedIndex(r, c.truth);
  for (let s = 0; s <= v; s++) {
    const b = (r.boards as unknown as Record<number, (number | null)[][]>)[s];
    if (!b) continue;
    ours.push(bestTspinLines(b as never));
    boards.push(b.map(row => row.map(x => (x === null ? '.' : 'X')).join('')).join('\n'));
    cells.push(b);
    where.push(`${c.file} r${c.round} ${c.user} board ${s}`);
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
// This fired on 1 board of 20 226 at the hand-port scope and fires on 8 of 61 656 at the oracle's
// (all eight `ours=2` against `cc=1`). The arithmetic was checked by hand before the rule was
// written rather than after, on a board that is still among the eight: 2026-08-09
// `replay-2026-08-09-2.ttrm` r5 pinglamb board 18, ours 2 against cc's 1 (`tst_twist_left`).
// Rows 38 and 39 read `XXX...XXXX` and
// `XXXX.XXXXX`, i.e. r38 is missing exactly c3/c4/c5 and r39 exactly c4 — so a T at r38 c3-c5 with
// its nose at r39 c4 completes both rows. Two lines is the right answer and cc's 1 is its own
// different placement. Had the count gone the other way this would have stayed a failure.
//
// THE FALSE-NEGATIVE ARM IS SANCTIONED, THE UNDER-COUNT ARM IS NOT, and the asymmetry is the point.
// `classify` (tslot-sanction.ts) tolerates a slot our BFS cannot reach only where our side found
// NOTHING and the board explains it — a spin is reachable but clears no line, or the stack is
// near-topout, where cold-clear matches column heights and a T can barely manoeuvre. Where both
// sides find a slot and cc's count is larger, no near-topout argument applies: that is a miscount of
// the number the metric consumes, and it fails unconditionally, as it always has.
let underCount = 0, falseNeg = 0, bothPos = 0, oursOnly = 0, overNamed = 0, falseNegSanctioned = 0;
const unsanctioned: string[] = [];
const explained: string[] = [];
for (let i = 0; i < ours.length; i++) {
  if (ours[i]! > 0 && cc[i]! > 0) {
    bothPos++;
    if (ours[i]! < cc[i]!) underCount++;
    else if (ours[i]! > cc[i]!) overNamed++;
  } else if (ours[i] === 0 && cc[i]! > 0) {
    const s = classify(cells[i]! as never);
    const line = `${where[i]} cc=${cc[i]} ours=0 stackTop=${s.stackTop} anySpinLines=${s.anySpinLines}: ${s.reason}`;
    if (s.sanctioned) { falseNegSanctioned++; explained.push(line); }
    else { falseNeg++; unsanctioned.push(line); }
  }
  else if (ours[i]! > 0 && cc[i] === 0) oursOnly++;
}

console.log(`${ours.length} boards | both find a slot: ${bothPos}, counts match: ${bothPos - underCount - overNamed}`
  + ` | UNDER-counts (ours < cc): ${underCount} | false negatives (cc>0, ours=0): ${falseNeg} unsanctioned`
  + ` + ${falseNegSanctioned} sanctioned`
  + ` | ours clears more than cc's named shape: ${overNamed}`
  + ` | general spins beyond cold-clear's named shapes: ${oursOnly}`);
for (const l of explained) console.log(`  sanctioned: ${l}`);

if (underCount || falseNeg) {
  for (const l of unsanctioned) console.error(`  UNSANCTIONED: ${l}`);
  console.error(`FAIL: ${underCount} under-count(s) and ${falseNeg} unsanctioned false negative(s) vs the Rust original`);
  process.exit(1);
}
console.log('ok — we never count fewer lines than cold-clear, and every line-clearing slot we miss is'
  + ' one the board itself explains');
