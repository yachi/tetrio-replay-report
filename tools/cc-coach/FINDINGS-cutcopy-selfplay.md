# Pilot: does cold-clear, playing alone, build Cut Copies (千鳥格子)?
Research only, in the same tier as the rest of tools/cc-coach. Nothing here feeds facts.json, analysis/, a page or a claim. Every figure is one run's output, copied by hand on 2026-10-20. No committed artefact re-derives them, so re-run the commands to get them back and never copy them into anything published.

## Method
1. **Self-play** (`COACH_MODE=selfplay`). cold-clear 279edd7 with the patch and Standard::default plays alone from an empty board, with no garbage. The queue is a seeded 7-bag: the current piece plus 5 previews are visible, and one more is revealed per placement. A game is exactly the harness's rollout from that empty position. Same id, seed, CC_NODES and COACH_SEED give byte-identical output; seed 48 re-run alone matched.
2. **Replay through the repo's engine** (cutcopy-selfplay.ts): the vendored Triangle engine, TL ruleset, g = 0, the queue spliced in as runDemo does. Each placement's path comes from the planner's `reach` (a BFS over the engine's own moves, SRS+, 180 allowed) and `inputsOf`.
   - The engine's lock is what gets scored.
   - Wrong piece after a hold, no engine path, or different lines or cells: counted, and the game is cut.
   - Spin-credit disagreements are counted, and the engine's credit is used.
   - Each completed game's final board is compared with cold-clear's final_field.
3. **The corpus matcher, unchanged**: TechDigests (no garbage, every lock inside the prefix) go to `classify(CUTCOPY, …)`. That covers the scored-T-spin rule, the reconstruction check, both variants and both hands, and the matcher's own follow-up in the carried slot.
4. **Positive control** (`--control`): own.3.482 from analysis/cutcopy-own.json gives 1 cutcopy hit, as drawn, at lock 9, with the follow-up fired at lock 12. All 13 of 13 placements are reproduced and the final board is equal.
5. **Near-miss diagnostic** (pilot only, not the matcher): at each full TSD whose T is the window's flat, nub-down T, the number of window cells that disagree, taking the smaller over the two hands. A count of 0 matched every hit.

## Commands
```
git clone https://github.com/MinusKelvin/cold-clear cc && cd cc && git checkout 279edd7c3177ff8077f6a930193397814b281f27
git apply ~/tetrio-replay-report/tools/cc-coach/cold-clear-coach.patch
mkdir -p bot/src/bin && cp ~/tetrio-replay-report/tools/cc-coach/cc-coach.rs bot/src/bin/ && cp ~/tetrio-replay-report/tools/cc-coach/Cargo.lock .
cargo build --release -p cold-clear --bin cc-coach && cd ..
python3 -c "import json;[print(json.dumps({'id':f'sp-{s}','seed':s,'pieces':200})) for s in range(1,201)]" > games-in.jsonl
CC_NODES=40000 COACH_MODE=selfplay COACH_SEED=0 cc/target/release/cc-coach < games-in.jsonl > games-40k.jsonl
bun ~/tetrio-replay-report/tools/cc-coach/cutcopy-selfplay.ts games-40k.jsonl result-40k.json
bun ~/tetrio-replay-report/tools/cc-coach/cutcopy-selfplay.ts --control
```
- Speed: about 0.16 s per piece per core at 40k nodes. 200 games × 200 pieces took 29 min 39 s wall on 4 cores.
- Replay plus classify took 2.5 min, and two runs gave identical output.
- md5 of games-40k.jsonl: 654bbe48bd2ea5df0ef192911aeb3aa7. md5 of result-40k.json: 237379e5687e1c0d12756484d2181de4.

## Numbers (seeds 1-200, 200 pieces each, 40k nodes, COACH_SEED=0)
- **Games:** 200 played, 198 completed on the engine. 40 000 pieces placed by cold-clear, 39 971 replayed.
- **Engine disagreements:** 2 games cut, both no_engine_path for a flat I on the bottom row (seed 136 lock 190, seed 177 lock 181).
- **Checks:** spin-credit disagreements 0; final-board mismatches 0; row map unverified 0; reconstruction disagreements 0.
- **Scored full TSDs:** 3 194, the same as cold-clear's own tsd count. 314 in the opener window, 2 880 mid-game. TSS 172, TST 56.
- **cutcopy hits: 11** (5 as drawn, 6 mirrored). Follow-up fired in 10; the other was slot_filled_before_t.
- **uncut hits: 1**, as drawn, follow-up fired.
- Hits in the opener window: 2.
- cutcopy ablations (no must-empty / no roof / T overlap): 82 / 37 / 18.
- Near-miss for cutcopy (cells off: TSDs): 0: 11, 1: 56, 2: 459, 3: 1 105, 4: 139. 23 TSDs were not a flat, nub-down T.

| seed | lock | variant | hand | follow-up |
|---|---|---|---|---|
| 48 | 81 | cutcopy | as drawn | fired at lock 86 |
| 65 | 19 | cutcopy | mirrored | fired at lock 23 |
| 83 | 58 | cutcopy | mirrored | fired at lock 59 |
| 87 | 11 | cutcopy | mirrored | fired at lock 13 |
| 118 | 131 | cutcopy | mirrored | fired at lock 134 |
| 118 | 144 | cutcopy | as drawn | fired at lock 149 |
| 136 | 83 | uncut | as drawn | fired at lock 84 |
| 173 | 193 | cutcopy | mirrored | fired at lock 196 |
| 176 | 80 | cutcopy | as drawn | fired at lock 88 |
| 186 | 27 | cutcopy | as drawn | not fired: slot_filled_before_t (lock 28) |
| 193 | 26 | cutcopy | as drawn | fired at lock 32 |
| 195 | 135 | cutcopy | mirrored | fired at lock 141 |

To replay a hit, feed `{"id":"sp-<seed>","seed":<seed>,"pieces":200}` with CC_NODES=40000 and COACH_SEED=0.

## Reading
- **Yes, rarely, and it finishes them.** 11 Cut Copies in 3 194 TSDs (about 1 in 290), in 10 of the 200 games, with the second TSD fired in 10 of the 11. Every placement up to each hit was reproduced by the engine and checked by the row map.
- **It is not something cold-clear aims at.** Its evaluator knows TSD slots, not this shape. Close misses are common: 56 TSDs are one window cell off and 459 are two cells off, against 11 exact. Read the hits as a by-product of TSD-slot play.
- **This does not test the source's claim**, which is that Cut Copies mostly arise with rising garbage; self-play has none.
  - For orientation only: analysis/cutcopy-facts.json (read 2026-10-20) has 109 cutcopy hits in 10 058 scored TSDs, 95 of them with garbage in the window. That leaves 14 garbage-free corpus hits in 10 058, against cold-clear's 11 in 3 194.
  - The two are not comparable populations: no clock, no opponent, one search sample per game, and an unconverged budget (the README says the 40k pick equals the 640k pick only 185 of 300 times). And 11 is a small count. This is a pilot reading, not a measurement.
- **uncut appears once** (seed 136, lock 83) where the corpus has none. One event: recorded, not read.
- **The two engine disagreements** are flat bottom-row I placements with no SRS+ path. The likely cause is that cold-clear uses SRS for the I while the engine uses SRS+ (the README's residual table); not investigated further. Neither game was near a hit.

## Caveats a review raised
- **"Reconstruction disagreements 0" cannot fail here.** In the corpus the cleared rows come from the engine's own records; this script computes them from the same pre-lock board and lock cells the check re-derives from, so agreement holds by construction. The checks that can fail are the row map (predicted board against the engine's board) and the line count against cold-clear's.
- **Spin credit is partly chosen.** For a T, the script takes the first engine path whose spin matches cold-clear's and falls back to the first path only when none does. So "spin-credit disagreements 0" says some engine path gives the same credit, not that cold-clear's own path does.
- **The two no-path I placements are unexplained.** SRS against SRS+ is a guess; a limit of the planner's move search is just as possible. Untested.
- **The near-miss counts** treat a window cell off the board as disagreeing, where the matcher calls the window off the board. A diagnostic, not the matcher.

## Next step
Test the source's claim by giving self-play a received-garbage schedule (the rollout already inserts rows), or by grading the corpus's garbage-in-window hits with cold-clear. Using several COACH_SEEDs per game would turn the single draw into a sampled rate.