"""Structural complexity audit for the joint dyadic address.

Counts public combinatorial structure, independent of Python wall-clock time:
- blocks decoded from A_t = popcount(t) (0 -> special initial state)
- carries on append = number of trailing 1 bits of t
- blocks in A_{t+1} = popcount(t+1)
- random access descends at most floor(log2 largest dyadic block))+1

This validates O(log t) structural work for append/random access. It does not
claim unit-cost arithmetic: ranks/counts are big integers whose bit complexity
must be accounted separately.
"""
from __future__ import annotations
import math, random
from joint_dyadic_address import block_lengths, total_count, unrank_forest, append_joint, joint_bit_at
from standalone_four_bit_codec import initial_private, allowed


def trailing_ones(n:int)->int:
    c=0
    while n&1:c+=1;n>>=1
    return c


def structural_append_cost(t:int):
    return {
        'decode_blocks': len(block_lengths(t)),
        'carries': trailing_ones(t),
        'encode_blocks': len(block_lengths(t+1)),
        'upper_bound': 2*max(1,t.bit_length())+max(1,t.bit_length()),
    }


def main():
    print('t popcount_before carries popcount_after bit_length')
    worst=(0,None)
    for t in range(0,219):
        c=structural_append_cost(t)
        actual=c['decode_blocks']+c['carries']+c['encode_blocks']
        if actual>worst[0]:worst=(actual,t)
        if t in (0,1,2,3,7,15,31,63,127,200,217,218):
            print(t,c['decode_blocks'],c['carries'],c['encode_blocks'],max(1,t.bit_length()))
    print('worst_structural_units_0_218',worst)
    assert worst[0] <= 3*218 .bit_length()

    # Validate append correctness while reporting structural counts on random ranks.
    rng=random.Random(20260910)
    for t in (16,64,128,200,217):
        n=total_count(t)
        for _ in range(50):
            r=rng.randrange(n);s,f=unrank_forest(r,t)
            p=initial_private(s) if t==0 else f[-1].end
            os=[z for z in (0,1) if allowed(p,z,t%3)]
            z=rng.choice(os);r2=append_joint(r,t,z)
            assert 0<=r2<total_count(t+1)
        c=structural_append_cost(t)
        print('append_audit',t,c,'ok')

    # Random access structural depth at frontier.
    T=218;n=total_count(T);maxdepth=0
    for _ in range(200):
        r=rng.randrange(n)
        for _ in range(8):
            k=rng.randrange(T);_,d=joint_bit_at(r,T,k);maxdepth=max(maxdepth,d)
    print('frontier_random_access_max_tree_depth',maxdepth)
    print('frontier_block_count',len(block_lengths(T)))
    print('frontier_address_bits',math.ceil(math.log2(total_count(T))))
    print('interpretation: joint address is already O(log t) in structural block operations; remaining optimization is big-integer/count evaluation constants')

if __name__=='__main__':main()
