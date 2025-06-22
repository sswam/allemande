import asyncio
import os
# import wave # Not needed if we're primarily saving MP3
from elevenlabs.client import AsyncElevenLabs

# --- Configuration ---
# API Key will be read from environment variable ELEVENLABS_API_KEY
TEXT_TO_SAY = "Hello world, this audio is being saved to an MP3 file!"
OUTPUT_FILENAME_MP3 = "output.mp3"
# OUTPUT_FILENAME_WAV = "output.wav" # For the tier-restricted WAV saving method

# Voice and Model Settings
VOICE_ID = "pNInz6obpgDQGcFmaJgB" # Example: "Adam" - find IDs in your VoiceLab
MODEL_ID = "eleven_multilingual_v2" # Or your preferred model

# For direct MP3 saving, which is generally available on all tiers:
MP3_OUTPUT_FORMAT = "mp3_44100_128" # Example: MP3 at 44.1kHz, 128kbps

# --- Tier-Restricted PCM Settings (for reference if you upgrade) ---
# PCM_OUTPUT_FORMAT = "pcm_44100" # Requires Pro tier or above
# PCM_FRAMERATE = 44100
# PCM_SAMPWIDTH = 2 # 2 bytes for 16-bit audio
# PCM_NCHANNELS = 1 # Mono
# --------------------------------------------------------------------

async def generate_and_save_audio_to_mp3_file():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: The ELEVENLABS_API_KEY environment variable is not set.")
        print("Please set it before running the script.")
        return

    print(f"Initializing ElevenLabs async client...")
    client = AsyncElevenLabs(api_key=api_key)

    print(f"Requesting audio for: '{TEXT_TO_SAY}'")
    print(f"Using Voice ID: {VOICE_ID}, Model ID: {MODEL_ID}")

    # --- Primary Method: Generate MP3 and save directly ---
    print(f"Requesting output format: {MP3_OUTPUT_FORMAT}")
    audio_chunks_collected_for_mp3 = bytearray()
    try:
        print("Streaming MP3 audio data from ElevenLabs...")
        async_mp3_audio_stream = client.text_to_speech.stream(
            text=TEXT_TO_SAY,
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
            output_format=MP3_OUTPUT_FORMAT
        )

        chunk_count = 0
        async for chunk in async_mp3_audio_stream:
            if chunk:
                audio_chunks_collected_for_mp3.extend(chunk)
                chunk_count += 1
        print(f"Finished streaming MP3 data. Total chunks: {chunk_count}, Total bytes: {len(audio_chunks_collected_for_mp3)}")

        if not audio_chunks_collected_for_mp3:
            print("No MP3 audio data was received. Check API key, credits, or input text.")
            return

        print(f"Saving MP3 data as '{OUTPUT_FILENAME_MP3}'...")
        with open(OUTPUT_FILENAME_MP3, 'wb') as f_mp3:
            f_mp3.write(audio_chunks_collected_for_mp3)
        print(f"Successfully saved audio to '{OUTPUT_FILENAME_MP3}'")

    except elevenlabs.api.APIError as e:
        print(f"An ElevenLabs API Error occurred: {e}")
        if hasattr(e, 'body') and e.body:
            print(f"Error details: {e.body}")
        if hasattr(e, 'status_code') and e.status_code == 401:
            print("This is a 401 Unauthorized error. Please double-check your API key's validity and credit status.")
    except Exception as e:
        print(f"Error during MP3 generation/saving: {e}")
        import traceback
        traceback.print_exc()

    # --- Option for WAV (Requires Pro Tier or above - Commented out) ---
    # print(f"\n--- Attempting to save as WAV (Requires Pro Tier) ---")
    # print(f"Output format for WAV: {PCM_OUTPUT_FORMAT}")
    # audio_chunks_collected_for_wav = bytearray()
    # try:
    #     print("Streaming PCM audio data from ElevenLabs...")
    #     async_pcm_audio_stream = client.text_to_speech.stream(
    #         text=TEXT_TO_SAY + " (PCM attempt)",
    #         voice_id=VOICE_ID,
    #         model_id=MODEL_ID,
    #         output_format=PCM_OUTPUT_FORMAT
    #     )
    #     async for chunk in async_pcm_audio_stream:
    #         if chunk:
    #             audio_chunks_collected_for_wav.extend(chunk)
    #     print(f"Finished streaming PCM data. Total bytes: {len(audio_chunks_collected_for_wav)}")

    #     if not audio_chunks_collected_for_wav:
    #         print("No PCM audio data was received.")
    #     else:
    #         print(f"Saving PCM data as '{OUTPUT_FILENAME_WAV}'...")
    #         with wave.open(OUTPUT_FILENAME_WAV, 'wb') as wf:
    #             wf.setnchannels(PCM_NCHANNELS)
    #             wf.setsampwidth(PCM_SAMPWIDTH)
    #             wf.setframerate(PCM_FRAMERATE)
    #             wf.writeframes(audio_chunks_collected_for_wav)
    #         print(f"Successfully saved audio to '{OUTPUT_FILENAME_WAV}' (if Pro tier access was granted).")
    # except elevenlabs.api.APIError as e:
    #     print(f"API Error during WAV generation (likely tier restriction): {e}")
    #     if hasattr(e, 'body') and e.body and 'output_format_not_allowed' in str(e.body):
    #         print("As expected, PCM output format is likely restricted for your current API tier.")
    #     elif hasattr(e, 'body'):
    #         print(f"Error details: {e.body}")
    # except Exception as e:
    #     print(f"Other error during WAV generation/saving: {e}")

if __name__ == "__main__":
    print("Running script to generate TTS audio and save to MP3 file.")
    print(f"Ensure the 'ELEVENLABS_API_KEY' environment variable is set.\n")
    asyncio.run(generate_and_save_audio_to_mp3_file())
