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

The tree is data-dependent but deterministic under the public configuration.

#### Important correction

The first report described 20 steps as the tree's capacity frontier. That was too strong.

The recurrence used by the implementation,

```text
E(n) = LeafRange(n) + E(left) * E(right),
```

is a **redundant numeric address envelope**. It double-counts many trajectories that already have leaf representations.

Because unrestricted recursion may continue all the way to length-1 leaves, every binary sequence is eventually admissible. Therefore the exact semantic family is

```text
S(n) = 2^n.
```

So the unrestricted self-resolving grammar has the full entropy of arbitrary binary data. For one 63-bit final state, its information-theoretic arbitrary-data limit is still `n <= 63`.

The previously reported 20-step value is only the frontier of the current redundant address layout.

See:

- `docs/self_resolving_tree_2026-08-19.md`
- `docs/canonical_tree_correction_2026-08-19.md`
- `experiments/canonical_tree_count.py`

### 8. Admissibility laws

`trajectory_generator/admissible_trajectory.py`, `trajectory_generator/state_admissibility.py`, and `trajectory_generator/finite_law_codec.py`

These experiments change the question from how to encode every trajectory to **which trajectories are allowed by a public law**.

A period-3 law forces one state in every three from the previous two states and a public phase. Only 2/3 of the raw steps remain independent, giving a 63-bit frontier of 94 steps.

A state-dependent law produces Fibonacci counting without inserting Fibonacci or the golden ratio into the code. Its admissible counts satisfy

```text
N(n) = N(n-1) + N(n-2)
```

and therefore `N(n+1)/N(n)` tends to the golden ratio. Its 63-bit frontier is 89 steps.

The exhaustive memory-2 scan tests all `3^4 = 81` laws and finds a discrete algebraic spectrum including the plastic constant, golden ratio, and tribonacci constant.

The exhaustive memory-3 scan tests all `3^8 = 6,561` laws and finds about 193 numerical growth classes at `1e-9` rounding. Selected class counts include:

```text
plastic constant: 524 laws
golden ratio:     264 laws
tribonacci:         12 laws
```

The golden ratio is recurrent but not uniquely privileged.

### 9. Robustness, Pareto, and orbit-style metrics

The project now separates several independent properties of a trajectory law:

```text
entropy rate          h = log2(lambda)
exact 63-bit frontier
rule robustness       mutation stability in law space
trajectory robustness survival under a one-bit state perturbation
state occupancy       normalized Perron-state entropy
mixing diagnostic     1 - |lambda2|/|lambda1|
error propagation     number/span of violated transitions after a bit flip
```

A representative balanced law emerged near

```text
lambda ~= 1.285199033245
h      ~= 0.361992 bit/step
63-bit frontier = 170 steps
```

It is not phi, plastic, or tribonacci. This is useful evidence against selecting constants by prior expectation.

Representative orbit-style metrics at 64 steps show a clear trade-off:

| law | lambda | frontier63 | occupancy | mixing gap | flip survival |
|---|---:|---:|---:|---:|---:|
| balanced 1.285199 | 1.285199 | 170 | 0.7398 | 0.1964 | 0.0329 |
| plastic | 1.324718 | 152 | 0.6341 | 0.2451 | 0.0300 |
| golden ratio | 1.618034 | 90 | 0.7463 | 0.3820 | 0.5590 |
| tribonacci | 1.839287 | 71 | 0.9230 | 0.4563 | 0.7691 |

These are representative rules, not universal properties of each spectral class.

See:

- `docs/local_law_scan_2026-08-19.md`
- `docs/local_law_memory3_scan_2026-08-19.md`
- `docs/law_robustness_memory3_2026-08-19.md`
- `docs/trajectory_perturbation_memory3_2026-08-19.md`
- `docs/pareto_memory3_2026-08-19.md`
- `docs/orbit_metrics_memory3_2026-08-19.md`

## Bounded-tree result

To create a genuinely structured family for `steps > width`, recursion must be able to **reject** trajectories instead of always subdividing until single-bit leaves.

A public depth limit provides one simple test. With width 63, `K=5`, and relation levels 0..3, the conservative address frontiers are:

| maximum tree depth | conservative frontier |
|---:|---:|
| 0 | 10,672 |
| 1 | 274 |
| 2 | 68 |
| 3 | 46 |
| 4 | 28 |

This is not yet the desired final architecture; it quantifies the cost of adaptive structural freedom.

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

The current target is to search for **stable computational universes** rather than a preferred constant:

```text
local law
 -> transition graph
 -> spectral growth
 -> admissible entropy
 -> occupancy/mixing
 -> robustness/error propagation
 -> exact trajectory address
```

The working question is whether there is a reproducible region between two extremes:

```text
too free       -> high entropy, weak compression of trajectory length
too constrained -> long frontier, rigid/fragile trajectory geometry
```

A useful law would preserve enough freedom to carry information while imposing enough structure to make long trajectories exactly reconstructible from a compact final address.

## Quick start

```bash
python experiments/local_law_memory3_scan.py
python experiments/law_robustness_memory3.py
python experiments/trajectory_perturbation_memory3.py --steps 64 --samples 2048 --seed 123
python experiments/pareto_memory3.py
python experiments/orbit_metrics_memory3.py --steps 64 --samples 1024 --seed 123
python experiments/local_law_scan.py
python experiments/admissibility_frontier.py
python -m unittest discover -s tests -v
```

NumPy is required for experiments that use eigendecomposition. Core exact codecs remain pure Python.

## License

Source-available for academic, educational, and non-commercial research use under `LICENSE`. Commercial exploitation requires a separate commercial license from the copyright holder.

Because the license restricts commercial use, this repository should **not** be described as OSI Open Source.
