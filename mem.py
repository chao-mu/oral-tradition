#!/usr/bin/env python3

# Core
import queue
import time
import sys
import glob
import os

# Community - Audio
import sounddevice as sd
import soundfile as sf

# Community - UI
import pygame
from pygame.locals import *

CHANNELS = 1
SAMPLE_RATE = 44100

def main():
    base = sys.argv[1]

    rec = Recorder()

    pygame.init()

    clock = pygame.time.Clock()

    window_surface = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('oral traadition')

    background = pygame.Surface((800, 600))
    background.fill(pygame.Color('#000000'))

    is_running = True

    file_manager = FileManager(base)

    play_idx = 0
    while is_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYUP and event.key == K_q:
                is_running = False
            elif event.type == pygame.KEYDOWN and event.key == K_r:
                rec.start(file_manager.new_file())
            elif event.type == pygame.KEYUP and event.key == K_r:
                rec.stop()
            elif event.type == pygame.KEYDOWN and event.key == K_p:
                play_audio(file_manager.current)
            elif event.type == pygame.KEYDOWN and event.key == K_n:
                file_manager.next()
            elif event.type == pygame.KEYDOWN and event.key == K_b:
                file_manager.back()
            elif event.type == pygame.KEYDOWN and event.key == K_s:
                file_manager.seek(0)
            elif event.type == pygame.KEYDOWN and event.key == K_e:
                file_manager.seek(-1)

        window_surface.blit(background, (0, 0))

        pygame.display.update()
        clock.tick(30)

def play_audio(path):
    sd.stop()
    data, fs = sf.read(path, dtype='float32')
    sd.play(data, fs)

class FileManager:

    def __init__(self, base):
        self.paths = sorted(glob.glob("{}/*.wav".format(base)))
        self.base = base
        self.idx = 0

    def new_file(self):
        path = "{}/{}.wav".format(self.base, str(len(self.paths) + 1).zfill(5))
        self.paths.append(path)

        return path

    def seek(self, pos):
        if pos < 0:
            self.idx = max(0, self.max_idx + pos)
        else:
            self.idx = min(self.max_idx, pos)

    def next(self, count=1):
        self.idx = min(self.max_idx, self.idx + count)

    def back(self, count=1):
        self.idx = max(0, self.idx - count)

    @property
    def current(self):
        return self.paths[self.idx]

    def remove_current(self):
        os.remove(self.paths.pop())

    @property
    def max_idx(self):
        return len(self.paths) - 1

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
