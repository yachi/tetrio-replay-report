//! Test harness for `engine_gen::engine_placements` (pc-engine-gen-native.test.ts): one case per
//! stdin line, `<piece> <H> <row0> <row1> ...` (rows as decimal bitmasks, bottom first), one answer
//! per stdout line, placements joined by `;`, cells by `,`. With `--time`, also prints the elapsed
//! microseconds on stderr. Includes the module by path so it builds without the rest of the crate.
#[path = "../engine_gen.rs"]
mod engine_gen;
use std::io::{BufRead, Write};

fn main() {
    let time = std::env::args().any(|a| a == "--time");
    let stdin = std::io::stdin();
    let mut cases: Vec<(u8, usize, Vec<u16>)> = Vec::new();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let mut it = line.split_whitespace();
        let Some(p) = it.next() else { continue };
        let h: usize = it.next().unwrap().parse().unwrap();
        let rows: Vec<u16> = it.map(|s| s.parse().unwrap()).collect();
        cases.push((p.as_bytes()[0], h, rows));
    }
    let t0 = std::time::Instant::now();
    let res: Vec<Vec<Vec<u16>>> = cases.iter().map(|(p, h, r)| engine_gen::engine_placements(r, *p, *h)).collect();
    let us = t0.elapsed().as_micros();
    let out = std::io::stdout();
    let mut o = std::io::BufWriter::new(out.lock());
    for r in &res {
        let s: Vec<String> = r.iter().map(|c| c.iter().map(|v| v.to_string()).collect::<Vec<_>>().join(",")).collect();
        writeln!(o, "{}", s.join(";")).unwrap();
    }
    if time { eprintln!("rust_us {}", us); }
}
