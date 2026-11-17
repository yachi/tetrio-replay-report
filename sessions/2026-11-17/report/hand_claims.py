"""Hand-written claims for 2026-11-17 — what a generator cannot say about this night.

**Three matches and 24 rounds, pinglamb 3-0 in matches and 15-9 in rounds** [C001][C010]. The
twenty-third session in date order and in arrival, and the corpus's smallest (10-20 held 4
matches and 30 rounds).

**C010: yachi took 2 of m1's 7 rounds and 7 of the last two matches' 17**, so his round-win rate
is higher over m2-m3. m1 opened with four straight pinglamb rounds; m2 went to a ninth round
from a 3-2 yachi lead.

**C002 is the regime split: pinglamb's attack per piece is the higher in both** — +6.94% in the
rounds each won, +3.75% in the rounds each lost. **C003 is each player against himself**: yachi
+13.50%, pinglamb +16.99%.

**C004 / C005 / C009 are the volume route.** pinglamb's attack per piece is 10.46% above yachi's;
yachi threw 71 more pieces, 3.08% more, and finished 97 lines of attack short, 6.68% of
pinglamb's total.

**C006 is the death tally, 2 against 1.** **C008 pins keypresses per piece**, pinglamb 1.10% above.

**C014: pinglamb's attack per piece is the higher in all three matches**, m1 by over 25%.
**C015: the attack TOTAL decided two of the three**, the exception m3, which pinglamb won 5-3
with 7 lines less.

**NO C007 IS MINTED.** yachi won no match, so an ordering by per-match APP gap "separates" the
match winners only because there is nothing to separate — 08-09's degenerate case, not a
reproduction of 08-19's. Ordered by pinglamb's advantage: m3 +2.26, m2 +12.16, m1 +25.72.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 3
# The windows C010 pins, as [lo, hi) match positions: m1 and m2-m3.
FIRST, LAST = (0, 1), (1, 3)


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


def match_seq(mi, winners):
    """Pin a whole match's round order — the only way to state a lead later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PPPPYYP",     # m1   2-5   <- 0-4 down
    "PPYYYPYPP",   # m2   4-5   <- led 3-2, lost the ninth round
    "PPYYPPYP",    # m3   3-5
]

# The match whose winner landed the LOWER attack total, 0-based (m3, pinglamb's).
VOLUME_EXCEPTIONS = (2,)

MATCH_CANTO = [
    ("第一場 pinglamb 頭四局連贏 4 比 0，5 比 2 收",
     "match 1: pinglamb won the first four rounds and the match 5-2"),
    ("第二場 yachi 0 比 2 落後追到 3 比 2 領先，之後 4 比 4，第九局輸，4 比 5",
     "match 2: yachi came from 0-2 down to lead 3-2, it went to 4-4, and he lost the ninth round, 4-5"),
    ("第三場 2 比 2 之後 pinglamb 連贏兩局，5 比 3 收",
     "match 3: from 2-2 pinglamb won two straight rounds and the match 5-3"),
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
        "canto": "三場 match 全部係 pinglamb 贏",
        "english_gloss": "pinglamb won all three matches",
        "spec": conj(*[match_winner(mi, P) for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，兩邊都係 pinglamb 每粒方塊嘅攻擊高：贏嗰啲局高 6.94%，"
                 "輸嗰啲局高 3.75%",
        "english_gloss": "pinglamb's attack per piece is the higher in both regimes: 6.94 percent "
                         "above yachi's in the rounds each won and 3.75 percent in the rounds each lost",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 694),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 375),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 13.50%，pinglamb 高 16.99%",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 13.50 percent and pinglamb by 16.99 percent",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1350),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1699),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 10.46%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 10.46 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 1046),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 71 粒方塊，總攻擊照樣少過 pinglamb 97 條，"
                 "即係 pinglamb 總攻擊嘅 6.68%",
        "english_gloss": "yachi placed 71 more pieces than pinglamb and still landed 97 fewer "
                         "lines of attack, 6.68 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(71)),
            eq(sub(atk(P), atk(Y)), lit(97)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(668), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(669), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚有 3 局頂到上天花板收場：yachi 2 局，pinglamb 1 局",
        "english_gloss": "three rounds ended in a topout: two yachi's, one pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(2)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(1)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.592 下，pinglamb 3.632 下，"
                 "pinglamb 高 yachi 1.10%",
        "english_gloss": "keypresses per piece are close: yachi 3.592 and pinglamb 3.632, "
                         "pinglamb 1.10 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3592),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3632),
            gap_x100(sum_round(P, "inputs"), pieces(P), sum_round(Y, "inputs"), pieces(Y), 110),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 71 粒方塊盈餘，即係多過 pinglamb 3.08%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多填返 3.08 個百分點，C004 個 10.46% 窿填唔到三分一",
        "english_gloss": "yachi's piece count is 3.08 percent above pinglamb's, under a third of "
                         "the 10.46 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10308), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10309), pieces(P))),
            lt(mul(lit(3), sub(mul(lit(10000), pieces(Y)), mul(lit(10000), pieces(P)))),
               mul(lit(1046), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 9 比 15。第一場局數 2 比 5；尾兩場 7 比 10——"
                 "yachi 尾兩場嘅贏局率高過第一場",
        "english_gloss": "the rounds finished 9 to 15; match 1 went 2-5 and matches 2-3 7-10, "
                         "so yachi's round-win rate was higher over the last two",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 9),
            rounds_won_in(P, 0, MATCHES, 15),
            rounds_won_in(Y, *FIRST, 2), rounds_won_in(P, *FIRST, 5),
            rounds_won_in(Y, *LAST, 7), rounds_won_in(P, *LAST, 10),
            window_rate_lt(FIRST, LAST),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C014",
        "category": "style",
        "canto": "三場都係 pinglamb 每粒方塊嘅攻擊高，第一場差得最多，超過 25%",
        "english_gloss": "pinglamb's attack per piece is the higher in all three matches, "
                         "match 1's gap over 25 percent",
        "spec": conj(*[app_leads(mi, P) for mi in range(MATCHES)], app_gt_pct(0, 25)),
    },
    {
        "id": "C015",
        "category": "style",
        "canto": "逐場計總攻擊，打得多嗰個三場贏兩場。例外係第三場：yachi 總攻擊多 7 條，"
                 "但係 3 比 5 輸",
        "english_gloss": "in two of the three matches the player who landed more attack won; "
                         "the exception is match 3, which pinglamb won with 7 lines less",
        "spec": conj(*[conj(match_winner(mi, P),
                            attack_leads(mi, Y if mi in VOLUME_EXCEPTIONS else P))
                       for mi in range(MATCHES)],
                     eq(sub(window(Y, "garbage_attack", 2, 3), window(P, "garbage_attack", 2, 3)),
                        lit(7))),
    },
]
