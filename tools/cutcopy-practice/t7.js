const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'] });
  const pg = await ctx.newPage(); pg.setDefaultTimeout(3000); const errs = []; pg.on('pageerror', e => errs.push(e.message));
  const html = require('fs').readFileSync('cc-test.html', 'utf8');
  await pg.setContent('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + html + '</body></html>');
  const D = require('./drills.json'); const P = require('./paths.json'); const R=['易','中','難','極難']; const SORTED = D.slice().sort((a,b)=>R.indexOf(a.diff)-R.indexOf(b.diff)||a.need-b.need);
  async function drop(s) {
    const cur = await pg.evaluate(() => document.querySelector('#status') && window.__cur && window.__cur());
    for (let k = 0; k < s.r; k++) await pg.click('.pad [data-a="cw"]');
    const pos = await pg.evaluate(([s]) => {
      const E = CCE, bc = document.getElementById('board'), rect = bc.getBoundingClientRect(), CS = rect.width / 10;
      const top = CC_STATE.vis0();
      const cells = E.cellsOf(s.piece, s.x, s.y, s.r); const xs = cells.map(c => c[0]), ys = cells.map(c => c[1]);
      const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
      return { x: rect.left + (minx + (maxx - minx + 1) / 2) * CS, y: rect.top + ((miny - top) + (maxy - miny + 1) + 1) * CS };
    }, [s]);
    await pg.evaluate(({ x, y }) => { const bc = document.getElementById('board');
      const ev = (t, X, Y) => bc.dispatchEvent(new PointerEvent(t, { clientX: X, clientY: Y, pointerId: 1, pointerType: 'touch', bubbles: true }));
      ev('pointerdown', x, y - 60); ev('pointermove', x, y - 30); ev('pointermove', x, y); ev('pointerup', x, y); }, pos);
    await pg.waitForTimeout(80);
  }
  const rows = [];
  for (const pz of SORTED) {
    console.log('start', pz.id); await pg.selectOption('#psel', String(SORTED.indexOf(pz)));
    await pg.waitForTimeout(100);
    const path = P[pz.id]; let passedAt = null; const log = [];
    for (let i = 0; i < path.length; i++) {
      const s = path[i];
      let curP = await pg.evaluate(() => document.querySelector('#dcap') && CC_STATE.piece());
      if (curP !== s.piece) { await pg.click('.pad [data-a="hold"]'); curP = await pg.evaluate(() => CC_STATE.piece()); log.push('hold'); }
      if (curP !== s.piece) { log.push(`want ${s.piece} got ${curP}`); break; }
      await drop(s); log.push(s.piece);
      const st = await pg.textContent('#status');
      if (st.startsWith('✓')) { passedAt = i + 1; break; }
      if (await pg.evaluate(() => CC_STATE.failed())) { log.push('FAILED ' + st.slice(0, 30)); break; }
    }
    const locks = await pg.evaluate(() => CC_STATE.locks());
    await pg.locator('#board').screenshot({ path: `solved/${SORTED.indexOf(pz)}.png` });
    rows.push({ i: SORTED.indexOf(pz), id: pz.id, diff: pz.diff, min: pz.min, need: pz.need, planned: path.length, passedAt, locks, log: log.join(' ') });
    console.log(JSON.stringify(rows[rows.length - 1]));
    // demo + target checks
    await pg.click('#reset').catch(()=>{});
    await pg.click('#hint'); await pg.waitForTimeout(100);
    await pg.locator('#board').screenshot({ path: `solved/${SORTED.indexOf(pz)}-hint.png` });
    await pg.click('#hint').catch(()=>{});
    await pg.click('#demoBtn').catch(e=>console.log('demo click', e.message.slice(0,80))); await pg.waitForTimeout(7000);
    await pg.locator('#board').screenshot({ path: `solved/${SORTED.indexOf(pz)}-demo.png` });
    rows[rows.length-1].demoCap = (await pg.textContent('#dcap').catch(()=>'')).slice(0,80);
    console.log('demo', rows[rows.length-1].demoCap);
    await pg.click('#demoBtn').catch(()=>{}); await pg.click('#reset').catch(()=>{});
  }
  require('fs').writeFileSync('solved/rows.json', JSON.stringify(rows));
  console.log('errs', errs); await b.close();
})();
