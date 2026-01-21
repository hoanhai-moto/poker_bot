from typing import Dict, List, Optional
from .player import Player, PlayerStats
from .hand_history import HandRecord


class StatsCalculator:
    """Calculates player statistics from hand history."""

    # Weight decay for recent hands (recent hands count more)
    DECAY_FACTOR = 0.98

    def __init__(self):
        self._player_cache: Dict[str, PlayerStats] = {}

    def calculate_stats(self, player_name: str, hands: List[HandRecord]) -> PlayerStats:
        """
        Calculate stats for a player from hand records.

        Args:
            player_name: Name of the player
            hands: List of hand records involving this player

        Returns:
            Calculated PlayerStats
        """
        stats = PlayerStats()

        if not hands:
            return stats

        # Filter hands where player was involved
        player_hands = [h for h in hands if player_name in h.players]
        stats.hands = len(player_hands)

        if stats.hands == 0:
            return stats

        # Calculate each stat
        stats.vpip = self._calculate_vpip(player_name, player_hands)
        stats.pfr = self._calculate_pfr(player_name, player_hands)
        stats.three_bet = self._calculate_3bet(player_name, player_hands)
        stats.fold_to_3bet = self._calculate_fold_to_3bet(player_name, player_hands)
        stats.af = self._calculate_af(player_name, player_hands)
        stats.wtsd = self._calculate_wtsd(player_name, player_hands)
        stats.wssd = self._calculate_wssd(player_name, player_hands)
        stats.cbet = self._calculate_cbet(player_name, player_hands)

        return stats

    def _calculate_vpip(self, player: str, hands: List[HandRecord]) -> float:
        """Calculate Voluntarily Put $ In Pot percentage."""
        opportunities = 0
        voluntarily_put_in = 0

        for hand in hands:
            # Player had opportunity to play
            opportunities += 1

            # Check if player voluntarily put money in (not blind)
            for action in hand.actions:
                if action.get("player") == player:
                    action_type = action.get("action_type", "").lower()
                    street = action.get("street", "preflop")

                    if street == "preflop" and action_type in ["call", "raise", "bet"]:
                        voluntarily_put_in += 1
                        break

        if opportunities == 0:
            return 0.0
        return (voluntarily_put_in / opportunities) * 100

    def _calculate_pfr(self, player: str, hands: List[HandRecord]) -> float:
        """Calculate Pre-Flop Raise percentage."""
        opportunities = 0
        pfr_count = 0

        for hand in hands:
            opportunities += 1

            for action in hand.actions:
                if action.get("player") == player:
                    action_type = action.get("action_type", "").lower()
                    street = action.get("street", "preflop")

                    if street == "preflop" and action_type == "raise":
                        pfr_count += 1
                        break

        if opportunities == 0:
            return 0.0
        return (pfr_count / opportunities) * 100

    def _calculate_3bet(self, player: str, hands: List[HandRecord]) -> float:
        """Calculate 3-bet frequency."""
        opportunities = 0
        three_bet_count = 0

        for hand in hands:
            # Check if there was a raise before player's action
            raise_seen = False
            player_acted = False

            for action in hand.actions:
                if action.get("street") != "preflop":
                    break

                if action.get("action_type", "").lower() == "raise":
                    if action.get("player") != player:
                        raise_seen = True
                    elif raise_seen and not player_acted:
                        # This is a 3-bet
                        opportunities += 1
                        three_bet_count += 1
                        player_acted = True
                        break

                if action.get("player") == player:
                    if raise_seen and not player_acted:
                        opportunities += 1
                    player_acted = True

        if opportunities == 0:
            return 0.0
        return (three_bet_count / opportunities) * 100

    def _calculate_fold_to_3bet(self, player: str, hands: List[HandRecord]) -> float:
        """Calculate fold to 3-bet percentage."""
        opportunities = 0
        fold_count = 0

        for hand in hands:
            player_raised = False
            faced_3bet = False

            for action in hand.actions:
                if action.get("street") != "preflop":
                    break

                if action.get("player") == player:
                    if action.get("action_type", "").lower() == "raise" and not player_raised:
                        player_raised = True
                    elif faced_3bet:
                        opportunities += 1
                        if action.get("action_type", "").lower() == "fold":
                            fold_count += 1
                        break

                elif player_raised and action.get("action_type", "").lower() == "raise":
                    faced_3bet = True

        if opportunities == 0:
            return 0.0
        return (fold_count / opportunities) * 100

    def _calculate_af(self, player: str, hands: List[HandRecord]) -> float:
        """Calculate Aggression Factor (bets+raises / calls)."""
        bets_raises = 0
        calls = 0

        for hand in hands:
            for action in hand.actions:
                if action.get("player") == player:
                    action_type = action.get("action_type", "").lower()
                    if action_type in ["bet", "raise"]:
                        bets_raises += 1
                    elif action_type == "call":
                        calls += 1

        if calls == 0:
            return bets_raises if bets_raises > 0 else 0.0
        return bets_raises / calls

    def _calculate_wtsd(self, player: str, hands: List[HandRecord]) -> float:
        """Calculate Went To Showdown percentage."""
        saw_flop = 0
        went_to_showdown = 0

        for hand in hands:
            # Check if player saw flop
            player_saw_flop = False
            for action in hand.actions:
                if action.get("player") == player and action.get("street") == "flop":
                    player_saw_flop = True
                    break

            if player_saw_flop:
                saw_flop += 1
                if hand.went_to_showdown and player in hand.players:
                    went_to_showdown += 1

        if saw_flop == 0:
            return 0.0
        return (went_to_showdown / saw_flop) * 100

    def _calculate_wssd(self, player: str, hands: List[HandRecord]) -> float:
        """Calculate Won $ at Showdown percentage."""
        showdowns = 0
        wins = 0

        for hand in hands:
            if hand.went_to_showdown and player in hand.players:
                showdowns += 1
                if hand.winner == player:
                    wins += 1

        if showdowns == 0:
            return 0.0
        return (wins / showdowns) * 100

    def _calculate_cbet(self, player: str, hands: List[HandRecord]) -> float:
        """Calculate Continuation Bet frequency."""
        opportunities = 0
        cbet_count = 0

        for hand in hands:
            # Check if player was preflop aggressor
            was_aggressor = False
            for action in hand.actions:
                if action.get("street") != "preflop":
                    break
                if action.get("player") == player and action.get("action_type", "").lower() == "raise":
                    was_aggressor = True

            if not was_aggressor:
                continue

            # Check flop action
            for action in hand.actions:
                if action.get("street") == "flop" and action.get("player") == player:
                    opportunities += 1
                    if action.get("action_type", "").lower() in ["bet", "raise"]:
                        cbet_count += 1
                    break

        if opportunities == 0:
            return 0.0
        return (cbet_count / opportunities) * 100

    def update_player_stats(self, player: Player, hands: List[HandRecord]) -> None:
        """Update a player's stats in place."""
        new_stats = self.calculate_stats(player.name, hands)
        player.update_stats(new_stats)

    def get_stats_dict(self, player_name: str, hands: List[HandRecord]) -> Dict[str, float]:
        """Get stats as a dictionary for AI context."""
        stats = self.calculate_stats(player_name, hands)
        return stats.to_dict()
