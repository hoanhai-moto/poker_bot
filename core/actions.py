import time
import random
from typing import Optional

import pyautogui

from config import Settings


class ActionExecutor:
    """Executes mouse and keyboard actions for poker automation."""

    def __init__(self, settings: Settings):
        self._settings = settings
        # Safety settings for pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def _get_random_delay(self) -> float:
        """Get a random delay between min and max configured values."""
        min_delay = self._settings.min_delay_ms / 1000.0
        max_delay = self._settings.max_delay_ms / 1000.0
        return random.uniform(min_delay, max_delay)

    def _get_typing_delay(self) -> float:
        """Get the configured typing delay in seconds."""
        return self._settings.typing_delay_ms / 1000.0

    def click(self, x: int, y: int, delay: bool = True) -> None:
        """Click at the specified coordinates."""
        if delay:
            time.sleep(self._get_random_delay())

        # Add small random offset for more human-like behavior
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)

        pyautogui.click(x + offset_x, y + offset_y)

    def double_click(self, x: int, y: int, delay: bool = True) -> None:
        """Double-click at the specified coordinates."""
        if delay:
            time.sleep(self._get_random_delay())

        pyautogui.doubleClick(x, y)

    def type_text(self, text: str, delay: bool = True) -> None:
        """Type text with random delays between keystrokes."""
        if delay:
            time.sleep(self._get_random_delay() * 0.5)

        base_interval = self._get_typing_delay()
        for char in text:
            pyautogui.write(char, interval=0)
            # Random variation in typing speed
            time.sleep(base_interval * random.uniform(0.5, 1.5))

    def clear_field(self) -> None:
        """Select all text and delete it."""
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.press('delete')
        time.sleep(0.05)

    def press_key(self, key: str) -> None:
        """Press a single key."""
        pyautogui.press(key)

    def hotkey(self, *keys: str) -> None:
        """Press a key combination."""
        pyautogui.hotkey(*keys)

    # Poker-specific actions

    def perform_fold(self) -> bool:
        """Execute fold action."""
        pos = self._settings.get_button_position("fold")
        if pos == (0, 0):
            return False

        self.click(pos[0], pos[1])
        return True

    def perform_check(self) -> bool:
        """Execute check action."""
        pos = self._settings.get_button_position("check")
        if pos == (0, 0):
            return False

        self.click(pos[0], pos[1])
        return True

    def perform_call(self) -> bool:
        """Execute call action."""
        pos = self._settings.get_button_position("call")
        if pos == (0, 0):
            return False

        self.click(pos[0], pos[1])
        return True

    def perform_raise(self, amount: float) -> bool:
        """
        Execute raise action with specified amount.

        Steps:
        1. Click on bet input field
        2. Type new amount
        3. Click raise button
        """
        bet_input_pos = self._settings.get_button_position("bet_input")
        raise_pos = self._settings.get_button_position("raise")

        if bet_input_pos == (0, 0) or raise_pos == (0, 0):
            return False

        # Single click on bet input field
        self.click(bet_input_pos[0], bet_input_pos[1], delay=True)
        time.sleep(0.15)

        # Format the amount (remove trailing zeros)
        amount_str = f"{amount:.2f}".rstrip('0').rstrip('.')

        # Type the amount
        pyautogui.write(amount_str, interval=0.03)
        time.sleep(0.2)

        # Click raise button
        self.click(raise_pos[0], raise_pos[1], delay=True)
        return True

    def perform_action(self, action: str, amount: Optional[float] = None) -> bool:
        """
        Execute a poker action based on AI decision.

        Args:
            action: One of "fold", "check", "call", "raise"
            amount: Required for raise action, in BB or actual value

        Returns:
            True if action was executed successfully
        """
        action = action.lower()

        if action == "fold":
            return self.perform_fold()
        elif action == "check":
            return self.perform_check()
        elif action == "call":
            return self.perform_call()
        elif action == "raise" and amount is not None:
            return self.perform_raise(amount)
        else:
            return False

    def move_mouse_away(self) -> None:
        """Move mouse to a neutral position after action."""
        # Move to a corner of the screen
        screen_width, screen_height = pyautogui.size()
        pyautogui.moveTo(
            screen_width - 100 + random.randint(-20, 20),
            screen_height - 100 + random.randint(-20, 20),
            duration=0.3
        )
