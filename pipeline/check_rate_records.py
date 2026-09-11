"""Gate: every figure CLAUDE.md publishes from `analysis/rate_records.R`.

    python3 -m pipeline.check_rate_records            # staleness + the fragments
    python3 -m pipeline.check_rate_records --render   # the fragments, ready to paste
    python3 -m pipeline.check_rate_records --rerun    # also re-run the R script and diff
    python3 -m pipeline.check_rate_records --selftest # plant corruptions, require catches

The evidence for `QUALIFYING_MS` was the last figure family in the repo with no gate at
all. The script ran in no workflow and no `bin/` script, its session list was hardcoded,
and its output was hand-copied into `pipeline/records.py` and into fifteen sentences of
CLAUDE.md. Two of those copies were measurably wrong when this was written:

  * `pipeline/claims/generators.py` carried 26 lines of FOUR-SESSION statistics beside the
    `QUALIFYING_MS = 60_000` it justifies — 492 player-rounds, slopes −0.616/−0.697,
    「both with −0.5 inside the 95% CI」 (APM's is outside at seven), 「the MEAN stays flat」
    (it does not, p = 0.01), 12 records, p = 6e-08. Deleted rather than refreshed: a figure
    with three homes has two places to rot, and the artefact is the home now.
  * 「the same round for every cut-off from 50 s to 70 s」 was VS's band quoted for a
    sentence that named APM too. APM's is [54, 62]. The table printed underneath it as
    evidence showed VS only, so the metric the claim was false for was the one the evidence
    could not display — a check that cannot fail, arriving from a new direction.

**Rounding has a direction, and it is per claim, not per number.** A p-value supporting
「rejected」 must CEIL (a p rounded down claims more significance than was measured); a
p-value supporting 「still flat」 must FLOOR. A confidence interval quoted to show a value
lies OUTSIDE it must widen, not narrow. The SD-fall ratio floors and the mean-move ratio
ceils, because the footnote's argument is that the first dominates the second. Applying
this moved four published figures by one digit: 8.6e-05 → 8.7e-05, 5.3e-05 → 5.4e-05,
1.11× → 1.12×, and the band.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

from analysis.rate_records_artefact import ARTEFACT, REGEN, REPO, load, staleness
from . import records
from .docs_gate import (Incomplete, fragment_mutants, fragment_problems, load_docs,
                        render_fragments, reword)

DOCS = ("CLAUDE.md",)
REWORD = reword("pipeline/check_rate_records.py")
_EN = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
       "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
       "seventeen", "eighteen", "nineteen", "twenty")
MINUS = "−"          # the character the section uses, not an ASCII hyphen


def _q(x, dp, how):
    """Round to `dp` decimals in a named direction. `how` is 'round' | 'floor' | 'ceil'."""
    k = 10 ** dp
    v = {"round": lambda: round(x * k) / k,
         "floor": lambda: math.floor(x * k) / k,
         "ceil": lambda: math.ceil(x * k) / k}[how]()
    return f"{v:.{dp}f}"


def _signed(x, dp, how="round"):
    """`−0.625` — the section's minus sign, never an ASCII hyphen."""
    return _q(x, dp, how).replace("-", MINUS)


def _p(x, how):
    """A p-value the way this section writes them: `8.7e-05` under 0.001, else `0.25`.

    `how` is the DIRECTION the claim leans. 'ceil' for a p supporting a rejection (a p
    rounded down asserts more significance than the fit gives); 'floor' for a p supporting
    「still flat」, where a smaller number is weaker support for the claim being made.
    """
    if x >= 0.001:
        return _q(x, 2, how)
    e = math.floor(math.log10(x))
    scale = 10 ** (1 - e)
    m = (math.ceil if how == "ceil" else math.floor)(x * scale) / 10
    if m >= 10:                                    # 9.96e-5 ceils to 1.0e-4
        m, e = m / 10, e + 1
    return f"{m:.1f}e{e:+03d}"


def _ratio(a, b, how):
    return _q(a / b, 2, how).rstrip("0").rstrip(".") if how == "x" else _q(a / b, 2, how)


def _band(b):
    return f"[{b['lo']}, {b['hi']}] s"


def _hl(art, field):
    """07-22's VS headline, by name — the sentence is about that record specifically.

    Not a corpus argmax: the most extreme unqualified record in the corpus is 08-09's APM
    at 79% above its qualified peak, which is a different and stronger claim than the one
    the paragraph makes.
    """
    try:
        e = art["unqualified_peaks"]["2026-07-22"]["vs"]
    except KeyError:
        raise Incomplete("the artefact has no 2026-07-22 VS unqualified peak; the sentence "
                         "names that record specifically")
    return {"value": lambda: _q(e["value"], 1, "floor"),      # prefixed 約, so it floors
            "round_s": lambda: f"{_q(e['round_s'], 1, 'round')} s",
            # 「N% above」 — floor, so the gap is at least what is printed
            "pct": lambda: f"{_q(e['pct_above'], 0, 'floor')}%"}[field]()


FRAGMENTS = {
    # --- the corpus the regression ran over
    "rate:corpus": (lambda a: f"{a['n_player_rounds']} player-rounds", DOCS),
    "rate:sessions": (lambda a: f"{_EN[len(a['sessions'])]} sessions", DOCS),
    # --- the slope test. Point estimates round; the p's supporting the rejection ceil.
    "rate:slopes": (lambda a: f"{_signed(a['metrics']['vs']['slope'], 3)} for VS and "
                              f"{_signed(a['metrics']['apm']['slope'], 3)} for APM", DOCS),
    "rate:slope-p": (lambda a: f"{_p(a['metrics']['vs']['p'], 'ceil')} / "
                               f"{_p(a['metrics']['apm']['p'], 'ceil')}", DOCS),
    # An interval quoted to show −0.5 lies OUTSIDE it must widen, never narrow.
    "rate:apm-ci": (lambda a: f"[{_signed(a['metrics']['apm']['ci_lo'], 3, 'floor')}, "
                              f"{_signed(a['metrics']['apm']['ci_hi'], 3, 'ceil')}]", DOCS),
    # --- the two mean controls, which lean in opposite directions
    "rate:vs-mean": (lambda a: f"{_q(a['metrics']['vs']['mean_short'], 1, 'round')} → "
                               f"{_q(a['metrics']['vs']['mean_long'], 1, 'round')}", DOCS),
    "rate:vs-mean-p": (lambda a: _p(a["metrics"]["vs"]["mean_p"], "ceil"), DOCS),
    "rate:pps-mean-p": (lambda a: _p(a["metrics"]["pps"]["mean_p"], "floor"), DOCS),
    # --- the records test
    "rate:records": (lambda a: str(a["records"]["in_shortest_quartile"]), DOCS),
    # The DENOMINATOR of the line above. It existed only as a typed 「24」 beside these two
    # fragments until 2026-09-11, where it had been correct at eight sessions and was then
    # carried through three more — so the sentence read 「32 of the 24 unqualified records
    # (3 metrics x 11 sessions)」, an arithmetic impossibility sitting between two gated spans.
    # That is CLAUDE.md's eighth 冇第二份 instance exactly: a count derivable from the fragment
    # beside it, typed instead of derived. Rendered now, so the product and its factors move
    # together or the build goes red.
    "rate:records-denom": (lambda a: str(a["records"]["n_metrics"] * len(a["sessions"])), DOCS),
    "rate:records-basis": (lambda a: f"{a['records']['n_metrics']} metrics × "
                                     f"{len(a['sessions'])} sessions", DOCS),
    "rate:records-p": (lambda a: _p(a["records"]["p"], "ceil"), DOCS),
    # --- 07-22's headline, the example the qualifier was written for
    "rate:headline-vs": (lambda a: _hl(a, "value"), DOCS),
    "rate:headline-t": (lambda a: _hl(a, "round_s"), DOCS),
    "rate:headline-pct": (lambda a: _hl(a, "pct"), DOCS),
    # --- the footnote's argument: the spread moves a lot, the mean a little. So the SD
    #     ratio floors and the mean ratio ceils; each is quoted against the other.
    "rate:sd-ratio": (lambda a: _q(a["metrics"]["vs"]["sd_short"]
                                   / a["metrics"]["vs"]["sd_long"], 1, "floor") + "×", DOCS),
    "rate:mean-ratio": (lambda a: _q(a["metrics"]["vs"]["mean_long"]
                                     / a["metrics"]["vs"]["mean_short"], 2, "ceil") + "×",
                        DOCS),
    # --- the stability band, computed rather than asserted
    "rate:band": (lambda a: _band(a["stability"]["rate_records"]), DOCS),
    "rate:band-all": (lambda a: _band(a["stability"]["all_metrics"]), DOCS),
}


def problems(art, docs):
    out = []
    for name in DOCS:
        text = docs.get(name)
        if text is None:
            out.append(f"{name}: not found. {REWORD}")
            continue
        out += fragment_problems(name, text, FRAGMENTS, art, REWORD, "rate:")
    return out


def rerun(root=REPO):
    """Re-run the R script and require the committed artefact back, byte for byte.

    Byte-identity is safe here only because the emitter rounds to six significant digits —
    eight orders of magnitude above the ~1e-15 an `lm()` moves by across BLAS builds, and
    three above anything published. Skipped when Rscript is absent, and SAID so: a check
    that quietly did not run is the failure this file exists to stop.
    """
    if not shutil.which("Rscript"):
        return [], "Rscript not on PATH — fingerprints only, the artefact was not re-derived"
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "rate-records.json")
        r = subprocess.run(["Rscript", "analysis/rate_records.R", "--json", out, "--quiet"],
                           cwd=root, capture_output=True, text=True)
        if r.returncode:
            return [f"`{REGEN}` failed:\n{r.stderr.strip()}"], None
        got = open(out, encoding="utf-8").read()
    want = ARTEFACT.read_text(encoding="utf-8")
    if got != want:
        return [f"re-running the script does not reproduce analysis/rate-records.json. "
                f"Commit the new one: `{REGEN}`"], None
    return [], "re-ran the R script; the committed artefact came back byte-identical"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    stale, art = staleness()
    if stale:
        print("analysis/rate-records.json is stale:")
        for p in stale:
            print(f"  BAD {p}")
        return 1

    if args.render:
        for name in DOCS:
            print(f"--- {name}")
            print(render_fragments(FRAGMENTS, art, name), end="")
        return 0

    bad = list(problems(art, load_docs(REPO, DOCS)))
    note = None
    if args.rerun:
        more, note = rerun()
        bad += more
    for p in bad:
        print(f"  BAD {p}")
    if bad:
        return 1
    if note:
        print(f"  ok  {note}")
    print(f"  ok  {len(FRAGMENTS)} figures from {len(art['sessions'])} sessions "
          f"({art['n_player_rounds']} player-rounds) agree with CLAUDE.md")
    return 0


def selftest():
    ok = True
    art = load()
    docs = load_docs(REPO, DOCS)

    live = problems(art, docs)
    ok &= not live
    for p in live:
        print(f"  BAD committed tree already fails: {p}")
    if not live:
        print(f"  ok  the committed CLAUDE.md carries all {len(FRAGMENTS)} fragments")

    # Control — the artefact's 07-22 VS headline is the SAME record the session's own
    # proved ledger publishes. That is an outside witness, not a literal: the figure comes
    # out of facts.json through `generators._SUPERLATIVES` and `fmt`, a path this module
    # shares no code with, and it is the one example the paragraph names by session.
    #
    # It is also why CLAUDE.md's copy was wrong. The document said 約262.6 — the ROUNDED
    # value the 2026-07-26 約-floor pass replaced everywhere with 約262.5 — and identifies
    # 262.6 as the mistake six hundred lines further down, in the section stating the rule.
    ledger = json.loads((REPO / "sessions" / "2026-07-22" / "report"
                         / "claims-generated.json").read_text(encoding="utf-8"))
    canto = " ".join(c["canto"] for c in ledger)
    for field, want in (("value", _hl(art, "value")), ("round_s", "15.6 s"), ("pct", "46%")):
        good = _hl(art, field) == want
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} control: 07-22 headline {field} = "
              f"{_hl(art, field)} (want {want})")
    printed = f"約{_hl(art, 'value')}"
    good = printed in canto
    ok &= good
    print(f"  {'ok ' if good else 'BAD'} control: 07-22's own proved ledger prints "
          f"{printed} for that record")
    good = "約262.6" not in canto
    ok &= good
    print(f"  {'ok ' if good else 'BAD'} control: and never 約262.6, the rounded value "
          f"CLAUDE.md carried until 2026-08-23")

    # Control — the rounding helpers move in the direction each claim needs. A helper that
    # rounds is indistinguishable from one that ceils on most inputs, so every case here is
    # one where the three directions disagree.
    for label, got, want in (
            ("p 8.61434e-05 ceil", _p(8.61434e-05, "ceil"), "8.7e-05"),
            ("p 8.61434e-05 floor", _p(8.61434e-05, "floor"), "8.6e-05"),
            ("p 0.254411 floor", _p(0.254411, "floor"), "0.25"),
            ("p 0.254411 ceil", _p(0.254411, "ceil"), "0.26"),
            ("p 9.96e-05 ceil rolls the exponent", _p(9.96e-05, "ceil"), "1.0e-04"),
            ("signed floor", _signed(-0.886892, 3, "floor"), f"{MINUS}0.887"),
            ("signed ceil", _signed(-0.542233, 3, "ceil"), f"{MINUS}0.542"),
            ("ratio floor", _q(59.2419 / 15.5099, 1, "floor"), "3.8"),
            ("ratio ceil", _q(119.418 / 106.861, 2, "ceil"), "1.12")):
        good = got == want
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} control: {label} -> {got} (want {want})")

    # Control — `records.py`'s two footnote guards fire. Neither can fire on today's
    # corpus, which is exactly why they need a mutant: a guard nothing exercises is a
    # comment with a raise in it. Both CAN fire on legitimately-produced data — the
    # first when flooring the denominator pushes the printed quotient over a 0.1
    # boundary the unrounded one does not cross, the second when the SD stops falling.
    for label, patch in (
            ("the printed SD ratio exceeds the measured one",
             {"sd_ratio": "3.8", "sd_ratio_exact": 3.7, "sd_short": "59.2",
              "sd_long": "15.5"}),
            ("the SD fall drops under _MIN_SD_RATIO",
             {"sd_ratio": "1.9", "sd_ratio_exact": 1.95, "sd_short": "30.0",
              "sd_long": "15.5"})):
        try:
            records._check_sd_ratio(patch)
            fired = False
        except SystemExit:
            fired = True
        ok &= fired
        print(f"  {'ok ' if fired else 'BAD'} records.py guard: {label}")
    # ...and passes on the committed artefact, so the two above are not vacuous.
    records._check_sd_ratio(records.r_stats())
    print("  ok  records.py guard: silent on the committed artefact")

    # Control — staleness fires on each of its three inputs. Not one mutant: the three
    # are independent, and the DATA one is the class the old session-count guard missed.
    for label, patch in (
            ("a facts.json moves", lambda a: a["facts_md5"].__setitem__(
                a["sessions"][0], "0" * 32)),
            ("the script moves", lambda a: a.__setitem__("script_md5", "0" * 32)),
            ("a session lands", lambda a: a["sessions"].append("2026-09-01"))):
        with tempfile.TemporaryDirectory() as tmp:
            shadow = os.path.join(tmp, "analysis")
            os.makedirs(shadow)
            for f in ("rate_records.R",):
                shutil.copy(REPO / "analysis" / f, shadow)
            os.symlink(REPO / "sessions", os.path.join(tmp, "sessions"))
            mutant = json.loads(ARTEFACT.read_text(encoding="utf-8"))
            patch(mutant)
            with open(os.path.join(shadow, "rate-records.json"), "w") as fh:
                json.dump(mutant, fh)
            caught = bool(staleness(tmp)[0])
        ok &= caught
        print(f"  {'ok ' if caught else 'BAD'} staleness: {label}")

    # The fragment mutants: every (document, fragment) pair, five corruptions each, plus
    # the unclaimed-marker rule for the namespace.
    n, mutants_ok = 0, True
    for label, name, text, must_fail in fragment_mutants(
            FRAGMENTS, art, DOCS, docs.get, "rate:"):
        shadow = dict(docs, **{name: text})
        caught = bool(problems(art, shadow))
        good = caught == must_fail
        mutants_ok &= good
        n += 1
        if not good:
            print(f"  BAD mutant survived: {label}")
    ok &= mutants_ok
    print(f"  {'ok ' if mutants_ok else 'BAD'} {n} fragment mutants, all caught")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
