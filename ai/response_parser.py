import json
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class PokerDecision:
    """Represents a parsed poker decision from Claude."""

    action: str  # fold, check, call, raise
    amount: Optional[float] = None
    reasoning: str = ""
    confidence: float = 0.0
    detected_cards: Dict[str, List[str]] = field(default_factory=dict)
    pot_size: Optional[float] = None
    position: Optional[str] = None
    street: Optional[str] = None
    is_valid: bool = True
    error: Optional[str] = None
    raw_response: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action,
            "amount": self.amount,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "detected_cards": self.detected_cards,
            "pot_size": self.pot_size,
            "position": self.position,
            "street": self.street,
            "is_valid": self.is_valid,
            "error": self.error
        }


class ResponseParser:
    """Parses Claude's poker analysis responses."""

    VALID_ACTIONS = {"fold", "check", "call", "raise"}
    VALID_STREETS = {"preflop", "flop", "turn", "river"}

    def parse_response(self, response_text: str) -> PokerDecision:
        """
        Parse Claude's response into a PokerDecision.

        Args:
            response_text: The raw text response from Claude

        Returns:
            PokerDecision object with parsed data
        """
        # Try to extract JSON from the response
        json_data = self._extract_json(response_text)

        if json_data is None:
            return PokerDecision(
                action="fold",
                reasoning="Failed to parse response",
                is_valid=False,
                error="No valid JSON found in response",
                raw_response=response_text
            )

        try:
            return self._parse_json(json_data, response_text)
        except Exception as e:
            return PokerDecision(
                action="fold",
                reasoning=f"Parse error: {str(e)}",
                is_valid=False,
                error=str(e),
                raw_response=response_text
            )

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON object from text that may contain other content."""
        # Try to find JSON block in markdown code fence
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON object
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try parsing the entire text as JSON
        try:
            # Find the outermost { and }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

        return None

    def _parse_json(self, data: Dict, raw_response: str) -> PokerDecision:
        """Parse the extracted JSON into a PokerDecision."""
        # Extract and validate action
        action = str(data.get("action", "fold")).lower()
        if action not in self.VALID_ACTIONS:
            return PokerDecision(
                action="fold",
                reasoning=f"Invalid action: {action}",
                is_valid=False,
                error=f"Invalid action: {action}",
                raw_response=raw_response
            )

        # Extract amount (for raise)
        amount = None
        if action == "raise":
            raw_amount = data.get("amount")
            if raw_amount is not None:
                try:
                    amount = float(raw_amount)
                except (ValueError, TypeError):
                    pass

        # Extract confidence
        confidence = 0.5
        raw_conf = data.get("confidence")
        if raw_conf is not None:
            try:
                confidence = max(0.0, min(1.0, float(raw_conf)))
            except (ValueError, TypeError):
                pass

        # Extract detected cards
        detected_cards = {}
        raw_cards = data.get("detected_cards", {})
        if isinstance(raw_cards, dict):
            detected_cards = {
                "hole_cards": raw_cards.get("hole_cards", []),
                "board": raw_cards.get("board", [])
            }

        # Extract street
        street = None
        raw_street = data.get("street")
        if raw_street and str(raw_street).lower() in self.VALID_STREETS:
            street = str(raw_street).lower()

        # Extract pot size
        pot_size = None
        raw_pot = data.get("pot_size")
        if raw_pot is not None:
            try:
                pot_size = float(raw_pot)
            except (ValueError, TypeError):
                pass

        return PokerDecision(
            action=action,
            amount=amount,
            reasoning=str(data.get("reasoning", "")),
            confidence=confidence,
            detected_cards=detected_cards,
            pot_size=pot_size,
            position=data.get("position"),
            street=street,
            is_valid=True,
            raw_response=raw_response
        )

    def validate_decision(self, decision: PokerDecision) -> List[str]:
        """
        Validate a decision and return list of warnings.

        Returns:
            List of warning messages (empty if no issues)
        """
        warnings = []

        if decision.action == "raise" and decision.amount is None:
            warnings.append("Raise action without amount specified")

        if decision.confidence < 0.3:
            warnings.append(f"Low confidence decision ({decision.confidence:.0%})")

        if not decision.detected_cards.get("hole_cards"):
            warnings.append("No hole cards detected")

        return warnings
