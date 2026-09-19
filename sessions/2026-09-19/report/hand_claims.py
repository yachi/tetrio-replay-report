"""Hand-written claims for 2026-09-19 — what a generator cannot say about this night.

**This is the largest session the corpus has, and not by a little: 20 matches and 150 rounds
against the previous records of 11 and 84.** It is 1.79x the previous largest by rounds and
3.26x the smallest, and it takes the corpus from 734 rounds to 884 — one night is 17% of every
round ever measured here. That size is not a footnote about the scoreboard; it is what makes
this session's finding possible, because **a corpus quantity that is secretly proportional to
session length cannot be caught by twelve sessions that all sit within a factor of 1.8 of each
other.** CLAUDE.md's shortfall ordering is exactly such a quantity and this night breaks it. The
claims below deliberately pin only what happened on this night — the corpus statement belongs
to the corpus, not to a ledger that can see one session.

**pinglamb takes the series 15-5 and the rounds 91-59.** C001 pins all twenty match winners and
C010 the round totals plus the shape: the first ten matches went 28-47 and the second ten went
31-44, **over exactly 75 rounds each**. Two same-sized windows, so the raw counts compare
directly and no cross-multiplication is needed — which is the one case CLAUDE.md's rule about
windows permits. The night was not given away late (09-03's shape) and it was not decided early
(09-11's); yachi trailed from match 1 and closed the second half marginally better than the
first. A 15-5 scoreline says none of that.

**BOTH REGIME GAPS ARE LEVEL, AND BOTH SIT AT OR BELOW THEIR OWN MEDIANS.** Split the rounds by
who won them:

    attack per piece   won rounds    yachi .6478   pinglamb .6856   ->  +5.84%
                       lost rounds   yachi .5418   pinglamb .5765   ->  +6.39%

C002 pins both. Ranked against their OWN columns over the thirteen sessions — the check CLAUDE.md
demands before any pair is characterised — the won-gap is **10th of thirteen** (median +7.66) and
the lost-gap is **7th of thirteen, i.e. exactly the median** (+6.39). The won/lost ratio is 0.91.
So this is the 「roughly level」 class, with 07-24, 07-28 and 08-01 — and it is now the
best-powered instance that class has, at 150 rounds against 07-28's 64.

**That matters mainly for what it does to 09-17.** The previous session was the first in which
both gaps were large at once (ranks 2 and 3), and CLAUDE.md filed it explicitly as one instance
that a thirteenth session could not turn into a class. The thirteenth session is this one and it
does not reproduce it: both gaps come back to the middle of their columns. 09-17 stays one
instance, which is what it was written as.

**NEITHER figure needs a 「得一局撐住」 annotation, and this session sets a corpus minimum on that
measurement — but NOT for the reason a reader will reach for.** `check_loo` puts every one of the
five figures this session can carry below 0.16:

    app_gap_won      +5.8413 pp   m13r3 ->  +4.9635   rel 0.150   1.10x the next of 150
    app_gap_lost     +6.3927 pp    m5r4 ->  +7.1379   rel 0.117   1.10x
    app_gap_session +11.1598 pp    m1r5 -> +11.7174   rel 0.050   1.50x
    attack_diff         -476 行    m7r3 ->     -444   rel 0.067   1.03x
    score_diff       -117513 分    m7r3 ->  -105625   rel 0.101   1.08x

Four of those five are the lowest `rel` ever measured on their figure, and 0.150 is the lowest
maximum of any session. The obvious inference — 「150 rounds makes a pooled figure robust」 — is
**measured and false**: over the thirteen sessions the rank correlation between round count and
maximum `rel` is −0.06, i.e. nothing. 08-01 at 53 rounds reads 20.931 and 09-10 at 65 reads 2.081.
What makes this session's figures robust is that none of them sits near zero, which is what
`check_loo`'s own header names as the fragile kind. Length is a confound here, not a cause.

**C004's session gap is +11.16%, and C005/C009 are the volume route for a NINTH time** — yachi
threw 714 more pieces (5.20% more than pinglamb) and landed 476 fewer lines of attack, 5.36% of
pinglamb's total. Both the surplus and the deficit are the largest raw numbers the route has ever
produced, and **both are largest because the session is longest**; as rates they are unremarkable.
C005 therefore pins the two raw counts AND the deficit as a fraction of pinglamb's total, so that
nothing downstream can quote the 476 without the 5.36% beside it. C009 pins the surplus as a
ratio for the same reason. The ledger pins **no position in the corpus ordering**: that ordering
ranges over thirteen sessions and this ledger can see one.

**NO C007 IS MINTED, and the id is left empty rather than reused.** Order the twenty matches by
pinglamb's attack-per-piece advantage and the winner does not fall out — not nearly, not
approximately. yachi's five wins sit at −6.19%, −5.24%, +8.07%, +10.96% and +14.89%, and
pinglamb's fifteen run +2.43% to +24.36%: three of yachi's wins are above six of pinglamb's. The
count of separating sessions stays **3 of 13**. Following 09-10 and 09-11, the slot is skipped
instead of filled with a weakened claim, because a C007 that meant 「it did not separate」 would
corrupt a count that other sessions' C007s carry.

Two related absolutes also fail here, and both are recorded rather than smoothed:
**yachi leads attack per piece outright in m3 and m16** — the two matches are among the five he
won — so 「pinglamb leads every match」 holds in 7 of the 13 sessions, not this one.

**C006 is the death tally, 15 against 9, and it is the session's sharpest small trap.** Fifteen
is the largest raw topout count any player has recorded, past 08-14's eleven — and it is the
largest because the session is nearly twice as long. As a RATE, yachi's 15 of 150 rounds is 10.0%
against 08-14's 11 of 84 = 13.1%, so the raw record and the rate disagree about whether this was
a bad night for him. The session total of 24 in 150 rounds is 16.0%, which ties 07-24 for
mid-table. The claim pins the two counts; the report prose is what has to carry the rate, and it
does.

**C008 pins keypresses per piece, pooled: yachi 3.646 and pinglamb 3.608**, 1.04% apart with
**yachi on the higher side** — the opposite of 09-17, where he was lower. Three of the last four
sessions have flipped this column's sign, so it is a fact about a night. As before, this is
deliberately NOT a claim about KPP's paired AUC: that statistic compares a per-round ratio
between the two players, and the cond language has no cross-field ratio, so no `count_rounds`
predicate can express it.

The claims are of six kinds:

  * **the shape of the night** — C001 pins all twenty match winners at once, C010 the round
    totals and the two equal halves. Twenty separate score claims cannot say the margin was
    taken at a near-constant rate, because that is a fact about the sequence.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality
    because the denominators are different piece counts.
  * **each player against himself** — C003. Both players' attack per piece is higher in the
    rounds they won — the thirteenth session running for both. yachi's +19.55% against
    pinglamb's +18.93% puts **yachi the wider of the two** by six-tenths of a point, taking the
    count to seven of thirteen yachi. Stated as a count and not as a trend: the same column put
    yachi 24.7 points ahead on 08-09 and pinglamb 12.5 ahead on 09-10, and the gap here is the
    smallest the column has ever shown.
  * **the route and its price** — C005 and C009, each pinning a rate beside its raw count.
  * **the death tally** — C006.
  * **the twenty matches, one each** — C011-C030 as `round_seq` runs, the rule every session
    since 2026-08-01 follows: cover *all* of them, so no match card can describe a lead or a
    collapse that no lemma pins. m1 is why the rule earns its keep this session — yachi came
    back from 0-2 down to lead 4-3 and then lost two straight, and only the sequence says that.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, ge_, gt, lit, lt,
                                  mul, round_seq, sub, sum_round, sum_round_range,
                                  sum_round_where, match_winner)

Y, P = "yachi", "pinglamb"

MATCHES = 20
HALF = 10          # the match index the two equal-sized round windows split at


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided 「the gap is over 5%」 would survive any further
    collapse of yachi's rate, and every figure this ledger prints is the SIZE of a gap. It
    matters most of all this session, whose finding is that the two regime gaps are both
    MIDDLING and close together — a pair of one-sided lower bounds could not tell +5.8/+6.4
    apart from +5.8/+25.
    """
    lhs = mul(lit(100), mul(na, db))
    rhs = mul(nb, da)
    return conj(gt(lhs, mul(lit(lo), rhs)), lt(lhs, mul(lit(hi), rhs)))


def rate_x1000(num, den, v):
    """v == floor(1000 * num / den), as `v*den <= 1000*num < (v+1)*den`.

    The algebra has no division, so a derived rate is PINNED by bounding its numerator against
    its own denominator. It has teeth because the band is `den` wide while a one-unit change to
    `num` moves the left side by 1000.
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
    "PPYPYYYPP",   # m1   4-5   <- yachi came back from 0-2 to lead 4-3, then lost two
    "YPPPPP",      # m2   1-5
    "YPYPPYYY",    # m3   5-3
    "PYPPYPYP",    # m4   3-5
    "PPYYPYPP",    # m5   3-5
    "PPPPYP",      # m6   1-5
    "PPPPYP",      # m7   1-5
    "PPPYYPP",     # m8   2-5
    "PPPYYYPP",    # m9   3-5
    "YYPPPYPYY",   # m10  5-4
    "PPPPP",       # m11  0-5   <- the night's only shutout
    "YYPPPPP",     # m12  2-5
    "PPYPPYP",     # m13  2-5
    "YYPYYPPY",    # m14  5-3
    "PPYYYPPYP",   # m15  4-5
    "YYYPPYY",     # m16  5-2
    "PPYYPPYP",    # m17  3-5
    "PPPYPYP",     # m18  2-5
    "PYPYYPYPY",   # m19  5-4
    "PPYYPYPP",    # m20  3-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (2, 9, 13, 15, 18)

MATCH_CANTO = [
    ("第一場 yachi 開波連輸兩局，追到 4 比 3 反超前，跟住連失兩局，4 比 5",
     "match 1: yachi lost the first two, came back to lead 4-3, then lost two straight, 4-5"),
    ("第二場 yachi 贏咗第一局之後連輸五局，1 比 5",
     "match 2: yachi won the first then lost five straight, 1-5"),
    ("第三場 yachi 尾三局連贏，5 比 3 攞低全晚第一場",
     "match 3: yachi won the last three to take it 5-3, his first of the night"),
    ("第四場逐局咬，冇人連贏過兩局，最後 3 比 5",
     "match 4: traded round for round with no run of two, 3-5"),
    ("第五場 yachi 中段贏返兩局，尾兩局又失，3 比 5",
     "match 5: yachi took two in the middle and lost the last two, 3-5"),
    ("第六場 yachi 淨係贏到第五局，1 比 5",
     "match 6: yachi took only the fifth round, 1-5"),
    ("第七場同第六場一模一樣嘅走勢，又係淨贏第五局，1 比 5",
     "match 7: the identical shape to match 6 — only the fifth round, 1-5"),
    ("第八場 yachi 贏中間兩局，2 比 5",
     "match 8: yachi took the middle two, 2-5"),
    ("第九場 yachi 連贏三局追到 3 比 3，尾兩局連失，3 比 5",
     "match 9: yachi won three straight to level at 3-3, then lost the last two, 3-5"),
    ("第十場 yachi 開波連贏兩局，尾兩局再連贏，5 比 4",
     "match 10: yachi won the first two and the last two, 5-4"),
    ("第十一場 yachi 一局都冇贏，0 比 5——全晚唯一一場剃光頭",
     "match 11: yachi won no round at all, 0-5 — the night's only shutout"),
    ("第十二場 yachi 開波連贏兩局之後連失五局，2 比 5",
     "match 12: yachi won the first two then lost five straight, 2-5"),
    ("第十三場 yachi 淨係贏到第三同第六局，2 比 5",
     "match 13: yachi took only the third and sixth, 2-5"),
    ("第十四場 yachi 開波連贏兩局，第四第五局再贏，5 比 3",
     "match 14: yachi won the first two and the fourth and fifth, 5-3"),
    ("第十五場 yachi 中段連贏三局追平，最後一局俾人攞走，4 比 5",
     "match 15: yachi won three straight in the middle to level it and lost the last, 4-5"),
    ("第十六場 yachi 開波連贏三局，5 比 2——全晚贏得最爽嗰場",
     "match 16: yachi won the first three and took it 5-2, his cleanest of the night"),
    ("第十七場逐局咬到尾，3 比 5",
     "match 17: traded to the end, 3-5"),
    ("第十八場 yachi 淨係贏到第四同第六局，2 比 5",
     "match 18: yachi took only the fourth and sixth, 2-5"),
    ("第十九場 yachi 贏最後一局收 5 比 4",
     "match 19: yachi took the last round to win it 5-4"),
    ("第二十場 yachi 中段贏三局，尾兩局連失，3 比 5",
     "match 20: yachi took three in the middle and lost the last two, 3-5"),
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
        "canto": "二十場 match 打成 5 比 15：yachi 攞到第三、第十、第十四、第十六同第十九場，"
                 "其餘十五場俾 pinglamb 攞晒——呢晚係全 corpus 最大嘅一晚，"
                 "場數同局數都係新高",
        "english_gloss": "pinglamb won the series fifteen matches to five: yachi won matches 3, "
                         "10, 14, 16 and 19",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，今晚兩邊都爭得唔多，而且爭得差唔多咁多："
                 "贏嗰啲局兩個人每粒方塊嘅攻擊爭 5% 幾，輸嗰啲局爭 6% 幾。"
                 "擺返落自己嗰欄度排，贏嗰個差距十三晚排第十，輸嗰個啱啱好係中位數——"
                 "即係上一晚「兩邊一齊拉開」嗰個樣，今晚冇再出現",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is between 5 and 6 "
                         "percent above yachi's; in the rounds each lost it is between 6 and 7 "
                         "percent above — both gaps at or below their own medians",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 105, 106),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 106, 107),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 19% 幾，pinglamb 高 18% 幾。兩個人爭唔夠一個百分點，"
                 "係呢一欄十三晚以嚟最貼嘅一次",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by between 19 and 20 percent, pinglamb by "
                         "between 18 and 19 percent, the closest this column has ever been",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 119, 120),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 118, 119),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 11% 幾",
        "english_gloss": "over the whole session pinglamb's attack per piece is between 11 and "
                         "12 percent above yachi's",
        "spec": pct_between(atk(P), pieces(P), atk(Y), pieces(Y), 111, 112),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 714 粒方塊，打出嘅攻擊反而少 476 條，"
                 "即係 pinglamb 總攻擊嘅 5% 幾。714 同 476 都係呢條路歷來最大嘅數字，"
                 "但兩個都係因為今晚最長——換返做比率就好普通，所以呢個 claim 兩樣都釘住",
        "english_gloss": "yachi placed 714 more pieces than pinglamb yet landed 476 less attack, "
                         "a gap of between 5 and 6 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(714)),
            eq(sub(atk(P), atk(Y)), lit(476)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(5), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(6), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 24 局頂到上天花板收場，15 局係 yachi 頂爆、9 局係 pinglamb。"
                 "15 係單一個人歷來最大嘅數，但佢係因為今晚有 150 局——"
                 "計返比率係一百五十局入面一成，仲低過 08-14 嗰十一局（八十四局入面 13%）",
        "english_gloss": "twenty-four rounds ended in a topout, fifteen of them yachi's and nine "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(15)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(9)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.646 下，pinglamb 3.608 下，"
                 "爭 1.04%——今次高嗰個係 yachi，同上一晚啱啱掉轉",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.646 and pinglamb "
                         "3.608, about one percent apart, with yachi the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3646),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3608),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 714 粒方塊盈餘，即係多過 pinglamb 5% 幾——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 5 個幾百分點。但佢要填嘅係 C004 嗰 11 個幾，"
                 "即係填到一半左右",
        "english_gloss": "yachi's piece count is between 5 and 6 percent above pinglamb's, which "
                         "is the whole of what the volume route can buy back against the gap "
                         "C004 pins at between 11 and 12 percent",
        "spec": conj(
            gt(mul(lit(100), pieces(Y)), mul(lit(105), pieces(P))),
            lt(mul(lit(100), pieces(Y)), mul(lit(106), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 59 比 91。頭十場係 28 比 47，尾十場係 31 比 44——"
                 "兩截啱啱好各 75 局，所以呢兩個數可以直接比。"
                 "即係話呢晚唔係後段崩，亦都唔係開波就輸晒，係由頭到尾用差唔多嘅速度輸緊，"
                 "而尾段仲略為好返少少",
        "english_gloss": "the rounds finished 59 to 91; the first ten matches went 28 to 47 and "
                         "the last ten went 31 to 44, over exactly 75 rounds each",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 59),
            rounds_won_in(P, 0, MATCHES, 91),
            rounds_won_in(Y, 0, HALF, 28),
            rounds_won_in(P, 0, HALF, 47),
            rounds_won_in(Y, HALF, MATCHES, 31),
            rounds_won_in(P, HALF, MATCHES, 44),
        ),
    },
] + _seq_claims()
