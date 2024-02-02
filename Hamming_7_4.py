# Hamming (7,4) Coding
#
# Reads binary stream from standard input and outputs Hamming (7,4) encoded
# version to standard output.
#
# USAGE: python hamming-code-74-encode.py
#
# EXAMPLE:
#      $ python hamming-code-74-encode.py
#      Enter Input String of bits - 
#      0001
#       Output -  1101001
# AUTHOR: Shivam Bharadwaj <shivamb45@yahoo.in>
# FORK-DATE: 2017-04-19
#
#
# ORIGINAL AUTHOR: Mark Reid <mark.reid@anu.edu.au>
# ORGINAL CREATION DATE: 2013-10-21
K = 4
#works only for 7,4

def encode(s):
    # Read in K=4 bits at a time and write out those plus parity bits
    while len(s) >= K:
        nibble = s[0:K]
        input(hamming(nibble))
        s = s[K:]

def hamming(bits):
    # Return given 4 bits plus parity bits for bits (1,2,3), (2,3,4) and (1,3,4)
    t1 = parity(bits, [0,1,3])
    t2 = parity(bits, [0,2,3])
    t3 = parity(bits, [1,2,3])
    return t1 + t2 + bits[0] + t3 + bits[1:] #again saying, works only for 7,4

def parity(s, indicies):
    # Compute the parity bit for the given string s and indicies
    sub = ""
    for i in indicies:
        sub += s[i]
    return str(str.count(sub, "1") % 2)

if __name__ == "__main__":
#     print("Enter Input String of bits - ") #just for testing
#     input_string = input().strip()
#     print(" Output - ",end=' ') #just for testing
#     encode(input_string)
    for i in range(16):
        nybble = "{0:04b}".format(i)
        print("i =", nybble, "encoded =", hamming(nybble))