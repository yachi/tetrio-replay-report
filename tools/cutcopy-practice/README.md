# 千鳥格子練習場 — manual playwright runs

These scripts drive the practice page in a headless browser (an iPhone 13 profile). They solve every drill
with its committed solution, by touch drag, and then play the demo. **They are manual runs, not a gate.**
No workflow runs them and no build depends on them. A red or green run here proves nothing to CI. The
page's gate is `python3 -m pipeline.cutcopy_practice_page --selftest`, and the drills' gate is
`bun test pipeline/openers/cutcopy-drills.test.ts`.

- `run.js` is the one to use. It reads a rendered `practice-cutcopy.html` and `analysis/cutcopy-drills.json`,
  injects a `CC_STATE` hook into the page script, and writes `solved/*.png` and `full.png` under the output
  directory:

  ```bash
  bin/build-docs --out <dir>
  node tools/cutcopy-practice/run.js <dir>/practice-cutcopy.html analysis/cutcopy-drills.json <out-dir>
  ```

  It prints one JSON row per drill (the lock it passed at, the status line, the demo caption), the page's
  errors and every network request the page made. Each of those should be empty. It also prints
  `scrollWidth` against `innerWidth`; at phone width the two should be equal.

- `t7.js` and `t8.js` are the originals, written against the scratch build the page came from. They read a
  `cc-test.html` with the `CC_STATE` hook already in it, plus that build's `drills.json` / `paths.json`, so
  they do not run as they are against this repository. They are kept as the record of what was checked
  before the page landed. `run.js` is `t7.js` adapted to the rendered page.

Playwright is not a dependency of this repository. Install it wherever you run these.
