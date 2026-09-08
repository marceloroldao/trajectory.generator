"""Minimize the generative coordinate when phase is a public time input.

The previous raw search counted p0,p1 as part of the state.  But phase is not
private memory: phase = t mod 3 and the decoder already knows the step index.
This experiment therefore searches subsets of the six private bits

    h0 h1 h2 q0 q1 q2

while supplying phase as an external/public input to the local transition law.
A candidate private projection P is sufficient when (P, phase) uniquely
determines the labeled projected future and preserves all path counts/frontier.
"""
from __future__ import annotations

from collections import defaultdict, deque
from itertools import combinations

from minimal_generative_coordinate import bits, reference
from nonlinear_ablation import path_counts, frontier

PRIVATE=('h0','h1','h2','q0','q1','q2')


def project_private(node,coord):
    b=bits(node)
    return tuple(b[n] for n in coord)


def phase(node):
    return int(node[2])


def analyze_coord(nodes,edges,initials,coord,ref_counts):
    # Key includes public phase, but phase is not counted in private state bits.
    signatures=defaultdict(set)
    for s in nodes:
        k=(project_private(s,coord),phase(s))
        sig=tuple(sorted((z,(project_private(d,coord),phase(d))) for z,d in edges.get(s,())))
        signatures[k].add(sig)
    if any(len(v)>1 for v in signatures.values()):
        return None
    pedges={k:list(next(iter(v))) for k,v in signatures.items()}
    pinit=tuple((project_private(s,coord),phase(s)) for s in initials)
    seen=set(pinit); q=deque(pinit)
    while q:
        s=q.popleft()
        for _,d in pedges.get(s,()):
            if d not in seen:
                seen.add(d); q.append(d)
    if seen!=set(pedges):
        return None
    counts=path_counts(pedges,pinit)
    same=all(counts[i]==ref_counts[i] for i in range(min(len(counts),len(ref_counts))))
    if not same:
        return None
    rev=defaultdict(set)
    for s,outs in pedges.items():
        for z,d in outs: rev[(d,z)].add(s)
    return {
      'private_coordinate':coord,
      'private_bits':len(coord),
      'phase_public':True,
      'states_with_phase':len(pedges),
      'edges':sum(len(v) for v in pedges.values()),
      'reverse_ambiguous':sum(len(v)>1 for v in rev.values()),
      'frontier':frontier(counts),
      'same_counts':same,
    }


def main():
    nodes,edges,initials=reference()
    ref_counts=path_counts(edges,initials)
    winners=[]
    for k in range(0,len(PRIVATE)+1):
        level=[]
        for coord in combinations(PRIVATE,k):
            row=analyze_coord(nodes,edges,initials,coord,ref_counts)
            if row: level.append(row)
        print('private_bits',k,'sufficient',len(level))
        if level:
            winners=level; break
    print('minimum_private_bits',winners[0]['private_bits'] if winners else None)
    print('solutions',len(winners))
    for r in winners: print(r)

if __name__=='__main__':
    main()
