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


def load(report_dir, ledger="claims-generated.json", proof_map=None):
    """Claims from one ledger, each with its proof status resolved.

    `proof_map` defaults to the ledger's own `<stem>-proof-map.json`; the two hand
    ledgers share one map, so a caller reading those passes it explicitly.

    Returns dicts: id, family, category, canto, english_gloss, spec, lemma,
    status (raw, as the map recorded it) and verified (status == "verified").
    """
    path = os.path.join(report_dir, ledger)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        claims = json.load(fh)

    entries = {}
    if proof_map:
        maps = [os.path.join(report_dir, proof_map)]
    else:
        # The ledger's own map if it has one, otherwise the session-wide map. A
        # session whose ledgers all compile into one Claims.dfy has only the latter,
        # and without this fallback every one of its generated claims resolved to no
        # entry and rendered 待證 — a verified claim displayed as still being proved.
        stem = ledger[:-len(".json")] if ledger.endswith(".json") else ledger
        maps = glob.glob(os.path.join(report_dir, f"{stem}-proof-map.json"))
        if not maps:
            maps = glob.glob(os.path.join(report_dir, "claims-proof-map.json"))
    for pm in maps:
        if not os.path.exists(pm):
            continue
        with open(pm, encoding="utf-8") as fh:
            rows = json.load(fh)
        rows = rows if isinstance(rows, list) else [dict(v, id=k) for k, v in rows.items()]
        for row in rows:
            entries[row["id"]] = row

    out = []
    for c in claims:
        entry = entries.get(c["id"]) or {}
        status = entry.get("status")
        if status is None and entry.get("verified") is True:
            status = "verified"
        out.append({"id": c["id"], "family": c.get("family", ""),
                    "category": c.get("category", ""), "canto": c["canto"],
                    "english_gloss": c.get("english_gloss", ""),
                    "spec": c.get("spec"),
                    "lemma": entry.get("lemma") or entry.get("lemma_name")
                             or entry.get("name") or "",
                    "status": status, "verified": status == "verified"})
    return out


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
