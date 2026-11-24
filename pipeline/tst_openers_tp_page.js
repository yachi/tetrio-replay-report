const D = JSON.parse(document.getElementById('data').textContent);
const COL = { I: '#2fb8c9', O: '#e3b425', T: '#9a46d6', S: '#4cb648', Z: '#d9433d', J: '#3b61d6', L: '#e5792a' };
const NS = 'http://www.w3.org/2000/svg';
const sdBtns = [...document.querySelectorAll('.bar[data-bar="sd"] button')];
const posBtns = [...document.querySelectorAll('.bar[data-bar="pos"] button')];
const kindBtns = [...document.querySelectorAll('.bar[data-bar="kind"] button')];
const lab = {};
for (const b of sdBtns) lab[b.dataset.b] = b.textContent;
let sd = D.sd_default, pos = D.filter_default, kind = D.kind_default || 'all';
// Bag-1 pieces are upper case and drawn solid; bag-2 pieces are lower case and drawn lighter.
function mini(g) {
  const H = g.length / 10, cs = 11, sv = document.createElementNS(NS, 'svg');
  sv.setAttribute('width', 110); sv.setAttribute('height', H * cs); sv.classList.add('board');
  const r = (x, y, f, o) => {
    const e = document.createElementNS(NS, 'rect');
    e.setAttribute('x', x * cs + .5); e.setAttribute('y', y * cs + .5); e.setAttribute('width', cs - 1); e.setAttribute('height', cs - 1);
    e.setAttribute('fill', f);
    if (o) for (const k in o) e.setAttribute(k, o[k]);
    sv.appendChild(e);
  };
  r(0, 0, 'var(--well)', { width: 110, height: H * cs, x: 0, y: 0 });
  for (let i = 0; i < g.length; i++) {
    const k = g[i];
    if (k === '.') r(i % 10, Math.floor(i / 10), 'var(--grid)');
    else r(i % 10, Math.floor(i / 10), COL[k.toUpperCase()], k === k.toUpperCase() ? null : { opacity: .55 });
  }
  return sv;
}
// Every figure is precomputed by the renderer (floored); this script only draws them and re-orders the cards.
for (const d of document.querySelectorAll('details[data-s]')) d.addEventListener('toggle', () => {
  const box = d.querySelector('.tl');
  if (!d.open || box.childElementCount) return;
  const c = D.cards[d.dataset.s];
  const hint = document.createElement('p'); hint.className = 'muted sm'; hint.textContent = D.cl.cl_hint;
  box.before(hint);
  const panel = document.createElement('div'); panel.className = 'bo'; panel.hidden = true;
  box.after(panel);
  let open = -1;
  const toggle = (j, f) => {
    for (const o of box.children) o.setAttribute('aria-expanded', 'false');
    if (panel._stop) panel._stop();
    if (open === j) { open = -1; panel.hidden = true; panel.replaceChildren(); return; }
    open = j; f.setAttribute('aria-expanded', 'true');
    showBuild(panel, c, j); panel.hidden = false;
  };
  let j0 = 0;
  for (const [g, name, left, p5, ...ds] of c.t) {
    const f = document.createElement('figure');
    const j = j0++;
    f.setAttribute('role', 'button'); f.tabIndex = 0; f.setAttribute('aria-expanded', 'false'); f.dataset.j = j;
    f.addEventListener('click', () => toggle(j, f));
    f.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(j, f); } });
    f.appendChild(mini(g));
    const cap = document.createElement('figcaption');
    const top = document.createElement('b'); top.textContent = name;
    cap.append(top, ' ' + D.labels[3] + left + ' · PC ' + p5);
    f.appendChild(cap);
    const sdc = document.createElement('figcaption');
    D.bk.forEach((k, i) => { sdc.append(lab[k] + ' '); const e = document.createElement('b'); e.textContent = ds[i]; sdc.append(e, ' '); });
    f.appendChild(sdc);
    box.appendChild(f);
  }
});
// The build of one class, stepped piece by piece, and its worked PC (all precomputed by the renderer and audited).
const el = (t, cls, txt) => { const e = document.createElement(t); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
function board(H, cells, cs, flash) {
  const sv = document.createElementNS(NS, 'svg');
  sv.setAttribute('viewBox', `0 0 ${10 * cs} ${H * cs}`); sv.setAttribute('width', 10 * cs); sv.setAttribute('height', H * cs); sv.classList.add('board');
  const r = (x, y, a) => { const e = document.createElementNS(NS, 'rect'); for (const k in a) e.setAttribute(k, a[k]);
    e.setAttribute('x', x * cs + .5); e.setAttribute('y', (H - 1 - y) * cs + .5); e.setAttribute('width', cs - 1); e.setAttribute('height', cs - 1); sv.appendChild(e); };
  const bg = document.createElementNS(NS, 'rect'); bg.setAttribute('width', 10 * cs); bg.setAttribute('height', H * cs); bg.setAttribute('fill', 'var(--well)'); sv.appendChild(bg);
  for (let y = 0; y < H; y++) for (let x = 0; x < 10; x++) {
    const k = cells.get(y * 10 + x);
    if (!k) { r(x, y, { fill: 'var(--grid)' }); continue; }
    const a = { fill: k.fill };
    if (k.op) a.opacity = k.op;
    if (k.dash) { a.fill = 'none'; a.stroke = COL.T; a['stroke-width'] = 2; a['stroke-dasharray'] = '3 2'; }
    if (k.cur) { a.stroke = 'var(--fg)'; a['stroke-width'] = 2; }
    r(x, y, a);
    if (k.n) { const t = document.createElementNS(NS, 'text'); t.setAttribute('x', x * cs + cs / 2); t.setAttribute('y', (H - 1 - y) * cs + cs * .72);
      t.setAttribute('text-anchor', 'middle'); t.setAttribute('font-size', (cs * .55).toFixed(1)); t.setAttribute('fill', '#fff'); t.setAttribute('font-weight', '700');
      t.textContent = k.n; sv.appendChild(t); }
  }
  if (flash) for (const y of flash) {
    const e = document.createElementNS(NS, 'rect'); e.setAttribute('class', 'an-fl');
    e.setAttribute('x', 0); e.setAttribute('y', (H - 1 - y) * cs); e.setAttribute('width', 10 * cs); e.setAttribute('height', cs); sv.appendChild(e);
  }
  return sv;
}
// Rows of `cells` that are full, and the board with them cleared (rows above drop).
const fullRows = cells => { const n = new Map(); for (const q of cells.keys()) n.set(Math.floor(q / 10), (n.get(Math.floor(q / 10)) || 0) + 1);
  return [...n].filter(([, c]) => c === 10).map(([y]) => y).sort((a, b) => a - b); };
const clearRows = (cells, rows) => { const o = new Map();
  for (const [q, v] of cells) { const y = Math.floor(q / 10); if (rows.includes(y)) continue; o.set((y - rows.filter(r => r < y).length) * 10 + q % 10, v); }
  return o; };
const plain = cells => { const o = new Map(); for (const [q, v] of cells) o.set(q, { fill: v.fill, op: v.op }); return o; };
const REDUCE = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
const SPEEDS = [1100, 650, 330];
let speed = 1;
// The build of one class and its worked PC as one animation: every piece of the build, the T into the TST slot and its
// clear, then the solver's PC piece by piece until the board is empty (all precomputed by the renderer and audited).
function showBuild(panel, c, j) {
  panel.replaceChildren();
  if (!c.b[j]) { panel.append(el('p', 'muted sm', D.cl.bo_nobuild)); return; }
  const [order, sdTot] = c.b[j], [tst, line] = c.x[j], n1 = c.n1, m = order.length + 1;
  let bH = 1; for (const [, cs] of order) for (const q of cs) bH = Math.max(bH, Math.floor(q / 10) + 1);
  for (const q of tst) bH = Math.max(bH, Math.floor(q / 10) + 1);
  const e = D.px[line] || {};
  const vars = [];
  if (e.b3) vars.push([D.cl.an_v3, e.b3, D.cl.pcx_deal3.replace('{d}', e.b3[0][0])]);
  const lf = e.l ? D.cl.pcx_left.replace('{left}', e.l) : '';
  panel.append(el('h4', null, D.cl.bo_title));
  const vbar = el('div', 'an-v'), deal = el('p', 'muted sm');
  const wrap = el('div', 'bo-w'), side = el('div', 'bo-s'), pic = el('div', 'an-pic'), cap = el('p', 'an-cap');
  const nav = el('div', 'bo-nav an-nav'), seek = el('input'), list = el('ol', 'bo-l');
  seek.type = 'range'; seek.min = 0; seek.className = 'an-seek'; seek.setAttribute('aria-label', D.cl.an_seek);
  let frames = [], f = 0, timer = null, vi = 0, H = bH;
  const chips = [];
  const build = () => {
    frames = []; chips.length = 0; list.replaceChildren();
    const ex = vars[vi] ? vars[vi][1] : null;
    H = Math.max(bH, ex ? ex[1] : 0);
    const chip = (txt, color, extra) => { const li = el('li'); const b = el('button'); b.type = 'button';
      const k = el('b', null, txt); if (color) k.style.color = color; b.append(k); if (extra) b.append(' ' + extra);
      const at = frames.length; b.onclick = () => { stop(); go(at); }; li.append(b); chips.push([li, at]); list.append(li); };
    // the build
    let cells = new Map();
    frames.push({ cells: new Map(tst.map(q => [q, { dash: true }])), cap: D.cl.bo_step.replace('{n}', 0).replace('{m}', m) });
    list.append(el('li', 'bo-g', D.cl.bo_b1));
    order.forEach(([k, cs, d], i) => {
      if (i === n1) list.append(el('li', 'bo-g', D.cl.bo_rest));
      chip(k, COL[k], d ? D.cl.bo_sd : '');
      const now = plain(cells); for (const q of cs) now.set(q, { fill: COL[k], op: i < n1 ? null : .85 });
      cells = new Map(now); for (const q of cs) now.set(q, { fill: COL[k], op: i < n1 ? null : .85, cur: true });
      for (const q of tst) now.set(q, { dash: true });
      frames.push({ cells: now, cap: D.cl.bo_step.replace('{n}', i + 1).replace('{m}', m) + ' · ' + k + (d ? ' ' + D.cl.bo_sd : '') });
    });
    list.append(el('li', 'bo-g', D.cl.bo_tst)); chip('T', COL.T, '');
    for (const q of tst) cells.set(q, { fill: COL.T });
    const rows = fullRows(cells), withT = plain(cells); for (const q of tst) withT.set(q, { fill: COL.T, cur: true });
    frames.push({ cells: withT, flash: rows, cap: D.cl.bo_step.replace('{n}', m).replace('{m}', m) + ' · ' + D.cl.bo_tst + ' · ' + D.cl.an_clear.replace('{n}', rows.length), hold: 2 });
    // what the clear leaves: drawn in the build's colours when it is the audited residue, else in grey from it
    let left = clearRows(cells, rows);
    if (e.r) {
      const want = new Set(); e.r.forEach((row, y) => { for (let x = 0; x < 10; x++) if (row >> x & 1) want.add(y * 10 + x); });
      if (want.size !== left.size || [...want].some(q => !left.has(q))) left = new Map([...want].map(q => [q, { fill: '#8a8f9c' }]));
    }
    frames.push({ cells: left, cap: D.cl.an_left });
    if (!ex) return;
    // the worked PC, simulated from the residue: each step's cells are on the board as it stands at that step
    const steps = ex[3];
    list.append(el('li', 'bo-g', D.cl.an_pcg));
    cells = plain(left);
    steps.forEach(([p, cs, hd], i) => {
      chip(p, COL[p], hd ? D.cl.pcx_hold : '');
      for (const q of cs) cells.set(q, { fill: COL[p] });
      const now = plain(cells); for (const q of cs) now.set(q, { fill: COL[p], cur: true });
      const fr = fullRows(cells);
      frames.push({ cells: now, flash: fr, hold: fr.length ? 1.6 : 1,
        cap: D.cl.an_pc_step.replace('{n}', i + 1).replace('{m}', steps.length).replace('{p}', p) + (hd ? D.cl.pcx_hold : '') });
      cells = clearRows(cells, fr);
    });
    frames.push({ cells, cap: cells.size ? '' : D.cl.an_pc_done, hold: 2.5 });
  };
  const go = i => {
    f = Math.max(0, Math.min(frames.length - 1, i));
    const fr = frames[f];
    pic.replaceChildren(board(H, fr.cells, 22, fr.flash));
    cap.textContent = fr.cap;
    seek.value = f;
    let on = -1; chips.forEach(([, at], k) => { if (at <= f) on = k; });
    chips.forEach(([li], k) => li.classList.toggle('on', k === on && f > 0));
    play.textContent = timer ? D.cl.an_pause : D.cl.an_play;
  };
  const tick = () => { if (f >= frames.length - 1) { stop(); return; } go(f + 1); timer = setTimeout(tick, SPEEDS[speed] * (frames[f].hold || 1)); };
  const stop = () => { clearTimeout(timer); timer = null; if (frames.length) play.textContent = D.cl.an_play; };
  const start = () => { stop(); if (f >= frames.length - 1) go(0); timer = setTimeout(tick, SPEEDS[speed] * (frames[f].hold || 1)); play.textContent = D.cl.an_pause; };
  const btn = (t, fn, cls) => { const b = el('button', cls, t); b.type = 'button'; b.onclick = fn; nav.append(b); return b; };
  btn(D.cl.bo_first, () => { stop(); go(0); });
  btn(D.cl.bo_prev, () => { stop(); go(f - 1); });
  const play = btn(D.cl.an_play, () => timer ? stop() : start(), 'an-play');
  btn(D.cl.bo_next, () => { stop(); go(f + 1); });
  btn(D.cl.bo_last, () => { stop(); go(frames.length - 1); });
  const sp = el('div', 'an-sp'); sp.append(el('span', 'muted sm', D.cl.an_speed));
  [D.cl.an_slow, D.cl.an_mid, D.cl.an_fast].forEach((t, k) => { const b = el('button', null, t); b.type = 'button';
    b.setAttribute('aria-pressed', k === speed); b.onclick = () => { speed = k; for (const o of sp.querySelectorAll('button')) o.setAttribute('aria-pressed', o === b); }; sp.append(b); });
  seek.oninput = () => { stop(); go(+seek.value); };
  const setVar = k => {
    vi = k; stop(); build(); seek.max = frames.length - 1;
    for (const [b, i] of vbtns) b.setAttribute('aria-pressed', i === k);
    deal.textContent = vars[k] ? lf + vars[k][2] : '';
  };
  const vbtns = vars.map(([t], k) => { const b = el('button', null, t); b.type = 'button'; b.onclick = () => { setVar(k); go(0); start(); }; vbar.append(b); return [b, k]; });
  if (vars.length < 2) vbar.hidden = true;
  side.append(nav, seek, sp, list);
  wrap.append(el('div', 'an-l', null), side); wrap.firstChild.append(pic, cap);
  panel.append(vbar, deal, wrap, el('p', 'muted sm', D.cl.bo_note));
  if (!vars.length) panel.append(el('p', 'muted sm', D.cl.bo_none));
  else if (!e.b3) panel.append(el('p', 'muted sm', D.cl.pcx_none3));
  setVar(0);
  // the same PCs as numbered pictures, folded
  if (vars.length) {
    const det = el('details', 'an-st'); det.append(el('summary', null, D.cl.an_static));
    const pcx = el('div', 'pcxb');
    for (const [title, ex, dl] of vars) {
      const [, h, placed, steps] = ex, cells = new Map();
      e.r.forEach((row, y) => { for (let x = 0; x < 10; x++) if (row >> x & 1) cells.set(y * 10 + x, { fill: '#8a8f9c' }); });
      for (const [x, y, p, n] of placed) cells.set(y * 10 + x, { fill: COL[p], n });
      const fg = el('figure'), fc = el('figcaption'); fc.append(el('b', null, title), ' · ' + lf + dl); fg.append(fc, board(h, cells, 16));
      const ol = el('ol', 'steps');
      for (const [p, , hd] of steps) { const li = el('li'); const b = el('b', null, p); b.style.color = COL[p]; li.append(b); if (hd) li.append(D.cl.pcx_hold); ol.append(li); }
      fg.append(ol); pcx.append(fg);
    }
    det.append(pcx); panel.append(det);
  }
  go(0);
  if (panel.scrollIntoView) requestAnimationFrame(() => panel.scrollIntoView({ block: 'nearest', behavior: REDUCE ? 'auto' : 'smooth' }));
  if (!REDUCE) start();
  panel._stop = stop;
}
function apply() {
  for (const card of document.querySelectorAll('.card')) {
    const id = card.dataset.card, c = D.cards[id];
    card.classList.toggle('hide', (pos !== 'all' && card.dataset.pos !== pos) || (kind !== 'all' && card.dataset.kind !== kind));
    card.style.order = c.o[sd];
    card.dataset.rk = c.rk[sd];
    card.querySelector('.rk').textContent = c.rk[sd];
    card.querySelector('[data-cnt]').textContent = c.cnt[sd];
    card.querySelector('[data-f="two"]').textContent = c.f[sd][0];
    card.querySelector('[data-f="pc3"]').textContent = c.f[sd][1];
    card.querySelector('[data-f="joint"]').textContent = c.f[sd][2];
    card.querySelector('[data-f="tsd"]').textContent = c.ft[sd][0];
    card.querySelector('[data-f="tsdj"]').textContent = c.ft[sd][1];
  }
  for (const b of posBtns) b.setAttribute('aria-pressed', b.dataset.f === pos);
  for (const b of kindBtns) b.setAttribute('aria-pressed', b.dataset.k === kind);
  for (const b of sdBtns) b.setAttribute('aria-pressed', b.dataset.b === sd);
  for (const e of document.querySelectorAll('[data-fl]')) e.hidden = e.dataset.fl !== sd;
}
posBtns.forEach(b => b.onclick = () => { pos = b.dataset.f; apply(); });
kindBtns.forEach(b => b.onclick = () => { kind = b.dataset.k; apply(); });
sdBtns.forEach(b => b.onclick = () => { sd = b.dataset.b; apply(); });
// A link to a card the filters hide resets both filters, then scrolls to it.
function reveal() {
  const m = /^#(c[\w]+)$/.exec(location.hash);
  const el = m && document.getElementById(m[1]);
  if (!el || !el.classList.contains('card')) return;
  if (el.classList.contains('hide')) { pos = 'all'; kind = 'all'; apply(); }
  if (el.scrollIntoView) el.scrollIntoView({ block: 'start' });
}
window.addEventListener('hashchange', reveal);
apply();
reveal();
