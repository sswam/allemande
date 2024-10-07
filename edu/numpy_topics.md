Here are 100 illuminating flashcard topics about NumPy for programmers:

# 1. Front: What is **NumPy**?
Back: A fundamental Python library for scientific computing, providing support for large, multi-dimensional arrays and matrices, along with a collection of mathematical functions to operate on these arrays.

# 2. Front: What does **NumPy** stand for?
Back: Numerical Python

# 3. Front: Primary data structure in NumPy
Back: **ndarray** (n-dimensional array)

# 4. Front: What is an **ndarray**?
Back: A multidimensional, homogeneous array of fixed-size items, primarily used for numerical computations in NumPy.

# 5. Front: How to import NumPy?
Back: import numpy as np

# 6. Front: Create a 1D array in NumPy
Back: np.array([1, 2, 3, 4, 5])

# 7. Front: Create a 2D array in NumPy
Back: np.array([[1, 2, 3], [4, 5, 6]])

# 8. Front: Create an array of zeros
Back: np.zeros((3, 4))

# 9. Front: Create an array of ones
Back: np.ones((2, 3))

# 10. Front: Create an identity matrix
Back: np.eye(3)

# 11. Front: Generate an array with a range of values
Back: np.arange(0, 10, 2)

# 12. Front: Generate an array with evenly spaced numbers
Back: np.linspace(0, 1, 5)

# 13. Front: What is **broadcasting** in NumPy?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 14. Front: How to reshape an array?
Back: array.reshape(new_shape) or np.reshape(array, new_shape)

# 15. Front: What is the **shape** of an array?
Back: A tuple indicating the size of each dimension of the array.

# 16. Front: How to get the shape of an array?
Back: array.shape

# 17. Front: What is the **dtype** of an array?
Back: The data type of the elements in the array.

# 18. Front: How to get the data type of an array?
Back: array.dtype

# 19. Front: How to change the data type of an array?
Back: array.astype(new_dtype)

# 20. Front: What is **array slicing**?
Back: Extracting a portion of an array using index ranges.

# 21. Front: How to slice a 1D array?
Back: array[start:stop:step]

# 22. Front: How to slice a 2D array?
Back: array[row_start:row_stop, col_start:col_stop]

# 23. Front: What is **boolean indexing**?
Back: Selecting array elements based on a boolean condition.

# 24. Front: How to perform element-wise addition?
Back: np.add(array1, array2) or array1 + array2

# 25. Front: How to perform element-wise multiplication?
Back: np.multiply(array1, array2) or array1 * array2

# 26. Front: How to calculate the dot product?
Back: np.dot(array1, array2) or array1.dot(array2)

# 27. Front: How to transpose a matrix?
Back: array.T or np.transpose(array)

# 28. Front: What is **axis** in NumPy operations?
Back: The dimension along which the operation is performed.

# 29. Front: How to calculate the sum of all elements?
Back: np.sum(array)

# 30. Front: How to calculate the mean of an array?
Back: np.mean(array)

# 31. Front: How to find the maximum value in an array?
Back: np.max(array)

# 32. Front: How to find the minimum value in an array?
Back: np.min(array)

# 33. Front: How to calculate the standard deviation?
Back: np.std(array)

# 34. Front: How to calculate the variance?
Back: np.var(array)

# 35. Front: What is **vectorization**?
Back: The process of converting a loop-based operation to a vector operation for improved performance.

# 36. Front: How to generate random numbers?
Back: np.random.rand(), np.random.randn(), np.random.randint()

# 37. Front: What is **broadcasting** in NumPy?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 38. Front: How to stack arrays vertically?
Back: np.vstack((array1, array2))

# 39. Front: How to stack arrays horizontally?
Back: np.hstack((array1, array2))

# 40. Front: What is **array concatenation**?
Back: Joining two or more arrays along a specified axis.

# 41. Front: How to concatenate arrays?
Back: np.concatenate((array1, array2), axis=0)

# 42. Front: What is **array splitting**?
Back: Dividing an array into multiple sub-arrays.

# 43. Front: How to split an array?
Back: np.split(array, indices_or_sections)

# 44. Front: What is **broadcasting** in NumPy?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 45. Front: How to find unique elements in an array?
Back: np.unique(array)

# 46. Front: How to sort an array?
Back: np.sort(array)

# 47. Front: What is **argmax**?
Back: A function that returns the indices of the maximum values along a specified axis.

# 48. Front: What is **argmin**?
Back: A function that returns the indices of the minimum values along a specified axis.

# 49. Front: How to find the indices of non-zero elements?
Back: np.nonzero(array)

# 50. Front: What is **array flattening**?
Back: Converting a multi-dimensional array into a 1D array.

# 51. Front: How to flatten an array?
Back: array.flatten() or array.ravel()

# 52. Front: What is **array iteration**?
Back: Looping over array elements using np.nditer()

# 53. Front: How to perform element-wise comparison?
Back: np.equal(array1, array2) or array1 == array2

# 54. Front: What is **broadcasting** in NumPy?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 55. Front: How to calculate the inverse of a matrix?
Back: np.linalg.inv(array)

# 56. Front: How to calculate the determinant of a matrix?
Back: np.linalg.det(array)

# 57. Front: What is **eigendecomposition**?
Back: Factorizing a matrix into its eigenvalues and eigenvectors.

# 58. Front: How to perform eigendecomposition?
Back: np.linalg.eig(array)

# 59. Front: What is **singular value decomposition (SVD)**?
Back: Factorizing a matrix into three matrices: U, Σ, and V^T.

# 60. Front: How to perform SVD?
Back: np.linalg.svd(array)

# 61. Front: What is **broadcasting** in NumPy?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 62. Front: How to solve a system of linear equations?
Back: np.linalg.solve(A, b)

# 63. Front: What is **array masking**?
Back: Creating a boolean array to select specific elements from another array.

# 64. Front: How to create a mask?
Back: mask = array > value

# 65. Front: What is **fancy indexing**?
Back: Using integer arrays to index another array.

# 66. Front: How to perform fancy indexing?
Back: array[[0, 2, 4]]

# 67. Front: What is **broadcasting** in NumPy?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 68. Front: How to calculate the cross product?
Back: np.cross(array1, array2)

# 69. Front: How to calculate the inner product?
Back: np.inner(array1, array2)

# 70. Front: What is **array broadcasting**?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 71. Front: How to save an array to a file?
Back: np.save('filename.npy', array)

# 72. Front: How to load an array from a file?
Back: np.load('filename.npy')

# 73. Front: What is **structured array**?
Back: An array with compound data types for each element.

# 74. Front: How to create a structured array?
Back: np.array([(1, 'John'), (2, 'Jane')], dtype=[('id', int), ('name', 'U10')])

# 75. Front: What is **broadcasting** in NumPy?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 76. Front: How to perform element-wise exponentiation?
Back: np.power(array, exponent) or array ** exponent

# 77. Front: How to calculate the logarithm of array elements?
Back: np.log(array)

# 78. Front: How to calculate the sine of array elements?
Back: np.sin(array)

# 79. Front: How to calculate the cosine of array elements?
Back: np.cos(array)

# 80. Front: What is **array broadcasting**?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 81. Front: How to find the indices that would sort an array?
Back: np.argsort(array)

# 82. Front: How to perform a set operation on arrays?
Back: np.union1d(), np.intersect1d(), np.setdiff1d()

# 83. Front: What is **array broadcasting**?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 84. Front: How to calculate the cumulative sum?
Back: np.cumsum(array)

# 85. Front: How to calculate the cumulative product?
Back: np.cumprod(array)

# 86. Front: What is **array broadcasting**?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 87. Front: How to perform polynomial operations?
Back: np.polyfit(), np.polyval()

# 88. Front: How to perform Fast Fourier Transform (FFT)?
Back: np.fft.fft()

# 89. Front: What is **array broadcasting**?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 90. Front: How to calculate the gradient of an array?
Back: np.gradient(array)

# 91. Front: How to perform convolution?
Back: np.convolve()

# 92. Front: What is **array broadcasting**?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 93. Front: How to perform element-wise rounding?
Back: np.round(array)

# 94. Front: How to perform element-wise floor division?
Back: np.floor_divide(array1, array2) or array1 // array2

# 95. Front: What is **array broadcasting**?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 96. Front: How to calculate the absolute value?
Back: np.abs(array)

# 97. Front: How to clip array values?
Back: np.clip(array, min_value, max_value)

# 98. Front: What is **array broadcasting**?
Back: The ability to perform operations on arrays of different shapes and sizes.

# 99. Front: How to perform element-wise comparison with tolerance?
Back: np.isclose(array1, array2)

# 100. Front: How to calculate the histogram of an array?
Back: np.histogram(array)

