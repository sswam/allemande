#!/usr/bin/env python3

"""
This module visualizes an audio file waveform as a log mel spectrogram in a wide window.
"""

from math import log

import numpy as np
import librosa
import matplotlib.pyplot as plt

from ally import main, logs  # type: ignore

__version__ = "0.1.13"

logger = logs.get_logger()


def load_audio(file_path: str) -> tuple[np.ndarray, int]:
    """Load audio file and return the time series and sampling rate."""
    y, sr = librosa.load(file_path)
    return y, int(sr)


def create_mel_spectrogram(y: np.ndarray, sr: int, fmin: float, fmax: float) -> np.ndarray:
    """Create a mel spectrogram from the audio time series."""
    n_mels = (log(fmax) - log(fmin)) * 20
    logger.debug("Number of mel bands: %s", n_mels)
    return librosa.feature.melspectrogram(y=y, sr=sr, fmin=fmin, fmax=fmax, n_mels=n_mels)


def plot_spectrogram(
    S: np.ndarray,
    sample_rate: int,
    threshold: float,
    fmin: float,
    fmax: float,
    output_file: str = None,
) -> None:
    """Plot the log mel spectrogram."""
    fig, ax = plt.subplots(figsize=(20, 5))
    S_dB = librosa.power_to_db(S, ref=np.max)

    if threshold != float("-inf"):
        S_dB = np.where(S_dB <= threshold, -80, S_dB)

    img = librosa.display.specshow(
        S_dB, x_axis="time", y_axis="mel", sr=sample_rate, fmin=fmin, fmax=fmax, ax=ax
    )
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    ax.set_title("Log Mel-frequency spectrogram")
    plt.tight_layout()

    if output_file:
        plt.savefig(output_file)
    else:
        plt.show()


def audio_view(
    audio: np.ndarray,
    sample_rate: int,
    threshold: float = float("-inf"),
    fmin: float = 20,
    fmax: float = 10000,
    output_file: str = None,
) -> None:
    """Visualize audio data as a log mel spectrogram."""
    S = create_mel_spectrogram(audio, sample_rate, fmin, fmax)
    plot_spectrogram(S, sample_rate, threshold, fmin, fmax, output_file)


def audio_view_file(
    file: str,
    output_file: str = None,
    threshold: float = float("-inf"),
    fmin: float = 20,
    fmax: float = 10000,
) -> None:
    """Visualize an audio file waveform as a log mel spectrogram."""
    audio, sample_rate = load_audio(file)
    audio_view(audio, sample_rate, threshold, fmin, fmax, output_file)


def setup_args(arg) -> None:
    """Set up the command-line arguments."""
    arg("file", help="Path to the audio file")
    arg("output_file", nargs="?", help="Path to save the output PNG file")
    arg("-s", "--threshold", help="Silence threshold in dB.")
    arg("-f", "--fmin", help="Minimum frequency for the spectrogram")
    arg("-g", "--fmax", help="Maximum frequency for the spectrogram")


if __name__ == "__main__":
    main.go(audio_view_file, setup_args)
