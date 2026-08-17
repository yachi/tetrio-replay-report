"""Hand-written narrative claims for 2026-07-24, as specs.

Ported from the `python_check`-only ledger this session shipped with, replacing a
session-local ~520-line codegen_dafny.py that hardcoded every bound a second time.
See 2026-07-22's hand_claims_narrative.py for the rendering patterns; this session
leans harder on the per-match leaderboard block (C020-C022) and carries the corpus's
one score-margin near-equivalence at C005, noted at its entry.
"""
from pipeline.claims.idioms import (dur_max, dur_min, max_over_players, pp_count)
from pipeline.claims.spec import (between, c_winner, conj, count_matches_margin,
                                  count_matches_won, count_rounds_window,
                                  count_rounds_won, dur, eq, gt, lb, le, lit,
                                  match_winner, nrounds, rnd, round_seq, round_winner,
                                  rounds_window, score, sum_ge, sum_lb)


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
        "id": 'C001',
        "category": 'score',
        "canto": '今場 pinglamb 贏咗四場、yachi 三場，pinglamb 反手攞返個系列',
        "english_gloss": 'pinglamb won 4 matches, yachi 3 — pinglamb takes the series',
        "spec": conj(eq(count_matches_won(P), lit(4)), eq(count_matches_won(Y), lit(3))),
    },
    {
        "id": 'C002',
        "category": 'score',
        "canto": '數返總局數，pinglamb 贏咗 29 局，yachi 得 21 局',
        "english_gloss": 'round wins: pinglamb 29, yachi 21',
        "spec": conj(eq(count_rounds_won(P), lit(29)), eq(count_rounds_won(Y), lit(21))),
    },
    {
        "id": 'C003',
        "category": 'score',
        "canto": '開場第一 match，pinglamb 5:0 直落橫掃 yachi',
        "english_gloss": 'match 1: pinglamb sweeps yachi 5-0',
        "spec": conj(match_winner(0, P), eq(score(0, Y), lit(0)), eq(score(0, P), lit(5))),
    },
    {
        "id": 'C004',
        "category": 'score',
        "canto": '去到 m4，pinglamb 再一次 5:0 橫掃，一局都唔俾 yachi',
        "english_gloss": 'match 4: pinglamb sweeps 5-0 again',
        "spec": conj(match_winner(3, P), eq(score(3, Y), lit(0)), eq(score(3, P), lit(5))),
    },
    {
        "id": 'C005',
        "category": 'score',
        "canto": '全場得兩個 5:0 橫掃，兩個都係 pinglamb 造出嚟',
        "english_gloss": 'the only two 5-0 sweeps of the session both belong to pinglamb',
        "spec": conj(eq(count_matches_margin(5), lit(2)),
                 eq(score(0, Y), lit(0)), eq(score(0, P), lit(5)), match_winner(0, P),
                 eq(score(3, Y), lit(0)), eq(score(3, P), lit(5)), match_winner(3, P)),
    },
    {
        "id": 'C006',
        "category": 'clutch',
        "canto": '由 m3 尾到 m4 尾，pinglamb 跨住兩場連贏九局',
        "english_gloss": 'pinglamb won 9 consecutive rounds spanning the end of m3 into m4',
        "spec": round_seq([(2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
                       (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (4, 0)],
                      [Y] + [P] * 9 + [Y]),
    },
    {
        "id": 'C007',
        "category": 'spike',
        "canto": 'm5 第二局，pinglamb 打出成晚冇設限之下最勁嘅單局 APM，約 95.4——不過嗰局係一局短打，速率紀錄唔計短局',
        "english_gloss": "m5 round 2 (index 1): pinglamb's ~95.4 APM is the session's highest single-round APM",
        "spec": conj(eq(rnd(4, 1, P, "apm_x1000"), lit(95498)), mx("apm_x1000", 95498),
                 between(rnd(4, 1, P, "apm_x1000"), 95000, 96000)),
    },
    {
        "id": 'C008',
        "category": 'spike',
        "canto": '同一局 pinglamb 個 VS 約 178.4，同樣係冇設限之下全場最高，同樣因為局太短唔計入紀錄',
        "english_gloss": "same round: pinglamb's ~178.4 VS is the session's highest single-round VS",
        "spec": conj(eq(rnd(4, 1, P, "vs_x1000"), lit(178457)), mx("vs_x1000", 178457),
                 between(rnd(4, 1, P, "vs_x1000"), 178000, 179000)),
    },
    {
        "id": 'C009',
        "category": 'duration',
        "canto": '呢一局淨係約 21 秒就完，係全場最短嘅一局，pinglamb 贏',
        "english_gloss": 'that round lasted ~21s, the shortest round of the session, won by pinglamb',
        "spec": conj(round_winner(4, 1, P), eq(dur(4, 1), lit(21023)), dur_min(21023),
                 between(dur(4, 1), 21000, 22000)),
    },
    {
        "id": 'C010',
        "category": 'spike',
        "canto": 'm5 第八局 pinglamb 一下打出 17 嘅單次 spike，係全場最大嘅一 spike',
        "english_gloss": "m5 round 8 (index 7): pinglamb's maxspike of 17 is the biggest single spike of the session",
        "spec": conj(eq(rnd(4, 7, P, "maxspike"), lit(17)), mx("maxspike", 17)),
    },
    {
        "id": 'C011',
        "category": 'duration',
        "canto": 'm3 第三局係全場最長嘅一局，打足約 240 秒，最後 yachi 頂硬上贏咗',
        "english_gloss": 'm3 round 3 (index 2) is the longest round, ~240s, won by yachi',
        "spec": conj(round_winner(2, 2, Y), eq(dur(2, 2), lit(240131)), dur_max(240131),
                 between(dur(2, 2), 240000, 241000)),
    },
    {
        "id": 'C012',
        "category": 'comeback',
        "canto": '呢場馬拉松 yachi 面對 177 嘅射埋嚟攻擊，比對面 158 仲多，都照贏',
        "english_gloss": "in that marathon yachi won facing 177 queued attack vs pinglamb's 158 — more incoming",
        "spec": conj(eq(sum_ge(Y, 2, 2), lit(177)), eq(sum_ge(P, 2, 2), lit(158))),
    },
    {
        "id": 'C013',
        "category": 'style',
        "canto": '呢場馬拉松 yachi 疊出全場最長嘅一條 8 combo',
        "english_gloss": "in that marathon yachi hit an 8-combo, the session's top combo",
        "spec": conj(eq(rnd(2, 2, Y, "topcombo"), lit(8)), mx("topcombo", 8)),
    },
    {
        "id": 'C014',
        "category": 'clutch',
        "canto": '最後 m7 打足九局先分到勝負，yachi 5:4 收火',
        "english_gloss": 'm7 went the full 9 rounds, yachi won 5-4',
        "spec": conj(eq(nrounds(6), lit(9)), eq(score(6, Y), lit(5)), eq(score(6, P), lit(4)),
                 match_winner(6, Y)),
    },
    {
        "id": 'C015',
        "category": 'duration',
        "canto": 'm7 係全場唯一一場要打夠九局嘅 match',
        "english_gloss": 'm7 is the only match that reached 9 rounds',
        "spec": conj(eq(nrounds(6), lit(9)),
                 *[le(nrounds(mi), lit(8)) for mi in range(MATCHES) if mi != 6]),
    },
    {
        "id": 'C016',
        "category": 'clutch',
        "canto": 'm7 局勢反反覆覆：yachi 先贏兩局，pinglamb 連追三局反超，之後 yachi 又追返',
        "english_gloss": 'm7 seesaw: yachi wins first two, pinglamb takes three straight to lead, then yachi claws back',
        "spec": conj(eq(nrounds(6), lit(9)), match_seq(6, "YYPPPYYPY")),
    },
    {
        "id": 'C017',
        "category": 'clutch',
        "canto": 'pinglamb 打平 4:4 逼出決勝局，yachi 最後嗰局頂硬上先贏到',
        "english_gloss": 'pinglamb tied m7 at 4-4 (round 8), forcing a final round that yachi won',
        "spec": conj(round_winner(6, 7, P), round_winner(6, 8, Y)),
    },
    {
        "id": 'C018',
        "category": 'style',
        "canto": 'm2 第三局 pinglamb 一局插足 18 個 T-spin，係全場之最，但係嗰局都輸咗俾 yachi',
        "english_gloss": "m2 round 3 (index 2): pinglamb's 18 T-spins is the session max in one round, yet lost the round to yachi",
        "spec": conj(eq(rnd(1, 2, P, "tspins"), lit(18)), mx("tspins", 18),
                 round_winner(1, 2, Y)),
    },
    {
        "id": 'C019',
        "category": 'style',
        "canto": 'm6 第五局 pinglamb 疊到 8 條 back-to-back，係全場最長嘅 B2B chain',
        "english_gloss": "m6 round 5 (index 4): pinglamb's top B2B of 8 is the session's longest back-to-back chain",
        "spec": conj(eq(rnd(5, 4, P, "topbtb"), lit(8)), mx("topbtb", 8)),
    },
    {
        "id": 'C020',
        "category": 'pace',
        "canto": 'm4 嗰場 pinglamb 個 match APM 高達約 64.9，係全場所有 match 最高',
        "english_gloss": "m4: pinglamb's match APM ~64.9 is the highest match-level APM of the session",
        "spec": conj(eq(lb(3, P, "apm_x1000"), lit(64901)),
                 *[le(lb(mi, pl, "apm_x1000"), lit(64901))
                   for mi in range(MATCHES) for pl in (Y, P)],
                 between(lb(3, P, "apm_x1000"), 64000, 65000)),
    },
    {
        "id": 'C021',
        "category": 'attack',
        "canto": '計返殺人數，pinglamb 收咗 29 條命，yachi 得 21 條',
        "english_gloss": 'total kills: pinglamb 29, yachi 21',
        "spec": conj(eq(sum_lb(P, "kills"), lit(29)), eq(sum_lb(Y, "kills"), lit(21))),
    },
    {
        "id": 'C022',
        "category": 'pace',
        "canto": '有樣嘢好諷刺：七場 match 入面 yachi 場場疊得快過 pinglamb（match PPS 全部高），但係都輸咗個系列',
        "english_gloss": "yachi's match PPS was higher than pinglamb's in all 7 matches, yet still lost the series",
        "spec": conj(*[gt(lb(mi, Y, "pps_x1000"), lb(mi, P, "pps_x1000"))
                   for mi in range(MATCHES)]),
    },
    {
        "id": 'C023',
        "category": 'comeback',
        "canto": '輸咗個系列都好，yachi 最後兩場 m6 同 m7 連贏，冇俾 pinglamb 攞多個 5:0 面',
        "english_gloss": 'despite losing the series, yachi won the last two matches m6 and m7',
        "spec": conj(match_winner(5, Y), match_winner(6, Y)),
    },
    {
        "id": 'C024',
        "category": 'duration',
        "canto": 'm7 最後決勝局打得好快，約 24 秒就分咗勝負，yachi 贏',
        "english_gloss": 'm7 final round (index 8) was quick, ~24s, won by yachi',
        "spec": conj(round_winner(6, 8, Y), eq(dur(6, 8), lit(24942)),
                 between(dur(6, 8), 24000, 25000)),
    },
    {
        "id": 'C025',
        "category": 'score',
        "canto": 'm2 yachi 反手 5:2 贏返嚟',
        "english_gloss": 'm2: yachi wins 5-2',
        "spec": conj(eq(score(1, Y), lit(5)), eq(score(1, P), lit(2)), match_winner(1, Y)),
    },
    {
        "id": 'C026',
        "category": 'score',
        "canto": 'm3 最後 pinglamb 5:3 收咗呢場',
        "english_gloss": 'm3: pinglamb wins 5-3',
        "spec": conj(eq(score(2, Y), lit(3)), eq(score(2, P), lit(5)), match_winner(2, P)),
    },
    {
        "id": 'C027',
        "category": 'score',
        "canto": 'm5 pinglamb 一路壓住 5:3 攞落',
        "english_gloss": 'm5: pinglamb wins 5-3',
        "spec": conj(eq(score(4, Y), lit(3)), eq(score(4, P), lit(5)), match_winner(4, P)),
    },
    {
        "id": 'C028',
        "category": 'score',
        "canto": 'm6 yachi 反手 5:3 贏返',
        "english_gloss": 'm6: yachi wins 5-3',
        "spec": conj(eq(score(5, Y), lit(5)), eq(score(5, P), lit(3)), match_winner(5, Y)),
    },
]
