import numpy as np
import matplotlib.pyplot as plt

def newton_raphson_fractal(width=800, height=600, max_iter=50):
    # Define the complex function and its derivative
    def f(z): return z**3 - 1
    def df(z): return 3*z**2

    # Create complex plane
    y, x = np.ogrid[-1.5:1.5:height*1j, -2:2:width*1j]
    z = x + y*1j

    # Roots of z^3 - 1 = 0
    roots = np.array([1, -0.5 + 0.866j, -0.5 - 0.866j])

    # Initialize iteration count array
    iterations = np.zeros(z.shape, dtype=int)

    # Newton-Raphson iteration
    for i in range(max_iter):
        z_old = z.copy()
        z = z - f(z)/df(z)
        converged = abs(z - z_old) < 1e-6
        iterations[converged & (iterations == 0)] = i

    # Color based on which root each point converged to
    distances = np.array([abs(z - root) for root in roots])
    closest_root = np.argmin(distances, axis=0)

    # Create colormap
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    cmap = plt.cm.get_cmap('viridis')

    # Plot
    plt.figure(figsize=(12, 9))
    plt.imshow(closest_root, cmap=plt.cm.RdYlBu)
    plt.colorbar(label='Convergence Basin')
    plt.title('Newton-Raphson Fractal for z³ - 1')
    plt.axis('off')
    plt.show()

newton_raphson_fractal()
