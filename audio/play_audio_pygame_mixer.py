"""Audio playback module using pygame.mixer"""

import time
import pygame.mixer


def play_audio_v1(audio_data: bytes) -> None:
    """Play audio data using pygame.mixer

    Args:
        audio_data: Raw audio data as bytes
    """
    sound = pygame.mixer.Sound(audio_data)
    sound.play()
    time.sleep(sound.get_length())


if __name__ == "__main__":
    pygame.mixer.init(frequency=24000, channels=1)

    path_audio = "audio.bin"

    with open(path_audio, "rb") as fh:
        audio_buffer = bytearray(fh.read())

    for _ in range(3):
        play_audio_v1(audio_buffer)
        time.sleep(5)  # Additional delay between plays

    pygame.mixer.quit()  # Clean up once at the end
