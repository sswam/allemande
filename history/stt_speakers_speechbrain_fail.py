#!/usr/bin/env python3

"""
This module analyzes an audio file to identify different speakers and outputs
the results in a three-column TSV format using Pyannote Audio or SpeechBrain.
"""

from typing import TextIO

import numpy as np
from pyannote.audio import Pipeline  # type: ignore
from speechbrain.processing import diarization as sb_diarization  # type: ignore
from speechbrain.inference import EncoderClassifier  # type: ignore

# lazy('pyannote.audio', 'Pipeline')
# lazy('speechbrain.inference', 'EncoderClassifier')

from ally import main, logs  # type: ignore

__version__ = "0.1.20"

logger = logs.get_logger()


def load_pyannote_pipeline() -> Pipeline:
    """Load the Pyannote Audio pipeline."""
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
    return pipeline


def load_speechbrain_pipeline() -> tuple[EncoderClassifier, sb_diarization.Spec_Cluster]:
    """Load the SpeechBrain pipeline."""
    encoder = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="pretrained_models/spkrec-ecapa-voxceleb",
    )
    clusterer = sb_diarization.Spec_Cluster()
    return encoder, clusterer


def analyze_audio(
    file_path: str,
    pipeline: Pipeline | tuple[EncoderClassifier, sb_diarization.Spec_Cluster],
    speechbrain: bool,
    speakers: int,
) -> list[tuple[float, float, str]]:
    """Analyze the audio file and return speaker segments."""
    if speechbrain:
        encoder, clusterer = pipeline
        # Extract embeddings
        signal = encoder.load_audio(file_path)
        embeds = encoder.encode_batch(signal)

        # Reshape embeddings if necessary
        if embeds.ndim == 3:
            embeds = embeds.squeeze(0)  # Remove batch dimension if present
        if embeds.ndim == 3:
            embeds = embeds.mean(axis=1)  # Average over time dimension

        # Perform spectral clustering
        labels = clusterer.perform_sc(embeds, n_neighbors=speakers - 1)

        # Convert labels to segments
        segment_duration = len(signal) / encoder.sample_rate / len(labels)
        results = [
            (i * segment_duration, (i + 1) * segment_duration, f"SPEAKER_{label}")
            for i, label in enumerate(labels)
        ]
    else:
        diarization_result = pipeline(file_path)
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
    speechbrain: bool = False,
    speakers: int = 2,
) -> None:
    """Analyze an audio file to identify different speakers and output results."""
    if not file_path:
        raise ValueError("Input file path is required.")

    logger.info("Analyzing file: %s", file_path)

    pipeline = load_speechbrain_pipeline() if speechbrain else load_pyannote_pipeline()
    results = analyze_audio(file_path, pipeline, speechbrain, speakers)
    output_results(results, ostream)
    logger.info("Analysis complete. Generated %d segments.", len(results))


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("file_path", help="path to the input audio file")
    arg("-b", "--speechbrain", action="store_true", help="use SpeechBrain not Pyannote Audio")
    arg("-n", "--speakers", help="Number of speakers")


if __name__ == "__main__":
    main.go(stt_speakers, setup_args)
