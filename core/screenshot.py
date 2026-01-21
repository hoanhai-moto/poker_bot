import base64
import io
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple

import mss
from PIL import Image

from .window_manager import WindowInfo


class ScreenshotCapture:
    """Captures screenshots of windows and regions. Thread-safe implementation."""

    def __init__(self):
        # Windows API setup for direct window capture
        self._user32 = ctypes.windll.user32
        self._gdi32 = ctypes.windll.gdi32

    def capture_window(self, window: WindowInfo) -> Image.Image:
        """Capture a screenshot of the specified window using screen coordinates."""
        # Use mss to capture the screen region where the window is
        monitor = {
            "left": window.x,
            "top": window.y,
            "width": window.width,
            "height": window.height
        }
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    def _capture_window_by_handle(self, hwnd: int, width: int, height: int) -> Image.Image:
        """Capture window content directly by handle using PrintWindow API."""
        # Define BITMAPINFOHEADER structure
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ('biSize', ctypes.c_uint32),
                ('biWidth', ctypes.c_int32),
                ('biHeight', ctypes.c_int32),
                ('biPlanes', ctypes.c_uint16),
                ('biBitCount', ctypes.c_uint16),
                ('biCompression', ctypes.c_uint32),
                ('biSizeImage', ctypes.c_uint32),
                ('biXPelsPerMeter', ctypes.c_int32),
                ('biYPelsPerMeter', ctypes.c_int32),
                ('biClrUsed', ctypes.c_uint32),
                ('biClrImportant', ctypes.c_uint32),
            ]

        # Get window DC
        hwnd_dc = self._user32.GetWindowDC(hwnd)

        # Create compatible DC and bitmap
        mfc_dc = self._gdi32.CreateCompatibleDC(hwnd_dc)
        bitmap = self._gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
        self._gdi32.SelectObject(mfc_dc, bitmap)

        # Use PrintWindow to capture the window content (works even if window is behind others)
        # PW_RENDERFULLCONTENT = 2 for better capture on Windows 8.1+
        PW_RENDERFULLCONTENT = 2
        result = self._user32.PrintWindow(hwnd, mfc_dc, PW_RENDERFULLCONTENT)

        if not result:
            # Fallback: try without PW_RENDERFULLCONTENT
            self._user32.PrintWindow(hwnd, mfc_dc, 0)

        # Setup BITMAPINFOHEADER
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = width
        bmi.biHeight = -height  # Negative for top-down DIB
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0  # BI_RGB

        # Create buffer for pixel data
        buffer_size = width * height * 4
        buffer = ctypes.create_string_buffer(buffer_size)

        self._gdi32.GetDIBits(mfc_dc, bitmap, 0, height, buffer, ctypes.byref(bmi), 0)

        # Cleanup
        self._gdi32.DeleteObject(bitmap)
        self._gdi32.DeleteDC(mfc_dc)
        self._user32.ReleaseDC(hwnd, hwnd_dc)

        # Convert to PIL Image (BGRA format)
        image = Image.frombuffer("RGBA", (width, height), buffer.raw, "raw", "BGRA", 0, 1)
        return image.convert("RGB")

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> Image.Image:
        """Capture a screenshot of a specific screen region."""
        monitor = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    def capture_window_region(
        self,
        window: WindowInfo,
        rel_x: int,
        rel_y: int,
        width: int,
        height: int
    ) -> Image.Image:
        """Capture a region relative to a window's position."""
        return self.capture_region(
            window.x + rel_x,
            window.y + rel_y,
            width,
            height
        )

    @staticmethod
    def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
        """Convert a PIL Image to base64 encoded string."""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def capture_window_as_base64(
        self,
        window: WindowInfo,
        format: str = "PNG"
    ) -> str:
        """Capture window screenshot and return as base64."""
        image = self.capture_window(window)
        return self.image_to_base64(image, format)

    def capture_full_screen(self) -> Image.Image:
        """Capture the entire primary monitor."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    def save_screenshot(
        self,
        image: Image.Image,
        filepath: str,
        format: Optional[str] = None
    ) -> None:
        """Save a screenshot to file."""
        image.save(filepath, format=format)

    def get_image_dimensions(self, image: Image.Image) -> Tuple[int, int]:
        """Get image width and height."""
        return image.size

    def resize_image(
        self,
        image: Image.Image,
        max_width: int = 1920,
        max_height: int = 1080
    ) -> Image.Image:
        """Resize image if it exceeds max dimensions while maintaining aspect ratio."""
        width, height = image.size

        if width <= max_width and height <= max_height:
            return image

        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def close(self) -> None:
        """Clean up resources (no-op for thread-safe implementation)."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
