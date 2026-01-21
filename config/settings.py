import json
import os
from pathlib import Path
from typing import Any, Optional


class Settings:
    """Application configuration management."""

    DEFAULT_CONFIG_PATH = Path(__file__).parent / "default_config.json"
    USER_CONFIG_PATH = Path(__file__).parent.parent / "user_config.json"

    def __init__(self, config_path: Optional[Path] = None):
        self._config: dict = {}
        self._config_path = config_path or self.USER_CONFIG_PATH
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from files."""
        # Load defaults first
        with open(self.DEFAULT_CONFIG_PATH, 'r') as f:
            self._config = json.load(f)

        # Override with user config if exists
        if self._config_path.exists():
            with open(self._config_path, 'r') as f:
                user_config = json.load(f)
                self._deep_update(self._config, user_config)

    def _deep_update(self, base: dict, updates: dict) -> None:
        """Recursively update nested dictionary."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def save(self) -> None:
        """Save current configuration to user config file."""
        with open(self._config_path, 'w') as f:
            json.dump(self._config, f, indent=2)

    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated keys."""
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys: str, value: Any) -> None:
        """Set a configuration value by dot-separated keys."""
        if not keys:
            return

        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value

    # Window settings
    @property
    def window_title_pattern(self) -> str:
        return self.get("window", "title_pattern", default="GGPoker")

    @property
    def capture_region(self) -> Optional[dict]:
        return self.get("window", "capture_region")

    # Button positions
    @property
    def buttons(self) -> dict:
        return self.get("buttons", default={})

    def get_button_position(self, button_name: str) -> tuple[int, int]:
        """Get button coordinates."""
        btn = self.get("buttons", button_name, default={"x": 0, "y": 0})
        return (btn["x"], btn["y"])

    def set_button_position(self, button_name: str, x: int, y: int) -> None:
        """Set button coordinates."""
        self.set("buttons", button_name, value={"x": x, "y": y})

    # Hotkey settings
    @property
    def hotkeys(self) -> dict:
        return self.get("hotkeys", default={})

    def get_hotkey(self, action: str) -> str:
        return self.get("hotkeys", action, default="")

    # Timing settings
    @property
    def min_delay_ms(self) -> int:
        return self.get("timing", "min_delay_ms", default=1000)

    @property
    def max_delay_ms(self) -> int:
        return self.get("timing", "max_delay_ms", default=3000)

    @property
    def typing_delay_ms(self) -> int:
        return self.get("timing", "typing_delay_ms", default=50)

    # AI settings
    @property
    def api_key(self) -> str:
        # First check for direct API key in config
        direct_key = self.get("ai", "api_key", default="")
        if direct_key:
            return direct_key
        # Fall back to environment variable
        env_var = self.get("ai", "api_key_env", default="ANTHROPIC_API_KEY")
        return os.environ.get(env_var, "")

    @property
    def ai_model(self) -> str:
        return self.get("ai", "model", default="claude-sonnet-4-20250514")

    @property
    def max_tokens(self) -> int:
        return self.get("ai", "max_tokens", default=1024)

    # Data settings
    @property
    def sessions_dir(self) -> Path:
        return Path(self.get("data", "sessions_dir", default="./data/sessions"))

    @property
    def stats_file(self) -> Path:
        return Path(self.get("data", "stats_file", default="./data/player_stats.csv"))
