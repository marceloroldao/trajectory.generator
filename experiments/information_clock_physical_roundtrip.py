"""Exact physical round-trip for the information-clock macro codec.

This experiment derives the recurrent macrograph from the public causal dynamics,
assigns the canonical A/B labels used by ``information_clock_codec``, expands
macro-events back to microscopic phase-lifted causal nodes, and proves the
following round-trip for admissible recurrent-core paths:

    physical trajectory -> macro labels -> rank
    discard trajectory
    (rank, public physical length, public start branch) -> macro labels
    -> identical physical trajectory

No microscopic path table is stored in the address.  The microscopic flights are
re-derived from the public recurrent graph each run.
"""

from __future__ import annotations

from dataclasses import dataclass

from information_clock_macrograph import dominant_component, macro_edges
from trajectory_generator.information_clock_codec import rank_path, unrank_path


@dataclass(frozen=True)
class PhysicalMacroEdge:
    source_name: str
    target_name: str
    physical_length: int
    label: str
    path: tuple[tuple[int, int, int], ...]


def canonical_physical_macrograph() -> tuple[dict[str, tuple[int, int, int]], tuple[PhysicalMacroEdge, ...]]:
    edges, comp = dominant_component()
    branches, macros = macro_edges(edges, comp)

    # The abstract codec intentionally exposes only A/B.  Derive a stable public
    # mapping from the concrete branch states rather than storing it per address.
    ordered = tuple(sorted(branches))
    if len(ordered) != 2:
        raise RuntimeError("canonical candidate no longer has exactly two branch states")
    names = {ordered[0]: "A", ordered[1]: "B"}
    branch_states = {name: node for node, name in names.items()}

    out: list[PhysicalMacroEdge] = []
    for source, target, length, path in macros:
        source_name = names[source]
        target_name = names[target]
        label = f"{source_name}{target_name}{length}"
        out.append(
            PhysicalMacroEdge(
                source_name=source_name,
                target_name=target_name,
                physical_length=length,
                label=label,
                path=path,
            )
        )

    out.sort(key=lambda edge: (edge.source_name, edge.label))
    expected = {"AB1", "AA12", "BA2", "BA5"}
    labels = {edge.label for edge in out}
    if labels != expected:
        raise RuntimeError(f"derived physical macrograph disagrees with canonical codec: {labels!r}")
    return branch_states, tuple(out)


def expand_labels(labels: tuple[str, ...], *, start_state: str) -> tuple[tuple[int, int, int], ...]:
    """Regenerate every microscopic causal node from public dynamics."""
    _, edges = canonical_physical_macrograph()
    by_source = {}
    for edge in edges:
        by_source.setdefault(edge.source_name, {})[edge.label] = edge

    current = start_state
    physical: list[tuple[int, int, int]] = []
    for index, label in enumerate(labels):
        edge = by_source.get(current, {}).get(label)
        if edge is None:
            raise ValueError(f"invalid macro label {label!r} from {current!r}")
        if index == 0:
            physical.extend(edge.path)
        else:
            # Consecutive macro paths share their branch endpoint/startpoint.
            if physical[-1] != edge.path[0]:
                raise RuntimeError("non-contiguous microscopic macro expansion")
            physical.extend(edge.path[1:])
        current = edge.target_name
    return tuple(physical)


def physical_length(path: tuple[tuple[int, int, int], ...]) -> int:
    return max(0, len(path) - 1)


def roundtrip(labels: tuple[str, ...], *, start_state: str) -> tuple[tuple[int, int, int], ...]:
    original = expand_labels(labels, start_state=start_state)
    length = physical_length(original)
    address = rank_path(labels, start_state=start_state, total_length=length)

    # At this point the original labels and physical nodes are conceptually
    # discarded.  Recovery receives only public length, public start state and rank.
    recovered_labels = unrank_path(address, start_state=start_state, total_length=length)
    recovered = expand_labels(recovered_labels, start_state=start_state)
    if recovered != original:
        raise AssertionError("microscopic physical trajectory failed exact regeneration")
    return recovered


def main() -> None:
    branch_states, edges = canonical_physical_macrograph()
    print("branch_states", branch_states)
    for edge in edges:
        print(edge.label, "length", edge.physical_length, "path", edge.path)

    samples = (
        ("A", ("AB1", "BA2")),
        ("A", ("AA12",)),
        ("A", ("AB1", "BA5", "AA12")),
        ("B", ("BA2", "AB1", "BA5")),
    )
    for start, labels in samples:
        path = roundtrip(labels, start_state=start)
        rank = rank_path(labels, start_state=start, total_length=physical_length(path))
        print("roundtrip", start, labels, "rank", rank, "physical_length", physical_length(path), "nodes", len(path))


if __name__ == "__main__":
    main()
