"""Spec idioms that several ledgers need, each with its equivalence argument.

These exist because the algebra is deliberately conjunctive (see spec.py) and the
statements below are the ones whose conjunctive form is not obvious — "the maximum is
V" most of all. Writing them once means the argument for *why* the conjunctive form is
the same predicate lives in one place instead of being re-derived, differently, in
every session module.

The rule every idiom here follows: **do not name a round the claim's sentence does not
name.** Pinning an argmax round would make the lemma prove something stronger than the
sentence it is attached to, and a badge that proves more than its sentence is as much a
drift as one that proves less.
"""
from .spec import (add, c_dur, c_field, conj, count_rounds, eq, ge_, lit)


def pp_count(pl_a, pl_b, f, op, v):
    """How many PLAYER-ROUNDS satisfy `f op v` — the two players' counts added.

    `count_rounds` counts rounds, and a round holds two player data points. A round
    where both players clear the bar must count twice, which is exactly what the sum
    does: |{(r,pl) : P(r,pl)}| = |{r : P(r,a)}| + |{r : P(r,b)}|.
    """
    return add(count_rounds(c_field(pl_a, f, op, v)),
               count_rounds(c_field(pl_b, f, op, v)))


def max_over_players(pl_a, pl_b, f, v):
    """max over every (round, player) of `f` == v.

    A maximum is two independent facts and this is both of them:
        nothing exceeds v      count of (r,pl) with f > v  == 0
        something attains v    count of (r,pl) with f == v >= 1
    Together those are equivalent to `max(...) == v` for any non-empty set, which is
    what makes this a translation rather than a re-statement. Note the second is `>= 1`
    and not `== 1`: `max` says nothing about how many rounds tie for it, and demanding
    uniqueness would prove more than the sentence.
    """
    return conj(eq(pp_count(pl_a, pl_b, f, ">", v), lit(0)),
                ge_(pp_count(pl_a, pl_b, f, "==", v), lit(1)))


def min_over_players(pl_a, pl_b, f, v):
    """min over every (round, player) of `f` == v. The mirror of max_over_players."""
    return conj(eq(pp_count(pl_a, pl_b, f, "<", v), lit(0)),
                ge_(pp_count(pl_a, pl_b, f, "==", v), lit(1)))


def max_for(pl, f, v):
    """max over the session of ONE player's `f` == v."""
    return conj(eq(count_rounds(c_field(pl, f, ">", v)), lit(0)),
                ge_(count_rounds(c_field(pl, f, "==", v)), lit(1)))


def dur_max(v):
    """The longest round of the session lasted exactly v ms.

    Round duration is the larger of the two players' `lifetime`, which `c_dur` renders
    identically to the `dur` expression (one helper per backend), so "no round is
    longer" and "this round is that long" cannot disagree about what a round's length
    is.
    """
    return conj(eq(count_rounds(c_dur(">", v)), lit(0)),
                ge_(count_rounds(c_dur("==", v)), lit(1)))


def dur_min(v):
    """The shortest round of the session lasted exactly v ms."""
    return conj(eq(count_rounds(c_dur("<", v)), lit(0)),
                ge_(count_rounds(c_dur("==", v)), lit(1)))
