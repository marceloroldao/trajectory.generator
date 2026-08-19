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
4. Can additional admissible structure in the step count or trajectory class extend recoverability without secretly storing the data?
5. What orbit statistics emerge without being imposed?

## Why this differs from the earlier XOR/NOT prototype

The earlier prototype used transformations dominated by

```text
~(x ^ t)
```

which is equivalent, at fixed width, to XOR with a time-dependent constant. XOR compositions commute, so much of the ordering information collapses. This project replaces that core with reversible **non-commutative** operations: modular multiplication by odd constants, modular addition, rotation, and time-dependent mixing.

## Repository layout

```text
trajectory_generator/
    core.py             reversible dynamics
    decode.py           recovery from final state + step count
experiments/
    exhaustive_scan.py  exact collision/injectivity scans
    emergence_scan.py   orbit statistics; phi is analysis-only
    demo.py             end-to-end examples
tests/
    test_core.py        inverse and recovery tests
docs/
    METHODOLOGY.md      hypotheses, metrics, falsification criteria
```

## Quick start

```bash
python -m experiments.demo
python -m experiments.exhaustive_scan --max-bits 20
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
