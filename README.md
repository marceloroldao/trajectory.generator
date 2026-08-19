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

## Three complementary machines

The project keeps three distinct constructions so their claims are not mixed.

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

`trajectory_generator/trajectory_address.py` asks a constructive question: can the dynamics deliberately preserve one fresh degree of freedom per arbitrary input bit so that recovery becomes direct?

Yes, for `steps <= state_width`.

At every step the public deterministic universe permutes/mixes the state. The data bit is then injected into a coordinate known to be free of prior data deviation relative to the public universe baseline. The decoder reconstructs the same schedule from the step count, reads the bit, removes it, and inverts the universe step.

For the current implementation:

```text
search: none
external trajectory memory: none
recovery input: final_state + steps + public machine definition
arbitrary capacity: at most state_width bits
```

Random full-capacity 63-bit tests recover exactly. Exhaustive full-capacity scans at widths 8, 12, and 16 found zero collisions and zero decode failures. At `n = width`, the tested construction uses the full finite state space bijectively.

This machine is a **reversible trajectory address**, not compression and not a cryptographic hash.

See `docs/trajectory_address_2026-08-19.md`.

### 3. Hierarchical / relational trajectory address

`trajectory_generator/hierarchical_trajectory.py` asks whether long but structured trajectories can be addressed by storing **relations between changes** rather than one explicit degree of freedom per raw step.

The current constrained family stores the initial bit plus the ordered positions where the bit changes. For length `n` and at most `K` changes, the number of admissible trajectories is

```text
M(n,K) = 2 * sum(C(n-1, j), j=0..K)
```

and exact recovery is permitted only when

```text
M(n,K) <= 2^state_width.
```

With the default 63-bit state and `max_changes = 5`, the complete admissible family remains exactly addressable through **14,082 steps**; step 14,083 exceeds the 63-bit capacity for that constrained family.

This is not arbitrary 14,082-bit compression. The advantage exists because the admissible trajectory family has far less than 14,082 bits of entropy.

See `docs/hierarchical_trajectory_2026-08-19.md`.

## Core hypothesis

Let a deterministic universe evolution be `U_t` and a data-dependent transition be `D_{b,t}`. A generic trajectory evolves as

```text
X_(t+1) = D_(b_t,t)( U_t(X_t) )
```

The project studies three questions separately:

1. can generic reversible mixing preserve enough trajectory identity for exact inversion over useful finite domains?
2. can a deliberately structured trajectory address attain exact recovery efficiently without hidden side information?
3. can structured long trajectories be represented more compactly by relations among changes while keeping the information accounting explicit?

The dynamics intentionally do **not** contain the golden ratio or any other preferred irrational constant. If a stable ratio appears in orbit/trajectory measurements, it must emerge from the dynamics rather than being inserted into them.

## Fundamental limit

For a fixed `w`-bit final state and a fixed step count `n`, there are at most `2^w` possible final states but `2^n` arbitrary binary trajectories. Therefore, when `n > w`, a globally injective mapping of *all* possible `n`-bit messages into one `w`-bit final state is impossible by the pigeonhole principle.

The linear trajectory-address construction reaches this arbitrary-data capacity boundary (`n <= w`) but does not exceed it.

Longer trajectories can be exactly recoverable from the same fixed-width final state only when the admissible input family is constrained so that its entropy is no greater than the state capacity, or when additional state/metadata is supplied explicitly. The hierarchical experiment studies exactly this constrained case.

## Why this differs from the earlier XOR/NOT prototype

The earlier prototype used transformations dominated by

```text
~(x ^ t)
```

which is equivalent, at fixed width, to XOR with a time-dependent constant. XOR compositions commute, so much of the ordering information collapses.

The mixed-state core replaces that with reversible non-commutative operations. The linear trajectory-address construction explicitly preserves a fresh reachable-state degree of freedom for each new arbitrary bit. The hierarchical construction instead ranks a constrained family by its relational change structure.

## Repository layout

```text
trajectory_generator/
    core.py                    generic reversible mixed-state dynamics
    decode.py                  exhaustive + MITM + partitioned MITM recovery
    trajectory_address.py      constructive trajectory address for arbitrary bits
    hierarchical_trajectory.py relational address for constrained trajectories
experiments/
    exhaustive_scan.py
    frontier_scan.py
    width_frontier_scan.py
    universe_period_ablation.py
    emergence_scan.py
    mitm_demo.py
    trajectory_address_scan.py
tests/
    test_core.py
    test_decode.py
    test_trajectory_address.py
    test_hierarchical_trajectory.py
docs/
    METHODOLOGY.md
    results_2026-08-19.md
    mitm_recovery_2026-08-19.md
    partitioned_mitm_2026-08-19.md
    universe_ablation_2026-08-19.md
    trajectory_address_2026-08-19.md
    hierarchical_trajectory_2026-08-19.md
```

## Quick start

```bash
python experiments/trajectory_address_scan.py --widths 8 12 16
python experiments/mitm_demo.py --bits 22
python experiments/frontier_scan.py --from-bits 17 --max-bits 22
python -m unittest discover -s tests -v
```

No third-party Python dependency is required for the current experiments.

## Success criterion

A result is only counted as exact recovery when the decoder receives only:

```text
final_state
number_of_steps
```

plus the public deterministic machine definition and public initial state, and returns exactly one trajectory which reproduces that final state.

If several trajectories match, the mixed-state decoders explicitly report ambiguity rather than guessing.

## License

Source-available for academic, educational, and non-commercial research use under the repository `LICENSE`. Commercial exploitation requires a separate commercial license from the copyright holder.

This licensing model contains commercial-use restrictions and therefore should **not** be described as OSI Open Source.
