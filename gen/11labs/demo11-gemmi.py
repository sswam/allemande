import os
import asyncio
import elevenlabs
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import play # For synchronous playback of collected bytes

# --- Set your API Key ---
ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
# ------------------------

async def speak_hello_world_collect_then_play(api_key: str):
    if not api_key or api_key == "YOUR_ELEVENLABS_API_KEY":
        print("Hey! Please set your ELEVENLABS_API_KEY in the script first.")
        print("You can get a key from your profile on the ElevenLabs website.")
        return

    try:
        print(f"Using elevenlabs library version: {elevenlabs.__version__}")
    except Exception:
        print("Could not determine elevenlabs library version.")

    print("Initializing AsyncElevenLabs client...")
    client = AsyncElevenLabs(api_key=api_key)

    text_to_say = "Hello world"
    voice_id_to_use = "pNInz6obpgDQGcFmaJgB" # Default "Adam" voice ID
    model_to_use = "eleven_multilingual_v2" # A common model

    print(f"Preparing to say: '{text_to_say}' (using Voice: {voice_id_to_use}, Model: {model_to_use})")

    audio_chunks_collected = bytearray() # Use bytearray for efficient concatenation of bytes

    try:
        print("Calling client.text_to_speech.stream() to get the async audio generator...")
        # This call returns an async generator. We do NOT 'await' the call itself.
        async_audio_generator = client.text_to_speech.stream(
            text=text_to_say,
            voice_id=voice_id_to_use,
            model_id=model_to_use
        )
        print(f"Type of object returned by client.text_to_speech.stream(): {type(async_audio_generator)}")

        print("Iterating over the async audio generator to collect all chunks...")
        chunk_count = 0
        # This is the correct way to consume an async generator:
        async for chunk in async_audio_generator:
            if chunk: # Make sure chunk is not empty
                audio_chunks_collected.extend(chunk)
                chunk_count += 1
                # print(f"  Collected chunk {chunk_count}, length: {len(chunk)}") # Uncomment for very verbose output

        print(f"Finished collecting audio. Total chunks: {chunk_count}, Total bytes: {len(audio_chunks_collected)}")

        if not audio_chunks_collected:
            print("No audio data was received from the stream. Possible reasons:")
            print("- API key issue (invalid, out of credits).")
            print("- Invalid voice_id or model_id.")
            print("- Text might be empty or contain only unsupported characters.")
            print("- Network connectivity issues to ElevenLabs API.")
            return

        print("\nAttempting to play the collected audio using elevenlabs.play()...")
        # elevenlabs.play() is a synchronous function that takes a single bytes object.
        play(bytes(audio_chunks_collected)) # Convert bytearray to bytes for play()
        print("Playback via elevenlabs.play() has been initiated.")
        print("(Note: elevenlabs.play() might be non-blocking, so script may end while audio is playing).")

    except TypeError as e:
        print(f"A TypeError occurred during the process: {e}")
        print("If this error occurred while doing 'async for chunk in async_audio_generator',")
        print("it would be very unusual and might point to a deeper environment or library issue.")
        import traceback
        traceback.print_exc()
    except elevenlabs.api.APIError as e: # Catch specific ElevenLabs API errors
        print(f"An ElevenLabs API Error occurred: {e}")
        if hasattr(e, 'status_code') and e.status_code == 401:
            print("This is a 401 Unauthorized error. Please double-check your API key's validity and credit status.")
        else:
            print("Details: ", e.body if hasattr(e, 'body') else "No additional details.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors

if __name__ == "__main__":
    print("Running script: Collect all audio chunks from async stream, then play synchronously.")
    print("This test helps diagnose if audio generation is working, separate from the `elevenlabs.stream` utility.")
    print("Make sure your ELEVENLABS_API_KEY is set in the script!\n")
    asyncio.run(speak_hello_world_collect_then_play(ELEVENLABS_API_KEY))
