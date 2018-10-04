import wave
import math
import pygame
import numpy as np
import struct


def sound_generator(name, frequency=440.0, duration=2.0, sample_rate=44100.0, wave_type='sin'):
    wavef = wave.open(name, 'w')
    wavef.setnchannels(1)  # mono
    wavef.setsampwidth(2)
    wavef.setframerate(sample_rate)

    for i in range(int(duration * sample_rate)):
        if wave_type == 'sin':
            value = int(32767.0*math.sin(frequency*math.pi*float(i)/float(sample_rate)))
        elif wave_type == 'white':
            value = 25 * int(np.random.normal(frequency, 200))
        else:
            raise Exception("{} is unknown wave_type".format(wave_type))

        data = struct.pack('<h', value)
        wavef.writeframesraw(data)

    wavef.writeframes(b'')
    wavef.close()


def play_sound(name, volume=1):
    pygame.mixer.music.load(name)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play()
