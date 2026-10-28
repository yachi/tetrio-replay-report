"""Hand-written claims for 2026-10-20 — what a generator cannot say about this night.

**Four matches and 30 rounds, 2-2 in matches and 15-15 in rounds.** The eighteenth session in
date order and in arrival, and the second drawn one after 09-10's 4-4 — but 09-10's rounds were
32-33, so this is the first session level on BOTH measures. It is also the smallest by matches
(four, against 08-09's and 09-03's six) and by rounds (30, against 09-03's 46). yachi won the
first two matches, 10-5 in rounds; pinglamb won the last two, 5-10 [C001][C010]. The night is
two halves of fifteen rounds that mirror each other exactly.

**THE VOLUME ROUTE MORE THAN COVERED THE GAP, by more than any night has.** C004's session gap
is +6.73%: pinglamb's attack per piece is that much above yachi's. yachi threw 323 more pieces,
11.18% more than pinglamb [C009], so the surplus buys back about 11.18 points of a 6.73-point
gap — a shortfall near −4.45, the lowest in the corpus, past 10-09's −1.12 — and yachi's attack
total is the higher: 2000 against 1920, 80 lines and 4.16% of pinglamb's total [C005]. The series
was still drawn.

**C015 is what decided each match: the attack TOTAL, all four.** In m1 pinglamb had the higher
attack per piece and yachi won anyway, on volume; in m4 yachi had the lower attack per piece AND
the lower total, and lost. C016 is the sign: pinglamb's attack per piece is the higher in m1, m3
and m4, and yachi's in m2 by more than 7%.

**NO C007 IS MINTED, and the id is left empty**, following 09-10, 09-11, 09-19 and 10-09. Order
the four matches by pinglamb's per-piece advantage:

    m2 -7.37 Y   m4 +8.28 P   m1 +10.52 Y   m3 +11.20 P

m4, a pinglamb win, sits below m1, a yachi win, so no cut exists — and two wins among four is
1/C(4,2) = 1 in 6, which is degenerate even had it separated.

**THE REGIMES ARE THE MIRROR SHAPE: CEILINGS APART, FLOORS LEVEL.**

    attack per piece   won rounds    pinglamb above yachi by  +7.23%
                       lost rounds   pinglamb above yachi by  +1.27%

C002 pins both to the hundredth (floored). The ledger pins no rank.

**C003 is each player against himself**: yachi +12.36%, pinglamb +18.97%, pinglamb the wider.

**C006 is the death tally, 0 against 2** — yachi topped out in none of the 30 rounds.

**C008 pins keypresses per piece, pooled: yachi 3.631 and pinglamb 3.637, pinglamb 0.16% above.**

**C010 is the night's shape.** Rounds 15-15. The first two matches went 10-5 and the last two
5-10; the windows are the same size, and their order is pinned as cross-multiplied rates anyway.

The claims are of six kinds:

  * **the shape of the night** — C001 pins all four match winners at once, C010 the halves.
  * **the two regimes** — C002 and C004.
  * **each player against himself** — C003.
  * **the route and its price** — C005 and C009.
  * **the death tally** — C006.
  * **the four matches** — C011-C014 as `round_seq` runs, C015 (totals) and C016 (sign).
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 4
# The windows C010 pins, as [lo, hi) match positions.
FIRST, SECOND = (0, 2), (2, 4)


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


def window_rate_lt(a, b):
    """yachi's round-win RATE over window `a` is below his rate over window `b`.

    The windows hold different numbers of rounds, so the counts are not comparable; the
    denominators are each window's own round count, read out of the data as the sum of both
    players' `alive`, not written as literals.
    """
    ya = window(Y, "alive", *a)
    yb = window(Y, "alive", *b)
    ta = add(ya, window(P, "alive", *a))
    tb = add(yb, window(P, "alive", *b))
    return lt(mul(ya, tb), mul(yb, ta))


def app_leads(mi, leader):
    """`leader`'s attack per piece is strictly higher than the other's over match `mi`."""
    other = P if leader == Y else Y
    return gt(mul(window(leader, "garbage_attack", mi, mi + 1), window(other, "pieces", mi, mi + 1)),
              mul(window(other, "garbage_attack", mi, mi + 1), window(leader, "pieces", mi, mi + 1)))


def attack_leads(mi, leader):
    """`leader` landed strictly more attack than the other over match `mi`."""
    other = P if leader == Y else Y
    return gt(window(leader, "garbage_attack", mi, mi + 1),
              window(other, "garbage_attack", mi, mi + 1))


def pieces_lead(mi, leader):
    """`leader` placed strictly more pieces than the other over match `mi`."""
    other = P if leader == Y else Y
    return gt(window(leader, "pieces", mi, mi + 1), window(other, "pieces", mi, mi + 1))


def match_seq(mi, winners):
    """Pin a whole match's round order — the only way to state a lead later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "YYPPPPYYY",   # m1   5-4   <- led 2-0, trailed 2-4, won the last three
    "YYPYYY",      # m2   5-1
    "PYPPPYP",     # m3   2-5
    "PPYYYPPP",    # m4   3-5   <- trailed 0-2, led 3-2, lost the last three
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (0, 1)
# The one match in which yachi's attack per piece is the higher, 0-based (m2).
SIGN_EXCEPTION = 1

MATCH_CANTO = [
    ("第一場 yachi 2 比 0 開波，之後連輸四局 2 比 4 落後，尾三局連贏，5 比 4",
     "match 1: yachi led 2-0, trailed 2-4 after four straight losses, then won the last three, 5-4"),
    ("第二場 yachi 頭兩局贏、第三局輸，之後連贏三局，5 比 1",
     "match 2: yachi won the first two rounds, lost the third, then won three straight, 5-1"),
    ("第三場 pinglamb 5 比 2，yachi 淨係贏到第二同第六局",
     "match 3: pinglamb won 5-2, yachi taking only the second and sixth rounds"),
    ("第四場 yachi 0 比 2 落後，連贏三局 3 比 2 反超，尾三局連失，3 比 5",
     "match 4: yachi trailed 0-2, won three straight to lead 3-2, then lost the last three, 3-5"),
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
        "canto": "四場 match 打成 2 比 2：yachi 攞頭兩場，pinglamb 攞尾兩場",
        "english_gloss": "the series was drawn two matches each: yachi won matches 1 and 2, "
                         "pinglamb matches 3 and 4",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 7.23%，"
                 "輸嗰啲局淨係高 1.27%",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 7.23 percent "
                         "above yachi's, and in the rounds each lost it is only 1.27 percent above",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 723),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 127),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 12.36%，pinglamb 高 18.97%，今次闊啲嗰個係 pinglamb",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 12.36 percent and pinglamb by 18.97 "
                         "percent, pinglamb the wider",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1236),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1897),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 6.73%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 6.73 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 673),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 323 粒方塊，總攻擊反而多過 pinglamb 80 條，"
                 "即係 pinglamb 總攻擊嘅 4.16%",
        "english_gloss": "yachi placed 323 more pieces than pinglamb and landed 80 more lines "
                         "of attack, 4.16 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(323)),
            eq(sub(atk(Y), atk(P)), lit(80)),
            ge_(mul(lit(10000), sub(atk(Y), atk(P))), mul(lit(416), atk(P))),
            lt(mul(lit(10000), sub(atk(Y), atk(P))), mul(lit(417), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚得 2 局頂到上天花板收場，兩局都係 pinglamb；yachi 一局都冇",
        "english_gloss": "two rounds ended in a topout, both pinglamb's; yachi topped out in none",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(0)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(2)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人幾乎一樣：yachi 3.631 下，pinglamb 3.637 下，"
                 "pinglamb 高 yachi 0.16%",
        "english_gloss": "keypresses per piece are almost equal: yachi 3.631 and pinglamb 3.637, "
                         "pinglamb 0.16 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3631),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3637),
            gap_x100(sum_round(P, "inputs"), pieces(P), sum_round(Y, "inputs"), pieces(Y), 16),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 323 粒方塊盈餘，即係多過 pinglamb 11.18%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 11.18 個百分點，大過 C004 個 6.73% 窿",
        "english_gloss": "yachi's piece count is 11.18 percent above pinglamb's, more than the "
                         "6.73 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(11118), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(11119), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 15 比 15。頭兩場 10 比 5，兩場都係 yachi；尾兩場 5 比 10，兩場都係 "
                 "pinglamb——兩段各 15 局，啱啱好倒轉",
        "english_gloss": "the rounds finished 15 to 15; the first two matches went 10-5 and the "
                         "last two 5-10, so yachi's round-win rate was lower in the second half",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 15),
            rounds_won_in(P, 0, MATCHES, 15),
            rounds_won_in(Y, *FIRST, 10), rounds_won_in(P, *FIRST, 5),
            rounds_won_in(Y, *SECOND, 5), rounds_won_in(P, *SECOND, 10),
            window_rate_lt(SECOND, FIRST),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C015",
        "category": "style",
        "canto": "逐場計總攻擊，打得多嗰個四場全贏。第一場 pinglamb 每粒方塊嘅攻擊高啲，"
                 "但 yachi 落多咗粒數、總攻擊多過對手，係 yachi 贏",
        "english_gloss": "in all four matches the player who landed more attack won it; in "
                         "match 1 pinglamb's attack per piece was the higher, but yachi placed "
                         "more pieces, landed more attack and won",
        "spec": conj(*[conj(match_winner(mi, Y if mi in YACHI_MATCHES else P),
                            attack_leads(mi, Y if mi in YACHI_MATCHES else P))
                       for mi in range(MATCHES)],
                     app_leads(0, P), pieces_lead(0, Y)),
    },
    {
        "id": "C016",
        "category": "style",
        "canto": "四場入面，淨係第二場 yachi 每粒方塊嘅攻擊高過 pinglamb，而且高過 7%；"
                 "其餘三場都係 pinglamb 高",
        "english_gloss": "only in match 2 is yachi's attack per piece the higher, by more than "
                         "7 percent; in the other three matches pinglamb's is the higher",
        "spec": conj(
            gt(mul(lit(100), mul(window(Y, "garbage_attack", 1, 2), window(P, "pieces", 1, 2))),
               mul(lit(107), mul(window(P, "garbage_attack", 1, 2), window(Y, "pieces", 1, 2)))),
            *[app_leads(mi, P) for mi in range(MATCHES) if mi != SIGN_EXCEPTION],
        ),
    },
]
