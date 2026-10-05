"""`python3 -m pipeline.claims.equiv --selftest` — the relevance index, checked against the oracle.

The indexed sweep in `equiv.py` evaluates only the claims a mutant can observe (every run
prints the share, per mode — `equiv.evals_line`) and fills the rest with pristine verdicts. That is exact only while `readset.py`'s premises hold, and a
defect in the index is SILENT in the worst direction: a claim wrongly left out keeps its
pristine verdict, its vector loses False bits, and a hand claim drifts toward 「implied」. So
the index is held to the repo's standing method, two implementations of one question:

  (i)  DIFFERENTIAL. `equiv_reference` — the frozen exhaustive implementation — and the
       indexed `measure_modes` run over 2026-09-03 and 2026-07-24, single_value +
       two_site_match (and 09-03's two_site_round with `--selftest-round`). The WHOLE result
       dict must be json-identical (`detail` and `two_site_log` included, not just the
       artefact projection), and so must every claim's `Vec` — defined, value and nbits.
       The indexed side runs twice, in-process and as a chunked task pool, and both must
       agree with the oracle.
  (ii) PLANTED MUTANTS. Each breaks one premise or one piece of bookkeeping and must make
       the differential, or a runtime guard (G1-G5, the chunk tiling, the restore assert,
       the session cache's content key), fail. Fewer kills than plants is a failure: a guard nobody has watched fail is
       decorative.
  (iii) CONTROLS. The unplanted code passes; every committed claim passes G1 and G2; a
       planted predicate passes G1 again once re-rendered from its spec; a ledger rewritten
       between two measurements in one process is seen by the second (the session cache is
       keyed by content, not by path); and a session whose file changed after it was
       planned refuses to load (`StaleInputs`).

The sessions are fixed and small on purpose — the oracle evaluates every claim on every
mutant, which is the cost this whole change exists to avoid — and they are chosen because
they kill every plant (checked here, not assumed: a plant neither kills fails the run).
"""
import contextlib
import copy
import json
import os
import random
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor

from pipeline import perturb

from . import equiv as E
from . import readset

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SESSIONS = ("2026-09-03", "2026-07-24")
ROUND_SESSION = "2026-09-03"
PLANT_CHUNK = 400            # small enough that every plant's run cuts the match family up


def _paths(session):
    from .check_equiv_coverage import hand_ledgers
    d = os.path.join(ROOT, "sessions", session, "report")
    return (os.path.join(d, "facts.json"), hand_ledgers(d),
            os.path.join(d, "claims-generated.json"))


def _capture(module):
    """Wrap `module._search` so each call also records every claim's Vec, in call order."""
    sink = []
    orig = module._search

    def search(gen_codes, hand_codes, gvecs, hvecs, corpus):
        rec = {}
        for (c, _), v in list(zip(gen_codes, gvecs)) + list(zip(hand_codes, hvecs)):
            vv = v if hasattr(v, "defined") else module.Vec.of(v)
            nb = getattr(vv, "nbits", None)
            rec[c["id"]] = (vv.defined, vv.value, len(v) if nb is None else nb)
        sink.append(rec)
        return orig(gen_codes, hand_codes, gvecs, hvecs, corpus)
    return sink, orig, search


def _oracle(session, modes):
    """Run in a worker: the exhaustive reference, its result and every Vec."""
    from . import equiv_reference as R
    facts, hand, gen = _paths(session)
    sink, orig, search = _capture(R)
    R._search = search
    try:
        res = R.measure_modes(facts, hand, generated_path=gen, two_site_modes=modes)
    finally:
        R._search = orig
    return res, sink


def _indexed(session, modes, jobs=1, chunk=E.DEFAULT_CHUNK):
    facts, hand, gen = _paths(session)
    E._SESSIONS.clear()            # a plant may change how a session is built; never reuse one
    sink, orig, search = _capture(E)
    E._search = search
    try:
        res = E.measure_modes(facts, hand, generated_path=gen, two_site_modes=modes,
                              jobs=jobs, chunk=chunk)
    finally:
        E._search = orig
        E._SESSIONS.clear()
    return res, sink


def _diff(got, want):
    """None if identical, else a one-line reason."""
    gres, gvec = got
    wres, wvec = want
    if json.dumps(gres, sort_keys=True) != json.dumps(wres, sort_keys=True):
        modes = [m for m in wres if json.dumps(gres.get(m), sort_keys=True)
                 != json.dumps(wres[m], sort_keys=True)]
        return f"result dict differs in {modes}"
    if len(gvec) != len(wvec):
        return f"{len(gvec)} vector sets against {len(wvec)}"
    for k, (g, w) in enumerate(zip(gvec, wvec)):
        bad = sorted(c for c in w if g.get(c) != w[c])
        if bad or set(g) != set(w):
            return f"mode #{k}: Vec differs for {len(bad)} claim(s), first {bad[:3]}"
    return None


@contextlib.contextmanager
def _patch(obj, name, value):
    old = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, old)


def _drop_label(label):
    orig = readset.key_labels
    return _patch(readset, "key_labels", lambda w, ids: orig(w, ids) - {label})


def _raw_score_key():
    return _patch(readset, "key_labels", lambda w, ids: frozenset(k for _, k, _ in w))


def _readers_drop_one():
    """Drop the first reader of the most-read round FIELD label.

    A field label, not just the most-read label: a field mutant writes that one key and
    nothing else, so the dropped claim is then never evaluated on it. The most-read label
    overall is `matches`, which no mutant writes, so dropping a reader from it is an
    equivalent mutant — the first version of this plant did exactly that and survived.
    """
    orig = readset.build_readers

    def build(keysets):
        r = dict(orig(keysets))
        label = max(sorted(k for k in r if k in E.SCALARS), key=lambda k: len(r[k]))
        r[label] = r[label][1:]
        return r
    return _patch(readset, "build_readers", build)


def _pristine_fill_inverted():
    orig = E.Vec.from_sparse.__func__
    return _patch(E.Vec, "from_sparse",
                  classmethod(lambda cls, n, p, exc: orig(cls, n, not p, exc)))


def _offset_off_by_one():
    return _patch(E, "_move_base", lambda n: 2 + n)


def _drop_last_chunk():
    orig = E._plan_chunks
    return _patch(E, "_plan_chunks",
                  lambda n, chunk: (lambda r: r[:-1] if len(r) > 1 else r)(orig(n, chunk)))


def _restore_disabled():
    @contextlib.contextmanager
    def perturbed(writes):
        for container, key, value in writes:
            container[key] = value
        yield
    return _patch(perturb, "perturbed", perturbed)


# name, what it breaks, the plant
RUN_PLANTS = [
    ("M1", "key_labels drops 'alive' (a round-winner flip's companion write)",
     lambda: _drop_label("alive")),
    ("M2", "key_labels drops 'lifetime'", lambda: _drop_label("lifetime")),
    ("M3", "a score write is labelled with the raw player key, not 'score'", _raw_score_key),
    ("M6", "the reader index drops one claim from its most-read field label", _readers_drop_one),
    ("M7", "the pristine fill uses `not pristine`", _pristine_fill_inverted),
    ("M8", "move exceptions are offset one sample too far", _offset_off_by_one),
    ("M9", "the last chunk of a move family is never run", _drop_last_chunk),
    ("M11", "perturb.perturbed stops restoring the tree", _restore_disabled),
]

AUDIT_PLANTS = [
    ("M4", "a predicate reading a field through `.get('pieces')`",
     "facts['matches'][0]['rounds'][0]['players']['yachi'].get('pieces') > 0"),
    ("M5", "a predicate reading a player dict through `{**r['players']}`",
     "sum(1 for m in facts['matches'] for r in m['rounds'] "
     "if len({**r['players']}) == 2) > 0"),
]


CACHE_SESSION = "2026-07-24"
CACHE_SAMPLES = 200          # a sampled corpus: this control is about the cache, not coverage


def _cache_control():
    """Measure through one temp hand ledger, rewrite it, measure again IN THE SAME PROCESS
    without touching `_SESSIONS`, then measure fresh. None if the second call saw the rewrite
    (equals the fresh one and differs from the first), else the reason.

    The rewrite keeps the PATH, which is the whole point: a cache keyed by path alone answers
    the second call with the first ledger's claims, and this is the control that says so."""
    facts, hand, gen = _paths(CACHE_SESSION)
    claims = [c for p in hand for c in json.load(open(p, encoding="utf-8"))]
    tmp = tempfile.mkdtemp(prefix="equiv-cache-")
    path = os.path.join(tmp, "hand.json")

    def run():
        res = E.measure_modes(facts, [path], generated_path=gen, samples=CACHE_SAMPLES)
        sv = res["single_value"]
        return sorted(sv["covered"] + sv["uncovered"] + sv["untested"])

    try:
        E._SESSIONS.clear()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(claims[:3], fh)
        first = run()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(claims, fh)
        second = run()
        E._SESSIONS.clear()
        fresh = run()
    finally:
        E._SESSIONS.clear()
        shutil.rmtree(tmp, ignore_errors=True)
    if first == fresh:
        return "the rewrite did not change the measured claims, so this control cannot fail"
    if second != fresh:
        return (f"the second call measured {len(second)} hand claims where a fresh one "
                f"measures {len(fresh)} — a stale session was reused")
    return None


def _stale_inputs_control():
    """A session planned under one content digest must refuse to build from different bytes.
    None if `StaleInputs` is raised, else the reason."""
    facts, hand, gen = _paths(CACHE_SESSION)
    tmp = tempfile.mkdtemp(prefix="equiv-stale-")
    path = os.path.join(tmp, "hand.json")
    try:
        shutil.copyfile(hand[0], path)
        key = E._session_key(facts, [path], gen, CACHE_SAMPLES, E.DEFAULT_SEED)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n")                     # same JSON, different bytes
        try:
            E._Session(key)
        except E.StaleInputs:
            return None
        return "a session built from bytes other than the planned ones loaded silently"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _path_only_key():
    """The cache keyed by paths and parameters alone — the defect `_session_key` fixed."""
    return _patch(E, "_digest_of", lambda blobs: "")


def _sparse_unit(rng):
    """Vec.from_sparse(n, pristine, exceptions) == Vec.of(dense), all three values."""
    for n in list(range(0, 20)) + [63, 64, 65, 1000, 4099]:
        for pristine in (True, False):
            for density in (0.0, 0.05, 0.5, 1.0):
                dense = [pristine] * n
                for i in range(n):
                    if rng.random() < density:
                        dense[i] = rng.choice((True, False, None))
                exc = [(i, v) for i, v in enumerate(dense) if v is not pristine]
                if E.Vec.from_sparse(n, pristine, exc) != E.Vec.of(dense):
                    return f"from_sparse != of(dense) at n={n}, pristine={pristine}"
    return None


def run(round_tier=False, jobs=None):
    jobs = jobs or os.cpu_count() or 1
    t0 = time.time()
    planted = killed = 0
    fails = []

    def ok(msg):
        print(f"  ok  {msg}", flush=True)

    def bad(msg):
        print(f"  FAIL {msg}", flush=True)
        fails.append(msg)

    def plant(name, what, reason):
        nonlocal planted, killed
        planted += 1
        if reason:
            killed += 1
            ok(f"{name} killed — {what}: {reason}")
        else:
            bad(f"{name} SURVIVED — {what}: the index would publish this unseen")

    work = [(s, ("match",)) for s in SESSIONS]
    if round_tier:
        work.append((ROUND_SESSION, ("match", "round")))
    pool = ProcessPoolExecutor(max_workers=max(1, min(jobs, len(work))))
    oracle = {w: pool.submit(_oracle, *w) for w in work}

    # (iii) controls that need no oracle
    err = _sparse_unit(random.Random(20261004))
    (ok if err is None else bad)("Vec.from_sparse equals Vec.of on random dense vectors"
                                 + ("" if err is None else f": {err}"))
    from .check_equiv_coverage import hand_ledgers, session_dirs
    measurable, _ = session_dirs(ROOT)
    n = 0
    for _, d in measurable:
        claims = []
        for p in [os.path.join(d, "claims-generated.json")] + hand_ledgers(d):
            with open(p, encoding="utf-8") as fh:
                claims.extend(json.load(fh))
        try:
            E.check_index_premises(claims)
        except readset.IndexUnsound as exc:
            bad(f"control: a committed claim fails G1/G2: {exc}")
        n += len(claims)
    ok(f"control: all {n} committed claims of {len(measurable)} sessions pass G1 and G2")

    err = _cache_control()
    (ok if err is None else bad)("control: a ledger rewritten between two measurements in "
                                 "one process is seen by the second"
                                 + ("" if err is None else f": {err}"))
    err = _stale_inputs_control()
    (ok if err is None else bad)("control: a session whose file changed after planning "
                                 "refuses to load (StaleInputs)"
                                 + ("" if err is None else f": {err}"))
    with _path_only_key():
        reason = _cache_control()
    plant("M12", "the session cache is keyed by path, not content",
          f"the rewrite control — {reason}" if reason else None)

    # (ii) plants that need no oracle: the grammar guard and G1
    for name, what, src in AUDIT_PLANTS:
        try:
            readset.audit({"id": name, "python_check": src})
            reason = None
        except readset.IndexUnsound as exc:
            reason = f"G2 — {str(exc).split(':', 2)[1].strip()}"
        plant(name, what, reason)
    facts_path, hand, gen = _paths(SESSIONS[0])
    with open(gen, encoding="utf-8") as fh:
        claim = copy.deepcopy(json.load(fh)[0])
    claim["python_check"] = "(" + claim["python_check"] + ")"     # same verdict, new text
    try:
        E.check_index_premises([claim])
        reason = None
    except readset.IndexUnsound:
        reason = "G1 — python_check is not spec.to_python(spec)"
    plant("M10", "a hand-reformatted predicate that no longer matches its spec", reason)
    from .spec import to_python
    claim["python_check"] = to_python(claim["spec"])
    try:
        E.check_index_premises([claim])
        ok("control: the same predicate passes G1 again once re-rendered from its spec")
    except readset.IndexUnsound as exc:
        bad(f"control: a re-rendered predicate fails G1: {exc}")

    # (i) the differential, then (ii) the plants that need it
    want = {w: f.result() for w, f in oracle.items()}
    pool.shutdown()
    for (s, modes), w in want.items():
        for label, kw in (("in-process", {"jobs": 1}),
                          (f"{jobs} workers, chunked", {"jobs": jobs, "chunk": PLANT_CHUNK})):
            reason = _diff(_indexed(s, modes, **kw), w)
            if reason is None:
                ok(f"differential: {s} {'+'.join(('single_value',) + modes)} ({label}) is "
                   f"identical to the exhaustive oracle — whole result dict and every Vec")
            else:
                bad(f"differential: {s} ({label}) differs from the oracle: {reason}")

    # Each run-plant is tried twice: with every guard, and again with G5's shadow sample
    # switched off. A kill needs only the first; the second is printed so the record says
    # whether the differential ALONE would have caught it — G5 is a tripwire, and a plant
    # that only the tripwire catches is one a different stratum boundary could miss.
    for name, what, make in RUN_PLANTS:
        found = {}
        for g5 in (True, False):
            reason = None
            for s in SESSIONS:
                try:
                    with make(), contextlib.ExitStack() as stack:
                        if not g5:
                            stack.enter_context(
                                _patch(E, "_first_per_stratum", lambda *a, **k: set()))
                        got = _indexed(s, ("match",), jobs=1, chunk=PLANT_CHUNK)
                    why = _diff(got, want[(s, ("match",))])
                    if why:
                        reason = f"differential on {s}: {why}"
                except (readset.IndexUnsound, AssertionError) as exc:
                    reason = f"{type(exc).__name__} on {s}: {str(exc).splitlines()[0][:100]}"
                if reason:
                    break
            found[g5] = reason
        if found[True]:
            print(f"      {name} without G5: {found[False] or 'SURVIVES — only the tripwire sees it'}")
        plant(name, what, found[True])

    print(f"\nplanted {planted}, killed {killed}; {len(fails)} failure(s) "
          f"({time.time() - t0:.0f} s)")
    return 1 if fails or killed < planted else 0
