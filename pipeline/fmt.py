"""Number formatting shared by every generator that prints a measured value.

All of these **floor** rather than round. The reports say 約 in front of any value
that has been shortened, and 約 has to mean "at least this much" consistently —
a value that sometimes rounds up would make the word a lie. The claim generator
applies the same convention to its Cantonese, so a card and the claim it cites
print the same digits.
"""


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
