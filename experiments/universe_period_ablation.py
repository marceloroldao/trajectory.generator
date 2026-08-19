from __future__ import annotations

import argparse

from trajectory_generator.core import MachineConfig, data_forward, universe_forward


def first_collision(width: int, max_bits: int, *, universe: bool, period: int = 3) -> dict[str, object]:
    cfg = MachineConfig(width=width, universe_period=period)
    states: dict[int, int] = {cfg.initial_state & cfg.mask: 0}

    for t in range(max_bits):
        next_states: dict[int, int] = {}
        collisions = 0
        witness: tuple[int, int, int] | None = None

        for state, prefix in states.items():
            base = universe_forward(state, t, cfg) if universe else state
            for bit in (0, 1):
                final_state = data_forward(base, bit, t, cfg)
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
            a, b, final_state = witness
            return {
                "width": width,
                "universe": universe,
                "period": period if universe else None,
                "first_collision_bits": n,
                "unique_states": len(next_states),
                "collisions": collisions,
                "trajectory_a": format(a, f"0{n}b"),
                "trajectory_b": format(b, f"0{n}b"),
                "final_state": final_state,
            }
        states = next_states

    return {
        "width": width,
        "universe": universe,
        "period": period if universe else None,
        "first_collision_bits": None,
        "tested_through": max_bits,
        "unique_states": len(states),
        "collisions": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--widths", type=int, nargs="+", default=[16, 24, 32])
    parser.add_argument("--periods", type=int, nargs="+", default=[1, 3, 5])
    parser.add_argument("--max-bits", type=int, default=21)
    args = parser.parse_args()

    for width in args.widths:
        print(first_collision(width, args.max_bits, universe=False))
        for period in args.periods:
            print(first_collision(width, args.max_bits, universe=True, period=period))


if __name__ == "__main__":
    main()
