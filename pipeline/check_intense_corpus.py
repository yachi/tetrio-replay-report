"""Gate: 最癲一局's corpus lede is a literal, so something must re-derive it.

    python3 -m pipeline.check_intense_corpus --check        # re-derive, then gate every document
    python3 -m pipeline.check_intense_corpus --check-prose  # documents only, against COMMITTED CORPUS
    python3 -m pipeline.check_intense_corpus --render       # print the CORPUS block to paste
    python3 -m pipeline.check_intense_corpus --selftest     # plant corruptions, require catches

**The case.** `pipeline/intense_round.CORPUS` holds `n = 380`, a tercile triple and seven
Spearman rho with their raw and adjusted p, as strings. They have to be literals: the section
renders once per session, and a generator that read every other session's `facts.json` at render
time would re-render all six reports the day a seventh landed, which is the opposite of what this
repo's byte-identity gates are for. The cost of a literal is staleness, and it was paid within
the hour — the lede landed at `0cc719c` (2026-08-16 01:42) and `0804a7e` re-sourced apm/pps/vs
from the live tick to `results.aggregatestats` at 02:54, moving five of the seven. Nobody could
have noticed, because no script computed any of them.

`analysis/corpus_stats.py` computes them now. This is the gate that makes the computing matter.

**Three links, and each one has broken independently.**

    derivation  ->  CORPUS       a re-source moves the data and the literal does not follow
    CORPUS      ->  docstrings   the module prose quotes the figures and nothing reads prose
    CORPUS      ->  report.html  a rendered report predates the literal it was rendered from

The third is not covered by `build_report --check`, which compares each report's region against
what the CURRENT code renders and is therefore silent about whether the current code is right.
It is also the link that is RED as this file lands: all six committed reports carry the
pre-re-source figures (rho ＋0.210 / −0.187 / ＋0.096 / ＋0.236) and the Holm wording. That is
the gate working, not the gate broken — the remedy is `build_report`, run by a person.

**Re-derived, never fingerprinted.** The cheap version of this gate stores a hash of the session
list, or of the `facts.json` bytes, and re-derives only when it changes. That version would have
passed straight through the failure it exists for: the re-source changed the *values* inside a
fixed set of files under a fixed set of sessions, so a fingerprint that noticed would have to be
a fingerprint of the whole data — at which point it is cheaper to measure. `measure()` over six
sessions is well under a second. There is no fingerprint here, on purpose.

**One formatter, proved rather than asserted.** `analysis/corpus_stats.fmt_rho` / `fmt_auc` /
`fmt_p` produce every string in `CORPUS`, and `intense_round.cjk` turns the ASCII signs into the
typographic ones the Cantonese renders — the gate imports that function rather than carrying a
copy. `_selftest`'s control then pins every needle `quoted()` produces against
`intense_round.build()`'s ACTUAL output for a real session, because a format only the gate agrees
with would pass every mutant below while gating nothing anybody reads. That is check_loo.py:288.

**Which figures each document owes.** Every rho must be quoted somewhere — it is the figure the
finding rests on, and the docstrings' staleness paragraph lists all seven. The p are quoted
selectively, because the section's own argument is that p is supporting evidence and the
progression is the claim; demanding all twenty-one would turn two paragraphs into a table, which
is what `--render` is for. Unquoted p are still gated against the data by link 1 — they simply
have no second site to drift from.

**What this gate cannot see.** Whether the family is the right family, and whether a rank
correlation is the right statistic. Both are arguments, and they are made in
`analysis/corpus_stats.py`'s docstring where a reader can disagree with them. This file only
enforces that what is published is what was computed.
"""
import argparse
import ast
import copy
import json
import os
import sys

from analysis import corpus_stats
from pipeline import intense_round, region
from pipeline.docs_gate import load_docs, reword, session_dirs

REWORD = reword("pipeline/check_intense_corpus.py")

# The region the section owns, and the producer build_report names in the marker.
REGION = region.markers("intense-round", "pipeline/build_report.py")

# The module docstrings that quote the figures, and WHICH KINDS each one owes. Prose is not a
# gate anywhere else in this repo — CLAUDE.md says so in as many words — and these two are the
# exception because the figures in them are the SAME strings, derived from the same dict, so
# gating them costs one substring search each.
#
# The two owe different sets, and that is the point rather than an oversight.
# `pipeline/intense_round.py` PUBLISHES the finding, so it owes the tercile triple its lede is
# built on. `analysis/corpus_stats.py` DERIVES the triple; requiring its docstring to quote it
# would make the deriving module hard-code its own output, which is precisely the coupling this
# gate exists to break. What that module does quote is the staleness list — every rho, before
# and after the re-source — plus `n` and `m`, so those it owes.
#
# A third document may be added here. It may not be added by rewording one of these.
DOCSTRING_OWES = {
    "pipeline/intense_round.py": ("n", "m", "terciles", "rho"),
    "analysis/corpus_stats.py": ("n", "m", "rho"),
}

# test -> the words that precede its rho, its adjusted p and its raw p in the rendered
# Cantonese; None where the section does not print that figure at all (see the module docstring
# on which figures each document owes).
#
# The prefixes are part of the needle because a bare `＋0.212` is four characters that could
# fall out of a table cell, and a gate satisfied by a coincidence stops failing before the prose
# stops being wrong. They are also why this is a TABLE and not one prefix applied to everything:
# the section names APM and 攻擊 as a pair —「rho −0.178 同 −0.184」— so 攻擊's figures are
# introduced by 同, and 局長's rho sits behind 「rho 得」. Every entry here is pinned by
# `_selftest`'s control, which renders a live session and requires each needle to be in it; the
# first draft of this table guessed a bare `rho ` for all six and the control caught two.
RENDERED = {
    "cleared_pp/intensity": ("rho ", "校正後 ", "raw p "),
    "cleared/intensity": (None, None, None),        # docstring only — the raw 清走 figure
    "cleared_pp/duration": ("rho 得 ", "校正後 ", "raw p "),
    "apm/duration": ("rho ", "校正後 ", None),
    "attack/duration": ("同 ", "同 ", None),
    "cleared_per_received/intensity": ("rho ", None, None),
    "received/intensity": ("rho ", "校正後 ", "raw p "),
}


# --------------------------------------------------------------------------- the spec


def derived(root):
    """`{key: string}` — every figure `CORPUS` publishes, re-derived and re-formatted.

    Keys are `CORPUS`'s own: `n`, `m`, `tercile<i>`, and `<test>/<rho|raw|adj>`. Same key space
    as `published()` below, so the comparison is a dict diff and a key on one side only is a
    reported problem rather than a silently skipped one.
    """
    data = corpus_stats.measure(root)
    out = {"n": str(data["n_rounds"]), "m": str(data["family_size"])}

    tercile_test = intense_round.CORPUS["tercile_test"]
    if tercile_test in data["tests"]:
        for i, v in enumerate(data["tests"][tercile_test]["terciles"]):
            out[f"tercile{i}"] = corpus_stats.fmt_auc(v) if v is not None else "—"

    for test in intense_round.CORPUS["tests"]:
        t = data["tests"].get(test)
        if t is None:
            continue                       # reported by `problems`, never papered over here
        for field, value, fmt in (("rho", t["rho"], corpus_stats.fmt_rho),
                                  ("raw", t["p_raw"], corpus_stats.fmt_p),
                                  ("adj", t["p_bonferroni"], corpus_stats.fmt_p)):
            out[f"{test}/{field}"] = fmt(value) if value is not None else "—"
    return out


def published(corpus):
    """The same key space, read out of `intense_round.CORPUS`."""
    out = {"n": str(corpus["n"]), "m": str(corpus["m"])}
    for i, v in enumerate(corpus["terciles"]):
        out[f"tercile{i}"] = v
    for test, fields in corpus["tests"].items():
        for field in ("rho", "raw", "adj"):
            out[f"{test}/{field}"] = fields[field]
    return out


# --------------------------------------------------------------------------- what the documents say


def _ascii_signs(s):
    """`＋` / `−` to `+` / `-`.

    Applied to needle and haystack alike, because the docstrings were typed with an ASCII plus
    and a typographic minus and both readings are legitimate prose. Deliberately NOT a general
    punctuation strip: the digits, the decimal point and the `rho` prefix survive untouched, so
    `+0.212` still fails to match `+0.213`. `_selftest` plants exactly that.
    """
    return s.replace("＋", "+").replace("−", "-")


def quoted(corpus):
    """`{key: [strings that must appear in the rendered section]}`, per `RENDERED`."""
    out = {
        "n": [f'{corpus["n"]} 局'],
        "m": [f'family {corpus["m"]} 個測試'],
        "tercile0": [f'由 {corpus["terciles"][0]}%'],
        "tercile1": [f'升到 {corpus["terciles"][1]}%'],
        "tercile2": [f'再升到 {corpus["terciles"][2]}%'],
    }
    for test, (rho_at, adj_at, raw_at) in RENDERED.items():
        if test not in corpus["tests"]:
            continue                       # rule 3 reports the mismatch; do not invent a needle
        fields = corpus["tests"][test]
        if rho_at:
            out[f"{test}/rho"] = [rho_at + intense_round.cjk(fields["rho"])]
        if adj_at:
            out[f"{test}/adj"] = [adj_at + fields["adj"]]
        if raw_at:
            out[f"{test}/raw"] = [raw_at + fields["raw"]]
    return out


def docstring_quoted(corpus, owes):
    """`{key: [strings that must appear in this docstring]}` for one module's `owes` set.

    `cleared/intensity` reaches a document only here — it is the raw 清走 figure the per-piece
    headline is stated against, and the section renders only the per-piece one — which is why
    the rho kind must reach both documents and not the reports alone.
    """
    out = {}
    if "n" in owes:
        out["n"] = [str(corpus["n"])]
    if "m" in owes:
        out["m"] = [str(corpus["m"])]
    if "terciles" in owes:
        for i, v in enumerate(corpus["terciles"]):
            out[f"tercile{i}"] = [v]
    if "rho" in owes:
        for test, fields in corpus["tests"].items():
            out[f"{test}/rho"] = [_ascii_signs(fields["rho"])]
    return out


# --------------------------------------------------------------------------- the documents


def report_sections(root):
    """`({session: the intense-round region's markup or None}, excluded)`.

    Sessions come off the glob, never a list. A `report.html` carrying no region maps to None
    rather than being dropped: the section is conditional (it needs a qualifying round and the
    `intense_round_*` claims), so its absence is legitimate — but six absences must not read
    like six passes, so the count is printed.
    """
    out = {}
    measurable, excluded = session_dirs(root, require=("facts.json", "report.html"))
    start, end = REGION
    for session, d in measurable:
        with open(os.path.join(d, "report.html"), encoding="utf-8") as fh:
            text = fh.read()
        i, j = text.find(start), text.find(end)
        out[session] = text[i:j + len(end)] if 0 <= i < j else None
    return out, excluded


def strip_corpus(text):
    """`text` with any module-level `CORPUS = {...}` blanked out, line for line.

    **Without this the check is self-satisfying for the module that DEFINES the dict.**
    `pipeline/intense_round.py` holds `{"rho": "+0.212", ...}` as source, so a haystack of the
    whole file contains every figure by construction and the docstring could say anything at
    all. Mutant A found it: perturbing CORPUS to `+0.213` made that module's prose check pass,
    because the perturbed literal was itself the match.

    Blanking LINES rather than deleting them keeps the rest of the file at its own offsets, so
    nothing downstream has to care that this happened. A file that will not parse is returned
    unchanged: this is a search haystack, not a compiler, and a syntax error is somebody else's
    failure to report.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text
    lines = text.split("\n")
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CORPUS"
                                                for t in node.targets):
            for i in range(node.lineno - 1, (node.end_lineno or node.lineno)):
                lines[i] = ""
    return "\n".join(lines)


def load_docstrings(root):
    """`{module path: its prose or None}` — the whole file, less any `CORPUS` literal.

    The whole file and not `ast.get_docstring`: a figure that migrated out of the docstring
    into a comment beside `CORPUS` is still published prose, and reading the file keeps it
    gated through that move. Less the literal, for the reason `strip_corpus` gives.
    """
    return {name: None if text is None else strip_corpus(text)
            for name, text in load_docs(root, sorted(DOCSTRING_OWES)).items()}


# --------------------------------------------------------------------------- the gate


def problems(want, sections, docstrings, corpus):
    """Every problem, as strings. Pure — no filesystem, no measuring.

    `want` is `derived()`'s output, or None to gate the documents alone.
    """
    out = []
    have = published(corpus)
    spec = quoted(corpus)
    doc_specs = {name: docstring_quoted(corpus, owes) for name, owes in DOCSTRING_OWES.items()}
    doc_keys = {k for d in doc_specs.values() for k in d}

    # 1. Every test id in CORPUS must be one corpus_stats actually runs. A key naming a test
    #    outside the family is a figure adjusted by an `m` that never counted it.
    family = {f"{c}/{x}" for c, x in corpus_stats.FAMILY}
    for test in sorted(set(corpus["tests"]) - family):
        out.append(f"CORPUS names the test {test!r}, which is not in corpus_stats.FAMILY. Its "
                   f"adjusted p was computed over a family that does not include it")
    if corpus["tercile_test"] not in family:
        out.append(f"CORPUS's tercile_test {corpus['tercile_test']!r} is not in "
                   f"corpus_stats.FAMILY, so the published triple splits nothing measured")

    # 2. The literals against the derivation. Link one.
    if want is not None:
        for key in sorted(set(have) | set(want)):
            mine, theirs = have.get(key), want.get(key)
            if theirs is None:
                out.append(f"{key}: CORPUS publishes {mine!r} and corpus_stats derives no such "
                           f"figure at all")
            elif mine is None:
                out.append(f"{key}: corpus_stats derives {theirs!r} and CORPUS publishes "
                           f"nothing — a figure the section's `m` counts but never shows")
            elif mine != theirs:
                out.append(f"{key}: CORPUS publishes {mine!r}, the data says {theirs!r}. Print "
                           f"the fresh block with --render, paste it into "
                           f"pipeline/intense_round.CORPUS, then re-run build_report so the "
                           f"rendered reports follow")

    # 3. A needle for a key CORPUS does not carry can never be satisfied, so it is a broken
    #    spec rather than a failing document.
    #
    #    There was a second rule here, the other way round — "every rho in CORPUS must be
    #    quoted by some document" — and it was DECORATIVE: `docstring_quoted` derives its keys
    #    from `corpus["tests"]`, so every rho is in `doc_spec` by construction and no mutant
    #    could make the rule fire. The property it was reaching for is real and is enforced by
    #    rule 5 instead: adding a rho to CORPUS puts a needle in `doc_spec`, and the docstrings
    #    do not contain it until somebody writes it there. `_selftest` plants that addition and
    #    asserts the catch comes from rule 5, which is what proves the deletion was safe.
    for key in sorted((set(spec) | doc_keys) - set(have)):
        out.append(f"{key}: this gate's spec quotes it and CORPUS carries no such key. {REWORD}")

    # 4. The rendered reports. Link three.
    if not sections:
        out.append("no session on disk carries a report.html to check — the glob found nothing")
    for session in sorted(sections):
        markup = sections[session]
        if markup is None:
            continue                       # conditional section; counted by the caller
        for key in sorted(set(spec) & set(have)):
            for needle in spec[key]:
                if needle not in markup:
                    out.append(f"{session}: the rendered 最癲一局 does not contain {needle!r} "
                               f"({key}). Either the report predates the current CORPUS — "
                               f"re-run build_report — or the sentence was reworded past this "
                               f"gate. {REWORD}")

    # 5. The module docstrings. Link two. Each owes its own kinds — see DOCSTRING_OWES.
    for name, doc_spec in sorted(doc_specs.items()):
        text = docstrings.get(name)
        if text is None:
            out.append(f"{name}: not found, so the prose quoting these figures cannot be "
                       f"checked. {REWORD}")
            continue
        hay = _ascii_signs(text)
        for key in sorted(set(doc_spec) & set(have)):
            for needle in doc_spec[key]:
                if _ascii_signs(needle) not in hay:
                    out.append(f"{name}: its prose does not carry {needle!r} ({key}). The "
                               f"figures in these docstrings are the same strings CORPUS holds; "
                               f"one quoting a different value is the stale-prose failure this "
                               f"gate exists for")
    return out


# --------------------------------------------------------------------------- rendering


def render(root):
    """The `CORPUS` block to paste into `pipeline/intense_round.py`."""
    want = derived(root)
    corpus = intense_round.CORPUS
    lines = ["CORPUS = {",
             f'    "n": {want["n"]},',
             f'    "m": {want["m"]},',
             f'    "tercile_test": "{corpus["tercile_test"]}",',
             '    "terciles": ['
             + ", ".join(f'"{want[f"tercile{i}"]}"' for i in range(len(corpus["terciles"])))
             + "],",
             '    "tests": {']
    for test in corpus["tests"]:
        if f"{test}/rho" not in want:
            lines.append(f'        # {test}: corpus_stats derives no such test')
            continue
        lines.append(f'        "{test}": {{"rho": "{want[f"{test}/rho"]}", '
                     f'"raw": "{want[f"{test}/raw"]}", '
                     f'"adj": "{want[f"{test}/adj"]}"}},')
    lines += ["    },", "}"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- selftest


def _live_markup(root):
    """`intense_round.build()`'s output for the first session that renders one, or None."""
    measurable, _ = session_dirs(root, require=("facts.json", "report.html"))
    for _session, d in measurable:
        with open(os.path.join(d, "facts.json"), encoding="utf-8") as fh:
            facts = json.load(fh)
        markup = intense_round.build(facts, d)
        if markup:
            return markup
    return None


def _selftest(root):
    ok = True

    def check(good, what):
        nonlocal ok
        ok &= bool(good)
        print(f"  {'ok ' if good else 'BAD'} {what}")

    want = derived(root)
    corpus = intense_round.CORPUS

    # The synthetic documents are rendered FROM whichever CORPUS a case supplies, so a case that
    # perturbs a literal is caught by the derivation half alone and a case that perturbs a
    # document is caught by the document half alone. Using the COMMITTED reports as the control
    # would not work: they are stale as this file lands (that is the finding), so every case
    # below would fail for one pre-existing reason and prove nothing about its own mutant.
    def syn_section(c):
        return "…前…" + "…".join(n for ns in quoted(c).values() for n in ns) + "…後…"

    def syn_docs(c):
        return {name: "'''prose "
                + "…".join(n for ns in docstring_quoted(c, owes).values() for n in ns)
                + " more prose'''"
                for name, owes in DOCSTRING_OWES.items()}

    def run(c=None, section=None, docs=None, want_=None):
        c = corpus if c is None else c
        return problems(want if want_ is None else want_,
                        {"2026-01-01": syn_section(c) if section is None else section},
                        syn_docs(c) if docs is None else docs, c)

    check(not run(), "control: the committed CORPUS re-derives, and a section and docstrings "
                     "rendered from it satisfy every quote")

    def mutant(key, field, value):
        c = copy.deepcopy(corpus)
        if key in ("n", "m"):
            c[key] = value
        elif key == "terciles":
            c["terciles"][field] = value
        else:
            c["tests"][key][field] = value
        return c

    # 1. MUTANT A — a published figure perturbed by one decimal place, in each formatter kind.
    #    The documents are re-rendered from the mutant, so ONLY the derivation half can catch
    #    it. That is the point: a gate comparing documents to literals alone would call a
    #    wholesale re-typing perfectly consistent.
    for key, field, value, what in (
            ("cleared_pp/intensity", "rho", "+0.213", "the headline rho, one digit up"),
            ("cleared_pp/duration", "rho", "+0.057", "the length control's rho, one digit down"),
            ("cleared/intensity", "rho", "+0.202", "the docstring-only rho, one digit up"),
            ("received/intensity", "raw", "0.0581", "a raw p, one digit up"),
            ("attack/duration", "adj", "0.0080", "an adjusted p, one digit down"),
            ("terciles", 2, "83.6", "the top tercile, one digit up"),
            ("n", None, 379, "the round count"),
            ("m", None, 25, "the family size")):
        c = mutant(key, field, value)
        assert c != corpus, (key, field)     # a no-op mutant proves nothing
        check(bool(run(c)), f"MUTANT A — a published figure drifts: {what}")

    # 2. MUTANT B — a seventh session lands and moves a true value. Distinct from A and both
    #    are required: a corpus that GREW is what a session-list fingerprint would catch, and a
    #    re-source inside a fixed session list is what it would miss. This gate re-derives, so
    #    the same comparison catches both, which is the argument for not fingerprinting.
    grown = dict(want)
    grown["n"] = str(int(want["n"]) + 84)
    grown["cleared_pp/intensity/rho"] = "+0.187"
    grown["cleared_pp/intensity/raw"] = "0.0004"
    grown["cleared_pp/intensity/adj"] = "0.0093"
    check(bool(run(want_=grown)),
          "MUTANT B — a seventh session moves n and the headline rho")
    check(bool(run(want_={**want, "n": str(int(want["n"]) + 84)})),
          "MUTANT B — ...and a seventh session that moves ONLY n still fails")

    # 3. The documents fall behind a CORPUS that is itself right — link three, and link two.
    stale_section = syn_section(corpus).replace(
        intense_round.cjk(corpus["tests"]["cleared_pp/intensity"]["rho"]), "＋0.210")
    assert stale_section != syn_section(corpus)
    check(bool(run(section=stale_section)),
          "a rendered report carries the pre-re-source rho while CORPUS is right")

    docs = syn_docs(corpus)
    stale_docs = {k: v.replace(corpus["tests"]["cleared_pp/intensity"]["rho"], "+0.210")
                  for k, v in docs.items()}
    assert stale_docs != docs
    check(bool(run(docs=stale_docs)),
          "a module docstring carries the pre-re-source rho while CORPUS is right")
    check(bool(run(docs={name: "'''prose with no figures at all'''"
                         for name in DOCSTRING_OWES})),
          "the docstrings stop quoting the figures entirely")
    check(bool(run(docs={**docs, sorted(DOCSTRING_OWES)[0]: None})),
          "a document this gate names is not on disk")

    # 3b. Each document is checked SEPARATELY: one drifting while the other stays right must
    #     still fail. Without this the two could be concatenated into one haystack and a figure
    #     present in either would satisfy both — which is how a gate over two documents
    #     silently becomes a gate over their union.
    for name in sorted(DOCSTRING_OWES):
        one = {k: (v.replace("-0.184", "-0.185") if k == name else v) for k, v in docs.items()}
        assert one != docs, name
        check(bool(run(docs=one)), f"only {name}'s docstring drifts, the other is right")

    # 3c. ...and the split itself is load-bearing in BOTH directions. The two modules owe
    #     different kinds — the deriving module is not made to quote the triple it derives — so
    #     dropping the terciles must fail for one document and be accepted for the other. A
    #     `DOCSTRING_OWES` whose values were all equal would pass every case above.
    check(set(DOCSTRING_OWES["pipeline/intense_round.py"])
          != set(DOCSTRING_OWES["analysis/corpus_stats.py"]),
          "control: the two documents owe different kinds, so the split decides something")
    without_terciles = "…".join(
        n for key, ns in docstring_quoted(corpus, ("n", "m", "rho")).items() for n in ns)
    check(not run(docs={**docs, "analysis/corpus_stats.py": f"'''{without_terciles}'''"}),
          "control: the DERIVING module may omit the tercile triple it computes")
    check(bool(run(docs={**docs, "pipeline/intense_round.py": f"'''{without_terciles}'''"})),
          "the PUBLISHING module omits the tercile triple its lede is built on")

    # 3d. The self-satisfying haystack, pinned to the REAL file rather than to a synthetic one.
    #     `intense_round.py` holds CORPUS as source, so without `strip_corpus` its prose check
    #     matches its own literal and the module can say anything. The synthetic docs above
    #     cannot show this — they have no CORPUS assignment — so this case reads the file.
    real = load_docs(root, ["pipeline/intense_round.py"])["pipeline/intense_round.py"]
    if real is None:
        check(False, "control: pipeline/intense_round.py is not on disk")
    else:
        headline = corpus["tests"]["cleared_pp/intensity"]["rho"]
        check(f'"rho": "{headline}"' in real
              and f'"rho": "{headline}"' not in strip_corpus(real),
              "control: strip_corpus removes the CORPUS literal from the haystack")
        check(headline in strip_corpus(real),
              "control: ...and leaves the docstring's own copy of the same figure")
        # The mutant that hole allowed: the docstring drops a rho while CORPUS keeps it. BOTH
        # spellings go, because `_ascii_signs` makes ＋0.212 and +0.212 the same figure — a
        # mutant that blinded only the ASCII one would be defeated by any full-width copy, and
        # was: `cjk`'s docstring used the live headline rho as its example, so this case
        # reported a catch that came from an unrelated line until that example was changed.
        blinded = (strip_corpus(real).replace(headline, "+0.999")
                   .replace(intense_round.cjk(headline), "＋0.999"))
        assert blinded != strip_corpus(real)
        assert _ascii_signs(headline) not in _ascii_signs(blinded), "the mutant left a copy"
        check(bool(run(docs={**docs, "pipeline/intense_round.py": blinded})),
              "the publishing module's PROSE drops a rho its CORPUS still carries")

    # 4. The sign tolerance, in both directions. It buys the docstrings their typographic minus
    #    and nothing else; without the second control it could be widened to a blanket strip and
    #    every case above would still pass, leaving a gate that cannot tell two rho apart.
    check(_ascii_signs("＋0.212") == "+0.212" and _ascii_signs("−0.178") == "-0.178",
          "control: _ascii_signs maps the two sign glyphs")
    check("+0.212" not in _ascii_signs("＋0.213"),
          "control: the sign tolerance does not make +0.212 match +0.213")
    check(bool(run(docs={k: v.replace("+0.", "0.") for k, v in docs.items()})),
          "the docstrings drop the sign from every rho")

    # 5. A CORPUS key naming a test outside the family.
    outside = copy.deepcopy(corpus)
    outside["tests"]["vs/intensity"] = {"rho": "+0.999", "raw": "0.0001", "adj": "0.0001"}
    check(bool(problems(None, {"2026-01-01": syn_section(outside)}, syn_docs(outside), outside)),
          "CORPUS names a test corpus_stats.FAMILY does not run")

    # 6. A rho is ADDED to CORPUS and nobody writes it into the prose. The only case here that
    #    fires on an addition rather than on a change, and the one that licenses deleting the
    #    decorative backwards rule in `problems`: the catch must come from rule 5, the docstring
    #    check, so the assertion is on the MESSAGE and not merely on a non-empty result.
    added = copy.deepcopy(corpus)
    added["tests"]["lines/intensity"] = {"rho": "+0.085", "raw": "0.0995", "adj": "1.0000"}
    got = problems(None, {"2026-01-01": syn_section(corpus)}, syn_docs(corpus), added)
    check(any("its prose does not carry '+0.085'" in p for p in got),
          "a rho is added to CORPUS and the docstrings never mention it")

    # 7. THE control that makes every case above mean something: the needles are the strings the
    #    REAL renderer emits. A gate whose spec only it agrees with passes all of the above
    #    while gating nothing a reader sees. Rendered from a live session, so it fails the day
    #    the Cantonese is reworded past the spec — correct, because the spec is then wrong.
    live = _live_markup(root)
    if live is None:
        check(False, "control: no session rendered, so the spec is pinned to nothing")
    else:
        missing = [n for ns in quoted(corpus).values() for n in ns if n not in live]
        check(not missing,
              "control: every string this gate searches for is one intense_round.build() "
              "actually emits" + ("" if not missing else f" — MISSING {missing}"))

    # 8. ...and the state of the committed tree, reported rather than asserted: the reports are
    #    stale as this lands, which is a fact about the reports and not about the gate.
    sections, _excluded = report_sections(root)
    live_problems = problems(want, sections, load_docstrings(root), corpus)
    print(f"  --  the committed tree reports {len(live_problems)} problem(s); "
          f"{sum(1 for s in sections.values() if s is None)} of {len(sections)} sessions carry "
          f"no 最癲一局 region")

    print(f"{'ok ' if ok else 'FAIL'} selftest")
    return 0 if ok else 1


# --------------------------------------------------------------------------- main


def _report(out, note):
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
    ap.add_argument("--check", action="store_true",
                    help="re-derive the figures, then gate CORPUS and every document")
    ap.add_argument("--check-prose", action="store_true", dest="check_prose",
                    help="gate the documents against the COMMITTED CORPUS, without re-deriving")
    ap.add_argument("--render", action="store_true",
                    help="print the CORPUS block to paste into pipeline/intense_round.py")
    ap.add_argument("--selftest", action="store_true",
                    help="plant corruptions and require the gate to catch them, then exit")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    if args.selftest:
        return _selftest(root)
    if args.render:
        print(render(root), end="")
        return 0
    if not (args.check or args.check_prose):
        ap.error("one of --check, --check-prose, --render, --selftest is required")

    sections, excluded = report_sections(root)
    for d, why in excluded:
        # Named, never silently skipped — pipeline/codegen.py:76-78.
        print(f"  --  {os.path.relpath(d, root)}: not checked ({why})")
    skipped = sorted(s for s, v in sections.items() if v is None)
    if skipped:
        print(f"  --  no 最癲一局 region in {', '.join(skipped)} — the section is conditional")

    want = None
    if args.check:
        data = corpus_stats.measure(root)
        want = derived(root)
        print(f"  ..  re-derived {len(want)} figures over {data['n_rounds']} decided rounds "
              f"in {len(data['sessions'])} sessions, family m = {data['family_size']}")

    rc = _report(problems(want, sections, load_docstrings(root), intense_round.CORPUS),
                 "Print the fresh block with --render, paste it into "
                 "pipeline/intense_round.CORPUS, then re-run build_report so the rendered "
                 "reports follow. --check-prose skips the re-derivation; --check does both.")
    if rc == 0:
        print(f"\n  ok  CORPUS {'re-derives and ' if want else ''}is quoted intact by "
              f"{len(sections) - len(skipped)} rendered report(s) and "
              f"{len(DOCSTRING_OWES)} module docstring(s)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
