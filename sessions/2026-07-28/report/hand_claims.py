"""Hand-written claims for 2026-07-28 — what a generator cannot say about this night.

The generated ledger (G001-G071) already covers the scores, the session records and
the per-player rate splits. What it has no family for is the *shape* of this session:
yachi took the first two matches and then lost six straight, and the interesting
question is what changed at that seam.

So every claim here is a **windowed** one — matches 1-2 against matches 3-8 — which is
why `spec.sum_round_range` and `spec.count_rounds_range` exist. The windows hold
different numbers of rounds (15 against 49), so nothing here compares raw sums: every
rate is cross-multiplied into an integer inequality, the same way the generated
per-piece claims are.

The finding these pin down: it was not a collapse. pinglamb was already the better
downstacker in the first two matches; what changed after them is that his attack per
piece went up while yachi's went down, and the two lines crossed.
"""
from pipeline.claims.spec import (c_winner, conj, count_rounds_range, eq, gt, lit, lt,
                                  match_winner, mul, round_seq, sub, sum_round,
                                  sum_round_range)

Y, P = "yachi", "pinglamb"

EARLY = (0, 2)   # matches 1-2, the two yachi won
LATE = (2, 8)    # matches 3-8, the six pinglamb won


def atk(pl, w):
    return sum_round_range(pl, "garbage_attack", *w)


def pieces(pl, w):
    return sum_round_range(pl, "pieces", *w)


def cleared(pl, w):
    return sum_round_range(pl, "garbage_cleared", *w)


def rate_gt(na, da, nb, db):
    """na/da > nb/db, as integers — the denominators are round counts that differ."""
    return gt(mul(na, db), mul(nb, da))


def rate_lt(na, da, nb, db):
    return lt(mul(na, db), mul(nb, da))


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who won when,
    which is the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


CLAIMS = [
    {
        "id": "C001",
        "category": "score",
        "canto": "成晚嘅形狀：yachi 贏晒頭兩場，跟住 pinglamb 一口氣連贏埋落嚟六場",
        "english_gloss": "yachi won the first two matches, pinglamb won all six after",
        "spec": conj(
            match_winner(0, "yachi"), match_winner(1, "yachi"),
            *[match_winner(i, "pinglamb") for i in range(2, 8)],
        ),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "頭兩場，兩邊每粒方塊打出嘅攻擊（APP）叮噹馬頭，yachi 僅僅高過一線",
        "english_gloss": "in matches 1-2 yachi's attack per piece was higher than pinglamb's",
        "spec": rate_gt(atk("yachi", EARLY), pieces("yachi", EARLY),
                        atk("pinglamb", EARLY), pieces("pinglamb", EARLY)),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "由第三場開始，pinglamb 嘅 APP 反超前，六場都係佢每粒方塊打得多過 yachi",
        "english_gloss": "from match 3 on pinglamb's attack per piece was higher than yachi's",
        "spec": rate_gt(atk("pinglamb", LATE), pieces("pinglamb", LATE),
                        atk("yachi", LATE), pieces("yachi", LATE)),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "pinglamb 自己同自己比：後六場嘅 APP 高過佢頭兩場嘅 APP，即係佢真係打好咗",
        "english_gloss": "pinglamb's own attack per piece rose from matches 1-2 to matches 3-8",
        "spec": rate_gt(atk("pinglamb", LATE), pieces("pinglamb", LATE),
                        atk("pinglamb", EARLY), pieces("pinglamb", EARLY)),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 自己同自己比就啱啱相反：後六場嘅 APP 跌咗，低過頭兩場",
        "english_gloss": "yachi's own attack per piece fell from matches 1-2 to matches 3-8",
        "spec": rate_lt(atk("yachi", LATE), pieces("yachi", LATE),
                        atk("yachi", EARLY), pieces("yachi", EARLY)),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "清垃圾嘅功夫（DS）唔係後尾先出現：頭兩場 pinglamb 每粒方塊清走嘅垃圾已經多過 yachi",
        "english_gloss": "in matches 1-2 pinglamb already cleared more garbage per piece than yachi",
        "spec": rate_gt(cleared("pinglamb", EARLY), pieces("pinglamb", EARLY),
                        cleared("yachi", EARLY), pieces("yachi", EARLY)),
    },
    {
        "id": "C007",
        "category": "style",
        "canto": "後六場條距離仲要拉闊：pinglamb 每粒方塊清走嘅垃圾照樣多過 yachi",
        "english_gloss": "in matches 3-8 pinglamb still cleared more garbage per piece than yachi",
        "spec": rate_gt(cleared("pinglamb", LATE), pieces("pinglamb", LATE),
                        cleared("yachi", LATE), pieces("yachi", LATE)),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "成晚計埋：yachi 多疊咗 378 粒方塊，但係打出嘅攻擊反而仲少過 pinglamb 15 條",
        "english_gloss": "yachi placed 378 more pieces than pinglamb yet landed 15 less attack",
        "spec": conj(
            eq(sub(sum_round("yachi", "pieces"), sum_round("pinglamb", "pieces")), lit(378)),
            eq(sub(sum_round("pinglamb", "garbage_attack"),
                   sum_round("yachi", "garbage_attack")), lit(15)),
        ),
    },
    {
        "id": "C009",
        "category": "score",
        "canto": "分開兩段睇局數：頭兩場 yachi 10 比 5 壓住，後六場調轉頭變成 pinglamb 30 比 19",
        "english_gloss": "round wins by phase: 10-5 to yachi in matches 1-2, 30-19 to pinglamb in matches 3-8",
        "spec": conj(
            eq(count_rounds_range(c_winner("yachi"), *EARLY), lit(10)),
            eq(count_rounds_range(c_winner("pinglamb"), *EARLY), lit(5)),
            eq(count_rounds_range(c_winner("pinglamb"), *LATE), lit(30)),
            eq(count_rounds_range(c_winner("yachi"), *LATE), lit(19)),
        ),
    },
    {
        "id": "C010",
        "category": "moment",
        "canto": "第一場 pinglamb 先開兩局，之後 yachi 一啖氣連追五局收火",
        "english_gloss": "match 1: pinglamb took the first two rounds, yachi then won five straight",
        "spec": match_seq(0, [P, P, Y, Y, Y, Y, Y]),
    },
    {
        "id": "C011",
        "category": "moment",
        "canto": "第三場係轉勢位：yachi 一度 3 比 1 領先，跟住連輸四局俾人反轉豬肚",
        "english_gloss": "match 3: yachi led 3-1, then pinglamb won the last four rounds straight",
        "spec": match_seq(2, [P, Y, Y, Y, P, P, P, P]),
    },
    {
        "id": "C012",
        "category": "moment",
        "canto": "第七場最肉痛：yachi 一度 4 比 1 拋離，最後四局全部俾 pinglamb 收晒，5 比 4 輸咗",
        "english_gloss": "match 7: yachi led 4-1, then pinglamb won the last four rounds straight",
        "spec": match_seq(6, [Y, Y, Y, P, Y, P, P, P, P]),
    },
]
