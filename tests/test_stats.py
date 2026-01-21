"""Tests for poker statistics and player tracking."""

import unittest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from poker.player import Player, PlayerStats
from poker.game_state import GameState, Street, Action
from poker.stats_calculator import StatsCalculator
from poker.hand_history import HandRecord, HandHistory


class TestPlayerStats(unittest.TestCase):
    """Test player statistics model."""

    def test_stats_defaults(self):
        """Test default stat values."""
        stats = PlayerStats()

        self.assertEqual(stats.hands, 0)
        self.assertEqual(stats.vpip, 0.0)
        self.assertEqual(stats.pfr, 0.0)

    def test_stats_to_dict(self):
        """Test converting stats to dictionary."""
        stats = PlayerStats(hands=100, vpip=25.5, pfr=20.0)
        d = stats.to_dict()

        self.assertEqual(d["hands"], 100)
        self.assertEqual(d["vpip"], 25.5)
        self.assertEqual(d["pfr"], 20.0)

    def test_stats_from_dict(self):
        """Test creating stats from dictionary."""
        d = {"hands": 50, "vpip": 30.0, "pfr": 22.5}
        stats = PlayerStats.from_dict(d)

        self.assertEqual(stats.hands, 50)
        self.assertEqual(stats.vpip, 30.0)


class TestPlayer(unittest.TestCase):
    """Test player model."""

    def test_player_creation(self):
        """Test creating a player."""
        player = Player(name="TestPlayer", seat=3, stack=100.0)

        self.assertEqual(player.name, "TestPlayer")
        self.assertEqual(player.seat, 3)
        self.assertEqual(player.stack, 100.0)

    def test_player_type_classification(self):
        """Test player type classification."""
        # TAG player
        tag = Player(name="TAG")
        tag.stats = PlayerStats(hands=50, vpip=22.0, af=3.0)
        self.assertEqual(tag.get_player_type(), "TAG (Tight Aggressive)")

        # LAG player
        lag = Player(name="LAG")
        lag.stats = PlayerStats(hands=50, vpip=35.0, af=3.0)
        self.assertEqual(lag.get_player_type(), "LAG (Loose Aggressive)")

        # Unknown (not enough hands)
        unknown = Player(name="New")
        unknown.stats = PlayerStats(hands=5, vpip=30.0, af=2.0)
        self.assertEqual(unknown.get_player_type(), "Unknown")

    def test_player_to_dict(self):
        """Test converting player to dictionary."""
        player = Player(name="Test", seat=1, stack=50.0)
        d = player.to_dict()

        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["seat"], 1)
        self.assertIn("stats", d)


class TestGameState(unittest.TestCase):
    """Test game state model."""

    def test_game_state_defaults(self):
        """Test default game state."""
        state = GameState()

        self.assertEqual(state.street, Street.PREFLOP)
        self.assertEqual(state.pot_size, 0.0)
        self.assertEqual(state.hero_cards, [])

    def test_advance_street(self):
        """Test advancing to next street."""
        state = GameState()

        state.advance_street()
        self.assertEqual(state.street, Street.FLOP)

        state.advance_street()
        self.assertEqual(state.street, Street.TURN)

        state.advance_street()
        self.assertEqual(state.street, Street.RIVER)

        # Should stay on river
        state.advance_street()
        self.assertEqual(state.street, Street.RIVER)

    def test_add_action(self):
        """Test adding actions to history."""
        state = GameState()

        state.add_action("Player1", "raise", 10.0)
        state.add_action("Player2", "call", 10.0)

        self.assertEqual(len(state.actions), 2)
        self.assertEqual(state.actions[0].player, "Player1")
        self.assertEqual(state.actions[0].action_type, "raise")

    def test_pot_odds_calculation(self):
        """Test pot odds calculation."""
        state = GameState()
        state.pot_size = 10.0
        state.current_bet = 5.0
        state.hero_invested = 0.0

        # Call 5 into pot of 15 = 33.3%
        expected = (5 / 15) * 100
        self.assertAlmostEqual(state.pot_odds, expected, places=1)

    def test_spr_calculation(self):
        """Test SPR calculation."""
        state = GameState()
        state.hero_stack = 100.0
        state.pot_size = 20.0

        self.assertEqual(state.spr, 5.0)

    def test_game_state_reset(self):
        """Test resetting game state."""
        state = GameState()
        state.hero_cards = ["Ah", "Kh"]
        state.board = ["Qh", "Jh", "Th"]
        state.pot_size = 50.0

        state.reset()

        self.assertEqual(state.hero_cards, [])
        self.assertEqual(state.board, [])
        self.assertEqual(state.pot_size, 0.0)


class TestHandHistory(unittest.TestCase):
    """Test hand history tracking."""

    def test_hand_record_creation(self):
        """Test creating a hand record."""
        hand = HandRecord(
            hero_cards=["Ah", "Kh"],
            board=["Qh", "Jh", "Th"],
            hero_position="BTN",
            result_bb=15.5
        )

        self.assertEqual(hand.hero_cards, ["Ah", "Kh"])
        self.assertEqual(hand.result_bb, 15.5)

    def test_add_action_to_hand(self):
        """Test adding actions to hand record."""
        hand = HandRecord()

        hand.add_action("Hero", "raise", 10.0, "preflop")
        hand.add_action("Villain", "call", 10.0, "preflop")

        self.assertEqual(len(hand.actions), 2)

    def test_hand_history_tracking(self):
        """Test hand history management."""
        history = HandHistory()

        # Start and end a hand
        hand = history.start_new_hand()
        hand.hero_cards = ["Ah", "Kh"]
        history.end_hand(result_bb=10.0)

        self.assertEqual(history.get_hands_count(), 1)
        self.assertEqual(history.get_total_profit_bb(), 10.0)

    def test_recent_hands(self):
        """Test getting recent hands."""
        history = HandHistory()

        for i in range(15):
            hand = history.start_new_hand()
            history.end_hand(result_bb=float(i))

        recent = history.get_recent_hands(5)
        self.assertEqual(len(recent), 5)

    def test_hand_summaries_for_ai(self):
        """Test getting hand summaries for AI context."""
        history = HandHistory()

        hand = history.start_new_hand()
        hand.hero_cards = ["Ah", "Kh"]
        hand.hero_position = "BTN"
        history.end_hand(result_bb=5.0)

        summaries = history.get_summaries_for_ai()
        self.assertEqual(len(summaries), 1)
        self.assertIn("hero_cards", summaries[0])


class TestStatsCalculator(unittest.TestCase):
    """Test statistics calculation."""

    def test_empty_hands(self):
        """Test calculating stats with no hands."""
        calc = StatsCalculator()
        stats = calc.calculate_stats("Player1", [])

        self.assertEqual(stats.hands, 0)
        self.assertEqual(stats.vpip, 0.0)

    def test_vpip_calculation(self):
        """Test VPIP calculation."""
        calc = StatsCalculator()

        hands = [
            HandRecord(
                players=["Hero", "Villain"],
                actions=[
                    {"player": "Hero", "action_type": "call", "street": "preflop"}
                ]
            ),
            HandRecord(
                players=["Hero", "Villain"],
                actions=[
                    {"player": "Hero", "action_type": "fold", "street": "preflop"}
                ]
            )
        ]

        stats = calc.calculate_stats("Hero", hands)

        # 1 voluntary action out of 2 hands = 50%
        self.assertEqual(stats.vpip, 50.0)

    def test_pfr_calculation(self):
        """Test PFR calculation."""
        calc = StatsCalculator()

        hands = [
            HandRecord(
                players=["Hero"],
                actions=[
                    {"player": "Hero", "action_type": "raise", "street": "preflop"}
                ]
            ),
            HandRecord(
                players=["Hero"],
                actions=[
                    {"player": "Hero", "action_type": "call", "street": "preflop"}
                ]
            ),
            HandRecord(
                players=["Hero"],
                actions=[
                    {"player": "Hero", "action_type": "fold", "street": "preflop"}
                ]
            )
        ]

        stats = calc.calculate_stats("Hero", hands)

        # 1 raise out of 3 hands = 33.3%
        self.assertAlmostEqual(stats.pfr, 33.3, places=1)


if __name__ == "__main__":
    unittest.main()
