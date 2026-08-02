/**
 * Faithful port of halp1/triangle's garbage queue, replacing sim.ts's flattened `pending`
 * list and its scalar knobs.
 *
 * Ported rather than approximated because the knobs produced an unresolvable conflict:
 * `cancelMode:'inTransit'` fixed received-garbage totals (exact 11/21 -> 15/21 on a fixed
 * cohort) while wrecking attack coverage (17.9% -> 12.4%). Cancellation could not
 * simultaneously explain how much garbage landed and how much attack got through, which
 * means no setting of those knobs expressed the real rule.
 *
 * The real rule, from src/engine/index.ts and src/engine/garbage/legacy.ts:
 *
 *  - On `interaction`, garbage is queued with frame = MAX_SAFE_INTEGER - speed. tank()'s
 *    readiness test is `item.frame + speed > frame`, so an unconfirmed entry is NEVER
 *    insertable — but cancel() ignores frame entirely, so it CAN still be cancelled.
 *    That asymmetry is the thing the scalar knobs could not express.
 *  - On `interaction_confirm`, confirm(iid, gameid, frame) rewrites the entry's frame to the
 *    confirm event's frame. Insertion timing therefore counts from confirmation, and the
 *    queue is re-sorted by frame, so confirmation can REORDER it.
 *  - cancel() decrements the head entry one line at a time; the remainder is what gets sent.
 *  - tank() fills up to a cap per call, splitting the head entry when it would overflow.
 *
 * Measured in this dataset: confirm delay is median 8 frames (mean 8.5, max 44), and only
 * 1 of 2209 interactions is never confirmed — so the never-insert rule is nearly inert here,
 * but the delay is not.
 */

export interface QueueEntry {
  frame: number;        // MAX_SAFE_INTEGER - speed until confirmed, then the confirm frame
  amount: number;
  size: number;         // hole width
  x: number;            // hole column as transmitted
  cid: number;          // stored from the event's iid, matching triangle
  gameid: number;
  confirmed: boolean;
}

export interface TankResult { amount: number; x: number; size: number }

export class GarbageQueue {
  queue: QueueEntry[] = [];
  /** running total of attack actually sent after cancellation, as triangle tracks it */
  sent = 0;

  constructor(private speed: number, private absoluteCap = Number.MAX_SAFE_INTEGER) {}

  get size() { return this.queue.reduce((a, g) => a + g.amount, 0); }

  /** queue an incoming attack; unconfirmed entries sort to the end and cannot be tanked */
  receive(e: Omit<QueueEntry, 'frame' | 'confirmed'>) {
    if (e.amount <= 0) return;
    this.queue.push({ ...e, frame: Number.MAX_SAFE_INTEGER - this.speed, confirmed: false });
    // absolute cap trims from the BACK (newest), not the front
    let total = this.size;
    while (total > this.absoluteCap && this.queue.length) {
      const excess = total - this.absoluteCap;
      const last = this.queue[this.queue.length - 1]!;
      if (last.amount <= excess) { total -= last.amount; this.queue.pop(); }
      else { last.amount -= excess; total -= excess; }
    }
  }

  /** server confirmation: makes the entry insertable, timed from `frame` */
  confirm(cid: number, gameid: number, frame: number): boolean {
    const obj = this.queue.find(g => g.cid === cid && g.gameid === gameid);
    if (!obj) return false;
    obj.frame = frame;
    obj.confirmed = true;
    return true;
  }

  /**
   * Offset an outgoing attack against the queue. Returns what is left to send.
   * Deliberately ignores `frame`: unconfirmed, un-insertable garbage is still cancellable.
   */
  cancel(amount: number): number {
    let send = amount;
    while (send > 0 && this.queue.length > 0) {
      const head = this.queue[0]!;
      head.amount--;
      if (head.amount <= 0) this.queue.shift();
      send--;
    }
    this.sent += send;
    return send;
  }

  /** Insert up to `cap` lines whose travel time has elapsed. `hard` = called from a lock. */
  tank(frame: number, cap: number, hard: boolean): TankResult[] {
    if (!this.queue.length) return [];
    this.queue.sort((a, b) => a.frame - b.frame);
    const res: TankResult[] = [];
    let total = 0;
    while (total < cap && this.queue.length > 0) {
      const head = this.queue[0]!;
      // the reference uses `frame - 1` for a soft tank; an unconfirmed entry's frame is
      // MAX_SAFE_INTEGER - speed, so this test can never pass for it
      if (head.frame + this.speed > (hard ? frame : frame - 1)) break;
      let take = head.amount;
      total += take;
      if (total > cap) { const excess = total - cap; take -= excess; head.amount = excess; }
      else this.queue.shift();
      if (take > 0) res.push({ amount: take, x: head.x, size: head.size });
    }
    return res;
  }
}
