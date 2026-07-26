"""Read a session's claim ledgers plus their proof map.

One loader, because every section that cites claims needs the same three things
and must agree about the third: the claim's id, its Cantonese, and whether the
*verifier* said it holds. A status is only ever "verified" when a proof-map entry
says so — codegen never stamps one, and a claim absent from the map is pending,
not assumed good.
"""
import glob
import json
import os


def load(report_dir, ledger="claims-generated.json"):
    """Claims from one ledger, each with its proof status resolved.

    Returns a list of dicts: id, family, category, canto, spec, verified.
    """
    path = os.path.join(report_dir, ledger)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        claims = json.load(fh)

    status = {}
    stem = ledger[:-len(".json")] if ledger.endswith(".json") else ledger
    for pm in glob.glob(os.path.join(report_dir, f"{stem}-proof-map.json")):
        with open(pm, encoding="utf-8") as fh:
            rows = json.load(fh)
        rows = rows if isinstance(rows, list) else [dict(v, id=k) for k, v in rows.items()]
        for row in rows:
            status[row["id"]] = row.get("status")

    return [{"id": c["id"], "family": c.get("family", ""),
             "category": c.get("category", ""), "canto": c["canto"],
             "spec": c.get("spec"), "verified": status.get(c["id"]) == "verified"}
            for c in claims]


def by_family(claims, prefixes):
    """Claims whose family starts with any of `prefixes`, ledger order preserved."""
    return [c for c in claims if c["family"].startswith(tuple(prefixes))]


def round_operand(claim):
    """The (match, round, player, field, value) a superlative claim is *about*.

    Superlative specs open with `eq(round(mi, ri, pl, f), lit(v))` — the operands
    of the equality the verifier proved. Reading them here means a card's number
    is the proved number, not a re-derivation from facts.json that could disagree
    with it. Returns None when the spec has any other shape, so a section can
    skip the claim rather than invent a figure for it.
    """
    spec = claim.get("spec") or {}
    first = spec["xs"][0] if spec.get("p") == "and" and spec.get("xs") else spec
    if first.get("p") != "eq":
        return None
    a, b = first.get("a") or {}, first.get("b") or {}
    if a.get("e") != "round" or b.get("e") != "lit":
        return None
    if not all(k in a for k in ("mi", "ri", "pl", "f")):
        return None
    return {"match": a["mi"] + 1, "round": a["ri"] + 1, "player": a["pl"],
            "field": a["f"], "value": b["v"]}
