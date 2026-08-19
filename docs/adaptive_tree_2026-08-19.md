# Adaptive trajectory-tree experiments — 2026-08-19

Status: pre-alpha experimental result

## Objective

Allow different regions of one trajectory to use different recursive relation depths while preserving the strict decoder contract:

`(final_state, steps) -> original trajectory`

No external block boundaries, level choices, side table, checksum, or plaintext hint may be supplied.

## Experiment A — arbitrary block boundaries

`trajectory_generator/adaptive_trajectory_tree.py` ranks the complete representation, including:

- number of blocks;
- each block length;
- recursive level chosen for each block;
- sparse relational coefficients inside each block.

This is an intentionally conservative information accounting: multiple representations of the same trajectory are counted separately, so the envelope may overestimate the number of distinct trajectories but never hides metadata.

With the default parameters:

- width = 63 bits;
- max deviations per block = 5;
- recursive levels = 0..3;
- max blocks = 4;

capacity is exhausted after 48 steps. The 49-step representation envelope exceeds `2^63`.

### Interpretation

Arbitrary adaptive cuts are too expensive under a 63-bit fixed final state. The freedom to choose boundaries consumes more address space than the local structural simplification saves. This is retained as a negative result.

## Experiment B — public midpoint split

`trajectory_generator/dyadic_trajectory_tree.py` removes the arbitrary-boundary cost. The only optional split is the public midpoint, so the cut position does not need to be encoded.

The final address has two disjoint regions:

1. unsplit: one recursive-relation block;
2. split: left midpoint block + right midpoint block, each with an independently selected recursive level.

The level choices and both block payloads are encoded in the final state itself.

With the same default width/deviation/depth parameters, the conservative capacity frontier becomes:

- 274 steps: fits inside `2^63`;
- 275 steps: exceeds `2^63`.

This is a substantial improvement over arbitrary cuts, but still far below the 10,672-step frontier of the single-global-level recursive model because two independently described blocks require a product address space.

## Meaning of the result

Adaptive structure gives **coverage**, not free capacity.

A global recursive model is extremely efficient when one relation depth explains the whole trajectory. The dyadic model is useful when different halves have different structural laws, but it pays for that flexibility in address space.

The emerging design rule is:

> A useful trajectory hierarchy must make structural boundaries predictable from public dynamics or derive them from a very low-entropy grammar. Arbitrary segmentation destroys the gain.

## Reproduction

```bash
python -m unittest tests.test_dyadic_trajectory_tree -v
```

## Next direction

Investigate deterministic recursive dyadic grammars where a node is split only when a public relation criterion is met, and where the tree shape can be inferred during decoding rather than explicitly ranked. The scientific target is to determine whether tree structure can become a property of the trajectory dynamics instead of metadata about the trajectory.
