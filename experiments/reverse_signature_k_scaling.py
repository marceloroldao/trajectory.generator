"""Innovation-budget scaling for a frozen reverse signature.

Train once at (W=6,T=6,K=1 or 2), freeze the signature, then test increasing K
and width. A structural relation should not require a new hand-picked signature
for each innovation count.
"""
from reverse_relation_signature_search import dataset,search,signature_separates

LAW=(1,2,3,1,5)

def main():
    for trainK in (1,2):
        sig,n=search(3,6,trainK,LAW,max_bits=5)
        print("K_SCALE_TRAIN","K",trainK,"signature",sig,"records",n)
        if sig is None:continue
        for K in (1,2,3,4):
            for w in (4,5,6,7,8):
                T=2*w
                rec=dataset(w,T,K,LAW)
                ok=signature_separates(rec,sig)
                print("K_SCALE_TEST","trainK",trainK,"K",K,
                      "W",2*w,"T",T,"PASS",ok,"records",len(rec))
                if not ok:break

if __name__=="__main__":main()
