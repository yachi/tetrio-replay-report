"""Hand-written claims for 2026-10-03 — what a generator cannot say about this night.

**This is the smallest session the corpus has, on both measures at once: 5 matches and 36
rounds, against previous minima of 6 (08-09 and 09-03) and 46 (09-03).** It is also the
fifteenth session in date order and the fifteenth to arrive, so the two orderings CLAUDE.md
had to start distinguishing at 09-18 agree again here. Every extreme this night sets is a
small-n reading first and is written that way; the corpus statements themselves belong to the
corpus and are recorded in CLAUDE.md, not pinned here, because a ledger can see one session.

**pinglamb takes the series 3-2 while yachi takes the ROUNDS 19-17.** That is the first time in
the corpus the two measures name different players — 09-10's 4-4 had no match winner at all,
and every other session's round winner is its match winner. C011 pins the split itself, and it
pins the mechanism with it: yachi's two wins are both 5-1 and pinglamb's three are all 5-3, so
yachi banked 10 rounds to 2 in his matches and lost 9 to 15 in pinglamb's. Nothing about that
is a rate and nothing in it needs a cross-multiplication; it is arithmetic on five scorelines.

**C010 pins the shape: yachi led the series 2-1 and the rounds 13-7 after three matches, and
then went 6-10 in the last two.** The two windows are 20 and 16 rounds, so the counts are NOT
comparable as counts — CLAUDE.md's rule for windows of different sizes — and the claim pins the
fall as a cross-multiplied rate: 13/20 = 65% against 6/16 = 37.5%. This is 09-03's shape (the
margin arrives late), at the smallest size the corpus has held it.

**THE REGIMES ARE 07-22'S SHAPE, ALMOST EXACTLY.** Split the rounds by who won them:

    attack per piece   won rounds    yachi .6537   pinglamb .6862   ->  +4.96%
                       lost rounds   yachi .5153   pinglamb .5786   ->  +12.28%

C002 pins both. Ranked against their OWN columns over the fifteen sessions — the check CLAUDE.md
demands before any pair is characterised — the won-gap is **13th of fifteen**, under two-hundredths
above 08-25's +4.945, and the lost-gap is **5th of fifteen**, just under 07-22's +12.80. So the
ceilings are close and the floors apart: the class 07-22, 08-19 and 08-25 already hold, and this
is its fourth instance. 07-22 read +5.78/+12.80; this reads +4.96/+12.28. Two sessions ten weeks
apart landing on the same pair is a coincidence of two numbers, not a return to anything.

**C004's session gap is +6.86%, the second-narrowest of fifteen behind 09-10's +6.64%, and
C005/C009 are the volume route for an ELEVENTH time** — yachi threw 222 more pieces (6.20% more
than pinglamb) and landed 14 fewer lines of attack, 0.62% of pinglamb's total. The surplus and
the gap are 6.20% and 6.86% (C009 and C004, each pinned to the hundredth), so the route
bought back nearly all of it: the shortfall is about 0.66 pp, third-smallest in the corpus. **The 14 is the
smallest raw attack difference the corpus holds and it is smallest because the night is
shortest**; as a rate, 0.621% is the second-smallest in size, behind 07-28's 0.460% and only
five-thousandths of a point under 07-22's 0.626% (which went yachi's way). C005 pins the per-mille
beside the count so nothing downstream can quote the 14 alone. The ledger pins no position in the corpus
ordering.

**NO C007 IS MINTED, and the reason is the probability, not the ordering.** Order the five
matches by pinglamb's attack-per-piece advantage and the winner DOES fall out: yachi's two wins
are the two smallest gaps (m1 −7.59%, m3 −4.08%), pinglamb's three the three largest (m4 +9.44%,
m2 +13.16%, m5 +14.23%). But two wins among five fall that way by chance with probability
1/C(5,2) = **1 in 10**. CLAUDE.md files the instances by that number: 1 in 120 and 1 in 126 are
well-powered, 09-17's 1 in 21 is intermediate and minted, 09-11's 1 in 7 is degenerate and not.
1 in 10 sits on the degenerate side of the gap between 7 and 21 (their geometric midpoint is
about 12), so it is filed with 09-11 and 08-09. The count of separating sessions stays 3.

**What this night does have is the stronger and simpler statement, and C017 pins it: the player
with the higher attack per piece won every one of the five matches.** yachi leads APP outright
in both of his wins and pinglamb in all three of his. That is a SIGN statement, which CLAUDE.md
says the separation is not, and it is recorded as what it is — five matches, a fact about this
night. It also means 「pinglamb leads every match」 fails here.

**C006 is the death tally, 1 against 3.** Four topouts over 36 rounds is 11.1%, third-lowest
rate in the corpus behind 08-09's 8.0% and 08-19's 10.0%. yachi's one is 2.8% of rounds, his
lowest except 08-09's zero. A column CLAUDE.md records as predicting nothing.

**C008 pins keypresses per piece, pooled: yachi 3.579 and pinglamb 3.623**, and pins the ratio
too: pinglamb is between 1.2% and 1.3% above yachi. The direction is the reverse of 09-18's and
09-19's. As before, this is not a claim about KPP's paired AUC.

The claims are of seven kinds:

  * **the shape of the night** — C001 pins all five match winners, C010 the round totals, the
    two windows and the fall in yachi's round-win rate between them.
  * **the split between the two scoreboards** — C011.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality
    because the denominators are different piece counts.
  * **each player against himself** — C003. yachi's +26.86% against pinglamb's +18.59% puts
    yachi the wider, and +26.86 is the second-widest in yachi's column behind 08-09's +31.4.
  * **the route and its price** — C005 and C009, each pinning a rate beside its raw count.
  * **the death tally and KPP** — C006, C008.
  * **the five matches** — C012-C016 as `round_seq` runs, the rule every session since
    2026-08-01 follows; and C017, the per-match APP leader.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 5
SPLIT = 3          # the match index the two windows split at (3 matches, then 2)


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def gap_x100(na, da, nb, db, v):
    """(na/da) / (nb/db) is exactly (100 + v/100)% to the hundredth, FLOORED — i.e.
    `(10000+v)·nb·da <= 10000·na·db < (10001+v)·nb·da`.

    The prose prints these gaps at two decimals (+4.96%, +12.28%), and the one-point band
    earlier ledgers use (`pct_between`, 「between 4 and 5 percent」) would leave both decimals
    unproved — a number in a report with a
    weaker claim beside it, which CLAUDE.md names as the thing not to do. Floored because
    every figure this repo prints is floored.
    """
    lhs = mul(lit(10000), mul(na, db))
    rhs = mul(nb, da)
    return conj(ge_(lhs, mul(lit(10000 + v), rhs)), lt(lhs, mul(lit(10001 + v), rhs)))


def rate_x1000(num, den, v):
    """v == floor(1000 * num / den), as `v*den <= 1000*num < (v+1)*den`."""
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
    """How many of matches [lo_m, hi_m)'s rounds `pl` won, as a window sum over `alive`.

    `alive` is 1 for the round's survivor, and in first-to-death 1v1 the survivor is the
    winner. `count_rounds` has no window form, so a window's round wins are counted this way.
    """
    return eq(window(pl, "alive", lo_m, hi_m), lit(n))


def window_rate_falls():
    """yachi's round-win RATE is lower in matches 4-5 than in matches 1-3.

    The windows hold 20 and 16 rounds, so 13 and 6 are not comparable as counts. The
    denominators are each window's own round count, read out of the data as the sum of both
    players' `alive`, not written as the two literals the prose quotes.
    """
    first_y = window(Y, "alive", 0, SPLIT)
    last_y = window(Y, "alive", SPLIT, MATCHES)
    first_total = add(first_y, window(P, "alive", 0, SPLIT))
    last_total = add(last_y, window(P, "alive", SPLIT, MATCHES))
    return lt(mul(last_y, first_total), mul(first_y, last_total))


def app_leads(mi, leader):
    """`leader`'s attack per piece is strictly higher than the other's over match `mi`."""
    other = P if leader == Y else Y
    return gt(mul(window(leader, "garbage_attack", mi, mi + 1), window(other, "pieces", mi, mi + 1)),
              mul(window(other, "garbage_attack", mi, mi + 1), window(leader, "pieces", mi, mi + 1)))


def match_seq(mi, winners):
    """Pin a whole match's round order — the only way to state a lead later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "YPYYYY",      # m1   5-1
    "YPPPYYPP",    # m2   3-5   <- yachi levelled at 3-3 from 1-3 down, then lost two
    "YYPYYY",      # m3   5-1
    "PYYYPPPP",    # m4   3-5   <- yachi led 3-1, then lost four straight
    "PPPYYPYP",    # m5   3-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (0, 2)

MATCH_CANTO = [
    ("第一場 yachi 淨係輸咗第二局，5 比 1",
     "match 1: yachi dropped only the second round, 5-1"),
    ("第二場 yachi 由 1 比 3 追到 3 比 3，尾兩局連失，3 比 5",
     "match 2: yachi came back from 1-3 to level at 3-3, then lost the last two, 3-5"),
    ("第三場 yachi 淨係輸咗第三局，5 比 1",
     "match 3: yachi dropped only the third round, 5-1"),
    ("第四場 yachi 打到 3 比 1 領先，跟住連失四局，3 比 5",
     "match 4: yachi led 3-1, then lost four straight, 3-5"),
    ("第五場 yachi 開波連輸三局，追到 3 比 4，最後一局俾人攞走，3 比 5",
     "match 5: yachi lost the first three, closed to 3-4, and lost the last, 3-5"),
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
        "canto": "五場 match 打成 2 比 3：yachi 攞到第一同第三場，"
                 "第二、第四、第五場俾 pinglamb 攞走",
        "english_gloss": "pinglamb won the series three matches to two: yachi won matches 1 and 3",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，今晚天花板貼埋、地板分開："
                 "贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 yachi 4.96%，輸嗰啲局高 12.28%",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 4.96 percent "
                         "above yachi's; in the rounds each lost it is 12.28 percent above",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 496),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1228),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 26.86%，pinglamb 高 18.59%。今次闊嗰個係 yachi",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 26.86 percent, pinglamb by 18.59 percent",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 2686),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1859),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 6.86%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 6.86 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 686),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 222 粒方塊，打出嘅攻擊只係少 14 條，"
                 "即係 pinglamb 總攻擊嘅 0.62%",
        "english_gloss": "yachi placed 222 more pieces than pinglamb and landed 14 less attack, "
                         "a gap of 0.62 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(222)),
            eq(sub(atk(P), atk(Y)), lit(14)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(62), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(63), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 4 局頂到上天花板收場，1 局係 yachi 頂爆、3 局係 pinglamb",
        "english_gloss": "four rounds ended in a topout, one of them yachi's and three "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(1)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(3)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.579 下，pinglamb 3.623 下，"
                 "pinglamb 高 yachi 1.23%",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.579 and pinglamb "
                         "3.623, pinglamb 1.23 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3579),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3623),
            gap_x100(sum_round(P, "inputs"), pieces(P), sum_round(Y, "inputs"), pieces(Y), 123),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 222 粒方塊盈餘，即係多過 pinglamb 6.20%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 6.20 個百分點，而 C004 個窿係 6.86%，"
                 "即係差唔多填返晒",
        "english_gloss": "yachi's piece count is 6.20 percent above pinglamb's, against the "
                         "6.86 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10620), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10621), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 19 比 17。頭三場 yachi 13 比 7，尾兩場 6 比 10——"
                 "兩截唔同長短（20 局同 16 局），所以要當比率比：65% 對 37.5%。"
                 "即係話 yachi 打完三場仲係 2 比 1 領先，個系列係尾段先輸",
        "english_gloss": "the rounds finished 19 to 17; the first three matches went 13 to 7 over "
                         "20 rounds and the last two went 6 to 10 over 16, so yachi's round-win "
                         "rate is lower in the last two matches than in the first three",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 19),
            rounds_won_in(P, 0, MATCHES, 17),
            rounds_won_in(Y, 0, SPLIT, 13),
            rounds_won_in(P, 0, SPLIT, 7),
            rounds_won_in(Y, SPLIT, MATCHES, 6),
            rounds_won_in(P, SPLIT, MATCHES, 10),
            window_rate_falls(),
        ),
    },
    {
        "id": "C011",
        "category": "score",
        "canto": "局數係 yachi 多，場數係 pinglamb 多：yachi 贏嗰兩場都係 5 比 1，"
                 "合共 10 比 2；pinglamb 贏嗰三場都係 5 比 3，合共 15 比 9",
        "english_gloss": "yachi won more rounds and pinglamb more matches: yachi's two wins went "
                         "5-1 each, 10 rounds to 2, and pinglamb's three went 5-3 each, 15 to 9",
        "spec": conj(
            gt(window(Y, "alive", 0, MATCHES), window(P, "alive", 0, MATCHES)),
            match_winner(0, Y), match_winner(2, Y),
            match_winner(1, P), match_winner(3, P), match_winner(4, P),
            eq(window(Y, "alive", 0, 1), lit(5)), eq(window(P, "alive", 0, 1), lit(1)),
            eq(window(Y, "alive", 2, 3), lit(5)), eq(window(P, "alive", 2, 3), lit(1)),
            eq(window(P, "alive", 1, 2), lit(5)), eq(window(Y, "alive", 1, 2), lit(3)),
            eq(window(P, "alive", 3, 4), lit(5)), eq(window(Y, "alive", 3, 4), lit(3)),
            eq(window(P, "alive", 4, 5), lit(5)), eq(window(Y, "alive", 4, 5), lit(3)),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C017",
        "category": "style",
        "canto": "逐場計每粒方塊嘅攻擊，邊個高邊個就贏咗嗰場，五場冇一場例外："
                 "yachi 喺第一同第三場高，pinglamb 喺第二、第四、第五場高",
        "english_gloss": "in every one of the five matches the player with the higher attack per "
                         "piece won it: yachi in matches 1 and 3, pinglamb in matches 2, 4 and 5",
        "spec": conj(
            match_winner(0, Y), app_leads(0, Y),
            match_winner(2, Y), app_leads(2, Y),
            match_winner(1, P), app_leads(1, P),
            match_winner(3, P), app_leads(3, P),
            match_winner(4, P), app_leads(4, P),
        ),
    },
]
