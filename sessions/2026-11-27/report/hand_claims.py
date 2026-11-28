"""Hand-written claims for 2026-11-27 — what a generator cannot say about this night.

**Five matches and 61 rounds, yachi 4-1 in matches and 34-27 in rounds** [C001][C010] — his
largest series win in the corpus, and his second in a row after 11-25. The twenty-eighth session
in date order and in arrival. **Every match was played to SEVEN**, the fourth night running.

**Three of the five went to the thirteenth round** (m1, m2, m3 [C011][C012][C013]); yachi lost m1
6-7 from 6-6, won m2 from 5-6 down and m3 from 1-3 down. m5 he won 7-3 from 1-3 down, the last
six rounds in a row [C015].

**C010: the rounds are level over m1-m2 (13-13) and yachi's over m3-m5 (21-14)**, so the whole
round margin is the last three matches.

**C002 is the regime split: pinglamb's attack per piece is the higher in both** — +3.86% in the
rounds each won, +2.92% in the rounds each lost. **C003**: yachi +17.73%, pinglamb +18.81%.

**C004 / C005 / C009 are the volume route, and it MORE than covered the gap.** pinglamb's attack
per piece is 2.15% above yachi's, the narrowest session gap the corpus holds; yachi threw 160 more
pieces, 2.60% more, and finished 17 lines of attack AHEAD, 0.44% of pinglamb's total.

**C016: the APP leader per match is yachi in m1-m2 and pinglamb in m3-m5**, so yachi won three
matches with the lower APP. **C017: the attack TOTAL decided two of the five** (m2, m5): yachi lost
m1 with more attack and won m3 and m4 with less. **C018: yachi cleared 100 MORE lines.**

**NO C007 IS MINTED.** pinglamb's per-match APP gap is −1.49% in his one win (m1), and −1.12%,
+1.30%, +4.80% and +8.71% in yachi's four; the loss is the smallest gap, the wrong way round for a
separation, so the ordering does not separate (1 in 5 by chance either way).
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, score, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 5
# The windows C010 pins, as [lo, hi) match positions: m1-m2 level, m3-m5 yachi's.
FIRST, LAST = (0, 2), (2, 5)


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
    "PPYPYYPYPPYYP",   # m1   6-7  <- 6-6, lost the thirteenth round
    "PYYYPYPYPPPYY",   # m2   7-6  <- 5-3 up, 5-6 down, won the last two rounds
    "PYPPYPYYPYYPY",   # m3   7-6  <- 1-3 down, won the thirteenth round
    "YYPYPYPPYYPY",    # m4   7-5  <- 4-2 up, caught at 4-4
    "PYPPYYYYYY",      # m5   7-3  <- 1-3 down, won the last six rounds
]

SCORES = [(6, 7), (7, 6), (7, 6), (7, 5), (7, 3)]   # (yachi, pinglamb)
WINNERS = [P, Y, Y, Y, Y]
APP_LEADER = [Y, Y, P, P, P]
ATK_LEADER = [Y, Y, P, P, Y]

MATCH_CANTO = [
    ("第一場打到 6 比 6，第十三局 pinglamb 贏，yachi 6 比 7 輸",
     "match 1: level at 6-6, pinglamb won the thirteenth round; yachi lost 6-7"),
    ("第二場 yachi 5 比 3 領先，俾人反超 5 比 6，最後兩局連贏，7 比 6",
     "match 2: yachi led 5-3, trailed 5-6 and won the last two rounds, 7-6"),
    ("第三場 yachi 1 比 3 落後，追到 6 比 6，第十三局贏，7 比 6",
     "match 3: yachi trailed 1-3, levelled at 6-6 and won the thirteenth round, 7-6"),
    ("第四場 yachi 4 比 2 領先，俾人追到 4 比 4，7 比 5 贏",
     "match 4: yachi led 4-2, was caught at 4-4 and won 7-5"),
    ("第五場 yachi 1 比 3 落後，之後連贏六局，7 比 3",
     "match 5: yachi trailed 1-3 and won the last six rounds, 7-3"),
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
        "canto": "五場 match 全部打到先贏七局：pinglamb 贏第一場，yachi 贏第二至第五場；"
                 "比數係 6:7、7:6、7:6、7:5、7:3",
        "english_gloss": "all five matches were first to seven; pinglamb won match 1 and yachi "
                         "matches 2 to 5; the scores were 6-7, 7-6, 7-6, 7-5 and 7-3",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]),
                            eq(score(mi, Y), lit(SCORES[mi][0])),
                            eq(score(mi, P), lit(SCORES[mi][1])))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，兩邊都係 pinglamb 每粒方塊嘅攻擊高：贏嗰啲局高 3.86%，"
                 "輸嗰啲局高 2.92%",
        "english_gloss": "pinglamb's attack per piece is the higher in both regimes: 3.86 percent "
                         "above yachi's in the rounds each won and 2.92 percent in the rounds each lost",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 386),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 292),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 17.73%，pinglamb 高 18.81%",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 17.73 percent and pinglamb by 18.81 percent",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1773),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1881),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 2.15%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 2.15 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 215),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 160 粒方塊，總攻擊反而多過 pinglamb 17 條，"
                 "即係 pinglamb 總攻擊嘅 0.44%",
        "english_gloss": "yachi placed 160 more pieces than pinglamb and landed 17 more lines of "
                         "attack, 0.44 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(160)),
            eq(sub(atk(Y), atk(P)), lit(17)),
            ge_(mul(lit(10000), sub(atk(Y), atk(P))), mul(lit(44), atk(P))),
            lt(mul(lit(10000), sub(atk(Y), atk(P))), mul(lit(45), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 11 局頂到上天花板收場：yachi 6 局，pinglamb 5 局",
        "english_gloss": "eleven rounds ended in a topout: six yachi's, five pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(6)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(5)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.635 下，pinglamb 3.610 下",
        "english_gloss": "keypresses per piece are close: yachi 3.635 and pinglamb 3.610",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3635),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3610),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 160 粒方塊盈餘，即係多過 pinglamb 2.60%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多填返 2.60 個百分點，大過 C004 個 2.15% 窿超過 0.4 個百分點",
        "english_gloss": "yachi's piece count is 2.60 percent above pinglamb's, more than 0.4 "
                         "points above the 2.15 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10260), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10261), pieces(P))),
            gt(sub(mul(lit(10000), pieces(Y)), mul(lit(10000), pieces(P))),
               mul(lit(255), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 yachi 34 比 27。頭兩場 match 局數 13 比 13 打和，"
                 "最後三場 yachi 21 比 14",
        "english_gloss": "yachi won the rounds 34 to 27; matches 1-2 went 13-13 and matches 3-5 "
                         "went 21-14 to yachi",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 34),
            rounds_won_in(P, 0, MATCHES, 27),
            rounds_won_in(Y, *FIRST, 13), rounds_won_in(P, *FIRST, 13),
            rounds_won_in(Y, *LAST, 21), rounds_won_in(P, *LAST, 14),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C016",
        "category": "style",
        "canto": "逐場計每粒方塊嘅攻擊，第一、二場 yachi 高，第三至第五場 pinglamb 高——"
                 "即係 yachi 贏嗰四場有三場每粒攻擊低過對手",
        "english_gloss": "per match, yachi's attack per piece is the higher in matches 1 and 2 and "
                         "pinglamb's in matches 3 to 5, so three of yachi's four wins came with "
                         "the lower attack per piece",
        "spec": conj(*[app_leads(mi, APP_LEADER[mi]) for mi in range(MATCHES)]),
    },
    {
        "id": "C017",
        "category": "style",
        "canto": "逐場計總攻擊，只有第二、五場係打得多嗰個贏：第一場 yachi 打多咗都輸，"
                 "第三、四場 yachi 打少咗都贏",
        "english_gloss": "the player with more attack won only matches 2 and 5: yachi lost match 1 "
                         "with more attack and won matches 3 and 4 with less",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]), attack_leads(mi, ATK_LEADER[mi]))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C018",
        "category": "style",
        "canto": "yachi 全晚清咗 3532 行，多過 pinglamb 嘅 3432 行 100 行",
        "english_gloss": "yachi cleared 100 more lines than pinglamb, 3532 to 3432",
        "spec": conj(eq(sum_round(Y, "lines"), lit(3532)), eq(sum_round(P, "lines"), lit(3432))),
    },
]
