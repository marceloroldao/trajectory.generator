"""Compare 63-bit information bound with natural syndrome construction.

For K innovations among T positions, exact identification requires at least
log2(sum_{j=0..K} C(T,j)) bits.  Separately test whether the natural propagated
63-bit directions have unique XOR syndromes for K<=2.
"""
from math import comb,log2
from itertools import combinations
from natural_sparse_innovation_syndrome import propagated_columns,W

def bound(T,K):
    n=sum(comb(T,j) for j in range(K+1))
    return log2(n), n <= (1<<W)

def unique_k2(T):
    cols=propagated_columns(T); seen={0}
    for c in cols:
        if c in seen:return False
        seen.add(c)
    for i,j in combinations(range(T),2):
        y=cols[i]^cols[j]
        if y in seen:return False
        seen.add(y)
    return True

def main():
    for T in (128,256,512,1024,2048,4096):
        vals=[]
        for K in range(1,9):
            bits,fit=bound(T,K)
            vals.append((K,round(bits,3),fit))
        natural=unique_k2(T) if T<=2048 else None
        print("FRONTIER","T",T,"bounds",vals,"natural_K2_unique",natural)

if __name__=="__main__":main()
