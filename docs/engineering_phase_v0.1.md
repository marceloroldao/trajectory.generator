# trajectory.generator — Engineering Phase v0.1

Status: ACTIVE
Mathematical baseline: FROZEN

## Purpose

Turn the validated mathematical construction into a small, auditable reference core without changing the frozen invariants.

## Reference API target

The engineering core should expose four conceptual operations:

- `count(T)` -> number of admissible trajectories at horizon T.
- `rank(trajectory)` -> bijective integer address `A_T`.
- `unrank(A_T, T)` -> complete admissible trajectory.
- `access(A_T, T, k)` -> symbol at position k without reconstructing all symbols.
- `append(A_T, T, z)` -> address at T+1 when z is an admissible next symbol.

## Frozen invariants

Any implementation replacing the experimental reference must preserve:

1. Exact bijection / roundtrip.
2. Exact interval-conditioned path counts.
3. `N(218) = 9,131,204,053,820,206,208` (63 bits).
4. `N(219) = 10,214,739,716,735,776,832` (64 bits).
5. Online append equals direct final ranking.
6. Random access equals full decode at the queried position.
7. Fixed 4-bit private-state automaton and public phase `t mod 3`.

## Engineering sequence

### E1 — Reference core
Extract the fixed transition law, interval matrix counting, joint dyadic rank/unrank, append and access into a minimal importable module. Experiments remain independent validation oracles.

### E2 — Differential test suite
For small horizons, exhaust all admissible trajectories and compare reference-core operations against the frozen experimental implementations. For larger horizons, use deterministic randomized vectors including T=218 and T=219.

### E3 — Benchmarks
Measure separately:

- `count(T)` latency;
- `rank/unrank` latency;
- `append` latency;
- random-access latency;
- peak memory;
- number and bit-width of integer arithmetic operations.

Do not conflate structural O(log T) block complexity with big-integer arithmetic cost.

### E4 — Conventional baselines
Compare the representation against explicit bit storage and conventional reversible/indexed representations. Report both payload bits and metadata/runtime cost. Do not call the trajectory address a cryptographic hash or claim generic compression.

### E5 — Optimization
Only after E1-E4 pass: cache fixed matrix powers, specialize the 16-state matrices, reduce allocations, and consider a compiled implementation. Every optimization must pass the same differential suite.

## Release gate

A software release named v0.1 should only be cut when E1 and E2 pass in CI and the benchmark methodology from E3 is committed. Mathematical changes require a new baseline rather than a silent refactor.
