"""Direct table-free decoders for full-capacity periodic Feistel endpoints.

For the W=6 and W=8 candidates in time_periodic_feistel_endpoint.py, both input
branches share the same linear map at each phase and differ only by constants.
Therefore the final endpoint is an affine GF(2) transform of the W input bits:

    y = c XOR M b

If M is invertible, the original arbitrary W-bit word is recovered from the
natural endpoint alone (plus public T=W) by

    b = M^{-1}(y XOR c)

No reachable-state table, rank, history, or restricted input language is used.
"""
from __future__ import annotations
from itertools import product


def rotl(x,r,w):
    m=(1<<w)-1; r%=w
    return ((x<<r)|(x>>(w-r)))&m if r else x&m


def forward(state,b,t,w,params):
    h,v=state; r,k=params[t%3][b]
    return v,(h ^ rotl(v,r,w) ^ k)&((1<<w)-1)


def endpoint_int(bits,w,params):
    h=v=0
    for t,b in enumerate(bits):
        h,v=forward((h,v),b,t,w,params)
    return h | (v<<w)


def parity(x):return x.bit_count()&1

CASES={
    3:{
        'params':[[(2,2),(2,3)],[(0,1),(0,3)],[(2,6),(2,7)]],
        'const':45,
        'inverse_rows':[37,49,53,5,22,42],
    },
    4:{
        'params':[[(3,1),(3,2)],[(1,15),(1,14)],[(0,12),(0,11)]],
        'const':20,
        'inverse_rows':[103,46,170,231,169,165,137,119],
    },
}


def decode_endpoint(y,w):
    case=CASES[w]; W=2*w
    z=y^case['const']
    return tuple(parity(z&mask) for mask in case['inverse_rows'][:W])


def main():
    for w,case in CASES.items():
        W=2*w
        seen=set()
        for bits in product((0,1),repeat=W):
            y=endpoint_int(bits,w,case['params'])
            assert y not in seen
            seen.add(y)
            got=decode_endpoint(y,w)
            assert got==bits,(w,bits,y,got)
        assert len(seen)==1<<W
        print('DIRECT_ENDPOINT_ONLY_DECODE_OK','W',W,'states',len(seen),
              'const',case['const'],'inverse_rows',case['inverse_rows'])

if __name__=='__main__':main()
