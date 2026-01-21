from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import uuid


@dataclass
class HandRecord:
    """Record of a completed poker hand."""

    hand_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Cards
    hero_cards: List[str] = field(default_factory=list)
    board: List[str] = field(default_factory=list)

    # Players and positions
    players: List[str] = field(default_factory=list)
    hero_position: Optional[str] = None

    # Blinds
    small_blind: float = 0.0
    big_blind: float = 0.0

    # Actions
    actions: List[Dict] = field(default_factory=list)

    # Result
    result_bb: float = 0.0  # Profit/loss in big blinds
    winner: Optional[str] = None
    went_to_showdown: bool = False

    # AI info
    ai_action: Optional[str] = None
    ai_reasoning: Optional[str] = None
    ai_confidence: Optional[float] = None

    def add_action(
        self,
        player: str,
        action_type: str,
        amount: Optional[float] = None,
        street: str = "preflop"
    ) -> None:
        """Add an action to the hand record."""
        self.actions.append({
            "player": player,
            "action_type": action_type,
            "amount": amount,
            "street": street,
            "timestamp": datetime.now().isoformat()
        })

    def get_action_sequence(self) -> str:
        """Get a string representation of the action sequence."""
        parts = []
        for action in self.actions:
            action_str = f"{action['player']}: {action['action_type']}"
            if action.get('amount'):
                action_str += f" {action['amount']}"
            parts.append(action_str)
        return " -> ".join(parts)

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "hand_id": self.hand_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "hero_cards": self.hero_cards,
            "board": self.board,
            "players": self.players,
            "hero_position": self.hero_position,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "actions": self.actions,
            "result_bb": self.result_bb,
            "winner": self.winner,
            "went_to_showdown": self.went_to_showdown,
            "ai_action": self.ai_action,
            "ai_reasoning": self.ai_reasoning,
            "ai_confidence": self.ai_confidence
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "HandRecord":
        """Create from dictionary."""
        return cls(
            hand_id=data.get("hand_id", str(uuid.uuid4())[:8]),
            session_id=data.get("session_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            hero_cards=data.get("hero_cards", []),
            board=data.get("board", []),
            players=data.get("players", []),
            hero_position=data.get("hero_position"),
            small_blind=data.get("small_blind", 0.0),
            big_blind=data.get("big_blind", 0.0),
            actions=data.get("actions", []),
            result_bb=data.get("result_bb", 0.0),
            winner=data.get("winner"),
            went_to_showdown=data.get("went_to_showdown", False),
            ai_action=data.get("ai_action"),
            ai_reasoning=data.get("ai_reasoning"),
            ai_confidence=data.get("ai_confidence")
        )

    def to_summary(self) -> Dict:
        """Get a summary for AI context."""
        return {
            "hero_cards": " ".join(self.hero_cards),
            "board": " ".join(self.board) if self.board else "No board",
            "position": self.hero_position,
            "result_bb": self.result_bb,
            "action_summary": self.get_action_sequence()[:100]  # Truncate if too long
        }


class HandHistory:
    """Manages hand history for a session."""

    def __init__(self, max_hands: int = 1000):
        self._hands: List[HandRecord] = []
        self._max_hands = max_hands
        self._current_hand: Optional[HandRecord] = None

    def start_new_hand(self, session_id: Optional[str] = None) -> HandRecord:
        """Start tracking a new hand."""
        self._current_hand = HandRecord(session_id=session_id)
        return self._current_hand

    def end_hand(self, result_bb: float = 0.0, winner: Optional[str] = None) -> None:
        """Finish the current hand and add to history."""
        if self._current_hand:
            self._current_hand.result_bb = result_bb
            self._current_hand.winner = winner
            self._hands.append(self._current_hand)

            # Trim old hands if exceeded max
            if len(self._hands) > self._max_hands:
                self._hands = self._hands[-self._max_hands:]

            self._current_hand = None

    @property
    def current_hand(self) -> Optional[HandRecord]:
        """Get the current hand being tracked."""
        return self._current_hand

    @property
    def hands(self) -> List[HandRecord]:
        """Get all completed hands."""
        return self._hands

    def get_recent_hands(self, count: int = 10) -> List[HandRecord]:
        """Get the most recent N hands."""
        return self._hands[-count:] if self._hands else []

    def get_hands_by_player(self, player_name: str) -> List[HandRecord]:
        """Get all hands involving a specific player."""
        return [h for h in self._hands if player_name in h.players]

    def get_total_profit_bb(self) -> float:
        """Get total profit in big blinds."""
        return sum(h.result_bb for h in self._hands)

    def get_hands_count(self) -> int:
        """Get total number of completed hands."""
        return len(self._hands)

    def get_summaries_for_ai(self, count: int = 5) -> List[Dict]:
        """Get hand summaries formatted for AI context."""
        recent = self.get_recent_hands(count)
        return [h.to_summary() for h in recent]

    def clear(self) -> None:
        """Clear all hand history."""
        self._hands.clear()
        self._current_hand = None

    def to_list(self) -> List[Dict]:
        """Convert all hands to list of dicts for storage."""
        return [h.to_dict() for h in self._hands]

    def load_from_list(self, data: List[Dict]) -> None:
        """Load hands from list of dicts."""
        self._hands = [HandRecord.from_dict(d) for d in data]
