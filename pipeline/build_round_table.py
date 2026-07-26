"""Build the per-round data table and inject it into a report.

    python3 -m pipeline.build_round_table sessions/2026-07-24/report

One table per match, two rows per round (one per player), every stat in its own
column with a header. The winner's row is tinted and marked, numerals are
tabular-aligned, the 局 / 時間 / 玩家 columns stay pinned while the stat columns scroll,
and the whole table scrolls inside its own container so the page never scrolls sideways.

Columns beyond the in-game end screen's APM / PPS / VS: pieces, APP (attack per piece),
KPP (keys per piece), DS (downstack per piece), lines, spike, B2B, combo, T-spins,
quads, TSD, TST, perfect clears, finesse rate and faults, attack, garbage sent, queued
vs materialised garbage, garbage cleared, score, and how the round ended.

Everything is derived from facts.json, so the table cannot disagree with the data the
claims are proved against. The section sits between comment markers and is replaced in
place on re-runs, so this is idempotent.
"""
import argparse
import json
import os
import re

from pipeline import claim_cards
from pipeline.fmt import fmt_clock, r1, r2

START = "<!-- BEGIN generated round-table (pipeline/build_round_table.py) -->"
END = "<!-- END generated round-table -->"

CSS = """
<style>
/* ---------- per-round data table (generated) ---------- */
/* The host report defines --accent only on .match-card[data-winner], so it resolves
   to an empty string here and any color-mix() using it silently paints nothing.
   This section carries its own token instead. */
#rounds { --rt-accent: var(--yachi); }
.rt-match { margin: 0 0 2.2rem; }
.rt-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: .5rem .9rem;
  margin-bottom: .5rem; }
.rt-head .rt-no { font-family: var(--font-mono); font-size: .74rem; letter-spacing: .12em;
  text-transform: uppercase; color: var(--muted); }
.rt-head .rt-score { font-weight: 800; font-size: 1.02rem; font-variant-numeric: tabular-nums; }
.rt-head .rt-who { font-family: var(--font-mono); font-size: .74rem; color: var(--muted); }
.rt-head .rt-agg { font-family: var(--font-mono); font-size: .7rem; color: var(--muted);
  margin-left: auto; font-variant-numeric: tabular-nums; }
.rt-y { color: var(--yachi); } .rt-p { color: var(--pinglamb); }

.rt-scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px;
  background: var(--bg-raised); -webkit-overflow-scrolling: touch; }
table.rt-tbl { border-collapse: separate; border-spacing: 0; width: max-content;
  min-width: 100%; font-variant-numeric: tabular-nums; font-size: .74rem; }
table.rt-tbl th, table.rt-tbl td { padding: .42rem .6rem; text-align: right;
  white-space: nowrap; border-bottom: 1px solid var(--border); }
table.rt-tbl thead th { position: sticky; top: 0; z-index: 3; cursor: pointer;
  user-select: none;
  background: var(--bg-sunken); font-family: var(--font-mono); font-size: .66rem;
  font-weight: 700; letter-spacing: .04em; color: var(--ink-secondary);
  text-transform: uppercase; border-bottom: 1px solid var(--border-strong); }
table.rt-tbl tbody tr:last-child td { border-bottom: none; }
/* Pinned identity columns.
   These MUST be fully opaque: the player tints are translucent, and a translucent
   sticky cell lets the scrolling columns show through underneath it, so the pinned
   name ends up with stat values printed on top of it. Painting the tint as a
   background-image over an opaque background-color composites to something solid. */
.rt-tbl .c-rd, .rt-tbl .c-time, .rt-tbl .c-who { position: sticky; z-index: 2;
  background-color: var(--bg-raised); text-align: left; }
.rt-tbl .c-rd { left: 0; width: 2.4rem; font-family: var(--font-mono); color: var(--muted); }
.rt-tbl .c-time { left: 2.4rem; width: 3.2rem; font-family: var(--font-mono); font-weight: 700; }
.rt-tbl .c-who { left: 5.6rem; width: 5.6rem; font-weight: 700;
  border-right: 1px solid var(--border); }
.rt-tbl thead .c-rd, .rt-tbl thead .c-time, .rt-tbl thead .c-who {
  z-index: 4; background-color: var(--bg-sunken); background-image: none; }
/* a hairline so the pinned block reads as a separate group while scrolling */
.rt-tbl .c-who { box-shadow: 1px 0 0 var(--border); }
/* a round is two rows; separate rounds with a stronger rule */
.rt-tbl tr.rt-round-end td { border-bottom: 1px solid var(--border-strong); }
.rt-tbl tr.rt-w-y td { background: var(--yachi-tint); }
.rt-tbl tr.rt-w-y .c-rd, .rt-tbl tr.rt-w-y .c-time, .rt-tbl tr.rt-w-y .c-who {
  background-color: var(--bg-raised);
  background-image: linear-gradient(var(--yachi-tint-strong), var(--yachi-tint-strong)); }
.rt-tbl tr.rt-w-p td { background: var(--pinglamb-tint); }
.rt-tbl tr.rt-w-p .c-rd, .rt-tbl tr.rt-w-p .c-time, .rt-tbl tr.rt-w-p .c-who {
  background-color: var(--bg-raised);
  background-image: linear-gradient(var(--pinglamb-tint-strong), var(--pinglamb-tint-strong)); }
.rt-tbl tr.rt-loser td { color: var(--ink-secondary); }
/* Hover layer. A 28-column lookup table is unreadable without one: the eye loses
   the row between the pinned name and the column it is reading. */
.rt-tbl tbody tr:hover td { background-image:
  linear-gradient(var(--bg-sunken), var(--bg-sunken)); }
.rt-tbl tbody tr:hover .c-rd, .rt-tbl tbody tr:hover .c-time,
.rt-tbl tbody tr:hover .c-who { background-image:
  linear-gradient(var(--bg-sunken), var(--bg-sunken)); }
/* Identity is a coloured dot plus ink-coloured text, not coloured text: a name
   painted in the series colour is colour-as-information and reads worse. */
.rt-dot { display: inline-block; width: .5rem; height: .5rem; border-radius: 50%;
  margin-right: .35rem; vertical-align: baseline; }
.rt-dot.is-y { background: var(--yachi); }
.rt-dot.is-p { background: var(--pinglamb); }
.rt-tbl .c-who { color: var(--ink); }
/* sort affordance */
.rt-tbl thead th .rt-arrow { opacity: .25; margin-left: .25rem; font-size: .85em; }
.rt-tbl thead th[aria-sort="ascending"] .rt-arrow,
.rt-tbl thead th[aria-sort="descending"] .rt-arrow { opacity: 1; color: var(--rt-accent); }
.rt-tbl thead th:hover { color: var(--ink); }
.rt-oddgroup td { border-bottom-color: var(--border); }
/* low-signal columns: present, hidden by default (see OPTIONAL_COLS) */
.rt-tbl .rt-opt { display: none; }
#rounds.rt-show-all .rt-tbl .rt-opt { display: table-cell; }
.rt-toggle { display: inline-flex; align-items: center; gap: .4rem; cursor: pointer;
  font-size: .74rem; font-family: var(--font-mono); color: var(--muted);
  border: 1px solid var(--border); border-radius: 999px; padding: .25rem .7rem;
  background: var(--bg-raised); margin: 0 0 1rem; }
.rt-toggle:hover { color: var(--ink); border-color: var(--border-strong); }
.rt-toggle input { accent-color: var(--rt-accent); margin: 0; }
/* Magnitude bar. Drawn as a pseudo-element rather than a background layer, because
   the row tint and the hover layer already occupy background-color/background-image. */
.rt-tbl td.rt-bar { position: relative; }
.rt-tbl td.rt-bar::before { content: ""; position: absolute; left: 0; top: 3px; bottom: 3px;
  width: calc(var(--b, 0) * 100%); border-radius: 0 2px 2px 0; pointer-events: none;
  background: color-mix(in srgb, var(--muted) 30%, transparent); }
/* Bar length is magnitude, bar hue is identity — two channels, two meanings, the way
   the game's own end screen does it. */
.rt-tbl tr[data-who="yachi"] td.rt-bar::before {
  background: color-mix(in srgb, var(--yachi) 30%, transparent); }
.rt-tbl tr[data-who="pinglamb"] td.rt-bar::before {
  background: color-mix(in srgb, var(--pinglamb) 30%, transparent); }
.rt-tbl td.rt-bar > span { position: relative; }
#rounds.rt-nobars .rt-tbl td.rt-bar::before { display: none; }
/* row filters */
#rounds.f-win .rt-tbl tbody tr.rt-loser { display: none; }
#rounds.f-yachi .rt-tbl tbody tr:not([data-who="yachi"]) { display: none; }
#rounds.f-pinglamb .rt-tbl tbody tr:not([data-who="pinglamb"]) { display: none; }
.rt-controls { display: flex; flex-wrap: wrap; gap: .45rem; align-items: center;
  margin: 0 0 1rem; }
.rt-chip { font-family: var(--font-mono); font-size: .72rem; cursor: pointer;
  border: 1px solid var(--border); border-radius: 999px; padding: .26rem .7rem;
  background: var(--bg-raised); color: var(--muted); }
.rt-chip:hover { color: var(--ink); border-color: var(--border-strong); }
.rt-chip[aria-pressed="true"] { color: var(--rt-accent); border-color: var(--rt-accent);
  background: color-mix(in srgb, var(--rt-accent) 12%, transparent); }
.rt-tbl td.rt-key { font-weight: 700; color: var(--ink); }
.rt-tbl td.c-end { text-align: left; font-family: var(--font-mono); font-size: .68rem;
  color: var(--muted); }
.rt-tbl .rt-win-mark { color: var(--good); font-weight: 700; }
.rt-tbl td.rt-zero { color: var(--muted); opacity: .55; }
.rt-legend { font-size: .8rem; color: var(--muted); margin: 0 0 1.3rem; line-height: 1.75; }
.rt-legend code { font-family: var(--font-mono); font-size: .95em; color: var(--ink-secondary); }
.rt-hint { font-family: var(--font-mono); font-size: .66rem; color: var(--muted);
  margin: .3rem 0 0; }
/* header strip: row count is the first thing a data reader looks for */
.rt-meta { font-family: var(--font-mono); font-size: .72rem; color: var(--muted);
  margin: 0 0 .5rem; }
.rt-meta b { color: var(--ink); }
/* summary panel — recomputed from the VISIBLE rows on every filter change */
.rt-summary { display: grid; gap: .5rem; margin: 0 0 1rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 128px), 1fr)); }
.rt-stat { border: 1px solid var(--border); border-radius: 8px; padding: .5rem .65rem;
  background: var(--bg-raised); }
.rt-stat dt { font-family: var(--font-mono); font-size: .62rem; letter-spacing: .06em;
  text-transform: uppercase; color: var(--muted); margin: 0; }
.rt-stat dd { margin: .15rem 0 0; font-weight: 700; font-size: 1rem;
  font-variant-numeric: tabular-nums; }
.rt-stat dd small { font-weight: 500; font-size: .68rem; color: var(--muted); }
/* detail drawer */
.rt-tbl tbody tr { cursor: pointer; }
.rt-drawer { position: fixed; inset: auto 0 0 0; max-height: 76vh; overflow-y: auto;
  background: var(--bg-raised); border-top: 2px solid var(--rt-accent);
  box-shadow: 0 -8px 32px rgba(0,0,0,.18); padding: 1rem 1.2rem 1.6rem;
  z-index: 50; display: none; }
.rt-drawer.is-open { display: block; }
.rt-drawer-head { display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap;
  margin-bottom: .7rem; }
.rt-drawer-head h4 { margin: 0; font-size: 1rem; }
.rt-close { margin-left: auto; border: 1px solid var(--border); background: none;
  border-radius: 999px; padding: .2rem .7rem; cursor: pointer; font-size: .74rem;
  color: var(--muted); font-family: var(--font-mono); }
.rt-close:hover { color: var(--ink); border-color: var(--border-strong); }
.rt-fields { display: grid; gap: .3rem .9rem; margin: 0 0 .9rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr)); }
.rt-fields div { display: flex; justify-content: space-between; gap: .5rem;
  font-size: .76rem; border-bottom: 1px dotted var(--border); padding: .15rem 0; }
.rt-fields dt, .rt-fields .k { color: var(--muted); font-family: var(--font-mono);
  font-size: .68rem; }
.rt-fields .v { font-variant-numeric: tabular-nums; font-weight: 600; }
.rt-timeline { margin-top: .4rem; }
.rt-timeline h5 { margin: 0 0 .35rem; font-size: .78rem; }
.rt-spark { display: block; width: 100%; height: 56px; }
.rt-status { font-family: var(--font-mono); font-size: .68rem; color: var(--muted);
  min-height: 1.1em; }
/* print: keep the bars and tints meaningful on paper */
@media print {
  .rt-controls, .rt-hint, .rt-drawer { display: none !important; }
  .rt-scroll { overflow: visible; border: none; }
  table.rt-tbl { font-size: .6rem; }
  .rt-tbl td, .rt-tbl th { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
/* per-piece efficiency findings */
.rt-find { display: grid; gap: .6rem; margin: 0 0 2rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); }
.rt-card { border: 1px solid var(--border); border-left-width: 3px; border-radius: 8px;
  padding: .7rem .85rem; background: var(--bg-raised); }
.rt-card.is-lever { border-left-color: var(--good); }
.rt-card.is-flat { border-left-color: var(--muted); }
.rt-card.is-compare { border-left-color: var(--rt-accent); }
.rt-card.is-compare .rt-verdict { color: var(--rt-accent); }
.rt-card .rt-metric { font-family: var(--font-mono); font-size: .68rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--muted); display: flex; gap: .4rem; align-items: center; }
.rt-card .rt-verdict { font-family: var(--font-mono); font-size: .62rem; padding: .05rem .35rem;
  border-radius: 999px; border: 1px solid currentColor; }
.rt-card.is-lever .rt-verdict { color: var(--good); }
.rt-card.is-flat .rt-verdict { color: var(--muted); }
.rt-card p { margin: .35rem 0 0; font-size: .82rem; line-height: 1.65; }
.rt-card .rt-cid { font-family: var(--font-mono); font-size: .6rem; color: var(--muted); }
</style>
"""

EXPLORE_JS = r"""
<script>
/* Live count, summary, detail drawer, CSV/summary export, URL-hash state.
   DOM is built with createElement/textContent only — never innerHTML from a value. */
(function () {
  var sect = document.getElementById("rounds");
  if (!sect) return;
  var island = document.getElementById("rt-rounds");
  var DATA = island ? JSON.parse(island.textContent) : [];
  var byKey = {};
  DATA.forEach(function (d) { byKey[d.m + "-" + d.r + "-" + d.who] = d; });

  var countEl = document.getElementById("rt-count");
  var sumEl = document.getElementById("rt-summary");
  var statusEl = document.getElementById("rt-status");

  function visibleRows() {
    return Array.prototype.slice.call(sect.querySelectorAll(".rt-tbl tbody tr"))
      .filter(function (tr) { return tr.offsetParent !== null; });
  }

  function num(tr, name) {
    var idx = HEAD_INDEX[name];
    if (idx === undefined) return NaN;
    return parseFloat(tr.cells[idx].dataset.v);
  }

  /* Column name -> cell index. Read from ONE header row: every table shares the
     same column order, and querying across all of them let the LAST table's
     indices win, putting every lookup past the end of a row. */
  var HEAD_INDEX = {};
  (function () {
    var firstHead = sect.querySelector(".rt-tbl thead tr");
    if (!firstHead) return;
    Array.prototype.forEach.call(firstHead.cells, function (th, i) {
      HEAD_INDEX[th.textContent.replace(/[\u2195]/g, "").trim()] = i;
    });
  })();

  function stat(dl, label, value, sub) {
    var wrap = document.createElement("div");
    wrap.className = "rt-stat";
    var dt = document.createElement("dt");
    dt.textContent = label;
    var dd = document.createElement("dd");
    dd.textContent = value;
    if (sub) {
      var small = document.createElement("small");
      small.textContent = " " + sub;
      dd.appendChild(small);
    }
    wrap.appendChild(dt); wrap.appendChild(dd);
    dl.appendChild(wrap);
  }

  function mean(rows, name) {
    var vals = rows.map(function (r) { return num(r, name); })
                   .filter(function (v) { return !isNaN(v); });
    if (!vals.length) return null;
    return vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
  }

  function refresh() {
    var rows = visibleRows();
    var total = sect.querySelectorAll(".rt-tbl tbody tr").length;
    if (countEl) {
      countEl.textContent = " 　現正顯示 " + rows.length + " / " + total + " 行。";
    }
    if (!sumEl) return;
    while (sumEl.firstChild) sumEl.removeChild(sumEl.firstChild);
    var wins = rows.filter(function (r) { return !r.classList.contains("rt-loser"); }).length;
    stat(sumEl, "行數", rows.length, "/ " + total);
    stat(sumEl, "贏 / 輸", wins + " / " + (rows.length - wins));
    var m;
    if ((m = mean(rows, "APM")) !== null) stat(sumEl, "平均 APM", m.toFixed(1));
    if ((m = mean(rows, "PPS")) !== null) stat(sumEl, "平均 PPS", m.toFixed(2));
    if ((m = mean(rows, "VS")) !== null) stat(sumEl, "平均 VS", m.toFixed(1));
    if ((m = mean(rows, "APP")) !== null) stat(sumEl, "平均 APP", m.toFixed(2));
    if ((m = mean(rows, "方塊")) !== null) stat(sumEl, "平均方塊", Math.round(m));
    writeHash();
  }

  /* ---------------- filters, clear-all, bars, columns ---------------- */
  function setFilter(name) {
    sect.classList.remove("f-win", "f-yachi", "f-pinglamb");
    if (name) sect.classList.add(name);
    Array.prototype.forEach.call(sect.querySelectorAll(".rt-chip[data-filter]"), function (c) {
      c.setAttribute("aria-pressed", (c.dataset.filter || "") === (name || "") ? "true" : "false");
    });
    refresh();
  }
  Array.prototype.forEach.call(sect.querySelectorAll(".rt-chip[data-filter]"), function (chip) {
    chip.addEventListener("click", function () { setFilter(chip.dataset.filter); });
  });
  var clearBtn = document.getElementById("rt-clear");
  if (clearBtn) clearBtn.addEventListener("click", function () { setFilter(""); });

  /* ---------------- detail drawer ---------------- */
  var drawer = document.getElementById("rt-drawer");
  var dTitle = document.getElementById("rt-drawer-title");
  var dSub = document.getElementById("rt-drawer-sub");
  var dFields = document.getElementById("rt-drawer-fields");
  var dClears = document.getElementById("rt-drawer-clears");
  var dTime = document.getElementById("rt-drawer-timeline");
  var FIELD_LABELS = __FIELD_LABELS__;
  var CLEAR_LABELS = __CLEAR_LABELS__;

  function kv(host, key, val) {
    var row = document.createElement("div");
    var k = document.createElement("span"); k.className = "k"; k.textContent = key;
    var v = document.createElement("span"); v.className = "v"; v.textContent = val;
    row.appendChild(k); row.appendChild(v); host.appendChild(row);
  }

  function clock(ms) {
    var t = Math.floor(ms / 1000);
    return Math.floor(t / 60) + ":" + String(t % 60).padStart(2, "0");
  }

  function sparkline(events, dur) {
    var W = 640, H = 56, pad = 4;
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("class", "rt-spark");
    svg.setAttribute("role", "img");
    var maxAmt = events.reduce(function (a, e) { return Math.max(a, e[1]); }, 1);
    var lastFrame = events.reduce(function (a, e) { return Math.max(a, e[0]); }, 1);
    var axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
    axis.setAttribute("x1", 0); axis.setAttribute("x2", W);
    axis.setAttribute("y1", H - pad); axis.setAttribute("y2", H - pad);
    axis.setAttribute("stroke", "currentColor");
    axis.setAttribute("stroke-opacity", ".25");
    svg.appendChild(axis);
    events.forEach(function (e) {
      var x = pad + (e[0] / lastFrame) * (W - pad * 2);
      var h = (e[1] / maxAmt) * (H - pad * 3);
      var bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      bar.setAttribute("x", x.toFixed(1)); bar.setAttribute("width", 3);
      bar.setAttribute("y", (H - pad - h).toFixed(1)); bar.setAttribute("height", h.toFixed(1));
      bar.setAttribute("fill", "currentColor"); bar.setAttribute("fill-opacity", ".55");
      var t = document.createElementNS("http://www.w3.org/2000/svg", "title");
      t.textContent = e[1] + " 行 @ frame " + e[0];
      bar.appendChild(t);
      svg.appendChild(bar);
    });
    return svg;
  }

  function openDrawer(tr) {
    var table = tr.closest("table");
    var mLabel = table.dataset.match;
    var rd = tr.cells[HEAD_INDEX["局"]].textContent.replace("R", "");
    var who = tr.dataset.who;
    var d = byKey[mLabel + "-" + rd + "-" + who];
    if (!d) return;
    dTitle.textContent = "M" + d.m + " R" + d.r + " · " + d.who + (d.won ? " ✓ 贏" : " 輸");
    dSub.textContent = "局長 " + clock(d.dur) + " · 結果 " + (d.end || "—");
    [dFields, dClears, dTime].forEach(function (host) {
      while (host.firstChild) host.removeChild(host.firstChild);
    });
    FIELD_LABELS.forEach(function (pair) {
      var key = pair[0], label = pair[1], scale = pair[2];
      if (!(key in d.f)) return;
      var v = d.f[key];
      kv(dFields, label, scale === 1000 ? (v / 1000).toFixed(2) : String(v));
    });
    CLEAR_LABELS.forEach(function (pair) {
      if (!(pair[0] in d.c)) return;
      kv(dClears, pair[1], String(d.c[pair[0]]));
    });
    var h5 = document.createElement("h5");
    var queued = d.ge.reduce(function (a, e) { return a + e[1]; }, 0);
    h5.textContent = "俾人射埋嚟嘅攻擊：" + d.ge.length + " 次，合共 " + queued +
      " 行（未計 cancel）";
    dTime.appendChild(h5);
    if (d.ge.length) {
      dTime.appendChild(sparkline(d.ge, d.dur));
      var note = document.createElement("p");
      note.className = "rt-hint";
      note.textContent = "橫軸係時間（frame），每條係一次攻擊，高度係行數。";
      dTime.appendChild(note);
    }
    drawer.classList.add("is-open");
  }

  Array.prototype.forEach.call(sect.querySelectorAll(".rt-tbl"), function (table) {
    table.addEventListener("click", function (ev) {
      if (ev.target.closest("thead")) return;
      var tr = ev.target.closest("tbody tr");
      if (tr) openDrawer(tr);
    });
  });
  document.getElementById("rt-drawer-close").addEventListener("click", function () {
    drawer.classList.remove("is-open");
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") drawer.classList.remove("is-open");
  });

  /* ---------------- export ---------------- */
  function copyText(text, msg) {
    function done() { statusEl.textContent = msg; setTimeout(function () {
      statusEl.textContent = ""; }, 2600); }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () {
        statusEl.textContent = "複製唔到，請手動選取";
      });
    } else {
      var ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); }
      catch (err) { statusEl.textContent = "複製唔到"; }
      ta.remove();
    }
  }

  function visibleCsv() {
    var heads = Array.prototype.slice.call(sect.querySelectorAll(".rt-tbl thead th"))
      .map(function (th) { return th.textContent.replace(/[\u2195]/g, "").trim(); });
    var lines = [["場"].concat(heads).join(",")];
    Array.prototype.forEach.call(sect.querySelectorAll(".rt-tbl"), function (table) {
      var mLabel = table.dataset.match;
      Array.prototype.forEach.call(table.tBodies[0].rows, function (tr) {
        if (tr.offsetParent === null) return;
        var cells = Array.prototype.map.call(tr.cells, function (td) {
          var v = td.dataset.v !== undefined ? td.dataset.v : td.textContent;
          v = String(v).replace(/\s+/g, " ").trim();
          return /[",]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
        });
        lines.push(["M" + mLabel].concat(cells).join(","));
      });
    });
    return lines.join("\n");
  }

  document.getElementById("rt-csv").addEventListener("click", function () {
    var csv = visibleCsv();
    copyText(csv, "已複製 " + (csv.split("\n").length - 1) + " 行 CSV");
  });
  document.getElementById("rt-sum").addEventListener("click", function () {
    var rows = visibleRows();
    var wins = rows.filter(function (r) { return !r.classList.contains("rt-loser"); }).length;
    var parts = ["顯示 " + rows.length + " 行（贏 " + wins + " / 輸 " + (rows.length - wins) + "）"];
    [["APM", 1], ["PPS", 2], ["VS", 1], ["APP", 2]].forEach(function (p) {
      var m = mean(rows, p[0]);
      if (m !== null) parts.push("平均 " + p[0] + " " + m.toFixed(p[1]));
    });
    copyText(parts.join("，"), "已複製摘要");
  });

  /* ---------------- URL hash state ---------------- */
  function writeHash() {
    var bits = [];
    ["f-win", "f-yachi", "f-pinglamb"].forEach(function (c) {
      if (sect.classList.contains(c)) bits.push(c);
    });
    if (sect.classList.contains("rt-show-all")) bits.push("all");
    if (sect.classList.contains("rt-nobars")) bits.push("nobars");
    var h = bits.length ? "#rounds=" + bits.join(",") : "";
    if (h && location.hash !== h) history.replaceState(null, "", h);
  }
  (function readHash() {
    var m = /#rounds=([a-z,-]+)/.exec(location.hash);
    if (!m) { refresh(); return; }
    var bits = m[1].split(",");
    bits.forEach(function (b) {
      if (b === "all") {
        sect.classList.add("rt-show-all");
        var box = document.getElementById("rt-toggle-all");
        if (box) box.checked = true;
      } else if (b === "nobars") {
        sect.classList.add("rt-nobars");
        var bb = document.querySelector(".rt-chip[data-bars]");
        if (bb) bb.setAttribute("aria-pressed", "false");
      } else if (b.indexOf("f-") === 0) {
        setFilter(b);
      }
    });
    refresh();
  })();
})();
</script>
"""

SORT_JS = """
<script>
/* Click a column header to sort that match's rounds by it; click again to reverse;
   a third click restores the original round order. Self-contained, no libraries. */
(function () {
  var sect = document.getElementById("rounds");
  var chips = Array.prototype.slice.call(document.querySelectorAll(".rt-chip[data-filter]"));
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      chips.forEach(function (c) {
        c.setAttribute("aria-pressed", c === chip ? "true" : "false");
      });
      sect.classList.remove("f-win", "f-yachi", "f-pinglamb");
      if (chip.dataset.filter) sect.classList.add(chip.dataset.filter);
    });
  });
  var barBtn = document.querySelector(".rt-chip[data-bars]");
  if (barBtn) {
    barBtn.addEventListener("click", function () {
      var on = barBtn.getAttribute("aria-pressed") === "true";
      barBtn.setAttribute("aria-pressed", on ? "false" : "true");
      sect.classList.toggle("rt-nobars", on);
    });
  }
  var box = document.getElementById("rt-toggle-all");
  if (box) {
    box.addEventListener("change", function () {
      document.getElementById("rounds").classList.toggle("rt-show-all", box.checked);
    });
  }
  document.querySelectorAll("table.rt-tbl").forEach(function (table) {
    var body = table.tBodies[0];
    var heads = Array.prototype.slice.call(table.querySelectorAll("thead th"));
    heads.forEach(function (th, idx) {
      th.addEventListener("click", function () {
        var state = th.getAttribute("aria-sort");
        var next = state === "descending" ? "ascending"
                 : state === "ascending" ? "none" : "descending";
        heads.forEach(function (h) { h.removeAttribute("aria-sort"); });
        var rows = Array.prototype.slice.call(body.rows);
        if (next === "none") {
          rows.sort(function (a, b) {
            return (+a.dataset.order) - (+b.dataset.order);
          });
        } else {
          th.setAttribute("aria-sort", next);
          var dir = next === "ascending" ? 1 : -1;
          rows.sort(function (a, b) {
            var x = a.cells[idx].dataset.v, y = b.cells[idx].dataset.v;
            var nx = parseFloat(x), ny = parseFloat(y);
            var cmp = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : String(x).localeCompare(String(y));
            /* stable: fall back to the original order so equal values keep round order */
            return cmp !== 0 ? cmp * dir : (+a.dataset.order) - (+b.dataset.order);
          });
        }
        rows.forEach(function (r) { body.appendChild(r); });
      });
    });
  });
})();
</script>
"""

# Columns whose measured value does not justify a permanent slot. Over 129 rounds
# (both sessions), each was scored on how often the round's winner held the higher
# value — the paired AUC, where 50% means the column says nothing about who won —
# plus its spread and its share of zeros:
#
#   PC     AUC 50.8%, 89.1% zeros   — says nothing, and is empty nine times in ten
#   COMBO  AUC 45.0%                — no signal
#   TST    AUC 55.8%, 23.6% zeros   — little signal, often empty
#   TSD    AUC 60.9%                — weak
#   KPP    AUC 39.9%, CV 0.05       — near-constant; the finding is its flatness,
#   FIN%   AUC 64.0%, CV 0.05         which the verdict cards already state
#
# They stay available behind a toggle rather than being deleted: hiding them takes
# the table from 1430px to 1121px, inside the 1130px container, so the default view
# needs no horizontal scrolling at all.
OPTIONAL_COLS = {"PC", "COMBO", "TST", "TSD", "KPP", "FIN%"}

# In-cell magnitude bars, only on the columns that measured as strongly tied to the
# round result (paired AUC >= 85%, counting inverted). Barring all 22 would be noise;
# these four are where a glance is worth as much as reading the number.
# The scale is session-wide, not per match, so a bar length means the same thing in
# every table. One hue, light to dark by magnitude — sequential data, sequential ramp.
BAR_COLS = {"APM", "VS", "APP", "攻"}

# (header label, title/explanation) — order defines the columns after the pinned three
COLUMNS = [
    ("APM", "attack per minute"),
    ("PPS", "pieces per second"),
    ("VS", "versus score"),
    ("方塊", "pieces placed"),
    ("APP", "attack per piece"),
    ("KPP", "keypresses per piece"),
    ("DS", "garbage cleared per piece (downstack)"),
    ("清行", "lines cleared"),
    ("SPIKE", "biggest single spike"),
    ("B2B", "longest back-to-back chain"),
    ("COMBO", "longest combo"),
    ("T", "T-spins including ones that cleared nothing"),
    ("QUAD", "quads"),
    ("TSD", "T-spin doubles"),
    ("TST", "T-spin triples"),
    ("PC", "perfect clears"),
    ("FIN%", "perfect-placement rate"),
    ("錯", "finesse faults"),
    ("攻", "attack dealt"),
    ("送", "garbage sent"),
    ("射埋", "attack queued at this player, before cancelling"),
    ("食", "garbage that actually materialised"),
    ("清", "garbage cleared away"),
    ("分", "in-game score"),
    ("結果", "how the round ended for this player"),
]


def ratio(num, den, dp=2):
    if not den:
        return "–"
    scale = 10 ** dp
    return f"{(num * scale) // den / scale:.{dp}f}"


def pct(num, den):
    return "–" if not den else f"{(num * 100) // den}%"


END_LABEL = {"winner": "生還", "garbagesmash": "俾垃圾頂爆",
             "topout": "自己頂爆", "forfeit": "投降"}


def bar_ranges(facts):
    """Session-wide min/max for the barred columns, so bars are comparable."""
    acc = {k: [] for k in BAR_COLS}
    for m in facts["matches"]:
        for r in m["rounds"]:
            for p in r["players"].values():
                acc["APM"].append(p["apm_x1000"])
                acc["VS"].append(p["vs_x1000"])
                acc["攻"].append(p["garbage_attack"])
                acc["APP"].append((p["garbage_attack"] * 1000) // p["pieces"]
                                  if p["pieces"] else 0)
    return {k: (min(v), max(v)) for k, v in acc.items() if v}


def bar_value(p, label):
    if label == "APM":
        return p["apm_x1000"]
    if label == "VS":
        return p["vs_x1000"]
    if label == "攻":
        return p["garbage_attack"]
    if label == "APP":
        return (p["garbage_attack"] * 1000) // p["pieces"] if p["pieces"] else 0
    return None


def cells(p, won):
    """The stat cells for one player in one round, in COLUMNS order."""
    c = p["clears"]
    queued = sum(g["amt"] for g in p["garbage_events"])
    reason = p.get("gameoverreason", "")
    return [
        (r1(p["apm_x1000"]), True),
        (r2(p["pps_x1000"]), True),
        (r1(p["vs_x1000"]), True),
        (str(p["pieces"]), False),
        (ratio(p["garbage_attack"], p["pieces"]), True),
        (ratio(p["inputs"], p["pieces"]), False),
        (ratio(p["garbage_cleared"], p["pieces"]), False),
        (str(p["lines"]), False),
        (str(p["maxspike"]), True),
        (str(p["topbtb"]), False),
        (str(p["topcombo"]), False),
        (str(p["tspins"]), False),
        (str(c["quads"]), False),
        (str(c["tspin_doubles"]), False),
        (str(c["tspin_triples"]), False),
        (str(c["allclear"]), False),
        (pct(p["finesse_perfect"], p["pieces"]), False),
        (str(p["finesse_faults"]), False),
        (str(p["garbage_attack"]), False),
        (str(p["garbagesent"]), False),
        (str(queued), False),
        (str(p["garbagereceived"]), False),
        (str(p["garbage_cleared"]), False),
        (f"{p['score']:,}", False),
        (END_LABEL.get(reason, reason or "–"), False),
    ]


def findings(report_dir):
    """The APP / KPP / DS verdicts from the generated ledger, with proof status.

    These are read from claims-generated.json rather than re-derived here, so the card
    text and the proved lemma are the same statement.
    """
    keep = ("rate_split_", "rate_flat_", "app_decides_rounds", "ds_session",
            "keys_per_piece", "per_piece_")
    out = []
    for c in claim_cards.by_family(claim_cards.load(report_dir), keep):
        fam = c["family"]
        metric = ("APP" if "garbage_attack" in fam or fam == "app_decides_rounds"
                  else "KPP" if "inputs" in fam or fam == "keys_per_piece"
                  else "DS" if "garbage_cleared" in fam or fam == "ds_session"
                  else "FINESSE")
        # Three kinds, because they answer different questions:
        #   lever      the player's own rate differs between rounds won and lost
        #   flat       it barely differs, so it is not what decides their rounds
        #   compare    one player against the other — says nothing about winning,
        #              and must not be dressed up as if it did
        if fam.startswith("rate_flat_"):
            kind = "flat"
        elif fam.startswith("rate_split_") or fam == "app_decides_rounds":
            kind = "lever"
        else:
            kind = "compare"
        out.append({"id": c["id"], "metric": metric, "kind": kind,
                    "canto": c["canto"], "verified": c["verified"]})
    order = {"APP": 0, "DS": 1, "KPP": 2, "FINESSE": 3}
    rank = {"lever": 0, "flat": 1, "compare": 2}
    out.sort(key=lambda d: (rank[d["kind"]], order.get(d["metric"], 9), d["id"]))
    return out


DETAIL_FIELDS = [
    ("apm_x1000", "APM", 1000), ("pps_x1000", "PPS", 1000), ("vs_x1000", "VS", 1000),
    ("pieces", "方塊", 1), ("lines", "清行", 1), ("inputs", "按鍵", 1),
    ("holds", "hold", 1), ("kills", "KO", 1),
    ("garbage_attack", "攻擊", 1), ("garbagesent", "送出", 1),
    ("garbagereceived", "食垃圾", 1), ("garbage_cleared", "清垃圾", 1),
    ("maxspike", "最大 spike", 1), ("maxspike_nomult", "spike(無倍率)", 1),
    ("garbage_sent_raw", "送出(原始)", 1), ("garbage_sent_nomult", "送出(無倍率)", 1),
    ("topbtb", "B2B", 1), ("topcombo", "combo", 1), ("tspins", "T-spin", 1),
    ("finesse_perfect", "完美擺放", 1), ("finesse_faults", "finesse 失誤", 1),
    ("finesse_combo", "finesse 連續", 1),
    ("score", "分數", 1), ("combo_power", "combo power", 1),
    ("btb_power", "B2B power", 1), ("finaltime_ms", "引擎時長(ms)", 1),
]
CLEAR_FIELDS = [
    ("singles", "single"), ("doubles", "double"), ("triples", "triple"),
    ("quads", "quad"), ("pentas", "penta"),
    ("tspin_singles", "TSS"), ("tspin_doubles", "TSD"), ("tspin_triples", "TST"),
    ("tspin_quads", "TSQ"), ("mini_tspin_singles", "mini TSS"),
    ("mini_tspin_doubles", "mini TSD"), ("mini_tspin_triples", "mini TST"),
    ("real_tspins", "真 T-spin"), ("mini_tspins", "mini T-spin"),
    ("allclear", "Perfect Clear"),
]


def detail_payload(facts):
    """Per-round records for the drawer, including the frame-stamped attack timeline.

    The table can only show a total for queued attack; the drawer is where the
    timeline actually lives, which is the point of keeping the events in facts.json.
    """
    out = []
    for mi, m in enumerate(facts["matches"]):
        for ri, r in enumerate(m["rounds"]):
            dur = max(d["lifetime"] for d in r["players"].values())
            for pl, p in r["players"].items():
                out.append({
                    "m": mi + 1, "r": ri + 1, "who": pl,
                    "won": r["winner"] == pl, "dur": dur,
                    "end": p.get("gameoverreason", ""),
                    "f": {k: p[k] for k, _lab, _s in DETAIL_FIELDS if k in p},
                    "c": {k: p["clears"][k] for k, _lab in CLEAR_FIELDS
                          if k in p["clears"]},
                    "ge": [[g["frame"], g["amt"]] for g in p["garbage_events"]],
                })
    return out


def build(facts, report_dir=None):
    p1, p2 = facts["players"]
    ranges = bar_ranges(facts)
    out = [START, CSS,
           '<section id="rounds">', '  <div class="wrap-wide">',
           '    <div class="eyebrow">逐局數據 · ROUND BY ROUND</div>',
           '    <h2 class="section-title">逐局全數據</h2>',
           '    <p class="rt-legend">',
           '      每局兩行，一行一個玩家，贏嗰行有底色同 ✓。除咗遊戲畫面嘅 APM / PPS / VS，',
           '      仲有：<code>APP</code> 每粒方塊嘅攻擊、<code>KPP</code> 每粒方塊按幾多下、',
           '      <code>DS</code> 每粒方塊清走幾多垃圾、<code>FIN%</code> 完美擺放率同失誤次數、',
           '      <code>射埋</code>（對手射過嚟、未 cancel 嘅攻擊）對 <code>食</code>（真正變成垃圾行）、',
           '      同埋 <code>結果</code>（點收嘅）。',
           '    </p>',
           ]
    cards = findings(report_dir) if report_dir else []
    if cards:
        out += [
            '    <h3 style="font-size:1.05rem;margin:.2rem 0 .3rem">'
            '每粒方塊嘅效率：邊個數真係決定輸贏</h3>',
            '    <p class="rt-legend" style="margin-bottom:.9rem">',
            '      呢幾個判斷係由 pipeline 自動生成、再逐條用 Dafny 證過嘅（claim id 喺下面）。',
            '      <b>決定輸贏</b>／<b>唔係關鍵</b> 係拿同一個玩家「贏嘅局」對「輸嘅局」比出嚟嘅；',
            '      <b>兩人對比</b> 淨係比兩個人嘅高低，講唔到邊個數影響勝負。',
            '    </p>',
            '    <div class="rt-find">',
        ]
        VERDICT = {"lever": ("is-lever", "決定輸贏"),
                   "flat": ("is-flat", "唔係關鍵"),
                   "compare": ("is-compare", "兩人對比")}
        for c in cards:
            cls, verdict = VERDICT[c["kind"]]
            tick = "✓ Dafny 已證" if c["verified"] else "⏳ 待證"
            out.append(f'      <div class="rt-card {cls}">')
            out.append(f'        <div class="rt-metric">{c["metric"]}'
                       f'<span class="rt-verdict">{verdict}</span></div>')
            out.append(f'        <p>{c["canto"]}</p>')
            out.append(f'        <div class="rt-cid">{c["id"]} · {tick}</div>')
            out.append('      </div>')
        out.append('    </div>')
    nrounds = sum(len(m["rounds"]) for m in facts["matches"])
    nrows = nrounds * 2
    last_ts = facts["matches"][-1]["ts"][:10] if facts["matches"][-1].get("ts") else ""
    out += [
        f'    <p class="rt-meta">全部 <b>{nrounds}</b> 局（<b>{nrows}</b> 行，一局兩行）'
        f'都焗死喺呢個檔案裏面 —— 篩選只係改你睇到嘅範圍，唔會改檔案內容。'
        f'{"資料截至 " + last_ts + "。" if last_ts else ""}'
        f'<span id="rt-count"></span></p>',
        '    <div class="rt-controls">',
        '      <button class="rt-chip" data-filter="" aria-pressed="true">全部局</button>',
        '      <button class="rt-chip" data-filter="f-win" aria-pressed="false">只睇贏嘅一方</button>',
        f'      <button class="rt-chip" data-filter="f-yachi" aria-pressed="false">只睇 {p1}</button>',
        f'      <button class="rt-chip" data-filter="f-pinglamb" aria-pressed="false">只睇 {p2}</button>',
        '      <button class="rt-chip" data-bars aria-pressed="true">長條圖</button>',
        '      <label class="rt-toggle" style="margin:0">'
        '<input type="checkbox" id="rt-toggle-all">'
        f'全部 {len(COLUMNS) + 3} 欄</label>',
        '      <button class="rt-chip" id="rt-clear">清空篩選</button>',
        '      <button class="rt-chip" id="rt-csv">複製 CSV</button>',
        '      <button class="rt-chip" id="rt-sum">複製摘要</button>',
        '      <span class="rt-status" id="rt-status"></span>',
        '    </div>',
        '    <dl class="rt-summary" id="rt-summary"></dl>',
        f'    <p class="rt-hint" style="margin:-.6rem 0 1rem">APM／VS／APP／攻 嘅長條'
        '按全 session 同一把尺畫，所以跨場都可以直接比。</p>',
    ]
    for mi, m in enumerate(facts["matches"]):
        lb, win = m["leaderboard"], m["winner"]
        out.append('    <div class="rt-match">')
        out.append('      <div class="rt-head">')
        out.append(f'        <span class="rt-no">M{mi + 1}</span>')
        out.append(f'        <span class="rt-score"><span class="rt-y">{p1}</span> '
                   f'{m["score"][p1]}:{m["score"][p2]} '
                   f'<span class="rt-p">{p2}</span></span>')
        out.append(f'        <span class="rt-who">{win} 贏</span>')
        out.append('        <span class="rt-agg">'
                   f'{p1} {r1(lb[p1]["apm_x1000"])}/{r2(lb[p1]["pps_x1000"])}/'
                   f'{r1(lb[p1]["vs_x1000"])} &nbsp;·&nbsp; '
                   f'{p2} {r1(lb[p2]["apm_x1000"])}/{r2(lb[p2]["pps_x1000"])}/'
                   f'{r1(lb[p2]["vs_x1000"])} &nbsp;(APM/PPS/VS)</span>')
        out.append('      </div>')
        out.append('      <div class="rt-scroll">')
        out.append(f'        <table class="rt-tbl" data-match="{mi + 1}">')
        out.append('          <thead><tr>')
        ARROW = '<span class="rt-arrow">↕</span>'
        out.append(f'            <th class="c-rd" title="round number">局{ARROW}</th>'
                   f'<th class="c-time" title="round length">時間{ARROW}</th>'
                   f'<th class="c-who" title="player">玩家{ARROW}</th>')
        for label, title in COLUMNS:
            klass = ["c-end"] if label == "結果" else []
            if label in OPTIONAL_COLS:
                klass.append("rt-opt")
            cls = f' class="{" ".join(klass)}"' if klass else ""
            out.append(f'            <th{cls} title="{title}">{label}{ARROW}</th>')
        out.append('          </tr></thead>')
        out.append('          <tbody>')
        for ri, r in enumerate(m["rounds"]):
            dur = max(d["lifetime"] for d in r["players"].values())
            for n, pl in enumerate((p1, p2)):
                p = r["players"][pl]
                won = r["winner"] == pl
                classes = []
                if won:
                    classes.append("rt-w-y" if pl == p1 else "rt-w-p")
                else:
                    classes.append("rt-loser")
                if n == 1:
                    classes.append("rt-round-end")
                out.append(f'            <tr class="{" ".join(classes)}" '
                           f'data-order="{ri * 2 + n}" data-who="{pl}">')
                # Every row repeats 局 and 時間 instead of using rowspan: rowspan would
                # pin the pairs together and make the table unsortable.
                out.append(f'              <td class="c-rd" data-v="{ri}">R{ri + 1}</td>')
                out.append(f'              <td class="c-time" data-v="{dur}">{fmt_clock(dur)}</td>')
                dot = "is-y" if pl == p1 else "is-p"
                mark = ' <span class="rt-win-mark">✓</span>' if won else ""
                out.append(f'              <td class="c-who" data-v="{pl}">'
                           f'<span class="rt-dot {dot}"></span>{pl}{mark}</td>')
                for (val, key), (label, _t) in zip(cells(p, won), COLUMNS):
                    cls = []
                    if label == "結果":
                        cls.append("c-end")
                    elif key:
                        cls.append("rt-key")
                    if label in OPTIONAL_COLS:
                        cls.append("rt-opt")
                    if val in ("0", "–"):
                        cls.append("rt-zero")
                    # data-v carries the raw value so sorting and the summary means are
                    # numeric, not textual ("10" must not sort before "9"). It MUST be
                    # computed before any markup is wrapped around the value, or the
                    # sort key becomes the markup itself.
                    raw = val.replace(",", "").replace("%", "")
                    try:
                        key_v = str(float(raw))
                    except ValueError:
                        key_v = val
                    style = ""
                    if label in BAR_COLS and label in ranges:
                        lo, hi = ranges[label]
                        bv = bar_value(p, label)
                        if bv is not None and hi > lo:
                            frac = (bv - lo) / (hi - lo)
                            cls.append("rt-bar")
                            style = f' style="--b:{frac:.3f}"'
                            val = f"<span>{val}</span>"
                    attr = f' class="{" ".join(cls)}"' if cls else ""
                    attr += style
                    out.append(f'              <td{attr} data-v="{key_v}">{val}</td>')
                out.append('            </tr>')
        out.append('          </tbody>')
        out.append('        </table>')
        out.append('      </div>')
        out.append('      <p class="rt-hint">← 左右拉睇齊全部欄 · 點欄名可以排序 →</p>')
        out.append('    </div>')
    out += [
        '    <aside class="rt-drawer" id="rt-drawer" aria-live="polite">',
        '      <div class="rt-drawer-head">',
        '        <h4 id="rt-drawer-title"></h4>',
        '        <span class="rt-hint" id="rt-drawer-sub"></span>',
        '        <button class="rt-close" id="rt-drawer-close">關閉 ✕</button>',
        '      </div>',
        '      <div class="rt-fields" id="rt-drawer-fields"></div>',
        '      <div class="rt-fields" id="rt-drawer-clears"></div>',
        '      <div class="rt-timeline" id="rt-drawer-timeline"></div>',
        '    </aside>',
        '  </div>',
        '<script type="application/json" id="rt-rounds">'
        + json.dumps(detail_payload(facts), ensure_ascii=False, separators=(",", ":"))
        + '</script>',
        SORT_JS,
        (EXPLORE_JS
         .replace("__FIELD_LABELS__",
                  json.dumps([[k, lab, sc] for k, lab, sc in DETAIL_FIELDS],
                             ensure_ascii=False))
         .replace("__CLEAR_LABELS__",
                  json.dumps([[k, lab] for k, lab in CLEAR_FIELDS],
                             ensure_ascii=False))),
        '</section>', END,
    ]
    return "\n".join(out) + "\n"


def inject(report_path, section):
    with open(report_path, encoding="utf-8") as fh:
        html = fh.read()
    if START in html and END in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: section.rstrip("\n"),
                      html, flags=re.S)
        how = "replaced"
    else:
        anchor = '<section id="appendix">'
        if anchor not in html:
            raise SystemExit(f"cannot find {anchor} in {report_path}")
        html = html.replace(anchor, section + "\n" + anchor, 1)
        how = "inserted before the appendix"
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return how


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report_dir", help="a session's report/ directory")
    args = ap.parse_args(argv)

    with open(os.path.join(args.report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    report_path = os.path.join(args.report_dir, "report.html")
    section = build(facts, args.report_dir)
    how = inject(report_path, section)
    nrounds = sum(len(m["rounds"]) for m in facts["matches"])
    print(f"{how}: {nrounds} rounds x {len(COLUMNS) + 3} columns over "
          f"{len(facts['matches'])} matches -> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
