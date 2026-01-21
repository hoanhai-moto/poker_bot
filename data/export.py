"""Hand history export functionality."""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from poker.hand_history import HandRecord


class HandHistoryExporter:
    """Exports hand history to various formats."""

    def __init__(self, output_dir: Optional[Path] = None):
        self._output_dir = output_dir or Path("./exports")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def export_to_json(
        self,
        hands: List[HandRecord],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export hands to JSON format.

        Args:
            hands: List of hand records to export
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hand_history_{timestamp}.json"

        filepath = self._output_dir / filename

        data = {
            "export_date": datetime.now().isoformat(),
            "hand_count": len(hands),
            "hands": [h.to_dict() for h in hands]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

    def export_to_text(
        self,
        hands: List[HandRecord],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export hands to human-readable text format.

        Args:
            hands: List of hand records to export
            filename: Optional filename

        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hand_history_{timestamp}.txt"

        filepath = self._output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Hand History Export\n")
            f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Hands: {len(hands)}\n")
            f.write("=" * 60 + "\n\n")

            for i, hand in enumerate(hands, 1):
                f.write(f"--- Hand #{i} ({hand.hand_id}) ---\n")
                f.write(f"Time: {hand.timestamp}\n")
                f.write(f"Hero Cards: {' '.join(hand.hero_cards)}\n")

                if hand.board:
                    f.write(f"Board: {' '.join(hand.board)}\n")

                f.write(f"Position: {hand.hero_position}\n")
                f.write(f"Blinds: {hand.small_blind}/{hand.big_blind}\n")
                f.write(f"Result: {hand.result_bb:+.2f} BB\n")

                if hand.ai_action:
                    f.write(f"AI Action: {hand.ai_action}\n")
                    f.write(f"AI Confidence: {hand.ai_confidence:.0%}\n")

                f.write("\nAction Sequence:\n")
                for action in hand.actions:
                    amount_str = f" {action['amount']}" if action.get('amount') else ""
                    f.write(f"  [{action['street']}] {action['player']}: {action['action_type']}{amount_str}\n")

                if hand.ai_reasoning:
                    f.write(f"\nAI Reasoning:\n  {hand.ai_reasoning}\n")

                f.write("\n" + "-" * 40 + "\n\n")

        return filepath

    def export_summary(
        self,
        hands: List[HandRecord],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export a summary of the session.

        Args:
            hands: List of hand records
            filename: Optional filename

        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_summary_{timestamp}.txt"

        filepath = self._output_dir / filename

        # Calculate stats
        total_profit = sum(h.result_bb for h in hands)
        winning_hands = len([h for h in hands if h.result_bb > 0])
        losing_hands = len([h for h in hands if h.result_bb < 0])
        break_even = len(hands) - winning_hands - losing_hands

        # Position breakdown
        position_stats: Dict[str, Dict] = {}
        for hand in hands:
            pos = hand.hero_position or "Unknown"
            if pos not in position_stats:
                position_stats[pos] = {"hands": 0, "profit": 0.0}
            position_stats[pos]["hands"] += 1
            position_stats[pos]["profit"] += hand.result_bb

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("SESSION SUMMARY\n")
            f.write("=" * 40 + "\n\n")

            f.write(f"Total Hands: {len(hands)}\n")
            f.write(f"Total Profit: {total_profit:+.2f} BB\n")
            f.write(f"BB/100: {(total_profit / len(hands) * 100):+.2f}\n\n") if hands else None

            f.write(f"Winning Hands: {winning_hands} ({winning_hands/len(hands)*100:.1f}%)\n") if hands else None
            f.write(f"Losing Hands: {losing_hands} ({losing_hands/len(hands)*100:.1f}%)\n") if hands else None
            f.write(f"Break Even: {break_even}\n\n")

            f.write("PROFIT BY POSITION\n")
            f.write("-" * 30 + "\n")
            for pos, stats in sorted(position_stats.items()):
                f.write(f"{pos:10} | {stats['hands']:4} hands | {stats['profit']:+8.2f} BB\n")

            f.write("\n")

            # AI performance
            ai_hands = [h for h in hands if h.ai_action]
            if ai_hands:
                ai_profit = sum(h.result_bb for h in ai_hands)
                avg_confidence = sum(h.ai_confidence or 0 for h in ai_hands) / len(ai_hands)

                f.write("AI PERFORMANCE\n")
                f.write("-" * 30 + "\n")
                f.write(f"AI-Assisted Hands: {len(ai_hands)}\n")
                f.write(f"AI Hands Profit: {ai_profit:+.2f} BB\n")
                f.write(f"Avg Confidence: {avg_confidence:.0%}\n")

        return filepath


def export_hands(
    hands: List[HandRecord],
    format: str = "json",
    output_dir: Optional[Path] = None
) -> Path:
    """
    Convenience function to export hands.

    Args:
        hands: List of hand records
        format: Export format ("json", "text", or "summary")
        output_dir: Output directory

    Returns:
        Path to exported file
    """
    exporter = HandHistoryExporter(output_dir)

    if format == "json":
        return exporter.export_to_json(hands)
    elif format == "text":
        return exporter.export_to_text(hands)
    elif format == "summary":
        return exporter.export_summary(hands)
    else:
        raise ValueError(f"Unknown format: {format}")
