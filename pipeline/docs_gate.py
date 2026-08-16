"""The document-parsing layer shared by the gates that re-derive published figures.

`pipeline/claims/check_equiv_coverage.py` grew a small parser for the three documents this
repo publishes figures into — a markdown table keyed by session, a per-session prose
sentence, and the membership rule that every session on disk appears exactly once. The
leave-one-out gate (`pipeline/check_loo.py`) needs the same primitives against the same
files, and **two parsers over one document is this repo's recurring failure shape**: they
agree the day they are written and diverge the first time either document is reworded, at
which point one gate reports a paragraph it cannot find and the other reports nothing at all.
So they live here once and both gates import them.

Nothing in this module knows what a figure MEANS. It locates blocks, splits cells, resolves
paragraphs and checks membership; every comparison against an artefact is a hook the caller
supplies. That split is what lets one parser serve a coverage percentage and a leave-one-out
shift without either gate's policy leaking into the other's.

Three rules the callers inherit by using it, each of which has a failure behind it:

* **A block the parser cannot find is a FAILURE, never a skip.** `REWORD` is the sentence
  every such failure ends with, and it names the file carrying the spec so the fix has an
  address. A gate that skips an unparseable document passes forever after one reword.
* **Absence is a failure too.** `row_membership` fails on a session on disk that the document
  does not publish, on a published session that is not on disk, on a duplicate, and on a
  session whose artefact is missing — the four ways a table can look complete and not be.
* **Session discovery is globbed, and what is left out is NAMED** (`pipeline/codegen.py:76-78`).
  `session_dirs` returns the exclusions rather than dropping them, and every caller prints them.
"""
import glob
import os
import re

_SESSION = re.compile(r"\d{4}-\d{2}-\d{2}")


def reword(spec_module):
    """The sentence every parse failure ends with. It names where the spec lives.

    A parse failure whose message does not say what to edit is a failure a reader routes
    around by deleting the paragraph, which is the outcome the gate exists to prevent.
    """
    return f"If you reworded it, update the spec in {spec_module} so the figures stay gated."


# --------------------------------------------------------------------------- sessions


def candidate_dirs(root, marker="claims*.json"):
    """Every `sessions/<date>/<sub>` directory carrying a claim ledger, sorted.

    Deliberately wider than `sessions/*/report`: a glob narrow enough to miss
    `sessions/2026-07-24/proof` would leave nothing to name, and naming what was left out is
    the whole point of the rule at pipeline/codegen.py:76-78.
    """
    out = []
    for d in sorted(glob.glob(os.path.join(root, "sessions", "*", "*"))):
        if os.path.isdir(d) and glob.glob(os.path.join(d, marker)):
            out.append(d)
    return out


def session_dirs(root, require=("facts.json", "claims-generated.json"), marker="claims*.json"):
    """(measurable, excluded) — excluded is [(dir, why)], and every caller prints it.

    `require` is the caller's list of inputs, because two gates need different ones: the
    coverage gate cannot measure a directory with no generated ledger, while the leave-one-out
    gate only reads facts.json. Widening the requirement would silently drop a session from
    one gate; narrowing it would make the other measure a directory it cannot measure. Both
    show up in `excluded`, which is printed either way.
    """
    measurable, excluded = [], []
    for d in candidate_dirs(root, marker):
        missing = [n for n in require if not os.path.exists(os.path.join(d, n))]
        if missing:
            excluded.append((d, "no " + " and no ".join(missing)))
        else:
            measurable.append((os.path.basename(os.path.dirname(d)), d))
    # Sessions are keyed by date everywhere below, so two measurable directories under one date
    # would have the second's artefact quietly replace the first's in every dict. Loud, because
    # the failure would look like a session that simply measured differently than expected.
    seen = [s for s, _ in measurable]
    dupes = sorted({s for s in seen if seen.count(s) > 1})
    if dupes:
        raise SystemExit(f"more than one measurable directory under {', '.join(dupes)}: "
                         + ", ".join(d for s, d in measurable if s in dupes))
    return measurable, excluded


# --------------------------------------------------------------------------- membership


def row_membership(name, listed, arts, artefact, noun="coverage"):
    """Every session on disk appears exactly once, and nothing else appears at all.

    Rules two and four between them already turn ABSENCE into a failure: a session on disk that
    the document does not name trips rule two, and one it does name whose artefact is missing
    trips rule four. `pipeline/check_loo.py` therefore has no second "a session on disk has no
    artefact" loop of its own — it wrote one, found no mutant could kill it (this call catches
    every case first), and deleted it. `check_equiv_coverage.py` still carries one; it is
    redundant with this in the same way, and is left alone only because its output is
    byte-compared against a committed baseline.
    """
    out = []
    for session in sorted(set(listed) - set(arts)):
        out.append(f"{name}: publishes a figure for {session}, which is not a session on disk")
    missing = sorted(set(arts) - set(listed))
    if missing:
        out.append(f"{name}: publishes {len(set(listed) & set(arts))} of the "
                   f"{len(arts)} sessions on disk — nothing is published for "
                   f"{', '.join(missing)}, so those sessions' {noun} is unmeasured in public")
    for session in sorted(s for s in set(listed) if listed.count(s) > 1):
        out.append(f"{name}: publishes {session} more than once")
    for session in sorted(s for s in set(listed) & set(arts) if arts[s] is None):
        out.append(f"{name}: publishes a figure for {session}, which has no {artefact} "
                   f"to check it against")
    return out


def granularity(name, published, arts, coarse, fine, message):
    """A coarse-granularity figure published with no fine companion, when a fine run exists.

    Both gates have a granularity pair whose coarser half is not the same measurement as the
    finer one, so the shape is shared and the SENTENCE is not: `message(name, have)` is the
    caller's, because what the coarse figure fails to see differs (the coverage gate's `match`
    enumerates fewer moves; the leave-one-out gate's `match` drops a whole match, whose rounds
    can cancel). A shared sentence would have to be vague enough to cover both, which is how a
    gate ends up saying something true and useless.
    """
    if coarse not in published or fine in published:
        return []
    have = sorted(s for s, a in arts.items() if a and fine in (a.get("modes") or {}))
    if not have:
        return []
    return [message(name, have)]


# --------------------------------------------------------------------------- paragraphs


def paragraph(text, anchor):
    """The whole blank-line-delimited paragraph holding `anchor`'s first match, or None.

    The WHOLE paragraph, not the tail from the anchor line: the qualifying token a gate looks
    for (a granularity label, a leave-one-out annotation) can sit ahead of the anchor as
    easily as after it, and reading only forwards would report a labelled paragraph as
    unlabelled. That bug was live in the coverage gate's `Prose.rows` before it was fixed the
    same way.
    """
    m = anchor.search(text)
    if m is None:
        return None
    # `rfind(...) + 2` on its own is off by one for the FIRST paragraph in a file: rfind
    # returns -1, +2 lands on index 1, and the paragraph silently loses its first character.
    # Harmless for an anchor that sits deep in a document, and not harmless at all for a gate
    # whose whole job is a substring match — check_loo found it with a synthetic document
    # whose annotation opens the file.
    cut = text.rfind("\n\n", 0, m.start())
    start = 0 if cut < 0 else cut + 2
    end = text.find("\n\n", m.start())
    return text[start:end if end >= 0 else len(text)]


# --------------------------------------------------------------------------- document specs


class Table:
    """A markdown table keyed by session, one column per key.

    `column(header_cell) -> key|None` names each column; `cell(name, session, art, key, text)`
    is the per-cell comparison; `per_table` and `per_row` are extra rules the caller layers on.
    All four are the caller's, so this class holds only the markdown.
    """

    def __init__(self, name, header, cell, column, reword, artefact,
                 per_table=(), per_row=(), subject="the coverage table", column_noun="mode"):
        self.name, self.header, self.cell, self.column = name, header, cell, column
        self.reword, self.artefact = reword, artefact
        self.per_table, self.per_row = tuple(per_table), tuple(per_row)
        self.subject, self.column_noun = subject, column_noun

    def rows(self, text):
        """(columns, [(session, {column index: cell text})]) or None if it cannot be found."""
        m = self.header.search(text)
        if not m:
            return None
        lines = text[m.start():].split("\n")
        block = []
        for line in lines:
            if not line.startswith("|"):
                break
            block.append([c.strip() for c in line.strip().strip("|").split("|")])
        if len(block) < 3:
            return None
        cols = [self.column(c) for c in block[0]]
        rows = []
        for cells in block[2:]:
            sm = _SESSION.search(cells[0] if cells else "")
            if not sm:
                return None
            rows.append((sm.group(0), dict(enumerate(cells))))
        return cols, rows

    def check(self, text, arts):
        parsed = self.rows(text)
        if parsed is None:
            return [f"{self.name}: could not parse {self.subject}. {self.reword}"]
        cols, rows = parsed
        out = row_membership(self.name, [s for s, _ in rows], arts, self.artefact)
        published = [c for c in cols if c and c != "identical"]
        if not published:
            return out + [f"{self.name}: {self.subject} publishes no {self.column_noun} "
                          f"column. {self.reword}"]
        for hook in self.per_table:
            out += hook(self.name, published, arts)
        for session, cells in rows:
            art = arts.get(session)
            if art is None:
                continue                       # already reported by row_membership
            for hook in self.per_row:
                out += hook(self.name, session, art, published)
            for i, key in enumerate(cols):
                if not key or i not in cells:
                    continue
                out += self.cell(self.name, session, art, key, cells[i])
        return out


class Prose:
    """A paragraph whose `item` regex yields one match per published figure.

    `verdict(spec, para, found, arts) -> [str]` is the caller's policy over the parse.
    """

    def __init__(self, name, anchor, item, verdict, reword, artefact,
                 subject="the per-session coverage sentence"):
        self.name, self.anchor, self.item, self.verdict = name, anchor, item, verdict
        self.reword, self.artefact, self.subject = reword, artefact, subject

    def rows(self, text):
        para = paragraph(text, self.anchor)
        if para is None:
            return None
        found = self.item.findall(para)
        return (para, found) if found else None

    def check(self, text, arts):
        parsed = self.rows(text)
        if parsed is None:
            return [f"{self.name}: could not parse {self.subject}. {self.reword}"]
        return self.verdict(self, parsed[0], parsed[1], arts)


def load_docs(root, names):
    """{name: text or None}. A document that is not on disk maps to None, and every caller
    turns that into a failure rather than a skip."""
    docs = {}
    for name in names:
        path = os.path.join(root, name)
        docs[name] = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                docs[name] = fh.read()
    return docs
