from trajectory_generator.admissible_trajectory import (
    PeriodicAdmissibilityConfig,
    capacity_ok,
    free_count,
)


def frontier(width: int, period: int, limit: int = 100000) -> int:
    cfg = PeriodicAdmissibilityConfig(width=width, period=period)
    last = 0
    for steps in range(limit + 1):
        if not capacity_ok(steps, cfg):
            return last
        last = steps
    return last


if __name__ == "__main__":
    print("width period frontier free_bits_at_frontier")
    for period in range(3, 9):
        cfg = PeriodicAdmissibilityConfig(width=63, period=period)
        n = frontier(63, period)
        print(63, period, n, free_count(n, cfg))
