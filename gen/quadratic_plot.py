import numpy as np
import matplotlib.pyplot as plt

def quadratic(x, a, b, c):
        return a*x**2 + b*x + c

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 6))

# Generate x values
x = np.linspace(-4, 4, 200)

# Example quadratic: x² - 2x - 3
a, b, c = 1, -2, -3

# Calculate vertex (B = -b/2a)
B = -b/(2*a)
# Calculate C
C = (-b**2 + 4*a*c)/(4*a**2)

# Plot the parabola
y = quadratic(x, a, b, c)
ax.plot(x, y, 'b-', label='f(x) = x² - 2x - 3')

# Plot the axis of symmetry
ax.axvline(x=B, color='r', linestyle='--', label='Axis of symmetry (x = B)')

# Plot the solutions
solutions = [B - np.sqrt(-C), B + np.sqrt(-C)]
ax.plot(solutions, [0, 0], 'go', label='Solutions')

# Plot the distance √C
y_vertex = quadratic(B, a, b, c)
ax.plot([B, solutions[1]], [0, 0], 'g--', label='√C')

# Formatting
ax.grid(True, alpha=0.3)
ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.legend()
ax.set_title('Geometric Interpretation of Quadratic Formula')

plt.tight_layout()
plt.show()
