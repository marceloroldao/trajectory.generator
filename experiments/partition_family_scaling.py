"""Cross-width generalization gate for partition-preserving universe laws.

A law found at one small width is scientifically interesting only if the SAME
parameter rule survives other widths/horizons without payload-specific retuning.
This script evaluates fixed parameter families across widths and K.

No candidate is declared successful merely because it was found by search at one
width. Results expose first failure depth and normalized depth/W.
"""
from partition_preserving_universe_search import gate

FAMILIES={
    # Fixed public laws, deliberately not selected per payload.
    "A":(1,2,3,1,5),
    "B":(2,1,5,3,7),
    "C":(3,2,9,1,11),
    "D":(1,3,13,2,15),
}

def depth(w,T,K,p):
    ok,d,n=gate(w,T,K,p)
    return ok,d,n

def main():
    for name,p in FAMILIES.items():
        for K in (1,2,3):
            row=[]
            for w in range(3,13):
                T=4*w
                ok,d,n=depth(w,T,K,p)
                row.append((2*w,d,round(d/(2*w),3),ok))
            print("FAMILY_SCALE",name,"K",K,"law",p,"results",row)

if __name__=="__main__":main()
