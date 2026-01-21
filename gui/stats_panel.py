from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QGroupBox,
    QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class StatsPanel(QWidget):
    """Panel displaying player statistics and session info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Session stats group
        session_group = QGroupBox("Session Stats")
        session_layout = QVBoxLayout(session_group)

        self._session_stats_layout = QHBoxLayout()
        self._session_labels = {}

        for label_name in ["Hands", "Profit", "BB/100", "Duration"]:
            stat_widget = self._create_stat_widget(label_name, "0")
            self._session_stats_layout.addWidget(stat_widget)
            self._session_labels[label_name.lower()] = stat_widget.findChild(QLabel, "value")

        session_layout.addLayout(self._session_stats_layout)
        layout.addWidget(session_group)

        # Player stats table
        players_group = QGroupBox("Player Statistics")
        players_layout = QVBoxLayout(players_group)

        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(9)
        self._stats_table.setHorizontalHeaderLabels([
            "Player", "Hands", "VPIP", "PFR", "3-Bet",
            "Fold to 3B", "AF", "WTSD", "C-Bet"
        ])

        header = self._stats_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 9):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self._stats_table.setAlternatingRowColors(True)
        self._stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._stats_table.verticalHeader().setVisible(False)

        players_layout.addWidget(self._stats_table)
        layout.addWidget(players_group)

        # Current hand info
        hand_group = QGroupBox("Current Hand")
        hand_layout = QVBoxLayout(hand_group)

        self._hand_info_label = QLabel("No active hand")
        self._hand_info_label.setWordWrap(True)
        hand_layout.addWidget(self._hand_info_label)

        self._ai_decision_label = QLabel("")
        self._ai_decision_label.setWordWrap(True)
        self._ai_decision_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        hand_layout.addWidget(self._ai_decision_label)

        layout.addWidget(hand_group)

    def _create_stat_widget(self, name: str, value: str) -> QWidget:
        """Create a stat display widget."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: gray; font-size: 11px;")

        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        layout.addWidget(name_label)
        layout.addWidget(value_label)

        return widget

    def update_session_stats(
        self,
        hands: int = 0,
        profit_bb: float = 0.0,
        bb_per_100: float = 0.0,
        duration_minutes: float = 0.0
    ):
        """Update session statistics display."""
        if self._session_labels.get("hands"):
            self._session_labels["hands"].setText(str(hands))

        if self._session_labels.get("profit"):
            profit_str = f"{profit_bb:+.1f} BB"
            color = "#4CAF50" if profit_bb >= 0 else "#f44336"
            self._session_labels["profit"].setText(profit_str)
            self._session_labels["profit"].setStyleSheet(f"color: {color};")

        if self._session_labels.get("bb/100"):
            bb100_str = f"{bb_per_100:+.1f}"
            color = "#4CAF50" if bb_per_100 >= 0 else "#f44336"
            self._session_labels["bb/100"].setText(bb100_str)
            self._session_labels["bb/100"].setStyleSheet(f"color: {color};")

        if self._session_labels.get("duration"):
            hours = int(duration_minutes // 60)
            mins = int(duration_minutes % 60)
            self._session_labels["duration"].setText(f"{hours}h {mins}m")

    def update_player_stats(self, player_stats: Dict[str, Dict]):
        """Update player statistics table."""
        self._stats_table.setRowCount(len(player_stats))

        for row, (player_name, stats) in enumerate(player_stats.items()):
            self._stats_table.setItem(row, 0, QTableWidgetItem(player_name))
            self._stats_table.setItem(row, 1, QTableWidgetItem(str(stats.get("hands", 0))))
            self._stats_table.setItem(row, 2, QTableWidgetItem(f"{stats.get('vpip', 0):.1f}%"))
            self._stats_table.setItem(row, 3, QTableWidgetItem(f"{stats.get('pfr', 0):.1f}%"))
            self._stats_table.setItem(row, 4, QTableWidgetItem(f"{stats.get('three_bet', 0):.1f}%"))
            self._stats_table.setItem(row, 5, QTableWidgetItem(f"{stats.get('fold_to_3bet', 0):.1f}%"))
            self._stats_table.setItem(row, 6, QTableWidgetItem(f"{stats.get('af', 0):.1f}"))
            self._stats_table.setItem(row, 7, QTableWidgetItem(f"{stats.get('wtsd', 0):.1f}%"))
            self._stats_table.setItem(row, 8, QTableWidgetItem(f"{stats.get('cbet', 0):.1f}%"))

            # Color code based on player type
            self._color_code_row(row, stats)

    def _color_code_row(self, row: int, stats: Dict):
        """Apply color coding to a player row based on their stats."""
        hands = stats.get("hands", 0)
        if hands < 20:
            return  # Not enough data

        vpip = stats.get("vpip", 0)
        af = stats.get("af", 0)

        # Determine player type color
        if vpip < 25 and af > 2.0:  # TAG
            color = "#E3F2FD"  # Light blue
        elif vpip < 25:  # Tight passive
            color = "#F3E5F5"  # Light purple
        elif af > 2.0:  # LAG
            color = "#FFF3E0"  # Light orange
        else:  # Loose passive
            color = "#FFEBEE"  # Light red

        for col in range(self._stats_table.columnCount()):
            item = self._stats_table.item(row, col)
            if item:
                item.setBackground(Qt.GlobalColor.transparent)

    def update_hand_info(self, hand_info: Optional[Dict]):
        """Update current hand information."""
        if not hand_info:
            self._hand_info_label.setText("No active hand")
            return

        cards = " ".join(hand_info.get("hero_cards", []))
        position = hand_info.get("position", "?")
        pot = hand_info.get("pot_size", 0)
        street = hand_info.get("street", "preflop")

        info_text = f"Cards: {cards}  |  Position: {position}  |  Pot: {pot:.1f}  |  Street: {street}"
        self._hand_info_label.setText(info_text)

    def update_ai_decision(self, decision: Optional[Dict]):
        """Update AI decision display."""
        if not decision:
            self._ai_decision_label.setText("")
            return

        action = decision.get("action", "").upper()
        amount = decision.get("amount")
        confidence = decision.get("confidence", 0)

        action_str = action
        if amount and action == "RAISE":
            action_str = f"{action} to {amount}"

        confidence_pct = f"({confidence:.0%} confidence)"
        self._ai_decision_label.setText(f"AI Recommends: {action_str} {confidence_pct}")

        # Color based on action
        colors = {
            "FOLD": "#f44336",
            "CHECK": "#9E9E9E",
            "CALL": "#2196F3",
            "RAISE": "#4CAF50"
        }
        color = colors.get(action, "#4CAF50")
        self._ai_decision_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def clear(self):
        """Clear all displayed data."""
        self.update_session_stats()
        self._stats_table.setRowCount(0)
        self._hand_info_label.setText("No active hand")
        self._ai_decision_label.setText("")
