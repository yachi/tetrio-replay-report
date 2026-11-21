//! One worked Perfect Clear per TST-opener board, for the cards of docs/tst-openers.html.
//!
//! Reads `rows|left` lines (the residue after the two-bag TST and the pieces left over, exactly the
//! lines `tst2bag`'s `pc4` reads) and prints one JSON object per line:
//!
//! * `b3`: the FIRST bag-3 deal, in the fixed permutation order of `perms()`, for which the solver finds
//!   a Perfect Clear (frame up to 5 rows, 2 000 000 nodes, the engine's movegen: `pc4`'s bag-3 call), and
//!   the plan it returns; null when no deal does.
//! * `b4`: the FIRST bag-3 deal the solver PROVES has no Perfect Clear (`Verdict::False`; an unknown is
//!   skipped), then the FIRST bag-4 deal after it with one (frame up to 7 rows, 20 000 000 nodes: `pc4`'s
//!   bag-4 call), and that plan; null when bag 3 always clears or no pair is found.
//!
//! A plan is the solver's own: per placement the piece, its four cells in the board AS IT STANDS at that
//! step (rows already cleared are gone, row*10+col), and whether it came out of the hold. The page maps
//! the cells back to the starting board and its audit replays every plan; nothing here is a figure.
use pc_solver_rs::solver::*;
use std::io::{BufRead, Write};
use std::sync::{Arc, atomic::{AtomicUsize, Ordering}};

fn perms() -> Vec<Vec<u8>> { let mut out = vec![]; fn r(p: &mut Vec<u8>, rest: &mut Vec<u8>, out: &mut Vec<Vec<u8>>) { if rest.is_empty() { out.push(p.clone()); return; } for i in 0..rest.len() { let c = rest.remove(i); p.push(c); r(p, rest, out); p.pop(); rest.insert(i, c); } } r(&mut vec![], &mut b"IOTSZJL".to_vec(), &mut out); out }
/// `pc4`'s start state: the leftover pieces first (current, then hold), then the dealt bags.
fn start(left: &[u8], b: &[u8]) -> (u8, u8, Vec<u8>) {
    match left.len() { 0 => (b[0], NONE, b[1..].to_vec()), 1 => (left[0], NONE, b.to_vec()), 2 => (left[0], left[1], b.to_vec()),
        _ => { let mut s = left[2..].to_vec(); s.extend(b); (left[0], left[1], s) } }
}
fn plan_json(h: i32, plan: &[Pl]) -> String {
    let ps: Vec<String> = plan.iter().map(|p| format!("[\"{}\",[{},{},{},{}],{}]", p.piece as char, p.cells[0], p.cells[1], p.cells[2], p.cells[3], p.held)).collect();
    format!("\"h\":{},\"plan\":[{}]", h, ps.join(","))
}
fn s(b: &[u8]) -> String { String::from_utf8(b.to_vec()).unwrap() }
fn main() {
    let nt: usize = std::env::var("JOBS").ok().and_then(|s| s.parse().ok()).unwrap_or(4);
    let lines: Arc<Vec<String>> = Arc::new(std::io::stdin().lock().lines().map(|l| l.unwrap()).filter(|l| !l.is_empty()).collect());
    let ps = Arc::new(perms()); let next = Arc::new(AtomicUsize::new(0)); let (tx, rx) = std::sync::mpsc::channel();
    for _ in 0..nt { let (ps, lines, next, tx) = (ps.clone(), lines.clone(), next.clone(), tx.clone()); std::thread::spawn(move || loop {
        let i = next.fetch_add(1, Ordering::SeqCst); if i >= lines.len() { break; }
        let l = &lines[i]; let mut it = l.split('|');
        let rows: Vec<u16> = it.next().unwrap().split(',').filter(|x| !x.is_empty()).map(|s| s.parse().unwrap()).collect();
        let left: Vec<u8> = it.next().unwrap_or("").bytes().collect();
        let mut b3 = String::from("null");
        let mut fail: Option<&Vec<u8>> = None;
        for b in ps.iter() {
            let (c, h, sq) = start(&left, b);
            match check(&rows, c, h, &sq, 0, &mut Memo::default(), 5, 2_000_000, Gen::Engine) {
                Verdict::Ok { h, plan } => { if b3 == "null" { b3 = format!("{{\"deal\":\"{}\",{}}}", s(b), plan_json(h, &plan)); } }
                Verdict::False => { if fail.is_none() { fail = Some(b); } }
                Verdict::Short => {}
            }
            if b3 != "null" && fail.is_some() { break; }
        }
        let mut b4 = String::from("null");
        if let Some(f) = fail {
            for b in ps.iter() {
                let mut d = f.clone(); d.extend(b.iter()); let (c, h, sq) = start(&left, &d);
                if let Verdict::Ok { h, plan } = check(&rows, c, h, &sq, 0, &mut Memo::default(), 7, 20_000_000, Gen::Engine) {
                    b4 = format!("{{\"deal3\":\"{}\",\"deal4\":\"{}\",{}}}", s(f), s(b), plan_json(h, &plan)); break;
                }
            }
        }
        eprintln!("{} done", i);
        tx.send((i, format!("{{\"line\":{:?},\"b3\":{},\"b4\":{}}}", l, b3, b4))).unwrap();
    }); }
    drop(tx); let mut out: Vec<(usize, String)> = rx.into_iter().collect(); out.sort();
    let so = std::io::stdout(); let mut so = so.lock();
    for (_, s) in out { writeln!(so, "{}", s).unwrap(); }
}
