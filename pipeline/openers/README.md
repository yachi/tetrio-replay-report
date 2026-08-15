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
                                        sessions/2026-07-28 sessions/2026-08-01 \
                                        sessions/2026-08-09 sessions/2026-08-14
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

## What it found (2026-08-10, all five sessions)

| | |
|---|---|
| rounds with a verified clean 7-piece first bag | **358** of 592 |
| within 4 cells of any catalogued **C-Spin** | **0** — nearest is 6 cells |
| within 4 cells of any catalogued **DT Cannon** | **0** — nearest is 6 cells |
| rounds holding a `self_built` Triple | 264, and none of them near a C-Spin either |
| exact first-bag matches | **5**, all of them PCO |

So the players' Triples are **not** catalogued C-Spin openers, which retires the "self_built is
C-Spin execution" reading. What survives is weaker and still measured: early roofs, triple-heavy,
canonical TST slot geometry.

## Which pages count as "a C-Spin" is the whole argument — so all four sets are reported

A distance to "the C-Spin set" cannot be told apart from an artefact of picking that set, and this
set is genuinely doubtful. `isCSpin` is a substring match, and **not one of the three names it
selects is the C-Spin as harddrop draws it**:

- `Fake C-Spin {JP: 偽TKI}` — by its own name a *fake*;
- `Secspin {JP: None}` — a different opener whose name merely ends in those letters;
- a compound page listing `SDPC-Spin` among eight names.

`openers.test.ts` asserts exactly that, so if a future catalogue carries the real thing the test
fails and this paragraph has to be rewritten rather than quietly outlived.

The answer therefore has to be shown to survive the set choice, and `match.ts` defines four sets for
that (`NAME_SETS`), reported side by side by `emit-opener-facts.ts`:

| set | openers | pages | nearest, over 358 bags | within 4 cells |
|---|---|---|---|---|
| C-Spin (by name) | 3 | 8 | 6 cells | 0 |
| C-Spin **or TKI** | 6 | 24 | 6 cells | 0 |
| DT Cannon | 6 | 12 | 6 cells | 0 |
| DT family (widest — any name carrying "DT") | 48 | 115 | 4 cells | 1 |

The middle row is the one that matters. C-Spin is commonly identified with TKI, `TKI-3 {Alt: TKI}`
is catalogued with 12 pages that `isCSpin` does not select, and **widening to it does not move the
answer** — so the null does not depend on settling whether C-Spin *is* TKI, which is a taxonomy
question this repo has no authority to settle. Same for DT: the narrow reading and the widest
reading agree that nothing lands inside the threshold, with one board in 2026-07-22 sitting 4 cells
from a DT-family page that the narrow set does not contain.

For scale, against **any** catalogued opener: 5 of the 358 bags are exact (all PCO), 1 more is
within 2 cells, **244 sit in the 3–4 band** and 104 in the 5–8 band. So boards do get close to the
catalogue in general — the instrument is not simply reporting "far from everything" — and the
C-Spin and DT rows are far in a way the `any` row is not. `Ichinoseki Variable` is the nearest page
for 236 of the 358, which is a fact about these players' stacking, not about either opener here.

**What still bounds the negative:** coverage, not the matcher. This is "not these catalogued pages",
never "no C-Spin anywhere", and no distance threshold buys the stronger sentence. Widening it means
a better catalogue — or an enumeration by construction — not better matching code. See ROADMAP.

## Controls

A lookup that finds nothing is indistinguishable from a lookup that is broken, so `openers.test.ts`
runs four before the result is allowed to mean anything: every C-Spin page fed back in is named as
itself; each is found again mirrored; a board no opener draws is named as nothing; and a page
shifted by one row is strictly further away than the page itself, which is what rules out a constant
misalignment masquerading as "everyone plays a 3-cell variant".

Three more guard the name sets themselves, because a regex that selects the wrong pages turns every
number above into a sentence about nothing: what `isCSpin` selects is asserted by name; `isDTCannon`
is required to carry `DT Cannon {JP: 開幕DT砲}` and to reject the four substring hits (`SDT`, `SDDT`,
`SZDT`, `NEWDT` Cannon) that a bare `/DT ?Cannon/` would swallow; and TKI is required to be present
under its own name, since otherwise the wide reading would be the narrow one reported twice.

## The report metric

`pipeline/sim/emit-opener-facts.ts` turns this into `sessions/<date>/sim/opener-facts.json`, which
`pipeline/opener_section.py` renders into each report — quarantined exactly like the forecast
section, with no claim ids and no ✓ badges, because it is simulator-derived. The first-bag
comparison above is one of its metrics; the others are the **ordering** of the two T-spins
(DT Cannon is a Double then a Triple, the C-Spin a Triple then a Double) and the **slot geometry**
against harddrop's own diagrams. See that emitter's docstring for what each one's control is.

## Two of these are not openers at all

`wiki-tspin-techniques.json` (built by `extract_wiki_techniques.py`, same discipline as
`wiki-openers.json`) carries harddrop's **Donation** and **STMB Cave** pages. Neither is an opener —
both are filed under `Mid-game T-Spin setups` and drawn on partial stacks — so they are scored as
per-T-spin board-state predicates over the whole round, never against a first bag. The file holds
each page's drawn boards **with the outcome the article shows** (`clears`, `well_col`, `cavity`,
`cave_width`), which is what makes them instrument controls rather than illustrations: `openers.test.ts`
runs the shipped predicates over them and requires every positive to fire and every negative — including
harddrop's own one-cell minimal pair, "a case where an S donation does not work" — to be rejected.
