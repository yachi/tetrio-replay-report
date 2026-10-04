"""Hand-written claims for 2026-10-03 — what a generator cannot say about this night.

**Twenty matches and 146 rounds: the second-largest session by rounds (behind 09-19's 150) and
level with 09-19 on matches.** This session was first published from five of the night's twenty
replays (16-20); it was rebuilt from all twenty, and nothing in this ledger is carried from that
version. pinglamb takes the series 14-6 and the rounds 82-64, so the round majority belongs to the
match winner, as it does in every decided session the corpus holds.

**C007 IS MINTED, AND IT IS THE BEST-POWERED SEPARATION THE CORPUS HAS.** Order the twenty matches
by pinglamb's attack-per-piece advantage and yachi's six wins are the six smallest gaps — m3
−9.36%, m8 −7.80%, m16 −7.59%, m4 −6.38%, m18 −4.08%, m12 +3.25% — while pinglamb's fourteen run
+6.65% (m15) to +20.63% (m5), nothing between +3.25 and +6.65. With k wins among m matches a
random assignment puts all k at the bottom with probability 1/C(m,k): **1 in 38 760 here**,
against 1/120 (08-19), 1/126 (08-25) and 1/21 (09-17) for the three earlier instances. The two
sessions that had more power than any of those — 09-19 at 1 in 15 504 and 09-18 at 1 in 31 824 —
both interleaved; this one, more powered than either, does not. The claim pins the SIZE of the
gap on each side of a cut (under +4% in every yachi win, over +6% in every pinglamb win), not who
leads, because who leads fails once:

**C031 pins the sign, and the sign is not what separates.** The player with the higher attack per
piece won 19 of the 20 matches. The exception is m12, which yachi won 5-3 while pinglamb led by
+3.25% — the top of yachi's band. So 「yachi won the matches he out-hit pinglamb in」 is true five
times out of six, and the separation is a statement about the gap's size.

**BOTH REGIME GAPS ARE SMALL.** Split the rounds by who won them:

    attack per piece   won rounds    yachi .6523   pinglamb .6830   ->  +4.70%
                       lost rounds   yachi .5370   pinglamb .5683   ->  +5.83%

C002 pins both to the hundredth. Ranked against their OWN columns over the fifteen sessions the
won-gap is 14th (only 08-09's +1.85 is smaller) and the lost-gap 10th; both are below their
column medians and the won/lost ratio is 0.81, so this is the 「roughly level」 class. C004's
session gap of +7.24% is the second-smallest in the corpus, behind 09-10's +6.65%. None of the
three needs a 「得一局撐住」 annotation: `check_loo` puts every figure this session can carry
under 0.16.

**C005/C009 are the volume route for the eleventh time, and this is where the night's margin
actually is.** yachi threw 328 more pieces (2.38% more than pinglamb's count) and landed 395 fewer
lines of attack, 4.53% of pinglamb's total. The surplus buys back 2.38 points of a 7.24-point gap
— a shortfall near 4.9 — so a small efficiency gap and a small surplus leave a mid-table hole.
Both claims pin a rate beside the raw count, because the raw counts are large for the same reason
the session is: it is long.

**C006 is the death tally, 14 against 13.** Twenty-seven topouts in 146 rounds. The claim pins
the two counts; that 27 is the largest session total and 13 pinglamb's largest tally is a corpus
fact the report prose carries with the rate (18.49%) beside it.

**C010 is the night's shape, and it is the one thing this ledger has that no generated claim can
say.** Cut the twenty matches into four blocks of five: 16-22, 17-20, 12-23, then **19-17** — the
last block is the only one in which yachi won more rounds than pinglamb, and the third is his
worst. The blocks hold 38, 37, 35 and 36 rounds, so the ordering of the four rates is pinned by
cross-multiplication, never by the raw counts. After fifteen matches the rounds stood 45-65.

**C008 pins keypresses per piece, pooled: yachi 3.614 and pinglamb 3.591, yachi 0.63% above.**
Written as 「A is X% above B」 so it cannot be read two ways.

The claims are of seven kinds:

  * **the shape of the night** — C001 pins all twenty match winners at once, C010 the four
    five-match blocks.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality.
  * **each player against himself** — C003: yachi +21.46%, pinglamb +20.17%, yachi the wider.
  * **the route and its price** — C005 and C009.
  * **the death tally** — C006.
  * **the per-match ordering** — C007 (size) and C031 (sign).
  * **the twenty matches, one each** — C011-C030 as `round_seq` runs, so no match card can
    describe a lead or a collapse that no lemma pins.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 20
BLOCKS = [(0, 5), (5, 10), (10, 15), (15, 20)]


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def gap_x100(na, da, nb, db, v):
    """(na/da) / (nb/db) is exactly (100 + v/100)% to the hundredth, FLOORED — i.e.
    `(10000+v)·nb·da <= 10000·na·db < (10001+v)·nb·da`.

    The prose prints these gaps at two decimals, and a one-point band would leave both decimals
    unproved. Floored because every figure this repo prints is floored.
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


def block_rate_lt(a, b):
    """yachi's round-win RATE in block `a` is below his rate in block `b`.

    The blocks hold different numbers of rounds, so the counts are not comparable; the
    denominators are each block's own round count, read out of the data as the sum of both
    players' `alive`, not written as literals.
    """
    ya = window(Y, "alive", *BLOCKS[a])
    yb = window(Y, "alive", *BLOCKS[b])
    ta = add(ya, window(P, "alive", *BLOCKS[a]))
    tb = add(yb, window(P, "alive", *BLOCKS[b]))
    return lt(mul(ya, tb), mul(yb, ta))


def app_leads(mi, leader):
    """`leader`'s attack per piece is strictly higher than the other's over match `mi`."""
    other = P if leader == Y else Y
    return gt(mul(window(leader, "garbage_attack", mi, mi + 1), window(other, "pieces", mi, mi + 1)),
              mul(window(other, "garbage_attack", mi, mi + 1), window(leader, "pieces", mi, mi + 1)))


def match_gap_under(mi, pct):
    """pinglamb's attack-per-piece advantage over match `mi` is under `pct - 100` percent."""
    return lt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1),
                                window(Y, "pieces", mi, mi + 1))),
              mul(lit(pct), mul(window(Y, "garbage_attack", mi, mi + 1),
                                window(P, "pieces", mi, mi + 1))))


def match_gap_over(mi, pct):
    """pinglamb's attack-per-piece advantage over match `mi` is over `pct - 100` percent."""
    return gt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1),
                                window(Y, "pieces", mi, mi + 1))),
              mul(lit(pct), mul(window(Y, "garbage_attack", mi, mi + 1),
                                window(P, "pieces", mi, mi + 1))))


def match_seq(mi, winners):
    """Pin a whole match's round order — the only way to state a lead later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PPYPPP",      # m1   1-5
    "YPYPPPYYP",   # m2   4-5   <- yachi won two straight to level 4-4, lost the last
    "PYPYYYPY",    # m3   5-3
    "YPPYPYPYY",   # m4   5-4   <- yachi trailed 3-4 and won the last two
    "PPPYPP",      # m5   1-5
    "PPYYPPYYP",   # m6   4-5
    "PPYYPPYP",    # m7   3-5
    "YYYYY",       # m8   5-0   <- yachi's shutout
    "PPPYPP",      # m9   1-5
    "YPPYPYYPP",   # m10  4-5   <- yachi led 4-3 and lost the last two
    "PYPPPYP",     # m11  2-5
    "YYPPYYPY",    # m12  5-3
    "PPPPP",       # m13  0-5   <- pinglamb's shutout
    "PYYYPPPP",    # m14  3-5   <- yachi led 3-1, then lost four straight
    "YYPPPPP",     # m15  2-5
    "YPYYYY",      # m16  5-1
    "YPPPYYPP",    # m17  3-5
    "YYPYYY",      # m18  5-1
    "PYYYPPPP",    # m19  3-5   <- yachi led 3-1, then lost four straight
    "PPPYYPYP",    # m20  3-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (2, 3, 7, 11, 15, 17)
# The one match whose winner did NOT have the higher attack per piece, 0-based (m12).
SIGN_EXCEPTION = 11

MATCH_CANTO = [
    ("第一場 yachi 淨係贏到第三局，1 比 5",
     "match 1: yachi took only the third round, 1-5"),
    ("第二場 yachi 第七第八局連贏追到 4 比 4，最後一局俾人攞走，4 比 5",
     "match 2: yachi won the seventh and eighth to level at 4-4 and lost the last, 4-5"),
    ("第三場 yachi 中段連贏三局反超前，5 比 3",
     "match 3: yachi won three straight in the middle to go ahead and took it 5-3"),
    ("第四場 yachi 落後 3 比 4，尾兩局連贏，5 比 4",
     "match 4: yachi trailed 3-4 and won the last two to take it 5-4"),
    ("第五場 yachi 淨係贏到第四局，1 比 5",
     "match 5: yachi took only the fourth round, 1-5"),
    ("第六場兩局兩局咁交換，打到最後一局，4 比 5",
     "match 6: traded in pairs to the last round, 4-5"),
    ("第七場 yachi 第三第四局連贏追平 2 比 2，之後四局得返一局，3 比 5",
     "match 7: yachi won the third and fourth to level at 2-2, then took one of the last four, 3-5"),
    ("第八場 yachi 五局全取，5 比 0",
     "match 8: yachi won all five rounds, 5-0"),
    ("第九場 yachi 淨係贏到第四局，1 比 5",
     "match 9: yachi took only the fourth round, 1-5"),
    ("第十場 yachi 打到 4 比 3 領先，尾兩局連失，4 比 5",
     "match 10: yachi led 4-3 and lost the last two, 4-5"),
    ("第十一場 yachi 淨係贏到第二同第六局，2 比 5",
     "match 11: yachi took only the second and sixth rounds, 2-5"),
    ("第十二場 yachi 開波連贏兩局，5 比 3",
     "match 12: yachi won the first two and took it 5-3"),
    ("第十三場 yachi 一局都冇贏，0 比 5",
     "match 13: yachi won no round at all, 0-5"),
    ("第十四場 yachi 打到 3 比 1 領先，跟住連失四局，3 比 5",
     "match 14: yachi led 3-1, then lost four straight, 3-5"),
    ("第十五場 yachi 開波連贏兩局，之後五局全失，2 比 5",
     "match 15: yachi won the first two then lost five straight, 2-5"),
    ("第十六場 yachi 淨係輸咗第二局，5 比 1",
     "match 16: yachi dropped only the second round, 5-1"),
    ("第十七場 yachi 由 1 比 3 追到 3 比 3，尾兩局連失，3 比 5",
     "match 17: yachi came back from 1-3 to level at 3-3, then lost the last two, 3-5"),
    ("第十八場 yachi 淨係輸咗第三局，5 比 1",
     "match 18: yachi dropped only the third round, 5-1"),
    ("第十九場 yachi 打到 3 比 1 領先，跟住連失四局，3 比 5",
     "match 19: yachi led 3-1, then lost four straight, 3-5"),
    ("第二十場 yachi 開波連輸三局，追到 3 比 4，最後一局俾人攞走，3 比 5",
     "match 20: yachi lost the first three, closed to 3-4, and lost the last, 3-5"),
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
        "canto": "二十場 match 打成 6 比 14：yachi 攞到第三、第四、第八、第十二、第十六同第十八場，"
                 "其餘十四場俾 pinglamb 攞晒",
        "english_gloss": "pinglamb won the series fourteen matches to six: yachi won matches 3, "
                         "4, 8, 12, 16 and 18",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，兩邊都爭得唔多：贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 4.70%，"
                 "輸嗰啲局高 5.83%",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 4.70 percent above "
                         "yachi's, and in the rounds each lost it is 5.83 percent above",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 470),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 583),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 21.46%，pinglamb 高 20.17%，今次闊啲嗰個係 yachi",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 21.46 percent and pinglamb by 20.17 "
                         "percent, yachi the wider",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 2146),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 2017),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 7.24%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 7.24 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 724),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 328 粒方塊，打出嘅攻擊反而少 395 條，"
                 "即係 pinglamb 總攻擊嘅 4.53%",
        "english_gloss": "yachi placed 328 more pieces than pinglamb yet landed 395 less attack, "
                         "4.53 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(328)),
            eq(sub(atk(P), atk(Y)), lit(395)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(453), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(454), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 27 局頂到上天花板收場，14 局係 yachi 頂爆、13 局係 pinglamb",
        "english_gloss": "twenty-seven rounds ended in a topout, fourteen of them yachi's and "
                         "thirteen pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(14)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(13)),
        ),
    },
    {
        "id": "C007",
        "category": "style",
        "canto": "二十場 match 排開，個效率差距同邊個贏場波分得開：yachi 贏嗰六場，"
                 "pinglamb 每粒方塊嘅攻擊高唔夠 4%；pinglamb 贏嗰十四場，佢每場都高過 6%，"
                 "中間一場都冇",
        "english_gloss": "in each of the six matches yachi won, pinglamb's attack per piece is "
                         "less than 4 percent above yachi's; in each of the fourteen matches "
                         "pinglamb won it is more than 6 percent above",
        "spec": conj(*[(match_gap_under(mi, 104) if mi in YACHI_MATCHES
                        else match_gap_over(mi, 106))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.614 下，pinglamb 3.591 下，"
                 "yachi 高 pinglamb 0.63%",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.614 and pinglamb "
                         "3.591, yachi 0.63 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3614),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3591),
            gap_x100(sum_round(Y, "inputs"), pieces(Y), sum_round(P, "inputs"), pieces(P), 63),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 328 粒方塊盈餘，即係多過 pinglamb 2.38%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 2.38 個百分點，而 C004 個窿係 7.24%",
        "english_gloss": "yachi's piece count is 2.38 percent above pinglamb's, against the "
                         "7.24 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10238), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10239), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 64 比 82。五場一截切開：16 比 22、17 比 20、12 比 23、19 比 17——"
                 "yachi 淨係喺最後五場贏多過對手，第三截係佢最差嗰截。"
                 "四截局數唔同（38、37、35、36 局），所以要當比率比。打完十五場係 45 比 65",
        "english_gloss": "the rounds finished 64 to 82; in blocks of five matches they went 16-22, "
                         "17-20, 12-23 and 19-17, so yachi out-won pinglamb only in the last block "
                         "and his round-win rate was lowest in the third and highest in the "
                         "fourth; after fifteen matches it stood 45 to 65",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 64),
            rounds_won_in(P, 0, MATCHES, 82),
            rounds_won_in(Y, 0, 5, 16), rounds_won_in(P, 0, 5, 22),
            rounds_won_in(Y, 5, 10, 17), rounds_won_in(P, 5, 10, 20),
            rounds_won_in(Y, 10, 15, 12), rounds_won_in(P, 10, 15, 23),
            rounds_won_in(Y, 15, 20, 19), rounds_won_in(P, 15, 20, 17),
            rounds_won_in(Y, 0, 15, 45), rounds_won_in(P, 0, 15, 65),
            block_rate_lt(2, 0), block_rate_lt(2, 1), block_rate_lt(2, 3),
            block_rate_lt(0, 3), block_rate_lt(1, 3),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C031",
        "category": "style",
        "canto": "逐場計每粒方塊嘅攻擊，邊個高邊個就贏咗嗰場——二十場入面十九場係咁。"
                 "唯一例外係第十二場：pinglamb 每粒方塊高啲，但 yachi 5 比 3 贏咗",
        "english_gloss": "in nineteen of the twenty matches the player with the higher attack per "
                         "piece won it; the exception is match 12, which yachi won while "
                         "pinglamb's attack per piece was higher",
        "spec": conj(*[conj(match_winner(mi, Y if mi in YACHI_MATCHES else P),
                            app_leads(mi, P if mi == SIGN_EXCEPTION
                                      else (Y if mi in YACHI_MATCHES else P)))
                       for mi in range(MATCHES)]),
    },
]
