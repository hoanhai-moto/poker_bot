import os
import threading
from pathlib import Path
from typing import Optional, Dict
import winsound


class SoundManager:
    """Manages sound alerts for the poker bot."""

    # Default sound frequencies and durations (for beep sounds)
    SOUNDS = {
        "action_taken": (800, 100),      # Short high beep
        "your_turn": (600, 200),         # Medium beep
        "error": (300, 300),             # Low long beep
        "session_end": (500, 150),       # Medium short beep
        "warning": (400, 200),           # Low medium beep
        "success": (1000, 100),          # High short beep
    }

    def __init__(self, sound_dir: Optional[Path] = None, enabled: bool = True):
        self._sound_dir = sound_dir or Path("./sounds")
        self._enabled = enabled
        self._custom_sounds: Dict[str, Path] = {}
        self._load_custom_sounds()

    def _load_custom_sounds(self):
        """Load any custom WAV files from the sound directory."""
        if not self._sound_dir.exists():
            return

        for wav_file in self._sound_dir.glob("*.wav"):
            name = wav_file.stem
            self._custom_sounds[name] = wav_file

    def play(self, sound_name: str, blocking: bool = False):
        """
        Play a sound by name.

        Args:
            sound_name: Name of the sound to play
            blocking: If True, wait for sound to finish
        """
        if not self._enabled:
            return

        if blocking:
            self._play_sound(sound_name)
        else:
            # Play in background thread
            thread = threading.Thread(
                target=self._play_sound,
                args=(sound_name,),
                daemon=True
            )
            thread.start()

    def _play_sound(self, sound_name: str):
        """Internal method to play a sound."""
        try:
            # Check for custom WAV file first
            if sound_name in self._custom_sounds:
                wav_path = self._custom_sounds[sound_name]
                winsound.PlaySound(
                    str(wav_path),
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )
            # Fall back to beep
            elif sound_name in self.SOUNDS:
                freq, duration = self.SOUNDS[sound_name]
                winsound.Beep(freq, duration)
            else:
                # Unknown sound, play default beep
                winsound.Beep(500, 100)

        except Exception:
            pass  # Silently ignore sound errors

    def play_action_taken(self):
        """Play sound for action taken confirmation."""
        self.play("action_taken")

    def play_your_turn(self):
        """Play sound for your turn notification."""
        self.play("your_turn")

    def play_error(self):
        """Play error sound."""
        self.play("error")

    def play_session_end(self):
        """Play session end sound."""
        self.play("session_end")

    def play_warning(self):
        """Play warning sound."""
        self.play("warning")

    def play_success(self):
        """Play success sound."""
        self.play("success")

    def enable(self):
        """Enable sound alerts."""
        self._enabled = True

    def disable(self):
        """Disable sound alerts."""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if sounds are enabled."""
        return self._enabled

    def add_custom_sound(self, name: str, wav_path: Path):
        """Add a custom sound file."""
        if wav_path.exists() and wav_path.suffix.lower() == ".wav":
            self._custom_sounds[name] = wav_path

    def list_sounds(self) -> list:
        """List all available sound names."""
        return list(self.SOUNDS.keys()) + list(self._custom_sounds.keys())
