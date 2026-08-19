# trajectory.generator

Experimental research project testing the hypothesis that **information can be represented by an ordered trajectory of reversible state transformations**.

Primary target:

> Given only `(final_state, number_of_steps)`, recover the unique original trajectory.

No trajectory log, side table, plaintext hint, checksum, or externally stored branch history is allowed unless explicitly stated by an experiment.

## Research status

**Maturity:** experimental / pre-alpha  
**Publication status:** not a release candidate

Positive, negative, and corrected results are all preserved.

## Current constructions

### 1. Mixed-state reversible machine

`trajectory_generator/core.py`

Generic reversible, time-dependent, non-commutative dynamics. Exhaustive enumeration reached 22 input bits with 4,194,304 distinct final states and zero observed collisions in that tested domain.

Exact recovery methods include exhaustive search, meet-in-the-middle (MITM), and partitioned MITM. Target-specific MITM recovery has been demonstrated through 36 bits.

### 2. Linear trajectory address

`trajectory_generator/trajectory_address.py`

Constructive direct recovery for arbitrary data while `steps <= state_width`. The machine deliberately preserves one fresh degree of freedom per arbitrary input bit.

For a 63-bit state, arbitrary exact capacity is therefore at most 63 independent bits. This is a reversible trajectory address, not compression and not a cryptographic hash.

### 3. Hierarchical / relational trajectory address

`trajectory_generator/hierarchical_trajectory.py`

Represents a structured trajectory by its initial value and the positions where the value changes. For at most `K` changes:

```text
M(n,K) = 2 * sum(C(n-1,j), j=0..K)
```

With width 63 and `K=5`, the complete constrained family fits through 14,082 steps. This does **not** mean 14,082 arbitrary bits fit in 63 bits; the admissible family has much lower entropy.

### 4. Multi-scale trajectory

`trajectory_generator/multiscale_trajectory.py`

Compares multiple public relational bases, currently local and Fenwick/tree. The benefit is broader structural coverage: a trace complex in one basis may be sparse in another.

With width 63 and `K=5`, the conservative two-basis envelope fits through 12,259 steps.

### 5. Recursive relation trajectory

`trajectory_generator/recursive_trajectory.py`

Repeatedly applies the invertible relation transform:

```text
state -> relation -> relation of relations -> ...
```

Examples:

```text
010101...   -> 1 non-root deviation at level 2
00110011... -> 1 non-root deviation at level 3
```

With levels 0..3, width 63 and `K=5`, the conservative union envelope fits through 10,672 steps.

### 6. Adaptive / dyadic tree experiments

`trajectory_generator/adaptive_trajectory_tree.py` preserves the negative result for arbitrary cut positions: once cut metadata is honestly counted, the conservative frontier collapses to about 48 steps.

`trajectory_generator/dyadic_trajectory_tree.py` permits one public midpoint split, eliminating cut-position metadata. Its conservative frontier is about 274 steps, and each half may choose a different recursive relation level.

These experiments show that **freedom of structure has an information cost**.

### 7. Self-resolving canonical tree

`trajectory_generator/self_resolving_tree.py`

Canonical rule:

1. encode a block as a leaf if any allowed relation level is sparse enough;
2. otherwise split at the public midpoint;
3. recurse.

Important correction: unrestricted recursion ultimately admits every binary sequence, so its exact semantic family is `2^n`; the earlier 20-step value was only a redundant numeric-envelope limit, not true semantic capacity.

### 8. Admissibility laws

`trajectory_generator/admissible_trajectory.py`, `trajectory_generator/state_admissibility.py`, and `trajectory_generator/finite_law_codec.py`

These experiments change the question from how to encode every trajectory to **which trajectories are allowed by a public law**.

A period-3 law gives a 63-bit frontier of 94 steps. A state-dependent Fibonacci law gives 89 steps. Exhaustive memory-2 and memory-3 scans reveal many algebraic spectral growth classes, including the plastic constant, golden ratio, and tribonacci constant, without inserting those constants into the rules.

### 9. Robustness, Pareto, and orbit-style metrics

The project separates entropy rate, exact frontier, rule robustness, trajectory robustness, occupancy, mixing, and error propagation. A representative balanced fixed-law class emerged near `lambda ~= 1.285199`, with frontier 170 steps.

### 10. Dynamic and endogenous universes

`dynamic_law_codec.py`, `coherence_universe.py`, `emergent_law_bank.py`, and `policy_universe.py` progressively move the "universe" from a fixed law toward endogenous law selection.

Current exact 63-bit results include:

```text
full-bank first selector: 80 steps
three-law coherence selector: 117 steps
balanced searched fixed policy: 184 steps
rigid searched fixed policy: ~202 steps, but very low perturbation tolerance
```

### 11. Second-order dynamic policy universe

`trajectory_generator/dynamic_policy_universe.py`

The selector weights themselves now change deterministically with `(history, phase)`. No policy sequence is stored externally.

A moderate-entropy second-order policy found by seeded search has:

```text
184 steps -> 2^63 admissible trajectories
185 steps -> 2^64 admissible trajectories
```

It therefore **does not beat** the balanced fixed-policy capacity frontier. However, it uses 12 distinct active laws across the 24 `(history, phase)` contexts, versus 5 laws for the frozen 184-step policy, while sampled one-bit perturbation survival remains about 32.4%.

This is an important negative result: making the policy layer more dynamic increases internal law diversity but does not automatically increase addressable information capacity.

See `docs/dynamic_policy_universe_2026-08-19.md`.

## Fundamental limit

For a fixed `w`-bit final state and fixed step count `n`, there are at most `2^w` final states but `2^n` arbitrary binary trajectories. Therefore a globally injective mapping of all arbitrary `n`-bit messages into one `w`-bit final state is impossible when `n > w`.

Longer trajectories are exactly recoverable only when the admissible family is constrained enough that its entropy fits the final-state address space, or when additional information is supplied explicitly.

For an admissible family `A_n`, the exact information accounting is

```text
H_adm(n) = log2 |A_n|.
```

A `w`-bit final state can address the whole family only if

```text
H_adm(n) <= w.
```

## Current research direction

The current target is a **stable endogenous computational universe** in which state, policy, law, and transition all participate but every adaptive choice remains recoverable from the public dynamics.

The latest result shows that adding a second adaptive layer does not by itself improve the 184-step balanced frontier. The next experiments should therefore search for a genuinely useful invariant or state variable carried by the dynamics, rather than merely adding selector complexity.

## Quick start

```bash
python experiments/dynamic_policy_search_memory3.py
python experiments/policy_search_memory3.py
python experiments/emergent_law_bank_scan.py
python experiments/coherence_universe_scan.py
python experiments/local_law_memory3_scan.py
python -m unittest discover -s tests -v
```

NumPy is required for experiments that use eigendecomposition. Core exact codecs remain pure Python.

## License

Source-available for academic, educational, and non-commercial research use under `LICENSE`. Commercial exploitation requires a separate commercial license from the copyright holder.

Because the license restricts commercial use, this repository should **not** be described as OSI Open Source.
