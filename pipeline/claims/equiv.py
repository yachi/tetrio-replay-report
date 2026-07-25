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
import copy
import json
import random

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


def apply_mutation(facts, site, rng):
    """Mutate one value in a deep copy and return it."""
    f2 = copy.deepcopy(facts)
    other = {facts["players"][0]: facts["players"][1],
             facts["players"][1]: facts["players"][0]}
    kind = site[0]
    if kind == "match_winner":
        _, mi = site
        m = f2["matches"][mi]
        m["winner"] = other[m["winner"]]
    elif kind == "score":
        _, mi, pl = site
        f2["matches"][mi]["score"][pl] += rng.choice([-1, 1])
    elif kind == "lb":
        _, mi, pl, f = site
        f2["matches"][mi]["leaderboard"][pl][f] = _bump(
            f2["matches"][mi]["leaderboard"][pl][f], rng)
    elif kind == "round_winner":
        _, mi, ri = site
        r = f2["matches"][mi]["rounds"][ri]
        r["winner"] = other[r["winner"]]
        for pl in f2["players"]:
            r["players"][pl]["alive"] = (pl == r["winner"])
    elif kind == "field":
        _, mi, ri, pl, f = site
        p = f2["matches"][mi]["rounds"][ri]["players"][pl]
        p[f] = _bump(p[f], rng)
    elif kind == "clear":
        _, mi, ri, pl, f = site
        c = f2["matches"][mi]["rounds"][ri]["players"][pl]["clears"]
        c[f] = _bump(c[f], rng)
    elif kind == "ge":
        _, mi, ri, pl, gi = site
        g = f2["matches"][mi]["rounds"][ri]["players"][pl]["garbage_events"]
        g[gi]["amt"] = _bump(g[gi]["amt"], rng)
    return f2


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


def truth_vector(compiled, corpus):
    out = []
    for facts in corpus:
        try:
            out.append(bool(eval(compiled, {"__builtins__": __builtins__}, {"facts": facts})))
        except Exception:                    # noqa: BLE001 - a mutation broke an index
            out.append(None)
    return tuple(out)


def implies(g, h):
    """g -> h on every sample where both evaluated."""
    seen = False
    for a, b in zip(g, h):
        if a is None or b is None:
            continue
        seen = True
        if a and not b:
            return False
    return seen


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

    # Stream the mutants: build one, evaluate every claim on it, discard. Holding
    # thousands of deep copies at once would cost gigabytes for nothing.
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
    for n, site in enumerate(sites, 1):
        evaluate(apply_mutation(facts, site, rng))
        if n % 500 == 0:
            print(f"  ... {n}/{len(sites)} mutants evaluated")

    gtriples = []
    for (c, _), v in zip(gen_codes, gvecs):
        vt = tuple(v)
        gtriples.append((c, vt, any(x is False for x in vt)))

    trivial = [c["id"] for c, _, nt in gtriples if not nt]
    if trivial:
        print(f"WARNING: generated claims never falsified by any mutation: {trivial}")

    covered, uncovered, untested = [], [], []
    for (h, _), v in zip(hand_codes, hvecs):
        hv = tuple(v)
        if not any(x is False for x in hv):
            untested.append(h)
            continue
        exact = next((c for c, gv, nt in gtriples if nt and gv == hv), None)
        impl = exact or next((c for c, gv, nt in gtriples if nt and implies(gv, hv)), None)
        if impl is None:
            # A hand claim often bundles two facts ("more quads, fewer T-spins").
            # The ledger still carries it if a PAIR of generated claims does, so try
            # conjunctions of two before declaring it uncovered.
            for i, (c1, v1, nt1) in enumerate(gtriples):
                if not nt1:
                    continue
                for c2, v2, nt2 in gtriples[i + 1:]:
                    if not nt2:
                        continue
                    both = tuple(None if (a is None or b is None) else (a and b)
                                 for a, b in zip(v1, v2))
                    if implies(both, hv):
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
