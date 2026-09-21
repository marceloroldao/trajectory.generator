# Automatic endogenous recurrent pipeline — 2026-09-20

## Objective

Remove the manually assembled information-clock layer.

The pipeline now starts from the public transition graph of an endogenous
universe and derives, automatically:

```text
public universe graph
    -> strongly connected components
    -> dominant recurrent core
    -> branch states
    -> deterministic flights
    -> weighted information-clock macrograph
    -> exact physical-step reversible address
```

The operational address no longer assumes that a trajectory stops exactly on a
branch event.

## Important correction to the previous weighted codec

`information_clock_streaming_codec.py` encoded complete macro-edges and was
therefore **branch-aligned**: it represented prefixes whose final physical time
landed on a macrograph branch node.

That construction remains valid as an information-clock codec, but it is not by
itself sufficient for the global target `(final_state, physical_steps)` because
a trajectory may stop in the middle of a deterministic flight.

`recurrent_macrograph.py` fixes this by building a second codec directly on all
physical transitions inside the selected recurrent core. Every internal edge
has physical length 1.

As a result, every physical stopping time is addressable.

## Automatic core extraction

The new library code performs Tarjan SCC decomposition and keeps recurrent
components. The dominant component is selected by asymptotic internal path
growth using exact integer path counts and an nth-root growth estimate.

For the current historical candidates, the automatic extraction produces:

```text
candidate      core nodes   branch nodes   macro edges   macro lengths
robust_208          24            6            12        3x6, 4x6
balanced_221        14            2             4        1, 2, 5, 12
long_239             8            1             2        3, 6
```

The balanced candidate reproduces the earlier manually extracted macrograph.

## Physical-step reversible address

For every core node `v` and physical time `t`, the weighted path codec counts
the number of exact physical paths that end at `v`.

Because every physical edge has length 1, the state partitions are valid at
every physical time, including nodes inside deterministic flights.

Reverse decoding uses only:

- current integer address;
- current physical step count;
- the public recurrent-core graph.

The endpoint bucket identifies the current core node. The incoming-edge rank
block identifies the unique previous physical edge. Removing that block offset
produces the predecessor address.

Repeating the operation regenerates the complete physical core trajectory.

## 63-bit core-only reference results

The default gate encodes the initial core node as part of the address by
allowing every node of the selected recurrent component as an initial state.

Under that convention:

```text
candidate      frontier   states at frontier            occupancy
robust_208        203     9,205,907,984,925,546,288     99.810654%
balanced_221      219     8,758,470,803,266,242,662     94.959531%
long_239          259     8,640,201,583,112,448,360     93.677253%
```

The next physical step exceeds `2^63` in each case:

```text
robust_208   T=204   11,238,057,716,022,295,524
balanced_221 T=220  10,472,067,813,616,391,156
long_239     T=260  10,420,180,999,117,162,549
```

These numbers are **core-only address frontiers** and are not the same metric
as the earlier whole-universe frontiers carried in the candidate names.

Why they can differ in either direction:

- the core-only language excludes transient trajectories;
- the new default allows every recurrent-core node as a possible initial
  state, so the initial core state itself consumes address entropy;
- the earlier universe counters used different initial-condition semantics.

Therefore `203`, `219`, and `259` should not replace `208`, `221`, and `239` in
historical reports. They answer a different operational question.

## Growth factors recovered automatically

Using 4096 physical transitions for the nth-root estimate:

```text
robust_208    lambda ~= 1.220743436655
balanced_221  lambda ~= 1.206164251908
long_239      lambda ~= 1.173978947703
```

The balanced estimate converges toward the previously derived information-clock
value near `1.2061897`; the small difference is finite-horizon estimation error.

## What this changes

The reversible path layer no longer needs hardcoded symbols such as `A`, `B`,
or manually entered edge lengths `1/12/2/5`.

The public universe itself determines:

- which recurrent region dominates;
- where genuine choice occurs;
- which transitions are deterministic consequences;
- how long each deterministic flight lasts;
- how path addresses are partitioned in reverse.

This is materially closer to the original trajectory.generator hypothesis:

```text
current state + public time + public universe
    -> predecessor state
```

for every physical step inside the selected recurrent core.

## Remaining boundary

The construction still begins **inside** the recurrent core.

It does not yet encode:

1. the transient path from the universe's original initial condition into the
   recurrent core;
2. trajectories that leave the selected recurrent component;
3. automatic handoff between transient and recurrent address spaces.

The next gate should therefore extend the same reverse-block method to the
condensation DAG outside the recurrent SCC, producing one address that covers
the transient prefix and the recurrent orbit without supplying the core-entry
point as side metadata.
