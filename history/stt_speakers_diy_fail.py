#!/usr/bin/env python3

"""
This module analyzes an audio file to identify different speakers and outputs
the results in a three-column TSV format.
"""

import sys
import logging
from typing import TextIO, Tuple, List

import numpy as np
import librosa
import torch
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from ally import main, logs, geput  # type: ignore

__version__ = "0.1.14"

logger = logs.get_logger()

# Default values for settings
DEFAULT_MIN_SPEECH_DURATION = 0.5
DEFAULT_SILERO_THRESHOLD = 0.5
DEFAULT_MAX_SPEAKERS = 5
DEFAULT_WINDOW_SIZE = 0.25  # seconds

# Global variables for Silero VAD model
vad_model = None
get_speech_timestamps = None


def load_silero_vad_model():
    """Load the Silero VAD model and related utilities."""
    global vad_model, get_speech_timestamps
    vad_model, vad_utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad")
    (get_speech_timestamps, _save_audio, _read_audio, _VADIterator, _collect_chunks) = vad_utils


def load_audio(file_path: str) -> Tuple[np.ndarray, float]:
    """Load audio file and return the audio time series and sampling rate."""
    y, sr = librosa.load(file_path)
    logger.debug(f"Audio loaded successfully. Duration: {len(y)/sr:.2f} seconds")

    # Resample to 16000 Hz if necessary for Silero VAD compatibility
    if sr not in [8000, 16000]:
        sr_new = (sr // 8000) * 8000
        y = librosa.resample(y, orig_sr=sr, target_sr=sr_new)
        sr = sr_new
        logger.debug(f"Audio resampled to {sr} Hz")

    return y, sr


def calculate_mel_diff(
    y: np.ndarray, sr: float, window_size: float = DEFAULT_WINDOW_SIZE
) -> np.ndarray:
    """Calculate the difference between consecutive mel spectrograms."""
    n_mels = 128
    hop_length = int(sr * window_size)
    n_fft = 2048

    mel_specs = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=n_mels, n_fft=n_fft, hop_length=hop_length
    )
    log_mel_specs = librosa.power_to_db(mel_specs)

    # Calculate the difference between consecutive spectrograms
    mel_diffs = np.diff(log_mel_specs, axis=1)
    logger.debug(f"Mel differences calculated. Shape: {mel_diffs.shape}")
    return mel_diffs


def extract_features(y: np.ndarray, sr: float, window_size: float) -> np.ndarray:
    """Extract log mel spectrogram features and mel differences from the audio."""
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)
    log_mel_spec = librosa.power_to_db(mel_spec)
    mfcc = librosa.feature.mfcc(S=log_mel_spec, n_mfcc=20)
    mel_diffs = calculate_mel_diff(y, sr, window_size)

    # Ensure mfcc and mel_diffs have the same number of time steps
    min_time_steps = min(mfcc.shape[1], mel_diffs.shape[1])
    mfcc = mfcc[:, :min_time_steps]
    mel_diffs = mel_diffs[:, :min_time_steps]

    # Combine MFCC and mel differences
    combined_features = np.concatenate([mfcc, mel_diffs], axis=0)
    logger.debug(f"Features extracted. Shape: {combined_features.T.shape}")
    return combined_features.T


def detect_number_of_speakers(features: np.ndarray) -> int:
    """Detect the optimal number of speakers using silhouette score."""
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    max_score = -1
    optimal_n = 1

    # TODO this doesn't work correctly

    for n in range(2, DEFAULT_MAX_SPEAKERS + 1):
        kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled_features)
        score = silhouette_score(scaled_features, labels)

        if score > max_score:
            max_score = score
            optimal_n = n

    logger.debug(f"Detected optimal number of speakers: {optimal_n}")
    return optimal_n


def cluster_speakers(features: np.ndarray, n_speakers: int) -> np.ndarray:
    """Cluster the features to identify different speakers."""
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    kmeans = KMeans(n_clusters=n_speakers, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled_features)
    logger.debug(f"Clustered speakers. Unique labels: {np.unique(labels)}")
    return labels


def generate_timestamps(
    labels: np.ndarray,
    sr: float,
    hop_length: int,
    y: np.ndarray,
    min_speech_duration: float,
    speech_timestamps: List[dict],
) -> List[Tuple[float, float, str]]:
    """Generate timestamps for each speaker segment."""
    timestamps = []
    frame_duration = hop_length / sr

    for speech_segment in speech_timestamps:
        segment_start = speech_segment["start"] / sr
        segment_end = speech_segment["end"] / sr

        segment_labels = labels[
            int(segment_start / frame_duration) : int(segment_end / frame_duration)
        ]
        if len(segment_labels) == 0:
            logger.warning(f"Empty segment found: {segment_start:.2f} - {segment_end:.2f}")
            continue

        current_speaker = chr(ord("A") + np.argmax(np.bincount(segment_labels)))
        timestamps.append((segment_start, segment_end, current_speaker))

    logger.debug(f"Generated {len(timestamps)} timestamps")
    return timestamps


# def is_silence_old(
#     y: np.ndarray, sr: float, start_time: float, end_time: float, threshold: float
# ) -> bool:
#     """Check if a segment is silence based on energy threshold."""
#     start_sample = int(start_time * sr)
#     end_sample = int(end_time * sr)
#     segment = y[start_sample:end_sample]
#
#     if len(segment) == 0:
#         return True
#
#     energy_db = librosa.amplitude_to_db(np.abs(segment), ref=np.max)
#     return np.mean(energy_db) < threshold


def analyze_audio(
    file_path: str,
    n_speakers: int,
    min_speech_duration: float,
    threshold: float,
    window_size: float,
) -> List[Tuple[float, float, str]]:
    """Analyze the audio file and return speaker segments."""
    y, sr = load_audio(file_path)
    features = extract_features(y, sr, window_size)

    if n_speakers == 0:
        n_speakers = detect_number_of_speakers(features)
        logger.info(f"Detected {n_speakers} speakers")

    labels = cluster_speakers(features, n_speakers)
    hop_length = int(sr * window_size)

    speech_timestamps = get_speech_timestamps(
        torch.from_numpy(y), vad_model, sampling_rate=sr, threshold=threshold
    )

    return generate_timestamps(labels, sr, hop_length, y, min_speech_duration, speech_timestamps)


def output_results(results: List[Tuple[float, float, str]], output: TextIO) -> None:
    """Output the results in TSV format."""
    if not results:
        logger.warning("No results to output.")
        return

    for start, end, speaker in results:
        output.write(f"{start:.2f}\t{end:.2f}\t{speaker}\n")
    logger.debug(f"Output {len(results)} results")


def stt_speakers(
    ostream: TextIO,
    file_path: str = "",
    n_speakers: int = 0,
    min_speech_duration: float = DEFAULT_MIN_SPEECH_DURATION,
    threshold: float = DEFAULT_SILERO_THRESHOLD,
    window_size: float = DEFAULT_WINDOW_SIZE,
) -> None:
    """Analyze an audio file to identify different speakers and output results."""
    if not file_path:
        raise ValueError("Input file path is required.")

    logger.info(f"Analyzing file: {file_path}")
    logger.info(
        f"Parameters: n_speakers={n_speakers}, min_speech_duration={min_speech_duration}, "
        f"threshold={threshold}, window_size={window_size}"
    )

    load_silero_vad_model()

    try:
        results = analyze_audio(
            file_path, n_speakers, min_speech_duration, threshold, window_size
        )
        output_results(results, ostream)
        logger.info(f"Analysis complete. Generated {len(results)} segments.")
    except Exception as e:
        logger.error(f"Error during audio analysis: {e}")
        raise


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("file_path", help="path to the input audio file")
    arg("-n", "--n-speakers", help="number of speakers to identify (0 for auto-detection)")
    arg("-m", "--min-speech-duration", help="minimum duration for a speech segment (in seconds)")
    arg("-s", "--silence-threshold", help="Silero VAD silence threshold (0.0 - 1.0)")
    arg("-w", "--window-size", help="duration of each spectrogram window (in seconds)")


if __name__ == "__main__":
    main.go(stt_speakers, setup_args)


# Regarding the use of existing models or tools, there are indeed some options
# available on Hugging Face that could be considered:
#
# 1. Pyannote Audio: This is a popular toolkit for speaker diarization, which
# includes pre-trained models. It's available on Hugging Face:
# https://huggingface.co/pyannote/speaker-diarization
#
# 2. SpeechBrain: This is another toolkit that includes models for speaker
# diarization and recognition: https://huggingface.co/speechbrain
#
# Using these pre-trained models could potentially provide better results and
# save development time. However, they might require more computational
# resources and have different dependencies.
#
# If you decide to use one of these pre-trained models, you would need to
# significantly refactor the code to integrate it. The current implementation
# provides more control over the process and can be useful for understanding
# the underlying concepts.
#
# As for other observations:
# 1. The code structure is generally good and follows Python best practices.
# 2. Error handling could be improved in some areas, especially when dealing with file operations and external library calls.
# 3. The silence detection method could potentially be improved by using more sophisticated voice activity detection algorithms.
#
# These are areas that could be addressed in future iterations of the code.
#
# If you still encounter issues with specific audio files, you may want to
# consider adjusting the `min_speech_duration` parameter to a lower value when
# calling the `stt_speakers` function.
