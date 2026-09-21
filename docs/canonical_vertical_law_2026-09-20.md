# Canonical coefficient-free vertical law — 2026-09-20

## Result

The earlier periodic vertical lift proved that a nontrivial vertical coordinate
can evolve reversibly, but its drive used hand-chosen numerical mixing
constants.

That arbitrariness has now been removed.

The accepted vertical law is:

```text
sigma(t) = (-1)^(t mod P)
b(e)     = incoming_index(e)

local' = (sigma(t) * y + b(e)) mod |F(source,t)|
y'     = incoming_offset(e,t) + local'
```

For the current topological universes:

```text
P = 3
```

so the orientation pattern is:

```text
phase 0 -> +1
phase 1 -> -1
phase 2 -> +1
```

and the rotation is simply the public ordinal of the predecessor edge inside
the target fiber partition.

No fitted constants remain.

## Restricted law grammar

The search intentionally permits only unit-coefficient primitives.

Temporal orientation features:

```text
phase = t mod P
cycle = floor((t mod P_vertical)/P)
```

Structural rotation features:

```text
incoming_index
outgoing_index
source_branch_excess
target_merge_excess
```

The allowed law form is:

```text
sigma = (-1)^(sum(selected temporal features) mod 2)
b     = sum(selected structural features)
```

Allowed public periods are:

```text
P, 2P, 4P
```

No arbitrary integer coefficient, hash, random seed, candidate-specific value,
or trajectory-dependent parameter is allowed.

## Search result

GitHub Actions run:

```text
35553843921
workflow: reversible-pipeline-gate
conclusion: success
```

The search accepted the **first minimum-description candidate**:

```text
period_multiple      = 1
vertical_period      = P = 3
orientation_features = (phase,)
shift_features       = (incoming_index,)
term_count           = 2
```

The search therefore did not need `2P` or `4P`.

Executed activity:

```text
robust_208
  orientation flips      110
  non-zero rotations      81
  nontrivial maps         123

balanced_221
  orientation flips       85
  non-zero rotations      66
  nontrivial maps         108

long_239
  orientation flips       83
  non-zero rotations      46
  nontrivial maps          85
```

The full gate passed for all three candidates with:

- exact periodicity;
- exact reversibility;
- exact projection onto the original causal graph;
- complete frontier predecessor partition;
- exact frontier roundtrip.

## Structural derivation

The same frozen law can be derived from two explicit axioms.

### Axiom 1 — temporal orientation

Orientation must be:

- non-constant;
- public;
- periodic;
- defined with the smallest public period.

At period `P`, the only non-constant temporal primitive in the restricted
grammar is:

```text
phase = t mod P
```

Therefore:

```text
sigma = (-1)^phase
```

### Axiom 2 — target-partition rotation

The vertical coordinate belongs to the target causal fiber.

When several causal predecessors merge into the same target node, that fiber is
partitioned into incoming edge sub-fibers.

The canonical edge-local coordinate of that partition is:

```text
incoming_index
```

The other primitive structural quantities do not play that exact role:

- `outgoing_index` indexes the source branch;
- `source_branch_excess` is constant at the source node;
- `target_merge_excess` is constant for all incoming edges of one target.

Therefore the minimal target-partition rotation is:

```text
b = incoming_index
```

The implementation freezes this result as:

```text
CANONICAL_PHASE_MERGE_SPEC
```

and verifies that the structural derivation returns the same law.

## Final-state-only dynamic vertical machine

The canonical law was then integrated into:

```text
trajectory_generator/canonical_vertical_state_machine.py
```

Its public decoder remains:

```text
decode(final_state, steps)
```

with only the fixed public universe law supplied externally.

GitHub Actions run `35553978845` passed:

```text
robust_208
  frontier                  208
  frontier family           8,484,982,157,878,442,411
  small addresses checked   288
  frontier roundtrip        true
  rank mapping changed      5/5 samples

balanced_221
  frontier                  221
  frontier family           9,131,204,053,820,206,208
  small addresses checked   270
  frontier roundtrip        true
  rank mapping changed      5/5 samples

long_239
  frontier                  239
  frontier family           8,736,326,121,603,609,111
  small addresses checked   234
  frontier roundtrip        true
  rank mapping changed      5/5 samples
```

The `5/5` changed mappings are important.

For each sampled final integer, the canonical vertical machine recovered a
different admissible trajectory than the old static rank codec, while
re-encoding returned to the exact same integer.

Therefore the new vertical coordinate is not merely the old rank under a new
name.

## Current interpretation

The lifted state is now:

```text
(horizontal causal node, vertical dynamic coordinate)
```

Horizontal evolution follows the original public causal graph.

Vertical evolution is:

```text
orientation <- public phase
rotation    <- predecessor position in target partition
```

This is substantially more constrained than the previous designed period-6
mixer.

## Remaining boundary

The law is now coefficient-free and structurally motivated, but the axioms
themselves are still design choices.

The next stronger test is to determine whether the same phase/merge law can be
derived from a more general principle, such as:

- minimal reversible extension of a many-to-one causal map;
- natural ordering of predecessor fibers;
- information-clock branch/merge duality;
- categorical or automata-theoretic reversible completion.

That would move the result from a compact engineered law toward a law forced by
the reversible completion problem itself.

## Correction after the general reversible-completion gate

Later experiments generalized the lift beyond the three topological candidates and established an important limitation on the word **canonical**.

Minimal reversibility forces:

- fiber cardinalities;
- predecessor-edge image cardinalities;
- disjoint predecessor partitions;
- bijective recoverability of histories.

It does **not** force one unique numerical permutation inside each edge image whenever a fiber has more than one state.

Identity, reflection, phase reflection, and the phase/merge law can all be exact gauges of the same coordinate-free history dynamics.

The natural-extension gate verifies the conjugacy relation between such gauges.

Therefore `CANONICAL_PHASE_MERGE_SPEC` should now be read as:

```text
a canonical gauge under the restricted ordered-graph grammar
```

not as a unique consequence of reversible completion.

The newer preferred intrinsic gauge removes the predecessor-index rotation from the internal dynamics:

```text
sigma(t) = (-1)^(t mod P)
b        = 0
```

and leaves incoming-edge ordering only in the integer serialization of predecessor blocks.

See:

- `docs/general_minimal_reversible_completion_2026-09-20.md`
- `docs/intrinsic_phase_reflection_2026-09-20.md`
