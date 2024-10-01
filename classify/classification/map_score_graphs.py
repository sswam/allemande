#!/usr/bin/env python3

"""
This module graphs linear and nonlinear mappings for quality assessment.
"""

import sys
import logging
from typing import TextIO
import numpy as np
import matplotlib.pyplot as plt

from argh import arg

from ally import main
from map_quality_linear import map_score as linear_map_score
from map_quality_nonlinear import map_score as nonlinear_map_score

__version__ = "0.1.2"

logger = main.get_logger()


def create_graph(x: np.ndarray) -> plt.Figure:
    """Create a graph comparing linear and nonlinear mappings."""
    linear_y = np.array([linear_map_score(score) for score in x])
    nonlinear_y = np.array([nonlinear_map_score(score) for score in x])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, linear_y, label="Linear Mapping", linewidth=2)
    ax.plot(x, nonlinear_y, label="Nonlinear Mapping", linewidth=2)
    ax.set_xlabel("Old Score (0-6)", fontsize=12)
    ax.set_ylabel("New Score (0-10)", fontsize=12)
    ax.set_title("Comparison of Linear and Nonlinear Quality Score Mappings", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 10)
    return fig


@arg("--output", help="output file name for PNG (if not specified, show graph)")
@arg("--dpi", help="DPI for the output image", type=int, default=300)
def map_quality_graphs(
    output: str = "",
    dpi: int = 300,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Graph linear and nonlinear mappings for quality assessment.
    """
    get, put = main.io(istream, ostream)

    x = np.linspace(0, 6, 100)
    fig = create_graph(x)

    if output:
        logger.info(f"Saving graph to {output} with {dpi} DPI")
        fig.savefig(output, dpi=dpi, bbox_inches='tight')
        put(f"Graph saved to {output}")
    else:
        logger.info("Displaying graph")
        plt.show()

    plt.close(fig)


if __name__ == "__main__":
    main.run(map_quality_graphs)
