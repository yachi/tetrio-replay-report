async page => {
  const result = await page.evaluate(async () => {
    const BASE = "http://localhost:8931/";
    const NAMES = ["replay-2026-07-22-.ttrm"];
    for (let i = 2; i <= 10; i++) NAMES.push("replay-2026-07-22-" + i + ".ttrm");

    function deq(a, b, path) {
      path = path || "$";
      if (a === b) return null;
      if (typeof a !== typeof b) return "type@" + path + " " + typeof a + "/" + typeof b;
      if (a && b && typeof a === "object") {
        if (Array.isArray(a) !== Array.isArray(b)) return "arr@" + path;
        if (Array.isArray(a)) {
          if (a.length !== b.length) return "len@" + path + " " + a.length + "/" + b.length;
          for (let i = 0; i < a.length; i++) { const r = deq(a[i], b[i], path + "[" + i + "]"); if (r) return r; }
          return null;
        }
        const ka = Object.keys(a), kb = Object.keys(b);
        const sa = ka.slice().sort(), sb = kb.slice().sort();
        if (sa.length !== sb.length || sa.join(",") !== sb.join(",")) return "keys@" + path + " {" + sa + "}/{" + sb + "}";
        for (const k of ka) { const r = deq(a[k], b[k], path + "." + k); if (r) return r; }
        return null;
      }
      return "val@" + path + " " + JSON.stringify(a) + "/" + JSON.stringify(b);
    }

    // load raw ttrm texts + expected facts
    const texts = await Promise.all(NAMES.map(n => fetch(BASE + encodeURIComponent(n)).then(r => r.text())));
    const items = NAMES.map((n, i) => ({ name: n, text: texts[i] }));
    const expected = await fetch(BASE + "report/facts.json").then(r => r.json());

    const out = {};

    // ---- TEST A: deep-equal ----
    const factsA = window.__analyze(items);
    const diff = deq(factsA, expected);
    out.A = { equal: diff === null, firstDiff: diff, matches: factsA.matches.length, players: factsA.players };

    // ---- TEST B: subset of 3 ----
    const factsB = window.__analyze(items.slice(0, 3));
    out.B = {
      matchCount: factsB.matches.length,
      indices: factsB.matches.map(m => m.index),
      files: factsB.matches.map(m => m.file),
      totalRounds: factsB.matches.reduce((t, m) => t + m.rounds.length, 0),
      claimsAllPass: window.__claims().every(c => c.pass),
      residueCheck: factsB.matches.length === 3
    };

    // ---- TEST C: tamper one apm value ----
    const raw = JSON.parse(texts[0]);
    const pl = raw.replay.leaderboard[0];
    const uname = pl.username;
    const origApm = pl.stats.apm;
    const before = window.__analyze([{ name: NAMES[0], text: texts[0] }]);
    const beforeApm = before.matches[0].leaderboard[uname].apm_x1000;
    pl.stats.apm = 99.123;
    const tamperedText = JSON.stringify(raw);
    const after = window.__analyze([{ name: NAMES[0], text: tamperedText }]);
    const afterApm = after.matches[0].leaderboard[uname].apm_x1000;
    out.C = {
      user: uname, origApm, beforeApm, afterApm,
      expectedAfter: Math.floor(99.123 * 1000 + 0.5),
      changed: beforeApm !== afterApm,
      correct: afterApm === Math.floor(99.123 * 1000 + 0.5)
    };

    // ---- TEST D: full session, all claims pass ----
    window.__analyze(items);
    const claims = window.__claims();
    out.D = {
      total: claims.length,
      passed: claims.filter(c => c.pass).length,
      failed: claims.filter(c => !c.pass).map(c => ({ id: c.id, canto: c.canto })),
      allPass: claims.length > 0 && claims.every(c => c.pass)
    };

    // ---- TEST F: malformed input handling ----
    let fCrash = false, fFacts = null;
    try {
      fFacts = window.__analyze(["this is not json {{{", items[0].text, items[1].text]);
    } catch (e) { fCrash = true; }
    out.F = {
      crashed: fCrash,
      validParsed: fFacts ? fFacts.matches.length : -1,
      expectValid2: fFacts ? fFacts.matches.length === 2 : false
    };

    return out;
  });
  return JSON.stringify(result, null, 2);
}
