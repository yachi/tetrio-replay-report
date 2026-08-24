"""The Donation ablation bands: rendered from the seven artefacts, never typed into prose.

WHAT WENT WRONG, because the gate's shape is a direct consequence of it. `emit-opener-facts.ts`
carried the sentence "the same predicate at these thresholds without the re-opening clause fires on
29-34%" in two comments AND in the `means` prose of every `sessions/*/sim/opener-facts.json`. The
seven-session range is 28.93-36.84% — wrong at BOTH ends, the ceiling by nearly three points — and
because those artefacts are byte-identity gated, the wrong figure was *pinned*: re-emitting them
reproduced it exactly, so every gate in the repo agreed with it. A byte-identity gate certifies
"unchanged", never "correct", and a hand-typed figure inside one is the worst place a number can
live in this repo.

THREE THINGS FOLLOW, and each is a rule rather than a fix to one number.

* **A per-session artefact may not carry a corpus band.** It cannot see the other sessions, so a
  band written into it is a claim it has no way to check — which is how one string was wrong in
  seven files at once. `donation.ablation` now carries this session's own counts and rates, and the
  `means` prose quotes this session's figure and says so. The corpus band is rendered here, from
  all seven, because here is the only place that can see all seven.
* **An ablation is a PARAMETER of the predicate, never a copy of it.** `DONATION_ABLATIONS` in the
  emitter deletes one clause and keeps the rest of the shipped code path, and the emitter throws if
  the `shipped` ablation ever disagrees with the shipped path. A re-implementation would agree the
  day it was written and answer the old question forever after.
* **CLAUDE.md's ROADMAP entry refused the obvious repair for the repertoire ranges** — "a gate that
  recomputes the bands ... its normal state would be red, and a gate whose normal state is red is
  not a gate" — and that refusal does NOT transfer here. It was about a band with no renderer, so
  red meant hand-measuring again. These bands have `--render`: a new session that moves one costs a
  paste, which is the repo's standing rule for any figure with a renderer.

The naive clause is emitted as a CONTROL, not as a finding. `NaiveClauseForced` in
spec/DonationCave.dfy proves it fires on every T-spin clear, so 100.00% here measures nothing about
donations — it says the reconstruction still holds. Anything else is a broken pipeline, and
`_invariants` treats it as one.
"""
import argparse
import glob
import json
import math
import os
import sys

from .docs_gate import (Incomplete, fragment_mutants, fragment_problems, load_docs,
                        render_fragments, reword)

DOCS = ("CLAUDE.md",)
NS = "don:"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGEN = ("REPLAY_DIR=sessions/<date> bun pipeline/sim/emit-opener-facts.ts "
         "--out sessions/<date>/sim/opener-facts.json")
#: the ablation chain, widest last. Every entry deletes a clause the one before it kept, so the
#: counts must be non-decreasing along it — see `_invariants`.
CHAIN = ("shipped", "no_reopen", "cavity1_no_reopen", "naive")
WORDS = {7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def pct2(n, d):
    """A 2-dp percentage string, rounded half-up — `pct2` in emit-opener-facts.ts, in Python.

    Both compute `n * 10000 / d` as one double and round half-up, so they agree by construction
    rather than by convention; `_invariants` checks the emitter's own string against this one so a
    divergence in the last digit is a red build instead of two figures nobody compares.
    """
    return f"{math.floor(n * 10000 / d + 0.5) / 100:.2f}"


def opener_artefacts(root=REPO):
    """[(session, whole artefact)] over every committed opener-facts.json, plus what was left out.

    Shared with `pipeline/check_dual_engine.py`, which rolls up a different block of the same seven
    files. One loader, because two gates that each glob `sessions/*` disagree the first time a
    session directory grows an exception — and the one that reads FEWER sessions is the one that
    goes quietly green on a narrower corpus.
    """
    out, excluded = [], []
    for d in sorted(glob.glob(os.path.join(root, "sessions", "*"))):
        if not os.path.isdir(d):
            continue
        s = os.path.basename(d)
        p = os.path.join(d, "sim", "opener-facts.json")
        if not os.path.exists(p):
            excluded.append((s, "no sim/opener-facts.json"))
            continue
        out.append((s, json.load(open(p, encoding="utf-8"))))
    return out, excluded


def artefacts(root=REPO):
    """[(session, ablation, means)] over every committed opener-facts.json, plus what was left out."""
    whole, excluded = opener_artefacts(root)
    out = []
    for s, art_all in whole:
        art = art_all["donation"]
        if "ablation" not in art:
            # Never a skip. An artefact predating the field would otherwise drop out of the band
            # silently, and a band measured over fewer sessions than the corpus reads identically
            # to one measured over all of them.
            excluded.append((s, "its opener-facts.json predates donation.ablation — re-emit it: "
                                + REGEN))
            continue
        out.append((s, art["ablation"], art["means"]))
        # The well-provenance counts ride along: they are the other figure this section publishes
        # over the same denominator, and a second gate over the same seven files is the "two
        # parsers over one document" shape docs_gate.py was written to stop.
        out[-1][1]["self_built"] = sum(p["self_built_well"] for p in art["players"])
        out[-1][1]["garbage"] = sum(p["garbage_derived_well"] for p in art["players"])
    return out, excluded


def _invariants(arts):
    """The three things that must hold before any band is worth rendering."""
    bad = []
    for s, a, means in arts:
        n, c = a["scored"], a["counts"]
        # (1) THE FORCED CLAUSE. Proved, so this measures the reconstruction and not the technique.
        if c["naive"] != n:
            bad.append(f"{s}: the naive clause fired on {c['naive']} of {n} scored clears. It is "
                       f"PROVED forced (NaiveClauseForced, spec/DonationCave.dfy), so anything but "
                       f"all of them means the reconstruction is broken, not the theorem")
        # (2) THE LATTICE. Each ablation deletes a clause the previous one kept, so it can only
        # widen. A drop means two entries no longer differ by one clause — i.e. the ablation is no
        # longer an ablation of the shipped predicate.
        for x, y in zip(CHAIN, CHAIN[1:]):
            if c[x] > c[y]:
                bad.append(f"{s}: ablation {y!r} ({c[y]}) fires less often than {x!r} ({c[x]}), "
                           f"but it deletes a clause {x!r} keeps, so it can only fire more")
        # (3) THE TWO RENDERERS. The artefact's own prose quotes this session's no_reopen rate;
        # it is written by emit-opener-facts.ts and this string by pct2 above. They are checked
        # against each other because two renderers of one figure is this repo's recurring shape.
        want = f"fires on {pct2(c['no_reopen'], n)}% of this session's {n}."
        if want not in means:
            bad.append(f"{s}: donation.means does not say {want!r}. The emitter renders that "
                       f"figure and so does this gate; if they disagree, one of them is wrong "
                       f"and neither says so. Re-emit: {REGEN}")
    return bad


def figures(arts):
    """Everything the fragments below are rendered from. Counts in, strings out."""
    rate = {k: {s: pct2(a["counts"][k], a["scored"]) for s, a, _ in arts} for k in CHAIN}
    tot = {k: sum(a["counts"][k] for _, a, _ in arts) for k in CHAIN}
    n = sum(a["scored"] for _, a, _ in arts)
    f = {"sessions": len(arts), "scored": n, "donations": tot["shipped"],
         "pooled": {k: pct2(tot[k], n) for k in CHAIN},
         "self_built": sum(a["self_built"] for _, a, _ in arts),
         "latest": arts[-1][0], "latest_garbage": arts[-1][1]["garbage"],
         "latest_donations": arts[-1][1]["counts"]["shipped"]}
    for k in CHAIN:
        vals = [rate[k][s] for s, _, _ in arts]
        f[k] = {"series": vals, "lo": min(vals, key=float), "hi": max(vals, key=float),
                "hi_session": max(arts, key=lambda t: float(rate[k][t[0]]))[0]}
    return f


def _band(f, k):
    return f"{f[k]['lo']}-{f[k]['hi']}%"


def _series(f, k):
    return " · ".join(f[k]["series"])


def _word(f):
    n = f["sessions"]
    if n not in WORDS:
        raise Incomplete(f"there is no spelled-out word for {n} sessions — add it to WORDS")
    return WORDS[n]


#: key -> (renderer, the documents that must carry it). A document not listed here that carries the
#: marker is an error, and so is a `don:` marker no key claims — see `fragment_problems`.
SPECS = {
    NS + "sessions": (_word, DOCS),
    NS + "scored": (lambda f: str(f["scored"]), DOCS),
    NS + "donations": (lambda f: str(f["donations"]), DOCS),
    # Pooled, not a band: `_invariants` forces it to be every session's whole denominator, so
    # a per-session range would render "100.00-100.00%" and read as a measurement with spread.
    NS + "naive": (lambda f: f["pooled"]["naive"] + "%", DOCS),
    NS + "noreopen-band": (lambda f: _band(f, "no_reopen"), DOCS),
    NS + "noreopen-series": (lambda f: _series(f, "no_reopen"), DOCS),
    NS + "noreopen-ceiling": (lambda f: f["no_reopen"]["hi_session"], DOCS),
    NS + "shipped-band": (lambda f: _band(f, "shipped"), DOCS),
    NS + "cav1-band": (lambda f: _band(f, "cavity1_no_reopen"), DOCS),
    NS + "cav1-series": (lambda f: _series(f, "cavity1_no_reopen"), DOCS),
    NS + "cav1-ceiling": (lambda f: f["cavity1_no_reopen"]["hi"], DOCS),
    NS + "pooled-noreopen": (lambda f: f["pooled"]["no_reopen"], DOCS),
    NS + "pooled-cav1": (lambda f: f["pooled"]["cavity1_no_reopen"], DOCS),
    NS + "self-built": (lambda f: f"{f['self_built']} of {f['donations']}", DOCS),
    # The newest session's own row, because "0 self-built" is the kind of absolute that is worth
    # re-stating for the session that just landed — and the session NAME is inside the marker, so
    # adding one cannot leave the sentence naming the previous one.
    NS + "latest-garbage": (lambda f: f"{f['latest'][5:]} adds {f['latest_garbage']} of "
                                      f"{f['latest_donations']}", DOCS),
}


def problems(f, docs):
    out = []
    for name, text in docs.items():
        out += fragment_problems(name, text, SPECS, f, reword(__name__), namespace=NS)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    arts, excluded = artefacts()
    for s, why in excluded:
        print(f"  not measured: {s} — {why}")
    if not arts:
        print("no sessions/*/sim/opener-facts.json carries donation.ablation")
        return 1
    bad = _invariants(arts)
    if bad:
        for b in bad:
            print("  " + b)
        return 1
    f = figures(arts)
    if args.render:
        for name in DOCS:
            print(f"# {name}")
            print(render_fragments(SPECS, f, name), end="")
        return 0
    docs = load_docs(REPO, DOCS)
    bad = problems(f, docs)
    for b in bad:
        print("  " + b)
    print(f"donation ablations: {f['sessions']} sessions, {f['scored']} scored clears; "
          f"shipped {_band(f, 'shipped')} ({f['donations']}), "
          f"no-reopen {_band(f, 'no_reopen')}, cavity>=1 {_band(f, 'cavity1_no_reopen')}, "
          f"naive {f['pooled']['naive']}% (forced) — {len(bad)} problem(s)")
    return 1 if bad else 0


def selftest():
    """Mutants. A gate over a number nobody can move is the defect this file was written about."""
    arts, _ = artefacts()
    f = figures(arts)
    docs = load_docs(REPO, DOCS)
    ok = True

    def case(label, fn, must_fail=True):
        nonlocal ok
        got = bool(fn())
        good = got == must_fail
        ok = ok and good
        print(f"  {'ok  ' if good else 'BAD '} {label}")

    # ── the committed state passes, which is the control every mutant is read against
    case("the committed CLAUDE.md agrees with the artefacts", lambda: problems(f, docs), False)

    # ── the invariants
    def bend(session, key, delta):
        m = [(s, json.loads(json.dumps(a)), t) for s, a, t in arts]
        for s, a, _ in m:
            if s == session:
                a["counts"][key] += delta
        return _invariants(m)

    s0 = arts[0][0]
    case("the naive clause stops firing on everything", lambda: bend(s0, "naive", -1))
    case("an ablation fires less than the one it widens",
         lambda: bend(s0, "cavity1_no_reopen", -10 ** 6))
    case("the emitter's own means figure disagrees with this renderer",
         lambda: _invariants([(s, a, t.replace("fires on", "fires around")) for s, a, t in arts]))
    # ...and the control: the committed artefacts satisfy all three.
    case("the committed artefacts satisfy the invariants", lambda: _invariants(arts), False)

    # ── a session dropping out must not silently narrow the band. The band is a min/max, so
    # dropping the CEILING session is the mutation that matters: it is the one that reads as a
    # narrower, tidier band rather than as a missing session.
    hi = f["no_reopen"]["hi_session"]
    case("dropping the ceiling session changes the published band",
         lambda: _band(figures([t for t in arts if t[0] != hi]), "no_reopen") != _band(f, "no_reopen"))

    # ── the fragments
    n = 0
    for label, name, text, must in fragment_mutants(SPECS, f, DOCS,
                                                    lambda k: docs[k], namespace=NS):
        d = dict(docs)
        d[name] = text
        got = bool(problems(f, d))
        if got != must:
            ok = False
            print(f"  BAD  {label}")
        n += 1
    print(f"  {'ok  ' if ok else 'BAD '} {n} fragment mutants")
    print("selftest: " + ("ok" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
