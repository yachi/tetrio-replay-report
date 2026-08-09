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
"""
import argparse
import json
import random

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
