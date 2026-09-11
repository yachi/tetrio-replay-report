"""Hand-written claims for 2026-09-11 — what a generator cannot say about this night.

The generated ledger has the scores, the session records and the per-player rate splits. What
it has no family for is the *comparison between* those splits, and — this session — the size of
the gap that produced the most one-sided round column in the corpus.

**pinglamb takes the series 6-1 and the rounds 32-19.** That round split is 62.7% of the
night's rounds, the highest share any player has taken across eleven sessions (past 2026-08-09's
and 2026-08-19's 60.0%), and it lands one session after the corpus's only draw. C001 pins all
seven match winners and C010 the round totals plus the 8-20 the first four matches produced.
The two sessions are adjacent and at opposite ends of every scoreboard measure the repo keeps,
which is worth one sentence and no mechanism: two nights are two nights.

Split the rounds by who won them and the two regimes come apart in the shape 2026-09-10 also
took, but wider on the floor and narrower on the ceiling:

    attack per piece   won rounds    yachi .6371   pinglamb .6996   ->  +9.82%
                       lost rounds   yachi .5479   pinglamb .5734   ->  +4.65%

C002 pins both. Read it beside C004's session gap of +12.41%: the regimes are closer to each
other here than the session figure is to either, which is the arithmetic of pooling and not a
finding — it is why the decomposition is re-derived every session rather than read off the
session-level number.

**C005 and C009 are the volume route, a seventh time, and this is the run that shows what the
route CANNOT do.** yachi threw 110 more pieces for 309 fewer lines of attack — 9.15% of
pinglamb's total, the largest deficit in the corpus. His surplus is 2.13% of pinglamb's count,
so the route can buy back 2.13 pp against C004's 12.41 pp gap, leaving a shortfall of 10.28 pp,
also the largest in the corpus. The corpus ordering — sessions ranked by shortfall, ranked the
same way by attack difference — puts this session last on both, which is where it landed.

That is the THIRD out-of-sample test the ordering has had. 2026-09-03 missed and took Spearman
from a perfect 1.000 to 0.950; 2026-09-10 hit and took it to 0.9636; this one hits and takes it
to 0.9727, with 09-03 still the single session out of place. C005 and C009 pin this session's
arithmetic and deliberately pin NO position in that ordering: the ordering ranges over eleven
sessions and this ledger covers one.

**NO figure here needs a 「得一局撐住」 annotation, and that is measured rather than assumed.**
`check_loo` puts the largest relative single-round shift at 0.447 (`app_gap_lost`, dropping
m2r5), under THRESHOLD, and nothing flips sign. That 0.447 is nonetheless the closest any figure
in the corpus has come to the cut without crossing it, so the absence of a caveat here is a
near thing and is recorded as such in `check_loo.PUBLISHED`. The opposite end is worth naming
too: the −309 attack difference is the corpus's largest and its `rel` is 0.107 — a big pooled
difference over 51 rounds is exactly what leave-one-out cannot dent, which is the mirror image
of 2026-09-10's −47 at `rel` 0.766. Two adjacent sessions, the same figure, opposite fragility.

The claims are of six kinds:

  * **the shape of the night** — C001 pins all seven match winners at once, C010 the round
    totals and the 8-20 after four matches. Seven separate score claims cannot say the series
    was one-sided, because that is a fact about the set of matches and not about any one.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality
    because the denominators are different piece counts.
  * **each player against himself** — C003. Both players' attack per piece is higher in the
    rounds they won than in the rounds they lost, the eleventh session running that this holds
    for both. pinglamb's +22.01% against yachi's +16.27% makes this the fourth session running
    with pinglamb the wider of the two, and the first such run of four — stated as a count in
    the prose and NOT as a trend, because the same column put yachi 24.6 points ahead on
    2026-08-09 and the corpus high on it is still his.
  * **the route and its price** — C005 and C009. C006 is the death tally, 7 against 5.
  * **the seven matches, one each** — C011-C017 as `round_seq` runs, the rule every session
    since 2026-08-01 follows: cover *all* of them, so no match card can describe a lead or a
    collapse that no lemma pins.

C008 pins keypresses per piece for both players, pooled: yachi 3.620 and pinglamb 3.608, 0.33%
apart with **yachi on the HIGHER side this time**. That flip is the only reason the claim is
worth minting twice in two sessions — 09-10 pinned the same quantity 0.21% apart with yachi
lower, so the two ledgers together say the column's sign is not a property of either player. It
is deliberately NOT a claim about KPP's paired AUC: that statistic counts rounds by comparing a
per-round RATIO between the two players, and the cond language (`c_field`, `c_winner_gt_loser`,
`c_str`, `c_dur`) compares a field against a literal or against the other player's same field —
it has no cross-field ratio, so no `count_rounds` predicate can express it.

THE PER-MATCH SEPARATION FORMALLY HOLDS AND THERE IS DELIBERATELY NO CLAIM FOR IT — this is the
one judgement call in the ledger and it goes the other way from how it looks.

Order the seven matches by pinglamb's attack-per-piece advantage and yachi's single win (m5,
+0.21%) is the smallest, with pinglamb's six running +5.57% to +19.57% and nothing between 0.21
and 5.57. That is the same pattern 2026-08-19 and 2026-08-25 minted a C007 for. It is not the
same EVIDENCE, and the difference is countable: with k wins among m matches, a random assignment
puts all k at the bottom with probability 1/C(m,k) — 1/120 for 08-19's 3 of 10, 1/126 for
08-25's 4 of 9, and **1 in 7 here**, because yachi won one match. A pattern that would arise by
chance one night in seven is not a reproduction of one that would arise one night in 120, and
minting C007 on it would be fitting the claim to the night — the exact move CLAUDE.md records
08-09 as NOT being allowed to make when yachi won no match at all. The count of sessions that
separate stays 2 of 11 and this session is filed with 08-09 as the degenerate case, not with
08-19 and 08-25. Nothing in the report says the winner falls out of the ordering.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, ge_, gt, lit, lt,
                                  mul, round_seq, sub, sum_round, sum_round_range,
                                  sum_round_where, match_winner)

Y, P = "yachi", "pinglamb"

MATCHES = 7


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided 「the gap is over 9%」 would survive any further
    collapse of yachi's winning rounds, and every figure this ledger prints is the SIZE of a
    gap, not merely its direction.
    """
    lhs = mul(lit(100), mul(na, db))
    rhs = mul(nb, da)
    return conj(gt(lhs, mul(lit(lo), rhs)), lt(lhs, mul(lit(hi), rhs)))


def rate_x1000(num, den, v):
    """v == floor(1000 * num / den), as `v*den <= 1000*num < (v+1)*den`.

    The algebra has no division, so a derived rate is PINNED by bounding its numerator against
    its own denominator rather than compared to another rate. It has teeth because the band is
    `den` wide while a one-unit change to `num` moves the left side by 1000. Two predicates and
    not one `between`, because `between`'s bounds must be integer literals and this denominator
    is an expression.
    """
    scaled = mul(lit(1000), num)
    return conj(ge_(scaled, mul(lit(v), den)), lt(scaled, mul(lit(v + 1), den)))


def won(pl, f):
    return sum_round_where(pl, f, c_winner(pl))


def lost(pl, f):
    """The rounds this player did not win — the opponent's `winner` cond, same rounds."""
    other = P if pl == Y else Y
    return sum_round_where(pl, f, c_winner(other))


def window(pl, f, lo, hi):
    return sum_round_range(pl, f, lo, hi)


def rounds_won_in(pl, lo_m, hi_m, n):
    """How many of matches [lo_m, hi_m)'s rounds `pl` won, as a window sum over a 0/1 field.

    `alive` is 1 for the round's survivor and 0 for the player who died, and in first-to-death
    1v1 the survivor is the winner — the generated ledger states that identity and refuses to
    present the two as independent signals. Summing it over a match window is the only way this
    algebra can count a window's round wins: `count_rounds` takes a cond over the whole session
    and has no window form.
    """
    return eq(window(pl, "alive", lo_m, hi_m), lit(n))


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who led when, which is
    the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "YYPYPPPP",    # m1  3-5
    "PPPYPP",      # m2  1-5
    "PPPYPYP",     # m3  2-5
    "PPYPPYP",     # m4  2-5
    "YYYPYPY",     # m5  5-2   <- yachi's only match
    "YYPPPYPP",    # m6  3-5
    "PYPYPYPP",    # m7  3-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (4,)

MATCH_CANTO = [
    ("第一場 yachi 開波連贏兩局，第四局再贏，之後尾四局全失，3 比 5",
     "match 1: yachi won the first two and the fourth, then lost the last four, 3-5"),
    ("第二場最短，六局入面 yachi 淨係贏到第四局，1 比 5",
     "match 2: the shortest of the night — yachi took only the fourth round, 1-5"),
    ("第三場 yachi 頭三局全失，第四同第六局贏返，2 比 5",
     "match 3: yachi lost the first three and took the fourth and sixth, 2-5"),
    ("第四場一樣係贏兩局：第三同第六，2 比 5",
     "match 4: two rounds again, the third and the sixth, 2-5"),
    ("第五場 yachi 全晚唯一贏嘅一場，開波連贏三局，5 比 2",
     "match 5: yachi's only match of the night — three straight from the start, 5-2"),
    ("第六場 yachi 又係開波連贏兩局，跟住四局失三局，3 比 5",
     "match 6: yachi again won the first two, then lost three of the next four, 3-5"),
    ("第七場逐局咬，yachi 追到 3 比 3，最後兩局連失，3 比 5",
     "match 7: traded to 3-3 and yachi lost the last two, 3-5"),
]


def _seq_claims():
    out = []
    for mi, (run, (canto, gloss)) in enumerate(zip(RUNS, MATCH_CANTO)):
        out.append({
            "id": f"C{11 + mi:03d}",
            "category": "moment",
            "canto": canto,
            "english_gloss": gloss,
            "spec": match_seq(mi, [Y if ch == "Y" else P for ch in run]),
        })
    return out


CLAIMS = [
    {
        "id": "C001",
        "category": "score",
        "canto": "七場 match 打成 1 比 6：yachi 淨係攞到第五場，其餘六場全部俾 pinglamb 攞晒",
        "english_gloss": "pinglamb won the series six matches to one: yachi won only match 5",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局兩個人每粒方塊嘅攻擊爭 9% 幾，"
                 "輸嗰啲局爭 4% 幾——兩邊都拉開咗，只係天花板拉得闊啲",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is between 9 and "
                         "10 percent above yachi's; in the rounds each lost it is between 4 and "
                         "5 percent above",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 109, 110),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 104, 105),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 16% 幾，pinglamb 高 22% 幾",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by between 16 and 17 percent, pinglamb by "
                         "between 22 and 23 percent",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 116, 117),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 122, 123),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 12% 幾",
        "english_gloss": "over the whole session pinglamb's attack per piece is between 12 and "
                         "13 percent above yachi's",
        "spec": pct_between(atk(P), pieces(P), atk(Y), pieces(Y), 112, 113),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 110 粒方塊，打出嘅攻擊反而少 309 條，"
                 "即係 pinglamb 總攻擊嘅 9% 幾",
        "english_gloss": "yachi placed 110 more pieces than pinglamb yet landed 309 less attack, "
                         "a gap of between 9 and 10 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(110)),
            eq(sub(atk(P), atk(Y)), lit(309)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(9), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(10), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 12 局頂到上天花板收場，7 局係 yachi 頂爆、5 局係 pinglamb",
        "english_gloss": "twelve rounds ended in a topout, seven of them yachi's and five "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(7)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(5)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.620 下，pinglamb 3.608 下，"
                 "爭 0.33%——今次高嗰個係 yachi，同上一晚啱啱調轉",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.620 and pinglamb "
                         "3.608, about a third of a percent apart, with yachi the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3620),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3608),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 110 粒方塊盈餘，即係多過 pinglamb 2% 幾——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 2 個幾百分點，而佢要填嘅係 C004 嗰 12 個幾。"
                 "唔係條路唔得，係個窿大過條路成五倍",
        "english_gloss": "yachi's piece count is between 2 and 3 percent above pinglamb's, which "
                         "is the whole of what the volume route can buy back against the gap "
                         "C004 pins at between 12 and 13 percent",
        "spec": conj(
            gt(mul(lit(100), pieces(Y)), mul(lit(102), pieces(P))),
            lt(mul(lit(100), pieces(Y)), mul(lit(103), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 19 比 32——pinglamb 食咗成晚 62% 嘅局，係十一晚以嚟最一面倒嘅一次。"
                 "打完頭四場已經 8 比 20，之後三場都追唔返",
        "english_gloss": "the rounds finished 19 to 32; after the first four matches they stood "
                         "at 8 to 20",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 19),
            rounds_won_in(P, 0, MATCHES, 32),
            rounds_won_in(Y, 0, 4, 8),
            rounds_won_in(P, 0, 4, 20),
        ),
    },
] + _seq_claims()
