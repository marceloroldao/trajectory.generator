"""Horizon-free online address from actual branching events only.

State law is imported from standalone_four_bit_codec. We do NOT know the
future horizon while evolving. Whenever the current private state has two
admissible labels, append one branch bit to R. Deterministic transitions do
not change R.

This experiment measures the min/max number of real branch events reachable
at each physical transition count. If max_branch_events <= 63 at T=218, this
simple horizon-free address can fit in 63 bits without modular overflow.
"""
from __future__ import annotations

from collections import defaultdict

from standalone_four_bit_codec import initial_private, allowed, step, total

LIMIT_BITS = 63


def branch_options(p, phase):
    return tuple(z for z in (0,1) if allowed(p,z,phase))


def branch_count_range(transitions:int):
    # map (private_state, phase) -> (min_branch_events, max_branch_events)
    cur = {}
    for s in range(8):
        key = (initial_private(s), 0)
        if key in cur:
            lo, hi = cur[key]
            cur[key] = (min(lo,0), max(hi,0))
        else:
            cur[key] = (0,0)

    for _ in range(transitions):
        nxt = {}
        for (p,phase),(lo,hi) in cur.items():
            opts = branch_options(p,phase)
            inc = 1 if len(opts)==2 else 0
            for z in opts:
                np = step(p,z,phase)
                key = (np,(phase+1)%3)
                nlo,nhi = lo+inc,hi+inc
                if key not in nxt:
                    nxt[key]=(nlo,nhi)
                else:
                    a,b=nxt[key]
                    nxt[key]=(min(a,nlo),max(b,nhi))
        cur=nxt
    return min(lo for lo,_ in cur.values()), max(hi for _,hi in cur.values()), len(cur)


def main():
    print('T total_paths min_branch max_branch reachable_phase_states')
    for T in (0,1,16,32,64,128,180,200,218,219):
        lo,hi,n=branch_count_range(T)
        print(T,total(T),lo,hi,n)
    lo,hi,_=branch_count_range(218)
    print('frontier218_max_branch_bits',hi)
    print('fits_raw_branch_address_63',hi<=LIMIT_BITS)

if __name__=='__main__':
    main()
