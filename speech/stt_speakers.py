#!/usr/bin/env python3

"""
Analyze an audio file to identify different speakers and output results in TSV format.
"""

import sys
from typing import TextIO

from pyannote.audio import Pipeline  # type: ignore

from ally import main, logs  # type: ignore

__version__ = "0.1.22"

logger = logs.get_logger()


def load_pyannote_pipeline() -> Pipeline:
    """Load the Pyannote Audio pipeline."""
    return Pipeline.from_pretrained("pyannote/speaker-diarization")


def analyze_audio(
    file_path: str,
    pipeline: Pipeline,
    speakers: int,
) -> list[tuple[float, float, str]]:
    """Analyze the audio file and return speaker segments."""
    diarization_result = pipeline(file_path, num_speakers=speakers)
    results = [
        (turn.start, turn.end, speaker)
        for turn, _, speaker in diarization_result.itertracks(yield_label=True)
    ]

    logger.debug("Generated %d segments", len(results))
    return results


def output_results(results: list[tuple[float, float, str]], output: TextIO) -> None:
    """Output the results in TSV format."""
    if not results:
        logger.warning("No results to output.")
        return

    for start, end, speaker in results:
        output.write(f"{start:.2f}\t{end:.2f}\t{speaker}\n")
    logger.debug("Output %d results", len(results))


def stt_speakers(
    ostream: TextIO,
    file_path: str = "",
    speakers: int = 2,
) -> None:
    """Analyze an audio file to identify different speakers and output results."""
    if not file_path:
        raise ValueError("Input file path is required.")

    logger.info("Analyzing file: %s", file_path)

    pipeline = load_pyannote_pipeline()
    results = analyze_audio(file_path, pipeline, speakers)
    output_results(results, ostream)
    logger.info("Analysis complete. Generated %d segments.", len(results))


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("file_path", help="path to the input audio file")
    arg("-n", "--speakers", type=int, default=2, help="Number of speakers")


if __name__ == "__main__":
    main.go(stt_speakers, setup_args)
