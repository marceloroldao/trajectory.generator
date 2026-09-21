# Final-state-only reversible machine — 2026-09-20

## Milestone

For the three historical topological trajectory families, the project now has an
operational state machine whose public decode interface is exactly:

```text
decode(final_state, number_of_steps)
```

with the universe law/configuration fixed publicly.

The decoder is **not** given:

- original trajectory;
- current causal node;
- endpoint rank;
- recurrent-core entry node;
- branch history;
- trajectory table;
- time-indexed count table;
- full endpoint-count vector.

The causal path and original bit sequence are regenerated from the integer final
state, the public physical length, and the public universe law.

## State-machine interface

`trajectory_generator/seeded_graph_state_machine.py` exposes:

```text
advance(state, steps, bit)
    -> (new_state, new_steps)

rewind(state, steps)
    -> (previous_state, previous_steps, recovered_bit)

encode(bits)
    -> (final_state, steps)

decode(final_state, steps)
    -> bits
```

The current topological universe uses a public 3-bit bootstrap history.

Before the third bit, the state is the literal partial binary prefix.

At the third bit, that seed maps to one of the eight public lifted initial nodes.
From that point onward, the same integer is the graph trajectory address and
evolves by public affine translations.

## Forward law after bootstrap

For public edge `e` at physical transition time `t`:

```text
S_(t+1) = S_t + Delta(e,t)
```

The input bit selects the allowed public outgoing edge.

`Delta(e,t)` is independent of the trajectory-specific rank and is generated
from scalar partition laws obeying the public Floquet recurrence.

## Reverse law

Given only:

```text
S_(t+1), t+1
```

the decoder:

1. regenerates scalar endpoint boundaries;
2. identifies the current public graph node;
3. regenerates scalar incoming-edge boundaries;
4. identifies the previous edge;
5. recovers the bit associated with that edge;
6. computes:

```text
S_t = S_(t+1) - Delta(e,t)
```

and repeats.

The three bootstrap bits are recovered when reverse reaches the initial lifted
state.

## Executed gate

GitHub Actions run:

```text
35552480599
workflow: reversible-pipeline-gate
conclusion: success
```

All 11 workflow gates passed.

The end-to-end result was:

```text
robust_208
  PASS=True
  frontier=208
  frontier family=8,484,982,157,878,442,411
  next family=10,357,991,777,215,491,665
  small addresses checked=288
  frontier samples=5
  decode inputs=(final_state,steps)+public_law_only
  exhaustive roundtrip=True
  frontier roundtrip=True
  next over capacity=True

balanced_221
  PASS=True
  frontier=221
  frontier family=9,131,204,053,820,206,208
  next family=10,214,739,716,735,776,832
  small addresses checked=270
  frontier samples=5
  decode inputs=(final_state,steps)+public_law_only
  exhaustive roundtrip=True
  frontier roundtrip=True
  next over capacity=True

long_239
  PASS=True
  frontier=239
  frontier family=8,736,326,121,603,609,111
  next family=9,803,398,575,756,969,808
  small addresses checked=234
  frontier samples=5
  decode inputs=(final_state,steps)+public_law_only
  exhaustive roundtrip=True
  frontier roundtrip=True
  next over capacity=True
```

Since:

```text
2^63 = 9,223,372,036,854,775,808
```

the next admissible family is larger than the 63-bit address space in all three
cases.

## Why the frontier test is stronger than encode/decode roundtrip

The frontier gate does not begin only from trajectories that were first encoded.

It selects final integer addresses directly from the admissible address space:

```text
0
N/4
N/2
3N/4
N-1
```

for the complete frontier family of size `N`.

For each integer:

```text
final integer
    -> decode
    -> admissible trajectory
    -> encode
    -> same final integer
```

This rejects a weak implementation that only knows how to reverse states it
recently produced.

## Count-field dependency

The scalar partition gate in the same successful run explicitly disabled the
full-vector API:

```text
full_vector_api_disabled=True
```

and still reproduced the frontier paths.

Executed scalar results:

```text
robust_208
  checked low-horizon addresses=2,255
  frontier path identity=True

balanced_221
  checked low-horizon addresses=1,965
  frontier path identity=True

long_239
  checked low-horizon addresses=1,956
  frontier path identity=True
```

Therefore the final-state-only machine does not depend operationally on
reconstructing `D(.,t)` as a complete vector at the queried time.

## Precise interpretation

This result meets the project's **operational target** for the tested
constrained trajectory families:

> given the final trajectory state, physical length, and fixed public universe
> law, regenerate the original admissible trajectory exactly.

It does not violate the information bound. The admissible trajectory family at
the frontier still contains at most `2^63` members.

It also does not show that the old raw causal node

```text
(history_3bit, topology_3bit, phase)
```

contains the whole past.

The reversible final state is the **63-bit enumerative trajectory coordinate**.
The raw causal node is a public projection/partition of that coordinate.

This distinction should remain explicit in every scientific claim.

## Architectural view

The tested system can now be represented as:

```text
public universe law
       |
       +-> small Floquet recurrence
       |       |
       |       +-> scalar bucket boundaries
       |       +-> scalar Delta(edge,t)
       |
input bit
       |
       v
one integer state S
       |
       v
S' = S + Delta
```

Reverse:

```text
(final S, steps)
       |
       v
public scalar partitions
       |
       v
previous edge + recovered bit
       |
       v
S_prev = S - Delta
       |
      ...
       |
       v
original bit trajectory
```

## What remains unresolved

There are now two different goals, and they should not be conflated.

### Operational goal

For the tested admissible universe families:

```text
(final_state, steps) -> trajectory
```

is achieved.

### Strong ontological goal

The stronger hypothesis would require the universe's *native causal state
geometry itself* to carry the reversible coordinate, rather than attaching an
explicit enumerative coordinate generated from path counts.

That stronger goal is not yet demonstrated.

The next research gate should quantify exactly how much historical information
the old raw causal node loses at the current frontiers and determine the minimum
additional state dimension required for a native reversible universe.
