# Linear trajectory-address experiment — 2026-08-19

Status: pre-alpha constructive result
RSMS compatibility: pending central specification mapping

## Objective

Test whether a machine can recover an arbitrary bit trajectory from only:

1. one final fixed-width state; and
2. the number of steps,

without trajectory logs, auxiliary lookup tables, plaintext hints, checksums, or MITM search.

## Construction

A second experimental machine was added in `trajectory_generator/trajectory_address.py`.

The state is interpreted relative to a fully public deterministic universe baseline. At every step:

1. the universe applies a deterministic reversible permutation/mixing transform to the whole state;
2. the set of coordinates carrying previous data deviations is permuted with it;
3. a coordinate that is guaranteed to be free of prior data deviation is selected deterministically;
4. bit `0` leaves that coordinate unchanged;
5. bit `1` flips that coordinate.

Because the selected coordinate contains only the public universe baseline before the new bit is injected, the decoder can read the data bit directly from the deviation between the final trajectory state and the public baseline at that coordinate. It then removes the bit and applies the exact inverse universe transform.

The decoder therefore needs only `(final_state, steps)` plus the public machine definition.

## Complexity

For `n <= width`:

- encoding: `O(n * width)` with the current simple set-based schedule implementation;
- decoding: `O(n * width)` with schedule reconstruction;
- trajectory search: none;
- external trajectory memory: none.

The schedule is a deterministic function of `(steps, width, public machine parameters)` and does not depend on the data bits.

A more compact schedule implementation can reduce the bookkeeping constant, but this does not change the information-theoretic capacity.

## Exact capacity limit

This construction supports at most `width` arbitrary binary input steps in one `width`-bit final state.

For the default width 63:

`n <= 63`

can be made exactly reversible by this construction. For arbitrary `n > 63`, exact one-to-one recovery from only one 63-bit state plus a fixed known step count is impossible by the pigeonhole principle.

The construction therefore reaches the theoretical arbitrary-data capacity of the final state; it does not exceed it.

## Validation

Random full-capacity tests passed for 63-bit trajectories.

Exhaustive full-capacity scans were also performed:

| width | trajectory length | trajectories | unique final states | collisions | decode failures |
|---:|---:|---:|---:|---:|---:|
| 8 | 8 | 256 | 256 | 0 | 0 |
| 12 | 12 | 4,096 | 4,096 | 0 | 0 |
| 16 | 16 | 65,536 | 65,536 | 0 | 0 |

At `n = width`, the construction is a bijection over the full finite state space for the tested widths.

Reproduce with:

```bash
python experiments/trajectory_address_scan.py --widths 8 12 16
python -m unittest discover -s tests -v
```

## Interpretation

This is materially different from the original mixed-state machine.

The original machine tries to discover whether trajectory identity emerges from generic reversible mixing; recovery currently requires exponential search (MITM reduces the exponent to approximately one half).

The trajectory-address machine is constructive: it deliberately maintains one fresh degree of freedom per arbitrary input bit. That makes exact linear-time decoding possible, but it also makes clear where the information resides.

The result supports the statement:

> A time-dependent reversible trajectory can serve as an address for information.

It does **not** support the stronger statement that more arbitrary information than the final state's bit capacity has been stored in that state.

## Important terminology

The final value should currently be called `final_state` or `trajectory_address`, not a cryptographic hash. A cryptographic hash is intentionally many-to-one and normally designed to resist inversion; this construction is intentionally reversible over its admitted domain.

## Next research questions

1. Can the fresh-coordinate idea be generalized from explicit bit coordinates to less trivial invariant subspaces while preserving O(n) decoding?
2. Can the universe transformation be strengthened beyond coordinate permutation/XOR without losing the ability to identify a fresh data degree of freedom?
3. Can structured, non-arbitrary inputs exceed `width` steps because their admissible trajectory set has entropy below `width` bits?
4. Is there a useful hierarchy of trajectory addresses analogous to multi-level resolving layers, while keeping all side information explicit and auditable?
5. Do any orbit ratios emerge statistically without inserting preferred constants such as phi into the generator?
