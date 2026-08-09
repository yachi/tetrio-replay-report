"""Hand-written claims for 2026-08-09 — what a generator cannot say about this night.

The generated ledger (G001-G076) has the scores, the session records and the per-player
rate splits. What it has no family for is this session's shape, and the shape is a
contradiction: **pinglamb swept 6-0 while winning only 30 of the 50 rounds**, and yachi
led at some point in five of the six matches without closing one.

Underneath that sits the finding, and it is a *regime* finding rather than a level one.
Split every round by who won it and pool attack over pieces:

    rounds won     yachi 1204/1787 = .6738    pinglamb 2154/3139 = .6862   → +1.8%
    rounds lost    yachi 1714/3345 = .5124    pinglamb 1035/1611 = .6425   → +25.4%

The ceiling is level and the floor is not. That is the opposite decomposition to
2026-08-01, where pinglamb led in both regimes by roughly the same margin and the
difference read as *style*; here the won-round gap has collapsed to under 2% while the
lost-round gap has blown out past 25%, so what separates them this night is what happens
in the rounds that go wrong. The rank test agrees and is not a variance artefact: over
the losing rounds P(yachi > pinglamb) = 0.138 (permutation p = 1e-5), over the winning
rounds 0.464 (p = 0.34) — indistinguishable. It also survives dropping the three
near-zero rounds (yachi m2r1/m2r7, pinglamb m6r4): the lost-round means become .491 and
.649, the medians .523 and .667.

So the claims here are of four kinds:

  * **the close** — C001 pins that pinglamb took the last round of all six matches,
    three of them 5-4 deciders. A count of round wins cannot say who took the last one,
    and this session's whole margin lives there
  * **the two regimes** — C002-C004, every rate cross-multiplied into an integer
    inequality because the denominators are different piece counts. C003 states the
    sharp end of it: yachi's *won*-round attack per piece is above pinglamb's
    *lost*-round attack per piece, so his good rounds are not the problem
  * **the route, and the gap closing under it** — C005 is the windowed pair
    (`sum_round_range` over matches 1-2 against matches 5-6). The efficiency gap fell
    from over a third to under 8% across the night and not one match changed hands,
    which is the counterweight to reading C002 as "just play better"
  * **the six matches, one each** — C007-C012 as `round_seq` runs, following the same
    rule as 2026-08-01: cover *all* of them, so no card can describe a lead or a
    collapse that no lemma pins. Every match here was decided by a run, and picking only
    the interesting ones would leave the uninteresting ones unchecked

C006 is the death tally, and it is worth stating because it inverts: all four topouts are
pinglamb's, yachi has none. On 2026-08-01 six of the eight were yachi's.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, gt, lit, lt,
                                  mul, round_seq, round_winner, sub, sum_round,
                                  sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 6

# (match index, index of that match's last round) — the six matches run 8, 7, 9, 8, 9, 9.
LAST_ROUND = [(0, 7), (1, 6), (2, 8), (3, 7), (4, 8), (5, 8)]


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def rate_gt(na, da, nb, db):
    """na/da > nb/db, as integers — the denominators are piece counts that differ."""
    return gt(mul(na, db), mul(nb, da))


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters here: a one-sided "the gap is over 25%" would survive any
    further collapse of yachi's losing rounds, and the report's point is the size of the
    gap, not merely its direction.
    """
    lhs = mul(lit(100), mul(na, db))
    rhs = mul(nb, da)
    return conj(gt(lhs, mul(lit(lo), rhs)), lt(lhs, mul(lit(hi), rhs)))


def won(pl, f):
    return sum_round_where(pl, f, c_winner(pl))


def lost(pl, f):
    """The rounds this player did not win — the opponent's `winner` cond, same rounds."""
    other = P if pl == Y else Y
    return sum_round_where(pl, f, c_winner(other))


def window(pl, f, lo, hi):
    return sum_round_range(pl, f, lo, hi)


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who led when,
    which is the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


CLAIMS = [
    {
        "id": "C001",
        "category": "score",
        "canto": "六場 match 嘅最後一局，全部 pinglamb 攞——包括三場打到 5 比 4 嘅決勝局",
        "english_gloss": "pinglamb won the final round of all six matches, three of them 5-4 deciders",
        "spec": conj(*[round_winner(mi, ri, P) for mi, ri in LAST_ROUND]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "贏嗰啲局，兩個人每粒方塊嘅攻擊幾乎打成平手，pinglamb 高過 yachi 唔夠 2%；"
                 "輸嗰啲局就爭超過 25%——天花板貼到實，地板差咁遠",
        "english_gloss": "in the rounds each won their attack per piece is within 2 percent; "
                         "in the rounds each lost pinglamb's is over 25 percent above yachi's",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 100, 102),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 125, 126),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "講到盡：yachi 贏嗰啲局每粒方塊嘅攻擊，仲要高過 pinglamb 輸嗰啲局——高出超過 4%，"
                 "即係話 yachi 打得好嗰陣唔係問題所在",
        "english_gloss": "yachi's attack per piece in the rounds he won is over 4 percent above "
                         "pinglamb's in the rounds pinglamb lost",
        "spec": pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                            lost(P, "garbage_attack"), lost(P, "pieces"), 104, 105),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "但埋單嗰陣，多落方塊呢條路今次冇買返個 gap：yachi 多疊咗 382 粒方塊，"
                 "打出嘅攻擊反而少 271 條，即係 pinglamb 總攻擊嘅 8% 以上",
        "english_gloss": "yachi placed 382 more pieces than pinglamb yet landed 271 less attack, "
                         "a gap of more than 8 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(382)),
            eq(sub(atk(P), atk(Y)), lit(271)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(8), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(9), atk(P))),
        ),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "個效率 gap 成晚一路收窄：頭兩場 pinglamb 每粒方塊嘅攻擊高過 yachi 超過三成半，"
                 "去到尾兩場唔夠 8%——但六場 match 一場都冇轉手",
        "english_gloss": "the attack-per-piece gap narrowed from over 34 percent in matches 1-2 "
                         "to under 8 percent in matches 5-6, and pinglamb won every match anyway",
        "spec": conj(
            pct_between(window(P, "garbage_attack", 0, 2), window(P, "pieces", 0, 2),
                        window(Y, "garbage_attack", 0, 2), window(Y, "pieces", 0, 2), 134, 136),
            pct_between(window(P, "garbage_attack", 4, 6), window(P, "pieces", 4, 6),
                        window(Y, "garbage_attack", 4, 6), window(Y, "pieces", 4, 6), 107, 108),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚淨係 4 局頂到上天花板收場，4 局都係 pinglamb 頂爆，yachi 一次都冇",
        "english_gloss": "all four rounds that ended in a topout were pinglamb's; yachi had none",
        "spec": conj(
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(4)),
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(0)),
        ),
    },
    {
        "id": "C007",
        "category": "moment",
        "canto": "第一場 yachi 開波連贏兩局，跟住俾人連追三局，最後 3 比 5",
        "english_gloss": "match 1: yachi led 2-0, pinglamb answered with three straight and took it 5-3",
        "spec": match_seq(0, [Y, Y, P, P, P, Y, P, P]),
    },
    {
        "id": "C008",
        "category": "moment",
        "canto": "第二場係全晚最一面倒嗰場：yachi 由頭到尾冇領先過一次，2 比 5 交波",
        "english_gloss": "match 2: yachi never led at any point and lost 2-5",
        "spec": match_seq(1, [P, P, Y, P, P, Y, P]),
    },
    {
        "id": "C009",
        "category": "moment",
        "canto": "第三場 yachi 又係 2 比 0 開頭，跟住俾人連贏四局，追返兩局拉成 4 比 4，決勝局俾人收咗",
        "english_gloss": "match 3: yachi led 2-0, conceded four straight, levelled at 4-4 and lost the decider",
        "spec": match_seq(2, [Y, Y, P, P, P, P, Y, Y, P]),
    },
    {
        "id": "C010",
        "category": "moment",
        "canto": "第四場 yachi 贏嘅三局係第一、第四、第七局，中間每次都俾人即刻收返，3 比 5",
        "english_gloss": "match 4: yachi won rounds 1, 4 and 7 and pinglamb answered each time, 5-3",
        "spec": match_seq(3, [Y, P, P, Y, P, P, Y, P]),
    },
    {
        "id": "C011",
        "category": "moment",
        "canto": "第五場 yachi 一度 4 比 3 領先，尾二同尾三局連輸，4 比 5",
        "english_gloss": "match 5: yachi led 4-3 and lost the last two rounds",
        "spec": match_seq(4, [Y, P, P, Y, Y, P, Y, P, P]),
    },
    {
        "id": "C012",
        "category": "moment",
        "canto": "第六場最肉痛：yachi 一度 4 比 2 領先，最後三局連輸，4 比 5 收工，成晚 6 比 0",
        "english_gloss": "match 6: yachi led 4-2 and lost the last three rounds straight, 4-5",
        "spec": match_seq(5, [P, Y, Y, Y, P, Y, P, P, P]),
    },
]
