import numpy as np; from PIL import Image
w, h, zoom = 800, 800, 1; cx, cy = -0.7, 0.27015; maxIter = 255
img = Image.new("RGB", (w, h)); pix = img.load()
for x in range(w):
    for y in range(h):
        zx, zy = zoom*(x-w/2)/(w/2), zoom*(y-h/2)/(h/2)
        zx, zy = zx + cx, zy + cy
        c = zx + zy*1j; z = 0
        for i in range(maxIter):
            if z.real*z.real + z.imag*z.imag >= 4:
                pix[x, y] = (i<<21) + (i<<10) + i*8; break
            z = z*z + c
img.show()
