import csv
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


class CSVHandler:
    """Handles reading and writing CSV files for poker data."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base_dir = base_dir or Path("./data")
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        (self._base_dir / "sessions").mkdir(exist_ok=True)

    # Player Stats CSV Operations

    def save_player_stats(self, stats: Dict[str, Dict], filepath: Optional[Path] = None) -> None:
        """
        Save player statistics to CSV.

        Args:
            stats: Dict mapping player names to their stats dicts
            filepath: Path to save to (default: data/player_stats.csv)
        """
        filepath = filepath or self._base_dir / "player_stats.csv"

        fieldnames = [
            "player_name", "hands", "vpip", "pfr", "three_bet",
            "fold_to_3bet", "af", "wtsd", "wssd", "cbet", "last_updated"
        ]

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for player_name, player_stats in stats.items():
                row = {"player_name": player_name}
                row.update(player_stats)
                row["last_updated"] = datetime.now().isoformat()
                writer.writerow(row)

    def load_player_stats(self, filepath: Optional[Path] = None) -> Dict[str, Dict]:
        """
        Load player statistics from CSV.

        Returns:
            Dict mapping player names to their stats
        """
        filepath = filepath or self._base_dir / "player_stats.csv"

        if not filepath.exists():
            return {}

        stats = {}
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                player_name = row.pop("player_name")
                # Convert numeric fields
                for key in ["hands", "vpip", "pfr", "three_bet", "fold_to_3bet", "af", "wtsd", "wssd", "cbet"]:
                    if key in row:
                        try:
                            row[key] = float(row[key]) if '.' in str(row[key]) else int(row[key])
                        except (ValueError, TypeError):
                            row[key] = 0
                stats[player_name] = row

        return stats

    # Hand History CSV Operations

    def save_hands(self, hands: List[Dict], filepath: Path) -> None:
        """
        Save hand records to CSV.

        Args:
            hands: List of hand dictionaries
            filepath: Path to save to
        """
        if not hands:
            return

        fieldnames = [
            "hand_id", "session_id", "timestamp", "hero_cards", "board",
            "hero_position", "action_sequence", "result_bb",
            "ai_action", "ai_reasoning", "ai_confidence"
        ]

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for hand in hands:
                row = {
                    "hand_id": hand.get("hand_id", ""),
                    "session_id": hand.get("session_id", ""),
                    "timestamp": hand.get("timestamp", ""),
                    "hero_cards": " ".join(hand.get("hero_cards", [])),
                    "board": " ".join(hand.get("board", [])),
                    "hero_position": hand.get("hero_position", ""),
                    "action_sequence": json.dumps(hand.get("actions", [])),
                    "result_bb": hand.get("result_bb", 0),
                    "ai_action": hand.get("ai_action", ""),
                    "ai_reasoning": hand.get("ai_reasoning", ""),
                    "ai_confidence": hand.get("ai_confidence", "")
                }
                writer.writerow(row)

    def load_hands(self, filepath: Path) -> List[Dict]:
        """Load hand records from CSV."""
        if not filepath.exists():
            return []

        hands = []
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hand = {
                    "hand_id": row.get("hand_id", ""),
                    "session_id": row.get("session_id", ""),
                    "timestamp": row.get("timestamp", ""),
                    "hero_cards": row.get("hero_cards", "").split() if row.get("hero_cards") else [],
                    "board": row.get("board", "").split() if row.get("board") else [],
                    "hero_position": row.get("hero_position", ""),
                    "result_bb": float(row.get("result_bb", 0)),
                    "ai_action": row.get("ai_action", ""),
                    "ai_reasoning": row.get("ai_reasoning", ""),
                    "ai_confidence": float(row.get("ai_confidence")) if row.get("ai_confidence") else None
                }

                # Parse action sequence
                try:
                    hand["actions"] = json.loads(row.get("action_sequence", "[]"))
                except json.JSONDecodeError:
                    hand["actions"] = []

                hands.append(hand)

        return hands

    # Session CSV Operations

    def save_sessions(self, sessions: List[Dict], filepath: Optional[Path] = None) -> None:
        """Save session records to CSV."""
        filepath = filepath or self._base_dir / "sessions.csv"

        fieldnames = [
            "session_id", "start_time", "end_time",
            "hands_played", "profit_bb", "notes"
        ]

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for session in sessions:
                writer.writerow(session)

    def load_sessions(self, filepath: Optional[Path] = None) -> List[Dict]:
        """Load session records from CSV."""
        filepath = filepath or self._base_dir / "sessions.csv"

        if not filepath.exists():
            return []

        sessions = []
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["hands_played"] = int(row.get("hands_played", 0))
                row["profit_bb"] = float(row.get("profit_bb", 0))
                sessions.append(row)

        return sessions

    # Action Log CSV Operations

    def append_action_log(
        self,
        action: Dict,
        filepath: Optional[Path] = None
    ) -> None:
        """Append a single action to the action log."""
        filepath = filepath or self._base_dir / "action_log.csv"

        fieldnames = [
            "timestamp", "hand_id", "player", "action",
            "amount", "street", "pot_size"
        ]

        file_exists = filepath.exists()

        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(action)

    def load_action_log(self, filepath: Optional[Path] = None) -> List[Dict]:
        """Load action log from CSV."""
        filepath = filepath or self._base_dir / "action_log.csv"

        if not filepath.exists():
            return []

        actions = []
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("amount"):
                    row["amount"] = float(row["amount"])
                if row.get("pot_size"):
                    row["pot_size"] = float(row["pot_size"])
                actions.append(row)

        return actions

    # Utility Methods

    def get_session_hands_path(self, session_id: str) -> Path:
        """Get the path for a session's hands file."""
        return self._base_dir / "sessions" / f"{session_id}_hands.csv"

    def export_to_json(self, data: Any, filepath: Path) -> None:
        """Export data to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def import_from_json(self, filepath: Path) -> Any:
        """Import data from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
