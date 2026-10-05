/* 逐局重播 page controller — pipeline/replay_page.py inlines this AFTER replay_player.js.

   Page-only: the round picker, the hash, and the attack chart. The boards, seek bar, keys and key
   moments are the shared player (rpReplay.mount), mounted afresh on a clone of the
   #rpg-player-tpl box whenever the round changes, and destroy()ed before the next one, so no
   listener outlives its round.

   - the hash is #m<pos>r<round>@p<n>; picking a round is a plain link to #m<pos>r<round>, and
     moving inside a round rewrites the hash with replaceState (no history flood);
   - the chart plots the RECORDED garbage events (射埋, before cancellation), never the simulator;
     clicking it seeks to the last placement at or before that moment on the shared clock;
   - nodes are built with createElement / textContent only. */
(function () {
  "use strict";
  var island = document.getElementById("rpg-data");
  var root = document.getElementById("round-replay");
  var tpl = document.getElementById("rpg-player-tpl");
  if (!island || !root || !tpl || !window.rpReplay) return;
  var DATA = JSON.parse(island.textContent);
  var byLabel = {};
  DATA.rounds.forEach(function (r) {
    var full = {};
    Object.keys(DATA.shared).forEach(function (k) { full[k] = DATA.shared[k]; });
    Object.keys(r).forEach(function (k) { full[k] = r[k]; });
    byLabel[r.label] = full;
  });

  var host = root.querySelector(".rpg-host");
  var nowEl = document.getElementById("rpg-now");
  var notesEl = root.querySelector(".rpg-notes");
  var flagEl = root.querySelector(".rpg-flag");
  var missingEl = root.querySelector(".rpg-missing");
  var cv = root.querySelector(".rpg-canvas");
  var legend = root.querySelector(".rpg-legend");
  var matchBtns = Array.prototype.slice.call(document.querySelectorAll(".rpg-match"));
  var roundLinks = Array.prototype.slice.call(document.querySelectorAll(".rpg-round"));

  var cur = null, handle = null, quiet = false, playhead = 0;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
  function fmtTime(frames) {           // floored, like fmt: m:ss
    var s = Math.floor(frames / 60);
    var ss = s % 60;
    return Math.floor(s / 60) + ":" + (ss < 10 ? "0" : "") + ss;
  }

  /* ---------- picker ---------- */
  function openMatch(m) {
    matchBtns.forEach(function (b) {
      var on = b.getAttribute("data-m") === String(m);
      b.setAttribute("aria-expanded", String(on));
      // bring the open match's chip into the horizontally scrolled row, without moving the page
      var row = b.parentNode;
      if (on && (b.offsetLeft < row.scrollLeft || b.offsetLeft + b.offsetWidth > row.scrollLeft + row.clientWidth)) {
        row.scrollLeft = b.offsetLeft - row.offsetLeft - 8;
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll(".rpg-rounds"), function (ol) {
      ol.hidden = ol.getAttribute("data-m") !== String(m);
    });
  }
  matchBtns.forEach(function (b) {
    b.addEventListener("click", function () { openMatch(b.getAttribute("data-m")); });
  });

  /* ---------- chart: cumulative 射埋 per sender, from the recorded events ---------- */
  var tok = {};
  function readTokens() {
    var cs = getComputedStyle(root);
    ["--rp-c0", "--rp-c1", "--muted", "--border", "--ink", "--ink-secondary"].forEach(function (n) {
      var v = cs.getPropertyValue(n).trim();
      if (!v) throw new Error("replay page: CSS token " + n + " is not defined");
      tok[n] = v;
    });
  }
  // series[s] = what player s SENT, i.e. the events recorded on the other player (the receiver)
  function series(D) {
    return [0, 1].map(function (s) {
      var recv = D.players[1 - s], pts = [], tot = 0;
      recv.ge.forEach(function (e) { tot += e[1]; pts.push([e[0], tot]); });
      return { from: D.players[s].user, to: recv.user, pts: pts, total: tot, n: recv.ge.length };
    });
  }
  var PAD_L = 34, PAD_R = 10, PAD_T = 10, PAD_B = 20;
  function geom() {
    var r = cv.getBoundingClientRect();
    return { w: r.width, h: r.height };
  }
  function drawChart() {
    if (!cur || !handle) return;
    var g = geom(), dpr = window.devicePixelRatio || 1;
    if (!g.w) return;
    cv.width = Math.round(g.w * dpr); cv.height = Math.round(g.h * dpr);
    var ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, g.w, g.h);
    var S = series(cur), T = Math.max(1, handle.endFrame);
    var top = Math.max(1, S[0].total, S[1].total);
    var pw = g.w - PAD_L - PAD_R, ph = g.h - PAD_T - PAD_B;
    function X(f) { return PAD_L + pw * Math.min(f, T) / T; }
    function Y(v) { return PAD_T + ph * (1 - v / top); }
    // axes: y at 0 and the max, x every 30 s
    ctx.strokeStyle = tok["--border"]; ctx.lineWidth = 1;
    ctx.fillStyle = tok["--ink-secondary"];
    ctx.font = "11px ui-monospace, monospace";
    ctx.textBaseline = "middle"; ctx.textAlign = "right";
    [0, top].forEach(function (v) {
      ctx.beginPath(); ctx.moveTo(PAD_L, Y(v) + 0.5); ctx.lineTo(PAD_L + pw, Y(v) + 0.5); ctx.stroke();
      ctx.fillText(String(v), PAD_L - 6, Y(v));
    });
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    for (var f = 0; f <= T; f += 1800) ctx.fillText(fmtTime(f), X(f), PAD_T + ph + 5);
    // the two step lines
    S.forEach(function (sr, s) {
      ctx.strokeStyle = tok[s === 0 ? "--rp-c0" : "--rp-c1"];
      ctx.lineWidth = 2;
      if (ctx.setLineDash) ctx.setLineDash(s === 0 ? [] : [6, 3]);   // not colour alone
      ctx.beginPath();
      ctx.moveTo(X(0), Y(0));
      var v = 0;
      sr.pts.forEach(function (p) { ctx.lineTo(X(p[0]), Y(v)); v = p[1]; ctx.lineTo(X(p[0]), Y(v)); });
      ctx.lineTo(X(T), Y(v));
      ctx.stroke();
      if (ctx.setLineDash) ctx.setLineDash([]);
    });
    // the playhead, on the replay's shared clock
    ctx.strokeStyle = tok["--ink"]; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(X(playhead) + 0.5, PAD_T - 4); ctx.lineTo(X(playhead) + 0.5, PAD_T + ph); ctx.stroke();
  }
  function chartLabel() {
    var S = series(cur);
    cv.setAttribute("aria-label", "射埋累積圖（replay 記錄，抵銷之前）：" + S.map(function (sr) {
      return sr.from + " 射埋 " + sr.to + " 合共 " + sr.total + " 行（" + sr.n + " 次）";
    }).join("；") + "。撳圖可以跳去嗰個時間。");
    clear(legend);
    S.forEach(function (sr, s) {
      var span = el("span");
      var key = el("i"); key.setAttribute("data-slot", String(s));
      span.appendChild(key);
      span.appendChild(document.createTextNode(
        sr.from + " 射埋 " + sr.to + "：" + sr.total + " 行（" + sr.n + " 次）" + (s === 0 ? "，實線" : "，虛線")));
      legend.appendChild(span);
    });
  }
  cv.addEventListener("click", function (e) {
    if (!handle) return;
    var r = cv.getBoundingClientRect(), pw = r.width - PAD_L - PAD_R;
    var frac = Math.max(0, Math.min(1, (e.clientX - r.left - PAD_L) / pw));
    handle.seek(handle.posAtFrame(frac * handle.endFrame));
  });

  /* ---------- the hash ---------- */
  function parseHash() {
    var m = /^#(m\d+r\d+)(?:@p(\d+))?$/.exec(location.hash);
    return m ? { label: m[1], pos: m[2] == null ? 0 : +m[2] } : null;
  }
  function writeHash(pos) {
    if (quiet || !cur || !history.replaceState) return;
    var h = "#" + cur.label + "@p" + pos;
    if (location.hash !== h) history.replaceState(null, "", h);
  }

  /* ---------- switching rounds ---------- */
  function show(label, pos, missing) {
    var D = byLabel[label];
    /* quiet BEFORE destroy: destroy() pauses, and that pause's notify() reports playing false
       with the OLD cur and position — unguarded it would overwrite the hash the link just set. */
    quiet = true;
    if (handle) { handle.destroy(); handle = null; }
    clear(host);
    cur = D;
    var box = tpl.content.firstElementChild.cloneNode(true);
    box.setAttribute("aria-label", D.label + " 模擬重播；撳 ? 睇快捷鍵");
    host.appendChild(box);
    nowEl.textContent = "第 " + D.match + " 場第 " + D.round + " 局（" + D.label + "）· "
      + D.file + " · " + D.winner + " 贏" + (label === DATA["default"] ? " · ★ 最癲一局" : "");
    clear(notesEl);
    D.notes.forEach(function (n, i) {
      if (i) notesEl.appendChild(el("br"));
      notesEl.appendChild(document.createTextNode(n));
    });
    flagEl.hidden = !D.flags.length;
    missingEl.hidden = !missing;
    openMatch(D.match);
    roundLinks.forEach(function (a) {
      if (a.getAttribute("data-label") === label) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    });
    handle = rpReplay.mount(root, box, D, {
      hashPrefix: null,
      pos: pos,
      onChange: function (p, frames, playing) {
        playhead = frames; drawChart();
        /* never while playing: notify() fires every animation frame, and WebKit throws once a
           page passes ~100 history calls in a short window, which would kill the rAF loop.
           pause() -> still() -> notify() reports the final position with playing false. */
        if (!playing) writeHash(p);
      }
    });
    quiet = false;
    chartLabel();
    drawChart();
    return box;
  }

  function fromHash(focus) {
    var h = parseHash();
    if (h && byLabel[h.label]) {
      var box = show(h.label, h.pos, false);
      if (focus) box.focus({ preventScroll: true });
      return;
    }
    show(DATA["default"], 0, !!(h || location.hash.length > 1));
  }
  window.addEventListener("hashchange", function () { fromHash(true); });
  roundLinks.forEach(function (a) {
    // a click on the round already showing would not fire hashchange; reset it explicitly
    a.addEventListener("click", function (e) {
      if (location.hash === a.getAttribute("href")) { e.preventDefault(); fromHash(true); }
    });
  });

  readTokens();
  function retheme() { readTokens(); drawChart(); }
  if (window.matchMedia) matchMedia("(prefers-color-scheme: dark)").addEventListener("change", retheme);
  if (window.MutationObserver) new MutationObserver(retheme).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "class"] });
  window.addEventListener("resize", drawChart);
  fromHash(false);
})();
