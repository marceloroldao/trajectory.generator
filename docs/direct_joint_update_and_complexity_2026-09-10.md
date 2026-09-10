# Direct joint update law and complexity audit — 2026-09-10

## Question

Can the unified 63-bit joint dyadic address be advanced by a simple scalar law such as `A' = A + delta(t,z)` without opening its dyadic structure?

## Direct scalar-law scan

The exact map `A_t -> A_{t+1}` was enumerated for admissible `z` over small and moderate horizons and compressed into affine runs.

The mapping fragments rapidly. Examples:

- t=20, z=0: 459 admissible source ranks, 236 slope-1 runs;
- t=28, z=0: 2800 sources, 766 slope-1 runs;
- t=36, z=0: 8914 sources, 3517 slope-1 runs;
- t=40, z=0: 26651 sources, 7939 slope-1 runs.

Therefore a single offset or a small state-independent piecewise-affine scalar law is not supported by the current ordering. This does not rule out a more sophisticated closed form, but it makes such a form a poor optimization target.

## Structural complexity of the existing unified address

The joint dyadic address already has logarithmic structural complexity.

For time `t`:

- decoding the forest touches `popcount(t)` dyadic blocks;
- appending one transition creates one length-1 block;
- binary carry merges equal blocks; the number of merges is the number of trailing 1 bits in `t`;
- reranking touches `popcount(t+1)` blocks.

Across t=0..218, the exact maximum of

`popcount(t) + trailing_ones(t) + popcount(t+1)`

is 15, attained at t=127.

At the 63-bit frontier T=218:

- block shape is `[128, 64, 16, 8, 2]`;
- block count is 5;
- random symbol access reached maximum tree depth 8 in the audit;
- the jointly enumerated address remains exactly 63 bits.

## Conclusion

The unified coordinate already satisfies the desired structural target:

`A_{t+1} = Psi(A_t,t,z_t)`

with O(log t) dyadic structural work, while supporting O(log t) random access and preserving the exact 63-bit frontier at T=218.

The remaining optimization target is not the number of structural blocks. It is the cost of evaluating public path counts, suffix counts and big-integer rank arithmetic inside those O(log t) operations.

## Next experiment

Replace generic matrix/path-count evaluation inside the joint address with the previously derived scalar public recurrence / fast O(log t) count field, then benchmark arithmetic operations and cache footprint. The target is a production-style codec whose structural and numerical paths both use the compact laws already discovered.
