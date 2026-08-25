"""Hybrid local-memory 3<->4 search.

The machine always carries the last four recovered bits internally, but the
active local grammar normally consults only the low 3-bit history.  Memory-4 is
activated only when the deterministic coherence bucket belongs to a public
critical set.

No switch history is stored: during decoding the same coherence trajectory can
be regenerated from the recovered prefix.  This experiment focuses on exact
family counting and Pareto diagnostics; it does not yet promote a hybrid codec
into the public API.

For search speed, admissible-family counts are propagated iteratively over the
finite causal state (history4, coherence_bucket).  This is equivalent to the
recursive suffix counting used by the exact codecs for total-count purposes.
"""

from __future__ import annotations

import argparse
import itertools
import math
import random
from functools import lru_cache

from memory_order_compare import (
    Config,
    POLICIES,
    allowed,
    canonical_bank,
    next_state,
    rule_features,
)


class Hybrid34:
    def __init__(
        self,
        *,
        bank_size: int = 256,
        seed: int = 12648430,
        policy_map: tuple[int, ...] = (1, 3, 4, 0),
        update_mode: str = "rolling",
        critical_buckets: tuple[int, ...] = (0,),
        coherence_levels: int = 4,
    ) -> None:
        self.bank_size = bank_size
        self.seed = seed
        self.policy_map = policy_map
        self.update_mode = update_mode
        self.critical_buckets = frozenset(critical_buckets)
        self.coherence_levels = coherence_levels
        if len(policy_map) != coherence_levels:
            raise ValueError("policy_map length must equal coherence_levels")
        if update_mode not in ("occupancy", "signed_bit", "rolling"):
            raise ValueError("unknown update_mode")

        self.banks = {m: canonical_bank(m, bank_size, seed) for m in (3, 4)}
        self.globals = {
            m: tuple(rule_features(rule, m) for rule in self.banks[m])
            for m in (3, 4)
        }
        self._precompute_actions()

    def initial_coherence(self, history4: int) -> int:
        return min(self.coherence_levels - 1, history4.bit_count())

    def update_coherence(self, c: int, history4: int, bit: int) -> int:
        nxt4 = next_state(history4, bit, 4)
        top = self.coherence_levels - 1
        if self.update_mode == "occupancy":
            balanced = abs(nxt4.bit_count() - 2.0) <= 0.5
            return min(top, c + 1) if balanced else max(0, c - 1)
        if self.update_mode == "signed_bit":
            return (c + (1 if bit else -1)) % self.coherence_levels
        return ((c << 1) ^ nxt4 ^ bit) % self.coherence_levels

    def active_order(self, coherence: int) -> int:
        return 4 if coherence in self.critical_buckets else 3

    @lru_cache(maxsize=None)
    def _selected_rule(self, memory: int, state: int, phase: int, policy_index: int) -> int:
        weights = POLICIES[policy_index]
        center = memory / 2.0
        pop = state.bit_count()
        best_index = 0
        best_score = None
        for i, rule in enumerate(self.banks[memory]):
            action = rule[state]
            opts = allowed(action)
            balanced_next = sum(
                abs(next_state(state, bit, memory).bit_count() - center) <= 0.5
                for bit in opts
            )
            extreme = pop in (0, memory)
            extreme_restore = int(
                extreme
                and action != 2
                and abs(next_state(state, action, memory).bit_count() - center)
                < abs(pop - center)
            )
            phase_free = int(not extreme and phase == 1 and action == 2)
            vec = (
                extreme_restore,
                phase_free,
                balanced_next,
                int(action != 2),
                int(action == 2),
                *self.globals[memory][i],
            )
            score = sum(a * b for a, b in zip(vec, weights))
            if best_score is None or score > best_score:
                best_score = score
                best_index = i
        return best_index

    def _precompute_actions(self) -> None:
        self.actions: dict[tuple[int, int, int, int], int] = {}
        for memory in (3, 4):
            for state in range(1 << memory):
                for phase in range(3):
                    for pidx in range(len(POLICIES)):
                        ridx = self._selected_rule(memory, state, phase, pidx)
                        self.actions[(memory, state, phase, pidx)] = self.banks[memory][ridx][state]

    def action(self, history4: int, t: int, coherence: int) -> int:
        memory = self.active_order(coherence)
        state = history4 & ((1 << memory) - 1)
        pidx = self.policy_map[coherence]
        return self.actions[(memory, state, t % 3, pidx)]

    def counts_through(self, max_steps: int) -> list[int]:
        if max_steps < 0:
            raise ValueError("max_steps must be non-negative")
        out = [1]
        for n in range(1, min(4, max_steps) + 1):
            out.append(1 << n)
        if max_steps <= 4:
            return out

        # Every 4-bit prefix is initially admissible.
        dist: dict[tuple[int, int], int] = {
            (h4, self.initial_coherence(h4)): 1 for h4 in range(16)
        }
        out.append(sum(dist.values()))  # n=4 already equals 16; overwritten below
        out = out[:5]

        for t in range(4, max_steps):
            nxt_dist: dict[tuple[int, int], int] = {}
            for (h4, c), count in dist.items():
                for bit in allowed(self.action(h4, t, c)):
                    nh = next_state(h4, bit, 4)
                    nc = self.update_coherence(c, h4, bit)
                    key = (nh, nc)
                    nxt_dist[key] = nxt_dist.get(key, 0) + count
            dist = nxt_dist
            out.append(sum(dist.values()))
        return out

    def frontier_and_rate(self, max_steps: int = 1000, width: int = 63) -> tuple[int, bool, float, list[int]]:
        counts = self.counts_through(max(max_steps, 300))
        limit = 1 << width
        frontier = max_steps
        crossed = False
        for n in range(min(max_steps, len(counts) - 1) + 1):
            if counts[n] > limit:
                frontier = n - 1
                crossed = True
                break
        rate300 = math.log2(counts[300]) / 300 if len(counts) > 300 and counts[300] else 0.0
        return frontier, crossed, rate300, counts


def search(args: argparse.Namespace) -> None:
    rows = []
    bucket_sets = [
        tuple(i for i in range(4) if mask & (1 << i))
        for mask in range(1, 15)
    ]
    for mode in ("occupancy", "signed_bit", "rolling"):
        for critical in bucket_sets:
            machine = Hybrid34(
                bank_size=args.bank_size,
                seed=args.seed,
                policy_map=tuple(args.policy_map),
                update_mode=mode,
                critical_buckets=critical,
            )
            frontier, crossed, rate300, counts = machine.frontier_and_rate(args.max_steps)
            if not args.min_rate <= rate300 <= args.max_rate:
                continue
            rows.append((frontier, crossed, rate300, mode, critical, counts[64]))

    rows.sort(key=lambda r: (r[0], r[2]), reverse=True)
    print("frontier crossed rate300 count64 mode critical_buckets")
    for row in rows[: args.top]:
        f, crossed, rate, mode, critical, c64 = row
        marker = str(f) if crossed else f">={f}"
        print(f"{marker:>8s} {str(crossed):>7s} {rate:7.4f} {c64:12d} {mode:10s} {critical}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank-size", type=int, default=256)
    ap.add_argument("--seed", type=int, default=12648430)
    ap.add_argument("--max-steps", type=int, default=1000)
    ap.add_argument("--min-rate", type=float, default=0.20)
    ap.add_argument("--max-rate", type=float, default=0.50)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--policy-map", type=int, nargs=4, default=(1, 3, 4, 0))
    args = ap.parse_args()
    search(args)


if __name__ == "__main__":
    main()
