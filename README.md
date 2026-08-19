# trajectory.generator

Experimental research project for testing the hypothesis that **information can be represented by an ordered trajectory of reversible state transformations**.

The primary experimental target is deliberately strict:

> Given only `(final_state, number_of_steps)`, attempt to recover the unique original bit trajectory.

No trajectory log, side table, checksum, plaintext hint, or externally stored branch history is allowed in the decoder.

## Research status

**Maturity:** experimental / pre-alpha  
**Publication status:** not a release candidate  
**RSMS compatibility:** pending formal alignment with the current `resolutive-science` specification before any stable scientific release.

This repository is a laboratory. Positive and negative results are both preserved.

### Current experimental frontier

The default 63-bit machine has been exhaustively enumerated through **22 input bits**. At 22 bits, all **4,194,304 trajectories** produced distinct final states for the same step count: **zero exact collisions were observed**. This establishes injectivity only within the tested domain; it does not prove scalability or injectivity beyond that frontier.

A second exact decoder now uses **meet-in-the-middle (MITM)** recovery. It still receives only `(final_state, steps)` plus the public machine definition, but reduces search from approximately `2^n` complete trajectories to two half searches of order `2^(n/2)`.

Validated target recoveries include 22, 24, 28, 32, and 36-bit trajectories. These are target-specific uniqueness results, not proofs that every trajectory of those lengths is collision-free.

See:

- `docs/results_2026-08-19.md` for exhaustive injectivity results;
- `docs/mitm_recovery_2026-08-19.md` for structural recovery results;
- `docs/universe_ablation_2026-08-19.md` for the universe-period ablation.

## Core hypothesis

Let a deterministic universe evolution be `U_t` and a data-dependent transition be `D_{b,t}`. The state evolves as

```text
X_(t+1) = D_(b_t,t)( U_t(X_t) )
```

with each primitive transformation reversible. The project investigates whether time-dependent, non-commutative composition can preserve enough trajectory identity that

```text
(final_state, number_of_steps) -> original trajectory
```

is unique over useful finite domains.

The dynamics intentionally do **not** contain the golden ratio or any other preferred irrational constant. If a stable ratio appears in orbit/trajectory measurements, it must emerge from the dynamics rather than being inserted into them.

## Fundamental limit

For a fixed `w`-bit final state and a fixed step count `n`, there are at most `2^w` possible final states but `2^n` arbitrary binary trajectories. Therefore, when `n > w`, a globally injective mapping of *all* possible `n`-bit messages into one `w`-bit final state is impossible by the pigeonhole principle.

The scientific questions are therefore:

1. For which finite domains is the mapping injective?
2. How quickly do collisions appear as trajectory length grows?
3. Does a deterministic universe transformation delay or structure those collisions?
4. Can useful recovery be achieved from `(final_state, steps)` without trajectory-side information?
5. What orbit statistics emerge without being imposed?

## Why this differs from the earlier XOR/NOT prototype

The earlier prototype used transformations dominated by

```text
~(x ^ t)
```

which is equivalent, at fixed width, to XOR with a time-dependent constant. XOR compositions commute, so much of the ordering information collapses. This project replaces that core with reversible **non-commutative** operations: modular multiplication by odd constants, modular addition, rotation, and time-dependent mixing.

## Exact decoders

### Exhaustive

Enumerates all `2^n` trajectories. It is retained as a correctness oracle for small domains.

### Meet-in-the-middle

Splits the trajectory at an intermediate time `m`.

- forward: enumerate all prefixes from the public initial state to time `m`;
- backward: enumerate all suffixes from the supplied final state back to time `m` using exact inverse transitions;
- match equal intermediate states.

The intermediate state is **not** supplied to the decoder and is not stored with the encoded value. It is discovered during decoding.

Approximate complexity:

```text
exhaustive: time O(2^n)
MITM:       time O(2^(n/2)), memory O(2^(n/2))
```

## Repository layout

```text
trajectory_generator/
    core.py             reversible dynamics
    decode.py           exhaustive + MITM recovery
experiments/
    exhaustive_scan.py  independent exact scan from t=0 for each length
    frontier_scan.py    incremental exhaustive frontier + collision witnesses
    width_frontier_scan.py width scaling experiments
    universe_period_ablation.py universe-period ablation
    emergence_scan.py   orbit statistics; phi is analysis-only
    mitm_demo.py        exact target recovery from final state + steps
    demo.py             end-to-end examples
tests/
    test_core.py        inverse/core tests
    test_decode.py      exhaustive/MITM equivalence and recovery tests
docs/
    METHODOLOGY.md      hypotheses, metrics, falsification criteria
    results_2026-08-19.md
    mitm_recovery_2026-08-19.md
    universe_ablation_2026-08-19.md
```

## Quick start

```bash
python experiments/mitm_demo.py --bits 22
python experiments/frontier_scan.py --from-bits 17 --max-bits 22
python -m unittest discover -s tests -v
```

No third-party Python dependency is required for the initial experiments.

## Success criterion

A result is only counted as exact recovery when the decoder receives **only**:

```text
final_state
number_of_steps
```

plus the public deterministic machine definition and public initial state, and returns exactly one trajectory which reproduces that final state.

If several trajectories match, the result is explicitly reported as ambiguous rather than guessed.

## License

Source-available for academic, educational, and non-commercial research use under the repository `LICENSE`. Commercial exploitation requires a separate commercial license from the copyright holder.

This licensing model contains commercial-use restrictions and therefore should **not** be described as OSI Open Source.
