# Memory-4 targeted policy search — 2026-08-22

Status: controlled targeted search / pre-alpha

## Objective

The multi-seed memory-order ablation showed that memory 4 explores a much wider range of entropy/frontier regimes than memory 3, but the inherited memory-3 coherence policy is usually fragile.

This experiment therefore searches memory 4 directly over the same public coherence design space used by the memory-3 work:

```text
update_mode in {occupancy, signed_bit, rolling}
policy_map in {0,1,2,3,4}^4
```

The canonical law bank is held fixed at:

```text
memory = 4
bank_size = 256
seed = 12648430
width = 63
```

No named spectral constant is targeted.

## Main result

Memory 4 can substantially extend the exact 63-bit frontier, but in this search the gain remains strongly coupled to fragility.

The longest candidate inside the initial finite-rate window (`0.20 <= rate300 <= 0.45`) was:

```text
update_mode = occupancy
policy_map  = (0, 0, 3, 0)
frontier63  = 313
rate300     ~= 0.20207 bit/step
flip64      ~= 1.80%
```

A more robust candidate found in the same search was:

```text
update_mode = occupancy
policy_map  = (0, 3, 4, 2)
frontier63  = 244
rate300     ~= 0.25654 bit/step
flip64      ~= 7.23%
```

Other representative points:

```text
occupancy (1,4,2,1): frontier 307, rate ~0.20456, flip ~4.17%
occupancy (1,3,4,0): frontier 238, rate ~0.26181, flip ~2.38%
signed_bit (1,0,0,1): frontier 250, rate ~0.25061, flip ~0.88%
```

The perturbation estimates above use 512 sampled admissible 64-step trajectories with all 64 one-bit flips tested.

## Comparison with the memory-3 balanced reference

Current balanced memory-3 reference:

```text
frontier63 = 187
rate300 ~= 0.33602 bit/step
flip64 ~= 32.80%
```

Memory 4 therefore wins easily on raw frontier in several configurations, but none of the tested memory-4 candidates approaches the memory-3 perturbation robustness.

The present evidence supports a Pareto interpretation:

```text
memory 3 -> shorter frontier, substantially broader local stability
memory 4 -> longer frontier available, but much greater structural fragility
```

This is not evidence that memory 3 is universally optimal. It shows that, for the current selector family and canonical memory-4 bank, additional local causal depth has not yet produced a balanced improvement over the 187-step memory-3 point.

## Methodological note

A long frontier is not a compression claim. These are constrained admissible trajectory families. The information-theoretic accounting remains:

```text
H_adm(n) = log2 |A_n|
```

and exact addressing by one 63-bit final state is valid only while `|A_n| <= 2^63`.

## Reproduction

```bash
python experiments/memory4_policy_search.py \
  --seed 12648430 \
  --bank-size 256 \
  --min-rate 0.20 \
  --max-rate 0.45 \
  --top 30 \
  --samples 256
```
