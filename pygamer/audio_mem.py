import time
import board
import digitalio
import audiomp3
import audioio
import analogio
import displayio
import repeat
import terminalio
import analogjoy
from adafruit_display_text.label import Label
import os


speaker_enable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
speaker_enable.switch_to_output(value=True)
speaker = audioio.AudioOut(board.SPEAKER)

joystick = analogjoy.AnalogJoystick()

up_key = repeat.KeyRepeat(lambda: joystick.up, rate=0.2)
down_key = repeat.KeyRepeat(lambda: joystick.down, rate=0.2)
left_key = repeat.KeyRepeat(lambda: joystick.left, rate=0.2)
right_key = repeat.KeyRepeat(lambda: joystick.right, rate=0.2)

BUTTON_SEL = const(8)
BUTTON_START = const(4)
BUTTON_A = const(2)
BUTTON_B = const(1)

buttons = gamepadshift.GamePadShift(digitalio.DigitalInOut(board.BUTTON_CLOCK),
                                    digitalio.DigitalInOut(board.BUTTON_OUT),
                                    digitalio.DigitalInOut(board.BUTTON_LATCH))

def main():
    display = board.DISPLAY

    mp3_paths = [d for d in os.listdir("/") if not d.startswith('.') and d.lower().endswith('.mp3')]
    files = CursorList(sorted(mp3_paths))
    play_audio(files.current)

    while True:
        joystick.poll()

        if up_key.value:
            files.back()
        elif down_key.value:
            files.forward()

        main_group = displayio.Group(max_size=25)

        line = Label(terminalio.FONT, text=files.current, color=(255, 192, 203))
        line.y = 10
        main_group.append(line)

        display.show(main_group)

        time.sleep(0.33)


def play_audio(path):
    stream = audiomp3.MP3Decoder(open(path, "rb"))
    speaker.play(stream)

class Button:

    def __init__(self, pin):
        btn = digitalio.DigitalInOut(board.SWITCH)
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.UP

        self.btn = btn
        self.prev_state = False
        self.cur_state = False

    def poll(self):
        self.cur_state = self.btn.value
        pressed = self.cur_state != self.prev_state

class CursorList(list):

    def __init__(self, els):
        self.idx = 0
        super().__init__(els)

    def join(self, s=" "):
        return s.join(self)

    def goto(self, pos):
        if pos < 0:
            self.idx = max(0, self.max_idx + pos)
        else:
            self.idx = min(self.max_idx, pos)

        self.word_idx = 0

    def next(self, count=1):
        self.idx = min(self.max_idx, self.idx + count)
        self.word_idx = 0

    def back(self, count=1):
        self.idx = max(0, self.idx - count)
        self.word_idx = 0

    @property
    def peek_next(self):
        if self.idx == self.max_idx:
            return None

        return self[self.idx + 1]

    @property
    def current(self):
        return self[self.idx]

    @property
    def max_idx(self):
        return len(self) - 1


if __name__ == "__main__":
    main()
