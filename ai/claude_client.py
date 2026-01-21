from typing import Dict, List, Optional, Any
import anthropic

from config import Settings
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser, PokerDecision


class ClaudeClient:
    """Claude API integration for poker analysis."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = anthropic.Anthropic(api_key=settings.api_key)
        self._prompt_builder = PromptBuilder()
        self._response_parser = ResponseParser()

    def analyze_poker_screenshot(
        self,
        screenshot_base64: str,
        player_stats: Optional[Dict[str, Dict]] = None,
        hand_history: Optional[List[Dict]] = None,
        game_context: Optional[Dict] = None
    ) -> PokerDecision:
        """
        Analyze a poker screenshot and return the recommended action.

        Args:
            screenshot_base64: Base64 encoded screenshot image
            player_stats: Dictionary of player stats keyed by player name
            hand_history: List of recent hand summaries
            game_context: Additional context (stack sizes, blinds, etc.)

        Returns:
            PokerDecision object with action, amount, reasoning, etc.
        """
        # Build the prompt with all context
        prompt = self._prompt_builder.build_analysis_prompt(
            player_stats=player_stats,
            hand_history=hand_history,
            game_context=game_context
        )

        # Make the API call with vision
        message = self._client.messages.create(
            model=self._settings.ai_model,
            max_tokens=self._settings.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            system=self._prompt_builder.get_system_prompt()
        )

        # Extract the response text
        response_text = message.content[0].text

        # Parse and return the decision
        return self._response_parser.parse_response(response_text)

    def analyze_with_retry(
        self,
        screenshot_base64: str,
        player_stats: Optional[Dict[str, Dict]] = None,
        hand_history: Optional[List[Dict]] = None,
        game_context: Optional[Dict] = None,
        max_retries: int = 2
    ) -> PokerDecision:
        """
        Analyze with automatic retry on failure.

        Returns:
            PokerDecision object, with is_valid=False if all retries fail
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                decision = self.analyze_poker_screenshot(
                    screenshot_base64=screenshot_base64,
                    player_stats=player_stats,
                    hand_history=hand_history,
                    game_context=game_context
                )

                if decision.is_valid:
                    return decision

                last_error = f"Invalid decision: {decision.error}"

            except anthropic.APIError as e:
                last_error = f"API error: {str(e)}"
            except Exception as e:
                last_error = f"Error: {str(e)}"

        # Return failed decision
        return PokerDecision(
            action="fold",
            reasoning=f"Analysis failed after {max_retries + 1} attempts: {last_error}",
            confidence=0.0,
            is_valid=False,
            error=last_error
        )

    def test_connection(self) -> bool:
        """Test the API connection."""
        try:
            self._client.messages.create(
                model=self._settings.ai_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception:
            return False
