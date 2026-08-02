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

**Shipped (2026-07-25): the hero and scoreboard**, and with it the prose split the rest of P5
follows. `pipeline/hero.py` derives the date, both player names and the series score from
`facts.json`; the headline, taglines, lede and the optional eyebrow kicker come from
`<report_dir>/prose/hero.json`. Derived values are HTML-escaped; prose is inserted raw because
it legitimately carries `<span class="hl-y">`, `<strong>` and badge spans.

Validation:
* both committed heroes were *extracted* into prose files and regenerated **byte-for-byte** —
  the migration only wrote a prose file where the round-trip was exact, so no prose was
  silently rewritten. The reports' only diff is the two marker lines.
* five adversarial probes, all caught: hero drift vs the committed report, a simplified glyph
  in prose, an empty prose field, a missing prose file, and a session whose replay timestamps
  disagree with the directory it was dropped into
* both heroes re-rendered in a browser: one `.hero`, correct eyebrow (including 07-24's
  第二回合 kicker), score in player order (6:4 / 3:4), taglines, and every badge resolving

**Shipped (2026-07-25): the match cards.** `pipeline/matches.py` generates the `match-copy`
island from `<report_dir>/prose/matches.json`; the card's numbers (score, winner, the
per-round pip trail) already came from the chart island.

The interesting part was what had to stop being code. Two editorial constants were baked into
each report's inline script — `m.index === 7` (which card gets the spotlight) and a literal
`data-claim="C026"` on every card's score — and they differed per session, which is a large
part of why the script could not be shared. Both are now `hero_match` and `score_claim` in the
prose file. The score itself is built from DOM nodes instead of an `innerHTML` string, and
reads `CD.players` by position rather than `m.score.yachi`, so that renderer no longer knows
who is playing. `chart_data` emits `players` for it.

Validation: both islands round-trip (the committed copy regenerates exactly); six adversarial
probes all caught (a match with no card, an unknown card index, an empty body, `hero_match`
out of range, a simplified glyph, and drift in the committed island); both reports re-rendered
— 10/7 cards, exactly one spotlight card at the right index, scores in player order with
07-22's C026 badge and none on 07-24, pip trails summing to 79/50 rounds, 110 badges, no
console errors.

**Shipped (2026-07-26): 全場之最 — the session records.** The generators already found every
session superlative; they were only readable as rows in the 52-row appendix, which is the wrong
form for a headline number. Nine stat tiles per session now carry them (single-round max VS,
APM, lines, spike, B2B, T-spin, combo, plus the longest and shortest round), ordered by how
much each measure actually says about who won the round — the paired AUC, so COMBO's tile comes
last rather than first.

Design references: Leetify's "NEW PERSONAL BEST" callouts (a superlative deserves a card, not a
table row) and Lichess's habit of stating the finding as a sentence under the figure. The form
follows the bundled `dataviz` procedure: a KPI row of stat tiles, no hover layer, proportional
figures (`tabular-nums` is for columns), identity as a coloured dot beside ink-coloured text,
and no new colours.

The load-bearing decision: **each tile's figure is read out of the claim's own spec** — the
operands of the equality Dafny proved — via `claim_cards.round_operand()`, never re-derived
from `facts.json`. Swap the literal in a spec and the tile changes with it; give a claim a spec
of another shape and it gets no tile at all rather than an invented figure. `match_apm_max` is
listed in the table on purpose so its exclusion prints in a footnote instead of vanishing. The
claim's full sentence sits under every figure, which is what keeps disclosures like
「呢個數字全場出現過 3 次」 attached to the number.

Also folded out: `pipeline/fmt.py` (the floored formatters) and `pipeline/claim_cards.py` (one
ledger + proof-map loader), both of which `build_round_table.py` now uses instead of its own
copies — its output verified byte-identical after the change.

This surfaced a **pre-existing inconsistency**, since fixed (below): the hand ledgers rounded
their 約 figures while the generated ledger floors them (C009 約262.6 vs G017 約262.5, one
integer).

## The 約 convention, enforced (2026-07-26)

45 rounded figures were rewritten to their floored values across both sessions — 25 + 6 in the
Cantonese and prose, 12 + 2 in `english_gloss`, which ships inside the claims island and is
therefore just as published. Every replacement was computed from `facts.json` and applied only
where the data gave exactly one floored candidate, so nothing but the last digit changed.

Three passes were needed, and each found what the previous one had missed — worth recording,
because the misses were all *scope* misses rather than logic errors:

1. one-decimal 約-figures in the ledgers and prose files
2. figures in seconds (「約128.6秒」 is the same artifact), and prose typed straight into
   `report.html` rather than into a prose file
3. two-decimal figures (`約1.84` — the pattern for one decimal never matched it) and the
   `~` / `≈` markers used in `english_gloss`

`pipeline/check_prose_figures.py` now closes the class instead of the instances: it resolves
every 約 / `~` / `≈` figure in every hand-written surface against `facts.json` and fails when no
datum floors to it but one rounds to it. Wired into CI per session. `check_claims` could never
have caught this — every predicate compares the integer, not the printed text.

### The second-order bug it caused

`codegen` builds each lemma's *name* from the claim's `english_gloss`, so correcting 14 glosses
renamed 14 lemmas and stranded 8 proof-map entries — badges pointing at lemmas that no longer
existed. Every existing gate stayed green: the verifier still reported 0 errors, and the
status check still counted 54/54 verified, because it only reads statuses. The maps were rebuilt
from real verifier output, and `pipeline/check_proof_links.py` now fails when any entry names a
missing lemma (mutation-tested). It runs per artefact in CI, plus once against the generated
`Claims.dfy` in the temp directory CI builds it in, since those lemmas are not committed.

Worth remembering as a pattern: a *derived identifier* (lemma name ← gloss text) turns a
cosmetic edit into a structural one. Nothing in the pipeline had declared that dependency.

## SMT-LIB as a third backend (2026-07-26)

**The finding that motivated it, measured not assumed:** all 106 hand lemmas and all 153
generated ones have **empty bodies**, and use no quantifiers, no functions and no loops. Dafny
was translating a ground arithmetic statement into Boogie, which generated a verification
condition, which Z3 evaluated. None of Dafny's proving machinery was in use — only its syntax,
and the Boogie layer that caused the balanced-tree workaround in `spec.bal`.

So `pipeline/claims/smt.py` renders the same specs to SMT-LIB 2.6, `pipeline/codegen_smt.py`
emits one self-contained `claims.smt2` per session (facts as `define-fun`, one
`(assert (not claim))/(check-sat)` per claim, every answer must be `unsat`), and
`pipeline/check_smt.py` gates it. Constant names match `Facts.dfy` exactly so the two backends
can be read side by side; sums are emitted n-ary because an s-expression has no AST-depth limit
to work around.

Measured over the same claims: **40 ms and 10 ms** versus Dafny's ~4.6 s and ~3 s. That is what
makes the anti-vacuity mutation test cheap enough to run on **every push** (`--mutate 12`, under
a second) instead of weekly — the mutation escalates (+1, +1000, far) because banded predicates
like `135000 <= v < 136000` survive +1 by design.

Validation: 77/77 and 76/76 `unsat`; the committed file regenerates byte-for-byte; 12/12
perturbations falsified at least one claim. Dafny stays exactly as it was — this is a
cross-check, not a replacement, and the report's badges still cite Dafny lemmas.

**Two encoding facts, both found by a solver refusing the file rather than by reasoning:**

* strings are **integer codes** with a legend in the header, not the `String` sort. The sort
  worked with z3 and cvc5 and locked everyone else out, which defeats the point of emitting a
  standard format so an independent solver can read it.
* the logic is **`QF_NIA`**, not `QF_LIA`. The integer variance identity squares a datum, and
  `QF_LIA` rejects `(* v v)` outright.

The second attempt at that first point also exposed a hole in the gate itself: with the wrong
logic declared, z3 answered nothing and printed `(error "logic does not support nonlinear
arithmetic")` per claim — and the token-based output parser read the words inside those errors
as claim ids and answers, so a **refused file reported 15 kills per mutation**. The parser is
line-based now, solver errors are a failure in their own right, and that is mutation-tested by
re-declaring the wrong logic.

### What CI caught that local runs did not (2026-07-28)

The first push with cvc5 went red, and the failure was real rather than environmental: CI
sampled 12 constants where local runs had sampled 6, and hit
`m5_r2_yachi_gameoverreason` — a constant **no perturbation could kill**. Chasing it found
three separate defects in the mutation operator, each hidden behind the last:

1. **Categorical codes need a category, not an offset.** That constant is `5 = winner`, and
   G065 counts death reasons (42 `garbagesmash`, 8 `topout`). Adding 1, 1000 or 10⁶ moves it to
   a value that is still neither, so both counts hold. `5 → 3` falsifies it immediately.
2. **Coded-ness must come from the name, not the value.** The first fix asked "is this value in
   the code range 1–5?", which reclassified a `topcombo` of **4** as a category and mutated it
   to 1/2/3/5 — none of which crosses the `> 6` its claim tests. Six genuine measurements were
   reported as survivors. The emitter already marks coded constants with a trailing `; label`,
   so that is what is read now.
3. **Escalation has to go both ways.** `m4_r3_pinglamb_inputs` feeds "yachi's keys-per-piece is
   lower than pinglamb's" — *raising* pinglamb's keypresses keeps that true at any magnitude.
   Only lowering it (to 0) falsifies anything. The operator was increase-only.

The sample is now **stratified by kind of datum** rather than uniform, since all three bugs
lived in a kind, and CI mutates 96 constants covering all 32 kinds instead of 12 uniform draws.
Both sessions: 96/96 killed, and a 250-constant sweep also came back 500/500 clean.

The lesson worth keeping: a mutation gate reporting "all killed" says as much about the operator
as about the data, and an operator that only knows one kind of perturbation will certify
whatever it cannot express.

### The second solver, done (2026-07-26)

**z3 4.16.0 and cvc5 1.3.4 both answer `unsat` on all 153 generated claims.** That is the
argument the SMT backend existed to make: the same file, two independently implemented solvers,
same verdict — the dual-extractor design applied to the proof side.

Finding cvc5 took a wrong turn worth recording: `brew install cvc5` fails and
`brew search --formula cvc5` finds nothing, because cvc5 is packaged as a **cask in the
project's own tap** (`brew install --cask cvc5/cvc5/cvc5`). The PyPI package is Python bindings
with no CLI. The cask is also what makes CI pinning trustworthy — it carries the release
sha256, GitHub's asset digest reports the same hash, and the downloaded bytes matched both
before the binary was run.

Then two invocation facts, both found by the solver refusing to work rather than by reading
docs: `check_smt` had hardcoded z3's `-in`, which cvc5 rejects outright, and cvc5 will not
honour the file's `push`/`pop` without `--incremental` (it errors with
`cannot push when not solving incrementally`). `SOLVERS` maps each name to its flags now, and
the file is passed as a path, which every front end accepts.

Cost of the whole gate with both solvers, byte-identity and 8 mutations: **0.33 s**.

z3 is deliberately not in CI: recent z3 releases ship only `x64-glibc-2.39` builds, which cannot
run on the `ubuntu-22.04` runner the Dafny step pins (glibc 2.35), and the ≤ 4.14.1 builds that
target 2.35 have no GitHub-reported digest to pin against. So z3 runs locally and cvc5 in CI,
over the same committed artefact.

### Dead constants, found by the same probe

Mutating `m9_r8_yachi_vs` killed nothing, which turned out to be correct (a banded predicate),
but checking why exposed a real defect: the per-session `codegen_dafny.py` scripts emitted the
whole dataset, so **157 constants in 2026-07-22, 6 in 2026-07-24 and 15 in `proof/` were read
by no lemma**. A const nothing reads cannot be killed by a mutation, so it inflates how much of
the data the proofs appear to pin down. `pipeline/codegen.py` had filtered the generated ledger
this way from the start; the three legacy scripts now do too, and
`pipeline/check_dead_consts.py` keeps it that way. All three artefacts re-verify: 56, 52 and 22
lemmas, 0 errors.

## The appendix (2026-07-26)

`pipeline/appendix.py` now owns 證明附錄 — the trust-chain note, the status line, and one table
row per claim — plus the `claims-data` island the badges resolve through. The rows are **static
HTML** rather than assembled in the browser, which deletes the last concatenating row builder
(44 lines of JS per report), makes the appendix exist without JavaScript, and lets it print.
The two per-session `build_appendix.py` scripts are deleted: the pipeline supersedes them.

Three things stopped being hand-maintained:

* the island's `generated_at` timestamp, which nothing displayed and which made the artefact
  differ on every run — the opposite of what every other gate here checks
* 「7 個 replay 檔案」 and 「52 條」 in the trust-chain prose, typed by hand per session and now
  derived from `facts.json` and the ledgers
* the three status-line wordings, which all shipped in the JS so the browser could pick one;
  only the applicable branch is emitted now

Verified by snapshotting the JS-rendered appendix in a browser *before* the change and comparing
after: 54 and 52 rows, **every cell identical**, same status line, same `data-all-verified`, 110
badges. Probes: a hand-edited row fails `--check`; a claim downgraded in the proof map renders
驗證中（failed） with `data-all-verified="false"` and no tick; markup injected into a claim's
Cantonese comes out escaped.

**關鍵時刻 done (2026-08-02)** — `pipeline/moments.py` + `prose/moments.json`, extracted from
the committed HTML rather than retyped and verified to render identical content in all four
reports. The trivia numbers stopped being hand-typed (they are positional now), and the
figures gained per-field attribution: `prose/moments.json cards[3].body` instead of an
anonymous "report.html hand-written prose". Doing it exposed that `check_prose_figures`
enumerated prose files by NAME, so the move silently removed 4 figures per session from the
scan; it now walks `prose/*.json` generically.

**數據對決 and 建議 done (2026-08-02)** — `pipeline/stats_section.py` and
`pipeline/coaching.py`, built in parallel by two agents and wired in serially, because both
touch `build_report.SECTIONS` and all four reports. Verified by an independent harness rather
than by the agents' own reports: all 8 section renders are content-identical to the committed
markup, the element-id sets match (the chart mount points are read by the inline JS, so
losing one silently blanks a chart), and each whole report reproduces its own content. The
`約`-figure coverage landed back on 102/49/43/48 — the number to watch, since moving prose out
of report.html is what silently narrowed that gate when 關鍵時刻 moved.

**P5 — DONE (2026-08-02).** `pipeline/skeleton.py` emits the shell, the marker regions
in document order, and TODO prose; `bin/new-session` calls it as step 6 and never touches a
report.html that exists. Verified end to end from raw replays: 6617 lines, every region
filled, `build_report --check` clean, `check_report_shell` clean, and re-running leaves a
written report byte-unchanged.

The copy-forward workflow it replaces had been propagating stale constants. The VS small
multiples' emphasised rounds were literals computed once for 07-24 and carried into three
later reports, where they marked unremarkable rounds and missed the real extremes (07-28's
168s marathon, 08-01's 206s). Now derived in `chart_data.extreme_rounds()`, so they are
covered by `build_report --check`. Two more of the same shape were fixed on the way: BSD
`cp -n` exits 1 when it skips, so `set -e` aborted `bin/new-session` at step 1 on any
re-run; and the player colours are now positional `--p1`/`--p2` with `--yachi`/`--pinglamb`
kept as aliases, because `records.py` and `build_round_table.py` emit `var(--yachi)`
literally into the regions they own.

Residue, deliberately not done: the four committed reports still declare the palette under
the old names (the aliases make both spellings work), and the `<title>` is the one authored
string outside any region.
2. a report skeleton, so `bin/new-session` emits a report with TODO prose rather than
   expecting one to be copied from a previous session. This is also where the inline script
   stops being player-hardcoded: ~110 occurrences of `yachi`/`pinglamb` remain in colours,
   keys and labels, and they should be resolved once, by the template, not chipped at.


---

## Board reconstruction — open (2026-07-29)

Everything above derives from `results.stats`. A whole class of question cannot: where the stack
was, how deep the well ran, what the board looked like when the kill landed. Those need the board,
and the board needs a simulator that replays the input stream.

**What exists.** A frame-stepped TETR.IO simulator (session scratchpad, not in this repo) on top of
the SRS geometry from `yachi/td-opener-trainer`. Solved and verified: the piece queue (MINSTD
`16807`/`2147483647` over the `ZLOSIJT` bag, 158/158 rounds well-formed), the 60 fps frame clock
(`frames == finaltime_ms * 0.06`, 158/158), incoming garbage content (`amt`/`x`/`size` are in the
`ige` payload — no RNG derivation), and the outgoing attack timeline (recoverable from the
*opponent's* ige stream, 156/158 against `garbage.sent`).

**What blocks it.** Attack timing is **100% correct before the first garbage and ~6% after**. The
insertion rule is wrong, not its parameters — 40 combinations of `garbagespeed`/`garbagecap`/insert
mode/cancel mode were swept and the best still survives only 7/158 rounds. So the board is provable
only on a *prefix* of each round, using the opponent's ige stream as a per-attack oracle:
**2001/14517 placements, 13.8%**, and systematically the early part of every round.

**What it produced so far.** One metric, T-Spin Forecast, written up in
`sessions/2026-07-22/forecast-metric.md`. It came back a **negative result** — AUC 61.4%, on top of
TSD's 60.9%, inside the no-signal band. Worth reading before extending this work, because the
loose version of the same metric scored 72.7% and would have looked like a finding.

### 1 — DONE (2026-07-29): the triage says no

Eight board-derived measures, paired AUC over the 26 rounds with a decided winner and a verified
prefix on both sides:

| measure | AUC | W-L-T | two-sided p | 95% CI |
|---|---|---|---|---|
| height when garbage lands | 28.6% (inv) | 4-10-0 | 0.180 | 45–88% |
| holes at end of prefix | 32.7% (inv) | 7-16-3 | 0.093 | 49–84% |
| max stack height | 36.5% (inv) | 8-15-3 | 0.210 | 45–81% |
| bumpiness | 38.5% (inv) | 10-16-0 | 0.327 | 43–78% |
| well depth | 38.5% (inv) | 10-16-0 | 0.327 | 43–78% |
| holes per piece | 42.3% (inv) | 10-14-2 | 0.541 | 39–76% |
| clear rate | 46.2% | — | — | — |
| average height | 50.0% | — | — | — |

**Nothing reaches significance**, and every confidence interval includes chance. All six
non-trivial measures point the same way — lower, cleaner board wins — which reads less like six
findings than like six proxies for *played well*, a thing `APP` already measures at 91.5% AUC
straight out of `results.stats`. Against a baseline of VS 100% / APM 94.6% / APP 91.5%, a
board metric would have to be far stronger than any of these to earn a column.

**Caveat, stated so nobody over-reads this:** n=26 is underpowered, and the verified prefix is
systematically the *early* part of every round — precisely excluding the deep stacks and heavy
downstacking where these measures should matter most. This is "not justified on current evidence",
not "proven worthless". If the simulator ever gets fixed for another reason, re-run the triage on
full coverage before concluding again.

### 2 — DONE (2026-07-29): mutation coverage closed, 5/5

The two survivors needed adversarial boards, and both took a search rather than an argument:

* **accepts non-rotation landings** — a vertical T slides down a 2-wide channel and comes to rest
  with three corners filled. It satisfies the corner rule but the last action was a downward move,
  so it is a placement, not a spin. Dropping the `rot` guard scores it 2 lines.
* **`bestTspinLines` drops the spin test** — a 3-deep 1-wide well; the T rotates in and completes a
  row with only two corners filled. Dropping the corner test scores it 1.

The first search for the second board returned boards whose rows were **already full**, which
cannot persist in a real game — an invalid state that would have certified a mutant as equivalent.
Excluding pre-existing full rows found a valid one immediately. Worth remembering: a mutation
search over synthesised boards needs the game's own invariants applied to the search space, or it
answers with states the game can never reach.

### 3 — advanced, not finished (2026-07-29)

Worked on despite (1), at the user's direction. Two hypotheses tested and refuted: rising the
*remaining* garbage after a clearing placement (`insertAfterClear`), and using the ige wrapper's
frame rather than the outer event frame for arrival. Neither moved the matched-attack prefix.

**The attack table is not the problem — it is now confirmed correct.** Aggregating every attack
against the opponent's ige stream, keeping only samples where nothing was cancelled:

| signature | observed | formula |
|---|---|---|
| `full-3 b2b0` | 6 (n=50) | TST 6 |
| `full-2 b2b0/1/2/3` | 4 / 5 / 5 / 6 | base 4, then +1, +1, +2 |
| `none-4 b2b0/1/2/3` | 4 / 5 / 5 / 6 | quad 4, same escalation |
| `none-2 c0/c1/c2` | 1 / 1 / 1 | combo multiplier ×1.25, ×1.5, floored |
| `full-2 b2b1 c1` | 6 (n=2) | (4+1)×1.25 = 6.25 → 6 |

**The residual is a board error, and specifically a line-count one.** The minority readings are
`full-1 b2b0 → 6` (the sim cleared 1 line where the real game cleared 3) and `none-2 b2b-1 → 4`
(the sim called a T-spin double a plain double). A missed line also breaks the B2B chain, so a
single early board error cascades into every later attack — which is why one mistake destroys a
whole round rather than one claim.

**Where the error starts, measured:** of the 42 rounds that diverge, **16 diverge before any
garbage has been inserted at all**, 25 after, 1 with no garbage in the round. So this is not one
bug in the garbage model — there is a garbage-independent placement bug too, and it is the more
tractable of the two because no garbage timing is involved. That is the next thing to chase.

**IRS/IHS implemented and refuted (2026-07-29).** The handling block carries `irs: "tap"` and
`ihs: "tap"`, and 3 of 35 pieces in a sample round are hard-dropped with a rotate or hold key still
held — so initial-rotation looked like a strong candidate for the garbage-free bug. Implementing it
made things sharply *worse* (matched attacks 197 → 76, survivors 7 → 2). The reading is that
**"tap" mode fires only on a fresh press, not on a key held across a spawn**, so the baseline was
already correct. Kept behind a default-off flag; the refutation is the result worth keeping,
because it removes handling from the suspect list.

**A note on formal methods, since it comes up:** Dafny and the SMT backend prove *claim ⇔ extracted
data*. Whether the simulator matches TETR.IO is an empirical question about an external system, and
no proof assistant can settle it — only the replay oracle can. Formal proof becomes applicable
once the sim passes its gate and its outputs enter `facts.json` as data, at which point claims
about those numbers are provable like any other.

This corrects the earlier claim that timing is "100% correct pre-garbage": that was measured over
the prefix before the first garbage *arrival*, a shorter window than before the first *insertion*.

### 3b — the method was wrong, and fixing it localised the bug to single pieces (2026-07-29)

Six hypotheses had been refuted one at a time, each costing a full 158-round sweep. That is the
wrong shape for this problem. The field this belongs to is **deterministic-lockstep desync
debugging**, and its standard method is *per-tick state checksums on both sides, compare every
frame, then per-subsystem hashes to narrow which subsystem broke* — a search over **time**, not
over hypotheses. The companion technique is **ddmin** (Zeller & Hildebrandt, IEEE TSE 2002), which
minimises a failing input until removing any single element makes the failure vanish.

Sources: Zeller & Hildebrandt, *Simplifying and Isolating Failure-Inducing Input*;
`bugnet.io/blog/how-to-debug-desync-in-deterministic-lockstep-games`;
`gafferongames.com/post/deterministic_lockstep`.

Applying the search-over-time half properly — bisecting each round on the opponent's ige stream and
keeping only divergences that occur before any garbage is inserted — narrows the bug from "somewhere
in the round" to **a single piece**:

| replay | round | player | piece | sim said | real |
|---|---|---|---|---|---|
| `…-3.ttrm` | 1 | yachi | **14** (O) | 2 lines, no spin → 11 | 1 |
| `…-2.ttrm` | 6 | yachi | **19** (T) | 2 lines, no spin → 11 | 1 |
| `…22-.ttrm` | 0 | pinglamb | **20** (T) | 2 lines, full spin → 6 | 7 |
| `…-9.ttrm` | 0 | pinglamb | **33** (I) | 3 lines, no spin → 1 | 2 |

Nine such single-piece cases exist. An attack of **11** for a two-line non-spin clear can only be
`double(1) + allclear(10)`, so at those pieces the simulated board is empty when the real one is
not. Aggregate check: the sim reports **7** perfect clears where the real games had **19** — it is
losing real all-clears, another board-divergence signature rather than a scoring one.

**What remains is the oracle half.** TETR.IO's own client is the reference implementation (a
`.ttrm` dropped into the PC or web client plays back); no third-party board renderer exists. With
the window already down to one piece, the capture needed is a handful of board states from one
round — a bounded task, not the screen-scraping pipeline it was estimated as earlier. It needs a
logged-in TETR.IO session, which the agent cannot and must not do.

### 3c — differential test run, and it found a mechanic that was never modelled (2026-07-29)

The oracle half was executed: `replay-2026-07-22-3.ttrm` round 1 loaded in the TETR.IO client,
paused, scrubbed to a chosen frame. The transport exposes a **frame counter** under the scrubber
(`0:27.583 FRAME 1655`), which independently re-confirms the 60 fps clock and makes frame-accurate
comparison possible.

At **frame 421**, yachi's real board against the simulator's board at its last preceding lock
(frame 387):

```
sim @387            real @421
36 XXX..XXXXX       XXX..XXXXX     <- identical
37 XXX..XXXXX       XXX..XXXXX     <- identical
38 XXX...XXXX       XXXXXXXXXX     <- full, magenta T at cols 3,4,5
39 XXXX.XXXXX       XXXXXXXXXX     <- full, magenta at col 4
```

The overlapping stack matches **cell for cell**. The two bottom rows are full in the real client
because a T-spin Double had just completed them and they were still on screen — caught mid
**line-clear animation**. The simulator performs the same TSD at frame 429 and reaches the same
`XXX..XXXXX / XXX..XXXXX`.

**So placement geometry is not the bug.** Queue, hold, DAS/ARR, rotation and hard drop all produce
the right stack. What differs is *when a completed row vacates*: the simulator clears instantly on
lock, while TETR.IO holds completed rows for a **line-clear delay** — about 34 frames in this
instance. Nothing in the simulator models that, and it was not on the suspect list, which is why
six hypothesis sweeps walked straight past it.

It also explains the phantom perfect clear: at frame 449 the simulator drops an O into the two
remaining gaps, empties the board and scores `double + allclear = 11`, where the real game sent 1.
With a clear delay, a piece can land before the rows vacate, leaving residue that makes a perfect
clear impossible.

**Next:** capture frames 429–470 the same way and confirm what the real board holds when the
simulator empties it, then model the line-clear delay (and check whether `results.stats` or the
options block pins its length rather than fitting it).

### 4 — not started

Gated on (3). Nothing from a simulator can carry a badge without a second independent
implementation agreeing byte-for-byte, and there is no point writing one against a simulator that
still fails its own gate.

### Original TODO, for reference

1. **AUC-triage candidate board metrics on the existing 13.8%.** Before spending days on simulator
   fidelity, ask whether *any* board-derived measure carries signal: stack height when garbage
   lands, covered holes created per piece, well depth, downstack rate under pressure, height
   differential at the kill. The probe already exists. If they all sit at 50–60% like forecast did,
   stop here — that is the whole answer and it costs an hour.
2. **Close the two surviving mutants** on the T-spin availability probe ("accepts non-rotation
   landings", "`bestTspinLines` drops the spin test"). Either construct a board that distinguishes
   them or demonstrate equivalence. Currently recorded as open, not as equivalent.
3. **Fix the post-garbage divergence** — only if (1) says the sim is worth finishing. The per-attack
   oracle localises failures to individual pieces now, so this iterates far faster than it did.
4. **A second independent simulator**, agreeing byte-for-byte on emitted per-round values. The
   dual-extractor rule applied to derived data; nothing from a simulator can carry a badge without
   it.

Items 3 and 4 are gated on 1. Item 2 is independent and small.
