#!/usr/bin/python3
import os
import sys
import time
import datetime
import argparse
import locale
import numpy as np
import curses
import termios
import tty
from xbanner_bdf import font, get_glyph_matrix

intr=0

def disable_intr():
    """Temporarily disable Ctrl+C as an interrupt signal using termios."""
    global intr
    fd = sys.stdin.fileno()
    attr = termios.tcgetattr(fd)
    intr = attr[6][termios.VINTR]
    attr[6][termios.VINTR] = 0  # Disable INTR character (Ctrl+C)
    termios.tcsetattr(fd, termios.TCSANOW, attr)

def restore_intr():
    """Restore Ctrl+C as an interrupt signal using termios."""
    global intr
    fd = sys.stdin.fileno()
    attr = termios.tcgetattr(fd)
    attr[6][termios.VINTR] = b'\x03'  # Restore INTR character (Ctrl+C)
    termios.tcsetattr(fd, termios.TCSANOW, attr)

def draw_clock(stdscr, font_path):
    global intr
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)  # Non-blocking input
    stdscr.timeout(1000)  # Refresh every second

    disable_intr()  # Temporarily disable Ctrl+C handling

    try:
        # Load the font
        fnt = font()
        with open(font_path) as fd:
            for line in fd:
                fnt.handle_line(line.rstrip())

        last_display = None
        while True:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            glyph_matrix = get_glyph_matrix(fnt, current_time)

            # Get screen size
            height, width = stdscr.getmaxyx()
            start_y = (height - len(glyph_matrix)) // 2
            start_x = (width - len(glyph_matrix[0])) // 2

            if last_display is None:
                last_display = [[' '] * width for _ in range(height)]

            # Only update changed characters
            for i, row in enumerate(glyph_matrix):
                for j, char in enumerate(row):
                    if i + start_y < height and j + start_x < width:
                        if last_display[i][j] != char:
                            stdscr.addch(i + start_y, j + start_x, char)
                            last_display[i][j] = char

            stdscr.refresh()
            key = stdscr.getch()
            if key == 3:  # ASCII 3 = Ctrl+C
                break  # Exit on Ctrl+C
    finally:
        # Ensure terminal cleanup before exiting
        restore_intr()  # Restore Ctrl+C before exiting
        stdscr.clear()
        stdscr.refresh()
        time.sleep(0.1)  # Allow screen refresh before exiting

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", '-f', required=True, help="Path to BDF font file")
    args = parser.parse_args()

    curses.wrapper(draw_clock, args.font)

if __name__ == "__main__":
    main()
