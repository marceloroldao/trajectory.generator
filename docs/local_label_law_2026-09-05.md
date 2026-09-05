# Local reversible-label law — 2026-09-05

## Result

The operational causal graph has 37 causal classes and 49 operational edges. A canonical binary edge label `z` already provides bidirectional local reversibility and exact recovery of the transition/data bit.

This milestone tests whether `z` can be computed without consulting causal-class IDs or the global edge-coloring map.

## Table-free local function

Using only local transition observables, there are no conflicting observations on the 49 operational edges: every distinct local observation tuple maps to exactly one canonical reversible label.

An exact Boolean algebraic-normal-form (ANF) representation exists at degree 3. Degree 1 and degree 2 are insufficient for the tested families.

Critically, the exact degree-3 law remains possible after removing:

- causal class IDs `c` and `cn`;
- branch `ordinal`;
- branch/outdegree metadata;
- absolute topology state.

Therefore the reversible edge label can be computed, on the observed operational domain, from relation/history/phase observables alone.

## Minimal observed variable set

Exhaustive subset search over the 10 relation/phase primitives found that 7 variables are necessary within the tested degree <= 3 ANF family. No subset of 6 or fewer variables closed the canonical label on all 49 edges.

There are 21 exact 7-variable subsets. The best solution found by the current GF(2) solver uses:

- `hdelta1`
- `history_lsb`
- `next_history_lsb`
- `next_phase`
- `phase`
- `tdelta1`
- `tdelta2`

with the following exact ANF on the operational domain:

```text
z = hdelta1
  ^ next_history_lsb
  ^ hdelta1&tdelta2
  ^ next_history_lsb&next_phase
  ^ next_history_lsb&tdelta2
  ^ phase&tdelta1
  ^ hdelta1&history_lsb&phase
  ^ hdelta1&next_history_lsb&next_phase
  ^ hdelta1&next_history_lsb&tdelta2
  ^ hdelta1&next_phase&tdelta1
  ^ history_lsb&phase&tdelta1
```

This expression contains 11 active monomials and degree 3.

## Interpretation

This is stronger than the prior global coloring result. The canonical one-bit reversible edge label is not merely an arbitrary graph-color assignment: on the tested operational graph it is reproducible from local relational observables without consulting a global edge table.

The current evidence supports the local form

```text
z_t = F(local history relation, local topology relation, phase)
```

and therefore the reversible causal dynamics

```text
C_t --z_t--> C_{t+1}
C_{t+1} --z_t--> C_t
```

can be driven by a locally computed one-bit relation on the observed domain.

## Important limits

This is an exact result on the current 49-edge operational domain only. It does not yet prove that the same formula generalizes to unseen states or to larger universes. The current ANF solution is also not guaranteed to be the sparsest algebraic expression; the GF(2) solver returns one exact solution with free variables fixed to zero.

## Next experiments

1. Minimize the exact degree-3 expression for term count, not only variable count.
2. Search for equivalent geometric or phase/topology invariants that replace raw bit-position names.
3. Validate the resulting local law on expanded operational graphs/universes.
4. If the law survives expansion, replace the precomputed edge-coloring table in the codec with direct local computation of `z`.
