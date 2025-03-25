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
from xbanner_bdf import font, msg  # now importing msg instead of get_glyph_matrix

intr = 0

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
    stdscr.nodelay(1)   # Non-blocking input
    stdscr.timeout(1000)  # Refresh every second

    disable_intr()  # Temporarily disable Ctrl+C handling

    try:
        # Load the font from the specified BDF file
        fnt = font()
        with open(font_path) as fd:
            for line in fd:
                fnt.handle_line(line.rstrip())

        last_display = None
        while True:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            # Use msg() to render the time with full block glyphs
            rendered = msg(fnt, current_time)
            glyph_matrix = rendered.splitlines()

            # Determine screen dimensions and centre the output
            scr_height, scr_width = stdscr.getmaxyx()
            matrix_height = len(glyph_matrix)
            matrix_width = len(glyph_matrix[0]) if matrix_height > 0 else 0
            start_y = (scr_height - matrix_height) // 2
            start_x = (scr_width - matrix_width) // 2

            if last_display is None:
                last_display = [[' '] * scr_width for _ in range(scr_height)]

            # Update only cells that have changed
            for i, row in enumerate(glyph_matrix):
                for j, char in enumerate(row):
                    sy, sx = i + start_y, j + start_x
                    if sy < scr_height and sx < scr_width and last_display[sy][sx] != char:
                        stdscr.addch(sy, sx, char)
                        last_display[sy][sx] = char

            stdscr.refresh()
            key = stdscr.getch()
            if key == 3:  # ASCII 3 = Ctrl+C
                break  # Exit on Ctrl+C
    finally:
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

