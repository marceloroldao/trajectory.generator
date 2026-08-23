"""Controlled comparison of local memory orders 2, 3, and 4.

The complete rule space has size 3^(2^m):

    m=2 -> 81
    m=3 -> 6,561
    m=4 -> 43,046,721

An exhaustive all-law comparison therefore stops being practical at memory 4.
This experiment uses the same deterministic canonical bank size at each memory
order so that memory length can be varied without also changing candidate-bank
size by orders of magnitude.

Important: a common fixed bank/selector can become degenerate at a particular
memory order.  Therefore this script reports not only frontier but also finite
rate, admissible count at 64 steps, and sampled one-bit perturbation survival.
A very long/non-crossing frontier with near-zero rate is *not* treated as an
advantage.
"""

from __future__ import annotations

import argparse
import math
import random
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
    return tuple(_mix64(seed ^ (memory << 48) ^ (rule_id << 16) ^ s) % 3 for s in range(1 << memory))


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
        return bank[selected(state, t % 3, cfg.policy_map[c])][state]

    @lru_cache(maxsize=None)
    def suffix(state: int, c: int, t: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        return sum(
            suffix(
                next_state(state, b, cfg.memory),
                update_c(c, state, b),
                t + 1,
                remaining - 1,
            )
            for b in allowed(action(state, t, c))
        )

    def count(steps: int) -> int:
        if steps <= cfg.memory:
            return 1 << steps
        rem = steps - cfg.memory
        return sum(suffix(s, initial_c(s), cfg.memory, rem) for s in range(1 << cfg.memory))

    def validate(bits: list[int]) -> bool:
        if len(bits) <= cfg.memory:
            return True
        state = 0
        for b in bits[:cfg.memory]:
            state = (state << 1) | b
        c = initial_c(state)
        for t, bit in enumerate(bits[cfg.memory:], start=cfg.memory):
            if bit not in allowed(action(state, t, c)):
                return False
            c = update_c(c, state, bit)
            state = next_state(state, bit, cfg.memory)
        return True

    def unrank(rank: int, steps: int) -> list[int]:
        if steps <= cfg.memory:
            return [((rank >> (steps - 1 - i)) & 1) for i in range(steps)] if steps else []
        rem = steps - cfg.memory
        prefix = None
        for s in range(1 << cfg.memory):
            n = suffix(s, initial_c(s), cfg.memory, rem)
            if rank < n:
                prefix = s
                break
            rank -= n
        assert prefix is not None
        bits = [((prefix >> (cfg.memory - 1 - i)) & 1) for i in range(cfg.memory)]
        state = prefix
        c = initial_c(state)
        for t in range(cfg.memory, steps):
            rem_after = steps - t - 1
            for bit in allowed(action(state, t, c)):
                ns = next_state(state, bit, cfg.memory)
                nc = update_c(c, state, bit)
                n = suffix(ns, nc, t + 1, rem_after)
                if rank < n:
                    bits.append(bit)
                    state, c = ns, nc
                    break
                rank -= n
        return bits

    return count, validate, unrank


def frontier(count, width: int, max_steps: int = 5000) -> tuple[int, bool]:
    limit = 1 << width
    last = 0
    for n in range(max_steps + 1):
        if count(n) > limit:
            return n - 1, True
        last = n
    return last, False


def flip_survival(validate, unrank, total: int, steps: int, samples: int, seed: int) -> float:
    if total <= 0:
        return 0.0
    rng = random.Random(seed)
    tested = survived = 0
    for _ in range(min(samples, total)):
        bits = unrank(rng.randrange(total), steps)
        for pos in range(steps):
            trial = bits.copy()
            trial[pos] ^= 1
            tested += 1
            survived += int(validate(trial))
    return survived / tested if tested else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank-size", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0xC0FFEE)
    ap.add_argument("--max-steps", type=int, default=5000)
    ap.add_argument("--samples", type=int, default=512)
    args = ap.parse_args()

    print("memory bank frontier crossed rate300 count64 flip64")
    for memory in (2, 3, 4):
        cfg = Config(memory=memory, bank_size=args.bank_size, seed=args.seed)
        count, validate, unrank = build(cfg)
        f, crossed = frontier(count, cfg.width, args.max_steps)
        c300 = count(300)
        rate = math.log2(c300) / 300 if c300 else 0.0
        c64 = count(64)
        survival = flip_survival(validate, unrank, c64, 64, args.samples, args.seed)
        marker = str(f) if crossed else f">={f}"
        print(f"{memory:6d} {args.bank_size:4d} {marker:>8s} {str(crossed):>7s} {rate:7.4f} {c64:8d} {survival:7.4f}")


if __name__ == "__main__":
    main()
