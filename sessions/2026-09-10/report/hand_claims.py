"""Hand-written claims for 2026-09-10 — what a generator cannot say about this night.

The generated ledger has the scores, the session records and the per-player rate splits. What
it has no family for is the *comparison between* those splits, and — this session — the fact
that the two sides finished level on both measures at once, which is a first in ten sessions.

**The series is drawn 4-4 and the rounds are 32-33.** No session before this one ended level in
matches, and none came within three rounds; 2026-08-25's 5-4 / 38-35 was the closest on both and
is now second on both. C001 pins the eight match winners and C010 the round totals, plus the one
figure that says how the night actually felt: **after seven matches the round count was level at
28-28**, and the last match decided both columns.

That level finish is not two players playing the same way. Split the rounds by who won them and
the two regimes come apart about as far as this corpus ever puts them:

    attack per piece   won rounds    yachi .6271   pinglamb .7022   -> +11.99%
                       lost rounds   yachi .5317   pinglamb .5384   ->  +1.25%

C002 pins both. **+1.25% is the narrowest lost-regime gap in the corpus**, under 2026-08-14's
+1.78%, and this session is the second of the ten to take the 08-14 shape — ceilings apart,
floors together — where three take its mirror and four are level in both.

**READ THE LOST-REGIME FIGURE WITH ITS LEAVE-ONE-OUT BESIDE IT.** `check_loo` measures the
lost gap at `rel` 2.081, the third-largest in the corpus after 2026-08-01's `score_diff` and
2026-07-28's `attack_diff`: drop m8r4 and +1.2535 becomes +3.8619. m8r4 is the round where
yachi threw the session's second-highest APP (.7207 over 179 pieces) and still lost, so it
lifts his losing-round pool on its own. 「地板貼到實」 is that round's statement as much as the
night's, and the prose carries the annotation. The sign does not flip and the direction
survives; the SIZE does not.

**C005 and C009 are the volume route, a sixth time, and this is the run it lands on.** yachi
threw 276 more pieces for 47 fewer lines of attack. His surplus is 5.14% of pinglamb's count,
so the route can buy back 5.14 pp against C004's 6.65 pp gap, leaving a shortfall of 1.51 pp.
The corpus ordering — sessions ranked by shortfall, ranked the same way by attack difference —
puts 1.51 between 2026-08-01's 1.00 (−32 lines) and 2026-07-24's 2.66 (−72), and so predicts an
attack difference in that band. Measured, it is **−47**: in its slot.

That matters because of what happened last session. 2026-09-03 was the first out-of-sample test
the ordering had and it MISSED, taking Spearman from a perfect 1.000 to 0.950. 09-10 is the
second, and it hits: ρ rises to 0.9636 (exact permutation p = 2.5e-05) with 09-03 still the one
session out of place. So the reading that survives is the one 09-03 forced — a strong monotone
relationship with one inversion, not an exact ranking — and it now has a point arriving on each
side of it. C005 and C009 pin this session's arithmetic and deliberately pin NO position in that
ordering: the ordering ranges over ten sessions and this ledger covers one.

**The attack difference needs its own leave-one-out.** At `rel` 0.766 it crosses THRESHOLD too:
m2r9 alone is 36 of the 47 lines, and without it the difference is −11. 「爭 47 行」 is one
round's; 「兩邊嘅總攻擊撞埋一齊」 is the night's. Both annotations are in the prose.

**The night's oddity has NO claim of its own, and that is the correct call.** m5 and m6 ran
the IDENTICAL round sequence — PPPYPYYYY, both times 0-3 down, both times 5-4 up, the same
winner in all nine slots. The first draft of this ledger gave it a C011 that conjoined the two
matches' `round_seq` runs. That claim is entailed by C015 and C016, which pin those two runs
individually and sit six lines apart in the same file: there is no fact base on which C015 and
C016 both hold and the conjunction fails. By this repo's own screening question — *what would
have to be true for this to fire?* — it is a comment wearing a claim id, the fifth instance of
the class the naive Donation clause and `width_ge_3` belong to. The prose cites [C015][C016]
for the coincidence, which is the same statement with nothing decorative attached, and nothing
anywhere claims a mechanism for it.

The claims are of six kinds:

  * **the shape of the night** — C001 pins all eight match winners at once, C010 the round
    totals and the 28-28 after seven. Eight separate score claims cannot say the series was
    level, because that is a fact about the set of matches and not about any one of them.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality
    because the denominators are different piece counts.
  * **each player against himself** — C003. Both players' attack per piece is higher in the
    rounds they won than in the rounds they lost, the tenth session running that this holds for
    both. pinglamb's +30.44% is his own corpus high and the second-widest player-session of the
    twenty, behind yachi's +31.49% on 2026-08-09.
  * **the route and its price** — C005 and C009. C006 is the death tally, one apart at 5
    against 6 over 65 rounds.
  * **the eight matches, one each** — C011-C018 as `round_seq` runs, the rule every session
    since 2026-08-01 follows: cover *all* of them, so no match card can describe a lead or a
    collapse that no lemma pins.

C008 pins keypresses per piece for both players. It is deliberately NOT a claim about KPP's
paired AUC: that statistic counts rounds by comparing a per-round RATIO between the two players,
and the cond language (`c_field`, `c_winner_gt_loser`, `c_str`, `c_dur`) compares a field against
a literal or against the other player's same field — it has no cross-field ratio, so no
`count_rounds` predicate can express it. What C008 can say is the flatness the AUC is a
consequence of: pooled over the night the two players' KPP differ by 0.214%, **the narrowest this
column has been across the ten sessions** (against 2026-09-03's 0.285%), with yachi on the lower
side. It is deliberately not called the flattest column of this night — per-piece downstacking is
flatter still at 0.262% — because a within-session superlative and a cross-session one are
different claims.

THE PER-MATCH SEPARATION DOES NOT REPRODUCE, and there is deliberately no claim for it.
2026-08-19 and 2026-08-25 each ordered their matches by pinglamb's attack-per-piece advantage and
had the match winner fall out perfectly. Here it interleaves, and badly: yachi won m5 at +18.89%,
the LARGEST gap of the eight, and also m7 at −8.43%, the smallest. Two of ten sessions separate,
eight interleave. There is also no C007-shaped claim available in the weaker「pinglamb leads every
match」form either — he does not: yachi leads attack per piece in m1 and m7.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, ge_, gt, lit, lt,
                                  mul, round_seq, sub, sum_round, sum_round_range,
                                  sum_round_where, match_winner)

Y, P = "yachi", "pinglamb"

MATCHES = 8


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided 「the gap is over 11%」 would survive any further
    collapse of yachi's winning rounds, and every figure this ledger prints is the SIZE of a
    gap, not merely its direction.
    """
    lhs = mul(lit(100), mul(na, db))
    rhs = mul(nb, da)
    return conj(gt(lhs, mul(lit(lo), rhs)), lt(lhs, mul(lit(hi), rhs)))


def rate_x1000(num, den, v):
    """v == floor(1000 * num / den), as `v*den <= 1000*num < (v+1)*den`.

    The algebra has no division, so a derived rate is PINNED by bounding its numerator against
    its own denominator rather than compared to another rate. It has teeth because the band is
    `den` wide while a one-unit change to `num` moves the left side by 1000. Two predicates and
    not one `between`, because `between`'s bounds must be integer literals and this denominator
    is an expression.
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

    `alive` is 1 for the round's survivor and 0 for the player who died, and in first-to-death
    1v1 the survivor is the winner — the generated ledger states that identity and refuses to
    present the two as independent signals. Summing it over a match window is the only way this
    algebra can count a window's round wins: `count_rounds` takes a cond over the whole session
    and has no window form.
    """
    return eq(window(pl, "alive", lo_m, hi_m), lit(n))


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who led when, which is
    the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "YYPPYYY",     # m1  5-2
    "PYPYYPYPP",   # m2  4-5
    "PPPPYP",      # m3  1-5
    "YPYYPPPP",    # m4  3-5
    "PPPYPYYYY",   # m5  5-4
    "PPPYPYYYY",   # m6  5-4   <- byte-for-byte m5's run; see C011
    "YYPYYPPY",    # m7  5-3
    "YPYPYPPYP",   # m8  4-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (0, 4, 5, 6)

MATCH_CANTO = [
    ("第一場 yachi 開波贏兩局，俾人追平之後再連贏三局收，5 比 2",
     "match 1: yachi won the first two, was pegged back, then won the last three, 5-2"),
    ("第二場拉鋸到尾，yachi 4 比 3 領先仲爭一局，最後兩局連失，4 比 5",
     "match 2: yachi led 4-3 needing one round and lost the last two, 4-5"),
    ("第三場全晚最一面倒，yachi 淨係喺第五局贏返一局，1 比 5",
     "match 3: the most one-sided of the night — yachi won only the fifth round, 1-5"),
    ("第四場 yachi 頭四局贏三局，之後四局全失，3 比 5",
     "match 4: yachi won three of the first four and then lost four straight, 3-5"),
    ("第五場 yachi 0 比 3 落後，第四局贏返，跟住尾四局連贏，5 比 4",
     "match 5: yachi went 0-3 down, took the fourth round, then won the last four, 5-4"),
    ("第六場同第五場一模一樣：又係 0 比 3 落後，又係尾四局連贏，5 比 4",
     "match 6: the same run as match 5 — 0-3 down, then the last four, 5-4"),
    ("第七場 yachi 頭兩局贏晒，中段拉開到 4 比 1，5 比 3 收",
     "match 7: yachi won the first two, stretched it to 4-1, and closed it 5-3"),
    ("第八場逐局咬到 4 比 4，最後一局俾 pinglamb 執走，4 比 5",
     "match 8: traded to 4-4 and pinglamb took the last round, 4-5"),
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
        "canto": "八場 match 打成 4 比 4：yachi 攞第一、第五、第六、第七場，"
                 "pinglamb 攞第二、第三、第四、第八場——十晚以嚟第一次冇人贏個系列",
        "english_gloss": "the series is level at four matches each: yachi won matches 1, 5, 6 "
                         "and 7 and pinglamb won matches 2, 3, 4 and 8",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局兩個人每粒方塊嘅攻擊爭 11% 幾，"
                 "輸嗰啲局淨係爭 1% 幾——天花板拉開咗，地板就貼到實",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is between 11 and "
                         "12 percent above yachi's; in the rounds each lost it is between 1 and "
                         "2 percent above",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 111, 112),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 101, 102),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 17% 幾，pinglamb 高 30% 幾。pinglamb 呢個係佢自己十晚以嚟最闊",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by between 17 and 18 percent, pinglamb by "
                         "between 30 and 31 percent",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 117, 118),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 130, 131),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 6% 幾——"
                 "呢個係十晚以嚟最窄嘅一次",
        "english_gloss": "over the whole session pinglamb's attack per piece is between 6 and 7 "
                         "percent above yachi's",
        "spec": pct_between(atk(P), pieces(P), atk(Y), pieces(Y), 106, 107),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 276 粒方塊，打出嘅攻擊反而少 47 條，"
                 "即係 pinglamb 總攻擊嘅 1% 幾",
        "english_gloss": "yachi placed 276 more pieces than pinglamb yet landed 47 less attack, "
                         "a gap of between 1 and 2 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(276)),
            eq(sub(atk(P), atk(Y)), lit(47)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(1), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(2), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 11 局頂到上天花板收場，5 局係 yachi 頂爆、6 局係 pinglamb——差一局",
        "english_gloss": "eleven rounds ended in a topout, five of them yachi's and six "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(5)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(6)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人幾乎一模一樣：yachi 3.598 下，"
                 "pinglamb 3.606 下，爭 0.22%——十晚以嚟最窄嘅一次",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.598 and pinglamb "
                         "3.606, about a fifth of a percent apart",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3598),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3606),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 276 粒方塊盈餘，即係多過 pinglamb 5% 幾——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 5 個幾百分點，而佢要填嘅得 C004 嗰 6 個幾。"
                 "十晚以嚟第一次，佢買得起嗰個窿同要買嘅窿差唔多咁大",
        "english_gloss": "yachi's piece count is between 5 and 6 percent above pinglamb's, which "
                         "is the whole of what the volume route can buy back against the gap "
                         "C004 pins at between 6 and 7 percent",
        "spec": conj(
            gt(mul(lit(100), pieces(Y)), mul(lit(105), pieces(P))),
            lt(mul(lit(100), pieces(Y)), mul(lit(106), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 32 比 33，一局之差——十晚以嚟最貼。打完頭七場仲要係 28 比 28 平手，"
                 "係最後一場先分到高低",
        "english_gloss": "the rounds finished 32 to 33; after the first seven matches they were "
                         "level at 28 each",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 32),
            rounds_won_in(P, 0, MATCHES, 33),
            rounds_won_in(Y, 0, 7, 28),
            rounds_won_in(P, 0, 7, 28),
        ),
    },
] + _seq_claims()
