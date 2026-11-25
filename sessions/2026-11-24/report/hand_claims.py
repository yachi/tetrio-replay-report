"""Hand-written claims for 2026-11-24 — what a generator cannot say about this night.

**Six matches and 72 rounds, pinglamb 5-1 in matches and 39-33 in rounds** [C001][C010]. The
twenty-sixth session in date order and in arrival. **Every match was played to SEVEN**, as on
11-23; C001 pins all six scores, and no generated family assumes the target.

**Four of the six went to the thirteenth round and yachi lost all four** [C011][C012][C013][C016]:
m1 from 2-6 down to 6-6, m2 from 6-5 up, m3 from 5-0 and 6-4 up, m6 at 6-6.

**C010: after four matches the rounds were LEVEL, 25-25** (matches 1-3 to pinglamb); m5-m6 went
8-14, and that is the whole round margin.

**C002 is the regime split: pinglamb's attack per piece is the higher in both** — +6.11% in the
rounds each won, +1.80% in the rounds each lost. **C003 is each player against himself**: yachi
+16.77%, pinglamb +21.71%.

**C004 / C005 / C009 are the volume route.** pinglamb's attack per piece is 6.58% above yachi's;
yachi threw 285 more pieces, 3.98% more, and finished 111 lines of attack short, 2.43% of
pinglamb's total. **C019: he cleared 114 MORE lines** (4186 to 4072).

**C006 is the death tally, 7 against 6.** **C008 pins keypresses per piece**, yachi 3.547 against
pinglamb 3.598.

**C017: pinglamb's attack per piece is the higher in five of the six matches; m4, yachi's one win,
is the exception.** **C018: the attack TOTAL decided five of the six**; the exception is m3, which
pinglamb won 7-6 with 811 lines against 826.

**NO C007 IS MINTED.** yachi's one win (m4) IS the smallest gap — yachi leads it — but one win
among six falls at the bottom by chance one time in six, which is 09-11's degenerate case.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, score, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 6
# The windows C010 pins, as [lo, hi) match positions: m1-m4 (level), and m5-m6.
FIRST, LAST = (0, 4), (4, 6)


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
    "PPPYPYPPYYYYP",   # m1   6-7  <- 2-6 down, 6-6, lost the thirteenth round
    "YPPYPPYPYYYPP",   # m2   6-7  <- 6-5 up, lost the last two rounds
    "YYYYYPPPPYPPP",   # m3   6-7  <- 5-0 and 6-4 up, lost the last three rounds
    "YYPPYPYYPYY",     # m4   7-4
    "PPPPYPPYP",       # m5   2-7  <- 0-4 down
    "YYPPYYPPPYPYP",   # m6   6-7  <- 6-6, lost the thirteenth round
]

SCORES = [(6, 7), (6, 7), (6, 7), (7, 4), (2, 7), (6, 7)]   # (yachi, pinglamb)
WINNERS = [P, P, P, Y, P, P]

MATCH_CANTO = [
    ("第一場 yachi 2 比 6 落後，連贏四局追到 6 比 6，第十三局輸，6 比 7",
     "match 1: yachi trailed 2-6, won four straight to 6-6 and lost the thirteenth round, 6-7"),
    ("第二場 yachi 3 比 5 落後反超到 6 比 5，最後兩局都輸，6 比 7",
     "match 2: yachi came back from 3-5 to lead 6-5 and lost the last two rounds, 6-7"),
    ("第三場 yachi 開頭連贏五局 5 比 0，之後 6 比 4 領先，最後三局都輸，6 比 7",
     "match 3: yachi won the first five rounds, led 6-4, and lost the last three, 6-7"),
    ("第四場 yachi 7 比 4 贏",
     "match 4: yachi won 7-4"),
    ("第五場 pinglamb 頭四局連贏，2 比 7 輸",
     "match 5: pinglamb won the first four rounds; yachi lost 2-7"),
    ("第六場 6 比 6 打到第十三局，輸咗，6 比 7",
     "match 6: level at 6-6, yachi lost the thirteenth round, 6-7"),
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
        "canto": "六場 match 全部打到先贏七局：pinglamb 贏五場，yachi 贏第四場；"
                 "比數係 6:7、6:7、6:7、7:4、2:7、6:7",
        "english_gloss": "all six matches were first to seven; pinglamb won five and yachi "
                         "match 4; the scores were 6-7, 6-7, 6-7, 7-4, 2-7 and 6-7",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]),
                            eq(score(mi, Y), lit(SCORES[mi][0])),
                            eq(score(mi, P), lit(SCORES[mi][1])))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，兩邊都係 pinglamb 每粒方塊嘅攻擊高：贏嗰啲局高 6.11%，"
                 "輸嗰啲局高 1.80%",
        "english_gloss": "pinglamb's attack per piece is the higher in both regimes: 6.11 percent "
                         "above yachi's in the rounds each won and 1.80 percent in the rounds each lost",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 611),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 180),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 16.77%，pinglamb 高 21.71%",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 16.77 percent and pinglamb by 21.71 percent",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1677),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 2171),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 6.58%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 6.58 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 658),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 285 粒方塊，總攻擊照樣少過 pinglamb 111 條，"
                 "即係 pinglamb 總攻擊嘅 2.43%",
        "english_gloss": "yachi placed 285 more pieces than pinglamb and still landed 111 fewer "
                         "lines of attack, 2.43 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(285)),
            eq(sub(atk(P), atk(Y)), lit(111)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(243), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(244), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 13 局頂到上天花板收場：yachi 7 局，pinglamb 6 局",
        "english_gloss": "thirteen rounds ended in a topout: seven yachi's, six pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(7)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(6)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.547 下，pinglamb 3.598 下",
        "english_gloss": "keypresses per piece are close: yachi 3.547 and pinglamb 3.598",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3547),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3598),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 285 粒方塊盈餘，即係多過 pinglamb 3.98%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多填返 3.98 個百分點，C004 個 6.58% 窿仲差超過 2 個百分點",
        "english_gloss": "yachi's piece count is 3.98 percent above pinglamb's, more than 2 "
                         "points short of the 6.58 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10398), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10399), pieces(P))),
            lt(add(sub(mul(lit(10000), pieces(Y)), mul(lit(10000), pieces(P))),
                   mul(lit(200), pieces(P))),
               mul(lit(658), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 33 比 39。頭四場 match 局數 25 比 25 打和；"
                 "最後兩場 pinglamb 全取，局數 8 比 14——成晚嘅局數差距全部喺尾兩場",
        "english_gloss": "the rounds finished 33 to 39; over matches 1-4 the rounds were level "
                         "25-25, and matches 5-6 went 8-14, so yachi's round-win rate was higher "
                         "over the first four matches than over the last two",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 33),
            rounds_won_in(P, 0, MATCHES, 39),
            rounds_won_in(Y, *FIRST, 25), rounds_won_in(P, *FIRST, 25),
            rounds_won_in(Y, *LAST, 8), rounds_won_in(P, *LAST, 14),
            window_rate_lt(LAST, FIRST),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C017",
        "category": "style",
        "canto": "逐場計每粒方塊嘅攻擊，六場有五場係 pinglamb 高；例外係 yachi 贏嗰第四場",
        "english_gloss": "pinglamb's attack per piece is the higher in five of the six matches; "
                         "the exception is match 4, the one yachi won",
        "spec": conj(*[app_leads(mi, P) for mi in range(MATCHES) if mi != 3], app_leads(3, Y)),
    },
    {
        "id": "C018",
        "category": "style",
        "canto": "逐場計總攻擊，六場有五場係打得多嗰個贏；例外係第三場，pinglamb 攻擊少 15 條都贏咗",
        "english_gloss": "in five of the six matches the player who landed more attack won; the "
                         "exception is match 3, which pinglamb won with 15 lines of attack fewer",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]), attack_leads(mi, WINNERS[mi]))
                       for mi in range(MATCHES) if mi != 2],
                     match_winner(2, P),
                     eq(sub(window(Y, "garbage_attack", 2, 3), window(P, "garbage_attack", 2, 3)),
                        lit(15))),
    },
    {
        "id": "C019",
        "category": "style",
        "canto": "yachi 全晚清咗 4186 行，多過 pinglamb 嘅 4072 行 114 行",
        "english_gloss": "yachi cleared 114 more lines than pinglamb, 4186 to 4072",
        "spec": conj(eq(sum_round(Y, "lines"), lit(4186)), eq(sum_round(P, "lines"), lit(4072))),
    },
]
