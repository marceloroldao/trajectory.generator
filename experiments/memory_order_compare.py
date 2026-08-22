"""Controlled comparison of local memory orders 2, 3, and 4.

Why a fixed canonical bank?

The complete rule space has size 3^(2^m):

    m=2 -> 81
    m=3 -> 6,561
    m=4 -> 43,046,721

An exhaustive all-law comparison therefore stops being practical at memory 4.
This experiment uses the same deterministic canonical bank size at each memory
order so that memory length can be varied without also changing the number of
candidate laws by orders of magnitude.

This is a controlled ablation, not a replacement for the exhaustive memory-2
and memory-3 scans already in the repository.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from functools import lru_cache

FORCE_0 = 0
FORCE_1 = 1
FREE = 2


def _mix64(x: int) -> int:
    x &= (1 << 64) - 1
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & ((1 << 64) - 1)
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & ((1 << 64) - 1)
    x ^= x >> 31
    return x


def canonical_rule(memory: int, rule_id: int, seed: int) -> tuple[int, ...]:
    states = 1 << memory
    out = []
    for s in range(states):
        z = _mix64(seed ^ (memory << 48) ^ (rule_id << 16) ^ s)
        out.append(z % 3)
    return tuple(out)


def canonical_bank(memory: int, bank_size: int, seed: int) -> tuple[tuple[int, ...], ...]:
    return tuple(canonical_rule(memory, i, seed) for i in range(bank_size))


def allowed(action: int) -> tuple[int, ...]:
    return (0, 1) if action == FREE else (action,)


def next_state(state: int, bit: int, memory: int) -> int:
    return ((state << 1) & ((1 << memory) - 1)) | bit


def rule_features(rule: tuple[int, ...], memory: int) -> tuple[int, int, int, int]:
    states = 1 << memory
    free = rule.count(FREE)
    f0 = rule.count(FORCE_0)
    f1 = rule.count(FORCE_1)
    freedom_balance = free * (states - free)
    force_symmetry = -abs(f0 - f1)
    balanced_forced = 0
    covered = set()
    center = memory / 2.0
    for state, action in enumerate(rule):
        for bit in allowed(action):
            covered.add(next_state(state, bit, memory))
        if action != FREE:
            ns = next_state(state, action, memory)
            if abs(ns.bit_count() - center) <= 0.5:
                balanced_forced += 1
    return freedom_balance, force_symmetry, balanced_forced, len(covered)


# Same feature semantics as the memory-3 policy experiments, generalized.
POLICIES: tuple[tuple[int, ...], ...] = (
    (0, 1, 3, 3, 0, 1, 0, 3, 0),
    (3, 3, 0, 3, 1, 2, 2, 0, 1),
    (2, 3, 1, 3, 1, 2, 0, 3, 0),
    (0, 2, 3, 1, 2, 2, 1, 5, 0),
    (0, 0, 3, 4, 0, 2, 2, 3, 0),
)


@dataclass(frozen=True)
class Config:
    memory: int
    bank_size: int = 256
    seed: int = 0xC0FFEE
    coherence_levels: int = 4
    policy_map: tuple[int, ...] = (1, 3, 4, 0)
    update_mode: str = "rolling"
    width: int = 63


def build(cfg: Config):
    bank = canonical_bank(cfg.memory, cfg.bank_size, cfg.seed)
    globals_ = tuple(rule_features(r, cfg.memory) for r in bank)
    mask = (1 << cfg.memory) - 1
    center = cfg.memory / 2.0

    def initial_c(state: int) -> int:
        return min(cfg.coherence_levels - 1, state.bit_count())

    def update_c(c: int, state: int, bit: int) -> int:
        ns = next_state(state, bit, cfg.memory)
        top = cfg.coherence_levels - 1
        if cfg.update_mode == "occupancy":
            balanced = abs(ns.bit_count() - center) <= 0.5
            return min(top, c + 1) if balanced else max(0, c - 1)
        if cfg.update_mode == "signed_bit":
            return (c + (1 if bit else -1)) % cfg.coherence_levels
        return ((c << 1) ^ ns ^ bit) % cfg.coherence_levels

    @lru_cache(maxsize=None)
    def selected(state: int, phase: int, policy_idx: int) -> int:
        weights = POLICIES[policy_idx]
        best_i = 0
        best_score = None
        pop = state.bit_count()
        for i, rule in enumerate(bank):
            action = rule[state]
            opts = allowed(action)
            balanced_next = sum(
                abs(next_state(state, b, cfg.memory).bit_count() - center) <= 0.5
                for b in opts
            )
            extreme = pop in (0, cfg.memory)
            extreme_restore = int(
                extreme
                and action != FREE
                and abs(next_state(state, action, cfg.memory).bit_count() - center) < abs(pop - center)
            )
            phase_free = int(not extreme and phase == 1 and action == FREE)
            vec = (
                extreme_restore,
                phase_free,
                balanced_next,
                int(action != FREE),
                int(action == FREE),
                *globals_[i],
            )
            score = sum(a * b for a, b in zip(vec, weights))
            if best_score is None or score > best_score:
                best_score = score
                best_i = i
        return best_i

    def action(state: int, t: int, c: int) -> int:
        pidx = cfg.policy_map[c]
        return bank[selected(state, t % 3, pidx)][state]

    @lru_cache(maxsize=None)
    def suffix(state: int, c: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        total = 0
        for b in allowed(action(state, t, c)):
            total += suffix(
                next_state(state, b, cfg.memory),
                update_c(c, state, b),
                t + 1,
                remaining - 1,
            )
        return total

    def count(steps: int) -> int:
        if steps <= cfg.memory:
            return 1 << steps
        rem = steps - cfg.memory
        return sum(suffix(s, initial_c(s), cfg.memory, rem) for s in range(1 << cfg.memory))

    return count


def frontier(count, width: int, max_steps: int = 600) -> int:
    limit = 1 << width
    for n in range(max_steps + 1):
        if count(n) > limit:
            return n - 1
    return max_steps


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank-size", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0xC0FFEE)
    ap.add_argument("--max-steps", type=int, default=600)
    args = ap.parse_args()

    print("memory bank frontier63 rate300")
    for memory in (2, 3, 4):
        cfg = Config(memory=memory, bank_size=args.bank_size, seed=args.seed)
        count = build(cfg)
        f = frontier(count, cfg.width, args.max_steps)
        c300 = count(300)
        rate = math.log2(c300) / 300 if c300 else 0.0
        print(f"{memory:6d} {args.bank_size:4d} {f:10d} {rate:7.4f}")


if __name__ == "__main__":
    main()
