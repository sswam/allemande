#!/usr/bin/env python3-allemande

"""
Check if video is compatible with web platform and encode if needed.
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


async def get_codecs(file_path: str) -> tuple[list[str], list[str]]:
    """Get the container and codecs of the video."""
    cmd = ["ffprobe", "-v", "error", "-show_entries",
        "stream=codec_name,codec_type", "-of", "json", file_path]

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()

    logger.debug("ffprobe stdout: %s", stdout.decode("utf-8"))
    logger.debug("ffprobe stderr: %s", stderr.decode("utf-8"))

    data = json.loads(stdout)
    video_codecs = set()
    audio_codecs = set()

    for stream in data.get("streams", []):
        if stream["codec_type"] == "video":
            video_codecs.add(stream["codec_name"])
        elif stream["codec_type"] == "audio":
            audio_codecs.add(stream["codec_name"])

    return list(video_codecs), list(audio_codecs)


async def check_container_and_streamable(file_path: str) -> bool:
    """Check the video container format, and whether it is streamable."""
    cmd = ["mediainfo", "--Output=JSON", "-f", file_path]

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()

    logger.debug("mediainfo stdout: %s", stdout.decode("utf-8"))
    logger.debug("mediainfo stderr: %s", stderr.decode("utf-8"))

    data = json.loads(stdout)

    track = data.get("media", {}).get("track", [{}])[0]
    container = track.get("Format", "")
    streamable = track.get("IsStreamable", "No") == "Yes"

    return container, streamable


async def check(file_path: str) -> dict:
    """Check if video is compatible with the web platform."""
    video_codecs, audio_codecs = await get_codecs(file_path)
    container, streamable = await check_container_and_streamable(file_path)

    container_compatible = container in ["MPEG-4", "Ogg", "WebM"]
    video_compatible = all(codec in ["h264", "vp8", "vp9", "av1"] for codec in video_codecs)
    audio_compatible = all(codec in ["aac", "vorbis", "opus"] for codec in audio_codecs)

    return {
        "compatible": container_compatible and video_compatible and audio_compatible and streamable,
        "container_compatible": container_compatible,
        "video_compatible": video_compatible,
        "audio_compatible": audio_compatible,
        "streamable": streamable,
        "container": container,
        "video_codecs": list(video_codecs),
        "audio_codecs": list(audio_codecs),
    }


async def recode_if_needed(file_path: str, result=None, replace: bool = False, fast: bool = False) -> str:
    """Encode video if it is not compatible with the web platform."""
    result = result or await check(file_path)

    if result["compatible"]:
        return file_path

    logger.info("Video is not compatible, encoding...")
    ifile = Path(file_path)
    directory = ifile.parent
    prefix = ifile.stem + "_"

    with tempfile.NamedTemporaryFile(delete=False, dir=directory,
                                prefix=prefix, suffix=".mp4") as ofile:
        ofile.close()

    video_codec = "copy" if result["video_compatible"] else "libx264"
    audio_codec = "copy" if result["audio_compatible"] else "aac"

    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", file_path,
        "-f", "mp4", "-movflags", "+faststart",
        "-c:v", video_codec, "-c:a", audio_codec,
    ]

    if fast:
        cmd.extend(["-preset", "ultrafast"])

    cmd.append(ofile.name)

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error("ffmpeg stdout: %s", stdout.decode("utf-8"))
        logger.error("ffmpeg stderr: %s", stderr.decode("utf-8"))
        raise RuntimeError(f"ffmpeg failed with return code {process.returncode}")

    stats = os.stat(ifile)
    os.chmod(ofile.name, stats.st_mode)
    os.utime(ofile.name, ns=(stats.st_atime_ns, stats.st_mtime_ns))

    if not replace:
        return ofile.name

    Path(ofile.name).rename(ifile)
    return file_path


async def video_compatible(file: str, recode: bool = False,
                        replace: bool = False, fast: bool = False) -> None:
    """Check or re-encode video for web platform compatibility."""
    if recode:
        result = await recode_if_needed(file, replace=replace, fast=fast)
        print(result)
    else:
        result = await check(file)
        print(json.dumps(result))


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("file", help="video file to check")
    arg("--recode", action="store_true", help="re-encode video if needed")
    arg("--replace", action="store_true", help="replace video file with re-encoded video")
    arg("--fast", action="store_true", help="use fast encoding settings")


if __name__ == "__main__":
    main.go(video_compatible, setup_args)
