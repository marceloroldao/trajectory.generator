# Two-channel nonlinear decomposition — 2026-09-06

The five nonlinear forward monomials of the balanced universe can be grouped exactly as two composite bits:

- `I = t0 ^ t1 ^ t3`
- `G = t2 ^ t4`

with `N = I ^ G`.

This is an exact algebraic regrouping on the validated 49-edge operational domain.  The names are functional labels inferred from ablation behavior, not physical claims.

## Channel ablation

Using the exact observed `(state,label)` domain:

| configuration | reversible | frontier | rate@200 | dominant rho | agreement |
|---|---:|---:|---:|---:|---:|
| L only | no | >=300 | 0.0398577 | 1.0000000 | 25/49 |
| L + I | yes | >=300 | 0.0419616 | 1.0000000 | 39/49 |
| L + G | no | 229 | 0.2778759 | 1.1959689 | 27/49 |
| L + I + G | yes | 218 | 0.2905864 | 1.2061897 | 49/49 |

## Interpretation

The channels have strongly separated roles in this machine:

- `I` is sufficient to remove all local reverse ambiguity.  By itself it leaves the recurrent dynamics essentially non-expansive (`rho ~= 1`).
- `G` restores most of the information-growth geometry but does not resolve reverse ambiguity.
- `I + G` is required for exact fidelity to the original balanced universe.

Thus the validated decomposition is:

`U = L + z + I + G`

where:

- `L`: near-linear transport;
- `z`: local relation label / branch choice;
- `I`: causal-identity constraint;
- `G`: orbital-growth / admissibility geometry.

This suggests that reversibility and information growth are separable functions of the nonlinear core in the current automaton.

## Caution

`I` and `G` are constructed from the already-discovered monomials, so the factorization itself is not an independent law discovery.  Its value is that channel ablation validates distinct functional roles.  The next test should search for local geometric observables that compute `I` and `G` directly, without referencing the five raw monomials.
