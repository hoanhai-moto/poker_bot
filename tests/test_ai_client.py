"""Tests for AI client and response parsing."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.response_parser import ResponseParser, PokerDecision
from ai.prompt_builder import PromptBuilder


class TestResponseParser(unittest.TestCase):
    """Test response parsing functionality."""

    def setUp(self):
        self.parser = ResponseParser()

    def test_parse_valid_fold_response(self):
        """Test parsing a valid fold response."""
        response = '''
        {
            "action": "fold",
            "amount": null,
            "reasoning": "Weak hand out of position",
            "confidence": 0.85,
            "detected_cards": {
                "hole_cards": ["7h", "2s"],
                "board": ["Ah", "Kd", "Qc"]
            },
            "pot_size": 15.5,
            "position": "UTG",
            "street": "flop"
        }
        '''

        decision = self.parser.parse_response(response)

        self.assertTrue(decision.is_valid)
        self.assertEqual(decision.action, "fold")
        self.assertIsNone(decision.amount)
        self.assertEqual(decision.confidence, 0.85)
        self.assertEqual(decision.position, "UTG")
        self.assertEqual(decision.street, "flop")

    def test_parse_valid_raise_response(self):
        """Test parsing a valid raise response."""
        response = '''
        {
            "action": "raise",
            "amount": 15.0,
            "reasoning": "Strong hand, building pot",
            "confidence": 0.92,
            "detected_cards": {
                "hole_cards": ["Ah", "Ad"],
                "board": []
            },
            "pot_size": 3.5,
            "position": "BTN",
            "street": "preflop"
        }
        '''

        decision = self.parser.parse_response(response)

        self.assertTrue(decision.is_valid)
        self.assertEqual(decision.action, "raise")
        self.assertEqual(decision.amount, 15.0)
        self.assertEqual(decision.confidence, 0.92)

    def test_parse_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = '''
        Here's my analysis:

        ```json
        {
            "action": "call",
            "amount": null,
            "reasoning": "Good pot odds",
            "confidence": 0.75,
            "detected_cards": {"hole_cards": ["Kh", "Qh"], "board": []},
            "pot_size": 10,
            "position": "BB",
            "street": "preflop"
        }
        ```
        '''

        decision = self.parser.parse_response(response)

        self.assertTrue(decision.is_valid)
        self.assertEqual(decision.action, "call")

    def test_parse_invalid_action(self):
        """Test handling of invalid action."""
        response = '''
        {
            "action": "all_in",
            "amount": 100,
            "reasoning": "YOLO",
            "confidence": 0.5
        }
        '''

        decision = self.parser.parse_response(response)

        self.assertFalse(decision.is_valid)

    def test_parse_no_json(self):
        """Test handling of response without JSON."""
        response = "I think you should fold because the hand is weak."

        decision = self.parser.parse_response(response)

        self.assertFalse(decision.is_valid)

    def test_validate_decision_warnings(self):
        """Test decision validation warnings."""
        # Raise without amount
        decision = PokerDecision(action="raise", amount=None, confidence=0.8)
        warnings = self.parser.validate_decision(decision)
        self.assertIn("Raise action without amount specified", warnings)

        # Low confidence
        decision = PokerDecision(action="fold", confidence=0.2)
        warnings = self.parser.validate_decision(decision)
        self.assertTrue(any("Low confidence" in w for w in warnings))


class TestPromptBuilder(unittest.TestCase):
    """Test prompt building functionality."""

    def setUp(self):
        self.builder = PromptBuilder()

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        system_prompt = self.builder.get_system_prompt()
        self.assertIsInstance(system_prompt, str)
        self.assertGreater(len(system_prompt), 100)

    def test_build_basic_prompt(self):
        """Test building a basic prompt."""
        prompt = self.builder.build_analysis_prompt()
        self.assertIn("Analyze", prompt)
        self.assertIn("JSON", prompt)

    def test_build_prompt_with_stats(self):
        """Test building prompt with player stats."""
        player_stats = {
            "Villain1": {
                "hands": 50,
                "vpip": 28.5,
                "pfr": 22.0,
                "three_bet": 8.5,
                "fold_to_3bet": 65.0,
                "af": 2.5,
                "wtsd": 25.0,
                "wssd": 55.0,
                "cbet": 70.0
            }
        }

        prompt = self.builder.build_analysis_prompt(player_stats=player_stats)

        self.assertIn("Villain1", prompt)
        self.assertIn("VPIP", prompt)
        self.assertIn("28.5", prompt)

    def test_build_prompt_with_history(self):
        """Test building prompt with hand history."""
        hand_history = [
            {
                "hero_cards": "Ah Kd",
                "board": "Qh Jh Tc",
                "position": "BTN",
                "result_bb": 15.5,
                "action_summary": "Hero raises, Villain calls"
            }
        ]

        prompt = self.builder.build_analysis_prompt(hand_history=hand_history)

        self.assertIn("Recent Hand History", prompt)
        self.assertIn("Ah Kd", prompt)


class TestPokerDecision(unittest.TestCase):
    """Test PokerDecision data class."""

    def test_decision_to_dict(self):
        """Test converting decision to dictionary."""
        decision = PokerDecision(
            action="raise",
            amount=10.5,
            reasoning="Strong hand",
            confidence=0.9,
            position="BTN",
            street="flop"
        )

        d = decision.to_dict()

        self.assertEqual(d["action"], "raise")
        self.assertEqual(d["amount"], 10.5)
        self.assertEqual(d["confidence"], 0.9)

    def test_decision_defaults(self):
        """Test decision default values."""
        decision = PokerDecision(action="fold")

        self.assertIsNone(decision.amount)
        self.assertEqual(decision.reasoning, "")
        self.assertEqual(decision.confidence, 0.0)
        self.assertTrue(decision.is_valid)


if __name__ == "__main__":
    unittest.main()
