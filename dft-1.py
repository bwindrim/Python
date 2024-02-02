from math import pi, sin, cos

# Using nested 'for' loops:
def idft1(REX, IMX):
    "The Inverse Discrete Fourier Transform"
    assert len(REX) == 257
    assert len(IMX) == 257
    XX = [0.0]*(512) # holds the time domain signal
    N = len(XX) # N is the number of points in XX
    
    # Find the cosine and sin wave amplitudes
    for k in range(len(REX)):
        REX[k] = REX[k]/(N/2)
        IMX[k] = -IMX[k]/(N/2)
    # Adjust the first and last
    REX[0] = REX[0]/2
    REX[-1] = REX[-1]/2
    
    # Note that the nesting of these two loops can
    # be swapped without affecting the result of the
    # calculation. The two nesting options correspond
    # to the "input view" and "output view".
    for i in range(N):
        for k in range(len(REX)):
            XX[i] += REX[k]*cos(2*pi*k*i/N)
            XX[i] += IMX[k]*sin(2*pi*k*i/N)
    
    return XX

# Using a 'for' loop and a list comprehension
def idft2(REX, IMX):
    "The Inverse Discrete Fourier Transform"
    assert len(REX) == 257
    assert len(IMX) == 257
    XX = [0.0]*(512) # holds the time domain signal
    N = len(XX) # N is the number of points in XX
    
    # Find the cosine and sin wave amplitudes
    for k in range(len(REX)):
        REX[k] = REX[k]/(N/2)
        IMX[k] = -IMX[k]/(N/2)
    # Adjust the first and last
    REX[0] = REX[0]/2
    REX[-1] = REX[-1]/2
    
    for i in range(N):
        XX[i] = sum([REX[k]*cos(2*pi*k*i/N) +
                     IMX[k]*sin(2*pi*k*i/N) for k in range(len(REX))])
    
    return XX

# Using nested list comprehensions
def idft3(REX, IMX):
    "The Inverse Discrete Fourier Transform"
    assert len(REX) == 257
    assert len(IMX) == 257
    N = 512 # N is the number of points in XX
    
    # Find the cosine and sin wave amplitudes
    for k in range(len(REX)):
        REX[k] = REX[k]/(N/2)
        IMX[k] = -IMX[k]/(N/2)
    # Adjust the first and last
    REX[0] = REX[0]/2
    REX[-1] = REX[-1]/2
    
    XX = [sum([REX[k]*cos(2*pi*k*i/N) +
               IMX[k]*sin(2*pi*k*i/N)
               for k in range(len(REX))])
          for i in range(N)]
    
    return XX

# Using a generator nested within a list comprehension
def idft4(REX, IMX):
    "The Inverse Discrete Fourier Transform"
    assert len(REX) == 257
    assert len(IMX) == 257
    N = 512 # N is the number of points in XX
    
    # Find the cosine and sin wave amplitudes
    for k in range(len(REX)):
        REX[k] = REX[k]/(N/2)
        IMX[k] = -IMX[k]/(N/2)
    # Adjust the first and last
    REX[0] = REX[0]/2
    REX[-1] = REX[-1]/2
    
    XX = [sum(REX[k]*cos(2*pi*k*i/N) +
               IMX[k]*sin(2*pi*k*i/N)
               for k in range(len(REX)))
          for i in range(N)]
    
    return XX

# Using nested 'for' loops:
def dft1(XX):
    "The Discrete Fourier Transform"
    assert len(XX) == 512
    REX = [0.0]*(257)
    IMX = [0.0]*(257)
    N = len(XX) # N is the number of points in XX
        
    # Note that the nesting of these two loops can
    # be swapped without affecting the result of the
    # calculation. The two nesting options correspond
    # to the "input view" and "output view".
    for k in range(len(REX)):
        for i in range(N):
            REX[k] += XX[i]*cos(2*pi*k*i/N)
            IMX[k] -= XX[i]*sin(2*pi*k*i/N)
    
    return REX, IMX

# Using a 'for' loop and list comprehensions
def dft2(XX):
    "The Discrete Fourier Transform"
    assert len(XX) == 512
    REX = [0.0]*(257)
    IMX = [0.0]*(257)
    N = len(XX) # N is the number of points in XX
        
    for k in range(len(REX)):
        REX[k] =  sum([XX[i]*cos(2*pi*k*i/N) for i in range(N)])
        IMX[k] = -sum([XX[i]*sin(2*pi*k*i/N) for i in range(N)])
    
    return REX, IMX

# Using nested list comprehensions
def dft3(XX):
    "The Discrete Fourier Transform"
    assert len(XX) == 512
    N = len(XX) # N is the number of points in XX
    K = 257
    REX = [sum([+XX[i]*cos(2*pi*k*i/N) for i in range(N)])
           for k in range(K)]
    IMX = [sum([-XX[i]*sin(2*pi*k*i/N) for i in range(N)])
           for k in range(K)]
    
    return REX, IMX

# Using generators nested within list comprehensions
def dft4(XX):
    "The Discrete Fourier Transform"
    assert len(XX) == 512
    N = len(XX) # N is the number of points in XX
    K = 257
    REX = [sum(+XX[i]*cos(2*pi*k*i/N) for i in range(N))
           for k in range(K)]
    IMX = [sum(-XX[i]*sin(2*pi*k*i/N) for i in range(N))
           for k in range(K)]
    
    return REX, IMX

rex = [1.0]*257
imx = [0.0]*257

xx1 = idft1(rex, imx)
rex1, imx1 = dft1(xx1)
# assert rex1 == rex
# assert imx1 == imx

xx2 = idft2(rex, imx)
assert xx2 == xx1
rex2, imx2 = dft2(xx2)
# assert rex2 == rex
# assert imx2 == imx

xx3 = idft3(rex, imx)
assert xx3 == xx2
rex3, imx3 = dft3(xx3)
# assert rex3 == rex
# assert imx3 == imx

xx4 = idft4(rex, imx)
assert xx4 == xx3
rex4, imx4 = dft4(xx4)
# assert rex4 == rex
# assert imx4 == imx
