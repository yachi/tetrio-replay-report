"""Parse the seven worked forecast examples, and gate the two files that describe them.

The seven examples (A–G) exist twice, written independently:

  * `spec/ForecastExamples.dfy` — each is a `returns (h, e)` lemma whose body fixes a concrete
    `History` and `Event` and whose `ensures` are a machine-checked verdict. This is the
    authoritative side: Dafny proves what the definition SAYS about each witness.
  * `spec/example-boards.ts` — the boards drawn alongside, carrying an `event:` string, a
    `history:` string, a `clauses:` array and a `verdict:`. `example-boards.test.ts` checks the
    boards are legal and reachable, and (one gate) that the roof/floor SEPARATION matches the
    Dafny lemma. Nothing checked the rest.

So the two files could disagree on the very thing they both claim to describe — a board captioned
"reject, clause 2" sitting beside a lemma that proves the opposite — and every gate would stay
green: the Dafny verifier never reads the TypeScript, and the TS test only compared one derived
number. That is exactly the drift this repo's whole trust argument is built to forbid ("two
independently written extractors agreeing byte-for-byte"), applied to the pedagogy instead of the
data.

This module is the missing agreement check. It parses BOTH descriptions of all seven examples and
fails on any mismatch of:

  * the `Event` fields the two files share — roofAt, floorAt, holeOpenAtJ, spinAtK;
  * the setup `Step` — clearedRows, wasSpin, garbageRows (the TS `history` IS the Dafny `h[0]`);
  * the verdict — accept / accept-loose / reject — DERIVED from the Dafny `ensures`, not taken on
    the TS file's word, and, for a rejection, the single clause that fails;
  * the lemma name and the A–G id linking the two.

It also emits `spec/forecast-examples.json`: the seven examples as one machine-readable record,
sourced from the verified Dafny witnesses (event/history) with the human title/verdict/clauses
from the boards, having proven the two agree. Like `claims.smt2` it is committed and byte-identity
gated, so it doubles as a portable artefact anything can read without this pipeline — and so a
hand-edit to either source that this checker would catch also shows up as a diff.

Usage:

    python3 -m pipeline.forecast_examples            # the gate: cross-check + JSON is byte-identical
    python3 -m pipeline.forecast_examples --write     # regenerate spec/forecast-examples.json
    python3 -m pipeline.forecast_examples --json       # print the canonical JSON, write nothing
    python3 -m pipeline.forecast_examples --selftest   # prove the gate rejects a planted drift
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DFY = ROOT / "spec" / "ForecastExamples.dfy"
BOARDS = ROOT / "spec" / "example-boards.ts"
ARTIFACT = ROOT / "spec" / "forecast-examples.json"

IDS = ["A", "B", "C", "D", "E", "F", "G"]

# The four clauses of IsForecast, in order, with the JSON key each maps to. The names are the
# predicates in Forecast.dfy; keeping them here means a clause rename in the spec surfaces as a
# failed cross-check rather than a silently stale label.
CLAUSE_KEYS = ["tucked", "holePreExisted", "gapClosed", "nonSpinClear"]


# ---------------------------------------------------------------------------------------------
# Small balanced-delimiter reader. The Dafny witnesses nest brackets (`[ Step([17,18,19], ...) ]`)
# and parens (`Event(...)`), so a non-greedy regex stops at the first close. This walks to the
# match instead. Dafny has no delimiters inside string/char literals in these witnesses, so a
# plain depth count is exact here (asserted by the round-trip: a misparse desyncs A–G).
# ---------------------------------------------------------------------------------------------
def _balanced(text: str, start: int, open_ch: str, close_ch: str) -> tuple[str, int]:
    """From `text[start] == open_ch`, return (inner, index-after-close)."""
    assert text[start] == open_ch, f"expected {open_ch!r} at {start}, got {text[start]!r}"
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
    raise ValueError(f"unbalanced {open_ch!r} from index {start}")


def _split_top(s: str) -> list[str]:
    """Split on top-level commas only (not commas inside nested [] or ())."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _int(tok: str) -> int:
    return int(tok.strip())


def _bool(tok: str) -> bool:
    t = tok.strip()
    if t not in ("true", "false"):
        raise ValueError(f"expected a bool, got {tok!r}")
    return t == "true"


def _parse_step(expr: str) -> dict:
    """`Step([17, 18, 19], false, 0)` -> {clearedRows, wasSpin, garbageRows}."""
    inner, _ = _balanced(expr, expr.index("("), "(", ")")
    a, b, c = _split_top(inner)
    rows_inner, _ = _balanced(a, a.index("["), "[", "]")
    rows = [_int(x) for x in rows_inner.split(",") if x.strip()]
    return {"clearedRows": rows, "wasSpin": _bool(b), "garbageRows": _int(c)}


def _parse_history(expr: str) -> list[dict]:
    """`[ Step(...), Step(...) ]` -> [step, step]."""
    inner, _ = _balanced(expr, expr.index("["), "[", "]")
    steps = []
    i = 0
    while True:
        m = inner.find("Step", i)
        if m < 0:
            break
        _, after = _balanced(inner, inner.index("(", m), "(", ")")
        steps.append(_parse_step(inner[m:after]))
        i = after
    return steps


EVENT_FIELDS = ["j", "k", "roofAt", "floorAt", "holeOpenAtJ", "spinAtK", "availAtJ", "availAtK"]


def _parse_event(expr: str) -> dict:
    """`Event(0, 2, 15, 21, true, true, 0, 0)` -> the 8 fields by name."""
    inner, _ = _balanced(expr, expr.index("("), "(", ")")
    vals = _split_top(inner)
    if len(vals) != len(EVENT_FIELDS):
        raise ValueError(f"Event has {len(vals)} args, expected {len(EVENT_FIELDS)}: {expr!r}")
    out = {}
    for name, tok in zip(EVENT_FIELDS, vals):
        out[name] = _bool(tok) if name in ("holeOpenAtJ", "spinAtK") else _int(tok)
    return out


# ---------------------------------------------------------------------------------------------
# The Dafny side: the executable witness (h, e) and the verdict read off the `ensures`.
# ---------------------------------------------------------------------------------------------
def parse_dafny(text: str | None = None) -> dict[str, dict]:
    if text is None:
        text = DFY.read_text(encoding="utf-8")
    out: dict[str, dict] = {}
    for letter in IDS:
        m = re.search(rf"\blemma\s+(Example{letter}_\w+)\s*\(", text)
        if not m:
            raise ValueError(f"no lemma Example{letter}_… found in {DFY.name}")
        lemma = m.group(1)
        # Scope to this lemma: from its header to the next `lemma ` keyword (or EOF).
        nxt = re.search(r"\blemma\s", text[m.end():])
        body = text[m.start(): m.end() + (nxt.start() if nxt else len(text))]

        he = re.search(r"\bh\s*:=\s*\[", body)
        history = _parse_history(body[he.start():]) if he else None
        ee = re.search(r"\be\s*:=\s*Event\s*\(", body)
        event = _parse_event(body[ee.start():]) if ee else None
        if history is None or event is None:
            raise ValueError(f"{lemma}: could not read h/e witness")

        ensures = " ".join(
            ln.strip() for ln in body.splitlines() if ln.strip().startswith("ensures")
        )
        out[letter] = {
            "id": letter,
            "lemma": lemma,
            "event": event,
            "history": history,
            "verdict": _verdict_from_ensures(ensures),
            "fails_clause": _failing_clause(ensures),
        }
    return out


def _has(ensures: str, pat: str) -> bool:
    return re.search(pat, ensures) is not None


def _forecast_signs(ensures: str) -> tuple[set[str], set[str]]:
    """The IsForecast* predicates asserted positively and negatively."""
    pos, neg = set(), set()
    for m in re.finditer(r"(!\s*)?IsForecast(Triple|AnyClear|Shape)\b", ensures):
        (neg if m.group(1) else pos).add(m.group(2))
    return pos, neg


def _verdict_from_ensures(ensures: str) -> str:
    pos, neg = _forecast_signs(ensures)
    # A rejection states the situation is NOT a forecast at all (shape, i.e. minLines 0, or the
    # any-clear reading). B negates only Triple while asserting AnyClear — that is the loose accept,
    # not a rejection.
    if "Shape" in neg or "AnyClear" in neg:
        return "reject"
    if "AnyClear" in pos and "Triple" in neg:
        return "accept-loose"
    if pos and not neg:
        return "accept"
    raise ValueError(f"cannot classify verdict from ensures: {ensures!r}")


def _failing_clause(ensures: str) -> int | None:
    """For a rejection, the one clause (1..4) that fails, read from the ensures; else None."""
    if _verdict_from_ensures(ensures) != "reject":
        return None
    hits = []
    if _has(ensures, r"!\s*Tucked\b"):
        hits.append(1)
    if _has(ensures, r"!\s*HolePreExisted\b"):
        hits.append(2)
    if _has(ensures, r"!\s*GapClosed\b"):
        hits.append(3)
    # Clause 4 is the C-Spin shape: the gap DID close (asserted positively) but by a spin, so the
    # non-spin count is zero. No predicate negates clause 4 directly, so it is read off these two.
    if _has(ensures, r"(?<!!)(?<!!\s)\bGapClosed\b") and _has(ensures, r"\bClosedByPlain\s*\([^)]*\)\s*==\s*0\b"):
        hits.append(4)
    if len(hits) != 1:
        raise ValueError(f"expected exactly one failing clause, found {hits}: {ensures!r}")
    return hits[0]


# ---------------------------------------------------------------------------------------------
# The TypeScript side: the drawn boards' declared fields.
# ---------------------------------------------------------------------------------------------
def _named_fields(spec: str) -> dict[str, str]:
    """`roofAt := 15, holeOpenAtJ := true, …` -> {roofAt: '15', …} (raw tokens)."""
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"(\w+)\s*:=\s*([^,)]+)", spec)}


def parse_boards(text: str | None = None) -> dict[str, dict]:
    if text is None:
        text = BOARDS.read_text(encoding="utf-8")
    # Isolate the EXAMPLES array so the OVERHANGS block below it is never scanned.
    start = text.index("export const EXAMPLES")
    arr_start = text.index("[", start)
    inner, _ = _balanced(text, arr_start, "[", "]")

    out: dict[str, dict] = {}
    # Each example object is a top-level `{ ... }` in the array.
    i = 0
    while True:
        b = inner.find("{", i)
        if b < 0:
            break
        obj, after = _balanced(inner, b, "{", "}")
        i = after
        idm = re.search(r"\bid:\s*'([A-G])'", obj)
        if not idm:
            continue
        letter = idm.group(1)
        verdict = re.search(r"\bverdict:\s*'([^']+)'", obj).group(1)
        title = re.search(r"\btitle:\s*'((?:[^'\\]|\\.)*)'", obj).group(1).replace("\\'", "'")
        lemma = re.search(r"\blemma:\s*'([^']+)'", obj).group(1)
        event_spec = re.search(r"\bevent:\s*'([^']+)'", obj).group(1)
        history_spec = re.search(r"\bhistory:\s*'([^']+)'", obj).group(1)
        clauses_raw, _ = _balanced(obj, obj.index("[", obj.index("clauses:")), "[", "]")
        clauses = [c.strip() for c in clauses_raw.split(",") if c.strip()]
        failm = re.search(r"\bfails:\s*(\d+)", obj)

        ev = _named_fields(event_spec)
        st = _named_fields(history_spec)
        out[letter] = {
            "id": letter,
            "lemma": lemma,
            "title": title,
            "verdict": verdict,
            "fails": int(failm.group(1)) if failm else None,
            "clauses": clauses,
            "event_shared": {
                "roofAt": _int(ev["roofAt"]), "floorAt": _int(ev["floorAt"]),
                "holeOpenAtJ": _bool(ev["holeOpenAtJ"]), "spinAtK": _bool(ev["spinAtK"]),
            },
            "setup_step": {
                "clearedRows": [_int(x) for x in
                                _balanced(history_spec, history_spec.index("["), "[", "]")[0].split(",")
                                if x.strip()],
                "wasSpin": _bool(st["wasSpin"]), "garbageRows": _int(st["garbageRows"]),
            },
        }
    return out


# ---------------------------------------------------------------------------------------------
# Cross-check, and the canonical record built once agreement is proven.
# ---------------------------------------------------------------------------------------------
def cross_check(dfy: dict[str, dict], boards: dict[str, dict]) -> list[str]:
    problems: list[str] = []

    def eq(letter, what, a, b):
        if a != b:
            problems.append(f"{letter}: {what} disagree — Dafny {a!r} vs boards {b!r}")

    if sorted(dfy) != IDS:
        problems.append(f"Dafny examples are {sorted(dfy)}, expected {IDS}")
    if sorted(boards) != IDS:
        problems.append(f"board examples are {sorted(boards)}, expected {IDS}")

    for letter in IDS:
        if letter not in dfy or letter not in boards:
            continue
        d, t = dfy[letter], boards[letter]

        eq(letter, "lemma name", d["lemma"], t["lemma"])
        if not t["lemma"].startswith(f"Example{letter}_"):
            problems.append(f"{letter}: board lemma {t['lemma']!r} is not an Example{letter}_ lemma")

        # shared Event fields
        for f in ("roofAt", "floorAt", "holeOpenAtJ", "spinAtK"):
            eq(letter, f"event.{f}", d["event"][f], t["event_shared"][f])

        # the TS `history` is the Dafny setup step h[0]
        eq(letter, "setup step", d["history"][0], t["setup_step"])

        # verdict: the board's word vs the verdict PROVEN by the Dafny ensures
        eq(letter, "verdict", d["verdict"], t["verdict"])

        # the failing clause: the board's `fails` vs the clause the ensures negate
        eq(letter, "failing clause", d["fails_clause"], t["fails"])

        # the board's `clauses` array, tied to the machine-checked event flags and the verdict
        problems += _check_clauses(letter, d["verdict"], d["fails_clause"], d["event"], t["clauses"])

    return problems


# The four clause tokens as they appear in example-boards.ts. `clauses[i]` is `true`/`false` for
# a settled clause, or `'partial'` for clause 4 of the loose-reading accept (B), where a single
# line is enough under one reading of "triple line(s)" and not the other.
_CLAUSE_TOKENS = {"true", "false", "'partial'"}


def _check_clauses(letter: str, verdict: str, fails: int | None, event: dict,
                   clauses: list[str]) -> list[str]:
    """The board's four-clause annotation, checked against what is independently known.

    Not every clause is derivable from parsing alone (clause 3 needs the board simulated), so this
    does NOT reconstruct the whole array — E and G legitimately carry two false clauses because a
    gap that never closes is also a gap no plain clear took. It pins the parts that ARE known:
    clauses 1 and 2 are exactly the event flags, and a rejection must mark its headline clause
    false.
    """
    out: list[str] = []
    if len(clauses) != 4:
        return [f"{letter}: clauses array has {len(clauses)} entries, expected 4"]
    bad = [c for c in clauses if c not in _CLAUSE_TOKENS]
    if bad:
        return [f"{letter}: unrecognised clause token(s) {bad}"]

    # clause 1 is Tucked == spinAtK; clause 2 is HolePreExisted == holeOpenAtJ. A board that draws
    # the flag one way and annotates the clause the other contradicts itself.
    for idx, flag in ((0, "spinAtK"), (1, "holeOpenAtJ")):
        want = "true" if event[flag] else "false"
        if clauses[idx] != want:
            out.append(f"{letter}: clause {idx + 1} is {clauses[idx]!r} but {flag} is {event[flag]}")

    if verdict == "accept":
        if any(c == "false" for c in clauses):
            out.append(f"{letter}: accepted, but a clause is marked false: {clauses}")
    elif verdict == "accept-loose":
        if clauses[3] != "'partial'":
            out.append(f"{letter}: loose accept must mark clause 4 'partial', got {clauses[3]!r}")
    else:  # reject
        if fails is None:
            return out + [f"{letter}: rejected but no failing clause was identified"]
        if clauses[fails - 1] != "false":
            out.append(f"{letter}: rejected on clause {fails}, but clauses[{fails - 1}] "
                       f"is {clauses[fails - 1]!r}, not false")
    return out


def build(dfy: dict[str, dict] | None = None, boards: dict[str, dict] | None = None) -> dict:
    """The canonical parsed record — call only after cross_check returns []."""
    dfy = dfy if dfy is not None else parse_dafny()
    boards = boards if boards is not None else parse_boards()
    examples = []
    for letter in IDS:
        d, t = dfy[letter], boards[letter]
        examples.append({
            "id": letter,
            "lemma": d["lemma"],
            "title": t["title"],
            "verdict": d["verdict"],
            "failsClause": d["fails_clause"],
            "clauses": dict(zip(CLAUSE_KEYS, [_clause_val(c) for c in t["clauses"]])),
            "event": d["event"],
            "history": d["history"],
        })
    return {
        "_note": ("The seven worked T-Spin Forecast examples, parsed from the machine-checked "
                  "Dafny witnesses in spec/ForecastExamples.dfy and cross-checked against the drawn "
                  "boards in spec/example-boards.ts. Regenerate with "
                  "`python3 -m pipeline.forecast_examples --write`."),
        "sources": ["spec/ForecastExamples.dfy", "spec/example-boards.ts"],
        "clauseOrder": CLAUSE_KEYS,
        "examples": examples,
    }


def _clause_val(token: str):
    """A boards clause token -> a JSON value: True / False / "partial"."""
    return {"true": True, "false": False, "'partial'": "partial"}[token]


def render_json(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------------------------
# CLI / gate
# ---------------------------------------------------------------------------------------------
def _run_check() -> int:
    dfy, boards = parse_dafny(), parse_boards()
    problems = cross_check(dfy, boards)
    for p in problems:
        print("FAIL  " + p, file=sys.stderr)
    if problems:
        print(f"{len(problems)} disagreement(s) between the Dafny lemmas and the drawn boards",
              file=sys.stderr)
        return 1
    want = render_json(build(dfy, boards))
    have = ARTIFACT.read_text(encoding="utf-8") if ARTIFACT.exists() else None
    if have != want:
        where = "missing" if have is None else "stale"
        print(f"FAIL  {ARTIFACT.relative_to(ROOT)} is {where}; run "
              f"`python3 -m pipeline.forecast_examples --write`", file=sys.stderr)
        return 1
    print(f"ok — {len(dfy)} forecast examples agree across "
          f"{DFY.name} and {BOARDS.name}, and {ARTIFACT.name} is byte-identical")
    return 0


def selftest() -> int:
    """Prove the gate has teeth: perturb each source in a way that must be caught."""
    dfy = parse_dafny()
    boards = parse_boards()
    if cross_check(dfy, boards):
        print("SELFTEST FAIL: the real files do not agree", file=sys.stderr)
        return 1

    # 1. a flipped Event flag on the boards side (holeOpenAtJ) must be caught
    import copy
    b = copy.deepcopy(boards)
    b["C"]["event_shared"]["holeOpenAtJ"] = not b["C"]["event_shared"]["holeOpenAtJ"]
    if not cross_check(dfy, b):
        print("SELFTEST FAIL: a flipped holeOpenAtJ was not caught", file=sys.stderr)
        return 1

    # 2. a wrong verdict on the boards side must be caught
    b = copy.deepcopy(boards)
    b["A"]["verdict"] = "reject"
    if not cross_check(dfy, b):
        print("SELFTEST FAIL: a wrong verdict was not caught", file=sys.stderr)
        return 1

    # 3. a mis-stated failing clause must be caught
    b = copy.deepcopy(boards)
    b["C"]["fails"] = 3
    b["C"]["clauses"] = ["true", "true", "false", "true"]
    if not cross_check(dfy, b):
        print("SELFTEST FAIL: a mis-stated failing clause was not caught", file=sys.stderr)
        return 1

    # 4. a changed setup step (garbageRows) must be caught
    b = copy.deepcopy(boards)
    b["E"]["setup_step"]["garbageRows"] += 1
    if not cross_check(dfy, b):
        print("SELFTEST FAIL: a changed setup step was not caught", file=sys.stderr)
        return 1

    # 5. the verdict is DERIVED from Dafny, not trusted. Negating ExampleA's forecast conclusion
    #    must re-derive off "accept" — proving the boards cannot assert a verdict the lemma refutes.
    if _verdict_from_ensures("ensures !IsForecastShape(h, e)") != "reject":
        print("SELFTEST FAIL: a negated forecast conclusion did not read as a rejection",
              file=sys.stderr)
        return 1
    d = copy.deepcopy(dfy)
    d["A"]["verdict"], d["A"]["fails_clause"] = "reject", 2
    if not cross_check(d, boards):
        print("SELFTEST FAIL: a Dafny/boards verdict disagreement was not caught", file=sys.stderr)
        return 1

    print("selftest ok — the gate catches a flipped flag, a wrong verdict, a mis-stated clause, "
          "a changed step, and a flipped Dafny conclusion")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--json" in argv:
        dfy, boards = parse_dafny(), parse_boards()
        problems = cross_check(dfy, boards)
        if problems:
            for p in problems:
                print("FAIL  " + p, file=sys.stderr)
            return 1
        sys.stdout.write(render_json(build(dfy, boards)))
        return 0
    if "--write" in argv:
        dfy, boards = parse_dafny(), parse_boards()
        problems = cross_check(dfy, boards)
        if problems:
            for p in problems:
                print("FAIL  " + p, file=sys.stderr)
            print("refusing to write: the two sources disagree", file=sys.stderr)
            return 1
        ARTIFACT.write_text(render_json(build(dfy, boards)), encoding="utf-8")
        print(f"wrote {ARTIFACT.relative_to(ROOT)} ({len(dfy)} examples)")
        return 0
    return _run_check()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
