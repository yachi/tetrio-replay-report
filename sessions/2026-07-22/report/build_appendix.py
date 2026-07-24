#!/usr/bin/env python3
"""
build_appendix.py — regenerate report.html's embedded claims-data island.

Merges claims-narrative.json (C0xx) + claims-coaching.json (R0xx) with
claims-proof-map.json (id -> Dafny lemma -> status), if it exists, and
writes the merged JSON back into report.html between the
<!-- CLAIMS_DATA_START --> / <!-- CLAIMS_DATA_END --> markers.

Status fallback: any claim missing from the proof-map (file absent, or
file present but that id not yet in it) renders as "pending" (呈現「驗證中」)
until re-run. Only a proof-map entry whose status is exactly "verified"
renders as a checked badge.

Read-only against the claims/facts inputs. The only file this script
writes is report.html (in place, markers-scoped replace).

Usage: python3 build_appendix.py
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
NARRATIVE_PATH = HERE / "claims-narrative.json"
COACHING_PATH = HERE / "claims-coaching.json"
PROOF_MAP_PATH = HERE / "claims-proof-map.json"
REPORT_PATH = HERE / "report.html"

START_MARKER = "<!-- CLAIMS_DATA_START -->"
END_MARKER = "<!-- CLAIMS_DATA_END -->"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_lemma_status(entry):
    """Proof-map entries may come from different Dafny-agent output shapes.
    Be defensive about key names rather than assume one exact schema."""
    if entry is None:
        return "—", "pending", "驗證中"
    lemma = entry.get("lemma") or entry.get("lemma_name") or entry.get("name") or "—"
    status_raw = entry.get("status")
    if status_raw is None and entry.get("verified") is True:
        status_raw = "verified"
    if status_raw == "verified":
        return lemma, "verified", "已驗證"
    # any other status (failed / in_progress / missing) still falls back
    # to the honest "pending" display per spec
    label = "驗證中" if status_raw is None else f"驗證中（{status_raw}）"
    return lemma, "pending", label


def build_claims(source_path, source_tag, proof_map):
    claims = []
    for c in load_json(source_path):
        lemma, status_key, status_label = extract_lemma_status(proof_map.get(c["id"]))
        claims.append({
            "id": c["id"],
            "source": source_tag,
            "canto": c["canto"],
            "english_gloss": c.get("english_gloss", ""),
            "category": c.get("category", ""),
            "lemma": lemma,
            "status": status_key,
            "status_label": status_label,
        })
    return claims


def main():
    proof_map_available = PROOF_MAP_PATH.exists()
    proof_map_raw = load_json(PROOF_MAP_PATH) if proof_map_available else {}
    if isinstance(proof_map_raw, list):
        # shape: [{"id": "C001", "lemma": "...", "status": "verified", ...}, ...]
        proof_map = {}
        for entry in proof_map_raw:
            if isinstance(entry, dict) and "id" in entry:
                proof_map[entry["id"]] = entry
    elif isinstance(proof_map_raw, dict):
        # shape: {"C001": {"lemma": "...", "status": "verified"}, ...}
        proof_map = proof_map_raw
    else:
        print(f"WARNING: {PROOF_MAP_PATH.name} has an unrecognized top-level shape "
              f"({type(proof_map_raw).__name__}); treating as empty "
              "(all claims fall back to 驗證中).", file=sys.stderr)
        proof_map = {}

    claims = build_claims(NARRATIVE_PATH, "narrative", proof_map) + \
        build_claims(COACHING_PATH, "coaching", proof_map)

    verified_count = sum(1 for c in claims if c["status"] == "verified")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "proof_map_available": proof_map_available,
        "total_claims": len(claims),
        "verified_count": verified_count,
        "claims": claims,
    }

    report_html = REPORT_PATH.read_text(encoding="utf-8")
    if START_MARKER not in report_html or END_MARKER not in report_html:
        print(f"ERROR: markers {START_MARKER!r} / {END_MARKER!r} not found in "
              f"{REPORT_PATH.name}. Nothing was written.", file=sys.stderr)
        sys.exit(1)

    new_block = (
        f'{START_MARKER}\n'
        f'<script type="application/json" id="claims-data">\n'
        f'{json.dumps(payload, ensure_ascii=False, indent=2)}\n'
        f'</script>\n'
        f'{END_MARKER}'
    )

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL
    )
    updated_html, n = pattern.subn(new_block, report_html, count=1)
    if n != 1:
        print("ERROR: failed to substitute claims-data block.", file=sys.stderr)
        sys.exit(1)

    REPORT_PATH.write_text(updated_html, encoding="utf-8")

    print(f"claims merged: {len(claims)} "
          f"({sum(1 for c in claims if c['source'] == 'narrative')} narrative + "
          f"{sum(1 for c in claims if c['source'] == 'coaching')} coaching)")
    print(f"proof-map available: {proof_map_available} "
          f"({PROOF_MAP_PATH.name}{'' if proof_map_available else ' not found'})")
    print(f"verified: {verified_count}/{len(claims)}")
    print(f"wrote: {REPORT_PATH}")


if __name__ == "__main__":
    main()
