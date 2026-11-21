const D = JSON.parse(document.getElementById('data').textContent);
const COL = { I: '#2fb8c9', O: '#e3b425', T: '#9a46d6', S: '#4cb648', Z: '#d9433d', J: '#3b61d6', L: '#e5792a' };
const NS = 'http://www.w3.org/2000/svg';
function mini(g, tst) {
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
  for (let i = 0; i < g.length; i++) { const k = g[i]; r(i % 10, Math.floor(i / 10), COL[k] || 'var(--grid)'); }
  for (const [x, y] of tst) r(x, H - 1 - y, 'none', { stroke: '#c77dff', 'stroke-width': 1.5, 'stroke-dasharray': '2 2' });
  return sv;
}
// Every figure is precomputed by the renderer (floored); this script only draws them.
for (const d of document.querySelectorAll('details[data-s]')) d.addEventListener('toggle', () => {
  const box = d.querySelector('.tl');
  if (!d.open || box.childElementCount) return;
  const s = D.shapes[d.dataset.s];
  for (const [g, two, pc3, pc4, joint, left] of s.t) {
    const f = document.createElement('figure');
    f.appendChild(mini(g, s.tst));
    const c = document.createElement('figcaption');
    [[D.labels[0], two], [D.labels[1], pc3], [D.labels[2], pc4], [D.labels[3], joint]].forEach(([a, b]) => {
      c.append(a + ' ');
      const e = document.createElement('b'); e.textContent = b; c.append(e, ' ');
    });
    if (left) c.append(D.labels[4] + left);
    f.appendChild(c); box.appendChild(f);
  }
});
const bs = [...document.querySelectorAll('.bar button')];
function f(v) {
  for (const c of document.querySelectorAll('.card')) c.classList.toggle('hide', v !== 'all' && c.dataset.pos !== v);
  for (const b of bs) b.setAttribute('aria-pressed', b.dataset.f === v);
}
bs.forEach(b => b.onclick = () => f(b.dataset.f));
f(D.filter_default);
