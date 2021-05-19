#!/usr/bin/env python3

# Core
import queue
import time
import sys

# Community - Audio
import sounddevice as sd
import soundfile as sf

# Community - UI
import pygame
from pygame.locals import *

CHANNELS = 1
SAMPLE_RATE = 44100

def main():
    prefix = sys.argv[1]

    rec = Recorder()

    pygame.init()

    pygame.display.set_caption('audi-mem')
    window_surface = pygame.display.set_mode((800, 600))

    background = pygame.Surface((800, 600))
    background.fill(pygame.Color('#000000'))

    is_running = True

    filenames = []

    play_idx = 0
    while is_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYDOWN and event.key == K_r:
                filenames.append("{}-{}.wav".format(prefix, len(filenames)))
                print("recording {}...".format(filenames[-1]))
                rec.start(filenames[-1])
                play_idx = len(filenames) - 1
            elif event.type == pygame.KEYUP and event.key == K_q:
                is_running = False
            elif event.type == pygame.KEYUP and event.key == K_r:
                rec.stop()
            elif event.type == pygame.KEYDOWN and event.key == K_p:
                print("playing... {}")
                play_audio(filenames[play_idx])
            elif event.type == pygame.KEYDOWN and event.key == K_n:
                play_idx = min(len(filenames) - 1, play_idx + 1)
            elif event.type == pygame.KEYDOWN and event.key == K_1:
                play_idx = max(0, play_idx - 1)

        window_surface.blit(background, (0, 0))

        pygame.display.update()

def play_audio(path):
    data, fs = sf.read(path, dtype='float32')
    sd.play(data, fs)
    sd.wait()

class Recorder:

    def __init__(self):
        self.file = None
        self.buffer = None
        self.stream = None

    def start(self, path):
        self.file = sf.SoundFile(path, mode='x', samplerate=SAMPLE_RATE,
                channels=CHANNELS, subtype="PCM_24")

        self.buffer = queue.Queue()

        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=self.callback)
        self.stream.start()

    def stop(self):
        if self.file is None:
            raise "Attempted to stop a stopped recorder"

        self.stream.stop()

        while not self.buffer.empty():
            self.file.write(self.buffer.get())

        self.stream = None

        return self.file.name

    def callback(self, indata, frames, time, status):
        """Process an audio block (called asynchronously)."""
        if status:
            print("audio status: {}".format(status))
        else:
            self.buffer.put(indata.copy())

if __name__ == "__main__":
    main()
