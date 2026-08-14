"""Hand-written claims for 2026-08-14 — what a generator cannot say about this night.

The generated ledger (G001-G084) has the scores, the session records, the per-player rate
splits (G071/G072) and the death count (G067). What it has no family for is the *comparison
between* those splits, and that comparison is this session's finding.

Split every round by who won it and pool attack over pieces:

    rounds won     yachi 2598/4307 = .6032    pinglamb 2665/3715 = .7174   → +18.9%
    rounds lost    yachi 2113/3754 = .5629    pinglamb 2252/3931 = .5729   →  +1.8%

The floors have met and the ceilings have not. That is the exact mirror of 2026-08-09,
where the won-round gap was under 2% and the lost-round gap over 25%; the same session-level
APP gap decomposes the opposite way two nights running, which is why the decomposition is
worth pinning as a claim rather than read off a session total.

Said within a player instead of across them, it is sharper still. The gap between a player's
own winning and losing rounds is +25.2% for pinglamb and only +7.2% for yachi (C003) — so the
regime separation that five previous sessions found in *both* players exists here in one. And
yachi's ceiling now sits nearer pinglamb's floor than pinglamb's ceiling: 5.3% above the one,
15.9% below the other (C004).

The claims are of five kinds:

  * **the three acts** — C001 pins all eleven match winners at once, because the night's
    shape is that pinglamb took matches 1-3 and 10-11 and every one of yachi's four wins
    falls between them. Eleven separate score claims (G004-G014) cannot state that shape.
  * **the two regimes** — C002-C004, every rate cross-multiplied into an integer inequality
    because the denominators are different piece counts.
  * **the route and its price** — C005 is the volume route's third run: 415 more pieces for
    206 less attack. C006 is what it cost, and it inverts 2026-08-09 exactly: 11 of the 13
    topouts are yachi's, where that night all four were pinglamb's and yachi had none.
  * **where the gap actually was** — C007 windows the night into its three acts with
    `sum_round_range`. The efficiency gap is over 17% across matches 1-3, under 7% across
    matches 4-9, and back over 11% for the last two — the middle window is the one yachi
    won four matches in.
  * **the eleven matches, one each** — C008-C018 as `round_seq` runs, the same rule
    2026-08-01 and 2026-08-09 follow: cover *all* of them, so no match card can describe a
    lead or a collapse that no lemma pins.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, gt, lit, lt,
                                  match_winner, mul, round_seq, sub, sum_round,
                                  sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 11


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided "the gap is over 18%" would survive any further
    collapse of yachi's winning rounds, and every figure this ledger prints is the SIZE of a
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


def window_gap(lo, hi, plo, phi):
    """pinglamb's attack per piece against yachi's, over matches [lo, hi)."""
    return pct_between(window(P, "garbage_attack", lo, hi), window(P, "pieces", lo, hi),
                       window(Y, "garbage_attack", lo, hi), window(Y, "pieces", lo, hi),
                       plo, phi)


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who led when,
    which is the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "YPYPYPPP",   # m1  3-5
    "PPPYPP",     # m2  1-5
    "PPPYPYP",    # m3  2-5
    "PYPYYYPPY",  # m4  5-4
    "PYYYPYPPP",  # m5  4-5
    "PPPYYYYY",   # m6  5-3
    "YYYPPPYPY",  # m7  5-4
    "PPPPP",      # m8  0-5
    "YYPYYPY",    # m9  5-2
    "YPYPPPYP",   # m10 3-5
    "PPYPYYPP",   # m11 3-5
]

MATCH_CANTO = [
    ("第一場拉鋸到第五局都仲係 3 比 2，跟住 pinglamb 連贏三局收工，3 比 5",
     "match 1: level at 3-2 after five rounds, then pinglamb took three straight for 5-3"),
    ("第二場最短，六局完事，yachi 淨係贏到第四局，1 比 5",
     "match 2: the shortest match — six rounds, yachi won only the fourth, 1-5"),
    ("第三場 yachi 開波連輸三局，追返兩局都止唔到血，2 比 5",
     "match 3: yachi lost the first three rounds and never levelled, 2-5"),
    ("第四場 yachi 落後 1 比 2 之後連贏三局反超，最後一局收咗個決勝波，5 比 4",
     "match 4: yachi trailed 1-2, won three straight and took the deciding final round 5-4"),
    ("第五場 yachi 一度 4 比 2 領先，最後三局連輸，4 比 5——全晚最肉痛嗰場",
     "match 5: yachi led 4-2 and lost the last three rounds straight, 4-5"),
    ("第六場 yachi 開頭連輸三局，跟住連贏五局翻盤，5 比 3",
     "match 6: yachi lost the first three rounds then won five straight to take it 5-3"),
    ("第七場 yachi 又係開波連贏三局，俾人追平之後最後一局收波，5 比 4",
     "match 7: yachi led 3-0, was pegged back and took the deciding final round 5-4"),
    ("第八場係全晚唯一一場白果：五局全部 pinglamb 攞，0 比 5",
     "match 8: the night's only sweep — pinglamb won all five rounds, 0-5"),
    ("第九場 yachi 打得最順，七局贏五局，5 比 2",
     "match 9: yachi's cleanest match — five of seven rounds, 5-2"),
    ("第十場 yachi 一度 2 比 1 領先，之後連輸三局，3 比 5",
     "match 10: yachi led 2-1 then lost three straight, 3-5"),
    ("第十一場係全晚最長嘅一場，yachi 追到 3 比 3，最後兩局又俾人收晒，3 比 5",
     "match 11: the night's longest match — yachi levelled at 3-3 and lost the last two, 3-5"),
]


def _seq_claims():
    out = []
    for mi, (run, (canto, gloss)) in enumerate(zip(RUNS, MATCH_CANTO)):
        out.append({
            "id": f"C{8 + mi:03d}",
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
        "canto": "成晚分三段：頭三場 pinglamb 食晒，尾兩場又係佢，yachi 贏嘅四場 match "
                 "全部夾喺中間第四至第九場入面",
        "english_gloss": "pinglamb won matches 1-3 and matches 10-11, and all four of yachi's "
                         "match wins fall between them, in matches 4 through 9",
        "spec": conj(
            match_winner(0, P), match_winner(1, P), match_winner(2, P),
            match_winner(3, Y), match_winner(4, P), match_winner(5, Y),
            match_winner(6, Y), match_winner(7, P), match_winner(8, Y),
            match_winner(9, P), match_winner(10, P),
        ),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "輸嗰啲局，兩個人每粒方塊嘅攻擊已經睇齊——pinglamb 淨係高過 yachi 唔夠 2%；"
                 "但贏嗰啲局就爭超過 18%。地板貼到實，天花板差咁遠",
        "english_gloss": "in the rounds each lost their attack per piece is within 2 percent; "
                         "in the rounds each won pinglamb's is over 18 percent above yachi's",
        "spec": conj(
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 101, 102),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 118, 119),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "同一件事喺一個人身上講：pinglamb 贏嗰啲局每粒方塊嘅攻擊，高過佢自己輸嗰啲局 "
                 "25%；yachi 自己贏同自己輸淨係爭 7%——分得開贏同輸嘅，今晚淨係得一個",
        "english_gloss": "pinglamb's attack per piece is over 25 percent higher in the rounds he "
                         "won than in the rounds he lost, while yachi's is only about 7 percent "
                         "higher — the winning-versus-losing separation is one player's alone",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 125, 126),
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 107, 108),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "講到盡：yachi 打得最好嗰啲局，離 pinglamb 打得最差嗰啲局淨係 5%，"
                 "但離 pinglamb 打得最好嗰啲局差咗成 15% 以上——佢個天花板貼近對手個地板",
        "english_gloss": "yachi's attack per piece in the rounds he won is about 5 percent above "
                         "pinglamb's in the rounds pinglamb lost, and more than 15 percent below "
                         "pinglamb's in the rounds pinglamb won",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 105, 106),
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        won(P, "garbage_attack"), won(P, "pieces"), 84, 85),
        ),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "多落方塊呢條路今次又係買唔返個 gap：yachi 全晚多疊咗 415 粒方塊，"
                 "打出嘅攻擊反而少 206 條，即係 pinglamb 總攻擊嘅 4% 以上",
        "english_gloss": "yachi placed 415 more pieces than pinglamb yet landed 206 less attack, "
                         "a gap of more than 4 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(415)),
            eq(sub(atk(P), atk(Y)), lit(206)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(4), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(5), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 13 局頂到上天花板收場，11 局係 yachi 頂爆，pinglamb 淨係 2 局",
        "english_gloss": "of the 13 rounds that ended in a topout, 11 were yachi's and 2 were "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(11)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(2)),
        ),
    },
    {
        "id": "C007",
        "category": "style",
        "canto": "個效率 gap 兩頭大中間細：頭三場 pinglamb 每粒方塊嘅攻擊高過 yachi 超過 17%，"
                 "中間第四至第九場唔夠 7%，尾兩場又彈返上 11% 以上——yachi 四場 match "
                 "全部喺中間嗰段贏返嚟",
        "english_gloss": "the attack-per-piece gap was over 17 percent across matches 1-3, under "
                         "7 percent across matches 4-9, and back over 11 percent across matches "
                         "10-11",
        "spec": conj(
            window_gap(0, 3, 117, 118),
            window_gap(3, 9, 106, 107),
            window_gap(9, 11, 111, 112),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C019",
        "category": "style",
        "canto": "十一場入面，yachi 每粒方塊嘅攻擊淨係第九場高過 pinglamb，其餘十場全部輸蝕——"
                 "而第九場就係佢全晚贏得最鬆嗰場",
        "english_gloss": "match 9 is the only one of the eleven where yachi's attack per piece "
                         "is above pinglamb's; in the other ten it is below",
        "spec": conj(*[
            (gt if mi == 8 else lt)(
                mul(window(Y, "garbage_attack", mi, mi + 1), window(P, "pieces", mi, mi + 1)),
                mul(window(P, "garbage_attack", mi, mi + 1), window(Y, "pieces", mi, mi + 1)))
            for mi in range(MATCHES)
        ]),
    },
    {
        "id": "C020",
        "category": "moment",
        "canto": "第十一場係全晚最大嘅一場：兩邊夾埋落咗 2141 粒方塊，比其餘十場每一場都多",
        "english_gloss": "match 11 is the largest of the night at 2141 pieces placed by the two "
                         "players together, more than any other match",
        "spec": conj(
            eq(add(window(Y, "pieces", 10, 11), window(P, "pieces", 10, 11)), lit(2141)),
            *[gt(add(window(Y, "pieces", 10, 11), window(P, "pieces", 10, 11)),
                 add(window(Y, "pieces", mi, mi + 1), window(P, "pieces", mi, mi + 1)))
              for mi in range(MATCHES - 1)],
        ),
    },
]
