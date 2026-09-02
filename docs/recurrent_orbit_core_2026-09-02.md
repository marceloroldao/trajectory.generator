# Recurrent orbit-core analysis — 2026-09-02

Status: pre-alpha structural analysis

## Objective

Instead of adding another memory variable, inspect the finite causal graph of the topological-transition machine and identify recurrent strongly connected components (SCCs) that support indefinite return trajectories.

The phase-lifted causal node is:

```text
(history3, topology3, phase3)
```

so the full graph has at most 192 nodes.

## Main result

The topological candidates are not expanding uniformly over the full causal graph. Their asymptotic information growth is concentrated in a very small recurrent core.

For the 221-step candidate:

```text
params = (0,2,4,4)
```

the dominant recurrent SCC has approximately:

```text
nodes             = 14
internal edges    = 16
outgoing edges    = 6
internal branches = 2
lambda            ~= 1.206189700
log2(lambda)      ~= 0.270456821 bit/step
```

Only two nodes in the 14-state recurrent core branch internally. Most of the core is deterministic return structure; the information growth is concentrated at those branch points.

The finite-length rate measured earlier at 300 steps (~0.28081 bit/step) is slightly higher than the dominant-core asymptotic rate because transient paths still contribute at finite length.

## Comparison of three topological Pareto candidates

```text
candidate   frontier   flip64    dominant lambda   core nodes  branch nodes
208         208        ~14.86%   ~1.220744085      24          6
221         221        ~14.16%   ~1.206189700      14          2
239         239        ~12.66%   ~1.173984997       8/7        1 per core
```

As frontier increases, the dominant recurrent structure becomes smaller and less branching. This is consistent with the broader trade-off seen throughout the project: longer addressable trajectories arise by reducing the number of independent branch decisions per unit time.

## Why this is closer to an orbit

Earlier coherence variables were summaries imposed on the trajectory. Here the recurrent component is discovered from the transition graph itself.

A trajectory that remains in one of these SCCs can return indefinitely to equivalent causal classes. This is an actual graph-theoretic recurrence property, not merely numerical proximity between states.

The public period-3 phase is part of the node definition, so cycle lengths that are multiples of three are not evidence of a new physical periodicity by themselves. The meaningful result is the concentration of growth into a small recurrent branching core.

## Research consequence

This suggests a better next question than adding more state bits:

> Can the branch events inside the recurrent core be treated as the true information-bearing events, while deterministic travel around the core is treated as universe evolution?

If so, the natural trajectory coordinate is no longer every time step. It is the ordered sequence of visits to branch points / return classes.

That would create a two-timescale representation:

```text
physical/universe step t
        ↓
recurrent orbit travel
        ↓
branch-event index k
        ↓
information-bearing decision
```

This remains subject to the same information bound: no arbitrary extra information is created. The potential advantage is a more faithful coordinate system for structured trajectories.

## Reproduction

```bash
python experiments/recurrent_orbit_core.py
```
