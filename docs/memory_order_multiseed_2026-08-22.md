# Memory-order multi-seed validation — 2026-08-22

Status: controlled ablation / pre-alpha

## Objective

Repeat the fixed-size canonical-law-bank comparison for local history orders 2, 3, and 4 across multiple deterministic seeds. The purpose is to separate true memory-order effects from artifacts of one canonical bank.

Shared setup:

```text
bank_size = 256
seeds = 8
coherence_levels = 4
policy_map = (1, 3, 4, 0)
update_mode = rolling
period = 3
width = 63
max_steps = 1000
flip test = 128 sampled admissible trajectories at 64 steps, all single-bit flips
base_seed = 12648430
seed stride = 0x9E3779B1
```

The comparison is controlled but not exhaustive over all possible law banks. Memory-4 has 43,046,721 possible local laws, so the canonical bank is only a reproducible sample.

## Results

### Memory 2

```text
frontier range : 265 .. >=1000
median frontier: 632.5 (censored by four non-crossing seeds)
rate300 range  : 0.02557 .. 0.23746 bit/step
median rate300 : 0.13096 bit/step
flip64 range   : 1.318% .. 2.075%
median flip64  : 1.495%
non-crossing   : 4 / 8 seeds
```

The very long frontiers are mostly low-rate, highly rigid regimes. This is not a balanced improvement.

### Memory 3

```text
frontier range : 187 .. >=1000
median frontier: 350.5 (censored by two non-crossing seeds)
rate300 range  : 0.03152 .. 0.33602 bit/step
median rate300 : 0.18179 bit/step
flip64 range   : 1.624% .. 32.788%
median flip64  : 2.173%
non-crossing   : 2 / 8 seeds
```

Two seeds reproduce the previously discovered balanced regime:

```text
seed 13284827235 -> frontier 187, rate300 0.3360245, flip64 32.788%
seed 15939262996 -> frontier 187, rate300 0.3344064, flip64 31.348%
```

This is important: the 187-step / ~33% robustness regime is not unique to the original hand-selected full memory-3 bank. It reappears in independent canonical banks.

### Memory 4

```text
frontier range : 112 .. >=1000
median frontier: 571.0 (censored by three non-crossing seeds)
rate300 range  : 0.03044 .. 0.55361 bit/step
median rate300 : 0.11742 bit/step
flip64 range   : 1.025% .. 5.615%
median flip64  : 2.191%
non-crossing   : 3 / 8 seeds
```

Memory 4 explores a much wider regime. One seed is highly permissive (frontier 112, rate300 ~0.554), while others are extremely rigid. Its best sampled perturbation survival in this run was only ~5.62%, far below the balanced memory-3 regime.

## Interpretation

There is no monotonic law of the form

```text
more local memory -> better trajectory universe
```

Increasing memory order expands the space of possible grammars, but it also increases variance across law banks. In this controlled sample:

- memory 2 often collapses toward rigid low-entropy dynamics;
- memory 4 shows the broadest spread of rates/frontiers but remains fragile under one-bit perturbation;
- memory 3 is the only order in this run that repeatedly reaches a moderate information rate (~0.335 bit/step) together with high perturbation survival (~31–33%).

Therefore the current balanced reference remains memory 3 rather than memory 4.

This does not prove that memory 3 is universally optimal. It shows that the balanced regime found earlier is reproducible across independent deterministic banks, while the memory-4 canonical sample has not yet matched its robustness/capacity Pareto point.

## Exact per-seed snapshot

```text
memory 2:
12648430    >=1000  rate=.0255748  count64=46     flip=.0152853
2667084191  >=1000  rate=.0255748  count64=46     flip=.0146060
5321519952  265     rate=.2370614  count64=79206  flip=.0198975
7975955713  >=1000  rate=.0255748  count64=46     flip=.0139266
10630391474 265     rate=.2374556  count64=85971  flip=.0207520
13284827235 >=1000  rate=.0255748  count64=46     flip=.0139266
15939262996 265     rate=.2370614  count64=79206  flip=.0202637
18593698757 265     rate=.2363462  count64=68260  flip=.0131836

memory 3:
12648430    >=1000  rate=.0476276  count64=890      flip=.0303955
2667084191  262     rate=.2395300  count64=132337   flip=.0200195
5321519952  373     rate=.1702304  count64=9958     flip=.0196533
7975955713  376     rate=.1699867  count64=9468     flip=.0181885
10630391474 >=1000  rate=.0315178  count64=149      flip=.0234375
13284827235 187     rate=.3360245  count64=3670025  flip=.3278809
15939262996 187     rate=.3344064  count64=2621498  flip=.3134766
18593698757 328     rate=.1933412  count64=22177    flip=.0162354

memory 4:
12648430    358     rate=.1778192  count64=14591        flip=.0178223
2667084191  568     rate=.1187150  count64=2901         flip=.0218506
5321519952  >=1000  rate=.0444620  count64=524          flip=.0268555
7975955713  112     rate=.5536074  count64=101141106517 flip=.0473633
10630391474 574     rate=.1161293  count64=1593         flip=.0102539
13284827235 >=1000  rate=.0304395  count64=126          flip=.0153770
15939262996 283     rate=.2217527  count64=80782        flip=.0561523
18593698757 >=1000  rate=.0332289  count64=212          flip=.0219727
```

## Reproduction

```bash
python experiments/memory_order_multiseed.py \
  --bank-size 256 \
  --seeds 8 \
  --max-steps 1000 \
  --samples 128 \
  --base-seed 12648430
```
