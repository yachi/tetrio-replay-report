# Plan: `tetrio-replay-report` — a repo that turns a batch of .ttrm replays into a proof-backed Cantonese report

Decisions locked: **public repo**, **everything included** (replays + reports + full pipeline), goal = **repeatable: drop in a batch of replays → get a report**.

> **呢個 header 之下、去到「## 7. Open risks」為止,係 2026-07 寫嗰份原始計劃,照原文留低做記錄,
> 唔會改成今日份 tree。所以嗰個 tree diagram 同 reuse audit 表入面有幾個名而家已經唔啱:
> `codegen_dafny.py` 同兩個 session-local `build_proof_map.py` 喺 2026-08-16 刪咗(`d7e6384`),
> emitter 係 `pipeline/codegen.py`;`check_claims.py` 唔再係「argv,原樣重用」——佢一度變成八份
> byte-identical 嘅副本,而家淨返一個 module(`python3 -m pipeline.check_claims`)。要睇今日嘅
> 結構,睇 CLAUDE.md,唔好睇呢一段。

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
| ~~`codegen_dafny.py` Facts emitter + helper lib~~ | ~~generic (`bal`, `sum_rf`, `sumsq_rf`, `max_pp_is`, `rmin_is`, `rmax_is`, `lb_max_is`, `variance`, `count_expr`)~~ | ~~**promote to `dafny_lib.py`**~~ — OBSOLETE 2026-08-16: `codegen_dafny.py` itself is gone (both session-local copies deleted by the 106-claim spec port), so there is nothing left to promote and `dafny_lib.py` was never created. The helper names in the middle column name nothing in the repo today. |
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

Then the optional prose pass (Claude Code, the phase that genuinely needs judgment): narrative beats + coaching recommendations written against the auto claims, re-run `build_report.py`. ~~The adversarial audit prompt ships in the repo as `docs/AUDIT-PROMPT.md` so the review loop is reproducible too.~~ **False, and it was never true** (2026-08-16): no commit in this repo's history has ever added that file, and `docs/` is `bin/build-docs`' generated Pages output, so a hand-written document there would not survive a rebuild anyway. The review loop is NOT reproducible from the repo — the two `sessions/*/report/audit-phase5.md` files are records of audits that happened, not a prompt anyone can re-run. Left as a real gap rather than quietly deleted: the sentence was aspirational when written and hardened into a claim by sitting there.

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

| Session | Coverage | `--two-site match` | `--two-site round` | Identical behaviour |
|---|---|---|---|---|
| 2026-07-22 | 43/53 testable = **81%** | 42/53 = **79%** | 42/53 = **79%** | 24 |
| 2026-07-24 | 48/50 testable = **96%** | 48/50 = **96%** | 47/50 = **94%** | 29 |
| 2026-07-28 | 10/10 testable = **100%** | 6/10 = **60%** | 6/10 = **60%** | 2 |
| 2026-08-01 | 13/13 testable = **100%** | 12/13 = **92%** | 12/13 = **92%** | 1 |
| 2026-08-09 | 9/11 testable = **82%** | 8/11 = **73%** | 8/11 = **73%** | 0 |
| 2026-08-14 | 16/19 testable = **84%** | 13/19 = **68%** | 13/19 = **68%** | 1 |

Every cell is measured, and gated on push — see "Gating equiv.py coverage" below for what
that replaced. Claims no mutation can falsify are reported separately rather than counted
as covered.

**The ≥85% acceptance gate this phase set is not met by three of the six sessions**, and
2026-07-22 — the session it was declared on — is one of them, at 81% rather than the 85%
recorded here for three weeks. That figure was a seeded draw; enumerating every
perturbation kind settles it lower. The gate is therefore restated as a measurement rather
than a threshold: no honest floor exists when one hand claim is worth 10.0 points on
2026-07-28, and a floor all six pass would sit at 60%.

2026-07-28 is the session where the two families' distinction bites: 10/10 = 100% on single
values, 6/10 = 60% under `--two-site`, because all four of its windowed claims survive every
single-value change. It is not an isolated artefact — five of the six sessions lose coverage
under the second family, and every claim that drops is a windowed or per-match one. See
README's "Where this metric breaks down".

**Bugs this phase's own gates caught**
* the "only one decider" claim restated that match's score without proving it was the
  *only* one — fixed by adding a match-margin counter to the algebra
* `total_rounds` rendered to Dafny as a literal, making "50 rounds" the tautology
  `50 == 50` — real in Python, vacuous in Dafny; now the sum of the `nrounds` consts
* `Facts.dfy` emitted the whole dataset, leaving dead consts no lemma reads, so mutation
  survivors were meaningless — now only load-bearing data is emitted
* `+1` mutations could not kill values that are only constrained beyond a threshold; the
  operator escalates before calling a mutant a survivor (14/14 killed)

## P5 — DONE (2026-08-02); this header read 「in progress」 until 2026-08-16

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

**Superseded 2026-08-02 — see [`FORECAST-PLAN.md`](FORECAST-PLAN.md).** The instrument was pointed
at the other three sessions (it had always honoured `REPLAY_DIR`; nobody had tried). On the three
sessions it was *not* tuned on the round-level signal is **exactly 50.0%** — 17W-17L-43T, p = 1.000
— against 68.8% on 2026-07-22, at 78% power versus a true 70% effect. The descriptive level
survives and is homogeneous across all four sessions (χ² p = 0.978): **14.5% [11.9%, 17.5%]** over
654 verified T-spins. That document also records four defects the work found in committed code,
and the plan for P0–P4.

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
straight out of `results.stats`. Against a baseline of VS 100% / APM 93.8% / APP 91.5%, a
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

### 4 — SUPERSEDED BY POLICY, not pending (annotated 2026-08-16)

Gated on (3). Nothing from a simulator can carry a badge without a second independent
implementation agreeing byte-for-byte, and there is no point writing one against a simulator that
still fails its own gate.

**Both halves of that have since happened, and the conclusion was replaced rather than reached.**
Two engines sharing no code exist and are differentialed (`runCase` vs `runCaseOracle` —
`dualEngineCheck`'s confusion matrix, cross-tslot's 61 656 boards with `unexplained` empty). But the
goal as stated — simulator outputs entering `facts.json` carrying badges — was consciously abandoned
for the **denominator-anchor** architecture: a twice-extracted counter licenses a denominator, the
numerator stays quarantined, and the dual-engine figure is published as a confusion matrix
*precisely because* it does not license badges. Read this item as a route not taken, not a route
still planned. See CLAUDE.md's 分母錨咗 section.

### Original TODO, for reference

1. **AUC-triage candidate board metrics on the existing 13.8%.** Before spending days on simulator
   fidelity, ask whether *any* board-derived measure carries signal: stack height when garbage
   lands, covered holes created per piece, well depth, downstack rate under pressure, height
   differential at the kill. The probe already exists. If they all sit at 50–60% like forecast did,
   stop here — that is the whole answer and it costs an hour.
2. **Close the two surviving mutants** on the T-spin availability probe ("accepts non-rotation
   landings", "`bestTspinLines` drops the spin test"). Either construct a board that distinguishes
   them or demonstrate equivalence. ~~Currently recorded as open, not as equivalent.~~
   **DONE 2026-07-29 — see 「2 — mutation coverage closed, 5/5」 above**, which constructs exactly the
   two boards this item names. This sentence stayed false for eighteen days because the closure was
   written in a new section instead of struck here.
3. **Fix the post-garbage divergence** — only if (1) says the sim is worth finishing. The per-attack
   oracle localises failures to individual pieces now, so this iterates far faster than it did.
4. **A second independent simulator**, agreeing byte-for-byte on emitted per-round values. The
   dual-extractor rule applied to derived data; nothing from a simulator can carry a badge without
   it.

Items 3 and 4 are gated on 1. Item 2 is independent and small.

---

## T-Spin Forecast — the mechanism is settled, the gate in front of it is not (2026-08-02)

The metric now establishes a mechanism for every event it counts (`1a5ce30`): the window is walked
to find the step where the executed spin became available, and that step is decomposed into
place → clear → insert garbage, so whichever edit the availability crosses IS the cause. Rate is
**1 of 654**. What remains open is not the mechanism test but the gate that decides which events
reach it.

### 0 — RESOLVED: the user's own definition agrees with the published number

Stated by the user on 2026-08-02: *"putting an overhang over a few lines far of a hole, when the lines
between them clear, like 1,2,3,4,5+ **cleared by not tspin**, it becomes a tspin hole."* Implemented in
full it is a **necessity** test — track the overhang cell and the cell the T lands on, and count the
event when rows are removed from between them — plus the clause that the removing clear must not itself
be a T-spin.

Measured over all four sessions:

| step | events |
|---|---|
| gap between overhang and landing cell closes | 181 |
| ... rows removed **only by T-spin clears** | 180 |
| ... mixed | 0 |
| ... rows removed **only by plain clears** | **1** |

The 180 are the C-Spin: a T-spin triple removes three rows under an overhang laid in bag 2 (174 of 181
roofs are pieces 7-13), the overhang descends three, the T-spin double goes in. The clear that opens the
slot is itself a T-spin, so the "not tspin" clause excludes them — correctly, since that is the opener,
not a read of the board. The single survivor is `pinglamb replay-2026-07-28-6 r5 lock 32`, closed by a
plain double then a plain single, overhang at piece 19.

**That is the same event the committed metric publishes.** Four routes reach it independently: step
localisation with the straddle test (the shipped rule), the gap-closure necessity test, the not-a-tspin
clause, and a hand-check of the raw boards. No figure changes.

Two things this settled that were previously recorded here as open puzzles:

* **Prophecy and Forecasting are not independent axes.** Implemented as separate predicates over 649
  events, both off-diagonal cells are EMPTY (181 both, 0 either-only). Nothing except a line clear can
  lower an overhang — filling under it does not move it and garbage pushes it up — so placing a roof
  above its final position forces a clear to be what completes it. four.lol's two sections describe one
  event from its two ends.
* **The bimodal gap distribution was not an artefact.** Gap-at-placement being 2 or 5 and never 3 or 4
  is a T-spin triple removing exactly three rows, every time.

### 1 — CLOSED: the leak was not a leak, and the defect was in the counterfactual's deletion set

This item used to read: *"`improved` collapses the board to one number, so a mechanism that replaces
one two-line spin with a different two-line spin moves nothing… 1 event of 654 has garbage that IS
load-bearing at execution."* The sizing run it asked for was done on 2026-08-04. **Every part of that
claim is false except the arithmetic.**

**The event is not load-bearing.** `yachi replay-2026-07-28-1 r5 lock 36`: the T tucks into a garbage
row that arrived at **lock 11**, and the roof is at lock 33. The only garbage that arrived inside the
window `(33, 36]` is a single row at lock 34, sitting at the very bottom of the field twelve rows
below the slot. Delete just that row and the executed spin is untouched — still two lines. The 2 → 1
drop comes from `withoutGarbage` (the PRE-FIX function, deleted in `7a7aefe`; the counterfactual is
`withoutRows` + `garbageArrivedAfter` now, deleting only post-roof arrivals) stripping **all thirteen**
garbage rows, including the one that is
the slot's own floor and predates the roof by 22 locks. The scalar falls because the board was
mangled, not because any post-roof garbage held the spin up.

**Zero events of 654 depend on post-roof garbage.** Restricting the deletion set to rows whose derived
arrival lock is in `(j, k]`: 121 events have such a row (`|D|` from 1 to 14), and the executed spin
survives its removal in **all 121** — 0 gone, 0 degraded, 0 undecidable. The remap was mutation-tested
(drop the row-shift term → 0 reachable / 121 gone), the arrival tagging was validated against the
board at 17,076 lock-steps with 0 disagreements, and a BFS matching the executed cell set reproduces
the actual placement, line count and spin grade on 654/654 events.

**The proposed replacement does not subsume `improved`; it contradicts it in the wrong direction.**
`improved` asks about the board's best slot, the executed-spin test asks about the one slot the player
used, and those differ whenever the mechanism opens a *better* slot than the one executed. At least
**81** currently-accepted events get re-decided INDEPENDENT by the garbage arm alone. Direction B —
`improved = false` and the executed spin DEPENDS — is **empty**. And the line-clear arm has no
execution-time form at all: re-inserting a cleared row yields a board carrying a full row, a state
`lockPiece` cannot leave behind. Back-mapping the executed cells across a cleared row leaves a shape
that is not a T in 47 of 50 cases, so a naive version reports "load-bearing" for 100% of clearing
steps. Retiring `improved` in its favour would delete the corpus's only positive, which is a
`forecast_lineclear`.

**The deletion set is now restricted, and the last disagreement is gone.** `withoutGarbage` is
replaced by `withoutRows(board, garbageArrivedAfter(r, j, k))`. Arrival is derived rather than
tracked, by replaying each step's row edits over one boolean per row; the marks reproduce the real
garbage mask of `boards[t]` at all **110,927 lock-steps** of the four sessions across all seven
swept configs, ordered oldest-on-top everywhere — including `reference_queue`, the one config that
inserts garbage before the piece rather than after it. `loadBearingButNotImproved` is 0, the four
`forecast-facts.json` regenerate byte-identical (the counterfactual observes, it does not classify),
and five new mutants guard the set, `deletion-set-unrestricted` among them.

Note what the corpus test now asserts: `0` is a far weaker statement than the `1` it replaces. It
says only that the two instruments never diverge. The census and the mutants are what hold the rule
in place now, which is the usual cost of fixing the event a test was pinning.

**Also settled:** the sizing sweep costs **2.1 seconds** for all four sessions, not the hour this item
budgeted. `audit-mechanism.ts` already walks them cross-session and needs no `REPLAY_DIR`.

### 2 — CLOSED: the two-slot board exists, and the mutant is live (2026-08-05)

`metric/localise-skip-placement` sat unlisted as "equivalent for every step in the corpus": with no
clear at the causing step `B` IS `Bpre`, so the next branch runs the identical test, and all 388
placement attributions land on steps that cleared nothing. The separating shape has now been built
by hand and the mutant is in the sweep.

What made it awkward is worth recording, because the obvious construction cannot work. The board
needs a second slot that reaches the target in `Bpre` while the post-clear best slot straddles the
cleared row — but **a slot's rows go full, so nothing can descend past them**. Any ordinary second
slot placed above the low well seals it in both `Bpre` and `B`, and the low slot is never reachable.
Three attempts died there.

The way through is that `bestTspin` counts every full row in the board it produces, including the
one about to be cleared. So the high spin need clear nothing of its own: a nook confined to the
right-hand columns, worth exactly 1 in `Bpre` and 0 in `B`, blocking no column. With `target = 1`
the early return fires and the answer is `placement`; drop the early return and the same board is
`line-clear`. The fixture asserts both, so it also demonstrates the two branches genuinely disagree
rather than merely that one of them runs.

### Closed since the last roadmap entry

The "Original TODO" item 2 above — the two surviving mutants on the availability probe
(`best/no-rotation`, `best/no-spin-test`) — is **done**. Both are killed in the current sweep,
which stands at **36/36**. The probe they guard is now `bestTspin`, a single BFS returning both the
line count and the slot's rows; the second copy that once carried a different cap is gone.

### 3 — CLOSED: the garbage-floor events were the same five events as item 1, and they are decidable

This item used to read: *"When the cell the T lands on is GARBAGE it has no placing lock… That is 5
events."* Both halves are now settled, and the two items turned out to describe one population.

The five are `pinglamb 07-24-2 r6 lock 45`, `pinglamb 07-24-3 r7 lock 29`, `yachi 07-24-5 r7 lock 20`,
`yachi 07-28-1 r5 lock 36`, `yachi 07-28-8 r6 lock 21` — every one a TSD tucking into a garbage well
whose lower row is garbage. Item 1's "leak" is the fourth of them. They looked undecidable only under
the strip-all deletion set; under the restricted one **D never touches the slot in any of the five**,
because in every case the in-slot garbage arrived 8 to 22 locks *before* that event's own roof. All
five are decidable and none depends on post-roof garbage.

The tracing problem is also gone, and not by tracking cells. Clause 2 now reads **every cell holding
the piece up**, not the deepest row alone, so a garbage cell under the nose is no longer the only
evidence available — the shoulders usually rest on player stack whose provenance is exact. Where a
genuine support *is* garbage, the existing two-ended test decides it (no garbage at the roof ⇒ it
arrived later; no garbage event in the window ⇒ it predates), and only a straddling window is reported
`undetermined`. Corpus-wide that is **10 of 654**, reported and never counted either way.

What prompted the rewrite was measuring the branch this item leaned on. `floorOrigin` used to return
`'field-floor'` — documented as "the nose reaches the bottom of the playfield, which predates all
play" — in two structurally different situations, and the second one had inspected nothing at all.
Measured over 654 events: 161 nose-on-row-39 and **95 nose-over-empty**, all counted clause 2 TRUE.
Judging the real supports flips **36** of them (35 true→false, 1 true→null). The label is deleted: a
piece supported by the playfield bottom **alone** occurs 0 times in 654 events across all seven
configs, so the case it named does not exist. More generally the inspected cells were a *proper
subset* of the genuine supports in **all 654** events — 294 missed one, 204 two, 156 three — and the
missed cells carried strictly newer provenance in 258 of the 398 events where both sets were
non-empty. The old rule was reaching the right verdict from an input that did not entail it.

The published rate is unchanged at **0 of 654**, under all seven simulator configs.

### 6 — CLOSED: the scalar does conflate slots, and it changes nothing (2026-08-05)

Opened by the player disputing the published sentence — *"forecast is quite common"* — and closed by
the same player reading the boards. Both directions were wrong before the evidence arrived, mine
worse than theirs.

**The mechanism is real.** `localiseMechanism` and `improved` both track `avail(t)`, the board's
BEST T-spin, so neither can see a new slot born beside an existing one of equal line count. Item 1
said exactly this and was closed on 2026-08-04 by testing the GARBAGE arm alone — the line-clear arm
has no counterfactual, so the scalar was never checked there.

**The consequence is nil, and the first three measurements of it were wrong.** A slot-tracking test —
carry the executed T's cells back through every row edit and ask in each frame whether the slot is
spinnable — settles it, but only once it SELF-CHECKS: it must report spinnable at the frame the T
was really executed in. Two versions did not, and each produced a confident number. Requiring every
row the T occupies to fill (a T-Spin Single spans two rows and fills one) gave 323 events where the
spin demonstrably happened but the slot "did not exist"; requiring the roof above a TOP-ROW cell (a
vertical T's roof usually sits over the other column) gave 298. A looser straddle test gave 183.
With the self-check passing 654/654:

| what first made the executed slot spinnable | n |
|---|---|
| already spinnable when the overhang landed — the roof was the last piece | 585 |
| the player's own later placement | 64 |
| garbage | 4 |
| a line clear | 1 |

Four of the five fail clause 2. The survivor, `pinglamb 07-28-6 r6 lock 19`, is a vertical-T
three-row clear in a well walled by the player's own pieces, with the garbage five rows below it;
the arrival only shifted the stack. **So the published 0 of 654 holds under the player's own
criterion** — a clear or garbage before the hole becomes spinnable — and a slot-tracking rewrite
would land on 0 as well. It is therefore not worth doing.

**Re-probed 2026-08-09 from the executed-slot angle, and now GATED.** Recomputing `improved`
slot-locally — `bestTspin`'s BFS constrained to the columns the T actually occupied — over every
reactive event in all four sessions: **0 of 265** rose slot-locally (probe validated: 0 probe-misses,
and it reports a rise on 385/388 self_built and 1/1 forecast_lineclear, so it discriminates). 122 of
the 265 had garbage/clear co-occurrence in-window and none formed the executed slot. So a slot-local
gate reclassifies nothing; the 0% is real, not a saturation artifact. `forecast-saturation.test.ts`
pins it with a non-vacuity self-check (mutation-killed) — if a future session ever makes a reactive
event's own slot rise, that test fails and forces the slot-local rewrite decision on the data.

**What the detour found.** The 183 the loose test flagged are the C-Spin: **179** have a vertical T
clearing three rows as the piece that closes the gap, 175 laid the overhang in bag 1-2, and 173
executed in bag 3 — matching harddrop.com/wiki/C-Spin, *"a T-Spin Triple which is usually followed
by a T-Spin Double within three bags"*. Nothing in the code knows that. They are excluded because
the slot was already spinnable when the overhang landed, which is what an opener is, and clause 2 is
no help — it returns `pre-existed` for 146 of them. `forecast-corpus.test.ts` now pins the outcome
as an oracle (46 such events in 2026-07-28, 0 counted), demonstrated to fail when openers are
admitted. Deliberately NOT a rule in `forecast.ts`: a "vertical T, three rows, first bags"
blacklist needs one entry per named opener and encodes folklore where a property will do.

The wiki is reachable at `harddrop.com/wiki/<page>?action=raw`; the rendered HTML is 403.

### 4 — CLOSED: a dangling nose is still an overhang over a hole, at any depth (2026-08-05)

This item asked whether a T whose nose hangs into a well, with the shoulders carrying the piece,
is really "an overhang over a hole" — the worry being that there might be no cavity under the
overhang at all. **Ruled by the player, and the answer is that depth is not a criterion:** the hole
under a T-spin may be arbitrarily deep, and the nose failing to reach its floor only means the
shoulders got there first. The well the nose points into IS the hole. Nothing changes.

Re-derived while putting the decision to them, and the population was misstated here: it is **95**
events with a dangling nose, of which clause 2 already rejects 21. The **74** was the surviving
subset, not the population. Depth of the well beneath the nose, among those 74:

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 9 |
|---|---|---|---|---|---|---|---|
| 36 | 8 | 13 | 4 | 3 | 7 | 1 | 2 |

Half sit at depth 1, which is simply what an ordinary T-Spin Double looks like — the cell under the
nose stays empty, and that is exactly why it clears two rows rather than three. Had a cutoff been
adopted anywhere it would only have moved the clause-2 census (568 `pre-existed`, down to 494 at
most); the published rate is 0 of 654 either way. Also confirmed while measuring: **0** events have
a piece resting on nothing at all, which is the case `'field-floor'` used to name.

No code change. The item is closed because the question was answered, not because it was worked
around, and clause 2 was right as written.

### 5 — CLOSED: the simulator's tests ran nowhere, and a dead import proved it

`forecast.test.ts` imported `isForecastOrUnverified`, which no file in the repo exports. It had been
there for weeks and the suite was green throughout, because three things are true at once: Bun does
not validate named exports, a name that is imported but never called is never evaluated, and there
is no `tsc` step. The third is the one that mattered — `bun test` was not in CI at all. Only
`cross-extractor` runs Bun, and only to re-run the extractors, so every assertion about this metric
(the corpus census, the wiki fixtures, the clause-2 verdicts, the mutation-guarded gates) was
verified on a laptop and nowhere else.

Both halves are fixed by a `typescript` job: `pipeline/check_ts_imports.py`, then the suite, which
takes under four seconds. The gate has a `--selftest` like `check_forecast_section` does, and it was
run against the actual historical defect — restoring the import makes it fail with the right
message. It reports rather than skips any import form it cannot parse, because a checker that
silently ignores what it does not recognise reports "all clear" for the files it never read.

It is deliberately not a typechecker. A real `tsc` pass would subsume it and is worth doing; it
needs a `tsconfig.json` and a pinned `typescript`, which is a dependency decision, not a gate.

---

## Original TODO 1 — DONE (2026-08-06): four of five candidates are dead, one is not

`pipeline/sim/board-metrics.ts`, all four sessions, 120 rounds with a decided winner and a verified
prefix on both sides. Everything is computed over the verified prefix only, so none of it depends on
the part of the simulation known to diverge. Paired winner-vs-loser AUC through the same
`decideWinner` the forecast AUC uses, with Holm across the five candidates.

| metric | pairs | decided | AUC | p | p (Holm) |
|---|---|---|---|---|---|
| height at garbage | 54 | 50 | 53.7% | 0.672 | 1.000 |
| holes per piece | 120 | 104 | 54.2% | 0.378 | 1.000 |
| well depth | 120 | 114 | 55.0% | 0.303 | 1.000 |
| **downstack rate under pressure** | 54 | 51 | **67.6%** | **0.011** | 0.077 |
| height at end | 120 | 109 | 45.4% | 0.338 | 1.000 |

Four land in the 45–55% band this project already files under "no signal", which is the answer the
item was asking for: **items 3 and 4 (post-garbage divergence, a second simulator) are not justified
by any of them.**

The exception is downstack rate under pressure — rows cleared per piece while garbage is on the
board. Two pre-declared controls were computed in the same run, before the result was read:

- **clear rate with NO garbage on the board: 45.4%** (p=0.343). The winner does not simply clear
  more; the effect is specific to pressure, which is what a confound would not respect.
- **verified prefix length: 59.6%** (raw p=0.033). Exposure is imbalanced — winners' prefixes are
  longer — and that is a caveat, not a refutation, since the metric is a rate per pressure-lock.

Per session the sign is the same in all four (71.9 · 71.9 · 58.3 · 65.0), none individually
significant at 9–15 decided pairs each.

**What it does NOT license.** Holm-adjusted p = 0.077 is not significant, and all four sessions have
now been used, so nothing is held out. This is exploratory. Confirming it needs a NEW session, run
against a pre-registered direction and threshold — the same exploratory/confirmatory split the
forecast metric used, with git as the audit trail. Until then it is a candidate, not a finding, and
it does not earn a column.

### Fallout: a stale cache was feeding the published artifacts

`pairs-cache.json` was keyed on the rule flags and the replay directory but not on the code that
decides the rows. Clause 2 changed `isVerifiedForecast` on 2026-08-05 without bumping `CACHE_V`, so
every consumer kept reading pre-clause-2 rows: the committed `forecast-facts.json` carried
`round AUC p=0.211` on 16 decided pairs while the live classifier scored 0 forecasts for everyone
and therefore tied every pair. Fixed by keying the cache on a sha256 of `forecast.ts`, `sim.ts` and
`verified-prefix.ts`, so a rule change invalidates it without anyone remembering to. All four
artifacts re-emitted. `emit-forecast-facts.ts` now also says "round AUC undecidable — 0 decided
pairs" instead of silently dropping the line when the test has nothing to decide.

---

## Open — 2026-08-07

### 1 — Pre-register `downstack rate under pressure` BEFORE the next session is recorded

The triage above left exactly one candidate alive: rows cleared per piece while garbage is on the
board. Pooled AUC **67.6%** on 51 decided pairs, exact p=0.011, Holm 0.077, same sign in all four
sessions (71.9 / 71.9 / 58.3 / 65.0), and its pre-declared control — the same rate with *no* garbage
on the board — sits at 45.4%, so it is not "clears more" in disguise.

It cannot be strengthened with the data already in this repo. All four sessions were used to find it,
so nothing is held out, and re-reading them is exactly how a 0.077 turns into a 0.03 that means
nothing. The only thing that can move it is a session that does not exist yet — and only if the
prediction predates that session. So it is written down now, in full:

- **Estimand** — paired AUC, winner vs loser, of `downstack rate` exactly as `board-metrics.ts`
  computes it today: rows cleared per piece over locks whose PRE-lock board carries at least one
  garbage row, over the verified prefix only. No re-definition afterwards.
- **Unit** — the player-round, paired by `decideWinner` (the player still alive at the end).
- **Direction** — ONE-SIDED, winner higher. A significant result the other way is a failure, not a
  discovery.
- **Test** — exact sign test over decided pairs, with the decided count always printed beside it.
- **Threshold** — p < 0.05 one-sided **on the new data alone**. Pooling the new session with these
  four is not a confirmation and must not be reported as one.
- **Controls that must also hold** — the calm-clear-rate control stays inside 45–55%, and the
  verified-prefix-length imbalance is reported alongside (59.6%, raw p=0.033 on the exploratory set:
  exposure is not balanced, and that is a caveat carried forward, not a fixed bug).
- **What kills it** — a new session at or below 50%, or the calm control moving with it.

**How much data this actually needs, computed rather than hoped:** the exact sign test needs
≥12 of 15 wins to clear 0.05 one-sided, which at the observed 68% has **24% power**. One session
(9–15 decided pairs) cannot decide this and running it as though it could is how a null gets called
a finding.

| decided pairs | wins needed | power at true 68% | at true 60% |
|---|---|---|---|
| 12 | 10 | 21% | 8% |
| 15 | 12 | 24% | 9% |
| 30 | 20 | 65% | 29% |
| 50 | 32 | 78% | 34% |

So: bank sessions until **~50 decided pairs exist outside the exploratory four** (roughly four more
sessions at the current rate), test once, and report whatever comes out. Anything short of that is
parked, not pending. Nothing here goes in a report until the above is satisfied.

**Two updates this pre-registration needs, recorded 2026-08-16 and neither noticed when they
happened.** First, the bank is about half full: 2026-08-09 and 2026-08-14 arrived after registration,
134 rounds between them, so "roughly four more sessions" is now roughly two.

Second, and this is the one that matters: **the estimand froze a computation that no longer exists.**
The registration says "exactly as `board-metrics.ts` computes it today ... over the verified prefix
only. No re-definition afterwards." Since then the hoisted-DAS fix (2026-08-11) lengthened the
verified prefix by **+31%** and the board source moved to `runCaseOracle`. The metric is the same
formula over a materially larger and differently-produced denominator. That is not cheating — nobody
changed it to chase a result, and both changes are improvements — but it does mean "as computed then"
is now ambiguous, and the ambiguity must be resolved **before** the test runs, not after seeing it.
The honest options are: re-register against the current implementation and treat 08-09/08-14 as
exploratory too (safest, costs two sessions), or run it on the current implementation and report the
prefix change as a deviation with the exploratory figures re-derived under the new prefix for
comparison. **Pick one in writing before the seventh session lands.** A pre-registration that quietly
tracks its own implementation is not a pre-registration.

### 2 — The C-Spin negative is bounded by CATALOGUE COVERAGE, not by the matcher

**Updated 2026-08-10: the corpus is five sessions now (358 clean bags), the same null holds, and it
has been shown to survive the set choice — which is what the rest of this item asked for.** See
`pipeline/openers/README.md` for the table. Two things changed:

- **The C-Spin set is worse than "3 openers" suggested.** Not one of the three names `isCSpin`
  selects is the C-Spin as harddrop draws it: `Fake C-Spin {JP: 偽TKI}` is by its own name a fake,
  `Secspin` merely ends in those letters, and the third is a compound page listing `SDPC-Spin`
  among eight names. The set arguably contains **zero** genuine C-Spins, so a null computed over it
  alone was a statement about very little. `openers.test.ts` now asserts the three names, so this
  paragraph fails a test rather than quietly outliving the catalogue.
- **Widening it does not move the answer**, which is the finding that makes the null reportable.
  C-Spin is commonly identified with TKI; `TKI-3 {Alt: TKI}` is catalogued with 12 pages `isCSpin`
  does not select; adding them (6 openers, 24 pages) leaves the nearest bag at **6 cells** and the
  within-4 count at **0**. So the null no longer depends on settling whether C-Spin *is* TKI. Same
  shape for DT Cannon: narrow (6 openers) and widest (48 openers, any name carrying "DT") agree.

What remains true and unfixed is the sentence below.

`pipeline/openers/` establishes: 0 of 358 clean first bags come within four cells of a catalogued
C-Spin. The catalogue behind that sentence is **3 distinct C-Spin openers across 8 drawn pages**, out
of 360 openers and 783 pages. So the claim the repo can make is "**not these C-Spins**". "No C-Spin
anywhere" is not available at any distance threshold, and no amount of tuning gets it.

Better matching code cannot fix this. The matcher already round-trips every C-Spin page it holds,
finds their mirrors, rejects a junk board, and is alignment-checked against a one-row shift. What is
missing is **data**:

- harddrop's own C-Spin page draws setups the community catalogue does not carry —
  `pipeline/sim/wiki-cspin-boards.json` already holds 38 placements parsed from it, in a different
  format, so a converter would widen coverage today;
- the wiki calls C-Spin a **family** ("there are many C-Spin openers", ZST core, vertical and
  horizontal T), which means an enumeration BY CONSTRUCTION — J and L building an overhang over a
  1-wide covered well — would bound the family instead of sampling it;
- `knewjade/solution-finder` enumerates setups satisfying a pattern, and is the right tool for that
  enumeration if it is worth doing.

Until one of those exists, every C-Spin statement in this repo carries the coverage caveat, and
`pipeline/openers/README.md` says so in the same words.

**What the first bag could never answer, and now is answered elsewhere.** Board comparison asks
"did they build this shape", which coverage bounds. The two openers are also distinguishable by
something coverage cannot touch — the ORDER of their two T-spins. DT Cannon (開幕DT砲, "Double
Triple Cannon") is a Double then a Triple; the C-Spin is a Triple then a Double. Over five sessions,
of the 221 verified rounds holding both spins, **221 run the C-Spin order and 0 run the DT order**,
and dropping the verified-prefix window widens it to 277/277 with the split unchanged. That is a
clean separation with no catalogue in it at all, and it is the spine of the new report section
(`pipeline/opener_section.py`, fed by `pipeline/sim/emit-opener-facts.ts`, quarantined outside the
claims chain like the forecast section).

### 2b — The saturation gate has fired, and the decision it defers is now live — DONE (RESOLVED, global)

**DONE 2026-08-12, `147e7f8`; struck here 2026-08-16.** The decision was taken, **in favour of the
GLOBAL gate**, and it is gated — not deferred. What settled it: the switch to the oracle board source
(verified prefix 24.8% → 92.3%) took the deferred list from 2 risers to **14**, and on all 14 a T-spin
was **already globally available when the roof went up**. A forecast is a slot built while none was
available; if one was already on the board, executing a different slot that happened to rise
slot-locally is opportunism, not foresight. So `forecast-saturation.test.ts` stopped pinning identities
and now asserts the PROPERTY that makes the decision sound (`roseWithoutRoofTspin` empty) — a future
riser on a board with NO global T-spin at the roof would be a genuine masked-forecast candidate and
fails there, which is what the list protected, without enumerating a growing corpus.

**Everything below this line is superseded.** In particular "changing `improved` moves every published
forecast figure in four sessions" is no longer the reason to hesitate — the reason is that the global
gate is now the *justified* choice, and a slot-local rewrite would be a regression rather than a
deferred improvement.

Measured 2026-08-16 at six sessions while confirming this, because the numbers below are worth having
and the entry quoted none of them — global vs slot-local `improved` over all 3 926 records in the
verified prefixes.

**Provenance, per this section's own measured/unverified convention.** The counterfactual was computed
by an agent's probe; what I re-ran on the main thread is its **control**, which is the part that can be
checked against something committed: the probe's GLOBAL side reproduces all **12 player-entries of all
six `sim/forecast-facts.json` exactly, 0 mismatches**, and its baseline corpus `forecast_total` of 6 is
the committed sum. So the driver is the shipped one and the global column is not a re-derivation. The
slot-local column has no committed counterpart to check it against and is **unverified** in that
narrower sense — it is one probe, and its own `roseWithoutRoofTspin` analogue is separately gated by
`forecast-saturation.test.ts`, which is green at six sessions.

| | slot-local YES | slot-local NO |
|---|---|---|
| **global YES** | 1 769 | **20** |
| **global NO** | **18** | 2 119 |

Both off-diagonal cells matter and this entry counted neither correctly. `global-no / local-yes` is
**18**, not the "two deferred risers" recorded below — the 2 were a five-session, hand-port figure.
And `global-yes / local-NO` — 20 events the global max credits while the executed slot did not
improve — **had never been counted at all**, in either direction. A slot-local rewrite is not
"catch 2 more": it is 38 reclassifications, 20 of them removals.

Following all 38 through clauses 2-4: `mechanism_established` 9 → 15, `forecast_total` **6 → 7**
corpus-wide. The one addition is `2026-07-22 pinglamb replay-8 r0 lock 48`, which is the same event
the `access` branch would claim if it were inserted before the strictly-inside test — so the two
open questions overlapped on exactly one record. No session's published headline breaks: 2026-08-14 is
the only session printing 「冇一個 tucked 消行 T-spin 符合曬四項條件」 and it stays at 0.

The 2026-08-16 note further up — "the `access` branch must not be written so a slot-local rewrite has
to redo it" — is satisfied and moot in the same stroke: the branch is a counterfactual on `A` alone,
so global-vs-slot-local lives entirely in the availability function it calls, and there is no rewrite
coming anyway.

**`forecast-saturation.test.ts` held `reactiveRose === 0` over four sessions. On 2026-08-10 it went
to one:** `2026-08-09 pinglamb replay-2 r5 lock 26` rises 1 → 2 slot-locally while the board's
global best does not move, out of 313 reactive events across five sessions. So `improved`'s
global-max gate is losing exactly one forecast today, and the slot-local rewrite the test was
written to force is no longer hypothetical.

**Not done here, deliberately.** Changing `improved` moves every published forecast figure in four
sessions; that is a decision to take on its own terms, not as a side effect of adding an unrelated
metric. The test now pins the riser BY IDENTITY rather than by count, so a second one still fails —
a count can only be updated by writing a bigger number, which is how a gate that found something
becomes a gate that records that something was found.

**Update (2026-08-11): the second riser has now landed** — `2026-08-01 pinglamb replay-6 r4
lock16` (localJ 0 → 1), surfaced not by new behaviour but by the hoisted-DAS fix's longer verified
prefix bringing lock16 into scope (see "Simulator drift" below). Both risers are now named in
`ROSE_KNOWN`. The by-identity design worked as intended — it forced this to be a conscious
addition rather than a silent count bump — but two deferred instances now stand, so the slot-local
decision is that much more live.

**How it stayed hidden is the more useful half.** That test's `SESSIONS` admits a session only once
it has a `sim/` directory. 2026-08-09 had none until `opener-facts.json` was written into one, so
the test scanned four sessions while appearing to scan every session present — a corpus defined by
an incidental directory's existence, reporting full coverage. Worth a sweep for the same shape
elsewhere; `pipeline/sim/cross-tslot.test.ts` carried a hardcoded four-session list and had
likewise never seen 2026-08-09. **That sweep happened on 2026-08-15 (`ab962bc`) and found three
instances, all now at six sessions** — the workflow loop, `cross-tslot.test.ts:74`, and
`cross-tslot-multi.ts`. Extending the test's list failed it immediately, 39033 → 61656 boards, while
its differential stayed empty. This paragraph read as still-open for a day after the fix landed, two
sections above the entry recording it; that is the same staleness class it describes.

**2026-08-16 —— 呢一項同下面個 fifth `Mechanism` 係同一個形狀,做嗰陣要一齊諗。** 兩者都係「個
metric 攞成塊板一個 global 數字嚟答一個 slot-local 嘅問題」:`improved` 用嘅係成塊板嘅 best
availability,而兩個 riser 都係 slot-local 升;而 `localiseMechanism` 冇 access bucket,係因為
`bestTspin` 嘅 availability 係 reachability,而個 step model 淨係識問 formation。新嗰個 access
branch 都係用 `bestTspinLines`(即係 global),所以 slot-local 改寫一落嚟,佢要一齊改。寫個 branch
嗰陣要留意呢一點,唔好寫到 slot-local 改寫要重做佢。

**收咗(2026-08-16),而且兩邊都收:** access branch 落咗(`22ab03e`),個形狀係「淨係喺 `A` 度刪走
同一批行」嘅 counterfactual,global 定 slot-local 完全困喺佢叫嗰個 availability function 入面,所以
一個 slot-local 改寫係換個 measure,唔使動個 branch 本身 —— 呢個 note 要求嘅嘢做到咗。而個 slot-local
改寫本身亦都唔會嚟:上面 2b 已經話咗,個決定 2026-08-12 就落咗,揀咗 global,而且有證有 gate。所以呢
兩件事嘅共同點仍然啱(兩者都係 global 數字答 slot-local 問題),但佢已經唔再係一個要一齊做嘅顧慮。

## T-Spin Forecast — covering the definition's state space (2026-08-08)

A four-agent sweep enumerated the metric's dimensions and cross-tabbed every cell against corpus
instances, fixtures and lemmas. Two commits landed from it (`7b4eb51`, `58378a5`). What follows is
the part that did **not** land: the inventory is the deliverable here, so "cover all possibilities"
is a finite task rather than an aspiration. Roughly a third of it is done.

Every item is marked **measured** (I ran it) or **unverified** (reported by an agent, not reproduced).
That distinction is load-bearing — of the four agent reports, each contained at least one claim that
did not survive checking: a wrong symptom, a wrong file path, a crash misread as a false positive, a
re-derivation of an already-closed finding, and a "surviving" mutant that dies.

### 1 — The two-piece roof: a rule the corpus can NEVER exercise. Highest value. — DONE

**DONE 2026-08-09, `33b233b`; struck here 2026-08-16.** The second two-placer fixture is
`twoPlacerRoof()` in `forecast.test.ts`, provs {1,4}, and it asserts all three things this entry asks
for: the window (`roofFrom` 4, `separation` 3), the ANSWER (`reactive` under `max`, a VERIFIED
`forecast_garbage` under `min`), and clause 2's comparison base (its own test, one floor provenance
either side of 4). With it and the provs-{1,5} fixture both skipped, the `max`→`min` mutant survives
the entire corpus — so this entry's "no corpus can distinguish them" is now measured rather than
argued. **This closure sat unrecorded for seven days**: it landed in `33b233b`'s commit message and
the entry below was never touched, which is the failure mode CLAUDE.md names — a commit message is not
documentation, nothing re-derives it.

**measured.** `Math.max(...placers)` (`pipeline/sim/forecast.ts`) is the whole "the roof's most recent
builder is the piece that set up the slot" rule. Censused over all 654 tucked T-spins: **every roof is
exactly one cell, 654 of 654.** So `placers` is a singleton in every real event and the corpus cannot
distinguish `max` from `min` — not now, and not at any corpus size. One fixture exists
(`forecast.test.ts`, provs {1,5}) and it is the only thing killing `metric/roof-oldest-builder`.

Near-forced rather than surprising: a flat T needs a three-wide pocket and covering a second cell
seals its only entry. That makes it permanent, which is exactly why it needs a fixture rather than
more data. Build a second two-placer board where `j` differs between `max` and `min`, and assert the
window, `separation` and clause 2's comparison base all move with it.

### 2 — A mini spin has never been the EXECUTED spin — DONE

**DONE 2026-08-09, `33b233b`; struck here 2026-08-16.** No mini/full asymmetry exists, and the
identity is now pinned (`forecast.test.ts`, "the EXECUTED spin has never been a mini") so a future one
fails rather than passing unnoticed. Same seven-day recording gap as item 1.

**measured.** `forecast.ts` admits any `spin !== 'none'`, and `bestTspin` counts minis as available.
Across the four sessions the verified prefix holds **exactly one mini lock**; it cleared lines and is
excluded only by the no-roof filter, never by the spin filter. So: 0 of 654 records, 0 fixtures. The
`mk` helper defaults `spin: 'full'` and the clause-4 loop varies the CLOSING clear's spin, not the
executed one. Any mini/full asymmetry is invisible today.

### 3 — `bestTspinLines` counts pre-existing full rows, and only `Bpre` has any

**CLOSED 2026-08-09 — the count is correct, not a latent bug.** `bestTspin` sets `lines` to the
TOTAL full-row count of the post-placement board, not the rows the T completes. That is the
game-faithful contract: the game clears every full row on lock, so "the lines this T-spin would
clear if it locked here" IS the total full-row count, and reading only the rows the T's own cells
complete would be the wrong number. It never misattributes because `bestTspin` only ever sees a full
row on `Bpre`, and every such row was completed by that step's own placement: `A = boards[t-1]` is
post-clear (never full), `B` and every `avail(t)` board have their full rows removed, and
`Bpre = A + this step's placement` — so the full rows are the placement's. The comment above
`localiseMechanism` ("can only LOWER avail(Bpre)") describes the descent-blocking effect; the
inflating effect it fights with only ever applies to placement-completed rows, so it credits
`placement` exactly rather than by mistake.

Probed on a real TSD to see the two effects: 0 extra full rows -> 2, one -> **3**, two -> **3**,
three or more -> **0** (the rows block the T's descent). Those extra full rows are a constructed
input, not a corpus one — exposure is **1 of 389** events whose causing step clears anything (the
single line-clear event), and even its inflated reading stayed under target, so nothing moves.
`bestTspin`'s doc now states the contract so the "total full-row count" is not re-read as a bug.

### 4 — `forecast_garbage` has no corpus instance and no spec backing

**measured.** 0 of 654 events, 0 with `mechanism = 'garbage'`, 0 with `garbageLoadBearing = true`,
and `roofIsGarbage` false for all 654. The arm rests on three hand fixtures over wiki boards.

`58378a5` establishes why the spec cannot help: `GarbageAmountCannotChangeAnyGap` proves two steps
clearing the same rows and differing only in `garbageRows` are indistinguishable to every gap-based
predicate, so **the model cannot adjudicate this branch in either direction** — it fires on garbage
CONTENT and `Step` has no hole column. `GarbageAloneCannotMakeAForecast` is not a refutation of it.
Adjudicating it needs `Step` to carry the hole column per inserted row, which is a model change.

~~Related and open: `garbageLoadBearing` is vacuous. Garbage arrives in-window in **121 of 654** events
and the flag is true in 0, so the corpus test asserting classifier/oracle agreement asserts `0 === 0`.
It needs the anti-vacuity treatment `property-forecast.test.ts` already applies elsewhere.~~

**DONE 2026-08-09 (item 4b), `33b233b`; struck here 2026-08-16.** Reachable after all: 288 constructed
cases, 144 of them load-bearing, so the corpus's 0 is asserted against a population where the flag is
true rather than against an empty one. The arm's lack of a corpus instance (the rest of item 4 above)
is unchanged and stays open — it is a different statement from the flag being untestable.

### 5 — Clause 2 `'undetermined'` has never reached a forecast kind — DONE

~~**measured.** `undecidedClause2` and the emitted `clause2_undecided` are 0 in all four artifacts. The
verdict is unit-tested but the reporting path that exists to stop a zero rate hiding an undecidable
case has never carried a non-zero value.~~

**DONE 2026-08-09, `33b233b`; struck here 2026-08-16.** Constructed end to end in `forecast.test.ts`:
`expect(r.undecidedClause2).toBe(1)`. The reporting path has now carried a non-zero value, so a zero
in an artefact means "none occurred" rather than "this path has never run". It is still 0 in all
**six** artefacts — that is the corpus, not the code. Same seven-day recording gap as item 1.

### 6 — Clause 3 is still witness-only — DONE

**DONE 2026-08-09, `6866f7a`; struck here 2026-08-16.** All three proposals below landed, plus one
correction to this entry: clause 3 is **not** unconditionally redundant beside clause 4 at
`minLines >= 1` — only given `BothSurvive`. See "Closed · 6" below for the detail; it is not repeated
here, because two copies of a closure is how this inventory got into the state this sweep is fixing.
The entry as originally written follows.

**measured.** Clauses 2 and 4 each have a universal `...IsNotAForecast` lemma; `58378a5` added clause
1's (`NotASpinIsNeverAForecast`). Clause 3 has none — nothing states `!GapClosed ==> !IsForecast`, and
`GapClosesOnlyByClearsBetween` / `GarbageNeverClosesAGap` are both single-step. Three proposals, in
dependency order:

- `GapEqualsRowsRemovedBetween` — lift the header's identity to a window of any length. Induct via
  `TrackSplit` / `RemovedBetweenSplit` with `h` symbolic, so the three-step ground blow-up does not
  apply. Needs `CountBetweenIsDistinctCount` (landed) as a prerequisite.
- `Clause3FollowsFromClause4` — turns the prose claim that `GapClosed` is redundant beside clause 4 at
  `minLines >= 1` into a theorem. One-line corollary of the above.
- `NothingRemovedIsNotEvenForecastShaped` — clause 3's first universal; strictly generalises
  `GapClauseIsLoadBearingAtZero` and the `minLines == 0` case `GarbageAloneCannotMakeAForecast` excludes.

### 7 — Modelling `improved` in Dafny is BLOCKED, not pending

**measured, from the codebase's own words.** It needs `BestTspinLines` as a max over reachable
placements; a finite max needs a bounded position set; `forecast.ts` states outright that the ROW
coordinate is not bounded by the engine (`vendor/core/srs.ts` is `if (row < 0) continue`), that the
`4*10*42 = 1680` bound is an ASSUMPTION resting on kick-table reasoning "nobody has turned into a
proof", and that `h < 40000` is "a LIVE belt rather than dead code". Discharging that boundedness
lemma is the prerequisite; until then the spec's clause 3 and the implementation's are different
predicates and the repo should keep saying so.

### 8 — Two sources of truth for "was a spin" — DONE

**DONE 2026-08-09, `6866f7a`; struck here 2026-08-16.** `WellFormed` now requires
`spinAtK == h[k-1].wasSpin`. Doing it exposed that `OnlyClause1SeparatesAFromF` had been green only
because the flag floated free of the history, and that 17 witnesses carried the same defect — all
fixed without weakening the invariant. See "Closed · 8" below. The entry as written follows.


**measured.** In every witness in both spec files `e.spinAtK == true` while `h[e.k - 1]` has
`wasSpin == false`, and nothing relates them. More broadly `WellFormed` never relates `spinAtK`,
`holeOpenAtJ`, `roofAt` or `floorAt` to `h` at all — clauses 1 and 2 have **zero history-side
content**, so the spec can prove the predicate reads those flags and never that a flag is right. The
corpus result turns on clause 2, which is one of the two.

### 9 — The spec mutation suite is 15 killed + 1 unresolved, not 16/16 — DONE

**DONE 2026-08-09, `6866f7a`; struck here 2026-08-16.** The root cause was not the time limit: the
harness tested TIMEOUT before ERROR, so a mutant with nine proved errors sitting behind one slow
obligation scored as a whole-file timeout. Fixed, and the obligation sped up — **18/18 killed**, so
the "either raise the CI limit or speed it up" choice below was a false one. See "Closed · 9".


**measured.** `58378a5` made `mutate-forecast-spec.sh` read the verifier's output instead of its exit
code, because Dafny exits 4 on a TIMEOUT and the harness scored that as a kill. It immediately
reclassified "gap test inverted (>= not <)", which times out at the default and resolves to KILLED at
`DAFNY_TIME_LIMIT=300`. Either speed that obligation up or run the suite at the higher limit in CI; a
standing TIMEOUT is an unread survivor.

### 10 — Unverified, carried from the sweep so they are not lost — DONE

**DONE 2026-08-09, `33b233b`; struck here 2026-08-16.** Both were reproduced, and the first was
**refuted rather than fixed**: the negative roof row is the correct generalisation and clamping it
would regress the straddle test, so it got a comment and no code change. Two of the three
"unreachable" guards are reachable through the exported `localiseMechanism` and got mutants plus
contract fixtures; the third is provably unreachable and got a comment. The census is **7,544
boards, not the 7,579 claimed below**. See "Closed · Item 10".

~~Neither was reproduced. Do not act on them without checking first.~~

- **Negative-row slots.** `bestRows` appends `min(rows) - 1`, so a slot topping at row 0 yields roof
  row -1; `back(-1)` then finds no match and returns -1, and the straddle test would admit every
  cleared row below the slot's bottom — over-attribution to `'line-clear'`. Claimed 0 of 7,579 boards
  observed, constructible.
- **Three unreachable guards** that survive mutation: `avail(t) >= target` at the garbage branch (the
  walk's exit condition may already establish it), `if (!slot)` after a positive `bestTspinLines`, and
  the `t <= j` early return. If genuinely unreachable they want deletion or a comment, not a mutant.

### 11 — Decision, not a task: does `insertMode` join the swept configs?

**measured.** `insertMode: 'immediate'` is legal, is used by `coverage-strict.ts` and
`triage-garbage-totals.ts`, and is not among the seven swept. Before `7b4eb51` it returned **13
verified forecasts** across the four sessions (2.83%) against 0.00% for `best`, every one
`mechanism: 'garbage'` with `garbageLoadBearing: false`. It now throws 20 times instead, and all seven
swept configs are unaffected. So the metric no longer reports a number it cannot justify — but the
published 0% is still a claim about seven configs, and whether that set is the right one is an
editorial call about what the figure asserts, not a bug.

## T-Spin Forecast — inventory resolved (2026-08-09)

A parallel expert sweep (four implementation agents + a fable-model reviewer + a read-only
verifier) worked the inventory above. Three commits landed: `33b233b` (sim fixtures + mutants +
the j=-1 fix), `6866f7a` (spec + the spec's first CI job), `5cc6573` (a numerator bug the
inventory could not see). Every agent claim was reproduced on the main thread before landing;
several did not survive that check and are called out below.

### Closed

- **1 — two-piece roof.** Second multi-placer fixture whose *answer* moves with max-vs-min, not
  just an intermediate. With both it and the provs-{1,5} fixture skipped, the max→min mutant
  survives the whole corpus — the "no corpus can distinguish them" claim, now measured, not argued.
- **2 — mini executed spin.** No asymmetry exists (nothing reads `lk.spin` but the admission test
  and the record's field); the identity is pinned so a future asymmetry fails, and it is the right
  answer — clause 4 already refuses a size exemption at the other end of the window.
- **4b — `garbageLoadBearing` vacuity.** Reachable: 288 constructed cases, 144 load-bearing via a
  landing shift, 144 not. The corpus's 0 is now asserted against a population where the flag is
  true, not `0 === 0`. Reproduced the 121/654-and-0 census independently.
- **5 — clause 2 `'undetermined'`.** Constructed end to end by the strict rule; `undecidedClause2`
  carries 1 for the first time.
- **6 — clause 3 universals.** `GapEqualsRowsRemovedBetween` (any-length window),
  `Clause3FollowsFromClause4`, `NothingRemovedIsNotEvenForecastShaped`. One correction to the
  inventory: clause 3 is **not** unconditionally redundant beside clause 4 at `minLines >= 1` —
  only given `BothSurvive`; the old `IsForecastShape` comment claimed the stronger thing and was
  provably imprecise.
- **8 — grounding `spinAtK`.** `WellFormed` now requires `spinAtK == h[k-1].wasSpin`. This exposed
  that `OnlyClause1SeparatesAFromF` was green only because the flag floated free of the history; 17
  witnesses carried the same defect. Fixed all without weakening the invariant.
- **9 — spec mutation suite.** Root cause was the harness testing timeout before error (a mutant
  with nine proved errors behind one slow obligation scored as a whole-file timeout). Fixed, and
  the obligation sped up. 18/18 killed, was 15 + 1 unread timeout.
- **The numerator blind spot (new, not on the list).** Four published reports carried a split-half
  reliability from the superseded `kind !== 'reactive'` numerator; under the live metric the figure
  does not exist. Fixed, re-emitted, and closed with a source scanner + an artifact test, both of
  which fail on the pre-fix artifact. This is the class the inventory structurally could not see:
  every item asked "is each cell of the definition exercised?", none asked "does every published
  figure come from this definition?". See `5cc6573`.
- **Item 10 — refuted, not fixed.** Claim A (negative roof rows) is a **non-bug**: the negative
  bound is the correct generalisation and clamping it would regress the straddle test — a comment
  records why, no code change. Two of the three "unreachable guards" are reachable via the exported
  `localiseMechanism` and got mutants + contract fixtures rather than deletion; the third is
  provably unreachable and got a comment. The census is **7,544 boards, not 7,579** (7,544 matches
  project memory; the inventory's figure was the outlier). The `j = -1` crash the sweep surfaced is
  fixed (it read `boards[-1]`, contradicting its own doc comment; 0 corpus exposure).

### Re-classified (fable-model review; not yet actioned)

- **3 — `bestTspinLines` counts pre-existing full rows — CLOSED, the count is correct** (fable
  reversed its own "recommend fixing" on second look; the main thread had already reverted the code
  change). Measured under a patched classifier over 654 events × 6 configs: **zero classification
  changes, zero rate changes**. The reversal: counting every full row of the resulting board IS the
  contract — `bestTspin.lines` is "the lines this T-spin would clear if it locked here", and the game
  clears every full row on lock, not "the rows the T's own cells complete". `bestTspin` only ever
  sees a full row on `Bpre`: `A = boards[t-1]` is post-clear so never full, and `B` and every
  `avail(t)` board have their full rows removed, so every full row in `Bpre = A + this step's
  placement` was completed by THAT placement — crediting `placement` is exact, not an artifact.
  Subtracting the pre-existing count would be identity on every corpus board and would BREAK the
  contract on the constructed boards where it is not, so nothing is subtracted. Verified against
  `localiseMechanism` source before closing; `bestTspin`'s doc now carries the contract line.
- **7 — DONE 2026-08-09 in `300b358`, the same day this line was written — and its stated reason
  is unsound.** `spec/Forecast.dfy` has carried `availAtJ`/`availAtK`, `predicate Improved` and both
  halves of the difference theorem since then. The justification BOTH this item and that commit give
  for the `<= 3` bound — "a max over LINE COUNTS, bounded by 3, regardless of the position set" — is
  false: `bestTspin` scores every full row of the RESULTING board, so over n pre-existing full rows it
  measures 1 · 2 · 3 · 4 · 6 · 11. That is settled correct behaviour (Re-classified item 3), but it
  makes `<= 3` a well-formedness assumption about the caller — every board handed to `bestTspin` is
  post-clear — rather than a geometric fact about the T. Corrected in the spec 2026-08-16 with
  `BestTspinLinesIsBoundedOnlyOnClearedBoards` and `TheBoundOfThreeIsAttained`. A DONE record that
  repeats a wrong reason is worth less than none.
- ~~**7 — modelling `improved` was NOT blocked.**~~ The premise "a finite max needs a bounded position
  set" is false: `BestTspinLines` is a max over LINE COUNTS, bounded by 3, regardless of the
  position set's size. Cheap path (hours): add `availAtJ`/`availAtK: nat` to `Event` (exactly like
  the two flags already there, `<= 3`), prove `Improved` and `GapClosed` are *different* predicates
  with two witnesses + an anti-vacuity witness. No boundedness lemma. This matters: `improved`
  performs 653 of 654 corpus exclusions and is the single largest unmodelled thing.
- **11 — OBSOLETE (2026-08-16): the seven-config sweep it argues about no longer exists.**
  `emit-forecast-facts.ts:88` is now `CONFIGS = [['triangle-oracle', {}]]`, and :84-87 records why —
  the multi-config sweep hedged the hand-sim's option uncertainty, the reference engine has no such
  options, "so the sweep collapses to a single authoritative config and the printed simulator range
  is a point" (`147e7f8`). Both recommendations below target a mechanism that was deleted rather than
  narrowed; the artefact already states its config basis in `simulator_configs_for_range`.
- ~~**11 — `insertMode`, keep seven not eight.**~~ Four *other* legal garbage-timing configs
  (`cancelMode:inTransit`, `readyFrom:confirm`, `garbagespeed:0`, `insertAfterClear`) all measure 0
  without throwing, which strengthens the 0%. But the published `simulator_range [0,0]` is over seven
  configs, six of which vary piece kinematics and only one touches garbage — the axis the metric is
  actually about. Recommend: add the four that run (free, all 0), and emit the `insertMode`
  exclusion as data (`simulator_configs_excluded`) rather than dropping a throwing config silently.

### Consolidated

- **4 (main) + 8 (clause 2) are one model change.** Grounding `holeOpenAtJ`/`roofAt`/`floorAt` and
  adjudicating `forecast_garbage` both need a board-carrying `Step` (column information, which
  `Step` has none of today). Grounding clause 2 strictly subsumes `forecast_garbage`: clause 2 needs
  to know which cells each *placement* filled (`roofIsGarbage` is false for all 654), of which
  garbage hole columns are a subset. Driver is clause 2. Cheaper than it sounds — `Cell`, `Board`,
  `Filled`, `Width` are already declared in `Forecast.dfy` and referenced by nothing (dead today).

### New, carried so they are not lost

- **`roofIsGarbage` anti-vacuity — CLOSED 2026-08-09.** Was 0 of 654 with no fixture, same vacuity
  class as 4b. Unlike `garbageLoadBearing` it gates no classification — it is the diagnostic
  `run-forecast.ts` prints as "roof literally IS garbage (strongest signal)" — so the fix is one
  discriminating pair rather than a population: `roofOwner: -1` (garbage overhang) → true,
  `roofOwner: 2` (built) → false, both non-empty, mutation-checked (hardcoding the flag false fails
  the test). `forecast.test.ts`.
- **`determinable` degrades silently at `j = -1`.** Even with the crash fixed, a garbage roof has
  `determinable === false`, so the strict clause-2 rule falls back to loose co-occurrence there.
- **Layer 1 of the numerator gate is deferred.** A branded `VerifiedCount` type would make a
  hand-rolled numerator a *compile* error rather than a scanner finding — the right fix — but this
  tree has no typechecker (no tsconfig, no tsc step; `check_ts_imports.py` is the homemade stand-in).
  Its true cost is "adopt a typecheck step for the whole TS tree", a separate decision.

## BFS arrival key — landed, and what it left behind (2026-08-10)

`bestTspin` deduped on `(rotation, col, row)` while its admission test also read the arrival mode,
so a shift or soft-drop reaching a position first discarded the kicked rotation arrival behind it.
Found by porting cold-clear-2's movegen as a second opinion, which keys on `Placement` (spin
included) and does not lose it. Fixed in `0b0aaf6`; proved in `spec/BfsKey.dfy` (`dfd2834`);
191 of 8 995 verified-prefix boards gained exactly one line, 0 lost, published classifications
unchanged on all five sessions, every committed `forecast-facts.json` byte-identical. Open items
below are what the work turned up and did not close.

- **`bfs-cap.ts` measured a REPLICA of the search — CLOSED 2026-08-16.** It imported `sim.ts` and
  `vendor/core/srs.ts` and never imported `forecast.ts`; it walked its own copy of the BFS. So it
  printed the same 688 for the shipped and the fixed engine, and **that agreement was worth nothing
  as evidence** — it cannot disagree with an engine it never calls. It now drives the shipped
  `bestTspin` through a new opt-in `withBfsTrace`, which derives its figures by walking the real
  `q` AFTER the search, so the hot path pays one null test per call and nothing per edge.
  **No published figure moves**, which is the useful part of the result: 688 distinct positions
  and 848 pair queue both reproduce exactly, at 1.23 entries per position — verified against the
  pre-change file run out of `git show HEAD:`, not against this entry's account of it. Every
  committed `sessions/*/sim/*.json` re-emits byte-identical under the change.

  **The replica was wrong TWO ways, and the second is the stronger argument for deleting replicas.**
  The first is the one above: it could not disagree with an engine it never called. The second is
  that it **printed a different number from the file it was supposedly measuring** — it divided the
  40 000 cap by the position count and reported 58x of headroom, where `forecast.ts`'s own header
  says ~47x. Those two numbers sat one file apart, in contradiction, and nobody noticed, because
  noticing required knowing that「states explored」in one file and「pair queue」in the other were
  different quantities wearing the same name. "It printed the same number twice" is a weak
  indictment; "it silently disagreed with its subject" is the real one. It prints both quantities
  now, separately labelled, and 47.17x.
- ~~**PARTIAL (checked 2026-08-16): the machinery is done and better than this asked; the controls
  themselves still do not exist.**~~ **CLOSED later the same day** — the audit was right at the time
  it was written: `mutate-forecast.ts` carried the full expected-verdict system
  (`Verdict = 'killed' | 'survived'` per entry, a control that starts dying fails the run, STALE as
  a distinct outcome) and **no entry declared `expect: 'survived'`**, with no poison entry. The
  three controls and the poison were added hours later; see the entry directly below, which is the
  same item and carries the measurement.
- **The control mutants `pipeline/sim/README.md` claimed did not exist and never had — CLOSED
  2026-08-16.** The claim was corrected in `8d44543` by *deleting* it, not by building them, and
  the machinery-without-controls state was annotated PARTIAL by the 2026-08-16 ROADMAP audit. Both
  halves are now real. The machinery: each entry in `mutate-forecast.ts` carries an optional
  `expect` defaulting to `killed`, and a mismatch in either direction fails the run. The controls:
  three `expect: 'survived'` entries — `bestTspinLines(b) > 0` → `>= 1` on an integer count,
  `x !== 'none'` → `!(x === 'none')`, `filter(...).length` → `reduce` — and `poison/spawn-column`,
  the BFS spawning at column 9. Measured over the default suite: **52/55 killed, 3 controls held,
  0 mismatched**, the poison among the killed.

  **Each control is equivalent by an argument checkable by eye, and deliberately not by "the suite
  still passes"** — justifying a control that way is circular, because the suite agreeing with it
  is the exact thing the control exists to test. What the four buy is the one failure a mutation
  harness cannot see about itself: if `bun test` silently stopped reaching `forecast.ts` — wrong
  path, a test file erroring on import, an `execSync` throwing for its own reasons — every defect
  injection would report `killed` and the run would look like the best in the file's history. So
  the deleted companion sentence ("a sweep where everything dies is a syntax error") is true now
  and was not before: everything dying means the three controls died.
- **`mutate-forecast.ts` restored its startup snapshot unconditionally — CLOSED 2026-08-16.** It
  snapshotted `forecast.ts`, planted, tested, restored — with no check that the file moved
  underneath it, so a concurrent write was silently overwritten. Strictly worse than the abort fixed
  in `d17a454`, because it destroyed work rather than mis-reporting. The guard is `ours()`: the
  harness compares the file against what IT last wrote and refuses rather than clobbers.
  **Checked before every PLANT, not only before the restore** — a restore-time check alone protects
  the last write and nothing before it, because the next `writeFileSync` in the loop would have
  overwritten the concurrent edit long before the restore ran and the comparison would then match
  again. A refusal leaves the file alone, says so loudly, and deliberately does NOT unlink
  `.mutbak`. Demonstrated, not reasoned: a write planted into `forecast.ts` mid-sweep aborts the run
  at the next plant with rc 1 and the backup still on disk. Two related traps, both hit on
  2026-08-10 and both still true: a planted mutant in a tracked file is exactly `+1/-1` on
  `git diff --stat`, and a test run against a planted tree reports plausible failures that are not
  regressions.
- **`arrival-key.test.ts` was not in the mutation baseline — CLOSED 2026-08-16.** `mutate-forecast.ts`'s
  default set was `['forecast.test.ts', 'wiki-fixtures.test.ts', 'forecast-corpus.test.ts']`, so the
  fixture that proves this whole fix contributed no kills to the main sweep, and there was no mutant
  for the arrival key in that harness at all. Both halves are done: the file is in the default set,
  and `key/revert-to-position` plants the pre-`0b0aaf6` behaviour (rotation arrivals dedup on the
  position key, `expand: true`). The two are one change, not two — without the fixture the mutant is
  not reliably killed by the corpus (191 of 8 995 boards gain a line and no published classification
  moves), and without the mutant the fixture guards a line nothing attacks.

  **This entry itself understated the hole, and that is worth recording.** It said a future revert
  "would be caught only by the separate `mutate-arrival-key.ts`" — **there is no such file**, in
  this tree or in git. So the honest statement of the pre-fix state is that a revert of the visited
  key would have been caught by no mutation harness at all; `arrival-key.test.ts` would have failed
  under `bun test`, but nothing was measuring whether that line was attackable. A named file that
  does not exist reads as coverage.
- **`sessions/2026-08-09/sim/forecast-facts.json` — CLOSED 2026-08-11 (`c9f3065`).** Was
  untracked, so the newest session was uncovered by the forecast-section gate (`verify.yml:280`
  guards with `if [ -f ... ]` and skipped it) and the blast radius of any forecast change was
  silently four sessions, not five. Committed alongside the hoisted-DAS regeneration, so all five
  sessions are now covered. Worth confirming `verify.yml` no longer skips it.
- **DONE — `cross-movegen.test.ts` (`fe9d64b` + `5ab03cb`), in CI at `verify.yml:717-720`.** Five
  deviations from the spec below, each deliberate: the oracle is the ORIGINAL cold-clear run as an
  external nix-built binary rather than a vendored CC2 port (executing a binary sidesteps the
  MPL-2.0 concern entirely); the invariant is `cc ⊆ ours`, not equality; the anti-vacuity liveness
  assertion is present; `fast_mode` under-reporting is handled via `MovementMode::ZeroGComplete`;
  and the no-180 shared-blind-spot statement lives in `pipeline/sim/README.md:233`, not the test.
  The kick tables got the separate exact check the item asked for as well (`cross-srs-tables.test.ts`).
  ~~The `cc-movegen.ts` standing gate is not built.~~ `cc-tslot.ts` cross-checks slot *presence* by
  shape-matching and structurally could not have caught this defect, which is about *reachability*.
  A cold-clear-2 port did catch it. Port from **CC2** (MIT/Apache — CC1 is MPL-2.0, see `fba5ddc`),
  run with `fast_mode` pruning disabled or it under-reports, carry an anti-vacuity liveness
  assertion, and state that it shares this engine's **no-180-rotation** blind spot so it can never
  detect the `wiki-fixtures.test.ts` `UNREACHABLE = {31,35,37}` class. No claim ids, no badges, same
  quarantine as `cc-tslot.ts`.

## Simulator drift — the hoisted-DAS fix, and what it leaves open (2026-08-11)

The Triangle.js oracle (`tools/triangle-oracle/`) was built as a headless, batchable board
oracle to map where `pipeline/sim` diverges from a faithful engine. Following its disagreement
map to a root cause found a real sim bug and closed the entire opening-divergence class.

**DONE (2026-08-11), `c9f3065`.** `.ttrm` keydowns carry `hoisted: true` when the client
recorded that direction as ALREADY held when the piece spawned — DAS is pre-charged, so the
piece slams to the wall rather than moving a single tap. The sim dropped the flag
(`verified-prefix.ts` never plumbed it, `InEvent` had no field) and treated every keydown as a
fresh tap. `scan-lock0.mjs` found 148/592 openers (25%) diverged sim-vs-oracle; `scan-hoisted.mjs`
found 146 of them carried a hoisted opening move-key. The ground truth was the client's OWN
recorded flag, stronger than a pixel capture — no live capture needed. Fix:
`dasTimer = e.hoisted ? handling.dcd : handling.das`, arming ARR when no charge remains.
Result: opening divergences **148 → 3**, corpus bit-exact **39.5% → 49.6%**, verified prefix
**+31%** (cross-tslot step total 7544 → 9878). `facts.json` is python-extracted, so claims,
Dafny and SMT were untouched (08-09 `verify-session`: 88/88 verified); the ripple was confined to
the quarantined opener/forecast tiers and their audit count-pins, re-blessed with comments. Guarded
by `pipeline/sim/hoisted-das.test.ts`.

**TODO — three open items the fix left, in the order they were surfaced:**

1. **Resolve slot-local gating (the decision two gates now force).** The hoisted fix's longer
   prefix admitted a SECOND slot-local riser — `2026-08-01 pinglamb replay-6 r4 lock16`
   (localJ 0 → 1) — alongside the 08-09 one that section 2b already flagged. Both are now named
   in `forecast-saturation.test.ts`'s `ROSE_KNOWN`, and the full-round ordering control picked up
   one stray Double-then-Triple subsequence in two sessions (past the verified prefix, so
   `openers.test.ts` bounds it rather than pinning zero). All three point at the same latent
   decision — should the forecast/ordering metrics gate slot-locally instead of using the global
   `improved`? — which moves every published forecast figure and must be taken on its own terms
   (see 2b and "T-Spin Forecast" item 7). Not resolved unilaterally.

2. **Chase the 3 residual lock-0 divergences.** After the fix, 3/592 openers still diverge
   sim-vs-oracle (2 "plain", i.e. non-hoisted, + 1). A separate, rarer cause — likely a
   movement/spawn edge case. `diag.mjs <file> <round> <user>` dumps the boards to localise it.

3. **Certify mid-round garbage timing (`garbagespeed`/cap).** The opening class is closed but the
   corpus is still only 49.6% bit-exact — the bulk of the remainder is garbage-insertion TIMING,
   where the oracle's `TL_DEFAULTS` are best-effort (holes and gravity are pinned; speed/cap are
   not; see the README caveat). Pin them against a live-capture sample of the early mid-round
   divergences to turn the disagreement map into a certified drift oracle for that class too.

## 最癲一局 — one round deep-dived, and the gate class it re-exposed (2026-08-15)

**DONE (2026-08-15), `2177531` + merge `177dfa5`.** Every report gains a section on the session's
highest-combined-VS round. The selector is not new — `most_intense_round` has picked that round since
the first session — so `generators._intense_round` was factored out and shared, and the section
cannot describe a different round than the claim announcing it. Seven families per session
(`intense_round_profile` ×2, `_edges`, `_attack_rate`, `_downstack_rate`, `_vs_split` ×2), 42 new
lemmas, 526 generated + 164 hand = 690 claims. `pipeline/intense_round.py`, region `intense-round`,
`SELF_INSERTING` (the selector returns None when no round qualifies).

The finding it exists for: **in three of six sessions the winner of that round trailed on APM, on
attack, or both**, and won on downstack — 07-22 m1r5 (DS/piece ×2.00) and 07-24 m6r8 (×2.20) with the
winner also behind on APP, and 08-14 m11r2 (×1.81). 08-09 m5r7's winner led on everything, which is
why the generator has two shapes; the flat case prints「冇得拗」as the result it is rather than as a
failed reveal.

Two idioms the algebra already supported, both reusable. With no division, a derived rate is **pinned**
rather than merely compared: `v·den <= 1000·num < (v+1)·den`, one `between`, with teeth because the
band is `den` wide while a one-unit change moves the left side by 1000. And `|d| <= ε` is
`between(d, -ε, ε+1)` — `between` is `lo <= x < hi` in all three backends.

The VS split is a **bound, never an equality**: `vs·time == 10^8·(attack + cleared)` is observed in
this data, not a published formula. The residual is median 1.1e-4 for the player who died and at most
**6.3e-4** for a survivor, so the family skips any player whose residual reaches half a unit. (It read
**13.4%** for a survivor until the rates were re-sourced from `aggregatestats` on 2026-08-16; that
figure was a live in-game tick being compared against an end-of-round count, which is why it landed on
survivors. The guard now fires on 0 of 760 player-rounds where it fired on 13 — kept, because the
residual grows with `attack + cleared` and the corpus sits ~18× under the trigger, not because it is
structurally impossible.)

**TODO — seven open items, the first three raised by the user, in priority order:**

1. **DONE (2026-08-15) — see 「Gating equiv.py coverage」 below. Item 2 closed with it.**
   ~~Gate `equiv.py` coverage — and it demonstrated the gap itself.~~ The coverage figure is published
   in a table and nothing re-derives it on push. This session added 7 generated claims per session
   directly under that table and the numbers held **by luck**, not by a check: claim-id stability was
   verified, coverage was not. Sharpest remaining instance of the manual-only-gate class. Same fix
   shape as `tools/triangle-oracle/cross-extract.mjs --check`, path-filtered in CI on
   `pipeline/claims/**` and `sessions/**/claims-generated.json`. While doing it: 07-28's 100% is the
   known single-value-mutation artefact and a new gate must not bless it as measured.

2. **DONE (2026-08-15), with item 1 — measured at `round` for all six sessions, not just 07-22.**
   ~~Run `--two-site` on 07-22.~~ Its 83% is a MATCH UPPER BOUND, labelled as such in three documents.
   One ~8-minute run replaces it with the measured figure; update all three together, since a resolved
   bound still described as a bound is the same staleness class as item 1.

3. **CLOSED (2026-08-16) — it is not a forecast, and the instrument that found it was wrong for
   three of its four candidates.** ~~The 4th `forecast_lineclear` candidate — 08-14 yachi r2
   lock19.~~ The verdict is `reactive`: availability at the true roof is 2 and at the spin 1, so it
   **fell**, and `improved` fails. Clause 2 fails independently — a support of the T is garbage while
   `garbageRows(boards[j]) = 0` — so the event could not have passed even had `improved` held.

   **Three independent confirmations, none of which needs the other two.** (a) The roof cell is drawn
   `S`; `oracle-forecast.mjs` attributed it to lock 12, whose piece is a `T`. (b) A backward trace
   using only `boards[]` and each lock's own `cells` — no provenance at all — follows the cell from
   `boards[18]` row 30 back through the two-row clear at lock 12 and the garbage inserts at 14 and 18
   to lock 10, an `S`; lock 12's only column-3 cells were cleared away at lock 13. (c) Both production
   engines say lock 10, and they share no code: `runCaseOracle` (cell-identity provenance over the
   vendored engine) and the `sim.ts` hand-port (its own bookkeeping). Lock 19 is **inside** the
   hand-port's verified prefix (`verifiedIndex` 21), so its agreement is over a board that provably
   matches the real game.

   **Root cause: a superseded file nobody moved.** `tools/triangle-oracle/oracle-forecast.mjs`
   (2026-08-11) rolled its own provenance by mirroring the engine's shift/splice with a force-align
   fallback. `pipeline/sim/oracle-source.ts` replaced that a day later — 2026-08-12, `a53a952`, whose
   message is "95% -> 100%" — with exact cell identity, a WeakMap tag on the engine's own cells. The
   tool was never moved onto it. Same class as `25878d7` and the `dual-backed.json` staleness: not a
   wrong calculation, a right one living in the wrong copy.

   **The census that settles it needs no second engine and no frames.** A provenance index on a
   non-garbage cell is admissible only if that lock's piece is the letter the board draws. Measured
   over six sessions: the tool names an impossible placer for **544 of 2024 (26.9%)** roof cells and
   **1 191 905 of 3 811 813 (31.3%)** placed cells; `oracle-source.ts` for **0 of 4202**, the hand-port
   for **0 of 1988**. That check is now `pipeline/sim/check_provenance.ts` — seven named rules, one
   planted mutant each, plus a positive control that the clean fixture reports nothing — carried into
   CI by `pipeline/sim/provenance.test.ts` so it cannot become another manual-only gate.

   **Three of the four candidates evaporate under the published board source, and nothing published
   moves.** A's roof goes lock 12 → 8 (its `Z` roof cell blamed on a `T`) and C's 6 → 16 (an `L` cell
   blamed on an `I`); both become `reactive`, as does D. Only B survives, roof lock 19 bit-identical
   under both sources — and B still fails clause 2. None of A/C/D was ever in `forecast-facts.json`,
   which is computed over `runCaseOracle` and the verified prefix, so no session artefact, ledger or
   report changes; the four forecast test files pass unedited.

   **The tool's second defect is larger than the first.** It also relocated garbage holes in the live
   engine board — the move `oracle-source.ts:48-58` records as verified dead — and over the corpus it
   produced **90 078** locks where the replays record **70 493** pieces placed. Its PHASE 2 was not
   "scanning 100% of the material"; it was running 28% past the end of rounds that had finished.
   `runCaseOracle` gives 70 500, seven locks off the game's own count over 760 rounds. So the fix was
   a deletion: `oracleSim` is gone, the three probes that imported it read `oracle-source.ts` now, and
   PHASE 1 went **204/205 rounds and 549-vs-548 to 205/205 and 549 = 549**. That "99%" had been read
   as reconstruction noise for four days.

   `ForecastCandidate.dfy`'s `ExactlyOnePreExistedAmongABC` is now `NonePreExistedAmongABCD`: its one
   `PreExisted` disjunct rested on A. The A and C lemmas are kept and marked UNINSTANTIATED — the
   arithmetic is sound, the constants name the wrong lock — and a `AdmissiblePlacer` layer proves the
   letter test that withdrew them. `dafny verify`: 10 verified, 0 errors, and both mutants (declaring
   D admissible; collapsing the predicate to `false`) are killed.

4. **DONE (2026-08-16), `0cc719c` — and the section's stated lede was not what the corpus supports.**
   ~~Measure the new section's metric set.~~ The 13 printed columns are reasoned, not measured — the
   research that was to settle it died on a usage limit. Three angles: paired AUC per candidate;
   a sourced external glossary for what TETR.IO and the community mean by VS/DS/APP, so the Cantonese
   labels are defensible; and an overlap map against all 10 existing generators. If 逐局全數據 already
   prints the whole row, this section's value is the ANALYSIS and the printed set should shrink.

5. **DONE (2026-08-16), `0cc719c` — `pipeline/check_loo.py`, and M11 R2 is rank 3 of the corpus.**
   ~~A leave-one-out gate for published pooled figures.~~ M11 R2 moves 08-14's published lost-regime
   APP gap by 2.874 pp — rank 1 of 84 and 1.72× the next. "The floors have met" is substantially a
   statement about one round and the narrative does not say so. A check that fails when one round
   moves a pooled figure past some fraction of its own value generalises well past this case. Likely
   falls out of item 1's harness rather than needing its own.

6. **CLOSED (2026-08-16) — both counter anomalies. Neither was about the players.**

   **(a) The VS-identity residual is a two-object artefact, not a measurement.** A round carries
   three stat objects and `extract.py:160-162` reads across two of them: `apm_x1000` / `pps_x1000` /
   `vs_x1000` come from `player.stats`, a **live in-game tick**, while `garbage_attack` /
   `garbage_cleared` / `finaltime_ms` come from `player.replay.results.stats`, the **final
   snapshot**. Two objects, two frames — so the identity is being asked of a rate and counters that
   are one tick apart. The third object, `player.replay.results.aggregatestats` = `{apm, pps,
   vsscore}`, is the final rate triple and nothing in the repo reads it.

   The clean instrument is the **time-free** form, which removes the clock entirely:
   `vs·60·attack == apm·100·(attack+cleared)`. Over all 760 player-rounds — **6 above 1% residual
   using `player.stats`, 0 using `aggregatestats`.** (Under the original 2%-of-`10⁸(attack+cleared)`
   screen the count is the roadmap's 8; against `max(|lhs|,|rhs|)` it is 7. All yachi, all
   `alive=True`, under every denominator.)

   The player skew follows mechanically and is not a fact about how anyone plays. The live snapshot
   is stale in **183 of 760** player-rounds, and **181 of those 183 are the round's SURVIVOR** —
   because the survivor keeps playing frames after the opponent tops out, and `player.stats` freezes
   before those frames fold in. The dead player has nothing left to accumulate, so their live tick
   and their final snapshot are the same object's worth of data: 2 of 380. Sharpened, staleness needs
   a conjunction — **179 of the 181** rounds that are both `alive` and have that player's `finaltime`
   running past the opponent's are stale, against **6 of the other 579**. yachi's recording runs later
   in **374 of 380** rounds, so he is stale in 174 of his 177 survivals (98.3%) against pinglamb's 7
   of 203 (3.4%). "8 of 8, same player" was whose client recorded the longer round, not a fact about
   a person.

   `aggregatestats` also settles the formula, and the honest statement is **exact up to `finaltime`'s
   own millisecond rounding, not exact simpliciter**: `100·(attack+cleared)/T`, `60·attack/T`,
   `pieces/T` reproduce all three fields to ≤4.2e-16 when T is read at the clock's true resolution,
   **T = ⌊finaltime_ms·60/1000⌋/60** — the integer FRAME count, floored. Take `finaltime_ms/1000`
   instead and the same identity leaves up to **1.2e-3** relative error on 247 of 760 rounds, all of
   it traceable to the clock and none to the counters. That is large enough to look like a finding;
   a probe using the millisecond value will report a discrepancy the data does not have.

   **DONE (2026-08-16) — the rates are re-sourced.** The sizing below is kept because it is what the
   decision was made on, and every number in it held.

   `intense_round_vs_split` skips any player whose residual reaches half a unit, and on the six
   selected rounds it *was* one stale tick from firing: five of six sat at **0.16–0.49** of the
   0.50 threshold, and all five were the round's **surviving** player (07-22 0.449, 07-24 0.426,
   07-28 0.393, 08-01 0.489, 08-09 0.164; 08-14's survivor is pinglamb at 0.024, which is why it was
   five and not six). The fix was re-sourcing the three rate fields from `aggregatestats` — it
   changed **183 player-rounds** of published APM/PPS/VS (45/22/30/28/20/38, exactly as sized) and
   forced a full re-extraction of all six sessions, both extractors, every ledger and every proof map.

   Those five residuals are now 0.028, 0.0002, 0.0005, 0.0009, 0.0003; 08-14's 0.024 is unchanged
   because pinglamb's rates in that round were already final. The guard is **kept** — see the note
   above — but it no longer fires anywhere in the corpus.

   **That collapse is measured from the committed artefacts, not from a probe**, which is what makes
   it the strongest single number here: the `intense_round_vs_split` claims themselves re-emit with
   `residual under 0.66` becoming `residual under 0.01` (08-01; 07-22 0.61→0.04, 07-24 0.57→0.01,
   07-28 0.55→0.01, 08-09 0.13→0.01). A probe can be written to agree with whoever wrote it; a
   published bound that moves two orders of magnitude when the source is corrected was describing
   the reader, not the data. The guard's old docstring said it existed because the residual "reaches
   13% on some surviving players' records" — that 13% was a mid-round VS being checked against an
   end-of-round attack count, which is why it fell on survivors and only on survivors.

   Seven things the sizing did not predict, all recorded because they are the reusable part:

   - **A published lemma was proving a spurious tie.** 07-22 m1r5 had both players at PPS 1465 under
     the live tick, and `intense_round_edges` rendered `==`. They threw the same 108 pieces but yachi
     survived 250 ms longer, so his true PPS is strictly lower. The claim goes from "trailed on 2 of
     4 attacking axes" to "3 of 4". An equality that holds only because two stale samples coincided
     is the worst case for this repo, and nothing but re-sourcing would have found it.
   - **The correction is not directional in the way the sizing said.** APM falls in 172 of the 183,
     which made "winners' rates are overstated" the natural summary — but 11 rise, and three of them
     cross a threshold: the `rounds with APM >= 65` counts go 15/15 → 16/16 (07-22), 6/6 → 7/7
     (08-09) and 7/10 → 8/11 (08-14). Two published 約-figures also move *up*.
   - **The session-local emitters are a SECOND SOURCE OF TRUTH for every bound, and that is a
     standing hazard, not an incident.** 07-22's `codegen_dafny.py` writes each claim's constant as a
     literal (`/ 1000 == 74`, `/ 79 == 1433`, `== 1630`, `== 74105`, and the C008/C024 bands) with no
     reference to the ledger's `python_check`. Only the *comment* above each lemma is derived from the
     ledger, so editing the claim JSON produced five lemmas proving the OLD bound underneath a comment
     quoting the NEW value — the two disagreeing in the same file, three lines apart. `dafny verify`
     caught it only because all five stale bounds happened to be falsified by the corrected data. **A
     stale bound that still held would have verified clean, kept its status in the proof map, and
     shipped a badge whose lemma proves something other than what the ledger says it proves** — with
     no gate anywhere that compares the two. R021's value turned out to live in *three* places: the
     ledger, this emitter, and `mutation_test.sh` (below).
     **07-28 onward are immune** — their bounds are rendered from the spec by `pipeline.codegen`, so
     the ledger is the only source and `gen_consistency.sh` byte-compares the result. The exposure is
     exactly the two sessions whose hand claims predate the spec algebra, 07-22 and 07-24.
     ~~**CLOSED (2026-08-16)** — both sessions ported to the spec algebra and both emitters deleted;
     see 「106 條手寫 claim 入返 spec 代數」 below. The exposure is now zero sessions.~~
   - **A third copy again, and the mutation test found it.** `sessions/2026-07-22/report/
     mutation_test.sh:58` hardcoded `"m9_r8_yachi_apm: int := 74105"` as mutant [8]. After the
     re-source it reported `NOT-APPLIED ... pattern not found — TEST BROKEN` and the suite came out
     11/12, which `bin/verify-session` fails on. Credit where due: it announces a broken mutant rather
     than scoring it, which is the only reason a *weakened* mutation suite could not pass silently.
   - **A claim can re-emit with identical rendered text and a changed underlying record.** 07-28's
     G039 and 08-14's G043 both print the same gloss before and after while their claim objects
     differ. Diffing glosses — the obvious thing to do, and what a person reviewing a ledger does by
     eye — would report those as unchanged. Compare claim objects field by field. Same lesson as the
     equiv coverage figures: the rendered surface is not the artefact.
   - **A hand list of affected prose runs about 30% short, and some corrections go UP.** The figures
     to fix were enumerated by one method and came to 15; resolving every 約/~/≈ literal in every
     `prose/*.json` against a datum pool built from the old and new facts, then disambiguating each
     candidate by the sentence's own badge, found **22 across 13 sentences** — and ruled out 5
     apparent hits that matched an unrelated datum by coincidence. Two of the seven missed go the
     wrong way for any heuristic: 08-09's 約1.461 → **約1.462** and 08-14's 約50.2 → **約50.3**. The
     method for this class is a datum pool plus badge resolution; `check_prose_figures` is not (it
     passes on all six both before and after), and neither is a list.
   - **`equiv.py` coverage did not move at all — including 07-22, which was expected to.** A full
     `--write` re-measure of all three modes over all six sessions came back **byte-identical**:
     corpus counts, and every mode's `covered` / `identical` set. The reason is worth keeping, because
     it says what the artefact actually measures: coverage is a statement about *logical structure* —
     which generated claim's truth vector implies which hand claim's under the same mutation sites —
     and the hand constants were moved to track the data, so no claim's truth flips. A value change
     that keeps every predicate true and every site in place is invisible to it **by design**. The
     corollary is the warning: coverage being unchanged is not evidence the data is unchanged, and it
     must never be read as one.

   **(b) The finesse counters are on two different units.** `perfectpieces` counts **pieces**;
   `faults` counts **fault events**, and one piece can register several. Pooled over six sessions,
   11 865 faults over 7 510 non-perfect pieces = **1.580 fault events per faulty piece**, which is
   the whole of the excess.

   **The control this item stated was itself wrong.** It is **650/760**, not 168/168 — with **110
   exact equalities and 0 below**; 168 was simply 2026-08-14's player-round count quoted as if it
   were the corpus. The invariant is `perfect + faults >= pieces`, strict in 85.5%.

   The decisive round admits no per-piece reading: **2026-07-24 `replay-2026-07-24-2.ttrm` r0
   pinglamb — `pieces=30, perfect=29, combo=29, faults=7`.** A finesse combo of 29 leaves exactly
   ONE non-perfect piece and it carries all 7 faults. Supporting, all 760/760: `perfect <= pieces`,
   `faults >= pieces - perfect`, `combo <= perfect`; and `combo == perfect` in all 10 zero-fault
   rounds. Each of the three is tight somewhere (10, 110 and 12 rounds respectively), so none is a
   decorative guard. Excess rises monotonically across KPP quartiles (1.41 → 1.54 → 1.60 → 1.75
   pooled, 1.42 → 1.50 → 1.59 → 1.81 as a mean of round ratios), which is why hold-swap was
   refuted — holds are not what varies.

   **No published spec exists**: `finesse`, `perfectpieces` and `faults` appear nowhere on
   <https://tetr.io/about/api/>. The mechanism is inferred from the data plus the official wiki's
   PRO MODE wording ("a percentage of perfect pieces placed, and total faults" — two counters, two
   units) and TetraStats' `finessePercentage => perfectPieces / piecesPlaced`. The
   per-excess-input granularity is **inferred, not specified**, and this repo should say so wherever
   it says anything.

   `pipeline/finesse-counters.test.ts` pins all of it — the three invariants at 760/760, the
   650/110/0 split per session, session totals as literals rather than re-derived, the decisive
   round, and the four rates as four different numbers. The units rule is in CLAUDE.md: **any
   finesse rate must name its denominator.**

7. **Decide the 07-22/07-24 island question.** The section prints claim ids that are not in those two
   reports' claims islands (their generated ledgers sit behind a separate proof map; the island is
   deliberately capped at 54/52 rows). `pc_section` already does this, so the new section matched the
   pattern rather than diverging — but an unresolvable id is close to the failure `check_badge_links`
   exists to prevent. Accept it, extend the island, or stop printing ids the island lacks; whichever
   is chosen must apply to `pc_section` too.

## Gating equiv.py coverage — and the sampled figure underneath it (2026-08-15)

**DONE.** `pipeline/claims/check_equiv_coverage.py` re-derives the hand-claim coverage figures on
push and fails when they drift. `.github/workflows/equiv-coverage.yml` runs it, path-filtered *and*
weekly, per `dual-backed.yml`'s rule that neither alone is sufficient. Items 1 and 2 of 最癲一局's
list both close here.

**The item said the numbers "held by luck". They held by construction, which is worse.** The
numerator is monotone non-decreasing in the generated ledger — adding a family can only ever cover
more hand claims — so the seven `intense_round` families of 最癲一局 could not have moved the
percentage whatever they did. Ablating them confirms it: 07-22 stays 45/53, 08-14 stays 16/19, the
whole attribution block diffs clean. **A scalar gate of any shape — a floor, a byte-compared
percentage, a delta bound — is structurally blind to the edit that motivated the item.** So the
artefact stores verdict SETS and the percentages are derived at read time: a family that newly
covers C007 moves it from `uncovered` to `covered` even when the count stands still, and that is a
line in a diff.

**The figure being gated turned out to be a seeded sample.** `equiv.py` was exhaustive over mutation
*sites* but drew ONE of five perturbation kinds at each, so 07-22 read 85% at the committed seed,
87% at seed 3, 83% at seed 42 — 82.7-86.8% across twelve seeds, with the *denominator* moving
(51-53) because which claims are falsifiable at all depends on which mutants were drawn. The module
docstring said the opposite in so many words: "the whole space of one-value changes — not a random
sample of it." Pinning the seed would have gated a sample and inherited the false claim, so the draw
is gone: every kind at every site, de-duped. ~5× the mutants, deterministic across `--seed` and
`PYTHONHASHSEED`, and `--seed` survives only because `--samples` still draws.

Three consequences, none of them cosmetic:

- **Two published figures fall.** 07-22 85% → **81%**, 07-24 98% → **96%**. The mechanism is exact:
  more samples can only BREAK implications, and 07-22's two losses (C007, C024) were pair-covered
  conjunctions. 07-24 is the instructive one — C024 leaves the numerator while R006 is rescued from
  `untested` into both sides, so the percentage falls with a flat numerator.
- **The ≥85% acceptance gate P4 declared is not met by three of six sessions**, including 07-22, the
  session it was declared on. Restated as a measurement rather than enforced: one hand claim is worth
  10.0 points on 07-28, so no honest floor exists, and one all six pass would sit at 60% and bless
  that session's artefact by definition.
- **Three sessions had never been measured in public at all** (08-01, 08-09, 08-14), and every
  `--two-site` figure ever published was a `match` upper bound. All six are now measured at all three
  granularities, so the table carries no bounds.

**07-28 was never the exception.** Five of six sessions lose coverage to the second family, and every
claim that drops is windowed or per-match — 08-01 C002, 08-09 C005, 08-14 C007/C019/C020, the last of
which are 08-14's own headline claims. `sum_round_range` arrived at 07-28 and every session since uses
it. The gate therefore fails a single-value figure published without its two-site companion for any
session holding windowed claims — a property, not a threshold, so session seven needs no edit.

Four things worth keeping, each a bug that was live:

- **The old match-vs-round gap was an artefact of the draw.** The docstring read "`round` finds two
  implications `match` does not (44/53 vs 42/53)" — backwards, since `match`'s moves are a strict
  subset of `round`'s and extra mutants only break implications. Under the exhaustive family both
  granularities read 42/53 on 07-22, and the two claims that used to separate them are exactly the two
  the single-value family now falsifies by itself. A gap that closes when the cheap family stops
  sampling was never a fact about granularity.
- **The equivalence proof for sharing one sweep across granularities did not gate what it claimed.**
  Mutating the per-mode vector copy to an alias left all three modes returning unchanged results — the
  leaked corpus is a superset and no implication happened to break on the extra moves. A length assert
  in `_search` kills the mutant now. The check that was supposed to prove the refactor safe would have
  passed over a real leak.
- **The path filter `pipeline/claims/**` that this item proposed is too narrow.** The measured import
  closure includes `pipeline/perturb.py` — the make/unmake module the sweep's correctness rests on,
  whose failure mode is a silently *raised* baseline, i.e. a gate that passes when it should not.
- **`PERF-PLAN.md`'s two `claims.equiv` rows stopped being that command's runtime** the moment the
  corpus grew 5×. Annotated rather than rewritten: a speedup table that silently absorbs a scope change
  stops being a measurement.

Cost, measured: push tier (`--modes single_value,two_site_match`) **4m13s** for the whole corpus;
weekly tier (all three granularities) **25m49s**. Neither is a matrix — the gate globs sessions off
disk and takes no session argument, so adding a session cannot leave a list behind. Two such lists were
found stale on the way, and all three are now fixed: `verify.yml`'s cross-tslot loop stopped at 08-01,
leaving 134 rounds outside it, and `pipeline/sim/cross-tslot-multi.ts` and `cross-tslot.test.ts` each
carried their own copy of the same four-session list — so that CI step covered four sessions whatever
the workflow said. Extending the test's list failed it immediately, **39033 → 61656 boards**, which is
a pinned table doing its job. The result worth keeping is not the larger denominator but that
`unexplained` stayed EMPTY over the extra 22 623 boards: the two implementations sharing no code still
disagree on nothing, now over six sessions. A repo-wide sweep found every other session list
(`bin/build-docs`, `analysis/rate_records.R`, `cross-movegen`, `cross-tspin`, `openers.test.ts`)
already at six.

## 最癲一局 items 4 and 5, written up (2026-08-16)

Both landed in `0cc719c`. They were left reading as OPEN in the list above for a day, and neither
`pipeline/check_loo.py` nor `pipeline/docs_gate.py` was named anywhere in this file or CLAUDE.md —
found by an adversarial audit, not by a gate. **That is this session's own failure mode occurring
inside the session that was about it**: the commit message described the work, the ROADMAP did not,
and a reader of the ROADMAP would have concluded two shipped gates were future work. A commit message
is not documentation; nothing re-derives it.

### 4 — the metric set, measured. The section's own lede was not supported.

380 decided rounds over six sessions, reusing `pipeline/sim/pairs.ts`'s tie handling and reproducing
CLAUDE.md's published 129-round AUC block exactly as a control first.

- **入力 dropped** — AUC 61.6 overall but **89.8 / 16.1** split by whether the winner also placed more
  pieces, and 44.7 once normalised as KPP. It is exposure wearing a hat, and it was the only one of
  the 13 rows 逐局全數據 does not already print.
- **手順失誤 dropped with it** — 62.5 inverted overall but 30.5 / 50.0 across the same strata. Cutting
  both is what retired the disclaimer paragraph whose only job was to tell the reader to ignore them;
  keeping one would have left that paragraph paying rent for a single row.
- **最高 B2B demoted out of the edges, row kept** — it loses signal exactly where this section looks:
  terciles 71.0 → 67.7 → **53.1**, rho −0.183, Holm p 0.0068.
- **Edges count AXES, not columns** — APM↔攻擊量 agree directionally 98.2%, PPS↔粒數 97.1%, while no
  other pair among the seven exceeds 73.4%. The old sentence inflated its own finding; this is a
  correctness fix, not taste.
- **The lede moved onto downstacking.** "The winner trailed on attack" is not an intensity effect —
  APM/攻擊 rho ≈ −0.07, ns, and their apparent decay is a round-LENGTH effect (−0.187 / −0.184, Holm
  0.0040 / 0.0098). What survives is 清走/DS rho **+0.200 / +0.210**, Holm **0.0020 / 0.0028**, against
  a length control at +0.054 / +0.058 (Holm 1.000) and a death-bias control that *strengthens* it
  (normalising by garbage received → +0.236, while 食 — same bias, no skill — does not trend).

**The set did not shrink to nothing, and the reason is proof, not ink**: 逐局全數據 prints 12 of the
13 rows already, but as *unproved* table cells — 10 of the 13 fields acquire a Dafny lemma only here.

Two defects found by reading the rendered page rather than by any gate: the flat branch said "led on
every axis" while listing only the *ahead* ones, so a level axis would be proved equal and then
described as a lead; and "more cells than axes" is false when the only trailing axis is a singleton.

### 5 — the leave-one-out gate. The motivating case is rank 3.

`pipeline/check_loo.py` + `pipeline/docs_gate.py`, in `verify.yml` on **every push at 0.062 s**.

The control reproduces (2.8742 pp, rank 1 of 84, 1.7233×), but over the 17 published round-pooled
figures m11r2 is **third**. Worse are 08-01's in-game score gap (`rel` **20.93** — one round moves it
20.9× its own value, while the two players differ by a **median 3 038 points per round**, so "0.05%
apart" is cancellation across 53 rounds, not convergence) and 07-28's attack gap (2.27, sign flips).

**`rel` = largest single-round shift / |value|, and the threshold 0.5 is derived, not picked**: among
cuts that still catch the motivating case, 0.969 → 0.406 is the widest gap at 2.386×. 5 of 17 fire,
0 false positives. Absolute shift does **not** distinguish these — m11r2's 2.87 pp is only 1.17× the
largest absolute shift anywhere.

**The remedy is the caveat, not silence**: a crossing figure is satisfied by its sentence carrying its
own leave-one-out annotation, and the four affected CLAUDE.md sentences now do. `ANNOTATED` is a named
exception list (`DT_ORDER_IN_OPENER` pattern) so a sixth crossing must be investigated rather than
absorbed — and a *named* figure that stops crossing also fails, because an unearned caveat is as stale
as a missing one. The gate prints the sorted `rel` distribution every run, so a seventh session filling
the gap in is visible.

Three limits stated in the artefact rather than in prose: the AUC block is **structurally immune**
(one round moves a mean of {0, 0.5, 1} scores by at most 1/(n−1); measured `rel` ≈ 0.012); the claim
layer is a **dead end** (260 of 463 claims break under some single-round drop, because any `sum == N`
claim does); and **match granularity is not a bound on round granularity** in either direction.

Lifting the doc parser into `docs_gate.py` — so CLAUDE.md is parsed in exactly one place — exposed a
latent off-by-one in `paragraph()`: `rfind(...) + 2` returns index 1 for a paragraph at byte 0,
silently dropping its first character. Harmless for equiv's anchors, not harmless for a substring gate.

## `localiseMechanism` has no bucket for "the clear opened the PATH" (2026-08-16) — DONE

**DONE (2026-08-16).** `access` is the fifth `Mechanism` and `path_opened` the fifth `ForecastKind`,
inserted after the clear's own geometry and before the piece's, exactly as Design A below specifies.
Both corpus events are reclassified, `unattributed` is 0 in every session and player,
`step-model-gap.ts` is deleted, and **no published rate, CI or statistic moved** — the six artefacts
differ only by the schema string, the new key, and `self_built` falling by 1 in two sessions.
`sessions/2026-08-09/report/report.html` no longer says 「玩家自己落嗰隻棋整出嚟」 of the slot that
Z did not make, which was the concrete cost this item was filed for.

Four things came out of the implementation that the design below did not anticipate, and all four
are worth more than the item itself:

1. **The rejected row's own number was wrong here: it is 9, not 7.** Measured twice, independently —
   a fresh probe that first reproduces all 1789 shipped verdicts, and `forecast-access-class.test.ts`'s
   pre-existing sweep, whose `clearAlone` is 9 = 5 `formed` + 2 overdetermined + 2 `access`. The "7"
   counted the 5 `formed` and the 2 `access` and silently dropped the 2 overdetermined. The chosen row
   (2, in-prefix, 0 beyond) is confirmed by both.
2. **The `touches` exit is now UNREACHED on this corpus, and that is the shape of the repair.** 11
   records reach that block across six sessions: 9 `formed`, 2 `access`, **0** either way below.
   Before the branch, `touches` fired exactly once — 08-09 r7 pinglamb lock 24, i.e. the entire
   confidently-wrong half. It is kept as live code (a clear displacing a slot the piece *did* build is
   an ordinary board), but the only thing exercising it is `forecast.test.ts`'s `DISP_*` fixture — and
   that fixture is the **sole** killer of the mutant that asks the counterfactual of `Bpre` instead of
   `A`. That mutant makes the branch fire unconditionally and **no corpus test notices**, because
   everything reaching there takes the `access` exit anyway. A corpus-only mutation suite would have
   scored it a survivor.
3. **`run-forecast.ts` reproduced its own documented bug, one line under the comment describing it.**
   Its hand-written zeroed tally had omitted `self_built` in 2026-08-08, printing `NaN` for 388 of 654
   records; `path_opened` was about to do it again verbatim. The literal is gone rather than extended —
   `FORECAST_KINDS` + `zeroKindTotals()` derive it, and the runner throws if its printed breakdown does
   not sum to its own header. `satisfies Record<ForecastKind, number>` was written first and rejected:
   **there is no `tsc` step in this repo**, so a type-level guard there fires on nothing. The same
   `else`-swallows-a-bucket hazard existed in `emit-forecast-facts.ts`, where the fifth kind would have
   been published as `reactive` — i.e. as "the available spin did not improve", the opposite of what it
   means.
4. **The first draft of the rendered sentence claimed more than the predicate proves.** It said
   「個窿位一格都冇變過，一早就已經喺度」. Cell-identity is measured and true of both events (recorded
   per entry in `ACCESS_CLASS`) but is **not** what puts an event in the bucket — the branch tests only
   that the cleared rows alone already reach the target. The section renders off the artefact's *count*
   and never sees that list, so the sentence would have rested on a property no gate in the render path
   can check. It now states the counterfactual. Same family as the 4d0f2f5 trap: the gate re-renders
   from the artefact, so it compares the sentence against itself and never against the truth.

`check_forecast_section.py` gains two anchors — one for the CLAIM, one for the clause-3 REASON — for
the reason `check_opener_section`'s `ANCHOR_MARKERS` exist: checks 1-2 are render-vs-renderer and are
blind to a sentence the renderer stops producing. Its `path_opened` mutant is MANUFACTURED, since four
of six sessions hold none and a perturbation mutant is vacuous there; the partition-assert case expects
a **raise**, not a rejection, because with the assert deleted the input still renders. 17 corruptions,
all caught, on every session.

`forecast-access-class.test.ts`'s mutation header was re-measured rather than carried forward (the old
13/10 described a file whose `ACCESS_CLASS` held different verdicts): **20 planted, 16 killed, 4
survive**, nothing regressed. The fourth survivor is new and is an honest correction — widening the
cross-check back to `access || placement || unattributed` survives, so tightening it to the exact
`access` is *correctness, not coverage*, and must not be described as what catches a deleted branch.

The original entry, unedited, follows.

Found by looping `forecast-facts.test.ts` over every session instead of the one it defaulted to. The
test read `DISCOVERED[0]`, which is the *oldest* session, so a default run checked 2026-07-22 six
times and reported as though it covered the corpus. Rescoped (236 → 312 tests, and a session
directory with no artefact now fails); 2026-08-14 immediately went red on an invariant the file
itself asserts.

**`bestTspin` is a BFS from spawn, so its availability is REACHABILITY, not shape** — and the step
model only reasons about *formation*. `forecast.ts:494` says a cleared row outside the slot
"displaces the slot rigidly and cannot have formed it", which is true, and leaves **a clear that
removes the lid over a pre-existing but unreachable slot** with nowhere to go.

Demonstrated by deleting the cleared row from the pre-board **alone** — no piece cells, nothing else —
with three controls, on 2026-08-14 `-0.ttrm` r4 yachi lock 74 (step 70):

```
A                        best= 1 rows [32,32,32,33,31]
A minus row 33 (no T)    best= 2 rows [36,36,36,37,35]     <- the slot, already there
A minus row 31 (control) best= 0 null
A minus row 32 (control) best= 0 null
A minus row 34 (control) best= 1 rows [33,33,33,34,32]
rows 34..39 identical A vs A-minus-33: true
```

**The counter detects only half of its own class, and the undetected half is the dangerous one.**
Sweeping all six sessions for the property rather than the bucket — cleared rows alone reach the
target, no cleared row strictly inside the slot — gives **2 events in 1789 localised records**, 0
beyond the verified prefixes, so neither is a coverage artefact waiting to grow. (1789 is the
localised count; 3926 is every record in the verified prefixes, most of which are `reactive` or
not-determinable and never reach `localiseMechanism` at all.)

| session | event | filed as | why |
|---|---|---|---|
| 2026-08-14 | `-0.ttrm` r4 yachi lock 74 | `unattributed` | the piece does not touch the slot, so nothing claims it |
| 2026-08-09 | `-6.ttrm` r7 pinglamb lock 24 | **`placement`** | a Z whose cells are provably outside the slot; `touches` fires on adjacency alone |

So the same defect gives an honest "don't know" when the piece sits away from the slot and a
**confident wrong verdict** when it happens to sit beside it. **2026-08-09's published report
therefore says 「玩家自己落嗰隻棋整出嚟」 of a slot that piece did not make.** That sentence is the
concrete cost, and it is the reason this is filed as a defect rather than a curiosity.

**The repair is a fifth `Mechanism`, not a widened line-clear branch.** The report's line-clear gloss
「消嗰行啱啱夾喺天花板同窿位中間」 *is* the strictly-inside test, so widening the branch would falsify
a printed sentence to fix a miscount. Access needs its own value so both glosses stay true.

**設計已經定咗:出 `access` 呢個 Mechanism,同時出一個新 kind,但個新 kind 唔入
`isVerifiedForecast`(Design A)。** 三樣量過嘅嘢定咗佢:

1. **淨係加一個 Mechanism 乜都唔會變。** `forecast.ts:717-726` 個 kind ladder 收尾係
   `: 'self_built'`,所以一個新 mechanism 會靜靜雞跌落 self_built,上面講嗰個
   404 → 403 根本唔會發生。要一齊加 kind。
2. **插邊度係量出嚟嘅,唔係揀嘅。** 新 branch 放喺 strictly-inside 測試之後、`touches` 之前:

   | 位置 | 全 corpus 重新分類幾多條 |
   |---|---|
   | strictly-inside 之前 | ~~**7**~~ **9** —— 兩條 access 加**全部 5 條 `formed`**(即係成個 corpus 出街嗰批 forecast_lineclear)**再加兩條 overdetermined**,原文漏咗最後嗰兩條。唔收得。 |
   | line-clear 之後、touches 之前 | **2** —— in-prefix,prefix 以外 0 |
   | touches/placement 之後 | **1** —— `touches` 會 short-circuit 咗 08-09 嗰條做 placement,即係confidently-wrong 嗰半原封不動 |

3. **新 kind 唔可以入 `isVerifiedForecast`,因為 `spec/Forecast.dfy:506-530` 唔准。** Clause 3
   `GapClosed` 講嘅係「天花板同個底之間嗰啲行縮咗」——就係 strictly-inside 嗰條規則,寫喺手寫嘅概念
   spec 入面。一條 access event 消嘅行喺 `[roofAt, floorAt]` 之外,所以 `IsForecast` 係 false。畀佢
   入 numerator 就係 TS 同 Dafny spec 對唔上,而喺呢個 repo 入面 spec 先係定義。個 spec 亦都完全冇
   reachability 呢個詞彙(`availAtJ`/`availAtK` 係 opaque int)。個 kind 亦都**唔好**用 `forecast_`
   做前綴:今日 `forecast_*` 剛剛好標住可以入 numerator 嗰兩個 kind。

**上面「加一個 clause2_undecided」嗰句要更正。** 喺 Design A 之下 `clause2_undecided` 維持 0。佢只
會喺 Design B(新 kind 入 numerator)之下先至出現,因為 08-14 嗰條 event 個 floorOrigin 量出嚟係
`undetermined`——即係 clause 2 對佢係*查唔到答案*,唔係「通過」。原文寫「rejected by clause 4」讀落
好似 clause 2 過咗,兩句都啱但合埋會誤導。

**`step-model-gap.ts` 修好之後應該刪,唔係清空。** 08-14 嗰條變咗 `access`,所以每個 session 每個
player 嘅 `unattributed` 都係 0,個 record 會變空——而一張空嘅具名例外清單,正正就係佢自己個 header
話唔准嘅嘢(「一條例外唔到嘢嘅 stale entry,同漏咗一條一樣衰」),而且 `forecast-facts.test.ts:71-85`
嗰個 reciprocal test 係 iterate entries 嘅,空 record 令佢變 vacuous。文件內容(點解呢一類存在、點解
個 counter 淨係見到一半)要搬入新 branch 嘅 doc comment 同 `forecast-access-class.test.ts` 個 header,
唔可以連檔案一齊冇咗。

**No published rate moves**, which is why this could be deferred rather than rushed: 08-14's event is
rejected by clause 4 (its closing clear was itself a T-spin) and 08-09's by clause 2
(`floorOrigin: arrived-later`), so `forecast_total`, `forecast_rate_x1000`, the CIs and the
"0 forecasts" headline are all untouched. What moves on repair is the `self_built` count and gloss
(08-14: 404 → 403 plus a `clause2_undecided`; 08-09: 232 → 231).

Pinned meanwhile as a **named exception list** (`UNATTRIBUTED_STEP_MODEL_GAP` in
`forecast-facts.test.ts`, the `DT_ORDER_IN_OPENER` shape), exact in both directions and with a
reciprocal test so a renamed session cannot carry its own exception out of scope. Six mutants kill it:
entry removed, count drifts up, named event disappears, exception spreads to another session, stale
entry, wrong player named.

~~**What that list does NOT cover, stated because it would otherwise be invisible: the 08-09 event is
unpinned.** The list keys on the `unattributed` counter, and 08-09's event is filed `placement`, so it
reaches no assertion — a third event arriving in the confidently-wrong shape would pass silently.
Pinning it needs the record, which needs the simulator rather than the committed artefact. Until the
fifth `Mechanism` lands, the only thing holding that half is this paragraph.~~

**Both paragraphs above are obsolete as of the DONE block.** `UNATTRIBUTED_STEP_MODEL_GAP` and
`step-model-gap.ts` are deleted — with `unattributed` at 0 everywhere the list would have been empty,
and an exception list excusing nothing is what its own header forbade, besides making
`forecast-facts.test.ts`'s reciprocal test vacuous. Both halves of the class are pinned by verdict in
`forecast-access-class.test.ts`'s `ACCESS_CLASS`, which keys on the measured property rather than on a
counter, so the 08-09 half is no longer held by prose.

**Related scoping, narrower than it first looked — and the first version of this paragraph
overstated it.** `REPLAY_DIR=sessions/2026-07-22 bun test` (`verify.yml:569`) supplies the session for
exactly **one** file, `pipeline/sim/ige-y-oracle.test.ts`, whose third test measures the ige-`y`
oracle's agreement rate over whatever `REPLAY_DIR` names — so in CI the other five sessions' rates are
never measured, while its other two tests are hand-worked fixtures and session-independent. Every
other sim and opener test names its own sessions, and the workflow comment at `:567` already says so
("One test reads it; the rest name their sessions themselves"). Documented scope, not an accident.

~~**Genuinely the same shape, and still open:** `pipeline/sim/forecast-corpus.test.ts:71` hardcodes
2026-07-28 and pins `unattributed: 0` inside its bucket `toEqual`, commented "an improvement the step
model cannot explain would invalidate the buckets above it". Choosing 07-28 is deliberate — it carries
the corpus's only mechanism-established forecast — but it means that file never saw 08-14's 1 either.
One file wide, same `DISCOVERED[0]` failure mode.~~

**DONE (2026-08-16), `fac914c`.** `forecast-corpus.test.ts` now pins all six sessions' bucket totals
and reads `unattributed` from `UNATTRIBUTED_BY_SESSION` in `pipeline/sim/step-model-gap.ts` — the one
list both granularities derive from, so a third event is added once instead of being mirrored by hand
in two files that agreed "by inspection".

*(Superseded the same day by the fifth `Mechanism`: `unattributed` is 0 everywhere, so that shared
list had nothing left to hold and the file is deleted. The bucket pins remain, with `path_opened`
added. The point the file made — one fact in one place, never mirrored by hand — is why its content
went into `localiseMechanism`'s own doc rather than into a second test header.)*

## 106 條手寫 claim 入返 spec 代數 — 兩個 session-local emitter 刪清 (2026-08-16) — DONE

**DONE.** 2026-07-22 同 2026-07-24 嘅 54 + 52 條手寫 claim 全部改寫成 spec，
`sessions/*/report/codegen_dafny.py`（783 + 522 行）同 `build_proof_map.py`（71 + 55 行）四個檔案
一齊刪走。刪 **1431 行**、加 1232 行（四個 `hand_claims_*.py` 共 1162 行，加 `pipeline/claims/idioms.py` 70
行），淨減 199 行 —— 但重點唔係行數，係刪走嗰 1431 行係**第二份 bound**。呢個直接收咗上面「The session-local emitters are a SECOND SOURCE OF
TRUTH」嗰粒 —— 而家零個 session 有第二份 bound。

### 收咗嘅係一整類，唔係一單嘢

那兩個 emitter 將每條 claim 嘅 bound 硬寫多一次，同 ledger 無任何關係，所以 ledger 一改就出現
「lemma 證住舊 bound、上面三行 comment 引住新數」。上次靠 `dafny verify` 見到，純粹因為五個過時
bound 啱啱好被新數據 falsify —— **一個仍然成立嘅過時 bound 會 verify 得乾乾淨淨、proof map 照樣
verified、badge 照樣出街**，全 repo 冇一個 gate 會比較兩者。而家 bound 只有 ledger 一個來源，
`gen_consistency.sh` 逐 byte 比對，呢一類冇咗。

### 代數加咗七樣嘢，全部有等價論證

`score_of_winner` · `dur` · `nrounds` · `nmatches` · `count_rounds_window` · `count_round_pairs` ·
`alive` 用 0/1 出（`_int_lit`，因為 Python `bool` 係 `int` 嘅 subclass，f-string 會寫出 `True`，
Dafny 同 SMT-LIB 都唔收）。三個要記住嘅決定：

- **代數繼續係 conjunctive** —— 冇 `or`、冇 negation。「最大值係 V」寫成
  `count_rounds(f > V) == 0` 同 `count_rounds(f == V) >= 1` 一對，`pipeline/claims/idioms.py` 收埋
  等價論證。用 witness round 釘住反而**證多過句子講嘅嘢**，同 badge 證少過句子一樣係 drift。
- **兩個 window index space，揀錯會靜靜雞改咗個 claim。** `count_rounds_range` 係**場**嘅窗，
  `count_rounds_window` 係全 session **局**位置嘅窗。連勝會跨場，所以只可以用後者；用前者會把個
  run 截喺場界。
- **C021 個 window bound 冇得用「放鬆 bound」嚟 mutate。** 5 放到 6 個 conjunct 仍然真，帶住一個
  被削弱但仍然真嘅 conjunct 嘅 conjunction 一樣 verify 到 —— 個 mutant 生還講唔到個 lemma 任何嘢。
  真正殺得死佢嘅係改**數據**：m1r3 由 pinglamb 反做 yachi，兩個相鄰嘅 run 併成一個七局嘅 run，
  其他 conjunct 全部照樣成立，得個 window bound 捉到。`mutation_test.sh` 入面兩個 mutant 都係咁釘。

### 驗證：八個 layer 入面跑咗六個

| | 07-22 | 07-24 |
|---|---|---|
| `dafny verify` | 54 verified, 0 errors | 52 verified, 0 errors |
| `gen_consistency.sh` byte-identity | ok | ok |
| `mutation_test.sh` | **17/17 killed**（原本 12） | **16/16 killed** |
| `check_lemma_vacuity` | 144/144 falsified | 141/141 falsified |
| `claims.smt2` + z3 + cvc5 | 144 claims, 100 ms | 141 claims, 60 ms |
| `equiv.py` verdict sets | 逐 byte 不變 | 逐 byte 不變 |

**Port 唔止要「照樣成立」，要「逐個 dataset 都一樣」—— 而呢個測試捉到一單嘢。** `bin/verify-session`
只證到每條 ported predicate 喺 committed facts.json 上面係 True，但**一條被削弱嘅 predicate 一樣係
True**，所以嗰個 gate 分唔到翻譯同放水。攞 `git HEAD` 嘅舊 `python_check` 同新嗰個，喺 `equiv.py`
同一份窮舉 single-value mutation corpus 上面逐個 dataset 比對真值：07-24 **52 條 claim × 22 060 個
dataset 完全一致**，07-22 **53 條一致，C021 唔一致**。

C021 唔一致嘅原因唔係個 port 錯，係**舊嗰條 predicate 喺 `equiv.py` 入面根本 evaluate 唔到**。佢用
`all(facts[...] for mi,ri in [...])` —— `facts` 出現喺 generator **body** 而唔係第一個 iterable，而
generator body 有自己嘅 scope，睇唔到 `eval` 嘅 locals。`equiv.py`（同 `build_claims.validate`）將
`facts` 放 locals，`check_claims.py` 放 globals，所以同一條 predicate 喺主 gate 年年綠、喺 equiv 入面
年年 `NameError`。量過：HEAD 有兩條係咁，07-22 C021 同 `sessions/2026-07-24/proof/claims-24.json`
C018。

**一條 evaluate 唔到嘅 hand claim 會被算做 covered。** C021 喺三個 mode 嘅 `covered` 入面 —— 一條真值
向量全部 undefined 嘅 claim，vacuously 被任何 generated claim implies。Port 之後佢真係 evaluate 到
（10 + 21 個 dataset falsify 佢），而 `covered` 個 set 照樣一樣，所以出街嗰個百分比冇郁；但**佢之前係
啱嘅原因係錯嘅**。Spec 代數由構造上出唔到呢個形狀（每個 `facts` 引用都喺 top level 或者第一個
iterable），`build_claims.validate` 又用嚴格 scoping，所以 106 條 ported claim 全部即刻入咗閘。
**未收嘅係兩個 evaluator 用緊唔同 scoping** —— `check_claims.py` 寬鬆嗰個先係 `bin/verify-session`
行嘅嗰個。下一個 increment 收。

**`equiv-coverage.json` 逐 byte 不變係最有力嗰個獨立證據。** 個 coverage 講嘅係邏輯結構 —— 邊條
generated claim 嘅 truth vector 喺同一批 mutation site 下 implies 邊條 hand claim —— 完全冇經過
呢次改寫嘅任何一行代碼。106 條 claim 換晒表示法而每條嘅 truth vector 一個 bit 都冇郁，係翻譯
而唔係重寫嘅證據。

**唯一真係郁咗嘅一個 field，本身就係一個發現。** `windowed_claims` 由 `null`（＝「讀唔到，因為
冇 spec」）變成量得出嚟嘅值：07-22 係 `[]`，07-24 係 `["R015", "R018"]`。即係話 07-24 一直帶住兩條
`count_rounds_range` claim，而 single-value coverage figure **原則上 falsify 唔到佢哋** —— 呢個
session 過去一直被當成冇 windowed claim 嚟讀。

### 順手捉到一個 CI 窿，佢同呢次 port 係同一個形狀

`verify.yml` 個 hand-ledger byte-identity step 寫死 `[ -f "$W/hand_claims.py" ] || exit 0`。07-22 同
07-24 拆咗做 narrative + coaching 兩個模組，所以個 step 會**靜靜雞跳過**，兩個 session 嘅 hand
ledger 冇任何嘢睇住佢哋同模組同步。而家改成行 `build_hand.hand_ledgers()`，佢對**冇模組重建嘅
ledger 直接 raise**，唔係跳過；`--selftest` 四個 case（兩個 mutant 兩個 control）證明兩邊都有牙。
Control 唔可以省：一個乜都 raise 嘅 check 會免費「殺死」兩個 mutant。

### 出街嘅嘢郁咗 108 行，全部係 lemma 名

兩份 `report.html` 各自嘅 appendix 同 `claims-data` island 入面嘅 `lemma` 值變長咗 —— 舊
emitter 截 60 個字元，`pipeline.codegen` 截得闊啲，所以而家印出嚟嘅名同真正 emit 嗰個一致。冇一行
散文、數字或者 status 郁過（逐行核過），`check_proof_links` 同 `check_badge_links` 兩個都綠。

### 跟手要決定嘅三樣（唔係 bug，係 contract）

1. **`codegen.partition_spec_ledgers` 而家永遠 `without == []`。** 佢係為 07-22/07-24 而存在嘅
   「講明我漏咗乜」機制，而家 repo 入面冇任何工具整得出冇 spec 嘅 ledger。照本 repo 嘅標準
   「冇 mutation 殺得死嘅 guard 係擺設」佢應該刪，連 `check_smt` 嗰段 narrowing 一齊；留低嘅
   理由只有「佢寫低咗個 contract」。要揀，唔好當清潔做。
2. **`check_equiv_coverage.windowed_claims` 個 `None` 分支同上。** 得 selftest 嘅合成 session 行到。
3. **`sessions/2026-07-24/proof/` 仲有佢自己嘅 `codegen_dafny.py`。** 佢係 cross-check artefact，
   `check_cross_artefact` 睇住佢同 `report/` 講同一件事，`bin/verify-session` 亦全綠。但佢係
   corpus 入面最後一個 session-local emitter，同上面收咗嗰個 hazard 同一個形狀 —— 分別係佢冇
   badge 出街。

## 兩份出街報告寫錯咗個 event 為咩唔計數 (2026-08-16) — DONE (`4d0f2f5`)

`pipeline/forecast_section.py:333-340`:一見到 `mechanism_established > forecast_total`,就render
一句寫死咗嘅理由 ——「但（當中 N 個）嘅底係天花板之後先至嚟嘅,所以計唔到數」。嗰句係 **clause 2**
(`floorOrigin === 'arrived-later'`)。但 JSON 冇任何一個 field 講邊條 clause 否決咗個 event,所以嗰句
係假設,唔係讀返嚟嘅。

量過(獨立探針,行 `runCaseOracle` + `verifiedIndex`,重現到六個 artefact 嘅
`mechanism_established` 1·1·2·2·2·1):三個唔計數嘅 event 入面**得一個**係 clause 2。

| session | event | floorOrigin | closingClearWasSpin | 真正否決佢嘅 | 出街嗰句 |
|---|---|---|---|---|---|
| 2026-07-28 | `-6.ttrm` r5 pinglamb lock 32 | arrived-later | false | **clause 2** | 啱 |
| 2026-08-09 | `-6.ttrm` r6 yachi lock 213 | pre-existed | **true** | **clause 4** | **錯** |
| 2026-08-14 | `-2.ttrm` r3 yachi lock 18 | pre-existed | **true** | **clause 4** | **錯** |

08-14 嗰句最斬釘截鐵——「但佢個底係天花板之後先至嚟嘅」——而嗰個 event 個底係 pre-existed,佢唔計數
係因為**收尾嗰下消行本身就係一個 T-spin**。而且嗰局就係全 corpus 唯一嗰個 DT 砲(`-2.ttrm` r3
yachi),即係成個 repo 講得最多嗰局,個錯誤理由就貼喺嗰度。

**點解冇 gate 捉到:** `check_forecast_section.py` 係攞住 JSON 再 render 一次同出街嗰份逐 byte 比,
而 JSON 根本冇 clause 資料。一個由假設砌出嚟嘅句子,喺一個「重新 render 再比對」嘅 gate 面前永遠一致。
同 `check_prose_figures` 捉唔到 finesse 標籤、同 tape chart 住喺 shell 入面係同一個形狀:gate 睇住
generated content,但個**理由**唔喺數據入面。

**收法:** emit 一個 `rejected_by` breakdown(每個 mechanism-established 但唔計數嘅 event 由邊條
clause 否決),句子照住佢分支。**唔好**改成「clause 2 或者 clause 4」——嗰個係寫嚟氹 checker,唔係
寫俾讀者。同時要有一個 mutant:將 `rejected_by` 嘅值調轉,而 render 出嚟嘅句子必須要變。

呢單同下面個 fifth `Mechanism` 係兩單嘢,但兩單都要改 `forecast-facts` 個 schema 同重出六份 artefact
加六份報告,所以要順住做,schema `/8` → `/9` → `/10`,唔好夾埋一個 commit。

**收咗(`4d0f2f5`),schema `/9`。** `forecast.ts` 出 `rejectedBy()`,六個互斥兼窮盡嘅 bucket;
emitter 當場比對 `rejectedBy(rec)==='counted'` 同 `isVerifiedForecast(rec)`,唔一致就掟;section
逐條 clause 分支,裸讀 `rejected_by` 加一個 partition assert。`check_forecast_section --selftest`
加咗個 mutant:將一個 event 由 clause 2 改做 clause 4,render 出嚟嘅句子一定要變 —— 佢係**砌**個
rejection 出嚟而唔係攞現成嘅,所以六個 session 都有牙(三個 session 根本冇 uncounted event)。

**兩樣要記低嘅。** 第一,`clause2_undecided` 唔再由 section 讀:佢本來另開一段講「查唔到」,而上面
嗰句已經將同一批 event 當成 clause 2 否決咗數過一次 —— 同一件事講兩次兼且講成兩樣嘢。而家
`rejected_by` 對每個 uncounted event 淨係數一次,而 `forecast-facts.test.ts` 拿兩個 undecidable
bucket 同 `clause2_undecided` 對數,所以個 field 唔會冇人睇住就飄。

第二,寫 clause 4 嗰句解說嗰陣行差咗一步,值得記:第一版寫「屬於自己砌,唔係垃圾或者對手逼出嚟嘅
外力」。喺呢一節自己嘅詞彙入面兩句都錯 —— 上面兩段先啱啱定義 外力 = 「垃圾升起或者消行」,即係消行
本身就係外力;而 自己砌 係 `self_built` 嗰格嘅名,呢個 event 係 `forecast_lineclear`,唔喺嗰格。
即係話:**改一句寫錯咗嘅理由,好容易換成另一句寫錯咗嘅理由**,而個 gate 一樣係綠嘅,因為 gate 對
嘅係 render 出嚟同 artefact 一唔一致,唔係對嗰句講得啱唔啱。真正嘅理由係循環:開個窿位嗰下消行就係
個 spin 自己。`spec/Forecast.dfy` 個 `GapClosedIsExactlyRowsRemoved` 講緊同一件事。散文啱唔啱,
到今日為止仲係要人讀。
