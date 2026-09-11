from __future__ import annotations

import json
import random
import statistics
import time
import tracemalloc

from trajectory_generator import reference_v01 as ref


def timed(fn, repeat=5):
    values=[]
    out=None
    for _ in range(repeat):
        t0=time.perf_counter_ns()
        out=fn()
        values.append(time.perf_counter_ns()-t0)
    return out, {
        "repeat":repeat,
        "min_ns":min(values),
        "median_ns":int(statistics.median(values)),
        "max_ns":max(values),
    }


def memory_peak(fn):
    tracemalloc.start()
    fn()
    _,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def main():
    rng=random.Random(20260911)
    report={"python_reference":True,"results":{}}

    for T in (16,64,128,218,219):
        _,lat=timed(lambda T=T: ref.count(T),repeat=7)
        report["results"][f"count_{T}"]={"latency":lat,"value":ref.count(T)}

    for T in (16,64,128,218):
        n=ref.count(T)
        a=rng.randrange(n)
        path=ref.unrank(a,T)

        _,unrank_lat=timed(lambda a=a,T=T: ref.unrank(a,T),repeat=5)
        _,rank_lat=timed(lambda path=path: ref.rank(path),repeat=5)
        ks=[0,T//4,T//2,(3*T)//4,T-1]
        _,access_lat=timed(lambda a=a,T=T,ks=ks:[ref.access(a,T,k) for k in ks],repeat=5)

        # append with one admissible symbol found from the decoded path state
        p=ref.initial_private((path[0]<<2)|(path[1]<<1)|path[2])
        for t,z in enumerate(path[3:]):
            p=ref.step(p,z,t%3)
        z=next(z for z in (0,1) if ref.allowed(p,z,T%3))
        _,append_lat=timed(lambda a=a,T=T,z=z: ref.append(a,T,z),repeat=5)

        report["results"][f"slice_{T}"]={
            "address":a,
            "rank":rank_lat,
            "unrank":unrank_lat,
            "access_5":access_lat,
            "append":append_lat,
            "unrank_peak_bytes":memory_peak(lambda a=a,T=T: ref.unrank(a,T)),
            "rank_peak_bytes":memory_peak(lambda path=path: ref.rank(path)),
        }

    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
