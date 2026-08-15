/**
 * MULTI-SLOT differential: does cold-clear's multi-slot cutout counting see anything our scalar
 * `bestTspin` (a max over placements) does not — and would any of it change the forecast metric?
 *
 * `cross-tslot-count.ts` differentials the LINE COUNT (our `bestTspinLines` vs cold-clear's
 * `cutout_tslot`) and finds 1,831/1,831 agreement, 0 false negatives. That is a SCALAR-vs-SCALAR
 * check: both sides report one number, the best T-spin on the board. This script asks the next
 * question up — cold-clear's evaluator does not stop at the best slot, it cuts each slot out and
 * re-detects (standard.rs `Evaluator::evaluate`), so it counts a CHAIN of slots. The oracle now
 * emits that chain as `slots:[...]` under `CC_ORACLE_SLOTS=1`; here we compare it, per board, to
 * what our scalar sees.
 *
 * WHY THIS MATTERS. This repo's memory (`scalar-gate-leaks-the-lineclear-arm`) records the exact
 * defect: the forecast metric walks `avail(t)` = the board's BEST T-spin, a scalar, and so "cannot
 * see a NEW slot born while another slot of equal line-count already exists". Multi-slot counting is
 * the thing that CAN see it. So the measurement is: how often does the corpus actually contain 2+
 * independent slots (the blind spot's precondition), and does exposing them ever change the value
 * the metric would consume (availability, and the best-line count `improved`/`localiseMechanism`
 * read)?
 *
 * This is a SCRIPT, not a .test.ts: it needs the built oracle binary as argv[2] and measures, it
 * does not gate. It sets CC_ORACLE_SLOTS=1 so the oracle appends the `slots` field.
 *
 *   bun pipeline/sim/cross-tslot-multi.ts ./result/bin/cc-oracle
 */
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { bestTspinLines } from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

const oracle = process.argv[2];
if (!oracle) { console.error('usage: cross-tslot-multi.ts <path to cc-oracle>'); process.exit(2); }

// Every session. This stood at four from 2026-08-12 to 2026-08-15 while 08-09 and 08-14 joined
// the corpus, so the CI step that runs this file covered four sessions no matter what the workflow
// said — the same silent-under-coverage the workflow's own loop had. Adding a session means adding
// it HERE too; nothing derives this list.
const SESSIONS = ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14'];

interface CC { any: boolean; lines: number; slots: number[]; }

// Aggregates. `ours` is the scalar the metric actually consumes (bestTspinLines). `lines` is
// cold-clear's max over its six named detectors (the quantity cross-tslot-count.ts already agrees
// with). `slots` is the multi-slot chain.
let N = 0;               // verified-prefix boards over every session in SESSIONS
let ccAnySlot = 0;       // boards where cold-clear's chain finds >=1 slot (incl. 0-line spins)
let ccLineClearing = 0;  // boards where at least one chained slot clears >=1 line
let multi2 = 0;          // boards with >=2 slots in the chain
let multi2LineClearing = 0; // boards with >=2 slots that each clear >=1 line
let equalTop = 0;        // boards with >=2 line-clearing slots SHARING the top line count -> the
                         // exact case the scalar max hides ("a new slot of equal line-count")
const slotHist = new Map<number, number>(); // chain length -> boards

// Scalar-vs-multi divergences that could touch the metric.
let oursNeMultiBest = 0; // ours != max(slots)   (any divergence)
let oursGtMultiBest = 0; // ours >  max(slots)   (our BFS sees a spin outside cold-clear's named vocab)
let multiBestGtOurs = 0; // max(slots) > ours    (multi sees a bigger CURRENT-board spin than scalar) -> would move the metric
let availDisagree = 0;   // (ours>0) != (max(slots)>0)   availability flip
let hiddenCapacity = 0;  // sum over multi boards of (sum(slots) - max(slots)): line-clears the scalar drops

const perSession: string[] = [];

for (const s of SESSIONS) {
  const ours: number[] = [];
  const boards: string[] = [];
  for (const c of loadCases(resolve('sessions', s))) {
    const r = runCase(c);
    const v = verifiedIndex(r, c.truth);
    for (let t = 0; t <= v; t++) {
      const b = (r.boards as unknown as Record<number, (number | null)[][]>)[t];
      if (!b) continue;
      ours.push(bestTspinLines(b as never));
      boards.push(b.map(row => row.map(x => (x === null ? '.' : 'X')).join('')).join('\n'));
    }
  }

  const res = spawnSync(oracle, {
    input: boards.join('\n') + '\n', encoding: 'utf8', maxBuffer: 1 << 28,
    env: { ...process.env, CC_ORACLE_SLOTS: '1' },
  });
  if (res.status !== 0) { console.error('cc-oracle failed:', res.stderr); process.exit(2); }
  const cc: CC[] = res.stdout.split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
  if (cc.length !== ours.length) {
    console.error(`length mismatch in ${s}: ours ${ours.length}, cc ${cc.length}`); process.exit(2);
  }

  let sMulti2 = 0, sEqualTop = 0, sMultiBestGtOurs = 0;
  for (let i = 0; i < cc.length; i++) {
    N++;
    const o = ours[i]!;
    const slots = cc[i]!.slots;
    const lc = slots.filter(x => x > 0);       // line-clearing slots in the chain
    const best = slots.length ? Math.max(...slots) : 0;

    if (slots.length >= 1) ccAnySlot++;
    if (lc.length >= 1) ccLineClearing++;
    if (slots.length >= 2) { multi2++; sMulti2++; }
    if (lc.length >= 2) multi2LineClearing++;
    // "equal top": >=2 line-clearing slots at the maximum line count -> a second slot the scalar
    // max cannot distinguish from the first. This is the precise structural blind spot.
    if (lc.length >= 2 && lc.filter(x => x === best).length >= 2) { equalTop++; sEqualTop++; }
    slotHist.set(slots.length, (slotHist.get(slots.length) ?? 0) + 1);

    if (o !== best) oursNeMultiBest++;
    if (o > best) oursGtMultiBest++;
    if (best > o) { multiBestGtOurs++; sMultiBestGtOurs++; }
    if ((o > 0) !== (best > 0)) availDisagree++;
    if (slots.length >= 2) hiddenCapacity += lc.reduce((a, x) => a + x, 0) - best;
  }
  perSession.push(`  ${s}: ${cc.length} boards | 2+ slots: ${sMulti2} | 2+ equal-top line-clearing: ${sEqualTop}`
    + ` | multi-best > scalar: ${sMultiBestGtOurs}`);
}

const histStr = [...slotHist.entries()].sort((a, b) => a[0] - b[0])
  .map(([k, v]) => `${k}:${v}`).join('  ');

console.log(`\n=== multi-slot differential over ${N} verified-prefix boards (${SESSIONS.length} sessions) ===\n`);
console.log(perSession.join('\n'));
console.log(`\nchain-length histogram (slots found per board):  ${histStr}`);
console.log(`\ncold-clear finds >=1 slot (any):            ${ccAnySlot}`);
console.log(`cold-clear finds >=1 LINE-CLEARING slot:    ${ccLineClearing}`);
console.log(`boards with 2+ slots in the chain:          ${multi2}`);
console.log(`  of those, 2+ that each clear a line:      ${multi2LineClearing}`);
console.log(`  of those, 2+ line-clearing at EQUAL top:  ${equalTop}   <- the scalar-max blind spot`);
console.log(`line-clears the scalar max drops (sum-max): ${hiddenCapacity}`);
console.log(`\n--- does multi ever change what the metric CONSUMES? ---`);
console.log(`scalar (bestTspinLines) != multi-best:      ${oursNeMultiBest}`);
console.log(`  scalar > multi-best (spins outside cold-clear's named shapes; not a multi issue): ${oursGtMultiBest}`);
console.log(`  multi-best > scalar (multi sees a bigger CURRENT-board spin):                     ${multiBestGtOurs}`);
console.log(`availability flips (ours>0 vs multi-best>0): ${availDisagree}`);
console.log('');

// THE GATE. The forecast metric consumes ONE number per board — `bestTspinLines`, a max over
// placements — and cross-tslot-count already pins it against cold-clear's single best detector.
// This pins the STRONGER statement multi-slot could threaten: our scalar is never BELOW what
// cold-clear's multi-slot cutout chain finds on the SAME board (`multi-best > scalar` must be 0).
// If it ever fires, multi-slot sees a bigger current-board spin than the scalar, the metric is
// reading a number lower than the board actually offers, and the "don't wire multi-slot in"
// decision would need re-opening. `equalTop` (2+ line-clearing slots sharing the top count) is
// the scalar-max blind spot's PRECONDITION and is reported, not gated: whether it yields a real
// false-negative needs the slot-LOCAL temporal analysis (a slot at j vs at k), which is a separate
// blocked item, not something this current-board differential can adjudicate.
if (multiBestGtOurs > 0) {
  console.error(`FAIL: multi-slot cutout saw a bigger current-board spin than the scalar on ${multiBestGtOurs} board(s). `
    + `The forecast metric consumes the scalar, so it would understate availability. Re-open the multi-slot decision.`);
  process.exit(1);
}
console.log(`ok — the scalar the metric consumes is never below cold-clear's multi-slot chain on any of ${N} boards; `
  + `multi-slot changes the path of exclusion, not the value (${equalTop} equal-top boards exist but move nothing).`);
