"""Hand-written claims for 2026-08-25 — what a generator cannot say about this night.

The generated ledger has the scores, the session records and the per-player rate splits. What
it has no family for is the *comparison between* those splits, and — for the second session
running — the comparison between the MATCHES, which is where the night's finding is.

Split every round by who won it and pool attack over pieces:

    rounds won     yachi 2570/4005 = .6417    pinglamb 2953/4385 = .6734   →  +4.9%
    rounds lost    yachi 2406/4617 = .5211    pinglamb 2199/3592 = .6122   → +17.5%

Ceilings close, floors apart — 2026-07-22's shape (+5.8 / +12.8) and 2026-08-19's (+6.2 /
+11.1), with the floor gap wider than either. C002 pins the decomposition rather than letting
a reader infer it from the session total, because the session-level gap (C004, +11.9%) is
within a point of 2026-08-19's and says nothing about which regime carries it.

**The finding is C007, and it is 2026-08-19's finding reproducing.** Order the nine matches by
pinglamb's attack-per-piece advantage and the match winner falls out perfectly: yachi's four
wins are the four smallest gaps and pinglamb's five are the five largest, with nothing between
8.3% and 10.3%. Until 2026-08-19 no session in the corpus separated; two now do, back to back.

What C007 must NOT say is 「yachi won the matches where his attack per piece was higher」.
That reading is false NINE times over here, not once: **pinglamb's attack per piece is higher
in every one of the nine matches**, including all four that yachi won. The threshold is not
zero and it is not fixed — 2026-08-19's separation falls between +0.72% and +11.53%, this
one between +8.21% and +10.32% — so what reproduces is a within-night ordering, never a
corpus-wide cut point. A sign-test wording would have been refuted by every match it covers
while still sounding like the same sentence.

**C009 is the other half of C005, and the pair is the point.** A piece surplus buys back an
APP gap of exactly `100·(surplus_pieces/other_pieces − 1)` percentage points; the remainder is
the shortfall. yachi's 645 extra pieces buy 8.09 pp (C009 pins the surplus at between 8 and 9
percent of pinglamb's count) against C004's 11.9 pp gap, so the shortfall is under 4 pp — and
the attack difference, −176 lines, lands where the corpus's shortfall ordering says it should,
between 2026-08-01's −72 at shortfall 2.66 and 2026-08-14's −206 at 4.61. Writing C005 without
C009 beside it would publish 「多疊 645 粒買唔返」 as though volume had failed, when what the
data says is that volume delivered its arithmetic and the gap handed to it was bigger.

The claims are of six kinds:

  * **the shape of the night** — C001 pins all nine match winners at once. pinglamb was five
    matches to one up after six and yachi took the last three straight; nine separate score
    claims cannot state that the wins arrive in a block at the end.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer
    inequality because the denominators are different piece counts.
  * **each player against himself** — C003. Both players' attack per piece is higher in the
    rounds they won than in the rounds they lost, the eighth session running that this holds
    for both. pinglamb's separation is +10.00%, the second-narrowest of his eight, and yachi
    separates himself more than pinglamb does for the second session running.
  * **the route and its price** — C005 and C009, above. C006 is the death tally, and this one
    is not flat: 9 against 4, yachi's second-worst after 2026-08-14's 11.
  * **where the gap actually was** — C007.
  * **the nine matches, one each** — C010-C018 as `round_seq` runs, the rule every session
    since 2026-08-01 follows: cover *all* of them, so no match card can describe a lead or a
    collapse that no lemma pins.

C008 pins keypresses per piece for both players. It is deliberately NOT a claim about KPP's
paired AUC: that statistic counts rounds by comparing a per-round RATIO between the two
players, and the cond language (`c_field`, `c_winner_gt_loser`, `c_str`, `c_dur`) compares a
field against a literal or against the other player's same field — it has no cross-field
ratio, so no `count_rounds` predicate can express it. What C008 can say is the flatness the
AUC is a consequence of: pooled over the night the two players' KPP differ by about 1.1%,
with yachi on the lower side.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, ge_, gt, lit, lt,
                                  mul, round_seq, sub, sum_round, sum_round_range,
                                  sum_round_where, match_winner)

Y, P = "yachi", "pinglamb"

MATCHES = 9


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided 「the gap is over 17%」 would survive any further
    collapse of yachi's losing rounds, and every figure this ledger prints is the SIZE of a
    gap, not merely its direction.
    """
    lhs = mul(lit(100), mul(na, db))
    rhs = mul(nb, da)
    return conj(gt(lhs, mul(lit(lo), rhs)), lt(lhs, mul(lit(hi), rhs)))


def rate_x1000(num, den, v):
    """v == floor(1000 * num / den), as `v*den <= 1000*num < (v+1)*den`.

    The algebra has no division, so a derived rate is PINNED by bounding its numerator
    against its own denominator rather than compared to another rate. It has teeth because
    the band is `den` wide while a one-unit change to `num` moves the left side by 1000.
    Two predicates and not one `between`, because `between`'s bounds must be integer
    literals and this denominator is an expression.
    """
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


def match_gap_under(mi, pct):
    """pinglamb's attack-per-piece advantage over match `mi` is under `pct - 100` percent."""
    return lt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1),
                                window(Y, "pieces", mi, mi + 1))),
              mul(lit(pct), mul(window(Y, "garbage_attack", mi, mi + 1),
                                window(P, "pieces", mi, mi + 1))))


def match_gap_over(mi, pct):
    return gt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1),
                                window(Y, "pieces", mi, mi + 1))),
              mul(lit(pct), mul(window(Y, "garbage_attack", mi, mi + 1),
                                window(P, "pieces", mi, mi + 1))))


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who led when,
    which is the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PYPYYYPPP",   # m1  4-5
    "PPPYPYYP",    # m2  3-5
    "YPYYPYY",     # m3  5-2
    "YPPYPPP",     # m4  2-5
    "PYYYPPPYP",   # m5  4-5
    "PPPPYYP",     # m6  2-5
    "PYYYPPYY",    # m7  5-3
    "PPYPYPYYY",   # m8  5-4
    "YYYPPPPYY",   # m9  5-4
]

# The matches yachi won, 0-based. C001 and C007 both range over this, so it is written once.
YACHI_MATCHES = (2, 6, 7, 8)

MATCH_CANTO = [
    ("第一場打足九局，yachi 中段連贏三局反超到 4 比 2，最後三局俾人連追走晒，4 比 5",
     "match 1: yachi won three straight in the middle to lead 4-2 and lost the last three, 4-5"),
    ("第二場開波連失三局，中段追返三局到 3 比 4，最後一局收唔到，3 比 5",
     "match 2: yachi lost the first three, won three of the next four to reach 3-4, and lost "
     "the last, 3-5"),
    ("第三場係 yachi 全晚打得最順嗰場，七局攞五局，5 比 2",
     "match 3: yachi's cleanest match — five of seven rounds, 5-2"),
    ("第四場 yachi 贏頭局，之後七局入面淨係再贏到一局，2 比 5",
     "match 4: yachi won the opening round and only one more, 2-5"),
    ("第五場 yachi 連贏三局做到 3 比 1，跟住連失三局，最後一局輸波，4 比 5",
     "match 5: yachi won three straight to lead 3-1, lost three straight, and lost the "
     "decider, 4-5"),
    ("第六場開波連失四局，追返兩局都太遲，2 比 5",
     "match 6: yachi lost the first four and his two back were too late, 2-5"),
    ("第七場 yachi 連贏三局，中段俾人追返兩局，最後連贏兩局收波，5 比 3",
     "match 7: yachi won three straight, conceded two, and closed with two more, 5-3"),
    ("第八場打足九局，yachi 最後連贏三局，5 比 4",
     "match 8: nine rounds — yachi won the last three, 5-4"),
    ("第九場 yachi 開波連贏三局，跟住連失四局，最後兩局又贏返，5 比 4",
     "match 9: yachi won the first three, lost four straight, and took the last two, 5-4"),
]


def _seq_claims():
    out = []
    for mi, (run, (canto, gloss)) in enumerate(zip(RUNS, MATCH_CANTO)):
        out.append({
            "id": f"C{10 + mi:03d}",
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
        "canto": "九場 match 入面 pinglamb 贏咗頭六場入面嘅五場，一度 5 比 1 拋離，"
                 "跟住 yachi 尾三場連贏，全晚 4 比 5 收",
        "english_gloss": "pinglamb won matches 1, 2, 4, 5 and 6 to lead five matches to one, "
                         "and yachi won the last three of the night to finish 4-5",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局兩個人每粒方塊嘅攻擊爭 4% 幾，"
                 "輸嗰啲局爭到 17% 幾——天花板貼得好近，地板差好遠",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is between 4 and 5 "
                         "percent above yachi's; in the rounds each lost it is between 17 and 18 "
                         "percent above",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 104, 105),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 117, 118),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 23% 幾，pinglamb 高 10% 出頭。連續第二晚分得最開嗰個係 yachi",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by between 23 and 24 percent, pinglamb by "
                         "between 10 and 11 percent",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 123, 124),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 110, 111),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 11% 幾",
        "english_gloss": "over the whole session pinglamb's attack per piece is between 11 and 12 "
                         "percent above yachi's",
        "spec": pct_between(atk(P), pieces(P), atk(Y), pieces(Y), 111, 112),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 645 粒方塊，打出嘅攻擊反而少 176 條，"
                 "即係 pinglamb 總攻擊嘅 3% 幾",
        "english_gloss": "yachi placed 645 more pieces than pinglamb yet landed 176 less attack, "
                         "a gap of between 3 and 4 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(645)),
            eq(sub(atk(P), atk(Y)), lit(176)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(3), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(4), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 13 局頂到上天花板收場，9 局係 yachi 頂爆、4 局係 pinglamb——"
                 "yachi 呢個係佢八晚以嚟第二差",
        "english_gloss": "thirteen rounds ended in a topout, nine of them yachi's and four "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(9)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(4)),
        ),
    },
    {
        "id": "C007",
        "category": "style",
        "canto": "九場 match 排開，個效率差距同邊個贏場波完全分得開：yachi 贏嗰四場，"
                 "pinglamb 每粒方塊嘅攻擊高唔夠 9%；pinglamb 贏嗰五場，佢每場都高過 10%，"
                 "中間一場都冇。要留意個分界線唔係零——九場 match pinglamb 每場都高過 yachi，"
                 "連 yachi 贏嗰四場都係，所以分得開嘅係個差距幾大，唔係邊個高",
        "english_gloss": "in each of the four matches yachi won, pinglamb's attack per piece is "
                         "less than 9 percent above yachi's; in each of the five matches "
                         "pinglamb won it is more than 10 percent above",
        "spec": conj(*[(match_gap_under(mi, 109) if mi in YACHI_MATCHES
                        else match_gap_over(mi, 110))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人好接近：yachi 3.581 下，pinglamb 3.621 下，"
                 "yachi 按少約 1%——呢個係全晚最平嘅一欄",
        "english_gloss": "keypresses per piece are close: yachi 3.581 and pinglamb 3.621, about "
                         "1 percent apart",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3581),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3621),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 645 粒方塊盈餘，即係多過 pinglamb 8% 幾——換返做每粒方塊嘅攻擊，"
                 "呢條路最多只可以填返 8 個百分點，但佢要填嘅係 C004 嗰 11 個幾。"
                 "唔係買唔返，係俾佢買嘅嗰個窿本身大過佢買得起",
        "english_gloss": "yachi's piece count is between 8 and 9 percent above pinglamb's, which "
                         "is the whole of what the volume route can buy back against the gap "
                         "C004 pins at between 11 and 12 percent",
        "spec": conj(
            gt(mul(lit(100), pieces(Y)), mul(lit(108), pieces(P))),
            lt(mul(lit(100), pieces(Y)), mul(lit(109), pieces(P))),
        ),
    },
] + _seq_claims()
