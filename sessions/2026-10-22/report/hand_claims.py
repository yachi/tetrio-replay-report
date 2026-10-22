"""Hand-written claims for 2026-10-22 — what a generator cannot say about this night.

**Nine matches and 63 rounds, pinglamb 6-3 in matches and 38-25 in rounds** [C001][C010]. The
nineteenth session in date order and in arrival. pinglamb has two 5-0 matches (m5, m9).

**THE SESSION APP GAP IS THE CORPUS RECORD.** C004 pins pinglamb's attack per piece 20.59% above
yachi's, past 09-17's 20.11%. yachi threw 573 more pieces, 9.99% more [C009], so the volume route
covers about half the gap and yachi's attack total is 349 lines short, 8.79% of pinglamb's [C005].

**BOTH REGIME GAPS ARE LARGE, the second session after 09-17 where they are.**

    attack per piece   won rounds    pinglamb above yachi by  +15.16%
                       lost rounds   pinglamb above yachi by  +20.12%

C002 pins both to the hundredth (floored). The ledger pins no rank; the ranks are CLAUDE.md's.

**C003 is each player against himself**: yachi +21.20%, pinglamb +16.20%, yachi the wider.

**C006 is the death tally, 5 against 1.** **C008 pins keypresses per piece**, yachi's 1.01% above.

**C010 is the night's shape**, four windows: m1 5-4 to yachi, m2-m5 6-20 (pinglamb won all four),
m6-m8 14-9 (yachi won two of three), m9 0-5. yachi's round-win rate in m6-m8 is above his rate in
m2-m5; the windows differ in size, so the comparison is cross-multiplied.

**C020 is the sign, and it does not decide**: pinglamb's attack per piece is the higher in all
nine matches, yachi's three wins included. **C021 is what decided seven of the nine: the attack
TOTAL.** The two exceptions are m1 and m6, both yachi wins in which pinglamb landed more attack.

**NO C007 IS MINTED.** Ordered by pinglamb's per-match APP advantage:

    m8 +7.97 Y  m1 +13.61 Y  m7 +17.28 P  m6 +18.03 Y  m2 +23.20 P  m4 +26.36 P
    m9 +30.59 P  m3 +31.27 P  m5 +31.50 P

m7, a pinglamb win, sits below m6, a yachi win, so no cut exists; 1/C(9,3) = 1 in 84.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 9
# The windows C010 pins, as [lo, hi) match positions: m1, m2-m5, m6-m8, m9.
OPEN, SLUMP, RALLY, CLOSE = (0, 1), (1, 5), (5, 8), (8, 9)


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
    "PPYYYPYPY",   # m1   5-4
    "YPYPPPYP",    # m2   3-5
    "YPPPYPP",     # m3   2-5
    "PPPYPP",      # m4   1-5
    "PPPPP",       # m5   0-5
    "YYPYPYY",     # m6   5-2
    "YPPYYYPPP",   # m7   4-5   <- led 4-2, lost the last three
    "YYPPYYY",     # m8   5-2
    "PPPPP",       # m9   0-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (0, 5, 7)
# yachi's wins in which pinglamb landed the higher attack total, 0-based (m1, m6).
VOLUME_EXCEPTIONS = (0, 5)

MATCH_CANTO = [
    ("第一場 yachi 0 比 2 落後，連贏三局反超，之後一人一局，第九局 5 比 4 收",
     "match 1: yachi trailed 0-2, won three straight, then the rounds alternated and he took the ninth, 5-4"),
    ("第二場 yachi 2 比 1 領先，pinglamb 連贏三局，yachi 追到 3 比 4，第八局 pinglamb 收，3 比 5",
     "match 2: yachi led 2-1, pinglamb won three straight, yachi pulled back to 3-4, pinglamb took the eighth, 3-5"),
    ("第三場 pinglamb 5 比 2，yachi 淨係贏到第一同第五局",
     "match 3: pinglamb won 5-2, yachi taking only the first and fifth rounds"),
    ("第四場 pinglamb 5 比 1，yachi 淨係贏到第四局",
     "match 4: pinglamb won 5-1, yachi taking only the fourth round"),
    ("第五場 pinglamb 5 比 0",
     "match 5: pinglamb won 5-0"),
    ("第六場 yachi 5 比 2，pinglamb 淨係贏到第三同第五局",
     "match 6: yachi won 5-2, pinglamb taking only the third and fifth rounds"),
    ("第七場 yachi 4 比 2 領先，尾三局連失，4 比 5",
     "match 7: yachi led 4-2, then lost the last three rounds, 4-5"),
    ("第八場 打到 2 比 2，yachi 尾三局連贏，5 比 2",
     "match 8: level at 2-2, yachi won the last three rounds, 5-2"),
    ("第九場 pinglamb 5 比 0",
     "match 9: pinglamb won 5-0"),
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


def app_gt_pct(mi, pct):
    """pinglamb's attack per piece over match `mi` is more than `pct` percent above yachi's."""
    return gt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1), window(Y, "pieces", mi, mi + 1))),
              mul(lit(100 + pct), mul(window(Y, "garbage_attack", mi, mi + 1), window(P, "pieces", mi, mi + 1))))


def app_lt_pct(mi, pct):
    """pinglamb's attack per piece over match `mi` is less than `pct` percent above yachi's."""
    return lt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1), window(Y, "pieces", mi, mi + 1))),
              mul(lit(100 + pct), mul(window(Y, "garbage_attack", mi, mi + 1), window(P, "pieces", mi, mi + 1))))


CLAIMS = [
    {
        "id": "C001",
        "category": "score",
        "canto": "九場 match pinglamb 贏 6 場：yachi 攞第一、第六同第八場，其餘六場都係 pinglamb",
        "english_gloss": "pinglamb won six of the nine matches; yachi won matches 1, 6 and 8",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 15.16%，"
                 "輸嗰啲局更加高 20.12%——兩邊都闊",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 15.16 percent "
                         "above yachi's, and in the rounds each lost it is 20.12 percent above",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 1516),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 2012),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 21.20%，pinglamb 高 16.20%，今次闊啲嗰個係 yachi",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 21.20 percent and pinglamb by 16.20 "
                         "percent, yachi the wider",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 2120),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1620),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 20.59%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 20.59 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 2059),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 573 粒方塊，總攻擊仍然少過 pinglamb 349 條，"
                 "即係 pinglamb 總攻擊嘅 8.79%",
        "english_gloss": "yachi placed 573 more pieces than pinglamb and still landed 349 fewer "
                         "lines of attack, 8.79 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(573)),
            eq(sub(atk(P), atk(Y)), lit(349)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(879), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(880), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 6 局頂到上天花板收場：yachi 5 局，pinglamb 1 局",
        "english_gloss": "six rounds ended in a topout: five yachi's, one pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(5)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(1)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.620 下，pinglamb 3.583 下，"
                 "yachi 高 pinglamb 1.01%",
        "english_gloss": "keypresses per piece are close: yachi 3.620 and pinglamb 3.583, "
                         "yachi 1.01 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3620),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3583),
            gap_x100(sum_round(Y, "inputs"), pieces(Y), sum_round(P, "inputs"), pieces(P), 101),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 573 粒方塊盈餘，即係多過 pinglamb 9.99%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 9.99 個百分點，唔夠 C004 個 20.59% 窿嘅一半",
        "english_gloss": "yachi's piece count is 9.99 percent above pinglamb's, less than half "
                         "the 20.59 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10999), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(11000), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 25 比 38。第一場 yachi 5 比 4；第二到第五場四場全輸，局數 6 比 20；"
                 "第六到第八場贏兩場，局數 14 比 9；第九場 0 比 5",
        "english_gloss": "the rounds finished 25 to 38; match 1 went 5-4 to yachi, matches 2-5 "
                         "6-20, matches 6-8 14-9 and match 9 0-5, so yachi's round-win rate in "
                         "matches 2-5 was below his rate in matches 6-8",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 25),
            rounds_won_in(P, 0, MATCHES, 38),
            rounds_won_in(Y, *OPEN, 5), rounds_won_in(P, *OPEN, 4),
            rounds_won_in(Y, *SLUMP, 6), rounds_won_in(P, *SLUMP, 20),
            rounds_won_in(Y, *RALLY, 14), rounds_won_in(P, *RALLY, 9),
            rounds_won_in(Y, *CLOSE, 0), rounds_won_in(P, *CLOSE, 5),
            window_rate_lt(SLUMP, RALLY),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C020",
        "category": "style",
        "canto": "九場入面場場都係 pinglamb 每粒方塊嘅攻擊高，連 yachi 贏嗰三場都係；"
                 "差得最少嗰場係第八場，唔夠 8%，最多嗰場係第五場，超過 31%",
        "english_gloss": "pinglamb's attack per piece is the higher in all nine matches, yachi's "
                         "three wins included; the smallest gap is match 8's, under 8 percent, "
                         "and the largest match 5's, over 31 percent",
        "spec": conj(*[app_leads(mi, P) for mi in range(MATCHES)],
                     app_lt_pct(7, 8), app_gt_pct(4, 31)),
    },
    {
        "id": "C021",
        "category": "style",
        "canto": "逐場計總攻擊，打得多嗰個九場贏七場。兩場例外係第一同第六場："
                 "pinglamb 總攻擊多啲，但係 yachi 贏",
        "english_gloss": "in seven of the nine matches the player who landed more attack won; "
                         "the exceptions are matches 1 and 6, which yachi won while pinglamb "
                         "landed more attack",
        "spec": conj(*[conj(match_winner(mi, Y if mi in YACHI_MATCHES else P),
                            attack_leads(mi, P if mi in VOLUME_EXCEPTIONS
                                         else (Y if mi in YACHI_MATCHES else P)))
                       for mi in range(MATCHES)]),
    },
]
