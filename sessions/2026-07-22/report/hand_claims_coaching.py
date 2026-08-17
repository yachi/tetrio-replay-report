"""Hand-written coaching claims for 2026-07-22, as specs.

The sibling of hand_claims_narrative.py; see that module's docstring for the three
rendering patterns both files use (a maximum as a conjunction, floor division as a
`between`, and a literal tautology replaced by the bound it was meant to be).

Two claims here are the only ones in either session that needed machinery the algebra
did not have, and both are noted at their entry: R003's winner-relative match score,
and R023's count over ADJACENT rounds. R021 carries the corpus's only boolean datum.

R001 states the same predicate as the narrative ledger's C001. That is not a
duplicate to be removed: the two ledgers are separate documents with separate
audiences, and build_hand's duplicate check is per-ledger for exactly that reason.
"""
from pipeline.claims.idioms import (max_for, max_over_players, pp_count)
from pipeline.claims.spec import (between, c_field, c_winner, conj, count_matches_won,
                                  count_round_pairs, count_rounds, count_rounds_window,
                                  count_rounds_won, eq, gt, le, lit, lt, match_winner,
                                  mul, nmatches, nrounds, rnd, round_seq, round_winner,
                                  rounds_window, score, score_of_winner, sub, sum_ge,
                                  sum_round, sum_sq_round, total_rounds)


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
        "id": 'R001',
        "category": 'score',
        "canto": 'yachi 十場入面贏咗六場,pinglamb 贏四場',
        "english_gloss": 'yachi won 6 of 10 matches, pinglamb 4',
        "spec": conj(eq(count_matches_won(Y), lit(6)), eq(count_matches_won(P), lit(4))),
    },
    {
        "id": 'R002',
        "category": 'score',
        "canto": '分開一局局計,yachi 贏咗 43 局,pinglamb 贏 36 局',
        "english_gloss": 'round wins: yachi 43, pinglamb 36',
        "spec": conj(eq(count_rounds_won(Y), lit(43)), eq(count_rounds_won(P), lit(36))),
    },
    {
        "id": 'R003',
        "category": 'duration',
        "canto": '成個 series 打足 79 局,十場都係先贏五局嗰個贏',
        "english_gloss": '79 rounds total across 10 matches, every match won by first to 5 round-wins',
        "spec": conj(eq(nmatches(), lit(MATCHES)), eq(total_rounds(), lit(ROUNDS)),
                 *[eq(score_of_winner(mi), lit(5)) for mi in range(MATCHES)]),
    },
    {
        "id": 'R004',
        "category": 'pace',
        "canto": 'yachi 手快啲,全 series 落咗 7546 粒,多過 pinglamb 嘅 6971 粒',
        "english_gloss": 'yachi placed more pieces overall (7546 vs 6971)',
        "spec": conj(eq(sum_round(Y, "pieces"), lit(7546)),
                 eq(sum_round(P, "pieces"), lit(6971))),
    },
    {
        "id": 'R005',
        "category": 'pace',
        "canto": 'yachi 平均 PPS 約 1.43,快過 pinglamb 約 1.34',
        "english_gloss": 'yachi mean PPS ~1.43 > pinglamb ~1.34',
        "spec": conj(between(sum_round(Y, "pps_x1000"), 1435 * ROUNDS, 1436 * ROUNDS),
                 between(sum_round(P, "pps_x1000"), 1342 * ROUNDS, 1343 * ROUNDS)),
    },
    {
        "id": 'R006',
        "category": 'attack',
        "canto": '逐局 APM 打成平手,pinglamb 每局平均 APM 淨係叻 yachi 少少',
        "english_gloss": 'per-round APM essentially tied, pinglamb marginally higher per-round average',
        "spec": conj(gt(sub(sum_round(P, "apm_x1000"), sum_round(Y, "apm_x1000")), lit(0)),
                 lt(sub(sum_round(P, "apm_x1000"), sum_round(Y, "apm_x1000")),
                    lit(20000))),
    },
    {
        "id": 'R007',
        "category": 'attack',
        "canto": '論每粒方塊嘅傷害,pinglamb 高過 yachi,佢慢啲但係打得實淨',
        "english_gloss": 'pinglamb has higher attack-per-piece than yachi (more damage per piece)',
        "spec": gt(mul(sum_round(P, "garbage_attack"), sum_round(Y, "pieces")),
              mul(sum_round(Y, "garbage_attack"), sum_round(P, "pieces"))),
    },
    {
        "id": 'R008',
        "category": 'style',
        "canto": 'yachi 打 Quad(四行)多好多,373 個 vs pinglamb 293 個',
        "english_gloss": 'yachi cleared more quads (373 vs 293)',
        "spec": conj(eq(sum_round(Y, "clears.quads"), lit(373)),
                 eq(sum_round(P, "clears.quads"), lit(293))),
    },
    {
        "id": 'R009',
        "category": 'style',
        "canto": 'pinglamb 玩 T-spin double 玩得勁,339 個 vs yachi 292 個',
        "english_gloss": 'pinglamb hit more T-spin doubles (339 vs 292)',
        "spec": conj(eq(sum_round(P, "clears.tspin_doubles"), lit(339)),
                 eq(sum_round(Y, "clears.tspin_doubles"), lit(292))),
    },
    {
        "id": 'R010',
        "category": 'style',
        "canto": '連 T-spin triple pinglamb 都多啲,82 個 vs yachi 53 個',
        "english_gloss": 'pinglamb hit more T-spin triples (82 vs 53)',
        "spec": conj(eq(sum_round(P, "clears.tspin_triples"), lit(82)),
                 eq(sum_round(Y, "clears.tspin_triples"), lit(53))),
    },
    {
        "id": 'R011',
        "category": 'style',
        "canto": '整體 T-spin 數量 pinglamb 482 個,多過 yachi 406 個',
        "english_gloss": 'pinglamb has more total T-spins (482 vs 406)',
        "spec": conj(eq(sum_round(P, "tspins"), lit(482)),
                 eq(sum_round(Y, "tspins"), lit(406))),
    },
    {
        "id": 'R012',
        "category": 'style',
        "canto": 'yachi 出 all-clear(執清)多過 pinglamb,12 次 vs 7 次',
        "english_gloss": 'yachi hit more all-clears (12 vs 7)',
        "spec": conj(eq(sum_round(Y, "clears.allclear"), lit(12)),
                 eq(sum_round(P, "clears.allclear"), lit(7))),
    },
    {
        "id": 'R013',
        "category": 'style',
        "canto": '單局最高 B2B pinglamb 去到 10,yachi 最高得 8',
        "english_gloss": "pinglamb's best single-round B2B is 10 vs yachi's 8",
        "spec": conj(max_for(P, "topbtb", 10), max_for(Y, "topbtb", 8)),
    },
    {
        "id": 'R014',
        "category": 'style',
        "canto": '單局最高 combo pinglamb 去到 7,yachi 最高 6',
        "english_gloss": "pinglamb's best single-round combo is 7 vs yachi's 6",
        "spec": conj(max_for(P, "topcombo", 7), max_for(Y, "topcombo", 6)),
    },
    {
        "id": 'R015',
        "category": 'finesse',
        "canto": 'pinglamb 每粒方塊嘅 finesse 失誤率高過 yachi 接近五成,手指效率係佢嘅弱項',
        "english_gloss": "pinglamb's finesse faults per piece is ~46-48% higher than yachi's",
        "spec": conj(le(mul(lit(146), mul(sum_round(Y, "finesse_faults"), sum_round(P, "pieces"))),
                    mul(lit(100), mul(sum_round(P, "finesse_faults"), sum_round(Y, "pieces")))),
                 lt(mul(lit(100), mul(sum_round(P, "finesse_faults"), sum_round(Y, "pieces"))),
                    mul(lit(148), mul(sum_round(Y, "finesse_faults"), sum_round(P, "pieces"))))),
    },
    {
        "id": 'R016',
        "category": 'finesse',
        "canto": 'yachi 每粒方塊嘅 perfect finesse 比率高過 pinglamb,手法乾淨啲',
        "english_gloss": 'yachi has higher perfect-piece-per-piece ratio than pinglamb',
        "spec": gt(mul(sum_round(Y, "finesse_perfect"), sum_round(P, "pieces")),
              mul(sum_round(P, "finesse_perfect"), sum_round(Y, "pieces"))),
    },
    {
        "id": 'R017',
        "category": 'finesse',
        "canto": 'yachi 用 hold 用得多啲,每粒方塊 hold 比率高過 pinglamb',
        "english_gloss": 'yachi holds slightly more per piece than pinglamb',
        "spec": gt(mul(sum_round(Y, "holds"), sum_round(P, "pieces")),
              mul(sum_round(P, "holds"), sum_round(Y, "pieces"))),
    },
    {
        "id": 'R018',
        "category": 'attack',
        "canto": '防守方面 yachi 清咗 1368 行垃圾,多過 pinglamb 嘅 1324 行',
        "english_gloss": 'yachi cleared more garbage lines total (1368 vs 1324)',
        "spec": conj(eq(sum_round(Y, "garbage_cleared"), lit(1368)),
                 eq(sum_round(P, "garbage_cleared"), lit(1324))),
    },
    {
        "id": 'R019',
        "category": 'attack',
        "canto": 'yachi 俾人射埋嚟嘅攻擊約 3667,但真係食咗嘅垃圾得 3127,即係佢 cancel 咗成一成半',
        "english_gloss": "yachi's queued incoming attack (~3667) exceeds materialized garbage received (3127), ~15% cancelled",
        "spec": conj(eq(sum_ge(Y), lit(3667)),
                 eq(sum_round(Y, "garbagereceived"), lit(3127)),
                 le(mul(lit(14), sum_ge(Y)),
                    mul(lit(100), sub(sum_ge(Y), sum_round(Y, "garbagereceived")))),
                 lt(mul(lit(100), sub(sum_ge(Y), sum_round(Y, "garbagereceived"))),
                    mul(lit(15), sum_ge(Y)))),
    },
    {
        "id": 'R020',
        "category": 'clutch',
        "canto": '三場打到 5-4 嘅決勝場入面,pinglamb 攞咗 m2 同 m3,yachi 攞返 m10',
        "english_gloss": 'of the three 5-4 deciders, pinglamb won m2 and m3, yachi won m10',
        "spec": conj(match_winner(1, P), eq(nrounds(1), lit(9)),
                 match_winner(2, P), eq(nrounds(2), lit(9)),
                 match_winner(9, Y), eq(nrounds(9), lit(9))),
    },
    {
        "id": 'R021',
        "category": 'clutch',
        "canto": 'm10 嘅決勝局,yachi 撑到最後 alive,PPS(1621)同 APM(73680)兩樣都爆過 pinglamb',
        "english_gloss": "in m10's decider yachi survived alive with higher PPS (1621) and APM (73680) than pinglamb",
        "spec": conj(round_winner(9, 8, Y), eq(rnd(9, 8, Y, "alive"), lit(1)),
                 eq(rnd(9, 8, Y, "pps_x1000"), lit(1621)),
                 eq(rnd(9, 8, Y, "apm_x1000"), lit(73680)),
                 gt(rnd(9, 8, Y, "pps_x1000"), rnd(9, 8, P, "pps_x1000")),
                 gt(rnd(9, 8, Y, "apm_x1000"), rnd(9, 8, P, "apm_x1000"))),
    },
    {
        "id": 'R022',
        "category": 'spike',
        "canto": 'm3 嘅決勝局,pinglamb 用少過 yachi 嘅方塊(40 vs 53)但係劈出更大 spike(13 vs 5)反殺',
        "english_gloss": "in m3's decider pinglamb won with fewer pieces (40 vs 53) but a bigger spike (13 vs 5)",
        "spec": conj(round_winner(2, 8, P), eq(rnd(2, 8, P, "pieces"), lit(40)),
                 eq(rnd(2, 8, Y, "pieces"), lit(53)),
                 eq(rnd(2, 8, P, "maxspike"), lit(13)),
                 eq(rnd(2, 8, Y, "maxspike"), lit(5))),
    },
    {
        "id": 'R023',
        "category": 'comeback',
        "canto": '輸咗上一局之後,yachi 反彈贏返嗰局嘅比率高過 pinglamb(18/32 vs 19/37)',
        "english_gloss": "yachi's bounce-back rate after losing the previous round is higher than pinglamb's (18/32 vs 19/37)",
        "spec": conj(eq(count_round_pairs(c_winner(P), c_winner(Y)), lit(18)),
                 eq(count_round_pairs(c_winner(P)), lit(32)),
                 eq(count_round_pairs(c_winner(Y), c_winner(P)), lit(19)),
                 eq(count_round_pairs(c_winner(Y)), lit(37)),
                 gt(mul(count_round_pairs(c_winner(P), c_winner(Y)),
                        count_round_pairs(c_winner(Y))),
                    mul(count_round_pairs(c_winner(Y), c_winner(P)),
                        count_round_pairs(c_winner(P))))),
    },
    {
        "id": 'R024',
        "category": 'spike',
        "canto": '兩個嘅單 spike 天花板一樣,都試過劈出 16 嘅 spike',
        "english_gloss": 'both players peaked at a single spike of 16',
        "spec": conj(max_for(Y, "maxspike", 16), max_for(P, "maxspike", 16)),
    },
    {
        "id": 'R025',
        "category": 'spike',
        "canto": '但係大 spike 出得密啲嘅係 pinglamb,有 22 局 spike 到 12 或以上,yachi 得 16 局',
        "english_gloss": 'pinglamb had more rounds with maxspike >= 12 (22 vs 16)',
        "spec": conj(eq(count_rounds(c_field(P, "maxspike", ">=", 12)), lit(22)),
                 eq(count_rounds(c_field(Y, "maxspike", ">=", 12)), lit(16))),
    },
    {
        "id": 'R026',
        "category": 'pace',
        "canto": '論落 piece 嘅穩定性,yachi 嘅 PPS 波動細過 pinglamb,節奏穩陣啲',
        "english_gloss": "yachi's per-round PPS is less variable than pinglamb's (steadier pace)",
        "spec": lt(sub(mul(lit(ROUNDS), sum_sq_round(Y, "pps_x1000")),
                   mul(sum_round(Y, "pps_x1000"), sum_round(Y, "pps_x1000"))),
              sub(mul(lit(ROUNDS), sum_sq_round(P, "pps_x1000")),
                  mul(sum_round(P, "pps_x1000"), sum_round(P, "pps_x1000")))),
    },
    {
        "id": 'R027',
        "category": 'attack',
        "canto": '但係論攻擊輸出嘅穩定性,反而係 pinglamb 嘅 APM 波動細過 yachi',
        "english_gloss": "pinglamb's per-round APM is less variable than yachi's (steadier attack output)",
        "spec": lt(sub(mul(lit(ROUNDS), sum_sq_round(P, "apm_x1000")),
                   mul(sum_round(P, "apm_x1000"), sum_round(P, "apm_x1000"))),
              sub(mul(lit(ROUNDS), sum_sq_round(Y, "apm_x1000")),
                  mul(sum_round(Y, "apm_x1000"), sum_round(Y, "apm_x1000")))),
    },
]
