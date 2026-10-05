/* 重播 player — ONE source for every simulator replay this repo publishes: the 最癲一局 region
   (pipeline/replay_section.py, inlined verbatim so that region's drift gate re-renders it too) and
   the per-session replay page (pipeline/replay_page.py, which inlines this same file and mounts it
   once per round the viewer picks). It defines `rpReplay.mount` and does nothing on its own.

   Rules this file keeps, each one a trap the report has shipped before:
   - nodes are built with createElement / textContent, never by assigning markup strings;
   - every class is rp- prefixed and every rule is scoped under #round-replay (check_generated_css);
   - keys act only while the player box has focus (WCAG 2.1.4), and it starts PAUSED (2.2.2);
   - prefers-reduced-motion is re-read on change: no drop tween, no clear flash;
   - per-piece rates name 每粒 and are FLOORED, because 約 means "at least" in this report;
   - colours come from the report's own tokens (--p1/--p2 via the section's --rp-c0/--rp-c1, which
     fall back to the player-named tokens of the oldest shells), re-read when the theme moves;
   - in the report the hash is #replay-m<pos>r<round>@p<n>, written with replaceState, and never
     touches the round table's #rounds= state; on the replay page the page owns the hash
     (opts.hashPrefix null) and hears every move through opts.onChange. */
(function () {
  "use strict";
  var NS = window.rpReplay = window.rpReplay || {};

  /* mount(root, box, D, opts) — root is the #round-replay element (tokens are read off it), box
     the .rp-player inside it, D one round's payload. opts: hashPrefix (string, or null to leave
     the hash alone), pos (initial position), onChange(pos, frames, playing) — called on every
     animation frame while playing, so a listener that writes history must wait for playing to
     be false (pause() reports the final position that way). Returns a handle whose
     destroy() drops every listener the player put outside `box`. */
  NS.mount = function (root, box, D, opts) {
    opts = opts || {};
    var W = D.width, ROWS = D.rows, VIS = D.visible, NEXT = D.next;
    var CELLS = W * ROWS;
    var N = D.order.length;
    var CODE = { I: 1, O: 2, T: 3, S: 4, Z: 5, J: 6, L: 7, G: 8 };
    var LETTER = ["", "I", "O", "T", "S", "Z", "J", "L", "G"];
    var PIECE_COLOR = ["", "#3fb8c4", "#d9b638", "#9b5fd0", "#4caf50", "#d64f4a", "#4a72d1", "#e08a35"];
    var LINE_NAME = ["", "Single", "Double", "Triple", "Quad"];
    var SPIN_PREFIX = ["", "Mini T-spin ", "T-spin "];

    function $(sel) { return box.querySelector(sel); }
    function el(tag, cls, text) {
      var e = document.createElement(tag);
      if (cls) e.className = cls;
      if (text != null) e.textContent = text;
      return e;
    }

    /* ---------- decoding: mirror of emit-replay.ts decodeTimeline / queueStates ---------- */
    function placeCells(piece, place) {
      if (Array.isArray(place)) return place.slice();
      var shape = D.shapes[piece][Math.floor(place / CELLS)];
      var a = place % CELLS, ax = a % W, ay = Math.floor(a / W);
      return shape.map(function (d) { return (ay + d[1]) * W + ax + d[0]; });
    }

    function decodePlayer(p) {
      var n = p.locks.length, seq = D.seq;
      var boards = [new Uint8Array(CELLS)], pre = [], cleared = [], cells = [], pieces = [];
      var queue = [];            // state BEFORE lock k: {cur, hold, ptr}
      var cur = seq[0], ptr = 1, hold = "";
      var b = new Uint8Array(CELLS);
      var absF = [], atk = [0], ins = [0], f = 0;
      for (var k = 0; k < n; k++) {
        var lk = p.locks[k];
        queue.push({ cur: cur, hold: hold, ptr: ptr });
        if (lk[5]) {
          if (hold === "") { hold = cur; cur = seq[ptr++]; } else { var t = hold; hold = cur; cur = t; }
        }
        var piece = cur;
        pieces.push(piece);
        // 1. garbage, in order, the engine's own splice
        var g = 0;
        lk[4].forEach(function (gc) {
          var col = gc[0], amt = gc[1];
          g += amt;
          var rows = [];
          for (var y = 0; y < ROWS; y++) rows.push(b.subarray(y * W, y * W + W).slice());
          var add = [];
          for (var i = 0; i < amt; i++) {
            var r = new Uint8Array(W).fill(8); r[col] = 0; add.push(r);
          }
          rows.splice.apply(rows, [0, 0].concat(add));
          rows.splice(ROWS - amt - 1, amt);
          for (var yy = 0; yy < ROWS; yy++) b.set(rows[yy], yy * W);
        });
        // 2. the piece
        var pc = placeCells(piece, lk[1]);
        pc.forEach(function (c) { b[c] = CODE[piece]; });
        pre.push(b.slice());
        cells.push(pc);
        // 3. clears
        var full = [];
        for (var y2 = 0; y2 < ROWS; y2++) {
          var all = true;
          for (var x = 0; x < W; x++) if (!b[y2 * W + x]) { all = false; break; }
          if (all) full.push(y2);
        }
        cleared.push(full);
        if (full.length) {
          var keep = [];
          for (var y3 = 0; y3 < ROWS; y3++) if (full.indexOf(y3) < 0) keep.push(b.slice(y3 * W, y3 * W + W));
          b = new Uint8Array(CELLS);
          keep.forEach(function (r, i) { b.set(r, i * W); });
        }
        boards.push(b.slice());
        f += lk[0];
        absF.push(f);
        atk.push(atk[k] + lk[6]);
        ins.push(ins[k] + g);
        cur = seq[ptr++];
      }
      queue.push({ cur: cur, hold: hold, ptr: ptr });
      // the meter: queued (recorded 射埋 events) − cancelled (attack − sent) − inserted, by frame
      var outAt = [0];
      for (var k2 = 0; k2 < n; k2++) {
        var g2 = 0;
        p.locks[k2][4].forEach(function (gc) { g2 += gc[1]; });
        outAt.push(outAt[k2] + (p.locks[k2][6] - p.locks[k2][7]) + g2);
      }
      return { boards: boards, pre: pre, cleared: cleared, cells: cells, pieces: pieces, queue: queue,
               absF: absF, atk: atk, ins: ins, outAt: outAt };
    }

    var P = D.players.map(function (p) { return { d: p, x: decodePlayer(p) }; });

    // merged position -> locks applied per player, and the frame each position is reached at
    var countAt = [[0], [0]], tAt = [0];
    (function () {
      var c = [0, 0];
      for (var i = 0; i < N; i++) {
        var s = +D.order[i];
        c[s]++;
        countAt[0].push(c[0]); countAt[1].push(c[1]);
        tAt.push(P[s].x.absF[c[s] - 1]);
      }
    })();
    var T_END = Math.max(P[0].d.frames, P[1].d.frames, tAt[N]);
    function posOfLock(s, i) {   // merged position AFTER player s's lock i
      for (var q = 1; q <= N; q++) if (countAt[s][q] === i + 1) return q;
      return N;
    }

    /* ---------- tokens ---------- */
    var tok = {};
    function readTokens() {
      // read off the section, not :root, so the section's own scoped tokens (--rp-c0/1, --rp-bad)
      // resolve; every shell token inherits down to it
      var cs = getComputedStyle(root);
      ["--bg-sunken", "--bg-raised", "--grid-line", "--muted", "--ink", "--ink-secondary", "--rp-c0",
       "--rp-c1", "--rp-bad", "--good", "--pending", "--border-strong"].forEach(function (n) {
        var v = cs.getPropertyValue(n).trim();
        if (!v) throw new Error("replay: CSS token " + n + " is not defined");
        tok[n] = v;
      });
    }
    readTokens();

    var motionQ = window.matchMedia ? matchMedia("(prefers-reduced-motion: reduce)") : null;
    var reduced = !!(motionQ && motionQ.matches);

    /* ---------- the DOM the player owns ---------- */
    var boardsEl = $(".rp-boards");
    var C = 16;                                   // logical cell size
    var HOLD_W = 4.6, GAP = 0.4, METER_W = 0.6, NEXT_W = 4.6, TOP = 1;
    var CW = (HOLD_W + GAP + METER_W + 0.2 + W + GAP + NEXT_W) * C;
    var CH = (VIS + TOP) * C;
    var BX = (HOLD_W + GAP + METER_W + 0.2) * C;  // board left edge
    var sides = P.map(function (pp, s) {
      var side = el("div", "rp-side");
      side.setAttribute("data-slot", String(s));
      var name = el("div", "rp-name", pp.d.user + (pp.d.user === D.winner ? "（贏咗呢局）" : ""));
      var callout = el("div", "rp-callout");
      var cv = el("canvas", "rp-canvas");
      cv.setAttribute("role", "img");
      cv.width = Math.round(CW); cv.height = Math.round(CH);
      var strip = el("div", "rp-strip");
      var state = el("div", "rp-state");
      var flag = el("div", "rp-flag", D.flag_words);
      flag.hidden = true;
      side.appendChild(name); side.appendChild(callout); side.appendChild(cv);
      side.appendChild(strip); side.appendChild(state); side.appendChild(flag);
      boardsEl.appendChild(side);
      cv.addEventListener("click", function (e) {
        var r = cv.getBoundingClientRect();
        if (e.clientX - r.left < r.width / 2) stepBy(-1); else stepBy(1);
      });
      return { side: side, cv: cv, callout: callout, strip: strip, state: state, flag: flag };
    });

    var seek = $(".rp-seek"), posEl = $(".rp-pos"), playBtn = $('[data-act="play"]');
    var speedSel = $(".rp-speed"), live = $(".rp-sr"), help = $(".rp-help");
    var lettersBtn = $('[data-act="letters"]'), helpBtn = $('[data-act="help"]');
    seek.max = String(N);

    function frac(q) { return "calc(8px + (100% - 16px) * " + (N ? q / N : 0) + ")"; }

    // boundary bands: three states per player
    P.forEach(function (pp, s) {
      var band = $('.rp-band[data-slot="' + s + '"]');
      var v = pp.d.verified_to, n = pp.d.locks.length;
      var cut = v >= 0 ? posOfLock(s, v) : 0;
      function seg(a, b, st) {
        if (b <= a) return;
        var g = el("i", "rp-seg");
        g.setAttribute("data-state", st);
        g.style.left = frac(a);
        g.style.width = "calc((100% - 16px) * " + (b - a) / N + ")";
        band.appendChild(g);
      }
      seg(0, cut, "verified");
      if (pp.d.after === "no_evidence") seg(cut, N, "no_evidence");
      if (pp.d.after === "check_failed") seg(cut, N, "check_failed");
      if (pp.d.after === "end" && n) seg(cut, N, "verified");
    });

    // key moments: markers on the bar + a list, both focusable buttons
    var marks = $(".rp-marks"), list = $(".rp-moments");
    var momentBtns = D.moments.map(function (m) {
      var q = m[0], who = m[1], kind = m[2], label = m[3];
      var mk = el("button", "rp-mark");
      mk.type = "button";
      mk.setAttribute("data-slot", String(who));
      mk.setAttribute("data-kind", kind);
      mk.style.left = frac(q);
      mk.setAttribute("aria-label", label + "（第 " + q + " 粒）");
      mk.title = label;
      mk.addEventListener("click", function () { pause(); setPos(q, true); announceMoments(q); });
      marks.appendChild(mk);
      var li = el("li");
      var b = el("button", "rp-moment", fmtTime(tAt[q]) + " " + label);
      b.type = "button";
      b.addEventListener("click", function () { pause(); setPos(q, true); announceMoments(q); });
      li.appendChild(b);
      list.appendChild(li);
      return b;
    });

    /* ---------- state ---------- */
    var pos = 0, t = 0, playing = false, raf = 0, last = 0, letters = false, touched = false;
    var fx = [null, null];         // per player: {k, t0, drop}

    function fmtTime(frames) {
      var tenths = Math.floor(frames / 6);
      var s = Math.floor(tenths / 10), m = Math.floor(s / 60);
      var ss = s % 60;
      return m + ":" + (ss < 10 ? "0" : "") + ss + "." + (tenths % 10);
    }
    function floor2(x) { return (Math.floor(x * 100) / 100).toFixed(2); }

    function describe(s, i) {
      var lk = P[s].d.locks[i];
      var x = P[s].x;
      var lines = lk[2], spin = lk[3], words = "";
      var empty = lines > 0 && x.boards[i + 1].every(function (v) { return v === 0; });
      if (empty) words = "全消";
      else if (spin && lines) words = SPIN_PREFIX[spin] + LINE_NAME[lines];
      else if (lines) words = LINE_NAME[lines];
      if (lk[6]) words += (words ? " " : "") + "+" + lk[6];
      return words;
    }

    function pendingAt(s, frames, k) {
      var ge = P[s].d.ge, inc = 0;
      for (var i = 0; i < ge.length && ge[i][0] <= frames; i++) inc += ge[i][1];
      // never clamped: replay_section._meter_check makes a negative value a build error, and a clamp
      // here would turn the one visible sign of a mis-join into a plausible empty meter
      return inc - P[s].x.outAt[k];
    }

    /* ---------- drawing ---------- */
    function cellRect(ctx, x, yUp, color, letter, garbage) {
      var px = BX + x * C, py = (VIS + TOP - 1 - yUp) * C;
      ctx.fillStyle = color;
      ctx.fillRect(px + 1, py + 1, C - 2, C - 2);
      if (garbage) {   // not colour alone: garbage carries a hatch
        ctx.strokeStyle = "rgba(0,0,0,.35)"; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(px + 3, py + C - 3); ctx.lineTo(px + C - 3, py + 3); ctx.stroke();
      }
      if (letters && letter) {
        ctx.fillStyle = "rgba(255,255,255,.92)";
        ctx.font = "600 " + Math.round(C * 0.62) + "px ui-monospace, monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(letter, px + C / 2, py + C / 2 + 1);
      }
    }
    function miniPiece(ctx, piece, ox, oy, size) {
      if (!piece) return;
      var shape = D.shapes[piece][0];
      var wMax = 0, hMax = 0;
      shape.forEach(function (d) { wMax = Math.max(wMax, d[0]); hMax = Math.max(hMax, d[1]); });
      var cx = ox + (4 - (wMax + 1)) * size / 2, cy = oy + (2 - (hMax + 1)) * size / 2;
      ctx.fillStyle = PIECE_COLOR[CODE[piece]];
      shape.forEach(function (d) {
        ctx.fillRect(cx + d[0] * size + 1, cy + (hMax - d[1]) * size + 1, size - 2, size - 2);
      });
      if (letters) {
        ctx.fillStyle = tok["--ink"]; ctx.font = "600 " + Math.round(size * 0.8) + "px ui-monospace, monospace";
        ctx.textAlign = "left"; ctx.textBaseline = "middle";
        ctx.fillText(piece, ox - size * 0.15, oy + size);
      }
    }

    function drawSide(s, now) {
      var sd = sides[s], cv = sd.cv, ctx = cv.getContext("2d");
      var dpr = window.devicePixelRatio || 1;
      if (cv.width !== Math.round(CW * dpr)) { cv.width = Math.round(CW * dpr); cv.height = Math.round(CH * dpr); }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, CW, CH);
      var pp = P[s], x = pp.x, k = countAt[s][pos];
      var accent = tok[s === 0 ? "--rp-c0" : "--rp-c1"];
      // field
      ctx.fillStyle = tok["--bg-sunken"];
      ctx.fillRect(BX, 0, W * C, CH);
      ctx.strokeStyle = tok["--grid-line"]; ctx.lineWidth = 1;
      for (var gx = 1; gx < W; gx++) {
        ctx.beginPath(); ctx.moveTo(BX + gx * C + 0.5, 0); ctx.lineTo(BX + gx * C + 0.5, CH); ctx.stroke();
      }
      ctx.fillStyle = "rgba(127,127,127,.12)";
      ctx.fillRect(BX, 0, W * C, TOP * C);         // the buffer row above the visible field
      // which board, with what effect
      var board = x.boards[k], f = fx[s], flashRows = null, flashA = 0, mover = null, outline = null;
      if (f && !reduced && f.k === k - 1) {
        var dropMs = f.drop ? 150 / speed() : 0, flashMs = 200 / speed(), el2 = now - f.t0;
        var full = x.cleared[f.k];
        if (el2 < dropMs) {
          board = x.pre[f.k].slice();
          x.cells[f.k].forEach(function (c) { board[c] = 0; });
          var minY = Math.min.apply(null, x.cells[f.k].map(function (c) { return Math.floor(c / W); }));
          var fall = Math.max(0, VIS - 1 - minY);
          mover = { cells: x.cells[f.k], piece: x.pieces[f.k], dy: Math.round(fall * (1 - el2 / dropMs)) };
        } else if (full.length && el2 < dropMs + flashMs) {
          board = x.pre[f.k]; flashRows = full; flashA = 1 - (el2 - dropMs) / flashMs;
        } else if (el2 < dropMs + flashMs + 250 && !full.length) {
          outline = x.cells[f.k];
        }
      }
      for (var y = 0; y < VIS + TOP; y++) {
        for (var cx = 0; cx < W; cx++) {
          var v = board[y * W + cx];
          if (!v) continue;
          cellRect(ctx, cx, y, v === 8 ? tok["--muted"] : PIECE_COLOR[v], LETTER[v] === "G" ? "" : LETTER[v], v === 8);
        }
        if (flashRows && flashRows.indexOf(y) >= 0) {
          ctx.globalAlpha = Math.max(0, flashA);
          ctx.fillStyle = "#ffffff";
          ctx.fillRect(BX, (VIS + TOP - 1 - y) * C, W * C, C);
          ctx.globalAlpha = 1;
        }
      }
      if (mover) {
        mover.cells.forEach(function (c) {
          var yy = Math.floor(c / W) + mover.dy;
          if (yy < VIS + TOP) cellRect(ctx, c % W, yy, PIECE_COLOR[CODE[mover.piece]], mover.piece, false);
        });
      }
      if (outline) {
        ctx.strokeStyle = accent; ctx.lineWidth = 2;
        outline.forEach(function (c) {
          var yy = Math.floor(c / W);
          if (yy < VIS + TOP) ctx.strokeRect(BX + (c % W) * C + 1, (VIS + TOP - 1 - yy) * C + 1, C - 2, C - 2);
        });
      }
      // boundary state on the board frame: solid = checked, dashed = past the checked prefix
      var v0 = pp.d.verified_to, past = k - 1 > v0 && k > 0;
      ctx.lineWidth = 2;
      ctx.strokeStyle = !past ? accent : (pp.d.after === "check_failed" ? tok["--rp-bad"] : tok["--pending"]);
      if (ctx.setLineDash) ctx.setLineDash(past ? [5, 4] : []);
      ctx.strokeRect(BX + 1, 1, W * C - 2, CH - 2);
      if (ctx.setLineDash) ctx.setLineDash([]);
      // meter
      var mx = (HOLD_W + GAP) * C, frames = Math.min(t, pp.d.frames);
      var pend = pendingAt(s, frames, k);
      ctx.fillStyle = tok["--border-strong"];
      ctx.fillRect(mx, TOP * C, METER_W * C, VIS * C);
      ctx.fillStyle = tok["--rp-bad"];
      var hgt = Math.min(pend, VIS) * C;
      ctx.fillRect(mx, CH - hgt, METER_W * C, hgt);
      // hold + next
      var q = x.queue[Math.min(k, x.queue.length - 1)];
      ctx.fillStyle = tok["--ink-secondary"];
      ctx.font = "600 " + Math.round(C * 0.62) + "px ui-monospace, monospace";
      ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
      ctx.fillText("HOLD", 2, C * 0.9);
      var nx = BX + W * C + GAP * C;
      ctx.fillText("NEXT", nx + 2, C * 0.9);
      var sz = C * 0.8;
      miniPiece(ctx, q.hold, 4 + sz * 0.3, C * 1.4, sz);
      var nexts = k < pp.d.locks.length ? [q.cur].concat(D.seq.slice(q.ptr, q.ptr + NEXT - 1).split("")) : [];
      nexts.forEach(function (pc, i) { miniPiece(ctx, pc, nx + sz * 0.3, C * 1.4 + i * sz * 2.4, sz); });
    }

    function speed() { return +speedSel.value || 1; }

    function updateText() {
      P.forEach(function (pp, s) {
        var sd = sides[s], k = countAt[s][pos], n = pp.d.locks.length, a = pp.x.atk[k];
        sd.strip.textContent = "第 " + k + "/" + n + " 粒 · 攻擊 " + a + " · 每粒攻擊 "
          + (k ? floor2(a / k) : "—") + " · 食垃圾 " + pp.x.ins[k] + " 行";
        var v = pp.d.verified_to, st, words;
        if (k === 0 || k - 1 <= v) { st = "verified"; words = k === 0 ? "未落第一粒" : "已核：第 " + k + " 粒之前嘅攻擊都對得上"; }
        else if (pp.d.after === "check_failed") { st = "check_failed"; words = "核對失敗：第 " + (pp.d.failed_at + 1) + " 粒嘅攻擊對唔上，第 " + (v + 2) + " 粒起盤面可能同真實唔同"; }
        else { st = "no_evidence"; words = "最後一次攻擊之後：冇證據話啱定唔啱（核到第 " + (v + 1) + " 粒）"; }
        sd.state.setAttribute("data-state", st);
        sd.state.textContent = words;
        var flagged = D.flags.some(function (fl) { return fl[1] === s && fl[0] <= pos; });
        sd.flag.hidden = !flagged;
        // the callout names this player's last placement only while it is recent (one second of
        // game time), so a stale "Double +1" does not sit beside a board that has moved on
        sd.callout.textContent = k > 0 && tAt[pos] - pp.x.absF[k - 1] <= 60 ? describe(s, k - 1) : "";
      });
      seek.value = String(pos);
      var vt = "第 " + pos + "/" + N + " 粒（兩邊合計）· " + fmtTime(t);
      seek.setAttribute("aria-valuetext", vt);
      posEl.textContent = vt;
      momentBtns.forEach(function (b, i) {
        if (D.moments[i][0] === pos) b.setAttribute("aria-current", "true"); else b.removeAttribute("aria-current");
      });
    }

    function boardLabel(s) {
      var pp = P[s], k = countAt[s][pos], b = pp.x.boards[k], top = 0, gar = 0;
      for (var y = 0; y < ROWS; y++) {
        var any = false, g = false;
        for (var x = 0; x < W; x++) { var v = b[y * W + x]; if (v) { any = true; if (v === 8) g = true; } }
        if (any) top = y + 1;
        if (g) gar++;
      }
      return pp.d.user + " 嘅模擬盤面，第 " + k + "/" + pp.d.locks.length + " 粒之後：最高去到第 " + top
        + " 行，有 " + gar + " 行有垃圾，等緊嘅垃圾 " + pendingAt(s, Math.min(t, pp.d.frames), k) + " 行。";
    }

    function draw() {
      var now = performance.now();
      drawSide(0, now); drawSide(1, now);
    }
    function notify() { if (opts.onChange) opts.onChange(pos, t, playing); }
    function still() {
      updateText(); draw();
      if (!playing) sides.forEach(function (sd, s) { sd.cv.setAttribute("aria-label", boardLabel(s)); });
      notify();
    }

    /* ---------- navigation ---------- */
    var HASH = opts.hashPrefix == null ? null : String(opts.hashPrefix);
    function writeHash() {
      if (!touched || HASH === null) return;
      var h = "#" + HASH + D.label + "@p" + pos;
      if (location.hash !== h && history.replaceState) history.replaceState(null, "", h);
    }
    function setPos(q, animate) {
      q = Math.max(0, Math.min(N, q));
      var prev = pos;
      pos = q; t = tAt[q];
      fx = [null, null];
      if (animate && q === prev + 1) {
        var s = +D.order[q - 1];
        fx[s] = { k: countAt[s][q] - 1, t0: performance.now(), drop: true };
        kick();
      }
      touched = true;
      still();
      if (!playing) writeHash();
    }
    function stepBy(d) {
      pause();
      setPos(pos + d, d === 1);
      if (d === 1 || d === -1) announceMoments(pos);
    }
    function jumpMoment(dir) {
      pause();
      var target = null;
      D.moments.forEach(function (m) {
        if (dir > 0 && m[0] > pos && (target === null || m[0] < target)) target = m[0];
        if (dir < 0 && m[0] < pos && (target === null || m[0] > target)) target = m[0];
      });
      if (target !== null) { setPos(target, false); announceMoments(target); }
    }
    function announce(text) { live.textContent = ""; setTimeout(function () { live.textContent = text; }, 30); }
    function announceMoments(q) {
      var here = D.moments.filter(function (m) { return m[0] === q; }).map(function (m) { return m[3]; });
      if (here.length) announce(here.join("；"));
    }

    /* ---------- playback on ONE shared frame clock ---------- */
    function kick() { if (!raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }
    function frame(now) {
      raf = 0;
      var dt = Math.min(100, now - last); last = now;
      var fxActive = fx.some(function (f) { return f && now - f.t0 < 700; });
      if (playing) {
        t += dt * 60 / 1000 * speed();
        var moved = [];
        while (pos < N && tAt[pos + 1] <= t) {
          pos++;
          var s = +D.order[pos - 1];
          fx[s] = { k: countAt[s][pos] - 1, t0: now, drop: false };
          moved.push(pos);
        }
        if (speed() <= 1) {
          var said = [];
          moved.forEach(function (q) {
            D.moments.forEach(function (m) { if (m[0] === q) said.push(m[3]); });
          });
          if (said.length) announce(said.join("；"));
        }
        if (t >= T_END) { t = T_END; pos = N; pause(true); return; }
        updateText(); draw(); notify();
        raf = requestAnimationFrame(frame);
      } else if (fxActive) {
        draw();
        raf = requestAnimationFrame(frame);
      } else {
        draw();
      }
    }
    function play() {
      if (playing) return;
      if (pos >= N) { pos = 0; t = 0; }
      playing = true; touched = true;
      playBtn.textContent = "暫停"; playBtn.setAttribute("aria-label", "暫停");
      kick();
    }
    function pause(ended) {
      if (!playing) return;
      playing = false;
      playBtn.textContent = "播放"; playBtn.setAttribute("aria-label", "播放");
      if (raf) { cancelAnimationFrame(raf); raf = 0; }
      still();
      writeHash();
      var parts = P.map(function (pp, s) {
        return pp.d.user + " 第 " + countAt[s][pos] + "/" + pp.d.locks.length + " 粒";
      });
      announce((ended ? "播完：" : "暫停：") + "第 " + pos + "/" + N + " 粒，" + fmtTime(t) + "。" + parts.join("，") + "。");
    }

    playBtn.addEventListener("click", function () { if (playing) pause(); else play(); });
    $('[data-act="back"]').addEventListener("click", function () { stepBy(-1); });
    $('[data-act="fwd"]').addEventListener("click", function () { stepBy(1); });
    $('[data-act="start"]').addEventListener("click", function () { pause(); setPos(0, false); });
    $('[data-act="end"]').addEventListener("click", function () { pause(); setPos(N, false); announceMoments(N); });
    seek.addEventListener("input", function () { pause(); setPos(+seek.value, false); });
    speedSel.addEventListener("change", function () { if (!playing) still(); });
    lettersBtn.addEventListener("click", function () {
      letters = !letters; lettersBtn.setAttribute("aria-pressed", String(letters)); draw();
    });
    function toggleHelp(force) {
      var open = force == null ? help.hidden : force;
      help.hidden = !open; helpBtn.setAttribute("aria-expanded", String(open));
    }
    helpBtn.addEventListener("click", function () { toggleHelp(); });

    var SPEEDS = ["0.5", "1", "2", "4"];
    function shiftSpeed(d) {
      var i = SPEEDS.indexOf(speedSel.value) + d;
      if (i < 0 || i >= SPEEDS.length) return;
      speedSel.value = SPEEDS[i];
      announce("速度 " + SPEEDS[i] + "×");
      if (!playing) still();
    }

    // keys act only while focus is inside the player (WCAG 2.1.4)
    box.addEventListener("keydown", function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      var tag = e.target.tagName, k = e.key;
      if (tag === "INPUT" && /^(ArrowLeft|ArrowRight|ArrowUp|ArrowDown|Home|End|PageUp|PageDown)$/.test(k)) return;
      if (tag === "SELECT" && k !== "?") return;
      if ((tag === "BUTTON") && (k === " " || k === "Enter")) return;
      var done = true;
      switch (k) {
        case " ": case "k": case "K": if (playing) pause(); else play(); break;
        case "ArrowLeft": stepBy(-1); break;
        case "ArrowRight": stepBy(1); break;
        case "ArrowUp": jumpMoment(-1); break;
        case "ArrowDown": jumpMoment(1); break;
        case "j": case "J": pause(); setPos(pos - 5, false); break;
        case "l": case "L": pause(); setPos(pos + 5, false); break;
        case "Home": pause(); setPos(0, false); break;
        case "End": pause(); setPos(N, false); break;
        case "<": case ",": shiftSpeed(-1); break;
        case ">": case ".": shiftSpeed(1); break;
        case "?": toggleHelp(); break;
        case "Escape": if (!help.hidden) toggleHelp(false); else done = false; break;
        default: done = false;
      }
      if (done) e.preventDefault();
    });

    // theme and motion are re-read when they change; destroy() drops all three listeners
    function retheme() { readTokens(); draw(); }
    function remotion() { reduced = motionQ.matches; draw(); }
    var schemeQ = window.matchMedia ? matchMedia("(prefers-color-scheme: dark)") : null;
    if (schemeQ) schemeQ.addEventListener("change", retheme);
    var themeObs = window.MutationObserver ? new MutationObserver(retheme) : null;
    if (themeObs) themeObs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "class"] });
    if (motionQ && motionQ.addEventListener) motionQ.addEventListener("change", remotion);

    if (typeof opts.pos === "number") {
      pos = Math.max(0, Math.min(N, Math.floor(opts.pos))); t = tAt[pos];
      touched = true;
    }
    // deep link: #<prefix>m<pos>r<round>@p<n> (a different round's link is ignored, not misapplied)
    if (HASH !== null) (function readHash() {
      var m = /^#([a-z-]*)(m\d+r\d+)(?:@p(\d+))?$/.exec(location.hash);
      if (m && m[1] === HASH && m[2] === D.label) {
        pos = Math.min(N, +(m[3] || 0)); t = tAt[pos];
        touched = true;
        setTimeout(function () { root.scrollIntoView(); }, 0);
      }
    })();
    still();

    return {
      label: D.label,
      length: N,
      frameAt: function (q) { return tAt[Math.max(0, Math.min(N, q))]; },
      /* the last merged position reached at or before `frames` on the shared clock */
      posAtFrame: function (frames) {
        var lo = 0, hi = N;
        while (lo < hi) { var mid = (lo + hi + 1) >> 1; if (tAt[mid] <= frames) lo = mid; else hi = mid - 1; }
        return lo;
      },
      endFrame: T_END,
      seek: function (q) { pause(); setPos(q, false); announceMoments(pos); },
      destroy: function () {
        pause();
        if (raf) { cancelAnimationFrame(raf); raf = 0; }
        if (schemeQ) schemeQ.removeEventListener("change", retheme);
        if (themeObs) themeObs.disconnect();
        if (motionQ && motionQ.removeEventListener) motionQ.removeEventListener("change", remotion);
      }
    };
  };
})();
