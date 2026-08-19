# Universe-period ablation — 2026-08-19

Status: pre-alpha negative/neutral result

## Question

Does the deterministic universe intervention improve the collision frontier, and is period 3 special?

The same data transition was tested with no universe transition and with universe periods 1, 3, and 5. Each configuration was exhaustively expanded until its first exact final-state collision.

## Results

| state width | no universe | period 1 | period 3 | period 5 |
|---:|---:|---:|---:|---:|
| 16 | 10 bits | 7 bits | 10 bits | 9 bits |
| 24 | 13 bits | 12 bits | 14 bits | 14 bits |
| 32 | 17 bits | 17 bits | 17 bits | 18 bits |

The numbers report the first trajectory length at which at least two distinct bit trajectories produced the same final state for that same step count.

## Interpretation

There is currently **no evidence that period 3 is universally optimal or structurally privileged**.

- At width 16, period 3 ties the no-universe case and beats periods 1 and 5.
- At width 24, periods 3 and 5 delay the first observed collision by one step relative to no universe.
- At width 32, no-universe, period 1, and period 3 tie; period 5 delays the first collision by one step.

The universe mechanism therefore changes collision structure, but the present data do not justify treating the value 3 as a law. It remains an experimental parameter.

This negative/neutral result is retained because the project requires reproducible evidence rather than post-hoc selection of favorable parameters.

## Reproduction

```bash
python experiments/universe_period_ablation.py --widths 16 24 32 --periods 1 3 5 --max-bits 21
```

## Next test

Sweep a wider set of periods under identical widths and compare not only first-collision depth but collision multiplicity, orbit radius statistics, and sensitivity to input ordering. Parameter selection must be done on a training domain and then validated on held-out widths to avoid tuning the dynamics to the benchmark.
