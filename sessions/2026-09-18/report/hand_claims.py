"""Hand-written claims for 2026-09-18 — what a generator cannot say about this night.

**This session is the corpus's second-largest — 18 matches and 127 rounds — and it lands
BEFORE the largest in the ordering, which is the first time a session has been added anywhere
but at the end.** That is a fact about the corpus and not about the night, and it is what makes
this session useful twice over: it is a genuine out-of-sample test of two things 2026-09-19 had
just changed, and it is the only test either of them will get at this size. Both pass, and both
are recorded in CLAUDE.md rather than here, because a ledger can see one session.

**pinglamb takes the series 11-7 and the rounds 69-58, and the scoreline hides the shape.**
Split the eighteen matches down the middle and the two halves run OPPOSITE WAYS:

    matches  1-9    yachi 2-7 in matches,  24-37 in rounds  (61 rounds)
    matches 10-18   yachi 5-4 in matches,  34-32 in rounds  (66 rounds)

yachi WINS the second half on rounds. C010 pins both windows, and it pins the comparison as a
CROSS-MULTIPLIED inequality rather than by setting 24 beside 34: the two windows are 61 and 66
rounds, so the raw counts are not comparable and CLAUDE.md's rule for windowed claims says so
explicitly. 24/61 = 39.3% against 34/66 = 51.5%. This is 09-11's shape — the night decided early
— at twice the size, and the opposite of 09-03's.

**FOUR SHUTOUTS, WHICH IS THE CORPUS RAW RECORD, AND ONE OF THEM IS THE FINDING.** m2, m9 and
m18 are 0-5 to pinglamb; **m4 is 5-0 to yachi, and it is the only shutout yachi has recorded in
the corpus.** Every one of the other nine, across six sessions, is pinglamb's. C011 pins all
four. Two things that claim must not be read as, and the prose says both:

  * **Four is a raw record and not a rate record.** Four of eighteen matches is 22.2%; 07-24's
    two of seven is 28.6%, which is higher. This is exactly the trap 09-19's topout column set
    one session ago — a raw tally that is largest because the session is longest — and the
    correct summary is the rate, on which this night is second.
  * **「yachi's first shutout」 is a COUNT over the corpus, so it is safe**, where the four is
    not. It does not become a rate, it cannot be inflated by session length, and one more
    session cannot make it retrospectively wrong — it can only end it.

**THE LOST-REGIME GAP IS +1.54%, THE SECOND-NARROWEST THE CORPUS HOLDS, AND ITS LEAVE-ONE-OUT
RUNS THE OTHER WAY.** Split the rounds by who won them:

    attack per piece   won rounds    yachi .6431   pinglamb .6967   ->  +8.33%
                       lost rounds   yachi .5447   pinglamb .5531   ->  +1.54%

C002 pins both. Ranked against their own columns over the fourteen sessions — the check
CLAUDE.md demands before any pair is characterised — the won-gap is 6th and the lost-gap is
**13th of fourteen**, i.e. second-smallest behind 09-10's +1.25%. The won/lost ratio is 5.40.
So this is the mirror class, with 08-14 and 09-10, and it is the third instance of it.

What is new is the fragility. `check_loo` puts `app_gap_lost` at **rel 0.618**, over THRESHOLD,
so the figure carries a 「得一局撐住」 annotation — and it is the first case on that measurement
whose influential round moves the figure TOWARD zero rather than away from it:

    app_gap_lost     +1.5434 pp    m1r7 ->  +0.5900   rel 0.618   1.16x the next of 127

In 08-14 and 09-10 — the only other near-zero lost-gaps — dropping the round WIDENED the gap, so
「the floors have met」 was the reading that failed. Here dropping m1r7 narrows it further, so the
qualitative reading survives its own leave-one-out and is sharpened by it; only the figure +1.54
is the one round's. m1r7 is pinglamb's: he threw .7086 attack per piece over 151 pieces and lost
the round. `rel` is direction-blind and this session is what shows the cost of that.

**C004's session gap is +8.93%, and C005/C009 are the volume route for a TENTH time** — yachi
threw 426 more pieces (3.71% more than pinglamb) and landed 352 fewer lines of attack, 4.80% of
pinglamb's total. C005 pins the two raw counts AND the deficit as a fraction of pinglamb's total,
following 09-19, so nothing downstream can quote the 352 without the 4.80% beside it. C009 pins
the surplus as a ratio for the same reason. The ledger pins **no position in the corpus
ordering**: that ordering ranges over fourteen sessions and this ledger can see one.

**NO C007 IS MINTED, and the id is left empty rather than reused.** Order the eighteen matches by
pinglamb's attack-per-piece advantage and the winner does not fall out. yachi's seven wins sit at
−18.26%, −11.41%, −5.00%, −3.89%, −2.06%, +0.81% and +8.39%; pinglamb's eleven run −2.72% to
+26.81%, so pinglamb's m17 (−2.72%) sits inside yachi's band and no cut exists. The count of
separating sessions stays **3 of 14**. Following 09-10, 09-11 and 09-19, the slot is skipped
rather than filled with a weakened claim.

**yachi leads attack per piece outright in six of the eighteen matches** (m4, m11, m14, m15, m16
and m17), so 「pinglamb leads every match」 fails here too — it holds in 7 of the 14 sessions.

**C006 is the death tally, 11 against 12, and it is the second one-apart split with PINGLAMB on
the higher side** after 09-10's 5-6. The session's 23 topouts over 127 rounds is 18.1%, the
second-highest RATE of the fourteen behind 09-11's 23.5% — so this column, which CLAUDE.md
records as predicting nothing, lands near its top again on a night the series was not close.

**C008 pins keypresses per piece, pooled: yachi 3.628 and pinglamb 3.608**, with yachi 0.57%
above pinglamb. The direction matches 09-19 and the size is about half of it. As there, this is
deliberately NOT a claim about KPP's paired AUC: that statistic compares a per-round ratio
between the two players, and the cond language has no cross-field ratio.

The claims are of seven kinds:

  * **the shape of the night** — C001 pins all eighteen match winners at once, C010 the round
    totals and the two halves with their rate comparison.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality
    because the denominators are different piece counts.
  * **each player against himself** — C003. Both players' attack per piece is higher in the
    rounds they won — the fourteenth session running for both. pinglamb's +25.96% against
    yachi's +18.07% puts pinglamb the wider, taking the count to seven yachi and seven pinglamb
    over the fourteen. Stated as a count, never as a trend.
  * **the route and its price** — C005 and C009, each pinning a rate beside its raw count.
  * **the death tally** — C006.
  * **the four shutouts** — C011, which is the one claim here no other session's ledger could
    have carried.
  * **the eighteen matches, one each** — C012-C029 as `round_seq` runs, the rule every session
    since 2026-08-01 follows: cover *all* of them, so no match card can describe a lead or a
    collapse that no lemma pins. m1 and m17 are why the rule earns its keep — both are 4-5, and
    in both yachi led at some point.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 18
HALF = 9           # the match index the two round windows split at (9 matches each side)


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided 「the gap is over 8%」 would survive any further
    collapse of yachi's rate, and every figure this ledger prints is the SIZE of a gap. It
    matters most for the lost-regime gap, whose whole content is that it is NEAR ZERO — a
    lower bound alone could not tell +1.5 from +15.
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


def half_rate_rises():
    """yachi's round-win RATE is higher in matches 10-18 than in matches 1-9.

    The two windows hold 61 and 66 rounds, so 24 and 34 are NOT comparable as counts —
    CLAUDE.md: 「Windows of different sizes must be compared as cross-multiplied rates, never
    as raw sums」. The denominators are each window's own total round count, written as the sum
    of both players' `alive` over that window, so the inequality is pinned by the data rather
    than by the two literals the prose quotes.
    """
    first_y = window(Y, "alive", 0, HALF)
    last_y = window(Y, "alive", HALF, MATCHES)
    # each window's round count = yachi's wins + pinglamb's wins in it, so the denominators
    # are read out of the data rather than written as the two literals the prose quotes
    first_total = add(first_y, window(P, "alive", 0, HALF))
    last_total = add(last_y, window(P, "alive", HALF, MATCHES))
    return gt(mul(last_y, first_total), mul(first_y, last_total))


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who led when, which is
    the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PYPYPPYYP",   # m1   4-5   <- yachi led 4-3 after seven, then lost two
    "PPPPP",       # m2   0-5   <- shutout
    "PYYPYPPP",    # m3   3-5
    "YYYYY",       # m4   5-0   <- the corpus's only shutout BY yachi
    "YPPYPPP",     # m5   2-5
    "PYPYYPPP",    # m6   3-5
    "PYPPPYP",     # m7   2-5
    "PYYYYPY",     # m8   5-2
    "PPPPP",       # m9   0-5   <- shutout
    "PPPYYYYY",    # m10  5-3   <- yachi lost the first three then won five straight
    "PYYYYY",      # m11  5-1
    "PPYYYPPP",    # m12  3-5
    "PPYPYPP",     # m13  2-5
    "YYPYPPYY",    # m14  5-3
    "PYYPYYY",     # m15  5-2
    "YYPYPYPY",    # m16  5-3
    "YPYYPPYPP",   # m17  4-5   <- yachi led 4-3 after seven and lost two, as in m1
    "PPPPP",       # m18  0-5   <- shutout, and the night's last match
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (3, 7, 9, 10, 13, 14, 15)

# The four shutouts, 0-based match index -> the player who took every round.
SHUTOUTS = ((1, P), (3, Y), (8, P), (17, P))

MATCH_CANTO = [
    ("第一場 yachi 打到 4 比 3 反超前，跟住連失兩局，4 比 5",
     "match 1: yachi led 4-3 after seven rounds, then lost two straight, 4-5"),
    ("第二場一局都冇贏，0 比 5——全晚三場剃光頭嘅第一場",
     "match 2: yachi won no round at all, 0-5 — the first of the night's three whitewashes"),
    ("第三場 yachi 中段連贏兩局，尾三局連失，3 比 5",
     "match 3: yachi took two in the middle then lost the last three, 3-5"),
    ("第四場 yachi 五局全取，5 比 0——全 corpus 到今日為止，yachi 唯一一場剃光頭",
     "match 4: yachi won all five, 5-0 — his only shutout anywhere in the corpus"),
    ("第五場 yachi 贏頭一局同第四局，2 比 5",
     "match 5: yachi took the first and the fourth, 2-5"),
    ("第六場 yachi 中段連贏兩局，尾三局連失，3 比 5",
     "match 6: yachi took two in the middle and lost the last three, 3-5"),
    ("第七場 yachi 淨係贏到第二同第六局，2 比 5",
     "match 7: yachi took only the second and the sixth, 2-5"),
    ("第八場 yachi 連贏四局，5 比 2",
     "match 8: yachi won four straight and took it 5-2"),
    ("第九場又係一局都冇贏，0 比 5",
     "match 9: yachi won no round again, 0-5"),
    ("第十場 yachi 開波連輸三局，跟住連贏五局收，5 比 3",
     "match 10: yachi lost the first three then won five straight, 5-3"),
    ("第十一場 yachi 輸咗第一局之後連贏五局，5 比 1",
     "match 11: yachi lost the first then won five straight, 5-1"),
    ("第十二場 yachi 中段連贏三局，尾三局連失，3 比 5",
     "match 12: yachi won three in the middle and lost the last three, 3-5"),
    ("第十三場 yachi 淨係贏到第三同第五局，2 比 5",
     "match 13: yachi took only the third and the fifth, 2-5"),
    ("第十四場 yachi 開波連贏兩局，尾兩局再連贏，5 比 3",
     "match 14: yachi won the first two and the last two, 5-3"),
    ("第十五場 yachi 尾三局連贏，5 比 2",
     "match 15: yachi won the last three to take it 5-2"),
    ("第十六場逐局咬，yachi 贏多兩局收，5 比 3",
     "match 16: traded round for round, yachi two ahead at the end, 5-3"),
    ("第十七場同第一場一樣：yachi 4 比 3 反超前之後連失兩局，4 比 5",
     "match 17: the same shape as match 1 — yachi led 4-3 after seven and lost two, 4-5"),
    ("第十八場一局都冇贏收爐，0 比 5",
     "match 18: the night ends on a third whitewash, 0-5"),
]


def _seq_claims():
    out = []
    for mi, (run, (canto, gloss)) in enumerate(zip(RUNS, MATCH_CANTO)):
        out.append({
            "id": f"C{12 + mi:03d}",
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
        "canto": "十八場 match 打成 7 比 11：yachi 攞到第四、第八、第十、第十一、第十四、"
                 "第十五同第十六場，其餘十一場俾 pinglamb 攞晒",
        "english_gloss": "pinglamb won the series eleven matches to seven: yachi won matches 4, "
                         "8, 10, 11, 14, 15 and 16",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，今晚兩邊嘅地板幾乎貼埋一齊，天花板就冇："
                 "贏嗰啲局兩個人每粒方塊嘅攻擊爭 8% 幾，輸嗰啲局淨係爭 1% 幾。"
                 "擺返落自己嗰欄度排，輸嗰個差距十四晚以嚟排第十三，即係第二窄——"
                 "呢個係 08-14 同 09-10 嗰個鏡像樣，第三次出現",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is between 8 and 9 "
                         "percent above yachi's; in the rounds each lost it is between 1 and 2 "
                         "percent above — the second-narrowest floor gap in the corpus",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 108, 109),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 101, 102),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 18% 幾，pinglamb 高 25% 幾。今次闊嗰個係 pinglamb，"
                 "十四晚計落去就變成七比七，即係呢一欄講唔出邊個係邊個",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by between 18 and 19 percent, pinglamb by "
                         "between 25 and 26 percent",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 118, 119),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 125, 126),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 8% 幾",
        "english_gloss": "over the whole session pinglamb's attack per piece is between 8 and "
                         "9 percent above yachi's",
        "spec": pct_between(atk(P), pieces(P), atk(Y), pieces(Y), 108, 109),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 426 粒方塊，打出嘅攻擊反而少 352 條，"
                 "即係 pinglamb 總攻擊嘅 4% 幾。呢條路連續第十次填唔返個窿",
        "english_gloss": "yachi placed 426 more pieces than pinglamb yet landed 352 less attack, "
                         "a gap of between 4 and 5 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(426)),
            eq(sub(atk(P), atk(Y)), lit(352)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(4), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(5), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 23 局頂到上天花板收場，11 局係 yachi 頂爆、12 局係 pinglamb。"
                 "一百二十七局入面 18%，係十四晚以嚟第二高嘅比率",
        "english_gloss": "twenty-three rounds ended in a topout, eleven of them yachi's and "
                         "twelve pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(11)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(12)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.628 下，pinglamb 3.608 下，"
                 "yachi 高 pinglamb 0.57%——方向同上一晚一樣，大細細一半",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.628 and pinglamb "
                         "3.608, about half a percent apart, with yachi the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3628),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3608),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 426 粒方塊盈餘，即係多過 pinglamb 3% 幾——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 3 個幾百分點。但佢要填嘅係 C004 嗰 8 個幾",
        "english_gloss": "yachi's piece count is between 3 and 4 percent above pinglamb's, which "
                         "is the whole of what the volume route can buy back against the gap "
                         "C004 pins at between 8 and 9 percent",
        "spec": conj(
            gt(mul(lit(100), pieces(Y)), mul(lit(103), pieces(P))),
            lt(mul(lit(100), pieces(Y)), mul(lit(104), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 58 比 69。頭九場係 24 比 37，尾九場係 34 比 32——"
                 "即係話 yachi 喺下半晚嘅局數係贏返嘅。兩截唔同長短（61 局同 66 局），"
                 "所以兩個數唔可以直接比，要當比率算：39% 對 51%。"
                 "呢晚係開頭就輸咗，唔係尾段崩",
        "english_gloss": "the rounds finished 58 to 69; the first nine matches went 24 to 37 "
                         "over 61 rounds and the last nine went 34 to 32 over 66, so yachi's "
                         "round-win rate is higher in the second half than in the first",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 58),
            rounds_won_in(P, 0, MATCHES, 69),
            rounds_won_in(Y, 0, HALF, 24),
            rounds_won_in(P, 0, HALF, 37),
            rounds_won_in(Y, HALF, MATCHES, 34),
            rounds_won_in(P, HALF, MATCHES, 32),
            half_rate_rises(),
        ),
    },
    {
        "id": "C011",
        "category": "moment",
        "canto": "全晚四場剃光頭：第二、第九、第十八場 pinglamb 五局全取，"
                 "第四場 yachi 五局全取。四場係 raw 數字上全 corpus 最多，"
                 "但計比率 07-24 嗰兩場（七場入面）仲高。"
                 "真正新嘅係第四場：全 corpus 十場剃光頭，淨係呢一場係 yachi 嗰邊",
        "english_gloss": "four matches were whitewashes: pinglamb took every round of matches 2, "
                         "9 and 18, and yachi took every round of match 4",
        "spec": conj(
            match_winner(1, P), eq(window(Y, "alive", 1, 2), lit(0)),
            match_winner(8, P), eq(window(Y, "alive", 8, 9), lit(0)),
            match_winner(17, P), eq(window(Y, "alive", 17, 18), lit(0)),
            match_winner(3, Y), eq(window(P, "alive", 3, 4), lit(0)),
        ),
    },
] + _seq_claims()
