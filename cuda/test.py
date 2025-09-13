# example from Claude

import torch
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.cpp_extension import load
import time

# Compile and load the CUDA extension
mandel_cuda = load(
    name="mandel_cuda",
    sources=["mandel_kernel.cu"],
    verbose=True
)

def plot_mandelbrot(width=800, height=600, max_iter=1000):
    # Create coordinate grid
    x = np.linspace(-2, 1, width)
    y = np.linspace(-1.5, 1.5, height)
    X, Y = np.meshgrid(x, y)

    # Prepare inputs for CUDA
    x_coords = torch.tensor(X.flatten(), dtype=torch.float64, device='cuda')
    y_coords = torch.tensor(Y.flatten(), dtype=torch.float64, device='cuda')

    # Run CUDA kernel
    t0 = time.time()
    result = mandel_cuda.mandelbrot_cuda(x_coords, y_coords, max_iter)
    t1 = time.time()
    duration = t1 - t0
    print(f"Computation completed in {duration:.4f} seconds")

    # Reshape and plot
    mandel = result.cpu().numpy().reshape(height, width)

    plt.figure(figsize=(10, 8))
    plt.imshow(mandel, cmap='hot', extent=[-2, 1, -1.5, 1.5])
    plt.colorbar(label='Iteration count')
    plt.title('Mandelbrot Set')
    plt.show()

if __name__ == "__main__":
    plot_mandelbrot()
