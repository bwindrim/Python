# Function to calculate hamming distance 
def hammingDistance(n1, n2) :

    x = n1 ^ n2 
    setBits = 0

    while (x > 0) :
        setBits += x & 1
        x >>= 1
    
    return setBits 

def hammingDistances(marker, len = 24):
    mask = (0xFFFFFFFF >> (32 - len))
    src = (marker & mask) | (marker << len)
    list = []
    
    for i in range(1, len):
        rot = (src >> i) & mask
        list.append(hammingDistance(marker, rot))
        
    return list

def search():
    best = 0
    for i in range(0xFFFFFF):
        m = min(hammingDistances(i)) 
        if m > best:
            best = m;
            best_i = i
            print("i =", format(i, '#026b'), i, hex(i), "m =", m)
    
    return best_i

# print("Min Hamming distance:", min(distances))
# print("Max Hamming distance:", max(distances))

search()


