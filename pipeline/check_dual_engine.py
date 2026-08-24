"""The `dual_engine` corpus figures: rolled up from the seven artefacts, never typed into prose.

WHY THIS FAMILY WAS THE ONE LEFT. CLAUDE.md's 第二個引擎 section publishes seventeen figures — a
confusion matrix, its board-equality split, two coverage figures and the two engines' prefix
lengths — and on 2026-08-24 every one of them was correct. That is exactly what made it the next
item rather than a closed one: **correct-today is the normal state of a figure with no gate.** The
same section's history says so twice over. `emit-opener-facts.ts` carried a five-session copy of
these numbers, which survived the sixth session for two days; the six-session copy that replaced it
sat under a sentence promising "every figure in this block is the sum over the six committed
sim/opener-facts.json, not a remembered one" and was wrong the moment the seventh landed.

THE SPLIT IS THE FINDING AND THE GATE ENFORCES ITS SHAPE, not just its digits:

* **the rate is never the sentence.** Both verdicts are rare, so `agreement_overall` is negatives
  agreeing with negatives — `_invariants` requires `both_no` to be the overwhelming majority of the
  donation's agreements, which is what makes the overall rate uninformative, and fails if that ever
  stops being true while the section still prints the rate.
* **the cave's row is a different claim from the donation's.** Agreeing on differing boards is the
  verdict being ROBUST to board drift, not independent confirmation. The two are rendered from
  different fragments so neither sentence can be reworded into the other's shape.
* **coverage bounds everything.** The hand-port verifies a far shorter prefix, so the comparison
  reaches well under half the scored clears. `prefix_locks` is why, and it is emitted rather than
  described — it used to be "27 locks against 81 on average" in a comment and in CLAUDE.md, with
  nothing anywhere re-deriving either. Measured: 26.2 and 80.4. The 81 was rounded in the direction
  that made the gap look bigger, which is the fourth figure on this branch to fail that way.

ROUNDING IS PER CLAIM, NOT PER NUMBER — the rule this repo learned on `rate_records.R`. A figure
quoted to show a rate is MISLEADINGLY HIGH is ceiled, so the debunk survives the most generous
reading; one quoted to show agreement is LOW is ceiled for the same reason; a share quoted to show
how many boards DIFFER is floored. `_q`'s `how` argument records the direction beside every figure,
and `--selftest` plants a mutant for each.
"""
import argparse
import json
import math
import sys

from .check_donation_bands import REGEN, REPO, opener_artefacts
from .docs_gate import (Incomplete, fragment_mutants, fragment_problems, load_docs,
                        render_fragments, reword)

DOCS = ("CLAUDE.md",)
NS = "dual:"
#: `both_no` must be at least this share of the donation's agreements for the "the overall rate is
#: negatives agreeing with negatives" sentence to be true. Deliberately NOT today's 0.9943: a
#: threshold set to the current measurement is a copy of the measurement. 0.99 is the bound
#: `openers.test.ts` already asserts, so the two say the same thing in two places on purpose.
_MIN_BOTH_NO_SHARE = 0.99


def _q(x, dp, how):
    """`x` to `dp` places, rounded in the direction the CLAIM needs. See the module docstring."""
    f = 10 ** dp
    if how == "floor":
        v = math.floor(x * f) / f
    elif how == "ceil":
        v = math.ceil(x * f) / f
    else:
        v = math.floor(x * f + 0.5) / f
    return f"{v:.{dp}f}"


def roll_up(root=REPO):
    """Every dual_engine figure, summed over the committed artefacts. Counts in, counts out."""
    whole, excluded = opener_artefacts(root)
    t, hist, sessions = {}, {}, []

    def add(k, v):
        t[k] = t.get(k, 0) + v

    for s, art in whole:
        d = art["donation"]["dual_engine"]
        missing = [k for k in ("prefix_locks", "board_diff_hist") if k not in d]
        if missing:
            # Never a skip — an artefact predating a field would silently shrink the corpus a
            # figure is measured over, and a smaller corpus reads exactly like the full one.
            excluded.append((s, f"its dual_engine has no {' and no '.join(missing)} — "
                                f"re-emit it: {REGEN}"))
            continue
        # The two metrics embed the SAME dual_engine object. Checked rather than assumed, because
        # reading one and publishing it as the other would be invisible while they agree.
        if art["stmb_cave"]["dual_engine"] != d:
            excluded.append((s, "donation.dual_engine and stmb_cave.dual_engine differ, so "
                                "'the dual-engine check' names two different things"))
            continue
        sessions.append(s)
        for k in ("locks_scored", "locks_comparable", "locks_same_board"):
            add(k, d[k])
        for k, v in d["prefix_locks"].items():
            add("pf_" + k, v)
        for k, v in d["board_diff_hist"].items():
            hist[int(k)] = hist.get(int(k), 0) + v
        for m in ("donation", "cave"):
            for k in ("both_yes", "both_no", "oracle_positives"):
                add(f"{m}_{k}", d[m][k])
            add(f"{m}_agree", d[m]["agreement_overall"][0])
            add(f"{m}_of", d[m]["agreement_overall"][1])
            for k, v in d["board_split"]["don" if m == "donation" else m].items():
                add(f"{m}_{k}", v)
        add("caves", sum(p["width_ge_3"] for p in art["stmb_cave"]["players"]))
        add("donations", sum(p["donations"] for p in art["donation"]["players"]))
    t["sessions"], t["hist"] = sessions, hist
    return t, excluded


def _median(hist):
    """The corpus median of a count histogram — the reason the artefacts emit the histogram."""
    n = sum(hist.values())
    if not n:
        raise Incomplete("no comparison point put the two engines on differing boards, so there is "
                         "no median board difference to publish")
    seen = 0
    for x in sorted(hist):
        seen += hist[x]
        if seen * 2 >= n:
            return x
    raise AssertionError("unreachable: the cumulative count must reach half the total")


def _invariants(t):
    """What must hold before any of these figures is worth rendering."""
    bad = []
    if not t["sessions"]:
        bad.append("no artefact carries a usable dual_engine block")
        return bad
    # (1) The comparison is bounded by the SHORTER prefix, which is the hand-port's. If that ever
    # stopped being true the coverage sentence would be describing the wrong engine.
    if t["pf_hand_port_locks"] >= t["pf_oracle_locks"]:
        bad.append(f"the hand-port verifies {t['pf_hand_port_locks']} locks against the oracle's "
                   f"{t['pf_oracle_locks']}, so it is no longer the shorter prefix and the "
                   f"coverage sentence names the wrong engine")
    if t["locks_comparable"] > t["locks_scored"]:
        bad.append(f"{t['locks_comparable']} comparison points against {t['locks_scored']} scored "
                   f"clears — the comparison cannot reach past what is scored")
    if t["locks_same_board"] > t["locks_comparable"]:
        bad.append(f"{t['locks_same_board']} same-board points against {t['locks_comparable']} "
                   f"comparison points")
    # (2) The differing-board histogram must account for EXACTLY the comparison points that are not
    # same-board. A histogram that lost points would move the median silently.
    diff = t["locks_comparable"] - t["locks_same_board"]
    if sum(t["hist"].values()) != diff:
        bad.append(f"the board-diff histogram holds {sum(t['hist'].values())} points against "
                   f"{diff} comparison points on differing boards — it is not the same population")
    if 0 in t["hist"]:
        bad.append("the board-diff histogram bins a difference of 0, which is a SAME board and is "
                   "already counted by locks_same_board — binning it puts a mode at 0 in a "
                   "distribution whose subject is the non-zero tail")
    # (3) THE SENTENCE THE SECTION RESTS ON. "The overall rate is negatives agreeing with
    # negatives" is only true while both_no dominates the agreements. Bound, not measurement.
    share = t["donation_both_no"] / t["donation_agree"] if t["donation_agree"] else 0
    if share < _MIN_BOTH_NO_SHARE:
        bad.append(f"both_no is {share:.4f} of the donation's agreements, under "
                   f"{_MIN_BOTH_NO_SHARE} — the section says the overall rate is negatives "
                   f"agreeing with negatives, and at this share that sentence is no longer true")
    # (4) The split must partition the positives, both ways. A split that dropped one would make
    # "the disagreement is the board" rest on a subset nobody named.
    for m in ("donation", "cave"):
        parts = t[f"{m}_positives_same_board"] + t[f"{m}_positives_diff_board"]
        if parts != t[f"{m}_oracle_positives"]:
            bad.append(f"{m}: the board split holds {parts} positives against "
                       f"{t[f'{m}_oracle_positives']} — the split is not a partition")
        agree = t[f"{m}_agree_same_board"] + t[f"{m}_agree_diff_board"]
        if agree != t[f"{m}_both_yes"]:
            bad.append(f"{m}: the board split holds {agree} agreements against "
                       f"{t[f'{m}_both_yes']} both-yes")
    return bad


def _pair(t, m):
    return f"{t[f'{m}_both_yes']} / {t[f'{m}_oracle_positives']}"


def _row(t, m):
    """One row of the board-equality table — rendered whole so the five cells cannot drift apart."""
    return (f"{t[f'{m}_oracle_positives']} | {t[f'{m}_positives_same_board']} | "
            f"{t[f'{m}_both_yes']}/{t[f'{m}_oracle_positives']} | "
            f"{t[f'{m}_agree_same_board']}/{t[f'{m}_positives_same_board']} | "
            f"{t[f'{m}_agree_diff_board']}/{t[f'{m}_positives_diff_board']}")


#: key -> (renderer, documents). Each `how` records which direction the CLAIM beside it needs.
SPECS = {
    # "both verdicts are rare" — the two numerators against the denominator they sit in
    NS + "rare": (lambda t: f"{t['caves']} caves and {t['donations']} donations in "
                            f"{t['locks_scored']} scored clears", DOCS),
    # Every comparable lock passes the strong reconstruction licence — the figure that says
    # `dualVerdict` uses the shipped path's check and not a weaker one. Rendered as the pair it is
    # published as, because a bare 2019 would be a second copy of the denominator above.
    NS + "strong-licence": (lambda t: f"{t['locks_comparable']} of {t['locks_comparable']}", DOCS),
    NS + "coverage": (lambda t: f"{t['locks_comparable']} of {t['locks_scored']}", DOCS),
    # the hand-port's prefix CEILS and the oracle's FLOORS: at the most generous reading of the
    # short one and the least generous of the long one, it is still three times shorter.
    NS + "prefix": (lambda t: f"{_q(t['pf_hand_port_locks'] / t['pf_rounds'], 1, 'ceil')} locks "
                              f"against {_q(t['pf_oracle_locks'] / t['pf_rounds'], 1, 'floor')}",
                    DOCS),
    # the confusion matrix
    NS + "cave-overall": (lambda t: f"{t['cave_agree']}/{t['cave_of']} "
                                    f"({_q(100 * t['cave_agree'] / t['cave_of'], 0, 'floor')}%)",
                          DOCS),
    NS + "cave-pos": (lambda t: _pair(t, "cave"), DOCS),
    # CEILED: the sentence's job is to debunk this rate, so the debunk must survive its highest
    # reading. Same for the donation's agreement share below.
    NS + "don-overall": (lambda t: f"{t['donation_agree']}/{t['donation_of']} "
                                   f"({_q(100 * t['donation_agree'] / t['donation_of'], 1, 'ceil')}%)",
                         DOCS),
    NS + "don-pos": (lambda t: _pair(t, "donation"), DOCS),
    NS + "don-pos-pct": (lambda t: _q(100 * t["donation_both_yes"] / t["donation_oracle_positives"],
                                      1, "ceil") + "%", DOCS),
    NS + "don-bothno": (lambda t: f"{t['donation_both_no']} of {t['donation_agree']}", DOCS),
    # FLOORED: quoted to show the share is close to 1, so the claim must hold at its lowest reading
    NS + "bothno-share": (lambda t: _q(t["donation_both_no"] / t["donation_agree"], 4, "floor"),
                          DOCS),
    NS + "cave-of-corpus": (lambda t: f"{t['cave_oracle_positives']} of the corpus's {t['caves']}",
                            DOCS),
    # the board split
    NS + "same-board": (lambda t: f"{t['locks_same_board']} of the {t['locks_comparable']}", DOCS),
    # FLOORED: quoted to show how MANY differ, so it must hold at its lowest reading
    NS + "diff-share": (lambda t: _q(100 * (t["locks_comparable"] - t["locks_same_board"])
                                     / t["locks_comparable"], 1, "floor") + "%", DOCS),
    NS + "diff-median": (lambda t: str(_median(t["hist"])), DOCS),
    NS + "row-cave": (lambda t: _row(t, "cave"), DOCS),
    NS + "row-don": (lambda t: _row(t, "donation"), DOCS),
}


def problems(t, docs):
    out = []
    for name, text in docs.items():
        out += fragment_problems(name, text, SPECS, t, reword("pipeline/check_dual_engine.py"),
                                 namespace=NS)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    t, excluded = roll_up()
    for s, why in excluded:
        print(f"  not measured: {s} — {why}")
    bad = _invariants(t)
    if bad:
        for b in bad:
            print("  " + b)
        return 1
    if args.render:
        for name in DOCS:
            print(f"# {name}")
            print(render_fragments(SPECS, t, name), end="")
        return 0
    docs = load_docs(REPO, DOCS)
    bad = problems(t, docs)
    for b in bad:
        print("  " + b)
    print(f"dual engine: {len(t['sessions'])} sessions, {t['locks_comparable']} of "
          f"{t['locks_scored']} clears comparable; cave {_pair(t, 'cave')} on the positives, "
          f"donation {_pair(t, 'donation')}; {t['locks_same_board']} same-board, median "
          f"{_median(t['hist'])} cells apart — {len(bad)} problem(s)")
    return 1 if bad else 0


def selftest():
    t, _ = roll_up()
    docs = load_docs(REPO, DOCS)
    ok = True

    def case(label, fn, must_fail=True):
        nonlocal ok
        good = bool(fn()) == must_fail
        ok = ok and good
        print(f"  {'ok  ' if good else 'BAD '} {label}")

    def bend(**kw):
        m = dict(t)
        m["hist"] = dict(t["hist"])
        m.update(kw)
        return _invariants(m)

    case("the committed CLAUDE.md agrees with the artefacts", lambda: problems(t, docs), False)
    case("the committed artefacts satisfy the invariants", lambda: _invariants(t), False)

    # ── the invariants, one mutant each
    case("the hand-port is no longer the shorter prefix",
         lambda: bend(pf_hand_port_locks=t["pf_oracle_locks"] + 1))
    case("more comparison points than scored clears",
         lambda: bend(locks_comparable=t["locks_scored"] + 1))
    case("more same-board points than comparison points",
         lambda: bend(locks_same_board=t["locks_comparable"] + 1))
    case("the diff histogram loses a point",
         lambda: bend(hist={**t["hist"], min(t["hist"]): t["hist"][min(t["hist"])] - 1}))
    case("the diff histogram bins a same board", lambda: bend(hist={**t["hist"], 0: 1}))
    case("both_no stops dominating the donation's agreements",
         lambda: bend(donation_both_no=int(t["donation_agree"] * 0.9)))
    case("the board split drops a positive",
         lambda: bend(donation_positives_diff_board=t["donation_positives_diff_board"] - 1))
    case("the board split drops an agreement",
         lambda: bend(cave_agree_diff_board=t["cave_agree_diff_board"] - 1))

    # ── the rounding DIRECTIONS. Each figure is re-rendered with the opposite rule and must differ
    # from the committed one, or the direction is unobservable here and the comment claiming it is
    # decorative. A `--` result is honest: it names a figure this corpus cannot discriminate.
    for key, x, dp, how in (
            (NS + "don-overall", 100 * t["donation_agree"] / t["donation_of"], 1, "ceil"),
            (NS + "don-pos-pct", 100 * t["donation_both_yes"] / t["donation_oracle_positives"],
             1, "ceil"),
            (NS + "bothno-share", t["donation_both_no"] / t["donation_agree"], 4, "floor"),
            (NS + "diff-share", 100 * (t["locks_comparable"] - t["locks_same_board"])
             / t["locks_comparable"], 1, "floor"),
            (NS + "prefix", t["pf_oracle_locks"] / t["pf_rounds"], 1, "floor")):
        other = "floor" if how == "ceil" else "ceil"
        if _q(x, dp, how) == _q(x, dp, other):
            print(f"  --   {key}: this corpus does not discriminate {how} from {other} "
                  f"({_q(x, dp, how)}), so the direction is unchecked here")
        else:
            print(f"  ok   {key}: {how} gives {_q(x, dp, how)}, {other} gives {_q(x, dp, other)}")

    # ── the fragments
    n = 0
    for label, name, text, must in fragment_mutants(SPECS, t, DOCS, lambda k: docs[k], namespace=NS):
        d = dict(docs)
        d[name] = text
        if bool(problems(t, d)) != must:
            ok = False
            print(f"  BAD  {label}")
        n += 1
    print(f"  {'ok  ' if ok else 'BAD '} {n} fragment mutants")
    print("selftest: " + ("ok" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
