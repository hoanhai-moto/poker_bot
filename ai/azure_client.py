"""Azure OpenAI client for poker analysis."""

from typing import Dict, List, Optional
import httpx
import json

from config import Settings
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser, PokerDecision


class AzureOpenAIClient:
    """Azure OpenAI API integration for poker analysis."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._prompt_builder = PromptBuilder()
        self._response_parser = ResponseParser()

        # Azure OpenAI configuration
        self._endpoint = settings.get("ai", "azure_endpoint", default="")
        self._api_key = settings.get("ai", "azure_api_key", default="")
        self._api_version = settings.get("ai", "azure_api_version", default="2025-01-01-preview")

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

        system_prompt = self._prompt_builder.get_system_prompt()

        # Prepare the request
        headers = {
            "Content-Type": "application/json",
            "api-key": self._api_key
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": self._settings.max_tokens,
            "temperature": 0.3
        }

        # Make the API call
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self._endpoint}?api-version={self._api_version}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

        # Extract the response text
        response_text = result["choices"][0]["message"]["content"]

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

            except httpx.HTTPStatusError as e:
                last_error = f"API error: {e.response.status_code} - {e.response.text}"
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
            headers = {
                "Content-Type": "application/json",
                "api-key": self._api_key
            }

            payload = {
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self._endpoint}?api-version={self._api_version}",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
            return True
        except Exception:
            return False
