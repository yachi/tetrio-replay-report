use pc_solver_rs::solver::*;
use std::io::{BufRead, Write};
use std::sync::{Arc, atomic::{AtomicUsize, Ordering}};
fn perms() -> Vec<Vec<u8>> { let mut out = vec![]; fn r(p: &mut Vec<u8>, rest: &mut Vec<u8>, out: &mut Vec<Vec<u8>>) { if rest.is_empty() { out.push(p.clone()); return; } for i in 0..rest.len() { let c = rest.remove(i); p.push(c); r(p, rest, out); p.pop(); rest.insert(i, c); } } r(&mut vec![], &mut b"IOTSZJL".to_vec(), &mut out); out }
fn start(left: &[u8], b: &[u8]) -> (u8, u8, Vec<u8>) {
    match left.len() { 0 => (b[0], NONE, b[1..].to_vec()), 1 => (left[0], NONE, b.to_vec()), 2 => (left[0], left[1], b.to_vec()),
        _ => { let mut s = left[2..].to_vec(); s.extend(b); (left[0], left[1], s) } }
}
fn main() {
    let k: usize = std::env::var("K").ok().and_then(|s| s.parse().ok()).unwrap_or(200);
    let nt: usize = std::env::var("JOBS").ok().and_then(|s| s.parse().ok()).unwrap_or(4);
    let lines: Arc<Vec<String>> = Arc::new(std::io::stdin().lock().lines().map(|l| l.unwrap()).filter(|l| !l.is_empty()).collect());
    let ps = Arc::new(perms()); let next = Arc::new(AtomicUsize::new(0)); let (tx, rx) = std::sync::mpsc::channel();
    for _ in 0..nt { let (ps, lines, next, tx) = (ps.clone(), lines.clone(), next.clone(), tx.clone()); std::thread::spawn(move || loop {
        let i = next.fetch_add(1, Ordering::SeqCst); if i >= lines.len() { break; }
        let l = &lines[i]; let mut it = l.split('|');
        let rows: Vec<u16> = it.next().unwrap().split(',').map(|s| s.parse().unwrap()).collect();
        let left: Vec<u8> = it.next().unwrap_or("").bytes().collect();
        let t0 = std::time::Instant::now();
        let fails: Vec<&Vec<u8>> = ps.iter().filter(|b| { let (c,h,s) = start(&left, b); !matches!(check(&rows, c, h, &s, 0, &mut Memo::default(), 5, 2_000_000, Gen::Engine), Verdict::Ok{..}) }).collect();
        let mut seed: u64 = l.bytes().fold(7u64, |a, c| a.wrapping_mul(131).wrapping_add(c as u64));
        let mut rnd = || { seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407); (seed >> 33) as usize };
        let n = if fails.is_empty() { 0 } else { k };
        let (mut ok, mut unk) = (0, 0);
        for _ in 0..n {
            let b3 = fails[rnd() % fails.len()]; let b4 = &ps[rnd() % ps.len()];
            let mut b = b3.clone(); b.extend(b4.iter()); let (c,h,s) = start(&left, &b);
            match check(&rows, c, h, &s, 0, &mut Memo::default(), 7, 20_000_000, Gen::Engine) { Verdict::Ok{..} => ok += 1, Verdict::Short => unk += 1, Verdict::False => {} }
        }
        eprintln!("{} {:?}", i, t0.elapsed());
        tx.send(format!("{{\"line\":{:?},\"fail3\":{},\"n\":{},\"ok\":{},\"unk\":{}}}", l, fails.len(), n, ok, unk)).unwrap();
    }); }
    drop(tx); let so = std::io::stdout(); let mut so = so.lock();
    for s in rx { writeln!(so, "{}", s).unwrap(); so.flush().unwrap(); }
}
