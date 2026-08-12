"""Claim families.

Each family is a function `facts -> list[claim]`, where a claim is

    {"family": str, "category": str, "canto": str, "english_gloss": str, "spec": Spec}

The family locates its own instances in whatever session it is handed (argmax, streak
scan, aggregate comparison…), writes the Cantonese sentence, and builds the spec. It
never writes a predicate string — spec.py renders those, so the checked predicate and
the proved lemma always agree.

Wording rules encoded here on purpose, because each one was a review finding once:

* a rounded number is written 約 N using FLOOR (24942 ms -> 約24秒, never 約25秒)
* streaks that cross a match boundary must say so — a run spanning two matches is not
  unbroken momentum, the match reset in between
* garbage_events is QUEUED incoming attack (射埋嚟), never called 食咗嘅垃圾; the
  materialised figure is garbagereceived
* kills equal round wins by construction in first-to-death 1v1, so they are never
  presented as a second, independent signal
* the raw `tspins` counter includes spins that cleared nothing, so T-spin totals say
  which measure they mean
* traditional characters only (build_claims.py asserts this)

A NEW FAMILY GOES AT THE END OF THIS FILE. `build_claims.generate` walks FAMILIES in
decoration order and numbers the claims G001, G002, … as it goes, so inserting a family
in the middle renumbers every claim after it. Reports cite those ids in prose badges, and
a shifted id still RESOLVES — it just resolves to a different claim than the sentence is
about, which no gate can see. Appending keeps every existing id where it was.
"""

from .spec import (add, all_rounds, c_str, le, lt, sum_round_where, between, c_and, c_dur, c_field, c_winner,
                  count_matches_margin, sum_lb,
                  c_winner_gt_loser, conj, count_matches_won, count_rounds,
                  count_rounds_won, eq, gt, lb, lit, match_winner, mul, rnd,
                  round_seq, round_winner, score, sub, sum_ge, sum_round,
                  sum_sq_round, total_rounds)

FAMILIES = []


def family(fn):
    FAMILIES.append(fn)
    return fn


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #

def _players(facts):
    return facts["players"]


def _rounds(facts):
    """[(mi, ri, round_dict)] in session order."""
    return [(mi, ri, r) for mi, m in enumerate(facts["matches"])
            for ri, r in enumerate(m["rounds"])]


def _match_wins(facts):
    w = {p: 0 for p in _players(facts)}
    for m in facts["matches"]:
        w[m["winner"]] += 1
    return w


def _round_wins(facts):
    w = {p: 0 for p in _players(facts)}
    for _, _, r in _rounds(facts):
        w[r["winner"]] += 1
    return w


def _tot(facts, pl, f):
    return sum(r["players"][pl][f] for _, _, r in _rounds(facts))


def _dur(r):
    return max(d["lifetime"] for d in r["players"].values())


def _queued(r, pl):
    return sum(g["amt"] for g in r["players"][pl]["garbage_events"])


def _sec(ms):
    """Floor to whole seconds — the project's rounding convention for 約."""
    return ms // 1000


def _one_dp(x_x1000):
    """x1000 integer -> '12.3' using floor, matching the 約 convention."""
    return f"{x_x1000 // 100 / 10:.1f}"


def _two_dp(x_x1000):
    return f"{x_x1000 // 10 / 100:.2f}"


def _three_dp(x_x1000):
    """x1000 integer -> '0.666'. Exact, so flooring and rounding coincide."""
    return f"{x_x1000 / 1000:.3f}"


def _bound_dp(x_x1000):
    """An UPPER bound as 2dp, rounded **up**: 13 -> '0.02', not '0.01'.

    The flooring convention exists so 約 means "at least this much". A bound runs the
    other way — "the gap is under X" is only true if the printed X is at least the
    proved one, so this is the one place that must ceil. Flooring here printed
    "under 0.01" for a bound the lemma proved at 0.015: a claim strictly stronger
    than its own proof.
    """
    return f"{-(-x_x1000 // 10) / 100:.2f}"


def _ordinal(mi):
    return f"m{mi + 1}"


def _rank_desc(facts, key):
    """[(mi, ri, pl, value)] sorted by value, highest first."""
    out = []
    for mi, ri, r in _rounds(facts):
        for pl in _players(facts):
            out.append((mi, ri, pl, key(r["players"][pl])))
    out.sort(key=lambda t: -t[3])
    return out


# --------------------------------------------------------------------------- #
# score / structure
# --------------------------------------------------------------------------- #

@family
def series_result(facts):
    w = _match_wins(facts)
    champ = max(w, key=lambda p: w[p])
    other = [p for p in _players(facts) if p != champ][0]
    return [{
        "family": "series_result", "category": "score",
        "canto": f"成個 series {len(facts['matches'])} 場，{champ} 贏咗 {w[champ]} 場、"
                 f"{other} 贏 {w[other]} 場，{champ} 攞低個系列",
        "english_gloss": f"{champ} won the series {w[champ]}-{w[other]}",
        "spec": conj(eq(count_matches_won(champ), lit(w[champ])),
                     eq(count_matches_won(other), lit(w[other]))),
    }]


@family
def round_totals(facts):
    rw = _round_wins(facts)
    n = sum(len(m["rounds"]) for m in facts["matches"])
    a, b = sorted(rw, key=lambda p: -rw[p])
    return [{
        "family": "round_totals", "category": "score",
        "canto": f"分開一局局計，全 session 打足 {n} 局：{a} 贏 {rw[a]} 局、{b} 贏 {rw[b]} 局",
        "english_gloss": f"{n} rounds total; {a} won {rw[a]}, {b} won {rw[b]}",
        "spec": conj(eq(total_rounds(), lit(n)),
                     eq(count_rounds_won(a), lit(rw[a])),
                     eq(count_rounds_won(b), lit(rw[b]))),
    }]


@family
def first_to_five(facts):
    targets = {m["score"][m["winner"]] for m in facts["matches"]}
    if targets != {5}:
        return []
    return [{
        "family": "first_to_five", "category": "score",
        "canto": f"{len(facts['matches'])} 場都係先贏五局嗰個贏，冇一場例外",
        "english_gloss": "every match was first-to-5",
        "spec": conj(*[eq(score(mi, m["winner"]), lit(5))
                       for mi, m in enumerate(facts["matches"])]),
    }]


@family
def per_match_score(facts):
    out = []
    for mi, m in enumerate(facts["matches"]):
        win = m["winner"]
        lose = [p for p in _players(facts) if p != win][0]
        sw, sl = m["score"][win], m["score"][lose]
        out.append({
            "family": "per_match_score", "category": "score",
            "canto": f"{_ordinal(mi)}：{win} {sw}:{sl} 贏 {lose}",
            "english_gloss": f"match {mi + 1}: {win} won {sw}-{sl}",
            "spec": conj(match_winner(mi, win),
                         eq(score(mi, win), lit(sw)),
                         eq(score(mi, lose), lit(sl))),
        })
    return out


@family
def sweeps(facts):
    sw = [(mi, m) for mi, m in enumerate(facts["matches"])
          if min(m["score"].values()) == 0]
    if not sw:
        return []
    owners = {m["winner"] for _, m in sw}
    where = "、".join(_ordinal(mi) for mi, _ in sw)
    if len(owners) == 1:
        who = next(iter(owners))
        canto = (f"全場有 {len(sw)} 個 5:0 橫掃（{where}），"
                 f"全部都係 {who} 造出嚟，對手一局都冇贏過")
        gloss = f"all {len(sw)} sweep(s) belong to {who}"
        spec = conj(eq(count_matches_margin(5), lit(len(sw))),
                    *[conj(match_winner(mi, m["winner"]),
                           eq(score(mi, m["winner"]), lit(5)),
                           eq(score(mi, [p for p in _players(facts)
                                         if p != m["winner"]][0]), lit(0)))
                      for mi, m in sw])
    else:
        canto = f"全場有 {len(sw)} 個 5:0 橫掃（{where}），兩邊都試過掃人同俾人掃"
        gloss = f"{len(sw)} sweeps, shared between both players"
        spec = conj(eq(count_matches_margin(5), lit(len(sw))),
                    *[eq(score(mi, [p for p in _players(facts)
                                    if p != m["winner"]][0]), lit(0))
                      for mi, m in sw])
    return [{"family": "sweeps", "category": "score", "canto": canto,
             "english_gloss": gloss, "spec": spec}]


@family
def deciders(facts):
    """Matches that went the full distance (loser reached target - 1)."""
    dec = [(mi, m) for mi, m in enumerate(facts["matches"])
           if min(m["score"].values()) == max(m["score"].values()) - 1]
    if not dec:
        return []
    detail = "、".join(f"{_ordinal(mi)} {m['winner']} 執" for mi, m in dec)
    return [{
        "family": "deciders", "category": "clutch",
        "canto": f"有 {len(dec)} 場打到最後一局先分勝負（{detail}），場場都貼到最後",
        "english_gloss": f"{len(dec)} match(es) went to a deciding final round",
        # the count is part of the claim, so prove it: exactly this many matches
        # in the whole session have a one-round margin
        "spec": conj(eq(count_matches_margin(1), lit(len(dec))),
                     *[conj(match_winner(mi, m["winner"]),
                            eq(score(mi, m["winner"]), lit(m["score"][m["winner"]])),
                            eq(score(mi, [p for p in _players(facts)
                                          if p != m["winner"]][0]),
                               lit(min(m["score"].values()))))
                       for mi, m in dec])
    }]


@family
def longest_streak(facts):
    """Longest run of consecutive round wins, disclosing any match boundary crossed."""
    flat = [(mi, ri, r["winner"]) for mi, ri, r in _rounds(facts)]
    best_len, best_start, best_who = 0, 0, None
    i = 0
    while i < len(flat):
        j = i
        while j + 1 < len(flat) and flat[j + 1][2] == flat[i][2]:
            j += 1
        if j - i + 1 > best_len:
            best_len, best_start, best_who = j - i + 1, i, flat[i][2]
        i = j + 1
    if best_len < 3:
        return []
    span = flat[best_start:best_start + best_len]
    matches = sorted({mi for mi, _, _ in span})
    pairs = [(mi, ri) for mi, ri, _ in span]
    winners = [best_who] * best_len
    if len(matches) > 1:
        where = f"由 {_ordinal(matches[0])} 打到 {_ordinal(matches[-1])}"
        note = ("（中間換過 match，唔係一場之內嘅連勝）")
    else:
        where = f"喺 {_ordinal(matches[0])} 之內"
        note = ""
    return [{
        "family": "longest_streak", "category": "clutch",
        "canto": f"全場最長連勝係 {best_who} 連贏 {best_len} 局，{where}{note}",
        "english_gloss": (f"{best_who}'s longest run is {best_len} consecutive rounds, "
                          f"spanning {'matches ' + str([m + 1 for m in matches]) if len(matches) > 1 else 'match ' + str(matches[0] + 1)}"),
        "spec": round_seq(pairs, winners),
    }]


# --------------------------------------------------------------------------- #
# superlatives
# --------------------------------------------------------------------------- #

# A RATE record needs a qualifying round, the way a batting title needs a minimum
# number of plate appearances. APM and VS are ratios with the round's length in
# the denominator, so over a short round they behave like a sample mean over a
# small n: measured across all 492 player-rounds of the four sessions, the SD of
# VS falls from 58.2 (21 s bin) to 15.2 (144 s bin) while the MEAN stays flat
# (108 -> 118). Fitting log SD on log t gives -0.616 for VS and -0.697 for APM,
# both with -0.5 inside the 95% CI and slope 0 rejected (p 0.001 / 0.0003) —
# the signature of sampling noise, not of better play. The consequence shipped:
# all 12 unqualified rate records (3 metrics x 4 sessions) came from the shortest
# quartile of rounds, which under chance is p = 6e-08, and 07-22's headline
# "約262.6" was a 15.6-second round 45% above that session's qualified peak.
#
# 60_000 ms is where the definition and the data agree: APM and VS are per-MINUTE
# rates, so the window should be at least a minute — and each session's record
# names the identical round for every cut-off from 50 s to 70 s, so nothing here
# rests on the exact number. The full analysis is `analysis/rate_records.R`.
#
# COUNT records are deliberately NOT qualified: the artifact runs the other way
# for them. Fitting more lines or a longer B2B chain into a short round is
# harder, not easier, so a short-round count record is a real one.
QUALIFYING_MS = 60_000

_SUPERLATIVES = [
    # field, x1000?, category, noun, formatter, qualify?
    ("apm_x1000", True, "pace", "單局 APM", _one_dp, True),
    ("vs_x1000", True, "pace", "單局 VS", _one_dp, True),
    ("maxspike", False, "spike", "單一次 spike", str, False),
    ("topcombo", False, "style", "combo", str, False),
    ("topbtb", False, "style", "B2B 鏈", str, False),
    ("tspins", False, "style", "單局 T-spin 數", str, False),
    ("lines", False, "style", "單局清行數", str, False),
]


@family
def round_superlatives(facts):
    out = []
    n_qual = sum(1 for _, _, r in _rounds(facts) if _dur(r) >= QUALIFYING_MS)
    qual_secs = QUALIFYING_MS // 1000
    for f, scaled, cat, noun, fmt, qualify in _SUPERLATIVES:
        ranked = _rank_desc(facts, lambda p, f=f: p[f])
        if qualify:
            # The record is over qualifying rounds only, so the ranking, the tie
            # count and the "nobody exceeds it" conjuncts must all be restricted
            # to the same set — a superlative proved over one population and
            # stated over another is exactly the kind of gap this pipeline exists
            # to close.
            ok = {(mi, ri) for mi, ri, r in _rounds(facts) if _dur(r) >= QUALIFYING_MS}
            ranked = [t for t in ranked if (t[0], t[1]) in ok]
        if not ranked:
            continue
        mi, ri, pl, v = ranked[0]
        if v <= 0:
            continue
        ties = [t for t in ranked if t[3] == v]
        shown = fmt(v)
        tie_note = f"（呢個數字全場出現過 {len(ties)} 次）" if len(ties) > 1 else ""
        extra = "（計埋冇消行嘅 T-spin）" if f == "tspins" else ""
        winner = facts["matches"][mi]["rounds"][ri]["winner"]
        approx = "約" if scaled else ""
        # The qualified sentence names its own population, and the count of
        # qualifying rounds is proved alongside it, so a reader can see how much
        # of the session the record was taken over instead of trusting the word.
        if qualify:
            scope = (f"打足 {qual_secs} 秒以上嘅 {n_qual} 局入面，最高{noun}係")
            gloss_scope = (f"session-max {f} among the {n_qual} rounds lasting "
                           f"{qual_secs}s or more")
            note = ("（短局嘅 APM／VS 係細分母嘅產物，唔計入紀錄）"
                    if not tie_note else tie_note)
        else:
            scope = f"全場最高{noun}係"
            gloss_scope = f"session-max {f}"
            note = tie_note
        exceed = [c_field(p, f, ">", v) for p in _players(facts)]
        if qualify:
            long_enough = c_dur(">=", QUALIFYING_MS)
            both = c_and(long_enough, *exceed)
            each = [c_and(long_enough, e) for e in exceed]
        else:
            both = c_and(*exceed)
            each = exceed
        out.append({
            "family": f"round_max_{f}", "category": cat,
            "canto": f"{scope} {pl} 喺 {_ordinal(mi)} 第 {ri + 1} 局打出嘅 "
                     f"{approx}{shown}{extra}，嗰局 {winner} 生還{note}",
            "english_gloss": f"{gloss_scope} is {v} by {pl} at m{mi + 1}r{ri + 1}",
            "spec": conj(
                eq(rnd(mi, ri, pl, f), lit(v)),
                # the superlative itself: nobody in any (qualifying) round exceeds it
                eq(count_rounds(both), lit(0)),
                eq(count_rounds(each[0]), lit(0)),
                eq(count_rounds(each[1]), lit(0)),
                round_winner(mi, ri, winner),
                # how many rounds the record was taken over — without this the
                # qualifier is a word in the sentence that no lemma covers
                eq(count_rounds(c_dur(">=", QUALIFYING_MS)), lit(n_qual)) if qualify else None,
            ),
        })
    return out


@family
def round_duration_extremes(facts):
    rs = [(mi, ri, r, _dur(r)) for mi, ri, r in _rounds(facts)]
    out = []
    for label, pick, cmp_op in (("最長", max, ">"), ("最短", min, "<")):
        mi, ri, r, v = pick(rs, key=lambda t: t[3])
        secs = _sec(v)
        mins = f"（{secs // 60} 分 {secs % 60} 秒）" if secs >= 60 else ""
        out.append({
            "family": f"round_duration_{'max' if label == '最長' else 'min'}",
            "category": "duration",
            "canto": f"全場{label}嗰局係 {_ordinal(mi)} 第 {ri + 1} 局，打咗約 {secs} 秒"
                     f"{mins}，最後 {r['winner']} 生還",
            "english_gloss": (f"{'longest' if label == '最長' else 'shortest'} round is "
                              f"m{mi + 1}r{ri + 1} at {v} ms, won by {r['winner']}"),
            "spec": conj(
                # exact value AND the displayed rounding, so the claim pins both the
                # datum and the number a reader sees
                eq(rnd(mi, ri, r["winner"], "lifetime"), lit(v)),
                between(rnd(mi, ri, r["winner"], "lifetime"), secs * 1000, (secs + 1) * 1000),
                eq(count_rounds(c_dur(cmp_op, v)), lit(0)),
                round_winner(mi, ri, r["winner"]),
            ),
        })
    return out


@family
def match_level_apm_max(facts):
    best = max(((mi, pl, m["leaderboard"][pl]["apm_x1000"])
                for mi, m in enumerate(facts["matches"]) for pl in _players(facts)),
               key=lambda t: t[2])
    mi, pl, v = best
    return [{
        "family": "match_apm_max", "category": "pace",
        "canto": f"以整場 match 計，最高 APM 係 {pl} 喺 {_ordinal(mi)} 嘅約 {_one_dp(v)}",
        "english_gloss": f"highest match-level APM is {_one_dp(v)} by {pl} in m{mi + 1}",
        "spec": conj(
            between(lb(mi, pl, "apm_x1000"), v // 100 * 100, v // 100 * 100 + 100),
            *[gt(lit(v + 1), lb(m2, p2, "apm_x1000"))
              for m2 in range(len(facts["matches"])) for p2 in _players(facts)],
        ),
    }]


# --------------------------------------------------------------------------- #
# pressure / defence
# --------------------------------------------------------------------------- #

@family
def vs_decides(facts):
    exceptions = 0
    for _, _, r in _rounds(facts):
        win = r["winner"]
        lose = [p for p in r["players"] if p != win][0]
        if r["players"][win]["vs_x1000"] <= r["players"][lose]["vs_x1000"]:
            exceptions += 1
    n = sum(len(m["rounds"]) for m in facts["matches"])
    if exceptions == 0:
        canto = f"{n} 局裏面，每一局贏嗰個嘅 VS 都高過輸嗰個，零例外"
        gloss = f"in all {n} rounds the winner had the higher VS"
        spec = all_rounds(c_winner_gt_loser("vs_x1000"))
    else:
        canto = (f"{n} 局裏面有 {n - exceptions} 局係 VS 高嗰個贏，"
                 f"得 {exceptions} 局爆冷")
        gloss = f"{n - exceptions}/{n} rounds won by the higher-VS player"
        spec = eq(count_rounds(c_winner_gt_loser("vs_x1000")), lit(n - exceptions))
    return [{"family": "vs_decides", "category": "style", "canto": canto,
             "english_gloss": gloss, "spec": spec}]


@family
def biggest_comeback(facts):
    """Round won while more attack was queued at the winner than at the loser."""
    best = None
    for mi, ri, r in _rounds(facts):
        win = r["winner"]
        lose = [p for p in r["players"] if p != win][0]
        diff = _queued(r, win) - _queued(r, lose)
        if best is None or diff > best[0]:
            best = (diff, mi, ri, win, lose, _queued(r, win), _queued(r, lose))
    if best is None:
        return []
    diff, mi, ri, win, lose, qw, ql = best
    if diff <= 0:
        return []
    return [{
        "family": "biggest_comeback", "category": "comeback",
        "canto": f"最硬淨嘅一局係 {_ordinal(mi)} 第 {ri + 1} 局：{win} 俾人射埋嚟 {qw} 行，"
                 f"多過 {lose} 嘅 {ql} 行，照樣頂住贏返",
        "english_gloss": (f"biggest comeback m{mi + 1}r{ri + 1}: winner faced {qw} queued "
                          f"attack vs loser's {ql}"),
        "spec": conj(round_winner(mi, ri, win),
                     eq(sum_ge(win, mi, ri), lit(qw)),
                     eq(sum_ge(lose, mi, ri), lit(ql))),
    }]


@family
def cancellation(facts):
    out = []
    for pl in _players(facts):
        queued = sum(_queued(r, pl) for _, _, r in _rounds(facts))
        got = _tot(facts, pl, "garbagereceived")
        if queued <= got:
            continue
        out.append({
            "family": "cancellation", "category": "attack",
            "canto": f"{pl} 全場俾人射埋嚟 {queued} 行，真正食落身嘅係 {got} 行，"
                     f"即係 cancel 咗 {queued - got} 行",
            "english_gloss": (f"{pl}: {queued} lines of attack queued, {got} materialised, "
                              f"{queued - got} cancelled"),
            "spec": conj(eq(sum_ge(pl), lit(queued)),
                         eq(sum_round(pl, "garbagereceived"), lit(got))),
        })
    return out


# --------------------------------------------------------------------------- #
# player aggregates
# --------------------------------------------------------------------------- #

_TOTALS = [
    ("pieces", "pace", "落咗嘅方塊", "粒"),
    ("garbage_attack", "attack", "打出嘅攻擊", "行"),
    ("garbage_cleared", "attack", "清走嘅垃圾", "行"),
    ("finesse_faults", "finesse", "finesse 失誤", "次"),
    ("holds", "style", "hold 次數", "次"),
    ("tspins", "style", "T-spin 總數（計埋冇消行嘅）", "個"),
]


@family
def totals_comparison(facts):
    out = []
    for f, cat, noun, unit in _TOTALS:
        vals = {p: _tot(facts, p, f) for p in _players(facts)}
        hi, lo = sorted(vals, key=lambda p: -vals[p])
        if vals[hi] == vals[lo]:
            continue
        out.append({
            "family": f"total_{f}", "category": cat,
            "canto": f"全 session {noun}：{hi} {vals[hi]} {unit}，{lo} {vals[lo]} {unit}",
            "english_gloss": f"total {f}: {hi} {vals[hi]}, {lo} {vals[lo]}",
            "spec": conj(eq(sum_round(hi, f), lit(vals[hi])),
                         eq(sum_round(lo, f), lit(vals[lo]))),
        })
    return out


_CLEARS = [("quads", "Quad"), ("tspin_doubles", "T-spin double"),
           ("tspin_triples", "T-spin triple"), ("allclear", "All Clear")]


@family
def clear_mix(facts):
    out = []
    for key, label in _CLEARS:
        vals = {p: sum(r["players"][p]["clears"][key] for _, _, r in _rounds(facts))
                for p in _players(facts)}
        if max(vals.values()) == 0:
            continue
        hi, lo = sorted(vals, key=lambda p: -vals[p])
        # clears live under r['players'][pl]['clears'][key]; the spec algebra reads
        # flat per-round fields, so these are summed via the dedicated clear field
        out.append({
            "family": f"clears_{key}", "category": "style",
            "canto": f"{label} 總數：{hi} {vals[hi]} 個，{lo} {vals[lo]} 個",
            "english_gloss": f"total {key}: {hi} {vals[hi]}, {lo} {vals[lo]}",
            "spec": conj(eq(sum_round(hi, f"clears.{key}"), lit(vals[hi])),
                         eq(sum_round(lo, f"clears.{key}"), lit(vals[lo]))),
        })
    return out


@family
def kills(facts):
    vals = {p: _tot(facts, p, "kills") for p in _players(facts)}
    hi, lo = sorted(vals, key=lambda p: -vals[p])
    return [{
        "family": "kills", "category": "attack",
        "canto": f"KO 數：{hi} {vals[hi]}、{lo} {vals[lo]} —— 1v1 一局一命，"
                 f"所以呢個數等於局數，唔算另一個獨立指標",
        "english_gloss": (f"kills: {hi} {vals[hi]}, {lo} {vals[lo]} — equal to round wins "
                          f"by construction in 1v1"),
        "spec": conj(eq(sum_round(hi, "kills"), lit(vals[hi])),
                     eq(sum_round(lo, "kills"), lit(vals[lo])),
                     eq(sum_lb(hi, "kills"), lit(vals[hi])),
                     eq(sum_lb(lo, "kills"), lit(vals[lo]))),
    }]


@family
def average_rates(facts):
    n = sum(len(m["rounds"]) for m in facts["matches"])
    out = []
    for f, label, fmt in (("pps_x1000", "PPS", _two_dp), ("apm_x1000", "APM", _one_dp)):
        sums = {p: _tot(facts, p, f) for p in _players(facts)}
        hi, lo = sorted(sums, key=lambda p: -sums[p])
        if sums[hi] == sums[lo]:
            continue
        out.append({
            "family": f"avg_{f}", "category": "pace",
            "canto": f"每局平均 {label}：{hi} 約 {fmt(sums[hi] // n)}，"
                     f"高過 {lo} 嘅約 {fmt(sums[lo] // n)}",
            "english_gloss": (f"per-round mean {label}: {hi} {_three_dp(sums[hi] // n)} > "
                              f"{lo} {_three_dp(sums[lo] // n)}"),
            "spec": conj(eq(sum_round(hi, f), lit(sums[hi])),
                         eq(sum_round(lo, f), lit(sums[lo])),
                         gt(sum_round(hi, f), sum_round(lo, f))),
        })
    return out


@family
def per_piece_rates(facts):
    """Cross-multiplied ratio comparisons — no division, so it stays integer-exact."""
    out = []
    for f, cat, phrase in (("garbage_attack", "attack", "每粒方塊打出嘅攻擊"),
                           ("finesse_faults", "finesse", "每粒方塊嘅 finesse 失誤"),
                           ("finesse_perfect", "finesse", "perfect piece 嘅比率")):
        a, b = _players(facts)
        va, vb = _tot(facts, a, f), _tot(facts, b, f)
        pa, pb = _tot(facts, a, "pieces"), _tot(facts, b, "pieces")
        if va * pb == vb * pa:
            continue
        hi, lo = (a, b) if va * pb > vb * pa else (b, a)
        better = "多" if f == "garbage_attack" else "多"
        out.append({
            "family": f"per_piece_{f}", "category": cat,
            "canto": f"{phrase}：{hi} {better}過 {lo}",
            "english_gloss": f"{f} per piece: {hi} > {lo}",
            "spec": gt(mul(sum_round(hi, f), sum_round(lo, "pieces")),
                       mul(sum_round(lo, f), sum_round(hi, "pieces"))),
        })
    return out


@family
def consistency(facts):
    """Integer variance identity n*Sum(x^2) - (Sum x)^2 — no sqrt, no floats."""
    n = sum(len(m["rounds"]) for m in facts["matches"])
    out = []
    for f, label in (("pps_x1000", "PPS"), ("apm_x1000", "APM")):
        var = {}
        for p in _players(facts):
            s, sq = _tot(facts, p, f), sum(
                r["players"][p][f] ** 2 for _, _, r in _rounds(facts))
            var[p] = n * sq - s * s
        steady, swingy = sorted(var, key=lambda p: var[p])
        if var[steady] == var[swingy]:
            continue
        out.append({
            "family": f"consistency_{f}", "category": "style",
            "canto": f"逐局 {label} 嘅波動：{steady} 平穩過 {swingy}",
            "english_gloss": f"per-round {label} variance: {steady} < {swingy}",
            "spec": gt(sub(mul(lit(n), sum_sq_round(swingy, f)),
                           mul(sum_round(swingy, f), sum_round(swingy, f))),
                       sub(mul(lit(n), sum_sq_round(steady, f)),
                           mul(sum_round(steady, f), sum_round(steady, f)))),
        })
    return out


# --------------------------------------------------------------------------- #
# situational records
# --------------------------------------------------------------------------- #

@family
def fast_round_record(facts):
    LIMIT = 40_000
    fast = [(mi, ri, r) for mi, ri, r in _rounds(facts) if _dur(r) < LIMIT]
    if len(fast) < 4:
        return []
    rec = {p: sum(1 for _, _, r in fast if r["winner"] == p) for p in _players(facts)}
    hi, lo = sorted(rec, key=lambda p: -rec[p])
    if rec[hi] == rec[lo]:
        return []
    return [{
        "family": "fast_round_record", "category": "clutch",
        "canto": f"{LIMIT // 1000} 秒內收工嘅快局共 {len(fast)} 局，"
                 f"{hi} 贏 {rec[hi]} 局、{lo} 贏 {rec[lo]} 局",
        "english_gloss": (f"rounds under {LIMIT // 1000}s: {hi} won {rec[hi]}, "
                          f"{lo} won {rec[lo]} (of {len(fast)})"),
        "spec": conj(eq(count_rounds(c_dur("<", LIMIT)), lit(len(fast))),
                     eq(count_rounds(c_and(c_dur("<", LIMIT), c_winner(hi))), lit(rec[hi])),
                     eq(count_rounds(c_and(c_dur("<", LIMIT), c_winner(lo))), lit(rec[lo]))),
    }]


@family
def high_apm_round_record(facts):
    LIMIT = 65_000
    out = []
    for pl in _players(facts):
        hot = [(mi, ri, r) for mi, ri, r in _rounds(facts)
               if r["players"][pl]["apm_x1000"] >= LIMIT]
        if len(hot) < 4:
            continue
        won = sum(1 for _, _, r in hot if r["winner"] == pl)
        out.append({
            "family": "high_apm_record", "category": "clutch",
            "canto": f"{pl} 打到 APM {LIMIT // 1000} 以上嘅局有 {len(hot)} 局，"
                     f"贏咗 {won} 局",
            "english_gloss": f"{pl} in rounds with APM >= {LIMIT // 1000}: {won}/{len(hot)}",
            "spec": conj(eq(count_rounds(c_field(pl, "apm_x1000", ">=", LIMIT)), lit(len(hot))),
                         eq(count_rounds(c_and(c_field(pl, "apm_x1000", ">=", LIMIT),
                                               c_winner(pl))), lit(won))),
        })
    return out


@family
def bounce_back(facts):
    """After dropping a round, how often does a player take the next one?"""
    out = []
    for pl in _players(facts):
        chances = wins = 0
        for m in facts["matches"]:
            rs = m["rounds"]
            for i in range(len(rs) - 1):
                if rs[i]["winner"] != pl:
                    chances += 1
                    if rs[i + 1]["winner"] == pl:
                        wins += 1
        if chances < 5:
            continue
        out.append({
            "family": "bounce_back", "category": "clutch",
            "canto": f"{pl} 輸咗一局之後，{chances} 次機會裏面即刻贏返 {wins} 次",
            "english_gloss": f"{pl} bounce-back after a lost round: {wins}/{chances}",
            "spec": _bounce_spec(facts, pl, chances, wins),
        })
    return out


def _bounce_spec(facts, pl, chances, wins):
    """Ground the bounce-back counts as sums over the concrete round pairs."""
    pairs = []
    for mi, m in enumerate(facts["matches"]):
        rs = m["rounds"]
        for i in range(len(rs) - 1):
            pairs.append((mi, i, rs[i]["winner"] != pl, rs[i + 1]["winner"] == pl))
    got_chances = sum(1 for _, _, c, _ in pairs if c)
    got_wins = sum(1 for _, _, c, w in pairs if c and w)
    assert (got_chances, got_wins) == (chances, wins)
    # expressed as a conjunction over the individual round winners involved, which
    # keeps the Dafny side ground and mutation-sensitive
    parts = []
    for mi, i, c, _won in pairs:
        if not c:
            continue
        loser = [p for p in _players(facts) if p != pl][0]
        parts.append(round_winner(mi, i, loser))
        nxt = facts["matches"][mi]["rounds"][i + 1]["winner"]
        parts.append(round_winner(mi, i + 1, nxt))
    return conj(*parts)


# --------------------------------------------------------------------------- #
# match-level dominance and spike profile
# --------------------------------------------------------------------------- #

@family
def match_rate_dominance(facts):
    """One player ahead on a match-level rate in EVERY match — speed that did not pay."""
    out = []
    a, b = _players(facts)
    wins = _match_wins(facts)
    for f, label in (("pps_x1000", "PPS"), ("apm_x1000", "APM")):
        for hi, lo in ((a, b), (b, a)):
            if not all(m["leaderboard"][hi][f] > m["leaderboard"][lo][f]
                       for m in facts["matches"]):
                continue
            lost = wins[hi] < wins[lo]
            tail = ("，但係都輸咗個系列 —— 快唔等於贏" if lost else "，全面壓住對手")
            out.append({
                "family": f"match_dominance_{f}", "category": "pace",
                "canto": f"{len(facts['matches'])} 場 match，{hi} 嘅場均 {label} "
                         f"場場都高過 {lo}{tail}",
                "english_gloss": (f"{hi}'s match-level {label} exceeded {lo}'s in all "
                                  f"{len(facts['matches'])} matches"),
                "spec": conj(*[gt(lb(mi, hi, f), lb(mi, lo, f))
                               for mi in range(len(facts["matches"]))]),
            })
    return out


_CEILINGS = [("maxspike", "spike", "單一次 spike", "行"),
             ("topbtb", "style", "B2B 鏈", "段"),
             ("topcombo", "style", "combo", "下")]


@family
def player_ceilings(facts):
    """Each player's own personal best — a ceiling comparison, not a session max."""
    out = []
    for f, cat, noun, unit in _CEILINGS:
        best = {pl: max(((mi, ri, r["players"][pl][f]) for mi, ri, r in _rounds(facts)),
                        key=lambda t: t[2]) for pl in _players(facts)}
        a, b = _players(facts)
        if best[a][2] == best[b][2] or max(best[a][2], best[b][2]) == 0:
            continue
        hi, lo = (a, b) if best[a][2] > best[b][2] else (b, a)
        out.append({
            "family": f"player_ceiling_{f}", "category": cat,
            "canto": f"{noun} 嘅個人上限：{hi} 做到 {best[hi][2]} {unit}，"
                     f"{lo} 最多 {best[lo][2]} {unit}",
            "english_gloss": f"best single-round {f}: {hi} {best[hi][2]} vs {lo} {best[lo][2]}",
            "spec": conj(
                eq(rnd(best[hi][0], best[hi][1], hi, f), lit(best[hi][2])),
                eq(count_rounds(c_field(hi, f, ">", best[hi][2])), lit(0)),
                eq(rnd(best[lo][0], best[lo][1], lo, f), lit(best[lo][2])),
                eq(count_rounds(c_field(lo, f, ">", best[lo][2])), lit(0)),
            ),
        })
    return out


@family
def spike_frequency(facts):
    """How often each player reached a big spike — frequency, not ceiling."""
    LIMIT = 12
    counts = {p: sum(1 for _, _, r in _rounds(facts)
                     if r["players"][p]["maxspike"] >= LIMIT) for p in _players(facts)}
    if max(counts.values()) < 3 or counts[_players(facts)[0]] == counts[_players(facts)[1]]:
        return []
    hi, lo = sorted(counts, key=lambda p: -counts[p])
    return [{
        "family": "spike_frequency", "category": "spike",
        "canto": f"劈到 {LIMIT} 行以上嘅局數：{hi} 有 {counts[hi]} 局，{lo} 有 {counts[lo]} 局",
        "english_gloss": (f"rounds with a spike of {LIMIT}+: {hi} {counts[hi]}, "
                          f"{lo} {counts[lo]}"),
        "spec": conj(eq(count_rounds(c_field(hi, "maxspike", ">=", LIMIT)), lit(counts[hi])),
                     eq(count_rounds(c_field(lo, "maxspike", ">=", LIMIT)), lit(counts[lo]))),
    }]


@family
def tspin_lines(facts):
    """T-spin doubles + triples: the line-clearing T-spin measure, spelled out."""
    vals = {}
    for pl in _players(facts):
        vals[pl] = sum(r["players"][pl]["clears"]["tspin_doubles"]
                       + r["players"][pl]["clears"]["tspin_triples"]
                       for _, _, r in _rounds(facts))
    a, b = _players(facts)
    if vals[a] == vals[b]:
        return []
    hi, lo = (a, b) if vals[a] > vals[b] else (b, a)
    return [{
        "family": "tspin_lines", "category": "style",
        "canto": f"T-spin double 加 triple 計埋：{hi} {vals[hi]} 個，{lo} {vals[lo]} 個"
                 f"（唔計冇消行嘅 T-spin）",
        "english_gloss": (f"T-spin doubles+triples: {hi} {vals[hi]}, {lo} {vals[lo]} "
                          f"(line-clearing T-spins only)"),
        "spec": conj(
            eq(add(sum_round(hi, "clears.tspin_doubles"),
                   sum_round(hi, "clears.tspin_triples")), lit(vals[hi])),
            eq(add(sum_round(lo, "clears.tspin_doubles"),
                   sum_round(lo, "clears.tspin_triples")), lit(vals[lo])),
        ),
    }]


@family
def sweep_shutout(facts):
    """In a 5-0 sweep the loser wins nothing — state it as round winners."""
    sw = [(mi, m) for mi, m in enumerate(facts["matches"])
          if min(m["score"].values()) == 0]
    if not sw:
        return []
    out = []
    for mi, m in sw:
        win = m["winner"]
        lose = [p for p in _players(facts) if p != win][0]
        gap_lo = min(abs(m["leaderboard"][win]["apm_x1000"]
                         - m["leaderboard"][lose]["apm_x1000"]) // 1000, 99)
        out.append({
            "family": "sweep_shutout", "category": "clutch",
            "canto": f"{_ordinal(mi)} 嘅 5:0：{lose} 一局都攞唔到，"
                     f"嗰場 {win} 嘅場均 APM 拋離對手十幾（差 {gap_lo} 以上）",
            "english_gloss": (f"m{mi + 1} shutout: {lose} won no rounds; {win} led match "
                              f"APM by at least {gap_lo}"),
            "spec": conj(
                *[round_winner(mi, ri, win) for ri in range(len(m["rounds"]))],
                gt(lb(mi, win, "apm_x1000"),
                   add(lb(mi, lose, "apm_x1000"), lit(gap_lo * 1000))),
            ),
        })
    return out


# --------------------------------------------------------------------------- #
# comebacks, shutouts, spotlights
# --------------------------------------------------------------------------- #

@family
def score_table(facts):
    """Every match score in one claim — the whole result table, pinned."""
    seq = "、".join(
        f"{_ordinal(mi)} {m['score'][facts['players'][0]]}-{m['score'][facts['players'][1]]}"
        for mi, m in enumerate(facts["matches"]))
    return [{
        "family": "score_table", "category": "score",
        "canto": f"{len(facts['matches'])} 場嘅比數（{facts['players'][0]} 對 "
                 f"{facts['players'][1]}）：{seq}",
        "english_gloss": ("all match scores in order (" +
                          "-".join(facts["players"]) + "): " +
                          ", ".join(f"{m['score'][facts['players'][0]]}-"
                                    f"{m['score'][facts['players'][1]]}"
                                    for m in facts["matches"])),
        "spec": conj(*[conj(eq(score(mi, facts["players"][0]),
                               lit(m["score"][facts["players"][0]])),
                            eq(score(mi, facts["players"][1]),
                               lit(m["score"][facts["players"][1]])),
                            match_winner(mi, m["winner"]))
                       for mi, m in enumerate(facts["matches"])]),
    }]


@family
def comeback_rounds(facts):
    """Rounds won by the player who actually ate MORE garbage (materialised, not queued)."""
    hits = []
    for mi, ri, r in _rounds(facts):
        win = r["winner"]
        lose = [p for p in r["players"] if p != win][0]
        if r["players"][win]["garbagereceived"] > r["players"][lose]["garbagereceived"]:
            hits.append((mi, ri, win))
    if len(hits) < 2:
        return []
    split = {p: sum(1 for _, _, w in hits if w == p) for p in _players(facts)}
    hi, lo = sorted(split, key=lambda p: -split[p])
    return [{
        "family": "comeback_rounds", "category": "comeback",
        "canto": f"有 {len(hits)} 局係食多過對手嘅垃圾都照贏，"
                 f"{hi} 佔 {split[hi]} 局、{lo} 佔 {split[lo]} 局",
        "english_gloss": (f"{len(hits)} rounds won while receiving more real garbage; "
                          f"{hi} {split[hi]}, {lo} {split[lo]}"),
        "spec": conj(
            eq(count_rounds(c_winner_gt_loser("garbagereceived")), lit(len(hits))),
            *[eq(count_rounds(c_and(c_winner_gt_loser("garbagereceived"), c_winner(p))),
                 lit(split[p])) for p in (hi, lo)],
        ),
    }]


@family
def cleanest_win(facts):
    """The round where the winner conceded the least — a shutout measure."""
    best = min(((mi, ri, r, r["players"][r["winner"]]["garbagereceived"])
                for mi, ri, r in _rounds(facts)), key=lambda t: t[3])
    mi, ri, r, v = best
    win = r["winner"]
    lose = [p for p in r["players"] if p != win][0]
    return [{
        "family": "cleanest_win", "category": "clutch",
        "canto": f"最乾淨嘅一局係 {_ordinal(mi)} 第 {ri + 1} 局：{win} 全局只食咗 {v} 行垃圾，"
                 f"直接封死 {lose}",
        "english_gloss": (f"cleanest win m{mi + 1}r{ri + 1}: {win} conceded only {v} "
                          f"lines of garbage (session minimum for a winner)"),
        "spec": conj(round_winner(mi, ri, win),
                     eq(rnd(mi, ri, win, "garbagereceived"), lit(v)),
                     eq(count_rounds(c_and(c_winner(win),
                                           c_field(win, "garbagereceived", "<", v))), lit(0)),
                     eq(count_rounds(c_and(c_winner(lose),
                                           c_field(lose, "garbagereceived", "<", v))), lit(0))),
    }]


@family
def decider_final_rounds(facts):
    """Spotlight the last round of every match that went the distance."""
    out = []
    for mi, m in enumerate(facts["matches"]):
        if min(m["score"].values()) != max(m["score"].values()) - 1:
            continue
        ri = len(m["rounds"]) - 1
        r = m["rounds"][ri]
        win = r["winner"]
        lose = [p for p in r["players"] if p != win][0]
        vw, vl = r["players"][win]["vs_x1000"], r["players"][lose]["vs_x1000"]
        aw, al = r["players"][win]["apm_x1000"], r["players"][lose]["apm_x1000"]
        out.append({
            "family": "decider_final_round", "category": "clutch",
            "canto": f"{_ordinal(mi)} 嘅生死局：{win} 打出 VS 約 {_one_dp(vw)}、"
                     f"APM 約 {_one_dp(aw)}，{lose} 得 VS 約 {_one_dp(vl)}、"
                     f"APM 約 {_one_dp(al)}",
            "english_gloss": (f"m{mi + 1} deciding round: {win} VS {_one_dp(vw)} / APM "
                              f"{_one_dp(aw)} vs {lose} VS {_one_dp(vl)} / APM "
                              f"{_one_dp(al)}"),
            "spec": conj(round_winner(mi, ri, win),
                         between(rnd(mi, ri, win, "vs_x1000"), vw // 100 * 100, vw // 100 * 100 + 100),
                         between(rnd(mi, ri, win, "apm_x1000"), aw // 100 * 100, aw // 100 * 100 + 100),
                         between(rnd(mi, ri, lose, "vs_x1000"), vl // 100 * 100, vl // 100 * 100 + 100),
                         between(rnd(mi, ri, lose, "apm_x1000"), al // 100 * 100, al // 100 * 100 + 100)),
        })
    return out


@family
def most_intense_round(facts):
    """Highest combined VS — the round where both players were swinging hardest.

    Qualified at QUALIFYING_MS for the same reason as the single-player VS record:
    a sum of two rates carries both denominators, so a short round inflates it
    twice over. The comparison conjuncts range over the qualifying rounds only.
    """
    qual = [(mi, ri, r) for mi, ri, r in _rounds(facts) if _dur(r) >= QUALIFYING_MS]
    if not qual:
        return []
    best = max(((mi, ri, r, sum(r["players"][p]["vs_x1000"] for p in r["players"]))
                for mi, ri, r in qual), key=lambda t: t[3])
    mi, ri, r, tot = best
    win = r["winner"]
    lose = [p for p in r["players"] if p != win][0]
    qual_secs = QUALIFYING_MS // 1000
    return [{
        "family": "most_intense_round", "category": "pace",
        "canto": f"打足 {qual_secs} 秒以上嘅局入面最癲嘅一局係 {_ordinal(mi)} 第 {ri + 1} 局，"
                 f"兩邊 VS 加埋約 "
                 f"{_one_dp(tot)}（{win} 約 {_one_dp(r['players'][win]['vs_x1000'])} 對 "
                 f"{lose} 約 {_one_dp(r['players'][lose]['vs_x1000'])}）",
        "english_gloss": (f"highest combined VS among rounds of {qual_secs}s or more is "
                          f"m{mi + 1}r{ri + 1} at {_one_dp(tot)}, won by {win}"),
        "spec": conj(round_winner(mi, ri, win),
                     eq(add(rnd(mi, ri, win, "vs_x1000"), rnd(mi, ri, lose, "vs_x1000")),
                        lit(tot)),
                     *[le(add(rnd(m2, r2, facts["players"][0], "vs_x1000"),
                              rnd(m2, r2, facts["players"][1], "vs_x1000")), lit(tot))
                       for m2, r2, _ in qual]),
    }]


# --------------------------------------------------------------------------- #
# stats the in-game end screen does not surface
# --------------------------------------------------------------------------- #

@family
def keys_per_piece(facts):
    """KPP — how many keypresses each piece costs. Lower is cleaner movement."""
    a, b = _players(facts)
    ia, ib = _tot(facts, a, "inputs"), _tot(facts, b, "inputs")
    pa, pb = _tot(facts, a, "pieces"), _tot(facts, b, "pieces")
    if ia * pb == ib * pa:
        return []
    lo, hi = (a, b) if ia * pb < ib * pa else (b, a)
    return [{
        "family": "keys_per_piece", "category": "finesse",
        "canto": f"每粒方塊要按幾多下（KPP）：{lo} 少過 {hi}，即係 {lo} 嘅手法比較省力",
        "english_gloss": f"keys per piece: {lo} lower than {hi}",
        "spec": gt(mul(sum_round(hi, "inputs"), sum_round(lo, "pieces")),
                   mul(sum_round(lo, "inputs"), sum_round(hi, "pieces"))),
    }]


@family
def death_reasons(facts):
    """How rounds actually ended, from the loser's game-over reason."""
    from collections import Counter
    tally = Counter()
    for _, _, r in _rounds(facts):
        for pl, p in r["players"].items():
            if pl != r["winner"]:
                tally[p.get("gameoverreason", "")] += 1
    tally.pop("", None)
    if not tally:
        return []
    label = {"garbagesmash": "俾垃圾頂爆", "topout": "自己頂到頂",
             "forfeit": "投降", "winner": "對手死"}
    total = sum(tally.values())
    parts = "、".join(f"{tally[k]} 局{label.get(k, k)}" for k, _ in tally.most_common())
    return [{
        "family": "death_reasons", "category": "style",
        "canto": f"{total} 局係點收嘅：{parts}",
        "english_gloss": ("how rounds ended: " +
                          ", ".join(f"{k} {v}" for k, v in tally.most_common())),
        # counted per reason across both players; the winner's reason is always
        # "winner", so these counts are exactly the losing sides
        "spec": conj(*[
            eq(add(count_rounds(c_str(_players(facts)[0], "gameoverreason", reason)),
                   count_rounds(c_str(_players(facts)[1], "gameoverreason", reason))),
               lit(n))
            for reason, n in tally.most_common()]),
    }]


@family
def score_totals(facts):
    """In-game score — a rough proxy for total constructive output."""
    vals = {p: _tot(facts, p, "score") for p in _players(facts)}
    hi, lo = sorted(vals, key=lambda p: -vals[p])
    if vals[hi] == vals[lo]:
        return []
    return [{
        "family": "score_totals", "category": "style",
        "canto": f"全 session 累計分數：{hi} {vals[hi]:,} 分，{lo} {vals[lo]:,} 分",
        "english_gloss": f"total in-game score: {hi} {vals[hi]}, {lo} {vals[lo]}",
        "spec": conj(eq(sum_round(hi, "score"), lit(vals[hi])),
                     eq(sum_round(lo, "score"), lit(vals[lo]))),
    }]


@family
def spike_multiplier_effect(facts):
    """How much of each player's damage came from multipliers rather than raw sends."""
    out = []
    for pl in _players(facts):
        raw = _tot(facts, pl, "garbage_sent_nomult")
        sent = _tot(facts, pl, "garbage_sent_raw")
        if sent <= raw:
            continue
        out.append({
            "family": "multiplier_bonus", "category": "attack",
            "canto": f"{pl} 送出 {sent} 行垃圾，當中 {sent - raw} 行係倍率加成嚟嘅"
                     f"（唔計倍率淨係 {raw} 行）",
            "english_gloss": (f"{pl} sent {sent} lines, {sent - raw} of them from "
                              f"multipliers ({raw} before multipliers)"),
            "spec": conj(eq(sum_round(pl, "garbage_sent_raw"), lit(sent)),
                         eq(sum_round(pl, "garbage_sent_nomult"), lit(raw))),
        })
    return out


# --------------------------------------------------------------------------- #
# per-piece rates split by outcome — does the rate actually predict winning?
# --------------------------------------------------------------------------- #
# APP (attack per piece), KPP (keypresses per piece) and DS (garbage cleared per
# piece) are the rates a coach cares about, but a session total only says who was
# higher overall. The useful question is whether a player's OWN rate moves between
# the rounds they won and the rounds they lost. All comparisons are cross-multiplied
# so they stay exact integer arithmetic.

_RATES = [
    ("garbage_attack", "APP", "每粒方塊打出嘅攻擊", "attack per piece"),
    ("inputs", "KPP", "每粒方塊要按幾多下", "keypresses per piece"),
    ("garbage_cleared", "DS", "每粒方塊清走幾多垃圾", "garbage cleared per piece"),
]


def _rate_x1000(facts, pl, f, won):
    """The player's rate over the rounds they won (or lost), x1000."""
    num = den = 0
    for _, _, r in _rounds(facts):
        if (r["winner"] == pl) != won:
            continue
        num += r["players"][pl][f]
        den += r["players"][pl]["pieces"]
    return ((num * 1000) // den if den else 0), num, den


@family
def rate_by_outcome(facts):
    """For each player and each rate: is it higher in the rounds they won?"""
    out = []
    for f, short, phrase, gloss in _RATES:
        for pl in _players(facts):
            other = [p for p in _players(facts) if p != pl][0]
            rw, nw, dw = _rate_x1000(facts, pl, f, True)
            rl, nl, dl = _rate_x1000(facts, pl, f, False)
            if not dw or not dl or rw == rl:
                continue
            gap = abs(rw - rl)
            # The threshold has to be RELATIVE. KPP sits around 3.6 and DS around
            # 0.19, so one absolute cutoff either dismisses real DS differences as
            # noise or promotes KPP rounding into a finding.
            base = min(rw, rl) or 1
            gap_pct = (gap * 100) // base
            # numerator/denominator sums restricted to won and lost rounds
            n_won = sum_round_where(pl, f, c_winner(pl))
            p_won = sum_round_where(pl, "pieces", c_winner(pl))
            n_lost = sum_round_where(pl, f, c_winner(other))
            p_lost = sum_round_where(pl, "pieces", c_winner(other))

            if gap_pct < 5:
                # A gap this small is not a lever — say so instead of dressing it up
                # as a finding. Proved as a bound on the cross-multiplied difference.
                bound = gap + 10
                bigger = (mul(n_lost, p_won) if rl > rw else mul(n_won, p_lost))
                smaller = (mul(n_won, p_lost) if rl > rw else mul(n_lost, p_won))
                out.append({
                    "family": f"rate_flat_{f}", "category": "finesse",
                    "canto": f"{pl} 嘅 {short}（{phrase}）贏局同輸局幾乎一樣，"
                             f"差距唔夠 {_bound_dp(bound)}（即係唔到 {gap_pct + 1}%），"
                             f"所以 {short} 唔係佢輸贏嘅關鍵",
                    "english_gloss": (f"{pl}'s {gloss} barely differs between rounds won "
                                      f"and lost (under {_bound_dp(bound)}, "
                                      f"~{gap_pct}%) — not the lever"),
                    "spec": lt(mul(sub(bigger, smaller), lit(1000)),
                               mul(lit(bound), mul(p_won, p_lost))),
                })
            else:
                higher_when_winning = rw > rl
                verb = "高" if higher_when_winning else "低"
                read = ("即係話佢贏嘅時候係靠每粒方塊打得更重，唔係靠落多啲方塊"
                        if higher_when_winning and f == "garbage_attack" else
                        "贏嘅時候花多啲方塊落去清垃圾，守得住先贏得到"
                        if higher_when_winning and f == "garbage_cleared" else
                        "輸嘅局清得更多，即係一路捱打、淨係顧住清垃圾"
                        if not higher_when_winning and f == "garbage_cleared" else
                        "輸嘅時候手法反而更亂" if not higher_when_winning and f == "inputs" else
                        "值得留意")
                out.append({
                    "family": f"rate_split_{f}", "category":
                        ("attack" if f == "garbage_attack" else
                         "finesse" if f == "inputs" else "style"),
                    "canto": f"{pl} 贏嘅局嘅 {short}（{phrase}）約 {_two_dp(rw)}，"
                             f"輸嘅局約 {_two_dp(rl)}，"
                             f"贏局{verb}咗大約 {gap_pct}% —— {read}",
                    "english_gloss": (f"{pl}'s {gloss}: {_three_dp(rw)} in rounds won vs "
                                      f"{_three_dp(rl)} in rounds lost"),
                    "spec": (gt(mul(n_won, p_lost), mul(n_lost, p_won))
                             if higher_when_winning
                             else gt(mul(n_lost, p_won), mul(n_won, p_lost))),
                })
    return out


@family
def app_decides_rounds(facts):
    """Both players' APP rises in the rounds they win — the cross-player read."""
    hits = []
    for pl in _players(facts):
        rw, _, dw = _rate_x1000(facts, pl, "garbage_attack", True)
        rl, _, dl = _rate_x1000(facts, pl, "garbage_attack", False)
        if dw and dl and rw > rl:
            hits.append(pl)
    if len(hits) != len(_players(facts)):
        return []
    parts = []
    for pl in hits:
        other = [p for p in _players(facts) if p != pl][0]
        parts.append(gt(mul(sum_round_where(pl, "garbage_attack", c_winner(pl)),
                            sum_round_where(pl, "pieces", c_winner(other))),
                        mul(sum_round_where(pl, "garbage_attack", c_winner(other)),
                            sum_round_where(pl, "pieces", c_winner(pl)))))
    return [{
        "family": "app_decides_rounds", "category": "attack",
        "canto": "兩個人都一樣：贏嘅局嘅 APP 高過輸嘅局。"
                 "呢個 session 決定一局嘅唔係手速，而係每粒方塊嘅傷害",
        "english_gloss": ("both players' attack per piece is higher in the rounds they "
                          "won than in the rounds they lost"),
        "spec": conj(*parts),
    }]


@family
def ds_session_comparison(facts):
    """Session-level downstack rate — who spends more of each piece on defence."""
    a, b = _players(facts)
    ca, cb = _tot(facts, a, "garbage_cleared"), _tot(facts, b, "garbage_cleared")
    pa, pb = _tot(facts, a, "pieces"), _tot(facts, b, "pieces")
    if ca * pb == cb * pa:
        return []
    hi, lo = (a, b) if ca * pb > cb * pa else (b, a)
    return [{
        "family": "ds_session", "category": "style",
        "canto": f"全 session 計每粒方塊清走幾多垃圾（DS）：{hi} 高過 {lo}，"
                 f"即係 {hi} 花多啲方塊落喺守同清垃圾上面",
        "english_gloss": f"session downstack per piece: {hi} higher than {lo}",
        "spec": gt(mul(sum_round(hi, "garbage_cleared"), sum_round(lo, "pieces")),
                   mul(sum_round(lo, "garbage_cleared"), sum_round(hi, "pieces"))),
    }]


@family
def unqualified_rate_peaks(facts):
    """The unqualified maximum of each rate — kept, but stated as a burst.

    `round_superlatives` qualifies APM and VS at QUALIFYING_MS, which is right for
    a record and wrong for coverage: it restricts the "nobody exceeds it" conjuncts
    to qualifying rounds, so a short round's rate constant is left with no upper
    bound. Its only other constraint is "the round's winner had the higher VS",
    which every INCREASE preserves. `mutation_test.sh` found exactly that hole the
    first time this ran — `m6_r1_yachi_vs` survived +1 and x10.

    So the unqualified peak stays in the ledger as its own claim, bounding every
    round again, and says what it actually is. It is emitted only when the peak
    round is NOT a qualifying one; otherwise it would duplicate the record claim's
    predicate, which `validate` rejects.

    Defined last on purpose: FAMILIES runs in definition order and ids are assigned
    over the flattened output, so appending here leaves every existing claim id —
    and therefore every badge already published in four reports — untouched.
    """
    out = []
    qual_secs = QUALIFYING_MS // 1000
    for f, scaled, cat, noun, fmt, qualify in _SUPERLATIVES:
        if not qualify:
            continue
        ranked = _rank_desc(facts, lambda p, f=f: p[f])
        mi, ri, pl, v = ranked[0]
        if v <= 0:
            continue
        if _dur(facts["matches"][mi]["rounds"][ri]) >= QUALIFYING_MS:
            continue          # the peak IS the record; one claim already covers it
        winner = facts["matches"][mi]["rounds"][ri]["winner"]
        dur_s = _dur(facts["matches"][mi]["rounds"][ri]) // 1000
        approx = "約" if scaled else ""
        out.append({
            "family": f"round_peak_{f}", "category": cat,
            "canto": f"唔設任何局長下限嘅話，全場最高{noun}係 {pl} 喺 {_ordinal(mi)} 第 "
                     f"{ri + 1} 局打出嘅 {approx}{fmt(v)}，但嗰局只打咗 {dur_s} 秒——"
                     f"速率嘅分母就係局長，所以呢個數唔算紀錄，"
                     f"紀錄只計打足 {qual_secs} 秒嘅局",
            "english_gloss": (f"unqualified session peak {f} is {v} by {pl} at "
                              f"m{mi + 1}r{ri + 1}, a {dur_s}s round — not the record"),
            "spec": conj(
                eq(rnd(mi, ri, pl, f), lit(v)),
                # over EVERY round this time: this is what re-bounds the short ones
                eq(count_rounds(c_field(_players(facts)[0], f, ">", v)), lit(0)),
                eq(count_rounds(c_field(_players(facts)[1], f, ">", v)), lit(0)),
                round_winner(mi, ri, winner),
                # and that the round really is a short one, so the sentence's
                # reason for demoting it is proved rather than asserted
                eq(count_rounds(c_and(c_dur("<", QUALIFYING_MS),
                                      c_field(pl, f, "==", v))), lit(1)),
            ),
        })
    return out


@family
def perfect_clears(facts):
    """全消 — not how many, but whether the round that held one was won.

    `clear_mix` already counts All Clears per player, and a count on its own reads as an
    achievement list. The question a report has to answer is what the achievement bought,
    and this session pair answers it with a shape the totals cannot show: a Perfect Clear
    is a large one-off attack, and the round it lands in is won about as often as any
    other. Two claims per player say that with counts a solver can refute:

      * rounds holding at least one of the player's Perfect Clears, and how many of those
        the player won — printed beside the session's own round record, because "won 7 of
        12" means nothing without "won 43 of 79" next to it. The comparison is left to the
        reader as four integers rather than folded into a rate: the denominators here are
        3-12 rounds, and a percentage over 3 rounds invites a conclusion the sample cannot
        carry.
      * rounds where the player was the ONLY one to get a Perfect Clear and still lost.
        This is the sharp form, because it removes the obvious confound — a round both
        players cleared out is not evidence either way — and it is a count of individually
        checkable rounds rather than a rate.

    Skipped entirely for a session with no Perfect Clear: `count_rounds(...) == 0` would be
    a claim no mutation of any allclear counter can falsify (raising one to 1 makes the
    predicate false, but so does every other claim about that round), and a family whose
    lemma is decorative is worse than a family that stays quiet.
    """
    pls = _players(facts)
    rows = _rounds(facts)
    if not any(r["players"][p]["clears"]["allclear"] for _, _, r in rows for p in pls):
        return []
    out = []
    total = len(rows)
    for pl in pls:
        other = [p for p in pls if p != pl][0]
        mine = [r for _, _, r in rows if r["players"][pl]["clears"]["allclear"] > 0]
        won = sum(1 for r in mine if r["winner"] == pl)
        wins = _round_wins(facts)[pl]
        if not mine:
            continue
        out.append({
            "family": "pc_rounds", "category": "style",
            "canto": f"{pl} 有 {len(mine)} 局做到 Perfect Clear，入面贏咗 {won} 局；"
                     f"佢成晚打 {total} 局贏 {wins} 局",
            "english_gloss": (f"{pl} had a perfect clear in {len(mine)} rounds and won {won} "
                              f"of them; {wins} round wins out of {total} overall"),
            "spec": conj(
                eq(count_rounds(c_field(pl, "clears.allclear", ">", 0)), lit(len(mine))),
                eq(count_rounds(c_and(c_field(pl, "clears.allclear", ">", 0),
                                      c_winner(pl))), lit(won)),
                eq(count_rounds_won(pl), lit(wins)),
                eq(total_rounds(), lit(total)),
            ),
        })
        solo = [r for r in mine if r["players"][other]["clears"]["allclear"] == 0]
        lost = sum(1 for r in solo if r["winner"] == other)
        if not solo:
            continue
        out.append({
            "family": "pc_solo_lost", "category": "style",
            "canto": f"有 {len(solo)} 局係全場淨係 {pl} 做到 Perfect Clear，"
                     f"入面佢仲要輸咗 {lost} 局",
            "english_gloss": (f"{len(solo)} rounds where only {pl} got a perfect clear; "
                              f"{pl} lost {lost} of them"),
            "spec": conj(
                eq(count_rounds(c_and(c_field(pl, "clears.allclear", ">", 0),
                                      c_field(other, "clears.allclear", "==", 0))),
                   lit(len(solo))),
                eq(count_rounds(c_and(c_field(pl, "clears.allclear", ">", 0),
                                      c_field(other, "clears.allclear", "==", 0),
                                      c_winner(other))), lit(lost)),
            ),
        })
    return out
