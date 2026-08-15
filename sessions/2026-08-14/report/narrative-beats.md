# 2026-08-14 — narrative beats

Sixth session. **pinglamb 7 : yachi 4** over 11 matches and 84 rounds — the largest
session in the corpus by both counts (previous max: 79 rounds on 2026-07-22).

Every beat below names the claim that pins it. Nothing goes into the report that does not.

---

## 1. The night has three acts, and they are the whole story

pinglamb took matches 1-3. yachi took four of matches 4-9. pinglamb took matches 10-11.
All eleven match winners are pinned in one claim [C001], and the per-match scores are
[G004]-[G014].

The efficiency gap tracks the acts exactly [C007]:

| window | pinglamb APP / yachi APP |
|---|---|
| m1-3 | over 17% |
| m4-9 | under 7% |
| m10-11 | over 11% |

The middle window is the only one yachi won a match in — and he won four there.

## 2. The finding: the floors have met, the ceilings have not

Split all 84 rounds by who won them and pool attack over pieces:

```
rounds won     yachi 2598/4307 = .6032    pinglamb 2665/3715 = .7174   → +18.9%
rounds lost    yachi 2113/3754 = .5629    pinglamb 2252/3931 = .5729   →  +1.8%
```

[C002]. Both players now *lose* at essentially the same rate — within 2%. What separates
them is what winning looks like.

Said within a player [C003]: pinglamb's own won-vs-lost separation is +25%, yachi's is
only +7%. The generated ledger states each side of that separately ([G071], [G072]); the
comparison between them is the hand claim.

And the sharp form [C004]: yachi's *best* regime (.6032) sits 5% above pinglamb's *worst*
(.5729) and more than 15% below pinglamb's best (.7174). His ceiling is nearer his
opponent's floor than his opponent's ceiling.

**This is the exact mirror of 2026-08-09**, where the won-round gap was under 2% and the
lost-round gap over 25%. Two nights running, the same session-level APP gap decomposes the
opposite way. That is why the decomposition is a claim and not a note: reading the session
total alone would have called these two nights the same night.

For the record, the six-session series of the two gaps:

```
won-gap    +5.8  +10.8  +5.9  +7.9   +1.8  +18.9
lost-gap  +12.8   +7.3  +6.0  +6.1  +25.4   +1.8
```

yachi's own won-round APP had sat in a .657-.674 band for five sessions. This night it is
.6032.

## 3. The volume route, third run, and its price

yachi placed **415 more pieces** and landed **206 less attack** — over 4% of pinglamb's
total [C005]. Same route as 2026-08-01 (bought the gap back to within 32 lines) and
2026-08-09 (missed by 271 lines). Two failures running.

What it cost is in the death tally [C006]: **11 of the 13 topouts are yachi's**, pinglamb
has 2. On 2026-08-09 all four topouts were pinglamb's and yachi had none — so this column
has swung from one extreme to the other in a single session. It is yachi's worst topout
count of six sessions.

## 4. Style is stable across all six sessions

yachi opens quads (398 vs 320) [G038]; pinglamb plays T-spins (531 vs 430 raw [G037],
TSD 371 vs 312 [G039], TST 89 vs 50 [G040]). Both directions hold in all six sessions.
That is the mechanism behind [G045] — pinglamb's attack per piece is higher because a
T-spin costs fewer pieces per line sent.

## 5. Perfect clears: the most of any session, and still no signal

20 All Clears (yachi 11, pinglamb 9) [G041] — the corpus previously held 65 across five
sessions. yachi had one in 11 rounds and won 5 [G081]; in the 9 rounds where only he had
one, he lost 5 [G082]. pinglamb: 8 rounds, won 6 [G083]; 6 solo rounds, lost 1 [G084].
Paired AUC for All Clears this session is 52.4% with 68 ties. Reported as counts, never a
rate — the denominators are 8-11 rounds.

## 6. KPP is flat for the sixth time

3.5989 vs 3.5830, 0.4% apart; paired AUC 40.5%, i.e. below chance again [G066], [G073],
[G074]. Six sessions, same negative result.

## 7. VS decides, for the sixth time

All 84 rounds: the winner held the higher VS [G028]. 100% for the sixth consecutive
session, now over 380 rounds of corpus.

---

## Rounds worth a card

- **m1r3** — 約239.7 s, the night's longest [G025]; yachi cleared 202 lines, the session
  single-round maximum [G024]; both players got a perfect clear in it; pinglamb hit combo
  7 [G021]. yachi won it.
- **m2r2** — pinglamb's 19-line spike [G020] and 8-deep B2B [G022], both session maxima.
- **m2r6** — 約11.2 s, the shortest round [G026]; pinglamb's unqualified APM peak 約125.6
  [G079]; he conceded 0 garbage, the cleanest win of the night [G061].
- **m3r7** — 約12.0 s. yachi's VS was 約8.3; pinglamb's 約196.0.
- **m6r6 → m7r3** — yachi's 8-round winning run, spanning two matches [G017].
- **m7r4** — pinglamb took two perfect clears in one round, yachi one, and pinglamb won it.
- **m8** — the night's only sweep, 0-5 [G015], [G058].
- **m10r5** — pinglamb's unqualified VS peak 約217.4 in a 20-second round [G080].
- **m11r2** — 約170.1 s. Holds both qualified rate records: yachi's APM 約71.2 [G018] and
  pinglamb's VS 約163.1 [G019]; the highest combined VS of any qualifying round, 約317.2
  [G065]; yachi's 18 T-spins [G023]; and the night's biggest comeback — pinglamb absorbed
  165 lines of queued attack to yachi's 133 and won anyway [G029].
- **The deciders** — three matches went to a final round [G016]: m4 (yachi, VS 約78.1 to
  約24.9) [G062], m5 (pinglamb, 約123.7 to 約99.1) [G063], m7 (yachi, 約109.1 to 約103.0)
  [G064].
- **APM 65+** — pinglamb reached it in 21 rounds and won all 21 [G052]; yachi reached it in
  10 and won 7 [G051].
