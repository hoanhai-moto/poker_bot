from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class Street(Enum):
    """Poker streets/rounds."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class Position(Enum):
    """Standard poker positions."""
    UTG = "UTG"
    UTG1 = "UTG+1"
    UTG2 = "UTG+2"
    MP = "MP"
    MP1 = "MP+1"
    HJ = "HJ"  # Hijack
    CO = "CO"  # Cutoff
    BTN = "BTN"  # Button
    SB = "SB"   # Small Blind
    BB = "BB"   # Big Blind


@dataclass
class Action:
    """Represents a single poker action."""
    player: str
    action_type: str  # fold, check, call, bet, raise
    amount: Optional[float] = None
    street: Street = Street.PREFLOP
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "player": self.player,
            "action_type": self.action_type,
            "amount": self.amount,
            "street": self.street.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class GameState:
    """Current state of a poker hand."""

    # Hand identification
    hand_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    # Cards
    hero_cards: List[str] = field(default_factory=list)
    board: List[str] = field(default_factory=list)

    # Betting info
    pot_size: float = 0.0
    current_bet: float = 0.0
    street: Street = Street.PREFLOP

    # Blinds
    small_blind: float = 0.0
    big_blind: float = 0.0

    # Players
    hero_position: Optional[str] = None
    hero_stack: float = 0.0
    players: Dict[str, Dict] = field(default_factory=dict)  # name -> {stack, position, is_active}

    # Action history for current hand
    actions: List[Action] = field(default_factory=list)

    # Tracking
    hero_invested: float = 0.0
    is_hero_turn: bool = False

    @property
    def effective_stack(self) -> float:
        """Get the effective stack (smallest stack in hand in BB)."""
        if not self.big_blind:
            return 0.0
        stacks = [p["stack"] for p in self.players.values() if p.get("is_active")]
        if not stacks:
            return self.hero_stack / self.big_blind if self.big_blind else 0.0
        return min(min(stacks), self.hero_stack) / self.big_blind

    @property
    def pot_odds(self) -> float:
        """Calculate pot odds as percentage."""
        if self.current_bet <= 0:
            return 0.0
        call_amount = self.current_bet - self.hero_invested
        if call_amount <= 0:
            return 100.0
        return (call_amount / (self.pot_size + call_amount)) * 100

    @property
    def spr(self) -> float:
        """Stack to pot ratio."""
        if self.pot_size <= 0:
            return float('inf')
        return self.hero_stack / self.pot_size

    def add_action(self, player: str, action_type: str, amount: Optional[float] = None) -> None:
        """Add an action to the history."""
        self.actions.append(Action(
            player=player,
            action_type=action_type,
            amount=amount,
            street=self.street,
            timestamp=datetime.now()
        ))

    def advance_street(self) -> None:
        """Move to the next street."""
        street_order = [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]
        current_idx = street_order.index(self.street)
        if current_idx < len(street_order) - 1:
            self.street = street_order[current_idx + 1]
            self.current_bet = 0.0

    def get_actions_for_street(self, street: Street) -> List[Action]:
        """Get all actions for a specific street."""
        return [a for a in self.actions if a.street == street]

    def get_action_summary(self) -> str:
        """Get a brief summary of the action."""
        summary_parts = []

        for street in Street:
            street_actions = self.get_actions_for_street(street)
            if street_actions:
                action_str = ", ".join(
                    f"{a.player}: {a.action_type}" +
                    (f" {a.amount}" if a.amount else "")
                    for a in street_actions
                )
                summary_parts.append(f"{street.value}: {action_str}")

        return " | ".join(summary_parts)

    def reset(self) -> None:
        """Reset for a new hand."""
        self.hand_id = None
        self.hero_cards = []
        self.board = []
        self.pot_size = 0.0
        self.current_bet = 0.0
        self.street = Street.PREFLOP
        self.actions = []
        self.hero_invested = 0.0
        self.is_hero_turn = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "hand_id": self.hand_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "hero_cards": self.hero_cards,
            "board": self.board,
            "pot_size": self.pot_size,
            "current_bet": self.current_bet,
            "street": self.street.value,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "hero_position": self.hero_position,
            "hero_stack": self.hero_stack,
            "players": self.players,
            "actions": [a.to_dict() for a in self.actions],
            "hero_invested": self.hero_invested
        }

    def to_context_dict(self) -> Dict:
        """Convert to context dict for AI prompt."""
        return {
            "blinds": f"{self.small_blind}/{self.big_blind}",
            "hero_stack": self.hero_stack / self.big_blind if self.big_blind else 0,
            "table_type": f"{len(self.players)}-handed",
            "notes": f"SPR: {self.spr:.1f}, Pot Odds: {self.pot_odds:.1f}%"
        }
