# Meet-in-the-middle recovery — 2026-08-19

Status: pre-alpha experimental result
RSMS compatibility: pending central specification mapping

## Question

Can recovery from only `(final_state, number_of_steps)` be made substantially cheaper than exhaustive enumeration without introducing trajectory-side information?

## Method

The decoder splits an `n`-step trajectory at `m = floor(n/2)`.

1. Enumerate every prefix of length `m` from the public initial state and record its intermediate state.
2. Enumerate every suffix of length `n-m` backward from the supplied final state using the exact inverse transition at the correct absolute time.
3. Match forward and backward intermediate states.
4. Verify every joined candidate end-to-end.

The intermediate state is generated during the search. It is not supplied to the decoder and is not stored alongside the final state.

## Complexity

Exhaustive decoding requires order `2^n` complete candidates.

The MITM implementation requires approximately:

- time: `O(2^ceil(n/2) * n)`;
- memory: `O(2^floor(n/2))`.

This is still exponential, but it changes the exponent by approximately one half.

## Validation

The MITM decoder was first checked against the exhaustive decoder over all trajectories for small domains (through 8 bits in the unit-test suite). Both methods return the same exact match sets.

Target recoveries were then performed under the default 63-bit machine:

| steps | exhaustive full-space size | MITM half candidates (approx.) | target recovered | second match found |
|---:|---:|---:|:---:|:---:|
| 22 | 4,194,304 | 4,096 | yes | no |
| 24 | 16,777,216 | 8,192 | yes | no |
| 28 | 268,435,456 | 32,768 | yes | no |
| 32 | 4,294,967,296 | 131,072 | yes | no |
| 36 | 68,719,476,736 | 524,288 | yes | no |

`second match found = no` means the complete MITM search for that specific `(final_state, steps)` found only the original trajectory. It does **not** establish global injectivity over every possible trajectory at that length.

## Interpretation

This is the first decoder in the project that materially exploits reversibility rather than merely scoring candidate trajectories. It demonstrates that the final state and public step count can be sufficient to recover selected trajectories at lengths for which direct full enumeration would be much more expensive.

However:

- the algorithm remains exponential;
- memory grows as approximately `2^(n/2)`;
- target-specific uniqueness does not imply global injectivity;
- the 63-bit information-theoretic bound remains unchanged.

## Reproduction

```bash
python experiments/mitm_demo.py --bits 22
python experiments/mitm_demo.py --bits 28
python experiments/mitm_demo.py --bits 32
```

Run the complete tests with:

```bash
python -m unittest discover -s tests -v
```

## Next research direction

The next goal is to reduce the MITM memory requirement and determine whether the trajectory geometry offers a stronger pruning rule than generic reversible search. Candidate approaches should be benchmarked against MITM as the new exact baseline.
