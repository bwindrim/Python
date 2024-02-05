import numpy as np

# def padList(list, pad, n):
#     "Pad 'list' with 'pad', to multiple of 'n'"
#     l = len(list)
#     list += [pad] * ((n - (l %n)) % n)
#     return list

def glom(list, bits=4):
    "Combine 4-bit numbers into word"
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
#     list = padList(list, pad=0, n=n)
    for i in range(0, len(list), n):
        r = glom(list[i:i+n], bits=bits)
        assert(r >= 0)
        assert(r <= 0xFFFF)
        print(f"\t{r:#0{6}x},")
    print("};")
    
# # Function to get parity of number n. 
# # It returns 1 if n has odd parity, 
# # and returns 0 if n has even parity
# def getParity( n ):
#     parity = 0
#     while n:
#         parity = ~parity
#         n = n & (n - 1)
#     return parity
 
def bits(n, b=4):
    return np.array([n >> i & 1 for i in range(b)])

def unbits(l):
    result = 0
    for i,b in enumerate(l):
        result |= b << i
    return result
    
# generator matrix
P = np.array([
    [0, 1, 0, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 1, 1, 0],
    [0, 1, 0, 1, 0, 0, 1, 1],
    [1, 0, 1, 0, 1, 0, 0, 1],
    [1, 1, 0, 1, 0, 1, 0, 0],
    [0, 1, 1, 0, 1, 0, 1, 0],
    [0, 0, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 1, 1, 0, 1, 0]
    ])
# parity check matrix
H = np.array([
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1],
    [0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1],
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1],
    [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1],
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0]
    ])

def quasiCyclic16_8_encode(n):
    m = bits(n, 8)
#     p = np.array(b)
    p = np.matmul(m,P)
    f = lambda x: x % 2
    y = f(p) # modulo-2
    return unbits(y)

def hamming7_4_parity(n):
    r = bits(n, 7)
#     p = np.array(b)
#     print("r =", r)
    x = np.matmul(H,r)
#     print("x =", x)
    f = lambda x: x % 2
    y = f(x) # modulo-2
#     print("y =", y)
    l = list(y)
    l.reverse()
    p = unbits(l)
#     assert(0 == p)
    return p

def hamming7_4_decode(n):
    d = bits(n,7)
    p = hamming7_4_parity(n)
    if 0 != p:
        print("Error in bit", p - 1)
        d[p - 1] = 1 - d[p - 1]
        
    return unbits(d)

for n in range(256):
    h = quasiCyclic16_8_encode(n)
    print("data =", n, "codeword =", hex(h))
#     y = hamming7_4_decode(h)
#     print("y =", y) # , " decoded =", hex(unbits(y)))
#     
# encode = [ hamming7_4_encode(n) for n in range(16)]
# print("encode =", encode)
# printVar(encode, 2, 8, varName="hamming7_4_encode")
# decode = [ hamming7_4_decode(n) for n in range(128)]
# print("decode =", decode)
# printVar(decode, 4, 4, varName="hamming7_4_decode")

      