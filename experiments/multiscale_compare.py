from trajectory_generator import (
    MultiScaleTrajectoryConfig,
    choose_mode,
    deviation_count,
    multiscale_capacity_ok,
)


def repeated_block(block: list[int], repeats: int) -> list[int]:
    return block * repeats


def max_steps(cfg: MultiScaleTrajectoryConfig) -> int:
    lo, hi = 0, 1
    while multiscale_capacity_ok(hi, cfg):
        lo, hi = hi, hi * 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if multiscale_capacity_ok(mid, cfg):
            lo = mid
        else:
            hi = mid
    return lo


def main() -> None:
    cfg = MultiScaleTrajectoryConfig(width=63, max_deviations=5)
    samples = {
        "one_run_change": [0] * 16 + [1] * 16,
        "0011_repeat": repeated_block([0, 0, 1, 1], 8),
        "00001111_repeat": repeated_block([0, 0, 0, 0, 1, 1, 1, 1], 4),
        "alternating": repeated_block([0, 1], 16),
    }

    print("name,steps,local,fenwick,selected,score")
    for name, bits in samples.items():
        mode, score = choose_mode(bits, cfg) if min(
            deviation_count(bits, "local"), deviation_count(bits, "fenwick")
        ) <= cfg.max_deviations else ("inadmissible", -1)
        print(
            f"{name},{len(bits)},{deviation_count(bits, 'local')},"
            f"{deviation_count(bits, 'fenwick')},{mode},{score}"
        )

    frontier = max_steps(cfg)
    print(f"\n63-bit, K=5, two-mode conservative frontier: {frontier} steps")
    print(f"next step fits: {multiscale_capacity_ok(frontier + 1, cfg)}")


if __name__ == "__main__":
    main()
