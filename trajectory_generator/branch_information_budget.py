"""Exact information budget created by causal branch events.

Let D_t(u) be the number of admissible histories at causal node u after t
physical transitions, and let d+(u) be the public outgoing edge multiplicity.

The total number of histories is:

    N_t = sum_u D_t(u).

Every history at u produces exactly d+(u) successor histories, hence:

    N_(t+1)
      = sum_u D_t(u) d+(u)
      = N_t + B_t

where:

    B_t = sum_u D_t(u) (d+(u)-1).

B_t is the exact number of *additional* successor histories created by causal
branching at physical step t.

Consequences:

- if every populated causal state is deterministic, B_t=0 and N_(t+1)=N_t;
- deterministic flights create zero new history information;
- all growth of the exact reversible history space is sourced at branch events.

In Shannon-style address units for the complete exact family:

    H_t = log2 N_t

and the physical-step information increment is:

    Delta H_t = log2(N_(t+1)/N_t)
              = log2(1 + B_t/N_t).

The increments telescope exactly:

    H_T - H_0 = sum_{t=0}^{T-1} Delta H_t.

This module treats that identity as the vertical-capacity budget of the minimal
reversible completion. It does not claim that a particular numeric fiber chart
is physical.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Hashable, Mapping, Sequence


Node = Hashable


@dataclass(frozen=True)
class InformationBudgetStep:
    time: int
    total_before: int
    branch_excess: int
    total_after: int
    information_bits_before: float
    information_bits_after: float
    delta_bits: float
    populated_nodes: int
    populated_branch_nodes: int

    @property
    def deterministic(self) -> bool:
        return self.branch_excess == 0


def step_counts(
    adjacency: Mapping[Node, Sequence[Node]],
    counts: Mapping[Node, int],
) -> dict[Node, int]:
    nodes = set(adjacency)
    for targets in adjacency.values():
        nodes.update(targets)

    nxt = {node: 0 for node in nodes}
    for source, count in counts.items():
        if not count:
            continue
        for target in adjacency.get(source, ()):
            nxt[target] += count
    return nxt


def branch_excess(
    adjacency: Mapping[Node, Sequence[Node]],
    counts: Mapping[Node, int],
) -> int:
    return sum(
        count * (len(adjacency.get(node, ())) - 1)
        for node, count in counts.items()
        if count and len(adjacency.get(node, ())) >= 1
    )


def budget_step(
    adjacency: Mapping[Node, Sequence[Node]],
    counts: Mapping[Node, int],
    *,
    time: int,
) -> tuple[InformationBudgetStep, dict[Node, int]]:
    if time < 0:
        raise ValueError("time must be >= 0")

    total_before = sum(counts.values())
    if total_before <= 0:
        raise ValueError(
            "budget requires at least one admissible history"
        )

    excess = branch_excess(adjacency, counts)
    nxt = step_counts(adjacency, counts)
    total_after = sum(nxt.values())

    if total_after != total_before + excess:
        raise AssertionError(
            "branch-excess conservation identity failed"
        )

    populated = sum(
        1 for count in counts.values()
        if count
    )
    populated_branches = sum(
        1
        for node, count in counts.items()
        if count and len(adjacency.get(node, ())) > 1
    )

    before_bits = log2(total_before)
    after_bits = log2(total_after)

    return (
        InformationBudgetStep(
            time=time,
            total_before=total_before,
            branch_excess=excess,
            total_after=total_after,
            information_bits_before=before_bits,
            information_bits_after=after_bits,
            delta_bits=after_bits - before_bits,
            populated_nodes=populated,
            populated_branch_nodes=populated_branches,
        ),
        nxt,
    )


def information_budget(
    adjacency: Mapping[Node, Sequence[Node]],
    *,
    start_nodes: Sequence[Node],
    steps: int,
) -> tuple[InformationBudgetStep, ...]:
    if steps < 0:
        raise ValueError("steps must be >= 0")
    if not start_nodes:
        raise ValueError("start_nodes must be non-empty")

    nodes = set(adjacency)
    for targets in adjacency.values():
        nodes.update(targets)

    counts = {node: 0 for node in nodes}
    for node in start_nodes:
        counts[node] += 1

    rows = []
    for time in range(steps):
        row, counts = budget_step(
            adjacency,
            counts,
            time=time,
        )
        rows.append(row)

    return tuple(rows)


def cumulative_created_bits(
    rows: Sequence[InformationBudgetStep],
) -> float:
    return sum(row.delta_bits for row in rows)


def endpoint_information_gain(
    rows: Sequence[InformationBudgetStep],
) -> float:
    if not rows:
        return 0.0
    return (
        rows[-1].information_bits_after
        - rows[0].information_bits_before
    )
