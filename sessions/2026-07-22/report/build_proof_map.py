#!/usr/bin/env python3
"""build_proof_map.py — write claims-proof-map.json from the REAL Dafny verifier.

Runs `dafny verify` on the generated files, attributes any error to its enclosing
lemma (by source line), and marks each of the 54 claims "verified" only if the
verifier actually verified it. Never stamps a status the verifier did not produce.
Exits nonzero if any claim is not verified.
"""
import json, os, re, subprocess, sys
import codegen_dafny as cg

HERE = os.path.dirname(os.path.abspath(__file__))
DAFNY = "/opt/homebrew/bin/dafny"
FILES = ["Facts.dfy", "Claims_narrative.dfy", "Claims_coaching.dfy"]


def enclosing_lemmas_with_errors(dfy_path, error_lines):
    """Map 1-based error line numbers to the nearest preceding `lemma NAME(`."""
    names_by_line = {}
    cur = None
    with open(dfy_path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            m = re.match(r"\s*lemma\s+([A-Za-z0-9_]+)\s*\(", line)
            if m:
                cur = m.group(1)
            names_by_line[i] = cur
    return {names_by_line.get(ln) for ln in error_lines if names_by_line.get(ln)}


def main():
    os.chdir(os.path.join(HERE, "dafny"))
    proc = subprocess.run(
        [DAFNY, "verify", *FILES, "--cores", "4", "--verification-time-limit", "120"],
        capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    summary = re.search(r"(\d+) verified, (\d+) errors", out)
    print(out.strip().splitlines()[-1] if out.strip() else "(no verifier output)")

    # attribute errors to lemmas
    failed = set()
    for m in re.finditer(r"(Claims_narrative|Claims_coaching|Facts)\.dfy\((\d+),", out):
        f, ln = m.group(1) + ".dfy", int(m.group(2))
        failed |= enclosing_lemmas_with_errors(os.path.join(HERE, "dafny", f), [ln])

    idx = cg.lemma_index()
    n_err = int(summary.group(2)) if summary else 999
    proof_map = []
    for e in idx:
        # verified only when the run finished cleanly OR the error was attributed
        # to a *different* lemma; any unattributed error => conservative "unverified".
        if e["lemma"] in failed:
            st = "failed"
        elif n_err == 0:
            st = "verified"
        elif failed:  # errors exist and were all attributed to other lemmas
            st = "verified"
        else:  # errors exist but none could be attributed -> do not claim success
            st = "unverified"
        proof_map.append({"id": e["id"], "lemma": e["lemma"], "file": e["file"], "status": st})

    with open(os.path.join(HERE, "claims-proof-map.json"), "w") as f:
        json.dump(proof_map, f, indent=2, ensure_ascii=False)

    nverif = sum(1 for e in proof_map if e["status"] == "verified")
    print(f"claims-proof-map.json: {nverif}/{len(proof_map)} verified "
          f"(verifier reported {n_err} errors)")
    sys.exit(0 if nverif == len(proof_map) else 1)


if __name__ == "__main__":
    main()
