from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit,
    QPushButton, QHBoxLayout, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat


class LogViewer(QWidget):
    """Widget for displaying action logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_lines = 1000
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Log text area
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                border: 1px solid #3C3C3C;
            }
        """)
        layout.addWidget(self._log_text)

        # Control buttons
        btn_layout = QHBoxLayout()

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self.clear)
        btn_layout.addWidget(self._clear_btn)

        self._export_btn = QPushButton("Export Log")
        self._export_btn.clicked.connect(self._export_log)
        btn_layout.addWidget(self._export_btn)

        btn_layout.addStretch()

        self._auto_scroll_btn = QPushButton("Auto-Scroll: ON")
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(True)
        self._auto_scroll_btn.clicked.connect(self._toggle_auto_scroll)
        btn_layout.addWidget(self._auto_scroll_btn)

        layout.addLayout(btn_layout)

        self._auto_scroll = True

    def _toggle_auto_scroll(self):
        self._auto_scroll = self._auto_scroll_btn.isChecked()
        status = "ON" if self._auto_scroll else "OFF"
        self._auto_scroll_btn.setText(f"Auto-Scroll: {status}")

    def log(self, message: str, level: str = "INFO"):
        """
        Add a log message.

        Args:
            message: The message to log
            level: Log level (INFO, WARNING, ERROR, SUCCESS, AI)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color mapping
        colors = {
            "INFO": "#D4D4D4",
            "WARNING": "#FFCC00",
            "ERROR": "#FF6B6B",
            "SUCCESS": "#4CAF50",
            "AI": "#64B5F6",
            "ACTION": "#CE93D8"
        }

        color = colors.get(level.upper(), "#D4D4D4")

        # Format the log entry
        cursor = self._log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Timestamp format
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#808080"))
        cursor.insertText(f"[{timestamp}] ", fmt)

        # Level format
        fmt.setForeground(QColor(color))
        cursor.insertText(f"[{level}] ", fmt)

        # Message
        fmt.setForeground(QColor("#D4D4D4"))
        cursor.insertText(f"{message}\n", fmt)

        # Trim if too many lines
        self._trim_log()

        # Auto scroll
        if self._auto_scroll:
            self._log_text.setTextCursor(cursor)
            self._log_text.ensureCursorVisible()

    def log_action(self, player: str, action: str, amount: Optional[float] = None):
        """Log a poker action."""
        msg = f"{player}: {action}"
        if amount is not None:
            msg += f" {amount}"
        self.log(msg, "ACTION")

    def log_ai_decision(
        self,
        action: str,
        amount: Optional[float] = None,
        confidence: float = 0.0,
        reasoning: str = ""
    ):
        """Log an AI decision."""
        msg = f"Recommended: {action.upper()}"
        if amount is not None:
            msg += f" {amount}"
        msg += f" (confidence: {confidence:.0%})"
        self.log(msg, "AI")

        if reasoning:
            # Log reasoning on separate line with indentation
            for line in reasoning.split('\n')[:3]:  # Limit to 3 lines
                self.log(f"  > {line.strip()}", "AI")

    def log_error(self, message: str):
        """Log an error message."""
        self.log(message, "ERROR")

    def log_warning(self, message: str):
        """Log a warning message."""
        self.log(message, "WARNING")

    def log_success(self, message: str):
        """Log a success message."""
        self.log(message, "SUCCESS")

    def _trim_log(self):
        """Remove old lines if log exceeds max."""
        doc = self._log_text.document()
        while doc.blockCount() > self._max_lines:
            cursor = QTextCursor(doc.firstBlock())
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove newline

    def _export_log(self):
        """Export log to file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Log",
            f"poker_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._log_text.toPlainText())
            self.log_success(f"Log exported to {filepath}")

    def clear(self):
        """Clear the log."""
        self._log_text.clear()

    def get_log_text(self) -> str:
        """Get all log text."""
        return self._log_text.toPlainText()
