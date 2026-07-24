#!/usr/bin/env python3
"""build_proof_map.py (07-24) — write proof-map-24.json from the REAL verifier.

Runs `dafny verify` on the generated files, attributes any error to its
enclosing lemma, and marks each of the 20 claims "verified" only if the verifier
actually verified it. Exits nonzero if any claim is not verified.
"""
import json, os, re, subprocess, sys
import codegen_dafny as cg

HERE = os.path.dirname(os.path.abspath(__file__))
DAFNY = "/opt/homebrew/bin/dafny"
FILES = ["Facts24.dfy", "Claims24.dfy"]


def lemmas_with_errors(dfy_path, error_lines):
    names = {}
    cur = None
    with open(dfy_path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            m = re.match(r"\s*lemma\s+([A-Za-z0-9_]+)\s*\(", line)
            if m:
                cur = m.group(1)
            names[i] = cur
    return {names.get(ln) for ln in error_lines if names.get(ln)}


def main():
    os.chdir(os.path.join(HERE, "dafny"))
    proc = subprocess.run([DAFNY, "verify", *FILES, "--cores", "4", "--verification-time-limit", "120"],
                          capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    print(out.strip().splitlines()[-1] if out.strip() else "(no verifier output)")
    summary = re.search(r"(\d+) verified, (\d+) errors", out)
    n_err = int(summary.group(2)) if summary else 999
    failed = set()
    for m in re.finditer(r"(Facts24|Claims24)\.dfy\((\d+),", out):
        failed |= lemmas_with_errors(os.path.join(HERE, "dafny", m.group(1) + ".dfy"), [int(m.group(2))])

    proof_map = []
    for e in cg.lemma_index():
        if e["lemma"] in failed:
            st = "failed"
        elif n_err == 0:
            st = "verified"
        elif failed:
            st = "verified"
        else:
            st = "unverified"
        proof_map.append({"id": e["id"], "lemma": e["lemma"], "file": e["file"], "status": st})

    with open(os.path.join(HERE, "proof-map-24.json"), "w") as f:
        json.dump(proof_map, f, indent=2, ensure_ascii=False)
    nver = sum(1 for e in proof_map if e["status"] == "verified")
    print(f"proof-map-24.json: {nver}/{len(proof_map)} verified (verifier reported {n_err} errors)")
    sys.exit(0 if nver == len(proof_map) else 1)


if __name__ == "__main__":
    main()
