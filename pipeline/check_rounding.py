"""Does the corpus actually distinguish this rounding rule from the alternatives?

THE DEFECT CLASS, stated once. Every printed figure in this repo shortens a number, and
shortening needs a rule: 約 means "at least this much" so it FLOORS, an upper bound must CEIL or
the sentence claims more than its proof, and a p supporting 「rejected」 ceils while one supporting
「still flat」 floors. Those rules are enforced by exactly one thing — a corpus value where the
rules disagree. Where no such value exists, the rule is a comment: a mutant swapping it survives
every byte-identity gate, every ledger regeneration and every re-render, because nothing it
produces changes.

That is not hypothetical. `forecast_section` printed a ratio with `:.0f`, which is round-half-even,
where the surrounding convention floors; it was invisible for exactly as long as no ratio in the
corpus landed on a half. And three of the four rounding defects found on 2026-08-23/24 were not
missing rules at all but rules pointed the WRONG WAY — 「2.1-3.3%」 for a band whose floor is 2.08,
「足足細咗四倍」 for a ratio of 3.82, 「27 locks against 81」 for a mean of 80.4.

SO THIS GATE ANSWERS TWO QUESTIONS PER SITE, and the second is the one that was missing:

  1. **Is the rule exercised?** Replay every recorded call under the other rules. If some call
     renders differently, the corpus discriminates and the rule is enforced by the artefacts.
  2. **Is the rule declared?** `fmt.quant` takes the rule as an argument, so every site states
     which one it wants at the call. A site with no declared rule cannot be checked, and
     `_uncovered` makes that a failure rather than an absence.

WHAT IT DOES NOT DO, said plainly because a gate that overstates its coverage is the thing this
repo keeps finding. It cannot tell you a declared direction is the RIGHT one — 「27 against 81」
had a rule, applied it consistently, and pointed the wrong way. It reports which sites are
enforced by data and which are on trust; choosing the direction stays a human judgement recorded
beside the call.

The population is what a full render actually calls, not what the source could call: the tracer
runs `build_report` over every session and the fragment renderers over their documents, then
reports per site. A site the render never reaches is reported as unreached, never as agreeing.
"""
import argparse
import ast
import collections
import glob
import io
import os
import re
import shutil
import sys
import tempfile
import tokenize

from . import fmt
from .docs_gate import (fragment_mutants, fragment_problems, load_docs,
                        render_fragments, reword)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Modules whose printed figures this gate covers. Every precision-reducing expression in one of
#: these must go through `fmt.quant` or be named in `EXCUSED` with a reason — see `_uncovered`.
#: A list, and it is checked against the filesystem rather than trusted: `_uncovered` walks these
#: paths and fails on a site it does not recognise, which is the `bin/verify-repo` discipline
#: (read the source, do not carry a copy of what it says).
COVERED = (
    "pipeline/fmt.py",
    "pipeline/claims/generators.py",
    "pipeline/intense_round.py",
    "pipeline/opener_section.py",
    "pipeline/forecast_section.py",
    "pipeline/forecast_pooled.py",
    "pipeline/records.py",
    "pipeline/pc_section.py",
    "pipeline/build_round_table.py",
    "pipeline/skeleton.py",
    "pipeline/claim_cards.py",
)

#: What this gate does NOT cover, and why — printed on every run. An uncovered module is not a
#: silence here for the same reason `bin/verify-repo` prints every job it did not run: a sweep that
#: covered less than it claimed is the failure the tool exists to stop.
NOT_COVERED = {
    "the check_* gates": "each renders figures for its own document (`check_rate_records._q`, "
                         "`check_dual_engine._q`, `check_donation_bands.pct2`, "
                         "`check_stat_sources`) and each already re-renders its directional "
                         "figures under the opposite rule in its own --selftest. Folding them in "
                         "would mean this gate importing every gate",
    "analysis/*.py": "produces artefacts, not published prose; `rate-records.json` and "
                     "`stat-sources` figures are rendered by the gates above",
    "pipeline/extract.py": "`floor(v * 1000 + 0.5)` is the x1000 EXTRACTION rule — it decides what "
                           "the dataset holds, not how a figure prints, and it is pinned by the "
                           "two extractors agreeing byte-for-byte",
    "the TypeScript side": "`emit-opener-facts.ts`'s `pct2` is checked against its Python twin by "
                           "`check_donation_bands._invariants`",
}

#: (path, function) -> why this function's precision-reducing arithmetic is not a printed figure.
#: Keyed by the ENCLOSING FUNCTION rather than by a substring of the line, because a substring
#: excuse silently widens: `"// 1000"` written to excuse one millisecond conversion also excuses
#: the next one anybody adds anywhere in the file. Every entry is a decision with a reason, and an
#: entry that matches nothing is a failure too — a stale excuse is how a list starts lying.
EXCUSED = {
    # ---- an OPERAND OF THE PROOF, which no rounding rule may touch ----
    ("pipeline/claims/generators.py", "intense_round_vs_split"):
        "`_VS_K * atk // ft` and `-(-resid // ft)` are terms of the proved VS identity — they are "
        "what the lemma asserts, not how a figure prints. Changing the rule would change the "
        "THEOREM",
    ("pipeline/claims/generators.py", "match_level_apm_max"):
        "`v // 100 * 100` are the edges of a `between` predicate — the bucket the lemma proves "
        "the value sits in",
    ("pipeline/claims/generators.py", "decider_final_rounds"):
        "`v // 100 * 100` band edges again, inside the proved predicate",
    ("pipeline/claims/generators.py", "sweep_shutout"):
        "`// 1000` converts an x1000 difference to whole units for a `between` bound",
    ("pipeline/intense_round.py", "_pinned_rate"):
        "`between['lo'] // den` INVERTS a quantization the claim already made — it reads the "
        "figure back out of the proved band rather than deciding one",
    # ---- a threshold or a comparison, not a printed figure ----
    ("pipeline/claims/generators.py", "rate_by_outcome"):
        "`(gap * 100) // base` feeds `gap_pct < 5`, a relative significance cutoff; the quotient "
        "is never printed",
    ("pipeline/build_round_table.py", "bar_ranges"):
        "the per-piece rate here sets a bar's MIN/MAX for scaling, not a printed cell",
    ("pipeline/build_round_table.py", "bar_value"):
        "the same value as a bar width and a sort key — `ratio()` renders the printed cell",
    # ---- not a published figure at all ----
    ("pipeline/build_round_table.py", "build"):
        "`--b: {frac:.3f}` is a CSS custom property driving a bar's width",
    ("pipeline/records.py", "_check_sd_ratio"):
        "`:.4f` inside the guard's own ERROR MESSAGE — it prints only on the build failure it "
        "describes",
    ("pipeline/records.py", "build"):
        "`QUALIFYING_MS // 1000` prints the threshold the qualifier is defined by",

    # ---- not a published figure at all ----
    ("pipeline/build_round_table.py", "build"):
        "`--b: {frac:.3f}` is a CSS custom property driving a bar's width, not a number anybody "
        "reads; three places is a rendering detail of the bar",
    ("pipeline/records.py", "_check_sd_ratio"):
        "`:.4f` inside the guard's own ERROR MESSAGE — it prints only on the build failure it "
        "describes, and the figure it diagnoses is the one the guard just rejected",
    ("pipeline/records.py", "build"):
        "`QUALIFYING_MS // 1000` prints the threshold the qualifier is defined by",

    # ---- not a precision choice at all ----
    ("pipeline/fmt.py", "fmt_clock"):
        "`// 60` and `% 60` split an already-floored second count into m:ss — clock arithmetic",
    ("pipeline/claims/generators.py", "round_duration_extremes"):
        "the same m:ss split, on the claim side",
    # ---- a floor that IS the convention, pinned elsewhere ----
    ("pipeline/fmt.py", "ratio1"):
        "quantizes decimal STRINGS rather than an x1000 integer, so it cannot route through "
        "quant; `fmt --selftest` pins its floor on three discriminating cases, including the two "
        "float spellings that get it wrong",
    ("pipeline/fmt.py", "secs"):
        "floors milliseconds to whole seconds; `fmt --selftest` pins it at 228999 -> 228",
    ("pipeline/claims/generators.py", "_sec"):
        "the same millisecond floor as fmt.secs, on the claim side",
    ("pipeline/claims/generators.py", "unqualified_rate_peaks"):
        "`QUALIFYING_MS // 1000` is the threshold in seconds, and `_dur(...) // 1000` is the same "
        "millisecond floor as fmt.secs",
    # ---- a THRESHOLD being printed, not a measurement being shortened ----
    ("pipeline/claims/generators.py", "round_superlatives"):
        "`QUALIFYING_MS // 1000` prints the constant the qualifier is defined by",
    ("pipeline/claims/generators.py", "most_intense_round"):
        "`QUALIFYING_MS // 1000`, the same constant",
    ("pipeline/claims/generators.py", "fast_round_record"):
        "`LIMIT // 1000` prints the cut-off the record is defined by",
    ("pipeline/claims/generators.py", "high_apm_round_record"):
        "`LIMIT // 1000`, the same shape",
    # ---- an OPERAND OF THE PROOF, which no rounding rule may touch ----
    ("pipeline/claims/generators.py", "match_level_apm_max"):
        "`v // 100 * 100` are the edges of a `between` predicate — the bucket the lemma proves "
        "the value sits in. Changing the rule here would change what is PROVED, not how it prints",
    ("pipeline/claims/generators.py", "decider_final_rounds"):
        "`v // 100 * 100` band edges again, inside the proved predicate",
    ("pipeline/claims/generators.py", "sweep_shutout"):
        "`// 1000` converts an x1000 difference to whole units for a `between` bound in the "
        "predicate, not for printing",
}

#: The precision-reducing spellings this gate knows how to look for. Deliberately WIDER than what
#: it expects to find: a pattern that missed a spelling would report a clean sweep over a module
#: carrying an unchecked rule, which is the failure mode the whole file is about.
#:
#: IT ALREADY HAPPENED HERE, on the first run. The pattern was `//\s*\d`, which reads as "integer
#: division" and is not: `opener_section._share` floors with `num * 1000 // den`, dividing by a
#: NAME, and the scan reported that module clean while the floor the whole 約 convention rests on
#: sat unexamined. A bare `//` over-reports — every index-halving and every millisecond conversion
#: lands in EXCUSED with a reason — and over-reporting is the direction this must fail in.
_REDUCERS = re.compile(r"math\.floor|math\.ceil|ROUND_[A-Z_]+|\bround\(|//|:\s*\.\d+f")

#: The bodies in `pipeline/fmt.py` that IMPLEMENT a rule rather than choose one.
_QUANTIZERS = frozenset({"quant", "quantf", "permille", "mean_x1000"})

_DEF_LINE = {}


def _code_lines(path):
    """{line no: the line's CODE, strings and comments removed}.

    Via `tokenize`, not a `#`-split: the first version walked raw lines and reported a sentence
    inside this file's own docstring because it contained "ROUND_HALF_UP". A gate whose findings
    include its own prose is one nobody reads twice.
    """
    out = collections.defaultdict(str)
    with open(path, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER):
                continue
            # F-STRINGS ARE KEPT, and that exception is the whole reason this is not a plain
            # token filter: `:.1f` lives INSIDE the literal, so dropping every STRING drops
            # exactly the spelling most likely to carry an undeclared rule. Plain literals and
            # docstrings are still dropped, which is what stops this file's own prose from being
            # reported. (Under Python 3.12+ f-strings tokenize into pieces and this is moot; the
            # prefix test covers the single-token spelling every earlier version produces.)
            if tok.type == tokenize.STRING and not tok.string[:3].lower().lstrip("r").startswith("f"):
                continue
            out[tok.start[0]] += tok.string + " "
    return out


def _enclosing(path):
    """{line no: the innermost enclosing def's name}, so an excuse names a FUNCTION."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    out, depth = {}, {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        span = (node.end_lineno or node.lineno) - node.lineno
        for ln in range(node.lineno, (node.end_lineno or node.lineno) + 1):
            # the SHORTEST span wins, which is the innermost def covering the line
            if ln not in depth or span < depth[ln]:
                out[ln], depth[ln] = node.name, span
    return out


def _uncovered(root=REPO):
    """Precision-reducing code in COVERED modules that neither routes through `quant` nor carries
    an excuse, plus any excuse that no longer matches anything.

    Returns [(path, line no, source or reason)] — every entry is a failure.
    """
    out, used = [], set()
    for rel in COVERED:
        path = os.path.join(root, rel)
        code = _code_lines(path)
        where = _enclosing(path)
        for i, text in sorted(code.items()):
            if not _REDUCERS.search(text):
                continue
            fn = where.get(i)
            # The quantizers themselves are what everything else declares AGAINST, so their own
            # bodies are the one place a bare `//` is the subject rather than a finding. Named
            # rather than pattern-matched, so adding a helper to fmt.py without adding it here is
            # a failure and not a silent exemption.
            if rel == "pipeline/fmt.py" and fn in _QUANTIZERS:
                continue
            # `\bquant\s*\(` and not `"quant" in text`: the loose test also matched
            # `Decimal.quantize(...)`, which is a DIFFERENT rounding decision and exactly the
            # kind of site this gate exists to see.
            if re.search(r"\bquant\s*\(", text):
                continue
            why = EXCUSED.get((rel, fn))
            if why is None:
                out.append((rel, i, text.strip()[:90]))
            else:
                used.add((rel, fn))
    for key in sorted(set(EXCUSED) - used):
        out.append((key[0], 0, f"the excuse for {key[1]!r} matches nothing any more — a stale "
                               f"excuse is a list that has started lying"))
    return out


def _render_all(root=REPO):
    """Run every renderer the corpus has, with the tracer on. Returns the recorded calls.

    `build_report` is the whole published pipeline — hero, 數據對決, 全場之最, the claim ledgers
    through `build_claims`, 最癲一局, the round table. Running it for every session is what makes
    the population the figures actually printed rather than the ones the code could print.
    """
    from .claims import build_claims
    from . import build_report, build_round_table, forecast_pooled

    fmt.TRACE = []
    quiet = io.StringIO()
    real = sys.stdout
    try:
        sys.stdout = quiet
        for d in sorted(glob.glob(os.path.join(root, "sessions", "*", "*"))):
            if not os.path.exists(os.path.join(d, "facts.json")):
                continue
            # `--check` so the sweep cannot write: this gate renders in order to WATCH, and a
            # renderer that also rewrote the corpus would make its own findings unfalsifiable.
            build_report.main([d, "--check"])
            build_claims.main([os.path.join(d, "facts.json"), "--out", os.devnull])
            # The round table has its own generator predating `pipeline/region.py`, so
            # `build_report` does not reach it — and it holds two of the quantizers. A sweep that
            # skipped it would report a site count that reads complete.
            # …in a COPY. `build_round_table` has no --check mode, and a gate that rewrites the
            # corpus it is measuring cannot be trusted about what it found: the re-render would
            # be measuring its own output. The copy is two files.
            with tempfile.TemporaryDirectory() as tmp:
                for name in ("report.html", "facts.json"):
                    shutil.copy(os.path.join(d, name), os.path.join(tmp, name))
                build_round_table.main([tmp])
        # The pooled forecast block is a docs-level renderer, not a per-session one, so it is
        # run once outside the loop. Guarded: a repo with no forecast artefact is a legitimate
        # state and `section()` renders a refusal for it.
        forecast_pooled.section(forecast_pooled.pool(forecast_pooled.load_all(root)))
    finally:
        sys.stdout = real
        trace, fmt.TRACE = fmt.TRACE, None
    return trace


def discriminate(trace):
    """{site: {'calls', 'kind', 'rule', 'alt': {other rule: how many calls it would change}}}

    The replay calls the SAME helper under the other rule — `fmt._helpers()[kind]` — rather than
    reimplementing it. A reimplementation would answer the question about the copy, which is the
    mistake `DONATION_ABLATIONS` was written to avoid on the simulator side.
    """
    helpers = fmt._helpers()
    by = collections.defaultdict(list)
    for site, kind, args, rule in trace:
        by[(site, kind)].append((args, rule))
    out = {}
    for (site, kind), calls in sorted(by.items(), key=lambda kv: str(kv[0])):
        fn = helpers[kind]
        rules = {r for _, r in calls}
        alt = {}
        for other in fmt.RULES:
            if other in rules:
                continue
            alt[other] = sum(1 for args, r in calls if fn(*args, r) != fn(*args, other))
        # KEYED BY (site, kind), not by site. `build_round_table.ratio` quantizes TWICE — a
        # per-mille and then a quantize — under one site name, and keying by site alone let the
        # second overwrite the first: the printed figure count came out 7 954 against a trace of
        # 11 554, i.e. the summary silently dropped 3 600 calls it had recorded.
        out[f"{site} [{kind}]" if site else f"<unnamed {kind} call>"] = {
            "calls": len(calls), "kind": kind, "rule": "/".join(sorted(rules)), "alt": alt,
            # EVERY alternative must be discriminated, not just one. At seven sessions
            # `records._dp1` separated floor from ceil on 14 calls and from ROUND on none, so a
            # mutant swapping its floor for round changed no published byte — a site reported as
            # enforced on the strength of the ceil column alone would have hidden exactly the
            # defect this gate is named after. Ten sessions later the round column is non-zero
            # too and the site is genuinely enforced; the rule did not move, the data did, which
            # is the whole argument for measuring this rather than asserting it.
            "unenforced": sorted(k for k, v in alt.items() if not v),
            "discriminating": bool(alt) and all(alt.values())}
    return out


DOCS = ("CLAUDE.md",)
NS = "round:"

#: key -> (renderer, documents). The sweep's own headline figures, gated the way every other
#: rendered number in this repo is — a gate that publishes an ungated count of ungated figures
#: would be the joke version of itself.
SPECS = {
    NS + "figures": (lambda r: str(r["figures"]), DOCS),
    NS + "sites": (lambda r: str(r["sites"]), DOCS),
    NS + "enforced": (lambda r: str(r["enforced"]), DOCS),
    NS + "ontrust": (lambda r: str(r["sites"] - r["enforced"]), DOCS),
    NS + "dp1-split": (lambda r: f"{r['dp1_ceil']} 個 call", DOCS),
    NS + "dp1-round": (lambda r: f"{r['dp1_round']} 個 call", DOCS),
}


def problems(head, docs):
    out = []
    for name, text in docs.items():
        out += fragment_problems(name, text, SPECS, head,
                                 reword("pipeline/check_rounding.py"), namespace=NS)
    return out


def headline(res):
    dp1 = res.get("records._dp1 [quantf]", {})
    return {"figures": sum(v["calls"] for v in res.values()), "sites": len(res),
            "enforced": sum(1 for v in res.values() if v["discriminating"]),
            "dp1_ceil": dp1.get("alt", {}).get("ceil", 0),
            # BOTH alternatives, because the prose quoting this site names the floor-vs-ROUND
            # pair specifically. Only `dp1_ceil` was exposed, so CLAUDE.md's sentence about the
            # round pair was rendered from the ceil column — gated, and describing the wrong
            # comparison. Both are fragments now; a sentence naming one may not print the other.
            "dp1_round": dp1.get("alt", {}).get("round", 0)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    bad = []
    for rel, i, src in _uncovered():
        bad.append(f"{rel}:{i} reduces precision outside fmt.quant and carries no excuse: {src}")
    trace = _render_all()
    res = discriminate(trace)
    if not res:
        bad.append("a full render recorded no fmt.quant call at all — the tracer is not wired to "
                   "the renderers, so a clean sweep here would mean nothing")
    print(f"rounding: {len(trace)} quantized figures over {len(res)} "
          f"(site, helper) pair(s)")
    weak = []
    for site, r in res.items():
        alts = ", ".join(f"{k} would change {v}" for k, v in sorted(r["alt"].items()))
        mark = "ok  " if r["discriminating"] else "--  "
        print(f"  {mark} {site}: rule={r['rule']} calls={r['calls']} — "
              f"{alts or 'no alternative'}")
        for other in r["unenforced"]:
            weak.append(f"{site}: {r['rule']} vs {other}")
    if weak:
        # NOT a failure, and that is a decision rather than a softening. A pair the corpus cannot
        # separate is a true statement about the corpus — `fmt.r3` prints thousandths of an x1000
        # integer and can never separate anything, so failing here would make the gate's normal
        # state red with no fix but deleting a correct line. Naming the pairs is the deliverable.
        print(f"  ON TRUST — no corpus value separates these {len(weak)} rule pair(s), so a "
              f"mutant swapping them changes no published byte:")
        for w in weak:
            print(f"      {w}")
    head = headline(res)
    if args.render:
        for name in DOCS:
            print(f"# {name}")
            print(render_fragments(SPECS, head, name), end="")
        return 0
    docs = load_docs(REPO, DOCS)
    bad += problems(head, docs)
    print("  not covered, and why:")
    for what, why in sorted(NOT_COVERED.items()):
        print(f"      {what}: {why}")
    for b in bad:
        print("  " + b)
    return 1 if bad else 0


def selftest():
    ok = True

    def case(label, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print(f"  {'ok  ' if good else 'BAD '} {label}")

    # ── the quantizer itself, on values that DISCRIMINATE. A case where the rules agree pins
    # nothing, which is the defect this whole module reports on.
    case("floor 114.299 -> 114.2", fmt.quant(114299, 1, "floor"), "114.2")
    case("round 114.299 -> 114.3", fmt.quant(114299, 1, "round"), "114.3")
    case("ceil 114.299 -> 114.3", fmt.quant(114299, 1, "ceil"), "114.3")
    case("floor 1.429 -> 1.42", fmt.quant(1429, 2, "floor"), "1.42")
    case("ceil 0.013 -> 0.02 (the bound rule)", fmt.quant(13, 2, "ceil"), "0.02")
    case("floor 0.013 -> 0.01 (what the bound must not print)", fmt.quant(13, 2, "floor"), "0.01")
    # half-up, not half-even: 0.125 at 2dp is 0.13, and Python's own f"{0.125:.2f}" says 0.12
    case("round is half-UP at a tie", fmt.quant(125, 2, "round"), "0.13")
    case("...which Python's own float formatting does not do", f"{0.125:.2f}", "0.12")
    # ── the three copies are now ONE function, and that is asserted by identity rather than by
    # agreement on a value: two copies that happen to agree today is exactly the state this
    # refactor removed, and a test comparing outputs would pass in that state too.
    from .claims import generators
    from . import intense_round
    for name, got in (("generators._one_dp", generators._one_dp(114299)),
                      ("generators._two_dp", generators._two_dp(1429)),
                      ("intense_round._r1", intense_round._r1(114299)),
                      ("intense_round._r2", intense_round._r2(1429))):
        want = fmt.quant(114299, 1, "floor") if name.endswith(("_one_dp", "_r1")) \
            else fmt.quant(1429, 2, "floor")
        case(f"{name} routes through quant on a discriminating value", got, want)
    case("generators._bound_dp ceils where the others floor",
         (generators._bound_dp(13), generators._two_dp(13)), ("0.02", "0.01"))

    # ── the other three helpers, each on a value that discriminates
    case("permille floors 1/3", fmt.permille(1, 3), 333)
    case("permille ceils 1/3", fmt.permille(1, 3, "ceil"), 334)
    case("permille rounds 2/3 half-up", fmt.permille(2, 3, "round"), 667)
    case("mean_x1000 floors 7/2", fmt.mean_x1000(7, 2), 3)
    case("mean_x1000 ceils 7/2", fmt.mean_x1000(7, 2, "ceil"), 4)
    case("mean_x1000 rounds 7/2 half-up", fmt.mean_x1000(7, 2, "round"), 4)
    case("quantf floors 3.8666", fmt.quantf(3.8666, 1), "3.8")
    case("quantf rounds 3.8666", fmt.quantf(3.8666, 1, "round"), "3.9")
    case("pct1 is exact on a per-mille", fmt.pct1(432), "43.2%")
    for kind, fn in sorted(fmt._helpers().items()):
        try:
            fn(1, 1, "nearest") if kind in ("permille", "mean_x1000") else fn(1, 1, "nearest")
            case(f"{kind} refuses an unknown rule", "accepted", "raised")
        except ValueError:
            case(f"{kind} refuses an unknown rule", "raised", "raised")

    # ── every helper the tracer can record must be replayable, or `discriminate` KeyErrors on a
    # site the corpus actually has. Checked as a set rather than by exercising each: a helper
    # added to fmt.py without a `_helpers()` entry is the failure, and it is silent until a
    # render happens to reach it.
    import inspect
    traced = {m.group(1) for m in re.finditer(r'TRACE\.append\(\(site, "(\w+)"',
                                             inspect.getsource(fmt))}
    case("every traced helper is replayable", traced - set(fmt._helpers()), set())
    case("every replayable helper is traced", set(fmt._helpers()) - traced, set())
    case("the quantizer bodies named here are the ones fmt defines",
         _QUANTIZERS - set(fmt._helpers()), set())

    # ── a stale excuse is a failure too: a list that has started lying reads exactly like one
    # that has not.
    saved = dict(EXCUSED)
    try:
        EXCUSED[("pipeline/fmt.py", "no_such_function")] = "planted"
        case("an excuse matching nothing is reported",
             any("matches nothing" in x[2] for x in _uncovered()), True)
    finally:
        EXCUSED.clear()
        EXCUSED.update(saved)
    case("...and the committed excuses all match something",
         any("matches nothing" in x[2] for x in _uncovered()), False)

    # ── an unknown rule must be refused rather than silently floored
    try:
        fmt.quant(1, 1, "nearest")
        case("an unknown rule is refused", "accepted", "raised")
    except ValueError:
        case("an unknown rule is refused", "raised", "raised")

    # ── the coverage scan has teeth: a planted reducer in a covered module must be reported
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for rel in COVERED:
            os.makedirs(os.path.join(tmp, os.path.dirname(rel)), exist_ok=True)
            with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
                body = fh.read()
            with open(os.path.join(tmp, rel), "w", encoding="utf-8") as fh:
                fh.write(body)
        case("the committed modules are clean", _uncovered(tmp), [])
        planted = os.path.join(tmp, COVERED[1])
        with open(planted, "a", encoding="utf-8") as fh:
            fh.write('\n\ndef _sneaky(x):\n    return f"{x / 100:.1f}"\n')
        case("a planted `:.1f` in a covered module is reported",
             bool(_uncovered(tmp)), True)

    # ── the discriminator: a site whose calls all agree under every rule is NOT discriminating
    case("an exact-valued site is reported as on-trust",
         discriminate([("s", "quant", (666, 3), "floor")])["s [quant]"]["discriminating"],
         False)
    case("a site with one straddling value IS discriminating",
         discriminate([("s", "quant", (666, 3), "floor"),
                       ("s", "quant", (1150, 1), "floor")])["s [quant]"]["discriminating"], True)

    # ── the fragments, enumerated per (document, key) like every other gate here
    res = discriminate(_render_all())
    head = headline(res)
    docs = load_docs(REPO, DOCS)
    case("the committed CLAUDE.md agrees with the sweep", bool(problems(head, docs)), False)
    # A LOCAL flag, not the cumulative `ok`: reusing it made this line print BAD because some
    # earlier case had failed, i.e. the summary blamed the mutants for someone else's failure.
    n, frag_ok = 0, True
    for label, name, text, must in fragment_mutants(SPECS, head, DOCS,
                                                    lambda k: docs[k], namespace=NS):
        d = dict(docs)
        d[name] = text
        if bool(problems(head, d)) != must:
            frag_ok = False
            print(f"  BAD  {label}")
        n += 1
    ok = ok and frag_ok
    print(f"  {'ok  ' if frag_ok else 'BAD '} {n} fragment mutants")

    print("selftest: " + ("ok" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
