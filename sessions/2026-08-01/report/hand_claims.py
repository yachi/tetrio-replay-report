"""Hand-written claims for 2026-08-01 — what a generator cannot say about this night.

The generated ledger (G001-G072) covers the scores, the session records and the
per-player rate splits. What it has no family for is the *shape* of this session, and
this one has a shape no earlier session had: the seven matches alternate winners
perfectly — yachi took the odd ones, pinglamb the even ones — so the series was 3-3
going into the last match and the night was decided by which side of the alternation
it fell on.

Underneath that, the two players finished statistically indistinguishable in
aggregate: 3394 against 3426 lines of attack, 1087345 against 1087921 in-game points.
What separates them is not level but **route**. yachi got his attack out of volume
(326 more pieces, faster in all seven matches) and pinglamb out of efficiency (a
higher attack-per-piece in all seven). Both totals land in the same place.

So the claims here are of three kinds:

  * the alternation and the moments inside it, pinned as `round_seq` runs — a count
    of round wins cannot say who led when, and every match here was decided by a run.
    C008-C014 cover **all seven** matches, one each, so no card can describe a lead
    or a comeback that no lemma pins: this session's prose leans on run structure
    far more than the earlier ones did, and picking only the interesting matches
    would leave exactly the uninteresting ones unchecked
  * the two routes, as **per-match** windows (`sum_round_range` over one match) so
    "in all seven" is proved match by match rather than asserted from the session sum
  * the near-tie, bounded rather than merely stated: the attack gap is under 1% of
    pinglamb's total, the score gap under a thousandth of yachi's

Every rate is cross-multiplied into an integer inequality — the denominators are
different piece counts, so nothing here compares raw sums.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, gt, lit, lt,
                                  match_winner, mul, round_seq, sub, sum_round,
                                  sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 7


def atk(pl, mi=None):
    return sum_round(pl, "garbage_attack") if mi is None \
        else sum_round_range(pl, "garbage_attack", mi, mi + 1)


def pieces(pl, mi=None):
    return sum_round(pl, "pieces") if mi is None \
        else sum_round_range(pl, "pieces", mi, mi + 1)


def rate_gt(na, da, nb, db):
    """na/da > nb/db, as integers — the denominators are piece counts that differ."""
    return gt(mul(na, db), mul(nb, da))


def won(pl, f):
    return sum_round_where(pl, f, c_winner(pl))


def lost(pl, f):
    """The rounds this player did not win — the opponent's `winner` cond, same rounds."""
    other = P if pl == Y else Y
    return sum_round_where(pl, f, c_winner(other))


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who led when,
    which is the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


CLAIMS = [
    {
        "id": "C001",
        "category": "score",
        "canto": "成晚七場梅花間竹：yachi 攞單數場，pinglamb 攞雙數場，一場都冇亂過，最後 4 比 3",
        "english_gloss": "the seven matches alternated winners: yachi took 1, 3, 5, 7 and pinglamb 2, 4, 6",
        "spec": conj(*[match_winner(i, Y if i % 2 == 0 else P)
                       for i in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "七場入面每一場，pinglamb 每粒方塊打出嘅攻擊都高過 yachi — 七場七次，冇一場例外",
        "english_gloss": "pinglamb's attack per piece exceeded yachi's in each of the seven matches",
        "spec": conj(*[rate_gt(atk(P, i), pieces(P, i), atk(Y, i), pieces(Y, i))
                       for i in range(MATCHES)]),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "埋單 yachi 多疊咗 326 粒方塊，但打出嘅攻擊反而仲少過 pinglamb 32 條",
        "english_gloss": "yachi placed 326 more pieces than pinglamb yet landed 32 less attack",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(326)),
            eq(sub(atk(P), atk(Y)), lit(32)),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "換句話講，pinglamb 每粒方塊嘅攻擊高過 yachi 超過 7%，但唔夠 8%",
        "english_gloss": "pinglamb's attack per piece is between 7% and 8% above yachi's",
        "spec": conj(
            gt(mul(lit(100), mul(atk(P), pieces(Y))), mul(lit(107), mul(atk(Y), pieces(P)))),
            lt(mul(lit(100), mul(atk(P), pieces(Y))), mul(lit(108), mul(atk(Y), pieces(P)))),
        ),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "兩條路殊途同歸：總攻擊爭 32 條，唔夠 pinglamb 總攻擊嘅百分之一；遊戲分數爭 576 分，唔夠 yachi 總分嘅千分之一",
        "english_gloss": "the two totals are near-tied: the attack gap is under 1% of pinglamb's and the score gap under 0.1% of yachi's",
        "spec": conj(
            lt(mul(lit(100), sub(atk(P), atk(Y))), atk(P)),
            eq(sub(sum_round(P, "score"), sum_round(Y, "score")), lit(576)),
            lt(mul(lit(1000), sub(sum_round(P, "score"), sum_round(Y, "score"))),
               sum_round(Y, "score")),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "贏嘅局同輸嘅局都一樣：pinglamb 贏嗰啲局每粒方塊嘅攻擊高過 yachi 贏嗰啲局，佢輸嗰啲局又高過 yachi 輸嗰啲局",
        "english_gloss": "pinglamb's attack per piece is above yachi's in the rounds each won and in the rounds each lost",
        "spec": conj(
            rate_gt(won(P, "garbage_attack"), won(P, "pieces"),
                    won(Y, "garbage_attack"), won(Y, "pieces")),
            rate_gt(lost(P, "garbage_attack"), lost(P, "pieces"),
                    lost(Y, "garbage_attack"), lost(Y, "pieces")),
        ),
    },
    {
        "id": "C007",
        "category": "style",
        "canto": "全晚 8 局頂到上天花板收場，其中 6 局係 yachi，pinglamb 得 2 局",
        "english_gloss": "of the 8 rounds that ended in a topout, 6 were yachi's and 2 pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(6)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(2)),
        ),
    },
    {
        "id": "C008",
        "category": "moment",
        "canto": "第一場 yachi 一度 2 比 3 落後，跟住連贏三局收火 5 比 3",
        "english_gloss": "match 1: yachi trailed 2-3, then won the last three rounds straight",
        "spec": match_seq(0, [P, Y, Y, P, P, Y, Y, Y]),
    },
    {
        "id": "C009",
        "category": "moment",
        "canto": "第三場一模一樣：又係 2 比 3 落後，又係連贏三局 5 比 3 埋單",
        "english_gloss": "match 3: yachi again trailed 2-3, then won the last three rounds straight",
        "spec": match_seq(2, [Y, P, P, Y, P, Y, Y, Y]),
    },
    {
        "id": "C010",
        "category": "moment",
        "canto": "第四場係全晚唯一打到決勝局：yachi 由 2 比 4 追成 4 比 4，最後一局俾人收咗",
        "english_gloss": "match 4: yachi came back from 2-4 to 4-4 and lost the deciding round",
        "spec": match_seq(3, [Y, P, P, Y, P, P, Y, Y, P]),
    },
    {
        "id": "C011",
        "category": "moment",
        "canto": "第六場最肉痛：yachi 得第三局贏過，1 比 5 交波",
        "english_gloss": "match 6: yachi won only the third round and lost 1-5",
        "spec": match_seq(5, [P, P, Y, P, P, P]),
    },
    {
        "id": "C012",
        "category": "moment",
        "canto": "決勝第七場 yachi 開波連贏三局，一路冇畀人追返，5 比 2 攞埋成晚",
        "english_gloss": "match 7, the decider: yachi won the first three rounds and closed it 5-2",
        "spec": match_seq(6, [Y, Y, Y, P, Y, P, Y]),
    },
    {
        "id": "C013",
        "category": "moment",
        "canto": "第二場調轉頭：pinglamb 開波連贏三局，yachi 追成 3 比 3，最後兩局又俾人收晒",
        "english_gloss": "match 2: pinglamb won the first three rounds, yachi levelled at 3-3, pinglamb took the last two",
        "spec": match_seq(1, [P, P, P, Y, Y, Y, P, P]),
    },
    {
        "id": "C014",
        "category": "moment",
        "canto": "第五場 2 比 2 之後 yachi 連贏最後三局，5 比 2 收工",
        "english_gloss": "match 5: level at 2-2, yachi then won the last three rounds straight",
        "spec": match_seq(4, [Y, Y, P, P, Y, Y, Y]),
    },
]
