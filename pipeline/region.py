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

    `anchor` may be a TUPLE of candidates, tried in order, first one present
    wins. That exists because one conditional region may anchor on another
    conditional region's marker: 最癲一局 anchors on 全消's BEGIN marker so that it
    lands above it, but on a report being built from a fresh skeleton NEITHER
    region exists yet, and on a session with no All Clear 全消 never will. A single
    anchor is right for the retrofit case (inserting into a report that already
    carries the other region) and impossible for the fresh case; the chain covers
    both, by naming the region it wants to precede first and a marker the skeleton
    always emits as the fallback. Order still comes out right in the fresh case:
    the earlier section inserts before the shared fallback first, and the later one
    then inserts before that same fallback, landing after it.

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
    candidates = (anchor,) if isinstance(anchor, str) else tuple(anchor)
    if not candidates:
        raise ValueError(f"region {start!r} not found and the anchor chain is empty")
    for candidate in candidates:
        if candidate in html:
            return html.replace(candidate, section + "\n\n" + candidate, 1), "inserted"
    raise ValueError(f"none of the anchors {list(candidates)!r} are in the document")
