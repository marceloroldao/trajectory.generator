# General minimal reversible completion and vertical gauge — 2026-09-20

## Main result

For a finite public causal graph, exact reversible completion separates into two parts:

1. a **forced invariant structure**;
2. a **non-unique vertical coordinate gauge**.

This distinction is implemented in:

- `trajectory_generator/minimal_reversible_completion.py`
- `trajectory_generator/reversible_natural_extension.py`

## 1. The invariant object: admissible history space

Let `H_t(v)` be the set of admissible public edge histories of length `t` ending at raw causal node `v`.

If an exact lifted state projects to `v` and must allow complete history recovery, then two distinct elements of `H_t(v)` cannot occupy the same lifted state.

Therefore every exact reversible lift satisfies:

```text
|F_t(v)| >= |H_t(v)|
```

A fiberwise minimal lift has:

```text
|F_t(v)| = |H_t(v)|
```

This is the information-theoretically forced vertical cardinality.

## 2. Forced predecessor partition

Every history in `H_(t+1)(v)` has a unique final public edge `e:u->v`.

Removing that edge gives one history in `H_t(u)`. Therefore:

```text
F_(t+1)(v)
  = disjoint_union over e:u->v of Image_t(e)
```

with forced block cardinality:

```text
|Image_t(e)| = |H_t(u)|
```

and consequently:

```text
|F_(t+1)(v)| = sum over e:u->v |F_t(u)|
```

This is the same endpoint-count recurrence already used by the trajectory codec.

## 3. What is not forced

Inside one edge-image block, reversibility requires only a bijection from the source fiber into that block.

If `n = |F_t(u)|`, any permutation in `S_n` is valid.

Examples include identity, reflection, periodic reflection, and the earlier phase/merge gauge.

All preserve the same history set, horizontal causal projection, and exact reverse recovery.

Therefore the internal vertical permutation is not uniquely selected by minimal reversibility alone.

## 4. Trivial versus nontrivial gauge

If every reachable fiber has size at most one, the gauge group is trivial.

If any reachable fiber has size greater than one, distinct vertical coordinate laws can represent the same reversible history dynamics.

## 5. Executed general gate

GitHub Actions run:

```text
35554542838
workflow: reversible-pipeline-gate
conclusion: success
```

Executed results:

```text
true merge
  PASS=True
  states checked=45
  edges checked=44
  gauge pairs checked=90
  minimality=True
  partition=True
  reversible=True
  projection=True
  gauge equivalent=True
  nontrivial fiber exists=True
  vertical law nonunique=True

singleton fibers
  PASS=True
  states checked=15
  edges checked=14
  gauge pairs checked=30
  nontrivial fiber exists=False
  vertical law nonunique=False

branch + merge
  PASS=True
  states checked=87
  edges checked=86
  gauge pairs checked=174
  nontrivial fiber exists=True
  vertical law nonunique=True

two initial states
  PASS=True
  states checked=60
  edges checked=58
  gauge pairs checked=120
  nontrivial fiber exists=True
  vertical law nonunique=True

parallel-edge growth
  PASS=True
  states checked=145
  edges checked=144
  gauge pairs checked=290
  nontrivial fiber exists=True
  vertical law nonunique=True
```

The full gate conclusion is:

```text
fiber sizes and edge-block cardinalities are forced;
internal vertical permutations are gauge freedom
```

## 6. Natural extension

The coordinate-free reversible object is the admissible history space itself.

Forward appends one public edge. Reverse removes the unique final edge.

A numerical fiber representation is a chart:

```text
chart_t:
    histories ending at v
      <->
    {0,...,D(v,t)-1}
```

## 7. Gauge conjugacy

Given two chart families `C_t` and `C'_t`, define:

```text
G_t = C'_t o C_t^-1
```

If `F_e` and `F'_e` are the same public history transition in the two gauges, then:

```text
G_(t+1) o F_e = F'_e o G_t
```

The natural-extension gate checked this identity explicitly.

Executed results:

```text
merge
  histories checked=45
  transitions checked=44
  charts bijective=True
  history reversible=True
  gauge conjugacy=True
  coordinate difference=True

branch_merge
  histories checked=87
  transitions checked=86
  charts bijective=True
  gauge conjugacy=True

two_starts
  histories checked=60
  transitions checked=58
  charts bijective=True
  gauge conjugacy=True
```

The full gate reports:

```text
history space is invariant;
vertical coordinates are gauge charts
```

## 8. Consequence for the phase/merge law

The previously frozen law:

```text
sigma(t) = (-1)^(t mod P)
b(e)     = incoming_index(e)
```

remains valid, reversible, periodic, coefficient-free, and useful as a deterministic public coordinate convention.

But it is **not uniquely implied by minimal reversibility**.

It is better described as a compact gauge fixing within an ordered public graph.

`incoming_index` partly belongs to how predecessor blocks are serialized into one integer coordinate.

## 9. Stronger invariant interpretation

The native reversible object is one admissible history state. A numerical vertical coordinate is a chart on that object.

This does not weaken the final-state-only result. It clarifies what the integer represents.

## 10. Next question

After quotienting out gauge freedom, the meaningful question is not which internal numerical permutation is uniquely correct. Minimal reversibility cannot answer that.

The next question is whether an additional invariant principle can select a useful gauge.

Candidate principles include:

- invariance under causal-graph relabeling;
- minimum description length;
- locality;
- smallest public temporal period;
- compatibility with the information clock;
- equivariance under graph automorphisms.

A phase-only reflection gauge is the next candidate because its internal permutation does not depend on predecessor ordering.
