"""Gate: every corpus figure CLAUDE.md publishes about WHY one player's APP is higher.

    python3 -m pipeline.check_app_decomposition            # re-derive and compare
    python3 -m pipeline.check_app_decomposition --render   # the fragments, ready to paste
    python3 -m pipeline.check_app_decomposition --selftest # controls + planted corruptions

The figures were first measured on 2026-10-11 by a probe that lived only in a scratchpad — the
冇第二份 class exactly: a number in prose with nothing able to re-derive it. They are now MARKED
FRAGMENTS (`pipeline/docs_gate.py`) byte-compared against `analysis/app_decomposition.py`, which
rolls up the committed per-session `sim/attack-facts.json`.

THE CONTROL THAT THIS IS THE ORIGINAL MEASUREMENT. The scratchpad probe was a separate
implementation (it re-ran the engine itself and split the windows in its own loop), and it printed
the values in `PROBE_2026_10_11`. `--selftest` requires the committed route to reproduce every one
to the probe's printed precision — two implementations of one split agreeing, not one copied twice.
Those values are a fixed historical measurement over the sixteen sessions that existed that day;
the control restricts the roll-up to those sixteen, so a new session does not break it.

ROUNDING, per claim. Rates that mean 「at least」 floor. A signed decomposition term rounds half
up once from the exact value, because flooring a negative term overstates it. The jackknife band
floors its low end and ceils its high end, so the printed band contains every drop.
"""
import argparse
import os
import sys
from fractions import Fraction

import analysis.app_decomposition as src
from pipeline import fmt
from .docs_gate import fragment_mutants, fragment_problems, load_docs, render_fragments, reword

DOCS = ("CLAUDE.md",)
REWORD = reword("pipeline/check_app_decomposition.py")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIXTEEN = ("2026-07-22", "2026-07-24", "2026-07-28", "2026-08-01", "2026-08-09", "2026-08-14",
           "2026-08-19", "2026-08-25", "2026-09-03", "2026-09-10", "2026-09-11", "2026-09-17",
           "2026-09-18", "2026-09-19", "2026-10-03", "2026-10-09")
#: what the 2026-10-11 scratchpad probe printed (x100 per piece, 2 dp; APP 4 dp)
PROBE_2026_10_11 = {"gap": "6.06", "mix": "3.84", "value": "2.22", "opener": "2.49",
                    "mid": "3.57", "app_lo": "0.5886", "app_hi": "0.6492",
                    "tsd_mix": "4.15", "tst_mix": "3.01", "q_mix": "-2.66"}


def _rate(num, den, dp, site):
    return fmt.quant(fmt.permille(num, den, "floor", site=site), dp, "floor", site=site)


def _signed(frac, site):
    s = fmt.quantf(float(frac * 100), 2, "round", site=site)
    return s if s.startswith("-") else "+" + s


def _term(d, k):
    return next(t for t in d["decomposition"]["terms"] if t[0] == k)


def _pair(d, f):
    return f"{d['lo']['user']} {f(d['lo'])} against {d['hi']['user']} {f(d['hi'])}"


def _signs(d):
    n = d["sessions"]
    s = d["signs"]
    return (f"T-spin Doubles in {s['TSD']} of {n}, T-spin Triples in {s['TST']} of {n}, "
            f"quads in {s['Q']} of {n}")


def _by_window(k):
    def f(d):
        lo, hi = d["lo"]["user"], d["hi"]["user"]
        t = d["by_window"][k]
        return (f"{t[hi][0]} against {t[lo][0]} inside the window and "
                f"{t[hi][1]} against {t[lo][1]} after it")
    return f


def _jack(d):
    a, b = d["jackknife"]
    lo = fmt.quantf(float(a * 100), 2, "floor", site="check_app_decomposition.jack")
    hi = fmt.quantf(float(b * 100), 2, "ceil", site="check_app_decomposition.jack")
    return f"{lo} and {hi}"


FRAGMENTS = {
    "app:anchor": (lambda d: f"{d['anchor']['attack']['agree']} of {d['anchor']['attack']['rounds']} "
                             f"player-rounds for the attack total and "
                             f"{d['anchor']['counts']['agree']} of {d['anchor']['counts']['rounds']} "
                             f"for the clear-type counts", DOCS),
    "app:app": (lambda d: _pair(d, lambda p: _rate(p["attack"], p["pieces"], 3, "check_app_decomposition.app")),
                DOCS),
    "app:lpp": (lambda d: _pair(d, lambda p: _rate(p["lines"], p["pieces"], 3, "check_app_decomposition.lpp")),
                DOCS),
    "app:apl": (lambda d: _pair(d, lambda p: _rate(p["attack"], p["lines"], 3, "check_app_decomposition.apl")),
                DOCS),
    "app:gap": (lambda d: _signed(d["decomposition"]["gap"], "check_app_decomposition.gap"), DOCS),
    "app:windows": (lambda d: f"{_signed(d['decomposition']['windows']['opener'], 'check_app_decomposition.win')} "
                              f"from the first {d['window_pieces']} locks and "
                              f"{_signed(d['decomposition']['windows']['mid'], 'check_app_decomposition.win')} "
                              f"after them", DOCS),
    "app:kitagawa": (lambda d: f"{_signed(d['decomposition']['mix'], 'check_app_decomposition.kit')} of mix and "
                               f"{_signed(d['decomposition']['value'], 'check_app_decomposition.kit')} of value",
                     DOCS),
    "app:terms": (lambda d: ", ".join(f"{name} {_signed(_term(d, k)[1], 'check_app_decomposition.term')}"
                                      for k, name in (("TSD", "T-spin Doubles"), ("TST", "T-spin Triples"),
                                                      ("Q", "quads"), ("TSS", "T-spin Singles"))), DOCS),
    "app:tsd-window": (_by_window("TSD"), DOCS),
    "app:tst-window": (_by_window("TST"), DOCS),
    "app:signs": (_signs, DOCS),
    "app:jackknife": (lambda d: f"{d['matches']} single-match drops leave it between {_jack(d)}", DOCS),
}


def problems(data, docs):
    out = []
    for name in DOCS:
        text = docs.get(name)
        if text is None:
            out.append(f"{name}: not found. {REWORD}")
            continue
        out += fragment_problems(name, text, FRAGMENTS, data, REWORD, "app:")
    return out


def _probe_control():
    """The roll-up restricted to the sixteen sessions the probe measured, in the probe's format."""
    arts = src.artefacts
    src.artefacts = lambda root=src.REPO: {s: a for s, a in arts(root).items() if s in SIXTEEN}
    try:
        d = src.derive()
    finally:
        src.artefacts = arts
    dd = d["decomposition"]
    f2 = lambda x: f"{float(x) * 100:.2f}"  # noqa: E731 — the probe printed with :.2f
    return {"gap": f2(dd["gap"]), "mix": f2(dd["mix"]), "value": f2(dd["value"]),
            "opener": f2(dd["windows"]["opener"]), "mid": f2(dd["windows"]["mid"]),
            "app_lo": f"{d['lo']['attack'] / d['lo']['pieces']:.4f}",
            "app_hi": f"{d['hi']['attack'] / d['hi']['pieces']:.4f}",
            "tsd_mix": f2(_term(d, "TSD")[1]), "tst_mix": f2(_term(d, "TST")[1]),
            "q_mix": f2(_term(d, "Q")[1])}


def selftest():
    ok = True
    got = _probe_control()
    for k, want in PROBE_2026_10_11.items():
        good = got[k] == want
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} control: {k} = {got[k]} (the probe printed {want})")

    data = src.derive()
    gap = data["decomposition"]["gap"]
    good = abs(gap - data["replay_gap"]) < Fraction(1, 10_000)
    ok &= good
    print(f"  {'ok ' if good else 'BAD'} control: engine gap and replay-counter gap agree to 1e-4")

    live = problems(data, load_docs(REPO, DOCS))
    ok &= not live
    print(f"  {'ok ' if not live else 'BAD'} control: the committed document agrees: "
          f"{'yes' if not live else live[0]}")

    def doc_of(name):
        return "prelude\n\n" + render_fragments(FRAGMENTS, data, name) + "\npostlude\n"

    caught = planted = 0
    for label, name, text, must_fail in fragment_mutants(FRAGMENTS, data, DOCS, doc_of, "app:"):
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
    ap = argparse.ArgumentParser(description="gate the APP-gap figures CLAUDE.md publishes")
    ap.add_argument("--render", action="store_true", help="print the fragments to paste")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    data = src.derive()
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
    print(f"  ok  {len(FRAGMENTS)} figures over {data['sessions']} sessions agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
