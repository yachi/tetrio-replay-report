"""Hand-written claims for 2026-09-03 — what a generator cannot say about this night.

The generated ledger has the scores, the session records and the per-player rate splits. What
it has no family for is the *comparison between* those splits, and — this session — the
comparison between the two HALVES of the night, which is where the finding is.

**The night divides at m3 and the two halves are a different night each.** Through the first
three matches the round count is 13-12 to yachi; over the last three it is 6-15. C010 pins
both. What did NOT move across that break is the thing a reader will reach for first:

    attack per piece    m1-m3   yachi .5785   pinglamb .6303   →  +8.95%
                        m4-m6   yachi .5685   pinglamb .6269   → +10.27%

Both players' APP is flat to within two percent of itself, and the gap between them widens by
about one and a third points — while the round split inverts from +1 to −9. So whatever
decided the second half, it is not that pinglamb started hitting harder per piece. C011 pins
the pair of window gaps as a bound each rather than as a difference, because the claim is that
they are CLOSE, and two loose bounds around one number would be satisfied by any pair inside
them.

**What did move is downstacking, and it crosses over.** Garbage cleared per piece:

    m1-m3   yachi .1983   pinglamb .1880   →  pinglamb at 94.8% of yachi
    m4-m6   yachi .1858   pinglamb .2145   →  pinglamb at 115.4% of yachi

C012 pins that crossover — pinglamb below yachi in the first window, above him in the second —
which is the one column in this session that changes sign at the break. It is stated as two
cross-multiplied inequalities and NOT as a ratio of ratios: the four rates have four different
denominators, and a single 「+20 個百分點」 would be a number no lemma here proves.

Read C012 as a description of the second half and not as its cause. Nothing in this ledger
establishes that the downstack crossover produced the 6-15; the same rounds carry both, and a
session is one observation. What C012 buys is that the collapse cannot be told as an attacking
story, because C011 shows the attacking columns did not move.

**C005 and C009 are the volume route again, and this session is the one that breaks its
ordering.** yachi threw 207 more pieces for 120 fewer lines of attack. His surplus is 4.75% of
pinglamb's count, so the route can buy back 4.75 pp against C004's 9.54 pp gap, leaving a
shortfall of 4.79 pp. The corpus's shortfall ordering — every session so far, ranked by
shortfall, ranked identically by attack difference — puts a shortfall of 4.79 between
2026-08-14's 4.61 (−206 lines) and 2026-08-19's 6.89 (−236), and predicts an attack difference
in that band. Measured, it is **−120**, which is outside it on the other side: 09-03 sits where
a shortfall near 3 should sit. Eight sessions ranked perfectly; the ninth does not, and it is
the first added since the ordering was written down, i.e. the first genuine out-of-sample test
it has had. Spearman falls from 1.000 to 0.950 (exact permutation p = 0.0002), so the
relationship survives as a strong monotone one and the perfect ordering does not.

C005 and C009 therefore pin the arithmetic — the surplus, the attack difference, and what the
surplus can buy — and deliberately pin NO position in that ordering. The ordering is a
corpus-level statement over nine sessions; this ledger covers one, and a claim here cannot
range over the other eight.

The claims are of six kinds:

  * **the shape of the night** — C001 pins all six match winners at once, and C010 the round
    counts either side of the break. Six separate score claims cannot state that yachi was
    level after three matches, because that is a fact about a window and not about a match.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer
    inequality because the denominators are different piece counts.
  * **each player against himself** — C003. Both players' attack per piece is higher in the
    rounds they won than in the rounds they lost, the ninth session running that this holds
    for both. Here pinglamb separates himself more than yachi does (+23.7% against +19.3%),
    ending the two-session run in which yachi was the wider of the two.
  * **the route and its price** — C005 and C009. C006 is the death tally, and it is the
    flattest of the corpus: 3 against 4 over 46 rounds.
  * **the break at m3** — C010, C011, C012.
  * **the six matches, one each** — C013-C018 as `round_seq` runs, the rule every session
    since 2026-08-01 follows: cover *all* of them, so no match card can describe a lead or a
    collapse that no lemma pins.

C008 pins keypresses per piece for both players. It is deliberately NOT a claim about KPP's
paired AUC: that statistic counts rounds by comparing a per-round RATIO between the two
players, and the cond language (`c_field`, `c_winner_gt_loser`, `c_str`, `c_dur`) compares a
field against a literal or against the other player's same field — it has no cross-field
ratio, so no `count_rounds` predicate can express it. What C008 can say is the flatness the
AUC is a consequence of: pooled over the night the two players' KPP differ by under 0.3%,
which is the narrowest this column has been in the corpus, with pinglamb on the lower side.

THE PER-MATCH SEPARATION DOES NOT REPRODUCE, and there is deliberately no claim for it.
2026-08-19 and 2026-08-25 each ordered their matches by pinglamb's APP advantage and had the
match winner fall out perfectly. Here it interleaves: yachi's single win (m3, +6.61%) sits
between pinglamb's m4 (+0.58%) and m2 (+7.98%). Two of nine sessions separate, six interleave,
and this one interleaves — which refutes nothing, because the six earlier ones already did.
Writing a weakened version of C007 that "nearly" separates would be fitting a claim to a
session that does not support it.
"""
from pipeline.claims.spec import (c_str, c_winner, conj, count_rounds, eq, ge_, gt, lit, lt,
                                  mul, round_seq, sub, sum_round, sum_round_range,
                                  sum_round_where, match_winner)

Y, P = "yachi", "pinglamb"

MATCHES = 6

# The break: matches [0, SPLIT) against [SPLIT, MATCHES) in 0-based window coordinates.
SPLIT = 3


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def pct_between(na, da, nb, db, lo, hi):
    """lo% < (na/da) / (nb/db) < hi% — a ratio of two rates, cross-multiplied twice.

    Bounding both sides matters: a one-sided 「the gap is over 7%」 would survive any further
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


def win_gap_between(f, lo_m, hi_m, lo, hi):
    """pinglamb's per-piece rate in `f` over matches [lo_m, hi_m) is between lo% and hi% of
    yachi's, cross-multiplied. Window sums only — never `if in_window then x else 0`, whose
    folded-away `if false` would leave a const referenced in the text but unread by the proof."""
    pn, pd = window(P, f, lo_m, hi_m), window(P, "pieces", lo_m, hi_m)
    yn, yd = window(Y, f, lo_m, hi_m), window(Y, "pieces", lo_m, hi_m)
    return pct_between(pn, pd, yn, yd, lo, hi)


def match_seq(mi, winners):
    """Pin a whole match's round order. Stronger than a count: it fixes who led when,
    which is the only way to state a lead that was later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


def rounds_won_in(pl, lo_m, hi_m, n):
    """How many of matches [lo_m, hi_m)'s rounds `pl` won, as a window sum over a 0/1 field.

    `alive` is 1 for the round's survivor and 0 for the player who died, and in first-to-death
    1v1 the survivor is the winner — G036 in the generated ledger states that identity and
    refuses to present the two as independent signals. Summing it over a match window is the
    only way this algebra can count a window's round wins: `count_rounds` takes a cond over the
    whole session and has no window form.
    """
    return eq(window(pl, "alive", lo_m, hi_m), lit(n))


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PYPYYYPPP",   # m1  4-5
    "PPPYYYPYP",   # m2  4-5
    "PYYPYYY",     # m3  5-2
    "PPYPPYP",     # m4  2-5
    "YPYPPPP",     # m5  2-5
    "YPPPYPP",     # m6  2-5
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (2,)

MATCH_CANTO = [
    ("第一場打足九局，yachi 中段連贏三局反超到 4 比 2，最後三局俾人連追走晒，4 比 5",
     "match 1: yachi won three straight in the middle to lead 4-2 and lost the last three, 4-5"),
    ("第二場開波連失三局，跟住連贏三局追平，最後一局收唔到，4 比 5",
     "match 2: yachi lost the first three, won three straight to level, and lost the last, 4-5"),
    ("第三場係 yachi 全晚唯一贏嘅一場，最後四局連贏三局，5 比 2",
     "match 3: yachi's only match of the night — he won three of the last four, 5-2"),
    ("第四場 yachi 得中段一局同尾二一局，2 比 5",
     "match 4: yachi took only the middle round and the second-last, 2-5"),
    ("第五場 yachi 開波贏頭局，第三局再贏返一局，之後四局全失，2 比 5",
     "match 5: yachi won the opening round and the third, then lost the last four, 2-5"),
    ("第六場 yachi 開波贏返一局，之後六局淨係再贏到一局，2 比 5",
     "match 6: yachi won the opening round and only one more, 2-5"),
]


def _seq_claims():
    out = []
    for mi, (run, (canto, gloss)) in enumerate(zip(RUNS, MATCH_CANTO)):
        out.append({
            "id": f"C{13 + mi:03d}",
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
        "canto": "六場 match 入面 yachi 淨係贏到第三場，其餘五場全部俾 pinglamb 攞走，5 比 1 收",
        "english_gloss": "pinglamb won matches 1, 2, 4, 5 and 6 and yachi won match 3, "
                         "five matches to one",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局兩個人每粒方塊嘅攻擊爭 7% 幾，"
                 "輸嗰啲局爭 3% 幾——天花板反而爭得多過地板",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is between 7 and 8 "
                         "percent above yachi's; in the rounds each lost it is between 3 and 4 "
                         "percent above",
        "spec": conj(
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        won(Y, "garbage_attack"), won(Y, "pieces"), 107, 108),
            pct_between(lost(P, "garbage_attack"), lost(P, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 103, 104),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 19% 幾，pinglamb 高 23% 幾。今晚分得開啲嗰個係 pinglamb",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by between 19 and 20 percent, pinglamb by "
                         "between 23 and 24 percent",
        "spec": conj(
            pct_between(won(Y, "garbage_attack"), won(Y, "pieces"),
                        lost(Y, "garbage_attack"), lost(Y, "pieces"), 119, 120),
            pct_between(won(P, "garbage_attack"), won(P, "pieces"),
                        lost(P, "garbage_attack"), lost(P, "pieces"), 123, 124),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 9% 幾",
        "english_gloss": "over the whole session pinglamb's attack per piece is between 9 and 10 "
                         "percent above yachi's",
        "spec": pct_between(atk(P), pieces(P), atk(Y), pieces(Y), 109, 110),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 207 粒方塊，打出嘅攻擊反而少 120 條，"
                 "即係 pinglamb 總攻擊嘅 4% 幾",
        "english_gloss": "yachi placed 207 more pieces than pinglamb yet landed 120 less attack, "
                         "a gap of between 4 and 5 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(207)),
            eq(sub(atk(P), atk(Y)), lit(120)),
            gt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(4), atk(P))),
            lt(mul(lit(100), sub(atk(P), atk(Y))), mul(lit(5), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 7 局頂到上天花板收場，3 局係 yachi 頂爆、4 局係 pinglamb——"
                 "呢一欄係九晚以嚟最平嘅一晚",
        "english_gloss": "seven rounds ended in a topout, three of them yachi's and four "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(3)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(4)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人幾乎一模一樣：yachi 3.619 下，"
                 "pinglamb 3.609 下，爭唔到 0.3%——呢個係全晚最平嘅一欄",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.619 and pinglamb "
                         "3.609, under a third of a percent apart",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3619),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3609),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 207 粒方塊盈餘，即係多過 pinglamb 4% 幾——換返做每粒方塊嘅攻擊，"
                 "呢條路最多只可以填返 4 個幾百分點，但佢要填嘅係 C004 嗰 9 個幾。"
                 "唔係買唔返，係俾佢買嘅嗰個窿大過佢買得起",
        "english_gloss": "yachi's piece count is between 4 and 5 percent above pinglamb's, which "
                         "is the whole of what the volume route can buy back against the gap "
                         "C004 pins at between 9 and 10 percent",
        "spec": conj(
            gt(mul(lit(100), pieces(Y)), mul(lit(104), pieces(P))),
            lt(mul(lit(100), pieces(Y)), mul(lit(105), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "成晚斷開兩橛：頭三場 46 局裏面嘅 25 局，yachi 贏 13 局、pinglamb 贏 12 局，"
                 "打成平手；尾三場 21 局，yachi 得 6 局、pinglamb 攞 15 局",
        "english_gloss": "over the first three matches yachi won 13 rounds to pinglamb's 12; "
                         "over the last three he won 6 to pinglamb's 15",
        "spec": conj(
            rounds_won_in(Y, 0, SPLIT, 13),
            rounds_won_in(P, 0, SPLIT, 12),
            rounds_won_in(Y, SPLIT, MATCHES, 6),
            rounds_won_in(P, SPLIT, MATCHES, 15),
        ),
    },
    {
        "id": "C011",
        "category": "style",
        "canto": "但每粒方塊嘅攻擊兩橛都差唔多：頭三場 pinglamb 高 8% 幾，尾三場高 10% 幾。"
                 "局數由 13 比 12 變 6 比 15，效率個差距就只係闊咗一個幾百分點——"
                 "所以尾三場唔係俾人打得重咗",
        "english_gloss": "pinglamb's attack per piece is between 8 and 9 percent above yachi's "
                         "over the first three matches and between 10 and 11 percent above over "
                         "the last three",
        "spec": conj(
            win_gap_between("garbage_attack", 0, SPLIT, 108, 109),
            win_gap_between("garbage_attack", SPLIT, MATCHES, 110, 111),
        ),
    },
    {
        "id": "C012",
        "category": "style",
        "canto": "真正掉轉頭嗰欄係清垃圾：頭三場每粒方塊清走幾多垃圾，pinglamb 仲低過 yachi，"
                 "得佢嘅 94% 幾；尾三場反過來高過佢，去到 115% 幾。"
                 "全晚淨係呢一欄喺個分水嶺度轉咗正負",
        "english_gloss": "garbage cleared per piece crosses over at the break: over the first "
                         "three matches pinglamb's is between 94 and 95 percent of yachi's, and "
                         "over the last three it is between 115 and 116 percent of it",
        "spec": conj(
            win_gap_between("garbage_cleared", 0, SPLIT, 94, 95),
            win_gap_between("garbage_cleared", SPLIT, MATCHES, 115, 116),
        ),
    },
] + _seq_claims()
