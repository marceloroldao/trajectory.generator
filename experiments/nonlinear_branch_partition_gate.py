"""Exact branch-partition gate for sparse local reversibility.

For each t, construct images I0 and I1 of all K-sparse reachable predecessors.
Local reverse branch inference from the endpoint alone is possible iff I0 and I1
are disjoint. This is independent of which classifier formula we happen to try.

When disjoint, report the minimum Boolean description baseline obtained by a
truth-table partition over the small exhaustive universe. The truth table is
NOT an accepted decoder; it only proves that a separating function exists.
"""
from nonlinear_sparse_local_regions import reachable,forward

def gate(w,T,K):
    levels=reachable(T,w,K)
    worst=0
    for t in range(T):
        I=[set(),set()]
        for h,v,k in levels[t]:
            for e in (0,1):
                if k+e<=K:I[e].add(forward((h,v),e,t,w))
        inter=I[0]&I[1]
        worst=max(worst,len(I[0]|I[1]))
        if inter:
            y=next(iter(inter))
            return False,t,y,len(I[0]),len(I[1]),worst
    return True,None,None,None,None,worst

def main():
    for K in (1,2,3):
        for w,T in ((3,6),(4,8),(5,10),(6,12),(7,14),(8,16)):
            ok,t,y,n0,n1,worst=gate(w,T,K)
            print("BRANCH_PARTITION","W",2*w,"T",T,"K",K,
                  "PASS",ok,"first_collision_t",t,"collision_state",y,
                  "I0",n0,"I1",n1,"max_partition_states",worst)

if __name__=="__main__":main()
