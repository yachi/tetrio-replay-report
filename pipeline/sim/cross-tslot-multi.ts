/**
 * MULTI-SLOT differential: does cold-clear's multi-slot cutout counting see anything our scalar
 * `bestTspin` (a max over placements) does not — and would any of it change the forecast metric?
 *
 * `cross-tslot-count.ts` differentials the LINE COUNT (our `bestTspinLines` vs cold-clear's
 * `cutout_tslot`) and finds 10,834 boards where both sides see a slot, 0 under-counts, and 6 false
 * negatives that the board itself explains (near-topout). That is a SCALAR-vs-SCALAR
 * check: both sides report one number, the best T-spin on the board. This script asks the next
 * question up — cold-clear's evaluator does not stop at the best slot, it cuts each slot out and
 * re-detects (standard.rs `Evaluator::evaluate`), so it counts a CHAIN of slots. The oracle now
 * emits that chain as `slots:[...]` under `CC_ORACLE_SLOTS=1`; here we compare it, per board, to
 * what our scalar sees.
 *
 * A CHAIN IS NOT A LIST OF COEXISTING SLOTS, and every comparison below turns on that. Each link
 * REPLACES the board (`cur = c.result`), and `cutout_tslot` hands back a continuation only after a
 * 2- or 3-line cut, so `slots[k]` for k>0 counts lines on a board from which k earlier spins have
 * already been cleared. Only `slots[0]` describes the board we passed in. Anything gated against
 * our scalar must therefore use `slots[0]`; `max(slots)` is a different quantity wearing the same
 * units, which is precisely the bug this file shipped with (see THE GATE at the bottom).
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
 * BOARD SOURCE: `runCaseOracle`, the vendored Triangle engine — the board source the published
 * forecast metric consumes, and the one `cross-tslot.test.ts` switched to on 2026-08-12. This file
 * was left on the hand-port `runCase` until 2026-08-17, so it saw 20,226 of the metric's 61,656
 * boards. Widening it is what brought the near-topout sanction (tslot-sanction.ts) into this gate:
 * at the hand-port's shorter prefix no board needed one, so a sanction here would have been
 * decorative — the widening and the sanction are one change, not two.
 *
 *   bun pipeline/sim/cross-tslot-multi.ts ./result/bin/cc-oracle
 */
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { bestTspinLines } from './forecast.ts';
import { classify } from './tslot-sanction.ts';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';

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
//
// `slots[0]` and `max(slots)` ARE NOT THE SAME KIND OF QUANTITY, and conflating them is what this
// gate did until 2026-08-17. The chain re-assigns the board on every link (`cur = c.result` in
// cc-oracle.rs), and `cutout_tslot` only returns a continuation after a 2- or 3-line cut — so link
// k>0 is measured on a board where k earlier spins have been executed AND their rows cleared.
// Only `slots[0]` is about the board we handed in. Comparing `max(slots)` against a current-board
// scalar is a category error that reads as a real finding, which is exactly how it fired.
let oursNeMultiBest = 0; // ours != max(slots)   (any divergence)
let oursGtMultiBest = 0; // ours >  max(slots)   (our BFS sees a spin outside cold-clear's named vocab)
let multiBestGtOurs = 0; // max(slots) > ours    REPORTED, NOT GATED — contaminated by later links
let firstGtOurs = 0;     // slots[0] > ours      THE GATE: the chain's first link, on the board as given
let nonMonotone = 0;     // max(slots) > slots[0]  a later link clears MORE than the first
// `slots[0]` is not `lines` under another name, and this counts how often. Reported, not gated:
// cross-tslot-count.ts is what pins `lines` against our scalar. It used to be a bare figure in the
// comment at the bottom, which is the shape this repo has been bitten by — a number nothing re-derives.
let firstNeLines = 0;    // slots[0] != cold-clear's raw six-detector max
let availDisagree = 0;   // (ours>0) != (max(slots)>0)   availability flip
let hiddenCapacity = 0;  // sum over multi boards of (sum(slots) - max(slots)): line-clears the scalar drops

const nonMonotoneWhere: string[] = [];
const firstGtWhere: string[] = [];        // the gate's failures, with the classification that let them through
const firstGtSanctioned: string[] = [];   // slots[0] > ours, tolerated, and why
const perSession: string[] = [];

for (const s of SESSIONS) {
  const ours: number[] = [];
  const boards: string[] = [];
  const cells: (number | null)[][][] = [];   // kept for the sanction, evaluated after the oracle answers
  const where: string[] = [];
  for (const c of loadCases(resolve('sessions', s))) {
    const r = runCaseOracle(c);
    const v = verifiedIndex(r, c.truth);
    for (let t = 0; t <= v; t++) {
      const b = (r.boards as unknown as Record<number, (number | null)[][]>)[t];
      if (!b) continue;
      ours.push(bestTspinLines(b as never));
      boards.push(b.map(row => row.map(x => (x === null ? '.' : 'X')).join('')).join('\n'));
      cells.push(b);
      where.push(`${s} ${c.file} r${c.round} ${c.user} board ${t}`);
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

  let sMulti2 = 0, sEqualTop = 0, sFirstGtOurs = 0, sNonMonotone = 0;
  for (let i = 0; i < cc.length; i++) {
    N++;
    const o = ours[i]!;
    const slots = cc[i]!.slots;
    const lc = slots.filter(x => x > 0);       // line-clearing slots in the chain
    const best = slots.length ? Math.max(...slots) : 0;
    const first = slots.length ? slots[0]! : 0; // the only link measured on the board as given

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
    if (best > o) multiBestGtOurs++;
    // THE GATE's arm, and it carries the same sanction as `cross-tslot-count.ts` — from the same
    // module, so the two can never again answer one question two ways. Applied ONLY where our scalar
    // is 0: there the board can explain the gap (no reachable T-spin at all on a near-topout stack,
    // where cold-clear matches column heights rather than reachable placements). Where our scalar is
    // positive and `slots[0]` is larger, that is a real under-count of the number the metric
    // consumes and nothing sanctions it.
    if (first > o) {
      const line = `${where[i]} slots=${JSON.stringify(slots)} cc-lines=${cc[i]!.lines} ours=${o}`;
      if (o === 0) {
        const sn = classify(cells[i]! as never);
        if (sn.sanctioned) firstGtSanctioned.push(`${line} stackTop=${sn.stackTop} anySpinLines=${sn.anySpinLines}: ${sn.reason}`);
        else { firstGtOurs++; sFirstGtOurs++; firstGtWhere.push(`${line} stackTop=${sn.stackTop} anySpinLines=${sn.anySpinLines}: ${sn.reason}`); }
      } else {
        firstGtOurs++; sFirstGtOurs++;
        firstGtWhere.push(`${line}  [both sides find a slot — no sanction applies]`);
      }
    }
    if (best > first) {
      nonMonotone++; sNonMonotone++;
      nonMonotoneWhere.push(`${where[i]}  slots=${JSON.stringify(slots)} cc-lines=${cc[i]!.lines} ours=${o}`);
    }
    if (first !== cc[i]!.lines) firstNeLines++;
    if ((o > 0) !== (best > 0)) availDisagree++;
    if (slots.length >= 2) hiddenCapacity += lc.reduce((a, x) => a + x, 0) - best;
  }
  perSession.push(`  ${s}: ${cc.length} boards | 2+ slots: ${sMulti2} | 2+ equal-top line-clearing: ${sEqualTop}`
    + ` | slots[0] > scalar (unsanctioned): ${sFirstGtOurs} | non-monotone chain: ${sNonMonotone}`);
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
console.log(`  multi-best > scalar (NOT current-board — see below):                              ${multiBestGtOurs}`);
console.log(`  slots[0] > scalar  (current-board; THIS is the gate):                             ${firstGtOurs} unsanctioned`
  + ` + ${firstGtSanctioned.length} sanctioned`);
for (const w of firstGtSanctioned) console.log(`    sanctioned: ${w}`);
console.log(`availability flips (ours>0 vs multi-best>0): ${availDisagree}`);
console.log(`chain's first link != cold-clear's raw six-detector max (slots[0] != lines): ${firstNeLines}`);
// REPORTED, NOT GATED, for the same reason `equalTop` is: this is a structural fact about the
// chain, not a defect. Clearing the first slot's rows drops the stack, which can leave a well that
// was 2 deep below the surface sitting 3 deep below the new one — so a later link legitimately
// clears more than the first. It is called out by name because a `max(slots)` reading of it looks
// exactly like a real scalar under-count, and did.
console.log(`\nchains where a LATER link clears more than the first: ${nonMonotone}`);
for (const w of nonMonotoneWhere) console.log(`  ${w}`);
console.log('');

// THE GATE. The forecast metric consumes ONE number per board — `bestTspinLines`, a max over
// placements — and cross-tslot-count already pins it against cold-clear's single best detector.
// This pins the statement multi-slot could threaten: our scalar is never BELOW what cold-clear's
// cutout finds on the board AS GIVEN. If it fires, the metric is reading a number lower than the
// board actually offers and the "don't wire multi-slot in" decision would need re-opening.
//
// IT IS `slots[0]`, NOT `max(slots)`, AND THE DIFFERENCE IS THE WHOLE POINT. This gate compared
// `max(slots)` from the day it was written until 2026-08-17, and that is a category error, not a
// stricter bound: the chain re-assigns the board on every link, so `max` can be a count from a
// board that has had two rows cleared out of it. Measured over all 61 656 boards — `slots[0] >
// ours` fires 6 times and every one is a near-topout board the shared sanction explains, while
// `max(slots) > ours` fires 8. The extra 2 are the non-monotone chains listed above (2026-08-09
// `replay-2026-08-09-6.ttrm` r6 yachi board 207 and 2026-08-14 `replay-2026-08-14-2.ttrm` r3 yachi
// board 12), both `slots=[2,3]` where cold-clear's OWN current-board answer is `lines: 2` — the
// same 2 our scalar reports. So cold-clear and this repo never disagreed about those boards at all;
// the gate was reading a post-clear continuation as if it described the input.
//
// Nor is `slots[0]` merely `lines` under another name — the chain picks by PRIORITY with cave and
// corner refinement, so it can select a placement the raw six-detector max does not. That count is
// printed above (`slots[0] != lines`) rather than left in this comment, where nothing re-derived it.
//
// `equalTop` (2+ line-clearing slots sharing the top count) is the scalar-max blind spot's
// PRECONDITION and is reported, not gated: whether it yields a real false-negative needs the
// slot-LOCAL temporal analysis (a slot at j vs at k), which is a separate blocked item, not
// something this current-board differential can adjudicate.
if (firstGtOurs > 0) {
  for (const w of firstGtWhere) console.error(`  UNSANCTIONED: ${w}`);
  console.error(`FAIL: cold-clear's cutout saw a bigger spin than the scalar on the board AS GIVEN, on ${firstGtOurs} board(s), `
    + `and the board does not explain it. `
    + `The forecast metric consumes the scalar, so it would understate availability. Re-open the multi-slot decision.`);
  process.exit(1);
}
console.log(`ok — the scalar the metric consumes is never below cold-clear's cutout on the board as given, on any of ${N} boards `
  + `that the board itself does not explain (${firstGtSanctioned.length} near-topout board(s) sanctioned above); `
  + `multi-slot changes the path of exclusion, not the value (${equalTop} equal-top boards exist but move nothing, `
  + `and the ${nonMonotone} non-monotone chain(s) are measured on post-clear continuations, not on the input).`);
