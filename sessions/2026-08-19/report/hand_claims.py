"""Hand-written claims for 2026-08-19 — what a generator cannot say about this night.

The generated ledger has the scores, the session records and the per-player rate splits. What
it has no family for is the *comparison between* those splits, and — this session — the
comparison between the ten MATCHES, which is where the night's finding is.

Split every round by who won it and pool attack over pieces:

    rounds won     yachi 1664/2446 = .6803    pinglamb 2488/3443 = .7226   →  +6.2%
    rounds lost    yachi 1951/3529 = .5528    pinglamb 1363/2220 = .6140   → +11.1%

That is neither 2026-08-09 (won +1.8, lost +25.4) nor its mirror 2026-08-14 (won +18.9, lost
+1.8) — it is a return to the ordinary band, and it reproduces 2026-07-22's shape (+5.8 /
+12.8) almost exactly. Two consecutive extremes did not become a trend in either direction,
which is why C002 pins the decomposition rather than letting a reader infer it from the
session total: the session-level gap (C004, +12.4%) is the same size on all three of those
nights and says nothing about which regime carries it.

**The finding is C007, and it is the one claim here that had to be worded against its own
obvious reading.** Order the ten matches by pinglamb's attack-per-piece advantage and the
match winner falls out perfectly: yachi's three wins are the three smallest gaps and
pinglamb's seven are the seven largest, with nothing in between — under 1% against over 11%.
No other session in the corpus separates. What C007 must NOT say is 「yachi won the matches
where his attack per piece was higher」: that is FALSE, because match 4 is a yachi win with
pinglamb 0.72% ahead. The threshold is not zero, and the claim is a separation with a gap in
it, not a sign test. A sign-test wording would have been refuted by one of the ten matches it
covers while still sounding like the same sentence.

The claims are of six kinds:

  * **the shape of the night** — C001 pins all ten match winners at once. yachi took matches
    1, 4 and 7 and then lost the last three straight; ten separate score claims cannot state
    that the wins stop after match 7.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer
    inequality because the denominators are different piece counts.
  * **each player against himself** — C003. Both players' attack per piece is higher in the
    rounds they won than in the rounds they lost, which is the seventh session running that
    this holds for both; here yachi separates his own regimes MORE than pinglamb does
    (+23% against +18%), the second session where that is true.
  * **the route and its price** — C005 is the volume route again: 312 more pieces for 236
    less attack. C006 is the death tally, and it is the flat one — 4 against 3, where the
    previous session had 11 against 2.
  * **where the gap actually was** — C007, above.
  * **the ten matches, one each** — C009-C018 as `round_seq` runs, the rule every session
    since 2026-08-01 follows: cover *all* of them, so no match card can describe a lead or a
    collapse that no lemma pins.

C008 pins keypresses per piece for both players. It is deliberately NOT a claim about KPP's
paired AUC: that statistic counts rounds by comparing a per-round RATIO between the two
players, and the cond language (`c_field`, `c_winner_gt_loser`, `c_str`, `c_dur`) compares a
field against a literal or against the other player's same field — it has no cross-field
ratio, so no `count_rounds` predicate can express it. What C008 can say is the flatness the
AUC is a consequence of: pooled over the night the two players' KPP differ by about 0.3%.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, ge_, gt, lit, lt,
                                  match_winner, mul, round_seq, sub, sum_round,
                                  sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 10


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided 「the gap is over 11%」 would survive any further
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


def match_gap(mi, lo, hi):
    """pinglamb's attack per piece against yachi's, over match `mi` alone (0-based)."""
    return pct_between(window(P, "garbage_attack", mi, mi + 1), window(P, "pieces", mi, mi + 1),
                       window(Y, "garbage_attack", mi, mi + 1), window(Y, "pieces", mi, mi + 1),
                       lo, hi)


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
    "PYYYPYPY",   # m1  5-3
    "YPPPPP",     # m2  1-5
    "PPPPP",      # m3  0-5
    "YPPYYYPY",   # m4  5-3
    "YPPPYPP",    # m5  2-5
    "YPPPYPP",    # m6  2-5
    "YYYYPY",     # m7  5-1
    "PPYPPP",     # m8  1-5
    "PYPPYYYPP",  # m9  4-5
    "YPPPPYYP",   # m10 3-5
]

# The matches yachi won, 0-based. C001 and C007 both range over this, so it is written once.
YACHI_MATCHES = (0, 3, 6)

MATCH_CANTO = [
    ("第一場一開波輸咗第一局，跟住連贏三局反超，最後穩住 5 比 3",
     "match 1: yachi lost the opening round, won the next three and held on for 5-3"),
    ("第二場 yachi 贏咗開頭嗰局之後連輸五局，1 比 5",
     "match 2: yachi won the first round then lost five straight, 1-5"),
    ("第三場係全晚唯一一場白果，五局全部 pinglamb 攞，0 比 5",
     "match 3: the night's only sweep — pinglamb won all five rounds, 0-5"),
    ("第四場 yachi 贏頭局之後連失兩局，跟住連贏三局反超，最後一局收波，5 比 3",
     "match 4: yachi won the first, lost two, then won three straight and took the last, 5-3"),
    ("第五場 yachi 贏頭局同第五局，其餘全失，2 比 5",
     "match 5: yachi took the first and the fifth rounds and lost the rest, 2-5"),
    ("第六場同第五場一模一樣嘅走勢：贏頭局同第五局，2 比 5",
     "match 6: the same run as match 5 — the first and the fifth rounds only, 2-5"),
    ("第七場 yachi 打得最順，開波連贏四局，六局收工，5 比 1",
     "match 7: yachi's cleanest match — four straight from the start, over in six, 5-1"),
    ("第八場 yachi 淨係贏到第三局，1 比 5",
     "match 8: yachi won only the third round, 1-5"),
    ("第九場係全晚最長嘅一場，yachi 一度連贏三局追到 4 比 4，最後兩局俾人收晒，4 比 5",
     "match 9: the night's longest — yachi won three straight to level at 4-4 and lost the "
     "last two, 4-5"),
    ("第十場 yachi 贏頭局之後連輸四局，追返兩局都太遲，3 比 5",
     "match 10: yachi won the first, lost four straight, and his two back were too late, 3-5"),
]


def _seq_claims():
    out = []
    for mi, (run, (canto, gloss)) in enumerate(zip(RUNS, MATCH_CANTO)):
        out.append({
            "id": f"C{9 + mi:03d}",
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
        "canto": "十場 match 入面 yachi 贏咗第一、第四同第七場，之後尾三場連輸，"
                 "全晚 3 比 7",
        "english_gloss": "yachi won matches 1, 4 and 7 and pinglamb won the other seven, "
                         "including the last three of the night",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局兩個人每粒方塊嘅攻擊爭 6% 幾，"
                 "輸嗰啲局爭 11% 幾——兩個範圍都唔算闊，輸嗰邊爭得多啲",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is between 6 and 7 "
                         "percent above yachi's; in the rounds each lost it is between 11 and 12 "
                         "percent above",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 106, 107),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 111, 112),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 23% 幾，pinglamb 高 17% 幾。今次分得最開嗰個係 yachi",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by between 23 and 24 percent, pinglamb by "
                         "between 17 and 18 percent",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 123, 124),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 117, 118),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 12% 幾",
        "english_gloss": "over the whole session pinglamb's attack per piece is between 12 and 13 "
                         "percent above yachi's",
        "spec": pct_between(atk(P), pieces(P), atk(Y), pieces(Y), 112, 113),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "多落方塊呢條路今次又係買唔返個 gap：yachi 全晚多疊咗 312 粒方塊，"
                 "打出嘅攻擊反而少 236 條，即係 pinglamb 總攻擊嘅 6% 幾",
        "english_gloss": "yachi placed 312 more pieces than pinglamb yet landed 236 less attack, "
                         "a gap of between 6 and 7 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(312)),
            eq(sub(atk(P), atk(Y)), lit(236)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(6), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(7), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚得 7 局頂到上天花板收場，4 局係 yachi 頂爆、3 局係 pinglamb，"
                 "兩邊差唔多",
        "english_gloss": "seven rounds ended in a topout, four of them yachi's and three "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(4)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(3)),
        ),
    },
    {
        "id": "C007",
        "category": "style",
        "canto": "十場 match 排開，個效率差距同邊個贏場波完全分得開：yachi 贏嗰三場，"
                 "pinglamb 每粒方塊嘅攻擊高唔夠 1%；pinglamb 贏嗰七場，佢每場都高過 11%，"
                 "中間一場都冇。要留意個分界線唔係零——第四場 pinglamb 都仲係高少少，"
                 "但一樣係 yachi 贏",
        "english_gloss": "in each of the three matches yachi won, pinglamb's attack per piece is "
                         "less than 1 percent above yachi's; in each of the seven matches "
                         "pinglamb won it is more than 11 percent above",
        "spec": conj(*[(match_gap_under(mi, 101) if mi in YACHI_MATCHES
                        else match_gap_over(mi, 111))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人幾乎一樣：yachi 3.628 下，pinglamb 3.639 下，"
                 "爭唔夠 0.3%——呢個係全晚最平嘅一欄",
        "english_gloss": "keypresses per piece are nearly identical: yachi 3.628 and pinglamb "
                         "3.639, under 0.3 percent apart",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3628),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3639),
        ),
    },
] + _seq_claims()
