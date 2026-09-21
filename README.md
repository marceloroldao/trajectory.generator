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

The selector weights themselves change deterministically with `(history, phase)`. No policy sequence is stored externally.

A moderate-entropy second-order policy remains at the 184-step balanced frontier while using more active laws. This is an important negative result: adding selector hierarchy increases internal diversity but does not automatically improve capacity.

### 12. Accumulated coherence-memory universe

`trajectory_generator/coherence_memory_universe.py`

The causal grammar state is now:

```text
(history_3bit, coherence_bucket, public_phase)
```

The coherence bucket is a deterministic finite memory of the recovered path and is never supplied as side metadata. An exhaustive scan of all `3 * 5^4 = 1,875` four-bucket configurations found two useful reference points.

Balanced profile:

```text
update_mode = rolling
policy_map  = (1, 3, 4, 0)
187 steps -> 8,070,450,532,247,928,961 trajectories
188 steps -> 16,140,901,064,495,857,795 trajectories
rate300 ~= 0.3360245 bit/step
sampled one-bit survival ~= 32.80%
```

This is a modest Pareto improvement over the earlier 184-step balanced universe while retaining similar perturbation tolerance.

Capacity-oriented extreme:

```text
update_mode = signed_bit
policy_map  = (4, 0, 2, 1)
244 steps -> 8,887,676,923,343,977,346 trajectories
245 steps -> 14,225,417,450,507,601,237 trajectories
rate300 ~= 0.2570568 bit/step
sampled one-bit survival ~= 1.31%
```

The 244-step profile is deliberately not the default because its much longer frontier is purchased with severe structural fragility.

See `docs/coherence_memory_universe_2026-08-20.md`.

### 13. Controlled memory-order comparison

`experiments/memory_order_compare.py` and `experiments/memory_order_multiseed.py`

Local history orders 2, 3, and 4 were compared while holding the candidate-law-bank size fixed. This is necessary because the complete rule spaces grow as:

```text
memory 2 -> 81 laws
memory 3 -> 6,561 laws
memory 4 -> 43,046,721 laws
```

Across eight deterministic canonical banks, no monotonic relation of the form `more local memory -> better universe` was observed. Memory 4 explores a wider range of entropy/frontier regimes, but remains much more fragile in the tested sample. Memory 3 is the only order that repeatedly reproduced the balanced region near:

```text
frontier = 187
rate300 ~= 0.334 .. 0.336 bit/step
one-bit survival ~= 31 .. 33%
```

See `docs/memory_order_multiseed_2026-08-22.md`.

### 14. Hybrid memory 3<->4 experiment

`experiments/hybrid_memory34_search.py`

The machine always carries four recent bits but exposes memory-4 to the active grammar only when the reconstructed coherence bucket belongs to a public critical set. No switch history is stored.

The hybrid can extend the frontier, but does not improve the balanced Pareto point. Representative results include:

```text
286 steps, rate300 ~= 0.21964, one-bit survival ~= 2.02%
247 steps, rate300 ~= 0.25009, one-bit survival ~= 2.51%
234 steps, rate300 ~= 0.26653, one-bit survival ~= 3.99%
206 steps, rate300 ~= 0.30006, one-bit survival ~= 5.22%
```

All are much more fragile than the memory-3 balanced reference at 187 steps and ~32.8% one-bit survival. The hybrid is therefore preserved as a negative result and is not promoted into the public codec API.

See `docs/hybrid_memory34_2026-08-24.md`.

### 15. Recurrent orbit core and information clock

`experiments/recurrent_orbit_core.py` and `experiments/information_clock_macrograph.py`

A topological transition-state candidate with frontier around 221 steps has a dominant recurrent core of only 14 phase-lifted causal states. Inside that core there are just two states with more than one internal successor.

Collapsing deterministic flights between those two branch states produces a two-state variable-length macrograph with four macro edges:

```text
A -> B : 1 physical step
A -> A : 12 physical steps
B -> A : 2 physical steps
B -> A : 5 physical steps
```

The macrograph exactly reproduces the dominant physical-time growth factor through

```text
lambda^12 - lambda^9 - lambda^6 - 1 = 0
lambda ~= 1.206189700118
log2(lambda) ~= 0.270456820917 bit / physical step
```

Under the maximal-entropy path measure, one branch event spans about 2.59856 physical steps on average and carries about 0.70280 bit of entropy. Their ratio returns the same physical-time information rate.

This gives the project an explicit distinction between physical time `t` and information-event time `k`: most intermediate transitions are deterministic consequences of the public dynamics; entropy enters at branch events.

See `docs/recurrent_orbit_core_2026-09-02.md` and `docs/information_clock_macrograph_2026-09-02.md`.

### 16. Algebraic root trajectory

`trajectory_generator/algebraic_root_trajectory.py` and
`experiments/algebraic_root_trajectory_gate.py`

For a trajectory with at most `K` innovation events, the state is a monic
degree-`K` polynomial over a public prime field:

```text
P(z) = z^(K-r) * product(z - (t_i + 1))
```

An innovation replaces one zero root with the current public step address.
Reverse decoding is local:

```text
e_t = 1  iff  P_(t+1)(t+1) = 0 mod p
```

If the root is present, synthetic division removes it and multiplication by
`z` restores the predecessor. The decoder therefore needs only current state,
public time, and public universe parameters; it does not reconstruct the
reachable manifold or consult a trajectory table.

For `K=5`, reference packed-state frontiers include:

```text
W=63  -> 6,202 steps
W=128 -> 50,858,998 steps
```

The representation is not information-theoretically optimal, but for fixed
`K` its asymptotic redundancy is only about `log2(K!)` bits
(`~6.9069` bits for `K=5`). Reverse work is `O(K)` per physical step.

See `docs/algebraic_root_trajectory_2026-09-20.md`.

### 17. Streaming colex trajectory

`trajectory_generator/streaming_colex_trajectory.py` and
`experiments/streaming_colex_trajectory_gate.py`

This is an operational refinement of the hierarchical trajectory family, not a
new admissible family. It keeps the exact count

```text
M(n,K) = 2 * sum(C(n-1,j), j=0..K)
```

but replaces batch combination rank/unrank with a step-by-step colex state.

For an exact-`r` change set among `n` public positions, the newest position is
present iff the within-bucket colex address lies in the public suffix:

```text
c >= C(n-1,r)
```

That gives a local reverse decision from current address, public step count, and
`K`. No list of change positions is reconstructed.

For `W=63, K=5`:

```text
frontier       = 14,082 steps
valid states   = 9,222,784,404,533,559,556
2^63           = 9,223,372,036,854,775,808
occupancy      ~= 99.9936289%
14,083 steps   = over capacity
```

So the construction preserves the exact information-theoretic frontier of the
hierarchical family while making forward and reverse evolution operational one
physical step at a time.

See `docs/streaming_colex_trajectory_2026-09-20.md`.

### 18. Streaming weighted information-clock address

`trajectory_generator/weighted_path_trajectory.py` and
`experiments/information_clock_streaming_codec.py`

The two-state information-clock macrograph is now operationally addressable.
For a public weighted macrograph, exact-length paths ending at each branch state
are counted by a public dynamic program. Incoming macro-edges define contiguous
rank blocks.

Forward evolution inserts the predecessor rank into the selected edge block;
reverse evolution identifies the last macro-edge from the block containing the
current rank. The deterministic physical path attached to that public edge is
then regenerated rather than stored.

For the current macrograph with physical edge lengths `1, 12, 2, 5`, the first
branch-aligned exact-length family that exceeds 63 bits occurs at physical time
234. The branch-aligned streaming frontier is therefore 233 physical steps.
This result applies to prefixes ending on macrograph branch nodes; section 19
adds the physical-step codec required for prefixes that stop inside a
deterministic flight.

See `docs/information_clock_streaming_codec_2026-09-20.md`.

### 19. Automatic endogenous recurrent pipeline

`trajectory_generator/recurrent_macrograph.py` and
`experiments/automatic_endogenous_pipeline_gate.py`

The recurrent-address pipeline is now derived directly from the public universe
graph. No branch symbols or macro-edge lengths are supplied manually.

The pipeline performs:

```text
public universe
    -> SCC decomposition
    -> dominant recurrent core
    -> branch-node detection
    -> deterministic-flight collapse
    -> weighted information-clock macrograph
    -> exact physical-step reversible address
```

A second codec is built directly on every physical transition inside the
selected recurrent core. This removes a limitation of the earlier weighted
macrograph codec: the final state may now occur at **any physical step**,
including in the middle of a deterministic flight.

For the three historical topological candidates, automatic extraction gives:

```text
candidate      core   branches   macro lengths
robust_208      24       6       3x6, 4x6
balanced_221    14       2       1, 2, 5, 12
long_239         8       1       3, 6
```

With every recurrent-core node treated as an admissible initial state, the
63-bit physical-core frontiers are:

```text
robust_208    203 steps   occupancy ~= 99.8107%
balanced_221  219 steps   occupancy ~= 94.9595%
long_239      259 steps   occupancy ~= 93.6773%
```

These are core-only operational frontiers and are not replacements for the
historical whole-universe frontier numbers in the candidate names.

See `docs/automatic_endogenous_recurrent_pipeline_2026-09-20.md`.

### 20. Full-universe streaming graph address

`trajectory_generator/public_graph_trajectory.py` and
`experiments/full_universe_streaming_codec.py`

The phase-lifted topological universe can now be addressed directly as one
public finite-state graph. The codec starts from the eight public lifted states
corresponding to the initial three-bit histories and evolves one graph edge per
additional physical bit.

For every node `v` and transition time `t`, public path counts define incoming
rank blocks. Forward evolution inserts the predecessor address into the selected
edge block; reverse evolution identifies the previous edge from the block
containing the current address.

The streaming counts are identical, step by step, to the historical batch
universe counts and recover the same 63-bit frontiers:

```text
robust_208    -> 208 steps
balanced_221  -> 221 steps
long_239      -> 239 steps
```

Small-horizon exhaustive comparison also gives the same trajectory language as
the historical batch unranker.

This removes the need for a special transient-to-core address handoff. The
recurrent-core and information-clock analyses remain valuable for exposing the
geometry of where entropy enters, but the exact address can run over the entire
public graph.

Important distinction: the final integer is a constructed **enumerative address
state derived from the universe laws**. This result does not claim that the raw
causal node `(history, topology, phase)` alone contains the complete past.

See `docs/full_universe_streaming_trajectory_2026-09-20.md`.

### 21. Floquet count-field recurrence

`trajectory_generator/count_field_recurrence.py`,
`trajectory_generator/floquet_count_field.py`, and
`experiments/floquet_count_field_gate.py`

The full-universe graph address no longer requires a count table that grows with
physical time.

The exact endpoint-count vector obeys a finite Krylov recurrence derived from
the public graph. Because the topological universe is phase-lifted modulo 3, the
recurrence is compressed further onto the phase-0 Floquet slice.

Measured minimum recurrence orders:

```text
candidate      full order   phase-0 states   Floquet order
robust_208         31             16              11
balanced_221       23             13               8
long_239           22             12               8
```

The seed Krylov basis is used only during derivation and is then discarded.
During reverse decoding, a short fixed Floquet window walks backward together
with the trajectory.

GitHub Actions run `35551989944` passed the complete gate with unchanged
languages, addresses, and frontiers:

```text
robust_208    -> 208
balanced_221  -> 221
long_239      -> 239
```

Estimated resident count-integer reductions versus retaining every reachable
time row through the frontier:

```text
robust_208     ~29.16x
balanced_221   ~34.33x
long_239       ~41.54x
```

These ratios compare count integers, not Python heap bytes.

See `docs/floquet_count_field_recurrence_2026-09-20.md`.

### 22. Affine translation address dynamics

`trajectory_generator/translation_address_trajectory.py` and
`experiments/translation_address_gate.py`

The streaming address update has the exact affine form:

```text
S_(t+1) = S_t + Delta(edge,t)
```

`Delta` depends only on the public edge, public time, and public universe law;
it is independent of the trajectory-specific rank. Reverse identifies the
incoming edge and subtracts the same translation.

For every reachable physical edge in all three topological candidates, the
phase-aligned `Delta` sequence obeys the same Floquet recurrence as the public
count field. GitHub Actions run `35552165365` passed rank-independence,
translation-recurrence, and full-path identity gates through frontiers
`208 / 221 / 239`.

See `docs/translation_address_dynamics_2026-09-20.md`.

### 23. Scalar partition reverse

`trajectory_generator/scalar_floquet_partition.py` and
`trajectory_generator/scalar_partition_trajectory.py`

Reverse decoding no longer needs to materialize the full endpoint-count vector
at the queried time. Endpoint boundaries, incoming-edge block sizes, and affine
translations are evaluated directly as scalar linear functionals of the Floquet
count field.

The acceptance gate explicitly disables `field.vector_at()`. GitHub Actions
run `35552323533` still passed exact frontier-path identity and exhaustive
low-horizon address identity for all three topological candidates.

See `docs/scalar_partition_reverse_2026-09-20.md`.

### 24. Final-state-only reversible machine

`trajectory_generator/seeded_graph_state_machine.py` and
`experiments/final_state_only_gate.py`

The operational decode interface is now:

```text
decode(final_state, number_of_steps)
```

with the universe law fixed publicly.

No causal node, trajectory rank, branch history, core-entry state, trajectory
table, time-indexed count table, or full count vector is supplied to decode.

GitHub Actions run `35552480599` passed the end-to-end gate:

```text
robust_208    -> frontier 208
balanced_221  -> frontier 221
long_239      -> frontier 239
```

The frontier test starts from integer addresses selected directly from the final
address space, decodes them, and requires re-encoding to reproduce the exact
same integer.

This achieves the project's operational `(final_state, steps) -> trajectory`
target for these constrained admissible families. The final state is a
constructed 63-bit enumerative trajectory coordinate; it is not the old raw
causal node by itself.

See `docs/final_state_only_reversible_machine_2026-09-20.md`.

### 25. Causal information gap and minimal reversible lift

`experiments/causal_state_information_gap.py`,
`trajectory_generator/reversible_fiber_lift.py`, and
`trajectory_generator/lifted_causal_universe.py`

At the 63-bit frontiers, the old raw causal node retains only a few bits of
which-history information while many admissible trajectories merge into the same
node.  The missing history cannot be recovered from the raw node alone.

The reversible completion therefore lifts each raw node `v` at time `t` into
a vertical fiber of exactly `D(v,t)` states.  This lift is fiberwise minimal:
fewer states above `v` would necessarily merge at least two admissible
histories.

GitHub Actions run `35553256436` passed the minimal-lift gate with exact
semiconjugacy, reversibility, and complete target-fiber partitioning through the
historical frontiers.

See `docs/causal_state_information_gap_2026-09-20.md`.

### 26. Endogenous periodic vertical dynamics

`trajectory_generator/endogenous_vertical_dynamics.py` and
`experiments/endogenous_vertical_dynamics_gate.py`

The vertical fiber coordinate is no longer transported as an identity rank.
For public edge `e` and source-fiber size `n`:

```text
local' = (sigma(e,t) * y + b(e,t)) mod n
y'     = incoming_offset(e,t) + local'
```

with `sigma in {+1,-1}`.

The drive is regenerated from local causal graph invariants and a public
vertical phase.  The current topological universes have causal period `P=3`
and use vertical period `2P=6`, so repeated visits to the same causal phase
alternate between two vertical phases.

Using only `+1/-1` orientation guarantees a permutation for every positive
fiber size; no `gcd(a,n)=1` condition is required while fiber cardinalities
change.

GitHub Actions run `35553256436` passed all gates.  The periodic vertical gate
verified:

```text
candidate      nontrivial maps   orientation flips   frontier roundtrip
robust_208          1,216               390                 true
balanced_221        1,054               294                 true
long_239            1,062               264                 true
```

It also verified exact periodicity of the drive, exact lifted reversibility,
complete frontier sub-fiber partitioning, and projection onto the original
causal graph.

The current mixing constants are frozen design choices, not an emergent result.
The next research step is to derive the vertical drive from existing universe
modes or branch geometry instead of arbitrary mixing coefficients.

See `docs/endogenous_periodic_vertical_dynamics_2026-09-20.md`.

### 27. Canonical coefficient-free vertical law

`trajectory_generator/canonical_vertical_law.py`,
`trajectory_generator/canonical_vertical_state_machine.py`,
`experiments/canonical_vertical_law_search.py`, and
`experiments/canonical_vertical_final_state_gate.py`

The vertical law no longer uses hand-chosen numerical mixing constants.

A restricted grammar permits only:

- temporal orientation from public phase/cycle;
- structural rotation from canonical causal edge/node ordinals;
- unit coefficients;
- periods `P`, `2P`, or `4P`.

The first minimum-description law already passes all three historical
topological universes:

```text
sigma(t) = (-1)^(t mod P)
b(e)     = incoming_index(e)
P        = 3
```

so:

```text
local' = (sigma*y + b) mod source_fiber_size
```

before embedding into the incoming-edge sub-fiber of the target node.

GitHub Actions run `35553843921` passed exact periodicity, reversibility,
causal projection, frontier partitioning, and full frontier roundtrip.

The same run then validated the **dynamic vertical final-state machine**:
`decode(final_state, steps)` still recovers the admissible bit trajectory and
re-encoding returns the exact same final integer at frontiers `208 / 221 / 239`.

For every frontier candidate, all five sampled final integers mapped to a
different trajectory than the old static rank codec. Thus the vertical
coordinate is operationally dynamic, not passive rank transport.

The frozen law also has a structural derivation:

1. minimum-period non-constant orientation -> public `phase`;
2. target-fiber predecessor partition coordinate -> `incoming_index`.

See `docs/canonical_vertical_law_2026-09-20.md`.

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

The operational target remains satisfied:

```text
(final_state, steps, public universe law)
    -> exact admissible trajectory
```

The stronger native-state program has now reached a simpler form than the
earlier period-6 mixer.

The reversible universe is represented as:

```text
horizontal = original public causal node
vertical   = minimal history-distinguishing causal coordinate
```

and the vertical coordinate has its own coefficient-free periodic dynamics:

```text
sigma(t) = (-1)^(t mod P)
b(e)     = incoming_index(e)
P        = 3
```

This law is enough to preserve exact reversibility and exact projection through
the historical frontiers `208 / 221 / 239`. It also changes the mapping
between final integers and trajectories relative to the old static rank codec,
while preserving final-state-only recovery.

The main unresolved question has therefore narrowed again. It is no longer
whether the vertical coordinate can have a native reversible dynamics; it can.
It is whether the phase/merge law can be shown to follow from a **general
minimal reversible-completion principle**, rather than from two explicit design
axioms.

The next research direction should formalize that principle: characterize the
minimal reversible extension of a finite many-to-one causal graph, and determine
whether phase orientation plus predecessor-partition rotation appears as a
canonical or unique completion under natural symmetry/locality constraints.

## Quick start

```bash
python experiments/canonical_vertical_law_search.py
python experiments/canonical_vertical_final_state_gate.py
python experiments/causal_state_information_gap.py
python experiments/reversible_fiber_lift_gate.py
python experiments/minimal_reversible_causal_lift_gate.py
python experiments/endogenous_vertical_dynamics_gate.py
python experiments/translation_address_gate.py
python experiments/scalar_partition_gate.py
python experiments/final_state_only_gate.py
python experiments/floquet_count_field_gate.py
python experiments/count_field_recurrence_gate.py
python experiments/full_universe_streaming_codec.py
python experiments/automatic_endogenous_pipeline_gate.py
python experiments/information_clock_streaming_codec.py
python experiments/streaming_colex_trajectory_gate.py
python experiments/algebraic_root_trajectory_gate.py
python experiments/information_clock_macrograph.py
python experiments/recurrent_orbit_core.py
python experiments/hybrid_memory34_search.py --bank-size 256 --seed 12648430
python experiments/memory_order_multiseed.py --bank-size 256 --seeds 8 --base-seed 12648430
python experiments/memory_order_compare.py --bank-size 256 --seed 12648430
python experiments/coherence_memory_search.py --samples 64 --seed 123
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
