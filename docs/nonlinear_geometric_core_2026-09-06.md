# Nonlinear geometric core — 2026-09-06

## Scope

This note records the current structural decomposition of the operational reversible automaton. It is an empirical property of the present finite machine, not a physical or ontological claim.

## Operational state space

The reachable operational graph has 37 causally distinct states and 49 directed edges. Bidirectional refinement cannot merge any of the 37 states while preserving the reversible binary edge labeling. Therefore an exact binary coordinate needs at least ceil(log2(37)) = 6 bits.

A best compact semantic coordinate found by exhaustive search over the current feature family is:

```
G = (h1, orientation, phase0, phase1, q0, q1)
```

This uses exactly six bits, meeting the information-theoretic lower bound.

## Minimal nonlinear channel count

Across all 688 injective six-bit semantic coordinates tested, the minimum number of nonlinear output channels is:

- forward: 1 of 6 outputs;
- reverse: 1 of 6 outputs.

144 coordinates achieve this one-channel-per-direction minimum.

For the best coordinate above, the algebraic degree profile is:

```
forward: [1, 1, 1, 1, 3, 1]
reverse: [1, 4, 1, 1, 1, 1]
```

Thus five coordinates are affine in each direction and all irreducible nonlinear behavior is concentrated in one coordinate.

## Exact decomposition

Write the update as

```
G_next = L_f(G, z) XOR e_q0 * N_f(G)
G_prev = L_r(G, z) XOR e_orientation * N_r(G)
```

where `L_f` and `L_r` are affine maps on the observed operational domain, `e_q0` selects the q0 output coordinate, and `e_orientation` selects the orientation output coordinate.

### Forward nonlinear gate

The nonlinear correction affects `q0`. Its exact gate is:

```
N_f(G) =
    g1&g4
  XOR g1&g5
  XOR g0&g3&g5
  XOR g1&g4&g5
  XOR g2&g4&g5
```

Important: `z` is not required to determine this gate. Exhaustive subset minimization found that all six state-coordinate bits are required within the tested representation; no 5-bit subset determines `N_f` exactly on all operational edges.

The forward nonlinear correction is active on 24 of 49 edges (~48.98%).

### Reverse nonlinear gate

The nonlinear correction affects `orientation`. Its exact gate is:

```
N_r(G) =
    g1&g2
  XOR g1&g3
  XOR g2&g5
  XOR g3&g5
  XOR g0&g1&g2
  XOR g0&g1&g5
  XOR g0&g3&g5
  XOR g1&g3&g5
  XOR g0&g1&g3&g5
```

Again, `z` is not required. In the reverse direction the gate depends on only five state bits:

```
(g0, g1, g2, g3, g5)
```

so `g4` and `z` are unnecessary for deciding whether the nonlinear correction fires.

The reverse nonlinear correction is active on 19 of 49 edges (~38.78%).

## Structural interpretation

The current machine admits a useful separation:

```
state geometry -> decides whether nonlinear correction is active
binary edge label z -> participates in the affine transport / branch selection
```

Equivalently, the nonlinear gate is endogenous to the local geometric state in this representation. The data/edge label does not switch the nonlinear interaction on or off.

This is stronger than merely finding a reversible labeling: it shows that the tested automaton can be written as mostly affine transport plus a single state-controlled nonlinear channel.

## What this does not prove

This does not demonstrate that information is physically stored in vacuum, that these variables correspond to physical dimensions, or that the decomposition generalizes beyond the current finite automaton. It establishes a precise computational structure that can now be stress-tested under enlarged state spaces and changed transition rules.

## Next falsification target

The next useful test is robustness under rule perturbation. We should vary the universe cadence, topology map, initial-state set, and state width and ask whether the same qualitative structure persists:

1. six-bit-optimal or near-optimal causal coordinates;
2. one nonlinear channel per direction;
3. nonlinear gate independent of the edge/data label;
4. stable information-capacity frontier.

If these properties disappear under small perturbations, they are likely artifacts of the current automaton. If they persist across a family of independently generated machines, they become a candidate invariant of the trajectory construction.
