from math import pi, sin, cos, fsum

# # Using nested 'for' loops:
# def idft1(rex, imx):
#     "The Inverse Discrete Fourier Transform"
#     assert len(rex) == fft_size
#     assert len(imx) == fft_size
#     XX = [0.0]*(samples) # holds the time domain signal
#     REX = rex[:]
#     IMX = imx[:]
#     N = len(XX) # N is the number of points in XX
#     assert N == 32
#     
#     # Find the cosine and sin wave amplitudes
#     for k in range(len(REX)):
#         REX[k] = REX[k]/(N/2)
#         IMX[k] = -IMX[k]/(N/2)
#     # Adjust the first and last
#     REX[0] = REX[0]/2
#     REX[-1] = REX[-1]/2
#     
#     # Note that the nesting of these two loops can
#     # be swapped without affecting the result of the
#     # calculation. The two nesting options correspond
#     # to the "input view" and "output view".
#     for n in range(N):
#         for k in range(len(REX)):
#             XX[i] += REX[k]*cos(2*pi*k*i/N) + IMX[k]*sin(2*pi*k*i/N)
#     
#     return XX

# Using a 'for' loop and a list comprehension
def idft2(rex, imx):
    "The Inverse Discrete Fourier Transform"
    assert len(rex) == fft_size
    assert len(imx) == fft_size
    REX = rex[:]
    IMX = imx[:]
    K = len(REX)
    N = (K - 1) * 2 # N is the number of points in XX
    XX = [0.0]*(N) # holds the time domain signal
    
    # Find the cosine and sin wave amplitudes
    for k in range(len(REX)):
        REX[k] = REX[k]/(N/2)
        IMX[k] = -IMX[k]/(N/2)
    # Adjust the first and last
    REX[0] = REX[0]/2
    REX[-1] = REX[-1]/2
    
    for n in range(N):
        XX[n] = fsum([REX[k]*cos(2*pi*k*n/N) +
                     IMX[k]*sin(2*pi*k*n/N) for k in range(len(REX))])
    
    return XX

# Using nested list comprehensions
def idft3(rex, imx):
    "The Inverse Discrete Fourier Transform"
    assert len(rex) == len(imx)
    REX = rex[:]
    IMX = imx[:]
    K = len(REX)
    N = (K - 1) * 2 # N is the number of points in XX
    
    # Find the cosine and sin wave amplitudes
    for k in range(len(REX)):
        REX[k] = REX[k]/(N/2)
        IMX[k] = -IMX[k]/(N/2)
    # Adjust the first and last
    REX[0] = REX[0]/2
    REX[-1] = REX[-1]/2
    
    XX = [fsum([REX[k]*cos(2*pi*k*n/N) +
               IMX[k]*sin(2*pi*k*n/N)
               for k in range(len(REX))])
          for n in range(N)]
    
    return XX

# Using a generator nested within a list comprehension
# - possibly more efficient as fsum() takes an iterable as its
# first argument rather than just a list.
def idft4(rex, imx):
    "The Inverse Discrete Fourier Transform"
    assert len(rex) == len(imx)
    REX = rex[:]
    IMX = imx[:]
    K = len(REX)
    N = (K - 1) * 2 # N is the number of points in XX

# Find the cosine and sin wave amplitudes
    for k in range(len(REX)):
        REX[k] = REX[k]/(N/2)
        IMX[k] = -IMX[k]/(N/2)
    # Adjust the first and last
    REX[0] = REX[0]/2
    REX[-1] = REX[-1]/2
    
    XX = [fsum(REX[k]*cos(2*pi*k*n/N) +
               IMX[k]*sin(2*pi*k*n/N)
               for k in range(len(REX)))
          for n in range(N)]
    
    return XX

# # Using nested 'for' loops:
# def dft1(XX):
#     "The Discrete Fourier Transform"
#     assert len(XX) == samples
#     REX = [0.0]*(fft_size)
#     IMX = [0.0]*(fft_size)
#     N = len(XX) # N is the number of points in XX
#         
#     # Note that the nesting of these two loops can
#     # be swapped without affecting the result of the
#     # calculation. The two nesting options correspond
#     # to the "input view" and "output view".
#     for k in range(len(REX)):
#         for n in range(N):
#             REX[k] += XX[i]*cos(2*pi*k*i/N)
#             IMX[k] -= XX[i]*sin(2*pi*k*i/N)
#     
#     return REX, IMX

# Using a 'for' loop and list comprehensions
def dft2(XX):
    "The Discrete Fourier Transform"
    assert len(XX) == samples
    N = len(XX) # N is the number of points in XX
    K = N//2 + 1
    REX = [0.0]*(K)
    IMX = [0.0]*(K)
        
    for k in range(len(REX)):
        REX[k] =  fsum([XX[n]*cos(2*pi*k*n/N) for n in range(N)])
        IMX[k] = -fsum([XX[n]*sin(2*pi*k*n/N) for n in range(N)])
    
    return REX, IMX

# Using nested list comprehensions
def dft3(XX):
    "The Discrete Fourier Transform"
    assert len(XX) == samples
    N = len(XX) # N is the number of points in XX
    K = N//2 + 1
    REX = [fsum([+XX[n]*cos(2*pi*k*n/N) for n in range(N)])
           for k in range(K)]
    IMX = [fsum([-XX[n]*sin(2*pi*k*n/N) for n in range(N)])
           for k in range(K)]
    
    return REX, IMX

# Using generators nested within list comprehensions
# - possibly more efficient as fsum() takes an iterable as its
# first argument rather than just a list.
def dft4(XX):
    "The Discrete Fourier Transform"
    assert len(XX) == samples
    N = len(XX) # N is the number of points in XX
    K = N//2 + 1
    REX = [fsum(+XX[n]*cos(2*pi*k*n/N) for n in range(N))
           for k in range(K)]
    IMX = [fsum(-XX[n]*sin(2*pi*k*n/N) for n in range(N))
           for k in range(K)]
    
    return REX, IMX

samples = 32
fft_size = (samples >> 1) + 1

rex = [1.0]*fft_size
imx = [0.0]*fft_size

xx2 = idft2(rex, imx)
rex2, imx2 = dft2(xx2)

xx3 = idft3(rex, imx)
assert xx3 == xx2
rex3, imx3 = dft3(xx3)
assert rex3 == rex2
assert imx3 == imx2

xx4 = idft4(rex, imx)
assert xx4 == xx3
rex4, imx4 = dft4(xx4)
assert rex4 == rex3
assert imx4 == imx3

yy = [1.0]*samples
yy[0] = 1.0
rex2, imx2 = dft2(yy)
rex3, imx3 = dft3(yy)
rex4, imx4 = dft4(yy)
assert rex3 == rex2
assert imx3 == imx2
assert rex4 == rex3
assert imx4 == imx3


