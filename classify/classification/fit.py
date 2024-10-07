#!/usr/bin/env python3

"""
This module performs linear fitting and score mapping.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline  # type: ignore
import csv
from typing import TextIO
import sys

from argh import arg
from ally import main

__version__ = "2.0.2"

logger = main.get_logger()

Score = float
Range = tuple[float, float]
Segments = list[tuple[float, float]]


def smooth_fit(
    x: np.ndarray,
    y: np.ndarray,
    dy_dx: np.ndarray | None = None,
    smoothness: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Implements a smooth fitting function that hits all points.
    Optionally considers the derivative at each point.
    """
    if dy_dx is None:
        cs = CubicSpline(x, y, bc_type="natural")
    else:
        cs = CubicSpline(x, y, bc_type=((1, dy_dx[0]), (1, dy_dx[-1])))

    x_smooth = np.linspace(min(x), max(x), 1000)
    y_smooth = cs(x_smooth)

    return x_smooth, y_smooth


def read_tsv(filename: str) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Reads a TSV file containing x, y, and optionally dy/dx values.
    """
    x, y, dy_dx = [], [], []
    with open(filename, "r") as file:
        reader = csv.reader(file, delimiter="\t")
        for row in reader:
            x.append(float(row[0]))
            y.append(float(row[1]))
            if len(row) > 2:
                dy_dx.append(float(row[2]))

    return np.array(x), np.array(y), np.array(dy_dx) if dy_dx else None


def plot_mappings(tsv_file: str):
    """
    Plots the linear mapping and smooth fit
    """
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 8))

    x_tsv, y_tsv, dy_dx_tsv = read_tsv(tsv_file)
    input_range = [min(x_tsv) - 1, max(x_tsv) + 1]
    output_range = [min(y_tsv) - 1, max(y_tsv) + 1]
    x_smooth, y_smooth = smooth_fit(x_tsv, y_tsv, dy_dx_tsv)
    ax.plot(x_smooth, y_smooth, label="Smooth Fit", linewidth=2)
    ax.scatter(x_tsv, y_tsv, color="red", label="Data Points")

    ax.set_xlabel("Input Score", fontsize=12)
    ax.set_ylabel("Output Score", fontsize=12)
    ax.set_title("Score Mapping Comparison", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.set_xlim(input_range)
    ax.set_ylim(output_range)
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))

    plt.tight_layout()
    plt.show()


@arg("tsv-file", help="TSV file containing data points")
def linear_fit(
    tsv_file: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Performs linear fitting and score mapping.
    """
    get, put = main.io(istream, ostream)

    # Plot mappings
    plot_mappings(tsv_file)


if __name__ == "__main__":
    main.run(linear_fit)
