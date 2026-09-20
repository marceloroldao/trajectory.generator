"""Decode K<=2 sparse innovations from a natural endpoint, no trajectory rank.

Uses time-generated endpoint signatures from natural_sparse_innovation_dynamics.
The decoder builds the public signature relation from (T, universe seed). It does
not store input history. For K<=2, endpoint residual is 0, s_i, or s_i XOR s_j.

Important accounting: constructing a reverse dictionary is an algorithmic lookup
optimization, not payload side information, because it is derived solely from
public laws and T. We also provide a scan decoder requiring no retained table.
"""
from natural_sparse_innovation_dynamics import signatures

def endpoint_residual(pos,T,seed):
    s=signatures(T,seed)
    x=0
    for i in pos:x^=s[i]
    return x

def decode_scan(x,T,seed):
    s=signatures(T,seed)
    if x==0:return ()
    for i,a in enumerate(s):
        if x==a:return (i,)
    lookup={a:i for i,a in enumerate(s)}
    for i,a in enumerate(s):
        j=lookup.get(x^a)
        if j is not None and j>i:return (i,j)
    raise ValueError("not a <=2 innovation endpoint")

def main():
    cases=[(256,1),(512,1),(1024,1)]
    for T,seed in cases:
        # verify all zero/single and all pairs: exact exhaustive K<=2 gate
        assert decode_scan(0,T,seed)==()
        s=signatures(T,seed)
        for i in range(T):assert decode_scan(s[i],T,seed)==(i,)
        for i in range(T):
            for j in range(i+1,T):
                x=s[i]^s[j]
                got=decode_scan(x,T,seed)
                assert got==(i,j),(T,i,j,got)
        print("NATURAL_DECODE_EXHAUSTIVE_OK","T",T,"Kmax",2,
              "rank_used",False,"payload_history_stored",False)
if __name__=="__main__":main()
