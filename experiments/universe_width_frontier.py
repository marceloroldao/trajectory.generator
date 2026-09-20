"""Information frontier for larger endpoint universes."""
from math import comb,log2
def max_k(T,W):
    s=0;best=-1
    for k in range(T+1):
        n=s+comb(T,k)
        if n>(1<<W):break
        s=n;best=k
    return best,log2(s) if s else 0
def main():
    for W in (63,128,256,512):
        for T in (256,1024,4096,16384,65536,1_000_000):
            k,b=max_k(T,W)
            print("WIDTH_FRONTIER","W",W,"T",T,"Kmax",k,
                  "used_bits",round(b,3),"innovation_density",k/T)
if __name__=="__main__":main()
