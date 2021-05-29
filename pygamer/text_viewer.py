import json
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
import os
import storage
import sdcardio

from adafruit_display_text.label import Label

SDCARD_PATH = "/sd"

spi = board.SPI()
cs = board.SD_CS

sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, SDCARD_PATH)

display = board.DISPLAY

joystick = analogjoy.AnalogJoystick()

up_key = repeat.KeyRepeat(lambda: joystick.up, rate=0.2)
down_key = repeat.KeyRepeat(lambda: joystick.down, rate=0.2)
left_key = repeat.KeyRepeat(lambda: joystick.left, rate=0.2)
right_key = repeat.KeyRepeat(lambda: joystick.right, rate=0.2)

def main():
    with open("/foundation.txt", "r") as f:
        lines = f.readlines()

    verses = make_pager(lines, max_width=26, max_height=7)

    data = Data.load(SDCARD_PATH + "/data.json")
    mode = TextReader(data, verses)
    data.save()

    while True:
        joystick.poll()

        if up_key.value:
            mode.btn_up()
        elif down_key.value:
            mode.btn_down()
        elif left_key.value:
            mode.btn_left()
        elif right_key.value:
            mode.btn_right()

        mode.show()

class Data:
    def __init__(self, path):
        self.path = path
        self.data = {}

    def store(self, caller, key, value):
        namespace = self.namespace(caller)

        self.data.setdefault(namespace, {})
        self.data[namespace][key] = value

        self.save()

    def get(self, caller, key, default=None):
        namespace = self.namespace(caller)

        self.data.setdefault(namespace, {})

        return self.data[namespace].get(key, default)

    def namespace(self, caller):
        return caller.__class__.__name__

    def load(path):
        data = Data(path)

        try:
            with open(path, "r") as f:
                j = f.read()
        except OSError as e:
            j = "{}"

        data.data = json.loads(j)

        return data

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f)

class Mode:

    def __init__(self, data):
        self.data = data
        self.next_state = self

    def btn_a(self):
        pass

    def btn_b(self):
        pass

    def btn_left(self):
        states.back()

    def btn_right(self):
        pass

    def btn_up(self):
        pass

    def btn_down(self):
        pass

class TextReader(Mode):
    STATE_ENUMS = [FULL, INITIALS, BLANK] = range(3)

    def __init__(self, data, verses):
        super().__init__(data)

        self.states = CursorList(self.STATE_ENUMS)
        self.verses = verses
        self.verses.goto(self.data.get(self, "verse", 0))

    def btn_left(self):
        self.states.back()

    def btn_right(self):
        self.states.next()

    def btn_up(self):
        self.verses.back()
        self.data.store(self, "verse", self.verses.idx)

    def btn_down(self):
        self.verses.next()
        self.data.store(self, "verse", self.verses.idx)

    def show(self):
        text = self.verses.current
        if self.states.current == self.FULL:
            pass
        elif self.states.current == self.INITIALS:
            initials = ""
            last_space = True
            for current in text:
                is_space = current in [" ", "\n"]
                if last_space or is_space:
                    initials += current

                last_space = is_space

            text = initials
        elif self.states.current == self.BLANK:
            text = " "

        main_group = displayio.Group(max_size=25)

        line = Label(terminalio.FONT, text=text, color=(255, 192, 203))
        line.y = 10
        main_group.append(line)

        display.show(main_group)

class Button:

    def __init__(self, pin):
        btn = digitalio.DigitalInOut(pin)
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.UP

        self.btn = btn
        self.prev_state = False
        self.cur_state = False

    def poll(self):
        self.cur_state = self.btn.value
        pressed = self.cur_state != self.prev_state

def make_pager(lines, max_width, max_height):
    lines = [line.strip() for line in lines]

    pages = []
    block = ""
    chunk = ""
    for line in lines:
        idx = 0
        space_chunk_idx = 0
        space_line_idx = 0

        if len(line) == 0:
            line = [" "]

        while idx < len(line):
            current = line[idx]
            idx += 1
            chunk += current
            if current == " ":
                space_chunk_idx = len(chunk) - 1
                space_line_idx = idx - 1

            # We exceeded our chunk limit, rewind
            if len(chunk) > max_width:
                block += chunk[:space_chunk_idx] + "\n"
                chunk = ""
                idx = space_line_idx

            if block.count("\n") >= max_height:
                pages.append(block)
                block = ""

        if chunk != "":
            block += chunk + "\n"
            chunk = ""

    if block != "":
        pages.append(block)

    return CursorList(pages)

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
