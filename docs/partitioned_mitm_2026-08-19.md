# Partitioned MITM — 2026-08-19

Status: pre-alpha experimental result
RSMS compatibility: pending central specification mapping

## Question

Can exact recovery from only `(final_state, number_of_steps)` use substantially less memory than standard meet-in-the-middle without introducing side information?

## Method

The midpoint state is partitioned by a deterministic bucket derived from its low `p` bits. For each bucket:

1. enumerate all forward prefixes;
2. retain only prefixes whose midpoint state belongs to that bucket;
3. enumerate all backward suffixes;
4. compare only suffixes whose reconstructed midpoint state belongs to the same bucket;
5. verify every exact full trajectory end-to-end.

The bucket is not stored with the hash and is not supplied to the decoder. It is recomputed from candidate midpoint states during decoding.

## Exactness

The partitioned decoder was compared against the standard MITM decoder over all trajectories through 8 bits. The exact match sets were identical.

## Memory/time tradeoff

For a representative 24-step target under the default 63-bit machine:

| partition bits `p` | midpoint buckets | candidate evaluations | peak retained prefixes | exact matches |
|---:|---:|---:|---:|---:|
| 0 | 1 | 8,192 | 4,096 | 1 |
| 2 | 4 | 32,768 | 1,066 | 1 |
| 4 | 16 | 131,072 | 278 | 1 |
| 6 | 64 | 524,288 | 88 | 1 |

The observed peak memory reduction is close to the expected factor `2^p` for a well-mixed midpoint distribution, while time rises by approximately the same factor because the two half-spaces are revisited per bucket.

This is therefore a memory/time tradeoff, not a reduction in the asymptotic exponent.

## Negative result: simple local orbit signatures

Simple midpoint descriptors such as low-bit buckets, parity, and Hamming-weight summaries did not show a reliable predictive signal for the correct branch beyond their use as exact partition keys. They should not be presented as a trajectory-pruning law.

This negative result matters: the current dynamics appear sufficiently mixed that local state geometry does not trivially reveal the hidden bit history.

## Interpretation

The project now has three exact recovery baselines:

- exhaustive search: minimal conceptual complexity, `O(2^n)`;
- MITM: roughly `O(2^(n/2))` time and memory;
- partitioned MITM: same exponential exponent as MITM, but tunable peak memory at increased time cost.

The next meaningful advance requires a structural rule that reduces the number of half-trajectories actually explored, not merely how they are stored.

## Next experiments

- search for invariants under the reversible maps rather than raw bit-level signatures;
- test multi-level dissection / recursive MITM as an exact memory-time baseline;
- benchmark trajectory-sensitive heuristics only if they preserve completeness or clearly report probabilistic failure;
- compare any new pruning method against standard and partitioned MITM on identical targets.
