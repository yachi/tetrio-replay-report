"""Measure how much of a hand-written ledger the generated families already cover.

    python3 -m pipeline.claims.equiv sessions/2026-07-24/report/facts.json \
        --hand sessions/2026-07-24/report/claims-narrative.json \
               sessions/2026-07-24/report/claims-coaching.json

Why this is not a string comparison: every predicate in every ledger is True on the
real data, so evaluating them there tells you nothing about whether two predicates pin
the same fact. Instead we perturb the dataset many times and compare behaviour.

A hand claim H counts as covered by a generated claim G when, across every sampled
mutation, G being true forces H to be true (G implies H), and G is not trivially
always-true. If that holds, proving G gives you H for free.

By default every single-value mutation of the dataset is tried, so the conclusion holds
for the whole space of one-value changes — not a random sample of it. It is still not a
proof of equivalence (two predicates could differ only under a simultaneous change to
two values), and claims that no single mutation can falsify are reported separately
rather than counted as covered.

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


def mutation_writes(facts, site, rng):
    """The `(container, key, value)` writes that realise one mutation.

    Was `apply_mutation`, which deep-copied `facts` and wrote into the copy — an O(|facts|)
    rebuild per O(1) edit, and 88 % of this tool's runtime. `pipeline.perturb.perturbed`
    applies these in place and undoes them, which is the same mutant for a few hundred
    nanoseconds instead of twelve milliseconds. See that module for what the trade costs
    and which assertion buys it back.

    The `rng` draws happen HERE, in site order, exactly as often as the deepcopy version
    drew them — one `_bump` (or one `choice`) per site, none for the winner flips. That is
    not incidental tidiness: the corpus is seeded, so any change to the number or order of
    draws silently produces a different set of mutants and a different coverage figure,
    which would read as a result rather than as a bug.
    """
    other = {facts["players"][0]: facts["players"][1],
             facts["players"][1]: facts["players"][0]}
    kind = site[0]
    if kind == "match_winner":
        _, mi = site
        m = facts["matches"][mi]
        return [(m, "winner", other[m["winner"]])]
    if kind == "score":
        _, mi, pl = site
        s = facts["matches"][mi]["score"]
        return [(s, pl, s[pl] + rng.choice([-1, 1]))]
    if kind == "lb":
        _, mi, pl, f = site
        lb = facts["matches"][mi]["leaderboard"][pl]
        return [(lb, f, _bump(lb[f], rng))]
    if kind == "round_winner":
        _, mi, ri = site
        r = facts["matches"][mi]["rounds"][ri]
        new = other[r["winner"]]
        # `alive` is derived from the winner, so flipping one without the other would
        # build a mutant no extractor could ever produce.
        return ([(r, "winner", new)]
                + [(r["players"][pl], "alive", pl == new) for pl in facts["players"]])
    if kind == "field":
        _, mi, ri, pl, f = site
        p = facts["matches"][mi]["rounds"][ri]["players"][pl]
        return [(p, f, _bump(p[f], rng))]
    if kind == "clear":
        _, mi, ri, pl, f = site
        c = facts["matches"][mi]["rounds"][ri]["players"][pl]["clears"]
        return [(c, f, _bump(c[f], rng))]
    if kind == "ge":
        _, mi, ri, pl, gi = site
        g = facts["matches"][mi]["rounds"][ri]["players"][pl]["garbage_events"][gi]
        return [(g, "amt", _bump(g["amt"], rng))]
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

      **That gap is measured, not assumed, and it is not the same on every session.** On
      2026-07-28 the two granularities return the identical verdict — 6/10, same covered
      set — from 2 429 moves instead of 143 186, 8.6 s instead of 165 s. On 2026-07-22
      `round` finds two implications `match` does not (44/53 vs 42/53), and both are
      per-round claims: C007 names one marathon round, C024 one round's peak VS. So quote
      a `match`-granularity figure as an upper bound on coverage, and re-run `round`
      before publishing one.

    The delta is HALF the source (`d = max(1, source[f] // 2)`). Two constraints pull
    against each other here and half is where they meet. `_bump`'s argument says a gentle
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
    this family draws nothing. The single-site sweep's draws — and therefore its mutants
    and its coverage figure — are byte-identical whether or not `--two-site` is given.
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


def _bump(v, rng):
    """Perturb aggressively.

    Gentle nudges are useless here: a +-1 change to one round out of fifty never flips
    an aggregate comparison, so the claim stays true under every mutation and then
    looks "implied" by anything at all. Mutations have to be big enough to move totals.
    """
    kind = rng.choice(["zero", "double", "halve", "swing", "step"])
    if kind == "zero":
        return 0
    if kind == "double":
        return v * 2 + 1
    if kind == "halve":
        return v // 2
    if kind == "swing":
        return max(0, v + rng.choice([-1, 1]) * max(1, abs(v) // 3))
    return max(0, v + rng.choice([-1, 1]) * max(1, abs(v) // 20))


class Vec:
    """A three-valued truth vector as two bitmaps, one bit per mutant.

    `defined` bit i is set when claim evaluation produced a verdict on sample i;
    `value` bit i is set when that verdict was True. `value` is always a subset of
    `defined`, so an undefined sample reads as 0 in both and "defined and False" is
    exactly `defined ^ value`.

    Why not a list of True/False/None: the pair-coverage search below tries every PAIR
    of generated claims against each uncovered hand claim — O(|hand| x |gen|^2) vector
    operations, and on 2026-07-22 that is 167 million interpreter steps inside one
    generator expression, the single hottest line in the tool. Python's ints are
    arbitrary-precision bitmaps, so the same conjunction over 7 020 samples becomes a
    couple of `&`s over ~110 machine words. This is the word-parallel trick behind
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
        growing int is O(n) per bit and so O(n^2) overall, which for 7 020 samples costs
        more than it saves.
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("facts")
    ap.add_argument("--hand", nargs="+", required=True, help="hand-written ledgers")
    ap.add_argument("--generated", help="generated ledger (default: build it now)")
    ap.add_argument("--samples", type=int, default=0,
                    help="cap the mutation count (0 = exhaustive, the default)")
    ap.add_argument("--seed", type=int, default=20260725)
    ap.add_argument("--two-site", choices=["off", "match", "round"], default="off",
                    help="add value-preserving two-site moves (see move_sites for the "
                         "bound). 'match' is one move per match pair, 'round' every "
                         "cross-match round pair. Neither is capped or sampled; "
                         "--samples applies to the single-value family only.")
    ap.add_argument("--min-coverage", type=float, default=0.0,
                    help="exit non-zero if coverage falls below this fraction")
    args = ap.parse_args(argv)

    with open(args.facts, encoding="utf-8") as fh:
        facts = json.load(fh)

    if args.generated:
        with open(args.generated, encoding="utf-8") as fh:
            gen = json.load(fh)
    else:
        from .build_claims import generate, render
        gen = render(generate(facts))

    hand = []
    for path in args.hand:
        with open(path, encoding="utf-8") as fh:
            hand.extend(json.load(fh))

    rng = random.Random(args.seed)
    sites = mutation_sites(facts)
    if args.samples and args.samples < len(sites):
        rng.shuffle(sites)
        sites = sites[:args.samples]
        note = f"{len(sites)} sampled single-value mutations"
    else:
        note = f"all {len(sites)} single-value mutation sites (exhaustive)"
    print(f"mutation corpus: {note}")

    gen_codes = [(c, compile(c["python_check"], "<gen>", "eval")) for c in gen]
    hand_codes = [(h, compile(h["python_check"], "<hand>", "eval")) for h in hand]

    # Mutate `facts` in place, evaluate every claim, undo. Nothing is copied and nothing
    # is held: the mutant exists only for the duration of the `with` block.
    gvecs = [[] for _ in gen_codes]
    hvecs = [[] for _ in hand_codes]

    def evaluate(dataset):
        env = {"__builtins__": __builtins__}
        for i, (_, code) in enumerate(gen_codes):
            try:
                gvecs[i].append(bool(eval(code, env, {"facts": dataset})))
            except Exception:            # noqa: BLE001 - mutation broke an index
                gvecs[i].append(None)
        for i, (_, code) in enumerate(hand_codes):
            try:
                hvecs[i].append(bool(eval(code, env, {"facts": dataset})))
            except Exception:            # noqa: BLE001
                hvecs[i].append(None)

    evaluate(facts)
    pristine = perturb.fingerprint(facts)
    for n, site in enumerate(sites, 1):
        with perturb.perturbed(mutation_writes(facts, site, rng)):
            evaluate(facts)
        if n % 500 == 0:
            print(f"  ... {n}/{len(sites)} mutants evaluated")
    # The one thing deepcopy gave for free. A restore that misses a single site leaves
    # every later mutant on a wrong baseline and still prints a plausible coverage
    # figure, so this is checked rather than assumed.
    assert perturb.unchanged(facts, pristine), \
        "the mutation sweep did not restore facts — coverage below would be measured " \
        "against a corrupted baseline"

    if args.two_site != "off":
        log = {}
        moves = move_sites(facts, gen + hand, args.two_site, log)
        print(f"two-site corpus: {len(moves)} value-preserving moves "
              f"({args.two_site} granularity)")
        # Everything the bound threw away, named. A cap nobody can see is worse than a
        # smaller one everybody can.
        print(f"  fields never read by any predicate, so not moved: "
              f"{log['dropped_fields'] or 'none'}")
        print(f"  moves skipped because the source was too small to split (<2): {log['zero_source']}")
        print(f"  round/field slots absent from the data: {log['absent_field']}")
        print("  not enumerated by the bound: moves between two rounds of the SAME "
              "match (no window and no total can see one), between different fields, "
              "and between the two players")
        if args.two_site == "match":
            print("  not enumerated at this granularity: moves out of any round but the "
                  "source match's largest, or into any but the target match's smallest "
                  "— so a claim that turns on WHICH round is touched is out of scope")
        for n, site in enumerate(moves, 1):
            with perturb.perturbed(move_writes(facts, site)):
                evaluate(facts)
            if n % 500 == 0:
                print(f"  ... {n}/{len(moves)} moves evaluated")
        assert perturb.unchanged(facts, pristine), \
            "the two-site sweep did not restore facts — coverage below would be " \
            "measured against a corrupted baseline"

    gtriples = []
    for (c, _), v in zip(gen_codes, gvecs):
        vt = Vec.of(v)
        gtriples.append((c, vt, vt.falsified()))

    trivial = [c["id"] for c, _, nt in gtriples if not nt]
    if trivial:
        print(f"WARNING: generated claims never falsified by any mutation: {trivial}")

    # A claim no mutation falsifies can imply nothing useful, and both loops below skipped
    # it. Filtering once keeps the quadratic pair search off them entirely.
    live = [(c, v) for c, v, nt in gtriples if nt]

    covered, uncovered, untested = [], [], []
    for (h, _), v in zip(hand_codes, hvecs):
        hv = Vec.of(v)
        if not hv.falsified():
            untested.append(h)
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
        (covered if impl else uncovered).append((h, impl, exact is not None))

    testable = len(covered) + len(uncovered)
    frac = len(covered) / testable if testable else 0.0
    exact_n = sum(1 for _, _, e in covered if e)
    print(f"\ncoverage: {len(covered)}/{testable} testable hand-written claims "
          f"({frac:.0%}) are implied by a generated claim "
          f"({exact_n} of them behave identically)")
    if untested:
        print(f"  ({len(untested)} claims were never falsified by any sampled mutation, "
              f"so this run cannot judge them: {[h['id'] for h in untested]})")
    print("\ncovered:")
    for h, g, e in covered:
        print(f"  {h['id']} <- {g['id']} {g['family']}{'  (identical)' if e else ''}")
    print("\nNOT covered (these stay hand-written):")
    for h, _, _ in uncovered:
        print(f"  {h['id']} [{h.get('category','?')}] {h['english_gloss'][:88]}")

    if args.min_coverage and frac < args.min_coverage:
        print(f"\nFAIL: coverage {frac:.0%} below required {args.min_coverage:.0%}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
