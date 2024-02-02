
def convolve(X, H):
    "Convolve input signal X with impulse response H (or vice-versa)"
    Y = [0.0]*(len(X) + len(H) - 1)
    for i,x in enumerate(X):
        for j,h in enumerate(H):
            Y[i+j] += x*h
    return Y

def correlate(X,T):
    "Correlate input signal X with signal T (or vice-versa)"
    Y = [0.0]*(len(X) + len(T) - 1)
    for i,x in enumerate(X):
        for j,t in enumerate(reversed(T)):
            Y[i+j] += x*t
    return Y

def find_correlation(X,T):
    correlation = correlate(X,T)
    m = max(correlation)
    return correlation.index(m), m

H1 = [1.0,-0.5,-0.25,-0.125]
X1 = [0.0, -1.0, -1.25, 2.0, 1.33, 1.33, 0.66, 0.0, -0.66]
D1 = [1.0]
Y1 = convolve(X1, H1)
print (Y1)
print (len(Y1))
Y2 = convolve(H1, X1)
print (Y2)
print (len(Y2))
assert Y1 == Y2
assert(convolve(D1, H1) == H1)
assert(convolve(D1, X1) == X1)
assert(convolve(H1, D1) == H1)
assert(convolve(X1, D1) == X1)

print(correlate(X1, H1))
print(correlate(X1, X1))
print(correlate(H1, H1))

