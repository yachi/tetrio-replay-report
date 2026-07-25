"""Replace a marked region of an HTML file in place.

Every generator in this pipeline writes into a report that also contains
hand-written Cantonese prose, so none of them may own the whole file. They own a
region between two HTML comments and nothing else:

    <!-- BEGIN generated <name> (<producer>) -->
    ...generated...
    <!-- END generated <name> -->

`replace` is idempotent by construction: it matches the markers themselves, so
re-running over an already-generated file replaces the same span rather than
nesting a second copy inside the first. That property is what makes it safe to
re-run a generator over a report a person has edited around.

`build_round_table.py` predates this module and carries its own marker pair with
a different wording; `markers()` reproduces the shape the newer generators use.
"""
import re


def markers(name, producer):
    """The BEGIN/END comment pair for a generated region."""
    return (f"<!-- BEGIN generated {name} ({producer}) -->",
            f"<!-- END generated {name} -->")


def replace(html, start, end, body, anchor=None):
    """Return `html` with the region between `start`/`end` set to `body`.

    The markers are written as part of the region, so the result always contains
    exactly one pair. If the region is absent, `body` is inserted before
    `anchor` (a literal string that must occur in `html`); without an anchor a
    missing region is an error, because silently appending would put generated
    markup outside the document's structure.

    Returns (html, how) where `how` is "replaced" or "inserted".
    """
    section = f"{start}\n{body.strip()}\n{end}"
    if start in html and end in html:
        # A lambda replacement keeps backslashes and \g in `body` literal.
        return re.sub(re.escape(start) + r".*?" + re.escape(end),
                      lambda _m: section, html, count=1, flags=re.S), "replaced"
    if start in html or end in html:
        raise ValueError(f"only one of the markers for {start!r} is present — "
                         "the region is corrupt, refusing to guess where it ends")
    if anchor is None:
        raise ValueError(f"region {start!r} not found and no anchor given")
    if anchor not in html:
        raise ValueError(f"anchor {anchor!r} not found in the document")
    return html.replace(anchor, section + "\n\n" + anchor, 1), "inserted"
