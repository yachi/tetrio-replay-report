"""Hand-written claims for 2026-11-25 — what a generator cannot say about this night.

**Five matches and 62 rounds, yachi 3-2 in matches and LEVEL on rounds, 31-31** [C001][C010] —
yachi's first series win since 2026-08-01. The twenty-seventh session in date order and in
arrival. **Every match was played to SEVEN**, as on 11-23 and 11-24.

**Three of the five went to the thirteenth round** (m1, m4, m5 [C011][C014][C015]); yachi won m1
and m5 from 5-6 down, and lost m4 6-7 after leading 5-4.

**C010: the rounds are level over m1-m3 (18-18) and over m4-m5 (13-13).**

**C002 is the regime split: pinglamb's attack per piece is the higher in both** — +2.74% in the
rounds each won, +8.60% in the rounds each lost. **C003**: yachi +18.46%, pinglamb +12.06%.

**C004 / C005 / C009 are the volume route, and it MORE than covered the gap.** pinglamb's attack
per piece is 6.36% above yachi's; yachi threw 469 more pieces, 7.51% more, and finished 44 lines
of attack AHEAD, 1.08% of pinglamb's total — the third night after 10-09 and 10-20.

**C016: pinglamb's attack per piece is the higher in all five matches**, yachi's three wins
included. **C017: the attack TOTAL decided all five.** **C018: yachi cleared 137 MORE lines.**

**NO C007 IS MINTED.** yachi's wins sit at +1.13% (m5), +7.16% (m3) and +9.05% (m1); pinglamb's
m2 (+6.59%) and m4 (+6.84%) sit inside that band, so the ordering interleaves (1 in 10 by chance).
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, score, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 5
# The windows C010 pins, as [lo, hi) match positions: m1-m3 and m4-m5, both level.
FIRST, LAST = (0, 3), (3, 5)


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def gap_x100(na, da, nb, db, v):
    """(na/da) / (nb/db) is exactly (100 + v/100)% to the hundredth, FLOORED — i.e.
    `(10000+v)·nb·da <= 10000·na·db < (10001+v)·nb·da`."""
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
    """How many of matches [lo_m, hi_m)'s rounds `pl` won, as a window sum over `alive`
    (the survivor of a first-to-death round is its winner)."""
    return eq(window(pl, "alive", lo_m, hi_m), lit(n))


def window_rate_lt(a, b):
    """yachi's round-win RATE over window `a` is below his rate over window `b`, the
    denominators read out of the data as both players' `alive` sums."""
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


def match_seq(mi, winners):
    """Pin a whole match's round order — the only way to state a lead later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PYYPPYPPYYPYY",   # m1   7-6  <- 3-5 and 5-6 down, won the last two rounds
    "PYYPYPPYPPP",     # m2   4-7  <- 4-4, lost the last three rounds
    "YYYPPYPPYPYY",    # m3   7-5  <- 3-0 up, caught at 4-4
    "PPYPYYYPYPPYP",   # m4   6-7  <- 5-4 up, lost the thirteenth round
    "PPYYYPPYYPPYY",   # m5   7-6  <- 0-2 and 5-6 down, won the last two rounds
]

SCORES = [(7, 6), (4, 7), (7, 5), (6, 7), (7, 6)]   # (yachi, pinglamb)
WINNERS = [Y, P, Y, P, Y]

MATCH_CANTO = [
    ("第一場 yachi 3 比 5、5 比 6 落後，最後兩局連贏，7 比 6",
     "match 1: yachi trailed 3-5 and 5-6 and won the last two rounds, 7-6"),
    ("第二場 4 比 4 之後 pinglamb 連贏三局，4 比 7",
     "match 2: level at 4-4, pinglamb won the last three rounds; yachi lost 4-7"),
    ("第三場 yachi 開頭 3 比 0，俾人追到 4 比 4，7 比 5 贏",
     "match 3: yachi led 3-0, was caught at 4-4 and won 7-5"),
    ("第四場 yachi 5 比 4 領先，打到第十三局輸咗，6 比 7",
     "match 4: yachi led 5-4 and lost the thirteenth round, 6-7"),
    ("第五場 yachi 0 比 2、5 比 6 落後，最後兩局連贏，7 比 6",
     "match 5: yachi trailed 0-2 and 5-6 and won the last two rounds, 7-6"),
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
        "canto": "五場 match 全部打到先贏七局：yachi 贏第一、三、五場，pinglamb 贏第二、四場；"
                 "比數係 7:6、4:7、7:5、6:7、7:6",
        "english_gloss": "all five matches were first to seven; yachi won matches 1, 3 and 5 and "
                         "pinglamb matches 2 and 4; the scores were 7-6, 4-7, 7-5, 6-7 and 7-6",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]),
                            eq(score(mi, Y), lit(SCORES[mi][0])),
                            eq(score(mi, P), lit(SCORES[mi][1])))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，兩邊都係 pinglamb 每粒方塊嘅攻擊高：贏嗰啲局高 2.74%，"
                 "輸嗰啲局高 8.60%",
        "english_gloss": "pinglamb's attack per piece is the higher in both regimes: 2.74 percent "
                         "above yachi's in the rounds each won and 8.60 percent in the rounds each lost",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 274),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 860),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 18.46%，pinglamb 高 12.06%",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 18.46 percent and pinglamb by 12.06 percent",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1846),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1206),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 6.36%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 6.36 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 636),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 469 粒方塊，總攻擊反而多過 pinglamb 44 條，"
                 "即係 pinglamb 總攻擊嘅 1.08%",
        "english_gloss": "yachi placed 469 more pieces than pinglamb and landed 44 more lines of "
                         "attack, 1.08 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(469)),
            eq(sub(atk(Y), atk(P)), lit(44)),
            ge_(mul(lit(10000), sub(atk(Y), atk(P))), mul(lit(108), atk(P))),
            lt(mul(lit(10000), sub(atk(Y), atk(P))), mul(lit(109), atk(P))),
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
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.579 下，pinglamb 3.581 下",
        "english_gloss": "keypresses per piece are close: yachi 3.579 and pinglamb 3.581",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3579),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3581),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 469 粒方塊盈餘，即係多過 pinglamb 7.51%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多填返 7.51 個百分點，大過 C004 個 6.36% 窿超過 1 個百分點",
        "english_gloss": "yachi's piece count is 7.51 percent above pinglamb's, more than 1 point "
                         "above the 6.36 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10751), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10752), pieces(P))),
            gt(sub(mul(lit(10000), pieces(Y)), mul(lit(10000), pieces(P))),
               mul(lit(737), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 31 比 31 打和。頭三場 match 局數 18 比 18，最後兩場 13 比 13，"
                 "兩段都係打和",
        "english_gloss": "the rounds finished level, 31 to 31; matches 1-3 went 18-18 and "
                         "matches 4-5 went 13-13",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 31),
            rounds_won_in(P, 0, MATCHES, 31),
            rounds_won_in(Y, *FIRST, 18), rounds_won_in(P, *FIRST, 18),
            rounds_won_in(Y, *LAST, 13), rounds_won_in(P, *LAST, 13),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C016",
        "category": "style",
        "canto": "逐場計每粒方塊嘅攻擊，五場全部都係 pinglamb 高，yachi 贏嗰三場都係",
        "english_gloss": "pinglamb's attack per piece is the higher in all five matches, "
                         "yachi's three wins included",
        "spec": conj(*[app_leads(mi, P) for mi in range(MATCHES)]),
    },
    {
        "id": "C017",
        "category": "style",
        "canto": "逐場計總攻擊，五場全部都係打得多嗰個贏",
        "english_gloss": "in all five matches the player who landed more attack won",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]), attack_leads(mi, WINNERS[mi]))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C018",
        "category": "style",
        "canto": "yachi 全晚清咗 3741 行，多過 pinglamb 嘅 3604 行 137 行",
        "english_gloss": "yachi cleared 137 more lines than pinglamb, 3741 to 3604",
        "spec": conj(eq(sum_round(Y, "lines"), lit(3741)), eq(sum_round(P, "lines"), lit(3604))),
    },
]
