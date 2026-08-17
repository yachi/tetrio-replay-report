"""Two artefacts describing the same session must agree on every field they share.

    python3 -m pipeline.check_cross_artefact            # every sessions/* holding two artefacts
    python3 -m pipeline.check_cross_artefact --selftest # plant one mutant per rule, require catches

`sessions/2026-07-24` carries two independently built artefacts of the same night:
`report/facts.json` (the published one) and `proof/facts-24.json` (the lighter 20-claim
cross-check, written by its own `extract-24.py` / `extract2-24.ts`). `bin/verify-session`
checks each directory INTERNALLY — dual-extractor agreement, claim predicates, Dafny, the
proof map — and it takes ONE artefact directory, so it has no place to stand from which to
compare the two. Both therefore go green while disagreeing with each other, and the only
thing that has ever stopped them diverging is somebody remembering to re-extract `proof/`
whenever `report/` moved.

That hazard is live-but-remembered, not hypothetical: the 2026-08-15 change that moved
apm/pps/vs off the in-game live tick and onto `aggregatestats` touched both extractors in
`report/`, and `proof/` had to be re-extracted by hand. It was. Nothing would have said so
otherwise — `verify-session sessions/2026-07-24/proof` passes over a stale artefact just as
happily as over a fresh one, because every gate it runs is internal to that directory.

WHY ITS OWN CHECKER AND NOT A LEG OF `bin/verify-session`. The subject is a PAIR, and
`verify-session`'s argument is a single artefact. As a leg it would run twice per session
(once from each side, asking the same question), and — the part that actually decides it —
it would have nowhere to fail when the pair is MISSING: delete `proof/` and every
`verify-session` invocation still passes, which is precisely the vacuous-clean shape this
repo's gates are written against. Here the sweep is globbed over `sessions/*`, and finding
no pair at all is a failure.

WHAT IT DOES NOT COMPARE, AND WHY THAT IS PRINTED. The two artefacts have different
schemas — `report/` carries 30 per-player fields `proof/` never had (`score`,
`finaltime_ms`, `gameoverreason`, the four extra `clears` counters, ...). A gate that
silently intersected them would be free to shrink to nothing and still print `ok`, which is
the `codegen.py:76-78` rule in reverse. So every field carried by only one side is NAMED,
and the count of compared leaves is printed beside it.

The distinction that makes that safe is RECORD vs FIELD. A field on one side only is a
schema difference and is named. A RECORD on one side only — a match, a round, a player, a
garbage event — is a missing observation, and that is a failure: the tolerated axis is which
columns exist, never which rows do. `RECORD_DICTS` below names the dicts whose keys are rows.
"""
import argparse
import json
import os
import sys

# Dicts whose KEYS are records rather than fields, as ABSTRACT paths (list keys dropped).
#
# Everywhere else a key present on one side only is a schema difference — the lighter artefact
# does not carry that column — and is named rather than failed. In these three it is a missing
# observation, which is the thing this gate exists to catch.
#
# The artefact ROOT is deliberately not here. A top-level key on one side only is a whole new
# section, which is a schema change and belongs in the named list with everything else; the two
# top-level keys that must exist are asserted directly, by `REQUIRED` below.
RECORD_DICTS = {
    ("matches", "rounds", "players"),     # keyed by username, because order is not stable
    ("matches", "leaderboard"),
    ("matches", "score"),
}

# The shape a facts file has by definition. Asserted rather than inferred, because everything else
# here degrades gracefully: without this, an artefact that had lost `matches` entirely would report
# its every field as "carried by the other side only" — named, and therefore tolerated — and the
# comparison would shrink to the two player names while still printing `ok`.
REQUIRED = ("players", "matches")

# Lists are rekeyed by a natural key so a comparison survives a reordering instead of silently
# comparing match 1 against match 2. `file` is a match's identity and `index` is its POSITION in
# the session — so keying by `file` and then comparing `index` as an ordinary leaf is what turns
# "the two extractors sorted differently" from an invisible offset into a named disagreement.
# That is the m1-vs-第2場 hazard recorded in CLAUDE.md, one artefact against another.
LIST_KEYS = ("file", "index")


def _list_keys(items):
    """A natural key per element, or the positions when the list has none."""
    if items and all(isinstance(x, dict) for x in items):
        for k in LIST_KEYS:
            if all(k in x for x in items):
                keys = [x[k] for x in items]
                if len(set(map(repr, keys))) == len(keys):
                    return keys, k
    return list(range(len(items))), None


def flatten(obj, path=(), abstract=()):
    """`(leaves, records)` — every scalar by path, and every keyed container by path.

    `records` holds the ROW axes: each list's key sequence (so a dropped or reordered match is a
    difference in the sequence, not a pile of missing leaves) and each `RECORD_DICTS` dict's key
    set. Everything else about a dict — which fields it carries — is left to the leaf comparison,
    where a one-sided key is named rather than failed.
    """
    leaves, records = {}, {}
    if isinstance(obj, dict):
        if abstract in RECORD_DICTS:
            records[path] = ("keys", tuple(sorted(map(repr, obj))))
        for k, v in obj.items():
            sub_l, sub_r = flatten(v, path + (k,), abstract + (k,))
            leaves.update(sub_l)
            records.update(sub_r)
    elif isinstance(obj, list):
        keys, by = _list_keys(obj)
        records[path] = (f"order by {by or 'position'}", tuple(map(repr, keys)))
        for k, v in zip(keys, obj):
            # The list key is deliberately NOT part of the abstract path: `matches.rounds.players`
            # must read the same for every match, or `RECORD_DICTS` would have to enumerate them.
            sub_l, sub_r = flatten(v, path + (k,), abstract)
            leaves.update(sub_l)
            records.update(sub_r)
    else:
        leaves[path] = (abstract, obj)
    return leaves, records


def _p(path):
    return ".".join(str(x) for x in path) or "<root>"


def compare(a, b):
    """`(compared, disagreements, structural, only_a, only_b)` for two facts trees."""
    la, ra = flatten(a)
    lb, rb = flatten(b)

    structural = []
    for k in REQUIRED:
        for name, tree in (("left", a), ("right", b)):
            if k not in tree:
                structural.append(f"the {name} artefact has no `{k}` — it is not a facts file")
    # A container path in only ONE tree is a new section, not a missing record: its leaves are
    # named by the field comparison below, which is where a schema difference belongs. What is a
    # missing record is a container both sides have whose KEY SEQUENCE differs — a dropped match, a
    # reordered one, a round that is not there, a player who is.
    for path in sorted(set(ra) & set(rb), key=_p):
        if ra[path] != rb[path]:
            kind = ra[path][0]
            structural.append(
                f"{_p(path)} ({kind}): {list(ra[path][1])} vs {list(rb[path][1])}")

    shared = set(la) & set(lb)
    disagreements = [f"{_p(p)}: {la[p][1]!r} vs {lb[p][1]!r}"
                     for p in sorted(shared, key=_p) if la[p][1] != lb[p][1]]
    # Collapsed to the FIELD, not listed per record: 30 fields x 100 rounds x 2 players is the
    # same 30 facts said 6000 times, and a gate whose "not compared" note is unreadable is a gate
    # whose "not compared" note goes unread.
    only_a = sorted({".".join(la[p][0]) for p in set(la) - shared})
    only_b = sorted({".".join(lb[p][0]) for p in set(lb) - shared})
    return len(shared), disagreements, structural, only_a, only_b


def _facts_file(artefact_dir):
    """The artefact's own facts file, under either naming convention; never the 2nd extractor's."""
    for name in sorted(os.listdir(artefact_dir)):
        if (name.startswith("facts") and name.endswith(".json")
                and not name.startswith("facts2")):
            return os.path.join(artefact_dir, name)
    return None


def artefact_pairs(root):
    """Every `sessions/<date>` holding two or more artefact directories. Globbed, never listed."""
    base = os.path.join(root, "sessions")
    out = []
    if not os.path.isdir(base):
        return out
    for session in sorted(os.listdir(base)):
        sdir = os.path.join(base, session)
        if not os.path.isdir(sdir):
            continue
        found = []
        for sub in sorted(os.listdir(sdir)):
            adir = os.path.join(sdir, sub)
            if os.path.isdir(adir):
                f = _facts_file(adir)
                if f:
                    found.append((sub, f))
        for i in range(len(found)):
            for j in range(i + 1, len(found)):
                out.append((session, found[i], found[j]))
    return out


def check_pair(session, left, right, log=print, err=lambda s: print(s, file=sys.stderr)):
    (lname, lpath), (rname, rpath) = left, right
    with open(lpath, encoding="utf-8") as fh:
        a = json.load(fh)
    with open(rpath, encoding="utf-8") as fh:
        b = json.load(fh)
    compared, disagreements, structural, only_a, only_b = compare(a, b)

    label = f"{session} {lname} vs {rname}"
    if structural or disagreements:
        for s in structural[:10]:
            err(f"FAIL {label}: {s}")
        for d in disagreements[:10]:
            err(f"FAIL {label}: {d}")
        if len(structural) + len(disagreements) > 20:
            err(f"FAIL {label}: … and {len(structural) + len(disagreements) - 20} more")
        err(f"FAIL {label}: {len(structural)} structural difference(s), "
            f"{len(disagreements)} of {compared} shared values disagree — two artefacts of "
            f"one session have diverged, and nothing else in the repo compares them")
        return 1
    if not compared:
        err(f"FAIL {label}: the two artefacts share no field at all, so agreeing on all of "
            f"them says nothing")
        return 1
    log(f"  ok  {label}: {compared} shared values agree")
    # Named, never silently intersected — see the module docstring.
    for name, only in ((lname, only_a), (rname, only_b)):
        if only:
            log(f"  --  {label}: {len(only)} field(s) NOT compared, carried by {name} only: "
                + ", ".join(only))
    return 0


def selftest(log=print):
    """Plant each thing that can go wrong and require `compare` to notice — or to tolerate it.

    The two controls come first. A checker that fails on everything catches every mutant below
    and gates nothing; and a checker that failed on the SCHEMA difference would have to be
    switched off for the only pair in the repo, which is how a gate becomes advisory.
    """
    import copy

    def base():
        return {
            "players": ["yachi", "pinglamb"],
            "matches": [
                {"file": "r-1.ttrm", "index": 1, "score": {"yachi": 1, "pinglamb": 0},
                 "leaderboard": {"yachi": {"wins": 1}, "pinglamb": {"wins": 0}},
                 "rounds": [
                     {"index": 0, "winner": "yachi", "players": {
                         "yachi": {"lines": 10, "clears": {"quads": 2},
                                   "garbage_events": [{"frame": 5, "amt": 2}]},
                         "pinglamb": {"lines": 8, "clears": {"quads": 1},
                                      "garbage_events": [{"frame": 7, "amt": 1}]}}}]},
                {"file": "r-2.ttrm", "index": 2, "score": {"yachi": 0, "pinglamb": 1},
                 "leaderboard": {"yachi": {"wins": 0}, "pinglamb": {"wins": 1}},
                 "rounds": [
                     {"index": 0, "winner": "pinglamb", "players": {
                         "yachi": {"lines": 3, "clears": {"quads": 0},
                                   "garbage_events": []},
                         "pinglamb": {"lines": 9, "clears": {"quads": 3},
                                      "garbage_events": [{"frame": 9, "amt": 4}]}}}]},
            ],
        }

    def drop_field(f):
        for m in f["matches"]:
            for r in m["rounds"]:
                for p in r["players"].values():
                    p.pop("lines")
        return f

    def reorder(f):
        f["matches"] = list(reversed(f["matches"]))
        return f

    def renumber(f):
        for m in f["matches"]:
            m["index"] += 1
        return f

    def drop_round(f):
        f["matches"][0]["rounds"] = []
        return f

    def drop_player(f):
        del f["matches"][0]["rounds"][0]["players"]["pinglamb"]
        return f

    def drop_event(f):
        f["matches"][0]["rounds"][0]["players"]["yachi"]["garbage_events"] = []
        return f

    def bump_value(f):
        f["matches"][1]["rounds"][0]["players"]["pinglamb"]["clears"]["quads"] = 4
        return f

    def drop_match(f):
        f["matches"] = f["matches"][:1]
        return f

    def drop_matches(f):
        del f["matches"]
        return f

    def add_section(f):
        f["sim"] = {"forecasts": 3}
        return f

    # (name, must the gate fail?, mutation of the RIGHT-hand artefact)
    cases = [
        ("control: two identical artefacts agree", False, lambda f: f),
        ("control: a field only one side carries is a SCHEMA difference, not a failure",
         False, drop_field),
        # ...and so is a whole new SECTION. The gate must not have to be edited before a new
        # top-level block can be added to the published artefact — that is how a gate becomes the
        # thing people switch off. Its leaves are named, like any other uncompared field.
        ("control: a top-level section only one side carries is named, not failed",
         False, add_section),
        ("`matches` is gone entirely — not a facts file", True, drop_matches),
        ("a shared value disagrees", True, bump_value),
        ("a match's index is renumbered (the m1-vs-第2場 hazard, artefact against artefact)",
         True, renumber),
        ("the matches are in a different order", True, reorder),
        ("a match is missing", True, drop_match),
        ("a round is missing", True, drop_round),
        ("a player is missing from a round", True, drop_player),
        ("a garbage event is missing", True, drop_event),
    ]

    failures, planted = 0, 0
    for name, must_fail, mutate in cases:
        a, b = base(), mutate(base())
        compared, dis, struct, only_a, only_b = compare(a, b)
        fired = bool(dis or struct)
        if must_fail:
            planted += 1
        if fired != must_fail:
            print(f"SELFTEST FAIL: {name} — {'no' if must_fail else 'a spurious'} difference "
                  f"reported ({len(struct)} structural, {len(dis)} value)", file=sys.stderr)
            failures += 1
        else:
            log(f"  ok  {name}")
    # The tolerated case must also be REPORTED, or "tolerated" is indistinguishable from
    # "invisible" — which is the silent-intersection failure the docstring is about. The left
    # artefact carries `lines`; the right had it dropped, so it must appear in `only_a` by name.
    compared, _, _, only_a, only_b = compare(base(), drop_field(base()))
    want = ["matches.rounds.players.pinglamb.lines", "matches.rounds.players.yachi.lines"]
    if only_a != want or only_b != [] or compared == 0:
        print(f"SELFTEST FAIL: a field carried by one side only was not named "
              f"(only_a={only_a}, only_b={only_b}, compared={compared})", file=sys.stderr)
        failures += 1
    else:
        log(f"  ok  control: the {len(want)} uncompared fields are named rather than silently "
            f"intersected, beside the {compared} that were compared")

    if failures:
        print(f"selftest: {failures} of {len(cases) + 1} cases failed", file=sys.stderr)
        return 1
    log(f"  ok  selftest: {planted} planted mutants, all caught; "
        f"{len(cases) - planted + 1} controls held")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--selftest", action="store_true",
                    help="check the gate can still fail, then exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    pairs = artefact_pairs(args.root)
    # Absence is a failure, never a skip: delete `proof/` and a sweep that merely found nothing
    # to do would print nothing and exit 0, which reads exactly like two artefacts agreeing.
    if not pairs:
        print("FAIL no sessions/* holds two artefact directories — this gate would have "
              "nothing to compare, and a sweep over no pairs reads like a clean one",
              file=sys.stderr)
        return 1
    bad = 0
    for session, left, right in pairs:
        bad |= check_pair(session, left, right)
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
