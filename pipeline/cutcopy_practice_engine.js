// 千鳥格子練習場's in-page engine: a small TETR.IO-like engine for practice — SRS+ kicks, 180
// rotation, the T-spin corner rule — on a y-DOWN board (row 0 the top, 40 rows, the visible 20 are
// rows 20..39). The kick and piece tables are copied from pipeline/sim/oracle-rs/src/data.rs
// (generated from the vendored Triangle engine). Plain browser JS: the page inlines it, and bun
// can require() it (pipeline/openers/cutcopy-drills.test.ts holds it to the reference engine).
// It is NOT the reference engine and is in no count: it only plays the constructed practice drills.
(function (G) {
  const P = "IJLOSTZ";
  const W = 10, H = 40;
  const WIDTH = [4, 3, 3, 2, 3, 3, 3];
  const STATES = [
    [[[0,1],[1,1],[2,1],[3,1]],[[2,0],[2,1],[2,2],[2,3]],[[3,2],[2,2],[1,2],[0,2]],[[1,3],[1,2],[1,1],[1,0]]],
    [[[0,0],[0,1],[1,1],[2,1]],[[2,0],[1,0],[1,1],[1,2]],[[2,2],[2,1],[1,1],[0,1]],[[0,2],[1,2],[1,1],[1,0]]],
    [[[2,0],[0,1],[1,1],[2,1]],[[2,2],[1,0],[1,1],[1,2]],[[0,2],[2,1],[1,1],[0,1]],[[0,0],[1,2],[1,1],[1,0]]],
    [[[0,0],[1,0],[0,1],[1,1]],[[1,0],[1,1],[0,0],[0,1]],[[1,1],[0,1],[1,0],[0,0]],[[0,1],[0,0],[1,1],[1,0]]],
    [[[1,0],[2,0],[0,1],[1,1]],[[2,1],[2,2],[1,0],[1,1]],[[1,2],[0,2],[2,1],[1,1]],[[0,1],[0,0],[1,2],[1,1]]],
    [[[1,0],[0,1],[1,1],[2,1]],[[2,1],[1,0],[1,1],[1,2]],[[1,2],[2,1],[1,1],[0,1]],[[0,1],[1,2],[1,1],[1,0]]],
    [[[0,0],[1,0],[1,1],[2,1]],[[2,0],[2,1],[1,1],[1,2]],[[2,2],[1,2],[1,1],[0,1]],[[0,2],[0,1],[1,1],[1,0]]],
  ];
  const KI = [null,[[1,0],[-2,0],[-2,1],[1,-2]],[[0,-1]],[[-1,0],[2,0],[2,1],[-1,-2]],[[-1,0],[2,0],[-1,2],[2,-1]],null,[[-1,0],[2,0],[-1,-2],[2,1]],[[1,0]],[[0,1]],[[-2,0],[1,0],[-2,-1],[1,2]],null,[[2,0],[-1,0],[2,-1],[-1,2]],[[1,0],[-2,0],[1,2],[-2,-1]],[[-1,0]],[[1,0],[-2,0],[1,-2],[-2,1]],null];
  const KX = [null,[[-1,0],[-1,-1],[0,2],[-1,2]],[[0,-1],[1,-1],[-1,-1],[1,0],[-1,0]],[[1,0],[1,-1],[0,2],[1,2]],[[1,0],[1,1],[0,-2],[1,-2]],null,[[1,0],[1,1],[0,-2],[1,-2]],[[1,0],[1,-2],[1,-1],[0,-2],[0,-1]],[[0,1],[-1,1],[1,1],[-1,0],[1,0]],[[-1,0],[-1,-1],[0,2],[-1,2]],null,[[1,0],[1,-1],[0,2],[1,2]],[[-1,0],[-1,1],[0,-2],[-1,-2]],[[-1,0],[-1,-2],[-1,-1],[0,-2],[0,-1]],[[-1,0],[-1,1],[0,-2],[-1,-2]],null];
  const KICKS = [KI, KX, KX, KX, KX, KX, KX];
  const TC = [[-1,-1,3,0],[1,-1,0,1],[1,1,1,2],[-1,1,2,3]];

  function emptyBoard() { const b = []; for (let y = 0; y < H; y++) b.push(new Array(W).fill(null)); return b; }
  function boardFromRows(rows) { // rows top first, any height <= H, aligned to the floor
    const b = emptyBoard(), off = H - rows.length;
    rows.forEach((r, i) => { for (let x = 0; x < W; x++) { const c = r[x]; b[off + i][x] = (c === "." || c === "-" || c === undefined) ? null : c; } });
    return b;
  }
  function cloneBoard(b) { return b.map(r => r.slice()); }
  function sym(p) { return P.indexOf(p); }
  function cellsOf(p, x, y, r) { return STATES[sym(p)][r].map(([sx, sy]) => [x + sx, y + sy]); }
  function occupied(b, x, y) { return x < 0 || x >= W || y < 0 || y >= H || b[y][x] !== null; }
  function legal(b, cells) { for (const [x, y] of cells) if (occupied(b, x, y)) return false; return true; }
  function spawn(b, p) {
    const s = { p, x: Math.floor(W / 2 - WIDTH[sym(p)] / 2), y: 17, r: 0, spin: "none" };
    if (!legal(b, cellsOf(p, s.x, s.y, 0))) { s.y -= 1; if (!legal(b, cellsOf(p, s.x, s.y, 0))) return null; }
    return s;
  }
  function detectSpin(b, s, tst) {
    if (s.p !== "T") return "none";
    if (legal(b, cellsOf(s.p, s.x, s.y + 1, s.r))) return "none";
    let corners = 0, front = 0;
    for (const t of TC) {
      if (occupied(b, s.x + 1 + t[0], s.y + 1 + t[1])) { corners++; if (s.r === t[2] || s.r === t[3]) front++; }
    }
    if (corners < 3) return "none";
    if (tst) return "full";
    return front === 2 ? "full" : "mini";
  }
  function rotate(b, s, amount) {
    const to = ((s.r + amount) % 4 + 4) % 4, id = s.r * 4 + to;
    let nx = null, ny = null, kick = [0, 0], used = false;
    if (legal(b, cellsOf(s.p, s.x, s.y, to))) { nx = s.x; ny = s.y; }
    else {
      const set = KICKS[sym(s.p)][id];
      if (!set) return null;
      for (const [dx, dy] of set) {
        if (legal(b, cellsOf(s.p, s.x + dx, s.y + dy, to))) { nx = s.x + dx; ny = s.y + dy; kick = [dx, dy]; used = true; break; }
      }
      if (nx === null) return null;
    }
    const tst = used && (((id === 11 || id === 3) && kick[0] === 1 && kick[1] === 2) || ((id === 9 || id === 1) && kick[0] === -1 && kick[1] === 2));
    const n = { p: s.p, x: nx, y: ny, r: to, spin: "none" };
    n.spin = detectSpin(b, n, tst);
    return n;
  }
  function shift(b, s, dx) { const c = cellsOf(s.p, s.x + dx, s.y, s.r); return legal(b, c) ? { ...s, x: s.x + dx } : null; }
  function down(b, s) { const c = cellsOf(s.p, s.x, s.y + 1, s.r); return legal(b, c) ? { ...s, y: s.y + 1, spin: "none" } : null; }
  function dropped(b, s) { let t = s, n; while ((n = down(b, t))) t = n; return t; }
  function lock(b, s) { // returns {board, lines, cleared rows (pre-clear), spin, cells}
    const nb = cloneBoard(b), cells = cellsOf(s.p, s.x, s.y, s.r);
    for (const [x, y] of cells) nb[y][x] = s.p;
    const full = []; for (let y = 0; y < H; y++) if (nb[y].every(v => v !== null)) full.push(y);
    for (let i = full.length - 1; i >= 0; i--) nb.splice(full[i], 1);
    for (let i = 0; i < full.length; i++) nb.unshift(new Array(W).fill(null));
    return { board: nb, lines: full.length, cleared: full, spin: s.spin, cells };
  }
  function addGarbage(b, n, col) {
    const nb = cloneBoard(b);
    for (let i = 0; i < n; i++) { nb.shift(); const row = new Array(W).fill("G"); row[col] = null; nb.push(row); }
    return nb;
  }
  const key = (cells) => cells.map(([x, y]) => y * W + x).sort((a, b) => a - b).join(",");

  // BFS over inputs: every resting placement of piece p, with its shortest key path and the spin at lock.
  // moves: L R (tap), LL RR (to wall), cw ccw 180, sd (soft drop to floor). A lock is a hard drop.
  function placements(b, p) {
    const st = spawn(b, p); if (!st) return [];
    const seen = new Map(), out = new Map(), q = [[st, []]];
    const sk = (s) => `${s.x},${s.y},${s.r},${s.spin}`;
    seen.set(sk(st), true);
    const moves = [
      ["←", s => shift(b, s, -1)], ["→", s => shift(b, s, 1)],
      ["⇤", s => { let t = s, n; let m = false; while ((n = shift(b, t, -1))) { t = n; m = true; } return m ? t : null; }],
      ["⇥", s => { let t = s, n; let m = false; while ((n = shift(b, t, 1))) { t = n; m = true; } return m ? t : null; }],
      ["↻", s => rotate(b, s, 1)], ["↺", s => rotate(b, s, -1)], ["180", s => rotate(b, s, 2)],
      ["↓", s => { const d = dropped(b, s); return d.y !== s.y ? d : null; }],
    ];
    while (q.length) {
      const [s, path] = q.shift();
      const d = dropped(b, s);
      const fin = d.y === s.y ? s : d; // hard drop
      const k = key(cellsOf(fin.p, fin.x, fin.y, fin.r)) + "|" + fin.spin;
      if (!out.has(k)) out.set(k, { state: fin, path: path.concat(["硬降"]) });
      if (path.length > 12) continue;
      for (const [name, f] of moves) {
        const n = f(s); if (!n) continue;
        const kk = sk(n); if (seen.has(kk)) continue; seen.set(kk, true);
        q.push([n, path.concat([name])]);
      }
    }
    return [...out.values()];
  }

  // ---- the Cut Copy window. The window data is NOT typed here: the page passes the windows the
  // drills artefact carries (analysis/cutcopy-drills.json `windows`, from technique-facts.ts's
  // prepare() for the cutcopy and uncut variants, both hands), and the rule below is the one
  // technique-facts.ts's windowMatch applies: the T's cells equal the window's T under one
  // translation (row offset from the top T row, column offset from the leftmost T column), every
  // window cell is on the board, '#' cells filled (garbage counts as filled) and '.' cells empty.
  let WINDOWS = [];
  function setWindows(ws) { WINDOWS = ws.slice(); }
  // b = board BEFORE the T locks, tcells = the T's cells [x,y]. Returns {variant, mirrored, follow
  // (absolute [x,y]), cells [x,y,ch] ('X' for a cell outside the box), box} or null.
  function matchWindow(b, tcells) {
    const tk = key(tcells);
    for (const w of WINDOWS) {
      if (tcells.length !== w.T.length) continue;
      const dy = Math.min(...tcells.map(c => c[1])) - Math.min(...w.T.map(t => t.r));
      const dx = Math.min(...tcells.map(c => c[0])) - Math.min(...w.T.map(t => t.c));
      if (key(w.T.map(t => [t.c + dx, t.r + dy])) !== tk) continue;
      let ok = true; const wc = [];
      for (const q of w.cells) {
        const x = q.c + dx, y = q.r + dy;
        if (x < 0 || x >= W || y < 0 || y >= H) { ok = false; break; }
        wc.push([x, y, q.extra ? "X" : q.v]);
        if (q.v === "T") continue;
        if (q.v === "#" && b[y][x] === null) { ok = false; break; }
        if (q.v === "." && b[y][x] !== null) { ok = false; break; }
      }
      if (!ok) continue;
      return { variant: w.id, mirrored: w.mirrored, follow: w.followup.map(f => [f.c + dx, f.r + dy]),
               box: { x: w.box.c0 + dx, y: w.box.r0 + dy, w: w.box.c1 - w.box.c0 + 1, h: w.box.r1 - w.box.r0 + 1 }, cells: wc };
    }
    return null;
  }
  // carry slot cells through a lock's cleared rows (pre-clear y) — null if a slot cell was cleared
  function carry(cells, cleared) {
    const out = [];
    for (const [x, y] of cells) { if (cleared.includes(y)) return null; out.push([x, y + cleared.filter(r => r > y).length]); }
    return out;
  }

  // ---- a practice run: the game state machine shared by the page and the build-time checker.
  // events: {kind:"garbage", before: lockIndex, n, col}
  function newRun(puzzle) {
    let board = boardFromRows(puzzle.start);
    // garbage that arrives before the first lock (before: 0) is on the board from the start
    for (const e of (puzzle.events || [])) if (e.kind === "garbage" && e.before === 0) board = addGarbage(board, e.n, e.col);
    return { board, queue: puzzle.queue.slice(), hold: puzzle.hold || null, holdUsed: false,
             locks: 0, stage: 0, slot: null, hit: null, done: false, failed: null, log: [] };
  }
  // apply one lock of state s; mutate run; returns a feedback entry
  function applyLock(run, puzzle, s) {
    const before = run.board;
    const res = lock(before, s);
    const fb = { piece: s.p, cells: res.cells, lines: res.lines, spin: res.spin, msg: null, good: null };
    const build = puzzle.mode === "build";
    if (run.stage === 0) {
      if (s.p === "T" && res.lines > 0) {
        const m = matchWindow(before, res.cells);
        if (m && res.spin === "full" && res.lines === 2) {
          run.stage = 1; run.hit = m; run.slot = carry(m.follow, res.cleared);
          fb.good = true; fb.msg = "first";
        } else if (s.p === "T" && !build) { fb.good = false; fb.msg = m ? "notfull" : "nowindow"; }
      } else if (s.p === "T" && !build) { fb.good = false; fb.msg = "t_noclear"; }
    } else if (run.stage === 1) {
      if (s.p === "T") {
        if (key(res.cells) === key(run.slot) && res.spin === "full" && res.lines === 2) { run.stage = 2; run.done = true; fb.good = true; fb.msg = "second"; }
        else { fb.good = false; fb.msg = key(res.cells) === key(run.slot) ? "second_notfull" : "second_wrong"; run.failed = fb.msg; }
      } else {
        const filled = res.cells.some(c => run.slot.some(d => d[0] === c[0] && d[1] === c[1]));
        if (filled) { fb.good = false; fb.msg = "slot_filled"; run.failed = "slot_filled"; }
        else { const n = carry(run.slot, res.cleared); if (!n) { fb.good = false; fb.msg = "slot_cleared"; run.failed = "slot_cleared"; } else run.slot = n; }
      }
    }
    run.board = res.board; run.locks++;
    for (const e of (puzzle.events || [])) if (e.kind === "garbage" && e.before === run.locks) {
      run.board = addGarbage(run.board, e.n, e.col);
      if (run.slot) run.slot = run.slot.map(([x, y]) => [x, y - e.n]);
    }
    if (run.stage === 0 && s.p === "T" && fb.good === false) run.failed = run.failed || fb.msg;
    run.log.push(fb);
    return fb;
  }
  // every reachable T placement that fires the window as a full TSD (shortest key path first)
  function findBuild(b) {
    const out = [];
    for (const pl of placements(b, "T")) {
      if (pl.state.spin !== "full") continue;
      const r = lock(b, pl.state); if (r.lines !== 2) continue;
      const m = matchWindow(b, r.cells); if (!m || !carry(m.follow, r.cleared)) continue;
      out.push({ state: pl.state, path: pl.path, m, cells: r.cells });
    }
    out.sort((a, c) => a.path.length - c.path.length);
    return out[0] || null;
  }
  // the second T straight into the carried slot, if reachable now
  function findSecond(b, slot) {
    const k = key(slot);
    for (const pl of placements(b, "T").sort((a, c) => a.path.length - c.path.length)) {
      if (pl.state.spin !== "full") continue;
      const r = lock(b, pl.state); if (r.lines === 2 && key(r.cells) === k) return { state: pl.state, path: pl.path };
    }
    return null;
  }
  const API = { findBuild, findSecond, W, H, P, STATES, emptyBoard, boardFromRows, cloneBoard, cellsOf, legal, spawn, rotate, shift, down, dropped, lock, addGarbage,
                placements, matchWindow, setWindows, windows: () => WINDOWS, carry, key, newRun, applyLock, KICKS };
  if (typeof module !== "undefined" && module.exports) module.exports = API; else G.CCE = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
