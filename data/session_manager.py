from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
import uuid

from .csv_handler import CSVHandler
from poker.hand_history import HandHistory, HandRecord


@dataclass
class Session:
    """Represents a poker session."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    hands_played: int = 0
    profit_bb: float = 0.0
    notes: str = ""

    def duration_minutes(self) -> float:
        """Get session duration in minutes."""
        end = self.end_time or datetime.now()
        delta = end - self.start_time
        return delta.total_seconds() / 60

    def hands_per_hour(self) -> float:
        """Calculate hands per hour."""
        duration = self.duration_minutes()
        if duration < 1:
            return 0.0
        return (self.hands_played / duration) * 60

    def bb_per_100(self) -> float:
        """Calculate BB/100 hands."""
        if self.hands_played < 1:
            return 0.0
        return (self.profit_bb / self.hands_played) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "hands_played": self.hands_played,
            "profit_bb": self.profit_bb,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        """Create from dictionary."""
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())[:8]),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else datetime.now(),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            hands_played=int(data.get("hands_played", 0)),
            profit_bb=float(data.get("profit_bb", 0)),
            notes=data.get("notes", "")
        )


class SessionManager:
    """Manages poker sessions and their data."""

    def __init__(self, data_dir: Optional[Path] = None):
        self._data_dir = data_dir or Path("./data")
        self._csv_handler = CSVHandler(self._data_dir)
        self._current_session: Optional[Session] = None
        self._hand_history: Optional[HandHistory] = None
        self._sessions: List[Session] = []
        self._load_sessions()

    def _load_sessions(self) -> None:
        """Load previous sessions from CSV."""
        data = self._csv_handler.load_sessions()
        self._sessions = [Session.from_dict(d) for d in data]

    def _save_sessions(self) -> None:
        """Save sessions to CSV."""
        data = [s.to_dict() for s in self._sessions]
        self._csv_handler.save_sessions(data)

    def start_session(self, notes: str = "") -> Session:
        """Start a new session."""
        self._current_session = Session(notes=notes)
        self._hand_history = HandHistory()
        return self._current_session

    def end_session(self) -> Optional[Session]:
        """End the current session and save data."""
        if not self._current_session:
            return None

        session = self._current_session
        session.end_time = datetime.now()

        # Update session stats from hand history
        if self._hand_history:
            session.hands_played = self._hand_history.get_hands_count()
            session.profit_bb = self._hand_history.get_total_profit_bb()

            # Save hands to session-specific file
            hands_path = self._csv_handler.get_session_hands_path(session.session_id)
            self._csv_handler.save_hands(
                self._hand_history.to_list(),
                hands_path
            )

        # Add to sessions list and save
        self._sessions.append(session)
        self._save_sessions()

        self._current_session = None
        self._hand_history = None

        return session

    @property
    def current_session(self) -> Optional[Session]:
        """Get the current session."""
        return self._current_session

    @property
    def hand_history(self) -> Optional[HandHistory]:
        """Get the current session's hand history."""
        return self._hand_history

    def is_session_active(self) -> bool:
        """Check if a session is currently active."""
        return self._current_session is not None

    def get_all_sessions(self) -> List[Session]:
        """Get all historical sessions."""
        return self._sessions

    def get_recent_sessions(self, count: int = 10) -> List[Session]:
        """Get the most recent sessions."""
        return self._sessions[-count:] if self._sessions else []

    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get a session by its ID."""
        for session in self._sessions:
            if session.session_id == session_id:
                return session
        return None

    def load_session_hands(self, session_id: str) -> List[HandRecord]:
        """Load hands for a specific session."""
        hands_path = self._csv_handler.get_session_hands_path(session_id)
        data = self._csv_handler.load_hands(hands_path)
        return [HandRecord.from_dict(d) for d in data]

    def get_total_stats(self) -> Dict:
        """Get aggregate stats across all sessions."""
        if not self._sessions:
            return {
                "total_sessions": 0,
                "total_hands": 0,
                "total_profit_bb": 0.0,
                "total_hours": 0.0,
                "bb_per_100": 0.0,
                "hands_per_hour": 0.0
            }

        total_hands = sum(s.hands_played for s in self._sessions)
        total_profit = sum(s.profit_bb for s in self._sessions)
        total_minutes = sum(s.duration_minutes() for s in self._sessions)

        return {
            "total_sessions": len(self._sessions),
            "total_hands": total_hands,
            "total_profit_bb": total_profit,
            "total_hours": total_minutes / 60,
            "bb_per_100": (total_profit / total_hands * 100) if total_hands > 0 else 0,
            "hands_per_hour": (total_hands / (total_minutes / 60)) if total_minutes > 0 else 0
        }

    def record_hand_result(self, result_bb: float, winner: Optional[str] = None) -> None:
        """Record the result of the current hand."""
        if self._hand_history and self._hand_history.current_hand:
            self._hand_history.end_hand(result_bb, winner)

    def get_session_summary(self) -> Optional[Dict]:
        """Get summary of current session."""
        if not self._current_session:
            return None

        session = self._current_session
        return {
            "session_id": session.session_id,
            "duration_minutes": session.duration_minutes(),
            "hands_played": self._hand_history.get_hands_count() if self._hand_history else 0,
            "profit_bb": self._hand_history.get_total_profit_bb() if self._hand_history else 0,
            "bb_per_100": session.bb_per_100(),
            "hands_per_hour": session.hands_per_hour()
        }
