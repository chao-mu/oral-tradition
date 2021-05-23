#!/usr/bin/env python3

# Core
import queue
import time
import sys
import glob
import os
import random

# UI
import pygame
from pygame.locals import *

pygame.init()

font = pygame.font.SysFont(None, 48)
background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))

screen = pygame.display.set_mode((800, 600))

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
PINK = (255,20,147)

def main():
    path = sys.argv[1]

    clock = pygame.time.Clock()

    pygame.display.set_caption('last word')

    is_running = True

    lines = load_file(path)
    game = Game(lines)
    state = Menu(game)

    play_idx = 0
    while is_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYUP and event.key == K_q:
                is_running = False
            elif event.type == pygame.KEYDOWN and event.key == K_1:
                state.btn_a()
            elif event.type == pygame.KEYDOWN and event.key == K_2:
                state.btn_b()
            elif event.type == pygame.KEYDOWN and event.key == K_UP:
                state.btn_up()
            elif event.type == pygame.KEYDOWN and event.key == K_DOWN:
                state.btn_down()
            elif event.type == pygame.KEYDOWN and event.key == K_LEFT:
                state.btn_left()
            elif event.type == pygame.KEYDOWN and event.key == K_RIGHT:
                state.btn_right()

        state = state.next_state
        state.tick()

        pygame.display.update()
        clock.tick(30)


class Game:

    def __init__(self, lines):
        self.points = 0
        self.lines = lines
        self.word_pool = list(set([word.lower() for line in lines for word in line]))

class State:

    def __init__(self, game):
        self.game = game
        self.next_state = self

    def btn_a(self):
        pass

    def btn_b(self):
        pass

    def btn_left(self):
        pass

    def btn_right(self):
        pass

    def btn_up(self):
        self.back_line()
        self.refresh()

    def btn_down(self):
        self.next_line()
        self.refresh()

    def next_line(self):
        self.lines.next()
        self.current_line.goto(0)

    def back_line(self):
        self.lines.back()
        self.current_line.goto(0)

    def refresh(self):
        pass

    @property
    def lines(self):
        return self.game.lines

    @property
    def current_line(self):
        return self.game.lines.current

    @property
    def current_word(self):
        return self.current_line.current

class Menu(State):

    def btn_right(self):
        self.next_state = GuessNext(self.game)

    def tick(self):
        screen.blit(background, (0, 0))

        text_rect = Rect((20, 20), (800, 800))
        draw_text(screen, self.lines.current.join(), GRAY, text_rect, font)

class Initialisms(State):

    def btn_left(self):
        self.next_state = GuessNext(self.game)

    def btn_right(self):
        self.next_state = Blank(self.game)

    def tick(self):
        screen.blit(background, (0, 0))

        text_rect = Rect((20, 20), (800, 800))
        draw_text(screen, self.initials, RED, text_rect, font)

    @property
    def initials(self):
        return " ".join([word[0] for word in self.current_line])

class Blank(State):

    def __init__(self, game, last_shown=0):
        super().__init__(game)

        self.last_shown = last_shown

    def btn_left(self):
        self.next_state = Initialisms(self.game)

    def btn_a(self):
        self.last_shown = min(self.last_shown + 1, len(self.current_line))

    def btn_b(self):
        self.last_shown = 0

    def refresh(self):
        self.last_shown = 0

    def tick(self):
        screen.blit(background, (0, 0))

        initials = [word[0] for word in self.current_line]
        initials = initials[0:self.last_shown]
        initials = " ".join(initials)

        text_rect = Rect((20, 20), (800, 800))
        draw_text(screen, initials, RED, text_rect, font)

class GuessNext(State):

    def __init__(self, game):
        super().__init__(game)

        self.option_a = None
        self.option_b = None
        self.winning = None

        self.current_line.goto(0)
        self.refresh()


    def btn_a(self):
        self.guess(self.option_a)

    def btn_b(self):
        self.guess(self.option_b)

    def btn_left(self):
        if self.current_line.idx > 0:
            self.next_state = GuessNext(self.game)
        else:
            self.next_state = Menu(self.game)

    def btn_right(self):
        self.next_state = Initialisms(self.game)

    def refresh(self):
        options = [random.choice(self.game.word_pool), self.current_line.peek_next]
        random.shuffle(options)
        self.option_a, self.option_b = options
        self.choice = None

    def guess(self, choice):
        if choice == self.current_line.peek_next:
            if self.winning:
                self.game.points += 10
            self.current_line.next()
            self.winning = True
        else:
            self.winning = False

        self.refresh()

    def tick(self):
        screen.blit(background, (0, 0))

        if self.current_line.peek_next is None:
            render_text("Finished!", GRAY, (20, 20))
        else:
            render_text(self.current_word, RED, (20, 20))
            render_text(self.option_a, GREEN, (20, 80))
            render_text(self.option_b, BLUE, (20, 120))

        status_pos = [20, 300]
        status_pos[0] += render_text(str(self.game.points), PINK, (status_pos)).get_width()
        if self.winning is not None:
            status_pos[0] += 20
            render_text(":-)" if self.winning else ":-(", PINK, status_pos)

def render_text(text, color, pos):
    surface = font.render(text, True, color)
    screen.blit(surface, pos)

    return surface

def load_file(path):
    lines = []
    with open(path) as f:
        lines = f.readlines()

    lines = [l.strip() for l in lines]
    lines = [CursorList(l.split()) for l in lines if len(l) > 0]

    return CursorList(lines)

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


# copy and pasted from https://www.pygame.org/wiki/TextWrap
# draw some text into an area of a surface
# automatically wraps words
# returns any text that didn't get blitted
def draw_text(surface, text, color, rect, font, aa=False, bkg=None):
    rect = Rect(rect)
    y = rect.top
    lineSpacing = -2

    # get the height of the font
    fontHeight = font.size("Tg")[1]

    while text:
        i = 1

        # determine if the row of text will be outside our area
        if y + fontHeight > rect.bottom:
            break

        # determine maximum width of line
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1

        # if we've wrapped the text, then adjust the wrap to the last word
        if i < len(text):
            i = text.rfind(" ", 0, i) + 1

        # render the line and blit it to the surface
        if bkg:
            image = font.render(text[:i], 1, color, bkg)
            image.set_colorkey(bkg)
        else:
            image = font.render(text[:i], aa, color)

        surface.blit(image, (rect.left, y))
        y += fontHeight + lineSpacing

        # remove the text we just blitted
        text = text[i:]

    return text

if __name__ == "__main__":
    main()
