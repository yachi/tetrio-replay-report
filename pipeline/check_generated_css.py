"""Gate: a generated section's CSS may only style markup that section owns.

    python3 -m pipeline.check_generated_css sessions/2026-07-24/report

Generated sections ship their own `<style>` block, injected into the body — later
in the document than the report's own stylesheet, so at equal specificity the
generated rule wins. A class name that the rest of the report already uses
therefore gets silently restyled.

That happened: 全場之最 defined `.rec-grid` for its tile grid, 建議 had used
`.rec-grid` for its two-column layout since long before, and the coaching columns
collapsed into narrow auto-fit ones. Nothing failed — the section itself looked
right, which is exactly why a checker beats another careful look.

What is checked is whether a rule **can match an element outside its region**, not
whether a name is shared. A selector is pinned to the region as soon as any of its
compounds carries a class or id that appears nowhere outside — `.sr-dot.is-y` is
safe because `.sr-dot` is the section's own, and `.rt-fields .k` is safe because
its ancestor is. A rule like `.rec-grid`, whose only compound is a name the rest of
the report uses, is what fails.

CSS comments are stripped before selectors are read, because a rule may legitimately
*mention* a host class while explaining why it avoids it.
"""
import argparse
import os
import re
import sys

REGION = re.compile(r"<!-- BEGIN generated (?P<name>[a-z-]+) \([^)]*\) -->"
                    r"(?P<body>.*?)"
                    r"<!-- END generated (?P=name) -->", re.S)
STYLE = re.compile(r"<style>(.*?)</style>", re.S)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
TOKEN = re.compile(r"[.#](-?[A-Za-z_][\w-]*)")
CLASS_ATTR = re.compile(r'class="([^"]*)"')
ID_ATTR = re.compile(r'id="([^"]+)"')
AT_RULE = re.compile(r"@[\w-]+[^{]*$")
PSEUDO = re.compile(r"::?[\w-]+(\([^)]*\))?")
ATTR_SEL = re.compile(r"\[[^\]]*\]")
COMBINATOR = re.compile(r"\s*[>+~]\s*|\s+")


def selectors(region_body):
    """Every selector in this region's <style> blocks, at-rule preludes dropped."""
    out = []
    for block in STYLE.findall(region_body):
        css = CSS_COMMENT.sub(" ", block)
        for chunk in css.split("}"):
            head = chunk.split("{")[0].strip()
            if not head or AT_RULE.match(head):
                continue
            out += [s.strip() for s in head.split(",") if s.strip()]
    return out


def compounds(selector):
    """The selector's compounds, each as its set of class/id names."""
    clean = ATTR_SEL.sub(" ", PSEUDO.sub("", selector))
    return [set(TOKEN.findall(part)) for part in COMBINATOR.split(clean) if part.strip()]


def used_names(text):
    names = set()
    for attr in CLASS_ATTR.findall(text):
        names.update(attr.split())
    names.update(ID_ATTR.findall(text))
    return names


def scan(report_path):
    """[(region, [unpinned selectors])] — a selector that can match outside its region."""
    with open(report_path, encoding="utf-8") as fh:
        html = fh.read()
    regions = [(m.group("name"), m.group("body"), m.start(), m.end())
               for m in REGION.finditer(html)]
    findings = []
    for name, body, start, end in regions:
        sels = selectors(body)
        if not sels:
            continue
        # Markup in *other* generated regions counts as outside too: two generated
        # sections colliding with each other is the same defect.
        outside = used_names(html[:start] + html[end:])
        unpinned = []
        for sel in sels:
            parts = compounds(sel)
            if not any(part - outside for part in parts if part):
                unpinned.append(sel)
        findings.append((name, len(sels), unpinned))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    args = ap.parse_args(argv)

    report = os.path.join(args.report_dir, "report.html")
    if not os.path.exists(report):
        print(f"FAIL {report} does not exist", file=sys.stderr)
        return 1

    findings = scan(report)
    if not findings:
        print(f"  --  no generated section in {os.path.basename(report)} ships CSS")
        return 0

    bad = 0
    for name, total, unpinned in findings:
        if unpinned:
            bad += len(unpinned)
            for sel in unpinned:
                print(f"FAIL region {name!r}: selector {sel!r} can match elements "
                      f"outside the region", file=sys.stderr)
        else:
            print(f"  ok  region {name!r} — all {total} selector(s) pinned to markup "
                  "the region owns")
    if bad:
        print(f"\n{bad} selector(s) reach outside their region. Rename the generated "
              "section's classes, or scope the rule under the section id.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
