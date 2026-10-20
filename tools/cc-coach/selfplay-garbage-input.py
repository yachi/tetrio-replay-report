#!/usr/bin/env python3
"""Input lines for cc-coach COACH_MODE=selfplay WITH a received-garbage schedule (research pilot only).

    python3 selfplay-garbage-input.py FIRST LAST PIECES > games-garbage-in.jsonl

One line per seed in [FIRST, LAST]: {"id": "spg-<seed>", "seed": <seed>, "pieces": PIECES, "garbage": [...]}.
The queue is the harness's own (StdRng seeded with `seed`), so a seed gives the SAME queue as the no-garbage
pilot; only the garbage is added.

THE RULE (ours, not TETR.IO's; written down so a schedule can be re-derived from its seed):
  rng = random.Random(f"cc-garbage-{seed}")      # Python's str seeding is deterministic across runs
  j = rng.randint(4, 10) - 1                     # 0-based piece the first attack arrives at
  while j < PIECES:
      lines = rng.randint(1, 4)                  # rows in the attack
      col = rng.randrange(10)                    # hole column, the same for every row of the attack
      emit {"after_piece": j, "lines": lines, "col": col}
      j += rng.randint(4, 10)                    # next attack 4-10 pieces later
i.e. an attack every 7 pieces on average, 2.5 rows on average: about 0.36 rows per piece offered. The corpus's
materialised received garbage (facts.json `garbagereceived` over `pieces`, all sessions) was measured at about
0.43 rows per piece on 2026-10-20 — re-measure it rather than quote it. The harness tanks pending rows only on a
lock that clears nothing, 8 rows at most per lock, and cold-clear sends nothing back, so nothing cancels.
"""
import json
import random
import sys


def schedule(seed: int, pieces: int):
    rng = random.Random(f"cc-garbage-{seed}")
    out = []
    j = rng.randint(4, 10) - 1
    while j < pieces:
        lines = rng.randint(1, 4)
        col = rng.randrange(10)
        out.append({"after_piece": j, "lines": lines, "col": col})
        j += rng.randint(4, 10)
    return out


def main():
    first, last, pieces = (int(a) for a in sys.argv[1:4])
    for s in range(first, last + 1):
        print(json.dumps({"id": f"spg-{s}", "seed": s, "pieces": pieces, "garbage": schedule(s, pieces)}))


if __name__ == "__main__":
    main()
