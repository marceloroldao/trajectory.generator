# Local causal reversible codec — 2026-09-05

Status: validated experimental milestone

## Summary

The operational topological trajectory universe contains only 37 causal states
reachable from the eight public initial states, with 49 directed operational
edges.

Offline bidirectional partition refinement defines an injective structural
coordinate `C(X)` on those 37 states.  The new result is that the operational
edge relation admits a **minimal binary reversible labeling**.

## Local closure

Using the raw transition/data bit `b = next_history_lsb`, forward evolution is
single-valued on all 49 edges:

```text
(C_t, b_t) -> C_{t+1}
```

with zero ambiguous keys.

The same bit alone is not sufficient in reverse: 15 reverse keys remain
ambiguous.

A topology relation `deltaQ = Q_t XOR Q_{t+1}` closes reverse evolution.  Exact
partition search shows that its 8 values can be reduced to two classes:

```text
r = 0 for deltaQ in {0,1,2,3}
r = 1 for deltaQ in {4,5,6,7}
```

This one-bit relation is sufficient for

```text
(C_{t+1}, r_t) -> C_t
```

but is not sufficient for forward evolution.

## Minimal common reversible edge label

The operational graph has

```text
max out-degree = 2
max in-degree  = 2
```

so any edge alphabet that is injective at both source and destination requires
at least two symbols.

Treating source classes and destination classes as the two sides of a bipartite
incidence graph, a deterministic 2-edge-coloring was constructed.  The result
is a binary label `z in {0,1}` with zero ambiguity in all four maps:

```text
(C_t,     z_t) -> C_{t+1}
(C_{t+1}, z_t) -> C_t
(C_t,     z_t) -> data bit
(C_{t+1}, z_t) -> data bit
```

The label distribution over the 49 operational edges is:

```text
z=0: 34 edges
z=1: 15 edges
```

Because the lower bound is two symbols and a two-symbol construction exists,
the binary alphabet is minimal for this operational graph.

Important: this binary coloring is currently a canonical public structural
label derived from the operational graph.  It has not yet been reduced to a
simple closed-form local arithmetic expression.

## Exact enumerative codec

`experiments/causal_label_codec.py` ranks/unranks all admissible fixed-length
paths on the 37-state binary-labeled causal automaton and maps the rank through
a reversible 63-bit affine permutation.

The public decoder receives only:

```text
(final_state_63, physical_steps)
```

plus the public machine definition.  It reconstructs:

- public initial causal state;
- complete causal-class trajectory;
- complete binary relation-label trajectory;
- original transition/data bits.

Small-length exhaustive/self tests pass.

## Capacity equivalence

The causal-coordinate codec reproduces exactly the previously measured full
topological trajectory counts:

```text
steps 216:  5,820,770,252,654,087,216   fits 2^63
steps 217:  6,862,834,056,478,043,753   fits 2^63
steps 218:  9,131,204,053,820,206,208   fits 2^63
steps 219: 10,214,739,716,735,776,832   exceeds 2^63
steps 220: 12,043,434,212,870,513,151   exceeds 2^63
```

Therefore the exact 63-bit frontier is unchanged:

```text
218 physical transitions
+ 3 public initial history bits
= 221 trajectory bits in the represented constrained language.
```

This is expected: the causal-coordinate representation is an isomorphic
re-description of the same constrained path family, not a new source of
capacity.

## Interpretation

The main structural result is not extra compression.  It is that the complete
operational dynamics can be represented as a finite causal coordinate system
whose edges need only one binary relational label to be locally invertible:

```text
C_t <--- z_t ---> C_{t+1}
```

The original bit is itself recoverable from the endpoint class and this
relation label.

That is a concrete computational form of the hypothesis that information can
be carried by the **relation between states along a trajectory**, rather than
by the raw state value alone.

## What this does not yet prove

It does not show that an arbitrary binary string can be compressed into 63 bits.
The codec is exact only for the constrained trajectory language whose path count
stays below the 63-bit address space.

It also does not yet eliminate the public graph/table definition: the binary
edge labeling was discovered from global graph structure.

## Next experiment

The strongest next question is whether the canonical reversible label `z_t` can
be generated locally from a compact function such as

```text
z_t = F(local state relation, phase)
```

without storing the 49-edge table.  If that succeeds, the runtime machine would
need only the current causal coordinate, one relational bit and a small public
local law, while exact trajectory decoding would still be supplied by the
fixed-length enumerative rank/unrank layer.
