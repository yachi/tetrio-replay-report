"""Gate: every corpus figure CLAUDE.md publishes about the three stat objects.

    python3 -m pipeline.check_stat_sources            # re-derive and compare
    python3 -m pipeline.check_stat_sources --render   # the fragments, ready to paste
    python3 -m pipeline.check_stat_sources --selftest # plant corruptions, require catches

Two long bullets in CLAUDE.md are almost entirely counts of how often a round's three stat
objects disagree — `player.stats` (a live tick), `results.stats` (the final snapshot) and
`results.aggregatestats` (the final rate triple). Every count was measured once by hand over
the **760** player-rounds of the first six sessions and typed into prose. The corpus reached
900 and nothing said so.

This is the 冇第二份 class at its purest, and the reason it is the hardest one the document
carries: **the sentences were not wrong.** Each said, in as many words, that it was measured
over the first six sessions and had not been re-run. A caveat is honest and it is not a
measurement — nothing goes red, the figure stays published, and it reads exactly like a
number somebody still stands behind.

So each figure is a MARKED FRAGMENT (`pipeline/docs_gate.py`), byte-compared against
`analysis/stat_sources.py`, which globs the replays off disk and carries no session list.
The prose around each fragment is free; only the figure is pasted.

**Bounds CEIL, and that changed five published numbers.** `1.81899e-12` was published as
`1.8e-12`, `2.43096e-16` as `2.4e-16`, `6.13187e-16` as `6.1e-16`, `1.51976e-3` as `1.5e-3`
and `1.25354e-3` as `1.2e-3` — every one of them rounded DOWN, i.e. each asserted a tighter
bound than the data supports. That is the rule `pipeline/fmt._bound_dp` already states for
the reports ("an upper bound is the one figure that must round the other way") applied here:
`_bound` below ceils at two significant figures. The corrections are tiny and the class is
not — this repo has shipped 「差距唔夠 0.01」 against a lemma proving only 0.015 before.

**The control that says this module IS the original measurement.** Restricted to the six
sessions the figures were measured on, the derivation reproduces every published integer
exactly: 183, 181, 172, 257, 245, 201, 7, 1, 758, 11865, 7510, 650, 750, 760, 98. `--selftest`
runs it. One of those needed the definition corrected rather than the figure: 「245 of the
760」 is 245 only when the residual is maximised over ALL THREE rates — VS and APM alone give
243. `aggregatestats` is a triple, so a route claiming to reconstruct it has to reconstruct
the triple, and the hand measurement was right where the first re-derivation was not.

**And every float bound is IDENTICAL at six sessions and at seven** — the worst-case rounds
all sit in the first six. Only the counts moved. That is what "the ratios are what to carry
forward, not the numerators" meant, sharper than it was written.
"""
import argparse
import math
import os
import sys

from analysis.stat_sources import derive
from .docs_gate import (Incomplete, fragment_mutants, fragment_problems, load_docs,
                        render_fragments, reword)

DOCS = ("CLAUDE.md",)
REWORD = reword("pipeline/check_stat_sources.py")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The six-session values every figure was published as. Not decoration: they are the control
# that this module measures the same thing the hand pass did, and one of them (245) is why the
# residual is maximised over three rates instead of one.
SIX = ("2026-07-22", "2026-07-24", "2026-07-28", "2026-08-01", "2026-08-09", "2026-08-14")
PUBLISHED_AT_SIX = {
    "player_rounds": 760, "tick_stale": 183, "tick_stale_survivor": 181, "tick_apm_high": 172,
    "floor_wrong": 257, "secs_over_1e4": 245, "kills_disagree": 201,
    "kills_live1_final0_survivor": 201, "garbagesent_differ": 7, "garbagereceived_differ": 1,
    "identity_rounds": 758, "finesse_faults": 11865, "finesse_nonperfect": 7510,
    "finesse_faults_exceed": 650, "finesse_nonperfect_rounds": 750, "leaderboard_entries": 98,
}


def _bound(x, sig=2):
    """Ceil at `sig` significant figures, in the `1.6e-3` shape the prose uses.

    CEIL, never round: these are all 「up to X」 / 「≤X」 statements, and a bound rounded down
    is a sentence stronger than its measurement.
    """
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    scale = 10 ** (sig - 1 - e)
    m = math.ceil(abs(x) * scale) / scale
    e2 = math.floor(math.log10(m))                 # 9.99e-3 ceils to 1.0e-2
    return f"{m / 10 ** e2:.1f}e{e2}"


def _thousands(n):
    """`13 964` — a space, which is how the pooled finesse figures are written."""
    return f"{n:,}".replace(",", " ")


def _worst_finesse(d):
    """`07-24 m2r0 puts 7 faults on a single non-perfect piece`.

    The `m` is the replay's EXPORT number out of the filename, not the match's position in
    the session — the two agreed by accident until 2026-08-01 and this is the filename form
    the sentence has always used. Derived, so it moves if the round does.
    """
    path, ri, _user, faults, nonperf = d["finesse_worst_round"]
    stem = os.path.splitext(path)[0].split("-")
    return (f"{stem[2]}-{stem[3]} m{stem[4]}r{ri} puts {faults} fault"
            f"{'s' if faults != 1 else ''} on a single non-perfect piece"
            if nonperf == 1 else
            f"{stem[2]}-{stem[3]} m{stem[4]}r{ri} puts {faults} faults on {nonperf} "
            f"non-perfect pieces")


FRAGMENTS = {
    # --- the live tick against the final rate triple
    # The corpus size is published at three sites. Each gets its own key, because "exactly
    # one pair" is per key — one shared key would make two of the three a duplicate and fail.
    "stat:corpus": (lambda d: f"{d['player_rounds']} player-rounds", DOCS),
    "stat:corpus-agg": (lambda d: f"{d['player_rounds']} player-rounds", DOCS),
    "stat:corpus-frames": (lambda d: str(d["player_rounds"]), DOCS),
    "stat:tick-stale": (lambda d: f"{d['tick_stale']} of {d['player_rounds']}", DOCS),
    "stat:tick-stale-survivor": (lambda d: str(d["tick_stale_survivor"]), DOCS),
    # --- T from pps, and the residuals it leaves
    "stat:resid-worst": (lambda d: _bound(max(d["resid_apm"], d["resid_vs"])), DOCS),
    "stat:resid-pair": (lambda d: f"{_bound(d['resid_apm'])} for APM and "
                                  f"{_bound(d['resid_vs'])} for VS", DOCS),
    "stat:frames-integer": (lambda d: _bound(d["frames_integer_to"]), DOCS),
    # --- the two finaltime routes that do not work
    "stat:floor-wrong": (lambda d: f"{d['floor_wrong']} of the {d['player_rounds']}", DOCS),
    "stat:floor-worst": (lambda d: _bound(d["floor_worst"]), DOCS),
    "stat:secs-worst": (lambda d: _bound(d["secs_worst"]), DOCS),
    "stat:secs-over": (lambda d: f"{d['secs_over_1e4']} of the {d['player_rounds']}", DOCS),
    # --- the T-free identity, which is the checkable form
    # Values, never markup: a fragment carrying `**` would make the gate the arbiter of the
    # document's emphasis, and a reword of the bold would then be a code change.
    "stat:identity": (lambda d: _bound(d["identity_worst"]), DOCS),
    "stat:identity-rounds": (lambda d: str(d["identity_rounds"]), DOCS),
    # --- kills, and the two garbage counters
    "stat:kills": (lambda d: f"{d['kills_disagree']} of {d['player_rounds']}", DOCS),
    "stat:garbage-differ": (lambda d: f"{d['garbagesent_differ']} and "
                                      f"{d['garbagereceived_differ']} of {d['player_rounds']}",
                            DOCS),
    # --- finesse: two units, four rates, one of them on no meaningful denominator
    "stat:finesse-pool": (lambda d: f"{_thousands(d['finesse_faults'])} faults over "
                                    f"{_thousands(d['finesse_nonperfect'])} non-perfect pieces",
                          DOCS),
    "stat:finesse-per-piece": (lambda d: f"{d['finesse_per_faulty_piece']:.3f}", DOCS),
    "stat:finesse-fault-rate": (lambda d: f"{d['finesse_fault_rate']:.2f}%", DOCS),
    "stat:finesse-share": (lambda d: f"{d['finesse_faulty_share']:.2f}%", DOCS),
    "stat:finesse-tetrio": (lambda d: f"{d['finesse_tetrio_figure']:.2f}%", DOCS),
    "stat:finesse-meaningless": (lambda d: f"{d['finesse_meaningless']:.2f}%", DOCS),
    "stat:finesse-exceed": (lambda d: f"{d['finesse_faults_exceed']} of "
                                      f"{d['finesse_nonperfect_rounds']}", DOCS),
    "stat:finesse-worst": (_worst_finesse, DOCS),
    # --- the VS-split guard. NOT a re-pool: whether it still fires at 900 is the question,
    # and the answer is a count of firings, so it is derived per round and reported as one.
    "stat:vs-guard": (lambda d: f"{d['vs_guard_fires']} of {d['vs_guard_rounds']}", DOCS),
    "stat:vs-guard-worst": (lambda d: f"{d['vs_guard_worst_frac']:.3f} of the trigger "
                                      f"(~{d['vs_guard_headroom']:.0f}× headroom)", DOCS),
    "stat:vs-guard-need": (lambda d: f"~{d['vs_guard_would_need']} against its actual "
                                     f"{d['vs_guard_worst'][4]}", DOCS),
    # --- why the leaderboard rollup stays on the live tick
    "stat:leaderboard-agg": (lambda d: f"{d['leaderboard_with_agg']} of "
                                       f"{d['leaderboard_entries']}", DOCS),
}


def problems(data, docs):
    out = []
    for name in DOCS:
        text = docs.get(name)
        if text is None:
            out.append(f"{name}: not found. {REWORD}")
            continue
        out += fragment_problems(name, text, FRAGMENTS, data, REWORD, "stat:")
    return out


def _six_session_control():
    """Re-derive restricted to the six sessions the figures were hand-measured on."""
    import analysis.stat_sources as src
    rf, fr = src.replay_files, src.facts_rounds
    src.replay_files = lambda root=src.REPO: [
        p for p in rf(root) if os.path.basename(os.path.dirname(p)) in SIX]
    src.facts_rounds = lambda root=src.REPO: [r for r in fr(root) if r["session"] in SIX]
    try:
        return src.derive()
    finally:
        src.replay_files, src.facts_rounds = rf, fr


def selftest():
    ok = True
    data = derive()

    # Control 1 — the derivation IS the hand measurement. Restricted to the six sessions the
    # figures were taken on, every published integer must come back exactly. Without this the
    # module could be measuring something adjacent and nothing would say so: at 900 rounds
    # there is no published number left to disagree with.
    six = _six_session_control()
    for key, want in sorted(PUBLISHED_AT_SIX.items()):
        good = six.get(key) == want
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} control: {key} at six sessions = {six.get(key)} "
              f"(published {want})")

    # Control 2 — the committed CLAUDE.md carries every fragment, and they agree.
    docs = load_docs(REPO, DOCS)
    live = problems(data, docs)
    ok &= not live
    print(f"  {'ok ' if not live else 'BAD'} control: the committed document agrees: "
          f"{'yes' if not live else live[0]}")

    # Control 3 — `_bound` ceils. A rounding helper that rounds is the defect this file was
    # written to correct, and it would pass every case above.
    for x, want in ((1.81899e-12, "1.9e-12"), (2.43096e-16, "2.5e-16"),
                    (6.13187e-16, "6.2e-16"), (1.51976e-3, "1.6e-3"),
                    (1.25354e-3, "1.3e-3"), (4.16852e-16, "4.2e-16"),
                    (9.99e-3, "1.0e-2"), (1.0e-3, "1.0e-3")):
        good = _bound(x) == want
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} control: _bound({x:g}) = {_bound(x)} (want {want})")

    # The planted corruptions, from docs_gate so this sweep cannot be thinner than the other
    # caller's.
    def doc_of(name):
        return "prelude\n\n" + render_fragments(FRAGMENTS, data, name) + "\npostlude\n"

    caught = planted = 0
    for label, name, text, must_fail in fragment_mutants(FRAGMENTS, data, DOCS, doc_of, "stat:"):
        planted += 1
        failed = bool(problems(data, {name: text}))
        good = failed == must_fail
        ok &= good
        caught += failed
        if not good:
            print(f"  BAD {label}: {'rejected' if failed else 'accepted'}")
    print(f"  {'ok ' if ok else 'BAD'} {planted} planted corruptions, {caught} caught")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--render", action="store_true", help="print the fragments to paste")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    data = derive()
    if args.render:
        for name in DOCS:
            print(f"=== {name} ===")
            print(render_fragments(FRAGMENTS, data, name), end="")
        return 0
    bad = problems(data, load_docs(REPO, DOCS))
    for b in bad:
        print(f"FAIL {b}", file=sys.stderr)
    if bad:
        return 1
    print(f"  ok  {len(FRAGMENTS)} figures over {data['player_rounds']} player-rounds "
          f"({data['sessions']} sessions) agree with {', '.join(DOCS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
