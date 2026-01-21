from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


@dataclass
class PlayerStats:
    """Statistics for a poker player."""

    # Core stats
    hands: int = 0
    vpip: float = 0.0  # Voluntarily Put $ In Pot %
    pfr: float = 0.0   # Pre-Flop Raise %
    three_bet: float = 0.0  # 3-bet frequency
    fold_to_3bet: float = 0.0  # Fold to 3-bet %
    af: float = 0.0    # Aggression Factor
    wtsd: float = 0.0  # Went To Showdown %
    wssd: float = 0.0  # Won $ at Showdown %
    cbet: float = 0.0  # Continuation bet %

    # Tracking counters for calculation
    vpip_opportunities: int = 0
    vpip_count: int = 0
    pfr_opportunities: int = 0
    pfr_count: int = 0
    three_bet_opportunities: int = 0
    three_bet_count: int = 0
    fold_to_3bet_opportunities: int = 0
    fold_to_3bet_count: int = 0
    bets_raises: int = 0
    calls: int = 0
    showdown_opportunities: int = 0
    showdown_count: int = 0
    showdown_wins: int = 0
    cbet_opportunities: int = 0
    cbet_count: int = 0

    # Positional stats
    stats_by_position: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for display/storage."""
        return {
            "hands": self.hands,
            "vpip": self.vpip,
            "pfr": self.pfr,
            "three_bet": self.three_bet,
            "fold_to_3bet": self.fold_to_3bet,
            "af": self.af,
            "wtsd": self.wtsd,
            "wssd": self.wssd,
            "cbet": self.cbet
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PlayerStats":
        """Create from dictionary."""
        stats = cls()
        for key, value in data.items():
            if hasattr(stats, key):
                setattr(stats, key, value)
        return stats


@dataclass
class Player:
    """Represents a player at the poker table."""

    name: str
    seat: int = 0
    stack: float = 0.0
    is_hero: bool = False
    position: Optional[str] = None
    stats: PlayerStats = field(default_factory=PlayerStats)
    last_updated: Optional[datetime] = None
    notes: str = ""

    def update_stats(self, new_stats: PlayerStats) -> None:
        """Update player stats."""
        self.stats = new_stats
        self.last_updated = datetime.now()

    def get_stat(self, stat_name: str) -> float:
        """Get a specific stat value."""
        return getattr(self.stats, stat_name, 0.0)

    def is_tight(self) -> bool:
        """Check if player plays tight (low VPIP)."""
        return self.stats.vpip < 20 and self.stats.hands >= 20

    def is_loose(self) -> bool:
        """Check if player plays loose (high VPIP)."""
        return self.stats.vpip > 35 and self.stats.hands >= 20

    def is_aggressive(self) -> bool:
        """Check if player is aggressive (high AF)."""
        return self.stats.af > 2.5 and self.stats.hands >= 20

    def is_passive(self) -> bool:
        """Check if player is passive (low AF)."""
        return self.stats.af < 1.5 and self.stats.hands >= 20

    def get_player_type(self) -> str:
        """Categorize player based on stats."""
        if self.stats.hands < 20:
            return "Unknown"

        tight = self.stats.vpip < 25
        aggressive = self.stats.af > 2.0

        if tight and aggressive:
            return "TAG (Tight Aggressive)"
        elif tight and not aggressive:
            return "TP (Tight Passive)"
        elif not tight and aggressive:
            return "LAG (Loose Aggressive)"
        else:
            return "LP (Loose Passive)"

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "seat": self.seat,
            "stack": self.stack,
            "is_hero": self.is_hero,
            "position": self.position,
            "stats": self.stats.to_dict(),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Player":
        """Create player from dictionary."""
        stats = PlayerStats.from_dict(data.get("stats", {}))
        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])

        return cls(
            name=data["name"],
            seat=data.get("seat", 0),
            stack=data.get("stack", 0.0),
            is_hero=data.get("is_hero", False),
            position=data.get("position"),
            stats=stats,
            last_updated=last_updated,
            notes=data.get("notes", "")
        )
