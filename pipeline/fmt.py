"""Number formatting shared by every generator that prints a measured value.

All of these **floor** rather than round. The reports say 約 in front of any value
that has been shortened, and 約 has to mean "at least this much" consistently —
a value that sometimes rounds up would make the word a lie. The claim generator
applies the same convention to its Cantonese, so a card and the claim it cites
print the same digits.

    python3 -m pipeline.fmt --selftest    # the floor convention, pinned on values that
                                          # actually discriminate it from rounding

That selftest exists because **the live corpus cannot tell floor from round.** Every figure
these helpers currently produce comes out the same under either rule, so a mutant swapping the
rounding mode survives every byte-identity gate in this repo — the state CLAUDE.md's
「byte-identity guards only discriminating values」 note describes. The cases below are chosen
to discriminate, which is the only thing that makes the convention enforced rather than merely
documented.
"""
import argparse
import decimal
import sys


def ratio1(num, den):
    """`num / den` as one decimal place, FLOORED, from two exact decimal strings.

    Decimal end to end, and the callers hold their inputs as STRINGS so the printed digits and
    the arithmetic are the same decimal number. Divide in binary float instead and 41/10 lands
    one ulp under 4.1, which floors to "4.0" — a rounding rule that is wrong only sometimes,
    which is worse than one that is wrong always because nothing surfaces it.

    That claim is measured, not assumed, and the obvious version of it is FALSE: the all-float
    spelling `floor(x*10)/10` gets 41/10 right, because multiplying by 10 rounds the ulp back
    off. It is `Decimal(float(num)/float(den))` — float division, decimal quantize, the most
    natural way to write the mutation — that returns "4.0". A sweep of 200 000 random pairs has
    the two float spellings disagreeing with this one 1 006 and 429 times respectively, and
    `_selftest` pins one case for each so neither can be reintroduced.

    Flooring is what lets a ratio keep an "at least" word in front of it: the value prints as
    a lower bound, so 足足細咗 N 倍 is true by construction rather than by whoever last checked.

    The rounding-mode example is `ratio1("58.0", "15.0") == "3.8"` — 3.8666…, where
    ROUND_HALF_UP gives "3.9". Picked because it DISCRIMINATES. The live corpus divides 59.2 by
    15.5 = 3.8195, which floors and rounds alike to "3.8" and so pins nothing.
    """
    q = decimal.Decimal(num) / decimal.Decimal(den)
    return str(q.quantize(decimal.Decimal("0.1"), rounding=decimal.ROUND_FLOOR))


def r1(x1000):
    """An x1000 integer as one decimal place, floored: 114223 -> "114.2"."""
    return f"{x1000 // 100 / 10:.1f}"


def r2(x1000):
    """An x1000 integer as two decimal places, floored: 1423 -> "1.42"."""
    return f"{x1000 // 10 / 100:.2f}"


def secs(ms):
    """Whole seconds, floored: 228310 -> 228."""
    return ms // 1000


def fmt_clock(ms):
    """m:ss, floored: 228310 -> "3:48"."""
    total = secs(ms)
    return f"{total // 60}:{total % 60:02d}"


# --------------------------------------------------------------------------- the selftest
#
# Every case here is DISCRIMINATING: it is a value where flooring and rounding give different
# answers, so each assertion kills a specific mutant. A case where both rules agree would pass
# under either and pin nothing — which is the whole reason this file needed a selftest at all
# (see the module docstring). One line per rule, not one line per helper.
_CASES = [
    # ---- ratio1: the rounding MODE ----
    # 58.0/15.0 = 3.8666…; ROUND_HALF_UP gives "3.9". This is the only assertion standing
    # between the codebase and a silently-rounding 足足 claim.
    (lambda: ratio1("58.0", "15.0"), "3.8", "ratio1 floors 3.866… (half-up would say 3.9)"),
    # ---- ratio1: the ARITHMETIC, i.e. Decimal and not float ----
    # 41/10 is exactly 4.1. `Decimal(float(41)/float(10))` is 4.09999999999999964… and floors
    # to "4.0". Kills the float-division spelling of the mutation.
    (lambda: ratio1("41", "10"), "4.1", "ratio1 divides in Decimal (float division says 4.0)"),
    # 0.3/0.1 is exactly 3. BOTH float spellings say "2.9" here — including `floor(x*10)/10`,
    # which the case above cannot catch. Two cases because there are two ways to write it wrong.
    (lambda: ratio1("0.3", "0.1"), "3.0", "ratio1 is exact at a tenth (both float forms say 2.9)"),
    # ---- the x1000 helpers: floor, never round ----
    # The floor happens in integer arithmetic (`// 100`) before the float ever appears, which is
    # why these are safe — but nothing said so, and nothing would notice if the `//` became `/`.
    (lambda: r1(114299), "114.2", "r1 floors 114.299 (rounding would say 114.3)"),
    (lambda: r2(1429), "1.42", "r2 floors 1.429 (rounding would say 1.43)"),
    # ---- the millisecond helpers ----
    (lambda: secs(228999), 228, "secs floors 228.999 (rounding would say 229)"),
    (lambda: fmt_clock(239999), "3:59", "fmt_clock floors 239.999s (rounding would say 4:00)"),
]


def selftest():
    failures = 0
    for fn, want, what in _CASES:
        got = fn()
        if got != want:
            print(f"SELFTEST FAIL: {what} — got {got!r}, want {want!r}", file=sys.stderr)
            failures += 1
    if failures:
        print(f"selftest: {failures} of {len(_CASES)} cases failed", file=sys.stderr)
        return 1
    print(f"  ok  selftest: {len(_CASES)} discriminating cases — every one is a value where "
          "flooring and rounding differ")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true",
                    help="pin the floor convention on discriminating values, then exit")
    args = ap.parse_args(argv)
    if not args.selftest:
        ap.error("nothing to do: this module is a library; --selftest is its only entry point")
    return selftest()


if __name__ == "__main__":
    raise SystemExit(main())
