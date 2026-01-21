from typing import Dict, List, Optional


class PromptBuilder:
    """Builds prompts for Claude poker analysis."""

    SYSTEM_PROMPT = """You are an expert poker player and analyst. Your task is to analyze poker game screenshots and recommend optimal actions based on game theory optimal (GTO) principles while also exploiting opponent tendencies when profitable.

You will receive:
1. A screenshot of the current poker game state
2. Statistics about opponents at the table
3. Recent hand history for context

Analyze the image carefully to identify:
- Your hole cards
- Community cards (if any)
- Current pot size
- Your stack size and position
- Opponent stack sizes
- Current action (bet amounts, who has acted)
- What street we're on (preflop, flop, turn, river)

Always respond with a valid JSON object containing your decision and reasoning."""

    RESPONSE_FORMAT = """
Respond ONLY with a JSON object in this exact format:
{
    "action": "fold" | "check" | "call" | "raise",
    "amount": <number or null>,
    "reasoning": "<detailed explanation of your decision>",
    "confidence": <0.0 to 1.0>,
    "detected_cards": {
        "hole_cards": ["card1", "card2"],
        "board": ["card1", "card2", ...]
    },
    "pot_size": <number>,
    "position": "<position name>",
    "street": "preflop" | "flop" | "turn" | "river"
}

Notes:
- For "action": use exactly one of: fold, check, call, raise
- For "amount": provide a number only for raise actions (in same units as displayed), null otherwise
- For "confidence": 1.0 = very confident, 0.5 = uncertain, 0.0 = guessing
- Card format: use standard notation (e.g., "Ah" for Ace of hearts, "Td" for Ten of diamonds)
"""

    def get_system_prompt(self) -> str:
        """Get the system prompt for Claude."""
        return self.SYSTEM_PROMPT

    def build_analysis_prompt(
        self,
        player_stats: Optional[Dict[str, Dict]] = None,
        hand_history: Optional[List[Dict]] = None,
        game_context: Optional[Dict] = None
    ) -> str:
        """
        Build the complete analysis prompt.

        Args:
            player_stats: Dict mapping player names to their stats
            hand_history: List of recent hand dictionaries
            game_context: Additional context like stack sizes, blinds
        """
        parts = ["Analyze this poker screenshot and recommend the optimal action."]

        # Add player stats if available
        if player_stats:
            parts.append(self._format_player_stats(player_stats))

        # Add hand history if available
        if hand_history:
            parts.append(self._format_hand_history(hand_history))

        # Add game context if available
        if game_context:
            parts.append(self._format_game_context(game_context))

        # Add response format instructions
        parts.append(self.RESPONSE_FORMAT)

        return "\n\n".join(parts)

    def _format_player_stats(self, player_stats: Dict[str, Dict]) -> str:
        """Format player statistics as a markdown table."""
        if not player_stats:
            return ""

        lines = ["## Opponent Statistics", ""]
        lines.append("| Player | Hands | VPIP | PFR | 3-Bet | Fold to 3-Bet | AF | WTSD | W$SD | C-Bet |")
        lines.append("|--------|-------|------|-----|-------|---------------|-----|------|------|-------|")

        for name, stats in player_stats.items():
            lines.append(
                f"| {name} | "
                f"{stats.get('hands', 0)} | "
                f"{stats.get('vpip', 0):.1f}% | "
                f"{stats.get('pfr', 0):.1f}% | "
                f"{stats.get('three_bet', 0):.1f}% | "
                f"{stats.get('fold_to_3bet', 0):.1f}% | "
                f"{stats.get('af', 0):.1f} | "
                f"{stats.get('wtsd', 0):.1f}% | "
                f"{stats.get('wssd', 0):.1f}% | "
                f"{stats.get('cbet', 0):.1f}% |"
            )

        lines.append("")
        lines.append("**Stat Explanations:**")
        lines.append("- VPIP: Voluntarily Put $ In Pot %")
        lines.append("- PFR: Pre-Flop Raise %")
        lines.append("- 3-Bet: 3-bet frequency")
        lines.append("- AF: Aggression Factor (bets+raises / calls)")
        lines.append("- WTSD: Went To Showdown %")
        lines.append("- W$SD: Won $ at Showdown %")
        lines.append("- C-Bet: Continuation bet frequency")

        return "\n".join(lines)

    def _format_hand_history(self, hand_history: List[Dict]) -> str:
        """Format recent hand history."""
        if not hand_history:
            return ""

        lines = ["## Recent Hand History", ""]

        for i, hand in enumerate(hand_history[-5:], 1):  # Last 5 hands
            lines.append(f"**Hand {i}:**")

            if "hero_cards" in hand:
                lines.append(f"- Hero cards: {hand['hero_cards']}")
            if "board" in hand:
                lines.append(f"- Board: {hand['board']}")
            if "position" in hand:
                lines.append(f"- Position: {hand['position']}")
            if "result_bb" in hand:
                result = hand['result_bb']
                result_str = f"+{result}" if result > 0 else str(result)
                lines.append(f"- Result: {result_str} BB")
            if "action_summary" in hand:
                lines.append(f"- Actions: {hand['action_summary']}")

            lines.append("")

        return "\n".join(lines)

    def _format_game_context(self, game_context: Dict) -> str:
        """Format additional game context."""
        if not game_context:
            return ""

        lines = ["## Game Context", ""]

        if "blinds" in game_context:
            lines.append(f"- Blinds: {game_context['blinds']}")
        if "hero_stack" in game_context:
            lines.append(f"- Hero stack: {game_context['hero_stack']} BB")
        if "table_type" in game_context:
            lines.append(f"- Table: {game_context['table_type']}")
        if "notes" in game_context:
            lines.append(f"- Notes: {game_context['notes']}")

        return "\n".join(lines)
