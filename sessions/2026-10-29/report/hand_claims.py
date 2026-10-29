"""Hand-written claims for 2026-10-29 — what a generator cannot say about this night.

**Nine matches and 68 rounds, pinglamb 6-3 in matches and 38-30 in rounds** [C001][C010]. The
twentieth session in date order and in arrival. No match is a 5-0; m9 is the only one to go to a
ninth round.

**C010 is the night in thirds, and yachi's round-win rate rises through all three:** m1-m3 8-15
(pinglamb won all three), m4-m6 8-13 (yachi won one), m7-m9 14-10 (yachi won two). The windows
are the same size in matches and not in rounds, so the comparison is cross-multiplied.

**The regime split is the MIRROR shape** (08-14's, 09-10's, 09-18's, 10-20's):

    attack per piece   won rounds    pinglamb above yachi by  +15.72%
                       lost rounds   pinglamb above yachi by   +3.86%

C002 pins both to the hundredth (floored). The lost gap carries a leave-one-out caveat (m2r3) in
CLAUDE.md; the ledger pins no rank.

**C003 is each player against himself**: yachi +13.32%, pinglamb +26.27%, pinglamb the wider.

**C004 / C005 / C009 are the volume route.** pinglamb's attack per piece is 11.06% above yachi's;
yachi threw 417 more pieces, 7.29% more, and finished 124 lines of attack short, 3.39% of
pinglamb's total.

**C006 is the death tally, 5 against 6.** **C008 pins keypresses per piece**, yachi's 0.90% above.

**C020 is the sign, and it does not decide**: pinglamb's attack per piece is the higher in all
nine matches, yachi's three wins included. **C021: the attack TOTAL decided seven of the nine.**
The exceptions are m3 (pinglamb won with less attack) and m7 (yachi won with less attack).

**NO C007 IS MINTED.** Ordered by pinglamb's per-match APP advantage:

    m4 +1.05 Y  m8 +2.83 Y  m3 +4.23 P  m9 +6.67 P  m7 +8.07 Y  m5 +14.98 P
    m1 +16.60 P  m6 +23.13 P  m2 +32.15 P

m3 and m9, pinglamb wins, sit below m7, a yachi win, so no cut exists; 1/C(9,3) = 1 in 84.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 9
# The windows C010 pins, as [lo, hi) match positions: the night in thirds, m1-m3, m4-m6, m7-m9.
FIRST, MIDDLE, LAST = (0, 3), (3, 6), (6, 9)


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
    "YPPPYPP",     # m1   2-5
    "YPYYPPPP",    # m2   3-5
    "YYYPPPPP",    # m3   3-5   <- led 3-0, lost the last five
    "YYPPYYPY",    # m4   5-3
    "PPPYPP",      # m5   1-5
    "YPPPYPP",     # m6   2-5
    "YYYPYPPY",    # m7   5-3
    "PYPYYYY",     # m8   5-2
    "PYYYPYPPP",   # m9   4-5   <- led 4-2, lost the last three
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (3, 6, 7)
# The matches whose winner landed the LOWER attack total, 0-based (m3 pinglamb's, m7 yachi's).
VOLUME_EXCEPTIONS = (2, 6)

MATCH_CANTO = [
    ("第一場 pinglamb 5 比 2，yachi 淨係贏到第一同第五局",
     "match 1: pinglamb won 5-2, yachi taking only the first and fifth rounds"),
    ("第二場 yachi 3 比 1 領先，pinglamb 尾四局連贏，3 比 5",
     "match 2: yachi led 3-1, then pinglamb won the last four rounds, 3-5"),
    ("第三場 yachi 頭三局連贏 3 比 0，之後 pinglamb 連贏五局，3 比 5",
     "match 3: yachi won the first three rounds, then pinglamb won five straight, 3-5"),
    ("第四場 yachi 5 比 3",
     "match 4: yachi won 5-3"),
    ("第五場 pinglamb 5 比 1，yachi 淨係贏到第四局",
     "match 5: pinglamb won 5-1, yachi taking only the fourth round"),
    ("第六場 pinglamb 5 比 2，yachi 淨係贏到第一同第五局",
     "match 6: pinglamb won 5-2, yachi taking only the first and fifth rounds"),
    ("第七場 yachi 頭三局連贏，5 比 3",
     "match 7: yachi won the first three rounds and the match 5-3"),
    ("第八場 打到 2 比 2，yachi 尾三局連贏，5 比 2",
     "match 8: level at 2-2, yachi won the last three rounds, 5-2"),
    ("第九場 yachi 4 比 2 領先，尾三局連失，4 比 5",
     "match 9: yachi led 4-2, then lost the last three rounds, 4-5"),
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


def winner(mi):
    return Y if mi in YACHI_MATCHES else P


def other(pl):
    return P if pl == Y else Y


CLAIMS = [
    {
        "id": "C001",
        "category": "score",
        "canto": "九場 match pinglamb 贏 6 場：yachi 攞第四、第七同第八場，其餘六場都係 pinglamb",
        "english_gloss": "pinglamb won six of the nine matches; yachi won matches 4, 7 and 8",
        "spec": conj(*[match_winner(mi, winner(mi)) for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 15.72%，"
                 "輸嗰啲局淨係高 3.86%——差距喺贏局，輸局兩個人貼得好埋",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 15.72 percent "
                         "above yachi's, and in the rounds each lost only 3.86 percent above",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 1572),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 386),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 13.32%，pinglamb 高 26.27%，今次闊啲嗰個係 pinglamb",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 13.32 percent and pinglamb by 26.27 "
                         "percent, pinglamb the wider",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1332),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 2627),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 11.06%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 11.06 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 1106),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 417 粒方塊，總攻擊仍然少過 pinglamb 124 條，"
                 "即係 pinglamb 總攻擊嘅 3.39%",
        "english_gloss": "yachi placed 417 more pieces than pinglamb and still landed 124 fewer "
                         "lines of attack, 3.39 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(417)),
            eq(sub(atk(P), atk(Y)), lit(124)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(339), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(340), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 11 局頂到上天花板收場：yachi 5 局，pinglamb 6 局",
        "english_gloss": "eleven rounds ended in a topout: five yachi's, six pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(5)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(6)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.618 下，pinglamb 3.586 下，"
                 "yachi 高 pinglamb 0.90%",
        "english_gloss": "keypresses per piece are close: yachi 3.618 and pinglamb 3.586, "
                         "yachi 0.90 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3618),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3586),
            gap_x100(sum_round(Y, "inputs"), pieces(Y), sum_round(P, "inputs"), pieces(P), 90),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 417 粒方塊盈餘，即係多過 pinglamb 7.29%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 7.29 個百分點，填唔晒 C004 個 11.06% 窿",
        "english_gloss": "yachi's piece count is 7.29 percent above pinglamb's, short of the "
                         "11.06 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10729), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10730), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 30 比 38。分三段睇：第一到第三場三場全輸，局數 8 比 15；"
                 "第四到第六場贏一場，局數 8 比 13；第七到第九場贏兩場，局數 14 比 10——"
                 "yachi 每段嘅贏局率都高過上一段",
        "english_gloss": "the rounds finished 30 to 38; matches 1-3 went 8-15, matches 4-6 8-13 "
                         "and matches 7-9 14-10, so yachi's round-win rate rose from each third "
                         "of the night to the next",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 30),
            rounds_won_in(P, 0, MATCHES, 38),
            rounds_won_in(Y, *FIRST, 8), rounds_won_in(P, *FIRST, 15),
            rounds_won_in(Y, *MIDDLE, 8), rounds_won_in(P, *MIDDLE, 13),
            rounds_won_in(Y, *LAST, 14), rounds_won_in(P, *LAST, 10),
            window_rate_lt(FIRST, MIDDLE),
            window_rate_lt(MIDDLE, LAST),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C020",
        "category": "style",
        "canto": "九場入面場場都係 pinglamb 每粒方塊嘅攻擊高，連 yachi 贏嗰三場都係；"
                 "差得最少嗰場係第四場，唔夠 2%，最多嗰場係第二場，超過 32%",
        "english_gloss": "pinglamb's attack per piece is the higher in all nine matches, yachi's "
                         "three wins included; the smallest gap is match 4's, under 2 percent, "
                         "and the largest match 2's, over 32 percent",
        "spec": conj(*[app_leads(mi, P) for mi in range(MATCHES)],
                     app_lt_pct(3, 2), app_gt_pct(1, 32)),
    },
    {
        "id": "C021",
        "category": "style",
        "canto": "逐場計總攻擊，打得多嗰個九場贏七場。兩場例外：第三場 yachi 總攻擊多啲但係輸，"
                 "第七場 pinglamb 總攻擊多啲但係 yachi 贏",
        "english_gloss": "in seven of the nine matches the player who landed more attack won; "
                         "the exceptions are match 3, which pinglamb won with less attack, and "
                         "match 7, which yachi won with less attack",
        "spec": conj(*[conj(match_winner(mi, winner(mi)),
                            attack_leads(mi, other(winner(mi)) if mi in VOLUME_EXCEPTIONS
                                         else winner(mi)))
                       for mi in range(MATCHES)]),
    },
]
