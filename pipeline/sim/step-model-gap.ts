/**
 * The one list of events the step model cannot attribute — see ROADMAP's
 * "`localiseMechanism` has no bucket for 'the clear opened the PATH'".
 *
 * `bestTspin` is a BFS from spawn, so its availability is REACHABILITY, not shape. The step model
 * (place -> clear -> insert garbage) asks which edit *formed* a slot, and has nowhere to put a clear
 * that removed the lid over a slot which already existed. Two events in 1789 localised records over
 * six sessions, 0 beyond the verified prefixes.
 *
 * WHY THIS FILE EXISTS AT ALL. It was two lists: `UNATTRIBUTED_STEP_MODEL_GAP` in
 * forecast-facts.test.ts (per player) and `CORPUS_UNATTRIBUTED_GAP` in forecast-corpus.test.ts
 * (per session, a sum of the same numbers). They agreed "by inspection" and each carried a comment
 * pointing at the other. That is one fact in two places with nothing keeping them in step — the
 * exact shape that let a claim bound live in a ledger, an emitter AND a mutation script until a
 * re-source moved it and only one of the three was checked. Both files import from here now, so a
 * third event is added once and both granularities move together.
 *
 * BOTH DIRECTIONS ARE ASSERTED, in each consumer: a session or player acquiring an unexplained
 * improvement fails, and a named entry that stops naming a real event fails too. A stale exception
 * excusing nothing is as bad as a missing one — the reciprocal `check_loo.py` keeps for ANNOTATED.
 *
 * ONLY HALF THE CLASS IS VISIBLE HERE, and that is not an oversight in this file. The 2026-08-09
 * event (`replay-2026-08-09-6.ttrm` r7 pinglamb lock 24, causing step 20) is filed `placement`
 * rather than `unattributed`, because a lock cell one row above the slot satisfies `touches` — so it
 * reaches no `unattributed` counter and cannot be pinned by session or player. It is pinned instead
 * by `ACCESS_CLASS` in forecast-access-class.test.ts, which keys on the measured property. Do not
 * "tidy" the two into one list: they pin different things, and this one alone would leave the
 * confidently-wrong half unguarded.
 */

/** Per session, per player. 2026-08-14 `replay-2026-08-14-0.ttrm` r4 (m1r5), lock 74, step 70. */
export const UNATTRIBUTED_STEP_MODEL_GAP: Record<string, Record<string, number>> = {
  '2026-08-14': { yachi: 1 },
};

/** The same events summed per session, for consumers that only see a session total. Derived, never
 *  written by hand — a hand-maintained mirror is what this file was created to delete. */
export const UNATTRIBUTED_BY_SESSION: Record<string, number> = Object.fromEntries(
  Object.entries(UNATTRIBUTED_STEP_MODEL_GAP)
    .map(([session, byUser]) => [session, Object.values(byUser).reduce((a, b) => a + b, 0)]),
);
