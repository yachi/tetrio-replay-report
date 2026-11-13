//! A Rust port of pipeline/sim/pc-solver.ts (SRS movegen + PC DFS) and of the engine movegen
//! pc-engine-gen.ts uses, loaded from Bun through bun:ffi. Every answer must equal the TS one,
//! placement order included, because the DFS returns the FIRST plan it finds.
pub mod srs;        // SRS+ tables, tryMove/tryRotate, the BFS movegen (pc-solver.ts `placements`)
pub mod solver;     // apply, regionsOk, solve, frames (pc-solver.ts)
pub mod engine_gen; // the engine's reachability with 180 (pc-engine-gen.ts `enginePlacements`)
pub mod ffi;        // extern "C" surface for bun:ffi
