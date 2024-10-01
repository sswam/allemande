#!/usr/bin/env python3

"""
This module provides a function to map quality scores from one scale to another
using a non-linear sigmoid function.
"""

import math
from scipy.optimize import minimize

from ally import main

__version__ = "1.1.5"

logger = main.get_logger()


def sigmoid(x: float, L: float, k: float, x0: float) -> float:
    """
    Generalized sigmoid function.

    Parameters:
        x (float): Input value
        L (float): Maximum value of the curve
        k (float): Steepness of the curve
        x0 (float): x-value of the sigmoid's midpoint

    Returns:
        float: Output of the sigmoid function
    """
    return L / (1 + math.exp(-k * (x - x0)))


def calculate_parameters(p1: tuple[float, float], p2: tuple[float, float]) -> tuple[float, float, float]:
    """
    Calculate optimal parameters for the mapping function to hit two specific points.

    Parameters:
        p1 (tuple): (old_score1, new_score1)
        p2 (tuple): (old_score2, new_score2)

    Returns:
        tuple: (a, b, c) parameters for the map_score function
    """
    x1, y1 = p1
    x2, y2 = p2

    def objective(params):
        a, b, c = params
        return (map_score(x1, a, b, c) - y1)**2 + (map_score(x2, a, b, c) - y2)**2

    result = minimize(objective, [0.8, 3.0, 10.0], method='Nelder-Mead')
    return tuple(result.x)


def map_score(old_score: float|None, a: float = 0.8, b: float = 3.0, c: float = 10.0) -> float:
    """
    Maps an old score from 0.0–6.0 to a new score from 0.0–10.0 using an S-curve.

    Parameters:
        old_score (float or None): The old score between 0.0 and 6.0.
            Use 6.0 for blank content, and None for corrupt or empty files.
        a (float): Parameter controlling the curve's shape
        b (float): Parameter controlling the curve's midpoint
        c (float): Parameter controlling the curve's maximum value

    Returns:
        float: The new score between 0.0 and 10.0.
    """
    if old_score is None:
        logger.info("Empty file detected, assigning maximum score")
        return 10.0

    old_score = max(0.0, min(old_score, 6.0))
    sigmoid_min = sigmoid(0, 1, a, b)
    sigmoid_max = sigmoid(6, 1, a, b)
    numerator = sigmoid(old_score, 1, a, b) - sigmoid_min
    denominator = sigmoid_max - sigmoid_min

    if denominator == 0:
        # Apply L'Hôpital's rule
        return c * (a * old_score * math.exp(a * (old_score - b))) / (a * 6 * math.exp(a * (6 - b)))
    else:
        return c * numerator / denominator


if __name__ == "__main__":
    main.run(map_score)
