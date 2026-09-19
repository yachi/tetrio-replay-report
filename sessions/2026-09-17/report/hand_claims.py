"""Hand-written claims for 2026-09-17 — what a generator cannot say about this night.

The generated ledger has the scores, the session records and the per-player rate splits. What it
has no family for is the *comparison between* those splits — and this session is the one the corpus
has been waiting eleven nights for, because it does the thing CLAUDE.md records as never having
happened.

**pinglamb takes the series 5-2 and the rounds 30-19.** C001 pins all seven match winners and C010
the round totals plus the shape that makes this night worth writing up: after three matches the
rounds stood at **14-10 to YACHI**, and he took 5 of the last 20. Nothing about the final scoreline
says that, which is exactly why the window is a claim and not a sentence.

**BOTH REGIME GAPS ARE LARGE, and that has not happened before.** Split the rounds by who won them:

    attack per piece   won rounds    yachi .6093   pinglamb .6981   ->  +14.57%
                       lost rounds   yachi .5120   pinglamb .5920   ->  +15.63%

C002 pins both. Ranked against their OWN columns over the twelve sessions — which is the check
CLAUDE.md demands before any pair is called 「both large」, and which a first draft of this docstring
skipped — the won-gap is **2nd of twelve** (median +7.78) and the lost-gap **3rd of twelve** (median
+6.65). No earlier session has both in the top half by more than a hair: 07-24's +10.8/+7.3 is
ranks 4 and 6, with the second figure a tenth of a point above its median, and CLAUDE.md already
names it as the closest prior case. So this is the first session where the two regimes are apart at
once rather than one being apart and the other level.

Two things this must NOT be turned into. It is **not the most balanced session** — the won/lost
ratio here is 0.93 and 07-28's is 0.98, closer to 1. What is new is that the balance sits on LARGE
values: 07-28 is balanced at +5.9/+6.0, both below their medians, which is the 「roughly level」
class and the opposite reading. And it is **not a mirror and not the mirror's opposite**: the
mirror shape (08-14, 09-10) is a wide ceiling over a floor that has met, and this is neither.

**NEITHER figure needs a 「得一局撐住」 annotation, and for this session that is the load-bearing
measurement rather than a footnote.** 「Both gaps large」 is a claim about two pooled ratios, so the
first question is whether either is one round's. `check_loo` puts the won-gap at `rel` 0.107 (m5r1,
and 1.02x the next round — the FLATTEST x2nd column in the corpus, meaning no single round stands
out at all) and the lost-gap at 0.226 (m3r8, 1.77x). Both are under half of THRESHOLD and neither
flips sign, so the headline survives dropping any round. The measurement is recorded in
`check_loo.PUBLISHED` because 「no caveat」 must never be an omission.

**C004's session gap of +20.11% is the corpus record**, past 08-09's +18.08%. Note it is LARGER
than either regime's gap, which is the arithmetic of pooling over two differently-sized round pools
and not a finding — it is why the decomposition is re-derived every session instead of read off the
session figure.

**C005 and C009 are the volume route, an eighth time.** yachi threw 455 more pieces for 250 fewer
lines of attack, 8.38% of pinglamb's total. His surplus is 10.05% of pinglamb's count — the LARGEST
buy-back the route has ever had — and it is asked to cover C004's 20.11 pp, the largest hole. Both
ends of the arithmetic are corpus records and they very nearly cancel: the shortfall is 10.06 pp,
which lands 0.03 pp from 08-09's 10.03. C005 and C009 pin this session's arithmetic and
deliberately pin NO position in the corpus ordering: that ordering ranges over twelve sessions and
this ledger covers one.

**C007 IS MINTED AND ITS EVIDENCE IS WEAKER THAN THE TWO EARLIER ONES BY A FACTOR OF SIX.** Order
the seven matches by pinglamb's attack-per-piece advantage and yachi's two wins are the two
smallest (+3.90%, +13.47%), pinglamb's five the five largest (+16.91% … +44.36%), nothing between
13.47 and 16.91. That is 08-19's and 08-25's pattern, and the honest way to say so is to put the
power beside it: with k wins among m matches a random assignment puts all k at the bottom with
probability 1/C(m,k) — **1/120 for 08-19's 3 of 10, 1/126 for 08-25's 4 of 9, and 1/21 here.**

1 in 21 is not 1 in 120 and it is not 09-11's 1 in 7 either, which CLAUDE.md files as degenerate
because one win among seven leaves the ordering almost unable to fail. Two wins among seven gives
twenty ways to fail and it took none of them, so the claim is minted; but the report prose states
the 1-in-21 rather than leaving it here, exactly as 09-11's states its 1-in-7. The corpus count
becomes 3 of 12 and the three are NOT equally powered — a sentence that says 「it separated again」
without that is the provenance mistake CLAUDE.md's whole 冇第二份 section is about.

What makes the separation substantive here rather than merely ordinal is the spread it sits in:
the per-match gaps run 3.90% to 44.36%, and m7's +44.36% is the largest per-match gap in the
corpus, past 08-19's +40.67%.

The claims are of six kinds:

  * **the shape of the night** — C001 pins all seven match winners at once, C010 the round totals
    and the 14-10 yachi led by after three matches. Seven separate score claims cannot say a lead
    was given back, because that is a fact about the sequence of matches and not about any one.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality
    because the denominators are different piece counts.
  * **each player against himself** — C003. Both players' attack per piece is higher in the rounds
    they won than in the rounds they lost, the twelfth session running that this holds for both.
    yachi's +19.01% against pinglamb's +17.92% puts **yachi the wider of the two**, which ends the
    run of three sessions with pinglamb wider and takes the count to six of twelve. Stated as a
    count and NOT as a trend: the same column put yachi 24.6 points ahead on 2026-08-09 and
    pinglamb 12.5 ahead on 2026-09-10.
  * **the route and its price** — C005 and C009. C006 is the death tally, 4 against 2.
  * **the ordering that separates** — C007, with its power stated in the prose that cites it.
  * **the seven matches, one each** — C011-C017 as `round_seq` runs, the rule every session since
    2026-08-01 follows: cover *all* of them, so no match card can describe a lead or a collapse
    that no lemma pins. m1 is why the rule earns its keep this session — yachi led it 4-1 and lost
    it 4-5, and only the sequence can say that.

C008 pins keypresses per piece for both players, pooled: yachi 3.592 and pinglamb 3.623, 0.84%
apart with **yachi on the lower side**, which is the side he was on for 09-10 and the opposite of
09-11. Three sessions, two flips, so the column's sign is a fact about a night and not about
either player. It is deliberately NOT a claim about KPP's paired AUC: that statistic counts rounds
by comparing a per-round RATIO between the two players, and the cond language (`c_field`,
`c_winner_gt_loser`, `c_str`, `c_dur`) compares a field against a literal or against the other
player's same field — it has no cross-field ratio, so no `count_rounds` predicate can express it.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, ge_, gt, lit, lt,
                                  mul, round_seq, sub, sum_round, sum_round_range,
                                  sum_round_where, match_winner)

Y, P = "yachi", "pinglamb"

MATCHES = 7


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided 「the gap is over 14%」 would survive any further
    collapse of yachi's winning rounds, and every figure this ledger prints is the SIZE of a gap,
    not merely its direction. It matters more than usual here, because the finding is that the two
    gaps are BOTH large and CLOSE TO EACH OTHER — a pair of one-sided lower bounds could not
    distinguish +14.6/+15.6 from +14.6/+60.
    """
    lhs = mul(lit(100), mul(na, db))
    rhs = mul(nb, da)
    return conj(gt(lhs, mul(lit(lo), rhs)), lt(lhs, mul(lit(hi), rhs)))


def rate_x1000(num, den, v):
    """v == floor(1000 * num / den), as `v*den <= 1000*num < (v+1)*den`.

    The algebra has no division, so a derived rate is PINNED by bounding its numerator against its
    own denominator rather than compared to another rate. It has teeth because the band is `den`
    wide while a one-unit change to `num` moves the left side by 1000. Two predicates and not one
    `between`, because `between`'s bounds must be integer literals and this denominator is an
    expression.
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


def rounds_won_in(pl, lo_m, hi_m, n):
    """How many of matches [lo_m, hi_m)'s rounds `pl` won, as a window sum over a 0/1 field.

    `alive` is 1 for the round's survivor and 0 for the player who died, and in first-to-death 1v1
    the survivor is the winner — the generated ledger states that identity and refuses to present
    the two as independent signals. Summing it over a match window is the only way this algebra can
    count a window's round wins: `count_rounds` takes a cond over the whole session and has no
    window form.
    """
    return eq(window(pl, "alive", lo_m, hi_m), lit(n))


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
    """Pin a whole match's round order. Stronger than a count: it fixes who led when, which is the
    only way to state a lead that was later given back — and m1 is exactly that this session."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "YYPYYPPPP",   # m1  4-5   <- yachi led 4-1
    "PYPYYYY",     # m2  5-2
    "YPPYYPYY",    # m3  5-3
    "PPPYPP",      # m4  1-5
    "YPPPPP",      # m5  1-5
    "YPPPYYPP",    # m6  3-5
    "PPPPP",       # m7  0-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (1, 2)

MATCH_CANTO = [
    ("第一場 yachi 開波贏頭兩局，第四第五局再贏，4 比 1 領先，之後連失四局收 4 比 5",
     "match 1: yachi won the first two and the fourth and fifth to lead 4-1, then lost four "
     "straight to lose it 4-5"),
    ("第二場 yachi 輸咗第一同第三局，跟住連贏四局，5 比 2",
     "match 2: yachi lost the first and third, then won four straight, 5-2"),
    ("第三場逐局咬到 4 比 3，yachi 再贏最後一局，5 比 3",
     "match 3: traded to 4-3 and yachi took the last, 5-3"),
    ("第四場 yachi 淨係贏到第四局，1 比 5",
     "match 4: yachi took only the fourth round, 1-5"),
    ("第五場 yachi 開波贏一局，之後五局全失，1 比 5",
     "match 5: yachi won the first and then lost five straight, 1-5"),
    ("第六場 yachi 第一局同第五第六局贏，尾兩局連失，3 比 5",
     "match 6: yachi won the first and the fifth and sixth, then lost the last two, 3-5"),
    ("第七場 yachi 一局都冇贏，0 比 5——全晚唯一一場剃光頭",
     "match 7: yachi won no round at all, 0-5 — the night's only shutout"),
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
        "canto": "七場 match 打成 2 比 5：yachi 攞到第二同第三場，其餘五場俾 pinglamb 攞晒",
        "english_gloss": "pinglamb won the series five matches to two: yachi won matches 2 and 3",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇，今晚兩邊一齊拉開：贏嗰啲局兩個人每粒方塊嘅攻擊爭 14% 幾，"
                 "輸嗰啲局爭 15% 幾——十二晚以嚟第一次，天花板同地板一齊爭得咁大，"
                 "而且地板爭得仲多過天花板少少",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is between 14 and 15 "
                         "percent above yachi's; in the rounds each lost it is between 15 and 16 "
                         "percent above — both regimes apart at once",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 114, 115),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 115, 116),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 19% 幾，pinglamb 高 17% 幾，今次闊嗰個係 yachi",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by between 19 and 20 percent, pinglamb by "
                         "between 17 and 18 percent, with yachi the wider of the two",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 119, 120),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 117, 118),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 20% 幾——十二晚以嚟最闊嘅一次",
        "english_gloss": "over the whole session pinglamb's attack per piece is between 20 and 21 "
                         "percent above yachi's",
        "spec": pct_between(atk(P), pieces(P), atk(Y), pieces(Y), 120, 121),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 455 粒方塊，打出嘅攻擊反而少 250 條，"
                 "即係 pinglamb 總攻擊嘅 8% 幾",
        "english_gloss": "yachi placed 455 more pieces than pinglamb yet landed 250 less attack, "
                         "a gap of between 8 and 9 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(455)),
            eq(sub(atk(P), atk(Y)), lit(250)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(8), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(9), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚得 6 局頂到上天花板收場，4 局係 yachi 頂爆、2 局係 pinglamb——"
                 "呢個比率係十二晚第二低，淨係高過 08-09",
        "english_gloss": "six rounds ended in a topout, four of them yachi's and two pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(4)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(2)),
        ),
    },
    {
        "id": "C007",
        "category": "style",
        "canto": "七場 match 排開，個效率差距同邊個贏場波分得開：yachi 贏嗰兩場，"
                 "pinglamb 每粒方塊嘅攻擊高唔夠 14%；pinglamb 贏嗰五場，佢每場都高過 16%，"
                 "中間一場都冇。要留意兩樣嘢——個分界線唔係零（七場 match pinglamb 每場都高過 "
                 "yachi，連 yachi 贏嗰兩場都係，所以分得開嘅係個差距幾大，唔係邊個高），"
                 "同埋兩勝七場排得咁靚，隨機都有廿一分之一機會，證據弱過 08-19 同 08-25 六倍",
        "english_gloss": "in each of the two matches yachi won, pinglamb's attack per piece is "
                         "less than 14 percent above yachi's; in each of the five matches "
                         "pinglamb won it is more than 16 percent above",
        "spec": conj(*[(match_gap_under(mi, 114) if mi in YACHI_MATCHES
                        else match_gap_over(mi, 116))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.592 下，pinglamb 3.623 下，"
                 "爭 0.84%——今次低嗰個係 yachi",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.592 and pinglamb "
                         "3.623, under a percent apart, with yachi the lower",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3592),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3623),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 455 粒方塊盈餘，即係多過 pinglamb 10% 幾——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 10 個幾百分點，係十二晚以嚟買得最多嘅一次。"
                 "但佢要填嘅係 C004 嗰 20 個幾，一樣係十二晚以嚟最大嘅一個窿——"
                 "條路同個窿兩頭都破紀錄，啱啱好抵銷",
        "english_gloss": "yachi's piece count is between 10 and 11 percent above pinglamb's, "
                         "which is the whole of what the volume route can buy back against the "
                         "gap C004 pins at between 20 and 21 percent",
        "spec": conj(
            gt(mul(lit(100), pieces(Y)), mul(lit(110), pieces(P))),
            lt(mul(lit(100), pieces(Y)), mul(lit(111), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 19 比 30。但打完頭三場係 14 比 10 — yachi 領先——"
                 "之後二十局佢淨係贏到五局。個比數睇唔出呢件事，所以要另外講",
        "english_gloss": "the rounds finished 19 to 30; after the first three matches they stood "
                         "at 14 to 10 in yachi's favour",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 19),
            rounds_won_in(P, 0, MATCHES, 30),
            rounds_won_in(Y, 0, 3, 14),
            rounds_won_in(P, 0, 3, 10),
        ),
    },
] + _seq_claims()
