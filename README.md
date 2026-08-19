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

## Five complementary constructions

The project keeps distinct constructions so their claims are not mixed.

### 1. Mixed-state machine

`trajectory_generator/core.py` asks whether trajectory identity can emerge from generic reversible, time-dependent, non-commutative mixing.

The default 63-bit machine has been exhaustively enumerated through **22 input bits**. At 22 bits, all **4,194,304 trajectories** produced distinct final states for the same step count: zero exact collisions were observed. This establishes injectivity only within the tested domain.

Exact recovery methods:

```text
exhaustive:       time O(2^n)
MITM:             time O(2^(n/2)), memory O(2^(n/2))
partitioned MITM: exact memory/time trade-off
```

Validated MITM target recoveries include 22, 24, 28, 32, and 36-bit trajectories. These are target-specific uniqueness results, not global collision-free proofs at those lengths.

### 2. Linear trajectory-address machine

`trajectory_generator/trajectory_address.py` deliberately preserves one fresh degree of freedom per arbitrary input bit so recovery becomes direct for `steps <= state_width`.

```text
search: none
external trajectory memory: none
recovery input: final_state + steps + public machine definition
arbitrary capacity: at most state_width bits
```

Random full-capacity 63-bit tests recover exactly. Exhaustive full-capacity scans at widths 8, 12, and 16 found zero collisions and zero decode failures.

This machine is a **reversible trajectory address**, not compression and not a cryptographic hash.

### 3. Hierarchical / relational trajectory address

`trajectory_generator/hierarchical_trajectory.py` stores the initial bit plus positions where the value changes. For length `n` and at most `K` changes:

```text
M(n,K) = 2 * sum(C(n-1, j), j=0..K)
```

With a 63-bit state and `K=5`, the complete constrained family remains exactly addressable through **14,082 steps**. This is not arbitrary 14,082-bit compression; the admissible family has much lower entropy.

### 4. Multi-scale trajectory tree

`trajectory_generator/multiscale_trajectory.py` evaluates more than one relational basis. The current experiment includes:

- local relation: compare with the previous state;
- Fenwick/tree relation: compare with a hierarchical ancestor.

A trajectory such as repeated `00001111` can be simpler in the tree basis than in the local basis. With two public bases, 63 bits and `K=5`, the conservative full-family envelope fits through **12,259 steps**. The gain is structural coverage rather than raw capacity.

### 5. Recursive relation trajectory

`trajectory_generator/recursive_trajectory.py` applies the relation transform repeatedly:

```text
state -> relation -> relation of relations -> relation of relations of relations
```

This exposes patterns that are not sparse at the raw or first-relation level. Examples:

```text
010101...      -> 1 non-root deviation at level 2
00110011...    -> 1 non-root deviation at level 3
```

With levels 0..3, a 63-bit state and `K=5`, the conservative union envelope fits through **10,672 steps**. Again, the benefit is wider coverage of structured trajectories, not increased information-theoretic capacity.

See `docs/recursive_trajectory_2026-08-19.md`.

## Core hypothesis

Let a deterministic universe evolution be `U_t` and a data-dependent transition be `D_{b,t}`. A generic trajectory evolves as

```text
X_(t+1) = D_(b_t,t)( U_t(X_t) )
```

The project now separates three kinds of questions:

1. can generic reversible dynamics preserve trajectory identity?
2. can arbitrary bits be given a direct reversible trajectory address up to the state-capacity limit?
3. can long structured traces be represented by sparse relations at one or more hierarchical levels?

The dynamics intentionally do **not** contain the golden ratio or another preferred irrational constant. If a stable scale ratio appears, it must emerge from measured optimal structures rather than being inserted into the generator.

## Fundamental limit

For a fixed `w`-bit final state and a fixed step count `n`, there are at most `2^w` possible final states but `2^n` arbitrary binary trajectories. Therefore, for `n > w`, a globally injective mapping of all arbitrary `n`-bit messages into one `w`-bit final state is impossible.

Longer traces can be exactly recoverable only when the admissible family is constrained enough that its information content fits the final-state address space, or when additional state/metadata is supplied explicitly.

This project therefore distinguishes carefully between:

```text
more capacity        != more structural coverage
longer raw trajectory != more independent information
```

## Repository layout

```text
trajectory_generator/
    core.py
    decode.py
    trajectory_address.py
    hierarchical_trajectory.py
    multiscale_trajectory.py
    recursive_trajectory.py
experiments/
    exhaustive_scan.py
    frontier_scan.py
    width_frontier_scan.py
    universe_period_ablation.py
    emergence_scan.py
    mitm_demo.py
    trajectory_address_scan.py
    multiscale_compare.py
    recursive_compare.py
tests/
    test_core.py
    test_decode.py
    test_trajectory_address.py
    test_hierarchical_trajectory.py
    test_multiscale_trajectory.py
    test_recursive_trajectory.py
docs/
    METHODOLOGY.md
    results_2026-08-19.md
    mitm_recovery_2026-08-19.md
    partitioned_mitm_2026-08-19.md
    universe_ablation_2026-08-19.md
    trajectory_address_2026-08-19.md
    hierarchical_trajectory_2026-08-19.md
    multiscale_trajectory_2026-08-19.md
    recursive_trajectory_2026-08-19.md
```

## Quick start

```bash
python experiments/recursive_compare.py
python experiments/multiscale_compare.py
python experiments/trajectory_address_scan.py --widths 8 12 16
python experiments/mitm_demo.py --bits 22
python -m unittest discover -s tests -v
```

No third-party Python dependency is required for the current experiments.

## Success criterion

A result is counted as exact recovery only when the decoder receives:

```text
final_state
number_of_steps
```

plus the public deterministic machine definition and public initial state, and returns exactly one trajectory reproducing that final state.

## License

Source-available for academic, educational, and non-commercial research use under the repository `LICENSE`. Commercial exploitation requires a separate commercial license from the copyright holder.

This licensing model contains commercial-use restrictions and therefore should **not** be described as OSI Open Source.
