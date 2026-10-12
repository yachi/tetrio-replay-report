"""Hand-written claims for 2026-10-12 — what a generator cannot say about this night.

**Eight matches and 55 rounds, pinglamb 5-3 in matches and 30-25 in rounds.** The seventeenth
session in date order and in arrival. No match went to a ninth round — 09-11 is the only other
session with none — and both players were shut out once: pinglamb 5-0 in m1, yachi 5-0 in m3
[G012]. After three matches yachi led the series 2-1 and the rounds 10-7 [C010], having won
nine rounds in a row across m2 and m3 [G013]. pinglamb then took m4, m5 and m6, 15-7 in rounds,
and that stretch is the whole margin: the last two matches split 1-1 and 8-8.

**C007 IS MINTED.** Order the eight matches by pinglamb's attack-per-piece advantage:

    m3 -28.02 Y   m7 +3.13 Y   m2 +4.54 Y   |   m5 +11.97 P   m4 +15.34 P   m6 +20.12 P
    m8 +29.45 P   m1 +30.99 P

yachi's three wins are the three smallest gaps, pinglamb's five the five largest, and the void
the cut falls into runs from +4.54 to +11.97. Three wins among eight fall that way by chance
with probability 1/C(8,3) = 1 in 56 — between 09-17's 1 in 21 and 08-19's 1 in 120, so this is
the intermediate tier and the prose states the 1-in-56 beside it. The claim pins the SIZE of
the gap on each side of the cut (under +5% in each yachi win, over +11% in each pinglamb win),
not who leads, because who leads fails twice:

**C019 pins the sign and the totals.** pinglamb's attack per piece is the higher in seven of the
eight matches; the eighth is m3, where yachi's is more than 38% above his [C020]. So in m2 and
m7 yachi won with the LOWER attack per piece — and in both he placed more pieces and landed
more attack. The player with more attack won all eight matches [C019].

**THE REGIMES ARE THE 07-22 SHAPE: CEILINGS CLOSE, FLOORS APART.**

    attack per piece   won rounds    yachi .6814   pinglamb .7301   ->   +7.14%
                       lost rounds   yachi .5402   pinglamb .6237   ->  +15.44%

C002 pins both to the hundredth (floored). The ledger pins no rank: the columns range over
seventeen sessions and this ledger can see one. `check_loo` puts both under THRESHOLD (won-gap
0.318 dropping m5r7, lost-gap 0.156 dropping m8r5), so neither needs an annotation.

**C003 is each player against himself**: yachi +26.11%, pinglamb +17.05%, yachi the wider.

**C004/C005/C009 are the volume route for the thirteenth time.** C004's session gap is +13.50%.
yachi threw 468 more pieces, 9.92% more than pinglamb [C009], and landed 102 fewer lines of
attack, 3.15% of pinglamb's total [C005]. The surplus buys back 9.92 points of a 13.50-point gap,
a shortfall near 3.58.

**C006 is the death tally, 4 against 4** — eight topouts in 55 rounds.

**C008 pins keypresses per piece, pooled: yachi 3.591 and pinglamb 3.683, pinglamb 2.54% above.**

**C010 is the night's shape.** Rounds 25-30 overall. The first three matches went 10-7 (two of
three yachi's), matches 4-6 went 7-15 (all pinglamb's), matches 7-8 went 8-8. The windows differ
in size, so their order is pinned as cross-multiplied rates, never by the raw counts.

The claims are of seven kinds:

  * **the shape of the night** — C001 pins all eight match winners at once, C010 the windows.
  * **the two regimes** — C002 and C004, every rate cross-multiplied into an integer inequality.
  * **each player against himself** — C003.
  * **the route and its price** — C005 and C009.
  * **the death tally** — C006.
  * **the per-match ordering** — C007 (size), C019 (sign and totals) and C020 (m3).
  * **the eight matches, one each** — C011-C018 as `round_seq` runs, so no match card can
    describe a lead or a collapse that no lemma pins.
"""
from pipeline.claims.spec import (add, c_str, c_winner, conj, count_rounds, eq, ge_, gt,
                                  lit, lt, match_winner, mul, round_seq, sub,
                                  sum_round, sum_round_range, sum_round_where)

Y, P = "yachi", "pinglamb"

MATCHES = 8
# The windows C010 pins, as [lo, hi) match positions.
OPENING, MIDDLE, LATE = (0, 3), (3, 6), (6, 8)


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


def pieces_lead(mi, leader):
    """`leader` placed strictly more pieces than the other over match `mi`."""
    other = P if leader == Y else Y
    return gt(window(leader, "pieces", mi, mi + 1), window(other, "pieces", mi, mi + 1))


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


def match_seq(mi, winners):
    """Pin a whole match's round order — the only way to state a lead later given back."""
    return round_seq([(mi, ri) for ri in range(len(winners))], winners)


# Round winners in order, one string per match, 0-based match index. `Y` is yachi.
RUNS = [
    "PPPPP",       # m1   0-5   <- shut out
    "YPPYYYY",     # m2   5-2   <- trailed 1-2, won the last four
    "YYYYY",       # m3   5-0   <- shut out the other way
    "PYPPPP",      # m4   1-5   <- level at 1-1, then four straight to pinglamb
    "PPPYPYYP",    # m5   3-5   <- 0-3 and 1-4 down, pulled back to 3-4, lost the next
    "YYYPPPPP",    # m6   3-5   <- yachi 3-0, then five straight to pinglamb
    "YYYPYPPY",    # m7   5-3   <- yachi 3-0 and 4-1, pinglamb to 4-3, yachi closed it
    "PYYPYPPP",    # m8   3-5   <- yachi led 3-2, lost the last three
]

# The matches yachi won, 0-based.
YACHI_MATCHES = (1, 2, 6)
# The one match in which yachi's attack per piece is the higher, 0-based (m3).
SIGN_EXCEPTION = 2

MATCH_CANTO = [
    ("第一場 pinglamb 五局全贏，5 比 0",
     "match 1: pinglamb won all five rounds, 5-0"),
    ("第二場 yachi 贏咗第一局之後 1 比 2 落後，尾四局連贏，5 比 2",
     "match 2: yachi won the first round, trailed 1-2, then won the last four, 5-2"),
    ("第三場 yachi 五局全贏，5 比 0",
     "match 3: yachi won all five rounds, 5-0"),
    ("第四場打到 1 比 1，之後 pinglamb 連贏四局，1 比 5",
     "match 4: level at 1-1, then pinglamb won four straight, 1-5"),
    ("第五場 yachi 0 比 3、1 比 4 落後，追到 3 比 4，最後一局輸，3 比 5",
     "match 5: yachi trailed 0-3 and 1-4, pulled back to 3-4 and lost the next round, 3-5"),
    ("第六場 yachi 開波連贏三局，之後五局全失，3 比 5",
     "match 6: yachi won the first three rounds, then lost five straight, 3-5"),
    ("第七場 yachi 3 比 0、4 比 1 領先，被追到 4 比 3，最後一局贏返，5 比 3",
     "match 7: yachi led 3-0 and 4-1, was pulled back to 4-3 and won the next round, 5-3"),
    ("第八場 yachi 3 比 2 領先，尾三局連失，3 比 5",
     "match 8: yachi led 3-2, then lost the last three rounds, 3-5"),
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
        "canto": "八場 match 打成 3 比 5：yachi 攞到第二、第三同第七場，其餘五場俾 pinglamb 攞晒",
        "english_gloss": "pinglamb won the series five matches to three: yachi won matches 2, 3 "
                         "and 7",
        "spec": conj(*[match_winner(mi, Y if mi in YACHI_MATCHES else P)
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C002",
        "category": "style",
        "canto": "拆開贏同輸嘅局嚟睇：贏嗰啲局 pinglamb 每粒方塊嘅攻擊高 7.14%，"
                 "輸嗰啲局高 15.44%",
        "english_gloss": "in the rounds each won pinglamb's attack per piece is 7.14 percent "
                         "above yachi's, and in the rounds each lost it is 15.44 percent above",
        "spec": conj(
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     won(Y, "garbage_attack"), won(Y, "pieces"), 714),
            gap_x100(lost(P, "garbage_attack"), lost(P, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 1544),
        ),
    },
    {
        "id": "C003",
        "category": "style",
        "canto": "喺一個人自己身上講：兩個人贏嗰啲局每粒方塊嘅攻擊都高過自己輸嗰啲局——"
                 "yachi 高 26.11%，pinglamb 高 17.05%，今次闊啲嗰個係 yachi",
        "english_gloss": "each player's attack per piece is higher in the rounds he won than in "
                         "the rounds he lost — yachi by 26.11 percent and pinglamb by 17.05 "
                         "percent, yachi the wider",
        "spec": conj(
            gap_x100(won(Y, "garbage_attack"), won(Y, "pieces"),
                     lost(Y, "garbage_attack"), lost(Y, "pieces"), 2611),
            gap_x100(won(P, "garbage_attack"), won(P, "pieces"),
                     lost(P, "garbage_attack"), lost(P, "pieces"), 1705),
        ),
    },
    {
        "id": "C004",
        "category": "style",
        "canto": "成晚夾埋計，pinglamb 每粒方塊嘅攻擊高過 yachi 13.50%",
        "english_gloss": "over the whole session pinglamb's attack per piece is 13.50 percent "
                         "above yachi's",
        "spec": gap_x100(atk(P), pieces(P), atk(Y), pieces(Y), 1350),
    },
    {
        "id": "C005",
        "category": "style",
        "canto": "yachi 全晚多疊咗 468 粒方塊，總攻擊仍然少過 pinglamb 102 條，"
                 "即係 pinglamb 總攻擊嘅 3.15%",
        "english_gloss": "yachi placed 468 more pieces than pinglamb and still landed 102 fewer "
                         "lines of attack, 3.15 percent of pinglamb's total",
        "spec": conj(
            eq(sub(pieces(Y), pieces(P)), lit(468)),
            eq(sub(atk(P), atk(Y)), lit(102)),
            ge_(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(315), atk(P))),
            lt(mul(lit(10000), sub(atk(P), atk(Y))), mul(lit(316), atk(P))),
        ),
    },
    {
        "id": "C006",
        "category": "style",
        "canto": "全晚 8 局頂到上天花板收場，yachi 同 pinglamb 各佔 4 局",
        "english_gloss": "eight rounds ended in a topout, four of them yachi's and four "
                         "pinglamb's",
        "spec": conj(
            eq(count_rounds(c_str(Y, "gameoverreason", "topout")), lit(4)),
            eq(count_rounds(c_str(P, "gameoverreason", "topout")), lit(4)),
        ),
    },
    {
        "id": "C007",
        "category": "style",
        "canto": "八場 match 排開，個效率差距同邊個贏場波分得開：yachi 贏嗰三場，"
                 "pinglamb 每粒方塊嘅攻擊高唔夠 5%；pinglamb 贏嗰五場，佢每場都高過 11%，"
                 "中間一場都冇",
        "english_gloss": "in each of the three matches yachi won, pinglamb's attack per piece is "
                         "less than 5 percent above yachi's; in each of the five matches "
                         "pinglamb won it is more than 11 percent above",
        "spec": conj(*[(match_gap_under(mi, 105) if mi in YACHI_MATCHES
                        else match_gap_over(mi, 111))
                       for mi in range(MATCHES)]),
    },
    {
        "id": "C008",
        "category": "style",
        "canto": "每粒方塊要按幾多下（KPP）兩個人差唔多：yachi 3.591 下，pinglamb 3.683 下，"
                 "pinglamb 高 yachi 2.54%",
        "english_gloss": "keypresses per piece are close: yachi 3.591 and pinglamb 3.683, "
                         "pinglamb 2.54 percent the higher",
        "spec": conj(
            rate_x1000(sum_round(Y, "inputs"), pieces(Y), 3591),
            rate_x1000(sum_round(P, "inputs"), pieces(P), 3683),
            gap_x100(sum_round(P, "inputs"), pieces(P), sum_round(Y, "inputs"), pieces(Y), 254),
        ),
    },
    {
        "id": "C009",
        "category": "style",
        "canto": "yachi 嗰 468 粒方塊盈餘，即係多過 pinglamb 9.92%——換返做每粒方塊嘅攻擊，"
                 "呢條路最多可以填返 9.92 個百分點，而 C004 個窿係 13.50%，填唔晒",
        "english_gloss": "yachi's piece count is 9.92 percent above pinglamb's, less than the "
                         "13.50 percent attack-per-piece gap C004 pins",
        "spec": conj(
            ge_(mul(lit(10000), pieces(Y)), mul(lit(10992), pieces(P))),
            lt(mul(lit(10000), pieces(Y)), mul(lit(10993), pieces(P))),
        ),
    },
    {
        "id": "C010",
        "category": "score",
        "canto": "逐局計 25 比 30。頭三場 10 比 7，打完三場 yachi 2 比 1 領先；第四到第六場 7 比 15，"
                 "三場都係 pinglamb，係三段入面 yachi 比率最差嗰段；第七、第八場 8 比 8。"
                 "幾段局數唔同（17、22、16 局），所以要當比率比",
        "english_gloss": "the rounds finished 25 to 30; the first three matches went 10-7, "
                         "matches 4 to 6 went 7-15, and matches 7 and 8 went 8-8, so yachi's "
                         "round-win rate was lower in matches 4 to 6 than in matches 1 to 3 or "
                         "7 to 8",
        "spec": conj(
            rounds_won_in(Y, 0, MATCHES, 25),
            rounds_won_in(P, 0, MATCHES, 30),
            rounds_won_in(Y, *OPENING, 10), rounds_won_in(P, *OPENING, 7),
            rounds_won_in(Y, *MIDDLE, 7), rounds_won_in(P, *MIDDLE, 15),
            rounds_won_in(Y, *LATE, 8), rounds_won_in(P, *LATE, 8),
            window_rate_lt(MIDDLE, OPENING), window_rate_lt(MIDDLE, LATE),
        ),
    },
] + _seq_claims() + [
    {
        "id": "C019",
        "category": "style",
        "canto": "逐場計總攻擊，打得多嗰個八場全贏。第二同第七場 pinglamb 每粒方塊嘅攻擊高啲，"
                 "但 yachi 落多咗粒數、總攻擊多過對手，兩場都係 yachi 贏",
        "english_gloss": "in all eight matches the player who landed more attack won it; in "
                         "matches 2 and 7 pinglamb's attack per piece was the higher, but yachi "
                         "placed more pieces, landed more attack and won both",
        "spec": conj(*[conj(match_winner(mi, Y if mi in YACHI_MATCHES else P),
                            attack_leads(mi, Y if mi in YACHI_MATCHES else P))
                       for mi in range(MATCHES)],
                     *[conj(app_leads(mi, P), pieces_lead(mi, Y)) for mi in (1, 6)]),
    },
    {
        "id": "C020",
        "category": "style",
        "canto": "八場入面，淨係第三場 yachi 每粒方塊嘅攻擊高過 pinglamb，而且高過 38%；"
                 "其餘七場都係 pinglamb 高",
        "english_gloss": "only in match 3 is yachi's attack per piece the higher, by more than "
                         "38 percent; in the other seven matches pinglamb's is the higher",
        "spec": conj(
            gt(mul(lit(100), mul(window(Y, "garbage_attack", 2, 3), window(P, "pieces", 2, 3))),
               mul(lit(138), mul(window(P, "garbage_attack", 2, 3), window(Y, "pieces", 2, 3)))),
            *[app_leads(mi, P) for mi in range(MATCHES) if mi != SIGN_EXCEPTION],
        ),
    },
]
