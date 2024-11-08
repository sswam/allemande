#!/usr/bin/env python3-allemande

# Demonstrate Python basics and new features  

# Add type hints
from typing import List, Dict, Set


# Add logging for debugging:

import logging

logger = logging.getLogger(__name__)
logger.info("Program started")

# Use f-string for string interpolation  
name = "John"  
print(f"Hello, {name}!")  

# Use a list comprehension  
squares: List[int] = [x*x for x in range(10)]  
print(squares)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# Use a dictionary comprehension 
square_dict: Dict[int, int] = {x: x*x for x in range(10)}
print(square_dict)  # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25, 6: 36, 7: 49, 8: 64, 9: 81}  

# Use a set comprehension
square_set: Set[int] = {x*x for x in range(10)}
print(square_set)  # {0, 1, 4, 9, 16, 25, 36, 49, 64, 81}

# Define a function with a default argument
def add(a=10):
    return a + a
print(add()) # 20
print(add(5)) # 10 

# Use functools for partial application 
from functools import partial
add_five = partial(add, 5)
print(add_five()) # 10

# Use a namedtuple  
from collections import namedtuple  
Point = namedtuple("Point", "x y")  
p = Point(x=10, y=20)
print(p) # Point(x=10, y=20)

# Use a Counter from the Collections module  
from collections import Counter  
c = Counter([1,1,1,2,2,3])  
print(c) # Counter({1: 3, 2: 2, 3: 1})

# Use numpy for fast array processing 
import numpy as np 
a = np.array([1, 2, 3]) 
b = np.array([4, 5, 6])
c = a + b  
print(c) # [5 7 9] 

# Use a context manager to time a block of code 
import time

# Timer context manager 
class Timer:
    """A context manager for timing a block of code."""
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()

    def duration(self):
        return self.end - self.start

    def __repr__(self):
        return f"{self.duration()} seconds"

with Timer() as t:    
    time.sleep(1)
print(f"Sleep time: {t}") # Sleep time: 1.0 seconds
