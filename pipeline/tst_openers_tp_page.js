const D = JSON.parse(document.getElementById('data').textContent);
const COL = { I: '#2fb8c9', O: '#e3b425', T: '#9a46d6', S: '#4cb648', Z: '#d9433d', J: '#3b61d6', L: '#e5792a' };
const NS = 'http://www.w3.org/2000/svg';
const sdBtns = [...document.querySelectorAll('.bar[data-bar="sd"] button')];
const posBtns = [...document.querySelectorAll('.bar[data-bar="pos"] button')];
const lab = {};
for (const b of sdBtns) lab[b.dataset.b] = b.textContent;
let sd = D.sd_default, pos = D.filter_default;
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
function board(H, cells, cs) {
  const sv = document.createElementNS(NS, 'svg');
  sv.setAttribute('width', 10 * cs); sv.setAttribute('height', H * cs); sv.classList.add('board');
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
  return sv;
}
function showBuild(panel, c, j) {
  panel.replaceChildren();
  if (!c.b[j]) { panel.append(el('p', 'muted sm', D.cl.bo_nobuild)); return; }
  const [order, sd] = c.b[j], [tst, line, a3] = c.x[j], n1 = c.n1, m = order.length + 1;
  let H = 1; for (const [, cs] of order) for (const q of cs) H = Math.max(H, Math.floor(q / 10) + 1);
  for (const q of tst) H = Math.max(H, Math.floor(q / 10) + 1);
  panel.append(el('h4', null, D.cl.bo_title), el('p', 'muted sm', D.cl.bo_note));
  const wrap = el('div', 'bo-w'), side = el('div', 'bo-s'), pic = el('div'), cap = el('p', 'sm');
  const nav = el('div', 'bo-nav'), list = el('ol', 'bo-l');
  let s = m;
  const lis = [];
  const draw = () => {
    const cells = new Map();
    order.forEach(([k, cs], i) => { if (i < s) for (const q of cs) cells.set(q, { fill: COL[k], n: i + 1, cur: i === s - 1, op: i < n1 ? null : .85 }); });
    for (const q of tst) cells.set(q, s === m ? { fill: COL.T, n: m, cur: true } : { dash: true });
    pic.replaceChildren(board(H, cells, 18));
    cap.textContent = D.cl.bo_step.replace('{n}', s).replace('{m}', m) + (s === 0 ? '' : ' · ' + (s === m ? D.cl.bo_tst : order[s - 1][0] + (order[s - 1][2] ? ' ' + D.cl.bo_sd : '')));
    lis.forEach((li, i) => li.classList.toggle('on', i === s - 1));
  };
  for (const [lab, f] of [[D.cl.bo_first, () => 0], [D.cl.bo_prev, () => Math.max(0, s - 1)], [D.cl.bo_next, () => Math.min(m, s + 1)], [D.cl.bo_last, () => m]]) {
    const b = el('button', null, lab); b.type = 'button'; b.onclick = () => { s = f(); draw(); }; nav.append(b);
  }
  const item = (i, txt, color, extra) => {
    const li = el('li'); const b = el('button'); b.type = 'button';
    const k = el('b', null, txt); if (color) k.style.color = color; b.append(k); if (extra) b.append(' ' + extra);
    b.onclick = () => { s = i + 1; draw(); }; li.append(b); lis.push(li); return li;
  };
  list.append(el('li', 'bo-g', D.cl.bo_b1));
  order.forEach(([k, , d], i) => { if (i === n1) list.append(el('li', 'bo-g', D.cl.bo_rest)); list.append(item(i, k, COL[k], d ? D.cl.bo_sd : '')); });
  list.append(el('li', 'bo-g', D.cl.bo_tst)); list.append(item(order.length, 'T', COL.T, ''));
  side.append(nav, cap, list); wrap.append(pic, side); panel.append(wrap);
  draw();
  // the worked PC
  panel.append(el('h4', null, D.cl.bo_pc));
  const e = D.px[line];
  if (!e || (!e.b3 && !e.b4)) { panel.append(el('p', 'muted sm', D.cl.bo_none)); return; }
  panel.append(el('p', 'muted sm', D.cl.bo_pc_note));
  const lf = e.l ? D.cl.pcx_left.replace('{left}', e.l) : '';
  const pcx = el('div', 'pcxb');
  const fig = (ex, title, dl) => {
    const [d, h, placed, steps] = ex, cells = new Map();
    e.r.forEach((row, y) => { for (let x = 0; x < 10; x++) if (row >> x & 1) cells.set(y * 10 + x, { fill: '#8a8f9c' }); });
    for (const [x, y, p, n] of placed) cells.set(y * 10 + x, { fill: COL[p], n });
    const f = el('figure'), fc = el('figcaption'); fc.append(el('b', null, title), ' · ' + dl); f.append(fc, board(h, cells, 16));
    const ol = el('ol', 'steps');
    for (const [p, , hd] of steps) { const li = el('li'); const b = el('b', null, p); b.style.color = COL[p]; li.append(b); if (hd) li.append(D.cl.pcx_hold); ol.append(li); }
    f.append(ol); return f;
  };
  if (e.b3) pcx.append(fig(e.b3, D.cl.pcx_b3, lf + D.cl.pcx_deal3.replace('{d}', e.b3[0][0]))); else pcx.append(el('p', 'muted sm', D.cl.pcx_none3));
  if (a3) pcx.append(el('p', 'muted sm', D.cl.pcx_always3));
  else if (e.b4) pcx.append(fig(e.b4, D.cl.pcx_b4, lf + D.cl.pcx_deal34.replace('{d3}', e.b4[0][0]).replace('{d4}', e.b4[0][1])));
  else pcx.append(el('p', 'muted sm', D.cl.pcx_none4));
  panel.append(pcx);
}
function apply() {
  for (const card of document.querySelectorAll('.card')) {
    const id = card.dataset.card, c = D.cards[id];
    card.classList.toggle('hide', pos !== 'all' && card.dataset.pos !== pos);
    card.style.order = c.o[sd];
    card.dataset.rk = c.rk[sd];
    card.querySelector('.rk').textContent = c.rk[sd];
    card.querySelector('[data-cnt]').textContent = c.cnt[sd];
    card.querySelector('[data-f="two"]').textContent = c.f[sd][0];
    card.querySelector('[data-f="pc3"]').textContent = c.f[sd][1];
    card.querySelector('[data-f="joint"]').textContent = c.f[sd][2];
  }
  for (const b of posBtns) b.setAttribute('aria-pressed', b.dataset.f === pos);
  for (const b of sdBtns) b.setAttribute('aria-pressed', b.dataset.b === sd);
}
posBtns.forEach(b => b.onclick = () => { pos = b.dataset.f; apply(); });
sdBtns.forEach(b => b.onclick = () => { sd = b.dataset.b; apply(); });
apply();
