"""Hand-written narrative claims for 2026-07-22, as specs.

Ported from the `python_check`-only ledger this session shipped with. Until then these
27 claims and their 27 coaching siblings were proved by a session-local ~780-line
codegen_dafny.py that hardcoded every bound a SECOND time, independently of the ledger
— so a bound edited in one place and not the other left the verifier proving the old
number with 0 errors. Carrying a spec removes the second copy: one definition renders
to the Python predicate, the Dafny ensures and the SMT-LIB assertion.

Three renderings here are worth knowing about, because each is a different predicate
from the one it replaces even though both hold on this data:

* **a maximum is a conjunction.** `max(...) == v` becomes "nothing exceeds v" and
  "something attains v" (idioms.max_over_players). It deliberately does NOT name the
  round that attains it — the legacy emitter did, which proved more than the sentence.
* **`x // 1000 == 73` is `between(x, 73000, 74000)`.** Exactly equivalent for every
  integer, because Python's `//` floors and the algebra has no division.
* **a literal tautology becomes the bound it was meant to be.** The legacy emitter
  wrote conjuncts like `262000 <= 262582 && 262582 < 263000`, comparing literals. Here
  the same conjunct bounds the CONST (C010) — which the neighbouring `eq` already pins
  to that value, so the conjunction is unchanged as a predicate while no longer
  carrying a clause no mutation could ever kill.
"""
from pipeline.claims.idioms import (dur_max, dur_min, max_over_players, pp_count)
from pipeline.claims.spec import (add, all_rounds, between, c_and, c_field, c_winner,
                                  c_winner_gt_loser, conj, count_matches_won,
                                  count_rounds, count_rounds_window, count_rounds_won,
                                  dur, eq, le, lit, match_winner, nrounds, rnd,
                                  round_seq, round_winner, rounds_window, score, sub,
                                  sum_round, total_rounds)


Y, P = "yachi", "pinglamb"

ROUNDS = 79
MATCHES = 10
# Flat round position of each match's first and last+1 round. A streak crosses match
# boundaries, so the "longest run" claims are windows over this flat space, not over
# matches — see spec.rounds_window.
SPANS = [(0, 7), (7, 16), (16, 25), (25, 33), (33, 41),
         (41, 47), (47, 55), (55, 63), (63, 70), (70, 79)]


def mx(f, v):
    """The session maximum of f, over both players' rounds."""
    return max_over_players(Y, P, f, v)


def ppc(f, op, v):
    """How many player-rounds satisfy `f op v`."""
    return pp_count(Y, P, f, op, v)


def match_seq(mi, run):
    """Pin a whole match's round order; `run` is one character per round, Y or P."""
    return round_seq([(mi, ri) for ri in range(len(run))],
                     [Y if ch == "Y" else P for ch in run])


def no_run_longer_than(pl, k):
    """No k+1 consecutive rounds anywhere in the session went to pl.

    A window of k+1 rounds is all-pl exactly when it contains k+1 of them, so bounding
    every window's count at k says precisely "there is no run of k+1" — with no
    disjunction and no negation, which is why the algebra can state it at all.
    """
    return conj(*[le(count_rounds_window(c_winner(pl), s, s + k + 1), lit(k))
                  for s in range(ROUNDS - k)])


def no_run_longer_than_within_a_match(pl, k):
    """The same, but only over windows that lie inside a single match."""
    return conj(*[le(count_rounds_window(c_winner(pl), s, s + k + 1), lit(k))
                  for lo, hi in SPANS for s in range(lo, hi - k)])


CLAIMS = [
    {
        "id": 'C001',
        "category": 'score',
        "canto": 'yachi 十場打咗六場，pinglamb 執四場',
        "english_gloss": 'yachi won 6 matches, pinglamb won 4 (of 10)',
        "spec": conj(eq(count_matches_won(Y), lit(6)), eq(count_matches_won(P), lit(4))),
    },
    {
        "id": 'C002',
        "category": 'score',
        "canto": '成個 series 打足 79 局，yachi 贏 43 局、pinglamb 贏 36 局，局數其實好貼',
        "english_gloss": '79 rounds total; yachi won 43 rounds, pinglamb 36',
        "spec": conj(eq(total_rounds(), lit(ROUNDS)),
                 eq(count_rounds_won(Y), lit(43)), eq(count_rounds_won(P), lit(36))),
    },
    {
        "id": 'C003',
        "category": 'clutch',
        "canto": '有三場打到 5-4 先分勝負：第2、第3場 pinglamb 執，第10場 yachi 執',
        "english_gloss": 'three matches went to a 5-4 decider: m2 & m3 to pinglamb, m10 to yachi',
        "spec": conj(*[c for mi, sy, sp, w in [(1, 4, 5, P), (2, 4, 5, P), (9, 5, 4, Y)]
                  for c in (eq(score(mi, Y), lit(sy)), eq(score(mi, P), lit(sp)),
                            match_winner(mi, w))]),
    },
    {
        "id": 'C004',
        "category": 'comeback',
        "canto": '決勝第10場 yachi 一度 2-4 落後、俾人拎住 match point，跟住連贏最後三局翻盤 5-4 封 series',
        "english_gloss": 'in m10 yachi was down 2-4 (facing match point) then won the last 3 rounds to take it 5-4',
        "spec": conj(eq(nrounds(9), lit(9)), match_seq(9, "YPYPPPYYY")),
    },
    {
        "id": 'C005',
        "category": 'clutch',
        "canto": '第10場最尾一局 yachi 打到 vs 約135.0、pinglamb 得約93.9，APM 約73 對約43，一面倒收工',
        "english_gloss": 'm10 final round: yachi vs≈135.0 vs pinglamb≈93.9, apm 73 vs 43',
        "spec": conj(between(rnd(9, 8, Y, "vs_x1000"), 135000, 136000),
                 between(rnd(9, 8, P, "vs_x1000"), 93000, 94000),
                 round_winner(9, 8, Y),
                 between(rnd(9, 8, Y, "apm_x1000"), 73000, 74000),
                 between(rnd(9, 8, P, "apm_x1000"), 43000, 44000)),
    },
    {
        "id": 'C006',
        "category": 'duration',
        "canto": '成個 session 最長嗰局係第2場第3局，打足約228秒（三分四十八秒，差唔多四分鐘），最後 yachi 生還',
        "english_gloss": 'longest round of the session is m2r2 (~228s, ~3.8min), won by yachi',
        "spec": conj(dur_max(228310), between(dur(1, 2), 228000, 229000), round_winner(1, 2, Y)),
    },
    {
        "id": 'C007',
        "category": 'comeback',
        "canto": '呢局係場落樓大戰：yachi 一路食多過對手嘅垃圾（真係食咗127行、pinglamb 得109行）都照贏，仲清咗204行',
        "english_gloss": 'in that marathon yachi won despite receiving more real garbage (127) than pinglamb (109), and cleared 204 lines',
        "spec": conj(eq(rnd(1, 2, Y, "garbagereceived"), lit(127)),
                 eq(rnd(1, 2, P, "garbagereceived"), lit(109)),
                 eq(rnd(1, 2, Y, "lines"), lit(204)), round_winner(1, 2, Y)),
    },
    {
        "id": 'C008',
        "category": 'duration',
        "canto": '最快嗰局係第6場第2局，約15秒就收咗工，yachi APM 爆到約91.7、pinglamb 得約24.3',
        "english_gloss": 'shortest round is m6r1 (~15s); yachi apm≈91.7 vs pinglamb≈24.3',
        "spec": conj(dur_min(15054), round_winner(5, 1, Y),
                 between(rnd(5, 1, Y, "apm_x1000"), 91000, 92000),
                 between(rnd(5, 1, P, "apm_x1000"), 24000, 25000)),
    },
    {
        "id": 'C009',
        "category": 'spike',
        "canto": '全場火力最集中嗰局係第7場第2局：pinglamb APM 爆到約114.2、PPS 約1.83、vs 約262.5，約15秒閃電殺（呢啲係速率，15 秒嘅分母做唔到速率紀錄）',
        "english_gloss": 'highest-intensity round is m7r1: pinglamb apm≈114.2, pps≈1.83, vs≈262.5, a ~15s blitz',
        "spec": conj(mx("apm_x1000", 114223), eq(rnd(6, 1, P, "apm_x1000"), lit(114223)),
                 eq(rnd(6, 1, P, "pps_x1000"), lit(1838)), round_winner(6, 1, P),
                 between(dur(6, 1), 15000, 16000)),
    },
    {
        "id": 'C010',
        "category": 'spike',
        "canto": '嗰局 pinglamb 嘅 vs 約262.5，係成個 session 冇設限之下單局最高嘅 vs score；不過只計打足一分鐘嘅局，紀錄就唔係佢',
        "english_gloss": "pinglamb's vs≈262.5 in m7r1 is the highest single-round vs of the session",
        "spec": conj(mx("vs_x1000", 262582), eq(rnd(6, 1, P, "vs_x1000"), lit(262582)),
                 between(rnd(6, 1, P, "vs_x1000"), 262000, 263000)),
    },
    {
        "id": 'C011',
        "category": 'clutch',
        "canto": '第2場嘅決勝局 pinglamb 頂住約128.5秒嘅拉鋸，清咗121行、APM 約60.3 執咗場波',
        "english_gloss": 'm2 decider: pinglamb won a ~128.5s round, 121 lines, apm≈60.3',
        "spec": conj(round_winner(1, 8, P), between(rnd(1, 8, P, "lifetime"), 128000, 129000),
                 eq(rnd(1, 8, P, "lines"), lit(121)),
                 between(rnd(1, 8, P, "apm_x1000"), 60000, 61000)),
    },
    {
        "id": 'C012',
        "category": 'clutch',
        "canto": '第3場決勝局 pinglamb 用約30.4秒、APM 約74.0、vs 約150.0 快刀斬亂麻',
        "english_gloss": 'm3 decider: pinglamb won in ~30.4s with apm≈74.0, vs≈150.0',
        "spec": conj(round_winner(2, 8, P), between(rnd(2, 8, P, "lifetime"), 30000, 31000),
                 between(rnd(2, 8, P, "apm_x1000"), 74000, 75000),
                 between(rnd(2, 8, P, "vs_x1000"), 150000, 151000)),
    },
    {
        "id": 'C013',
        "category": 'spike',
        "canto": '全場最大單發 spike 係16，呢個數兩邊都掂過（全場出現咗三次），yachi 喺第4場第3局劈嗰一嘢16仲順手贏埋嗰局',
        "english_gloss": "biggest single spike of the session is 16 (reached 3 times, by both players); yachi's came in m4r2 and he won that round",
        "spec": conj(mx("maxspike", 16), eq(ppc("maxspike", "==", 16), lit(3)),
                 eq(rnd(3, 2, Y, "maxspike"), lit(16)), round_winner(3, 2, Y)),
    },
    {
        "id": 'C014',
        "category": 'score',
        "canto": '打得最一面倒嗰場係第6場，yachi 5-1 冚咗 pinglamb',
        "english_gloss": 'most one-sided match is m6, yachi 5-1',
        "spec": conj(*[c for mi in range(MATCHES)
                  for c in (le(sub(score(mi, Y), score(mi, P)), lit(4)),
                            le(sub(score(mi, P), score(mi, Y)), lit(4)))],
                 eq(score(5, Y), lit(5)), eq(score(5, P), lit(1))),
    },
    {
        "id": 'C015',
        "category": 'style',
        "canto": '全場79局，每一局贏嗰個 vs score 都高過輸嗰個——vs 就係命，冇一局例外',
        "english_gloss": 'in all 79 rounds the winner had a higher vs than the loser (0 exceptions)',
        "spec": all_rounds(c_winner_gt_loser("vs_x1000")),
    },
    {
        "id": 'C016',
        "category": 'comeback',
        "canto": '有8局係贏家真係食多過對手嘅垃圾行都照樣翻盤',
        "english_gloss": '8 rounds were won by the player who received more real garbage than the loser',
        "spec": eq(count_rounds(c_winner_gt_loser("garbagereceived")), lit(8)),
    },
    {
        "id": 'C017',
        "category": 'clutch',
        "canto": '打得最乾淨嗰局係第1場第3局：pinglamb 全局淨係食咗1行垃圾（全場贏家最少），仲把 yachi 嘅 APM 壓到約5.3、vs 約8.9',
        "english_gloss": 'cleanest kill is m1r2: pinglamb conceded only 1 line (session-min for a winner), holding yachi to apm≈5.3, vs≈8.9',
        "spec": conj(eq(add(count_rounds(c_and(c_winner(Y), c_field(Y, "garbagereceived", "<", 1))),
                     count_rounds(c_and(c_winner(P), c_field(P, "garbagereceived", "<", 1)))),
                 lit(0)),
                 eq(rnd(0, 2, P, "garbagereceived"), lit(1)), round_winner(0, 2, P),
                 between(rnd(0, 2, Y, "apm_x1000"), 5000, 6000),
                 between(rnd(0, 2, Y, "vs_x1000"), 8000, 9000)),
    },
    {
        "id": 'C018',
        "category": 'style',
        "canto": '單局最多 T-spin 係第2場第8局 pinglamb 嘅21個，佢就係靠啲 T-spin 攞低咗嗰局約200.5秒嘅馬拉松',
        "english_gloss": 'most tspins in a round is 21 by pinglamb in m2r7, winning a ~200.5s marathon',
        "spec": conj(mx("tspins", 21), eq(rnd(1, 7, P, "tspins"), lit(21)),
                 round_winner(1, 7, P),
                 between(rnd(1, 7, P, "lifetime"), 200000, 201000)),
    },
    {
        "id": 'C019',
        "category": 'style',
        "canto": '最長 back-to-back 鏈係第9場第6局 pinglamb 嘅10連 B2B',
        "english_gloss": 'longest back-to-back streak is 10 by pinglamb in m9r5',
        "spec": conj(mx("topbtb", 10), eq(rnd(8, 5, P, "topbtb"), lit(10))),
    },
    {
        "id": 'C020',
        "category": 'style',
        "canto": '成個 series 兩人夾埋出咗19次 Perfect Clear（All Clear）',
        "english_gloss": '19 all-clears (perfect clears) were made across the whole series',
        "spec": eq(add(sum_round(Y, "clears.allclear"), sum_round(P, "clears.allclear")),
               lit(19)),
    },
    {
        "id": 'C021',
        "category": 'clutch',
        "canto": '跨場計 yachi 最多可以連贏五局（全場最長，pinglamb 最多得三局），不過單場之內佢最多連贏四局（第1場中段）。兩條五連勝：第5場尾駁第6場頭嗰條五局全部係贏波局；另一條第1場尾駁到第2場頭，但要留意第2場嗰個開局其實係 yachi 之後輸咗場（4-5）嘅頭一局',
        "english_gloss": "yachi's longest cross-match round-win streak is 5 (session max; pinglamb's is 3); within a single match his max is 4. Of the two 5-streaks, m5r6-m6r2 are all wins in won territory, while m1r3-m2r0 bridges into m2 which yachi lost 4-5",
        "spec": conj(
        # yachi's two runs of five, the ten rounds the sentence itself names ...
        round_seq([(0, 3), (0, 4), (0, 5), (0, 6), (1, 0)], [Y] * 5),
        round_seq([(4, 6), (4, 7), (5, 0), (5, 1), (5, 2)], [Y] * 5),
        no_run_longer_than(Y, 5),
        # ... pinglamb's longest is three. The sentence does not name WHICH three, so
        # naming them here proves slightly more than it says; that is deliberate and
        # recorded, and it is the price of an algebra with no disjunction.
        round_seq([(3, 3), (3, 4), (3, 5)], [P] * 3),
        no_run_longer_than(P, 3),
        # inside a single match yachi never got past four — the witness is the first
        # four of the run above, so no extra rounds are pinned for this leg
        no_run_longer_than_within_a_match(Y, 4),
        match_winner(1, P)),
    },
    {
        "id": 'C022',
        "category": 'comeback',
        "canto": '第1場 yachi 一度 1-2 落後，之後連贏最後四局反超 5-2 收爐',
        "english_gloss": 'in m1 yachi trailed 1-2 then won the last 4 rounds to close 5-2',
        "spec": conj(eq(nrounds(0), lit(7)), match_seq(0, "PYPYYYY"),
                 eq(score(0, Y), lit(5)), eq(score(0, P), lit(2))),
    },
    {
        "id": 'C023',
        "category": 'duration',
        "canto": '第2場第3局嗰場落樓大戰，yachi 一局清咗204行，係全場單局最多',
        "english_gloss": 'yachi cleared 204 lines in m2r2, the most lines in any single round of the session',
        "spec": conj(mx("lines", 204), eq(rnd(1, 2, Y, "lines"), lit(204))),
    },
    {
        "id": 'C024',
        "category": 'spike',
        "canto": '第3場入面 yachi 喺第6局 vs 爆到約201.9，係佢嗰場單局最高嘅 vs',
        "english_gloss": "in m3, yachi's vs≈201.9 in round 6 (idx5) is the highest single-round vs of that match",
        "spec": conj(between(rnd(2, 5, Y, "vs_x1000"), 201000, 202000),
                 *[le(rnd(2, ri, pl, "vs_x1000"), rnd(2, 5, Y, "vs_x1000"))
                   for ri in range(9) for pl in (Y, P)]),
    },
    {
        "id": 'C025',
        "category": 'score',
        "canto": '第4場 yachi 先贏頭三局、pinglamb 追返三局打成 3-3，最後 yachi 贏埋尾兩局 5-3 收',
        "english_gloss": 'in m4 yachi won the first 3, pinglamb answered with 3 to tie 3-3, then yachi took the last 2 to close 5-3',
        "spec": conj(eq(nrounds(3), lit(8)), match_seq(3, "YYYPPPYY"),
                 eq(score(3, Y), lit(5)), eq(score(3, P), lit(3))),
    },
    {
        "id": 'C026',
        "category": 'score',
        "canto": '十場嘅最終比數順序係 5-2、4-5、4-5、5-3、5-3、5-1、3-5、5-3、2-5、5-4（yachi 對 pinglamb）',
        "english_gloss": 'the 10 match final scores in order (yachi-pinglamb): 5-2, 4-5, 4-5, 5-3, 5-3, 5-1, 3-5, 5-3, 2-5, 5-4',
        "spec": conj(*[c for mi, (sy, sp) in enumerate(
                     [(5, 2), (4, 5), (4, 5), (5, 3), (5, 3),
                      (5, 1), (3, 5), (5, 3), (2, 5), (5, 4)])
                  for c in (eq(score(mi, Y), lit(sy)), eq(score(mi, P), lit(sp)))]),
    },
    {
        "id": 'C027',
        "category": 'comeback',
        "canto": '嗰8局翻盤局（贏家食多過對手垃圾都照贏），yachi 佔咗其中6局、pinglamb 佔2局',
        "english_gloss": 'of the 8 comeback rounds (winner received more garbage yet won), yachi took 6 and pinglamb 2',
        "spec": conj(eq(count_rounds(c_and(c_winner(Y), c_winner_gt_loser("garbagereceived"))),
                    lit(6)),
                 eq(count_rounds(c_and(c_winner(P), c_winner_gt_loser("garbagereceived"))),
                    lit(2))),
    },
]
