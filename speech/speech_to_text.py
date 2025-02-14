from ally import portals, filer
import av_convert


portal = portals.get_portal("stt_whisper")


# formats that whisper can handle, and are not too large
acceptable_audio_formats = ("ogg", "mp3", "m4a", "webm")


async def convert_audio_video_to_text(file: str, medium: str) -> str:
    """Convert audio or video file to text."""
    remove_audio_file = False
    ext = Path(file).suffix.lower().lstrip(".")

    if medium not in ("audio", "video"):
        raise ValueError(f"Unknown medium: {medium}")
    if medium == "audio" and ext in acceptable_audio_formats:
        audio_file = file
    else:
        file_path = Path(file)
        audio_file = filer.generate_unique_name(str(file_path.parent), file_path.stem, "webm")
        await av_convert.convert_to_audio(file, audio_file)
        remove_audio_file = True

    text, confident, _result = await speech_to_text(portal, audio_file)

    if remove_audio_file:
        audio_file.unlink()

    return text if confident else None


async def client_request(portal, audio_file, config=None):
    """ Call the core server and get a response. """
    req = portals.prepare_request(portal, config=config)
    req_audio = req/"request.aud"
    portals.link_or_copy(audio_file, req_audio)
    await portals.send_request(portal, req)
    await resp, status = portals.wait_for_response(portal, req)
    if status == "error":
        await portals.response_error(resp)
    text = (resp/"text.txt").read_text(encoding="utf-8")
    result = yaml.safe_load((resp/"result.yaml").read_text(encoding="utf-8"))
    await portals.remove_response(portal, resp)
    return text, result


async def speech_to_text(portal, audio_filename, lang=None, confidence_threshold=0.8):
    """ Transcribe an acceptable audio file to text """
    config = {
        "language": lang,
        "confidence_threshold": confidence_threshold,
    }
    text, result = await client_request(portal, audio, config=config)
    return text, result["confident"], result
