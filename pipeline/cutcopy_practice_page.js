// 千鳥格子練習場's page script (docs/practice-cutcopy.html). It plays the CONSTRUCTED practice drills of
// analysis/cutcopy-drills.json, inlined as the data island #cc-drills, through the inlined practice engine
// (pipeline/cutcopy_practice_engine.js). The windows the engine fires are the artefact's own, which are
// technique-facts.ts's prepare() output: nothing here types a window. Rendered by
// pipeline/cutcopy_practice_page.py, which audits the page; no figure on it is a corpus measurement.
(function(){
const E = CCE, ART = JSON.parse(document.getElementById("cc-drills").textContent);
E.setWindows(ART.windows);
const DORDER = ["易", "中", "難", "極難"], dlab = pz => pz.difficulty.label, dmin = pz => pz.difficulty.min;
const PZ = ART.drills.slice().sort((a, b) => DORDER.indexOf(dlab(a)) - DORDER.indexOf(dlab(b)) || a.need - b.need);
let VIS0 = 18, VROWS = 22;
const $ = id => document.getElementById(id);
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const VLAB = { cutcopy: "基本形", uncut: "Uncut" };
const store = { get(k){ try { return JSON.parse(localStorage.getItem(k)); } catch(e){ return null; } }, set(k,v){ try { localStorage.setItem(k, JSON.stringify(v)); } catch(e){} } };
let solved = new Set(store.get("practice-cutcopy-solved") || []);

function info(pz){
  const k = pz.kind, so = pz.source, t = pz.target;
  const tv = `${VLAB[t.variant]}${t.mirrored ? "（鏡像）" : ""}`;
  const DG = { "易": "易 · 1–2 粒就砌到", "中": "中 · 最少 3 粒", "難": "難 · 最少 4 粒", "極難": "極難 · 要 4 粒以上" };
  const group = DG[dlab(pz)] || DG["極難"];
  const name = k === "page" ? pz.title : k === "corpus" ? `${so.session.slice(5)} 第${so.match}場第${so.round}局` : k === "selfplay" ? `cold-clear 局${so.seed}` : "空板起";
  const title = name + (dmin(pz) != null ? `（最少 ${dmin(pz)} 粒）` : "（4 粒以上）") + (pz.need !== dmin(pz) ? `・原本 ${pz.need} 粒` : "");
  let note = (k === "page" ? (pz.note || "") + " " : k === "corpus" ? `${so.player} 喺 ${so.session} 真係砌過嘅盤面，倒返 ${pz.need} 粒。` : k === "selfplay" ? `cold-clear 自己玩（冇垃圾行）嘅盤面，倒返 ${pz.need} 粒。` : "我哋自己設計、由空板開始嘅盤面。")
    + `原本係用 ${pz.need} 粒砌成${tv}。你用自己方法砌都得，只要個形砌好到 T 一嚟就打得千鳥格子嘅 TSD（第二槽嘅蓋要先擺好）就過關，唔使等 T，T 亦唔使打。`;
  if (pz.skippedTetris) note += " 原本中間有一下 Tetris，已經幫你打咗，由 Tetris 之後開始。";
  if (pz.queue.slice(0, pz.need).includes("T")) note += " 呢段入面有 T，可以拎嚟砌，或者 Hold 住。";
  for (const e of mergeEv(pz.events)) if (e.before <= pz.need) note += ` 第 ${e.before} 粒落完之後會入 ${e.n} 行垃圾（窿喺第 ${e.col + 1} 列）。`;
  return { group, title, note };
}

function mergeEv(evs){ const o = []; for (const e of evs || []) { const l = o[o.length - 1]; if (l && l.before === e.before && l.col === e.col) l.n += e.n; else o.push({ ...e }); } return o; }
const GROUPS = ["易 · 1–2 粒就砌到", "中 · 最少 3 粒", "難 · 最少 4 粒", "極難 · 要 4 粒以上"];
// ---- picker
const groups = {};
PZ.forEach((pz, i) => { const f = info(pz); (groups[f.group] = groups[f.group] || []).push([i, f]); });
const picker = $("picker");
for (const g of GROUPS) {
  if (!groups[g]) continue;
  const div = document.createElement("div"); div.className = "grp";
  const lab = document.createElement("span"); lab.textContent = g; div.appendChild(lab);
  for (const [i, f] of groups[g]) { const b = document.createElement("button"); b.className = "pz"; b.textContent = f.title; b.dataset.i = i; b.addEventListener("click", () => load(i)); div.appendChild(b); }
  picker.appendChild(div);
}
const psel = $("psel");
for (const g of GROUPS) { if (!groups[g]) continue; const og = document.createElement("optgroup"); og.label = g;
  for (const [i, f] of groups[g]) { const o = document.createElement("option"); o.value = i; o.textContent = f.title; og.appendChild(o); } psel.appendChild(og); }
psel.addEventListener("change", () => load(+psel.value));
function markPicker(){ psel.value = String(cur); for (const o of psel.querySelectorAll("option")) o.textContent = info(PZ[+o.value]).title + (solved.has(PZ[+o.value].id) ? " ✓" : ""); for (const b of picker.querySelectorAll(".pz")) { const i = +b.dataset.i; b.setAttribute("aria-current", i === cur ? "true" : "false"); b.classList.toggle("solved", solved.has(PZ[i].id)); } }

// ---- state
let dragMode = false, orient = 0, drag = null, cands = null, run = null;
let cur = 0, pz, piece, hist, hintOn = false, lastCells = null, demo = null, msgs = [];
function cloneRun(r){ return JSON.parse(JSON.stringify(r)); }
function spawnNext(){
  if (!run.queue.length) { piece = null; return; }
  const p = run.queue.shift(); piece = E.spawn(run.board, p); orient = 0; cands = null;
  if (!piece) { run.failed = "topout"; }
}
function load(i){
  cur = i; pz = PZ[i]; store.set("practice-cutcopy-last", i);
  run = E.newRun(pz); hist = []; built = null; clearInterval(autoTimer); lastCells = null; msgs = []; hintOn = false; exitDemo(false);
  spawnNext();
  const f = info(pz); $("ptitle").textContent = f.title; $("pnote").textContent = f.note;
  markPicker(); say(); sizeBoard(); draw();
}
function snapshot(){ hist.push({ run: cloneRun(run), piece: piece && { ...piece }, lastCells, msgs: msgs.slice() }); }
function undo(){ if (demo && demo.auto) exitDemo(false); if (demo) return; const h = hist.pop(); if (!h) return; built = null; clearInterval(autoTimer); run = h.run; piece = h.piece; orient = 0; cands = null; drag = null; lastCells = h.lastCells; msgs = h.msgs; say(); draw(); }

const LINE = ["", "Single", "Double", "Triple", "Quad"];
function spinLabel(fb){
  if (fb.spin === "full" && fb.piece === "T") return `T-spin ${LINE[fb.lines] || "（冇清行）"}`.replace("T-spin （冇清行）", "T-spin（冇清行）");
  if (fb.spin === "mini" && fb.piece === "T") return `T-spin Mini${fb.lines ? " " + LINE[fb.lines] : ""}`;
  return fb.lines ? `清 ${fb.lines} 行` : "";
}
const MSG = {
  first: () => "呢粒 T 打中咗千鳥格子嘅 TSD。",
  second: () => "兩粒 TSD 都打晒，千鳥格子完成！",
  notfull: () => "T 擺啱咗位，但唔係完整 TSD（變咗 mini 或者冇清夠兩行）。試下用轉嚟入槽，唔好直接放落去。",
  nowindow: () => "呢粒 T 唔係打喺千鳥格子嘅位：打完之後下面冇第二個槽留低，或者槽外嗰格蓋未擺好。",
  t_noclear: () => "T 擺落去冇清行。呢題第一粒 T 要打 TSD。",
  second_notfull: () => "第二粒 T 入咗槽，但冇算到完整 TSD。",
  second_wrong: () => "第二粒 T 冇打入黃色虛線嗰個槽。",
  slot_filled: () => "呢粒塞住咗第二個槽。",
  slot_cleared: () => "清行清走咗第二個槽嘅一部份，個槽冇咗。",
  topout: () => "方塊出唔到嚟（頂咗上去）。",
  empty: () => "方塊用晒，個形未砌好。",
  budget: () => `用咗 ${run.locks} 粒（原本 ${pz.need} 粒）都未砌到。紅框係實戰個形仲欠嘅格，紅交叉係應該留空但塞咗嘅格。撳「上一步」改，或者撳「示範」睇原本點砌。`,
};
function hard(){
  if (demo || !piece || run.done || run.failed) return;
  commit(E.dropped(run.board, piece), null);
}
function commit(st, path){
  snapshot();
  const fb = E.applyLock(run, pz, st);
  lastCells = null;
  const lab = spinLabel(fb);
  let text = `${fb.piece}${path ? "（" + path.join(" ") + "）" : ""}${lab ? "：" + lab : ""}`;
  if (fb.msg) text += " — " + MSG[fb.msg]();
  msgs.push({ text, good: fb.good });
  run.holdUsed = false;
  if (fb.msg === "first") { run.done = true; built = { player: true }; msgs.push({ text: "你用咗粒 T 打埋落去，不過個形本身係啱嘅。下次 T 可以留低，淨係砌形就得。", good: true }); }
  if (!run.done && !run.failed) { spawnNext(); if (!piece && !run.failed) run.failed = "empty"; if (run.failed === "topout" || run.failed === "empty") msgs.push({ text: MSG[run.failed](), good: false }); }
  if (!run.done && !run.failed) checkBuilt();
  if (run.done) { solved.add(pz.id); store.set("practice-cutcopy-solved", [...solved]); markPicker(); }
  say(); draw();
}
let built = null, autoTimer = null;
function tAvail(){ return (piece && piece.p === "T") || run.hold === "T" || run.queue.slice(0, 5).includes("T"); }
function checkBuilt(){
  const b = E.findBuild(run.board);
  if (b) {
    run.done = true; built = b;
    msgs.push({ text: `✓ 形砌好咗！用咗 ${run.locks} 粒（原本 ${pz.need} 粒）。係${VLAB[b.m.variant]}${b.m.mirrored ? "（鏡像）" : ""}。${tAvail() ? "" : "（下面 5 粒未有 T，實戰要等 T 先打得。）"}`, good: true });
    return;
  }
  if (run.locks >= pz.need + 2) { run.failed = "budget"; msgs.push({ text: MSG.budget(), good: false }); }
}
function autoPlay(){
  if (!built || !built.state) return;
  const frames = [], r = cloneRun(run); r.done = false;
  frames.push({ board: E.cloneBoard(r.board), slot: null, piece: built.state, queue: [], cap: `你砌好嘅形。T 自動打第一粒 TSD（${built.path.join(" ")}）`, path: [] });
  E.applyLock(r, pz, built.state);
  frames.push({ board: E.cloneBoard(r.board), slot: r.slot && r.slot.map(c => c.slice()), piece: null, queue: [], cap: "清咗兩行，黃色虛線係下面露出嚟嘅第二個 TSD 槽。" });
  const sec = r.slot && E.findSecond(r.board, r.slot);
  if (sec) {
    frames.push({ board: E.cloneBoard(r.board), slot: r.slot.map(c => c.slice()), piece: sec.state, queue: [], cap: `第二粒 T 即刻打得入（${sec.path.join(" ")}）` });
    E.applyLock(r, pz, sec.state);
    frames.push({ board: E.cloneBoard(r.board), slot: null, piece: null, queue: [], cap: "兩粒 TSD 打晒，千鳥格子完成。" });
  } else frames[1].cap += "呢個盤面要先喺上面封頂，第二粒 T 先轉得入。";
  demo = { frames, i: 0, auto: true }; $("demo").classList.add("on"); $("demoBtn").disabled = true; $("pad").style.opacity = .5; showDemo();
  clearInterval(autoTimer); autoTimer = setInterval(() => { if (!demo || !demo.auto || demo.i >= demo.frames.length - 1) { clearInterval(autoTimer); return; } demo.i++; showDemo(); }, 1100);
}
function act(a){
  if (a === "undo") return undo();
  if (demo) { if (a === "left") step(-1); else if (a === "right") step(1); return; }
  if (dragMode && piece && !run.done && !run.failed && (a === "cw" || a === "ccw" || a === "180")) { orient = (orient + (a === "cw" ? 1 : a === "ccw" ? 3 : 2)) % 4; draw(); return; }
  if (dragMode && a !== "hold") return;
  if (!piece || run.done || run.failed) return;
  const b = run.board; let n = null;
  if (a === "left") n = E.shift(b, piece, -1);
  else if (a === "right") n = E.shift(b, piece, 1);
  else if (a === "soft") n = E.down(b, piece);
  else if (a === "cw") n = E.rotate(b, piece, 1);
  else if (a === "ccw") n = E.rotate(b, piece, -1);
  else if (a === "180") n = E.rotate(b, piece, 2);
  else if (a === "hard") return hard();
  else if (a === "hold") {
    if (run.holdUsed) return; snapshot();
    if (run.hold === null) { run.hold = piece.p; spawnNext(); }
    else { const t = run.hold; run.hold = piece.p; piece = E.spawn(run.board, t); orient = 0; cands = null; }
    run.holdUsed = true; draw(); return;
  }
  if (n) { piece = n; draw(); }
}
function say(){
  const st = $("status");
  let cls = "fb", text;
  if (run.done) { cls += " good"; text = "✓ 砌好！橙框＝蓋，紫虛線＝T 位，黃虛線＝第二槽。"; }
  else if (run.failed) { cls += " bad"; text = "✗ 呢次唔得。撳「上一步」或者「重嚟」。紅框＝欠嘅格，紅交叉＝唔應該塞。"; }
  else if (run.stage === 1) { cls += " good"; text = "第一粒中咗，而家將 T 打入黃色虛線槽。"; }
  else text = `砌好千鳥格子個形（連蓋），唔使打 T。已落 ${run.locks} / ${pz.need} 粒。`;
  st.className = cls; st.textContent = text;
  const log = $("log"); log.textContent = "";
  for (const m of msgs) { const li = document.createElement("li"); li.textContent = m.text; if (m.good === true) li.style.color = css("--ok"); if (m.good === false) li.style.color = css("--bad"); log.appendChild(li); }
  log.scrollTop = log.scrollHeight;
  $("hint").textContent = hintOn ? "收起目標" : "目標形"; $("hint").disabled = false;
  $("undo").disabled = !hist.length;
}

// ---- demo
function buildDemo(){
  const r = E.newRun(pz), frames = [];
  pz.solution.slice(0, pz.need).forEach((s, i) => {
    const st = { p: s.piece, x: s.x, y: s.y, r: s.r, spin: s.spin };
    const f = { board: E.cloneBoard(r.board), slot: r.slot && r.slot.map(c => c.slice()), piece: st, queue: pz.queue.slice(i + 1), idx: i, path: s.path };
    const fb = E.applyLock(r, pz, st); f.fb = fb; f.msg = fb.msg;
    frames.push(f);
  });
  const end = { board: r.board, slot: null, piece: null, queue: [], idx: pz.solution.length, done: r.done };
  end.shape = E.findBuild(r.board); end.queue = pz.queue.slice(pz.need);
  frames.push(end);
  return { frames, i: 0 };
}
function step(d){ if (!demo) return; demo.i = Math.max(0, Math.min(demo.frames.length - 1, demo.i + d)); showDemo(); }
function showDemo(){
  const f = demo.frames[demo.i], n = pz.need;
  const cap = $("dcap"); cap.textContent = "";
  if (f.cap) { cap.textContent = `${demo.i + 1} / ${demo.frames.length}：${f.cap}`; draw(); return; }
  if (f.piece) {
    const head = document.createElement("div"); head.textContent = `第 ${f.idx + 1} / ${n} 粒：${f.piece.p}${spinLabel(f.fb) ? "，" + spinLabel(f.fb) : ""}${f.msg === "first" ? "（第一粒 TSD）" : f.msg === "second" ? "（第二粒 TSD）" : ""}`;
    const p = document.createElement("span"); p.className = "path"; p.textContent = f.path.join(" ");
    cap.appendChild(head); cap.appendChild(p);
  } else cap.textContent = "砌好：呢個就係個形。橙框係蓋，紫虛線係 T 位，黃虛線係第二槽。T 唔使打。";
  draw();
}
function enterDemo(){ demo = buildDemo(); $("demo").classList.add("on"); $("demoBtn").disabled = true; $("pad").style.opacity = .5; showDemo(); }
function exitDemo(redraw = true){ clearInterval(autoTimer); demo = null; $("demo").classList.remove("on"); $("demoBtn").disabled = false; $("pad").style.opacity = 1; if (redraw) draw(); }

// ---- drawing
let CS = 24;
const bc = $("board"), bx = bc.getContext("2d");
// in drag mode, show only the rows the drill uses (plus headroom) so the board can be bigger on a phone
function cropRows(){
  VIS0 = 18; VROWS = 22;
  if (!dragMode || !pz) return;
  let top = E.H;
  const see = b => { for (let y = 0; y < E.H; y++) if (b[y].some(c => c)) { top = Math.min(top, y); break; } };
  try {
    const d = buildDemo();
    for (const f of d.frames) { see(f.board); if (f.piece) for (const [, y] of E.cellsOf(f.piece.p, f.piece.x, f.piece.y, f.piece.r)) top = Math.min(top, y); if (f.shape) for (const [, y] of f.shape.cells) top = Math.min(top, y); }
  } catch (e) { return; }
  const v0 = Math.max(18, Math.min(top - 4, E.H - 12));
  VIS0 = v0; VROWS = E.H - v0;
}
function sizeBoard(){
  cropRows();
  const narrow = window.innerWidth <= 760; const avail = Math.min(window.innerWidth, document.documentElement.clientWidth) - 32 - 2 * (narrow ? 46 : 64) - 24;
  let cs = Math.max(12, Math.min(narrow ? 30 : 26, Math.floor(avail / 10)));
  // fit the play column (status, buttons, board, pad) plus the header into one screen
  const col = $("play");
  const cr = col.getBoundingClientRect(), other = cr.top + window.scrollY + cr.height - bc.getBoundingClientRect().height + (narrow ? 12 : 24);
  const byH = Math.floor((window.innerHeight - other) / VROWS);
  cs = Math.min(cs, Math.max(narrow ? 12 : 20, byH));
  CS = cs;
  const dpr = window.devicePixelRatio || 1;
  bc.width = 10 * CS * dpr; bc.height = VROWS * CS * dpr; bc.style.width = 10 * CS + "px"; bc.style.height = VROWS * CS + "px";
  bx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
function col(ch){ return ch === "G" ? css("--G") : css("--" + ch) || css("--G"); }
function cell(ctx, x, y, s, color, alpha = 1){ ctx.globalAlpha = alpha; ctx.fillStyle = color; ctx.fillRect(x * s + 1, y * s + 1, s - 2, s - 2); ctx.globalAlpha = 1; }
function outline(ctx, cells, color, dash){
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = 2; if (dash) ctx.setLineDash([4, 3]);
  for (const [x, y] of cells) { const yy = y - VIS0; if (yy < 0) continue; ctx.strokeRect(x * CS + 2, yy * CS + 2, CS - 4, CS - 4); }
  ctx.restore();
}
function draw(){
  const f = demo ? demo.frames[demo.i] : null;
  const board = f ? f.board : run.board;
  const slot = f ? f.slot : run.slot;
  const pc = f ? f.piece : piece;
  bx.fillStyle = css("--well"); bx.fillRect(0, 0, 10 * CS, VROWS * CS);
  bx.strokeStyle = css("--wellgrid"); bx.lineWidth = 1;
  for (let x = 1; x < 10; x++) { bx.beginPath(); bx.moveTo(x * CS + .5, 0); bx.lineTo(x * CS + .5, VROWS * CS); bx.stroke(); }
  for (let y = 1; y < VROWS; y++) { bx.beginPath(); bx.moveTo(0, y * CS + .5); bx.lineTo(10 * CS, y * CS + .5); bx.stroke(); }
  bx.fillStyle = "rgba(255,255,255,.04)"; bx.fillRect(0, 0, 10 * CS, 2 * CS);
  for (let y = VIS0; y < E.H; y++) for (let x = 0; x < 10; x++) { const c = board[y][x]; if (c) cell(bx, x, y - VIS0, CS, col(c)); }
  if (slot) outline(bx, slot, css("--slot"), true);
  if (!f && (hintOn || run.failed) && !run.done) targetOverlay(board, !!run.failed);
  const shp = f ? f.shape : (run.done && built && built.m ? built : null);
  if (shp) shapeOverlay(shp);
  if (!f && dragMode && pc) {
    if (drag && drag.cells) {
      const c = drag.cand;
      if (c) { const cc = E.cellsOf(c.state.p, c.state.x, c.state.y, c.state.r); for (const [x, y] of cc) if (y >= VIS0) cell(bx, x, y - VIS0, CS, col(c.state.p), .9); outline(bx, cc, "#ffffff", false); }
      for (const [x, y] of drag.cells) if (y >= VIS0) cell(bx, x, y - VIS0, CS, c ? col(pc.p) : css("--bad"), c ? .35 : .6);
    } else {
      const cc = E.cellsOf(pc.p, pc.x, pc.y, orient), lift = Math.max(0, VIS0 - Math.min(...cc.map(c => c[1])));
      for (const [x, y] of cc) cell(bx, x, y + lift - VIS0, CS, col(pc.p));
    }
  } else if (pc) {
    if (!f) { const g = E.dropped(board, pc); for (const [x, y] of E.cellsOf(g.p, g.x, g.y, g.r)) if (y >= VIS0) cell(bx, x, y - VIS0, CS, col(g.p), .28); }
    for (const [x, y] of E.cellsOf(pc.p, pc.x, pc.y, pc.r)) if (y >= VIS0) cell(bx, x, y - VIS0, CS, col(pc.p));
    if (f) outline(bx, E.cellsOf(pc.p, pc.x, pc.y, pc.r), "#ffffff", false);
  }
  // side boxes
  mini($("hold"), f ? [] : (run.hold ? [run.hold] : []), f ? false : run.holdUsed);
  // only the pieces this drill still needs, so the preview stays short
  // (one more than the placements left, in case a hold pulls the next one forward)
  const left = Math.max(1, Math.min(5, pz.need - (f ? (f.idx ?? pz.need) : run.locks)));
  mini($("next"), (f ? f.queue : run.queue).slice(0, left), false);
}
function gAt(n){ let g = 0; for (const e of pz.events || []) if (e.before <= n) g += e.n; return g; }
function targetOverlay(board, diff){
  const t = pz.target, dy = gAt(t.at) - gAt(run.locks);
  const at = (x, y) => (y + dy >= 0 && y + dy < E.H) ? board[y + dy][x] : null;
  bx.save();
  for (const [x, y, ch] of t.cells) {
    const yy = y + dy - VIS0; if (yy < 0) continue;
    if (ch === "#" || ch === "X") {
      if (at(x, y) === null) { bx.strokeStyle = diff ? css("--bad") : (ch === "X" ? css("--accent") : css("--ghost")); bx.lineWidth = ch === "X" ? 3 : 2; bx.setLineDash(diff ? [] : [3, 2]); bx.strokeRect(x * CS + 3, yy * CS + 3, CS - 6, CS - 6); }
    } else if (ch === "." && at(x, y) !== null && diff) {
      bx.strokeStyle = css("--bad"); bx.lineWidth = 2.5; bx.setLineDash([]); bx.beginPath(); bx.moveTo(x * CS + 5, yy * CS + 5); bx.lineTo(x * CS + CS - 5, yy * CS + CS - 5); bx.moveTo(x * CS + CS - 5, yy * CS + 5); bx.lineTo(x * CS + 5, yy * CS + CS - 5); bx.stroke();
    }
  }
  bx.restore();
  bx.save(); bx.globalAlpha = .45; for (const [x, y] of t.t) { const yy = y + dy - VIS0; if (yy >= 0) { bx.strokeStyle = css("--T"); bx.lineWidth = 2; bx.setLineDash([4, 3]); bx.strokeRect(x * CS + 2, yy * CS + 2, CS - 4, CS - 4); } } bx.restore();
}
function shapeOverlay(b){
  bx.save();
  for (const [x, y, ch] of b.m.cells || []) { const yy = y - VIS0; if (yy < 0 || ch !== "X") continue; bx.strokeStyle = css("--accent"); bx.lineWidth = 3; bx.setLineDash([]); bx.strokeRect(x * CS + 2, yy * CS + 2, CS - 4, CS - 4); }
  bx.lineWidth = 2; bx.setLineDash([4, 3]);
  for (const [x, y] of b.cells) { const yy = y - VIS0; if (yy >= 0) { bx.strokeStyle = css("--T"); bx.strokeRect(x * CS + 3, yy * CS + 3, CS - 6, CS - 6); } }
  for (const [x, y] of b.m.follow) { const yy = y - VIS0; if (yy >= 0) { bx.strokeStyle = css("--slot"); bx.strokeRect(x * CS + 6, yy * CS + 6, CS - 12, CS - 12); } }
  bx.restore();
}
function mini(cv, list, dim){
  const ctx = cv.getContext("2d"), s = 13; ctx.clearRect(0, 0, cv.width, cv.height);
  list.forEach((p, i) => {
    const cells = E.cellsOf(p, 0, 0, 0), minx = Math.min(...cells.map(c => c[0])), maxx = Math.max(...cells.map(c => c[0])), miny = Math.min(...cells.map(c => c[1]));
    const ox = (cv.width - (maxx - minx + 1) * s) / 2, oy = i * 40 + 6;
    ctx.globalAlpha = dim ? .35 : 1; ctx.fillStyle = col(p);
    for (const [x, y] of cells) ctx.fillRect(ox + (x - minx) * s, oy + (y - miny) * s, s - 1, s - 1);
    ctx.globalAlpha = 1;
  });
}
function legend(){
  const L = $("legend");
  for (const w of ART.windows) {
    if (w.mirrored) continue;
    const all = [...w.cells, ...w.followup], r0 = Math.min(...all.map(q => q.r)), c0 = Math.min(...all.map(q => q.c));
    const rows = Math.max(...all.map(q => q.r)) - r0 + 1, cols = Math.max(...all.map(q => q.c)) - c0 + 1, s = 16;
    const cv = document.createElement("canvas"); cv.width = cols * s; cv.height = rows * s; const ctx = cv.getContext("2d");
    ctx.fillStyle = css("--well"); ctx.fillRect(0, 0, cv.width, cv.height);
    for (const q of w.cells) { const x = q.c - c0, y = q.r - r0;
      if (q.extra) cell(ctx, x, y, s, css("--accent")); else if (q.v === "#") cell(ctx, x, y, s, css("--G")); else if (q.v === "T") cell(ctx, x, y, s, css("--T")); }
    ctx.strokeStyle = css("--slot"); ctx.setLineDash([3, 2]); ctx.lineWidth = 1.5;
    for (const q of w.followup) ctx.strokeRect((q.c - c0) * s + 2, (q.r - r0) * s + 2, s - 4, s - 4);
    const fig = document.createElement("figure"); fig.appendChild(cv);
    const cap = document.createElement("figcaption"); cap.textContent = VLAB[w.id] || w.id; fig.appendChild(cap); L.appendChild(fig);
  }
  const p = document.createElement("p"); p.className = "note"; p.style.margin = "0";
  p.textContent = "紫：第一粒 T；灰：一定要有嘢；橙：第二槽嘅蓋，打第一粒 T 之前要擺好；黃虛線：第二個槽（清完兩行之後）；冇顏色：一定要空。"; L.appendChild(p);
}

// ---- drag and drop: the piece snaps to the nearest placement the keys can reach (same BFS as the demo paths)
const norm = cells => { const mx = Math.min(...cells.map(c => c[0])), my = Math.min(...cells.map(c => c[1])); return [mx, my, E.key(cells.map(([x, y]) => [x - mx, y - my]))]; };
const SPINRANK = { full: 0, mini: 1, none: 2 };
function candidates(){
  if (!cands) cands = E.placements(run.board, piece.p).map(pl => { const [mx, my, k] = norm(E.cellsOf(pl.state.p, pl.state.x, pl.state.y, pl.state.r)); return { ...pl, mx, my, k }; });
  return cands;
}
function dragAt(e){
  const rect = bc.getBoundingClientRect(), fx = (e.clientX - rect.left) / CS, fy = (e.clientY - rect.top) / CS;
  const off = E.cellsOf(piece.p, 0, 0, orient), [ox, oy] = norm(off), w = Math.max(...off.map(c => c[0])) - ox + 1, h = Math.max(...off.map(c => c[1])) - oy + 1;
  let X = Math.round(fx - w / 2) - ox; X = Math.max(-ox, Math.min(10 - w - ox, X));
  const lift = e.pointerType === "mouse" ? h / 2 : h + 1;
  const Y = Math.round(fy - lift) + VIS0 - oy;
  drag.cells = E.cellsOf(piece.p, X, Y, orient);
  const [mx, my, k] = norm(drag.cells);
  let best = null;
  for (const c of candidates()) { if (c.k !== k || c.mx !== mx) continue;
    const d = Math.abs(c.my - my), sc = d * 10 + SPINRANK[c.state.spin];
    if (!best || sc < best.sc || (sc === best.sc && c.path.length < best.c.path.length)) best = { sc, c }; }
  drag.cand = best && best.c;
}
bc.addEventListener("pointerdown", e => {
  if (!dragMode || demo || !piece || run.done || run.failed) return;
  e.preventDefault(); bc.setPointerCapture(e.pointerId);
  drag = { sx: e.clientX, sy: e.clientY, moved: false }; dragAt(e); draw();
});
bc.addEventListener("pointermove", e => {
  if (!drag) return; if (Math.hypot(e.clientX - drag.sx, e.clientY - drag.sy) > 8) drag.moved = true; dragAt(e); draw();
});
bc.addEventListener("pointerup", () => {
  if (!drag) return; const d = drag; drag = null;
  if (!d.moved) { orient = (orient + 1) % 4; draw(); return; }
  if (d.cand) commit(d.cand.state, d.cand.path); else draw();
});
bc.addEventListener("pointercancel", () => { drag = null; draw(); });
function setMode(m){ dragMode = m; store.set("practice-cutcopy-mode", m ? "drag" : "key"); document.body.classList.toggle("drag", m);
  $("mDrag").setAttribute("aria-pressed", m); $("mKey").setAttribute("aria-pressed", !m); orient = 0; drag = null; sizeBoard(); if (run) draw(); }
$("mDrag").addEventListener("click", () => setMode(true));
$("mKey").addEventListener("click", () => setMode(false));

// ---- input
$("undo").addEventListener("click", undo);
$("reset").addEventListener("click", () => load(cur));
$("hint").addEventListener("click", () => { hintOn = !hintOn; say(); draw(); });
$("demoBtn").addEventListener("click", enterDemo);
$("dexit").addEventListener("click", () => exitDemo());
$("d0").addEventListener("click", () => { demo.i = 0; showDemo(); });
$("d9").addEventListener("click", () => { demo.i = demo.frames.length - 1; showDemo(); });
$("dp").addEventListener("click", () => step(-1));
$("dn").addEventListener("click", () => step(1));
for (const b of $("pad").querySelectorAll("button")) b.addEventListener("click", () => act(b.dataset.a));
const KEYS = { ArrowLeft: "left", ArrowRight: "right", ArrowDown: "soft", ArrowUp: "cw", x: "cw", X: "cw", z: "ccw", Z: "ccw", a: "180", A: "180", " ": "hard", c: "hold", C: "hold", Shift: "hold" };
document.addEventListener("keydown", e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "Backspace") { e.preventDefault(); undo(); return; }
  if (e.key === "r" || e.key === "R") { load(cur); return; }
  const a = KEYS[e.key]; if (!a) return;
  e.preventDefault();
  if ((a === "hard" || a === "hold") && e.repeat) return;
  act(a);
});
window.addEventListener("resize", () => { sizeBoard(); draw(); });
const mq = window.matchMedia("(prefers-color-scheme: dark)"); if (mq.addEventListener) mq.addEventListener("change", () => draw());
if (window.innerWidth <= 760) { const st = document.querySelector(".stage"); st.after($("log")); st.after($("status")); $("status").style.width = "100%"; $("log").style.width = "100%"; }
const sm = store.get("practice-cutcopy-mode"); setMode(sm ? sm === "drag" : window.matchMedia("(pointer: coarse)").matches); legend();
const last = store.get("practice-cutcopy-last"); load(Number.isInteger(last) && last >= 0 && last < PZ.length ? last : 0);
})();
