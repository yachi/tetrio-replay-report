"""Gate: a published pooled figure that one round carries must say so.

    python3 -m pipeline.check_loo --write      # regenerate each session's loo.json
    python3 -m pipeline.check_loo --check      # re-measure, byte-compare, then gate the prose
    python3 -m pipeline.check_loo --check-prose  # prose only, against the COMMITTED artefacts
    python3 -m pipeline.check_loo --render     # print the annotations to paste
    python3 -m pipeline.check_loo --selftest   # plant corruptions, require catches

**The case.** 2026-08-14's published lost-regime APP gap is +1.7795 pp. Drop one round of 84 —
m11r2 — and it becomes +4.6537, a shift of 2.8742 pp, rank 1 of 84 and 1.72x the next largest.
「The floors have met」 is substantially a statement about that one round, and the paragraph
saying it does not mention it. ROADMAP item 5 asked for a gate that generalises past this case.

**What is measured.** For every figure this repo publishes as a *round-pooled* finding, the
leave-one-round-out shift vector: the figure recomputed with each round deleted in turn. The
statistic is `rel` = the largest single-round shift divided by the figure's own absolute value
— scale-free, so a percentage-point gap and a count of attack lines are comparable, and a
figure whose value is near zero is correctly the most fragile kind.

**The threshold is DERIVED, not picked.** Over the 17 published figures, sorted by `rel`:

    20.931  08-01  in-game score difference    base   -576   m6r5 -> +11480 (the sign flips)
     2.267  07-28  attack difference           base    -15   m8r8 ->     -49 (the sign flips)
     1.615  08-14  APP gap, lost rounds        base +1.780  m11r2 ->  +4.654   <- the case above
     1.306  08-09  APP gap, won rounds         base +1.848   m2r5 ->  +4.262
     0.969  08-01  attack difference           base    -32   m1r4 ->      -1
    ------------------------------------------------ 2.386x, the widest gap below the case
     0.406  and below: the twelve ordinary regime-gap entries, correctly silent

All five above the gap are the same rhetorical move — 「these two totals have converged」 — and
the twelve below it are ordinary series entries. Every cut in (0.406, 0.969) gives the identical
partition; 2.386x is the widest gap among the cuts that still catch the motivating case (the
9.2x gap at the very top catches only one figure and would have missed it). `THRESHOLD = 0.5`
is that interval's round number. **0 false positives on the published population.**

Three alternatives were measured and rejected: the ratio of the top shift to the second (fires
on 23 of 285 catalogue figures — at these n the ratio is noise), the absolute shift (m11r2's
2.87 pp is only 1.17x the largest absolute shift anywhere, so it does not separate at all), and
a scale-free concentration score (fires on 145 of 285).

**The remedy is the caveat, not silence.** A figure at `rel >= THRESHOLD` is satisfied by its
sentence carrying the leave-one-out annotation this file renders — the reader is told which
round the sentence rests on, and the sentence stays. `ANNOTATED` is the named exception list
of the cases already investigated, one entry per (session, figure) with its reason, following
`DT_ORDER_IN_OPENER` in pipeline/sim/openers.test.ts: **relax to a named list so a sixth case
has to be investigated rather than absorbed, never to a loosened threshold.** A figure that is
named and no longer crosses fails too — an unearned caveat is as stale as a missing one.

**Round granularity only.** Leave-one-MATCH-out is a different question and this threshold is
not calibrated for it: at match granularity 11 of the 17 figures cross 0.5 and the neighbours
either side of the cut sit 1.24x apart, against 5 and 2.386x at round granularity. It is not
even an upper bound in either direction — 08-14 reads 1.310 by match against 1.615 by round
(m11r2 and m11r5 are both in match 11 and pull opposite ways), while 07-22's lost gap reads
0.507 by match against 0.149 by round. Both are derivable from the same stored terms, so the
artefact carries both granularities' standing and `--check` prints both distributions; only
`round` gates. That is stated in the artefact (`granularities`) rather than in prose, because
prose is not a gate.

**What this gate cannot see.** Figures that are not round-pooled sums, and figures nobody has
added to `PUBLISHED`. The first is a real limit with a good reason: the AUC block is a mean of
per-round scores in {0, 0.5, 1}, so one round moves it by at most 1/(n-1) — `rel` lands near
0.012 for every column in every session and the gate would have no reach there even if it
looked. The second is the manual-list class this repo has been bitten by, so it is closed from
the other side: every measurable session must appear in `PUBLISHED` at least once, and every
entry's sentence must still be findable in its document. A reworded or deleted sentence FAILS.

**The artefact stores the per-round TERMS, never `rel`.** Two reasons, both load-bearing. The
terms are integers, so the JSON is byte-stable and `--check` can compare bytes — the house rule
at tools/triangle-oracle/cross-extract.mjs:11-12. And storing `rel` alone would hide which round
moved the figure, which is the only thing a reader can act on; it is also what makes the match
granularity derivable from the same file instead of a second measurement.
"""
import argparse
import decimal
import json
import os
import re
import sys

from .docs_gate import load_docs, paragraph, reword, row_membership, session_dirs

ARTEFACT = "loo.json"
SCHEMA = "loo/1"
REWORD = reword("pipeline/check_loo.py")

THRESHOLD = 0.5

WHAT = (
    "Leave-one-round-out sensitivity of the round-pooled figures this repo publishes as "
    "findings: each figure recomputed with every round deleted in turn. `rel` is the largest "
    "single-round shift over the figure's own absolute value, derived at read time from the "
    "per-round terms stored here — never stored, because a stored ratio hides WHICH round "
    "moved the figure, and because integers are what make this file byte-stable. A figure at "
    "rel >= 0.5 is one round's statement as much as the session's, and its sentence has to say "
    "so. This measures fragility, not error: a fragile figure is not a wrong figure."
)

# The two granularities the stored terms support, and where the threshold is calibrated.
# Stated in the artefact because a reader downstream has no other way to know that the same
# file answers a question the gate deliberately does not ask.
GRANULARITIES = {
    "round": {"gated": True, "reason": None},
    "match": {"gated": False, "reason": (
        "dropping a whole match drops rounds that can pull opposite ways, so this is a "
        "different question and THRESHOLD is not calibrated for it — over the published "
        "population 11 of 17 figures cross 0.5 by match against 5 by round, and the "
        "neighbours either side of the cut sit 1.24x apart against 2.386x. Neither "
        "granularity bounds the other: 2026-08-14 reads 1.310 by match and 1.615 by round, "
        "2026-07-22's lost gap 0.507 by match and 0.149 by round.")},
}


# --------------------------------------------------------------------------- the figures

# id -> (what it is, kind, the kind's argument, the unit its shift is quoted in)
#
# `rate_gap` is 100 * (p2's attack per piece) / (p1's attack per piece) - 100 restricted to a
# regime, which is how every APP figure in CLAUDE.md is built. `diff` is p1's pooled field
# minus p2's. Players are POSITIONAL (facts["players"][0], [1]); nothing in this pipeline is
# bound to the two names any more and this gate does not reintroduce that.
FIGURES = {
    "app_gap_won": ("the APP gap over each side's own won rounds", "rate_gap", "won", "pp"),
    "app_gap_lost": ("the APP gap over each side's own lost rounds", "rate_gap", "lost", "pp"),
    "app_gap_session": ("the session-level APP gap", "rate_gap", "all", "pp"),
    "attack_diff": ("player 1's pooled attack minus player 2's", "diff", "garbage_attack", "行"),
    "score_diff": ("player 1's pooled in-game score minus player 2's", "diff", "score", "分"),
}

# How many integers each kind stores per round. A row of the wrong width is a build error, not
# a figure that silently folds a missing column in as zero.
TERM_WIDTH = {"rate_gap": 4, "diff": 2}


def round_terms(kind, arg, recs, winner, p1, p2):
    """One round's contribution to a figure, as integers.

    A round outside the figure's regime contributes zeros rather than being dropped, so every
    figure's `terms` is indexed by the same round list and one round's label means the same
    thing across all of them.
    """
    if kind == "rate_gap":
        keep = {pl: arg == "all" or ((winner == pl) == (arg == "won")) for pl in (p1, p2)}
        return [recs[p1]["garbage_attack"] if keep[p1] else 0,
                recs[p1]["pieces"] if keep[p1] else 0,
                recs[p2]["garbage_attack"] if keep[p2] else 0,
                recs[p2]["pieces"] if keep[p2] else 0]
    if kind == "diff":
        return [recs[p1][arg], recs[p2][arg]]
    raise ValueError(kind)


def value(kind, terms):
    """The pooled figure over a subset of rounds, or None where it is undefined."""
    if kind == "rate_gap":
        n1 = sum(t[0] for t in terms)
        d1 = sum(t[1] for t in terms)
        n2 = sum(t[2] for t in terms)
        d2 = sum(t[3] for t in terms)
        if not d1 or not d2 or not n1:
            return None
        return 100.0 * (n2 / d2) / (n1 / d1) - 100.0
    if kind == "diff":
        return float(sum(t[0] - t[1] for t in terms))
    raise ValueError(kind)


# --------------------------------------------------------------------------- the measurement


def label(match_index, round_index):
    """`m11r2` — the match's position in the session and the round's 1-based position in it.

    facts.json numbers rounds from 0 and matches from 1; the prose and the ROADMAP both say
    m11r2 for the second round of the eleventh match, so the label converts and the parser
    below reads the match number back out of it rather than storing it twice.
    """
    return f"m{match_index}r{round_index + 1}"


_LABEL = re.compile(r"^m(\d+)r(\d+)$")


def match_of(lbl):
    m = _LABEL.match(lbl)
    if not m:
        raise ValueError(f"{lbl!r} is not a round label")
    return int(m.group(1))


def build(session, report_dir):
    """Measure every figure `PUBLISHED` names for this session and shape the artefact."""
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    p1, p2 = facts["players"]
    rounds = [(label(m["index"], r["index"]), r["players"], r["winner"])
              for m in facts["matches"] for r in m["rounds"]]

    wanted = sorted({f for s, f, _ in PUBLISHED if s == session})
    if not wanted:
        # Every measurable session must be published somewhere; `problems` says so too, but a
        # --write that quietly produced an empty artefact would make that failure look like a
        # session whose figures happen to be safe.
        raise SystemExit(f"{session}: no entry in PUBLISHED. A session on disk with no "
                         f"published figure is the manual-list failure this gate is here to "
                         f"close — add its figures, or say in PUBLISHED why it has none.")
    figures = {}
    for fid in wanted:
        _, kind, arg, _unit = FIGURES[fid]
        figures[fid] = {"kind": kind,
                        "terms": [round_terms(kind, arg, recs, w, p1, p2)
                                  for _lbl, recs, w in rounds]}
    return {"schema": SCHEMA,
            "what": WHAT,
            "session": session,
            "granularities": GRANULARITIES,
            "rounds": [lbl for lbl, _, _ in rounds],
            "figures": figures}


def dumps(artefact):
    return json.dumps(artefact, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def artefact_path(report_dir):
    return os.path.join(report_dir, ARTEFACT)


# --------------------------------------------------------------------------- derived at read


def shifts(art, fid, granularity="round"):
    """[(shift, key, value_without)] sorted by shift descending, over the dropped keys.

    `key` is a round label at round granularity and `m<n>` at match granularity. A key whose
    removal leaves the figure undefined is skipped — that is a key the figure cannot be
    measured without, not a zero shift.
    """
    fig = art["figures"][fid]
    kind, terms, labels = fig["kind"], fig["terms"], art["rounds"]
    base = value(kind, terms)
    if base is None:
        return None
    keys = [lbl if granularity == "round" else f"m{match_of(lbl)}" for lbl in labels]
    out = []
    for key in dict.fromkeys(keys):
        kept = [t for t, k in zip(terms, keys) if k != key]
        v = value(kind, kept)
        if v is None:
            continue
        out.append((abs(v - base), key, v))
    out.sort(reverse=True)
    return out


def measured(art, fid, granularity="round"):
    """(base, rel, top shift, top key, value without it, ratio to the next), or None.

    `rel` is inf where the figure's own value is 0 — a figure sitting exactly on zero is
    carried entirely by whichever round is dropped, which is the fragile end of the scale and
    not a division to be guarded away.
    """
    got = shifts(art, fid, granularity)
    if not got or len(got) < 2:
        return None
    base = value(art["figures"][fid]["kind"], art["figures"][fid]["terms"])
    top, second = got[0], got[1]
    rel = top[0] / abs(base) if base else float("inf")
    ratio = top[0] / second[0] if second[0] else float("inf")
    return base, rel, top[0], top[1], top[2], ratio


# --------------------------------------------------------------------------- the formatter


def _down(x, places):
    """|x| truncated toward zero at `places`, sign preserved, as a Decimal.

    Toward zero, not floor: these are quoted magnitudes, and flooring -0.9999 to -1.00 would
    state a bigger movement than was measured. pipeline/fmt.py floors because 約 has to mean
    "at least this much"; nothing here is 約, and the safe direction for a signed value quoted
    without 約 is the one that never overstates it.
    """
    q = decimal.Decimal(1).scaleb(-places)
    d = decimal.Decimal(repr(x)).quantize(q, rounding=decimal.ROUND_DOWN)
    return d


def fmt_value(x, unit):
    """THE formatter for a value this gate publishes. Renderer and parser share it."""
    if unit == "pp":
        return f"{_down(x, 2):+.2f}%"
    return f"{int(_down(x, 0)):+d} {unit}"


def fmt_shift(x, unit):
    """THE formatter for a shift magnitude. Always non-negative, so truncation is a floor."""
    if unit == "pp":
        return f"{_down(x, 2):.2f} pp"
    return f"{int(_down(x, 0))} {unit}"


# A CJK glyph or a CJK/full-width punctuation mark. Chinese text wraps between ANY two of
# these, so a newline the author inserted there is not a space the annotation ever had.
_CJK = "　-〿一-鿿＀-￯"


def _norm(s):
    """Collapse whitespace runs to one space, then drop any space touching a CJK glyph.

    The documents are hard-wrapped at ~100 columns, so an annotation pasted into a paragraph
    is going to have a newline somewhere inside it. Comparing raw would make the gate fail on
    line wrapping, which teaches a reader to reflow the paragraph rather than read the gate.

    Collapsing alone is not enough and the reason is worth keeping: Chinese wraps between two
    adjacent glyphs, where the annotation has no space at all, so `行，\\n即係` would collapse
    to `行， 即係` and miss. Dropping spaces adjacent to CJK models exactly that wrap and
    nothing else — a space between two ASCII tokens survives, so `m1 1r2` still fails to match
    `m11r2`, which a blanket whitespace strip would have waved through.
    """
    s = " ".join(s.split())
    s = re.sub(f"(?<=[{_CJK}]) ", "", s)
    return re.sub(f" (?=[{_CJK}])", "", s)


def annotation(art, fid):
    """The exact string the figure's sentence must contain, or None if it is not measurable.

    One sentence, rendered here and searched for verbatim (modulo line wrapping, see `_norm`),
    so `--render` prints what to paste and a reworded annotation is a failure rather than a
    near-miss nobody notices.
    """
    if not readable(art, fid):
        return None
    got = measured(art, fid)
    if got is None:
        return None
    _base, _rel, shift, key, without, _ratio = got
    unit = FIGURES[fid][3]
    return (f"（留一局：抽走 {key}，數字變 {fmt_value(without, unit)}，"
            f"即係郁 {fmt_shift(shift, unit)}）")


# --------------------------------------------------------------------------- the population

# key -> (document, the regex that finds the sentence, what the sentence says)
#
# A regex and not a line number: CLAUDE.md is edited constantly and a line number would rot
# into a gate that checks the wrong paragraph while still passing. The whole PARAGRAPH is
# read (docs_gate.paragraph), because an annotation reads as well before the figure as after.
SENTENCES = {
    "regimes_0809": ("CLAUDE.md", re.compile(r"the two regimes come\s+apart"),
                     "2026-08-09's won/lost regime decomposition"),
    "series": ("CLAUDE.md", re.compile(r"won-gap runs"),
               "the per-session won-gap / lost-gap series"),
    "regimes_0814": ("CLAUDE.md", re.compile(r"Same decomposition, opposite answer"),
                     "2026-08-14's won/lost regime decomposition"),
    "session_gap": ("CLAUDE.md", re.compile(r"the \*session-level\* APP gap"),
                    "the session-level APP gap for 08-09 and 08-14"),
    "totals_0728": ("CLAUDE.md", re.compile(r"Both totals are nearly equal"),
                    "2026-07-28's near-equal attack totals"),
    "totals_0801": ("CLAUDE.md", re.compile(r"totals land on top of each other"),
                    "2026-08-01's near-equal attack and score totals"),
}

# (session, figure id, the sentence that publishes it). Every measurable session must appear.
PUBLISHED = (
    ("2026-07-22", "app_gap_won", "series"),
    ("2026-07-22", "app_gap_lost", "series"),
    ("2026-07-24", "app_gap_won", "series"),
    ("2026-07-24", "app_gap_lost", "series"),
    ("2026-07-28", "app_gap_won", "series"),
    ("2026-07-28", "app_gap_lost", "series"),
    ("2026-07-28", "attack_diff", "totals_0728"),
    ("2026-08-01", "app_gap_won", "series"),
    ("2026-08-01", "app_gap_lost", "series"),
    ("2026-08-01", "attack_diff", "totals_0801"),
    ("2026-08-01", "score_diff", "totals_0801"),
    ("2026-08-09", "app_gap_won", "regimes_0809"),
    ("2026-08-09", "app_gap_lost", "regimes_0809"),
    ("2026-08-09", "app_gap_session", "session_gap"),
    ("2026-08-14", "app_gap_won", "regimes_0814"),
    ("2026-08-14", "app_gap_lost", "regimes_0814"),
    ("2026-08-14", "app_gap_session", "session_gap"),
)

# The named exception list: every (session, figure) already investigated, with the reason it
# crosses. Named, not a raised threshold — a sixth case must be looked at, and a case that
# stops crossing must be taken off the list and out of the prose.
ANNOTATED = {
    ("2026-08-01", "score_diff"): (
        "the two in-game score totals are 0.05% apart, so their difference is -576 against "
        "totals near 1.09 million; m6r5 alone is +12056 and flips the sign. The convergence "
        "is real at session scale and the DIFFERENCE is not a stable quantity."),
    ("2026-07-28", "attack_diff"): (
        "the attack totals are 3264 vs 3249, so the difference is -15 and m8r8's 34 flips "
        "the sign. 「Both totals are nearly equal」 survives; 「yachi is 15 behind」 does not."),
    ("2026-08-14", "app_gap_lost"): (
        "ROADMAP item 5's motivating case. m11r2 moves the lost-regime gap 1.7795 -> 4.6537, "
        "rank 1 of 84 and 1.72x the next; 「the floors have met」 rests on that round. See "
        "the memory note m11r2-carries-the-floors-met-headline."),
    ("2026-08-09", "app_gap_won"): (
        "the mirror of the case above, one session earlier: m2r5 moves the won-regime gap "
        "1.8480 -> 4.2616. 「+1.8, the smallest in the corpus」 is the same shape of "
        "statement and rests on one round the same way."),
    ("2026-08-01", "attack_diff"): (
        "the attack totals are 3394 vs 3426, difference -32, and m1r4's 31 takes it to -1. "
        "「within 32 lines」 is a figure one round owns; 「the totals land on top of each "
        "other」 is not."),
}


# --------------------------------------------------------------------------- the gate


def load_artefacts(root):
    """{session: artefact or None}. A session on disk with no artefact maps to None."""
    arts = {}
    for session, d in session_dirs(root, require=("facts.json",))[0]:
        path = artefact_path(d)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                arts[session] = json.load(fh)
        else:
            arts[session] = None
    return arts


def _artefact_problems(session, art, published):
    out = []
    if art.get("schema") != SCHEMA:
        out.append(f"{session}: {ARTEFACT} declares schema {art.get('schema')!r}, want {SCHEMA!r}")
    if art.get("session") != session:
        out.append(f"{session}: {ARTEFACT} names session {art.get('session')!r}")
    if not art.get("what"):
        out.append(f"{session}: {ARTEFACT} carries no `what` — it would travel without the "
                   f"sentence saying this measures fragility and not error")
    if art.get("granularities") != GRANULARITIES:
        out.append(f"{session}: {ARTEFACT}'s `granularities` block does not match this "
                   f"file's. The match granularity's standing is stated in the artefact, not "
                   f"in prose; an artefact carrying a different one publishes a limit the "
                   f"gate does not honour")
    out += rounds_problems(session, art)
    figs = art.get("figures") or {}
    for fid in sorted({f for s, f, _ in published if s == session}):
        if fid not in figs:
            out.append(f"{session}: {ARTEFACT} carries no `{fid}`, which PUBLISHED says the "
                       f"documents quote. Absence is a failure here, not a skip")
            continue
        out += figure_problems(session, art, fid)
    for fid in sorted(set(figs) - {f for s, f, _ in published if s == session}):
        out.append(f"{session}: {ARTEFACT} carries `{fid}`, which PUBLISHED does not name. "
                   f"A measured figure nothing publishes is measured against nothing")
    return out


def rounds_problems(session, art):
    """The round list's own shape. Split out because `readable` below needs the predicate."""
    labels = art.get("rounds")
    if not isinstance(labels, list) or not labels:
        return [f"{session}: {ARTEFACT} carries no round list"]
    out = []
    bad = [x for x in labels if not (isinstance(x, str) and _LABEL.match(x))]
    if bad:
        out.append(f"{session}: {ARTEFACT} carries round label(s) {bad[:3]} that are not m<n>r<n>")
    if len(set(labels)) != len(labels):
        out.append(f"{session}: {ARTEFACT} repeats a round label, so a shift cannot be "
                   f"attributed to one round")
    return out


def figure_problems(session, art, fid):
    """One figure's own shape, as strings. Empty means `measured()` can read it."""
    fig = (art.get("figures") or {}).get(fid)
    if fig is None:
        return [f"{session}: {ARTEFACT} carries no `{fid}`"]
    want_kind = FIGURES[fid][1]
    if fig.get("kind") != want_kind:
        return [f"{session}: {fid} declares kind {fig.get('kind')!r}, want {want_kind!r}"]
    terms, labels = fig.get("terms"), art.get("rounds") or []
    if not isinstance(terms, list) or len(terms) != len(labels):
        return [f"{session}: {fid} carries {len(terms or [])} term rows against "
                f"{len(labels)} rounds — a figure indexed by a different round list "
                f"cannot name the round that moved it"]
    width = TERM_WIDTH[want_kind]
    if any(not isinstance(t, list) or len(t) != width
           or any(not isinstance(v, int) or isinstance(v, bool) for v in t)
           for t in terms):
        return [f"{session}: {fid}'s terms are not rows of {width} integers — a "
                f"non-integer term makes this file's bytes unstable, and a short row "
                f"folds a missing column in as zero"]
    return []


def readable(art, fid):
    """Can `measured()` read this figure at all?

    ONE predicate, used by the reporter above and by every consumer below. Deriving a number
    from an artefact whose shape has not been checked is how a gate ends up dying with an
    IndexError instead of printing the problem it was about to print — which is exactly what
    the planted short-row mutant did before this split existed. A traceback is not a verdict.
    """
    session = art.get("session", "?")
    return not (rounds_problems(session, art) or figure_problems(session, art, fid))


def distribution(arts, published, granularity="round"):
    """[(rel, session, fid, base, shift, key, without, ratio)] sorted by rel descending.

    Figures whose shape `readable` rejects are left out; `problems` reports them instead.
    """
    out = []
    for session, fid, _sentence in published:
        art = arts.get(session)
        if art is None or fid not in (art.get("figures") or {}) or not readable(art, fid):
            continue
        got = measured(art, fid, granularity)
        if got is None:
            continue
        base, rel, shift, key, without, ratio = got
        out.append((rel, session, fid, base, shift, key, without, ratio))
    out.sort(key=lambda r: -r[0])
    return out


def problems(arts, docs, published=PUBLISHED, annotated=ANNOTATED, sentences=SENTENCES):
    """Every problem in (artefacts, documents), as strings. Pure — no filesystem, no measuring."""
    out = []
    if not arts:
        out.append("no measurable sessions found at all — the glob found nothing to check")

    # Membership, through the same helper the coverage gate uses, and it carries the whole of
    # the absence rule: a session on disk that PUBLISHED does not name is a figure nobody
    # gated (the manual-list failure), and one it does name with no artefact on disk is the
    # missing-artefact failure. A second loop for the latter was written here and deleted —
    # no mutant could kill it, because this call reports every case first.
    out += row_membership("PUBLISHED", sorted({s for s, _, _ in published}), arts, ARTEFACT,
                          noun="leave-one-out sensitivity")

    for session in sorted(s for s, a in arts.items() if a):
        out += _artefact_problems(session, arts[session], published)

    # Every sentence PUBLISHED points at must still be findable, and its document must exist.
    paras = {}
    for key, (doc, anchor, says) in sorted(sentences.items()):
        if not any(k == key for _s, _f, k in published):
            out.append(f"{key}: names {says}, which PUBLISHED does not point any figure at. "
                       f"A sentence spec nothing uses is a spec nobody maintains")
            continue
        text = docs.get(doc)
        if text is None:
            out.append(f"{doc}: not found, so {says} cannot be checked. {REWORD}")
            continue
        para = paragraph(text, anchor)
        if para is None:
            out.append(f"{doc}: could not find {says}. {REWORD}")
            continue
        paras[key] = para

    for rel, session, fid, _base, _shift, _key, _without, _ratio in distribution(arts, published):
        art, named = arts[session], (session, fid) in annotated
        want = annotation(art, fid)
        sentence = next(k for s, f, k in published if (s, f) == (session, fid))
        says = sentences[sentence][2]
        if rel >= THRESHOLD and not named:
            out.append(
                f"{session} {fid}: one round moves this figure by {rel:.3f} of its own value "
                f"(threshold {THRESHOLD}), and it is not in ANNOTATED. This is a case past the "
                f"five the threshold was derived over — investigate it and add it BY NAME with "
                f"its reason, never by raising the threshold. Paste into {says}: {want}")
        elif rel < THRESHOLD and named:
            out.append(
                f"{session} {fid}: ANNOTATED names this figure, but one round now moves it by "
                f"only {rel:.3f} of its own value. The caveat in {says} is unearned — take it "
                f"out of both, or say in ANNOTATED why it stays")
        if not named:
            continue
        para = paras.get(sentence)
        if para is None:
            continue                       # already reported above
        if _norm(want) not in _norm(para):
            out.append(
                f"{session} {fid}: {says} carries no leave-one-out annotation, or a stale one. "
                f"The gate's remedy is the caveat, not silence — the sentence stays and gains: "
                f"{want}")
    return out


# --------------------------------------------------------------------------- rendering


def render(arts, published=PUBLISHED, annotated=ANNOTATED, sentences=SENTENCES):
    """The annotations to paste, and the distribution the threshold rests on."""
    lines = []
    for (session, fid), why in sorted(annotated.items()):
        art = arts.get(session)
        if art is None or fid not in (art.get("figures") or {}):
            lines.append(f"{session} {fid}: no artefact to render from")
            continue
        sentence = next((k for s, f, k in published if (s, f) == (session, fid)), None)
        says = sentences[sentence][2] if sentence else "(no sentence in PUBLISHED)"
        lines.append(f"{session} {fid} -> {says}\n    {annotation(art, fid)}\n    why: {why}")
    return "\n".join(lines) + "\n"


def print_distribution(arts, published=PUBLISHED, annotated=ANNOTATED, granularity="round"):
    """The sorted `rel` distribution, every run.

    The threshold rests on a 2.386x gap in a 17-figure population over six sessions. A seventh
    session that fills the gap in must be VISIBLE rather than silently absorbed, and the only
    thing that makes it visible is printing the distribution whether or not anything failed.
    """
    rows = distribution(arts, published, granularity)
    gate = " (gated)" if GRANULARITIES[granularity]["gated"] else " (NOT gated)"
    print(f"\n  leave-one-{granularity}-out, sorted by rel = |largest shift| / |value|"
          f"{gate}")
    print(f"      {'rel':>8s}  {'session':11s} {'figure':17s} {'value':>11s} "
          f"{'drop':>7s} {'shift':>10s} {'becomes':>11s} {'x2nd':>5s}")
    prev, crossed = None, 0
    for rel, session, fid, base, shift, key, without, ratio in rows:
        if prev is not None and prev >= THRESHOLD > rel:
            print(f"      {'-' * 8}  threshold {THRESHOLD} — the gap here is "
                  f"{prev:.3f} -> {rel:.3f} = {prev / rel:.3f}x "
                  f"(2.386x when it was derived)")
        prev = rel
        crossed += rel >= THRESHOLD
        mark = "  " if (session, fid) not in annotated else "* "
        print(f"  {mark}  {rel:8.3f}  {session:11s} {fid:17s} {base:11.4f} {key:>7s} "
              f"{shift:10.4f} {without:11.4f} {ratio:5.2f}")
    if prev is not None and prev >= THRESHOLD:
        print(f"      {'-' * 8}  threshold {THRESHOLD} — nothing below it in this population")
    print(f"      {crossed} of {len(rows)} figures at or above {THRESHOLD}; "
          f"`*` marks the ones ANNOTATED names")
    return rows


# --------------------------------------------------------------------------- selftest


def _synthetic():
    """Two sessions of hand-built terms: one fragile figure, one ordinary, one immune."""
    def rounds(n, match_size=4):
        return [label(i // match_size + 1, i % match_size) for i in range(n)]

    labels = rounds(12)
    # A `diff` whose per-round terms cancel to a near-zero total, with one round carrying it:
    # 11 rounds of (10, 10) and one of (10, 4) -> base +6, drop it and the base is 0. rel = 1.0.
    fragile = [[10, 10]] * 11 + [[10, 4]]
    # An ordinary `diff`: a base of +60 no single round can move by more than 6. rel = 0.1.
    ordinary = [[16, 10]] * 12
    # A rate gap that sits far from zero: every round identical, so every shift is 0.
    flat = [[60, 100, 66, 100]] * 12

    def art(session, figs):
        return {"schema": SCHEMA, "what": WHAT, "session": session,
                "granularities": json.loads(json.dumps(GRANULARITIES)),
                "rounds": labels,
                "figures": {fid: {"kind": FIGURES[fid][1], "terms": t}
                            for fid, t in figs.items()}}

    return {"2026-01-01": art("2026-01-01", {"attack_diff": fragile, "score_diff": ordinary}),
            "2026-01-02": art("2026-01-02", {"app_gap_won": flat})}


_SYN_SENTENCES = {
    "fragile": ("CLAUDE.md", re.compile(r"the two totals converged"), "the fragile sentence"),
    "ordinary": ("CLAUDE.md", re.compile(r"the ordinary series"), "the ordinary sentence"),
    "flat": ("CLAUDE.md", re.compile(r"the flat gap"), "the flat sentence"),
}

_SYN_PUBLISHED = (
    ("2026-01-01", "attack_diff", "fragile"),
    ("2026-01-01", "score_diff", "ordinary"),
    ("2026-01-02", "app_gap_won", "flat"),
)

_SYN_ANNOTATED = {("2026-01-01", "attack_diff"): "the planted fragile case"}


def _syn_doc(arts, annotated=None):
    """A CLAUDE.md holding all three sentences, each annotated where ANNOTATED says so."""
    annotated = _SYN_ANNOTATED if annotated is None else annotated
    out = []
    for session, fid, key in _SYN_PUBLISHED:
        body = {"fragile": "the two totals converged", "ordinary": "the ordinary series",
                "flat": "the flat gap"}[key]
        note = ""
        if (session, fid) in annotated:
            note = " " + (annotation(arts[session], fid) or "")
        out.append(f"prelude — {body} this session.{note}")
    return {"CLAUDE.md": "\n\n".join(out) + "\n"}


def _selftest(root):
    arts = _synthetic()
    docs = _syn_doc(arts)

    def run(a, d, published=_SYN_PUBLISHED, annotated=None):
        return problems(a, d, published,
                        _SYN_ANNOTATED if annotated is None else annotated, _SYN_SENTENCES)

    cases: list[tuple[str, object, object, dict, bool]] = [
        ("control: the fragile figure is annotated, the ordinary one is silent",
         arts, docs, _SYN_ANNOTATED, False)]

    # The synthetic fragile figure is built to be measurable, so this is a statement about the
    # fixture rather than a guard — but `annotation` returns None for an unreadable figure and
    # every mutant below rewrites this string, so a fixture that stopped producing one would
    # otherwise plant `None` into a dozen cases and fail them for the wrong reason.
    ann = annotation(arts["2026-01-01"], "attack_diff")
    assert ann is not None, "the synthetic fragile figure must render an annotation"

    # 1. the annotation is deleted from the prose
    stripped = {"CLAUDE.md": docs["CLAUDE.md"].replace(ann, "")}
    cases.append(("the annotation is deleted from the sentence", arts, stripped,
                  _SYN_ANNOTATED, True))

    # 2. the annotation quotes the wrong shift
    cases.append(("the annotation quotes the wrong shift", arts,
                  {"CLAUDE.md": docs["CLAUDE.md"].replace(ann, ann.replace("郁 6", "郁 3"))},
                  _SYN_ANNOTATED, True))

    # 3. the annotation names the wrong round
    cases.append(("the annotation names the wrong round", arts,
                  {"CLAUDE.md": docs["CLAUDE.md"].replace(ann, ann.replace("m3r4", "m1r1"))},
                  _SYN_ANNOTATED, True))

    # 4. a SIXTH case appears and nobody named it — the mutant the exception list exists for
    crossed = json.loads(json.dumps(arts))
    crossed["2026-01-01"]["figures"]["score_diff"]["terms"][0] = [16, 70]
    cases.append(("a second figure crosses the threshold and is not in ANNOTATED",
                  crossed, _syn_doc(crossed), _SYN_ANNOTATED, True))

    # 5. ...and the control that says what that rule is NOT: the same figure crossing IS
    #    accepted once it is named AND its sentence carries the annotation. Without this the
    #    rule could be "never let two figures cross", which is a threshold in disguise.
    both = dict(_SYN_ANNOTATED)
    both[("2026-01-01", "score_diff")] = "named in the control"
    cases.append(("control: the same second crossing, named and annotated",
                  crossed, _syn_doc(crossed, both), both, False))

    # 6. a named figure stops crossing — an unearned caveat is as stale as a missing one
    calmed = json.loads(json.dumps(arts))
    calmed["2026-01-01"]["figures"]["attack_diff"]["terms"] = [[16, 10]] * 12
    cases.append(("a named figure no longer crosses the threshold", calmed,
                  _syn_doc(calmed), _SYN_ANNOTATED, True))

    # 7. the sentence is reworded past the parser
    cases.append(("the sentence is reworded past the parser", arts,
                  {"CLAUDE.md": docs["CLAUDE.md"].replace("the two totals converged",
                                                          "they ended up close")},
                  _SYN_ANNOTATED, True))

    # 8. a session PUBLISHED names whose artefact is absent. Named, not unnamed: an unnamed
    #    one trips the not-on-disk rule instead (case 9 is that one), and the absence rule
    #    would then have no mutant of its own.
    cases.append(("a session PUBLISHED names has no artefact",
                  {**arts, "2026-01-01": None}, docs, _SYN_ANNOTATED, True))

    # 9. a session on disk that PUBLISHED does not name at all. Its artefact carries NO figure,
    #    on purpose: an artefact with a figure would also trip the orphan-figure rule below, and
    #    a mutant two guards catch proves neither of them.
    extra = json.loads(json.dumps(arts))
    extra["2026-01-09"] = json.loads(json.dumps(arts["2026-01-02"]))
    extra["2026-01-09"]["session"] = "2026-01-09"
    extra["2026-01-09"]["figures"] = {}
    cases.append(("a session on disk is in no PUBLISHED entry", extra, docs,
                  _SYN_ANNOTATED, True))

    # 10. the terms and the round list disagree in length. On the UNANNOTATED figure, because
    #     shortening the annotated one also changes its rendered annotation and the prose check
    #     would catch it — leaving the length guard itself unproved. (It was: the deletion sweep
    #     said so.) Truncated terms zip silently against the round list, so with no length guard
    #     this measures a figure over 11 of 12 rounds and reports nothing at all.
    short = json.loads(json.dumps(arts))
    short["2026-01-01"]["figures"]["score_diff"]["terms"].pop()
    cases.append(("a figure's terms are shorter than the round list", short, docs,
                  _SYN_ANNOTATED, True))

    # 11. a term is a float — byte-stability, and the reason `rel` is not stored
    floaty = json.loads(json.dumps(arts))
    floaty["2026-01-01"]["figures"]["attack_diff"]["terms"][0] = [10.0, 10]
    cases.append(("a term is a float rather than an integer", floaty, docs,
                  _SYN_ANNOTATED, True))

    # 11b. a term ROW is short. Distinct from 11 above and from 10: a two-integer row where
    # four are expected folds the missing columns in as zero, which is a figure measured over
    # a regime nobody asked for rather than a figure that fails to parse.
    narrow = json.loads(json.dumps(arts))
    narrow["2026-01-02"]["figures"]["app_gap_won"]["terms"][0] = [60, 100]
    cases.append(("a figure's term row is narrower than its kind", narrow, docs,
                  _SYN_ANNOTATED, True))

    # 11c. a round label that is not m<n>r<n>. The match granularity is derived by reading the
    # match number back out of the label, so an unparseable one is a file that cannot answer
    # the question the `granularities` block says it can.
    mislabelled = json.loads(json.dumps(arts))
    mislabelled["2026-01-01"]["rounds"][0] = "round one"
    cases.append(("a round label is not m<n>r<n>", mislabelled, docs, _SYN_ANNOTATED, True))

    # 11d. two rounds carrying the same label — a shift could then be attributed to either.
    doubled = json.loads(json.dumps(arts))
    doubled["2026-01-01"]["rounds"][1] = doubled["2026-01-01"]["rounds"][0]
    cases.append(("two rounds carry the same label", doubled, docs, _SYN_ANNOTATED, True))

    # 12. the granularity block is edited so the artefact publishes a limit the gate ignores
    regran = json.loads(json.dumps(arts))
    regran["2026-01-02"]["granularities"]["match"]["gated"] = True
    cases.append(("the artefact claims the match granularity is gated", regran, docs,
                  _SYN_ANNOTATED, True))

    # 13. an artefact carries a figure PUBLISHED does not name
    orphan = json.loads(json.dumps(arts))
    orphan["2026-01-02"]["figures"]["app_gap_lost"] = {
        "kind": "rate_gap", "terms": [[60, 100, 66, 100]] * 12}
    cases.append(("an artefact measures a figure nothing publishes", orphan, docs,
                  _SYN_ANNOTATED, True))

    # 13b. the annotation sits BEFORE the anchor phrase, in the same paragraph. A control, and
    # the only thing that pins docs_gate.paragraph to reading the whole paragraph rather than
    # forwards from the anchor: an author who leads with the caveat is writing the same
    # sentence, and a gate that only reads forwards would call it missing.
    ahead = {"CLAUDE.md": docs["CLAUDE.md"].replace(
        f"prelude — the two totals converged this session. {ann}",
        f"{ann} — 所以 the two totals converged this session.")}
    cases.append(("control: the annotation leads the sentence instead of trailing it",
                  arts, ahead, _SYN_ANNOTATED, False))

    # 14-16. the whitespace tolerance, stated in both directions. The two controls say the
    # gate survives a markdown reflow (Chinese wraps between two glyphs, where the annotation
    # has no space); the mutant says the tolerance is not a blanket whitespace strip, because
    # a space inside the round label names a different round.
    for what, was, now, must_fail in (
            ("control: the annotation survives a line wrap at a space",
             "抽走 m3r4", "抽走\nm3r4", False),
            ("control: the annotation survives a line wrap between two CJK glyphs",
             "行，即係", "行，\n即係", False),
            ("a space is planted inside the round label", "m3r4", "m3 r4", True)):
        text = docs["CLAUDE.md"].replace(was, now)
        assert text != docs["CLAUDE.md"], was     # a no-op mutant proves nothing
        cases.append((what, arts, {"CLAUDE.md": text}, _SYN_ANNOTATED, must_fail))

    ok = True
    for name, a, d, annotated, must_fail in cases:
        failed = bool(run(a, d, annotated=annotated))
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if failed else 'accepted'}"
              f"{'' if good else '  <- expected ' + ('rejection' if must_fail else 'acceptance')}")

    # The match granularity must NOT gate. Same planted crossing, read at match granularity:
    # its rel crosses there too, and the gate must still be reading `round`. Without this the
    # "round granularity only" sentence in the docstring is documentation, not behaviour.
    mrows = distribution(arts, _SYN_PUBLISHED, "match")
    rrows = distribution(arts, _SYN_PUBLISHED, "round")
    mrel = {(s, f): rel for rel, s, f, *_ in mrows}
    rrel = {(s, f): rel for rel, s, f, *_ in rrows}
    good = mrel != rrel and not run(arts, docs)
    ok &= good
    print(f"  {'ok ' if good else 'BAD'} control: the two granularities disagree "
          f"({rrel.get(('2026-01-01', 'score_diff'), 0):.3f} by round vs "
          f"{mrel.get(('2026-01-01', 'score_diff'), 0):.3f} by match) and only `round` gates")

    # The formatter is the renderer AND the parser, so a rendered annotation must be found in
    # the text it was rendered into. A format only this file agrees with would pass every case
    # above while gating nothing publishable.
    good = ann in docs["CLAUDE.md"]
    ok &= good
    print(f"  {'ok ' if good else 'BAD'} control: a rendered annotation is found by the parser")

    # ...and it is still found once markdown wraps it, which is the only tolerance `_norm`
    # buys. A control rather than a mutant: without it the whitespace collapse could be
    # tightened back to an exact match and every case above would still pass, leaving a gate
    # that fails on a reflowed paragraph and teaches people to delete the annotation.
    # ...and pinned to the REAL document: every sentence PUBLISHED points at must still be
    # locatable in the committed CLAUDE.md. The figures there are allowed to be stale (the
    # annotations are not written yet); the sentences must still be FOUND.
    live = load_docs(root, sorted({d for d, _, _ in SENTENCES.values()}))
    for key, (doc, anchor, says) in sorted(SENTENCES.items()):
        text = live.get(doc)
        good = text is not None and paragraph(text, anchor) is not None
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} control: the committed {doc} still carries "
              f"{says}: {'located' if good else 'NOT FOUND — the gate anchors nothing'}")

    planted = sum(1 for c in cases if c[4])
    print(f"{'ok ' if ok else 'FAIL'} selftest {planted} corruptions, "
          f"{'all caught' if ok else 'SOME MISSED'}")
    return 0 if ok else 1


# --------------------------------------------------------------------------- main


def _report(out, note):
    # The distribution above went to stdout and these go to stderr; in a CI log the two are
    # interleaved by buffering, and a failure printed before the table it refers to reads as a
    # failure about nothing.
    sys.stdout.flush()
    for line in out:
        print(f"FAIL {line}", file=sys.stderr)
    if out:
        print(f"\n{len(out)} problem(s). {note}", file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.join(os.path.dirname(__file__), ".."),
                    help="repository root (default: this file's)")
    ap.add_argument("--write", action="store_true", help="re-measure and write the artefacts")
    ap.add_argument("--check", action="store_true",
                    help="re-measure, byte-compare the artefacts, then gate the prose")
    ap.add_argument("--check-prose", action="store_true", dest="check_prose",
                    help="gate the prose against the COMMITTED artefacts, without re-measuring")
    ap.add_argument("--render", action="store_true",
                    help="print the annotations to paste into the documents")
    ap.add_argument("--selftest", action="store_true",
                    help="plant corruptions and require the gate to catch them, then exit")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    if args.selftest:
        return _selftest(root)

    measurable, excluded = session_dirs(root, require=("facts.json",))
    for d, why in excluded:
        # Named, never silently skipped — pipeline/codegen.py:76-78.
        print(f"  --  {os.path.relpath(d, root)}: not measured ({why})")
    if not measurable:
        print(f"FAIL no measurable session found under {root}/sessions", file=sys.stderr)
        return 1

    if args.render:
        print(render(load_artefacts(root)), end="")
        return 0

    if args.check_prose and not (args.write or args.check):
        arts = load_artefacts(root)
        docs = load_docs(root, sorted({d for d, _, _ in SENTENCES.values()}))
        for gran in GRANULARITIES:
            print_distribution(arts, granularity=gran)
        rc = _report(problems(arts, docs),
                     "--check-prose does NOT re-measure: it gates the documents against the "
                     "COMMITTED artefacts. Run --check for the byte-identity half. Paste the "
                     "annotations with --render.")
        if rc == 0:
            print(f"\n  ok  {len(arts)} sessions' artefacts and every sentence publishing "
                  f"them agree (no re-measurement — that is --check)")
        return rc

    if not (args.write or args.check):
        ap.error("one of --write, --check, --check-prose, --render, --selftest is required")

    fresh, stale = {}, []
    for session, d in measurable:
        art = build(session, d)
        path = artefact_path(d)
        if args.write:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(dumps(art))
            print(f"wrote {os.path.relpath(path, root)}")
            continue
        raw = ""
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                raw = fh.read()
        if not raw.strip().startswith("{"):
            stale.append(f"{os.path.relpath(path, root)} does not exist, or is not JSON")
            fresh[session] = None                # absence is a failure, not a skip
            continue
        if raw != dumps(art):
            stale.append(f"{os.path.relpath(path, root)} differs from a fresh run")
        fresh[session] = art

    if args.write:
        print("\nartefacts written. --write never checks the prose; run --check-prose next.")
        return 0

    for gran in GRANULARITIES:
        print_distribution(fresh, granularity=gran)
    docs = load_docs(root, sorted({d for d, _, _ in SENTENCES.values()}))
    rc = _report(stale + problems(fresh, docs),
                 "Regenerate the artefacts with --write, and print the annotations to paste "
                 "with --render.")
    if rc == 0:
        print(f"\n  ok  {len(fresh)} sessions reproduce byte-for-byte, and every published "
              f"figure one round carries says so")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
