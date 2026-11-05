"""Hand-written claims for 2026-11-05 — what a generator cannot say about this night.

**Eight matches and 67 rounds in the replays, pinglamb 6-2 in matches and 37-30 in rounds**
[C001][C010]. The twenty-second session in date order and in arrival. A ninth match was played
between m6 and m7 and has no replay; the video section reads it (yachi 5-2) and it is in NO
claim here — every figure below is over the eight replayed matches only.

**C010: the night lost its first three matches 9-15 and split the last five 21-22**, yachi
winning two of them (m4, m7); his round-win rate is higher over the last five. Three matches
(m2, m5, m8) went to a ninth round, all lost 4-5.

**The regime split is a first for the corpus: in the rounds each LOST, yachi's attack per piece
is the HIGHER** — pinglamb +12.73% in won rounds [C002], yachi +1.91% in lost ones. C002 pins
both, the second written the way round that is positive. The lost gap carries a leave-one-out
caveat (m7r6) in CLAUDE.md; dropping it moves the gap toward zero and the sign stands.

**C003 is each player against himself**: yachi +11.75%, pinglamb +28.41%.

**C004 / C005 / C009 are the volume route.** pinglamb's attack per piece is 6.14% above yachi's;
yachi threw 392 more pieces, 5.69% more, and finished 18 lines of attack short, 0.42% of
pinglamb's total.

**C006 is the death tally, 5 against 3.** **C008 pins keypresses per piece**, yachi 0.48% above.

**C019: pinglamb's attack per piece is the higher in seven of the eight matches**; m7, a yachi
win, is the one where yachi's is higher. **C020: the attack TOTAL decided seven of the eight**,
the exception m2, which pinglamb won 5-4 with one line less.

**NO C007 IS MINTED.** Ordered by pinglamb's per-match APP advantage:

    m7 -0.17 Y  m5 +3.31 P  m1 +4.91 P  m3 +5.49 P  m2 +6.03 P  m6 +6.98 P
    m4 +7.66 Y  m8 +13.40 P

m4, a yachi win, sits above five pinglamb wins, so no cut exists; 1/C(8,2) = 1 in 28.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 8
# The windows C010 pins, as [lo, hi) match positions: m1-m3 and m4-m8.
FIRST, LAST = (0, 3), (3, 8)


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
    "PPYPYYPP",    # m1   3-5
    "YYPPYPYPP",   # m2   4-5   <- led 2-0
    "PPYPYPP",     # m3   2-5
    "PYYPPYYPY",   # m4   5-4
    "PYYYPPYPP",   # m5   4-5   <- led 3-1, lost the last two
    "YPPPPYYP",    # m6   3-5
    "PYPPYYYY",    # m7   5-3   <- down 1-3, won the last four
    "YPPYPPYYP",   # m8   4-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (3, 6)
# The match whose winner landed the LOWER attack total, 0-based (m2, pinglamb's).
VOLUME_EXCEPTIONS = (1,)
# The match in which yachi's attack per piece is the higher, 0-based (m7).
YACHI_APP_MATCHES = (6,)

MATCH_CANTO = [
    ("第一場 pinglamb 5 比 3",
     "match 1: pinglamb won 5-3"),
    ("第二場 yachi 頭兩局連贏 2 比 0，之後打到第九局，4 比 5 輸",
     "match 2: yachi won the first two rounds, and lost 4-5 in the ninth round"),
    ("第三場 pinglamb 5 比 2",
     "match 3: pinglamb won 5-2"),
    ("第四場 yachi 打到第九局，5 比 4 贏",
     "match 4: yachi won 5-4 in the ninth round"),
    ("第五場 yachi 3 比 1 領先，之後 4 比 4，第九局輸，4 比 5",
     "match 5: yachi led 3-1, it went to 4-4, and he lost the ninth round, 4-5"),
    ("第六場 pinglamb 連贏四局 4 比 1 領先，5 比 3 收",
     "match 6: pinglamb won four straight rounds to lead 4-1, and won 5-3"),
    ("第七場 yachi 1 比 3 落後，尾四局連贏，5 比 3",
     "match 7: yachi trailed 1-3, then won the last four rounds, 5-3"),
    ("第八場 打到第九局，yachi 4 比 5 輸",
     "match 8: yachi lost 4-5 in the ninth round"),
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


def winner(mi):
    return Y if mi in YACHI_MATCHES else P


def other(pl):
    return P if pl == Y else Y


CLAIMS = [
    {
        "id": "C001",
        "category": "score",
        "canto": "有 replay 嘅八場 match pinglamb 贏 6 場：yachi 攞第四同第七場，其餘六場都係 pinglamb",
        "english_gloss": "pinglamb won six of the eight replayed matches; yachi won matches 4 and 7",
        "spec": conj(*[match_winner(mi, winner(mi)) for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 12.73%；"
                 "輸嗰啲局反轉，係 yachi 高 1.91%",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 12.73 percent "
                         "above yachi's, and in the rounds each lost yachi's is 1.91 percent "
                         "above pinglamb's",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 1273),
            gap_x100(lost(Y, "garbage_attack"), lost(Y, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 191),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 11.75%，pinglamb 高 28.41%，闊啲嗰個係 pinglamb",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 11.75 percent and pinglamb by 28.41 "
                         "percent, pinglamb the wider",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1175),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 2841),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 6.14%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 6.14 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 614),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 392 粒方塊，總攻擊淨係少過 pinglamb 18 條，"
                 "即係 pinglamb 總攻擊嘅 0.42%",
        "english_gloss": "yachi placed 392 more pieces than pinglamb and landed only 18 fewer "
                         "lines of attack, 0.42 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(392)),
            eq(sub(atk(P), atk(Y)), lit(18)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(42), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(43), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 8 局頂到上天花板收場：yachi 5 局，pinglamb 3 局",
        "english_gloss": "eight rounds ended in a topout: five yachi's, three pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(5)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(3)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.621 下，pinglamb 3.604 下，"
                 "yachi 高 pinglamb 0.48%",
        "english_gloss": "keypresses per piece are close: yachi 3.621 and pinglamb 3.604, "
                         "yachi 0.48 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3621),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3604),
            gap_x100(sum_round(Y, "inputs"), pieces(Y), sum_round(P, "inputs"), pieces(P), 48),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 392 粒方塊盈餘，即係多過 pinglamb 5.69%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 5.69 個百分點，差少少先填得晒 C004 個 6.14% 窿",
        "english_gloss": "yachi's piece count is 5.69 percent above pinglamb's, a little short of "
                         "the 6.14 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10569), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10570), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 30 比 37。頭三場全輸，局數 9 比 15；尾五場贏兩場，局數 21 比 22——"
                 "yachi 尾五場嘅贏局率高過頭三場",
        "english_gloss": "the rounds finished 30 to 37; matches 1-3 went 9-15 and matches 4-8 "
                         "21-22, so yachi's round-win rate was higher over the last five",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 30),
            rounds_won_in(P, 0, MATCHES, 37),
            rounds_won_in(Y, *FIRST, 9), rounds_won_in(P, *FIRST, 15),
            rounds_won_in(Y, *LAST, 21), rounds_won_in(P, *LAST, 22),
            window_rate_lt(FIRST, LAST),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C019",
        "category": "style",
        "canto": "八場入面七場都係 pinglamb 每粒方塊嘅攻擊高，連 yachi 贏嘅第四場都係；"
                 "淨係第七場係 yachi 高。差得最多嗰場係第八場，超過 13%",
        "english_gloss": "pinglamb's attack per piece is the higher in seven of the eight "
                         "matches, yachi's match 4 included; match 7 is the one where yachi's "
                         "is higher, and the largest gap is match 8's, over 13 percent",
        "spec": conj(*[app_leads(mi, Y if mi in YACHI_APP_MATCHES else P)
                       for mi in range(MATCHES)],
                     app_gt_pct(7, 13)),
    },
    {
        "id": "C020",
        "category": "style",
        "canto": "逐場計總攻擊，打得多嗰個八場贏七場。例外係第二場：yachi 總攻擊多一條，"
                 "但係 4 比 5 輸",
        "english_gloss": "in seven of the eight matches the player who landed more attack won; "
                         "the exception is match 2, which pinglamb won with one line less",
        "spec": conj(*[conj(match_winner(mi, winner(mi)),
                            attack_leads(mi, other(winner(mi)) if mi in VOLUME_EXCEPTIONS
                                         else winner(mi)))
                       for mi in range(MATCHES)],
                     eq(sub(window(Y, "garbage_attack", 1, 2), window(P, "garbage_attack", 1, 2)),
                        lit(1))),
    },
]
