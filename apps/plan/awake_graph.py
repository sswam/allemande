#!/usr/bin/env python3

"""
This module generates a graph of computer activity based on an 'awake' log file.
It plots activity levels over time, with options for smoothing and date range.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import TextIO
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import numpy as np
from argh import arg

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def load_data(log_file: TextIO, days: int) -> tuple[list[datetime], list[float]]:
    """Load and process data from the log file."""
    cutoff_date = datetime.now() - timedelta(days=days)
    timestamps = []
    activity_levels = []

    for line in log_file:
        timestamp_str, status = line.strip().split(" - ")
        timestamp = datetime.fromisoformat(timestamp_str)
        if timestamp < cutoff_date:
            continue

        timestamps.append(timestamp)
        if status == "active":
            activity_levels.append(1.0)
        elif status == "inactive":
            activity_levels.append(0.5)
        else:  # away
            activity_levels.append(0.0)

    return timestamps, activity_levels


def exponential_smoothing(data: list[float], alpha: float) -> list[float]:
    """Apply exponential smoothing to the data."""
    smoothed = [data[0]]
    for i in range(1, len(data)):
        smoothed.append(alpha * data[i] + (1 - alpha) * smoothed[i-1])
    return smoothed


@arg("--log_file", help="Path to the awake log file")
@arg("--days", help="Number of days to plot")
@arg("--smooth", help="Smoothing factor (0-1)")
@arg("--save", help="Save the graph as a PNG file")
def awake_graph(
    log_file: str = str(Path(os.environ["HOME"])/".awake.log"),
    days: int = 7,
    smooth: float = 0,
    save: str = "awake.png",
) -> None:
    """
    Generate a graph of computer activity based on an 'awake' log file.
    """
    logger.info(f"Processing log file: {log_file}")
    logger.info(f"Plotting data for the last {days} days")

    with open(log_file, 'r') as file:
        timestamps, activity_levels = load_data(file, days)

    if smooth > 0:
        logger.info(f"Applying smoothing with factor: {smooth}")
        activity_levels = exponential_smoothing(activity_levels, smooth)

    plt.figure(figsize=(12, 6))
    plt.style.use('dark_background')

    # Plot the line
    plt.plot(timestamps, activity_levels, color='white')

    # Fill the area under the graph
    plt.fill_between(timestamps, activity_levels, color='darkgrey', alpha=0.5)

    plt.ylim(-0.1, 1.1)
    plt.yticks([0, 0.5, 1], ['Away', 'Inactive', 'Active'])
    plt.xlabel('Date')
    plt.ylabel('Activity Level')
    plt.title(f'Computer Activity Over the Last {days} Days')

    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    plt.gcf().autofmt_xdate()

    plt.show()

    if save:
        logger.info(f"Saving graph as: {save}")
        plt.savefig(save)
        logger.info(f"Graph saved as {save}")
    else:
        logger.info("Displaying graph")
        plt.show()


if __name__ == "__main__":
    main.run(awake_graph)
