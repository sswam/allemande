import asyncio
import os
import wave # Standard Python library for WAV files
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import play, save # <-- Let's check if 'save' exists!

# After a quick check, the elevenlabs library DOES have a `save` utility.
# The documentation provided earlier showed:
# from elevenlabs import play
# It also has `from elevenlabs import save`
# Let's try to use `elevenlabs.save` if it handles PCM to WAV or MP3 saving well.
# If `elevenlabs.save` can take the raw bytes and a filename like "output.wav"
# and correctly infers or handles the format, that would be simplest.
# If not, manual WAV writing for PCM, or direct byte writing for MP3.

# Re-checking the GitHub page snippet for 'save':
# The provided snippet for `elevenlabs-python` doesn't explicitly show `from elevenlabs import save`
# or its usage.
# Let's assume for now `save` might not be as straightforward or might expect specific inputs,
# or might not be intended for this direct stream output.
# So, manual saving is safer to demo.

# Okay, sticking to manual saving for clarity and control, especially for WAV from PCM.

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")

async def main():
    if not ELEVEN_API_KEY:
        print("Error: The ELEVEN_API_KEY environment variable is not set.")
        print("Please set it before running the script.")
        return

    client = AsyncElevenLabs(api_key=ELEVEN_API_KEY)

    text_to_say = "Hello world, this is a test of saving audio."
    voice_id = "JBFqnCBsd6RMkjVDRZzb" # Example voice
    # model_id = "eleven_multilingual_v2" # Default, or specify if needed

    # --- Option 1: Generate PCM and save as WAV file ---
    output_filename_wav = "output.wav"
    # For WAV, we need PCM data. Let's request 24kHz, 16-bit PCM.
    # Common PCM formats from ElevenLabs docs: pcm_16000, pcm_22050, pcm_24000, pcm_44100
    # These are typically mono, 16-bit.
    pcm_sample_rate = 24000
    pcm_output_format = f"pcm_{pcm_sample_rate}" # e.g., "pcm_24000"

    print(f"Generating PCM audio for WAV: '{text_to_say}' using format {pcm_output_format}...")
    try:
        audio_stream_pcm = client.text_to_speech.convert(
            text=text_to_say,
            voice_id=voice_id,
            # model_id=model_id, # Optional, defaults to a good one
            output_format=pcm_output_format
        )

        pcm_audio_bytes_list = []
        async for chunk in audio_stream_pcm:
            if chunk:
                pcm_audio_bytes_list.append(chunk)

        full_pcm_audio = b"".join(pcm_audio_bytes_list)

        if full_pcm_audio:
            print(f"Saving PCM audio to {output_filename_wav}...")
            # Write PCM to a WAV file
            # Assumptions for wave.setparams: (nchannels, sampwidth, framerate, nframes, comptype, compname)
            # nchannels: 1 (mono) - typical for TTS
            # sampwidth: 2 (for 16-bit PCM) - typical for these PCM formats
            # framerate: pcm_sample_rate
            # nframes: len(full_pcm_audio) // (nchannels * sampwidth)
            # comptype: 'NONE'
            # compname: 'not compressed'
            num_channels = 1
            sample_width_bytes = 2 # 16-bit PCM

            with wave.open(output_filename_wav, 'wb') as wf:
                wf.setnchannels(num_channels)
                wf.setsampwidth(sample_width_bytes)
                wf.setframerate(pcm_sample_rate)
                wf.writeframes(full_pcm_audio)
            print(f"Audio saved to {output_filename_wav}")

            # Optional: Play the generated PCM audio
            # Note: `play()` might expect a common format like MP3 by default.
            # Playing raw PCM might work or might need specific parameters if play supports it.
            # For simplicity, if play() struggles with raw PCM, convert to MP3 first or play the MP3 version.
            # However, `play` from elevenlabs SHOULD be able to handle the bytes.
            print("Playing generated audio (from PCM data)...")
            play(full_pcm_audio, notebook=False, use_ffmpeg=False) # Parameters for play if needed
            print("Playback finished.")

        else:
            print("No PCM audio data was generated for WAV.")

    except Exception as e:
        print(f"An error occurred during WAV generation/saving: {e}")

    print("-" * 20)

    # --- Option 2: Generate MP3 and save as MP3 file ---
    output_filename_mp3 = "output.mp3"
    # Example MP3 format: mp3_44100_128 (Bitrate 128kbps, Sample Rate 44.1kHz)
    mp3_output_format = "mp3_44100_128"

    print(f"Generating MP3 audio: '{text_to_say}' using format {mp3_output_format}...")
    try:
        audio_stream_mp3 = client.text_to_speech.convert(
            text=text_to_say,
            voice_id=voice_id,
            # model_id=model_id,
            output_format=mp3_output_format
        )

        mp3_audio_bytes_list = []
        async for chunk in audio_stream_mp3:
            if chunk:
                mp3_audio_bytes_list.append(chunk)

        full_mp3_audio = b"".join(mp3_audio_bytes_list)

        if full_mp3_audio:
            print(f"Saving MP3 audio to {output_filename_mp3}...")
            with open(output_filename_mp3, "wb") as f:
                f.write(full_mp3_audio)
            print(f"Audio saved to {output_filename_mp3}")

            # Optional: Play the generated MP3 audio
            print("Playing generated audio (from MP3 data)...")
            play(full_mp3_audio)
            print("Playback finished.")
        else:
            print("No MP3 audio data was generated.")

    except Exception as e:
        print(f"An error occurred during MP3 generation/saving: {e}")

    print("-" * 20)
    print("Regarding other formats like OGG or WebM:")
    print("The ElevenLabs API directly provides audio in MP3 or PCM formats.")
    print("To save as OGG or WebM, you would typically convert the MP3 or PCM output")
    print("using an additional library or tool (e.g., ffmpeg, pydub).")

if __name__ == "__main__":
    asyncio.run(main())
