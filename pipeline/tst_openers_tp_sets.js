// 學邊幾個: shows the block of the soft-drop budget the page's bar has pressed, and looks up which of the best three boards
// to pick for a first bag. Reads #sdata only; builds nodes, assigns no markup.
(function () {
  const S = JSON.parse(document.getElementById('sdata').textContent);
  const bar = [...document.querySelectorAll('.bar[data-bar="sd"] button')];
  const blocks = [...document.querySelectorAll('.sx-bk')];
  const pb = [...document.querySelectorAll('.sx-pb button[data-p]')];
  const seqEl = document.querySelector('.sx-seq'), outEl = document.querySelector('.sx-out');
  const FACT = [1, 1, 2, 6, 24, 120, 720];
  let chosen = [], ok = true;
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
  for (const k of S.bk) if (S.p[k].length !== 5040) ok = false;
  function lookup() {
    const bk = budget();
    outEl.replaceChildren();
    if (!ok) { outEl.appendChild(el('p', 'sx-fail', S.t.lk_fail)); return; }
    if (chosen.length < 7) return;
    const o = idx(chosen.join('')), c = S.p[bk][o], pick = c === 'x' ? -1 : +c;
    if (pick < 0) outEl.appendChild(el('p', null, S.t.lk_nopick));
    S.m[bk].forEach((n, i) => {
      const card = el('div', 'sx-o' + (i === pick ? ' on' : ' dim'));
      const cost = S.bd[n].v[o];
      card.appendChild(el('b', null, n + (i === pick ? ' · ' + fmt(S.t.lk_pick, { n }) : '')));
      const f = cost === '.' ? null : S.f[bk][n][+cost];
      if (f) {
        card.appendChild(el('div', null, fmt(S.t.lk_cost, { s: cost })));
        card.appendChild(el('div', null, fmt(S.t.lk_fig, { b: f[0], j: f[1] })));
      } else card.appendChild(el('div', null, S.t.lk_unbuildable));
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
