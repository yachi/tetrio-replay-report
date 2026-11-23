"""Hand-written claims for 2026-11-23 — what a generator cannot say about this night.

**Seven matches and 82 rounds, pinglamb 5-2 in matches and 46-36 in rounds** [C001][C010]. The
twenty-fifth session in date order and in arrival. **Every match was played to SEVEN** — the
corpus's first first-to-7 night (11-19's m4 was first-to-15, every other match first-to-5); C001
pins all seven scores, and no generated family assumes the target.

**C010: after four matches the night was level, 2-2 in matches and 26-25 to yachi in rounds**;
pinglamb took all three of m5-m7, 21-10, and that is the whole margin.

**C002 is the regime split: pinglamb's attack per piece is the higher in both** — +6.88% in the
rounds each won, +5.05% in the rounds each lost. **C003 is each player against himself**: yachi
+19.45%, pinglamb +21.54%.

**C004 / C005 / C009 are the volume route.** pinglamb's attack per piece is 8.45% above yachi's;
yachi threw 193 more pieces, 2.46% more, and finished 278 lines of attack short, 5.52% of
pinglamb's total. **C020: he cleared 101 MORE lines** (4427 to 4326).

**C006 is the death tally, 8 against 9.** **C008 pins keypresses per piece**, yachi 3.580 against
pinglamb 3.577.

**C018: pinglamb's attack per piece is the higher in all seven matches**, yachi's two wins
included. **C019: the attack TOTAL decided six of the seven**; the exception is m3, which yachi
won 7-6 with 824 lines against 843.

**NO C007 IS MINTED.** yachi's two wins (m2 +6.37%, m3 +7.12%) are not the two smallest gaps —
pinglamb's m4 is, at +1.80% — so the per-match ordering interleaves (1 in 21 by chance).
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, score, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 7
# The windows C010 pins, as [lo, hi) match positions: m1-m4 (level), and m5-m7.
FIRST, LAST = (0, 4), (4, 7)


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
    "YPPYPYPYPYPYP",   # m1   6-7  <- level at 6-6, lost the thirteenth round
    "PYYPPYPYYYPY",    # m2   7-5
    "YYPPYPYYYPPPY",   # m3   7-6  <- 6-3 up, 6-6, won the thirteenth round
    "PYYPPYYPPPYYP",   # m4   6-7  <- level at 6-6, lost the thirteenth round
    "PPPYYPPPP",       # m5   2-7
    "PPYPPYPYYYYPP",   # m6   6-7  <- 6-5 up, lost the last two rounds
    "PPPPYPYPP",       # m7   2-7  <- 0-4 down
]

SCORES = [(6, 7), (7, 5), (7, 6), (6, 7), (2, 7), (6, 7), (2, 7)]   # (yachi, pinglamb)
WINNERS = [P, Y, Y, P, P, P, P]

MATCH_CANTO = [
    ("第一場 6 比 6 打到第十三局，輸咗，6 比 7",
     "match 1: level at 6-6, yachi lost the thirteenth round, 6-7"),
    ("第二場 yachi 7 比 5 贏",
     "match 2: yachi won 7-5"),
    ("第三場 yachi 6 比 3 領先，畀人追到 6 比 6，第十三局贏返，7 比 6",
     "match 3: yachi led 6-3, was caught at 6-6 and won the thirteenth round, 7-6"),
    ("第四場又係 6 比 6 打到第十三局，又輸，6 比 7",
     "match 4: level at 6-6 again, yachi lost the thirteenth round, 6-7"),
    ("第五場 2 比 7 輸",
     "match 5: yachi lost 2-7"),
    ("第六場 yachi 6 比 5 領先，最後兩局都輸，6 比 7",
     "match 6: yachi led 6-5 and lost the last two rounds, 6-7"),
    ("第七場 pinglamb 頭四局連贏，2 比 7 輸",
     "match 7: pinglamb won the first four rounds; yachi lost 2-7"),
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
        "canto": "七場 match 全部打到先贏七局：pinglamb 贏五場，yachi 贏第二、三場；"
                 "比數係 6:7、7:5、7:6、6:7、2:7、6:7、2:7",
        "english_gloss": "all seven matches were first to seven; pinglamb won five and yachi "
                         "matches 2 and 3; the scores were 6-7, 7-5, 7-6, 6-7, 2-7, 6-7 and 2-7",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]),
                            eq(score(mi, Y), lit(SCORES[mi][0])),
                            eq(score(mi, P), lit(SCORES[mi][1])))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，兩邊都係 pinglamb 每粒方塊嘅攻擊高：贏嗰啲局高 6.88%，"
                 "輸嗰啲局高 5.05%",
        "english_gloss": "pinglamb's attack per piece is the higher in both regimes: 6.88 percent "
                         "above yachi's in the rounds each won and 5.05 percent in the rounds each lost",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 688),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 505),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 19.45%，pinglamb 高 21.54%",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 19.45 percent and pinglamb by 21.54 percent",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1945),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 2154),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 8.45%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 8.45 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 845),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 193 粒方塊，總攻擊照樣少過 pinglamb 278 條，"
                 "即係 pinglamb 總攻擊嘅 5.52%",
        "english_gloss": "yachi placed 193 more pieces than pinglamb and still landed 278 fewer "
                         "lines of attack, 5.52 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(193)),
            eq(sub(atk(P), atk(Y)), lit(278)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(552), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(553), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 17 局頂到上天花板收場：yachi 8 局，pinglamb 9 局",
        "english_gloss": "seventeen rounds ended in a topout: eight yachi's, nine pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(8)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(9)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人幾乎一樣：yachi 3.580 下，pinglamb 3.577 下",
        "english_gloss": "keypresses per piece are all but equal: yachi 3.580 and pinglamb 3.577",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3580),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3577),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 193 粒方塊盈餘，即係多過 pinglamb 2.46%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多填返 2.46 個百分點，C004 個 8.45% 窿仲差超過 5 個百分點",
        "english_gloss": "yachi's piece count is 2.46 percent above pinglamb's, more than 5 "
                         "points short of the 8.45 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10246), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10247), pieces(P))),
            lt(add(sub(mul(lit(10000), pieces(Y)), mul(lit(10000), pieces(P))),
                   mul(lit(500), pieces(P))),
               mul(lit(845), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 36 比 46。頭四場 match 2 比 2、局數 26 比 25，yachi 仲多一局；"
                 "最後三場 pinglamb 全取，局數 10 比 21——成晚嘅差距全部喺尾三場",
        "english_gloss": "the rounds finished 36 to 46; over matches 1-4 yachi led the rounds "
                         "26-25, and matches 5-7 went 10-21, so his round-win rate was higher over "
                         "the first four matches than over the last three",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 36),
            rounds_won_in(P, 0, MATCHES, 46),
            rounds_won_in(Y, *FIRST, 26), rounds_won_in(P, *FIRST, 25),
            rounds_won_in(Y, *LAST, 10), rounds_won_in(P, *LAST, 21),
            window_rate_lt(LAST, FIRST),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C018",
        "category": "style",
        "canto": "逐場計每粒方塊嘅攻擊，七場都係 pinglamb 高，yachi 贏嗰兩場都唔例外",
        "english_gloss": "pinglamb's attack per piece is the higher in all seven matches, "
                         "including the two yachi won",
        "spec": conj(*[app_leads(mi, P) for mi in range(MATCHES)]),
    },
    {
        "id": "C019",
        "category": "style",
        "canto": "逐場計總攻擊，七場有六場係打得多嗰個贏；例外係第三場，yachi 攻擊少 19 條都贏咗",
        "english_gloss": "in six of the seven matches the player who landed more attack won; the "
                         "exception is match 3, which yachi won with 19 lines of attack fewer",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]), attack_leads(mi, WINNERS[mi]))
                       for mi in range(MATCHES) if mi != 2],
                     match_winner(2, Y),
                     eq(sub(window(P, "garbage_attack", 2, 3), window(Y, "garbage_attack", 2, 3)),
                        lit(19))),
    },
    {
        "id": "C020",
        "category": "style",
        "canto": "yachi 全晚清咗 4427 行，多過 pinglamb 嘅 4326 行 101 行",
        "english_gloss": "yachi cleared 101 more lines than pinglamb, 4427 to 4326",
        "spec": conj(eq(sum_round(Y, "lines"), lit(4427)), eq(sum_round(P, "lines"), lit(4326))),
    },
]
