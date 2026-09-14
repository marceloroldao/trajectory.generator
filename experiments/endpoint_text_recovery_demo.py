"""End-to-end original-objective demo with real text.

Arbitrary UTF-8 bytes (up to 63 bits in this demo) are fed bit-by-bit into the
systematic endpoint-only dynamics from general_endpoint_controllability.py.
After encoding, the source bits and intermediate states are discarded. Decode
uses only (x_final, T), W=63, and the fixed public laws.

This is NOT compression: T input bits require at least T endpoint bits for exact
arbitrary recovery. The purpose is to demonstrate the exact original contract
with a natural dynamic endpoint rather than an external rank/address.
"""
from __future__ import annotations

from general_endpoint_controllability import (
    Model, build_model, mat_vec, rank_vectors,
)


def bytes_to_bits(data:bytes):
    return [(byte>>shift)&1 for byte in data for shift in range(7,-1,-1)]


def bits_to_bytes(bits):
    if len(bits)%8: raise ValueError('bit length must be multiple of 8 for byte decode')
    out=bytearray()
    for i in range(0,len(bits),8):
        v=0
        for b in bits[i:i+8]: v=(v<<1)|b
        out.append(v)
    return bytes(out)


def encode_prefix(bits, model:Model):
    T=len(bits)
    if T>model.W: raise ValueError('T cannot exceed endpoint width W')
    x=0
    for b,(A,dv,c) in zip(bits,model.laws[:T]):
        x=mat_vec(A,x,model.W) ^ (dv if b else 0) ^ c
    return x


def endpoint_basis_for_T(model:Model,T:int):
    if not 0<=T<=model.W: raise ValueError
    zero=encode_prefix([0]*T,model)
    cols=[]
    for j in range(T):
        bits=[0]*T; bits[j]=1
        cols.append(encode_prefix(bits,model)^zero)
    assert rank_vectors(cols,model.W)==T
    return zero,tuple(cols)


def solve_columns(cols,y,W):
    """Solve xor_j cols[j]*b_j = y; cols are independent."""
    # pivot -> (state-vector, coefficient-vector)
    basis={}
    for j,v0 in enumerate(cols):
        v=v0; coeff=1<<j
        while v:
            p=v.bit_length()-1
            if p in basis:
                bv,bc=basis[p]; v^=bv; coeff^=bc
            else:
                basis[p]=(v,coeff); break
        if not v: raise ValueError('dependent columns')
    v=y; coeff=0
    while v:
        p=v.bit_length()-1
        if p not in basis: raise ValueError('endpoint outside reachable image for T')
        bv,bc=basis[p]; v^=bv; coeff^=bc
    return [(coeff>>j)&1 for j in range(len(cols))]


def decode_prefix(x_final:int,T:int,model:Model):
    zero,cols=endpoint_basis_for_T(model,T)
    return solve_columns(cols,x_final^zero,model.W)


def roundtrip_text(text:str,model:Model):
    raw=text.encode('utf-8')
    bits=bytes_to_bits(raw); T=len(bits)
    if T>model.W:
        raise ValueError(f'{len(raw)} UTF-8 bytes = {T} bits exceeds W={model.W}')
    x=encode_prefix(bits,model)
    # Conceptual erase point: only x, T, W and public law remain.
    recovered_bits=decode_prefix(x,T,model)
    recovered=bits_to_bytes(recovered_bits).decode('utf-8')
    assert recovered==text
    return T,x,recovered


def main():
    model=build_model(63)
    tests=['A','ABC','ABCDefg','Roldao!']
    for text in tests:
        T,x,rec=roundtrip_text(text,model)
        print('text',repr(text),'T',T,'x_final',x,'endpoint_bits',x.bit_length(),'recovered',repr(rec))
    print('PASS: real UTF-8 text recovered from natural 63-bit endpoint + T only')
    print('LIMIT: arbitrary input requires T<=63; this is reversible dynamics, not compression')

if __name__=='__main__': main()
