"""Exact cardinality frontier for sparse innovations in a 63-bit endpoint."""
from math import comb, log2
W=63
def frontier(T):
    s=0; best=-1
    for k in range(T+1):
        n=s+comb(T,k)
        if n>(1<<W): break
        s=n;best=k
    return best,s
def main():
    for T in [63,64,128,256,512,1024,2048,4096,8192,16384,65536]:
        k,n=frontier(T)
        print(T,k,f"{log2(n):.6f}",f"{k/T:.8f}")
if __name__=="__main__":main()
