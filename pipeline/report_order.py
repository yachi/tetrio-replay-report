"""The order a report's sections are read in, and the navigation bar that follows it.

    python3 -m pipeline.report_order --selftest sessions/2026-11-05/report

A report used to grow by appending: each new section was anchored on whatever marker sat
nearest, so the order on the page was the order things were WRITTEN, not the order a reader
wants them. On 2026-11-05 the advice sat at 35% of a 50 000 px page and the two sections it
should point at (行錯咗嗰一步, finesse) sat under 39 000 px. yachi agreed on 2026-11-14 to read the
page in four tiers instead:

  今晚 30 秒   what happened tonight            hero, 三件事, 戰況, 影片
  練乜         what to practise                 建議, 練習卡, 行錯咗嗰一步, finesse, 定式路線同中盤手法
  點解         why the numbers came out so      數據對決, 每粒攻擊, 攻擊由邊度嚟, 最癲一局 and its replay,
                                                全場之最, 全消
  參考         look-up material                 逐局全數據, T-Spin Forecast, C-Spin 同 DT 砲, 證明附錄

`apply` is the ONE place that order lives. `build_report.render` calls it after every region has
been written, so the anchors in `build_report.SECTIONS` only have to put a new region SOMEWHERE in
the body; this moves it to its tier. That is what lets the 22 committed reports and a report built
from a fresh skeleton come out in the same order without two copies of the order to drift.

What it refuses, because each is a way to lose content silently:
  * a region in the body that `TIERS` does not name (a new section must be given a tier);
  * anything between the regions other than whitespace and the `<!-- ===== … ===== -->` separator
    comments (hand-written markup there would otherwise be dropped);
  * a region appearing twice.

Trust tiers are NOT reading tiers. The 練乜 tier holds simulator sections (未經證明) next to 建議,
which is proved; each of those sections keeps its own eyebrow and quarantine sentences, and the
nav names reading tiers only.
"""
import argparse
import html as H
import os
import re
import sys

from pipeline import build_round_table, region

PRODUCER = "pipeline/build_report.py"

# (key, nav label, separator label, region names in reading order)
TIERS = (
    ("tonight", "今晚 30 秒", "今晚 30 秒", ("hero", "moments", "matches", "video")),
    ("practise", "練乜", "練乜", ("coaching", "practice", "pc-miss", "finesse-placements",
                                  "routes-techniques")),
    ("why", "點解", "點解", ("stats", "app", "attack-sources", "intense-round", "round-replay",
                             "records", "perfect-clear")),
    ("lookup", "參考", "參考", ("round-table", "forecast", "openers", "appendix")),
)
ORDER = tuple(n for _, _, _, names in TIERS for n in names)
NAV = "nav"
FOOTER = '<footer class="report-footer">'
SEPARATOR = re.compile(r"<!-- =+ [^<>]*? =+ -->")
REGION_OPEN = re.compile(r"<!-- BEGIN generated ([a-z-]+) \(([^)]*)\) -->")
SECTION_ID = re.compile(r'<section\b[^>]*\bid="([^"]+)"')

NAV_CSS = """  <style>
    /* Scoped under #report-nav, every class carries the rn- prefix: a generated region's <style>
       lands in the body and beats the report's own stylesheet. */
    #report-nav { position: sticky; top: 0; z-index: 20; display: flex; justify-content: center;
      padding: .45rem .75rem; background: color-mix(in srgb, var(--bg) 88%, transparent);
      -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--border); }
    #report-nav .rn-bar { display: flex; gap: .3rem; overflow-x: auto; max-width: 100%;
      scrollbar-width: none; }
    #report-nav .rn-bar a { padding: .3rem .8rem; border-radius: 999px; white-space: nowrap;
      color: var(--ink-secondary); text-decoration: none; font-size: .88rem; }
    #report-nav .rn-bar a:hover { color: var(--ink); background: var(--bg-sunken); }
    #report-nav .rn-bar a.rn-on { color: var(--bg); background: var(--ink); }
  </style>"""

# Nodes are only re-classed, never built from markup. A click scrolls the tier's first element to
# just under the bar, which a plain #fragment jump would put underneath it.
NAV_SCRIPT = r"""  <script>
(function () {
  var nav = document.getElementById("report-nav");
  if (!nav) return;
  var links = nav.querySelectorAll("a[data-target]");
  // Looked up on every call: this script runs while the page is still parsing, before the
  // sections it points at exist.
  function target(i) {
    var id = links[i].getAttribute("data-target");
    return id ? document.getElementById(id) : null;
  }
  function topOf(el) { return el ? el.getBoundingClientRect().top + window.pageYOffset : 0; }
  function mark() {
    var y = window.pageYOffset + nav.offsetHeight + 12, on = 0;
    for (var i = 1; i < links.length; i++) { var el = target(i); if (el && topOf(el) <= y) on = i; }
    for (var j = 0; j < links.length; j++) links[j].className = j === on ? "rn-on" : "";
  }
  nav.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("a[data-target]") : null;
    if (!a) return;
    var i = Array.prototype.indexOf.call(links, a);
    e.preventDefault();
    window.scrollTo({ top: Math.max(0, topOf(target(i)) - nav.offsetHeight - 8), behavior: "smooth" });
    if (history.replaceState) history.replaceState(null, "", a.getAttribute("href"));
  });
  window.addEventListener("scroll", mark, { passive: true });
  document.addEventListener("DOMContentLoaded", mark);
  mark();
})();
  </script>"""


class OrderError(ValueError):
    pass


def _markers(name):
    if name == "round-table":
        return build_round_table.START, build_round_table.END
    return region.markers(name, PRODUCER)


def _span(doc):
    """(start, end) of the body run the tiers own: the first named region (with the separator
    comments and whitespace in front of it) up to the footer."""
    firsts = [doc.find(_markers(n)[0]) for n in ORDER + (NAV,)]
    firsts = [i for i in firsts if i >= 0]
    if not firsts:
        raise OrderError("no ordered region in the document")
    start = min(firsts)
    head = doc[:start]
    m = re.search(r"(?:\s|" + SEPARATOR.pattern + r")*\Z", head)
    start = m.start()
    end = doc.find(FOOTER, start)
    if end < 0:
        raise OrderError("no report footer after the ordered regions")
    return start, end


def _cut(run):
    """{name: block} for every region in `run`, and what is left over."""
    blocks, rest, pos = {}, [], 0
    while True:
        m = REGION_OPEN.search(run, pos)
        if not m:
            rest.append(run[pos:])
            break
        name = m.group(1)
        start, end = _markers(name)
        if run[m.start():m.start() + len(start)] != start:
            raise OrderError(f"region {name!r} opens with an unexpected producer: {m.group(0)}")
        stop = run.find(end, m.end())
        if stop < 0:
            raise OrderError(f"region {name!r} has no END marker")
        if name in blocks:
            raise OrderError(f"region {name!r} appears twice")
        rest.append(run[pos:m.start()])
        blocks[name] = run[m.start():stop + len(end)]
        pos = stop + len(end)
    left = SEPARATOR.sub("", "".join(rest))
    if left.strip():
        raise OrderError("content between the regions that no region owns: "
                         + repr(left.strip()[:120]))
    return blocks


def _target(block):
    m = SECTION_ID.search(block)
    return m.group(1) if m else None


def nav(blocks):
    """The bar: one link per tier that has a region, to the first section id in that tier. The
    first tier links to the top of the page (its hero has no id)."""
    items = []
    for i, (key, label, _, names) in enumerate(TIERS):
        present = [n for n in names if n in blocks]
        if not present:
            continue
        # The first region in the tier that carries a section id. A skeleton's round table is an
        # empty marker pair until build_round_table fills it, so "first region" alone would fail
        # on a new session; bin/new-session re-runs build_report after the table is filled.
        ids = [t for t in (_target(blocks[n]) for n in present) if t]
        target = "" if i == 0 else (ids[0] if ids else "")
        if i and not target:
            raise OrderError(f"tier {key!r}: none of its regions {present} carries a section id")
        href = f"#{target}" if target else "#"
        items.append(f'<a href="{H.escape(href)}" data-target="{H.escape(target)}">{H.escape(label)}</a>')
    return "\n".join([
        '<nav id="report-nav" aria-label="報告目錄">',
        NAV_CSS,
        f'  <div class="rn-bar">{"".join(items)}</div>',
        NAV_SCRIPT,
        '</nav>'])


def apply(doc):
    """`doc` with its body regions in tier order and the nav bar written after the hero."""
    start, end = _span(doc)
    blocks = _cut(doc[start:end])
    blocks.pop(NAV, None)
    unknown = sorted(set(blocks) - set(ORDER))
    if unknown:
        raise OrderError(f"regions with no tier in report_order.TIERS: {unknown}")
    s, e = _markers(NAV)
    nav_block = f"{s}\n{nav(blocks)}\n{e}"
    parts = []
    for _key, _label, sep, names in TIERS:
        present = [blocks[n] for n in names if n in blocks]
        if not present:
            continue
        parts.append(f"<!-- ============================= {sep} ============================= -->")
        for n in names:
            if n in blocks:
                parts.append(blocks[n])
                if n == "hero":
                    parts.append(nav_block)
    if "hero" not in blocks:
        parts.insert(0, nav_block)
    return doc[:start] + "\n\n" + "\n\n".join(parts) + "\n\n" + doc[end:]


def _selftest(report_dir):
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    ok = True
    out = apply(doc)
    cases = [("idempotent", apply(out) == out)]
    names = [m.group(1) for m in REGION_OPEN.finditer(out[slice(*_span(out))])]
    want = [n for n in ("hero", NAV) + ORDER[1:] if n in names]
    cases.append(("regions come out in tier order", [n for n in names] == want))

    def refused(mutant):
        try:
            apply(mutant)
            return False
        except OrderError:
            return True

    # Plant right after the first region's END: markup before the first region is outside the
    # span and kept where it is, so it is not the case this guard is for.
    first = REGION_OPEN.search(out[_span(out)[0]:])
    first_end = _markers(first.group(1))[1]
    i = out.index(first_end, _span(out)[0]) + len(first_end)
    cases.append(("hand-written markup between regions is refused",
                  refused(out[:i] + "<p>stray</p>\n" + out[i:])))
    s, e = region.markers("mystery", PRODUCER)
    cases.append(("a region with no tier is refused",
                  refused(out[:i] + f"{s}\n<div></div>\n{e}\n" + out[i:])))
    hs, he = _markers("hero")
    hero_block = out[out.index(hs):out.index(he) + len(he)]
    cases.append(("a region twice is refused", refused(out[:i] + hero_block + "\n" + out[i:])))
    for name, good in cases:
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}")
    print(f"{'ok ' if ok else 'FAIL'} report_order selftest, {len(cases)} cases")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest(args.report_dir)
    ap.error("only --selftest is supported; build_report applies the order")


if __name__ == "__main__":
    raise SystemExit(main())
