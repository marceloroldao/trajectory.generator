"""Standalone exact trajectory codec using only the minimal time-driven law.

No reference graph, policy universe, 37-state list or 49-edge table is imported.
Private causal state:
    P=(h2,q0,q1,q2)  # four bits
Public clock:
    phase=t mod 3
Edge alphabet:
    z in {0,1}

The local Boolean laws below are the best exact laws synthesized in
four_bit_time_driven_law.py.  This module demonstrates that path counting,
rank/unrank and the 63-bit 218/219 frontier can be reproduced from the compact
law alone.
"""
from __future__ import annotations

from functools import lru_cache
import random

LIMIT=1<<63


def initial_topology(state:int)->int:
    oldest=(state>>2)&1
    middle=(state>>1)&1
    newest=state&1
    r1=oldest^middle
    r2=middle^newest
    return (oldest<<2)|(r1<<1)|r2


def initial_private(state:int):
    q=initial_topology(state)
    return ((state>>2)&1,(q>>0)&1,(q>>1)&1,(q>>2)&1)


def allowed(p,z,phase):
    r0,r1,r2,r3=p
    if phase==0:
        return (1^r0^r3^z^(r0&r2)^(r0&z)^(r2&r3)^(r2&z)^(r3&z)^
                (r0&r2&z)^(r1&r2&z)^(r1&r3&z)^(r0&r1&r3&z)^
                (r1&r2&r3&z)^(r0&r1&r2&r3&z))&1
    if phase==1:
        return (r1^r3^(r1&r3)^(r3&z)^(r1&r2&z)^(r1&r3&z)^
                (r1&r2&r3&z))&1
    return (r2^(r0&r1)^(r1&r3)^(r1&z)^(r2&z)^(r0&r1&r2)^
            (r0&r1&r3)^(r0&r2&r3)^(r1&r2&r3)^(r1&r2&r3&z))&1


def step(p,z,phase):
    r0,r1,r2,r3=p
    n0=r0^r2
    n2=r1
    n3=r2
    if phase==0:
        n1=1^r0^r3^z^(r1&r2)
    elif phase==1:
        n1=r1^r3^z^(r0&r1)^(r1&r2)^(r0&r1&r2)
    else:
        n1=r0^r3^z
    return (n0&1,n1&1,n2&1,n3&1)


INITIAL=tuple(initial_private(s) for s in range(8))


@lru_cache(maxsize=None)
def suffix(p,phase,remaining):
    if remaining==0:
        return 1
    total=0
    for z in (0,1):
        if allowed(p,z,phase):
            total+=suffix(step(p,z,phase),(phase+1)%3,remaining-1)
    return total


def total(steps:int)->int:
    if steps<0: raise ValueError('steps must be >=0')
    # The original first three data bits select one of eight public initial
    # states.  Thereafter `steps-3` labeled transitions evolve P.
    if steps<=3:
        return 1<<steps
    rem=steps-3
    return sum(suffix(initial_private(s),0,rem) for s in range(8))


def unrank(rank:int,steps:int):
    n=total(steps)
    if not 0<=rank<n: raise ValueError('rank outside family')
    if steps<=3:
        return [((rank>>(steps-1-i))&1) for i in range(steps)]

    rem=steps-3
    initial=None
    for s in range(8):
        p=initial_private(s)
        c=suffix(p,0,rem)
        if rank<c:
            initial=s; break
        rank-=c
    assert initial is not None

    prefix=[(initial>>2)&1,(initial>>1)&1,initial&1]
    labels=[]
    p=initial_private(initial); phase=0
    for k in range(rem):
        left=rem-k-1
        for z in (0,1):
            if not allowed(p,z,phase): continue
            np=step(p,z,phase)
            c=suffix(np,(phase+1)%3,left)
            if rank<c:
                labels.append(z); p=np; phase=(phase+1)%3; break
            rank-=c
        else:
            raise AssertionError('unrank lost path')
    return prefix+labels


def rank(path):
    steps=len(path)
    if steps<=3:
        v=0
        for b in path: v=(v<<1)|int(b)
        return v
    initial=(path[0]<<2)|(path[1]<<1)|path[2]
    rem=steps-3
    r=0
    for s in range(initial):
        r+=suffix(initial_private(s),0,rem)
    p=initial_private(initial); phase=0
    for k,z_actual in enumerate(path[3:]):
        left=rem-k-1
        for z in (0,1):
            if not allowed(p,z,phase): continue
            np=step(p,z,phase)
            if z==z_actual:
                p=np; phase=(phase+1)%3; break
            r+=suffix(np,(phase+1)%3,left)
        else:
            raise ValueError('path is not admissible')
    return r


def final_private(path):
    if len(path)<=3:
        return None
    initial=(path[0]<<2)|(path[1]<<1)|path[2]
    p=initial_private(initial); phase=0
    for z in path[3:]:
        if not allowed(p,z,phase): raise ValueError('inadmissible')
        p=step(p,z,phase); phase=(phase+1)%3
    return p,phase


def main():
    print('initial_private_states',len(set(INITIAL)),INITIAL)
    print('count218',total(218))
    print('count219',total(219))
    print('fits218',total(218)<=LIMIT,'fits219',total(219)<=LIMIT)
    assert total(218)==9131204053820206208
    assert total(219)==10214739716735776832
    assert total(218)<=LIMIT<total(219)

    rng=random.Random(20260908)
    for steps in (1,3,4,16,64,218):
        n=total(steps)
        samples=min(100,n)
        for _ in range(samples):
            r=rng.randrange(n)
            path=unrank(r,steps)
            rr=rank(path)
            assert rr==r,(steps,r,rr)
        print('roundtrip',steps,samples,'ok')

    # Demonstrate the intended address+length contract at the current frontier.
    address=0x123456789ABCDEF & (LIMIT-1)
    address%=total(218)
    path=unrank(address,218)
    print('demo_address',address)
    print('demo_steps',218)
    print('demo_path_bits',len(path))
    print('demo_final_private',final_private(path))
    print('demo_rank_back',rank(path))
    assert rank(path)==address

if __name__=='__main__':
    main()
