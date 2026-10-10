"""Hand-written claims for 2026-10-09 — what a generator cannot say about this night.

**Twelve matches and 102 rounds, pinglamb 7-5 in matches and 53-49 in rounds.** The sixteenth
session in date order and in arrival. Seven of the twelve matches went to a ninth round [G016],
and after eight matches the series stood 4-4 and the rounds 33-34 [C001][C010]; pinglamb then took
m9, m10 and m11, two of them 5-4, and yachi took m12. So the whole margin of the series sits in
three consecutive close matches, which is 09-03's shape (the margin arrives late) at a closer
size.

**THE VOLUME ROUTE WORKED, AND IT IS STILL NOT WHAT DECIDED THE NIGHT.** C004's session gap is
+11.52%: pinglamb's attack per piece is that much above yachi's. yachi threw 1064 more pieces —
12.64% more than pinglamb's count [C009], by some way the largest surplus the corpus holds as a
count and as a rate — and the surplus buys back MORE than the whole gap. So the shortfall
(the gap minus what the surplus buys) is negative, about −1.12, and yachi's attack total is the
higher one: 5815 against 5757, 58 lines and 1.00% of pinglamb's total [C005]. 07-22 is the only
other session where yachi out-attacked pinglamb over the night, and that by 28.

**The 58 is one round's as much as the night's.** `check_loo` puts `attack_diff` at `rel` 0.603:
drop m7r8 — the longest round of the night, ~217 s, where yachi cleared 201 lines and survived
[G024][G025] — and the difference is +23. The sign holds and the size does not, which is why the
sentence that publishes it in narrative-beats.md carries the annotation, and why C005 pins the
two raw counts beside the rate rather than letting the prose round them into 「贏咗攻擊」.
C025 pins that round's own attack (207 against 172) and the 23 left without it, so the prose can
print the caveat with a badge rather than as an unpinned aside.

**C023 and C024 say what the night turned on, and they disagree with each other on purpose.**
pinglamb's attack per piece is higher in ALL TWELVE matches [C023], and he won seven of them. The
player with the higher attack TOTAL won ten [C024]; the two exceptions are m6 and m10, both
pinglamb's, both with yachi ahead on attack. On a night where the volume route covered the gap,
the per-piece measure picks the match winner seven times in twelve and the total picks it ten.

**NO C007 IS MINTED, and the id is left empty rather than reused**, following 09-10, 09-11 and
09-19. Order the twelve matches by pinglamb's per-piece advantage:

    m10 +1.94 P   m5 +2.41 Y   m12 +2.85 Y   m7 +6.66 Y   m8 +9.59 Y   m11 +9.85 P
    m6 +12.59 P   m3 +14.07 P  m1 +14.49 P   m9 +17.04 P  m4 +22.66 Y  m2 +27.95 P

Five yachi wins among twelve matches is 1/C(12,5) = 1 in 792, so a separation would have been
well-powered — and there is none: the smallest gap of the night is a pinglamb win (m10) and the
second-largest is a yachi win (m4). C023 pins those two ends, the evidence that no cut exists —
and pins them AS the ends, by cross-multiplied comparisons against every other match (`gap_lt`),
because a bound against a fixed percentage would leave 最細 and 第二大 unproved.

**BOTH REGIME GAPS ARE ABOVE THEIR COLUMN MEDIANS.**

    attack per piece   won rounds    yachi .6716   pinglamb .7537   ->  +12.23%
                       lost rounds   yachi .5599   pinglamb .6015   ->   +7.43%

C002 pins both to the hundredth. The ledger pins no rank: the columns range over sixteen sessions
and this ledger can see one.

**C003 is each player against himself**: yachi +19.94%, pinglamb +25.30%, pinglamb the wider.

**C006 is the death tally, 7 against 5** — twelve topouts in 102 rounds.

**C008 pins keypresses per piece, pooled: yachi 3.661 and pinglamb 3.624, yachi 1.01% above.**

**C010 is the night's shape.** Rounds 49-53 overall. The first three matches went 10-15 (all
pinglamb's), matches 4-8 went 23-19 (four of five yachi's), and after eight the rounds stood
33-34. Matches 9-11 went 11-15. The windows differ in size, so their order is pinned as
cross-multiplied rates, never by the raw counts.

The claims are of seven kinds:

  * **the shape of the night** — C001 pins all twelve match winners at once, C010 the windows.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality.
  * **each player against himself** — C003.
  * **the route and its price** — C005 and C009.
  * **the death tally** — C006.
  * **what decided the matches** — C023 (per piece, and the two ends that refuse a cut),
    C024 (totals) and C025 (the one round the session's attack lead leans on).
  * **the twelve matches, one each** — C011-C022 as `round_seq` runs, so no match card can
    describe a lead or a collapse that no lemma pins.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, rnd, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 12
# The windows C010 pins, as [lo, hi) match positions.
OPENING, MIDDLE, LATE = (0, 3), (3, 8), (8, 11)


def atk(pl):
    return sum_round(pl, "garbage_attack")


def pieces(pl):
    return sum_round(pl, "pieces")


def gap_x100(na, da, nb, db, v):
    """(na/da) / (nb/db) is exactly (100 + v/100)% to the hundredth, FLOORED — i.e.
    `(10000+v)·nb·da <= 10000·na·db < (10001+v)·nb·da`.

    The prose prints these gaps at two decimals, and a one-point band would leave both decimals
    unproved. Floored because every figure this repo prints is floored.
    """
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
    """How many of matches [lo_m, hi_m)'s rounds `pl` won, as a window sum over `alive`.

    `alive` is 1 for the round's survivor, and in first-to-death 1v1 the survivor is the
    winner. `count_rounds` has no window form, so a window's round wins are counted this way.
    """
    return eq(window(pl, "alive", lo_m, hi_m), lit(n))


def window_rate_lt(a, b):
    """yachi's round-win RATE over window `a` is below his rate over window `b`.

    The windows hold different numbers of rounds, so the counts are not comparable; the
    denominators are each window's own round count, read out of the data as the sum of both
    players' `alive`, not written as literals.
    """
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


def match_gap_under(mi, pct):
    """pinglamb's attack-per-piece advantage over match `mi` is under `pct - 100` percent."""
    return lt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1),
                                window(Y, "pieces", mi, mi + 1))),
              mul(lit(pct), mul(window(Y, "garbage_attack", mi, mi + 1),
                                window(P, "pieces", mi, mi + 1))))


def match_gap_over(mi, pct):
    """pinglamb's attack-per-piece advantage over match `mi` is over `pct - 100` percent."""
    return gt(mul(lit(100), mul(window(P, "garbage_attack", mi, mi + 1),
                                window(Y, "pieces", mi, mi + 1))),
              mul(lit(pct), mul(window(Y, "garbage_attack", mi, mi + 1),
                                window(P, "pieces", mi, mi + 1))))


def gap_lt(a, b):
    """pinglamb's attack-per-piece advantage over match `a` is strictly SMALLER than over match
    `b`, as the ratio (P_atk/P_pc)/(Y_atk/Y_pc) cross-multiplied:
    `P_atk(a)·Y_pc(a)·Y_atk(b)·P_pc(b) < P_atk(b)·Y_pc(b)·Y_atk(a)·P_pc(a)`.

    This is what lets a sentence say 最細 / 第二大 about a match's gap: `match_gap_under` and
    `match_gap_over` pin one match against a fixed percentage and say nothing about the others.
    """
    def w(pl, f, mi):
        return window(pl, f, mi, mi + 1)
    return lt(mul(mul(w(P, "garbage_attack", a), w(Y, "pieces", a)),
                  mul(w(Y, "garbage_attack", b), w(P, "pieces", b))),
              mul(mul(w(P, "garbage_attack", b), w(Y, "pieces", b)),
                  mul(w(Y, "garbage_attack", a), w(P, "pieces", a))))


def match_seq(mi, winners):
    """Pin a whole match's round order — the only way to state a lead later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PYPYYPPYP",   # m1   4-5   <- yachi led 3-2, levelled 4-4, lost the decider
    "YYPPPPP",     # m2   2-5   <- yachi won the first two, then lost five straight
    "YYPYPPYPP",   # m3   4-5   <- yachi led 3-1 and 4-3, lost the last two
    "PYPYYYPY",    # m4   5-3
    "PYYYPYPY",    # m5   5-3
    "PPPYYYPP",    # m6   3-5   <- pinglamb 3-0, yachi levelled 3-3, lost the last two
    "YYYPPPPYY",   # m7   5-4   <- yachi 3-0, pinglamb four straight to 3-4, yachi the last two
    "YYPPYYPPY",   # m8   5-4   <- pairs to 4-4, yachi the decider
    "PYPPYYYPP",   # m9   4-5   <- yachi from 1-3 to 4-3, lost the last two
    "YYPPPPYYP",   # m10  4-5   <- yachi 2-0, then 2-4, levelled 4-4, lost the decider
    "YPPYPPYP",    # m11  3-5
    "YYPPYPYPY",   # m12  5-4   <- level at 2, 3 and 4, yachi the decider
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (3, 4, 6, 7, 11)
# The two matches whose winner landed LESS attack than the loser, 0-based (m6, m10).
ATTACK_EXCEPTIONS = (5, 9)

MATCH_CANTO = [
    ("第一場 yachi 打到 3 比 2 領先，之後追平 4 比 4，最後一局俾人攞走，4 比 5",
     "match 1: yachi led 3-2, levelled at 4-4 and lost the last round, 4-5"),
    ("第二場 yachi 開波連贏兩局，之後五局全失，2 比 5",
     "match 2: yachi won the first two then lost five straight, 2-5"),
    ("第三場 yachi 先後 3 比 1、4 比 3 領先，尾兩局連失，4 比 5",
     "match 3: yachi led 3-1 and again 4-3, then lost the last two, 4-5"),
    ("第四場 yachi 1 比 2 落後，連贏三局反超，5 比 3",
     "match 4: yachi trailed 1-2, won three straight to go ahead and took it 5-3"),
    ("第五場 yachi 輸咗第一局，跟住連贏三局，5 比 3",
     "match 5: yachi lost the first round, won the next three and took it 5-3"),
    ("第六場 pinglamb 開波連贏三局，yachi 連贏三局追平 3 比 3，尾兩局連失，3 比 5",
     "match 6: pinglamb won the first three, yachi levelled at 3-3, then lost the last two, 3-5"),
    ("第七場 yachi 開波連贏三局，被連贏四局反超 3 比 4，尾兩局連贏，5 比 4",
     "match 7: yachi won the first three, lost four straight to trail 3-4, and won the last "
     "two, 5-4"),
    ("第八場兩局兩局咁交換，打到 4 比 4，yachi 贏最後一局，5 比 4",
     "match 8: traded in pairs to 4-4 and yachi won the last round, 5-4"),
    ("第九場 yachi 由 1 比 3 連贏三局反超 4 比 3，尾兩局連失，4 比 5",
     "match 9: yachi came back from 1-3 to lead 4-3, then lost the last two, 4-5"),
    ("第十場 yachi 2 比 0 領先，連失四局，再連贏兩局追平 4 比 4，最後一局俾人攞走，4 比 5",
     "match 10: yachi led 2-0, lost four straight, levelled at 4-4 and lost the last round, 4-5"),
    ("第十一場 yachi 贏咗第一、第四同第七局，3 比 5",
     "match 11: yachi took the first, fourth and seventh rounds, 3-5"),
    ("第十二場 2 比 2、3 比 3、4 比 4 三次打和，yachi 贏最後一局，5 比 4",
     "match 12: level at 2-2, 3-3 and 4-4, and yachi won the last round, 5-4"),
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
        "canto": "十二場 match 打成 5 比 7：yachi 攞到第四、第五、第七、第八同第十二場，"
                 "其餘七場俾 pinglamb 攞晒",
        "english_gloss": "pinglamb won the series seven matches to five: yachi won matches 4, "
                         "5, 7, 8 and 12",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 12.23%，"
                 "輸嗰啲局高 7.43%",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 12.23 percent "
                         "above yachi's, and in the rounds each lost it is 7.43 percent above",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 1223),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 743),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 19.94%，pinglamb 高 25.30%，今次闊啲嗰個係 pinglamb",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 19.94 percent and pinglamb by 25.30 "
                         "percent, pinglamb the wider",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1994),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 2530),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 11.52%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 11.52 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 1152),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 1064 粒方塊，總攻擊反而多過 pinglamb 58 條，"
                 "即係 pinglamb 總攻擊嘅 1.00%",
        "english_gloss": "yachi placed 1064 more pieces than pinglamb and landed 58 more lines "
                         "of attack, 1.00 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(1064)),
            eq(sub(atk(Y), atk(P)), lit(58)),
            ge_(mul(lit(10000), sub(atk(Y), atk(P))), mul(lit(100), atk(P))),
            lt(mul(lit(10000), sub(atk(Y), atk(P))), mul(lit(101), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 12 局頂到上天花板收場，7 局係 yachi 頂爆、5 局係 pinglamb",
        "english_gloss": "twelve rounds ended in a topout, seven of them yachi's and five "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(7)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(5)),
        ),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.661 下，pinglamb 3.624 下，"
                 "yachi 高 pinglamb 1.01%",
        "english_gloss": "keypresses per piece are near-identical: yachi 3.661 and pinglamb "
                         "3.624, yachi 1.01 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3661),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3624),
            gap_x100(sum_round(Y, "inputs"), pieces(Y), sum_round(P, "inputs"), pieces(P), 101),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 1064 粒方塊盈餘，即係多過 pinglamb 12.64%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 12.64 個百分點，而 C004 個窿係 11.52%，填得晒仲有剩",
        "english_gloss": "yachi's piece count is 12.64 percent above pinglamb's, more than the "
                         "11.52 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(11264), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(11265), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 49 比 53。頭三場 10 比 15；第四到第八場 23 比 19，係三段入面 yachi 比率最好嗰段；"
                 "打完八場係 33 比 34；第九到第十一場 11 比 15。幾段局數唔同（25、42、26 局），"
                 "所以要當比率比",
        "english_gloss": "the rounds finished 49 to 53; the first three matches went 10-15, "
                         "matches 4 to 8 went 23-19, the rounds stood 33-34 after eight "
                         "matches, and matches 9 to 11 went 11-15, so yachi's round-win rate was "
                         "higher in matches 4 to 8 than in matches 1 to 3 or 9 to 11",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 49),
            rounds_won_in(P, 0, MATCHES, 53),
            rounds_won_in(Y, *OPENING, 10), rounds_won_in(P, *OPENING, 15),
            rounds_won_in(Y, *MIDDLE, 23), rounds_won_in(P, *MIDDLE, 19),
            rounds_won_in(Y, 0, 8, 33), rounds_won_in(P, 0, 8, 34),
            rounds_won_in(Y, *LATE, 11), rounds_won_in(P, *LATE, 15),
            window_rate_lt(OPENING, MIDDLE), window_rate_lt(LATE, MIDDLE),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C023",
        "category": "style",
        "canto": "十二場逐場計，pinglamb 每粒方塊嘅攻擊場場都高過 yachi，但佢淨係贏咗七場。"
                 "排開都分唔到邊個贏：yachi 贏嘅第四場，pinglamb 每粒高過 22%，係十二場入面"
                 "差距第二大，嗰場 yachi 落多咗粒數；pinglamb 贏嘅第十場，佢每粒高唔夠 2%，"
                 "係十二場入面差距最細",
        "english_gloss": "pinglamb's attack per piece is higher in all twelve matches, yet he won "
                         "seven; in match 4, which yachi won, it is more than 22 percent higher, "
                         "the second-largest gap of the twelve, and yachi placed more pieces "
                         "there; in match 10, which pinglamb won, it is less than 2 percent "
                         "higher, the smallest gap of the twelve",
        "spec": conj(*[app_leads(mi, P) for mi in range(MATCHES)],
                     match_winner(3, Y), match_gap_over(3, 122),
                     match_winner(9, P), match_gap_under(9, 102),
                     # m10's gap is the smallest of the twelve ...
                     *[gap_lt(9, mi) for mi in range(MATCHES) if mi != 9],
                     # ... and m4's the second-largest: above every match but m2, below m2.
                     *[gap_lt(mi, 3) for mi in range(MATCHES) if mi not in (1, 3)],
                     gap_lt(3, 1),
                     # in m4 yachi also placed more pieces than pinglamb.
                     gt(window(Y, "pieces", 3, 4), window(P, "pieces", 3, 4))),
    },
    {
        "id": "C024",
        "category": "style",
        "canto": "逐場計總攻擊，打得多嗰個贏咗十場；兩個例外係第六同第十場，"
                 "yachi 攻擊多過對手但輸咗",
        "english_gloss": "in ten of the twelve matches the player who landed more attack won it; "
                         "the exceptions are matches 6 and 10, which pinglamb won with less "
                         "attack than yachi",
        "spec": conj(*[conj(match_winner(mi, Y if mi in YACHI_MATCHES else P),
                            attack_leads(mi, Y if (mi in YACHI_MATCHES
                                                   or mi in ATTACK_EXCEPTIONS) else P))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C025",
        "category": "style",
        "canto": "m7 第八局 yachi 打出 207 條攻擊、pinglamb 172 條，一局就差 35 條；"
                 "抽走呢局，全晚總攻擊 yachi 淨係多 23 條",
        "english_gloss": "in match 7 round 8 yachi landed 207 lines of attack and pinglamb 172, "
                         "35 apart; without that round yachi's session attack lead is 23",
        "spec": conj(
            eq(rnd(6, 7, Y, "garbage_attack"), lit(207)),
            eq(rnd(6, 7, P, "garbage_attack"), lit(172)),
            eq(sub(sub(atk(Y), atk(P)),
                   sub(rnd(6, 7, Y, "garbage_attack"), rnd(6, 7, P, "garbage_attack"))),
               lit(23)),
        ),
    },
]
