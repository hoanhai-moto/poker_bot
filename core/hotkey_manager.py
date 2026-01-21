from typing import Callable, Dict, Optional
from pynput import keyboard
import threading


class HotkeyManager:
    """Manages global hotkey registration and handling."""

    def __init__(self):
        self._callbacks: Dict[str, Callable] = {}
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self._emergency_stop_callback: Optional[Callable] = None

    def register_hotkey(self, key: str, callback: Callable) -> None:
        """
        Register a callback for a hotkey.

        Args:
            key: Key name (e.g., "f1", "f2", "escape")
            callback: Function to call when key is pressed
        """
        self._callbacks[key.lower()] = callback

    def unregister_hotkey(self, key: str) -> None:
        """Unregister a hotkey."""
        key_lower = key.lower()
        if key_lower in self._callbacks:
            del self._callbacks[key_lower]

    def set_emergency_stop(self, callback: Callable) -> None:
        """Set the emergency stop callback."""
        self._emergency_stop_callback = callback

    def _on_press(self, key) -> None:
        """Handle key press events."""
        try:
            # Handle regular keys
            if hasattr(key, 'char') and key.char:
                key_name = key.char.lower()
            # Handle special keys (F1, F2, etc.)
            elif hasattr(key, 'name'):
                key_name = key.name.lower()
            else:
                return

            # Check for emergency stop (escape key)
            if key_name == "esc" or key_name == "escape":
                if self._emergency_stop_callback:
                    self._emergency_stop_callback()
                if "escape" in self._callbacks:
                    self._callbacks["escape"]()
                return

            # Execute registered callback
            if key_name in self._callbacks:
                # Run callback in separate thread to not block listener
                threading.Thread(
                    target=self._callbacks[key_name],
                    daemon=True
                ).start()

        except Exception:
            pass  # Ignore errors in hotkey processing

    def start(self) -> None:
        """Start listening for hotkeys."""
        if self._running:
            return

        self._running = True
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None

    def is_running(self) -> bool:
        """Check if the hotkey listener is running."""
        return self._running

    def clear_all(self) -> None:
        """Clear all registered hotkeys."""
        self._callbacks.clear()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
