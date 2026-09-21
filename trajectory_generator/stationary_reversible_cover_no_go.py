"""No-go theorem for finite stationary reversible covers of positive-entropy graphs.

Suppose a public causal multigraph has a time-independent vertical fiber of
finite cardinality m_v > 0 above each causal node v.

Assume every public causal edge e:u->v is admissible from every vertical state
above u and exact reverse recovery must distinguish all predecessor edge/state
pairs.

Then the target fiber above v must contain disjoint images of every incoming
source fiber:

    m_v >= sum_{e:u->v} m_u.

In vector notation, with adjacency matrix A counting edge multiplicity:

    m >= A^T m.

For an irreducible recurrent component with Perron growth factor lambda > 1,
let l > 0 be a left Perron vector of A^T (equivalently a positive right Perron
vector of A). Multiplying the inequality by the positive Perron functional gives

    <l,m> >= lambda <l,m>,

impossible for finite positive m when lambda > 1.

Therefore a positive-entropy recurrent causal graph cannot have a finite,
time-homogeneous, full-domain reversible cover with fixed positive fiber sizes.

At least one assumption must change:
- fiber capacity grows with time / more bits become available;
- some causal choices are forbidden for some vertical states;
- histories are merged/lost;
- external information is supplied;
- the admissible language has zero asymptotic entropy.

This is the structural version of the information-capacity bound.
"""

from __future__ import annotations

from collections import deque
from typing import Hashable, Mapping, Sequence


Node = Hashable


def incoming_required_sizes(
    adjacency: Mapping[Node, Sequence[Node]],
    fiber_sizes: Mapping[Node, int],
) -> dict[Node, int]:
    nodes = set(adjacency)
    for targets in adjacency.values():
        nodes.update(targets)

    required = {node: 0 for node in nodes}

    for source in nodes:
        size = fiber_sizes.get(source)
        if size is None or size < 1:
            raise ValueError(
                "every node must have positive fiber size"
            )

        for target in adjacency.get(source, ()):
            required[target] += size

    return required


def stationary_cover_inequality_holds(
    adjacency: Mapping[Node, Sequence[Node]],
    fiber_sizes: Mapping[Node, int],
) -> bool:
    required = incoming_required_sizes(
        adjacency,
        fiber_sizes,
    )
    return all(
        fiber_sizes[node] >= required[node]
        for node in required
    )


def exact_stationary_partition_holds(
    adjacency: Mapping[Node, Sequence[Node]],
    fiber_sizes: Mapping[Node, int],
) -> bool:
    required = incoming_required_sizes(
        adjacency,
        fiber_sizes,
    )
    return all(
        fiber_sizes[node] == required[node]
        for node in required
    )


def path_counts(
    adjacency: Mapping[Node, Sequence[Node]],
    *,
    start_nodes: Sequence[Node],
    steps: int,
) -> dict[Node, int]:
    if steps < 0:
        raise ValueError("steps must be >= 0")

    nodes = set(adjacency)
    for targets in adjacency.values():
        nodes.update(targets)

    counts = {node: 0 for node in nodes}
    for start in start_nodes:
        counts[start] += 1

    for _ in range(steps):
        nxt = {node: 0 for node in nodes}
        for source, count in counts.items():
            if not count:
                continue
            for target in adjacency.get(source, ()):
                nxt[target] += count
        counts = nxt

    return counts


def maximum_fiber_demand(
    adjacency: Mapping[Node, Sequence[Node]],
    *,
    start_nodes: Sequence[Node],
    steps: int,
) -> int:
    counts = path_counts(
        adjacency,
        start_nodes=start_nodes,
        steps=steps,
    )
    return max(counts.values(), default=0)


def total_path_count(
    adjacency: Mapping[Node, Sequence[Node]],
    *,
    start_nodes: Sequence[Node],
    steps: int,
) -> int:
    return sum(
        path_counts(
            adjacency,
            start_nodes=start_nodes,
            steps=steps,
        ).values()
    )
