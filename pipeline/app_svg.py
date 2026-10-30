"""Small deterministic SVG/HTML helpers for the 每粒攻擊 (`app`) section.

Every chart in that section is rendered here, server-side, as a string: no script, no
`innerHTML`, and byte-identical on every run. Two kinds of number leave this module and they
are kept apart on purpose:

  * **coordinates** (`coord`) — positions inside a viewBox. Not a published figure, so they
    are formatted at two places with trailing zeros stripped and do NOT go through `fmt`;
    `check_rounding` should excuse `app_svg.coord` by name if this module joins its COVERED list.
  * **printed figures** (`num`, `rate`, `pct`) — anything a reader reads as a value, including
    tick labels and `<title>` tooltips. These route through `pipeline.fmt` with an explicit rule
    and a `site=` name, so `check_rounding` sees every call. 約 means floored, so the default
    rule is "floor"; pass "ceil" for an upper bound.

Classes emitted here are `ap-` prefixed and the section's CSS scopes them under `#app`
(`check_generated_css`).
"""
import html
import math

from pipeline import fmt


# ------------------------------------------------------------------ markup

def esc(s):
    return html.escape(str(s), quote=True)


def coord(x):
    """A viewBox coordinate: two places, trailing zeros stripped, never "-0"."""
    s = f"{float(x):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _attr(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return coord(v)
    return esc(v)


def el(tag, attrs=None, *children, text=None):
    """`<tag a="…">children</tag>`. Attribute order is the dict's (insertion) order, so the
    output is deterministic; a None attribute is dropped. `text` is escaped, `children` are
    trusted markup (strings this module or a block built). No children and no text -> self-closing.
    """
    a = "".join(f' {k.replace("_", "-")}="{_attr(v)}"'
                for k, v in (attrs or {}).items() if v is not None)
    inner = (esc(text) if text is not None else "") + "".join(c for c in children if c)
    if not inner:
        return f"<{tag}{a}/>"
    return f"<{tag}{a}>{inner}</{tag}>"


def title(text):
    """An SVG `<title>` tooltip. Figures in `text` must already have come through `num`/`rate`."""
    return el("title", None, text=text)


def svg(width, height, children, label, cls="ap-svg"):
    """Root element: a viewBox of `width` x `height`, scaled by CSS, labelled for assistive tech."""
    return el("svg", {"class": cls, "viewBox": f"0 0 {coord(width)} {coord(height)}",
                      "role": "img", "aria-label": label,
                      "xmlns": "http://www.w3.org/2000/svg"}, *children)


# ------------------------------------------------------------------ printed figures

def num(x1000, dp, site, rule="floor"):
    """An x1000 integer printed at `dp` places through `fmt.quant`."""
    return fmt.quant(x1000, dp, rule, site=site)


def rate(n, d, dp, site, rule="floor"):
    """`n / d` printed at `dp` (<= 3) places: permille then quant, one declared rule, integer
    arithmetic throughout. APP is `rate(attack, pieces, 3, site=…)`."""
    return fmt.quant(fmt.permille(n, d, rule, site=site), dp, rule, site=site)


def pct(n, d, dp, site, rule="floor"):
    """`100 * n / d` printed at `dp` places, without the % sign. A ratio gap of a over b is
    `pct(a - b, b, …)`, which is signed: floor of a negative value moves away from zero."""
    return fmt.quant(fmt.permille(100 * n, d, rule, site=site), dp, rule, site=site)


# ------------------------------------------------------------------ scales and axes

class Scale:
    """Linear map from a data domain [d0, d1] to a pixel range [r0, r1]. Reversed ranges are
    fine (a y axis is `Scale(lo, hi, bottom, top)`); a zero-width domain maps to the range's mid."""

    def __init__(self, d0, d1, r0, r1):
        self.d0, self.d1, self.r0, self.r1 = d0, d1, r0, r1

    def __call__(self, v):
        if self.d1 == self.d0:
            return (self.r0 + self.r1) / 2
        return self.r0 + (v - self.d0) * (self.r1 - self.r0) / (self.d1 - self.d0)

    def clamp(self, v):
        lo, hi = min(self.d0, self.d1), max(self.d0, self.d1)
        return self(min(max(v, lo), hi))


def ticks(lo, hi, step):
    """Every multiple of `step` in [lo, hi], each computed as `k * step` from an integer k so
    there is no accumulated float drift. `step` > 0."""
    k = math.ceil(lo / step - 1e-9)
    out = []
    while k * step <= hi + 1e-9:
        out.append(k * step)
        k += 1
    return out


def grid_x(sx, values, y0, y1, labels=None, label_y=None):
    """Vertical gridlines at `values` from y0 to y1, with optional tick labels below.
    `labels` is a list of already-formatted strings parallel to `values`."""
    out = []
    for i, v in enumerate(values):
        x = sx(v)
        out.append(el("line", {"class": "ap-grid", "x1": x, "x2": x, "y1": y0, "y2": y1}))
        if labels is not None:
            out.append(el("text", {"class": "ap-tick", "x": x,
                                   "y": label_y if label_y is not None else y1 + 14,
                                   "text-anchor": "middle"}, text=labels[i]))
    return "".join(out)


def grid_y(sy, values, x0, x1, labels=None, label_x=None):
    """Horizontal gridlines at `values` from x0 to x1, with optional labels left of x0."""
    out = []
    for i, v in enumerate(values):
        y = sy(v)
        out.append(el("line", {"class": "ap-grid", "x1": x0, "x2": x1, "y1": y, "y2": y}))
        if labels is not None:
            out.append(el("text", {"class": "ap-tick",
                                   "x": label_x if label_x is not None else x0 - 6,
                                   "y": y + 4, "text-anchor": "end"}, text=labels[i]))
    return "".join(out)


def axis_line(x1, y1, x2, y2):
    return el("line", {"class": "ap-ax", "x1": x1, "y1": y1, "x2": x2, "y2": y2})


def axis_label(x, y, text, anchor="middle", rotate=False):
    attrs = {"class": "ap-axlabel", "x": x, "y": y, "text-anchor": anchor}
    if rotate:
        attrs["transform"] = f"rotate(-90 {coord(x)} {coord(y)})"
    return el("text", attrs, text=text)
