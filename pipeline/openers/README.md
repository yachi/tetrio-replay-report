# `openers/` — naming the opener a round played

Answers one question: **is this first bag a catalogued opener, and which one?**

The catalogue is [`swng/opener_db`](https://github.com/swng/opener_db), itself a scrape of
Ivan(28283)'s Comprehensive Opener Database. It is vendored here **already decoded** —
`opener-fields.json` holds plain 10-wide row strings, not fumen — so nothing in `pipeline/` needs a
dependency, and a change upstream shows up in a diff as changed boards rather than as changed
base64. The fetch is pinned to commit `b4a66878`, and the sha256 of the upstream `data.json` is
recorded in the file and asserted in the test.

```fish
bun run pipeline/openers/run-openers.ts sessions/2026-07-22 sessions/2026-07-24 \
                                        sessions/2026-07-28 sessions/2026-08-01
REPLAY_DIR=sessions/2026-07-22 bun test pipeline/openers/openers.test.ts
bun add tetris-fumen; bun run pipeline/openers/fetch-catalogue.ts   # only to re-vendor
```

## The rule

After N locks with no line clear and no garbage, a board holds exactly 4N cells. Any catalogue page
with 4N cells is a candidate, and the board played that opener **iff the two fields are equal cell
for cell**, as drawn or mirrored (columns reversed, `L<->J`, `S<->Z`). Distance is Hamming over the
bottom-aligned 8-row grid, which is what makes "a variant" and "a different opener" distinguishable.

Comparison is by **occupancy, not colour**: many catalogue pages are drawn all-grey (`X` = "any
piece"), which is why opener_db's own front-end greys fumens before comparing. A colour test against
a grey page can only fail.

## What it found (2026-08-06, all four sessions)

| | |
|---|---|
| rounds with a verified clean 7-piece first bag | **300** of 492 |
| within 4 cells of any catalogued **C-Spin** | **0** — nearest band is 5–8 cells (220 rounds) |
| rounds holding a `self_built` Triple | 219, and none of them within 4 cells of a C-Spin either |
| exact first-bag matches | **5**, all of them PCO |

So the players' Triples are **not** catalogued C-Spin openers, which retires the "self_built is
C-Spin execution" reading. What survives is weaker and still measured: early roofs, triple-heavy,
canonical TST slot geometry.

**What bounds that negative:** the catalogue holds **3 distinct C-Spin openers, 8 drawn pages**. This
is "not these C-Spins", not "no C-Spin anywhere". Widening it means a better catalogue, not a better
matcher.

## Controls

A lookup that finds nothing is indistinguishable from a lookup that is broken, so `openers.test.ts`
runs four before the result is allowed to mean anything: every C-Spin page fed back in is named as
itself; each is found again mirrored; a board no opener draws is named as nothing; and a page
shifted by one row is strictly further away than the page itself, which is what rules out a constant
misalignment masquerading as "everyone plays a 3-cell variant".
