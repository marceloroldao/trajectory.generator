"""Measure how much trajectory ambiguity remains in the final dynamical state.

The standalone 4-bit codec already provides an exact bijection between
(enumerative address, transition count) and an admissible trajectory.  This
experiment asks the stronger original question:

    Is (P_final, transition count) itself sufficient?

For each transition horizon T, dynamic programming counts how many admissible
trajectories terminate in each final private state P.  At T=218 we report:
- occupied endpoints;
- min/max/mean endpoint multiplicity;
- endpoint entropy H(P_final);
- conditional trajectory entropy H(Path | P_final, T), assuming the uniform
  distribution over admissible trajectories;
- effective residual address bits after revealing only P_final.

No reference graph is used; only the standalone four-bit local laws.
"""
from __future__ import annotations

from collections import defaultdict
import math

from standalone_four_bit_codec import INITIAL, allowed, step, total


def endpoint_counts(transitions:int):
    dist=defaultdict(int)
    for p in INITIAL:
        dist[(p,0)] += 1
    for _ in range(transitions):
        nxt=defaultdict(int)
        for (p,phase),count in dist.items():
            for z in (0,1):
                if allowed(p,z,phase):
                    np=step(p,z,phase)
                    nxt[(np,(phase+1)%3)] += count
        dist=nxt
    by_private=defaultdict(int)
    for (p,_phase),count in dist.items():
        by_private[p]+=count
    return dict(by_private)


def entropy_from_counts(counts):
    n=sum(counts.values())
    if n==0: return 0.0
    return -sum((c/n)*math.log2(c/n) for c in counts.values() if c)


def summarize(T:int):
    counts=endpoint_counts(T)
    n=sum(counts.values())
    assert n==total(T)
    vals=sorted(counts.values())
    h_endpoint=entropy_from_counts(counts)
    h_path=math.log2(n)
    h_cond=h_path-h_endpoint
    return {
      'transitions':T,
      'total_paths':n,
      'occupied_private_endpoints':len(counts),
      'min_multiplicity':vals[0],
      'max_multiplicity':vals[-1],
      'mean_multiplicity':n/len(vals),
      'H_path_bits':h_path,
      'H_final_private_bits':h_endpoint,
      'H_path_given_final_bits':h_cond,
      'fraction_entropy_resolved_by_final':h_endpoint/h_path if h_path else 1.0,
      'endpoint_counts':dict(sorted(counts.items())),
    }


def main():
    for T in (0,1,2,3,8,16,64,218):
        row=summarize(T)
        print({k:v for k,v in row.items() if k!='endpoint_counts'})
        if T in (16,64,218):
            print(' endpoint_counts',row['endpoint_counts'])

    final=summarize(218)
    # The endpoint alone is not injective if any multiplicity >1.
    assert final['max_multiplicity']>1
    assert final['H_path_given_final_bits']>0

if __name__=='__main__':
    main()
