# Endpoint ↔ hierarchical coordinate conversion — 2026-09-10

## Result

The endpoint/colex rank and hierarchical midpoint rank are exact bijections of
the same admissible trajectory language, but their orderings are structurally
incompatible with a simple state-only logarithmic conversion.

Exact small-horizon conversion passed for T=0..8. Fifty random conversions at
T=218 also round-tripped exactly.

## Midpoint fragmentation

In endpoint-rank order, trajectories sharing the same midpoint private state do
not occupy one contiguous interval. Fragmentation appears immediately and grows:

- T=5: 21 midpoint-state intervals over 10 midpoint states; max 5 intervals/state.
- T=11: 46 intervals over 12 states; max 12 intervals/state.
- T=17: 83 intervals over 12 states; max 27 intervals/state.

Therefore a midpoint state alone is insufficient to identify a contiguous rank
block in the endpoint coordinate.

## Current exact conversion cost

The exact endpoint -> hierarchical baseline reverses the endpoint address one
transition at a time. At T=218 it requires exactly 218 predecessor steps. It
does not need a separately stored trajectory, but it is O(T), not O(log T).

This does not prove that no sublinear conversion algorithm can exist. It does
rule out the tested simple strategy based only on midpoint state and contiguous
rank blocks.

## Architectural implication

The endpoint rank is naturally causal/online. The hierarchical rank is naturally
random-access oriented. Rather than treating one as a temporary representation
that must be converted into the other, the next experiment should seek a unified
online coordinate with hierarchical structure, for example a dyadic block/merge
representation.
