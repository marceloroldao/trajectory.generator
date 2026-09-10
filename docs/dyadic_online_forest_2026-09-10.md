# Dyadic online forest — 2026-09-10

## Goal

Seek one trajectory representation that is both causal/online and random-access friendly, avoiding an O(T) conversion between endpoint/colex rank and hierarchical rank.

## Construction

Each new transition begins as a length-1 block. Equal-size adjacent blocks merge by binary carry into lengths 2, 4, 8, ... . Each block stores a hierarchical rank conditioned on its start and end private states.

For T=218 the canonical forest shape is exactly:

`[128, 64, 16, 8, 2]`

Only five blocks are present.

## Random access

The construction passed exact reconstruction tests. In 200 sampled T=218 trajectories with 16 random symbol queries each, every query was correct and required at most 8 recursive levels inside its target block.

Thus the forest has the desired online merge structure and logarithmic-depth symbol access.

## Bit cost

A practical serialization was tested:

- 3 bits for initial prefix;
- for each dyadic block, 4 bits for its end private state;
- fixed-width local rank using `ceil(log2 paths(start,end,interval))` bits.

On 200 sampled T=218 trajectories, total serialized size ranged from 23 to 59 bits, average 46.685 bits. This sample is not an entropy claim because the sampling distribution is not uniform over all admissible trajectories.

An exact dynamic program over every reachable chain of block-boundary states found the true serialization bounds at T=218:

- minimum: 23 bits;
- maximum: 80 bits.

Therefore this straightforward field serialization does **not** preserve the 63-bit worst-case target.

## Interpretation

The structural idea remains promising. The excess comes from independently coding each 4-bit block endpoint and then coding the conditional block rank. Endpoints and ranks are correlated, so this fixed-field representation wastes information.

The next experiment should jointly rank `(endpoint, local_rank)` choices at each dyadic block, or jointly enumerate the entire five-block boundary/rank chain while retaining the dyadic decomposition. Since the complete T=218 language has only 9,131,204,053,820,206,208 trajectories, information theory guarantees that a global 63-bit enumeration exists. The open question is whether that enumeration can preserve online dyadic updates and logarithmic random access without reintroducing an O(T) conversion.
