// 學邊幾個: shows the block of the soft-drop budget the page's bar has pressed, and looks up which of the best three boards
// to pick for a first bag. Reads #sdata only; builds nodes, assigns no markup.
(function () {
  const S = JSON.parse(document.getElementById('sdata').textContent);
  const bar = [...document.querySelectorAll('.bar[data-bar="sd"] button')];
  const blocks = [...document.querySelectorAll('.sx-bk')];
  const pb = [...document.querySelectorAll('.sx-pb button[data-p]')];
  const seqEl = document.querySelector('.sx-seq'), outEl = document.querySelector('.sx-out');
  const FACT = [1, 1, 2, 6, 24, 120, 720];
  const kbs = [...document.querySelectorAll('.sx-kb button[data-k]')];
  let chosen = [], ok = true, kk = S.k0;
  const budget = () => {
    const p = bar.find(b => b.getAttribute('aria-pressed') === 'true');
    return p ? p.dataset.b : S.shown;
  };
  const idx = perm => {
    const rest = S.ord.split('');
    let n = 0;
    for (let i = 0; i < 7; i++) {
      const j = rest.indexOf(perm[i]);
      n += j * FACT[6 - i];
      rest.splice(j, 1);
    }
    return n;
  };
  const el = (tag, cls, txt) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt !== undefined) e.textContent = txt;
    return e;
  };
  const fmt = (s, o) => s.replace(/\{(\w+)\}/g, (_m, k) => o[k]);
  // the order index must be the counter's recursion rank: check the pinned fixtures and the table lengths
  for (const [perm, i] of S.fix) if (idx(perm) !== i) ok = false;
  for (const k of S.bk) for (const j of S.ks) if (S.p[k][j].length !== 5040) ok = false;
  const NS = 'http://www.w3.org/2000/svg';
  const sv = (tag, at) => {
    const e = document.createElementNS(NS, tag);
    for (const k in at) e.setAttribute(k, at[k]);
    return e;
  };
  // a mini board of one board's pieces, the way the section's figures draw it (nodes only)
  function pic(n) {
    const cells = [];
    let H = 4;
    for (const [k, cs] of S.bd[n].c) for (const c of cs) { cells.push([c % 10, Math.floor(c / 10), k]); H = Math.max(H, Math.floor(c / 10) + 1); }
    const cs = 12, svg = sv('svg', { class: 'board', width: 10 * cs, height: H * cs, viewBox: '0 0 ' + 10 * cs + ' ' + H * cs, role: 'img', 'aria-label': S.lb[n] });
    svg.appendChild(sv('rect', { width: 10 * cs, height: H * cs, fill: 'var(--well)' }));
    for (let x = 0; x < 10; x++) for (let y = 0; y < H; y++)
      svg.appendChild(sv('rect', { x: x * cs + .5, y: (H - 1 - y) * cs + .5, width: cs - 1, height: cs - 1, fill: 'var(--grid)' }));
    for (const [x, y, k] of cells)
      svg.appendChild(sv('rect', { x: x * cs + .5, y: (H - 1 - y) * cs + .5, width: cs - 1, height: cs - 1, fill: S.col[k.toUpperCase()] || '#8a8f9c' }));
    return svg;
  }
  function link(n) {
    const l = S.lk[n], d = el('div', 'sx-lnk');
    if (!l) { d.textContent = S.t.no_card; return d; }
    const a = el('a', null, S.t.to_card);
    a.href = '#c' + l[1];
    d.appendChild(a);
    if (l[0] === 'm') d.appendChild(document.createTextNode(' ' + fmt(S.t.mirror_card, { m: S.lb[l[1]] })));
    return d;
  }
  function lookup() {
    const bk = budget();
    outEl.replaceChildren();
    if (!ok) { outEl.appendChild(el('p', 'sx-fail', S.t.lk_fail)); return; }
    if (chosen.length < 7) return;
    const o = idx(chosen.join('')), c = S.p[bk][kk][o], pick = c === 'x' ? -1 : +c;
    if (pick < 0) outEl.appendChild(el('p', null, fmt(S.t.lk_nopick, { k: kk })));
    S.m[bk][kk].forEach((n, i) => {
      const card = el('div', 'sx-o' + (i === pick ? ' on' : ' dim'));
      const cost = S.bd[n].v[o];
      const head = el('b', null, i === pick ? fmt(S.t.lk_pick, { n: S.lb[n] }) : S.lb[n]);
      card.appendChild(head);
      card.appendChild(document.createTextNode(' '));
      card.appendChild(el('span', 'sx-id', n));
      if (i === pick) card.appendChild(pic(n));
      const f = cost === '.' ? null : S.f[bk][n][+cost];
      if (f) {
        card.appendChild(el('div', null, fmt(S.t.lk_cost, { s: cost })));
        card.appendChild(el('div', null, fmt(S.t.lk_fig, { b: f[0], j: f[1] })));
      } else card.appendChild(el('div', null, S.t.lk_unbuildable));
      if (i === pick) card.appendChild(link(n));
      outEl.appendChild(card);
    });
  }
  function draw() {
    seqEl.replaceChildren(el('span', 'muted sm', S.t.lk_seq + ' '));
    if (!chosen.length) seqEl.appendChild(el('span', 'muted sm', S.t.lk_none_yet));
    for (const k of chosen) seqEl.appendChild(el('i', 'chip c-' + k, k));
    for (const b of pb) if (b.dataset.p !== 'reset') b.disabled = !ok || chosen.includes(b.dataset.p);
    lookup();
  }
  function push(k) {
    if (chosen.includes(k) || chosen.length >= 7) return;
    chosen.push(k);
    if (chosen.length === 6) chosen.push(S.ord.split('').find(x => !chosen.includes(x)));
    draw();
  }
  for (const b of kbs) b.onclick = () => {
    kk = b.dataset.k;
    for (const x of kbs) x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
    lookup();
  };
  for (const b of pb) b.onclick = () => { if (b.dataset.p === 'reset') { chosen = []; draw(); } else push(b.dataset.p); };
  const show = () => {
    const bk = budget();
    for (const e of blocks) e.hidden = e.dataset.bk !== bk;
    lookup();
  };
  for (const b of bar) b.addEventListener('click', () => setTimeout(show, 0));
  draw();
  show();
})();
