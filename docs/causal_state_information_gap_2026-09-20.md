# Causal-state information gap — 2026-09-20

## Question

After reaching exact recovery from `(final_state, steps)`, the next question is
whether the explicit trajectory address can simply be removed and the old raw
causal state can recover the same histories.

For the topological universe, the raw phase-lifted causal node is:

```text
(history_3bit, topology_3bit, phase)
```

At known physical time the phase is public, so the non-time causal payload has
at most:

```text
3 history bits + 3 topology bits = 6 bits
```

This experiment measures how many distinct admissible histories merge into each
raw causal node at the 63-bit frontier.

## Information identity

Let `C_v` be the number of admissible trajectories ending at raw node `v`,
and let:

```text
N = sum_v C_v.
```

Under the uniform distribution over admissible trajectories:

```text
H(path) = log2(N)

H(raw_node)
  = -sum_v (C_v/N) log2(C_v/N)

H(path | raw_node)
  = sum_v (C_v/N) log2(C_v)
```

The experiment verifies numerically:

```text
H(path)
  = H(raw_node) + H(path | raw_node)
```

to floating-point precision.

## Executed gate

GitHub Actions run:

```text
35552632658
workflow: reversible-pipeline-gate
conclusion: success
```

### robust_208

```text
frontier trajectories
  8,484,982,157,878,442,411

total trajectory entropy
  62.879617334061 bits

active raw nodes
  14

raw-node endpoint entropy
  3.524457826894 bits

history entropy still missing after raw node is known
  59.355159507167 bits

largest number of histories sharing one raw node
  1,143,377,287,880,525,663

minimum worst-case extra bits for that node
  60 bits

raw nodes with immediate predecessor ambiguity
  6

fraction of trajectories ending at immediately ambiguous nodes
  0.598428428790
```

### balanced_221

```text
frontier trajectories
  9,131,204,053,820,206,208

total trajectory entropy
  62.985510816588 bits

active raw nodes
  12

raw-node endpoint entropy
  3.214604833128 bits

history entropy still missing after raw node is known
  59.770905983460 bits

largest number of histories sharing one raw node
  2,754,405,653,601,624,727

minimum worst-case extra bits for that node
  62 bits

raw nodes with immediate predecessor ambiguity
  2

fraction of trajectories ending at immediately ambiguous nodes
  0.358708176513
```

### long_239

```text
frontier trajectories
  8,736,326,121,603,609,111

total trajectory entropy
  62.921732420141 bits

active raw nodes
  10

raw-node endpoint entropy
  2.184323259988 bits

history entropy still missing after raw node is known
  60.737409160153 bits

largest number of histories sharing one raw node
  3,627,481,408,934,513,129

minimum worst-case extra bits for that node
  62 bits

raw nodes with immediate predecessor ambiguity
  4

fraction of trajectories ending at immediately ambiguous nodes
  0.914073515768
```

## Consequence

The old raw causal node does not merely make reverse decoding inconvenient.

It has **already merged** enormous numbers of distinct admissible histories.

For example, in `long_239`, one identical raw node represents more than:

```text
3.6 * 10^18
```

different admissible pasts.

No deterministic function of that raw node alone can recover which one occurred.

The missing information is not hidden by an inefficient decoder. It is absent
from the state.

## What a native reversible universe must do

A future native reversible causal state must carry enough additional degrees of
freedom to distinguish the histories that would otherwise merge.

At the current frontiers, the worst raw node requires an auxiliary state space
of at least:

```text
robust_208     1,143,377,287,880,525,663 states  -> 60 bits
balanced_221   2,754,405,653,601,624,727 states  -> 62 bits
long_239       3,627,481,408,934,513,129 states  -> 62 bits
```

Thus the trajectory address is not arbitrary bookkeeping that can be deleted
while leaving the 6-bit causal payload unchanged.

Equivalent historical information must exist somewhere in the state geometry.

## Horizontal/vertical interpretation

The natural decomposition is:

```text
horizontal coordinate:
  raw causal node v

vertical coordinate:
  history rank r in 0 .. C_v-1
```

So a lifted state is:

```text
(v, r)
```

and the packed 63-bit trajectory address is simply an enumerative coordinate
over these fibers.

This gives a precise mathematical meaning to a multilayer interpretation:

- horizontal motion follows the public causal graph;
- vertical position distinguishes histories merged by the horizontal node;
- incoming causal edges occupy disjoint vertical sub-fibers;
- reverse identifies the sub-fiber and returns to the predecessor fiber.

This geometry is implemented by
`trajectory_generator/reversible_fiber_lift.py`.

## Research implication

The stronger ontological target should no longer be stated as:

> recover 63 bits of lost history from a 6-bit raw node.

That is impossible for the complete frontier family.

The meaningful stronger target is:

> construct the universe so the required vertical coordinate is an intrinsic
> causal degree of freedom rather than an externally interpreted enumerative
> label.

The information cannot disappear. The research question is how naturally the
universe can carry it.
