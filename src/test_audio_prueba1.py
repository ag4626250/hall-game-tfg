import os
import wave
from pathlib import Path
from time import sleep

# Forzamos ALSA porque es la salida que ya funcionó en la Raspberry.
os.environ["SDL_AUDIODRIVER"] = "alsa"

import pygame


def crear_silencio(path, duracion=0.7, sample_rate=44100):
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        silencio = (0).to_bytes(2, byteorder="little", signed=True)
        for _ in range(int(sample_rate * duracion)):
            wav.writeframes(silencio + silencio)


base_dir = Path(__file__).resolve().parent.parent
audio_dir = base_dir / "assets" / "audios"

silencio_path = audio_dir / "silencio.wav"
audio_path = audio_dir / "prueba1_inicio_stereo.mp3"

crear_silencio(silencio_path)

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
pygame.mixer.init()

print("Reproduciendo silencio inicial...")
pygame.mixer.music.load(str(silencio_path))
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    sleep(0.1)

print("Reproduciendo audio real...")
pygame.mixer.music.load(str(audio_path))
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    sleep(0.1)

pygame.mixer.quit()
print("Prueba finalizada")