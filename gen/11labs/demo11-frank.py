import os
import asyncio
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import play

# You need to get your API key from your ElevenLabs account
# and either set it as an environment variable ELEVEN_API_KEY
# or pass it directly to AsyncElevenLabs like this:
ELEVEN_API_KEY = os.environ["ELEVENLABS_API_KEY"]

async def main():
    if ELEVEN_API_KEY == "YOUR_ELEVENLABS_API_KEY":
        print("Please replace 'YOUR_ELEVENLABS_API_KEY' with your actual ElevenLabs API key.")
        return

    client = AsyncElevenLabs(api_key=ELEVEN_API_KEY)

    text_to_say = "Hello world"
    voice_id = "JBFqnCBsd6RMkjVDRZzb"
    model_id = "eleven_multilingual_v2"

    print(f"Generating audio for: '{text_to_say}'...")
    try:
        # The .convert() method in AsyncElevenLabs returns an async generator
        audio_stream = client.text_to_speech.convert(
            text=text_to_say,
            voice_id=voice_id,
            model_id=model_id
        )

        # Collect all chunks from the async generator
        audio_bytes_list = []
        async for chunk in audio_stream:
            if chunk:  # Ensure the chunk is not None or empty
                audio_bytes_list.append(chunk)

        # Join all chunks to form the complete audio data
        full_audio = b"".join(audio_bytes_list)

        if full_audio:
            print("Playing audio...")
            play(full_audio) # play() expects the complete bytes
            print("Playback finished.")
        else:
            print("No audio data was generated.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
