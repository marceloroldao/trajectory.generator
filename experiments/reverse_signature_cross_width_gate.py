"""Cross-width gate for compact reverse relation signatures.

Find a signature on the smallest training width, then freeze its observable
indices. Test that exact same signature on larger widths/horizons. No retuning
is allowed after training. This rejects small-universe coincidences.
"""
from reverse_relation_signature_search import dataset,search,signature_separates

LAWS=[(1,2,3,1,5),(2,1,5,3,7),(3,2,9,1,11)]

def main():
    for p in LAWS:
        sig,n=search(3,6,2,p,max_bits=5)
        print("SIGNATURE_TRAIN","law",p,"W",6,"T",6,"signature",sig,"records",n)
        if sig is None:continue
        for w in range(4,11):
            T=2*w
            rec=dataset(w,T,2,p)
            ok=signature_separates(rec,sig)
            print("SIGNATURE_TRANSFER","law",p,"trained_W",6,
                  "test_W",2*w,"T",T,"signature",sig,
                  "records",len(rec),"PASS",ok)
            if not ok:break

if __name__=="__main__":main()
