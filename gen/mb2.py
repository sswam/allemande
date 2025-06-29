import numpy as np
import matplotlib.pyplot as plt

def mandelbrot(h, w, max_iter):
    y, x = np.ogrid[-1.4:1.4:h*1j, -2:0.8:w*1j]
    c = x + y*1j
    z = c
    divtime = max_iter + np.zeros(z.shape, dtype=int)

    for i in range(max_iter):
        z = z**2 + c
        diverge = z*np.conj(z) > 2**2
        div_now = diverge & (divtime == max_iter)
        divtime[div_now] = i
        z[diverge] = 2

    return divtime

plt.figure(figsize=(10, 10))
plt.imshow(mandelbrot(500, 500, 50), cmap='hot', extent=[-2, 0.8, -1.4, 1.4])
plt.title("Mandelbrot Set")
plt.colorbar(label='Iteration count')
plt.show()
