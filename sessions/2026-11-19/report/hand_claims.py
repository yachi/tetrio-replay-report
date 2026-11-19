"""Hand-written claims for 2026-11-19 — what a generator cannot say about this night.

**Four matches and 44 rounds, pinglamb 3-1 in matches and 26-18 in rounds** [C001][C010]. The
twenty-fourth session in date order and in arrival. **Its fourth match was played to FIFTEEN**,
15-6, where every earlier match in the corpus was first-to-5; nothing in a hand or generated
family assumes the target (`first_to_five` emits nothing on a mixed night), and C001 pins all
four scores.

**C010: yachi led the rounds 12-11 over the three first-to-5 matches, and the night's whole round
margin is m4**, which went 6-15 after pinglamb took its first five rounds [C014].

**C002 is the regime split: pinglamb's attack per piece is the higher in both** — +6.80% in the
rounds each won, +9.15% in the rounds each lost (leave-one-out: both under THRESHOLD; the won
gap's largest move is m4r6, rel 0.456). **C003 is each player against himself**: yachi +25.25%,
pinglamb +22.55%.

**C004 / C005 / C009 are the volume route.** pinglamb's attack per piece is 13.94% above yachi's;
yachi threw 334 more pieces, 8.78% more, and finished 115 lines of attack short, 4.52% of
pinglamb's total. **C017: he cleared 115 MORE lines** (2233 to 2118) — the volume route bought
lines and not attack, where 11-17's bought neither.

**C006 is the death tally, 4 against 4.** **C008 pins keypresses per piece**, pinglamb 1.17% above.

**C015: pinglamb's attack per piece is the higher in m1, m3 and m4, yachi's in m2**, the one
match yachi won. **C016: the attack TOTAL decided all four matches.**

**NO C007 IS MINTED.** yachi won one match of four and its gap is the smallest (m2 −10.13; then
m3 +11.78, m1 +17.70, m4 +19.16), so the ordering separates the match winners — but one win
among four falls at the bottom by chance one time in four, below 09-11's 1 in 7: the degenerate
case, not a reproduction.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, score, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 4
# The windows C010 pins, as [lo, hi) match positions: the three first-to-5 matches, and m4.
FIRST, LAST = (0, 3), (3, 4)


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
    "YPYPPYPP",               # m1   3-5   <- 3-3, then pinglamb's two
    "YYPYYY",                 # m2   5-1
    "YPPYPPYYP",              # m3   4-5   <- 2-4 down, 4-4, lost the ninth round
    "PPPPPYYPPPYPYPYPPPPYP",  # m4   6-15  <- first-to-15; 0-5 down
]

SCORES = [(3, 5), (5, 1), (4, 5), (6, 15)]   # (yachi, pinglamb)
WINNERS = [P, Y, P, P]

MATCH_CANTO = [
    ("第一場 3 比 3 之後 pinglamb 連贏兩局，3 比 5 輸",
     "match 1: from 3-3 pinglamb won the last two rounds; yachi lost 3-5"),
    ("第二場 yachi 頭兩局贏，輸一局之後連贏三局，5 比 1 贏",
     "match 2: yachi won the first two rounds, dropped one and won the next three, 5-1"),
    ("第三場 yachi 2 比 4 落後追到 4 比 4，第九局輸，4 比 5",
     "match 3: yachi came from 2-4 down to 4-4 and lost the ninth round, 4-5"),
    ("第四場打十五局先贏：pinglamb 頭五局連贏，之後 yachi 最近都仲差三局，6 比 15 輸",
     "match 4, first to fifteen: pinglamb won the first five rounds and yachi never got closer "
     "than three rounds behind after that; he lost 6-15"),
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
        "canto": "四場 match pinglamb 贏三場，yachi 贏第二場；比數係 3:5、5:1、4:5，"
                 "第四場打到十五局，6:15",
        "english_gloss": "pinglamb won three of the four matches and yachi match 2; the scores "
                         "were 3-5, 5-1, 4-5 and, in a match played to fifteen, 6-15",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]),
                            eq(score(mi, Y), lit(SCORES[mi][0])),
                            eq(score(mi, P), lit(SCORES[mi][1])))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，兩邊都係 pinglamb 每粒方塊嘅攻擊高：贏嗰啲局高 6.80%，"
                 "輸嗰啲局高 9.15%",
        "english_gloss": "pinglamb's attack per piece is the higher in both regimes: 6.80 percent "
                         "above yachi's in the rounds each won and 9.15 percent in the rounds each lost",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 680),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 915),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 25.25%，pinglamb 高 22.55%",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 25.25 percent and pinglamb by 22.55 percent",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 2525),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 2255),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 13.94%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 13.94 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 1394),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 334 粒方塊，總攻擊照樣少過 pinglamb 115 條，"
                 "即係 pinglamb 總攻擊嘅 4.52%",
        "english_gloss": "yachi placed 334 more pieces than pinglamb and still landed 115 fewer "
                         "lines of attack, 4.52 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(334)),
            eq(sub(atk(P), atk(Y)), lit(115)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(452), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(453), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 8 局頂到上天花板收場：yachi 4 局，pinglamb 4 局",
        "english_gloss": "eight rounds ended in a topout: four yachi's, four pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(4)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(4)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.562 下，pinglamb 3.604 下，"
                 "pinglamb 高 yachi 1.17%",
        "english_gloss": "keypresses per piece are close: yachi 3.562 and pinglamb 3.604, "
                         "pinglamb 1.17 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3562),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3604),
            gap_x100(sum_round(P, "inputs"), pieces(P), sum_round(Y, "inputs"), pieces(Y), 117),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 334 粒方塊盈餘，即係多過 pinglamb 8.78%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多填返 8.78 個百分點，C004 個 13.94% 窿仲差超過 5 個百分點",
        "english_gloss": "yachi's piece count is 8.78 percent above pinglamb's, more than 5 "
                         "points short of the 13.94 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10878), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10879), pieces(P))),
            lt(add(sub(mul(lit(10000), pieces(Y)), mul(lit(10000), pieces(P))),
                   mul(lit(500), pieces(P))),
               mul(lit(1394), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 18 比 26。頭三場（全部係先贏五局）局數 12 比 11，yachi 仲多一局；"
                 "第四場 6 比 15——成晚嘅局數差距全部喺第四場",
        "english_gloss": "the rounds finished 18 to 26; over the three first-to-5 matches yachi "
                         "led 12-11, and match 4 went 6-15, so his round-win rate was higher over "
                         "the first three matches than in the fourth",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 18),
            rounds_won_in(P, 0, MATCHES, 26),
            rounds_won_in(Y, *FIRST, 12), rounds_won_in(P, *FIRST, 11),
            rounds_won_in(Y, *LAST, 6), rounds_won_in(P, *LAST, 15),
            window_rate_lt(LAST, FIRST),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C015",
        "category": "style",
        "canto": "逐場計每粒方塊嘅攻擊：第一、三、四場係 pinglamb 高，第二場（yachi 贏嗰場）係 yachi 高",
        "english_gloss": "pinglamb's attack per piece is the higher in matches 1, 3 and 4, and "
                         "yachi's in match 2, the match he won",
        "spec": conj(*[app_leads(mi, WINNERS[mi]) for mi in range(MATCHES)]),
    },
    {
        "id": "C016",
        "category": "style",
        "canto": "逐場計總攻擊，四場都係打得多嗰個贏",
        "english_gloss": "in all four matches the player who landed more attack won",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]), attack_leads(mi, WINNERS[mi]))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C017",
        "category": "style",
        "canto": "yachi 全晚清咗 2233 行，多過 pinglamb 嘅 2118 行 115 行",
        "english_gloss": "yachi cleared 115 more lines than pinglamb, 2233 to 2118",
        "spec": conj(eq(sum_round(Y, "lines"), lit(2233)), eq(sum_round(P, "lines"), lit(2118))),
    },
]
