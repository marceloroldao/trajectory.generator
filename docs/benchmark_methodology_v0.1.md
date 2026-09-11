# Benchmark methodology — trajectory.generator v0.1

Purpose: measure the frozen Python reference implementation before optimization.

## Operations

- `count(T)`
- `rank(path)`
- `unrank(address,T)`
- `append(address,T,z)`
- `access(address,T,k)`

## Horizons

Use T = 16, 64, 128, 218. Include T=219 for `count` to preserve the frontier check.

## Timing

- Python 3.12 reference implementation.
- `time.perf_counter_ns()`.
- Report min / median / max over repeated calls.
- Keep deterministic addresses from a fixed PRNG seed.
- Distinguish warm-cache measurements from any later cold-process benchmark.

## Memory

Use `tracemalloc` peak bytes around rank and unrank. This measures Python allocations, not total RSS.

## Interpretation rules

1. Do not compare asymptotic block complexity with wall-clock latency as if they were the same metric.
2. Big-integer width grows with horizon and must be reported separately in later optimized benchmarks.
3. The address payload is compared independently from runtime metadata/caches.
4. Do not claim generic compression; comparisons apply only to the restricted admissible trajectory language.
5. An optimization is accepted only if all frozen differential tests remain green.

Reference harness: `benchmarks/reference_v01_benchmark.py`.
