import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import Optional, List
import re


@dataclass
class WindowInfo:
    """Information about a window."""
    handle: int
    title: str
    x: int
    y: int
    width: int
    height: int

    @property
    def rect(self) -> tuple[int, int, int, int]:
        """Return (left, top, right, bottom) rectangle."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)


class WindowManager:
    """Manages window detection and tracking for GGPoker."""

    def __init__(self):
        self._user32 = ctypes.windll.user32
        self._current_window: Optional[WindowInfo] = None

    def enumerate_windows(self) -> List[WindowInfo]:
        """Get list of all visible windows with titles."""
        windows = []

        def enum_callback(hwnd, _):
            if self._user32.IsWindowVisible(hwnd):
                length = self._user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    self._user32.GetWindowTextW(hwnd, buffer, length + 1)
                    title = buffer.value

                    rect = wintypes.RECT()
                    self._user32.GetWindowRect(hwnd, ctypes.byref(rect))

                    windows.append(WindowInfo(
                        handle=hwnd,
                        title=title,
                        x=rect.left,
                        y=rect.top,
                        width=rect.right - rect.left,
                        height=rect.bottom - rect.top
                    ))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )
        self._user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

        return windows

    def find_window_by_title(self, pattern: str) -> Optional[WindowInfo]:
        """Find a window whose title matches the given pattern."""
        windows = self.enumerate_windows()
        # Escape special regex characters for exact matching
        escaped_pattern = re.escape(pattern)
        regex = re.compile(escaped_pattern, re.IGNORECASE)

        for window in windows:
            if regex.search(window.title):
                return window
        return None

    def find_ggpoker_window(self) -> Optional[WindowInfo]:
        """Find the GGPoker window."""
        return self.find_window_by_title("GGPoker")

    def get_window_titles(self) -> List[str]:
        """Get list of all visible window titles."""
        return [w.title for w in self.enumerate_windows() if w.title.strip()]

    def set_current_window(self, window: WindowInfo) -> None:
        """Set the current window to track."""
        self._current_window = window

    @property
    def current_window(self) -> Optional[WindowInfo]:
        """Get the currently tracked window."""
        return self._current_window

    def refresh_current_window(self) -> bool:
        """Refresh the current window's position and size."""
        if not self._current_window:
            return False

        rect = wintypes.RECT()
        result = self._user32.GetWindowRect(
            self._current_window.handle, ctypes.byref(rect)
        )

        if result:
            self._current_window.x = rect.left
            self._current_window.y = rect.top
            self._current_window.width = rect.right - rect.left
            self._current_window.height = rect.bottom - rect.top
            return True
        return False

    def is_window_valid(self) -> bool:
        """Check if the current window handle is still valid."""
        if not self._current_window:
            return False
        return bool(self._user32.IsWindow(self._current_window.handle))

    def bring_to_front(self) -> bool:
        """Bring the current window to the foreground using multiple techniques."""
        if not self._current_window:
            return False

        hwnd = self._current_window.handle

        # Constants
        SW_RESTORE = 9
        SW_SHOW = 5

        # Get current foreground window's thread
        foreground_hwnd = self._user32.GetForegroundWindow()
        foreground_thread = self._user32.GetWindowThreadProcessId(foreground_hwnd, None)
        current_thread = self._user32.GetWindowThreadProcessId(hwnd, None)

        # Attach threads to allow SetForegroundWindow
        if foreground_thread != current_thread:
            self._user32.AttachThreadInput(foreground_thread, current_thread, True)

        # Restore if minimized
        self._user32.ShowWindow(hwnd, SW_RESTORE)

        # Multiple methods to bring to front
        self._user32.BringWindowToTop(hwnd)
        self._user32.SetForegroundWindow(hwnd)
        self._user32.SetActiveWindow(hwnd)

        # Detach threads
        if foreground_thread != current_thread:
            self._user32.AttachThreadInput(foreground_thread, current_thread, False)

        return True
