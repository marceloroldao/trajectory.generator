# Nonlinear ablation across perturbed universes — 2026-09-06

## Question

Does the single nonlinear geometric channel `N` universally sustain causal reversibility, or does it play a different structural role?

We tested the same controlled family of 18 nearby universes used in `structural_perturbation_scan.py`.  For every universe we retained the same six-bit semantic coordinate

`G = (h1, orientation, phase0, phase1, q0, q1)`

and the same construction of a binary bidirectionally-reversible edge label `z`.  We then compared the exact reachable dynamics `U_full = L + N` against an ablated dynamics `U_linear = L`, where every ANF monomial of degree >= 2 is removed from the learned forward law.  Both variants start from the same eight public initial states.

## Result

All 18 full universes are locally reversible under `(G,z)`.

After removing the nonlinear channel:

- 14/18 remain locally reversible;
- 4/18 become reversely ambiguous;
- therefore loss of reversibility is **not** a universal consequence of nonlinear ablation.

However, a stronger family-wide effect appears in path growth.

Every linear-only universe reaches the 63-bit limit at 60 transitions and has measured rate at 200 steps approximately `1.015 bit/step` (the extra 0.015 comes from the eight public starting states).  The full universes have substantially lower rates and much later 63-bit frontiers, spanning 112–236 transitions in this controlled family.

The median shift

`frontier_linear - frontier_full = -73 transitions`.

The mean rate shift is

`rate_linear - rate_full = +0.5881789143 bit/step`.

Thus the robust role of the nonlinear channel is not simply "make the map reversible".  Its universal role in this tested family is to **restrict admissible continuation freedom** and thereby lower path entropy.  In a subset of universes (4/18), that restriction is also necessary for unique local reversal.

## Interpretation

The original stronger hypothesis

`nonlinearity = mechanism that universally sustains reversibility`

is rejected for this family.

The evidence supports the narrower and stronger empirical statement

`nonlinearity = structural entropy regulator / constraint mechanism`.

In the full dynamics, not every `(G,z)` continuation remains admissible.  The nonlinear channel bends or rejects part of the otherwise fully branching affine evolution.  This preserves a much smaller language of trajectories, allowing many more physical transitions before the trajectory count exceeds `2^63`.

For the balanced universe `(0,2,4,4)` specifically, nonlinear ablation also destroys reverse uniqueness, so there `N` serves both roles:

1. entropy restriction;
2. causal disambiguation.

But the second role is not family-universal.

## Controlled results

| universe | full reversible | linear reversible | full frontier | linear frontier | full rate@200 | linear rate@200 |
|---|---:|---:|---:|---:|---:|---:|
| (0,0,4,4) | yes | yes | 181 | 60 | 0.350000 | 1.015000 |
| (0,1,4,4) | yes | yes | 124 | 60 | 0.501035 | 1.015000 |
| (0,2,0,4) | yes | yes | 118 | 60 | 0.522352 | 1.015000 |
| (0,2,1,4) | yes | yes | 127 | 60 | 0.488185 | 1.015000 |
| (0,2,2,4) | yes | yes | 133 | 60 | 0.461294 | 1.015000 |
| (0,2,3,4) | yes | no | 171 | 60 | 0.367042 | 1.015000 |
| (0,2,4,0) | yes | yes | 178 | 60 | 0.351112 | 1.015000 |
| (0,2,4,1) | yes | yes | 112 | 60 | 0.545216 | 1.015000 |
| (0,2,4,2) | yes | yes | 145 | 60 | 0.427845 | 1.015000 |
| (0,2,4,3) | yes | no | 147 | 60 | 0.422089 | 1.015000 |
| (0,2,4,4) | yes | no | 218 | 60 | 0.290586 | 1.015000 |
| (0,3,4,4) | yes | yes | 124 | 60 | 0.496867 | 1.015000 |
| (0,4,4,4) | yes | yes | 131 | 60 | 0.471549 | 1.015000 |
| (1,0,0,2) | yes | yes | 205 | 60 | 0.307204 | 1.015000 |
| (1,2,4,4) | yes | no | 132 | 60 | 0.470199 | 1.015000 |
| (2,2,4,4) | yes | yes | 129 | 60 | 0.478298 | 1.015000 |
| (3,2,4,4) | yes | yes | 236 | 60 | 0.271776 | 1.015000 |
| (4,2,4,4) | yes | yes | 136 | 60 | 0.460129 | 1.015000 |

## Reproducibility

Experiment: `experiments/nonlinear_ablation_perturbations.py`

Workflow: `.github/workflows/nonlinear-ablation.yml`

GitHub Actions run: `34067108749`
