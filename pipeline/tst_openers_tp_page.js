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
  for (const [g, name, left, p5, ...ds] of c.t) {
    const f = document.createElement('figure');
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
