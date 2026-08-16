"""Hand-written coaching claims for 2026-07-24, as specs.

The sibling of this session's hand_claims_narrative.py. R011 is the one claim here that
needed an operator the algebra did not have — a count over ADJACENT rounds within a
match — and it is noted at its entry. R001 restates the narrative ledger's C001, which
is intended; see 2026-07-22's coaching module for why that is not a duplicate.
"""
from pipeline.claims.idioms import (max_for, max_over_players, pp_count)
from pipeline.claims.spec import (add, between, c_and, c_dur, c_field, c_winner, conj,
                                  count_matches_won, count_round_pairs, count_rounds,
                                  count_rounds_range, count_rounds_window,
                                  count_rounds_won, eq, ge_, gt, lb, le, lit, lt,
                                  match_winner, mul, round_seq, rounds_window, score,
                                  sub, sum_ge, sum_round, sum_sq_round, total_rounds)


Y, P = "yachi", "pinglamb"

ROUNDS = 50
MATCHES = 7
# Flat round position of each match's first and last+1 round. A streak crosses match
# boundaries, so the "longest run" claims are windows over this flat space, not over
# matches — see spec.rounds_window.
SPANS = [(0, 5), (5, 12), (12, 20), (20, 25), (25, 33), (33, 41), (41, 50)]


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
        "canto": '呢個 session pinglamb 贏咗四場，yachi 贏咗三場',
        "english_gloss": 'pinglamb won 4 matches, yachi won 3',
        "spec": conj(eq(count_matches_won(P), lit(4)), eq(count_matches_won(Y), lit(3))),
    },
    {
        "id": 'R002',
        "category": 'score',
        "canto": '五十局入面 pinglamb 攞咗 29 局，yachi 得 21 局',
        "english_gloss": 'of 50 rounds pinglamb won 29, yachi 21',
        "spec": conj(eq(total_rounds(), lit(ROUNDS)), eq(count_rounds_won(P), lit(29)),
                 eq(count_rounds_won(Y), lit(21))),
    },
    {
        "id": 'R003',
        "category": 'pace',
        "canto": 'yachi 平均每局 PPS 約 1.40，快過 pinglamb 嘅約 1.33',
        "english_gloss": 'yachi mean per-round PPS approx 1.40 vs pinglamb approx 1.33',
        "spec": conj(between(sum_round(Y, "pps_x1000"), 70000, 70500),
                 between(sum_round(P, "pps_x1000"), 66500, 67000)),
    },
    {
        "id": 'R004',
        "category": 'attack',
        "canto": 'pinglamb 每粒方塊打出嘅攻擊多過 yachi',
        "english_gloss": 'pinglamb deals more attack per piece placed than yachi',
        "spec": gt(mul(sum_round(P, "garbage_attack"), sum_round(Y, "pieces")),
              mul(sum_round(Y, "garbage_attack"), sum_round(P, "pieces"))),
    },
    {
        "id": 'R005',
        "category": 'pace',
        "canto": '成個 session yachi 落多過 pinglamb 三百粒方塊（4748 對 4439）',
        "english_gloss": 'yachi placed more total pieces than pinglamb (4748 vs 4439)',
        "spec": conj(eq(sum_round(Y, "pieces"), lit(4748)),
                 eq(sum_round(P, "pieces"), lit(4439))),
    },
    {
        "id": 'R006',
        "category": 'finesse',
        "canto": 'yachi 嘅手法比較乾淨，每粒方塊嘅 finesse fault 少過 pinglamb',
        "english_gloss": 'yachi has fewer finesse faults per piece than pinglamb',
        "spec": lt(mul(sum_round(Y, "finesse_faults"), sum_round(P, "pieces")),
              mul(sum_round(P, "finesse_faults"), sum_round(Y, "pieces"))),
    },
    {
        "id": 'R007',
        "category": 'style',
        "canto": 'yachi 開多咗 quad（248 對 191），pinglamb 就開多咗 T-spin double（232 對 189）',
        "english_gloss": 'yachi cleared more quads (248 vs 191); pinglamb more T-spin doubles (232 vs 189)',
        "spec": conj(eq(sum_round(Y, "clears.quads"), lit(248)),
                 eq(sum_round(P, "clears.quads"), lit(191)),
                 eq(sum_round(Y, "clears.tspin_doubles"), lit(189)),
                 eq(sum_round(P, "clears.tspin_doubles"), lit(232))),
    },
    {
        "id": 'R008',
        "category": 'style',
        "canto": '計埋 T-spin double 同 triple，pinglamb 消嘅 T-spin 行數多過 yachi（284 對 221）',
        "english_gloss": 'counting T-spin doubles+triples pinglamb cleared more T-spin lines than yachi (284 vs 221)',
        "spec": conj(eq(add(sum_round(P, "clears.tspin_doubles"),
                       sum_round(P, "clears.tspin_triples")), lit(284)),
                 eq(add(sum_round(Y, "clears.tspin_doubles"),
                        sum_round(Y, "clears.tspin_triples")), lit(221))),
    },
    {
        "id": 'R009',
        "category": 'attack',
        "canto": 'pinglamb 全場 KO 咗對手 29 次，yachi 得 21 次',
        "english_gloss": 'pinglamb has 29 round-level kills vs yachi 21',
        "spec": conj(eq(sum_round(P, "kills"), lit(29)), eq(sum_round(Y, "kills"), lit(21))),
    },
    {
        "id": 'R010',
        "category": 'clutch',
        "canto": '40 秒內收工嘅快局，pinglamb 贏 11 局，yachi 得 5 局',
        "english_gloss": 'in rounds ending under 40s pinglamb won 11, yachi 5',
        "spec": conj(eq(count_rounds(c_and(c_dur("<", 40000), c_winner(P))), lit(11)),
                 eq(count_rounds(c_and(c_dur("<", 40000), c_winner(Y))), lit(5))),
    },
    {
        "id": 'R011',
        "category": 'comeback',
        "canto": '輸咗一局之後，yachi 25 次入面得 8 次即刻贏返；pinglamb 18 次入面贏返 9 次',
        "english_gloss": 'after losing a round yachi won the next only 8 of 25 times; pinglamb 9 of 18',
        "spec": conj(eq(count_round_pairs(c_winner(P), c_winner(Y)), lit(8)),
                 eq(count_round_pairs(c_winner(P)), lit(25)),
                 eq(count_round_pairs(c_winner(Y), c_winner(P)), lit(9)),
                 eq(count_round_pairs(c_winner(Y)), lit(18))),
    },
    {
        "id": 'R012',
        "category": 'clutch',
        "canto": 'yachi 一開火（單局 APM 到 65 以上）就贏，九局入面贏咗八局；pinglamb 到 65 以上 14 局全贏',
        "english_gloss": 'yachi won 8 of 9 rounds where his APM reached 65+; pinglamb won all 14 such rounds',
        "spec": conj(eq(count_rounds(c_field(Y, "apm_x1000", ">=", 65000)), lit(9)),
                 eq(count_rounds(c_and(c_field(Y, "apm_x1000", ">=", 65000),
                                       c_winner(Y))), lit(8)),
                 eq(count_rounds(c_field(P, "apm_x1000", ">=", 65000)), lit(14)),
                 eq(count_rounds(c_and(c_field(P, "apm_x1000", ">=", 65000),
                                       c_winner(P))), lit(14))),
    },
    {
        "id": 'R013',
        "category": 'spike',
        "canto": 'pinglamb 單次最大 spike 去到 17，yachi 最勁得 15',
        "english_gloss": 'pinglamb biggest single spike is 17 vs yachi 15',
        "spec": conj(max_for(P, "maxspike", 17), max_for(Y, "maxspike", 15)),
    },
    {
        "id": 'R014',
        "category": 'spike',
        "canto": '打出 12 或以上大 spike 嘅局數，pinglamb 有 13 局，yachi 得 9 局',
        "english_gloss": 'pinglamb had 13 rounds with a max spike of 12+, yachi 9',
        "spec": conj(eq(count_rounds(c_field(P, "maxspike", ">=", 12)), lit(13)),
                 eq(count_rounds(c_field(Y, "maxspike", ">=", 12)), lit(9))),
    },
    {
        "id": 'R015',
        "category": 'clutch',
        "canto": '兩場 5-0 (m1、m4) 都係 pinglamb 掃走，yachi 呢兩場一局都冇贏過',
        "english_gloss": 'both 5-0 sweeps (m1, m4) went to pinglamb; yachi won zero rounds across them',
        "spec": conj(eq(score(0, Y), lit(0)), eq(score(0, P), lit(5)),
                 eq(score(3, Y), lit(0)), eq(score(3, P), lit(5)),
                 eq(count_rounds_range(c_winner(Y), 0, 1), lit(0)),
                 eq(count_rounds_range(c_winner(Y), 3, 4), lit(0))),
    },
    {
        "id": 'R016',
        "category": 'clutch',
        "canto": '兩場被掃嘅波，pinglamb 全場 APM 都拋離 yachi 一大截（m1 高過 12、m4 高過 14）',
        "english_gloss": 'in both swept matches pinglamb match APM far exceeded yachi (m1 by 12+, m4 by 14+)',
        "spec": conj(ge_(sub(lb(0, P, "apm_x1000"), lb(0, Y, "apm_x1000")), lit(12000)),
                 ge_(sub(lb(3, P, "apm_x1000"), lb(3, Y, "apm_x1000")), lit(14000))),
    },
    {
        "id": 'R017',
        "category": 'clutch',
        "canto": '決勝嗰場 m7，yachi 5-4 險勝',
        "english_gloss": 'in the decider m7 yachi won 5-4',
        "spec": conj(match_winner(6, Y), eq(score(6, Y), lit(5)), eq(score(6, P), lit(4))),
    },
    {
        "id": 'R018',
        "category": 'clutch',
        "canto": 'm7 入面 yachi 單局 APM 上到 70 以上嗰三局，佢全部贏晒',
        "english_gloss": 'in m7 yachi won all 3 rounds where his APM reached 70+',
        "spec": conj(eq(count_rounds_range(c_field(Y, "apm_x1000", ">=", 70000), 6, 7), lit(3)),
                 eq(count_rounds_range(c_and(c_field(Y, "apm_x1000", ">=", 70000),
                                             c_winner(Y)), 6, 7), lit(3))),
    },
    {
        "id": 'R019',
        "category": 'style',
        "canto": 'yachi 每局 APM 波動細過 pinglamb，穩定啲',
        "english_gloss": "yachi round-to-round APM dispersion is smaller than pinglamb's (more consistent)",
        "spec": lt(sub(mul(lit(ROUNDS), sum_sq_round(Y, "apm_x1000")),
                   mul(sum_round(Y, "apm_x1000"), sum_round(Y, "apm_x1000"))),
              sub(mul(lit(ROUNDS), sum_sq_round(P, "apm_x1000")),
                  mul(sum_round(P, "apm_x1000"), sum_round(P, "apm_x1000")))),
    },
    {
        "id": 'R020',
        "category": 'style',
        "canto": '但講 PPS 節奏，就係 pinglamb 波動細過 yachi，出手速度更穩',
        "english_gloss": "for PPS pace pinglamb's round-to-round dispersion is smaller than yachi's",
        "spec": lt(sub(mul(lit(ROUNDS), sum_sq_round(P, "pps_x1000")),
                   mul(sum_round(P, "pps_x1000"), sum_round(P, "pps_x1000"))),
              sub(mul(lit(ROUNDS), sum_sq_round(Y, "pps_x1000")),
                  mul(sum_round(Y, "pps_x1000"), sum_round(Y, "pps_x1000")))),
    },
    {
        "id": 'R021',
        "category": 'style',
        "canto": '全場 all-clear，yachi 開咗 6 個，多過 pinglamb 嘅 4 個',
        "english_gloss": 'yachi made 6 all-clears vs pinglamb 4',
        "spec": conj(eq(sum_round(Y, "clears.allclear"), lit(6)),
                 eq(sum_round(P, "clears.allclear"), lit(4))),
    },
    {
        "id": 'R022',
        "category": 'attack',
        "canto": '防守方面兩個叮到嚟嘅攻擊都消得差唔多（yachi cancel 咗 333 行、pinglamb 329 行）',
        "english_gloss": 'both cancelled a similar amount of queued garbage (yachi 333 lines, pinglamb 329)',
        "spec": conj(eq(sub(sum_ge(Y), sum_round(Y, "garbagereceived")), lit(333)),
                 eq(sub(sum_ge(P), sum_round(P, "garbagereceived")), lit(329))),
    },
    {
        "id": 'R023',
        "category": 'style',
        "canto": 'pinglamb T-spin triple 開咗 52 個，係 yachi（32 個）嘅超過一倍半',
        "english_gloss": 'pinglamb cleared 52 T-spin triples vs yachi 32',
        "spec": conj(eq(sum_round(P, "clears.tspin_triples"), lit(52)),
                 eq(sum_round(Y, "clears.tspin_triples"), lit(32))),
    },
    {
        "id": 'R024',
        "category": 'finesse',
        "canto": 'yachi 用 hold 用得密啲，全場 hold 咗 1792 次，多過 pinglamb 嘅 1703 次',
        "english_gloss": 'yachi used hold more often (1792 vs pinglamb 1703)',
        "spec": conj(eq(sum_round(Y, "holds"), lit(1792)),
                 eq(sum_round(P, "holds"), lit(1703))),
    },
]
