#!/usr/bin/env python3

"""
This module provides a function to map quality scores from one scale to another,
using line segments.
"""

from ally import main

__version__ = "1.0.3"

logger = main.get_logger()


def map_score(old_score: float|None) -> float:
    """
    Maps an old score from 0.0–6.0 to a new score from 0.0–10.0, where lower scores
    represent better quality. Handles invalid or empty files by assigning
    scores of 9 or 10.

    Parameters:
        old_score (float or None): The old score between 0.0 and 6.0.
            Use 6.0 for blank content, and None for corrupt or empty files.

    Returns:
        float: The new score between 0.0 and 10.0.
    """
    if old_score is None:
        logger.info("Empty file detected, assigning maximum score")
        return 10.0

    old_score = max(0.0, min(6.0, old_score))
    logger.debug(f"Mapping old score: {old_score}")

    if old_score <= 1.0:
        new_score = old_score
    elif old_score <= 2.0:
        new_score = 1.0 + (old_score - 1.0) * 2.0
    elif old_score <= 3.0:
        new_score = 3.0 + (old_score - 2.0) * 2.0
    elif old_score <= 4.0:
        new_score = 5.0 + (old_score - 3.0) * 2.0
    elif old_score <= 5.0:
        new_score = 7.0 + (old_score - 4.0) * 2.0
    else:
        new_score = 9.0 + (old_score - 5.0)

    logger.debug(f"Mapped to new score: {new_score}")
    return new_score


if __name__ == "__main__":
    main.run(map_score)
