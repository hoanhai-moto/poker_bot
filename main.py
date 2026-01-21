#!/usr/bin/env python3
"""
AI Poker Bot - Main Entry Point

Uses Claude Vision API to analyze poker screenshots and make optimal decisions.
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from config import Settings
from gui import MainWindow
from utils import setup_logger


def check_dependencies() -> bool:
    """Check that all required dependencies are available."""
    missing = []

    try:
        import anthropic
    except ImportError:
        missing.append("anthropic")

    try:
        import PyQt6
    except ImportError:
        missing.append("PyQt6")

    try:
        import pyautogui
    except ImportError:
        missing.append("pyautogui")

    try:
        import mss
    except ImportError:
        missing.append("mss")

    try:
        import pynput
    except ImportError:
        missing.append("pynput")

    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Please install with: pip install -r requirements.txt")
        return False

    return True


def check_api_key(settings: Settings) -> bool:
    """Check if API key is configured."""
    azure_key = settings.get("ai", "azure_api_key", default="")
    if not azure_key:
        print("Warning: No Azure API key configured.")
        print("AI analysis will not be available until configured.")
        return False
    return True


def main():
    """Main entry point."""
    # Setup logging
    logger = setup_logger("poker_bot")
    logger.info("Starting Poker Bot...")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Poker Bot")
    app.setStyle("Fusion")

    # Apply dark theme
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QGroupBox {
            border: 1px solid #3c3c3c;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            background-color: #0d47a1;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1565c0;
        }
        QPushButton:pressed {
            background-color: #0a3d91;
        }
        QPushButton:disabled {
            background-color: #555555;
            color: #888888;
        }
        QComboBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
            min-width: 150px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            selection-background-color: #0d47a1;
        }
        QSpinBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        }
        QTableWidget {
            background-color: #1e1e1e;
            alternate-background-color: #252525;
            gridline-color: #3c3c3c;
            border: 1px solid #3c3c3c;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QTableWidget::item:selected {
            background-color: #0d47a1;
        }
        QHeaderView::section {
            background-color: #3c3c3c;
            padding: 5px;
            border: none;
            font-weight: bold;
        }
        QStatusBar {
            background-color: #1e1e1e;
            border-top: 1px solid #3c3c3c;
        }
        QMenuBar {
            background-color: #2b2b2b;
        }
        QMenuBar::item:selected {
            background-color: #0d47a1;
        }
        QMenu {
            background-color: #2b2b2b;
            border: 1px solid #3c3c3c;
        }
        QMenu::item:selected {
            background-color: #0d47a1;
        }
        QSplitter::handle {
            background-color: #3c3c3c;
        }
        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
    """)

    # Load settings
    try:
        settings = Settings()
        logger.info("Settings loaded")
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        QMessageBox.critical(
            None,
            "Configuration Error",
            f"Failed to load settings: {e}"
        )
        sys.exit(1)

    # Check API key (warning only)
    check_api_key(settings)

    # Create and show main window
    try:
        window = MainWindow(settings)
        window.show()
        logger.info("Main window displayed")
    except Exception as e:
        logger.error(f"Failed to create main window: {e}")
        QMessageBox.critical(
            None,
            "Startup Error",
            f"Failed to start application: {e}"
        )
        sys.exit(1)

    # Run application
    exit_code = app.exec()
    logger.info(f"Application exited with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
