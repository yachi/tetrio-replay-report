"""Record which claims the verifier actually proved.

    python3 -m pipeline.build_proof_map <claims.json>... --dafny-dir <dir> --out <map.json>

Takes as many ledgers as codegen was given, in the same order, so one map covers every
lemma in the emitted Claims.dfy.

Runs `dafny verify` itself, parses the output, and marks a claim "verified" only if its
lemma is present and no error was attributed to it. Codegen must never stamp this field:
an optimistic "verified" that the verifier never produced is exactly the overclaim the
whole pipeline exists to prevent.

It refuses to write the map (exit 2, `--out` untouched) unless the run's own summary line
says `N verified, 0 errors`, or every error it reports is attributed to a lemma. Without that
check an error outside Claims.dfy's lemmas (Facts.dfy, a resolution error, a crash, empty
output) left nothing attributed and every row read "verified".

    python3 -m pipeline.build_proof_map --selftest   # fake-dafny shims: three failures, one control
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


SUMMARY = re.compile(r"(\d+) verified, (\d+) errors?")


def refusal(output, returncode, bad):
    """Why this verifier run cannot license a map, or None when it can.

    Dafny's verified count is not compared with the lemma count: it counts Facts.dfy's
    obligations too, so that comparison would break on a change that is not an error."""
    found = SUMMARY.findall(output)
    if not found:
        return "no 'N verified, M errors' summary in the verifier output"
    errors = int(found[-1][1])
    if errors and not bad:
        return f"the verifier reported {errors} error(s), none inside a lemma of Claims.dfy"
    if returncode != 0 and not bad:
        return f"dafny exited {returncode} with no error attributed to a lemma"
    return None


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if argv[:1] == ["--selftest"]:
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("claims", nargs="+",
                    help="one or more ledgers, in the order codegen was given them")
    ap.add_argument("--dafny-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    claims = []
    for path in args.claims:
        with open(path, encoding="utf-8") as fh:
            claims.extend(json.load(fh))

    claims_dfy = f"{args.dafny_dir}/Claims.dfy"
    lemmas = lemma_lines(claims_dfy)

    proc = subprocess.run(
        ["dafny", "verify", f"{args.dafny_dir}/Facts.dfy", claims_dfy, "--cores", "4"],
        capture_output=True, text=True, check=False)
    output = proc.stdout + proc.stderr
    bad = failing_lemmas(output, lemmas)
    summary = output.strip().splitlines()[-1] if output.strip() else "(no verifier output)"
    why = refusal(output, proc.returncode, bad)
    if why:
        print(f"verifier said: {summary}", file=sys.stderr)
        print(f"refusing to write {args.out}: {why}", file=sys.stderr)
        return 2

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


def selftest():
    """Run main() against fake `dafny` binaries; each failure must exit non-zero and leave
    --out byte-identical, the control must write the map."""
    import os
    import tempfile
    shims = {
        "facts-error": ("Facts.dfy(3,4): Error: unresolved identifier\n"
                        "1 resolution/type errors detected in Facts.dfy\n", 2),
        "empty-output": ("", 0),
        "unlocated-error": ("Dafny program verifier finished with 5 verified, 1 errors\n", 4),
        "exit-nonzero": ("Dafny program verifier finished with 5 verified, 0 errors\n", 3),
    }
    control = ("Dafny program verifier finished with 5 verified, 0 errors\n", 0)
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, "claims.json")
        with open(ledger, "w", encoding="utf-8") as fh:
            json.dump([{"id": "C001", "family": "f"}, {"id": "C002", "family": "f"}], fh)
        with open(os.path.join(tmp, "Claims.dfy"), "w", encoding="utf-8") as fh:
            fh.write("lemma C001_a()\n  ensures true\n{}\nlemma C002_b()\n  ensures true\n{}\n")
        bindir = os.path.join(tmp, "bin")
        os.mkdir(bindir)
        out = os.path.join(tmp, "map.json")
        sentinel = "untouched\n"
        path = os.environ.get("PATH", "")

        def run(text, code):
            with open(os.path.join(tmp, "out.txt"), "w", encoding="utf-8") as fh:
                fh.write(text)
            shim = os.path.join(bindir, "dafny")
            with open(shim, "w", encoding="utf-8") as fh:
                fh.write(f"#!/bin/sh\ncat '{tmp}/out.txt'\nexit {code}\n")
            os.chmod(shim, 0o755)
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(sentinel)
            os.environ["PATH"] = bindir + os.pathsep + path
            try:
                import contextlib
                import io
                with contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    rc = main([ledger, "--dafny-dir", tmp, "--out", out])
            finally:
                os.environ["PATH"] = path
            with open(out, encoding="utf-8") as fh:
                return rc, fh.read()

        for name, (text, code) in shims.items():
            rc, body = run(text, code)
            ok = rc != 0 and body == sentinel
            print(f"  {'killed' if ok else 'SURVIVED'}  {name} (exit {rc}, "
                  f"out {'untouched' if body == sentinel else 'WRITTEN'})")
            if not ok:
                failures.append(name)
        rc, body = run(*control)
        ok = rc == 0 and body != sentinel and \
            [r["status"] for r in json.loads(body)] == ["verified", "verified"]
        print(f"  {'ok' if ok else 'FAILED'}  control (exit {rc})")
        if not ok:
            failures.append("control")
        rc, body = run("Claims.dfy(5,2): Error: postcondition might not hold\n"
                       "Dafny program verifier finished with 4 verified, 1 errors\n", 4)
        ok = rc == 1 and [r["status"] for r in json.loads(body)] == ["verified", "failed"]
        print(f"  {'ok' if ok else 'FAILED'}  attributed error writes a 'failed' row (exit {rc})")
        if not ok:
            failures.append("attributed")
    print(f"build_proof_map selftest: {len(shims)} planted, {len(failures)} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
