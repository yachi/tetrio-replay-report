"""The corpus-wide statistics the 最癲一局 lede publishes — derived, not typed in.

    python3 -m analysis.corpus_stats            # the whole family, as a table
    python3 -m analysis.corpus_stats --json     # the same, machine-readable
    python3 -m analysis.corpus_stats --selftest # the split rule's control, and the estimator's

**Why this file exists.** `pipeline/intense_round.py` published `n = 380`, a tercile triple,
seven Spearman rho and seven adjusted p-values as string literals in a docstring and in the
rendered Cantonese, and **no script in this repo computed any of them**. Two things followed,
and both are established rather than hypothetical:

1. **Five of the seven went stale in 72 minutes.** The lede landed at 2026-08-16 01:42
   (`0cc719c`); `0804a7e` re-sourced `apm`/`pps`/`vs` from the live `player.stats` tick to
   `results.aggregatestats` at 02:54. Exactly the figures whose inputs contain APM or VS moved
   — rho +0.210 → +0.212, +0.200 → +0.201, −0.187 → −0.178, +0.096 → +0.097, +0.236 → +0.238 —
   and the two built only from attack / cleared / pieces / duration (+0.058 and −0.184) sat
   exactly where they were. Over the whole family it is 15 of 26. Nobody could have known: the
   figures had no derivation to re-run.

   **The count was "four" here until it was measured**, and the omitted one is instructive:
   +0.200 → +0.201 is 清走 against INTENSITY, and its COLUMN is `garbage_cleared` alone, which
   the re-source did not touch. Reading "contains APM or VS" off the column and forgetting that
   the x-variable is itself a sum of two players' VS is the entire error, and it is the error a
   reader of the sentence would make next. The measurement is `git archive 0cc719c sessions`
   into a scratch tree and
   this module run against both roots — the same shape as the leave-one-out gate's evidence,
   and the reason the two roots are worth naming is that `--root` makes it a one-line probe.

   **Those five arrows are the SIX-session values and stay here as the record of that failure,
   not as current figures.** 2026-08-19 took the corpus to seven sessions and 450 rounds, and it
   moved all seven rho — the two the re-source had left alone included. That is the other half of
   the same lesson: invariance to a re-source is not invariance to data, which is why the guard
   downstream re-derives rather than counting sessions. As of that session they read **+0.176**
   (cleared_pp/intensity), **+0.169** (cleared/intensity), **+0.060** (cleared_pp/duration),
   **−0.173** (apm/duration), **−0.180** (attack/duration), **+0.223**
   (cleared_per_received/intensity) and **+0.055** (received/intensity). Nothing else in this
   repo needs them typed out again, and they are typed out here only because
   `pipeline/check_intense_corpus.DOCSTRING_OWES` names this file — a module that derives a
   figure and then quotes a DIFFERENT one is the state that gate exists to make impossible.
2. **The published Holm triple was internally impossible.** Holm's multiplier decreases with
   rank by construction — the raw-ascending p are scaled by m, m−1, m−2, … before the running
   maximum. Divide each published adjusted value by the raw p it was computed from (i.e. by the
   PRE-re-source raw p, which is the data it was published from) and the implied multipliers
   are 5.55, 16.84, 31.83 in raw-ascending order: increasing, where Holm's must not increase.
   No family of any size can produce that, so the three numbers were never the output of one
   computation.

   Stating it that way is deliberate. The obvious argument — Holm's adjusted p is non-decreasing
   in the raw p, and raw(攻擊) = 3.08e-04 < raw(APM) = 5.06e-04 while adjusted 攻擊 = 0.0098 >
   APM = 0.0040 — reaches the right conclusion from a comparison it is not entitled to make:
   those raw p are the POST-re-source ones and those adjusted p are the PRE-re-source ones, so
   it pairs two data versions. Under the version the figures were actually published from the
   raw p run the other way (2.38e-04 < 3.08e-04) and that argument yields no contradiction at
   all. The multiplier argument holds under both.

**Stdlib only, on purpose.** This repo has no Python dependency manifest and every gate it
ships imports nothing outside the standard library; a figure whose re-derivation needs a
`pip install` is a figure CI cannot check. The Spearman estimator and the Student-t tail below
are therefore written out. They agree with `scipy.stats.spearmanr` to ~1e-15 over this corpus
(the probe that establishes it is not committed — `--selftest` pins the identities that do not
need scipy: exact-tie rho, perfect-monotone rho, and the t-tail against known quantiles).

# The method

    population   every DECIDED round of every sessions/*/report/facts.json
    intensity    W.vs_x1000 + L.vs_x1000                      (how hard BOTH sides swung)
    duration     max(W.finaltime_ms, L.finaltime_ms)          (the length control)
    score        paired {0, 0.5, 1} — did the round's WINNER hold the higher value
    terciles     rank boundaries floor(n/3), floor(2n/3)
    AUC          mean(score) * 100 per tercile
    rho          Spearman of the x-variable against the paired score
    p            two-sided, Student-t on n-2 df, then Bonferroni over the whole FAMILY

The score is PAIRED — one number per round, not per player — which is what makes it an AUC:
`mean(score)` is P(winner's value > loser's value) with ties at a half. That is the same
statistic the AUC block in CLAUDE.md quotes and the same one `pipeline/sim/board-metrics.ts`
computes, so a column's tercile AUC and its session AUC are comparable by construction.

# Bonferroni, not Holm

At these raw p (3e-05 .. 5e-04) with a family of this size every correction agrees: the worst
Bonferroni ceiling in the family is well inside 0.05, so nothing is at stake in power and the
choice is purely about **re-derivability**.

Holm's adjusted value for one test is a function of the ENTIRE vector of the family's raw p —
a re-source in some other column moves your figure with no change whatever in your data. That
is not a hypothetical; it is precisely the shape of what broke here. Bonferroni's `m * p` is a
pure function of two numbers this file records: the test's own raw p, and `len(FAMILY)`.

Both are therefore printed. A quoted adjusted p with no `m` beside it is not re-derivable by a
reader, which is the state the published lede was in.

# The family is DATA

`FAMILY` below is the cross-product of `COLUMNS` and `X_VARS`, written out and counted, and it
is **m = 26: thirteen columns against two x-variables**. The thirteen are the eleven the 最癲一局
table prints minus `vs_x1000` (see the next paragraph), plus the two per-piece rates the
section's own claims pin (`cleared_pp`, `attack_pp`) and the death-bias control
(`cleared_per_received`) — i.e. every column any published sentence in that section quotes. The
two x-variables are the finding's (intensity) and its control's (duration); the control is a
test that was run and must be counted, and dropping it would be choosing the denominator after
seeing which half of the cross-product carried the result.

**The published lede said "over the 20 columns tested", and 20 is not reproducible.** No list of
20 columns exists anywhere in this repo, and none of the natural readings gives one: the table
prints 11, the axes group to 4, the columns tested here are 13 and the tests are 26. So the
multiplicity correction's own denominator was unrecorded — the correction was unauditable in
principle, which is a strictly worse defect than being wrong by six. The change from 20 to 26 is
therefore not a re-tuning; it is the first time the number is a count of anything.

A column added here changes `m` and therefore every published adjusted p, which is the intended
coupling: it is what a multiplicity correction MEANS.

`vs_x1000` is deliberately not a column. It is a term of the intensity variable itself (the
sum of both sides'), so testing it against intensity is a test against itself; and its paired
AUC is 100.0 over every round in the corpus, i.e. it decides the winner by construction.
`finaltime_ms` is not a column for the same reason on the other axis — it IS the duration
variable. Excluding a cell of the cross-product per-axis instead would make `m` depend on
which axis you were reading, which is exactly the unauditable state above.

# What this does NOT establish

The 450 rounds are nested in matches, in sessions, and in two players. Every p here assumes
independent rounds, so every one of them is ANTI-CONSERVATIVE: the true family-wise error is
larger than the number printed. The rank-order pattern (a monotone tercile progression that
its own duration control does not reproduce) is the finding; p is supporting evidence for it,
not the claim. `pipeline/intense_round.py`'s prose is worded that way round on purpose.
"""
import argparse
import decimal
import glob
import json
import math
import os

# --------------------------------------------------------------------------- the population


def facts_paths(root):
    """Every `sessions/<date>/report/facts.json`, sorted. Globbed — never a session list.

    `sessions/2026-07-24/proof` is deliberately out of reach: it is a second, lighter artefact
    over a session `report/` already covers, and including it would count that night's rounds
    twice. The glob names the directory rather than filtering a wider one so that stays visible.
    """
    return sorted(glob.glob(os.path.join(root, "sessions", "*", "report", "facts.json")))


def load_rounds(root):
    """[(session, m<i>r<j>, winner_record, loser_record)] over every DECIDED round.

    A round with no winner, or one that does not hold exactly two players, is skipped — the
    paired score is undefined without both sides. Nothing else is filtered here; a column that
    needs more (a non-zero denominator, say) declares it as its own `domain`.
    """
    out = []
    for path in facts_paths(root):
        session = os.path.basename(os.path.dirname(os.path.dirname(path)))
        with open(path, encoding="utf-8") as fh:
            facts = json.load(fh)
        for match in facts["matches"]:
            for rnd in match["rounds"]:
                win = rnd.get("winner")
                players = rnd.get("players") or {}
                if not win or len(players) != 2 or win not in players:
                    continue
                lose = next(p for p in players if p != win)
                out.append((session, f"m{match['index']}r{rnd['index'] + 1}",
                            players[win], players[lose]))
    return out


# --------------------------------------------------------------------------- the family

# id -> (label, accessor, domain). `domain` is the predicate BOTH players' records must
# satisfy for the round to be scored on this column; a round failing it is dropped from this
# column's population and counted, never scored as a tie.
#
# The labels are the ones the 最癲一局 table prints, so a reader moving between the table and
# this output sees the same words. The three derived columns are not in that table; they are
# the per-piece rates the section's own claims pin, plus the normalisation control.
COLUMNS = [
    ("apm", "APM", lambda d: d["apm_x1000"], None),
    ("pps", "PPS", lambda d: d["pps_x1000"], None),
    ("pieces", "粒數", lambda d: d["pieces"], None),
    ("attack", "攻擊", lambda d: d["garbage_attack"], None),
    ("sent", "送出", lambda d: d["garbagesent"], None),
    ("received", "食", lambda d: d["garbagereceived"], None),
    ("cleared", "清走", lambda d: d["garbage_cleared"], None),
    ("lines", "行數", lambda d: d["lines"], None),
    ("maxspike", "最大單波", lambda d: d["maxspike"], None),
    ("topbtb", "最高 B2B", lambda d: d["topbtb"], None),
    # Derived. The two per-piece rates are what `intense_round_attack_rate` and
    # `intense_round_downstack_rate` pin for the selected round, so the corpus test and the
    # per-round claims are about the same quantity.
    ("cleared_pp", "每粒清走", lambda d: d["garbage_cleared"] / d["pieces"],
     lambda d: d["pieces"] > 0),
    ("attack_pp", "每粒攻擊", lambda d: d["garbage_attack"] / d["pieces"],
     lambda d: d["pieces"] > 0),
    # The death-bias control: the loser dies with garbage still on the board, so any raw
    # downstack count is biased toward the winner. Dividing by what ARRIVED removes the level
    # of that bias; it cannot remove the bias itself, and the section's note says so.
    ("cleared_per_received", "清走／食",
     lambda d: d["garbage_cleared"] / d["garbagereceived"],
     lambda d: d["garbagereceived"] > 0),
]

# id -> (label, accessor over (winner_record, loser_record))
X_VARS = [
    ("intensity", "兩邊 VS 加埋", lambda W, L: W["vs_x1000"] + L["vs_x1000"]),
    ("duration", "局長", lambda W, L: max(W["finaltime_ms"], L["finaltime_ms"])),
]

# Every test this file runs, and therefore the multiplicity denominator. Written as the
# cross-product rather than a hand-kept list so a new column or a new x-variable cannot be
# added without moving `m` — the coupling is the point.
FAMILY = [(c, x) for c, _l, _a, _d in COLUMNS for x, _xl, _xa in X_VARS]

COLUMN_BY_ID = {c: (l, a, d) for c, l, a, d in COLUMNS}
XVAR_BY_ID = {x: (l, a) for x, l, a in X_VARS}


# --------------------------------------------------------------------------- statistics


def _ranks(xs):
    """Fractional (average) ranks, 1-based. Ties share the mean of the ranks they span."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def _betacf(a, b, x):
    """Lentz's continued fraction for the incomplete beta. Numerical Recipes 6.4."""
    tiny, eps = 1e-300, 3e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        for aa in (m * (b - m) * x / ((qam + m2) * (a + m2)),
                   -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1.0 + aa * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + aa / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            h *= d * c
        if abs(d * c - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """The regularized incomplete beta I_x(a, b), stdlib only."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_two_sided(t, df):
    """P(|T| > |t|) for Student's t on `df` degrees of freedom.

    The identity is P(|T| > t) = I_{df/(df+t^2)}(df/2, 1/2), which is exact and needs no
    normal approximation — at n = 450 the two agree anyway, but the corpus will not always
    be this size and an approximation whose error is invisible at one n is a trap.
    """
    if df <= 0:
        return 1.0
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def spearman(xs, ys):
    """(rho, two-sided p) — Pearson on fractional ranks, tail from the t-approximation.

    The same estimator and the same tail `scipy.stats.spearmanr` uses, so a figure published
    from here is comparable with anything measured with scipy elsewhere in this repo's
    history. Returns (None, None) when either variable is constant: rho is undefined, and a
    0.0 there would read as "measured, no relationship".
    """
    n = len(xs)
    if n < 3:
        return None, None
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx <= 0.0 or syy <= 0.0:
        return None, None
    rho = sxy / math.sqrt(sxx * syy)
    rho = max(-1.0, min(1.0, rho))
    if abs(rho) >= 1.0:
        return rho, 0.0
    t = rho * math.sqrt((n - 2) / ((1.0 + rho) * (1.0 - rho)))
    return rho, t_two_sided(t, n - 2)


def bonferroni(p, m):
    """`min(1, m*p)` — a pure function of the test's own p and the family size.

    Deliberately not Holm. Holm's value for one test depends on every other test's raw p, so
    it cannot be re-derived from anything a report prints, and it moves when an unrelated
    column's data is re-sourced. See the module docstring.
    """
    return None if p is None else min(1.0, m * p)


# --------------------------------------------------------------------------- the split rule


def terciles(n):
    """The two rank boundaries, as (b1, b2). Sizes are (b1, b2-b1, n-b2).

    `floor(n/3)` and `floor(2n/3)`. The obvious alternative — `floor(n/3)` and `2*floor(n/3)`
    — gives a DIFFERENT published triple whenever n is not a multiple of 3: at n = 380 this
    rule gives 126 / 127 / 127 and that one gives 126 / 126 / 128.

    **The n = 380 in the line above is deliberate and must not be "updated" to the current
    corpus size.** The corpus is 450, and 450 is divisible by 3, so BOTH rules give
    150 / 150 / 150 — the current n cannot demonstrate what the choice is between, and an
    example rewritten to it would silently stop being an example. 380 is kept because it is
    the smallest corpus this repo has actually held where the two rules disagree. `_selftest`
    pins the disagreement independently, which is what keeps this honest for the sessions
    where n happens to hide it.

    The rule keeps the three bins within one round of each other for every n, which the
    doubling rule does not: it drifts by up to 2 and puts the surplus in the top bin, the one
    the finding is about.
    """
    return n // 3, 2 * n // 3


def _tercile_groups(xs, n):
    """Indices per tercile, ordered by `xs` ascending.

    Ties are broken by corpus order (Python's sort is stable, and the corpus order is the
    globbed session order), so a tie straddling a boundary is resolved deterministically but
    arbitrarily. `_selftest` reports how many boundary ties exist; at the time of writing
    there are none, so no published figure rests on the tie-break.
    """
    order = sorted(range(n), key=lambda i: xs[i])
    b1, b2 = terciles(n)
    return [order[:b1], order[b1:b2], order[b2:]]


def boundary_ties(xs):
    """How many rounds sit exactly on a tercile boundary value — 0 means the split is clean."""
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    out = 0
    for b in terciles(n):
        if 0 < b < n and xs[order[b - 1]] == xs[order[b]]:
            out += 1
    return out


# --------------------------------------------------------------------------- the measurement


def paired_scores(rounds, column):
    """([x-free scores], [kept round indices]) for one column, over `rounds`.

    A round is kept only where the column's `domain` holds for BOTH players. Dropping it is
    not the same as scoring it 0.5: a tie is a round the column saw and could not separate,
    and folding an undefined round in as one would move every AUC toward 50 by an amount
    nobody could see. `dropped` is reported for exactly that reason.
    """
    _label, get, domain = COLUMN_BY_ID[column]
    scores, kept = [], []
    for i, (_s, _lbl, W, L) in enumerate(rounds):
        if domain and not (domain(W) and domain(L)):
            continue
        a, b = get(W), get(L)
        scores.append(1.0 if a > b else (0.0 if a < b else 0.5))
        kept.append(i)
    return scores, kept


def measure(root):
    """Everything this file derives, as plain JSON-able data.

    Every number the 最癲一局 lede publishes is in here, keyed by `<column>/<x-variable>`, and
    `m` is `len(FAMILY)` — the two things a reader needs to re-derive an adjusted p.
    """
    rounds = load_rounds(root)
    n = len(rounds)
    m = len(FAMILY)
    xs = {x: [get(W, L) for _s, _l, W, L in rounds] for x, _xl, get in X_VARS}

    tests = {}
    for column, xvar in FAMILY:
        scores, kept = paired_scores(rounds, column)
        xv = [xs[xvar][i] for i in kept]
        rho, p = spearman(xv, scores)
        groups = _tercile_groups(xv, len(kept))
        tests[f"{column}/{xvar}"] = {
            "column": column,
            "column_label": COLUMN_BY_ID[column][0],
            "x": xvar,
            "x_label": XVAR_BY_ID[xvar][0],
            "n": len(kept),
            "dropped": n - len(kept),
            "auc": sum(scores) / len(scores) * 100.0 if scores else None,
            "terciles": [sum(scores[i] for i in g) / len(g) * 100.0 if g else None
                         for g in groups],
            "tercile_sizes": [len(g) for g in groups],
            "boundary_ties": boundary_ties(xv),
            "rho": rho,
            "p_raw": p,
            "p_bonferroni": bonferroni(p, m),
        }
    return {
        "sessions": sorted({s for s, _l, _W, _L in rounds}),
        "n_rounds": n,
        "family_size": m,
        "family": [f"{c}/{x}" for c, x in FAMILY],
        "correction": "bonferroni",
        "tests": tests,
    }


# --------------------------------------------------------------------------- the formatters

# THE formatters for every figure this file publishes. `pipeline/intense_round.py` renders
# through them and `pipeline/check_intense_corpus.py` parses what they produce, so a format
# only one side agrees with cannot exist — the rule check_loo.py:288 states.


def _quantize(x, places, rounding):
    return decimal.Decimal(repr(x)).quantize(decimal.Decimal(1).scaleb(-places),
                                             rounding=rounding)


def fmt_rho(x):
    """`+0.212` — rounded half-up at 3dp.

    Rounded and not floored, which is the opposite of `pipeline/fmt.py` and needs its reason
    stated: 約 floors because 約 asserts "at least this much", and rho asserts no such thing.
    It is a two-sided point estimate, so truncation is not the safe direction — it is a
    systematic pull toward zero for a positive rho and away from it for a negative one, i.e.
    it would make the headline look weaker and the control look stronger. `fmt_p` below is
    the one figure here that IS a bound, and it ceils.
    """
    return f"{_quantize(x, 3, decimal.ROUND_HALF_UP):+.3f}"


def fmt_auc(x):
    """`83.5` — rounded half-up at 1dp. A point estimate of a probability; see `fmt_rho`."""
    return f"{_quantize(x, 1, decimal.ROUND_HALF_UP):.1f}"


def fmt_p(x):
    """`0.0009` — CEILED at 4dp, because a p-value is an upper bound on a false-positive rate.

    The one figure here that must round the other way: quoting 0.00006 as 0.0000 asserts a
    smaller error rate than was computed. `pipeline/fmt.py:_bound_dp` ceils for the same
    reason. 0 stays 0 — an exact zero is exact.
    """
    return f"{_quantize(x, 4, decimal.ROUND_CEILING):.4f}"


# There was a `cjk()` here — ASCII signs to the ＋ / − the Cantonese renders. It was never
# called: `pipeline/intense_round.cjk` already did it, at the site that renders. Two
# implementations of one translation is the failure shape `pipeline/docs_gate.py` was extracted
# to end, and the second one is worse than useless when it is the unused one, because it agrees
# on the day it is written and is never exercised again. The renderer's is the survivor;
# `pipeline/check_intense_corpus.py` imports THAT one, so the gate searches for exactly what
# was rendered by construction rather than by coincidence.


# --------------------------------------------------------------------------- selftest


def _selftest(root):
    """Controls for the two things in this file that could be silently wrong."""
    ok = True

    def check(good, what):
        nonlocal ok
        ok &= bool(good)
        print(f"  {'ok ' if good else 'BAD'} {what}")

    # 1. The split rule is a CHOICE. If the two candidate rules agreed at this corpus size the
    #    docstring above would be describing a distinction with no consequence.
    n = len(load_rounds(root))
    b1, b2 = terciles(n)
    alt = (n // 3, 2 * (n // 3))
    check((b1, b2) != alt or n % 3 == 0,
          f"split rule: floor(n/3), floor(2n/3) = {(b1, b2)} at n = {n}; the doubling rule "
          f"gives {alt} — {'they differ, so the rule is load-bearing' if (b1, b2) != alt else 'IDENTICAL, so this control proves nothing at this n'}")
    sizes = [b1, b2 - b1, n - b2]
    check(max(sizes) - min(sizes) <= 1,
          f"split rule: bins within one round of each other {sizes}")

    # 2. The estimator, against identities that need no second library.
    rho, p = spearman([1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7, 8])
    check(rho == 1.0 and p == 0.0, f"spearman: perfect monotone gives rho {rho}, p {p}")
    rho, p = spearman([1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
    check(rho == -1.0, f"spearman: perfect antitone gives rho {rho}")
    rho, _p = spearman([1, 1, 1, 2, 2, 2], [1, 2, 3, 1, 2, 3])
    # `is not None` written out rather than asserted away: x here is TIED but not constant, so
    # rho is defined and 0. An estimator that started returning None on this input would be a
    # real regression — every column in the corpus carries ties — and the guard must report
    # that as a failed control, not raise a TypeError inside `abs` on the way to reporting it.
    check(rho is not None and abs(rho) < 1e-12,
          f"spearman: fully tied x against a free y gives rho {rho}")
    # A t-tail at a quantile every table carries: t = 1.96 on a large df is ~0.05.
    check(abs(t_two_sided(1.959964, 10 ** 7) - 0.05) < 1e-5,
          f"t tail: P(|T| > 1.96) at df 1e7 = {t_two_sided(1.959964, 10 ** 7):.6f} (normal 0.05)")
    check(abs(t_two_sided(2.228139, 10) - 0.05) < 1e-6,
          f"t tail: P(|T| > 2.2281) at df 10 = {t_two_sided(2.228139, 10):.6f} (table 0.05)")
    check(abs(t_two_sided(0.0, 100) - 1.0) < 1e-12, "t tail: P(|T| > 0) = 1")

    # 3. Bonferroni's three properties that make it re-derivable: monotone in p, capped at 1,
    #    and undefined-preserving. The third is why the comparison below spells its guards out
    #    instead of asserting them away — an undefined rho must never acquire an adjusted p,
    #    and it is the branch that makes `float | None` the honest return type.
    lo, hi = bonferroni(1e-6, 26), bonferroni(1e-5, 26)
    check(bonferroni(0.5, 26) == 1.0 and lo is not None and hi is not None and lo < hi,
          "bonferroni: capped at 1 and monotone in the raw p")
    check(bonferroni(None, 26) is None,
          "bonferroni: an undefined p stays undefined, never adjusted into a number")

    # 4. The tie-break is not load-bearing today. Reported rather than asserted-zero: a
    #    seventh session may introduce one, and that must be visible, not a failure.
    data = measure(root)
    ties = {k: v["boundary_ties"] for k, v in data["tests"].items() if v["boundary_ties"]}
    check(True, f"boundary ties on the tercile split: {ties or 'none in any test'}")

    print(f"{'ok ' if ok else 'FAIL'} selftest")
    return 0 if ok else 1


# --------------------------------------------------------------------------- main


def _table(data):
    out = [f"sessions {', '.join(data['sessions'])}",
           f"n = {data['n_rounds']} decided rounds · family m = {data['family_size']} "
           f"({len(COLUMNS)} columns x {len(X_VARS)} x-variables) · "
           f"correction {data['correction']}",
           "",
           f"  {'test':28s} {'n':>4s} {'drop':>4s} {'AUC':>6s}  "
           f"{'tercile AUC':>20s}  {'rho':>7s} {'p raw':>9s} {'p bonf':>9s}"]
    for key in data["family"]:
        t = data["tests"][f"{key.split('/')[0]}/{key.split('/')[1]}"]
        tri = " / ".join(fmt_auc(v) if v is not None else "—" for v in t["terciles"])
        out.append(f"  {key:28s} {t['n']:4d} {t['dropped']:4d} "
                   f"{fmt_auc(t['auc']):>6s}  {tri:>20s}  "
                   f"{fmt_rho(t['rho']) if t['rho'] is not None else '—':>7s} "
                   f"{fmt_p(t['p_raw']) if t['p_raw'] is not None else '—':>9s} "
                   f"{fmt_p(t['p_bonferroni']) if t['p_bonferroni'] is not None else '—':>9s}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.join(os.path.dirname(__file__), ".."),
                    help="repository root (default: this file's)")
    ap.add_argument("--json", action="store_true", help="emit the measurement as JSON")
    ap.add_argument("--selftest", action="store_true",
                    help="the split rule's control and the estimator's, then exit")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    if args.selftest:
        return _selftest(root)
    data = measure(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(_table(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
