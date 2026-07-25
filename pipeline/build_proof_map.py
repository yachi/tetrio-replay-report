"""Record which claims the verifier actually proved.

    python3 -m pipeline.build_proof_map <claims.json> --dafny-dir <dir> --out <map.json>

Runs `dafny verify` itself, parses the output, and marks a claim "verified" only if its
lemma is present and no error was attributed to it. Codegen must never stamp this field:
an optimistic "verified" that the verifier never produced is exactly the overclaim the
whole pipeline exists to prevent.
"""
import argparse
import json
import re
import subprocess
import sys


def lemma_lines(claims_dfy):
    """{lemma name: line number} for every lemma in the file."""
    out = {}
    with open(claims_dfy, encoding="utf-8") as fh:
        for n, line in enumerate(fh, start=1):
            m = re.match(r"\s*lemma\s+([A-Za-z0-9_]+)\s*\(", line)
            if m:
                out[m.group(1)] = n
    return out


def failing_lemmas(verifier_output, lemmas):
    """Attribute each reported error to the lemma it falls inside."""
    starts = sorted(((n, name) for name, n in lemmas.items()))
    bad = set()
    for m in re.finditer(r"Claims\.dfy\((\d+),\d+\):\s*Error", verifier_output):
        line = int(m.group(1))
        enclosing = None
        for n, name in starts:
            if n <= line:
                enclosing = name
            else:
                break
        if enclosing:
            bad.add(enclosing)
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("claims")
    ap.add_argument("--dafny-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    with open(args.claims, encoding="utf-8") as fh:
        claims = json.load(fh)

    claims_dfy = f"{args.dafny_dir}/Claims.dfy"
    lemmas = lemma_lines(claims_dfy)

    proc = subprocess.run(
        ["dafny", "verify", f"{args.dafny_dir}/Facts.dfy", claims_dfy, "--cores", "4"],
        capture_output=True, text=True, check=False)
    output = proc.stdout + proc.stderr
    bad = failing_lemmas(output, lemmas)
    summary = output.strip().splitlines()[-1] if output.strip() else "(no verifier output)"

    rows = []
    for c in claims:
        name = next((n for n in lemmas if n.startswith(c["id"] + "_")), None)
        if name is None:
            status = "missing-lemma"
        elif name in bad:
            status = "failed"
        else:
            status = "verified"
        rows.append({"id": c["id"], "lemma": name or "", "file": "Claims.dfy",
                     "family": c.get("family", ""), "status": status})

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    ok = sum(1 for r in rows if r["status"] == "verified")
    print(f"verifier said: {summary}")
    print(f"wrote {args.out} — {ok}/{len(rows)} verified")
    if ok != len(rows):
        for r in rows:
            if r["status"] != "verified":
                print(f"  {r['id']}: {r['status']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
