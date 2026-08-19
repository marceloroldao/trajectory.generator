from trajectory_generator.recursive_trajectory import (
    RecursiveTrajectoryConfig,
    choose_level,
    deviation_count,
    encode_recursive_trajectory,
    decode_recursive_trajectory,
)


def report(name: str, bits: list[int], cfg: RecursiveTrajectoryConfig) -> None:
    scores = [deviation_count(bits, level) for level in range(cfg.max_level + 1)]
    try:
        level, score = choose_level(bits, cfg)
        state, steps = encode_recursive_trajectory(bits, cfg)
        recovered = decode_recursive_trajectory(state, steps, cfg)
        status = "PASS" if recovered == bits else "FAIL"
        print(f"{name:16s} n={len(bits):4d} scores={scores} best=L{level}:{score} roundtrip={status}")
    except ValueError as exc:
        print(f"{name:16s} n={len(bits):4d} scores={scores} rejected={exc}")


def main() -> None:
    cfg = RecursiveTrajectoryConfig(width=63, max_deviations=5, max_level=3)
    samples = {
        "constant-0": [0] * 64,
        "constant-1": [1] * 64,
        "alternating": [0, 1] * 32,
        "period-0011": [0, 0, 1, 1] * 16,
        "blocks-00001111": [0, 0, 0, 0, 1, 1, 1, 1] * 8,
    }
    for name, bits in samples.items():
        report(name, bits, cfg)


if __name__ == "__main__":
    main()
