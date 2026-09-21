"""No-go theorem for nontrivial natural automorphisms of the history extension.

Let H_t(v) be the set of admissible length-t histories ending at causal node v.
For each public edge e:u->v, append defines an injective map:

    J_e : H_t(u) -> H_(t+1)(v)
    J_e(h) = h · e.

A vertical transformation alpha is a natural automorphism over the fixed causal
base when, for every public edge,

    alpha_(t+1,v) o J_e = J_e o alpha_(t,u).

If every initial fiber H_0(v) contains at most one history, alpha_0 is forced to
be identity.  Every later history has a unique final edge e and unique prefix h.
Inductively:

    alpha_(t+1)(h · e)
      = J_e(alpha_t(h))
      = J_e(h)
      = h · e.

Therefore the identity is the only natural automorphism of the complete
edge-labelled history extension that fixes the causal base and singleton
initial fibers.

This theorem distinguishes:
- intrinsic history dynamics: append/remove public edges;
- chart/gauge dynamics: time-dependent fiber relabelings, which need not commute
  with append in one fixed chart but are related by gauge conjugacy.

A nontrivial physical vertical degree of freedom therefore requires additional
state/structure not already exhausted by the bare history extension, or a
relaxation of the naturality/base-fixing assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .minimal_reversible_completion import (
    History,
    MinimalReversibleCompletion,
)


Node = Hashable


@dataclass(frozen=True)
class NaturalityNoGoCertificate:
    horizon: int
    singleton_initial_fibers: bool
    histories_checked: int
    forced_fixed_histories: int
    identity_forced: bool


def singleton_initial_fibers(
    completion: MinimalReversibleCompletion,
) -> bool:
    return all(
        completion.fiber_size(node, 0) <= 1
        for node in completion.nodes
    )


def forced_natural_image(
    completion: MinimalReversibleCompletion,
    history: History,
) -> History:
    """Return the image forced by base-fixing edge naturality.

    With singleton initial fibers this recursively strips the unique final edge,
    applies the forced image to the prefix, and appends the same edge.  The
    result must be the original history.
    """
    time = len(history.edges)

    if time == 0:
        rows = completion.histories(
            history.endpoint,
            0,
        )
        if len(rows) > 1:
            raise ValueError(
                "initial fiber is not singleton; image is not forced"
            )
        if history not in rows:
            raise ValueError("history is not an admissible initial history")
        return history

    edge = completion.edge_by_label.get(
        history.edges[-1]
    )
    if edge is None or edge.target != history.endpoint:
        raise ValueError("history has invalid final edge")

    prefix = History(
        start=history.start,
        edges=history.edges[:-1],
        endpoint=edge.source,
    )
    image_prefix = forced_natural_image(
        completion,
        prefix,
    )

    return History(
        start=image_prefix.start,
        edges=image_prefix.edges + (edge.label,),
        endpoint=edge.target,
    )


def certificate(
    completion: MinimalReversibleCompletion,
    horizon: int,
) -> NaturalityNoGoCertificate:
    if horizon < 0:
        raise ValueError("horizon must be >= 0")

    singleton = singleton_initial_fibers(
        completion
    )
    if not singleton:
        return NaturalityNoGoCertificate(
            horizon=horizon,
            singleton_initial_fibers=False,
            histories_checked=0,
            forced_fixed_histories=0,
            identity_forced=False,
        )

    checked = 0
    fixed = 0

    for time in range(horizon + 1):
        completion.ensure_horizon(time)
        for node in completion.nodes:
            for history in completion.histories(
                node,
                time,
            ):
                checked += 1
                if (
                    forced_natural_image(
                        completion,
                        history,
                    )
                    == history
                ):
                    fixed += 1

    return NaturalityNoGoCertificate(
        horizon=horizon,
        singleton_initial_fibers=True,
        histories_checked=checked,
        forced_fixed_histories=fixed,
        identity_forced=(checked == fixed),
    )
