# cc-coach — your mid-game positions, replayed by cold-clear

**Question:** can we take the mid-game positions out of a `.ttrm`, hand them to the cold-clear bot,
and learn something from where it disagrees with the human? **Yes**, and this directory does it end to
end. It is a research tool in the same tier as `tools/triangle-oracle`: nothing here feeds `facts.json`,
mints a claim, or runs in CI. Every figure it produces is a **one-engine** figure (cold-clear's opinion),
never a verified one.

First run: the 2026-10-03 session (20 matches, 292 player-rounds, 27 868 placements), results in
[`FINDINGS-2026-10-03.md`](FINDINGS-2026-10-03.md).

## Pipeline

```fish
set -x REPLAY_DIR /path/to/session/replays      # a directory of .ttrm
set W (mktemp -d); cd $W

# 1. every decision point, through the repo's reference board source (vendored Triangle engine)
OUT=positions.jsonl bun ~/tetrio-replay-report/tools/cc-coach/extract-positions.ts
python3 ~/tetrio-replay-report/tools/cc-coach/validate-boards.py      # board_i + cells_i + garbage_i == board_{i+1}
bun ~/tetrio-replay-report/tools/cc-coach/validate-attack.ts          # TETR.IO attack re-priced == replay's own

# 2. cold-clear, pinned rev 279edd7 (the same rev as nix/cold-clear-oracle), plus this patch + harness
git clone https://github.com/MinusKelvin/cold-clear cc && cd cc && git checkout 279edd7c3177ff8077f6a930193397814b281f27
git apply ~/tetrio-replay-report/tools/cc-coach/cold-clear-coach.patch
cp ~/tetrio-replay-report/tools/cc-coach/cc-coach.rs bot/src/bin/ && cp ~/tetrio-replay-report/tools/cc-coach/Cargo.lock .
cargo build --release -p cold-clear --bin cc-coach && cd ..

# 3a. per-move grading (mid-game = lock >= 21, verified prefix only)
python3 -c "import json;[print(l,end='') for l in open('positions.jsonl') if (lambda p:p['lock']>=21 and p['verified'])(json.loads(l))]" > mid.jsonl
CC_NODES=40000 COACH_DUEL=80000 cc/target/release/cc-coach < mid.jsonl > grade-mid.jsonl
python3 ~/tetrio-replay-report/tools/cc-coach/grade-analyze.py grade-mid.jsonl

# 3b. 14-piece rollouts from the same positions, same pieces, same received garbage
python3 ~/tetrio-replay-report/tools/cc-coach/build-rollouts.py
CC_NODES=40000 COACH_MODE=rollout cc/target/release/cc-coach < rollouts.jsonl > rollouts-40k.jsonl
bun ~/tetrio-replay-report/tools/cc-coach/analyze-rollouts.ts rollouts.jsonl rollouts-40k.jsonl
python3 ~/tetrio-replay-report/tools/cc-coach/window-analysis.py rollouts-40k.priced.jsonl
```

Runtime on 4 cores: extraction 30 s; grading ~0.6 s per position per core; a 40k-node 14-piece
rollout ~5 s per window per core.

## What each piece of evidence rests on

| step | how it is checked | result on 2026-10-03 |
|---|---|---|
| board reconstruction | whole round: engine piece count and line count == replay `results.stats` | 292 / 292 rounds |
| piece sequence / bag | every aligned 7-block of the reconstructed sequence is a permutation | 292 / 292 |
| decision records | start field + played cells → clear → recorded garbage (amount, hole column) reproduces the next decision's field | 27 576 / 27 576 transitions |
| attack pricing | the vendored engine's own `garbageCalcV2` with re-derived b2b/combo counters == replay's pre-cancel `rawGarbage` | 27 866 / 27 868 locks (2 straddle a garbage-multiplier step) |
| b2b / combo counters | recomputed counters == engine's next-state counters | 27 868 / 27 868 |
| attack-row prefix | the repo's `verifiedIndex(..., 'frame+row')` | 24 268 of 27 868 decisions inside it; only those are graded |
| reachability | the human's placement is among cold-clear's root candidates (`ZeroGComplete` movegen) | 18 341 of 18 356 graded mid-game moves (15 are 180° / SRS+ placements cold-clear cannot generate; they are still scored, through the duel) |

## Three measurement decisions, each made because the obvious version was wrong

**1. Cold-clear is not converged, so a single "it would have played X" is weak evidence.** Over 300
calibration positions its 40k-node pick equals its own 640k-node pick only 185 times. A per-move verdict
therefore needs a noise floor, and that is measured, not assumed (`calib.py`, `duelcal.py`).

**2. Values read off the main tree are biased against the human.** Root candidates carry backed-up
MAXIMA, and cold-clear's favourite is searched far deeper than the human's move, so its max is drawn
from more samples. The **duel** removes this: each of the two placements gets its own reward plus an
independent fresh search of the same budget from the board it leaves (`COACH_DUEL`). Regret is
`duel(cc pick) − duel(human)` and can be negative — the human beats cc's pick in ~40% of positions.

**3. A threshold is a calibration, not a taste.** A "clear mistake" is duel regret ≥ 600, which is
above the 95th percentile of a deliberately weakened cold-clear (10k nodes) judged by the same duel.
Reproducibility of a single flag at 600, re-judged with 4× the budget: ~75%. So individual examples
shown to a player are **re-verified at higher budget** before being shown, and the headline numbers
are aggregates.

## Rollouts: what "same position" means

From a mid-game decision, cold-clear plays the next 14 pieces (two bags). It sees exactly what the
human saw: the same field, hold, b2b/combo state, the 5-piece preview, and the true future sequence
revealed one piece per placement. Garbage is **pressure-matched**: the rows the human actually
received at step *j* (amount and hole column) enter cold-clear's pending list after its step-*j* lock
and are inserted on its next non-clearing lock (TETR.IO only tanks on a lock that clears nothing).
Cold-clear gets no cancellation credit for its own attack, and both sides' attack is the TETR.IO
pre-cancel figure priced by the same `garbageCalcV2`.

Received garbage is ENDOGENOUS (a human who attacks less cancels less and receives more), so it is
never used as a stratifier; pressure is stratified by what is fixed at the window's start (garbage rows
already on the board, garbage already queued).

## Residual differences from TETR.IO, and which way each one biases

| difference | effect | direction |
|---|---|---|
| no clock: cold-clear thinks ~0.2 s per piece unpressured, the human plays at ~2 PPS | cc is advantaged | overstates the gap; the 4k-node rollouts are the "fast bot" check |
| cold-clear's evaluator is tuned for PPT, values b2b as a boolean, knows nothing of TETR.IO's b2b chain levels or combo multiplier | cc plays sub-optimally for TETR.IO scoring | understates the gap |
| no 180° rotation, SRS instead of SRS+ for I | cc's move set is a subset of the human's | understates the gap |
| no cancellation credit for cc in rollouts | cc faces at least the garbage the human let through | understates the gap |
| cold-clear's own T-spin / mini rule prices cc's spins | small; minis are rare in both | either |
| spawn rule `Row19Or20`, lock-out pruning above row 20 | cc declares positions near topout dead earlier than TETR.IO | rollouts where cc topped out are reported, and excluding them raises the gap |
