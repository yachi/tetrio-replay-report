"""Hand-written claims for 2026-11-01 — what a generator cannot say about this night.

**Eighteen matches and 130 rounds, pinglamb 11-7 in matches and LEVEL at 65-65 in rounds**
[C001][C010]. The twenty-first session in date order and in arrival, and the first the corpus
holds that is level on rounds and not on matches (09-10 was 4-4 and 32-33, 10-20 2-2 and 15-15).

**C031 is how a level round count loses 11-7**: yachi's seven wins went 35-10 on rounds (5-0 once,
5-1 three times), his eleven losses 30-55 (4-5 twice). He won big and lost close.

**C010 is the night in four stretches:** pinglamb took m1 2-5; yachi m2-m5 20-6 (four straight);
pinglamb m6-m13 20-40 (eight straight); yachi m14-m18 23-14 (three of five). The windows differ in
size; the ledger pins counts only, never a rate across them.

**The regime split is the floors-apart shape** (07-22's, 08-19's, 08-25's, 10-12's):

    attack per piece   won rounds    pinglamb above yachi by  +10.20%
                       lost rounds   pinglamb above yachi by  +14.64%

C002 pins both to the hundredth (floored); the ledger pins no rank.

**C003 is each player against himself**: yachi +20.07%, pinglamb +15.43%, yachi the wider.

**C004 / C005 / C009 are the volume route.** pinglamb's attack per piece is 10.73% above yachi's;
yachi threw 1038 more pieces, 8.76% more, and finished 138 lines of attack short, 1.77% of
pinglamb's total.

**C006 is the death tally, 10 against 16.** **C008 pins keypresses per piece**, yachi's 0.76% above.

**C029 is the sign**: pinglamb's attack per piece is the higher in fourteen matches and yachi's in
four (m3, m4, m17, m18), all four yachi wins. **C030: the attack TOTAL decided seventeen of the
eighteen.** The exception is m5, which yachi won 5-3 with five lines less attack.

**NO C007 IS MINTED.** Ordered by pinglamb's per-match APP advantage:

    m3 -8.89 Y  m18 -4.20 Y  m17 -2.58 Y  m4 -1.48 Y  m2 +2.90 Y  m5 +4.09 Y
    m7 +11.52 P  m14 +11.57 Y  m11 +12.63 P  ...  m16 +30.59 P

m7, a pinglamb win, sits below m14, a yachi win, by 0.05 points, so no cut exists; 1/C(18,7) =
1 in 31 824. C029 pins that inversion.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 18
# The windows C010 pins, as [lo, hi) match positions.
OPEN, YRUN, PRUN, CLOSE = (0, 1), (1, 5), (5, 13), (13, 18)


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
    "PPPPYYP",     # m1   2-5
    "YYPYYPY",     # m2   5-2
    "YYYYPY",      # m3   5-1
    "YYYYY",       # m4   5-0
    "YYPYPPYY",    # m5   5-3
    "PPYPPYYP",    # m6   3-5
    "PPYPYPYP",    # m7   3-5
    "PYPPPYP",     # m8   2-5
    "YPPPPYP",     # m9   2-5
    "PYPPPP",      # m10  1-5
    "PYPPPYYP",    # m11  3-5
    "PYYPPPYP",    # m12  3-5
    "YYPPPYPP",    # m13  3-5
    "YYYYPPY",     # m14  5-2
    "PYYPYPYPP",   # m15  4-5   <- led 4-3, lost the last two
    "PYYYPYPPP",   # m16  4-5   <- led 4-2, lost the last three
    "YYYPYY",      # m17  5-1
    "YPYYYY",      # m18  5-1
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (1, 2, 3, 4, 13, 16, 17)
# The matches whose winner landed the LOWER attack total, 0-based (m5, yachi's).
VOLUME_EXCEPTIONS = (4,)
# The matches in which yachi's attack per piece is the higher, 0-based (m3, m4, m17, m18).
YACHI_APP = (2, 3, 16, 17)

MATCH_CANTO = [
    ("第一場 pinglamb 頭四局連贏，5 比 2",
     "match 1: pinglamb won the first four rounds and the match 5-2"),
    ("第二場 yachi 5 比 2",
     "match 2: yachi won 5-2"),
    ("第三場 yachi 頭四局連贏，5 比 1",
     "match 3: yachi won the first four rounds and the match 5-1"),
    ("第四場 yachi 5 比 0 橫掃",
     "match 4: yachi swept 5-0"),
    ("第五場 yachi 5 比 3，尾兩局連贏收場",
     "match 5: yachi won 5-3, closing with two straight rounds"),
    ("第六場 pinglamb 5 比 3",
     "match 6: pinglamb won 5-3"),
    ("第七場 pinglamb 5 比 3，由第二局起兩個人逐局交替贏",
     "match 7: pinglamb won 5-3, the two alternating round by round from the second round on"),
    ("第八場 pinglamb 5 比 2",
     "match 8: pinglamb won 5-2"),
    ("第九場 yachi 贏第一局，之後 pinglamb 連贏四局，5 比 2",
     "match 9: yachi took the first round, then pinglamb won four straight, 5-2"),
    ("第十場 pinglamb 5 比 1，yachi 淨係贏到第二局",
     "match 10: pinglamb won 5-1, yachi taking only the second round"),
    ("第十一場 pinglamb 5 比 3",
     "match 11: pinglamb won 5-3"),
    ("第十二場 pinglamb 5 比 3",
     "match 12: pinglamb won 5-3"),
    ("第十三場 yachi 頭兩局連贏，之後六局 pinglamb 贏五局，3 比 5",
     "match 13: yachi won the first two rounds, then pinglamb won five of six, 3-5"),
    ("第十四場 yachi 頭四局連贏，5 比 2",
     "match 14: yachi won the first four rounds and the match 5-2"),
    ("第十五場 yachi 4 比 3 領先，尾兩局連失，4 比 5",
     "match 15: yachi led 4-3, then lost the last two rounds, 4-5"),
    ("第十六場 yachi 4 比 2 領先，尾三局連失，4 比 5",
     "match 16: yachi led 4-2, then lost the last three rounds, 4-5"),
    ("第十七場 yachi 5 比 1",
     "match 17: yachi won 5-1"),
    ("第十八場 yachi 輸第二局之後連贏四局，5 比 1",
     "match 18: yachi lost the second round, then won four straight, 5-1"),
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


def app_below_pct(mi, pct):
    """pinglamb's attack per piece over match `mi` is more than `pct` percent BELOW yachi's."""
    return lt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1), window(Y, "pieces", mi, mi + 1))),
              mul(lit(100 - pct), mul(window(Y, "garbage_attack", mi, mi + 1), window(P, "pieces", mi, mi + 1))))


def gap_lower(a, b):
    """pinglamb's per-match APP advantage (a ratio) is strictly smaller in match `a` than in `b`.

    (aP_a/pP_a)/(aY_a/pY_a) < (aP_b/pP_b)/(aY_b/pY_b), cross-multiplied.
    """
    def w(pl, f, mi):
        return window(pl, f, mi, mi + 1)
    return lt(mul(mul(w(P, "garbage_attack", a), w(Y, "pieces", a)),
                  mul(w(Y, "garbage_attack", b), w(P, "pieces", b))),
              mul(mul(w(P, "garbage_attack", b), w(Y, "pieces", b)),
                  mul(w(Y, "garbage_attack", a), w(P, "pieces", a))))


def winner(mi):
    return Y if mi in YACHI_MATCHES else P


def other(pl):
    return P if pl == Y else Y


def rounds_over(pl, mis):
    """`pl`'s round wins summed over the listed matches, as per-match `alive` windows."""
    terms = [window(pl, "alive", mi, mi + 1) for mi in mis]
    acc = terms[0]
    for t in terms[1:]:
        acc = add(acc, t)
    return acc


PINGLAMB_MATCHES = tuple(mi for mi in range(MATCHES) if mi not in YACHI_MATCHES)


CLAIMS = [
    {
        "id": "C001",
        "category": "score",
        "canto": "十八場 match pinglamb 贏 11 場：yachi 攞第二到第五、第十四、第十七同第十八場，"
                 "其餘十一場都係 pinglamb",
        "english_gloss": "pinglamb won eleven of the eighteen matches; yachi won matches 2 to 5, "
                         "14, 17 and 18",
        "spec": conj(*[match_winner(mi, winner(mi)) for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 10.20%，"
                 "輸嗰啲局高 14.64%——差距喺輸局，贏局兩個人貼得埋啲",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 10.20 percent "
                         "above yachi's, and in the rounds each lost 14.64 percent above",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 1020),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1464),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 20.07%，pinglamb 高 15.43%，今次闊啲嗰個係 yachi",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 20.07 percent and pinglamb by 15.43 "
                         "percent, yachi the wider",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 2007),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1543),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 10.73%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 10.73 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 1073),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 1038 粒方塊，總攻擊仍然少過 pinglamb 138 條，"
                 "即係 pinglamb 總攻擊嘅 1.77%",
        "english_gloss": "yachi placed 1038 more pieces than pinglamb and still landed 138 fewer "
                         "lines of attack, 1.77 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(1038)),
            eq(sub(atk(P), atk(Y)), lit(138)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(177), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(178), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 26 局頂到上天花板收場：yachi 10 局，pinglamb 16 局",
        "english_gloss": "twenty-six rounds ended in a topout: ten yachi's, sixteen pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(10)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(16)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.608 下，pinglamb 3.581 下，"
                 "yachi 高 pinglamb 0.76%",
        "english_gloss": "keypresses per piece are close: yachi 3.608 and pinglamb 3.581, "
                         "yachi 0.76 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3608),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3581),
            gap_x100(sum_round(Y, "inputs"), pieces(Y), sum_round(P, "inputs"), pieces(P), 76),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 1038 粒方塊盈餘，即係多過 pinglamb 8.76%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 8.76 個百分點，填唔晒 C004 個 10.73% 窿",
        "english_gloss": "yachi's piece count is 8.76 percent above pinglamb's, short of the "
                         "10.73 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10876), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10877), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 65 比 65，打和。分四段睇：第一場 2 比 5；第二到第五場 yachi 連贏四場，"
                 "局數 20 比 6；第六到第十三場 pinglamb 連贏八場，局數 20 比 40；"
                 "第十四到第十八場 yachi 贏三場，局數 23 比 14",
        "english_gloss": "the rounds finished level at 65 to 65; match 1 went 2-5, matches 2-5 "
                         "20-6, matches 6-13 20-40 and matches 14-18 23-14",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 65),
            rounds_won_in(P, 0, MATCHES, 65),
            rounds_won_in(Y, *OPEN, 2), rounds_won_in(P, *OPEN, 5),
            rounds_won_in(Y, *YRUN, 20), rounds_won_in(P, *YRUN, 6),
            rounds_won_in(Y, *PRUN, 20), rounds_won_in(P, *PRUN, 40),
            rounds_won_in(Y, *CLOSE, 23), rounds_won_in(P, *CLOSE, 14),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C029",
        "category": "style",
        "canto": "十八場入面十四場係 pinglamb 每粒方塊嘅攻擊高，yachi 高嘅得四場——"
                 "第三、第四、第十七同第十八場，四場都係 yachi 贏；第三場 pinglamb 低過 yachi "
                 "超過 8%，第十六場高過超過 30%。第七場 pinglamb 贏，佢嗰場高出嘅比例"
                 "細過 yachi 贏嘅第十四場",
        "english_gloss": "pinglamb's attack per piece is the higher in fourteen of the eighteen "
                         "matches and yachi's in four, matches 3, 4, 17 and 18, all yachi wins; "
                         "in match 3 pinglamb's is over 8 percent below yachi's and in match 16 "
                         "over 30 percent above; pinglamb's advantage in match 7, which he won, "
                         "is smaller than in match 14, which yachi won",
        "spec": conj(*[app_leads(mi, Y if mi in YACHI_APP else P) for mi in range(MATCHES)],
                     *[match_winner(mi, Y) for mi in YACHI_APP],
                     app_below_pct(2, 8), app_gt_pct(15, 30),
                     match_winner(6, P), match_winner(13, Y), gap_lower(6, 13)),
    },
    {
        "id": "C030",
        "category": "style",
        "canto": "逐場計總攻擊，打得多嗰個十八場贏十七場。唯一例外係第五場："
                 "pinglamb 總攻擊多啲，但係 yachi 5 比 3 贏",
        "english_gloss": "in seventeen of the eighteen matches the player who landed more attack "
                         "won; the exception is match 5, which yachi won with less attack",
        "spec": conj(*[conj(match_winner(mi, winner(mi)),
                            attack_leads(mi, other(winner(mi)) if mi in VOLUME_EXCEPTIONS
                                         else winner(mi)))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C031",
        "category": "score",
        "canto": "局數打和、場數輸 7 比 11，係因為 yachi 贏嗰七場局數 35 比 10，"
                 "輸嗰十一場局數 30 比 55——贏就贏得闊，輸就輸得窄",
        "english_gloss": "the rounds are level and the matches 7-11 because yachi's seven match "
                         "wins went 35-10 on rounds and his eleven match losses 30-55",
        "spec": conj(
            *[match_winner(mi, winner(mi)) for mi in range(MATCHES)],
            eq(rounds_over(Y, YACHI_MATCHES), lit(35)),
            eq(rounds_over(P, YACHI_MATCHES), lit(10)),
            eq(rounds_over(Y, PINGLAMB_MATCHES), lit(30)),
            eq(rounds_over(P, PINGLAMB_MATCHES), lit(55)),
        ),
    },
]
