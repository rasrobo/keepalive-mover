#!/usr/bin/env python3
"""
keepalive-mover - Prevent Discord and other apps from marking status as idle/away.
Moves mouse slightly after configurable idle threshold.
"""

import argparse
import signal
import sys
import time
import subprocess
import logging
from threading import Thread, Event
from pynput import mouse, keyboard

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except (ImportError, SystemExit):
    PYAUTOGUI_AVAILABLE = False

try:
    import Xlib.display
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False


class KeepAliveMover:
    def __init__(self, interval=45, idle_threshold=120, pixels=1, verbose=False):
        self.interval = interval
        self.idle_threshold = idle_threshold
        self.pixels = pixels
        self.verbose = verbose
        self.last_activity = time.time()
        self.running = True
        self.stop_event = Event()
        self.mouse_listener = None
        self.keyboard_listener = None

        self._setup_logging()
        self._setup_listeners()

    def _setup_logging(self):
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def _setup_listeners(self):
        self.mouse_listener = mouse.Listener(
            on_move=self._on_activity,
            on_click=self._on_activity,
            on_scroll=self._on_activity
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_activity,
            on_release=self._on_activity
        )
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def _on_activity(self, *args, **kwargs):
        self.last_activity = time.time()

    def _get_mouse_position(self):
        try:
            return pyautogui.position()
        except Exception:
            try:
                display = Xlib.display.Display()
                screen = display.screen()
                root = screen.root
                pointer = root.query_pointer()
                return (pointer.root_x, pointer.root_y)
            except Exception:
                return None

    def _move_mouse_pyautogui(self, x, y):
        try:
            pyautogui.moveRel(self.pixels, 0, duration=0.1)
            pyautogui.moveRel(-self.pixels, 0, duration=0.1)
            return True
        except Exception as e:
            if self.verbose:
                self.logger.debug(f"pyautogui failed: {e}")
            return False

    def _move_mouse_xdotool(self, x, y):
        try:
            subprocess.run(
                ['xdotool', 'mousemove_relative', '--', str(self.pixels), '0'],
                check=True, capture_output=True
            )
            subprocess.run(
                ['xdotool', 'mousemove_relative', '--', str(-self.pixels), '0'],
                check=True, capture_output=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if self.verbose:
                self.logger.debug(f"xdotool failed: {e}")
            return False

    def _jiggle_mouse(self):
        pos = self._get_mouse_position()
        if pos is None:
            self.logger.warning("Could not get mouse position")
            return False

        x, y = pos
        if self.verbose:
            self.logger.debug(f"Current position: ({x}, {y})")

        if PYAUTOGUI_AVAILABLE:
            if self._move_mouse_pyautogui(x, y):
                return True

        self.logger.info("pyautogui unavailable/failed, trying xdotool")
        return self._move_mouse_xdotool(x, y)

    def _check_idle_and_jiggle(self):
        idle_time = time.time() - self.last_activity
        if idle_time >= self.idle_threshold:
            if self.verbose:
                self.logger.info(f"Idle for {idle_time:.0f}s, jiggling mouse")
            self._jiggle_mouse()
            self.last_activity = time.time()

    def run(self):
        self.logger.info(
            f"Starting keepalive-mover: interval={self.interval}s, "
            f"idle_threshold={self.idle_threshold}s, pixels={self.pixels}"
        )

        try:
            while self.running and not self.stop_event.is_set():
                self._check_idle_and_jiggle()
                self.stop_event.wait(self.interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        self.running = False
        self.stop_event.set()
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        self.logger.info("keepalive-mover stopped")


def signal_handler(signum, frame):
    raise KeyboardInterrupt()


def main():
    parser = argparse.ArgumentParser(
        description='Prevent Discord and other apps from marking status as idle/away'
    )
    parser.add_argument(
        '--interval', '-i', type=int, default=45,
        help='Check interval in seconds (default: 45)'
    )
    parser.add_argument(
        '--idle-threshold', '-t', type=int, default=120,
        help='Idle threshold in seconds before jiggling (default: 120)'
    )
    parser.add_argument(
        '--pixels', '-p', type=int, default=1,
        help='Pixels to move mouse (default: 1)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose logging'
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    mover = KeepAliveMover(
        interval=args.interval,
        idle_threshold=args.idle_threshold,
        pixels=args.pixels,
        verbose=args.verbose
    )
    mover.run()


if __name__ == '__main__':
    main()