"""Hand-written claims for 2026-11-26 — what a generator cannot say about this night.

**Seven matches and 75 rounds, pinglamb 5-2 in matches and 44-31 in rounds** [C001][C010].
The twenty-eighth session in date order and in arrival. **Every match was played to SEVEN**,
the fourth night running, after 11-23, 11-24 and 11-25. C001 pins all seven scores, and no
generated family assumes the target. None of the scores is 7-6, so no match reached 6-6.

**C010 is the night's shape.** Matches 1-4 went 13-28 to pinglamb — he won all four — and
matches 5-7 went 18-16 to yachi, who won two of those three. The match margin is the opening
sweep; yachi's round-win rate is the higher over the last three.

**C002 is the regime split: pinglamb's attack per piece is the higher in both** — +8.34% in
the rounds each won, +6.36% in the rounds each lost. **C003 is each player against himself**:
yachi +17.79%, pinglamb +19.98%.

**C004 / C005 / C009 are the volume route, and it did not cover the gap.** pinglamb's attack
per piece is 10.37% above yachi's; yachi threw 534 more pieces, 7.00% more, and finished 152
lines of attack short, 3.04% of pinglamb's total. **C020: he cleared 65 MORE lines** (4554
to 4489).

**C006 is the death tally, 6 against 7.** **C008 pins keypresses per piece**, yachi 3.604
against pinglamb 3.616.

**C018: pinglamb's attack per piece is the higher in all seven matches**, yachi's two wins
included; the smallest gap is m5's, under 4%, and the largest m6's, over 18%. **C019: the
attack total decided five of the seven**; m1 pinglamb won with 5 lines less, and m7 yachi
won with 18 lines less.

**NO C007 IS MINTED.** yachi's two wins are m5 and m7. m5 is the smallest gap and m7 is not
the next — m2, m1 and m4 sit between them — so the ordering interleaves (two wins among
seven, 1 in 21 by chance).
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, score, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 7
# The windows C010 pins, as [lo, hi) match positions: m1-m4 (the sweep) and m5-m7.
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


def app_gt_pct(mi, pct):
    """pinglamb's attack per piece over match `mi` is more than `pct` percent above yachi's."""
    return gt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1), window(Y, "pieces", mi, mi + 1))),
              mul(lit(100 + pct), mul(window(Y, "garbage_attack", mi, mi + 1), window(P, "pieces", mi, mi + 1))))


def app_lt_pct(mi, pct):
    """pinglamb's attack per piece over match `mi` is less than `pct` percent above yachi's."""
    return lt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1), window(Y, "pieces", mi, mi + 1))),
              mul(lit(100 + pct), mul(window(Y, "garbage_attack", mi, mi + 1), window(P, "pieces", mi, mi + 1))))


def match_seq(mi, winners):
    """Pin a whole match's round order — the only way to state a lead later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PYYPPYYPPPYP",   # m1   5-7  <- led 4-3, level 4-4
    "PPPYYPPYPP",     # m2   3-7  <- 0-3 down
    "PPYPPYPPYP",     # m3   3-7  <- never led
    "YPPPPYPPP",      # m4   2-7  <- won the opener
    "PPYYYYPPYPYY",   # m5   7-5  <- 0-2, four in a row, level 5-5
    "PYPYPYPPPYP",    # m6   4-7  <- level 3-3, then three straight
    "YPPPYYYPYYY",    # m7   7-4  <- trailed 1-3, won the last three
]

SCORES = [(5, 7), (3, 7), (3, 7), (2, 7), (7, 5), (4, 7), (7, 4)]   # (yachi, pinglamb)
WINNERS = [P, P, P, P, Y, P, Y]

MATCH_CANTO = [
    ("第一場 yachi 4 比 3 領先，打和 4 比 4，5 比 7 輸",
     "match 1: yachi led 4-3, the match was level at 4-4, and he lost 5-7"),
    ("第二場開頭三局全輸，0 比 3，最後 3 比 7",
     "match 2: yachi lost the first three rounds, 0-3, and lost the match 3-7"),
    ("第三場 yachi 全程冇領先過，3 比 7 輸",
     "match 3: yachi never led and lost 3-7"),
    ("第四場 yachi 贏咗第一局，之後 2 比 7 輸",
     "match 4: yachi won the opening round and lost the match 2-7"),
    ("第五場 yachi 0 比 2 落後，連贏四局去到 4 比 2，打到 5 比 5，最後兩局贏，7 比 5",
     "match 5: yachi trailed 0-2, won four in a row to lead 4-2, was level at 5-5 "
     "and won the last two rounds, 7-5"),
    ("第六場 3 比 3 之後 pinglamb 連贏三局，yachi 4 比 7 輸",
     "match 6: level at 3-3, pinglamb won the next three rounds, and yachi lost 4-7"),
    ("第七場 yachi 1 比 3 落後，最後三局連贏，7 比 4",
     "match 7: yachi trailed 1-3 and won the last three rounds, 7-4"),
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
        "canto": "七場 match 全部打到先贏七局：pinglamb 贏第一到第四場同第六場，yachi 贏第五、七場；"
                 "比數係 5:7、3:7、3:7、2:7、7:5、4:7、7:4",
        "english_gloss": "all seven matches were first to seven; pinglamb won matches 1, 2, 3, 4 "
                         "and 6 and yachi matches 5 and 7; the scores were 5-7, 3-7, 3-7, 2-7, "
                         "7-5, 4-7 and 7-4",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]),
                            eq(score(mi, Y), lit(SCORES[mi][0])),
                            eq(score(mi, P), lit(SCORES[mi][1])))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，兩邊都係 pinglamb 每粒方塊嘅攻擊高：贏嗰啲局高 8.34%，"
                 "輸嗰啲局高 6.36%",
        "english_gloss": "pinglamb's attack per piece is the higher in both regimes: 8.34 percent "
                         "above yachi's in the rounds each won and 6.36 percent in the rounds each lost",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 834),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 636),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 17.79%，pinglamb 高 19.98%",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 17.79 percent and pinglamb by 19.98 percent",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1779),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1998),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 10.37%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 10.37 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 1037),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 534 粒方塊，總攻擊照樣少過 pinglamb 152 條，"
                 "即係 pinglamb 總攻擊嘅 3.04%",
        "english_gloss": "yachi placed 534 more pieces than pinglamb and still landed 152 fewer "
                         "lines of attack, 3.04 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(534)),
            eq(sub(atk(P), atk(Y)), lit(152)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(304), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(305), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 13 局頂到上天花板收場：yachi 6 局，pinglamb 7 局",
        "english_gloss": "thirteen rounds ended in a topout: six yachi's, seven pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(6)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(7)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.604 下，pinglamb 3.616 下",
        "english_gloss": "keypresses per piece are close: yachi 3.604 and pinglamb 3.616",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3604),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3616),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 534 粒方塊盈餘，即係多過 pinglamb 7.00%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多填返 7.00 個百分點，C004 個 10.37% 窿仲差超過 3 個百分點",
        "english_gloss": "yachi's piece count is 7.00 percent above pinglamb's, more than 3 "
                         "points short of the 10.37 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10700), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10701), pieces(P))),
            lt(add(sub(mul(lit(10000), pieces(Y)), mul(lit(10000), pieces(P))),
                   mul(lit(300), pieces(P))),
               mul(lit(1037), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 31 比 44。頭四場 match pinglamb 全取，局數 13 比 28；"
                 "尾三場 yachi 贏兩場，局數 18 比 16——成晚嘅場數差距喺頭四場，"
                 "尾三場 yachi 嘅贏局率高過頭四場",
        "english_gloss": "the rounds finished 31 to 44; matches 1-4, all pinglamb's, went 13-28, "
                         "and matches 5-7 went 18-16, so yachi's round-win rate was higher over "
                         "the last three matches than over the first four",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 31),
            rounds_won_in(P, 0, MATCHES, 44),
            rounds_won_in(Y, *FIRST, 13), rounds_won_in(P, *FIRST, 28),
            rounds_won_in(Y, *LAST, 18), rounds_won_in(P, *LAST, 16),
            window_rate_lt(FIRST, LAST),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C018",
        "category": "style",
        "canto": "逐場計每粒方塊嘅攻擊，七場全部都係 pinglamb 高，yachi 贏嗰兩場都係；"
                 "差得最少嗰場係第五場，唔夠 4%，最多嗰場係第六場，超過 18%",
        "english_gloss": "pinglamb's attack per piece is the higher in all seven matches, "
                         "yachi's two wins included; the smallest gap is match 5's, under 4 "
                         "percent, and the largest match 6's, over 18 percent",
        "spec": conj(*[app_leads(mi, P) for mi in range(MATCHES)],
                     app_lt_pct(4, 4), app_gt_pct(5, 18)),
    },
    {
        "id": "C019",
        "category": "style",
        "canto": "逐場計總攻擊，七場有五場係打得多嗰個贏。兩場例外：第一場 yachi 總攻擊多 5 條但係輸，"
                 "第七場 pinglamb 總攻擊多 18 條但係 yachi 贏",
        "english_gloss": "in five of the seven matches the player who landed more attack won; "
                         "match 1 pinglamb won with 5 lines of attack fewer, and match 7 yachi "
                         "won with 18 lines fewer",
        "spec": conj(*[conj(match_winner(mi, WINNERS[mi]), attack_leads(mi, WINNERS[mi]))
                       for mi in (1, 2, 3, 4, 5)],
                     match_winner(0, P),
                     eq(sub(window(Y, "garbage_attack", 0, 1),
                            window(P, "garbage_attack", 0, 1)), lit(5)),
                     match_winner(6, Y),
                     eq(sub(window(P, "garbage_attack", 6, 7),
                            window(Y, "garbage_attack", 6, 7)), lit(18))),
    },
    {
        "id": "C020",
        "category": "style",
        "canto": "yachi 全晚清咗 4554 行，多過 pinglamb 嘅 4489 行 65 行",
        "english_gloss": "yachi cleared 65 more lines than pinglamb, 4554 to 4489",
        "spec": conj(eq(sum_round(Y, "lines"), lit(4554)), eq(sum_round(P, "lines"), lit(4489))),
    },
]
