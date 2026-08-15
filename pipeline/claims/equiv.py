"""Measure how much of a hand-written ledger the generated families already cover.

    python3 -m pipeline.claims.equiv sessions/2026-07-24/report/facts.json \
        --hand sessions/2026-07-24/report/claims-narrative.json \
               sessions/2026-07-24/report/claims-coaching.json

Why this is not a string comparison: every predicate in every ledger is True on the
real data, so evaluating them there tells you nothing about whether two predicates pin
the same fact. Instead we perturb the dataset many times and compare behaviour.

A hand claim H counts as covered by a generated claim G when, across every mutant in the
corpus, G being true forces H to be true (G implies H), and G is not trivially
always-true. If that holds, proving G gives you H for free.

EXHAUSTIVE means both halves of "which value, changed how": every mutation *site*
(`mutation_sites`) and, at each site, every perturbation *kind* (`_bumps` — zero, double,
halve, a third either way, a twentieth either way; both signs for a match score),
de-duped where two kinds land on the same value.

It used to mean only the first half. One kind was DRAWN per site, so the published figure
moved with `--seed`: 2026-07-22 read 45/53 = 85% at the committed seed, 46/53 = 87% at
seed 3, 43/52 = 83% at seed 42 — 82.7-86.8% over twelve of them (the committed one, 1-10
and 42), with the *denominator* moving too (51-53), because which claims are falsifiable
at all depends on which mutants were drawn. A figure that moves with an argument nobody
varies reads as a property of the data. Enumerating instead costs ~5x the mutants and ~5x
the wall clock (7 019 sites, 34 779 mutants, 13.9 s to 69.2 s on that session), and
2026-07-22 settles at 43/53 = 81%.

What is still not exhaustive, and is not claimed to be: pairs. Two predicates can differ
only under a simultaneous change to two values, so this remains no proof of equivalence;
claims that no mutation can falsify are reported separately rather than counted as
covered; `--two-site` below attacks one family of pairs under a bound of its own; and
`--samples`, off by default, is the one path that still draws — it subsamples the site
list, and is the only thing `--seed` governs.

`--two-site` adds the second family, and it exists because that caveat decided a headline
number. A *windowed* claim ("yachi's attack per piece fell after match 2") draws on the
same rounds as the session total that is meant to imply it, so no single-value change can
falsify one without falsifying the other, and 2026-07-28 duly reported 100%. What breaks
the tie is a **value-preserving move**: take half of one round's `pieces` and add it to
another round's, and every session total over that field is unchanged while every window
sum that separates the two rounds moves. See `move_sites` for the bound and for why the
delta is a *half* rather than the whole value.
"""
import argparse
import json
import random
import re

from pipeline import perturb

SCALARS = [
    "apm_x1000", "pps_x1000", "vs_x1000", "lifetime", "maxspike", "topcombo",
    "topbtb", "tspins", "pieces", "garbage_attack", "garbage_cleared",
    "finesse_faults", "finesse_perfect", "kills", "holds", "lines", "inputs",
    "garbagesent", "garbagereceived",
]
CLEARS = ["singles", "doubles", "triples", "quads", "tspin_singles",
          "tspin_doubles", "tspin_triples", "mini_tspin_singles",
          "mini_tspin_doubles", "allclear"]


def mutation_sites(facts):
    """Every place a single-value mutation can be applied."""
    sites = []
    for mi, m in enumerate(facts["matches"]):
        sites.append(("match_winner", mi))
        for pl in facts["players"]:
            sites.append(("score", mi, pl))
            for f in ("apm_x1000", "pps_x1000", "vs_x1000", "garbagesent",
                      "garbagereceived", "kills"):
                if f in m["leaderboard"][pl]:
                    sites.append(("lb", mi, pl, f))
        for ri, r in enumerate(m["rounds"]):
            sites.append(("round_winner", mi, ri))
            for pl in facts["players"]:
                p = r["players"][pl]
                for f in SCALARS:
                    if f in p:
                        sites.append(("field", mi, ri, pl, f))
                for f in CLEARS:
                    if f in p.get("clears", {}):
                        sites.append(("clear", mi, ri, pl, f))
                for gi in range(len(p.get("garbage_events", []))):
                    sites.append(("ge", mi, ri, pl, gi))
    return sites


def site_mutants(facts, site):
    """Every mutant at one site, as lists of `(container, key, value)` writes.

    Was `mutation_writes(facts, site, rng)`, which returned ONE mutant per site because it
    drew a perturbation kind from `rng`. That draw is what made the tool's headline figure
    depend on `--seed` (see the module note), so it is gone: this returns the whole fan-out
    — one write-list per value in `_bumps`, or per sign for a score, or the single flip for
    a winner — and nothing here consumes randomness. The seven branches are the seven site
    kinds `mutation_sites` emits, unchanged.

    Each mutant is a list because a write can need a companion: flipping a round's winner
    must also flip both players' `alive`. `pipeline.perturb.perturbed` applies a list in
    place and undoes it in reverse, so a mutant exists for a few hundred nanoseconds rather
    than the twelve milliseconds a `deepcopy` of `facts` used to cost. See that module for
    what the trade gives up and which assertion buys it back.

    Read the values BEFORE any perturbation is applied: each write's new value is computed
    from the datum's current one, so building the corpus lazily inside the sweep would read
    a slot some earlier mutant had not yet restored.
    """
    other = {facts["players"][0]: facts["players"][1],
             facts["players"][1]: facts["players"][0]}
    kind = site[0]
    if kind == "match_winner":
        _, mi = site
        m = facts["matches"][mi]
        return [[(m, "winner", other[m["winner"]])]]
    if kind == "score":
        _, mi, pl = site
        s = facts["matches"][mi]["score"]
        return [[(s, pl, s[pl] + d)] for d in (-1, 1)]
    if kind == "lb":
        _, mi, pl, f = site
        lb = facts["matches"][mi]["leaderboard"][pl]
        return [[(lb, f, v)] for v in _bumps(lb[f])]
    if kind == "round_winner":
        _, mi, ri = site
        r = facts["matches"][mi]["rounds"][ri]
        new = other[r["winner"]]
        # `alive` is derived from the winner, so flipping one without the other would
        # build a mutant no extractor could ever produce.
        return [[(r, "winner", new)]
                + [(r["players"][pl], "alive", pl == new) for pl in facts["players"]]]
    if kind == "field":
        _, mi, ri, pl, f = site
        p = facts["matches"][mi]["rounds"][ri]["players"][pl]
        return [[(p, f, v)] for v in _bumps(p[f])]
    if kind == "clear":
        _, mi, ri, pl, f = site
        c = facts["matches"][mi]["rounds"][ri]["players"][pl]["clears"]
        return [[(c, f, v)] for v in _bumps(c[f])]
    if kind == "ge":
        _, mi, ri, pl, gi = site
        g = facts["matches"][mi]["rounds"][ri]["players"][pl]["garbage_events"][gi]
        return [[(g, "amt", v)] for v in _bumps(g["amt"])]
    raise AssertionError(f"unknown mutation site kind {kind!r}")


def read_fields(claims):
    """The round-level fields some predicate actually reads, and the ones it never does.

    Every field access in a rendered predicate is a literal string key
    (`d['lifetime']`, `p['clears']['quads']`); the only `.values()` / `.items()` calls in
    any ledger are over `r['players']` and `m['score']`, never over a round's stat dict.
    So a field whose name does not appear as a token anywhere in the sources cannot be
    read, and moving it is provably a no-op mutant. `\\b<word>\\b` over `\\w+` is a token
    boundary, which is why one `findall` answers the same question as one `re.search` per
    name — the same argument `check_dead_consts` makes.

    Returns `(scalars, clears, dropped)`. `dropped` is printed, never discarded silently.
    """
    toks = set()
    for c in claims:
        toks.update(re.findall(r"\w+", c["python_check"]))
    scalars = [f for f in SCALARS if f in toks]
    clears = [f for f in CLEARS if f in toks]
    dropped = ([f for f in SCALARS if f not in toks]
               + [f for f in CLEARS if f not in toks])
    return scalars, clears, dropped


def _round_stats(facts, kind, mi, ri, pl):
    p = facts["matches"][mi]["rounds"][ri]["players"][pl]
    return p if kind == "field" else p.get("clears", {})


def move_sites(facts, claims, granularity, log=None):
    """Ordered `(source, target)` pairs for value-preserving two-site moves.

    A move is `source[f] -= d; target[f] += d`, so **any sum over both sites is
    unchanged** while a sum over one of them is not. That is the whole point: a generated
    session total stays true by construction, and a windowed hand claim that the total was
    supposed to imply is free to flip.

    THE BOUND, and what it therefore cannot see
    -------------------------------------------
    Naive two-site is the single-site corpus squared — 5 453^2 for 2026-07-28, which does
    not finish. Three restrictions cut it, each with a reason rather than a cap:

    * **same field, same player.** A move between two different fields, or between two
      players, preserves no total any claim takes, so it is an arbitrary two-value change
      and not a *move* at all. Nothing in the ledger sums one player's `pieces` together
      with the other's.
    * **different matches.** Every window in the algebra is a contiguous range of
      *matches* (`spec.rounds_in_range` filters `lo <= mi < hi`), so two rounds of the same
      match are on the same side of every window there is. A within-match move therefore
      changes no window sum and no session total — it flips only per-round claims, which
      single-site mutation already falsifies far more directly.
    * **fields some predicate reads** (`read_fields`).

    One family is deliberately outside all of that: `garbage_events[].amt`, which
    `mutation_sites` does perturb one at a time. `sum_ge` is only ever rendered over the
    whole session (`sum_ge(pl)`) or over one named round (`sum_ge(pl, mi, ri)`) — the
    algebra has no windowed variant of it — so there is no window/total pair for a move to
    drive apart, which is the only thing this family exists to find. If a windowed
    `sum_ge` is ever added, this exclusion stops being sound.

    `granularity` then chooses how finely the surviving space is enumerated:

    * ``"round"`` — every ordered cross-match pair of rounds. Exhaustive within the bound.
    * ``"match"`` — one pair per (source match, target match, player, field): the source
      match's largest-valued round, moved into the target match's smallest-valued one.
      For a *windowed* claim this loses nothing at all, since only the two matches enter a
      window sum, and taking the largest value maximises the shift. What it cannot see is
      any implication that fails only for a move touching some *other* round — i.e. one
      that turns on per-round granularity (a record, a per-round threshold, a specific
      round's comparison). Those are exactly the claims single-site mutation is good at,
      which is why this is the cheap setting rather than the only one.

      **`match`'s moves are a SUBSET of `round`'s**, which is why its figure is an upper
      bound by construction and not by luck: the one pair it keeps per (source match,
      target match, player, field) is one of the pairs `round` enumerates, and an
      implication that survives more mutants survives fewer. The bound is on the
      *implications*, not on the fraction — extra mutants also make more claims
      falsifiable, which moves the denominator — so re-run `round` before publishing a
      percentage.

      **What the extra moves buy is measured, and against the exhaustive single-value
      family it is less than it was against the seeded one.** 2026-07-28: identical
      verdict, 6/10 and the same covered set, from 2 289 moves and 32 s against 137 970
      moves and 179 s (total wall, single-value sweep included). 2026-07-22: also
      identical, 42/53 either way, from 3 690 moves and 79 s against 217 480 and 517 s —
      the finer granularity's only visible effect there is that R013 stops behaving
      *identically* to G054, some move separating two predicates no single-value mutation
      tells apart, while still being implied by it. Both granularities do move the
      single-value figure on 2026-07-22, 43/53 to 42/53: R021 names one decider round, and
      the pair that implied it (avg PPS + the decider family) survives a redistribution
      that the round-level claim does not.

      **Why the two granularities used to disagree there, and no longer do.** Under the
      seeded family the figures were 44/53 at `match` and 42/53 at `round` — the finer
      granularity BREAKING two implications the coarser one left standing, which is what
      the subset argument above predicts and the opposite of what this paragraph said for
      as long as the numbers sat in it. The two were C007 (a marathon round) and C024 (one
      round's peak VS), and they are exactly the two the exhaustive single-value family now
      falsifies on its own. A gap that closes when the cheap family stops sampling was
      never a fact about granularity.

    The delta is HALF the source (`d = max(1, source[f] // 2)`). Two constraints pull
    against each other here and half is where they meet. `_bumps`'s argument says a gentle
    move never shifts an aggregate comparison, so a claim nothing falsifies reads as
    implied by anything — that pushes the delta up. But moving the *whole* value leaves
    the source at 0, and a round with `pieces=0, lines=48` is not a dataset any extractor
    can emit, so a claim falsified only by that is not evidence — that pushes it down.
    Half satisfies both, and is also literally the published example: CLAUDE.md's
    "move 120 pieces from a match-3 round to a match-1 round" is a redistribution between
    two live rounds. Sources below 2 are dropped — halving them would be the deletion the
    rule exists to avoid — and counted in `log`.
    """
    scalars, clears, dropped = read_fields(claims)
    fields = [("field", f) for f in scalars] + [("clear", f) for f in clears]
    nm = len(facts["matches"])
    rounds = {mi: range(len(facts["matches"][mi]["rounds"])) for mi in range(nm)}

    sites, zero, missing = [], 0, 0
    for pl in facts["players"]:
        for kind, f in fields:
            # value per (mi, ri); None where the field is absent from that round
            val = {}
            for mi in range(nm):
                for ri in rounds[mi]:
                    val[(mi, ri)] = _round_stats(facts, kind, mi, ri, pl).get(f)
            live = {mi: [(mi, ri) for ri in rounds[mi] if val[(mi, ri)] is not None]
                    for mi in range(nm)}
            # counted once per slot, not once per (mi, mj) pair — an inflated "dropped"
            # figure reads as a bigger hole than the one that exists
            missing += sum(len(rounds[mi]) - len(live[mi]) for mi in range(nm))
            for mi in range(nm):
                for mj in range(nm):
                    if mi == mj:
                        continue
                    src, tgt = live[mi], live[mj]
                    if not src or not tgt:
                        continue
                    if granularity == "match":
                        pairs = [(max(src, key=lambda k: (val[k], -k[1])),
                                  min(tgt, key=lambda k: (val[k], k[1])))]
                    else:
                        pairs = [(a, b) for a in src for b in tgt]
                    for a, b in pairs:
                        # `< 2` and not `== 0`: the delta is half the source, so a source
                        # of 1 would halve to 1 and leave the round at 0 — the degenerate
                        # deletion this family exists not to produce.
                        if not val[a] or val[a] < 2:
                            zero += 1
                            continue
                        sites.append(("move", kind, a, b, pl, f))
    if log is not None:
        log.update(dropped_fields=dropped, zero_source=zero, absent_field=missing)
    return sites


def move_writes(facts, site):
    """The two writes that realise one value-preserving move.

    No `rng` argument, deliberately: the delta is a fixed function of the source value, so
    this family draws nothing. Neither does the single-value family any more, so the two
    are independent in the strong sense — the single-value corpus is the same list of
    mutants whether or not `--two-site` is given, and a granularity comparison is a
    comparison of the moves alone.
    """
    _, kind, (mia, ria), (mib, rib), pl, f = site
    ca = _round_stats(facts, kind, mia, ria, pl)
    cb = _round_stats(facts, kind, mib, rib, pl)
    va, vb = ca[f], cb[f]
    d = max(1, va // 2)
    # `d` is HALF the source, not all of it, and that is the difference between a
    # redistribution and a deletion. An earlier revision used `d = va`, which left every
    # source at exactly 0 — 145 615 of 145 615 moves — so the family's own evidence was
    # rounds like `pieces=0, lines=48, lifetime=65591`. The claim this metric exists to
    # test is CLAUDE.md's "move 120 pieces from a match-3 round to a match-1 round": a
    # redistribution between two live rounds, which a half-move expresses and a zeroing
    # does not.
    #
    # There is no value-preservation assert here any more, deliberately. The old one read
    # `(va - d) + (vb + d) == va + vb`, which is an integer identity for EVERY d — it
    # could not fail for any input, so it was decorative by this repo's own rule.
    # Preservation is not something this function can check anyway: it holds because `a`
    # and `b` are distinct rounds of the SAME (player, field) — guaranteed by the site
    # constructor's `mi != mj` — so whatever leaves `a` lands in `b` and every sum taken
    # over both is unchanged. That is an argument from the constructor, not a runtime
    # property of one write, and writing it as an assert only made it look checked.
    #
    # This guard IS load-bearing: it constrains the delta rule three lines up. No *data*
    # can reach it — sources with `va < 2` are dropped before a site is built — but an
    # edit to that rule is exactly what it catches (set `d = va` and it fires on the
    # first move). It guards the code, which is where the defect was.
    assert 1 <= d <= va - 1, f"delta {d} does not leave the source live (va={va})"
    return [(ca, f, va - d), (cb, f, vb + d)]


def _bumps(v):
    """Every perturbation of one datum, aggressive and in a fixed order.

    Gentle nudges are useless here: a +-1 change to one round out of fifty never flips
    an aggregate comparison, so the claim stays true under every mutation and then
    looks "implied" by anything at all. Mutations have to be big enough to move totals —
    hence zero, double, halve, and a third and a twentieth of the value in both
    directions. What is new is that every kind is TRIED rather than one being drawn; a
    drawn kind made the coverage figure a function of `--seed`, which is a knob, not a
    finding.

    Both directions of both offsets, and not just the direction that shrinks: a great many
    of these claims are one-sided ("yachi's KPP is lower"), so a mutant that only ever
    moves a datum one way cannot falsify half of them. That is the same argument
    `check_smt --mutate` makes for escalating a measurement both ways.

    De-duped, which is a cost saving and not a semantic choice: at `v = 0` five of the
    seven collapse onto 0 or 1, and a repeated value is a repeated verdict — the same bit
    in every truth vector, so no implication can turn on it. Measured rather than argued:
    keeping the coincident values changes no covered, uncovered, untested, identical or
    trivial list on either 2026-07-24 (22 059 mutants against 28 596, 1.30x) or
    2026-08-09 (22 309 against 29 323, 1.31x). A candidate equal to `v` is dropped by the
    same rule and is not a saving but a correctness point: it is not a mutation. The
    de-dupe can never empty a site out: every datum here is non-negative, so `2v + 1`
    differs from `v` always, and each site keeps at least that one mutant.
    """
    out = [0, v * 2 + 1, v // 2]
    for sign in (-1, 1):
        out.append(max(0, v + sign * max(1, abs(v) // 3)))
    for sign in (-1, 1):
        out.append(max(0, v + sign * max(1, abs(v) // 20)))
    seen, uniq = {v}, []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


class Vec:
    """A three-valued truth vector as two bitmaps, one bit per mutant.

    `defined` bit i is set when claim evaluation produced a verdict on sample i;
    `value` bit i is set when that verdict was True. `value` is always a subset of
    `defined`, so an undefined sample reads as 0 in both and "defined and False" is
    exactly `defined ^ value`.

    Why not a list of True/False/None: the pair-coverage search below tries every PAIR
    of generated claims against each uncovered hand claim — O(|hand| x |gen|^2) vector
    operations, and on 2026-07-22 that was 167 million interpreter steps inside one
    generator expression, the single hottest line in the tool. That figure was measured
    over the 7 020-sample seeded corpus; the cost is linear in the sample count, and the
    exhaustive corpus is 34 780, so the list version would now be some 800 million.
    Python's ints are arbitrary-precision bitmaps, so the same conjunction becomes a
    couple of `&`s over ~544 machine words. This is the word-parallel trick behind
    Shift-Or approximate matching (Baeza-Yates & Gonnet, CACM 35(10), 1992) and bitset
    dataflow analysis; nothing about the answers changes, only how many operations
    compute them.
    """
    __slots__ = ("defined", "value")

    def __init__(self, defined, value):
        self.defined, self.value = defined, value

    @classmethod
    def of(cls, verdicts):
        """Pack a list of True/False/None, sample 0 in bit 0.

        Built from a binary string rather than by `|= 1 << i` in a loop: shifting into a
        growing int is O(n) per bit and so O(n^2) overall, which for a corpus of tens of
        thousands of samples (34 780 on 2026-07-22) costs more than it saves.
        """
        d = "".join("1" if v is not None else "0" for v in reversed(verdicts))
        b = "".join("1" if v else "0" for v in reversed(verdicts))
        return cls(int(d, 2), int(b, 2))

    def falsified(self):
        """Was this claim False on at least one sample? (`any(x is False for x in v)`)"""
        return (self.defined ^ self.value) != 0

    def __and__(self, other):
        """Pointwise conjunction, undefined wherever either side is."""
        d = self.defined & other.defined
        return Vec(d, self.value & other.value & d)

    def __eq__(self, other):
        return self.defined == other.defined and self.value == other.value


def implies(g, h):
    """g -> h on every sample where both evaluated.

    A violation is a sample where g is True and h is False. `h.defined ^ h.value` is
    exactly h's False bits, and `g.value` is inside `g.defined`, so their intersection is
    already restricted to samples both sides decided — no separate mask is needed.

    `seen` in the list version required at least one commonly-decided sample, so a pair
    that never overlaps is not an implication. `g.defined & h.defined` is that condition.
    """
    if not (g.defined & h.defined):
        return False
    return (g.value & (h.defined ^ h.value)) == 0


DEFAULT_SEED = 20260725

GRANULARITIES = ("match", "round")


def _search(gen_codes, hand_codes, gvecs, hvecs, corpus):
    """The implication search over one pair of truth-vector sets, and the result it shapes.

    Split out of `measure` so that every mode `measure_modes` reports goes through the
    same search. The vectors are the only thing that distinguishes one mode from another:
    a two-site mode's vectors are the single-value ones with that family's moves appended,
    so if this function were duplicated per mode the modes could disagree for a reason
    that had nothing to do with the mutants.

    The length assert is the ONLY thing standing between a mode and the family that ran
    before it, and it is here rather than in prose because the obvious check does not
    work. Alias `measure_modes`' per-mode vector copies instead of copying them and every
    later mode is measured over its predecessor's moves too — yet on 2026-08-09 that
    mutant changes NO verdict in any of the three modes (measured, not assumed: the
    aliased corpus is a superset, and coverage happens not to move on it). A leak that
    the results cannot show is one the results cannot gate, so the corpus is checked by
    size: one pristine sample, plus every mutant, plus this mode's moves, and nothing
    else. The same mutant dies here immediately.
    """
    expect = 1 + corpus["mutants"] + corpus["moves"]
    wrong = [len(v) for v in list(gvecs) + list(hvecs) if len(v) != expect]
    assert not wrong, (
        f"a truth vector carries {wrong[0]} samples, not the {expect} this mode's corpus "
        f"has ({corpus['mutants']} mutants + {corpus['moves']} moves + the pristine "
        f"dataset) — the vectors of another mode have leaked into this one")
    gtriples = []
    for (c, _), v in zip(gen_codes, gvecs):
        vt = Vec.of(v)
        gtriples.append((c, vt, vt.falsified()))

    trivial = sorted(c["id"] for c, _, nt in gtriples if not nt)

    # A claim no mutation falsifies can imply nothing useful, and both loops below skipped
    # it. Filtering once keeps the quadratic pair search off them entirely.
    live = [(c, v) for c, v, nt in gtriples if nt]

    covered, uncovered, untested, identical, detail = [], [], [], [], {}
    for (h, _), v in zip(hand_codes, hvecs):
        hv = Vec.of(v)
        if not hv.falsified():
            untested.append(h["id"])
            continue
        exact = next((c for c, gv in live if gv == hv), None)
        impl = exact or next((c for c, gv in live if implies(gv, hv)), None)
        if impl is None:
            # A hand claim often bundles two facts ("more quads, fewer T-spins").
            # The ledger still carries it if a PAIR of generated claims does, so try
            # conjunctions of two before declaring it uncovered.
            for i, (c1, v1) in enumerate(live):
                for c2, v2 in live[i + 1:]:
                    if implies(v1 & v2, hv):
                        impl = {"id": f"{c1['id']}+{c2['id']}",
                                "family": f"{c1['family']} + {c2['family']}"}
                        break
                if impl:
                    break
        if impl:
            covered.append(h["id"])
            if exact is not None:
                identical.append(h["id"])
            detail[h["id"]] = {"implied_by": impl["id"], "family": impl["family"],
                               "identical": exact is not None}
        else:
            uncovered.append(h["id"])
            detail[h["id"]] = {"implied_by": None, "family": None, "identical": False,
                               "category": h.get("category", "?"),
                               "gloss": h["english_gloss"]}

    return {"sites": corpus["sites"], "mutants": corpus["mutants"],
            "moves": corpus["moves"],
            "covered": sorted(covered), "uncovered": sorted(uncovered),
            "untested": sorted(untested), "identical": sorted(identical),
            "trivial_generated": trivial, "detail": detail,
            "two_site_log": corpus["two_site_log"]}


def measure_modes(facts_path, hand_paths, generated_path=None, two_site_modes=(),
                  samples=0, seed=DEFAULT_SEED, progress=None):
    """Measure several granularities from ONE single-value sweep.

    Returns ``{'single_value': {...}, 'two_site_match': {...}, 'two_site_round': {...}}``
    with only the requested modes present besides `single_value`. Each value has the same
    shape `measure` returns, and `measure` is one call to this with one mode, so there is
    a single implementation and the two cannot drift.

    WHY THE SWEEP CAN BE SHARED
    ---------------------------
    A mode is not a different measurement of the same corpus — it is the single-value
    corpus with a family of moves APPENDED. `move_writes` draws nothing and `site_mutants`
    draws nothing, so the single-value mutants are a pure function of the dataset, and the
    same list of verdicts prefixes every mode. Recomputing it per mode is recomputing an
    identical answer: ~230 s across the six sessions, against ~20 s for all the match
    moves.

    WHAT THAT RISKS, AND THE SHAPE OF THE GUARD
    -------------------------------------------
    Truth vectors are accumulating state, which is exactly the kind of thing that leaks
    between phases: append a family's verdicts to the shared lists rather than to a copy
    and the *next* mode is measured over both families, silently reporting a `round`
    number under a `match` label. So each mode gets its own `list(v)` copies and the
    shared vectors are never appended to after the sweep.

    Two things check that, and the weaker one is the one that looks convincing.
    `measure_modes(..., ('match', 'round'))` returns per-mode results byte-identical to
    three separate `measure()` calls on 2026-08-09 and 2026-07-24 — which says the sharing
    is behaviour-preserving, but does NOT gate the copy: replacing it with an alias leaves
    all three modes' results unchanged on 2026-08-09, because the leaked corpus is a
    superset and no implication happens to break on the extra moves. `_search`'s length
    assert is what actually kills that mutant. A guard whose only evidence is an
    equivalence that survives its removal is decorative.

    `facts` itself is shared too, and `perturb.unchanged` is asserted after the sweep and
    after each family, so a mode never starts from a tree a previous mode left dirty.
    """
    say = progress or (lambda *_: None)
    bad = [g for g in two_site_modes if g not in GRANULARITIES]
    if bad:
        # `move_sites` branches on `granularity == "match"` and treats everything else as
        # `round`, so a typo would silently return the expensive granularity under the
        # cheap one's name. Naming it is the whole difference between a bound and a bug.
        raise ValueError(f"unknown two-site granularity {bad}, expected {GRANULARITIES}")

    with open(facts_path, encoding="utf-8") as fh:
        facts = json.load(fh)

    if generated_path:
        with open(generated_path, encoding="utf-8") as fh:
            gen = json.load(fh)
    else:
        from .build_claims import generate, render
        gen = render(generate(facts))

    hand = []
    for path in hand_paths:
        with open(path, encoding="utf-8") as fh:
            hand.extend(json.load(fh))

    sites = mutation_sites(facts)
    n_sites = len(sites)
    if samples and samples < n_sites:
        # The only draw left in the tool, and the only thing `seed` governs.
        random.Random(seed).shuffle(sites)
        sites = sites[:samples]
    # Built before the sweep, not inside it: every new value is a function of the datum's
    # CURRENT value, and inside the sweep a slot may be one an earlier mutant has restored
    # only moments ago. Up front, every read is of the pristine tree.
    mutants = [w for site in sites for w in site_mutants(facts, site)]
    if len(sites) < n_sites:
        note = (f"{len(sites)} of {n_sites} single-value mutation sites, sampled with "
                f"--seed {seed}; {len(mutants)} mutants (every kind at each sampled site)")
    else:
        note = (f"all {n_sites} single-value mutation sites, {len(mutants)} mutants "
                f"(every perturbation kind at every site, exhaustive)")
    say(f"mutation corpus: {note}")

    gen_codes = [(c, compile(c["python_check"], "<gen>", "eval")) for c in gen]
    hand_codes = [(h, compile(h["python_check"], "<hand>", "eval")) for h in hand]

    # Mutate `facts` in place, evaluate every claim, undo. Nothing is copied and nothing
    # is held: the mutant exists only for the duration of the `with` block.
    gvecs = [[] for _ in gen_codes]
    hvecs = [[] for _ in hand_codes]

    def evaluate(dataset, gv, hv):
        env = {"__builtins__": __builtins__}
        for i, (_, code) in enumerate(gen_codes):
            try:
                gv[i].append(bool(eval(code, env, {"facts": dataset})))
            except Exception:            # noqa: BLE001 - mutation broke an index
                gv[i].append(None)
        for i, (_, code) in enumerate(hand_codes):
            try:
                hv[i].append(bool(eval(code, env, {"facts": dataset})))
            except Exception:            # noqa: BLE001
                hv[i].append(None)

    evaluate(facts, gvecs, hvecs)
    pristine = perturb.fingerprint(facts)
    for n, writes in enumerate(mutants, 1):
        with perturb.perturbed(writes):
            evaluate(facts, gvecs, hvecs)
        if n % 2000 == 0:
            say(f"  ... {n}/{len(mutants)} mutants evaluated")
    # The one thing deepcopy gave for free. A restore that misses a single site leaves
    # every later mutant on a wrong baseline and still prints a plausible coverage
    # figure, so this is checked rather than assumed.
    assert perturb.unchanged(facts, pristine), \
        "the mutation sweep did not restore facts — coverage below would be measured " \
        "against a corrupted baseline"

    out = {"single_value": _search(gen_codes, hand_codes, gvecs, hvecs,
                                   {"sites": len(sites), "mutants": len(mutants),
                                    "moves": 0, "two_site_log": None})}

    for gran in two_site_modes:
        log = {}
        moves = move_sites(facts, gen + hand, gran, log)
        say(f"two-site corpus: {len(moves)} value-preserving moves "
            f"({gran} granularity)")
        # Everything the bound threw away, named. A cap nobody can see is worse than a
        # smaller one everybody can.
        say(f"  fields never read by any predicate, so not moved: "
            f"{log['dropped_fields'] or 'none'}")
        say(f"  moves skipped because the source was too small to split (<2): "
            f"{log['zero_source']}")
        say(f"  round/field slots absent from the data: {log['absent_field']}")
        say("  not enumerated by the bound: moves between two rounds of the SAME "
            "match (no window and no total can see one), between different fields, "
            "and between the two players")
        if gran == "match":
            say("  not enumerated at this granularity: moves out of any round but the "
                "source match's largest, or into any but the target match's smallest "
                "— so a claim that turns on WHICH round is touched is out of scope")
        # Copies, not the shared lists: see the module note above on what leaks otherwise.
        gv = [list(v) for v in gvecs]
        hv = [list(v) for v in hvecs]
        for n, site in enumerate(moves, 1):
            with perturb.perturbed(move_writes(facts, site)):
                evaluate(facts, gv, hv)
            if n % 2000 == 0:
                say(f"  ... {n}/{len(moves)} moves evaluated")
        assert perturb.unchanged(facts, pristine), \
            "the two-site sweep did not restore facts — coverage below would be " \
            "measured against a corrupted baseline"
        out[f"two_site_{gran}"] = _search(gen_codes, hand_codes, gv, hv,
                                          {"sites": len(sites), "mutants": len(mutants),
                                           "moves": len(moves), "two_site_log": log})

    return out


def measure(facts_path, hand_paths, generated_path=None, two_site=None,
            samples=0, seed=DEFAULT_SEED, progress=None):
    """Measure hand-claim coverage. `two_site` is None | 'match' | 'round'.

    One mode of `measure_modes`, and nothing else — a caller wanting several granularities
    should call that directly rather than this three times, since the single-value sweep
    is the expensive part and it is the same sweep for every mode.

    Returns a dict with sorted lists and NO percentages::

        {'sites': int, 'mutants': int, 'moves': int,
         'covered': [claim_id, ...], 'uncovered': [...], 'untested': [...],
         'identical': [...], 'trivial_generated': [...],
         'detail': {claim_id: {...}}, 'two_site_log': {...} | None}

    Ids rather than claim objects, and sorted, so a caller diffing two runs gets a stable
    answer that does not move with ledger order. No percentages, because the denominator
    is the interesting part: `covered + uncovered` is the *testable* set and `untested` is
    the rest, and a caller that wants a rate has to decide which it is quoting — 08-09 is
    9/11 over eleven claims, and a bare 82% hides that. `identical` is a subset of
    `covered`: those hand claims whose truth vector equals some generated claim's exactly.
    `trivial_generated` names generated claims no mutant falsified, which imply nothing
    and are excluded from the search.

    `detail` carries what the lists cannot — which generated claim (or pair) implied each
    covered claim, and the category and gloss of each uncovered one — so the CLI's output
    comes out of this function's answer rather than out of a second traversal.

    `progress` is called with each line the CLI prints during the sweep; leave it None to
    run silently.
    """
    if two_site in ("off", ""):
        two_site = None
    modes = measure_modes(facts_path, hand_paths, generated_path=generated_path,
                          two_site_modes=(two_site,) if two_site else (),
                          samples=samples, seed=seed, progress=progress)
    return modes[f"two_site_{two_site}"] if two_site else modes["single_value"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("facts")
    ap.add_argument("--hand", nargs="+", required=True, help="hand-written ledgers")
    ap.add_argument("--generated", help="generated ledger (default: build it now)")
    ap.add_argument("--samples", type=int, default=0,
                    help="subsample the mutation SITES (0 = every site, the default). "
                         "Every perturbation kind is still tried at each site that "
                         "survives the draw; this is the only sampled path in the tool.")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED,
                    help="seeds the --samples draw and nothing else — with --samples 0, "
                         "the default, the output is byte-identical for every seed")
    ap.add_argument("--two-site", choices=["off", "match", "round"], default="off",
                    help="add value-preserving two-site moves (see move_sites for the "
                         "bound). 'match' is one move per match pair, 'round' every "
                         "cross-match round pair. Neither is capped or sampled.")
    ap.add_argument("--min-coverage", type=float, default=0.0,
                    help="exit non-zero if coverage falls below this fraction")
    args = ap.parse_args(argv)

    res = measure(args.facts, args.hand, generated_path=args.generated,
                  two_site=args.two_site, samples=args.samples, seed=args.seed,
                  progress=print)

    if res["trivial_generated"]:
        print("WARNING: generated claims never falsified by any mutation: "
              f"{res['trivial_generated']}")

    covered, uncovered, untested = res["covered"], res["uncovered"], res["untested"]
    testable = len(covered) + len(uncovered)
    frac = len(covered) / testable if testable else 0.0
    print(f"\ncoverage: {len(covered)}/{testable} testable hand-written claims "
          f"({frac:.0%}) are implied by a generated claim "
          f"({len(res['identical'])} of them behave identically)")
    if untested:
        print(f"  ({len(untested)} claims were never falsified by any mutant in this "
              f"corpus, so this run cannot judge them: {untested})")
    print("\ncovered:")
    for cid in covered:
        d = res["detail"][cid]
        print(f"  {cid} <- {d['implied_by']} {d['family']}"
              f"{'  (identical)' if d['identical'] else ''}")
    print("\nNOT covered (these stay hand-written):")
    for cid in uncovered:
        d = res["detail"][cid]
        print(f"  {cid} [{d['category']}] {d['gloss'][:88]}")

    if args.min_coverage and frac < args.min_coverage:
        print(f"\nFAIL: coverage {frac:.0%} below required {args.min_coverage:.0%}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
