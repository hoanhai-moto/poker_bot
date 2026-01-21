import random
import time
from typing import Tuple


def random_delay(
    min_ms: int = 1000,
    max_ms: int = 3000,
    execute: bool = True
) -> float:
    """
    Generate and optionally execute a random delay.

    Args:
        min_ms: Minimum delay in milliseconds
        max_ms: Maximum delay in milliseconds
        execute: If True, actually sleep for the delay

    Returns:
        The delay time in seconds
    """
    delay_ms = random.randint(min_ms, max_ms)
    delay_sec = delay_ms / 1000.0

    if execute:
        time.sleep(delay_sec)

    return delay_sec


def humanize_delay(base_ms: int, variance_pct: float = 0.3) -> float:
    """
    Add human-like variance to a base delay.

    Args:
        base_ms: Base delay in milliseconds
        variance_pct: Percentage variance (0.3 = +/- 30%)

    Returns:
        Delay time in seconds
    """
    variance = base_ms * variance_pct
    delay_ms = base_ms + random.uniform(-variance, variance)
    return max(0, delay_ms / 1000.0)


def get_typing_delays(
    text_length: int,
    base_delay_ms: int = 50,
    variance_pct: float = 0.5
) -> list:
    """
    Generate a list of delays for typing simulation.

    Args:
        text_length: Number of characters
        base_delay_ms: Base delay between keystrokes
        variance_pct: Variance percentage

    Returns:
        List of delay times in seconds
    """
    delays = []
    for _ in range(text_length):
        delay = humanize_delay(base_delay_ms, variance_pct)
        delays.append(delay)
    return delays


def random_pause(
    min_sec: float = 0.5,
    max_sec: float = 2.0
) -> None:
    """
    Execute a random pause between actions.

    Args:
        min_sec: Minimum pause in seconds
        max_sec: Maximum pause in seconds
    """
    time.sleep(random.uniform(min_sec, max_sec))


def thinking_delay(
    complexity: str = "medium"
) -> None:
    """
    Simulate human thinking time based on decision complexity.

    Args:
        complexity: One of "easy", "medium", "hard"
    """
    delays = {
        "easy": (500, 1500),
        "medium": (1000, 3000),
        "hard": (2000, 5000)
    }

    min_ms, max_ms = delays.get(complexity, delays["medium"])
    random_delay(min_ms, max_ms)


class RateLimiter:
    """Simple rate limiter for actions."""

    def __init__(self, min_interval_ms: int = 1000):
        self._min_interval = min_interval_ms / 1000.0
        self._last_action_time = 0.0

    def wait_if_needed(self) -> float:
        """
        Wait if necessary to maintain minimum interval between actions.

        Returns:
            Time waited in seconds
        """
        current_time = time.time()
        elapsed = current_time - self._last_action_time
        wait_time = max(0, self._min_interval - elapsed)

        if wait_time > 0:
            time.sleep(wait_time)

        self._last_action_time = time.time()
        return wait_time

    def reset(self):
        """Reset the rate limiter."""
        self._last_action_time = 0.0
