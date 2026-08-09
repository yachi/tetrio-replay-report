"""Perturb one datum in `facts`, evaluate, put it back — without copying the tree.

Two gates ask the same question: *if I change this one number, which claims flip?*
`claims/equiv.py` asks it 4 440 times per session (7 019 on 2026-07-22),
`check_rate_coverage.py` 324 times. Both used to answer it with

    m = copy.deepcopy(facts)
    m[...][...] = new_value

which rebuilds a 300-480 KB object graph to write a single integer. Profiling put 88 %
of `equiv.py` and 68 % of `check_rate_coverage.py` inside `copy.deepcopy` — 76.5 million
deepcopy calls to change 4 440 values.

The general instrument for "many versions of one structure" is persistence (Driscoll,
Sarnak, Sleator & Tarjan, *Making Data Structures Persistent*, JCSS 38(1) 1989), but
persistence is more than is needed: no caller here keeps a mutant after evaluating it.
The cheaper exact discipline is **make/unmake** — the undo log game-tree searchers have
used since Knuth & Moore's alpha-beta analysis (*Artificial Intelligence* 6(4) 1975).
Apply the write in place, evaluate, apply the inverse. O(1) per mutant instead of
O(|facts|), with identical semantics.

WHAT THIS TRADES AWAY, and the guard that buys it back
------------------------------------------------------
deepcopy cannot corrupt the original — that is its whole appeal, and giving it up is
the real cost of this module. An undo log that restores 4 439 of 4 440 sites leaves
every later mutant sitting on a wrong baseline, and the run still prints a plausible
coverage number. Nothing about the output would look wrong.

So the restore is not left to inspection. `unchanged()` fingerprints the tree, and both
callers assert over the whole sweep that the fingerprint they started with is the one
they end with. The assertion is in the code, not in a one-off manual check, because
this is precisely the failure mode that a passing test run would not show.

Two preconditions, both true of the callers and neither checked at runtime:

  * the code that runs inside the `with` must not mutate `facts` — it is `eval` of a
    pure comparison expression in both cases, and `unchanged()` catches a violation
    after the fact;
  * a write must name a container and a key that already exist, so the old value can be
    read back. Every site in both callers is an existing field.
"""
import hashlib
import json
from contextlib import contextmanager

__all__ = ["perturbed", "fingerprint", "unchanged"]


@contextmanager
def perturbed(writes):
    """Apply `(container, key, new_value)` writes in place; restore them on exit.

    `writes` is any iterable of triples where `container[key]` is already set —
    a dict and a str key, or a list and an int index, both work.

    Restoring in reverse order is what makes repeated writes to the same slot safe:
    the last write applied is the first undone, so the slot walks back to the value it
    held before the block rather than to some intermediate one. The callers do not
    currently write a slot twice, but a mutation operator that touched a field and then
    a field derived from it would, and the cost of ordering it correctly is nil.

    `finally` rather than a plain suffix: a predicate that raises mid-sweep must still
    leave the tree intact, and `equiv.py` deliberately runs predicates that raise
    (a mutation can break an index, which it scores as `None`).
    """
    undo = []
    try:
        for container, key, value in writes:
            undo.append((container, key, container[key]))
            container[key] = value
        yield
    finally:
        for container, key, old in reversed(undo):
            container[key] = old


def fingerprint(facts):
    """A stable digest of the whole tree, order-insensitive for dict keys."""
    return hashlib.sha256(
        json.dumps(facts, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def unchanged(facts, before):
    """True if `facts` still digests to `before`. See the module note on why this exists."""
    return fingerprint(facts) == before
