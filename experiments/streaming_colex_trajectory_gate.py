"""Acceptance gate for the streaming colex trajectory address."""

from trajectory_generator.hierarchical_trajectory import (
    HierarchicalTrajectoryConfig,
    admissible_count as hierarchical_count,
)
from trajectory_generator.streaming_colex_trajectory import (
    StreamingColexConfig,
    admissible_count,
    capacity_ok,
    decode,
    encode,
)


def frontier(width, max_changes):
    cfg = StreamingColexConfig(width=width, max_changes=max_changes)
    lo, hi = 0, 1
    while capacity_ok(hi, cfg):
        lo, hi = hi, hi * 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if capacity_ok(mid, cfg):
            lo = mid
        else:
            hi = mid
    return lo


def exhaustive_gate(steps=10, max_changes=3):
    cfg = StreamingColexConfig(width=32, max_changes=max_changes)
    seen = set()
    checked = 0

    for word in range(1 << steps):
        bits = [(word >> i) & 1 for i in range(steps)]
        changes = sum(bits[i] != bits[i - 1] for i in range(1, steps))
        if changes > max_changes:
            continue

        state, got_steps = encode(bits, cfg)
        if got_steps != steps or state in seen:
            return False, checked, "collision or step mismatch"
        seen.add(state)

        if decode(state, steps, cfg) != bits:
            return False, checked, "decode mismatch"
        checked += 1

    expected = admissible_count(steps, cfg)
    return checked == expected == len(seen), checked, None


def main():
    ok, checked, error = exhaustive_gate()
    print(
        "STREAMING_COLEX_EXHAUSTIVE",
        "PASS", ok,
        "checked", checked,
        "error", error,
    )

    cfg = StreamingColexConfig(width=63, max_changes=5)
    hcfg = HierarchicalTrajectoryConfig(width=63, max_changes=5)
    f = frontier(63, 5)
    used = admissible_count(f, cfg)
    capacity = 1 << 63

    print(
        "STREAMING_COLEX_63BIT",
        "frontier", f,
        "PASS_frontier", capacity_ok(f, cfg),
        "PASS_frontier_plus_1", not capacity_ok(f + 1, cfg),
        "states_used", used,
        "capacity", capacity,
        "occupancy", used / capacity,
        "same_family_as_hierarchical",
        used == hierarchical_count(f, hcfg),
    )

    change_positions = {1, 100, 1000, 5000, f - 1}
    bits = [0] * f
    current = 0
    for i in range(f):
        if i in change_positions:
            current ^= 1
        bits[i] = current

    state, steps = encode(bits, cfg)
    print(
        "STREAMING_COLEX_FULL_FRONTIER_ROUNDTRIP",
        "PASS", decode(state, steps, cfg) == bits,
        "steps", steps,
        "state_bits", state.bit_length(),
    )


if __name__ == "__main__":
    main()
