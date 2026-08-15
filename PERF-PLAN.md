# Efficiency plan — measured, not guessed

Scope: every executable in the repo (Python pipeline, TypeScript simulator, shell gates).
Method: profile first, pick the target by measured share, replace the *algorithm* rather than
tune the constant, and gate each change on byte-identical output.

Nothing here changes what any gate *decides*. Every item below is a pure
performance rewrite whose acceptance test is "same output, same verdict, less time". A
speed-up that weakens a gate is a regression, not an optimisation — that is the one
invariant this plan may not trade against.

## How the repo was scanned

1. `wc -l` over every `.py` / `.ts` / `.dfy` / `.sh` to find where the code volume is.
2. `cProfile` on each Python gate, `--cores`-free wall clock on each shell gate,
   `performance.now()` micro-benchmarks on the simulator hot paths.
3. Ranked by **measured total wall clock in CI**, which is per-session × 4 sessions for the
   matrix jobs — not by how slow a single invocation feels.

Timings below are on this machine (darwin/arm64, Python 3.12.3, bun 1.2.8), taken on
`main` at `b019718`.

## Measured baseline

| Target | Wall clock | Profiler says | CI multiplier |
|---|---|---|---|
| `pipeline/claims/equiv.py` | 18.6 s (07‑24, the *smallest* session) | 88 % `copy.deepcopy` | not in CI, run by hand |
| `pipeline/check_dead_consts.py` | 9.1 s | 4 376 whole-body regex scans | × 4 sessions = 36 s |
| `bun test` (simulator suite) | 17.5 s | `bestTspin` BFS ≈ 0.48 ms/board | × 1 |
| `pipeline/check_rate_coverage.py` | 3.4 s | 68 % `copy.deepcopy` | × 4 sessions = 14 s |
| `pipeline/check_lemma_vacuity.py` | 2.4–3.5 s | already optimised (127× in a prior pass) | × 4 |
| every other Python gate | ≤ 0.03 s | — | — |

The long tail is genuinely flat: seven of the nine Python gates finish in 30 ms. There is no
diffuse "make everything faster" work to do — the cost is concentrated in four places, and
three of them are the same mistake made twice.

## The root cause, stated once

Three of the five hot spots are instances of one design error:

> **an O(n) copy is paid for an O(1) edit.**

`equiv.py` and `check_rate_coverage.py` both answer the question *"if I perturb this one
datum, which claims flip?"*. Both answer it by `copy.deepcopy(facts)` — rebuilding a
300–480 KB object graph — then writing one integer into the copy. `equiv.py` does this 4 440
times per session; `check_rate_coverage.py` 324 times. That is 76.5 million `deepcopy` calls
to change 4 440 integers.

This is not two bugs in two files. It is one missing abstraction, and per the repo's own L9
rule the fix is the abstraction, not two patches. The literature name for the general
problem is *persistence* (Driscoll, Sarnak, Sleator & Tarjan, **"Making Data Structures
Persistent"**, JCSS 38(1), 1989) — but full persistence is not needed here, because no caller
keeps a mutant after evaluating it. The cheaper exact instrument is the **make/unmake** (undo
log) discipline that game-tree search has used since Knuth & Moore's alpha-beta analysis
(*Artificial Intelligence* 6(4), 1975): apply the edit in place, evaluate, apply the inverse.
Cost drops from O(|facts|) to O(1) per mutant with *identical* semantics, provided the
evaluated predicates do not mutate `facts` — which they do not, being `eval` of a pure
comparison expression.

## Work items

Ordered by measured payoff. Each is independently landable and independently revertible.

### A. One perturbation module, make/unmake instead of deepcopy

**New:** `pipeline/perturb.py` — a context manager that writes a value into a JSON path,
yields, and restores the previous value on exit, including the multi-leaf case
(`round_winner` also rewrites both players' `alive` flags).

**Callers:** `pipeline/claims/equiv.py::apply_mutation`, `pipeline/check_rate_coverage.py::_mutated`.

Expected: removes 88 % of `equiv.py` and 68 % of `check_rate_coverage.py`.

**Correctness gate.** The restore must be exact, and "it looked fine" is not evidence. Two
checks, both required:

- output of both tools byte-identical to the captured baseline on all four sessions;
- a **self-check** asserting `facts` is unchanged after the whole sweep, compared by
  `json.dumps(..., sort_keys=True)` against a snapshot taken before it. An undo log that
  restores 4 439 of 4 440 sites would otherwise silently corrupt every later mutant — this is
  the one failure mode deepcopy structurally cannot have, so trading it away requires the
  assertion to be *in the code*, not in a one-off manual run.

### B. `check_dead_consts` — multi-pattern matching in one pass

Today: for each of ~4 500 const names, `re.search(rf"\b{n}\b", body)` over the ~600 KB
concatenated lemma text. That is O(|consts| × |body|) with a fresh regex compile per const.

The classical instrument is **Aho–Corasick** (*"Efficient string matching: an aid to
bibliographic search"*, CACM 18(6), 1975): one automaton over all patterns, one pass over the
text, O(|text| + Σ|patterns| + matches).

For this input a strictly simpler construction is *exactly equivalent* and beats it: every
pattern is `\b<word>\b` where the word is `\w+`, so a const is read iff its name appears as a
whole-word token. Tokenise the body once with `re.findall(r"\w+", body)`, build a `set`, and
test membership in O(1). Same answer by definition of `\b`, one pass, no automaton.

Expected 9.1 s → well under 0.1 s. Gate: identical output on all four sessions, plus a
regression test that a genuinely dead const is still reported (the check must be able to fail).

### C. `equiv.py` implication search — bitsets

`implies(g, h)` walks two 4 441-element Python lists per call, and the uncovered-claim
fallback tries every *pair* of generated claims — O(|hand| × |gen|² × |mutants|), i.e. up to
2 926 pairs × 4 441 samples for a single uncovered hand claim.

Truth vectors are three-valued (`True` / `False` / `None` for "the mutation broke an index"),
which encodes exactly into **two Python ints used as bitmaps**: `defined` and `value`. Then

```
implies(g, h)  ==  (g.val & g.def & h.def & ~h.val) == 0   and   (g.def & h.def) != 0
conjunction    ==  (a.def & b.def, a.val & b.val)
```

Python's arbitrary-precision ints make each of those a handful of machine words, so a
4 441-sample comparison becomes ~70 word operations instead of 4 441 interpreter steps. This
is the standard **word-parallel / bit-parallel** trick behind Shift-Or approximate matching
(Baeza-Yates & Gonnet, CACM 35(10), 1992) and bitset dataflow analysis.

Gate: identical `covered` / `uncovered` / `untested` partition and identical printed report.

### D. `bestTspin` BFS — direct-address visited set

`pipeline/sim/forecast.ts` keys its BFS `seen` set on a built string, `` `${rot}:${col}:${row}` ``,
and pushes `{p, rot, kick}` objects onto a queue. Per board that is hundreds of string
constructions plus hash lookups; measured 0.48 ms/board, and the corpus test runs 7 544
boards.

The state is three small integers. `bfs-cap.ts` already establishes the reachable ranges as an
*observation* (rotation 0–3, anchor column −1…8, rows unbounded below but measured within
[−2, 39]). So encode the state as one integer and use a **direct-address table**
(Cormen et al., *Introduction to Algorithms*, §11.1) — a `Uint8Array` — instead of a hash set
of strings.

The row range is the catch: `bfs-cap.ts` is explicit that rows are **not** bounded by the
engine, only by a kick-table argument nobody has proved. So the encoding must not *assume* a
range — it takes the direct-address fast path inside the measured window and falls back to the
existing `Set` for any state outside it. That keeps the table a pure optimisation and leaves
`bfs-cap.ts`'s standing warning true.

Gate: `bun test` green, plus a differential harness asserting old and new `bestTspin` agree on
every board of a randomised corpus — the same shape of evidence `bfs-cap.ts` already uses.

### E. `mutation_test.sh` — noted, deliberately not done

Each mutant re-runs `dafny verify Facts.dfy Claims.dfy`, re-proving **every** lemma to learn
about **one** constant, so the sweep samples 12 of ~4 500 consts and still costs ~90 s.
Program slicing (Weiser, *"Program Slicing"*, ICSE 1981) applied to the const→lemma reference
graph — which `check_dead_consts` already computes — would verify only the lemmas that
mention the mutated const, making an exhaustive sweep affordable.

Not attempted in this pass. It changes what a gate *proves*, not just how fast it runs: a
sliced verification is only sound if the slice provably contains every lemma that could
break, and `Claims.dfy` lemma bodies are empty but their `ensures` clauses are generated —
establishing that closure is a correctness argument, not a refactor. It belongs in its own
change with its own review, and `check_smt --mutate` already provides the fast anti-vacuity
signal on every push.

## Results

Measured the same way as the baseline, both trees on the same machine and the same inputs.
"identical" is `diff` of the two runs' full stdout+stderr, not a spot check.

| target | before | after | speedup | output |
|---|---|---|---|---|
| `check_dead_consts` 07‑22 | 3.56 s | 0.03 s | **109×** | identical |
| `check_dead_consts` 07‑24 | 2.96 s | 0.03 s | **102×** | identical |
| `check_dead_consts` 07‑28 | 9.06 s | 0.04 s | **206×** | identical |
| `check_dead_consts` 08‑01 | 7.90 s | 0.04 s | **188×** | identical |
| `check_rate_coverage` 07‑22 | 4.44 s | 3.08 s | 1.4× | identical |
| `check_rate_coverage` 07‑24 | 2.26 s | 1.65 s | 1.4× | identical |
| `check_rate_coverage` 07‑28 | 3.53 s | 2.30 s | 1.5× | identical |
| `check_rate_coverage` 08‑01 | 2.19 s | 1.50 s | 1.5× | identical |
| `claims.equiv` 07‑22 | 51.79 s | 13.88 s | 3.7× | identical |
| `claims.equiv` 07‑24 | 18.36 s | 4.60 s | 4.0× | identical |
| ↳ both superseded 2026‑08‑15 — see the note below the table | | | | |
| **total** | **106.05 s** | **27.16 s** | **3.9×** | |
| `bun test` (130 tests) | 17.5 s | 14.4 s | 1.2× | 130 pass, 0 fail |

**The two `claims.equiv` rows are no longer that command's runtime, and the reason is not a
regression.** On 2026-08-15 the single-value family stopped drawing one perturbation kind per
site and started enumerating every kind, because the drawn version made the published coverage
figure move with `--seed`. That is ~5× the mutants by construction: 07-22 goes 13.88 s → 71.5 s
and 07-24 4.60 s → 23.7 s. The make/unmake speedup this table records is still in there and
still worth its 3.7-4.0× — the work simply got five times larger, deliberately. Kept rather than
rewritten, because a speedup table that silently absorbs a scope change stops being a measurement.

Two numbers came in under what the profiler implied, and they are worth recording as
calibration rather than quietly rounding up:

- **`check_rate_coverage` gained 1.4–1.5×, not the 3× that "68 % of the run is deepcopy"
  suggests.** `cProfile` charges per function call, and `deepcopy` is millions of tiny
  recursive calls, so instrumentation inflates its share far more than it inflates the
  `eval` of a claim predicate. The 68 % was a profiler artefact; the wall-clock share was
  nearer 30 %. Profile to find *where*, but only wall clock says *how much*.
- **The BFS visited set gained 1.31×, not the order of magnitude a string-keyed hash set
  usually costs.** A differential harness over 3 000 boards confirmed 0 mismatches and
  timed both: the search's real cost is `hardDrop` / `tryMove` / `tryRotate` walking the
  board, not the `seen` lookup. Removing the string keys was worth doing and was not the
  bottleneck. The remaining cost would need column-height precomputation inside
  `vendor/core/srs.ts`, which is the vendored engine that defines correctness here.

### What was verified, and what was not

Against the repo's own 8-layer standard, this change reaches layers 1, 2, 3 and 7:

- **integration** — `bin/verify-session` passes on all five artefacts; every other CI gate
  passes on all four sessions; `bun test` 130/130; `bin/build-docs --check` clean.
- **differential** — every touched tool's full output is byte-identical to the baseline
  captured before the first edit. For `bestTspin`, a 3 000-board harness compares against a
  verbatim copy of the old implementation.
- **mutation (layer 3)** — both new guards were planted and observed to fail:
  disabling the undo loop in `perturb.py` makes `check_rate_coverage` die on the
  fingerprint assertion (`pipeline/test_perturb.sh` case 5), and loosening the
  `check_dead_consts` tokeniser to a substring test makes its `--selftest` fail cases 3
  and 4. Both are wired into CI.
- **not done**: property-based testing over random fact bases (layer 4), coverage
  measurement of the new lines (layer 5). Neither is load-bearing for a change whose
  acceptance test is byte-identical output on the real corpus, but neither was run.

## Out of scope

- **Rewriting the simulator on bitboards.** A 40×10 `Uint16Array` with `row === 0x3FF` for a
  full row would beat the array-of-arrays representation everywhere, but it touches the
  verified forecast semantics across a dozen files. The evidence chain in `forecast.ts` is
  the asset here; a representation change that invalidates it is a bad trade for a suite that
  already finishes in 17.5 s.
- **Parallelising the CI matrix further.** Already six jobs; the tail is Dafny, not Python.
- Micro-tuning the seven gates that run in 30 ms.
