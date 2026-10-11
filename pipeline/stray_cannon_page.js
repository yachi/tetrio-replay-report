/* 迷走砲 node-page controller — pipeline/stray_cannon_page.py inlines this AFTER replay_player.js.

   Page-only: which case is showing, and the hash. The boards, seek bar, keys and key moments are
   the shared player (rpReplay.mount), mounted on a clone of the #scp-player-tpl box only when a
   case is picked (a click on a case link, or a hash naming one), and destroy()ed before the next,
   so one player exists at a time and no listener outlives its round.

   - the hash is #<date>-m<pos>r<round>@p<n>; every case link is a plain link carrying the position
     just after the case's own step, and moving inside a round rewrites the hash with replaceState;
   - nodes are built with createElement / textContent only. */
(function () {
  "use strict";
  var island = document.getElementById("scp-data");
  var root = document.getElementById("round-replay");
  var tpl = document.getElementById("scp-player-tpl");
  if (!island || !root || !tpl || !window.rpReplay) return;
  var DATA = JSON.parse(island.textContent);
  var byKey = {};
  Object.keys(DATA.rounds).forEach(function (k) {
    var r = DATA.rounds[k], full = {};
    Object.keys(DATA.shared).forEach(function (f) { full[f] = DATA.shared[f]; });
    Object.keys(r).forEach(function (f) { full[f] = r[f]; });
    byKey[k] = full;
  });

  var host = root.querySelector(".rpg-host");
  var nowEl = document.getElementById("rpg-now");
  var idleEl = root.querySelector(".scp-idle");
  var notesEl = root.querySelector(".rpg-notes");
  var flagEl = root.querySelector(".rpg-flag");
  var missingEl = root.querySelector(".rpg-missing");
  var links = Array.prototype.slice.call(document.querySelectorAll(".scp-case"));

  var cur = null, handle = null, quiet = false;

  function el(tag) { return document.createElement(tag); }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  /* ---------- the hash ---------- */
  function parseHash() {
    var m = /^#(\d{4}-\d{2}-\d{2}-m\d+r\d+)(?:@p(\d+))?$/.exec(location.hash);
    return m ? { key: m[1], pos: m[2] == null ? 0 : +m[2] } : null;
  }
  function writeHash(pos) {
    if (quiet || !cur || !history.replaceState) return;
    var h = "#" + cur.label + "@p" + pos;
    if (location.hash !== h) history.replaceState(null, "", h);
  }

  /* ---------- switching cases ---------- */
  function show(key, pos) {
    var D = byKey[key];
    /* quiet BEFORE destroy: destroy() pauses, and that pause's notify() reports playing false
       with the OLD cur and position — unguarded it would overwrite the hash the link just set. */
    quiet = true;
    if (handle) { handle.destroy(); handle = null; }
    clear(host);
    cur = D;
    var box = tpl.content.firstElementChild.cloneNode(true);
    box.setAttribute("aria-label", D.label + " 模擬重播；撳 ? 睇快捷鍵");
    host.appendChild(box);
    nowEl.textContent = D.session + " 第 " + D.match + " 場第 " + D.round + " 局 · " + D.file
      + " · " + D.winner + " 贏";
    idleEl.hidden = true;
    clear(notesEl);
    D.notes.forEach(function (n, i) {
      if (i) notesEl.appendChild(el("br"));
      notesEl.appendChild(document.createTextNode(n));
    });
    flagEl.hidden = !D.flags.length;
    missingEl.hidden = true;
    links.forEach(function (a) {
      if (a.getAttribute("data-round") === key) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    });
    handle = rpReplay.mount(root, box, D, {
      hashPrefix: null,
      pos: pos,
      onChange: function (p, frames, playing) {
        /* never while playing: notify() fires every animation frame, and WebKit throws once a
           page passes ~100 history calls in a short window, which would kill the rAF loop. */
        if (!playing) writeHash(p);
      }
    });
    quiet = false;
    return box;
  }

  function fromHash(focus) {
    var h = parseHash();
    if (h && byKey[h.key]) {
      var box = show(h.key, h.pos);
      root.scrollIntoView();
      if (focus) box.focus({ preventScroll: true });
      return;
    }
    missingEl.hidden = !(h || location.hash.length > 1) || /^#g-/.test(location.hash);
  }
  window.addEventListener("hashchange", function () { fromHash(true); });
  links.forEach(function (a) {
    // a click on the case already showing would not fire hashchange; reset it explicitly
    a.addEventListener("click", function (e) {
      if (location.hash === a.getAttribute("href")) { e.preventDefault(); fromHash(true); }
    });
  });
  fromHash(false);
})();
