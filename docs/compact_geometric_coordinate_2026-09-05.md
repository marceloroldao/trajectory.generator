# Compact six-bit geometric coordinate — 2026-09-05

## Result

The operational reversible graph has 37 causally distinct states. Bidirectional partition refinement shows that none can be merged while preserving the binary reversible edge label. Therefore an exact binary internal coordinate requires at least

\[
\lceil \log_2 37 \rceil = 6
\]

bits.

A search over semantic state-local features found 688 injective six-bit coordinates, so the information-theoretic lower bound is achieved.

The best coordinate under the current ANF-complexity objective is

\[
G=(h_1,\;orientation,\;phase_0,\;phase_1,\;q_0,\;q_1).
\]

Thus the 37 operational causal identities can be represented exactly by six public/local binary coordinates rather than a 37-entry state ID.

## Local update law

With the reversible binary edge label `z`, the forward map

\[
G_{t+1}=\Gamma(G_t,z_t)
\]

has algebraic degree at most 3. Five of the six output coordinates are affine/linear; only one coordinate needs a cubic law. The selected forward solution uses 19 ANF terms total.

The inverse map

\[
G_t=\Gamma^{-1}(G_{t+1},z_t)
\]

has algebraic degree at most 4. Again five of the six output coordinates are affine/linear; only the orientation-like coordinate needs the quartic law. The selected reverse solution uses 23 ANF terms total.

For the selected coordinate, the simple components include shift/phase-like laws such as

- `g0' = g0 xor g4`
- `g1' = g0 xor g4 xor g5`
- `g2' = 1 xor g2 xor g3`
- `g3' = g2`
- `g5' = g4`

with the remaining coordinate carrying the nonlinear interaction and `z`.

## Interpretation

The exact causal state cannot be reduced below 37 equivalence classes, but its representation can be reduced to the theoretical minimum of six bits. More importantly, most of the state evolution is linear. The nonlinearity of the current operational universe is concentrated into one coordinate in each direction.

This is a computational property of the present automaton. It is not evidence by itself of a physical six-dimensional state space.

## Next test

`experiments/affine_geometric_dynamics.py` tests whether, after conditioning on `z`, one of the 688 six-bit semantic coordinates makes each labeled transition an affine permutation

\[
G' = A_z G + c_z
\]

over GF(2). If both `A_0` and `A_1` are invertible, the observed operational dynamics can be extended to two reversible affine permutations over all 64 six-bit states. Otherwise the test quantifies the lowest nonlinear degree required.
