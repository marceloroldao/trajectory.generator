# Hierarchical relational trajectory experiment — 2026-08-19

Status: pre-alpha constructive result
RSMS compatibility: pending central specification mapping

## Question

Can a trajectory be represented by relations between state changes rather than by one explicit final-state coordinate per raw input bit, while preserving exact recovery from only `(final_state, steps)`?

For arbitrary binary data, the answer cannot exceed the fixed-width information bound: a `w`-bit state cannot uniquely encode every arbitrary message with more than `w` independent bits.

The experiment therefore targets **structured trajectories** whose admissible family has lower entropy than their raw step count.

## Relational representation

A binary trajectory is represented by:

1. its initial bit;
2. the ordered positions at which the bit changes.

Example:

```text
000001111100000
```

is represented by the initial value `0` and two change positions.

For trajectory length `n` and at most `K` changes, the exact number of admissible trajectories is

```text
M(n,K) = 2 * sum(C(n-1, j), j=0..K)
```

for `n > 0`.

The complete constrained family is ranked combinatorially. The resulting rank is then passed through a public reversible affine universe permutation in the fixed-width state space. Decoding inverts the universe permutation and un-ranks the relational trajectory.

No trajectory log, side table, checksum, plaintext hint, or data-dependent external metadata is used.

## Capacity condition

Exact recovery is admitted only when

```text
M(n,K) <= 2^width
```

This is the correct information-theoretic criterion for the constrained family.

## 63-bit result

With:

- `width = 63`;
- `max_changes = 5`;

we obtain:

```text
capacity_ok(14082) = True
capacity_ok(14083) = False
```

Therefore a 63-bit final state can exactly address every binary trajectory of length up to **14,082 steps** in the public family containing at most five changes.

This does **not** mean 14,082 arbitrary bits were compressed into 63 bits. The admissible family is drastically smaller than `2^14082`; its information content is bounded by 63 bits by construction.

## Comparison with the linear trajectory address

### Linear trajectory address

- arbitrary bits supported;
- one fresh degree of freedom per bit;
- exact capacity: `steps <= width`;
- direct reversible decoding.

### Hierarchical / relational trajectory address

- structured trajectories only;
- stores relations (change positions), not every raw bit independently;
- can support `steps >> width` when the admissible family entropy remains <= width;
- exact decoding from `(final_state, steps)`.

The hierarchical method therefore provides a real advantage only when the trajectory itself has structure.

## Scientific interpretation

This experiment supports a narrower and more defensible statement than arbitrary compression:

> The amount of state required to address a trajectory depends on the number of admissible trajectories, not directly on the number of time steps.

Equivalently, long trajectories can fit into a small final address when their relational degrees of freedom are sparse enough.

This is consistent with the project's broader hypothesis that information can be represented by ordered transformations and relations between states.

## Reproduction

Run:

```bash
python -m unittest tests.test_hierarchical_trajectory -v
```

Key implementation:

```text
trajectory_generator/hierarchical_trajectory.py
```

## Next tests

1. Replace the simple bounded-change model with multi-level change trees.
2. Measure capacity for piecewise-periodic and repeated-motif trajectories.
3. Compare enumerative relation coding against conventional run-length and entropy coding baselines.
4. Test corruption sensitivity: how a one-bit final-state error changes decoded relations.
5. Keep the universe permutation ablated separately; it must not be credited for compression that comes from the constrained trajectory family.
6. Search for emergent orbit ratios only after the information accounting is explicit; no preferred constant is inserted into the encoder.
