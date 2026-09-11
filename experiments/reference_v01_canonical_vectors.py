from hashlib import sha256
from trajectory_generator.reference_v01 import count, unrank, rank, access

CASES = [
    (0, 0),
    (1, 0),
    (1, 7),
    (8, 0),
    (8, 31),
    (16, 12345),
    (64, 0x123456789ABCDEF),
    (128, 0x123456789ABCDEF),
    (218, 0),
    (218, 0x123456789ABCDEF),
    (218, 9131204053820206207),
]

for T, raw in CASES:
    n=count(T); a=raw % n
    p=unrank(a,T)
    assert rank(p)==a
    payload=''.join(map(str,p)).encode('ascii')
    digest=sha256(payload).hexdigest()
    probes=[]
    if T:
        for k in sorted(set((0,T//3,T//2,(2*T)//3,T-1))):
            probes.append((k,access(a,T,k)))
    print(T,a,len(p),digest,probes)
