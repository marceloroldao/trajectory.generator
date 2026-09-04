# Causal coordinate refinement — 2026-09-04

Status: experimental structural result

## Question

Can the present causal state be characterized structurally, rather than by carrying its raw tuple label, using only properties derived from the public dynamics?

The starting coarse coordinate is:

```text
(B(X), Phi(X))
```

where `B(X)` is the reachable attractor/basin signature and `Phi(X)` is the dominant spectral potential where defined.

## Operational state space

The formal phase-lifted graph contains 192 states, but from the eight public initial states only:

```text
37 states
```

are actually forward reachable.  This operational subgraph is the relevant state space for the present machine.

Among those 37 reachable states:

```text
18
```

lie in the positive-support dominant spectral basin.

## Coarse coordinate insufficiency

On the 37 reachable states, `(B,Phi)` yields only:

```text
16 coordinate classes
```

with collisions as large as 11 states in one class.  Therefore basin plus scalar potential is not an injective causal address.

## Future-only refinement

Starting from `(B,Phi)`, repeatedly split classes according to the multiset of successor classes.  The stable future-language partition contains:

```text
24 classes
```

with a largest class of 5 states.

So future accessibility alone still leaves causal ambiguities.

## Bidirectional refinement

Now refine using both:

```text
successor-class multiset
predecessor-class multiset
```

at every iteration.

On the 37-state operational graph the partition stabilizes at:

```text
37 classes for 37 states
```

with largest class size:

```text
1
```

Therefore the bidirectional structural coordinate is injective on the operational graph.

## Interpretation

Define a structural causal coordinate `C(X)` as the stable equivalence class obtained by iterative refinement from `(B,Phi)` using both accessible past and future class structure.

For this automaton:

```text
C(X) uniquely identifies every reachable causal state.
```

This does not mean `(B,Phi)` alone recovers the state, and it does not prove a physical ontology.  It shows a narrower computational fact: within the reachable dynamics, the identity of a state can be recovered from its relational position in the causal graph rather than from its raw binary tuple.

A useful hierarchy is now:

```text
B(X)   -> basin / terminal possibilities
Phi(X) -> spectral potential inside a basin
C(X)   -> bidirectional relational identity
```

The next question is whether `C(X)` can be generated locally and incrementally along a trajectory, instead of being obtained by an offline whole-graph refinement.  If so, it could become an actual state coordinate usable by the reversible trajectory machine.

## Reproduction

```bash
PYTHONPATH=. python experiments/causal_coordinate_refinement.py
```
