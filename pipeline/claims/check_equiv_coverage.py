"""Gate: `equiv.py`'s hand-claim coverage, committed per session and gated in the prose.

    python3 -m pipeline.claims.check_equiv_coverage --write        # regenerate the artefacts
    python3 -m pipeline.claims.check_equiv_coverage --check        # re-measure + byte-compare + prose
    python3 -m pipeline.claims.check_equiv_coverage --check --modes single_value,two_site_match
    python3 -m pipeline.claims.check_equiv_coverage --check-prose  # prose only, no re-measurement
    python3 -m pipeline.claims.check_equiv_coverage --render       # print the doc blocks to paste
    python3 -m pipeline.claims.check_equiv_coverage --selftest     # plant corruptions, require catches

`pipeline/claims/equiv.py` measures what fraction of a session's hand-written claims a
generated claim already implies, by mutating the dataset and comparing truth vectors.
Its figures are published in README.md, ROADMAP.md and CLAUDE.md — and until this file
existed **nothing re-derived them**: `equiv.py` appeared in no workflow and in no `bin/`
script, so the published table had been run by hand, once, on the first two of six
sessions. Three sessions had never been measured in public and two of those sit below the
>=85% acceptance gate the ROADMAP quotes beside them.

Four decisions this file is built on, each of which has a failure mode behind it:

1. **The artefact stores verdict SETS, never percentages.** That is the house rule
   (`tools/triangle-oracle/cross-extract.mjs:11-12` — "Counts are integers so the JSON is
   byte-stable; percentages are derived at read time, never stored") and here it is
   load-bearing for a second reason. The numerator is *monotone non-decreasing* in the
   generated ledger: adding a generated family can only ever cover more hand claims, never
   fewer, so a scalar gate of ANY shape — a floor, a byte-compared percentage, a delta
   bound — is structurally blind to the exact edit that motivated this work (2026-08-15
   added seven `intense_round` families and coverage held at 85%/84%). The verdict SETS are
   not blind: a family that newly covers C007 moves C007 from `uncovered` to `covered` even
   when the count and the percentage both stand still, and that is the line a diff shows.

2. **No threshold.** One hand claim is worth 10.0 percentage points on 2026-07-28, so a
   floor all six sessions pass would have to sit at 60% — which blesses that session's
   known artefact by definition. `equiv.py` ships an unused `--min-coverage`; it stays
   unused, and this gate gives it no caller. The gate is reproducibility, not a bar.

3. **No session list.** Sessions are globbed off disk, and a directory that cannot be
   measured is **named**, never silently dropped — the rule at `pipeline/codegen.py:76-78`
   ("Callers that can only consume specs use this and name what they left out — a silent
   skip here would understate the artefact's coverage"). `sessions/2026-07-24/proof` is the
   one such directory today: a lighter cross-check report with its own 20-claim ledger and
   no generated ledger to measure against.

4. **Absence is a failure, never a skip.** A session on disk with no artefact fails. A
   mode in the committed artefact that a fresh run does not produce fails. A published
   paragraph the parser cannot match fails. There is no `if os.path.exists(...)` guard
   anywhere below that turns a missing input into a pass — that is the
   conditional-gates-pass-on-stale-input class this repo has already been bitten by twice.

**Why `--check` gates the PROSE and not only the JSON.** Byte-identity of an artefact says
nothing about the numbers quoted in documents, because the percentages are derived at read
time. That gap is not hypothetical: `tools/triangle-oracle/dual-backed.json` sat green
through two regenerations that moved every figure the README published from it. So the
three documents are parsed and every figure is compared against the artefacts through ONE
formatter (`pct` below), and — copying `cross-extract.mjs:93-106` verbatim in spirit — **a
paragraph the parser cannot match is a FAILURE, never a skip.** If you reword a table, you
update the spec in this file so the figures stay gated.

Three further failure conditions, each earned:

* a table with fewer rows than there are sessions on disk. This was live when the file was
  written: three rows against a six-session corpus, with the missing three unmeasured;
* a single-value figure published with no two-site companion for a session that HAS
  windowed claims. The single-value number is an upper bound there by construction — a
  windowed claim draws on the same rounds as the session total meant to imply it, so no
  single-value mutation can falsify one without the other. Deleting the companion column
  and keeping "100%" turns an artefact into a measurement, the same shape as deleting the
  Doubles sentence in `check_opener_section.py`;
* a figure quoted from a `match`-granularity run when the artefact carries a `round` one.
  `match` is itself an upper bound (it enumerates only the source match's largest round and
  the target match's smallest), so a resolved bound still described as a bound is exactly
  the staleness this gate exists to close.

**Three tiers, because one re-measurement cost does not fit both schedules.** `--two-site
round` is 854,937 moves over the six-session corpus — ~25 minutes for ALL SIX sessions, not
per session — while `single_value` + `two_site_match` is ~4m13s for the corpus. So:

* `--check --modes single_value,two_site_match` — **every push**. It genuinely re-measures,
  which is the whole point of the item: a change to `generators.py`, `spec.py` or
  `perturb.py` that moves real coverage must not go green. It byte-compares only the named
  modes' blocks and **names the ones it did not check**, per `pipeline/codegen.py:76-78`,
  because a narrowed run that prints like a full one is this gate's own failure class.
* `--check` (all three modes) — **weekly**, and before publishing a figure.
* `--check-prose` — no measurement at all. Useful locally after editing prose; it is NOT a
  substitute for a push tier that re-measures, and its own success line says so.
"""
import argparse
import json
import os
import re
import sys

# The document-parsing layer is SHARED with pipeline/check_loo.py, which gates the same three
# files. Two parsers over one document agree until the document is reworded; see
# pipeline/docs_gate.py's header for why they live in one place.
from ..docs_gate import Prose, Table, granularity
from ..docs_gate import candidate_dirs as _candidate_dirs
from ..docs_gate import load_docs as _load_docs
from ..docs_gate import reword as _reword
from ..docs_gate import row_membership as _row_membership
from ..docs_gate import session_dirs as _session_dirs

ARTEFACT = "equiv-coverage.json"
GENERATED = "claims-generated.json"
SCHEMA = "equiv-coverage/1"

WHAT = (
    "Hand-claim coverage by exhaustive mutation, per pipeline/claims/equiv.py: a hand-written "
    "claim counts as COVERED when some generated claim (or a pair of them) cannot be true unless "
    "it is, over every mutation of the dataset in the corpus, and both are falsifiable somewhere. "
    "This is NOT a proof of equivalence — it is a statement about one dataset under one family of "
    "perturbations, so a claim listed as covered is a claim the generators would have caught, not "
    "a theorem. Verdict SETS are stored and percentages are derived at read time, because the "
    "numerator is monotone non-decreasing in the generated ledger: adding a generated family can "
    "never lower a percentage, so only the attribution shows what an edit did."
)

# (mode key, the --two-site granularity it runs at)
MODES = (("single_value", None), ("two_site_match", "match"), ("two_site_round", "round"))

# Which corpus counts a run over a given mode actually re-derives. `moves_round` is not
# evidence a `single_value,two_site_match` run produced, so comparing it under --modes would
# be checking the committed file against itself.
CORPUS_OF_MODE = {"single_value": (), "two_site_match": ("moves_match",),
                  "two_site_round": ("moves_round",)}
ALWAYS_CORPUS = ("single_value_sites", "single_value_mutants")

# A mode is an UPPER BOUND when its mutation family cannot reach some claims at all, so its
# coverage figure is at least the truth and possibly above it. Stated per mode in the artefact
# rather than in prose, because the reason differs and both are load-bearing.
UPPER_BOUND_REASON = {
    "single_value": (
        "a windowed claim shares its rounds with the session total meant to imply it, so no "
        "single-value mutation falsifies one without the other; see 2026-07-28, whose 100% here "
        "is 60% once value-preserving moves are added"
    ),
    "two_site_match": (
        "match granularity enumerates only moves out of the source match's largest round and into "
        "the target match's smallest, so a claim that turns on WHICH round is touched is out of "
        "scope; the round granularity enumerates every cross-match round pair"
    ),
    "two_site_round": None,
}

# The two window operators in pipeline/claims/spec.py. A per-match claim is a window of one
# match (`sum_round_range(pl, f, mi, mi + 1)`), so this catches those too.
WINDOW_OPS = {"sum_round_range", "count_rounds_range"}

REWORD = _reword("pipeline/claims/check_equiv_coverage.py")


# --------------------------------------------------------------------------- sessions


def candidate_dirs(root):
    """Every `sessions/<date>/<sub>` directory carrying a claim ledger, sorted."""
    return _candidate_dirs(root)


def session_dirs(root):
    """(measurable, excluded) — excluded is [(dir, why)], and every caller prints it.

    This gate needs BOTH facts.json and the generated ledger: with no ledger there is nothing
    to measure coverage against. `pipeline/check_loo.py` requires only facts.json, which is
    why the requirement is the caller's and not docs_gate's.
    """
    return _session_dirs(root, require=("facts.json", GENERATED))


def hand_ledgers(report_dir):
    """The session's hand ledgers: its canonical ledger order minus the generated one."""
    from ..codegen import session_ledgers
    return [p for p in session_ledgers(report_dir) if os.path.basename(p) != GENERATED]


def _uses_window(node):
    if isinstance(node, dict):
        return node.get("e") in WINDOW_OPS or any(_uses_window(v) for v in node.values())
    if isinstance(node, list):
        return any(_uses_window(v) for v in node)
    return False


def windowed_claims(hand_paths):
    """Ids of hand claims built on a window operator, or None when none of them carry a spec.

    `None` means "not established", never "none" — the distinction exists because a ledger
    with no spec offers nothing to read a window out of, and answering `[]` there would be a
    claim about the data that only a token scan of a predicate string supported.

    **No such ledger exists any more.** 07-22 and 07-24 were the last two, and porting them to
    the spec algebra turned their `null` into a measurement: `[]` for 07-22 and `["R015",
    "R018"]` for 07-24, which had been carrying two `count_rounds_range` claims that the
    single-value coverage figure cannot falsify. The branch is kept because it states what the
    field means, and the selftest exercises it on a synthetic session; nothing on disk reaches
    it.
    """
    ids, saw_spec = [], False
    for path in hand_paths:
        with open(path, encoding="utf-8") as fh:
            for claim in json.load(fh):
                if "spec" not in claim:
                    continue
                saw_spec = True
                if _uses_window(claim["spec"]):
                    ids.append(claim["id"])
    return sorted(ids) if saw_spec else None


# --------------------------------------------------------------------------- the artefact


def _default_measure_modes():
    from . import equiv                     # noqa: PLC0415 - only --write/--check need it
    fn = getattr(equiv, "measure_modes", None)
    if fn is None:
        # Not a fallback to `measure()` three times. One sweep is the contract: three calls
        # redo the single-value corpus twice over for nothing, and two call sites measuring
        # the same thing differently is how the two figures start disagreeing.
        raise SystemExit(
            "pipeline/claims/equiv.py carries no measure_modes(facts_path, hand_paths, "
            "generated_path=None, two_site_modes=()) -> {mode: result}. This gate is written "
            "against that seam so one single-value sweep serves every granularity.")
    return fn


def build(session, report_dir, modes=None, measure_modes=None):
    """Measure `modes` over one session and shape the artefact. Sorted lists, no percentages.

    ONE sweep, not one per granularity: the two-site families are additions to the
    single-value corpus, so measuring them separately re-runs that corpus once per mode.

    `modes` defaults to all of them and is narrowed only by `--check --modes`. A narrowed
    build is a PARTIAL artefact and must never be written — `main` enforces that by refusing
    `--modes` with `--write`, because a narrowed write deletes the blocks it did not measure.
    """
    want = list(modes or [k for k, _ in MODES])
    measure_modes = measure_modes or _default_measure_modes()
    facts = os.path.join(report_dir, "facts.json")
    hand = hand_ledgers(report_dir)
    gen = os.path.join(report_dir, GENERATED)

    results = measure_modes(facts, hand, generated_path=gen,
                            two_site_modes=tuple(g for k, g in MODES if g and k in want))
    absent = [k for k in want if k not in results]
    if absent:
        raise SystemExit(f"{session}: measure_modes returned no result for "
                         f"{', '.join(absent)} — the artefact would publish fewer modes than "
                         f"the gate compares, which reads as a session that measured cleanly")

    modes, sites, mutants, moves = {}, None, None, {}
    for key, gran in MODES:
        if key not in want:
            continue
        r = results[key]
        if sites is None:
            sites, mutants = r["sites"], r["mutants"]
        elif r["sites"] != sites:
            # The single-value corpus is a property of the dataset, so every mode must report
            # the same one. A disagreement means the modes ran over different data and no
            # figure below can be compared with any other.
            raise SystemExit(f"{session}: mode {key} reports {r['sites']} mutation sites, "
                             f"an earlier mode reported {sites}")
        moves[key] = r["moves"]
        entry = {"granularity": gran,
                 "is_upper_bound": UPPER_BOUND_REASON[key] is not None,
                 "covered": sorted(r["covered"]),
                 "uncovered": sorted(r["uncovered"]),
                 "untested": sorted(r["untested"]),
                 "identical": sorted(r["identical"]),
                 "trivial_generated": sorted(r["trivial_generated"])}
        if UPPER_BOUND_REASON[key] is not None:
            entry["upper_bound_reason"] = UPPER_BOUND_REASON[key]
        modes[key] = entry

    return {"schema": SCHEMA,
            "what": WHAT,
            "session": session,
            # `sites` is how many places the dataset can be written; `mutants` is how many
            # datasets were actually evaluated, which is larger because one site is escalated
            # in several directions. Both, because quoting only the smaller understates the
            # corpus and quoting only the larger hides that the sweep is exhaustive over sites.
            "corpus": {"single_value_sites": sites, "single_value_mutants": mutants,
                       **{k: moves[m] for m in want for k in CORPUS_OF_MODE[m]}},
            "windowed_claims": windowed_claims(hand),
            "modes": modes}


def dumps(artefact):
    return json.dumps(artefact, indent=2, sort_keys=True) + "\n"


def artefact_path(report_dir):
    return os.path.join(report_dir, ARTEFACT)


def project(artefact, modes):
    """The bytes a run over `modes` re-derives, and only those.

    `--modes` has to narrow the comparison HONESTLY: comparing the whole file would report a
    difference in a block the run never measured, and comparing nothing would make the flag a
    way to pass. So the projection carries the identity fields, the corpus counts that set of
    modes produces, and those modes' blocks — nothing else is read.
    """
    keys = set()
    for m in modes:
        keys.update(CORPUS_OF_MODE[m])
    corpus = artefact.get("corpus") or {}
    out = {k: v for k, v in artefact.items() if k not in ("modes", "corpus")}
    out["corpus"] = {k: v for k, v in corpus.items() if k in ALWAYS_CORPUS or k in keys}
    out["modes"] = {k: artefact["modes"][k] for k in modes if k in artefact.get("modes", {})}
    return dumps(out)


def _merge(committed, fresh, modes):
    """The whole artefact the document gate should see: fresh blocks where measured.

    Under a narrowed `--check` the unnamed modes' figures still appear in the documents and
    still have to be checked against something; the honest something is the committed file,
    and `unchecked_note` is what tells the reader that is what happened.
    """
    out = json.loads(json.dumps(committed))
    for key, value in fresh.items():
        if key not in ("modes", "corpus"):
            out[key] = value
    out.setdefault("corpus", {}).update(fresh.get("corpus") or {})
    out.setdefault("modes", {}).update({k: v for k, v in fresh["modes"].items() if k in modes})
    return out


def unchecked_note(modes):
    """The `  --  ` line naming the modes a narrowed run did NOT byte-compare, or ''.

    pipeline/codegen.py:76-78 — name what you left out. A narrowed run whose output is
    indistinguishable from a full one is the same silent-narrowing bug this file exists to
    catch in the documents, committed one level down in the tool itself.
    """
    left = [k for k, _ in MODES if k not in modes]
    if not left:
        return ""
    return (f"  --  {', '.join(left)} not measured and not byte-compared in this run; "
            f"their blocks in each {ARTEFACT} are carried over unread, and the figures "
            f"published for them were checked against the COMMITTED artefact")


def load_artefacts(root):
    """{session: artefact or None}. A session on disk with no artefact maps to None."""
    arts = {}
    for session, d in session_dirs(root)[0]:
        path = artefact_path(d)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                arts[session] = json.load(fh)
        else:
            arts[session] = None
    return arts


# --------------------------------------------------------------------------- the formatter


def pct(covered, testable):
    """THE formatter. Every published percentage in every document goes through this one.

    `.0%` is what equiv.py itself prints, so a figure copied out of a run and a figure
    checked by this gate are produced by the same rounding.
    """
    return "—" if not testable else f"{covered / testable:.0%}"


def figures(artefact, mode):
    """(covered, testable, pct, identical) for one mode — the four numbers a document may print."""
    if mode not in artefact.get("modes", {}):
        raise SystemExit(f"{artefact.get('session')}: {ARTEFACT} carries no {mode} mode, so "
                         f"there is no figure to publish for it — regenerate with --write")
    m = artefact["modes"][mode]
    testable = len(m["covered"]) + len(m["uncovered"])
    return len(m["covered"]), testable, pct(len(m["covered"]), testable), len(m["identical"])


# --------------------------------------------------------------------------- document specs


def _column_mode(header_cell):
    h = header_cell.lower()
    m = re.search(r"--two-site\W*(match|round)", h)
    if m:
        return "two_site_" + m.group(1)
    if "identical" in h:
        return "identical"
    if "single-value" in h or h.strip() == "coverage":
        return "single_value"
    return None


# `N of M` and `N/M` are both in use; the percentage may or may not be bolded.
COUNTS = re.compile(r"(\d+)\s*(?:of|/)\s*(\d+)")
PERCENT = re.compile(r"\*{0,2}(\d+)%\*{0,2}")


def _table_cell(name, session, art, mode, cell):
    if mode == "identical":
        # The identical-behaviour column has no granularity of its own, and the committed
        # ROADMAP figures (24 and 28) are the single-value ones, so that is the mode it is
        # read against. A table wanting the two-site count needs a labelled column.
        want = str(figures(art, "single_value")[3])
        got = re.search(r"\d+", cell)
        if not got:
            return [f"{name}: {session}'s identical-behaviour cell has no number. {REWORD}"]
        return ([] if got.group(0) == want else
                [f"{name}: {session} publishes {got.group(0)} identical-behaviour claims; "
                 f"the artefact has {want}"])
    if mode not in art["modes"]:
        return [f"{name}: {session} publishes a {mode} figure the artefact does not carry"]
    cov, testable, p, _ = figures(art, mode)
    c, q = COUNTS.search(cell), PERCENT.search(cell)
    if not c or not q:
        return [f"{name}: {session}'s {mode} cell {cell!r} has no `N of M ... P%` figure. {REWORD}"]
    bad = []
    if (int(c.group(1)), int(c.group(2))) != (cov, testable):
        bad.append(f"{name}: {session} publishes {c.group(1)}/{c.group(2)} for {mode}; "
                   f"the artefact gives {cov}/{testable}")
    if q.group(1) + "%" != p:
        bad.append(f"{name}: {session} publishes {q.group(1)}% for {mode}; "
                   f"the artefact gives {p}")
    return bad


def _prose_verdict(spec, para, found, arts):
    """The policy over CLAUDE.md's parsed per-session sentence. The parse itself is
    docs_gate.Prose's; everything below is about coverage percentages."""
    listed = [suf for suf, _, _ in found]
    gran = re.search(r"--two-site\W*(match|round)", para)
    if not gran:
        # An unlabelled `--two-site` figure cannot be checked against either mode, and the
        # two do not agree: `match` is an upper bound on `round`. Not a skip — and the
        # membership problems are still reported, so one reword does not hide the rest.
        return _membership(
            spec.name, [s for s in arts if s[5:] in listed], arts
        ) + [f"{spec.name}: the sentence quotes a two-site figure without naming its "
             f"granularity — `match` is itself an upper bound. {REWORD}"]
    two_mode = "two_site_" + gran.group(1)
    suffixes = {}
    for session in arts:
        suffixes.setdefault(session[5:], []).append(session)
    named = []
    out = _granularity(spec.name, ["single_value", two_mode], arts)
    for short, single, two in found:
        full = suffixes.get(short) or []
        if len(full) != 1:
            out.append(f"{spec.name}: {short!r} names "
                       f"{'no session on disk' if not full else 'more than one session'}")
            continue
        session, art = full[0], arts.get(full[0])
        named.append(session)
        if art is None:
            continue                       # already reported by _membership
        for mode, got in (("single_value", single), (two_mode, two)):
            if mode not in art["modes"]:
                out.append(f"{spec.name}: {session} quotes a {mode} figure the artefact "
                           f"does not carry")
                continue
            want = figures(art, mode)[2]
            if got + "%" != want:
                out.append(f"{spec.name}: {session} quotes {got}% for {mode}; "
                           f"the artefact gives {want}")
    return _membership(spec.name, named, arts) + out


def _membership(name, listed, arts):
    return _row_membership(name, listed, arts, ARTEFACT)


def _granularity(name, published, arts):
    """A `match` figure published with no `round` companion, when a round run exists."""
    return granularity(
        name, published, arts, "two_site_match", "two_site_round",
        lambda n, have: (
            f"{n}: publishes the `--two-site match` figure only, but the artefacts for "
            f"{', '.join(have)} carry a `round` run. `match` enumerates one round pair per "
            f"match pair and is an upper bound; a resolved bound still described as a bound "
            f"is the staleness this gate exists to close."))


def _companion(name, session, art, published):
    """A single-value figure with no two-site companion, for a session with windowed claims."""
    if "single_value" not in published:
        return []
    if any(p.startswith("two_site") for p in published):
        return []
    if not art.get("windowed_claims"):
        return []
    return [f"{name}: {session} publishes a single-value figure with no two-site companion, "
            f"and {len(art['windowed_claims'])} of its hand claims are windowed "
            f"({', '.join(art['windowed_claims'])}). No single-value mutation can falsify a "
            f"windowed claim without falsifying the session total meant to imply it, so that "
            f"figure alone is an upper bound published as a measurement."]


def _table(name, header):
    return Table(name, header, _table_cell, _column_mode, REWORD, ARTEFACT,
                 per_table=(_granularity,), per_row=(_companion,))


DOCS = (
    _table("README.md", re.compile(r"^\|\s*Session\s*\|[^\n]*single-value[^\n]*\|\s*$", re.M)),
    _table("ROADMAP.md", re.compile(r"^\|\s*Session\s*\|\s*Coverage\s*\|[^\n]*$", re.M)),
    Prose("CLAUDE.md",
          re.compile(r"^[^\n]*Per-session:[^\n]*$", re.M),
          re.compile(r"(\d{2}-\d{2})\s+\*{0,2}(\d+)%\*{0,2}\s*(?:→|->)\s*\*{0,2}(\d+)%\*{0,2}"),
          _prose_verdict, REWORD, ARTEFACT),
)

DOC_NAMES = tuple(d.name for d in DOCS)


def load_docs(root):
    return _load_docs(root, DOC_NAMES)


# --------------------------------------------------------------------------- the gate


def _artefact_problems(session, art):
    out = []
    if art.get("schema") != SCHEMA:
        out.append(f"{session}: {ARTEFACT} declares schema {art.get('schema')!r}, want {SCHEMA!r}")
    if art.get("session") != session:
        out.append(f"{session}: {ARTEFACT} names session {art.get('session')!r}")
    if not art.get("what"):
        out.append(f"{session}: {ARTEFACT} carries no `what` — the artefact would travel "
                   f"without the sentence saying it is not a proof of equivalence")
    modes = art.get("modes", {})
    for key, gran in MODES:
        if key not in modes:
            out.append(f"{session}: {ARTEFACT} carries no {key} mode")
            continue
        m = modes[key]
        if m.get("granularity") != gran:
            out.append(f"{session}: {key} declares granularity {m.get('granularity')!r}, "
                       f"want {gran!r}")
        want_bound = UPPER_BOUND_REASON[key] is not None
        if bool(m.get("is_upper_bound")) != want_bound:
            out.append(f"{session}: {key} declares is_upper_bound={m.get('is_upper_bound')!r}, "
                       f"want {want_bound}")
        if want_bound and not m.get("upper_bound_reason"):
            out.append(f"{session}: {key} is an upper bound with no upper_bound_reason — a "
                       f"reader has no way to know what the figure cannot see")
        for field in ("covered", "uncovered", "untested", "identical", "trivial_generated"):
            v = m.get(field)
            if not isinstance(v, list):
                out.append(f"{session}: {key}.{field} is not a list")
            elif v != sorted(v):
                out.append(f"{session}: {key}.{field} is not sorted, so the JSON is not "
                           f"byte-stable across runs")
        cov, unc, unt = (set(m.get(f) or []) for f in ("covered", "uncovered", "untested"))
        for a, b, an, bn in ((cov, unc, "covered", "uncovered"), (cov, unt, "covered", "untested"),
                            (unc, unt, "uncovered", "untested")):
            if a & b:
                out.append(f"{session}: {key} lists {sorted(a & b)} in both {an} and {bn}")
        extra = set(m.get("identical") or []) - cov
        if extra:
            out.append(f"{session}: {key} calls {sorted(extra)} identical but not covered")
    return out


def problems(arts, docs):
    """Every problem in (artefacts, documents), as strings. Pure — no filesystem, no measuring."""
    out = []
    for session in sorted(s for s, a in arts.items() if a is None):
        out.append(f"{session}: is a session on disk with no {ARTEFACT}. Absence is a failure "
                   f"here, not a skip — a gate that passes on a missing artefact passes forever")
    if not arts:
        out.append("no measurable sessions found at all — the glob found nothing to check")
    for session in sorted(s for s, a in arts.items() if a):
        out += _artefact_problems(session, arts[session])
    for spec in DOCS:
        text = docs.get(spec.name)
        if text is None:
            out.append(f"{spec.name}: not found. {REWORD}")
            continue
        out += spec.check(text, arts)
    return out


# --------------------------------------------------------------------------- rendering


def render(arts, name):
    """The document block for `name`, from the artefacts, through the same `pct`.

    Renderer and parser share this file so a reworded document is a one-place edit — and the
    selftest feeds each COMMITTED document through the parser, so the two cannot co-drift
    into a format only they agree on.
    """
    live = {s: a for s, a in sorted(arts.items()) if a}
    if name == "README.md":
        head = ("| Session | single-value only | `--two-site match` | `--two-site round` |\n"
                "|---|---|---|---|\n")
        row = ("| {s} | {a1} of {a2} testable — **{a3}** | {b1} of {b2} — **{b3}** "
               "| {c1} of {c2} — **{c3}** |\n")
    elif name == "ROADMAP.md":
        head = ("| Session | Coverage | `--two-site match` | `--two-site round` "
                "| Identical behaviour |\n|---|---|---|---|---|\n")
        row = ("| {s} | {a1}/{a2} testable = **{a3}** | {b1}/{b2} = **{b3}** "
               "| {c1}/{c2} = **{c3}** | {a4} |\n")
    elif name == "CLAUDE.md":
        items = []
        for s, a in live.items():
            items.append(f"{s[5:]} {figures(a, 'single_value')[2]} → "
                         f"**{figures(a, 'two_site_round')[2]}**")
        return ("Measured with `--two-site round`. Per-session: " + ", ".join(items) + ".\n")
    else:
        raise ValueError(name)
    out = head
    for s, a in live.items():
        f = {"s": s}
        for tag, mode in (("a", "single_value"), ("b", "two_site_match"), ("c", "two_site_round")):
            cov, testable, p, ident = figures(a, mode)
            f.update({tag + "1": cov, tag + "2": testable, tag + "3": p, tag + "4": ident})
        out += row.format(**f)
    return out


# --------------------------------------------------------------------------- selftest


def _synthetic():
    """Three sessions shaped like the real ones: one pre-spec, one windowed, one clean."""
    def mode(key, covered, uncovered, untested=(), identical=()):
        e = {"granularity": dict(MODES)[key],
             "is_upper_bound": UPPER_BOUND_REASON[key] is not None,
             "covered": sorted(covered), "uncovered": sorted(uncovered),
             "untested": sorted(untested), "identical": sorted(identical),
             "trivial_generated": []}
        if UPPER_BOUND_REASON[key] is not None:
            e["upper_bound_reason"] = UPPER_BOUND_REASON[key]
        return e

    def art(session, windowed, sv, ts_m, ts_r):
        return {"schema": SCHEMA, "what": WHAT, "session": session,
                "corpus": {"single_value_sites": 4440, "moves_match": 111, "moves_round": 9999},
                "windowed_claims": windowed,
                "modes": {"single_value": mode("single_value", *sv),
                          "two_site_match": mode("two_site_match", *ts_m),
                          "two_site_round": mode("two_site_round", *ts_r)}}

    c = [f"C{i:03d}" for i in range(1, 12)]
    return {
        # pre-spec hand ledger: windowed_claims is null, and 8 of 10 covered = 80%
        "2026-07-22": art("2026-07-22", None,
                          (c[:8], c[8:10], [c[10]], c[:3]),
                          (c[:7], c[7:10], [c[10]], c[:3]),
                          (c[:6], c[6:10], [c[10]], c[:2])),
        # windowed: the session whose single-value figure is the loudest upper bound
        "2026-07-28": art("2026-07-28", ["C002", "C004"],
                          (c[:10], [], [c[10]], c[:5]),
                          (c[:6], c[6:10], [c[10]], c[:4]),
                          (c[:5], c[5:10], [c[10]], c[:4])),
        "2026-08-14": art("2026-08-14", ["C007"],
                          (c[:9], c[9:10], [c[10]], c[:6]),
                          (c[:9], c[9:10], [c[10]], c[:6]),
                          (c[:8], c[8:10], [c[10]], c[:5])),
    }


def _selftest(root):
    arts = _synthetic()
    docs = {name: "prelude 2026-01-01 999%\n\n" + render(arts, name) + "\npostlude\n"
            for name in DOC_NAMES}

    # Annotated because one planted case maps a session to None — an artefact that is absent —
    # and inferring the element type from the first entry alone would make that an error rather
    # than the thing being tested. Function-local annotations are not evaluated at runtime.
    cases: list[tuple[str, dict, dict, bool]] = [
        ("control: rendered documents agree with the artefacts", arts, docs, False)]

    # A verdict moved covered -> uncovered. The percentages move with it, so the documents go
    # stale — which is the whole reason the artefact stores sets and the gate re-derives.
    flipped = json.loads(json.dumps(arts))
    m = flipped["2026-08-14"]["modes"]["two_site_round"]
    m["uncovered"] = sorted(m["uncovered"] + [m["covered"].pop()])
    cases.append(("a verdict flips covered -> uncovered in the artefact", flipped, docs, True))

    dropped = json.loads(json.dumps(arts))
    del dropped["2026-07-22"]["modes"]["two_site_round"]
    cases.append(("a mode is missing from the artefact", dropped, docs, True))

    missing = {s: (None if s == "2026-08-14" else a) for s, a in arts.items()}
    cases.append(("a session on disk has no artefact", missing, docs, True))

    unsorted = json.loads(json.dumps(arts))
    u = unsorted["2026-07-28"]["modes"]["single_value"]
    u["covered"] = u["covered"][::-1]
    cases.append(("a verdict list is not sorted", unsorted, docs, True))

    nobound = json.loads(json.dumps(arts))
    del nobound["2026-07-28"]["modes"]["single_value"]["upper_bound_reason"]
    cases.append(("an upper-bound mode drops its reason", nobound, docs, True))

    for name in DOC_NAMES:
        block = render(arts, name)

        # Every number the block renders, one at a time, same width. Derived from the render
        # rather than listed, so this is a completeness statement about the published figures
        # instead of the handful someone remembered.
        seen = set()
        for hit in re.finditer(r"\d+", block):
            tok = hit.group(0)
            if tok in seen:
                continue
            seen.add(tok)
            alt = tok[:-1] + str((int(tok[-1]) + 1) % 10)
            bad = block[:hit.start()] + alt + block[hit.end():]
            cases.append((f"{name}: planted figure {tok} -> {alt}", arts,
                          dict(docs, **{name: bad}), True))

        # Marker-style mutants, enumerated BY NAME. A derived list would let a rule ship with
        # no mutant proving it fires — check_opener_section.py:505-506 makes the same point.
        rows = [ln for ln in block.split("\n") if ln.startswith("|")]
        if rows:
            cut = "\n".join(rows[:-1] + [""]) if len(rows) > 2 else ""
            cases.append((f"{name}: a session's row is deleted", arts,
                          dict(docs, **{name: block.replace("\n".join(rows), cut)}), True))
        else:
            first = block.split("Per-session: ")[1].split(", ")[0]
            cases.append((f"{name}: a session is dropped from the sentence", arts,
                          dict(docs, **{name: block.replace(first + ", ", "")}), True))

        cases.append((f"{name}: the block is reworded past the parser", arts,
                      dict(docs, **{name: "coverage held steady this session.\n"}), True))

        cases.append((f"{name}: the round granularity is relabelled `match`", arts,
                      dict(docs, **{name: _to_match_only(block)}), True))

        if rows:
            extra = rows[-1].replace(sorted(arts)[-1], "2026-09-99")
            cases.append((f"{name}: a row names a session that is not on disk", arts,
                          dict(docs, **{name: block.replace(rows[-1], rows[-1] + "\n" + extra)}),
                          True))

    # The one shape that turns an artefact into a measurement: keep the single-value column,
    # drop its two-site companion, for a session whose hand claims are windowed.
    for name in ("README.md", "ROADMAP.md"):
        cases.append((f"{name}: the two-site columns are deleted, single-value stays", arts,
                      dict(docs, **{name: _single_column_only(render(arts, name))}), True))

    # ...and the control that says what that rule is NOT. The same deletion over sessions with
    # no windowed claim is not a failure: the single-value figure is only an upper bound where
    # a window operator makes it one. Without this case the rule could be "always demand a
    # two-site column", which is a different rule that happens to catch the same mutant.
    nowindow = json.loads(json.dumps(arts))
    for a in nowindow.values():
        a["windowed_claims"] = None
    nw_docs = {n: "prelude\n\n" + (_single_column_only(render(nowindow, n))
                                   if n != "CLAUDE.md" else render(nowindow, n)) + "\npostlude\n"
               for n in DOC_NAMES}
    cases.append(("control: no two-site column, and no session has a windowed claim",
                  nowindow, nw_docs, False))

    ok = True
    for name, a, d, must_fail in cases:
        failed = bool(problems(a, d))
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if failed else 'accepted'}"
              f"{'' if good else '  <- expected ' + ('rejection' if must_fail else 'acceptance')}")

    # --modes narrows the byte-comparison, and a narrowing has to be wrong in BOTH directions
    # to be worth having: too wide and the flag reports differences in blocks the run never
    # measured; too narrow and the flag is a way to pass. Both are planted.
    base = arts["2026-08-14"]
    in_round = json.loads(json.dumps(base))
    in_round["modes"]["two_site_round"]["covered"] = []
    in_round["corpus"]["moves_round"] = 1
    in_single = json.loads(json.dumps(base))
    in_single["modes"]["single_value"]["covered"] = []
    in_match = json.loads(json.dumps(base))
    in_match["corpus"]["moves_match"] = 1
    narrowed = ["single_value", "two_site_match"]
    narrow_cases = (
            ("--modes: an unchanged artefact compares equal", narrowed, base, False),
            ("--modes single_value,two_site_match: a corruption in the two_site_round block "
             "is out of scope", narrowed, in_round, False),
            ("--modes: the same corruption IS caught when two_site_round is named",
             [k for k, _ in MODES], in_round, True),
            ("--modes single_value,two_site_match: a corruption in single_value is caught",
             narrowed, in_single, True),
            ("--modes single_value,two_site_match: a corruption in moves_match is caught",
             narrowed, in_match, True),
            ("--modes single_value: moves_match is out of scope",
             ["single_value"], in_match, False))
    for name, modes, art, must_fail in narrow_cases:
        failed = project(art, modes) != project(base, modes)
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if failed else 'accepted'}"
              f"{'' if good else '  <- expected ' + ('rejection' if must_fail else 'acceptance')}")

    # ...and a narrowed run that PRINTS like a full one is the silent-narrowing bug this file
    # exists to catch in the documents, committed one level down in the tool itself.
    for modes, must_name in ((narrowed, ["two_site_round"]),
                             (["single_value"], ["two_site_match", "two_site_round"]),
                             ([k for k, _ in MODES], [])):
        note = unchecked_note(modes)
        good = all(m in note for m in must_name) and bool(note) == bool(must_name)
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} --modes {','.join(modes)} names what it left out: "
              f"{'|'.join(must_name) or '(nothing left out, no note)'}")

    # The parser is pinned to the REAL documents, not only to this file's renderer: a format
    # the two of them agree on and the repo does not use would pass every case above while
    # gating nothing that is actually published. Parsing only — the committed figures are
    # allowed to be stale (they are, today), but they must still be FOUND.
    live = load_docs(root)
    for spec in DOCS:
        text = live.get(spec.name)
        good = text is not None and spec.rows(text) is not None
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} control: the committed {spec.name} still parses: "
              f"{'located' if good else 'NOT FOUND — the parser gates nothing published'}")

    planted = sum(1 for c in cases if c[3]) + sum(1 for c in narrow_cases if c[3])
    print(f"{'ok ' if ok else 'FAIL'} selftest {planted} corruptions, "
          f"{'all caught' if ok else 'SOME MISSED'}")
    return 0 if ok else 1


def _to_match_only(block):
    """Drop the round column/figure and relabel the surviving one as a match run."""
    if "Per-session" in block:
        return block.replace("--two-site round", "--two-site match")
    out = []
    for line in block.split("\n"):
        if not line.startswith("|"):
            out.append(line)
            continue
        cells = line.strip().strip("|").split("|")
        keep = [c for c in cells if "round" not in c.lower()]
        if len(keep) == len(cells) and len(cells) > 2:
            keep = cells[:-2] + cells[-1:] if "identical" in cells[-1].lower() else cells[:-1]
        out.append("|" + "|".join(keep) + "|")
    return "\n".join(out)


def _single_column_only(block):
    """Keep the session and single-value columns; delete every two-site one."""
    lines = block.split("\n")
    header = [c.lower() for c in lines[0].strip().strip("|").split("|")]
    keep = [i for i, h in enumerate(header) if "two-site" not in h]
    out = []
    for line in lines:
        if not line.startswith("|"):
            out.append(line)
            continue
        cells = line.strip().strip("|").split("|")
        out.append("|" + "|".join(cells[i] for i in keep if i < len(cells)) + "|")
    return "\n".join(out)


# --------------------------------------------------------------------------- main


def _report(out, note):
    for line in out:
        print(f"FAIL {line}", file=sys.stderr)
    if out:
        print(f"\n{len(out)} problem(s). {note}", file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.join(os.path.dirname(__file__), "..", ".."),
                    help="repository root (default: this file's)")
    ap.add_argument("--write", action="store_true", help="re-measure and write the artefacts")
    ap.add_argument("--check", action="store_true",
                    help="re-measure, byte-compare the artefacts, then gate the prose")
    ap.add_argument("--check-prose", action="store_true", dest="check_prose",
                    help="gate the prose against the COMMITTED artefacts, without re-measuring")
    ap.add_argument("--modes", default=None,
                    help="comma-separated subset of " + ",".join(k for k, _ in MODES) +
                         " to byte-compare under --check (default: all). The unnamed modes' "
                         "blocks are carried over unread, and the run names them.")
    ap.add_argument("--render", action="store_true",
                    help="print the document blocks the artefacts imply, to paste")
    ap.add_argument("--selftest", action="store_true",
                    help="plant corruptions and require the gate to catch them, then exit")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    known = [k for k, _ in MODES]
    modes = known
    if args.modes is not None:
        modes = [m.strip() for m in args.modes.split(",") if m.strip()]
        bad = [m for m in modes if m not in known]
        if bad:
            # An unknown name is an error, never a silent no-op: a typo'd mode would narrow
            # the comparison to nothing and still exit 0.
            ap.error(f"unknown mode(s) {', '.join(bad)}; known modes are {', '.join(known)}")
        if not modes:
            ap.error("--modes was given with no mode names")
        modes = [k for k in known if k in modes]        # canonical order, deduplicated
        if not args.check:
            # --write always produces every mode; a narrowed write would drop the others from
            # the committed file, which is a deletion wearing a performance flag's clothes.
            ap.error("--modes narrows --check only; --write always measures every mode")

    if args.selftest:
        return _selftest(root)

    measurable, excluded = session_dirs(root)
    for d, why in excluded:
        # Named, never silently skipped — pipeline/codegen.py:76-78.
        print(f"  --  {os.path.relpath(d, root)}: not measured ({why})")
    if not measurable:
        print(f"FAIL no measurable session found under {root}/sessions", file=sys.stderr)
        return 1

    if args.render:
        for name in DOC_NAMES:
            print(f"\n=== {name} ===\n{render(load_artefacts(root), name)}", end="")
        return 0

    if args.check_prose and not (args.write or args.check):
        arts = load_artefacts(root)
        rc = _report(problems(arts, load_docs(root)),
                     "--check-prose does NOT re-measure: it gates the documents against the "
                     "COMMITTED artefacts. Run --check for the byte-identity half.")
        if rc == 0:
            print(f"  ok  {len(arts)} sessions' artefacts and the figures published in "
                  f"{', '.join(DOC_NAMES)} agree (no re-measurement — that is --check)")
        return rc

    if not (args.write or args.check):
        ap.error("one of --write, --check, --check-prose, --render, --selftest is required")

    note = "" if args.write else unchecked_note(modes)
    if note:
        print(note)

    for_prose, stale = {}, []
    for session, d in measurable:
        print(f"  ..  measuring {session} ({', '.join(modes)})", flush=True)
        art = build(session, d, modes=modes)
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
        committed = json.loads(raw) if raw.strip().startswith("{") else None
        if committed is None:
            stale.append(f"{os.path.relpath(path, root)} does not exist, or is not JSON")
            for_prose[session] = None            # absence is a failure, not a skip
            continue

        # Judged only over the modes this run measured: under --modes the others were never
        # produced, so calling them "gone" would be the narrowing inventing a problem.
        gone = sorted((set(committed.get("modes") or {}) & set(modes)) - set(art["modes"]))
        if gone:
            stale.append(f"{session}: the committed artefact carries mode(s) "
                         f"{', '.join(gone)} that a fresh run does not produce — dropping a "
                         f"mode narrows what is published without saying so")
        if project(committed, modes) != project(art, modes):
            stale.append(f"{os.path.relpath(path, root)} differs from a fresh run"
                         + (f" over {', '.join(modes)}" if note else ""))
        # The document gate needs a whole artefact. Freshly measured blocks win; the rest is
        # the committed file, which `note` above has already told the reader was not re-derived.
        for_prose[session] = _merge(committed, art, modes)

    if args.write:
        print("\nartefacts written. --write never checks the prose; run --check-prose next.")
        return 0

    rc = _report(stale + problems(for_prose, load_docs(root)),
                 "Regenerate the artefacts with --write, and update the published figures "
                 "with --render.")
    if rc == 0:
        print(f"  ok  {len(for_prose)} sessions reproduce byte-for-byte over "
              f"{', '.join(modes)}, and the figures published in {', '.join(DOC_NAMES)} "
              f"match them")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
