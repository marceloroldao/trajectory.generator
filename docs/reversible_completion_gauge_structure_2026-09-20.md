# Reversible completion, gauge structure, and intrinsic vertical dynamics — 2026-09-20

## Executive result

The trajectory.generator line now separates three objects that were previously
mixed together:

1. **coordinate-free reversible state**:
   the admissible history itself (the natural extension of the causal graph);

2. **minimal vertical fiber**:
   the set of distinct histories that project to one raw causal node;

3. **numeric final-state coordinate**:
   a compact chart that labels those histories for computation.

The first two are forced by exact reversibility. The third is not unique.

This distinction resolves an important ambiguity in the earlier vertical-law
experiments.

---

## 1. What exact reversibility forces

For causal node `v` at physical time `t`, let:

```text
H_t(v) = admissible histories of length t ending at v
```

and:

```text
D(v,t) = |H_t(v)|.
```

Any exact reversible lift projecting onto the original causal graph must have
at least `D(v,t)` distinct lifted states above `v`.

Otherwise two distinct histories would be mapped to one lifted state, making
exact reverse impossible.

Therefore the fiberwise minimum is exactly:

```text
|F_t(v)| = D(v,t).
```

For target node `v`, each incoming causal edge `e:u->v` must receive an
image block of size:

```text
D(u,t).
```

Those predecessor-edge images are disjoint and their union is the complete
target fiber.

These cardinalities are forced.

---

## 2. What exact reversibility does not force

Inside the image of one incoming edge, the source fiber may be permuted by any
bijection before it is embedded into the target fiber.

Thus:

```text
source fiber
    -> arbitrary permutation
    -> predecessor edge image
```

can remain exactly reversible.

The internal labeling is therefore a **vertical gauge freedom**.

Identity transport, phase reflection, phase+merge rotation, branch reflection,
and other valid permutations can represent the same underlying reversible
history dynamics.

---

## 3. Natural extension is the coordinate-free object

The intrinsic reversible state at finite time is:

```text
(start node, complete causal edge history, current endpoint)
```

Forward:

```text
append one public edge
```

Reverse:

```text
remove the last public edge
```

This operation is exactly reversible without introducing a numerical vertical
coordinate.

A minimal fiber lift is a chart:

```text
history <-> (causal node, vertical coordinate).
```

Different charts are related by history-preserving time-dependent bijections.

---

## 4. Gauge groupoid

For charts A and B:

```text
G_AB(t) = chart_B(t) o chart_A(t)^-1.
```

These maps satisfy:

```text
G_AA = identity

G_BA o G_AB = identity

G_BC o G_AB = G_AC
```

and conjugate the represented dynamics:

```text
G_AB(t+1) o F_A(e,t)
    =
F_B(e,t) o G_AB(t).
```

Thus different vertical laws are coordinate descriptions of the same history
dynamics when linked by the corresponding gauge change.

The operational 63-bit final state is therefore a compact chart coordinate, not
a second independent physical history.

---

## 5. Why a nontrivial numeric law cannot be fully gauge-invariant

If a fiber has no declared structure beyond having `n` elements, every
permutation is an admissible relabeling:

```text
g in S_n.
```

A concrete vertical permutation `f` would be independent of chart only if:

```text
g f g^-1 = f
```

for every `g in S_n`.

Therefore `f` must lie in the center:

```text
Z(S_n).
```

For:

```text
n >= 3
```

the center is:

```text
Z(S_n) = {identity}.
```

So no nontrivial **numeric representative** can be intrinsic on a generic
unstructured fiber.

This is a no-go result, not an implementation limitation.

---

## 6. Graph automorphism versus full fiber gauge

Two symmetry requirements must not be confused.

A vertical formula can be invariant under renaming equivalent causal graph
nodes while still depending on the chosen numeric labeling inside each fiber.

The repository found:

- phase reflection is invariant under the tested causal branch-swap
  automorphism;
- incoming-index rotation is not, because incoming order is an ordered-chart
  convention.

But even phase reflection is not fixed under every arbitrary internal fiber
relabeling when `n>=3`.

Therefore graph-automorphism invariance is weaker than full gauge invariance.

---

## 7. Gauge-covariant physical content

The no-go theorem does **not** require vertical dynamics to be trivial.

Under gauge change:

```text
f -> g f g^-1.
```

Although the representative changes, its conjugacy class does not.

For permutations of a finite set, the conjugacy class is determined by cycle
type.

Therefore a legitimate coordinate-free vertical statement can specify a cycle
type rather than one particular numeric permutation.

---

## 8. Information-event-driven action

The causal graph already supplies a coordinate-free event:

```text
information event
    <=> out_degree(source) > 1.
```

This is the same branch structure underlying the information clock.

The current strongest vertical proposal is:

```text
deterministic source:
    identity conjugacy class

information-event source:
    fixed-point-minimal involution conjugacy class
```

For fiber size `n`, an involution consists only of 1-cycles and 2-cycles.

Demanding that the event involve as many vertical states as possible is
equivalent to minimizing fixed points.

This uniquely gives:

```text
n even:
    n/2 transpositions
    0 fixed points

n odd:
    (n-1)/2 transpositions
    1 fixed point
```

So the gauge-invariant action class is forced by:

1. self-inverse local response;
2. gauge-covariant physical description;
3. maximal participation at an information event.

A convenient numeric representative is:

```text
R_n(y) = n - 1 - y.
```

But `R_n` itself is only a chart representative. The physical statement is
its conjugacy class.

---

## 9. Why this is stronger than phase+incoming-index

The previous coefficient-free law:

```text
sigma = (-1)^phase
shift = incoming_index
```

is a valid reversible chart law and works operationally.

However:

```text
incoming_index
```

changes under predecessor reordering and therefore cannot be claimed as
coordinate-free physics.

The information-event maximal-pairing class removes both dependencies:

- no absolute phase number is required;
- no incoming or outgoing edge ordering is required;
- no numerical coefficients are required.

Its trigger is local causal branching and its action is stated only up to
conjugacy.

---

## 10. Conditional cyclic-group route

There is another mathematically clean possibility.

If each fiber were endowed with a canonical cyclic-group structure:

```text
F_t(v) ~= Z_n
```

then group inversion:

```text
y -> -y
```

would be natural under every group automorphism:

```text
phi(-y) = -phi(y).
```

This was verified computationally for a range of finite cyclic groups.

But the existence of this group structure is an extra assumption.

---

## 11. Cardinality alone cannot create the cyclic group structure

A group needs a distinguished identity element.

If a fiber is only an `n`-element set, a canonical identity would have to be
fixed by every relabeling in `S_n`.

For every:

```text
n > 1
```

there is no such common fixed element.

Therefore:

```text
fiber cardinality
    !=>
canonical Z_n structure.
```

If a cyclic or other algebraic fiber law is to become intrinsic, the required
origin and operation must come from additional public structure of the
universe/history, not from the number of histories alone.

---

## 12. Operational final-state recovery remains valid

None of these gauge results removes the operational achievement.

For the tested constrained families:

```text
(final_state, steps, public law)
    -> exact admissible trajectory
```

continues to work.

Static rank, phase reflection, phase+merge, branch reflection, and
maximal-pairing representatives are different charts.

A given underlying trajectory may therefore have different integer addresses in
different charts.

After the corresponding gauge conversion, the history is identical.

So the final integer should be interpreted as:

```text
compact coordinate of the reversible history state
```

rather than as a chart-independent physical observable.

---

## Current strongest formulation

The reversible universe is best stated as:

```text
horizontal:
    raw causal state

vertical:
    history fiber required by reversibility

intrinsic evolution:
    append/remove causal edge in natural-extension history space

information-event vertical response:
    maximal-pairing involution conjugacy class

numeric final_state:
    one chosen compact gauge chart
```

This formulation is consistent with:

- exact reversibility;
- information bounds;
- causal projection;
- graph automorphisms;
- arbitrary fiber gauge changes;
- final-state-only decoding.

---

## Remaining research problem

The strongest unresolved question is no longer whether a nontrivial vertical
law can exist.

A nontrivial **gauge-covariant** law can exist and has a structurally derived
information-event class.

The unresolved problem is whether the public universe supplies additional
structure on each history fiber that selects a preferred representative, such
as:

- an endogenous origin;
- a canonical cyclic/abelian group operation;
- a recursive predecessor-tree coordinate;
- a symbol-preserving algebraic structure;
- another law generated by the recurrent information clock.

If no such structure exists, the gauge class — not one numeric permutation —
is the correct final level of description.


---

## Executed integrated validation

GitHub Actions run:

```text
35555298953
workflow: reversible-pipeline-gate
conclusion: success
```

All 29 scientific gates passed.

The general completion/gauge results reported:

```text
GENERAL_REVERSIBLE_COMPLETION_FULL_GATE
PASS=True
fiber sizes and edge-block cardinalities are forced;
internal vertical permutations are gauge freedom

NATURAL_EXTENSION_GAUGE_FULL_GATE
PASS=True
history space is invariant;
vertical coordinates are gauge charts

GAUGE_INVARIANCE_NO_GO_FULL_GATE
PASS=True
intrinsic object = admissible-history natural extension
numeric vertical law = gauge representation unless extra fiber structure exists

REVERSIBLE_COMPLETION_GROUPOID_FULL_GATE
PASS=True
minimal reversible lifts are unique up to
history-preserving time-dependent fiber gauge isomorphism
```

The real topological universes also passed direct chart-equivalence gates:

```text
robust_208
  frontier=208
  static/phase-reflection/phase-merge history identity=True
  frontier coordinate changes=4/5

balanced_221
  frontier=221
  history identity=True
  frontier coordinate changes=5/5

long_239
  frontier=239
  history identity=True
  frontier coordinate changes=5/5
```

So different final integers/charts can represent the same underlying history
after the correct gauge conversion.

### Gauge-covariant information-event action

The strongest current event law also passed end-to-end:

```text
robust_208
  branch public edges=38
  deterministic public edges=27
  maximal-pairing class=True
  deterministic identity=True
  nontrivial branch classes=132
  small mapping changes=269
  frontier mapping changes=5/5
  exhaustive roundtrip=True
  frontier roundtrip=True

balanced_221
  branch public edges=24
  deterministic public edges=25
  maximal-pairing class=True
  deterministic identity=True
  nontrivial branch classes=92
  small mapping changes=247
  frontier mapping changes=5/5
  exhaustive roundtrip=True
  frontier roundtrip=True

long_239
  branch public edges=20
  deterministic public edges=24
  maximal-pairing class=True
  deterministic identity=True
  nontrivial branch classes=76
  small mapping changes=212
  frontier mapping changes=5/5
  exhaustive roundtrip=True
  frontier roundtrip=True
```

The class derivation itself was checked exactly for small fibers:

```text
n=1 -> (1)
n=2 -> (2)
n=3 -> (1,2)
n=4 -> (2,2)
n=5 -> (1,2,2)
n=6 -> (2,2,2)
```

and the derived class matched the fixed-point-minimal involution class in every
case.

### Conditional algebraic structure

The same run also passed:

```text
CYCLIC_FIBER_NATURALITY_FULL_GATE
PASS=True
```

showing that if a fiber is endowed with a canonical `Z_n` group law, inversion
is natural under every group automorphism.

But it also passed:

```text
FIBER_GROUP_STRUCTURE_NO_GO_FULL_GATE
PASS=True
```

showing that fiber cardinality alone cannot select the distinguished origin
needed for that group law.

Therefore the cyclic-group interpretation remains conditional, not established
for the current history fibers.
