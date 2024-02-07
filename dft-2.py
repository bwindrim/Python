from math import pi, sin, cos, fsum


# Using a generator nested within a list comprehension
# - possibly more efficient as fsum() takes an iterable as its
# first argument rather than just a list.
def idft(rex, imx):
    "The Inverse Discrete Fourier Transform"
    assert len(rex) == len(imx)
    REX = rex[:] # copy rex and imx,
    IMX = imx[:] # prior to modification
    K = len(REX)
    N = (K - 1) * 2 # N is the number of points in XX
    assert N & (N - 1) == 0 # N should be a power of 2
    
    # Calculate the cosine and sin wave amplitudes
    for k in range(K):
        REX[k] = REX[k]/(N/2)
        IMX[k] = -IMX[k]/(N/2)
    # Halve the first and last cosine ampltudes
    REX[0] = REX[0]/2
    REX[-1] = REX[-1]/2
    
    # Use math.fsum() to avoid loss of precision
    XX = [fsum(REX[k]*cos(2*pi*k*n/N) +
               IMX[k]*sin(2*pi*k*n/N)
               for k in range(K))
          for n in range(N)]
    
    return XX

# Using generators nested within list comprehensions
# - possibly more efficient as fsum() takes an iterable as its
# first argument rather than just a list.
def dft(XX):
    "The Discrete Fourier Transform"
    N = len(XX) # N is the number of points in XX
    K = N//2 + 1
    assert N & (N - 1) == 0 # N should be a power of 2

    # Use math.fsum() to avoid loss of precision
    REX = [fsum(+XX[n]*cos(2*pi*k*n/N) for n in range(N))
           for k in range(K)]
    IMX = [fsum(-XX[n]*sin(2*pi*k*n/N) for n in range(N))
           for k in range(K)]
    
    return REX, IMX


