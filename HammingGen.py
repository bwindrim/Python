import numpy as np

def glom(list, bits=4):
    "Combine a list of (increasing) bit fields into a word"
    result = 0;
    list.reverse()
    for i in list:
        result <<= bits
        result |= i
    return result

def printVar(list, n, bits, varName="array"):
    print("static const uint16_t")
    print(varName, "[] = {")
    assert 0 == (len(list) % 4)
    for i in range(0, len(list), n):
        r = glom(list[i:i+n], bits=bits)
        assert(r >= 0)
        assert(r <= 0xFFFF)
        print(f"\t{r:#0{6}x},")
    print("};")
    
def bits(n, b=4):
    return np.array([n >> i & 1 for i in range(b)])

def unbits(l):
    result = 0
    for i,b in enumerate(l):
        result |= b << i
    return result
    
# generator matrix
G = np.array([
    [1,1,0,1],
    [1,0,1,1],
    [1,0,0,0],
    [0,1,1,1],
    [0,1,0,0],
    [0,0,1,0],
    [0,0,0,1]
    ])
# parity check matrix
H = np.array([
    [1,0,1,0,1,0,1],
    [0,1,1,0,0,1,1],
    [0,0,0,1,1,1,1]
    ])

def matMulModulo2(x, y):
    "Matrix multiply, modulo-2, of NumPy arrays"
    z = np.matmul(x,y)  # multiply the matrices
    f = lambda x: x % 2 # and use a lambda funtion to
    return f(z)         # convert to modulo-2

def hamming7_4_encode(n):
    p = bits(n, 4)          # expand to a bit array, size 4
    y = matMulModulo2(G,p) # multiply with the generator matrix
    return unbits(y)        # and convert back to an integer

def hamming7_4_decode(n):
    d = bits(n, 7)         # expand to a bit array, size 7
    x = matMulModulo2(H,d) # multiply with the parity matrix
    p = unbits(x)          # and convert back to an integer
    if 0 != p:             # if there is a bit error...
        d[p - 1] = 1 - d[p - 1]  # ...then invert the corrupted bit
    e = [d[2], d[4], d[5], d[6]] # make a list of the data bits
    return unbits(e)       # and convert it back to an integer

encode = [ hamming7_4_encode(n) for n in range(16)]
decode = [ hamming7_4_decode(n) for n in range(128)]
print("encode =", encode)
print("decode =", decode)

# Test the encode and decode tables
for n in range(16):
    h = encode[n]                 # encode the 4-bit data word via the table
    assert decode[h] == n         # check the decode
    for c in range(7):
        m = (h ^ (1 << c)) & 0x7F # corrupt each codeword bit in turn
        assert m != h             # the corrupted codeword should differ from the the original
        y = decode[m]             # decode the corrupted codeword
        assert encode[y] != m     # the re-encoded codeword should differ from the corrupted codeword
        assert y == n             # the decoded data word should match the original

# If all is well then dump the C lookup arrays
printVar(encode, 2, 8, varName="hamming7_4_encode")
printVar(decode, 4, 4, varName="hamming7_4_decode")
      