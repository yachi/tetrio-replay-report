# Plan: `tetrio-replay-report` — a repo that turns a batch of .ttrm replays into a proof-backed Cantonese report

Decisions locked: **public repo**, **everything included** (replays + reports + full pipeline), goal = **repeatable: drop in a batch of replays → get a report**.

## 0. What the repo is

Not an archive with two reports in it. A **tool** (`pipeline/`) plus **data** (`sessions/`), where adding a session is one command plus an optional prose pass.

```
tetrio-replay-report/
├── README.md                  # what it is, honest trust chain, how to run
├── LICENSE                    # MIT for code (data note in README)
├── .gitattributes             # *.ttrm linguist-vendored + -diff (65k-char single-line JSON)
├── .gitignore                 # .playwright-cli/ __pycache__/ .playwright/ shots/ *.zip
├── pipeline/
│   ├── extract.py             # extractor A (python)      — parameterized by session dir
│   ├── extract2.ts            # extractor B (typescript)  — independent impl, diff gate
│   ├── claims/
│   │   ├── generators.py      # ~20 claim FAMILIES (the core new work — see §2)
│   │   ├── dafny_lib.py       # generic emitters harvested from codegen_dafny.py
│   │   └── build_claims.py    # facts.json → claims.json (canto + python_check + dafny body)
│   ├── codegen_dafny.py       # claims.json → Facts.dfy + Claims.dfy   (already data-driven)
│   ├── check_claims.py        # python_check gate
│   ├── build_proof_map.py     # verifier output → proof map (never aspirational)
│   ├── build_report.py        # facts + claims + proof map + prose → report.html
│   ├── templates/             # design system, SVG chart renderers, appendix (from session-1/2 HTML)
│   ├── mutation_test.sh       # anti-vacuity gate
│   └── gen_consistency.sh     # codegen byte-identity gate
├── sessions/
│   ├── 2026-07-22/  replays/*.ttrm  facts.json  claims.json  dafny/  prose/  report.html
│   └── 2026-07-24/  (same shape; also keeps the lighter report-2026-07-24.html)
├── tools/analyzer.html        # standalone drop-a-.ttrm analyzer (client-side)
├── docs/                      # GitHub Pages: index + one page per session report
├── bin/new-session            # the one command (see §3)
└── .github/workflows/verify.yml   # CI re-runs every gate on push (SHA-pinned actions)
```

## 1. Reuse audit (measured, not assumed)

| Component | Today | Repo |
|---|---|---|
| `extract.py` / `extract2.ts` | filename glob hardcoded per session | parameterize input dir + ordering rule → **reuse as-is** |
| `check_claims.py` | already generic (argv) | **reuse unchanged** |
| `codegen_dafny.py` Facts emitter + helper lib | generic (`bal`, `sum_rf`, `sumsq_rf`, `max_pp_is`, `rmin_is`, `rmax_is`, `lb_max_is`, `variance`, `count_expr`) | **promote to `dafny_lib.py`** |
| `codegen_dafny.py` claim bodies | **hand-written `bC001…bR024` per session** ← the bottleneck | replaced by generators (§2) |
| Claim text + predicates | hand-written by 2 opus agents per session | auto-generated for ~85%, agents add flavor |
| `mutation_test.sh` / `gen_consistency.sh` / `build_proof_map.py` | near-generic | parameterize paths → **reuse** |
| report HTML | prose+layout hand-built per session | split: auto layer (scoreboard, match cards, charts, appendix) + prose layer |

## 2. Core work: claim generators (the thing that makes it repeatable)

One generator = one claim family = works on every future session. Each emits all three artifacts so nothing is hand-written downstream:

```python
class Generator:
    def find(facts) -> list[Params]      # locate the instances in THIS session (argmax, streak scan, …)
    def canto(p)   -> str                # 口語廣東話 sentence, with 約 + floor convention applied
    def check(p)   -> str                # python_check expression (integer-only)
    def dafny(p)   -> str                # lemma body via dafny_lib helpers
```

Families harvested from the 52 existing claims (each already proven twice):

**Structural / score** — series result; round-win totals; per-match final scores; sweeps (5-0) and who owns them; deciders (full-length matches); match-win order.
**Superlatives** — session-max single-round APM / VS / spike / combo / B2B / T-spins; longest & shortest round; highest match-level APM; per-player maxima. (`max_pp_is` / `rmin_is` / `lb_max_is` already exist.)
**Streaks** — longest consecutive round-win run, with the cross-match-boundary disclosure baked into the wording (session-2 review finding, now permanent).
**Pressure / comeback** — rounds won while facing more queued attack; queued-vs-materialized cancellation totals (semantics enforced in wording, not left to a writer).
**Player aggregates** — totals & per-piece rates for attack, quads, T-spin subtypes, all-clears, holds, finesse faults/perfects, inputs; kills.
**Consistency** — integer variance identity `n·Σx² − (Σx)²` comparisons (already integer-only).
**Situational** — fast-round (<40s) records, high-APM-round records, bounce-back-after-loss rates, sweep-match collapse stats.

Guardrails encoded once, so past bugs cannot recur:
- floor convention for 「約N秒」 (session-2 minor m5)
- streak wording must disclose match boundaries (session-2 minor m2)
- queued vs materialized garbage phrasing (session-1 recurring)
- no simplified glyphs in generated text (assert on output)
- kills ≡ round wins in 1v1 — never presented as independent corroboration (session-2 minor m3)

**Validation gate for this refactor:** regenerate both existing sessions with the generators and diff against the committed hand-made ledgers. Target ≥85% of the 52 claims reproduced with an equivalent predicate; the remainder stay as per-session bespoke entries. This is the phase's acceptance test — no hand-waving.

## 3. The one command

```fish
bin/new-session sessions/2026-08-01 ~/Downloads/replay-batch/
```
Runs, failing loudly at the first bad gate:
1. copy/normalize replays → `sessions/<id>/replays/`
2. both extractors → `facts.json` + `facts2.json`, **diff gate**
3. `build_claims.py` → `claims.json` (auto families) + `check_claims.py` **100% gate**
4. `codegen_dafny.py` → `dafny/*.dfy`; `dafny verify` **0-errors gate**; `mutation_test.sh` **all-killed gate**; `gen_consistency.sh` **byte-identity gate**
5. `build_proof_map.py` → statuses from real verifier output only
6. `build_report.py` → `report.html` with charts, scoreboard, match cards, 52-row appendix — prose sections marked `TODO`
7. print a summary table + the paths

Then the optional prose pass (Claude Code, the phase that genuinely needs judgment): narrative beats + coaching recommendations written against the auto claims, re-run `build_report.py`. The adversarial audit prompt ships in the repo as `docs/AUDIT-PROMPT.md` so the review loop is reproducible too.

## 4. CI + Pages

- `.github/workflows/verify.yml`: on push/PR — install Dafny, then re-run for every session: extractor diff → `check_claims` → `dafny verify` → mutation test → consistency. **The repo's central claim is "these numbers are proven"; CI is what keeps that true.** Actions SHA-pinned.
- GitHub Pages from `docs/`: index listing sessions (date, players, result) → each report + the analyzer tool. Reports are already self-contained, so publishing is a copy.
- Badge in README: verification workflow status.

## 5. Migration of existing work

Both sessions land intact, then get re-verified through the new pipeline (their committed reports stay as-is; only the tooling path changes). Excluded from git: `.playwright-cli/`, `__pycache__/`, `.playwright/`, `proof/shots/`, `*.zip` (~11 MB of QA screenshots). Payload ≈ **17 MB / 83 files** — comfortable.

Session-2's `proof/` (the lighter 20-claim report and its Dafny layer) moves under `sessions/2026-07-24/` as a second artifact rather than being deleted.

## 6. Phasing

| Phase | Output | Ships when |
|---|---|---|
| P1 | Repo created, both sessions + reports + existing scripts committed, README, .gitignore/.gitattributes, Pages live | immediately usable as an archive |
| P2 | CI green: every gate re-runs on push for both sessions | proves the archive's claims stay honest |
| P3 | `pipeline/` extracted & parameterized; both sessions reproducible from it | tool separated from data |
| P4 | Claim generators + `build_claims.py`; ≥85% reproduction gate against existing ledgers | **new sessions become one command** |
| P5 | `build_report.py` templating; prose-only agent pass | full loop |

P1+P2 are mechanical. P4 is the real engineering.

## 7. Open risks

- **Third-party data**: public repo publishes pinglamb's replays, TETR.IO user ID, and a critique of their weaknesses. Worth a heads-up to them; README should credit both players. An `--anonymize` flag in the pipeline is cheap insurance if they'd rather not be named.
- **Generator coverage**: if a future session's drama doesn't fit a family, the pipeline still produces a valid report — bespoke claims are additive, never required.
- **Dafny in CI**: pin the Dafny version (4.11.0 locally); verify time is ~3-5s per session, so CI stays fast.
- **`.ttrm` churn**: single-line JSON; marked `-diff` so PRs stay readable.

---

## P4 — DONE (2026-07-25)

Claim generators shipped. A session's ledger and its Dafny proofs are now generated from
`facts.json` by `bin/new-session`; only the Cantonese prose still needs a person.

**Design.** A family never writes a predicate string. It builds a *spec* (a nested dict
in `pipeline/claims/spec.py`) which is rendered to a Python predicate and to a Dafny
`ensures` clause by two backends, so the checked statement and the proved statement
cannot drift apart. 32 families live in `pipeline/claims/generators.py`.

**Measured coverage** (`pipeline/claims/equiv.py`). Comparing generated to hand-written
predicates by string is useless — every predicate is True on the real data. Instead every
single-value mutation of the dataset is applied (exhaustive: 4,440 sites for the 7-match
session, 7,019 for the 10-match one) and a hand claim counts as covered only when a
generated claim's truth is impossible without it, and both are falsifiable somewhere.

| Session | Coverage | Identical behaviour |
|---|---|---|
| 2026-07-22 (10 matches, 54 hand claims) | 45/53 testable = **85%** | 24 |
| 2026-07-24 (7 matches, 52 hand claims) | 48/49 testable = **98%** | 28 |

Combined 93/102 = **91%**, clearing the ≥85% acceptance gate. Claims no mutation can
falsify are reported separately rather than counted as covered.

**Bugs this phase's own gates caught**
* the "only one decider" claim restated that match's score without proving it was the
  *only* one — fixed by adding a match-margin counter to the algebra
* `total_rounds` rendered to Dafny as a literal, making "50 rounds" the tautology
  `50 == 50` — real in Python, vacuous in Dafny; now the sum of the `nrounds` consts
* `Facts.dfy` emitted the whole dataset, leaving dead consts no lemma reads, so mutation
  survivors were meaningless — now only load-bearing data is emitted
* `+1` mutations could not kill values that are only constrained beyond a threshold; the
  operator escalates before calling a mutant a survivor (14/14 killed)

## P5 — in progress

Report templating: `build_report.py` generating the scoreboard, match cards, charts and
appendix from `facts.json` + the ledger, leaving prose sections as the only hand-written
part. That closes the loop from replays to published report.

**Shipped (2026-07-25): the `chart-data` island.** Every chart in the report — the per-match
scoreboard strip, the VS small multiples, the clear-type bars, the tape chart, the match
timeline — reads one JSON island that until now was written by hand. Nothing tied it to
`facts.json`, so a chart could disagree with the proved data and no gate would notice; in a
repo whose whole claim is "these numbers are checked", that was the largest remaining hole.

`pipeline/chart_data.py` derives it, `pipeline/build_report.py` injects it into a marker
region, and `--check` fails CI if the committed report differs from what `facts.json`
generates.

Validation, in the same style as P4:
* the generator reproduces both committed islands exactly on the first run — every count,
  every float — with a single addition: session 2026-07-22's island was missing `kills`
  (43/36), which 2026-07-24's already carried
* the drift gate was mutation-tested (perturb one committed value → `--check` exits 1;
  restore → 0), so it is not decorative
* both reports were re-rendered in a browser: 10/7 match cards, 10/7 small multiples, both
  charts, 110 badges, 54/52 appendix rows, 158/100 round rows, no console errors

**Next in P5**, each a new entry in `build_report.SECTIONS`:
1. hero + scoreboard (needs a per-session prose file for the title/tagline/lede, which is the
   design decision the rest of P5 rests on)
2. match cards — the `match-copy` island, which is prose keyed by match index
3. appendix — folds in the three `innerHTML` sites, since the generator can build those rows
   with `textContent` instead of string concatenation
