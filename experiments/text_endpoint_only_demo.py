"""End-to-end text demo for the original objective, within the true 63-bit capacity.

A text payload is converted to raw UTF-8 bits with NO admissibility restriction.
The bits enter the W=63 temporal universe one by one through the same fixed local
input direction.  After encoding, the only payload-dependent retained value is
X_final plus T.  The original bits/text are reconstructed by the local reverse
decoder.

This is not compression.  Exact arbitrary recovery requires T <= 63 here.
"""
from local_reverse_endpoint_decoder import encode, decode_local
from fixed_injection_temporal_universe import SEEDS

W=63
SEED=SEEDS[63]


def bytes_to_bits(data:bytes):
    out=[]
    for byte in data:
        for s in range(7,-1,-1):out.append((byte>>s)&1)
    return tuple(out)

def bits_to_bytes(bits):
    if len(bits)%8:raise ValueError('demo requires byte-aligned text payload')
    out=bytearray()
    for i in range(0,len(bits),8):
        v=0
        for b in bits[i:i+8]:v=(v<<1)|b
        out.append(v)
    return bytes(out)


def encode_text(text:str):
    data=text.encode('utf-8');bits=bytes_to_bits(data)
    if len(bits)>W:raise ValueError(f'payload has {len(bits)} bits; W={W}')
    endpoint=encode(bits,W,SEED,1)
    return endpoint,len(bits)

def decode_text(endpoint:int,T:int):
    bits=decode_local(endpoint,T,W,SEED,1)
    return bits_to_bytes(bits).decode('utf-8')


def main():
    samples=['A','ABC','trajeto','Roldao!']  # <= 7 ASCII bytes = 56 bits
    for text in samples:
        endpoint,T=encode_text(text)
        recovered=decode_text(endpoint,T)
        assert recovered==text,(text,endpoint,T,recovered)
        print('TEXT_ENDPOINT_ONLY_OK',repr(text),'X_final',endpoint,'T',T,'recovered',repr(recovered))

if __name__=='__main__':main()
