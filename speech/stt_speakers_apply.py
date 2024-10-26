#!/usr/bin/env python3

"""
This module applies speaker information to SRT or JSON transcripts.
"""

import json
import re
from typing import TextIO
from dataclasses import dataclass

from ally import main, logs  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()


@dataclass
class SpeakerSegment:
    """Represents a segment of speech by a specific speaker."""
    start: float
    end: float
    speaker: str


@dataclass
class TranscriptSegment:
    """Represents a segment of transcript with timing information."""
    start: float
    end: float
    text: str


def parse_speakers_tsv(tsv_content: str) -> list[SpeakerSegment]:
    """Parse TSV content and return a list of SpeakerSegments."""
    speakers = []
    for line in tsv_content.strip().split("\n"):
        start, end, speaker = line.split("\t")
        speakers.append(SpeakerSegment(float(start), float(end), speaker))
    return speakers


def parse_srt(srt_content: str) -> list[TranscriptSegment]:
    """Parse SRT content and return a list of TranscriptSegments."""
    segments = []
    pattern = re.compile(r"(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)\n((?:.+\n?)+)")

    for match in pattern.finditer(srt_content):
        start = parse_srt_time(match.group(1))
        end = parse_srt_time(match.group(2))
        text = match.group(3).strip()
        segments.append(TranscriptSegment(start, end, text))

    return segments


def parse_srt_time(time_str: str) -> float:
    """Convert SRT time string to seconds."""
    h, m, s = time_str.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def apply_speakers_to_srt(speakers: list[SpeakerSegment], segments: list[TranscriptSegment], min_speech_duration: float) -> str:
    """Apply speaker information to SRT segments."""
    output = ""
    for i, segment in enumerate(segments, start=1):
        speaker_list = find_speakers(speakers, segment.start, segment.end, min_speech_duration)
        output += f"{i}\n"
        output += f"{format_srt_time(segment.start)} --> {format_srt_time(segment.end)}\n"
        output += f"{', '.join(speaker_list)}: {segment.text}\n\n"
    return output.strip()


def apply_speakers_to_json(speakers: list[SpeakerSegment], json_data: dict, min_speech_duration: float) -> dict:
    """Apply speaker information to JSON transcript data."""
    for segment in json_data["segments"]:
        speaker_list = find_speakers(speakers, segment["start"], segment["end"], min_speech_duration)
        segment["speaker"] = ", ".join(speaker_list)
    return json_data


def find_speakers(speakers: list[SpeakerSegment], start: float, end: float, min_speech_duration: float) -> list[str]:
    """Find speakers for a given time segment, filtering out those speaking less than min_speech_duration."""
    speaker_list: list[str] = []
    valid_speakers = []
    for speaker in speakers:
        if (
            (start <= speaker.start < end)
            or (start < speaker.end <= end)
            or (speaker.start <= start and end <= speaker.end)
        ):
            overlap = min(end, speaker.end) - max(start, speaker.start)
            if overlap >= min_speech_duration:
                valid_speakers.append((speaker.speaker, overlap))

    if valid_speakers:
        valid_speakers.sort(key=lambda x: x[1], reverse=True)
        speaker_list = [s[0] for s in valid_speakers]
    else:
        speaker_list = ["Unknown"]

    return speaker_list


def process_transcript(istream: TextIO, ostream: TextIO, speakers_file: str, min_speech_duration: float) -> None:
    """Process the transcript, applying speaker information."""
    with open(speakers_file, 'r', encoding='utf-8') as f:
        speakers = parse_speakers_tsv(f.read())

    content = istream.read()

    is_json = content[0] == "{" and content[-1] == "}"
    is_srt = re.match(r"^\d+$", content, flags=re.MULTILINE)

    if is_json:
        json_data = json.loads(content)
        output = apply_speakers_to_json(speakers, json_data, min_speech_duration)
        json.dump(output, ostream, indent=4)
    elif is_srt:
        segments = parse_srt(content)
        output = apply_speakers_to_srt(speakers, segments, min_speech_duration)
        ostream.write(output)
    else:
        raise ValueError("Unsupported transcript format. Use .srt or .json files.")

    logger.info("Processed transcript")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("speakers_file", help="Path to the speakers TSV file")
    arg("-m", "--min-speech-duration", type=float, default=0.5, help="Minimum speech duration to consider (default: 0.5s)")


if __name__ == "__main__":
    main.go(process_transcript, setup_args)
