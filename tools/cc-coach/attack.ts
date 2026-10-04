// TETR.IO attack for one lock, through the vendored reference engine's own garbageCalcV2.
import { garbageCalcV2 } from '../../pipeline/sim/vendor/teto/engine/utils/damageCalc/index.mjs';
export interface Ctr { b2b: number; combo: number }
// Advance TETR.IO's counters exactly as engine/index.mjs does, then price the lock. `spin` is
// 'none' | 'mini' | 'normal'. Returns the attack BEFORE the all-clear bonus (which TETR.IO emits
// as a separate event), plus that bonus, so callers can report both.
export function priceLock(ctr: Ctr, lines: number, spin: string, piece: string, pc: boolean, opts: any): { attack: number; pcBonus: number; ctr: Ctr } {
  let { b2b, combo } = ctr;
  if (lines > 0) {
    combo++;
    if ((spin !== 'none') || lines >= 4) b2b++;
    else b2b = -1;
  } else combo = -1;
  const g = garbageCalcV2({ b2b: Math.max(b2b, 0), combo: Math.max(combo, 0), enemies: 0, lines, piece: piece.toLowerCase(), spin },
    { spinBonuses: opts.spinbonuses ?? 'T-spins', comboTable: opts.combotable ?? 'multiplier', garbageTargetBonus: opts.garbagetargetbonus ?? 'none',
      b2b: { chaining: opts.b2bchaining ?? true, charging: false } });
  const attack = g.garbage > 0 ? Math.floor(g.garbage * (opts.garbagemultiplier ?? 1)) : 0;   // roundmode 'down'
  return { attack, pcBonus: pc && lines > 0 ? (opts.allclear_garbage ?? 10) : 0, ctr: { b2b, combo } };
}
