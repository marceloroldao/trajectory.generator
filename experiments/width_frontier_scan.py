from __future__ import annotations

import argparse

from trajectory_generator.core import MachineConfig, step_forward


def first_collision(width: int, max_bits: int) -> dict[str, object]:
    cfg = MachineConfig(width=width)
    states: dict[int, int] = {cfg.initial_state & cfg.mask: 0}

    for t in range(max_bits):
        next_states: dict[int, int] = {}
        collisions = 0
        witness: tuple[int, int, int] | None = None

        for state, prefix in states.items():
            for bit in (0, 1):
                final_state = step_forward(state, bit, t, cfg)
                trajectory = (prefix << 1) | bit
                previous = next_states.get(final_state)
                if previous is None:
                    next_states[final_state] = trajectory
                else:
                    collisions += 1
                    if witness is None:
                        witness = (previous, trajectory, final_state)

        n = t + 1
        if witness is not None:
            a, b, state = witness
            return {
                "width": width,
                "first_collision_bits": n,
                "trajectories": 1 << n,
                "unique_states": len(next_states),
                "collisions": collisions,
                "trajectory_a": format(a, f"0{n}b"),
                "trajectory_b": format(b, f"0{n}b"),
                "final_state": state,
            }
        states = next_states

    return {
        "width": width,
        "first_collision_bits": None,
        "tested_through": max_bits,
        "trajectories": 1 << max_bits,
        "unique_states": len(states),
        "collisions": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--widths", type=int, nargs="+", default=[16, 24, 32])
    parser.add_argument("--max-bits", type=int, default=21)
    args = parser.parse_args()

    for width in args.widths:
        if width < 4 or width > 64:
            raise SystemExit(f"invalid width: {width}")
        result = first_collision(width, args.max_bits)
        print(result)


if __name__ == "__main__":
    main()
